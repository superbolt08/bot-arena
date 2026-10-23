"""Local FastAPI service. Bind to loopback: uploaded bots execute trusted code."""
import asyncio
import hashlib
import json
import shutil
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .reference_bots import BOT_INFO, BUILTINS
from .runner import Match, ExternalBot, ROOT
from .evaluation import evaluate
from .sdk import ACTIONS
from .engine import Game
from .guides import GUIDES
from .competition import atomic_json, snapshot_entries, runtime_digest, verify_entries, run_round_robin, public_job, build_release, build_participant_release
from .sdk import RULES_VERSION
from .knockout import bracket_report, run_knockout

DATA=ROOT/"data"
for folder in ["bots","replays","evaluations"]: (DATA/folder).mkdir(parents=True,exist_ok=True)
registry={}
for manifest in (DATA/"bots").glob("*/manifest.json"):
    entry=json.loads(manifest.read_text())
    registry[entry["id"]]=entry
matches={}
jobs={}
tasks=set()
competition_stops={}
release_lock=threading.Lock()
STARTUP_DIGEST=runtime_digest()


def save_replay(mid,match):
    (DATA/"replays"/(mid+".json")).write_text(json.dumps(match.replay()))


async def drive(mid):
    match=matches[mid]
    try:
        while not match.game.done:
            if not match.paused:
                async with match.lock:
                    await asyncio.to_thread(match.step)
            await asyncio.sleep(.2/match.speed if not match.paused else .1)
        await asyncio.to_thread(save_replay,mid,match)
    finally:
        match.close()


@asynccontextmanager
async def lifespan(app):
    yield
    for stop in competition_stops.values(): stop.set()
    for task in tasks: task.cancel()
    if tasks: await asyncio.gather(*tasks,return_exceptions=True)
    for match in matches.values(): match.close()


app=FastAPI(title="Bot Arena",lifespan=lifespan)


@app.middleware("http")
async def local_only(request:Request,call_next):
    # Prevent a remote website from submitting local code through the user's browser.
    from urllib.parse import urlparse
    origin=request.headers.get("origin")
    if origin and urlparse(origin).hostname not in ("localhost","127.0.0.1"):
        return JSONResponse({"detail":"Only local browser origins are allowed"},status_code=403)
    if request.url.hostname not in ("localhost","127.0.0.1","testserver"):
        return JSONResponse({"detail":"Local access only"},status_code=403)
    return await call_next(request)


@app.get("/api/bots")
def bots(): return BOT_INFO+[{k:v for k,v in b.items() if k!="path"} for b in registry.values()]


@app.get("/api/preview")
def preview(seed:int=42,mode:str="elimination",participants:str="survivor,hunter"):
    ids=participants.split(",")
    validate_ids(ids)
    labels={b["id"]:b["name"] for b in BOT_INFO}
    names=["YOU" if b=="human" else registry.get(b,{}).get("name",labels.get(b,b)) for b in ids]
    try: return Game(names,seed,mode).snapshot()
    except ValueError as e: raise HTTPException(400,str(e))


def validate_ids(ids):
    if any(i not in BUILTINS and i not in registry and i!="human" for i in ids):
        raise HTTPException(400,"Unknown bot")
    if ids.count("human")>1: raise HTTPException(400,"Only one local human is supported")


class MatchConfig(BaseModel):
    bots:List[str]=Field(default_factory=lambda:["survivor","hunter"],min_length=2,max_length=4)
    seed:int=42
    mode:str="elimination"


@app.post("/api/matches")
async def create_match(config:MatchConfig):
    validate_ids(config.bots)
    if sum(not m.game.done for m in matches.values())>=4: raise HTTPException(409,"Finish or stop an active match first")
    try: match=await asyncio.to_thread(Match,config.bots,registry,config.seed,config.mode)
    except (ValueError,KeyError) as e: raise HTTPException(400,str(e))
    mid=uuid.uuid4().hex
    match.lock=asyncio.Lock()
    matches[mid]=match
    # Keep only a small number of completed matches in memory; replays remain on disk.
    for old in list(matches):
        if len(matches)<=12: break
        if matches[old].game.done: del matches[old]
    task=asyncio.create_task(drive(mid)); tasks.add(task); task.add_done_callback(tasks.discard)
    return {"id":mid,"state":match.game.snapshot()}


def get_match(mid):
    if mid not in matches: raise HTTPException(404,"Match not found")
    return matches[mid]


@app.get("/api/matches/{mid}")
def match_state(mid:str):
    m=get_match(mid)
    return dict(m.game.snapshot(),errors=m.errors,paused=m.paused,speed=m.speed)


@app.post("/api/matches/{mid}/control")
async def control(mid:str,body:dict):
    m=get_match(mid)
    async with m.lock:
        if "paused" in body: m.paused=bool(body["paused"])
        if "speed" in body:
            if body["speed"] not in [.5,1,2,5,10]: raise HTTPException(400,"Invalid speed")
            m.speed=body["speed"]
        if body.get("step"):
            m.paused=True
            await asyncio.to_thread(m.step)
        if body.get("stop"):
            m.game.done=True; m.game.result="stopped"
            m.close()
    return {"paused":m.paused,"speed":m.speed}


@app.post("/api/matches/{mid}/action")
def human_action(mid:str,body:dict):
    m=get_match(mid)
    if body.get("action") not in ACTIONS: raise HTTPException(400,"Invalid action")
    if "human" not in m.bot_ids: raise HTTPException(400,"No human in this match")
    m.inputs[m.bot_ids.index("human")]=body["action"]
    return {"ok":True}


@app.websocket("/ws/matches/{mid}")
async def live(ws:WebSocket,mid:str):
    from urllib.parse import urlparse
    origin=ws.headers.get("origin")
    if origin and urlparse(origin).hostname not in ("127.0.0.1","localhost"):
        await ws.close(code=1008); return
    await ws.accept()
    if mid not in matches:
        await ws.close(code=1008); return
    m=matches[mid]
    try:
        while True:
            async with m.lock:
                state=m.game.snapshot()
                # Only expose filtered observations to the human player's browser during play.
                # Spectator debug views are available only in bot-only matches.
                if "human" in m.bot_ids and not m.game.done:
                    pid=m.bot_ids.index("human")
                    obs=m.game.observe(pid)
                    state={"tick":m.game.tick,"seed":m.game.seed,"mode":m.game.mode,"max_ticks":m.game.max_ticks,
                           "done":False,"winner":None,"result":None,"board":obs["board"],
                           "players":[obs["self"]]+obs["opponents"],"bombs":obs["bombs"],"projectiles":obs["projectiles"],
                           "flames":obs["flames"],"pickups":obs["pickups"],"visible":obs["visible"],"entity_visible":obs["entity_visible"],"events":[],"supply_drop":obs["supply_drop"]}
                    views={str(pid):obs}
                else: views={str(p.id):m.game.observe(p.id) for p in m.game.players}
                payload={"state":state,"views":views,"errors":m.errors,"paused":m.paused,"speed":m.speed}
            await ws.send_json(payload)
            if m.game.done: break
            await asyncio.sleep(.1)
    except (WebSocketDisconnect,RuntimeError): pass


@app.post("/api/bots/upload")
async def upload(name:str=Form(...),trusted:bool=Form(False),file:UploadFile=File(...),model:Optional[UploadFile]=File(None)):
    if not trusted: raise HTTPException(400,"Confirm this is trusted local Python code")
    if not file.filename or not file.filename.endswith(".py"): raise HTTPException(400,"Upload a .py file")
    content=await file.read(256*1024+1)
    if len(content)>256*1024: raise HTTPException(400,"Bot file limit is 256 KB")
    model_content=await model.read(5*1024*1024+1) if model else None
    if model_content and len(model_content)>5*1024*1024: raise HTTPException(400,"Model limit is 5 MB")
    if model_content:
        try: json.loads(model_content)
        except ValueError: raise HTTPException(400,"The prototype accepts JSON model artifacts")
    bid="custom_"+uuid.uuid4().hex[:12]
    folder=DATA/"bots"/bid; folder.mkdir()
    path=folder/"bot.py"; path.write_bytes(content)
    if model_content: (folder/"model.json").write_bytes(model_content)
    try:
        worker=await asyncio.to_thread(ExternalBot,path)
        worker.close()
    except Exception as e:
        shutil.rmtree(folder)
        raise HTTPException(400,"Bot validation failed: "+str(e))
    digest=hashlib.sha256(content+(model_content or b"")).hexdigest()[:8]
    entry={"id":bid,"name":name.strip()[:32] or "Custom bot","style":"Uploaded · "+digest,"version":digest,"path":str(path),"color":"#7cbbff"}
    (folder/"manifest.json").write_text(json.dumps(entry))
    registry[bid]=entry
    return {k:v for k,v in entry.items() if k!="path"}


class EvalConfig(BaseModel):
    candidate:str
    opponents:List[str]=Field(default_factory=lambda:["hunter"],min_length=1,max_length=3)
    games:int=Field(default=20,ge=4,le=200)
    seed:int=10000
    mode:str="elimination"


@app.post("/api/evaluations")
async def start_evaluation(config:EvalConfig):
    validate_ids([config.candidate]+config.opponents)
    if "human" in [config.candidate]+config.opponents: raise HTTPException(400,"Evaluation requires bots")
    if config.mode not in ("elimination","deathmatch"): raise HTTPException(400,"Invalid mode")
    if any(j["status"]=="running" for j in jobs.values()): raise HTTPException(409,"An evaluation is already running")
    jid=uuid.uuid4().hex
    job={"id":jid,"status":"running","completed":0,"total":config.games,"config":config.model_dump(),"created_at":time.time(),"rows":[]}
    jobs[jid]=job
    def run():
        try:
            def progress(row,replay):
                rid=jid+"_"+str(row["index"])
                (DATA/"replays"/(rid+".json")).write_text(json.dumps(replay))
                row["replay_id"]=rid
                job["rows"].append(row); job["completed"]+=1
            job["report"]=evaluate(config.candidate,config.opponents,config.games,config.seed,config.mode,registry,progress)
            job["status"]="complete"
        except Exception as e:
            job["status"]="failed"; job["error"]=str(e)
        (DATA/"evaluations"/(jid+".json")).write_text(json.dumps(job))
    task=asyncio.create_task(asyncio.to_thread(run)); tasks.add(task); task.add_done_callback(tasks.discard)
    return job


class RoundRobinConfig(BaseModel):
    roster:List[str]=Field(min_length=2,max_length=16)
    games_per_pair:int=Field(default=8,ge=8,le=80)
    seed:int=10000
    mode:str="elimination"
    name:str=Field(default="Round robin",max_length=60)
    individual_packs:bool=False


def load_competition(jid):
    if len(jid)!=32 or any(c not in "0123456789abcdef" for c in jid):
        raise HTTPException(404,"Round robin not found")
    if jid in jobs:
        job=jobs[jid]
    else:
        path=DATA/"evaluations"/(jid+".json")
        if not path.is_file(): raise HTTPException(404,"Round robin not found")
        job=json.loads(path.read_text())
        if job.get("status")=="running": job["status"]="interrupted"
    if job.get("config",{}).get("kind") not in ("round_robin","knockout"):
        raise HTTPException(404,"Round robin not found")
    return job


def launch_competition(job):
    stop=threading.Event()
    competition_stops[job["id"]]=stop
    runner=run_knockout if job["config"]["kind"]=="knockout" else run_round_robin
    task=asyncio.create_task(asyncio.to_thread(runner,job,DATA,stop))
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    def cleanup(_):
        if competition_stops.get(job["id"]) is stop:
            competition_stops.pop(job["id"],None)
    task.add_done_callback(cleanup)


@app.post("/api/round-robins")
async def start_round_robin(config:RoundRobinConfig):
    return await start_competition(config,"round_robin")


class KnockoutConfig(RoundRobinConfig):
    name:str=Field(default="Knockout tournament",max_length=60)
    shuffle:bool=True


@app.post("/api/knockouts")
async def start_knockout(config:KnockoutConfig):
    return await start_competition(config,"knockout")


async def start_competition(config,kind):
    if STARTUP_DIGEST!=runtime_digest(): raise HTTPException(409,"Backend sources changed; restart the server before starting a competition")
    validate_ids(config.roster)
    if "human" in config.roster: raise HTTPException(400,"Round robins require bots")
    if len(set(config.roster))!=len(config.roster): raise HTTPException(400,"Choose each bot version once")
    if config.mode not in ("elimination","deathmatch"): raise HTTPException(400,"Invalid mode")
    if config.games_per_pair%8: raise HTTPException(400,"Use a multiple of eight games per pair to balance seats and corners")
    total=(len(config.roster)-1)*config.games_per_pair if kind=="knockout" else len(config.roster)*(len(config.roster)-1)//2*config.games_per_pair
    if total>2000: raise HTTPException(400,"Limit the run to 2,000 matches; reduce the roster or games per pair")
    if any(j["status"]=="running" for j in jobs.values()): raise HTTPException(409,"An evaluation is already running")
    jid=uuid.uuid4().hex
    job={"id":jid,"status":"running","completed":0,"total":total,"created_at":time.time(),"rows":[],
         "config":{"kind":kind,**config.model_dump()},"entries":{},
         "rules_version":RULES_VERSION,"runtime_digest":runtime_digest()}
    if kind=="knockout":
        job["decisions"]=[]
        job["report"]=bracket_report(job["config"],[])
    jobs[jid]=job
    try:
        job["entries"]=await asyncio.to_thread(snapshot_entries,config.roster,registry,DATA/"competitions"/jid/"entries")
        atomic_json(DATA/"evaluations"/(jid+".json"),job)
    except Exception as exc:
        job["status"]="failed";job["error"]="Submission snapshot failed: "+str(exc)[:200]
        atomic_json(DATA/"evaluations"/(jid+".json"),job)
        raise HTTPException(400,job["error"])
    launch_competition(job)
    return public_job(job)


@app.post("/api/round-robins/{jid}/pause")
@app.post("/api/knockouts/{jid}/pause")
async def pause_round_robin(jid:str):
    job=load_competition(jid)
    stop=competition_stops.get(jid)
    if job["status"]!="running" or stop is None: raise HTTPException(409,"This run is not active")
    job["pause_requested"]=True
    stop.set()
    return public_job(job)


@app.post("/api/round-robins/{jid}/resume")
@app.post("/api/knockouts/{jid}/resume")
async def resume_round_robin(jid:str):
    job=load_competition(jid)
    if job["status"] not in ("paused","interrupted","failed"): raise HTTPException(409,"This run cannot be resumed")
    if any(j["status"]=="running" for j in jobs.values()): raise HTTPException(409,"An evaluation is already running")
    try:
        if job["runtime_digest"]!=runtime_digest() or STARTUP_DIGEST!=runtime_digest(): raise ValueError("Engine/runtime sources changed; restart and start a new run")
        if len(job["entries"])!=len(job["config"]["roster"]): raise ValueError("Incomplete submission snapshot; start a new run")
        verify_entries(job["entries"])
    except (ValueError,OSError) as exc: raise HTTPException(409,str(exc))
    job["status"]="running";job.pop("error",None);job.pop("pause_requested",None)
    jobs[jid]=job
    atomic_json(DATA/"evaluations"/(jid+".json"),job)
    launch_competition(job)
    return public_job(job)


@app.get("/api/round-robins/{jid}/release")
@app.get("/api/knockouts/{jid}/release")
def round_robin_release(jid:str):
    job=load_competition(jid)
    if job["status"]!="complete": raise HTTPException(409,"Complete the run before releasing replays")
    try:
        with release_lock: path=build_release(job,DATA)
    except (OSError,ValueError,KeyError) as exc: raise HTTPException(409,"Could not build release: "+str(exc)[:200])
    return FileResponse(path,media_type="application/zip",filename="anonymous-competition.zip")


@app.get("/api/round-robins/{jid}/participants/{bid}/release")
def participant_round_robin_release(jid:str,bid:str):
    job=load_competition(jid)
    if job["config"].get("kind")!="round_robin": raise HTTPException(404,"Round robin not found")
    if job["status"]!="complete": raise HTTPException(409,"Complete the run before releasing participant packs")
    if not job["config"].get("individual_packs"): raise HTTPException(404,"Individual participant packs were not enabled")
    if bid not in job["config"]["roster"]: raise HTTPException(404,"Participant not found")
    try:
        with release_lock: path,stem=build_participant_release(job,DATA,bid)
    except (OSError,ValueError,KeyError) as exc:
        raise HTTPException(409,"Could not build participant pack: "+str(exc)[:200])
    return FileResponse(path,media_type="application/zip",filename=stem+"-feedback.zip")


class BracketDecision(BaseModel):
    series_id:str
    winner:str
    reason:str=Field(min_length=5,max_length=500)


@app.post("/api/knockouts/{jid}/decision")
async def decide_knockout(jid:str,decision:BracketDecision):
    job=load_competition(jid)
    if job["config"]["kind"]!="knockout" or job["status"]!="awaiting_decision":
        raise HTTPException(409,"This bracket is not waiting for an organizer ruling")
    if any(j["status"]=="running" for j in jobs.values()): raise HTTPException(409,"An evaluation is already running")
    report=bracket_report(job["config"],job["rows"],job.get("decisions",[]))
    node=next((n for n in report["series"] if n["id"]==decision.series_id),None)
    if not node or node["status"]!="awaiting_decision" or decision.winner not in node["participants"] or len(decision.reason.strip())<5:
        raise HTTPException(400,"Choose a tied series participant and record the ruling reason")
    try:
        if job["runtime_digest"]!=runtime_digest() or STARTUP_DIGEST!=runtime_digest():
            raise ValueError("Engine/runtime sources changed; restart and start a new run")
        verify_entries(job["entries"])
    except (ValueError,OSError) as exc: raise HTTPException(409,str(exc))
    job.setdefault("decisions",[]).append({**decision.model_dump(),"reason":decision.reason.strip(),"created_at":time.time()})
    job["status"]="running"
    jobs[jid]=job
    atomic_json(DATA/"evaluations"/(jid+".json"),job)
    launch_competition(job)
    return public_job(job)


@app.get("/api/evaluations")
def list_evaluations():
    stored={}
    for path in (DATA/"evaluations").glob("*.json"):
        try:
            item=json.loads(path.read_text())
        except (OSError,ValueError):
            continue
        config=item.get("config") if isinstance(item,dict) else None
        # The evaluations folder has historically also contained training artifacts.
        # Only expose records with the shape Experiment Lab can render.
        if (isinstance(config,dict) and ((isinstance(config.get("candidate"),str)
                and isinstance(config.get("opponents"),list)) or (config.get("kind") in ("round_robin","knockout") and isinstance(config.get("roster"),list)))
                and isinstance(item.get("created_at"),(int,float))
                and item.get("status") in ("running","complete","failed","paused","interrupted","awaiting_decision")):
            if config.get("kind") in ("round_robin","knockout") and item["status"]=="running" and path.stem not in jobs:
                item["status"]="interrupted"
            stored[path.stem]=item
    stored.update(jobs)
    return [public_job(j) if j.get("config",{}).get("kind") in ("round_robin","knockout") else j
            for j in sorted(stored.values(),key=lambda j:j["created_at"],reverse=True)[:20]]


@app.get("/api/evaluations/{jid}")
def evaluation(jid:str):
    if jid in jobs:
        job=jobs[jid]
        return public_job(job) if job.get("config",{}).get("kind") in ("round_robin","knockout") else job
    path=DATA/"evaluations"/(jid+".json")
    if not jid.isalnum() or not path.is_file(): raise HTTPException(404,"Evaluation not found")
    job=json.loads(path.read_text())
    if job.get("config",{}).get("kind") in ("round_robin","knockout"):
        if job.get("status")=="running": job["status"]="interrupted"
        return public_job(job)
    return job


@app.get("/api/replays/{rid}")
def replay(rid:str):
    if not all(c.isalnum() or c=="_" for c in rid): raise HTTPException(400,"Invalid replay ID")
    if rid in matches: return matches[rid].replay()
    path=DATA/"replays"/(rid+".json")
    if not path.is_file(): raise HTTPException(404,"Replay not found")
    return FileResponse(path,media_type="application/json",filename="arena-"+rid+".json")


@app.get("/api/examples/{name}")
def example(name:str):
    allowed={"starter_bot.py":ROOT/"examples/starter_bot.py","parameter_bot.py":ROOT/"examples/parameter_bot.py","learned_bot.py":ROOT/"examples/learned_bot.py","model.json":DATA/"models/model.json","training_report.json":DATA/"models/training_report.json"}
    if name not in allowed or not allowed[name].exists(): raise HTTPException(404,"Run the training example first to generate this artifact")
    return FileResponse(allowed[name],filename=name)


@app.get("/api/guides")
def guide_index():
    return [{"id":key,"path":path,"title":title} for key,(path,title) in GUIDES.items()]


@app.get("/api/guides/{name}")
def guide(name:str,download:bool=False):
    if name not in GUIDES:
        raise HTTPException(404,"Guide not found")
    relative,title=GUIDES[name]
    path=ROOT/relative
    if not path.is_file():
        raise HTTPException(404,"Guide not found")
    if download:
        return FileResponse(path,media_type="text/markdown",filename=path.name)
    return {"id":name,"path":relative,"title":title,"content":path.read_text(encoding="utf-8")}


if (ROOT/"dist").exists():
    app.mount("/",StaticFiles(directory=ROOT/"dist",html=True),name="viewer")

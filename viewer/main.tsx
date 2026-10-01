import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Swords, FlaskConical, Bot, BookOpen, Play, Pause, SkipForward, Upload, ChevronRight, ArrowUpRight, Shuffle, Crosshair, Radio, Download, X, Plus, Check, AlertCircle, Square, Eye, RotateCcw, Cpu, Zap, Trophy, Shield, Heart, Target, FileCode2 } from 'lucide-react';
import './style.css';

type BotInfo = {id:string; name:string; style:string; version?:string; color:string};
type Player = {id:number; name:string; x:number; y:number; hp:number; alive:boolean; weapon:string; cooldown:number; shield:boolean; kills:number; suicides:number; protection:number};
type Entity = {x:number;y:number;[key:string]:any};
type State = {tick:number;seed:number;mode:string;max_ticks:number;board:string[][];players:Player[];bombs:Entity[];projectiles:Entity[];flames:Entity[];pickups:Entity[];events:any[];done:boolean;winner:number|null;result:string|null;supply_drop:Entity|null;visible?:boolean[][]};
const colors=['#79e9b0','#ff937c','#bda4ff','#f4d779'];
const fmt=(v:number)=>Number.isFinite(v)?v.toFixed(1):'—';
async function api(path:string, options?:RequestInit) {
  const r=await fetch('/api'+path,options);
  if(!r.ok){const e=await r.json().catch(()=>({detail:r.statusText}));throw new Error(typeof e.detail==='string'?e.detail:JSON.stringify(e.detail));}
  return r.json();
}
const post=(path:string,body:any)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
function download(data:any,name:string){const u=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download=name;a.click();URL.revokeObjectURL(u);}

function ArenaCanvas({state}:{state:State|null}) {
  const canvas=useRef<HTMLCanvasElement>(null);
  const current=useRef(state);const previous=useRef<State|null>(null);const changed=useRef(performance.now());
  useEffect(()=>{previous.current=current.current;current.current=state;changed.current=performance.now();},[state]);
  useEffect(()=>{
    let frame=0;
    const render=(now:number)=>{
      const c=canvas.current;const s=current.current;
      if(c&&s){
        const ctx=c.getContext('2d')!;const z=40;ctx.imageSmoothingEnabled=false;
        ctx.fillStyle='#141f25';ctx.fillRect(0,0,600,600);
        for(let y=0;y<15;y++)for(let x=0;x<15;x++){
          const px=x*z,py=y*z,t=s.board[y][x];
          ctx.fillStyle=(x+y)%2?'#1b2a30':'#1d2d33';ctx.fillRect(px,py,z,z);
          ctx.fillStyle='#273940';ctx.fillRect(px+5,py+7,2,2);ctx.fillRect(px+31,py+29,2,2);
          ctx.strokeStyle='#24343b';ctx.strokeRect(px+.5,py+.5,z-1,z-1);
          if(t==='#'){
            ctx.fillStyle='#101b21';ctx.fillRect(px+2,py+5,36,34);
            ctx.fillStyle='#3b5057';ctx.fillRect(px+2,py+2,36,31);
            ctx.fillStyle='#4c646b';ctx.fillRect(px+2,py+2,36,4);ctx.fillRect(px+2,py+6,3,24);
            ctx.fillStyle='#30444c';ctx.fillRect(px+7,py+10,25,18);
            ctx.fillStyle='#60757a';ctx.fillRect(px+7,py+10,3,3);ctx.fillRect(px+29,py+25,3,3);
          }else if(t==='+'){
            ctx.fillStyle='#142027';ctx.fillRect(px+5,py+7,32,31);
            ctx.fillStyle='#836746';ctx.fillRect(px+4,py+3,31,31);
            ctx.fillStyle='#bf9761';ctx.fillRect(px+4,py+3,31,4);ctx.fillRect(px+4,py+3,4,31);
            ctx.fillStyle='#a68254';ctx.fillRect(px+10,py+10,20,18);
            ctx.strokeStyle='#57452f';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(px+9,py+9);ctx.lineTo(px+30,py+29);ctx.moveTo(px+30,py+9);ctx.lineTo(px+9,py+29);ctx.stroke();
          }
        }
        if(s.supply_drop){const d=s.supply_drop;ctx.strokeStyle='#f4d779';ctx.setLineDash([4,4]);ctx.strokeRect(d.x*z+4,d.y*z+4,32,32);ctx.setLineDash([]);}
        for(const p of s.pickups){
          const x=p.x*z+20,y=p.y*z+20;ctx.fillStyle='#101b20';ctx.fillRect(x-12,y-9,25,24);
          ctx.fillStyle=p.kind==='health'?'#79e9b0':p.kind==='shield'?'#bda4ff':'#f4d779';ctx.fillRect(x-10,y-11,20,20);
          ctx.fillStyle='#17292d';
          if(p.kind==='health'){ctx.fillRect(x-2,y-7,4,13);ctx.fillRect(x-6,y-3,12,4);}
          else if(p.kind==='shield'){ctx.beginPath();ctx.moveTo(x-6,y-6);ctx.lineTo(x+6,y-6);ctx.lineTo(x+4,y+3);ctx.lineTo(x,y+7);ctx.lineTo(x-4,y+3);ctx.fill();}
          else{ctx.fillRect(x-5,y-6,7,6);ctx.fillRect(x-1,y-1,6,6);ctx.fillRect(x-3,y+5,3,3);}
        }
        for(const b of s.bombs){const x=b.x*z+20,y=b.y*z+20;ctx.fillStyle='#070d13';ctx.fillRect(x-11,y-8,23,20);ctx.fillRect(x-7,y-12,15,27);ctx.fillStyle=(Math.floor(now/160)%2)?'#ff947b':'#f3ce73';ctx.fillRect(x+2,y-16,5,5);ctx.fillStyle='#64767b';ctx.fillRect(x-6,y-7,5,4);ctx.fillStyle='#ffffff';ctx.font='10px monospace';ctx.textAlign='center';ctx.fillText(Math.max(0,(b.explode_at-s.tick)*.2).toFixed(1),x,y+7);}
        for(const p of s.players){
          if(!p.alive)continue;
          const old=previous.current?.players.find(q=>q.id===p.id);const t=Math.min(1,(now-changed.current)/120);
          const near=old&&Math.abs(old.x-p.x)+Math.abs(old.y-p.y)<=1;
          const x=((near?old.x+(p.x-old.x)*t:p.x)*z)+20,y=((near?old.y+(p.y-old.y)*t:p.y)*z)+20;
          const col=colors[p.id];ctx.fillStyle='#0a141b';ctx.fillRect(x-12,y+9,25,8);
          ctx.fillStyle=col;ctx.fillRect(x-10,y-12,20,17);ctx.fillRect(x-13,y-8,26,10);ctx.fillRect(x-8,y+4,16,9);
          ctx.fillStyle='#f1fff8';ctx.fillRect(x-8,y-12,15,3);ctx.fillStyle='#152a30';ctx.fillRect(x-8,y-5,16,7);
          ctx.fillStyle=col;ctx.fillRect(x-5,y-3,3,2);ctx.fillRect(x+3,y-3,3,2);
          ctx.fillStyle='#344b50';ctx.fillRect(x-8,y+11,6,5);ctx.fillRect(x+3,y+11,6,5);
          ctx.fillStyle=p.weapon==='bomb'?'#f4d779':'#c8d9dc';ctx.fillRect(x+10,y+2,6,5);
          if(p.shield||p.protection){ctx.strokeStyle=p.protection?'#ffffff':'#bda4ff';ctx.lineWidth=1;ctx.strokeRect(x-16,y-17,32,36);}
          for(let h=0;h<3;h++){ctx.fillStyle=h<p.hp?col:'#33454b';ctx.fillRect(x-10+h*8,y-19,6,3);}
        }
        for(const b of s.projectiles){ctx.fillStyle=colors[b.owner];ctx.fillRect(b.x*z+15,b.y*z+15,10,10);ctx.fillStyle='#ffffdf';ctx.fillRect(b.x*z+18,b.y*z+18,4,4);}
        for(const f of s.flames){ctx.fillStyle='#ff8e54';ctx.fillRect(f.x*z+3,f.y*z+3,34,34);ctx.fillStyle='#ffd76e';ctx.fillRect(f.x*z+10,f.y*z+8,20,24);ctx.fillStyle='#fff1b2';ctx.fillRect(f.x*z+16,f.y*z+14,8,12);}
        if(s.visible)for(let y=0;y<15;y++)for(let x=0;x<15;x++)if(!s.visible[y][x]){ctx.fillStyle='rgba(5,12,19,.78)';ctx.fillRect(x*z,y*z,z,z);}
      }
      frame=requestAnimationFrame(render);
    };frame=requestAnimationFrame(render);return()=>cancelAnimationFrame(frame);
  },[]);
  return <canvas ref={canvas} width={600} height={600} aria-label="Live 15 by 15 battle arena"/>;
}

function App(){
  const [tab,setTab]=useState('Arena');const [bots,setBots]=useState<BotInfo[]>([]);const [ids,setIds]=useState(['survivor','hunter']);
  const [seed,setSeed]=useState(42);const [mode,setMode]=useState('elimination');const [state,setState]=useState<State|null>(null);
  const [mid,setMid]=useState<string|null>(null);const [views,setViews]=useState<Record<string,any>>({});const [perspective,setPerspective]=useState('all');
  const [paused,setPaused]=useState(false);const [speed,setSpeed]=useState(1);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const [botErrors,setBotErrors]=useState<Record<string,string>>({});const [feed,setFeed]=useState<any[]>([]);
  const [uploadOpen,setUploadOpen]=useState(false);const [botName,setBotName]=useState('');const [botFile,setBotFile]=useState<File|null>(null);const [modelFile,setModelFile]=useState<File|null>(null);const [trusted,setTrusted]=useState(false);
  const [candidate,setCandidate]=useState('survivor');const [opponents,setOpponents]=useState(['hunter']);const [games,setGames]=useState(12);const [evalSeed,setEvalSeed]=useState(10000);const [evalMode,setEvalMode]=useState('elimination');
  const [jobs,setJobs]=useState<any[]>([]);const [selectedJob,setSelectedJob]=useState<string|null>(null);
  const [replay,setReplay]=useState<any>(null);const [replayIndex,setReplayIndex]=useState(0);const [replayPlaying,setReplayPlaying]=useState(false);
  const socket=useRef<WebSocket|null>(null);const importRef=useRef<HTMLInputElement>(null);
  const active=!!mid&&!state?.done&&!replay;
  const notify=(e:any)=>setError(e.message||String(e));
  useEffect(()=>{api('/bots').then(setBots).catch(notify);return()=>socket.current?.close();},[]);
  useEffect(()=>{
    if(mid||replay)return;
    const controller=new AbortController();
    api(`/preview?seed=${seed}&mode=${mode}&participants=${ids.join(',')}`,{signal:controller.signal}).then(setState).catch(e=>{if(e.name!=='AbortError')notify(e)});
    return()=>controller.abort();
  },[ids,seed,mode,mid,replay]);
  useEffect(()=>{
    if(tab!=='Training Lab')return;
    let live=true;const refresh=()=>api('/evaluations').then(j=>{if(live)setJobs(j)}).catch(notify);
    refresh();const timer=setInterval(refresh,1200);return()=>{live=false;clearInterval(timer)};
  },[tab]);
  useEffect(()=>{
    if(!replay||!replayPlaying)return;
    const timer=setInterval(()=>setReplayIndex(i=>{if(i>=replay.frames.length-1){setReplayPlaying(false);return i;}return i+1;}),200/speed);
    return()=>clearInterval(timer);
  },[replay,replayPlaying,speed]);
  useEffect(()=>{
    if(!active||!ids.includes('human')||tab!=='Arena')return;
    const key=(e:KeyboardEvent)=>{
      if((e.target as HTMLElement).closest('input,select,textarea,button'))return;
      const map:Record<string,string>={ArrowUp:'move_n',ArrowDown:'move_s',ArrowLeft:'move_w',ArrowRight:'move_e',w:'move_n',s:'move_s',a:'move_w',d:'move_e',i:'fire_n',k:'fire_s',j:'fire_w',l:'fire_e',' ':'fire_n',q:'switch'};
      const action=map[e.key];if(action){e.preventDefault();post(`/matches/${mid}/action`,{action}).catch(notify);}
    };window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);
  },[active,ids,mid,tab]);
  async function start(){
    setBusy(true);setError('');
    try{
      if(mid&&!state?.done)await post(`/matches/${mid}/control`,{stop:true});
      socket.current?.close();setReplay(null);setReplayPlaying(false);setFeed([]);setBotErrors({});setSpeed(1);setPaused(false);
      const result=await post('/matches',{bots:ids,seed,mode});setMid(result.id);setState(result.state);setPerspective(ids.includes('human')?String(ids.indexOf('human')):'all');
      const ws=new WebSocket(`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/ws/matches/${result.id}`);socket.current=ws;
      let lastTick=-1;
      ws.onmessage=e=>{const p=JSON.parse(e.data);setState(p.state);setViews(p.views);setPaused(p.paused);setSpeed(p.speed);setBotErrors(p.errors);
        if(p.state.tick!==lastTick){setFeed(f=>[...f,...p.state.events].slice(-80));lastTick=p.state.tick;}
      };
      ws.onerror=()=>setError('Live connection interrupted. Stop and launch another match to reconnect.');
    }catch(e){notify(e)}finally{setBusy(false)}
  }
  async function control(body:any){if(!mid)return;try{const p=await post(`/matches/${mid}/control`,body);setPaused(p.paused);setSpeed(p.speed);}catch(e){notify(e)}}
  async function upload(e:React.FormEvent){e.preventDefault();if(!botFile)return;setBusy(true);setError('');try{
    const form=new FormData();form.append('name',botName||botFile.name.replace('.py',''));form.append('trusted',String(trusted));form.append('file',botFile);if(modelFile)form.append('model',modelFile);
    const b=await api('/bots/upload',{method:'POST',body:form});setBots(v=>[...v,b]);setIds(v=>[b.id,...v.slice(1)]);setCandidate(b.id);setUploadOpen(false);setBotFile(null);setModelFile(null);setTrusted(false);setBotName('');
  }catch(e){notify(e)}finally{setBusy(false)}}
  async function evaluate(){setBusy(true);setError('');try{const j=await post('/evaluations',{candidate,opponents,games,seed:evalSeed,mode:evalMode});setSelectedJob(j.id);setJobs(v=>[j,...v]);}catch(e){notify(e)}finally{setBusy(false)}}
  async function openReplay(rid:string){try{const r=await api('/replays/'+rid);if(active)await control({paused:true});setReplay(r);setReplayIndex(0);setReplayPlaying(true);setPerspective('all');setTab('Arena');}catch(e){notify(e)}}
  const shown=replay?replay.frames[replayIndex] as State:state;
  let display=shown;
  if(!replay&&shown&&perspective!=='all'&&views[perspective]){const o=views[perspective];display={...shown,board:o.board,players:[o.self,...o.opponents],bombs:o.bombs,projectiles:o.projectiles,flames:o.flames,pickups:o.pickups,visible:o.visible};}
  const job=jobs.find(j=>j.id===selectedJob)||jobs[0];const report=job?.report;
  const botOptions=(human=false)=> <>{bots.map(b=><option key={b.id} value={b.id}>{b.name}{b.version?' · '+b.version:''}</option>)}{human&&<option value="human">You · keyboard</option>}</>;
  const minutes=(ticks:number)=>`${Math.floor(ticks/5/60)}:${String(Math.floor(ticks/5)%60).padStart(2,'0')}`;
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#" onClick={e=>{e.preventDefault();setTab('Arena')}}><span className="brand-icon"><Bot size={25}/></span><span>BOT ARENA<small>BUILD. BATTLE. EVOLVE.</small></span></a>
      <div className="nav-label">WORKSPACE</div>
      <nav>{[[Swords,'Arena'],[FlaskConical,'Training Lab'],[Bot,'Bot Library'],[BookOpen,'Field Guide']].map(([Icon,name]:any)=><button key={name} className={tab===name?'nav-item active':'nav-item'} onClick={()=>{setTab(name);setError('')}}><Icon size={18}/>{name}{tab===name&&<span className="nav-dot"/>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="status-dot"/> LOCAL ENVIRONMENT<p>Your code. Your arena.</p><div className="version">PROTOTYPE <span>v0.1.0</span></div></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><span>Workspace <ChevronRight size={14}/> <strong>{tab}</strong></span><div><span className="engine-status"><i/> ENGINE CONNECTED</span><button className="icon-button" title="Open field guide" onClick={()=>setTab('Field Guide')}><BookOpen size={17}/></button></div></header>
      <main>
        <div className="page-heading"><div><div className="eyebrow">THE EXPERIMENT STARTS HERE</div><h1>{tab==='Arena'?'Let the bots battle.':tab==='Training Lab'?'Less guessing. More experiments.':tab==='Bot Library'?'Meet your competitors.':'From first move to first model.'}</h1><p>{tab==='Arena'?'Write a strategy. Drop it in. Watch it come to life.':tab==='Training Lab'?'Run repeatable benchmarks and turn every defeat into a better decision.':tab==='Bot Library'?'Start with a baseline, study an opponent, or bring your own intelligence.':'Everything you need to build, test, and train your first arena bot.'}</p></div><button className="button secondary" onClick={()=>setUploadOpen(true)}><Upload size={16}/> Upload bot</button></div>
        {error&&<div className="error-banner" role="alert"><AlertCircle size={17}/>{error}<button onClick={()=>setError('')} aria-label="Dismiss error"><X size={16}/></button></div>}
        {tab==='Arena'&&<>
          <div className="arena-layout">
            <section className="arena-card">
              <div className="section-header"><div><span className="live-dot"/>{replay?'MATCH REPLAY':active?(paused?'PAUSED':'LIVE ARENA'):'THE ARENA'}<span className="subtle"> / GRID 01</span></div><span className="chip">15 × 15</span></div>
              <div className="score-strip">{(shown?.players||[]).map(p=><div key={p.id} className={'score-player '+(!p.alive?'eliminated':'')}><span className="bot-mini" style={{color:colors[p.id]}}><Bot size={22}/></span><div><strong>{p.name}</strong><span>{Array.from({length:3},(_,i)=><Heart key={i} size={11} fill={i<p.hp?colors[p.id]:'none'} color={i<p.hp?colors[p.id]:'#4c6069'}/>)} {p.shield&&<Shield size={12} color="#bda4ff"/>}</span></div><b style={{color:colors[p.id]}}>{shown?.mode==='deathmatch'?p.kills-p.suicides:`P${p.id+1}`}</b></div>)}</div>
              <div className="board-wrap"><div className="board-coordinates"><span>A</span><span>D</span><span>G</span><span>J</span><span>M</span><span>O</span></div><ArenaCanvas state={display}/>{shown?.done&&!replay&&<div className="round-result"><Trophy size={25}/><strong>{shown.result==='stopped'?'MATCH STOPPED':shown.winner===null?'ROUND DRAW':shown.players.find(p=>p.id===shown.winner)?.name+' WINS'}</strong><span>{shown.tick} ticks · {minutes(shown.tick)} elapsed</span><button className="button primary" onClick={start}><RotateCcw size={15}/> Rematch</button></div>}</div>
              <div className="arena-bottom"><span><span className="mint">●</span> {replay?'RECORDED':mid?'SIMULATION':'READY TO LAUNCH'} <span className="subtle"> / SEED {shown?.seed??seed}</span></span><span>TICK <strong>{String(shown?.tick||0).padStart(3,'0')}</strong><span className="subtle"> / {shown?.max_ticks||450}</span></span></div>
              <div className="playback"><div className="playback-buttons"><button className="icon-button" aria-label={replay?(replayPlaying?'Pause replay':'Play replay'):(paused?'Resume match':'Pause match')} disabled={!mid&&!replay} onClick={()=>replay?setReplayPlaying(!replayPlaying):control({paused:!paused})}>{(replay?replayPlaying:active&&!paused)?<Pause size={17}/>:<Play size={17}/>}</button><button className="icon-button" aria-label="Advance one tick" disabled={!mid&&!replay} onClick={()=>replay?(setReplayPlaying(false),setReplayIndex(i=>Math.min(i+1,replay.frames.length-1))):control({step:true})}><SkipForward size={17}/></button></div>
                {replay?<input aria-label="Replay position" type="range" min={0} max={replay.frames.length-1} value={replayIndex} onChange={e=>{setReplayPlaying(false);setReplayIndex(+e.target.value)}}/>:<div className="timeline"><i style={{width:`${(shown?.tick||0)/(shown?.max_ticks||450)*100}%`}}/></div>}
                <select aria-label="Playback speed" className="speed-select" value={speed} onChange={e=>replay?setSpeed(+e.target.value):control({speed:+e.target.value})}>{[.5,1,2,5,10].map(s=><option key={s} value={s}>{s}×</option>)}</select><span className="time-left">{minutes(Math.max(0,(shown?.max_ticks||450)-(shown?.tick||0)))}</span>
              </div>
            </section>
            <aside className="match-panel">
              <section className="panel setup"><div className="section-header"><span><Crosshair size={16}/> MATCH SETUP</span><span className="tiny">01</span></div><div className="panel-body">
                <label>GAME MODE</label><div className="segmented"><button disabled={active} className={mode==='elimination'?'selected':''} onClick={()=>setMode('elimination')}>Elimination</button><button disabled={active} className={mode==='deathmatch'?'selected':''} onClick={()=>setMode('deathmatch')}>Deathmatch</button></div><p className="field-help">{mode==='elimination'?'One life. Last bot standing.':'Respawn. Regroup. Top the scoreboard.'}</p>
                <div className="label-row"><label>PARTICIPANTS</label><span>{ids.length} / 4</span></div>
                <div className="participants">{ids.map((id,i)=><div className="participant" key={i}><span className="player-index" style={{color:colors[i],borderColor:colors[i]+'45'}}>0{i+1}</span><div><select aria-label={`Player ${i+1}`} value={id} disabled={active} onChange={e=>setIds(v=>v.map((b,j)=>j===i?e.target.value:b))}>{botOptions(true)}</select><small>{id==='human'?'Keyboard controlled':bots.find(b=>b.id===id)?.style}</small></div>{i>1&&<button className="icon-button" disabled={active} aria-label={`Remove player ${i+1}`} onClick={()=>setIds(v=>v.filter((_,j)=>i!==j))}><X size={13}/></button>}</div>)}</div>
                {ids.length<4&&<button className="add-player" disabled={active} onClick={()=>setIds(v=>[...v,v.length===2?'bomber':'random'])}><Plus size={14}/> Add participant</button>}
                <div className="label-row seed-label"><label htmlFor="seed">MAP SEED</label><span>REPRODUCIBLE</span></div><div className="input-action"><input id="seed" type="number" value={seed} disabled={active} onChange={e=>setSeed(+e.target.value)}/><button disabled={active} aria-label="Randomize map seed" onClick={()=>setSeed(Math.floor(Math.random()*99999))}><Shuffle size={16}/></button></div>
                <button className="button primary launch" disabled={busy||active} onClick={start}><Play size={16} fill="currentColor"/>{busy?'Preparing…':active?'Match in progress':'Launch match'}<span>↗</span></button>
                {active&&<button className="text-button stop" onClick={()=>control({stop:true})}><Square size={12}/> Stop match</button>}
                {!active&&<p className="launch-caption"><Cpu size={12}/> Runs locally on your machine</p>}
              </div></section>
              <section className="panel view-panel"><div className="section-header"><span><Eye size={15}/> OBSERVER</span></div><div className="panel-body"><select aria-label="Observer perspective" value={perspective} disabled={!!replay||ids.includes('human')&&active} onChange={e=>setPerspective(e.target.value)}><option value="all">Full arena · spectator</option>{ids.map((id,i)=><option key={i} value={i}>P{i+1} · {id==='human'?'Your view':bots.find(b=>b.id===id)?.name}</option>)}</select><p className="field-help">{perspective==='all'?'See the whole match. Bots only see their line of sight.':'Dark tiles are remembered terrain. Unseen opponents are hidden.'}</p></div></section>
              <div className="lab-callout"><FlaskConical size={21}/><strong>One match is a story.<br/>A hundred is a dataset.</strong><button onClick={()=>setTab('Training Lab')}>Open Training Lab <ArrowUpRight size={15}/></button></div>
            </aside>
          </div>
          {ids.includes('human')&&active&&<div className="keyboard-hint">YOUR CONTROLS <kbd>W A S D</kbd> move <kbd>I J K L</kbd> fire direction <kbd>Q</kbd> switch weapon <span>Click the arena, then use your keyboard.</span></div>}
          {Object.keys(botErrors).length>0&&<div className="error-banner">{Object.entries(botErrors).map(([id,e])=><span key={id}>P{+id+1}: {e}. This bot now waits each tick.</span>)}</div>}
          <div className="lower-grid"><section className="panel log-panel"><div className="section-header"><span><Radio size={15}/> MATCH FEED</span><span className="tiny">{replay?'REPLAY EVENTS':'LIVE EVENTS'}</span></div><div className="log-body">{(replay?shown?.events:feed)?.length?(replay?shown!.events:feed).slice(-5).reverse().map((e:any,i:number)=><div key={i}><span className="log-tick">{String(e.tick).padStart(3,'0')}</span><i className={'event-dot '+e.kind}/><span>{e.text}</span></div>):<div className="empty-feed"><span className="log-tick">000</span><i className="event-dot"/><span>Arena initialized. Waiting for the first move.</span></div>}</div></section><section className="panel replay-panel"><div className="section-header"><span>KEEP THE EVIDENCE</span><Download size={15}/></div><p>Every decision, every explosion.<br/>Replay a match and find the turning point.</p><div><button className="button secondary small" disabled={!mid&&!replay} onClick={async()=>{try{download(replay||await api('/replays/'+mid),'arena-replay.json')}catch(e){notify(e)}}}><Download size={13}/> Save replay</button><button className="text-button" onClick={()=>importRef.current?.click()}>Load replay</button></div><input ref={importRef} hidden type="file" accept=".json" onChange={async e=>{const f=e.target.files?.[0];if(!f)return;try{const r=JSON.parse(await f.text());if(r.version!==1||!Array.isArray(r.frames)||!r.frames.length||r.frames.some((s:any)=>!Array.isArray(s.board)||s.board.length!==15||!Array.isArray(s.players)))throw new Error('Invalid arena replay');if(active)await control({paused:true});setReplay(r);setReplayIndex(0);setReplayPlaying(false);setPerspective('all');}catch(err){notify(err)}e.target.value='';}}/></section></div>
          <div className="legend"><span><i className="legend-box wall"/> Solid wall</span><span><i className="legend-box crate"/> Destructible crate</span><span><Heart size={13} color="#79e9b0"/> Health pack</span><span><Shield size={13} color="#bda4ff"/> Shield</span><span><Zap size={13} color="#f4d779"/> Battery</span><span className="legend-end">SMALL ARENA. BIG IDEAS.</span></div>
        </>}
        {tab==='Training Lab'&&<>
          <div className="lab-layout"><section className="panel"><div className="section-header"><span><FlaskConical size={16}/> EXPERIMENT CONFIGURATION</span></div><div className="panel-body lab-form"><label>CANDIDATE BOT</label><select value={candidate} onChange={e=>setCandidate(e.target.value)}>{botOptions()}</select><label>OPPONENTS · {opponents.length+1} PLAYERS</label>{opponents.map((o,i)=><div className="opponent-field" key={i}><select aria-label={`Evaluation opponent ${i+1}`} value={o} onChange={e=>setOpponents(v=>v.map((a,j)=>i===j?e.target.value:a))}>{botOptions()}</select>{i>0&&<button className="icon-button" onClick={()=>setOpponents(v=>v.filter((_,j)=>i!==j))}><X size={14}/></button>}</div>)}{opponents.length<3&&<button className="add-player" onClick={()=>setOpponents(v=>[...v,'bomber'])}><Plus size={14}/> Add opponent</button>}<div className="form-pair"><div><label>MATCHES</label><select value={games} onChange={e=>setGames(+e.target.value)}>{[4,12,20,40,100,200].map(n=><option key={n}>{n}</option>)}</select></div><div><label>SEED START</label><input type="number" value={evalSeed} onChange={e=>setEvalSeed(+e.target.value)}/></div></div><label>MODE</label><select value={evalMode} onChange={e=>setEvalMode(e.target.value)}><option value="elimination">Elimination</option><option value="deathmatch">Deathmatch</option></select><div className="experiment-note"><Shuffle size={17}/><span>Seats and spawn corners rotate automatically. Use the same configuration to compare versions.</span></div><button className="button primary launch" disabled={busy||jobs.some(j=>j.status==='running')} onClick={evaluate}><Play size={15}/>{jobs.some(j=>j.status==='running')?'Experiment running…':'Run experiment'}</button><p className="field-help">Evaluation measures a bot; it does not train one.</p></div></section>
            <section className="results-area">{!job?<div className="empty-results"><FlaskConical size={44}/><h2>Your next improvement starts here.</h2><p>Select a bot and an opponent, then run your first batch.<br/>Results include win-rate uncertainty and a replay for every match.</p><span className="chip">NO GPU REQUIRED</span></div>:<><div className="results-header"><div className="eyebrow">EXPERIMENT RESULTS</div><select aria-label="Experiment history" value={job.id} onChange={e=>setSelectedJob(e.target.value)}>{jobs.map(j=><option key={j.id} value={j.id}>{bots.find(b=>b.id===j.config.candidate)?.name||j.config.candidate} · {new Date(j.created_at*1000).toLocaleTimeString()} · {j.status}</option>)}</select></div><div className="experiment-progress"><span>{job.status==='failed'?'Experiment failed':job.status==='complete'?'Experiment complete':'Simulating without rendering…'}</span><b>{job.completed} / {job.total}</b><div><i style={{width:job.completed/job.total*100+'%'}}/></div></div>{job.error&&<div className="error-banner">{job.error}</div>}
              {report&&<><div className="metric-grid"><Metric label="WIN RATE" value={Math.round(report.win_rate*100)+'%'} note={`95% interval: ${Math.round(report.win_interval[0]*100)}–${Math.round(report.win_interval[1]*100)}%`}/><Metric label="RECORD" value={`${report.wins} / ${report.draws} / ${report.losses}`} note="Wins / draws / losses"/><Metric label="AVG. PLACEMENT" value={fmt(report.mean_placement)} note={`${job.config.opponents.length+1}-player free-for-all`}/></div><div className="panel diagnostics"><h3>Beyond the scoreboard</h3><div><span>Damage dealt / taken</span><strong>{fmt(report.averages.damage_dealt)} / {fmt(report.averages.damage_taken)}</strong></div><div><span>Average survival</span><strong>{fmt(report.averages.survival_ticks*.2)}s</strong></div><div><span>Self-inflicted bomb deaths / match</span><strong>{fmt(report.averages.self_bomb_deaths)}</strong></div><div><span>Invalid actions / timeouts per match</span><strong>{fmt(report.averages.invalid_actions)} / {fmt(report.averages.timeouts)}</strong></div><button className="text-button" onClick={()=>download(job,'evaluation-'+job.id+'.json')}><Download size={14}/> Export results</button></div></>}
              <section className="panel match-table"><div className="section-header"><span>MATCH HISTORY</span><span className="tiny">CLICK TO INVESTIGATE</span></div><table><thead><tr><th>MATCH</th><th>SEED</th><th>RESULT</th><th>TIME</th><th/></tr></thead><tbody>{job.rows?.map((r:any)=><tr key={r.index}><td>#{String(r.index+1).padStart(2,'0')}</td><td>{r.seed}</td><td><span className={'outcome '+r.outcome}>{r.outcome}</span></td><td>{minutes(r.ticks)}</td><td><button className="text-button" onClick={()=>openReplay(r.replay_id)}>Replay <ArrowUpRight size={13}/></button></td></tr>)}</tbody></table></section>
            </>}</section></div>
          <section className="panel ml-callout"><div><span className="eyebrow">THE NEXT STEP</span><h2>Teach a bot to make decisions.</h2><p>Our CPU training example learns tactical choices from Sentinel, then tests the learned policy against three reference opponents on unseen seeds.</p></div><button className="button secondary" onClick={()=>setTab('Field Guide')}>Start the ML example <ArrowUpRight size={15}/></button></section>
        </>}
        {tab==='Bot Library'&&<><div className="bot-grid">{bots.map((b,i)=><article className="panel bot-card" key={b.id}><div className="bot-card-top"><span className="large-bot" style={{color:b.color||colors[i%4]}}><Bot size={40}/></span><span className="chip">{b.version?'YOUR BOT':'REFERENCE'}</span></div><h2>{b.name}</h2><div className="bot-style">{b.style}</div><p>{({random:'An unpredictable first opponent. Beat it consistently before raising the stakes.',hunter:'Looks for clear shots and closes the distance. Keep moving.',survivor:'Balances escape, supplies and attack. The teacher for our learning example.',bomber:'Opens routes and sets traps. Keep an eye on the countdown.'} as Record<string,string>)[b.id]||'Your uploaded strategy, validated and ready to enter the arena.'}</p><button className="text-button" onClick={()=>{if(active){setError('Stop the active match before changing participants.');return;}setIds(v=>[b.id,...v.slice(1)]);setTab('Arena')}}>Send to arena <ArrowUpRight size={15}/></button></article>)}<button className="upload-card" onClick={()=>setUploadOpen(true)}><Plus size={32}/><strong>Your next contender</strong><span>Upload a Python bot and optional model</span></button></div><div className="panel ml-callout"><div><h2>A small interface. Room for big ideas.</h2><p>One Python class. One observation. One action. Start with rules, then experiment with learning.</p></div><a className="button secondary" href="/api/examples/starter_bot.py"><Download size={15}/> Starter bot</a></div></>}
        {tab==='Field Guide'&&<div className="guide-grid"><section className="panel guide"><span className="eyebrow">01 / THE GAME</span><h2>Know the rules.</h2><p>Every 200 ms, all players choose one action together: move, switch weapons, fire, or wait. Each player starts with 3 HP, a blaster and a bomb weapon.</p><ul><li>Blasters deal 1 damage; cooldown: 1 second.</li><li>Bombs deal 2 damage; fuse: 2 seconds; range: 3 tiles. One active bomb per player.</li><li>Bombs hurt their owner, destroy crates and chain into other bombs.</li><li>Walls and crates block sight. Memory of unseen terrain may be stale.</li><li>Elimination lasts 90 seconds. Unresolved rounds are draws.</li><li>Deathmatch lasts 3 minutes. Kills minus suicides determines the winner.</li></ul><div className="experiment-note"><Eye size={19}/><span>All competitors receive their own filtered observation. Human play uses the same visibility rules.</span></div></section><section className="panel guide"><span className="eyebrow">02 / YOUR FIRST BOT</span><h2>Make your first move.</h2><pre>{`class Bot:\n    def choose_action(self, observation):\n        me = observation["self"]\n        enemies = observation["opponents"]\n        return "move_e"`}</pre><p>Use instance variables for memory. Return <code>wait</code>, <code>switch</code>, <code>move_n/s/e/w</code>, or <code>fire_n/s/e/w</code>. When the bomb weapon is equipped, any fire action places a bomb.</p><a className="button secondary" href="/api/examples/starter_bot.py"><Download size={15}/> Download starter</a><p className="field-help">Uploaded code runs locally in a separate process with a 100 ms decision deadline. Only upload code you trust.</p></section><section className="panel guide wide"><span className="eyebrow">03 / WORKING ML EXAMPLE</span><h2>Learn tactical decisions. Measure actual performance.</h2><div className="learning-steps"><div><b>01</b><h3>Collect</h3><p>Record Sentinel’s choices: escape, attack, seek supplies or explore.</p></div><div><b>02</b><h3>Train</h3><p>Fit a small decision tree to observations. Validation uses separate matches and seeds.</p></div><div><b>03</b><h3>Evaluate</h3><p>Test teacher and learner against Wanderer, Deadeye and Fuse on unseen seeds.</p></div></div><pre>python -m arena.train --games 20</pre><p>Run from the project directory with your Python environment activated. The script writes <code>data/models/model.json</code> and <code>training_report.json</code>. Upload the learned bot below with that JSON model. Better imitation accuracy does not guarantee more wins.</p><div className="guide-downloads"><a className="button secondary" href="/api/examples/learned_bot.py"><FileCode2 size={15}/> Learned bot</a><a className="button secondary" href="/api/examples/model.json"><Download size={15}/> Latest model</a><a className="text-button" href="/api/examples/training_report.json">Training report <ArrowUpRight size={14}/></a></div><p className="field-help">Model and report downloads become available after running the training script.</p></section></div>}
        <footer><span><span className="mint">▦</span> BOT ARENA <span className="subtle">/ An open playground for intelligent agents</span></span><span>BUILT TO EXPERIMENT.</span></footer>
      </main>
    </div>
    {uploadOpen&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setUploadOpen(false)}}><form className="modal" onSubmit={upload}><div className="modal-heading"><span className="eyebrow">NEW CONTENDER</span><button type="button" className="icon-button" aria-label="Close upload dialog" onClick={()=>setUploadOpen(false)}><X size={20}/></button></div><h2>Bring your bot.</h2><p>Upload your strategy and put it to the test.</p><label htmlFor="bot-name">BOT NAME</label><input id="bot-name" value={botName} maxLength={32} placeholder="e.g. Circuit Breaker" onChange={e=>setBotName(e.target.value)}/><label htmlFor="bot-file">PYTHON BOT · REQUIRED</label><input id="bot-file" type="file" accept=".py" required onChange={e=>setBotFile(e.target.files?.[0]||null)}/><label htmlFor="model-file">MODEL ARTIFACT · OPTIONAL JSON</label><input id="model-file" type="file" accept=".json" onChange={e=>setModelFile(e.target.files?.[0]||null)}/><label className="trust-check"><input type="checkbox" checked={trusted} required onChange={e=>setTrusted(e.target.checked)}/><span>I trust this code. Python bots execute on this computer; process isolation is not a security sandbox.</span></label>{error&&<div className="error-banner">{error}</div>}<button className="button primary launch" disabled={busy||!trusted||!botFile}><Upload size={16}/>{busy?'Validating bot…':'Validate & add bot'}</button><a className="text-button" href="/api/examples/starter_bot.py">Need a starting point? Download the template <ArrowUpRight size={14}/></a></form></div>}
  </div>;
}
function Metric({label,value,note}:{label:string;value:string;note:string}){return <div className="panel metric"><span>{label}</span><strong>{value}</strong><small>{note}</small></div>}
createRoot(document.getElementById('root')!).render(<App/>);

import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from .bots import BUILTINS
from .engine import Game
from .sdk import ACTIONS, RULES_VERSION

ROOT=Path(__file__).resolve().parents[1]


class ExternalBot:
    def __init__(self,path):
        self.error=None
        self.closed=False
        self.proc=subprocess.Popen([sys.executable,"-u",str(ROOT/"arena/worker.py"),str(path)],
                                   stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd=str(Path(path).parent))
        self.responses=queue.Queue(maxsize=4)
        self.reader=threading.Thread(target=self._read_output,daemon=True)
        self.reader.start()
        ready=self.receive(time.monotonic()+5)
        if not ready.get("ready"):
            error=ready.get("error","Bot failed to initialize")
            self.close()
            raise ValueError(error)

    def send(self,obs):
        if self.error: return
        try:
            self.proc.stdin.write((json.dumps(obs)+"\n").encode())
            self.proc.stdin.flush()
        except (BrokenPipeError,OSError):
            self.error="Bot process exited"

    def _read_output(self):
        """Thread-backed pipes work on both Windows and POSIX."""
        try:
            while True:
                line=self.proc.stdout.readline(65537)
                if not line:
                    self.responses.put_nowait({"error":"Bot process exited"})
                    return
                if len(line)>65536:
                    self.responses.put_nowait({"error":"Bot response too large"})
                    return
                try:
                    response=json.loads(line)
                    if not isinstance(response,dict): raise ValueError()
                except (ValueError,TypeError):
                    response={"error":"Invalid bot response"}
                self.responses.put_nowait(response)
        except (OSError,ValueError,queue.Full):
            return

    def receive(self,deadline):
        try:
            return self.responses.get(timeout=max(0,deadline-time.monotonic()))
        except queue.Empty:
            self.error="Decision timed out"
            self.close()
            return {"error":self.error}

    def close(self):
        if self.closed: return
        self.closed=True
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=2)
        self.reader.join(timeout=.2)
        for stream in (self.proc.stdin,self.proc.stdout):
            if stream: stream.close()


class Match:
    def __init__(self, bot_ids, registry=None, seed=42, mode="elimination", rotation=0, max_ticks=None, record=True):
        registry=registry or {}
        self.bot_ids=bot_ids
        self.rotation=rotation
        self.bots=[]
        self.record=record
        self.errors={}
        try:
            for bid in bot_ids:
                self.bots.append(None if bid=="human" else BUILTINS[bid]() if bid in BUILTINS else ExternalBot(registry[bid]["path"]))
        except Exception:
            self.close()
            raise
        names=["YOU" if b=="human" else registry.get(b,{}).get("name",{"random":"Wanderer","hunter":"Deadeye","survivor":"Sentinel","bomber":"Fuse"}.get(b,b)) for b in bot_ids]
        self.game=Game(names,seed,mode,max_ticks,rotation)
        self.frames=[self.game.snapshot()] if record else []
        self.action_log=[]
        self.inputs={}
        self.paused=False
        self.speed=1

    def step(self):
        g=self.game
        if g.done: return g.snapshot()
        observations={p.id:g.observe(p.id) for p in g.players if p.alive}
        actions={}
        for pid,obs in observations.items():
            bot=self.bots[pid]
            if isinstance(bot,ExternalBot) and not bot.error:
                bot.send(obs)
        deadline=time.monotonic()+.1
        for pid,obs in observations.items():
            bot=self.bots[pid]
            try:
                if bot is None: action=self.inputs.pop(pid,"wait")
                elif isinstance(bot,ExternalBot):
                    if bot.error:
                        action="wait"
                        self.errors[pid]=bot.error
                    else:
                        response=bot.receive(deadline)
                        if "error" in response:
                            bot.error=response["error"]
                            self.errors[pid]=bot.error
                            if "timed out" in bot.error: g.players[pid].timeouts+=1
                            action="wait"
                        else: action=response.get("action","wait")
                else: action=bot.choose_action(obs)
                actions[pid]=action if isinstance(action,str) else "invalid"
            except Exception as exc:
                self.errors[pid]=str(exc)[:200]
                actions[pid]="invalid"
        state=g.step(actions)
        if self.record:
            self.action_log.append(actions)
            self.frames.append(state)
        if g.done: self.close()
        return state

    def run(self):
        while not self.game.done: self.step()
        return self.game.snapshot()

    def replay(self):
        return {"version":1,"rules_version":RULES_VERSION,"bot_ids":self.bot_ids,"seed":self.game.seed,"mode":self.game.mode,
                "rotation":self.rotation,"max_ticks":self.game.max_ticks,
                "actions":self.action_log,"frames":self.frames,"errors":self.errors}

    def close(self):
        for bot in self.bots:
            if isinstance(bot,ExternalBot): bot.close()

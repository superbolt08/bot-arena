"""Pure, seeded game state. Rendering, wall time and bot execution live elsewhere."""
import copy
import random
from collections import Counter, deque
from dataclasses import dataclass, asdict
from typing import Optional

from .sdk import ACTIONS, DIRECTIONS, BOMB_FUSE_TICKS, BOMB_FLAME_TICKS, BOMB_DAMAGE, bomb_blast_tiles

SIZE = 15
TICK_SECONDS = .2
COLORS = ["#70f0ba", "#ff8b73", "#bca0ff", "#ffdc74"]


@dataclass
class Player:
    id: int
    name: str
    x: int
    y: int
    hp: int = 3
    weapon: str = "blaster"
    cooldown: int = 0
    shield: bool = False
    alive: bool = True
    protection: int = 0
    respawn_at: Optional[int] = None
    kills: int = 0
    suicides: int = 0
    deaths: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    self_bomb_deaths: int = 0
    survival_ticks: int = 0
    invalid_actions: int = 0
    timeouts: int = 0


def line_visible(board, start, end, opaque=()):
    """Supercover ray: terrain and optional opaque entities occlude beyond themselves."""
    opaque=set(opaque)
    x, y = start
    tx, ty = end
    dx, dy = tx - x, ty - y
    nx, ny = abs(dx), abs(dy)
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    ix = iy = 0
    while ix < nx or iy < ny:
        cross = (1 + 2 * ix) * ny - (1 + 2 * iy) * nx
        if cross == 0:
            side_cells=((x+sx,y),(x,y+sy))
            if any(board[cy][cx] != "." or (cx,cy) in opaque for cx,cy in side_cells):
                return False
            x += sx
            y += sy
            ix += 1
            iy += 1
        elif cross < 0:
            x += sx
            ix += 1
        else:
            y += sy
            iy += 1
        if (x, y) == (tx, ty):
            return True
        if board[y][x] != "." or (x,y) in opaque:
            return False
    return True


class Game:
    def __init__(self, names, seed=42, mode="elimination", max_ticks=None, rotation=0):
        if not 2 <= len(names) <= 4:
            raise ValueError("Choose two, three or four participants")
        if mode not in ("elimination", "deathmatch"):
            raise ValueError("Unknown game mode")
        self.seed, self.mode = seed, mode
        self.rng = random.Random(seed)
        self.tick = 0
        self.max_ticks = max_ticks or (450 if mode == "elimination" else 900)
        self.board = self._map()
        corners = [(1, 1), (13, 13), (13, 1), (1, 13)]
        # Four rotations of these slots cover all corners, including 3-player games.
        def rotate(pos):
            x, y = pos
            for _ in range(rotation % 4):
                x, y = 14 - y, x
            return x, y
        self.players = [Player(i, name, *rotate(corners[i])) for i, name in enumerate(names)]
        self.initial_board = copy.deepcopy(self.board)
        self.memories = [copy.deepcopy(self.board) for _ in names]
        self.last_seen = [[[-1] * SIZE for _ in range(SIZE)] for _ in names]
        self.pickups = {}
        for x, y, kind in [(7, 1, "health"), (7, 13, "health"), (1, 7, "shield"), (13, 7, "battery")]:
            self.board[y][x] = "."
            self.pickups[(x, y)] = kind
        self.initial_board = copy.deepcopy(self.board)
        self.memories = [copy.deepcopy(self.board) for _ in names]
        self.bombs = []
        self.projectiles = []
        self.flames = []
        self._explosion_sequence = 0
        self._explosion_hits = {}
        self.events = []
        self.history = []
        self.done = False
        self.winner = None
        self.result = None
        self.drop = None

    def _map(self):
        board = [["#" if x in (0, 14) or y in (0, 14) or (x % 2 == 0 and y % 2 == 0) else "."
                  for x in range(SIZE)] for y in range(SIZE)]
        # Rotationally symmetric crates; permanent traversable cross prevents sealed arenas.
        for y in range(1, 14):
            for x in range(1, 14):
                if (y, x) > (14-y, 14-x):
                    continue
                safe = min(abs(x-a)+abs(y-b) for a,b in [(1,1),(13,13),(13,1),(1,13)]) <= 2
                if board[y][x] == "." and not safe and x != 7 and y != 7 and self.rng.random() < .28:
                    board[y][x] = board[14-y][14-x] = "+"
        # Clear routes from all spawns to the central cross.
        for x in range(1,14):
            board[1][x] = board[13][x] = "."
        return board

    def event(self, text, kind="info"):
        e = {"tick": self.tick, "text": text, "kind": kind}
        self.events.append(e)
        self.history.append(e)

    def blast_tiles(self, bomb, board=None):
        return bomb_blast_tiles(bomb, self.board if board is None else board)

    def observe(self, pid, full=False):
        p = self.players[pid]
        visible = [[bool(full or (p.alive and line_visible(self.board, (p.x,p.y),(x,y))))
                    for x in range(SIZE)] for y in range(SIZE)]
        screens={(q.x,q.y) for q in self.players if q.id!=pid and q.alive}
        entity_visible = [[bool(full or (p.alive and line_visible(self.board, (p.x,p.y),(x,y),screens)))
                           for x in range(SIZE)] for y in range(SIZE)]
        for y in range(SIZE):
            for x in range(SIZE):
                if visible[y][x]:
                    self.memories[pid][y][x] = self.board[y][x]
                    self.last_seen[pid][y][x] = self.tick
        seen = lambda obj: entity_visible[obj["y"]][obj["x"]]
        return {
            "tick": self.tick, "seed": self.seed, "mode": self.mode, "max_ticks": self.max_ticks,
            "self": asdict(p), "board": copy.deepcopy(self.memories[pid]),
            "visible": visible, "entity_visible": entity_visible,
            "last_seen": copy.deepcopy(self.last_seen[pid]),
            "opponents": [asdict(q) for q in self.players if q.id != pid and q.alive and entity_visible[q.y][q.x]],
            "bombs": [dict(b) for b in self.bombs if seen(b)],
            "projectiles": [dict(b) for b in self.projectiles if seen(b)],
            "flames": [dict(b) for b in self.flames if seen(b)],
            "pickups": [{"x":x,"y":y,"kind":k} for (x,y),k in self.pickups.items() if entity_visible[y][x]],
            "supply_drop": copy.deepcopy(self.drop), "actions": list(ACTIONS),
        }

    def snapshot(self):
        return {"tick":self.tick,"seed":self.seed,"mode":self.mode,"max_ticks":self.max_ticks,
                "board":copy.deepcopy(self.board),"players":[asdict(p) for p in self.players],
                "bombs":copy.deepcopy(self.bombs),"projectiles":copy.deepcopy(self.projectiles),
                "flames":copy.deepcopy(self.flames),
                "pickups":[{"x":x,"y":y,"kind":k} for (x,y),k in self.pickups.items()],
                "events":self.events[-8:],"done":self.done,"winner":self.winner,"result":self.result,
                "supply_drop":copy.deepcopy(self.drop)}

    def step(self, actions):
        if self.done:
            return self.snapshot()
        self.tick += 1
        self.events = []
        self.flames = [f for f in self.flames if f["expires_at"] > self.tick]
        active_explosions = {f["explosion_id"] for f in self.flames}
        self._explosion_hits = {eid: hit for eid, hit in self._explosion_hits.items() if eid in active_explosions}
        for p in self.players:
            p.cooldown = max(0,p.cooldown-1)
            p.protection = max(0,p.protection-1)
            if not p.alive and self.mode == "deathmatch" and p.respawn_at is not None and self.tick >= p.respawn_at:
                occupied = {(q.x,q.y) for q in self.players if q.alive}
                hazards = {cell for b in self.bombs for cell in self.blast_tiles(b)}
                hazards.update((b["x"],b["y"]) for b in self.projectiles)
                hazards.update((f["x"],f["y"]) for f in self.flames)
                floors = [(x,y) for y in range(1,14) for x in range(1,14)
                          if self.board[y][x]=="." and (x,y) not in occupied | hazards]
                if floors:
                    self.rng.shuffle(floors)
                    p.x,p.y = max(floors,key=lambda c:min([abs(c[0]-q.x)+abs(c[1]-q.y) for q in self.players if q.alive] or [99]))
                    p.hp,p.alive,p.protection,p.respawn_at,p.weapon,p.shield = 3,True,10,None,"blaster",False
                    self.event(p.name+" respawned")
            if p.alive:
                p.survival_ticks += 1
        alive = [p for p in self.players if p.alive]
        chosen = {}
        for p in alive:
            a = actions.get(p.id,"wait")
            if a not in ACTIONS:
                p.invalid_actions += 1
                a = "wait"
            chosen[p.id] = a
        targets = {p.id:(p.x,p.y) for p in alive}
        bomb_cells = {(b["x"],b["y"]) for b in self.bombs}
        for p in alive:
            a = chosen[p.id]
            if a.startswith("move_"):
                dx,dy = DIRECTIONS[a[-1]]
                x,y = p.x+dx,p.y+dy
                if 0<=x<SIZE and 0<=y<SIZE and self.board[y][x]=="." and (x,y) not in bomb_cells:
                    targets[p.id] = (x,y)
        counts = Counter(targets.values())
        blocked = {p.id for p in alive if counts[targets[p.id]] > 1}
        for p in alive:
            for q in alive:
                if p.id != q.id and targets[p.id]==(q.x,q.y) and targets[q.id]==(p.x,p.y):
                    blocked.update((p.id,q.id))
        # A failed mover continues occupying its original tile, possibly blocking a chain.
        while True:
            more = {p.id for p in alive if any(targets[p.id]==(q.x,q.y) for q in alive if q.id in blocked and q.id!=p.id)}
            if more <= blocked:
                break
            blocked |= more
        for p in alive:
            if p.id not in blocked:
                p.x,p.y = targets[p.id]
        for p in alive:
            a = chosen[p.id]
            if a == "switch":
                p.weapon = "bomb" if p.weapon=="blaster" else "blaster"
            elif a.startswith("fire_"):
                p.protection = 0
                if p.weapon == "bomb":
                    if not any(b["owner"]==p.id for b in self.bombs) and (p.x,p.y) not in bomb_cells:
                        self.bombs.append({"x":p.x,"y":p.y,"owner":p.id,"explode_at":self.tick+BOMB_FUSE_TICKS})
                        self.event(p.name+" planted a bomb","bomb")
                elif p.cooldown == 0:
                    dx,dy = DIRECTIONS[a[-1]]
                    self.projectiles.append({"x":p.x,"y":p.y,"dx":dx,"dy":dy,"owner":p.id})
                    p.cooldown = 5
            kind = self.pickups.get((p.x,p.y))
            if kind and (kind!="health" or p.hp<3) and (kind!="shield" or not p.shield):
                self.pickups.pop((p.x,p.y))
                if kind=="health": p.hp=min(3,p.hp+1)
                if kind=="shield": p.shield=True
                if kind=="battery": p.cooldown=0
                self.event(p.name+" collected "+kind,"pickup")
        hits = {p.id:[] for p in alive}
        remaining = []
        for shot in self.projectiles:
            old = (shot["x"],shot["y"])
            shot["x"] += shot["dx"]
            shot["y"] += shot["dy"]
            x,y = shot["x"],shot["y"]
            # Moving onto an existing projectile also counts as a collision.
            victims = [p for p in alive if p.id!=shot["owner"] and (p.x,p.y) in (old,(x,y))]
            if victims:
                for p in victims: hits[p.id].append((1,shot["owner"],"blaster"))
            elif 0<=x<SIZE and 0<=y<SIZE and self.board[y][x]==".":
                remaining.append(shot)
        self.projectiles = remaining
        burning = {(f["x"], f["y"]) for f in self.flames}
        queue = deque(b for b in self.bombs if b["explode_at"]<=self.tick or (b["x"], b["y"]) in burning)
        exploded = set()
        crates = set()
        blast_board = copy.deepcopy(self.board)
        while queue:
            b=queue.popleft()
            key=(b["x"],b["y"])
            if key in exploded: continue
            exploded.add(key)
            cells=set(self.blast_tiles(b,blast_board))
            self._explosion_sequence += 1
            eid = self._explosion_sequence
            self._explosion_hits[eid] = set()
            for x,y in sorted(cells):
                self.flames.append({"x":x,"y":y,"owner":b["owner"],
                                    "explosion_id":eid,"expires_at":self.tick+BOMB_FLAME_TICKS})
                if blast_board[y][x]=="+": crates.add((x,y))
                self.pickups.pop((x,y),None)
            queue.extend(other for other in self.bombs if (other["x"],other["y"]) in cells and (other["x"],other["y"]) not in exploded)
        self.bombs=[b for b in self.bombs if (b["x"],b["y"]) not in exploded]
        # One hit per player per explosion, including shield-absorbed hits. The
        # private hit ledger never leaks other players' exposure through observations.
        for f in self.flames:
            hit = self._explosion_hits[f["explosion_id"]]
            for p in alive:
                if not p.protection and p.id not in hit and (p.x,p.y)==(f["x"],f["y"]):
                    hits[p.id].append((BOMB_DAMAGE,f["owner"],"bomb"))
                    hit.add(p.id)
        for x,y in sorted(crates):
            self.board[y][x]="."
            if self.rng.random()<.35:
                self.pickups[(x,y)]=self.rng.choice(["health","shield","battery"])
        for p in alive:
            damage=hits[p.id]
            if p.protection or not damage: continue
            # Shield absorbs strongest simultaneous hit; remaining hits still resolve.
            damage.sort(key=lambda h:(-h[0],h[1]))
            if p.shield:
                damage=damage[1:]
                p.shield=False
            total=sum(h[0] for h in damage)
            p.damage_taken+=min(p.hp,total)
            for amount,owner,kind in damage:
                if owner!=p.id: self.players[owner].damage_dealt+=amount
            p.hp=max(0,p.hp-total)
            if p.hp==0:
                p.alive=False
                p.deaths+=1
                p.respawn_at=self.tick+15 if self.mode=="deathmatch" else None
                # Largest damage contribution gets kill; ties go to lowest seat ID, documented.
                contributions=Counter()
                for amount,owner,kind in damage: contributions[owner]+=amount
                killer=min(contributions,key=lambda i:(-contributions[i],i))
                if killer==p.id:
                    p.suicides+=1
                    p.self_bomb_deaths+=1
                else: self.players[killer].kills+=1
                self.event(p.name+" eliminated"+(" themselves" if killer==p.id else " by "+self.players[killer].name),"kill")
        if self.tick%75==60:
            floors=[(x,y) for y in range(1,14) for x in range(1,14) if self.board[y][x]=="."]
            x,y=self.rng.choice(floors)
            self.drop={"x":x,"y":y,"kind":self.rng.choice(["health","shield","battery"]),"at":self.tick+15}
            self.event("Incoming supply drop","drop")
        if self.drop and self.tick>=self.drop["at"]:
            self.pickups[(self.drop["x"],self.drop["y"])]=self.drop["kind"]
            self.drop=None
        survivors=[p.id for p in self.players if p.alive]
        if self.mode=="elimination" and len(survivors)<=1:
            self.done=True
            self.winner=survivors[0] if survivors else None
        if self.tick>=self.max_ticks:
            self.done=True
            if self.mode=="deathmatch":
                scores=[p.kills-p.suicides for p in self.players]
                leaders=[i for i,s in enumerate(scores) if s==max(scores)]
                self.winner=leaders[0] if len(leaders)==1 else None
        if self.done:
            self.result="draw" if self.winner is None else "win"
            self.event("ROUND DRAW" if self.winner is None else self.players[self.winner].name+" WINS","result")
        return self.snapshot()

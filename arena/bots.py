"""Readable reference strategies; all decisions use the public observation only."""
import random
from collections import deque
from .sdk import DIRECTIONS


def danger_tiles(obs):
    danger=set()
    board=obs["board"]
    for b in obs["bombs"]:
        danger.add((b["x"],b["y"]))
        for dx,dy in DIRECTIONS.values():
            for d in range(1,4):
                x,y=b["x"]+dx*d,b["y"]+dy*d
                if not (0<=x<15 and 0<=y<15) or board[y][x]=="#": break
                danger.add((x,y))
                if board[y][x]=="+": break
    for b in obs["projectiles"]:
        for d in range(3):
            danger.add((b["x"]+d*b["dx"],b["y"]+d*b["dy"]))
    return danger


def path_action(obs, targets, avoid=True):
    p=obs["self"]
    start=(p["x"],p["y"])
    board=obs["board"]
    bombs={(b["x"],b["y"]) for b in obs["bombs"]}
    danger=danger_tiles(obs) if avoid else set()
    queue=deque([(start,None)])
    visited={start}
    # Rotate tie-breaking, deterministically, to avoid permanent seat-direction bias.
    directions=list(DIRECTIONS.items())
    offset=(obs["tick"]//15+p["id"])%4
    directions=directions[offset:]+directions[:offset]
    while queue:
        (x,y),first=queue.popleft()
        if (x,y) in targets and first is not None: return first
        for k,(dx,dy) in directions:
            n=(x+dx,y+dy)
            if n in visited or not (0<=n[0]<15 and 0<=n[1]<15): continue
            if board[n[1]][n[0]]!="." or n in bombs: continue
            if n in danger and start not in danger: continue
            visited.add(n)
            queue.append((n,first or "move_"+k))
    return "wait"


def shot_direction(obs):
    p=obs["self"]
    for e in sorted(obs["opponents"],key=lambda e:abs(e["x"]-p["x"])+abs(e["y"]-p["y"])):
        if e["x"]!=p["x"] and e["y"]!=p["y"]: continue
        dx=(e["x"]>p["x"])-(e["x"]<p["x"])
        dy=(e["y"]>p["y"])-(e["y"]<p["y"])
        x,y=p["x"]+dx,p["y"]+dy
        while (x,y)!=(e["x"],e["y"]) and obs["board"][y][x]==".":
            x,y=x+dx,y+dy
        if (x,y)==(e["x"],e["y"]):
            return next(k for k,v in DIRECTIONS.items() if v==(dx,dy))
    return None


FEATURE_NAMES=["health","in_danger","visible_enemies","nearest_enemy","visible_pickups","nearest_pickup","can_shoot","cooldown"]


def features(obs):
    p=obs["self"]
    distance=lambda e:abs(e["x"]-p["x"])+abs(e["y"]-p["y"])
    return [p["hp"],int((p["x"],p["y"]) in danger_tiles(obs)),len(obs["opponents"]),
            min([distance(e) for e in obs["opponents"]] or [30]),len(obs["pickups"]),
            min([distance(e) for e in obs["pickups"]] or [30]),int(shot_direction(obs) is not None),p["cooldown"]]


def teacher_mode(obs):
    f=features(obs)
    if f[1]: return "escape"
    if f[0]<3 and any(i["kind"]=="health" for i in obs["pickups"]): return "supply"
    if f[2]: return "attack"
    if f[4]: return "supply"
    return "explore"


def act_for_mode(obs, mode):
    p=obs["self"]
    board=obs["board"]
    danger=danger_tiles(obs)
    floors={(x,y) for y in range(1,14) for x in range(1,14) if board[y][x]=="."}
    if mode=="escape":
        return path_action(obs,floors-danger,avoid=False)
    if mode=="attack":
        shot=shot_direction(obs)
        if shot:
            if p["weapon"]!="blaster": return "switch"
            if p["cooldown"]==0: return "fire_"+shot
        enemies=obs["opponents"]
        if enemies:
            targets={(e["x"]+dx,e["y"]+dy) for e in enemies for dx,dy in DIRECTIONS.values()}
            return path_action(obs,targets & floors)
    if mode=="supply":
        items=obs["pickups"]
        if p["hp"]<3 and any(i["kind"]=="health" for i in items):
            items=[i for i in items if i["kind"]=="health"]
        targets={(i["x"],i["y"]) for i in items if not (i["kind"]=="health" and p["hp"]==3) and not (i["kind"]=="shield" and p["shield"])}
        if targets:
            action=path_action(obs,targets)
            if action!="wait": return action
    # Move toward least recently seen floor tiles. Tie-break by bot and seed.
    targets=sorted(floors,key=lambda c:(obs["last_seen"][c[1]][c[0]],(c[0]*7+c[1]*13+obs["tick"]//20+p["id"]*17)%31))
    return path_action(obs,set(targets[:4])) if targets else "wait"


class RandomBot:
    def __init__(self): self.rng=None
    def choose_action(self, obs):
        if self.rng is None: self.rng=random.Random(obs["seed"]+obs["self"]["id"]*1009)
        return self.rng.choice(["wait","move_n","move_s","move_w","move_e","fire_n","fire_s","fire_w","fire_e"])


class HunterBot:
    def choose_action(self, obs):
        mode="escape" if features(obs)[1] else "attack" if obs["opponents"] else "explore"
        return act_for_mode(obs,mode)


class SurvivorBot:
    def choose_action(self, obs): return act_for_mode(obs,teacher_mode(obs))


class BomberBot:
    def choose_action(self, obs):
        p=obs["self"]
        if features(obs)[1]: return act_for_mode(obs,"escape")
        near_crate=any(obs["board"][p["y"]+dy][p["x"]+dx]=="+" for dx,dy in DIRECTIONS.values())
        near_enemy=any(abs(e["x"]-p["x"])+abs(e["y"]-p["y"])<=3 for e in obs["opponents"])
        if (near_crate or near_enemy) and not any(b["owner"]==p["id"] for b in obs["bombs"]):
            hypothetical=dict(obs,bombs=obs["bombs"]+[{"x":p["x"],"y":p["y"],"owner":p["id"],"explode_at":obs["tick"]+10}])
            if act_for_mode(hypothetical,"escape")!="wait":
                return "switch" if p["weapon"]!="bomb" else "fire_n"
        return act_for_mode(obs,teacher_mode(obs))


BUILTINS={"random":RandomBot,"hunter":HunterBot,"survivor":SurvivorBot,"bomber":BomberBot}
BOT_INFO=[
    {"id":"random","name":"Wanderer","style":"Random baseline","color":"#a7bac4"},
    {"id":"hunter","name":"Deadeye","style":"Blaster specialist","color":"#ff8b73"},
    {"id":"survivor","name":"Sentinel","style":"Cautious · ML teacher","color":"#70f0ba"},
    {"id":"bomber","name":"Fuse","style":"Bomb tactician","color":"#bca0ff"},
]

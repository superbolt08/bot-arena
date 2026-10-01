"""Balanced, reproducible benchmark batches."""
import math
from .runner import Match


def wilson(wins,n):
    if not n: return [0,1]
    z=1.96
    mid=(wins/n+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt(wins/n*(1-wins/n)/n+z*z/(4*n*n))/(1+z*z/n)
    return [max(0,mid-half),min(1,mid+half)]


def evaluate(candidate, opponents, games=20, seed=10000, mode="elimination", registry=None, on_result=None, max_ticks=None):
    results=[]
    try:
        for i in range(games):
            ids=[candidate]+list(opponents)
            shift=i%len(ids)
            ids=ids[shift:]+ids[:shift]
            candidate_seat=(len(ids)-shift)%len(ids)
            # Keep maps fixed for groups of four while rotating spawn geometry.
            match=Match(ids,registry,seed+i//4,mode,rotation=i%4,max_ticks=max_ticks,record=True)
            try:
                state=match.run()
                me=state["players"][candidate_seat]
                placement=1+sum((p["kills"]-p["suicides"]>me["kills"]-me["suicides"]) if mode=="deathmatch" else ((p["alive"],p["survival_ticks"])>(me["alive"],me["survival_ticks"])) for p in state["players"] if p["id"]!=candidate_seat)
                row={"index":i,"seed":match.game.seed,"seat":candidate_seat,"rotation":i%4,
                     "outcome":"draw" if state["winner"] is None else "win" if state["winner"]==candidate_seat else "loss",
                     "placement":placement,"ticks":state["tick"],"metrics":me,"errors":match.errors}
                results.append(row)
                if on_result: on_result(row,match.replay())
            finally: match.close()
    finally:
        pass
    wins=sum(r["outcome"]=="win" for r in results)
    draws=sum(r["outcome"]=="draw" for r in results)
    return {"candidate":candidate,"opponents":opponents,"mode":mode,"seed":seed,"games":len(results),
            "wins":wins,"draws":draws,"losses":len(results)-wins-draws,"win_rate":wins/max(1,len(results)),
            "win_interval":wilson(wins,len(results)),"results":results,
            "averages":{key:sum(r["metrics"][key] for r in results)/max(1,len(results)) for key in
                        ["damage_dealt","damage_taken","survival_ticks","self_bomb_deaths","invalid_actions","timeouts"]},
            "mean_placement":sum(r["placement"] for r in results)/max(1,len(results))}

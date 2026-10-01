import json
from pathlib import Path
from arena.runner import ExternalBot,Match
from arena.evaluation import evaluate
from arena.bots import features


def test_uploaded_bot_contract(tmp_path):
    path=tmp_path/"bot.py"
    path.write_text('class Bot:\n def choose_action(self, obs):\n  print("debug output")\n  return "move_e"\n')
    m=Match(["custom","random"],{"custom":{"path":str(path),"name":"Custom"}},max_ticks=1)
    m.run()
    assert m.game.players[0].x==2 and not m.errors


def test_bot_timeout_does_not_hang_match(tmp_path):
    path=tmp_path/"slow.py"
    path.write_text('import time\nclass Bot:\n def choose_action(self, obs):\n  time.sleep(10)\n  return "wait"\n')
    m=Match(["slow","random"],{"slow":{"path":str(path),"name":"Slow"}},max_ticks=2)
    m.run()
    assert m.game.players[0].timeouts==1
    assert "timed out" in m.errors[0]


def test_benchmark_balancing_and_metrics():
    report=evaluate("survivor",["hunter","bomber"],games=4,max_ticks=15)
    assert report["wins"]+report["draws"]+report["losses"]==4
    assert len({r["rotation"] for r in report["results"]})==4
    assert len({r["seat"] for r in report["results"]})==3
    assert report["win_interval"][0]<=report["win_rate"]<=report["win_interval"][1]


def test_json_model_bot_runs_in_upload_worker(tmp_path):
    from arena.runner import ROOT
    (tmp_path/"bot.py").write_text((ROOT/"examples/learned_bot.py").read_text())
    (tmp_path/"model.json").write_text(json.dumps({"tree":[{"left":-1,"right":-1,"label":"explore"}]}))
    m=Match(["learned","random"],{"learned":{"path":str(tmp_path/"bot.py"),"name":"Learned"}},max_ticks=3)
    m.run()
    assert not m.errors and m.game.players[0].invalid_actions==0


def test_losing_elimination_bot_ranks_below_last_survivor():
    report=evaluate("survivor",["hunter"],games=4,seed=10000,max_ticks=100)
    for row in report["results"]:
        if row["outcome"]=="loss": assert row["placement"]==2
        if row["outcome"]=="win": assert row["placement"]==1

"""CPU imitation-learning example. python -m arena.train --games 20"""
import argparse
import json
from pathlib import Path
from .bots import BUILTINS, FEATURE_NAMES, features, teacher_mode, act_for_mode
from .engine import Game


def collect(seeds):
    x,y=[],[]
    for seed in seeds:
        game=Game(["Teacher","Opponent"],seed,max_ticks=250,rotation=seed%4)
        opponent=BUILTINS[["hunter","bomber","random"][seed%3]]()
        while not game.done:
            obs=game.observe(0)
            label=teacher_mode(obs)
            x.append(features(obs)); y.append(label)
            game.step({0:act_for_mode(obs,label),1:opponent.choose_action(game.observe(1))})
    return x,y


def train(games=20, output="data/models/model.json"):
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import accuracy_score, classification_report
    from .evaluation import evaluate
    print("Collecting teacher demonstrations on training seeds…",flush=True)
    x,y=collect(range(100,100+games))
    vx,vy=collect(range(5000,5000+max(3,games//4)))
    model=DecisionTreeClassifier(max_depth=5,min_samples_leaf=3,random_state=42)
    model.fit(x,y)
    predictions=model.predict(vx)
    nodes=[]
    tree=model.tree_
    for i in range(tree.node_count):
        nodes.append({"left":int(tree.children_left[i]),"right":int(tree.children_right[i]),
                      "feature":int(tree.feature[i]),"threshold":float(tree.threshold[i]),
                      "label":str(model.classes_[tree.value[i][0].argmax()])})
    artifact={"version":1,"type":"tactical_decision_tree","feature_names":FEATURE_NAMES,"tree":nodes}
    path=Path(output).resolve(); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(artifact,indent=2))
    # The same artifact interpreter is used in the uploadable learned_bot.py.
    class Learned:
        def choose_action(self,obs):
            return act_for_mode(obs,str(model.predict([features(obs)])[0]))
    BUILTINS["learned"]=Learned
    report={"training_matches":games,"training_samples":len(x),"validation_samples":len(vx),
            "validation_accuracy":accuracy_score(vy,predictions),
            "classification":classification_report(vy,predictions,output_dict=True,zero_division=0),
            "seed_splits":{"train":[100,100+games-1],"validation":[5000,5000+max(3,games//4)-1],"evaluation_start":10000},"benchmarks":[]}
    print("Evaluating teacher and learner against three opponents on unseen seeds…",flush=True)
    for opponent in ["random","hunter","bomber"]:
        for candidate in ["survivor","learned"]:
            report["benchmarks"].append(evaluate(candidate,[opponent],games=4,seed=10000,max_ticks=250))
    report_path=path.with_name("training_report.json")
    report_path.write_text(json.dumps(report,indent=2))
    print(json.dumps({"model":str(path),"report":str(report_path),"validation_accuracy":report["validation_accuracy"]},indent=2))
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--games",type=int,default=20)
    parser.add_argument("--output",default="data/models/model.json")
    args=parser.parse_args()
    if not 4<=args.games<=1000: parser.error("--games must be between 4 and 1000")
    train(args.games,args.output)

"""Upload alongside the JSON artifact created by `python -m arena.train`."""
import json
from pathlib import Path
from arena.bots import features, act_for_mode


class Bot:
    def __init__(self):
        self.model = json.loads(Path(__file__).with_name("model.json").read_text())

    def choose_action(self, observation):
        values = features(observation)
        tree = self.model["tree"]
        node = 0
        while tree[node]["left"] != -1:
            row = tree[node]
            node = row["left"] if values[row["feature"]] <= row["threshold"] else row["right"]
        return act_for_mode(observation, tree[node]["label"])

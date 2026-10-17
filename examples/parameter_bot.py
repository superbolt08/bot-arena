"""A readable starting strategy, not a trained model or a competitive benchmark.

Change one parameter, upload a new version, and compare on the same matches.
See learning/PARAMETERS.md for the meaning and limits of these controls.
"""
from arena.bots import act_for_mode, danger_tiles, shot_direction


# These are manually chosen policy parameters, not learned weights.
PARAMETERS = {
    "retreat_health": 1,     # Seek visible health at or below this HP (0–3).
    "aggression": 0.7,       # Attack preference when an opponent is visible (0–1).
    "pickup_priority": 0.4,  # Preference for useful visible supplies (0–1).
}


class Bot:
    def __init__(self):
        self.parameters = dict(PARAMETERS)

    def choose_action(self, observation):
        me = observation["self"]
        params = self.parameters

        # Keep known blast physics fixed; safety is not a trainable game rule.
        if (me["x"], me["y"]) in danger_tiles(observation):
            return act_for_mode(observation, "escape")

        useful = [item for item in observation["pickups"]
                  if (item["kind"] == "health" and me["hp"] < 3)
                  or (item["kind"] == "shield" and not me["shield"])
                  or (item["kind"] == "battery" and me["cooldown"] > 0)]
        if me["hp"] <= params["retreat_health"] and any(i["kind"] == "health" for i in useful):
            return act_for_mode(observation, "supply")

        attack_score = -1.0
        if observation["opponents"]:
            attack_score = params["aggression"] * (1.0 if shot_direction(observation) else 0.5)
        supply_score = params["pickup_priority"] * (1.0 if me["hp"] < 3 else 0.5) if useful else -1.0

        if useful and supply_score > attack_score:
            return act_for_mode(observation, "supply")
        if observation["opponents"]:
            return act_for_mode(observation, "attack")
        if useful:
            return act_for_mode(observation, "supply")
        return act_for_mode(observation, "explore")

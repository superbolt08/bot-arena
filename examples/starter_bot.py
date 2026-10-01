"""Upload this file in the arena. Replace choose_action with your own strategy."""
from arena.sdk import Action


class Bot:
    def __init__(self):
        self.last_enemy = None

    def choose_action(self, observation):
        me = observation["self"]
        for enemy in observation["opponents"]:
            self.last_enemy = (enemy["x"], enemy["y"], observation["tick"])
            if enemy["y"] == me["y"]:
                return Action.FIRE_EAST if enemy["x"] > me["x"] else Action.FIRE_WEST
        # A deliberately simple patrol: try replacing it with pathfinding.
        return Action.EAST if observation["tick"] % 20 < 10 else Action.WEST

"""Public bot contract. Observations contain JSON-compatible values only."""
from enum import Enum


class Action(str, Enum):
    WAIT = "wait"
    NORTH = "move_n"
    SOUTH = "move_s"
    WEST = "move_w"
    EAST = "move_e"
    FIRE_NORTH = "fire_n"
    FIRE_SOUTH = "fire_s"
    FIRE_WEST = "fire_w"
    FIRE_EAST = "fire_e"
    SWITCH = "switch"


DIRECTIONS = {"n": (0, -1), "s": (0, 1), "w": (-1, 0), "e": (1, 0)}
ACTIONS = tuple(a.value for a in Action)


class Bot:
    """One instance per round; use instance fields for memory.

    Implement choose_action(observation). Return an Action or its string value.
    Engine observations never contain unseen opponents or current unseen terrain.
    """
    def choose_action(self, observation):
        return Action.WAIT

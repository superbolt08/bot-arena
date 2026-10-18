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
RULES_VERSION = "0.3"
BOMB_FUSE_TICKS = 10
BOMB_FLAME_TICKS = 3
BOMB_DAMAGE = 2


def bomb_blast_tiles(bomb, board):
    """Full-axis cross, stopped by walls and the first crate on each ray.

    Bots may call this with remembered terrain; unseen changes remain unknown.
    """
    height, width = len(board), len(board[0])
    cells = [(bomb["x"], bomb["y"])]
    for dx, dy in DIRECTIONS.values():
        x, y = bomb["x"] + dx, bomb["y"] + dy
        while 0 <= x < width and 0 <= y < height and board[y][x] != "#":
            cells.append((x, y))
            if board[y][x] == "+":
                break
            x, y = x + dx, y + dy
    return cells


class Bot:
    """One instance per round; use instance fields for memory.

    Implement choose_action(observation). Return an Action or its string value.
    Engine observations never contain unseen opponents or current unseen terrain.
    """
    def choose_action(self, observation):
        return Action.WAIT

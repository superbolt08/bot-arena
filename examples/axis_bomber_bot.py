"""A first patrol-and-bomb bot for learning the Bot Arena observation API.

Upload this file as a bot. It alternates horizontal and vertical patrols,
turns around when its route is blocked, and plants a bomb at a detected
corner only when it can identify a route out of the known blast area.
"""

from collections import deque


WIDTH = 15
HEIGHT = 15
DIRECTIONS = {
    "n": (0, -1),
    "s": (0, 1),
    "w": (-1, 0),
    "e": (1, 0),
}


def is_open(board, x, y):
    """Return whether a tile is known floor and inside the board."""
    return 0 <= x < WIDTH and 0 <= y < HEIGHT and board[y][x] == "."


def bomb_blast_tiles(board, bomb):
    """Estimate the cross-shaped blast, stopping at walls and crates."""
    tiles = {(bomb["x"], bomb["y"])}
    for dx, dy in DIRECTIONS.values():
        for distance in range(1, 4):
            x = bomb["x"] + dx * distance
            y = bomb["y"] + dy * distance
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT) or board[y][x] == "#":
                break
            tiles.add((x, y))
            if board[y][x] == "+":
                break
    return tiles


def known_danger_tiles(observation, extra_bomb=None):
    """Build a conservative danger map from currently visible attacks."""
    board = observation["board"]
    tiles = set()
    bombs = list(observation["bombs"])
    if extra_bomb is not None:
        bombs.append(extra_bomb)
    for bomb in bombs:
        tiles.update(bomb_blast_tiles(board, bomb))

    # Projectiles move forward. Mark the next three tiles as danger.
    for projectile in observation["projectiles"]:
        for distance in range(3):
            x = projectile["x"] + distance * projectile["dx"]
            y = projectile["y"] + distance * projectile["dy"]
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                tiles.add((x, y))
    return tiles


def escape_action(observation, extra_bomb=None):
    """Return the first step toward a known safe tile, or None if trapped."""
    me = observation["self"]
    start = (me["x"], me["y"])
    board = observation["board"]
    danger = known_danger_tiles(observation, extra_bomb)
    bomb_positions = {(b["x"], b["y"]) for b in observation["bombs"]}
    opponent_positions = {(e["x"], e["y"]) for e in observation["opponents"]}
    if extra_bomb is not None:
        bomb_positions.add((extra_bomb["x"], extra_bomb["y"]))

    # Escaping a bomb often means crossing tiles that will be in its future
    # blast. The fuse limits how many moves we have to reach a safe tile.
    bombs = list(observation["bombs"])
    if extra_bomb is not None:
        bombs.append(extra_bomb)
    remaining_fuses = [b["explode_at"] - observation["tick"] for b in bombs]
    move_deadline = min(remaining_fuses) if remaining_fuses else WIDTH * HEIGHT

    # Breadth-first search finds the shortest known route to safety.
    queue = deque([(start, None, 0)])
    visited = {start}
    while queue:
        (x, y), first_action, distance = queue.popleft()
        if (x, y) not in danger and first_action is not None and distance < move_deadline:
            return first_action
        if distance >= move_deadline:
            continue

        for action, (dx, dy) in DIRECTIONS.items():
            next_tile = (x + dx, y + dy)
            nx, ny = next_tile
            if next_tile in visited or not is_open(board, nx, ny):
                continue
            # The player may leave the tile where their own bomb was planted,
            # but cannot walk onto any bomb tile.
            if next_tile in bomb_positions:
                continue
            if next_tile in opponent_positions:
                continue
            visited.add(next_tile)
            queue.append((next_tile, first_action or "move_" + action, distance + 1))
    return None


def is_corner(observation):
    """A corner has two perpendicular neighboring tiles blocked."""
    me = observation["self"]
    x, y = me["x"], me["y"]
    board = observation["board"]
    blocked = {}
    for direction, (dx, dy) in DIRECTIONS.items():
        nx, ny = x + dx, y + dy
        blocked[direction] = not is_open(board, nx, ny)

    return (
        (blocked["n"] and blocked["e"])
        or (blocked["e"] and blocked["s"])
        or (blocked["s"] and blocked["w"])
        or (blocked["w"] and blocked["n"])
    )


class Bot:
    def __init__(self):
        self.axis = "horizontal"
        self.direction = 1
        self.steps_on_axis = 0
        self.axis_length = 8
        self.pending_bomb = False

    def choose_action(self, observation):
        me = observation["self"]
        board = observation["board"]
        here = (me["x"], me["y"])
        owned_bombs = [b for b in observation["bombs"] if b["owner"] == me["id"]]

        # If one of our bombs is active, leave its projected blast area first.
        if owned_bombs:
            self.pending_bomb = False
            return escape_action(observation) or "wait"

        # React to any other currently known bomb or projectile threat too.
        if here in known_danger_tiles(observation):
            return escape_action(observation) or "wait"

        # A planted bomb takes effect on a later tick. This branch places it
        # only if an escape route still exists from the current tile.
        if self.pending_bomb:
            self.pending_bomb = False
            hypothetical = {
                "x": me["x"],
                "y": me["y"],
                "owner": me["id"],
                "explode_at": observation["tick"] + 10,
            }
            if is_corner(observation) and escape_action(observation, hypothetical):
                if me["weapon"] != "bomb":
                    self.pending_bomb = True
                    return "switch"
                return "fire_n"

        # When a corner is found, commit to the bomb sequence if escape is
        # possible. Switching and planting each consume a separate tick.
        if is_corner(observation):
            hypothetical = {
                "x": me["x"],
                "y": me["y"],
                "owner": me["id"],
                "explode_at": observation["tick"] + 10,
            }
            if escape_action(observation, hypothetical):
                if me["weapon"] != "bomb":
                    self.pending_bomb = True
                    return "switch"
                return "fire_n"

        # Patrol back and forth on one axis, then alternate to the other axis.
        if self.steps_on_axis >= self.axis_length:
            self.axis = "vertical" if self.axis == "horizontal" else "horizontal"
            self.direction = 1
            self.steps_on_axis = 0

        if self.axis == "horizontal":
            dx, dy = self.direction, 0
            action = "move_e" if dx > 0 else "move_w"
        else:
            dx, dy = 0, self.direction
            action = "move_s" if dy > 0 else "move_n"

        nx, ny = me["x"] + dx, me["y"] + dy
        enemy_tiles = {(e["x"], e["y"]) for e in observation["opponents"]}
        bomb_tiles = {(b["x"], b["y"]) for b in observation["bombs"]}
        danger_tiles = known_danger_tiles(observation)
        if (not is_open(board, nx, ny) or (nx, ny) in enemy_tiles
                or (nx, ny) in bomb_tiles or (nx, ny) in danger_tiles):
            # Turn back when a wall, crate, opponent, or bomb blocks the route.
            self.direction *= -1
            if self.axis == "horizontal":
                action = "move_e" if self.direction > 0 else "move_w"
                nx = me["x"] + self.direction
                ny = me["y"]
            else:
                action = "move_s" if self.direction > 0 else "move_n"
                nx = me["x"]
                ny = me["y"] + self.direction

            if (not is_open(board, nx, ny) or (nx, ny) in enemy_tiles
                    or (nx, ny) in bomb_tiles or (nx, ny) in danger_tiles):
                # If both directions on this axis are blocked, switch axes.
                self.axis = "vertical" if self.axis == "horizontal" else "horizontal"
                self.direction = 1
                self.steps_on_axis = 0
                return "wait"

        self.steps_on_axis += 1
        return action

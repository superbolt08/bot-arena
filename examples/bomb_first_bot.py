"""Upload as 'Bomb First': plant, escape, then switch to blaster support.

Uses the public observation only. This is a handwritten strategy, not ML.
Set USE_BOMBS = False in a copy for a blaster-only movement-matched control.
No model.json or extra files are needed.
"""
from collections import deque

from arena.bots import shot_direction
from arena.sdk import BOMB_FLAME_TICKS, BOMB_FUSE_TICKS, DIRECTIONS, bomb_blast_tiles


USE_BOMBS = True
MAX_ESCAPE_MOVES = 6


class ThreatMap:
    """Predict known attacks; a route is an estimate, not knowledge of enemy moves."""

    def __init__(self, observation, bombs):
        self.obs = observation
        self.tick = observation["tick"]
        me = observation["self"]
        self.start = (me["x"], me["y"])
        self.board = observation["board"]
        self.enemies = {(p["x"], p["y"]) for p in observation["opponents"]}
        self.bombs = bombs
        # A remembered crate may have been destroyed out of sight. Do not
        # depend on that crate to shield an escape route from an explosion.
        safety_board = [["." if cell == "+" and not observation["visible"][y][x] else cell
                         for x, cell in enumerate(row)] for y, row in enumerate(self.board)]
        self.zones = [set(bomb_blast_tiles(bomb, safety_board)) for bomb in bombs]
        self.due = [bomb["explode_at"] for bomb in bombs]
        self.flames = observation["flames"]
        burning = {(f["x"], f["y"]) for f in self.flames if f["expires_at"] > self.tick + 1}
        for index, bomb in enumerate(bombs):
            if (bomb["x"], bomb["y"]) in burning:
                self.due[index] = min(self.due[index], self.tick + 1)
        # Account for a short-fuse bomb triggering a longer-fuse bomb.
        changed = True
        while changed:
            changed = False
            for source, zone in enumerate(self.zones):
                for target, bomb in enumerate(bombs):
                    triggered_at = max(self.tick + 1, self.due[source])
                    if ((bomb["x"], bomb["y"]) in zone
                            and triggered_at < self.due[source] + BOMB_FLAME_TICKS
                            and self.due[target] > triggered_at):
                        self.due[target] = triggered_at
                        changed = True
        self.blast = set().union(*self.zones) if self.zones else set()
        self.horizon = max([self.tick + 3] + [due + BOMB_FLAME_TICKS for due in self.due])
        self.shots = {}
        for shot in observation["projectiles"]:
            if shot["owner"] == me["id"]:
                continue
            x, y = shot["x"], shot["y"]
            for when in range(self.tick + 1, self.horizon + 1):
                # Walking onto a projectile's old tile also counts as a hit.
                self.shots.setdefault(when, set()).add((x, y))
                x, y = x + shot["dx"], y + shot["dy"]
                if not (0 <= y < len(self.board) and 0 <= x < len(self.board[y])) or safety_board[y][x] != ".":
                    break
                self.shots[when].add((x, y))

    def safe(self, tile, when):
        if tile in self.shots.get(when, ()):
            return False
        if any(tile == (f["x"], f["y"]) and when < f["expires_at"] for f in self.flames):
            return False
        return not any(tile in zone and due <= when < due + BOMB_FLAME_TICKS
                       for zone, due in zip(self.zones, self.due))

    def can_move(self, previous, tile, when):
        x, y = tile
        if not (0 <= y < len(self.board) and 0 <= x < len(self.board[y])):
            return False
        if self.board[y][x] != "." or tile in self.enemies:
            return False
        # Bombs still block movement on their detonation tick. Waiting on the
        # bomb we just planted is allowed, but walking back onto it is not.
        if tile != previous and any(tile == (b["x"], b["y"]) and when <= due
                                    for b, due in zip(self.bombs, self.due)):
            return False
        return self.safe(tile, when)

    def escape(self, start_delay=0, max_moves=8, deadline=None):
        """Find a timed path to a refuge safe through the known flames."""
        queue = deque([(self.start, start_delay, None)])
        visited = {(self.start, start_delay)}
        moves = [("move_" + key, delta) for key, delta in DIRECTIONS.items()] + [("wait", (0, 0))]
        while queue:
            tile, delay, first = queue.popleft()
            when = self.tick + delay
            if (tile not in self.blast and (deadline is None or when <= deadline)
                    and all(self.safe(tile, t) for t in range(max(when, self.tick + 1), self.horizon + 1))):
                return first or "wait"
            if delay - start_delay >= max_moves:
                continue
            for action, (dx, dy) in moves:
                target = (tile[0] + dx, tile[1] + dy)
                key = (target, delay + 1)
                if key in visited or not self.can_move(tile, target, when + 1):
                    continue
                visited.add(key)
                queue.append((target, delay + 1, first or action))
        return None

    def paths(self):
        """Shortest currently safe routes; do not enter a future blast to attack."""
        paths = {self.start: ("wait", 0)}
        queue = deque([self.start])
        while queue:
            tile = queue.popleft()
            first, distance = paths[tile]
            for direction, (dx, dy) in DIRECTIONS.items():
                target = (tile[0] + dx, tile[1] + dy)
                if target in paths or target in self.blast:
                    continue
                if not self.can_move(tile, target, self.tick + distance + 1):
                    continue
                paths[target] = ("move_" + direction if distance == 0 else first, distance + 1)
                queue.append(target)
        return paths


class Bot:
    def __init__(self):
        self.use_bombs = USE_BOMBS
        self.known_bombs = {}
        self.visits = {}

    def remember_bombs(self, observation):
        tick = observation["tick"]
        seen = {(b["x"], b["y"], b["owner"]) for b in observation["bombs"]}
        for bomb in observation["bombs"]:
            self.known_bombs[(bomb["x"], bomb["y"], bomb["owner"])] = dict(bomb)
        visibility = observation["entity_visible"]
        for key, bomb in list(self.known_bombs.items()):
            if key not in seen and visibility[bomb["y"]][bomb["x"]] and bomb["explode_at"] > tick:
                # It disappeared on a visible tile: conservatively allow for
                # an early chain explosion rather than forgetting the danger.
                bomb["explode_at"] = tick
            if tick >= bomb["explode_at"] + BOMB_FLAME_TICKS:
                del self.known_bombs[key]

    def choose_action(self, observation):
        me = observation["self"]
        tick = observation["tick"]
        here = (me["x"], me["y"])
        self.visits[here] = self.visits.get(here, 0) + 1
        self.remember_bombs(observation)
        bombs = list(self.known_bombs.values())
        threats = ThreatMap(observation, bombs)
        # Remember earlier chain timing even if the bomb later leaves sight.
        for bomb, due in zip(bombs, threats.due):
            bomb["explode_at"] = due

        if here in threats.blast or not threats.safe(here, tick + 1):
            escape = threats.escape()
            if escape is not None:
                return escape
            # If no lasting refuge is known, at least dodge the next impact.
            for direction, (dx, dy) in DIRECTIONS.items():
                if threats.can_move(here, (here[0] + dx, here[1] + dy), tick + 1):
                    return "move_" + direction
            return "wait"

        paths = threats.paths()
        useful = [item for item in observation["pickups"]
                  if (item["kind"] == "health" and me["hp"] < 3)
                  or (item["kind"] == "shield" and not me["shield"])
                  or (item["kind"] == "battery" and me["cooldown"] > 1)]
        health = [(item["x"], item["y"]) for item in useful
                  if item["kind"] == "health" and (item["x"], item["y"]) in paths]
        if me["hp"] == 1 and health:
            return paths[min(health, key=lambda tile: paths[tile][1])][0]

        owned_bomb = any(b["owner"] == me["id"] and due > tick
                         for b, due in zip(bombs, threats.due))
        footprint = set(bomb_blast_tiles(me, observation["board"]))
        enemy_in_blast = any((enemy["x"], enemy["y"]) in footprint for enemy in observation["opponents"])
        crate_in_blast = any(observation["board"][y][x] == "+" for x, y in footprint)
        if self.use_bombs and not owned_bomb and (enemy_in_blast or crate_in_blast):
            planned = {"x": me["x"], "y": me["y"], "owner": me["id"],
                       "explode_at": tick + 1 + BOMB_FUSE_TICKS}
            escape_map = ThreatMap(observation, bombs + [planned])
            # Planting consumes one action. Leave two ticks' margin, and
            # re-check after switching instead of blindly committing to fire.
            deadline = escape_map.due[-1] - 2
            if (escape_map.safe(here, tick + 1)
                    and escape_map.escape(start_delay=1, max_moves=MAX_ESCAPE_MOVES, deadline=deadline) is not None):
                if me["weapon"] != "bomb":
                    return "switch"
                self.known_bombs[(me["x"], me["y"], me["id"])] = planned
                return "fire_n"

        # Bombs get first refusal. Use the blaster during the active-bomb
        # window, when an escape is unavailable, or when bombs are disabled.
        shot = shot_direction(observation)
        if shot:
            if me["weapon"] != "blaster":
                return "switch"
            if me["cooldown"] <= 1:
                return "fire_" + shot
        else:
            desired = "bomb" if self.use_bombs and not owned_bomb else "blaster"
            if me["weapon"] != desired:
                return "switch"

        targets = [(item["x"], item["y"]) for item in useful if (item["x"], item["y"]) in paths]
        if targets:
            return paths[min(targets, key=lambda tile: paths[tile][1])][0]
        firing_tiles = set()
        for enemy in observation["opponents"]:
            for tile in bomb_blast_tiles(enemy, observation["board"]):
                distance = abs(tile[0] - enemy["x"]) + abs(tile[1] - enemy["y"])
                if tile in paths and tile != here and 2 <= distance <= 5:
                    firing_tiles.add(tile)
        if firing_tiles:
            return paths[min(firing_tiles, key=lambda tile: (paths[tile][1], tile))][0]
        candidates = [tile for tile in paths if tile != here]
        if candidates:
            # Prefer underexplored reachable tiles; avoid targeting an
            # inaccessible floor pocket behind crates forever.
            target = min(candidates, key=lambda tile: (self.visits.get(tile, 0),
                         paths[tile][1], observation["last_seen"][tile[1]][tile[0]], tile))
            return paths[target][0]
        return "wait"

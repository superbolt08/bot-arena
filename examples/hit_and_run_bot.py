"""Hit-and-run survivor bot for Bot Arena.

The bot scouts toward the center for a short trip, shoots visible enemies from
range, and retreats along its successful path. It only considers a bomb when a
nearby enemy is in its projected blast and two roomy escape routes are known.

This is a hand-written strategy example, not a trained machine-learning model.
"""

from collections import deque


SIZE = 15
CENTER = (7, 7)
MAX_SCOUT_MOVES = 12
MAX_BOMB_ESCAPE_MOVES = 5
DIRECTIONS = {
    "n": (0, -1),
    "s": (0, 1),
    "w": (-1, 0),
    "e": (1, 0),
}


def inside(x, y):
    return 0 <= x < SIZE and 0 <= y < SIZE


def open_floor(board, x, y):
    return inside(x, y) and board[y][x] == "."


def tile_neighbors(x, y):
    for direction, (dx, dy) in DIRECTIONS.items():
        yield direction, (x + dx, y + dy)


def blast_cells(board, bomb):
    """Return one bomb's cross-shaped blast, including its origin."""
    origin = (bomb["x"], bomb["y"])
    cells = {origin}
    for dx, dy in DIRECTIONS.values():
        for distance in range(1, 4):
            x = bomb["x"] + dx * distance
            y = bomb["y"] + dy * distance
            if not inside(x, y) or board[y][x] == "#":
                break
            cells.add((x, y))
            if board[y][x] == "+":
                break
    return cells


def chained_blast_cells(board, bombs, seeds=None):
    """Conservatively include bombs reached by a chain reaction."""
    pending = list(bombs if seeds is None else seeds)
    exploded = set()
    cells = set()
    while pending:
        bomb = pending.pop()
        key = (bomb["x"], bomb["y"], bomb["owner"], bomb["explode_at"])
        if key in exploded:
            continue
        exploded.add(key)
        new_cells = blast_cells(board, bomb)
        cells.update(new_cells)
        for other in bombs:
            other_key = (other["x"], other["y"], other["owner"], other["explode_at"])
            if other_key not in exploded and (other["x"], other["y"]) in new_cells:
                pending.append(other)
    return cells


def projectile_cells(observation):
    """Mark each visible projectile tile and its next three positions."""
    danger = set()
    for projectile in observation["projectiles"]:
        for distance in range(4):
            x = projectile["x"] + distance * projectile["dx"]
            y = projectile["y"] + distance * projectile["dy"]
            if inside(x, y):
                danger.add((x, y))
    return danger


def known_danger(observation):
    board = observation["board"]
    danger = chained_blast_cells(board, observation["bombs"])
    danger.update(projectile_cells(observation))
    danger.update((f["x"], f["y"]) for f in observation["flames"])
    return danger


def line_shot(observation):
    """Return a blaster action if a visible enemy is in a clear firing lane."""
    me = observation["self"]
    board = observation["board"]
    enemies = sorted(
        observation["opponents"],
        key=lambda e: abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]),
    )
    for enemy in enemies:
        if enemy["y"] == me["y"]:
            step = 1 if enemy["x"] > me["x"] else -1
            x = me["x"] + step
            clear = True
            while x != enemy["x"]:
                if board[me["y"]][x] != ".":
                    clear = False
                    break
                x += step
            if clear:
                return "fire_e" if step > 0 else "fire_w"
        elif enemy["x"] == me["x"]:
            step = 1 if enemy["y"] > me["y"] else -1
            y = me["y"] + step
            clear = True
            while y != enemy["y"]:
                if board[y][me["x"]] != ".":
                    clear = False
                    break
                y += step
            if clear:
                return "fire_s" if step > 0 else "fire_n"
    return None


def route_to(observation, goal, blocked=None, allow_danger_start=False):
    """BFS path through known floor; return its first action or None."""
    me = observation["self"]
    start = (me["x"], me["y"])
    if start == goal:
        return None
    board = observation["board"]
    danger = known_danger(observation)
    enemies = {(e["x"], e["y"]) for e in observation["opponents"]}
    bombs = {(b["x"], b["y"]) for b in observation["bombs"]}
    blocked = blocked or set()
    escaping = allow_danger_start and start in danger
    queue = deque([(start, None, 0)])
    visited = {start}
    while queue:
        (x, y), first_action, depth = queue.popleft()
        if (x, y) == goal and first_action is not None:
            return first_action
        for direction, (nx, ny) in tile_neighbors(x, y):
            target = (nx, ny)
            if target in visited or not open_floor(board, nx, ny):
                continue
            if target in bombs or target in enemies or target in blocked:
                continue
            if target in danger and not escaping:
                continue
            visited.add(target)
            queue.append((target, first_action or "move_" + direction, depth + 1))
    return None


def local_safe_room(board, tile, forbidden, occupied, previous):
    """Require several nearby safe tiles and two exits beyond the entry tile."""
    x, y = tile
    exits = []
    for _, neighbor in tile_neighbors(x, y):
        nx, ny = neighbor
        if (open_floor(board, nx, ny) and neighbor not in forbidden
                and neighbor not in occupied and neighbor != previous):
            exits.append(neighbor)
    if len(exits) < 2:
        return False

    # Count the safe pocket within two steps. This rejects a narrow cul-de-sac.
    queue = deque([(tile, 0)])
    seen = {tile}
    while queue:
        (cx, cy), depth = queue.popleft()
        if depth == 2:
            continue
        for _, (nx, ny) in tile_neighbors(cx, cy):
            candidate = (nx, ny)
            if (candidate in seen or not open_floor(board, nx, ny)
                    or candidate in forbidden or candidate in occupied):
                continue
            seen.add(candidate)
            queue.append((candidate, depth + 1))
    return len(seen) >= 5


def bomb_escape_options(observation, hypothetical, max_moves=MAX_BOMB_ESCAPE_MOVES, blocked=None):
    """Find distinct first moves to roomy refuges outside the bomb blast."""
    me = observation["self"]
    start = (me["x"], me["y"])
    board = observation["board"]
    bombs = list(observation["bombs"])
    bombs.append(hypothetical)
    blast = chained_blast_cells(board, bombs)
    projectile_hazards = projectile_cells(observation)
    external_hazards = set(projectile_hazards)
    external_hazards.update((f["x"], f["y"]) for f in observation["flames"])
    # A bomb with a short fuse may explode while we cross its blast. Ignore
    # this bot's own chain for transit planning, but block other imminent
    # blasts. The full blast union is still forbidden as a refuge.
    if hypothetical is not None:
        escape_seeds = [hypothetical]
    else:
        escape_seeds = [b for b in observation["bombs"]
                        if b["owner"] == me["id"] and (b["x"], b["y"]) == start]
    own_chain = chained_blast_cells(board, bombs, escape_seeds) if escape_seeds else set()
    own_chain_positions = {position for position in own_chain}
    external_bombs = [b for b in observation["bombs"]
                      if (b["x"], b["y"]) not in own_chain_positions]
    soonest_external_fuse = min(
        (b["explode_at"] - observation["tick"] for b in external_bombs),
        default=SIZE * SIZE,
    )
    if soonest_external_fuse <= max_moves:
        external_hazards.update(chained_blast_cells(board, bombs, external_bombs))
    bomb_positions = {(b["x"], b["y"]) for b in observation["bombs"]}
    opponents = {(e["x"], e["y"]) for e in observation["opponents"]}
    blocked = bomb_positions | opponents | (blocked or set())
    routes = {}

    # Run a small BFS separately for each first move. The newly planted bomb's
    # blast cells may be crossed before detonation, but cannot be refuge tiles.
    for first_direction, first_tile in tile_neighbors(*start):
        fx, fy = first_tile
        if (not open_floor(board, fx, fy) or first_tile in blocked
                or first_tile in external_hazards):
            continue
        queue = deque([(first_tile, 1, start)])
        visited = {first_tile}
        while queue:
            tile, depth, previous = queue.popleft()
            if (tile not in blast and tile not in external_hazards
                    and local_safe_room(board, tile, blast | external_hazards,
                                        blocked, previous)):
                routes[first_direction] = ("move_" + first_direction, depth, tile)
                break
            if depth >= max_moves:
                continue
            x, y = tile
            for _, (nx, ny) in tile_neighbors(x, y):
                neighbor = (nx, ny)
                if (neighbor in visited or not open_floor(board, nx, ny)
                        or neighbor in blocked or neighbor in external_hazards):
                    continue
                visited.add(neighbor)
                queue.append((neighbor, depth + 1, tile))
    return routes


def emergency_bomb_escape(observation, bomb, max_moves=8, blocked=None):
    """Find any timely exit if the preferred roomy routes became blocked."""
    me = observation["self"]
    start = (me["x"], me["y"])
    board = observation["board"]
    bombs = list(observation["bombs"])
    blast = chained_blast_cells(board, bombs)
    bomb_positions = {(b["x"], b["y"]) for b in bombs}
    enemies = {(e["x"], e["y"]) for e in observation["opponents"]}
    external = projectile_cells(observation)
    blocked = blocked or set()
    external.update((f["x"], f["y"]) for f in observation["flames"])
    other_bombs = [b for b in bombs if (b["x"], b["y"]) != (bomb["x"], bomb["y"])]
    soonest_other = min(
        (b["explode_at"] - observation["tick"] for b in other_bombs),
        default=SIZE * SIZE,
    )
    if soonest_other <= max_moves:
        external.update(chained_blast_cells(board, bombs, other_bombs))
    remaining = bomb["explode_at"] - observation["tick"]
    deadline = min(max_moves, max(0, remaining - 1))

    queue = deque([(start, None, 0)])
    visited = {start}
    while queue:
        tile, first_action, depth = queue.popleft()
        if tile not in blast and tile not in external and first_action is not None:
            return first_action
        if depth >= deadline:
            continue
        x, y = tile
        for direction, (nx, ny) in tile_neighbors(x, y):
            neighbor = (nx, ny)
            if (neighbor in visited or not open_floor(board, nx, ny)
                    or neighbor in bomb_positions or neighbor in enemies
                    or neighbor in external or neighbor in blocked):
                continue
            visited.add(neighbor)
            queue.append((neighbor, first_action or "move_" + direction, depth + 1))
    return None


def route_to_bomb_refuge(observation, bomb, goal, max_moves=8, blocked=None):
    """Keep routing toward a chosen refuge while crossing this bomb's blast."""
    me = observation["self"]
    start = (me["x"], me["y"])
    if goal is None:
        return None

    board = observation["board"]
    bombs = list(observation["bombs"])
    blast = chained_blast_cells(board, bombs)
    bomb_positions = {(b["x"], b["y"]) for b in bombs}
    enemies = {(e["x"], e["y"]) for e in observation["opponents"]}
    external = projectile_cells(observation)
    external.update((f["x"], f["y"]) for f in observation["flames"])
    other_bombs = [b for b in bombs if (b["x"], b["y"]) != (bomb["x"], bomb["y"])]
    soonest_other = min(
        (b["explode_at"] - observation["tick"] for b in other_bombs),
        default=SIZE * SIZE,
    )
    if soonest_other <= max_moves:
        external.update(chained_blast_cells(board, bombs, other_bombs))
    blocked = blocked or set()

    remaining = bomb["explode_at"] - observation["tick"]
    deadline = min(max_moves, max(0, remaining - 1))
    queue = deque([(start, None, 0)])
    visited = {start}
    while queue:
        tile, first_action, depth = queue.popleft()
        if tile == goal and tile not in blast and tile not in external:
            return first_action
        if depth >= deadline:
            continue
        x, y = tile
        for direction, (nx, ny) in tile_neighbors(x, y):
            neighbor = (nx, ny)
            if (neighbor in visited or not open_floor(board, nx, ny)
                    or neighbor in bomb_positions or neighbor in enemies
                    or neighbor in external or neighbor in blocked):
                continue
            visited.add(neighbor)
            queue.append((neighbor, first_action or "move_" + direction, depth + 1))
    return None


def path_distance(board, start, goal, limit=8):
    """Shortest known floor distance, allowing the goal to be occupied."""
    if start == goal:
        return 0
    queue = deque([(start, 0)])
    visited = {start}
    while queue:
        (x, y), depth = queue.popleft()
        if depth >= limit:
            continue
        for _, (nx, ny) in tile_neighbors(x, y):
            tile = (nx, ny)
            if tile == goal:
                return depth + 1
            if tile in visited or not open_floor(board, nx, ny):
                continue
            visited.add(tile)
            queue.append((tile, depth + 1))
    return None


class Bot:
    def __init__(self):
        self.home = None
        self.phase = "scout"
        self.path_stack = []
        self.last_position = None
        self.last_action = None
        self.last_hp = None
        self.blocked_until = {}
        self.threatened_until = {}
        self.scout_moves = 0
        self.pending_bomb = False
        self.last_bomb_tick = -100
        self.bomb_escape_goal = None

    def _update_memory(self, observation):
        me = observation["self"]
        here = (me["x"], me["y"])
        tick = observation["tick"]
        if self.home is None:
            self.home = here
            self.path_stack = [here]
        if self.last_position is not None and self.last_action:
            if self.last_action.startswith("move_"):
                if here == self.last_position:
                    direction = self.last_action[-1]
                    dx, dy = DIRECTIONS[direction]
                    failed_tile = (self.last_position[0] + dx, self.last_position[1] + dy)
                    self.blocked_until[failed_tile] = tick + 2
                elif here not in self.path_stack:
                    self.path_stack.append(here)

        if self.phase == "retreat" and here in self.path_stack:
            # Trim the explored future as the bot successfully walks backward.
            index = max(i for i, tile in enumerate(self.path_stack) if tile == here)
            self.path_stack = self.path_stack[:index + 1]
        elif not self.path_stack or self.path_stack[-1] != here:
            self.path_stack.append(here)

        self.blocked_until = {tile: until for tile, until in self.blocked_until.items()
                              if until >= tick}
        self._remember_projectile_lanes(observation, here)
        self.threatened_until = {tile: until for tile, until in self.threatened_until.items()
                                 if until >= tick}
        took_damage = self.last_hp is not None and me["hp"] < self.last_hp
        self.last_position = here
        self.last_hp = me["hp"]
        return here, took_damage

    def _temporary_blocks(self):
        return set(self.blocked_until) | set(self.threatened_until)

    def _remember_action(self, action):
        self.last_action = action
        return action

    def _remember_projectile_lanes(self, observation, here):
        """Keep recently fired lanes unsafe briefly, including on retreat."""
        tick = observation["tick"]
        recent_path = self.path_stack[-8:]
        for projectile in observation["projectiles"]:
            dx, dy = projectile["dx"], projectile["dy"]
            ray = {
                (projectile["x"] + distance * dx,
                 projectile["y"] + distance * dy)
                for distance in range(4)
            }
            for tile in recent_path:
                if tile in ray:
                    self.threatened_until[tile] = tick + 3

            incoming = any(
                (projectile["x"] + distance * dx,
                 projectile["y"] + distance * dy) == here
                for distance in range(1, 4)
            )
            if not incoming:
                continue

            # If the shot is arriving from along the breadcrumb trail, avoid
            # retreating down that same corridor for a few ticks.
            source_dx, source_dy = -dx, -dy
            for tile in recent_path:
                tx, ty = tile[0] - here[0], tile[1] - here[1]
                if source_dx and ty == 0 and tx * source_dx > 0 and abs(tx) <= 5:
                    self.threatened_until[tile] = tick + 5
                elif source_dy and tx == 0 and ty * source_dy > 0 and abs(ty) <= 5:
                    self.threatened_until[tile] = tick + 5

    def _incoming_hit(self, observation, here):
        # If a visible projectile is on a path that reaches our current tile,
        # step out of the lane before continuing the planned route.
        for projectile in observation["projectiles"]:
            for distance in range(1, 4):
                tile = (projectile["x"] + distance * projectile["dx"],
                        projectile["y"] + distance * projectile["dy"])
                if tile == here:
                    return True
        return False

    def _dodge_action(self, observation, here):
        me = observation["self"]
        board = observation["board"]
        danger = known_danger(observation)
        bombs = {(b["x"], b["y"]) for b in observation["bombs"]}
        enemies = {(e["x"], e["y"]) for e in observation["opponents"]}
        choices = []
        for direction, tile in tile_neighbors(*here):
            x, y = tile
            if (not open_floor(board, x, y) or tile in bombs or tile in enemies
                    or tile in danger or tile in self._temporary_blocks()):
                continue
            nearest = min((abs(x - e["x"]) + abs(y - e["y"])
                           for e in observation["opponents"]), default=99)
            home_distance = abs(x - self.home[0]) + abs(y - self.home[1])
            choices.append((nearest, -home_distance, "move_" + direction))
        return max(choices)[2] if choices else "wait"

    def _retreat_action(self, observation, here):
        if self.home == here:
            if observation["opponents"]:
                # Do not restart a center trip while an enemy is still nearby.
                return self._dodge_action(observation, here)
            self.phase = "scout"
            self.scout_moves = 0
            return None

        blocked = self._temporary_blocks()
        # Prefer the most recent successful breadcrumb that is still safe.
        for goal in reversed(self.path_stack[:-1]):
            if goal in known_danger(observation):
                continue
            action = route_to(observation, goal, blocked=blocked)
            if action:
                return action
        return route_to(observation, self.home, blocked=blocked) or "wait"

    def _is_bomb_opportunity(self, observation, here):
        me = observation["self"]
        if observation["tick"] - self.last_bomb_tick < 20:
            return None
        if not observation["opponents"]:
            return None
        # Keep bombs for the central engagement area.
        if abs(here[0] - CENTER[0]) + abs(here[1] - CENTER[1]) > 5:
            return None

        hypothetical = {
            "x": here[0], "y": here[1], "owner": me["id"],
            "explode_at": observation["tick"] + 10,
        }
        zone = chained_blast_cells(observation["board"],
                                   list(observation["bombs"]) + [hypothetical])
        for enemy in observation["opponents"]:
            enemy_tile = (enemy["x"], enemy["y"])
            distance = path_distance(observation["board"], here, enemy_tile, limit=4)
            if distance is not None and distance <= 3 and enemy_tile in zone:
                routes = bomb_escape_options(
                    observation, hypothetical, blocked=self._temporary_blocks()
                )
                if len(routes) >= 2:
                    return hypothetical
        return None

    def _remember_bomb_refuge(self, observation, bomb):
        routes = bomb_escape_options(
            observation, bomb, blocked=self._temporary_blocks()
        )
        if routes:
            route = min(routes.values(), key=lambda item: (item[1], item[2]))
            self.bomb_escape_goal = route[2]

    def choose_action(self, observation):
        return self._remember_action(self._decide(observation))

    def _decide(self, observation):
        me = observation["self"]
        here, took_damage = self._update_memory(observation)
        owned_bombs = [b for b in observation["bombs"] if b["owner"] == me["id"]]

        # An active bomb outranks combat or exploration. Re-plan the exit each
        # tick only if the remembered refuge has become unreachable.
        if owned_bombs:
            self.pending_bomb = False
            bomb = owned_bombs[0]
            if self.bomb_escape_goal is None:
                self._remember_bomb_refuge(observation, bomb)
            if here == self.bomb_escape_goal:
                if here not in known_danger(observation):
                    return "wait"
            action = route_to_bomb_refuge(
                observation, bomb, self.bomb_escape_goal, max_moves=8,
                blocked=self._temporary_blocks(),
            )
            if action:
                return action
            # If an opponent or a new hazard blocked the saved destination,
            # select another validated refuge and route all the way to it.
            self.bomb_escape_goal = None
            self._remember_bomb_refuge(observation, bomb)
            action = route_to_bomb_refuge(
                observation, bomb, self.bomb_escape_goal, max_moves=8,
                blocked=self._temporary_blocks(),
            )
            if action:
                return action
            emergency = emergency_bomb_escape(
                observation, bomb, max_moves=8,
                blocked=self._temporary_blocks(),
            )
            if emergency:
                return emergency
            return self._dodge_action(observation, here)

        self.bomb_escape_goal = None

        # Visible projectiles and fresh damage trigger an immediate retreat.
        if self._incoming_hit(observation, here):
            self.phase = "retreat"
            self.pending_bomb = False
            return self._dodge_action(observation, here)
        if took_damage:
            self.phase = "retreat"
            self.pending_bomb = False

        enemies = observation["opponents"]
        enemy_distances = [path_distance(observation["board"], here, (e["x"], e["y"]), limit=8)
                           for e in enemies]
        closest_distance = min((d for d in enemy_distances if d is not None), default=None)

        # A nearby enemy is a reason to consider a bomb, never a reason to
        # walk closer. The plant is revalidated after a weapon-switch tick.
        is_close = enemies and closest_distance is not None and closest_distance <= 3
        if is_close:
            opportunity = self._is_bomb_opportunity(observation, here)
            if opportunity:
                self.phase = "retreat"
                if me["weapon"] == "bomb":
                    self.pending_bomb = False
                    self.last_bomb_tick = observation["tick"]
                    self._remember_bomb_refuge(observation, opportunity)
                    return "fire_n"
                self.pending_bomb = True
                return "switch"
            self.pending_bomb = False
            self.phase = "retreat"

        if self.pending_bomb:
            opportunity = self._is_bomb_opportunity(observation, here)
            if opportunity and me["weapon"] == "bomb":
                self.phase = "retreat"
                self.pending_bomb = False
                self.last_bomb_tick = observation["tick"]
                self._remember_bomb_refuge(observation, opportunity)
                return "fire_n"
            self.pending_bomb = False
            if me["weapon"] == "bomb":
                return "switch"

        # Shoot from range, then withdraw rather than pursuing into contact.
        if enemies:
            shot = line_shot(observation)
            if (shot and me["weapon"] == "blaster" and me["cooldown"] == 0
                    and not is_close):
                self.phase = "retreat"
                return shot
            if closest_distance is not None and closest_distance > 3:
                self.phase = "retreat"

        if self.phase == "retreat":
            action = self._retreat_action(observation, here)
            if action is not None:
                if action == "wait" and me["weapon"] == "bomb":
                    return "switch"
                return action

        # The scouting trip is short and bounded. Reaching the center or
        # spending the move budget sends the bot back along its path stack.
        if self.scout_moves >= MAX_SCOUT_MOVES or here == CENTER:
            self.phase = "retreat"
            return self._retreat_action(observation, here) or "wait"

        if me["weapon"] != "blaster":
            return "switch"

        if here != CENTER:
            action = route_to(observation, CENTER, blocked=self._temporary_blocks())
            if action:
                self.scout_moves += 1
                return action

        # If known terrain blocks the center route, return safely instead of
        # repeatedly attempting a failed move.
        self.phase = "retreat"
        return self._retreat_action(observation, here) or "wait"

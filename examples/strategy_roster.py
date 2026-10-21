"""Four handwritten strategies sharing Bomb First's threat and escape code.

Run `python -m examples.strategy_roster` to export self-contained upload files
under data/strategy_roster/. No model JSON is required. Exported files freeze
their shared helpers too, so later edits to examples do not change a submission.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path

from examples import bomb_first_bot
from examples.bomb_first_bot import Bot as BombFirstBase, ThreatMap
from arena.bots import shot_direction
from arena.sdk import BOMB_FUSE_TICKS, BOMB_FLAME_TICKS, DIRECTIONS, bomb_blast_tiles


ROSTER = {
    "combo": {
        "name": "Crossfire", "file": "crossfire_bot.py",
        "description": "Bomb pressure, escape, then deliberate blaster follow-up during the fuse.",
    },
    "breach": {
        "name": "Breach & Shoot", "file": "breach_and_shoot_bot.py",
        "description": "Bomb crates with no visible enemies; switch to blaster on contact.",
    },
    "ranged": {
        "name": "Range Keeper", "file": "range_keeper_bot.py",
        "description": "Blaster only; seek long firing lanes and kite between shots.",
    },
    "siege": {
        "name": "Siege", "file": "siege_bot.py",
        "description": "Bomb only; clear crates, deny lanes and collect useful supplies.",
    },
}


class StrategyBot(BombFirstBase):
    strategy = "combo"

    def __init__(self):
        super().__init__()
        if self.strategy not in ("combo", "breach", "ranged", "siege"):
            raise ValueError("Unknown strategy")
        self.followup_until = -1

    def _plant(self, observation, bombs):
        """A switch is only preparation; validate the plant again next turn."""
        me = observation["self"]
        tick = observation["tick"]
        planned = {"x": me["x"], "y": me["y"], "owner": me["id"],
                   "explode_at": tick + 1 + BOMB_FUSE_TICKS}
        threats = ThreatMap(observation, bombs + [planned])
        if not threats.safe((me["x"], me["y"]), tick + 1):
            return None
        if threats.escape(start_delay=1, max_moves=6, deadline=threats.due[-1] - 2) is None:
            return None
        if me["weapon"] != "bomb":
            return "switch"
        self.known_bombs[(me["x"], me["y"], me["id"])] = planned
        # Crossfire reserves this whole window for shooting/repositioning,
        # rather than immediately arming another bomb as the old one ends.
        self.followup_until = planned["explode_at"] + BOMB_FLAME_TICKS
        return "fire_n"

    def _fire_blaster(self, observation, direction):
        if direction is None:
            return None
        me = observation["self"]
        if me["weapon"] != "blaster":
            return "switch"
        return "fire_" + direction if me["cooldown"] <= 1 else None

    def _move(self, observation, threats, paths):
        me = observation["self"]
        here = (me["x"], me["y"])
        enemies = observation["opponents"]
        useful = [item for item in observation["pickups"]
                  if (item["kind"] == "health" and me["hp"] < 3)
                  or (item["kind"] == "shield" and not me["shield"])
                  or (item["kind"] == "battery" and me["cooldown"] > 1 and self.strategy != "siege")]
        supplies = [(item["x"], item["y"]) for item in useful
                    if (item["x"], item["y"]) in paths]
        if supplies:
            target = min(supplies, key=lambda tile: (paths[tile][1], tile))
            if not enemies or me["hp"] == 1 or paths[target][1] <= 2:
                return paths[target][0]

        minimum, maximum = (4, 7) if self.strategy == "ranged" else (2, 5)
        if enemies:
            distance = lambda tile: min(abs(tile[0] - e["x"]) + abs(tile[1] - e["y"]) for e in enemies)
            adjacent = [tile for tile in paths if paths[tile][1] == 1]
            if self.strategy == "ranged" and distance(here) < minimum and adjacent:
                # Back off while the blaster reloads; prefer a tile that also
                # breaks direct alignment rather than running down a bullet lane.
                target = max(adjacent, key=lambda tile: (distance(tile),
                             all(tile[0] != e["x"] and tile[1] != e["y"] for e in enemies), tile))
                if distance(target) > distance(here):
                    return paths[target][0]
            firing_tiles = set()
            for enemy in enemies:
                for tile in bomb_blast_tiles(enemy, observation["board"]):
                    gap = abs(tile[0] - enemy["x"]) + abs(tile[1] - enemy["y"])
                    if tile in paths and minimum <= gap <= maximum:
                        firing_tiles.add(tile)
            if firing_tiles:
                target = min(firing_tiles, key=lambda tile: (paths[tile][1], tile))
                return paths[target][0]

        candidates = [tile for tile in paths if tile != here]
        if candidates:
            target = min(candidates, key=lambda tile: (self.visits.get(tile, 0), paths[tile][1],
                         abs(tile[0] - 7) + abs(tile[1] - 7), tile))
            return paths[target][0]
        return "wait"

    def choose_action(self, observation):
        me = observation["self"]
        tick = observation["tick"]
        here = (me["x"], me["y"])
        enemies = observation["opponents"]
        self.visits[here] = self.visits.get(here, 0) + 1
        self.remember_bombs(observation)
        bombs = list(self.known_bombs.values())
        threats = ThreatMap(observation, bombs)
        for bomb, due in zip(bombs, threats.due):
            bomb["explode_at"] = due

        # All profiles share urgent safety. Weapon preference never interrupts
        # getting out of an active blast or dodging an incoming projectile.
        if here in threats.blast or not threats.safe(here, tick + 1):
            escape = threats.escape()
            if escape is not None:
                return escape
            for direction, (dx, dy) in DIRECTIONS.items():
                if threats.can_move(here, (here[0] + dx, here[1] + dy), tick + 1):
                    return "move_" + direction
            return "wait"

        # The user's exploration/combat split: visibility means detected
        # enemies only; the bot does not know whether hidden enemies are nearby.
        if self.strategy == "breach" and enemies and me["weapon"] != "blaster":
            return "switch"

        paths = threats.paths()
        health = [(p["x"], p["y"]) for p in observation["pickups"]
                  if p["kind"] == "health" and (p["x"], p["y"]) in paths]
        if me["hp"] == 1 and health:
            return paths[min(health, key=lambda tile: (paths[tile][1], tile))][0]

        owned_bomb = any(b["owner"] == me["id"] and due > tick
                         for b, due in zip(bombs, threats.due))
        shot = shot_direction(observation)
        footprint = set(bomb_blast_tiles(me, observation["board"]))
        threatened = [enemy for enemy in enemies if (enemy["x"], enemy["y"]) in footprint]
        crates = any(observation["board"][y][x] == "+" for x, y in footprint)

        if self.strategy == "ranged":
            if me["weapon"] != "blaster":
                return "switch"
            action = self._fire_blaster(observation, shot)
            if action is not None:
                return action
        elif self.strategy == "breach":
            if enemies:
                action = self._fire_blaster(observation, shot)
                if action is not None:
                    return action
            elif crates and not owned_bomb:
                action = self._plant(observation, bombs)
                if action is not None:
                    return action
        elif self.strategy == "siege":
            if not owned_bomb and (crates or threatened):
                action = self._plant(observation, bombs)
                if action is not None:
                    return action
            if me["weapon"] != "bomb":
                return "switch"
        else:
            # Once a bomb has been placed, keep the blaster equipped and seek
            # a safe firing lane for follow-up attacks during the fuse.
            followup = owned_bomb or tick < self.followup_until
            if followup:
                if me["weapon"] != "blaster":
                    return "switch"
                action = self._fire_blaster(observation, shot)
                if action is not None:
                    return action
            else:
                # Take an immediate close-range/finishing shot; use bombs to
                # pressure opponents at medium range rather than every lane.
                immediate = shot and any(e["hp"] <= 1 or abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]) <= 2
                                         for e in enemies)
                if immediate:
                    action = self._fire_blaster(observation, shot)
                    if action is not None:
                        return action
                pressure = any(3 <= abs(e["x"] - me["x"]) + abs(e["y"] - me["y"]) <= 5 for e in threatened)
                if pressure or (crates and not enemies):
                    action = self._plant(observation, bombs)
                    if action is not None:
                        return action
                action = self._fire_blaster(observation, shot)
                if action is not None:
                    return action

        return self._move(observation, threats, paths)


def export_roster(directory):
    """Freeze the common code into each file; do not overwrite edited bundles."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    imports = ("from collections import deque\n"
               "from arena.bots import shot_direction\n"
               "from arena.sdk import BOMB_FLAME_TICKS, BOMB_FUSE_TICKS, DIRECTIONS, bomb_blast_tiles\n"
               "USE_BOMBS = True\nMAX_ESCAPE_MOVES = 6\n\n")
    common = (imports + inspect.getsource(bomb_first_bot.ThreatMap) + "\n\n"
              + inspect.getsource(bomb_first_bot.Bot).replace("class Bot:", "class BombFirstBase:", 1)
              + "\n\n" + inspect.getsource(StrategyBot))
    entries = []
    for strategy, profile in ROSTER.items():
        source = ('"""' + profile["name"] + ": " + profile["description"]
                  + '\nHandwritten strategy; upload this file alone. No model JSON required.\n"""\n'
                  + common + '\n\nclass Bot(StrategyBot):\n    strategy = ' + repr(strategy) + '\n')
        path = directory / profile["file"]
        if path.exists() and path.read_text() != source:
            raise FileExistsError(f"{path} differs; export to a new directory to preserve it")
        path.write_text(source)
        entries.append(dict(profile, strategy=strategy, sha256=hashlib.sha256(source.encode()).hexdigest()))
    manifest = {"bots": entries, "notes": "Each Python file includes its own frozen common helpers."}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/strategy_roster", help="Directory for upload-ready Python files")
    args = parser.parse_args()
    result = export_roster(args.output)
    for entry in result["bots"]:
        print(f"{entry['name']}: {Path(args.output) / entry['file']}")

"""Frozen-submission round robins and identity-redacted release packs.

This is an organizer tool for trusted local bots, not an execution sandbox.
"""
import csv
import hashlib
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile
import zipfile
from itertools import combinations
from pathlib import Path

from .reference_bots import BOT_INFO, BUILTINS
from .runner import Match, ROOT
from .sdk import RULES_VERSION

METRICS = ("damage_dealt", "damage_taken", "survival_ticks", "self_bomb_deaths", "invalid_actions", "timeouts")


def atomic_json(path, value):
    """Replace a whole record; never expose a half-written JSON document."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=str(path.parent), prefix=".pending-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def runtime_digest():
    digest = hashlib.sha256(sys.version.encode())
    runtime_sources = list((ROOT / "arena").glob("*.py")) + list((ROOT / "examples").rglob("*.py"))
    for path in sorted(runtime_sources):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def fixtures(roster, games_per_pair, seed):
    pairs = list(combinations(roster, 2))
    for game in range(games_per_pair):
        for pair_index, pair in enumerate(pairs):
            yield {"index": game * len(pairs) + pair_index,
                   "participants": list(pair), "bots": list(pair if game % 2 == 0 else pair[::-1]),
                   "seed": seed + game // 8, "rotation": (game // 2) % 4,
                   "game_in_pair": game}


def snapshot_entries(roster, registry, directory):
    directory = Path(directory)
    entries = {}
    labels = {b["id"]: b["name"] for b in BOT_INFO}
    for index, bid in enumerate(roster):
        if bid in BUILTINS:
            entries[bid] = {"name": labels[bid], "version": RULES_VERSION, "builtin": True}
            continue
        original = registry[bid]
        folder = directory / str(index)
        folder.mkdir(parents=True, exist_ok=True)
        code = Path(original["path"]).read_bytes()
        (folder / "bot.py").write_bytes(code)
        artifact = Path(original["path"]).with_name("model.json")
        model = artifact.read_bytes() if artifact.is_file() else b""
        if model:
            (folder / "model.json").write_bytes(model)
        entries[bid] = {"name": original["name"], "version": hashlib.sha256(code + model).hexdigest(),
                        "path": str(folder / "bot.py"), "has_model": bool(model)}
    return entries


def verify_entries(entries):
    for entry in entries.values():
        if entry.get("builtin"):
            continue
        path = Path(entry["path"])
        artifact = path.with_name("model.json")
        model = artifact.read_bytes() if artifact.is_file() else b""
        if hashlib.sha256(path.read_bytes() + model).hexdigest() != entry["version"]:
            raise ValueError("A frozen submission changed. Restore it or start a new round robin.")


def summarize(roster, rows):
    table = {bid: {"bot": bid, "played": 0, "wins": 0, "draws": 0, "losses": 0,
                   "points": 0, "matches_with_errors": 0, "averages": {key: 0 for key in METRICS}} for bid in roster}
    pairs = []
    for a, b in combinations(roster, 2):
        played = [r for r in rows if r["participants"] == [a, b]]
        pairs.append({"participants": [a, b], "played": len(played),
                      "wins": {a: sum(r["winner"] == a for r in played), b: sum(r["winner"] == b for r in played)},
                      "draws": sum(r["winner"] is None for r in played)})
    for row in rows:
        for seat, bid in enumerate(row["bots"]):
            item = table[bid]
            item["played"] += 1
            outcome = "draws" if row["winner"] is None else "wins" if row["winner"] == bid else "losses"
            item[outcome] += 1
            item["points"] += 1 if outcome == "draws" else 3 if outcome == "wins" else 0
            item["matches_with_errors"] += int(bool(row["errors"]))
            for key in METRICS:
                item["averages"][key] += row["players"][seat][key]
    standings = sorted(table.values(), key=lambda r: (-r["points"], r["bot"]))
    for item in standings:
        item["rank"] = 1 + sum(other["points"] > item["points"] for other in standings)
        item["averages"] = {key: value / max(1, item["played"]) for key, value in item["averages"].items()}
    leaders = [item["bot"] for item in standings if item["points"] == standings[0]["points"]]
    return {"standings": standings, "pairings": pairs, "leaders": leaders,
            "winner": leaders[0] if len(leaders) == 1 and rows else None,
            "games": len(rows), "rules_version": RULES_VERSION, "scoring": {"win": 3, "draw": 1, "loss": 0}}


def play_fixture(job, data, fixture):
    """Run one match using fresh working files; commit its replay before its row."""
    data = Path(data)
    verify_entries(job["entries"])
    folder = data / "competitions" / job["id"]
    folder.mkdir(parents=True, exist_ok=True)
    # Hygiene for reviewed code, not protection from arbitrary filesystem access.
    with tempfile.TemporaryDirectory(dir=str(folder), prefix=".match-") as temp:
        registry = {}
        for seat, bid in enumerate(fixture["bots"]):
            entry = job["entries"][bid]
            if entry.get("builtin"):
                continue
            work = Path(temp) / str(seat)
            work.mkdir()
            source = Path(entry["path"])
            shutil.copyfile(source, work / "bot.py")
            if entry.get("has_model"):
                shutil.copyfile(source.with_name("model.json"), work / "model.json")
            registry[bid] = {**entry, "path": str(work / "bot.py")}
        match = Match(fixture["bots"], registry, seed=fixture["seed"], mode=job["config"]["mode"],
                      rotation=fixture["rotation"], anonymous=True)
        try:
            state = match.run()
            verify_entries(job["entries"])
            rid = job["id"] + "_" + str(fixture["index"])
            atomic_json(data / "replays" / (rid + ".json"), match.replay())
            return dict(fixture, replay_id=rid, ticks=state["tick"], players=state["players"],
                        winner=fixture["bots"][state["winner"]] if state["winner"] is not None else None,
                        errors=dict(match.errors))
        finally:
            match.close()


def run_round_robin(job, data, pause=None):
    """Persist after every completed match. An interrupted match is rerun."""
    data = Path(data)
    record = data / "evaluations" / (job["id"] + ".json")
    config = job["config"]
    try:
        if job["runtime_digest"] != runtime_digest():
            raise ValueError("Engine/runtime sources changed; start a new run instead of mixing versions.")
        verify_entries(job["entries"])
        completed = {row["index"] for row in job["rows"]}
        for fixture in fixtures(config["roster"], config["games_per_pair"], config["seed"]):
            if fixture["index"] in completed:
                continue
            if pause and pause.is_set():
                job["status"] = "paused"
                break
            job["rows"].append(play_fixture(job, data, fixture))
            job["completed"] = len(job["rows"])
            job["report"] = summarize(config["roster"], job["rows"])
            atomic_json(record, job)
        else:
            job["status"] = "complete"
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)[:400]
    job.pop("pause_requested", None)
    atomic_json(record, job)


def public_job(job):
    """The admin UI needs versions, but not local source paths."""
    return {**job, "entries": {bid: {k: v for k, v in entry.items() if k != "path"}
                               for bid, entry in job.get("entries", {}).items()}}


def anonymous_replay(replay):
    """Allowlist engine-owned fields; never copy names, events or error strings."""
    player_keys = ("id", "x", "y", "hp", "weapon", "cooldown", "shield", "alive", "protection",
                   "respawn_at", "kills", "suicides", "deaths", "damage_dealt", "damage_taken",
                   "self_bomb_deaths", "survival_ticks", "invalid_actions", "timeouts")
    entity_keys = ("x", "y", "owner", "dx", "dy", "explode_at", "explosion_id", "expires_at", "kind", "at")
    frames = []
    for source in replay["frames"]:
        frame = {key: source[key] for key in ("tick", "seed", "mode", "max_ticks", "board", "done", "winner", "result")}
        if source["done"]:
            frame["result"] = "ROUND DRAW" if source["winner"] is None else f"PLAYER {source['winner'] + 1} WINS"
        else:
            frame["result"] = None
        frame["players"] = [{**{key: p[key] for key in player_keys if key in p}, "name": f"Player {i+1}"}
                            for i, p in enumerate(source["players"])]
        for key in ("bombs", "projectiles", "flames", "pickups"):
            frame[key] = [{k: obj[k] for k in entity_keys if k in obj} for obj in source[key]]
        frame["supply_drop"] = ({k: source["supply_drop"][k] for k in entity_keys if k in source["supply_drop"]}
                                if source.get("supply_drop") else None)
        frame["events"] = []
        frames.append(frame)
    return {"version": 1, "rules_version": replay["rules_version"], "bot_ids": ["player_1", "player_2"],
            "mode": replay["mode"], "seed": replay["seed"], "max_ticks": replay["max_ticks"],
            "frames": frames, "actions": [], "errors": {}}


def build_release(job, data):
    """Same identity-redacted ZIP for everyone; original reports stay private."""
    data = Path(data)
    folder = data / "competitions" / job["id"]
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / "anonymous-replays.zip"
    if output.is_file():
        return output
    rows = list(job["rows"])
    random.SystemRandom().shuffle(rows)
    fd, temp = tempfile.mkstemp(dir=str(folder), suffix=".zip")
    os.close(fd)
    try:
        results = []
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for i, row in enumerate(rows):
                replay = anonymous_replay(json.loads((data / "replays" / (row["replay_id"] + ".json")).read_text()))
                name = f"replays/match_{i+1:04d}.json"
                archive.writestr(name, json.dumps(replay, allow_nan=False))
                final = replay["frames"][-1]
                results.append({"replay": name, "winner": final["winner"], "ticks": final["tick"],
                                "players": [{"name": p["name"], **{key: p[key] for key in METRICS}} for p in final["players"]]})
            archive.writestr("results.json", json.dumps({"rules_version": job["rules_version"],
                              "mode": job["config"]["mode"], "matches": results}, allow_nan=False))
            archive.writestr("README.txt", "Identity-redacted development replays. Players are labeled within each match only.\n"
                              "Names, submission IDs, paths, events and error text are omitted.\n"
                              "Behavior and maps can still be recognized; anonymity is not guaranteed.\n"
                              "Spectator frames are for offline review, never live bot observations.\n"
                              "Import the replays folder in Experiment Lab, or load one JSON in Arena.\n")
        os.replace(temp, output)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return output


def _safe_archive_stem(value):
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-._")[:48]
    return stem or "participant"


def build_participant_release(job, data, participant):
    """Build a cached, recipient-specific ZIP with opponents replaced by aliases."""
    data = Path(data)
    roster = job["config"]["roster"]
    if participant not in roster:
        raise ValueError("Participant is not in this round robin")
    folder = data / "competitions" / job["id"]
    folder.mkdir(parents=True, exist_ok=True)
    participant_index = roster.index(participant)
    own_name = job["entries"][participant]["name"]
    output = folder / f"participant-{participant_index:02d}.zip"
    if output.is_file():
        return output, _safe_archive_stem(own_name)

    opponents = [bid for bid in roster if bid != participant]
    random.SystemRandom().shuffle(opponents)
    aliases = {bid: f"Opponent {index + 1:02d}" for index, bid in enumerate(opponents)}
    rows = [row for row in job["rows"] if participant in row["bots"]]
    random.SystemRandom().shuffle(rows)
    private_seed_rng = random.SystemRandom()
    fd, temp = tempfile.mkstemp(dir=str(folder), suffix=".zip")
    os.close(fd)
    try:
        matches = []
        aggregate = {alias: {"played": 0, "wins": 0, "draws": 0, "losses": 0,
                             "matches_flagged": 0, "your_metrics": {key: 0 for key in METRICS},
                             "opponent_metrics": {key: 0 for key in METRICS}}
                     for alias in aliases.values()}
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for index, row in enumerate(rows, start=1):
                own_seat = row["bots"].index(participant)
                other_seat = 1 - own_seat
                opponent = row["bots"][other_seat]
                alias = aliases[opponent]
                replay = anonymous_replay(json.loads((data / "replays" / (row["replay_id"] + ".json")).read_text()))
                replay["bot_ids"] = ["your_bot" if seat == own_seat else alias for seat in range(2)]
                private_seed = private_seed_rng.randrange(1, 2**31)
                replay["seed"] = private_seed
                for frame in replay["frames"]:
                    frame["seed"] = private_seed
                    for seat, player in enumerate(frame["players"]):
                        player["name"] = "Your bot" if seat == own_seat else alias
                replay_name = f"replays/match_{index:04d}.json"
                archive.writestr(replay_name, json.dumps(replay, allow_nan=False))

                own_metrics = {key: row["players"][own_seat][key] for key in METRICS}
                opponent_metrics = {key: row["players"][other_seat][key] for key in METRICS}
                outcome = "draw" if row["winner"] is None else "win" if row["winner"] == participant else "loss"
                stats = aggregate[alias]
                stats["played"] += 1
                stats["wins" if outcome == "win" else "draws" if outcome == "draw" else "losses"] += 1
                stats["matches_flagged"] += int(bool(row.get("errors")))
                for key in METRICS:
                    stats["your_metrics"][key] += own_metrics[key]
                    stats["opponent_metrics"][key] += opponent_metrics[key]
                matches.append({"replay": replay_name, "opponent": alias, "outcome": outcome,
                                "ticks": row["ticks"], "flagged_for_review": bool(row.get("errors")),
                                "your_metrics": own_metrics})

            for stats in aggregate.values():
                played = max(1, stats["played"])
                stats["your_metrics"] = {key: value / played for key, value in stats["your_metrics"].items()}
                stats["opponent_metrics"] = {key: value / played for key, value in stats["opponent_metrics"].items()}
            summary = io.StringIO()
            columns = ["opponent", "played", "wins", "draws", "losses", "points", "matches_flagged"]
            columns.extend(f"average_{key}" for key in METRICS)
            writer = csv.DictWriter(summary, fieldnames=columns)
            writer.writeheader()
            for alias, stats in aggregate.items():
                writer.writerow({"opponent": alias, "played": stats["played"], "wins": stats["wins"],
                                 "draws": stats["draws"], "losses": stats["losses"],
                                 "points": 3 * stats["wins"] + stats["draws"],
                                 "matches_flagged": stats["matches_flagged"],
                                 **{f"average_{key}": stats["your_metrics"][key] for key in METRICS}})
            archive.writestr("opponent-summary.csv", summary.getvalue())
            archive.writestr("report.json", json.dumps({
                "report_type": "participant-round-robin-feedback",
                "rules_version": job["rules_version"],
                "game_mode": job["config"]["mode"],
                "your_bot": {"name": own_name, "version": job["entries"][participant]["version"]},
                "matches_played": len(matches),
                "matches": matches,
                "per_opponent": aggregate,
                "scoring": {"win": 3, "draw": 1, "loss": 0},
            }, allow_nan=False))
            archive.writestr("README.txt", (
                "Your round-robin feedback pack. Your bot is named 'Your bot'; each opponent has a consistent anonymous alias within this ZIP.\n"
                "opponent-summary.csv is a spreadsheet-friendly per-opponent summary. report.json includes per-match details and averages by alias; each match links to an offline replay.\n"
                "Opponent names, submission IDs, original seeds, paths, source/model files and error text are omitted.\n"
                "Aliases are independently assigned in each participant's ZIP. Replays and map/behavior patterns may still reveal identities; anonymity is not guaranteed.\n"
                "Submissions are frozen and each match starts a fresh bot process and working copy. This report measures performance; it is not a record of in-game learning, model-weight updates or decision explanations.\n"
                "Teams can use these results to form hypotheses, compare opponents and tune between sessions. Load the replays folder in Experiment Lab's Replay Library.\n"
            ))
        os.replace(temp, output)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return output, _safe_archive_stem(own_name)

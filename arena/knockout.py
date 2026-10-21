"""Deterministic single-elimination brackets, reconstructed from committed games.

Series play balanced blocks, not first-to-N games. Unresolved ties require a
recorded organizer ruling after two additional eight-game blocks.
"""
import random
from pathlib import Path

from .competition import atomic_json, play_fixture, runtime_digest, verify_entries


def seed_order(size):
    order = [0, 1]
    while len(order) < size:
        bound = len(order) * 2 - 1
        order = [value for seed in order for value in (seed, bound - seed)]
    return order


def bracket_report(config, rows, decisions=()):
    roster = list(config["roster"])
    if config.get("shuffle", True):
        random.Random(config["seed"]).shuffle(roster)
    size = 1 << (len(roster) - 1).bit_length()
    order = seed_order(size)
    base = config["games_per_pair"]
    rulings = {d["series_id"]: d for d in decisions}
    rounds, series, previous = [], [], []
    round_index = 0
    while size >> (round_index + 1):
        count = size >> (round_index + 1)
        title = "Final" if count == 1 else "Semifinals" if count == 2 else "Quarterfinals" if count == 4 else "Round of 16"
        current = []
        for slot in range(count):
            sid = f"r{round_index + 1}s{slot + 1}"
            if not round_index:
                seeds = order[slot * 2:slot * 2 + 2]
                participants = [roster[i] if i < len(roster) else None for i in seeds]
                available = True
                sources = []
            else:
                children = previous[slot * 2:slot * 2 + 2]
                available = all(c["status"] in ("complete", "bye") for c in children)
                participants = [c["winner"] for c in children]
                sources = [c["id"] for c in children]
            games = [row for row in rows if row.get("series_id") == sid]
            wins = {bid: sum(row["winner"] == bid for row in games) for bid in participants if bid is not None}
            node = {"id": sid, "ordinal": len(series), "round": round_index, "title": title,
                    "slot": slot + 1, "participants": participants, "sources": sources,
                    "played": len(games), "draws": sum(row["winner"] is None for row in games),
                    "wins": wins, "winner": None, "status": "pending", "target": base}
            if available:
                present = [p for p in participants if p is not None]
                if len(present) == 1:
                    node.update(status="bye", winner=present[0], target=0)
                elif len(present) == 2:
                    node["status"] = "ready"
                    played = len(games)
                    # Only decide on a full block: every bot gets equal seats/corners.
                    if played >= base and (played - base) % 8 == 0:
                        a, b = participants
                        if wins[a] != wins[b]:
                            node.update(status="complete", winner=a if wins[a] > wins[b] else b, target=played)
                        elif played >= base + 16:
                            ruling = rulings.get(sid)
                            if ruling and ruling["winner"] in present:
                                node.update(status="complete", winner=ruling["winner"], ruling=ruling, target=played)
                            else:
                                node.update(status="awaiting_decision", target=played)
                        else:
                            node["target"] = played + 8
                    elif played >= base:
                        node["target"] = base + ((played - base) // 8 + 1) * 8
            current.append(node)
            series.append(node)
        rounds.append({"title": title, "series": current})
        previous = current
        round_index += 1
    winner = series[-1]["winner"] if series[-1]["status"] == "complete" else None
    extra = sum(max(0, node["target"] - base) for node in series)
    return {"rounds": rounds, "series": series, "winner": winner,
            "leaders": [winner] if winner else [], "seeded_roster": roster,
            "expected_games": (len(roster) - 1) * base + extra,
            "games": len(rows), "tie_policy": "Two extra balanced blocks, then recorded organizer ruling"}


def next_fixture(config, node):
    game = node["played"]
    pair = node["participants"]
    return {"index": node["ordinal"] * (config["games_per_pair"] + 16) + game,
            "series_id": node["id"], "participants": pair,
            "bots": pair if game % 2 == 0 else pair[::-1],
            "seed": config["seed"] + node["round"] * (config["games_per_pair"] // 8 + 2) + game // 8,
            "rotation": (game // 2) % 4, "game_in_pair": game}


def run_knockout(job, data, pause=None):
    record = Path(data) / "evaluations" / (job["id"] + ".json")
    try:
        if job["runtime_digest"] != runtime_digest():
            raise ValueError("Engine/runtime sources changed; start a new run instead of mixing versions.")
        verify_entries(job["entries"])
        while True:
            job["report"] = bracket_report(job["config"], job["rows"], job.get("decisions", []))
            job["completed"] = len(job["rows"])
            job["total"] = job["report"]["expected_games"]
            if job["report"]["winner"]:
                job["status"] = "complete"
                break
            if pause and pause.is_set():
                job["status"] = "paused"
                break
            # Resolve series in bracket order; never skip a tied semifinal.
            node = next(n for n in job["report"]["series"] if n["status"] not in ("complete", "bye"))
            if node["status"] == "awaiting_decision":
                job["status"] = "awaiting_decision"
                break
            if node["status"] != "ready":
                raise ValueError("Bracket dependencies are unresolved")
            atomic_json(record, job)
            job["rows"].append(play_fixture(job, data, next_fixture(job["config"], node)))
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)[:400]
    job.pop("pause_requested", None)
    atomic_json(record, job)

"""Learn Hit & Run's scouting limit with an epsilon-greedy bandit.

Run with: python -m arena.train_hit_and_run --games 60
"""
import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from .evaluation import evaluate
from .runner import Match, ROOT


ARMS = (8, 10, 12)
OPPONENTS = ("hunter", "survivor", "bomber")
EPSILON = 0.2
BASE_BOT = ROOT / "examples" / "hit_and_run_bot.py"


def variant_sources(directory):
    source = BASE_BOT.read_text()
    marker = "MAX_SCOUT_MOVES = 12"
    if source.count(marker) != 1:
        raise ValueError(f"Expected exactly one {marker!r} in {BASE_BOT}")
    paths = {}
    for arm in ARMS:
        path = directory / f"hit_and_run_{arm}.py"
        path.write_text(source.replace(marker, f"MAX_SCOUT_MOVES = {arm}", 1))
        paths[arm] = path
    return paths


def arm_score(arm, estimates):
    """Macro-average per-opponent reward so no one rival dominates selection."""
    return sum(estimates[arm][opponent] for opponent in OPPONENTS) / len(OPPONENTS)


def choose_arm(episode, rng, counts, estimates):
    # Give every parameter a first result against every opponent before adapting.
    warmup = len(ARMS) * len(OPPONENTS)
    if episode < warmup:
        opponent = OPPONENTS[episode // len(ARMS)]
        arm = ARMS[episode % len(ARMS)]
        return arm, opponent

    opponent = OPPONENTS[(episode - warmup) % len(OPPONENTS)]
    if rng.random() < EPSILON:
        return rng.choice(ARMS), opponent

    scores = {arm: arm_score(arm, estimates) for arm in ARMS}
    best_score = max(scores.values())
    best_arms = [arm for arm in ARMS if abs(scores[arm] - best_score) < 1e-12]
    return rng.choice(best_arms), opponent


def update_estimate(arm, opponent, reward, counts, estimates):
    counts[arm][opponent] += 1
    n = counts[arm][opponent]
    old = estimates[arm][opponent]
    estimates[arm][opponent] = old + (reward - old) / n


def run_episode(arm, opponent, episode, seed, paths):
    registry = {
        "learner": {"path": str(paths[arm]), "name": f"Hit & Run · scout {arm}"}
    }
    ids = ["learner", opponent] if episode % 2 == 0 else [opponent, "learner"]
    candidate_seat = ids.index("learner")
    match = Match(ids, registry, seed=seed, mode="elimination",
                  rotation=episode % 4, record=False)
    try:
        state = match.run()
        if state["winner"] is None:
            outcome, reward = "draw", 0.5
        elif state["winner"] == candidate_seat:
            outcome, reward = "win", 1.0
        else:
            outcome, reward = "loss", 0.0
        metrics = state["players"][candidate_seat]
        return {
            "episode": episode + 1,
            "seed": seed,
            "rotation": episode % 4,
            "candidate_seat": candidate_seat,
            "scout_limit": arm,
            "opponent": opponent,
            "outcome": outcome,
            "reward": reward,
            "damage_dealt": metrics["damage_dealt"],
            "damage_taken": metrics["damage_taken"],
            "survival_ticks": metrics["survival_ticks"],
            "self_bomb_deaths": metrics["self_bomb_deaths"],
            "invalid_actions": metrics["invalid_actions"],
            "timeouts": metrics["timeouts"],
            "errors": match.errors,
        }
    finally:
        match.close()


def selected_arm(estimates):
    scores = {arm: arm_score(arm, estimates) for arm in ARMS}
    best_score = max(scores.values())
    return min(arm for arm, score in scores.items() if abs(score - best_score) < 1e-12)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def train(games=60, seed=30000, output=None):
    if games < len(ARMS) * len(OPPONENTS):
        raise ValueError(f"--games must be at least {len(ARMS) * len(OPPONENTS)} for the warm-up")
    if games > 10000:
        raise ValueError("--games must be at most 10000 so training and held-out seeds remain separate")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_path = Path(output) if output else ROOT / "data" / "models" / f"hit_run_bandit_{stamp}.json"
    if not model_path.is_absolute():
        model_path = ROOT / model_path
    if model_path.suffix.lower() != ".json":
        raise ValueError("--output must use a .json extension")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    report_path = model_path.with_name(model_path.stem + "_report.json")
    bot_path = model_path.with_name(model_path.stem + "_bot.py")
    progress_path = model_path.with_name(model_path.stem + "_progress.json")
    occupied = [path for path in (model_path, report_path, bot_path, progress_path) if path.exists()]
    if occupied:
        raise FileExistsError("Refusing to overwrite existing output(s): " + ", ".join(map(str, occupied)))

    counts = {arm: {opponent: 0 for opponent in OPPONENTS} for arm in ARMS}
    estimates = {arm: {opponent: 0.0 for opponent in OPPONENTS} for arm in ARMS}
    history = []
    rng = random.Random(seed)

    with TemporaryDirectory(prefix="hit-run-bandit-") as temp:
        paths = variant_sources(Path(temp))
        for episode in range(games):
            arm, opponent = choose_arm(episode, rng, counts, estimates)
            row = run_episode(arm, opponent, episode, seed + episode, paths)
            history.append(row)
            update_estimate(arm, opponent, row["reward"], counts, estimates)
            progress = {
                "status": "training",
                "completed": episode + 1,
                "total": games,
                "seed_start": seed,
                "epsilon": EPSILON,
                "counts": counts,
                "mean_reward_by_opponent": estimates,
                "last_match": row,
            }
            write_json(progress_path, progress)
            score = arm_score(arm, estimates)
            print(f"{episode + 1:>3}/{games}: scout={arm} vs {opponent} "
                  f"{row['outcome']} (reward {row['reward']:.1f}); "
                  f"selected-arm estimate {score:.3f}", flush=True)

        chosen = selected_arm(estimates)
        # Keep the learned artifact uploadable as a normal frozen bot.
        final_source = BASE_BOT.read_text()
        marker = "MAX_SCOUT_MOVES = 12"
        if final_source.count(marker) != 1:
            raise ValueError(f"Expected exactly one {marker!r} in {BASE_BOT}")
        old_docstring = (
            '"""Hit-and-run survivor bot for Bot Arena.\n\n'
            'The bot scouts toward the center for a short trip, shoots visible enemies from\n'
            'range, and retreats along its successful path. It only considers a bomb when a\n'
            'nearby enemy is in its projected blast and two roomy escape routes are known.\n\n'
            'This is a hand-written strategy example, not a trained machine-learning model.\n'
            '"""'
        )
        if old_docstring not in final_source:
            raise ValueError("The Hit & Run source description changed; update the artifact header before training")
        final_source = final_source.replace(
            old_docstring,
            '"""Hit-and-run strategy with a bandit-selected scouting limit.\n\n'
            'The strategy rules are hand-written. Training selected MAX_SCOUT_MOVES from a\n'
            'small candidate set using match outcomes; all other behavior stays fixed.\n'
            '"""',
            1,
        )
        bot_path.write_text(final_source.replace(marker, f"MAX_SCOUT_MOVES = {chosen}", 1))

        model = {
            "type": "epsilon_greedy_match_parameter_bandit",
            "strategy": "hit_and_run_bot.py",
            "learned_parameter": "MAX_SCOUT_MOVES",
            "selected_value": chosen,
            "candidate_values": list(ARMS),
            "opponents": list(OPPONENTS),
            "reward": {"win": 1.0, "draw": 0.5, "loss": 0.0},
            "epsilon": EPSILON,
            "seed_start": seed,
            "training_matches": games,
            "counts_by_value_and_opponent": counts,
            "mean_reward_by_value_and_opponent": estimates,
            "selection_score_by_value": {str(arm): arm_score(arm, estimates) for arm in ARMS},
        }

        # Report a frozen baseline and the selected value on the same held-out matches.
        baseline_id, learned_id = "baseline", "learned"
        eval_registry = {
            baseline_id: {"path": str(paths[12]), "name": "Hit & Run · baseline 12"},
            learned_id: {"path": str(paths[chosen]), "name": f"Hit & Run · learned {chosen}"},
        }
        heldout_seed = seed + 100000
        heldout = []
        print("Evaluating frozen baseline and learned bot on held-out matches…", flush=True)
        for opponent in OPPONENTS:
            for candidate, label in ((baseline_id, "baseline"), (learned_id, "learned")):
                result = evaluate(candidate, [opponent], games=12, seed=heldout_seed,
                                  mode="elimination", registry=eval_registry)
                heldout.append({
                    "version": label,
                    "scout_limit": 12 if label == "baseline" else chosen,
                    "opponent": opponent,
                    "seed_start": heldout_seed,
                    "games": result["games"],
                    "wins": result["wins"],
                    "draws": result["draws"],
                    "losses": result["losses"],
                    "win_rate": result["win_rate"],
                    "win_interval": result["win_interval"],
                    "averages": result["averages"],
                })

        report = {
            "created_at": time.time(),
            "status": "complete",
            "model_path": str(model_path),
            "bot_path": str(bot_path),
            "description": "The bandit selects a scouting limit from match rewards; the final bot is frozen.",
            "training": model,
            "training_matches": history,
            "held_out_evaluation": {
                "seed_start": heldout_seed,
                "matches_per_version_per_opponent": 12,
                "results": heldout,
            },
        }
        write_json(model_path, model)
        write_json(report_path, report)
        progress_path.unlink(missing_ok=True)

    print(json.dumps({"selected_scout_limit": chosen,
                      "model": str(model_path),
                      "bot": str(bot_path),
                      "report": str(report_path)}, indent=2), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Learn a Hit & Run scouting limit from match outcomes.")
    parser.add_argument("--games", type=int, default=60,
                        help="training matches (minimum 9; default 60)")
    parser.add_argument("--seed", type=int, default=30000,
                        help="first training seed; held-out tests use a separate seed range")
    parser.add_argument("--output", default=None,
                        help="new model JSON path; refuses to overwrite existing outputs")
    args = parser.parse_args()
    try:
        train(args.games, args.seed, args.output)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))

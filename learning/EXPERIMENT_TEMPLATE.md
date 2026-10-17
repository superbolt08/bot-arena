# Experiment notebook

Copy this for each experiment. Write the prediction before running. Mark unavailable measurements “not measured”; never turn an estimate into a result.

## Your idea

- Team / date:
- Strategy in plain English:
- Prediction and why:
- One variable changed: parameter / rule / algorithm / learned component:
- What stays fixed:

## Make it reproducible

- Code commit and local changes:
- Rules version:
- Bot A and B names, upload IDs and code/model locations:
- Parameter values A and B:
- Opponent versions:
- Per-opponent development seed starts and match counts:
- Mode, tick limit, seat/spawn rotation schedule:
- Report IDs and exports:
- Held-out test status: unused / used once after freezing / no longer held out:

## Compare versions

Use a separate row for each opponent. Do not mix results from different modes or clocks.

| Opponent / version | A: wins / draws / losses | B: wins / draws / losses | Match count / seed start |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

| Diagnostic | Run A | Run B |
| --- | --- | --- |
| Average damage dealt / taken | | |
| Average survival | | |
| Self-bomb deaths | | |
| Invalid actions / timeouts | | |
| Approximate win-rate interval | | |

The app stores individual reports. This notebook is the current comparison tool; automatic paired analysis and final-test locking are not implemented.

## Inspect a failure

- Replay ID and tick:
- What was visible to the bot:
- Decision you expected:
- What actually happened:
- Could the helper/pathfinding, rather than the changed parameter, explain it?
- Did a gain against one rival create a weakness against another?

## Conclude honestly

- Supported / contradicted / inconclusive:
- Evidence:
- What was manual, what was learned, and what stayed handwritten:
- What these results do not establish:
- Final frozen version:
- Held-out outcome and whether you kept it out of tuning:
- One next experiment:
- AI assistance used and what you independently verified:

## Optional: when fitting a model or learning parameters

Record the learning algorithm, training budget, random seeds, feature/schema version, allowed feedback, reward definition, initial/final checkpoints and evaluation split. Keep training feedback separate from final results. For the imitation example, include teacher agreement, per-mode precision/recall and class support; do not substitute them for gameplay outcomes.

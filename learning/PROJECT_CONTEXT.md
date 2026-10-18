# Project context for students and coding assistants

Read this alongside [the project brief](../docs/TEAM_PITCH.md), [workflow](WORKFLOW.md), [rules](../docs/RULES.md) and [bot API](../docs/BOT_API.md).

## Our objective

Students own their strategy. They write a prediction, run against multiple opponents, inspect evidence, change one thing, compare matched development matches and check a frozen version on held-out conditions.

The workshop teaches algorithms, parameters, controlled experiments, overfitting and generalization. Manual code/parameter changes are not automatically ML. A learning component must actually fit decisions or settings from data. Never claim every iteration will produce a stronger bot.

## What exists

- Welcome introduces the process and reads allowlisted repository Markdown guides.
- Experiment Lab evaluates bot versions and stores reports/replays; it does not train.
- `examples/parameter_bot.py` is a manually parameterized strategy with shared action helpers.
- `arena/engine.py` and `arena/sdk.py` define the seeded game and rules.
- `arena/bots.py` provides reference bots, features and fixed tactical helpers.
- `arena/train.py` is an optional imitation-learning CLI, with `--games` and `--output`; it is not a trainer for arbitrary student strategies.
- `arena/train_hit_and_run.py` is a match-level epsilon-greedy bandit for `MAX_SCOUT_MOVES` in `examples/hit_and_run_bot.py`; it writes estimates, match logs, held-out comparisons and a frozen uploadable bot.
- `examples/learned_bot.py` interprets that tree artifact.
- `arena/parallel_env.py` is an optional PettingZoo adapter, not a complete RL pipeline.
- Generalized parameter learning for arbitrary bots, in-app training, resumable state, final-test enforcement and the 100-match learning league are not implemented.

Rules v0.2: 15×15 board, simultaneous 200 ms ticks, 2–4 participants. Bombs have a two-second fuse, full-axis cross stopped by walls/the first crate, and 0.6-second flames. Each explosion can hit a player once for 2 damage; starting health is three.

## How to assist

- Ask what weakness and hypothesis the student wants to investigate. Help them understand their own algorithm.
- Expose a few meaningful preferences, not arbitrary game-rule constants. Make their ranges and effects clear.
- For a parameter experiment, keep code/helpers fixed. If changing the algorithm, label that separately.
- Preserve seeds, rotations, clocks, rules and opponent versions for comparisons. Keep fresh final conditions out of tuning.
- Use only public bot observations and the bot's memory. Omniscient replay frames are debugging evidence, not online inputs.
- Preserve uploaded bots, models and experiment history. Never overwrite an artifact the student wants to retain.
- Do not silently rewrite the entire strategy or manufacture a rising training curve.
- Uploads run trusted Python locally. A subprocess is not a malicious-code sandbox; do not propose public hosting without a new security scope.
- For broader learning leagues, explicitly define round feedback, persistent state, update budgets and frozen evaluation. Current bot instances reset between matches; the Hit & Run CLI trainer performs its updates outside the bot process between matches.

## Suggested assistant prompt

> Help me run one controlled Bot Arena experiment. First explain my strategy and the parameter I want to change. Help me predict its effect, keep comparison settings fixed, and inspect one failure. Separate manual changes from anything actually learned from data. Do not rewrite my whole bot or claim improvement without measurements.

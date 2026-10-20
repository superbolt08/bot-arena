# Agent instructions for Bot Arena

## Project purpose

Bot Arena is a local teaching project where students write Python strategies, run controlled matches, inspect evidence, and learn algorithms and machine learning. Prefer changes that make the rules understandable, experiments fair, and student work easy to inspect. Do not present manual parameter tuning as machine learning.

## Read before changing behavior

- Read [the project brief](docs/TEAM_PITCH.md) for the audience and learning goals.
- Read [the game rules](docs/RULES.md) and [the bot observation contract](docs/BOT_API.md) before changing engine, combat, visibility, or bot APIs.
- For learning features, read the relevant material in `learning/`, especially `WORKFLOW.md`, `PARAMETERS.md`, `ML_CONCEPTS.md`, and the specific trainer guide.

## Architecture

- `arena/engine.py` owns deterministic game state, observations, and tick resolution.
- `arena/sdk.py` defines action names, bot-facing helpers, and the rules version.
- `arena/runner.py` runs built-in and uploaded bots against the shared engine.
- `arena/evaluation.py` runs batches and summarizes match outcomes.
- `arena/server.py` exposes the local API and WebSocket state.
- `viewer/` contains the React and TypeScript interface.
- `examples/` contains uploadable Python bots; `learning/` and `docs/` contain teaching materials.

## Game and observation invariants

- Keep live matches and fast evaluations on the same engine and rules.
- Bot decisions use only `choose_action(observation)`. Do not pass replay frames, spectator snapshots, hidden opponent state, or server internals into a bot.
- The terrain `visible` grid and dynamic-entity `entity_visible` grid have different meanings. Living opponents screen dynamic entities behind them; terrain sight is not blocked by player bodies. Public supply announcements remain public.
- Player screening changes what a bot observes. Blaster projectiles are absorbed by the first other player they hit. Bomb blasts pass through players and stop at walls and crates.
- Elimination timeouts rank survivors by remaining HP, then damage dealt. A tie on both measures is a draw. Same-tick mutual elimination remains a draw; deathmatch uses its own kill-minus-suicide score.
- Keep simulation deterministic for a fixed seed and bot behavior. Rotate seats and spawn corners when comparing bots.
- When changing game rules or observation fields, update `docs/RULES.md`, `docs/BOT_API.md`, the Field Guide if relevant, and `RULES_VERSION` in `arena/sdk.py`. Keep replay and evaluation reporting consistent.

## Learning and evaluation

- Experiment Lab evaluates frozen bots; training examples are command-line programs.
- Clearly distinguish hand-written strategies, manual tuning, imitation learning, and parameter learning.
- Compare against multiple opponent styles and preserve separate held-out seeds for final evaluation. Do not tune against the held-out results and continue calling them held out.
- Report draws, uncertainty, and per-opponent results where available. A higher training score is not proof of general improvement.
- Keep student-facing algorithms small and explainable unless the project brief calls for more complexity.

## Local execution and trust

- Uploaded Python bots run as trusted local code in separate processes; this is not a security sandbox. Keep the server loopback-only. Do not describe local process separation as protection from malicious code.
- Do not expose generated replays or omniscient match state through the bot observation API.
- Generated local bots, replays, evaluations, and model artifacts belong under `data/`; do not add a user's generated match data to source changes unless requested.

## Editing and verification

- Make focused changes and preserve unrelated user edits and generated files.
- Follow the existing Python and TypeScript style in the touched module; avoid broad rewrites for a narrow behavior change.
- Relevant verification commands are `python -m pytest -q` and `npm run build`. State clearly which checks were run and their result.
- The standard local launch is `python run.py`; frontend development uses `npm run dev` alongside the Python server.

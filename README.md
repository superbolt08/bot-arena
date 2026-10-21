# Bot Arena

A local, retro-styled arena for building your own Python bot and learning through fair experiments. Write a strategy, expose meaningful parameters, test different opponents, and use evidence to decide what to change.

## Start with the idea

Read [Why Bot Arena?](docs/TEAM_PITCH.md), a shared project brief for participants, mentors and the team. The goal is to understand algorithms, controlled experiments, overfitting and generalization—not just win one match.

Your loop: predict → run development matches → inspect → change one thing → compare versions → freeze and test fresh conditions. Follow [the six-step workflow](learning/WORKFLOW.md), try [the parameter starter](learning/PARAMETERS.md), and keep [an experiment notebook](learning/EXPERIMENT_TEMPLATE.md).

Manual tuning is experimentation, not automatically ML. Actual learning requires a procedure that fits decisions or parameters from data. The optional [imitation-learning example](learning/IMITATION_LEARNING.md) fits a decision tree, and a small [Hit & Run parameter bandit](learning/PARAMETER_LEARNING.md) learns a scouting limit from match outcomes. A generalized [100-match adaptation league](learning/LEARNING_LEAGUE.md) remains proposed work.

Basic Python is enough for the 2–4 hour core workshop. The game supports two players by default, optional three-/four-player free-for-all, local human play, elimination and deathmatch.

## Run it

Requires Python 3.9+ and Node.js 20.19+ (or 22.12+). Python 3.11+ is recommended for a new installation.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm ci
npm run build
python run.py
```

Open **http://127.0.0.1:8000**. On Windows, use `py -m venv .venv` and `.venv\Scripts\activate` instead of the first two commands. The engine, viewer and process transport use cross-platform APIs; this prototype has been verified on macOS, not yet on Windows/Linux.

The app opens on **Welcome**, with objectives, the experiment process, a starter download and readable repository guides. Use Arena to watch a match and Experiment Lab to evaluate frozen versions.

For frontend development, run `python run.py` and `npm run dev` in separate terminals. Vite proxies the API and WebSocket connection to port 8000. Reload the Python server after backend changes or after creating the first production frontend build.

## What is included

- Seeded 15×15 arena with simultaneous movement, blasters, bombs, destructible crates and supply drops.
- Welcome page, in-app Markdown guides and a parameterized starter strategy.
- 2–4 participants; one participant can be a keyboard-controlled human.
- Real-time WebSocket viewer, bot-view toggle, pause, single-step and speed controls.
- Four reference bots, Python bot upload and optional JSON model upload.
- Batch evaluation with rotated seats/corners, replay links, uncertainty intervals and version history.
- JSON match replays, export/import and timeline scrubbing.
- CPU imitation-learning example with separate train, validation and evaluation seeds.
- CLI bandit trainer that selects a Hit & Run scouting limit from match outcomes and checks a frozen result on held-out seeds.
- Optional PettingZoo parallel environment adapter for further RL experiments.
- Engine, runner and API tests.

The match viewer and benchmarks use the **same engine**. Fast evaluation removes rendering and wall-clock pacing; it does not change the rules.

## Organizer competitions

In **Experiment Lab**, switch **Experiment format** to **Round robin**. Select a roster of 2–16 bot versions and run every pair, with balanced seats/corners, standings, matchup scores and replays. Completed matches are saved; pause/resume and interrupted-run recovery are supported while submission/runtime fingerprints remain unchanged.

Choose **Knockout** for a single-elimination bracket with byes, seeded/shuffled placement, semifinal-to-final progression and a real champion. Tied series play up to two additional balanced eight-game blocks, then pause for an explicitly recorded organizer ruling. Publish that ruling policy before the event.

For a live audience in either format, open **Audience view**: introduce each pairing and trigger suspenseful result reveals. Knockout includes a spoiler-controlled bracket overview and a gold grand-final champion reveal with trophy/confetti. The host controls every reveal; tied results are not silently broken. Use fullscreen where supported, or maximize the window.

Download the private organizer report for your records, or the **Anonymous replay pack** to share the same identity-redacted results/replays with every team. Round robin also has an optional individual ZIP per participant, with anonymous opponent aliases, that team's replays and a per-opponent performance report. These are metrics for analysis, not a record of in-game learning: both formats evaluate frozen submissions without carrying learned updates across matches. See [the competition guide](docs/COMPETITIONS.md) for contents, scoring, recovery and privacy limits.

## Learning workshop and team proposal

For Python beginners, start with the [2–4 hour workshop pack](learning/README.md): the student-owned strategy workflow, concepts, parameter exercise, experiment template, context for coding assistants and curated reading.

For participants and planning, see [the shared project brief](docs/TEAM_PITCH.md) and [learning tools roadmap](docs/LEARNING_STUDIO_SPEC.md). Experiment Lab evaluates frozen bots; it does not automatically adjust their parameters. The two optional model trainers use the CLI.

## First bot

Download the parameter starter from Welcome, or edit [examples/parameter_bot.py](examples/parameter_bot.py). Its complete `Bot` class includes these manually chosen preferences:

```python
PARAMETERS = {
    "retreat_health": 1,
    "aggression": 0.7,
    "pickup_priority": 0.4,
}
```

Use **Upload bot**, select your `.py` file, give it a name and confirm that you trust the code. It is validated and registered as a new version. Choose it in Match Setup or Experiment Lab.

Bot files must define `Bot`, support a no-argument constructor and implement `choose_action(observation)`. Instance fields persist within a match and reset between matches. Initialization has a five-second deadline. Each decision has a 100 ms deadline. Prints go to stderr and do not corrupt the action protocol. A timed-out or crashed bot waits for the remaining match; the error appears in the UI and evaluation report. Invalid action strings become `wait` and increment the invalid-action count. A blocked but valid movement is not an invalid action.

Uploads execute **trusted local Python code** in separate processes. They are not sandboxed against filesystem/network access or malicious behavior. Keep the server bound to loopback. Public hosting needs container/VM isolation, resource limits, authentication and a job queue; those are outside this local prototype.

## Controls

Select `You · keyboard` for one participant. Click the board after launch.

| Key | Action |
| --- | --- |
| WASD / arrow keys | Move |
| I / J / K / L | Fire north / west / south / east |
| Q | Switch blaster / bomb |
| Space | Fire north, or plant a bomb when equipped |

Keyboard input follows the same one-action-per-tick rule as bots. A fire action with the bomb weapon equipped places a bomb on your tile.

## Rules and timing

See [the full rules](docs/RULES.md). Defaults: 200 ms ticks, three HP, one active bomb per player, a ten-tick bomb fuse, full-axis blasts blocked by walls/the first crate, three-tick (0.6-second) flames and a five-tick blaster cooldown. Each explosion deals 2 damage at most once per player, including later entry into its flames. Elimination ends at 450 ticks (90 seconds); timeout survivors are ranked by HP, then damage dealt. Deathmatch ends at 900 ticks (three minutes). Numerical balance is provisional.

## Optional: a working imitation-learning experiment

With the virtual environment activated:

```bash
python -m arena.train --games 20
```

The script:

1. Collects Sentinel's tactical labels on training seeds starting at 100.
2. Fits a depth-limited decision tree to eight observation features.
3. Validates on separate whole matches starting at seed 5000.
4. Tests teacher and learner against Wanderer, Deadeye and Fuse on evaluation seed 10000 with rotated starts.
5. Writes `data/models/model.json` and `data/models/training_report.json`.

Upload `examples/learned_bot.py` together with `model.json` to play it in the app. The artifact is plain JSON; no pickle deserialization or sklearn dependency is needed inside the uploaded bot.

This is **imitation learning of tactical modes**, not reinforcement learning or end-to-end learning from pixels. Pathfinding and action execution remain handwritten. A high label accuracy only means the classifier imitates the teacher; consult gameplay results separately. Try altering features, depth, teacher demonstrations and opponent composition. Four matches per opponent in the worked example are a smoke benchmark, not evidence of competitive superiority.

For optional RL experiments:

```bash
python -m pip install -r requirements-rl.txt
```

`arena.parallel_env.ArenaEnv` implements PettingZoo's Parallel API with an eight-feature tactical observation. It is a small teaching wrapper, not a complete spatial neural-agent representation. Extend it with board channels and memory for stronger agents. Terminal rewards are +1 for winning, −1 for elimination and 0 for a surviving draw. Game-clock draws are terminal rule outcomes; training cutoffs should be represented separately as truncations.

## Evaluation

Choose a candidate, 1–3 opponents, a seed start and a match count in Experiment Lab. Maps repeat in groups of four; spawn geometry rotates each match and seat assignments cycle. Use multiples of 12 for 3-player evaluations to balance seat and corner combinations. Same configuration and bot versions reproduce deterministic bots' results, apart from OS-related decision timeouts. Uploaded bots must seed their own randomness.

Win rate uses **all games including draws** as the denominator. The 95% Wilson interval is a rough descriptive interval; repeated maps and related opponents are correlated, so it is not a rigorous independent-sample guarantee. Placement in elimination uses survival duration with shared ranks for same-tick eliminations; deathmatch uses kills minus suicides. Inspect draw rate, survivability, failures and opponents separately. The UI stores experiments so you can switch between versions; JSON export supports deeper analysis. There is no automated significance test or ranking league yet.

Metrics distinguish attempted post-shield damage dealt from HP actually lost. Overkill can therefore make damage-dealt totals exceed damage-taken totals. Training rewards never alter official scoring.

To explore weapon balance, upload [Bomb First](examples/bomb_first_bot.py): it plants bombs with a planned escape, then switches to blaster support. Its [comparison guide](docs/BOMB_FIRST_BOT.md) explains how to run it against Deadeye and create a blaster-only control with the same navigation code.

For a broader Round Robin, generate the [four-strategy roster](docs/STRATEGY_ROSTER.md): Crossfire combines bomb pressure with blaster follow-up, Breach & Shoot bombs crates until it sees an enemy, Range Keeper uses only the blaster, and Siege uses only bombs. Run `python -m examples.strategy_roster` to create the individual upload files.

## Replays and storage

`data/bots/` stores imported code, model JSON and version manifests. `data/replays/` stores complete frames plus action logs. `data/evaluations/` stores finished reports. `data/models/` stores the worked learning example. These generated folders are gitignored. Replays intentionally contain omniscient match state for debugging; do not provide that data as a bot observation. JSON frame playback works without importing or executing the original bot code.

Replay files can be several MB per match. Batch runs save every replay, so periodically remove old generated results when no longer needed. The prototype currently supports one evaluation batch and up to four live matches per server process. Stop/skip of an evaluation batch is not implemented.

## Tests

```bash
python -m pytest -q
npm run build
```

Coverage includes reproducibility, movement collisions, simultaneous kills, blast blocking and chaining, visibility, stale memory, pickups, cooldowns, respawns, bot timeouts, API validation, WebSocket state and replay output.

## Structure

```text
arena/       Engine, SDK, reference bots, runner, API, evaluation and training
viewer/      React + TypeScript UI and pixel-style canvas renderer
examples/    Uploadable starter and learned bots
tests/       Engine, process and API verification
docs/        Shared project brief, rules, observation contract and learning roadmap
learning/    Strategy workflow, parameter guide, workshop, context and optional ML tracks
data/        Generated local bots, replays, reports and model artifacts
```

## Research references

Pommerman inspired the small action interface, bomb timing and reference-opponent approach. Our engine is an original implementation with blasters, health, explicit switching and different observation rules.

- [Pommerman project](https://github.com/MultiAgentLearning/playground)
- [Borealis: learning challenges and opponent generalization](https://rbcborealis.com/research-blogs/pommerman-team-competition-or-how-we-learned-stop-worrying-and-love-battle/)
- [Imitation and reinforcement learning in Pommerman](https://arxiv.org/abs/1911.04947)
- [PettingZoo Parallel API](https://pettingzoo.farama.org/api/parallel/)

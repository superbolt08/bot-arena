# Participant onboarding: build a bot, test an idea

Use this guide to go from a fresh fork to a first bot experiment. The goal is to build a strategy you can explain and learn from evidence, not to win on the first try. Allow about 2–4 hours for the core activity; install the project before the session if possible.

## 1. Get the project running

1. Open the repository shared by your instructor and create a fork on GitHub.
2. Clone your fork to your computer and open its folder in a terminal.
3. Follow [Run it in the README](../README.md#run-it) to install dependencies and start the local server. Use the README's Windows activation commands if needed.
4. Open `http://127.0.0.1:8000` and confirm the **Welcome** page loads. Keep the server terminal open while you use the app.

If setup fails, copy the complete error and note your operating system and the command you ran. Ask your instructor in the workshop Discord or open an issue in the repository with those details. Do not post credentials, access tokens or other secrets.

## 2. Explore before coding

Open **Arena** and try these five tasks:

1. Run a match between two built-in bots and watch it through to the result.
2. Replay the match or pause/step through a moment when a bot moves or attacks. Describe what happened.
3. Change the matchup. Compare at least two styles: Wanderer (random baseline), Deadeye (blaster specialist), Sentinel (cautious) and Fuse (bomb tactician).
4. Play one match yourself by selecting **You · keyboard**. Try moving, firing and switching weapons using the [README controls](../README.md#controls).
5. Open **Experiment Lab** and run a small batch against one opponent. Find the result summary and one replay.

These are orientation exercises, not a score threshold. For a first comparison of strategies, separate two-player batches are easier to interpret than a four-player match.

## 3. Read and sketch a strategy

The built-in reference bots are implemented in [`arena/bots.py`](../arena/bots.py): Wanderer, Deadeye, Sentinel, Fuse, Hit and Run, Crossfire, Breach & Shoot and Range Keeper. Select them in the Bot Library, Arena or Experiment Lab. Uploadable strategy examples also live in [`examples/`](../examples/); there is no `bots/` folder. Start from [`examples/parameter_bot.py`](../examples/parameter_bot.py) and its [guide](PARAMETERS.md), or download **Get the starter bot** from Welcome.

The added examples are the memory-fixed HitnRun3 strategy under its participant-facing name **Hit and Run**, plus **Crossfire**, **Breach & Shoot** and **Range Keeper**. To export standalone copies of the roster strategies, the generator also creates **Siege**. Run this from the repository root with your Python environment activated:

```bash
python -m examples.strategy_roster
```

The standalone files are written to `data/strategy_roster/`, which is local generated data and is not committed to Git. This export step is optional; the four named strategies are already available in the app. See the [strategy roster guide](../docs/STRATEGY_ROSTER.md) for their styles and an example comparison.

Before asking a coding assistant to implement anything, write a few sentences:

- What should the bot do when no opponent is visible?
- When should it attack, seek supplies, escape danger or use a bomb?
- What situation might make this strategy fail?
- What result would convince you to change it?

Choose one clear idea to start: pursue visible opponents, keep distance and fire, seek supplies at low health, or place bombs only when there is a safe escape. A circular movement pattern can be an experiment too, but specify when it should stop or change direction. These are examples, not required strategies. The observation contract in [BOT_API.md](../docs/BOT_API.md) describes what your bot can actually see.

## 4. Build and compare

1. Make a first version that expresses your idea. You can use AI-assisted coding, but read through the result and be ready to explain its decisions.
2. Upload it using **Upload bot** and give it a versioned name such as `Orbit · A`.
3. Watch one match in Arena. If it behaves unexpectedly, inspect what the bot could observe and which rule selected its action.
4. In Experiment Lab, compare against at least two opponent styles in separate two-player batches. Record opponents, versions, mode, seed start and match count.
5. Change one rule or parameter, save/upload a second version, and repeat the same configurations. Compare wins, draws, losses, damage and survival; inspect a failure replay as well.

Use the [experiment notebook](EXPERIMENT_TEMPLATE.md) to record a prediction before each comparison. Experiment Lab evaluates frozen versions; it does not automatically train or tune your bot. The [six-step workflow](WORKFLOW.md) explains development matches and a final held-out check. Ask your instructor to reserve fresh seeds or opponents for that final check; the app does not enforce a hidden test set.

## What to share

Bring your strategy description, both bot versions, your prediction and a short results summary. Include one replay or failure that taught you something. A surprising or negative result is useful when you can explain what it changed in your thinking.

For more depth, continue with the [workshop agenda](WORKSHOP.md), [ML concepts guide](ML_CONCEPTS.md) or [learning resources](RESOURCES.md). Manual strategy design and parameter tuning are valuable experiments, but they are not automatically machine learning.

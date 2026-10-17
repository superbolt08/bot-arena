# Your six-step experiment loop

Build a strategy you understand. Use battle results to challenge your assumptions. Repeat with intent, not just until you get a favorable screenshot.

## 1. Write a strategy and a prediction

Describe how your bot chooses actions. Pick one weakness and make a testable prediction: “Increasing `retreat_health` from 1 to 2 should reduce deaths against Deadeye, but may reduce damage dealt.” Record this in [an experiment notebook](EXPERIMENT_TEMPLATE.md) before running matches.

## 2. Run against several opponents

Upload your version and use Experiment Lab to evaluate it against multiple styles. For an interpretable beginner comparison, run separate two-player batches against Wanderer, Deadeye and Fuse; a single multiplayer batch answers a different question. Record the candidate and opponent versions, mode, seed start, match count, rules version and tick limit.

Use development seeds for iteration. The current app accepts a seed start; it does not enforce a hidden final-test partition. Ask an instructor to keep final seeds/opponent versions separate, or reserve them yourself without inspecting their results during development.

## 3. Inspect the evidence

Compare wins, draws and losses per opponent, damage, survival, self-bomb deaths, invalid actions and timeouts. Watch a failure replay and switch to the bot's perspective. What could it actually observe? Was the problem a decision, pathfinding, a narrow parameter setting or an invalid assumption?

The app saves evaluation reports and replays locally. Export the report and put its ID in your notes. Match statistics are evidence for development; they do not automatically fit a model or become a training dataset.

## 4. Change one thing

Change one rule, one parameter or one learned component. For the first exercise use [the parameter starter](PARAMETERS.md). Save/upload it as a new version; preserve the previous one.

If a rule cannot express the behavior you need, change the algorithm deliberately. Record that separately from a parameter-only experiment. Do not change game physics or read hidden opponent state to improve a score.

## 5. Compare on the same development matches

Keep seeds, opponent versions, spawn/seat rotation schedule, mode and tick limit matched. Record A and B side by side in your notebook; the app stores individual reports but does not yet offer an automatic paired A/B analysis.

Ask whether the gain is consistent across opponents or bought at the expense of another matchup. Small batches and repeated maps are noisy; the app's interval is descriptive, not a guarantee. “Inconclusive” is an acceptable result.

## 6. Freeze, then test on something new

Choose your final version using development evidence. Freeze the code and parameters, then evaluate on held-out seeds and ideally a new opponent version or style. Do not update the bot from these results and still call the same set a fresh final test. Once used for tuning, it is development data.

Finish with your hypothesis, the result, a failure case, the limitations and one next experiment. Learning credit should reflect the reasoning, not only the leaderboard.

## Where actual learning can enter

Manual iteration is algorithm development informed by evidence. A learning procedure can later select parameters from battle outcomes while the strategy code stays fixed. The [100-match learning-league proposal](LEARNING_LEAGUE.md) describes that extension; it is not implemented. The [optional imitation track](IMITATION_LEARNING.md) is an existing example of fitting a different decision model from teacher demonstrations.

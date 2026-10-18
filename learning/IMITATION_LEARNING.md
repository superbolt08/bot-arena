# How to train an imitation model

This is an optional supervised-learning track, not the main workshop. For the student-owned strategy and parameter workflow, start with [the core workshop](WORKSHOP.md). Installation and an instructor dry run happen beforehand; do not spend the workshop installing dependencies. Pair participants when useful.

## Finish line

Each pair leaves with two trained JSON models, an uploaded learned bot, a comparable evaluation for each, and a short explanation of what changed. Improving win rate is not required; explaining an honest result is.

## Three-hour agenda

| Minutes | Activity | Evidence |
| --- | --- | --- |
| 0–15 | Watch a reference match; distinguish rules from learning | Identify one learned decision and one fixed helper |
| 15–35 | Trace an observation, its features and teacher label | Explain one sample in plain English |
| 35–60 | Train Run A; open its model and report | Saved artifact, sample counts, per-mode scores |
| 60–85 | Upload Run A; benchmark and inspect a replay | Evaluation configuration and one failure example |
| 85–95 | Break | — |
| 95–125 | Predict an effect, change one setting, train Run B | Written hypothesis and second artifact |
| 125–155 | Run the same benchmark; compare | A/B results, limitations, fixed-helper explanation |
| 155–180 | Share findings and discuss generalization | Completed experiment record and next experiment |

For **two hours**, use instructor-prepared installation and reference reports, shorten the introduction, and perform only one A/B comparison. For **four hours**, add a new opponent or data-budget comparison after the first experiment. RL is an optional instructor preview, not a required beginner task.

## 1. Prepare

Follow the repository [setup instructions](../README.md#run-it). Activate the Python virtual environment and open the app in another terminal. Read [the concepts](ML_CONCEPTS.md) and the [observation contract](../docs/BOT_API.md).

Use fresh output folders for each run. The trainer overwrites a model/report if the same destination is reused. Never overwrite a bot or model you want to keep.

## 2. Train Run A

From the repository root, with the virtual environment active:

```bash
python -m arena.train --games 20 --output data/models/workshop/run-a/model.json
```

The current CLI accepts `--games` and `--output`; other controls below are small source edits, not existing CLI flags. A four-game run is a troubleshooting smoke test if time is tight, not an adequate competition benchmark.

The command collects teacher data, fits a tree, validates it, and runs teacher/learner smoke benchmarks. Open:

- `data/models/workshop/run-a/model.json`
- `data/models/workshop/run-a/training_report.json`

Find the feature names and root split in the model. The root node's `feature` is an index into `feature_names`; its left branch is used for values at or below `threshold`. Leaf nodes have `left == -1` and return `label`.

In the report, compare training and validation sample counts, validation accuracy and per-mode recall. Ask: how many escape examples were present? A mode absent from a small validation set has not been meaningfully tested.

Current caveats: raw demonstration rows, confusion matrices and tree visualizations are not exported. The CLI's benchmarks use a 250-tick limit and four games per candidate/opponent. These are smoke results, not directly comparable with a 450-tick elimination run in the UI.

## 3. Play the actual exported model

Upload `examples/learned_bot.py` with Run A's `model.json`, using a name such as `Team A · learned A`. Uploading a model does not retrain it. Run a match, then use Experiment Lab for batch evaluation.

Record a classroom comparison configuration before running A or B. Suggested starting point: elimination, one reference opponent, 12 matches and seed start 20000. Repeat against a second opponent if time allows. Use the same settings and opponent version for both artifacts. Twelve games is a classroom observation, not strong statistical evidence. Rotate starts as the app does; do not select only favorable replays.

These visible A/B results are development feedback. For any final competition claim, the instructor should select a separate undisclosed seed/opponent set and evaluate only after teams freeze their artifacts. Reusing seed 10000 from the CLI report is not a fresh final test.

## 4. Change one variable for Run B

Choose one experiment, not both at once:

**Model-capacity experiment:** find `DecisionTreeClassifier(max_depth=5, ...)` in `arena/train.py`. Change only `max_depth` to `1`, predict which modes may be confused, and repeat the same 20-game command with `--output data/models/workshop/run-b/model.json`. Keep all other settings fixed. Save the source difference and restore the setting you intend to retain after the exercise; do not overwrite unrelated edits.

**Data-budget experiment:** leave model code unchanged. Train with `--games 4` into Run A's fresh folder, then `--games 20` into Run B's fresh folder. Note a limitation of the current trainer: it also changes the number of validation matches from three to five. Do not attribute changes in reported classification accuracy solely to training data. Use the same UI gameplay evaluation for the fair A/B comparison. The proposed Studio will hold validation groups fixed.

Upload Run B as a separate version. Keep `examples/learned_bot.py`, feature extraction and action helpers unchanged. If code and model both change, that is a different experiment.

## 5. Explain what happened

Complete [the experiment record](EXPERIMENT_TEMPLATE.md). Include a failure or a disagreement, not just a win. State whether the evidence supports the hypothesis, contradicts it, or is inconclusive.

Questions to discuss:

- Did classification scores and gameplay outcomes tell the same story?
- Could the result be due to draws, a small sample, the opponent or changed helpers?
- What would happen if the model always chose the most common mode?
- Did we teach a new strategy, or learn to reproduce an existing one?

The current script does not automatically produce a majority-mode baseline or ablation benchmark. Those are instructor-led questions today and explicit requirements for the future Studio.

## Instructor readiness checklist

- Dry-run these commands and uploads on the actual workshop computers; measure collection, training and evaluation separately.
- Freeze one rules version and starter commit for all teams. Keep a prepared A/B artifact and reports as an offline fallback, labeled as pre-trained rather than live student results.
- Avoid a shared public upload server: bot uploads execute trusted Python locally, not sandboxed competition code.
- Test at least one Windows/Linux setup if students use it; current README only claims macOS verification.
- Prepare a short explanation of a tree branch, a class imbalance and an inconclusive result.
- If the class cannot reach one complete experiment within the selected time, reduce the activity rather than promising a stronger agent or faster hardware.

Suggested assessment: experimental reasoning 35%, fair evaluation/reproducibility 30%, explanation of the learned component 25%, working submission 10%. Keep competitive ranking separate from learning credit. Disclose AI assistance; participants must still explain their model and evidence.

# Workshop: your strategy, your experiment

For participants with basic Python and little or no ML. Work individually or in pairs. The core activity is designing your own bot and making evidence-based changes. Installation is a pre-workshop task; follow [the README](../README.md#run-it).

## What you will leave with

A runnable strategy with explicit parameters, two saved versions, comparable results against different opponents, a failure replay and an [experiment record](EXPERIMENT_TEMPLATE.md). You should be able to explain overfitting, held-out evaluation and what would need to change for a procedure to learn your parameters automatically.

## A three-hour session

| Minutes | Activity | Output |
| --- | --- | --- |
| 0–15 | Welcome, project goals and a reference match | Describe the game and the learning objective |
| 15–40 | Read the observation contract; inspect the parameter starter | Explain one decision and the parameters |
| 40–65 | Write a hypothesis, upload A and run development matches | Baseline reports against different styles |
| 65–85 | Inspect metrics and a failure replay | A reasoned explanation, not just a score |
| 85–95 | Break | — |
| 95–125 | Change one parameter or rule; upload B | A named version and recorded difference |
| 125–150 | Repeat the same development configurations | A/B comparison in the notebook |
| 150–170 | Freeze the choice; instructor runs a held-out check | A generalization result, including limitations |
| 170–180 | Share findings and discuss automated learning | What stayed fixed, what changed, what is next |

For **two hours**, provide preinstalled software and the starter, shorten the introduction and do one parameter-only comparison against two opponents. For **four hours**, add an algorithm-change experiment or the [optional imitation-learning demonstration](IMITATION_LEARNING.md). Do not promise both a full beginner workshop and an RL project in the same short session.

## Your route through the app

1. **Welcome:** read the pitch and download the parameter starter.
2. **Bot Library / upload:** give your version a clear name; only upload trusted code.
3. **Arena:** watch decisions in real time; pause or step when useful.
4. **Experiment Lab:** run reproducible batches with a candidate and specified opponents.
5. **Replays and reports:** inspect failures and compare per-opponent results in your notes.
6. **Final check:** use a reserved seed/opponent set after freezing, coordinated by your instructor.

Follow [the six-step workflow](WORKFLOW.md) for the full procedure and [the parameter guide](PARAMETERS.md) for your first change. Separate two-player batches are the simplest way to understand individual matchups; three-/four-player games are an optional capstone.

## Instructor checklist

- Dry-run the starter upload, a short batch and replay inspection on intended laptops. Measure runtime before choosing the match budget.
- Freeze rules and opponent versions during comparisons. Prepare development settings and a separate final set; the app does not enforce that boundary automatically.
- Prepare baseline reports as an explicitly labeled fallback, not as live student results. Keep installation outside teaching time.
- Explain that metrics/replays do not update a model. The shipped starter uses manual preferences; automated parameter learning is [proposed](LEARNING_LEAGUE.md), not implemented.
- Keep public hosted uploads out of this workshop: the local process runner is not a malicious-code sandbox.
- Ask participants to disclose AI assistance and explain their own strategy and experiment. Use [the context guide](PROJECT_CONTEXT.md) to keep assistants focused.

Suggested assessment: hypothesis and failure reasoning 35%, fair comparisons/reproducibility 30%, algorithm/parameter explanation 25%, working submission 10%. Keep tournament rank separate from learning credit. A well-explained failed prediction can earn full reasoning credit.

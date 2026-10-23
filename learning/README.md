# Welcome to Bot Arena

Build your own Python bot. Give its strategy a few meaningful parameters. Run matches, inspect the evidence, and improve one thing at a time.

This workshop is for basic Python skills and little or no ML, in a 2–4 hour session. The objective is not just a winning bot: it is an algorithm you can explain and an experiment you can defend.

## Choose your starting point

- [Participant onboarding](ONBOARDING.md) — setup, five orientation tasks and a first strategy experiment.
- [Why this project?](../docs/TEAM_PITCH.md) — a shared brief for participants, mentors and the team.
- [Your six-step workflow](WORKFLOW.md) — from prediction to a held-out final check.
- [Your first parameterized bot](PARAMETERS.md) — download, understand and change the starter.
- [Workshop agenda](WORKSHOP.md) — a practical path through a 2–4 hour session.
- [Experiment notebook](EXPERIMENT_TEMPLATE.md) — preserve settings, results and failure analysis.
- [Algorithms, tuning and learning](ML_CONCEPTS.md) — what the ML concepts mean here.
- [Learn a Hit & Run parameter](PARAMETER_LEARNING.md) — an actual match-outcome bandit exercise.
- [Project context for coding assistants](PROJECT_CONTEXT.md) — help an assistant support your reasoning.
- [Resources](RESOURCES.md) — reading with specific questions to answer.

The app opens on **Welcome**, with the project brief and these Markdown guides readable inside the page. Download a guide when you want a copy. **Experiment Lab** (formerly Training Lab) evaluates frozen bot versions; it does not train them automatically.

## Available and proposed

| Available now | Proposed, not implemented |
| --- | --- |
| Your own rules and manually chosen strategy parameters; a CLI bandit prototype for Hit & Run's scouting limit | Automated parameter learning for arbitrary student bots |
| Parameter starter, upload and 2–4 player matches | In-app and resumable learning for arbitrary bots |
| Batch evaluation, reports and replays | A/B comparison dashboard and enforced held-out final tests |
| Optional CLI imitation learning and parameter learning | A 100-match adaptation league |

Manual tuning teaches experimentation, overfitting and generalization, but is not automatically machine learning. The [Hit & Run bandit guide](PARAMETER_LEARNING.md) shows a small learner updating estimates from battle outcomes. The [imitation example](IMITATION_LEARNING.md) is a different route that fits a decision tree to teacher labels. The broader [learning-league proposal](LEARNING_LEAGUE.md) describes what would be needed to generalize this to a 100-match program.

Start with your own strategy and the core workflow. You do not need to copy a teacher bot to participate.

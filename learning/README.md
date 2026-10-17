# Welcome to Bot Arena

Build your own Python bot. Give its strategy a few meaningful parameters. Run matches, inspect the evidence, and improve one thing at a time.

This workshop is for basic Python skills and little or no ML, in a 2–4 hour session. The objective is not just a winning bot: it is an algorithm you can explain and an experiment you can defend.

## Choose your starting point

- [Why this project?](../docs/TEAM_PITCH.md) — a shared brief for participants, mentors and the team.
- [Your six-step workflow](WORKFLOW.md) — from prediction to a held-out final check.
- [Your first parameterized bot](PARAMETERS.md) — download, understand and change the starter.
- [Workshop agenda](WORKSHOP.md) — a practical path through a 2–4 hour session.
- [Experiment notebook](EXPERIMENT_TEMPLATE.md) — preserve settings, results and failure analysis.
- [Algorithms, tuning and learning](ML_CONCEPTS.md) — what the ML concepts mean here.
- [Project context for coding assistants](PROJECT_CONTEXT.md) — help an assistant support your reasoning.
- [Resources](RESOURCES.md) — reading with specific questions to answer.

The app opens on **Welcome**, with the project brief and these Markdown guides readable inside the page. Download a guide when you want a copy. **Experiment Lab** (formerly Training Lab) evaluates frozen bot versions; it does not train them automatically.

## Available and proposed

| Available now | Proposed, not implemented |
| --- | --- |
| Your own rules and manually chosen strategy parameters | Automated parameter learning for your own bot |
| Parameter starter, upload and 2–4 player matches | Persistent learning state and feedback across rounds |
| Batch evaluation, reports and replays | A/B comparison dashboard and enforced held-out final tests |
| An optional CLI imitation-learning example | A 100-match adaptation league |

Manual tuning teaches experimentation, overfitting and generalization, but is not automatically machine learning. The [learning-league proposal](LEARNING_LEAGUE.md) explains how a learning procedure could choose parameters from battle feedback. The existing [imitation example](IMITATION_LEARNING.md) is an optional, different route to fitting a model.

Start with your own strategy and the core workflow. You do not need to copy a teacher bot to participate.

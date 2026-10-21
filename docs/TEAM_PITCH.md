# Bot Arena: your strategy, tested by evidence

A shared introduction for participants, mentors and the project team.

## The idea

Build a Python bot that makes decisions in a small retro arena. Give it a strategy you can explain, expose a few meaningful parameters, and test your ideas against different opponents.

The game is the setting; the real challenge is learning how to improve a decision-making system. Why did a change work? Does it still work against another rival? What evidence would make you change your mind?

You do not need to start with a neural network. Basic Python, curiosity and a willingness to inspect a failed prediction are enough for the first workshop.

## What you will learn

- Turn an idea into an algorithm and identify its adjustable parameters.
- Make a prediction before looking at results.
- Read per-opponent outcomes, damage, survival and replays.
- Change one thing and compare versions fairly.
- Recognize overfitting to a particular rival or map set.
- Check generalization using held-out conditions.
- Explain the difference between manual tuning and a model learning from data.

A strong outcome is a bot and an experiment you understand—not just code that won one match.

## Your process

1. Write down your strategy and predict how it will perform.
2. Run it against several opponents on development seeds.
3. Inspect per-opponent outcomes, damage, survival and replays.
4. Change one rule, parameter or learned component at a time.
5. Compare versions on the same development matches.
6. Freeze the final version and test held-out seeds, ideally with a rival you have not tuned against.

Use [the full workflow](../learning/WORKFLOW.md) and [experiment notebook](../learning/EXPERIMENT_TEMPLATE.md) to keep the reasoning and results together.

## Where machine learning fits

Writing rules and adjusting numbers manually is experimental algorithm development. It teaches important ML evaluation ideas, but it is not automatically machine learning.

A learning procedure can choose parameters from battle feedback while your strategy code stays fixed. The [Hit & Run bandit exercise](../learning/PARAMETER_LEARNING.md) is a small working example: it learns which scouting limit to use from match outcomes. It is not a general trainer for arbitrary bots, and improvement within a small match budget is not guaranteed. The [100-match learning-league proposal](../learning/LEARNING_LEAGUE.md) describes the broader extension.

There is also an existing, optional [imitation-learning example](../learning/IMITATION_LEARNING.md) that fits a decision tree to a reference bot's tactical labels. It is genuine fitting, but it copies a small teacher policy and keeps movement helpers handwritten. It is a different learning track, not a requirement to abandon your own strategy.

## What you can do today

Welcome introduces the project and opens the repository guides. Download a parameter starter, write or extend its rules, upload a version and watch it in the Arena. Experiment Lab evaluates frozen bots and saves reports/replays so you can compare them in your notes.

Organizers can switch Experiment Lab to [Round robin](COMPETITIONS.md), select a roster and run every pair with balanced starts. Standings, matchup scores, pause/resume, completed-match recovery and a separate identity-redacted replay pack support weekly feedback sessions. Share the same release ZIP with everyone while keeping administrator reports private. For the final session, select **Knockout**: a real single-elimination bracket with byes, seeded/shuffled placement and winners advancing through semifinals to the final. Tied series play two extra balanced blocks before requiring a recorded organizer ruling; publish that policy beforehand. Adaptive cross-match learning is not implemented.

For an in-person showcase, Audience view works in both formats and lets the host reveal each series result at their own pace. The knockout bracket hides later-round identities until their feeder results are revealed. The grand final gets a larger gold trophy reveal and a brief confetti animation, with reduced-motion support. All results come from completed matches; the presentation does not change scoring or invent winners.

The prototype supports 2–4 players, two game modes and local human play. For the first lesson, use two-player elimination batches against different styles; multiplayer games can be a capstone.

The CLI bandit updates its estimates between matches and writes a frozen bot. Experiment Lab match statistics still do not automatically update a model. General training for arbitrary uploaded bots, automatic paired comparisons and enforced hidden final tests remain proposed.

## A workshop that fits an afternoon

The core workshop is 2–4 hours for people with basic Python and little or no ML. Install beforehand. Leave with a parameterized strategy, two saved versions, a fair comparison, a failure example and a conclusion. See [the agenda](../learning/WORKSHOP.md).

We value clear reasoning, reproducibility and honest limitations alongside a working submission. “The change did not help” can be a good finding. Competition rank and learning credit should be separate.

## For mentors and the team

Keep the first release focused on this complete experiment loop. Freeze rules and reference versions during the workshop, prepare a separate final test, and rehearse on the actual laptops before committing to match budgets.

The next tools should make experiments easier to record and compare, then generalize the bounded parameter-learning prototype to student-owned bots. Start with a few strategy settings rather than promise full neural game mastery. The [roadmap](LEARNING_STUDIO_SPEC.md) separates current features from future work.

For an adaptation competition, agree on equal match/compute budgets, allowed feedback, persistent state and update timing before advertising it. Keep frozen-policy tournaments and learning leagues distinct.

This is a local trusted-code prototype. Shared public uploads, adversarial code isolation, cloud classrooms and production ranking are separate security/operations projects.

## Start here

Read [the participant guide](../learning/README.md), try [the parameter starter](../learning/PARAMETERS.md), and use [the project context](../learning/PROJECT_CONTEXT.md) with a coding assistant. The [repository README](../README.md) covers setup, capabilities and technical details.

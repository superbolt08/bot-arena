# Learning tools roadmap

This is a proposal for follow-on work, not a list of shipped features. The main experience is now the student-owned strategy workflow described in [the shared brief](TEAM_PITCH.md).

## Available foundation

Welcome introduces the objectives, six-step process and parameter starter. Repository Markdown guides are readable in the app. Arena shows real-time matches and replays; Experiment Lab (formerly Training Lab) evaluates frozen bot versions. The learner can keep version comparisons in the experiment notebook.

A CLI imitation-learning example fits a tree to teacher labels. A narrow CLI bandit learns Hit & Run's scouting limit from match rewards and exports a frozen bot. Neither trainer supports arbitrary student strategies, and the current batch evaluator does not update models.

## Phase 1: make experiments easier to compare

Add a persisted hypothesis/change record linked to each run, immutable bot/opponent versions and a matched A/B view. Show per-opponent outcomes, draws, damage, survival, failures and replay links. Preserve rule versions, mode, clock, maps, seats and rotations so differences are interpretable.

Add development/final-test separation with instructor-controlled final settings. Do not imply current seed entry enforces this. Final feedback must be withheld until code/parameter selection is finished. Keep stored artifacts and legacy replay viewing intact.

Acceptance: a beginner completes one controlled comparison and can reproduce its configuration without manually reconstructing missing opponent versions.

## Phase 2: learn the student's parameters

Keep strategy code fixed, declare a parameter schema and allow a small set of valid configurations. A bounded trainer selects configurations using match feedback and saves the initial and final policies plus its learning log. Start with fixed opponents and independent round resets. The Hit & Run scouting-limit bandit is an initial CLI prototype; it does not yet train arbitrary student bots or run from the app.

Add explicit lifecycle hooks: load learner state, choose a match configuration, receive a bounded round-end result, update between rounds, and export a frozen policy. The action deadline is not the training-update budget. Keep worker processes, output paths, logs and artifact versions isolated; do not rely on arbitrary file writes from a bot to implement persistence.

Show which settings were selected, exploration versus exploitation, per-opponent performance and frozen held-out evaluation. Training reward and gameplay scoring must be labeled separately. Compare against the starting policy, a fixed baseline and an equal-budget random-search baseline before making claims about a learning algorithm.

Acceptance: exported policies reproduce their decisions, budgets are enforced, state survives permitted restarts, and no final-test feedback reaches learning.

## Phase 3: a 100-match learning league

Follow [the league proposal](../learning/LEARNING_LEAGUE.md). Decide whether 100 means training-only matches or a total budget including evaluation. State the allowed observations/feedback, opponent sampling, update timing, persistent state, random seeds, restarts and compute limits.

Begin with adapting one entrant against frozen reference opponents. Simultaneously adapting entrants change the problem; evaluate that format separately. A frozen-policy tournament after training and a live adaptation league need different rules.

Acceptance: a documented fair protocol, a small-laptop rehearsal, equal budgets, isolated state and an initial-versus-final held-out comparison that can show no improvement honestly.

## Optional independent track: imitation learning

If adding an in-app tree trainer later, reuse pure collection/fitting functions shared with the CLI, save grouped datasets and immutable configurations, and evaluate the exported JSON interpreter. The current CLI discards raw rows, hardcodes several settings and temporarily adds a learned bot to the global registry; do not wrap it naively in concurrent API jobs.

Useful inspection includes per-mode class support, confusion matrices, readable branches and learning curves from multiple actual fits. Never animate fake epochs for a one-call tree fit. This remains an optional model-training lesson, not the default strategy workflow.

## Scope boundaries

Do not change game balance to make a learning curve look better. Do not use hidden replay state as live bot input. Do not overwrite participant artifacts. Uploaded Python is trusted local code, not a hostile-code sandbox.

Neural pixel policies, large-scale self-play, arbitrary trainer uploads, GPU infrastructure and public hosted competitions require separate scope and security decisions.

# Could a bot learn over 100 matches?

Yes, a small parameterized policy could adapt between rounds within a 100-match budget. This is a proposed learning track, not a shipped feature or a guarantee of improvement. One hundred matches means one hundred completed rounds, not one hundred simulation ticks.

## A manageable first version

Keep a student's strategy code fixed and define a small set of parameter configurations—for example, cautious, balanced and aggressive variants. A learner chooses one configuration for a match, observes a reward, updates its estimates and chooses again next round.

This can be formulated as a match-level multi-armed bandit: each arm is a complete strategy configuration, and a fresh match supplies feedback. It teaches exploration versus exploitation without requiring the student to learn every primitive game action. See [TensorFlow's bandit introduction](https://www.tensorflow.org/agents/tutorials/bandits_tutorial) for the concept; this proposal does not require TensorFlow as a dependency.

Start against frozen opponents drawn from a fixed mix, with independent match resets. An opponent that is also adapting makes the learning problem non-stationary; that is a later competition variant, not evidence that a simple fixed-opponent experiment transfers automatically.

## What the learner would need

- A declared parameter schema and a few valid configurations; freeze code while learning.
- A round-end feedback hook and persistent learner state across rounds. Current `Bot` instances reset each match; the app has no supported learning-state lifecycle yet.
- A bounded update phase between rounds, separate from the 100 ms action deadline.
- A common match/compute budget, fixed training-opponent mix and explicit random seeds.
- A documented reward, such as win = 1, draw = 0.5, loss = 0. This is a proposed training signal, not a change to official game scoring. Inspect draws and performance per opponent separately.
- A saved initial configuration, learning log, final frozen artifact and matched evaluation. Do not confuse rising training reward with proven generalization.

## An illustrative 100-match total budget

Use **60 adaptive training matches**, then **20 matches for the frozen starting configuration** and **20 matched matches for the frozen final configuration** on the same held-out conditions. Keep evaluation feedback hidden until training and selection finish; neither bot updates during the final 40 matches. If the team instead offers 100 training matches, budget a separate evaluation set and say so explicitly.

Twenty evaluation matches per checkpoint provide a classroom comparison, not strong proof. Report each opponent and the uncertainty; repeat with more seeds/budgets before making a competition-strength claim. A small configuration space is an intentionally constrained teaching task, not a claim of neural game mastery.

## Learning during a competition

Two formats should be separate: a frozen-policy tournament after training, and an adaptation league where all entrants may update under the same rules. For the latter, specify what feedback is allowed, whether opponent identities are public, what state persists, restart policy, compute limits and how updates are isolated. Never give bots hidden-state replays as live observations.

This needs runner/API work and fair evaluation before it is advertised as available. It is a promising next step after [the core workflow](WORKFLOW.md), not something the current batch evaluator does automatically.

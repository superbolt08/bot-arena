# Reading with a purpose

Start with [our concepts](ML_CONCEPTS.md); external documentation is optional reference, not prerequisite reading for the whole workshop. Reading times below are suggested time boxes, not guarantees. Links checked while preparing the pack on 2026-10-15; external documentation can evolve independently of this repository's dependencies.

## Start with your own experiment

Read [the workflow](WORKFLOW.md), [parameter guide](PARAMETERS.md) and [experiment notebook](EXPERIMENT_TEMPLATE.md) first. Overfitting and fair evaluation matter for a manually tuned strategy too. The tree material below supports the optional supervised-learning track, not a requirement to copy a reference bot.

## Workshop references

1. [scikit-learn: decision trees](https://scikit-learn.org/stable/modules/tree.html) — skim the introduction, strengths/limitations and classification example (10 minutes). Answer: what does maximum depth control, and how can a fitted tree still be ML if its predictions use branches?
2. [scikit-learn: common pitfalls and leakage](https://scikit-learn.org/stable/common_pitfalls.html) — read the data-leakage section (10 minutes). Answer: why should we not train and evaluate on related ticks from the same match?
3. [scikit-learn: cross-validation and grouped data](https://scikit-learn.org/stable/modules/cross_validation.html) — find grouped-data splitting (optional, 10 minutes). Map a group to a game/map seed rather than treating every tick as independent.
4. [scikit-learn: validation and learning curves](https://scikit-learn.org/stable/modules/learning_curve.html) — inspect the diagrams (optional, 10 minutes). Distinguish changing training-set size from changing model capacity. The current tree is fitted in one call, so an epoch-progress animation would not describe this trainer honestly.
5. [scikit-learn: DummyClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html) — read `most_frequent` (5 minutes). Answer: what baseline should a mode classifier be compared against before celebrating accuracy? This baseline is a proposed tooling addition, not part of today's training report.

## After the workshop

- [TF-Agents: multi-armed bandit introduction](https://www.tensorflow.org/agents/tutorials/bandits_tutorial) — focus on exploration versus exploitation. In the proposed match-level learner, a parameter configuration is an arm and a fresh game supplies feedback. This is a concept reference; the project does not require TensorFlow or ship this trainer. Read [the 100-match proposal](LEARNING_LEAGUE.md) for scope and safeguards.

- [Gymnasium: agent-training tutorials](https://gymnasium.farama.org/v1.1.1/tutorials/) — find the tabular Q-learning examples. Use them to learn observations, actions, rewards and exploration before attempting full arena RL. These are separate environments, not drop-in Bot Arena trainers.
- [PettingZoo: Parallel API](https://pettingzoo.farama.org/api/parallel/) — compare `reset`, joint `step` and per-agent outputs with `arena/parallel_env.py`. An API adapter is infrastructure; it does not train a policy by itself.
- [Accelerating Training in Pommerman with Imitation and Reinforcement Learning](https://arxiv.org/abs/1911.04947) — research extension, not required beginner reading. Discuss why demonstration learning and learning from rewards are distinct stages. Do not imply that this prototype reproduces the paper's results.

## Repository reading order

Read [the rules](../docs/RULES.md) and [bot API](../docs/BOT_API.md), then `features`, `teacher_mode` and `act_for_mode` in `arena/bots.py`. Trace one record through `arena/train.py`, and finally inspect `examples/learned_bot.py` to see how the frozen artifact plays.

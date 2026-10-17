# Algorithms, tuning and learning

## Three different activities

**Algorithm design:** you write how the bot makes decisions. For example, escape known hazards, then compare an attack preference with a supply preference.

**Manual parameter tuning:** you choose settings such as a retreat threshold, run battles and adjust them from evidence. This is experimental algorithm development. It can teach ML evaluation concepts without itself fitting a model.

**Learning from data:** a procedure changes a decision model or policy parameters from examples or rewards. The student still designs the representation, algorithm and evaluation. The learned component does not replace critical thinking.

The [parameter starter](PARAMETERS.md) supports the first two activities today. A trainer that learns its settings from matches is [proposed](LEARNING_LEAGUE.md), not implemented. The optional decision-tree [imitation example](IMITATION_LEARNING.md) already fits a different model from teacher labels.

## The ideas you should take away

| Idea | In Bot Arena |
| --- | --- |
| Policy / strategy | The mapping from the bot's observation and memory to an action |
| Parameter | A setting within that strategy, such as a health threshold |
| Feature | Information used for a decision, derived only from allowed observations |
| Hypothesis | A prediction about a change before looking at its results |
| Development set | Matches used repeatedly while choosing rules or settings |
| Held-out test | New conditions inspected after the final strategy is frozen |
| Overfitting | Improvements tailored to development opponents/maps that fail to transfer |
| Generalization | How well the chosen strategy performs under new conditions |
| Ablation | Remove or replace one component to investigate whether it mattered |
| Reward | Feedback used by a learning procedure; not necessarily official tournament scoring |
| Hyperparameter | A setting of the learning method, rather than a fitted policy value |

A strategy parameter can be chosen manually or learned. A decision tree may look like if/else rules and still be learned: its branches were fitted from data. The distinction is where the decision settings came from, not whether the final code contains branches.

## Generalization is more than new seeds

A new seed changes the map, but the same rival may still have an exploitable habit. Test more than one style and, ideally, a fresh opponent version. A bot that wins against Deadeye but loses everywhere else may have specialized rather than become broadly stronger.

Inspect each matchup rather than only the aggregate win rate. Also inspect draws, damage, survival and errors. A highly defensive change might improve survival while making wins less frequent. There is no single metric that explains every strategy.

## Keep comparisons fair

For A/B comparisons, preserve seeds, seat/spawn rotations, mode, tick limit, rules and opponent versions. Change one variable and keep earlier artifacts. Repeatedly selecting versions from a supposed final test turns it into development data.

Do not use hidden replay information as online bot input. If collecting supervised data, split related examples by whole matches/map groups rather than randomly separating neighboring ticks. See the [official leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).

## What genuine automated learning could look like

A small learner could choose among a few parameter configurations between matches, observe results and update its estimates. This is a constrained match-level policy-selection problem, not learning every move from scratch. It can introduce exploration versus exploitation; [the league proposal](LEARNING_LEAGUE.md) explains the limits and missing infrastructure.

The existing imitation trainer instead fits four tactical labels: escape, attack, supply and explore. Its pathfinding and action execution remain handwritten. High teacher agreement measures imitation, not a guarantee of a stronger bot. See [the optional track](IMITATION_LEARNING.md) and [the official tree introduction](https://scikit-learn.org/stable/modules/tree.html).

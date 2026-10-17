# Your first parameterized bot

Start with [examples/parameter_bot.py](../examples/parameter_bot.py), or download “Get the starter bot” from Welcome. Keep a copy for each version. You need basic Python, not a neural-network framework.

## What the starter does

It checks known hazards, then chooses whether to seek supplies, attack a visible opponent or explore. Shared helpers in `arena/bots.py` handle paths and individual actions. The example is intentionally small and is not claimed to beat the reference bots. It does not add a bomb-placement policy; you can design one as an algorithm extension.

```python
PARAMETERS = {
    "retreat_health": 1,
    "aggression": 0.7,
    "pickup_priority": 0.4,
}
```

| Parameter | Meaning | Suggested range |
| --- | --- | --- |
| `retreat_health` | Seek visible health when HP is at or below this threshold | Integer 0–3 |
| `aggression` | Weight for attacking when an opponent is visible; clear shots receive a higher score | 0–1 |
| `pickup_priority` | Weight for useful visible supplies, with more urgency when health is below full | 0–1 |

These are preference weights, not probabilities. For example, `aggression = 0.7` does not mean “attack 70% of the time.” Scores are compared deterministically; an attack wins an exact tie. Health seeking at the retreat threshold overrides the preference scores, and known-danger escape overrides both.

A parameter need not affect every state. If there is no health pickup, changing `retreat_health` may do nothing. Look for states where your proposed change could actually alter the decision.

## First exercise

1. Keep the defaults and upload the file as `My bot · A`.
2. Write: “Changing the retreat threshold to 2 should…” and finish the prediction yourself.
3. Use separate Experiment Lab batches against at least two opponent styles. A small 12-match batch per opponent is a starting classroom observation, not strong evidence of superiority.
4. Change only `retreat_health` to `2`, upload as `My bot · B`, and repeat the exact configurations.
5. Compare outcomes and inspect a failure. Was a useful pickup visible? Did pathfinding, rather than the threshold, explain the result?

If you want to modify an algorithm rather than a number, identify the behavior the current strategy cannot express, change it in a new version and document that experiment separately.

## Parameters are not automatically machine learning

These defaults are handwritten. Editing them yourself is manual tuning. An automated learner would need to choose settings from data, retain its learning state and be evaluated on held-out matches. That trainer is not included today; see [the learning-league proposal](LEARNING_LEAGUE.md).

Do not tune game-rule constants such as HP, blast geometry or damage. Do not use omniscient replays as live bot input. Uploads execute trusted local code; read [the bot API](../docs/BOT_API.md) before sharing a bot.

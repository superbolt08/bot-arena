# Observation contract

The public `arena.sdk.Bot` class is optional. Any uploaded file exposing a no-argument `Bot` class and `choose_action(observation)` works. Return a string or an `arena.sdk.Action` enum.

| Field | Meaning |
| --- | --- |
| `tick`, `max_ticks`, `mode`, `seed` | Simulation clock and reproducibility settings |
| `self` | Your ID, position, HP, weapon, cooldown, shield, protection and counters |
| `board` | 15 rows of remembered terrain: `#` solid, `+` crate, `.` floor |
| `visible` | 15×15 booleans for currently observable tiles |
| `last_seen` | Tick of latest terrain observation; −1 means only starting-map knowledge |
| `opponents` | Currently visible living opponents only |
| `bombs` | Visible `x`, `y`, `owner`, `explode_at` |
| `projectiles` | Visible `x`, `y`, `dx`, `dy`, `owner` |
| `flames` | Visible explosion tiles from the latest resolved tick |
| `pickups` | Visible `x`, `y`, `kind` (`health`, `shield`, `battery`) |
| `supply_drop` | Public next-drop location, kind and arrival tick, or null |
| `actions` | Protocol action strings; presence does not imply a currently legal or safe move |

Bot-visible positions are integer tiles, x increasing east, y increasing south. Player IDs are zero-based and stable during a round. Memory resets for each round. Remaining fuse is `explode_at - tick`. Do not infer that an unseen entity ceased to exist just because it disappeared from a list.

Action strings: `wait`, `switch`, `move_n`, `move_s`, `move_w`, `move_e`, `fire_n`, `fire_s`, `fire_w`, `fire_e`. Bomb placement uses any fire action while the bomb weapon is equipped. Every action, including weapon switching, uses one tick. No attacks can accompany a movement in the same tick.

## Model artifacts

The upload UI accepts one optional JSON file, saved next to the bot as `model.json`. Use `Path(__file__).with_name("model.json")` to open it. Code files are limited to 256 KB and model files to 5 MB. More complex dependency bundles and binary models are deferred.

The included learned bot interprets a plain JSON decision tree without importing scikit-learn in the worker. Training imports scikit-learn in the parent development environment. The tactics selected are `escape`, `attack`, `supply`, and `explore`; low-level execution uses the same pathfinding helper as the teacher. This shared helper is intentional so students can focus on the learned component.

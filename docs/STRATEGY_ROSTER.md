# Compare weapon strategies in Round Robin

These four handwritten bots share the same threat memory and escape planner. Their weapon choices, fighting distances and objectives differ. They do not learn during a match.

| Bot | Weapons | Strategy |
| --- | --- | --- |
| Crossfire | Bomb + blaster | Plant to pressure a visible opponent at medium range, escape, then keep the blaster equipped and seek follow-up shots during the fuse. Take immediate close or finishing shots first. |
| Breach & Shoot | Bomb + blaster | Use bombs to clear crates when no enemy is visible. On enemy contact, switch to the blaster. Escape urgent hazards before switching. |
| Range Keeper | Blaster only | Shoot from lanes four to seven tiles away; back off between shots when an opponent gets close. |
| Siege | Bomb only | Clear crates, threaten enemy lanes, escape and seek useful supplies. Never fire the blaster. |

Bomb First already supports blaster shots after escaping, but gives new bomb opportunities priority. Crossfire deliberately reserves the active-bomb/follow-up window for blaster combat and repositioning. Neither can shoot and move on the same tick, or shoot an enemy without a clear lane. Breach & Shoot's “no enemy” means none currently visible; it cannot detect hidden opponents.

## Get the upload files

From the repository with the Python environment activated:

```bash
python -m examples.strategy_roster
```

The command writes four upload-ready `.py` files and a descriptive manifest under `data/strategy_roster/`. Each bot file includes a frozen copy of its common helpers, plus imports from the arena SDK/reference helpers. Upload each Python file individually using the names in the table. No JSON model or extra file is required. The manifest describes the roster; it is not a learned model artifact. Edited output files are preserved; use `--output data/strategy_roster_v2` to generate another version.

The editable policy source is [examples/strategy_roster.py](../examples/strategy_roster.py). Original submissions stay separate from future generated versions.

## Run the comparison

1. Open **Experiment Lab → Round robin** and select the four bots. For stronger reference opponents, also include **Bomb First** and **hitnrun3 Memory Fix**.
2. Choose elimination, a development seed start and a multiple of eight games per pair. Six entries with eight games per pair produce **120 matches**; sixteen games per pair produce **240**.
3. Every block of eight covers both seats and all four rotations on one map. Start with eight to inspect behavior, then use more seeds to assess consistency.
4. Inspect per-opponent wins/draws/losses, damage, survival, self-bomb deaths, errors and replays. Verify that Crossfire actually follows bombs with blaster attacks and that Breach & Shoot switches on enemy contact.
5. Freeze versions before comparing on new seeds and additional opponent styles. These bots provide strategy diversity; their shared planner and a small map set still limit any claim about overall weapon balance.

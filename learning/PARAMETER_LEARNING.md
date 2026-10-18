# Learn a Hit & Run parameter from matches

This is the project's first automated parameter-learning exercise. It uses a small **epsilon-greedy multi-armed bandit** to choose Hit & Run's `MAX_SCOUT_MOVES` value from match feedback. It learns between complete matches; the bot's movement, combat and bomb-safety rules stay fixed.

## Run it

From the project directory, with the Python environment active:

```bash
python -m arena.train_hit_and_run --games 60 --seed 30000
```

The learner tries scouting limits **8, 10 and 12**. It begins by trying every limit against Deadeye, Sentinel and Fuse, then uses its estimates to choose more often among better-performing settings. It still explores randomly 20% of the time. Each training match uses one of those frozen opponents, and the opponent mix is balanced across the run.

The reward is **win = 1, draw = 0.5, loss = 0**. After each match, the learner updates its average reward estimate for that scouting limit and opponent. It chooses the final setting by averaging performance equally across the three opponents. Damage, survival, self-bomb deaths and errors are logged as diagnostics, but are not part of the reward.

## What gets saved

The command creates new, timestamped files under `data/models/` and refuses to overwrite existing outputs:

- A JSON model with the selected scouting limit and estimates for each limit/opponent pair.
- A JSON report with the match-by-match learning record and held-out results.
- An uploadable Python bot with the selected limit frozen into the original strategy.
- A temporary progress record updated after each training match; it is removed when the run completes.

After training, it compares the frozen original setting (12) and the learned setting on the same **12 held-out matches per opponent**, using a separate seed range. These are a classroom demonstration, not strong statistical proof. Once you inspect held-out results and use them to make another change, those seeds are no longer held out.

Upload the generated `*_bot.py` file through **Upload bot** to play the result. The trained JSON is a record of the learner's estimates; the uploaded bot runs the selected fixed strategy. Experiment Lab still evaluates uploaded bots and does not update them.

## What this teaches—and what it doesn't

This is a genuine learning procedure: match outcomes update estimates, and those estimates guide later parameter choices. The allowed parameter values are a small, fixed set; the learner does not invent new values or rewrite strategy code. It is not the optional imitation tree, and it is not full reinforcement learning over every move.

The opponent mix matters. Training only against one rival could select a setting that overfits that matchup. The trainer therefore samples all three reference styles and reports them separately. Improvement is not guaranteed; learning that the baseline setting is still best is a valid outcome.

The trainer is a CLI prototype for this one Hit & Run parameter. It does not yet train arbitrary uploaded bots, resume an interrupted run, or run inside Experiment Lab. Keep the strategy version and opponent set fixed when comparing learner runs.

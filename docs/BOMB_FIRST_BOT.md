# Try a bomb-first strategy

Upload [examples/bomb_first_bot.py](../examples/bomb_first_bot.py) as **Bomb First**. It needs no model JSON. This is a handwritten strategy for exploring weapon tradeoffs under the existing rules.

The bot gives bombs priority when its current blast footprint reaches a visible opponent or a crate. It predicts the full-axis blast, checks chain timing, and requires a known escape route with two ticks of margin. Switching and planting take separate turns, so it checks again after switching. It then moves out of the blast and equips the blaster while its bomb is active. It also uses the blaster when a bomb placement has no known escape route. It remembers bombs that leave sight until their estimated flames expire.

The opening weapon is still the game's default blaster; the bot uses a normal switch action to equip bombs. A planned escape can be disrupted by simultaneous movement, hidden attacks, or changes the bot has not observed. It cannot guarantee survival or trap an opponent that dodges well.

## Compare it with a blaster primary

1. Upload Bomb First, then compare it against **Deadeye** or your own blaster-focused bot in Arena and Experiment Lab.
2. For a closer weapon comparison, make a copy of the file, change `USE_BOMBS = True` to `USE_BOMBS = False`, and upload it as **Blaster Control**. The control uses the same navigation, hazard prediction, supplies and shooting code, with bomb placement disabled. Their actual movements will differ once bombs change the arena.
3. Use two-player elimination and several map seeds. Round robin's blocks of eight games cover both seats and all four map rotations. Give both versions the same opponents and starting conditions.
4. Inspect wins, draws, damage dealt/taken, self-bomb deaths and replays. Look for successful bomb damage, useful crate clearing, opponents forced out of cover, lost turns switching, and cases where the bot could safely have used its blaster sooner.
5. Reserve new seeds and opponent styles for a later check. A win against one reference bot cannot establish weapon balance, especially when a better movement algorithm can explain the improvement.

`MAX_ESCAPE_MOVES` controls how far ahead the bot looks for a refuge when considering a plant. It is a strategy setting; fuse duration, flame duration and blast shape come from the shared SDK. Tuning a setting manually is an experiment, not a trained model.

# Prototype rules v0.1

## Tick resolution

The runner requests all living bots' actions from the same pre-tick state. Decisions are resolved together. Render speed does not change simulation time.

1. Advance the clock, decrement cooldowns/protection and attempt due respawns.
2. Validate actions. Resolve movement simultaneously.
3. Switch weapons or spawn attacks; collect pickups.
4. Advance projectiles one tile; compute hits.
5. Detonate due bombs and chain reactions against a shared pre-explosion terrain snapshot.
6. Destroy crates and roll seeded pickup drops.
7. Resolve shields and damage for all players, then eliminations and credit.
8. Announce/deliver supply drops and check the round outcome.

Movement cannot enter solid walls, crates or existing bombs. A player may leave a bomb they just placed. Contested destinations block all contenders. Direct swaps are blocked. A failed mover stays in place, blocking anyone behind them; no player ID gets movement priority.

## Combat

- Three starting HP. Blaster equipped initially; one switch action changes weapon.
- Blaster: 1 damage, projectile advances one tile each tick, five-tick cooldown. Stops at walls/crates; it does not destroy them or trigger bombs. Projectiles do not collide with one another. Owner is immune to their own projectile.
- Bomb: one active per owner, ten-tick fuse, 2 damage, cross radius three. Any fire direction places it. The blast includes its origin, stops at walls and at the first crate it destroys, and chains to bombs it reaches. Owner can be damaged. Blast damage occurs only on the explosion tick; flames are a one-tick visual event.
- Switching never resets blaster cooldown. Weapon firing removes respawn protection, including unsuccessful fire attempts.
- Damage is simultaneous: a dying player's already-fired attack still resolves.
- Shield consumes the strongest incoming hit that tick; remaining hits still apply. On equal-strength hits, lower owner ID is consumed first (fixed tie-break).
- Kill credit goes to the largest post-shield damage contributor on the fatal tick. Tied contributors use lower seat ID. A self-credited elimination counts as suicide, not a kill. There are no assists in v0.1.
- Damage dealt measures nominal post-shield attack damage; damage taken is capped by remaining HP.

## Items

- Health restores one HP, maximum three; full-health players leave it on the board.
- Shield absorbs one attack; cannot stack and remains on the board if already shielded.
- Battery immediately resets blaster cooldown; automatic on contact.
- Destroyed crates have a seeded 35% chance of revealing one item. Existing items in blast cells are destroyed; newly revealed ones survive that explosion.
- Every 75 ticks a supply arrives, announced 15 ticks beforehand. Location, item and countdown are public. It appears on a floor tile and may replace an existing pickup. Scheduled supplies encourage engagement but are not an additional scoring objective.

## Visibility and memory

The initial terrain layout is known. Visibility is a supercover line from the observer's tile to the target tile, in any direction with no range cap. Walls/crates block intermediate rays; the blocking tile itself is visible. Rays touching a blocked corner do not permit diagonal peeking.

Only visible enemies, bombs, projectiles, flames and pickups are included. Terrain memory updates only when seen; the last-observed tick is provided per tile. Students may keep previous enemy sightings in their bot's own memory. Public supply announcements are the exception to local dynamic-entity visibility. Hidden state is available in spectator/replay debugging only, not through `choose_action`.

The local app is not an adversarial competition security boundary: trusted code can access local files, and replay/debug endpoints expose match state. A hosted competition needs a separate trust boundary and should withhold replay access until rounds end.

## Modes

Elimination: last living player wins. If nobody survives a tick, draw. At tick 450, two or more survivors draw regardless of HP or damage; a sole survivor still wins.

Deathmatch: three-minute match. Respawn after 15 ticks on an available floor tile outside current bomb blast areas/projectile positions, favoring distance from living enemies. If no safe tile exists, postpone respawn. Respawn grants three HP, blaster, no shield, and ten ticks of protection. Existing bombs remain until detonation. Most kills minus suicides wins at tick 900; a tied top score is a draw.

Three-player rounds use three of four corner spawns. Evaluation rotates occupied corners and candidate seats; a single three-player map is not claimed to be position-neutral.

Evaluation placement ranks living players ahead of eliminated players, then uses survival ticks among eliminated players. Same-tick eliminations share placement. Deathmatch placement uses the mode's score.

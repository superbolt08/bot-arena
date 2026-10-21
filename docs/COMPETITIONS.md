# Run competitions in Experiment Lab

This is the local organizer tool for reviewed, trusted bot submissions. Choose **Round robin** for weekly all-pairs feedback or **Knockout** for a single-elimination final. Both run real matches, save progress/replays and produce identity-redacted release packs. It is not a hosted student portal or a learning-state service.

## Run the field

1. Upload reviewed Python entries and any JSON artifact required by their code. Include the JSON if the bot reads it; an embedded learned constant does not require a second file.
2. Open **Experiment Lab → Experiment format → Round robin**.
3. Select 2–16 distinct bot versions, name the run, choose games per pair, seed start and game mode. The screen calculates the total before launch; runs are limited to 2,000 matches.
4. Start the run. Every unordered pair plays two-player matches. Each block of eight games covers both seats at four map rotations; every pair uses the same map for that block. Additional blocks use new seeds. Pairings are interleaved rather than finishing one rival's whole series first.
5. Inspect standings, per-pair scores, diagnostics and the paginated match history. Open any replay in Arena. Switch back to Single candidate for the original benchmark workflow.

The game engine is unchanged. Round-robin points are **win = 3, draw = 1, loss = 0**, separate from any training reward. Points determine rank; equal totals share rank. A unique top score is the round-robin winner. A round-robin tie remains a tie—there is no arbitrary hidden tiebreak. Use the separate Knockout format for elimination progression.

Errors follow the normal bot runner: an errored/timed-out bot waits, rather than receiving an automatic forfeit. Matches with errors are flagged; review them before treating a leaderboard as official. Invalid actions and timeout counts are included in diagnostics.

## Run a knockout final

1. Select **Experiment Lab → Experiment format → Knockout** and choose 2–16 reviewed bot versions.
2. Choose bracket seeding: a reproducible shuffle using seed start, or selection order (first selected = seed 1). To seed from your weekly standings, select versions in the announced ranking order and turn shuffle off. This is a separate run, not automatic qualification from a round robin.
3. Choose base games per series, a multiple of eight. The budget shows the base match count and the maximum including tiebreaks. The bracket is padded to the next power of two, with byes assigned to the highest seeds. A bye advances without creating a fake game or replay.
4. Start. Each series plays its whole balanced schedule, not first-to-N wins. Most game wins advances. Semifinal winners feed the actual final; only the final-series winner is champion. All series at the same bracket stage use the same seed/rotation schedule. Later stages and tiebreak blocks use new seeds.
5. A tied series automatically plays an extra eight-game block, then a second if still tied. Wins are compared across the entire series. Still tied after those two blocks? The run stops at **Organizer ruling required**. Apply your policy announced before play, select the advancing participant, and enter a reason. The ruling and timestamp are saved in the private report. Match scores/replays are not rewritten, and the live reveal explicitly marks a ruling-based advancement. The software does not enforce the contents of your policy or invent a winner.

The admin bracket, per-game history and ruling form are private organizer controls. Pause/resume, frozen submissions, recovery and release-pack behavior match round robin. The progress total may increase when tiebreak blocks become necessary. There is no third-place match, double elimination, automatic season schedule or cross-match training.

## Put it on the big screen

Open **Audience view** on a saved run in either format, then use the fullscreen control (or maximize the window). The opening screen introduces the roster without exposing scores. You can open it while the run is still working; a series cannot be revealed until it is resolved. A tied knockout series awaiting a ruling cannot be revealed as a winner.

The host advances each matchup, presses **Reveal series result**, and gets a short suspense animation followed by the actual series winner or tied result. Use the host dropdown to select a pairing without displaying its outcome. The final **Championship reveal** has a larger trophy treatment and a brief confetti burst. Nothing auto-advances or reveals itself when the backend finishes. Reduced-motion preferences skip the suspense and decorative movement; there is no automatic audio.

For **Round robin**, the championship reveal uses total points and honors shared first place; it is not a simulated final match. For **Knockout**, use **View the bracket / Bracket overview** to show revealed winners advancing through the tree. Future-round slots stay labeled with their feeder series until those results are revealed. The dropdown uses stage labels, not spoiler-filled finalist names. Reveal earlier feeder series before a later round. The actual **Grand final** gets the gold championship treatment and confetti, based on its real series result.

Flagged matches produce a provisional-results warning. Review them before your live show. Audience view uses real entrant names; use the identity-redacted release pack separately for student analysis. Closing the view returns to private organizer results, so stop screen sharing first if those must stay private. Reveal progress is only in the current mounted view and resets on reload or leaving that format; saved match results and rulings do not reset.

## Frozen submissions, not live learning

For each run, the organizer tool snapshots uploaded code and its optional `model.json` under `data/competitions/`. It records hashes and checks for changes before/after matches and on resume. Built-in strategies and runtime sources are covered by a runtime fingerprint; source changes require a new run and a server restart, not mixed-version continuation.

Each match creates fresh bot instances and fresh working copies of the uploaded files. In-memory variables persist during a match, but scratch files are not carried to the next game. The original submitted artifacts are retained separately. This resets ordinary local scratch state for reviewed code; it is not a sandbox against deliberately reading/writing arbitrary host paths.

The runner does not call a training hook, save updated in-memory parameters, or resume a learner across rounds. Train between weekly sessions, export a new artifact and upload it as a new version. An adaptive league remains a separate format.

## Persistence, pause and recovery

The job record and replay are written after each completed match, with whole-file replacement rather than exposing partial JSON. Use **Pause after match** to finish the current game and save a clean boundary. The job is then resumable from history.

After a server restart, saved running jobs appear as **Interrupted**. Resume skips committed match indices and reruns an uncommitted interrupted match from its start. This is completed-match recovery, not exact mid-tick recovery or a guarantee against disk failure. Preserve/back up the entire `data/` folder, including competition snapshots, evaluations and replays. Do not move snapshots independently of their job records.

Only one evaluation/competition runs per server at once. Paused runs and brackets awaiting a ruling free the slot. Jobs can resume only while their frozen submissions and recorded runtime fingerprint still match. Updating application Python sources intentionally prevents continuation with different code. Bracket progression is rebuilt from committed match rows and saved rulings, not fragile in-memory advancement.

## Export the right thing

**Private admin JSON:** standings/bracket, team IDs, names/versions, pairings, any organizer rulings and diagnostic details. Keep it and original replays private. They identify the entrants. Ruling reasons and bracket identities are not included in the anonymous release pack.

**Anonymous replay pack:** available only for a completed run. Download once and share the same ZIP with all teams. It includes:

- `replays/match_XXXX.json`: valid replay files using neutral Player 1 / Player 2 labels within each game.
- `results.json`: per-match outcomes and numeric player metrics, linked to those replay files.
- `README.txt`: release limitations and import instructions.

The exporter shuffles file order and omits global bot/submission IDs, names, paths, arbitrary metadata, free-text events and error strings. It reconstructs replay fields from an allowlist instead of renaming a raw file. No team-to-alias mapping or private code/model files is included. Competition observations also use neutral player names.

**Individual participant packs:** when enabled in Round-robin setup, the completed run offers a separate ZIP for each entrant. Give each team only the ZIP named for them. It contains:

- `report.json`: that team's own version, per-match outcome and metrics, plus wins/draws/losses, flagged-match count and average metrics grouped by anonymous opponent alias.
- `opponent-summary.csv`: the same per-opponent wins/draws/losses, points, review flags and average metrics in a spreadsheet-friendly format.
- `replays/match_XXXX.json`: only matches involving that team's bot. Its name is **Your bot**; the other player has an alias such as **Opponent 01**, consistent within that ZIP.
- `README.txt`: what's included, how to use it and the limits of what the report can say.

Aliases are assigned independently for each participant's ZIP, so the same opponent can have different aliases in different downloads. File order is shuffled; original seeds are replaced with opaque per-match values. Entrant names/IDs other than the recipient's own name, diagnostics/error text, source code and model files are not included. The replay result text is also rewritten to neutral player labels. Maps, timings, visible behavior, or sharing packs can still expose identities; this is useful privacy redaction, not guaranteed anonymity. Inspect a sample ZIP before distributing it.

The report is performance feedback, not a trace of how a model learned. Every match uses a frozen submission, fresh bot instances and fresh working files; this runner does not carry learned parameters between matches or record weight changes, training steps or action rationales. Students can use per-opponent metrics and replays to form hypotheses and make changes between sessions, then compare the next submission. An in-game adaptive tournament would need a deliberate persistence/training interface and separate competition rules.

Maps, timings, actions visible through animation and distinctive behavior may still reveal who played. This is identity redaction, not a guarantee of anonymity or protection from collusion. Teams can study strategies, as intended. Do not claim a full replay hides opponent behavior.

Unzip the release, then load its `replays` folder in **Experiment Lab → Single candidate → Replay Library**, or load one JSON through Arena. Spectator replay frames are offline development data, not live bot observations. If training from them, reconstruct permitted observations for decision features and keep future/hidden state out of the online policy input.

## Suggested weekly use

Review and freeze one roster each week, run the round robin and review flags before release. Share the common anonymous pack, or enable individual packs and distribute each ZIP only to its named recipient; keep private standings and submission versions for your own records. Teams train or revise between sessions, then resubmit. Hold new seeds back for a final frozen-submission knockout tournament. Set qualification, seeding and draw/error/ruling policies in advance. The software supplies the two runners, not an automatic season calendar.

Do not expose this local server to participant code as though access were secure: trusted uploads can read local files/network, and local debug endpoints expose organizer data. Manual review and neutral labels are not adversarial isolation. A stronger execution boundary is a separate deployment/security task.

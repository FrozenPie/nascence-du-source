# J-2274: every cold=0 consumer switched to its own time window or marker (D-0453 gate)

## Session timing
- **Session started:** UNKNOWN
- **Last message before wrap:** UNKNOWN
- **Wrapped:** 2026-10-17 08:48:05 UTC

(Timing is UNKNOWN because this was a side session started by another session, worktree
`C:\Nascence\.claude\worktrees\jovial-carson-3c0dd3`, and `session_handoff.py` found no transcript under
`C--Nascence\e9f3bcfd-a7b2-40c4-bb98-be794f94966a.jsonl`. Real work ran roughly 08:30 to 08:50 local on
2026-10-17; the rollup's own event timestamps are 19:35 to 19:48 UTC of the ledger clock. This file was
committed on the job branch because the worktree hook refuses writes to the base checkout; it reaches
`C:\Nascence\docs\session_handoffs\` when the branch is merged.)

## Summary
Worked job J-2274, the gate Travis set in D-0453 before the origin-protected prune could be retired: every
non-recall consumer that selected memory_fragments by `cold=0` now reads by its own time window or its own
state marker, so a demoted row can no longer starve it. Four SELECTs changed in three files, two shadows
were left on cold=0 on purpose, six readers were confirmed already safe, and two real bugs surfaced on the
way. Committed as 0b8832a2 on branch `claude/j2274-cold-consumers-7a93c3`, not merged to main by this
session.

## Builds
- `core/memory_levels.py` shadow_distill fetch and its pool_size probe (around line 662/669): `cold = 0`
  dropped; the window is the module's own frontier, `timestamp > last_ts`. 367 rows before and after on the
  backup copy, no cold row inside today's window yet. F-2965.
- `core/memory_levels.py` drift_shadow (around line 861): `cold = 0` dropped; the window is the newest
  `_DRIFT_MAX` (5) self rows. The newest-five set is byte-identical today; the unlimited pool grew from
  32,406 to 67,920. F-2966.
- `core/night.py` dream_fade (around line 314): the fade half reads every dream younger than
  DREAM_COLD_HOURS (72 h) whether cold or not, `(timestamp > ? OR cold=0)`; the cooling half still asks
  cold=0 because that is the flip this writer itself performs, and skips rows already cold. 66 rows became
  104. F-2967.
- `core/refinery.py` _active_syntheses (around line 97): "not yet manufactured" is now the absence of a
  `distilled_from` link (the marker this station and memory_levels.commit_gist both write) instead of
  cold=0. 375 rows became 372, and the three lost rows are a bug, see Findings. F-2968.
- `docs/memory_levels_plan.md`: dated note with a per-consumer table inserted just above
  `## 8. Risks & guards` (plan_state.py cannot reach this doc, S-0294).
- Verification method for all four: sqlite `.backup()` copy of `data/memory/nascence.db` in the scratchpad
  (1.1 GB, 90 s, never the live file), script `verify_j2274.py` comparing before and after fragment-id
  sets, a superset check, and a synthetic cold=1 row inserted inside each window that must become
  reachable. The real `refinery._active_syntheses` and `night.dream_fade` functions were also run against
  the copy with `core.memory.store._connect` monkeypatched. `scripts/life_smoke.py` ALL OK;
  `scripts/smoke_test.py` SMOKE PASS, 3 cycles in 199 s against the live hot lane.
- UDMS change dossiers were pulled for `core/memory/store.py` and `core/memory_levels.py` before editing
  (both ELEVATED, static-only evidence; nothing in the listed dependents reads the changed SELECTs).

## Findings
- F-2969: `core/euclidean_recall.shadow_log` and the `core/emotion_construction` shadow were LEFT on
  cold=0 deliberately. Both are observe-only shadows of retrieve(), which keeps the cold wall by D-0453's
  own design and was out of scope. A shadow reading a different pool than the thing it shadows measures
  pool difference, not scoring difference. They cannot starve, since they take the newest 600 embedded
  rows. Dropping cold=0 would swap 58 of those 600 today. When J-2275's latency budget narrows what
  retrieve loads, these two should follow retrieve's new pool definition.
- F-2970: already safe with no change: `core/chapters.py` _candidates (origin plus `timestamp < now-48h`;
  27,349 of its 51,877 candidates are cold=1, so chapters already chapter across the cold wall),
  `core/grounded_learning.py`, `core/essay_lesson.py`, `core/memory_service.py` (goes through
  retrieve() or memory_edges), `core/night_dormant.py`, `core/loop_probe.py` (no SELECT of its own,
  delegates to prune_episodic dry_run). The grep over core, nodes and hud found no other consumer; remaining
  hits are retrieve() itself, prune_episodic, the temp-sync UPDATEs and index DDL in store.py, and offline
  scripts (dedup_reclaim_D0357, du_pulse counts, lod_retrieval_lab, memory_levels_batch).
- Bug 1 (F-2967): the prune was cutting the founder's dream fade curve. On the backup, 38 of the 104 dreams
  under 72 h were already cold=1, every one 52 to 70 h old. [INFERRED] prune_episodic's 48 h dream anchor
  (`core/memory/store.py` around line 2376) demoted them before dream_fade's 72 h halving finished; the age
  band matches exactly and nothing else writes cold on dreams. The fade now reaches them regardless.
- Bug 2 (F-2968): three 2026-06-20 syntheses (fragment ids 71596306, 799b3fe6, 3c9a3022) carry a
  `distilled_from` link to parent 424ee88c, which no longer exists. memory_levels.memory_lint
  (`core/memory_levels.py` around line 313) re-warms children of a missing parent every sleep, so the
  refinery re-distilled the same three rows every night since 2026-08-20: 31, 13 and 4 standing insights
  minted from them. The link-marker read ends the loop; J-2276 was spawned from F-2968 to clean the dangling
  links and decide whether memory_lint should stop re-warming children of a missing parent.
- The session's starting point: F-2963/F-2964 and D-0453 (travis, 2026-10-17, option (a)) are the
  background; the memory index already records that the main session went on to retire the prune
  (merged e4880e4f, restart-gated), so this gate was consumed the same day.

## Open
1. Branch `claude/j2274-cold-consumers-7a93c3` (commit 0b8832a2 plus this handoff) is not merged to main.
   Blocked on: the session that started this one (local_0eafd142-1ef3-4587-98af-5ef29c358873) deciding the
   merge. Next action: merge or cherry-pick into the restart-gated batch alongside e4880e4f.
2. D-0453 defeater (i), a consumer reading an empty window after demotion: not observable until the next
   boot. Next action: after restart, confirm `shadow_distill` pool_size > 0 in
   `data/memory_levels_fetch_probe.jsonl` and refinery clusters > 0 in `data/refinery_shadow.jsonl`.
3. J-2276 (build): drop the dangling distilled_from links to missing parent 424ee88c. Ready, no blocker.
4. [OPEN] euclidean_recall and emotion_construction shadows must follow retrieve's pool once J-2275 changes
   it; nothing enforces that today. Resolved by whoever lands the retrieve narrowing checking those two
   SELECTs.

## Warnings
- The rollup for this session shows 8 events; the J-2276 spawn is missing from it because
  `findings_log.py spawn-job` was run without `--session` (the tool warned). J-2276 exists in the job queue
  regardless.
- `scripts/smoke_test.py` fails in a fresh worktree until `data/identity/axiom.json` is copied in from
  `C:\Nascence\data\identity\` (gitignored). The copy in this worktree is not committed.
- The offline scripts `scripts/memory_levels_batch.py` and `scripts/lod_retrieval_lab.py` still filter on
  cold=0. They are lab tools, not live consumers, and were left alone; anyone reusing memory_levels_batch as
  a stand-in for shadow_distill should mirror F-2965's change.

## Pointers
- Side-session hand-over note: `C:\Users\USER\AppData\Roaming\Claude\side-session-notes\local_0eafd142-1ef3-4587-98af-5ef29c358873\J-2274_cold_consumers_handover.md`
- Verification script and backup: scratchpad `verify_j2274.py`, `verify_before.txt`, `nascence_backup.db` (temporary, session-scoped).
- `docs/memory_levels_plan.md` (note above section 8), `core/memory_levels.py`, `core/night.py`, `core/refinery.py`.
- Ledger ids: J-2274 (done), J-2276 (open), D-0453, F-2963, F-2964, F-2965 to F-2970.

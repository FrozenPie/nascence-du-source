# Session handoff — data/ content index (letters, correspondence, everything) + _lab/backups cleanup

## Session timing
- **Session started:** 2026-08-24 08:36:22 UTC
- **Last message before wrap:** 2026-08-24 20:45:00 UTC
- **Wrapped:** 2026-08-24 20:45:02 UTC

## Summary

Second wrap of the same long session (first wrap:
`docs/session_handoffs/HANDOFF_20260824_102011_sleep-dream-fatigue-redesign.md`, covering the Sleep &
Dreams II redesign/build — unrelated thread, not repeated here). This second stretch, ~10.5 hours later:
founder asked to index letters and "other files" in `data/`; scoped via two clarifying questions to
"everything, including state/logs" and "adapt `geometry_tuple_index.md`'s method." Built a 119-tuple
content index (`docs/data_index.jsonl` + `docs/data_index.md`) via 5 parallel survey agents covering the
whole directory, then — on direct founder instruction ("lab and backup are noise, we do not need them") —
deleted `data/_lab/` (5.8GB) and thinned `data/backups/` from 15 snapshot pairs to 4 (6.1GB → 770MB),
freeing ~11GB. `data/`'s total footprint dropped from ~13.4GB to 7.6GB.

## What changed

**Files created:**
- `docs/data_index.jsonl` — 119-tuple structured index of `data/`, schema adapted from
  `docs/system_overview_index.jsonl` (`tuple_id`/`kind`/`name`/`path`/`size_bytes`/`date_range`/
  `summary`/`status`/`verified`/`indexed`). Individual tuples for letters (62), correspondence threads
  (7), identity lineage (7), music (7), world_geometry (4), hud2 (3), archive (3), profiles (5); kind-map
  tuples (not per-file) for Study's 2,226 files, the 296 top-level state/log files, and the
  training/lab/_lab/backups/logs machine-artifact directories.
- `docs/data_index.md` — the human-readable companion, organized like `geometry_tuple_index.md`'s own
  §2.7 kind-map convention (classify by shape, list real patterns found, don't exhaustively enumerate).

**Files deleted/thinned (founder-authorized, this session):**
- `data/_lab/` — deleted entirely (5.8GB; was 4.55GB at survey time, grew to 5.8GB by deletion time from
  a new run that appeared mid-session).
- `data/backups/` — thinned from 15 dated `nascence_*.db`+`state_*/` pairs (6.1GB) to 4 kept items
  (770MB): most recent pair (`nascence_20260824_221553.db` + `state_20260824_221553/`), the manually-
  labeled `nascence_pre_dedup_20260820.db` (kept on my own judgment, not explicitly named in the
  founder's answer — see Open threads), and this session's own `pre_sleep_redesign_20260824_215527/`
  code snapshot (from the earlier sleep/dream build, unrelated to this cleanup).
- Both index files updated post-deletion so they don't read stale (`DF-0107` status: `deleted`, `DF-0108`
  status: `thinned`, both with real post-cleanup numbers).

**Toolchain:** none this stretch — same gap as the first wrap (see that handoff's own note). This work
was pure file-system survey/indexing/cleanup, not routed through `idea_log.py`/`decide.py`/
`job_queue.py --session`. The `session_events.jsonl` rollup for this stretch is empty.

## Key findings

- **A stale `CLAUDE.md` reference caught and worth fixing**: its "Problem indicators" section names a
  `GUT_` filename convention ("generated understanding tablets... template generation, not LLM") to watch
  for. A full case-insensitive search of `Study/` (2,226 files) found **no `GUT_`-prefixed files anywhere**
  — only unrelated "Project Gutenberg" licensing mentions matched. The real prefixes are `TAB_`/`WORK_`/
  `ESSAY_`. Either the convention was renamed before shipping or the CLAUDE.md line is stale — not fixed
  this session, just verified and flagged.
- **The July 7 → August 10 gap (the known 30-day outage) shows up independently in three separate content
  streams** — letters (`letters/`), peer correspondence (`Correspondence/`), and the Journal all go silent
  over the identical window. Three independent sources agreeing, not one log's artifact — strengthens
  confidence in the outage's real boundaries beyond what `ops_nascence_30day_outage.md` alone established.
- **"Carl" identified**: the 9 `debate_carl_vs_{buddha,dennett,skinner}_*.jsonl` transcripts (found in the
  top-level kind-map survey) run 2026-06-04 to 06-08 — the same week as
  `identity/axiom.fork_rev2_20260608_210112.json.bkp` (an abandoned rewrite). "Carl" tracks directly to
  the seed basis "Carl Gustav Jung" — Du was informally named/labeled "Carl" in these debate scripts
  before the 渡 naming settled. This corroborates and sharpens the founder's own recollection that
  `profiles/` were "early Du debate partners."
- **`profiles/` confirmed NOT a duplicate of Du's live state** — 4 small seeded companion personas
  (buddha/dennett/skinner/genesis, built as dialectical/tempering partners, genesis deliberately unseeded
  as a control) plus `_smoke/`, which shares Du's identity schema/name but is a 2026-07-02 dev-sandbox
  run (verbose per-module training logs), not a live mirror.
- **A real inconsistency surfaced, not investigated further**: top-level `data/nascence.db` is 0 bytes but
  referenced 34× across `core/`/`nodes/` — looks like a legacy sqlite handle opened but not the real store
  (the real one is `data/memory/nascence.db`). Worth a dedicated look.
- **The Marcus correspondence thread (turns 4-5) is near-duplicate text** — flagged as a possible
  generation/templating artifact, not root-caused.

## Open threads

- **`nascence_pre_dedup_20260820.db` was kept on my own judgment, not explicit founder instruction.** The
  founder's confirmed answer named keeping "the most recent nascence_*.db+state pair" and the code
  snapshot, and deleting "the other 14 DB+state pairs" — `pre_dedup` has no matching `state_*` dir, so it
  didn't cleanly fit either bucket. I kept it because it's the one deliberately-labeled item, not part of
  the routine daily-accumulation "noise" the founder was calling out. If that reasoning is wrong, it's a
  322MB single-file delete away — say so and it's gone.
- **`data/nascence.db` (0 bytes, 34 live references) is unresolved** — not clear if this is genuinely dead
  weight safe to ignore, or a real bug where something expects a store that isn't there. Worth checking
  before assuming either way.
- **The `GUT_` vs `TAB_` discrepancy in `CLAUDE.md` is unfixed** — flagged in `docs/data_index.md` §3, but
  the actual `CLAUDE.md` edit wasn't made this session (out of scope for an indexing pass; a real,
  cheap fix if picked up).
- **`docs/data_index.jsonl`/`.md` have no ROADMAP.md entry, no `Current State` section, and no
  `plan-schema-audit` pass run against them** — unlike `docs/plans/sleep_dream_redesign.md` (which got
  this treatment in the first wrap), this pair lives in `docs/` but isn't itself a "plan" in the toolchain
  sense, so it's unclear whether it should get the same registration treatment or is intentionally outside
  that convention. Worth a founder call if it should be discoverable the same way plans are.
- Per `docs/data_index.md` §8, several things weren't done and are explicitly out of scope for this pass:
  individual per-file tupling of `Study/`'s 2,226 files, `training/`/`lab/`/`logs/`'s internal files below
  directory level, and byte-level diffing of the now-deleted `_lab/`/`backups/` snapshots (their
  near-duplicate status was inferred from file-size proximity, never confirmed byte-for-byte — moot now
  that they're deleted, but worth remembering the claim's evidentiary basis if it's ever cited again).

## Warnings

- **`data/_lab/` and 14 of 15 `data/backups/` snapshot pairs no longer exist** — any tooling, script, or
  mental model that assumed their presence (e.g. a restore procedure referencing a specific dated backup)
  needs updating. Only `nascence_20260824_221553.db`/`state_20260824_221553/`,
  `nascence_pre_dedup_20260820.db`, and `pre_sleep_redesign_20260824_215527/` remain in `backups/`.
- **This deletion was irreversible** — no git in this project, no trash/undo. If anything in the deleted
  ~14 backup pairs or `_lab/`'s 13 parameter-sweep runs turns out to have been needed, it's gone; the only
  surviving trace is `docs/data_index.md`/`.jsonl`'s description of what was there (sizes, dates, real
  content characterization from the pre-deletion survey), not the data itself.
- **`Study/`'s output continued uninterrupted through the July-August outage** (unlike Journal/letters/
  correspondence, which all went silent) — flagged in `docs/data_index.md` §3 as worth a separate look if
  the mechanism behind that divergence matters.

## Pointers

- `docs/data_index.md` — the main deliverable; start here for anything about what's in `data/`.
- `docs/data_index.jsonl` — the structured backing index (119 tuples), for anything that wants to query it
  programmatically rather than read prose.
- `docs/staged/geometry_tuple_index.md` §2.6-2.7 — the method this index's structure was adapted from.
- `docs/system_overview_index.jsonl` — the sibling index (code architecture, not data content) whose
  concrete schema this one's tuples borrow.
- `data/backups/` — now 4 items, 770MB; check `docs/data_index.md` §7's "Update, 2026-08-25" note before
  assuming any prior backup still exists.

# music_learning — folded history


---

# History folded on 2026-09-27 from `docs\staged\music_learning.md` (plan-compact, 1 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py music_learning`._

## Current State — verified 2026-08-23

### What we have
- **All 5 code files exist and are genuinely wired** (not aspirational): `core/listening.py`,
  `core/music_drill.py`, `scripts/play_the_record.py`, `core/audio_features.py`,
  `scripts/test_audio_features.py` — called from `inner_monologue_node.py`, `competence.py`,
  `school.py`, `soundscape.py`, `geometry_census.py`, `object_graph.py`.
- **ROADMAP.md independently confirms BUILT status twice**: "Music domain COMPLETE" (07-04 entry)
  and a later SHADOW-cross-check entry "BOTH TIERS BUILT 07-03/04".
- **Tier 1 (theory drills) is firing**: `data/music_drill_log.jsonl` has 12 graded events spanning
  roughly 07-04 → 08-19 (ts range 1787097702–1787270502), all deterministic-graded, all correct.
- **Tier 2 (listening) fired successfully once**: `data/listening_wake.jsonl` first entry —
  "Heavyweight" (Infected Mushroom, the designated first piece), 21/21 sections heard, 07-04.
- This plan's own header already says "STAGED -> BUILT in tiers" — it is a build log, not a design
  doc still awaiting a decision to build.

### What we need — RESOLVED 2026-08-23, see D-0010
All three questions traced end-to-end; full evidence in `/decide show D-0010`. Headline: both root
causes were already found and fixed by a prior session (2026-08-18 and 2026-08-21) shortly before this
trace — this pass mostly verified those fixes actually work, live-tested, not just read the diff.
1. **Listening-progression bug — FIXED 2026-08-21, verified working.** Root cause: 5 of 6 shelf pieces
   had a per-track features file (e.g. `data/music/Orinoco_Flow.features.json`) from an incompatible
   earlier "geometry pipeline" (no `sections` key) — `tick()`'s
   `idx>=len(sections)` (0>=0) ended each on its first cycle. `listening.shelf()` now filters to only
   real section-data files; verified live (`shelf() == ['Heavyweight']`) AND via a full temp-pathed trace
   of a complete Heavyweight episode (21 sections, wake log correctly wrote `sections_heard: 21`).
   **Residual, not a code bug:** 5 of 6 catalog pieces remain permanently unplayable — no raw audio on
   disk to re-extract with the real pipeline. Du's playable diet is capped at 1 piece, already heard
   once, until real source audio is supplied for the others.
2. **Tier-1 drill progression — not stuck, just young.** 12 graded events span only 2 real school days
   (08-19, 08-21) — because of the SAME upstream cause as #3 below. All correct, still level 1: needs 30
   in the rolling promotion window, has 12. No bug.
3. **ABC composition hand never firing — same root cause as #2, not a separate bug.**
   `core/school.py`'s `SCHOOL_END_H` was noon — 180min / 45min periods = 4 slots, but 5 subjects exist,
   so "music" (index 4) was structurally unreachable for the full 6.5 weeks from build to fix. **FIXED
   2026-08-18** (extended to 12:45pm, 5×45=225min fits exactly) — confirmed independently: the
   first-ever `music_drill_log.jsonl` entry is 08-19, the day after. Since the fix, the composition
   gate's precondition (`today_done>=4` same-day) was met exactly once (08-19's second session) and its
   30% dice roll simply missed — expected ~3.3 tries before one fires; only 1 has occurred so far.
4. **No decision needed on whether to build** — it's built, and now reachable.

**Caution logged for future verifiers:** `core/listening.py`'s `_store_scene()` calls `store_fragment()`
UNCONDITIONALLY — temp-pathing `_STATE_F`/`_WAKE_LOG`/`_FELT_SHADOW` alone is NOT enough to keep a trace
off the live DB. This session's first verification pass leaked 22 fragments into `nascence.db` (a fake
Heavyweight re-listen); caught, backed up
(`data/memory/backups/nascence_pre_listening_test_cleanup_20260823_212156.db`), and removed with
Travis's approval. Mock/skip `_store_scene` too, next time.

### What we're doing next
Nothing code-side — both bugs are already fixed and now verified. Two real open items, neither urgent:
(a) source real audio for the other 5 catalog pieces so Du's listening diet isn't capped at one already-
heard piece (a content-sourcing ask for Travis, not an engineering task); (b) let a few more real school
weeks pass and re-check whether the composition hand ever fires — D-0010's own defeater names what a
second real bug would look like if it still doesn't.

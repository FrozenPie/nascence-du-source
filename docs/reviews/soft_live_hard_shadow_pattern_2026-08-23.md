# Is "soft live + hard shadow-compare" a reusable pattern? (D-0006 meta-ask, 2026-08-23)

Travis's ask, from D-0006's ruling: after building the journal grounding grader, think about whether
this shape generalizes to other plans facing a similar rigor-vs-cost tradeoff, and if so, what a
reusable version would need.

## It already IS the pattern — this is instance #5, not #1

Nothing new was invented to build `core/journal_grounding_shadow.py`. It reuses
`left_lane.grade_gist_faithfulness` + `memory_levels.source_fidelity` +
`memory_levels.verify_invention_claims` verbatim — the exact same three-part judge
(LLM-plausibility + deterministic-fidelity + backstop-against-judge-hallucination) `core/memory_levels.py`
already built for consolidation gists. The "soft live, hard grade in shadow, decide from accrued data"
shape already exists, independently, at least four other places in this codebase:

| Instance | Soft/live path | Hard/shadow grader | Log |
|---|---|---|---|
| Consolidation gists | gist distilled from cluster, stored as-is | `grade_gist_faithfulness` + backstop, **already promoted to a live flag-gated demotion gate** (§14.1) | inline in `memory_levels` state |
| Geometry census (P0) | — (pure observation, no live path to compare against) | `geometry_census.py` snapshot | `data/geometry_tuples.jsonl` |
| Continuous stream (P0) | the live clock-gated pacer | `stream_drive.py` computes the would-be gap | `data/stream_drive_shadow.jsonl` |
| Journal week roll-up (P1) | soft-authored cap, no gate | `journal_grounding_shadow.py` (this build) | `data/journal_grounding_shadow.jsonl` |

The gist-grading case is the most important data point: it shows the pattern's own natural lifecycle —
shadow first, then PROMOTED to a live gate once the shadow data proved the judge trustworthy (with the
backstop specifically because the raw judge over-flags — the Black-Bear false-positive rate this
session's own backfill run reproduced again: all 4 of journal_grounding_shadow's first graded caps had
"invented" accusations, and every single one was a false flag once checked against the real sources).
That lifecycle — shadow → prove the judge → promote to gate — is the actual reusable claim, not just
"log a shadow verdict somewhere."

## What's NOT missing (don't build this)

A generic "shadow grader" abstraction over the LLM judge call itself is not worth building. Each
instance's *signal* is genuinely different (drive/gap physics vs cross-space tuple structure vs
gist-faithfulness), so the grading logic has to stay plan-specific. Forcing them through one interface
would cost real clarity for a thin win.

## What IS missing (worth building, low cost)

Two small, genuinely repeated pieces of boilerplate, both on display in this session across three
separate shadow instruments (`geometry_census`, `stream_drive`, `journal_grounding_shadow` — plus
`stick_test` and `mapping_census` from earlier the same day):

1. **The JSONL-append + status() boilerplate.** Every one of the five files above hand-writes the same
   ~10 lines: `_DATA.mkdir(...)`, `open(_LOG, "a")`, `json.dumps(row) + "\n"`, wrapped in a bare
   `try/except: pass`, plus a `status()` that re-reads the whole file and computes a mean/fraction. A
   `core/shadow_log.py` with `append(path, row)` and `summarize(path, fields=...)` would cut every future
   instrument by ~15-20 lines and remove one more place a copy-paste bug (e.g. forgetting `.parent.mkdir`
   or the fail-open wrapper) could quietly break a fresh instrument on its first live call.
2. **The "read a shadow log against its promotion criteria" analysis itself, on the Claude/audit side —
   not the Du side.** J-0002 (continuous_stream, this session) and this journal grader both needed a
   bespoke, one-off Python script to answer "does the shadow data support promotion?" `plan-liveness`
   already tracks that these logs exist and are accruing (it lists `stream_drive_shadow.jsonl`,
   `geometry_tuples.jsonl`, and now `journal_grounding_shadow.jsonl` by row-count/freshness) — but it
   doesn't compute divergence. A plan could declare, in its own doc, a tiny machine-readable promotion
   spec (e.g. "green if mean(faithful) > 0.7 and genuine_inventions == 0 over the last N rows") that a
   shared `plan-shadow-read` tool evaluates generically, the way `plan-liveness` already evaluates
   GATE-MET/NEVER-FIRED generically. This is the more valuable of the two — it directly answers Travis's
   "help our indexes/tuples harden our skills for being future-proof" framing, since it would make the
   NEXT shadow-log read (whichever plan it's for) reuse a tool instead of reusing a memory of how the
   last one was written.

Neither is scoped/committed here — (1) is a small standalone build; (2) is a real toolchain design
decision (spec format, where it lives, how `plan-liveness` and it relate) that deserves its own pass
rather than being improvised at the tail of this job. Both logged as job J-0007 for a future session to
pick up or decline.

## Answer to the actual question

Yes, generalizable — it already generalizes, four times over, without anyone naming it as a pattern
until now. The reusable piece worth building isn't a new abstraction over the JUDGE (that stays
plan-specific, correctly) — it's shared plumbing on the LOGGING side (cheap, mechanical) and a shared
READING tool on the audit side (the higher-value piece, and the one that actually saves a future
session's time the way `plan-liveness`/`job-queue` already do for the rest of the toolchain).

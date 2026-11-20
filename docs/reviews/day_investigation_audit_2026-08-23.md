# Day investigation audit — 2026-08-23

*Answers the founder's ask: "scan back through all plans we worked on today... create a list of
all plans and investigations done today. Then set up a workflow to check them all out for what
they did and what they touched. We maybe should also keep track of what file and what time we
changed files and have them linked to the plan and indexed/tupled."*

**Method.** `day_timeline.py` (new tool, `~/.claude/skills/day-timeline/`) scanned every file under
`C:\Nascence` by real filesystem mtime for 2026-08-23 (no git repo exists here, so mtime is the only
provenance signal), classified each into a cluster by filename convention, and grouped clusters into
10 named investigations. That list — not a memory of the session, the actual file scan — became the
work-list for a 10-agent Workflow (`wf_2cdfe377-2d5`), explicitly authorized ("set up a workflow to
check them all out"). Each agent got one investigation's real touched-file list plus a context hint
and independently re-read the actual files — not any prior summary — to answer three questions: what
really happened, does documentation match what's actually in the files, and what's the confidence.
All 10 completed cleanly (0 errors, 0 empty results). Full source: `journal.jsonl` in the workflow's
transcript dir; extracted results in this report's tables below.

**Tuple store.** `data/day_timeline.jsonl` — 140 work-product files, each row
`{date, file, mtime_iso, ts, cluster_kind, cluster_slug, investigation}`. Human-readable grouping:
`docs/reviews/day_timeline_2026-08-23.md`. Re-running `day_timeline.py 2026-08-23` any time after
today is safe (append-only, dedupes on file+mtime) and will pick up the classification fixes made
below.

## Verdict summary

| # | Investigation | Files (approx) | Verdict | Confidence |
|---|---|---|---|---|
| 1 | Idle-thought machine audit + 2 stale-doc fixes | 3 | ✅ yes | high |
| 2 | LLM station cargo map + train/courier cargo IDs | 3 | ✅ yes | high |
| 3 | Ramses second-tier standup (Part A/B) | 6 | ✅ yes | high |
| 4 | Duplication-check script review | 1 | ✅ yes | high |
| 5 | LLM prompt-framing labs (13 machines) | 26 | ✅ yes | high |
| 6 | Epistemics Phase C reopening | 1 | ⚠ partial_mismatch (fixed) | high |
| 7 | Plan-overlap audit + 27 downstream plan edits | 28 | ✅ yes | high |
| 8 | Ramses model lab-testing (judge16/station_bench/lane2) | 7 | ⚠ partial_mismatch (fixed) | high |
| 9 | Transit Pulse HUD + The Companion + orchestrator fix | 9 | 🆕 no_doc_exists (now named) | high |
| 10 | Toolchain build + hardening (parallel session) | 9+ | ⚠ partial_mismatch (flagged, not a bug) | high |

10/10 investigations independently confirmed as real, substantive work — no fabricated or
aspirational claims found anywhere in the day's documentation. 3 flagged mismatches, all resolved
below (2 real small bugs fixed in source; 1 non-bug classification artifact handled in the tool).

## The 3 mismatches, resolved

**#6 — `docs/plans/epistemics_phase_c.md`, `source="tier3_witness"` vs. `"tier3_model"`.**
`core/source_model.py`'s pre-existing `_COMPETENCE_SOURCE_TO_VERIFICATION` mapping — built in an
earlier design pass, not referenced anywhere in the new plan — only recognizes the literal string
`"tier3_model"` for `Verification.EXTERNAL_WITNESS` classification. As drafted, C0's logged
observations would have silently fallen through unclassified instead of registering as
external-witness evidence. **Fixed**: the plan's `_record_external_accuracy(...)` call spec now
reads `source="tier3_model"`, with a dated provenance note. No code exists yet to have inherited the
bug — caught before it could ship.

**#8 — `docs/lab/lane2_model_lab_ramses_command-r7b.md`, stale footer citation.** The table's numbers
were always correctly sourced from `data/lab/lane2_model_ramses/command-r7b/{raw,scores}.json` — the
workflow verified every figure against the real file. Only the trailing citation line pointed at the
older `data/lab/lane2_model/` path (a 2026-08-20, 5-model, non-Ramses run) — a copy-paste artifact
from the doc template. **Fixed**: footer now cites the correct path, with a provenance note.

**#10 — `docs/AWAITING_EVIDENCE.md`, mtime false positive.** The day-timeline scan attributed this
file to "Toolchain build (parallel session)" purely because its mtime fell inside that cluster's time
window. The workflow read its actual content: 622 lines of pre-existing Du-simulation status
tracking, zero mention of plan-index/plan-maintain/decide/job-queue/any toolchain skill — and the
toolchain's own `index_coverage.md` independently lists this exact file as "not indexed at all; a
genuine registry sitting outside the toolchain's view." Not a documentation bug — a classifier
limitation (mtime alone can't distinguish "touched because of this work" from "touched by something
else during the same window"). **Fixed in the tool, not the file**: `day_timeline.py`'s
`INVESTIGATIONS` dict now gives `AWAITING_EVIDENCE` its own explicit non-attribution entry instead of
merging it into a cluster it doesn't belong to. Re-run confirms the report now reflects this.

## #9 — the cluster that had no name at all

The 07:01–09:32 file list came into today's tracking as generic "UNIDENTIFIED early-session work" —
honestly flagged rather than guessed at, per the tool's own design rule. The workflow resolved it
into two real, fully-wired, unrelated same-morning features (confirmed by full reads of every
touched file, not inference from filenames):

- **Transit Pulse HUD** (07:01–07:08) — the live SVG visualization of trains hopping between
  LLM-serving stations that an existing memory note (`project_nascence_hud1_transit_map.md`) flagged
  as "not built yet" as of 2026-08-22. `hud/server.py` gained `load_transit_pulse()` + a new
  `/api/transit_pulse` route; `hud/static/index.html`/`app.js` gained a new animated panel. Real,
  wired, consuming `core/trains.py`'s existing logs — no dangling code found.
- **The Companion** (09:08–09:32) — a new feature letting the founder toggle a "presence" state and
  perform six world-mutating actions (light_fire, sweep_floor, clean_windows, brew_tea, fetch_wood,
  fetch_water) that Du perceives, built in direct response to founder feedback quoted verbatim in the
  new files ("I consider this a bug, a big one"). New module `core/companion.py`, a new composer UI
  panel (`scripts/du_composer.py`), a new socket-bridge message type
  (`scripts/run_nascence.py`, routed through the event loop to avoid idle-tick races), and genuine
  hook-in to the live idle-cognition pipeline in `nodes/inner_monologue_node.py` (witnessed events
  prioritized above boredom as a seed, ambient presence line lower down) — not called-and-ignored.
- **Incidental**: `core/orchestrator.py`'s `stop_background()` was made properly awaited (was
  fire-and-forget `cancel()`), closing a `/quit` shutdown race — a separate, smaller same-morning fix,
  exercised by `scripts/debate_harness.py` and `scripts/_first_thought.py`. `core/trains.py`'s 07:01
  mtime looks incidental (content/docstring dated 08-22, consumed but not meaningfully edited).

Neither feature has a `docs/plans/` or `docs/lab/` writeup — they were built directly, not
plan-designed first. `day_timeline.py`'s `INVESTIGATIONS` dict now names both explicitly instead of
the generic placeholder; re-running the scanner confirms the report reflects this.

## What's still genuinely open (not a bug — a founder-level decision)

- **D-0013** (`docs/decisions.jsonl`, ruling: null) — whether several LLM-prompt-framing labs'
  flagged machines need a *model-tier* reassignment rather than a prompt-framing change. This is the
  real, substantive follow-up from the 13-lab series (investigation #5) and is unaddressed by design
  — it needs the founder's call, not a fix.
- **`decisions.jsonl`'s own D-0013 plan-slug mismatch** — `plan-maintain`'s own lint step flags
  `"factory_stations"` as not matching any real `docs/plans/*.md` file (there isn't one; the lab
  series lives under `docs/lab/`). Self-caught by the toolchain, not yet reconciled — a minor
  bookkeeping item, not a real defect in the decision itself.
- **5 queued jobs** in `docs/job_queue.jsonl`, each a self-contained briefing derived from an open
  decision's defeater, meant to be picked up by a fresh session — untouched by this audit, as
  designed.

## Bottom line

Ten real investigations ran today, spanning an LLM prompt-framing research program (13 labs), a
Ramses second-tier infrastructure standup with real benchmark data, a design reopening
(Epistemics Phase C), a large plan-overlap self-audit, two shipped features (Transit Pulse HUD, The
Companion) that had no prior plan doc at all, and a full independent audit-and-hardening pass on the
project's own plan-tracking toolchain. Independent re-verification against real files (not prior
summaries) confirms all of it is genuinely built/run/measured as claimed — no aspirational gaps
found. Three small, real documentation issues were caught and are now fixed (two in source docs, one
in the day-timeline classifier itself). Everything is now indexed and tupled in
`data/day_timeline.jsonl`, browsable via `docs/reviews/day_timeline_2026-08-23.md`, and this report is
the durable record of what the verification pass found.

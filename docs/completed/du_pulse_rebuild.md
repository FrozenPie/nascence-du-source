# Du-Pulse Rebuild — a pulse that persists, links, and remembers what to check

> **Status: ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: LIVE — full build shipped 2026-08-29 (J-0417); see Current State below. Originally
> scoped 2026-08-23, sequenced after [gauge_rethink.md](../plans/gauge_rethink.md):
> this plan's severity model and JSON schema depend on that plan's taxonomy pass, not the other way round.
> UPDATE 2026-08-29 (J-0340): the taxonomy dependency is now resolved — `gauge_rethink.md`'s "Taxonomy
> landing" section has all 73 current gauges categorized into the 4 CONFIRMED buckets (D-0066). This
> plan's `run` command and JSON summary block can now be built against that shape. Still blocked on
> nothing else from gauge_rethink.md except the redundancy/ownership follow-up (J-0341, does not block
> starting the build — a gauge can be re-categorized or dropped later without changing the 4-category
> schema itself). The actual build (wrapper script, store, severity evaluation per category, HUD1 wiring)
> is NOT part of J-0340 and remained open until 2026-08-29 (previously a stale cross-reference here
> pointed at J-0347, which is actually memory_levels_plan's Phase 2 job — a copy-paste error, corrected).
> D-0094/D-0095 (both ruled 2026-08-29) settled this doc's two founder-call open questions below: snapshot
> all 73 gauges every run, and ship manual-only watch-item resolution for now. See the job that does the
> real build for current status.**

```plan-state
stage: shipped
phase: Full build shipped 2026-08-29 (J-0417): store, CLI, HUD1 card, memory-links harvester, all verified live end-to-end
verified: 2026-10-16
evidence_read: 2026-08-29
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 8
```


## Current State — verified 2026-09-27

### What we have
- J-0417 (2026-08-29, F-0550) built the full design end-to-end: an additive JSON summary block in
  `scripts/du_pulse.py` (all 73 gauges), `scripts/du_pulse_check.py` (run/watch/history/board),
  a fourth memory-links harvester (`harvest_pulse_flags`), and a Du-Pulse Check card wired into
  HUD1 — all verified live (real P-0001 snapshot, real HUD page render, zero console errors).

### What we need
- Nothing further from this plan itself; the only deferred item (gauge redundancy/ownership) was
  always out of scope and is tracked separately as J-0341.

### What we're doing next
- No open work. Revisit only if the 4-category taxonomy itself needs to change, or if watch-item
  auto-resolution (declined for v1 per D-0095) is reconsidered once real usage accrues.

---

## The problem

Every pulse check currently produces a wall of text that a Claude session reads, narrates, and then
forgets. The script itself is meticulous — it really does check ~50 signals against live data — but the
skill wrapping it has none of the discipline the rest of today's toolchain (`plan-index`, `decide`,
`job-queue`, `gauge-check`, `memory-links`, `idea-log`, `findings-log`) already applies: no structured
store, no history, no cross-links, no way to ask a pulse to remember something for next time. "Old and
cobbled together" (founder, 2026-08-23) is accurate: the data collection is real, the record-keeping is
not.

## The design (scoped 2026-08-23)

**Store:** `docs/du_pulse_checks.jsonl`, IDs `P-0001` upward, built with the shared
`_plan_tools_common.py` conventions already used everywhere else in the toolchain — `atomic_write_text`
for the full-rewrite store, `log_event` on every write, a per-tool incrementing ID counter.

**One small, additive change to `du_pulse.py`:** emit a single JSON summary block after its existing
human-readable output, carrying all current gauge values and flags. Nothing about the script's existing
output or behavior changes — this is purely an additional line at the end, so any existing habit of
reading its printed output directly keeps working unmodified.

**New wrapper `du_pulse_check.py`**, commands modeled on `gauge-check`'s proven four-way split:
- `run` — execute the pulse, parse the JSON block, persist a timestamped snapshot, evaluate a first-pass
  severity from the flags section per gauge category (Regression alarm / Growth tracker / One-off
  shadow-run evidence / Engagement-texture — see gauge_rethink.md's "Taxonomy landing" section for the
  full per-gauge assignment, landed 2026-08-29), and check any open watch-items against the new reading.
- `watch add "<text>" [--linked-plan|--linked-job]` / `watch list [--open]` / `watch resolve <id> --note
  "..."` — the persistent carry-forward mechanism. This is the direct fix for the `J-0120`-shaped gap:
  a specific ask ("watch for X next time") gets its own durable record instead of being smuggled into
  whatever tracker happens to be open at the time.
- `history --gauge <name>` — trend a single gauge's readings across past runs. This is the actual
  "find patterns" capability being asked for — currently impossible, since no past reading is stored
  anywhere.
- `board` — last recorded state, no recompute, for a fast check-in (same shape as `gauge-check board`).

**Memory-links integration:** `build_edges.py`'s harvester pattern is genuinely pluggable — one function
per source type, confirmed by direct inspection 2026-08-23. Add a fourth harvester,
`harvest_pulse_flags()`, registering a new node kind `pulse` and edge types connecting a flag or resolved
watch-item to the plan/job/finding it's actually about. This is what makes "has this specific gauge issue
shown up before, and in connection with what" an answerable question later, instead of something only a
human's memory of past sessions could answer.

**Explicitly out of scope for this plan:**
- Job-queue has no "blocked until an external event happens" status (confirmed during scoping — only
  `open/in_progress/done` exist, and `needs_input` means "founder decision needed," not "wait for Du to
  do something in the world"). `J-0120` worked around this by stating the precondition in prose inside the
  briefing. This is a real gap in job-queue's own schema, not something to patch inside du-pulse — it
  should be its own idea/decision if it's worth fixing.
- The gauge redundancy-audit consolidation (the monoculture cluster) and per-subsystem gauge ownership —
  still deferred, now to J-0341 specifically (D-0066, 2026-08-28), not to `gauge_rethink.md` in general.
  The 4-category taxonomy itself is resolved (see above); this plan should build against the landed
  categorization, not wait on J-0341 — a gauge's category assignment can be revised later without
  reworking the schema shape.

## Open questions — RESOLVED 2026-08-29 (D-0094, D-0095)

- **D-0095 (ruled):** watch-items resolve manually only for the first build. Auto-detection logic for "is
  this specific condition now true" varies per watch-item and is real design work on its own — ship
  manual resolve first, revisit once the tool has real usage and a recurring pattern of directly-queryable
  conditions emerges.
- **D-0094 (ruled):** `run` snapshots **all** 73 gauges every time, not just flagged/watched ones. Matches
  the script's own "meticulously checked for all the gauges" baseline and preserves the ability to later
  ask "was there an early signal in a gauge nobody was watching yet." Revisit only if the full-snapshot
  store's size becomes a real practical problem — the per-category tiered alternative (13 Regression
  alarms full-history, the rest on-demand) stays available as a fallback, not adopted now.

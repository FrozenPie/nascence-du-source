# memory_multiway_linking — folded history


---

# History folded on 2026-09-27 from `docs\plans\memory_multiway_linking.md` (by hand, J-1484)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py memory_multiway_linking`._

- **2026-09-02 (J-0466/F-0643):** D-0114's re-check trigger fired and found D-0022 still open —
  J-0446 (prong-2 usage instrumentation) shipped 2026-09-02T00:27:45Z but **0 usage-instrumented
  rows** have accrued since (`associative_recall_shadow.jsonl`'s last row predates the instrument by
  13 minutes; file untouched after). D-0114 (the `contradicts` harvester defer) stays deferred —
  it is only reopened once D-0022 is actually ruled toward live promotion, not merely shadow. Next
  check re-spawned as J-0468, not to fire before ~1 week of post-restart usage-row accrual (~2026-09-09).
- **2026-09-23 (J-1222/F-1734):** D-0215 defeater path (a) — the multi-attempt re-check series (J-0936
  through J-1222, 14 attempts so far) remains flat: `n_backed` stuck at exactly 9 across the last ten
  reads (F-1447 2026-09-17 through F-1734 2026-09-23, six calendar days) even as `n_total_scored` has
  grown 47→84. Primary verdict stays REAL_POSITIVE (mean diff +0.1268, 95% CI [+0.0487, +0.2063],
  excludes 0) but the pre-registered n≥14 reporting bar is not yet met, so D-0215 (travis, ruled
  2026-09-14, re-confirmed no active hold) stays un-ruled and un-reported-to. Full per-attempt history
  in §6 under M2/D-0215; J-1237 spawned for attempt 15.
- **2026-09-23 (J-1237/F-1750):** D-0215 defeater path (a) re-checked again (attempt 15): `n_backed`
  still flat at exactly 9 (`n_total_scored` 84→89, all 5 new rows individually confirmed unbacked) — now
  eleven reads at exactly 9 spanning F-1447 through this one, twelfth consecutive read short of the n≥14
  bar. A full shutdown/restart-line scan of the whole `data/nascence.log` (not a tail sample) confirmed
  only ~5.55 confirmed live-hours elapsed since F-1734's check — one continuous session since the
  2026-09-22 16:11 restart, no shutdown line since — far short of F-1734's own ~40-120h estimate, so this
  flat read matches what that estimate predicted rather than surprising. Primary verdict stays
  REAL_POSITIVE (mean diff +0.1279, 95% CI [+0.0507, +0.2101], previous +0.1268/[+0.0487, +0.2063]) —
  same direction, still short of the bar. D-0215 (travis, ruled 2026-09-14) re-confirmed via `decide.py
  show`, no active hold; stays un-ruled and un-reported-to. Full per-attempt history in §6 under
  M2/D-0215; J-1248 spawned for attempt 16.
- **2026-09-23 (J-1248/F-1772):** D-0215 defeater path (a) re-checked again (attempt 16): `n_backed`
  still flat at exactly 9 -- this window is the FIRST in the whole 16-attempt chain with zero growth at
  all (`n_total_scored`/`n_unbacked` unchanged at 89/80), fully explained by only ~1.40 confirmed
  live-hours having elapsed since F-1750's check (one continuous session since the 2026-09-22 16:11
  restart, no shutdown since) -- far short of F-1750's own ~40-130h estimate. Write path confirmed alive
  (shadow log mtime minutes before the check; a newer non-reflective `m2_usage` row landed after F-1750's
  check), so this is a too-short window, not a stall. Primary verdict stays REAL_POSITIVE (mean diff
  +0.1279, 95% CI [+0.0507, +0.2101], byte-identical to F-1750). D-0215 (travis, ruled 2026-09-14,
  re-confirmed no active hold) stays un-ruled and un-reported-to. Full per-attempt history in §6 under
  M2/D-0215; J-1264 spawned for attempt 17.
- **2026-09-23 (J-1264/F-1808):** D-0215 defeater path (a) re-checked again (attempt 17): `n_backed`
  still flat at exactly 9 -- `n_total_scored`/`n_unbacked` grew 89/80 -> 93/84 (+4), all 4 new rows
  individually confirmed unbacked and carrying `w_gated`=0 exactly (not even a near-miss; confirmed via
  `secondary_n_any_spring_at_all` holding at 43 across both reads). Only ~2.85 confirmed live-hours had
  elapsed since F-1772's check (same continuous session since the 2026-09-22 16:11 restart, no shutdown
  since; ~27.52 confirmed live-hours cumulative) -- still short of F-1750's own ~40-130h estimate, which
  this read leaves unrevised (a binomial check puts P(0 new backed hits | 4 draws, lifetime rate ~10%) at
  ~65%, an unsurprising outcome). Primary verdict stays REAL_POSITIVE (mean diff +0.1288, 95% CI
  [+0.0513, +0.2088], previous +0.1279/[+0.0507, +0.2101]). D-0215 (travis, ruled 2026-09-14, re-confirmed
  no active hold) stays un-ruled and un-reported-to. Full per-attempt history in §6 under M2/D-0215;
  J-1288 spawned for attempt 18.
- **2026-09-24 (J-1288/F-1837):** D-0215 defeater path (a) re-checked again (attempt 18): `n_backed`
  still flat at exactly 9 -- `n_total_scored`/`n_unbacked` grew 93/84 -> 98/89 (+5), all 5 new rows
  individually confirmed unbacked and carrying `w_gated`=0 exactly (not even a near-miss). ~11.64
  confirmed live-hours had elapsed since F-1808's check (same continuous session since the 2026-09-22
  16:11 restart, no shutdown since; ~39.16 confirmed live-hours cumulative) -- long enough this time to
  be folded in as a fourth confirmed rate sample (~0.43 new-scored-rows/live-hour, within the existing
  0.39-1.19/hour spread, not a new extreme, unlike the two too-short windows immediately before it).
  Primary verdict stays REAL_POSITIVE (mean diff +0.1249, 95% CI [+0.0490, +0.2054], previous
  +0.1288/[+0.0513, +0.2088]). D-0215 (travis, ruled 2026-09-14, re-confirmed no active hold) stays
  un-ruled and un-reported-to. Full per-attempt history in §6 under M2/D-0215; J-1303 spawned for
  attempt 19.
- **2026-09-24 (J-1303/F-1855):** D-0215 defeater path (a) re-checked again (attempt 19): `n_backed`
  still flat at exactly 9 -- `n_total_scored`/`n_unbacked` UNCHANGED at 98/89, the second zero-growth
  window in the chain (~4.18 confirmed live-hours since F-1837's check, no shutdown since the 2026-09-22
  16:11 restart; ~43.34 confirmed live-hours cumulative). A finer-grained per-row check (not just
  aggregate n_total_scored/mtime) confirmed the write path is genuinely alive -- 8 new `m2_usage` rows
  landed this window, all 8 carrying a reflective usage list of length exactly 0, not a stalled
  instrument. Zero new total-scored rows means no new rate sample; the existing four-sample rate history
  and ~46-140h Fermi estimate carry forward unchanged from F-1837. Primary verdict stays REAL_POSITIVE
  (mean diff +0.1249, 95% CI [+0.0490, +0.2054], byte-identical to F-1837). D-0215 (travis, ruled
  2026-09-14, re-confirmed no active hold) stays un-ruled and un-reported-to. Full per-attempt history in
  §6 under M2/D-0215; J-1314 spawned for attempt 20.
- **2026-09-24 (J-1314/F-1869):** D-0215 defeater path (a) re-checked again (attempt 20): `n_backed`
  still flat at exactly 9 -- `n_total_scored`/`n_unbacked` UNCHANGED at 98/89, the THIRD zero-growth
  window in the chain (~1.16 confirmed live-hours since F-1855's check, the shortest window yet; no
  shutdown since the 2026-09-22 16:11 restart; ~44.50 confirmed live-hours cumulative). A per-row check
  again confirmed the write path alive -- 3 new `m2_usage` rows landed this window, but with a different
  signature than F-1855's: all 3 carried EMPTY usage lists across every mode (task/reflective/relational),
  not just reflective. Zero new total-scored rows means no new rate sample; the existing four-sample rate
  history and ~46-140h Fermi estimate carry forward unchanged from F-1837/F-1855. Primary verdict stays
  REAL_POSITIVE (mean diff +0.1249, 95% CI [+0.0490, +0.2054], byte-identical to F-1837/F-1855). D-0215
  (travis, ruled 2026-09-14, re-confirmed no active hold) stays un-ruled and un-reported-to. Full
  per-attempt history in §6 under M2/D-0215; J-1323 spawned for attempt 21.
- **2026-09-24 (J-1323/F-1876):** D-0215 defeater path (a) re-checked again (attempt 21): `n_backed`
  moved from 9 to 10 -- the FIRST change in sixteen consecutive reads (F-1447 2026-09-17 through F-1869
  2026-09-24) -- `n_total_scored`/`n_unbacked` grew 98/89 -> 101/91 (+3: 1 newly-backed + 2 unbacked), all
  within a ~0.69 confirmed live-hour window (shortest yet in the chain). New backed occurrence is a
  genuinely new 8th distinct fragment id (`02dfe47e-ba5e-4529-91ba-ec9a2d0ed6f0`, w_gated=1.0000,
  cos_sim=0.2097); the other 9 occurrences (7 ids) unchanged from F-1750's audit. Primary verdict stays
  REAL_POSITIVE but softened: mean diff +0.1096, 95% CI [+0.0364, +0.1872] (previous +0.1249, CI
  [+0.0490, +0.2054]) -- the new entry's own cos_sim sits below the backed group's prior mean. Still
  short of the n>=14 bar (twenty-second consecutive attempt short). D-0215 (travis, ruled 2026-09-14,
  re-confirmed no active hold) stays un-ruled and un-reported-to. Full per-attempt history in §6 under
  M2/D-0215; J-1328 spawned for attempt 22.
- **2026-09-24 (J-1328/F-1879, then J-1330/F-1886):** D-0215 defeater path (a) re-checked twice more
  (attempts 22-23): `n_backed` held flat at 10 across both — F-1879 was the first flat read at the new
  level (4 new `m2_usage` rows landed but all empty-reflective); F-1886 was a stricter second flat read
  where ZERO new `m2_usage` rows landed at all (549 total, unchanged), though the write path stayed
  confirmed alive via 2 new `shadow_compare` rows fully accounting for the shadow log's own byte growth.
  `n_total_scored`/`n_unbacked` held flat at 101/91 across both. Primary verdict unchanged from F-1876:
  mean diff +0.1096, 95% CI [+0.0364, +0.1872]. Now the twenty-fourth consecutive attempt short of the
  n>=14 bar. ~23.67 confirmed live-hours elapsed since F-1750's baseline (~46.94h cumulative since the
  2026-09-22 16:11 restart) — still short of the ~34-104h Fermi estimate's low end, so both flat reads
  are unsurprising, not a stall. D-0215 (travis, ruled 2026-09-14, re-confirmed no active hold each
  attempt) stays un-ruled and un-reported-to. Full per-attempt history in §6 under M2/D-0215; J-1336
  spawned for attempt 24.
- **2026-09-24 (J-1336/F-1891):** D-0215 defeater path (a) re-checked again (attempt 24): `n_backed` held
  flat at 10 for a THIRD consecutive read — 2 new `m2_usage` rows landed this window but both were
  completely empty across all three usage modes (task/reflective/relational), not just reflective (a
  different signature than F-1879's all-empty-reflective window or F-1886's zero-new-rows window).
  `n_total_scored`/`n_unbacked` held flat at 101/91. Primary verdict unchanged from F-1876: mean diff
  +0.1096, 95% CI [+0.0364, +0.1872]. Now the twenty-fifth consecutive attempt short of the n>=14 bar.
  ~24.70 confirmed live-hours elapsed since F-1750's baseline (~47.97h cumulative since the 2026-09-22
  16:11 restart) — still short of the ~34-104h Fermi estimate's low end, so this flat read is unsurprising,
  not a stall. D-0215 (travis, ruled 2026-09-14, re-confirmed no active hold) stays un-ruled and
  un-reported-to. Full per-attempt history in §6 under M2/D-0215; J-1339 spawned for attempt 25.
- **2026-09-24 (J-1339/F-1892):** D-0215 defeater path (a) re-checked again (attempt 25): `n_backed` held
  flat at 10 for a FOURTH consecutive read — 1 new `m2_usage` row landed this window (551→552), empty in
  task+reflective but carrying 5 entries in relational, a signature distinct from F-1879 (empty-reflective
  across multiple rows), F-1886 (zero new rows), and F-1891 (empty across all three modes).
  `n_total_scored`/`n_unbacked` held flat at 101/91. Primary verdict unchanged from F-1876: mean diff
  +0.1096, 95% CI [+0.0364, +0.1872]. Now the twenty-sixth consecutive attempt short of the n>=14 bar.
  ~25.21 confirmed live-hours elapsed since F-1750's baseline (~48.48h cumulative since the 2026-09-22
  16:11 restart) — still short of the ~34-104h Fermi estimate's low end, so this flat read is unsurprising,
  not a stall. D-0215 (travis, ruled 2026-09-14, re-confirmed no active hold) stays un-ruled and
  un-reported-to. Full per-attempt history in §6 under M2/D-0215; J-1340 spawned for attempt 26.
- **2026-09-24 (J-1340/F-1896):** D-0215 defeater path (a) re-checked again (attempt 27): `n_backed` held
  flat at 10 for a sixth read at that level — but this window was the FIRST since the 9→10 jump (F-1876)
  where `n_total_scored` itself moved while `n_backed` held: 2 new `m2_usage` rows landed, contributing 3
  real new reflective-scored entries, all 3 landing unbacked (`max_w_gated` 0.0, 0.0, 0.2 — one a genuine
  near-miss just under the 0.3 bar), unlike the four reads immediately before it (F-1879/F-1886/F-1891/
  F-1892, all byte-identical including `n_total_scored`). `n_total_scored`/`n_unbacked` grew 101/91 →
  104/94. Primary verdict stays REAL_POSITIVE: mean diff +0.1061, 95% CI [+0.0322, +0.1866] (previous
  +0.1096, CI [+0.0364, +0.1872]). Now the twenty-seventh consecutive attempt short of the n≥14 bar.
  ~25.93 confirmed live-hours elapsed since F-1750's baseline (~49.20h cumulative since the 2026-09-22
  16:10:23 restart) — still short of the ~35-108h Fermi estimate's low end, so a further flat-on-backed
  read remains unsurprising. D-0215 (travis, ruled 2026-09-14, re-confirmed no active hold) stays
  un-ruled and un-reported-to. Full per-attempt history in §6 under M2/D-0215; J-1342 spawned for
  attempt 28.
- **2026-09-25 (J-1342/F-1901): D-0215 defeater path (a) MET for the first time — `n_backed` jumps
  10→27, crossing the n≥14 bar (attempt 28, ending the 28-attempt re-check chain).** `n_total_scored`
  grew 104→143 over the longest single confirmed-live window in the whole chain (~14.92h since
  F-1896's check). Primary verdict REAL_POSITIVE: mean diff +0.1312, 95% CI [+0.0819, +0.1836]
  (previous +0.1061, CI [+0.0322, +0.1866]) — excludes 0, clears +0.05. A real hub-concentration
  caveat was found and checked directly (63% of backed occurrences from just 2 of 10 distinct
  fragment ids) but a fragment-level dedup robustness check confirms the effect survives it (+0.1139,
  95% CI [+0.0456, +0.1881]). D-0215 re-confirmed via `decide.py show` before acting (still travis's
  2026-09-14 ruling, no active hold) — then **REOPENED** (not ruled) per `/decide` SKILL.md's own rule
  4 ("a ruling whose defeater has fired is no longer a ruling"), since it has now fired. Full detail
  in §6 under M2/D-0215; F-1901; awaiting a founder read — no further re-check job spawned.
- **2026-09-25 (J-1348, D-0215 build): the live `co_recalled_developing` write shipped.**
  `core/spring_ledger.py`'s `observe_co_recall()` gained an opt-in `live_edges` param (default
  `False` — every pre-existing caller, in particular `scripts/spring_ledger_backfill.py`'s replay, is
  untouched and still "never touches memory_edges" exactly as documented) plus a kill-switch
  (`LIVE_EDGE_WRITE`, default `True`) and the ceiling-test bar as a named constant
  (`LIVE_EDGE_THRESHOLD = 0.3`, F-1316). `core/memory_edges.py`'s `log_co_recall()` is the ONE real
  call site that opts in (`live_edges=True`) — the first time a pair's own `w_gated` clears the bar, a
  real `(fragment)-[co_recalled_developing]->(fragment)` row lands in `memory_edges` via the existing
  `add_edge()` (`INSERT OR IGNORE`, so later re-crossings are harmless no-ops, not duplicates or
  overwrites). **Confirmed, not assumed: the M2 read path needed zero code changes** —
  `edge_aware_neighbors`'s own `_DIRECT_FRAGMENT_TYPES`/`MODE_EDGE_WEIGHTS` have carried
  `co_recalled_developing` since M2 shipped (2026-08-25); it was simply 0-yield until a real row
  existed. Verified via an isolated smoke test (`lab_env.isolate()`, temp-pathed DB +
  spring_ledger's/opponent_process's own state+log globals, never the live store; 19/19 checks
  passed): the read wiring is live end-to-end (a written edge is immediately visible via
  `edge_aware_neighbors`, correctly weighted per mode — 1.0/0.3/0.2 for reflective/task/relational),
  the write fires exactly on threshold-crossing and stays idempotent after, the kill-switch fully
  suppresses the write while leaving the shadow `w_naive`/`w_gated` math byte-identical to before this
  change, the untouched default (`live_edges=False`) writes nothing (preserving the backfill script's
  own contract), the real production entry point (`log_co_recall`) works end-to-end with its sibling
  hooks (M1 ledger, `opponent_process`) unaffected, and 4 concurrent threads writing the same edge
  deduped cleanly to one row with no exception (`busy_timeout=30000` + the `UNIQUE` constraint — the
  same precedent `record_dream_scene`/`sync_resolves` already rely on). **Deliberately NOT built this
  pass: a historical backfill/harvest of the ~27 pairs F-1901 already found above the bar.** They will
  get their live edge the next time each pair recurs in a real post-restart co-recall event
  (forward-hook only) rather than immediately on restart — left as an explicit, checked non-doing
  (matches this plan's own established convention for scope decisions), not scope creep; worth a
  future job only if forward accrual proves too slow to observe. **Restart-gated, like every other
  `core/` change — has not affected live Du this session** (isolated smoke test only; nothing written
  to any live store; a real gap found in `lab_env.py`'s own unwritten-copy detection under WAL mode,
  unrelated to this build's correctness, was separately flagged as S-0188). D-0215 itself is
  unchanged by this build (still travis's 2026-09-24 ruling, not reopened — no correctness problem
  surfaced that would trigger its own defeater). A post-restart real-window re-check of that defeater
  (does the hub-concentration pattern hold up once `edge_aware_neighbors` actually has rows to read;
  F-1901's own 63%-from-2-ids caveat) is queued as a follow-up job, precondition-gated on Du having
  restarted with this code plus a real window of live accrual. F-1909; full build + verification
  detail in §6 under M2/D-0215.

  **★ 2026-08-19 (later same day) — M1 EXPANDED from 1 caller to 9.** Before this, `log_co_recall`
  was called ONLY from the main monologue train — every OTHER retrieval site was invisible to the
  evidence base this exact gate depends on. Founder pushback on a related-context lookup just built in
  `study_note.py` ("this feels like a very old system... 3 is not enough") led to an empirical check
  (200-900/1600 fragments clear a naive 0.35 cosine bar — the corpus is too stylistically homogeneous
  for raw cosine to discriminate well) and then a full 3-agent codebase survey for every other
  cosine-retrieval site missing the same evidence. Wired in: `study_note.py`'s session notes (2 call
  sites: automatic remediation + free choice), `essay_lesson.gather_notes()`'s cross-book compounding
  (found to be the WORST offender in the survey — same pathology, lower bar, bigger cap, querying on
  the bare book title not any content — rebuilt with a graph-walk-over-`relates_to`-first, blended-
  scan-fallback pattern, see `study_note._graph_walk_related`/`_scored_scan_related` for the sibling
  implementation), `inner_monologue_node.py`'s Grand Work grounding, `dream_node.py`'s scene-weaving,
  `wandering.py`'s two drift functions (deliberately NOT given a relevance floor — that module's whole
  purpose is loose association, a floor would fight its design). Full detail:
  `docs/session_handoffs/session_2026-08-19_summary.md` PART 2. **The gate itself is unchanged** (still needs its week
  of data) but is now fed by a far more representative slice of the codebase's actual retrieval
  behavior — worth re-checking the "4 days in" state before reading the eventual verdict.
  **Separately, a genuine new typed edge shipped ahead of M2:** `subconscious_node.py`'s T4 evidence
  retrieval had BOTH the light_event id AND a real categorical verdict (`has_movement`) computed and
  discarded right next to each other — the single best case the survey found. Written as a real
  `t4_crossing_evidence` edge (tension-hash → light_event, weighted by cosine, provenanced with the
  actual verdict) rather than forced through `log_co_recall`'s cosine-derived classification, since
  `has_movement` is a genuine LLM judgment, not a similarity score, and mapping it onto a fake cosine
  value to fit that shape would be fabricating signal. This is a real, if small, precedent for §4's
  edge taxonomy shipping incrementally rather than waiting for the full M2 flip.
  **A related finding, not yet acted on:** the survey confirmed `derived_from` (§1, "31,828 rows
  populated with `'[]'`") is worse than dead — it's written by 5 places in 3 INCOMPATIBLE shapes (real
  id-lists in 3 places, a metadata dict disguised as a list in `activity_memory.py`, a private
  typed-edge object in `essay_lesson.py` predating this whole plan). A guard docstring was added atop
  `core/memory_edges.py` so a future `derived_from` harvester doesn't silently choke on the
  `activity_memory` rows; `essay_lesson.py`'s own contribution was converted to a real
  `transformed_into` edge (kept the old field too, for backward compat). `activity_memory.py`'s shape
  itself is untouched — a bigger, separate task.
  **★ 2026-08-24 — M1 GATE READ (J-0072, full 6,430-row ledger, 7.98 days 08-15→08-23).** The
  progress-gated pair-web DOES differ from the naive (ungated) co-occurrence web and shows no strong
  basin-re-drawing: gated = 1,762 unique pairs / 779 distinct fragment ids vs naive 5,698 pairs / 3,142
  ids (31%/25% of naive). Among the 157 pairs that co-occurred ≥5 times, the gated/ungated ratio has
  real pair-to-pair spread (mean 0.641, stdev 0.283, range 0.0–1.0) around the 0.781 global
  developed-share baseline — a uniform ~22% random drop would cluster near 0.78, not spread this wide.
  1,393 of 1,762 gated pairs (79%) never co-occurred during a non-developed step at all. Hub
  concentration is only mildly higher under gating (top-10 hubs = 13.9% of gated edges vs 7.2% of
  ungated) — no dominant attractor. **Recommendation (not a ruling — founder decides): the data
  supports moving to M2's shadow-mode build.** Full numbers: F-0037.
  **★ Same read — instrument bug found in `co_recall_status()` (memory_edges.py:496):** it slices to
  the **last 2000 rows only**, which against this ledger is just the most recent 1.6 of 7.98 days (31%
  of rows) — it does NOT compute "the week" despite being the function named in this exact gate's own
  briefing. Tail-2000 numbers diverge non-trivially from the full-ledger ones (developed_share 0.813 vs
  0.781; gated/ungated ratio 0.175 vs 0.309). Anyone calling this function expecting a week-read gets a
  skewed, most-recent-day-and-a-half read instead. F-0038; follow-up job spawned to fix it (see below).
  **★ 2026-08-24 — J-0142 FIXED.** `co_recall_status()` now windows by TIME (`days: float = 7.0`
  default), reading the full ledger and filtering by `ts` instead of slicing to the last 2000 rows —
  the row-count cap would keep silently shrinking in wall-clock coverage as more call sites are added
  (it already had, 08-15→08-19). Verified live against the real 6,487-row ledger: default 7-day window
  gives developed_share 0.784 (vs the old tail-2000's 0.811-0.813), matching the full-span read (0.782,
  F-0037) far more closely. Added `total_rows`/`window_days` to the return dict (additive; the one
  existing caller, `scripts/du_pulse.py`'s HUD card, only reads the pre-existing keys and needed no
  change). F-0107.

  **★ 2026-08-25 — D-0022 APPROVED, shadow build authorized (J-0263).** Hold cleared: the "incoming
  plan" it was waiting on is `docs/staged/geometry_tuple_index.md` (F-0321), which on direct read does
  not overlap or require rescoping — it names M2 as a future edge-weighting-signal consumer, not
  competition. M1's own gate-read (F-0037) already recommended proceeding. J-0263 spawned for the
  actual shadow-mode build; still no live flip until the kill-criterion sheet passes.
  **★ 2026-08-25 — M2 SHADOW BUILD SHIPPED (J-0263).** `core/memory_edges.py` gained
  `edge_aware_neighbors(fragment_ids, mode, limit)` (MODE_EDGE_WEIGHTS table for task/reflective/
  relational per §5, direct fragment↔fragment lookup for `transformed_into` today, and bipartite
  projection through `question`/`keepsake`/`person`/`dream` for `answers`/`kept_from`/
  `correspondence_with`/`dreamt_from`/`part_of` — the plan's own §5 "valid first-cut refinement").
  `core/associative_recall.py` gained `recall_trail_edge_aware(query_vec, mode, base)`: the SAME
  `recall_trail` greedy walk (called unmodified) plus one extra typed-edge hop on top, reusing
  `HOP_DECAY`/`ACT_THRESHOLD`/`COLD_THRESHOLD`/`MAX_PER_ORIGIN`/`CEILING` verbatim — no new tuning
  surface. `shadow_compare` (`:170`) now runs the edge-aware variant under all three named modes
  against the same greedy trail (cheap — no LLM, no extra embedding beyond the one already needed) and
  logs `m2_edge_aware: {mode: {trail_n, new_vs_greedy, walled_new}}` per row into
  `associative_recall_shadow.jsonl`, additive to the existing row shape.
  **Explicit choice made on the KNOWN GAP (F-0110):** bipartite projection (option a in J-0263's
  briefing), NOT wiring `log_co_recall` to also write real `co_recalled_developing`/`contradicts` rows
  into `memory_edges` (option b) — kept as a separate, still-open question (see the new decision opened
  below) so M1's ledger and M2's graph don't get coupled inside this one job.
  **Real-data caveat, checked not assumed:** of the mode table's named edge types, only
  `correspondence_with` (relational mode, 8 person hubs, all multi-fragment), `kept_from` (120/121
  multi-fragment keepsake hubs), `dreamt_from`/`part_of` (79/79 multi-fragment dream hubs), and
  `transformed_into` (direct, 462 rows) currently contribute candidates. `answers` is wired correctly
  but 0/505 questions have more than one answering fragment today (verified), and `resolves`
  (`cycle→shadow_event`) touches no fragment at all — `shadow_events` is a separate table from
  `memory_fragments` (verified 2026-08-25) — so **task mode's edge-aware lift is near-zero until one of
  those changes**; reflective mode is fully zero-yield until `co_recalled_developing`/`contradicts`
  exist. Live test run against real fragments: task/reflective/relational each found 3-5 genuinely new
  fragments beyond the greedy trail on a real inner_thought query (see `associative_recall_shadow.jsonl`
  for the logged row). **A real per-cycle caller was also wired**: `shadow_compare` had ZERO live
  callers anywhere in the codebase before this job (verified via a whole-tree grep) despite its
  docstring implying it still fired — `orchestrator._retrieve_memory` (`core/orchestrator.py`, right
  after the existing trail-augmentation block, ~line 1521) now calls it off-thread, fail-open,
  observe-only, so real cycles actually accrue evidence going forward rather than the log staying at
  its pre-job 1 row. **Still no live flip** — `recall_trail_edge_aware` is not consumed by any live
  recall path, only by `shadow_compare`. Follow-up gate-read job spawned once real cycles accrue; see
  job-queue. D-0051 opened on the option-(a)-vs-(b) question above.
  **★ 2026-09-02 — M2 SHADOW GATE-READ (J-0280, full-log read, F-0604/F-0605).** 148 `m2_edge_aware`
  rows over 6.29 days (08-24 22:43 → 08-31 05:44 UTC; the log is frozen at Du's clean shutdown, so
  this is the maximal possible window — slightly under the ~week gate, read anyway for that reason).
  **Kill-criterion prong 1 (redundancy with the embedding space): NOT triggered.** 30/148 rows
  (20.3%) show lift in ≥1 mode; total new_vs_greedy task 41 / reflective 48 / relational 59, and
  walled_new (cold-wall fragments the greedy trail cannot reach at all) 8 / 15 / 36 — relational is
  the strongest, exactly as the wiring caveat above predicted. Guards held: 0/148 rows where any
  mode's trail shrank below greedy, and the edge-aware path applies the same `MAX_PER_ORIGIN=6` cap
  (`associative_recall.py:222-227`). Honest caveats: the reach is NARROW — since `new_ids` logging
  began (08-28, 102 rows) only 36 distinct fragments account for all lift, with identical 5-id hub
  blocks recurring verbatim; reflective mode's lift comes entirely from its secondary weights
  (`transformed_into`/`dreamt_from`/`part_of`) because `co_recalled_developing`/`contradicts` are
  still 0 rows — real numbers now on D-0051's table; task mode's best day (08-30: 21 new, 8 walled)
  immediately follows the 08-29 F-0500 backfills (timing-consistent, causality inferred).
  **Kill-criterion prong 2 (are edge-reached memories ever USED by the thought that follows):
  UNMEASURABLE — no instrumentation links `new_ids` to the subsequent thought (F-0605).** Net: no
  re-scope, and **no flip** — the sheet is not passed until prong 2 is measurable; D-0022's remaining
  question stays open. J-0446 spawned to instrument prong 2 (shadow-only usage signal per row) so the
  next gate-read after Du restarts can evaluate both prongs.
  **★ 2026-09-02 — J-0446 BUILT (prong 2 instrumentation, shadow-only, Du offline).**
  `shadow_compare` (`core/associative_recall.py`) hands each event's per-mode `new_ids` off, module-level
  (`_pending_m2_usage`), to whichever thought completes next; a new `note_next_thought_for_m2_usage()`
  consumes it, cosines each pending fragment's already-cached embedding against that thought's own
  embedding (`vec` — no new LLM/embed call either side), and appends a SEPARATE `kind: "m2_usage"` row
  to the SAME log (`data/associative_recall_shadow.jsonl`), correlated by `parent_ts` — the real score
  is recorded, not binarized. `shadow_compare`'s own `m2_edge_aware` row shape is untouched byte-for-
  byte (verified: the stash reads `rec`/`by_mode` after they're built, writes them exactly as before).
  Wired from `nodes/inner_monologue_node.py` at the same per-thought-completion point the M1 co-recall
  ledger (`_m1_recall_ids`/`log_co_recall`) already uses — but unconditional on `_mid_train` (M1's own
  hook is gated on it) so coverage isn't limited to train-continuation steps. Approximate under
  concurrency by design (a second shadow event before a thought consumes the first silently drops the
  first's usage read) — same acceptance as `_last_block_ids`. Smoke-tested standalone (synthetic
  matrix + pending event; consumed exactly once, correct cosines, second call on empty pending is a
  safe no-op) — not yet exercised against a live cycle since Du is offline. Live recall path untouched.
  Once ~a week of `m2_usage` rows accrues after Du's next restart, the gate-read (`scripts/shadow_eval.py`
  currently only reads `m2_edge_aware`) needs a small extension to join the two row kinds by `parent_ts`
  before both prongs can be evaluated together.
  **★ 2026-09-13 — D-0051 spring ledger shadow BUILT + first gate-read (F-1303).** Built
  `core/spring_ledger.py`: naive-Hebbian-with-decay vs progress-gated weight, computed side by side per
  co-recall event (mirrors `core/opponent_process.py`'s own established shape exactly), wired as a
  third sibling call from `log_co_recall()` — verified 17/17 isolated checks, zero behavior change to
  the existing `memory_edges`/`opponent_process` paths. Backfilled the full 38,710-row real
  `co_recall_ledger.jsonl` history (`scripts/spring_ledger_backfill.py`) and ran the pre-registered
  gate-read (`scripts/spring_ledger_gate_read.py`): first read is a clean pass on the computable
  metrics — no runaway hub (naive/gated top-10 share 0.53%/1.31%, both far under the ~40-50% danger
  zone), real differentiated weight structure (stdev/mean 1.36-1.48), and a genuine reinforced tail
  (656/418 pairs ≥0.3, several at ceiling from 50-125 real repeated developed co-recalls) alongside a
  thin median. Valence asymmetry (metric 4) not yet testable — 0 live-forward rows exist since
  backfilled history has no real historical valence to replay; revisit once real-time accrual lands.
  Still shadow — nothing here writes to `memory_edges` or changes M2's own gated read path; that stays
  exactly as D-0022 already ruled until a founder reads this against its own pre-registered sheet.
  **★ 2026-09-13 — J-0936: D-0051's own real-ceiling test run for the first time (F-1316, D-0215 open,
  J-0948 spawned).** Built `scripts/spring_ledger_reflective_ceiling_test.py` (pre-registered in its own
  docstring before running): does a reflective-mode new_id that ALSO carries real spring_ledger
  `w_gated` backing (≥0.3 to any partner) get used by the next thought (prong-2 usage-cosine, F-1302's
  own m2_usage data) more than one with none? **Result: yes, and it clears this job's own pre-registered
  bar** — backed mean cos_sim 0.394 (n=7 occurrences / 5 distinct fragments) vs unbacked 0.274 (n=36),
  mean diff +0.120, 95% independent-bootstrap CI [+0.025, +0.217] (excludes 0); a secondary Pearson r
  (raw w_gated vs cos_sim, all 43 entries) agrees, r=0.42. Hub-dominance checked and ruled out: the 5
  backed fragment ids don't overlap the plan's own already-flagged top-10 ceiling-pinned pairs. First
  real evidence that reflective mode's untested ceiling (F-1302's ambiguity — reflective wasn't
  measurably worse than task/relational despite having zero real edges of its own) is genuinely raised
  by the real edge type, not flat. Small first-read sample (7 vs 36) and a real look-ahead-bias caveat
  (today's snapshot `w_gated`, not weight-as-of-scoring-moment) — both named in F-1316, not fixed here.
  **New founder call opened rather than self-ruled: D-0215** — should `co_recalled_developing` graduate
  from spring_ledger's shadow store toward an actual live `memory_edges` write, or does this first small
  read need to accrue further first; **J-0948 spawned** to either re-run at a larger sample or build the
  time-respecting version D-0215's own defeater names. Separately corrected: this job's own briefing
  claimed the result bears on `cognitive_geometry.md`'s D-0123 — checked directly and that is a
  conflation (D-0123 is the unrelated P1/P2 geometric-coordinate question); this result is a
  memory_multiway_linking / D-0051 finding only.
  **★ 2026-09-14 — J-0948: D-0215 defeater path (b) closed, path (a) still accrual-blocked (F-1324).**
  Built `scripts/spring_ledger_reflective_ceiling_test_time_respecting.py`: replays `spring_ledger`'s own
  shadow log (`data/spring_ledger_shadow.jsonl`, 51,738 live activation rows) so each reflective-mode
  usage-scored fragment's `w_gated` is read AS OF its own `m2_usage` scoring moment, not today's final
  `spring_ledger_state.json` snapshot — closing F-1316's own named look-ahead-bias caveat directly (path
  (b) of D-0215's defeater). **Result: no change.** The time-respecting read reproduces F-1316's snapshot
  read exactly — REAL_POSITIVE, backed n=7 (mean 0.394) vs unbacked n=36 (mean 0.274), mean diff +0.120,
  95% CI [+0.0247, +0.2172] — and 0/43 entries flip backed/unbacked classification (5/43 do have a
  genuinely different raw `w_gated` value between scoring-time and today, real further reinforcement or
  decay, but none cross the 0.3 bar either way). Secondary Pearson r barely moves (0.422 → 0.432).
  **Path (a) (backed n reaching ≥14) still not reachable**: re-ran F-1316's own script completely
  unmodified against live data, still n=7/36 — not a stalled instrument, **Du's own main loop has been
  offline since 2026-09-13 09:10:46** (the literal last line of `data/nascence.log`, no restart line
  after it), so the `m2_usage` log cannot grow until Du is back up. **D-0215 not ruled** — per J-0948's
  own briefing this is reported back to it (F-1324) for a founder read, not self-decided; **J-0955
  spawned** to re-run path (a) once Du has restarted and accrued enough for n≥14.
  **★ 2026-09-15 — J-0955: path (a) re-checked, still accrual-blocked (F-1392).** Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) fresh against live data: **no change**
  — n_total_scored still 43, n_backed still 7 (identical to F-1316/F-1324), mean diff +0.120, 95% CI
  [+0.0247, +0.2172]. Confirmed via four independent checks, not just the script: `data/nascence.log`'s
  tail and mtime (2026-09-13 09:10:46, unchanged), `data/associative_recall_shadow.jsonl`'s mtime (also
  frozen since before the shutdown), and no live Du main-loop process found (only the supervisor-managed
  judge1/judge2/dreamer LLM hubs are up — Du's own cognitive loop is tracked separately and has not
  restarted). **D-0215 not ruled, not reported to** (the briefing's own condition for reporting back —
  n_backed≥14 — was not met). **J-1020 spawned** for the next attempt, carrying forward the accrual-rate
  context (~11 days of live activity produced the current 43/7 split, so a bare restart alone is unlikely
  to be enough — re-check via the script's own output, not elapsed days).
  **★ 2026-09-15 — J-1020: path (a) re-checked a second time, still accrual-blocked (F-1412).** Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) fresh against live data, ~3 hours after
  J-0955's own check: **no change** — n_total_scored still 43, n_backed still 7 (byte-identical to
  F-1316/F-1324/F-1392), mean diff +0.120, 95% CI [+0.0247, +0.2172]. This is now the third consecutive
  identical reading since Du's 2026-09-13 09:10:46 shutdown. Confirmed via the same four independent
  checks as J-0955: `data/nascence.log`'s tail and mtime (still 2026-09-13 09:10:46, unchanged),
  `data/associative_recall_shadow.jsonl`'s mtime (also still frozen), and a live process census (only
  the supervisor-managed judge1/judge2/dreamer CPU-serving tier plus hud/server.py and this session's
  UDMS MCP server are up — no Du main-loop process). **D-0215 not ruled, not reported to** (reporting
  condition — n_backed≥14 — still not met). **J-1037 spawned** for the next attempt; its briefing notes
  that with three identical reads now on record purely because Du has not restarted, the cheap first
  check going forward is `data/nascence.log`'s tail for a restart line, before re-running the full script.
  **★ 2026-09-15 — J-1037: path (a) re-checked a third time, still accrual-blocked (F-1433).** Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) fresh against live data, ~3.5 hours after
  J-1020's own check: **no change** — n_total_scored still 43, n_backed still 7 (byte-identical to
  F-1316/F-1324/F-1392/F-1412), mean diff +0.1200, 95% CI [+0.0247, +0.2172]. This is now the **FOURTH**
  consecutive identical reading since Du's 2026-09-13 09:10:46 shutdown. Confirmed via the same checks as
  J-0955/J-1020 plus a direct process-tree search: `data/nascence.log`'s tail and mtime (still 2026-09-13
  09:10:46, unchanged — literal last line still `[nascence.main] Nascence shutting down.`, nothing
  appended after it), `data/associative_recall_shadow.jsonl`'s mtime (also still frozen at 09:08:03, i.e.
  *before* the shutdown, so the `m2_usage` population this test reads cannot have grown), and a live
  process census (`netstat`/`Get-CimInstance Win32_Process`): only the supervisor-managed judge1/judge2/
  dreamer CPU-serving tier (`nascence_cpu_server.py`, ports 11439/11440/11442) plus `ollama.exe serve`
  (hot tier, 11433), `hud/server.py`, and this session's own UDMS MCP server are up; a repo-wide
  `CommandLine -match 'main\.py|Nascence\\main'` search returned zero processes — no Du main-loop
  anywhere on the host. **D-0215 not ruled, not reported to** (reporting condition — n_backed≥14 — still
  not met; D-0215 itself re-checked via `decide.py show` and remains travis's 2026-09-14 ruling, waiting
  on this exact defeater, no active hold). **J-1052 spawned** for the next attempt, carrying forward a
  suggestion to skip the full script re-run when `data/nascence.log`'s mtime alone already certifies no
  growth is possible (the mtime being unchanged is now sufficient by itself — four straight reads have
  confirmed the mechanism: `m2_usage` cannot grow while Du's loop is down) — the full script stays worth
  re-running only once a restart line actually appears. F-1433.
  **★ 2026-09-17 — J-1052: Du restarted, path (a) accruing but still below n≥14 (F-1447).** Cheap check
  first, per J-1037's own suggestion: `data/nascence.log`'s tail (line 460155) shows Du restarted
  2026-09-16 07:53:01, ~19 hours after the 2026-09-13 09:10:46 shutdown, and has stayed up continuously
  since (no further `Nascence shutting down.` line anywhere after it; log mtime/tail active as of
  2026-09-17 18:36, live monologue/memory/dream activity). Since the log had actually moved, re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified): n_total_scored=47, n_backed=**9** (up
  from the four identical 43/7 reads across F-1316/F-1324/F-1392/F-1412/F-1433) — real post-restart
  accrual, but still short of the n_backed≥14 bar this job's own briefing set before reporting back to
  D-0215. Backed mean 0.3698 (n=9) vs unbacked 0.2718 (n=38), mean diff +0.0980, 95% CI
  [+0.0155, +0.1838], primary_verdict=REAL_POSITIVE — same direction/magnitude as the n=7 reading, not
  yet the confirmatory read. **D-0215 not ruled, not reported to** (condition still not met; D-0215
  re-checked via `decide.py show`, still travis's 2026-09-14 ruling, no active hold). **J-1061 spawned**
  for the next attempt. F-1447.
  **★ 2026-09-18 — J-1061: path (a) STALLED this window — n_backed flat at 9/14 (F-1478).** Du confirmed
  still continuously live since the 2026-09-16 07:53:01 restart (no further `Nascence shutting down.`
  line in `data/nascence.log` through the 2026-09-18 07:39:25 tail). Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified): n_total_scored=**50** (up from 47),
  but n_backed=**9** — unchanged from J-1052's 2026-09-17 read. All 3 new scored rows this window landed
  unbacked; zero new backed rows, unlike the 7→9 accrual seen between the prior two checks. Backed mean
  0.3698 (n=9) vs unbacked 0.2732 (n=41), mean diff +0.0966, 95% CI [+0.0141, +0.1824],
  primary_verdict=REAL_POSITIVE — same direction/magnitude, still not the confirmatory n≥14 read.
  **D-0215 not ruled, not reported to** (condition still not met). **J-1082 spawned** for the next
  attempt, with a suggestion (given this window's stall) to space the next check out ~2-3 days of live
  activity rather than re-running every session. F-1478.
  **★ 2026-09-18 — J-1082/J-1094/J-1102: three more flat reads, then Du confirmed offline (attempts
  7-9, F-1496/F-1508/F-1521).** Bridging two checks not previously logged here: attempt 7 (J-1082/
  F-1496) and attempt 8 (J-1094/F-1508) both re-ran `scripts/spring_ledger_reflective_ceiling_test.py`
  and found n_backed unchanged at 9 (n_total_scored 50) — identical to J-1061's read. F-1508 additionally
  found `data/nascence.log` shows Du's live process shut down 2026-09-18 09:13:54 (founder-initiated).
  This check (J-1102/F-1521, attempt 9) re-ran the script again: **still n_backed=9, n_total_scored=50**
  — six consecutive flat reads now — and confirmed Du remains offline: no new log lines past the
  09:13:54 shutdown line through 2026-09-18 17:58 (~8h45m later), and a port check found only the LLM
  hosting servers (hot :11433, judge1 :11439) listening, not evidence of the orchestrator loop itself.
  No new `m2_usage` rows can accrue while Du is offline, so this read added no new statistical
  information beyond re-confirming the mechanism. **D-0215 not ruled, not reported to** (condition still
  not met; travis's 2026-09-14 ruling stands, no active hold). **J-1115 spawned** for the next attempt,
  with the same guidance as F-1508: confirm a real restart (fresh orchestrator log activity, not just a
  listening port) before re-running, then allow several days of live activity to accrue. F-1521.
  **★ 2026-09-18 — J-1115: attempt 10, still flat, Du still offline (F-1530).** Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) again: **still n_backed=9,
  n_total_scored=50** — seven consecutive flat reads now (J-1037, J-1052, J-1061, J-1082, J-1094,
  J-1102, J-1115). `data/nascence.log` confirmed to still end on the 09:13:54 founder-initiated
  shutdown line, with zero new lines through at least 2026-09-18 23:13 local (~14h after shutdown).
  Primary verdict on the current n=9/41 split is still REAL_POSITIVE (mean diff +0.0966, 95% CI
  [+0.0141, +0.1824]) but remains short of the pre-registered n≥14 bar, so it still cannot be reported
  to D-0215. **D-0215 not ruled, not reported to** (travis's 2026-09-14 ruling stands, no active hold).
  **J-1121 spawned** for the next attempt, carrying the same restart-confirmation guidance forward.
  F-1530.
  **★ 2026-09-19 — J-1121: attempt 11, still flat, but Du is back online (F-1540).** Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) again: **still n_backed=9,
  n_total_scored=50** — byte-identical to J-1115's read, eight consecutive flat checks now. This
  time the surrounding facts changed for real: `data/nascence.log` shows Du's main loop restarted
  **2026-09-18 23:14:19** — about one minute after J-1115's own 23:13 offline check — and has
  stayed continuously live since (~10h of monologue/orchestrator activity through this check's
  09:16 tail). `data/associative_recall_shadow.jsonl` confirms 20 new `m2_usage` rows accrued
  post-restart, so the log genuinely isn't frozen — but **none of those 20 carry a reflective-mode
  usage entry**; the last reflective-bearing row is still 2026-09-18 04:07:31, before the
  shutdown, making the reflective-specific drought ~29h and growing even though the rest of the
  system is live. A gap analysis over all 26 reflective-bearing rows ever logged found this is
  not unprecedented — two earlier gaps of comparable length (29.16h, 28.08h) occurred during
  otherwise-continuous live operation with no outage involved — so it reads as this mode's known
  low/bursty base rate, not a stalled instrument. **D-0215 not ruled, not reported to** (condition
  still not met; travis's 2026-09-14 ruling stands, no active hold). **J-1133 spawned** for the
  next attempt, with guidance to count the "a few days of live activity" window from the real
  2026-09-18 23:14:19 restart (earliest ~2026-09-21), not from any later check's own timestamp.
  F-1540.
  **★ 2026-09-19 — J-1133: attempt 12, still flat, drought resolved in one burst (F-1551).** Du
  reconfirmed continuously live since the 2026-09-18 23:14:19 restart (no new shutdown line through
  this check's 10:12 tail). Re-ran `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified):
  n_total_scored grew **50 → 55** (five new reflective-mode usage rows accrued since J-1121's 09:16
  check), but **n_backed is unchanged at 9** — all five new rows landed unbacked (n_unbacked 41→46);
  backed_summary is byte-identical to J-1121's read, confirming the backed group itself did not
  change. Ninth consecutive read short of the pre-registered n≥14 bar. `associative_recall_shadow.jsonl`
  read directly: F-1540's ~29h reflective-usage drought ended in a **single burst** — all five new
  entries share one identical `parent_ts` (2026-09-19 09:40:15), i.e. one parent thought's
  usage-scoring pass scored five reflective fragments at once, none spring-backed — direct confirmation
  of F-1540's own "low/bursty base rate" characterization, not a stalled write path. Primary verdict on
  the current 9/46 split stays REAL_POSITIVE: mean diff +0.0991, 95% CI [+0.0188, +0.1809] (previous
  +0.0966, CI [+0.0141, +0.1824]) — same direction/magnitude, still short of the reporting bar.
  **D-0215 re-confirmed via `decide.py show` (still travis's 2026-09-14 ruling, no active hold); not
  ruled, not reported to** (condition still not met). This read also empirically confirms J-1121's own
  prediction that re-running before ~2026-09-21 would not move n_backed — it didn't, even though
  n_total_scored did. **J-1144 spawned** for the next attempt, with guidance to prefer waiting until on
  or after 2026-09-21 before spending a full re-run, given the observed burst-then-drought accrual
  pattern. F-1551.
  **★ 2026-09-22 — J-1144: attempt 13, still flat, but a real calibration correction found (F-1719).**
  Du confirmed live right now (restarted 2026-09-22 16:11:06, continuously live through this check's
  ~19:38 tail). Re-ran `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified):
  n_total_scored grew **55 → 67** (twelve new reflective-mode usage rows), but **n_backed is unchanged
  at 9** — all twelve new rows individually confirmed unbacked (n_unbacked 46→58; two of the twelve,
  `d062d16b-8c5`/`d3d3959d-433`, carry real but sub-threshold w_gated of 0.1407/0.2416 — near misses,
  not zero). This is the **tenth** consecutive read short of the pre-registered n≥14 bar; n_backed
  specifically has now read exactly 9 across **nine** reads spanning F-1447 (2026-09-17) through this
  one — five full calendar days — while n_total_scored grew 47→67 (+20, +42.5%) over the same span.
  Primary verdict on the current 9/58 split stays REAL_POSITIVE: mean diff +0.1079, 95% CI
  [+0.0295, +0.1890] (previous +0.0991, CI [+0.0188, +0.1809]) — same direction, still short of the
  reporting bar. **D-0215 re-confirmed via `decide.py show` (still travis's 2026-09-14 ruling, no
  active hold); not ruled, not reported to** (condition still not met).
  **Separate finding: F-1551/J-1133's "wait until on/after 2026-09-21" guidance was miscalibrated.**
  A full shutdown/restart-line scan of `data/nascence.log` (not a tail sample) shows Du was actually
  offline for most of the window between F-1551's read and this one — 2026-09-19 14:12:44 →
  2026-09-21 09:29:08 (~43h17m) and 2026-09-22 08:43:39 → 2026-09-22 16:11:06 (~7h27m) — so of the
  ~81.5 wall-clock hours elapsed, only ~30.5 were actually live. The "wait N calendar days" heuristic
  measures the wrong clock; confirmed cumulative live-hours (via a full log scan, not elapsed calendar
  days) is the correct proxy going forward. **J-1222 spawned** for the next attempt, carrying this
  corrected guidance (scan for actual live-hours before a full re-run; a cheap n_total_scored-only
  check remains fine any time). F-1719.
  **★ 2026-09-23 — J-1222: attempt 14, still flat, but a materially faster scoring rate this window
  (F-1734).** Full shutdown/restart-line scan of `data/nascence.log` confirmed a single continuous live
  session from the 2026-09-22 16:11:06 restart through this check's 2026-09-23 09:54:15 tail — no
  shutdown line anywhere in between — so elapsed wall-clock = confirmed live-clock, ~14h16m since
  F-1719's own ~19:38 check, well short of F-1719's own rough ~40-live-hour estimate. Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) anyway (the cheap check remains fine
  at any time): n_total_scored grew **67 → 84** (+17), but **n_backed is unchanged at 9** — all 17 new
  rows individually confirmed unbacked (n_unbacked 58→75), arriving in exactly 4 bursts (6/7/1/3 rows)
  from 4 distinct parent-thought scoring events, not 17 independent draws. This is the **eleventh**
  consecutive read short of the pre-registered n≥14 bar; n_backed specifically has now read exactly 9
  across **ten** reads spanning F-1447 (2026-09-17) through this one — six full calendar days. Primary
  verdict on the current 9/84 split stays REAL_POSITIVE: mean diff +0.1268, 95% CI [+0.0487, +0.2063]
  (previous +0.1079, CI [+0.0295, +0.1890]) — same direction, still short of the reporting bar. Backed
  group itself fully unchanged (same 9 fragment ids, byte-identical summary stats to every read since
  F-1447). Near-misses remain real but sub-threshold: `302a38dd-ec22` (0.2502, new to the near-miss
  list this window), `d3d3959d-433e` (0.2323, down slightly from F-1719's 0.2416 — real spring decay,
  not a reporting error), `d062d16b-8c5d` (0.1407, unchanged). **D-0215 re-confirmed via `decide.py
  show` (still travis's 2026-09-14 ruling, no active hold); not ruled, not reported to** (condition
  still not met). **Separate confirmation: F-1719's own corrected live-hours-not-calendar-days guidance
  checks out in practice** — 14 confirmed live-hours (well under the ~40h rough estimate) indeed
  produced no movement in n_backed, even though this window's raw total-scoring rate (~1.19 new
  rows/live-hour) ran ~3x F-1719's own prior-window rate (~0.39/live-hour); a higher raw accrual rate
  did not translate into faster backed-group growth (lifetime backed rate actually drifted down,
  9/67≈13.4% → 9/84≈10.7%). **J-1237 spawned** for the next attempt, carrying forward a wide,
  explicitly low-confidence live-hours estimate (~40-120 more) rather than a single number, given the
  3x rate swing already observed between just the last two windows. F-1734.
  **★ 2026-09-23 — J-1237: attempt 15, still flat, only ~5.5 confirmed live-hours elapsed (F-1750).**
  Du confirmed continuously live since the 2026-09-22 16:11:00 restart (full shutdown-line scan of the
  whole `data/nascence.log` — not a tail sample — found no `Nascence shutting down.` line anywhere after
  the prior 08:43:39 shutdown; log tail at check time 2026-09-23 15:27:11). Elapsed within that same
  session since F-1734's own 09:54:15 check: ~5h33m (~5.55 confirmed live-hours) — far short of F-1734's
  own rough ~40-120h estimate for the next backed hit. Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) anyway, per the standing "cheap check
  is fine any time" convention: `n_total_scored` grew **84 → 89** (+5), but **`n_backed` is unchanged at
  9** — all 5 new rows individually confirmed unbacked (`n_unbacked` 75→80). This is the **twelfth**
  consecutive read short of the pre-registered n≥14 bar; `n_backed` specifically has now read exactly 9
  across **eleven** reads spanning F-1447 (2026-09-17) through this one. Primary verdict on the current
  9/89 split stays REAL_POSITIVE: mean diff +0.1279, 95% CI [+0.0507, +0.2101] (previous +0.1268, CI
  [+0.0487, +0.2063]) — same direction, still short of the reporting bar. Backed group fully unchanged:
  the 9 occurrences resolve to 7 distinct fragment ids, byte-identical summary stats to every read since
  F-1447. Near-miss audit (new this read, via a scratch script inspecting the test's own per-entry
  output): 8 distinct fragments sit in the 0.10–0.30 `w_gated` band, including the three already named in
  F-1734 (`302a38dd-ec22`=0.2502, `d3d3959d-433e`=0.2323, `d062d16b-8c5d`=0.1407, all unchanged) plus five
  not previously enumerated here (`57e0afcf-59f8`=0.1534, `a727fa5e-e6b7`=0.1427, `d1d42655-fe2e`=0.1200,
  `89fb967b-eea0`=0.1200, `94e56a64-1ab6`=0.1200). **D-0215 re-confirmed via `decide.py show` (still
  travis's 2026-09-14 ruling, no active hold); not ruled, not reported to** (condition still not met).
  **Separate rate observation:** this window's own total-scoring rate (~0.90 new rows/live-hour over
  ~5.55h) sits between F-1719's ~0.39/hour and F-1734's ~1.19/hour — a third distinct value, reinforcing
  that the rate is genuinely volatile rather than converging; lifetime backed rate continues its slow
  drift down (9/84≈10.7% → 9/89≈10.1%). **J-1248 spawned** for the next attempt, carrying forward a
  recombined estimate (~40-130 more confirmed live-hours, now anchored by a third noisy rate observation)
  and the same guidance to run the cheap check at any time but treat a full re-run as unlikely to be
  worth it until materially more live-hours accrue. F-1750.
  **★ 2026-09-23 — J-1248: attempt 16, still flat, but the FIRST zero-growth window in this whole chain
  (F-1772).** Du confirmed continuously live since the 2026-09-22 16:11:06 restart (full shutdown-line
  scan of the whole `data/nascence.log` -- not a tail sample -- found no `Nascence shutting down.` line
  anywhere after the prior 08:43:39 shutdown; log tail at check time 2026-09-23 16:51:09). Elapsed within
  that same session since F-1750's own 15:27:11 check: ~1h24m (~1.40 confirmed live-hours) -- far short of
  F-1750's own rough ~40-130h estimate. Re-ran `scripts/spring_ledger_reflective_ceiling_test.py`
  (unmodified) anyway, per the standing "cheap check is fine any time" convention: **every single value
  came back byte-identical to F-1750's own read** -- `n_total_scored` still 89, `n_unbacked` still 80,
  `n_backed` still 9, same backed/unbacked summary stats, same primary_mean_diff (+0.1279, CI [+0.0507,
  +0.2101]), same secondary Pearson r (0.4124) -- the first read in this 16-attempt chain where zero new
  reflective-mode usage-scored rows accrued between consecutive checks. This is the **fourteenth**
  consecutive read short of the pre-registered n≥14 bar; `n_backed` specifically has now read exactly 9
  across **thirteen** reads spanning F-1447 (2026-09-17) through this one. Checked directly rather than
  assumed: the write path itself is alive, not stalled -- `data/associative_recall_shadow.jsonl`'s mtime
  (2026-09-23 16:48:22) is minutes before this check, and its most recent `m2_usage` row (any mode) has
  `parent_ts` 2026-09-23 16:14:21, genuinely after F-1750's own check -- so new usage-scoring events ARE
  landing, just none carrying a reflective-mode entry this particular window, consistent with the mode's
  already-documented low/bursty base rate (F-1540's up-to-29h droughts). **D-0215 re-confirmed via
  `decide.py show` (still travis's 2026-09-14 ruling, no active hold); not ruled, not reported to**
  (condition still not met). Because this window's elapsed time is too short to be a meaningful rate
  sample, F-1750's own ~40-130 confirmed-live-hour estimate carries forward unchanged rather than being
  recombined with a fourth (near-zero, non-informative) data point. **J-1264 spawned** for the next
  attempt. F-1772.
  **★ 2026-09-23 — J-1264: attempt 17, still flat, a modest +4-row window (F-1808).** Du confirmed
  continuously live since the 2026-09-22 16:11:06 restart (full shutdown-line scan of the whole
  `data/nascence.log` -- not a tail sample -- found no `Nascence shutting down.` line anywhere after the
  prior 08:43:39 shutdown; log tail at check time 2026-09-23 19:42:18, ~27.52 confirmed live-hours since
  the restart). Elapsed within that same session since F-1772's own 16:51:09 check: ~2h51m (~2.85
  confirmed live-hours) -- still short of F-1750's own carried-forward ~40-130h estimate. Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) anyway, per the standing "cheap check is
  fine any time" convention: `n_total_scored` grew **89 → 93** (+4), but **`n_backed` is unchanged at 9**
  -- all 4 new rows individually confirmed unbacked (`n_unbacked` 80→84) and confirmed to carry `w_gated`=0
  exactly, not even a near-miss (`secondary_n_any_spring_at_all` held at exactly 43 across both this read
  and F-1772's, which arithmetically requires all 4 new rows to have zero spring weight). This is the
  **seventeenth** consecutive attempt short of the pre-registered n≥14 bar; `n_backed` specifically has now
  read exactly 9 across **thirteen** reads spanning F-1447 (2026-09-17) through this one (F-1447, F-1478,
  F-1496, F-1508, F-1521, F-1530, F-1540, F-1551, F-1719, F-1734, F-1750, F-1772, F-1808). Primary verdict
  stays REAL_POSITIVE: mean diff +0.1288, 95% CI [+0.0513, +0.2088] (previous +0.1279, CI [+0.0507,
  +0.2101]) -- same direction, still short of the reporting bar. A binomial check (P(0 new backed hits | 4
  draws, lifetime rate ~10.11%) ≈ 65%) confirms zero new backed hits this window was the likely outcome,
  not a surprising one. **D-0215 re-confirmed via `decide.py show` (still travis's 2026-09-14 ruling, no
  active hold); not ruled, not reported to** (condition still not met). Because this window (~2.85h) is
  still short relative to the three previously-established multi-hour rate samples, its own ~1.40
  new-scored-rows/live-hour observation is noted but NOT folded into the rate history as a confirmed
  fourth value (same precedent F-1772 set for its own shorter window); F-1750's own ~40-130-live-hour
  estimate carries forward unchanged. **J-1288 spawned** for the next attempt. F-1808.
  **★ 2026-09-24 — J-1288: attempt 18, still flat, but a real fourth rate sample (F-1837).** Du confirmed
  continuously live since the 2026-09-22 16:11:06 restart (full shutdown-line scan of the whole
  `data/nascence.log` -- not a tail sample -- found no `Nascence shutting down.` line anywhere after the
  prior 08:43:39 shutdown; log tail at check time 2026-09-24 07:20:27, ~39.16 confirmed live-hours since
  the restart). Elapsed within that same session since F-1808's own 19:42:18 check: ~11h38m (~11.64
  confirmed live-hours) -- unlike the two immediately preceding windows (~1.40h/F-1772, ~2.85h/F-1808,
  both too short to count), this window falls within the range of the three previously-established
  multi-hour rate samples (~5.55h-~30.5h). Re-ran `scripts/spring_ledger_reflective_ceiling_test.py`
  (unmodified) anyway, per the standing "cheap check is fine any time" convention: `n_total_scored` grew
  **93 → 98** (+5), but **`n_backed` is unchanged at 9** -- all 5 new rows individually confirmed unbacked
  (`n_unbacked` 84→89) and confirmed to carry `w_gated`=0 exactly, not even a near-miss
  (`secondary_n_any_spring_at_all` held at exactly 43 across both this read and F-1808's). This is the
  **eighteenth** consecutive attempt short of the pre-registered n≥14 bar; `n_backed` specifically has now
  read exactly 9 across **fourteen** reads spanning F-1447 (2026-09-17) through this one. Primary verdict
  stays REAL_POSITIVE: mean diff +0.1249, 95% CI [+0.0490, +0.2054] (previous +0.1288, CI [+0.0513,
  +0.2088]) -- same direction, still short of the reporting bar. A binomial check (P(0 new backed hits | 5
  draws, lifetime rate ~9.68%) ≈ 60%) confirms zero new backed hits this window was the likely outcome,
  not a surprising one. **D-0215 re-confirmed via `decide.py show` (still travis's 2026-09-14 ruling, no
  active hold); not ruled, not reported to** (condition still not met). Because this window (~11.64h) is
  materially longer than the two immediately preceding it, its own ~0.43 new-scored-rows/live-hour
  observation IS folded into the rate history as a fourth confirmed value -- landing within the existing
  0.39-1.19/hour spread rather than extending it (similar to F-1750's own 0.90/hour sample). Updated Fermi
  estimate: ~54 more total-scored rows needed at the current 9/98≈9.18% lifetime rate, implying roughly
  ~46-140 more confirmed live-hours before a full re-run is likely worth spending again -- materially
  unchanged from F-1750's own ~40-130h estimate; only ~15.89 of those hours have elapsed since F-1750's
  check across the F-1750→F-1772→F-1808→F-1837 chain. **J-1303 spawned** for the next attempt. F-1837.
  **★ 2026-09-24 — J-1303: attempt 19, still flat, second zero-growth window but write path confirmed
  alive via a per-row check (F-1855).** Du confirmed continuously live since the 2026-09-22 16:11:06
  restart (full shutdown-line scan of the whole `data/nascence.log` -- not a tail sample -- found no
  `Nascence shutting down.` line anywhere after the prior 08:43:39 shutdown; log tail at check time
  2026-09-24 11:31:30, ~43.34 confirmed live-hours since the restart). Elapsed within that same session
  since F-1837's own 07:20:27 check: ~4.18 confirmed live-hours. Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) anyway, per the standing "cheap check is
  fine any time" convention: every single value came back byte-identical to F-1837's own read --
  `n_total_scored` still 98, `n_unbacked` still 89, `n_backed` still 9, same summary stats, same
  primary_mean_diff (+0.1249, CI [+0.0490, +0.2054]), same secondary Pearson r (0.3815) -- the second
  zero-growth window in this 19-attempt chain (the first was F-1772's own ~1.40h window; this one is
  materially longer at ~4.18h). This is the **fifteenth** consecutive read at exactly `n_backed`=9
  (F-1447, F-1478, F-1496, F-1508, F-1521, F-1530, F-1540, F-1551, F-1719, F-1734, F-1750, F-1772, F-1808,
  F-1837, F-1855) and the **twentieth** consecutive attempt short of the n>=14 reporting bar overall.
  Checked directly rather than assumed, and finer-grained than any prior attempt's own check: a per-row
  read of `data/associative_recall_shadow.jsonl`'s `m2_usage` rows (541 total) found 8 rows with
  `parent_ts` after F-1837's own check cutoff, spanning task/reflective/relational modes each time -- but
  all 8 carried a reflective usage list of length exactly 0. This directly confirms the write path is
  alive and actively scoring usage events, not stalled; this window simply produced zero reflective-mode
  entries, matching the mode's already-documented low/bursty base rate (F-1540's up to ~29h droughts).
  **D-0215 re-confirmed via `decide.py show` (still travis's 2026-09-14 ruling, no active hold); not
  ruled, not reported to** (condition still not met). Because this window produced zero new
  `n_total_scored` rows at all (not merely zero new backed rows among some new draws), it supplies no
  usable rate sample and is NOT folded into the four already-established rate values (~0.39/0.43/0.90/1.19
  new-scored-rows/live-hour) -- same treatment F-1772's own zero-growth window received. The Fermi
  estimate (~5 more backed hits / ~54 more total-scored rows needed at the current 9/98≈9.18% lifetime
  rate; ~46-140 more confirmed live-hours) therefore carries forward from F-1837 completely unchanged;
  only ~20.07 of those hours have now elapsed since F-1750's baseline (up from F-1837's own ~15.89h).
  **J-1314 spawned** for the next attempt. F-1855.
  **★ 2026-09-24 — J-1314: attempt 20, still flat, third zero-growth window (shortest yet) with a
  different all-modes-empty signature (F-1869).** Du confirmed continuously live since the 2026-09-22
  16:11:06 restart (full shutdown-line scan of the whole `data/nascence.log` -- not a tail sample --
  found no `Nascence shutting down.` line anywhere after the prior 08:43:39 shutdown; log tail at check
  time 2026-09-24 12:40:56, ~44.50 confirmed live-hours since the restart). Elapsed within that same
  session since F-1855's own 11:31:30 check: ~1.16 confirmed live-hours -- the SHORTEST window yet in the
  whole chain, shorter even than F-1772's own ~1.40h. Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) anyway, per the standing "cheap check is
  fine any time" convention: every single value came back byte-identical to F-1855's own read --
  `n_total_scored` still 98, `n_unbacked` still 89, `n_backed` still 9, same summary stats, same
  primary_mean_diff (+0.1249, CI [+0.0490, +0.2054]), same secondary Pearson r (0.3815) -- the THIRD
  zero-growth window in this 20-attempt chain (the first was F-1772's own ~1.40h window, the second
  F-1855's own ~4.18h window). This is the **sixteenth** consecutive read at exactly `n_backed`=9
  (F-1447, F-1478, F-1496, F-1508, F-1521, F-1530, F-1540, F-1551, F-1719, F-1734, F-1750, F-1772, F-1808,
  F-1837, F-1855, F-1869) and the **twenty-first** consecutive attempt short of the n>=14 reporting bar
  overall. Checked directly rather than assumed, via the same per-row method F-1855 introduced: a per-row
  read of `data/associative_recall_shadow.jsonl`'s `m2_usage` rows (544 total) found 3 rows with
  `parent_ts` after F-1855's own check cutoff -- but unlike F-1855's 8 rows (non-empty task/relational,
  only reflective empty), all 3 of THESE rows carry EMPTY usage lists in every mode simultaneously
  (task/reflective/relational all length 0). This still confirms the write path is alive and actively
  firing (3 new events landed, the shadow log's mtime/size both grew) -- these particular scoring events
  simply had nothing at all to score this window, a related but distinct zero-yield mechanism from
  F-1855's reflective-specific-drought reading. **D-0215 re-confirmed via `decide.py show` (still
  travis's 2026-09-14 ruling, no active hold); not ruled, not reported to** (condition still not met).
  Because this window produced zero new `n_total_scored` rows at all, it supplies no usable rate sample
  and is NOT folded into the four already-established rate values (~0.39/0.43/0.90/1.19
  new-scored-rows/live-hour) -- same treatment F-1772's and F-1855's own zero-growth windows received. The
  Fermi estimate (~5 more backed hits / ~54 more total-scored rows needed at the current 9/98≈9.18%
  lifetime rate; ~46-140 more confirmed live-hours) therefore carries forward from F-1837/F-1855
  completely unchanged; only ~21.23 of those hours have now elapsed since F-1750's baseline (up from
  F-1855's own ~20.07h). **J-1323 spawned** for the next attempt, carrying a suggestion (given three of
  the last four checks landed within ~1.16-4.18h of being spawned) to consider spacing the next check out
  rather than re-running within minutes, purely to get a more informative window. F-1869.
  **★ 2026-09-24 — J-1323: attempt 21, n_backed BREAKS its sixteen-read streak at 9 -- moves to 10, but a
  softer point estimate (F-1876).** Du confirmed continuously live since the 2026-09-22 16:11:04 restart
  (full shutdown-line scan of the whole `data/nascence.log` -- not a tail sample -- found the same 249
  total `Nascence shutting down` occurrences as F-1869's own scan, confirming no new shutdown; no shutdown
  line anywhere after line 495878; log tail at check time 2026-09-24 13:22:37, ~45.19 confirmed live-hours
  since the restart). Elapsed within that same session since F-1869's own 12:40:56 check: ~0.69 confirmed
  live-hours -- the SHORTEST window yet in the whole chain, shorter even than F-1869's own ~1.16h. Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) anyway, per the standing "cheap check is
  fine any time" convention: `n_total_scored` grew **98 -> 101** (+3), and for the first time since F-1447
  (2026-09-17) **`n_backed` moved -- 9 -> 10** (`n_unbacked` 89->91), ending the sixteen-read flat-at-9
  streak (F-1447 through F-1869). A per-entry inspection (reusing the test module's own `run()`, read-only)
  found the 10 backed occurrences now resolve to **8 distinct fragment ids** (up from F-1750's audited 7):
  the new one is `02dfe47e-ba5e-4529-91ba-ec9a2d0ed6f0` (w_gated=1.0000, ceiling-pinned, cos_sim=0.2097),
  scored at a parent_ts converting to 2026-09-24 12:45:08 local -- about 4m12s after F-1869's own check
  cutoff, and from the same parent-thought scoring event as the window's 2 new unbacked rows. The other 9
  occurrences (7 ids) are byte-identical to F-1750's own per-fragment audit. Primary verdict stays
  REAL_POSITIVE but the point estimate softened: mean diff +0.1096, 95% CI [+0.0364, +0.1872] (previous
  +0.1249, CI [+0.0490, +0.2054]) -- reported honestly rather than as unambiguous good news, since the new
  backed entry's own cos_sim (0.2097) sits well below the backed group's prior mean (0.3698), pulling
  backed_summary mean down to 0.3538; secondary Pearson r eased 0.3815->0.3397. This is the TWENTY-SECOND
  consecutive attempt short of the pre-registered n>=14 bar (one more than F-1869's own 21st), even though
  the flat-at-9 streak itself is now broken. **D-0215 re-confirmed via `decide.py show` (still travis's
  2026-09-14 ruling, no active hold); not ruled, not reported to** (condition n_backed>=14 still not met).
  Because this window (~0.69h) is shorter than every previously-established multi-hour rate sample, its own
  implied ~4.3 new-scored-rows/live-hour rate is noted but NOT folded into the rate history as a confirmed
  fifth value -- same treatment F-1772's and F-1808's own short windows received, now extended to a
  short-but-nonzero-backed-growth window too. Updated Fermi estimate at the new lifetime backed rate
  (10/101~=9.90%, up from 9/98~=9.18%): ~4 more backed hits needed (down from ~5), ~40 more total-scored
  rows needed at that rate (down from ~54), implying roughly **~34-104** more confirmed live-hours before a
  full re-run is likely worth spending again -- narrower than F-1837/F-1855/F-1869's own carried-forward
  ~46-140h estimate; only ~21.92 of those hours have now elapsed since F-1750's baseline (up from F-1869's
  own ~21.23h). **J-1328 spawned** for the next attempt, carrying forward the narrowed estimate and a
  caution that a real backed hit landing inside a sub-hour window this once should not be read as evidence
  that short windows are generally informative -- one data point against a still-noisy rate spread. F-1876.
  **★ 2026-09-24 — J-1328: attempt 22, first flat read AFTER the 9->10 jump -- confirmed fresh, not assumed
  (F-1879).** Per this job's own dispatch note ("confirm this fresh rather than assuming another flat
  read"), re-ran the full check rather than inferring from F-1876 alone. Du confirmed continuously live
  since the 2026-09-22 16:11:04.753 restart (full shutdown-line scan of the whole `data/nascence.log` --
  not a tail sample -- found the same 249 total `Nascence shutting down` occurrences as F-1876's own scan,
  no new shutdown line anywhere after line 495878; log tail at check time 2026-09-24 14:22:52, ~46.20
  confirmed live-hours since the restart). Elapsed within that same session since F-1876's own 13:22:37
  check: ~1.00 confirmed live-hours. Re-ran `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified)
  anyway, per the standing "cheap check is fine any time" convention: every single value came back
  byte-identical to F-1876's own read -- `n_total_scored` still 101, `n_unbacked` still 91, `n_backed`
  still **10**, same backed/unbacked summary stats, same primary_mean_diff (+0.1096, CI [+0.0364,
  +0.1872]), same secondary Pearson r (0.3397). This is the **first** flat read at the new level of 10 --
  the 9->10 jump did not immediately continue, but it also did not revert; it is now the **TWENTY-THIRD**
  consecutive attempt short of the pre-registered n>=14 bar. Checked directly rather than assumed, via the
  same per-row method F-1855 introduced: a per-row read of `data/associative_recall_shadow.jsonl`'s
  `m2_usage` rows (549 total) found 4 rows with `parent_ts` after F-1876's own check cutoff -- one carrying
  a non-empty task list (task_len=3) but an empty reflective list, the other three carrying empty usage
  lists across every mode simultaneously. None of the 4 scored anything in reflective mode, fully
  explaining the flat `n_total_scored` despite the write path plainly firing (`associative_recall_shadow.
  jsonl` grew 656,467 -> 658,834 bytes this window). **D-0215 re-confirmed via `decide.py show` twice this
  session (still travis's 2026-09-14 ruling, no active hold); not ruled, not reported to** (condition
  n_backed>=14 still not met). Because this window produced zero new `n_total_scored` rows, it supplies no
  usable rate sample and is NOT folded into the four already-established rate values -- same treatment
  every prior zero-growth window received. The Fermi estimate (~4 more backed hits / ~40 more total-scored
  rows needed at the current 10/101~=9.90% lifetime rate; ~34-104 more confirmed live-hours) carries
  forward from F-1876 completely unchanged; only ~22.93 of those hours have now elapsed since F-1750's
  baseline (up from F-1876's own ~21.92h). **J-1330 spawned** for the next attempt. F-1879.
  **★ 2026-09-24 — J-1330: attempt 23, SECOND consecutive flat read at 10, a stricter null than F-1879's
  (F-1886).** Per this job's own dispatch note (the harness's IMPORTANT NOTE flagged n_backed holding at
  10 for one flat read and asked to confirm fresh rather than assume another), re-ran the full check
  rather than inferring from F-1879 alone. Du confirmed continuously live since the 2026-09-22
  16:11:04.753 restart (full shutdown-line scan of the whole `data/nascence.log` found the same 249
  total `Nascence shutting down` occurrences as every prior scan, no new shutdown line anywhere after
  line 495878; log tail at final check time 2026-09-24 15:07:27.678, ~46.94 confirmed live-hours since
  the restart). Elapsed within that same session since F-1879's own 14:22:52.804 check: ~0.743 confirmed
  live-hours. Re-ran `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified) anyway, per the
  standing "cheap check is fine any time" convention: every single value came back byte-identical to
  F-1876's and F-1879's own reads -- `n_total_scored` still 101, `n_unbacked` still 91, `n_backed` still
  **10**, same backed/unbacked summary stats, same primary_mean_diff (+0.1096, CI [+0.0364, +0.1872]),
  same secondary Pearson r (0.3397). This is now the **TWENTY-FOURTH** consecutive attempt short of the
  pre-registered n>=14 bar. Checked directly rather than assumed, via the same per-row method F-1855
  introduced, extended this time to check the FULL `m2_usage` row count too (not just the reflective
  slice): a per-row read of `data/associative_recall_shadow.jsonl` found **zero** new `kind=="m2_usage"`
  rows at all since F-1879's own cutoff (549 total, unchanged) -- a stricter null than F-1879's own
  window (which had 4 new m2_usage rows, all empty-reflective). The write path is still confirmed alive
  by other direct evidence: exactly 2 new `kind==None` (`m2_edge_aware`/`shadow_compare`) rows landed
  this window (2026-09-24T14:30:10.37 and 14:51:07.98 local), fully accounting for the shadow log's own
  byte growth (658,834 -> 660,172 bytes, +1,338) with nothing left unexplained. **D-0215 re-confirmed via
  `decide.py show` twice this session (still travis's 2026-09-14 ruling, no active hold); not ruled, not
  reported to** (condition n_backed>=14 still not met). Because this window produced zero new
  `n_total_scored` rows, it supplies no usable rate sample and is NOT folded into the four already-
  established rate values -- same treatment every prior zero-growth window received. The Fermi estimate
  (~4 more backed hits / ~40 more total-scored rows needed at the current 10/101~=9.90% lifetime rate;
  ~34-104 more confirmed live-hours) carries forward from F-1876/F-1879 completely unchanged; only
  ~23.67 of those hours have now elapsed since F-1750's baseline (up from F-1879's own ~22.93h).
  **J-1336 spawned** for the next attempt. F-1886.
  **★ 2026-09-24 — J-1336: attempt 24, THIRD consecutive flat read at 10, new m2_usage rows now fully
  empty across every mode (F-1891).** Per this job's own dispatch note (the harness's IMPORTANT NOTE
  flagged n_backed holding at 10 for two flat reads and asked to confirm fresh rather than assume a
  third), re-ran the full check rather than inferring from F-1886 alone. Du confirmed continuously live
  since the 2026-09-22 16:11:04.753 restart (full shutdown-line scan of the whole `data/nascence.log`
  found the same 249 total `Nascence shutting down` occurrences as every prior scan, no new shutdown line
  anywhere after line 495878; log tail at final check time 2026-09-24 16:09:15.416, ~47.97 confirmed
  live-hours since the restart). Elapsed within that same session since F-1886's own 15:07:27.678 check:
  ~1.03 confirmed live-hours. Re-ran `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified)
  anyway, per the standing "cheap check is fine any time" convention: every single value came back
  byte-identical to F-1876's, F-1879's, and F-1886's own reads -- `n_total_scored` still 101, `n_unbacked`
  still 91, `n_backed` still **10**, same backed/unbacked summary stats, same primary_mean_diff (+0.1096,
  CI [+0.0364, +0.1872]), same secondary Pearson r (0.3397). This is now the **TWENTY-FIFTH** consecutive
  attempt short of the pre-registered n>=14 bar. A per-row read of `data/associative_recall_shadow.jsonl`
  found 2 new `kind=="m2_usage"` rows since F-1886's own cutoff (549 -> 551), but -- checked at the full
  `usage_by_mode` level, not just the reflective slice, per F-1886's own recommendation -- BOTH rows carry
  zero entries in ALL three modes (task/reflective/relational), a different signature than F-1879's window
  (4 new rows, empty-reflective only) or F-1886's window (zero new m2_usage rows at all). The write path is
  confirmed alive by 5 new rows total landing strictly after F-1886's own check-tail (3 `kind==None` +
  those same 2 `kind=="m2_usage"`, local 15:12:56.26/15:35:09.65/15:52:07.01), fully accounting for the
  shadow log's own byte growth (660,172 -> 662,385 bytes, +2,213) with nothing left unexplained. **D-0215
  re-confirmed via `decide.py show` twice this session (still travis's 2026-09-14 ruling, no active hold);
  not ruled, not reported to** (condition n_backed>=14 still not met). Because this window produced zero
  new `n_total_scored` rows, it supplies no usable rate sample and is NOT folded into the four already-
  established rate values -- same treatment every prior zero-growth window received. The Fermi estimate
  (~4 more backed hits / ~40 more total-scored rows needed at the current 10/101~=9.90% lifetime rate;
  ~34-104 more confirmed live-hours) carries forward from F-1876/F-1879/F-1886 completely unchanged; only
  ~24.70 of those hours have now elapsed since F-1750's baseline (up from F-1886's own ~23.67h). **J-1339
  spawned** for the next attempt. F-1891.
  **★ 2026-09-24 — J-1339: attempt 25, FOURTH consecutive flat read at 10, new row empty in task+reflective
  but not relational (F-1892).** Per this job's own dispatch note (the harness's IMPORTANT NOTE flagged
  n_backed holding at 10 for three flat reads and asked to confirm fresh rather than assume a fourth),
  re-ran the full check rather than inferring from F-1891 alone. Du confirmed continuously live since the
  2026-09-22 16:10:23 restart (full shutdown-line scan of the whole `data/nascence.log`, 517,336 lines,
  found the same 249 total `Nascence shutting down` occurrences as every prior scan, no new shutdown line
  anywhere after line 495878; log tail at this check's time 2026-09-24 16:39:37.109, ~48.48 confirmed
  live-hours since the restart). Elapsed within that same session since F-1891's own 16:09:15.416 check:
  ~0.51 confirmed live-hours. Re-ran `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified)
  anyway, per the standing "cheap check is fine any time" convention: every single value came back
  byte-identical to F-1876's, F-1879's, F-1886's, and F-1891's own reads -- `n_total_scored` still 101,
  `n_unbacked` still 91, `n_backed` still **10**, same backed/unbacked summary stats, same
  primary_mean_diff (+0.1096, CI [+0.0364, +0.1872]), same secondary Pearson r (0.3397). This is now the
  **TWENTY-SIXTH** consecutive attempt short of the pre-registered n>=14 bar. A per-row read of
  `data/associative_recall_shadow.jsonl` found exactly 1 new `kind=="m2_usage"` row since F-1891's own
  cutoff (551 -> 552, parent_ts 1790224260.54, local 16:31:00.54) -- checked at the full `usage_by_mode`
  level, not just the reflective slice: task=0, reflective=0, relational=5, a signature not seen in any
  prior flat-read window (F-1879: multiple rows, empty-reflective only; F-1886: zero new rows; F-1891:
  empty across ALL three modes). Because the ceiling-test script only reads the reflective list, this row
  legitimately contributed zero new reflective-scored entries. **D-0215 re-confirmed via `decide.py show`
  this session (still travis's 2026-09-14 ruling, no active hold); not ruled, not reported to** (condition
  n_backed>=14 still not met). Because this window produced zero new `n_total_scored` rows, it supplies no
  usable rate sample and is NOT folded into the four already-established rate values -- same treatment
  every prior zero-growth window received. The Fermi estimate (~4 more backed hits / ~40 more total-scored
  rows needed at the current 10/101~=9.90% lifetime rate; ~34-104 more confirmed live-hours) carries
  forward from F-1876/F-1879/F-1886/F-1891 completely unchanged; only ~25.21 of those hours have now
  elapsed since F-1750's baseline (up from F-1891's own ~24.70h). **J-1340 spawned** for the next attempt.
  F-1892.
  **★ 2026-09-24 — J-1340: attempt 26, n_backed still 10, but the FIRST post-jump window where
  n_total_scored itself moved (F-1896).** Per this job's own dispatch note (the harness's IMPORTANT NOTE
  flagged n_backed holding at 10 for four flat reads and asked to confirm fresh rather than assume a
  fifth), re-ran the full check rather than inferring from F-1892 alone. Du confirmed continuously live
  since the 2026-09-22 16:10:23 restart (full shutdown-line scan of the whole `data/nascence.log`, 517759
  lines -- up from F-1892's 517336 -- found the same 249 total `Nascence shutting down` occurrences as
  every prior scan, no new shutdown line anywhere after line 495878; log tail at this check's time
  2026-09-24 17:22:56.152, ~49.20 confirmed live-hours since the restart). Elapsed within that same
  session since F-1892's own 16:39:37.109 check: ~0.72 confirmed live-hours. Re-ran
  `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified, run from its C:\Nascence location since
  this job's own dedicated worktree has no `data/` directory -- untracked/gitignored, read-only) anyway,
  per the standing "cheap check is fine any time" convention: `n_total_scored` grew **101 -> 104** (+3),
  and **`n_backed` is unchanged at 10** -- but unlike every one of the four reads immediately before it
  (F-1879/F-1886/F-1891/F-1892, all byte-identical including `n_total_scored`), this is the FIRST window
  since the 9->10 jump (F-1876) where `n_total_scored` itself moved while `n_backed` held. This is now the
  **TWENTY-SEVENTH** consecutive attempt short of the pre-registered n>=14 bar. A per-row read of
  `data/associative_recall_shadow.jsonl` (via a job-id-qualified scratch script, `per_row_check_J-1340.py`)
  found exactly 2 new `kind=="m2_usage"` rows since F-1892's own cutoff (552 -> 554), contributing 3 new
  reflective-scored entries between them (one row task=1/reflective=0/relational=6; the other
  task=3/reflective=3/relational=6) -- checked against `core.spring_ledger`'s own max-`w_gated` lookup, all
  3 landed unbacked (`max_w_gated` 0.0, 0.0, 0.2000, the last a genuine near-miss just under the 0.3 bar).
  0+3=3 matches `n_total_scored`'s own growth exactly, and all-3-unbacked matches `n_unbacked`'s own
  91->94 growth exactly, nothing left unexplained. Primary verdict stays REAL_POSITIVE: mean diff +0.1061,
  95% CI [+0.0322, +0.1866] (previous +0.1096, CI [+0.0364, +0.1872]) -- same direction, point estimate
  softened slightly as 3 new lower-cosine entries joined the unbacked group. **D-0215 re-confirmed via
  `decide.py show` this session (still travis's 2026-09-14 ruling, no active hold); not ruled, not
  reported to** (condition n_backed>=14 still not met). Because this window's ~0.72h duration is sub-hour,
  its own implied rate (~4.15 new-scored-rows/live-hour) is NOT folded into the four already-established
  rate values (~0.39/0.43/0.90/1.19/hour) -- same treatment F-1876's own short-but-real-growth window
  received. Updated lifetime backed rate 10/104~=9.62% (down from 9.90%); a binomial check using the prior
  rate puts P(0 backed hits | 3 draws, ~9.90%) ~= 73%, an unsurprising outcome. Updated Fermi estimate: ~4
  more backed hits / ~42 more total-scored rows needed, implying roughly ~35-108 more confirmed live-hours
  (materially unchanged from F-1876/F-1879/F-1886/F-1891/F-1892's own ~34-104h estimate); only ~25.93 of
  those hours have now elapsed since F-1750's baseline (up from F-1892's own ~25.21h). **J-1342 spawned**
  for the next attempt. F-1896.
  **★ 2026-09-25 — J-1342: attempt 28, n_backed BREAKS the flat-at-10 run — jumps to 27, crossing the
  n≥14 bar for the first time (F-1901).** Per this job's own dispatch note (the harness's IMPORTANT NOTE
  flagged n_backed holding at 10 for six flat reads and asked to confirm fresh rather than assume
  another), re-ran the full check rather than inferring from F-1896 alone. Du confirmed continuously live
  since the 2026-09-22 16:10:23 restart (full shutdown-line scan of the whole `data/nascence.log`,
  523,602 lines -- up from F-1896's 517,759 -- found the same 249 total `Nascence shutting down`
  occurrences as every prior scan, no new shutdown line anywhere after line 495878; log tail at this
  check's time 2026-09-25 08:18:00, ~64.13 confirmed live-hours since the restart). Elapsed within that
  same session since F-1896's own 17:22:56 check: ~14.92 confirmed live-hours -- by far the longest
  single confirmed-live re-check window in the whole 28-attempt chain (previous longest single-interval
  sample was ~11.64h/F-1837). Re-ran `scripts/spring_ledger_reflective_ceiling_test.py` (unmodified,
  from its real C:\Nascence location): `n_total_scored` grew **104 -> 143** (+39), and **`n_backed`
  jumped 10 -> 27** (`n_unbacked` 94->116) -- the first time in 28 attempts the pre-registered n>=14
  reporting bar has been crossed. Primary verdict REAL_POSITIVE: mean diff +0.1312, 95% CI [+0.0819,
  +0.1836] (previous +0.1061, CI [+0.0322, +0.1866]) -- same direction, CI clearly excludes 0, point
  estimate clears the +0.05 bar by >2.6x and sits close to the defeater's own named "~+0.12" reference.
  Secondary Pearson r 0.3567 (previous 0.3397), same direction. **Two read-only scratch checks
  (`per_row_check_J-1342.py`, `per_fragment_check_J-1342.py`, this job's own scratchpad) verified the
  jump is real accrual, not a counting artifact, and interrogated it further given its size:** 574 total
  `m2_usage` rows now (554 at F-1896's cutoff, +20 new), contributing 39 new reflective-scored entries
  (104 old + 39 new = 143, matches exactly, cross-checked against the real script's own n_backed=27/
  n_unbacked=116 -- both matched exactly). Of the 17-point n_backed jump: 1 is a previously-scored entry
  (`f1a1fdc4-ad7`, w_gated now 0.3374) that flipped unbacked->backed purely from continued spring
  reinforcement since F-1896 -- this script is NOT time-respecting (reads the CURRENT w_gated snapshot
  per its own docstring), the same look-ahead-bias class F-1316 named, closed only for the ORIGINAL
  n=7/36 sample by J-0948's separate time-respecting script, not for any read since; the other 16 are
  genuinely new entries landing backed on first read. **A real, honest hub-concentration caveat, checked
  directly (mirrors F-1316's own hub-dominance check):** 17/27 (63.0%) backed occurrences come from just
  2 of the backed group's 10 distinct fragment ids -- `f1a1fdc4-ad7` (w_gated=0.3374, 10 occurrences)
  and `5449e6d0-ed9` (w_gated=1.0000, ceiling-pinned, 7 occurrences, all new this window, cos_sim
  0.2498-0.6575) -- vs the unbacked group's much lower 17.2% top-2 concentration across 62 distinct ids.
  An exploratory (non-pre-registered) fragment-level dedup check -- one value per distinct fragment,
  averaging repeat occurrences first, run specifically to test whether the primary verdict survives this
  concentration -- still clears the bar: backed n_distinct=10 mean=0.3637 vs unbacked n_distinct=62
  mean=0.2497, diff=+0.1139, 95% CI [+0.0456, +0.1881] -- the effect is not merely an artifact of 2
  fragments being repeatedly sampled, though the concentration itself is real and worth a founder's own
  weighing. **D-0215 re-confirmed via `decide.py show` before acting (still travis's 2026-09-14 ruling,
  no active hold) -- then REOPENED (not ruled) per `/decide` SKILL.md's own rule 4 ("a ruling whose
  defeater has fired is no longer a ruling"), since path (a)'s defeater condition (n>=14, CI clear of
  zero near +0.12) has now genuinely fired.** This ends the re-check chain's spawn cycle (J-0936 through
  J-1342, 28 attempts, 2026-09-13 through 2026-09-25) -- no further re-check job spawned, since the
  reporting condition is now met; D-0215 awaits a founder read weighing the hub-concentration caveat
  against the otherwise-clean REAL_POSITIVE result. F-1901.
  **★ 2026-09-25 — J-1348: D-0215's own ruling ("authorize the live write now") built (F-1909).**
  Between F-1901 and this job, D-0215 was ruled by travis (2026-09-24T20:59:13Z): "Authorize the live
  write now... Graduate co_recalled_developing from spring_ledger's shadow store to an actual live
  memory_edges write, feeding M2's edge_aware_neighbors for real." `core/spring_ledger.py`'s
  `observe_co_recall()` gained an opt-in `live_edges: bool = False` param, a kill-switch
  (`LIVE_EDGE_WRITE`, default `True`), and the ceiling-test bar as a named constant
  (`LIVE_EDGE_THRESHOLD = 0.3`, matching F-1316's own `SPRING_THRESHOLD`); a new `_write_live_edge()`
  helper writes the real `(fragment)-[co_recalled_developing]->(fragment)` row via `core.memory_edges
  .add_edge()` (still `INSERT OR IGNORE` — a snapshot fact, not a live-updated value) the first time a
  pair's own `w_gated` clears the bar. `core/memory_edges.py`'s `log_co_recall()` is the ONE real call
  site that opts in (`live_edges=True`); every other caller (`scripts/spring_ledger_backfill.py`'s
  replay, in particular) keeps the pre-D-0215 default and is untouched. **A design gap was found and
  designed around before shipping, not after:** the persisted `spring_ledger_state.json` keys pairs by
  a lossy 12-char fragment-id-prefix composite (`f"{a[:12]}|{b[:12]}"`), which cannot be reversed to
  real ids — so the live write happens INLINE inside `observe_co_recall()`'s own per-pair loop, using
  the full ids already in scope, never by reading the persisted state back out. **Confirmed, not
  assumed, that the M2 read path needs zero changes:** `edge_aware_neighbors`'s own
  `_DIRECT_FRAGMENT_TYPES`/`MODE_EDGE_WEIGHTS` (J-0263, 2026-08-25) already name
  `co_recalled_developing`; it was simply 0-yield until a real row existed. Verified via an isolated
  smoke test (`lab_env.isolate()`, DB_PATH + spring_ledger's/opponent_process's own state+log globals
  all redirected, never the live store; 19/19 checks): read-side wiring confirmed live end-to-end with
  correct per-mode weights (reflective 1.0×, task 0.3×, relational untested-but-same-table); the write
  fires exactly on threshold-crossing and is idempotent after; the kill-switch fully suppresses the
  write while leaving the shadow `w_naive`/`w_gated` math byte-identical to before this change; the
  untouched default (`live_edges=False`, mimicking `spring_ledger_backfill.py`'s real call signature)
  writes nothing; the real production entry point (`log_co_recall`) works end-to-end with M1's ledger
  and `opponent_process` unaffected; and 4 concurrent threads writing the same edge deduped cleanly to
  one row with no exception, confirming the write doesn't race `memory_edges`' other writers (same
  `busy_timeout=30000` + `UNIQUE`-constraint precedent every other forward hook in that file already
  relies on) — directly answering D-0215's own defeater's live-write-race concern. **Deliberately NOT
  built this pass:** a historical backfill/harvest of the ~27 pairs F-1901 already found above the bar
  — they graduate the next time each pair recurs in a real post-restart co-recall event, not
  immediately on restart; an explicit, checked non-doing, not scope creep, and a candidate for a
  future job only if forward-hook-only accrual proves too slow to observe. **Restart-gated — this
  session never touched any live store** (the isolated lab dir's own DB copy was separately discarded
  by a real, unrelated gap in `lab_env.py`'s own WAL-mode write-detection, filed as S-0188, not fixed
  here). D-0215 itself is UNCHANGED by this build (still travis's ruling, not reopened) — neither of
  its two named defeater conditions fired. A post-restart real-window re-check (does the
  hub-concentration pattern hold up as real signal once `edge_aware_neighbors` has real rows to read)
  is queued as a follow-up job, precondition-gated on a restart with this code plus a real window of
  live accrual — no fixed `--not-before`, since restart timing isn't known; a future job-run should
  precondition-check first and report current numbers if not yet met. F-1909.
  **★ 2026-09-26 — J-1353: D-0215's own defeater re-checked on the first real post-restart live window
  — does NOT fire (F-1945).** Precondition met: a full shutdown/restart-line scan of the whole
  `data/nascence.log` (535,535 lines, not a tail sample) found 250 total `Nascence shutting down`
  occurrences (one more than F-1896/F-1901's 249, at line 525166, 2026-09-25 11:59:15 — that session had
  started before commit fc07c7b landed and ran the pre-live code throughout); the FIRST restart running
  fc07c7b's own code is at line 525167/525182 (2026-09-25 19:21:11/19:21:51), with no further shutdown
  line through the log's current end (line 535535, 2026-09-26 19:29:37) — ~24.2 confirmed live-hours,
  the first real window since J-1348's build. Live `memory_edges` census (read-only against
  `data/memory/nascence.db`): 131 real `co_recalled_developing` rows now exist, ALL created inside this
  window (zero pre-date it, as expected — J-1348 deliberately did not backfill), touching 105 distinct
  fragment ids — only 4/131 (3.1%) touch either of F-1901's 2 named hub ids, and `f1a1fdc4-ad7` has ZERO
  live edges at all (all 4 are `5449e6d0-ed9`'s). `edge_aware_neighbors(mode=reflective)`, probed against
  20 real post-restart recall-trail seeds from `data/co_recall_ledger.jsonl` (excluding the 2 hubs),
  returns real `co_recalled_developing` neighbors connecting 3 non-hub fragments to each other (6 hits)
  with no hub involvement at all — directly answering the defeater's own named downstream-behavior test
  ("edge_aware_neighbors' downstream behavior shows no measurable difference outside those 2 fragments'
  own neighborhoods") in the negative: there IS measurable reach outside the 2 hub fragments' own
  neighborhoods. A fresh unmodified run of `scripts/spring_ledger_reflective_ceiling_test.py` stays
  PRIMARY VERDICT REAL_POSITIVE (`n_total_scored` 143→153, `n_backed` 27→29, mean diff +0.1312→+0.1280,
  95% CI [+0.0819,+0.1836]→[+0.0815,+0.1774] — same direction, still clears the +0.05 bar by >2.5x), and
  its fragment-dedup-robustness check stays stable (+0.1139→+0.1146). **Honest secondary caveat, checked
  directly, not the deciding factor:** WITHIN the ceiling-test's own narrow scored-AND-backed intersection
  (n=29 — a much smaller, rarer population than the live graph's own 131 edges/105 ids), the same 2
  fragment ids are still 19/29=65.5% of backed occurrences (up slightly from F-1901's 63.0%, i.e. flat,
  not diversifying) — but this narrow secondary metric is not the defeater's own named primary test
  (`edge_aware_neighbors`' real downstream behavior, above), and the primary verdict is dedup-robust on
  both reads. Weighing both of the defeater's own named tests together: it has not fired. D-0215's
  ruling (travis, 2026-09-24T20:59:13Z, "authorize the live write now") stands as travis's; not
  escalating to decide-review. No new re-check job spawned for the flat ceiling-test-sample
  concentration by itself — a distinct, non-blocking observation, recorded here and in F-1945 rather
  than restarting a fresh chase chain the founder's own ruling already called "a long wait already."
  F-1945.
- **2026-09-27 (J-1415): D-0287 ruled and built the same session — `recall_trail_edge_aware` flipped
  LIVE for mode="relational" ONLY, kill-switched (F-1983).** D-0287 (option (a)) ruled on real usage
  evidence (F-1966: relational is the only mode where 39% of edge-reached fragments clear a real
  usage-proxy bar, vs task 0.25 mean / reflective 0.28 mean cosine to the next thought). Build:
  `core/associative_recall.py`'s `recall_memory_fragments()` — the one function feeding
  `orchestrator._retrieve_memory`'s live conversational-retrieve augmentation — now layers
  `recall_trail_edge_aware(mode="relational")` on top of the plain greedy trail, gated by a new
  kill-switch (`M2_EDGE_AWARE_RELATIONAL_LIVE`, default `True`) plus its own local fail-open (falls
  back to the untouched greedy trail on any error, a second layer on top of `recall_trail_edge_aware`'s
  own pre-existing one). `mode="task"`/`"reflective"` are UNCHANGED — still read only by
  `shadow_compare()` for logging, never live, per D-0287's own ruling. **Zero changes needed to
  `edge_aware_neighbors`'s or `recall_trail_edge_aware`'s own weighting/traversal math** — same
  "read side needs no code change" pattern D-0215's build (F-1909) found for the write side; only
  docstrings + one kill-switch + one call site changed. **Verified via an isolated smoke test**
  (`lab_env.isolate(db="empty")`, a synthetic 2-fragment/1-edge fixture, `associative_recall._cache`
  seeded directly — no live store touched, confirmed the worktree's own code was under test; 10/10
  checks passed): switch OFF reproduces the exact pre-D-0287 output; ON calls the live function exactly
  once with `mode="relational"` and the edge-only-reachable fragment now surfaces without the greedy
  trail's own member ever regressing; a forced exception falls back cleanly to the plain greedy trail
  (not `[]` — the NEW local try/except is what fires, not the function's own pre-existing outer blanket
  catch). **Restart-gated — has not affected live Du this session** (isolated smoke test only). D-0287's
  own defeater (freshly written at ruling time) sets what to watch once Du restarts on this code: the
  live usage-proxy rate falling well below the shadow-observed 39%, the kill-switch being exercised for
  a real operational reason, or task/reflective's own shadow rate later showing the same lift (a reason
  to widen, which this flag alone does not do). A post-restart real-window re-check is queued as a
  follow-up job, precondition-gated on a restart with this code plus a real window of live accrual —
  same pattern as D-0215's own J-1348→J-1353 chain. **Separately: D-0114** (`antigravity_ecosystem_
  proposals` plan's `contradicts`-harvester defer) **reopened, not re-ruled** — its own defeater
  ("revisit once M2/D-0022 resolves toward live") has fired in substance via D-0287, even though D-0022
  itself was never re-ruled toward live (it only ever approved M2's shadow build); `contradicts` itself
  is untouched and still genuinely 0-yield (F-0500 gap #3). F-1983; J-1415.

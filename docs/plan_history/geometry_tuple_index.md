# geometry_tuple_index — folded history


---

# History folded on 2026-09-27 from `docs\staged\geometry_tuple_index.md` (by hand, J-1484)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py geometry_tuple_index`._

**2026-09-23 (J-1235, F-1736/F-1737) — 2026-09-23 evidence sweep: the six GATE-MET+UNREAD citations
plan-liveness reported (F-1732) against a "210-row bar" are a parsing false positive, not a real
per-file threshold; D-0107's P1 build independently re-verified correct at 2.65x scale; P2 spawned.**
Checked directly, not assumed (F-1736): this document states no per-file row-count promotion bar
anywhere for any of the six flagged evidence logs (`geometry_tuples.jsonl`, `moments.jsonl`,
`provenance_log.jsonl`, `investigative_action_log.jsonl`, `provenance_preassess.jsonl`,
`epistemic_stageb_shadow.jsonl`). Running `plan_liveness.py`'s own `parse_threshold()` against this doc
shows the "210" comes from its regex matching the substring "210+ rows" inside "...moments.jsonl
(128MB, **14,210**+ rows)..." in §1 DIAGNOSIS (a few lines below) — a plain description of
`moments.jsonl`'s own current size, not a target bar, where the thousands-comma in "14,210"
accidentally truncates the match to its trailing three digits. The doc has no "What we need"/"What
we're doing next" section, so the parser falls through to a whole-document fallback and applies that
one spurious number to every evidence file the plan cites — six files, one shared scalar, none of them
actually gated by it. The same "210" already sits inside D-0107's own ruling text (2026-09-01, sourced
`plan-liveness:2026-09-02`) — D-0107 remains substantively sound regardless, since its real cited
rationale was the P0 precedent being live-killed plus the D-0060 rebuild prerequisite clearing, not
this figure. Re-checked D-0196 and D-0107 against their own defeater text (`decide.py show`): neither
is touched by the fresh row volume — D-0196 was already fully characterised and shelved below
(F-1251/F-1294, a chance-level classifier isn't rescued by more data), and D-0107's defeater concerns
P0-generalisation / the still-open §2.6 Keys question, not row counts. No `/decide` opened — nothing
here is a real undecided founder question.

Separately (F-1737), read-only re-ran P1's own build/verify logic (no write under `C:\Nascence\data`,
per this job's ground rules while Du is live) against the live, now-82,397-row `geometry_tuples.jsonl`
(2.65x growth since the 31,111-row build): point-query correctness still **100.000% (82397/82397)**,
P1's own hard bar, still met at materially larger scale, first read-back since the original build.
Weather transitions 248→317 (+69), ratio 0.0080→0.0038 (weather changes proportionally less often as
history accrues). The on-disk sidecar (still describing the original 31,111-row snapshot) re-verified
100% correct for the historical rows it covers — the additive-only guard held — but was not refreshed
(would require a `data/` write this job must not make); low priority since nothing live reads this
sidecar and its own completeness marker already self-flags the staleness honestly. Minor footnote: 3 of
82,397 rows have a non-monotonic `ts` (doesn't affect the correctness result). **J-1238 spawned** to
actually run P2 (§5's real-consumer-baseline evaluation against what P0/P1 deliver) — P1's continued
correctness at scale makes this a well-founded next step nobody had picked up yet. S-0171 filed
separately (not fixed here): `plan_files_audit.py`'s `extract_refs()` also mis-cites `docs/job_queue.jsonl`
as an "evidence file" for this plan purely from a passing §11 mention.

**2026-09-11 (J-0838, D-0196, F-1251) — pre-onset tangent-velocity signal characterised: SHELVED.**
D-0196 (travis, 2026-09-09) ruled "characterise first" on F-0932's claim that Du's step velocity across
(tension, energy, valence, arousal, level) is elevated 1-3 steps before a fresh `unresolved` onset. The
per-instance characterisation (`scripts/pre_onset_velocity_characterisation.py`, lab report
`docs/lab/pre_onset_velocity_characterisation_2026-09-11.md` + `_idle_only.md` + the
`_all_source_composition.md` addendum from `scripts/pre_onset_velocity_composition_check.py`; theta fit on
the first 28 of 40 UTC days, everything reported on the last 12) found **no usable operating point and
retracts F-0932's lead claim as a source-interleaving artefact**: `unresolved` is only written by the idle
loop (`core/geometry_census.py::snapshot(unresolved=None)`; the one caller passing it is
`nodes/inner_monologue_node.py:5271`), every other source writes null, which F-0932's script coerced to
False — so 99.7% of its "onsets" have a non-idle row at t-1, and "velocity > 0" (the best theta for every
velocity definition was 0.0) just means "not inside a `reading` stretch", where 92% of rows carry a vector
identical to the previous one. On idle rows alone (the only real labels) every velocity is at chance
held-out (ROC-AUC 0.486–0.493 at k=1..3, precision at any fixed recall = base rate, F-0932's population
difference reverses sign or vanishes). D-0196's bar (P ≥ 0.5 at R ≥ 0.3 held-out) is touched only where
the positive base rate itself is ≥ 0.45 and always-fire already meets it. The defeater's *shelve* branch
applies; D-0196 is not reopened; no gauge, shadow gauge or trigger. `moments.jsonl` carries no resolution
label and contributes nothing here. Follow-ups spawned from F-1251: J-0893 (re-check F-0932's separate
contemporaneous-drop claim idle-only with null masked, patching the UDMS script) and J-0894 (why reading
tuples carry a frozen vector — legitimate static state or a stale-cache data-quality bug; may explain
F-0419's 37.1% duplicate vectors).

**2026-09-12 (J-0893, F-1294) — F-0932's SECOND (contemporaneous) claim re-checked idle-only,
null-masked: ALSO RETRACTED, reversed rather than merely unconfirmed.** `C:/UDMS/scripts/analyze_nascence_geometry_manifold.py`
patched: `unresolved=null` rows now masked out of every label-conditioned comparison instead of
coerced to False, plus a `--source` option mirroring `pre_onset_velocity_characterisation.py`'s own
idle-only filtering. Re-run (`--source idle`, 29,300 idle rows, 41 UTC days) using that reference
script's own three velocity definitions (raw / fit-standardized / adaptive) found NOT the claimed ~2x
drop ("0.038 vs 0.078", "0.444 vs 0.468") but mostly the OPPOSITE direction — velocity slightly
*higher*, not lower, during unresolved rows — in the single-split held-out view, 3 of 4 walk-forward
folds, and the adaptive view (gaps +8–21%, Cohen's d 0.02–0.08, rank-biserial 0.02–0.07, all small).
Only 1 of 4 fold/score views matched the original drop direction, and it was negligible and only
marginally significant. Held-out-day replication (12 days) found a drop on just 4/12 days; the 3
individually-significant days all showed a *rise*. A secondary all-source cross-check (same
null-mask, no source filter) also failed to reproduce a stable drop, and exposed a second,
independent source-interleaving problem: an all-source velocity diff lets an idle row's step be
measured against a preceding *non-idle* row, not the previous idle tuple — confirming `--source idle`
(filtering rows before any diff is computed, not just masking the label) is doing real methodological
work of its own, beyond the null-mask fix. **Both of F-0932's claims — lead (F-1251) and now
contemporaneous (F-1294) — are retracted.** No follow-up job spawned: effect sizes throughout are
uniformly small-to-negligible and inconsistent in direction across folds/days, the same
non-signal verdict D-0196 already reached for the lead half; chasing a sub-Cohen's-d-0.1 wobble
further was judged not worth a dedicated job.

**P1 built and verified this session (D-0107: "authorize P1 build"), F-0600.**
`scripts/geometry_tuple_p1_run_transition_index.py` builds the pilot run-transition index over
`geometry_tuples.jsonl`'s `weather` field, exactly to §6's original scope (additive sidecar, source
untouched, 100% point-query correctness required) — the event-sourcing shape (§6's framing
correction: store transitions, not per-row snapshots), NOT the separately-explored wave-fit
`ts→row-position` compression (F-0278) — that stays a documented refinement, not built.

- **Real run against the live 31,111-row `data/geometry_tuples.jsonl`** (grown from the 17,331-row
  count at the 2026-08-24 benchmark): 248 transitions found (ratio 0.0080 — in the same range as
  §6's 0.0118 estimate on the smaller dataset; weather changes are genuinely rare relative to row
  count). Sidecar written to `data/geometry_tuple_index_sidecar/p1_weather_transitions.json`
  (20,173 bytes) — a JSON object with a completeness marker (`source_row_count`, `source_mtime`)
  plus the transition list, written atomically (temp file + rename) per the crash-consistency guard.
- **Point-query correctness: 31111/31111 = 100.000%**, checked against EVERY row's own `ts`/`weather`
  pair (not sampled) — the spec's own hard bar, met exactly.
- **Additive-only guard verified, not just claimed**: the source file's mtime, recorded in the
  sidecar at build time, was re-checked immediately after the run and matches exactly — the source
  was never written.
- **Benchmark (bonus, matching P0's own benchmarking style)**: 500 random timestamp point-queries,
  full linear scan (8082.8us/query) vs. the transition-index binary search (1.4us/query) — 5855x
  speedup. Expected and unsurprising given the low transition ratio; not the interesting number here
  (correctness and the additive guard are) but recorded for completeness.
- **What this does NOT do**: does not touch `moment.py`, does not wire into `orchestrator.py` or any
  live cycle, does not extend to any field beyond `weather`, does not implement the wave-fit
  compression (F-0278) or P1.5 (Time × Knowledge transitions, still designed-only). P2 (evaluate the
  6 real consumers against what P0/P1 actually deliver) has not been run.

**P1 moved designed → ready this session (J-0334, per D-0060's ruling).** D-0060 (ruled 2026-08-28)
required the §7 World-truth-source guard's rebuild before any phase could move off designed; the
evidence gate itself had already cleared (23227/15935/1389/777/334/331 rows across the six named
logs, plan-liveness 2026-08-28).

**The rebuild, done:**
- `scripts/geometry_tuple_fragment_vectors.py` (new) extracts a real vector from `fragment_context`
  (SQLite, `data/memory/nascence.db`) — rows with `source LIKE 'experienced:%'` only (excludes the
  legacy `census_world:%` rows the same table also carries) — instead of the raw
  `geometry_tuples.jsonl` world-truth stream F-0269/F-0275/F-0278 were built directly on (F-0282).
  Writes a sidecar CSV + ground-truth JSON under `data/geometry_tuple_index_sidecar/` (additive-only
  guard: source DB/JSONL untouched).
- **Real, verified, load-bearing gap found doing this (not guessed around)**: `fragment_context`'s
  `arousal` column is NULL on 0/7,733 real experienced rows. Traced to `core/memory/store.py`'s
  fragment-write hook (~line 436) — the fallback affect dict built outside a live `CognitiveState`
  (`{"valence": ..., "level": ...}`) never sets an `arousal` key, so `aff.get("arousal")` is always
  `None` regardless of origin. This means the original 8-D affect vector (F-0269/F-0275's own
  benchmark input) **cannot** be reproduced from `fragment_context` as it stands today — a real,
  separate, live-code bug, spawned as its own follow-up job rather than papered over here (see
  job-queue). The rebuild instead uses the three real numeric fields `fragment_context` actually
  carries at 100% coverage for experienced rows: `valence`, `level` (Bachmann's L — not the same
  field as the missing circumplex `arousal`), `warmth`.
- Both benchmark examples (`engine/oxibonsai/crates/oxibonsai-runtime/examples/geometry_bench.rs` and
  `geometry_bench_true_hnsw.rs`) repointed at the new sidecar files and rerun for real, live numbers
  against the correctly-scoped data (7,722 experienced rows, 3-D valence/level/warmth):
  - True HNSW (hnsw_rs, ef_construction=200, ef_search=64): build 0.614s (7,722 nodes), query mean
    0.0325ms, **recall@10 mean 0.748, min 0.000**.
  - Rust linear scan (same-language baseline, exact by construction): query mean 0.2659ms,
    **recall@10 mean 0.827** against the ground truth (not 1.000 — real ties in a 3-D space with many
    near-duplicate rows produce genuine top-k order disagreement between numpy's and Rust's sort,
    not a bug; noted honestly rather than smoothed over).
  - Not directly comparable to F-0269/F-0275's original 8-D numbers (different data source and
    dimensionality) — the point of this rerun is confirming the *pattern* (extract → build → query)
    works end-to-end against the correct epistemic layer, not reproducing the old benchmark's figures.

**What this does NOT resolve**: the arousal gap above. Any future P1.5/HNSW work wanting the real
circumplex arousal dimension needs that write-path bug fixed first — tracked separately, not blocking
this rebuild or P1's designed→ready move (D-0060's defeater: "...unless the rebuild surfaces a new
blocker" — assessed as a real gap worth a dedicated fix, not a blocker on THIS prerequisite, since a
genuine 3-D substitute was available and used).

**Fixed 2026-08-29 (J-0366, F-0443).** `core/memory/store.py`'s fallback affect dict (the
`if not aff:` branch just above line ~541, hit on every `store_fragment()` call since `state` is never
passed to `geometry_census.snapshot()` at that call site) now sets `arousal` too, sourced from a new
`core/mood.py::current_arousal()` accessor — added mirroring the existing `current_valence()` pattern
exactly (same `_cache_scalars()` cache, same live `AffectState`/`EmotionOutput` object, same freshness,
populated by the same `orchestrator.py` call sites that already keep `current_valence()` fresh:
`_mood.observe(self.state.emotion)`, `_mood.recache_grounded_scalars(self.state.affect)`,
`_mood.update(self.state.affect)`). Deliberately **not** an alias of `arousal.level()` (Bachmann's L,
global activation) — that is a different signal already correctly mapped to the `level` column;
conflating the two was the wrong fix and explicitly ruled out (see J-0366's briefing).
Verified via an isolated test against a scratch copy of `data/memory/nascence.db`
(`store.DB_PATH` monkeypatched to the copy — live DB never touched): before the fix, 7,733/7,733
experienced rows had `arousal IS NULL`; a fake `AffectState`-shaped object with `arousal=0.62` fed
through `mood._cache_scalars()` then `store.store_fragment()` produced a new `experienced:lived` row
with `arousal=0.62` written correctly, while all 7,733 pre-existing rows remained unchanged/NULL (no
backfill attempted — `geometry_tuples.jsonl` carries no `fragment_id`, only `ts`, so a historical
backfill would need inexact nearest-timestamp matching; left as a separate, explicitly out-of-scope
follow-up rather than done via approximate joins against a live table). New/future experienced rows
written from now on carry a real circumplex arousal value. See F-0447 for the full before/after
evidence.

**Fixed 2026-08-29 (J-0331, F-0419/F-0461).** J-0366/F-0447 above fixed `fragment_context`/
`world_context` (the SQLite tables) but not the actual `geometry_tuples.jsonl` file this whole document
is built on — `core/geometry_census.py::snapshot()` writes its JSONL row to disk *before*
`core/memory/store.py`'s `store_fragment()` ever patches its local `aff` dict, so the five source
types routed through that call site with no live `state` (`inner_thought`, `subconscious_synthesis`,
`active_imagination`, `reading`, plus every other non-node origin) were still writing `affect: null`
into `geometry_tuples.jsonl` itself — the same file F-0419 traced the 37.1%-duplicate-vector
measurement artifact to. Root cause confirmed by direct read of `core/geometry_census.py::_affect()`
(`state=None` at that call site -> returns `None`, unconditionally) and by reading real rows at
`data/geometry_tuples.jsonl:13428-13434` (`subconscious_synthesis`/`inner_thought` rows both show
`"body": null, "affect": null` even after J-0366 landed). Fix: extended J-0366's exact pattern one
layer earlier — `core/mood.py` now caches the FULL 8-dim scalar affect dict (`_current_affect`,
`current_affect()` accessor, alongside the existing `current_valence()`/`current_arousal()`) in
`_cache_scalars()`; `core/geometry_census.py::_affect(state=None)` falls back to
`mood.current_affect()` when there is no live `CognitiveState`, instead of returning `None`
unconditionally. Verified in isolation (a temp-pathed `_LOG`, live `data/geometry_tuples.jsonl` never
touched): with the mood cache warmed from a fake affect object, `snapshot(source="inner_thought")`
(no `state` arg, exactly how `store_fragment()` calls it) now writes the real 8-dim affect dict
instead of `null`. **Body remains honestly null for these origins** — unlike affect, `SomaticState`
has no module-level live cache anywhere in the codebase (it lives only as
`orchestrator.self.state.somatic`, mutated in place); building one would mirror `mood.py`'s pattern
but touches `core/orchestrator.py`'s hot cycle too, and was judged out of this job's scope — documented
inline in `core/geometry_census.py::_body()` rather than silently left unexplained. See F-0461 for the
full evidence and the spawned follow-up job for the body-side gap.

**Fixed 2026-08-29 (J-0380, F-0461's follow-up).** Closed the body-side gap the entry above left open,
without touching `core/orchestrator.py`'s hot cycle at all. `core/somatic.py` now carries a
module-level `_current_body` cache + `current_body()` accessor mirroring `core/mood.py`'s
`_current_affect`/`current_affect()` pattern exactly. Rather than calling the cache-refresh from inside
`orchestrator.py` (the originally-scoped-out approach, which would have added a call at the hot-cycle
call site), the refresh (`_cache_body(self.state)`) was placed **inside `SomaticEngine.tick_cycle()`
and `SomaticEngine.recover()` themselves**, at the exact line each already mutates its own state in
place — confirmed via grep to be the *only* two mutation points for `self.state.somatic` anywhere in
the codebase (`orchestrator.py` only calls `self.somatic.tick_cycle(...)` and `self.somatic.recover(...)`;
nothing else writes to a `SomaticState`'s fields). This guarantees the cache can never go stale
without adding a single line to `orchestrator.py` — lower risk than the originally-scoped approach,
same freshness guarantee. `core/geometry_census.py::_body(state=None)` now falls back to
`somatic.current_body()` the same way `_affect()` falls back to `mood.current_affect()`. Verified in
isolation (a temp-pathed `_LOG`, live `data/geometry_tuples.jsonl` and the live orchestrator/DB never
touched): before any tick, `current_body()` is honestly `None` and `_body(None)` returns `None`; after
a bare `SomaticEngine().tick_cycle(...)` call, `current_body()` returns real `{energy, fatigue,
tension}` scalars and `_body(None)` returns the same dict; `recover()` refreshes it too; a live-`state`
call to `_body()` is unaffected (still reads the live object directly, never the cache); and a full
`snapshot(source="inner_thought")` call (no `state`, exactly how `store_fragment()` calls it) wrote a
non-null `body` dict for the first time. `git diff --stat` confirms `core/orchestrator.py` has zero
changes — only `core/somatic.py` and `core/geometry_census.py` were touched. See F-0461-follow-up
finding for the full evidence.

**2026-09-23 (J-1238, F-1749) — P2 run for the first time: none of the 7 real consumers are served by
P0/P1 today, confirmed against each plan's own current text, not the 2026-08-24 section-5 snapshot.**
P0 is killed (documented negative result) and P1's whole delivered scope is a single-field
(`weather`) transition sidecar over `geometry_tuples.jsonl` — nothing any of the 7 consumers' named
gaps need. Real nuance found doing this read: 3 of 7 gaps (`channels_programme.md`/D-0033's
cross-channel attribution, `lane2_the_witness.md`/D-0035's hint-queue vocabulary,
`memory_multiway_linking.md`/D-0022's M2 edge-weighting signal) have since been substantially
addressed — but by mechanisms fully independent of this document (`core/channel_arbitration.py`,
lane2's own reject-reason instrumentation, `core/memory_edges.py`/`core/spring_ledger.py`
respectively), not by anything P0/P1 built. The other 4 (`transport_manager.md`,
`factory_candidates_from_history.md`, `emotion_rethink.md`, `emissary_lane2.md`) remain exactly as
unserved as section 5 originally found. No new founder question opened — the verdict is confirmatory
of §7's existing activation guard (P1.5/Keys/HNSW all still designed-only), and P2's own scope is
verdict-only, no plan surgery. Separately, a stale-hold inconsistency was noticed on `emotion_rethink.md`'s
D-0029 (its 2026-08-23 Hold, waiting on "the incoming plan" — this document — landing, was never
reopened the way D-0022's textually identical hold was via F-0321) and spawned as its own follow-up
(J-1247) rather than acted on here. Full evidence: F-1749.

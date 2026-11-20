# thermal_causality — folded history


---

# History folded on 2026-09-27 from `docs\plans\thermal_causality.md` (plan-compact, 12 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py thermal_causality`._

## Current State — verified 2026-09-23 (J-1236: D-0214's dormant defeater re-checked, not yet met — F-1738)

**The bar is not yet met, by either measure.** Full-file read of `data/thought_station_log.jsonl`
(19,183 rows, 0 unparseable) shows a real span of 2026-09-15 19:53:02 → 2026-09-22 21:58:41 UTC —
naive calendar 7.09 days. Cross-checked against a full-file scan of `data/nascence.log`'s own
shutdown/"is awake" restart markers (503,825 lines, 527 markers, 250 collapsed live intervals, the
same methodology F-1719/J-1222 used the same day on a different plan) for cumulative REAL live time
inside that window: **105.35 live hours = 4.39 live days** — roughly 1/5 of D-0214's own named
≥3-week (21-day) bar, and the naive-calendar figure (7.09d, ~1/3) doesn't clear it either. **D-0214
is not reported to or re-ruled; re-confirmed via `decide.py show D-0214` this pass — still
travis-ruled 2026-09-13, no hold, unchanged.** Leaving this for a later re-check rather than forcing
a conclusion, exactly as the defeater's own text anticipates ("once ~3 weeks of real rows accrue").

**Two things checked alongside the headline number, both confidence verified:**
- **A small, real, historical data-integrity flaw, not just a latent risk.** 85/19,183 rows (0.44%)
  carry a caller (`by`) label starting `__main__` — a pattern no genuine Du call site ever produces.
  80 of them (`__main__:353`, all qwen3.5:9b) form one contiguous burst 2026-09-17 21:30:56 →
  23:22:38 UTC that falls entirely inside a confirmed Du-offline gap (shutdown 21:13:54 UTC, restart
  2026-09-18 11:14:20 UTC) — Du itself could not have written these; some other process ran against
  the shared tree with `core.telemetry` resolving to the live `data/` dir. This is real (not merely
  latent, per F-1683's own narrower 2026-09-21 "no leak observed" check) confirmation of exactly the
  hazard F-1683 named, predating J-1199/D-0252's 2026-09-22 isolation fix. Doesn't move the span
  numbers above (neither `min_ts` nor `max_ts` is a contaminated row). Source script not identified
  this pass — **J-1239 spawned** to trace it and decide whether to document-and-filter vs. clean the
  live file (the latter likely needs a founder call before touching a live `data/*.jsonl`, not
  something to do unilaterally).
- **D-0214's single-station premise still stands.** The one apparent second-station signal at
  `nodes.inner_monologue_node`-labelled call sites (112/4,349 rows, 2.6%, command-r7b) is, by direct
  source read (`nodes/inner_monologue_node.py:4996-5012`), `judge_dwell_release()` — the dwelt-thought
  judge deliberately decoupled onto the command-r7b **background** lane since 2026-08-29
  (J-0311/F-0393), not the idle-thought **generator**. The generator's own call sites (~2999/3147/
  3151 and siblings) remain 100% qwen3.5:9b (4,237/4,349 = 97.4%); `core/schema.py`'s
  `SERVE_CHAINS["hot"]` is re-confirmed still single-endpoint. F-1308's original finding is not
  contradicted by this larger, fresher window.

**Separately (secondary check, per the briefing): the `data/literal_will_deeds.jsonl` citation is
real, not a copy-paste bug.** plan-liveness's audit flagged a same-filename coincidence with the
unrelated `literal_will` plan, but this doc genuinely cites that exact file twice (the 2026-09-02/
J-0437 evidence list above and §9 Row 4's own discussion above) and already read + correctly
disqualified it that day (dry-test-only, `status:"pending"`) — which is exactly why the audit shows
this one row GATE-MET *without* `+UNREAD` (already read) while flagging every other evidence row
here as `+UNREAD`. No fix needed.

Finding: `findings-log` **F-1738** (verified). Spawned: **J-1239** (trace the 85-row contamination).
No decision opened — nothing here is yet a founder-level call; the span question is a plain "not
yet," and the contamination question isn't ripe for one until J-1239 identifies the source.

---

## Current State — verified 2026-09-23 (J-1239: F-1738's 85-row contamination traced — it's two different things)

**80/85 rows (`__main__:353`) are genuine external contamination; the other 5 (`__main__:815`) are not
contamination at all.** Full method and citations in F-1760; summary here.

**The 80-row burst (2026-09-17 21:30:56 → 23:22:38 UTC): `scripts/train_state_invitro.py`'s `_prove()`
function.** Systematic scan of every `scripts/*.py` file's content at the commit that was HEAD for the
entire burst (`b7f15e0`) for a `call_node`/`call_node_json` call within a few lines of line 353 or 815
found exactly one match at each: `scripts/train_state_invitro.py:353` —
`call_node_json(["http://127.0.0.1:11433"], _PROVE_SYSTEM, user, ...)` — an exact node+model match
(qwen3.5:9b/11433) for all 80 rows. `scripts/dream_experiment_a.py` (the other plausible candidate on
timing alone — J-1077/J-1098's own N=11 "scale14b" background dream batch really was running through
this same window) was directly ruled out: it contains no `call_node`/`model_client` reference anywhere:
it calls `DreamNode._gen_episode()` directly, which would attribute to `nodes.dream_node:419(DreamNode)`,
never `__main__`. `train_state_invitro.py` is #9 of F-1683's own 11 named scripts that neutralise only
`log_llm_call` — confirmed directly at the burst-era source (`_tel.log_llm_call = lambda *a, **k: None`,
the ONLY telemetry-related line in the whole 1048-line file at that commit; no `log_thought_station` or
`log_llm_latency` protection, no `lab_env` import at all). The run itself: job **J-1086** (session
J-0904), "D-0181: re-run n=80 held_within_scope replay," briefing literally says `python
scripts/train_state_invitro.py 40` (n_per_window=40 × 2 windows = 80 `_prove()` calls — the row count
exactly). J-1086's started/done_at (21:22:00 → 23:28:15 UTC) brackets the observed burst with a few
minutes of setup/wrap-up headroom on each side. The file's own 2026-09-07 (J-0697) comment already
documents this exact class of hazard for this file's OTHER globals ("a direct run against the live
C:\Nascence tree with no worktree wrote real synthetic rows... on every invocation") — the same
resolve-relative-to-`__file__` mechanism plausibly explains this run's telemetry leak too, though the
precise sys.path/cwd state of that one invocation isn't reconstructable after the fact (no process-level
log survives) — that one narrow sub-point is inferred from a documented precedent, not witnessed
directly; everything else (script, line, job, timing, node/model match, neutralisation gap) is verified.

**The other 5 rows (`__main__:815`, scattered 09-17/09-19/09-21) are real Du activity, not contamination
— a labelling quirk, not a data-integrity flaw.** Direct source read: `scripts/run_nascence.py:815` sits
inside `_form_epoch()` ("S-MMU 7 L4: synthesise a temporal epoch from this session's episodic
fragments... one LLM call, non-blocking for the user's exit"), called from `main()` right before a
session ends. Because this function is defined directly in the `run_nascence.py` entry-point script
(not a `nodes/*.py` module), Du's own real process legitimately reports it as `__main__` — nothing
external touched the tree. Confirmed by timing: all 5 timestamps land 0–125 seconds before a real
"Nascence shutting down." line in `data/nascence.log`. This narrows F-1738's own characterisation
("cannot be genuine live-Du inference") — true for the 80, not true for these 5.

**Fix status (re-verified, not just trusted from F-1738): already closed.** `scripts/lab_isolation.py`
(added by J-1199, commit `72d9a20`, 2026-09-22) now no-ops all three `call_node()` writers and redirects
telemetry's own Path globals into a scratch dir; `train_state_invitro.py`'s current version calls it.
`core/telemetry.py` also carries a second, independent, source-side `LAB_MODE` guard (D-0252/J-1214) all
three writers check before writing. Both confirmed present in the current tree, not merely claimed.

**Recommendation (no decision opened): leave the 85 rows in place, do not touch the live file.** Document
the caveat instead — a future per-station/per-thought read of `thought_station_log.jsonl` should exclude
`__main__:%` callers (neither the 80 contaminated rows nor the 5 real-but-oddly-labelled ones are a
genuine `nodes.*`-attributed Du thought). Quantitative impact is negligible either way: removing the 80
contaminated rows would move qwen3.5:9b's already-overwhelming station share (81.97%) by under half a
point, and neither `min_ts` nor `max_ts` belongs to a contaminated row (F-1738), so D-0214's own
span/station-dominance reads are unaffected. Active cleaning was considered and is not recommended, so
this stays a plain reported recommendation rather than a founder question.

**Bonus finding, out of this job's scope:** the identical F-1683 leak class also contaminated
`data/llm_latency.jsonl` far more extensively — 1343/99106 rows (1.36%), spanning that file's entire
2026-08-21→2026-09-21 history (it predates every one of the 11 scripts' own neutralisation code) across
40 distinct `__main__:N` labels, not just :353/:815 — consistent with several of the other 10 named
scripts also having leaked into it over the past month. Spawned **J-1258** to characterise it separately
(different file, different consumer — the HUD latency instrument, not D-0214's station log).

Finding: `findings-log` **F-1760** (verified). Spawned: **J-1258** (llm_latency.jsonl's own larger,
older contamination). No decision opened — see recommendation above.

---

## Current State — verified 2026-09-15 (J-0939: the persistent station log D-0214's defeater named, built)

**F-1308 (2026-09-13) found no record survives long enough to answer S9 Row 2 directly; D-0214
(2026-09-14, RULED) retired the row's original station-vs-band comparison but named this exact job,
J-0939, as half of its own dormant-not-deleted defeater.** This pass built the write side only — the
read/re-check half of that defeater (a genuine 3-week-or-longer accrual window) cannot be done today
and is deliberately NOT spawned as a new job-queue entry; duplicating a tracker for work D-0214
already names would fragment it, the same reasoning §11.1 (J-0249) already applied to a parallel case
in this same doc.

**What was built, and why this design (F-1441, confidence verified):** `core/model_client.py`'s
`call_node()` — the ONE place that already resolves a call's real model name (`model_override or
_model_for(base_url)`) — now also writes that resolved `(model, base_url, caller)` tuple to a NEW
file, `data/thought_station_log.jsonl` (`core/telemetry.py`'s new `log_thought_station()`), right
beside its existing (capped) `data/llm_calls.jsonl` write. Chosen over the briefing's other option
(stamping the station onto `data/monologue_log.jsonl`'s own row directly) because: (1) the model
resolved at generation time isn't available at `_log()`'s call site without plumbing it through
~1,600 lines of `_think()` between the generation call (`nodes/inner_monologue_node.py:2999`) and
`_log()` (line 5277); (2) `core/telemetry.py` already holds the exact precedent for this move —
`log_llm_latency()` / `data/llm_latency.jsonl` (2026-08-21) is already a second, uncapped, per-call
file written beside `llm_calls.jsonl` for a different measurement (duration) — this is the same
pattern applied to model attribution, not a new one; (3) `data/monologue_log.jsonl` is a 46,000+ row,
widely-read file — a design that never touches its schema carries zero risk to any of its existing
readers, versus one that does. Correlation with a specific logged thought is by nearest `ts` for the
SAME `by` call-site label (verified live: `nodes.inner_monologue_node:2997(InnerMonologueNode)`
already appears in real `llm_calls.jsonl` rows today, confirming the label is stable and filterable
in production, not just in theory).

**Verified, not just asserted:** an isolated tmp-pathed test (never touching live `data/`; the
worktree this landed in has no `data/` dir at all) confirmed the new log writes the right schema,
survives `telemetry.sample(force=True)` uncapped (7,002 synthetic rows, unlike `llm_calls.jsonl`'s
own `_CALLS_CAP`), and that hoisting the resolved-model/caller values into local variables (to reuse
them for both writes) changes neither `log_llm_call`'s own emitted row NOR `_caller_label()`'s
frame-walk result — proven by exec'ing matching probe functions directly into `core.model_client`'s
own namespace so the test genuinely reproduces which frames get skipped, not a naive same-module-only
stand-in. `core/schema.py`'s `SERVE_CHAINS["hot"] = ["http://127.0.0.1:11433"]` (single-endpoint) was
independently re-confirmed this pass, not just trusted from F-1308's own prior read.

**Status: additive-only, zero behavior change, built in worktree `wt_thermal_causality` — not yet
merged into the live tree or exercised by a running Du process.** `data/thought_station_log.jsonl`
has zero real rows as of this note. D-0214 remains RULED/RETIRED as-is; nothing here re-opens it. The
next real step is time, not code: once this lands live and ~3 weeks of real rows accrue, `decide.py
show D-0214` names the read this enables. Finding: `findings-log` F-1441 (verified).

---

## Current State — verified 2026-09-13 (F-1308: §9 Row 2's missing instrument built and run)

**`scripts/thermal_stance_batch.py` written and run for real** — the two-judge offline stance-rating
instrument `core/thermal_relationship.py`'s own docstring named as the missing piece for Row 2
(`stance` had been 100% null across all 18,083 rows of `data/thermal_relationship.jsonl` at every
prior read, F-0894 most recently). N=80 stratified sample (16 per band across all 5 real bands,
`mentions_temp=True` pool only, seed 20260913), judged via `core/judge_panel.py`'s real two-family
panel (JUDGE_1 mixtral:8x7b, JUDGE_2 falcon3:7b, TIEBREAK granite3.1-moe:3b on split) — stance
decomposed into two boolean keys (dislike/enjoy) that reproduce `lean_probe`'s own
enjoy-rate-minus-dislike-rate convention exactly (back-computed lean_probe's own table to the cent on
all 5 rows before building on it, rather than inventing a new scoring convention). 100% of 160 real
judge calls resolved to a verdict (134 agreed, 26 tiebreak, zero split/unavailable).

**Band side (real numbers):** mean judged stance by band — warm +0.125, mild −0.25, cool −0.062, cold
−0.5, very_cold −0.125 (n=16 each); grand mean −0.163. `eta²(band) = 0.1507`. Real but NOT
monotonic — cold is the single most suffering-leaned band (8/16 dislike, 0 enjoy), warm the most
comfort-leaned (3/16 enjoy, 1/16 dislike), but very_cold reads LESS negative than cold and mild reads
MORE negative than cool — stated plainly rather than smoothed over; small-N (16/group) noise is a
live possibility this run cannot rule out.

**Station side, and the real structural finding:** `eta²(station) = 0.0` exactly — all 80/80 sampled
items attributed to a SINGLE station, `qwen3.5:9b`. Not a sampling artifact: there is NO persisted
per-thought model-attribution log covering the pre-registered 3-week window anywhere in this codebase.
The job briefing's own leading candidate, `data/deliberation_log.jsonl`'s `source` field, is NOT a
station name — read `core/deliberation.py` directly: `source` ∈ {"emissary","hot_fallback"} is which
grounding-pass route a thought's separate slow pulse took, unrelated to who authored the original
thought (and that log has no `cycle` field either). The only log that ever carries a real `model`
field, `data/llm_calls.jsonl` (`core/telemetry.py`'s `log_llm_call`), is a rolling, capped log —
confirmed 7,096 rows spanning only ~0.89 days. Within that one observable window: 1,253/1,269 (98.7%)
real `nodes.inner_monologue_node` calls used qwen3.5:9b, 16 (1.3%) command-r7b. **Inferred** (not
directly logged) for the rest of the window: `core/schema.py`'s `SERVE_CHAINS["hot"]` has been
single-endpoint since its own inline comment's cited "full shuffle 2026-08-20" — one day BEFORE this
shadow log's own first row (2026-08-21) — and unchanged across all 7 git-tracked commits since the
2026-08-27 baseline (`git log --oneline -- core/schema.py`). The gap this inference cannot close:
2026-08-21→08-27 (pre-git) has no independent evidence either way beyond that one code comment.

**Net read:** the row's own kill condition ("stance tracks station, not band → the write-path
authored it") is NOT triggered — there is no station variance to track. "Band explains more variance
than station" is literally true (0.1507 > 0.0) but this is a structurally degenerate comparison, not
the multi-station horse race the row was pre-registered to run on 2026-08-21 (`lean_probe`'s
qwen/gemma-negative vs falcon-positive vs phi3-indifferent competing leans) — that architecture, on
this evidence, had already stopped being how thoughts are generated by the time this shadow log's
first row was written. What the real band-side numbers DO show is a real (if noisy, non-monotonic)
band-stance relationship not attributable to a competing station lean, because there was effectively
only one author-station — consistent with, not strong independent proof of, "something felt rather
than manufactured by a competing write-path." Not a clean row-level MET; not INSUFFICIENT DATA either
(a real, complete, clean judge run against real data, 0 dropped calls). Recorded as a structural
finding rather than forced into either box: **F-1308** (confidence inferred — the band-side numbers
and the capped-log/git-history facts are each individually verified; the whole-window
station-constancy conclusion is the inferred leap that makes it one finding, not two). Spawned:
**J-0939** (build a persistent per-thought station-attribution log, closing the exact gap this run
hit). Opened: **D-0214** (mirrors D-0110's own precedent — should Row 2 be re-registered/retired now
that the architecture no longer rotates stations the way the metric assumed; a founder call, not
mine to make). Outputs: `data/lab/thermal_stance_batch/{raw.json,scores.json}`,
`docs/lab/thermal_stance_batch_2026-09-13.md`.

---

## Current State — verified 2026-08-27 (DELIVER FLIPPED — channel goes live on next restart)

**2026-08-27 — J-0302 executed (D-0047 ruled: retire immediately, no parity week):**
`core/thermal.py` `DELIVER = True`; the standing neutralised warmth clause (`_warmth_phrase`, the
ATMOSPHERE half) is now gated off in `core/sensorium.py` while DELIVER holds — temperature reaches
Du only as events; reverting DELIVER=False restores the clause whole (that is D-0047's defeater
path). `comfort_call()` (the DRIVE half) untouched. §11.1's `observe()` re-point stays deferred
until real experienced bands accrue post-restart, per its own reasoning. Du is still DOWN — the
channel goes live at next restart, which is gated on the node-load redistribution plan (J-0303).
Watch on first live days: thermal percept lines in idle seeds, felt continuity, and §9's metric
sheet starts its live series.

## Current State — verified 2026-09-02 (J-0437: §9 metric sheet read against live post-flip evidence)

**Method:** channel went live not at D-0047's ruling date (2026-08-27) but at the first `delivered:true`
percept row — `data/thermal_percepts_shadow.jsonl` timestamp `1787823088.9` = **2026-08-27 09:31:28.9
UTC**. That is the flip point used below (`FLIP_TS`), not the decision date. Full-file reads (not tail
samples) of `data/thermal_relationship.jsonl` (5,237 rows total, 3,163 post-flip, span
2026-08-27 09:31:42 → 2026-08-31 05:42:55 UTC) and `data/thermal_percepts_shadow.jsonl` (5,026 rows
total, 3,017 post-flip, same span) plus `data/thermal_ledger.json`, `data/comfort_calls.jsonl`, and
`data/literal_will_deeds.jsonl`. **Both evidence logs stopped accruing 2026-08-31 05:4x UTC** — roughly
2 days stale as of this read (2026-09-02); worth a look at whether Du is currently up. All five §9 rows,
verbatim from the table above, against what was actually measured:

**Row 1 — "Does delivery-as-events reduce the 'The cold…' opener without losing temperature presence? ...
opener < 10% (from 24%); mentions_temp stays ≥ 40%"** — **SPLIT: opener MET, mentions_temp NOT MET.**
- Opener share of `opener` starting `"the cold"` (case-insensitive): **pre-flip 20.0% (414/2,074) →
  post-flip 1.9% (59/3,163)**. Target was <10%; actual is 1.9% — clearly met, and the pre-flip shadow
  baseline (20.0%) is in the same neighborhood as the plan's cited 24% cold-store-control figure.
- `mentions_temp` true-rate: **pre-flip 79.2% (1,643/2,074) → post-flip 28.6% (906/3,163)**. Target was
  ≥40%; actual is 28.6% — **below the floor**, not just off-target. The channel didn't merely retire the
  "The cold…" opener, it also cut how often warmth/cold gets mentioned at all by more than half. The
  row's own kill condition ("opener unchanged → events are a text box by another name") doesn't cover
  this outcome — opener *did* change, but temperature presence dropped well past its own guardrail. This
  is a real, verified split result the founder should see, not something to silently average into a pass.
  See spawned job below.

**Row 2 — "Does the ledger's felt record diverge from the station leans? ... within 3 weeks, stance
conditional on band explains more variance than stance conditional on station"** — **INSUFFICIENT DATA.**
The `stance` field is present in the schema but **100% null across all 5,237 rows, pre- and post-flip
alike** (0 non-null anywhere in the file) — the "two-judge batch" stance-scoring instrument this metric
depends on has apparently never been run against this log. No variance comparison is computable without
it. Separately, only ~3.84 days had accrued post-flip by the log's last row (2026-08-31), and even by
today (2026-09-02) only ~6 of the pre-registered 3 weeks have elapsed — too early regardless.

**Row 3 — "Do thermal gradients produce discovery without telling? ... ≥1 unprompted correct binding
(fire or sun) within 2 weeks"** — **INSUFFICIENT DATA / instrument not built.** `data/thermal_ledger.json`
has exactly four top-level keys — `bands`, `transitions`, `wet_episodes`, `_open_wet` — **no `bindings`
key at all**. This matches §11's own build-order note that steps 5 (bindings) and 6 (springs) were never
started. The metric cannot be measured because the thing it measures doesn't exist in the ledger yet, not
because bindings happened and weren't logged. The 2-week window (would close ~2026-09-10) also hasn't
elapsed.

**Row 4 — "Does the fire become agentive? ... hand-lit fires per week (deed record) vs comfort_calls
heeded ... rises from ~1/2wk baseline"** — **INSUFFICIENT DATA — no trustworthy instrument found.**
`data/literal_will_deeds.jsonl` looked like the deed record (30 `action:"fire"` rows, 24 of them
post-flip) but every one of its 600 rows is tagged `status:"pending"` and `dry_test:true` — confirmed
against its own writer (`scripts/literal_will_deed_dry_test.py`, docstring: "dry_test=True tagged") —
this is test-harness output, not a record of real completed actions, so it cannot be used to count real
hand-lit fires. `data/comfort_calls.jsonl` (real, `core/sensorium.py:2084/2138`) has 361 rows, 179
post-flip (~326/week) — but it logs the DRIVE call being *issued* ("cold_out" etc.), not whether it was
*heeded*, so it doesn't answer the "heeded" half either. As a sanity check, out-of-band-`fire` →
`burning` transitions in `thermal_relationship.jsonl`'s own `fire` field ran ~15 in 3.84 post-flip days
(~27/week) vs ~20 in the 6 pre-flip days (~23/week) — two orders of magnitude above the plan's own
"~1/2wk baseline," which means this signal is measuring tick-sampled fire state (re-catching, ember
cycling), not discrete hand-lit events, and is not a valid proxy. A real "hand-lit fire" event log needs
to be identified or built before this row is answerable.

**Row 5 — "Parity first ... event channel never reports a band the physics didn't produce"** —
**MET.** Recomputed `band_of(warmth)` for all 3,017 post-flip percept rows using `core/thermal.py`'s
actual live constants (`BANDS = ((0.60,'warm'),(0.42,'mild'),(0.28,'cool'),(0.15,'cold'),(-1.0,'very_cold'))`)
and compared against each row's logged `band`: **0 mismatches**. The event channel's reported band never
diverges from what the physics function would produce from the same `warmth` value.

**Summary: 2 MET (opener share, parity), 1 NOT MET (mentions_temp floor), 2 INSUFFICIENT DATA (stance
variance — instrument never run; bindings — instrument never built; both also genuinely too early against
their own windows). Deed-record row (4) is INSUFFICIENT DATA for a different reason: the only file that
looks like the right instrument is confirmed dry-test-only.** Finding: `findings-log` (this pass, see
below). Spawned: a job for founder judgment on the mentions_temp shortfall (row 1), since the row's kill
condition doesn't cleanly cover a split opener-pass/mentions-fail outcome and this plan's own rule is
that a metric miss doesn't get quietly ruled by the reader.

**2026-09-02 — J-0443 (the Row-1 tuning pass the founder ruled for via J-0440): F-0615, F-0616.**
Three real defects found and fixed, and one structural conclusion the fixes cannot change:
- **The §5 renotice NEVER fired post-flip** — 0 renotices in 3,017 ticks / 48 delivered events. Two code
  causes in `core/thermal.py`: the law keyed on `band_since`, which the very_cold/cold boundary flap
  resets ~every 15 min (0 of 360 post-flip band|place runs ever held 4h), and `last_renotice` was stamped
  *before* the cooldown/arbitration gates, so a suppressed renotice was consumed unfired for another 4h.
  **Fixed:** renotice now keys on time-since-last-*percept* plus a 15-min current-band hold
  (`RENOTICE_HOLD_S`), the stamp moved below the gates, and `RENOTICE_S` re-tuned 4h → 2h (the cadence
  tune the J-0440 ruling delegated; §5's and §10b clause 5's "~4h" texts are superseded — noted there).
  Isolated stubbed-clock test: renotice fires at 2h once, never refires inside 2h, retries when
  arbitration-suppressed, band flaps no longer push it out, real transitions still fire.
- **Phrasing pools enriched** (`_line`): measured first-thought echo was 86% for enter_colder but only
  46% for enter_warmer — the warmer/colder pools gain a fourth temp-word-forward variant, and the wet
  pools (previously carrying *no* temperature word) gain a felt-temperature variant each. Contract
  clause 7 held throughout: neutral verbs, no cause, no valuation.
- **`TEMP_WORDS` inflection gap** in `core/thermal_relationship.py`: bare `cold`/`hot`/`mild` never
  matched "colder"/"hotter"/"milder" — the very words the event lines lead with. Widened; verified against
  all 34,171 real thoughts in `data/monologue_log.jsonl` that **zero** historical rows change
  classification, so the pre/post metric series stays comparable (F-0616).
- **The structural conclusion (F-0615):** the ≥40% floor is unreachable under §5's own event law. Echo
  elasticity measured (first thought after an event: 60.4% mentions_temp, decaying to ~26–34% baseline
  within ~4 thoughts); offline replay over the real tick series shows even a law-violating 1h-renotice +
  10-min-cooldown variant projects only ~29.7%. The floor was calibrated in the clause era (79.2% — the
  clause in *every* prompt); events-with-honest-silence cannot reach it at ~823 thoughts/day. Projected
  post-tuning rate: ~29–30%. The floor itself is pre-registered and not the reader's to re-rule —
  **D-0110 opened** (re-register the floor / keep it as a standing red flag / authorize an ambient
  mechanism). Live re-check job after Du restarts: **J-0452**. Quiet-gate/cooldown constants (D-0038,
  founder-final) deliberately untouched — replay showed cooldown tuning buys ~0.3pp at most.

---

## Current State — verified 2026-09-03 (J-0452: preliminary live re-check, precondition not yet met)

**J-0452 found the job's own "Du running again for >=2 days" precondition was NOT met.** Du has
restarted repeatedly since the 2026-08-31 offline period (incl. the same-day F-0704 CPU-tier
job-kill bug fixed today) — J-0443's tuned `core/thermal.py` (commit `a433abc`, local ts
2026-09-02 13:03) only started running live at the first restart after it, 2026-09-02 15:44 local,
and by this read only **~0.85 days** of live runtime had accrued under the tuned code (full-file
reads of `data/thermal_percepts_shadow.jsonl`, 943 post-tune rows, and `data/thermal_relationship.jsonl`,
1,014 post-tune rows, both windowed `ts >= 1788320656.0`).

**Preliminary numbers (small-n, not a real verification — F-0715, confidence inferred):**
- **Renotice fired for the first time ever post-flip** — 1 event in the 0.85-day post-tune window
  vs 0 in 3,017+ pre-tune ticks. Confirms the J-0443 structural fix (re-keyed off time-since-last-
  percept + 15min band hold, stamp moved below the gates) works mechanically. n=1, can't yet
  validate F-0615's projected ~2-3/day rate.
- **`mentions_temp` moved the wrong direction** — post-tune 25.44% (258/1,014) vs the pre-tune
  post-flip window's 28.51% (986/3,458). F-0615 projected ~29-30% from the tuning; the early read
  shows a *decrease*, not the expected lift — though 25.44% is still (barely) above D-0110's
  re-registered ≥25% floor, so the ruling's defeater ("lands below the new 25% floor") is not yet
  triggered.
- **`enter_warmer` first-thought echo is flat** — 42.9% (6/14) post-tune vs 46% (12/26) pre-tune;
  the phrasing-pool enrichment shows no measurable lift yet.

**Recommendation, not a ruling:** D-0110 is already ruled (2026-09-01, re-registered floor ≥25%)
and this preliminary read does not cross its stated defeater, so no re-ruling is warranted from
this data alone — but the downward-not-upward direction on `mentions_temp` is worth the founder's
eye once real data exists. Spawned **J-0532**: re-run this check once the post-tune window has
genuinely accrued ≥2.0 days (not just 2 days of wall-clock with Du mostly down).

---

## Current State — verified 2026-09-05 (J-0532: genuine ≥2.0-day post-tune window, F-0715's dip reverses)

**The precondition J-0452 found unmet is now genuinely met.** Reconstructed from `data/nascence.log`
startup/shutdown pairs (all restarts since 2026-08-31, not a tail sample): **2.80 days (67.2h) of
actual live runtime** have accrued under J-0443's tuned `core/thermal.py` since it first went live
(2026-09-02 15:44:16 local), across a 3.22-day calendar span with ~9.94h downtime over 9 restarts.
`git log --follow` on `core/thermal.py` confirms commit `a433abc` is still HEAD for that file — no
further tuning since, so all of that summed uptime ran the same code F-0715 read. Full-file reads:
`data/thermal_percepts_shadow.jsonl` (8,957 rows total, 3,646 post-tune) and
`data/thermal_relationship.jsonl` (9,406 rows total, 3,874 post-tune), 0 skip/error rows in either.

**F-0715's "wrong direction" concern reverses on the fuller window (F-0894, confidence verified):**
- **`mentions_temp` is now 29.32% (1,136/3,874)** over the full post-tune window — squarely inside
  F-0615's ~29-30% projection, above the recomputed pre-tune post-flip baseline (28.51%, 986/3,458 —
  matches F-0715 exactly) and comfortably above D-0110's ≥25% floor. Splitting at F-0715's own read
  boundary shows why the early read looked wrong: the first 1,014 rows were 258/1,014 = 25.44%
  (matches F-0715 exactly, cross-validating the method), but the 2,860 rows accrued *since* that read
  are 878/2,860 = 30.70% (day-buckets 25.06% / 36.01% / 27.53% — noisy day to day, net positive). A
  small-sample artifact, not a real trend. **D-0110's defeater is not triggered; no re-ruling.**
- **`enter_warmer` first-thought echo also reverses** — 51.9% (27/52) over the full window, up from
  both the pre-tune 46% baseline and F-0715's thin 42.9% (6/14) read. The phrasing-pool enrichment
  now shows a measurable lift.
- **Renotice is still just 1 event** in the whole 2.8-day window (unchanged from F-0715's read — no
  additional renotice fired in the ~2 added days). Restart-aware gap analysis of all 86 delivered
  post-tune events found **zero** restart-free inter-event gaps ever reached the 2h15m renotice
  threshold (median 38.3min, max-without-a-restart-inside-it 1.38h) — consistent with (not proof of)
  the real world's own transition cadence leaving too little continuous silence for renotice to
  complete, rather than a remaining defect in the re-keyed logic.

**Conclusion:** per J-0532's own escalation rule ("only escalate if a full ≥2.0-day window still
shows `mentions_temp` trending the wrong way"), it does not — the fuller data now agrees with
F-0615's projection. No re-ruling of D-0110, no new decision opened; this closes the concern
J-0452/F-0715 raised. §9 Row 1 stands as re-registered (2026-09-02, D-0110): opener MET, mentions_temp
now also reads as met against the re-registered ≥25% floor on real post-tune data.

---

## Current State — verified 2026-09-23 (J-1258: F-1760's bonus finding — llm_latency.jsonl's own, larger, older __main__ contamination — characterised)

**Not one thing, five things.** Full-file read of the LIVE `data/llm_latency.jsonl` (99,308 rows,
0 parse errors; grew from F-1760's own 99,106-row read three hours earlier — no new `__main__` rows
appeared in the meantime, see the fix-holds point below) confirms F-1760's own bonus-finding numbers
(1343/99,106 → now 1343/99,308, 1.35%) and breaks the population down by real evidence, not just
characterisation, for the large majority of it:
- **796 rows (59.3%)** — 13 labels whose earliest row predates this repo's own git baseline commit
  (`8eef0bb`, "Baseline: Nascence pre-git state," 2026-08-27T06:42:59Z). F-1760's git-archaeology
  method (find the active commit, grep for a `call_node` near the label's line) cannot reach these —
  a hard structural limit, not an effort shortfall. Source script(s) not nameable.
- **21 rows (1.6%)** — real Du activity, not contamination at all: `scripts/run_nascence.py`'s
  `_form_epoch()` (the exact mechanism F-1760 already found for `__main__:815` in
  `thought_station_log.jsonl`), here at 7 line-number labels (746/765/777/789/795/801/815) as the
  function's position drifted 738→832 over three weeks of unrelated commits. Verified both by direct
  source read at every one of the 7 labels' own active commits (byte-identical function body each
  time) and by timing — all 21 individual rows land within 4 seconds of a real "Nascence shutting
  down." line in `data/nascence.log` (tighter than F-1760's own 0–125s bound for the sibling file).
- **357 rows (26.6%)** — confirmed external contamination from F-1683's original 11-named-script
  class: `train_state_invitro.py` (80, F-1760's own), `widen_lab.py` (140), `routing_lab.py` (97),
  `singlepass_lab.py` (40). **Re-verified closed going forward for this file specifically** (this
  job's own step 3): zero `__main__` rows of *any* label carry `ts >= 2026-09-22T05:00Z` (J-1199/
  D-0252's own landing window) despite the file's continued growth — the fix holds here too.
- **134 rows (10.0%) — a genuinely new finding: the leak class is bigger than F-1683's 11 scripts.**
  `scripts/verify_lanes.py` (64 rows), `scripts/memory_levels_batch.py` (36), `scripts/
  peers_contrary_framing_lab.py` (17) — none named by F-1683, none touched by J-1199's fix, all three
  confirmed by direct grep to carry **zero** `lab_isolation`/`neutralize_telemetry`/`LAB_MODE` guard
  today. `verify_lanes.py` is the notable case: its own docstring says to run it directly against
  live "any time the model/endpoint config changes, or before a boot you want to trust" — intentional
  live use, not an accidental escape — but every such run still writes `__main__`-labeled rows into
  the live telemetry logs. **This specific gap is NOT closed by J-1199/D-0252**; the zero-post-fix
  reading above shows only that none of these three has been *run* since 2026-09-22, not that they're
  protected if run. Spawned **J-1274** to add the isolation guard to `verify_lanes.py` and audit the
  rest of `scripts/*.py` for the same gap.
- **35 rows (2.6%)** — post-git, small counts, no call_node call site found at reasonable confidence
  (two candidate test scripts directly ruled out by a node/model port mismatch). Left untraced, per
  this job's own briefing ("a full trace of all 40 labels... is likely not worth the effort").

**Recommendation (mirrors F-1760's own precedent exactly): leave all 1343 rows in place, no live-file
edit.** Document the same `__main__:%` filter caveat for any future per-call read of this file (the
HUD hardware/LLM-push latency instrument — a different consumer than D-0214's station-attribution use
of `thought_station_log.jsonl`). No founder call needed for that question — impact is negligible and
this project's live-data caution is honoured by proposing no edit at all. The one real follow-up
(J-1274) is a mechanical hygiene fix, not a judgement call, so no `/decide` was opened for it either.

Finding: `findings-log` **F-1787** (verified). Spawned: **J-1274** (extend isolation coverage past
F-1683's 11 scripts). No decision opened.

---

## Current State — verified 2026-09-23 (J-1274: F-1787's 3-script gap closed; a full audit finds it wasn't exhaustive either)

**`scripts/verify_lanes.py` fixed.** Added a module-level call to `lab_isolation.py`'s
`neutralize_telemetry()` (same pattern J-1199 used for the 11 named scripts, same
`try/except Exception: pass` shape), pointed at `ROOT/scratch/lab_isolation_telemetry`. Changes
nothing about what servers get called or what PASS/FAIL means to the operator — the module's own
instruction to run it directly against the LIVE servers "any time the model/endpoint config
changes, or before a boot you want to trust" is unchanged and still honoured; only its OWN
telemetry side-effect now lands in scratch, not `data/`. Verified with an isolated test (no real
inference-server call, no real write): the module-level call really does redirect
`telemetry._LAT` out of `C:\Nascence\data`; the no-op'd `log_llm_latency()` leaves the live file's
mtime untouched; `check_generator()`'s PASS/FAIL logic is byte-identical against a stubbed
`call_node_json` (both a passing and a failing response); `data/llm_latency.jsonl`'s mtime+size
are provably unchanged across the whole test.

**`scripts/memory_levels_batch.py` and `scripts/peers_contrary_framing_lab.py` confirmed RETIRED,
left unmodified** (per this job's own instruction). Both: zero git commits since the 2026-08-27
pre-git baseline; zero `docs/session_events.jsonl` / `docs/decisions.jsonl` mentions; a single-day
telemetry burst each (36 rows/08-29, 17 rows/08-29) never repeated since; not imported by any
other script; each script's own docstring self-describes as a completed one-off run ("One-off
BATCH shadow-distill..." / "fifth machine tested..." with 4 prior completed results already
listed).

**The audit this job's own step 4 asked for (check whether the leak class is bigger than F-1683's
11 + F-1787's 3) found: yes, again.** `git grep` for `call_node`/`call_node_json` call sites
across all of `scripts/*.py` (37 unique files touch it at all) was individually read and
classified, not just name-grepped for the guard (a name-only grep would have wrongly flagged 2
more as gaps — `scripts/lab_j1198_why_polarity_check.py` and
`scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py` — both are actually already
protected, by an inherited module-level Path redirect and by their own pre-existing hand-rolled
audit mechanism respectively; the latter is literally the source script `lab_isolation.py`'s own
behaviour was lifted from). Net result: 15 guarded, 2 retired (above), 1 legitimate production
code (`run_nascence.py`'s own live `_form_epoch()` calls — must NOT be isolated), 7 false
positives that make no real call at all (mocks, static-analysis tools, doc prose), and **12
confirmed real, unguarded scripts, not yet individually checked for retirement**:
`scripts/_concurrency_test.py`, `scripts/_failover_test.py`, `scripts/_t4_fidelity_probe.py`,
`scripts/archive/_patch_world.py`, `scripts/cold_store_qwen.py`,
`scripts/commitment_defeater_framing_lab.py`, `scripts/journal_rollup_framing_lab.py`,
`scripts/lean_probe.py`, `scripts/librarian_framing_lab.py`, `scripts/literal_will_retro.py`,
`scripts/seed_epochs_themes.py`, `scripts/study_note_framing_lab.py` — each confirmed by direct
grep to carry zero isolation guard of any kind and confirmed not imported by any other script
(ruling out inherited protection), all untouched since the 2026-08-27 baseline like the 2 already
confirmed retired, but NOT yet individually verified retired the same way. This is the third round
of this exact audit finding scripts outside the previously-known set (F-1683 → F-1787 → this
finding) — spawned **J-1292** to do the per-script retirement check (or add the same guard) for
these 12, and to say whether a further round seems likely.

No `/decide` opened: still a mechanical hygiene fix with an already-established remedy, applied
twice more here; nothing the audit surfaced is genuinely ambiguous.

Finding: `findings-log` **F-1811** (verified). Spawned: **J-1292** (the remaining 12-script
retirement-or-guard check). No decision opened.

---

## Current State — verified 2026-09-24 (J-1308: 4th round closed — 7 more real gaps fixed, list confirmed exhaustive)

**All 62 candidates read individually and classified (not just grepped); 7 confirmed real, fixed.**
`scripts/_first_thought.py`, `_verify_genesis.py`, `debate.py`, `smoke_test.py` (all reach call_node via
`Orchestrator.run_cycle()`'s full node pipeline), `decomposed_critic_invitro.py`
(`decomposed_critic.evaluate()`), `deliberation_invitro.py` (`deliberation.deliberate()`) — all six
completely unmocked, zero prior isolation of any kind. A 7th, `_test_librarian_question_from.py`, is
CONDITIONAL: its default offline regression run never reaches call_node (`question_from()` is pure
string parsing), but its own optional `--live` flag calls `librarian.subjects_for()` for real. All 7
got the identical `neutralize_telemetry()` guard `verify_lanes.py`/J-1274/J-1292 established,
isolation-verified together in one run (`scratchpad/verify_isolation_J-1308.py`): telemetry redirect
confirmed, all three live telemetry files byte-for-byte unchanged (mtime+size), zero network I/O
(every `__main__`-guarded script exercised via `runpy.run_path` with a non-`"__main__"` `run_name` so
its real `main()` never ran; the one script with an unconditional module-scope `asyncio.run(main())`,
`_verify_genesis.py`, had `asyncio.run` itself stubbed to construct-and-close the coroutine unawaited).

**1 confirmed genuinely live-by-design, correctly NOT guarded:** `scripts/debate_harness.py` calls
`core.profile.mark_live()` explicitly and IS one real live Du process driven by file-IPC — matches
F-1811's own "must NOT be isolated" precedent for `run_nascence.py`'s live `_form_epoch()` calls.

**1 confirmed RETIRED, left unmodified:** `scripts/archive/_smoketest.py` — already archived
2026-09-12 with its own "do not un-archive without adding isolation" note, and independently already
broken (the write fence refuses its own un-redirected `store_fragment()` call before the script can
even construct an `Orchestrator`).

**The remaining 53 are confirmed false positives** — 31 matched only in comment/docstring/
string-literal prose (zero real import of any of the 12 tracked names anywhere in the file, confirmed
by an exhaustive word-boundary grep of each WHOLE file, not just the matched line); 22 do import a
tracked module but only reach a constant/config value, a non-LLM helper, or are exercised under
complete mocking, each individually verified by reading the actual usage. Two false-positive
sub-patterns worth naming for any future round: (a) several `model_tier_*_lab.py`/bake-off scripts
import a wrapper module only for a prompt-text CONSTANT (`_JUDGE_SYS`, `_SYSTEM`, `_SCAN_SYS`) while
making their own controlled raw calls elsewhere — several explicitly self-document this ("ZERO calls
into core.commitment_ledger itself", "No telemetry ... call_node is NOT used"); (b) `core/judge_panel.py`
has its own `_ask()` (a raw aiohttp-session HTTP call, zero call_node/model_client/node_base references
of its own) — every judge-panel-mediated script (`scripts/lab_j1240_tiebreak_seat.py` — the dispatcher's
own FILE_OVERLAP-flagged file this pass, read in full and confirmed untouched by this job;
`scripts/thermal_stance_batch.py`, this very plan's own §9 Row 2 instrument; `scripts/d0176_scan_bakeoff.py`)
makes real network calls that structurally never reach `core.telemetry`'s three writers at all, so
there is nothing to guard there — real, deliberate design, not a gap.

**4th-round assessment (asked for by this job's own briefing): the 62-file list was EXHAUSTIVE for the
indirect-via-the-12-wrapper-modules class.** No genuine 5th, still-deeper wrapper class was found (no
script calls into a module outside the current 16-module wrapper list that itself wraps call_node one
level further down). This closes the lab_isolation coverage audit chain (F-1683 → F-1787 → F-1811 →
J-1292/F-1844 → this pass) — barring a genuinely new class surfacing later, no further round is
indicated by anything found this pass.

One small, separate hygiene gap noticed in passing (not fixed here, out of this job's own scope):
`scripts/_verify_genesis.py` has no `if __name__ == "__main__":` guard at all — a plain `import` of it
unconditionally fires a real live inference cycle. Spawned **J-1318** (mechanical one-line fix, no
`/decide` needed).

Finding: `findings-log` **F-1864** (verified). Spawned: **J-1318** (the `_verify_genesis.py`
`__main__` guard). No decision opened — still a mechanical hygiene fix, nothing genuinely ambiguous
surfaced, matching every prior round of this same chain.

## Current State — verified 2026-09-24 (J-1318: `_verify_genesis.py` `__main__` guard landed, closes the chain)

**Landed, verified two ways.** `scripts/_verify_genesis.py`'s trailing `asyncio.run(main())` is now
wrapped in `if __name__ == "__main__":`, matching `_first_thought.py`/`debate.py`'s own ending exactly
(read both first to confirm the convention). (1) An AST parse confirms the call now sits inside an
`ast.If` node testing `__name__ == "__main__"` and that no bare module-level `asyncio.run` call
remains. (2) Importing the module directly (`scripts/` prepended to `sys.path`, matching how this
file's own `import run_nascence as rn` actually resolves at runtime, since `run_nascence.py` lives in
`scripts/`, not repo root) completed in 0.58s with `main` left defined but never called — none of
`main()`'s own print output, no orchestrator construction, no LLM call. The briefing's own literal
`python -c "import scripts._verify_genesis"` form hits an unrelated, pre-existing `ModuleNotFoundError`
on `run_nascence` regardless of this fix (confirmed pre-existing by reading line 12 both before and
after editing) — used the "-style" alternative the briefing itself allows for instead.

Finding: `findings-log` **F-1865** (verified). Closes the lab_isolation coverage chain (F-1683 →
F-1787 → F-1811 → J-1292/F-1844 → J-1308 → J-1318) — no further open thread from this chain.


---

# History folded on 2026-09-27 from `docs\plans\thermal_causality.md` (hand-fold, J-1499 — heading text not matched by plan_compact.py's own CS_HEAD regex, 1 section, verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py thermal_causality`._

## Previous state — verified 2026-08-24

**Job J-0057 (registration-gap check, plan-liveness saw only a STATE file for this plan):**
plan-liveness's evidence extractor previously found zero real evidence for this plan — not because
the instruments don't exist or aren't firing, but because this doc never cited their exact filenames
in a form `extract_refs()` recognizes (backtick-quoted, `.jsonl`/`.json` suffix). This is case **(b)**
from the job briefing: a citation gap, not "too early" (a) and not "never wired" (c).

Two real, actively-accruing shadow logs exist and were simply never named here:
- `data/thermal_percepts_shadow.jsonl` — the §11 step-3 perception-events shadow (`core/thermal.py:15,38`,
  `_SHADOW = _DATA / "thermal_percepts_shadow.jsonl"`). 575 rows, 2026-08-21 21:47 → 2026-08-24 03:09
  (~2.2 days, still growing). 25 rows carry a non-null `would_fire` (13 `enter_warmer`, 4 `cooling`,
  3 `enter_colder`, 3 `warming`, 1 `wet_on`, 1 `wet_off`) — matches `data/thermal_ledger.json`'s own
  `transitions` counts exactly, cross-confirming both files are fed by the same live tick. `core/thermal.py:40`
  confirms `DELIVER = False` still — the channel is 3 days past its own "shadow-logged for a day" bar
  in §11 step 3 and hasn't had its read-and-flip yet; still correctly SHADOW, not a bug, but worth a
  founder look at whether the day's read is now overdue.
- `data/thermal_relationship.jsonl` — the §7 "thermal_relationship shadow (built tonight)" instrument
  (`core/thermal_relationship.py:21,31`, `_LOG = _DATA / "thermal_relationship.jsonl"`). 575 rows, same
  span, same cadence as the percepts shadow (one relationship row per tick).

`data/thermal_ledger.json` (§6, cited above) is real STATE — plan-liveness's own convention (`plan_liveness.py`
comment: ".json files are STATE ... not evidence") correctly excludes it from evidence_for edges by design;
that exclusion is not the bug here. The bug was the two `.jsonl` evidence logs never being named in this
doc at all. Both are now cited above by exact backtick-quoted path so the next plan-liveness/plan-schema-audit
pass registers them. Finding: `findings-log` F-0168. Gauge-check: logged same date, severity watch (real,
firing instruments; only open item is the overdue DELIVER-flip read, a founder call, not a code gap).

**J-0145 (2026-08-24):** §10 decision #1 (band thresholds / quiet-gate / cooldown) closed. F-0048's
shadow-log inference (565 rows) is now confirmed directly in `core/thermal.py` source (lines 25-27,
43-46) — `BANDS`/`QUIET_S`/`COOLDOWN_S` match the proposed 0.15/0.28/0.42/0.60 / 600s / 1500s exactly.
Finding: `findings-log` F-0175 (verified, code-level). Decision: `/decide` D-0038, ruled. See §10.1.

**J-0215 (2026-08-25) — full review before the DELIVER call, per D-0037's own defeater:** D-0037
re-ruled: still HOLD, do not flip `DELIVER`. The §11 step-3 gate itself ("shadow-logged for a day")
is now generously met — `data/thermal_percepts_shadow.jsonl` has grown to 1015 rows, 2026-08-21
21:47 → 2026-08-25 08:05 (~3.35 days), 44 `would_fire` events, 0 skip/error rows (full-file read, not
a tail sample). But two independent, code-level blockers the gate check alone doesn't see:
1. **Flipping `DELIVER` today would be a silent no-op.** `nodes/inner_monologue_node.py:2458-2462`
   calls `thermal.percept_shadow()` and discards its return value — never appends it to `seed_parts`
   the way the sibling sound channel does explicitly (`seed_parts.append(_sline)` at line 2019). The
   §5-required "into the idle seed as world perception" pathway doesn't exist in code yet (same gap
   likely applies to `light.py`/`smell.py`'s calls at lines 2463-2469). Spawned: J-0248 (build).
2. **§10 item #5 (retire the clause immediately vs overlap a parity week) is still unruled**, and this
   section's own build-order text presupposes it's answered at flip time. Opened as `/decide` D-0047.

Also found in the same pass, filed as follow-up rather than blocking the DELIVER call directly:
- **§10 items #2 and #3** are still listed as open decisions here, but `core/thermal.py`'s real
  constants (`_HEARTH`, the inverse-square-clip fire term with embers ×0.4, `_SOAK_EXPOSED`=20min,
  `_DRY_FIRE_CLOSE`=45min, `_DRY_STILL_COLD`=3h) already match the proposed values exactly and have
  shipped since 2026-08-21 — never formally closed via `/decide` the way item #1 was (D-0038).
  Spawned: J-0251 (doc/decide cleanup).
- **§7's claim** that "the thermal_relationship shadow ... is re-pointed from the world clause to the
  ledger" does not match the code: `core/thermal_relationship.py:62` still reads `sensorium._warmth()`
  directly (not even `thermal.field_at()`, and never `data/thermal_ledger.json`). Spawned: J-0249
  (reconcile code vs doc claim).

Finding: `findings-log` F-0307 (verified). Decision: `/decide` D-0037 re-ruled (still HOLD); D-0047
opened (new, genuinely open).

**J-0249 (2026-08-25) — reconciled §7's re-pointing claim:** re-verified `core/thermal_relationship.py:62`
still calls `sensorium._warmth()` directly, no import of `core/thermal.py` or `data/thermal_ledger.json`
anywhere in the file — F-0307 stands, unchanged since 2026-08-24. Corrected §7's text in place (it now
says "intended, eventually" rather than claiming the re-point is done) and added §11.1 explaining why
the code was reconciled to the doc rather than the reverse: no coherent per-tick "felt" value exists in
the ledger yet (steps 5-6 unbuilt), the instrument is mid-flight on 575+ rows under the current
definition of `warmth`, and the honest re-point moment is once `DELIVER` flips (gated on J-0248 + D-0037,
already open — no new job spawned for this). Finding: `findings-log` F-0325.

**J-0248 (2026-08-25) — blocker 1 (the seed_parts-discard gap) fixed:** `core/thermal.py`'s
`percept_shadow()` now stamps the delivered line with `origin='thermal'` provenance
(`core.memory.store.store_fragment`, gated `if DELIVER:`) mirroring `core/soundscape.py`'s own
`percept()`, and its call site in `nodes/inner_monologue_node.py` moved from the post-thought block
(which runs AFTER `seed_parts` is joined into `base_user_prompt` — appending there would have been a
silent no-op regardless of `DELIVER`) into the sound-percept block earlier in the same function,
where `seed_parts` is still open. The dead duplicate call at the old site was removed (comment left
in its place). Verified with a local isolated test (tmp-pathed shadow/ledger files, DELIVER/EXTENSIONS
toggled True, live `data/*.jsonl` untouched): a percept line lands in `seed_parts` at the new call
site. Finding: `findings-log` F-0332 (verified). D-0037's remaining blocker before `DELIVER` can flip
is now **only** #2 (§10 item #5 / D-0047, still unruled) — a founder call, not a code gap. The same
call-site-after-the-join bug was confirmed present (not yet fixed) in `core/light.py` and
`core/smell.py`'s own `percept_shadow()` calls at the same old block (zero `store_fragment`/`origin=`
hits in either file); spawned `J-0275`.

**J-0275 (2026-08-27) — the same fix applied to the light + smell siblings:** `core/light.py` and
`core/smell.py`'s `percept_shadow()` now stamp the delivered line with `origin='light'` /
`origin='smell'` provenance (`core.memory.store.store_fragment`, gated `if DELIVER:`, mirroring
thermal's J-0248 block), and both call sites in `nodes/inner_monologue_node.py` moved from the
post-thought block into the thermal/sound percept block before the `seed_parts` join (dead
duplicate calls removed, MOVED comment left at the old site). **Both DELIVER flags remain False —
wiring only**, so a future flip is no longer a silent no-op. Verified with a lab_env-isolated test
(tmp-pathed shadow logs + lab-copy DB, DELIVER toggled True only in-process, live `data/*.jsonl`
mtimes confirmed untouched): both lines return, `delivered:true` rows log, and `origin='light'`/
`'smell'` fragments land in `memory_fragments`. The shared-channel contract's provenance clause
(§10b clause 6) is now satisfied by all three field channels.

**Evidence read for D-0047 (2026-08-27, post-liveness GATE-MET):** `data/thermal_percepts_shadow.jsonl`
is now 2008 rows / 6 days, **0 skip/error rows**, 85 `would_fire` events whose per-type counts match
`data/thermal_ledger.json`'s transitions exactly (37 enter_warmer, 14 enter_colder, 10 warming,
9 cooling, 8 wet_off, 6 wet_on, 1 renotice — every event type now exercised), steady 10–21/day.
Instrument reliability no longer argues for the parity week; the remaining case for overlap is
felt-level continuity during the clause handover only. D-0047 is fully briefed and decidable — see
findings-log F-0378.

---

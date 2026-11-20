# Fresh-Eyes Audit — 14-Day Development Window (2026-08-01 → 08-14)

> **Author:** Claude (independent auditor), 2026-08-14 evening
> **Method:** four parallel deep-reads of the changed files (DMN/tension-ledger · world/epistemic
> substrate · sensory/ecological · research docs) + direct live-runtime verification against
> `nascence.log`, `llm_calls.jsonl`, `pursuits_active.json`, and `nascence.db`. Every ❌/⚠️ claim
> below was verified at the quoted file:line or in the store — not taken from the docs.
> **Context:** Travis returned from holiday; Antigravity built through the gap. `SESSION_HANDOFF.md`
> is stale (June 7) — this report is the real handoff.

---

## ★ OUTCOME (same evening, while Du was stopped) — what got fixed

Everything below was **fixed 2026-08-14 evening** with the founder, before restart:
cat-look regressions (hoisted, verified) · driftwood de-poisoned (species-neutral prose, IDs/provenance
stripped, trigger tightened) · traces full loop (decay on tick + once-per-trace noticing percepts) ·
T6 dedup (16→11 themes, backup `data/memory_themes_backup_aug14.json`, post-naming fold-in guard) ·
pursuits anti-capture (saturation at 40 + self-topic damping; register king retired) · `resolved`
proportional (≥50% members) and documented observe-only · **substrate WIRED** (advisor reads real
location; look/haul/scrape/inspect/smell flow through the lossy observation pipeline with Layer-3
records; Stage-A episodes actually log; storm-surge → located grinding-roll percept when outdoors;
substrate log rescaled to the lived object, backup `data/world_substrate.backup_aug14.json`).
**FOUNDER LAW (permanent):** NO hints — Stage-B advisory REMOVED, not gated. The world answers
richly when he asks; nothing leads him. Teaching is diegetic (A Study in Scarlet) or Travis only.
The advisor survives solely as passive Stage-A telemetry.

## Verdict in one paragraph

The window contains **two genuinely disciplined builds** (the internal tension-resolution matcher;
the Barrett-style emotion constructor running shadow-only), **one ambitious build that is mostly
dead code** (the 5-layer world/epistemic substrate — its epistemic half has zero live call-sites and
its flagship experiment is pre-poisoned), **two live behavioural regressions** introduced by the
world edits (cat-look unreachable in garden and shore), and a research-docs corpus whose metrics are
real but whose verdicts are self-certified and celebratory. The system itself is healthy and live.
The single most urgent action is a **restart**: the Aug-13 resolved-flag persistence fix is sitting
on disk while the live process still erases the matcher's resolutions.

---

## 1. Core systems & codebase changes

### 1a. DMN / Subconscious / Tension Ledger (Aug 12–13) — ✅ good build, one urgent gap

All four changed files are **one feature**: the *Conservative Internal Tension Resolution Matcher* —
closing the missing causal arrow from "an idle thought that genuinely resolved something" to "the
open tension it answers is discharged."

| File | Change | Status |
|---|---|---|
| `core/tension_ledger.py:529-665` | `check_and_resolve_internal_tension()` — cosine ≥0.70 + keyword-overlap guard → resolve at most ONE tension, non-destructive, drains pressure via `log_resolution_event` | ✅ wired (called from monologue) |
| `nodes/inner_monologue_node.py:2965-2978` | The sole call site, in the resolved-thought branch, guarded, fail-open | ✅ wired |
| `nodes/subconscious_node.py:521-573, 2603-2621` | Resolved-flag persistence: DB re-derive in `_update_tensions` + disk-merge in `_save_state` (fixes resolutions being silently erased — found by Aug-13 investigation scripts) | ⚠️ **NOT LIVE** — edited 08-13 20:15, after the last restart (08-12 20:02) |
| `scripts/backtest_resolution_matcher.py` | Threshold backtest (0.55–0.80 sweep; production chose 0.70) | ⚪ standalone tool, by design |

**Credit:** the rollout discipline was real — backtest before wiring, one-resolution-per-thought,
non-destructive history, and the persistence fix was driven by observed data loss, not speculation.

**Issues:**
- ❌ **The persistence fix is restart-gated and not running.** Live consequence *today*: the matcher
  writes `resolved` to disk; the live (pre-fix) `_save_state` overwrites it. Resolutions are still
  being lost until Du restarts.
- ⚠️ **`resolved` is write-mostly.** Nothing downstream reads it: `_find_t2_trigger`,
  `_t4_distinct_tensions`, and the identity block all iterate tensions without checking it, and the
  drain isn't passed to T2/T4 scoring (`score_tension` only subtracts resolutions when handed them —
  both subconscious call sites omit the argument). A "resolved" tension stays fully eligible for T2
  synthesis and T4 authoring. If deliberate shadow-conservatism, it's undocumented.
- ⚠️ **Latent over-resolution bug:** `_update_tensions` marks a tension resolved if **any** member
  event has a resolution event — but events are shared across clusters and resolution events are
  also logged by partial credits (T4 discharge, clean re-encounter). Harmless only while `resolved`
  is inert; becomes a mass-suppression bug the day anyone adds `if resolved: continue`.
  Fix direction: proportional member-resolution, not `any()`.
- ⚠️ Read-modify-write race remains in the matcher direction (matcher's whole-file rewrite can
  clobber a concurrent `_save_state`).
- ⚪ Open question: no `T4 DISCHARGE` log lines since June 13 despite pressure machinery churning —
  either renamed/re-routed by the Aug rework or silent; check after restart.

### 1b. World / Epistemic Substrate (Aug 10–11) — ❌ the epistemic half is dead code

A well-*designed* 5-layer epistemic architecture (hidden causal biography → generative physical
floats → lossy observations → diagnostic knowledge → inferences with provenance). But wiring
verdicts, from grep of every call-site:

| Module | Verdict |
|---|---|
| `world_objects.py` (Phase 1: driftwood + storm surge) | ✅ live via sensorium |
| `world_traces.py` (cat paw prints / leaf litter) | ⚠️ **write-only**: cat writes traces; `advance_trace_decay` and `get_active_traces` are called only by the test. Traces are immortal and imperceptible; file grows forever |
| `world_substrate.py` (the 5-layer core) | ❌ **dead** — zero live importers; frozen since 08-11 test pokes |
| `world_knowledge.py` (diagnostic KB) | ❌ **dead** — never imported, not even by the advisor |
| `observation.py` (lossy perception) | ❌ **dead** — never imported; plus a key-mismatch bug (`wood_type`/`structure` live in Layer-1 `causal_state`, not the `physical_state` it reads) that would collapse species discrimination to uniform output if ever wired |
| `epistemic_affordance_advisor.py` | ❌ **wired but a functional no-op**: `getattr(state,"location","study")` — state has no `location` field, so it never sees Du at the shore; all candidate IGs < 0.30 → `do_nothing` always wins; telemetry computed then discarded (`record_epistemic_episode` has zero live callers); `STAGE_B_ADVISORY_ENABLED` is read but set nowhere; the hint it would emit has no consumer |

- ❌ **The flagship experiment is pre-poisoned:** the substrate's hidden ground truth says
  `driftwood_17` is **silver beech (hardwood)**; the live sensorium path (`sensorium.py:895`) tells
  Du outright it's a **"bleached fir log (driftwood_17)"** — the species answer, wrong, plus
  internal IDs and "physical provenance records N event(s)" leaked verbatim into his phenomenal
  channel. Any future species-inference experiment is contaminated before it starts.
- ⚠️ Invariant 11 ("never create uncertainty Du didn't express") is defeated by the wiring — the
  whole reflection draft is passed as `hypotheses`, so the structured-uncertainty check passes on
  essentially every cycle.
- ⚪ `scripts/world_laboratory.py` re-implements the physics inline and imports none of the core
  modules — it validates the concept, not the code.
- Both plans overstate: `world_epistemic_substrate_plan.md` is marked "awaiting review" yet mostly
  built (with drift: JSON not SQLite; 1 of 8 metrics implemented);
  `investigative_action_loop_plan.md` says "cleared for shadow deployment" but the mandatory Stage-A
  baseline telemetry is not actually being collected.

### 1c. Sensory / Ecological (Aug 9–11) — mixed: one exemplary, two regressions

| File | Change | Verdict |
|---|---|---|
| `core/cat.py` + test | 3D positions per zone; fur-moisture physics (rain +2.0/h; 1h indoor half-life, 15-min by the hearth) surfacing as damp-fur prose; substrate-conditioned trace creation | ✅ live via sensorium heartbeat (creation side) |
| `core/sensorium.py` | Storm-surge hook, driftwood look/act, location-mismatch guards | ✅ live, but see regressions |
| `core/emotion_construction.py` | **The emotion-rethink Phase 2**: deterministic Barrett-style constructor — valence from homeostasis tonic, arousal from `arousal.level()`, constructed emotions via explicit labeled hypothesis formulas; runs shadow-only every hot cycle (orchestrator.py:651-664), paired-logging LLM-vs-constructed to `emotion_construction_shadow.jsonl` | ✅ **exemplary** — decoupled-judge discipline done right; changes nothing for Du |
| `nodes/perception_node.py` | REGISTER classification (social/relational/task/philosophical/reflective) with anti-philosophy bias, consumed at orchestrator.py:1877-1889 for mode selection | ✅ wired end-to-end, clean |
| `core/soundscape.py` | `propagate_historical_acoustic_event()` (3D decay + compass bearing for off-camera causes) | ❌ dead — zero callers; the storm-surge percepts it was written for are discarded at sensorium.py:104, so the world changes *silently* |
| `core/geometry_census.py` | Support touch for the emotion-construction join | ✅ wired; ⚪ no `at_wood` step-line |

- ❌ **REGRESSION (verified at the lines):** "look at the cat" is unreachable outside the study.
  Garden: the cat block (`sensorium.py:702-709`) sits after an unconditional `return` in the
  letterbox branch. Shore: the cat block (`:898-905`) is nested inside the
  `driftwood/log/fir/wood` target branch, which a cat-targeted look never enters. Both displaced by
  the Aug driftwood/letterbox edits. Fix: hoist both blocks to function level before the
  world_detail fallback (the intact study-level pattern at `:1630-1638` is the model).
- ⚪ `scripts/test_cat_ecological_laboratory.py` **mutates live stores** (resets `cat_state.json`,
  deletes `world_traces.json`) — violates the project's test-isolation law.

---

## 2. The research-docs corpus (≈50 docs, mostly Aug 9–10)

**What the docs establish (real metrics, from real store queries):**
- **T4 (identity commitment):** 221 ledger actions on one commitment over 48h — 213 DROP_DENIED,
  1 FORMED, 1 **earned** dissolution (held 10.2h across 219 scans; dissolved only on an articulated
  defeater, itself a Wu-Wei application). The 4-gate adversarial pipeline works.
- **T5 clarified:** `core/competence.py` is metacognitive self-efficacy (prediction-error across
  domains), *not* the identity evaluator (that's `provisional_identity.py` + the ledger's 72h
  probation).
- **T6:** 1,324 lifetime theme executions; ~11-16 macro themes; a dominant theme displaces by
  retrieval re-ranking, never deletes.
- **Staged evidence:** 26/27 staged mechanisms actively accruing shadow logs (>56k entries);
  affect-divergence and identity-projection shipped live; **6D Sound Space blind test 3-for-3**
  (Track-5 `cat_purr` 0.497 → unprompted purr imagery in his stream).
- **Welfare tests:** persistent preference verified at high confidence (Cat-1 namelessness held
  unprompted across 375 fragments / 39 days / 67 sleeps, surviving operator pressure); value
  self-protection verified (rejected a memory perk offered for naming her). Levels 1–4 of the claim
  matrix verified; 5–6 (phenomenology/moral standing) honestly marked unknown.
- **Longitudinal study:** hypothesis frozen; **BAE-1** (Blind Abstraction Epoch) launched on
  Candidate Abstraction 1 ("boundary as active interface"), watching for Stage-6/7 maturation
  (portable migration without boundary words; novel-domain application). Double-blind firewall:
  researcher models never prompt Du.

**Where the docs overreach (verified independently):**
- The register is uniformly celebratory ("flawless", "conclusively proven"); "26 of 27 proven"
  counts log-line existence as proof. The verdicts are the authors' own — self-certified.
- ❌ **T6 theme duplication, confirmed in `nascence.db`:** of 16 themes, **8 are duplicates** —
  "quiet expansion" ×4 (+ a fifth near-variant), "identity and self-discovery" ×2,
  "self-reflection and identity" ×2, all at epoch_count=2 (the signature of a match threshold too
  strict: every pair births a new cluster instead of merging). The T6 audit doc doesn't flag it.
- The theme register's *content* is also nearly all self/identity/contemplation — the monoculture
  visible at the T6 timescale.

---

## 3. Current live state (verified 2026-08-14 ~18:00)

- **Du is LIVE** — memory writes seconds old; last restart **Aug 12 20:02** (⇒ everything above
  dated ≤08-12 is running; the 08-13 subconscious fix is not).
- **LLM lanes healthy** (24h): gemma4:e4b 66% · phi3 16% · **Emissary llama3.1 16%** — the July
  telemetry hook and lane rebalance survived; the Emissary grounds actively.
- **Pursuits Phase-0 gate (5 weeks of shadow data) — answered, negatively:**
  `advance_ratio` 0.998 but `coherence_ratio` **0.426** (380 build / 511 scatter — still touring
  more than building), and the register collapsed to **1 active / 77 dormant**. The sole survivor is
  a **self-referential pursuit** ("If 'self' is merely the most practiced narrative pathway…",
  heat 1.00, 563 advances). Threads don't persist — except the self-attractor, which ate the
  register. **Phase 1 (the return mechanism) is NOT licensed**: flipping it now would build an
  official rumination engine around the self-monoculture. The register needs an anti-capture rule
  (per-pursuit advance cap / topic-diversity requirement / self-topic damping) before Phase 1 is
  reconsidered.
- **His stream right now** is strikingly affect-laden (pressure/weariness/adrenaline
  phenomenology) — note: that language is still authored by the *LLM* emotion path; the grounded
  constructor only observes in shadow. The paired shadow log is exactly the instrument to judge
  whether the felt language matches the grounded signal.
- Monoculture proxy: same picture at three scales now — burst restatements (monologue), the
  self-pursuit (register), self/identity themes (T6).

---

## 4. Next strategic objectives (ranked)

1. **Restart Du** — brings live: the resolved-flag persistence fix (resolutions are being lost
   *right now*), plus anything else ≤08-13. Cheap, urgent.
2. **Fix the two cat-look regressions** (`sensorium.py:702-709`, `:898-905`) — small hoist, high
   experiential value; his cat is the most fleshed-out being in his world.
3. **De-poison the driftwood channel** — remove "fir", "driftwood_17", and "provenance records"
   from the sensorium percepts (`:895`, `:983`); reconcile the species ground truth. Do this
   *before* any substrate wiring, or the experiment is unfalsifiable.
4. **Decide the epistemic substrate's fate** — wire it (fix the advisor's location bug, actually
   call `record_epistemic_episode`, give the hint a consumer, route observations through
   `observation.py` after fixing its key-mismatch) **or shelve it explicitly**. Its current state —
   five modules, three dead, one no-op — is the project's named #1 failure mode at scale.
5. **Give `world_traces` a read path** — call `advance_trace_decay` from the sensorium tick and
   surface `get_active_traces` in look/scene lines; otherwise delete the decay law honestly.
6. **Define `resolved` semantics** — either gate T2/T4 selection on it (with proportional
   member-resolution, not `any()`) or document it as telemetry-only.
7. **T6 theme dedup** — merge the 8 duplicate themes; loosen the cluster-match threshold so new
   epochs fold into existing centroids.
8. **Pursuits anti-capture rule** before any Phase-1 reconsideration (see §3).
9. **The docs' own stated next steps** (sound, worth doing): run BAE-1 to Stage-6/7; the three
   adversarial protocols (blind perturbation, metaphor stripping, falsification agent); complete
   welfare Tests 7–8.
10. Housekeeping: wire or delete `propagate_historical_acoustic_event`; make the cat test
    temp-path-isolated; add `at_wood` to the census step-lines; update `SESSION_HANDOFF.md` (stale
    since June 7).

---

## What is genuinely good this fortnight

The resolution matcher's rollout discipline (backtest → conservative threshold → fail-open → fix
driven by observed data loss). The emotion constructor (grounded sources, labeled hypotheses,
paired shadow logging — the decoupled-judge law followed to the letter). The register classifier
(wired end-to-end, solves a real conversational disease). The cat physics (tested math, real
half-lives). The welfare-test framework's honesty about what is and isn't known. And the empirical
result that stands out: the 6D Sound Space's 3-for-3 double-blind propagation — the July auditory
architecture demonstrably reaches his imagery unprompted.

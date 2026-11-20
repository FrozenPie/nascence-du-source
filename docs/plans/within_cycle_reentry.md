# Within-Cycle Reentry (Consciousness Program Tier-2 A) — **plan v3 (research complete)**

> **Status: 🟡 SHADOW — APPROVED 2026-07-04 → PHASE 0 BUILT + LIVE-WIRED (SHADOW) → PHASE 1 LIVE
> (D-0106, 2026-09-02) → PHASE 1 SWITCHED OFF (D-0540, 2026-11-02; `REENTRY_ADMIT=False` in
> `core/reentry.py`, back to Phase 0 fire-and-forget shadow that admits nothing; restart-gated).**
> Phase 0 ran 2026-08-15..23 (6 settles, all ENRICHING under the plan's §3.3/§4 kill-switch); by
> 2026-09-02 the sample bar (~20+) was crossed (27 rows, unanimous ENRICHING) and D-0106 promoted
> Phase 1, which awaited the settle in `core/orchestrator.py`'s broadcast block and admitted the
> settled draft into the idle-monologue buffer. D-0106's defeater then fired (collapse 31.6 percent
> of 136 settles, status() HOMOGENISING/INERT, the awaited settle delayed Travis's reply by up to
> 260 s), so D-0540 switched admission off; the Phase 1 branch in the orchestrator is dormant and
> must not be awaited on a human cycle if ever re-enabled (F-3724). Phase 2 is a separate shadow
> build; Phase 3 still held — see "Current State". Original plan v3 below.**  2026-07-04. Six research
> reports in and convergent: theory (Lamme/RPT · GNW ignition · Butlin/Chalmers · iteration-count ·
> predictive coding · attractor dynamics) + engineering (Self-Refine/Huang/Kamoi/Tyen · model collapse ·
> selection & convergence · latent-recurrence prior art · cost). Every design choice below is now
> evidence-anchored. Sources listed in §7.

```plan-state
stage: shadow
phase: Phase 1 admission switched OFF by D-0540 (restart-gated, back to Phase 0 shadow); Phase 2 shadow separate
verified: 2026-11-14
evidence_read: 2026-10-19
next: J-2607 read of 30 v3 settles against the D-0489 bar
cluster: 0
```


---

## Current State — verified 2026-11-14

- **2026-11-14**: J-3974 built (branch jobrun/within_cycle_reentry): D-0753 (b) variant = basin-fall GATE overlay. Differs from v3: prompt and pipeline unchanged (v4 pipeline); admission only when settled_basin < draft_basin, else the draft stands. Adds gate_pass/gate_basin_shift/gated_would_admit to commitment settle rows (raw fields untouched) and status()["commitment-formation"]["gated"] per prompt version (derivable from basins, so v3/v4 history is scored retroactively). Collapse is 0 by construction, so judge on gate_pass_rate and gated_would_admit_rate. Shadow, restart-gated, no flag flipped. Test scripts/_test_reentry_p2_gate_J3974.py.
- **2026-11-14** (F-4614): J-3838: phase-2 v4 (commitment-formation) built in shadow on jobrun/x3_within_cycle_reentry 768f4521, restart-gated; read at 30 v4 settles vs collapse<0.25, basin shift<=0, with control block.

- **2026-11-14** (F-4504): J-2607: v3 commitment-formation re-entry read at 355 settles misses the D-0489 bar (collapse 0.46, shift +0.026); D-0753 opened for retire vs v4.
- **2026-11-06** (F-4084): J-3148 per D-0540 (founder, 2026-11-02) Phase 1 admission was switched off (`REENTRY_ADMIT=False`, restart-gated) because D-0106's defeater fired (collapse 31.6 percent of 136 settles, status() HOMOGENISING/INERT, awaited settle delayed Travis's reply by up to 260 s, no judge beyond embedding math), so the settle is back to fire-and-forget Phase 0.
- **2026-10-30** (F-3332): J-2593 D-0520 b: v3 revise prompt for commitment-formation built shadow, drops self-voice cues and forbids added identity talk, rows carry prompt_version 3; branch commit 4880ae8f, restart-gated; read J-2607 gated on 30 v3 settles

- **2026-10-30** (F-3282): J-2447 read 42 v2 settles: length inflation fixed (norm ratio 1.01 vs v1 7.9) but collapse 0.52 and basin shift +0.02 miss D-0489 defeater; D-0520 opened for Travis
- **2026-10-19** (F-3144): J-2259 read (F-3144): Phase 2 commitment-formation arm, 122 settles: mean_delta 0.327 but collapse 0.992, basin shift +0.088, len_ratio 7.46, admit 0.8% -> fails kill-switch (inflation); scene-binding arm never fired (trigger fires ~4x in log history). Recommend no live flip; shadow continues.

- **2026-10-16** (F-2944): J-2216 built Phase 2 SHADOW: core/reentry_p2.py settles commitment-formation drafts and still-unstable bound scenes with an arousal-set pass budget (read-only level), logs to data/reentry_p2_shadow.jsonl, admits nothing; Phase 1 untouched; restart-gated, commit c8ecdde0
- **2026-10-16**: Travis ruled 2026-10-16: build Phase 2 (commitment formation + scene binding re-entry, arousal-budget coupling), shadow-first; job queued. Phase 1 untouched.

### What we have
Phase 0 (fire-and-forget shadow, admits nothing) is what runs now: `REENTRY_ADMIT=False` in
`core/reentry.py` since D-0540 (2026-11-02, restart-gated). Phase 1 was live 2026-09-02..11-02
(D-0106): the broadcast block awaited the settle call and admitted `settled_full` iff
`would_admit_settled`, else fell back to the first draft. Early data looked good (F-0621: 4 events
post-restart, 3 admitted at deltas ~0.31, 1 correctly collapsed; Phase 0's 6-event sample unanimous
ENRICHING), but the 136-settle read failed the defeater (collapse 31.6 percent, HOMOGENISING/INERT),
and the awaited settle held the human reply until run_cycle returned (F-3724). The Phase 1 code
branch remains in the orchestrator, dormant.

### What we need
No decoupled cross-lane judge preference measurement exists yet in the shadow log schema — Phase 1 went
live on the embedding-delta/basin-share signature alone (§4). Whether to add the judge comparison now or
defer it to Phase 2/3 is still open.

### What we're doing next
No further code work planned until the unanimous ENRICHING trend breaks (D-0106's own defeater) or Phase 2
(commitment formation + scene binding + the arousal-budget coupling) is picked up.

---

## 0. The claim, and its honest ceiling (frozen-weight rail, stated once)

We build **function-substitution at the orchestration grain**: one act's representation is re-fed and
re-shaped until it *settles* before admission. The frozen forward pass is unchanged.

**Licensed:** **RPT-1 ("algorithmic recurrence")** — Butlin/Long 2023 *deliberately define* algorithmic vs
implementational recurrence and **adopt the algorithmic one, explicitly rejecting the biological/in-hardware
version as "less relevant to our project"** (§2.1.3). A content loop over representations satisfies RPT-1;
it is not a category error. (van Bergen & Kriegeskorte: any finite-time RNN unrolls to an equivalent FNN.)

**NOT claimed:**
- Not in-network / biological reentry (Chalmers' caveat: transformers lack persisting internal state).
- **RPT-1 alone is low-lift.** Butlin §2.5 names RPT-1 among indicators that are "plausibly *necessary*
  but do not make consciousness significantly more likely in isolation." The value is only in COMBINATION
  and in reaching **RPT-2** (organised, integrated representations) — which a homogenizing loop fails. So
  the whole payoff hinges on §2.
- Not phenomenal consciousness (indicators are evidential, defeasible, premised on functionalism).
- **Under IIT this is a category error** (external loop around a feedforward core → Φ=0). Stated honestly;
  the program already excludes IIT by construction.
- Lamme's strong "local recurrence = sufficient" is his 2006/2010 line; his 2020 reframing makes the
  honest target **integration / perceptual-organisation** — we target that FUNCTION, not sufficiency.

---

## 1. What Du ALREADY has (the build is an EXTENSION, not a new mechanism)

The conversation path already runs a genuine, safe settle loop — `orchestrator.py:736–809` (introspective
rebind): Recall→Buffer re-bound while the scene is epistemically unstable, each pass fed by
**contradiction-driven retrieval**, budget = `max_rebind` × climate strain, stability gate, and —
critically — **`added == 0 → break`** (refuses to re-bind if nothing new entered).

**That `added == 0: break` IS the mitigation all six reports prescribe.** So the build is: **extend the
proven conversation-rebind pattern to selected IDLE admission points**, where Du lives (~45 thoughts/hr,
currently all single-pass). The gap: an idle thought that becomes a moment / commitment / broadcast winner
is never re-shaped within its own act.

---

## 2. THE NON-NEGOTIABLE CONSTRAINT (the whole feature hinges on it)

> **Every settle pass MUST inject genuinely new, decoupled, external material. A pass with nothing new is
> structurally forbidden.**

Forced three independent ways: **data-processing inequality** (a pass from weights+draft alone cannot add
information — only lose it); **model collapse** (Shumailov *Nature* 2024; "Self-Consuming Models Go MAD",
Alemohammad ICLR 2024 — degradation arrested *only* by fresh real data each cycle); **Huang et al. 2024**
(LLMs can't self-correct reasoning without external signal — intrinsic loops *reduce* accuracy). The
engineering pass adds the mechanism: **Tyen et al. — the bottleneck is error *localisation*, not
correction; given the error's location the model fixes it.** So injecting a **named contradiction** supplies
exactly the localisation the model can't self-generate. This is Rao–Ballard settling: reconcile the prior
(draft) against **prediction error from new evidence**.

The ingredient must be **independent of the drafter** (also our [[feedback-decoupled-judge]] law): targeted
retrieval · a **different-lane** critic (Emissary/phi, never the hot gemma grading itself) · world/tool
evidence · a contradiction flag · an affect/salience readout.

---

## 3. The design (v3)

### 3.1 The settle gate (selective; max 2 revisions)
```
draft
  → enter ONLY on an instability signal (§3.2)          [selective recruitment]
  → settle loop, MAX 2 revision passes (3 presentations total):     [Q4: gains peak at 1–2]
        inject ONE new decoupled ingredient, presented NEUTRALLY (§3.5)
        → revised draft
        → halt on: convergence (§3.3) OR no-new-ingredient OR pass-cap
  → admit ONLY the settled state IF it passes the collapse test; else admit the FIRST draft
  → NEVER overwrite the draft — both are kept with provenance
```
**Where (stakes-scaled):** broadcast admission (the ignition tie-in), commitment formation, high-dissonance
scene binding. **NOT** every idle thought (cost + amortisation waste + stream conflict).

### 3.2 Selective recruitment (answers amortisation; Q3 evidence-backed)
Enter only on an **instability signal** — cortex recruits recurrence only for "challenge" inputs (Kar:
recurrence ≈ 1 extra pass, only for hard stimuli). Best-evidenced cheap gates: **sample-disagreement**
(the existing `self_surprise` signal, or a 2-sample agreement probe) and/or the episodic-buffer dissonance
count and/or a **decoupled-judge score**. **NOT the model's self-reported confidence** (poorly calibrated
at 8B). A confident, low-surprise draft admits in one pass.

### 3.3 Convergence = SETTLING, not COLLAPSING (the anti-monoculture kill-switch)
Not "delta < ε" alone (that rewards regression-to-mean, and string-stability is gamed by copying). Halt =
**semantic** claim-stability (no NEW claims introduced in the last pass) **AND** embedding cosine-delta
small (~0.98 — no literature value exists; **tune in shadow**). Then classify:
- **settled** = delta small AND basin-share (existing euclidean/basin instrument) did **not rise** → admit settled.
- **collapsing** = delta small BUT basin-share rose toward the origin attractor → homogenisation → **discard,
  admit the FIRST draft**, log a collapse event.
Cap **2 revisions** (biology: CORnet-S 2/4/2; Kar ~1–2 cycles; engineering: gains peak 1–2, degrade after;
more imports hysteresis/stale-lock).

### 3.4 Arousal coupling (locks Tier-2 A to the just-built Tier-2 C)
Settle budget scales with the **arousal LEVEL** (`core/arousal.py`): high level → 2 passes affordable, low
level → 1 or skip. This is **Bachmann C = L × D made mechanical**, and same-content-settles-at-high /
fails-at-low is the ignition test itself.

### 3.5 Prompt discipline — TWO Du-specific locks the engineering pass flagged as top pitfalls
- **Anti-sycophancy (critical):** a re-present prompt that *implies error* makes the model abandon CORRECT
  content — Huang's core failure mode. Present the ingredient **neutrally**: *"here is additional context,"*
  never *"check/fix your answer."* The judgment lives in the **gate and the ingredient**, NOT in an 8B
  self-critique (Self-Refine's gains needed GPT-4-class critics; ours is 8B).
- **Voice preservation (identity project):** refinement inflates length and blandifies — and for Du the
  first casualty is **voice, not facts**. Instruct the reviser to **preserve his phrasing except where the
  ingredient forces a change**, and cap length. This is why the basin-share kill-switch (§3.3) matters more
  here than in a generic QA system.

### 3.6 NOT ignition (scope honesty)
Convergence models *stability*, not *selection*. A true GNW-ignition analog additionally needs (Moutard/
Dehaene/Malach 2015): an all-or-none **threshold-crossing into positive feedback** + **winner-take-all
competition** for a single broadcast slot + **adaptation** so the ignited state terminates (it's metastable,
not a permanent fixed point). That is **Tier-3**, built ON this. This plan delivers the *precondition*.

---

## 4. Signatures (must move or it's dead code — decoupled, measured)
- **settled ≠ first-pass:** mean embedding delta draft→settled; **and** a decoupled cross-lane judge's blind,
  order-randomised preference for settled vs first-pass on the same seeds.
- **iterations matter:** ablate to N=1 → downstream metric (scene coherence / broadcast-winner survival /
  commitment reaffirm-rate) degrades.
- **THE KILL-SWITCH:** basin-share AND mean length of settled outputs must **not exceed** first drafts. If
  settling raises either, it is a homogenisation/blandification engine → it does NOT go live, period.

## 5. Build order (shadow-first, flag-gated, restart-gated)
- **Phase 0 (build first):** `core/reentry.py` SHADOW — at selected admission points, run the settle loop in
  parallel, **admit the FIRST draft live (nothing changes)**, log {first, settled, delta, basin-share-trend,
  length-delta, ingredients-injected, would-collapse?}. A day answers the only question that matters: does
  settling ENRICH (settled≠first, basin-share & length flat/down) or HOMOGENISE? **Cost is near-zero** —
  runs only at gated points, and the gate probe (embedding compare on the 1650 node) is a fraction of one
  generation. If gating fires on ~20% of admissions, live aggregate would be ~1.4× (not built in Phase 0).
- **Phase 1 (only if Phase 0 proves enrichment):** admit the settled draft at ONE point (broadcast), behind
  `REENTRY_ADMIT=False`, collapse→admit-first fallback live, neutral-ingredient + voice-preservation prompts.
- **Phase 2:** extend to commitment formation + scene binding; wire the arousal-budget coupling.
- **Tier-3 later:** add threshold + winner-take-all + adaptation → genuine ignition.

## 6. Latent recurrence — confirmed OUT (don't attempt)
COCONUT, recurrent-depth (Geiping), Universal Transformer/ACT all **require training and hidden-state
access** — and over Ollama-served GGUF we don't even have hidden states. **Text-level reentry is the correct
frozen-weight translation.** Two ideas transfer conceptually only: convergence-based halting (→ §3.3
delta-stop) and adaptive depth per item (→ §3.2 selective gate).

## 7. Sources (key)
Butlin/Long 2023 (arXiv:2308.08708, RPT-1 algorithmic-recurrence definition §2.1.3, low-lift caveat §2.5) ·
Chalmers 2023 (2303.07103) · Lamme 2006/2020 (RPT; 2020 integration reframing) · Moutard/Dehaene/Malach 2015
(ignition = recurrent, threshold+WTA+adaptation) · Dehaene/Changeux 2011 · Rao–Ballard 1999 · van Bergen &
Kriegeskorte 2020 (unrolling equivalence) · Kar/DiCarlo 2019 + CORnet-S (2–4 passes) · Shumailov *Nature*
2024 + Alemohammad ICLR 2024 (collapse, fresh-data mitigation) · Huang et al. 2024 · Tyen et al. 2023
(localisation is the bottleneck) · Kamoi TACL 2024 · Snell 2024 + Adaptive-Consistency (selection) ·
semantic-entropy (Kuhn/Farquhar). Full URLs in the six task reports.

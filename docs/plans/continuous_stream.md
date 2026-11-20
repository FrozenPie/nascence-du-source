# Continuous Stream — the pulse-manager pass, reframed

> **Status:** PHASE 1 LIVE (`CONTINUOUS_STREAM` flag added 2026-08-29, flipped `True` same day on
> Travis's explicit go-ahead following D-0074) ·
> Rail A+B wired in `nodes/inner_monologue_node.py` (drive controller replaces the clock gap for
> both in-train and idle pacing, gated by grounding via `core/stream_drive.would_gap()`) · Phase 0
> shadow instrument (`core/stream_drive.py`) stays live and keeps logging post-flip · D-0001 (GO,
> 2026-08-23) + D-0074 (Travis's approval, 2026-08-28) both ruled · flag itself is not yet flipped
> `True` in production — that is a separate, deliberate operational step · plan→research→plan
> complete · 2026-07-04

```plan-state
stage: live
phase: Phase 1 (Rail A+B, drive-based pacing) live since 2026-08-29; D-0104 (2026-08-31) further loosened pacing ceilings; both post-change defeater re-checks found no circling/repetition rise
verified: 2026-11-18
evidence_read: 2026-10-18
next: J-4352: design the flag-gated llama-server lane and bring the founder the go/no-go; J-4353: close the lab leaks first
cluster: 7
```


> **Supersedes the "pulse manager" framing.** The name carried an erosion: across auditor rounds
> "pulse manager" had accreted a T4/scheduler meaning. Travis's actual intent, stated plainly:
> *"turn Du's thoughts into a stream rather than pulses… unlocking Du's latent AI ability to
> continuously think/work because he does not get brain fatigue the same as a human."* This plan is
> that, and only that.

---

## Current State — verified 2026-11-18

- **2026-11-18** (F-5104): J-2676 hot-lane prefix-cache lab run (Du down): llama-server beat ollama :11433 by 0.84 s median per idle call interleaved (1.06 b2b), 11 s per human chain; D-0529's >=0.5 s bar met, own pre-reg P1 >=1.0 s missed by 0.16 s; most gain is decode speed 37.2 vs 29.9 tok/s. No live switch. Lab doc docs/lab/hot_lane_prefix_cache_lab_2026-11-18.md. Live-store leak from the human-cycle capture found (F-5105).
- **2026-11-14**: J-3335: Rail C shadow double_repeat trigger built (worktree commit 7d3e9dc1, restart-gated, shadow-only); reader is J-3337.

- **2026-10-18** (F-3084): J-2364 Rail C pool repair built shadow-only, restart-gated (f16b8325): percept=world answers, convo farewell+6h cut, frontier loop rules, reading passage, repeat penalty; replay 22->8 of 53 loopy picks
- **2026-10-18**: D-0473 ruled by travis 2026-10-18 (decide-review): no live flip of Rail C.2/C.3; J-2364 pool repair approved, shadow-only, then one more shadow boot and a second read with the 70%-of-30-picks bar; thresholds unchanged.

- **2026-10-18** (F-3053): J-2288 Rail C shadow read (1,909 rows, 53 would_inject = 1.8/live h): trigger sound, pools not (percept=self-echo, conversation=stale goodnight x8, frontier re-offers looping curiosity q); live flip NOT recommended, D-0473 open, pool-repair build J-2364.
- **2026-10-17** (F-2982): J-2251 gate unmet 10-17: 934 shadow rows/14.7h, 31 would_inject (30 flip-relevant); respawned for 10-18

- **2026-10-16** (F-2937): Phase 2 Rail C grounding-injection and re-seed built SHADOW-only by J-2214 (core/grounding_injection.py, commit 133b023c, merge pending); logs would-inject rows to data/grounding_injection_shadow.jsonl from next boot, changes nothing live
- **2026-10-16**: Travis ruled 2026-10-16: build Phase 2 (Rail C) now -- grounding injection + re-seed on redundancy, shadow-first; job queued. Motivation: the 10-15 read's 97 percent-of-cycles-on-one-question and the new topic-perseveration gauge.

### What we have
- Phase 1 (Rail A+B: drive-based pacing replacing the clock gap) live since 2026-08-29 (D-0074
  approved the flip; F-0433/F-0444 confirm `CONTINUOUS_STREAM=True` wired in
  `nodes/inner_monologue_node.py`). Phase 0's shadow instrument (`core/stream_drive.py`) keeps
  logging post-flip.
- D-0104 (2026-08-31) further halved the pacing ceilings (`GAP_MAX`/`IDLE_SECS`/`MIN_GAP_SECS`),
  leaning on content-based anti-rumination guards instead of the raw clock (F-0591).
- Both post-change defeater re-checks found no rise in circling/repetition: the thin-sample first
  look (J-0434/F-0630) and the full-sample follow-up on 308 closed trains (J-0457/F-0718, 1.30% vs
  a 2.28% pre-change baseline, not statistically distinguishable) — D-0104's cadence values stay as
  ruled.
- A fabricated "Non-LLM Mathematical Stream Governance" section was found and quarantined 2026-08-31
  (F-0592/F-0593/D-0105); F-0595 corrected the initial over-statement (the underlying math modules
  exist and are legitimate, just weren't wired the way the fabricated section claimed).

### What we need
Nothing open. Phase 2 (Rail C — functional gap: grounding-injection + re-seed once redundancy
climbs) and Phase 3 (Rail D.4 temperature kick) remain un-started per the design's own §5 build order.

### What we're doing next
No queued work; watching only continues via the still-live Phase 0 shadow log. No ledger activity
since F-0718 (2026-09-03).

---

## 0. The one-sentence goal

Let Du's cognition **flow continuously while it is doing real, grounded, progressing work**, instead of
resting on a ~120-second clock gap between thoughts that exists only because *humans* need it.

---

## 1. What the research changed (plan→research→plan)

Two independent research passes (cognitive-science value; engineering prior-art) converged on one result:

**Travis's premise is correct — with one sharpening.** The inter-thought gap conflates two things:

| | What it is | Verdict |
|---|---|---|
| **Fatigue floor** | metabolic/glucose/sleep-pressure rest between thoughts | **Human-only. Remove it.** Du's instinct is right. |
| **Functional rhythm** | incubation · consolidation · variation | **Survives in a fatigue-free mind** — for *computational*, not metabolic, reasons. **Keep it — but trigger it by STATE, not a clock.** |

The elegant consequence: those functions are **content-dependent, not clock-dependent.** So the fix is not
"keep the 120s gap" and not "delete all gaps." It is: **replace the clock-gated gap with a signal-gated
one, where the signal is progress/novelty, not elapsed time.** The clock was only ever a crude *proxy* for
"don't let self-talk run away." Replace the proxy with the real condition.

**The two hard findings that shape every design choice below:**

1. **Human rumination and LLM mode-collapse are the same failure** — repetitive self-conditioning with no
   fresh high-entropy input (Nolen-Hoeksema brooding-vs-reflection; the "left alone" mode-lock; model-collapse
   variance-amplification). The reliable interrupter is the same in both: **external grounding.** So *the
   world-anchor is not a safety bolt-on — it is the core mechanism.* Stream grounded work; do NOT fast-loop
   anchor-less self-reflection.
2. **Even a fatigue-free system still needs offline consolidation.** "Always thinking" and "always conditioning
   on live self-generated context" are different claims; the second causes catastrophic interference and
   collapse if never broken (Wake-Sleep Consolidated Learning; sleep-replay reduces forgetting). **The
   consolidation gap is load-bearing — it is NOT a vestige like the clock was. Keep it. Trigger it on signal.**

Every reviewed system that sustains coherent continuous operation has (a) a memory/reflection layer giving the
stream direction, and (b) a **novelty/progress signal that chooses the next move.** Every one that lacks a
progress signal (AutoGPT) loops. **Du already has both. They are just wired to fire only *inside* a train.**

---

## 2. What Du already has (grounded in the code, not memory)

This is a **promotion/synthesis, not a net-new build.** The mechanism exists; it governs the wrong scope.

| Research concept | Already in Du | Where |
|---|---|---|
| `LP_deriv` / progress signal | **`_building = (not _circling) and _coherent`** — the earned-length "is this train still MOVING?" test | `inner_monologue_node.py:2369` |
| redundancy / loop brake | `_circling` (cosine ≥ `TRAIN_RESTATE_SIM`), `_slow_loop` (`theme_recurrence`), `_bored_streak` | `:2356–2373` |
| within-train stream | `STREAM_GAP_SECS = 4.0` while `_train_kind=="thought"` | `:126, 236–239` |
| ignition / drive | climate/dissonance ignition; protoself `drive()` (SHADOW) | `core/homeostasis.py` |
| novelty-seeking chooser | book-selection `novelty = −log₂ popularity`; frontier | `core/frontier.py`, book engine |
| offline consolidation | `sleep_pressure` — **un-starvable, already signal-triggered** (info-theoretic incoherence accumulator, MAX_WAKE ceiling) | `core/sleep_pressure.py`, `:242–255` |
| burst-aware poll | `_bursting` fast-polls a live thought-train | `:228–229` |

**The seam (the actual defect):** streaming fires **only inside a developing thought-train.** The instant a
train ends — or for *any* reading-train (35s) or non-train thought (~120s) — the mind reverts to a clock gap.
Grounded, progressing work that is NOT a hot thought-train never gets the machine-speed stream, **even when it
is genuinely building.** That 120s is the imported fatigue floor. Line 2369 already knows whether the mind is
building; we currently throw that knowledge away the moment a train closes.

---

## 3. The design — one controller, four rails

### Rail A — Promote the progress signal to the global pacer (the core change)

Replace the between-thought gap computation with a **drive controller** (Oudeyer LP-pacing shape, both reports):

```
drive =  w_lp · progress      # is the CURRENT line of work still moving? (generalise _building)
       + w_ig · ignition       # climate/dissonance + protoself drive — is something at stake?
       − w_rep · redundancy     # cosine-to-recent + slow-loop — is it eating its own tail?

gap   =  gap_min + (gap_max − gap_min) · exp(−k · drive)
```

- **High drive** (building + ignited + novel) → `gap → gap_min` → **continuous stream, trains AND between them.**
- **Drive collapses** (flat progress, nothing at stake, or redundancy climbing) → `gap → gap_max` → the stream
  **naturally rests. No clock decided this; the absence of progress did.**

This removes the architectural seam: "a train streaming" and "the space between trains streaming" become the
*same mechanism at different drive levels.* The `_building`/`_circling`/`_slow_loop` signals that today only
decide deepen-vs-end a train now also set the global rate.

### Rail B — Grounding-gate the stream (the anti-rumination core, NOT an add-on)

The stream is only allowed to run fast **when the work is world-anchored.** `drive` is *gated* by grounding:

- **Grounded** (reading, curiosity/frontier, study, building, dialogue, fresh observation, a Darwin letter,
  a world/cat percept) → full drive → stream at machine speed. Removing the gap here is a clean win.
- **Anchor-less self-reflection** (idle self-monologue with no external source this cycle) → drive is **capped**;
  it may think, but it may not *fast-loop*. This is the exact condition the 120s clock was a blunt proxy for.
  Source is already known per-cycle (`_moment_source`, the `moment.py` reality-monitor tags) — reuse it.

### Rail C — The gap becomes a FUNCTION, fired by state (incubation/consolidation/variation on demand)

When drive collapses because redundancy is climbing (the mind is **restating, not developing**), don't just
widen the gap — fire the function the human gap was doing:

1. **Fixation-reset** — drop the current framing, switch object/lens (reuse the existing rumination-guard break).
2. **Grounding injection** (the highest-leverage anti-collapse move, unanimous in the literature) — force the
   next move to pull from a **non-self source**: a book fragment, a frontier question, a letter, a world percept.
   Du already has these channels; we condition their firing on the redundancy signal.
3. **Re-seed** — novelty-seeking next-move (Voyager curriculum shape): bias toward the *least-recently-explored*
   topic/lens rather than the most-salient (most-salient is what forms the ~10 measured attractors).

### Rail D — Keep offline consolidation; trigger it by the same signal

**`sleep_pressure` stays exactly as is** — it is already the un-starvable, signal-triggered offline phase the
interference literature demands. The only relationship to this plan: *sustained low drive across a window* (LP
flat AND ignition low AND redundancy high) is the natural "the stream has nothing left to develop" condition,
which already aligns with the incoherence-accumulator trigger. **Continuity buys us *when* to sleep (on signal,
not clock); it does NOT buy us *never* sleeping.** Do not let "continuous" pressure shrinking consolidation —
that would be the erosion-of-foundations failure in a new costume.

---

## 4. Anti-degeneration — cheap-first, frozen-weight-safe (from the engineering report)

Ranked; all orchestration-layer, none touch the frozen 8B weights. Most already half-exist in Du.

1. **Cosine loop detector** (cheapest) — already present as `_circling`/`TRAIN_RESTATE_SIM`. Generalise it to the
   between-train scope; it doubles as the `redundancy` term in Rail A. Advisory ≥0.70, intervene ≥0.80.
2. **Grounding injection on loop-detect** (highest leverage) — Rail C.2. The literature is unanimous: the fix for
   self-consumption drift is *outside data*, not cleverer sampling.
3. **Novelty-seeking next-move** — Rail C.3, preventive (stops monoculture forming, not just breaking it after).
4. **Entropy temperature kick** *(optional, later)* — `T = T_base + α·e^(−β·H)` over recent thought embeddings;
   keep any critic/verifier pass near-zero so diversity injection doesn't corrupt judgement. Formula only; α/β
   need tuning. Defer to a second wave.
5. **n-gram/opening blocking** *(floor, use sparingly)* — Du already has opening-keyed theme-recurrence; a hard
   backstop against re-emitting a recent opening sentence. Not primary — hard blocks distort coherence if overused.

---

## 5. Build order (all flag-gated · observe-first · fail-open · restart-gated)

Per project discipline: **observe before it gates anything.**

- **Phase 0 — SHADOW instrument (build first, changes nothing).** A `core/stream_drive.py` that each cycle
  computes `drive`, `grounded?`, `redundancy`, and the gap it *would* set — and logs to `stream_drive_shadow.jsonl`
  beside the *actual* gap taken. Run for a day. This tells us, on real data, whether the controller would stream
  the right work and rest the right work **before it touches a single live gap.** (Mirrors how `homeostasis.py` /
  `moment.py` were shipped — shadow, verify the signature, only then wire.)
- **Phase 1 — Promote the pacer (Rail A + B) behind `CONTINUOUS_STREAM = False`.** Flip on after the shadow log
  shows the drive/gap curve tracks grounded-progress and rests on redundancy. Keeps every existing fallback path.
- **Phase 2 — Functional gap (Rail C).** Wire grounding-injection + re-seed to the redundancy threshold.
- **Phase 3 — Optional (Rail D.4 temperature kick, n-gram floor)** only if Phases 1–2 leave residual looping.

**Verification signatures (decoupled — measured, not asserted):**
- burst% rises against the idle baseline for **grounded** trains specifically (the `/du-pulse` cadence gauge:
  PULSED → FLOWING → STREAM), while anchor-less self-monologue does **not** fast-loop.
- monoculture concentration (`loop_cluster_probe.py`) does **not** rise — Rail B/C hold the line.
- sleep still fires on schedule (Rail D not eroded).
- self_beats_naive / arousal-trend (protoself) unaffected or improved.

---

## 6. What this explicitly is NOT

- **Not** a scheduler, not a T4 change, not a "pulse" cadence. Those were the accreted meaning; this plan retires it.
- **Not** "delete all gaps." The consolidation gap is kept and protected (Rail D).
- **Not** letting idle self-talk run at machine speed. Grounding-gated by construction (Rail B) — that would
  manufacture rumination, the exact failure the research names.
- **Not** a weight change. Frozen 8B; everything is orchestration-layer.

---

## 7. Honesty flags (carried from the research, do not lose)

1. No published system runs a frozen-weight LLM as a fully clockless continuous stream across *all* work — the
   §3 controller is a synthesis of validated parts (LP-pacing, entropy-halting, similarity-nudge, wake-sleep),
   **not** a cited off-the-shelf design. This is why Phase 0 is shadow-only: we verify on Du's real data first.
2. The AI-native prize — **parallel incubating threads** (hold several grounded trains, let a stuck one incubate
   while others run) — is genuinely beyond "just faster" and is the thing no human can do. It is also the most
   extrapolative claim and is **deferred out of this plan** to a later wave; nothing here depends on it.

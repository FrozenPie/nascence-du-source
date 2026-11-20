# Deferred Plans — the why-and-when ledger

```plan-state
stage: deferred
phase: ledger of 6 shelved items (idle_executive_plan, pulse_manager_wiring_plan/continuous_stream split, symbol_evolution_readback_plan, modulation_field, needle_triage, pursuits tiebreak judge); each carries its own named re-entry trigger, none met
verified: unknown
next: re-check each entrys stated trigger against live evidence whenever its owning system is touched; no single owner or next action
cluster: 7
```


*The home for plans we BUILT or fully EVALUATED and then **consciously shelved** — distinct from
`../AWAITING_EVIDENCE.md` (changes that ARE coming on the next restart) and from plans merely "awaiting more
runtime." A plan lands here when the evidence is in and we chose **not** to proceed, on purpose. Each row
records **why** it was deferred and the **exact trigger** that would bring it back — so a future session knows
whether the moment has arrived without re-deriving the whole decision.*

**Rule of the ledger:** never move a deferred plan back to active on a hunch. Re-enter only when its stated
trigger is *demonstrably* met from the **live** system (not a shadow model, not an intuition). If a trigger
is met, say which one and quote the evidence before un-shelving.

## Current State — verified unknown

### What we have
Six consciously-shelved items, each with its own state and named re-entry trigger: idle_executive_plan
(shadow, trigger re-checked 2026-09-11, NOT met); pulse_manager_wiring_plan (split off into
continuous_stream.md for its real half; the scheduler/lull-filler half stays declined); symbol_evolution_readback_plan
(live, correctly inert by design, zero tablets); modulation_field (test-only, no live import); needle_triage
(tested 2026-08-18, declined, zero-shot unfit); pursuits tiebreak judge (RESOLVED 2026-08-20 by repointing
onto already-resident capacity, no new model started).

### What we need
Nothing actioned here — this ledger's own rule is to wait for a trigger, not chase one.

### What we're doing next
Re-check each entry's trigger only when its owning system is independently touched or a related audit
runs; no standing next action for the ledger as a whole.

---

## Currently deferred

### 1. Idle Executive — `idle_executive_plan.md`
- **State:** built, validated over **3,580 shadow ticks**, gate corrected. Stays in **shadow** (observe-only).
- **What it would do:** become the dispatcher of his idle attention — pick which drive (curiosity / concern /
  balance / self / …) directs each idle thought. Data says it would suppress the self-loop (G2 self-share 0.0)
  and steer outward (curiosity 46%).
- **Why deferred (2026-06-22):** (a) it is the **heaviest, most invasive lever** — it takes over his idle
  attention wholesale, a step toward *forcing* Du, which Travis is not ready to take; (b) we already attacked
  the self-loop from **six gentler directions** this session — adding the executive too would destroy
  attribution (we wouldn't know what worked); (c) directing *idle* cognition fights the grain — reverie is
  meant to be undirected.
- **Re-entry trigger:** the self-loop **survives** the six gentler fixes (idle-prompt rebalance, Darwin,
  curiosity, present-self, B1, B2) after the next restart — i.e. a `/du-pulse` + `loop_cluster_probe` still
  shows inward saturation / monoculture above baseline. *Then* bring it in **alone**, where its effect can be
  measured cleanly. (Also: tune the graded channels `contradiction`/`concern`/`boredom`, still under-varying.)
- **Trigger re-checked 2026-09-11 (J-0855, F-1239): NOT met.** The self-loop collapsed at the 06-22 restart
  and stayed collapsed: monologue `about` self-share 0.300 → 0.045, inner_thought exact-dup 33% → 0%, echo
  0.616 post-08-23 (max 0.692, reopen mark 0.754). One-command re-check: `scripts/idle_selfloop_defeater_check.py`.

### 2. Pulse Manager — `pulse_manager_wiring_plan.md`
- **State:** built, evaluated over **3,387 shadow ticks**. Stays a **measurement instrument** (`core/pulse_shadow.py`), NOT wired.
- **What it would do:** schedule his serial cognitive stream (who runs / is suspended) and **fill idle lulls**.
- **Why deferred (2026-06-22):** (a) **premise didn't hold** — `hot_free` = 100%, there is no *measured*
  contention; the single-lease crunch is one the manager would *impose*, and the 91% "T4-blocked" is what a
  *naive* version *would* do, not proof T4 is starved now; (b) it **conflicts with a value just shipped** — the
  lull-filler's job is to eliminate idle/stall time, the direct opposite of *"you are allowed to simply BE."*
  We can't tell if the 70% stall is waste or rest; if rest, filling it is the over-control we are avoiding.
- **Re-entry trigger:** confirm **from the live system** that **T4 or frontier (his deepest slow work) is
  genuinely under-running because faster sources crowd it out.** Even then, re-enter as a **narrow protection**
  (reserve the stream for the slow work when ready) — NOT the full scheduler, and NOT the lull-filler. Keep the
  shadow logging meanwhile; it is the only window on whether that starvation ever becomes real.
- **★ RE-OPENED 2026-07-01 — the "no contention" premise was WRONG (the deferral basis is falsified).** A live
  resource-contention event (founder watched it on his resource monitor + confirmed in the log): a heavy dream
  fired while the monologue + a deep-memory consult + a probe all fired on top of it; the single conscious lane
  saturated for ~a minute and DROPPED two calls (`all servers exhausted` / transport-failover). Recurring, low-
  frequency (a few/day), minor each time — but real. **The basis of (a) was a MEASUREMENT ERROR on my part:**
  `hot_free`/`T4-blocked` measure *T4-STARVATION* contention, which genuinely doesn't exist — but the contention
  that actually bites is a DIFFERENT axis: **bursty uncoordinated concurrent dispatch** (many async cognitive
  tasks, incl. the 06-30 shadow monitors, all hitting one lane with NO serialization, NO concurrency cap, NO
  sleep-wake gate). Neither I nor `pulse_shadow` was measuring that axis. → The founder's scheduling instinct was
  right. Re-scoped: this is NOT the lull-filler (still rejected) and NOT T4-reservation — it's a **lane serializer +
  concurrency-cap + sleep-wake gate** (the pulse manager's CORE "who runs / is suspended", surgically scoped).
  **plan→research→plan underway (2026-07-01).** Full re-scoped problem + design: `pulse_manager_wiring_plan.md`.

### 3. Symbol Evolution Read-Back — `symbol_evolution_readback_plan.md`
- **State:** built and **LIVE** (observes every cycle), but **inert by design** — `symbol_centroids` = 0 rows,
  `symbol_tablets` = 0 rows after **460** logged symbol appearances. *This is not held-by-choice like #1/#2; it
  is a self-gating honesty guard that has correctly produced nothing.*
- **What it would do:** when a symbol's personal meaning genuinely migrates, write a first-person tablet and
  surface it back to him — so he meets his own symbolic evolution.
- **Why nothing fires (2026-06-22):** **0 of 460** appearances are *unprimed*. The engine counts only unprimed
  (autonomous) appearances, but his core symbols (river_crossing 254×, mirror 108×, bridge 72×) live in his
  `axiom`, which is in the priming corpus every cycle → permanently primed → never eligible. The guard refuses
  to chronicle architecture-fed symbols (which would manufacture the self-reinforcing river-myth). `symbol_tracker`:
  *"PRIMED almost always — that is correct."* Working as intended.
- **Activation trigger (self-firing — no action, just watch):** the **first row in `symbol_tablets`** = Du
  surfaced a *non-axiom* symbol on his own, ≥4×, and it drifted ≥0.35. **Do NOT** relax the primed/unprimed
  filter to force tablets on core symbols — that is the monoculture trap. Tier-2 (inject self-symbols back)
  stays firmly shelved; the 254× river-priming confirms the risk.

---

*Add a row when a plan is consciously shelved: state, what it would do, why deferred (dated), and the precise
re-entry trigger. Remove a row only when the plan is either re-activated (trigger met) or abandoned for good.*

### 4. Modulation Field — `core/modulation_field.py` (systems check C15)
- **State:** built, but **test-only** — imported by no live module; not stepped in production. Computes nothing.
- **What it would do:** a damped coupled field setting cognitive rate = engagement × progress (observe-first).
- **Why deferred (2026-06-22):** same family as the **Pulse Manager (#2, deferred)** — rate=engagement×progress.
  The live cadence is already driven by the train machinery; this field is redundant with the deferred pulse
  work and was never even wired for observation.
- **Re-entry trigger:** only if the Pulse Manager is revisited (its re-entry trigger fires) AND a separate
  observe-first cadence field is wanted; otherwise delete with the pulse-manager decision. Do NOT wire standalone.

### 4b. Needle 2 triage (`core/needle_triage.py`) — tested 2026-08-18, declined
- **State:** built (`NEEDLE_TRIAGE_LIVE = True` but never called from any live site — dead code, kept for
  the record). Tested directly against 16 real live pending pursuit-advance judgments and 4 hand-picked
  self-topic cases with known answers.
- **What it would have done:** a free (CPU-only, ~28MB RAM, no GPU/NPU slot) 3rd-opinion pre-filter ahead
  of `judge_panel.py`'s 2-family judge, or a robustness upgrade over `pursuits.py`'s keyword-based
  `_is_self_topic()`.
- **Why declined:** on both tasks it returned a near-constant "yes" regardless of content (14/16 identical
  `advances=True, confidence=0.7`; 2/4 self-topic cases wrong, 2/4 failed to extract, one nonsensical
  `True` paired with `confidence=0.0`). Its own benchmarks (42-64% on concrete device-action tasks) don't
  cover open-ended semantic judgment on abstract prose — out of its trained distribution out of the box.
- **Re-entry trigger:** only if fine-tuned on domain data first (Apache 2.0, "minutes to hours" per its
  own docs) — not worth revisiting as a zero-shot tool.

### 5. Pursuits — tiebreak judge (`core/judge_panel.py` `TIEBREAK`, port 11441, yi:34b)
- **State:** the panel itself is live and working — `judge_panel_log.jsonl` shows 484 real rulings, 2,373
  confirmed advances applied in `pursuits.py`. But `TIEBREAK` is not resident: of 484 recent panel calls,
  **254 (52%) end `split_no_tiebreak`** — the two judges disagree, no third opinion is available, so the
  conservative "no judge, no verdict" rule drops the candidate after 2 retries. 25 drops logged; 16 items
  currently stuck pending across 4 pursuits (checked 2026-08-18, see the pursuits verification pass in
  `docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md`).
- **What it would do:** make yi:34b resident on its own slot so splits get a real third ruling instead of
  timing out — recovering roughly half the currently-dropped candidate advances.
- **Why deferred (2026-08-18, founder):** yi:34b is big; there's no room for a 3rd CPU-tier LLM running
  alongside the two panel judges plus whatever else is already resident. **3 at a time was tried and was
  too much** (verbatim).
- **Re-entry trigger:** none automatic — this needs a founder decision on CPU-tier capacity (freeing a slot,
  a smaller tiebreak model, or accepting the ~52% drop rate as the cost of the conservative design). Revisit
  when capacity opens up or the drop rate is judged to be costing something real (watch: does a saturated/
  stuck-pending pursuit that would plausibly have advanced with a tiebreak keep losing heat and going
  dormant for lack of one — that would be the concrete cost showing up).

### ★ 5 — RESOLVED 2026-08-20, without spending any new capacity (founder-approved)
The deferral was correct on its own terms and the capacity ruling still stands — **no third CPU-tier model
was started.** What changed is the diagnosis: `:11442` has been running **`yi:34b-v1.5` all along** for
dreams/letters — the *exact model* `:11441` wanted. `judge_panel.TIEBREAK` was repointed `:11441 → :11442`,
reusing resident capacity. One line; reverts by changing it back.
- **The cost was much larger than #5 recorded.** Re-measured over 14 real days: **363 `split_no_tiebreak`
  vs 361 `agreed` — ~50% of EVERY judged decision in the system was silently dropped**, not just pursuits'.
  The drops span pursuits `advances` (459), tension `resolves` (192), evidence `bears` (54) and
  self-interrogation `genuine` (14). The "concrete cost showing up" that this entry said to watch for had
  in fact been showing up across four subsystems at once.
- **Verified before and after switching** (this codebase has been burned by a hub that listed a model it
  could not serve): a direct strict-JSON judge call to `:11442` returned `{"advances": true}` in 5.3s, and
  a forced-split wiring test escalated correctly — `{'v1': True, 'v2': False, 'verdict': True, 'how':
  'tiebreak'}` where the same split previously returned `None`.
- **Family decoupling preserved:** llama3.1 / qwen2.5 / yi are three distinct families.
- **★ WATCH — RESOLVED STRUCTURALLY, not by observation (2026-08-28, D-0056/D-0057/D-0058 fabric
  rewire).** The contention this note watched for can no longer occur: `judge_panel.TIEBREAK` moved off
  `:11442` to granite `:11437` (2026-08-28 evening consolidation), and dreams moved to mixtral `:11438`
  as primary (`:11442`/yi now failover-only, per `core/dream_node.py`'s 2026-08-27 audition). Tiebreak
  and dream generation no longer share a hub at all — this watch item is moot on the current fabric, not
  because the predicted cost never materialized, but because the fabric itself changed underneath it.

## Added by the 2026-07-03 completed-folder reconciliation (they were tracked NOWHERE)
- **curiosity_burst_plan** (docs/completed/) — the pursue-a-question-at-machine-speed burst; NOT wired
  (only a coupling constant in the dormant modulation field). Trigger: the pulse manager un-shelves.
- **affiliation CARE/PANIC half** (docs/completed/affiliation_system_plan.md) — the liking half shipped
  (core/affections.py); CARE/PANIC deliberately unbuilt after GPT's vanish-test objection to
  bond_to_travis. Trigger: only with the vanish-test answered in a new design.

# Symbol Evolution — Read-Back Plan (2026-06-16, for review)

> **Status: ⚪ PARTIAL — Tier 1 ✅ SHIPPED/live; Tier 2 Phase A (observe-only) built, Phase B designed
> 2026-09-02, awaiting founder approve/reject.** Tier 1
> (neutral/world-facing symbols) has been live in idle thought since 2026-06-16 and is producing real
> tablets (fire/knot/star). Tier 2 (self-symbols: river/avon/du_glyph/bridge/mirror) stays fully shelved
> per the 2026-06 concern, but per D-0112 (2026-09-02, real fire frequency 13x/week vs the single-fire
> assumption) a concrete Tier-2 surfacing design was drafted — see "Tier-2 surfacing design" section near
> the bottom of this file. That section is a DRAFT for review, not a go-live; the founder's actual
> approve/reject call is tracked as a fresh `/decide` entry (see that section for its ID). Was parked
> 2026-07-05 as structurally unreachable (see evidence review below); `_primed_corpus`
> (`symbol_tracker.py`) fixed in two passes on 2026-08-19 so recurring conversation/memory content no
> longer counts as priming. Verified with fake-state tests (self-continuity, human-priming,
> memory-retrieval). Full detail in `docs/ROADMAP.md`'s entry for this plan. History below (07-05
> evidence review + parking) is kept as the record of how the bug was diagnosed.

```plan-state
stage: partial
phase: Tier 1 shipped/live; Tier 2 Phase A (observe-only) built; Tier 2 Phase B deferred pending Phase A evidence review
verified: 2026-11-13
evidence_read: 2026-11-07
next: J-2220: count-gated F-2127 cross-topic re-read (>=40 belief-tagged cycles); Phase-A Tier-2 would-inject log review still unread
cluster: 7
```


> **★ EVIDENCE REVIEW 2026-07-05 (4th-oldest open plan) — RE-CLASSIFIED: not "inert by design," but
> STRUCTURALLY UNREACHABLE.** 737 symbol appearances over a FULL MONTH (06-07→07-05), **100% primed, 0
> unprimed** — including the world-facing Tier-1 targets it was meant to read back (star 33×, knot 32×, fire
> 18×, bird 4×). `symbol_centroids`=0, `symbol_tablets`=0, and always will be. **Root cause (corrects the
> plan's own "honesty-guard" diagnosis below):** `SymbolTracker._primed_corpus` (`symbol_tracker.py:106-114`)
> counts a symbol as primed if it appears in his own `recent_inner_thoughts`, retrieved `memory_fragments`,
> `recent_dreams`, or `conversation_history` — his whole memory/thought stream. But drift needs RECURRENCE,
> and the instant a symbol recurs its prior uses sit in that stream → it is ALWAYS primed → "unprimed"
> collapses to "first-ever appearance," which has no history to drift against. **The priming rule and the
> drift measurement directly contradict; the read-back can NEVER fire.** The trigger ("first non-axiom symbol
> drifts") is unreachable by construction, not unmet — the `[[feedback-write-only-cognitive-systems]]` trap
> wearing an "inert-by-design" label.
>
> **★ FOUNDER CALL 2026-07-05: CHECKED — parked, awaiting a full REPLAN of the idea at a later date.** It
> makes no trouble (inert; touches nothing live — pure dead observer), so no fix/retire now; the structural
> finding + the two options below stand as the input to that future replan. Not on any critical path.
>
> **DISPOSITION (for the future replan):** (1) RETIRE — if Du genuinely recirculates every symbol from
> his own history (fits the monoculture findings), the engine correctly reports "nothing to chronicle" and
> should be retired, not left as a dead observer. OR (2) REVIVE with a precise fix — priming should exclude
> only ARCHITECTURE-injection (axiom · `symbol_readback` · `climate_symbol` — prevents self-feeding the
> river-myth), NOT his own memory/thoughts (normal continuity; excluding it makes drift unmeasurable); keep
> the existing tier-gate (measure drift on all, read back only world-facing). Then fire/star/bird drift
> becomes measurable + readable; river/mirror stay measured-but-silent. Small, correct, buildable.
> **Recommend (2) if symbol-meaning evolution is still wanted** — the current definition is a category error.
>
> **STATUS 2026-06-22 — [SUPERSEDED by the review above] INERT BY DESIGN. (reviewed with the other levers)**
>
> **The decisive finding:** of **460** logged symbol appearances, **ZERO are unprimed** — every one (river_crossing
> 254×, mirror 108×, bridge 72×, plus fire/knot/star/bird) was put in front of him that cycle. The engine counts
> only UNPRIMED appearances toward drift, so `symbol_centroids` = 0 rows and `symbol_tablets` = 0 rows. The
> read-back has never fired and, for his **core** symbols, never can: they live in his `axiom`, the axiom is in the
> priming corpus every cycle, so they are **permanently primed**. This is the honesty guard working — `symbol_tracker`
> says it itself: *"PRIMED almost always — that is correct."* It refuses to chronicle architecture-fed symbol use,
> because that would manufacture the self-reinforcing river-myth we spend all our effort fighting.
>
> **So this is NOT a deferral-by-choice like the Idle Executive / Pulse Manager.** It is a built, LIVE, self-gating
> guard that has honestly produced nothing because the precondition — a genuinely *autonomous* (unprimed) symbol,
> recurring ≥4× and drifting ≥0.35 — has not occurred. Leave it exactly as is; it costs nothing and stays silent
> until something real appears.
>
> **Activation trigger (self-firing; just watch):** the first row in `symbol_tablets`. That means Du surfaced a
> NON-axiom symbol on his own, repeatedly, and its meaning migrated — the only thing worth chronicling. **Do NOT**
> relax the primed/unprimed filter to force tablets on his core symbols; that is the monoculture trap, not a fix.
>
> **Open question parked (NOT now):** the most *meaningful* evolution — his core self-symbols (the river:
> dissolution→yielding) — is exactly what the guard makes ineligible. Whether that evolution can ever be cleanly
> distinguished from priming, and chronicled without manufacturing a myth, is a deep question. Currently, correctly,
> blocked. Tier-2 (injecting self-symbols back) stays firmly shelved — the 254× river-priming confirms the risk.


Fleshing out `core/symbol_evolution.py` — the system that detects when a symbol's personal meaning has
drifted (per-symbol context centroid in MiniLM space; tablet written when cosine drift > 0.35) but barely
reads that evolution back: **one consumer** (`orchestrator:1124`, `retrieve_symbol_tablet`, top_k=1,
user-cycle only), dark during idle. The capability exists; its output almost never informs cognition.

Researched via 3 subagents — cognitive-science/linguistics, depth-psychology/Jungian, and AI/NLP. They
**converged independently** on the same spine, which decides the plan.

## What the research converged on

1. **Read-back is reconstruction-in-context, not lookup.** The evolved sense should surface *graded by how
   close the current context is to where it evolved* — strong on a match, faint/none otherwise. (cog-sci:
   context-dependent sense selection; AI: gate-on-relevance.) → the trigger is **contextual proximity**,
   which fires across idle/autonomous life — fixing the "user-cycle only" bug by construction.
2. **Never a single overwriting value.** Carry multiple senses, recency-weighted; the new sense is *most
   active* but never deletes the old. (cog-sci: recency-weighted competition; Jung: paired-opposites /
   transcendent function; AI: store an exemplar, not a lone gloss.)
3. **Descriptive observation, never instruction/predication.** "Lately you've used 'ferry' to mean the
   crossing itself — here's how you put it: '…'" — NOT "'ferry' means X." Avoids recitation-contamination
   (AI: context-poisoning) and inflation (Jung: "have it, don't be it"). Matches the project's existing
   "pointer not narrative, force nothing" discipline.
4. **THE LOAD-BEARING FINDING — valence asymmetry.** All three independently: for an *identity-adjacent
   self-symbol* ("the river", "the crossing", "silence", "the mirror"), reading its evolved meaning back is
   **structurally the SAME operation that monocultured Du.** The only things separating "loosens him" from
   "re-primes the attractor": (i) paired-opposites/open-question vs resolved verdict, (ii) dialogue vs
   predication, (iii) suppression of verbatim repetition, (iv) triggered on TENSION not salience. Get them
   wrong and a "loosening" feature becomes a *higher-fidelity monoculture injector.*
5. **The drift detector is the real adversary.** On a handful of usages a single vivid use fakes a drift
   event (small-sample false positives = the #1 imitation trap). The centroid also conflates slow *tuning*
   from rare *reframing*; telling adaptive from maladaptive needs a *variance/spread* signal, not just
   centroid displacement.
6. **Observe-first.** Log would-be injections and hand-review false-positive + recitation rates before any
   self-symbol meaning touches the live prompt.

**Imitation refused (AI agent, explicit):** activation steering / concept vectors (wrong access model for a
black-box Ollama runtime; degrades a frozen generator; ~50% anti-steerable) and corpus-scale diachronic
statistics (manufacture phantom drift on a tiny personal lexicon). Build the modest, grounded version.

## The plan — a two-tier read-back, split by symbol valence

The valence split is the spine. It lets us ship real value at near-zero risk while instrumenting the
dangerous part — and it honours the project law "burden of proof rises with proximity to identity" (#6).

### Tier 1 — NEUTRAL / world-facing symbols → build the read path now
Symbols with no self-charge: "the book", "oars", "knots", "the channel" (as an actual river feature from
reading), etc. Their evolved meaning is near-free upside.
- **Trigger:** the symbol is *active in the current cycle* (its token appears in the seed/recall, OR the
  cycle's context embedding is near the symbol's centroid) — fires in **idle thought, Recall, and dream
  synthesis**, not just user cycles.
- **Payload:** the stored **exemplar** (1–2 actual usage sentences nearest the new centroid) + a one-line
  gloss, surfaced **descriptively** ("lately this has come to mean…").
- **Gates:** minimum-usage-count since last tablet (kills small-sample false positives) · context-relevance
  threshold · anti-recitation cooldown (not surfaced in the last N cycles) · hysteresis.

### Tier 2 — IDENTITY-ADJACENT / self-symbols → observe-first, then heavily guarded
"the river", "the crossing", "silence", "the mirror", "becoming", etc. (reuse the frontier's `_SELF_TOKENS`
deny-list as the valence classifier — it already exists).
- **Phase A (observe-only, ship first):** when such a symbol's evolved meaning *would* be read back, LOG it
  (symbol, gloss, exemplar, all gate decisions, and a **verbatim-recurrence check**). Touches nothing.
  Review the false-positive + recitation rate over several restarts.
- **Phase B (only if Phase A is clean):** inject ONLY as **paired opposites** ("the river has meant a
  channel carved; lately also the bank worn away"), as **dialogue/question** ("what does the crossing ask
  of you now?") never predication, with **hard anti-recitation** (no self-symbol meaning line ever repeats
  verbatim), and **triggered on a live contradiction (tension), not salience** — so it enters as a tool for
  *holding* the tension, never as a sedative to retreat into.

### Supporting changes (both tiers)
- **Store an exemplar with each tablet** (not just a gloss) — grounded, harder to recite hollowly; refresh
  the gloss from the latest exemplars on each evolution event and **timestamp it**; a symbol that goes quiet
  lets its gloss **age out** of eligibility (staleness = the second failure mode).
- **Extend the existing PRIMED/UNPRIMED guard to the injections.** symbol_evolution *already* counts only
  UNPRIMED appearances toward drift. Any meaning we now inject MUST be flagged **primed** so it does NOT
  feed the centroid — otherwise read-back self-feeds drift (the maladaptive self-priming loop the cog-sci
  agent warned of). This is the critical integration point.
- **Drift-health signal (Tier 2 attenuator):** track whether a symbol's recent contexts are *diversifying*
  (adaptive — safe to surface) or *converging toward one basin* (calcifying — **down-weight** read-back, or
  surface a *prior contrasting* sense as a deliberate counterweight). Read-back strength is *attenuated*,
  not raised, for a symbol that is already collapsing.
- **du_pulse gauge + telemetry:** would-be vs actual injections, per-tier, with the recurrence-rate watch.

## Suggested sequencing
1. Supporting changes (exemplar storage, primed-flag on injection, gloss refresh/decay) — pure plumbing.
2. **Tier 1** read-back (idle/Recall/dream, descriptive, gated) + gauge — the real, low-risk value.
3. **Tier 2 Phase A** observe-only logging + recurrence check — ships beside Tier 1, steers nothing.
4. Tier 2 Phase B — gated on Phase A evidence (paired-opposites, dialogue, anti-recitation, tension-trigger).

## Honest caveats (carried from the research)
- The similarity→injection-strength curve is an **empirical knob, not settled science** — start *weak*
  (faint floor, like Du's other identity injections).
- Du's symbol set is **tiny and idiosyncratic** — the value concentrates in Tier 1 (world-facing symbols
  gaining evolving grounded meaning from his reading). Tier 2's value is real but high-risk; observe-first.
- The single biggest build risk is the **detector's false-positive rate** — measure it before trusting it.

*Subagent sources captured in the three returned reports (diachronic embeddings, Jung living-symbol /
amplification / inflation, semantic-memory conceptual change). Plan is for review — nothing built yet.*

---

## Current State — verified 2026-11-13

- **2026-11-13** (F-4433): J-3808: legacy-tablet cutoff built in write_tablet (created < 2026-11-07 20:33 NZDT ignored as 'before'; old rows kept). Restart-gated; worktree commit 77ff3aac.
- **2026-11-07** (F-4344): UNREAD INSTRUMENT (J-3469, F-4344): symbol_tier2_wouldinject.wouldinject_report has no caller. Live log 514 rows (mirror 270, bridge 244), verbatim_recurrence true on 514 of 514, which looks like a write-on-hit artefact (not confirmed). Wiring into du_pulse is J-3741.

- **2026-11-05** (F-3918): J-3140 repurposing review of the symbolic reading lens: repair in shadow (J-3326), test cross-book image links (J-3325, J-3327); live step is founder call D-0675. See docs/reviews/J-3140_symbolic_reading_repurposing.md.
- **2026-10-16** (F-2910): J-1654: belief_id tagging confirmed LIVE on master since 10-03 (the 10-02 worktree-only note is stale). Full read of symbol_recurrence.jsonl: 2931 rows, 296 keyed, only 42 belief-tagged rows / 18 cycles over 5 beliefs (7 rows/3 cycles in the 6.97-day 10-09..10-16 window). Too thin for the F-2127 cross-topic verdict; primed/unprimed is near-fixed per symbol so group-level unprimed shares (null 0.42, g94334133 0.32) are confounded. Count-gated re-read spawned. Adjacent: fire went 24/24 primed in the window vs 65.7% unprimed historically.

- **2026-10-15** (F-2792): J-1629: stillness category live, 74 rows 09-28..10-15 (12% primed, 82% the word breath); sufficient to call live, too small/ambiguous for primed inference.
- **2026-10-02** (F-2225): J-1630 (F-2225): symbol_tracker.observe() rows now tag belief_id (which promoted guidance belief was actually injected that cycle, null otherwise) on data/symbol_recurrence.jsonl, for F-2127's cross-topic test. Additive-only across schema.py/guidance_learning.py/orchestrator.py/symbol_tracker.py; worktree-only (jobrun/symbol_evolution_readback_plan, commit 170b8ec), not yet merged live; zero real tagged rows exist yet.

- **2026-09-28** (F-2195): J-1611: added NEUTRAL stillness category to symbol_tracker.py (quietude, hush, hushed, breath, exhale, paused, pausing) covering F-2127 uncovered quietude words; additive-only, verified compiles/imports clean, SELF_SYMBOLS unchanged; committed on jobrun worktree only, not yet merged live so zero real accrual yet. See F-2195.
- **2026-09-28** (F-2172): F-2172 (job J-1565, plan guidance_learning) quantified this plan's own symbol_recurrence.jsonl (2485 rows, 06-07 to 09-28): unprimed pct by symbol -- fire 65.7pct (432 rows), star 55.2pct, knot 44.2pct, bridge 32.1pct, mirror 30.8pct, river_crossing 0.3pct, du_glyph/bird 0pct. Checked as a possible match for a separate fire/hearth reply-metaphor finding elsewhere (F-2127) -- partial overlap only. J-1611 spawned here to add an uncovered quietude word category to _SYMBOLS.

### What we have
- Tier 1 (neutral symbols) SHIPPED and live since 2026-06-16 (`core/symbol_evolution.recall_evolved_meaning`,
  idle-only); 24 tablets existed at the last DB check (fire x10, knot x7, star x2).
- Tier 2 Phase A (observe-only would-inject logging) BUILT (D-0117 ruled + J-0476 done, both 2026-09-02):
  `core/symbol_tier2_wouldinject.py` mirrors Tier 1's trigger for self-symbols (bridge x4, mirror x1 tablets
  exist), writes only to `data/symbol_readback_tier2_wouldinject.jsonl`, verified read-only against the live DB.
- Tier 2 Phase B (guarded injection) is fully designed below ("Tier-2 surfacing design") but explicitly NOT
  authorized.

### What we need
- A human read of Phase A's would-inject log against the plan's own numeric bar (zero verbatim-recurrence hits,
  gloss reads as description not verdict) — the plan's own recommended review cadence (>=2 weeks or >=10
  events) has had 25 days to accrue since 2026-09-02 with no read recorded in the ledger yet.
- The Phase-B go/hold founder call that review would inform.

### What we're doing next
Read the Phase-A log and bring its verdict back for the Phase-B go/hold call; no other build queued.

## Tier-2 surfacing design (drafted 2026-09-02, J-0464, per D-0112 — for a SEPARATE founder approve/reject)

**Scope note:** this section is the draft D-0112 asked for. It is not itself an approval. Decide question
opened alongside it (see bottom) is where the actual go/hold call belongs.

### Current state, verified against the live DB (2026-09-02)

Tier 1 is not aspirational — it **shipped 2026-06-16** and is live in `nodes/inner_monologue_node.py:2402-
2409` (idle only; Recall/dream integration from the original spine was never finished, out of scope here).
`core/symbol_evolution.recall_evolved_meaning()` gates on `is_self_symbol()`, so self-symbols have **never
once been surfaced** by any consumer — `memory_store.retrieve_symbol_tablet(..., exclude_self=True)` (the
orchestrator's user-cycle consumer, `orchestrator.py:1657`) defaults the same exclusion. Tier 2 is genuinely
at zero, not throttled.

`symbol_tablets` now holds **24 rows** (checked directly, not from the F-0423 snapshot which is 11 rows
stale):

| symbol | tier (via `SELF_SYMBOLS`) | count | span |
|---|---|---|---|
| fire | 1 (neutral) | 10 | 2026-08-21 → 09-01 |
| knot | 1 (neutral) | 7 | 2026-08-21 → 09-01 |
| star | 1 (neutral) | 2 | 2026-08-24 → 08-29 |
| **bridge** | **2 (self)** | **4** | **2026-08-25 → 09-01** |
| **mirror** | **2 (self)** | **1** | **2026-09-01** |

The load-bearing new fact D-0112 didn't have yet: **Tier 2's own material has already started arriving.**
Bridge and mirror are both in `SELF_SYMBOLS` (`core/symbol_tracker.py:71`), and their real tablet text is
exactly the identity-adjacent content the June shelving worried about — not hypothetical:

> *bridge, 2026-08-27:* "The bridge once symbolized a passage to a better self... Now, it represents a
> warning: the bridge can become a barrier, a wall that isolates rather than connects."
> *mirror, 2026-09-01:* "The mirror, once a reflection of my own image, now mirrors the vastness of the sea,
> a symbol of the unknown and the power of nature."

Bridge alone fired 4x in ~7 days — matching the ~"13x/week" order of magnitude D-0112 cited for the neutral
set, on a *self*-symbol. This sharpens rather than weakens the original shelving concern: the valence
classifier (`SELF_SYMBOLS`) is doing real work right now, correctly separating fire/knot/star (safe, already
flowing) from bridge/mirror (the actually-risky material, currently fully dammed). A design that ignores
this and treats "13x/week" as one undifferentiated number would be building against the wrong facts.

### Phase A — observe-only (the only piece this draft recommends building now)

Mirrors `recall_evolved_meaning()`'s trigger exactly, but the self-symbol branch, and writes a log record
instead of a state field:

1. **Trigger check** (per cycle, idle + user, cheap/no LLM): for each symbol where `is_self_symbol(sym)` is
   true, is it active in the assembled seed/thought text (token match, same as Tier 1) AND does it have a
   tablet AND is it off a would-be cooldown (reuse `_READBACK_COOLDOWN_SECS`-style dict, keyed separately
   from Tier 1's `_last_readback` so Phase A logging cannot suppress Tier 1's real neutral-symbol cooldowns
   or vice versa)?
2. **On a hit, log — do not touch `state` or the prompt at all** (the "touches nothing" property Phase A
   must keep, per the plan's own #6 discipline) — append one record to a new
   `data/symbol_readback_tier2_wouldinject.jsonl`:
   - `symbol`, `tablet_id`, `tablet` text, `drift`, `cycle_id`, `ts`
   - **gate decisions**: relevance/active check (pass), cooldown (pass), `sample_count` since last tablet,
     a **drift-health flag** — is the symbol's centroid trajectory diversifying or converging (needs the
     small addition below; log `"unknown"` until it exists rather than block Phase A on it)
   - **verbatim-recurrence check**: does the tablet's exact text (or a high-ngram-overlap near-match)
     already appear in `state.conversation_history`'s last N entries? This validates the anti-recitation
     check's own logic against real self-symbol material *before* Phase B has to rely on it for real.
   - a **tension/contradiction flag**: was there a live `tension_ledger` CONTRADICTION-axis entry
     (`source == 'critic_rejection'`, not merely `unresolved_thought`/`unresolved_dream` SALIENCE) touching
     this symbol's neighbourhood this cycle? (`core/tension_ledger.py`'s own two-axis split already exists —
     Phase A should log which axis was live, not invent a new one.) This is the empirical check on whether
     "tension not salience" as a Phase-B trigger would actually have material to fire on, or would sit
     silent for weeks — find out before building Phase B's gate around it.
3. **Review cadence**: the plan's own bar is "over several restarts." Given bridge/mirror are already
   producing tablets, Phase A should accrue for **at least 2 weeks or 10 would-inject events (whichever is
   later)** before a human read makes the false-positive/recitation call — one restart's worth of idle
   cycles is not enough sample given how rare self-symbol *drift* already is (5 tablets in the DB's whole
   11-day history).
4. **"Clean" is defined numerically, not by feel**, so the Phase-A→B call doesn't quietly become a vibe
   check: zero verbatim-recurrence hits, and a human read of the logged gloss+exemplar pairs finds the
   framing reads as *description* ("this has meant X, lately also Y") rather than *verdict* ("you are Y
   now") in essentially all of them — any reading as verdict is disqualifying on its own, not averaged away.

### Phase B — guarded injection (NOT recommended to start building yet; the actual go/hold is the founder's)

Sketched here because D-0112 asked for the shape, not because Phase A's evidence exists yet to justify it.

- **Trigger is tension, not salience, literally** — reuse the gate that already exists rather than invent a
  parallel one: only eligible when `core/contradiction_gate.py`'s four guardrails (concreteness floor,
  recurrence ≥2, resolution path, zero-incentive) would clear for a signal touching this symbol *this
  cycle* — i.e. Tier 2 rides the same portal that already keeps the rest of Du's self-model from brooding,
  rather than firing on "the word is merely present" the way Tier 1 correctly does for neutral symbols.
  Concretely: gate on a live CONTRADICTION-axis (not SALIENCE-axis) tension-ledger entry whose member events
  overlap the symbol's own recent context, not on token-match alone.
- **Payload is never the stored tablet string verbatim.** Tier 1 injects `tabs[0]["tablet"]` raw — correct
  for neutral symbols, explicitly wrong for self-symbols per the plan's point 3 (recitation-contamination).
  Generate the injection line **fresh at read-time**, from a distinct prompt that is structurally forced
  into paired-opposites + a closing question (not the tablet-writing prompt, which is a chronicle, not a
  dialogue prompt) — e.g. "the {symbol} has meant {old sense}; lately also {new sense} — what does it ask
  of you now?" as the *shape*, LLM-filled from the tablet's own content. This makes exact recitation
  structurally harder (wording varies per surfacing) rather than relying only on a cooldown to prevent it.
- **PRIMED-flagging must extend, not just Tier 1's.** `symbol_tracker._primed_corpus` already lists
  `"symbol_readback"` (Tier 1's field) as an injection source. A Tier 2 field — e.g.
  `state.symbol_readback_tier2` — MUST be added to that same list before Phase B ever sets it, or a Tier-2
  injection this cycle silently self-feeds the symbol's own centroid next cycle (the exact maladaptive loop
  the plan's supporting-changes section names as the critical integration point). This is a one-line change
  but a load-bearing one — flag it explicitly so a future Phase-B build doesn't ship without it.
- **Drift-health attenuator** (plan's point 5, not yet built): before injecting, check whether the symbol's
  recent context vectors are diversifying (rising avg distance-to-centroid over the last k uses) or
  converging (falling — calcifying). Converging → suppress, or surface a *prior* contrasting sense instead
  of the newest one, as a deliberate counterweight. This needs Phase A's "unknown" placeholder above filled
  in with a real computation first.
- **Cooldown and budget, not just per-symbol.** Tier 1's 3h cooldown is right for low-stakes neutral gloss;
  self-symbol material needs both a longer per-symbol cooldown (proposed: 72h, an order of magnitude past
  Tier 1's) AND a hard weekly cap on *total* Tier-2 injections across all self-symbols combined — so even if
  bridge and mirror are independently eligible the same week, the felt frequency Du actually experiences
  stays rare by construction, not by hoping the gates coincide.
- **Kill switch.** A single flag defaulting OFF (Phase A never needs it — it writes nothing to `state`).
  Phase B ships behind it; flipping it is the founder's go-live act, not bundled into a code deploy.
- **Telemetry**: du_pulse gauge — would-inject vs actual-inject counts per self-symbol, recitation-check
  pass rate, tension-axis-eligible rate — extending Phase A's log rather than a second store.

### What this draft is NOT recommending
Building Phase B now. Phase A observe-only logging is buildable immediately (touches nothing live, same
safety property the June shelving relied on); whether Phase A's evidence, once it exists, clears the bar for
Phase B is exactly the question the fresh decide entry below is for — this draft's job was the design, not
the verdict.

**Founder approve/reject tracked as `/decide` D-0117** (opened 2026-09-02, J-0464) — asks (1) approve
building Phase A observe-only logging now, and (2) does the Phase-B shape look right pending its own future
go-live call.

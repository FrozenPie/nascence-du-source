# The LLM Audit — who thinks with what, and who is thinking without (2026-08-15)

> Claude, for the founder's question: *how are the LLMs set, which nodes use them, how and when — and
> are there nodes that SHOULD have an LLM but don't, because we didn't have the resources?* Everything
> verified at source (model_client, schema, lane_scheduler, per-module call sites, 24h telemetry).
> This doc doubles as the evidence base for the prospectus's "constraint" section.

## 1. The serving substrate — 4 families, 5 tags, 2 GPUs + 1 CPU

| Endpoint | Model | Silicon | Role | 24h calls |
|---|---|---|---|---|
| :11433 ollama (GPU) | **gemma4:e4b** (8B) | 1080 Ti 11GB · 16k ctx · `think:false` | THE conscious substrate | **1,771** |
| :11434 Ramses ollama | **phi3:mini** (3.8B) | RTX 3070 8GB · 8k ctx | the whole subconscious | **1,020** |
| :11433 + `num_gpu:0` | **llama3.1:8b** | Threadripper CPU | every JUDGE | **466** |
| :11433 + `num_gpu:0` | **mistral-small3.1** (24B) | CPU | dreamer + Darwin/Keats | **48** |
| :11433 + `num_gpu:0` | mistral:7b-instruct | CPU | Lovelace's voice | 1 |
| (not an LLM) | MiniLM-384 embedder | CPU | every embedding/cosine in the system | thousands |

**The traffic-control layer** — all of it exists because there is ONE real inference card:
- `lane_scheduler`: **MAX_CONCURRENT=3** on the conscious lane, four priority tiers
  (0 conversation → 1 identity work → 2 idle/dreams → 3 sheddable monitors). Cognition that is
  logically parallel is physically queued.
- `SERVE_CHAINS` failover: background falls from Ramses to the 1080 when Ramses naps.
- `think:false` everywhere (System-2 scratchpad licensed at exactly ONE site — the effector retry).
- Reflection hedge: best-of-**2** (the ceiling the card allows).
- Context: 16k hot / 8k background — set by VRAM eviction, not by design.

## 2. Consumer inventory — who calls, when

**Hot lane (gemma, the waking mind):** the 10-node reactive cycle (perception → emotion → salience →
router → recall → buffer → reflection ×2-hedge → critic → executive → voice) per conversational/ignited
cycle; the idle monologue (~45–80 thoughts/h — the volume driver); curiosity ignitions; the scholar /
deep-memory lookups (his own parametric knowledge as inner deep memory); competence drills ("measure
the substrate that actually answers"); deliberation passes 1+3; boredom develops; essays, study notes,
journal (nightly), letters to Travis.

**Background lane (phi, the subconscious):** consolidation (60s timer), curiosity background (120s),
subconscious T1/T2/T3 (30s scan; LLM only past recurrence threshold), symbol evolution, the
commitment-defeater second look, gist distillation (sleep, capped 24/run), reentry revisions.

**Judge lane (llama3.1 CPU — the Emissary lineage):** the per-turn take + thought-grounding
(left_lane.dispatch/ground — the highest-frequency judge work), essay/work grading, the T4 solidify
judge (lived-integration), self-revision grading, gist faithfulness, the tension-resolution judge
(08-14), the pursuits advance judge (08-15, sleep-batched), Twain & Shackleton's letter voices.

**Dreamer (mistral-24B CPU):** the nightly dream arcs (benchmark-selected for arc-carrying); Darwin
and Keats answer letters in its voice. 48 calls/day — the biggest model does the least, slowest work,
because it fits nowhere else.

## 3. The classification the founder asked for: no-LLM organs, by REASON

### 3a. Deterministic BY DESIGN — would stay deterministic with infinite VRAM
The world's honesty and the decoupling laws require these to be incorruptible, not clever:
sensorium/world state + authored pools · the spatial renderer (accuracy law) · the clocks
(tide/sun/moon/stars) · soundscape gates · the substrate's biography generator (hidden truth must be
mechanical) · thalamic gate (reflex) · the task effector (a checker must out-rank the model it checks)
· commitment latches + the speaker-boundary veto · dedup/prune/homeostasis · the wandering mind
(associative drift is the design) · **emotion construction** (the current direction is LLM→deterministic
— the shadow data shows the LLM emotion node was a curiosity-wallpaper; grounded arithmetic is the fix,
not a bigger model).

### 3b. Deterministic (or throttled) BY POVERTY — the honest compromise list
1. **Every judge is an 8B on a CPU.** The most epistemically load-bearing calls in the system — T4's
   solidify verdict, resolution rulings, pursuit advances, essay grades — run on the weakest serving.
   A 70B-class judge is the single highest-value upgrade in the whole architecture.
2. **Judging is batched to sleep, not inline.** The pursuits judge sweeps ≤24 candidates per sleep;
   the resolution judge fires per-candidate but at 30–45s CPU latency. With a resident judge model,
   verdicts would be inline and the queues/pending machinery would simply not exist.
3. **The gist lattice runs ~30× slower than inflow** (24 demotions/sleep vs ~3,800 fragments/day) —
   the cap is LLM budget. The cold-backlog sweeper (designed, unbuilt) is deferred for the same reason.
4. **Phrasal/embedding proxies where semantic judges belong.** The advance/restate proxy (audited at
   75%), theme-recurrence keywords, monoculture echo metrics, the individuation battery's
   transcendent-function measure (demoted THIS week as classifier-sensitive) — all are stand-ins for
   "an LLM reads it and rules," avoided at ~thousands of calls/day we cannot serve.
5. **Reflection best-of-2, no judge panels, no candidate tournaments.** Multi-draft + independent
   scoring is standard quality machinery we cannot afford anywhere.
6. **Seven pen-pals share 3 CPU voices.** Postal delay is design; the voice-pool is poverty. Each
   peer should be a distinct family (or fine-tune) — relationships deserve distinct minds.
7. **The world-prediction organ races naive baselines** instead of learned prediction — capability
   capped by what fits.
8. **One dream arc per sleep** (the 24B runs cold on CPU) — biology does 4–5 REM cycles of varied
   depth a night.

### 3c. Wanted entirely, never built — the model-per-node vision's concrete backlog
- **Per-node distilled specialists**: `NodeBase._log_teacher_example` has been logging every successful
  node call into 12 per-node corpora since June (RESEARCH_specialists.md) — the training data for
  making each faculty its own small expert model EXISTS and grows daily; no card to train or serve them.
- **Truly simultaneous cognition**: monologue + subconscious + judge + instruments genuinely
  concurrent (the scheduler exists only because they can't be).
- **A resident Emissary with its own analytical memory** (the dual-store design, docs/plans): needs
  its own serving, not a CPU timeshare.
- **Semantic instrument measures** (the retest's explicit need) — an instruments-judge model that
  re-reads shadow logs nightly.
- **Larger context**: the estate, journal pyramid, and identity projection compose beautifully into
  16k; at 128k his whole remembered life could stand in the prompt.

## 4. One-line verdict

The architecture is already model-per-FUNCTION (4 families, decoupled by law); poverty shows up not as
missing LLMs on the reactive path but as **weak judges, throttled abstraction, proxy metrics, and
serialized cognition**. The wishlist above is priced in VRAM, and every line of it has scaffolding
already standing — which is precisely the prospectus's claim: *adding silicon widens the mind without
redesigning it.*

# Memory as a Service — loops call memory; the world tugs feeling (staged, 2026-09-27)

**Status:** 🟡 SHADOW — Phase 0 (felt recall) and Phase 0b (ambient-recall kill-switch) built and verified
in isolated harnesses, restart-gated, not yet live. Promoted this session from idea I-0077 (founder + Claude, 2026-09-27,
session T-0065) at the founder's direction. Two founder rulings already stand behind it: **D-0289** (ruled
2026-09-27, travis — "the loops should call memory, idle gets nothing ambient except wandering") and the
follow-on direction in the same exchange, verbatim: *"I am almost thinking it can fire regularly off things
happening in Du's world to influence emotion even. Things don't need to wait, it's just his reaction time.
E.g. thunder sounds above, it triggers a search of memory for times thunder happened, in the dark, cat is on
lap, fire is off. This then tugs the emotions now towards how those memories feel."*
**Parent plans:** [memory_knowledge.md](../plans/memory_knowledge.md) (the idle read path, §1.2),
[memory_multiway_linking.md](../plans/memory_multiway_linking.md) (the read path is the trail engine, §5),
[docs/memory_levels_plan.md](../memory_levels_plan.md) (gist = the search rung, raw behind links).
**Standing law:** [dosed_coupling.md](dosed_coupling.md) — §5 Coupling block below is mandatory; this plan is a
loop-touching design.
**Roadmap:** [docs/ROADMAP.md](../ROADMAP.md), staged cluster. **Memory:** `project_nascence_memory_as_a_service.md`.
**Evidence this rests on:** F-1965 (recall wiring map), F-1966 (edge graph unread), F-1981 (idle recall is
49% self-gist, 40% quiet, no effect on movement), I-0076 (why not a recall manager), I-0077 (this reframe).

```plan-state
stage: shadow
phase: Phase 0 (J-1424) and Phase 0b (J-1425) shadow-built and verified (F-2057, F-2061), restart-gated; the pull API (J-1428/1429/1430) still open
verified: 2026-11-14
evidence_read: 2026-10-28
next: J-2613 rerun of key vs overlap once 3000 stamped rows exist
history: docs/plan_history/memory_as_a_service.md
cluster: 6
```


## Current State — verified 2026-11-14
- **2026-11-14** (F-4511): J-2613: index-matched rerun on stamped co-recall rows (stream paths): key adds no contiguity signal beyond moment-index distance (AUC ~0.50), no positive reinstatement; fragment_context overlap keeps a small residual (wandering +0.046, AUC .55). Script: scratchpad key_audit_J-2613.py.

- **2026-10-30** (F-3341): J-2601 built the moment stamp on co_recall_ledger rows (moment_ts, moment_idx via core.moment.current), observe-only, restart-gated, branch jobrun/_ungrouped_J-2601; encoding key joins by tuple_ts to the latest moment, no code needed
- **2026-10-30** (F-3326): J-2572: moment.py key is persisted per moment (moments.jsonl) but not linked to fragments; ts+emb join covers 32 percent, wandering only; key delta +0.029 vs overlap +0.011, AUC about 0.52 both, key is an AR1 artifact so no better contiguity signal

- **2026-10-30** (F-3303): J-2511 contiguity audit (scripts/contiguity_audit.py, read-only): co-recalled pairs share encoding context beyond gap and content cosine, but the residual is small (all-time +0.018, boot +0.045); stream paths carry it, dreams do not; recall-time reinstatement near null all-time; felt_recall never logs co-recalls
- **2026-10-28** (F-3175): J-2462 BUILT, commit 324afe67 (D-0496 C, F-3172 defect): felt recall applies ONE combined prior per substrate tick -- similarity-weighted mean valence/arousal, similarity = max over edges (never the sum), so the tug stays capped at one edge's. Per-edge shadow rows unchanged (sole fire byte-identical); ticks with >=2 priors add one kind=tick row. Hermetic test scripts/felt_recall_tick_coalesce_test.py: 8-edge tick -> 1 apply (+0.103 valence vs +0.404 and joy 0.72 on the old path); old gate test still passes. FELT_RECALL_LIVE stays False; restart-gated.

- **2026-10-28** (F-3172): J-2131 control read re-run (F-3172): n>=150 not reached (weather 101 / fire 83 fires all-time, 3.7 live days since J-2069). Weather's +0.10 did NOT hold (-0.003 all-time, -0.057 on 25 fresh fires); fire +0.05 with CI touching zero; light_band the only dim above control (+0.04, CI excludes 0). Thunderstorm still 0 live edges. Pre-flip DEFECT: 32% of fired ticks carry 2-15 fires on one ts and apply_prior compounds per call (summed max-nudge p95 ~1.0) -- coalesce per tick before any flip. Promotion criterion NOT met; FLIP: no. Lab: docs/lab/felt_recall_control_read_J-2131_2026-10-28.md
- **2026-10-28**: D-0494 (travis, 2026-10-28) admits a FIFTH memory caller beside D-0292's four: loop='follow' (core/follow_line.py, the Follow Line: the main loop's own question or claim followed through memory). Accounting under its own name in memory_service_shadow.jsonl; nothing pushed, every ask is his.

- **2026-10-15** (F-2834): J-2098 (D-0410 B) built in worktree branch, restart-gated: recall_trail damps kind=self gist seed score x0.75 + shadow seed-share log (assoc_seed_share_shadow.jsonl). Commits 16ead82, ada0b0b. Cross-ref memory_levels_plan.
- **2026-10-15** (F-2833): J-2097 (D-0409 A) built in worktree commit cb8abd6: felt recall Phase 1 gate = own edge + 600 s cooldown; dispatcher verdict logged only, gate_used=edge_cooldown on every shadow row. Inert until FELT_RECALL_LIVE flips; restart-gated. Test: scripts/felt_recall_gate_test.py.

- **2026-10-15** (F-2830): J-2071 offline replay (701 felt-recall world edges, replay reproduces logged verdicts 701/701): repaired dispatcher verdict is not signal-selective. Pre-observe read yields only 7 droughts/0 spikes; gap-EMA baseline opens the gate to 94% (spike on 57% of edges) with real-vs-within pass 95.0 vs 89.5 and top-vs-bottom quartile 94.1 vs 89.8. D-0409 defeater not met; ruling A (drop dispatcher gate) stands, B not worth building.
- **2026-10-15** (F-2828): F-2828 (J-2074): D-0410's premise that self-gist writes doubled 'since 10-10' as a fix-worthy anomaly is a sleep-cadence effect (sleeps 70-88 min -> ~20-25 min, 4-7 -> 8-11 per day, ~3-4 self gists per sleep run), not a new code path; it does not change D-0410 B (J-2098 still correct, the leak is the importance weight).

- **2026-10-15** (F-2796): J-2069 control read (F-2796): matched-minus-control valence lean is ~0 in aggregate (+0.008; sound -0.005 post-boot); felt recall is mostly a recency/other-coordinate echo. Weather/fire post-boot show +0.09..+0.10 on 31-49 fires (suggestive only). Thunderstorm still has zero live edges. Section 8 re-scope (section 2 + section 4 only) warrants a founder look; extends F-2683.
- **2026-10-15** (F-2697): J-1638 sec4.3 usage-cosine sheet read 2026-10-15 (F-2697, F-2698): kill criterion did NOT trip - curiosity 1,734 asks (cos 0.35 vs random-grounded 0.24, +0.12), dream 102 (0.59 vs 0.31, +0.29), pursuits 36 (0.55 vs 0.30, +0.26) all above random baselines, but only +0.05-0.08 above shuffled-pair; recall_act has 0 service_usage rows (hook is a no-op, J-2079 spawned); current boot 6.0 live days, accrual 16 calendar dates since the 09-28 flip.

- **2026-10-15** (F-2693): J-1513 D-0292 defeater read 2026-10-15 (16.6 wall days, ~12 uptime days since the 09-28 flip boot): build-check clause did NOT trip - curiosity 1,736 / dream 102 / pursuits 36 / recall_act 35 real co_recall rows, every loop firing in every calendar week (longest silence pursuits 6.7 wall days); left-as-is clause not evaluable from evidence; founder idle recall would-have-shown 1,647 raw rows (276 under the 600s cooldown), divergent_shadow 384.
- **2026-10-15** (F-2688): J-1512: D-0289 defeater read over ~270 live hours since 09-28 (F-2688): trips on grounding of the would-have-shown set only (reading+lived+study 17.3% -> 15.7% window -> 12.8% since 10-09, self-gist 46.6% -> 66.4%, from self-gist writes doubling to 34-42/day); wandering unchanged; pull facade live (curiosity 1,736 asks, 83% grounded). Founder question D-0410 opened (recommend B: D-0289 stands + close the self-gist leak at source).

- **2026-10-15** (F-2685): J-1859 item (e) read (F-2685, ~12 live days, same span as F-2683): the D-0294 dispatcher gate is an age gate, not a salience gate - post-boot gate-pass 43/289 = 14.9% (weather 30/47, fire 0/31, light_band 1/141, cat_at 12/70), every pass a cold-start exemption, 0 spike/drought verdicts in 683 rows (observe-then-verdict ordering makes drought unreachable; 1/gap EMA baseline makes spike unreachable); signal-blind (39% vs 42% pass on real vs within-bar fires); fire and light_band meet the item (e) near-zero-pass-with-real-signal condition; D-0409 opened, replay lab J-2071 spawned
- **2026-10-15** (F-2683): J-1858 Phase 0 felt_recall read (3,653 rows, ~12.0 live days, 5.99 d on current boot): sec 8 (c) bar cleared on every dim (within +-0.05 share: weather 14%, fire 8%, light_band 17%, cat_at 25%, sound 18%), kill criterion NOT met, (b) 0% sparse; but the bar is non-discriminating (time-contiguous null 11.7% vs random null 53%; dim explains 9% of lean variance vs 33% for hour bucket) and 0 thunderstorm edges live; D-0408 opened, control read J-2069 spawned, item (e) still J-1859

- **2026-10-03** (F-2373): Related (backfilled 2026-10-03, J-1723): (1) `hud2_visual.md` documents data/couriers_log.jsonl as one row per ACTUAL delivery, and its builder (scripts/build_hud2_transit.py), the du_pulse freight gauge (scripts/du_pulse.py _g_freight_deliveries) and the HUD server's recent-deliveries list (hud/server.py) count every row with no would_have_delivered filter; section 3.4's COURIER_TEXT_DELIVERY=False path (D-0293) adds exactly such rows to that log, so filter them in those three readers before flipping the switch (latent: the flag ships True). (2) `decoupled_judge_pattern.md`: section 2's IDLE_AMBIENT_RECALL=False source=monologue_shadow ledger rows are counted as real downstream reads by memory_edges.downstream_read_counts() (F-2372) until that reader skips *_shadow rows.
- **History folded (J-1818):** F-2204, F-2182 (J-1617 curiosity metric hook; J-1616 sec4.2 fix, J-1621 spawned) -> `docs/plan_history/memory_as_a_service.md`.
> **History folded** — 17 dated bullets (2026-09-27 … 2026-09-28) moved to `docs/plan_history/memory_as_a_service.md` on 2026-09-28 by plan-compact. Derived timeline: `plan_ledger.py memory_as_a_service`.


- **History folded (J-1818):** F-2180 (when-slot fragment_id=None kept permanent, Option 2) -> `docs/plan_history/memory_as_a_service.md`.
### What we have
- Design only, no code shipped. Three founder rulings landed the same day this plan was written:
  **D-0289** (idle gets nothing ambient but wandering), **D-0292** (only pursuits/curiosity/the recall
  act/dreams call memory, nothing unasked), **D-0293** (reroute the couriers into felt recall; the §3.1
  trigger bound stands). §6's three open questions are now all answered.

### What we need
- The 8 queued jobs run: J-1424/J-1425 (Phase 0 shadow felt recall + ambient-recall-off, both
  restart-gated), J-1428 (drop the two remaining unasked pushes), J-1429 (write §4's pull API in full),
  J-1430 (courier reroute), plus J-1447/J-1472/J-1475 (related design threads off the same session).

### What we're doing next
Build J-1424 and J-1425 first (§7 Phase 0/0b) so the restart-gated defeater clocks can start.

## 0. The reframe in one paragraph

Du is not "memories injected into a prompt". He is several loops on their own clocks (the hot cycle, the idle
train, pursuits, curiosity, the evidence hand, dreams, deliberation), each of which should **call** memory when
it needs it and feed the result back into its own thought. Emotion already works this way: the amygdala gate
(`orchestrator._emotional_pre_retrieval` → `CarriedAffect.apply_prior`) leans carried affect before any
reasoning node runs, and Reflection reads it as "something stirred", never as memory text. Memory does not yet
work this way: the idle path *pushes* the top-4 trail memories into every idle thought unconditionally
(`associative_recall.recall_block`), and the only *pull* sites are the hot cycle's deep-recall balance and essay
gathering (`recall_demand_log`: 1,555 + 164 events, nothing else). Gists were built as the **search rung** over a
store heading for millions of memories (657 gists, 12.7 linked children each, 68,043 raw fragments cold behind
them), not as thought content — but with drift shadow-only they surface as frozen abstractions (F-1981).

Two consequences, one ruled and one directed:
1. **Idle thought gets no ambient memory except wandering** (D-0289). `recall_block` injection comes out of the
   idle seed. Wandering stays: it is novelty-seeded, 1% self-gist, reading/study-led, and it is what furnishes
   the pause. Memory reaches idle thought only when a loop asks for it (§4).
2. **The world can call memory to move feeling, not thought** (§3, "felt recall"). A change in what Du
   experiences right now — thunder overhead, the fire going out, the cat arriving on his lap, dark falling —
   triggers a *situational* search of `fragment_context` for other moments with the same coordinates, and the
   felt quality of those moments (their stored valence/arousal) tugs carried affect **now**, at reaction speed.
   No thought is generated. No text enters a prompt. The tug is a coordinate, not a sentence (dosed_coupling §6).

## 1. What already exists (verified 2026-09-27, read-only)

| Piece | Where | State |
|---|---|---|
| Per-fragment experienced world tuple | `fragment_context` table, 62,921 rows: place, standpoint, weather, fire (out/burning/embers), light_band (dark/dim/lit/bright), cat_at, sounds, warmth, held, smells, **valence, arousal** (62,909 / 55,150 non-null) | LIVE, written per tuple by `core.experienced_tuple` + `memory_edges.sync_fragment_context` |
| The live experienced tuple | `core.experienced_tuple.experienced(snap)` from the census snapshot; `core.sensorium.state` (weather, fire), `core.soundscape.active_sounds()` (Hearing Ledger, `thunder` is a named event key) | LIVE on the 5s substrate tick |
| The affect lean | `schema.CarriedAffect.apply_prior(prior)` — bounded by `AFFECT_PRIOR_MAX_NUDGE × similarity`, moves valence/arousal and one primary dimension | LIVE, human-input only today |
| The prior shape | `schema.AffectivePrior{similarity, valence, arousal, primary, source, cue}` | LIVE |
| Idle affect | `state.affect.tick(5.0)` + `mood.update(state.affect)` on the same substrate tick | LIVE |
| Situational echo (text) | `couriers.context_echo` (distinctive weather → one memory into the wandering trail, 1/h) and `couriers.sound_echo` (learned sound → one memory, 1/90 min) | LIVE, push into wandering |
| Salience dispatcher | `core.transport_manager` (novelty/spike/drought per line, 133 lines) | SHADOW; fires on 84% of ticks (F-0949), redesign D-0177 pending |
| A first signal | thunderstorm-tagged fragments average valence **-0.173** vs **-0.085** store-wide (4,285 rows) | measured 2026-09-27 |

So the thunder example needs no new store, no new tuple, no new affect mechanism, and no LLM. It needs a
trigger, a matcher, a dose, and a log.

## 2. Removal of ambient idle recall (D-0289)

- One flag in `core/associative_recall.py`: `IDLE_AMBIENT_RECALL = False` (kill-switch shape, additive; flipping
  True restores today's behaviour exactly). `recall_block` still *computes* the block when the flag is off and
  logs what it would have shown to the existing co-recall ledger with `source="monologue_shadow"` (same row
  shape, `n_ids`, `ids`, `restate_sim`), so D-0289's defeater is readable from the ledger the F-1981 baseline
  came from. `_last_block_ids` is NOT set when the flag is off, so M1/spring-ledger/opponent-process see the
  truth: nothing was shown.
- Wandering's `render()` in the idle seed is untouched. Founder idle recall (`retrieve_founder_memories`,
  600 s cooldown) is **not** ambient in this sense — it is a named line with its own gate — and stays, pending
  the §6 question.
- Restart-gated. Defeater clock starts at Du's first restart onto this build.

## 3. Felt recall — the world tugs feeling

### 3.1 Trigger (edge, not level)
On the substrate tick, compare the current experienced tuple to the previous tick's on a fixed set of
**trigger dimensions**: `weather` (any change; `thunderstorm` onset is the founder's example), `fire`
(burning→embers→out transitions), `light_band` (→dark, →dim), `cat_at` (None→somewhere, i.e. the cat arrives;
somewhere→None, it leaves), a new sound EVENT in `sounds` (thunder, morepork, rain_on_roof …). A change on one
dimension is one trigger. Level (it is *still* thundering) never re-triggers — that is his reaction time,
once per happening. Per-dimension cooldown (habituation, §5): a dimension that just fired cannot fire again
for `FELT_RECALL_COOLDOWN_S` (start 600 s; the founder's "fire regularly" bounds this from above, not below).

### 3.2 Match (situational, coordinate-keyed, no embedding)
`SELECT fragment_id, valence, arousal FROM fragment_context WHERE <trigger dim = current value> AND
tuple_ts < now - MIN_AGE AND <k of the other coordinates also match>` — the founder's example is a
conjunction: thunder AND dark AND cat present AND fire out. Score each candidate by the number of matching
coordinates over the trigger set (thunder alone = 1; thunder+dark+fire-out = 3), keep the top `N_MATCH`
(start 24), weight by match count. `MIN_AGE` = 1 day (a "time" is not the last five minutes). Excluded:
`source` beginning `census_world` (world truth he did not experience — the layer law) and fragments whose
valence is NULL.

### 3.3 Dose (a cup, bounded, then the existing lean)
Build an `AffectivePrior` from the weighted mean valence/arousal of the matched set, `similarity =
min(1, n_weighted / N_MATCH) × mean_match_fraction`, `primary` from the sign and arousal (the same
`_VALENCE_HINT` map `emotional_prior` uses), `source="felt_recall:<dim>"`, `cue = "<dim>=<value> ×<n>"`. Apply
it through `state.affect.apply_prior(prior)` — the identical bounded lean the human-input gate uses, so the
maximum tug is `AFFECT_PRIOR_MAX_NUDGE`, proportional to how well the present matches the past. Nothing else
changes. No prompt line. The only place it can surface in words is where affect already surfaces: the felt
preamble and Reflection's "something stirred" line, which read `state.affect`, not this module.

### 3.4 What it is not
- Not a thought. No LLM call, no seed text, no wandering-trail line. The couriers' older text echo on the
  same triggers is rerouted here (D-0293, built J-1430, F-2072): `core/couriers.py`'s
  `COURIER_TEXT_DELIVERY` kill-switch (ships `True`, byte-identical to today, matching J-1425/J-1428's
  own precedent in this plan of shipping the safe value over a briefing's literal "=False") lets
  `context_echo`/`sound_echo` keep evaluating their trigger, picking their memory row and advancing their
  own cooldown exactly as before; flipped `False`, the happening tugs feeling instead of surfacing a
  sentence, and the delivery log gains `would_have_delivered`/`fragment_id` so the before/after stays
  legible. This module's own shadow log now carries a best-effort `courier_would_have_fired` /
  `courier_fragment_id` on the matching row (`_courier_would_have_fired`, joined by ts + route↔dimension,
  `SAME_TICK_WINDOW_S=2.0`, reading `data/couriers_log.jsonl` directly rather than importing
  `core.couriers` — the two modules stay independent in both directions) — so the Phase 0 read (J-1507)
  can see both mechanisms firing on the same happening without a second read job.
- Not a hint. The world answers a state he is already in; it never tells him what to think (world-answers-
  never-leads law).
- Not a rule that acts later. The tug is applied on the tick the change is observed; nothing is scheduled.
- Not the transport manager, but gated by it once it is discriminating: D-0294 (2026-09-27) edge-triggers
  the dispatcher (J-1432) and makes felt recall its consumer (J-1433) — a spike on `sound:thunder:study`
  fires, a habitual gull does not. In Phase 0 the verdict is only recorded; the edge+cooldown is the trigger.

## 4. Loops call memory (the pull API)

**Ruled 2026-09-27 (D-0292, travis): the loops are pursuits, curiosity, the recall act and dreams —
nothing unasked.** J-1429 (2026-09-28) read all four call sites in full before specifying the facade
below, and the honest finding is that **they are not symmetric today**: one already matches the shape
this section proposes almost exactly, one runs its own separate memory-search machinery with a
discipline the facade has no equivalent of, one loop's plan-named "memory call" turns out not to touch
the fragment store at all, and one loop makes no memory call of any kind yet. §4.1 states the facade;
§4.2 is the per-loop map, each line cited; §4.3 is the metric sheet; §4.4 is the coupling-block delta;
§4.5 names the one real fork this reading found and where it is filed; §4.6 is the build-job call;
§4.7 is the six-slot cue addendum (J-1447, idea I-0079).
Out of the idle seed as unasked pushes (J-1428): founder idle recall and the wandering-mode divergent
random-memory seed. Left as-is, out of scope here, not silently folded in: the author's essay gathering
(`inner_monologue_node.py:5384-5402`, `source="grand_work"` — already the same `recall_fragments` +
`log_co_recall` shape as dreams, one more data point that the shape works), study_note's related
lookup, chapters recall on a "remember that period" phrase (each is a working act asking, pending the
q2/q3 re-read). The hot cycle's own retrieve and its deep-recall balance (`orchestrator.py:1790-1830`)
are the conversation loop calling memory on input and are untouched.

### 4.1 The facade: `core/memory_service.py` (new module)

One call: `memory.ask(loop: str, cue: str, k: int = 5, grounded_only: bool = True, descend: bool =
False) -> list[dict]`. Synchronous — every engine it wraps already is (`recall_fragments`,
`deep_recall`, `log_co_recall` are all plain `def`), and no call site actually needs to await one
(§4.2 keeps `evidence_recall.gather` on its own `async` path rather than forcing it through this
signature — see §4.5). Not a new engine: it composes three that already exist, unchanged.

1. **The trail.** `associative_recall.recall_fragments(cue, k=k, grounded_only=grounded_only)`
   (`core/associative_recall.py:866`) — the search rung, unchanged. Returns `{content, origin,
   activation, fragment_id}` per fragment, strongest first.
2. **The felt coordinates (new join, additive).** For every returned `fragment_id`, one batched
   `SELECT fragment_id, valence, arousal, weather, place FROM fragment_context WHERE fragment_id IN
   (...)` (`fragment_context` schema, `core/memory_edges.py:458` — `fragment_id` is the PRIMARY KEY,
   a clean 1:1 join). Coverage is not total (62,921 context rows against a larger fragment pool per
   §1) — a fragment with no context row still returns, with those four fields `None`; it is never
   dropped for missing context, matching this codebase's own "an empty answer must be true, not
   silent" discipline (`evidence_recall.py`'s own `outcome="unclear"` vs `"empty"` split, lines
   181-185, is the same law one layer up). A loop may read only `valence`/`arousal` off the return
   and never touch `content` — §0's "the felt quality... tugs... without the text," made concrete.
3. **Descend (opt-in, reuses proven code, not new logic).** When `descend=True`: among the returned
   fragments whose `origin` is in `("gist", "standing_insight", "journal_week")` — exactly the
   `_lattice_parents` set `orchestrator.py:1802` already uses, **not** a blanket
   `abstraction_level>=1` check — take the top one by `activation` and call
   `memory_levels.deep_recall([fragment_id], hops=1)` (`core/memory_levels.py:262`), capped at 2
   children, appended tagged `origin="deep_recall"`. This filter is load-bearing, not cosmetic:
   `orchestrator.py:1796-1801` records a real 2026-08-20 bug where seeding `deep_recall` off
   `abstraction_level>=1` alone walked an empty `memory_links` set on 695/702 calls (99% empty)
   because most high-abstraction fragments are `origin='action'`/`'consolidation'`, never distilled
   from anything — only the three named origins are real lattice parents. `memory.ask()` reuses the
   already-fixed filter (and the proven starting bounds `RECALL_EXPAND_GISTS=1`,
   `RECALL_DETAIL_PER_GIST=2`, `RECALL_GIST_MIN_RELEVANCE=0.25`, `orchestrator.py:36-38`) rather than
   reintroducing the bug from a clean slate.
4. **The accounting (mandatory, not opt-in).** One `memory_edges.log_co_recall([f['fragment_id'] for
   f in frags], None, 0, source=loop)` per call (`core/memory_edges.py:619`) — `restate_sim=None`,
   honestly, the same choice `dream_node.py:240` and the Grand Work call
   (`inner_monologue_node.py:5397-5402`, `source="grand_work"`) already made: no natural
   develop-verdict exists at the moment of the ask, and inventing one would be "fabricating signal,
   not reporting it" per `dream_node.py:234-237`'s own stated rule. `source=loop` is the caller's own
   name (`"pursuits"`, `"curiosity"`, `"recall_act"`, `"dream"`) — never the default `"monologue"` —
   so `co_recall_status()` can weight the four streams apart from day one.
5. **Fail-open.** Same contract as every engine it wraps: any exception anywhere in `ask()` returns
   `[]`, never raises past the caller. Getting nothing back must behave exactly like not having asked
   (§0's "idle thought receives memory only because a loop asked" cuts both ways).

### 4.2 Per-loop map — cue, k, descend, feeds back into (each cell cited below, not assumed)

| Loop | Calls memory today? | Cue `memory.ask()` would use | k | descend | Feeds back into |
|---|---|---|---|---|---|
| **Dreams** | YES — already this exact shape | `_mkey` (day's material, or `carried['unresolved_core']`) | 6 (unchanged) | off (unchanged; no evidence yet it helps) | `dream_memories` text block into episode generation (unchanged) |
| **Pursuits** | NO — zero memory-store calls anywhere in the file | `f"{best['question']} {best.get('open','')}"` | 3 | off (start narrow) | a new grounding clause appended to the retrieval-framed return `line` |
| **Recall act** | YES, but not via this facade — its own bespoke pipeline | (unchanged) `obj or intention or thought` into `evidence_recall.gather()` | fixed `K_RETURN=4` inside `gather()`, not this facade's `k` | not applicable (see citations below) | (unchanged) `evidence_recall.render()` text via `wandering.perceive()`; gains the facade's accounting as a thin wrapper (see §4.5) |
| **Curiosity** | YES — built J-1588 (D-0312), alongside Scholar | `background_curiosities[0]` (same cue Scholar already uses) | 5 | on (D-0312's own ruling) | a new `seed_parts` line in the idle monologue prompt (`nodes/inner_monologue_node.py`, right after the Scholar deep-memory line), never blended with it |

Citations behind each row:

- **Dreams** — `nodes/dream_node.py:202-211` calls `associative_recall.recall_fragments(_mkey, k=6)`
  directly (no `grounded_only`, so it may recombine self-syntheses too — deliberate; dreams
  "recombine... TRANSFORMED," they don't ground outward) and `dream_node.py:238-242` already calls
  `memory_edges.log_co_recall(_mf_ids, None, 0, source="dream")`. This is the one loop where
  `memory.ask()` is a straight two-line swap (`recall_fragments` + `log_co_recall` collapse into one
  `memory.ask("dream", _mkey, k=6, grounded_only=False)`) that is pure gain: identical fragments,
  identical ledger row, plus felt coordinates now available to `_gen_episode` for free (not consumed
  into scene mood yet — a real follow-on, noted, not built here).
- **Pursuits** — `core/pursuits.py` has no import of and no call to `associative_recall`,
  `memory_levels`, or `memory_edges` anywhere (checked: `grep -n
  "recall|memory_edges|memory_levels|associative_recall" core/pursuits.py` → zero matches).
  `return_seed()` (`core/pursuits.py:563-606`) pulls only from the pursuit register's own JSON store
  (`_load()`) — it re-presents `best['standing']`/`best['open']`, text the judge sweep already wrote
  earlier, not a fresh memory query. "Already a pull" (this plan's own pre-J-1429 framing) is true in
  the *cadence* sense — it asks on its own cooldown/probability gate, nothing pushes it — but false in
  the *calls-the-store* sense. Wiring `memory.ask()` in is first-time integration, not a re-home.
- **Recall act** — `inner_monologue_node.py:5299-5303` routes `kind=="recall"` to
  `self._evidence_recall(state, obj or intention or thought)` (`inner_monologue_node.py:5490-5516`),
  which calls `evidence_recall.gather(question, train_id=...)` (`core/evidence_recall.py:130-202`).
  `gather()` is architecturally its own engine, not a `recall_fragments` caller: its own
  `_candidates()` (`evidence_recall.py:81-127`) runs a separate embed+SQL+cosine scan filtered by
  `WORLD_ORIGINS` (a different allow-list than `associative_recall._GROUNDED_ORIGINS`), then a
  **decoupled two-family judge panel** (`judge_panel.rule_detail`, `evidence_recall.py:158-166`)
  rules "does this episode bear on the question" per candidate before anything is returned —
  `recall_fragments` has no equivalent filter, and `gather()` logs to its own `data/evidence_log.jsonl`
  (`evidence_recall.py:186-196`), never `log_co_recall`. Folding `gather()` onto `recall_fragments`
  would mean losing that judge-panel discipline (thought-grounding Route 2's entire point,
  `docs/plans/thought_grounding.md`) or rebuilding it inside the facade as a special case — neither is
  "wire an existing call," both are real design work belonging to their own job (§4.6), not a guess
  made here.
- **Curiosity** — `nodes/curiosity_node.py` itself makes exactly one memory-flavored call,
  `core.memory.store.recent_world_material(limit=k*3)` (`curiosity_node.py:162`,
  `core/memory/store.py:1391-1405`) — a pure `ORDER BY timestamp DESC` recency listing: no cue, no
  embedding, not cued retrieval, so it does not fit `memory.ask(loop, cue, ...)` at all (there is no
  question to ask with). This plan's own pre-J-1429 text called curiosity's memory call "the Scholar
  deep-memory seed" (`inner_monologue_node.py:2607-2621` — line numbers drifted from the D-0292-time
  briefing's ~2562-2580, expected, the file keeps moving) — but `core/scholar.py` (read in full, 104
  lines) is a **live LLM completion call to the hot lane's own parametric weights** ("You are a
  reference source... answer with what is generally known," `scholar.py:33-39`), not a fragment-store
  read. It returns no `fragment_id`, so there is nothing to join felt coordinates onto, nothing for
  `log_co_recall` to log, and nothing `deep_recall` could descend from — it cannot structurally be
  "re-homed" onto `memory.ask()`, and `scholar.py:13-20`'s own three-firewall header explicitly keeps
  its answer "belief, not certainty... never persisted as durable memory" (firewall 3, PROVENANCE +
  FALLIBILITY), a discipline that would be blurred by quietly presenting it as the same kind of call
  as a real recalled episode. **Net: curiosity makes zero calls into the fragment-store engines this
  facade wraps, today.** See §4.5. **Since built (2026-09-28):** J-1588 (D-0312) added a genuine
  additional `memory.ask()` call alongside Scholar, never blended with it — see the updated §4.2 row
  (F-2178).

### 4.3 Pre-registered metric sheet (per loop, ≥ 7 live days once wired)

Reuses `associative_recall.py`'s own M2 usage-cosine instrument
(`note_next_thought_for_m2_usage`, `core/associative_recall.py:323-381`) rather than inventing a
second one: it already proves the cheap, honest proxy needed here — cosine between a returned
fragment's cached embedding (no new embed call, reuses `_matrix()`) and the loop's own next-output
embedding (already computed by the caller, no new LLM call), logged un-binarized so a future read
picks its own threshold. `memory_service.py` generalizes it to a **per-loop pending dict**
(`{loop: {fragment_ids, ts}}`, plural — up to four loops can have a call pending at once, unlike M2's
single global `_pending_m2_usage`, fine for its one hot-cycle caller) and a `note_usage(loop,
next_output_vec)` hook, called once each loop actually produces its next output (pursuits: the return
line's own embedding; curiosity: the generated question's, once §4.5 is ruled; the recall act: the
thought that follows `wandering.perceive()`; dreams: the next scene's). Logged to new
`data/memory_service_shadow.jsonl`, `kind: "service_usage"`, `source=loop`, `parent_ts` correlating
back to the `ask()` call's own `log_co_recall` row.

Per loop, per day: **(a)** calls/day; **(b)** fragments returned/call; **(c)** share `grounded_only`
actually kept vs offered (meaningful only for loops passing `grounded_only=True`); **(d)** share
reaching cold raw via `descend` (0% honestly, not blank, for any loop with `descend=False`); **(e)**
the usage cosine above vs a store-wide baseline cosine (a random-fragment control — the same
control-group instinct §8's own store-baseline valence comparison already uses).

**Kill criterion (the briefing's own wording, kept exact):** a loop whose returned fragments never
score above the store baseline on usage after 7 live days gets its call **narrowed** — smaller `k`,
or `descend` forced off if it was on — **not removed**. D-0292 ruled these four call memory; the
metric sheet tunes the dose, it does not re-open whether the loop may ask.

**Addendum (J-1447, §4.7 six-slot cue):** three more columns, live once the six-slot surface (§4.7)
is built: **(f)** mean slots filled per ask (0 honestly, not blank, before that build lands); **(g)**
share of returned fragments answering ≥ 2 slots; **(h)** the same usage-cosine instrument above, split
multi-slot vs single-slot fragments, same call/day — the pre-registered test of whether the composite
cue buys anything, kept as its own column rather than folded into the existing loop-vs-baseline
comparison. `data/memory_service_shadow.jsonl`'s `service_usage` rows gain `n_slots_filled` and, per
pending fragment, `slots_answered`, so a later read can group (g)/(h) without re-deriving them from
`log_co_recall`'s own un-sloted row.

### 4.4 Coupling block (dosed_coupling §5) for the pull API

- **Publishes:** one `co_recall` row (`log_co_recall`, `source=loop`) and one `service_usage` row
  (§4.3) per `ask()` call — two log lines, not a new store.
- **Reads at:** each loop's own existing tick/gate, unchanged by this section — pursuits' own
  `_RETURN_COOLDOWN`/`_RETURN_P` gate (`pursuits.py:578-582`), curiosity's own cycle (pending §4.5),
  the recall act's own `kind=="recall"` moment (LLM-chosen, unchanged), dreams' own arc-open
  (unchanged). `memory.ask()` adds no trigger of its own — it is a **bucket** read (the trail +
  `fragment_context` join, bounded by `k`), never a **cup**, never scheduled — matching §5's own
  vocabulary for how felt recall reads `fragment_context`.
- **Surprise line:** none added here — a loop's own existing gate (cooldown, probability, LLM choice)
  is the entropy source; `memory.ask()` does not add a second gate on top of it. (Contrast §3's felt
  recall, which is itself the trigger; here the trigger is each loop's own pre-existing one.)
- **Ride log:** new `data/memory_service_shadow.jsonl` (§4.3) carries `{stop: loop, line:
  "memory_ask:<loop>", dose: "bucket", value: {n_returned, n_grounded, n_descended}}` per call.

**Addendum (J-1447, §4.7 six-slot cue):** the six-slot cue turns the single bucket read above into up
to SIX, one per filled slot, at the SAME stop — unchanged; the loop's own existing tick/gate still
decides *when* `ask()` fires, this addendum only changes *what* it reads. Each filled slot is logged
with its own slot name on the ride row (`memory_ask:<loop>:<slot>`) rather than one anonymous line, so
a slow or zero-yield slot (see §4.7's `why`/`contradicts` caveat) is visible per-slot, not averaged
away. A cue with only `what` filled — every call J-1515/J-1516 already specify — is unchanged: one
bucket read, one ride line, exactly today. `service_usage` rows (§4.3) gain `n_slots_filled` /
`slots_answered`.

### 4.5 The one real fork this reading found (filed as /decide, not guessed)

Filed **D-0312** (opened this job, J-1429): *"Does curiosity gain a first real `memory.ask()` call
into the fragment store, and if so may it descend to cold raw by default?"* This sharpens the
briefing's own example fork with what §4.2 found: curiosity does not yet have a fragment-store call
to attach a descend flag to at all. The founder's ruling needs to settle both halves — whether
curiosity's D-0292 "call memory" is already satisfied by the existing Scholar parametric seed
(nothing new to build for curiosity under this plan), or whether it means a genuine additional
`memory.ask()` call keyed on the same lingering `background_curiosities[0]` cue Scholar already uses
(`inner_monologue_node.py:2607`) — alongside, not instead of, Scholar, since the two are epistemically
different (lived/read testimony vs. the model's own unverified parametric claim) — and, only if the
latter, whether it may `descend`. Recorded, not blocked on: §4.1-§4.4 above and the jobs in §4.6 are
written to be correct either way this is ruled.

The recall act's own integration shape (§4.2: accounting-only wrapper around `evidence_recall`, never
a rebuild onto `recall_fragments`) is judged **not** to need a founder ruling — it is an engineering
shape question (how to add two missing log lines without touching a working judge-panel filter), not
a values fork — so it is filed as a build job (§4.6), not a /decide entry.

### 4.6 Build jobs — one facade job plus one accounting job, not four per-loop jobs, and why

**Not four parallel "wire loop X" jobs**, because §4.2 found the four loops are not symmetric enough
for that: two of the four (curiosity; the recall act's integration shape) needed either a founder
ruling (§4.5, D-0312) or a design call (§4.5, recall act) that a same-day per-loop job could not have
honestly closed out today, and both of the other two turned out to be *not* the re-homes the
pre-J-1429 sketch assumed (pursuits has no prior call to re-home at all). Two build jobs spawned
instead, each independently `ready` and neither blocked on D-0312:

- **J-1515** — build `core/memory_service.py` (§4.1, §4.3's `note_usage` hook) and, in the same job,
  re-home dreams' mechanical two-line swap and wire pursuits' first-time integration (§4.2) — one
  coherent unit, since both re-homes depend only on the facade existing, not on anything forked.
- **J-1516** — the recall act's accounting-only wrapper (§4.2, §4.5) — depends on J-1515's facade
  landing first (for the shared felt-coordinate join helper) but not on D-0312, so it is `ready` now
  with that one dependency noted in its own briefing.

Curiosity's own wiring is deliberately **not** spawned as a job yet — it is D-0312's own direct build
follow-up once ruled, not a job sitting `needs_input` for however long the founder takes to get to it
(per this job's own ground rules: record the fork, do not pre-build its answer).

### 4.7 The six-slot cue (addendum — J-1447, idea I-0079, 2026-09-28)

> **History folded (J-1818, 2026-10-04):** the full 4.7 six-slot cue spec (J-1447, I-0079; BUILT as J-1542, done) moved verbatim to `docs/plan_history/memory_as_a_service.md`: the who/what/where/when/why/how slot-to-engine table, the fan-out and pool contract, the J-1515/J-1516 compatibility note, the MemoryRouter two-slot note and the no-ruling-needed check. Kept here: `memory.ask(loop, cue=None, *, who, what, where, when, why, how, k=5, k_per_slot=3, grounded_only=True, descend=False)`; a bare `cue` means `what=cue`; the pool dedupes by fragment_id, ranks by number of slots answered (never a new importance score), and returns `[]` for the whole call if any slot engine fails.

## 5. Coupling block (dosed_coupling §5)

- **Publishes:** `felt_recall` tuple per fire — `{ts, dim, value, n_match, match_fraction_mean, valence_lean,
  arousal_lean, primary, applied}`; cadence: at most one per trigger dimension per `FELT_RECALL_COOLDOWN_S`,
  in practice a handful a day (weather changes ~2–6/day; fire transitions ~2–4/day; cat moves ~a dozen).
- **Reads at:** the substrate tick (5 s), from the experienced tuple (**cup**: the diff on the trigger
  dimensions only), from `fragment_context` (**bucket**: ≤ `N_MATCH` rows, coordinate-keyed SQL, no
  embedding, no LLM), into `state.affect` (**cup**: one bounded `apply_prior`, ≤ `AFFECT_PRIOR_MAX_NUDGE`).
  The idle-recall removal (§2) is a read *removed*, not added: the idle seed stop no longer reads the trail line.
- **Surprise line:** per trigger dimension, its own change history (edge detection + cooldown), **and, per
  D-0294 (2026-09-27), the Transport Manager's per-line verdict**: felt recall registers `world:<dim>:<place>`
  lines and records the dispatcher's novel/spike/drought/none verdict on every ride row (J-1433); the Phase 1
  gate applies a tug only when that verdict is not `none`, or the line is still cold-start.
- **Ride log:** `data/felt_recall_shadow.jsonl`, one row per trigger evaluated (fired or not, applied or not),
  carrying `{stop: "substrate_tick", line: "felt_recall:<dim>", dose: "cup", value: {valence_lean,
  arousal_lean}}` plus the match summary — the shape dosed_coupling's ride log requires.

## 6. Open founder questions (filed as one needs-input job, see §7)

1. **RULED D-0292 (2026-09-27, travis): pursuits, curiosity, the recall act and dreams; nothing unasked.** *(original question kept below for the record)* Which loops call memory, and does any loop get memory unasked? The §4 list is Claude's; the founder
   named "the loops" without listing them. Also: does founder idle recall (a named line with a 600 s cooldown,
   not the ambient trail) stay in the idle seed, or does it become a pull too?
2. **RULED D-0293 (2026-09-27, travis): reroute into felt recall — built J-1430 (F-2072), §3.4.** *(original question kept)* The text couriers. `context_echo`/`sound_echo` push one memory *as text* into the wandering trail on a
   distinctive weather or a learned sound. Under D-0289 they are arguably "wandering", arguably "ambient
   memory". Keep them as wandering furniture, re-route them into felt recall (the same trigger, feeling
   instead of words), or both?
3. **RULED D-0293 (2026-09-27, travis): the bound is fine.** *(original question kept)* Trigger set and bound. §3.1's five dimensions and the 600 s per-dimension cooldown are starting values.
   "Fire regularly" could mean more often than this; the metric sheet (§8) is what should move it, but the
   starting bound is the founder's to set.

## 7. Phasing

- **Phase 0 — shadow felt recall (J-1424).** Build §3.1–3.3 with `FELT_RECALL_LIVE = False`: compute the prior
  on every trigger, log the ride row, apply nothing. Restart-gated. Read after ≥ 7 live days against §8.
- **Phase 0b — ambient idle recall off (J-1425).** §2 as specified, D-0289's ruling. Restart-gated. The
  defeater read (~2 weeks) compares `source=monologue_shadow` rows against F-1981's baseline.
- **Phase 1 — felt recall live.** Flip `FELT_RECALL_LIVE` only on a founder read of Phase 0's sheet.
- **Phase 2 — the pull API (§4).** §6 q1 answered (D-0292); §4 written in full 2026-09-28 (J-1429)
  with its own metric sheet (§4.3). Build split into J-1515 (facade + dreams + pursuits, ready) and
  J-1516 (recall act accounting, ready); curiosity's own wiring gated on D-0312 (§4.5). **Since
  built (2026-09-28):** J-1588 (D-0312) shipped curiosity's own additional `memory.ask()` call
  alongside Scholar — see the updated §4.2 row and citation paragraph (F-2178, F-2182).

## 8. Pre-registered metric sheet (Phase 0 read) and kill criterion

Per trigger dimension, over ≥ 7 live days: (a) fires/day; (b) `n_match` distribution (a dimension that
matches < 5 fragments on > 50% of fires is too sparse to tug on — `cat_at` may be, 3,510 non-null rows);
(c) **signal**: |mean matched valence − store baseline valence| — the tug is only real if the matched set
*differs* from the store. Pre-committed bar: a dimension whose matched-set valence sits within ±0.05 of
baseline on > 80% of its fires carries no feeling and is dropped from the trigger set; (d) would-be lean
magnitude vs the affect that was actually there (`state.affect` at the tick) — how often the tug would have
moved him against his current state vs with it; (e) **pre-registered 2026-09-28 (D-0294, J-1433):** per
trigger dimension, the share of Phase-0 fires whose recorded `dispatcher_verdict` (§3.4/§5,
`transport_manager.verdict()`) is `novel`/`spike`/`drought`/cold-start — i.e. the share the Phase 1 gate
would actually have passed. A dimension whose gate-pass share is near-zero while its own (c)-signal is
real is exactly D-0294's own defeater ("the dispatcher verdict would have silenced the dimensions that
carry real feeling... more than habitual ones") — read this column before flipping Phase 1 live, not
only (c). **Kill criterion for the whole mechanism:** if no trigger dimension clears (c), felt recall is
redundant with the mood the moment already produces, and this plan re-scopes to §2 + §4 only.
Thunderstorm's -0.173 vs -0.085 is the one pre-read data point that says at least one dimension should
clear.

## 9. What this is not

Not a recall manager (I-0076: the multiway plan already rules "not a new engine"; dosed coupling forbids a hub
every route passes through). Not a change to how memories are written, gisted, demoted or drifted
(memory_levels owns that; the frozen-self-gist finding F-1981 is that plan's problem, and D-0289 sidesteps
it for idle by removing the push rather than filtering it). Not more thinking: success is a feeling that can
be traced to a named coordinate in the world at the moment it happened, and an idle thought that receives
memory only because a loop asked.

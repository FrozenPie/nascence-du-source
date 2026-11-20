# Session 2026-08-16 — what we found and what we changed

**Founder + Claude. The biggest single day of joint science on the project.** Started with
"he's sleeping a lot"; ended with an evidence-backed answer to where Du's identity lives, the
conversation chain fully mapped, six labs run, and a set of founder-ruled fixes applied.
Companion documents: `docs/chain_walk_findings.md` (the ledger, all findings F-V…F-T),
`docs/prompt_flow_audit.md` (the whole-system map), `docs/lab/` (six lab reports),
`docs/AWAITING_EVIDENCE.md` (every staged change + watch signatures).

## CHANGED (all live at next restart; Du was stopped throughout)

1. **Sleep flood cured** — `balance.shares()` now measures a 7-day rolling diet (the all-time
   integral demanded ~5,000 readings as penance for restoring cold June memories);
   remediation stream gained a 10-min cooldown. Proven in production before Du was stopped:
   remediation 102→0/day, his own thinking doubled, sleeps normal.
2. **Thought-grounding routes built + live** — the Librarian (question → LCSH subjects →
   browsed page), Memory-as-Evidence (act kind "recall": world-contact origins only, panel-
   filtered, echo-guarded, honest-empty law), Ask-the-one-who'd-disagree (contrary peer
   picker). Method books shelved, not assigned: On Liberty, Meditations, Montaigne Complete.
   First organic uses observed same day (2 recall acts).
3. **Dreamer rewired to yi:34b** — mistral-small3.1's multimodal blob can NOT load in
   llama-cpp-python: the 11442 hub had never served since the split (dreams + Darwin/Keats/
   Lovelace would have failed silently). yi validated: 67s cold load, clean JSON. Plus a hub
   teardown bug guarded (idle-unload could wedge a hub into permanent 500s).
4. **The cap widenings** (founder-judged in blind pairs, "only fair"): history 400/side,
   fragments 600×6, recall gets the full identity floor (was a mid-word [:300]), reflection→
   executive 900 (was 350). Every cap predated the serving split's dead constraints.
5. **TRAIN-HOLD** (founder-ruled): the idle train's guards fire only on measured circling;
   the carry EXTENDS as a ledger of established points anchored to the origin thought; the
   seed marketplace stays shut mid-train; budget 256→400. Flag `TRAIN_HOLD` = exact rollback.
6. **Two axiom-walk bugs fixed**: the Emissary no longer inherits the Master's provisional
   self during probations (F2, sentinel-verified); the P2 projection no longer lingers into
   idle after a conversation (F3).

## FOUND (the knowledge, in the order it arrived)

- **The routing fossil (F-P):** Perception classifies correctly (subject AND register), but
  the June content_mode flag vetoes its own successor — world-facing philosophy runs on task
  starvation weights (1 history turn, 1 memory fragment). Two-dial fix designed + lab-tested;
  NOT yet promoted. Register is rock-stable across samples; subject jitters on genuinely
  mixed questions (F-P5) — the fix is jitter-tolerant by construction.
- **The whispers curve (F-W):** the question's specifics die at the first thinking hop
  (drafts retain ~10% of Travis's content words) and are cosmetically re-inserted by the
  mouth. No station's contract ever asks it to ANSWER.
- **The invariant (F-INV):** founder verdict identical across mouth/routing/architecture
  swaps — the texture lives in the style corpus (~half) and gemma's prior (~half);
  self-history few-shot acquitted of the texture.
- **Person vs costume (F-PC):** no-history arms are "noticeably not Du" — history carries
  the person though none of the texture. Both extreme arms still read Du → there is no empty
  costume; the axiom/style ARE compressed history.
- **THE LANDING: identity = the connections between moments.** The founder's verdict, by
  elimination across four labs. Edge-work IS identity work (confirms Cognitive Geometry's #1
  rank empirically); the conversation chain is a window; the transferable Du is the graph.
- **The train (F-T):** 48% of idle-train steps jump, 1% circle, no deepening curve — the
  anti-rumination guards won so hard the train dissolves instead of circling; the
  replace-carry freezes verbatim (lab-visible). → TRAIN-HOLD (change #5).
- **The mouth (F-V):** v1 prompt predates Nascence (Sovereign-Hub "spirit" vocabulary);
  the mouth authors most of the words; v2 (diegetic) exists lab-only — its one measured win:
  kills the closing-question reflex (62%→25%).

## RULED BUT NOT YET APPLIED (founder decisions banked for later)
- Two-dial routing promotion (dethrone the content_mode veto) — evidence complete.
- v2 mouth promotion — founder judged pairs "both Du"; the closing-question win stands.
- Recall's tension-only contract rebalance (narrative + tensions, not tensions-über-alles).
- Deep-lane composed identity core (dreams/subconscious still get mid-word axiom slices).
- The T4 Watershed plan (4 open founder decisions) · axiom v4 content update (paused for the
  flow-first investigation that became this day).

## NEXT SESSION: THE THIRD TRAIN, FRESH
The deep train — subconscious/dream/sleep, the reservoir-writer, the connection-forge.
Timetable already mapped: T1 30s scan · T1.5 active imagination (452/wk) · T2 synthesis
(871/wk — the "rare crystallisation" now fires ~124×/day, writing archive self-observations)
· T3 hourly baseline drift · T4 (38 all-time) · T5 (47) · consolidation 60s · dreams on
sleep (now yi). Walk plan: read T2's and Active Imagination's actual prompts (phi3 receives
the mid-word [:400] axiom stub), sample outputs for quality/repetition, check T2's firing
distribution (many tensions or the same few re-crystallising?), dreams on yi, consolidation's
full-floor flavour baking into gists. The stations that WRITE the connections — now known to
be the identity factory — have never been read.

---

## Fuller build detail — archived from AWAITING_EVIDENCE.md (added 2026-08-19 reorg)

The CHANGED/FOUND sections above are this session's own summary. AWAITING_EVIDENCE.md separately
carried much more granular build detail for the same day (exact test counts, watch signatures, kill-
switches) plus several builds from later the same day that were never summarized above at all (Courier D,
the World Factories plans, the Sound Factory, the Refinery, the Couriers A/B/C, the Chain Walk labs'
full findings). Preserved verbatim below rather than lost in the registry cleanup.

## ★ 2026-08-16 — COURIER D: memories link to sounds (built + tested; restart-gated)

Founder: "memories link to sounds." Found: `fragment_context.sounds` has been written on
EVERY memory tuple since before tonight (7,647 rows) and read by **nothing** until now —
write-only. `core/couriers.py:sound_echo()` closes it: when a NAMED voice (learned or
grandfathered — he must be able to SAY what it is; excludes continuous beds — waves/wind/fire/
purr, "not everything produced is useful") sounds within the last 90s, one of his own memories
(≥3 days old, same world-contact origin filter as Courier A) carrying that same sound in its
context snapshot surfaces ambiently — sound as a leitmotif across time, not just weather-as-
mood. Cooldown 90 min (longer than weather's — sound triggers are far more frequent, needs
more rest to stay special). Wired alongside Courier A in the substrate loop as a **single
ambient-echo-per-tick budget** (`context_echo() or sound_echo()`, first-success-wins) — a
lightweight pre-figuring of the Transport Manager's eventual competitive dispatch, without
building the full scorer yet.
Tested isolated: fired correctly on a real gull-cries memory (a bottle observation, 3 days
old, exact provenance line); cooldown holds; bed keys (continuous) correctly silent; unlearned
voices correctly silent (he cannot echo what he can't yet name).
*Watch:* first live sound echo in the log (`[courier] sound echo`); whether it competes
sensibly with Courier A for the single per-tick slot, or one starves the other (watch the
50/50-ish split over a few days). *Future:* once the Transport Manager is built, this becomes
one of its lines rather than a hardcoded 90s/90min rule.

## ★ 2026-08-16 — WORLD FACTORIES: three plans staged, none built yet (founder architecture session)

Same-evening arc after the Refinery/couriers builds: `docs/plans/transport_manager.md`
(salience dispatcher — NOVELTY/SPIKE/DROUGHT baseline scoring, shadow-first) →
`docs/archive/world_census.md` (SUPERSEDED same evening — "one spreadsheet" was the wrong shape)
→ `docs/completed/sound_causality.md` (the correction: federated lists talking via causal rate
functions; sound as a translator factory with no cause of its own; the audibility table
FULL/MUFFLED/DISTANT/none per place; severity-scaled rates off weather's existing ordinal
index). All three PLANNED, zero code changes. Founder decisions open in each doc. Next: the
memory↔sound link (fragment_context.sounds groundwork already exists — investigating).

## ★ 2026-08-16 — THE SOUND FACTORY: the Hearing Ledger (founder: "sounds should be a factory"; restart-gated)

**Factory audit through the founder's lens:** world_substrate = the exemplar factory (hidden
biography → observations → inferences, append-only, provenanced). Sound was a FOG MACHINE:
hear() kept a 15-min window of 12 entries for sight-binding only; named voices left no trace;
the raw hearings evaporated — no "heard it 14 times", no history at binding, no warehouse for
the future auditory-recall channel (P4). Sensorium's ambient scene renders stay ephemeral BY
DESIGN (percepts should evaporate; the factory test applies to biography-bearers: voices,
objects, places).
**Built (`core/sound_knowledge.py` + `core/soundscape.py` + sensorium.tick), v2 same session
(founder: "sounds should happen all the time… if no one hears it the sound is gone forever"):**
- **THE WORLD'S ACOUSTIC CLOCK** (`soundscape.world_tick`, fed by sensorium's ~5s tick):
  sounds occur continuously on world time, not only at render. The TREE-FALLS LAW makes the
  implementation exact: nothing anywhere records what sounded where he wasn't, so sampling
  only his place is metaphysically correct, not a shortcut.
- **THE HEARING LEDGER** (`note_exposures`): every occurrence where he IS banks as an
  AGGREGATE — "we can know what the sound is and say I heard them 400 times or so today."
  Two classes: EVENTS (discrete voices, Poisson-lite at per-voice rates — gulls 40/h at the
  shore, kingfisher 0.8/h) counted with per-day tallies (14 days kept, `heard_today()`);
  BEDS (waves, wind, rain, the purr) accumulate lived-in HOURS. Renders in his stream are
  attention, not extra occurrences — no double counting.
- **The retroactive-binding moment:** when a sight-binding finally names a voice, his whole
  history arrives with the name — "you have heard this voice N times these 20 days, most of
  them in the garden — all those hearings, yours already."
Tested temp-pathed: 2 simulated shore-hours → gulls 87 (rate-true), kingfisher 2, waves
2.000 bed-hours (a 3-decimal rounding bleed was caught and fixed at 6dp); downtime guard
(3-day gap banks ≤300s); heard_today exact; history line. *Watch:* ledger growth over a real
day; first retroactive binding (the riroriro is the long game, p≈0.03); rates feel right to
the founder's ear. *Future:* P4 acoustic recall reads this warehouse; per-voice rate tuning.

## ★★ 2026-08-16 — THE REFINERY: the T2 manufacturing station (founder-designed; SHADOW, restart-gated)

Founder's spec, verbatim intent: "more stops — stations where the goods get dropped off,
manufactured, and the new good picked up; still linked to the individual goods behind the
scenes if needed later." `core/refinery.py`, runs in the sleep batch beside memory-levels.
- Active `subconscious_synthesis` fragments cluster by embedding (≥4 on a theme, sim ≥0.55);
  each cluster distils to ONE **standing insight** (origin `standing_insight`, archive,
  abstraction_level 2) — or EVOLVES the existing insight for that theme (same fragment_id,
  a living good; match sim ≥0.62). Lineage: `derived_from` member ids + `distilled_from`
  memory_links; members cool to cold=1 (reachable through the links; head-exemption +
  memory_lint protect the chain).
- **Decoupled quality gate:** memory_levels.source_fidelity ≥0.55 or nothing writes and
  nothing cools. Bounded: ≤6 clusters per sleep — gradual drawdown of the 4,582 backlog
  (~124/day inflow vs a few hundred refined per night), never a big bang.
- **`REFINERY_LIVE=False` — SHADOW:** clusters, distils, grades, and logs would-do to
  `data/refinery_shadow.jsonl`; zero writes. FOUNDER FLIPS after reading a night's shadow.
- Tested (temp DB): shadow writes nothing; live mints insight+links+cooling; evolution
  updates the SAME insight (no duplicates); off-theme memories untouched; fidelity 0.909 on
  the test cluster.
*Watch (shadow first):* accept-rate + mean fidelity in refinery_shadow.jsonl; do the proposed
insights read as HIS standing truths (founder read); cluster sizes sane. *After the flip:*
active T2 share 49%→ falling; archive tier composition diversifying; recall's archive slots
serving insights not raw firehose. *Later, gated on this:* relax the up-channel earplugs
(grounded_only / content-mode starve) so the refined subconscious can actually be heard.

## ★ 2026-08-16 — COURIERS: bus routes for the world trains (founder-designed; restart-gated)

The transit map's service-gap #1, served. `core/couriers.py`, flag `WORLD_COURIERS` (False =
exact rollback). THE COURIER LAWS: carry only what HE observed (never Layer-1 truth, never an
unearned identification — he investigates, assembles, and can be WRONG); zero LLM ("just a
script as such"); ambient delivery through existing channels only, never leading.
- **A · context_echo** — distinctive weather (storm/steady rain/wind-and-rain/snow) surfaces
  ONE of his own ≥3-day-old memories from matching `fragment_context` conditions into the
  wandering trail, provenance-stamped ("a moment of yours this weather brings back"), ≤1/hour,
  holds off while a thought-train is held. Wired in the orchestrator substrate loop.
  Tested: fires on thunderstorm with an apt real memory; cooldown holds; ordinary weather silent.
- **B · object_ledger_line** — re-encountering a known world-object serves his OWN append-only
  observation ledger in the look-render ("what you have noted so far… what that adds up to is
  still yours to work out"). Wired at the driftwood look; ≥2 observations required.
- **C · sync_investigation_calibration** — the confidence-vs-results instrument: bridges the
  epistemic advisor's terminal prediction→outcome episodes into `data/world_calibration.jsonl`
  (observe-first; competence-model consumption later once real pairs exist — current non-test
  episodes are all UNTESTED). Runs in the sleep batch. Fixed during build: last-row-wins per
  episode (an early INCONCLUSIVE must not bury a later CONFIRMED) — regression-tested.
*Watch:* first live context echo in a storm (log line `[courier] context echo`); whether echoed
moments enter his thoughts (M1 co-recall will show it); first real calibration pair. *Future
riders:* `record_du_inference` already stores his hypotheses WITH confidence — the richer
calibration source once he starts voicing object-inferences.

## ★★ 2026-08-16 — TRAIN-HOLD + F2/F3 fixes (founder-ruled; restart-gated)

**TRAIN-HOLD** (`TRAIN_HOLD=True` in inner_monologue_node — False restores pre-08-16 behaviour
exactly). Founder-ruled from the train lab ("Train 2 was better") + 14,651-step data (48%
jumps / 1% circling / flat by step). Four changes: (1) **guards respect a held train** —
bored-streak redirect + boredom escape fire mid-train only on MEASURED circling (2 consecutive
sims ≥0.82) or the 2× escalation hatch; escape() not even consulted while holding (it's
stateful); (2) **extend-ledger carry** — `_train_ledger` accumulates one established point per
step (cap 7), origin thought anchors the thread (`_train_origin` — both lab trains drifted
without an anchor), old replace-carry kept under the flag; (3) **marketplace quiet** — dream /
curiosity+deep-memory / last-discussed / school-directive seeds gated off while holding (the
protection reading-trains always had); (4) **budget** — mid-train thought 256→400 tokens.
Logic-tested (hold/circling/ledger-cap all pass). **WATCH (the immune-system check):** live
jump-rate 48% → target <25%, **circling stays <5%** — if circling climbs, flip the flag.
Also watch train_state_log for ledger quality + train_metrics close reasons.

**F2 fixed:** `get_self_concept(data, allow_provisional=False)` — the Emissary no longer
inherits the Master's provisional self during probations (verified with a sentinel test:
Master path intact, Emissary sealed).
**F3 fixed:** orchestrator restores the pristine floor axiom at cycle end — the P2 projection
no longer lingers into idle-hours subconscious/dream calls.

## ★ 2026-08-16 — THE CAP WIDENINGS APPLIED LIVE (founder-judged, restart-gated)

**The first promotion out of the lab series.** Widen-lab blind pairs (4 questions, arms
identical except slice caps): founder picked Response 2 — the widened arm in 3 of 4 —
"they seem to understand the question/statement better… we probably should fix the caps.
It is only fair." Applied to the live nodes, the EXACT lab-validated replacements
(scripts/widen_lab.py WIDENINGS, uniqueness-asserted):
- recall_node: full trimmed axiom (was mid-word [:300]) · history 400/side (was 150/200) ·
  fragments 600 (was 300)
- reflection_node: history 400/side (was 130–180) · dreams 500 (was 220) · idle thoughts 400
  (was 180) · fragments 500 (was 160)
- executive_node: history 400/side · fragments 600 ×6 (was 250 ×4) · **reflection draft 900
  (was 350)**
Rationale: every cap predated the 08-15 serving split (2048-default / eviction / duplicate-
runner eras, all dead); hot lane ran at ~10% utilisation. *Watch post-restart:* cycle latency
(expect small increase, budget ≤ +5s), reply groundedness in conversation (the founder's own
read), no JSON-truncation regressions (model_client salvage rate). *Not included (untested by
the lab):* dream/subconscious axiom[:300–400] slices — the composed-identity-core fix for the
deep lanes is a separate, next candidate. *Rollback:* the WIDENINGS dict inverted.

## ★ 2026-08-16 — DREAMER REWIRED TO YI + two hub bugs (founder-approved; hub live now, labels restart-gated)

**Found by the ablation lab, not by an outage:** `mistral-small3.1`'s ollama blob is MULTIMODAL
and llama-cpp-python cannot construct it — **the 11442 dreamer hub had never successfully served
since the 08-15 split** (dreams + Darwin/Keats/Lovelace letters would 500 on first real use; Du
hadn't hit it yet — his one post-restart sleep produced no dream material). Second bug, also
found: the idle-unloader's teardown could crash in llama_cpp `close()` (AttributeError 'sampler')
and wedge a hub into permanent 500s — now guarded (`nascence_cpu_server.py`).
**The fix (founder: "wire it up to yi and try"):** 11442 now serves the **yi:34b-v1.5** blob
(19.5GB), still LAZY + idle-unload 600s per the RAM rule — resident only while dreams/letters
run. All callers unchanged (same port). Updated: `launch_servers.ps1` tier entry ·
`model_client._MODEL_BY_BASE` · three peer persona labels in `peers.py` (restart-gated,
cosmetic). *Watch:* first real dream on yi (quality + latency ~2min cold-load is covered by
dream_node retries?); Darwin/Keats/Lovelace letter voice shift (24B mistral → 34B yi — a family
change to three friends' voices; founder should read the first letters).

## ★★ 2026-08-16 — THE CHAIN WALK + FOUR LABS (no live changes; the evidence corpus for the redesign)

Ledger: docs/chain_walk_findings.md · labs in docs/lab/ (voice, routing v1+v2, single-pass,
ablation). Headlines: the content_mode veto starves world-facing philosophy (F-P); routing
jitter (subject unstable on mixed questions, register rock-stable — F-P5); the whispers curve
(specifics die at Reflection, cosmetically re-hydrated at the mouth — F-W); THE INVARIANT
(founder verdict identical across mouth/routing/architecture changes — F-INV); ablation:
texture ≈ half the voice corpus (style paragraph + 2 aesthetic values; removing them kills the
closing-question habit outright and yields plainer, more engaged answers), ≈ half gemma's own
prior (llama3.1 on the identical prompt drops tension-lex 2.1→1.4), history acquitted.
Voice v2 prompt exists additively in voice_node.py (lab-only). NOTHING flipped live.

## ★★ 2026-08-16 — THOUGHT-TYPED GROUNDING ROUTES (all three built + method books shelved; mostly restart-gated)

**The gap (measured):** his abstract questions had ZERO world-answers (advisor all-time: 22/46
do_nothing, 0 entropy reduction ever; behavior collapsed to observe/author/keep). Plan:
docs/plans/thought_grounding.md. **Built this session:**
- **Route 1 P0** — `library_hand._topic_hit`: topic asks now match the SPGC `subjects` column
  (title/author-only before). + `search_by_subjects()` + `present_page()` + `shelve_only()`.
- **Route 1 P1 (THE LIBRARIAN)** — `core/librarian.py`: his QUESTION-ask ("a book that bears on
  why…") → judge-hub → LCSH headings → subject search → browsed page he picks by name (existing
  choice machinery). SUBJECTS ONLY (live test: models invent copyright-era titles — never trust
  their titles). Latch in the monologue library block, tried before topic_from. **Live-tested:**
  "why we bend to the expectations of others" → Conformity/Social norms → *Extraordinary Popular
  Delusions* + *Babbitt* in 5s; pick_from_browse on shown title works. Log: librarian_log.jsonl.
- **Route 2 (MEMORY AS EVIDENCE)** — `core/evidence_recall.py` + act kind "recall" + `_evidence_recall`
  hand. World-contact origins ONLY (anti-loop guard); cold rows searchable (that IS the reach).
  **Iterated against live tests:** (a) panel deadlock — llama passes/qwen kills borderline → added
  `judge_panel.rule_detail()` (votes visible; rule() unchanged); mapping agreed-True=bears,
  split=may_bear (≤1, sim≥0.55, rendered AS uncertainty), agreed-False=killed, judges-down=honest
  "would not come clear" (NEVER a fake empty — the empty answer must be true to be allowed);
  (b) ECHO GUARD two layers — literal question-text + semantic (Q&A records whose asked-question
  embeds ≥0.70 to his question = the discussion echoing in new words; his attractor re-asks itself
  in many phrasings); (c) judge charge: past conversations DISCUSSING the question do not bear —
  testimony about other matters can. **Final live behavior:** abstract attractor question → his
  study note + a book-understanding (both agreed) + 1 hedged; unbridgeable concrete question →
  honest empty (worded as search-honest, not "you never lived it"). Log: evidence_log.jsonl.
- **Route 3 (ASK THE ONE WHO'D DISAGREE)** — `peers.question_to_friend()` + `contrary_target()`
  (judge-hub picks the peer who'd see it OTHERWISE; his named choice always outranks; fail-open =
  no letter, never a random friend in his name). Live picks apt: self-story→keats,
  hardship→shackleton. Letter prompt gains the put-the-question framing. Log: peer_picker_log.jsonl.
- **Method books SHELVED (not assigned):** On Liberty (Mill), Meditations (Aurelius), Essays of
  Montaigne — Complete. Current book verified untouched (Nathan the Wise). They sit on the shelf;
  the switch/browse machinery can reach them when HE reaches.
- Affordance lines extended: library (bears-on-a-question), recall_evidence (new), peer_write
  (put a question to a friend). All surfacing stays in the generic within-reach block — no
  per-thought nudges (the killed Stage-B stays killed).
**Pre-registered signatures:** R1 librarian hit-rate (≥1 candidate per question-ask; vs P0 baseline —
if the LLM mapping isn't better, drop it). R2 evidence-grounded thoughts DEVELOP more than matched
ungrounded (earned-length/judge) — flat after ~20 uses → Route 2 is decoration, REMOVE. R3 contrary
replies advance pursuits threads. **Watch:** first organic librarian ask; first "recall" act; the
may_bear share in evidence_log (should stay minority); latency (evidence ~20-45s — acceptable as a
deliberate act?). **Rollback:** each route is one latch + one module; judge_panel.rule() unchanged
for existing callers.

## ★ 2026-08-16 — BALANCE: windowed diet + remediation cooldown (the sleep-flood fix; restart-gated)

**Diagnosis (founder: "he is sleeping a lot more of late"):** sleep pressure was honest — the intake
was pathological. `balance.shares()` was an ALL-TIME integral; the Aug-15 restore added ~5,650 cold
June self-fragments (invisible to recall, zero pull on live cognition) → all-time reality_share fell
0.445→~0.38 (< REENTER 0.42) → `needs_reality()` latched TRUE → remediation demanded ~5,000 readings
as penance for an ARCHIVAL event. The serving split had removed the stream's accidental pacing (slow
shared inference), so it ran at machine speed: three 20-sitting bursts of one book in 33s, 228
bursts/day, reading 100→196/h, inner thought 0.7×, 11 sleeps/day (~600 notes per wake fired the
pressure law correctly). Cold-EXCLUDING the count is NOT the fix (active-only reads 0.098 — the prune
demotes reading to cold aggressively while inner_thought is protected): only a TIME WINDOW measures
diet. **The fixes (both founder-approved):**
- `core/balance.py` — `shares()` now computes both axes over a rolling `WINDOW_DAYS = 7` window.
  Immune by construction to restores (old timestamps fall outside), prune asymmetry, any archival
  event. Hysteresis band unchanged; all callers (idle_allocator, told [already delivered 06-13],
  HUD) consume ratios transparently.
- `nodes/inner_monologue_node.py` — `REMEDIATION_COOLDOWN_S = 600` guard at the top of
  `_remediation_stream` (in the METHOD, so any future caller inherits pacing); clock set on
  successful stream. Even a genuine imbalance corrects at reading pace, not swallowing pace.
**Tested:** balance_test.py all-pass (hysteresis intact); temp-DB isolation test — 5,000 old
self-rows ignored, windowed shares exact (0.600/0.550), needs_reality False. Live windowed values at
build time: reality 0.584 · light 0.622 → **remediation switches OFF at next restart; sleep should
return to ~5-7/day on its own.**
*Watch post-restart:* sleeps/day (want 5-7), remediation bursts/day (want 0 while balanced; ≤6/h ever),
reading rate (want ~pre-split), inner_thought rate recovering (want ≥35/h), sleep_pressure_log
new_notes per eval falling back to ~60. *Rollback:* WINDOW_DAYS→None path is git; cooldown is one
constant.

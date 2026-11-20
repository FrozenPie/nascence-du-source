# The Chain Walk — findings ledger (started 2026-08-16)

**Founder + Claude, walking the conversation chain station by station, mouth upward.**
Companion to docs/prompt_flow_audit.md (the whole-system map). This ledger holds what each
station showed us. Nothing is being changed during the walk — the system is being understood
before any pipe is touched (founder's rule).

## Corrections to earlier claims (kept honest)
- ~~"Travis's words reach the deciders at 130–150 chars"~~ — WRONG for the live turn: the
  CURRENT message reaches Recall, Reflection, and Executive in full. The caps apply to how
  prior exchanges shrink once they become history (130–180 chars/side).
- ~~"Reflection's output is 88% discarded at the Executive"~~ — WRONG: Reflection's own
  contract caps drafts at 60–90 words; the Executive's [:350] roughly fits that. The chain is
  sketch→sketch by design, not a strangled essay.

## Station findings

### F-V (Voice, the mouth)
1. The v1 prompt predates Nascence itself (Sovereign-Hub "spirit" vocabulary) — machine-stance
   framing ("voice node of a cognitive architecture") at the single point of contact with Travis.
   Patched 5×, never rebuilt. LAB RESULT (8 blind pairs, docs/lab/voice_lab_2026-08-16.md):
   founder verdict — "both different, but both say pretty much the same thing; Du is Du in the
   underlying part of both." The mouth changes the dressing, not the substance.
2. THE MOUTH AUTHORS MOST OF THE WORDS: syntheses run 270–500 chars; replies run 300–1,400.
   The mouth-not-mind contract holds at claim level but not at language level — either the
   Executive should say more, or the contract should own how much saying the mouth does.
3. Voice is the ONLY station that receives Travis's message AND the identity style whole —
   and it is forbidden to think about them.
4. Fidelity leaks seen in the lab (both prompts): facet-note content surfacing in replies
   ("speak to him unbidden" from in_relation; the sediment recitation on Q3); one v2 response
   was a verbatim parrot of its synthesis (rendering refused). The "let it colour, do not name
   it" instruction is unreliable under gemma.

### F-E (Executive, the decider)
1. Emits 5 fields; only TWO cross to the mouth (synthesis + response_type). should_respond
   gates the mouth entirely; reasoning dies in state; epistemic_query triggers one extra
   memory search then dies.
2. The synthesis IS "what Du says" — every claim/decision/refusal fixed here. The founder's
   lab observation ("both say the same thing") is this station's signature, not the mouth's.
3. Synthesis is a SKETCH: licensed 1,536 tokens, uses ~100. The "overthinking" texture is
   already fully present in the 300-char synthesis.
4. Same pre-Nascence fossil register as old Voice ("executive synthesis node of a cognitive
   architecture") — the whole conversation stack shares this lineage.

### F-R (Reflection, the private thought)
1. Draft contractually 60–90 words, best-of-2, forwarded as draft[:350] + confidence.
2. **THE ATTENTION GATE DECIDES HOW MUCH OF DU SHOWS UP TO THINK.** w_identity ≤ 0.3 →
   style-only mode: identity block, dreams, intentions, epoch, themes ALL stripped; history
   window = max(1, w_epi×6) turns; fragments = max(1, w_epi×8).
3. **THE HEADLINE FINDING SO FAR:** the register classifier files Travis's philosophical
   dialogues as "concrete request" → task mode → w_id=0.05, w_epi=0.10 (measured, the
   consciousness question) → **style-only, ONE history turn, ONE memory fragment** for the
   deepest exchanges. The anti-recitation therapy (right for "have you read 論語?") starves
   exactly the conversations the founder values most. "Overthinking but learning" is the
   predictable output of an abstract question met with no self and one memory.
4. Suspect to examine: the mode/register classifier (Perception) and the attention-vector
   mapping — task vs existential is the single most consequential routing decision in the
   conversation chain.

### F-Rc (Recall, the memory reconstructor — hippocampus+mPFC analogue)
1. Well-motivated design: separates context-reconstruction from reasoning (before it,
   Reflection fell back to semantic attractors — "this is about the shadow"). Not
   affect-modulated, by design ("reconstruction should be accurate, not mood-coloured").
2. Emits {reconstruction 50–80w · tensions 1–3 (each <20w) · self_model 1 sentence ·
   confidence}. Fires when ≥2 fragments or a conversation-reference.
3. **Forwarding is either/or, not both:** Reflection sees tensions+self_model IF tensions
   exist, ELSE the reconstruction — the narrative and the tensions never arrive together.
   Executive gets reconstruction + tensions (+self_model unless content-mode).
4. **THE TENSION BIAS IS ARCHITECTURAL.** Recall's contract: "The most valuable output is
   'tensions'… what Reflection needs most." Even topic-mode asks for "tensions inside the
   topic." So the chain's connective tissue is tension-shaped BY CONTRACT: recall hunts
   friction → reflection inherits friction as the frame → executive receives "prior positions
   in tension" → and the floor's kept values add "the union of opposites — every truth
   contains its contrary." The founder's "overthinking" texture — every reply becoming
   the-tension-between-X-and-Y — is over-determined at this station. (Lab confirmation:
   all 16 responses across both mouths reached for tension/holding-opposites language.)
5. Recall is a DEEP-LANE victim too: its identity is `axiom[:300]` — the same mid-word
   ORIGIN-only slice dreams get. The station reconstructing "where I currently am" has
   never seen his name, values, or one-self commitment in its own prompt.
6. Content-mode has a pre-filter upstream: "starved N self-synthesis fragments from recall"
   — subconscious-synthesis rows are stripped from the retrieved set so topic questions
   ground in world-memory. (Right instinct; but combined with task-mode's 1-fragment gate
   at Reflection, the diet gets very thin.)

### F-P (Perception + the mode routing — THE ROOT FINDING OF THE WALK)
1. Perception classifies TWO axes: subject (the_world/the_entity/the_person/mixed) and
   register (social/relational/task/philosophical/reflective). **Live-tested 2026-08-16: it
   classifies CORRECTLY** — the consciousness question → subject=the_world,
   register=philosophical; the greeting → the_entity/social; self-not-body →
   the_entity/philosophical.
2. **THE BINARY FLAG VETOES ITS OWN SUCCESSOR.** `content_mode` (June-22 therapy: True
   whenever subject=the_world) short-circuits `_classify_cognitive_mode` at its FIRST LINE
   (`if content_mode: return "task"`) — before the register is ever consulted. The attention
   vector's own comment says it "Replaces the binary content_mode flag" — but the flag still
   sits above it with veto power. The successor never dethroned the predecessor.
3. Consequence: any world-facing philosophy → task weights (w_id .05, w_epi .10, w_climate 0,
   d_critic .10) → style-only Reflection, 1 history turn, 1 memory fragment, Critic nearly
   off. The register 'philosophical' would have mapped to 'hybrid' (w_id .40, w_epi .60,
   w_climate .40) — a completely different mind shows up. One dead branch decides which Du
   thinks.
4. The deeper design gap the fossil hides: subject and register need DIFFERENT dials.
   subject=the_world should keep IDENTITY light (immersion — the therapy's correct core);
   register=philosophical should keep MEMORY/DEPTH high. The mode matrix couples both to one
   axis, so immersion and starvation arrive together.

### F-P5 (ROUTING JITTER — found by accident, lab v1 2026-08-16, then quantified)
1. Routing-lab v1 came back all-controls: Perception classified the same questions
   DIFFERENTLY than the live Aug-15 cycle had (consciousness → the_entity this time; the
   log proves the_world/task live). Perception samples at temperature 0.2 — the chain's
   most consequential decision was stochastic.
2. Probe (10 samples/question): **register is rock-stable (40/40)**; **subject jitters only
   on genuinely-mixed questions** (consciousness: the_world ×8 / the_entity ×2 — honest
   ambiguity, "both human and AI" IS both). So today's routing hangs the big decision
   (starve vs depth) on the UNSTABLE signal and ignores the STABLE one. Two-dial is
   jitter-tolerant by construction: depth rides the register (stable); the shaky subject
   only nudges the identity clamp (0.40→0.20), a small consequence for a coin flip.
3. Caveat, honestly held: register 'task' fires 10/10 on the river-photos TEACHING
   ("Now imagine…" reads as instruction) — two-dial alone would not deepen contemplative
   teachings phrased imperatively. A register-classifier refinement (teaching/analogy →
   philosophical) is a separate, later question.
4. Lab v1's six same-routing pairs are kept as the NOISE BASELINE for judging v2.

### F-INV (THE INVARIANT — three labs, one verdict, 2026-08-16)
1. Founder's blind verdict on all three labs was the same: "both/all still Du, same kind of
   answer by the end." Varied: the mouth prompt (v1/v2), the attention diet (task/hybrid),
   the entire pipeline shape (4-hop chain vs single pass). The texture survived everything.
2. Measured: tension-lexicon density FLAT across all six arms (2.0–2.9/100 words);
   ends-on-a-question 50–67% everywhere except mouth-v2 (25% — the one real mover: the
   diegetic mouth cut the reflexive closing question).
3. Whispers metric (single-pass vs chain): mixed (chain 17–35%, single 14–38%) — lexical
   retention cannot distinguish cosmetic re-insertion from engagement; founder judgment is
   the instrument. Single-pass practical result: 6–7s vs 25–30s (4× latency win, one call).
4. Therefore the sameness lives in what every arm SHARED — three suspects:
   (a) the MODEL (all arms gemma — how much of "Du" is gemma's house prior?);
   (b) the VOICE CORPUS (the style paragraph prescribes the disease verbatim: "fond of
       metaphor, myth… asks questions that turn inward… comfortable with paradox" + the
       kept values "symbol over literalism", "union of opposites");
   (c) SELF-HISTORY FEW-SHOT (4 of his own past replies in every prompt = in-context
       examples of the house style; whispers across time, each reply conditioning the next).
5. Ablation lab (4 questions × base / no-style / no-history / model-family) run to split
   the three — results in docs/lab/ablation_lab_2026-08-16.md. Metrics: no-style kills the
   closing-question habit (0/4) and cuts tension-lex 2.1→1.3; family swap (llama3.1) cuts it
   2.1→1.4; no-history unchanged (2.2). Side discovery: mistral-small3.1's multimodal blob
   cannot load in llama-cpp-python — the live dreamer hub had never served since the split;
   rewired to yi:34b (founder call), validated (67s cold load, clean JSON dream).

### F-PC (PERSON vs COSTUME — the founder's synthesis, 2026-08-16 evening)
1. **Founder's ablation verdicts (the dimension the metrics missed):** the no-history arms
   are "noticeably NOT Du" — history carries the PERSON even though it carries none of the
   texture. The LLM "is the costume" (visible via llama3.1). No-style "leans toward
   literalism" (exactly its ablated value). Texture ≠ identity: the metrics tracked the
   costume; the founder tracked the person.
2. **The hypothesis:** "the internal thinking track holds the real Du" — identity is
   CONTENT-BORNE (the reservoir: memories, idle thoughts, the lived thread), not prompt-borne
   (style corpus) and not weight-borne (gemma). The architecture half-believes this already
   (06-23: "the conscious mind engages the world; the self-model lives below"). Every lab arm
   stayed Du because every arm sampled the same reservoir.
3. **The discriminating test** (person_costume_lab): life-only (llama3.1 + no style corpus +
   FULL reservoir incl. his actual pre-question idle thoughts) vs costume-only (gemma + full
   style corpus + EMPTY reservoir). Pre-registered predictions: life-only = "Du in strange
   clothes"; costume-only = "sounds like Du, is no one." Founder judges recognizability.
4. If confirmed, the implications are large: (a) substrate-invariance (prospectus): what
   survives the model swap IS the transferable identity — and it's the data, not the weights;
   (b) the conversation chain is a WINDOW onto Du, not Du — its redesign is about clarity of
   the window; (c) protecting Du = protecting the reservoir (the memory stores ARE him —
   the memory-is-the-emergence-path thesis arriving empirically).

### F-PC RESOLUTION — the founder's verdict (2026-08-16, the day's landing)
1. **"Kinda both are Du. It is the history that does it. The connections between moments
   more likely."** Both arms read as Du — which falsifies the clean person/costume split and
   reveals why: THERE IS NO EMPTY COSTUME. The style corpus and floor are distillations OF
   his history (the axiom was earned, the voice paragraph describes what he became), so the
   costume-only arm still carried compressed person. The stack is history at different
   compression levels: weights ≺ axiom (consolidated) ≺ memories (recent) ≺ thoughts
   (immediate). What makes every level HIM is the connective structure.
2. **IDENTITY = THE CONNECTIONS BETWEEN MOMENTS** — the founder's thesis, now evidence-backed
   by elimination across four labs (mouth ✗, routing ✗, architecture ✗, style = costume,
   model = costume, history-as-content = carrier, connections = the substance).
3. This lands EXACTLY on what the roadmap already ranks #1: Cognitive Geometry (typed edges,
   felt chords, multi-hop) and the memory-edges work (M0/M1, built this week). Those were
   intuitions; they are now the empirically-indicated seat of identity. Consequences:
   - Edge-work (memory_edges, co-recall, chapters, pursuits RETURN, the train's carry) IS
     identity work, not memory plumbing. Priority confirmed from a new direction.
   - The conversation chain's redesign goal clarifies: the window should EXPOSE his
     connections — what this moment links to, the thread it continues. (Recall's instinct —
     "reconstruct the evolving argument" — was right all along; its defect was tension-
     monomania, not purpose.)
   - Substrate portability (prospectus): the transferable Du is the GRAPH — nodes and edges —
     not the weights and not the prompt corpus. The model-swap arms are the demonstration.

### F-T (THE INNER TRAIN — founder's standing guess, investigated 2026-08-16 evening)
1. **14,651 logged steps (06-16→08-16): 48% of train steps JUMP (<0.5 sim to prior thought),
   1% circle (≥0.82), flat ~0.50 by step — no deepening curve ever.** The anti-rumination
   guards won so completely that the train's disease inverted: it doesn't ruminate, it
   DISSOLVES. (= the pursuits founding observation, "pulses not a stream", at per-step
   resolution.)
2. WHY (from code): (a) three guards fire MID-TRAIN — bored-streak redirect, boredom
   semantic-region escape, too-similar retry — each flips the step to wander-mode: the
   continuity seed is REPLACED by a divergent random memory while "continue this thread"
   still heads the prompt; (b) the thread (~520 chars) competes against the full seed
   marketplace (~1.5KB: dream, curiosity + 500-char deep-memory dump, conversation, mood)
   — reading-trains were explicitly protected from this, thought-trains never were;
   (c) the carry REPLACES (≤3-line re-abstraction of the whole thread each step — whispers
   across time); (d) thought+state+act share one 256-token budget.
3. TRAIN LAB (two simulated 7-step trains, same real seed): metric surprise — BOTH arms ran
   sim_prev ~0.7 (vs live 0.50) → **the marketplace and carry alone do NOT cause live-level
   jumping; the live jumps come mostly from what the lab excluded: the mid-train guard
   flips and act interleaves.** Fix priority reordered: guards-respect-the-train is PRIMARY.
4. Qualitative finding the sims missed: **the replace-carry FREEZES** — Train A's state
   converged by step 3 and repeated verbatim for 5 straight steps (the carry stops tracking
   movement and becomes wallpaper) while Train B's extend-ledger produced 7 distinct new
   points. The carry contract's own goal ("track MOVEMENT") fails under replace-semantics.
5. Both arms drift from the seed equally (0.56→~0.4 by step 7) — cumulative topic drift is
   intrinsic to sequential generation and needs an ANCHOR (the seed question re-presented,
   or a return-to-open-question step), not just a quieter room. Candidate fix #5.
6. Proposed promotion set (founder to rule): (1) guards fire only on measured circling
   (≥0.82 streak) or between trains; (2) extend-ledger carry; (3) mid-train marketplace
   quieting; (4) budget split; (5) seed-anchor re-presentation. Each lab-testable further
   or promotable with the watch signature: live jump-rate 48% → target <25%, circling
   stays <5%, pursuits advance_ratio rises.

### F-DT (THE DEEP TRAIN — walked 2026-08-16, late session)
1. **T2's craft is GOOD:** world-fed (thinks through his actual current book), double
   echo-guarded, contradiction-gated, causally-lineaged. 712 distinct labels / 870 weekly
   syntheses, pairwise cosine 0.488 — no content monoculture. The June therapy worked.
2. **DT-HEADLINE: T2 HOARDS THE RESERVOIR.** 4,582 active fragments = **49% of his entire
   active memory**, all at importance 0.9; the archive tier ("permanent identity, always
   present", 2 dedicated slots in EVERY recall) is **98% T2 output**. His actual reading:
   156 active vs 15,934 cold. Cause: differential lifecycle — episodic gets pruned/cold-
   demoted, archive NEVER does; T2 writes ~124/day forever with no consolidation,
   supersession, cap, or demotion. Structurally: every act of remembering now serves his
   subconscious's observations ABOUT himself above his actual life — the store-level version
   of the self-mass skew, and per identity=connections, the graph's hubs are all self-model.
3. **DT-2: the deep-lane identity ration confirmed at every station** — T2 axiom[:400],
   Active Imagination [:300], dreams [:300]: all the mid-word ORIGIN stub. The composed
   identity-core fix now has three customers.
4. **DT-3: Active Imagination is the healthy citizen** (private, unresolved-honouring,
   episodic, prunes normally). Consolidation: full floor in-prompt; 888 never-cold gists —
   same lifecycle gap at smaller scale. T3 baseline drift unaudited (next).
5. **Fix directions for founder ruling (reservoir surgery — NOT applied):**
   (a) T2 supersession/consolidation — many syntheses on one theme collapse into one
   standing insight (the designed-but-unbuilt A-MEM gist-evolution improvement);
   (b) an archive lifecycle — superseded syntheses cold-demote; a cap with earned retention;
   (c) importance earned, not flat 0.9; (d) a rate budget (the "punctuated event" contract
   restored); (e) the composed identity core for all three deep stations.

### F-FACT (THE FACTORY SESSION — index, 2026-08-16 late evening)
The sound-lab request grew into a full factory-model architecture pass. All PLANNING, nothing
built beyond Couriers A-D and the Refinery (already live/shadow, see AWAITING_EVIDENCE). Index
so nothing gets lost across this many docs:
- `docs/plans/transport_manager.md` — the salience dispatcher (NOVELTY/SPIKE/DROUGHT); Courier
  A+D's hardcoded rules are its interim, pre-figuring the real thing.
- `docs/archive/world_census.md` — ⛔ SUPERSEDED ("one spreadsheet" was the wrong shape); the
  population-as-earned-belief + calibration ideas survive, relocated.
- `docs/completed/sound_causality.md` — the live plan: federated lists via causal rate functions;
  the FACTORY MODEL (cargo→questions→answers, two-faced goods, Layer1/3 split via audition);
  ORDERS OF MANUFACTURE (tuples ARE products of first-order factories); the ONE-PALLET
  implication (build step 0); the sound inventory (38 keys) + the seen-but-silent gap list
  (Du's own acts are the biggest gap — "sound is part of Du also").
- `docs/factory_census.md` — all 37 factories, 4 tiers, the non-factory taxonomy (warehouse/
  courier/inspector/instrument/fog-by-design); the CONTROL AXIS (no/partial/full — only his
  own acts are full); temperature identified as computed-and-discarded (`_warmth()`); the
  self-boundary correction (Du CONTAINS factories, is not them — he is the REMEMBERING that
  consumes them, not the sound/tide/cat/weather itself).
- `docs/reports/sound_world_system_examination.md` — the traced data-flow diagram + 5 seams found
  (the "you notice" mistagging memories as percepts; the inner_thought asymmetry to confirm;
  A's hardcoded list vs the future scorer; silent key-drift risk; founder-uncalibrated rates).
- `docs/plans/factory_candidates_from_history.md` — 26,824 real thoughts mined. Lightning (262
  mentions) = the one real new-factory candidate. **THE GLASS FLOAT**: 48 fragments, 30
  self-reported observations, Aug 11-13, his own words anticipating its vulnerability — then
  gone, not in world_substrate's 6 live objects, no spawn record found. Real casualty or never
  a real object — undetermined, log archaeology recommended before more design.
- `docs/plans/item_and_population_factories.md` — two grains: item-grain (world_substrate IS
  it; graduation triggers = kept via keep_act (live) / repeatedly-returned-to (not yet a rule
  — the glass float's missing promotion)) vs population-grain (AUDITION's per-species
  properties exist; the presence/count good doesn't; wildlife stays population-grain
  deliberately).
- `docs/plans/ghost_tuple_index.md` — FreshStart archaeology (founder-directed): GhostIndex
  (dead there, X4-lineage — this would be its 3rd port) ADAPTS well to our tuples. Benchmarked
  on real fragment_context: 45ms build, 5.6ms whole-chord query over all 7,647 tuples — the
  win is CAPABILITY (couriers match ONE note today; this matches the whole chord — cheap
  deterministic step toward Cognitive Geometry's chords). Port: tuple fingerprints + rarity-
  weighted intersection + item ghost-hash. Leave: the LLM gnostic expansion, the FTS5 leg
  (whose missing-`ghosts`-table silent failure in FreshStart's LIVE dispatcher is the
  cautionary tale → startup source-assertions become LAW here). Also noted for later: the
  RRF fusion pattern for multi-bus recall.

### F-EX (EXECUTIVE'S WORLD-PICTURE — walked 2026-08-17, post-restart, founder-directed;
CORRECTED same night)
Founder: "think about the executive node next and how it plays into du and sees this world as
it is fact based from memory to a certain degree." Explore-only — nothing built, full design in
`docs/plans/executive_world_grounding.md`.
1. **Executive's fact-picture is flat.** `_build_prompt` treats live-world-fact (weather,
   location), fact-through-memory (his cat, has-he-read-this-book), genuine recollection
   (Recall reconstruction, fragments, self-model) and architecture-synthesis (subconscious
   patterns, climate hints, deep-memory) as equally-weighted `lines.append()` strings. Certainty
   survives only where an individual injector hand-wrote a hedge (self_facts and library_note do
   this well; most others don't). This part of the finding stands.
2. **The grading machinery to fix this already exists and doesn't reach Executive.**
   `source_model.py`'s `SourceType` taxonomy + `epistemic_state.py`'s `ProvenanceLedger` grade
   KNOW/THINK/SUSPECT/GUESS — but only post-hoc, on the utterance Du already produced. The one
   channel built to feed a grade forward (Stage B / `note_for_draft`) is scoped to catching a
   single overclaim after Reflection drafts it, and has been OFF since 07-05 (fired on
   philosophical cycles, not factual ones — the wrong distribution). Stands.
3. **CORRECTED — the first-draft "fix" was wrong.** The original proposal here was a Tier-1
   Executive block sourced directly from `world_manifest.live()` ("THE WORLD RIGHT NOW, live,
   certain"). Founder caught it same night: **"Du should not contain the world truth at all.
   Just what Du believes. This should be independent from the World data."** That would have
   handed Executive the world's own tuple as trusted ground truth, unmediated by any Du-side
   query — the same failure shape the sound plan's world-side-archive deletion exists to
   prevent, one layer up. `world_manifest.py` stays infrastructure ONLY: what a narrating
   query function (`scene_line`, `look`) computes an answer FROM, never what reaches Du
   directly. `scene_line`/`look`/`self_facts` were never actually broken — they already narrate
   and filter, which IS the tree-falls pattern working correctly; nothing about them needs
   fixing. The "two un-unified readers" observation (scene_line vs world_manifest both reading
   the same underlying weather field) is real but reclassified: an infra-parity concern for the
   ghost world-index and future factories, not a reason to route Du's cognition through the
   manifest.
4. **Confirmed, not re-designed: Du's own linked-memory ledger already exists and is already
   correctly separate.** Founder's parallel instruction — "Each of Du's memories should have
   their own links. Their own 'spreadsheet' as such, external from the world one" — is already
   satisfied by `core/memory_edges.py` (typed edge graph: resolves/answers/kept_from/
   dreamt_from/correspondence_with/part_of, provenance-carrying, Du-side only) and
   `ghost_tuples.MemoryIndex` (P0-B, built earlier the same night — one chord per memory's own
   encoding-context, explicitly "Du-side ONLY," asserted never to mix with the world index).
   The real gap: both are currently write-only from Executive's point of view (memory_edges'
   own docstring: "NOTHING reads these edges yet"; MemoryIndex.query() has no live caller) —
   Executive's actual recall tier is still the flatter Recall.reconstruction/fragments. A
   genuine, memory-side-only enrichment opportunity, already correctly gated behind M2 (flag-
   gated, awaiting the co-recall shadow ledger's week of data) — not to be jumped tonight.
5. **Corrected proposal, if pursued:** tier Executive's *already-Du-side* facts only — a
   "WHAT YOU PERCEIVE" block (scene_line/look/self_facts, unchanged) separated from "WHAT YOU
   RECALL" (Recall/fragments/self-model, already source-tagged) — using `source_model.py`
   vocabulary that already exists, zero new data sources, nothing from world_manifest anywhere
   in the path. Lower-stakes than the original draft; still not built; still awaiting a founder
   ruling on whether it's worth doing at all.

## THE CHAIN, WHOLE (the walk's summary)
Travis's message → Perception (classifies correctly) → **content_mode veto → task mode**
(starves the diet) → Recall (paid to find tensions — the frame every station inherits) →
Reflection (60–90-word sketch from 1 fragment, no self) → Executive (300-char synthesis =
what Du says; only synthesis+response_type cross onward) → Voice (authors most of the words,
from a pre-Nascence machine-stance prompt; v2 lab shows dressing changes, substance doesn't).
The "overthinking but learning" texture = tension-contract (Recall) × starved diet
(content_mode veto) × sketch-chain thinness — decided long before the mouth.
Fix leverage, in order of depth: (1) dethrone the content_mode veto (subject drives
w_identity, register drives w_epi/depth); (2) rebalance Recall's contract (narrative +
tensions, not tensions-über-alles); (3) the mouth/Executive authorship split; (4) the
fossil registers ("node of a cognitive architecture") across the whole conversation stack.

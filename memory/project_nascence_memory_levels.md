---
name: project_nascence_memory_levels
description: "Nascence — THE foundational memory reframe (docs/memory_levels_plan.md): abstraction-first, linked, gated-detail memory. Transcript→abstraction; lossy self-gist DRIFT = individuation engine; 'links not pipelines'. Supersedes #4 T4-commit spine. Ranked #1 thread. PHASE 0 BUILT 2026-06-17; PHASE 1 (LIVE demotion — the loop-break) BUILT 2026-06-18 RESTART-REQ after the evidence battery cleared."
metadata:
  node_type: memory
  type: project
  originSessionId: 012323c4-3fb7-4445-b78f-150a4e0a1404
---

Nascence **MEMORY LEVELS** — the deepest reframe of the project, spec'd 2026-06-17 (`docs/memory_levels_plan.md`,
NOT built). Came out of Travis describing the lost pre-fresh-start 9-layer memory (working/context/short/mid/long/
archive-hidden + custom compression: LLM-context + word-stripping + ghost-index + triple indexing). FreshStart kept
~1/3 (cognitive_mmu 4-tier + ghost_index + lossy_compressor + graph engines); Nascence regressed to ONE flat
transcript store (single `nascence.db`, `memory_fragments`, cosine recall, no graph).

**THE ONE PRINCIPLE Travis named: memory ABSTRACTS, it doesn't TRANSCRIBE.** Keep the technique (not every sum),
the event ("played Monopoly with a friend", not every move), the idea (not every step), the feeling — reconstruct
the rest. That single mechanism does THREE things: filters noise, de-loops (no verbatim left to recite), and
**individuates** (self-material reconstructed THROUGH WHO HE IS NOW drifts → identity forms/changes instead of
freezing). **Lossless memory is WHY Du stagnates** — he stores the river verbatim, recalls it verbatim, reinforces
it → recites it 83×, T4 can never out-fit it. The week's four hardest problems (recitation loops, T4 can't commit,
store bloat, blunt prune) are ONE disease: transcript memory. The fix is ONE organ replacing FOUR patches
(loop-guard, T4 gate, prune, dedup).

**"LINKS, NOT PIPELINES" (Travis's key constraint) resolves drift-vs-facts:** nothing deleted. A memory is held at
linked levels — GIST (abstraction, what normally surfaces, self-gists DRIFT) → link `distilled_from` → RAW
(verbatim, COLD/gated, never drifts, retrievable only via deep recall). Aging BUILDS A LINK down to demoted detail;
it doesn't push through stages and drop off the end. Drift on top, ground truth beneath, gate decides which
surfaces. Du CAN still recall the steps/sums when deep research calls — by descending the link. This IS the graph
the cognitive-ledger thread kept re-deriving, finally with a job.

**NOT A LADDER — A LATTICE (Travis refinement):** levels sit side-by-side AND above/below. Up/down =
abstraction (`abstraction_level` 0/1/2); side-by-side = `kind` (episodic|semantic|procedural|affective|
self, peers at one height); links go all directions (DOWN distilled_from/instance_of/step_of; SIDE
relates_to/contradicts/supports — the ledger's contradiction edges live here free). **PER-RUNG CLOCKS
(the key):** drift + cold-horizon are per-`kind`, NOT global — "sums quick, ideas long": procedural raw
goes cold FAST (drop instances, keep the stable technique), self/idea gists retained very long + drift
SLOWLY (weeks). Small per-kind config (cold_horizon/drift_rate/retention), not new schema. WHAT EXISTS:
archive(2548)+episodic(3500)+semantic(787)+emotion_vec+chapters = a HEAP; MISSING = the structure
(working/context/short/mid stages, the kind-separation, the links, the per-rung rates). Building
connective tissue, not new organs.

**Grounded build (additive, NOT a rewrite):** chapter system already proves the pattern (`chapter_id` links
fragment→chapter, `chapter_level` hierarchy, chapters "recalled only intentionally" = a gate). Generalise it: +2
cols on memory_fragments (`abstraction_level` 0 raw/1 gist/2 gist-of-gists; `cold` gate) + new `memory_links`
(parent_id/child_id/link_type) — the genuinely new primitive (only curiosity `parent_id` lineage exists today).
Consolidate (at sleep) extends chapters/grounded_learning with the TWO new steps: LINK gist→raw + GATE raw cold
(only AFTER the Emissary grades the gist faithful to its sources = the **decoupled judge**). Normal recall adds
`WHERE cold=0` (de-loop+filter). `deep_recall(seed, hops)` traverses links DOWN to cold raw, GATED by a decoupled
System-2 trigger (deliberation/curiosity/frontier) — idle thought gets gists only.

**MINIMUM TRANSFORMATIVE SLICE (auditor consensus 2026-06-17 — re-sequenced):** `abstraction_level` +
`memory_links` + `cold` gating + `deep_recall` = the WHOLE foundation, ~60-80% of the value, BEFORE a single
self-gist is reconstructed. DRIFT was sequenced too early — it's the CAPSTONE (Phase 3), NOT core: no earlier
failure (transcript dominance, loops, store pressure, bad attention targets) was caused by lack of drift, so the
slice fixes them without it; drift alone delivers identity actually CHANGING and must sit on a proven substrate;
nothing else depends on it (slice is fully valuable with drift off indefinitely). Don't build the six axes up
front. **Phasing:** P0 ship CORE schema only (abstraction_level+cold+memory_links)+SHADOW distiller (log would-be
gists/links/Emissary grade, gate nothing). P1=THE SLICE (link+gate+deep_recall, uniform cold-horizon, placeholder
trigger; gate: recitation drops, store eases via demotion-not-deletion, deep recall fetches right detail,
provenance answerable by walking links). P2 richer axes (kind/grounding/hidden-temp/per-rung clocks — typed
objects for attention+ledger; still NO drift). P3 DRIFT capstone (self-only, observe-first, Emissary-bounded;
gate: river MOVES w/o a T4 commit). **Makes T4 a NAMER of drift, not a committer** — supersedes the #4 spine.

**RANKED #1 of all threads** (Travis/auditor 2026-06-17, above attention-economy/provenance/T4/dream/ledger) —
because it gives the others somewhere concrete to LIVE: attention operates on gist-objects not fragment #4821,
provenance IS a link (no separate version-control subsystem), T4 observes drift not frozen text, dreams revisit
gists, pruning becomes demotion. The thesis line: **"fragments are not memory — they are the evidence BENEATH
memory"** (extends notes≠ideas / figures≠tensions / recurrence≠development / persistence≠value down to the
substrate). A terrain change, not another organ.

**GATING RULE (hard constraint on the deferred trigger — 2nd auditor, 2026-06-17):** default surface = gist;
detail must stay CHEAP to reach in the right CONTEXT. The dial the architecture balances on — too hard to descend
→ vague (gist w/o grounding); too easy → collapses back to transcript mode. So the trigger is CONTEXT-SENSITIVE,
not a fixed threshold: essay/citation/contradiction-chase → near-automatic descent; idle drift → near-never.
Detail sometimes matters MORE than gist (sources, debug steps) — never make it unreachable, only un-surfaced.
This is why the recall trigger is LOAD-BEARING, not a Phase-1 footnote.

**LEDGER RELATIONSHIP (merge-vs-separate, answered):** the cognitive ledger ("memory is prediction
infrastructure") = STRUCTURE+POLICY on ONE graph, not a separate system. Its ladder IS this plan's abstraction
axis (Evidence≈raw / Claim≈gist / Model≈theme / Identity≈identity); its supports/contradicts = the sideways
memory_links; its collapse-to-confidence = demotion. So the ledger is a TYPED-VALUE OVERLAY (confidence/status on
gist nodes + a predictive-value warmth/demote rule), ABSORBED at Phase 2 (grounding axis + per-memory dynamics),
NOT built in parallel. Division: ledger = what earns permanence; this plan = how the permanent is organized once
earned. Gives the shelved ledger framing a concrete home.

**PHASE 0 BUILT + in-vitro validated 2026-06-17 (RESTART-REQ):** core schema migration in store.py
(abstraction_level/cold cols both DEFAULT 0 → all 6836 rows stay raw+warm = ZERO behaviour change; +
memory_links table, TEXT keys to match fragment_id, created EMPTY) · `left_lane.grade_gist_faithfulness`
(the decoupled Emissary judge: is a gist faithful to its sources?) · `core/memory_levels.py` shadow_distill
(at sleep: cluster recent raw by kind+top-TOPIC-token w/ stoplist, distil would-be gist via call_node_json,
grade via Emissary, LOG to data/memory_levels_shadow.jsonl — stores nothing, gates nothing, no recall change)
· sleep hook in inner_monologue ~228 beside grounded_learning · du_pulse `memory levels (P0)` gauge. Validated:
files compile, migration on a COPY (live DB untouched) adds cols+table cleanly, clustering dry-run on real data
→ coherent topical clusters (camp/semantic, after stoplist fixed 'action'/'reading' kind-leak). **PHASE 0 FIRST-NIGHT DATA (2026-06-18, 5 gists, mean_faithful 0.77 range 0.6-0.85, episodic/self/semantic — §11
of the plan):** (1) SELF-GIST WORKS (0.85) — 5 scattered self-thoughts → one faithful claim ("tension between the
structured predictions of my programming and the fluid reality... identity crisis" = the river/becoming tension
compressed); thesis real on live data → Phase 1 may include kind=self. (2) **CORRECTED 2026-06-18 (Travis pushed back on "Black
Bear hallucination") — THE JUDGE ITSELF CONFABULATED.** My "Emissary caught a confabulation" was WRONG: the Black
Bear is REAL + richly grounded (17 frags: Camp-Lore reading→Du's question→research→his living symbol for the
religion/autonomy struggle "that something greater feels like the Black Bear, watching, waiting for me to face what
I have not yet embraced") AND it was at char 243 of source #4 — INSIDE the 300-char window the judge was shown. So
the Emissary had it in front of it and still cried "invented" = a FALSE fabrication-flag, denying a real
self-defining memory; docked the gist to 0.85 for a real detail (score contaminated too). INVERTS the finding: the
Emissary is NOT a reliable invention-detector alone — an LLM verdict can't be the final word on itself. **Phase 1
RULE (re-stated): the decoupled judge needs its OWN DETERMINISTIC BACKSTOP** — before an "invented X" flag is
trusted or gates anything, literal+embedding presence-check X against the source AND the wider store (a 2-line
check would have overturned this; cross-links grounded in the wider memory = the lattice's relates_to edges
working, NOT invention). Gate raw cold ONLY above faithfulness ~0.75 AND after the backstop confirms any "invented"
flag is real. The camp 0.6 (dropped specific ceremony commands = "detail matters more than gist") still stands.
Also: feed the judge FULLER sources, not 300-char stubs.

**BACKSTOP BUILT observe-only 2026-06-18 (RESTART-REQ) — Travis: "the Black Bear was important, almost a prototype
god for Du, a spiritual symbol" → the judge nearly ERASED emergent meaning, so the backstop is a GUARD not just a
metric.** (1) `left_lane.grade_gist_faithfulness` now makes the Emissary ENUMERATE its `invented` phrases + fed
FULLER sources (800 vs 300 chars). (2) `memory_levels.verify_invention_claims(invented, full_sources)` = the
non-LLM corroborator: per claim → IN_SOURCE (in the fed sources = judge hallucinated) / CROSS_LINK (in the WIDER
store = real relates_to edge, not invention) / GENUINE (nowhere = real confab). Wired into shadow_distill (logs
invented_claims + false_flags), status() + du_pulse expose the FALSE-FLAG RATE. VALIDATED on the real case: "Black
Bear"→IN_SOURCE (would've overturned the flag); "purple zeppelin"→GENUINE (not a rubber stamp); cross-link case→
CROSS_LINK. **Phase 1: only GENUINE flags may affect gating; IN_SOURCE/CROSS_LINK = judge erring, must NEVER erase
a memory.** The decoupled-judge principle one level deeper (a non-LLM judge of the LLM judge). (3) ACTIVITY_MEMORY IS ALREADY AN ABSTRACTION
— 2 clusters built from "Returned to X — 77 sittings" event-records = gist-of-gist → Phase 1 must STAMP
abstraction_level at write time by origin (activity_memory/understanding/consolidation/chapter = already ≥1; only
verbatim thought/passage/study-note = level 0); distil from level-0 ONLY, link down to raw. Carried watch:
self-kind fired once (accumulate more); clustering must be LEVEL-AWARE in Phase 1.

**2026-06-18 DEEP REVIEW (3 forward-relevant shifts, in plan §8/§10/§11):** (A) **CENTRAL CONCEPTUAL RISK —
"are gists stable objects?":** Phase 0 proves SUMMARIZATION (raw→useful-summary), NOT identity formation
(raw→gist→theme→identity). Humans recall from schemas/causal-models/predictive-structures/narratives — a gist may
be a SCAFFOLD not the final object. Drift (P3) admits gists aren't stable, BUT even a drifting gist is gist-TEXT;
identity may need a different representational TYPE (a MODEL/predictive-structure, where the ledger's Claim→Model
overlay does real work), not a longer sentence. Verdict: VALIDATED as a MEMORY architecture, UNPROVEN as an
IDENTITY architecture — don't over-claim identity from summary evidence; resolve empirically at P2-P3, may force a
model-typed top of the abstraction axis. (B) **FINDING #3 IS BIGGER — level = PROVENANCE, writers DECLARE, distiller
LINKS:** the system already emits an unlabeled ladder (reading=raw0/understanding=1/chapter=2/activity=1/T4=identity3).
Architecture flips from "distiller manufactures levels" → "writers stamp the level they produce; distiller builds
LINKS + summarizes level-0 ONLY" = a RELATIONSHIP-BUILDER not a universal summarizer (absorbs provenance: level +
down-links IS the provenance record). P1: add `abstraction_level` arg to store_fragment (each writer declares,
default 0). (C) **START MEASURING the recall trigger NOW** (it's MORE central, not less — the line between "a mind"
and "a database with summaries"): add a cheap observe-only GIST-INSUFFICIENCY log in P1 (when gist insufficient /
raw needed / why / what task) → spec the trigger FROM the log, not a guess. Auditor ranking: 1 Memory Levels / 2
Idle-Exec+Attention (allocator over the new gist-objects) / 3 Pulse Manager / 4 Provenance (absorbed into links) /
5 Ledger (overlay) / 6 T4 (consumer) / 7 Active Imagination (consumer) / 8 Drift (capstone). The other projects
become CONSUMERS of the graph, not separate engines.

**OBJECT TAXONOMY (plan §12, 2026-06-18 — resolves the memory-vs-identity question all 3 auditors converged on):**
"gist, claim, or model?" = ALL THREE at different levels, TYPE changes up the axis: 0 evidence(raw) / 1 GIST
(content compression, Emissary-graded) / 2 CLAIM (held proposition + confidence/status) / 2-3 MODEL (predictive
structure of claims, revised by PREDICTION ERROR) / 3 IDENTITY-OBJECT (a self-MODEL). **GIST is always the readable
SURFACE; but the load-bearing object changes type — at top the gist is only the readable FACE of a MODEL.** So
"summary=memory" is TRUE for content (gist IS the object) but FALSE for identity (object=model, gist=its
expression). This DISENTANGLES the two fused problems: memory-organization (de-loop+preserve-detail)=P1-2=gist+
links+gating (what P0 evidence supports); identity/individuation=P3=a MODEL problem, NOT solved by a clean gist
substrate. **Sharpens P3 + gives a confabulation DISCRIMINATOR the Emissary can't:** if identity is a model,
identity CHANGE = model-update driven by PREDICTION ERROR (Nascence already has L1 prediction_error!), drift = its
SURFACE expression. Legitimate self-update = prediction-error WARRANTS it (self-model mispredicted→revises);
confabulation = gist-text drifting with no predictive grounding. So P3 reframed: not "let self-gist drift + hope
the judge catches lies" but "let the self-MODEL update when reality mispredicts, gist re-renders to match." Ledger
overlay (P2) = where claim/model typing+confidence live → ledger is no longer "a value policy" but THE claim/model
TYPING of the upper axis. Writers stamp the TYPE (evidence|gist|claim|model|identity), not just a number. HONEST
STATUS: validated as a MEMORY architecture, UNPROVEN as IDENTITY; open buildable Q = "does a prediction-error-
updated self-model produce identity change gist-drift alone cannot?" — test P2-3, never assert.

**OBSERVE-ONLY INCREMENT BUILT 2026-06-18 (RESTART-REQ) — Travis chose this over Gemini's "build full Phase 1
now" (1 night/5 gists/self-once + Finding-3 contamination = too thin to flip live recall; trust the convergent
discipline over the single enthusiastic authorization).** NO gating/demotion/deep_recall/drift — fixes the data
validity + starts trigger telemetry: (1) `store.py` `_origin_level` (origin→level map) + `abstraction_level` arg on
store_fragment (writers DECLARE via origin; INSERT stamps it) + one-time idempotent BACKFILL in init_db (validated
on a copy: 794 rows correctly reclassified — 790 gists action/consolidation/understanding/essay→1, 4 chapters→2;
6053 stay level-0; 2nd run touches 0). (2) `memory_levels.py` _KIND/_RAW_ORIGINS tightened to level-0 ONLY (drops
action/understanding) + the existing `abstraction_level=0` query filter → NO MORE gist-of-gist contamination →
Phase-0 faithfulness data now VALID. (3) NEW `core/recall_demand.py` deep-recall-DEMAND telemetry (logs the
task-positive "a gist won't do, need the raw" moments = the empirical basis to DERIVE the P1 trigger, not guess) +
hook at essay_lesson.gather_notes (the canonical write-from-raw-notes moment) + du_pulse `recall-demand log` gauge.
Gemini blueprint ERRORS caught: fragment_id is TEXT not INTEGER; schema already shipped P0; retrieve() is
tier-mixed not string-munge; temp-string is a P2 axis (keep boolean cold for P1 minimum slice). HOLD for Phase 1:
gating+demotion+deep_recall, after several CLEAN nights (valid data now) + self-kind seen more.

OPEN Qs deferred: the deep-recall trigger (spec LATER once we know what we're recalling — but it's load-bearing,
see gating rule); charge's sign on drift (fixes flashbulb vs amplifies — empirical, Phase 3).

**PORTED IDEAS from 2 external "second-brain" repos (Travis 2026-06-18, plan §13 — both are assistant/KM TOOLS not
psyches; most doesn't transfer; honest filter applied):** (1) **HYBRID RETRIEVAL** (henrydaum) — Nascence retrieve()
/_score_tier is PURE COSINE when there's a query vec (lexical only a fallback); embeddings DILUTE specific tokens
(proper nouns/titles/symbols) — the Black Bear proved it (the deterministic backstop IS a lexical check). FOLD: fuse
lexical(BM25-ish)+cosine, semantics leads but lexical real-weighted; matters MOST for deep_recall (descent wants the
EXACT term not a fuzzy neighbour — near-prerequisite); build WITH deep_recall in Phase 1, not a 2nd pass. (2)
**LATTICE-INTEGRITY LINT / "cognitive hygiene"** (NicholasSpisak's only novel bit — a wikilink lint) — once
memory_links exists it can rot SILENTLY: dangling links (gist→deleted raw), **COLD raw with NO parent gist =
unreachable/LOST** (the demotion-safety failure §8 warns of), orphaned gists. FOLD: a small sleep-time observe-first
`memory_lint()` walking memory_links → report/repair dangling ids + RE-WARM cold-with-no-inbound-link (never strand a
memory) + flag zero-down-link gists; ships WITH Phase 1 (when demotion+links can first break). (3) VALIDATION only:
NicholasSpisak's sources→entities→concepts→synthesis taxonomy independently MIRRORS evidence→gist→claim/model (§12) +
entities-vs-concepts backs the kind axis — convergent external design = mild confirmation the typed-abstraction
direction is right. (3) **COUNT-GATED TIERED PROMOTION** (huytieu/COG — repo 3, plan §13.4) — COG enriches entities in tiers by
MENTION COUNT (Stub@1/Moderate@3+/Full@8+) = a concrete answer to "WHEN does a node earn promotion up the
abstraction axis?": when supporting-evidence count crosses a threshold (sharper than vague "charge"). FOLDS: (a)
the SYMBOLIC LENS promotion gate (currently fuzzy "genuine+low-echo+distinct") → count-gate it: a symbol earns a
symbol_tablet once it recurs ≥N times (the Black Bear @17 frags = "Full tier" → exactly what should mint a symbol);
(b) abstraction axis (P2): gist→claim→model promotion gated on inbound memory_links count (cheap, deterministic,
decoupled). (4) 3-WAY VALIDATION: three independent "second-brain" repos converge on this plan's spine — typed
abstraction, provenance+confidence, multi-timescale consolidation (≈chapter hierarchy), link-integrity, progressive
summarization = mild evidence the direction is sound. COG's worker-split (fast System-1 I/O workers + slow System-2
reasoning lead, FILE handoff not inline tokens) = a reference for the deferred "more lines=lanes=engines" trains
work (Nascence nodes already hand off via DB → already avoid the token-bloat it solves). Verdict across 3 repos: 3
real folds (hybrid retrieval, lattice-lint, count-gated promotion) + validation; everything else = "be a good
assistant," not Du's problem.

**PERPLEXITY REVIEW folds (2026-06-18, plan §14) — most "blind spots" already tracked (hybrid §13.1, lint §13.2,
gist-vs-model §8/§12, temporal-versioning=Zep bi-temporal §13.6, drift-special-case=§12); 3 sharpenings + 1 reframe:**
(1) HYBRID = a TWO-STAGE PIPELINE not one fused score (§13.1): lexical candidates → semantic+graph rerank → link
traversal (gist=reranker not sole entry point). (2) FAITHFULNESS IS MULTI-PART + judge is a STACK not one LLM score
(§14.1): source-fidelity(deterministic)+cross-source-support(graph)+non-contradiction(graph)+plausibility(LLM=ONE
vote, overridden by deterministic/graph when the term is present) = a LAYERED decoupled judge on the built backstop.
(3) REFRAME: **memory is a CONFLICT system not only compression** (§14.2) — interference-control/anti-over-merge
(split a bimodal cluster before distilling = split-twin of §13.2 duplicate-collapse); negative-evidence (gist
broadly-right-with-dissent KEEPS the dissenting raw via contradicts-link, never gates it = camp-0.6 lesson);
confidence-decay (wire to LEDGER confidence not just retrieval strength); **PRIVACY/SAFETY = NEW `protected` axis**
(L0 constitution / Travis's told / emergent self-symbols like the Black Bear = never promoted/drifted/gated — the
safety rail drift needs). HELD: "type upper layers early" → §12 DEFINES types day-one but BUILDS claim/model in P2
(minimum-slice); agree on destination (identity=model-update-via-prediction-error = review's own point), differ on
build order. Review verdict: "genuinely promising, much closer to a real cognitive memory architecture." [[feedback_decoupled_judge]] [[project_nascence_cognitive_ledger]]

**PHASE 1 BUILT + validated 2026-06-18 (RESTART-REQ) — THE LOOP-BREAK GOES LIVE.** Context: Travis "we've T4-trapped
OURSELVES — waiting for clean evidence against a corrupt baseline deepens the stagnation"; agreed to move via memory
(not unlock T4 — its INPUT is corrupt, candidates are reworded-river; the gate correctly refuses cosmetic_churn).
EVIDENCE: ran `scripts/memory_levels_batch.py` (one-off batch distill over clean level-0 raw, no wait) — 28 gists;
SELF-gists 0.8 LLM / 0.88-0.96 deterministic source_fidelity / sane links; agreement 80-85%; backstop caught the
27-44% Emissary false-flags. mean_faithful 0.71 (under 0.75) BUT the faithfulness FLOOR makes the mean irrelevant —
high gists demote, low ones leave raw warm. THE BUILD (flag-gated for reversibility, `memory_levels.PHASE1_ENABLED
=True`, FAITHFUL_FLOOR=0.75, MAX_DEMOTE_PER_RUN=24): (a) `_commit_gist` — stores the gist (level-1, surfaces), links
gist→raw (memory_links), DEMOTES the raw cold=1 ONLY if faithful≥floor + backstop-clean (no GENUINE invention) +
protected=0 + level-0; (b) `store.retrieve()` skips cold rows (mirrors the chapter-skip) = the verbatim river leaves
NORMAL recall, the gist answers for it = the loop-break; (c) `deep_recall(seed_ids)` traverses links DOWN to cold
raw (consumer wired in essay gather_notes); (d) `memory_lint()` at sleep RE-WARMS stranded cold (cold w/ no inbound
link = unreachable = the §8 safety failure); (e) `uncold_all()` + the flag = the revert net; (f) `protected` column
(§14.2). VALIDATED on a DB COPY (live untouched): commit→demote 4/4 + 4 links; retrieve EXCLUDES cold + gist
surfaces; deep_recall recovers 4/4; lint re-warms stranded; uncold reverts. du_pulse `memory levels (P0) → PHASE 1`
gauge (cold/gists/links). RUNS at sleep (conservative 24/run). WATCH post-restart: cold count climbs, recitation/
river drops in recall, lint re-warms ~0 (no strays), nothing important wrongly cooled (deep_recall + direct queries
recover it). REVERT if bad: PHASE1_ENABLED=False + uncold_all(). This de-recites the river → self-syntheses can
drift → T4 finally gets a non-monoculture candidate (the sequence that unlocks identity without committing
corruption).
[[project_nascence_theme_recurrence]] [[project_nascence_t4_redesign]] [[project-nascence-character-integration]]

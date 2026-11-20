---
name: project-nascence-geometry-tuple-index
description: 🟡 BUILT — P1 (2026-09-02, D-0107, F-0600 — standalone offline run-transition index sidecar, not wired into any live code path); otherwise a staged design doc (docs/staged/geometry_tuple_index.md) for multi-dimensional indexing (world-state, episodic memory, epistemic confidence, time) informed by ABF/Pinnacle archaeology, a real cross-plan consumer survey (F-0251), and three rounds of SOTA literature grounding (F-0252-F-0254) -- explicitly NOT part of Du's active architecture, no cognitive_geometry.md parent; ROADMAP.md badge corrected 2026-09-27 from an earlier LIVE badge (which overstated "live" for a deliberately-never-live offline artifact) to BUILT.
metadata:
  type: project
  originSessionId: c01d1276-8ff7-4f17-ab4a-607cfa3f1b07
  sessionStarted: 2026-08-24
  modified: 2026-09-27T10:55:46.118Z
---

**Stage sync 2026-09-02 (J-0415):** P1 (pilot run-transition index, weather field) is BUILT and
verified — D-0107 (founder-ruled, travis, 2026-09-01) authorized the build; F-0600 (verified)
records the result: additive sidecar `scripts/geometry_tuple_p1_run_transition_index.py` over
data/geometry_tuples.jsonl, 100% point-query correctness (31,111/31,111), 248 transitions,
~5855x point-query speedup, source untouched. Offline artifact only — NOT wired into any live
code path; nothing beyond P1 authorized. Plan doc Status line, ROADMAP.md badge (🟢), and this
file now agree.

Promoted from idea [[I-0023]] (itself promoted from thought T-0010), following the ABF-pillars
archaeology in [[project-nascence-abf-pillars-archaeology]] and its recovery-candidate fact-file
[[project-nascence-titan-final-recovery]]. Findings F-0243-F-0250 grounded the founder's Gemini
brainstorm: most `core/lib/abf/` v3 pillars are broken/one-directional, but a separate "Pinnacle"
generation (`pinnacle_hmc.py`, `neural_folder.py`) is real and self-verified, with a genuine
adaptive-octree index intertwined into its compression.

**Founder correction, load-bearing:** after an initial draft wired this as a child plan of
[[cognitive_geometry]] under Nascence's live ROADMAP cluster 0, the founder explicitly rejected that —
this must stay outside Du's active architecture entirely ("an outside tool at the moment that we may
give to Du at a later date... totally a thought experiment"), since several other real active plans
already touch this territory. Resolved via clarifying question: written to
`C:\Nascence\docs\staged\geometry_tuple_index.md`, unlinked from ROADMAP.md, no
`cognitive_geometry.md` parent relationship, no plan-schema-audit registration.

The staged doc keeps the project's own pre-registered-metrics/gate/kill-criterion discipline (good
practice regardless of live status) across 3 hypothetical phases: P0 reads job J-0210's results
(already independently filed, testing whether ABF's dead `fold_with_checkpoints` pattern transfers to
JSONL indexing); P1 would build one pilot run-transition index over one `geometry_tuples.jsonl` field;
P2 evaluates (never builds) whether [[project-nascence-abf-pillars-archaeology]]'s sibling document
`docs/RESEARCH_specialists.md` (a real, dormant "minibots as specialist nodes" brief with live
self-distillation logging) has any real consumer for this. Explicitly rules out fixing
`moment.py::recall()` (a different, semantic-search problem) and rules out any model training.

Lesson for future sessions: **when a founder brainstorm draws on archaeology from a sibling/predecessor
project, verify before assuming it should integrate into the live project's plan toolchain** — ask
first, since "investigate the principles" and "wire this into active work" are different requests.

**Session continuation, same day, FreshStart window (2026-08-24 later)**: added §2.4 (slice+overlay:
holes/missing/new/patterns as four standard queries over any dimension or overlay, plus the
disparity-filter "remove big-ticket items, see the residual pattern" refinement) and 3 predictive
targets for the Knowledge dimension (next-transition direction, time-to-next-transition, oscillation
rate) — both flagged unconfirmed pending Travis's correction, both reusing P1.5's own pre-registered
metrics rather than inventing new instrumentation.

**Real empirical benchmark run, same session (F-0269)**: tested whether the orphaned
`engine/oxibonsai/.../embedding_index.rs` candidate (corrected: it's a single-layer NSW/simplified-
HNSW-variant, not full HNSW as the doc had labelled it; also found `oxibonsai-runtime/TODO.md`'s own
`[x]` "semantic cache done" checkbox is wrong — `semantic_cache.rs` never calls `EmbeddingIndex`)
actually clears Hilbert's >3-dimension wall on real Du data (14,304 real 8-D affect vectors,
canonicalized for the first time — the fill-missing scheme §6 had named as an undesigned prerequisite).
**Verdict: no, not as-is.** At documented defaults, 12.4% recall (one query found zero of its true 10
neighbours). Fixing recall to 88.4% needs a much wider config, at which point queries cost 14.96ms —
~7x SLOWER than a plain same-language Rust linear scan (2.145ms, exact). Insertion-order/temporal-
autocorrelation was tested directly as a hypothesis and ruled out (shuffling barely moved the number);
it's a search-breadth config problem in this implementation, not (yet) proof of the theoretical Pestov
wall biting at only 8 real dimensions. Full write-up: `docs/staged/geometry_tuple_index.md` §3.1.
Real, added artifact: `engine/oxibonsai/crates/oxibonsai-runtime/examples/geometry_bench.rs` (new file,
additive, not wired into the crate's default build/test).

**Follow-up, same session (F-0275): found a real true-HNSW candidate and it works.** Web-verified
`hnsw_rs` 0.3.4 (jean-pierreBoth, pure Rust, no C deps, dual Apache/MIT, 118k downloads/month) — real
and current, unlike `instant-distance` (archived July 2026) or `usearch` (C++ FFI core). Added as a
dev-only dependency, re-ran the identical benchmark: true HNSW build 1.557s / query 0.0835ms / recall
88.8%, vs. the orphaned NSW candidate's best config (96.8s / 14.96ms / 88.4%) and the plain linear
scan (2.145ms / 100%). **~179x faster query than the NSW candidate, ~26x faster than linear scan, at
comparable recall.** F-0269's negative verdict was about oxibonsai's own simplified implementation,
not HNSW as a technique — the SOTA citations were right all along. Not run against a pre-written
prediction sheet, unlike F-0269 — named as a real procedural gap, not hidden. Still untested: the
actual multi-dimensional (Time×Knowledge×Memory) overlay case — both benchmarks so far are
single-dimension (Knowledge's affect vectors only).

**Founder decision, same session: "stop deferring" `moment.py::recall()`.** Added §2.5 — un-defers
the semantic/ANN boundary this doc carried since §0, at the DESIGN level only (activation guard §7
unchanged, no code touches live `moment.py`). Formalized fact-shaped (needs P1/P1.5's 100%-correctness
index) vs. gist-shaped (HNSW candidate) query split, re-read all 7 real §6/§7-survey consumers through
it — only 2 of 7 are clean gist-matches (`lane2_the_witness.md`, `memory_multiway_linking.md`); one
more is actually a rarity/salience question (`ghost_tuples` territory, not HNSW). **Real load-bearing
gap named**: `moment.py`'s actual similarity field `emb` is 384-D (verified by reading a live row) —
everything benchmarked (F-0269, F-0275) was only 8-D affect vectors. The 8-D win is not evidence this
works at 384-D; that's a distinct, unrun test.

**Closed same session (F-0276)**: real 384-D benchmark against live `moments.jsonl` `emb` vectors
(14,478 rows). True HNSW win transfers — recall actually BETTER than 8-D (89.6%/80.0% vs 88.8%/60.0%),
~6.9x query speedup over a fair Rust linear-scan baseline. Not a low-dimensionality artifact.

**Then swept docs/plans/*.md + System_Overview.md for missing tuples/indexes (F-0277, founder-directed:
"work out missing tuples/indexes from the plans folder and the overview").** Found 4 real tuple/index
systems this design doc's own §10 inventory had missed: `core/experienced_tuple`
(`world_context`/`fragment_context`, live, parallel to `geometry_tuples.jsonl`, already tuple-fed to
Lane 2 Witness in a real 2026-08-21 experiment); `sync_fragment_context()` (an ALREADY-BUILT
deterministic tuple→memory join, 300/300 verified, 6,804 memories, synced each sleep — **not yet
reconciled against this doc's own proposed `cycle_id` join fix, open question**); `world_substrate.py`
item-tuples (founder-originated, item-grain); `investigative_action_log.jsonl` + a SQLite index
projection (same event-log-plus-index shape as this doc's own P1/P1.5, built independently elsewhere).
Also found real missing prior art: `cognitive_geometry.md`'s own Kill Criterion #6 ran the same
neighbour-overlap methodology this session's benchmarks used, months earlier (3.8% overlap, 90.8%
marginal reach) — should have been cited from the start. All written into §10. Session paused here per
founder instruction to stop and discuss.

**Sound-encoding thread (F-0278): founder recalled an old sound-steganography pillar; real, working, but
led to a better result than the literal ask.** Verified directly: `C:\FreshStart\core\lib\abf\
abf_cipher_v3.py` (Pillar 15, real BPSK phase-modulation, bit-perfect round trip run and confirmed) —
NOT `abf_echo_1d.py` as this doc's §4 had wrongly pointed at (Echo has no decoder). Real cost measured:
2,822x storage expansion, ruling it out as a literal compression mechanism; "key" is decorative, not a
real cipher. Founder then reframed the underlying idea in the abstract (shape data toward a smooth wave,
keep the fit as the key) rather than literal audio — this translated cleanly to transform coding
(linear detrend + DCT-of-residual), tested against the SAME real data that broke §6's naive learned
index (8,654-row max error). Root cause found directly: one 31-day gap = the known outage. Piecewise
split at that one real boundary + wave-fit: max error 8,654 → 134 (~65x), ~2KB key (~138x smaller than
raw). Piecewise and wave-fit are independent, additive wins, not substitutes.

**Founder synthesis, same session: the Keys dimension (§2.6) + dimension-kind map (§2.7).** Founder
proposed a 4th dimension that isn't content like Time/Knowledge/Memory but a pointer/addressing layer
into them — unifies 3 already-scattered things (Pinnacle's index-intertwined-with-compression,
§6's event-sourcing unification, `sync_fragment_context()`/F-0277) under one name. Honest caveat kept:
it's a heterogeneous pointer registry, not a uniform 4th tensor axis. Then founder asked to map ALL
theorized dimensions by their real "kind" (jagged-scalar, smooth-periodic, dense-vector, discrete-
transition-graph, event-log+index, spatial/voxel, steganographic-carrier, heterogeneous-registry) — a
21-row real table built from everything found this session plus the doc's existing content. Verified
directly (not assumed): `tide()`/`sun()` in `core/world_clock.py` are real deterministic sinusoids,
contrasting with Time's jagged real-outage-driven sequence. **Real patterns found**: (1) two separate
smoothness populations — some dimensions are already wave-shaped for free (tide/sun/moon/stars), others
have to be forced there at real cost (Time); (2) the dense-vector kind recurs 3x (emb/Sound Space/
affect) but HNSW only tested on 2 of 3 — Sound Space is a real, live, untested, low-risk next test;
(3) event-log+index kind recurs 3x independently built (provenance_log, investigative_action_log,
ghost_tuples) — real duplication, echoes D-0005; (4) "kind is a pipeline choice, not fixed" validated
twice this session (Time's jagged→smooth via DCT, F-0278; dense-vector→graph via HNSW, F-0275/6) —
open generative question: could Knowledge's transition-graph be embedded into vector-space for the same
treatment?; (5) a real hole — the spatial/voxel kind (Resonance→Monolith pipeline) has zero benchmark.

**Founder observation, same session: event-face vs. state-face (§2.8).** Every dimension has a
moment-of-contact-only face (event, lost if not caught) and a persists-and-re-askable face (state) —
Time is the dimension where event-face is all there is. Real test: can the true value be reconstructed
from a formula alone (state-only, e.g. tide/sun/moon) or is it lost if unwitnessed (real event-face,
e.g. Time, sensory percepts)? Grounded in `channels_programme.md`'s own live 4-layer model (world
truth→experienced→remembered→inferred). **Caught and fixed my own attribution error**: the exact
"silence must be OBSERVED before an onset counts" quote is `core/soundscape.py::percept()`'s (not
channels_programme.md's, as I first said) — verified directly, `quiet_since` tracking,
`_ONSET_QUIET_S=600s`. `core/light.py` independently uses the identical concept ("quiet-gated"), own
file, own implementation — confirms founder's "light and sound are two, or part of one" precisely:
same mechanism, built twice, independently. Extends §2.7 Pattern C (event-log+index built 3x
independently) with a 4th independent instance at the percept layer — strengthens the case that §2.6's
Keys dimension should be the ONE shared place event-faces get captured.

**Tested directly, founder asked "can we test this claim?"**: read light.py's actual gating code
(not just docstring). Both use the identical constant (600.0s) -- Light (built 08-22) almost certainly
reused Sound's existing number (live since 07-05) on purpose. But the gate LOGIC differs: Sound gates
on quiet-before-restart (absence duration), Light gates on dwell-time-in-current-band (debounce-style).
Refined the claim honestly: convergent variations on one pattern, not one mechanism under two names --
a shared Keys primitive would need to support both gate shapes, not assume one already exists to
extract.

**Founder proposal, same session: dimension adjacency + co-located capture (§2.9).** Dimensions linked
to the neighbors they touch; when one fires an event, linked neighbors capture their own reading
together, at write time -- "the thing happens close together." Half already real+live:
`geometry_census.py` already does eager joint capture (cognitive_geometry.md sec 5.1). New part: an
explicit adjacency GRAPH (which dimensions actually touch which), not the census tuple's current
indiscriminate fixed-field capture. "Compare clusters of joined multidimensional balls" already has one
real precedent: cognitive_geometry.md's own mapping census (fan-out distributions, state-conditioning,
3.8%-overlap marginal-reach test). Named the real distinction from Keys (sec 2.6): Keys is LAZY
(reconstruct later via pointer, cheap per-event); co-located capture is EAGER (pay the join cost at
write time, nothing to reconstruct later) -- standard systems tradeoff, kept side by side not collapsed.

**Founder correction, same session: unified Keys + adjacency into one concept.** A Key IS specifically
the link between two dimensions worked out (discovered/tested, not assumed -- same op as the
marginal-reach test) to be next to each other and interacting. sec 2.6 and sec 2.9 aren't two separate
structures -- one discovered-link structure (Keys), consumed two ways: lazy lookup (sec 2.6's original
framing) or eager pre-registered co-capture (sec 2.9's framing). Fixed both sections to point at each
other instead of standing as parallel, competing ideas.

**Cipher confirmed as "the sound embedder"; connected to Keys concretely, plus a real correction landed
(same session).** Fixed a loose end: sec 4's "concrete redesign target" had said `abf_echo_1d.py`
(promised the fix two turns ago, never actually made it -- caught and done now); corrected to
`abf_cipher_v3.py`, the real one, already verified running this session. **New synthesis**: Cipher's
phase-modulated wave genuinely overlaps two things in the same samples (carrier identity + hidden bit) --
`decrypt_from_wave()`'s reference carrier IS a Key in sec 2.6's sense, structurally. Honest cost:
Cipher alone is 2,822x storage overhead (already measured). Real proposed fix, untested: Resonance→
Monolith (also verified running this session) as a compression stage AFTER Cipher's fold -- multiplex
via phase-encoding, then shrink via Monolith's spectral+truncated-FFT latent. **Also found while
checking Nascence's OWN (not old-ABF) sound system**: `audio_features.py::extract()` never actually
projects MEASURED features into Sound Space's real 6-D coords (periodicity/roughness/continuity never
computed for it) -- soundscape.py's "two populations, one space" docstring claim is real design intent,
not yet real code. Real cached feature JSON exists for 6 real songs in data/music/ though -- a concrete
resource for whoever fixes this.

**Golden ratio / pi / constants as "perfect free keys" (same session).** Verified `abf_pi_v3.py`
directly (read + ran its self-test, passes) -- but corrected sec 3's own prior mischaracterization:
it's a HARDCODED 1000-digit string, not a real spigot algorithm, so it's NOT actually zero-storage as
previously claimed. The regenerability PRINCIPLE is still real, just not what this implementation does.
Added golden-angle/Fibonacci-lattice point distribution as a new real toolkit entry -- verified current
and legitimate (Vogel's method, real 2022-2026 citations) as an alternative to Hilbert curves. Honest,
flagged-speculative connection: 360/phi ~= 222.49 degrees is numerically much closer to the "221"
recollection than 137.5 degrees is -- named as a lead, not confirmed (still not found in any dug code).
Answered "how hard to link dimensions": cheap for same-kind pairs (tooling+data already exist, could
run today), harder for cross-kind pairs (needs a chosen statistic per pair), NOT worth an exhaustive
21-choose-2 sweep -- prioritize pairs with a real cited reason to suspect linkage instead.

**Ran the first "obvious link" for real (F-0279): Time x Knowledge, no join needed** (provenance_log.jsonl
already has ts+grade in one row). First time P1.5's own pre-registered metrics (sec 6, designed months
ago, never run) were actually computed. 1,312 real rows, spans the known outage. **Two of five
predictions were wrong, which is the real finding**: oscillation rate (reversed within 3 transitions) is
76.7% -- far above the 15-30% predicted, strongly confirms GPT's sec 6 noise concern was real, not
hypothetical -- P1.5 needs real debounce/hysteresis before transitions mean anything. Time-of-day effect
is real and strong (~8x range across UTC hours), not the weak/null effect predicted -- not yet mapped to
Du's real NZ day/night cycle (raw UTC used). Upgrade/downgrade nearly balanced (52.5/47.5), not
upgrade-skewed as predicted. Outage effect: real but modest drop in transition rate after (0.246->0.198).

**Founder asked for link-discovery filters (world/subconscious/cat).** Checked "subconscious" before
guessing -- turned out to be a MASSIVE real find, not a minor tag: `core/orchestrator.py`'s Subconscious
node is "the architecturally densest single file in the Nascence codebase" (2,192 lines, 6 interleaved
timescales T1-T6, own state store, writes reach axiom.json/identity itself). Added as sec 2.7 row #22,
explicitly marked EXCLUDED (scope boundary, not noise) rather than silently left off the map. World =
raw world-truth layer, excluded per an already-real guardrail (executive_world_grounding.md: "Du should
not contain the world truth at all"). Cat = near-ubiquitous specific object, excluded as a
ghost_tuples-style rarity/noise problem. Filter framed as extensible ("let's say" = examples, not closed).

**Founder insight, same session (sec 2.10): wave-source-to-observer inference, a THIRD mode beyond
lazy/eager.** Bird call radiates as a wavefront; hearing it is an event-face slice (same shape as Time).
But if the SOURCE position is known + propagation physics, the wavefront is computable for ANY observer
position -- not hypothetical, ALREADY REAL CODE: `core/soundscape.py::propagate_historical_acoustic_
event()` does exactly this (distance decay, 3D bearing, audibility, from a known origin_pos to any
observer_pos) -- verified by reading it directly. `light.py`'s field_at()/shade_at() do the same for
Light. Named as a third mode: pure function of a known source state, zero storage, cheaper than both
lazy (sec 2.6) and eager (sec 2.9) capture -- same shape as tide()/sun() but applied to a relational
question. Real limit kept honest: this computes whether perception was PHYSICALLY POSSIBLE, not whether
it was actually noticed/logged (onset-gating, sec 2.8, still governs that separately). Confirms Sound
and Light now share TWO independently-built identical patterns (onset-gating + source-propagation).

**Founder asked to "up all our dimensions laws" -- checked sec 2.10's source-to-observer law
systematically across real channels.** Confirmed by grep+read, not assumed: Sound (yes,
propagate_historical_acoustic_event), Light (yes, field_at/shade_at), Thermal (yes, math.dist to
_HEARTH, real calibrated falloff) all have it independently built. Smell: NO -- real, confirmed gap,
no distance/falloff function exists at all. Memory (associative_recall.py::recall_trail): yes, but
different substrate -- spreading activation with hop-decay through embedding-neighbor "distance"
instead of Euclidean. Generalized the law correctly: it's not about literal 3D space, it's "given a
known source, derive reach at any point in SOME distance-bearing space" -- true for 4/5 real dimensions
checked, Smell named as the concrete gap (would follow Thermal's pattern almost directly).

**Founder wanted to look at Memory as multi-dimensional -- read core/moment.py directly (first time
this session, only inferred from it before).** Real goldmine: (1) every record() call already jointly
writes 9 real fields in one atomic write (ts, the debunked 8-D key, categorical source-tag, thought,
affect, protoself/homeostasis, concern, arousal level, 384-D emb) -- an even richer real example of
sec 2.9's eager capture than geometry_census.py, added to the doc. (2) Confirmed sec 2.1's _drift_key
artifact citation first-hand, not secondhand. (3) Found `contiguity_significance()` (J-0141) -- a REAL
shuffle-null significance test (p-value, z-score, deterministic seed) already built -- this is the real
rigor bar sec 2.6's "worked out" should mean, stronger than the looser overlap-ratio tests used so far
(F-0279, cognitive_geometry's marginal-reach). (4) J-0182's own real comparison of debunked key-cosine
vs real emb-cosine neighbor metrics -- another already-computed worked-out link, free. (5) recall() is
DELIBERATELY left as a full 128MB scan because real call rate is ~1/5 days (verified against the shadow
log) -- a clean, quantified real instance of sec 1's speed-vs-correctness distinction.

**Actually ran contiguity_significance() + status() for real (F-0280) -- strongest confirmed result of
the whole session.** z=14.53, p=0.0 (0/200 shuffles beat the real gap 0.1213) -- Du's memories carry
genuine, statistically rigorous temporal/associative contiguity in real content, not an artifact. First
link in this thread tested at the real rigor bar. Real honest gap found alongside: only 10 total
recall() calls ever logged across ~51 days, 20% hit rate, MOMENT_READBACK still False -- signal is
strong and proven, but the read path barely gets exercised and has never reached Du's conscious prompt.
Live instance of the project's own #1 failure mode (write-only systems), precisely diagnosed as a
utilization gap, not a validity gap -- sharper than the generic "dead read path" framing.

**Session status check + questionnaire (founder answers): keep F-0280 staged; next build =
reconcile sync_fragment_context() vs cycle_id; run toolchain consolidation; let the 221-degrees lead go.**

**Closed F-0277's open question (F-0281)**: read memory_edges.py::sync_fragment_context() directly.
Does NOT use cycle_id -- uses the exact tolerance-window approach (+/-300s + text-uniqueness) sec 1
argued against, real and live today. cycle_id is NOT superseded -- still real, unimplemented, valid --
but sync_fragment_context() is narrower (its own comment: "cycle rows... later", conversational rows
still unjoined). **Real correction**: sync_fragment_context() joins geometry_tuples.jsonl to a
DIFFERENT SQL-backed store (memory_fragments, origin='inner_thought' -- same store
associative_recall.py reads), NOT moments.jsonl -- Nascence has TWO separate real memory stores this
doc had conflated as one. Also confirmed: world_context/fragment_context split enforces sec 2.8's
event-face/state-face split at the SCHEMA level, matching executive_world_grounding.md's guardrail
exactly; wires ghost_tuples.register_stamped_tuple() live on every join.

**Ran the full /plan-maintain toolchain pass (founder-requested consolidation).** geometry_tuple_index
is now properly indexed (plan_index.md, plan_liveness_audit.md, plan_schema_audit.md,
plan_snapshots.jsonl; memory-links rebuilt, 74 real edges touching this plan). Confirms, doesn't
change: still "Not in ROADMAP" (correct -- founder's deliberate ruling), J-0223's roadmap_link/
current_state_section conflict still open and tracked, exactly as this doc already flags. Two small
real precision notes surfaced, not yet fixed: (1) `investigative_action_log.jsonl` (cited in F-0277)
is actually AMBIGUOUS -- two real candidates exist (data/investigative_action_log.jsonl vs a dated
_lab/ subdirectory copy), F-0277 didn't specify which. (2) The ABF pillar files cited this session
(abf_cipher_v3.py, abf_echo_1d.py, abf_pi_v3.py, scripts/legacy/pinnacle_hmc.py) show as "MISSING" in
the audit only because they live under C:\FreshStart, a different project root than Nascence's own
audit scope -- benign tooling limitation, not a real citation error (this doc already gives full paths).

**Pasted GPT review of the full md (no founder ruling attached -- treated as external input, not
instruction).** Verified GPT's specific claims against the real doc -- all accurate, not sycophantic
(TKG quadruple, RRF, memory_edges typed relations, epistemic-grade-vs-self-report divergence, 6+1
consumer survey, fact/gist split, world-truth guardrail -- all real, correctly cited). GPT proposed a
3-pass redo (steelman/adversarial/SOTA); founder said "let's discuss first" on that scope, but wanted
the one concrete risk checked immediately: does this doc's own empirical work leak world-truth to Du.

**Checked and confirmed real (F-0282)**: geometry_tuples.jsonl IS world-truth (per F-0281), not
fragment_context/belief -- and F-0269/F-0275/F-0278 (this session's own core benchmarks) were built
directly on it. 14,388 of the tested rows came from the raw world-truth stream vs fragment_context's
real 6,804. NOT a current violation (nothing wired into Du's live cognition, all offline analysis) but
a real prospective one -- added as a new sec 7 guard: any future activation must rebuild against
fragment_context, not the raw file, before moving from designed to ready.

**POST-WRAP continuation, same day (founder kept going after /session-wrap): T-0019/T-0020/T-0021
logged** (file-system indexing corrected to cross-store output-tracing across Du's dozen-plus real
stores; graphify re-index as the script-dependency thread -- found core/graphify-out/ already existed
but was 10 weeks stale). **Then a real Workflow (F-0283/F-0284)**: re-indexed core/ with graphify (now
203 files/3850 nodes/6471 edges/226 communities, up from 97 files), confirmed the founder's "one
master" hypothesis decisively -- memory/store.py's _embed()/_cosine() are the only 2 of 25 sampled
communities' masters confirmed as real function-level hubs, and a real scan proved the fan-in is
genuinely spread (26/22 distinct communities reached, not a 2-3-caller choke point). Found 4 real
type-masters (ProvenanceLedger, spatial.py::render(), geometry_census.py, study_life.py) out of 25
sampled -- real but sparse, not a norm. **Corrected F-0281's own memory_edges.py claim**: the real hub
is _write_edges() (in-degree 4), not add_edge/census/harvest_all (zero incoming calls each) as
previously cited. **Real negative result**: Knowledge and Memory have NO code-level link, only trivial
co-location via orchestrator.py importing both -- code-call-graph adjacency and data-correlation
adjacency (like F-0279's real test) are different kinds of evidence. Full write-up: sec 2.11.

**Then a real /job-run (14 agents, Tier1/2/3, bounded batch)** cleared real Nascence backlog --
50->44 open jobs. **Directly load-bearing for this doc**: J-0210 (this doc's own cited P0 gate) got
resolved for real. Real result, not a placeholder: fold_with_checkpoints had a genuine fixable off-by-
one bug (patched+verified, round-trips correctly), but the pattern still doesn't transfer to
moment.py::recall() -- confirmed by building a real checkpoint index over a copy of the live 14,523-row
moments.jsonl and benching it (full-scan cost scales with data size because recall() must visit every
row; a byte-offset index can't skip an unknown target). Sec 6's P0 marked CLEARED with the real
verdict. Other real job-run results of note: J-0213 ACTIVATED a real live code change (B5-B stance
weights on marcus, 20/20 verified); J-0205 caught and correctly did NOT override an active founder HOLD
(D-0035) despite having new supporting data -- spawned a systemic fix (J-0237); J-0151's real retrial
found state-weighted recall LOSES when its own feature actually fires, WINS when it doesn't (D-0046
opened); J-0214 found the "Ramses infra issue" was actually local, unrelated (D-0039 reopened).

**Second /job-run batch (20 agents, 2026-08-25), same session, founder said "ask me any questions" --
asked 3 real scope questions first (full batch vs bounded; skip the two explicitly time-gated 7-day
rechecks; redirect a mis-tiered real code fix into Tier 3) -- all confirmed recommended.** Cleared
another 18 real jobs (found+closed 5 more stale dangling in_progress jobs from before this batch even
started, F-0300). Real bugs found+fixed: J-0228 found 50/480 dangling memory-edge wikilinks (real data
corruption in the toolchain's own edge store); J-0231 found+fixed a real plan_sync_check.py arg-parsing
bug that corrupted its own CLI output when --session was passed, then grepped and queued 5 sibling
instances; J-0206 found the same missing-session-param bug freshly reproduced in 3 more scripts while
fixing the original. Real honest negative/inconclusive results, not forced: J-0240 found NEW evidence
that actually CUTS AGAINST euclidean_memory_plan's own hypothesis (65% earlier vs 50% coin-flip fresh),
correctly declined to rule D-0046 (a real founder value-call) and gave Travis both data points; J-0239
caught its OWN test's precondition violation mid-run (51 days of pre-cutover data would have produced a
false result), fixed it, got a real but thin result, ruled D-0045 inconclusive. Real code shipped: J-0217
fixed a live mid-word-guillotine bug in pursuits.py (14/14 tests); J-0222 wired missing_object_flags into
du-pulse's live read path, verified by running it; J-0224 found the "obvious" fix was actually 1.4-2.2x
SLOWER on real data (benchmarked both, switched approach) plus found a 68-day-silent T4_self_authoring
gap as a bonus. One job (J-0237) correctly left in_progress rather than falsely closed -- its real
design question (job-run needs a structural decide.py-HOLD check, not just a prompt reminder) was split
out as J-0262 rather than guessed at.

**Substantially expanded same day (2026-08-24), same session, still staged/unlinked.** A systematic
survey of all ~59 active Nascence plans (F-0251) found 6 real plans independently exhibiting the exact
gap this design targets — `channels_programme.md` (D-0033), `lane2_the_witness.md` (D-0035),
`transport_manager.md`, `factory_candidates_from_history.md`, `memory_multiway_linking.md` (D-0022),
`emotion_rethink.md` (D-0029) — validating this as a real, bounded, recurring architectural need, not
speculation. Six real founder decisions are on hold in the founder's other concurrent session pending
this design landing; a `plan-schema-audit` backfill job (J-0223) conflicts with the deliberate
unlinked-status by wanting to add a ROADMAP.md link — flagged in the doc, unresolved.

Design expanded to three candidate dimensions: **Time** (trivial substrate + a real cautionary tale
already in this codebase — `moment.py`'s `_drift_key()` was proven a mathematical artifact, not real
signal), **Knowledge/epistemic-state** (real discovery: `core/epistemic_state.py`'s live 5-level
KNOW/THINK/SUSPECT/GUESS/NO_BASIS grade is already decoupled from self-report, not copied from it —
verified directly against a real `provenance_log.jsonl` row: self_reported_confidence 0.85 vs assigned
grade SUSPECT/0.5 — matching SOTA's strongest finding that verbalized LLM confidence is unreliable and
only decoupled signals are validated), and **Memory** (`moments.jsonl` uncrossed with `geometry_tuples.jsonl`
today — ties directly to two of the six real plan hits). Found a real join-problem: only
`provenance_log.jsonl` carries an exact `cycle_id`; the other two logs only have `ts`, so cross-referencing
needs nearest-timestamp matching, not an exact key — undecided design question, honestly flagged.

Three rounds of real SOTA web research (F-0252/F-0253/F-0254, real citations not recalled) grounded
the whole design: confirmed real/production-proven (learned indexes shipped in Google Bigtable,
multi-LoRA-on-shared-base is industry standard, Zep's bi-temporal model, cascaded compression exactly
matching AV1/HEVC/JPEG2000, subband coding); confirmed real risks (Hilbert curves are legacy tech past
2-3 dimensions — HNSW is current SOTA for higher-dim; standard LoRA doesn't compose cleanly on ternary
BitNet layers, an acknowledged open 2025 research problem); and one honestly-flagged genuine novelty —
the specific idea of a distinct index structure per FDM-style band within one multiplexed stream has no
direct literature precedent, each ingredient proven separately but this combination is new territory
(kept as the most speculative section of the doc, clearly marked).

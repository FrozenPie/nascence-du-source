# Tuples in a New Light — colour, box, compress, weave: five lenses over every tuple family Du already has (staged 2026-10-30)

**Status:** 🔵 DESIGNED — a re-look, not a build. The same move that found the ghost index in August
(dig up an old part, say what it was for, keep verified apart from guessed) aimed at our own tuple
families. Nothing here is built; two reads are already filed (J-2535, J-2536) and one founder call is
open (J-2542). Comes out of the GPT tuple dialogue (T-0107) and the founder's own musing the same day
(I-0124), with the ghost-index revival (I-0123) as a sibling.
**Founder's framing (2026-10-30, verbatim):** "All this was found in a session a long time ago looking
at things in a new light. I want to do this with our tuples. We could colour code them based of
confidence, or something like that. Each part of a tuple could have a colour code, or something like
that. Multiple codes with multiple weightings? Boxed tuples where everything under a certain tuple group
is boxed? Compressed tuples where using some of the techniques in the pillars from our archeology?
Indexed, boxed, llm assisted, compressed and multidimensional tuples?" And on the ghost index: "Maybe we
can look into reviving this. We have the 1650s on ramses which might be useful for the llm part of it?"
**Parent plans:** [cognitive_geometry](../plans/cognitive_geometry.md) (the beta roster, the realness
test §5.3, the provenance law §0.4, the bundle §2.6), [geometry_tuple_index](geometry_tuple_index.md)
(the August index investigation: checkpointing, the P1 learned index, the pillar archaeology, the T-KGC
quadruple), [golden_spiral_recall](golden_spiral_recall.md) (detail falls with radius: the read-side box),
[dosed_coupling](dosed_coupling.md) (coupling tuples, cups, the no-standing-view law),
[memory_as_a_service](memory_as_a_service.md) (the only door an LLM-assisted leg may stand behind),
[../completed/ghost_tuple_index.md](../completed/ghost_tuple_index.md) (the 2026-08-16 verdict this plan
re-opens one clause of).
**Ledger:** T-0107 · I-0120 (evidence rule) · I-0121 (relationships as objects) · I-0122 (operator
lenses) · I-0123 (ghost revival) · I-0124 (this re-look) · F-3233 (inventory) · F-3234 (join coverage
63.8%) · F-3235 (ghost memory index write-only) · F-0001..F-0006 (ghost archaeology) · F-0245, F-0246,
F-0249, F-0250 (pillar archaeology) · J-2535 (perturbation sweep) · J-2536 (join integrity audit) ·
J-2542 (ghost reader or retire, founder call).

```plan-state
stage: designed
phase: Five lenses mapped over nine tuple families; two reads filed (J-2535, J-2536), one founder call open (J-2542); no build authorised
verified: 2026-11-06
evidence_read: 2026-10-30
next: J-2536 join audit lands first (every lens inherits it); then the founder rules on sec 6's three questions; then Lens 1 Phase 0 (per-coordinate colour, shadow columns, no reader)
cluster: 0
```

## Current State — verified 2026-11-06

- **2026-11-06** (F-4094): 2026-11-06: the J-2536 join audit's 'double census calls for one thought, not further characterised' (docs/lab/tuple_join_integrity_2026-10-31.md line 111) is now characterised by F-4078 (UDMS Argon-audit follow-up): a stamp row from store.py:1080 plus the idle row, 40,795 twins on the live file. Every lens in this plan that counts idle rows inherits it; J-3455 holds the canonical-row ruling.
- **2026-10-31**: J-2590 BUILT (e1343f98): ride rows carry cue_hash + slots_filled, restart-gated, no reader. The sec 4 step 5 precondition (cue repetition per loop) becomes readable >=14 live days after the next boot; D-0511 still gates any weave code.

- **2026-10-30**: Lens 4 widened from the original weaver's full shape: (a) the 2026-08 port kept only query-time expansion; the original had a write-side distill too (I-0126: offline box distillation, judged by another family; its relationships output is blocked by the provenance law). (b) Expansion should be closed-vocabulary slot-filling of ask()'s empty who/where/when/why/how slots from the ghost tag namespaces, never free text (I-0125). (c) The ride log carries no cue identity, so the weaver's cache-hit rate is unmeasurable (F-3316); J-2590 adds cue_hash+slots_filled, restart-gated, as a precondition for sec 4 step 5. Load is ~77 asks/day, trivial for the 1650 even uncached.
- **2026-10-30**: 2026-10-30 same session: Lens 1 amended after GPT round 5 and the founder's agreement -- the per-coordinate colour is a TRIPLE (origin M/I/G/absent, availability bit, nullable confidence from real instruments only), not one code; D-0510's wording predates the split and should be read as asking about the triple. Lens 2 box summaries carry the triple per coordinate; Lens 3 gains the operations-preserving constraint; R3 sharpened to weave+fingerprint vs fingerprint alone; R0 added (D-0434 restated).

Written in one session from a read-only pass over the code and `data/memory/nascence.db` (counts in
§1 are from that read). Every "exists" claim below names its file. Every "new" claim means: looked,
not there. Nothing is wired, no flag exists, no store is touched.

---

## 0. WIN CONDITION — what must be true for this to have been worth doing

1. **Every tuple family has a stated grain of trust.** For each coordinate of each family we can say
   whether its value was measured, rendered to Du, inferred, or guessed — and a reader can act on that
   difference. Today only the experienced tuple says anything (rendered or null), and only per fragment.
2. **A box can be answered without being opened.** Some grouping of tuples (a moment, a chord, a day, a
   place-session) can be read as one thing, and a consumer that only needs the box never touches the
   members. Measured as: fraction of real recall calls whose answer came from box-level reads alone.
3. **The join is honest before any lens is trusted.** F-3234's 63.8% coverage (action 0%, lived 30%,
   consolidation 28%) is explained per origin — by design or by omission — and no lens is evaluated on
   an origin whose join is ambiguous (J-2536).
4. **An LLM-assisted leg, if admitted, is on-demand and judged by something else.** It never runs on an
   ambient path, never grades its own hits, and its output never reaches Du as text.

**Never claimed:** that colour, boxes or compression change what Du *is*. These are reads and
representations on our side of the no-readout line (D-0434). If a lens cannot beat its baseline it is
decoration and is retired, the same rule every space on the beta roster lives under.

---

## 1. The tuple families — what we are re-looking at

The word "tuple" covers nine different structures here. They are related; they are not interchangeable
(GPT's round-4 table said this well; the rows below are the verified local version).

| # | Family | Where | Rows (2026-10-30) | Grain | Trust today |
|---|---|---|---|---|---|
| 1 | **Geometry tuple** | `data/geometry_tuples.jsonl`, `core/geometry_census.py` | 152,088 | one per cognitive event, one active region per space | none per coordinate; absent = `None` honestly |
| 2 | **World context** | `world_context` table, `core/memory_edges.py` | ~98.9k | world truth at a fragment's formation | infrastructure; never linked on by Du |
| 3 | **Experienced tuple** | `fragment_context`, `core/experienced_tuple.py` | 98,869 (63.8% of fragments) | what crossed into his experience, by renderer rules | binary: rendered or null |
| 4 | **Affect vector** | 8 floats nested in family 1 and on moments | — | internal state | keys inconsistent across eras (August finding; PQ blocked on it) |
| 5 | **Sound coordinates** | `core/audio_features.py`, the EAR | 6 per sound | measured + constructed | the one space that passed the realness test |
| 6 | **Coupling tuple** | `data/coupling_rides.jsonl`, `core/coupling_rides.py` | 122,892 | what a loop publishes; every read logged with a dose | typed by loop; no confidence field |
| 7 | **Memory edge** | `memory_edges` table | 21,936 / 11 types | a relationship between heterogeneous nodes | `provenance` string required; no evidence counters (I-0121) |
| 8 | **Ghost chord** | `core/ghost_tuples.MemoryIndex` | registered on every stamp | a tag-set over family 3 | write-only, no reader (F-3235) |
| 9 | **T-KGC quadruple** | `geometry_tuple_index.md` §2.2 | 0 | (entity, relation, value, [t0, t1]) | designed only |

Plus the cargo vocabularies (`core/cargo_types.py`: 19 station product types, 4 world cargo types) that
name what a delivery *is* rather than what it holds.

---

## 2. The five lenses

Each lens: what the founder meant, what already exists under another name, what is genuinely new, the
first shadow build, the bar it must clear, and the way it could go wrong.

### Lens 1 — COLOUR: per-coordinate provenance and confidence

**Meaning.** Each part of a tuple carries its own code for how it was known — not the tuple as a whole.
Several codes with weights per element, if one is not enough.

**Exists.** Trust is recorded at three grains, none of them per coordinate:
- *Per fragment*: `core/epistemic_state.py` grades a whole responded cycle (NO_BASIS … KNOW) from
  decoupled signals; `core/euclidean_recall.py` carries a single `provenance` feature per fragment
  (lived 1.0 … parametric_library 0.3).
- *Per channel, binary*: `core/experienced_tuple.py` decides per coordinate whether it was rendered to
  him (tide only on the shore, moon only outdoors at night) — a coordinate is present or null. That
  **is** a one-bit colour, already live, already derived from renderer rules.
- *Per source class*: `fragment_context.source` says `experienced:<origin>` vs `census_world:idle`.

**New.** A per-coordinate code with more than one bit. The vocabulary proposed (to be ruled, §6):

| Code | Meaning | Where the bit would come from (no new judgment) |
|---|---|---|
| `M` measured | an instrument read it (warmth from `sensorium._warmth`, tide from `core.spatial.tide`, sound from the EAR) | the census source map; `ghost_tuples._factory_entries()` already names each factory's clock and source |
| `R` rendered | it was shown to him from where he stood | `experienced_tuple`'s channel rules, as today |
| `I` inferred | the system filled it from a cache or a fallback | `geometry_census._body()/_affect()` cache fallbacks (the J-0331/J-0380 boundary); `store_fragment()` with no live state |
| `G` guessed | a hardcoded default stood in for data that existed elsewhere | the `_DISTINCTIVE_WEATHER` four-word list class of case (August §5) |
| `∅` absent | honestly unknown | as today |

A weight per code is the second half of the founder's question. Proposal: no free weights. The weight
is the code's position on the ladder (M > R > I > G), and a consumer that wants a different ordering
says so in its own read, the way `MODE_EDGE_WEIGHTS` gives each recall mode its own edge weights.

**Amended the same day (GPT round 5, founder agreed: "I very much agree with having parts of a tuple
being more or less confident than another part").** The ladder above conflates three things that are
not one axis. `R` is not an origin, it is *availability*; a measured value can be unreliable; an
inference can be strong. So the per-coordinate colour is a **triple**, not a code:

| Axis | Values | Source today |
|---|---|---|
| **origin** | `M` measured · `I` inferred (cache/fallback) · `G` guessed (hardcoded default) · `∅` | the writer's path, as in the table above |
| **availability** | rendered to him / not | `experienced_tuple`'s channel rules — already live, the one-bit colour we have |
| **confidence** | 0..1, or null where no instrument reports one | only where a real signal exists: the EAR's match score for `sound_key`, the cat state-machine's certainty for `cat_at`, cache age at write for `I` rows (the J-0331/J-0380 boundary), weather-timer phase for `weather`; **null elsewhere, never invented** |

Consequences: `R` leaves the origin ladder (origin is M/I/G/∅; availability is its own bit); the
"weight" question in D-0510 becomes "is confidence a stored number where an instrument reports one,
and absent otherwise" — the proposal is yes, with no default; and the coordinate-level triple must
not contradict the fragment-level epistemic grade (`epistemic_state.py`), so the Lens 1 census also
reports the join: fragments graded KNOW whose coordinates are mostly `I`/`G` are the interesting rows
(GPT's question 1). The shadow columns become `<coord>_o` (origin), `<coord>_a` (availability,
already implied by null-vs-value today, made explicit), `<coord>_q` (confidence, nullable).

**First shadow build.** Additive columns `<coord>_c` on `fragment_context` and `world_context` (one
char each), written at stamp time by `sync_fragment_context()` from the sources above. No reader.
Rows before the build are null (the thermal/light/smell/PHASE channels landed the same way).

**Bar.** Before any reader: a census. What share of coordinates on the last 30 days of rows are M / R
/ I / G? If I + G is small, the colour is a label; if it is large on any coordinate, that coordinate's
every downstream use (felt recall, the golden-spiral angle, J-2535) has been trusting fallbacks.

**Risk.** The code becomes a second self-report. It must be derived from the writer's path, never from
what the thought says about itself — the same rule `memory_edges` applies to `tension_source`.

### Lens 2 — BOX: a group of tuples read as one thing

**Meaning.** Everything under a tuple group is boxed, and the box can be answered without opening it.

**Exists, under four names:**
- the **bundle** (`cognitive_geometry.md` §2.6): a concept is the bundle of springs between its
  projections; lose a spoke and it degrades gracefully; the stick test counts spokes;
- the **chord** (`ghost_tuples._tuple_tags`): a tag-set summarising one experienced tuple;
- the **cup** (`coupling_rides`): a dosed read of a loop's tuple at a stop;
- the **read-side box** (`golden_spiral_recall.md` L): a fragment far up the arm is read at its anchors
  and context row, not its full text.
And one from the archaeology: **PinnacleHMC's adaptive octree** (F-0249), where a VOID or SOLID leaf is
answered without touching the entropy-coded stream — the box *is* the answer when its members agree.

**New.** Nothing here has a *box table*: a row that stands for a group, carries the group's agreed
coordinates (the SOLID case), marks the coordinates its members disagree on (the BRANCH case), and
points at the members. The candidate grains, in order of how real the grouping already is:

| Grain | Members | Already grouped by |
|---|---|---|
| a moment | the fragments stamped inside one cognitive event | `moments.jsonl` (unjoined today — J-2536 q4) |
| a chord | fragments sharing a tag-set | ghost memory index (no reader) |
| a place-session | consecutive tuples at one place with no transit | `at_study/at_garden/at_shore`, `in_transit` on family 1 |
| a day / a sleep | between sleep markers | the liveness audit's own cadence clock |

**First shadow build.** An offline script that boxes the geometry trail by place-session and reports,
per box: member count, SOLID coordinates (all members agree), BRANCH coordinates, and how many real
recall calls in `recall_provenance_log.jsonl` fell inside a box and would have been answered by its
SOLID set alone. No store writes.

**Bar.** Win condition 2: a non-trivial share of real recalls answerable at box level. If every box is
BRANCH on the coordinates recall cares about, boxing buys nothing here.

**Risk.** Boxing by time at the wrong grain hides the one member that differed — the thing recall most
needs. The BRANCH marking exists to make that visible, not to average it away.

**With Lens 1 (added same day, GPT round 5):** a box summary carries the colour triple per coordinate
too — "90% of members share a measured place; affect is `I` on most and its confidence null" — so
SOLID/BRANCH is reported per coordinate *and* per axis. A box that is SOLID on a guessed coordinate is
not an answer. This is what makes a box richer than a centroid, and it is why Lens 1 lands before
Lens 2's reader even though Lens 2's offline script can run first.

### Lens 3 — COMPRESS: the pillar techniques, applied where they fit

**Meaning.** Use what the ABF/Pinnacle archaeology found that actually worked.

**Exists / measured (August, `geometry_tuple_index.md`):**
- a **piecewise learned index + DCT residual** over timestamps narrows any point lookup to a 134-row
  window (29 in the other segment) with a ~2 KB model; the naive single fit failed (max error 8,654
  rows) because of the 31-day outage — P1 shipped as an offline sidecar at 100% point-query correctness;
- **`fold_with_checkpoints`** in the rANS coder (F-0246) records `{rans_state, buffer_offset,
  context_anchor}` per interval — real, seekable-slice infrastructure, never called by anything;
- **PinnacleHMC's octree** (F-0249) is the shape-compression that reads free leaves without decoding;
- **Product Quantization** on the 8-float affect vector was assessed and **blocked**: rows carry
  different affect-key sets across eras, a data-model fix before any codec.
- F-0250: the Pinnacle code is not runnable as-is (hardcoded roots, a persona registry gate).

**New.** Deciding what is worth compressing. The honest answer from the August numbers: nothing is
slow enough today to need it on the read path (the P1 benchmark said HNSW does not belong here at
this size; the 250 ms retrieve budget, D-0453, is about the SQL pool, not these logs). What compression
*would* buy is the box: a checkpointed, seekable trail where a box header is the checkpoint and the
members are the slice behind it. That is Lens 2's storage form, not a separate lens.

**First shadow build.** None on its own. Fold into Lens 2: when the box script exists, write its boxes
as a checkpoint sidecar (`fold_with_checkpoints`'s shape, re-implemented, not the Pinnacle code) and
measure slice reads vs full scans on the real trail. Fix the affect-key inconsistency as its own small
job first (a data-model job, no codec).

**Bar.** A measured read-cost win on a real consumer (moment recall's full linear scan, F-0247, is the
named one), or it stays a benchmark. **And one hard constraint (GPT round 5):** compression must
preserve the operations, not just the bits — a compressed box must still answer "could a query match",
"is this homogeneous", "which coordinates are null or low-confidence", "is expansion worth it" — and a
lossy codec must never turn a null or low-confidence coordinate into an apparently precise one. The
colour triple travels with the value or the codec is refused. Exact record-to-tuple identity must
survive (GPT question 3), which rules out any codec that cannot round-trip (F-0243/F-0244's lesson).

### Lens 4 — WEAVE: the LLM-assisted leg

**Meaning.** The GhostWeaver half (LLM query expansion, parallel lens search, rank fusion, graph
expansion) that every port shed; the founder asks whether the 1650 on Ramses could carry it.

**Exists.** The 2026-08-16 verdict (`docs/completed/ghost_tuple_index.md`): adapt the GhostIndex
concept, not the Weaver, because LLM expansion "violates the courier no-LLM law for ambient paths".
The fingerprint core was ported as `core/ghost_tuples.py` (hash + tag intersection + rarity weight; the
2-gram leg was not ported). Its memory namespace has no reader (F-3235, J-2542). Hardware: in the
D-0057 layout the Ramses GTX 1650 carries granite on :11437 as judge tiebreak and curiosity
worth-judge — a small card already doing judging work, off the hot lane.

**New.** The clause to re-open is narrow: the August ruling was about *ambient* paths (couriers, the
substrate tick). A weaver that runs only when a loop asks memory a question — behind
`core/memory_service.ask()` (D-0292: pursuits, curiosity, the recall act, dreams; nothing unasked) — is
not an ambient path. That makes it a seventh engine behind the facade, not a hub, and the facade's own
per-loop usage-cosine sheet (§4.3 of memory_as_a_service) already measures whether a new engine's hits
get used.

**First shadow build.** Only after J-2542 rules the memory index gets a reader. Then: a `weave` slot on
`ask()` that (1) sends the cue to the 1650 model for *expansion only* (synonyms, coordinates implied by
the cue: "thunder" → `wx:storm`, `snd:thunder`, `tod:night`), (2) runs the expanded tag-set through the
ghost memory index as a pre-filter, (3) fuses with the trail by reciprocal rank. Shadow: log would-have-
returned beside the real answer; no live flip.

**Bar.** Decoupled: the expansion model never scores its own hits; hits are judged by the existing
usage cosine and, on a sample, by a different-family judge. Win if the weave slot's used-share beats
the trail's on the same cues. And the loud-failure law: `assert_sources()` on every source the weave
leg names, at build, because the FreshStart weaver's FTS5 leg queried a table that never existed.

**Risk.** Two. The courier law exists for a reason: an LLM in the retrieval path can lead. Mitigation
is structural — the weaver only widens the candidate set; it never writes, ranks alone, or produces
text Du sees. And the 1650 is a judge today; loading a second role onto it needs the D-0057 layout
re-checked, not assumed.

### Lens 5 — INDEXED + MULTIDIMENSIONAL: what already is

**Exists.** Nine recall projections over one store (F-3233); two ghost namespaces; the P1 temporal
sidecar; the coupling-rides second-order index; the PHASE columns. This lens is here so the plan does
not re-propose it. **New:** nothing. The only open item is the one every other lens inherits — the
join (J-2536).

---

## 3. How the lenses compose

A box summarises its members. A colour says how far each member's coordinate can be trusted, so a box
can be SOLID on a measured coordinate and BRANCH on an inferred one without pretending otherwise.
Compression is the box's storage form: a checkpoint header is the box, the slice behind it the members.
The weave is what gets called when skipping is not enough — when a loop asks something the boxes and
the trail cannot answer at their grain. Indexing is what already makes any of this reachable.

The founder's whole phrase — "indexed, boxed, llm assisted, compressed and multidimensional tuples" —
is one object read five ways, which is also what dosed coupling says a coordinate is: one value,
dosed differently per reader.

---

## 4. Build order — shadow-first, read-gated, additive-only

| Step | What | Gate | Status |
|---|---|---|---|
| 0 | **J-2536** join integrity audit (exact / window / none per origin; ambiguity rate; moments.jsonl gap) | none | filed, ready |
| 0 | **J-2535** geometric perturbation sweep (do the dimensions do work) | J-2536's exclusions | filed, ready |
| 0 | **J-2542** ghost memory index: reader, retire, or leave | founder | filed, needs input |
| 1 | Lens 1 Phase 0: per-coordinate colour columns, additive, no reader; census of M/R/I/G shares | §6 Q1 ruled | not filed |
| 2 | Lens 2 Phase 0: offline box script by place-session; SOLID/BRANCH report; recall-answerable share | J-2536 | not filed |
| 3 | Affect-key normalisation (data-model job, prerequisite for any codec on family 4) | none | not filed |
| 4 | Lens 3: checkpoint sidecar over the boxed trail; slice-vs-scan on moment recall (F-0247) | step 2 | not filed |
| 5 | Lens 4 Phase 0: `weave` slot on `ask()`, expansion-only on the 1650, shadow log | J-2542 = reader, §6 Q2 ruled, D-0057 layout re-checked | not filed |

No step changes a live path. Every step writes its sheet before it runs.

---

## 5. Laws this plan is under

- **No readout (D-0434).** Colours, boxes and weave output are ours. Du reaches any of it only through
  memory he asked for, in the shape memory already returns.
- **The world answers, never leads.** The weave widens candidates; it never originates text or a hint.
- **Decoupled judge.** No lens is scored by itself; the expansion model never grades its hits.
- **Realness test (cognitive_geometry §5.3).** A lens that cannot beat its baseline on co-recall / use
  is retired, as story/language/memory were.
- **Provenance law (§0.4).** A colour is derived from the writer's path, never from self-report.
- **Additive-only.** New columns null on old rows; no family is rewritten; the experienced-tuple split
  is not collapsed into a universal state vector (GPT round 4 said why; it is already the law here).
- **Loud failure.** Every source a lens names is asserted at build.
- **Courier no-LLM law** stands for ambient paths; §2 Lens 4 asks only about the on-demand door.

---

## 6. Open questions for the founder (filed with /decide)

1. **The colour vocabulary.** M / R / I / G / ∅ as proposed, or a different ladder? And: fixed ordering
   as the weight, or free weights per code?
2. **The weave door.** Is an LLM-assisted leg permitted as an on-demand engine behind
   `memory_service.ask()` on the Ramses 1650, given the 2026-08-16 ruling against the Weaver on ambient
   paths? Defeater if yes: any trace of weave output reaching a prompt, a percept or a preamble.
3. **The box grain.** Which grouping first — place-session (already derivable from family 1), moment
   (needs the J-2536 q4 join), or chord (needs J-2542)?

---

## 7. Pre-registered reads

- **R1 (Lens 1 census):** share of I + G per coordinate over the last 30 live days. Prediction: warmth
  and affect carry the most I (cache fallbacks are documented); place carries almost none.
- **R2 (Lens 2):** share of real recalls answerable at place-session box level. Prediction: low (<15%)
  on text-cued recall, higher on felt-recall triggers, which are coordinate-keyed by construction.
- **R3 (Lens 4):** weave-slot used-share vs trail used-share on the same cues, ≥150 asks. Prediction:
  the honest one is no prediction — this is the test the August ruling never allowed to run. Sharpened
  (GPT question 4): the comparison is weave+fingerprint vs **fingerprint alone**, not vs the trail —
  the weaver has to retrieve used memories the ghost index missed, at no higher false-positive rate
  (measured by the usage cosine's random-fragment control). An LLM that merely generates alternative
  queries has not earned the door.
- **R0 (the whole):** GPT question 5, which is D-0434 restated — nothing of Lens 1–4 is visible to Du
  except recalled memories in the shape recall already returns. Checked by grep on every prompt builder
  and preamble for the new column names, at every merge, not once.
- **Kill rule for every lens:** two reads without beating baseline → retire the lens, note it here, keep
  the columns (additive, null, harmless).

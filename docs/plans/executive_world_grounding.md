# Executive's world-picture: fact vs memory, and where it currently blurs

> **Status: 🟢 LIVE ⚠ (2026-09-03, J-0493) — D-0068 was reopened by the J-0385 defeater, then
> re-ruled: PERCEIVE overrides RECALL on current-state conflicts. J-0462 built the explicit
> conflict-resolution instruction, live in `nodes/executive_node.py`. J-0493's 2026-09-03 live
> re-read (F-0716) found the post-fix sample too thin to test the defeater — only 2 PERCEIVE-bearing
> cycles in ~20h, both from one recurring prompt, neither a clean win/loss case (see the 2026-09-03
> update in Current State below). ⚠ Still not closed: D-0068's defeater requires a real
> PERCEIVE-vs-RECALL conflict Du actually resolves one way or the other before this can be marked
> fully resolved. Follow-up re-read queued as J-0528.**
>
> **Status (superseded 2026-09-02): 🟡 BUILT, DEFEATER FIRED (2026-09-02, J-0385) — the structural
> fix from D-0068's option (b) is built and correct, but its defeater has triggered: J-0385's
> re-check found real conflict cases where Executive still favors RECALL content over
> concurrently-present PERCEIVE content on a current-state claim. D-0068 was REOPENED — founder call
> on fix direction needed; see spawned job J-0458 (now done — see D-0068's re-ruling above).**
>
> **Status (original, superseded above): 🟢 BUILT (2026-08-29, J-0343) — D-0068 ruled option (b), the structural fix, and it is built.**
> `nodes/executive_node.py`'s `_build_prompt` now groups the already-Du-side fact lines into two
> headed blocks using `core/source_model.py`'s `SourceType` vocabulary, exactly as scoped:
> **"WHAT YOU PERCEIVE RIGHT NOW"** (`SourceType.PERCEPTION`) — the location scene-line
> (`asked_location`), `state.observation` ("WHAT YOU SEE RIGHT NOW"), and `state.self_facts`
> ("THE TRUTH OF YOUR OWN LIFE RIGHT NOW") — moved up to sit together right after the raw input,
> replacing their old scattered positions. **"WHAT YOU RECALL"** (`SourceType.MEMORY_RECALL` /
> `INFERENCE`) — `state.recall` (reconstruction/tensions/self-model) or `state.memory_fragments`,
> plus `state.recurring_subconscious_patterns` (previously stranded after Reflection, now grouped
> with the rest of recall) — sit together where the recall block used to be. Zero new data sources:
> every sub-line is the exact original text, just re-grouped under two shared headers instead of
> arriving as one flat, equally-weighted list. Verified by a synthetic `_build_prompt` run (correct
> grouping, gating, and content preserved) and by manually tracing the transformation against a real
> logged Executive prompt (`data/training/executive.jsonl`, 2933 lines, 22 in the last 24h) that had
> both perceive-now and recall content populated — see `docs/findings.jsonl` for the finding record.
> Everything NOT named in D-0068's scope (axiom, conversation history, emotion, salience, attention,
> reflection, critic, climate_hint, felt_preamble, library_note, epistemic_note, letters, left_take,
> content_mode, goal_note, and `state.perception` itself) is untouched — this was a relabelling of
> prompt structure, not a rewrite. D-0068's defeater: "reopens if the tiering doesn't measurably
> close the world-grounding gap it targets" — leave that read for a founder pass once live Executive
> cycles have run under the new structure.

```plan-state
stage: live
phase: Structural PERCEIVE/RECALL tiering and override rule LIVE since 2026-09-02 (J-0462); D-0068 own defeater still not meaningfully tested, only 2 thin PERCEIVE-bearing cases seen as of 2026-09-03
verified: 2026-11-18
evidence_read: 2026-08-29
next: Re-run the D-0068 defeater read when 8+ new clean non-templated PERCEIVE/RECALL location conflicts accrue (follow-up job spawned from F-5080, gated on executive.jsonl rows)
cluster: 2
```


> Founder prompt (2026-08-17, post-restart): "think about the executive node next and how it
> plays into du and sees this world as it is fact based from memory to a certain degree."
> Explore-only pass — no live code touched. Written while Travis sleeps; a design for him to
> rule on, in the pattern of every other plan doc this session.

> **CORRECTED 2026-08-17 (founder, same night):** the first draft of this doc proposed a
> "THE WORLD RIGHT NOW" Executive tier sourced directly from `world_manifest.live()`. Founder
> caught it: **"Du should not contain the world truth at all. Just what Du believes. This
> should be independent from the World data."** That proposal would have handed Executive the
> world's own objective tuple as trusted ground truth — exactly the thing the tree-falls law
> ("the world is a static object on its own schedule; Du does not have access to this
> information as such; Du gets to ask a question") was written to forbid, just relocated from
> the sound plan to this one. `world_manifest.py` stays infrastructure — a substrate other
> systems (factories, the ghost world-index, future rate functions) compute answers FROM. It
> must never be a direct source into Executive's prompt, no matter how "certain" its fields
> are. The section below is rewritten to match. The original mistaken section is kept, struck
> through, at the bottom, as the record of the correction (nothing here gets quietly erased).

## Current State — verified 2026-11-18
- **2026-11-18** (F-5080): J-4243 read of D-0068 defeater (F-5080): 37 post-J-0462 PERCEIVE rows; only 4 clean location conflicts, all the same 'bank the fire' prompt; PERCEIVE won 2, RECALL won 1 (line 3077), mixed 1 (3132). Fire-state conflicts are confounded by the human instruction. Defeater inconclusive (n=4), directionally better than pre-fix 1/4. Stale J-0528 reference corrected.

### What we have
- The structural fix is BUILT and LIVE (J-0343, 2026-08-29): `nodes/executive_node.py::_build_prompt`
  groups Du-side fact lines into "WHAT YOU PERCEIVE RIGHT NOW" (`SourceType.PERCEPTION`) and "WHAT
  YOU RECALL" (`SourceType.MEMORY_RECALL`/`INFERENCE`) blocks — zero new data sources, world_manifest
  never enters the path (per the 2026-08-17 founder correction below).
- D-0068's defeater fired once (J-0385, 2026-09-02, F-0629): tiering alone didn't stop Executive
  drawing a current-state claim from RECALL over concurrent PERCEIVE content. Re-ruled (J-0462):
  built an explicit "PERCEIVE overrides RECALL on conflict" instruction, live since 2026-09-02.
- J-0493's 2026-09-03 live re-read (F-0716) found the post-fix sample too thin to test the new
  defeater — only 2 PERCEIVE-bearing cycles in ~20h, neither a clean win/loss case.

### What we need
- A real day of PERCEIVE-vs-RECALL conflict cycles to actually test whether the override rule
  works, not just that it fires.

### What we're doing next
- File a fresh follow-up job once more conflict cycles accrue in `data/training/executive.jsonl` —
  the doc's own "J-0528" citation is stale/wrong (that id belongs to an already-done, unrelated
  social_world_school job), so no real re-read is currently queued.

## The question, read carefully

Executive is the node that decides what Du actually thinks and whether to say it
(`nodes/executive_node.py`). Its prompt (`_build_prompt`) is a flat sequence of `lines.append()`
calls — axiom, conversation history, location, self-facts, deep memory, recall reconstruction,
memory fragments, reflection draft, subconscious patterns, critic verdict. Every one of these
becomes an equally-weighted line of text. The founder's phrasing points at something real: Du's
picture of "what is true" is not one thing. Some of it is **live world-fact** (the weather, where
he is, whether the fire is lit — true regardless of what he remembers). Some of it is
**fact-through-memory** (his cat is his, he has/hasn't read this book — a deterministic ledger
lookup, but a *memory* lookup, not a live sensor read). Some of it is **genuine recollection**
(Recall's reconstruction, fragments, self-model — compressed, drift-prone, sometimes in tension
with itself). And some of it is **synthesis presented as knowledge** (subconscious patterns,
climate hints, deep-memory library notes — the architecture's own inference, correctly hedged
in a couple of places, not in others).

Executive currently cannot tell these apart structurally. It has to infer certainty from prose
register alone, line by line, because every injector writes its own hedge (or doesn't).

## What already exists for exactly this problem

Two systems already formalise the fact/memory/inference distinction — neither reaches Executive
before it decides:

1. **`core/source_model.py`** — `SourceType` taxonomy (perception, memory_recall, inference,
   parametric_library, external_witness, ...), `GROUNDED_SOURCES` vs `INJECTED_SOURCES`,
   strength ordering. This is the vocabulary.
2. **`core/epistemic_state.py`** (`ProvenanceLedger`) — grades the **utterance Du already
   produced**, post-hoc, into KNOW/THINK/SUSPECT/GUESS, by scoring evidence actually present.
   Stage A (`preassess`) runs every cycle, shadow-only. Stage B (`note_for_draft`) is the one
   channel that was built to feed a grade *back* into Executive's prompt — but it is scoped
   narrowly (a single hedge-admission for a caught overclaim) and is `STAGE_B_ENABLED = False`,
   off since 2026-07-05 because the shadow log showed it firing on philosophical cycles rather
   than factual ones.

So the grading machinery exists and is sound. What's missing is not a new grader — it's using
the *already-known* origin of each fact-line to sort it into a tier, at construction time,
architecturally, rather than trying to catch overclaims after the fact.

## The boundary, stated precisely (the correction)

There is exactly ONE physical substrate — `sensorium.state` / `room_state.json` — and everything
downstream reads from it one way or another; that was always true and stays true. The law isn't
"nothing may share a data source." The law is about what Du is HANDED:

- `world_manifest.py` sits BEHIND any query — it's what an ask-time answer gets *computed from*,
  never what Du receives directly. Its own docstring already says this ("this manifest is what
  ask-time answers are computed FROM") — P0 just forgot, one doc later, that "ask-time answers"
  means the NARRATED, FILTERED output of a Du-side query function (`scene_line()`, `look()`,
  a future `evidence_recall`-style world query) — never the manifest's own tuple, unmediated,
  dropped into a prompt.
- `scene_line()` and `look()` already do this correctly, and always have: they read live state
  and hand Du a filtered, narrated sentence — "the fire burning warm in the grate," not
  `fire="out", fire_fuel=0.0`. That IS "Du asks a question, gets an answer computed from current
  state" — the tree-falls pattern working as designed. Nothing about them is being questioned.
  Whether they read their raw numbers from `room_state.json` directly or, someday, from
  `world_manifest`'s parity-checked copy of the same numbers is a plumbing question with zero
  effect on what Du receives — not in scope here, not needed to fix anything named in this doc.
- **The one thing that must never happen: `world_manifest.live()` (or any of its fields) landing
  in a prompt Du reads, unmediated by a narrating query function.** That collapses the boundary —
  Du would be holding the world's own record of itself, not his perception of it. This is the
  same failure shape as the world-side sound archive the sound plan deleted for the identical
  reason, just one layer up the stack.

So the earlier "two un-unified readers" framing was solving the wrong problem. Whether
`scene_line()` and `world_manifest.py` read the same underlying weather field through two code
paths is an *infrastructure* parity question — it matters for whether the ghost world-index and
future factory rate-functions stay correct, and belongs with the P0 test suite, not with
Executive. It says nothing about what Du should be shown, and nothing here should route Du's
belief-picture through the manifest to "fix" it.

`orchestrator.py`'s `self_facts` block (cat name/status, book-read status — lines 491-538) was
never in question either: `core.cat.status()` and `core.reading.current_offset()` are Du-side
memory/belief stores (his cat, his reading ledger), not world-truth. They already behave exactly
right — a filtered, hedged, first-person-ready fact about HIS life, computed at ask-time from
HIS OWN records. The only real gap there is mechanical (every new fact of this shape needs its
own hand-rolled regex trigger) — a genuine but much smaller problem than the one this doc set
out to solve, and not urgent.

## Du's OWN linked-memory ledger — already built, correctly separate

Founder: "Each of Du's memories should have their own links. Their own 'spreadsheet' as such,
external from the world one." This already exists, and it already gets the separation right —
worth confirming explicitly rather than re-designing it:

- **`core/memory_edges.py`** — a typed relational graph OVER the memory store: `resolves`,
  `answers`, `kept_from`, `dreamt_from`, `correspondence_with`, `part_of`. Every edge carries
  provenance (which event earned it — no confabulated links). Entirely Du-side: fragments,
  shadow_events, cycles, questions, keepsakes, dreams, people. Zero world-factory content.
- **`ghost_tuples.MemoryIndex`** (P0-B, built earlier tonight) — the "spreadsheet" in the
  founder's literal sense: one entry per memory's own encoding-context chord (place/weather/
  tide/sounds/standpoint AT THE TIME that memory was laid down — his experience of the world in
  that moment, not the world's current state). Rarity-weighted chord matching. The module's own
  docstring already states the law this session had already reached: **"TWO NAMESPACES, NEVER
  MIXED... a query against one namespace can never return the other's entries — asserted in
  tests, not assumed."** The memory index is explicitly commented "Du-side ONLY."

So the founder's instruction is confirmation of ground already claimed correctly tonight, not a
new build. **The one real gap:** both of these are currently *write-only from Executive's point
of view* — `memory_edges.py`'s own docstring says "NOTHING reads these edges yet" (the trail-
engine upgrade, M2, is flag-gated and unbuilt), and `ghost_tuples.MemoryIndex.query()` has no
live caller either. Executive's actual "what I recall" tier today is still the older, flatter
`Recall.reconstruction` / `memory_fragments` list — it doesn't yet draw on Du's own linked-memory
graph or his chord index at all. That gap is real, but it's a *memory-side* enrichment (richer
recall, still 100% Du's own store), not a route into world-truth — and it's already on the
roadmap as M2, correctly gated behind a week of the co-recall shadow ledger's data. Nothing
here should jump that queue.

## What the corrected proposal actually is

Executive's prompt should keep receiving exactly the KIND of thing it receives today — Du's own
perception (`scene_line`/`look`, narrated, filtered, ask-time-computed) and Du's own memory
(Recall, fragments, self-model, self_facts) — with **no new channel from `world_manifest.py`
added at all.** The real, still-open problem named at the top of this doc stands as originally
diagnosed: these already-Du-side facts arrive as one flat, equally-weighted list, with certainty
surviving only where an individual injector hand-wrote a hedge. Two corrected options, in order
of how much they respect "don't build what isn't needed yet":

**(a) Minimal — do nothing new, just watch.** The existing hedges (self_facts, library_note) are
already good. The gap may be smaller than it looked once world_manifest is correctly removed
from consideration — worth re-reading a day of Executive prompts before designing further.

**(b) If the founder wants the structural fix:** tier by origin using vocabulary that ALREADY
exists (`source_model.py`'s `SourceType`, already computed per-fragment) — a "WHAT YOU PERCEIVE
RIGHT NOW" block (scene_line/look/self_facts — Du's own senses, already narrated) separated from
"WHAT YOU RECALL" (Recall/fragments/self-model/subconscious patterns — Du's own memory, already
source-tagged). Both blocks are, and remain, entirely Du-side. This is a smaller, safer version
of the original proposal: a relabelling of prompt structure using data Executive already
receives, zero new data sources, nothing from world_manifest anywhere in the path.

Neither option is time-critical. Both are queued behind the founder's read of the Refinery
shadow log and the P0 manifest's own day of parity, already in flight — and now behind this
correction being read and ruled on first.

---

### Retained for the record: the original (wrong) proposal, struck through

~~**Tier 1 — "THE WORLD RIGHT NOW" (live, certain).** Everything `world_manifest.live()` already
carries — place, weather, tide, temperature, fire, season, cat's visible activity, active
sounds — rendered as flat fact, no hedging needed, because it's re-read from the world every
tick and can't be stale by construction. This *replaces* `scene_line()`'s raw reads inside the
Executive path.~~ — **wrong**: this hands Du the world's own tuple directly, violating the
tree-falls boundary. Kept here, struck through, so the correction has a visible before/after
rather than a silently-edited history.

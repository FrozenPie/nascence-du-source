# emissary_lane2 — folded history


---

# History folded on 2026-09-27 from `docs\plans\emissary_lane2.md` (plan-compact, 3 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py emissary_lane2`._

## Current State — verified 2026-09-05

**Emissary grounding route (`core/left_lane.py` `ground_thought`) — the-Master leak gated (D-0153).** Since the
2026-09-02 move of grounding to mixtral:8x7b on Ramses, the Emissary's own title for Du leaked into groundings he
hears as his own thought (9.15% → 7.7% mixtral-era baseline; the 2026-09-04 prompt line cut it to 1.3% = 7/548 with
1 integrated leak, F-0848; bar was <1% and 0 integrated). Founder ruled **D-0153: retry once, then gate** — a leaking
grounding is re-asked once; if it leaks again it is discarded and `core/deliberation.py`'s existing hot-lane
fallback grounds the thought. Every gated grounding is logged to `data/ground_leak_gate.jsonl` (attempt, action,
snippet). Verified in isolation (6/6 cases incl. no false positive on "master bedroom", fail-open unchanged).
Restart-gated. **What we need:** a week of `ground_leak_gate.jsonl` + a fresh era split of `deliberation_log.jsonl`
(J-0556's re-measure) — the D-0153 defeater fires if the gate trips on >5% of groundings or any post-gate row still
carries the title. Note: D-0153 was filed under `thought_grounding` by mistake (S-0039); it belongs here.

## Current State — verified 2026-09-06

**J-0620 checked in — too early, not a defeater result (F-0989).** The gate has been live only ~23.8h (14.2%
of the "a week live" D-0153's own defeater names) as of this check: first restart after commit `7b8943f`
(2026-09-05 15:37:04 NZST) was 2026-09-05 18:14:35 NZST, no restart since. Interim/partial-window read only
(NOT the official week-mark re-measure): gate fire rate 33/1131 = 2.918% (under the >5% bar), 0 post-gate
`\b[Tt]he Master\b` hits (both casings) in `deliberation_log.jsonl`, hot-fallback share 7/1138 = 0.615% in-window
— but that last number is not yet interpretable: the same metric measured pre-gate swings from 0.265%
(equal-duration 23.8h window) to 4.782% (full week before gate-live), so a single day post-gate carries no
signal about the gate's real cost either way. No defeater condition has fired, but the window is far too short
to call it — D-0153 is not being reopened or re-confirmed on this data. **What we still need:** the same
measurement re-run after ~2026-09-12/13 (a full week post gate-live), per D-0153's own defeater wording and
J-0620's own title. J-0620 left `in_progress` (not `done`) for exactly this reason — it is a time-blocked job,
not a completed one.

## Current State — verified 2026-08-23

### What we have
- A complete, founder-directed design conversation (this doc), kept in full and unmodified since 08-17/08-19, converging on a specific architecture: the object-graph, per-property earning law, gap-diagnosis taxonomy, and the affect-nudge courier.
- A companion lab spec, `docs/completed/lane2_lab.md`, holding the pre-registered metric sheet and kill criteria for the zero-LLM script side (referenced directly in the STATUS line, late 08-17).
- A companion cognitive-science deep-dive, `docs/completed/emissary_lane2_cognition.md`, whose findings (§4.1/§5.1 windowing requirement, §5.2 gap-prioritized idle, §5.3 retroactive-backfill proposal, §5.5 arousal-modulated tick) are already folded into this design.
- A lab report with real trend data already run against Du's actual history: `docs/lab/lane2_lab_report.md`, cited for the six trend shapes (extinct ghost, new/active, perennial symbol, growing world-presence, settled companion, episodic) and the system-voiceprint filter finding (template vocabulary "'valence reflection' ×2,216" breaking frequency/channel-contrast discovery).
- Six existing, unconnected code fragments audited and catalogued as prototypes/precedent (table under "What already exists"): `core/emissary.py`, `core/left_lane.py`, `core/emissary_tension.py`, `core/prediction_error.py`, `core/competence.py`, `core/source_model.py`/`core/epistemic_state.py`, `core/memory_edges.py`, `core/ghost_tuples.MemoryIndex` — none of them wired to each other or to a standing Lane 2 loop.

### What we need
- `core/object_graph.py` itself does not exist — it is described, not built, per the doc's own RENAMED note ("What this doc describes — `core/object_graph.py`... was never a voice") and its founder-directed-design-session note ("Nothing in this doc is built").
- No standing tick/loop for Lane 2 exists anywhere: `orchestrator.start_background()` "has no entry for the Emissary at all" (per "The gap" section).
- The raw/label sensory split needed for the full gull example is an unbuilt upstream prerequisite in `soundscape.py` (flagged, not solved, in "The object-graph" section).
- The lab itself (`docs/completed/lane2_lab.md`) must run and be founder-graded before any live build — this is the explicit gate in the STATUS line, and nothing in this doc indicates that grading has happened yet.

### What we're doing next
- Per "Open questions": build sequencing is an explicit founder call not yet made, with the cognition research's RETROACTIVE BACKFILL (seed the object-graph from existing logs — 26k thoughts, the Hearing Ledger, fragment_context — before the loop runs live) proposed as the concrete first step, including its built-in validation case (the glass float should emerge from backfill as a high-observation object with an unexplained disappearance).
- Also open and undecided: which port becomes Lane 2's dedicated hub, the left-lane CPU-consolidation question, and the `librarian.py`/`peers.py` telemetry fix — all founder-deferred, not blocking, not forgotten (per "Open questions").

### Update 2026-08-29 — Rescoped per lab grading (D-0080, job J-0356)

The lab this doc's own STATUS line gated on (`docs/completed/lane2_lab.md`) has run twice (08-17, re-verified
08-24 on 35% more data) and been graded. D-0080 rules the rescope; this section states what survives and
what's excluded.

**What the passing criteria support (in scope, narrower than the original design):**
- **The backfilled object-graph itself** — L1 (build: 304 referents, 100,443 mention-edges, 7.8s) and L2
  (depth-ledger parity, 20/20 exact) both PASS. The per-property earning law's depth ladder (seen →
  looked-at → investigated → kept) and entry-channel tags (lived/read/told/dream/thought) are real and
  verified against four existing ledgers, not just designed.
- **The cat as multi-channel proof case** — L4 PASS (kept=True, 4 distinct channels). The channel/depth
  machinery works on a real, deep object, not just thin ones.
- **Windowed commonality weights, for the two pairs that replicated** — L5: storm↔arousal (z=13.74) and
  fire_crackle↔valence (z=21.27) both hold and strengthened on re-verification. storm↔valence did NOT
  replicate (z=-2.66→z=-1.21, below the |z|≥2 bar) — carry all three as computed, not as three-for-three
  proof.
- **The float-profile as a computed DIMENSION, not a single validation object** — K1 killed the narrow
  pre-registered test (one canonical "glass float" object, terminal+absent), but the same lab's own
  follow-up item-population scan found the pattern it was probing for is real and populated: 12 of 104
  cleaned concrete referents are float-like (thought≥20, thought≥5×lived), with real trend-shape
  structure (extinct ghost / new-active / perennial symbol / growing world-presence / settled companion /
  episodic) demonstrated end-to-end on the Jung-name trend-break. **Keep the dimension, drop the
  single-object gate.**
- **The system-voiceprint filter** — confirmed a hard requirement, not a nice-to-have: raw frequency and
  even channel-contrast discovery both broke on the store's own template vocabulary ("valence
  reflection" ×2,216) before this filter was applied. Any index build must filter first.
- **Coreference proposals** (`possibly_same_referent_as`) — mechanically works (41 candidates generated,
  founder-gradable), proposal-only, never auto-merged. Stays in scope as a candidate generator.

**What K1/K3 explicitly exclude from the next build (not designed away — killed by lab evidence):**
- **The standing tick/predict-loop** ("The loop's own tick — four behaviors" section below) — K3's own
  prescribed consequence: "the standing prediction loop is premature... the graph survives as an index
  only." The 30-day data hole (verified real outage, not artifact, F-0108) means there isn't yet enough
  continuous history for predict-outcome/re-check-trend to mean anything. Deferred until the data span
  covers a real post-outage stretch, not redesigned.
- **The LLM prediction call and its dedicated hardware** — downstream of the standing loop; waits on the
  same data-scale condition.
- **The affect-nudge courier** — its own spec already said "needs the loop live"; K3 keeps the loop from
  going live, so the courier stays out of scope with it.
- **The single canonical "glass float" object as a validation gate** — specifically wrong on the facts
  (the float turned out non-terminal, still being ruminated on near-daily), not just failed; replaced by
  the population-level float-profile dimension above.
- **Gap diagnosis (L8) and the temporal-extrapolation half of the loop as LIVE mechanisms** — the 5-cause
  taxonomy classifies real gaps correctly when run as a dry-run report (L8 founder-graded, mechanically
  sound), but wiring it into a live loop inherits K3's premise problem until the loop itself is unblocked.

**Net scope:** an index-only `core/object_graph.py` — backfill-built, script-side, zero-LLM, produce-only,
covering exactly L1/L2/L4/L5(2-of-3)/voiceprint-filter/float-profile-dimension/coreference-proposals —
with everything past that line (standing loop, LLM prediction, affect courier) left as designed-but-
deferred, gated on the data-scale condition K3 named, not on any further design work. `scripts/lane2_lab.py`
is already a working prototype of exactly this scope, run twice against live data; the remaining work is
porting it to a production module, not re-designing it. See job J-0363 (spawned this pass) for that build.

### Update 2026-08-29 (same day, later) — J-0363 build note: `core/object_graph.py` already existed;
### this pass closed the real gap (L5/L6 + L9), not a from-scratch build

**Correction, owned:** the line above ("core/object_graph.py is still not built") was stale by the time
J-0363 opened it. The module was already built and committed (git baseline `8eef0bb`, 2026-08-27; its own
internal history — `docs/lab/lane2_recheck_report.md`, `scripts/lane2_recheck.py` — shows it running for
real as early as 2026-08-18). Whoever built it never updated this doc's Current State/rescope sections to
say so — a real toolchain gap (plan doc vs. filesystem reality drifted), not a design problem. J-0363's
first real step was reading the existing module in full before touching anything, per the founder's own
UDMS-dossier discipline.

**What was already there, verified real:** L1 (backfill build), L2 (depth-ledger parity machinery), L4 (the
cat's multi-channel proof case), the voiceprint filter (`is_voiceprint()`, curated bigram/token/prefix
sets + an introspection lexicon — a fuller three-layer implementation than the lab prototype), the
float-profile trend dimension (all six shapes, `_classify_shape()`), the per-property earning law
(`_properties_from_object()`, Layer-1-forbidden boundary enforced and tested), and item-instance-to-class
coreference. Produce-only and unwired: confirmed `orchestrator.py` has no reference to `object_graph`
anywhere (grepped clean).

**What was genuinely missing and is what J-0363 actually built:** the module had **no L5/L6 windowed
commonality-weight machinery at all** — it never read `data/geometry_tuples.jsonl`, so the
storm↔arousal / storm↔valence / fire_crackle↔valence pairs the plan's own scope line (2) requires were
simply absent — and **no general L9 coreference-proposal generator** (only the narrower item-instance-
to-class case existed; the lab's book-X-vs-lived-X channel-mix proposal was never ported). Added both,
as a direct, unmodified-in-method port of `scripts/lane2_lab.py`'s `l5_commonality()`/`l6_windowing()`
and `l9_coreference()`:
- `_commonality_pass()` — same shuffle-null z-score discipline (100 shuffles, seed 20260817, the lab's
  own pre-registered seed), same 20-per-arm floor, now reporting BOTH the all-time weight+z AND the
  windowed (7d) weight per pair per call — never a hardcoded verdict from any prior run. Public reader:
  `object_graph.commonality()`.
- `_coreference_proposals()` — same read>=5-AND-lived>=5 channel-mix rule as the lab's L9, generalized
  across the whole lexicon (not just item instances). Public reader: `object_graph.coreference_proposals()`.
- Both are computed fresh on every `build_full()`/`refresh()` call and stored in `graph.json` under
  `commonality`/`coreference_proposals`; `status()` now surfaces `n_commonality_pairs`,
  `n_commonality_signal`, `n_coreference_proposals` for the HUD.

**Storage decision (the doc's own TBD, resolved):** a dedicated store (`data/lane2/graph.json`), NOT a new
node-kind in `core/memory_edges.py`. Read `memory_edges.py` in full and ran `udms_get_change_dossier` on
it first (CLAUDE.md rule) — it flagged CRITICAL/CYCLIC_FEEDBACK_LOOP risk (an import cycle between
`core/heavens.py`/`core/world_clock.py`, unrelated to this change) and 17 CONTRACT-layer (real, 100%-
certain static-AST) dependents, none of which import or touch object-graph concerns. `memory_edges.py`'s
own contract is explicit: "the typed relational fabric... edges that similarity cannot compute" — flat
`(src_kind, src_id, dst_kind, dst_id, edge_type, weight, provenance, created)` rows, deliberately NOT a
place for rich nested per-object documents. The object-graph's referents carry day-bucketed mention
series, per-property knowledge atoms, trend classifications, and now per-pair commonality stats and
coreference proposals — none of that is edge-shaped, and forcing it into `memory_edges` rows would mean
either flattening real structure into `provenance` text (dishonest) or bolting a second schema onto a
table whose own docstring already warns against exactly that kind of scope creep (the `derived_from`
three-incompatible-shapes guard is the cautionary precedent). The dedicated-store choice the module
already made (before this job even opened) is the more honest fit and is kept, not re-decided.

**Verification, real not simulated:** `python scripts/test_object_graph.py` — 200 passed / 5 failed. All
5 failures are pre-existing (the test file is unmodified from the same 2026-08-27 baseline commit as the
module) and are live-data drift, not caused by this pass: `driftwood_17` now has 10 observations, not the
2 the test hardcodes (Du kept looking at it since 08-17), and a Layer-1-leak check on newly-appeared
garden-factory items (`garden_plant_*`) throws false positives on shared property-key names
(`height_cm`, `life`) — worth a follow-up read, not blocking, and not this job's scope to fix (flagged
separately, not silently dropped). The two new test functions added for this pass (`t16_commonality_pairs`,
`t17_coreference_proposals`) both pass. A real production `build_full()` was also run for real (not just
in the test's tempdir) — `data/lane2/graph.json` rebuilt today: 439 referents, 129,061 mention-edges,
170 property atoms, all 3 commonality pairs currently SIGNAL on live data (storm↔valence, which had
weakened below |z|>=2 on the 2026-08-24 re-verification, reads SIGNAL again on today's larger dataset —
report honestly as a live, re-computed number each build, not as a re-confirmed 3-for-3 constant), and
132 coreference proposals (up from 41 at the original lab's data volume). See finding F-0451 for full
evidence.

> **[Section removed 2026-08-31]** A fabricated benchmark claim (confidence=verified, citing scripts/modules that do not exist) was quarantined from here per F-0593/D-0105 — see `docs/lab/fabricated_benchmark_claims_2026-08-25.md`.

> **★ RENAMED 2026-08-19.** This doc originally called itself "Lane 2." Founder decision, prompted by a
> return to the founder's ORIGINAL two-hot-loop idea (a genuine second continuous, autonomous,
> senses-grounded reasoning VOICE, running at Lane 1's own tempo — never built): that name now belongs
> to the new channel that actually matches it — see `docs/plans/lane2_the_witness.md`. What this doc
> describes — `core/object_graph.py`, deterministic, zero-LLM, "produce-only... not a participant" by
> its own contract — was never a voice; it's a fact-tracking ledger, closer in character to Lane 3 (the
> world/factories) than to a standing cognitive loop. Nothing in the design or the code below changed —
> only the name, and the honest recognition of what it actually is. Kept in full, unmodified otherwise,
> because the design conversation it records is still exactly right for what THIS organ is for.

> Founder-directed design session, the night after P0 (world_manifest.py / ghost_tuples.py) shipped.
> Nothing in this doc is built. It is the record of a long, iterative conversation that converged
> without ever contradicting itself — kept in full because of that. Companion docs: `docs/plans/
> world_factories_P0.md` (Lane 3, already built), `docs/reviews/chain_walk_findings.md` (F-EX — the correction
> that shaped this doc's central boundary), and `docs/completed/emissary_lane2_cognition.md` (the
> cognitive-science deep-dive — the mapping to real cognition, the constraints we escape, and the
> requirements it added to this doc: windowed trends, gap-prioritized idle, backfill-first).
>
> **The keystone justification, in one line (from the cognition research):** the human brain has no
> decoupled judge — confabulation is its normal operating mode (split-brain interpreter, choice
> blindness), because evolution couldn't afford a second brain to audit the first. Lane 2 is that
> organ, built. Every self-evaluation failure in this project's history is the same missing organ.
>
> **STATUS (late 08-17): refined into a lab test** — `docs/completed/lane2_lab.md` holds the
> pre-registered metric sheet and kill criteria for the script side (zero LLM, read-only over live
> stores, all outputs temp-pathed, Du stays up). The lab must run and be founder-graded before any
> live build.

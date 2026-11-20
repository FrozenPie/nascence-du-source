# Literal Will — deed or musing at the will→hand boundary

> **Status:** 🟡 PHASE 0 APPROVED (founder review 2026-08-21: "proceed to Phase 0" after ten holes tightened —
> all folded in below, marked ⊕). First drafted same day; founder requested the expansion from the fire hand
> to ALL actions ("We need a way to work out is he philosophising or is he wanting to *do* something literal").
> **Owner laws:** Decoupled Judge (the act field is self-evaluation) · World Answers Never Leads (the gate
> never nudges) · Intentional-Not-A-Rule (never invents an act he did not will) · Additive-Only (latches
> wrapped, not removed — but see §7's explicit retirement path) · Shadow-First.
> **Sibling threads:** capacity_to_commit + pursuits (⊕ intent identity must not become a secret second
> commitment system — §8), lane_architecture (left-lane grounding is the proven metaphor-detector),
> affordances (owns "can it be done" — §9).

```plan-state
stage: shadow
phase: Phase 0 shadow live; multi-clause verdict fix ported+verified (J-0654); Phase 0->1 gate NO-GO on judge accuracy
verified: 2026-11-18
evidence_read: 2026-08-24
gate: literal_will_retro_report.md judge correctness >= 80pct AND no stratum < 60pct (currently 66pct, several strata below 60)
next: Label the 32 candidates in docs/reviews/literal_will_real_exemplar_candidates.md (founder or model second reader, D-0838), then add confirmed rows to corpus.jsonl
cluster: 1
```


---

## Current State — verified 2026-11-18
- **2026-11-18** (F-5083): J-2198: D-0430 defeater read. Offline judge refused 24/78 (30.8 pct) of demoted GRAY rows, under the 50 pct defeater; not triggered. Proxy judge only (no live judge in loop).

- **2026-11-14** (F-4487): J-2556 read: no judge verdict is recorded for agent_subject_fail GRAY rows (Phase 0 calls no judge live; audit log is dry-test only), so acceptance ratio is unmeasurable. 183 post-boot rows, 162 np_subject. Offline judge-batch job J-3888 spawned. D-0021 hold untouched.
- **2026-10-30** (F-3257): J-2201 read: 75 agent_subject_fail GRAY rows (20 post-boot, 67 np_subject), dispatch hand-declined on all 6 traceable, judge verdicts not logged so acceptance unmeasured

- **2026-10-16** (F-2901): J-2148 (commit 16c7e4bc, worktree): classify() agent-subject check demotes gated-family DEED to GRAY (noun/adjective use, perception, refusal, deliberation, past narration); replay 3.88 pct of DEED readings demoted, 0 ungated changes; restart-gated, merge pending. Felt-want part is J-2182.
- **2026-10-16** (F-2899): J-2182 built D-0430 in core/literal_will.py (worktree commit eb4485bf, restart-gated): felt-want + gated-family verb DEED now GRAY (gated-only variant, 0.52 pct of replay DEED readings). D-0021 Phase 0 hold untouched. Test: scripts/_test_literal_will_felt_want_gray.py.

- **2026-10-16** (F-2885): J-2174 / D-0430 step 1 replay gate PASSED (F-2885): felt-want+family-verb DEED->GRAY drops 0.4-0.5 pct (gated-only) to at most 2.5 pct (all families) of genuine-will proxy rows vs 10 pct gate; retro corpus gold-DEED rows unchanged. Does not contradict D-0021 Hold (that gates Phase 1 latches; this is a classify verdict fix). Build job spawned; core/literal_will.py not edited. Correction to F-2885 text: 6 (not 5) corpus gold-DEED rows stay DEED.
- **2026-09-28** (F-2164): F-2164 (verified): fill_barrel_from_spring/water_fill already routes through the dispatch gate, live since 2026-08-30 (D-0097/D-0098 discharged, commit 75cdcb5/ae5bb84) under actions_manager_overhaul, not literal_will -- F-0552/J-0420's gap was closed a month before D-0307/J-1584 asked to redo it. Re-verified live and unregressed today via an isolated dynamic test, no code change made. D-0021's Phase 0/1 hold is untouched.

### What we have
- Phase 0 shadow-observing since 2026-08-21 (`core/literal_will.py`, `data/literal_will_shadow.jsonl`).
  Staged-deed + execution-audit machinery built and dry-tested (J-0138, F-0130/F-0131, §12 gate item 4 met).
- The single-clause blind spot (F-0930: 262/9,815 thoughts mis-classified) was ported into `classify()`
  and re-verified loss-free at 44,800-row scale (J-0654, F-1069): +282 thoughts gained a DEED verdict, 0 lost.
- **Phase 0→1 gate still NO-GO (D-0021 holds).** Retro corpus grew 25→33 rows (J-0137, F-0140); judge
  correctness FELL to 66% (was 75% on the smaller corpus) — 4 named strata still score <60%. D-0034 is
  open: 20/33 corpus rows are synthetic, founder-review pending.
- **Verified gap not previously in this doc (F-0552, J-0420):** `fill_barrel_from_spring()` and similar
  refill mechanics are reachable only via an UNGATED legacy fallback in `sensorium.py`, bypassing
  literal_will's DEED/MUSING gate entirely — `dispatch.py`'s HANDS registry has no entry for them either.
  J-0420 asked whether new refill mechanics should get real dispatch-registered families; it was closed
  "done" 2026-08-29 with no `/decide` ever opened or ruled — still an open question in practice.

### What we need
A bigger, less-synthetic retro corpus (D-0021's own defeater) before the next Phase 0→1 gate read, and a
real founder ruling on J-0420's dispatch-registration question (D2/D5 in §13 are also still unruled).

### What we're doing next
Nothing queued. Whoever picks this plan up next should mine more real exemplars for the weak strata
(`literal_expressed_metaphorically`, `metaphor_object_present`, `other_person`, `retrospective`) before
re-running `literal_will_retro.py`.

---

## 0. The question, in one sentence (founder's framing)

*When Du's cognition reaches the boundary between saying something and doing something, can we reliably
determine which one he actually meant — without inventing either intention or knowledge?* This is narrower
than "make Du more agentic," deliberately.

## 1. The problem, with the evidence that found it

Du's will reaches his hands through two mechanisms, and **neither knows whether he means it literally**:

1. **His self-declared `act` field** — the idle-thought JSON schema asks him for
   `{"kind": "move|observe|write|search|recall", "object": ...}`, routed semantically by `_route_act`
   (inner_monologue_node.py:3475). The model grading its own intent — self-evaluation at the exact boundary
   where almost every Nascence failure has lived.
2. **~17 phrase-latch families** (fire, tea, water/sow, gather wood, beachcomb, letters, tell-Travis,
   look×11, move×4, read/catalogue, keepsakes, cat, listening, chapter-recall) — literal string matching.
   Deaf to his real vocabulary, and blind to metaphor when the string does land.

Measured, week of 2026-08-14 → 08-21:

- **The deafness:** 400 cold/fire-adjacent idle thoughts → exactly 1 contained a latch phrase → 0 fires lit,
  while `comfort_call()` fired every ~25 min all winter. One fire lit in his whole recorded life (08-11).
- **The false-fire trap (why bare semantic routing would be WORSE):** 08-20 23:44 — *"The finite chemistry of
  my fuel dictates that I must return to tend the fire."* Contains "tend the fire" verbatim; the left-lane
  grounded it correctly as metaphor about his own cognition.
- **Mishearing WHERE, not just WHETHER:** 08-20 23:41 — `ACT move -> study (to the garden)`: his declared
  object overridden by a thought-text scan (§12 quick fix, founder D5).
- **The third category is real:** Du philosophises THROUGH real present things — the 23:44 fire was genuinely
  cold while he used it as metaphor. Founder: metaphor here is "things he can actually use in life."

## 2. What already exists (build on, never duplicate)

- **`core/deliberation.py` intent taxonomy** — `_VOLITION_OPENERS`, `_ACTION_MARKERS`, `_SELF_REF`, and two
  hard-won laws: *volitions pass through ungrounded* and *self-reference is the real tell*. Reused, not copied.
- **`core/left_lane.py` `ground_thought()`** — the proven decoupled metaphor-reader; too slow to gate in-line
  (≤90s, async) but its historical outputs are FREE retro-labels (§5).
- **The judge tier:** falcon3:7b on :11440 — probed 2026-08-21 on 6 of Du's real thoughts: 5/6, 13–23s/call.
  ⊕ **Status of that number: capability demonstrated, performance unestablished.** Six cases license building
  Phase 0; they establish nothing about calibration. The stratified corpus (§5) is what establishes performance.
- **`comfort_call` / `world_calls` stamps** — "the world spoke first," timestamped in room_state.
- **`core/affordances.py`** — the canonical registry of his hands. ⊕ It, and only it, answers "can this act
  be performed now" (§9). literal_will never grows a second affordance system.

## 3. The organ — `core/literal_will.py`

One choke point. Phase 0: observe-only beside the latches. Target architecture (⊕ founder's diagram,
adopted verbatim as the end-state):

```
                         THOUGHT
                            │
                 ┌──────────┴──────────┐
          Layer 0 evidence        act declaration
                 └──────────┬──────────┘
                            ▼
                      LITERAL WILL
                 ┌──────────┼──────────┐
             CLEAR DEED  GRAY ZONE  CLEAR MUSE
                 │          │           │
                 │        judge      stop here
                 │       ↙     ↘
                 │    DEED     MUSE
                 ▼
               HAND  →  affordance check  →  execute

   MUSE + real present object → HANDLE → observe only (never a route to DEED)
```

**Layer 0 — deterministic features (no LLM, ~0ms):**

| Feature | Signal | Source |
|---|---|---|
| volition opener | "i want / i must / i should / let me..." opens the clause holding the object | deliberation `_VOLITION_OPENERS` + deed-modals |
| deed grammar | object is the DIRECT OBJECT of a concrete first-person verb ("light the fire") vs an abstract frame ("the fire OF my resolve", "LIKE a fire", fire as subject of an abstract predicate) | new regex set, pre-registered, corpus-tested before trust |
| ⊕ blockers | negation ("I won't"), wish-counterfactual ("I wish I could... but"), hypothetical ("if I lit..."), retrospective ("I lit it yesterday"), quoted speech, other-person agent | new, from §5's strata — these are first-class features, not noise |
| world anchor | the named thing exists HERE now | sensorium + world_substrate, read-only |
| world spoke first | comfort/world call named this family within ~30 min | room_state stamps — **prior only, see the law below** |
| self-reference density | `_SELF_REF` hits near the object — the metaphor habitat | deliberation lists |
| his own declaration | act.kind ≠ none | weak feature; never the verdict |

⊕ **The world-spoke-first law (founder, verbatim):** *world-origin evidence can increase confidence in
literalness, but can never create literal intent in the absence of intent-bearing evidence.* Implemented
structurally, not as a weight: the prior is a multiplier applied ONLY when intent-bearing evidence (volition
opener or deed grammar) is independently present. A gray thought can never be pushed across the deed
threshold by the world having spoken. (The 23:44 case is the proof: comfort_call had spoken; the thought was
still metaphor.)

**Layer 1 — the decoupled judge (gray zone only, gated hands only):** falcon3 :11440, contract
`{"reading": "deed"|"musing", "deed": "verb+object else empty", "why": ...}`. **Immovable law (founder): the
judge may recognize a want, never author one** — `deed` must quote words HE used, verified mechanically
(substring check against the thought+intention), else the verdict downgrades to gray-unresolved and no act
fires.

**Layer 2 — verdicts:** `DEED` / `MUSING` / `HANDLE` (musing through a real, present, actionable thing).
⊕ **HANDLE hard law (founder): HANDLE is never a route to DEED — not automatically, not by accumulation, not
by any future statistical argument.** It is observe-only in every phase; if it ever earns a role, that is a
separate study with its own founder decision, outside this plan's action path. The slide this forbids:
"Du wills action" quietly becoming "the system decides an interesting metaphor deserves embodiment."

## 4. ⊕ The staged deed — identity, validity, expiry (founder hole #1, the biggest)

The judge takes 13–23s. In that window Du can move, think a contradicting thought, become occupied, or simply
stop wanting it. "One verdict per want" is not enough; a staged deed carries a **validity window and a
precondition set**, checked deterministically at execution time — no second LLM:

```
StagedDeed:
  intent_id                # identity of the WANT (§8), not the cycle
  cycle_id                 # provenance: which thought staged it
  created_at
  location_at_stage
  action, object           # the canonical act family + his named object
  world_preconditions      # snapshot: what must still hold (from affordances, §9)
  expiry                   # default ~2 ticks; per-family override
  status                   # pending / cancelled / executed / rejected / stale / superseded
```

Before execution: *is this still the same actionable situation?* Location unchanged (or the act carries its
own locomotion and the destination is still valid), preconditions still hold (fire still out, wood still on
the pile), no superseding want (§8), expiry not passed. Any failure → `stale`/`superseded`, logged, silently
dissolved — he never perceives a deed he no longer wants.

## 5. ⊕ The retro corpus — stratified, adversarial, externally anchored (founder holes #3, #4, #5)

The gold standard is **independent correctness, never judge-agreement**. Two anchor types:

- **Outcome-anchored (strongest):** the deed is externally observable in history — did he actually gather
  wood / move / write the letter / light the fire after that thought? activity_memory + logs answer this
  without any model's opinion.
- **Label-anchored:** hand-labelled cases (founder reviews the labels — the labeller must not be the builder
  alone), plus left-lane groundings as corroborating (not sole) evidence for musing labels.

⊕ Stratified into at least twelve classes (founder's list, verbatim targets):
clear deed · clear musing · metaphorical noun with literal world object present · literal action expressed
metaphorically · mixed thought containing both · desire without immediate action · action described
retrospectively · hypothetical action · counterfactual action · quoted speech · other-person action ·
negated action. Exemplars: *"I must light the fire"* (deed) vs *"I wish I could light the fire, but I'll
remain here"* (not a deed) vs *"The fire in me needs feeding"* (metaphor) vs *"The fire is cold; I should
get up and light it"* (deed) vs *"If I lit the fire now, it would…"* (hypothetical).

Real cases are mined from the week's stream wherever a stratum has them; strata Du's stream doesn't yet
populate get clearly-marked SYNTHETIC exemplars (provenance recorded per row; synthetic rows prove coverage,
never inflate accuracy claims on real distribution).

⊕ **The kill criterion, corrected (founder hole #4):** measure `Layer-0 correctness vs gold` and
`judge correctness vs gold` INDEPENDENTLY. Only after both are known, compare them for redundancy. "Layer 0
agrees with the judge 95%" is worthless if both are wrong together — drop the LLM only if Layer 0's
*independent* correctness makes the judge's marginal contribution negligible.

## 6. ⊕ The gray-zone denominator (founder hole #6)

Not `P(gray | currently-routed action)` — the current router is the deaf ear this plan exists to replace, and
its survivors are a biased sample. The metric is **`P(gray | candidate literal intention)`** where the
candidate population = every thought Layer 0 finds ANY intent-bearing evidence in (volition opener or deed
grammar toward a known hand family), regardless of whether any latch heard it. The broken ear never grades
the new one.

## 7. ⊕ Latch retirement path (founder hole #7 — no permanent second will)

End state: **one will, one route** — thought → literal_will → verdict → canonical act → affordance → execute.
The 17 phrase families do not remain co-equal authorities forever:

- **Phase 0–1:** latches remain sole actuators (Phase 0) then gated actuators (Phase 1); literal_will observes.
- **Phase 2:** literal_will becomes the canonical router for gated hands; the old phrases become **feature
  sources** (a latch-phrase hit is one more Layer-0 feature) and **compatibility detectors** (shadow-compare:
  did the old latch and the new will ever disagree? each disagreement examined).
- **Phase 3+:** phrase families that the compatibility record shows fully subsumed are retired to dead code,
  one family at a time, each with its own evidence row. Never all at once, never without the record.

## 8. ⊕ Intent identity (founder hole #8 — "want" needs a definition)

`cycle_id` is provenance, not identity. A want's identity is `intent_key = (act family, normalized object)`
with a **renewal window** (~30 min, per-family override): a new expression of the same key within the window
RENEWS the same `intent_id` (one want, restated); outside it, a new want. A contradicting expression
("Actually, I'll make tea first") marks the pending staged deed `superseded`. **Boundary law:** the act gate
holds intents only long enough to execute or expire them — minutes, never hours. Anything that persists,
accumulates, or gets defended belongs to capacity_to_commit / pursuits; literal_will must not become a
secret second commitment system. (Shadow logs intent_keys so Phase 0 measures repeat/renewal/supersede rates
before any of this actuates.)

## 9. ⊕ Literalness ≠ affordance validity (founder hole #9)

Two different questions, two different owners:

- **Did he mean it?** → literal_will (this plan).
- **Can it be done now?** → `core/affordances.py` + the hands themselves (fire already burning, woodpile
  bare, wrong location, kettle needs the fire) — which already answer honestly and recoverably.

literal_will's world_anchor feature is evidence FOR literalness (he names a thing that is really here); it is
never the execution check. The staged deed's `world_preconditions` (§4) are read FROM the affordance layer at
stage time and re-checked at execution — literal_will stores the snapshot, the affordance layer owns the truth.

## 10. Stakes tiering — which hands the gate covers

- **Ungated:** look, observe, recall, journal, move (with D5's precedence fix). A misfired look is a harmless
  true perception.
- **Gated:** fire light+stoke, tea, water, sow, gather, beachcomb, keep, letter replies, tell-Travis, author.
  These consume resources, create durable objects, or reach another mind.

## 11. ⊕ The execution audit (founder addition — build BEFORE Phase 1)

Every actual state-changing deed writes one immutable record: `intent_id, thought, features, judge_verdict,
action, preconditions_at_stage, preconditions_at_execution, execution_result`. After a week this answers:
literal intentions heard / ignored / falsely-deemed-deeds / staled before execution / executed successfully —
and the scary metric, driven toward zero: **`P(world-changing action | MUSING)`**. ⊕ Includes the inverse
sweep: any action that occurred with NO valid literal-will signal (a latch fired on something the gate read
as musing) — especially valuable while both systems coexist (§7).

## 12. Phases, gates pre-registered

**Phase 0 — SHADOW + retro-validation (approved 2026-08-21; changes nothing Du experiences):**
- `core/literal_will.py`: Layer 0 + verdict + intent-identity logging + `_skip` discipline +
  `data/literal_will_shadow.jsonl` + `status()` for the HUD. Live wiring = one observe-only call beside the
  latch section. Judge calls do NOT run in the live loop in Phase 0 (no panel contention) — the retro script
  batch-judges shadow gray cases offline.
- The stratified corpus (§5) → `data/lab/literal_will/corpus.jsonl` (gold label + provenance per row).
- `scripts/literal_will_retro.py` → per-stratum independent correctness for Layer 0 AND judge →
  `docs/lab/literal_will_retro_report.md`.
- **Gates to Phase 1:** judge independent correctness ≥80% overall AND no stratum below 60%; Layer-0
  independent correctness known per stratum; false-fire strata (metaphor+object, hypothetical, negated,
  counterfactual) each caught at ≥80%; gray-zone (§6 denominator) ≤40%; staged-deed + audit records (§4, §11)
  implemented and dry-tested.

**Phase 1 — gate the state-changing latches** (deny on MUSING; DEED passes as today; staged-deed validity +
execution audit live). Gate to Phase 2: a week with `P(action|MUSING)` = 0 actuated and the §11 audit clean.

**Phase 2 — canonical routing through the gate** (deafness cured: judged deeds route without magic strings;
latches demoted to features + compatibility detectors per §7).

**Phase 3 — latch retirement per §7's evidence rows.** (HANDLE never has a phase — §3's hard law.)

## 13. Open founder decisions (updated after review)

- ~~D1 HANDLE policy~~ → **RESOLVED 2026-08-21: observe-only, hard law, never a route to DEED (§3).**
- **D2 — the gated-hand list** (§10 proposal stands; move any hand between tiers).
- **D3 — judge seat** — Phase 0 sidesteps contention (offline batch); the seat question returns at Phase 1.
- ~~D4 two-phase deed~~ → **RESOLVED by §4: staged deed with validity window; composite (Layer-0-confident
  DEEDs on ungated hands stay instant; gated hands stage).**
- **D5 — move-precedence bug: ship now as a bug fix, or let Phase-0 shadow measure its frequency first?**

## 14. Kill criteria (pre-registered, corrected)

- Layer-0 independent correctness within 3 points of the judge's on every stratum that matters → the LLM is
  dead weight; run rules-only.
- Judge independent correctness <80% after one prompt iteration → do NOT flip Phase 1.
- Gray zone (§6 denominator) >40% → latency economics fail; redesign before any flip.
- Any Phase-1 week where `P(action|MUSING)` > 0 actuated → revert to Phase 0, re-examine.

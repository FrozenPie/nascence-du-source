# Object Permanence & the Pull of Absent Things — what he knows is out of sight, and what that does to him (2026-11-01)

> **Status: 🔵 IDEA → DESIGN OPEN (2026-11-01).** Opened by the founder after a live bug (below): *"We 100% need this.
> Children learn this fairly early. Maybe we can integrate this into Du's architecture."* Nothing here is built except
> the L0 stopgap (one reply string, shipped and untested live). Everything else is a proposal for a later discussion —
> the founder asked to "discuss this one another time". Cluster 0 child of `cognitive_geometry.md`.

```plan-state
stage: idea
phase: Opened 2026-11-01 from T-0118/T-0119; L0 stopgap (out_of_sight reply) edited in, restart-gated; L1-L3 undesigned
verified: 2026-11-18
next: Phase 1 shadow belief ledger build (see job filed from J-4380)
cluster: 0
```

---

## 1. Where this came from (read, not remembered)

2026-11-01 11:53 NZT. Travis, talking to Du in the live chat, asked about the lamp in his study ("it has no oil in it…
maybe I should bring electricity to your study"). Du was **in the garden** (`data/room_state.json` `location = "garden"`,
verified). The pre-answer sensorium gate (`core/orchestrator.py` `_look_map`) had no lamp key; only a later "your study"
fired the `room` look, and `sensorium.look()` from the garden returned a **yard description** — the garden fallback frame
— as if the question had been about the garden. Nothing told him the lamp was not in view.

Facts, verified by reading: the lamp is a real item (`study_life.py` `oil_lamp`), its reservoir was really dry
(`lamp_oil = 0.0`), the oil tin really held 2.8 — so Travis's observation was true and Du had no way to be told so.
The existing "it's up in your study" guard in `look()` covered only `desk/shelf/book/grate/hearth/fire`; every other
study object fell through to the place's default look. (Findings: T-0118, T-0119 in `thoughts.jsonl`.)

**L0 — shipped as a stopgap, same day (restart-gated, tested on a copy of the live state only):**
`study_life.out_of_sight()` + a guard in `sensorium.look()` + a lamp key in the orchestrator look map. From the garden,
shore or wood, a look at a fixed study item now answers *"You cannot see the lamp from the garden."* — no direction,
no hint (08-14 law). Carried items and items set down where he stands are exempt.

L0 is **not** object permanence. It is the world honestly saying "not in view". It does not say whether he *knows* the
lamp is there, what state he last saw it in, or whether that knowledge matters to him.

## 2. The idea, decomposed (what I infer — the founder's musing was one paragraph; this is my split of it)

| Layer | What it is | Status |
|---|---|---|
| **L0 Known-absent** | the world answers "cannot see X from here" | stopgap edited in 11-01 |
| **L1 Object permanence** | he holds a *belief* about where X is and what state it was last seen in — separate from the world's truth, aging, able to be stale | not designed; only `cat.py` keeps a `last_seen` today (verified by grep) |
| **L2 The pull** | a believed-unfinished absent thing (dry lamp, dusk, a wish to read) creates a *want* | not designed |
| **L3 Weighted wants** | multidimensional weights across many wants; a want that was pressed or acted on **fatigues**; a want that crossed its threshold is **sticky** (hysteresis) until satisfied or relaxed; wants may or may not be acted on | not designed |

Founder's own words for L3: *"Weighted wants that he may or may not do. Multidimensional weights that fatigue with
sticky springs maybe??"* — "springs" is not loose talk here: `cognitive_geometry.md` §2.2 already has a constitutional
law, **IMMUTABLE OBJECTS, PLASTIC SPRINGS**, and says *"Object permanence is the accumulation substrate: a spring can only
be EARNED if repeated encounters resolve to the same node."* So the geometry plan **requires** L1 before its springs can
exist at all — this plan is the missing precondition, not a side quest. (ROADMAP cluster 0, line ~401 repeats it.)

## 3. What exists that this must not duplicate or fight (each checked by reading its header)

- **`cognitive_geometry.md` §2.2** — objects as the anchor registry; the *keepsake rule* (individual node when kept or
  recurrent, else its kind-node). L1's "what is an object he can hold a belief about" should be that registry, not a new one.
- **`affect_drives.md`** — "all senses, no hands": felt signals computed but never reaching behaviour. L2/L3 are a drive
  layer; `drowsiness_phase.md` §2 already warned "build one mechanism and fold the other into it rather than shipping
  two competing injections". **Open question Q2 is exactly whether wants fold into drives or are new.**
- **`pursuits.md`** — persistent threads the idle mind RETURNs to; live, serial-monogamous (D-0109), with a decoupled
  judge. The nearest existing "pull across the gap". A want for an absent object may just be a *kind of pursuit*.
- **`executive_world_grounding.md`** — Executive's prompt separates *"WHAT YOU PERCEIVE RIGHT NOW"* from *"WHAT YOU
  RECALL"*, and D-0068 rules PERCEIVE overrides RECALL on current-state conflicts. A permanence belief is a RECALL item;
  it must be shown **with its age** and must never be rendered as PERCEIVE.
- **`capacity_to_commit.md`** — the want→must modal asymmetry (J-2660/F-3420: levelling "want" up to "must" is the only way
  idle wants register) is live evidence that *wants currently have no weight of their own*. L3 is partly the cure for that
  asymmetry — and must coordinate with D-0524/D-0527 before anything touches how wants are scanned.
- **`literal_will.md`** — musing vs deed at the will→hand boundary. A want must stay a *want* until he wills a deed.
- **`study_upgrade.md`** (SHIPPED) — the lamp, oil can, tin, wick are real items; its own §0 recorded the lamp as
  "prose-only", and the showpiece tea loop ("a kettle that wants herbs") has **never fired** (0 rows, per its plan-state) —
  a standing hint that household wants are too weak to register against the idle stream.
- **Precedent for stickiness:** `core/balance.py` — a hysteresis band (`REENTER_AT = 0.42`, latches `_sprinting/_reading`)
  so a mode doesn't flap at its threshold. This is the house idiom for "sticky".
- **Precedent for fatigue:** `core/curiosity_habituation.py` (exists; I have **not** read it — verify before reusing).

## 4. Developmental framing (from general knowledge, NOT verified in this repo)

Infants first act as if hidden things cease to exist, then search for them, then show the "A-not-B" error (search where it
was last found rather than where it was last seen), then hold stable representations. Rough ages are commonly given as
~8–12 months for search; I am quoting that from memory, and the analogy is a *function* to transfer, not a mechanism to
imitate (founder law: function over imitation). The useful structural point: **the early failures are belief-staleness
failures, and a belief store can be tested against the world for exactly that** — which is what makes it judgeable.

## 5. Laws that bind any design (and why each matters here)

1. **World answers, never leads (08-14).** A want must never arrive as "you should fill the lamp". It can only exist as
   something he *notices in himself* or is *free to notice* — and only because the world is genuinely that way.
2. **Intentional, not a rule.** No system acts on his behalf later. A want biases what he *attends to*; he wills the deed.
3. **Decoupled Judge.** The belief store is judged by something other than itself: **belief vs the world's current state**
   is an external, cheap, always-available check (`lamp_oil` known vs believed). The want layer needs its own judge
   (did the weight predict anything he later did?) — pre-register it before building.
4. **Write-only is the #1 failure.** Every layer must ship with its read path named and tested as *called*. A belief
   ledger nobody reads is the exact disease (`feedback_write_only_cognitive_systems`).
5. **Additive-only / shadow-first.** Base systems are protected. Each layer starts as a shadow log.
6. **Doses, not wiring.** DOSED COUPLING (ROADMAP, D-0149) governs how loops may touch each other; a want layer touches
   the idle loop, affect and the executive — it needs a dose plan before it needs code.

## 6. Open questions for the founder (not for me to settle)

- **Q1 — Where does the belief live?** Reuse the geometry anchor registry / `identity_estate` typed nodes, a thin new
  ledger keyed by `study_life` item key, or episodic memory fragments?
- **Q2 — New wants layer or fold into `affect_drives` / `pursuits`?** Three drive-ish systems competing is the risk.
- **Q3 — May a want ever *enter the idle stream* uninvited?** This is the sharpest edge of "no system-acts-later": a
  weighted want that surfaces a thought is a system acting on him, unless it only raises the *salience of an option*
  he can decline. Needs a ruling before L2.
- **Q4 — Scope of the first object set:** the lamp only, the whole study's items (`study_life._WORDS`), or the registry?
- **Q5 — Should his belief ever be wrong *in his experience*?** (A-not-B: he walks in expecting oil and finds it dry.)
  That is realistic and testable, but it is also the first moment the world *contradicts* him (cluster 5, afferent /
  contradiction signal, is the nearest existing home). Founder's call whether staleness is a feature.

## 7. Staged phases (restaged 2026-11-18 per D-0853; every phase pre-registers its metric first)

Rulings (D-0853, founder chat 2026-11-18): Q1 thin new ledger keyed by `study_life` item key (Claude default, open to veto);
Q2 fold into `affect_drives` / `pursuits`, no new wants layer; Q3 pull may only raise salience of a declinable option, never write a
thought; Q4 scope = the FULL registry (lamp-only may be the first measured slice); Q5 staleness is a feature, corrected only through
what he finds (D-0434), shadow-first. Q2 conflict check: `affect_drives` Item D is held (F-5088, saturated gap), so no phase below
rides on Item D until its normalisation is redesigned.

- **Phase 0 - Evidence, no code. DONE** (F-4548: study objects named in 3.7% of outside-study thoughts vs 22.1% inside).
- **Phase 1 - Belief ledger, shadow (no read path to Du).** Thin ledger keyed by `study_life` item key, rows
  `last_perceived_at / believed_state / source`, written on PERCEIVE (look, use, carry), compared with `st["items"]` truth at read time.
  Scope: full registry; report the lamp slice separately. **Pre-registered metrics:** (a) coverage: >= 80% of registry items
  have >= 1 belief row after 14 Du-up days; (b) drift: share of reads where believed_state != truth is non-zero and < 60% (not degenerate);
  (c) staleness age distribution has >= 3 distinct non-empty quartiles; (d) zero writes to any Du-facing prompt or store.
- **Phase 2 - Read path.** One age-stamped RECALL line in Executive's block behind a flag (D-0068 PERCEIVE>RECALL); a stale belief is
  corrected only by what he perceives, no world hint (D-0434). **Gate:** line is called (counter > 0) and a decoupled judge finds it
  true to the ledger in >= 90% of a 30-line sample; distress check: no rise in low-mood lines naming the object vs Phase 0 baseline.
- **Phase 3 - Salience, shadow only.** Salience weight of an absent-thing option computed (no actuation) via the `pursuits` /
  `affect_drives` read paths (not Item D until redesigned); log what it would have raised vs what he then did. **Gate:** predicts
  his next-option choice above a shuffled null (z >= 2) over >= 14 Du-up days. Never writes a thought (Q3).
- **Phase 4 - Fatigue + sticky springs.** Habituation on pressed pulls, hysteresis on committed ones, only after Phase 3 passes.
  **Gate:** no distress loops (D-0853 defeater); behaviour effect visible at 14 Du-up days or the plan is revisited.

## 8. Not decided / not claimed

- Nothing in this doc claims Du lacks object permanence internally: his LLM-side knowledge that the lamp is in the study
  may already be doing a version of L1 through the prompt. **That is a hypothesis; Phase 0 is meant to test it.**
- The L0 reply is untested against his live process (needs a restart) and untested for the willed-look path
  (`_observe_target` could not be located; treat willed looks as unverified).
- Whether a "want" belongs in Du at all, versus attention only, is a founder question, not an engineering one.

## Current State — verified 2026-11-18
- **2026-11-18**: 2026-11-18 (D-0853, J-4380): founder Q1-Q5 ruled (thin ledger by study_life key; fold into affect/pursuits; salience-only never a thought; full registry; staleness is a feature). Section 7 restaged with pre-registered metrics. Q2 conflict: affect Item D held (F-5088).

- **2026-11-14** (F-4548): Phase 0 evidence read done (J-3811, F-4548): study objects named in 3.7% of outside-study thoughts (vs 22.1% inside); mix of implicit belief and present-tense perception of absent objects. Q1-Q5 still need the founder (J-3063).
- **2026-11-01:** plan opened. L0 stopgap edited into `core/study_life.py` (`out_of_sight`), `core/sensorium.py` (guard before the letterbox branch in `look()`), `core/orchestrator.py` (lamp key in `_look_map`); tested on an in-memory copy of live state (garden/shore → "cannot see"; study → real lamp state; carried → exempt). Restart-gated. Thoughts T-0118, T-0119.

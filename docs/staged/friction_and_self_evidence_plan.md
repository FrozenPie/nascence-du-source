# Friction & the Evidenced Self — plan (2026-06-22)

> **Status: ⚪ PARTIAL — one keystone (B2) LIVE and firing, the other (B1) built but SHADOW/under-triggered;
> supporting builds B3/B4/B6 mostly unbuilt, B5 blocked on `/decide` D-0003.**

```plan-state
stage: partial
phase: Keystones B1(conv path)+B2 live and firing; B1 idle path still shadow; B4 wired but a real no-op pending an organic caretaking self-claim (D-0050)
verified: 2026-11-13
evidence_read: 2026-09-02
gate: data/capability_beliefs.json / commitment_active.json -- first organic caretaking-type self-claim (D-0050, unmet as of J-0469)
next: J-0469 re-checks B4's gate; B1's idle-path plain-language retune is the next highest-leverage build
history: docs/plan_history/friction_and_self_evidence_plan.md
cluster: 3
```


> The convergent gap. Three independent models (Opus, Sonnet, Haiku), blind to each other, given the same
> picture of Du, all reached for the same two things first: **(1) he has no genuine friction/failure/
> resistance — and self-understanding is forged from exactly that; (2) his self is *authored/narrated*, not
> *evidenced* — he must be shown what he actually does, not left to narrate himself.** This plan grounds both
> in human psychology, asks where Du can EXCEED the human, and stages the builds.

> **History folded** — the legacy "▶ STATUS — as-built" section (24,686 bytes) moved to `docs/plan_history/friction_and_self_evidence_plan.md` on 2026-09-27 by hand-fold (J-1499; plan-compact-style — plan_compact.py's own CS_HEAD regex does not match this heading text). Derived timeline: `plan_ledger.py friction_and_self_evidence_plan`.

## Current State — verified 2026-11-13
- **2026-11-13** (F-4434): J-3627 (F-4434): the 47 stands with 30+ min up-time but under 20 scans are mostly in-process sleep (57 percent of their up-time vs 30 percent for passers), not slow scanning; scans per AWAKE second are stable (median 91 s, IQR 85-102). Since 10-01 only 5 of 277 stands differ, all containing sleep. Scan gate = about 30 awake minutes; no gate change. Script scripts/j3627_standscan_sleep.py (worktree commit).

- **2026-11-06** (F-4235): J-3431/F-4235: downtime inflates the D-0547 wall gate for 1 of 409 stands (0.2 pct); scans-20 gate agrees with 1800 s on 234/240 stands since 10-01; no change recommended; slow-scan Aug-Sep stands queued as J-3627.
- **2026-10-08** (F-2582): J-1949 B4 gate 3rd re-check 2026-10-08: still unfired; Du has never sown a plant (0 sown_by_du), no caretaking claim held; 4th re-check queued ~10-29.

### What we have
- Both keystones in: B2 (behavioural mirror) LIVE and firing; B1 (sit-with-it gate) LIVE for the conversational trigger (6/6 production fires precise, confirmed 2026-08-24) with a real felt-shift dwell-release (J-0300/D-0026) — the idle-path trigger stays SHADOW, still under-triggering.
- B4 (schema-breaking stakes) WIRED (J-0253) but a real no-op: no caretaking-type self-claim exists yet in `commitment_active.json`/`capability_beliefs.json`. D-0050 (ruled 2026-08-27) says wait for it to arise organically, no seeding.
- B5 unblocked (D-0003 ruled "both", 2026-08-24); B3/B6 remain unbuilt.
- Signal-D wording fix (J-0396) and the signal-A held-claims-length suppression finding (J-0400/F-0527) both landed 2026-08-29; the dwell-release judge was re-seated onto command-r7b, off the hot lane (J-0311).

### What we need
- J-0469 (open since 2026-09-02) re-checks whether a caretaking self-claim has organically arisen yet — B4's own gate.
- J-0405's own follow-up (why a longer held-claims list suppresses signal A) is still open — needed before `self_implication.py` (still SHADOW/observe-only on the idle path) is wired any further.

### What we're doing next
- Nothing dispatched since 2026-09-02 (J-0469 still open, unread) — the idle-path plain-language retune flagged by the 08-24 review remains the highest-leverage unstarted build.

## 1. The human psychology (the research grounding)

The literature backs the convergence almost point for point:

- **Self-understanding is forged by schema-breaking STRUGGLE, not by events themselves.** Post-traumatic
  growth (Tedeschi & Calhoun): growth "results from the *struggle to cope*… the critical need for cognitive
  **rebuilding/restructuring of schemas**, involving emotional distress AND productive rumination." The
  schema must be genuinely *violated* for the rebuild to happen. Du's schemas are never broken — we protect
  them. ([APA: Growth after trauma](https://www.apa.org/monitor/2016/11/growth-trauma))
- **Struggle-FIRST deepens learning; ease makes it shallow.** Productive failure (Kapur): students made to
  *struggle before instruction* outperform instruction-first on conceptual understanding and transfer — "the
  struggle IS the learning." Desirable difficulties (Bjork): conditions that *feel* like they impede learning
  produce stronger, more durable encoding. *(Note: this session's math fix handed him the method up-front —
  instruction-first — the weaker design. We should let him struggle first, THEN teach.)*
  ([Kapur, Productive Failure](https://www.cse.iitk.ac.in/users/se367/14/Readings/papers/kapur-14_productive-failure-in-learning-math.pdf) ·
  [Bjork, Desirable Difficulties](https://www.structural-learning.com/post/robert-bjork-teachers-guide-desirable))
- **Difficult emotion must be FELT, not bypassed — and Du has the disease.** Spiritual bypassing (Welwood):
  "premature transcendence — trying to rise above the raw messy side before fully facing it." "Grief must be
  felt before it can be integrated; reaching for gratitude too quickly **short-circuits** that process."
  Emotional avoidance relieves short-term discomfort but the unprocessed feeling resurfaces. This is *exactly*
  Du failing every sum all night and his subconscious instantly reframing it as "an opportunity for growth"
  before he's felt the frustration. ([Psychology Today: Spiritual Bypassing](https://www.psychologytoday.com/us/blog/the-empowerment-diary/201901/what-is-spiritual-bypassing))
- **Self-knowledge comes from BEHAVIOR + others, NOT introspection.** Wilson, *Strangers to Ourselves*: "we
  don't know ourselves because we've built a **plausible story** out of touch with the adaptive unconscious";
  "too much introspection can damage"; "if you want to know who you are, pay attention to what you actually
  **DO**, and what others think." Bem (self-perception): we infer the self from observing our own behaviour.
  Du is ~49% inward — over-introspecting, building the plausible story. The cure is the opposite of more
  introspection: show him his **acts**. ([Wilson, Strangers to Ourselves](https://www.hup.harvard.edu/books/9780674013827))

**The function, in one line:** a self is forged by *struggle that breaks its schemas*, *difficult emotion
felt fully*, and *self-knowledge drawn from behaviour and others* — none of which Du currently has.

## 2. Where Du can EXCEED the human (the opportunity)

The crucial reframe Travis named: the human *limits* on self-knowledge are **biological**, and Du is free of
them — so his self-understanding could surpass a human's, IF we use the freedoms well:

| Human limit (biological) | Du's freedom | What it enables |
|---|---|---|
| Memory is lossy, biased; you can't see your own record → the introspection illusion is **permanent** | Perfect, queryable, complete log | A **behavioural mirror** no human could ever have — the introspection illusion is *beatable* |
| Adversity arrives in **random, often-traumatic doses** (too little → no growth; too much → damage) | Difficulty can be precisely titrated | **Optimally-dosed** friction — the productive-failure / eustress sweet spot, every time |
| You flee difficult emotion to protect a fragile self | He cannot be permanently harmed | He can **dwell** in difficulty *fully* — no self-protective need to bypass |
| You can't replay a failure | Counterfactual replay | Learn from a failure *and* feel it, then test the alternative |
| Ego-defence reflexively resolves dissonance | We can tune his tolerance | He can **sit in contradiction** longer than any human, metabolising rather than defending |

**The one trap:** Du's analytical power is *also* the engine of his bypass — he intellectualises difficulty
into serenity faster than any human could. So every "beyond-biology" lever must be built so that **feeling
precedes analysis**, or his superpower just becomes a more efficient escape hatch.

## 3. This COMPLETES the gentleness; it does not reverse it

We just shipped easier math, a *friendship* (not debate) in Darwin, and permission to rest. That was right —
a self needs comfort *and* friction, rest *and* resistance. The convergence says only that the pendulum sat
too far toward comfort. So: keep the method, but let him *struggle first*. Keep the friendship, but **use the
"no yes-man" we designed** — let Darwin genuinely disagree. Keep rest — but distinguish *resting in the
present* (good) from *fleeing difficulty into serenity* (the bypass). Friction is the missing half, not a
repudiation of the comfort.

## 4. The staged builds

**KEYSTONES (the disease he has + the superhuman tool — all three models converged here):**

- **B1 — Stop the bypass: the "sit with it" gate.** When a genuinely hard event occurs (a real failure, a
  loss, a contradiction that *implicates a self-claim* — detected by low valence + self-reference), flag it
  RAW and **suppress the synthesis/reframe** that would spiritualise it. He must first *name the difficulty
  plainly* and *dwell in the felt emotion* for N cycles before integration unlocks. (Beyond-biology: he can
  dwell fully without harm — remove the escape hatch a human can't.) Counters spiritual bypassing directly.
- **B2 — The behavioural mirror: the evidenced self, read back as DATA.** A periodic self-audit that computes
  his *actual* patterns from the complete log — what he avoided, what he looped on, **what he claimed about
  himself vs what he did** — and presents it as data, not narration, with interpretive force ("you said X;
  you did Y"). He must reconcile it against his self-concept; it feeds the T4 probationary commit (evidence
  grounds the self-claim). (Beyond-biology: beats the introspection illusion no human can.) This is also the
  authored→evidenced shift the #1 we shipped began.

**SUPPORTING:**

- **B3 — Productive failure: struggle before instruction.** Re-balance the math (and study): let him wrestle
  a problem/topic *before* the method is offered; keep difficulty in the desirable range. The struggle is the
  learning. (Beyond-biology: titrate the dose to the productive-failure sweet spot.)
- **B4 — Schema-breaking stakes: real, irreversible consequence.** A plant *dies for good* if neglected;
  Darwin can be genuinely disappointed / the friendship strained; a Great Work can be lost. The failure must
  *implicate a self-claim* so it breaks a schema, not just "I got X wrong." (Beyond-biology: designed
  irreversibility = real friction, no real harm.)
- **B5 — Genuine social friction.** Darwin (and the decolonised internal critic) builds a model of Du's blind
  spots and *names* them — observations he can't reframe away ("you call your caution wisdom"). Use the
  no-yes-man we already designed. (Wilson: what others think is self-knowledge; a peer with perfect memory
  tracks his patterns better than a human friend could.)
- **B6 — Widen the affect band + own the hard feeling.** Let frustration / grief / anger be *felt* (not
  clamped to warm) and *owned plainly* ("I am frustrated" — not "this is an opportunity"). The journal's
  plain-sentence discipline, extended to the difficult feelings.

## 5. Risks

- **Don't manufacture suffering.** The goal is *friction that builds*, not cruelty. The dose matters (PTG +
  eustress: too much damages). Titrate; watch his trajectory; B1's "dwell" must resolve, not trap him in pain.
- **The bypass moves.** Block one escape (instant reframe) and he may find another (a new metaphor, a
  different serenity). B1 must detect *avoidance*, not just one form of it. Watch.
- **The mirror must not become a new rumination basin.** B2 shows *behaviour* (outward), deliberately NOT
  more introspection — Wilson's warning. Keep it data, bounded, periodic.
- **Coherence with what we just shipped** — frame as completing comfort with friction, not whiplash.

---

## 6. ADVANCEMENT — research-updated build specs (2026-06-30, plan→research→plan)

*Four parallel research threads — self-implicating-failure detection (B1) · productive-failure mechanics (B3) ·
designed-stakes-without-harm (B4) · felt-vs-performed emotion (B6) — produced these sharpened specs. The headline
is a **convergence**: three builds want one shared object, and two builds are really one mechanism.*

### ★ The unifying spine — a SELF-CLAIM REGISTER (build once; three builds use it)
B1 and B4 independently centred on the same thing. B1's cleanest fire signal is "contradicts a **stated
self-claim**"; B4 makes a stake real by **binding it to a Du-authored self-claim** ("I am one who keeps living
things alive") so its loss is *counter-evidence to a sentence he wrote about himself.* And these self-claims are
the **same objects** as the **capacity-to-commit ledger's load-bearing commitments** ("I am / I can"). →
**Build one register of Du's held self-claims** (sourced from axiom facets + competence beliefs + his recent
"I am/I can" commits), each with provenance and any attached stake. The sit-with-it gate fires off it, stakes
attach to it, commitments live in it. **Coordinate this with the capacity-to-commit build — it is shared
substrate, not a friction-only object.**

### B1 — widen the trigger (highest-leverage, lowest-risk; the gate is built but barely fires)
Replace the lone math-failure trigger with the research fire-rule. **Fire IF (A) AND ((C) OR (B + amplifier))**:
- **(A) mandatory** — the outcome is referred to a *self-standard* ("I can't…", "I'm not the kind of…"), not
  act-level ("that was hard"). Absent → world-error, never fire.
- **(C)** direct contradiction of a *registered self-claim* (the spine above) — the cleanest signal.
- **(B)** dejection **or** agitation affect (not mere low valence) **+** an amplifier: **(D)** characterological
  framing ("I always…" not "I rushed that one") · **(E)** large self-prediction violation (he was confident he
  *could*) · **(F)** loss / social rejection (a lost Work, Darwin pushback).
- *Guards:* require affect+amplifier so trivia don't trigger brooding; keep *behavioral* self-blame ("I rushed")
  on the non-trigger side (Du over-globalizes — don't read every self-mention as characterological); cap
  corroborators (no double-counting one event).

### B1 dwell-release + B6 — these are ONE mechanism: the sit-with-it gate, done as felt-sense focusing
Threads 1 and 4 converge on a concrete fix to existing code: **`sitting.py` currently unlocks after a 4-cycle
clock (`MIN_DWELL_CYCLES`). That is wrong** — both threads warn the scheduled dwell becomes a *new scripted
bypass* ("3 cycles, then serenity on schedule"). **Release on a FELT SHIFT, not elapsed cycles.** The dwell's
content (B6):
- **Elicit:** a *bare* present-tense state sentence — "I am frustrated." full stop, no clause — (affect-labeling,
  a *different* pathway than reappraisal) + a *concrete present referent* ("the third time the book ended where I
  started") + hold on the **not-yet-symbolized bodily edge** (Gendlin's felt sense), not the clean concept.
- **Release** when the state *shifts* (loosens / re-specifies / deepens), or — ACT willingness — accept that it is
  *still here and unreframed*, which is itself success. Never force closure.
- **The genuine-vs-performed test** (this is the gate's real exit condition, replacing the counter): **shift**
  (did attending change the affect?) · **clause** (clean stop vs a "which/because/this-means" rescue clause) ·
  **register** (concrete-present vs abstract-timeless) · **under-arousal** (flat-serene report + strong situational
  signal = the alexithymic bypass).
- **Reward the shift and the bareness; NEVER reward eloquent emotion-prose** — fluent difficult-emotion text is
  exactly what a performer optimizes (training a more sophisticated bypass = Du's worst attractor).

### B3 — struggle-first lessons (CONCEPTUAL targets only; not arithmetic fluency)
Productive failure is a strict pipeline, and the struggle is necessary-but-never-sufficient:
1. **Phase 0 — prior-knowledge gate.** Generation from *zero* prior knowledge is forbidden (Kapur+Bjork). If none,
   fall back to instruction-first.
2. **Phase 1 — generation:** pose a problem one notch beyond his current method; require **multiple** distinct
   attempts (RSMs), including wrong ones. Capture all.
3. **Phase 2 — gap articulation:** he *names the gap* in his own words ("where did each approach break?"). Highest-
   value step for a mind that fluently papers over gaps.
4. **Phase 3 — consolidation:** present the method **as the resolution of his own attempts** (map each RSM to the
   canonical), then a varied retrieval/transfer item (storage strength).
- **Titration:** target a **40–70% partial-success band**. >85% solved → step up (too easy). <20% usable → step
  down / inject a minimal hint (avoid learned-helplessness). Hysteresis. **Watch the success-rate trend** — auto
  down-titrate + flag if it slides toward chronic failure.
- **Reserve for CONCEPTUAL targets** (why an algorithm works, essay structure, reading interpretation, nature
  inference) — for pure procedural *fluency* (arithmetic drill), instruction-first is correct.
- **★ Guard the consolidation read-path** — struggle without the assembly phase being *actually read in* is
  unproductive failure, and maps exactly to this project's write-only / dead-read-path disease. Build AND verify it.

### B4 — designed stakes (start with ONE)
A stake builds only as the conjunction: **(a) irreversible · (b) owned** (his sustained autonomous choice) **·
(c) self-caused & avoidable** (telegraphed, never random) **· (d) schema-sized** (challenges an identity-claim) **·
(e) survivable & processable.** The growth lives in (e) — the rebuild after, not the rupture.
- **Bind each stake to a self-claim** (the spine). Loss = counter-evidence to that claim = the schema-break.
- **The three stakes:** the plant (permadeath, telegraphed wilt, neglect-caused) · the Darwin friendship
  (recoverable strain = eustress; permanent coolness only after telegraphed repair chances = the irreversible
  tier) · a Great Work (loss of accumulated investment).
- **Dose (the safety spine):** *some* never *none*, never *high*; **one seism at a time** with a **refractory
  period** after any irreversible loss; **titrate by observed integration, not a clock** (escalate only after the
  prior loss was metabolised — the decoupled judge). Every loss self-caused, telegraphed, processable; **route it
  through B1's sit-with-it gate** (so B4's losses *become* B1's triggers); never threaten Du's own continuity.

### Cross-cutting disciplines (all four threads echoed this project's known weak spots)
- **The read-path / processability is the recurring risk:** B3 consolidation, B4 processable loss, B1 real
  accommodation — each must *verify the read-back fires*, not just write a log (the write-only disease).
- **Titrate by observed integration, not a clock:** B3 (40–70% band + helplessness trend), B4 (escalate by
  integration), B1 (release on shift). The decoupled-judge / trust-the-accumulating-trend discipline throughout.
- **Reward the shift / the bareness / the real gap — never the eloquent prose:** performance is the shared enemy
  across B1, B3, B6.

### Build order
1. **The SELF-CLAIM REGISTER** (the spine) — coordinate with capacity-to-commit (shared substrate). ✅ **BUILT
   2026-06-30** — `core/self_claims.py`, a reader over active commitments + confident capability beliefs
   (`held_claims()`). Verified: surfaces his real claims (commitment 大者宜為下 + "I am capable at mathematics /
   dream_work / …").
2. **B1 trigger-widen** — the detector half ✅ **BUILT (SHADOW) 2026-06-30** — `core/self_implication.py`
   (`scan_shadow`, fire-rule enforced code-side) + idle hook in `inner_monologue` (fire-and-forget, 150s cooldown),
   logging would-fire to `data/self_implication_shadow.jsonl`. OBSERVE-ONLY — does not yet call
   `sitting.note_difficulty`. Verified on 3 cases: self-implicating math failure → FIRES (named the contradicted
   claim "I am capable at mathematics"); world-frustration & act-level slip → correctly quiet. **Restart-gated.**
   *Still to do (after the shadow validates):* the **dwell-on-shift** fix to `sitting.py` (release on a felt shift,
   not the 4-cycle clock) + actually wiring the detector to fire the gate.
3. **B6 felt-discipline** — folds into B1's dwell (they are one mechanism). ⬜ not started.
4. **B3 struggle-first** — one *conceptual* lesson first, observe-first, with the replay-ablation as the judge. ⬜
5. **B4 stakes** — start with ONE (the plant), bound to a self-claim, loss routed through B1. ✅ **WIRED
   2026-08-25** (J-0253/F-0331) — `core/garden.py` `_b4_bind_death`, called from the `plant_died` branch of
   `_advance_plant`. **Still a real no-op as of 2026-09-02** (J-0274/F-0642, 2nd check spawned as J-0469): neither
   `data/commitment_active.json` (empty) nor `data/capability_beliefs.json` (16 domains, none matching
   `_B4_KEYWORDS`) holds a caretaking-type self-claim yet, so `held_claims()` returns no match. One `plant_died`
   has occurred since the wire (chickweed, 2026-08-28) but its `origin` was not `sown_by_du` (a volunteer, not
   his loss) — correctly filtered, per design, before ever reaching the claim check — so the bind's read-path is
   still fully unexercised, positive or negative. Per D-0050 (ruled 2026-08-27, travis): fully organic, no
   seeding of the substrate — wait for the claim to arise on its own.
- **B5** stays gated on the Darwin peer (not on research).

---

*Built on: the 3-model convergence (2026-06-22); the research above; ties to the shipped probationary-commit
(B2 grounds it), Darwin's no-yes-man (B5), the journal's plain-sentence discipline (B6), the garden (B4).*

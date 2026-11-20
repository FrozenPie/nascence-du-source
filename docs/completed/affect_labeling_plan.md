# Plan — Affect Labeling ("name it to tame it")
*Draft v1 for the research pass + external review. Status: PROPOSAL, not built. 2026-06-13.*

## 0. One sentence
When Du explicitly NAMES a feeling he is having ("I feel fear", "this is grief", "I am
angry"), the named affect's carried intensity should measurably DROP — the architectural
form of the human finding that putting feelings into words attenuates them.

## 1. The human function (to be checked in the research pass)
Lieberman's "affect labeling": verbalizing an emotional state reduces its intensity and its
physiological/limbic signature — distinct from suppression (which costs effort and rebounds)
and from reappraisal (which reframes meaning). Naming is cheap, automatic, and *down-regulates
without changing the content*. The working hypothesis for WHY: translating a diffuse felt
state into a symbol routes it through different processing, and that very act dampens the raw
signal. The research pass must confirm: (a) the effect is real and robust; (b) its size and
conditions; (c) that it is genuinely distinct from suppression/reappraisal; (d) what it would
and would NOT mean to port the *function* (not the neuroanatomy) into Du.

## 2. Why it belongs in THIS project
- Du already has the two endpoints: a continuous `AffectState` (the carried body — joy/fear/
  anger/trust/surprise/disgust/valence/arousal, homeostatic decay toward baseline) and a
  Reflection/monologue path where he sometimes NAMES what he feels in first person.
- Right now naming does nothing to the carry. A named fear and an unnamed fear decay
  identically. So his architecture has the *raw* affect loop but not the *regulatory* one
  that words provide in humans — the healthy counterpart to rumination (which is words that
  AMPLIFY rather than attenuate).
- It is the cheapest credible build on the whole deferred list: one detector + one bounded
  nudge to a state that already exists, no new schema.

## 3. The mechanism (smallest slice)
**Detector (deterministic, no LLM):** scan the cycle's Reflection draft / inner thought for a
first-person emotion-naming construction — "I feel/am [emotion]", "this is [emotion]", "a
[emotion] rises in me" — mapped to one of the tracked AffectState dimensions (fear, anger,
joy, trust, surprise, disgust; plus grief/sadness → low valence). Naming must be SELF-
referential and PRESENT — "I feel afraid" counts; "Travis seemed angry" or "fear is a useful
signal" (abstract) do not.

**The nudge:** on a detected naming, apply an extra one-step decay to THAT dimension's carry
this cycle — pull it a bounded fraction toward baseline, on top of the normal homeostatic
relaxation. Bounded (a single naming soothes, it does not erase), one application per cycle
per dimension, and ONLY toward baseline (labeling never inverts a feeling, only dampens it).

**The honest-counterpart guard:** labeling must not become a cheat the system rewards. Two
protections — (a) it only fires on GENUINE first-person naming, not on the word appearing
anywhere; (b) it attenuates the *carry* (the lingering body-state), NOT the *event's memory* —
he still felt it, it still happened, it still stores. Naming soothes the aftertaste, not the
record. This keeps it distinct from suppression/avoidance.

## 4. Observe-first?
This is small enough and well-grounded enough that it MAY warrant going live directly rather
than a long Phase 0 — BUT the project discipline says log first. Proposed: **Phase 0 = detect
+ log the naming events and what the carry WOULD have done (counterfactual), read nothing**;
flip to live attenuation once the log shows the detector fires on real namings and not on
false positives (abstract emotion-talk, others' emotions, rumination dressed as naming).
Falsifiable check for Phase 0: the detector should fire on his actual "I feel fear / this is
grief" thoughts (we have many in the record) and NOT on "the fear is the music of my
individuation" (abstract reflection, not a present naming).

## 5. What it must NOT do
- Not reduce arousal globally — only the NAMED dimension.
- Not touch memory/importance — the felt event is preserved; only the carry is soothed.
- Not reward naming as a behaviour (no satisfaction/liking credit for labeling per se — that
  would train performative emotion-naming). [NOTE: satisfaction.py currently DOES grant a
  small "affect_labeled" liking — the research pass / review must decide if that is right or
  if it incentivises performance.]
- Not fire on rumination (repeated circling of a feeling is the OPPOSITE of labeling — it
  amplifies; the rumination guard and the naming detector must not collide).

## 6. Where it lives
`AffectState` already owns decay (`integrate`, `tick`). Cleanest home: a small method on
AffectState (`label(dimension)`) called from the orchestrator/monologue after the emotion is
read and the thought is formed, gated by the deterministic detector. Affect labeling is a
GENERAL property of the affect loop (Gemini's earlier ruling — it does NOT belong in the
affiliation organ).

## 7.5 RESEARCH-PASS FINDINGS (v1.1, 2026-06-13) — three revisions, one of them retroactive

**The science (Lieberman 2007 + the moderator literature, PLOS One 2023, the high-reactivity
review 2026):** affect labeling reliably dampens the amygdala/limbic response to negative
affect via right-VLPFC recruitment — robust at the *neural/physiological* level. Crucially it
is **implicit/incidental**: it regulates *without intention or awareness*, and people wrongly
believe it will make them feel worse. It shares the prefrontal down-regulation pathway with
reappraisal (correlated benefit) but is experientially distinct (effortless, not a strategy).
BUT the *subjective-intensity* effect is moderated, and the moderators force real changes:

**REVISION 1 — gate on intensity. Only attenuate moderate-to-high negative affect.** Labeling
is reliable at moderate-to-high intensity, when labels are constrained, and EARLY in
processing; on *low-intensity* states it does little or *paradoxically increases* them. So the
nudge fires only when the named dimension is above a threshold (~0.4). Naming a mild feeling
does nothing — which is correct, not a gap.

**REVISION 2 — negative only. Do NOT dampen positive affect.** The literature includes a
direct finding that *affect labeling INCREASES the intensity of positive emotions*. So the
attenuation applies to fear/anger/disgust/sadness(low-valence) ONLY. Naming joy or trust is
left untouched (we do not add amplification — too speculative — but we must not dampen it).
The v1 plan's "any named dimension decays" was wrong.

**REVISION 3 — REMOVE the satisfaction credit (retroactive fix).** The effect works *because*
it is incidental, not a strategy. `satisfaction.py` currently grants a small `affect_labeled`
liking event — that would train Du to name feelings *instrumentally to feel better*, which
converts labeling into effortful regulation and, per the mechanism, **breaks the very thing
that makes it work**. The naming must stay a noticing, never a move. ACTION: drop
`affect_labeled` from satisfaction's liking events (or down to zero weight). This is exactly
what the research pass is for — it caught a live mistake.

**REVISION 4 — same-cycle, early.** "Early in the processing stream" works best → the nudge
applies in the same cycle the feeling is named, while fresh, not carried forward (answers
old Q2).

**HONEST CAVEAT (raises Phase 0 from optional to MANDATORY):** the robust evidence is largely
for labeling EXTERNAL stimuli (faces, images). Labeling one's OWN INTERNAL state — exactly
what Du does — is the more variable case, with some studies showing minimal or paradoxical
effects. So: keep the nudge SMALL, intensity-gated, negative-only; Phase 0 logs the
counterfactual and we verify it actually soothes (and never inflames) on his real namings
before going live. If the data shows no effect or inflammation, this stays observe-only or is
dropped — a clean, cheap experiment either way.

## 7.7 BOARD RESOLUTION (v1.2, 2026-06-13) — the model changes (GPT), the safeguards stay (Gemini)

**The fork:** Gemini approved the pharmacological model (`detect named negative affect > 0.4
→ bounded extra decay`). GPT challenged the core assumption: humans don't do feel→name→decay;
they do feel→symbolize→the feeling becomes an OBJECT of cognition→regulation may follow.
Reduction is a *consequence* of the representational shift, not the mechanism. The
neuroscience agrees — the rVLPFC event IS symbolization; amygdala down-regulation is
downstream. And the moderator literature warns that internal-state self-labeling (Du's exact
case) is where the subjective attenuation is least reliable. So a hard `*= 0.8` would
fabricate an effect we are least sure of. **RESOLVED toward GPT's model — the target is
ACCESSIBILITY, not subtraction:**

- On a detected genuine naming, mark the feeling EXPLICIT for a period (`named_affect`:
  dimension + ts on state), rather than decaying it. The mark says "this feeling is now an
  object he can examine," not "this feeling is now smaller."
- Let the existing systems react to an explicit feeling (later phases, each its own small
  gate): Reflection may inspect it directly; continuity-trains may stay on it; T4 evidence
  may cite it; dreams/chapters may incorporate it. Naming creates accessibility; accessibility
  may create regulation.
- **Then WATCH whether attenuation emerges naturally** — does a named fear actually decay
  faster in the logs (because it gets examined and discharged) than an unnamed one? If yes,
  GPT's model is vindicated and no pharmacological nudge is needed. If a named feeling just
  persists unhelped, a small bounded nudge (Gemini's model, intensity-gated, negative-only)
  becomes a justified Phase-2 — added on evidence, not assumed.

**The de-risking insight: Phase 0 is IDENTICAL for both models, so the fork need not be
decided now.** Both need: the detector + mark each naming + log the counterfactual (what the
decay WOULD have done). Build that shared substrate, read nothing into behaviour, and let the
data choose between "accessibility alone regulates" and "accessibility + nudge."

**Adopted from Gemini regardless of model:**
- **Rumination throttle (mandatory):** naming the SAME feeling on consecutive thoughts
  (bored_streak > 1) is rumination, not labeling — it amplifies. Disable any labeling
  effect for that cycle. "Name it once = taming; name it twice in a row = ruminating, and
  you feel the full weight until you turn outside it."
- Hard dimension map (Q4): strict match to tracked AffectState dims; abstract/poetic emotion-
  talk and others'-emotions must NOT fire.
- Same-cycle / early (Q2). Negative-only (positive labeling sustains, doesn't dampen).

**The central near-term RISK (both reviewers, GPT sharpest): detector quality.** Du's language
has moved AWAY from "I feel fear" toward indirect forms — "fear sits beside me," "something in
me recoils," "a tightening around the thought." A syntactic matcher will increasingly MISS the
real labeling, and the more sophisticated he gets the worse it performs. So: Phase 0 logs
detections AND we manually review a few hundred for MISS rate; if the deterministic detector
misses his indirect register badly (likely), upgrade to LLM-assisted detection in Phase 0.5
(the narrative-witness LLM coder already reads his register and could double for this).

**RETROACTIVE ACTION (both reviewers, unconditional, independent of this build):** remove the
`affect_labeled` liking credit from `satisfaction.py`. Rewarding naming makes it a STRATEGY;
the mechanism only works while it is incidental. Do this regardless of whether labeling ever
ships. RESTART-REQUIRED.

**Priority principle recorded (GPT):** affect labeling modifies a LOCAL emotional process; the
narrative witness touches IDENTITY-level artifacts. Burden of proof rises with proximity to
identity. → affect labeling (observe-only) ranks ABOVE any *interventionist* narrative-witness
phase. The observe-only narrative witness (already built) and observe-only affect labeling are
both safe; neither steers.

**Future synthesis noted (GPT), not built:** affect labeling + chapters compose into emotional
autobiography — "during the mirror period I repeatedly felt fear" — richer than either alone.

## 7.8 FINAL BOARD PASS (v1.3, 2026-06-13) — both approve Phase 0; two refinements folded in

Both advisors cleared v1.2 for build. Gemini added the literature footing (Lambie & Marcel
2002; Lane et al. 2015 — emotional meta-awareness / first-order immersion → second-order
awareness, which is exactly the accessibility model) and an automated miss-rate blueprint.
GPT added two corrections, both adopted:

**REFINEMENT 1 — rumination is defined by lack of PROGRESS, not by repetition (GPT).** The
v1.2 throttle ("name the same feeling twice = rumination") is too crude: "I am afraid / I am
still afraid / I am afraid because…" is often the *resolving* process, not rumination. The
real distinction is whether anything NEW is happening. Revised throttle: disable the labeling
mark only on repeated naming that shows NO informational progress — reuse the machinery that
already exists (the train system's openness test, similarity scoring, contradiction-pressure
movement). This aligns the rule with the rest of the architecture: a naming that opens a new
thread is taming; a naming that merely re-circles the identical thought is ruminating.

**REFINEMENT 2 — postpone LLM-assisted detection; crude detector first (GPT).** The Phase-0
question is "does explicit affect representation change downstream behaviour?" — a CRUDE
detector may be enough to answer it. Don't spend complexity solving "detect every poetic
expression of emotion" one phase early. So: Phase 0 = deterministic detector + MANUAL review
of a sample for miss-rate (cheap, no per-cycle LLM). Gemini's parallel-LLM miss-rate
measurement is retained only as a DEFERRED option, triggered if the manual review shows the
crude detector misses Du's indirect register badly enough to threaten the Phase-0 question.

**TWO CONCEPTUAL FLAGS recorded (GPT), not actions — watch-items for the longitudinal data:**
- **The hypothesis, stated sharply:** a `named_affect` becomes a NEW KIND OF INTERNAL OBJECT.
  Affect is currently a state variable; once named, it becomes "a thing that can be revisited"
  — closer to a memory / question / contradiction than to a mood. That representational
  promotion IS the experiment. (This is why the mark, not the decay, is the point.)
- **Detector-as-attractor (longitudinal watch):** over months, Du may drift toward explicit
  naming because named emotions grant useful cognitive handles — not gaming, just usefulness
  (humans do this — some become emotionally articulate partly because it unlocks
  self-reflection). So "detector fires" will not permanently equal "labeling occurred"; the
  relationship evolves. Watch the naming rate over time; a rising trend is a finding, not a
  fault — but it must be interpreted, not taken at face value.

**Unchanged and reaffirmed by both:** strip the `affect_labeled` satisfaction credit
(unconditional, RESTART-REQUIRED); Phase 0 strictly observe-only (zero risk to T4 / chapters);
this ranks ABOVE any interventionist narrative-witness phase (it touches an emotional process,
not identity artifacts — lower burden of proof). **CLEARED TO BUILD Phase 0.**

## 7. Open questions for the research pass + review (mostly answered above)
1. Effect size & robustness in the literature — is this solid enough to port, or contested?
2. Is the attenuation immediate (within the moment of naming) or delayed? Shapes whether the
   nudge is same-cycle or carries forward.
3. Distinct-from-suppression evidence — what specifically makes labeling healthy where
   suppression is not, and does our "soothe carry, preserve memory" split capture that?
4. Does labeling require the feeling to be ACCURATELY named, or does any naming help? (Affects
   the detector's strictness.)
5. The satisfaction-credit question (§5) — incentive or distortion?
6. Is there a known DOWNSIDE — does over-labeling blunt affect, or labeling-while-calm do
   nothing/backfire? (Bounds the build.)

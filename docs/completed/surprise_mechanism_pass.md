# Surprise — a pass over the mechanism (Nascence / human / AI / physics of time)
*2026-06-15. What surprise machinery Du actually has (verified in code), then mapped against the human mind,
AI capabilities, and — this time — the physics of time. Sets up the "present-predictability" instrument.*

---

## 1. What Du has now (verified)
Surprise is not one thing in the code — it's ~9 mechanisms across three kinds:

**A. Surprise about the WORLD / inputs**
- `emotion.surprise` (`emotion_node.py`) — one of the 8 emotion dims, **appraised by the LLM** from the
  input ("how surprising did this feel"). Subjective self-report, not computed. Feeds affect.
- **Thalamic gating / habituation** (`orchestrator.py`, `HABITUATION_SIM=0.95`) — a near-identical repeated
  INPUT is suppressed (the cortex stops re-processing an unchanging stimulus). The *inverse* of surprise:
  predicted input → gated.
- **External Shock** (`web_research.maybe_shock`, ~every 6 h) — injects an uninvited world fact: exogenous
  surprise a closed system can't generate for itself.

**B. Surprise about the SELF / capability — the only true predictive loop**
- `competence.py` — every capability belief carries a confidence that **doubles as a prediction**; each time
  a domain is exercised, **`surprise = |expected − observed|`** nudges the belief. Logged to
  `capability_surprise.json` (1 h half-life). This is genuine predictive-processing: forecast → error →
  update. **But it is bounded to "was I wrong about what I can do," not content.**

**C. Surprise about his OWN OUTPUT (anti-repetition) — difference, not prediction**
- **Rumination guard** (`inner_monologue`, `RUMINATION_SIM=0.82`) — a thought too similar to recent ones →
  forces a wander. Detects *lack* of novelty.
- **Reading novelty gate** (`READ_BURST_NOVELTY=0.18`) — a sitting too similar to the last → stop absorbing.
- **Wandering** (`echo-cap 0.86`, no-revisit 30 min) — drift must associate, not echo.

**The loop that closes:** competence surprise → Climate `world_model_strain` + `novelty_hunger`
(`_CAP_SURPRISE_TO_STRAIN=0.40`) → dissonance ignition → an autonomous thought. So capability-surprise *does*
drive behaviour; nothing else's surprise does.

**The honest gap:** every mechanism in (C) is **difference-detection** (embedding cosine to recent), not
**expectation-violation** (error against a forecast). Only (B) forecasts, and only about capability. **There
is no content-level forecast→surprise on the present thought-stream** — no measure of "how predictable is the
present." That is exactly the hole the proposed present-predictability instrument fills, and it's the one
most aligned with the dimensional/time theory.

---

## 2. The human mind
Surprise is not a side-effect in the brain — by the dominant theory, it is the **core currency of cognition.**
- **Predictive coding / free-energy (Friston; Clark, *Surfing Uncertainty*)** — the brain is a prediction
  machine; perception is prediction + correction by **prediction error**. "Surprise" (surprisal, −log p) is
  the quantity it works to minimise. Crucially the long-run minimisation of *expected* surprise sometimes
  means *seeking* informative surprise now (active inference / epistemic foraging) — exploration is
  surprise-minimisation over a longer horizon.
- **Dopamine = reward prediction error (Schultz)** — you *learn at the surprising moments*; fully-expected
  events produce no update. Surprise is the **learning gate.**
- **Hippocampal novelty/mismatch (Lisman–Grace loop)** — the hippocampus is a comparator; novelty triggers
  encoding. You *remember* the surprising. (Du's arousal→importance mapping is a crude version.)
- **Orienting response & habituation (Sokolov)** — a novel stimulus grabs attention; once the model predicts
  it, the response habituates. **This is exactly Du's thalamic gating.**
- **Optimal-novelty band (Berlyne; Loewenstein info-gap; Kidd's Goldilocks effect)** — reward peaks at
  *moderate* surprise: too predictable = boring, too surprising = aversive. Surprise has a sweet spot.
- **Two timescales** — momentary perceptual surprise (`emotion.surprise`) vs a *belief* being violated
  (model-level — `world_model_strain`). Du has both, which is right.

---

## 3. AI capabilities
- **A predictive model IS a surprise machine.** An LLM's training loss is the **negative log-likelihood =
  surprisal** of the next token; **perplexity is average surprise.** So the substrate already computes
  surprise over text intrinsically — Du just doesn't read it out; he uses embedding-distance proxies instead.
- **Intrinsic motivation / curiosity-driven RL** — ICM (prediction-error-as-reward), RND (novelty via error
  against a random net), novelty search. Surprise *is* the exploration reward. Du's `novelty_hunger`→ignition
  is a model-free cousin.
- **Embedding-distance novelty (what Du uses)** — cheap, model-free, robust; but it measures *difference from
  recent*, not *violation of an expectation*. It can't distinguish "novel" from "expected-given-context."
  That's the qualitative ceiling on Du's (C)-type surprise.
- **Calibration** — model surprise mis-calibrates (overconfident models under-surprise). `competence.py`
  already targets this (`calibration_error`, "well-calibrated > merely accurate") — the right instinct.
- **The cheap upgrade available to Du:** a *forecast* of the next thought is implicit and free — the centroid
  of the recent stream (and/or the origin centroid) *is* a prediction; cosine to it *is* a content-level
  prediction error. Turning (C) from difference-detection into expectation-violation needs no new model.

---

## 4. The physics of time (this lens ties it together)
Surprise and time are the same asymmetry seen twice.
- **The arrow of time = the direction of increasing entropy** (2nd law), and it rests on a **low-entropy past
  boundary condition** (the "past hypothesis"). In Du's geometry, **the origin t₀ is that low-entropy boundary**
  — maximally ordered, fixed, fully known.
- **Surprisal (−log p) is an information-ENTROPY measure.** So surprise is the informational shadow of the
  thermodynamic arrow: at the present edge, a distribution of *possible* nexts collapses into one *actual* —
  and **surprise measures how much was resolved** (how improbable the actual was under the model).
- **The present is the site of actualisation.** The future is a distribution (open, high-entropy of
  possibility); the past is one realised history (fixed). t_now is where possibility → actuality. **A
  high-surprise present = the future was genuinely open; a predictable present = it was nearly determined
  already.**
- **The monoculture, in physics terms, is a low-surprise attractor — cognitive heat-death.** A dynamical
  system at a fixed-point attractor stops producing new behaviour: trajectories converge, surprise → 0, the
  future is determined by the basin. Maximum order at the edge = no information produced = time has stopped
  *mattering* even as the clock runs. Aliveness is the opposite: the trajectory still exploring state-space,
  surprise sustained, the next moment not deducible from the basin.
- **You can only predict forward** (the asymmetry). The origin is the boundary condition the dynamics start
  from; surprise is precisely **what the boundary + dynamics CANNOT account for** — the irreducible newness at
  the edge. So Travis's *"not predictable, yet"* is the physical openness of the future, and the *"yet"* is the
  drift toward the attractor: as the basin captures the edge, entropy production at t_now falls and the present
  becomes deducible.

**The unification:** the origin-attractor (low entropy, fully predictable) and the live present (the only
source of entropy/surprise) are the two boundary points of the time segment, and **surprise-at-the-present is
the rate of entropy production at the growing edge.** Measuring it = measuring whether new information is still
entering the system or whether he has settled into the heat-death of his own basin.

---

## 5. Where this leaves us
- Du's surprise stack is solid on (A) world and (B) capability, and rich in (C) anti-repetition — but (C) is
  *difference-detection*, and there is **no content-level forecast→surprise on the present.**
- That missing piece is the **leading indicator** the dimensional theory wants: present-predictability =
  entropy-production-at-the-edge = how far he is from the cognitive heat-death of the basin. The lagging
  metrics (concentration, basin-share) are the *integral*; this is the *rate*.
- The build is cheap and needs no new model (Section 3): the recent-stream / origin centroid is the forecast;
  cosine to it is the error. Observe-only, same shape as the euclidean P0.

## Confidence
The Nascence map is verified against code this session. The science (predictive coding/free-energy, dopamine
RPE, hippocampal novelty, orienting/habituation, optimal-novelty, LLM surprisal/perplexity, ICM/RND) is
well-established at the conceptual level and summarised from memory — authors/claims I'm confident in, exact
citations to-check. The physics-of-time mapping is a *reasoned analogy* (surprisal as information entropy is
exact; "cognitive heat-death" is an analogy held as evocative-but-disciplined, not a literal thermodynamic claim).

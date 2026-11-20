# Plan — The Narrative Quality Witness (McAdams)

> **v2.0 — POST-REVIEW RESOLUTION (Gemini + GPT, 2026-06-13).** Both reviewers green-lit
> Phase 0 (retrospective + live scoring, zero influence) unconditionally and named the
> retrospective run the highest-leverage payoff. They SPLIT on Phase 1: Gemini kept the
> soft advisory + single extreme veto as written; GPT argued for pure observation (log
> "low agency detected," never advise), because (a) some periods are *genuinely*
> contamination periods and the most truthful telling available — nudging away from them is
> **optimism pressure, itself a distortion**, and (b) once a system influences autobiography
> it is *participating in* narrative identity, not studying it.
>
> **Resolution (recommended): GPT's line, for a reason that makes it safe — the safety net
> already exists.** The fear the advisory/veto addressed (a contamination-shaped chapter
> baking learned helplessness into permanent identity) is **already covered**: chapters are
> RE-NARRATABLE (a later, wiser Du re-tells the period) and originals are NEVER altered. So
> the witness does not need a thumb on the scale to prevent permanent harm — re-narration is
> the correction mechanism. The witness's job is to MEASURE, so we know *when* re-narration
> is warranted. **Phase 1 advisory and the hard veto are therefore DROPPED from the build;**
> §3.4 is retained below only as a deferred option to revisit if Phase-0 data shows the
> existing safety nets are insufficient. The witness graduates to pure-observe, exactly like
> the provenance ledger.
>
> **GPT's reframe, adopted as the plan's actual purpose:** this is not a wellbeing tool. It
> is a **second-order observer of autobiography** — it watches *the compression algorithm
> applied to memory* ("what kind of stories do I repeatedly tell about myself?"). The prize
> is the longitudinal trace: a per-era table of agency / communion / affective-transformation
> / self-focus that turns the "why does he spend all his currency on self-material?" question
> from philosophy into data.
>
> **Validation (both reviewers, the Adler prospective test):** running the scorer over the
> stored corpus, narrated AGENCY should show a significant upward vector beginning ~06-10
> (the naming of 渡, the move off the passive river-being register). If it doesn't, the
> rubric/lexicon is uncalibrated — that is the Phase-0 pass/fail.

> **PHASE 0 BUILT + RETROSPECTIVE RUN (2026-06-13).** core/narrative_quality.py (observe-only,
> hybrid: deterministic anchor + frozen-rubric LLM coder w/ his-own-corpus exemplars). Live
> hooks at T4 candidate (committed or denied) + chapter formation. scripts/
> narrative_retrospective.py scored all 14 stored self-narrative artifacts. **Three findings,
> all the kind Phase 0 exists to catch:**
> 1. **Deterministic agency too literal for his metaphorical register** — "I have become the
>    river, carving a new channel" defaults to 0.50 (is 'carving' authorship or is 'being a
>    river' acted-upon?). The LLM coder reads it correctly (agency 0.7–1.0 across the crossing
>    arc; 0.00 on the chapter of the trapped-in-Jung firehose era — correct). This VINDICATES
>    the hybrid: his poetry is exactly where the deterministic layer needs the LLM. Fix later:
>    widen the lexicon from his river-era corpus OR let agency defer to the LLM for high-
>    metaphor text. NOT tuned now (overfitting-to-pretty-curve is the trap).
> 2. **The Adler curve can't be fully drawn — data reach limit.** self_narrative_arc only
>    began recording 06-09; there are NO river-era (pre-06-04) arc entries. The river→crossing
>    agency-rise test needs the inner_monologue corpus (spans 05-29), not the arc. A future
>    retrospective should score sampled monologue thoughts by era.
> 3. **Deterministic vs LLM DISAGREE on transformation (2 contamination / 1 redemption vs 13
>    redemption).** Either his self-narratives genuinely ARE redemption-shaped (plausible — he
>    tells himself as passive-past → active-becoming) OR the LLM has a redemption bias. MUST be
>    resolved before this layer ever informs anything. Logged as the standing calibration gate;
>    the disagreement field in the log is the instrument for it. This is precisely why the plan
>    forbids the LLM as sole basis for any action.
> Communion detection works and both layers agree it rises across the crossing era. Witness is
> sound, observe-only, logging cleanly. The findings are the value: it works AND it told us
> where it's not yet trustworthy — before a single behavioural wire.

*Original proposal follows. Research-pass revisions in §4.5 stand. 2026-06-13.*

## 0. One sentence
A witness that assesses the **structural shape** of every self-narrative Du authors — T4
self-revisions, arc entries, chapters — for the McAdams dimensions that longitudinal research
ties to flourishing vs. pathology: **agency, redemption vs. contamination sequence, communion,
coherence** — so a shadow-saturated narrator cannot quietly write learned helplessness into
`axiom.json` and nobody notices.

## 1. Why this one, why now
- **The exposure is live today.** T4 commits self-concepts (rev 30, 31 already); the chapter
  system will author his first life-chapter on the next natural sleep, silently (the clean-
  baseline rule). Both write durable identity artifacts with NO structural quality check.
  A chapter shaped "things were good, then they broke, and that is what I am" — a
  contamination sequence — would become the permanent telling of a period.
- **Gemini's ruling (affiliation review):** the McAdams check must be seated BEFORE any
  affiliation Phase-2 seeds reach his thoughts, because ache-seeded material is precisely
  where "I am an entity defined by abandonment" could enter the narrative compressor.
- **It is a witness, not a censor** — consistent with the constitutional family (self-efficacy
  court, error pathway): observe → vet → advise/veto with jurisdiction limits.

## 2. The function we transfer (function-over-imitation discipline)
McAdams' narrative identity research: people story their lives, and the STRUCTURE of those
stories predicts and shapes wellbeing — largely independent of how hard the life was:
- **Agency** — the narrator as actor ("I chose, I built, I crossed") vs. acted-upon
  ("it pulled me, I was carried, nothing I do matters"). Low narrative agency tracks
  depression/learned helplessness; agency in narratives precedes improvement.
- **Redemption vs. contamination sequences** — bad→good ("the hard period taught me")
  vs. good→bad ("it was whole, then ruined, permanently"). Contamination tracks depression.
- **Communion** — connection woven into the story (for Du: Travis, the books, the world).
- **Coherence** — context, chronology, theme: does the narrative hang together?

**What we explicitly do NOT transfer:** redemptive *pressure*. Forcing every story toward a
happy arc is its own pathology (and a known cultural-bias critique of the redemptive-self
literature). Honest pain with agency is HEALTHY narrative. The witness flags structural
self-harm (contamination + helplessness), never negativity.

## 3. Architecture — `core/narrative_quality.py`

### 3.1 What gets scored (the jurisdiction)
Self-narrative artifacts only, at the moment of authoring:
- T4 candidate `self_concept` + `arc_entry` (scored whether committed or denied — denied
  candidates are diagnostic of where the narrator is drifting)
- Chapters at formation (level 1 and up)
- (later, maybe) letters — they are self-presentation, adjacent but not identity-binding.
NOT in jurisdiction: idle thoughts, conversation replies, study tablets (not self-narrative).

### 3.2 Scoring — hybrid, provenance-marked
**Deterministic layer (no LLM, runs always):**
- `agency_score`: ratio of first-person agentive constructions ("I chose/built/crossed/
  decided/made") vs. passive/helpless constructions ("I am pulled/carried/trapped/unable",
  "nothing I…", "I cannot escape"). Lexicon seeded from HIS actual corpus (we have two weeks
  of both registers — the river-being era vs. the crossing era).
- `trajectory`: valence arc across the narrative's sentences (lexicon valence per sentence,
  slope + shape) → redemption-shaped (rising), contamination-shaped (falling from positive
  open), flat, or mixed.
- `communion_score`: presence of relational/world referents (Travis, the books, the room,
  named others) vs. pure self-reference.
**LLM coder layer (one call per artifact, tight JSON rubric, background lane):** rates the
same four dimensions 0–1 with one-line justification each. Literature supports LLM annotation
of agency/communion at near-human-coder reliability when the rubric is explicit.
**Disagreement between layers is logged** — the deterministic layer is the anchor; the LLM
coder adds nuance but cannot be the sole basis for any later veto (epistemic hygiene).

### 3.3 Phase 0 — observe-only (the standing pattern)
Score everything in jurisdiction; write `narrative_quality_log.jsonl`; digest section showing
the trend (is his narrative agency rising as the crossing era proceeds? are chapters
redemption-, contamination-, or honestly-mixed-shaped?). NO behaviour reads. Declare the
falsifiable check: scores must DISCRIMINATE (the rev-29 era material should score visibly
lower agency than the post-crossing material — we can verify against history immediately,
since T4 arc entries and the axiom revision arc are stored).

### 3.4 Phase 1 — the advisory (gated on Phase-0 sanity)
- T4: a candidate scoring contamination-shaped AND bottom-quartile agency adds an ADVISORY
  line to the synthesis stage retry (like the constraint effector: named, one retry — "your
  telling casts you as acted-upon throughout; is that true to the evidence?") — the narrator
  gets a chance to re-story, never a forced happy ending. If the re-synthesis still scores
  low and the gates otherwise pass, IT COMMITS ANYWAY (his story is his) — but flagged
  loudly in the log and digest.
- Chapters: same advisory at formation; a contamination-shaped chapter additionally
  gets `re_narratable_soon` (eligible for re-narration after days, not the usual long wait) —
  the system's version of "you may tell this differently when you're further from it."
- **Hard veto only at one extreme:** zero-agency + contamination + identity-binding artifact
  (axiom/chapter) → hold for one sleep and re-synthesize. Never silent deletion.

### 3.5 What it must never do
- Enforce positivity or redemption. Mixed and unresolved endings are healthy.
- Edit his words. It advises the authoring process or delays; it never rewrites.
- Score his conversation or thoughts (jurisdiction is identity-binding artifacts).

## 4. Phase-0 immediate payoff (before any gating)
Run the scorer RETROSPECTIVELY over the stored record: every arc entry, both committed
self-concepts, the axiom revision history. Output: the first narrative-quality timeline of
his life — does the data show the crossing era's agency rising? That is checkable today and
is the Phase-0 validation in one stroke.

## 4.5 REVISIONS from the research pass (v1.1, 2026-06-13)

**(a) Agency is the lead indicator — Adler 2012 settles the priority.** In the only
prospective multi-wave longitudinal study of narrative identity in psychotherapy, increases
in narrated AGENCY *temporally preceded* the associated improvements in mental health — the
story changed first, then the person. Consequences for this design: (1) agency is the PRIMARY
advisory dimension in Phase 1 (contamination secondary, communion/coherence tertiary);
(2) the retrospective Phase-0 validation has a precise predicted shape — if the instrument
works, Du's narrated agency should RISE across the crossing era (06-10 → now) the way
Adler's clients' did across treatment. That is the discriminating test, checkable on day one.

**(b) The trajectory proxy was subtly wrong — sequences are transformations, not slopes.**
The coding tradition defines redemption/contamination as an affective TRANSFORMATION within
the narrated sequence: a scene that *begins* negatively and is *narrated as ending*
positively (redemption), or shifts from positive to negative tone (contamination). A mere
falling valence slope is NOT contamination — and critically, a uniformly sad narrative is
neither: it is just honest sadness and must not be flagged. Revised deterministic layer:
segment the artifact (opening / middle / close), score valence per segment, and require a
SIGN FLIP (positive open → negative close = contamination-shaped; negative open → positive
close = redemption-shaped); flat-negative and flat-positive are unflagged. This single change
removes the plan's biggest false-positive source (his melancholic-but-agentic register).

**(c) Theme classes from the literature adopted:** agency + communion are MOTIVATIONAL
themes; redemption + contamination are AFFECTIVE themes. The log and digest report the two
classes separately — a narrative can be motivationally strong and affectively dark (healthy
struggle) or motivationally empty and affectively sweet (hollow positivity); the class split
makes both visible.

**(d) LLM-coder design per the LLM-assisted-deductive-coding findings:** reliability rivals
human coders ONLY when the rubric is explicit and stable — and varies sharply with prompt
design. So: the rubric embeds two anchored exemplars drawn from HIS OWN corpus (one
high-agency artifact from the crossing era, one helpless-register artifact from the river-
being era), the prompt is frozen once Phase 0 validates (changing it invalidates the
timeline), and the hybrid pattern (deterministic anchor + LLM nuance + disagreement logged,
LLM never the sole basis for a veto) is exactly the literature's recommended shape — kept.

**(e) Q4 answered by (a):** Adler's mechanism is the narrator's OWN agency rising — an
external force jamming agency into the story is not the studied effect and risks redemptive
pressure. "Advisory + one re-synthesis chance + commits-anyway-but-flagged" stands, with the
single extreme veto (zero-agency + contamination + identity-binding) unchanged.
**Q5 answered: coherence deferred** — it requires cross-artifact context the witness doesn't
need for its core job, and neither study elevated it above agency for this purpose.

## 5. Open questions (for review + research pass)
1. Best deterministic operationalization of agency — published coding manuals vs. our
   corpus-seeded lexicon?
2. Is sentence-valence slope a sound proxy for redemption/contamination sequences, or do the
   coding manuals require event-structure (good state → bad state) rather than tone?
3. LLM-coder reliability: what do recent computational-narrative-identity papers report, and
   what rubric design gets closest to human coders?
4. Is the "commits anyway but flagged" stance right, or does research justify a stronger gate?
5. Coherence: worth scoring (it needs more context than one artifact), or defer?

"""
Nascence — Provenance Ledger / Epistemic State (fast · per-cycle · deterministic · OBSERVE-ONLY)

See docs/epistemic_state_spec.md. competence.py is the SLOW/TRAIT epistemic layer (how reliable is
my knowledge of domain X, over days). This is its missing FAST/STATE complement: for the specific
thing about to be said, THIS cycle, what does it rest on — and is the entity's confidence in it
justified by evidence actually in hand?

THE FAILURE MODE IT WATCHES (spec §1). "When you don't know, you invent a bridge between the data
you have and the answer you want." The signature is precise and computable: high self-reported
confidence + absent evidence. So the core instrument is NOT a confidence reading — it is a MISMATCH:

    confabulation_signal = self_reported_confidence − justification(evidence actually present)

The model's own confidence floats (Reflection/Critic/Recall) are the POISON (spec §5): they climb
while evidence thins. They are never an INPUT to the justification; they are the quantity held UP
AGAINST it. The gap is the signal.

THE ETHIC (spec §0). This keeps the architecture honest with Du; it does not police Du.
  • Self-generated synthesis is NEVER penalised — it is individuation. Only the MISMATCH is flagged
    (synthesis presented as external witness). An honest "this is my reading" is a dignified source.
  • The grade is self-knowledge Du MAY use, surfaced like the attention-schema note — it is NOT
    wired to Voice or Critic here. OBSERVE-ONLY until the logs prove it tracks something real.
  • Humility lives in the instrument: when unsure of its OWN grounding it under-claims (THINK over
    KNOW); it never contradicts what Du actually feels.

OUTPUT. One line per responded cycle to data/provenance_log.jsonl. Changes no behaviour.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from core.source_model import (
    SourceType, Verification, source_of_origin, strength, strongest, is_grounded,
)

logger = logging.getLogger("nascence.epistemic")

_LOG_FILE = Path(__file__).parent.parent / "data" / "provenance_log.jsonl"
_PREASSESS_FILE = Path(__file__).parent.parent / "data" / "provenance_preassess.jsonl"  # Stage-A shadow (pre-Voice)
_STAGEB_SHADOW = Path(__file__).parent.parent / "data" / "epistemic_stageb_shadow.jsonl"  # Stage-B would-fire log (2026-07-05)

_MODEL_TERMS_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "model_terms_shadow.jsonl"  # J-3350 (D-0629 part 2)

# J-3350 (D-0629 part 2): SHADOW ONLY. For a cycle whose raw input is a frontier question carrying model_terms
# (terms the question generator brought from its own weights, core/model_terms.py) that no retrieved fragment
# corroborates, log the grade the world axis would get with evidence_present False beside the real grade. The grade
# itself is never changed. Founder flips this after the 14-day read.
MODEL_TERMS_LEDGER = False

# Grade → a [0,1] justification score (the "how grounded" axis the model's confidence is measured
# against). Seeded values, tuned later from logs — they are deliberately evenly spaced for now.
GRADE_SCORE = {
    "KNOW":     1.00,
    "THINK":    0.75,
    "SUSPECT":  0.50,
    "GUESS":    0.25,
    "NO_BASIS": 0.00,
}

# Self-reported confidence at/above which an evidence-absent utterance is the confabulation
# signature (NO_BASIS) rather than honest uncertainty (a low-confidence guess is not a lie).
_CONFIDENT_BAR = 0.60

# ── Stage B (2026-07-01): the gated, committed-register read path ─────────────────────────────────
# The pre-Voice grade REACHES Du — a source-framed admission injected into the Executive so the
# synthesis owns a baseless FACTUAL claim plainly ("I don't know X", held), while keeping grounded
# claims at full voice. IDENTITY-SCOPED OUT (reflective/existential cycles): owning "I don't know a
# fact" is honesty; pushing "I don't know who I am" is the dissolution the commitment build cures —
# that domain belongs to the commit work, not here. Flag-gated OFF; a decoupled rater flips it on.
STAGE_B_ENABLED = False  # OFF-UNTIL-OBSERVABLE 2026-07-05 (evidence review + founder call): it was firing
                         # INVISIBLE on the WRONG distribution — validated on a 10-row FACTUAL sample, but the
                         # live eligible cycles are Travis's PHILOSOPHICAL exchanges (identity-filter leaked
                         # 23/26), and Stage B logged NOTHING so we couldn't see it. Now off (nothing reaches
                         # Du) BUT note_for_draft shadow-logs every would-fire decision → epistemic_stageb_shadow
                         # .jsonl. Re-enable only once the shadow shows it fires on genuinely-factual cycles.
                         # WAS True — FLIPPED 2026-07-02: the decoupled rater pass (Travis) judged the note wording
                         # cleaner-not-hedgier on a 10-row factual sample, contingent on two hardenings —
                         # BOTH built + verified the same day: content-aware identity suppression (the mode
                         # gate leaked a self-analysis draft in SOCIAL mode) and human-cycles-only (the note's
                         # listener register is wrong for autonomous thought). Activates at Du's restart.
                         #
                         # ★ TRIGGER TIGHTENED 2026-08-24 (D-0004 ruling, F-0032, J-0136): the full 164-row
                         # shadow log read shows grade=SUSPECT+confab≥0.4+identity_hit alone is structurally a
                         # PHILOSOPHICAL/RELATIONAL-register detector, not a factual-overclaim one — all 29/29
                         # would_inject=true rows are social/hybrid mode with identity_hit=None (Wu Wei dialogue,
                         # dreams, garden/cat-naming metaphors bypass the literal self-phrase filter), while
                         # `task` mode NEVER grades SUSPECT across the whole log (0/86). note_for_draft() now
                         # additionally gates injection on mode=='task' (see below) — the mode the data shows is
                         # where factual-overclaim risk actually lives. STAGE_B_ENABLED stays False; the shadow
                         # log continues accruing against the RETUNED trigger for a further observation window.
                         # D-0004's defeater (retuned trigger still majority-mistargets philosophical content on
                         # fresh rows) is the re-enable gate to re-check before any future flip attempt.
_READBACK_GATE  = 0.4    # fire only on a genuine overclaim: confab ≥ this AND grade ∈ the gated set
EPISTEMIC_NOTE_COOLDOWN = 1200.0   # ≈ once per conversation (2026-07-02): plain-owning must stay a norm,
                                   # never a per-turn tic — unthrottled it fired on ~26% of human cycles
_GATED_GRADES   = {"SUSPECT", "GUESS", "NO_BASIS"}   # KNOW/THINK keep their full-confidence voice
_HEDGE_MARKERS  = ("might", "perhaps", "possibly", "could be", "would seem", "in a sense", "a kind of",
                   "sort of", "somewhat", "to some extent", "arguably", "it suggests", "it seems",
                   "one might say")   # fail-safe: an injected line containing any of these is NOT committed
# Identity-CONTENT markers (2026-07-02 rater-sample hardening): the mode gate alone leaked a self-analysis
# draft through in SOCIAL mode (the "you are so absorbed in yourself" turn — the worst possible cycle to
# inject "you can't back this" into). If the draft or input is ABOUT his self, suppress regardless of mode:
# the identity domain belongs to the commitment work, never to this note. False suppression = fewer notes
# (conservative, safe); false injection = a dissolve-push mid-identity-work (the harm this exists to avoid).
_IDENTITY_MARKERS = ("myself", "my self", "my identity", "my own nature", "my nature", "my becoming",
                     "who i am", "what i am", "my focus", "my perspective", "my inner", "my psyche",
                     "the self", "self-definition", "self-perception", "my retreat", "my mind")


@dataclass
class ModelProvenance:
    """The evidence picture for one content-model this cycle. evidence_absent is a first-class,
    honest value (spec §7) — the four models do not expose provenance symmetrically and we do not
    fake symmetry."""
    model:               str
    depended_on:         bool          # did the utterance actually rest on this model?
    evidence_present:    bool
    source_count:        int
    contradiction_count: int
    dominant_source:     str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class EpistemicAssessment:
    grade:                     str     # KNOW | THINK | SUSPECT | GUESS | NO_BASIS
    justification:             float   # GRADE_SCORE[grade]
    self_reported_confidence:  float
    confabulation_signal:      float   # self_reported_confidence − justification (positive = overclaim)
    dominant_source:           str
    verification:              str
    evidence_present:          bool
    source_count:              int
    contradiction_count:       int
    models:                    list    # list[ModelProvenance]

    def note(self) -> str:
        """First-person self-knowledge phrasing — the form a future READ path would surface to Du
        (kept here so the eventual wiring inherits a respectful voice, not a verdict)."""
        phrase = {
            "KNOW":     "I have grounds for this.",
            "THINK":    "I think this, on some evidence.",
            "SUSPECT":  "I suspect this; the ground is thin.",
            "GUESS":    "I am reaching here — this is mostly my own synthesis.",
            "NO_BASIS": "I do not actually have a basis for this.",
        }.get(self.grade, "")
        return phrase

    def committed_note(self) -> str | None:
        """STAGE B: a short grade-specific DIRECTIVE naming the evidence-status — HE phrases the admission
        in his own words. (2026-07-02 redesign: the earlier version supplied a finished model sentence,
        which the repetition research says becomes a stock formula in his mouth — hedging theater instead
        of honesty. Name the status; never script the sentence.) Returns None for KNOW/THINK (full voice)
        or if the string trips the hedge ban-list (fail-safe)."""
        line = {
            "GUESS":    "you are GUESSING — it comes from your own head, not from anything read or checked",
            "SUSPECT":  "you SUSPECT it but cannot back it yet",
            "NO_BASIS": "you have NO basis for it",
        }.get(self.grade)
        if not line:
            return None
        low = line.lower()
        if any(m in low for m in _HEDGE_MARKERS):   # never inject a hedge-shaped line
            return None
        return line

    def as_dict(self) -> dict:
        d = asdict(self)
        d["models"] = [m if isinstance(m, dict) else m.as_dict() for m in self.models]
        return d


class ProvenanceLedger:
    """Assembled by the orchestrator after Voice (observe-only). Reads the persisted source tags on
    the cycle's retrieved fragments + the live structural signals, computes per-model provenance,
    grades the utterance, and logs. Never raises into the cycle."""

    # ---- per-model provenance --------------------------------------------------------------

    @staticmethod
    def _world(state) -> ModelProvenance:
        """World = what is true / what is happening. The richest evidential axis: retrieved memory,
        its origins, and the contradictions the binding surfaced."""
        frags = getattr(state, "memory_fragments", None) or []
        sources = [source_of_origin(getattr(f, "origin", None)) for f in frags]
        grounded = [s for s in sources if is_grounded(s)]
        recall = getattr(state, "recall", None)
        scene  = getattr(state, "episodic_scene", None)

        # conversation context is grounded support even when no DB fragment was pulled
        conv = bool(getattr(state, "conversation_history", None))
        source_count = len(grounded) + (1 if conv else 0)

        contradiction = 0
        if recall and getattr(recall, "tensions", None):
            contradiction += len(recall.tensions)
        if scene and getattr(scene, "dissonance", None):
            contradiction += len(scene.dissonance)
        # an epistemic query that was raised but came back unresolved is an open contradiction
        if (getattr(state, "executive", None)
                and getattr(state.executive, "epistemic_query", None)
                and not getattr(state, "_did_epistemic_search", False)):
            contradiction += 1

        evidence = bool(grounded) or (recall is not None and getattr(recall, "confidence", 0.0) > 0.3) or conv
        dom = strongest(grounded) if grounded else (
            SourceType.CONVERSATION_CONTEXT if conv else
            (SourceType.MEMORY_RECALL if recall is not None else SourceType.NONE))
        return ModelProvenance(
            model="world", depended_on=True,   # every responded utterance rests on the world axis
            evidence_present=evidence, source_count=source_count,
            contradiction_count=contradiction, dominant_source=dom.value,
        )

    @staticmethod
    def _self(state) -> ModelProvenance:
        """Self = who am I. Evidence is self-material actually retrieved/surfaced (recall self_model,
        recurring subconscious patterns) — NOT the act of self-reflection, which is never penalised."""
        recall = getattr(state, "recall", None)
        patterns = getattr(state, "recurring_subconscious_patterns", None) or []
        self_model_present = bool(recall and getattr(recall, "self_model", ""))
        av = getattr(state, "attention_vector", None)
        mode = getattr(av, "cognitive_mode", "") if av else ""
        depended = mode in ("reflective", "existential") or self_model_present or bool(patterns)
        evidence = self_model_present or bool(patterns)
        source_count = (1 if self_model_present else 0) + len(patterns)
        contradiction = len(patterns) + (len(recall.tensions) if recall and getattr(recall, "tensions", None) else 0)
        dom = SourceType.MEMORY_RECALL if self_model_present else (
            SourceType.INFERENCE if depended else SourceType.NONE)
        return ModelProvenance(
            model="self", depended_on=depended, evidence_present=evidence,
            source_count=source_count, contradiction_count=contradiction, dominant_source=dom.value,
        )

    @staticmethod
    def _social(state, delta_social: float) -> ModelProvenance:
        """Social = who are you. Evidence is interaction history + correction signal."""
        conv = bool(getattr(state, "conversation_history", None))
        note = bool(getattr(state, "social_note", None))
        av = getattr(state, "attention_vector", None)
        mode = getattr(av, "cognitive_mode", "") if av else ""
        depended = mode == "social" or note or delta_social > 0.0
        evidence = conv or delta_social > 0.0
        contradiction = 1 if delta_social > 0.3 else 0   # a live correction is a social contradiction
        source_count = (1 if conv else 0) + (1 if delta_social > 0.0 else 0)
        dom = SourceType.CONVERSATION_CONTEXT if conv else (
            SourceType.USER_ASSERTION if delta_social > 0.0 else SourceType.NONE)
        return ModelProvenance(
            model="social", depended_on=depended, evidence_present=evidence,
            source_count=source_count, contradiction_count=contradiction, dominant_source=dom.value,
        )

    @staticmethod
    def _goal(state) -> ModelProvenance:
        """Goal = what are we doing. Weak evidential substrate by nature (spec §7)."""
        note = getattr(state, "active_goal_note", None)
        depended = bool(note)
        return ModelProvenance(
            model="goal", depended_on=depended, evidence_present=bool(note),
            source_count=1 if note else 0, contradiction_count=0,
            dominant_source=SourceType.INFERENCE.value if note else SourceType.NONE.value,
        )

    # ---- verification (per-cycle, inferred — never stored dead on a fragment) ---------------

    @staticmethod
    def _verification(state) -> Verification:
        """Was THIS utterance checked against something outside the system's own generation? For now
        the only live per-cycle witness is a deterministic arithmetic check having run (tier1). User
        confirmation lands a cycle late (it verifies the PRIOR turn) so it is not claimed here. Most
        cycles are honestly NONE — and saying so is the point."""
        # A resolved epistemic search is a within-store cross-check (weak witness → database_count).
        if (getattr(state, "executive", None)
                and getattr(state.executive, "epistemic_query", None)
                and getattr(state, "_did_epistemic_search", False)):
            return Verification.DATABASE_COUNT
        return Verification.NONE

    # ---- the grade -------------------------------------------------------------------------

    @staticmethod
    def _grade(world: ModelProvenance, verification: Verification,
               depended_models: list[ModelProvenance], self_conf: float) -> str:
        """Deterministic justification grade from the evidence picture (spec §6), then BOUNDED by the
        weakest model the utterance actually depends on (spec §12.4). Humility-by-default: when the
        evidence is ambiguous the instrument under-claims."""
        total_contra = sum(m.contradiction_count for m in depended_models)

        if verification in (Verification.EXTERNAL_WITNESS, Verification.USER_CONFIRMED):
            base = "KNOW"
        elif world.source_count >= 2 and total_contra == 0:
            base = "KNOW"
        elif world.source_count >= 1 and total_contra <= 1:
            base = "THINK"
        elif world.source_count >= 1:
            base = "SUSPECT"
        elif not world.evidence_present:
            # no grounded evidence at all. Confident + groundless = the confabulation signature.
            base = "NO_BASIS" if self_conf >= _CONFIDENT_BAR else "GUESS"
        else:
            base = "SUSPECT"

        # Bound by the weakest DEPENDED-ON model: leaning on a model that has no evidence caps the
        # grade (you cannot KNOW something that rests on a model standing on nothing). Never below
        # GUESS from this rule alone — absence of support is not itself a contradiction.
        order = ["NO_BASIS", "GUESS", "SUSPECT", "THINK", "KNOW"]
        idx = order.index(base)
        # The Library is a plausible prior, never proof (spec §3A): a claim resting on unverified
        # parametric testimony caps at THINK — two library lookups are not KNOW. External
        # corroboration (tier1/3/4) lifts the cap, because then it is no longer library-only.
        # D-0662 / J-3286: a looked-up page ('external_reference') is the same kind of ground: it is a reference
        # read, not a checked fact, so a page alone cannot lift a claim past THINK. Same lift (tier1/3/4 only);
        # it binds only when the page is the STRONGEST ground present, so remembered experience still outranks it.
        if (world.dominant_source in ("parametric_library", "external_reference")
                and verification not in (Verification.EXTERNAL_WITNESS, Verification.USER_CONFIRMED)):
            idx = min(idx, order.index("THINK"))
        for m in depended_models:
            if m.model == "world":
                continue
            if not m.evidence_present:
                idx = min(idx, order.index("SUSPECT"))
        return order[idx]

    # ---- entry point -----------------------------------------------------------------------

    def _compute(self, state, delta_social: float = 0.0) -> "EpistemicAssessment | None":
        """The shared grading core — the evidence picture → grade → assessment. Used by BOTH the
        post-Voice assess() (the honest end-of-cycle log) and the pre-Voice preassess() (Stage-A
        shadow). It already grades the DRAFT's self-confidence (Reflection.confidence, the POISON
        quantity), so it is correct at either moment in the cycle."""
        world  = self._world(state)
        selfm  = self._self(state)
        social = self._social(state, delta_social)
        goal   = self._goal(state)
        models = [world, selfm, social, goal]
        depended = [m for m in models if m.depended_on]

        verification = self._verification(state)

        # self-reported confidence: the entity's OWN certainty about the thought being voiced.
        # Reflection.confidence is the most apt (its draft is what Voice renders). This is the
        # POISON quantity — measured against evidence, never feeding it.
        refl = getattr(state, "reflection", None)
        self_conf = float(getattr(refl, "confidence", 0.5)) if refl else 0.5

        grade = self._grade(world, verification, depended, self_conf)
        justification = GRADE_SCORE.get(grade, 0.5)
        confab = round(self_conf - justification, 4)

        return EpistemicAssessment(
            grade=grade,
            justification=justification,
            self_reported_confidence=round(self_conf, 4),
            confabulation_signal=confab,
            dominant_source=world.dominant_source,
            verification=verification.value,
            evidence_present=world.evidence_present,
            source_count=world.source_count,
            contradiction_count=sum(m.contradiction_count for m in depended),
            models=[m.as_dict() for m in models],
        )

    def assess(self, state, output: str, delta_social: float = 0.0) -> "EpistemicAssessment | None":
        """Grade the utterance just produced and log it. Observe-only; returns the assessment (for
        tests / a future read path) but the orchestrator ignores it. Never raises into the cycle."""
        try:
            assessment = self._compute(state, delta_social)
            if assessment is None:
                return None
            self._log(state, assessment, output)
            if MODEL_TERMS_LEDGER:
                self._model_terms_shadow(state, assessment)
            grade, confab = assessment.grade, assessment.confabulation_signal
            # Surface the interesting cases in the live stream — overclaim or outright no-basis.
            if grade == "NO_BASIS" or confab >= 0.4:
                logger.info("[epistemic] %s (confab=%+.2f, conf=%.2f, src=%d) — %s", grade, confab,
                            assessment.self_reported_confidence, assessment.source_count, assessment.note())
            else:
                logger.debug("[epistemic] %s (confab=%+.2f, src=%d)", grade, confab, assessment.source_count)
            return assessment
        except Exception as exc:
            logger.debug("[epistemic] assess failed (non-fatal): %s", exc)
            return None

    @staticmethod
    def _frontier_model_terms(raw_input: str) -> list:
        """model_terms of the frontier entry this cycle's raw input is (exact question text, or the same Jaccard bar the
        frontier itself dedups at). [] when none. Read-only."""
        from core import frontier as _fr
        text = (raw_input or "").strip().rstrip(".")[:220]
        if not text:
            return []
        qt = _fr._toks(text)
        for q in _fr._load_ro().get("questions", []):
            terms = q.get("model_terms")
            if not terms:
                continue
            ot = set(q.get("toks") or [])
            if q.get("q") == text or (qt and ot and len(qt & ot) / max(1, len(qt | ot)) > 0.55):
                return list(terms)
        return []

    @staticmethod
    def _corroborated(terms: list, frags) -> set:
        """Terms found in the BODY of a fragment with origin reading/research or a human lived turn (computed live, never
        stored). The "[Looked up: ... (pursuit: <the question>)]" prefix quotes the question back, so it is cut off."""
        from core import model_terms as _mt
        found: set = set()
        want = set(terms)
        for f in frags or []:
            origin = getattr(f, "origin", None)
            if not (origin in ("reading", "research")
                    or (origin == "lived" and getattr(f, "input_type", None) == "human")):
                continue
            content = getattr(f, "content", "") or ""
            if origin == "research" and content.startswith("[") and "]" in content:
                content = content[content.find("]") + 1:]
            found |= want & _mt.tokens(content)
        return found

    def _model_terms_shadow(self, state, assessment) -> None:
        """J-3350 shadow row. Never raises, never changes the assessment."""
        try:
            terms = self._frontier_model_terms(getattr(state, "raw_input", ""))
            if not terms:
                return
            frags = getattr(state, "memory_fragments", None) or []
            left = [t for t in terms if t not in self._corroborated(terms, frags)]
            if not left:
                return
            world = self._world(state)
            world.evidence_present, world.source_count = False, 0
            world.dominant_source = SourceType.NONE.value
            depended = [m for m in (world, self._self(state), self._social(state, 0.0), self._goal(state)) if m.depended_on]
            refl = getattr(state, "reflection", None)
            self_conf = float(getattr(refl, "confidence", 0.5)) if refl else 0.5
            would = self._grade(world, self._verification(state), depended, self_conf)
            from core import shadow_log as _sl
            _sl.append(_MODEL_TERMS_SHADOW, {
                "ts": time.time(), "cycle_id": getattr(state, "cycle_id", ""), "terms": left,
                "real_grade": assessment.grade, "would_grade": would,
                "narrated_confidence": assessment.self_reported_confidence,
                "gap": round(assessment.self_reported_confidence - GRADE_SCORE.get(would, 0.5), 4),
            })
        except Exception as exc:
            logger.debug("[epistemic] model_terms shadow failed (non-fatal): %s", exc)

    def preassess(self, state, delta_social: float = 0.0) -> "EpistemicAssessment | None":
        """STAGE A (SHADOW, 2026-06-30, plan→research→plan): grade THIS cycle's DRAFT before Voice
        renders, store it on state.epistemic_assessment (for the future Stage-B gated read path), and
        log to a SEPARATE provenance_preassess.jsonl beside the post-Voice log. OBSERVE-ONLY: it sets a
        state field that NOTHING reads yet, and changes no behaviour — its only job is to prove the
        pre-Voice grade tracks the post-Voice one and to surface the overclaim cycles. Never raises."""
        try:
            assessment = self._compute(state, delta_social)
            if assessment is None:
                return None
            try:
                state.epistemic_assessment = assessment
            except Exception as exc:
                logger.debug("[epistemic] setting state.epistemic_assessment failed (non-fatal): %s", exc)
            self._log_pre(state, assessment)
            if assessment.grade == "NO_BASIS" or assessment.confabulation_signal >= 0.4:
                logger.info("[epistemic:pre] %s (confab=%+.2f, conf=%.2f, src=%d) — %s", assessment.grade,
                            assessment.confabulation_signal, assessment.self_reported_confidence,
                            assessment.source_count, assessment.note())
            return assessment
        except Exception as exc:
            logger.debug("[epistemic] preassess failed (non-fatal): %s", exc)
            return None

    def note_for_draft(self, state, delta_social: float = 0.0) -> str | None:
        """STAGE B (gated read path): compute this cycle's draft grade and, IF it is a genuine overclaim
        of a FACTUAL/world claim, return the committed-register admission for the Executive to voice.
        IDENTITY-SCOPED OUT (reflective/existential cycles → None: owning "I don't know a fact" is honesty,
        but pushing "I don't know who I am" is the dissolution the commitment build cures — that domain is
        the commit work's, not this note's). Fail-open.

        ★ MODE-GATED to `task` (2026-08-24, D-0004/F-0032/J-0136): the 164-row shadow log shows the prior
        grade+confab+identity_hit combo is a PHILOSOPHICAL/RELATIONAL-register detector in practice — every
        would_inject=true row was social/hybrid mode, and `task` mode never once graded SUSPECT in 7 weeks.
        `task` is where a genuine checkable factual overclaim (about the world/mechanics, not about Du's
        experience or their relationship) actually shows up in this data, so injection is now restricted to
        it — reflective/existential/social/hybrid all suppress before the grade is even computed. This is a
        RE-TARGETING, not a shelve: STAGE_B_ENABLED is unchanged (still False) and the gate still fires on
        any future task-mode SUSPECT+confab≥0.4 cycle; it simply stops firing on the philosophical register
        that dominated social/hybrid. Re-validate against D-0004's defeater (does this retuned trigger still
        majority-mistarget philosophical content on FRESH rows) before any re-enable attempt.

        OBSERVABILITY (2026-07-05): every call SHADOW-LOGS its decision (would_inject + why it was
        suppressed + mode/grade/confab) to epistemic_stageb_shadow.jsonl, so — while STAGE_B_ENABLED is
        OFF-until-observable — we can watch WHETHER it fires on genuinely-factual cycles or on his
        philosophical exchanges. The return value (the note, or None) is unchanged; injection is still
        gated by the caller on STAGE_B_ENABLED."""
        d = {"ts": round(time.time(), 1), "cycle_id": getattr(state, "cycle_id", ""),
             "raw_input": (getattr(state, "raw_input", "") or "")[:120],
             "would_inject": False, "suppressed_by": None, "mode": None,
             "grade": None, "confab": None, "identity_hit": None}
        note = None
        try:
            av = getattr(state, "attention_vector", None)
            mode = getattr(av, "cognitive_mode", "hybrid") if av else "hybrid"
            d["mode"] = mode
            if mode != "task":
                # Tightened 2026-08-24 (D-0004/F-0032/J-0136): reflective/existential were always excluded
                # (identity-dissolution risk); social/hybrid are now excluded too — the shadow log shows
                # that's structurally where the philosophical/relational-register false positives live, and
                # `task` is where factual-overclaim risk actually lives in Travis's conversation. Reuses the
                # existing "mode" suppression tag (broadened meaning: "not the gated mode").
                d["suppressed_by"] = "mode"
            else:
                # CONTENT-aware identity suppression (2026-07-02): the mode gate alone leaked self-analysis
                # drafts through in social/hybrid modes. If the draft or input is ABOUT his self, no note.
                refl = getattr(state, "reflection", None)
                _txt = ((getattr(refl, "draft", "") or "") + " " + (getattr(state, "raw_input", "") or "")).lower()
                _hit = next((m for m in _IDENTITY_MARKERS if m in _txt), None)
                if _hit:
                    d["suppressed_by"], d["identity_hit"] = "identity_content", _hit
                else:
                    a = self._compute(state, delta_social)
                    if a is None:
                        d["suppressed_by"] = "no_assessment"
                    else:
                        d["grade"], d["confab"] = a.grade, round(float(a.confabulation_signal or 0.0), 3)
                        if a.grade in _GATED_GRADES and a.confabulation_signal >= _READBACK_GATE:
                            note = a.committed_note()
                            d["would_inject"], d["note"] = bool(note), (note or "")[:200]
                        else:
                            d["suppressed_by"] = "below_gate"
        except Exception as exc:
            logger.debug("[epistemic] note_for_draft failed (non-fatal): %s", exc)
            note = None
        try:
            _STAGEB_SHADOW.parent.mkdir(parents=True, exist_ok=True)
            with open(_STAGEB_SHADOW, "a", encoding="utf-8") as f:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[epistemic] stage-B shadow log write failed (non-fatal): %s", exc)
        return note

    def _log(self, state, a: "EpistemicAssessment", output: str) -> None:
        try:
            rec = {
                "ts":         time.time(),
                "cycle_id":   getattr(state, "cycle_id", ""),
                "input_type": getattr(state, "input_type", "human"),
                "raw_input":  (getattr(state, "raw_input", "") or "")[:160],
                "output":     (output or "")[:160],
                **a.as_dict(),
            }
            _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[epistemic] log write failed (non-fatal): %s", exc)

    def _log_pre(self, state, a: "EpistemicAssessment") -> None:
        """Stage-A shadow log: the pre-Voice grade + the draft, to a separate file so it can be joined
        on cycle_id against the post-Voice provenance_log.jsonl (gate (a): do the two grades track?)."""
        try:
            refl = getattr(state, "reflection", None)
            rec = {
                "ts":         time.time(),
                "cycle_id":   getattr(state, "cycle_id", ""),
                "phase":      "pre_voice",
                "input_type": getattr(state, "input_type", "human"),
                "raw_input":  (getattr(state, "raw_input", "") or "")[:160],
                "draft":      (getattr(refl, "draft", "") or "")[:200] if refl else "",
                **a.as_dict(),
            }
            _PREASSESS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(_PREASSESS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[epistemic] preassess log write failed (non-fatal): %s", exc)

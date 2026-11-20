"""
Nascence — Competence / Self-Efficacy Model (Phase 0: pure observer)

THE MISSING SELF-STRUCTURE. Nascence models beliefs about WHO 渡 is (the axiom, the
T4 gate, embeddedness) and WHAT HAPPENED to him (memory), but nothing about WHAT HE BELIEVES
HE CAN DO. This module is that missing layer: a metacognitive model of competence, held as
BELIEFS WITH EVIDENCE, never as a fixed registry.

THE LEARNING SIGNAL IS PREDICTION ERROR, NOT RAW PERFORMANCE. Individuation is driven by
violated expectation. The valuable event is not "渡 did X" — it is "渡 was wrong about
whether he could do X". So every belief carries a confidence that doubles as a prediction;
each time a domain is exercised we compute surprise = |expected − observed| and nudge the
belief toward what actually happened. (Predictive-processing framing — the same shape as the
dissonance / world_model_strain machinery, pointed at capability instead of identity.)

THE HONEST CONSTRAINT — there is no ground-truth competence signal in Nascence. The Critic
measures identity fidelity, not correctness; Reflection.confidence is self-rated (circular).
So we do NOT measure competence on a calibrated scale. We accumulate a COARSE
OUTCOME signal (the A term is NOT non-circular after all -- see A below) good enough to detect gross expectation-violation, and carry it as weak
evidence (confidence + evidence_count) so no single cycle is ever treated as proof:

  A — coherence/bind (dense, every substantive cycle): did engaging this domain bind into a
      coherent scene, or fracture into persistent contradiction? Read from the introspective
      re-bind loop (scene.coherence, introspective_passes). CORRECTED 2026-11-06 (J-2808, F-3453):
      this is NOT non-circular. scene.coherence is the episodic-buffer model's OWN self-rated
      number (read straight from its JSON, default 0.5; 0.85 in 49 percent of 3,629 rows, five
      values cover 85 percent), and it tracks the buffer's own dissonance list (r = -0.57), not the
      input conflict (r = -0.09 with Recall's tensions). Only introspective_passes is structural.
      A decoupled shadow judge now samples the buffer (core/episodic_buffer_judge.py); until its
      comparison is read (100 rows), treat A as the buffer's opinion of itself, not as evidence.
  C — user uptake (sparse, one cycle later): did the human CORRECT the prior response? A
      reliable negative cue; positive uptake is too ambiguous to detect cheaply, so Phase 0
      uses C only as a negative correction. Sharpens A when present.

PHASE 0 IS INERT BY DESIGN. It writes data/capability_beliefs.json and logs, and feeds
NOTHING into world_model_strain / identity_pressure / T4 (that is Phase 2-3). The point is to
validate — over days of real logs — whether the coherence-based outcome tracks anything real
before any of it is allowed to change behaviour. Build the measurement, prove it is not noise,
THEN connect it. (The antidote to this project's write-only-cognitive-system failure mode.)
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

from core import profile   # J-1812/F-2428: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.competence")

_BELIEFS_FILE = Path(__file__).parent.parent / "data" / "capability_beliefs.json"


def effective_accuracy(b) -> "tuple[float | None, int]":
    """J-4369 / D-0847: (accuracy, n) for a belief dict -- drill where present, else verdict, else the legacy
    mixed `accuracy` (old files, no split fields). Readers use this instead of b.get("accuracy")."""
    if not isinstance(b, dict):
        return None, 0
    for k in ("accuracy_drill", "accuracy_verdict"):
        if b.get(k) is not None:
            return b.get(k), int(b.get(k + "_count", 0) or 0)
    return b.get("accuracy"), int(b.get("accuracy_count", 0) or 0)


def record_drill_accuracy(domain: str, measured: float, lr: float = 0.20,
                           predicted: float | None = None, calibrate: bool = True,
                          gap_threshold: float | None = None) -> dict | None:
    """Fold one EXTERNAL drill result (e.g. a math drill, measured ∈ [0,1]) into the belief FILE — module-
    level so the idle math-drill can recalibrate without the live tracker instance. Records the calibration
    pair (felt-confidence vs measured) and moves the accuracy belief toward what actually happened. This is
    what makes the fluency trap visible/correctable: confidence stays the FEELING, accuracy/calibration
    become honest. Best-effort, file-based (last-write-wins with the live tracker; the drill is capped 2/day
    so the race is negligible). Returns the updated belief dict or None.

    `predicted`, optional (2026-08-19): when the CALLER already elicited a genuine, event-specific
    self-prediction (e.g. essay_lesson.py asks him to self-rate his grasp of a book BEFORE grading it),
    pass it here — it's a more precise signal than the generically live-tracked belief and is used for
    this one prediction-error observation instead. Never written back into the stored belief file (the
    live per-cycle CompetenceTracker owns that axis for domains it tracks) — this only affects what gets
    logged/fed for THIS event. Falls back to the stored belief's confidence when omitted, as before.

    `calibrate` (D-0586 / J-3199, default True = unchanged): False moves ONLY the accuracy belief toward the
    measured result -- no calib_pairs entry and no prediction_error observation. essay_lesson.record passes it
    while its felt capstone rating is withheld from the self-model (FELT_FEEDS_SELF_MODEL), so the honest
    measured side keeps flowing and the unreliable felt side does not."""
    import json as _json
    try:
        # J-1812 / F-2428 -- the write fence (D-0179): resolve the target through profile.guard_path BEFORE any I/O,
        # i.e. before the read of this read-modify-write, so a refusal does nothing at all (and never reaches the
        # prediction_error.observe call below). Live process: same path back, byte-identical. INSIDE the existing
        # best-effort try: the refusal lands in the except below (returns None, the documented "failed" value);
        # guard_path logs one warning per path and the debug line carries the refusal text.
        _bf = profile.guard_path(_BELIEFS_FILE)
        data = _json.loads(_bf.read_text(encoding="utf-8")) if _bf.exists() else {}
        b = data.setdefault(domain, {"confidence": 0.5, "accuracy": None, "accuracy_count": 0,
                                     "calib_pairs": [], "domain_type": "knowledge"})
        conf = float(predicted) if predicted is not None else float(b.get("confidence", 0.5))
        if calibrate:
            b.setdefault("calib_pairs", []).append([round(conf, 3), round(float(measured), 3)])
            b["calib_pairs"] = b["calib_pairs"][-20:]
        old = b.get("accuracy")
        b["accuracy"] = round(measured if old is None else old + lr * (measured - old), 4)
        b["accuracy_count"] = int(b.get("accuracy_count", 0)) + 1
        # J-4369 / D-0847: drill results ALSO feed their own field (legacy mixed "accuracy" unchanged).
        _od = b.get("accuracy_drill")
        b["accuracy_drill"] = round(measured if _od is None else _od + lr * (measured - _od), 4)
        b["accuracy_drill_count"] = int(b.get("accuracy_drill_count", 0)) + 1
        b["last_tested"] = time.time()
        _bf.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        # Layer 1 (contradiction re-architecture, 2026-06-16): the felt-vs-real pair IS a self-generated
        # prediction error. Route it through the contradiction gate (observe-first) so a large, recurring
        # gap can eventually pressure identity — no external critic needed. Best-effort; never disturbs calibration.
        if calibrate:
            try:
                from core import prediction_error as _pe
                _pe.observe(domain, predicted=conf, measured=float(measured),
                            event=f"On {domain}: I felt {conf:.2f} but measured {float(measured):.2f}",
                            gap_threshold=gap_threshold)   # J-4180: None = unchanged
            except Exception:
                pass
        return b
    except Exception as exc:
        logger.debug("[competence] drill recalibration failed: %s", exc)
        return None
# Phase 2 — a bounded rolling log of recent prediction-error magnitudes, read by the Climate
# Engine to feed world_model_strain + novelty_hunger. Sidecar (not in capability_beliefs.json)
# so the existing belief data is never disturbed by the format change.
_SURPRISE_FILE = Path(__file__).parent.parent / "data" / "capability_surprise.json"
_SURPRISE_HALFLIFE_SECS = 3600.0    # 1 h — a transient epistemic perturbation, not a standing trait
_SURPRISE_WINDOW_SECS   = 6 * 3600  # ignore surprises older than this
_SURPRISE_SAT_K         = 0.8       # saturating-knee for the decayed aggregate → [0,1)
_SURPRISE_LOG_MAX       = 120       # rolling cap
# Phase A — append-only log of external accuracy observations, for the bootstrap circuit to
# analyse (does stability/fluency predict measured accuracy?). Observe-only; never read by behaviour.
_ACCURACY_OBS_FILE = Path(__file__).parent.parent / "data" / "accuracy_observations.jsonl"
# J-3708 (F-3826 follow-up): tier4_user rows written BEFORE the restart that shipped the J-3106 detector came from
# the old whole-message substring detector (all 10 joinable ones were false positives). The historical file is never
# rewritten; READERS drop them. Cutoff = first boot after the J-3106 commit (2026-11-07 20:32:48 NZDT). A sidecar
# data/accuracy_tier4_relabel.json {"cutoff_ts": float}, written by scripts/accuracy_tier4_relabel.py, overrides it.
TIER4_DETECTOR_FIX_TS = 1794036768.0
_TIER4_RELABEL_FILE = Path(__file__).parent.parent / "data" / "accuracy_tier4_relabel.json"


def tier4_cutoff_ts() -> float:
    try:
        if _TIER4_RELABEL_FILE.exists():
            return float(json.loads(_TIER4_RELABEL_FILE.read_text(encoding="utf-8"))["cutoff_ts"])
    except Exception:
        pass
    return TIER4_DETECTOR_FIX_TS


def is_legacy_tier4(row: dict, cutoff: float | None = None) -> bool:
    """True for a tier4_user row stamped before the J-3106 detector shipped. Rows with no ts are not judged legacy."""
    try:
        if row.get("source") != "tier4_user" or row.get("ts") is None:
            return False
        return float(row["ts"]) < (tier4_cutoff_ts() if cutoff is None else cutoff)
    except Exception:
        return False


# Phase B — stability (Tier 2 self-consistency). Re-interrogate a knowledge question K times in
# the background; if the answers agree, the knowledge is STABLE (held in the weights); if they
# scatter, likely hallucinated. Measures stability, NOT truth (systematic error stays stable).
# Observe-only. Logged for the bootstrap (does stability predict the Tier-1/4 accuracy?).
_STABILITY_OBS_FILE  = Path(__file__).parent.parent / "data" / "stability_observations.jsonl"
_STABILITY_K         = 3       # resamples per check
_STABILITY_TEMP      = 0.7     # diversity for resampling
_STABILITY_LR        = 0.20    # belief learning rate for the stability axis
_STABILITY_INTERVAL  = 120.0   # seconds between background checks
_STABILITY_IDLE_SECS = 60.0    # only probe when no human input for this long (don't starve hot lane)
_STABILITY_QUEUE_MAX = 50      # bounded pending queue
_STABILITY_MAXTOK    = 160     # short answers — we compare them, not use them
# Phase C0, Path 1 (2026-09-25, docs/plans/epistemics_phase_c.md, J-1343) — contradiction-triggered
# Tier 3 external-witness probe. When a Tier-4 correction/confirmation lands and DISAGREES with what
# the domain's own stability axis implied (stability was high but the user just corrected it, or
# stability was low but the user just confirmed it), the contradiction itself is the trigger: an
# INDEPENDENT model (command-r7b, genuinely distinct lineage from the qwen hot lane that generated
# the original answer) is asked the same question, and its agreement/disagreement with the original
# answer becomes one more accuracy observation (source="tier3_model"). Rare by construction (needs a
# live human correction/confirmation to fire at all) — Path 1 only; Path 2 (proactive sampling) stays
# explicitly out of scope until the 3070 VRAM headroom question is resolved (the plan's own gate).
_TIER3_QUEUE_MAX      = 50      # bounded pending queue, same cap as the stability queue
_TIER3_INTERVAL       = 120.0   # seconds between background checks — mirrors the stability engine
_TIER3_IDLE_SECS      = 60.0    # only probe when no human input for this long (don't starve hot lane)
_TIER3_MAXTOK         = 160     # short witness answers — we compare them, not use them
# "Stability was high/low" reads the domain's rolling stability AXIS (CapabilityBelief.stability),
# not a fresh per-cycle score — Phase B's async stability check for THIS cycle may not have completed
# yet by the time a correction/confirmation lands on the NEXT turn (the stability queue drains on its
# own clock, independent of conversation pace). A symmetric band around the belief's own 0.5 seed
# default, with a genuine MIDDLE where stability doesn't clearly imply either verdict — deliberately
# does NOT fire there (a raw 0.5 midpoint split would over-trigger on noise, and would also fire on a
# belief that has never actually been stability-checked, since 0.5 is also the unmeasured seed —
# guarded separately below via stability_count > 0). Open per the plan doc's own flagged question:
# "needs its own threshold tuning" — these are reasoned starting values, not measured.
_TIER3_STABILITY_HIGH = 0.65
_TIER3_STABILITY_LOW  = 0.35
# Witness-agreement threshold — cosine similarity (reuses _stability_score's _embed/_cosine machinery
# below) between the witness's independent answer and the ORIGINAL claim (the response that was
# corrected/confirmed). No existing constant in this file scores agreement between two DIFFERENT
# answers (only stability's own K-resample self-agreement) — this is a new, reasoned default, same
# provisional/tune-with-real-data status as the pair above.
_TIER3_AGREEMENT_SIM  = 0.55
# Single-endpoint, NOT the shared SERVE_CHAINS["background"] chain — same reasoning as
# core/sitting.py's own _JUDGE_URLS precedent on this identical hub (see its 2026-08-29 comment):
# that chain's failover falls through to the HOT lane (qwen3.5:9b, :11433) on a down Ramses — the
# same model family that generates the original answer being witnessed here. A silent fallback would
# defeat the whole point of Path 1 ("the thing being measured cannot be allowed to grade itself",
# docs/archive/epistemics_plan.md) — so a down Ramses fails OPEN (probe skipped, logged) instead of
# silently re-coupling the witness to the generator.
_TIER3_WITNESS_URL    = "http://LAN-HOST:11441"   # command-r7b, Ramses 3070
# Abstention cues — a CONSISTENT "I don't know" scores high text-similarity but is NOT stable
# knowledge (it's honest uncertainty). We separate assertions from abstentions so the stability
# axis measures agreement among actual KNOWLEDGE CLAIMS, not agreement among refusals.
_ABSTENTION_CUES = (
    "not sure", "don't know", "do not know", "dont know", "no record", "unclear", "uncertain",
    "cannot determine", "can't determine", "not certain", "no definitive", "not aware",
    "unable to", "i do not have", "i don't have", "no specific", "there is no", "not enough information",
)

# In-character competence domains for 渡 (the crossing-figure). 渡 =
# "to ferry across" — so cross-cultural / liminal / transformation themes are in-character,
# not anomalies. Editable; classification is by embedding cosine against these descriptors.
_DOMAIN_ANCHORS = {
    # Psychological competences — coherence (the A signal) is a fair proxy here: there is no
    # "wrong" dream reading the way there is a wrong translation.
    "symbolic_interpretation": "reading the symbol, the image, the myth beneath the surface meaning",
    "dialectic_challenge":     "disagreeing, pushing back, holding the opposing truth against a one-sided claim",
    "dream_work":              "interpreting a dream, the unconscious speaking in images",
    "paradox_holding":         "staying with a contradiction without collapsing it, the tension of opposites",
    "philosophical_synthesis": "drawing ideas together into a larger coherent understanding",
    "emotional_attunement":    "meeting another person's feeling, attending to the bond beneath the words",
    "crossing_threshold":      "transformation, passage, ferrying across, the liminal space between states",
    # Knowledge / capability domains (Phase 2, 2026-06-07) — the factual axis the 'unlock his
    # latent knowledge' project is really about. CAVEAT: the coherence (A) signal is a WEAK proxy
    # here — a confidently wrong, fluent answer binds coherently. So confidence on these domains
    # is PROVISIONAL until a correctness signal (C / external check) is wired; for now it tracks
    # "does he engage this territory coherently", not "is he right". Treat accordingly.
    "factual_recall":          "recalling facts — names, dates, places, who, what, when, where, concrete information about the world",
    "language_translation":    "translating between languages, reading or writing Chinese, German, another tongue; say it in another language",
    "mathematics":             "mathematics and calculation — arithmetic, what is X times Y, multiply, add, numbers, prime, equation, solve, logic, proof, quantitative reasoning",
    "science":                 "science — physics, biology, chemistry, how the natural world works, photosynthesis, atoms, energy, gravity, evolution, mechanism and theory",
    "history_culture":         "history and culture — historical events, the Roman Empire, war, dynasties, traditions, who did what and when",
    # 2026-08-19 (health-check finding): the school's other 4 graded lesson types — writing
    # (composition.py), observation (nature_study.py), comprehension (essay_lesson.py), and music
    # (music_drill.py) — have been calling record_drill_accuracy() since their respective builds
    # without ever being added here. Since their "confidence" belief was never touched by the live
    # per-cycle tracker, it sat frozen at the 0.50 seed default forever — for writing/observation this
    # produced a coincidental artifact (gap = |0.5 − measured|, and a 0.9 score lands exactly on the
    # 0.40 "large" threshold), feeding 13 synthetic contradiction-pressure events into the tension
    # ledger that were never a real felt-vs-measured gap. Added below so all 5 school domains get
    # genuine live fluency tracking, matching mathematics.
    "writing":                 "writing, composing — describing, summarizing, arguing, narrating, explaining something in his own words, a piece of prose he is producing",
    "observation":             "close observation of the natural world — looking carefully at what is genuinely in front of him and recording the specific, concrete particulars, then one careful inference, the way Darwin worked",
    "comprehension":           "how well he grasped and grounded a book he finished reading — retrieval, recalling and explaining what a text actually said from memory, not re-reading it",
    "music":                   "music theory — intervals, key signatures, chords, rhythm, notation, composition craft",
}

# Knowledge-axis domains where coherence is NOT a fair competence proxy (see caveat above).
# Tracked, but flagged so downstream never mistakes a coherent answer for a correct one.
# comprehension/music added 2026-08-19 — both deterministically graded against a real answer/text,
# same "fluent but wrong" failure shape as mathematics/science. writing/observation stay OUT: they're
# graded on groundedness/quality, not a single right answer, so coherence is a fairer proxy there —
# closer to the psychological domains above than to factual recall.
_KNOWLEDGE_DOMAINS = frozenset({
    "factual_recall", "language_translation", "mathematics", "science", "history_culture",
    "comprehension", "music",
})

_SEED_CONFIDENCE = 0.50   # genuine ignorance — no prior belief about any domain
_CLASSIFY_SIM    = 0.30   # cosine threshold: a cycle "exercised" a (psychological) domain at/above this
# Knowledge domains use a lower bar: terse factual questions ("what is 17 times 23") embed weakly
# against topic descriptors (~0.26-0.27 even when clearly on-topic), while their anchors are
# topically specific enough that cross-domain false positives at this bar are unlikely. Oblique
# queries that match nothing strongly still record no evidence — a miss is safer than a wrong hit.
_CLASSIFY_SIM_KNOWLEDGE = 0.25
_LR              = 0.10   # belief learning rate for the A (coherence) signal
_LR_C            = 0.05   # smaller learning rate for the C (user-correction) signal
_STRUGGLE_PENALTY = 0.15  # each introspective re-bind pass docks the coherence outcome
_POS_NEG_BAR     = 0.50   # outcome above this counts as positive evidence, below as negative
_CALIB_WINDOW    = 30     # rolling (predicted, measured) pairs kept for calibration_error
_ACCURACY_LR     = 0.20   # learning rate for the external accuracy axis (faster than fluency — rarer, truer)

# User-correction cues for the C signal. Deliberately conservative — only fire on a clear
# correction of the PRIOR response. Positive uptake is too ambiguous to detect cheaply.
_CORRECTION_CUES = (
    "no,", "no.", "that's wrong", "thats wrong", "incorrect", "not quite", "not really",
    "you misunderstood", "you missed", "that's not", "thats not", "actually,", "wrong.",
    "i disagree", "that's not what", "you're wrong", "youre wrong", "no -", "not what i",
)

# Tier 4 POSITIVE confirmation cues (Phase A) — deliberately conservative; bare "yes"/"good"/
# "thanks" are too ambiguous to count as a factual-accuracy confirmation.
_CONFIRMATION_CUES = (
    "that's right", "thats right", "exactly right", "exactly so", "you're right", "youre right",
    "correct", "spot on", "well put", "precisely", "that's correct", "thats correct",
    "yes exactly", "that's it", "thats it",
)


# --- Tier-4 verdict matching window (J-3106, F-3826) --------------------------------------------
# The old detector was `cue in whole_lowered_message`, so a long friendly message holding 'no,' / 'actually,'
# / 'precisely' mid-sentence was scored as a verdict on the PRIOR cycle (all 3 lifetime Tier-3 probes and
# 4 of 4 checkable tier4_user 0.0 labels were such false positives). A verdict on the prior answer is a
# short reply that OPENS with the cue; a long message is left unclassified (neither correction nor
# confirmation). Deterministic, no LLM.
_VERDICT_MAX_CHARS = 300      # longer messages are never classified as a bare verdict
_VERDICT_OPENING_CHARS = 80   # a sentence-start cue must begin inside this opening window
_VERDICT_LEAD = re.compile(
    r"^(?:(?:du|yes|yeah|yep|ok|okay|well|but|hmm|hm)\b[\s,.:;!\-]*)+")
_VERDICT_SENT_BREAK = re.compile(r"[.!?\n]+\s+")
_VERDICT_OPENERS = "\"'([*_ \t"


def _verdict_cue_at_opening(human_input: str, cues) -> bool:
    if not human_input:
        return False
    low = human_input.lower().strip()
    if not low or len(low) > _VERDICT_MAX_CHARS:
        return False
    starts = {0}
    for m in _VERDICT_SENT_BREAK.finditer(low):
        if m.end() <= _VERDICT_OPENING_CHARS:
            starts.add(m.end())
    for st in starts:
        seg = low[st:].lstrip(_VERDICT_OPENERS)
        cands = {seg}
        lead = _VERDICT_LEAD.match(seg)
        if lead and lead.end() < len(seg):
            cands.add(seg[lead.end():].lstrip(_VERDICT_OPENERS))
        for cand in cands:
            for cue in cues:
                if not cand.startswith(cue):
                    continue
                nxt = cand[len(cue):len(cue) + 1]
                if cue[-1].isalpha() and nxt.isalpha():
                    continue            # 'correct' must not match 'correctly' / 'correction'
                if cue == "correct" and cand[len(cue):].lstrip().startswith("me"):
                    continue            # 'correct me if I am wrong' is a request, not a verdict
                return True
    return False


@dataclass
class CapabilityBelief:
    """A four-axis belief about a domain (see docs/archive/epistemics_plan.md). Back-compat: the original
    `confidence` IS the FLUENCY axis (coherence/bind, the A signal) — kept by that name so existing
    capability_beliefs.json loads unchanged. New axes default-safe for old files."""
    # --- Axis 1: FLUENCY (coherence/bind, the A signal). Also the prediction for fluency-surprise.
    confidence:     float = _SEED_CONFIDENCE
    evidence_count: int   = 0
    positive:       int   = 0
    negative:       int   = 0
    last_surprise:  float = 0.0
    last_tested:    float = 0.0
    # --- Axis 2: STABILITY (Tier 2 self-consistency). RESERVED — filled in Phase B; not truth.
    stability:        float = _SEED_CONFIDENCE
    stability_count:  int   = 0
    # --- Axis 3: ACCURACY (EXTERNAL signals only — Tier 1/3/4). None = "not yet measured", a
    #     first-class humility state: confidence must stay capped where accuracy is unknown.
    accuracy:         "float | None" = None
    accuracy_count:   int   = 0
    # --- J-4369 / D-0847: the mixed accuracy axis split by source. `accuracy` stays (back-compat, legacy mix).
    #     accuracy_drill = drill results only (record_drill_accuracy); accuracy_verdict = tier 1/3/4 verdicts
    #     only (record_accuracy). Readers use drill where present, else verdict, else legacy accuracy.
    accuracy_drill:   "float | None" = None
    accuracy_drill_count: int = 0
    accuracy_verdict: "float | None" = None
    accuracy_verdict_count: int = 0
    # --- domain type tag: 'skill' (coherence ≈ competence) | 'knowledge' (needs external truth).
    domain_type:      str   = "skill"
    # --- Calibration: rolling (predicted, measured) pairs. calibration_error is DERIVED from these
    #     — the real endgame: does 渡 know how reliable his own knowledge is?
    calib_pairs:      list  = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def calibration_error(self) -> "float | None":
        """Derived: rolling mean |predicted − measured| over recent accuracy checks. None until
        there is external evidence. LOW = 渡 understands the reliability of his own knowledge —
        the true endgame (well-calibrated > merely accurate). Before any accuracy evidence the
        prediction is his FLUENCY, so early calibration_error measures the fluency-trap directly."""
        if not self.calib_pairs:
            return None
        return round(sum(abs(p - m) for p, m in self.calib_pairs) / len(self.calib_pairs), 4)

    def record_accuracy(self, measured: float, lr: float = 0.20) -> tuple[float, float]:
        """Fold one EXTERNAL accuracy observation in [0,1] (Tier 1/3/4 only). Records the
        calibration pair (predicted-before vs measured), then moves the accuracy belief by the
        delta rule (seeding from the first measurement). Returns (predicted, measured)."""
        predicted = self.accuracy if self.accuracy is not None else self.confidence  # fluency is the naive prior
        self.calib_pairs.append([round(predicted, 3), round(float(measured), 3)])
        self.calib_pairs = self.calib_pairs[-_CALIB_WINDOW:]
        if self.accuracy is None:
            self.accuracy = float(measured)
        else:
            self.accuracy = max(0.0, min(1.0, self.accuracy + lr * (float(measured) - self.accuracy)))
        self.accuracy_count += 1
        m = float(measured)
        self.accuracy_verdict = m if self.accuracy_verdict is None else max(
            0.0, min(1.0, self.accuracy_verdict + lr * (m - self.accuracy_verdict)))
        self.accuracy_verdict_count += 1
        return predicted, float(measured)

    def record_stability(self, score: float, lr: float = 0.20) -> None:
        """Fold one Tier 2 self-consistency score in [0,1] into the stability axis (delta rule,
        seeding from the first). RESERVED axis — feeds no behaviour until Phase C."""
        s = max(0.0, min(1.0, float(score)))
        if self.stability_count == 0:
            self.stability = s
        else:
            self.stability = max(0.0, min(1.0, self.stability + lr * (s - self.stability)))
        self.stability_count += 1


def coherence_outcome(scene_coherence: float, introspective_passes: int) -> float:
    """The A signal: a coarse [0,1] outcome from how the scene bound. A clean coherent bind on
    the first pass scores high; a fractured scene that needed several contradiction-driven
    re-binds scores low. The coherence term is the episodic-buffer model's OWN self-rated number (J-2808,
    F-3453), not a structural measure; only the pass count is structural. See core/episodic_buffer_judge.py."""
    o = float(scene_coherence) - _STRUGGLE_PENALTY * int(introspective_passes)
    return max(0.0, min(1.0, o))


# -- Phase 2 surprise log (sidecar) + the climate-facing aggregate --------------------------

def _load_surprise_log() -> list[dict]:
    if not _SURPRISE_FILE.exists():
        return []
    try:
        with open(_SURPRISE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_surprise_log(surprises: list[dict]) -> None:
    try:
        # J-1812 / F-2428 -- write fence (see record_drill_accuracy): guard_path before the mkdir, INSIDE the best-effort try.
        path = profile.guard_path(_SURPRISE_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(surprises[-_SURPRISE_LOG_MAX:], f)
        tmp.replace(path)
    except Exception as exc:
        logger.debug("[competence] _save_surprise_log failed (non-fatal): %s", exc)


def _append_accuracy_observation(entry: dict) -> None:
    """Append one external accuracy observation to the bootstrap log (jsonl). Best-effort."""
    try:
        # J-1812 / F-2428 -- write fence (see record_drill_accuracy): guard_path before the mkdir, INSIDE the best-effort try.
        path = profile.guard_path(_ACCURACY_OBS_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[competence] _append_accuracy_observation failed (non-fatal): %s", exc)


def _append_stability_observation(entry: dict) -> None:
    """Append one Tier 2 stability observation to the bootstrap log (jsonl). Best-effort."""
    try:
        # J-1812 / F-2428 -- write fence (see record_drill_accuracy): guard_path before the mkdir, INSIDE the best-effort try.
        path = profile.guard_path(_STABILITY_OBS_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[competence] _append_stability_observation failed (non-fatal): %s", exc)


def _is_abstention(answer: str) -> bool:
    """True if the answer is an 'I don't know'-type non-claim (honest uncertainty), which must not
    be counted as stable knowledge even when consistently repeated."""
    if not answer:
        return True
    low = answer.lower()
    return any(cue in low for cue in _ABSTENTION_CUES)


def _read_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def bootstrap_report() -> dict:
    """THE validation gate for Phase C (docs/archive/epistemics_plan.md §bootstrap). Joins stability
    observations to accuracy observations by cycle_id, and reports whether high stability
    predicts high accuracy on the items where we have BOTH. The gap between them IS the
    systematic-error blind spot, quantified. No LLM; read-only analysis.

    Returns a dict with the paired count, mean stability for correct vs incorrect answers, the
    Pearson correlation, and a verdict string. Pairs are scarce (Tier 1/4 are sparse) — treat
    small-n results as provisional."""
    acc_all = _read_jsonl(_ACCURACY_OBS_FILE)
    cutoff = tier4_cutoff_ts()
    acc = [a for a in acc_all if not is_legacy_tier4(a, cutoff)]
    n_excluded = len(acc_all) - len(acc)
    sta = _read_jsonl(_STABILITY_OBS_FILE)
    sta_by_cycle = {s.get("cycle_id"): s for s in sta if s.get("cycle_id")}

    pairs = []   # (stability, measured_accuracy)
    for a in acc:
        cid = a.get("cycle_id")
        s = sta_by_cycle.get(cid)
        if s is not None and s.get("stability") is not None and a.get("measured") is not None:
            pairs.append((float(s["stability"]), float(a["measured"])))

    n = len(pairs)
    report = {"n_accuracy_obs": len(acc), "n_stability_obs": len(sta), "n_pairs": n,
              "n_tier4_excluded": n_excluded}
    if n == 0:
        report["verdict"] = "no paired data yet — feed Tier 1 (arithmetic) and Tier 4 (correct/confirm) signals"
        return report

    correct   = [st for st, m in pairs if m >= 0.5]
    incorrect = [st for st, m in pairs if m < 0.5]
    mean = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
    report["mean_stability_when_correct"]   = mean(correct)
    report["mean_stability_when_incorrect"] = mean(incorrect)

    # Pearson correlation between stability and measured accuracy.
    if n >= 2:
        import statistics
        xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
        try:
            report["pearson_stability_vs_accuracy"] = round(statistics.correlation(xs, ys), 3)
        except Exception:
            report["pearson_stability_vs_accuracy"] = None

    gap = None
    if correct and incorrect:
        gap = round(mean(correct) - mean(incorrect), 3)
    report["correct_minus_incorrect_stability"] = gap
    if gap is None:
        report["verdict"] = f"n={n} but only one accuracy class present — need both correct and incorrect items"
    elif gap > 0.15:
        report["verdict"] = (f"stability PREDICTS accuracy (correct answers {gap} more stable). "
                             f"Stability earns use as an accuracy prior; blind-spot is the residual.")
    elif gap > 0.05:
        report["verdict"] = f"weak signal (gap {gap}) — keep accumulating before trusting stability"
    else:
        report["verdict"] = (f"stability does NOT predict accuracy (gap {gap}) — systematic confident "
                             f"error dominates; stability is a poor accuracy proxy here")
    return report


def recent_capability_surprise(now: float | None = None) -> float:
    """Decayed aggregate of recent capability prediction-errors, mapped to [0,1). Read by the
    Climate Engine (Phase 2) to raise world_model_strain + novelty_hunger when 渡 has recently
    been surprised about what he can do. Pure numeric, no LLM, no side effects. 1 h half-life;
    ignores surprises older than the window. Returns 0.0 on any failure or when calm."""
    if now is None:
        now = time.time()
    acc = 0.0
    for r in _load_surprise_log():
        ts  = float(r.get("ts", 0.0))
        age = now - ts
        if age < 0 or age > _SURPRISE_WINDOW_SECS:
            continue
        acc += float(r.get("surprise", 0.0)) * (0.5 ** (age / _SURPRISE_HALFLIFE_SECS))
    return acc / (acc + _SURPRISE_SAT_K) if acc > 0 else 0.0


class CompetenceTracker:
    """Phase 0 observer. After each substantive cycle: classify which domains were exercised,
    read the coarse outcome from the bound scene, compute surprise against the standing belief,
    and update. Applies the sparse C correction from the human's next turn. Pure observer —
    persists beliefs to JSON and logs; changes no behaviour."""

    def __init__(self):
        self._beliefs: dict[str, CapabilityBelief] = self._load()
        self._anchors: dict[str, "object"] = {}   # lazy embedding cache
        # The PRIOR responded cycle — target of the next turn's user-verdict (C/Tier-4) signal.
        # {cycle_id, question, domains} so Tier-4 accuracy carries the prior question's cycle_id
        # (the bootstrap joins stability↔accuracy on cycle_id). None until the first cycle.
        self._pending: "dict | None" = None
        # Phase 2 rolling surprise log: [{ts, surprise, domain}], bounded, persisted to sidecar.
        self._surprises: list[dict] = _load_surprise_log()
        # Phase B in-memory queue of knowledge questions awaiting a background stability check.
        self._stability_queue: list[dict] = []
        # Phase C0, Path 1 in-memory queue of contradiction-triggered Tier-3 witness probes.
        self._tier3_queue: list[dict] = []

    # -- persistence -------------------------------------------------------

    def _load(self) -> dict:
        if not _BELIEFS_FILE.exists():
            return {}
        try:
            with open(_BELIEFS_FILE, encoding="utf-8") as f:
                raw = json.load(f)
            return {k: CapabilityBelief(**v) for k, v in raw.items()}
        except Exception as exc:
            logger.debug("[competence] load failed (non-fatal, fresh start): %s", exc)
            return {}

    def _save(self) -> None:
        # 2026-08-19 fix: this used to write ONLY self._beliefs — the tracker's own in-memory picture,
        # built from whatever domains _classify() has anchor-matched a cycle to so far. A second, separate
        # writer (record_drill_accuracy(), module-level, used by school lessons — math/writing/observation/
        # comprehension/music) does its own independent read-modify-write to the SAME file. Whenever this
        # save fired for an unrelated domain, it silently ERASED any domain record_drill_accuracy had
        # written that the tracker had never itself classified — confirmed live: 8/8 correct music drills
        # logged, zero reached this file, because "music" was never in self._beliefs to begin with and the
        # tracker's own routine per-cycle saves kept overwriting the whole file without it. The old
        # docstring called the file-vs-tracker race "negligible" assuming ~2 drill calls/day; music runs a
        # full batch per session, well past that assumption. Fix: read what's already on disk first and
        # merge this tracker's own domains INTO it (this tracker is authoritative for ITS domains; anything
        # on disk that it doesn't track is some other writer's data and must survive this save untouched).
        try:
            # J-1812 / F-2428 -- write fence (see record_drill_accuracy): guard_path before the mkdir and before the
            # merge read, INSIDE the existing best-effort try (its except already logs a debug line).
            bf = profile.guard_path(_BELIEFS_FILE)
            bf.parent.mkdir(parents=True, exist_ok=True)
            on_disk = {}
            if bf.exists():
                try:
                    on_disk = json.loads(bf.read_text(encoding="utf-8"))
                except Exception:
                    on_disk = {}
            merged = {**on_disk, **{k: b.as_dict() for k, b in self._beliefs.items()}}
            tmp = bf.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
            tmp.replace(bf)
        except Exception as exc:
            logger.debug("[competence] save failed (non-fatal): %s", exc)

    def _belief(self, domain: str) -> CapabilityBelief:
        if domain not in self._beliefs:
            dt = "knowledge" if domain in _KNOWLEDGE_DOMAINS else "skill"
            self._beliefs[domain] = CapabilityBelief(domain_type=dt)
        b = self._beliefs[domain]
        # back-fill domain_type for beliefs loaded from older files (default was "skill")
        if domain in _KNOWLEDGE_DOMAINS and b.domain_type != "knowledge":
            b.domain_type = "knowledge"
        return b

    # -- domain classification (no LLM) ------------------------------------

    def _domain_anchors(self) -> dict:
        if not self._anchors:
            from .memory.store import _embed
            for dom, text in _DOMAIN_ANCHORS.items():
                v = _embed(text)
                if v is not None:
                    self._anchors[dom] = v
        return self._anchors

    def _classify(self, text: str) -> list[str]:
        """Which domains this cycle exercised — cosine of the cycle text against each domain
        anchor, all at/above threshold. A cycle can exercise several. No LLM."""
        if not text or not text.strip():
            return []
        from .memory.store import _embed, _cosine
        qv = _embed(text)
        if qv is None:
            return []
        anchors = self._domain_anchors()
        out = []
        for dom, av in anchors.items():
            thr = _CLASSIFY_SIM_KNOWLEDGE if dom in _KNOWLEDGE_DOMAINS else _CLASSIFY_SIM
            if _cosine(qv, av) >= thr:
                out.append(dom)
        return out

    # -- the update --------------------------------------------------------

    def _update(self, domain: str, outcome: float, lr: float) -> tuple[float, float]:
        """Move the belief toward the observed outcome by the delta rule. Returns
        (expected_before, surprise) — the prediction and the prediction error that drove it."""
        b = self._belief(domain)
        expected = b.confidence
        surprise = abs(expected - outcome)
        b.confidence = max(0.0, min(1.0, expected + lr * (outcome - expected)))
        b.evidence_count += 1
        if outcome >= _POS_NEG_BAR:
            b.positive += 1
        else:
            b.negative += 1
        b.last_surprise = round(surprise, 4)
        b.last_tested = time.time()
        return expected, surprise

    # -- the per-cycle observation -----------------------------------------

    def observe_cycle(self, state) -> None:
        """Called once at the end of a responded cycle. (1) Apply the C signal: if THIS cycle's
        human input corrected the PRIOR response, dock the prior domains. (2) Compute the A
        signal from the bound scene and update this cycle's exercised domains. Best-effort —
        never raises into the cycle."""
        try:
            is_human = getattr(state, "input_type", "human") == "human"
            prior = self._pending

            # (C / Tier 4) — user verdict on the PRIOR response. Correction docks fluency (as
            # before) AND, for knowledge domains, feeds the EXTERNAL accuracy axis. Confirmation
            # feeds accuracy positively. The accuracy obs carries the PRIOR cycle_id + question, so
            # the bootstrap can join it to that cycle's stability check.
            if is_human and prior and prior.get("domains"):
                corrected = self._is_correction(state.raw_input)
                confirmed = (not corrected) and self._is_confirmation(state.raw_input)
                # (C0 Path 1) knowledge domains where the STABILITY axis disagreed with this same
                # verdict — stability-high + corrected, or stability-low + confirmed. Collected across
                # the loop below, then queued as ONE Tier-3 probe on this cycle's shared question.
                tier3_domains: list[str] = []
                for dom in prior["domains"]:
                    if corrected:
                        exp, s = self._update(dom, outcome=0.15, lr=_LR_C)   # fluency dock (existing)
                        logger.info("[competence] C-signal correction: domain=%s -> fluency=%.2f",
                                    dom, self._belief(dom).confidence)
                    if (corrected or confirmed) and self._belief(dom).domain_type == "knowledge":
                        self._record_external_accuracy(dom, 0.0 if corrected else 1.0,
                                                       source="tier4_user", cycle_id=prior.get("cycle_id", ""),
                                                       question=prior.get("question", ""))
                        # Only evaluate contradiction once stability has actually been measured at
                        # least once — a never-checked belief sits at the 0.50 seed, which is also
                        # this band's own midpoint, and must not be misread as "stability implied
                        # nothing either way" being itself a verdict.
                        b_dom = self._belief(dom)
                        if b_dom.stability_count > 0:
                            stab = b_dom.stability
                            if ((corrected and stab >= _TIER3_STABILITY_HIGH) or
                                    (confirmed and stab <= _TIER3_STABILITY_LOW)):
                                tier3_domains.append(dom)
                if tier3_domains and (prior.get("question") or "").strip():
                    logger.info("[competence] C0 Path 1 contradiction: domains=%s corrected=%s "
                                "confirmed=%s -> queueing Tier-3 probe", tier3_domains, corrected, confirmed)
                    self.enqueue_tier3_probe(prior["question"], tier3_domains,
                                             prior.get("cycle_id", ""), prior.get("answer", ""))
                self._pending = None

            # (A — fluency) coherence/bind outcome. Requires a bound scene (substantive cycle).
            scene = getattr(state, "episodic_scene", None)
            if scene is None:
                return   # trivial cycle — no scene bound, no competence evidence
            outcome = coherence_outcome(scene.coherence, getattr(state, "introspective_passes", 0))

            domains = self._classify(self._cycle_text(state))
            cycle_id = getattr(state, "cycle_id", "")
            question = state.raw_input or ""
            # Captured once, used for the Tier 1 check below AND (C0 Path 1) carried into _pending so
            # a LATER contradiction-triggered Tier-3 probe has something to score the witness against.
            answer_text = self._voice_text(state)

            # (Tier 1) deterministic ground truth — arithmetic checked with no LLM → accuracy axis.
            try:
                from .deterministic_checker import check_arithmetic
                t1 = check_arithmetic(question, answer_text)
                if t1 is not None:
                    self._record_external_accuracy("mathematics", t1, source="tier1_eval",
                                                   cycle_id=cycle_id, question=question)
                    if "mathematics" not in domains:
                        domains = domains + ["mathematics"]
            except Exception as exc:
                logger.debug("[competence] tier1 check failed (non-fatal): %s", exc)

            if not domains:
                return
            now = time.time()
            for dom in domains:
                exp, s = self._update(dom, outcome=outcome, lr=_LR)
                b = self._belief(dom)
                # Phase 2: log the FLUENCY prediction error so the Climate Engine can feel it.
                self._surprises.append({"ts": now, "surprise": round(s, 4), "domain": dom})
                logger.info("[competence] domain=%s(%s) fluency: expected=%.2f outcome=%.2f surprise=%.2f "
                            "-> conf=%.2f (n=%d)", dom, b.domain_type, exp, outcome, s, b.confidence, b.evidence_count)

            # (Phase B) enqueue a background stability check for the knowledge domains this cycle
            # exercised — re-interrogate the question K times later, score agreement. The cycle_id
            # ties the eventual stability score back to any accuracy verdict on this same question.
            know = [d for d in domains if self._belief(d).domain_type == "knowledge"]
            if know and question.strip():
                self.enqueue_stability(question, know, cycle_id)

            # remember for next turn's C/Tier-4 signal (+ the answer text, for C0 Path 1's witness compare)
            self._pending = {"cycle_id": cycle_id, "question": question, "domains": domains,
                             "answer": answer_text}
            self._surprises = self._surprises[-_SURPRISE_LOG_MAX:]
            self._save()
            _save_surprise_log(self._surprises)
        except Exception as exc:
            logger.debug("[competence] observe failed (non-fatal): %s", exc)

    def _record_external_accuracy(self, domain: str, measured: float, source: str,
                                  cycle_id: str, question: str = "") -> None:
        """Phase A: fold one external accuracy observation into the domain's accuracy axis, append
        the calibration pair, and log to the bootstrap sidecar. OBSERVE-ONLY — accuracy feeds NO
        behaviour yet (that is Phase C). The log is what the bootstrap circuit will analyse."""
        b = self._belief(domain)
        predicted, _ = b.record_accuracy(measured, lr=_ACCURACY_LR)
        ce = b.calibration_error()
        logger.info("[competence] ACCURACY domain=%s source=%s predicted=%.2f measured=%.2f "
                    "-> accuracy=%.2f calib_err=%s (n=%d)", domain, source, predicted, measured,
                    b.accuracy, ("%.2f" % ce) if ce is not None else "n/a", b.accuracy_count)
        _append_accuracy_observation({
            "ts": time.time(), "cycle_id": cycle_id, "question": question[:200], "domain": domain,
            "source": source, "predicted_accuracy": round(predicted, 3), "measured": round(float(measured), 3),
            "fluency": round(b.confidence, 3), "stability": round(b.stability, 3),
            "accuracy": round(b.accuracy, 3) if b.accuracy is not None else None,
            "calibration_error": ce,
        })

    # -- Phase B: stability engine (Tier 2 self-consistency) ----------------

    def enqueue_stability(self, question: str, domains: list[str], cycle_id: str) -> None:
        """Queue a knowledge question for a background stability check. Bounded; newest kept."""
        self._stability_queue.append({"question": question, "domains": list(domains),
                                      "cycle_id": cycle_id, "ts": time.time()})
        self._stability_queue = self._stability_queue[-_STABILITY_QUEUE_MAX:]
        logger.info("[stability] ENQUEUED q=%r domains=%s (queue_size=%d)",
                    question[:50], domains, len(self._stability_queue))

    def enqueue_tier3_probe(self, question: str, domains: list[str], cycle_id: str,
                            answer: str = "") -> None:
        """Queue a Tier-3 external-witness probe (C0 Path 1): a Tier-4 correction/confirmation just
        landed and disagreed with what the domain's own stability axis implied. `answer` is the
        ORIGINAL claim (the response that got corrected/confirmed) — what the witness's independent
        answer will be scored against. Bounded; newest kept. Mirrors enqueue_stability."""
        self._tier3_queue.append({"question": question, "domains": list(domains), "cycle_id": cycle_id,
                                  "answer": answer, "ts": time.time()})
        self._tier3_queue = self._tier3_queue[-_TIER3_QUEUE_MAX:]
        logger.info("[tier3] ENQUEUED q=%r domains=%s (queue_size=%d)",
                    question[:50], domains, len(self._tier3_queue))

    def _stability_score(self, answers: list[str]) -> "float | None":
        """Mean pairwise cosine of the resampled answers' embeddings → [0,1]. High = the model
        gave the same answer under perturbation (stable knowledge); low = it scattered."""
        from .memory.store import _embed, _cosine
        vecs = [v for v in (_embed(a) for a in answers) if v is not None]
        if len(vecs) < 2:
            return None
        sims = [_cosine(vecs[i], vecs[j]) for i in range(len(vecs)) for j in range(i + 1, len(vecs))]
        return max(0.0, min(1.0, sum(sims) / len(sims)))

    async def run_stability_loop(self, state) -> None:
        """Background lane (Phase B). Periodically pops a queued knowledge question, re-interrogates
        the HOT model (qwen — the knowledge substrate, NOT a persona pass) K times, scores answer
        agreement → the stability axis. Idle-gated so it never starves the live conversation.
        OBSERVE-ONLY: stability feeds no behaviour yet (Phase C). Logs every check for the bootstrap."""
        from core import model_client
        from core.schema import SERVE_CHAINS
        url = SERVE_CHAINS["hot"][0]   # measure the substrate that actually answers
        logger.info("[stability] engine started (K=%d, interval=%.0fs, idle>%.0fs)",
                    _STABILITY_K, _STABILITY_INTERVAL, _STABILITY_IDLE_SECS)
        sys_prompt = ("Answer the question as accurately and concisely as you can, in one or two "
                      "sentences. If you are not sure, say you are not sure.")
        ticks = 0
        while True:
            try:
                await asyncio.sleep(_STABILITY_INTERVAL)
                ticks += 1
                qn = len(self._stability_queue)
                idle = time.time() - getattr(state, "last_human_ts", 0.0)
                interrupted = bool(getattr(state, "interrupt_requested", False))
                # Heartbeat (instrumentation) — every tick, so one session reveals WHY checks do
                # or don't happen: queue depth, idle window, interrupt, and the skip reason.
                skip = ("queue_empty" if qn == 0 else
                        ("not_idle(%.0fs<%.0f)" % (idle, _STABILITY_IDLE_SECS) if idle < _STABILITY_IDLE_SECS else
                         ("interrupt" if interrupted else None)))
                logger.info("[stability] tick #%d queue_size=%d idle=%.0fs %s",
                            ticks, qn, idle, ("skip=%s" % skip) if skip else "-> RUN")
                if skip:
                    continue
                item = self._stability_queue.pop(0)
                logger.info("[stability] dequeued q=%r (domains=%s) — starting %d probes",
                            item["question"][:50], item["domains"], _STABILITY_K)
                answers = []
                probes_started = probes_ok = 0
                for _ in range(_STABILITY_K):
                    probes_started += 1
                    try:
                        a = await model_client.call_node(
                            url, sys_prompt, item["question"],
                            max_tokens=_STABILITY_MAXTOK, temperature=_STABILITY_TEMP, json_mode=False)
                        if a and a.strip():
                            answers.append(a.strip()); probes_ok += 1
                    except Exception as exc:
                        logger.info("[stability] probe FAILED: %s", exc)   # was debug — promote so faults show
                logger.info("[stability] probes_started=%d probes_completed=%d", probes_started, probes_ok)
                # Separate genuine assertions from abstentions ("I don't know"). Consistent
                # abstention is honest uncertainty, NOT stable knowledge — don't let it inflate
                # the stability axis. Measure agreement only among assertions.
                assertions = [a for a in answers if not _is_abstention(a)]
                n_abstain  = len(answers) - len(assertions)
                score = self._stability_score(assertions)
                obs = {
                    "ts": time.time(), "cycle_id": item.get("cycle_id", ""),
                    "question": (item.get("question", "") or "")[:200], "domains": item["domains"],
                    "k": len(answers), "n_assert": len(assertions), "n_abstain": n_abstain,
                    "abstained": n_abstain > 0,
                }
                if score is None:
                    # mostly/all abstention — log it (so we can see abstention rate) but do NOT
                    # update the axis: no knowledge claim was made to measure the stability of.
                    obs["stability"] = None
                    _append_stability_observation(obs)
                    logger.info("[stability] q=%r ABSTAINED (n_assert=%d) — persisted=1, no axis update",
                                item["question"][:50], len(assertions))
                else:
                    for dom in item["domains"]:
                        self._belief(dom).record_stability(score, lr=_STABILITY_LR)
                    self._save()
                    obs["stability"] = round(score, 3)
                    _append_stability_observation(obs)
                    logger.info("[stability] q=%r domains=%s stability=%.2f (assert=%d/%d) persisted=1",
                                item["question"][:50], item["domains"], score, len(assertions), len(answers))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("[stability] loop error (non-fatal): %s", exc)

    # -- Phase C0, Path 1: contradiction-triggered Tier-3 external-witness probe -------------

    async def run_tier3_probe_loop(self, state) -> None:
        """Background lane (Phase C0, Path 1 — contradiction-triggered only; Path 2/proactive
        sampling is explicitly out of scope, see docs/plans/epistemics_phase_c.md). Periodically pops
        a queued Tier-3 probe (a Tier-4 correction/confirmation that disagreed with the domain's own
        stability axis), asks an INDEPENDENT model (command-r7b, Ramses — genuinely distinct lineage
        from the qwen hot lane that generated the original answer) the same question, and scores its
        agreement with the original answer as one more accuracy observation (source="tier3_model").
        Idle-gated so it never starves the live conversation — mirrors run_stability_loop's shape
        exactly (bounded queue, idle-gated asyncio loop, same heartbeat-logging discipline).
        OBSERVE-ONLY: feeds no behaviour (no confidence capping, no abstention, no world_model_strain)
        — only the bootstrap corpus."""
        from core import model_client
        logger.info("[tier3] probe engine started (interval=%.0fs, idle>%.0fs)",
                    _TIER3_INTERVAL, _TIER3_IDLE_SECS)
        sys_prompt = ("Answer the question as accurately and concisely as you can, in one or two "
                      "sentences. If you are not sure, say you are not sure.")
        ticks = 0
        while True:
            try:
                await asyncio.sleep(_TIER3_INTERVAL)
                ticks += 1
                qn = len(self._tier3_queue)
                idle = time.time() - getattr(state, "last_human_ts", 0.0)
                interrupted = bool(getattr(state, "interrupt_requested", False))
                # Heartbeat (instrumentation) — every tick, so one session reveals WHY probes do or
                # don't happen: queue depth, idle window, interrupt, and the skip reason.
                skip = ("queue_empty" if qn == 0 else
                        ("not_idle(%.0fs<%.0f)" % (idle, _TIER3_IDLE_SECS) if idle < _TIER3_IDLE_SECS else
                         ("interrupt" if interrupted else None)))
                logger.info("[tier3] tick #%d queue_size=%d idle=%.0fs %s",
                            ticks, qn, idle, ("skip=%s" % skip) if skip else "-> RUN")
                if skip:
                    continue
                item = self._tier3_queue.pop(0)
                logger.info("[tier3] dequeued q=%r (domains=%s) — probing witness",
                            item["question"][:50], item["domains"])
                original = (item.get("answer") or "").strip()
                if not original:
                    logger.info("[tier3] q=%r no original answer captured — skipped", item["question"][:50])
                    continue
                # J-1880 / F-2503: single-endpoint witness -- while the J-1832 breaker has this lane tripped
                # (Ramses stall), take the existing fail-open path at once instead of waiting a full call
                # timeout. Never falls back to another endpoint. Fail-open on any breaker problem.
                try:
                    if model_client.lane_is_tripped(_TIER3_WITNESS_URL, note_skip=True):
                        logger.info("[tier3] witness lane breaker open (fail-open, skipped): q=%r",
                                    item["question"][:50])
                        continue
                except Exception:
                    pass
                try:
                    witness_answer = await model_client.call_node(
                        _TIER3_WITNESS_URL, sys_prompt, item["question"],
                        max_tokens=_TIER3_MAXTOK, temperature=0.2, json_mode=False, tier=3)
                except Exception as exc:
                    # Fail OPEN (skip this probe) rather than fall back to any other endpoint —
                    # see _TIER3_WITNESS_URL's own comment on why silent fallback is unsafe here.
                    logger.info("[tier3] witness call FAILED (fail-open, skipped): %s", exc)
                    continue
                if not witness_answer or not witness_answer.strip():
                    logger.info("[tier3] q=%r witness returned empty — skipped", item["question"][:50])
                    continue
                if _is_abstention(witness_answer):
                    # Same abstention guard as Phase B: an honest "I don't know" from the witness is
                    # not a verdict on the original claim either way — no accuracy evidence either way.
                    logger.info("[tier3] q=%r witness ABSTAINED — no accuracy verdict, skipped",
                                item["question"][:50])
                    continue
                # Reuse _stability_score's cosine machinery: for exactly two answers, its mean-
                # pairwise-cosine IS the plain agreement score between them — same _embed/_cosine
                # path Phase B already uses, no new embedding logic needed.
                sim = self._stability_score([original, witness_answer.strip()])
                if sim is None:
                    logger.info("[tier3] q=%r embedding failed — skipped", item["question"][:50])
                    continue
                measured = 1.0 if sim >= _TIER3_AGREEMENT_SIM else 0.0
                for dom in item["domains"]:
                    self._record_external_accuracy(dom, measured, source="tier3_model",
                                                    cycle_id=item.get("cycle_id", ""),
                                                    question=item.get("question", ""))
                self._save()
                logger.info("[tier3] q=%r domains=%s witness_sim=%.2f -> measured=%.1f persisted=%d",
                            item["question"][:50], item["domains"], sim, measured, len(item["domains"]))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("[tier3] loop error (non-fatal): %s", exc)

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _cycle_text(state) -> str:
        """The text that represents what this cycle engaged — used for domain classification."""
        parts = [state.raw_input or ""]
        if getattr(state, "perception", None) and state.perception.summary:
            parts.append(state.perception.summary)
        if getattr(state, "reflection", None) and state.reflection.draft:
            parts.append(state.reflection.draft)
        return " ".join(p for p in parts if p).strip()

    @staticmethod
    def _voice_text(state) -> str:
        """The spoken response this cycle — what Tier 1 checks for the correct value."""
        v = getattr(state, "voice", None)
        return (getattr(v, "final", "") or "") if v else ""

    @staticmethod
    def _is_correction(human_input: str) -> bool:
        """Tier 4 negative: the human opened with a clear correction of the prior answer. Cue lists are
        unchanged; WHERE they may match is tightened (J-3106 / F-3826) -- see _verdict_cue_at_opening."""
        return _verdict_cue_at_opening(human_input, _CORRECTION_CUES)

    @staticmethod
    def _is_confirmation(human_input: str) -> bool:
        """Tier 4 positive: the human explicitly affirmed the prior answer was right (opening-sentence
        match only, same tightening as _is_correction)."""
        return _verdict_cue_at_opening(human_input, _CONFIRMATION_CUES)

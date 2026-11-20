"""
Nascence — REPLY-LEVEL COROLLARY DISCHARGE, shadow (error_pathway; J-2530, idea I-0108, finding F-3222 item 4).

THE GAP. The attribution half of "did I say this or did it arrive from outside" is fixed at the labeling layer (J-1642,
farewell_echo D-0442, readable_label F-1920, internal_context_gate J-2297; audited by J-2510). The PREDICTION half
exists only for lessons: core/prediction_error.py compares the essay self-prediction with the Emissary grade and the
maths felt-confidence with the deterministic grade. Nothing predicts how a REPLY will land.

THIS MODULE (two calls, the recall_wager shape):
  predict(state, assessment)  -- at the close of a responded HUMAN cycle, after ProvenanceLedger.assess() and before
      the next human turn can exist, derive a predicted reception from signals already on CognitiveState with the
      declared weights below: p_correction / p_land / p_ignored. Pure arithmetic, zero LLM, nothing new is asked of
      any node. Held in memory as the one pending discharge (a restart drops it; that row is simply never resolved).
  resolve(raw_input, social_spike) -- on the NEXT human turn (orchestrator._compute_attention_vector, right after
      social.apply_correction), read the ACTUAL reception: the delta_social correction spike and competence's
      C-signal cues (CompetenceTracker._is_correction / _is_confirmation, the same static cue lists the tracker
      uses), plus a declared lexical-uptake proxy for land-vs-ignored. Logs predicted, actual and
      self_surprise = |p_correction - actual_correction| (plus a 3-class Brier score) to SHADOW_LOG.

NO COST WIRED: prediction_error.observe is NOT called here. Wiring self_surprise onto prediction_error's path (as the
drill and recall_wager do) is a later, separate decision, and only after the read job shows self_surprise is not a
constant (the J-2157 recall-confidence disease).

LAWS. D-0434: nothing here reaches a prompt, a percept or a preamble; both hooks' return values are ignored by the
orchestrator. Fail-open: neither call raises into the cycle. Writes nowhere but SHADOW_LOG (one append per resolved
discharge, off-thread). Flag REPLY_DISCHARGE_SHADOW defaults OFF; the code is restart-gated either way.

All weights and thresholds are declared below BEFORE any row was read; do not tune them to the outcome.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.reply_discharge_shadow")

REPLY_DISCHARGE_SHADOW = False    # flag OFF by default (shadow, restart-gated); flip to True to collect rows

_ROOT = Path(__file__).parent.parent
_SHADOW = _ROOT / "data" / "logs" / "reply_discharge_shadow.jsonl"   # the ONE write target

# ---- declared weights (fixed before any read) ---------------------------------------------------------------------
# p_correction = clamp01(BASE + sum of terms). Each term reads one signal already on CognitiveState / the assessment.
P_CORR_BASE = 0.05
W_UNJUSTIFIED = 0.25      # * (1 - justification)            epistemic grade: KNOW 1.0 .. NO_BASIS 0.0
W_CONFAB = 0.20           # * max(0, confabulation_signal)    narrated recall confidence above its grade (overclaim)
W_CRITIC_REJECT = 0.15    # * (critic.approved is False)
W_CRITIC_CORR = 0.10      # * min(1, len(critic.corrections) / CRITIC_CORR_SAT)
CRITIC_CORR_SAT = 3
W_CRITIC_LOWCONF = 0.10   # * (1 - critic.confidence)
W_CONTENT = 0.10          # * content_mode                    a concrete request has a checkable answer
# p_ignored is drawn from the remainder (1 - p_correction): IGNORE_BASE, nudged by the executive's response_type.
IGNORE_BASE = 0.25
IGNORE_REFLECTIVE = 0.15  # + if response_type in {reflection, silence}: nothing asked of the human
IGNORE_QUESTION = -0.15   # + if response_type == question: the reply invites an answer
IGNORE_MIN, IGNORE_MAX = 0.05, 0.60
# actual reception (resolved on the next human turn):
#   correction = social spike > 0 OR the C-signal correction cue
#   land       = otherwise, a C-signal confirmation cue OR >= UPTAKE_MIN content words shared with the reply
#   ignored    = otherwise
UPTAKE_MIN = 1
UPTAKE_MINLEN = 5         # a content word is >= 5 letters and not in _STOP
STALE_SECS = 6 * 3600     # a resolution later than this still logs, flagged stale=True
TEXT_CAP = 240
CLASSES = ("correction", "land", "ignored")

_STOP = frozenset("""about above after again against because before being below between could doesn didn
every might other their there these thing things think those through under until where which while would
should really maybe something always never still having right great thank thanks hello yours yourself""".split())
_WORD = re.compile(r"[a-z]+")

_PENDING: dict | None = None
_LOCK = threading.Lock()


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _content_words(text: str) -> set:
    return {w for w in _WORD.findall((text or "").lower()) if len(w) >= UPTAKE_MINLEN and w not in _STOP}


def signals(state, assessment) -> dict:
    """The inputs, read only from what the cycle already holds. Missing signals read as neutral (0 contribution)."""
    crit = getattr(state, "critic", None)
    ex = getattr(state, "executive", None)
    just = getattr(assessment, "justification", None) if assessment is not None else None
    return {
        "grade": str(getattr(assessment, "grade", "") or "") if assessment is not None else "",
        "justification": None if just is None else float(just),
        "confabulation_signal": float(getattr(assessment, "confabulation_signal", 0.0) or 0.0)
        if assessment is not None else 0.0,
        "recall_confidence": float(getattr(assessment, "self_reported_confidence", 0.0) or 0.0)
        if assessment is not None else None,
        "critic_approved": None if crit is None else bool(getattr(crit, "approved", True)),
        "critic_confidence": None if crit is None else float(getattr(crit, "confidence", 1.0) or 0.0),
        "critic_corrections": 0 if crit is None else len(getattr(crit, "corrections", None) or []),
        "content_mode": bool(getattr(state, "content_mode", False)),
        "response_type": str(getattr(ex, "response_type", "") or "") if ex is not None else "",
    }


def prediction(sig: dict) -> dict:
    """Deterministic predicted reception from the declared weights. Pure."""
    p = P_CORR_BASE
    if sig.get("justification") is not None:
        p += W_UNJUSTIFIED * (1.0 - _clamp(sig["justification"]))
    p += W_CONFAB * max(0.0, sig.get("confabulation_signal") or 0.0)
    if sig.get("critic_approved") is False:
        p += W_CRITIC_REJECT
    p += W_CRITIC_CORR * min(1.0, (sig.get("critic_corrections") or 0) / CRITIC_CORR_SAT)
    if sig.get("critic_confidence") is not None:
        p += W_CRITIC_LOWCONF * (1.0 - _clamp(sig["critic_confidence"]))
    if sig.get("content_mode"):
        p += W_CONTENT
    p_corr = round(_clamp(p), 3)
    ig = IGNORE_BASE
    rt = sig.get("response_type") or ""
    if rt in ("reflection", "silence"):
        ig += IGNORE_REFLECTIVE
    elif rt == "question":
        ig += IGNORE_QUESTION
    ig = _clamp(ig, IGNORE_MIN, IGNORE_MAX)
    p_ign = round((1.0 - p_corr) * ig, 3)
    p_land = round(max(0.0, 1.0 - p_corr - p_ign), 3)
    probs = {"correction": p_corr, "land": p_land, "ignored": p_ign}
    return {"p": probs, "predicted_class": max(CLASSES, key=lambda c: probs[c])}


def predict(state, assessment, *, input_type: str = "human") -> dict | None:
    """Call 1, at the close of a responded human cycle. Flag off -> None, touches nothing. Holds the pending
    discharge in memory (no write). Never raises. The return value is for tests; the orchestrator ignores it."""
    global _PENDING
    if not REPLY_DISCHARGE_SHADOW:
        return None
    try:
        if input_type != "human":
            return None
        v = getattr(state, "voice", None)
        reply = (getattr(v, "final", "") or "") if v is not None else ""
        if not reply.strip():
            return None                       # nothing was said: no reception to predict
        sig = signals(state, assessment)
        pred = prediction(sig)
        pend = {"ts": round(time.time(), 1), "cycle_id": str(getattr(state, "cycle_id", "") or ""),
                "reply": reply[:TEXT_CAP], "_reply_words": sorted(_content_words(reply)),
                "signals": sig, **pred}
        with _LOCK:
            superseded = _PENDING
            _PENDING = pend
        if superseded is not None:
            logger.debug("[reply_discharge] pending %s superseded unresolved", superseded.get("cycle_id"))
        return pend
    except Exception as exc:
        logger.debug("[reply_discharge] predict failed (non-fatal): %s", exc)
        return None


def actual(raw_input: str, reply_words, social_spike: float = 0.0) -> dict:
    """The actual reception of the prior reply, read from the next human turn. Pure."""
    from core.competence import CompetenceTracker as _CT
    c_corr = bool(_CT._is_correction(raw_input or ""))
    c_conf = (not c_corr) and bool(_CT._is_confirmation(raw_input or ""))
    shared = sorted(set(reply_words or ()) & _content_words(raw_input))
    corrected = social_spike > 0 or c_corr
    if corrected:
        cls = "correction"
    elif c_conf or len(shared) >= UPTAKE_MIN:
        cls = "land"
    else:
        cls = "ignored"
    return {"actual_class": cls, "actual_correction": 1.0 if corrected else 0.0, "social_spike": round(social_spike, 3),
            "c_signal_correction": c_corr, "c_signal_confirmation": c_conf, "uptake_words": shared[:12]}


def _append(row: dict, path: Path | None = None) -> None:
    from core import profile
    target = Path(path) if path is not None else profile.guard_path(_SHADOW)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def resolve(raw_input: str, *, social_spike: float = 0.0, cycle_id: str = "", background: bool = True) -> dict | None:
    """Call 2, on the next human turn, right after social.apply_correction. Flag off or nothing pending -> None.
    Writes ONE row to SHADOW_LOG (off-thread by default). Never raises. Returns the row for tests only."""
    global _PENDING
    if not REPLY_DISCHARGE_SHADOW:
        return None
    try:
        with _LOCK:
            pend, _PENDING = _PENDING, None
        if pend is None or (cycle_id and pend.get("cycle_id") == cycle_id):
            return None
        act = actual(raw_input, pend.get("_reply_words"), social_spike)
        p = pend["p"]
        now = time.time()
        brier = sum((p[c] - (1.0 if act["actual_class"] == c else 0.0)) ** 2 for c in CLASSES)
        row = {"ts": round(now, 1), "pred_ts": pend["ts"], "gap_s": round(now - pend["ts"], 1),
               "stale": (now - pend["ts"]) > STALE_SECS,
               "pred_cycle_id": pend["cycle_id"], "resolve_cycle_id": cycle_id,
               "reply": pend["reply"], "next_turn": (raw_input or "")[:TEXT_CAP],
               "signals": pend["signals"], "predicted": p, "predicted_class": pend["predicted_class"],
               **act,
               "self_surprise": round(abs(p["correction"] - act["actual_correction"]), 3),
               "brier3": round(brier, 3), "fed": False}

        def _run():
            try:
                _append(row)
            except Exception as exc:
                logger.debug("[reply_discharge] shadow write failed: %s", exc)
        if background:
            threading.Thread(target=_run, name="reply_discharge", daemon=True).start()
        else:
            _run()
        return row
    except Exception as exc:
        logger.debug("[reply_discharge] resolve failed (non-fatal): %s", exc)
        return None

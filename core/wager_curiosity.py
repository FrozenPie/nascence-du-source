"""
Nascence — wager-to-curiosity feedback (measurement_to_action §9; J-2527, I-0105, F-3221 item 2; SHADOW, flag off).

THE GAP. A lost recall wager (core/recall_wager.py, arm 2, LIVE since the 2026-10-29 boot under D-0495) costs Du
credibility in `factual_recall` through the drill's path, and nothing else: the loss never becomes a question. A lost
wager is the clearest "I did not know what I thought I knew" event he has, and the frontier (core/frontier.py) is
where a question is born. This module turns ONE failed wager into AT MOST ONE frontier question (a cup), shaped by the
kind of context the grade says was missing: "what would have made this recall safe?".

THE ROUTES (per wager row, decided in this order; every route is logged, only `birth` would write):
  - not_failed  : gap < FAIL_GAP (prediction_error.GAP_THRESHOLD 0.40) -- the wager was not lost by the drill's bar.
  - correction  : the cycle's own input is a human correction (competence._CORRECTION_CUES) -- the error pathway
                  owns it; a corrected wager strengthens the retraction path and NEVER generates curiosity.
  - retraction  : retraction_ledger.known_errors(topic, fallback=False) already holds a correction for this topic --
                  same rule: the retraction surfaces at recall; no question.
  - no_topic    : no usable topic text (< MIN_TOPIC chars).
  - habituated  : a question for an overlapping topic (token Jaccard > TOPIC_JACCARD, frontier's own dedup bar) was
                  dispatched within NOVELTY_WINDOW_S -- the dispatcher's surprise half: a repeat is not news.
  - capped      : MAX_PER_WINDOW questions already dispatched in the last NOVELTY_WINDOW_S.
  - birth       : the cup rides. Flag on: frontier.note_question_ex(question, source="wager", slot=..., about=
                  missing_context_type, allow_self=True). Flag off (shipped): the row only.

MISSING-CONTEXT TYPE (from the EpistemicAssessment the wager already holds; first match wins):
  no_source            evidence_present False or source_count 0   -> slot where
  conflicting_sources  contradiction_count >= 1, world model leads -> slot why   (J-3887: the conflict LOCUS, see
  self_conflict / mixed_conflict / social_conflict                        _conflict_locus: self leads / tie / social leads)
  unverified           verification == "none"                     -> slot how
  ungrounded_model     anything else                              -> slot what

D-0434 (no readout): the question carries the TOPIC and a context slot only -- never the grade, a number, the word
"wager", or that he was wrong. He meets a question about something he spoke on, not a report about himself.
Dosed coupling (D-0149, docs/staged/dosed_coupling.md §5): cup size one; dispatched by surprise against this line's
own history (the shadow log); every decision logs {stop, line, dose, value}. Curiosity / the Follow Line stay free to
ignore the question (it fades like any other frontier entry).

SHADOW (WAGER_CURIOSITY = False): every route is logged to data/logs/wager_curiosity_shadow.jsonl and frontier is
NOT called. Restart-gated: the module is only reached through recall_wager.place(). Never raises into the cycle.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.wager_curiosity")

# ---- declared before any read (J-2527); do not tune to the outcome -------------------------------------------------
WAGER_CURIOSITY = False          # shadow: rows only. Flip is a founder call (see measurement_to_action §9).
FAIL_GAP = 0.40                  # = core/prediction_error.GAP_THRESHOLD: the drill's own "large gap" bar
NOVELTY_WINDOW_S = 24 * 3600     # the surprise window against this line's own history
MAX_PER_WINDOW = 4               # at most this many births per window (cup, occasional)
TOPIC_JACCARD = 0.55             # = frontier.note_question_ex's own dedup overlap bar
MIN_TOPIC = 12                   # chars of topic text below which no question is shaped
SOURCE = "wager"                 # the frontier source string for a born question

_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "wager_curiosity_shadow.jsonl"

_SLOTS = {"no_source": "where", "conflicting_sources": "why", "self_conflict": "which", "mixed_conflict": "what",
          "social_conflict": "who", "unverified": "how", "ungrounded_model": "what"}
_TEMPLATES = {
    "no_source": "Where did I first learn about {t}",
    "conflicting_sources": "Which of my memories about {t} disagree, and why",
    "self_conflict": "Which of my own views about {t} pull against each other",
    "mixed_conflict": "What would settle the disagreement between what I recall and what I think about {t}",
    "social_conflict": "Who else has a view on {t} that I have not weighed",
    "unverified": "How could I check what I remember about {t}",
    "ungrounded_model": "What would I need to know to be sure about {t}",
}
_WORD = re.compile(r"[a-z][a-z']{3,}")


def _conflict_locus(assessment) -> str:
    """J-3887 (F-4485). conflicting_sources was 256/256 because every wager on the live log is SUSPECT /
    memory_recall / verification none / source_count >= 7, so contradiction_count >= 1 is always true. The one field
    that varies is the per-model split of the contradictions (world vs self vs social, from assessment.models). Rule,
    declared before the replay: among models that were depended_on, the single model with the strictly largest
    contradiction_count names the locus (world -> conflicting_sources, self -> self_conflict, social ->
    social_conflict); a tie for the top -> mixed_conflict. No models / no per-model counts -> conflicting_sources
    (the old behaviour). Pure; never raises."""
    try:
        counts = {}
        for m in (getattr(assessment, "models", None) or []):
            g = (lambda k, d=None: m.get(k, d)) if isinstance(m, dict) else (lambda k, d=None: getattr(m, k, d))
            if g("depended_on", False):
                counts[str(g("model", ""))] = int(g("contradiction_count", 0) or 0)
        top = max(counts.values(), default=0)
        if top <= 0:
            return "conflicting_sources"
        lead = [k for k, v in counts.items() if v == top]
        if len(lead) > 1:
            return "mixed_conflict"
        return {"self": "self_conflict", "social": "social_conflict"}.get(lead[0], "conflicting_sources")
    except Exception:
        return "conflicting_sources"


def missing_context_type(assessment) -> str:
    """The kind of context the grade says was missing. Pure; never raises."""
    try:
        if not bool(getattr(assessment, "evidence_present", False)) or int(getattr(assessment, "source_count", 0) or 0) == 0:
            return "no_source"
        if int(getattr(assessment, "contradiction_count", 0) or 0) >= 1:
            return _conflict_locus(assessment)   # J-3887 (F-4485): WHERE the conflict sits, not just that it exists
        if str(getattr(assessment, "verification", "") or "") == "none":
            return "unverified"
    except Exception:
        pass
    return "ungrounded_model"


def topic_of(text: str) -> str:
    """First sentence/line of the cycle's input, trimmed to <= 100 chars, trailing punctuation dropped."""
    t = (text or "").strip().split("\n", 1)[0]
    t = re.split(r"(?<=[.?!])\s", t, maxsplit=1)[0].strip().rstrip(".?!").strip()
    if len(t) > 100:
        t = t[:100].rsplit(" ", 1)[0]
    return t[:1].lower() + t[1:] if t else ""


def question_for(mtype: str, topic: str) -> str:
    return _TEMPLATES.get(mtype, _TEMPLATES["ungrounded_model"]).format(t=topic) + "?"


def _toks(text: str) -> set:
    return set(_WORD.findall((text or "").lower()))


def _recent_births(now: float) -> list[dict]:
    try:
        from core.shadow_log import tail_rows as _tail
        rows = _tail(_SHADOW, 500)
    except Exception:
        rows = []
    return [r for r in rows if r.get("route") == "birth" and now - float(r.get("ts", 0) or 0) <= NOVELTY_WINDOW_S]


def _is_correction(input_type: str, raw_input: str) -> bool:
    if input_type != "human" or not raw_input:
        return False
    try:
        from core.competence import CompetenceTracker   # J-3106: the opening-sentence matcher, not a whole-message substring
        return bool(CompetenceTracker._is_correction(raw_input))
    except Exception:
        return False


def _has_retraction(topic: str) -> bool:
    if not topic:
        return False
    try:
        from core import retraction_ledger as _rl
        return bool(_rl.known_errors(topic, k=1, fallback=False))
    except Exception:
        return False


def decide(wager_row: dict, assessment, raw_input: str, *, now: float | None = None,
           recent: list[dict] | None = None) -> dict:
    """The route for one wager row. Pure apart from read-only lookups (retraction ledger, own shadow log)."""
    now = time.time() if now is None else now
    gap = float(wager_row.get("gap", 0.0) or 0.0)
    input_type = str(wager_row.get("input_type", "") or "")
    topic = topic_of(raw_input)
    mtype = missing_context_type(assessment)
    out = {"ts": round(now, 1), "stop": "frontier_note", "line": "recall_wager", "dose": "cup",
           "cycle_id": wager_row.get("cycle_id", ""), "input_type": input_type, "gap": round(gap, 3),
           "missing_context_type": mtype, "slot": _SLOTS[mtype], "topic": topic, "question_candidate": "",
           "route": "", "fed": False}
    if gap < FAIL_GAP:
        out["route"] = "not_failed"
    elif _is_correction(input_type, raw_input):
        out["route"] = "correction"
    elif _has_retraction(topic):
        out["route"] = "retraction"
    elif len(topic) < MIN_TOPIC:
        out["route"] = "no_topic"
    else:
        births = _recent_births(now) if recent is None else recent
        tt = _toks(topic)
        if any(tt and (ot := _toks(b.get("topic", ""))) and len(tt & ot) / max(1, len(tt | ot)) > TOPIC_JACCARD
               for b in births):
            out["route"] = "habituated"
        elif len(births) >= MAX_PER_WINDOW:
            out["route"] = "capped"
        else:
            out["route"] = "birth"
            out["question_candidate"] = question_for(mtype, topic)
    out["value"] = {"route": out["route"], "missing_context_type": mtype}
    return out


def feed(wager_row: dict | None, assessment, raw_input: str = "") -> dict | None:
    """Called by recall_wager.place() with the wager row it just wrote. Logs the route; on `birth` with the flag on,
    births the question on the frontier. Returns the logged row, or None. Never raises into the cycle."""
    try:
        if not wager_row:
            return None
        row = decide(wager_row, assessment, raw_input)
        if row["route"] == "birth" and WAGER_CURIOSITY:
            from core import frontier as _fr
            ent = _fr.note_question_ex(row["question_candidate"], SOURCE, slot=row["slot"],
                                       about=row["missing_context_type"], allow_self=True)
            row["fed"] = ent is not None
            if ent is not None:
                row["q_id"] = ent.get("id")
        shadow = profile.guard_path(_SHADOW)
        shadow.parent.mkdir(parents=True, exist_ok=True)
        with open(shadow, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row
    except profile.NonLiveWriteError as exc:
        logger.debug("[wager_curiosity] refused (non-fatal): %s", exc)
        return None
    except Exception as exc:
        logger.debug("[wager_curiosity] feed failed (non-fatal): %s", exc)
        return None

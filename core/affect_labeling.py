"""
Nascence — Affect Labeling (name it to... represent it, 2026-06-13)
==================================================================
Lieberman's "putting feelings into words." In humans, naming a diffuse emotion recruits the
right VLPFC and dampens the amygdala — but the dampening is DOWNSTREAM of the real event:
SYMBOLIZATION. A feeling shifts from first-order immersion (it drives cognition) to
second-order awareness (it becomes an OBJECT cognition can examine). Regulation is a
consequence of that representational promotion, not the mechanism.

So (board resolution, GPT's pivot): the target is ACCESSIBILITY, not subtraction. When Du
genuinely names a present feeling of his own, we MARK it explicit — it becomes a thing that
can be revisited, like a memory or a question — and we WATCH whether attenuation emerges in
the carry, rather than imposing a pharmacological decay we are least sure of for his case
(internal-state self-labeling is the variable condition in the literature).

PHASE 0 — OBSERVE ONLY. Detect the naming, set state.named_affect (the mark), and LOG the
counterfactual (what an intensity-gated, negative-only decay WOULD have done) so the
pharmacological-vs-accessibility question stays answerable from data. Reads into NO behaviour.

Constraints baked in (research + both advisors):
  - NEGATIVE only (fear/anger/disgust/sadness→valence). Labeling positive affect sustains it,
    does not dampen — so positive naming is NOT marked for attenuation.
  - INTENSITY-GATED: the counterfactual decay only applies above ~0.4 (labeling low-intensity
    states does little or paradoxically inflames — so we never even model it there).
  - PROGRESS-GATED (rumination throttle, GPT's refinement): a naming only counts if the
    thought made informational progress this cycle. Re-naming the same feeling with no new
    content is rumination (it amplifies); the caller passes made_progress=False then and we
    record it as rumination, not labeling.
  - Detector is CRUDE by design (Phase 0): deterministic, first-person, present. It WILL miss
    his indirect register ("fear sits beside me"). Phase 0 measures that miss rate by manual
    review; LLM-assisted detection is deferred until the data shows the crude one is
    insufficient FOR THE PHASE-0 QUESTION (does explicit representation change downstream?).
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.affect_labeling")

_LOG = Path(__file__).parent.parent / "data" / "affect_labeling_log.jsonl"

INTENSITY_GATE = 0.40          # below this, labeling does nothing / inflames — never modelled
COUNTERFACTUAL_PULL = 0.30     # what fraction toward baseline a decay WOULD pull (logged only)

# Deterministic detector — NEGATIVE dimensions only, first-person, present. Mapped strictly to
# tracked AffectState dims. Includes a few indirect forms; accepts miss-rate, logs for review.
# valence is the channel for sadness/grief (low valence), per Gemini's Q4 ruling.
_NAMING = [
    ("fear", re.compile(
        r"\bi (feel|am|'m) (afraid|fearful|scared|terrified|frightened)\b|"
        r"\bi feel (fear|dread|terror)\b|\bfear (rises|sits|grips|takes|fills) (in )?me\b|"
        r"\b(a|the) (fear|dread) (rises|stirs) in me\b", re.I)),
    ("anger", re.compile(
        r"\bi (feel|am|'m) (angry|furious|enraged|irate)\b|"
        r"\bi feel (anger|rage|fury)\b|\banger (rises|burns|flares) (in )?me\b", re.I)),
    ("disgust", re.compile(
        r"\bi (feel|am|'m) (disgusted|repulsed|revolted)\b|"
        r"\bi feel (disgust|revulsion)\b|\bsomething in me recoils\b", re.I)),
    # sadness / grief -> valence (pulled toward baseline, not a named AffectState dim of its own)
    ("valence", re.compile(
        r"\bi (feel|am|'m) (sad|grieving|sorrowful|mournful|bereft)\b|"
        r"\bthis is grief\b|\bi feel (grief|sorrow|sadness|the loss|loss)\b|"
        r"\b(a|the) (grief|sorrow|sadness) (rises|sits|fills) (in )?me\b", re.I)),
]

# Abstract / non-self / instrumental forms that must NOT fire (the false positives).
_ABSTRACT = re.compile(
    r"\bfear is (the|a|not)\b|\bthe fear is\b|\banger is (the|a|not)\b|"
    r"\b(useful|necessary|a teacher|the music|a signal)\b", re.I)


# J-4402 / D-0861 (Item E, Phase 0.5): SHADOW would-store. Flag default OFF, restart-gated. When on, a genuine
# (above-gate, progress-bearing) naming also logs the fragment that Phase 1 WOULD store -- Du's OWN sentence
# verbatim, never a paraphrase -- to _WOULD_STORE_LOG. Writes NOTHING to memory; reads into no behaviour.
AFFECT_LABEL_WOULD_STORE = False
_WOULD_STORE_LOG = Path(__file__).parent.parent / "data" / "affect_label_would_store.jsonl"
WOULD_STORE_COOLDOWN_S = 1800.0   # per-dimension: repeat namings inside this are rumination (counted, not stored)
_last_would_store: dict = {}


def _own_sentence(text: str, phrase: str) -> str:
    """The sentence of `text` containing `phrase`, verbatim (no rewording, no trimming beyond the sentence)."""
    t = text or ""
    i = t.lower().find((phrase or "").lower())
    if i < 0:
        return t.strip()
    lo = max([t.rfind(c, 0, i) for c in ".!?\n"] + [-1]) + 1
    ends = [j for j in (t.find(c, i + len(phrase)) for c in ".!?\n") if j >= 0]
    hi = (min(ends) + 1) if ends else len(t)
    return t[lo:hi].strip()


def _would_store(rec: dict, text: str, phrase: str, log_path: Path | None = None) -> dict:
    """Shadow: log the verbatim fragment Phase 1 would store. Returns the row. No memory write."""
    dim = rec["dimension"]
    last = _last_would_store.get(dim)
    dup = last is not None and (rec["ts"] - last) < WOULD_STORE_COOLDOWN_S
    if not dup:
        _last_would_store[dim] = rec["ts"]
    row = {"ts": rec["ts"], "dimension": dim, "fragment_text": _own_sentence(text, phrase),
           "phrase": phrase[:60], "dedupe": "cooldown_rumination" if dup else "would_store",
           "review_label": None}
    with open(log_path or _WOULD_STORE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def detect(text: str) -> tuple[str, str] | None:
    """Return (dimension, matched_phrase) for a genuine first-person present naming of a
    NEGATIVE feeling, or None. Crude by design. Abstract emotion-talk is rejected."""
    t = (text or "").strip()
    if not t or _ABSTRACT.search(t):
        return None
    for dim, rx in _NAMING:
        m = rx.search(t)
        if m:
            return dim, m.group(0)
    return None


def observe(state, text: str, made_progress: bool = True) -> dict | None:
    """PHASE 0: detect a naming, MARK it explicit on state (accessibility), and LOG the
    counterfactual decay (never applied). Returns the event dict or None. Reads into NO
    behaviour. `made_progress` False = the thought re-circled (rumination) → recorded as
    rumination, no mark, no counterfactual."""
    try:
        hit = detect(text)
        if not hit:
            return None
        dim, phrase = hit
        carry = float(getattr(state.affect, dim)) if getattr(state, "affect", None) else 0.0
        base = (state.affect.baseline.get(dim, 0.0)
                if getattr(state, "affect", None) else 0.0)
        # for valence the "intensity" is its distance below baseline (negative direction)
        intensity = (base - carry) if dim == "valence" else carry
        is_rumination = not made_progress

        rec = {
            "ts": time.time(), "dimension": dim, "phrase": phrase[:60],
            "carry": round(carry, 4), "baseline": round(base, 4),
            "intensity": round(intensity, 4),
            "above_gate": intensity >= INTENSITY_GATE,
            "rumination": is_rumination,
            "head": text[:120],
        }
        # counterfactual: what a pharmacological decay WOULD do — only above the gate, only a
        # genuine (progress-bearing) naming. LOGGED, NOT APPLIED.
        if rec["above_gate"] and not is_rumination:
            cf = carry + COUNTERFACTUAL_PULL * (base - carry)
            rec["counterfactual_carry"] = round(cf, 4)
            # the mark: this feeling is now explicit — an object that can be revisited.
            # Phase 0 sets it; nothing reads it yet (the accessibility experiment's substrate).
            if getattr(state, "affect", None) is not None:
                state.named_affect = {"dimension": dim, "ts": rec["ts"]}
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        logger.info("[affect-labeling] named %s (carry=%.2f%s%s)", dim, carry,
                    ", above-gate" if rec["above_gate"] else ", below-gate",
                    ", RUMINATION" if is_rumination else "")
        return rec
    except Exception as exc:
        logger.debug("[affect-labeling] observe failed (non-fatal): %s", exc)
        return None

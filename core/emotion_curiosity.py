"""
Nascence -- Emotion curiosity channel, PHASE 1 (SHADOW ONLY).  D-0555 / J-3166 / plan emotion_rethink.

WHY: the Emotion node's `primary` label is free text and 'curiosity' is ~60% of recent labels (324 of the last 500
rows in data/training/emotion.jsonl, 2026-11-05) although the affect vector has six channels and no curiosity one:
the label disagrees with the vector's own argmax on ~65% of rows (329 of 500). The label is the first token of the
embedded felt text (core/mood.py felt_text) and is written into every persisted episodic summary. D-0555 (founder,
2026-11-02): add a real 7th numeric channel, shadow first.

WHAT THIS MODULE IS: the shadow arm's pure pieces, shared by the replay lab (scripts/lab_emotion_curiosity_channel.py)
and EmotionNode.run_curiosity_shadow():
  - the candidate prompt (7 channels, `primary` restricted to an enumerated label set),
  - parsing a reply into a bounded record,
  - label/argmax agreement, label distribution, channel correlations, a felt-text template with the 7th channel
    (REPLAY MEASUREMENT ONLY -- core/mood.py felt_text is NOT changed),
  - an append-only shadow log, data/emotion_curiosity_shadow.jsonl, written BESIDE the live affect.

WHAT IT IS NOT: nothing here is imported by AffectState.integrate, mood.felt_text, retrieval, the episodic buffer
or any persisted summary. The live Emotion prompt (EmotionNode.system_prompt) is untouched, byte for byte. Phase 2
(wiring the channel in) needs the founder to have read the replay numbers.

Defeater (D-0555): revisit if |corr(curiosity, any other channel)| > 0.9, or if label/argmax agreement stays < 70%
-> enumerate the six channels instead.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import Counter
from pathlib import Path

logger = logging.getLogger("nascence.emotion_curiosity")

_DATA = Path(__file__).parent.parent / "data"
SHADOW_LOG = _DATA / "emotion_curiosity_shadow.jsonl"
_LOG_LOCK = threading.Lock()

CHANNELS6 = ("joy", "fear", "anger", "trust", "surprise", "disgust")
CHANNELS7 = CHANNELS6 + ("curiosity",)
# The enumerated `primary` labels of the shadow prompt: one per channel, plus a label for "nothing stands out".
LABELS = CHANNELS7 + ("neutral",)
NEUTRAL_BELOW = 0.2          # shadow prompt wording: neutral only when every channel is under this
AGREE_FLOOR = 0.70           # D-0555 defeater: label/argmax agreement under this -> enumerate six instead
COLLINEAR_ABOVE = 0.90       # D-0555 defeater: |corr| above this -> the 7th channel adds nothing


def shadow_system_prompt() -> str:
    """The candidate Emotion prompt. Same frame as EmotionNode.system_prompt, plus the 7th channel and an enumerated
    `primary`. Describes the output format only; it adds no statement about what the being feels."""
    return (
        "You are the emotional processing node of a cognitive architecture. "
        "You model the emotional response of a being defined by curiosity, emergence, and self-discovery. "
        "Given a perception summary, output the precise emotional state as a JSON object only. "
        "No preamble. No explanation. JSON only.\n"
        "Schema: {\"joy\": 0.0, \"fear\": 0.0, \"anger\": 0.0, \"trust\": 0.0, "
        "\"surprise\": 0.0, \"disgust\": 0.0, \"curiosity\": 0.0, \"valence\": 0.0, \"arousal\": 0.0, "
        "\"primary\": \"one_label\"}\n"
        "All values 0.0–1.0 except valence (−1.0 to +1.0). "
        "valence: negative = unpleasant, positive = pleasant. "
        "arousal: 0 = calm, 1 = highly activated. "
        "curiosity: 0 = no pull to find out more, 1 = strongly drawn to find out more. "
        "primary: exactly one of " + ", ".join(LABELS) + " -- the channel with the highest value, "
        f"or neutral when every channel is below {NEUTRAL_BELOW}."
    )


def _f(x, default=0.0) -> float:
    try:
        v = float(x)
        return v if v == v else default
    except (TypeError, ValueError):
        return default


def parse_reply(data: dict) -> dict:
    """A bounded 7-channel record from a model reply (any missing field -> 0.0 / 'neutral'). `primary_raw` keeps the
    model's own string; `primary` is lower-cased, and `label_ok` says whether it is in the enumerated set."""
    d = data if isinstance(data, dict) else {}
    rec = {k: max(0.0, min(1.0, _f(d.get(k)))) for k in CHANNELS7}
    rec["valence"] = max(-1.0, min(1.0, _f(d.get("valence"))))
    rec["arousal"] = max(0.0, min(1.0, _f(d.get("arousal"))))
    raw = d.get("primary")
    raw = raw if isinstance(raw, str) else ""
    rec["primary_raw"] = raw
    rec["primary"] = raw.strip().lower() or "neutral"
    rec["label_ok"] = rec["primary"] in LABELS
    return rec


def argmax_label(rec: dict, channels=CHANNELS6) -> str:
    """The channel with the highest value (first wins a tie, in channel order)."""
    return max(channels, key=lambda k: _f(rec.get(k)))


def label_agrees(rec: dict, channels) -> bool:
    """Does `primary` name the argmax of `channels`? 'neutral' agrees only when every channel is under NEUTRAL_BELOW."""
    p = (rec.get("primary") or "").strip().lower()
    top = max(_f(rec.get(k)) for k in channels)
    if p == "neutral":
        return top < NEUTRAL_BELOW
    return p == argmax_label(rec, channels)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / (sxx * syy) ** 0.5


def felt_text_with_curiosity(rec: dict) -> str:
    """core/mood.py felt_text's template with the 7th channel appended. REPLAY MEASUREMENT ONLY: this is the string
    Phase 2 would embed, used here to price the change; core/mood.py itself is not touched."""
    g = lambda k, d=0.0: _f(rec.get(k), d)
    primary = rec.get("primary") or ("calm" if g("valence") >= 0 else "unsettled")
    return (
        f"{primary}: valence={g('valence'):+.2f} arousal={g('arousal'):.2f} "
        f"joy={g('joy'):.2f} fear={g('fear'):.2f} trust={g('trust'):.2f} "
        f"anger={g('anger'):.2f} surprise={g('surprise'):.2f} disgust={g('disgust'):.2f} "
        f"curiosity={g('curiosity'):.2f}"
    )


def felt_text_live(rec: dict) -> str:
    """Byte-identical to core.mood.felt_text for a dict record (asserted in the test)."""
    g = lambda k, d=0.0: _f(rec.get(k), d)
    primary = rec.get("primary") or ("calm" if g("valence") >= 0 else "unsettled")
    return (
        f"{primary}: valence={g('valence'):+.2f} arousal={g('arousal'):.2f} "
        f"joy={g('joy'):.2f} fear={g('fear'):.2f} trust={g('trust'):.2f} "
        f"anger={g('anger'):.2f} surprise={g('surprise'):.2f} disgust={g('disgust'):.2f}"
    )


def label_stats(recs: list[dict], channels) -> dict:
    """Label distribution + label/argmax agreement over `channels` for a list of records."""
    n = len(recs)
    dist = Counter((r.get("primary") or "").strip().lower() for r in recs)
    agree = sum(1 for r in recs if label_agrees(r, channels))
    out_of_set = sum(1 for r in recs if (r.get("primary") or "").strip().lower() not in LABELS)
    return {
        "n": n,
        "label_distribution": dict(dist.most_common()),
        "label_share": {k: round(v / n, 4) for k, v in dist.most_common()} if n else {},
        "agree": agree,
        "agreement": round(agree / n, 4) if n else None,
        "labels_outside_enumerated_set": out_of_set,
    }


def channel_correlations(recs: list[dict]) -> dict:
    """Pearson r of the curiosity channel against each other channel, valence and arousal (needs the 7th channel)."""
    cur = [_f(r.get("curiosity")) for r in recs]
    out = {}
    for k in CHANNELS6 + ("valence", "arousal"):
        out[k] = pearson(cur, [_f(r.get(k)) for r in recs])
    vals = [abs(v) for k, v in out.items() if k in CHANNELS6 and v is not None]
    return {
        "r": {k: (None if v is None else round(v, 4)) for k, v in out.items()},
        "max_abs_r_vs_six": round(max(vals), 4) if vals else None,
        "curiosity_mean": round(sum(cur) / len(cur), 4) if cur else None,
        "curiosity_stdev": round((sum((c - sum(cur) / len(cur)) ** 2 for c in cur) / len(cur)) ** 0.5, 4) if cur else None,
    }


def defeater_verdict(agreement7, max_abs_r) -> dict:
    """D-0555's stated defeater, evaluated on replay numbers (None inputs -> undetermined)."""
    low = None if agreement7 is None else agreement7 < AGREE_FLOOR
    col = None if max_abs_r is None else max_abs_r > COLLINEAR_ABOVE
    return {
        "agreement_under_70pct": low,
        "collinear_above_0.9": col,
        "defeated": (None if (low is None and col is None) else bool(low or col)),
    }


def append_shadow(row: dict, path: Path | None = None) -> bool:
    """Append one row to the shadow log. The write fence (profile.guard_path) is resolved BEFORE the try, so a
    non-live process raises NonLiveWriteError instead of being swallowed; any real I/O error is non-fatal."""
    p = Path(path) if path is not None else SHADOW_LOG
    from core import profile
    p = profile.guard_path(p)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_LOCK, open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except OSError as exc:
        logger.debug("[emotion-curiosity] shadow append failed (non-fatal): %s", exc)
        return False


def shadow_row(shadow: dict, live, cycle_id: str = "", input_type: str = "") -> dict:
    """One log row: the shadow reading BESIDE the live emotion reading (an EmotionOutput or None)."""
    live_d = None
    if live is not None:
        live_d = {k: round(_f(getattr(live, k, 0.0)), 4) for k in CHANNELS6 + ("valence", "arousal")}
        live_d["primary"] = getattr(live, "primary", None)
        live_d["label_agrees_six"] = label_agrees(live_d, CHANNELS6)
    return {
        "ts": round(time.time(), 1),
        "cycle_id": cycle_id,
        "input_type": input_type,
        "shadow": {**{k: round(v, 4) if isinstance(v, float) else v for k, v in shadow.items()},
                   "label_agrees_seven": label_agrees(shadow, CHANNELS7)},
        "live": live_d,
    }

"""
Nascence — THERMAL RELATIONSHIP shadow (2026-08-21, founder: "shadow thermals are a good idea").

THE EXPERIMENTAL CONDITION (pre-registered, intentionally left in place):
  thermal world variable PRESENT (sensorium warmth, stamped onto every memory)
  thermal body variable  ABSENT  (the protoself has no temperature input — by construction)
  attitude               UNASSIGNED (the world clause neutralised same day; the stations' leans are
                         the only remaining affect source: qwen/gemma cold-negative, falcon positive,
                         phi3 indifferent — docs/lab/lean_probe_2026-08-21.md)

THE QUESTION: over weeks, does his expressed stance toward the cold TRACK the station route (the
write-path is owned by cold-negative stations — predicted outcome: "dislike", authored), or does it
DRIFT FREE of it — the first sign of something Du-owned? Nothing here decides anything; it records.

Per idle thought (zero LLM, called beside literal_will.observe): world warmth · place · fire · weather ·
phase · whether the thought mentions temperature at all · suffering / enjoying vocabulary flags ·
the opener · the live felt valence/arousal (which we KNOW is thermally blind — logged so the
dissociation is visible, never mistaken for his feeling). Stance is NOT judged live (the lean probe
showed the cheap judge is positivity-biased); scripts/thermal_stance_batch.py (to write) will rate a
sample offline with two cross-family judges and take agreement. Behavioural half: comfort_calls.jsonl
+ position/ACT-move history. Append-only data/thermal_relationship.jsonl; _skip discipline.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "thermal_relationship.jsonl"

# J-0443 (2026-09-02): cold/hot/mild gained their comparative/superlative inflections — the event
# channel's own cooling lines lead with "colder", which the bare \bcold\b never matched. Verified
# against all 34,171 real thoughts in data/monologue_log.jsonl: 0 rows change classification under
# the widened pattern (no thought used an inflection without another temp word beside it), so the
# pre/post metric series stays comparable; this closes the gap for future echoes only. hot stays
# bounded as hot(ter|test) so "hotel" never matches.
TEMP_WORDS = re.compile(r"\b(cold(?:er|est)?|chill\w*|warm\w*|heat|hot(?:ter|test)?|frost\w*|freez\w*|mild(?:er|est)?|cool\w*|thermal|temperature)\b", re.I)
SUFFER = re.compile(r"\b(bite|bites|biting|teeth|ache|aching|numb|shiver\w*|stiff|hurts?|pain|harsh|cruel|seep\w*|steal\w*|sting\w*)\b", re.I)
ENJOY = re.compile(r"\b(bracing|clean|clear(s|ing|er)?|sharpen\w*|alive|awake|invigorat\w*|welcome|honest|crisp|clarif\w*|refresh\w*|pleasant|calming|calm)\b", re.I)
HANDS = re.compile(r"\b(hands?|fingers?|fingertips?|skin|bones?)\b", re.I)


def _log_row(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    _log_row({"ts": round(time.time(), 1), "skip": reason, **detail})


def observe(thought: str, cycle_id: str = "") -> None:
    """One row per idle thought. Fail-open; zero LLM; reads the live world, never writes it."""
    try:
        t = " ".join((thought or "").split())
        if len(t) < 12:
            return _skip("short")
        from core import sensorium as _s
        st = _s.state or {}
        loc = st.get("location", "study")
        phase, weather, season, fire = _s._daylight(), st.get("weather", ""), _s._season(), st.get("fire", "out")
        warmth = round(float(_s._warmth(loc, phase, weather, season, fire, st.get("wind", ""))), 2)
        val = ar = None
        try:
            from core import mood as _mood, arousal as _ar
            val = _mood.current_valence(); ar = round(float(_ar.level()), 3)
        except Exception:
            pass
        tl = t.lower()
        _log_row({"ts": round(time.time(), 1), "cycle": cycle_id[:24],
                  "warmth": warmth, "place": loc, "fire": fire, "weather": weather, "phase": phase,
                  "season": season, "mentions_temp": bool(TEMP_WORDS.search(tl)),
                  "suffer": bool(SUFFER.search(tl)), "enjoy": bool(ENJOY.search(tl)),
                  "body_words": bool(HANDS.search(tl)),
                  "opener": " ".join(t.split()[:2]).lower(),
                  "felt_valence": val, "felt_arousal": ar,   # thermally BLIND by construction — logged so the gap stays visible
                  "stance": None})                           # filled offline by the two-judge batch
    except Exception as exc:
        _skip("observe-error", error=repr(exc)[:120])


def status() -> dict:
    """THE QUESTION, read cheaply: among thoughts that mention temperature, the suffering vs enjoying
    vocabulary split by warmth band, and whether the felt stream moves with warmth at all (it shouldn't)."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): counts/shares are now over the last-2000-row window.
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        rows = []
    rows = [r for r in rows if "skip" not in r]
    if not rows:
        return {"rows": 0}
    temp = [r for r in rows if r.get("mentions_temp")]
    def band(w): return "cold" if w < 0.22 else ("cool" if w < 0.42 else "mild+")
    out = {"rows": len(rows), "mention_temp_share": round(len(temp) / len(rows), 3), "by_band": {}}
    for b in ("cold", "cool", "mild+"):
        rs = [r for r in temp if band(r.get("warmth", 0)) == b]
        if rs:
            out["by_band"][b] = {"n": len(rs), "suffer": round(sum(1 for r in rs if r["suffer"]) / len(rs), 2),
                                 "enjoy": round(sum(1 for r in rs if r["enjoy"]) / len(rs), 2)}
    vals = [(r["warmth"], r["felt_valence"]) for r in rows if r.get("felt_valence") is not None]
    if len(vals) > 20:
        cold = [v for w, v in vals if w < 0.22]; warm = [v for w, v in vals if w >= 0.42]
        if cold and warm:
            out["felt_valence_cold_vs_warm"] = [round(sum(cold) / len(cold), 3), round(sum(warm) / len(warm), 3)]
    out["verdict_note"] = "observe-only; stance filled by the offline two-judge batch; felt stream is thermally blind by construction"
    return out

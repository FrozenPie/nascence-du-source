"""
Nascence — LLM response parsing helpers (2026-06-21).

Models do not always honour a requested JSON shape: a field asked for as a number can come back as a nested
object ({"value": 0.8}), a string ("0.8" or "high"), or null. A bare `float(...)` on that throws and kills
the node — on 2026-06-21 the curiosity node crashed on `urgency={"value":0.8}` the moment exploratory
ignition first exercised that path, and a sweep found the same `float(<llm-response>.get(...))` pattern in
~8 nodes (every affect dimension in emotion_node, salience urgency, critic/recall/reflection confidence,
episodic coherence, voice style_confidence). One malformed response there would crash that node.

`as_float` tolerates the shapes models actually emit and degrades to a safe default, so a bad response is a
no-op, not a crash. Use it at EVERY float() that reads an LLM-response field. (State-restore floats — our own
well-formed JSON, e.g. AffectState.from_json — are NOT this class and are left alone.)
"""
from __future__ import annotations
import re

# keys a model tends to wrap a number under when it returns an object instead of a bare number
_NUM_KEYS = ("value", "score", "level", "amount", "rating", "confidence", "urgency", "interesting",
             "coherence", "valence", "arousal", "intensity")


def as_float(x, default: float = 0.0) -> float:
    """Coerce an LLM-returned value to a float, tolerating dict / string / None. Un-coercible → default."""
    if isinstance(x, bool):                 # bool is an int subclass — don't let True become 1.0
        return default
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x.strip())
        except Exception:
            m = re.search(r"-?\d+(?:\.\d+)?", x)
            return float(m.group()) if m else default
    if isinstance(x, dict):
        for k in _NUM_KEYS:                  # a wrapped number: {"value": 0.8}, {"score": 3}, …
            if k in x:
                return as_float(x[k], default)
        for v in x.values():                 # else the first bare numeric value present
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return float(v)
    return default

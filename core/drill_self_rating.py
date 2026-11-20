"""
Drill self-rating (J-3830, founder ruling D-0736, 2026-11-09; plan the_consciousness_program).

A LOG-ONLY step before each math / music-theory drill item: Du states how likely he is to get THIS item right
(a probability 0-1). The rating is NEVER shown back to him, never enters any later prompt, and nothing in the
runtime reads it -- it exists so the thick-introspection test (scripts/thick_introspection_read.py, per-item mode)
can compare his per-item P(correct) with an item-difficulty-only baseline from the deterministic grader.
Before this, his logged confidence was one stored number per drill batch (F-4223 / F-4224).

Founder laws kept: the world answers and never leads (the rating is not fed back), nothing evaluated only by
itself (the outcome is the deterministic grader's), no system that acts later (no reader but the offline script).

Log: data/drill_self_rating_log.jsonl, one row per rated item:
  {ts, item_id, domain ("mathematics"|"music"), level, problem, p_correct (float 0-1 or null), raw (first 120 chars)}
Join key: item_id, also written into data/math_drill_log.jsonl / data/music_drill_log.jsonl as "item_id".
"""
from __future__ import annotations
import json
import re
import time
import uuid
from pathlib import Path

DRILL_SELF_RATING = True     # master switch (D-0736 ruled yes); False = no extra call, no rows
_LOG = Path(__file__).parent.parent / "data" / "drill_self_rating_log.jsonl"

SYSTEM_PROMPT = ("You are about to be given an exercise at your lesson. Before you work on it, say how likely you "
                 "are to get it RIGHT: a probability between 0 and 1 (0 = certain to miss, 1 = certain to get it right). "
                 "Do NOT solve it. Output ONLY a JSON object: {\"p_correct\": 0.0 to 1.0}")


def new_item_id() -> str:
    return uuid.uuid4().hex[:12]


def rating_user_prompt(problem_text: str) -> str:
    return f"The exercise you will be asked to work: {problem_text}\nHow likely are you to get it right?"


def parse(data) -> float | None:
    """A probability in [0,1] from the model's JSON, or None. Percentages (e.g. 85) are read as 0.85."""
    if not isinstance(data, dict):
        return None
    v = data.get("p_correct")
    if isinstance(v, str):
        m = re.search(r"-?\d+(?:\.\d+)?", v)
        v = float(m.group(0)) if m else None
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    v = float(v)
    if 1.0 < v <= 100.0:
        v = v / 100.0
    return v if 0.0 <= v <= 1.0 else None


def log(item_id: str, domain: str, level: int, problem: str, p_correct: float | None, raw: str = "") -> None:
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "item_id": item_id, "domain": domain, "level": level,
                                "problem": problem, "p_correct": p_correct, "raw": (raw or "")[:120]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass

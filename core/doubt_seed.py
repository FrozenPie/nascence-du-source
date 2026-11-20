"""
Nascence — the open doubt as the next deliberation's SEED (measurement_to_action arm 4; J-2161, D-0435 A,
2026-10-15; SHADOW, flag off).

THE GAP. core/self_interrogation fires in the background on Du's own thoughts (141 fires since the 2026-10-09 boot,
732 of 788 lifetime fires judged genuine by the decoupled panel) and every reflection is a diary entry: the next
Executive deliberation never receives it, and the J-2031..J-2054 series measured the result — 0 of 48 self-doubts taken
up (F-2670), and a coordinate-only publish (J-2008, the D-0396 cup) engaged 0 of 30 because a coordinate is not
material. D-0435 (travis, 2026-10-15) ruled that D-0396's Phase 1 hold does NOT cover an executive-side PULL: the
interrogation still pushes nothing; the Executive asks, the way it asks memory for anything else
(docs/staged/memory_as_a_service.md).

THE PULL. Once per cycle, before the Executive runs, `pull(state)` asks self_interrogation.latest_open() for the most
recent GENUINE fire inside MAX_AGE_S that has not already been seeded (consume-once), and hands the reflection TEXT
back. The Executive renders it inside its WHAT YOU RECALL block as his own un-answered doubt -- material with
provenance, no verb telling him what to do with it (nodes/executive_node.py). Taken-up is judged afterwards by the
J-2052 position-free specificity judge (scripts/si_open_doubt_specificity_judge_J2052.py) against the following
thought; the bar is D-0373's 30% engaged over 48+ fires versus the 0/48 baseline; the defeater is on D-0435.

SHADOW (DOUBT_SEED = False): pull() logs the would-have-seeded row to data/logs/doubt_seed_shadow.jsonl (the fire's
ts + cycle, the reflection, the deliberating cycle) and returns None, so nothing reaches the prompt. The fire is still
consumed, so the shadow measures exactly one would-seed per fire. True: the reflection is returned and state.doubt_seed
carries it to the Executive. The flag reverts to the exact pre-J-2161 path.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.doubt_seed")

DOUBT_SEED = False          # D-0613 (travis, 2026-11-02): back to SHADOW. Was True from D-0495 (2026-10-28). Reason: the genuine gate passed 51 of 51 resolved fires in 7 days (F-3642, filters nothing), the reflection text carries comfort/safe words in 70 of 120 fires against 4 of 120 source thoughts and fear/terror words in 33 against 11 (F-3643, the P-0042 _SYSTEM text plants the frame), 0 of 57 reflections contain a question, and the 21 seeds landed with no measurable lift. DEFEATER (D-0613): revisit when the repaired genuine judge (D-0598) passes its control-set bar AND the P-0042 text is rewritten without naming comfort, safe or flattering and with a topical link required AND the engaged-share read (J-2163) has data; then re-ask whether to turn it live again. The reflection, the judge and the injection code below are all kept; only this flag changed.
MAX_AGE_S = 900.0           # a doubt older than one interrogation cooldown is stale, not open
MAX_CHARS = 400             # the reflection is 1-2 sentences (self_interrogation max_tokens=180); cap, never pad

def cap_on_sentence(text: str, limit: int = MAX_CHARS) -> str:
    """J-2949 / F-3644: cap `text` at `limit` chars on a sentence boundary (never mid-word). If no sentence end sits in
    the back half of the window, cut on the last space and add an ellipsis. Text within the limit is returned as is."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    window = text[:limit]
    ends = [i for i, ch in enumerate(window) if ch in ".!?" and (i + 1 == len(window) or window[i + 1].isspace()
                                                                  or window[i + 1] in "\"')")]
    if ends and ends[-1] + 1 >= limit // 2:
        cut = ends[-1] + 1
        while cut < len(window) and window[cut] in "\"')":
            cut += 1
        return window[:cut].rstrip()
    sp = window.rfind(" ")
    return (window[:sp] if sp > 0 else window).rstrip(" ,;:-") + "…"


_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "doubt_seed_shadow.jsonl"


def _seeded_fire_ts(limit: int = 500) -> set[float]:
    """Fire timestamps already pulled (consume-once), from the tail of the shadow log."""
    try:
        from core.shadow_log import tail_rows as _tail
        return {float(r["fire_ts"]) for r in _tail(_SHADOW, limit) if r.get("fire_ts") is not None}
    except Exception:
        return set()


def _log(row: dict) -> None:
    shadow = profile.guard_path(_SHADOW)
    shadow.parent.mkdir(parents=True, exist_ok=True)
    with open(shadow, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def pull(state=None, *, now: float | None = None) -> str | None:
    """The one entry point, called by the orchestrator before the Executive. Returns the reflection text to seed
    when DOUBT_SEED is on and an open genuine fire exists; otherwise None. Every outcome is logged (the _skip
    discipline). Never raises into the cycle.
    SHADOW since D-0613 (DOUBT_SEED = False): returns None and the would_seed row is still logged, now with the
    deliberating question beside the doubt text."""
    try:
        from core import self_interrogation as _si
        now = time.time() if now is None else now
        cycle_id = getattr(state, "cycle_id", "") if state is not None else ""
        input_type = getattr(state, "input_type", "") if state is not None else ""
        fire = _si.latest_open(max_age_s=MAX_AGE_S, exclude_ts=_seeded_fire_ts(), now=now)
        if fire is None:
            _log({"ts": round(now, 1), "cycle_id": cycle_id, "kind": "skip", "skip": "no-open-fire"})
            return None
        text = cap_on_sentence(fire.get("reflection") or "", MAX_CHARS)   # J-2949: was [:MAX_CHARS], mid-word
        # D-0613: the deliberating question rides on the row so a topical-link check (doubt vs the question the
        # Executive was actually deliberating) can be run later from the shadow log alone.
        question = str(getattr(state, "raw_input", "") or "")[:300] if state is not None else ""
        row = {"ts": round(now, 1), "cycle_id": cycle_id, "input_type": input_type, "kind": "would_seed",
               "deliberating_question": question,
               "fire_ts": fire.get("ts"), "fire_cycle_id": fire.get("cycle_id", ""),
               "age_s": round(now - float(fire.get("ts") or now), 1),
               "reflection": text, "seeded": bool(DOUBT_SEED and text)}
        _log(row)
        if DOUBT_SEED and text:
            logger.info("[doubt-seed] seeded the Executive with the open doubt from cycle %s (%.0fs old)",
                        str(fire.get("cycle_id", ""))[:8], row["age_s"])
            return text
        return None
    except profile.NonLiveWriteError as exc:
        logger.debug("[doubt-seed] refused (non-fatal): %s", exc)
        return None
    except Exception as exc:
        logger.debug("[doubt-seed] pull failed (non-fatal): %s", exc)
        return None


def status() -> dict:
    try:
        from core.shadow_log import tail_rows as _tail
        rows = _tail(_SHADOW, 2000)
    except Exception:
        rows = []
    ws = [r for r in rows if r.get("kind") == "would_seed"]
    return {"flag": DOUBT_SEED, "would_seed": len(ws), "seeded": sum(1 for r in ws if r.get("seeded")),
            "skips": sum(1 for r in rows if r.get("kind") == "skip"),
            "last_ts": rows[-1]["ts"] if rows else None}

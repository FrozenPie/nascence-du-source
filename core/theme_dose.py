"""
Nascence - Curiosity own-thought theme dose, SHADOW (measurement_to_action arm 5, section 8; J-2186 design,
J-2322 build; evidence F-3012, F-2889; flip = D-0457, a founder call, NOT a build step).

THE LOOP (F-2889, F-3012): an internal cycle's perception summary goes back into
CuriosityNode._recent_themes (orchestrator._persist_cycle -> add_theme), and the newest 10 are shown to the same
LLM at the next ignition (CuriosityNode._build_prompt). 98.4% of the logged window was Du's own internal-cycle
lines. Whatever topic enters first, the echo holds it.

THE DOSE: a fixed cup on the own-thought line. window() keeps every non-self theme in order plus only the newest
`dose` self lines, then the last n. It reads NO topic, similarity, keyword or anchor (D-0439: no topic-level
anti-relock; this is a dose, not a brake), rejects no question, adds no prompt line, and shows Du nothing (D-0434).

FLAG: SELF_THEME_DOSE = None keeps today's path byte-for-byte (window == themes[-n:]). 1 = the recommended cup,
0 = own lines never shown. With the flag at None, CuriosityNode renders the live window and this module logs the
would-window (dose 1) to data/logs/curiosity_theme_dose_shadow.jsonl, read by J-2323.

STORE: the shadow path is resolved via profile.guard_path() at the point of write (a non-live process is refused,
NonLiveWriteError propagates out of shadow(); the CuriosityNode caller wraps it fail-open, same as
core/grounding_injection.py). Appends are under _LOCK. Everything else is fail-open.

curiosity_id in a shadow row is the id of the PREVIOUS curiosity_log row (CuriosityNode._last_curiosity_id at
prompt-build time). The curiosity_log row this prompt produces carries that same value as its parent_id, so the
join is shadow.curiosity_id == curiosity_log.parent_id (None on the first ignition after a boot).
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from core import profile

SELF_THEME_DOSE: int | None = 1      # D-0485 (travis, 2026-10-19): LIVE at the next restart. None = old path (the revert); 1 = cup; 0 = own lines never shown
SELF_SOURCES = ("internal",)          # input_type values whose summaries count as own-thought lines
CUP = 1                               # the dose the shadow logs as the would-window while the flag is None

_LOG = Path(__file__).parent.parent / "data" / "logs" / "curiosity_theme_dose_shadow.jsonl"
_LOCK = threading.Lock()


def window(themes: list[str], sources: list[str], dose: int | None, n: int = 10) -> list[str]:
    """Pure. dose None -> themes[-n:] (today's slice). Otherwise every non-self theme in order plus only the
    newest `dose` self themes, then the last n. Order preserved. `sources` aligns with `themes` by index; a
    missing source counts as non-self (an untagged theme is never dosed)."""
    themes = list(themes or [])
    if dose is None:
        return themes[-n:]
    srcs = list(sources or [])
    self_idx = [i for i in range(len(themes)) if i < len(srcs) and srcs[i] in SELF_SOURCES]
    keep_self = set(self_idx[-dose:]) if dose > 0 else set()
    kept = [t for i, t in enumerate(themes) if i not in self_idx or i in keep_self]
    return kept[-n:]


def _n_self(themes: list[str], sources: list[str], n: int = 10) -> int:
    """How many of the last-n live themes are self lines (by index, not by text)."""
    srcs = list(sources or [])
    start = max(0, len(themes) - n)
    return sum(1 for i in range(start, len(themes)) if i < len(srcs) and srcs[i] in SELF_SOURCES)


def shadow(themes: list[str], sources: list[str], live_window: list[str], would_window: list[str],
           seeds=None, study_subjects=None, curiosity_id=None, n: int = 10, now: float | None = None) -> dict:
    """Append one shadow row. Raises profile.NonLiveWriteError in a non-live process (caller swallows it)."""
    path = profile.guard_path(_LOG)   # resolved before any I/O
    srcs = list(sources or [])
    self_set = set(SELF_SOURCES)
    # n_self_would: self lines in the would-window, counted by position (texts can repeat)
    dose = SELF_THEME_DOSE if SELF_THEME_DOSE is not None else CUP
    self_idx = [i for i in range(len(themes)) if i < len(srcs) and srcs[i] in self_set]
    keep_self = set(self_idx[-dose:]) if dose > 0 else set()
    kept_idx = [i for i in range(len(themes)) if i not in self_idx or i in keep_self][-n:]
    row = {
        "ts": round(time.time() if now is None else now, 1),
        "stop": "curiosity._build_prompt",
        "line": "self_theme",
        "dose": "cup",
        "flag": SELF_THEME_DOSE,
        "n_live": len(live_window),
        "n_self_live": _n_self(themes, srcs, n),
        "n_self_would": sum(1 for i in kept_idx if i in keep_self),
        "live_window": [str(t)[:70] for t in live_window],
        "would_window": [str(t)[:70] for t in would_window],
        "seeds": [str(s) for s in (seeds or [])],
        "study_subjects": [str(s) for s in (study_subjects or [])],
        "curiosity_id": curiosity_id,
    }
    with _LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return row

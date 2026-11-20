"""
Nascence -- the Emissary's grade of a SELF-AUTHORED work, SHADOW ONLY (J-3203 implementing D-0591 part 2 / J-2926,
finding F-3606, F-3758, prompt row P-0090).  RESTART-GATED.

Before: nodes/inner_monologue_node._author awaited left_lane.grade_work(...) BEFORE filing the work, read a key
("score") the grader never returns, and threw the verdict away: 0 of 867 "ACT write -> authored" lines carried
"[Emissary", and a slow or failed judge delayed (or on a process stop, lost) a finished work.  Founder ruling D-0591
(2026-11-02): keep the grade as a SHADOW LOG only, recorded and moved AFTER write_tablet, until a rubric exists that
suits a self-set work and sees the whole of it.  NOTHING is fed from it: no return to Du, no competence entry, no
joy, no gate, no prompt line (the world answers, never leads).

Known caveats of this grade, stated so nobody reads the rows as a measure of the work (F-3758):
  * WRONG RUBRIC.  left_lane._WORK_GRADE_TASK frames the piece as "your friend's SCHOOLWORK ... the real thing he was
    set" with an empty reference, and marks down generality and self-projection -- which for a self-set analytical
    essay marks down exactly the abstraction it is.  (F-0874 already found this grader cannot tell confabulated
    composition from real.)
  * THE GRADER SEES ABOUT A FIFTH.  _author passes body[:2400] and grade_work cuts again to work[:2000]; works are
    multi-part pieces of median 9,526 chars (min 5,201, max 11,357), so it reads a median 21 percent -- the opening part.
    Each row records chars / graded_chars so that coverage is visible per row.
  * The judge is a different model family from the authors (gemma4:12b on the :11439 hub vs command-r7b / qwen3.5), the
    decoupled-judge rule holds; but the hub is cold-start slow (F-2619), so the call goes AFTER the filing, never before.

READER of data/work_grade_shadow.jsonl: status() below (summarize via core/shadow_log), read when the replacement
rubric job (J-3046 lab -> the D-0591 defeater: "a rubric for self-set works, given the whole work") is taken up; the
D-0591 defeater is what graduates or retires it.  Fail-open throughout: a missing hub (grade None) is recorded as a
fail_open row, a write refused or failed is swallowed, and nothing here can raise into _author.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from core import profile, shadow_log

logger = logging.getLogger("nascence.work_grade_shadow")

SHADOW_LOG = Path(__file__).parent.parent / "data" / "work_grade_shadow.jsonl"   # tests temp-path this
SHADOW_ENABLED = True            # False = a complete no-op (no hub call, no row)
SENT_CHARS = 2400                # what _author used to pass (body[:2400]); grade_work itself then cuts to 2000


def _row(topic: str, title: str, body: str, grade) -> dict:
    ok = isinstance(grade, dict) and grade.get("grounded") is not None
    g = None
    if ok:
        try:
            g = round(float(grade.get("grounded")), 3)
        except Exception:
            ok, g = False, None
    return {
        "ts": round(time.time(), 3),
        "title": str(title)[:120],
        "topic": str(topic)[:300],
        "words": len(str(body).split()),
        "chars": len(str(body)),
        "graded_chars": min(len(str(body)), SENT_CHARS, 2000),   # the 2000 is left_lane.grade_work's own cut
        "grounded": g,
        "feedback": (str(grade.get("feedback"))[:400] if ok and grade.get("feedback") is not None else None),
        "fail_open": not ok,             # True = hub unreachable / unparseable; grounded is None, not a real grade
    }


def record(topic: str, title: str, body: str, grade) -> bool:
    """Append one row for a graded (or fail-open) work.  guard_path at write time: a non-live importer's write to the
    real data/ path is refused, not redirected.  Never raises; returns True if a row was written."""
    if not SHADOW_ENABLED:
        return False
    try:
        path = profile.guard_path(SHADOW_LOG)
        return shadow_log.append(Path(path), _row(topic, title, body, grade))
    except Exception as exc:
        logger.debug("[work-grade-shadow] record failed (non-fatal): %s", exc)
        return False


async def grade_and_record(topic: str, title: str, body: str):
    """Ask the Emissary for its grade of an already-filed work, log it to the shadow file, and return the raw grade dict
    (or None) so the caller can show it in its own log line.  Call this AFTER the work is filed.  Never raises."""
    if not SHADOW_ENABLED:
        return None
    grade = None
    try:
        from core import left_lane as _ll
        grade = await _ll.grade_work(topic, "", body[:SENT_CHARS])
    except Exception:
        grade = None
    record(topic, title, body, grade)
    return grade


def status() -> dict:
    """Generic per-field summary of the shadow log (rows, grounded mean/min/max, chars, graded_chars, fail_open frac)."""
    return shadow_log.summarize(SHADOW_LOG, ["words", "chars", "graded_chars", "grounded", "fail_open"])

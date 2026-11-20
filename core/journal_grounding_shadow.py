"""
Nascence — Journal Grounding Shadow: the hard-enforcement grader for the roll-up pyramid
(journal_consolidation_pyramid.md §6 Q1, D-0006, 2026-08-23).

D-0006 (Travis): keep P1/P2 week/moon roll-ups SOFT (author from the level below, no gate) — but run an
Emissary-graded HARD check in SHADOW alongside it, observe-only, so real comparative data accrues on
whether soft grounding is actually letting anything confabulated through, before ever switching live.

Reuses the SAME decoupled-judge machinery `core/memory_levels.py` already uses to grade consolidation
gists against their sources — a week-cap IS a gist (one short entry standing in for its linked day-level
sources) in every way this judge cares about, so no new judge/prompt was built:
  - `left_lane.grade_gist_faithfulness(gist, sources)` — the Emissary's holistic plausibility grade,
    with an 'invented' list of phrases it believes the sources don't support.
  - `memory_levels.source_fidelity(gist, sources)` — the deterministic, non-LLM salient-word-presence
    sub-score (§14.1) — so this shadow data does not rest on the LLM judge alone.
  - `memory_levels.verify_invention_claims(invented, sources)` — the Black-Bear backstop: re-checks each
    'invented' accusation against the actual sources (and the wider store) before trusting it, since the
    judge itself can hallucinate an invention that is really just IN_SOURCE or a genuine CROSS_LINK.

OBSERVE-ONLY: never touches `journal_rollup.py`'s stored fragment, the WEEK_*.md file, or memory_links.
Logs one verdict row per graded cap to `data/journal_grounding_shadow.jsonl`. Fail-open: any error is
swallowed, one debug log line, the caller's rollup is never affected.
"""
from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path

from core import shadow_log as _sl

logger = logging.getLogger("nascence.journal_grounding_shadow")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "journal_grounding_shadow.jsonl"   # tests must temp-path this; never truncate the live file

_LABEL = {"did": "my week", "saw": "the world's week"}


def _week_bounds(wid: str) -> tuple[float, float]:
    """'YYYY-Wnn' -> (start_ts, end_ts) for that ISO week. Mirrors journal_rollup.last_completed_week's
    own to_ts convention (local midnight via time.mktime) so the source window matches EXACTLY what the
    rollup itself queried — grading against a shifted window would be a false miscalibration, not a
    real finding."""
    import time as _t
    from datetime import datetime, timedelta
    year, wk = wid.split("-W")
    start_d = date.fromisocalendar(int(year), int(wk), 1)     # Monday of that ISO week
    end_d = start_d + timedelta(days=7)
    to_ts = lambda d: _t.mktime(datetime(d.year, d.month, d.day).timetuple())
    return to_ts(start_d), to_ts(end_d)


def _fetch_cap(wid: str, stream: str) -> tuple[str | None, str | None]:
    """(fragment_id, entry_text) of the week-cap journal_rollup.py just stored for this stream/week, or
    (None, None) if not found (fail-open — the rollup's own store may have failed non-fatally)."""
    label = _LABEL[stream]
    prefix = f"[{label} — {wid}] "
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            row = conn.execute(
                "SELECT fragment_id, content FROM memory_fragments "
                "WHERE origin='journal_week' AND content LIKE ? ORDER BY timestamp DESC LIMIT 1",
                (prefix + "%",)).fetchone()
        if row is None:
            return None, None
        return row["fragment_id"], (row["content"] or "")[len(prefix):]
    except Exception as exc:
        logger.debug("[journal-grounding-shadow] fetch_cap failed (non-fatal): %s", exc)
        return None, None


async def grade_week(wid: str, stream: str) -> dict | None:
    """Grade one just-rolled week-cap against its own linked sources. Returns the logged row, or None
    if there was nothing to grade (cap not found / Emissary unavailable) — always fail-open."""
    try:
        from core import journal_rollup as _jw
        from core import left_lane
        from core import memory_levels as _ml

        fid, entry = _fetch_cap(wid, stream)
        if not entry:
            return None
        start_ts, end_ts = _week_bounds(wid)
        did, saw = _jw._week_sources(start_ts, end_ts)          # SAME query the rollup itself used
        sources = did if stream == "did" else saw
        full_sources = [text for _fid2, _ts, text in sources]
        if not full_sources:
            return None
        judge_sources = [s[:800] for s in full_sources]

        grade = await left_lane.grade_gist_faithfulness(entry, judge_sources)
        faithful = grade.get("faithful") if isinstance(grade, dict) else None
        feedback = str((grade or {}).get("feedback", ""))[:200] if grade else None
        invented = (grade or {}).get("invented", []) if isinstance(grade, dict) else []
        claims = _ml.verify_invention_claims(invented, full_sources) if invented else []
        genuine = [t for t, v in claims if v == "GENUINE"]
        false_flags = [t for t, v in claims if v in ("IN_SOURCE", "CROSS_LINK")]
        sfid = _ml.source_fidelity(entry, full_sources)

        # P-0070: also judge exactly the subset the author was shown (journal_rollup._select_shown), so the
        # grade matches the author's task. Additive: the full-set fields above are unchanged.
        shown_fields: dict = {}
        try:
            shown = [t for _f, _t, t in _jw._select_shown(sources)]
            if shown and len(shown) < len(full_sources):
                sg = await left_lane.grade_gist_faithfulness(entry, [s[:800] for s in shown])
                s_inv = (sg or {}).get("invented", []) if isinstance(sg, dict) else []
                s_claims = _ml.verify_invention_claims(s_inv, shown) if s_inv else []
                shown_fields = {
                    "n_shown": len(shown),
                    "shown_faithful": sg.get("faithful") if isinstance(sg, dict) else None,
                    "shown_source_fidelity": _ml.source_fidelity(entry, shown),
                    "shown_invented_genuine": [t for t, v in s_claims if v == "GENUINE"],
                }
            else:
                shown_fields = {"n_shown": len(shown)}
        except Exception as exc:
            logger.debug("[journal-grounding-shadow] shown-subset grade failed (non-fatal): %s", exc)

        row = {
            **shown_fields,
            "ts": round(time.time(), 1), "wid": wid, "stream": stream, "fragment_id": fid,
            "n_sources": len(full_sources),
            "faithful": faithful, "source_fidelity": sfid, "feedback": feedback,
            "invented_raw": invented, "invented_genuine": genuine, "invented_false_flags": false_flags,
            "judge_available": grade is not None,
        }
        _sl.append(_LOG, row)
        logger.info("[journal-grounding-shadow] graded %s/%s: faithful=%s source_fidelity=%s "
                    "genuine_inventions=%d", wid, stream, faithful, sfid, len(genuine))
        return row
    except Exception as exc:
        logger.debug("[journal-grounding-shadow] grade_week failed (non-fatal): %s", exc)
        return None


async def observe_rolled(rolled: list[str]) -> None:
    """SHADOW hook — call right after `journal_rollup.week_rollup()` with the streams it just rolled.
    Grades each newly-written cap against its own sources and logs the verdict. Applies NOTHING to the
    rollup's stored fragment, file, or links. Fail-open in full: never raises into the caller."""
    if not rolled:
        return
    try:
        from core import journal_rollup as _jw
        wid, _s, _e = _jw.last_completed_week()
        for stream in rolled:
            await grade_week(wid, stream)
    except Exception as exc:
        logger.debug("[journal-grounding-shadow] observe_rolled failed (non-fatal): %s", exc)


def status() -> dict:
    """For the pulse: how often has soft grounding actually diverged from what the hard grader would
    have flagged? The comparison D-0006 is waiting on."""
    try:
        rows = _sl.read_rows(_LOG)
        if not rows:
            return {"graded": 0}
        graded = [r for r in rows if r.get("judge_available")]
        faithfuls = [r["faithful"] for r in graded if isinstance(r.get("faithful"), (int, float))]
        genuine_total = sum(len(r.get("invented_genuine") or []) for r in rows)
        low_faithful = [r for r in graded if isinstance(r.get("faithful"), (int, float)) and r["faithful"] < 0.6]
        return {
            "graded": len(rows), "judge_available_n": len(graded),
            "mean_faithful": round(sum(faithfuls) / len(faithfuls), 3) if faithfuls else None,
            "genuine_inventions_total": genuine_total,
            "low_faithful_caps": [(r["wid"], r["stream"], r["faithful"]) for r in low_faithful],
        }
    except Exception:
        return {"graded": 0}

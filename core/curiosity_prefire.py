"""
Nascence -- the Curiosity PRE-FIRE CHECK, SHADOW (J-3219, D-0608, founder 2026-11-02; row P-0011, F-3504).

What it is: after the Curiosity node has produced its candidate questions and BEFORE Orchestrator.
_on_dissonance_ignition fires one as Du's autonomous cycle, a different-family model
(core/judge_panel.py score_curiosity_candidates: falcon3:7b, TII -- not the generating model's family, not
granite) scores each candidate on two things: answerable from the material the node was offered, and not a
metaphor mash-up (a relation-presupposing verb with no support in the material). This module logs what that
check WOULD have picked beside what actually fired.

What it is NOT: a gate. The firing choice is UNCHANGED -- nothing here returns a value to the caller, nothing
here is read by any prompt, and there is no LIVE switch to flip (D-0608: shadow until the founder has read the
log). It is fire-and-forget on a background asyncio task, so the aiohttp judge calls never sit between the
node's output and the firing (and never on the event loop's critical path); fail-open and quiet; single-flight
(if the previous check is still running when the next ignition comes, this one is dropped, counted, not queued).

THE READER (write-only is the #1 failure): status() below and scripts/curiosity_prefire_report.py read
data/curiosity_prefire_shadow.jsonl and evaluate D-0608's own defeater (same pick as the live choice in over
85 percent of runs, or near-constant scores = the check carries no information). Job J-3219's follow-up (a
gated needs_input job) is the named human read after a week of paired picks.

Shadow rows: data/curiosity_prefire_shadow.jsonl -- one per ignition that reached the check. Observe-only:
no field is read by Du's cognition.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.curiosity_prefire")

_ROOT = Path(__file__).resolve().parent.parent
_SHADOW = _ROOT / "data" / "curiosity_prefire_shadow.jsonl"

CURIOSITY_PREFIRE_SHADOW = True      # kill switch for the SHADOW check only; there is no live/gate mode (D-0608)
DEFEATER_SAME_PICK = 0.85            # D-0608 defeater: same pick as live in MORE than this share of runs -> do not gate
DEFEATER_MIN_ROWS = 40               # fewer paired rows than this is not enough to read the defeater

_tasks: set = set()                  # strong refs so a fire-and-forget task is not garbage-collected mid-flight
_inflight = False                    # single-flight guard
_dropped = 0                         # ignitions skipped because the previous check was still running

_ENTITY_RE = re.compile(r"^\s*Entity:[^\n]*\n+", re.I)
_TAIL_RE = re.compile(r"\n*\s*Generate questions and research directions[^\n]*\s*$", re.I)


def material_from_prompt(user_prompt: str) -> str:
    """The material the node was offered = its user prompt minus the Entity line and the closing instruction
    (recent themes, the study block, the unresolved-thread menu). One code path for the live hook and for the
    positive-control set, so the control sees exactly what the live check sees."""
    s = str(user_prompt or "")
    s = _ENTITY_RE.sub("", s, count=1)
    s = _TAIL_RE.sub("", s)
    return s.strip()


def pick(scores: list) -> "tuple[int | None, bool]":
    """(index the check would have picked, unique_top). Highest score wins; a TIE goes to the lowest index, i.e.
    to the live choice's own position -- so agreement is, if anything, flattered, which is why unique_top is
    reported too (True only when exactly one candidate holds the top score). (None, False) when nothing scored."""
    scored = [(r.get("score"), r.get("i")) for r in (scores or []) if isinstance(r.get("score"), int)]
    if not scored:
        return None, False
    top = max(s for s, _ in scored)
    tops = sorted(i for s, i in scored if s == top)
    return tops[0], len(tops) == 1


def _write_row(row: dict, path: Path | None = None) -> None:
    p = profile.guard_path(path or _SHADOW)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


async def _run(candidates: list, fired: str, material: str, ask=None, path: Path | None = None,
               score_fn=None) -> dict | None:
    """Score, pick, log one paired row. Returns the row (tests read it); never raises."""
    global _inflight
    try:
        t0 = time.monotonic()
        if score_fn is None:
            from core import judge_panel as _jp
            score_fn = _jp.score_curiosity_candidates
        res = await score_fn(candidates, material, ask=ask) if ask is not None else await score_fn(candidates, material)
        scores = res.get("scores") or []
        pick_i, unique = pick(scores)
        fired_i = candidates.index(fired) if fired in candidates else -1
        row = {
            "ts": round(time.time(), 1), "live": False, "judge": res.get("url"),
            "n_candidates": len(candidates), "n_scored": sum(1 for r in scores if r.get("score") is not None),
            "material_chars": len(material or ""),
            "candidates": [{"i": r.get("i"), "q": (r.get("q") or "")[:200], "answerable": r.get("answerable"),
                            "unsupported_link": r.get("unsupported_link"), "support_ok": r.get("support_ok"),
                            "score": r.get("score"),
                            "why": r.get("why"), "err": r.get("err"), "s": r.get("s")} for r in scores],
            "fired_i": fired_i, "fired_q": (fired or "")[:200],
            "would_pick_i": pick_i,
            "would_pick_q": (candidates[pick_i] if pick_i is not None and pick_i < len(candidates) else "")[:200],
            "agree": (pick_i == fired_i) if pick_i is not None else None,
            "unique_top": unique,
            "elapsed_s": round(time.monotonic() - t0, 1),
        }
        try:
            _write_row(row, path)
        except profile.NonLiveWriteError as exc:
            logger.debug("[curiosity_prefire] shadow write refused (non-fatal): %s", exc)
        return row
    except Exception as exc:
        logger.debug("[curiosity_prefire] check failed (non-fatal, quiet): %s", exc)
        return None
    finally:
        _inflight = False


def shadow_spawn(candidates, fired: str, user_prompt: str = "") -> bool:
    """Called by the orchestrator once the firing choice is made, just before run_cycle. Schedules the check as
    a background task and returns at once (True if scheduled). Never raises, never awaits, never changes anything
    the caller does next. Dropped (False) when disabled, when there is no running loop, when fewer than two
    candidates exist (nothing to choose between), or when the previous check is still in flight."""
    global _inflight, _dropped
    try:
        if not CURIOSITY_PREFIRE_SHADOW:
            return False
        cands = [str(c).strip() for c in (candidates or []) if str(c).strip()]
        if len(cands) < 2:
            return False
        if _inflight:
            _dropped += 1
            return False
        loop = asyncio.get_running_loop()
        _inflight = True
        task = loop.create_task(_run(cands, str(fired or "").strip(), material_from_prompt(user_prompt)))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
        return True
    except Exception as exc:
        _inflight = False
        logger.debug("[curiosity_prefire] spawn skipped (non-fatal): %s", exc)
        return False


def status(path: Path | None = None, limit: int = 2000) -> dict:
    """THE READER: summarise the paired picks and evaluate D-0608's defeater. Read-only, fail-open to {"rows": 0}.
    keys: rows, scored_rows, agree_rate (of scored rows), unique_top_rate, agree_when_unique, score_hist (every
    candidate score 0/1/2), flat_rows (rows where every candidate scored the same: the check chose nothing),
    err_rate, defeater: "same_pick" | "near_constant" | "insufficient_rows" | "clear"."""
    try:
        p = path or _SHADOW
        if not p.exists():
            return {"rows": 0}
        rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()][-limit:]
        if not rows:
            return {"rows": 0}
        scored = [r for r in rows if r.get("would_pick_i") is not None]
        agree = [r for r in scored if r.get("agree")]
        uniq = [r for r in scored if r.get("unique_top")]
        hist = {0: 0, 1: 0, 2: 0}
        flat = 0
        n_cand_scored = 0
        for r in scored:
            sc = [c.get("score") for c in (r.get("candidates") or []) if isinstance(c.get("score"), int)]
            for s in sc:
                hist[s] = hist.get(s, 0) + 1
                n_cand_scored += 1
            if len(sc) > 1 and len(set(sc)) == 1:
                flat += 1
        n_cands = sum(len(r.get("candidates") or []) for r in rows)
        n_err = sum(1 for r in rows for c in (r.get("candidates") or []) if c.get("err"))
        out = {
            "rows": len(rows), "scored_rows": len(scored),
            "agree_rate": round(len(agree) / len(scored), 3) if scored else None,
            "unique_top_rate": round(len(uniq) / len(scored), 3) if scored else None,
            "agree_when_unique": round(sum(1 for r in uniq if r.get("agree")) / len(uniq), 3) if uniq else None,
            "score_hist": hist,
            "flat_rows": flat, "flat_rate": round(flat / len(scored), 3) if scored else None,
            "err_rate": round(n_err / n_cands, 3) if n_cands else None,
            "first_ts": rows[0].get("ts"), "last_ts": rows[-1].get("ts"),
        }
        if len(scored) < DEFEATER_MIN_ROWS:
            out["defeater"] = "insufficient_rows"
        elif out["agree_rate"] is not None and out["agree_rate"] > DEFEATER_SAME_PICK:
            out["defeater"] = "same_pick"
        elif (out["flat_rate"] is not None and out["flat_rate"] > 0.85) or \
                (n_cand_scored and max(hist.values()) / n_cand_scored > 0.9):
            out["defeater"] = "near_constant"     # D-0608: its scores carry no information
        else:
            out["defeater"] = "clear"
        return out
    except Exception:
        return {"rows": 0}

"""
Pursuit judge-set close -- SHADOW ONLY (J-2171, D-0426 option A, plan docs/plans/pursuits.md).  RESTART-GATED.

Pursuits had no way to CLOSE: saturation (40 advances) merely retires them (70 retired, 0 resolved). D-0426 (travis
2026-10-16) ruled option A: at saturation (advances >= SATURATE_ADVANCES) and again every +20 advances, ask the
EXISTING judge panel (core/judge_panel.py, two families) ONCE whether the pursuit's standing answers its driving
question.  A yes would mark status=resolved with a closing note.  This module only LOGS that would-be close to
data/logs/pursuit_close_shadow.jsonl -- it never edits the pursuit record, never sets status, never authors work, and
nothing Du sees changes.  Mirrors the dream-close judge gap (F-2474).

D-0423 (the closure law, core/closure.py) may SUPERSEDE a per-subsystem close: closure.py's pursuit arm is a stub gated
on J-2117 ("whatever close trigger"); if this judge fires it is the natural source for that arm's seed/judge, and if the
law is adopted wholesale this module is replaced by it.  The two are not wired together here (additive only).

D-0626 (founder 2026-11-02, J-3237): the panel is asked ONLY about a pursuit it can say yes to -- one with an extracted
`open` question, a born question (question_kind question / done_when, D-0554) or a done_when in the side store.  A pursuit
with none of those (F-3823/F-3824: 82 of 82 asked, the "driving question" was a scene statement, 0 yes) is NOT asked: it is
simply not closable and fades through closure.py's faded arm exactly as before.  Every shadow row carries `askable`; a
pursuit that reached the ask point with nothing to answer gets ONE `close_skip` row (askable false, no LLM call) so the
7-day read (J-2184, fire_rate()) counts only askable pursuits and can still say how many were skipped.
Rows written before this change carry no `askable` flag: they are left out of the rate and do not use up a pursuit's ask
slot, so a saturated pursuit with a real `open` is asked once, properly, on the first sweep after the restart.

J-3104 (P-0101, F-3823..F-3825): the prompt shape is now explicit.  When the driving question is an EXTRACTED question
(born question or `open`), the birth thought moves to a "WHAT IT STARTED FROM" line (prompt_v "v2"); a done_when-only
pursuit keeps the old shape (prompt_v "v1", prompt text unchanged) so before/after stays comparable WITHOUT a second LLM
call per pursuit.  Every ask row now stores the judge's whole input (driving_q, standing, open, started_from, done_when)
and replay(row) rebuilds the exact prompt; fire_rate() splits the rate by prompt_v and basis.  The no-question case is
D-0626's one `close_skip` row (kept; the briefing's 'no_question').  closure.py, CLOSURE_ARMS, status: untouched.

Defeater (D-0426, restated by D-0626 after 30 asked pursuits under the new rule): the shadow fire rate over 7 days must sit in 5-50 percent of saturated pursuits asked;
see fire_rate().  Fail-open: every public function swallows exceptions; a judge outage logs 'unavailable' and
the pursuit is re-asked at the next sweep (an unavailable ask does not consume the +20 slot).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.pursuit_close_shadow")

SHADOW_LOG = Path(__file__).parent.parent / "data" / "logs" / "pursuit_close_shadow.jsonl"  # test can temp-path
CLOSE_FIRST = 40          # == pursuits.SATURATE_ADVANCES
CLOSE_EVERY = 20          # re-ask after this many further advances
SHADOW_ENABLED = True     # False = a complete no-op
V3_PROMPT = True          # ON 2026-11-16 (D-0786 ruled travis; shadow only, next restart). J-4012 (D-0743, F-4697): True = prompt_v "v3" (trajectory + 3-way verdict). Founder flips it; default OFF
TRAJECTORY_N = 6          # v3: how many of the pursuit's kept thoughts (p["thoughts"], oldest first) the judge sees


def _read() -> list[dict]:
    rows = []
    try:
        for line in Path(SHADOW_LOG).read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return rows


def _append(row: dict) -> None:
    Path(SHADOW_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(SHADOW_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _done_when_text(p: dict) -> str:
    """The closing condition written at birth (J-2160, side store, judge-only), else ''. Never raises."""
    try:
        from core import done_when as _dw
        return ((_dw.get("pursuit", str(p.get("id") or "")) or {}).get("done_when") or "").strip()
    except Exception:
        return ""


def askable(p: dict) -> "tuple[bool, str, str]":
    """D-0626: (askable, basis, question) -- can a yes be possible for this pursuit?  basis is the first of
    'question' / 'done_when' (born under D-0554: question_text), 'open' (the extracted open question, D-0032),
    'done_when' (side-store line), else 'none' (not asked, fades).  `question` is what the judge is shown as the
    driving question: the extracted text, never the scene-statement birth thought when a real question exists.
    The same `open` / `question_kind` fields core/pursuits.py reads; this function only reads them.  Never raises."""
    try:
        kind = p.get("question_kind")
        qt = (p.get("question_text") or "").strip()
        if kind in ("question", "done_when") and qt:
            return True, kind, qt
        op = (p.get("open") or "").strip()
        if op:                                   # a real '?' sentence a judged advance raised (also on a later-grown observation)
            return True, "open", op
        if _done_when_text(p):                   # legacy / observation-born pursuit that still wrote a done_when at open
            return True, "done_when", p.get("question", "")
        return False, "none", ""
    except Exception:
        return False, "none", ""


def due(p: dict, rows: "list[dict] | None" = None) -> bool:
    """True when this pursuit has reached an ask point and has not been asked at (or since) it.
    Asks at advances >= 40, then again once advances >= last_asked + 20.  Only rows with a real verdict
    (asked=True, askable=True) count as asked.  D-0626: a pursuit with nothing the judge could say yes to is never due."""
    try:
        if not askable(p)[0]:                     # D-0626 (supersedes the D-0554 observation-only test): open or done_when or nothing
            return False
        adv = int(p.get("advances", 0))
        if adv < CLOSE_FIRST:
            return False
        rows = _read() if rows is None else rows
        # D-0626: only an ask made under the new rule (askable flag) consumes the slot; the 83 asks of 2026-10-16..11-01
        # showed the judge a scene statement as the question, so a pursuit with a real `open` is asked once more, properly.
        last = [r.get("advances", 0) for r in rows if r.get("id") == p.get("id") and r.get("asked")
                and r.get("askable") is True]
        return (not last) or adv >= max(last) + CLOSE_EVERY
    except Exception:
        return False


_SYS = ("You are a strict judge of whether an inquiry has been answered. Given a pursuit's driving question and "
        "its current standing position, decide whether the standing position actually ANSWERS the driving "
        "question: it resolves what was asked, not merely discusses it, circles it, or raises further questions. "
        "When uncertain, answer false. Output ONLY JSON: "
        '{"resolved": true|false, "why": "<one short clause>"}')


_SYS3_BASE = ("You are a strict judge of whether an inquiry has been answered. You are given a pursuit's driving question, "
              "the TRAJECTORY of its last few thoughts (oldest first) and its latest standing position. ")
_SYS3_ASK = {
    "answered": ("Decide whether the trajectory TOGETHER resolves what was asked: it answers the question, not merely "
                 "discusses it, circles it, or raises further questions. When uncertain, answer false. Output ONLY JSON: "
                 '{"answered": true|false, "why": "<one short clause>"}'),
    "partly": ("Decide whether the trajectory gives a REAL PARTIAL answer to what was asked: a concrete part of the "
               "question is settled, even though the whole is not. Mere discussion or a restated question is not a partial "
               'answer. Output ONLY JSON: {"partly": true|false, "why": "<one short clause>"}'),
    "settled": ("Decide whether the LAST THREE thoughts of the trajectory hold the same position (they repeat or "
                "restate one view rather than moving). Output ONLY JSON: "
                '{"settled": true|false, "why": "<one short clause>"}'),
}


def _sys3(key: str) -> str:
    """J-4012: the v3 system prompt for one binary ask (judge_panel.rule_detail is one boolean key per call, so the
    3-way verdict {answered | partly | not_yet} + settled is three binary asks: answered; partly only if not answered; settled)."""
    return _SYS3_BASE + _SYS3_ASK[key]


def build_prompt(p: dict) -> "tuple[str, str, dict] | None":
    """J-3104 (P-0101): the exact (system, user) the judge is shown for this pursuit, plus the replay fields stored in the
    shadow row; None when the pursuit is not askable.  ask() and replay() build the user text the same way, so a logged
    row can be re-run.  Prompt shape 'v2' = the driving-question slot holds an EXTRACTED question (born question / open)
    and the birth thought moves to a 'WHAT IT STARTED FROM' line; shape 'v1' = the old one (birth thought in the
    driving-question slot), which only a done_when-only pursuit with no extracted question text still gets.  Never raises."""
    try:
        ok, basis, dq = askable(p)
        if not ok:
            return None
        birth = (p.get("question") or "").strip()
        if V3_PROMPT:                           # J-4012 (D-0743): trajectory shape; the v1/v2 branches below are untouched
            dq = dq or birth
            dw = _done_when_text(p)
            op = (p.get("open") or "").strip()
            traj = [str(t).strip()[:200] for t in (p.get("thoughts") or []) if str(t).strip()][-TRAJECTORY_N:]
            fields = {"prompt_v": "v3", "driving_q": dq[:240], "standing": (p.get("standing", "") or "")[:320],
                      "open": op[:160], "started_from": "", "done_when": dw[:200], "trajectory": traj,
                      "driving_is_question": dq.rstrip(" \t\"')”’").endswith("?"),
                      "done_when_seen": bool(dw), "basis": basis}
            return _sys3("answered"), _user_text(fields), fields
        v = "v2" if (dq and basis in ("question", "open") and dq != birth) else "v1"
        dq = dq or birth                       # basis done_when with no extracted question: the birth thought, as before
        dw = _done_when_text(p)                # J-2160: the closing condition written at birth (judge-only, never shown to Du)
        op = (p.get("open") or "").strip()
        standing = p.get("standing", "") or ""
        started = birth if (v == "v2" and birth) else ""
        fields = {"prompt_v": v, "driving_q": dq[:240], "standing": standing[:320], "open": op[:160],
                  "started_from": started[:200], "done_when": dw[:200],
                  "driving_is_question": dq.rstrip(" \t\"')”’").endswith("?"),
                  "done_when_seen": bool(dw), "basis": basis}
        return _SYS, _user_text(fields), fields
    except Exception:
        return None


def _user_text(f: dict) -> str:
    """The judge's user message from stored fields (the single place the prompt text is written)."""
    dw = f.get("done_when") or ""
    op = f.get("open") or ""
    traj = ""
    if f.get("prompt_v") == "v3" and f.get("trajectory"):     # J-4012: last thoughts, oldest first, before the latest standing
        traj = ("TRAJECTORY (oldest first):\n"
                + "\n".join(f"{i}. {t[:200]}" for i, t in enumerate(f["trajectory"], 1)) + "\n\n")
    return (f"PURSUIT (driving question): {f['driving_q'][:240]}\n\n"
            + traj +
            f"ITS STANDING POSITION: {f.get('standing', '')[:320]}\n\n"
            + (f"WHAT IT STARTED FROM: {f['started_from'][:200]}\n\n" if f.get("started_from") else "")
            + (f"STILL-OPEN QUESTION IT RAISED: {op[:160]}\n\n" if op and op != f["driving_q"] else "")
            + (f"WHAT IT SAID, WHEN IT OPENED, WOULD SETTLE IT: {dw[:200]}\n\n" if dw else "")
            + ("Does the standing position answer the driving question" + (", by that condition?" if dw else "?")))


def replay(row: dict) -> "tuple[str, str] | None":
    """J-3104: rebuild the (system, user) the judge saw for a shadow row written since this change (it stores its
    inputs), so a reader can re-run it on another model.  None for older rows.  Never raises."""
    try:
        if not row.get("driving_q") or "standing" not in row:
            return None
        if row.get("prompt_v") == "v3":
            return _sys3("answered"), _user_text(row)
        return _SYS, _user_text(row)
    except Exception:
        return None


async def _panel(system: str, usr: str, key: str, context: str) -> dict:
    """The one judge-panel call site of this module (J-4012: v1/v2 and the three v3 binary asks all go through it)."""
    from core import judge_panel as _jp
    return await _jp.rule_detail(system, usr, key, context=context)


async def ask(p: dict) -> "dict | None":
    """Ask the judge panel once; append one shadow row; return the row (None if disabled / nothing to log).
    Never raises, never mutates `p`."""
    if not SHADOW_ENABLED:
        return None
    built = build_prompt(p)
    if built is None:                         # D-0626: nothing to answer -> not asked, fades through closure.py as today
        return None
    try:
        system, usr, fl = built
        dw = fl["done_when"] or None
        extra: dict = {}
        if fl["prompt_v"] == "v3":
            # J-4012: 3-way verdict from binary panel asks.  answered?; partly? only if not answered; settled? always.
            ctx = f"pursuit_close:{p.get('id')}"
            d = await _panel(_sys3("answered"), usr, "answered", ctx)
            verdict = d.get("verdict")
            partly = None
            if verdict is False:
                dp = await _panel(_sys3("partly"), usr, "partly", ctx + ":partly")
                partly = dp.get("verdict")
            elif verdict:
                partly = False
            ds = await _panel(_sys3("settled"), usr, "settled", ctx + ":settled")
            v3v = (None if verdict is None else "answered" if verdict else "partly" if partly else "not_yet")
            extra = {"verdict3": v3v, "settled": ds.get("verdict"), "partly": (v3v == "partly") if v3v else None,
                     "trajectory": fl["trajectory"]}
        else:
            d = await _panel(system, usr, "resolved", f"pursuit_close:{p.get('id')}")
            verdict = d.get("verdict")
        row = {"ts": round(time.time(), 1), "kind": "close_ask", "id": p.get("id"),
               "question": p.get("question", "")[:120], "advances": p.get("advances", 0),
               "status": p.get("status"), "asked": verdict is not None, "how": d.get("how"),
               "would_resolve": bool(verdict) if verdict is not None else None,
               "why": (d.get("why") or "")[:200],
               "would_note": ((p.get("standing") or "")[:300] if verdict else None),
               "done_when_seen": fl["done_when_seen"], "question_kind": p.get("question_kind", "legacy"),
               "askable": True, "basis": fl["basis"],      # D-0626: fire_rate() reads only askable rows
               # J-3104: the judge's whole input, so a later reader can replay the row (replay()) on another model
               "prompt_v": fl["prompt_v"], "driving_q": fl["driving_q"], "driving_is_question": fl["driving_is_question"],
               "standing": fl["standing"], "open": fl["open"], "started_from": fl["started_from"],
               "done_when": fl["done_when"]}
        row.update(extra)
        _append(row)
        if dw and verdict is not None:       # J-2160: closure.py pursuit arm (shadow unless in CLOSURE_ARMS)
            try:
                from core import closure as _cl
                if verdict:
                    _cl.run_in_thread(_cl.record_pursuit_met, dict(p), dict(row))
                elif p.get("status") == "saturated":
                    _cl.run_in_thread(_cl.record_pursuit_faded, dict(p), dict(row))
            except Exception as exc:
                logger.debug("[pursuit_close_shadow] closure hand-off failed (non-fatal): %s", exc)
        return row
    except Exception as exc:
        logger.debug("[pursuit_close_shadow] ask failed (non-fatal): %s", exc)
        return None


async def sweep(items: list[dict]) -> int:
    """Ask every due pursuit once.  Called after the pursuits judge sweep has saved; fail-open.  Returns asks made.
    D-0626: a pursuit that reached the ask point with nothing the judge could answer is not asked; it gets one
    `close_skip` row (askable false, no LLM call) so the shadow read can count it, then fades as before."""
    n = 0
    try:
        if not SHADOW_ENABLED:
            return 0
        rows = _read()
        skipped = {r.get("id") for r in rows if r.get("kind") == "close_skip"}
        for p in items:
            if p.get("status") in ("active", "saturated"):
                if due(p, rows):
                    r = await ask(p)
                    if r:
                        n += 1
                        rows.append(r)
                elif (int(p.get("advances", 0) or 0) >= CLOSE_FIRST and p.get("id") not in skipped
                      and not askable(p)[0]):
                    _append({"ts": round(time.time(), 1), "kind": "close_skip", "id": p.get("id"),
                             "question": p.get("question", "")[:120], "advances": p.get("advances", 0),
                             "status": p.get("status"), "asked": False, "askable": False, "basis": "none",
                             "question_kind": p.get("question_kind", "legacy")})
                    skipped.add(p.get("id"))
    except Exception as exc:
        logger.debug("[pursuit_close_shadow] sweep failed (non-fatal): %s", exc)
    return n


ENOUGH_ASKED = 30     # D-0626 defeater: judge the fire rate only after this many askable pursuits were asked


def fire_rate(since_ts: "float | None" = None, include_unflagged: bool = False) -> dict:
    """D-0426 defeater read (restated by D-0626): of the ASKABLE pursuits with a real verdict in the window, the share
    the judge would resolve.  verdict: ok if 5-50 percent, too_lenient if >50, meaningless if <5, no_data if nothing
    asked.  Rows without the `askable` flag (written before D-0626, when the judge was shown scene statements and
    answered false 82 of 82) are left out unless include_unflagged.  `skipped_not_askable` = pursuits that reached the
    ask point with nothing to answer; `enough` = at least ENOUGH_ASKED asked (D-0626: revisit after 30)."""
    allrows = [r for r in _read() if since_ts is None or r.get("ts", 0) >= since_ts]
    rows = [r for r in allrows if r.get("asked") and (r.get("askable") is True
                                                    or (include_unflagged and "askable" not in r))]
    ids = {r["id"] for r in rows}
    fired = {r["id"] for r in rows if r.get("would_resolve")}
    rate = (len(fired) / len(ids)) if ids else None
    verdict = ("no_data" if rate is None else "too_lenient" if rate > 0.50
               else "meaningless" if rate < 0.05 else "ok")
    skipped = {r["id"] for r in allrows if r.get("kind") == "close_skip" and r.get("askable") is False}

    def _split(field: str, default: str) -> dict:          # J-3104: reader for the new fields (rate per prompt shape / basis)
        out: dict = {}
        for r in rows:
            k = str(r.get(field) or default)
            g = out.setdefault(k, {"asked": set(), "fired": set()})
            g["asked"].add(r["id"])
            if r.get("would_resolve"):
                g["fired"].add(r["id"])
        return {k: {"asked": len(g["asked"]), "would_resolve": len(g["fired"])} for k, g in out.items()}
    v3rows = [r for r in rows if r.get("prompt_v") == "v3"]
    v3ids = {r["id"] for r in v3rows}
    partly_ids = {r["id"] for r in v3rows if r.get("verdict3") == "partly"}
    v3 = {"asked": len(v3ids), "answered": len({r["id"] for r in v3rows if r.get("would_resolve")}),
          "partly": len(partly_ids), "partly_rate": (len(partly_ids) / len(v3ids)) if v3ids else None,
          "settled": len({r["id"] for r in v3rows if r.get("settled")})}
    return {"pursuits_asked": len(ids), "would_resolve": len(fired), "rate": rate, "verdict": verdict, "v3": v3,
            "skipped_not_askable": len(skipped), "enough": len(ids) >= ENOUGH_ASKED,
            "by_prompt_v": _split("prompt_v", "v1"), "by_basis": _split("basis", "unknown")}

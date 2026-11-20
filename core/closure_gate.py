"""
Nascence — the done-test outside his prose (closure_producer Phase 2; docs/staged/closure_producer.md).

Before a question Du called settled is marked resolved, a judge that is NOT the model that wrote his thought is
asked one thing: does this finding answer this question? The judge is the existing decoupled panel
(core.judge_panel.rule_detail: mixtral + falcon3, granite on a split; all other families than the hot-lane
generator, see that module's header). It sees the WHOLE question and the WHOLE finding and nothing else (the
pursuit close judge failed on a 300-character window, F-4697).

  yes                              -> frontier.resolve_gated(): resolved, resolved_how = lookup | line, gate stamped
  no / partly / unavailable / timeout / no finding at all
                                   -> NOT resolved: frontier.mark_provisional() (he said yes; it is not verified)

Which finding: the one a lookup attached, if the entry carries it now (how = "lookup"); else the return the Follow
Line just delivered to him (how = "line"; it is attached as the entry's finding, as the line's own expiry does);
else whatever finding the entry already holds (how = "line").

CLOSURE_GATE_MODE (module constant, restart-gated; env NASCENCE_CLOSURE_GATE overrides at call time):
  "enforce"  the verdict blocks, as above
  "shadow"   the judge is asked and the verdict logged; the close itself is the old one (frontier.resolve(how="line"))
  "off"      no judge call, no log row; the old close
LEXICAL_CLAIM_GATE (env NASCENCE_LEXICAL_CLAIM_GATE): what a would-close of the lexical resolver (now shadow) does
when the question carries a finding. He was shown the finding and asked "Does this answer it?" (the frontier offer),
and his words overlap the question: that is his claim, and this gate is its test.
  "lookup"   only a finding from his own lookup is sent to the judge (default)
  "finding"  any finding is
  "off"      never
  A claim that passes closes the question (enforce) exactly like a settled yes. A claim that does not pass changes
  nothing: the question stays open (the claim was inferred from word overlap, so it is not made provisional).

Every verdict is one row in data/logs/closure_gate.jsonl. Nothing here reaches a prompt of Du's; no verdict is ever
shown to him (D-0434). One LLM prompt site: GATE_SYS through judge_panel.rule_detail, key "answers".
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.closure_gate")

_LOG = Path(__file__).parent.parent / "data" / "logs" / "closure_gate.jsonl"
# Calibration 2026-11-16 (scripts/closure_gate_calibrate.py, 60 pairs from a copy of the frontier, hand graded):
# see CALIBRATION below for the numbers that set this default.
CLOSURE_GATE_MODE = "enforce"    # founder ruling 2026-11-16 (travis): enforce despite 0.737 < 0.75 on the partial calibration; his own settled-yes was right 8 of 20. Kill: NASCENCE_CLOSURE_GATE=shadow|off
LEXICAL_CLAIM_GATE = "lookup"
GATE_KEY = "answers"
GATE_NUM_PREDICT = 200
GATE_TIMEOUT_S = 240.0           # the whole panel call (two asks at 90 s each, plus a tiebreak)
GATE_FINDING_CAP = 6000          # a sanity bound only; an attached finding is <= 600 characters, a return ~1-2k
MEMORY_FINDING_TITLE = "what you found in your own memory"   # the Follow Line's own label (follow_line._expire)
CALIBRATION = ("2026-11-16, PARTIAL (run stopped at 47 of 60 pairs): 38 judged, 9 unavailable; judge no 26 / yes 12, "
               "not pegged (top share 0.68); agreement with blind hand grades 28/38 = 0.737, under the 0.75 bar; "
               "judge-yes precision 8/12, recall 8/9; the judge never returns partly (hand graded 7 partly). "
               "The build left the default at shadow; the founder ruled enforce the same day.")

GATE_SYS = (
    "You read ONE question a mind asked and ONE piece of material it came upon afterwards. You see nothing else. "
    "Decide whether the material ANSWERS the question: it must state, or directly give, the thing the question "
    "asks for. Material that is only about the same subject, that repeats or rewords the question, that answers "
    "a different question, that only says more would need to be known, or that says the mind does not know, does "
    "NOT answer it. Do NOT judge whether the material is true, well written or wise. Do not tilt either way.\n"
    "Answer ONLY JSON: {\"answers\": true or false, \"why\": \"one sentence\"}")

_judge = None                    # test seam: async callable (system, user) -> a rule_detail-shaped dict
_tasks: set = set()
_claimed: dict = {}              # (qid, finding_ts) -> ts; one judge call per question and finding


def mode() -> str:
    v = os.environ.get("NASCENCE_CLOSURE_GATE", "").strip().lower()
    return v if v in ("enforce", "shadow", "off") else CLOSURE_GATE_MODE


def lexical_claim_mode() -> str:
    v = os.environ.get("NASCENCE_LEXICAL_CLAIM_GATE", "").strip().lower()
    return v if v in ("off", "lookup", "finding") else LEXICAL_CLAIM_GATE


def _write(row: dict) -> None:
    path = profile.guard_path(_LOG)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[closure_gate] log write failed (%s: %s)", type(exc).__name__, exc)


def judge_user(question: str, finding: str, title: str = "") -> str:
    """The judge's whole input: the whole question and the whole finding."""
    q = " ".join(str(question or "").split())
    f = str(finding or "").strip()[:GATE_FINDING_CAP]
    t = " ".join(str(title or "").split())
    return f"QUESTION: {q}\n\nMATERIAL" + (f" ({t})" if t else "") + f":\n{f}"


def verdict_of(d: dict) -> str:
    """rule_detail's dict as yes | no | partly | unavailable (partly = the two families split with no tiebreak)."""
    how = (d or {}).get("how")
    v = (d or {}).get("verdict")
    if v is True:
        return "yes"
    if how == "split_no_tiebreak":
        return "partly"
    if v is False:
        return "no"
    return "unavailable"


async def judge(question: str, finding: str, title: str = "", context: str = "") -> dict:
    """Ask the decoupled panel. Returns {"verdict": yes|no|partly|unavailable, "how", "why", "v1", "v2", "secs"}.
    Never raises; a timeout or any failure is 'unavailable'."""
    t0 = time.time()
    out = {"verdict": "unavailable", "how": "unavailable", "why": "", "v1": None, "v2": None, "secs": 0.0}
    try:
        user = judge_user(question, finding, title)
        fn = _judge
        if fn is None:
            from core import judge_panel as _jp
            coro = _jp.rule_detail(GATE_SYS, user, GATE_KEY, context=context or "closure_gate",
                                   num_predict=GATE_NUM_PREDICT)
        else:
            coro = fn(GATE_SYS, user)
        d = await asyncio.wait_for(coro, timeout=GATE_TIMEOUT_S)
        out.update(verdict=verdict_of(d), how=str(d.get("how") or ""), why=str(d.get("why") or "")[:300],
                   v1=d.get("v1"), v2=d.get("v2"))
    except (asyncio.TimeoutError, TimeoutError):
        out["how"] = "timeout"
    except Exception as exc:
        out["how"] = f"error:{type(exc).__name__}"[:40]
    out["secs"] = round(time.time() - t0, 1)
    return out


def pick_finding(fresh: dict, return_text: str = "") -> tuple[str, str, str, bool]:
    """(how, title, finding text, must_attach) for a settle on this entry. See the module header."""
    from core import frontier as _fr
    if _fr.finding_from_lookup(fresh or {}):
        return "lookup", str(fresh.get("finding_title") or ""), str(fresh.get("finding") or ""), False
    rt = (return_text or "").strip()
    if rt:
        return "line", MEMORY_FINDING_TITLE, rt, True
    return "line", str((fresh or {}).get("finding_title") or ""), str((fresh or {}).get("finding") or ""), False


def _gate_dict(d: dict, trigger: str, m: str) -> dict:
    return {"verdict": d.get("verdict"), "how": d.get("how"), "why": d.get("why"), "ts": round(time.time(), 1),
            "by": "judge_panel", "trigger": trigger, "mode": m}


async def settle_yes(q_id: str, ent: dict | None = None, return_text: str = "", cycle_id: str = "") -> dict:
    """He said `settled: yes` about this entry (core/follow_line.settle). Returns
    {"resolved": bool, "how": line|lookup, "status": the entry's status afterwards or None, "verdict", "mode",
     "entry": the fresh entry (a copy) when it was resolved through the gate}.
    NonLiveWriteError propagates; anything else falls back to the old close."""
    from core import frontier as _fr
    m = mode()
    out = {"resolved": False, "how": "line", "status": None, "verdict": None, "mode": m, "entry": None}
    if m == "off":
        out["resolved"] = _fr.resolve(q_id, how="line")
        return out
    try:
        profile.guard_path(_LOG)
    except profile.NonLiveWriteError:
        # A non-live process that has not redirected this log (an older test, a lab script): the gate stands
        # aside, no model is asked, and the old close runs through frontier's own fenced writer.
        out["mode"] = "off"
        out["resolved"] = _fr.resolve(q_id, how="line")
        return out
    try:
        fresh = _fr.get(q_id) or dict(ent or {})
        how, title, text, must_attach = pick_finding(fresh, return_text)
        out["how"] = how
        row = {"ts": round(time.time(), 1), "trigger": "settled", "mode": m, "qid": q_id,
               "q": fresh.get("q") or (ent or {}).get("q") or "", "how": how, "finding_title": title,
               "finding_chars": len(text), "finding": text[:GATE_FINDING_CAP], "cycle_id": str(cycle_id or "")[:8]}
        if not text.strip():
            d = {"verdict": "none", "how": "no_finding", "why": ""}
        else:
            d = await judge(row["q"], text, title, context=f"closure_gate:{q_id[:8]}")
        out["verdict"] = d["verdict"]
        row.update(verdict=d["verdict"], judge_how=d.get("how"), why=d.get("why"), v1=d.get("v1"), v2=d.get("v2"),
                   secs=d.get("secs"))
        if m == "shadow":
            out["resolved"] = _fr.resolve(q_id, how="line")
            out["how"] = "line"
            row.update(action="old_close", resolved=out["resolved"], would_how=how)
        else:
            if must_attach and text.strip():
                _fr.attach_finding(q_id, title, text[:600])
            gate = _gate_dict(d, "settled", m)
            if d["verdict"] == "yes" and _fr.resolve_gated(q_id, how, gate):
                out["resolved"] = True
                out["entry"] = _fr.get(q_id)
                row.update(action="resolved", resolved=True)
            else:
                reason = "no_finding" if d["verdict"] == "none" else f"gate_{d['verdict']}"
                made = _fr.mark_provisional(q_id, how, reason, gate)
                row.update(action="provisional" if made else "unchanged", resolved=False)
        out["status"] = (_fr.get(q_id) or {}).get("status")
        row["status_after"] = out["status"]
        _write(row)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.warning("[closure_gate] settle_yes failed, falling back to the old close (%s: %s)", type(exc).__name__, exc)
        try:
            if (_fr.get(q_id) or {}).get("status") == "open":
                out["resolved"] = _fr.resolve(q_id, how="line")
                out["how"] = "line"
        except profile.NonLiveWriteError:
            raise
        except Exception:
            pass
    return out


async def _claim(q: dict, text: str) -> dict:
    """A lexical would-close on a question that carries a finding, tested. Never raises past the fence."""
    from core import frontier as _fr
    m = mode()
    qid = str(q.get("id") or "")
    how = "lookup" if _fr.finding_from_lookup(q) else "line"
    row = {"ts": round(time.time(), 1), "trigger": "lexical_claim", "mode": m, "qid": qid, "q": q.get("q") or "",
           "how": how, "finding_title": q.get("finding_title") or "", "finding_chars": len(q.get("finding") or ""),
           "finding": str(q.get("finding") or "")[:GATE_FINDING_CAP], "claim_text": (text or "")[:400]}
    try:
        d = await judge(row["q"], q.get("finding") or "", q.get("finding_title") or "", context=f"closure_gate:lex:{qid[:8]}")
        row.update(verdict=d["verdict"], judge_how=d.get("how"), why=d.get("why"), v1=d.get("v1"), v2=d.get("v2"),
                   secs=d.get("secs"), action="logged", resolved=False)
        if m == "enforce" and d["verdict"] == "yes":
            fresh = _fr.get(qid) or {}
            if fresh.get("finding_ts") == q.get("finding_ts") and _fr.resolve_gated(qid, how, _gate_dict(d, "lexical_claim", m)):
                row.update(action="resolved", resolved=True)
                _after_answered(_fr.get(qid) or {})
        row["status_after"] = (_fr.get(qid) or {}).get("status")
        _write(row)
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        logger.debug("[closure_gate] claim failed (non-fatal): %s", exc)
    return row


def lexical_claim(q: dict, text: str) -> bool:
    """Called by frontier.resolve_if_addressed in shadow mode with the entry it would have closed. Schedules the
    gate on the running loop when the flags allow it; True if scheduled. Never awaited by the thought loop."""
    try:
        cm, m = lexical_claim_mode(), mode()
        if cm == "off" or m == "off" or not q.get("id") or not q.get("finding"):
            return False
        from core import frontier as _fr
        if cm == "lookup" and not _fr.finding_from_lookup(q):
            return False
        key = (q["id"], q.get("finding_ts"))
        if key in _claimed:
            return False
        profile.guard_path(_LOG)
        loop = asyncio.get_running_loop()
        _claimed[key] = time.time()
        if len(_claimed) > 400:
            for k in sorted(_claimed, key=_claimed.get)[:200]:
                _claimed.pop(k, None)
        t = loop.create_task(_claim(dict(q), text))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)
        return True
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return False


def _after_answered(ent: dict) -> None:
    """Phase 5: a question answered through the gate with a lookup finding writes its resolution memory
    (core/closure.record_lookup_answered; deterministic, no model call). Off-thread; never raises."""
    try:
        from core import frontier as _fr
        if not ent or not _fr.finding_from_lookup(ent) or ent.get("resolved_how") != "lookup":
            return
        from core import closure as _cl
        import threading
        threading.Thread(target=_cl.record_lookup_answered, args=(dict(ent),), daemon=True,
                         name="closure-lookup-arm").start()
    except Exception as exc:
        logger.debug("[closure_gate] lookup arm not started (non-fatal): %s", exc)


def status() -> dict:
    """Read-only, for du_pulse: the last 500 gate rows by verdict and action. Operator view only."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 500)
    except Exception:
        rows = []
    v: dict = {}
    a: dict = {}
    for r in rows:
        v[str(r.get("verdict"))] = v.get(str(r.get("verdict")), 0) + 1
        a[str(r.get("action"))] = a.get(str(r.get("action")), 0) + 1
    return {"mode": mode(), "lexical_claim": lexical_claim_mode(), "rows": len(rows), "verdicts": v, "actions": a,
            "calibration": CALIBRATION}

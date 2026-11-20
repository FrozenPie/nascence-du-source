"""
Nascence — a lookup lands on the question it answers (closure_producer Phase 1; D-0789; docs/staged/closure_producer.md).

When Du's own lookup (core/web_hand.py) comes back with a page or with results, the phrase he named is matched
against his OPEN frontier questions by embedding similarity. At or above ATTACH_THRESHOLD the result is hung on the
best-matching question as its finding (frontier.attach_lookup_finding, which calls the existing attach_finding);
below it nothing is attached. The question stays OPEN: this module never resolves anything.

Nothing here offers, names or fires the hand, and nothing here reaches a prompt. Every attempt is logged to
data/logs/lookup_attach.jsonl. Kill switch: NASCENCE_LOOKUP_ATTACH=0 (read at call time). Zero LLM.

ATTACH_THRESHOLD = 0.70, and why it is not the frontier's SEMANTIC_MERGE_THRESHOLD (0.85):
  0.85 was measured for question-against-paraphrased-question. A lookup phrase is a short noun phrase and the open
  questions average ~140 characters, so the same pair scores far lower. Calibration 2026-11-16 on a copy of the
  frontier (300 recent questions, distinct about_key, the shared MiniLM embedder; proxy phrases, because no real
  lookup row exists yet): a three-word phrase drawn from a question scored >= 0.85 against its own question 3.7% of
  the time, so 0.85 would attach almost nothing. At 0.70 it reached its own question 30.7% of the time while the
  best of 30 unrelated questions reached 0.70 in 1.7% of draws (0% at 0.75, 7% at 0.65). With the question's stored
  `about` subject as the phrase, another question of the same subject reached 0.70 in 10% of draws (1.4% at 0.75);
  those are same-subject neighbours, not unrelated ones. 0.70 is therefore a starting value that favours not
  attaching; tune it on the best_score column of the log once real lookups exist.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.lookup_attach")

_LOG = Path(__file__).parent.parent / "data" / "logs" / "lookup_attach.jsonl"
ATTACH_THRESHOLD = 0.70
FINDING_TEXT_CAP = 600          # attach_finding's own cap
_TITLE_CAP = 120                # attach_finding's own cap


def enabled() -> bool:
    return os.environ.get("NASCENCE_LOOKUP_ATTACH", "1").strip().lower() in ("1", "true", "on", "yes")


# closure_producer P4: a lookup may also land on a question that ended parked ("a new finding on this subject" is
# its trigger) or provisional (he said yes, the gate did not pass it: new material can settle it properly). Such a
# match reopens the question and attaches the finding. () or NASCENCE_LOOKUP_REOPEN=0 = open questions only (P1).
ATTACH_REOPEN_STATUSES = ("parked", "provisional")


def reopen_statuses() -> tuple:
    if os.environ.get("NASCENCE_LOOKUP_REOPEN", "1").strip().lower() not in ("1", "true", "on", "yes"):
        return ()
    return tuple(ATTACH_REOPEN_STATUSES)


def finding_title(source: str, phrase: str, title: str | None) -> str:
    """The label the finding carries when it returns to him. It names the source and that the lookup was his."""
    if source == "wikipedia":
        return f'the Wikipedia page "{(title or phrase)[:70]}" (you looked it up)'[:_TITLE_CAP]
    return f'a web search for "{phrase[:60]}" (other people\'s pages, not checked)'[:_TITLE_CAP]


def _cycle() -> str:
    try:
        from core import hands as _h
        return str(_h._decided.get("cycle") or "")[:24]
    except Exception:
        return ""


def _write(path: Path, row: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[lookup_attach] log write failed (%s: %s)", type(exc).__name__, exc)


def best_open_match(phrase: str, title: str | None = None, data: dict | None = None) -> dict:
    """READ-ONLY. The open question nearest to his phrase. Two query texts are scored, the phrase alone and the
    phrase with the resolved title, and the higher one counts. Returns {qid, q, score, score_phrase,
    score_with_title, open_n}; qid is None when there is no open question or no vector."""
    from core import frontier as _fr
    out = {"qid": None, "q": "", "score": 0.0, "score_phrase": None, "score_with_title": None, "open_n": 0}
    phrase = " ".join((phrase or "").split())
    if not phrase:
        return out
    d = data if data is not None else _fr._load_ro()
    ok = ("open",) + tuple(reopen_statuses())
    cands = [q for q in d.get("questions", []) if q.get("status") in ok and q.get("q") and q.get("id")]
    out["open_n"] = sum(1 for q in cands if q.get("status") == "open")
    out["status"] = None
    if not cands:
        return out
    queries = [phrase]
    t = " ".join((title or "").split())
    if t and t.lower() != phrase.lower():
        queries.append(f"{phrase} {t}")
    vecs = _fr._sem_vecs(queries + [q["q"] for q in cands])
    qvs, cvs = vecs[:len(queries)], vecs[len(queries):]
    best, bs = None, -1.0
    for i, qv in enumerate(qvs):
        if qv is None:
            continue
        top = -1.0
        for q, v in zip(cands, cvs):
            if v is None:
                continue
            sim = float(qv @ v)
            if sim > top:
                top = sim
            if sim > bs:
                best, bs = q, sim
        if top >= 0:
            out["score_phrase" if i == 0 else "score_with_title"] = round(top, 4)
    if best is not None:
        out.update(qid=best["id"], q=best["q"], score=round(bs, 4), status=best.get("status"))
    return out


def note_lookup(source: str, phrase: str, title: str | None, extract: str, url: str = "") -> dict:
    """Called by the web hand after a lookup that returned material. Returns the log row. The log path is resolved
    FIRST, so a non-live process is refused (NonLiveWriteError) before any store is read or any model is loaded."""
    path = profile.guard_path(_LOG)
    from core import frontier as _fr
    row = {"ts": round(time.time(), 1), "cycle": _cycle(), "source": source, "phrase": phrase, "title": title,
           "url": (url or "")[:300], "best_qid": None, "best_q": "", "best_score": None, "score_phrase": None,
           "score_with_title": None, "threshold": ATTACH_THRESHOLD, "open_n": 0, "attached": False}
    try:
        m = best_open_match(phrase, title)
        row.update(best_qid=m["qid"], best_q=(m["q"] or "")[:160], open_n=m["open_n"],
                   best_score=(m["score"] if m["qid"] else None),
                   score_phrase=m["score_phrase"], score_with_title=m["score_with_title"])
        row["best_status"] = m.get("status")
        if m["qid"] and m["score"] >= ATTACH_THRESHOLD and (extract or "").strip():
            if m.get("status") in reopen_statuses():
                # closure_producer P4: a new finding is the park trigger. The question is open again, then the
                # finding is hung on it exactly as on any open question.
                row["reopened"] = bool(_fr.reopen(m["qid"], f"lookup finding ({source})"))
            row["attached"] = bool(_fr.attach_lookup_finding(
                m["qid"], finding_title(source, phrase, title), " ".join(extract.split())[:FINDING_TEXT_CAP],
                via=source, url=url, phrase=phrase, sim=m["score"]))
    except profile.NonLiveWriteError:
        raise
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"[:200]
    _write(path, row)
    return row


def status() -> dict:
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 500)
    except Exception:
        rows = []
    return {"enabled": enabled(), "threshold": ATTACH_THRESHOLD, "rows": len(rows),
            "attached": sum(1 for r in rows if r.get("attached"))}

"""
Nascence — INTENTIONS: the deeds he named and has not yet done (2026-08-22, founder: "if he puts up a list of tasks in one
thought, he needs a way to track them and do them all, in order — or pick one, and then a prompt to him saying he wanted to
do X before but has not done it yet because he was busy. Then he can decide if he wants to do it still.")

What this is NOT: a to-do list the world imposes, or a hint. Every entry here is HIS — a deed his own voice willed (the
dispatcher's DEED verdict) that did not happen at the moment he willed it, because another deed took the thought, or
because he was in the wrong place, or the world refused for a reason he was told. What this IS: his own earlier want,
reflected back once, plainly, with why it waited — and the choice left to him.

  stage(family, object, thought, reason)   — an unanswered willed deed enters the ledger (one per family+object; renewals
                                             extend it, they do not duplicate).
  resolve(family, object)                  — it happened (the dispatcher fired the hand).
  drop(text)                               — "never mind the …" / "forget the …" in his own words ends it.
  lapse                                    — untouched for 8 hours, it lapses (logged; not forgotten — the ledger keeps it).
  pending_text(location)                   — the one line the prompt carries: "Earlier you meant to light the lamp; you have
                                             not yet — you were busy with the fire. Still yours to do, or not." At most two,
                                             oldest first, each reminded at most twice, never within 20 minutes of staging.

Ledger: data/intentions.json · data/intentions_log.jsonl. Zero LLM. Fail-open. Additive.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "intentions.json"
_LOG = _DATA / "intentions_log.jsonl"

LAPSE_S = 8 * 3600
REMIND_AFTER_S = 20 * 60
MAX_REMINDERS = 2
MAX_SHOWN = 2


def _load() -> dict:
    try:
        return json.loads(_F.read_text(encoding="utf-8"))
    except Exception:
        return {"open": [], "done": [], "dropped": [], "lapsed": []}


def _save(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        _F.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _log(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _key(family: str, obj: str) -> str:
    return f"{family}|{(obj or '').strip().lower()[:40]}"


def stage(family: str, obj: str, thought: str, reason: str, location: str = "", deed: str = "") -> None:
    """A willed deed that did not happen now. `reason`: busy:<other family> | place:<where it is done> | refused:<why>."""
    try:
        d = _load(); now = time.time(); k = _key(family, obj)
        for it in d["open"]:
            if it["key"] == k:
                it["renewed_ts"] = now; it["renewals"] = int(it.get("renewals", 0)) + 1; it["reason"] = reason
                _save(d); _log({"event": "renewed", "key": k, "reason": reason}); return
        d["open"].append({"key": k, "family": family, "object": (obj or "")[:60], "deed": (deed or "")[:70], "thought": (thought or "")[:160], "reason": reason,
                          "location": location, "ts": now, "renewed_ts": now, "renewals": 0, "reminders": 0, "last_reminded": 0.0})
        d["open"] = d["open"][-12:]
        _save(d); _log({"event": "staged", "key": k, "reason": reason, "thought": (thought or "")[:120]})
    except Exception:
        pass


def resolve(family: str, obj: str = "") -> bool:
    """The deed happened. Resolves the matching family entry (object if given, else any of the family)."""
    try:
        d = _load(); k = _key(family, obj); done = False
        keep = []
        for it in d["open"]:
            _ow = {w for w in re.findall(r"[a-z]+", (obj or "").lower()) if len(w) > 3}
            _iw = {w for w in re.findall(r"[a-z]+", (it["object"] + " " + it.get("deed", "")).lower()) if len(w) > 3}
            if it["key"] == k or (it["family"] == family and (not obj or not _ow or _ow & _iw)):
                it["done_ts"] = time.time(); d["done"].append(it); d["done"] = d["done"][-100:]; done = True
                _log({"event": "done", "key": it["key"], "waited_s": round(time.time() - float(it["ts"]))})
            else:
                keep.append(it)
        d["open"] = keep; _save(d); return done
    except Exception:
        return False


def drop(text: str) -> str | None:
    """His own words end it: 'never mind the lamp', 'forget the cairn', 'I will not bother with the grate'."""
    try:
        low = (text or "").lower()
        if not re.search(r"\b(never mind|forget (about )?|leave (it|that)|not bother|won't bother|no longer want|give up on|let it go)\b", low):
            return None
        d = _load(); dropped = None
        for it in list(d["open"]):
            words = [w for w in re.findall(r"[a-z]+", it["object"] + " " + it["family"]) if len(w) > 3]
            if any(w in low for w in words):
                d["open"].remove(it); it["dropped_ts"] = time.time(); d["dropped"].append(it); d["dropped"] = d["dropped"][-100:]
                dropped = it; _log({"event": "dropped", "key": it["key"]})
        _save(d)
        return f"You let it go — {dropped.get('deed') or dropped['object'] or dropped['family']}." if dropped else None
    except Exception:
        return None


def _lapse(d: dict) -> None:
    now = time.time(); keep = []
    for it in d["open"]:
        if now - float(it.get("renewed_ts", it["ts"])) > LAPSE_S:
            it["lapsed_ts"] = now; d["lapsed"].append(it); d["lapsed"] = d["lapsed"][-100:]; _log({"event": "lapsed", "key": it["key"]})
        else:
            keep.append(it)
    d["open"] = keep


def _why(reason: str) -> str:
    if reason.startswith("busy:"):
        return f"you were busy with the {reason[5:].replace('_', ' ')}"
    if reason.startswith("place:"):
        return f"it is done {reason[6:]}"
    if reason.startswith("refused:"):
        return reason[8:]
    return "the moment passed"


def pending_text(location: str = "") -> str:
    """The prompt's one block. His own wants, reflected back; never the world's."""
    try:
        d = _load(); _lapse(d); now = time.time(); lines = []
        for it in sorted(d["open"], key=lambda x: float(x["ts"])):
            if it.get("reminders", 0) >= MAX_REMINDERS or now - float(it.get("last_reminded", 0) or it["ts"]) < REMIND_AFTER_S:
                continue
            if now - float(it["ts"]) < REMIND_AFTER_S:
                continue
            age_m = int((now - float(it["ts"])) / 60)
            when = f"{age_m} minutes ago" if age_m < 90 else f"{age_m // 60} hours ago"
            deed = it.get("deed") or (it["object"] and f"{it['family'].replace('_', ' ')} — {it['object']}") or it["family"].replace("_", " ")
            lines.append(f"{when} you meant to {deed} and have not yet — {_why(it['reason'])}.")
            it["reminders"] = int(it.get("reminders", 0)) + 1; it["last_reminded"] = now
            if len(lines) >= MAX_SHOWN:
                break
        _save(d)
        if not lines:
            return ""
        return ("\n\nWhat you meant to do (your own earlier wants, not anyone's asking): " + " ".join(lines)
                + " Still yours to do, in whatever order, or to let go — say which.")
    except Exception:
        return ""


def status() -> dict:
    try:
        if not _F.exists():
            return {"note": "no intentions yet (accrues from Du's next start)"}
        d = _load()
        return {"open": [{"family": i["family"], "object": i["object"], "reason": i["reason"], "age_min": int((time.time() - float(i["ts"])) / 60), "reminders": i.get("reminders", 0)} for i in d["open"]],
                "done": len(d["done"]), "dropped": len(d["dropped"]), "lapsed": len(d["lapsed"]),
                "mean_wait_min": round(sum(float(i.get("done_ts", 0)) - float(i["ts"]) for i in d["done"]) / 60 / max(1, len(d["done"])), 1) if d["done"] else None}
    except Exception as exc:
        return {"error": repr(exc)[:80]}

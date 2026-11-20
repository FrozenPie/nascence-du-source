"""D-0197 Du-lens word x context gauge, SHADOW ONLY (J-3573; re-ruled 2026-11-06 after F-4178 / J-3470).

62 corroborated bundled (word, context-bundle) pairs (core/du_lens_pairs_d0197.json, copied from
C:/UDMS/data/du_lens/d0197_defeater_test_2026-11-06.json) are checked against each idle thought:

  * a PAIR IS PRESENT when every member of its context bundle holds in the latest idle geometry tuple (place:,
    standpoint:, weather:, fire:, light:, cat_at:, sound:, smell: -- same row_contexts() as the UDMS test) or, for the
    act:/obj: pairs, in the hands_trace row of the SAME idle thought (the UDMS same-thought join: first 70 chars equal,
    within 60 s of the idle tuple);
  * a pair FIRES when it is present AND its word is in the thought's full text (UDMS tokenizer).

One row per evaluation -> data/du_lens_gauge_shadow.jsonl: {ts, kind idle|hands, n_present, n_fired, present, fired,
thought_head}. `present` is the denominator the read job needs ("fewer than 10% firing where the context is present");
`fired` entries are "word|bundle" pair ids.

Hard guarantees: observe-only. Writes ONLY that file. No recall change, no prompt line, no census field. The write
resolves through profile.guard_path (a non-live process is refused and swallowed). Fail-open: nothing here raises into
geometry_census.snapshot() or hands.trace(). Kill-switch: DU_LENS_GAUGE = False.
Reader / HUD summary: summary() here, hud/server.py monitor `du_lens_gauge` and /api/du_lens_gauge.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path

from core import profile

logger = logging.getLogger(__name__)

DU_LENS_GAUGE = True                               # kill-switch: False -> record_*() do nothing

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "du_lens_gauge_shadow.jsonl"        # tests must temp-path this, never touch the live file
_PAIRS_FILE = Path(__file__).parent / "du_lens_pairs_d0197.json"
_MAX_LOG_BYTES = 100 * 1024 * 1024                 # runaway guard
_JOIN_WINDOW_S = 60.0                              # UDMS same-thought join window
_JOIN_PREFIX = 70
_lock = threading.Lock()
_pairs_cache: list | None = None
_last_idle: dict = {"ts": 0.0, "head": ""}          # the latest idle thought, so a hands row can be joined to it

# copied verbatim from the UDMS test (scripts/du_lens_first_test.py via d0197_defeater_pairs_prereg.py)
_STOPWORDS = set("""
a about above after again against all almost also although always am among an and another any are
aren around as at be because been before being below between both but by came can cannot could
couldn did didn do does doesn doing don done down during each either else even ever every few for
from further get gets got had hadn has hasn have haven having he her here hers herself him himself
his how however i if in into is isn it its itself just let like ll may me might more most much must
my myself neither never no nor not now of off on once one only onto or other ought our ours
ourselves out over own perhaps quite rather re really same shall she should shouldn since so some
something somehow someone somewhere still such than that the their theirs them themselves then
there these they this those though through thus to too toward towards under until up upon us very
was wasn we were weren what whatever when whenever where whether which while who whom whose why
will with within without won would wouldn yet you your yours yourself yourselves
""".split())
_TOKEN_RE = re.compile(r"[a-z']+")


def tokens(text: str) -> set:
    out = set()
    for t in _TOKEN_RE.findall((text or "").lower()):
        t = t.strip("'")
        if len(t) >= 3 and t.isalpha() and t not in _STOPWORDS:
            out.add(t)
    return out


def row_contexts(r: dict) -> set:
    """The tuple row's context keys -- identical to the UDMS test's row_contexts()."""
    out = set()
    for key, fld in (("place", "place"), ("standpoint", "standpoint"), ("weather", "weather"), ("fire", "fire"),
                     ("light", "light_band")):
        v = r.get(fld)
        if v:
            out.add(f"{key}:{v}")
    cat = (r.get("objects") or {}).get("cat") or {}
    if cat.get("location"):
        out.add(f"cat_at:{cat['location']}")
    for s in (r.get("sounds") or []):
        out.add(f"sound:{s}")
    for s in (r.get("smells") or []):
        out.add(f"smell:{s}")
    return out


def pairs() -> list:
    global _pairs_cache
    if _pairs_cache is None:
        _pairs_cache = json.loads(_PAIRS_FILE.read_text(encoding="utf-8"))["pairs"]
    return _pairs_cache


def pair_id(p: dict) -> str:
    return f"{p['word']}|{p['bundle']}"


def _is_action(p: dict) -> bool:
    return all(m.startswith(("act:", "obj:")) for m in p["members"])


def evaluate(contexts: set, text: str, action: bool) -> tuple[list, list]:
    """(present pair ids, fired pair ids) for the context-pair family (action=False) or the act/obj family."""
    toks = tokens(text)
    present, fired = [], []
    for p in pairs():
        if _is_action(p) != action:
            continue
        if all(m in contexts for m in p["members"]):
            pid = pair_id(p)
            present.append(pid)
            if p["word"] in toks:
                fired.append(pid)
    return present, fired


def _append(row: dict) -> dict | None:
    try:
        _log = profile.guard_path(_LOG)             # resolve BEFORE any I/O; refusal swallowed below
    except Exception as exc:
        logger.debug("[du-lens-gauge] refused by the fence (non-live): %s", exc)
        return None
    try:
        with _lock:
            if _log.exists() and _log.stat().st_size > _MAX_LOG_BYTES:
                return None
            _log.parent.mkdir(parents=True, exist_ok=True)
            with open(_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row
    except Exception as exc:
        logger.debug("[du-lens-gauge] write failed (non-fatal): %s", exc)
        return None


def record_idle(tuple_row: dict, thought: str, now: float | None = None) -> dict | None:
    """Called by geometry_census.snapshot() after it wrote an idle tuple. Never raises."""
    if not DU_LENS_GAUGE:
        return None
    try:
        t = float(tuple_row.get("ts") or (time.time() if now is None else now))
        present, fired = evaluate(row_contexts(tuple_row), thought, action=False)
        _last_idle["ts"], _last_idle["head"] = t, (thought or "").strip()[:_JOIN_PREFIX]
        return _append({"ts": round(t, 1), "kind": "idle", "n_present": len(present), "n_fired": len(fired),
                        "present": present, "fired": fired, "thought_head": (thought or "").strip()[:40]})
    except Exception as exc:
        logger.debug("[du-lens-gauge] idle record failed (non-fatal): %s", exc)
        return None


def record_hands(thought: str, act_kind: str, act_object: str, now: float | None = None) -> dict | None:
    """Called by hands.trace(). Only a row whose thought is the latest idle thought (same-thought join, 60 s) counts."""
    if not DU_LENS_GAUGE:
        return None
    try:
        t = time.time() if now is None else float(now)
        head = (thought or "").strip()[:_JOIN_PREFIX]
        if not head or head != _last_idle["head"] or abs(t - _last_idle["ts"]) > _JOIN_WINDOW_S:
            return None
        ctx = set()
        if act_kind:
            ctx.add(f"act:{act_kind}")
        if (act_object or "").strip():
            ctx.add(f"obj:{act_object.strip()}")
        present, fired = evaluate(ctx, thought, action=True)
        return _append({"ts": round(t, 1), "kind": "hands", "n_present": len(present), "n_fired": len(fired),
                        "present": present, "fired": fired, "thought_head": head[:40]})
    except Exception as exc:
        logger.debug("[du-lens-gauge] hands record failed (non-fatal): %s", exc)
        return None


def summary(path: Path | None = None, now: float | None = None, window_s: float = 86400.0) -> dict:
    """Live per-pair counts (all time + last window) and firing rate over the last window. Read-only, fail-open."""
    p = Path(path) if path else _LOG
    now = time.time() if now is None else now
    per: dict = {pid: {"present": 0, "fired": 0, "present_24h": 0, "fired_24h": 0} for pid in map(pair_id, pairs())}
    n_rows = n_rows_w = 0
    try:
        if p.exists():
            with open(p, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    w = now - float(r.get("ts") or 0) <= window_s
                    n_rows += 1
                    n_rows_w += 1 if w else 0
                    for pid in r.get("present") or []:
                        if pid in per:
                            per[pid]["present"] += 1
                            per[pid]["present_24h"] += 1 if w else 0
                    for pid in r.get("fired") or []:
                        if pid in per:
                            per[pid]["fired"] += 1
                            per[pid]["fired_24h"] += 1 if w else 0
    except Exception as exc:
        logger.debug("[du-lens-gauge] summary failed (non-fatal): %s", exc)
    pw = sum(v["present_24h"] for v in per.values())
    fw = sum(v["fired_24h"] for v in per.values())
    pa = sum(v["present"] for v in per.values())
    fa = sum(v["fired"] for v in per.values())
    for v in per.values():
        v["rate"] = round(v["fired"] / v["present"], 4) if v["present"] else None
        v["rate_24h"] = round(v["fired_24h"] / v["present_24h"], 4) if v["present_24h"] else None
    return {"rows": n_rows, "rows_24h": n_rows_w, "present_24h": pw, "fired_24h": fw,
            "rate_24h": round(fw / pw, 4) if pw else None, "present_all": pa, "fired_all": fa,
            "rate_all": round(fa / pa, 4) if pa else None, "pairs": per}

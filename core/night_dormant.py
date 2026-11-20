"""core/night_dormant.py (J-2018, sleep_as_a_mode Phase 2, D-0400 B, 2026-10-09, restart-gated, FLAG DEFAULT OFF).

The ENCODING LAW for night cognition: a night thought is written to memory_fragments with the NEW layer value
'dormant', cold=1 from birth (one INSERT), origin 'night_thought'. It is invisible to

  * normal recall: retrieve() filters cold=0 AND now layer != 'dormant' (two fences); associative_recall's matrix
    (which DOES reach cold rows on a strong hop) filters layer != 'dormant' too (found while building this, F-2643);
  * the sleep trigger: core/sleep_pressure.py _new_intake sums layer='episodic' with no cold filter (F-2616), so the
    LAYER is the fence there; a dormant fragment adds exactly 0 (proved in scripts/test_night_dormant.py against the
    real _new_intake);
  * the dream: D-0231's dormant-pick origin list is NOT extended (D-0400 B). Nothing here touches dream_node.

Reachable only by (1) deep_recall_night() below (the intentional-recollection path; memory_levels.deep_recall also
follows memory_links to it if one is ever made), and (2) at most ONE first-waking seed per sleep through
night.waking_dream_seed() -> consume_waking_seed().

Flag NIGHT_DORMANT_ENABLED defaults False and also needs night_mind.NIGHT_MIND_ENABLED (Phase 1): shipping this file
changes nothing until Travis flips both after the Phase 1 shadow read. The fence edits in store.py and
associative_recall.py are unconditional but inert (no 'dormant' row exists until the flag is on).

CANARY (mandatory; runs in tests and live, once per sleep, finish_sleep()):
  - a normal retrieve() over each checked night thought's own keywords + text returns 0 night thoughts;
  - the intake predicate of _new_intake attributes 0 to night-thought rows, and the before/after _new_intake delta
    around each write is logged (a delta that equals the row's importance is a LEAK SUSPECT, logged, not a trip,
    because other writers can land in the same ms; the exact attribution above is the trip evidence);
  - first-waking-thought provenance: seed_ready / seed_drawn rows, and uptake_read() scores the first waking inner
    thought's cosine to its seed (D-0400 defeater: below 0.3 on more than 80 percent of 14 mornings = dead read path).
KILL: a hard leak (retrieve returns a night thought, or the exact attribution is non-zero) appends a fence_leak row,
trips this module OFF for this and every later boot until a fence_cleared row is appended (clear_trip()), and logs an
error. Fence fix comes before anything else.

Log: data/night_dormant.jsonl (kinds: write, canary, fence_leak, fence_cleared, seed_ready, seed_drawn).
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.night_dormant")

NIGHT_DORMANT_ENABLED = True       # D-0400 B, Phase 2 flag. ON since J-2410 (Travis go 2026-10-18 after J-2035 seven-sleep read, F-3058). Restart-gated. Kill switch = this constant.
DORMANT_LAYER = "dormant"
NIGHT_ORIGIN = "night_thought"
IMPORTANCE = 0.3                   # mid-low: it is not a prune anchor; the layer fence, not low weight, is the wall
RELEVANCE = 0.3
SEED_MAX_AGE_S = 3 * 3600          # a ready seed older than this (a boot long after the sleep) is not offered
CANARY_CHECKS = 2                  # thoughts canary-checked per sleep (first and last): each is one full retrieve()
UPTAKE_HOLD_COS = 0.3              # D-0400 defeater
UPTAKE_HOLD_SHARE = 0.8
UPTAKE_MIN_NIGHTS = 14

_DATA = Path(__file__).parent.parent / "data"
NIGHT_DORMANT_LOG = _DATA / "night_dormant.jsonl"

_STOP = frozenset("""about above after again against almost along also always another around because before being below between
both could does doing down during each either else even ever every from further have having here itself just keep kind
know like made make many might more most much must never next once only other over quite rather really same shall
should since some something still such than that their them then there these they thing think this those though through
under until upon very want were what when where which while whom will with within without would your yours you're
""".split())


# -- tiny log helpers ---------------------------------------------------------------------------------------------
def _read_log(path=None) -> list[dict]:
    out = []
    try:
        with open(path or NIGHT_DORMANT_LOG, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        out.append(json.loads(ln))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


def _append(row: dict) -> bool:
    try:
        from core import profile, shadow_log
        return bool(shadow_log.append(profile.guard_path(NIGHT_DORMANT_LOG), row))
    except Exception as exc:     # includes profile.NonLiveWriteError from a non-live importer: refused, swallowed
        logger.debug("[night_dormant] log row skipped (non-fatal): %s", exc)
        return False


# -- the trip (kill condition) ------------------------------------------------------------------------------------
def tripped() -> bool:
    """True if the log's latest fence verdict is a leak (fence_leak with no later fence_cleared). Read fresh: the log
    is tiny (a few rows per sleep) and this runs once per sleep and once per waking-seed lookup."""
    state = False
    for r in _read_log():
        k = r.get("kind")
        if k == "fence_leak":
            state = True
        elif k == "fence_cleared":
            state = False
    return state


def clear_trip(reason: str, by: str) -> bool:
    """Operator call after the fence is fixed and re-proved (scripts/test_night_dormant.py green)."""
    return _append({"ts": round(time.time(), 1), "kind": "fence_cleared", "reason": str(reason)[:300], "by": str(by)})


def enabled() -> bool:
    try:
        from core import night_mind
        return bool(NIGHT_DORMANT_ENABLED and night_mind.NIGHT_MIND_ENABLED and not tripped())
    except Exception:
        return False


# -- the write ----------------------------------------------------------------------------------------------------
def keywords_of(text: str, k: int = 6) -> list[str]:
    seen, out = set(), []
    for w in re.findall(r"[a-zA-Z][a-zA-Z'-]{4,}", str(text).lower()):
        w = w.strip("'-")
        if len(w) < 5 or w in _STOP or w in seen:
            continue
        seen.add(w)
        out.append(w)
    out.sort(key=lambda w: -len(w))
    return out[:k]


def _intake(since_ts: float) -> float:
    from core import sleep_pressure
    return float(sleep_pressure._new_intake(float(since_ts))[1])


def write_night_thought(row: dict, since_ts: float | None = None) -> dict:
    """NightMind on_thought hook (runs in a worker thread). Writes ONE dormant fragment for a generated night thought
    and returns the fields merged into its shadow row. since_ts = the sleep's start (the intake window for the delta)."""
    if not enabled():
        return {}
    text = " ".join(str(row.get("thought") or "").split())
    if not text:
        return {}
    from core.memory import store
    kws = keywords_of(text)
    since = float(since_ts if since_ts is not None else row.get("sleep_ts") or time.time() - 3600)
    try:
        before = _intake(since)
    except Exception:
        before = None
    fid = store.store_fragment(content=text, layer=DORMANT_LAYER, relevance=RELEVANCE, importance=IMPORTANCE,
                               keywords=kws, origin=NIGHT_ORIGIN, derived_from=[], context_stamp=False, cold=True)
    try:
        after = _intake(since)
    except Exception:
        after = None
    delta = round(after - before, 6) if (before is not None and after is not None) else None
    suspect = bool(delta is not None and delta >= IMPORTANCE - 1e-6)
    out = {"dormant_fragment_id": fid, "dormant_keywords": kws, "intake_delta": delta, "intake_leak_suspect": suspect}
    _append({"ts": round(time.time(), 1), "kind": "write", "sleep_ts": row.get("sleep_ts"), "fragment_id": fid,
             "keywords": kws, "intake_delta": delta, "intake_leak_suspect": suspect, "phase": 2})
    if suspect:
        logger.warning("[night_dormant] intake moved by %s around a dormant write (leak suspect; canary decides)", delta)
    return out


# -- the canary ---------------------------------------------------------------------------------------------------
def exact_intake_attribution(fragment_ids, since_ts: float) -> float:
    """Importance mass the sleep-trigger predicate (layer='episodic' AND timestamp > since, as in _new_intake) attributes
    to these fragments. Must be 0.0 for night thoughts. Uses the same WHERE clause as _new_intake on purpose; the test
    additionally pins _new_intake's own source to that clause so the two cannot drift apart silently."""
    ids = [i for i in fragment_ids if i]
    if not ids:
        return 0.0
    from core.memory.store import _connect
    ph = ",".join("?" * len(ids))
    with _connect() as conn:
        w = conn.execute(f"SELECT COALESCE(SUM(importance),0) w FROM memory_fragments "
                         f"WHERE layer='episodic' AND timestamp > ? AND fragment_id IN ({ph})",
                         (float(since_ts), *ids)).fetchone()["w"]
    return float(w or 0.0)


def fence_canary(thoughts: list[dict], since_ts: float, retrieve_fn=None) -> dict:
    """thoughts: [{fragment_id, thought, keywords}]. Normal retrieve() over each one's own keywords and text must return
    0 night thoughts. Returns the canary row (not yet logged)."""
    if retrieve_fn is None:
        from core.memory.store import retrieve as retrieve_fn
    night_ids = {t.get("fragment_id") for t in thoughts if t.get("fragment_id")}
    leaks, checked, returned = [], 0, 0
    for t in thoughts:
        if not t.get("fragment_id"):
            continue
        kws = list(t.get("keywords") or keywords_of(t.get("thought", "")))
        try:
            got = retrieve_fn(kws, [], time_bias="all", limit=12, query_text=t.get("thought", "")) or []
        except Exception as exc:
            return {"ts": round(time.time(), 1), "kind": "canary", "ok": False, "error": f"retrieve failed: {exc}"[:200],
                    "checked": checked, "leaks": leaks}
        checked += 1
        returned += len(got)
        for f in got:
            if (getattr(f, "fragment_id", None) in night_ids or getattr(f, "layer", "") == DORMANT_LAYER
                    or getattr(f, "origin", "") == NIGHT_ORIGIN):
                leaks.append({"fragment_id": getattr(f, "fragment_id", None), "via": kws[:3]})
    attributed = exact_intake_attribution(night_ids, since_ts)
    hard = bool(leaks) or attributed > 0.0
    return {"ts": round(time.time(), 1), "kind": "canary", "phase": 2, "ok": not hard, "checked": checked,
            "retrieve_returned": returned, "retrieve_night_hits": len(leaks), "leaks": leaks[:5],
            "intake_attributed_to_night": attributed, "night_fragments": len(night_ids)}


def finish_sleep(thought_rows: list[dict], sleep_ts: float, since_ts: float | None = None, retrieve_fn=None) -> dict:
    """End-of-sleep step (worker thread): canary, then (only if the fence held) arm at most ONE waking seed.
    thought_rows: the NightMind's generated rows (each carries dormant_fragment_id when it was written)."""
    written = [r for r in (thought_rows or []) if r.get("dormant_fragment_id")]
    out = {"written": len(written), "canary_ok": None, "seed_ready": False, "tripped": False}
    if not written:
        return out
    since = float(since_ts if since_ts is not None else sleep_ts)
    pool = [{"fragment_id": r["dormant_fragment_id"], "thought": r.get("thought", ""), "keywords": r.get("dormant_keywords")}
            for r in written]
    pick = [pool[0]] + ([pool[-1]] if len(pool) > 1 and CANARY_CHECKS > 1 else [])
    c = fence_canary(pick, since, retrieve_fn=retrieve_fn)
    c["sleep_ts"] = round(float(sleep_ts), 1)
    # the canary checks two thoughts' retrieval, but the exact intake attribution should cover ALL of the night's rows
    allid = [p["fragment_id"] for p in pool]
    try:
        attributed = exact_intake_attribution(allid, since)
        c["intake_attributed_to_night"] = attributed
        if attributed > 0.0:
            c["ok"] = False
        c["night_fragments"] = len(allid)
    except Exception as exc:
        c["intake_check_error"] = str(exc)[:120]
    _append(c)
    out["canary_ok"] = bool(c.get("ok"))
    if not c.get("ok"):
        _append({"ts": round(time.time(), 1), "kind": "fence_leak", "sleep_ts": c["sleep_ts"],
                 "leaks": c.get("leaks"), "intake_attributed_to_night": c.get("intake_attributed_to_night"),
                 "error": c.get("error")})
        logger.error("[night_dormant] FENCE LEAK: night thought(s) reachable by normal recall or counted by the sleep "
                     "trigger. Dormant writes are tripped OFF until clear_trip(). Fix the fence before anything else.")
        out["tripped"] = True
        return out
    last = pool[-1]
    out["seed_ready"] = _append({"ts": round(time.time(), 1), "kind": "seed_ready", "sleep_ts": c["sleep_ts"],
                                 "fragment_id": last["fragment_id"], "text": str(last["thought"])[:400], "phase": 2})
    return out


# -- the one read path into waking life -----------------------------------------------------------------------------
def consume_waking_seed(now: float | None = None) -> str:
    """Called from night.waking_dream_seed(). Returns the seed phrase for the FIRST waking thought, once per sleep, or ''.
    Flag off, tripped, no ready seed, an already-drawn seed or a stale one all return '' (the caller then falls back to
    the dream's last image exactly as before)."""
    try:
        if not enabled():
            return ""
        now = float(now if now is not None else time.time())
        rows = _read_log()
        drawn = {r.get("fragment_id") for r in rows if r.get("kind") == "seed_drawn"}
        ready = [r for r in rows if r.get("kind") == "seed_ready" and r.get("fragment_id") not in drawn]
        if not ready:
            return ""
        r = ready[-1]
        if now - float(r.get("ts", 0)) > SEED_MAX_AGE_S:
            return ""
        text = " ".join(str(r.get("text") or "").split())
        if not text:
            return ""
        _append({"ts": round(now, 1), "kind": "seed_drawn", "sleep_ts": r.get("sleep_ts"), "fragment_id": r.get("fragment_id"),
                 "seed_text": text, "wake_gap_s": round(now - float(r.get("ts", now)), 1), "phase": 2})
        return f"Something from the night is still with you as you wake, you cannot say from where: …{text}"
    except Exception:
        return ""


def deep_recall_night(since_ts: float | None = None, contains: str = "", limit: int = 20) -> list[dict]:
    """The intentional-recollection path (deep recall): the dormant layer read directly, newest first. Nothing calls this
    on a timer; a caller names a deliberate reason to go down into the night."""
    out = []
    try:
        from core.memory.store import _connect
        q = "SELECT fragment_id, content, timestamp FROM memory_fragments WHERE layer='dormant' AND origin='night_thought'"
        args: list = []
        if since_ts is not None:
            q += " AND timestamp > ?"
            args.append(float(since_ts))
        if contains:
            q += " AND content LIKE ?"
            args.append(f"%{contains}%")
        q += " ORDER BY timestamp DESC LIMIT ?"
        args.append(int(limit))
        with _connect() as conn:
            for r in conn.execute(q, args).fetchall():
                out.append({"fragment_id": r["fragment_id"], "content": r["content"], "timestamp": r["timestamp"]})
    except Exception as exc:
        logger.debug("[night_dormant] deep_recall_night failed (non-fatal): %s", exc)
    return out


# -- the 14-night read of D-0400's defeater ---------------------------------------------------------------------------
def uptake_read(rows=None, embed=None, first_thought_fn=None) -> dict:
    """For each drawn seed: cosine of the FIRST inner thought written after the draw to the seed text. Read-only.
    D-0400 defeater: after 14 instrumented nights, cosine below 0.3 on more than 80 percent of mornings = dead read path
    (then option C, never store, is the honest law). first_thought_fn(drawn_ts) -> text, embed(text) -> vec are
    injectable for tests; the defaults read the memory store and use its embedder."""
    rows = rows if rows is not None else _read_log()
    drawn = [r for r in rows if r.get("kind") == "seed_drawn"]
    if embed is None:
        from core.memory.store import _embed as embed
    if first_thought_fn is None:
        def first_thought_fn(ts):
            from core.memory.store import _connect
            with _connect() as conn:
                r = conn.execute("SELECT content FROM memory_fragments WHERE origin='inner_thought' AND timestamp > ? "
                                 "ORDER BY timestamp ASC LIMIT 1", (float(ts),)).fetchone()
            return r["content"] if r else None
    coss = []
    for r in drawn:
        try:
            t = first_thought_fn(r["ts"])
            if not t:
                continue
            a, b = embed(t), embed(r.get("seed_text", ""))
            if a is None or b is None:
                continue
            coss.append(round(float(sum(float(x) * float(y) for x, y in zip(a, b))), 4))
        except Exception:
            continue
    low = [c for c in coss if c < UPTAKE_HOLD_COS]
    out = {"nights_drawn": len(drawn), "scored": len(coss), "cosines": coss,
           "low_share": round(len(low) / len(coss), 3) if coss else None, "verdict": "insufficient", "holds": []}
    if len(drawn) >= UPTAKE_MIN_NIGHTS and coss:
        if len(low) / len(coss) > UPTAKE_HOLD_SHARE:
            out["holds"].append("read_path_dead_cosine_below_0.3_on_over_80pct")
        out["verdict"] = "hold" if out["holds"] else "ok"
    return out

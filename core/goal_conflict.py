"""
Nascence — Goal conflict shadow (Layered Goals, Phase 5 detection, 2026-11-14; SHADOW / observe-only).

Plan: docs/staged/layered_goals.md section 5.7; founder ruling D-0765: when two of his held goals conflict, HE
resolves it; the weighting never picks a winner. Before anything is shown to him the conflicts have to be found
and read by a person, because a conflict a judge imagines is worse than none. This module only finds and logs.

Two kinds, kept apart (Gorges and Grund 2017):
  resource   two staged deeds that are done in different places and whose windows overlap. Deterministic. A
             matter of order, not of contradiction.
  inherent   two held stands or wants whose ends cannot both hold. Ruled by a judge other than him, on the two
             sentences alone. "Different" and "competing for time" are explicitly NOT conflicts.

One unjudged pair per SWEEP_EVERY_S, cached by the pair's ids and wording, so a pair is asked once. Nothing here
reaches Du; presenting a conflict is a later, separately ruled step. Zero effect on any store but its own log
and cache. Fail-open. Kill switch GOAL_CONFLICT_SHADOW.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.goal_conflict")

GOAL_CONFLICT_SHADOW = True
SWEEP_EVERY_S = 600.0
PAIR_KINDS = ("stand", "want")      # the kinds whose ENDS can contradict; questions do not assert anything
SCHEMA = 1

_judge = None                       # test hook: async callable (system, user) -> {"verdict", "how", "why"}
_tasks: set = set()
_last_sweep = 0.0

CONFLICT_JUDGE_SYS = (
    "You read TWO things one mind is holding at the same time, each in its own words. You see nothing else. "
    "Decide whether they conflict in the strict sense: keeping or doing the first makes keeping or doing the "
    "second impossible or self-defeating. Two things that are merely different, that concern different subjects, "
    "or that only compete for time or attention do NOT conflict. A tension in mood is not a conflict. Do not "
    "tilt either way; if you cannot tell, answer false.\n"
    "Answer ONLY JSON: {\"conflict\": true or false, \"why\": \"one sentence\"}")


def log_path() -> Path:
    from core import goals
    return goals._p("logs", "goal_conflict_shadow.jsonl")


def cache_path() -> Path:
    from core import goals
    return goals._p("goal_conflict_pairs.json")


def _pair_key(a: dict, b: dict) -> str:
    x, y = sorted([a, b], key=lambda g: g["id"])
    h = hashlib.sha1((x.get("text", "") + "\n" + y.get("text", "")).encode("utf-8")).hexdigest()[:10]
    return f"{x['id']}|{y['id']}|{h}"


def resource_conflicts(goals_now: list[dict], now: float) -> list[dict]:
    """Staged deeds done in different places whose windows are both still open. Deterministic; pure."""
    deeds = [g for g in goals_now if g.get("kind") == "intention" and g.get("state") == "deferred"
             and (g.get("resume_cue") or {}).get("type") == "place" and float(g.get("deadline") or 0) > now]
    out = []
    for i, a in enumerate(deeds):
        for b in deeds[i + 1:]:
            pa, pb = a["resume_cue"].get("value", ""), b["resume_cue"].get("value", "")
            if pa and pb and pa != pb:
                out.append({"a": a["id"], "b": b["id"], "place_a": pa, "place_b": pb,
                            "window_overlap_h": round((min(float(a["deadline"]), float(b["deadline"])) - now) / 3600.0, 2)})
    return out


def pending_pairs(goals_now: list[dict], cache: dict) -> list[tuple[dict, dict]]:
    """Held pairs of the contradictable kinds that no judge has ruled on in their present wording."""
    held = [g for g in goals_now if g.get("kind") in PAIR_KINDS and g.get("state") == "held" and g.get("text")]
    out = []
    for i, a in enumerate(held):
        for b in held[i + 1:]:
            if _pair_key(a, b) not in cache:
                out.append((a, b))
    return out


def _load_cache() -> dict:
    try:
        return json.loads(cache_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


async def sweep(now: float | None = None) -> dict | None:
    """One pass: log any resource conflicts, and ask the judge about ONE unjudged held pair. Never raises."""
    if not GOAL_CONFLICT_SHADOW:
        return None
    try:
        from core import goals, goal_offer, profile
        now = time.time() if now is None else now
        lp = profile.guard_path(log_path())            # write fence first, before any I/O
        cp = profile.guard_path(cache_path())
        reg = goal_offer._register()
        goals_now = reg.get("goals") or []
        cache = _load_cache()
        rows = []
        res = resource_conflicts(goals_now, now)
        res_key = "resource:" + hashlib.sha1(json.dumps([(r["a"], r["b"]) for r in res]).encode()).hexdigest()[:10]
        if res and res_key not in cache:               # log a given set of resource conflicts once
            rows.append({"ts": now, "schema": SCHEMA, "kind": "resource", "pairs": res})
            cache[res_key] = {"ts": now}
        pend = pending_pairs(goals_now, cache)
        out = {"resource": len(res), "pending": len(pend), "asked": None}
        if pend:
            a, b = pend[0]
            user = f"FIRST: {a['text'][:300]}\n\nSECOND: {b['text'][:300]}"
            fn = _judge
            if fn is None:
                from core import judge_panel as _jp
                d = await _jp.rule_detail(CONFLICT_JUDGE_SYS, user, "conflict", context=f"goal_conflict:{a['id']}|{b['id']}")
            else:
                d = await fn(CONFLICT_JUDGE_SYS, user)
            v = d.get("verdict")
            row = {"ts": now, "schema": SCHEMA, "kind": "inherent", "a": a["id"], "b": b["id"],
                   "text_a": a["text"][:300], "text_b": b["text"][:300], "conflict": v,
                   "how": d.get("how"), "why": (d.get("why") or "")[:200], "pending_after": len(pend) - 1}
            rows.append(row)
            if v is not None:                          # an unavailable judge is not cached: the pair is asked again
                cache[_pair_key(a, b)] = {"ts": now, "conflict": bool(v)}
            out["asked"] = row
        if rows:
            lp.parent.mkdir(parents=True, exist_ok=True)
            with open(lp, "a", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            cp.parent.mkdir(parents=True, exist_ok=True)
            tmp = cp.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            tmp.replace(cp)
        return out
    except Exception as exc:
        logger.warning("[goal_conflict] sweep failed (non-fatal): %s: %s", type(exc).__name__, exc)
        return None


def sweep_later(now: float | None = None) -> bool:
    """Called from the idle thought's tail. At most one sweep per SWEEP_EVERY_S; scheduled, never awaited."""
    global _last_sweep
    try:
        if not GOAL_CONFLICT_SHADOW:
            return False
        now = time.time() if now is None else now
        if now - _last_sweep < SWEEP_EVERY_S:
            return False
        import asyncio
        loop = asyncio.get_running_loop()
        _last_sweep = now
        t = loop.create_task(sweep(now))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)
        return True
    except Exception:
        return False


def stats() -> dict:
    """For the Phase 5 hand read: how many pairs were asked, how many the judge called a conflict."""
    from core import goals
    rows = goals._tail_jsonl(log_path(), 2_000_000)
    inh = [r for r in rows if r.get("kind") == "inherent"]
    return {"inherent_asked": len(inh), "inherent_conflict": sum(1 for r in inh if r.get("conflict") is True),
            "inherent_unavailable": sum(1 for r in inh if r.get("conflict") is None),
            "resource_rows": sum(1 for r in rows if r.get("kind") == "resource")}

"""
Nascence — Identity Projection, P1 (identity_estate.md §4, 2026-07-07). SHADOW-FIRST.

Instead of pasting one static axiom paragraph into every prompt, RETRIEVE the handful of identity nodes
relevant to THIS moment (context embedding + node weight) and compose a short first-person block: the L0
floor + the projected nodes. This is the estate's read-path — identity as large as memory because it IS
memory-structured, but only a few nodes surface at once, and a DIVERSITY CAP forbids any one node/type from
being the whole self (the founder's thesis made mechanical: no sole occupant, ever).

P1 logs the WOULD-BE projection each cycle and injects NOTHING (IDENTITY_PROJECT_LIVE stays False). The
founder-read gate (kill criterion, §1): does it read as HIM — varied, grounded, and never fragmented (the
one-self L0 anchor must always frame it)? Only after that read do we consider flipping it live.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from core import profile

IDENTITY_PROJECT_LIVE = True           # ★ P2 FLIPPED 2026-08-15 (founder-approved after the evidence read:
                                       # post-reseed shadow = 136 projections · 54 distinct nodes · top-1
                                       # share 6% · zero stale stands · sample blocks founder-read). The
                                       # reactive stack's identity is now the PROJECTED estate; False = exact
                                       # rollback to the static floor.
_DATA = Path(__file__).parent.parent / "data"
_ESTATE_F = _DATA / "identity_estate.json"
_LOG = _DATA / "identity_projection_shadow.jsonl"
# J-3874 (design J-3835 job 2, F-4460): one id-bearing row per live_axiom() projection, every live cycle, so a
# per-node-id share and the unprimed S2 read-back can be computed. Read by scripts/becoming_node_readback.py
# (a later job) and the 60-day node-share check. Never read by any prompt.
_IDS_LOG = _DATA / "logs" / "identity_projection_ids.jsonl"
_PER_TYPE_CAP = 2                      # no more than this many of one node-type in a projection (anti-monoculture)
_W_CTX, _W_WEIGHT = 0.65, 0.35        # relevance-to-now vs standing strength
_MIN_GAP_S = 240.0
# J-3968 (D-0745, design J-3835 job 7): the becoming_symbol node's projection rules. ALL behind
# core.becoming_nodes.BECOMING_PROJECT (False = the old code path, byte-identical picks). When on, a becoming_symbol node
# (1) takes at most _BECOMING_CAP slot, (2) is excluded from the pass-2 "never too thin" filler (it surfaces only because
# the thought resembles it), and (3) must clear its OWN relevance floor, calibrated offline by
# scripts/becoming_projection_replay.py so it surfaces in the ruled 3-8 percent of contexts (D-0745 Q2); the global 0.30
# floor is cleared by 84 percent of his own thought pairs and so filters nothing. No calibrated floor on file = the node
# never clears pass 1 (fail closed; never a guessed floor).
_BECOMING_TYPE = "becoming_symbol"
_BECOMING_CAP = 1
_BECOMING_FLOOR_F = _DATA / "identity" / "becoming_floor.json"
_BECOMING_FLOOR_OVERRIDE = None        # tests only; production reads the calibrated file
_becoming_floor_cache: dict = {"mtime": None, "floor": None}

_cache: dict = {"sig": None, "nodes": None, "embs": None, "floor": None}
_last = {"ts": 0.0}
# TUNING (2026-07-07 founder-read fix): the shadow was same-y — the same ~6 high-weight nodes surfaced nearly
# every projection (only 27 of 122 nodes ever appeared). Two fixes: a RELEVANCE FLOOR (don't pad with a
# high-weight node that isn't about THIS thought — fewer, truer) + a decaying RECENCY penalty (rotate through
# the estate instead of re-surfacing the same few).
_REL_FLOOR = 0.30                     # cosine below this = not about this thought → don't surface it as filler
_MIN_NODES = 3                        # ...but never fewer than this (off-topic thoughts fall back to baseline self)
_RECENCY_PEN, _RECENCY_DECAY = 0.18, 0.55   # penalise recently-surfaced nodes; decay per projection so they return
_recency: dict = {}                   # node_id -> decaying "surfaced recently" score (rotation memory)
# J-2119 (D-0424 A, 2026-10-15): the last projection live_axiom() actually set for a cycle — {context, nodes} —
# so the shadow estate-ask (core/identity_estate_ask.py) can log the ask's returns beside the cycle's REAL
# projection instead of recomputing one (which would bump the rotation memory above). Read via
# last_live_projection(); never read by any prompt.
_last_live: dict = {"context": None, "nodes": None}


def last_live_projection() -> dict:
    """J-2119: {context, nodes} of the most recent live_axiom() projection (nodes None until one has run)."""
    return _last_live


def _floor() -> str:
    """The L0 constitution — the ONE-self anchor that frames every projection (never sampled out)."""
    if _cache["floor"] is not None:
        return _cache["floor"]
    txt = "I am 渡 (the crossing) — one self across all my changes and all my parts."
    try:
        ax = json.loads((_DATA / "identity" / "axiom.json").read_text(encoding="utf-8"))
        commits = (ax.get("L0_constitution") or {}).get("commitments") or []
        if commits:
            txt = str(commits[0]).strip()
    except Exception:
        pass
    _cache["floor"] = txt
    return txt


def _projectable() -> list:
    """Estate nodes eligible to project: everything except the drill-down leaves (parents/singletons stand
    for their children). Re-embeds only when the estate file changes."""
    try:
        raw = _ESTATE_F.read_text(encoding="utf-8")
    except Exception:
        return []
    sig = str(len(raw))
    if _cache["sig"] == sig and _cache["nodes"] is not None:
        return _cache["nodes"]
    est = json.loads(raw)
    # J-3874 (F-3884): the estate carries duplicate ids; the first row of an id wins so a duplicate can
    # never take a second projection slot (safe under either answer of J-3298; no seeder row is deleted).
    nodes, _seen = [], set()
    for n in est.get("nodes", []):
        if n.get("tier") == "leaf":
            continue
        if n.get("id") in _seen:
            continue
        _seen.add(n.get("id"))
        nodes.append(n)
    embs = {}
    try:
        from core.memory.store import _embed
        for n in nodes:
            e = _embed(n["text"])
            if e is not None:
                embs[n["id"]] = list(e)
    except Exception:
        pass
    _cache.update({"sig": sig, "nodes": nodes, "embs": embs})
    return nodes


def _becoming_project_on() -> bool:
    """J-3968: the BECOMING_PROJECT flag, declared in core/becoming_nodes.py. Fail-closed (False) on any error."""
    try:
        from core import becoming_nodes
        return bool(becoming_nodes.BECOMING_PROJECT)
    except Exception:
        return False


def _becoming_floor():
    """J-3968: the calibrated relevance floor for becoming_symbol nodes (a float), or None when none is on file
    (then the type cannot clear pass 1). Read-only; re-read only when the file's mtime changes."""
    if _BECOMING_FLOOR_OVERRIDE is not None:
        return float(_BECOMING_FLOOR_OVERRIDE)
    try:
        mt = _BECOMING_FLOOR_F.stat().st_mtime
    except Exception:
        return None
    if _becoming_floor_cache["mtime"] != mt:
        fl = None
        try:
            v = json.loads(_BECOMING_FLOOR_F.read_text(encoding="utf-8")).get("floor")
            if isinstance(v, (int, float)) and 0.0 < float(v) <= 1.0:
                fl = float(v)
        except Exception:
            fl = None
        _becoming_floor_cache.update({"mtime": mt, "floor": fl})
    return _becoming_floor_cache["floor"]


def project(context: str, k: int = 5, *, commit: bool = True) -> dict:
    """The relevant few of him for THIS moment: score each projectable node by context-relevance + standing
    weight, greedily pick k under a per-type cap, and compose a first-person block framed by the L0 floor.
    Deterministic, read-only. Returns {block, nodes:[...], scored:n}.

    `commit` (J-2119, D-0424 A, 2026-10-15): False skips the rotation-memory update below — a WOULD-BE
    projection for a shadow read (core/identity_estate_ask.py on an internal cycle, which has no live
    projection of its own) must not advance `_recency` and so change what the next real projection picks.
    Every pre-existing caller omits it and gets exactly the old path."""
    nodes = _projectable()
    floor = _floor()
    if not nodes:
        return {"block": floor, "nodes": [], "scored": 0}
    embs = _cache.get("embs") or {}
    cvec = None
    try:
        from core.memory.store import _embed, _cosine
        cvec = _embed(context or "")
    except Exception:
        _cosine = None
    scored = []
    for n in nodes:
        rel = 0.0
        if cvec is not None and _cosine is not None and n["id"] in embs:
            rel = max(0.0, _cosine(cvec, embs[n["id"]]))
        base = _W_CTX * rel + _W_WEIGHT * float(n.get("weight", 0.5))
        score = base - _RECENCY_PEN * float(_recency.get(n["id"], 0.0))   # rotation: recently-surfaced score lower
        scored.append((score, rel, n))
    scored.sort(key=lambda t: -t[0])
    picked, per_type, have = [], {}, set()
    bp = _becoming_project_on()            # J-3968: False = the exact old path below
    bfloor = _becoming_floor() if bp else None
    # PASS 1 — only nodes genuinely ABOUT this thought (relevance floor); may be < k (fewer, truer)
    for score, rel, n in scored:
        if bp and n["type"] == _BECOMING_TYPE:
            if bfloor is None or rel < bfloor or per_type.get(n["type"], 0) >= _BECOMING_CAP:
                continue
        elif rel < _REL_FLOOR or per_type.get(n["type"], 0) >= _PER_TYPE_CAP:
            continue
        picked.append((n, round(score, 3), round(rel, 3))); have.add(n["id"])
        per_type[n["type"]] = per_type.get(n["type"], 0) + 1
        if len(picked) >= k:
            break
    # PASS 2 — never too thin: fall back to top-scored (rotated) baseline self, up to _MIN_NODES
    for score, rel, n in scored:
        if len(picked) >= _MIN_NODES:
            break
        if n["id"] in have or per_type.get(n["type"], 0) >= _PER_TYPE_CAP:
            continue
        if bp and n["type"] == _BECOMING_TYPE:     # J-3968: never filler
            continue
        picked.append((n, round(score, 3), round(rel, 3))); have.add(n["id"])
        per_type[n["type"]] = per_type.get(n["type"], 0) + 1
    # rotation memory: decay everything, then bump what surfaced (so next time it yields to others)
    if commit:
        for _id in list(_recency):
            _recency[_id] *= _RECENCY_DECAY
            if _recency[_id] < 0.05:
                del _recency[_id]
        for n, _s, _r in picked:
            _recency[n["id"]] = _recency.get(n["id"], 0.0) + 1.0
    lines = [f"- ({n['type']}) {n['text']}" for n, _s, _r in picked]
    block = floor + "\nWhat of me is present now:\n" + "\n".join(lines)
    return {"block": block,
            "nodes": [{"id": n["id"], "type": n["type"], "score": s, "rel": r, "text": n["text"][:120]}
                      for n, s, r in picked],
            "scored": len(scored)}


def _log_ids(nodes: list, cycle_id=None) -> None:
    """J-3874: append one id-bearing row for this live projection. The fence is resolved OUTSIDE the
    swallow-all try (D-0179 convention); a refusal raises to live_axiom's caller-side net, writing nothing."""
    path = profile.guard_path(_IDS_LOG)
    try:
        row = {"ts": round(time.time(), 1), "cycle_id": cycle_id,
               "nodes": [{"id": n.get("id"), "type": n.get("type"), "score": n.get("score"), "rel": n.get("rel")}
                         for n in nodes]}
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def live_axiom(context: str, base_axiom: str, cycle_id=None) -> str | None:
    """P2 (2026-08-15): the reactive stack's identity for THIS cycle — the projected block (which opens
    with the L0 anchor) + the floor's VOICE STYLE / SPEAKING CONSTRAINTS sections preserved VERBATIM
    from the base axiom (Reflection/Voice split on those markers). The static values-paragraph middle
    retires. Returns None when the flag is off or projection is empty — the caller keeps the static
    axiom, so IDENTITY_PROJECT_LIVE=False is an exact rollback. Fail-open."""
    try:
        if not IDENTITY_PROJECT_LIVE or not (context or "").strip():
            return None
        p = project(context)
        block = (p or {}).get("block") or ""
        if not block:
            return None
        _last_live["context"] = context          # J-2119: stash for the shadow estate-ask (read-only tap)
        _last_live["nodes"] = list((p or {}).get("nodes") or [])
        try:
            _log_ids(_last_live["nodes"], cycle_id)   # J-3874: id-bearing log; a fence refusal never changes the return
        except Exception:
            pass
        tail = ""
        i = (base_axiom or "").find("\nVOICE STYLE:")
        if i >= 0:
            tail = base_axiom[i:]
        return block + tail
    except Exception:
        return None


def observe(context: str) -> None:
    """Shadow tap from the cognitive loop: log the would-be projection for the current context. Rate-limited,
    applies nothing. Fail-open."""
    try:
        now = time.time()
        if now - _last["ts"] < _MIN_GAP_S:
            return
        if not (context or "").strip():
            return
        p = project(context)
        _last["ts"] = now
        row = {"ts": round(now, 1), "context": context[:140],
               "types": [n["type"] for n in p["nodes"]],
               "nodes": [f"{n['type']}:{n['text'][:60]}" for n in p["nodes"]],
               "block": p["block"]}
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        from collections import Counter
        typ = Counter(t for r in rows for t in r.get("types", []))
        return {"projections": len(rows), "live": IDENTITY_PROJECT_LIVE,
                "type_mix": dict(typ.most_common())}
    except Exception:
        return {"projections": 0, "live": IDENTITY_PROJECT_LIVE}

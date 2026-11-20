"""
Spatial sketch store -- I-0129 rung 1 INSTRUMENT (J-2661, F-3407/F-3408), SHADOW ONLY.

What this is: a deterministic per-place store of what the rendered spatial sense (core.spatial.render()) has
said, plus an aggregator that turns it back into a map and scores that map against the authored layout.
It exists because J-2628/J-2647 showed (F-3381, F-3382, F-3407, F-3408) that the rendered lines DO carry the
map (ideal decoder 0.2-0.8 m) but that the hot 9B model cannot hold it in its context: one-shot reading is
at chance, a running sketch in the prompt drifts and mirrors, and it turns egocentric relations into world
bearings correctly only ~20 percent of the time. So the pose arithmetic and the accumulation are CODE:

  record()     one render -> one row: stop pose (from the layout standpoint), and per clause the
               (object label, sector word, distance word) the deterministic clause parser reads off it.
               Clauses the parser cannot label are LOGGED as `unlabeled` (not guessed): a later job can
               decide from real counts whether a model extractor is ever needed (F-3408: it is a copier at
               best, and a regex recovers the renderer's fixed vocabulary exactly, so the default and only
               built extractor is the regex). `extractor=` is the seam for that optional alternative.
  estimate()   the ideal decoder's grid search (0.1 m): for each object, the max-consistent region's
               centroid given every (pose, sector, band) observation of it.
  score()      raw RMSE and pairwise E-W / N-S sign accuracy against the authored coordinates.
  shadow log   after each record() that adds a NEW unique observation, one score row per place.

HARD LIMITS (D-0434, J-2485): nothing here is ever rendered into Du's prompt, no reach/step consequence
reads it, and there is no readout path to Du: the only readers are this module's own functions and offline
scripts. The flag is OFF by default; flag off = record() returns immediately and writes nothing. It does not
decide whether render('study') goes on Du's prompt path (J-2485, founder call): it fills from wherever
render() / spatial.shadow() are really called, and the shadow rows say how often that is.

Files (both under data/, write-fenced with profile.guard_path like the other spatial shadows):
    data/spatial_sketch.jsonl          one row per recorded render (observations + unlabeled clauses)
    data/spatial_sketch_shadow.jsonl   one score row per place per new unique observation
RESTART-GATED: the flag is read from this module's constant; a running process picks the code up at restart.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from pathlib import Path

from core import profile
from core import shadow_log

_DATA = Path(__file__).parent.parent / "data"
_STORE = _DATA / "spatial_sketch.jsonl"
_SHADOW = _DATA / "spatial_sketch_shadow.jsonl"
_LOCK = threading.Lock()

SKETCH_SHADOW_LIVE = False       # J-2661: OFF. record() is a no-op until this is flipped (restart-gated).
GRID_M = 0.1                     # the ideal decoder's grid pitch
MOVING = ("waterline",)          # features whose authored position moves with the tide: never scored
_SEP = " — "                # the renderer's clause separator (em dash)

# ── the fixed vocabulary (J-2628 VOCAB, moved into core): clause regex -> object label -> authored feature ──
VOCAB = {
    "study": [("the fire", r"^the (fire|embers) ", "fireplace"), ("the window", r"window", "window"),
              ("the desk", r"desk", "desk"), ("the garden door", r"garden door", "door_garden"),
              ("the bed", r"\bbed\b", "bed"), ("the shelf", r"the shelf", "shelf_east")],
    "garden": [("the letterbox", r"letterbox|the gate", "letterbox"), ("the raised bed", r"raised bed", "raised_bed"),
               ("the garden wall", r"garden wall", "garden_wall"), ("the harakeke", r"harakeke", "harakeke"),
               ("the fence", r"fence", "fence"), ("the old tree", r"old tree", "tree"),
               ("the garden door", r"garden door|doorstep", "door_study")],
    "shore": [("the tideline", r"tideline|^the tide is", "waterline"), ("the driftwood", r"driftwood", "driftwood_tangle"),
              ("the path home", r"path home", "path_foot"), ("the rock pools", r"rock-pool|pools", "rock_pools")],
    "wood": [("the undergrowth", r"undergrowth", "undergrowth"), ("the old oak", r"oak", "the_old_oak"),
             ("the fallen wood", r"fallen wood", "deadfall"), ("the gap to the sea", r"gap down to the sea", "sea_gap")],
}
SECTORS = ["to your right", "to your left", "behind you", "ahead"]
BANDS = [("right beside you", 0.0, 1.0), ("across the room", 2.0, 3.5), ("at the far side", 3.5, 99),
         ("a little way off", 2.0, 3.5), ("far off", 3.5, 99), ("near", 1.0, 2.0)]


# ── extraction (deterministic regex path; the default and the only built extractor) ─────────────────────
def sector_of(pose: dict, pt) -> str:
    """The renderer's own sector wedge for a point seen from `pose` (x, y, facing_deg): +-45 ahead, etc."""
    dx, dy = pt[0] - pose["x"], pt[1] - pose["y"]
    r = (math.degrees(math.atan2(dx, dy)) % 360 - pose["facing_deg"]) % 360
    r = r - 360 if r > 180 else r
    if abs(r) <= 45:
        return "ahead"
    if 45 < r <= 135:
        return "to your right"
    if -135 <= r < -45:
        return "to your left"
    return "behind you"


def observe(place: str, clause: str):
    """(label, sector|None, distance_word|None) for one rendered clause, or None if no vocab label matches."""
    label = None
    for lab, rx, _f in VOCAB.get(place, []):
        if re.search(rx, clause if place == "shore" else clause.split(_SEP)[0]):
            label = lab
            break
    if not label:
        return None
    head = clause.split(_SEP)[0] if not clause.startswith("the tide is") else clause.split(_SEP, 1)[-1]
    sec = next((s for s in SECTORS if re.search(r"\b" + s + r"\b", head)), None)
    word = next((w for w, _lo, _hi in BANDS if re.search(r"\b" + w + r"\b", head)), None)
    return label, sec, word


def band_of(word: str | None):
    return next(((lo, hi) for w, lo, hi in BANDS if w == word), None)


def extract_regex(place: str, clauses: list) -> dict:
    """One render's clauses -> {"obs": [[label, sector, word]], "no_geom": [label], "unlabeled": [clause]}.
    `no_geom`: the clause named a known object but gave neither a sector nor a distance word (it cannot
    constrain a position); `unlabeled`: no vocab label matched at all (weather, sounds, the cat's own
    business...). Both are kept so a later job can count them."""
    obs, no_geom, unlabeled = [], [], []
    for c in clauses or []:
        o = observe(place, c)
        if o is None:
            unlabeled.append(str(c)[:200])
        elif o[1] or o[2]:
            obs.append([o[0], o[1], o[2]])
        else:
            no_geom.append(o[0])
    return {"obs": obs, "no_geom": no_geom, "unlabeled": unlabeled}


# ── the store ───────────────────────────────────────────────────────────────────────────────────────────
def _key(r):
    return (r[0], r[1], r[2])


def _pose_key(p: dict):
    return (round(p["x"], 2), round(p["y"], 2), round(p["facing_deg"], 1))


def _unique_set(rows: list, room: str) -> set:
    return {(_pose_key(r["pose"]), *_key(o)) for r in rows if r.get("room") == room for o in r.get("obs", [])}


_CACHE: dict = {}


def _cache_for(path: Path) -> dict:
    """Per-store working set, loaded from disk once per process (so record() stays O(new) as the store grows):
    unique (pose, label, sector, word) tuples, the deduped rows the scorer reads, and a render count."""
    k = str(path)
    if k not in _CACHE:
        c = {"uniq": {}, "rows": {}, "renders": {}}
        for r in shadow_log.read_rows(path):
            room = r.get("room")
            seen = c["uniq"].setdefault(room, set())
            fresh = [o for o in r.get("obs", []) if (_pose_key(r["pose"]), *_key(o)) not in seen]
            for o in fresh:
                seen.add((_pose_key(r["pose"]), *_key(o)))
            if fresh:
                c["rows"].setdefault(room, []).append({"room": room, "pose": r["pose"], "obs": fresh})
            c["renders"][room] = c["renders"].get(room, 0) + 1
        _CACHE[k] = c
    return _CACHE[k]


def read_rows(room: str | None = None, path: Path | None = None) -> list:
    """Every stored render row (oldest first), optionally for one room. Reads `_STORE` at call time."""
    rows = shadow_log.read_rows(path or _STORE)
    return [r for r in rows if room is None or r.get("room") == room]


def record(room: str, standpoint: str | None, pose: dict | None, clauses: list, ts: float | None = None,
           lay: dict | None = None, extractor=None, store: Path | None = None, shadow: Path | None = None,
           score_it: bool = True) -> dict | None:
    """Append one render to the sketch store; if it added a new unique observation, append a score row.

    Flag off (default) -> returns None and touches nothing. `pose` = {"x","y","facing_deg"} of the layout
    standpoint the render was made from. Paths are resolved through profile.guard_path BEFORE the fail-open
    try, so a non-live process is refused with NonLiveWriteError rather than writing; callers on the live
    path (core.spatial hooks) swallow that, exactly as spatial.shadow() does. Returns the row written."""
    if not SKETCH_SHADOW_LIVE:
        return None
    if room not in VOCAB or not pose or not clauses:
        return None
    store_path = profile.guard_path(store or _STORE)
    shadow_path = profile.guard_path(shadow or _SHADOW)
    try:
        ex = (extractor or extract_regex)(room, clauses)
        row = {"ts": round(ts if ts is not None else time.time(), 1), "room": room, "standpoint": standpoint,
               "pose": {"x": float(pose["x"]), "y": float(pose["y"]), "facing_deg": float(pose["facing_deg"])},
               "n_clauses": len(clauses), "obs": ex["obs"], "no_geom": ex["no_geom"],
               "unlabeled": ex["unlabeled"], "extractor": "regex" if extractor is None else getattr(extractor, "__name__", "custom")}
        with _LOCK:
            c = _cache_for(store_path)
            seen = c["uniq"].setdefault(room, set())
            fresh = [o for o in row["obs"] if (_pose_key(row["pose"]), *_key(o)) not in seen]
            for o in fresh:
                seen.add((_pose_key(row["pose"]), *_key(o)))
            if fresh:     # the deduped working set the scorer reads (one pseudo-row per render with news)
                c["rows"].setdefault(room, []).append({"room": room, "pose": row["pose"], "obs": fresh})
            shadow_log.append(store_path, row)
            new_unique = len(fresh)
            work = list(c["rows"].get(room, []))
        if score_it and new_unique and lay is not None:
            t0 = time.time()
            sc = score_room(room, work, lay)
            if sc:
                sc.update({"ts": row["ts"], "new_unique": new_unique,
                           "n_renders": c["renders"].get(room, 0) + 1,
                           "score_ms": round((time.time() - t0) * 1000)})
                with _LOCK:
                    shadow_log.append(shadow_path, sc)
        with _LOCK:
            c["renders"][room] = c["renders"].get(room, 0) + 1
        return row
    except Exception:
        return None


# ── the aggregator: the ideal decoder's 0.1 m grid search ───────────────────────────────────────────────
def collect(rows: list, room: str, dedup: bool = False) -> dict:
    """label -> [(pose, sector|None, (lo, hi)|None)] from stored rows. dedup=True keeps each distinct
    (pose, sector, word) once per label (repeat renders at the same stop are not independent evidence)."""
    by, seen = {}, set()
    for r in rows:
        if r.get("room") != room:
            continue
        for lab, sec, word in r.get("obs", []):
            if not (sec or word):
                continue
            k = (lab, _pose_key(r["pose"]), sec, word)
            if dedup and k in seen:
                continue
            seen.add(k)
            by.setdefault(lab, []).append((r["pose"], sec, band_of(word)))
    return by


def default_bounds(lay: dict, rows: list | None = None, margin: float = 1.0):
    """Search box from the layout alone (feature + standpoint positions) +- margin: needs no truth peek."""
    pts = [f["pos"] for f in (lay.get("features") or {}).values() if isinstance(f, dict) and f.get("pos")]
    pts += [s["pos"] for s in (lay.get("standpoints") or {}).values() if isinstance(s, dict) and s.get("pos")]
    pts += [(r["pose"]["x"], r["pose"]["y"]) for r in (rows or [])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin


def estimate(rows: list, room: str, bounds, dedup: bool = False, labels=None) -> tuple[dict, dict]:
    """(pred, consistency): per object, the centroid of the grid points satisfying the most observations."""
    x0, x1, y0, y1 = bounds
    grid = [(x0 + GRID_M * i, y0 + GRID_M * j) for i in range(int((x1 - x0) / GRID_M) + 1)
            for j in range(int((y1 - y0) / GRID_M) + 1)]
    pred, cons = {}, {}
    for lab, ob in collect(rows, room, dedup).items():
        if labels is not None and lab not in labels:
            continue

        def sc(pt):
            k = 0
            for pose, sec, band in ob:
                ok = (sec is None or sector_of(pose, pt) == sec)
                if band:
                    d = math.dist(pt, (pose["x"], pose["y"]))
                    ok = ok and band[0] <= d < band[1] + 1e-9
                k += ok
            return k
        scores = [sc(p) for p in grid]
        best = max(scores)
        pts = [p for p, s in zip(grid, scores) if s == best]
        pred[lab] = [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]
        cons[lab] = {"obs": len(ob), "best_consistent": best, "feasible_area_m2": round(len(pts) * GRID_M * GRID_M, 2)}
    return pred, cons


# ── scoring against the authored layout ─────────────────────────────────────────────────────────────────
def truth_of(room: str, lay: dict, include_moving: bool = False) -> dict:
    """label -> [x, y] authored coordinates (read from the layout, which is ground truth)."""
    from core import spatial as _sp
    out = {}
    for label, _rx, feat in VOCAB.get(room, []):
        if feat in MOVING and not include_moving:
            continue
        pos = _sp._waterline_pos(lay) if feat == "waterline" else _sp._pos_of(lay, feat)
        if pos:
            out[label] = [round(pos[0], 2), round(pos[1], 2)]
    return out


def _pairwise(P, T, sep=0.5):
    ok = tot = 0
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            for ax in (0, 1):
                dt = T[j][ax] - T[i][ax]
                if abs(dt) < sep:
                    continue
                tot += 1
                ok += (P[j][ax] - P[i][ax]) * dt > 0
    return ok, tot


def score(pred: dict, truth: dict) -> dict | None:
    """Raw RMSE (m) and pairwise E-W/N-S sign accuracy (pairs separated >= 0.5 m on that axis)."""
    names = [n for n in truth if n in pred]
    if not names:
        return None
    P, T = [pred[n] for n in names], [truth[n] for n in names]
    rmse = math.sqrt(sum(math.dist(p, t) ** 2 for p, t in zip(P, T)) / len(P))
    ok, tot = _pairwise(P, T)
    return {"n_objects": len(names), "of": len(truth), "raw_rmse": round(rmse, 2),
            "pair_acc": round(ok / tot, 3) if tot else None, "pairs": tot,
            "per_object_err": {n: round(math.dist(p, t), 2) for n, p, t in zip(names, P, T)}}


def score_room(room: str, rows: list, lay: dict, dedup: bool = True, bounds=None, include_moving: bool = False):
    """Estimate every observed object from `rows` and score against the layout. None if nothing observed."""
    truth = truth_of(room, lay, include_moving=include_moving)
    pred, cons = estimate(rows, room, bounds or default_bounds(lay, rows), dedup=dedup, labels=set(truth))
    sc = score(pred, truth)
    if not sc:
        return None
    sc.update({"room": room, "dedup": dedup, "n_unique_obs": sum(len(v) for v in collect(rows, room, True).values()),
               "est": {k: [round(v[0], 2), round(v[1], 2)] for k, v in pred.items()},
               "feasible_area_m2": {k: v["feasible_area_m2"] for k, v in cons.items()}})
    return sc


# ── read side (offline; never reaches Du) ───────────────────────────────────────────────────────────────
def status(path: Path | None = None, shadow: Path | None = None) -> dict:
    """Fill rate and last score per room: rows, unique observations, unlabeled-clause counts, last score row."""
    rows = shadow_log.read_rows(path or _STORE)
    out = {"rows": len(rows), "rooms": {}}
    for room in sorted({r.get("room") for r in rows}):
        rr = [r for r in rows if r.get("room") == room]
        un = {}
        for r in rr:
            for c in r.get("unlabeled", []):
                un[c] = un.get(c, 0) + 1
        out["rooms"][room] = {"renders": len(rr), "first_ts": rr[0].get("ts"), "last_ts": rr[-1].get("ts"),
                              "standpoints": sorted({r.get("standpoint") for r in rr if r.get("standpoint")}),
                              "unique_obs": len(_unique_set(rr, room)),
                              "unlabeled_clauses": sum(un.values()), "unlabeled_distinct": len(un),
                              "top_unlabeled": sorted(un.items(), key=lambda kv: -kv[1])[:5]}
    sh = shadow_log.read_rows(shadow or _SHADOW)
    out["shadow_rows"] = len(sh)
    out["last_score"] = {r["room"]: {k: r.get(k) for k in ("ts", "raw_rmse", "pair_acc", "n_objects", "n_unique_obs")}
                         for r in sh if r.get("room")} if sh else {}
    return out

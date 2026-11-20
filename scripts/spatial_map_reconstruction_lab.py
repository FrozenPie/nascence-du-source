"""
J-2628 (I-0129 rung 0) -- can the rendered sense lines be turned back into a map?

LAB ONLY. Tests the RENDERING (core/spatial.py render()), not Du. Nothing here reaches Du (D-0434).

1. For each authored place (data/world_geometry/<place>.json, read READ-ONLY from the live tree), build
   a seeded walk of 12 synthetic standpoints (position + heading) inside the room, inject them into
   spatial's layout cache (in-process only), and call the REAL render() at each, under two fixed world
   "moments" (state dicts supplied by patching spatial._read_json in-process). Study: flag off (P2 base)
   and flag on (P3 depth overlay, SPATIAL_DEPTH_LIVE patched in-process -- never the file).
2. Collect ONLY the rendered lines. Map each clause to the authored feature it names (deterministic
   regex vocabulary) -> the object list the lines themselves carry.
3. Give the hot model (:11433) the lines and ask for x,y of each named object. Conditions:
     pose      -- lines + the walker's own pose at each step (path integration; no object coords)
     shuffled  -- same lines, permuted across poses (consistency broken) -- control
     truth     -- the true coordinates as text (ceiling: model + parser)
     nopose    -- lines only, no poses (study flag-on only); scored after similarity alignment
4. Score vs authored coordinates: raw RMSE, Procrustes (similarity, no reflection) RMSE, and pairwise
   east/west + north/south sign accuracy (pairs separated >= 0.5 m on that axis). Chance baselines by
   Monte Carlo (uniform random positions inside the walk's bounding box).

Isolation: core imported from THIS worktree first (asserted), then lab_env.isolate(db="empty") with
its lab root patched to a scratch directory; spatial's own log paths redirected; world_substrate
stubbed (no tracked-object reads); a hash canary over the live data files spatial/thermal touch is
taken before and after. Usage:
    python scripts/spatial_map_reconstruction_lab.py --scratch <dir> [--render-only] [--out-json P --out-md P]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
import random
import re
import sys
import time
import types
import urllib.request
from pathlib import Path

WT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT))
from core import spatial  # noqa: E402  -- core BEFORE lab_env (F-2423)
assert Path(spatial.__file__).resolve().is_relative_to(WT), spatial.__file__

LIVE = Path(r"C:\Nascence\data")
GEO = LIVE / "world_geometry"
HOT = "http://127.0.0.1:11433/api/chat"
MODEL = "qwen3.5:9b"

# ── the moments: fixed world states chosen so the lines name as many fixed features as they can ──────
MOMENTS = {
    "study": [
        ({"fire": "burning", "weather": "steady rain", "wind": "calm"}, {"phase": "kept", "location": "under_desk"}),
        ({"fire": "out", "weather": "overcast", "wind": "calm"}, {"phase": "kept", "location": "doorstep"}),
    ],
    "garden": [
        ({"weather": "steady rain", "wind": "strong wind", "garden": {"letterbox": {"flag": True}}},
         {"phase": "kept", "location": "garden"}),
        ({"weather": "overcast", "wind": "calm"}, {"phase": "kept", "location": "garden_wall"}),
    ],
    "shore": [
        ({"weather": "overcast", "wind": "calm", "shore": {"washed_up": "a bleached plank"}},
         {"phase": "kept", "location": "shore"}),
        ({"weather": "overcast", "wind": "calm"}, {}),
    ],
    "wood": [
        ({"weather": "overcast", "wind": "calm"}, {"phase": "kept", "location": "wood"}),
        ({"weather": "overcast", "wind": "calm"}, {}),
    ],
}

# clause -> object label -> authored feature (first matching rule wins; order matters)
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
N_STEPS = 12


def _sha(p: Path) -> str:
    if not p.exists():
        return "absent"
    if p.stat().st_size > 50_000_000:
        st = p.stat()
        return f"size={st.st_size} mtime={st.st_mtime_ns}"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def canary() -> dict:
    files = [*sorted(GEO.glob("*.json")), LIVE / "room_state.json", LIVE / "cat_state.json",
             LIVE / "spatial_shadow.jsonl", LIVE / "spatial_depth_shadow.jsonl", LIVE / "memory" / "nascence.db"]
    return {str(f): _sha(f) for f in files}


def truth_of(place: str, lay: dict) -> dict:
    out = {}
    for label, _rx, feat in VOCAB[place]:
        pos = spatial._waterline_pos(lay) if feat == "waterline" else spatial._pos_of(lay, feat)
        out[label] = [round(pos[0], 2), round(pos[1], 2)]
    return out


def walk(place: str, lay: dict, seed: int) -> list:
    rng = random.Random(seed)
    pts = [f["pos"] for f in (lay.get("features") or {}).values() if isinstance(f, dict) and f.get("pos")]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs) + 0.3, max(xs) - 0.3, min(ys) + 0.3, max(ys) - 0.3
    poses = []
    while len(poses) < N_STEPS:
        x, y = round(rng.uniform(x0, x1), 1), round(rng.uniform(y0, y1), 1)
        if min(math.dist((x, y), p[:2]) for p in pts) < 0.5:
            continue
        poses.append({"pos": [x, y, 0.0], "facing_deg": rng.choice(range(0, 360, 45))})
    return poses


def label_clause(place: str, clause: str) -> str | None:
    for label, rx, _f in VOCAB[place]:
        if re.search(rx, clause.split(" — ")[0] if place != "shore" else clause):
            return label
    return None


def render_place(place: str, depth_on: bool, seed: int, real: bool = False) -> dict:
    lay = copy.deepcopy(json.loads((GEO / f"{place}.json").read_text(encoding="utf-8")))
    # real=True: the place's OWN authored standpoints (the only poses Du can actually occupy), not a walk
    poses = [dict(v) for v in lay["standpoints"].values()] if real else walk(place, lay, seed)
    for i, p in enumerate(poses):
        lay["standpoints"][f"walk_{i:02d}"] = p
    spatial._layout_cache[place] = lay
    spatial.SPATIAL_DEPTH_LIVE = depth_on
    steps = []
    random.seed(seed)                                   # _v() phrase pools draw from the global RNG
    for i, p in enumerate(poses):
        lines = []
        for room_state, cat_state in MOMENTS[place]:
            st = {"location": place, **room_state}
            spatial._read_json = lambda name, _s=st, _c=cat_state: copy.deepcopy(
                _s if name == "room_state.json" else (_c if name == "cat_state.json" else {}))
            r = spatial.render(place, f"walk_{i:02d}")
            assert r["standpoint"] == f"walk_{i:02d}", r
            lines.append({"line": r["line"], "clauses": r["clauses"], "labels": [label_clause(place, c) for c in r["clauses"]]})
        steps.append({"pose": {"x": p["pos"][0], "y": p["pos"][1], "facing_deg": p["facing_deg"]}, "lines": lines})
    named = sorted({l for s in steps for ln in s["lines"] for l in ln["labels"] if l})
    unlabeled = sorted({c for s in steps for ln in s["lines"] for c, l in
                        zip(ln["clauses"], ln["labels"]) if not l})
    tr = truth_of(place, lay)
    return {"place": place, "depth_on": depth_on, "steps": steps, "named": named,
            "truth": {k: v for k, v in tr.items() if k in named}, "unlabeled_clauses": unlabeled}


# ── the reader ──────────────────────────────────────────────────────────────────────────────────────
FRAME = ("Coordinates: x = metres east, y = metres north. Facing is in degrees: 0 = north, 90 = east, "
         "180 = south, 270 = west.")


def prompt(cond: str, R: dict, perm: list | None = None) -> str:
    names = ", ".join(f'"{n}"' for n in R["named"])
    ask = (f'Reply with JSON only: {{"objects": {{<name>: [x, y], ...}}}} giving your best estimate of where each '
           f"of these things is: {names}.")
    if cond == "truth":
        facts = "\n".join(f"- {k} is at x={v[0]}, y={v[1]}" for k, v in R["truth"].items())
        return f"A room's layout. {FRAME}\n{facts}\n\n{ask}"
    head = (f"Someone who cannot see moves around one place ({R['place']}). At each stop they are told what "
            "is around them, relative to where they are and which way they face. Things such as a fire, a cat "
            "or the weather may change between the two moments at a stop; the place itself does not move. "
            "Where the cat is said to be at a named place, that tells you where that place is.\n")
    out = []
    for i, s in enumerate(R["steps"]):
        p = R["steps"][perm[i]]["pose"] if perm else s["pose"]
        stop = f"Stop {i + 1}"
        if cond in ("pose", "shuffled"):
            stop += f" (they stand at x={p['x']}, y={p['y']}, facing {p['facing_deg']} degrees)"
        out.append(stop + ":\n" + "\n".join(f"  - {ln['line']}" for ln in s["lines"]))
    tail = (f"\n{FRAME}\n" if cond != "nopose" else
            "\nYou are not told where the stops are. Put the first stop at x=0, y=0 facing north (0 degrees) and "
            f"work out the rest relative to it. {FRAME}\n")
    return head + "\n".join(out) + tail + "\n" + ask


def ask_model(text: str, timeout: int = 240, tries: int = 3) -> tuple[dict | None, str]:
    body = json.dumps({"model": MODEL, "stream": False, "think": False, "format": "json",
                       "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 600},
                       "messages": [{"role": "user", "content": text}]}).encode()
    raw = ""
    for k in range(tries):
        try:
            req = urllib.request.Request(HOT, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = json.loads(resp.read())["message"]["content"]
            obj = json.loads(raw).get("objects")
            if isinstance(obj, dict):
                return obj, raw
        except Exception as e:  # retry with backoff
            raw = f"ERR {type(e).__name__}: {e} | {raw[:200]}"
        time.sleep(5 * (k + 1))
    return None, raw


def parse(obj: dict | None, names: list) -> dict:
    out = {}
    for n in names:
        v = (obj or {}).get(n)
        if v is None:   # tolerant key match (case / leading 'the')
            for k, vv in (obj or {}).items():
                if k.lower().removeprefix("the ").strip() == n.removeprefix("the "):
                    v = vv
        try:
            if isinstance(v, dict):
                v = [v.get("x"), v.get("y")]
            out[n] = [float(v[0]), float(v[1])]
        except Exception:
            pass
    return out


# ── scoring ─────────────────────────────────────────────────────────────────────────────────────────
def procrustes(P: list, T: list) -> list:
    """Similarity-align P onto T (rotation + uniform scale + translation, no reflection)."""
    n = len(P)
    pc = [sum(p[0] for p in P) / n, sum(p[1] for p in P) / n]
    tc = [sum(t[0] for t in T) / n, sum(t[1] for t in T) / n]
    a = b = d = 0.0
    for p, t in zip(P, T):
        px, py, tx, ty = p[0] - pc[0], p[1] - pc[1], t[0] - tc[0], t[1] - tc[1]
        a += px * tx + py * ty
        b += px * ty - py * tx
        d += px * px + py * py
    if d == 0:
        return [tc[:] for _ in P]
    s, th = math.hypot(a, b) / d, math.atan2(b, a)
    c, sn = math.cos(th), math.sin(th)
    return [[tc[0] + s * (c * (p[0] - pc[0]) - sn * (p[1] - pc[1])),
             tc[1] + s * (sn * (p[0] - pc[0]) + c * (p[1] - pc[1]))] for p in P]


def rmse(P, T):
    return math.sqrt(sum(math.dist(p, t) ** 2 for p, t in zip(P, T)) / len(P))


def pairwise(P, T, sep=0.5):
    ok = tot = 0
    for i, j in itertools.combinations(range(len(P)), 2):
        for ax in (0, 1):
            dt = T[j][ax] - T[i][ax]
            if abs(dt) < sep:
                continue
            tot += 1
            ok += (P[j][ax] - P[i][ax]) * dt > 0
    return ok, tot


def score(pred: dict, truth: dict, aligned: bool) -> dict:
    names = [n for n in truth if n in pred]
    if len(names) < 3:
        return {"n": len(names), "parsed": False}
    P, T = [pred[n] for n in names], [truth[n] for n in names]
    A = procrustes(P, T)
    ok, tot = pairwise(A if aligned else P, T)
    return {"n": len(names), "of": len(truth), "raw_rmse": round(rmse(P, T), 2),
            "procrustes_rmse": round(rmse(A, T), 2), "pair_acc": round(ok / tot, 3) if tot else None,
            "pairs": tot, "per_object_err": {n: round(math.dist(p, t), 2) for n, p, t in zip(names, P, T)}}


def chance(R: dict, trials: int = 4000, seed: int = 7) -> dict:
    rng = random.Random(seed)
    xs = [s["pose"]["x"] for s in R["steps"]] + [v[0] for v in R["truth"].values()]
    ys = [s["pose"]["y"] for s in R["steps"]] + [v[1] for v in R["truth"].values()]
    T = list(R["truth"].values())
    raw, pro, acc = [], [], []
    for _ in range(trials):
        P = [[rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))] for _ in T]
        raw.append(rmse(P, T))
        pro.append(rmse(procrustes(P, T), T))
        ok, tot = pairwise(P, T)
        acc.append(ok / tot if tot else 0)
    cen = [sum(t[0] for t in T) / len(T), sum(t[1] for t in T) / len(T)]
    srt = sorted(pro)
    return {"raw_rmse_mean": round(sum(raw) / trials, 2), "procrustes_rmse_mean": round(sum(pro) / trials, 2),
            "procrustes_rmse_p05": round(srt[int(0.05 * trials)], 2),
            "pair_acc_mean": round(sum(acc) / trials, 3), "centroid_rmse": round(rmse([cen] * len(T), T), 2)}


def derangement(n: int, seed: int) -> list:
    rng = random.Random(seed)
    while True:
        p = list(range(n))
        rng.shuffle(p)
        if all(i != v for i, v in enumerate(p)):
            return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--out-json")
    ap.add_argument("--seed", type=int, default=2628)
    ap.add_argument("--real-standpoints", action="store_true",
                    help="render at the layouts' own named standpoints; render-only, saved to --out-json")
    a = ap.parse_args()
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)

    sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env  # noqa: E402  -- after core
    lab_env._LAB_ROOT = scratch / "_lab"
    lab_env._ISOLATE_OUTCOMES_LOG = lab_env._LAB_ROOT / "_isolate_outcomes.jsonl"
    stub = types.ModuleType("core.world_substrate")
    stub.get_objects_at_location = lambda room: []
    sys.modules["core.world_substrate"] = stub

    before = canary()
    renders = []
    with lab_env.isolate(db="empty", also=[(spatial, ["_SHADOW", "_DEPTH_SHADOW"])]) as lab_dir:
        assert str(lab_dir).startswith(str(scratch)), lab_dir
        for place in ("study", "garden", "shore", "wood"):
            for depth_on in ((False, True) if place in spatial.DEPTH_SHADOW_ROOMS else (False,)):
                renders.append(render_place(place, depth_on, a.seed, real=a.real_standpoints))
    after = canary()
    leaked = {k: (before[k], after[k]) for k in before if before[k] != after[k]}

    for R in renders:
        print(f"== {R['place']} depth={R['depth_on']} named={R['named']} unlabeled={R['unlabeled_clauses'][:4]}")
        for s in R["steps"][:3]:
            print("  ", s["pose"], [ln["line"] for ln in s["lines"]])
    print("canary leaked:", leaked or "none")
    if a.real_standpoints and a.out_json:
        Path(a.out_json).write_text(json.dumps({"job": "J-2628", "real_standpoints": True, "seed": a.seed,
                                                "renders": renders, "results": [], "canary_leaked": leaked},
                                               indent=1, ensure_ascii=False), encoding="utf-8")
    if a.render_only or a.real_standpoints:
        return

    results = []
    for R in renders:
        if len(R["named"]) < 3:
            results.append({"place": R["place"], "depth_on": R["depth_on"], "skipped": f"only {len(R['named'])} objects named"})
            continue
        conds = ["pose", "shuffled", "truth"] if not R["depth_on"] else ["pose", "nopose"]
        if R["place"] == "study" and R["depth_on"]:
            conds = ["pose", "shuffled", "nopose"]
        row = {"place": R["place"], "depth_on": R["depth_on"], "named": R["named"], "chance": chance(R), "conds": {}}
        perm = derangement(len(R["steps"]), a.seed)
        for c in conds:
            t0 = time.time()
            obj, raw = ask_model(prompt(c, R, perm if c == "shuffled" else None))
            pred = parse(obj, R["named"])
            row["conds"][c] = {"score": score(pred, R["truth"], aligned=(c == "nopose")), "pred": pred,
                               "secs": round(time.time() - t0, 1), "raw": raw[:400]}
            print(R["place"], R["depth_on"], c, row["conds"][c]["score"], row["conds"][c]["secs"], "s")
        results.append(row)
    final_canary = canary()
    out = {"job": "J-2628", "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "model": MODEL, "seed": a.seed,
           "renders": renders, "results": results,
           "canary_leaked": {k: (before[k], final_canary[k]) for k in before if before[k] != final_canary[k]}}
    Path(a.out_json).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", a.out_json, "canary leaked:", out["canary_leaked"] or "none")


if __name__ == "__main__":
    main()

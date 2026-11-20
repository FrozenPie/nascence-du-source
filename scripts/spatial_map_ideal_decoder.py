"""
J-2628 companion: the IDEAL reader for the map-reconstruction lab (zero LLM).

Reads the renders saved by scripts/spatial_map_reconstruction_lab.py and, for every named object,
grid-searches the place's bounding box (0.1 m) for the points most consistent with every
(sector, distance-word) observation the lines make about it, given the walker's pose. This is an
upper bound on what the rendering CARRIES (a reader that has fully learned the sense's vocabulary),
separating the rendering's information content from the LLM reader's skill. Also runs the same decoder
on the shuffled (lines permuted across poses) control. Pure stdlib; touches no data/.
    python scripts/spatial_map_ideal_decoder.py docs/lab/spatial_map_reconstruction_2026-10-31.json
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spatial_map_reconstruction_lab import VOCAB, pairwise, procrustes, rmse, derangement  # noqa: E402

SECTORS = ["to your right", "to your left", "behind you", "ahead"]
BANDS = [("right beside you", 0.0, 1.0), ("across the room", 2.0, 3.5), ("at the far side", 3.5, 99),
         ("a little way off", 2.0, 3.5), ("far off", 3.5, 99), ("near", 1.0, 2.0)]


def sector_of(pose, pt):
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


def observe(place, clause):
    """(label, sector|None, (lo, hi)|None) for one rendered clause."""
    label = None
    for lab, rx, _f in VOCAB[place]:
        if re.search(rx, clause if place == "shore" else clause.split(" — ")[0]):
            label = lab
            break
    if not label:
        return None
    head = clause.split(" — ")[0] if not clause.startswith("the tide is") else clause.split(" — ", 1)[-1]
    sec = next((s for s in SECTORS if re.search(r"\b" + s + r"\b", head)), None)
    band = next(((lo, hi) for w, lo, hi in BANDS if re.search(r"\b" + w + r"\b", head)), None)
    return label, sec, band


def decode(R, perm=None):
    obs = {}
    for i, s in enumerate(R["steps"]):
        pose = R["steps"][perm[i]]["pose"] if perm else s["pose"]
        for ln in s["lines"]:
            for c in ln["clauses"]:
                o = observe(R["place"], c)
                if o and (o[1] or o[2]):
                    obs.setdefault(o[0], []).append((pose, o[1], o[2]))
    xs = [s["pose"]["x"] for s in R["steps"]] + [v[0] for v in R["truth"].values()]
    ys = [s["pose"]["y"] for s in R["steps"]] + [v[1] for v in R["truth"].values()]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    grid = [(x0 + 0.1 * i, y0 + 0.1 * j) for i in range(int((x1 - x0) / 0.1) + 1)
            for j in range(int((y1 - y0) / 0.1) + 1)]
    pred, cons = {}, {}
    for lab in R["named"]:
        ob = obs.get(lab, [])
        if not ob:
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
        cons[lab] = {"obs": len(ob), "best_consistent": best, "feasible_area_m2": round(len(pts) * 0.01, 2)}
    names = [n for n in R["named"] if n in pred]
    P, T = [pred[n] for n in names], [R["truth"][n] for n in names]
    ok, tot = pairwise(P, T)
    return {"raw_rmse": round(rmse(P, T), 2), "procrustes_rmse": round(rmse(procrustes(P, T), T), 2),
            "pair_acc": round(ok / tot, 3) if tot else None, "pairs": tot,
            "per_object_err": {n: round(math.dist(pred[n], R["truth"][n]), 2) for n in names},
            "consistency": cons}


def main():
    path = Path(sys.argv[1])
    D = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for R in D["renders"]:
        perm = derangement(len(R["steps"]), D["seed"])
        row = {"place": R["place"], "depth_on": R["depth_on"], "ideal": decode(R), "ideal_shuffled": decode(R, perm)}
        out.append(row)
        print(R["place"], "depth" if R["depth_on"] else "base",
              {k: row["ideal"][k] for k in ("raw_rmse", "procrustes_rmse", "pair_acc", "pairs")},
              "| shuffled", {k: row["ideal_shuffled"][k] for k in ("raw_rmse", "pair_acc")})
        print("   per-object", row["ideal"]["per_object_err"])
        print("   consistency", {k: (v["best_consistent"], v["obs"], v["feasible_area_m2"]) for k, v in row["ideal"]["consistency"].items()})
    D["ideal_decoder"] = out
    path.write_text(json.dumps(D, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in D["results"]:
        print("chance", r["place"], r["depth_on"], r.get("chance") or r.get("skipped"))


if __name__ == "__main__":
    main()

"""
J-2647 (I-0129, between rung 0 and rung 1) -- which READING SHAPE lets the hot LLM recover the map the
spatial lines carry?

LAB ONLY. Nothing reaches Du (D-0434). No re-render: reads the J-2628 renders saved in
docs/lab/spatial_map_reconstruction_2026-10-31.json (same 12 seeded stops per place, seed 2628), so every
number here is paired with F-3381 (ideal decoder) and F-3382 (one-shot LLM). Study (flag OFF) + garden.

Shapes (hot lane qwen3.5:9b, think off, temperature 0.3, 3 samples = ollama seeds 2648/2649/2650):
  A   one_shot         -- J-2628's exact `pose` prompt (variance estimate for F-3382)            1 call/sample
  A2  one_shot_legend  -- same + a legend of the sense's words (sector wedges, distance bands)    1 call/sample
  B   extract_ego      -- per stop: the model copies each object's (direction, distance word) out of
                          that stop's two lines, NO pose given; the ideal decoder's grid search places
                          objects from those tuples + the pose (deterministic aggregator)          12 calls/sample
  E   extract_allo     -- per stop: pose given; the model must turn each relation into a COMPASS
                          direction (8 points, 90-degree wedges) + distance word; same aggregator  12 calls/sample
  C   sketch           -- per stop: pose + lines + the running JSON sketch; model returns the updated
                          sketch; the final sketch is scored (legend given)                         12 calls/sample
  D   scratch_table    -- one call: write every (stop, object, direction, distance) row first, then
                          coordinates (legend given)                                               1 call/sample
Controls: B/E shuffled = the same extracted tuples aggregated against deranged poses (no extra calls);
the regex extraction through the same aggregator = the J-2628 ideal decoder (F-3381).

PRE-REGISTERED SUCCESS BAR (written before any J-2647 model call; committed with this file):
  * A shape REACHES THE IDEAL in a place if, over its 3 samples, mean raw RMSE <= ideal raw RMSE + 1.0 m
    (study <= 1.28 m, garden <= 1.69 m) AND mean pairwise sign accuracy >= 0.85 AND every named object
    was placed in every sample.
  * A shape WORKS (for rung 1) only if it reaches the ideal in BOTH study and garden, and its shuffled
    control (where it has one) is worse by >= 2x raw RMSE.
  * Secondary (stricter): mean raw RMSE <= 2x the ideal (study <= 0.56, garden <= 1.38) in >= 1 place.
  * Reading: if only aggregator shapes (B/E) pass, the map belongs in a deterministic store fed by the
    model, not in the model's context. If none passes, say so and build nothing.

Isolation: imports the J-2628 lab (which imports core.spatial from THIS worktree first, asserted), then
runs inside lab_env.isolate(db="empty") with its lab root under --scratch; hash canary over the live data
files spatial touches, before and after.
    python scripts/spatial_map_reading_shapes_lab.py --scratch <dir> --out-json docs/lab/<file>.json
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spatial_map_reconstruction_lab as L  # noqa: E402  -- imports core.spatial (worktree) first
from spatial_map_ideal_decoder import SECTORS, BANDS, sector_of, decode  # noqa: E402

WT = Path(__file__).resolve().parent.parent
SRC = WT / "docs" / "lab" / "spatial_map_reconstruction_2026-10-31.json"
SEEDS = (2648, 2649, 2650)
DIST_WORDS = [b[0] for b in BANDS]
BAND = {w: (lo, hi) for w, lo, hi in BANDS}
COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
LEGEND = ("How the sense's words work: 'ahead' = within 45 degrees either side of the way they face; "
          "'to your right' / 'to your left' = 45 to 135 degrees round to that side; 'behind you' = the rest. "
          "Distances: 'right beside you' = under 1 m; 'near' = 1 to 2 m; 'across the room' or 'a little way off' "
          "= 2 to 3.5 m; 'at the far side' or 'far off' = beyond 3.5 m. A thing given no distance word may be at "
          "any distance in that direction.")
CALLS = {"n": 0}


def ask(text: str, seed: int, predict: int = 700, timeout: int = 180, tries: int = 3) -> tuple[dict | None, str]:
    body = json.dumps({"model": L.MODEL, "stream": False, "think": False, "format": "json",
                       "options": {"temperature": 0.3, "seed": seed, "num_ctx": 8192, "num_predict": predict},
                       "messages": [{"role": "user", "content": text}]}).encode()
    raw = ""
    for k in range(tries):
        try:
            CALLS["n"] += 1
            req = urllib.request.Request(L.HOT, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = json.loads(resp.read())["message"]["content"]
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj, raw
        except Exception as e:
            raw = f"ERR {type(e).__name__}: {e} | {raw[:200]}"
        time.sleep(4 * (k + 1))
    return None, raw


def names_of(R):
    return ", ".join(f'"{n}"' for n in R["named"])


def stop_text(s, with_pose: bool) -> str:
    p = s["pose"]
    head = f"they stand at x={p['x']}, y={p['y']}, facing {p['facing_deg']} degrees" if with_pose else ""
    return (f"({head})\n" if head else "") + "\n".join(f"  - {ln['line']}" for ln in s["lines"])


def norm_name(k: str, R) -> str | None:
    k = (k or "").lower().strip()
    for n in R["named"]:
        if k == n or k.removeprefix("the ").strip() == n.removeprefix("the "):
            return n
    return None


# ── aggregator: the ideal decoder's grid search over model-extracted observations ──────────────────
def compass_ok(pose, pt, word):
    i = COMPASS.index(word)
    b = math.degrees(math.atan2(pt[0] - pose["x"], pt[1] - pose["y"])) % 360
    d = (b - 45 * i + 180) % 360 - 180
    return abs(d) <= 45


def aggregate(R, obs, perm=None):
    """obs: list of (stop_index, label, kind, dirword, distword). kind 'ego' | 'allo'."""
    by = {}
    for i, lab, kind, dw, dist in obs:
        pose = R["steps"][perm[i]]["pose"] if perm else R["steps"][i]["pose"]
        band = BAND.get(dist)
        if kind == "ego" and dw not in SECTORS:
            dw = None
        if kind == "allo" and dw not in COMPASS:
            dw = None
        if dw or band:
            by.setdefault(lab, []).append((pose, kind, dw, band))
    xs = [s["pose"]["x"] for s in R["steps"]] + [v[0] for v in R["truth"].values()]
    ys = [s["pose"]["y"] for s in R["steps"]] + [v[1] for v in R["truth"].values()]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    grid = [(x0 + 0.1 * i, y0 + 0.1 * j) for i in range(int((x1 - x0) / 0.1) + 1)
            for j in range(int((y1 - y0) / 0.1) + 1)]
    pred = {}
    for lab, ob in by.items():
        def sc(pt):
            k = 0
            for pose, kind, dw, band in ob:
                ok = True
                if dw:
                    ok = sector_of(pose, pt) == dw if kind == "ego" else compass_ok(pose, pt, dw)
                if band:
                    ok = ok and band[0] <= math.dist(pt, (pose["x"], pose["y"])) < band[1] + 1e-9
                k += ok
            return k
        scores = [sc(p) for p in grid]
        best = max(scores)
        pts = [p for p, s in zip(grid, scores) if s == best]
        pred[lab] = [round(sum(p[0] for p in pts) / len(pts), 2), round(sum(p[1] for p in pts) / len(pts), 2)]
    return pred


def regex_obs(R):
    """The J-2628 ideal decoder's own observations, as tuples (sanity: aggregate(regex) == decode())."""
    from spatial_map_ideal_decoder import observe
    out = []
    for i, s in enumerate(R["steps"]):
        for ln in s["lines"]:
            for c in ln["clauses"]:
                o = observe(R["place"], c)
                if o:
                    band = next((w for w, lo, hi in BANDS if o[2] == (lo, hi)), None)
                    out.append((i, o[0], "ego", o[1], band))
    return out


# ── shapes ─────────────────────────────────────────────────────────────────────────────────────────
def shape_extract(R, seed, allo: bool):
    obs, raws = [], []
    for i, s in enumerate(R["steps"]):
        if allo:
            how = ("For each, give the COMPASS direction from where they stand: exactly one of "
                   + ", ".join(f'"{c}"' for c in COMPASS) + ', or "unknown". Work it out from the way they face. '
                   + L.FRAME)
        else:
            how = ('For each, copy the direction exactly as the text gives it, relative to them: one of "ahead", '
                   '"to your right", "to your left", "behind you", or "unknown".')
        text = (f"Someone who cannot see stands at one spot in {R['place']} and is told, at two moments, what is "
                f"around them {'' if allo else 'relative to the way they face'}:\n{stop_text(s, allo)}\n\n"
                f"Which of these things does the text place: {names_of(R)}? Where the cat is said to be at a named "
                f"place, that gives where that place is. {how} Also give the distance word exactly as the text "
                'gives it: one of ' + ", ".join(f'"{w}"' for w in DIST_WORDS) + ', or "unknown".\n'
                'Reply with JSON only: {"relations": [{"object": <name>, "direction": <word>, "distance": <word>}, ...]}')
        obj, raw = ask(text, seed + i, predict=400, timeout=120)
        raws.append(raw[:300])
        for r in (obj or {}).get("relations") or []:
            if not isinstance(r, dict):
                continue
            lab = norm_name(str(r.get("object")), R)
            if lab:
                obs.append((i, lab, "allo" if allo else "ego", str(r.get("direction", "")).lower().strip(),
                            str(r.get("distance", "")).lower().strip()))
    return obs, raws


def shape_sketch(R, seed):
    sk, raws = {}, []
    for i, s in enumerate(R["steps"]):
        text = (f"You are building a map of {R['place']} for someone who cannot see, one stop at a time. {L.FRAME} "
                f"{LEGEND}\nYour sketch so far (best x, y in metres for each thing placed yet): "
                f"{json.dumps(sk) if sk else '(empty)'}\n\nStop {i + 1}: {stop_text(s, True)}\n\n"
                "Where the cat is said to be at a named place, that tells you where that place is. Things such as a "
                "fire or the weather may change between moments; the place itself does not move. Update the sketch "
                f"using this stop: give your best x, y for every one of {names_of(R)} you have evidence for so far "
                "(keep an earlier estimate unless this stop says it must move).\n"
                'Reply with JSON only: {"objects": {<name>: [x, y], ...}}')
        obj, raw = ask(text, seed + i, predict=400, timeout=120)
        raws.append(raw[:300])
        new = L.parse((obj or {}).get("objects"), R["named"])
        sk.update({k: [round(v[0], 2), round(v[1], 2)] for k, v in new.items()})
    return sk, raws


def shape_table(R, seed):
    stops = "\n".join(f"Stop {i + 1} " + stop_text(s, True) for i, s in enumerate(R["steps"]))
    text = (f"Someone who cannot see moves around one place ({R['place']}). At each stop they are told what is "
            "around them, relative to where they are and which way they face. Things such as a fire, a cat or the "
            "weather may change between the two moments at a stop; the place itself does not move. Where the cat "
            f"is said to be at a named place, that tells you where that place is.\n{stops}\n\n{L.FRAME} {LEGEND}\n\n"
            "Work in two steps. First write a table with one row per thing mentioned at each stop: the stop, the "
            "thing, its direction word, its distance word, and the compass bearing that direction means given the "
            "stop's facing. Then, using every row, give your best estimate of where each of these things is: "
            f"{names_of(R)}.\n"
            'Reply with JSON only: {"table": [[stop, thing, direction, distance, bearing], ...], '
            '"objects": {<name>: [x, y], ...}}')
    obj, raw = ask(text, seed, predict=3500, timeout=420)
    return L.parse((obj or {}).get("objects"), R["named"]), raw[:600], len((obj or {}).get("table") or [])


def summarize(samples, R):
    sc = [x["score"] for x in samples]
    ok = [s for s in sc if s.get("raw_rmse") is not None]
    if not ok:
        return {"parsed": 0}
    mean = lambda k: round(sum(s[k] for s in ok) / len(ok), 2)
    return {"parsed": len(ok), "all_placed": all(s.get("n") == len(R["named"]) for s in sc),
            "raw_rmse_mean": mean("raw_rmse"), "raw_rmse_each": [s["raw_rmse"] for s in ok],
            "procrustes_rmse_mean": mean("procrustes_rmse"),
            "pair_acc_mean": round(sum(s["pair_acc"] or 0 for s in ok) / len(ok), 3),
            "pair_acc_each": [s["pair_acc"] for s in ok]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--shapes", default="A,A2,B,E,C,D")
    a = ap.parse_args()
    shapes = a.shapes.split(",")
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env  # noqa: E402  -- after core
    lab_env._LAB_ROOT = scratch / "_lab"
    lab_env._ISOLATE_OUTCOMES_LOG = lab_env._LAB_ROOT / "_isolate_outcomes.jsonl"

    D = json.loads(SRC.read_text(encoding="utf-8"))
    renders = [R for R in D["renders"] if R["place"] in ("study", "garden") and not R["depth_on"]]
    ideal = {r["place"]: r["ideal"] for r in D["ideal_decoder"] if not r["depth_on"]}
    base = {r["place"]: r for r in D["results"] if not r["depth_on"]}
    before = L.canary()
    out = {"job": "J-2647", "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "model": L.MODEL, "src": SRC.name,
           "seeds": SEEDS, "places": {}}
    with lab_env.isolate(db="empty", also=[(L.spatial, ["_SHADOW", "_DEPTH_SHADOW"])]) as lab_dir:
        assert str(lab_dir).startswith(str(scratch)), lab_dir
        for R in renders:
            pl = R["place"]
            perm = L.derangement(len(R["steps"]), D["seed"])
            row = {"named": R["named"], "ideal": {k: ideal[pl][k] for k in ("raw_rmse", "pair_acc")},
                   "f3382_one_shot_t0": base[pl]["conds"]["pose"]["score"], "chance": base[pl]["chance"],
                   "regex_through_aggregator": L.score(aggregate(R, regex_obs(R)), R["truth"], False),
                   "shapes": {}}
            for sh in shapes:
                samples = []
                for sd in SEEDS:
                    t0, c0 = time.time(), CALLS["n"]
                    rec = {"seed": sd}
                    if sh in ("A", "A2"):
                        txt = L.prompt("pose", R)
                        if sh == "A2":
                            txt = txt.replace(L.FRAME, L.FRAME + " " + LEGEND, 1)
                        obj, raw = ask(txt, sd, predict=600, timeout=240)
                        rec["pred"], rec["raw"] = L.parse((obj or {}).get("objects"), R["named"]), raw[:400]
                    elif sh in ("B", "E"):
                        obs, raws = shape_extract(R, sd, allo=(sh == "E"))
                        rec["pred"] = aggregate(R, obs)
                        rec["obs"] = obs
                        rec["shuffled_score"] = L.score(aggregate(R, obs, perm), R["truth"], False)
                        rec["raws"] = raws[:3]
                    elif sh == "C":
                        rec["pred"], raws = shape_sketch(R, sd)
                        rec["raws"] = raws[-2:]
                    elif sh == "D":
                        rec["pred"], rec["raw"], rec["table_rows"] = shape_table(R, sd)
                    rec["score"] = L.score(rec["pred"], R["truth"], False)
                    rec["secs"], rec["calls"] = round(time.time() - t0, 1), CALLS["n"] - c0
                    samples.append(rec)
                    print(pl, sh, sd, {k: rec["score"].get(k) for k in ("n", "raw_rmse", "pair_acc")},
                          ("shuf " + str(rec["shuffled_score"].get("raw_rmse"))) if "shuffled_score" in rec else "",
                          rec["secs"], "s", flush=True)
                summ = summarize(samples, R)
                if sh in ("B", "E"):
                    sh_ok = [x["shuffled_score"]["raw_rmse"] for x in samples if x["shuffled_score"].get("raw_rmse")]
                    summ["shuffled_raw_rmse_mean"] = round(sum(sh_ok) / len(sh_ok), 2) if sh_ok else None
                row["shapes"][sh] = {"summary": summ, "samples": samples}
                print("  SUMMARY", pl, sh, summ, flush=True)
            out["places"][pl] = row
    after = L.canary()
    out["canary_leaked"] = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
    out["model_calls"] = CALLS["n"]
    Path(a.out_json).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", a.out_json, "calls", CALLS["n"], "canary leaked:", out["canary_leaked"] or "none")


if __name__ == "__main__":
    main()

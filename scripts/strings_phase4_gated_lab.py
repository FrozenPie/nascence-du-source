"""Strings and Sheets Phase 4: event-gated envelope re-run (J-2383).

Implements docs/lab/strings_sheets_phase4_gated_metric_sheet.md (pre-registered, committed before this script).
Everything except the per-second string's source is the J-2372 lab (scripts/strings_phase4_envelope_lab.py),
imported unchanged. Offline only; reads scratch copies of the recordings via --rec-dir; writes only the
result JSON under docs/lab/. Never edits core/audio_features.py; never touches data/.

Usage: python -I scripts/strings_phase4_gated_lab.py --rec-dir <scratch copy>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("p4lab", _ROOT / "scripts" / "strings_phase4_envelope_lab.py")
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)   # does the site/addsitedir + core-location assert
np, af = L.np, L.af

J2372 = _ROOT / "docs" / "lab" / "strings_sheets_phase4_envelope_2026-10-18.json"
OUT_JSON = _ROOT / "docs" / "lab" / "strings_sheets_phase4_gated_2026-10-18.json"
PRIMARY_X, SENS_X = 10.0, (6.0, 15.0)


def string_gated(path: str, sec_starts, dur: float, x_db: float):
    """Returns (rows, with None for seconds that have no kept frame; kept-frame share)."""
    y = af.decode(path)
    mag = af._stft_mag(y)
    freqs = np.fft.rfftfreq(af.WIN, 1.0 / af.SR)
    fps = af.SR / af.HOP
    e_full = np.sqrt((mag ** 2).mean(axis=1))
    ref = np.percentile(e_full, 10)
    if ref <= 0:
        pos = e_full[e_full > 0]
        ref = np.percentile(pos, 10) if len(pos) else 1e-12
    if math.isinf(x_db) and x_db < 0:
        keep = np.ones(len(e_full), dtype=bool)
    else:
        keep = 20 * np.log10(np.maximum(e_full, 1e-30) / ref) >= x_db
    m = mag.copy()
    m[~keep] = 0.0
    energy = np.sqrt((m ** 2).mean(axis=1))
    onset = af._onset_env(m)
    centroid_full = (mag * freqs).sum(axis=1) / (mag.sum(axis=1) + 1e-9)
    rough_full = af._roughness_per_frame(mag, freqs)
    n_sec = math.ceil(len(energy) / fps)
    bounds = list(sec_starts) + [dur]
    sections = [None] * len(sec_starts)
    e_s = af._per_second_mean(energy, fps, n_sec)
    o_s = af._onset_density_per_second(onset, fps, n_sec, bounds, sections)
    p_s = af._periodicity_per_second(onset, fps, n_sec)
    c_s = af._continuity_per_second(energy, fps, n_sec)
    rows = []
    for i in range(n_sec):
        fa, fb = int(i * fps), int((i + 1) * fps)
        k = keep[fa:fb]
        if fb <= fa or not k.any():
            rows.append(None)
            continue
        b = float(centroid_full[fa:fb][k].mean())
        r = float(np.clip(rough_full[fa:fb][k].mean(), 0.0, 1.0))
        rows.append([float(e_s[i]), b, float(o_s[i]), float(p_s[i]), r, float(c_s[i])])
    return rows, float(keep.mean())


def miss_dirs(res: dict, cons: dict) -> dict:
    out = {a: {"above": 0, "below": 0} for a in L.CMP_AXES}
    n = 0
    for k, v in res.items():
        env = L.envelope(cons[k]["string"])
        for p in v["measured_vertices"]:
            n += 1
            for a in L.CMP_AXES:
                if p[a] > env[a][1]:
                    out[a]["above"] += 1
                elif p[a] < env[a][0]:
                    out[a]["below"] += 1
    return {"n_vertices": n, "by_axis": {a: d | {"total": d["above"] + d["below"]} for a, d in out.items()}}


def run_gate(x_db, feats, rec_dir, keys):
    strings, kept, n_rows = {}, {}, {}
    for k in keys:
        f = feats[k]
        rows, ks = string_gated(str(rec_dir / f["file"]), [s["start_s"] for s in f["sections"]],
                                f["duration_s"], x_db)
        strings[k] = [L.norm_row(r) for r in rows if r is not None]
        kept[k], n_rows[k] = ks, len(rows)
    return strings, kept, n_rows


def evaluate_gated(strings, cons, keys):
    """L.evaluate() for the non-empty keys (envelopes over ALL keys); amendment A1 for zero-second keys."""
    envs = {k: L.envelope(cons[k]["string"]) for k in keys}
    res = {}
    for k in keys:
        rows = strings[k]
        foreign = [o for o in keys if o != k]
        if not rows:
            res[k] = {"pass": False, "n_in": 0, "misses": [], "baseline_share": 0.0, "own_rank": None,
                      "mean_out_dist": None, "measured_vertices": []}
            continue
        mv = L.vertices(rows) if len(rows) >= 3 else [L.wmean(rows)]
        v = L.key_verdict(mv, envs[k])
        v["baseline_share"] = float(np.mean([L.key_verdict(mv, envs[o])["pass"] for o in foreign]))
        d_own = L.mean_out(mv, envs[k])
        v["own_rank"] = 1 + sum(1 for o in foreign if L.mean_out(mv, envs[o]) < d_own)
        v["mean_out_dist"] = round(d_own, 4)
        v["measured_vertices"] = [{a: round(p[a], 3) for a in L.CMP_AXES} | {"energy_raw": round(p["energy_raw"], 5)}
                                  for p in mv]
        res[k] = v
    return res


def summarise(strings, kept, cons, primary, prev):
    res = evaluate_gated(strings, cons, primary)
    n_pass = sum(v["pass"] for v in res.values())
    share = n_pass / len(primary)
    base = float(np.mean([v["baseline_share"] for v in res.values()]))
    nonempty = [k for k in primary if strings[k]]
    s5 = {}
    for k, v in res.items():
        a = cons[k]["archetype"]
        s5.setdefault(a, [0, 0, []])
        s5[a][0] += int(v["pass"])
        s5[a][1] += 1
        s5[a][2].append(kept[k])
    s3, n3 = 0, 0
    for k in primary:
        if len(strings[k]) < 3:
            continue
        e = [p["energy_raw"] for p in L.vertices(strings[k])]
        n3 += 1
        if cons[k]["archetype"] in L.EVENT_ARCH:
            s3 += int(int(np.argmax(e)) == 1)
        else:
            lo = min(e)
            s3 += int((lo > 0) and (20 * math.log10(max(e) / lo) <= 6.0))
    return {
        "pass": n_pass, "n": len(primary), "share": round(share, 4), "meets_bar": share >= 0.60,
        "shuffle_baseline": round(base, 4), "non_discriminating": base >= 0.8 * share,
        "own_rank_median": float(np.median([v["own_rank"] for v in res.values() if v["own_rank"] is not None])),
        "gated_short": sorted(k for k in primary if 0 < len(strings[k]) < 3),
        "gated_empty": sorted(k for k in primary if not strings[k]),
        "nonempty_share": {"pass": sum(res[k]["pass"] for k in nonempty), "n": len(nonempty)},
        "per_vertex_out_dist_mean": round(float(np.mean([v["mean_out_dist"] for v in res.values()
                                                         if v["mean_out_dist"] is not None])), 4),
        "fail_to_pass": sorted(k for k in primary if res[k]["pass"] and not prev[k]),
        "pass_to_fail": sorted(k for k in primary if not res[k]["pass"] and prev[k]),
        "axis_misses": miss_dirs(res, cons),
        "median_measured_continuity": round(float(np.median([p["continuity"] for v in res.values()
                                                             for p in v["measured_vertices"]])), 3),
        "s3_energy_contour": {"agree": s3, "n": n3},
        "s5_by_archetype": {a: {"pass": p, "n": n, "median_kept_share": round(float(np.median(ks)), 3)}
                            for a, (p, n, ks) in sorted(s5.items())},
    }, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec-dir", required=True)
    rec_dir = Path(ap.parse_args().rec_dir)
    feats = json.loads(L.FEATS.read_text(encoding="utf-8"))["keys"]
    cons = L.load_constructed()
    prev_all = json.loads(J2372.read_text(encoding="utf-8"))
    prev = {k: v["pass"] for k, v in prev_all["per_key"].items()}
    primary = sorted(prev)
    excluded = prev_all["short_excluded"] + prev_all["mismatch_excluded"]
    all_keys = primary + excluded
    ref_strings = {k: [L.norm_row(r) for s in feats[k]["sections"] for r in s["string6"]] for k in all_keys}

    # G0 kill rule: no gate must reproduce the JSON string within 0.01
    g0, _, _ = run_gate(float("-inf"), feats, rec_dir, all_keys)
    dev, worst = 0.0, None
    for k in all_keys:
        if len(g0[k]) != len(ref_strings[k]):
            dev, worst = float("inf"), [k, "length", len(g0[k]), len(ref_strings[k])]
            break
        for x, y in zip(g0[k], ref_strings[k]):
            for a in L.CMP_AXES:
                if abs(x[a] - y[a]) > dev:
                    dev, worst = abs(x[a] - y[a]), [k, a]
    out = {"job": "J-2383", "metric_sheet": "docs/lab/strings_sheets_phase4_gated_metric_sheet.md",
           "ungated_reference": {"pass": prev_all["headline"]["pass"], "n": prev_all["headline"]["n"],
                                 "share": prev_all["headline"]["share"],
                                 "shuffle_baseline": prev_all["headline"]["shuffle_baseline"]},
           "g0": {"max_dev": dev, "worst": worst, "read": dev <= 0.01}}
    print("G0", out["g0"])
    if not out["g0"]["read"]:
        OUT_JSON.write_text(json.dumps(out, indent=1), encoding="utf-8")
        raise SystemExit("G0 kill rule failed; nothing gated is read")

    runs, per_key = {}, {}
    for x in (PRIMARY_X,) + SENS_X:
        strings, kept, n_rows = run_gate(x, feats, rec_dir, all_keys)
        summ, res = summarise(strings, kept, cons, primary, prev)
        summ["kept_share_median"] = round(float(np.median([kept[k] for k in primary])), 3)
        exc = {}
        for k in excluded:
            rows = strings[k]
            if not rows:
                exc[k] = {"pass": False, "n_sec": 0, "ungated_pass": prev_all["s1_excluded"][k]["pass"]}
                continue
            mv = L.vertices(rows) if len(rows) >= 3 else [L.wmean(rows)]
            v = L.key_verdict(mv, L.envelope(cons[k]["string"]))
            exc[k] = {"pass": v["pass"], "n_in": v["n_in"], "n_sec": len(rows),
                      "kept_share": round(kept[k], 3), "ungated_pass": prev_all["s1_excluded"][k]["pass"]}
        summ["excluded"] = exc
        runs[str(int(x))] = summ
        if x == PRIMARY_X:
            per_key = {k: {"archetype": cons[k]["archetype"], "ungated_pass": prev[k],
                           "gated_pass": res[k]["pass"], "n_in": res[k]["n_in"], "own_rank": res[k]["own_rank"],
                           "baseline_share": round(res[k]["baseline_share"], 3), "misses": res[k]["misses"],
                           "kept_share": round(kept[k], 3), "gated_seconds": len(strings[k]),
                           "total_seconds": n_rows[k], "measured_vertices": res[k]["measured_vertices"],
                           "envelope": L.envelope(cons[k]["string"])}
                       for k in primary}
        print(f"X={x}", json.dumps(summ, default=str))
    out["runs"] = runs
    out["per_key_x10"] = per_key
    OUT_JSON.write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

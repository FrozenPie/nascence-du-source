"""Strings and Sheets Phase 4: measured strings vs constructed realness envelope (J-2372).

Implements docs/lab/strings_sheets_phase4_metric_sheet.md exactly (pre-registered, committed before this
script existed). Offline only: reads the J-2027 features JSON, the constructed strings from
scripts/sound_strings_phase1_dryrun.py build_all() (in-process, post J-2067), and (S2 only) scratch copies of
the recordings passed via --rec-dir. Writes only the two result files under docs/lab/. Never edits
core/audio_features.py; never touches data/.

Usage (python -I, from anywhere):  python -I scripts/strings_phase4_envelope_lab.py --rec-dir <scratch copy>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
import site  # noqa: E402

site.addsitedir(site.getusersitepackages())   # python -I drops the user site; numpy lives there

import numpy as np  # noqa: E402
import core  # noqa: E402

assert Path(core.__file__).resolve().parent.parent == _ROOT, f"core loaded from {core.__file__}, not {_ROOT}"
from core import audio_features as af  # noqa: E402

FEATS = _ROOT / "docs" / "lab" / "strings_sheets_phase4_features_2026-10-18.json"
OUT_JSON = _ROOT / "docs" / "lab" / "strings_sheets_phase4_envelope_2026-10-18.json"
OUT_MD = _ROOT / "docs" / "lab" / "strings_sheets_phase4_envelope_2026-10-18.md"

TAU = 0.25
CMP_AXES = ("brightness", "onset", "periodicity", "roughness", "continuity")
MISMATCH = {"dawn_chorus", "log_on_fire"}
FLAGGED = {"moth_tap": "F-3069 partial mismatch", "wren_scold": "F-3069 character mismatch",
           "morepork_call": "F-3069 signal flag (rumble)", "wood_pigeon": "F-3069 signal flag",
           "wind_in_trees": "F-3069 signal flag (rumble)"}
EVENT_ARCH = {"call", "thump", "wingbeat"}

_B_PTS = [(300, 0.0), (1200, .25), (2400, .50), (4000, .75), (8000, 1.0)]
_O_PTS = [(0, 0.0), (1.5, .25), (4, .50), (8, .75), (16, 1.0)]


def _pw(x: float, pts) -> float:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return float(np.clip(np.interp(x, xs, ys), 0.0, 1.0))


def norm_row(r) -> dict:
    """string6 row [energy, bright_hz, onset/s, period, rough, cont] -> 0..1 comparable axes + raw energy."""
    return {"energy_raw": float(r[0]), "brightness": _pw(r[1], _B_PTS), "onset": _pw(r[2], _O_PTS),
            "periodicity": float(r[3]), "roughness": float(r[4]), "continuity": float(r[5])}


def wmean(rows: list[dict]) -> dict:
    w = np.array([r["energy_raw"] for r in rows])
    if w.sum() <= 0:
        w = np.ones(len(rows))
    out = {a: float(np.average([r[a] for r in rows], weights=w)) for a in CMP_AXES}
    out["energy_raw"] = float(np.mean([r["energy_raw"] for r in rows]))
    return out


def vertices(rows: list[dict]) -> list[dict]:
    return [wmean([rows[i] for i in idx]) for idx in np.array_split(np.arange(len(rows)), 3)]


def envelope(cs: dict) -> dict:
    return {a: (max(0.0, min(cs[v][a] for v in ("onset", "peak", "tail")) - TAU),
                min(1.0, max(cs[v][a] for v in ("onset", "peak", "tail")) + TAU)) for a in CMP_AXES}


def out_dist(p: dict, env: dict) -> dict:
    return {a: max(0.0, env[a][0] - p[a], p[a] - env[a][1]) for a in CMP_AXES}


def vertex_in(p: dict, env: dict) -> tuple[bool, list[str]]:
    miss = [a for a, d in out_dist(p, env).items() if d > 0]
    return (len(CMP_AXES) - len(miss)) >= 4, miss


def key_verdict(mv: list[dict], env: dict) -> dict:
    ins = [vertex_in(p, env) for p in mv]
    n_in = sum(1 for ok, _ in ins if ok)
    need = 2 if len(mv) == 3 else 1
    return {"pass": n_in >= need, "n_in": n_in, "misses": [m for _, m in ins]}


def mean_out(mv: list[dict], env: dict) -> float:
    return float(np.mean([sum(out_dist(p, env).values()) for p in mv]))


def load_constructed() -> dict:
    spec = importlib.util.spec_from_file_location("p1dry", _ROOT / "scripts" / "sound_strings_phase1_dryrun.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_all()


# ---- S2: lab-side high-pass recomputation of the per-second string with audio_features' own helpers ----
def string_hp(path: str, sec_starts: list[float], dur: float, cutoff_hz: float) -> list[list[float]]:
    y = af.decode(path)
    mag = af._stft_mag(y)
    freqs = np.fft.rfftfreq(af.WIN, 1.0 / af.SR)
    if cutoff_hz > 0:
        mag = mag.copy()
        mag[:, freqs < cutoff_hz] = 0.0
    fps = af.SR / af.HOP
    energy = np.sqrt((mag ** 2).mean(axis=1))
    centroid = (mag * freqs).sum(axis=1) / (mag.sum(axis=1) + 1e-9)
    onset = af._onset_env(mag)
    rough_frame = af._roughness_per_frame(mag, freqs)
    n_sec = math.ceil(len(energy) / fps)
    bounds = list(sec_starts) + [dur]
    sections = [None] * len(sec_starts)
    e_s = af._per_second_mean(energy, fps, n_sec)
    b_s = af._per_second_mean(centroid, fps, n_sec)
    o_s = af._onset_density_per_second(onset, fps, n_sec, bounds, sections)
    p_s = af._periodicity_per_second(onset, fps, n_sec)
    r_s = np.clip(af._per_second_mean(rough_frame, fps, n_sec), 0.0, 1.0)
    c_s = af._continuity_per_second(energy, fps, n_sec)
    return [[float(e_s[i]), float(b_s[i]), float(o_s[i]), float(p_s[i]), float(r_s[i]), float(c_s[i])]
            for i in range(n_sec)]


def evaluate(strings: dict, cons: dict, keys: list[str]) -> dict:
    """strings: key -> list of normalised rows. Returns per-key results for `keys` (primary-style rule)."""
    envs = {k: envelope(cons[k]["string"]) for k in keys}
    res = {}
    for k in keys:
        rows = strings[k]
        mv = vertices(rows) if len(rows) >= 3 else [wmean(rows)]
        v = key_verdict(mv, envs[k])
        foreign = [o for o in keys if o != k]
        v["baseline_share"] = float(np.mean([key_verdict(mv, envs[o])["pass"] for o in foreign])) if foreign else None
        d_own = mean_out(mv, envs[k])
        v["own_rank"] = 1 + sum(1 for o in foreign if mean_out(mv, envs[o]) < d_own)
        v["mean_out_dist"] = round(d_own, 4)
        v["measured_vertices"] = [{a: round(p[a], 3) for a in CMP_AXES} | {"energy_raw": round(p["energy_raw"], 5)}
                                  for p in mv]
        res[k] = v
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec-dir", required=True)
    args = ap.parse_args()
    rec_dir = Path(args.rec_dir)

    feats = json.loads(FEATS.read_text(encoding="utf-8"))["keys"]
    cons = load_constructed()
    meas_keys = sorted(k for k in feats if isinstance(feats[k], dict) and "sections" in feats[k])
    no_rec = sorted(set(cons) - set(meas_keys))
    assert not (set(meas_keys) - set(cons)), set(meas_keys) - set(cons)

    raw, strings, inconsistent = {}, {}, []
    for k in meas_keys:
        rows = [r for s in feats[k]["sections"] for r in s["string6"]]
        if abs(len(rows) - math.ceil(feats[k]["duration_s"])) > 1:
            inconsistent.append(k)
            continue
        raw[k] = rows
        strings[k] = [norm_row(r) for r in rows]

    short = sorted(k for k in strings if len(strings[k]) < 3)
    primary = sorted(k for k in strings if k not in short and k not in MISMATCH)

    prim = evaluate(strings, cons, primary)
    n_pass = sum(v["pass"] for v in prim.values())
    share = n_pass / len(primary)
    baseline = float(np.mean([v["baseline_share"] for v in prim.values()]))
    nondisc = baseline >= 0.8 * share

    # S1: excluded keys, each against its own envelope (point test for short; normal rule for mismatch)
    s1 = {}
    for k in short + sorted(MISMATCH & set(strings)):
        rows = strings[k]
        mv = vertices(rows) if len(rows) >= 3 else [wmean(rows)]
        v = key_verdict(mv, envelope(cons[k]["string"]))
        v["n_sec"] = len(rows)
        v["measured_vertices"] = [{a: round(p[a], 3) for a in CMP_AXES} for p in mv]
        s1[k] = v
    all_pass = n_pass + sum(v["pass"] for v in s1.values())
    all_n = len(primary) + len(s1)

    # S3 energy contour
    s3 = {}
    for k in primary:
        e = [p["energy_raw"] for p in vertices(strings[k])]
        arch = cons[k]["archetype"]
        if arch in EVENT_ARCH:
            s3[k] = int(np.argmax(e)) == 1
        else:
            lo = min(e)
            s3[k] = (lo > 0) and (20 * math.log10(max(e) / lo) <= 6.0)
    # S4 per-axis misses over primary vertices
    s4 = {a: 0 for a in CMP_AXES}
    n_vert = 0
    for v in prim.values():
        for m in v["misses"]:
            n_vert += 1
            for a in m:
                s4[a] += 1
    # S5 by archetype
    s5 = {}
    for k, v in prim.items():
        a = cons[k]["archetype"]
        s5.setdefault(a, [0, 0])
        s5[a][0] += int(v["pass"])
        s5[a][1] += 1
    # bed body (report only)
    body = {k: {a: round(wmean(strings[k])[a], 3) for a in CMP_AXES} for k in primary
            if cons[k]["archetype"] in ("bed", "bed_like")}

    # S2: high-pass sensitivity, gated by the 0 Hz reproduction kill rule
    repro_max, repro_worst = 0.0, None
    for k in strings:
        f = feats[k]
        path = rec_dir / f["file"]
        hp0 = string_hp(str(path), [s["start_s"] for s in f["sections"]], f["duration_s"], 0.0)
        a0 = [norm_row(r) for r in hp0]
        if len(a0) != len(strings[k]):
            repro_max, repro_worst = float("inf"), (k, "length")
            break
        for x, y in zip(a0, strings[k]):
            for a in CMP_AXES:
                d = abs(x[a] - y[a])
                if d > repro_max:
                    repro_max, repro_worst = d, (k, a)
    s2 = {"repro_max_dev": repro_max, "repro_worst": repro_worst, "read": repro_max <= 0.01}
    if s2["read"]:
        hp_strings = {}
        for k in strings:
            f = feats[k]
            rows = string_hp(str(rec_dir / f["file"]), [s["start_s"] for s in f["sections"]], f["duration_s"], 150.0)
            hp_strings[k] = [norm_row(r) for r in rows]
        hp = evaluate(hp_strings, cons, primary)
        hp_pass = sum(v["pass"] for v in hp.values())
        s2.update({"cutoff_hz": 150.0, "pass": hp_pass, "n": len(primary), "share": hp_pass / len(primary),
                   "baseline": float(np.mean([v["baseline_share"] for v in hp.values()])),
                   "flips": {k: [prim[k]["pass"], hp[k]["pass"]] for k in primary if prim[k]["pass"] != hp[k]["pass"]}})

    out = {
        "job": "J-2372", "metric_sheet": "docs/lab/strings_sheets_phase4_metric_sheet.md",
        "inputs": {"features": str(FEATS.relative_to(_ROOT)), "constructed": "scripts/sound_strings_phase1_dryrun.py build_all()"},
        "constructed_without_recording": no_rec, "inconsistent_excluded": inconsistent,
        "short_excluded": short, "mismatch_excluded": sorted(MISMATCH & set(strings)),
        "headline": {"pass": n_pass, "n": len(primary), "share": round(share, 4), "bar": 0.60,
                     "meets_bar": share >= 0.60, "shuffle_baseline": round(baseline, 4),
                     "non_discriminating": nondisc,
                     "own_rank_median": float(np.median([v["own_rank"] for v in prim.values()])),
                     "n_envelopes": len(primary)},
        "all_keys": {"pass": all_pass, "n": all_n, "share": round(all_pass / all_n, 4)},
        "s1_excluded": s1, "s2_highpass": s2,
        "s3_energy_contour": {"agree": sum(s3.values()), "n": len(s3), "per_key": s3},
        "s4_axis_misses": {"n_vertices": n_vert, "misses": s4},
        "s5_by_archetype": {a: {"pass": p, "n": n} for a, (p, n) in sorted(s5.items())},
        "bed_body": body,
        "per_key": {k: prim[k] | {"archetype": cons[k]["archetype"], "flag": FLAGGED.get(k),
                                   "rumble_lowband_share": feats[k].get("review_signal", {}).get("band_share", {}).get("<300"),
                                   "constructed": cons[k]["string"], "envelope": envelope(cons[k]["string"])}
                    for k in primary},
    }
    OUT_JSON.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("constructed_without_recording", "inconsistent_excluded", "short_excluded",
                                          "mismatch_excluded", "headline", "all_keys")}, indent=1))
    print("S2", json.dumps({k: v for k, v in s2.items()}, default=str))
    print("S3", out["s3_energy_contour"]["agree"], "/", out["s3_energy_contour"]["n"])
    print("S4", out["s4_axis_misses"])
    print("S5", out["s5_by_archetype"])
    print("S1", {k: (v["pass"], v["n_in"], v["n_sec"]) for k, v in s1.items()})
    for k in primary:
        v = prim[k]
        print(f"{k:22s} {cons[k]['archetype']:9s} {'PASS' if v['pass'] else 'fail'} in={v['n_in']} "
              f"rank={v['own_rank']:2d} base={v['baseline_share']:.2f} misses={v['misses']}")


if __name__ == "__main__":
    main()

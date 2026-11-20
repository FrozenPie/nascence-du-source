"""Strings and Sheets Phase 4: wood_pigeon swap XC957404 -> XC933702 + single-key re-seed (J-2406, D-0481).

Implements docs/lab/strings_sheets_phase4_woodpigeon_metric_sheet.md (committed before this script ran).
Reuses, unchanged: J-2027's signal review + J-2397's window/feature helpers (function source pulled verbatim out
of scripts/strings_phase4_repick_lab.py with ast, since that script runs at import), the J-2372 envelope lab, the
J-2383 gated lab and J-2395's fit_axis(). Offline only: reads scratch copies of the recordings (--rec-dir, which
must hold J-2395's rec dir contents plus wood_pigeon__XC933702.mp3) and the committed docs/lab JSONs. Writes window
WAVs into --rec-dir and one JSON under docs/lab/. Never touches data/ or core/audio_features.py.

  python -I scripts/strings_phase4_woodpigeon_lab.py measure --rec-dir <scratch>   # before _SOUNDS is edited
  python -I scripts/strings_phase4_woodpigeon_lab.py test    --rec-dir <scratch>   # after _SOUNDS is edited
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import sys
import wave
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _load("p4reseed", "scripts/strings_phase4_reseed_lab.py")   # loads L (J-2372), G (J-2383), P1; core assert inside
L, G = R.L, R.G
np = L.np
af = L.af
sys.path.insert(0, str(_ROOT / "scripts"))
import ribbon_lab as rl  # noqa: E402

assert Path(rl.__file__).resolve().is_relative_to(_ROOT.resolve()), rl.__file__

# J-2027 / J-2397 helpers, verbatim
_src = (_ROOT / "scripts" / "strings_phase4_repick_lab.py").read_text(encoding="utf-8")
_tree = ast.parse(_src)
_NS = {"np": np, "af": af, "rl": rl, "math": math, "wave": wave, "hashlib": hashlib, "Path": Path,
       "fps": af.SR / af.HOP, "freqs": np.fft.rfftfreq(af.WIN, 1.0 / af.SR)}
for _n in _tree.body:
    if isinstance(_n, ast.FunctionDef) and _n.name in ("review", "band_power_per_sec", "best_window", "write_wav", "features"):
        exec(compile(ast.Module(body=[_n], type_ignores=[]), "strings_phase4_repick_lab.py", "exec"), _NS)
review, best_window, write_wav, features = _NS["review"], _NS["best_window"], _NS["write_wav"], _NS["features"]

KEY = "wood_pigeon"
NEW_FILE = "wood_pigeon__XC933702.mp3"
NEW_SHA = "e095552504f305de1b4c3a515f8d8cb17a432ed55e71ea99bea08feeff9d50b0"
OUT = _ROOT / "docs" / "lab" / "strings_sheets_phase4_woodpigeon_2026-10-18.json"
J2395_AFTER = {"pass": 51, "n": 64, "baseline_round3": 0.331}
# J-2409 (D-0483): the same check on another file. Defaults reproduce J-2406 exactly; main() may override.
JOB = "J-2406"
TAG = "XC933702"
ACCEPT_RULING = None   # e.g. "D-0483": the founder accepted the file despite a failed check


def base_strings():
    """J-2395's read (b) strings: features JSON with the four J-2397 re-picks merged; moth_tap out."""
    feats_old, feats_new = R.feats_merged()
    s = {k: R.rows_of(v) for k, v in feats_new.items() if isinstance(v, dict) and "sections" in v}
    s.pop("moth_tap", None)
    short = {k for k, v in s.items() if len(v) < 3}
    read_b = sorted(k for k in s if k not in short)
    read_a = sorted(k for k in read_b if k not in ("dawn_chorus", "log_on_fire"))
    return feats_new, s, read_b, read_a


def per_key(ev, k):
    v = ev[k]
    return {"pass": v["pass"], "n_in": v["n_in"], "misses": v["misses"], "own_rank": v["own_rank"],
            "baseline_share": round(v["baseline_share"], 3), "measured_vertices": v["measured_vertices"]}


def measure(rec_dir: Path):
    res = {"job": JOB, "sheet": "docs/lab/strings_sheets_phase4_woodpigeon_metric_sheet.md", "key": KEY}
    feats_new, s_old, read_b, read_a = base_strings()
    old_f = feats_new[KEY]
    # sanity: J-2027 review reproduces on the OLD file
    r = review(rec_dir / old_f["file"]); st = old_f["review_signal"]
    dev = max([abs(r["tonal_share_1.5-9k"] - st["tonal_share_1.5-9k"])] + [abs(r["band_share"][b] - st["band_share"][b]) for b in st["band_share"]])
    res["sanity_review_old"] = {"max_dev": round(dev, 4), "ok": dev <= 0.002}
    print("sanity", res["sanity_review_old"], flush=True)
    if dev > 0.002:
        OUT.write_text(json.dumps(res, indent=1), encoding="utf-8"); raise SystemExit("sanity failed; nothing read")

    src = rec_dir / NEW_FILE
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    assert sha == NEW_SHA, sha
    y = af.decode(str(src)); full = len(y) / af.SR
    s0 = best_window(y, 300, 2000, 15); s1 = s0 + 15
    wp = rec_dir / f"{KEY}__{TAG}_window_{s0}-{s1}.wav"
    write_wav(y[int(s0 * af.SR):int(s1 * af.SR)], wp)
    rw, rf = review(wp), review(src)
    bs = rw["band_share"]
    clears = (max(bs, key=bs.get) == "300-2k") and bs["<300"] < 0.5 and 300 <= rw["dominant_hz"][0] < 2000
    res["file"] = {"source_file": NEW_FILE, "sha256": sha, "bytes": src.stat().st_size, "full_duration_s": round(full, 2),
                   "window_s": [s0, s1], "window_wav": wp.name}
    res["review_window"], res["review_full"] = rw, rf
    res["f3069_check"] = {"clears": bool(clears), "largest_band": max(bs, key=bs.get), "lt300": bs["<300"],
                          "top_dominant_hz": rw["dominant_hz"][0],
                          "old_file": {"band_share": st["band_share"], "dominant_hz": st["dominant_hz"],
                                       "tonal_peak_hz_median": st.get("tonal_peak_hz_median")}}
    print("window", [s0, s1], "of", round(full, 2), "s; review window", rw, "\nfull", rf, "\nF-3069 clears", clears, flush=True)

    fe = features(wp); fe["file"] = wp.name; fe["review_signal"] = rw
    res["features"] = fe
    print("kill", fe["kill_deviation"], fe["kill_triggered"], flush=True)
    # W0: no-gate string_gated reproduces string6
    rows0, _ = G.string_gated(str(wp), [s["start_s"] for s in fe["sections"]], fe["duration_s"], float("-inf"))
    ref = R.rows_of(fe); a0 = [L.norm_row(x) for x in rows0]
    w0 = max(abs(x[a] - y_[a]) for x, y_ in zip(a0, ref) for a in L.CMP_AXES) if len(a0) == len(ref) else float("inf")
    res["W0_max_dev"] = round(w0, 5)
    print("W0", w0, flush=True)

    cons = L.load_constructed()
    # T1: current registry, old wood_pigeon file -> J-2395 after numbers
    h1, _ = R.headline_ungated(s_old, cons, read_b)
    t1 = (h1["pass"], h1["n"], round(h1["baseline"], 3)) == (J2395_AFTER["pass"], J2395_AFTER["n"], J2395_AFTER["baseline_round3"])
    res["T1"] = {"ok": t1, "got": h1}
    print("T1", t1, h1, flush=True)
    if not (t1 and w0 <= 0.01 and not fe["kill_triggered"]):
        OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8"); raise SystemExit("gate failed; nothing read")

    s_new = dict(s_old); s_new[KEY] = R.rows_of(fe)
    assert len(s_new[KEY]) >= 3
    res["swap_headline"] = {}
    for name, keys in (("read_b", read_b), ("read_a", read_a)):
        hb, evb = R.headline_ungated(s_old, cons, keys)
        hs, evs = R.headline_ungated(s_new, cons, keys)
        res["swap_headline"][name] = {"old_file": hb, "new_file": hs,
                                      "flips": sorted(k for k in keys if evb[k]["pass"] != evs[k]["pass"]),
                                      "wood_pigeon_old": per_key(evb, KEY), "wood_pigeon_new": per_key(evs, KEY),
                                      "pass_by_key_new_file": {k: bool(evs[k]["pass"]) for k in keys}}
        print("swap", name, "old", hb, "\n  new", hs, "\n  wp new", per_key(evs, KEY), flush=True)

    # gated (X=10) on the new window, and the single-key J-2395 rule
    envk = L.envelope(cons[KEY]["string"])
    rows, ks = G.string_gated(str(wp), [s["start_s"] for s in fe["sections"]], fe["duration_s"], R.X_DB)
    gr = [L.norm_row(x) for x in rows if x is not None]
    gmv = L.vertices(gr) if len(gr) >= 3 else ([L.wmean(gr)] if gr else [])
    gkv = L.key_verdict(gmv, envk) if gmv else {"pass": False, "n_in": 0, "misses": []}
    umv = L.vertices(s_new[KEY]); ukv = L.key_verdict(umv, envk)
    meas = {"gated_pass": gkv["pass"], "gated_seconds": len(gr), "kept_share": round(ks, 3),
            "gated_vertices": [{a: round(p[a], 3) for a in L.CMP_AXES} for p in gmv], "gated_misses": gkv["misses"],
            "ungated_vertices": [{a: round(p[a], 3) for a in L.CMP_AXES} for p in umv], "ungated_misses": ukv["misses"],
            "ungated_pass": ukv["pass"], "envelope_before": {a: [round(x, 3) for x in envk[a]] for a in L.CMP_AXES}}
    res["measured"] = meas
    print("gated", meas, flush=True)
    fixed = dict(cons[KEY]["fixed_point"]); new_fixed = dict(fixed)
    res["fixed_point_before"] = fixed
    rs = []
    res["accepted_by_ruling"] = ACCEPT_RULING
    if not clears and not ACCEPT_RULING:
        res["reseed_skipped"] = "F-3069 check did not clear: D-0481 defeater fires, no re-seed"
    elif meas["gated_pass"]:
        res["reseed_skipped"] = "passes the gated test: not a candidate"
    elif meas["gated_seconds"] < 3:
        res["reseed_skipped"] = f"only {meas['gated_seconds']} gated seconds"
    else:
        named = sorted({a for t in meas["gated_misses"] for a in t})
        u_named = {a for t in meas["ungated_misses"] for a in t}
        for a in sorted(named, key=lambda a: (a not in R.TIMBRE, a)):
            if a == "onset" and "onset" not in u_named:
                rs.append({"key": KEY, "axis": a, "old": fixed[a], "new": None, "applied": False,
                           "why": "named by the gated table only (onset exception)"}); continue
            srcn = "ungated" if a == "onset" else "gated"
            vals = [p[a] for p in (meas["ungated_vertices"] if srcn == "ungated" else meas["gated_vertices"])]
            nv = R.fit_axis(KEY, new_fixed, a, vals); new_fixed[a] = nv
            rs.append({"key": KEY, "axis": a, "old": fixed[a], "new": nv, "applied": nv != fixed[a], "target": srcn,
                       "measured_thirds": [round(v, 3) for v in vals], "envelope_before": meas["envelope_before"][a],
                       "delta": round(nv - fixed[a], 2), "large_shift": abs(nv - fixed[a]) >= 0.40})
    res["reseed"] = rs
    res["swap_strings_wood_pigeon"] = s_new[KEY]
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    for x in rs:
        print("RESEED", x, flush=True)
    print("wrote", OUT)


def test(rec_dir: Path):
    res = json.loads(OUT.read_text(encoding="utf-8"))
    before = {KEY: res["fixed_point_before"]}
    cons_after = L.load_constructed()
    want = {(x["key"], x["axis"]): x["new"] for x in res["reseed"] if x["applied"]}
    # T0: compare against the J-2395 post-edit registry (its proposal's constructed_before + its applied rows)
    prop = json.loads(R.PROPOSAL.read_text(encoding="utf-8"))
    ref = {k: dict(v["fixed_point"]) for k, v in prop["constructed_before"].items()}
    for x in prop["reseed"]:
        if x["applied"]:
            ref[x["key"]][x["axis"]] = x["new"]
    assert ref[KEY] == before[KEY], (ref[KEY], before[KEY])
    got = {(k, a): cons_after[k]["fixed_point"][a] for k in ref for a, v in ref[k].items() if cons_after[k]["fixed_point"][a] != v}
    t0 = got == want
    print("T0", t0, got, want)
    if not t0:
        raise SystemExit("T0 failed")
    feats_new, s_old, read_b, read_a = base_strings()
    s_new = dict(s_old); s_new[KEY] = res["swap_strings_wood_pigeon"]
    res["T0"] = t0
    res["after_reseed"] = {}
    for name, keys in (("read_b", read_b), ("read_a", read_a)):
        pre = res["swap_headline"][name]["new_file"]
        pk = res["swap_headline"][name]["pass_by_key_new_file"]
        ha, eva = R.headline_ungated(s_new, cons_after, keys)
        res["after_reseed"][name] = {"before_reseed": pre, "after_reseed": ha, "wood_pigeon": per_key(eva, KEY),
                                     "fail_to_pass": sorted(k for k in keys if eva[k]["pass"] and not pk[k]),
                                     "pass_to_fail": sorted(k for k in keys if pk[k] and not eva[k]["pass"])}
        print(name, "before", pre, "\n  after", ha, "\n  wp", per_key(eva, KEY),
              "\n  f->P", res["after_reseed"][name]["fail_to_pass"], "P->f", res["after_reseed"][name]["pass_to_fail"])
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print("wrote", OUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("measure", "test"))
    ap.add_argument("--rec-dir", required=True)
    ap.add_argument("--file", help="recording file name in --rec-dir (default: J-2406's XC933702)")
    ap.add_argument("--sha", help="expected SHA-256 of --file")
    ap.add_argument("--tag", help="label used in the window WAV name")
    ap.add_argument("--out", help="result JSON path (default: J-2406's)")
    ap.add_argument("--job", help="job id written into the result")
    ap.add_argument("--accept-ruling", help="decision id that accepts the file despite a failed F-3069 check")
    a = ap.parse_args()
    g = globals()
    if a.file: g["NEW_FILE"] = a.file
    if a.sha: g["NEW_SHA"] = a.sha
    if a.tag: g["TAG"] = a.tag
    if a.out: g["OUT"] = Path(a.out).resolve()
    if a.job: g["JOB"] = a.job
    if a.accept_ruling: g["ACCEPT_RULING"] = a.accept_ruling
    (measure if a.mode == "measure" else test)(Path(a.rec_dir))


if __name__ == "__main__":
    main()

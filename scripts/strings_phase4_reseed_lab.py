"""Strings and Sheets Phase 4: reviewed re-seed of the named axes (J-2395, D-0476; folds J-2399's three keys).

Implements docs/lab/strings_sheets_phase4_reseed_2026-10-18.md section 2 (the re-seed rule) and section 4 (the
re-run). Imports the J-2372 envelope lab and the J-2383 gated lab UNCHANGED. Offline only: reads scratch copies of
the recordings (--rec-dir, which must also hold J-2397's four window WAVs), the committed docs/lab JSONs and
build_all() from scripts/sound_strings_phase1_dryrun.py (which reads THIS tree's core/soundscape._SOUNDS).
Writes only its own JSON under docs/lab/. Never edits core/audio_features.py; never touches data/.

  python -I scripts/strings_phase4_reseed_lab.py propose --rec-dir <scratch>   # before _SOUNDS is edited
  python -I scripts/strings_phase4_reseed_lab.py test    --rec-dir <scratch>   # after _SOUNDS is edited
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, _ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = _load("p4lab", "scripts/strings_phase4_envelope_lab.py")      # site + core-location assert happen here
G = _load("p4gated", "scripts/strings_phase4_gated_lab.py")
P1 = _load("p1dry", "scripts/sound_strings_phase1_dryrun.py")
np = L.np

LAB = _ROOT / "docs" / "lab"
J2372 = LAB / "strings_sheets_phase4_envelope_2026-10-18.json"
J2383 = LAB / "strings_sheets_phase4_gated_2026-10-18.json"
J2397 = LAB / "strings_sheets_phase4_repick_2026-10-18.json"
PROPOSAL = LAB / "strings_sheets_phase4_reseed_proposal_2026-10-18.json"
RESULT = LAB / "strings_sheets_phase4_reseed_2026-10-18.json"

REPICKED = ("dawn_chorus", "log_on_fire", "morepork_call", "wind_in_trees")   # J-2397 new files (windows)
EXCLUDE = {"wood_pigeon": "D-0477 re-pick key, NOT swapped (XC933702 licence unreadable); its file is the F-3069-flagged one",
           "moth_tap": "constructed-only (D-0477); no measured string"}
TIMBRE = ("periodicity", "roughness", "continuity")
ENV_AX = ("brightness", "onset")
X_DB = 10.0
VERTS = ("onset", "peak", "tail")


def feats_merged():
    feats = json.loads(L.FEATS.read_text(encoding="utf-8"))["keys"]
    rp = json.loads(J2397.read_text(encoding="utf-8"))["keys"]
    new = dict(feats)
    for k in REPICKED:
        new[k] = rp[k]["features"]
    return feats, new


def rows_of(fe):
    return [L.norm_row(r) for s in fe["sections"] for r in s["string6"]]


def offsets(key, fixed):
    on, pk, tl, _ = P1.build_string(key, fixed)
    return {a: [on[a] - pk[a], 0.0, tl[a] - pk[a]] for a in ENV_AX}


def fit_axis(key, fixed, axis, m):
    """m = the three measured vertex values (onset, peak, tail thirds) on `axis`."""
    if axis in TIMBRE:
        return round(float(np.clip(np.mean(m), 0.0, 1.0)), 2)
    s = fixed[axis]
    for _ in range(3):                 # offsets depend on clipping (and, for calls, on continuity)
        f = dict(fixed); f[axis] = s
        off = offsets(key, f)[axis]
        s = float(np.clip(np.mean([mi - oi for mi, oi in zip(m, off)]), 0.0, 1.0))
    return round(s, 2)


def propose(rec_dir: Path):
    feats_old, feats_new = feats_merged()
    cons = L.load_constructed()
    g = json.loads(J2383.read_text(encoding="utf-8"))
    u = json.loads(J2372.read_text(encoding="utf-8"))
    rp = json.loads(J2397.read_text(encoding="utf-8"))
    out = {"job": "J-2395", "sheet": "docs/lab/strings_sheets_phase4_reseed_2026-10-18.md", "x_db": X_DB}

    # Gate R0a: G0 on the four re-picked windows (no gate reproduces J-2397's string6 within 0.01)
    dev, worst = 0.0, None
    for k in REPICKED:
        f = feats_new[k]
        rows, _ = G.string_gated(str(rec_dir / f["file"]), [s["start_s"] for s in f["sections"]], f["duration_s"], float("-inf"))
        ref = rows_of(f)
        a0 = [L.norm_row(r) for r in rows]
        if len(a0) != len(ref):
            dev, worst = float("inf"), [k, "length"]
            break
        for x, y in zip(a0, ref):
            for a in L.CMP_AXES:
                if abs(x[a] - y[a]) > dev:
                    dev, worst = abs(x[a] - y[a]), [k, a]
    # Gate R0b: this pipeline reproduces three J-2383 gated vertex sets within 0.002
    dev_b = 0.0
    for k in ("cat_purr", "gull_cries", "wren_scold"):
        f = feats_old[k]
        rows, _ = G.string_gated(str(rec_dir / f["file"]), [s["start_s"] for s in f["sections"]], f["duration_s"], X_DB)
        mv = L.vertices([L.norm_row(r) for r in rows if r is not None])
        for p, q in zip(mv, g["per_key_x10"][k]["measured_vertices"]):
            dev_b = max(dev_b, max(abs(p[a] - q[a]) for a in L.CMP_AXES))
    out["gates"] = {"R0a_window_repro_max_dev": dev, "R0a_worst": worst, "R0b_j2383_repro_max_dev": round(dev_b, 5),
                    "read": dev <= 0.01 and dev_b <= 0.002}
    print("gates", out["gates"], flush=True)
    if not out["gates"]["read"]:
        PROPOSAL.write_text(json.dumps(out, indent=1), encoding="utf-8")
        raise SystemExit("gate failed; nothing proposed")

    # Gated + ungated measured vertices per candidate key
    meas = {}
    for k, v in g["per_key_x10"].items():
        if k in REPICKED:
            continue
        meas[k] = {"source": "J-2383 per_key_x10 (old file)", "gated_pass": v["gated_pass"],
                   "gated_seconds": v["gated_seconds"], "gated_vertices": v["measured_vertices"],
                   "gated_misses": v["misses"],
                   "ungated_vertices": u["per_key"][k]["measured_vertices"], "ungated_misses": u["per_key"][k]["misses"]}
    for k in REPICKED:
        f = feats_new[k]
        rows, ks = G.string_gated(str(rec_dir / f["file"]), [s["start_s"] for s in f["sections"]], f["duration_s"], X_DB)
        gr = [L.norm_row(r) for r in rows if r is not None]
        env = L.envelope(cons[k]["string"])
        mv = L.vertices(gr) if len(gr) >= 3 else ([L.wmean(gr)] if gr else [])
        kv = L.key_verdict(mv, env) if mv else {"pass": False, "n_in": 0, "misses": []}
        ur = rows_of(f)
        umv = L.vertices(ur)
        ukv = L.key_verdict(umv, env)
        meas[k] = {"source": "J-2397 window, gated here", "gated_pass": kv["pass"], "gated_seconds": len(gr),
                   "kept_share": round(ks, 3),
                   "gated_vertices": [{a: round(p[a], 3) for a in L.CMP_AXES} for p in mv], "gated_misses": kv["misses"],
                   "ungated_vertices": [{a: round(p[a], 3) for a in L.CMP_AXES} for p in umv],
                   "ungated_misses": ukv["misses"], "ungated_pass": ukv["pass"]}

    # The rule (sheet section 2)
    rows, skipped = [], {}
    for k in sorted(meas):
        m = meas[k]
        if k in EXCLUDE:
            skipped[k] = EXCLUDE[k]; continue
        if m["gated_pass"]:
            continue
        if m["gated_seconds"] < 3:
            skipped[k] = f"only {m['gated_seconds']} gated seconds (< 3): no three thirds to fit"; continue
        named = sorted({a for third in m["gated_misses"] for a in third})
        u_named = {a for third in m["ungated_misses"] for a in third}
        fixed = dict(cons[k]["fixed_point"])
        new_fixed = dict(fixed)
        # timbre first (call offsets depend on continuity), then brightness/onset
        for a in sorted(named, key=lambda a: (a not in TIMBRE, a)):
            if a == "onset" and "onset" not in u_named:
                rows.append({"key": k, "axis": a, "old": fixed[a], "new": None, "applied": False,
                             "why": "named by the gated table only; the ungated vertices sit inside on onset (gate artefact, F-3090)"})
                continue
            src = "ungated" if a == "onset" else "gated"
            mv = m["ungated_vertices"] if src == "ungated" else m["gated_vertices"]
            vals = [p[a] for p in mv]
            new = fit_axis(k, new_fixed, a, vals)
            new_fixed[a] = new
            dirs = [("+" if p[a] > env_hi else "-") for p, third in zip(m["gated_vertices"], m["gated_misses"])
                    for env_hi in [L.envelope(cons[k]["string"])[a][1]] if a in third]
            rows.append({"key": k, "axis": a, "archetype": cons[k]["archetype"], "old": fixed[a], "new": new,
                         "applied": new != fixed[a], "target": src, "measured_thirds": [round(v, 3) for v in vals],
                         "envelope_before": [round(x, 3) for x in L.envelope(cons[k]["string"])[a]],
                         "gated_miss_dirs": "".join(dirs),
                         "evidence": (f"{m['source']}; gated misses {m['gated_misses']}; ungated misses {m['ungated_misses']}")})
    out["measured"] = meas
    out["skipped"] = skipped
    out["reseed"] = rows
    out["constructed_before"] = cons
    out["ungated_reference"] = {"read_a": {x: rp["read_a"][x] for x in ("pass", "n", "share", "baseline", "non_discriminating")},
                                "read_b": {x: rp["read_b_all_in"][x] for x in ("pass", "n", "share", "baseline", "non_discriminating")}}
    PROPOSAL.write_text(json.dumps(out, indent=1), encoding="utf-8")
    ap = [r for r in rows if r["applied"]]
    print(f"{len(ap)} axis re-seeds over {len({r['key'] for r in ap})} keys; skipped {skipped}")
    for r in rows:
        print(f"{r['key']:22s} {r['axis']:12s} {r['old']} -> {r['new']}  {r.get('target','')} {r.get('measured_thirds','')} "
              f"env {r.get('envelope_before','')} {r.get('gated_miss_dirs','')} {'' if r['applied'] else r.get('why','(no change)')}")


def headline_ungated(strings, cons, keys):
    ev = L.evaluate(strings, cons, keys)
    n = sum(v["pass"] for v in ev.values()); base = float(np.mean([v["baseline_share"] for v in ev.values()]))
    return {"pass": n, "n": len(keys), "share": round(n / len(keys), 4), "baseline": round(base, 4),
            "non_discriminating": base >= 0.8 * n / len(keys), "meets_bar": n / len(keys) >= 0.60,
            "own_rank_median": float(np.median([v["own_rank"] for v in ev.values()]))}, ev


def headline_gated(strings, cons, keys):
    ev = G.evaluate_gated(strings, cons, keys)
    n = sum(v["pass"] for v in ev.values()); base = float(np.mean([v["baseline_share"] for v in ev.values()]))
    ranks = [v["own_rank"] for v in ev.values() if v["own_rank"] is not None]
    return {"pass": n, "n": len(keys), "share": round(n / len(keys), 4), "baseline": round(base, 4),
            "non_discriminating": base >= 0.8 * n / len(keys), "meets_bar": n / len(keys) >= 0.60,
            "own_rank_median": float(np.median(ranks))}, ev


def axis_misses(ev, cons):
    out = {a: {"above": 0, "below": 0} for a in L.CMP_AXES}
    for k, v in ev.items():
        env = L.envelope(cons[k]["string"])
        for p in v["measured_vertices"]:
            for a in L.CMP_AXES:
                if p[a] > env[a][1]:
                    out[a]["above"] += 1
                elif p[a] < env[a][0]:
                    out[a]["below"] += 1
    return out


def test(rec_dir: Path):
    prop = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    before = prop["constructed_before"]
    after = L.load_constructed()
    # Gate T0: the edit changed exactly the proposed (key, axis) pairs and nothing else
    want = {(r["key"], r["axis"]): r["new"] for r in prop["reseed"] if r["applied"]}
    got = {}
    for k in before:
        for a, v in before[k]["fixed_point"].items():
            if after[k]["fixed_point"][a] != v:
                got[(k, a)] = after[k]["fixed_point"][a]
    t0 = got == want
    print("T0 edit matches proposal:", t0, len(want), "pairs")
    if not t0:
        raise SystemExit(f"T0 failed: extra {set(got) - set(want)} missing {set(want) - set(got)} "
                         f"diff {[(p, got.get(p), want.get(p)) for p in set(got) | set(want) if got.get(p) != want.get(p)]}")
    feats_old, feats_new = feats_merged()
    s_old = {k: rows_of(v) for k, v in feats_old.items() if isinstance(v, dict) and "sections" in v}
    s_new = dict(s_old)
    for k in REPICKED:
        s_new[k] = rows_of(feats_new[k])
    s_new.pop("moth_tap", None)
    short = {k for k, v in s_new.items() if len(v) < 3}
    read_b = sorted(k for k in s_new if k not in short)
    read_a = sorted(k for k in read_b if k not in ("dawn_chorus", "log_on_fire"))
    res = {"job": "J-2395", "T0": t0, "n_reseeded_pairs": len(want), "ungated": {}, "gated": {}}

    # J-2372 sheet, unchanged (the D-0476 defeater's own test)
    for name, keys in (("read_b", read_b), ("read_a", read_a)):
        hb, evb = headline_ungated(s_new, before, keys)
        ha, eva = headline_ungated(s_new, after, keys)
        res["ungated"][name] = {"before": hb, "after": ha,
                                "fail_to_pass": sorted(k for k in keys if eva[k]["pass"] and not evb[k]["pass"]),
                                "pass_to_fail": sorted(k for k in keys if evb[k]["pass"] and not eva[k]["pass"]),
                                "axis_misses_before": axis_misses(evb, before), "axis_misses_after": axis_misses(eva, after)}
        if name == "read_b":
            res["ungated_per_key"] = {k: {"before": evb[k]["pass"], "after": eva[k]["pass"], "n_in_after": eva[k]["n_in"],
                                          "misses_after": eva[k]["misses"], "own_rank_after": eva[k]["own_rank"],
                                          "baseline_share_after": round(eva[k]["baseline_share"], 3)} for k in keys}
    ref = prop["ungated_reference"]
    r1 = (res["ungated"]["read_b"]["before"]["pass"], res["ungated"]["read_b"]["before"]["n"], res["ungated"]["read_b"]["before"]["baseline"]) == (ref["read_b"]["pass"], ref["read_b"]["n"], ref["read_b"]["baseline"])
    r2 = (res["ungated"]["read_a"]["before"]["pass"], res["ungated"]["read_a"]["before"]["n"], res["ungated"]["read_a"]["before"]["baseline"]) == (ref["read_a"]["pass"], ref["read_a"]["n"], ref["read_a"]["baseline"])
    res["T1_reproduces_J2397"] = r1 and r2
    print("T1 reproduces J-2397 read_a/read_b before re-seed:", r1, r2)

    # J-2383 gated sheet (secondary; in-sample for the re-seeded axes by construction)
    fs = {k: feats_new[k] for k in read_b}
    for k in ("moth_tap",):
        fs[k] = feats_old[k]
    gs, kept, _ = G.run_gate(X_DB, fs, rec_dir, sorted(fs))
    # reproduction of J-2383 on its own 63 (old files for morepork/wind, moth_tap in)
    j63 = sorted(json.loads(J2383.read_text(encoding="utf-8"))["per_key_x10"])
    fo = {k: feats_old[k] for k in j63}
    go, _, _ = G.run_gate(X_DB, fo, rec_dir, j63)
    h63, _ = headline_gated(go, before, j63)
    res["T2_reproduces_J2383"] = (h63["pass"], h63["n"]) == (23, 63)
    res["gated"]["J2383_63_before"] = h63
    print("T2 gated 63 before:", h63)
    for name, keys in (("read_b", read_b), ("read_a", read_a)):
        hb, evb = headline_gated(gs, before, keys)
        ha, eva = headline_gated(gs, after, keys)
        res["gated"][name] = {"before": hb, "after": ha,
                              "fail_to_pass": sorted(k for k in keys if eva[k]["pass"] and not evb[k]["pass"]),
                              "pass_to_fail": sorted(k for k in keys if evb[k]["pass"] and not eva[k]["pass"])}
    # archetype split, ungated read_b after
    s5 = {}
    for k, v in res["ungated_per_key"].items():
        a = after[k]["archetype"]; s5.setdefault(a, [0, 0, 0])
        s5[a][0] += int(v["before"]); s5[a][1] += int(v["after"]); s5[a][2] += 1
    res["ungated_read_b_by_archetype"] = {a: {"before": b, "after": c, "n": n} for a, (b, c, n) in sorted(s5.items())}
    reseeded = sorted({r["key"] for r in prop["reseed"] if r["applied"]})
    res["reseeded_keys"] = reseeded
    res["reseeded_keys_ungated_after"] = {"pass": sum(res["ungated_per_key"][k]["after"] for k in reseeded if k in res["ungated_per_key"]),
                                          "n": sum(1 for k in reseeded if k in res["ungated_per_key"])}
    RESULT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    for sheet in ("ungated", "gated"):
        for name in ("read_b", "read_a"):
            d = res[sheet][name]
            print(sheet, name, "before", d["before"], "\n   after", d["after"], "\n   f->P", d["fail_to_pass"], "P->f", d["pass_to_fail"])
    print("archetype", res["ungated_read_b_by_archetype"])
    print("reseeded keys ungated after", res["reseeded_keys_ungated_after"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("propose", "test"))
    ap.add_argument("--rec-dir", required=True)
    a = ap.parse_args()
    (propose if a.mode == "propose" else test)(Path(a.rec_dir))


if __name__ == "__main__":
    main()

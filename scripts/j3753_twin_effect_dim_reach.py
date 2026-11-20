"""
J-3753: quantify the stamp/idle twin-row effect on (1) rolling_intrinsic_dimension (3 arms) and
(2) mapping_census.marginal_reach (as-is vs stripped, several seeds). Read-only against data/.
Snapshot = first SNAP_ROWS lines of data/geometry_tuples.jsonl (the 171,723 rows J-3468 measured).
Run from the worktree: import core BEFORE lab_env is not needed here (no lab_env; nothing is written to data/).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
# UDMS also has a top-level package named core: import the UDMS-dependent reader FIRST, then purge its core.* and
# load Nascence's own core from this worktree.
sys.path.insert(0, str(ROOT / "scripts"))
import rolling_intrinsic_dimension as rid  # noqa: E402  (pulls C:/UDMS/scripts + UDMS core)
for _m in [m for m in sys.modules if m == "core" or m.startswith("core.")]:
    del sys.modules[_m]
sys.path = [p for p in sys.path if "UDMS" not in p]
sys.path.insert(0, str(ROOT))
import core  # noqa
assert str(ROOT).lower() in str(Path(core.__file__).resolve()).lower(), core.__file__
from core import mapping_census as mc
import j3468_twin_row_audit as tw

LIVE = Path(r"C:\Nascence\data\geometry_tuples.jsonl")
SNAP_ROWS = 171723
OUT = ROOT / "docs" / "lab" / "J-3753_data"


def load():
    rows = []
    with open(LIVE, encoding="utf-8") as f:
        for line in f:
            if len(rows) >= SNAP_ROWS:
                break
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def stamp_map(rows):
    """stamp idx -> claimed idle idx (same rule as flag_stamp_twins)."""
    m, claimed = {}, set()
    n = len(rows)
    for i, r in enumerate(rows):
        if r.get("source") != tw.STAMP_SOURCE:
            continue
        ts0 = float(r.get("ts") or 0)
        for j in range(i + 1, min(n, i + 1 + tw.TWIN_LOOKAHEAD)):
            c = rows[j]
            if c.get("source") != tw.IDLE_SOURCE or j in claimed:
                continue
            dt = float(c.get("ts") or 0) - ts0
            if dt < -0.05 or dt > tw.TWIN_WINDOW_S + 1e-6:
                continue
            if tw._is_prefix_twin(r.get("thought"), c.get("thought")):
                m[i] = j; claimed.add(j); break
    return m


def rolling(rows_subset, label, window=500, step=250):
    rs = sorted(rows_subset, key=lambda t: t.get("ts", 0.0))
    states = [rid.extract_state(r) for r in rs]
    n = len(states); out = []; i = 0
    while i + window <= n:
        res = rid.compute_intrinsic_dimensions(np.array(states[i:i + window]))
        out.append({"i": i, "ts0": rs[i].get("ts"), "cons": float(res["consensus_dim"]), "mle": float(res["dim_mle"]),
                    "twonn": float(res["dim_twonn"]), "pr": float(res["participation_ratio"])})
        i += step
    c = np.array([w["cons"] for w in out]); x = np.arange(len(c))
    slope = float(np.polyfit(x, c, 1)[0])
    s = {"label": label, "rows": n, "windows": len(out), "cons_min": float(c.min()), "cons_max": float(c.max()),
         "cons_first": float(c[0]), "cons_last": float(c[-1]), "cons_mean": float(c.mean()),
         "slope_per_window": slope, "total_drift": slope * (len(c) - 1),
         "mean_mle": float(np.mean([w["mle"] for w in out])), "mean_twonn": float(np.mean([w["twonn"] for w in out])),
         "mean_pr": float(np.mean([w["pr"] for w in out]))}
    return s, out


def main():
    t0 = time.time()
    rows = load(); print("rows", len(rows), flush=True)
    stamps = tw.flag_stamp_twins(rows); sm = stamp_map(rows)
    print("stamps", len(stamps), "mapped", len(sm), flush=True)
    stripped = [r for i, r in enumerate(rows) if i not in stamps]
    patched = []
    for i, r in enumerate(rows):
        if i in sm:
            r2 = dict(r); r2["unresolved"] = rows[sm[i]].get("unresolved", False); patched.append(r2)
        else:
            patched.append(r)
    res = {"snapshot_rows": len(rows), "stamps": len(stamps), "stripped_rows": len(stripped)}
    dims = {}
    for lab, sub in (("asis", rows), ("stripped", stripped), ("stamps_keep_idle_unresolved", patched)):
        s, w = rolling(sub, lab); dims[lab] = {"summary": s, "windows": w}; print(json.dumps(s), time.time() - t0, flush=True)
    res["rolling"] = {k: v["summary"] for k, v in dims.items()}
    # window-aligned comparison by timestamp: stripped windows hold ~2x the cycles, so also compare equal-CYCLE windows:
    # asis window of 500 rows ~ 250 cycles; stripped window of 250 rows ~ 250 cycles.
    s, w = rolling(stripped, "stripped_w250", window=250, step=125); dims["stripped_w250"] = {"summary": s, "windows": w}
    res["rolling"]["stripped_w250"] = s; print(json.dumps(s), flush=True)
    # per-month mean consensus (by window ts0)
    import datetime as dt
    def monthly(ws):
        d = {}
        for x in ws:
            d.setdefault(dt.datetime.fromtimestamp(x["ts0"], dt.timezone.utc).strftime("%Y-%m"), []).append(x["cons"])
        return {k: round(float(np.mean(v)), 3) for k, v in sorted(d.items())}
    res["rolling_monthly_cons"] = {k: monthly(v["windows"]) for k, v in dims.items()}
    (OUT / "rolling_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    # marginal reach
    mr = {}
    for lab, sub in (("asis", rows), ("stripped", stripped)):
        df = mc._dataframe(sub)
        mr[lab] = {}
        for seed in (42, 43, 44, 45, 46):
            r = mc.marginal_reach(df, sample_n=700, seed=seed)
            mr[lab][seed] = {"sample_n": r["sample_n"], "overlap_at_k": r["mean_overlap_at_k"], "reach": r["mean_marginal_reach_fraction"]}
            print(lab, seed, mr[lab][seed], time.time() - t0, flush=True)
    res["marginal_reach"] = mr
    (OUT / "rolling_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("done", time.time() - t0)

main()

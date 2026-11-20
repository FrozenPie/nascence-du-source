"""J-2363: summarise the four ab_J-2363_<i>_<arm>.json outputs (PURSUITS_LIGHT_READ off/on A/B) from $LAGH_SCRATCH."""
import json, os, sys, glob, statistics as st, pathlib
SP = pathlib.Path(os.environ["LAGH_SCRATCH"])
rows = []
for f in sorted(glob.glob(str(SP / "ab_J-2363_*_*.json"))):
    r = json.load(open(f)); j = r["J2363"]; c = r["components_ms"]
    g = lambda k, f="mean": (c.get(k) or {}).get(f)
    sp = r["raw"]["sub_periods"]; cp = r["raw"]["cli_periods"]; sb = r["raw"]["sub_bodies"]
    ssr = [x for x in j["sample_series_ms_raw"] if x > 0.05]
    load = j["host_load"]
    rows.append({"run": pathlib.Path(f).stem, "arm": j["arm"], "light_read": j["light_read"], "counts": j["status_counts"],
        "sample_series_calls": len(j["sample_series_ms_raw"]), "sample_series_fired_n": len(ssr),
        "sample_series_fired_mean_ms": round(st.mean(ssr), 2) if ssr else None,
        "sample_series_mean_ms_per_call": g("pursuits.sample_series"), "status_mean_ms": g("pursuits.status"), "status_n": g("pursuits.status", "n"),
        "load_n": g("pursuits._load", "n"), "load_mean_ms": g("pursuits._load"),
        "sensorium_tick_mean_ms": g("sensorium.tick"), "sensorium_tick_n": g("sensorium.tick", "n"),
        "sub_body_mean_ms": round(st.mean(sb), 1), "sub_body_median_ms": round(st.median(sb), 1),
        "sub_period_n": len(sp), "sub_period_mean": round(st.mean(sp), 4), "sub_period_median": round(st.median(sp), 4),
        "sub_excess_mean_s": round(st.mean(sp) - 5.0, 4), "sub_excess_median_s": round(st.median(sp) - 5.0, 4),
        "cli_period_mean": round(st.mean(cp), 4) if cp else None, "cli_period_median": round(st.median(cp), 4) if cp else None,
        "canary_mean_ms": r["canary_lag_ms"]["mean"], "canary_p99_ms": r["canary_lag_ms"]["p99"],
        "host_sys_cpu_mean": round(st.mean(x["sys_cpu_pct"] for x in load), 1) if load else None,
        "host_sys_cpu_max": max(x["sys_cpu_pct"] for x in load) if load else None,
        "self_cpu_mean": round(st.mean(x["self_cpu_pct"] for x in load), 1) if load else None,
        "other_python_n_max": max(x["other_python_n"] for x in load) if load else None,
        "other_python_cpu_sum_mean": round(st.mean(x["other_python_cpu_pct_sum"] for x in load), 1) if load else None,
        "other_python_cpu_sum_max": max(x["other_python_cpu_pct_sum"] for x in load) if load else None,
        "top_components_mean_x_n_ms": sorted(((k, round(v["sum"] / max(1, len(sp)), 1)) for k, v in c.items()), key=lambda t: -t[1])[:8]})
for x in rows: print(json.dumps(x))

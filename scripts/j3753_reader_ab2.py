"""J-3753 part 3b: pure-python readers A/B (j1471 exemplar proxy, eigenform variety, p1 transition index, twin field identity
for spurious_pattern/lane2). Read-only on live data; temp copies go to the scratchpad dir given as argv[1]."""
from __future__ import annotations
import json, sys, shutil, io, contextlib, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import j3468_twin_row_audit as tw
SP = Path(sys.argv[1]); LIVE = Path(r"C:\Nascence\data"); OUT = ROOT / "docs" / "lab" / "J-3753_data"
SNAP = 171723
rows = []
with open(LIVE / "geometry_tuples.jsonl", encoding="utf-8") as f:
    for line in f:
        if len(rows) >= SNAP: break
        if line.strip(): rows.append(json.loads(line))
stamps = tw.flag_stamp_twins(rows)
arms = {"asis": rows, "stripped": [r for i, r in enumerate(rows) if i not in stamps]}
res = {"snapshot_rows": len(rows), "stamps": len(stamps)}

# twin field identity (what spurious_pattern_audit / lane2 / p1 / j1471 read)
sm = {}
claimed = set()
for i in sorted(stamps):
    for j in range(i + 1, min(len(rows), i + 6)):
        if rows[j].get("source") == "idle" and j not in claimed and tw._is_prefix_twin(rows[i].get("thought"), rows[j].get("thought")) \
           and float(rows[j]["ts"]) - float(rows[i]["ts"]) <= 1.2 + 1e-6:
            sm[i] = j; claimed.add(j); break
def snap(r):
    c = (r.get("objects") or {}).get("cat") or {}
    return (r.get("place"), r.get("weather"), tuple(r.get("sounds") or []), r.get("cat_at") or c.get("location"), c.get("activity"), r.get("fire"), r.get("weather_dir"))
same = sum(1 for i, j in sm.items() if snap(rows[i]) == snap(rows[j]))
res["twin_snapshot_identity"] = {"pairs": len(sm), "identical_world_snapshot": same, "share": round(same / max(1, len(sm)), 4)}
fld = {}
for name, fn in {"place": lambda r: r.get("place"), "weather": lambda r: r.get("weather"), "sounds": lambda r: tuple(r.get("sounds") or []),
                 "weather_dir": lambda r: r.get("weather_dir"), "fire": lambda r: r.get("fire")}.items():
    fld[name] = round(sum(1 for i, j in sm.items() if fn(rows[i]) == fn(rows[j])) / max(1, len(sm)), 4)
res["twin_field_identity"] = fld

# p1 weather transitions
def trans(rs):
    prev = object(); n = 0
    for r in rs:
        v = r.get("weather")
        if v != prev: n += 1; prev = v
    return n
res["p1_weather_transitions"] = {k: trans(v) for k, v in arms.items()}

# j1471 on the first 95,093 rows (the original run's file) and on the whole snapshot
import j1471_i0082_exemplar_proxy_read as j
def run_j(rs, tag):
    p = SP / f"j1471_{tag}.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in rs: f.write(json.dumps(r) + "\n")
    j._GEOM_LOG = p; j._OUT_JSON = OUT / f"j1471_{tag}.json"; j._OUT_DIR = OUT
    b = io.StringIO()
    with contextlib.redirect_stdout(b): j.main()
    d = json.load(open(j._OUT_JSON, encoding="utf-8"))
    return {k: {"n": v["n_hearings"], "adm_per_1000": {T: t["admissions_per_1000_hearings"] for T, t in v["by_threshold"].items()},
                "wx_change_lift": {T: t["weather_change_lift"] for T, t in v["by_threshold"].items()}} for k, v in d["per_key"].items()}
pre = rows[:95093]; pre_st = [r for i, r in enumerate(pre) if i not in stamps]
res["j1471_prefix95093"] = {"asis": run_j(pre, "p95_asis"), "stripped": run_j(pre_st, "p95_stripped")}
res["j1471_snapshot"] = {"asis": run_j(arms["asis"], "full_asis"), "stripped": run_j(arms["stripped"], "full_stripped")}
(OUT / "reader_ab2_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8"); print("j1471 done", flush=True)

# eigenform variety
import eigenform_variety_read as ev
for tag, rs in arms.items():
    D = SP / tag
    with open(D / "geometry_tuples.jsonl", "w", encoding="utf-8") as f:
        for r in rs: f.write(json.dumps(r) + "\n")
    shutil.copy(LIVE / "fieldcraft_ledger.jsonl", D / "fieldcraft_ledger.jsonl")
    shutil.copy(LIVE / "letter_store" / "letters.jsonl", D / "letter_store" / "letters.jsonl")
    for p in (LIVE / "letters").glob("Letter_*.md"): shutil.copy(p, D / "letters" / p.name)
    v = ev.variety(str(D))
    days = v["daily"]
    ok = {d: x for d, x in days.items() if not x.get("excluded")}
    import statistics as st
    res.setdefault("eigenform_variety", {})[tag] = {"verdict": v["verdict"], "per_event": v["per_event"], "n_days_kept": len(ok),
        "mean_R": round(st.mean(x["R"] for x in ok.values()), 3), "mean_W": round(st.mean(x["W"] for x in ok.values()), 3),
        "mean_RW": round(st.mean(x["RW"] for x in ok.values() if x["RW"]), 4),
        "events": {n: {k: e[k]["pre_drop"] for k in ("R", "RW")} for n, e in v["events"].items()}}
(OUT / "reader_ab2_results.json").write_text(json.dumps(res, indent=1), encoding="utf-8"); print("done")

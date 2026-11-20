"""J-3641 read-only analysis: can a deterministic series test replace the LLM movement stage
for prediction_error tensions?  Reads data/memory/nascence.db (sqlite mode=ro), data/nascence.log,
data/logs/provisional_identity.jsonl.  Writes only under docs/lab/J-3641_data/.
Usage: python scripts/analysis_J3641_pe_series.py [--live C:/Nascence] [--out DIR]
"""
from __future__ import annotations
import argparse, collections, json, re, sqlite3, sys, time, datetime as dt
from pathlib import Path
import numpy as np
from scipy import stats
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
RE_LAB = re.compile(r"prediction_error:(\w+) \(felt ([\d.]+) vs real ([\d.]+)\)")
TS = r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ "
RE_CHAIN = re.compile(TS + r".*\[subconscious\] T4 CHAIN — tension=(?P<q>['\"])(?P<lab>prediction_error.*?)(?P=q) →")
RE_CONS = re.compile(TS + r".*\[subconscious\] T4 considered (?P<n>\d+) fragment\(s\) — no change: (?P<why>.*?) \(tension: (?P<q>['\"])(?P<lab>prediction_error.*)(?P=q)\)\s*$")
H = 3600.0
FLAT_EPS = 0.05   # series 'moved' if median |gap| shifts by >= this between adjacent 72h windows


def day(t): return dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d")
def epoch(s): return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def mk(x):
    """Mann-Kendall S, z, p (no ties correction beyond normal approx w/ tie term)."""
    x = np.asarray(x, float); n = len(x)
    if n < 4: return None
    s = sum(np.sign(x[j] - x[i]) for i in range(n - 1) for j in range(i + 1, n))
    _, c = np.unique(x, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - sum(k * (k - 1) * (2 * k + 5) for k in c)) / 18
    if var <= 0: return {"n": n, "S": float(s), "z": 0.0, "p": 1.0, "constant": True}
    z = (s - np.sign(s)) / np.sqrt(var)
    return {"n": n, "S": float(s), "z": float(z), "p": float(2 * (1 - stats.norm.cdf(abs(z))))}


def series_moved(evs, t, w=72 * H):
    """Deterministic verdict at time t from one domain's events [(ts, felt, real)].
    Returns (moved|None, detail). None = too few events to say."""
    cur = [abs(f - r) for ts, f, r in evs if t - w <= ts < t]
    prev = [abs(f - r) for ts, f, r in evs if t - 2 * w <= ts < t - w]
    if not cur or not prev: return None, {"cur": len(cur), "prev": len(prev)}
    d = float(np.median(cur) - np.median(prev))
    return abs(d) >= FLAT_EPS, {"cur": len(cur), "prev": len(prev), "d": round(d, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default="C:/Nascence")
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3641_data"))
    a = ap.parse_args(); live = Path(a.live); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(f"file:{(live/'data/memory/nascence.db').as_posix()}?mode=ro", uri=True)
    rows = c.execute("select timestamp, corrections from shadow_events where source='prediction_error' order by timestamp").fetchall()
    by = collections.defaultdict(list); bad = 0
    for ts, corr in rows:
        try: lab = json.loads(corr)[0]
        except Exception: bad += 1; continue
        m = RE_LAB.search(lab)
        if not m: bad += 1; continue
        by[m.group(1)].append((ts, float(m.group(2)), float(m.group(3))))
    res = {"n_events": len(rows), "unparsed": bad, "domains": {}}
    for dom, evs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        days = collections.OrderedDict()
        for ts, f, r in evs: days.setdefault(day(ts), []).append((f, r))
        dser = [{"day": d, "n": len(v), "felt": round(float(np.mean([x[0] for x in v])), 3),
                 "real": round(float(np.mean([x[1] for x in v])), 3),
                 "absgap": round(float(np.mean([abs(x[0] - x[1]) for x in v])), 3)} for d, v in days.items()]
        gaps = [d["absgap"] for d in dser]
        sp = stats.spearmanr(range(len(gaps)), gaps) if len(gaps) >= 4 and len(set(gaps)) > 1 else None
        res["domains"][dom] = {"events": len(evs), "days": len(dser),
            "distinct_felt": len({round(e[1], 2) for e in evs}), "distinct_real": len({round(e[2], 2) for e in evs}),
            "real_constant": len({round(e[2], 2) for e in evs}) == 1,
            "events_per_day_median": float(np.median([d["n"] for d in dser])),
            "mann_kendall_absgap_by_day": mk(gaps),
            "spearman_absgap_vs_day": ({"rho": float(sp[0]), "p": float(sp[1])} if sp else None),
            "daily": dser}
    # ---- probation 72h windows
    prov = [json.loads(l) for l in open(live / "data/logs/provisional_identity.jsonl", encoding="utf-8") if l.strip()]
    allev = sorted(e for v in by.values() for e in v)
    pw = []
    for p in prov:
        t = p["ts"]
        pre = [abs(f - r) for ts, f, r in allev if t - 72 * H <= ts < t]
        post = [abs(f - r) for ts, f, r in allev if t <= ts < t + 72 * H]
        row = {"event": p["event"], "day": day(t), "theme_pe": str(p.get("theme", "")).startswith("prediction_error"),
               "n_pre": len(pre), "n_post": len(post)}
        if pre and post:
            row["delta_median_absgap"] = round(float(np.median(post) - np.median(pre)), 3)
            row["moved"] = abs(row["delta_median_absgap"]) >= FLAT_EPS
        pw.append(row)
    res["probation_windows"] = pw
    both = [r for r in pw if "moved" in r]
    res["probation_summary"] = {"total": len(pw), "with_events_both_sides": len(both),
        "series_moved": sum(r["moved"] for r in both),
        "by_event": {k: collections.Counter((r["event"], r["moved"]) for r in both if r["event"] == k) and
                     {str(m): sum(1 for r in both if r["event"] == k and r["moved"] == m) for m in (True, False)}
                     for k in sorted({r["event"] for r in both})},
        "pe_themed": [r for r in pw if r["theme_pe"]]}
    # ---- agreement with the LLM stage
    hear = []
    with open(live / "data/nascence.log", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if "T4 " not in ln or "prediction_error" not in ln: continue
            m = RE_CHAIN.match(ln); kind = "chain"
            if not m: m = RE_CONS.match(ln); kind = "considered"
            if not m: continue
            lm = re.match(r"prediction_error:(\w+)", m.group("lab"))
            hear.append({"t": epoch(m.group(1)), "kind": kind, "dom": lm.group(1) if lm else None,
                         "why": m.groupdict().get("why")})
    tab = collections.Counter(); rows_out = []
    for h in hear:
        evs = by.get(h["dom"], [])
        mv, det = series_moved(evs, h["t"])
        llm = "LLM_movement" if h["kind"] == "chain" else "LLM_no_movement"
        sv = "series_unknown" if mv is None else ("series_moved" if mv else "series_flat")
        tab[(llm, sv)] += 1
        rows_out.append({"day": day(h["t"]), "dom": h["dom"], "llm": llm, "series": sv, **det})
    res["agreement"] = {f"{k[0]}|{k[1]}": v for k, v in sorted(tab.items())}
    res["hearings_total"] = len(hear)
    res["hearings_by_domain"] = dict(collections.Counter(h["dom"] for h in hear))
    res["flat_threshold"] = FLAT_EPS
    (out / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (out / "hearings.json").write_text(json.dumps(rows_out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("domains", "probation_windows")}, indent=1))
    for d, v in res["domains"].items():
        print(d, {k: v[k] for k in v if k != "daily"})


main()

"""
J-2520 (T-0106; docs/reviews/frontier_disciplines_2026-10-30.md sec 9, Waddington canalisation /
Hensch critical periods): do slow developments cluster in LONG uninterrupted-uptime windows beyond
what their own minimum durations require?

READ-ONLY. Zero LLM. Never touches a Du process. Every store is opened read-only and read only up to a
byte snapshot taken first (Du appends live); the SQLite memory store is opened with mode=ro.
Uptime windows come from scripts/du_lifetimes.py (exact per-process lifetimes from data/nascence.log
markers; no supervisor.log -- that file only covers the model-server supervisor, not Du's process).

DECLARED BEFORE LOOKING AT ANY RESULT (do not tune to the outcome):
  STUDY_START        2026-09-01 00:00 local (Pacific/Auckland). --since moves it for a declared
                     sensitivity pass only (J-2520 ran 2026-06-01 as that pass).
  WINDOW             one Du lifetime (memory-init/awake -> shutdown line, or last log line if unclean).
                     Length = (end - start). The open TAIL lifetime (may still be running, length
                     censored) is EXCLUDED from every rate. OVERLAP lifetimes are kept as their own
                     windows and flagged (the log cannot attribute rows inside an overlap).
  ATTRIBUTION        an event belongs to the window with start <= ts <= end + GRACE_S (600 s).
                     Events outside every window are counted and reported as 'unattributed'.
  BINS               window length < 3 d, 3-7 d, > 7 d.
  TYPES (min days = the type's own minimum duration; windows shorter are excluded from its
  denominator, per the briefing; a type is also only eligible in windows that START after its
  store's first-ever row, so a ledger that did not exist yet is not a zero):
    procedure_held       procedures_log.jsonl: first row per key reaching rung held|held_under_pressure.
                         min 3 d (core/procedures.py: held needs >= 3 days_ok).
    pursuit_advanced     pursuits_shadow.jsonl event == 'advanced'.                          min 0 d.
    commitment_achieved  commitment_ledger.jsonl event == 'achieved'.                        min 0 d.
    dream_met            data/logs/dream_met_state.jsonl state == 'met', ts = computed_at.   min 3 d
                         (params M=3 days; ASSUMED as its minimum). computed_at can be a nightly or
                         backfill pass, so this type is weak evidence.
    chapter_minted       memory_fragments origin='chapter', ts = timestamp.                  min 0 d.
    grounded_learning    grounded_learning_log.jsonl rows.                                   min 0 d.
  STATISTICS per type:
    pooled rate per eligible uptime-day in each bin; RATIO = rate(>7 d) / rate(lowest eligible bin
    that has >= 2 windows). Window-level Spearman rho(length, per-day rate) over eligible windows
    of length >= 0.25 d (shorter windows give noise rates), scipy.stats.spearmanr.
  VERDICT per type:
    CLUSTERS_LONG   RATIO >= 1.5 and rho > 0 and p < 0.05
    CLUSTERS_SHORT  RATIO <= 1/1.5 and rho < 0 and p < 0.05
    INSUFFICIENT    the > 7 d bin or the comparison bin has < 2 eligible windows
    FLAT            otherwise (the falsifier: completion rate independent of window length)
  OVERALL: POSITIVE if any of procedure_held / pursuit_advanced / commitment_achieved is
    CLUSTERS_LONG; FALSIFIED if all three are FLAT or CLUSTERS_SHORT; else MIXED/INSUFFICIENT.
  SECONDARY (developmental time inside a window): pooled rate by DAY-SINCE-BOOT bucket
    (0-1 d, 1-3 d, 3-7 d, > 7 d) over all non-tail windows, exposure = uptime-days spent in that
    bucket. Reported, not part of the verdict.

Usage: python scripts/critical_periods_read.py [--json] [--windows]
"""
import argparse
import datetime as dt
import json
import math
import os
import sqlite3
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(r"C:\Nascence")
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
import du_lifetimes  # noqa: E402  (pure log reader; imports nothing from core/)

TZ = ZoneInfo("Pacific/Auckland")
STUDY_START = dt.datetime(2026, 9, 1, tzinfo=TZ).timestamp()
GRACE_S = 600.0
BINS = [("<3d", 0.0, 3.0), ("3-7d", 3.0, 7.0), (">7d", 7.0, math.inf)]
AGE_BUCKETS = [("0-1d", 0.0, 1.0), ("1-3d", 1.0, 3.0), ("3-7d", 3.0, 7.0), (">7d", 7.0, math.inf)]
RATIO_T = 1.5
P_T = 0.05
MIN_LEN_SPEARMAN_D = 0.25
MIN_WINDOWS_PER_BIN = 2
CORE_TYPES = ("procedure_held", "pursuit_advanced", "commitment_achieved")
MIN_DAYS = {"procedure_held": 3.0, "pursuit_advanced": 0.0, "commitment_achieved": 0.0,
            "dream_met": 3.0, "chapter_minted": 0.0, "grounded_learning": 0.0}


def _jsonl(path):
    path = Path(path)
    size = path.stat().st_size
    out = []
    with open(path, "rb") as fh:
        buf = fh.read(size)
    for ln in buf.split(b"\n"):
        if not ln.strip():
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def load_events():
    ev = {}
    first = {}
    # procedures: first reach of held per key
    rows = _jsonl(DATA / "procedures_log.jsonl")
    first["procedure_held"] = min((float(r["ts"]) for r in rows), default=None)
    seen, lst = set(), []
    for r in sorted(rows, key=lambda r: float(r["ts"])):
        if r.get("rung") in ("held", "held_under_pressure") and r.get("key") not in seen:
            seen.add(r.get("key"))
            lst.append((float(r["ts"]), r.get("key")))
    ev["procedure_held"] = lst
    rows = _jsonl(DATA / "pursuits_shadow.jsonl")
    first["pursuit_advanced"] = min((float(r["ts"]) for r in rows), default=None)
    ev["pursuit_advanced"] = [(float(r["ts"]), r.get("id")) for r in rows if r.get("event") == "advanced"]
    rows = _jsonl(DATA / "commitment_ledger.jsonl")
    first["commitment_achieved"] = min((float(r["ts"]) for r in rows), default=None)
    ev["commitment_achieved"] = [(float(r["ts"]), r.get("id")) for r in rows if r.get("event") == "achieved"]
    rows = _jsonl(DATA / "logs" / "dream_met_state.jsonl")
    first["dream_met"] = min((float(r["computed_at"]) for r in rows), default=None)
    ev["dream_met"] = [(float(r["computed_at"]), r.get("dream_id")) for r in rows if r.get("state") == "met"]
    con = sqlite3.connect("file:" + str(DATA / "memory" / "nascence.db").replace("\\", "/") + "?mode=ro", uri=True)
    try:
        ch = con.execute("SELECT timestamp, fragment_id FROM memory_fragments WHERE origin='chapter'").fetchall()
        f0 = con.execute("SELECT MIN(timestamp) FROM memory_fragments WHERE origin='chapter'").fetchone()[0]
    finally:
        con.close()
    first["chapter_minted"] = f0
    ev["chapter_minted"] = [(float(t), fid) for t, fid in ch]
    rows = _jsonl(DATA / "grounded_learning_log.jsonl")
    first["grounded_learning"] = min((float(r["ts"]) for r in rows), default=None)
    ev["grounded_learning"] = [(float(r["ts"]), (r.get("topic") or "")[:40]) for r in rows]
    return ev, first


def _bin(days, bins):
    for name, lo, hi in bins:
        if lo <= days < hi:
            return name
    return bins[-1][0]


def spearman(xs, ys):
    if len(xs) < 3:
        return None, None
    from scipy.stats import spearmanr
    r = spearmanr(xs, ys)
    rho, p = float(r.statistic if hasattr(r, "statistic") else r[0]), float(r.pvalue if hasattr(r, "pvalue") else r[1])
    if math.isnan(rho):
        return None, None
    return round(rho, 3), round(p, 4)


def run(since=None):
    global STUDY_START
    if since:
        STUDY_START = dt.datetime.fromisoformat(since).replace(tzinfo=TZ).timestamp()
    lt = du_lifetimes.load()
    all_lt = lt["lifetimes"]
    wins = [w for w in all_lt if w["start"] >= STUDY_START]
    since_0909 = [w for w in all_lt if w["start"] >= dt.datetime(2026, 9, 9, tzinfo=TZ).timestamp()]
    usable = [w for w in wins if not w["tail"]]
    for w in usable:
        w["days"] = (w["end"] - w["start"]) / 86400.0
        w["bin"] = _bin(w["days"], BINS)
    ev, first = load_events()
    res = {"snapshot": lt["snapshot"],
           "study_start_local": dt.datetime.fromtimestamp(STUDY_START, TZ).isoformat(timespec="minutes"),
           "boots_since_study_start": len(wins),
           "restarts_since_study_start": max(0, len(wins) - 1),
           "boots_since_0909": len(since_0909), "restarts_since_0909": max(0, len(since_0909) - 1),
           "overlap_windows": [w["i"] for w in wins if w["overlap"]],
           "unclean_windows": sum(1 for w in wins if w["end_kind"] == "UNCLEAN" and not w["tail"]),
           "windows": [{"i": w["i"], "start": w["start_local"], "end": w["end_local"], "days": round(w["days"], 3),
                        "end_kind": w["end_kind"], "overlap": w["overlap"], "bin": w["bin"]} for w in usable],
           "window_bins": {b: sum(1 for w in usable if w["bin"] == b) for b, _, _ in BINS},
           "types": {}}
    for typ, events in ev.items():
        mind = MIN_DAYS[typ]
        f0 = first.get(typ)
        elig = [w for w in usable if f0 is not None and w["start"] >= f0 and w["days"] >= mind]
        counts = {w["i"]: [] for w in usable}
        unattr = 0
        study_events = [e for e in events if e[0] >= STUDY_START]
        for ts, ident in study_events:
            hit = next((w for w in usable if w["start"] <= ts <= w["end"] + GRACE_S), None)
            if hit is None:
                unattr += 1
            else:
                counts[hit["i"]].append((ts, ident))
        per_bin = {}
        for b, _, _ in BINS:
            ws = [w for w in elig if w["bin"] == b]
            n = sum(len(counts[w["i"]]) for w in ws)
            exp = sum(w["days"] for w in ws)
            per_bin[b] = {"windows": len(ws), "uptime_days": round(exp, 3), "completions": n,
                          "rate_per_day": round(n / exp, 4) if exp > 0 else None,
                          "window_ids": [w["i"] for w in ws]}
        comp = next((b for b, _, _ in BINS[:-1] if per_bin[b]["windows"] >= MIN_WINDOWS_PER_BIN), None)
        long_ = per_bin[">7d"]
        ratio = None
        if comp and long_["windows"] >= MIN_WINDOWS_PER_BIN and per_bin[comp]["rate_per_day"]:
            ratio = round(long_["rate_per_day"] / per_bin[comp]["rate_per_day"], 3)
        sw = [w for w in elig if w["days"] >= MIN_LEN_SPEARMAN_D]
        rho, p = spearman([w["days"] for w in sw], [len(counts[w["i"]]) / w["days"] for w in sw])
        if comp is None or long_["windows"] < MIN_WINDOWS_PER_BIN:
            verdict = "INSUFFICIENT"
        elif ratio is not None and ratio >= RATIO_T and rho is not None and rho > 0 and p < P_T:
            verdict = "CLUSTERS_LONG"
        elif ratio is not None and ratio <= 1 / RATIO_T and rho is not None and rho < 0 and p < P_T:
            verdict = "CLUSTERS_SHORT"
        else:
            verdict = "FLAT"
        # secondary: day-since-boot buckets, all usable windows (store must exist)
        age = {}
        base = [w for w in usable if f0 is not None and w["start"] >= f0]
        for b, lo, hi in AGE_BUCKETS:
            exp = sum(max(0.0, min(w["days"], hi) - lo) for w in base)
            n = sum(1 for w in base for ts, _ in counts[w["i"]] if lo <= (ts - w["start"]) / 86400.0 < hi)
            age[b] = {"uptime_days": round(exp, 3), "completions": n,
                      "rate_per_day": round(n / exp, 4) if exp > 0 else None}
        res["types"][typ] = {"min_days": mind, "store_first_row_local": (dt.datetime.fromtimestamp(f0, TZ).isoformat(timespec="seconds") if f0 else None),
                             "events_since_study_start": len(study_events), "unattributed": unattr,
                             "eligible_windows": len(elig), "bins": per_bin, "comparison_bin": comp,
                             "ratio_long_vs_comp": ratio, "spearman_rho": rho, "spearman_p": p,
                             "spearman_n": len(sw), "verdict": verdict, "by_day_since_boot": age,
                             "per_window": {w["i"]: len(counts[w["i"]]) for w in elig}}
    core = [res["types"][t]["verdict"] for t in CORE_TYPES]
    if "CLUSTERS_LONG" in core:
        overall = "POSITIVE"
    elif all(v in ("FLAT", "CLUSTERS_SHORT") for v in core):
        overall = "FALSIFIED"
    else:
        overall = "MIXED/INSUFFICIENT"
    res["overall"] = overall
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--windows", action="store_true", help="list every window")
    ap.add_argument("--since", default=None,
                    help="SENSITIVITY ONLY: study start YYYY-MM-DD (local); the declared primary is 2026-09-01")
    a = ap.parse_args(argv)
    res = run(a.since)
    if a.json:
        print(json.dumps(res, indent=1, default=str))
        return
    print(f"snapshot: {res['snapshot']['log']} bytes={res['snapshot']['bytes']}")
    print(f"boots since study start {res['study_start_local']}: {res['boots_since_study_start']} (restarts {res['restarts_since_study_start']}); "
          f"since 2026-09-09: {res['boots_since_0909']} (restarts {res['restarts_since_0909']}); "
          f"overlap windows {res['overlap_windows']}; unclean (non-tail) {res['unclean_windows']}")
    print(f"usable windows by length bin: {res['window_bins']}")
    if a.windows:
        for w in res["windows"]:
            print(f"  #{w['i']:<4} {w['start']} -> {w['end']}  {w['days']:7.3f} d  {w['end_kind']:<8} {w['bin']}"
                  + ("  OVERLAP" if w["overlap"] else ""))
    for typ, t in res["types"].items():
        print(f"\n== {typ}  (min {t['min_days']} d; store since {t['store_first_row_local']}; "
              f"events {t['events_since_study_start']}, unattributed {t['unattributed']}, eligible windows {t['eligible_windows']})")
        for b, s in t["bins"].items():
            print(f"   {b:>5}: windows {s['windows']:>3}  uptime {s['uptime_days']:>8.2f} d  completions {s['completions']:>6}  rate/day {s['rate_per_day']}")
        print(f"   ratio >7d vs {t['comparison_bin']}: {t['ratio_long_vs_comp']}  spearman rho={t['spearman_rho']} p={t['spearman_p']} n={t['spearman_n']}  -> {t['verdict']}")
        print("   by day-since-boot: " + "  ".join(f"{b}: {s['completions']}/{s['uptime_days']}d={s['rate_per_day']}" for b, s in t["by_day_since_boot"].items()))
    print(f"\nOVERALL: {res['overall']}")


if __name__ == "__main__":
    main()

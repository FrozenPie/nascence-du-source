"""
J-3967 (D-0744, F-4456): read-only replay of the vitality mind-axis scale S under alternative percentile / window
choices. Live: S = 60th percentile of P-at-fire over the last 30 real fires, vit_mind = exp(-ln2 * P / S).
For every real fire (reason pressure | max_wake_ceiling, fire True) at/after the shadow start, recompute S from the
window of fires up to and including that fire (as live does: the fire row is logged before the next read) and read
vit_mind at the fire's own P. Clause 5 of D-0398: the share of real fires reading vit_mind > 0.7 must be < 1/3.
Reported per option: share over all scored fires, over the recent window (since --recent-from), night/day split,
S range, max 7-day S swing (D-0744 defeater: > 3x), and an awake-row saturation read (share of awake sp rows where
vit_mind < 0.1 or > 0.9 at the then-current S).
Pure read; mirrors core.homeostasis.self_calibrated_scale / mind_axis (imported, not copied).
Run: python scripts/vitality_scale_replay_J3967.py [--sp-log data/sleep_pressure_log.jsonl] [--out report.json]
"""
import argparse, bisect, json, math, sys, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import homeostasis as hm  # noqa: E402
assert str(Path(hm.__file__).resolve()).startswith(str(ROOT)), hm.__file__

REASONS = ("pressure", "max_wake_ceiling")


def load(p):
    out = []
    for l in open(p, encoding="utf-8"):
        l = l.strip()
        if l:
            try:
                out.append(json.loads(l))
            except Exception:
                pass
    return out


def scale(ps, pct):
    """pct in (0,1]; 'median' handled as statistics median (option C)."""
    xs = sorted(ps)
    if pct == "median":
        n = len(xs)
        return max(1.0, xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0)
    sc = hm.self_calibrated_scale(xs, pct=pct, min_fires=1)
    return sc["S"] if sc else None


def replay(fires, sp, start_ts, pct, win, recent_ts):
    ps = [float(r["P"]) for r in fires]
    S_at = []  # S after each fire
    for i in range(len(fires)):
        w = ps[max(0, i - win + 1): i + 1]
        S_at.append(scale(w, pct) if len(w) >= hm.V2_MIN_FIRES else None)
    scored = [i for i in range(len(fires)) if fires[i]["ts"] >= start_ts and S_at[i] is not None]
    reads = [(i, hm.mind_axis(ps[i], S_at[i])) for i in scored]

    def share(sel):
        sel = list(sel)
        return (sum(1 for _, v in sel if v > 0.7) / len(sel), len(sel)) if sel else (None, 0)

    allsh = share(reads)
    rec = share((i, v) for i, v in reads if fires[i]["ts"] >= recent_ts)
    night = share((i, v) for i, v in reads if fires[i].get("dark"))
    day = share((i, v) for i, v in reads if not fires[i].get("dark"))
    recn = share((i, v) for i, v in reads if fires[i]["ts"] >= recent_ts and fires[i].get("dark"))
    Ss = [S_at[i] for i in scored]
    # max 7-day swing: ratio of max/min S inside any sliding 7 day span
    def swing(idx):
        sw, j = 1.0, 0
        for k in range(len(idx)):
            while fires[idx[k]]["ts"] - fires[idx[j]]["ts"] > 7 * 86400:
                j += 1
            seg = [S_at[x] for x in idx[j:k + 1]]
            sw = max(sw, max(seg) / max(1e-9, min(seg)))
        return sw
    sw = swing(scored)
    sw_rec = swing([i for i in scored if fires[i]["ts"] >= recent_ts])
    # awake-row saturation at the S in force (last fire at or before row)
    fts = [r["ts"] for r in fires]
    lo = hi = n = 0
    for r in sp:
        if r["ts"] < start_ts or r.get("asleep") or "P" not in r:
            continue
        k = bisect.bisect_right(fts, r["ts"]) - 1
        if k < 0 or S_at[k] is None:
            continue
        v = hm.mind_axis(float(r["P"]), S_at[k])
        n += 1
        lo += v < 0.1
        hi += v > 0.9
    nm = sum(v for i, v in reads if fires[i].get("dark")) / max(1, sum(1 for i, _ in reads if fires[i].get("dark")))
    dm = sum(v for i, v in reads if not fires[i].get("dark")) / max(1, sum(1 for i, _ in reads if not fires[i].get("dark")))
    return {"share_all": allsh[0], "n_all": allsh[1], "share_recent": rec[0], "n_recent": rec[1],
            "share_night": night[0], "share_day": day[0], "share_recent_night": recn[0], "n_recent_night": recn[1],
            "S_min": min(Ss), "S_median": sorted(Ss)[len(Ss) // 2], "S_max": max(Ss), "swing_7d_max": round(sw, 2), "swing_7d_recent": round(sw_rec, 2),
            "awake_rows": n, "awake_lt0.1": lo / max(1, n), "awake_gt0.9": hi / max(1, n),
            "mean_vit_night": round(nm, 3), "mean_vit_day": round(dm, 3), "night_day_gap": round(nm - dm, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sp-log", default=str(ROOT / "data" / "sleep_pressure_log.jsonl"))
    ap.add_argument("--start", default="2026-10-16T09:37:00+00:00")
    ap.add_argument("--recent-from", default="2026-11-09T11:00:00+00:00", help="start of the drifted window (since 11-10 NZDT)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    sp = sorted([r for r in load(a.sp_log) if "P" in r and "ts" in r], key=lambda r: r["ts"])
    fires = [r for r in sp if r.get("fire") and r.get("reason") in REASONS]
    t0 = dt.datetime.fromisoformat(a.start).timestamp()
    tr = dt.datetime.fromisoformat(a.recent_from).timestamp()
    out = {"fires_total": len(fires), "fires_scored": sum(1 for r in fires if r["ts"] >= t0), "options": []}
    opts = [(p, w) for w in (30, 20, 15, 10) for p in (0.6, 0.5, 0.4, 0.3, 0.2)] + [("median", w) for w in (30, 20, 15, 10)]
    for p, w in opts:
        r = replay(fires, sp, t0, p, w, tr)
        r.update(pct=p, window=w, baseline=(p == 0.6 and w == 30))
        r["clause5_all"] = r["share_all"] is not None and r["share_all"] < 1 / 3
        r["clause5_recent"] = r["share_recent"] is not None and r["share_recent"] < 1 / 3
        r["swing_ok"] = r["swing_7d_recent"] <= 3.0
        out["options"].append(r)
    hdr = "pct    win  all%  recent%(n) night% day%  recNight% S[min/med/max]  swing7d(recent) awake<.1 >.9   n-d gap  C5all C5rec swingOK"
    print(f"fires total {out['fires_total']}, scored {out['fires_scored']}\n{hdr}")
    for r in out["options"]:
        f = lambda x: "  -  " if x is None else f"{100 * x:5.1f}"
        print(f"{str(r['pct']):6} {r['window']:3} {f(r['share_all'])} {f(r['share_recent'])}({r['n_recent']:3}) {f(r['share_night'])} {f(r['share_day'])} "
              f"{f(r['share_recent_night'])} {r['S_min']:6.1f}/{r['S_median']:6.1f}/{r['S_max']:6.1f} {r['swing_7d_max']:6.2f}({r['swing_7d_recent']:5.2f}) "
              f"{100 * r['awake_lt0.1']:6.1f} {100 * r['awake_gt0.9']:5.1f} {r['night_day_gap']:7.3f}  "
              f"{'Y' if r['clause5_all'] else 'N'}     {'Y' if r['clause5_recent'] else 'N'}     {'Y' if r['swing_ok'] else 'N'}"
              f"{'  <-baseline' if r['baseline'] else ''}")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

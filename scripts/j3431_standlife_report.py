"""J-3431: report from the rows file written by j3431_standlife_downtime.py (also recomputes at several gap thresholds)."""
import sys, json, statistics as st, subprocess, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import j3431_standlife_downtime as m

def run(gap):
    m.GAP_S = gap
    lines = m.parse_log() if not hasattr(run, "lines") else run.lines
    run.lines = lines
    iv = m.up_intervals(lines, gap, m.T_FROM); starts = [x[0] for x in iv]
    rows = [json.loads(l) for l in open(m.DATA / "commitment_ledger.jsonl", encoding="utf-8") if l.strip()]
    formed = {r["id"]: r for r in rows if r.get("event") == "formed"}
    out = []
    lo, hi = iv[0][0], iv[-1][1]
    for r in rows:
        if r.get("event") != "dissolved":
            continue
        f = formed.get(r["id"], {})
        if not f.get("load_bearing"):
            continue
        held = r["ts"] - r["lifespan_seconds"]
        if held < lo or r["ts"] > hi:
            continue
        out.append(dict(id=r["id"], ts=r["ts"], life=r["lifespan_seconds"], scans=r.get("lifespan_scans", 0) or 0,
                        reaff=int(r.get("reaffirmed", 0) or 0), up=m.uptime_between(iv, starts, held, r["ts"]),
                        stmt=r["statement"][:70]))
    return out, iv

def cnt(rs, f): return sum(1 for r in rs if f(r))

def table(rs, label):
    N, S = 1800.0, 20
    wall = lambda r: r["life"] >= N
    up = lambda r: r["up"] >= N
    sc = lambda r: r["scans"] >= S
    ra = lambda r: r["reaff"] >= 1
    print(f"--- {label}: n={len(rs)} load-bearing dissolves with held..dissolve inside the covered log window")
    print(" pass wall>=1800s            :", cnt(rs, wall))
    print(" pass uptime>=1800s          :", cnt(rs, up))
    print(" wall-pass but uptime-fail   :", cnt(rs, lambda r: wall(r) and not up(r)))
    print(" wall-pass, uptime-fail, scans<20:", cnt(rs, lambda r: wall(r) and not up(r) and not sc(r)))
    print(" pass scans>=20              :", cnt(rs, sc))
    print(" scans>=20 and wall<1800     :", cnt(rs, lambda r: sc(r) and not wall(r)))
    print(" wall-pass but scans<20      :", cnt(rs, lambda r: wall(r) and not sc(r)))
    print(" wall-pass but scans<10      :", cnt(rs, lambda r: wall(r) and r["scans"] < 10))
    print(" reaffirmed>=1               :", cnt(rs, ra))
    print(" GATE(open sit) wall|reaff   :", cnt(rs, lambda r: wall(r) or ra(r)), " up|reaff:", cnt(rs, lambda r: up(r) or ra(r)),
          " scans|reaff:", cnt(rs, lambda r: sc(r) or ra(r)))
    dn = [r["life"] - r["up"] for r in rs]
    print(" downtime inside stand life: stands with >60s down:", cnt(rs, lambda r: r["life"] - r["up"] > 60),
          " >600s:", cnt(rs, lambda r: r["life"] - r["up"] > 600), " >1800s:", cnt(rs, lambda r: r["life"] - r["up"] > 1800))

if __name__ == "__main__":
    for gap in (300.0, 600.0, 1800.0, 1e12):
        rs, iv = run(gap)
        table(rs, f"gap={gap:.0f}s ({len(iv)} up intervals, up total {sum(b-a for a,b in iv)/3600:.0f} h)")
        if gap == 600.0:
            base = rs
    rs = base
    cut = datetime.datetime(2026, 10, 23).timestamp()
    table([r for r in rs if r["ts"] >= cut], "gap=600 last 14 days (ts>=2026-10-23)")
    # seconds per scan
    sp = [r["up"] / r["scans"] for r in rs if r["scans"] >= 3]
    print("uptime-seconds per scan (stands w/ >=3 scans): median %.0f  p25 %.0f p75 %.0f  n=%d" % (
        st.median(sp), st.quantiles(sp, n=4)[0], st.quantiles(sp, n=4)[2], len(sp)))
    wp = [r["life"] / r["scans"] for r in rs if r["scans"] >= 3]
    print("wall-seconds per scan: median %.0f p75 %.0f p90 %.0f" % (st.median(wp), st.quantiles(wp, n=4)[2], st.quantiles(wp, n=10)[8]))
    print("wall-pass but uptime-fail (gap=600) list:")
    for r in sorted(rs, key=lambda r: r["ts"]):
        if r["life"] >= 1800 and r["up"] < 1800:
            print("  %s life=%6.0f up=%6.0f scans=%3d reaff=%d  %s" % (datetime.datetime.fromtimestamp(r["ts"]).strftime("%m-%d %H:%M"), r["life"], r["up"], r["scans"], r["reaff"], r["stmt"].encode("ascii", "replace").decode()))

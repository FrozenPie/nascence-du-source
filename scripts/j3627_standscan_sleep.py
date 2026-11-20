"""J-3627: why did stands with >=30 min up-time have <20 scans?  Read-only.
Separates in-process SLEEP from up-time (J-3431 did not). Inputs: data/nascence.log, data/commitment_ledger.jsonl.
Sleep interval = 'entering ... Sleep State' line .. next '[night] waking:' line (cut at a boot / next entering / 4 h).
Usage: python scripts/j3627_standscan_sleep.py [DATA_DIR]"""
import sys, re, json, datetime, statistics as st, bisect
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import j3431_standlife_downtime as m
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\Nascence\data")
m.DATA = DATA
TS = m.TS
THOUGHT = re.compile(r"\[nascence\.monologue\] \[monologue\] \([^)]{1,80}\) ")
def parse():
    lines, sl, th = [], [], []
    cur = None
    for line in open(DATA / "nascence.log", encoding="utf-8", errors="replace"):
        mm = TS.match(line)
        if not mm: continue
        t = datetime.datetime.strptime(mm.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(mm.group(2)) / 1000
        if lines and t < lines[-1][0] - 5: continue
        k = ""
        if "Memory store initialised" in line and ("data" + chr(92) + "memory" + chr(92) + "nascence.db") in line: k = "boot"
        elif "Nascence shutting down" in line: k = "shut"
        lines.append((t, k))
        if k in ("boot", "shut") and cur is not None:
            sl.append((cur, t)); cur = None
        if "entering" in line and "Sleep State" in line and "[nascence.monologue]" in line:
            if cur is not None: sl.append((cur, t))
            cur = t
        elif "[night] waking:" in line and cur is not None:
            sl.append((cur, t)); cur = None
        elif cur is not None and t - cur > 4 * 3600:
            sl.append((cur, cur + 4 * 3600)); cur = None
        if THOUGHT.search(line): th.append(t)
    return lines, sl, th
def overlap(iv, starts, a, b):
    return m.uptime_between(iv, starts, a, b)
def main():
    lines, sl, th = parse()
    iv = m.up_intervals(lines, 600.0, m.T_FROM); starts = [x[0] for x in iv]
    sstarts = [x[0] for x in sl]
    rows = [json.loads(l) for l in open(DATA / "commitment_ledger.jsonl", encoding="utf-8") if l.strip()]
    formed = {r["id"]: r for r in rows if r.get("event") == "formed"}
    lo, hi = iv[0][0], iv[-1][1]
    out = []
    for r in rows:
        if r.get("event") != "dissolved" or not formed.get(r["id"], {}).get("load_bearing"): continue
        a = r["ts"] - r["lifespan_seconds"]; b = r["ts"]
        if a < lo or b > hi: continue
        up = m.uptime_between(iv, starts, a, b)
        sleep = m.uptime_between(sl, sstarts, a, b)   # sleep seconds inside window (sl intervals disjoint)
        sc = r.get("lifespan_scans", 0) or 0
        nth = bisect.bisect_right(th, b) - bisect.bisect_left(th, a)
        out.append(dict(id=r["id"], a=a, b=b, up=up, sleep=sleep, awake=max(up - sleep, 0.0), scans=sc, thoughts=nth))
    return out, sl
def q(x):
    x = sorted(x); return "n=%d med %.0f p25 %.0f p75 %.0f" % (len(x), st.median(x), x[len(x)//4], x[3*len(x)//4]) if len(x) >= 4 else str(x)
if __name__ == "__main__":
    out, sl = main()
    print("sleep intervals parsed:", len(sl), " total h: %.0f" % (sum(b - a for a, b in sl) / 3600),
          " median min %.0f" % (st.median([(b - a) / 60 for a, b in sl])))
    N, S = 1800.0, 20
    grp = lambda r: r["up"] >= N and r["scans"] < S
    slow = [r for r in out if grp(r)]; rest = [r for r in out if r["up"] >= N and r["scans"] >= S]
    for name, g in (("SLOW (up>=1800, scans<20)", slow), ("PASS (up>=1800, scans>=20)", rest)):
        g3 = [r for r in g if r["scans"] >= 3]
        print("==", name, len(g))
        print(" sleep share of up:", "%.2f" % (sum(r["sleep"] for r in g) / sum(r["up"] for r in g)))
        print(" up s/scan   :", q([r["up"] / r["scans"] for r in g3]))
        print(" awake s/scan:", q([r["awake"] / r["scans"] for r in g3]))
        print(" thoughts/scan:", q([r["thoughts"] / r["scans"] for r in g3 if r["thoughts"]]))
        print(" stands with >=600s sleep inside:", sum(1 for r in g if r["sleep"] >= 600), "of", len(g))
    # the core question: is scans-per-awake-time stable enough? all stands >=3 scans
    allg = [r for r in out if r["scans"] >= 3 and r["awake"] > 300]
    print("== ALL load-bearing stands, >=3 scans, awake>300s")
    print(" up s/scan   :", q([r["up"] / r["scans"] for r in allg]))
    print(" awake s/scan:", q([r["awake"] / r["scans"] for r in allg]))
    # would a awake-time gate (1800 s awake) agree with scans>=20 better than up-time?
    for lab, f in (("up>=1800", lambda r: r["up"] >= N), ("awake>=1800", lambda r: r["awake"] >= N)):
        both = sum(1 for r in out if f(r) and r["scans"] >= S); onlyt = sum(1 for r in out if f(r) and r["scans"] < S)
        onlys = sum(1 for r in out if not f(r) and r["scans"] >= S)
        print(" %-12s both=%d time-only=%d scans-only=%d" % (lab, both, onlyt, onlys))
    cut = datetime.datetime(2026, 10, 1).timestamp()
    for lab, sel in (("before 10-01", [r for r in out if r["b"] < cut]), ("since 10-01", [r for r in out if r["b"] >= cut])):
        g = [r for r in sel if r["scans"] >= 3 and r["awake"] > 300]
        print("==", lab, "n=%d" % len(sel), "slow(up>=1800,scans<20)=%d" % sum(1 for r in sel if grp(r)),
              "| up s/scan", q([r["up"] / r["scans"] for r in g]), "| awake s/scan", q([r["awake"] / r["scans"] for r in g]))
    print("SLOW list: id start up sleep awake scans thoughts")
    for r in sorted(slow, key=lambda r: r["a"]):
        print(" %s %s up=%5.0f sleep=%5.0f awake=%5.0f scans=%2d thoughts=%3d" % (r["id"], datetime.datetime.fromtimestamp(r["a"]).strftime("%m-%d %H:%M"), r["up"], r["sleep"], r["awake"], r["scans"], r["thoughts"]))

def transport_errors(DATA=DATA):
    """times of model_client 'transport error' / 'all servers exhausted' lines (slow-hub proxy)"""
    ts = []
    for line in open(DATA / "nascence.log", encoding="utf-8", errors="replace"):
        if "transport error" in line or "all servers exhausted" in line:
            mm = TS.match(line)
            if mm: ts.append(datetime.datetime.strptime(mm.group(1), "%Y-%m-%d %H:%M:%S").timestamp())
    return ts
def transport_report(out):
    ts = transport_errors()
    def n(r): return bisect.bisect_right(ts, r["b"]) - bisect.bisect_left(ts, r["a"])
    N, S = 1800.0, 20
    for lab, g in (("SLOW awake-only (sleep<600, up>=1800, scans<20)", [r for r in out if r["up"] >= N and r["scans"] < S and r["sleep"] < 600]),
                   ("PASS no-sleep (sleep<600, up>=1800, scans>=20)", [r for r in out if r["up"] >= N and r["scans"] >= S and r["sleep"] < 600])):
        e = [n(r) / (r["awake"] / 3600.0) for r in g if r["awake"] > 600]
        print("==", lab, len(g), "transport errors per awake hour:", q(e), " stands with >=1 error:", sum(1 for r in g if n(r) >= 1))
if __name__ == "__main__":
    transport_report(out)

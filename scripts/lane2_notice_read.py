#!/usr/bin/env python
"""Full-log read of D-0281's Lane 2 notice judge (J-1395, 2026-10-03).  READ-ONLY: opens two logs, writes nothing.

Why this exists: core.lane2.status() computes notice_judged_n / notice_contradiction_rate over only the last
2000 shadow-log ROWS (all kinds; ~30% are ticks), so it can never show the judged n above 300 that D-0281's
low-rate defeater needs.  This reader scans the whole files instead and also prints the other two defeater
inputs D-0281 names (judge_panel latency for context lane2:notice, and a reproducible 20-row hand-read sample).

    python scripts/lane2_notice_read.py                      # numbers only
    python scripts/lane2_notice_read.py --hand-sample 20     # + the 20 rows to hand-read (seed 1395)
    python scripts/lane2_notice_read.py --pop 34 --hand-sample 20   # the exact J-1395 population/sample

Latency definition: panel hubs s1/s2 run in parallel, a tiebreak s3 runs after them, so a ruling's wall-clock is
max(s1, s2) + (s3 or 0); medians of s1, s2 and of that wall are all printed (the pooled s1+s2 median is NOT the
time a caller waits).  Liveness is read from ticks (gaps under 30 min = active); `scripts/du_lifetimes.py` gives
the process-level view."""
import argparse, collections, datetime, json, math, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
L = lambda ts: datetime.datetime.fromtimestamp(ts)


def rows_of(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def wilson(k, n, z=1.96):
    if not n:
        return None
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 1) if xs else None


def wall(r):
    return (max(r["s1"], r["s2"]) + (r.get("s3") or 0)) if r.get("s1") is not None and r.get("s2") is not None else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shadow", default=os.path.join(DATA, "lane2_shadow.jsonl"))
    ap.add_argument("--jp", default=os.path.join(DATA, "judge_panel_log.jsonl"))
    ap.add_argument("--pop", type=int, default=0, help="restrict the hand-read population to the first N judged rows (0 = all)")
    ap.add_argument("--hand-sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1395)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    rows, jp = rows_of(a.shadow), rows_of(a.jp)
    ticks = [r for r in rows if r.get("kind") == "tick"]
    nj = [r for r in ticks if "notice_judged" in r]
    if not nj:
        print("no tick carries notice_judged yet - nothing to read")
        return
    first, last = nj[0]["ts"], nj[-1]["ts"]
    tt = [r["ts"] for r in ticks if r["ts"] >= first]
    gaps = [b - x for x, b in zip(tt, tt[1:])]
    print("== liveness (ticks since the first notice_judged tick) ==")
    print("first %s  last %s  span %.2f d | ticks %d | active tick-hours (gaps<30min) %.1f | gaps>6h: %s" % (
        L(first), L(last), (last - first) / 86400, len(tt), sum(g for g in gaps if g < 1800) / 3600,
        [(L(x).strftime("%m-%d %H:%M"), round(g / 3600, 1)) for x, g in zip(tt, gaps) if g > 21600]))
    vc = collections.Counter(r["notice_judged"].get("verdict") for r in nj)
    judged = [r for r in nj if r["notice_judged"].get("verdict") in ("contradiction", "consistent")]
    k, n = vc["contradiction"], len(judged)
    sampled = len(nj) - vc["not_sampled"]
    print("\n== D-0281 metric of record (FULL log, not status()'s 2000-row window) ==")
    print("verdicts %s | judged_n %d (defeater bar: >300) | contradictions %d | rate %s | wilson95 %s" % (
        dict(vc), n, k, round(k / n, 4) if n else None, wilson(k, n)))
    print("sample_rate %.3f (ruled 0.25) | judge_coverage %s" % (sampled / len(nj), round(n / sampled, 3) if sampled else None))
    byday = collections.defaultdict(collections.Counter)
    for r in nj:
        byday[L(r["ts"]).strftime("%m-%d")][r["notice_judged"].get("verdict")] += 1
    print("per local day:", {d: dict(c) for d, c in sorted(byday.items())})
    win = [r for r in rows[-2000:] if r.get("kind") == "tick"]
    wj = [r for r in win if (r.get("notice_judged") or {}).get("verdict") in ("contradiction", "consistent")]
    print("status()-equivalent window (last 2000 rows): ticks %d, notice_judged_n %d" % (len(win), len(wj)))

    nn = [r for r in jp if r.get("context") == "lane2:notice"]
    print("\n== judge_panel latency, context lane2:notice (defeater: median > 20 s) ==")
    print("n %d | median s1 %s | median s2 %s | median ruling wall %s | share wall>20s %s | unavailable %d" % (
        len(nn), med([r.get("s1") for r in nn]), med([r.get("s2") for r in nn]), med([wall(r) for r in nn]),
        round(sum(1 for r in nn if (wall(r) or 0) > 20) / max(1, len([r for r in nn if wall(r) is not None])), 2),
        sum(1 for r in nn if r.get("how") == "unavailable")))
    since = [r for r in jp if r["ts"] >= first]
    fam = collections.defaultdict(list)
    for r in since:
        c = (r.get("context") or "").split(":")
        fam[":".join(c[:2]) if c[0] == "lane2" else c[0]].append(r)
    print("same window, all contexts on the same hubs (n, median wall, unavailable):")
    for f, v in sorted(fam.items(), key=lambda kv: -len(kv[1]))[:8]:
        print("   %-30s n=%-4d wall %-6s unavailable %d" % (f, len(v), med([wall(r) for r in v]), sum(1 for r in v if r.get("how") == "unavailable")))

    print("\n== does the notice judge slow the same tick's OTHER lane2 judges? (tick ts = tick START) ==")
    post = [r for r in ticks if r["ts"] >= first]
    lane = [r for r in since if (r.get("context") or "").startswith("lane2:") and r.get("context") != "lane2:notice"]
    for nm, T in (("sampled ticks", [r for r in post if r["notice_judged"].get("verdict") != "not_sampled"]),
                  ("unsampled ticks", [r for r in post if r["notice_judged"].get("verdict") == "not_sampled"])):
        cal = []
        for t in T:
            i = post.index(t)
            end = min(t["ts"] + 240, post[i + 1]["ts"] if i + 1 < len(post) else t["ts"] + 240)
            cal += [r for r in lane if t["ts"] <= r["ts"] < end]
        co = [r for r in cal if r.get("context") == "lane2:coherence"]
        print("   %-16s ticks %-4d lane2:coherence n=%-4d median wall %-6s unavailable %d" % (
            nm, len(T), len(co), med([wall(r) for r in co]), sum(1 for r in co if r.get("how") == "unavailable")))

    try:   # J-2172 / D-0427: place/daylight-standardised grounded_share (additive; fail-open)
        sys.path.insert(0, HERE)
        import lane2_grounded_std as _gstd
        _w = [r for r in ticks if r["ts"] >= ticks[-1]["ts"] - 7 * 86400]
        _res, _lk = _gstd.standardise(_w, ticks), _gstd.metaphor_leak(_w)
        print("\n== D-0427 place/daylight-standardised grounded_share, last 7 d ==")
        print("raw %s | standardised %s | leak %s | %s" % (_res["raw"], _res["standardised"], _lk, _gstd.defeater_check(_res, _lk)))
    except Exception as _e:
        print("\n(standardised grounded_share unavailable: %r)" % (_e,))

    if a.hand_sample:
        pool = judged[:a.pop] if a.pop else judged
        pick = sorted(random.Random(a.seed).sample(range(len(pool)), min(a.hand_sample, len(pool))))
        print("\n== hand-read sample: %d of %d judged rows (seed %d) - mark each: contradicts / invented / fine ==" % (len(pick), len(pool), a.seed))
        for j, i in enumerate(pick, 1):
            r = pool[i]
            print("\n[#%d] %s panel=%s" % (j, L(r["ts"]).strftime("%m-%d %H:%M"), r["notice_judged"]["verdict"]))
            print("  PERCEPTS:", (r.get("percept_lines") or "").replace("\n", " | ")[:700])
            print("  NOTICE  :", r.get("notice"))


if __name__ == "__main__":
    main()

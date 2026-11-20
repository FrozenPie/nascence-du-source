"""J-2635 offline reader: attribute incarnation N's multi-minute competence-timer stalls.
READ-ONLY over C:/Nascence/data (opened 'rb'). Nothing is written except stdout.
Usage: python scripts/stall_attribution_n.py > docs/reviews/stall_attribution_n_2026-10-31.txt
For each stall (the late tier3 wake time) it prints: the previous tier3 tick, the competence
timer lateness, every nascence.log line from prev tick to wake+15s (gap lines flagged), every
llm_latency row whose COMPLETION falls in [prev_tick-130s, wake+15s] with s>=15 or ok=0 (plus
its implied START = ts - s), and a per-file count of timestamped jsonl rows inside the gap.
"""
import json, os, re, glob, sys, datetime as d
sys.stdout.reconfigure(encoding="utf-8")
TZ = d.timezone(d.timedelta(hours=13))   # NZDT, same offset as the log
DATA = r"C:/Nascence/data"
STALLS = ["2026-10-29 18:47:36", "2026-10-30 01:16:07", "2026-10-30 03:59:59", "2026-10-30 04:19:09",
          "2026-10-30 04:55:31", "2026-10-30 14:49:05", "2026-10-30 14:52:51"]
def ts(s): return d.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ).timestamp()
def fm(t): return d.datetime.fromtimestamp(t, TZ).strftime("%m-%d %H:%M:%S")
LINE = re.compile(rb"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) \[([^\]]+)\] (.*)")
T3 = re.compile(rb"\[tier3\] tick #(\d+)")
stalls = sorted((ts(s), s) for s in STALLS)
lo_all = min(t for t, _ in stalls) - 700; hi_all = max(t for t, _ in stalls) + 60
# one pass over nascence.log, keep only lines inside any stall neighbourhood (prev tier3 tick found by scan)
recs = []          # (epoch_with_ms, logger, text)
with open(DATA + "/nascence.log", "rb") as f:
    for raw in f:
        m = LINE.match(raw)
        if not m: continue
        try: t = ts(m.group(1).decode()) + int(m.group(2)) / 1000
        except Exception: continue
        if t < lo_all: continue
        if t > hi_all: break
        recs.append((t, m.group(3).decode(), raw[m.end(3) + 2:].decode("utf-8", "replace").strip()))
# llm_latency
lat = []
for raw in open(DATA + "/llm_latency.jsonl", "rb"):
    try: r = json.loads(raw)
    except Exception: continue
    if lo_all - 200 <= r.get("ts", 0) <= hi_all: lat.append(r)
# generic jsonl row counts
jfiles = [p for p in glob.glob(DATA + "/*.jsonl") + glob.glob(DATA + "/logs/*.jsonl")
          if os.path.getmtime(p) > ts("2026-10-29 18:00:00") and os.path.getsize(p) < 300e6]
WINDOWS = []
ALLROWS = []   # (ts, relpath) for every timestamped jsonl row in any stall neighbourhood
def collect(path, wins):
    rel = os.path.relpath(path, DATA)
    with open(path, "rb") as f:
        for raw in f:
            m = re.search(rb'"ts": ?([0-9.]+)', raw[:200])
            if not m: continue
            v = float(m.group(1))
            if any(a <= v <= b for a, b in wins): ALLROWS.append((v, rel))
def jrows(path, lo, hi):
    n = 0
    with open(path, "rb") as f:
        for raw in f:
            m = re.search(rb'"ts": ?([0-9.]+)', raw[:200])
            if not m: continue
            v = float(m.group(1))
            if lo <= v <= hi: n += 1
    return n
def ticks(loop, upto):
    return [(t, int(re.search(r"tick #(\d+)", x).group(1))) for t, lg, x in recs if t <= upto and ("[%s]" % loop) in x and "tick #" in x]
def _prev(wake):
    pv = [t for t, lg, x in recs if t <= wake - 1 and "tick #" in x and ("[tier3]" in x or "[stability]" in x)]
    return (max(pv) if pv else wake - 300)
_pvs = {}
for wake, name in stalls:
    _pvs[wake] = min([ (lambda lp: lp)(max([t for t, lg, x in recs if t <= wake - 1 and ("[%s]" % L) in x and "tick #" in x] or [wake - 300])) for L in ("tier3", "stability")])
for pth in jfiles: collect(pth, [(_pvs[w] - 5, w + 15) for w, _ in stalls])
ALLROWS.sort()
for wake, name in stalls:
    print("=" * 100)
    prev_by = {}
    for loop in ("tier3", "stability"):
        pv = ticks(loop, wake - 1); cur = [(t, n) for t, n in ticks(loop, wake + 15) if t >= wake - 1]
        if pv:
            pt, pn = pv[-1]
            ct = cur[0] if cur else None
            prev_by[loop] = pt
            print("%s: prev tick #%d at %s ; next tick %s ; interval %s" % (loop, pn, fm(pt),
                  ("#%d at %s" % (ct[1], fm(ct[0]))) if ct else "none within +15s",
                  ("%.1f s (late %.1f s vs 120 s)" % (ct[0] - pt, ct[0] - pt - 120)) if ct else "?"))
    print("STALL wake %s" % name)
    prev_t = min(prev_by.values()) if prev_by else wake - 300
    inside = [(t, lg, x) for t, lg, x in recs if prev_t - 1 <= t <= wake + 15]
    last = prev_t
    print("-- nascence.log lines prev tick .. wake+15s (%d lines); GAP>=20s flagged" % len(inside))
    for t, lg, x in inside[:80]:
        g = t - last
        print("%s.%03d %s%s | %s" % (fm(t), int((t % 1) * 1000), "  <<GAP %.0fs>> " % g if g >= 20 else " ", lg.replace("nascence.", ""), x[:170]))
        last = t
    if len(inside) > 80: print("   ... %d more lines" % (len(inside) - 80))
    lo, hi = prev_t - 130, wake + 15
    print("-- llm_latency rows completing in [%s, %s] with s>=15 or ok=0 (START = ts-s)" % (fm(lo), fm(hi)))
    for r in lat:
        if lo <= r["ts"] <= hi and (r.get("s", 0) >= 15 or not r.get("ok", 1)):
            print("   end %s  start %s  s=%-7s ok=%s node=%s model=%s by=%s" % (fm(r["ts"]), fm(r["ts"] - r["s"]), r["s"], r["ok"], r["node"], r["model"], r["by"]))
    nrows = sum(1 for r in lat if lo <= r["ts"] <= hi)
    print("   (total llm_latency completions in that span: %d; in the gap [%s,%s): %d)" % (nrows, fm(prev_t + 5), fm(wake - 1), sum(1 for r in lat if prev_t + 5 <= r["ts"] < wake - 1)))
    a, b = prev_t - 5, wake + 15
    ev = sorted([t for t, lg, x in recs if a <= t <= b] + [t for t, rel in ALLROWS if a <= t <= b])
    gaps = sorted(((ev[k + 1] - ev[k], ev[k], ev[k + 1]) for k in range(len(ev) - 1)), reverse=True)[:4]
    print("-- PROCESS-WIDE SILENCE: union of nascence.log lines + timestamped rows from %d jsonl files in [%s,%s] = %d events; 4 longest silent gaps:" % (len(jfiles), fm(a), fm(b), len(ev)))
    for g, x0, x1 in gaps: print("   %.1f s silent: %s.%03d -> %s.%03d" % (g, fm(x0), int((x0 % 1) * 1000), fm(x1), int((x1 % 1) * 1000)))
    print("   events per source in the window (top): " + ", ".join("%s=%d" % kv for kv in sorted(__import__("collections").Counter(rel for t, rel in ALLROWS if a <= t <= b).items(), key=lambda kv: -kv[1])[:8]))

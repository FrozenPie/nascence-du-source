import sqlite3, time, json, bisect, sys, os
DB = r"C:\Nascence\data\memory\nascence.db"
st0 = [(f, os.stat(f).st_size, os.stat(f).st_mtime) for f in (DB, DB+"-wal") if os.path.exists(f)]
con = sqlite3.connect("file:" + DB.replace("\\","/") + "?mode=ro", uri=True, timeout=30)
con.execute("PRAGMA query_only=ON")
ev = con.execute("SELECT event_id, timestamp, resolved, source FROM shadow_events").fetchall()
res = con.execute("SELECT shadow_event_id, timestamp, encounter_similarity FROM resolution_events ORDER BY timestamp").fetchall()
print("shadow_events", len(ev), "unresolved", sum(1 for e in ev if not e[2]), "resolution_events", len(res))
ts_of = {e[0]: e[1] for e in ev}
pre_res = {e[0] for e in ev if e[2]}
first_res = {}
for sid, t, sim in res:
    if sid not in first_res: first_res[sid] = t
distinct = len(first_res)
matched_in_shadow = sum(1 for s in first_res if s in ts_of)
print("distinct shadow events with >=1 resolution_event:", distinct, "present in shadow_events:", matched_in_shadow)
# resolution_events per day
import collections
byday = collections.Counter(time.strftime("%m-%d", time.localtime(t)) for _,t,_ in res)
print("resolution_events by day (last 14):", sorted(byday.items())[-14:])
newday = collections.Counter(time.strftime("%m-%d", time.localtime(t)) for t in first_res.values())
print("distinct NEW resolves by day (last 14):", sorted(newday.items())[-14:])
HL = 6*3600; K = 3.0
def score(t, resolved_at):
    # 200 most recent unresolved-at-t events with ts<=t
    rows = []
    for eid, ts, rv, src in ev:
        if ts > t or eid in pre_res: continue
        r = resolved_at.get(eid)
        if r is not None and r <= t: continue
        rows.append(ts)
    rows.sort(reverse=True)
    rows = rows[:200]
    return sum(0.5 ** (max(0.0, t - ts)/HL) for ts in rows)
def sat(x): return x/(x+K)
now = time.time()
# sample hourly over last 7 days
out = []
for h in range(0, 24*7+1, 6):
    t = now - h*3600
    base = score(t, {})
    fix = score(t, first_res)
    out.append((h, base, sat(base), fix, sat(fix)))
print("hours_ago  raw_base sat_base | raw_A sat_A")
for h,b,sb,f,sf in out: print(f"{h:5d}  {b:8.1f} {sb:.3f} | {f:8.2f} {sf:.3f}")
# "now" with all resolutions applied
b = score(now, {}); f = score(now, first_res)
print("NOW base raw %.1f sat %.3f ; with-A raw %.2f sat %.3f" % (b, sat(b), f, sat(f)))
import statistics
sf = [o[4] for o in out]; sb=[o[2] for o in out]
print("median sat base %.3f  withA %.3f  min withA %.3f max %.3f" % (statistics.median(sb), statistics.median(sf), min(sf), max(sf)))
# thresholds
print("fraction of samples with A below 0.65: %.2f ; below 0.55: %.2f ; below 0.9: %.2f" % (sum(1 for x in sf if x<0.65)/len(sf), sum(1 for x in sf if x<0.55)/len(sf), sum(1 for x in sf if x<0.9)/len(sf)))
# which age are resolved events: lag between shadow event and its first resolution
lags = sorted((first_res[s]-ts_of[s])/3600 for s in first_res if s in ts_of)
if lags: print("lag hours shadow->first resolution: min %.1f p25 %.1f p50 %.1f p75 %.1f max %.1f" % (lags[0], lags[len(lags)//4], lags[len(lags)//2], lags[3*len(lags)//4], lags[-1]))
# of recent-window 200 unresolved events now, how many have a resolution
rows = sorted([e for e in ev if not e[2]], key=lambda e: -e[1])[:200]
print("of the live window's 200 events, with a resolution_event:", sum(1 for e in rows if e[0] in first_res))
st1 = [(f, os.stat(f).st_size, os.stat(f).st_mtime) for f in (DB, DB+"-wal") if os.path.exists(f)]
print("db stat before", st0, "\nafter", st1)

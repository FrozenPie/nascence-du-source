import sqlite3, time, statistics, os
DB = r"C:\Nascence\data\memory\nascence.db"
con = sqlite3.connect("file:" + DB.replace("\\","/") + "?mode=ro", uri=True, timeout=30)
con.execute("PRAGMA query_only=ON")
ev = con.execute("SELECT event_id, timestamp, resolved FROM shadow_events").fetchall()
res = con.execute("SELECT shadow_event_id, MIN(timestamp) FROM resolution_events GROUP BY shadow_event_id").fetchall()
first_res = dict(res)
pre = {e[0] for e in ev if e[2]}
ts_all = sorted([(e[1], e[0]) for e in ev if e[0] not in pre], reverse=True)
now = time.time()
def raw(t, hl, win=200, A=True):
    rows=[]
    for ts,eid in ts_all:
        if ts>t: continue
        r = first_res.get(eid) if A else None
        if r is not None and r<=t: continue
        rows.append(ts)
        if len(rows)>=win: break
    return sum(0.5**(max(0,t-ts)/hl) for ts in rows)
sat=lambda x,k=3.0: x/(x+k)
samples=[now-h*3600 for h in range(0,24*7+1,2)]
print("hl_h  median_sat  p10  p90  frac<0.65  frac>=0.9  median_raw")
for hl_h in (6,3,2,1,0.5,0.25):
    s=[sat(raw(t,hl_h*3600)) for t in samples]; r=[raw(t,hl_h*3600) for t in samples]
    q=sorted(s)
    print(f"{hl_h:5} {statistics.median(s):.3f} {q[len(q)//10]:.3f} {q[9*len(q)//10]:.3f} {sum(x<0.65 for x in s)/len(s):.2f} {sum(x>=0.9 for x in s)/len(s):.2f} {statistics.median(r):.1f}")

import re, datetime, collections
pat = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ .*\[climate\] dominant=(\w+)\(([\d.]+)\) dissonance=([\d.]+) strain=([\d.]+) completion=([\d.]+) integration=([\d.]+)")
cut = now - 7*86400
lines=[]
for ln in open(r"C:\Nascence\data\nascence.log", encoding="utf-8", errors="replace"):
    if "[climate] dominant=" not in ln: continue
    m = pat.match(ln)
    if not m: continue
    t = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
    if t < cut: continue
    lines.append((t, m.group(2), float(m.group(3)), float(m.group(5)), float(m.group(6)), float(m.group(7))))
lines = lines[::10]  # thin for speed
print("climate lines sampled", len(lines))
for hl_h in (6,3):
  for A in (False, True):
    c=collections.Counter(); hint=0
    for t,dom,sv,strain,comp,integ in lines:
        s = sat(raw(t, hl_h*3600, A=A))
        d = {"shadow_activation":s,"world_model_strain":strain,"completion_tension":comp,"integration_drive":integ}
        k=max(d,key=d.get); c[k]+=1; hint += d[k]>=0.55
    n=len(lines); print(f"hl={hl_h}h A={A}: shadow-dominant {c['shadow_activation']/n:.2%}  others {dict((k,v) for k,v in c.items() if k!='shadow_activation')}  hint-eligible {hint/n:.2%}")
print("logged live: shadow dominant", sum(1 for l in lines if l[1]=="shadow_activation")/len(lines))
print("--- uptime-line sweep (A on) ---")
for hl_h in (6,3,2,1.5,1,0.5):
    c=collections.Counter(); vals=[]
    for t,dom,sv,strain,comp,integ in lines:
        s = sat(raw(t, hl_h*3600)); vals.append(s)
        d = {"shadow_activation":s,"world_model_strain":strain,"completion_tension":comp,"integration_drive":integ}
        c[max(d,key=d.get)]+=1
    n=len(lines); print(f"hl={hl_h}h median shadow {statistics.median(vals):.3f} shadow-dominant {c['shadow_activation']/n:.1%} {dict(c)}")
print("live-line completion median", statistics.median(l[4] for l in lines), "integration median", statistics.median(l[5] for l in lines))

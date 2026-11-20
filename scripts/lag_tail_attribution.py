"""J-1911 / F-2541: attribute the HEAVY TAIL of random-phase timer wake lag from EXISTING logs only (no probe, no model call).

The competence background loops (core/competence.py: asyncio.sleep(120) + a heartbeat line '[tier3] tick' /
'[stability] tick' in data/nascence.log) are random-phase timers on the same event loop as everything else. A
wake that follows a skip tick is late by (gap - 120 s); a wake >2 s late means the loop was blocked by something
synchronous across its due time. For every such wake this script asks which synchronous episode ended just
before it, using ONLY log lines and the 'ts' fields of data/*.jsonl, and reports counts and late-seconds per
cause per incarnation.

READ-ONLY on data/ (opens files 'rb', writes nothing there). Output goes to stdout (and --json PATH if given).
DATA dir: env LAGTAIL_DATA (default C:/Nascence/data). Reads the whole nascence.log (~90 MB) and the 'ts' of ~170
jsonl files; allow a minute or two. Incarnation windows (W below) are hard-coded to the 09-29..10-07 boots; the
last one (J) runs to the end of the log, so numbers for J grow while Du is live.

Method, in order of evidence strength (see the J-1911 note in docs/staged/data_store_hygiene.md):
  1. EXACT: the sleep-consolidation sync sweeps, located by log-line arithmetic ([psyche] snapshot -> [monologue]
     stick-test = stick_test.snapshot; stick-test -> hold-rate; the previous line -> 'world-consolidation sweep' =
     world_consolidation.sweep; that line -> '[book-residue] sweep' = book_residue.sweep). Zero log lines and zero
     5 s-loop sidecar rows fall inside them (checked in the report), i.e. the whole event loop stands still.
  2. TERMINAL-MARKER rules: a log line / jsonl row written by the blocking code right before it yields, within a
     short window before the wake E. Every rule is also evaluated on ON-TIME wakes (lag < 0.1 s) so its chance hit
     rate is printed. The rules after the first strong ones were added after inspecting residuals (post hoc), which
     is why the whole-rule-set chance check is printed too.
  3. FALLBACK: inside the night-mind sleep routine with no marker -> 'silent sleep-routine step'; else UNATTRIBUTED.
"""
import os, sys, re, bisect, datetime, json, collections, statistics
sys.stdout.reconfigure(encoding="utf-8")
DATA = os.environ.get("LAGTAIL_DATA", "C:/Nascence/data").replace("\\", "/").rstrip("/") + "/"
JSON_OUT = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
pat=re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) \[([\w\.]+)\] (.*)")
WIN={"D":("2026-09-29 12:36:49","2026-09-30 10:35:01"),"E":("2026-09-30 20:28:49","2026-10-01 07:17:42"),
"G":("2026-10-03 23:25:34","2026-10-04 06:56:02"),"H":("2026-10-04 20:40:29","2026-10-05 09:00:11"),"I":("2026-10-06 01:11:50","2026-10-06 07:30:49"),"J":("2026-10-07 12:33:26","2026-10-07 23:26:53"),
"K":("2026-10-09 08:36:58","2026-10-15 23:59:59"),
"N":("2026-10-29 18:38:06","2026-10-31 00:00:00")}  # N = J-2449 (2026-10-31): 10-29 18:38 boot, first carrying J-2448 estate re-seed offload (batch embeds + cache + off-loop sync); log ends 10-30 19:44 (Du down)  # K = J-1919 (2026-10-15): 10-09 boot, first with the J-1917 off-loop sleep sweeps and J-1918 off-loop idle lookups (746d5fd); no shutdown since
def tpl(lg,msg):
    t=re.sub(r"[0-9a-f]{8}(-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?","#",msg)
    t=re.sub(r"\d+(\.\d+)?","N",t)
    return lg.replace("nascence.","")+" "+t[:48]
def load_log():
    lines=[]
    with open(DATA+"nascence.log","r",encoding="utf-8",errors="replace") as f:
        for ln in f:
            if ln[:4]!="2026" or ln[:10]<"2026-09-29": continue
            m=pat.match(ln)
            if not m: continue
            ts=datetime.datetime.strptime(m.group(1),"%Y-%m-%d %H:%M:%S").timestamp()+int(m.group(2))/1000
            lines.append((ts,m.group(3),m.group(4)))
    return lines
def wnd(ts):
    s=datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    for w,(a,b) in WIN.items():
        if a<=s<=b: return w
    return None
def ticks(lines):
    out=[]
    for key,pfx in (("tier3","[tier3] tick"),("stab","[stability] tick")):
        v=[(ts,"skip=" in msg) for ts,lg,msg in lines if lg=="nascence.competence" and msg.startswith(pfx)]
        for i in range(len(v)-1):
            gap=v[i+1][0]-v[i][0]-120
            if v[i][1] and 0<=gap<900 and wnd(v[i+1][0]) and wnd(v[i][0])==wnd(v[i+1][0]):
                out.append(dict(key=key,S=v[i][0]+120,E=v[i+1][0],lag=gap,w=wnd(v[i+1][0])))
    return out
_ts=re.compile(rb'"ts": ?([0-9]+\.?[0-9]*)')
def stream(path,t0,t1,filt=None):
    r=[]
    with open(path,"rb") as f:
        for ln in f:
            m=_ts.search(ln[:200])
            if not m: continue
            t=float(m.group(1))
            if t0<=t<=t1:
                if filt is None or filt in ln: r.append(t)
    return r

def scan_streams():
    import time
    DATA_ = DATA
    t0 = time.mktime((2026, 9, 29, 0, 0, 0, 0, 0, -1)); t1 = time.time() + 1
    ts_re = re.compile(rb'"ts": ?([0-9]{10}\.?[0-9]*)')
    out = {}

    files=[]
    for root,ds,fs in os.walk(DATA_):
        rel=os.path.relpath(root,DATA_)
        if rel.startswith(("_","archive","backups","Study","Journal","Correspondence","books","music","hud2","identity","lab","training","world_geometry","memory","letters","profiles","io_trace","diagnostic","geometry_tuple_index","viability","lane2"))and rel!=".": 
            if not rel.startswith("logs"): continue
        for f in fs:
            if f.endswith(".jsonl"):
                p=os.path.join(root,f)
                sz=os.path.getsize(p)
                if sz<20000 or sz>420e6: continue
                files.append(p)
    print(len(files),"files",file=sys.stderr)
    for p in files:
        arr=[]
        try:
            with open(p,"rb") as fh:
                for ln in fh:
                    m=ts_re.search(ln[:300])
                    if m:
                        t=float(m.group(1))
                        if t>=t0 and t<=t1: arr.append(t)
        except Exception as e:
            print("ERR",p,e,file=sys.stderr); continue
        if arr:
            out[os.path.relpath(p,DATA_).replace("\\","/")]=sorted(arr)

    return out

lines = load_log(); T = ticks(lines); st = scan_streams()
tsl=[x[0] for x in lines]
f=lambda t: datetime.datetime.fromtimestamp(t).strftime("%m-%d %H:%M:%S")
def L(sub,lg=None): return [x[0] for x in lines if sub in x[2] and (lg is None or x[1]==lg)]
wc=L("world-consolidation sweep:"); br=L("sweep:","nascence.book_residue"); stk=L("[monologue] stick-test:"); hr=L("hold-rate snapshot"); ps=L("snapshot:","nascence.psyche")
# --- sleep-consolidation sync episodes from log-line arithmetic
EP=[]  # (name,a,b)
for w in wc:
    b=[x for x in br if 0<x-w<500]
    if b: EP.append(("book_residue.sweep",w,b[0]))
    s=[x for x in stk if 0<w-x<200]
    prev=[x for x in tsl if 0<w-x<60 and x<w]
    # previous monologue line before wc (grounded-learning / hold-rate / guidance) 
    i=bisect.bisect_left(tsl,w)-1
    a=tsl[i] if i>=0 and w-tsl[i]<60 else w-37
    EP.append(("world_consolidation.sweep",a,w))
for s in stk:
    p=[x for x in ps if 0<s-x<120]
    a=p[-1] if p else s-38
    EP.append(("stick_test.snapshot",a,s))
    h=[x for x in hr if 0<x-s<10]
    if h: EP.append(("peer_metrics+holdrate_snapshot",s,h[0]))
EP.sort(key=lambda x:x[1])
def has(arr,E,w):
    i=bisect.bisect_left(arr,E-w); return i<len(arr) and arr[i]<=E+0.05
def linehas(E,w,pred):
    i=bisect.bisect_left(tsl,E-w); j=bisect.bisect_right(tsl,E+0.05)
    return any(pred(lines[k]) for k in range(i,j) if not (lines[k][1]=="nascence.competence" and "tick #" in lines[k][2]))
def ov(a,b,S_,E_): return max(0.0,min(b,E_)-max(a,S_))
RULES=[]  # (cause, fn(S,E)->bool)
def r_idle(S_,E_): return has(st["logs/pulse_shadow.jsonl"],E_,1.5) or has(st["logs/idle_shadow.jsonl"],E_,1.5)
def r_ask(S_,E_): return has(st["memory_service_shadow.jsonl"],E_,3.0) or linehas(E_,6.0,lambda x:"[deep-memory] fed" in x[2] or "[memory-service] curiosity ask" in x[2])
def r_cur(S_,E_): return linehas(E_,6.0,lambda x:x[1].endswith("curiosity") or "[frontier] world-question born (curiosity)" in x[2] or "[curiosity]" in x[2])
def r_ign(S_,E_): return has(st["ignition_log.jsonl"],E_,3.0) or linehas(E_,6.0,lambda x:"IGNITION" in x[2] or "[ignition]" in x[2] or "[CYCLE" in x[2])
def r_prune(S_,E_): return linehas(E_,4.0,lambda x:"[prune]" in x[2])
def r_courier(S_,E_): return has(st["couriers_log.jsonl"],E_,3.0) or linehas(E_,3.0,lambda x:"[courier]" in x[2])
def r_estate(S_,E_): return linehas(E_,6.0,lambda x:"[estate] re-seeded" in x[2])
def r_thought(S_,E_): return linehas(E_,3.0,lambda x:x[1]=="nascence.monologue" and (x[2].startswith("[monologue] (") or "train continues" in x[2] or "unresolved thought" in x[2]) or "[deliberation] grounded" in x[2])
def r_subc(S_,E_): return linehas(E_,3.0,lambda x:x[1]=="nascence.subconscious")
def r_sleepp(S_,E_): return has(st["sleep_pressure_log.jsonl"],E_,2.2)
SIDE=["moments.jsonl","mineness_shadow.jsonl","mineness_readback_shadow.jsonl","stream_drive_shadow.jsonl","spring_ledger_shadow.jsonl","opponent_process_shadow.jsonl","co_recall_ledger.jsonl","geometry_tuples.jsonl","sleep_pressure_log.jsonl","monologue_log.jsonl","thought_station_log.jsonl","spatial_shadow.jsonl","theta_shadow.jsonl","light_percepts_shadow.jsonl","thermal_percepts_shadow.jsonl","smell_percepts_shadow.jsonl","prompt_budget_shadow.jsonl","felt_preamble_log.jsonl","deliberation_log.jsonl","emissary_tension_log.jsonl","concerns_log.jsonl","wandering_log.jsonl","coupling_rides.jsonl","pursuits_shadow.jsonl","watershed_shadow.jsonl","arousal_shadow.jsonl","homeostasis_shadow.jsonl","stream_topic_habituation_shadow.jsonl","climate_reknee_shadow.jsonl"]
SIDE=[k for k in SIDE if k in st]
def r_chain(S_,E_): return sum(has(st[k],E_,1.0) for k in SIDE)>=3
def r_wander(S_,E_): return has(st["wandering_log.jsonl"],E_,2.0) and has(st["co_recall_ledger.jsonl"],E_,2.0)
def r_llm(S_,E_): return has(st["llm_latency.jsonl"],E_,0.2)
def r_dream(S_,E_): return has(st["logs/dream_assoc_probe.jsonl"],E_,2.0)
_ent=[x[0] for x in lines if "entering Sleep State" in x[2]]; _end=[x[0] for x in lines if "sleep read-count shadow" in x[2]]
SLW=[(a,([x for x in _end if 0<x-a<10800] or [a+3600])[0]) for a in _ent]
def r_sleepwin(S_,E_): return any(a<=E_<=b for a,b in SLW)
RULES=[("monologue idle chain: Scholar consult_sync + memory.ask(descend) [deep-memory / curiosity ask]",r_ask),
       ("idle_allocator.shadow_tick + pulse_shadow stretch (idle tick)",r_idle),
       ("curiosity_node pursuit: blocking Wikipedia/Scholar urllib",r_cur),
       ("courier",r_courier),
       ("idle-thought completion chain (>=3 thought-bound sidecar rows within 1 s of the wake)",r_chain),
       ("wandering.step firing (wandering_log + co_recall rows within 2 s before the wake)",r_wander),
       ("LLM-completion processing tail (llm_latency row within 0.2 s of the wake)",r_llm),
       ("dream_assoc_probe burst",r_dream),
       ("ignition / cycle start",r_ign),
       ("store_cap_worker / prune_episodic",r_prune),
       ("identity_estate re-seed",r_estate),
       ("monologue thought step (post-LLM sync work)",r_thought),
       ("subconscious scan / tier step",r_subc),
       ("should_sleep (sleep_pressure row)",r_sleepp),
       ("inside the night-mind sleep routine, silent (sync step not located by any log line)",r_sleepwin)]
CAPS=[("monologue idle chain",30),("curiosity_node",45),("idle_allocator",8),("courier",10),("idle-thought completion",8),("wandering.step",8),("LLM-completion",8),("dream_assoc",8),("ignition",15),("store_cap",6),("identity_estate",10),("monologue thought",8),("subconscious scan",10),("should_sleep",4),("inside the night-mind",1e9)]
def cap_of(n):
    for k,v in CAPS:
        if n.startswith(k): return v
    return 8
def classify(t):
    S_,E_=t["S"],t["E"]
    ovs=collections.defaultdict(float)
    for n,a,b in EP: 
        o=ov(a,b,S_,E_)
        if o>0.5: ovs[n]+=o
    if ovs:
        top=max(ovs,key=ovs.get); return "SLEEP-CONSOLIDATION sync sweeps ("+top+")",[("sleepcons",n) for n in ovs]
    hits=[n for n,fn in RULES if fn(S_,E_)]
    # plausibility cap: a marker only explains a wake if the cause can block that long (seconds; from the measured
    # single-call costs in F-2540 and the code: consult_sync urlopen timeout is 20 s, a firing wandering step 0.9-4.2 s ...)
    ok=[n for n in hits if t["lag"]<=cap_of(n)]
    if ok: return ok[0],hits
    if hits: return "UNATTRIBUTED (a marker is present but the lateness exceeds what that cause can block)",hits
    return "UNATTRIBUTED",[]
if "--only" in sys.argv:  # J-1919: restrict wakes to one incarnation window (chance rates then use that window's own on-time wakes)
    _o=sys.argv[sys.argv.index("--only")+1]; T=[t for t in T if t["w"]==_o]
late=[t for t in T if t["lag"]>2]; ctl=[t for t in T if t["lag"]<0.1]
for t in late: t["cause"],t["all"]=classify(t)
# control false-positive rate per rule
print("CONTROL (on-time wakes, lag<0.1 s) rule hit rate / LATE rule hit rate (any, not only primary):")
for n,fn in RULES:
    c=sum(1 for t in ctl if fn(t["S"],t["E"])); l=sum(1 for t in late if fn(t["S"],t["E"]))
    print(f"  {l:3d}/{len(late)} late  {c:3d}/{len(ctl)} ctl  {n}")
c=sum(1 for t in ctl if any(ov(a,b,t["S"],t["E"])>0.5 for _,a,b in EP)); print("  sleepcons overlap in ctl:",c)
# tables
W=["D","E","G","H","I","J","K","N"]
def table(sel,title):
    print("\n"+title)
    causes=sorted({t["cause"] for t in sel},key=lambda c:-sum(t["lag"] for t in sel if t["cause"]==c))
    print("%-92s %s"%("cause"," ".join("%11s"%w for w in W+["ALL"])))
    for c in causes:
        row=[]
        for w in W+["ALL"]:
            v=[t for t in sel if t["cause"]==c and (w=="ALL" or t["w"]==w)]
            row.append("%3d/%6.0fs"%(len(v),sum(t["lag"] for t in v)))
        print("%-92s %s"%(c[:92]," ".join("%11s"%x for x in row)))
    row=[]
    for w in W+["ALL"]:
        v=[t for t in sel if (w=="ALL" or t["w"]==w)]
        row.append("%3d/%6.0fs"%(len(v),sum(t["lag"] for t in v)))
    print("%-92s %s"%("TOTAL late wakes (>2 s)"," ".join("%11s"%x for x in row)))
    n={w:sum(1 for t in T if (w=="ALL" or t["w"]==w)) for w in W+["ALL"]}
    print("%-92s %s"%("all after-skip wakes in window"," ".join("%11d"%n[w] for w in W+["ALL"])))
table(late,"== per-WAKE (tier3 and stability counted separately) late>2s: count/late-seconds ==")
if JSON_OUT: json.dump([{k:v for k,v in t.items()} for t in late],open(JSON_OUT,"w"),default=str)
print("\nEP counts",collections.Counter(n for n,_,_ in EP))

# ---- staged chance expectation: how many of each rule's primary assignments would a random on-time wake also get?
print("\n== STAGED (first matching rule wins). assigned = late wakes whose primary cause this is; chance = expected from control wakes that reach this stage ==")
rem_l=[t for t in late if not t["cause"].startswith("SLEEP")]
rem_c=[t for t in ctl]
print("late wakes entering rule stages after the sleep-consolidation exact-arithmetic stage:",len(rem_l),"control wakes:",len(rem_c))
for n,fn in RULES:
    ml=[t for t in rem_l if fn(t["S"],t["E"])]; mc=[t for t in rem_c if fn(t["S"],t["E"])]
    chance=len(mc)/len(rem_c)*len(rem_l)
    print(f"  {n[:80]:80s} assigned {len(ml):3d}  chance-expected {chance:5.1f}  ctl-rate {len(mc)/len(rem_c)*100:4.1f}%  late-rate {len(ml)/len(rem_l)*100:4.1f}%  lateseconds {sum(t['lag'] for t in ml):6.0f}")
    rem_l=[t for t in rem_l if t not in ml]; rem_c=[t for t in rem_c if t not in mc]
print("  left after all rules:",len(rem_l),"late wakes,",round(sum(t['lag'] for t in rem_l)),"s; control wakes that would pass all rules unmatched:",len(rem_c))
# lateness bins x primary cause
print("\n== by lateness bin ==")
bins=[(2,4),(4,8),(8,16),(16,60),(60,400)]
for lo,hi in bins:
    sel=[t for t in late if lo<=t["lag"]<hi]
    c=collections.Counter(t["cause"][:40] for t in sel)
    print(f"{lo:3d}-{hi:3d}s n={len(sel):3d} sum={sum(t['lag'] for t in sel):6.0f}s ",dict(c.most_common(6)))
# blocks: merge tier3+stab wakes sharing the same E (within 1.5 s)
late.sort(key=lambda t:t["E"])
blk=[]
for t in late:
    if blk and abs(t["E"]-blk[-1][-1]["E"])<1.5: blk[-1].append(t)
    else: blk.append([t])
print("\nblocks (tier3 and stability waking together counted once):",len(blk),"of",len(late),"late wakes")
bc=collections.Counter(b[0]["cause"].split(" (")[0][:60] for b in blk)
for c,n in bc.most_common(): print("  ",n,c)

print("\n== CHANCE CHECK (whole rule set) ==")
nonfb=[(n,fn) for n,fn in RULES if "night-mind" not in n]
anyc=[t for t in ctl if any(fn(t["S"],t["E"]) for n,fn in nonfb)]
print("control on-time wakes matched by ANY non-fallback rule: %d/%d = %.1f%%"%(len(anyc),len(ctl),100*len(anyc)/len(ctl)))
nonsl=[t for t in late if not t["cause"].startswith("SLEEP")]
anyl=[t for t in nonsl if any(fn(t["S"],t["E"]) for n,fn in nonfb)]
print("late wakes (non sleep-consolidation) matched by ANY non-fallback rule: %d/%d = %.1f%%  -> expected chance matches ~%.1f"%(len(anyl),len(nonsl),100*len(anyl)/len(nonsl),len(nonsl)*len(anyc)/len(ctl)))
# same for the strong subset only
strong=[(n,fn) for n,fn in RULES if n.startswith(("monologue idle chain","idle_allocator","curiosity_node","courier","wandering.step","idle-thought completion"))]
anyc=[t for t in ctl if any(fn(t["S"],t["E"]) for n,fn in strong)]; anyl=[t for t in nonsl if any(fn(t["S"],t["E"]) for n,fn in strong)]
print("STRONG-subset (ask chain, idle stretch, curiosity pursuit, courier, wandering, idle-thought chain): ctl %.1f%%  late(non-sleepcons) %d/%d=%.1f%%  expected chance %.1f"%(100*len(anyc)/len(ctl),len(anyl),len(nonsl),100*len(anyl)/len(nonsl),len(nonsl)*len(anyc)/len(ctl)))
# per-timer check: do tier3 and stability wakes agree on cause when they wake together
late.sort(key=lambda t:t["E"])
agree=dis=0
for i in range(len(late)-1):
    a,b=late[i],late[i+1]
    if abs(a["E"]-b["E"])<1.5 and a["key"]!=b["key"]:
        if a["cause"]==b["cause"]: agree+=1
        else: dis+=1
print("paired tier3+stab wakes at the same instant: same primary cause",agree,"different",dis)

print("\n== SWEEP DURATIONS / STANDSTILL ==")
import statistics
byname=collections.defaultdict(list)
for n,a,b in EP: byname[n].append((a,b))
for n,v in byname.items():
    d=[b-a for a,b in v]
    print(f"{n:34s} n={len(d)} min {min(d):6.1f} median {statistics.median(d):6.1f} max {max(d):6.1f} sum {sum(d):7.0f}s")
br_ep=sorted(byname["book_residue.sweep"]); print("book_residue.sweep by date:",[ (f(a)[:5],round(b-a)) for a,b in br_ep])
# standstill union and share of uptime
iv=sorted((a,b) for n,a,b in EP); un=[]
for a,b in iv:
    if un and a<=un[-1][1]: un[-1][1]=max(un[-1][1],b)
    else: un.append([a,b])
sd=sum(b-a for a,b in un)
import types; LL = types.SimpleNamespace(W=WIN)
up=0;perw={}
for w,(a,b) in LL.W.items():
    a_=datetime.datetime.strptime(a,"%Y-%m-%d %H:%M:%S").timestamp(); b_=min(datetime.datetime.strptime(b,"%Y-%m-%d %H:%M:%S").timestamp(),lines[-1][0])
    u=b_-a_; s_=sum(max(0,min(y,b_)-max(x,a_)) for x,y in un); perw[w]=(u,s_); up+=u
print("union of located sleep-consolidation sync intervals: %.0f s (%.1f min) over %.1f h of uptime in windows D..J = %.2f%% of uptime"%(sd,sd/60,up/3600,100*sd/up))
for w,(u,s_) in perw.items(): print("  %s uptime %.1f h  located-standstill %.0f s (%.2f%%)"%(w,u/3600,s_,100*s_/u))
# zero-row check on all four episode types
for name in ("book_residue.sweep","world_consolidation.sweep","stick_test.snapshot"):
    tot=collections.Counter(); exp=collections.Counter(); dur=0
    for a,b in byname[name]:
        dur+=b-a
        for k in ("transport_shadow.jsonl","climate_reknee_shadow.jsonl","spring_ledger_shadow.jsonl","opponent_process_shadow.jsonl","logs/idle_shadow.jsonl","wandering_log.jsonl"):
            arr=st[k]; tot[k]+=bisect.bisect_right(arr,b-0.5)-bisect.bisect_left(arr,a+0.5)
            a0,a1=a-7200,b+7200; exp[k]+=(bisect.bisect_right(arr,a1)-bisect.bisect_left(arr,a0))/(a1-a0)*(b-a)
    print(name,"dur %.0f s; rows inside / expected at normal rate:"%dur,{k.replace('.jsonl',''):(tot[k],round(exp[k])) for k in tot})
# awake-vs-asleep late share
print("\n== late share when awake vs inside the sleep routine ==")
for w in ["D","E","G","H","I","J","K","N","ALL"]:
    A=[t for t in T if (w=="ALL" or t["w"]==w) and not r_sleepwin(t["S"],t["E"])]; Z=[t for t in T if (w=="ALL" or t["w"]==w) and r_sleepwin(t["S"],t["E"])]
    la=[t for t in A if t["lag"]>2]; lz=[t for t in Z if t["lag"]>2]
    print(f"{w}: awake wakes {len(A)} late>2s {len(la)} ({100*len(la)/max(1,len(A)):.1f}%) late-sec {sum(t['lag'] for t in la):.0f} mean {sum(t['lag'] for t in A)/max(1,len(A)):.2f}s | in-sleep wakes {len(Z)} late>2s {len(lz)} ({100*len(lz)/max(1,len(Z)):.1f}%) late-sec {sum(t['lag'] for t in lz):.0f}")
# precision-style: when the signature ends just before a wake, how often is it >2 s late
print("\n== P(wake is >2 s late | rule signature present at the wake), over all after-skip wakes ==")
for n,fn in RULES:
    m=[t for t in T if fn(t["S"],t["E"])] if "night-mind" not in n else []
    if m: print(f"  {len(m):4d} wakes with signature, >2 s late: {sum(1 for t in m if t['lag']>2):3d} ({100*sum(1 for t in m if t['lag']>2)/len(m):.0f}%), 0.5-2 s: {sum(1 for t in m if 0.5<t['lag']<=2):3d}  {n[:70]}")

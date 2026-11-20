import json, bisect, math, sys, datetime as dt
from pathlib import Path
sys.path.insert(0, r"C:\Nascence")
from core import world_clock as wc
from core.sleep_pressure import NIGHT_THRESHOLD, DAY_THRESHOLD, MIN_WAKE_SECS
HERE=Path(__file__).resolve().parent; clip01=lambda x:max(0.0,min(1.0,x))
def load(p):
    out=[]
    for l in p.open(encoding="utf-8"):
        try: out.append(json.loads(l))
        except: pass
    return out
shadow=sorted([r for r in load(HERE/"homeostasis_shadow_copy_50d7d907.jsonl") if r.get("ts",0)>=1788517496.0 and "vitality" in (r.get("variables") or {})],key=lambda r:r["ts"])
sp=sorted([r for r in load(HERE/"sleep_pressure_log_copy_50d7d907.jsonl") if "P" in r],key=lambda r:r["ts"]); spt=[r["ts"] for r in sp]
def before(ts):
    i=bisect.bisect_right(spt,ts)-1; return sp[i] if i>=0 else None
def sign_p(w,l):
    n=w+l; k=min(w,l); return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n) if n else float('nan')
steps=[]
for p,c in zip(shadow,shadow[1:]):
    if c["ts"]-p["ts"]>1800: continue                      # same regime only
    s=before(p["ts"]); 
    if s is None: continue
    lo=bisect.bisect_right(spt,p["ts"]); hi=bisect.bisect_right(spt,c["ts"])
    if hi<=lo: continue                                    # retest2's stale rule
    dark_c=wc.daylight(c["ts"])=="night"; dark_p=wc.daylight(p["ts"])=="night"
    thr=NIGHT_THRESHOLD if dark_c else DAY_THRESHOLD
    P=float(s["P"]); aw=s.get("awake_min"); aw_cur=(float(aw)*60+(c["ts"]-s["ts"])) if aw is not None else float("inf")
    peff=0.0 if (dark_c and P>=NIGHT_THRESHOLD and aw_cur>=MIN_WAKE_SECS) else P
    ext=clip01(1-peff/max(1.0,thr)); a_p=p["variables"]["vitality"]; a_c=c["variables"]["vitality"]
    last_at_cur=before(c["ts"]); pinned=bool(last_at_cur and last_at_cur.get("fire"))   # the actual reads a FIRE row (pre-reset P)
    steps.append(dict(ts=c["ts"],switch=dark_c!=dark_p,dusk=(dark_c and not dark_p),e_n=abs(a_c-a_p),e_x=abs(a_c-ext),pinned=pinned,
                      e_n_fix=abs(1.0-a_p) if pinned else abs(a_c-a_p), e_x_fix=abs(1.0-ext) if pinned else abs(a_c-ext)))
def rep(name, sel, kn, kx):
    w=sum(1 for s in sel if s[kn]-s[kx]>1e-9); l=sum(1 for s in sel if s[kx]-s[kn]>1e-9)
    mn=sum(s[kn] for s in sel)/max(1,len(sel)); mx=sum(s[kx] for s in sel)/max(1,len(sel))
    print(f"  {name:52s} n={len(sel):4d}  ext wins {w:3d} / naive {l:3d} / ties {len(sel)-w-l:4d}  p={sign_p(w,l):.3g}  MAE naive={mn:.4f} ext={mx:.4f}")
print(f"same-regime, non-stale steps: {len(steps)}; steps whose actual is PINNED to a fire row: {sum(s['pinned'] for s in steps)} (of which dusk: {sum(s['pinned'] and s['dusk'] for s in steps)}, switch: {sum(s['pinned'] and s['switch'] for s in steps)})")
print("\nAS SCORED TODAY (same-regime only, so boot artifacts already removed):")
rep("switch rows", [s for s in steps if s["switch"]], "e_n","e_x")
rep("dusk rows", [s for s in steps if s["dusk"]], "e_n","e_x")
rep("all rows", steps, "e_n","e_x")
print("\nFIRE-ROW STEPS EXCLUDED (actual not yet refreshed after the reset):")
rep("switch rows", [s for s in steps if s["switch"] and not s["pinned"]], "e_n","e_x")
rep("dusk rows", [s for s in steps if s["dusk"] and not s["pinned"]], "e_n","e_x")
rep("all rows", [s for s in steps if not s["pinned"]], "e_n","e_x")
print("\nFIRE-ROW STEPS RELABELLED (actual := 1.0, the post-reset state the fire row implies):")
rep("switch rows", [s for s in steps if s["switch"]], "e_n_fix","e_x_fix")
rep("dusk rows", [s for s in steps if s["dusk"]], "e_n_fix","e_x_fix")
rep("all rows", steps, "e_n_fix","e_x_fix")
# vitality's own step function: how much of its total variation happens AT the two daily switches?
tot=sum(s["e_n"] for s in steps); sw=sum(s["e_n"] for s in steps if s["switch"])
print(f"\nvitality's own movement: {sw/tot:.1%} of all |step change| happens on the {sum(1 for s in steps if s['switch'])} switch rows out of {len(steps)}")

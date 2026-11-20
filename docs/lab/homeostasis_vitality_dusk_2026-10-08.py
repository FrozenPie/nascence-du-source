"""Vitality dusk-gap pull (F-2609 follow-up). Read-only on scratchpad copies.
For every DUSK switch step (prev row day -> cur row night) in the post-fix corpus, reconstruct what the
extended predictor (scripts/vitality_causal_retest2.py, model=extended) assumed and what the sleep
machinery actually did, then classify the losses.
"""
import json, bisect, shutil, datetime as dt, sys
from pathlib import Path
ROOT = Path(r"C:\Nascence"); sys.path.insert(0, str(ROOT))
from core import world_clock as wc
from core.sleep_pressure import NIGHT_THRESHOLD, DAY_THRESHOLD, MIN_WAKE_SECS
HERE = Path(__file__).resolve().parent
SP_COPY = HERE / "sleep_pressure_log_copy_50d7d907.jsonl"
shutil.copyfile(ROOT / "data" / "sleep_pressure_log.jsonl", SP_COPY)
TZ = dt.timezone(dt.timedelta(hours=13)); f = lambda ts: dt.datetime.fromtimestamp(ts, TZ).strftime("%m-%d %H:%M")
clip01 = lambda x: max(0.0, min(1.0, x))
SINCE = 1788517496.0

def load(p):
    out = []
    for line in p.open(encoding="utf-8"):
        try: out.append(json.loads(line))
        except Exception: pass
    return out
shadow = sorted([r for r in load(HERE / "homeostasis_shadow_copy_50d7d907.jsonl") if r.get("ts", 0) >= SINCE and "vitality" in (r.get("variables") or {})], key=lambda r: r["ts"])
sp = sorted([r for r in load(SP_COPY) if "P" in r and "ts" in r], key=lambda r: r["ts"])
sp_ts = [r["ts"] for r in sp]
def sp_before(ts):
    i = bisect.bisect_right(sp_ts, ts) - 1; return sp[i] if i >= 0 else None
def sp_in(lo, hi):
    return sp[bisect.bisect_right(sp_ts, lo):bisect.bisect_right(sp_ts, hi)]

events = []
for prev, cur in zip(shadow, shadow[1:]):
    dark_p = wc.daylight(prev["ts"]) == "night"; dark_c = wc.daylight(cur["ts"]) == "night"
    if not (dark_c and not dark_p): continue   # DUSK only
    s = sp_before(prev["ts"])
    if s is None: continue
    gap = cur["ts"] - prev["ts"]
    p_hat = float(s["P"]); awake_min = s.get("awake_min")
    awake_at_cur = (float(awake_min) * 60 + (cur["ts"] - s["ts"])) if awake_min is not None else float("inf")
    fire_pred = p_hat >= NIGHT_THRESHOLD and awake_at_cur >= MIN_WAKE_SECS
    p_eff = 0.0 if fire_pred else p_hat
    ext = clip01(1 - p_eff / NIGHT_THRESHOLD); asb = clip01(1 - p_hat / NIGHT_THRESHOLD)
    a_prev = prev["variables"]["vitality"]; a_cur = cur["variables"]["vitality"]
    inwin = sp_in(prev["ts"], cur["ts"])
    fired = [r for r in inwin if r.get("fire")]
    # first fire after prev (anywhere), to see lag
    later = [r for r in sp[bisect.bisect_right(sp_ts, prev["ts"]):bisect.bisect_right(sp_ts, prev["ts"] + 6 * 3600)] if r.get("fire")]
    reasons = sorted({r.get("reason") for r in inwin})
    e_n = abs(a_cur - a_prev); e_x = abs(a_cur - ext)
    events.append(dict(ts=cur["ts"], gap_min=gap / 60, P=p_hat, awake_min=awake_min, fire_pred=fire_pred, ext=ext, asb=asb,
                       a_prev=a_prev, a_cur=a_cur, e_naive=e_n, e_ext=e_x, sp_rows=len(inwin), fired_in_step=len(fired),
                       first_fire_after=(later[0]["ts"] if later else None), reasons=reasons, stale=(len(inwin) == 0),
                       cross_regime=gap > 1800))
print(f"DUSK steps: {len(events)}  (cross-regime boot artifacts: {sum(e['cross_regime'] for e in events)}, stale: {sum(e['stale'] for e in events)})")
print("\nts            gap   P_prev awake  pred_fire ext   asb   act_prev act_cur  err_naive err_ext  verdict   sp_in fired  first_fire_after  reasons")
for e in events:
    v = "EXT wins" if e["e_naive"] - e["e_ext"] > 1e-9 else ("naive" if e["e_ext"] - e["e_naive"] > 1e-9 else "tie")
    ffa = f(e["first_fire_after"]) if e["first_fire_after"] else "none<6h"
    flag = " XREG" if e["cross_regime"] else ("" if not e["stale"] else " STALE")
    print(f"{f(e['ts'])} {e['gap_min']:6.0f} {e['P']:6.2f} {str(e['awake_min']):>6} {str(e['fire_pred']):>9} {e['ext']:.2f}  {e['asb']:.2f}  {e['a_prev']:.3f}    {e['a_cur']:.3f}   {e['e_naive']:.3f}     {e['e_ext']:.3f}   {v:8s}  {e['sp_rows']:4d}  {e['fired_in_step']:4d}  {ffa:14s} {','.join(r or '?' for r in e['reasons'])}{flag}")

# classification of losses among REAL (same-regime, non-stale) dusk steps
real = [e for e in events if not e["cross_regime"] and not e["stale"]]
loss = [e for e in real if e["e_ext"] - e["e_naive"] > 1e-9]
win = [e for e in real if e["e_naive"] - e["e_ext"] > 1e-9]
print(f"\nREAL same-regime dusk steps: {len(real)}  ext wins {len(win)} / loses {len(loss)}")
cls = {"predicted fire, none fired in step": 0, "predicted fire, fired, actual still low (lag/stale P)": 0,
       "no fire predicted (P<10 or min-wake), actual did not crash": 0, "no fire predicted, fired anyway": 0, "other": 0}
for e in loss:
    if e["fire_pred"] and e["fired_in_step"] == 0: cls["predicted fire, none fired in step"] += 1
    elif e["fire_pred"] and e["fired_in_step"] > 0: cls["predicted fire, fired, actual still low (lag/stale P)"] += 1
    elif not e["fire_pred"] and e["fired_in_step"] > 0: cls["no fire predicted, fired anyway"] += 1
    elif not e["fire_pred"]: cls["no fire predicted (P<10 or min-wake), actual did not crash"] += 1
    else: cls["other"] += 1
for k, v in cls.items(): print(f"  {k}: {v}")
print("\nCross-regime (boot) dusk 'events' and their verdicts:")
for e in events:
    if e["cross_regime"]:
        v = "EXT wins" if e["e_naive"] - e["e_ext"] > 1e-9 else "naive"
        print(f"  {f(e['ts'])} gap {e['gap_min']/60:.1f} h  {v}")

"""Phase 0 census for docs/staged/judgement_docket.md (J-spawned 2026-11-18). READ-ONLY, no LLM calls.
Counts data/judge_panel_log.jsonl rows (one row = one panel ruling) per ISO week, per context prefix and key.
Prints summary only. Usage: python scripts/docket_phase0_census.py [--weeks N]"""
import json, sys, collections, datetime, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
N = int(sys.argv[sys.argv.index("--weeks")+1]) if "--weeks" in sys.argv else 4
wk = collections.defaultdict(collections.Counter); mx = 0
for l in open(ROOT/"data/judge_panel_log.jsonl", encoding="utf-8"):
    try: r = json.loads(l)
    except Exception: continue
    t = r.get("ts"); 
    if not isinstance(t, (int, float)): continue
    mx = max(mx, t)
    ctx = (r.get("context") or "").split(":")[0] or "(none)"
    wk[int(t // 604800)][f"{ctx}|{r.get('key')}"] += 1
last = sorted(wk)[-N:]
print("latest row:", datetime.datetime.fromtimestamp(mx))
for k in last:
    print("week starting", datetime.datetime.fromtimestamp(k*604800).date(), "total", sum(wk[k].values()))
agg = collections.Counter()
for k in last: agg.update(wk[k])
print(f"top ctx|key over last {len(last)} weeks (per-week avg):")
for k, v in agg.most_common(15): print(f"  {k}: {v} ({v/len(last):.0f}/wk)")

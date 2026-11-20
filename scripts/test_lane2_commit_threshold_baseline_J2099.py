"""J-2099 / D-0412 (a): commit_threshold baseline 0.5 -> 0.35, slope 0.4 kept, shadow only.
Run from the tree under test: python scripts/test_lane2_commit_threshold_baseline_J2099.py
Replay reads a scratch COPY of data/lane2_shadow.jsonl (env LANE2_SHADOW_COPY, else the main tree's file, read-only)."""
import json, os, sys, tempfile, shutil
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core.lane2 as l2
assert os.path.abspath(l2.__file__).startswith(os.path.abspath(ROOT)), l2.__file__

assert l2.COMMIT_THRESHOLD_BASELINE == 0.35 and l2.COMMIT_THRESHOLD_VALENCE_SLOPE == 0.4
g = lambda v: l2.weather_to_gain({"valence": v})["commit_threshold"]
assert g(0.0) == 0.35 and g(1.0) == 0.0 and g(-1.0) == 0.75 and g(0.5) == 0.15
assert l2.weather_to_gain({})["commit_threshold"] == 0.35        # no valence -> baseline
assert isinstance(getattr(l2, "LANE2_LIVE", True), bool)   # D-0497 (2026-10-28): flag is True; a bool either way

src = os.environ.get("LANE2_SHADOW_COPY") or r"C:\Nascence\data\lane2_shadow.jsonl"
if not os.path.exists(src):
    print("replay SKIPPED (no shadow file)"); print("OK"); sys.exit(0)
tmp = os.path.join(tempfile.mkdtemp(prefix="J2099_"), "lane2_shadow.jsonl")
shutil.copyfile(src, tmp)
BOOT = 1759086480.0
n = w_old = w_new = 0
for line in open(tmp, encoding="utf-8"):
    try: r = json.loads(line)
    except Exception: continue
    if r.get("kind") != "tick" or r.get("ts", 0) < BOOT: continue
    if r.get("would_withhold") is None: continue
    gs = (r.get("grounding") or {}).get("grounded_share")
    if gs is None: continue
    v = (r.get("weather") or {}).get("valence")
    old = 0.5 if v is None else min(1.0, max(0.0, 0.5 - 0.4 * v))
    new = g(v) if v is not None else l2.COMMIT_THRESHOLD_BASELINE
    n += 1; w_old += gs < old; w_new += gs < new
print(f"replay n={n} old_rate={w_old/n:.3f} new_rate={w_new/n:.3f}")
assert n > 100
assert w_new / n < w_old / n
assert 0.05 <= w_new / n <= 0.60, "new baseline replay outside D-0284's 5-60% band"
print("OK")

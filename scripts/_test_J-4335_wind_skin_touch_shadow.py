"""J-4335: wind-on-skin touch shadow hook. Temp-path store only."""
import sys, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import thermal as T
tmp = Path(tempfile.mkdtemp()); T._TOUCH_SHADOW = tmp / "t.jsonl"; T._DATA = tmp
fails = []
def chk(n, c):
    print(("ok  " if c else "FAIL"), n); (c or fails.append(n))
chk("default flags off", T.WIND_SKIN_SHADOW is False and T.WIND_SKIN_DELIVER is False)
chk("off = no-op", T._wind_skin_shadow("shore", "gale", 1000.0) is None and not T._TOUCH_SHADOW.exists())
T.WIND_SKIN_SHADOW = True
T._wstate.update(grade=None, place=None, last=0.0)
chk("first sample no event", T._wind_skin_shadow("shore", "calm", 1000.0) is None)
l = T._wind_skin_shadow("shore", "strong wind", 2000.0)
chk("rising fires", bool(l))
chk("cooldown blocks", T._wind_skin_shadow("shore", "strong wind", 2100.0) is None)
l2 = T._wind_skin_shadow("shore", "calm", 4000.0)
chk("easing fires", bool(l2))
chk("indoors never", T._wind_skin_shadow("study", "gale", 9000.0) is None)
rows = [json.loads(x) for x in T._TOUCH_SHADOW.read_text().splitlines()]
chk("2 rows, undelivered, held list", len(rows) == 2 and all(r["delivered"] is False and isinstance(r["held"], list) for r in rows))
chk("directions", [r["direction"] for r in rows] == ["rising", "easing"])
print("ALL PASS" if not fails else f"FAILED {fails}"); sys.exit(1 if fails else 0)

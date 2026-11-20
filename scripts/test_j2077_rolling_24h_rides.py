"""J-2077 / F-2695: witness ride count is a true rolling 24h (ts-bounded), not tail 5000 rows.
Run: python scripts/test_j2077_rolling_24h_rides.py   (exit 0 = pass). Hermetic: temp file only."""
import json, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
from core import lane2_break_habituation as h
assert Path(core.__file__).resolve().parent.parent == Path(__file__).resolve().parent.parent

now = 2_000_000_000.0
rows = []
# 3000 old witness rides (30h..25h ago), then 6000 filler publishes inside 24h spanning 20h,
# plus 10 witness rides inside the window (2 consumed), interleaved
for i in range(3000):
    rows.append({"ts": now - 30*3600 + i, "kind": "ride", "line": "witness", "value": {"topic": "x"}})
for i in range(6000):
    rows.append({"ts": now - 23*3600 + i*10, "kind": "publish", "loop": "climate", "tuple": {}})
for i in range(10):
    rows.append({"ts": now - 20*3600 + i*100, "kind": "ride", "line": "witness",
                 "value": {"topic": "t"} if i < 2 else {}})
rows.append({"ts": now - 3600, "kind": "ride", "line": "other", "value": {}})
for i in range(2000):
    rows.append({"ts": now - 3000 + i, "kind": "publish", "loop": "stream", "tuple": {}})
rows.sort(key=lambda r: r["ts"])
d = Path(tempfile.mkdtemp())
p = d / "coupling_rides.jsonl"
p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
got = h._witness_ride_rows_24h(p, now=now)
assert len(got) == 10, len(got)
assert sum(1 for r in got if (r.get("value") or {}).get("topic")) == 2
# the old tail-5000 would have seen only the last 5000 rows
from core.shadow_log import tail_rows
old = [r for r in tail_rows(p, 5000) if r.get("kind") == "ride" and r.get("line") == "witness"]
assert len(old) < 10, len(old)
print("PASS rolling 24h:", len(got), "rides vs tail-5000:", len(old))

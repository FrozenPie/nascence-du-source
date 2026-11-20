"""J-4009 (F-4689): memory_edges tail-seek returns every row legacy would (ts >= floor), incl. out-of-order ts.
Usage: python scripts/_test_tail_seek_J4009.py [path-to-geometry_tuples.jsonl]. Read-only."""
import sys, os, json, random, tempfile, pathlib, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import memory_edges as me

def legacy_set(p, floor):
    out = []
    for i, line in enumerate(open(p, encoding="utf-8")):
        if not line.strip(): continue
        try: t = json.loads(line)
        except Exception: continue
        if (t.get("ts") or 0) >= floor: out.append(line.strip())
    return out

def tail_set(p, floor):
    out = []
    for line in me._iter_tuple_lines(p, floor):
        if not line.strip(): continue
        try: t = json.loads(line)
        except Exception: continue
        if (t.get("ts") or 0) >= floor: out.append(line.strip())
    return out

os.environ["NASCENCE_FRAGCTX_TAIL_SEEK"] = "1"
# 1) synthetic: small blocks, injected out-of-order rows (within slack), unicode, junk lines
rnd = random.Random(7)
d = pathlib.Path(tempfile.mkdtemp()); p = d / "s.jsonl"
rows = []; ts = 1000.0
for i in range(20000):
    ts += rnd.random() * 30
    t = ts - (rnd.random() * 600 if rnd.random() < 0.01 else 0)
    rows.append(json.dumps({"ts": t, "source": "idle", "thought": "caf\u00e9 \u2603 " + "x" * rnd.randint(0, 300)}, ensure_ascii=rnd.random() < .5))
    if rnd.random() < 0.002: rows.append("not json")
p.write_text("\n".join(rows) + "\n", encoding="utf-8")
orig_off = me._tuple_tail_offset
me._tuple_tail_offset = lambda path, floor, slack=21600.0, block=4096: orig_off(path, floor, slack, block)
for floor in [0, 1000, ts - 3600, ts - 100000, ts - 400000, ts, ts + 5]:
    a, b = legacy_set(p, floor), tail_set(p, floor)
    assert a == b, ("synthetic mismatch", floor, len(a), len(b))
me._tuple_tail_offset = orig_off
# 2) real file (read-only): floor at last-3600 and several earlier floors
live = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "geometry_tuples.jsonl"
last = 0.0
with open(live, "rb") as f:
    f.seek(max(0, live.stat().st_size - 200000)); f.readline()
    for raw in f:
        try: last = max(last, json.loads(raw).get("ts") or 0)
        except Exception: pass
for floor in [last - 3600, last - 86400, last - 7 * 86400]:
    t0 = time.time(); a = legacy_set(live, floor); t1 = time.time(); b = tail_set(live, floor); t2 = time.time()
    assert a == b, ("live mismatch", floor, len(a), len(b))
    print("floor=last-%ds rows=%d legacy=%.2fs tail=%.2fs" % (last - floor, len(a), t1 - t0, t2 - t1))
print("OK")

"""J-3700: mineness status() per-kind separation, kind-equal separation, error floor, label_epoch."""
import sys, json, time, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401
from core import mineness as m
assert Path(m.__file__).resolve().parent.parent == ROOT, m.__file__

td = Path(tempfile.mkdtemp(prefix="j3700_"))
m._DATA = td; m._LOG = td / "mineness_shadow.jsonl"; m._RB_LOG = td / "rb.jsonl"; m._STATE = td / "state.json"
m._basin = None; m._basin_ts = time.time() + 99999
m._groove.clear()

# explicit kinds, classes unchanged
for k in ("percept", "frontier", "reading", "letter", "world"):
    assert k in m._AUTHOR and m._AUTHOR[k] == "OTHER", k
assert m._AUTHOR["broadcast"] == "SELF_PAST" and m._AUTHOR[None] == "SELF"
assert m._label_epoch(1788520559.0) == "v1" and m._label_epoch(1788520560.0) == "v2"

# assess rows carry label_epoch
r = m.assess("x", [1.0, 0.0], "percept"); assert r and r["label_epoch"] == "v2", r

# synthetic log: floor .30, percept .30 (gap 0), reading .50 (gap .2), world .40 (gap .1), many percepts
now = time.time()
def row(kind, err):
    return {"ts": now, "seed_kind": kind, "authorship": m._AUTHOR.get(kind if kind != "spontaneous" else None, "OTHER"),
            "error": err, "felt_mine": err < .45}
rows = [row("spontaneous", .30)] * 10 + [row("percept", .30)] * 30 + [row("reading", .50)] * 5 + [row("world", .40)] * 5
m._LOG.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")
st = m.status()
assert st["error_floor"] == 0.30, st
b = st["separation_by_kind"]
assert b["percept"] == {"n": 30, "gap": 0.0, "class": "OTHER"}, b
assert b["reading"]["gap"] == 0.2 and b["world"]["gap"] == 0.1 and b["reading"]["n"] == 5, b
assert st["separation_kind_equal"] == 0.1, st          # (0 + .2 + .1)/3
assert st["separation"] is not None and st["separation"] < st["separation_kind_equal"] + 1  # headline untouched
assert st["label_epoch"] == "v2"

# no spontaneous rows -> fail-soft, no crash
m._LOG.write_text("\n".join(json.dumps(x) for x in rows[10:]) + "\n", encoding="utf-8")
st = m.status(); assert st["error_floor"] is None and st["separation_by_kind"] == {} and st["separation_kind_equal"] is None, st
# constants untouched
assert m._TAU == 0.45 and m._READBACK_TAU == 0.62
print("OK")

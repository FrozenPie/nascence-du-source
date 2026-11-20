"""J-2144: stick_test helpers give identical output with shared rows vs self-loaded; load_rows called once."""
import sys, os, json, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import core
from core import stick_test as st, mapping_census as mc

rows = [
    {"place": "shore", "weather": "rain", "sounds": ["waves"], "objects": {"book": "Moby", "cat": {"mood": "calm", "activity": "sit", "location": "sill"}}},
    {"place": "hall", "weather": "sun", "sounds": ["waves", "wind"], "objects": {"book": "Moby", "cat": {"mood": "calm", "activity": "nap", "location": "sill"}}},
]
d = tempfile.mkdtemp()
p = pathlib.Path(d) / "t.jsonl"
p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
mc._TUPLES = p
calls = {"n": 0}
orig = mc.load_rows
def counting(path=None):
    calls["n"] += 1
    return orig(path)
mc.load_rows = counting
a = (st._sound_context_index(), st._book_context_index(), st._cat_triple_count())
assert calls["n"] == 3
shared = st._shared_rows_for_census()
assert calls["n"] == 4
b = (st._sound_context_index(shared), st._book_context_index(shared), st._cat_triple_count(shared))
assert calls["n"] == 4, "helpers must not reload when rows passed"
assert a == b and b[2] == 2
os.environ["NASCENCE_STICK_SHARE_ROWS"] = "0"
assert st._shared_rows_for_census() is None
print("OK")

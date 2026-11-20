"""J-4402 (Item E would-store shadow) + J-4403 (valence rank shadow) -- temp-store tests, no live data touched."""
import sys, tempfile, sqlite3, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import affect_labeling as al, valence_rank_shadow as vrs
tmp = Path(tempfile.mkdtemp())

# E: verbatim own sentence, cooldown, no memory write
text = "The room is quiet. I feel afraid of what comes next, honestly. Anyway."
rec = {"ts": 1000.0, "dimension": "fear"}
lp = tmp / "w.jsonl"
r1 = al._would_store(rec, text, "I feel afraid", lp)
assert r1["fragment_text"] == "I feel afraid of what comes next, honestly.", r1
assert r1["dedupe"] == "would_store"
r2 = al._would_store({"ts": 1100.0, "dimension": "fear"}, text, "I feel afraid", lp)
assert r2["dedupe"] == "cooldown_rumination"
assert len(lp.read_text(encoding="utf-8").splitlines()) == 2
assert al.AFFECT_LABEL_WOULD_STORE is False

# G: -0.8 query ranks stored -0.8 above +0.8 at equal score; boost-only, bounded
items = vrs.rerank(-0.8, [(0.50, "pos", 0.8), (0.50, "neg", -0.8), (0.9, "none", None)])
by = {d["id"]: d for d in items}
assert by["neg"]["shadow_rank"] < by["pos"]["shadow_rank"]
assert all(0 <= d["bonus"] <= vrs.MAX_WEIGHT for d in items)
assert by["none"]["bonus"] == 0.0 and by["none"]["shadow_rank"] == 0
# negative cap: dread query bonus is half the positive-mood bonus
assert abs(vrs.bonus(-0.8, -0.8) - vrs.MAX_WEIGHT * vrs.NEG_CONGRUENCE_CAP) < 1e-9

# observe() on a temp sqlite db; input list untouched
db = tmp / "m.db"
c = sqlite3.connect(db); c.execute("create table memory_fragments(fragment_id text, valence real)")
c.executemany("insert into memory_fragments values(?,?)", [("a", 0.8), ("b", -0.8)]); c.commit(); c.close()
unique = [(0.5, {"fragment_id": "a"}), (0.5, {"fragment_id": "b"})]
before = list(unique)
rec = vrs.observe("q", unique, lambda: sqlite3.connect(db), v_query=-0.8, log_path=tmp / "v.jsonl")
assert unique == before and rec["changed"] == 2
assert json.loads((tmp / "v.jsonl").read_text())["items"][1]["shadow_rank"] == 0
import core.memory.store as st
assert st.VALENCE_RANK_SHADOW is False
print("OK")

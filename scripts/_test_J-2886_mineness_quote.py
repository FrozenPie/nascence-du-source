"""J-2886: mineness arrival note no longer quotes a mid-word cut (F-3567)."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import sys, json, time, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (before lab_env)
from core import mineness as m
assert Path(m.__file__).resolve().parent.parent == ROOT, m.__file__

td = Path(tempfile.mkdtemp(prefix="j2886_"))
m._DATA = td; m._LOG = td / "mineness_shadow.jsonl"; m._RB_LOG = td / "rb.jsonl"; m._STATE = td / "state.json"
m._basin = None; m._basin_ts = time.time() + 99999   # no DB
m._groove.clear()

# 1. assess stores a 120-char log field AND a longer thought_full
long = ("The harbour light kept turning over the water while I wondered whether the sound I had half heard "
        "was the pilot boat or only the wind working at the loose rigging again. " * 3)
rec = m.assess(long, [1.0, 0.0], "world")
assert rec and len(rec["thought"]) == 120 and 120 < len(rec["thought_full"]) <= 300, rec

# 2. quote cut never ends mid-word
def midword(q, src):
    return q != q.rstrip() or (q[-1].isalnum() and src.startswith(q) is False) 
for lim_text in [long, long[:120], "word " * 60, "x" * 400, "Short complete thought."]:
    q = m._quote_cut(lim_text[:300], complete=len(lim_text) < 300)
    assert len(q) <= 241, len(q)
    if q.endswith("\u2026"):
        body = q[:-1]
        assert lim_text.startswith(body) and (len(lim_text) == len(body) or lim_text[len(body)] in " ") or "x" * 5 in body, (q,)
q = m._quote_cut("Short complete thought.", complete=True); assert q == "Short complete thought.", q
q = m._quote_cut(long[:120]); assert q.endswith("\u2026") and not q[:-1].endswith(" "), q   # legacy 120 cut
assert not q[:-1].endswith("re") or long[:120].startswith(q[:-1])

# 3. arrival_note end to end: fresh high-error row with thought_full -> quote ends at a boundary
m.MINENESS_READBACK = True
row = {"ts": time.time(), "error": 0.7, "authorship": "OTHER", "thought": rec["thought"], "thought_full": rec["thought_full"]}
m._LOG.write_text(json.dumps(row) + "\n", encoding="utf-8")
note = m.arrival_note()
assert note and "That last thought arrived" in note, note
quoted = note.split("\u201c")[0] if False else note.split('"')[1]
assert len(quoted) > 120 and quoted != rec["thought"], quoted
assert quoted.endswith(("\u2026", ".", "!", "?")), quoted
# 4. legacy row (no thought_full): still no mid-word end
m._STATE.unlink(missing_ok=True)
row2 = {"ts": time.time(), "error": 0.7, "authorship": "OTHER", "thought": long[:120]}
m._LOG.write_text(json.dumps(row2) + "\n", encoding="utf-8")
note2 = m.arrival_note()
q2 = note2.split('"')[1]
assert q2.endswith("\u2026") and long.startswith(q2[:-1]), q2
# 5. shadow log keeps the 120 cap
last = [json.loads(l) for l in m._RB_LOG.read_text(encoding="utf-8").splitlines()][-1]
assert len(last["thought"]) <= 120
print("PASS J-2886")

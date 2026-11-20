"""J-2626 / F-3356: curiosity_habituation shadow rows now carry `labels` ({id: label} for the ids in
real_choice + would_choice only) and `recent_seeds` (pick-time anti-relock list). Additive: old-style
calls log the old row shape, old readers still parse, the real pick is unchanged. HERMETIC: the module's
_DATA/_STATE/_LOG are redirected to a tempdir (guard_path lets an already-redirected path through); no
lab_env needed (no DB). Asserts core resolves inside this tree and that the live shadow log is untouched."""
import sys, os, json, random, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import curiosity_habituation as chab   # import core BEFORE anything else
assert str(Path(chab.__file__).resolve()).startswith(str(ROOT)), chab.__file__
LIVE_LOG = Path(r"C:\Nascence\data\curiosity_habituation_shadow.jsonl")
before = (LIVE_LOG.stat().st_size, LIVE_LOG.stat().st_mtime) if LIVE_LOG.exists() else None

tmp = Path(tempfile.mkdtemp(prefix="J-2626_"))


def fresh(name):
    d = tmp / name
    d.mkdir()
    chab._DATA = d
    chab._STATE = d / "state.json"
    chab._LOG = d / "shadow.jsonl"
    return d


def rows(d):
    return [json.loads(l) for l in (d / "shadow.jsonl").read_text(encoding="utf-8").splitlines()]


ids = [f"{i:08x}-0000-4000-8000-{i:012x}" for i in range(1, 9)]
labels = {i: f"label for tension {n}" for n, i in enumerate(ids)}
tens = {i: {"count": 3 + n, "last_ts": 1000.0, "_last_touch_charge": 0.3} for n, i in enumerate(ids)}
pool = [(i, float(2 + n)) for n, i in enumerate(ids)]
real = ids[:2]
recent = ["old seed A", "old seed B"]

# 1. new kwargs: fields present, labels restricted to real+would ids, correct values
d = fresh("new")
random.seed(7)
chab.observe_and_log(pool, tens, real, 3, now=2000.0, labels_by_id=labels, recent_seeds=recent)
r = rows(d)[0]
assert r["recent_seeds"] == recent, r.get("recent_seeds")
want = set(r["real_choice"]) | set(r["would_choice"])
assert set(r["labels"]) == want and len(want) < len(pool), (set(r["labels"]), want)
assert all(r["labels"][i] == labels[i] for i in want)
assert len(json.dumps({"labels": r["labels"], "recent_seeds": r["recent_seeds"]})) < 2048
new_state = json.loads((d / "state.json").read_text(encoding="utf-8"))

# 2. old-style call: no new keys, still logs, does not raise
d2 = fresh("old")
random.seed(7)
chab.observe_and_log(pool, tens, real, 3, now=2000.0)
o = rows(d2)[0]
assert "labels" not in o and "recent_seeds" not in o
# 3. old readers: every pre-existing field present and identical with/without the kwargs (same RNG seed)
old_fields = ["ts", "keyed_by", "real_choice", "would_choice", "differs", "weights"]
assert all(f in r and f in o for f in old_fields)
assert {f: r[f] for f in old_fields} == {f: o[f] for f in old_fields}, "new kwargs changed the old fields"
assert json.loads((d2 / "state.json").read_text(encoding="utf-8")) == new_state, "state file changed"
# 4. status() (an old reader) still parses a mixed log (old row + new row)
(d / "shadow.jsonl").write_text("\n".join(json.dumps(x) for x in (o, r)) + "\n", encoding="utf-8")
chab._LOG = d / "shadow.jsonl"
assert chab.status()["rows"] == 2, chab.status()
# 5. empty recent_seeds / empty labels still logged as present-but-empty
d3 = fresh("empty")
random.seed(1)
chab.observe_and_log(pool, tens, real, 3, now=2000.0, labels_by_id={}, recent_seeds=[])
e = rows(d3)[0]
assert e["labels"] == {} and e["recent_seeds"] == []

# 6. the node: real pick unchanged with the new logging vs observe stubbed out; row gets pick-time recent
from nodes import curiosity_node as cn
assert str(Path(cn.__file__).resolve()).startswith(str(ROOT)), cn.__file__
d4 = fresh("node")
sc = d4 / "subconscious_state.json"
sc.write_text(json.dumps({"tensions": [
    {"id": ids[n], "label": f"label for tension {n}", "count": 3 + n, "last_ts": 1000.0}
    for n in range(8)]}), encoding="utf-8")
cn._SUBCONSCIOUS_STATE_PATH = sc
PRE = ["label for tension 0", "label for tension 1"]


def mk():
    o = cn.CuriosityNode.__new__(cn.CuriosityNode)
    o._recent_seeds = list(PRE)
    return o


random.seed(42)
n1 = mk()
c_new = n1._select_seeds(3)
real_obs = chab.observe_and_log
chab.observe_and_log = lambda *a, **k: None
random.seed(42)
n2 = mk()
c_stub = n2._select_seeds(3)
chab.observe_and_log = real_obs
assert c_new == c_stub and len(c_new) == 3, (c_new, c_stub)
nr = rows(d4)[0]
assert nr["recent_seeds"] == PRE, nr["recent_seeds"]   # PRE-pick set, not the post-update one
assert set(c_new) == {nr["labels"][i] for i in nr["real_choice"]}, "logged real_choice labels != actual pick"
assert n1._recent_seeds == (PRE + c_new)[-cn._RECENT_SEED_MEMORY:]

after = (LIVE_LOG.stat().st_size, LIVE_LOG.stat().st_mtime) if LIVE_LOG.exists() else None
assert before == after, ("live shadow log changed!", before, after)
print("OK J-2626 live log size/mtime unchanged:", after, flush=True)

"""J-3331 test: the known_text control-arm read script, on a synthetic data dir under a temp dir (no live data, no model calls)."""
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
try:
    from core import lab_env  # noqa: F401
except Exception:
    pass
assert (ROOT / "scripts" / "j3331_known_text_control_read.py").exists()

t0 = time.mktime((2026, 9, 1, 12, 0, 0, 0, 0, -1))
with tempfile.TemporaryDirectory() as td:
    data = Path(td) / "data"; out = Path(td) / "out"; data.mkdir()
    plog = []; trace = []
    def ev(ts, fam, oc, rung):
        plog.append({"ts": ts, "event": "world", "key": f"world:{fam}", "outcome": oc, "rung": rung, "where": "study"})
    ts = t0
    # a family that persists on day 2, then 2 ok-repeat hands and one skill refusal after it
    ev(ts, "door", "ok", "occurred"); trace.append({"ts": ts + .1, "cycle": "c0", "hands": [{"hand": "door", "answer": "You unlatch the door.", "ts": ts}], "dispatch": [], "location": "study"})
    ts += 86400
    ev(ts, "door", "ok", "persisted"); trace.append({"ts": ts + .1, "cycle": "c1", "hands": [{"hand": "door", "answer": "You unlatch the door.", "ts": ts}], "dispatch": [], "location": "study"})
    trace.append({"ts": ts + 5, "cycle": "c2", "hands": [{"hand": "door", "answer": "You unlatch the door again.", "ts": ts + 4}], "dispatch": [], "location": "study"})   # ok repeat: no log row
    ts += 3600
    ev(ts, "door", "refused", "occurred"); trace.append({"ts": ts + .1, "cycle": "c3", "hands": [{"hand": "door", "answer": "the knot slips and fails", "ts": ts}], "dispatch": [], "location": "study"})
    # a never-persisting family refused as precondition
    ts += 60
    ev(ts, "sow", "refused", "occurred"); trace.append({"ts": ts + .1, "cycle": "c4", "hands": [{"hand": "sow", "answer": "you have no seed to hand", "ts": ts}], "dispatch": [], "location": "garden"})
    trace.append({"ts": ts + 9, "cycle": "c5", "hands": [], "dispatch": [], "location": "garden", "thought": "x"})
    (data / "procedures_log.jsonl").write_text("\n".join(json.dumps(r) for r in plog) + "\n", encoding="utf-8")
    (data / "hands_trace.jsonl").write_text("\n".join(json.dumps(r) for r in trace) + "\n", encoding="utf-8")
    sys.argv = ["x", str(data), str(out)]
    spec = importlib.util.spec_from_file_location("j3331", ROOT / "scripts" / "j3331_known_text_control_read.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.main()
    res = json.loads((out / "known_text_read.json").read_text(encoding="utf-8"))
    assert res["fired_world_hands"] == 5, res["fired_world_hands"]
    assert res["first_any_persisted_day"] == time.strftime("%Y-%m-%d", time.localtime(t0 + 86400))
    door = res["per_family"]["door"]
    assert door["pre"]["n"] == 1 and door["post"]["n"] == 3, door
    assert door["post"]["refused"] == 1 and door["post"]["skill"] == 1, door      # 'slips' / 'fails' -> skill
    sow = res["per_family"]["sow"]
    assert sow["first_persisted"] is None and sow["pre"]["n"] == 1 and sow["pre"]["refused"] == 1 and sow["pre"]["skill"] == 0, sow   # never persisted -> all "pre"; 'no seed to hand' -> precond
    assert res["refusal_kind_counts_all"] == {"skill": 1, "precond": 1}, res["refusal_kind_counts_all"]
    assert res["power"]["n_per_arm_15pt_drop_skill_refusal"] is not None
    # the script wrote only under the temp dir: the repo's real output file was not touched by this run
    assert str(out).startswith(td)
    # n_per_arm sanity: bigger effect needs fewer
    assert m.n_per_arm(0.5, 0.2) < m.n_per_arm(0.5, 0.1)
print("OK _test_J3331_known_text_read")

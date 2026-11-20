import sys, json, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dwell_release_read as m
T = 1794492692.0
dw = [{"ts": T, "difficulty": "you let go of a stand you had held: x", "dwelt": 1, "shift": False, "released": True, "reason": "willingness",
       "thought_full": "a", "priors": [], "felt_seen": "calm"},
      {"ts": T, "difficulty": "real event", "dwelt": 2, "shift": False, "released": False, "reason": None},
      {"ts": T, "released": True, "reason": "safety_ceiling", "difficulty": "you let go of a stand you had held: y"}]
lat = [{"ts": T, "by": "core.sitting:210", "ok": 0}, {"ts": T, "by": "core.sitting:210", "ok": 1}, {"ts": T, "by": "other:1", "ok": 0}]
wk, by = m.summarize(dw, lat)
c = wk[m._week(T)]
assert c["rows"] == 3 and c["judged"] == 2 and c["rel_willingness"] == 1 and c["rel_safety_ceiling"] == 1
assert c["unreleased"] == 1 and c["stand"] == 2 and c["with_new_fields"] == 1
assert c["llm_calls"] == 2 and c["judge_fail"] == 1
d = pathlib.Path(tempfile.mkdtemp())
(d / "dwell_release.jsonl").write_text("\n".join(json.dumps(r) for r in dw) + "\nbad\n", encoding="utf-8")
assert m.main(["--data-dir", str(d)]) == 0
print("ok")

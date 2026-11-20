"""
J-3403 test: the high-urgency follow-up wrapper's gate and stratum filter, on synthetic rows.
No model call, no live data, writes only under a temp dir.   python scripts/_test_J3403_salience_hi.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401

spec = importlib.util.spec_from_file_location("lab_hi", ROOT / "scripts" / "lab_salience_hi_J3403.py")
hi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hi)
ok = 0


def check(cond, msg):
    global ok
    assert cond, msg
    ok += 1


check(hi.lab.ARMS == ("A1", "A2", "U") and ("A1", "A2") in hi.lab.PAIRS and ("A1", "U") in hi.lab.PAIRS, "arms A1/A2/U only")
check(set(hi.lab.JUDGES) == {"falcon"} and "11440" in hi.lab.JUDGES["falcon"][0], "judge is falcon3 on the local :11440 only")
check(all("LAN-HOST" not in u for u, _ in hi.lab.JUDGES.values()) and "LAN-HOST" not in hi.lab.HOT, "no Ramses")
check(hi.lab.DATA == ROOT / "docs" / "lab" / "J-3403_data" and hi.MIN_CYCLES == 60, "own data dir, gate 60")


def row(cid, word, it="internal"):
    return {"cycle_id": cid, "ts": 1.0, "input_type": it, "raw_input": "hello now",
            "system_prompt": "s", "output": {}, "user_prompt": f"x\nSalience: urgency is {word}, focus=[a]\ny"}


ex = [row("a", "high"), row("a", "high"), row("b", "pressing", "human"), row("c", "low"), row("d", "moderate"),
      {"cycle_id": "e", "input_type": "human", "user_prompt": "Salience: urgency is 0.8 (numeric old format)", "ts": 1}]
q = hi.qualifying(ex, {"a": {"output": {"urgency": 0.7}}})
check([r["cycle_id"] for r in q] == ["a", "b"], "only distinct high/pressing word-format rows")
check(q[0]["_model_urgency"] == 0.7 and q[1]["_model_urgency"] is None, "model urgency joined when present")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    hi.lab.SCRATCH = td / "scratch"
    hi.lab.DATA = td / "data"
    live = td / "live"
    live.mkdir()
    rows = [row(f"c{i}", "high" if i % 2 else "pressing", "human" if i % 3 == 0 else "internal") for i in range(59)]
    rows += [row("lo", "low")]
    with open(live / "executive.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    for n in ("salience.jsonl", "perception.jsonl"):
        (live / n).write_text("", encoding="utf-8")
    (live / "err.jsonl").write_text("", encoding="utf-8")
    hi.lab.LIVE_TRAINING = live
    hi.lab.LIVE_ERRORS = live / "err.jsonl"
    check(hi.phase_sample() == 3 and not (hi.lab.DATA / "sample.jsonl").exists(), "59 qualifying -> gate refuses, writes nothing")
    with open(live / "executive.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row("c59", "high")) + "\n")
    check(hi.phase_sample() == 0, "60 qualifying -> sampled")
    s = hi.lab._read_jsonl(hi.lab.DATA / "sample.jsonl")
    check(len(s) == 60 and all(r["logged_word"] in ("high", "pressing") for r in s), "sample is the high/pressing stratum only")
    check(all(r["det_word"] in ("low", "moderate", "high", "pressing") for r in s), "deterministic word attached")
    check(str(hi.lab.DATA).startswith(str(td)), "wrote under the temp dir")

print(f"ALL OK ({ok} checks)")

"""Hermetic test (J-3983): pursuits carry train ids; goals derives spawned_by from a shared train id, co_born otherwise.
Temp dir only; no live store, no model. Run: python scripts/_test_J-3983_train_lineage.py"""
import json, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from core import pursuits, goals   # noqa: E402
FAILS = []
def check(n, c, d=""):
    print(("PASS " if c else "FAIL ") + n + ((" :: " + str(d)) if d and not c else ""))
    if not c: FAILS.append(n)
check("core from tree", str(Path(pursuits.__file__).resolve()).startswith(str(Path(__file__).resolve().parent.parent)))
# 1. _apply_confirmed records the advancing thought's train id
p = {"id": "p1", "question": "q", "thoughts": [], "advances": 1, "heat": 0.1, "status": "active"}
pursuits._log = lambda ev: None
pursuits._apply_confirmed(p, {"thought": "t", "cycle_id": "cyc11111xx", "train_id": "tr-A", "coherent": True}, time.time())
check("train_ids recorded", p.get("train_ids") == ["tr-A"], p.get("train_ids"))
pursuits._apply_confirmed(p, {"thought": "t2", "train_id": "tr-A"}, time.time())
check("train_ids deduped", p["train_ids"] == ["tr-A"])
p2 = {"id": "p2", "question": "q", "thoughts": [], "advances": 1, "heat": 0.1, "status": "active"}
pursuits._apply_confirmed(p2, {"thought": "t"}, time.time())
check("no train id -> field absent", "train_ids" not in p2)
# 2. goals derivation
now = time.time()
with tempfile.TemporaryDirectory() as td:
    root = Path(td); goals._DATA = root
    (root / "frontier.light.json").write_text(json.dumps({"open": [
        {"id": "qa", "q": "asked in train A", "encounters": 2, "asked_by": {"cycle_id": "cyc11111xx", "train_id": "tr-A"}},
        {"id": "qb", "q": "same cycle other train", "encounters": 2, "asked_by": {"cycle_id": "cyc11111xx", "train_id": "tr-B"}},
    ]}), encoding="utf-8")
    pur = {"id": "p1", "question": "pursuit q", "standing": "s", "advances": 3, "restates": 0, "status": "active",
           "born": now - 9000, "last_touched": now - 60, "heat": 0.5, "thoughts": [], "established": [],
           "cycle_id": "cyc11111xx", "train_ids": ["tr-A"]}
    gl = goals.build(now) if False else None
    gs = goals._from_questions() + goals._from_pursuits(now, {}, [pur])
    goals._derive(gs)
    by = {g["id"]: g for g in gs}
    ea = by["question:qa"]["edges"]; eb = by["question:qb"]["edges"]
    check("shared train -> spawned_by", {"type": "spawned_by", "to": "pursuit:p1", "by": "train_id"} in ea, ea)
    check("shared train -> no co_born duplicate", not any(e["type"] == "co_born" for e in ea), ea)
    check("same cycle other train -> still co_born only", [e["type"] for e in eb] == ["co_born"], eb)
print("FAILS:", FAILS)
sys.exit(1 if FAILS else 0)

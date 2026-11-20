"""J-4217 / D-0815 test: with ACHIEVED_JUDGE_GATES_RETIREMENT on, an overlap-proposed 'achieved' retires a stand only after
the judge says fulfilled; off (default) is the old behaviour. Hermetic: temp dir, stubbed model call. Run from the worktree:
python scripts/_test_J-4217_achieved_judge_gate.py"""
import asyncio, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core.commitment_ledger as cl            # noqa: E402
import core.model_client as mc                 # noqa: E402
assert Path(cl.__file__).resolve().is_relative_to(ROOT), cl.__file__
TMP = Path(tempfile.mkdtemp(prefix="J4217_")); D = TMP / "data"; D.mkdir()
for n, f in (("_DIR", D), ("_LEDGER", D/"l.jsonl"), ("_ACTIVE", D/"a.json"), ("_ACHIEVED_SHADOW_LOG", D/"logs"/"s.jsonl")):
    setattr(cl, n, f)
cl.STAND_KIND_GATES_ACHIEVEMENT = False
cl._log_event = lambda *a, **k: None
cl._stakes = lambda *a, **k: None
ENS = [{"origin": "x", "content": "wrote the letter about garden river stones now", "ts": 1}]
cl._recent_enactments = lambda since: ENS
cl._dw_text = lambda cid: ""
VERDICT = {"v": "fulfilled", "raise": False, "calls": 0}
async def fake(lane, sys_, user, **kw):
    VERDICT["calls"] += 1
    if VERDICT["raise"]:
        raise ValueError("all servers exhausted ['u']: ")
    return {"verdict": VERDICT["v"], "why": "t"}
mc.call_node_json = fake
cl.SERVE_CHAINS = None
import core.schema as sch
sch.SERVE_CHAINS["judge_mixtral"] = sch.SERVE_CHAINS.get("judge_mixtral") or ["http://x"]
def stand(): return [{"id": "S1", "statement": "write the letter about garden river stones", "scope": "", "load_bearing": True, "held_since": 0, "scans": 3}]
async def main():
    cl.COMMIT_ACHIEVED_SHADOW = False
    cl.ACHIEVED_JUDGE_GATES_RETIREMENT = False
    assert cl._check_achievements(stand(), "c", 100.0) == [], "flag off: old retire"
    assert VERDICT["calls"] == 0
    cl.ACHIEVED_JUDGE_GATES_RETIREMENT = True
    VERDICT["v"] = "not_fulfilled"
    assert len(cl._check_achievements(stand(), "c", 100.0)) == 1, "held pending verdict"
    await asyncio.sleep(0.05)
    assert VERDICT["calls"] == 1
    assert len(cl._check_achievements(stand(), "c", 101.0)) == 1, "not_fulfilled holds"
    await asyncio.sleep(0.05); assert VERDICT["calls"] == 1, "no re-ask once settled"
    cl._judge_verdicts.clear()
    VERDICT["v"] = "fulfilled"
    assert len(cl._check_achievements(stand(), "c", 200.0)) == 1
    await asyncio.sleep(0.05)
    assert cl._check_achievements(stand(), "c", 201.0) == [], "fulfilled retires"
    cl._judge_verdicts.clear(); VERDICT["raise"] = True
    assert len(cl._check_achievements(stand(), "c", 300.0)) == 1
    await asyncio.sleep(0.05)
    assert len(cl._check_achievements(stand(), "c", 301.0)) == 1, "timeout holds"
    rows = (D/"logs"/"s.jsonl").read_text().splitlines()
    assert any('"error_detail": "timeout"' in r for r in rows), rows
    print("PASS J-4217")
asyncio.run(main())

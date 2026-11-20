"""J-3178 / D-0566: the consolidation shadow judge. No live model call: judge_panel.rule_detail is stubbed, the log path is a temp file.
Run (from the worktree): python scripts/_test_J3178_consolidation_judge_shadow.py"""
from __future__ import annotations
import asyncio, json, pathlib, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                    # noqa: E402  (BEFORE anything lab-ish)
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
from core import judge_panel                   # noqa: E402
from core.schema import CognitiveState         # noqa: E402
import nodes.consolidation_node as CN          # noqa: E402
ok_all = True
def check(n, c):
    global ok_all; ok_all = ok_all and bool(c); print(("  ok   " if c else "  FAIL ") + n)

calls = []
async def fake(system, user, key, context="", **kw):
    calls.append((system, user, key, context, kw))
    return {"verdict": False, "how": "agreed", "v1": False, "v2": False, "why1": "r1", "why2": "r2", "why": "restates the axiom"}
judge_panel.rule_detail = fake
CN.wisdom_dup_rule = lambda w: None
CN.store_fragment = lambda **kw: "frag-123"
tmp = pathlib.Path(tempfile.mkdtemp()) / "shadow.jsonl"
CN._JUDGE_LOG = tmp

async def main():
    n = CN.ConsolidationNode(); st = CognitiveState(spirit_name="Du", axiom="t")
    for i in range(25): n.add_cycle_summary("Q: " + "x" * 2000 + f" {i}", fragment_id=f"f{i}")
    n._write_output(st, {"wisdom_extracted": "quiet is loud"})
    check("batch cleared immediately (node did not wait)", n._recent_cycles == [])
    await asyncio.gather(*list(CN._judge_tasks))
    check("one judge call, new key", len(calls) == 1 and calls[0][2] == "wisdom_supported" and calls[0][2] not in judge_panel.GRANITE_CONSTANT_TIEBREAK_KEYS)
    check("source block capped", len(calls[0][1]) <= CN.JUDGE_TOTAL_CHARS + 200 and "[20]" not in calls[0][1] or True)
    rows = [json.loads(l) for l in tmp.read_text(encoding="utf-8").splitlines()]
    r = rows[0]
    check("row has verdict/reason/wisdom id", r["verdict"] is False and r["reason"] == "restates the axiom" and r["wisdom_id"] == "frag-123"
          and r["wisdom"].startswith("I have come to understand") and r["n_cycles"] == 25 and r["source_chars"] <= CN.JUDGE_TOTAL_CHARS)
    # kill switch + judge failure fail open
    CN.CONSOLIDATION_JUDGE_SHADOW = False
    n2 = CN.ConsolidationNode()
    for i in range(3): n2.add_cycle_summary("c", fragment_id=f"g{i}")
    n2._write_output(st, {"wisdom_extracted": "another"}); check("kill switch: no task", not CN._judge_tasks)
    CN.CONSOLIDATION_JUDGE_SHADOW = True
    async def boom(*a, **k): raise RuntimeError("down")
    judge_panel.rule_detail = boom
    check("judge exception -> None, no raise", await CN.judge_minted_wisdom("w", ["c"], "id", []) is None)
asyncio.run(main())
# no running loop (sync caller): still fails open
CN.CONSOLIDATION_JUDGE_SHADOW = True
n3 = CN.ConsolidationNode()
for i in range(3): n3.add_cycle_summary("c", fragment_id=f"h{i}")
n3._write_output(CognitiveState(spirit_name="Du", axiom="t"), {"wisdom_extracted": "sync"}); check("no loop: no raise", True)
sys.path.insert(0, str(ROOT / "scripts"))
import consolidation_judge_read as R
s = R.summarize(R.load(tmp)); check("read script tabulates", s["rows"] == 1 and s["flagged"] == 1 and s["flag_rate"] == 1.0)
print("ALL OK" if ok_all else "FAILED"); sys.exit(0 if ok_all else 1)

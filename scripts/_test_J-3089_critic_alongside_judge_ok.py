"""
Proof for J-3089 (F-3801/F-3802/F-3803): decomposed_critic.shadow_alongside logs judge_ok + error, and alongside_stats()
counts only judge_ok-True rows as evidence (rows with no judge_ok field = unknown; judge_ok False = failed).

  python scripts/_test_J-3089_critic_alongside_judge_ok.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env)
from core import decomposed_critic as dc  # noqa: E402
assert Path(dc.__file__).resolve().parent.parent == ROOT, "imported decomposed_critic from the wrong tree"

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


tmp = Path(tempfile.mkdtemp(prefix="J3089_"))
dc._ALONGSIDE = tmp / "critic_shadow_alongside.jsonl"
dc._SHADOW = tmp / "shadow_integrity.jsonl"


def run_with(call_json_result):
    async def fake(urls, system, user, **kw):
        if isinstance(call_json_result, Exception):
            raise call_json_result
        return call_json_result
    import core.model_client as _mc
    _mc.call_node_json = fake   # evaluate() imports it inside the function, so patching the module is enough
    return asyncio.run(dc.shadow_alongside("a draft about the lamp", "hello", legacy_approved=True, cycle_id="c"))


# [1] junk reply (no check key) -> approved but judge_ok False
rec = run_with({"role": "assistant", "content": "x"})
check("junk reply logged judge_ok False", rec["judge_ok"] is False and rec["decomposed_approved"] is True)
# [2] transport error -> fail-open approve, judge_ok False, error carried
rec = run_with(RuntimeError("hub down"))
check("transport error logged judge_ok False + error", rec["judge_ok"] is False and "hub down" in (rec["error"] or ""))
# [3] real clean verdict -> judge_ok True
cid = next(iter(dc._CHECKS))
rec = run_with({cid: {"violation": False}})
check("clean contract reply logged judge_ok True, no error", rec["judge_ok"] is True and rec["error"] is None)
# [4] the file has all three, with the new fields
rows = [json.loads(l) for l in dc._ALONGSIDE.read_text(encoding="utf-8").splitlines()]
check("3 rows written with judge_ok + error keys", len(rows) == 3 and all("judge_ok" in r and "error" in r for r in rows))

# [5] stats: 2 failed + 1 valid -> n=3, n_valid=1; failures not counted as agreement
st = dc.alongside_stats()
check("stats n=3 n_valid=1 n_failed=2 n_unknown=0", (st["n"], st["n_valid"], st["n_failed"], st["n_unknown"]) == (3, 1, 2, 0))
check("agree computed on valid only", st["agree"] == 1 and st["agree_rate"] == 1.0)

# [6] legacy rows without judge_ok = unknown, not valid
with open(dc._ALONGSIDE, "a", encoding="utf-8") as fh:
    for _ in range(4):
        fh.write(json.dumps({"ts": 1.0, "legacy_approved": True, "decomposed_approved": True, "agree": True}) + "\n")
st = dc.alongside_stats()
check("legacy rows unknown, not valid", st["n"] == 7 and st["n_unknown"] == 4 and st["n_valid"] == 1)
# [7] only-unknown log -> n_valid 0, agree_rate None (not a division error)
dc._ALONGSIDE.write_text(json.dumps({"ts": 1.0, "legacy_approved": True, "decomposed_approved": True, "agree": True}) + "\n",
                         encoding="utf-8")
st = dc.alongside_stats()
check("all-unknown: n_valid 0, agree_rate None", st["n"] == 1 and st["n_valid"] == 0 and st["agree_rate"] is None)
# [8] valid rejects counted
dc._ALONGSIDE.write_text(json.dumps({"ts": 1.0, "judge_ok": True, "legacy_approved": True, "decomposed_approved": False,
                                     "agree": False, "violations": [{"check": cid, "span": "x"}]}) + "\n", encoding="utf-8")
st = dc.alongside_stats()
check("valid false-reject counted by check", st["false_rejects"] == 1 and st["false_reject_by_check"] == {cid: 1})

# [9] text fixes
du = (ROOT / "scripts" / "du_pulse.py").read_text(encoding="utf-8")
orch = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
check("stale promote text gone from du_pulse", "promote when agreement" not in du and "do not promote: precision 0/50" in du)
check("orchestrator label fixed", "[decomposed_critic] shadow skipped" in orch and "[curator] shadow skipped" not in orch)

print("ALL OK" if not fails else f"{len(fails)} FAILED: {fails}")
sys.exit(1 if fails else 0)

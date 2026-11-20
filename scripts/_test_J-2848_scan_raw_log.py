"""J-2848: the scan raw log gets one row per scan (null, no_reply, formed, observed, error), the judge class/why rows
exist in the attempts shadow, nothing live is touched, and the reader runs. Run from the worktree."""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env)
from core import commitment_ledger as cl  # noqa: E402

assert Path(cl.__file__).resolve().parent.parent == ROOT, "tests the wrong tree"
tmp = Path(tempfile.mkdtemp(prefix="j2848_"))
for name in ("_DIR", "_LEDGER", "_ACTIVE", "_OBSERVED", "_HOLDRATE_LOG", "_SCAN_RAW_LOG", "_SECOND_LOOK_LOG", "_ATTEMPTS_LOG"):
    old = getattr(cl, name)
    setattr(cl, name, tmp if name == "_DIR" else tmp / Path(old).name)
cl.COMMIT_SECOND_LOOK_SHADOW = False
cl._scan_lock = None
import core.memory.store as _st  # noqa: E402
_st._embed = lambda *_a, **_k: None


def run(reply, thought="I will keep the garden journal every single morning from now on."):
    async def cj(*a, **k):
        if isinstance(reply, Exception):
            raise reply
        return reply
    return asyncio.run(cl.scan_shadow(cj, ["x"], thought, "cyc-T"))


def rows():
    p = tmp / "commitment_scan_raw.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


run({"new_commitment": None, "dissolutions": []})
run(None)
run({"new_commitment": {"statement": "I will keep the garden journal every morning", "scope": "garden journal",
                        "load_bearing": True}, "dissolutions": []})
run({"new_commitment": {"statement": "maybe I want tea", "scope": "", "load_bearing": False}, "dissolutions": []})
run(RuntimeError("boom"))
run({"new_commitment": None}, thought="short")   # under 25 chars: no scan, no row
r = rows()
assert len(r) == 5, [x["outcome"] for x in r]
assert [x["outcome"] for x in r] == ["null", "no_reply", "formed", "observed", "error"], [x["outcome"] for x in r]
assert r[0]["raw"] == {"new_commitment": None, "dissolutions": []} and r[1]["raw"] is None
assert len(r[0]["thought_sha1"]) == 40 and r[0]["thought_head"].startswith("I will keep")
assert r[2]["new_commitment_present"] and r[0]["n_active"] == 0 and r[3]["n_active"] == 1
# judge class + why reach the attempts shadow (J-3158 writer), without a model call
cl._log_judge_attempt({"id": "abc", "held_since": 1.0}, "done it", "defeater", True, "achieved", "deed on record", "", 0.5)
j = [json.loads(l) for l in (tmp / "commitment_attempts_shadow.jsonl").read_text(encoding="utf-8").splitlines()]
assert j[0]["judge_class"] == "achieved" and j[0]["judge_why"] == "deed on record" and j[0]["verdict"] == "allow"
# the reader runs over the temp root
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("rd", ROOT / "scripts" / "commitment_scan_raw_read.py")
rd = importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
import time as _t  # noqa: E402
# tmp has the files directly; reader wants root/data
(tmp / "data").mkdir(); 
for f in ("commitment_scan_raw.jsonl", "commitment_attempts_shadow.jsonl"):
    (tmp / "data" / f).write_text((tmp / f).read_text(encoding="utf-8"), encoding="utf-8")
assert rd.main(["--root", str(tmp), "--since-days", "1"]) == 0
live = ROOT / "data" / "commitment_scan_raw.jsonl"
assert not live.exists() or live.stat().st_mtime < _t.time() - 5, "live scan log touched"
print("OK J-2848")

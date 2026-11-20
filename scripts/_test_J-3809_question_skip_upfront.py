"""J-3809 (D-0710): question-holding thoughts skip passes 2/3 up front, 1 in N audited. Stubbed models, temp logs."""
import asyncio, json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import deliberation as D  # noqa: E402
from core import left_lane  # noqa: E402

assert Path(D.__file__).resolve().parent.parent == ROOT
tmp = Path(tempfile.mkdtemp(prefix="j3809_"))
D._DATA_DIR = tmp
for a, n in (("_LOG_FILE", "log"), ("_NULL_LOG_FILE", "null"), ("_CONTROL_LOG_FILE", "control"),
             ("_GUARD_LOG_FILE", "guard"), ("_QSKIP_LOG_FILE", "qskip")):
    setattr(D, a, tmp / f"{n}.jsonl")
assert D.QUESTION_SKIP_UPFRONT is True and D.QUESTION_AUDIT_EVERY_N == 10
calls = {"g": 0, "i": 0}
async def _g(t):
    calls["g"] += 1
    return "Tides come from the moon and sun pulling on the oceans.", False
async def _i(urls, s, u, **kw):
    calls["i"] += 1
    return {"thought": "The moon pulls the tide whether or not I watch, and that steadies me like a breath."}
left_lane.ground_thought_verdict = _g
D.call_node_json = _i
RAW_Q = "I keep wondering why the tide turns when I am not looking, and whether I am the one who notices?"
RAW_S = "I keep thinking about the tide turning when I am not looking, and about who notices it."
run = lambda r: asyncio.run(D.deliberate(r, "idle", hot_urls=["x"]))

# audit draw never fires -> skipped, no model calls, raw returned, one skip row
D._question_audit_draw = lambda: False
out, prov = run(RAW_Q)
assert out == RAW_Q and prov is None and calls == {"g": 0, "i": 0}
assert len((tmp / "qskip.jsonl").read_text(encoding="utf-8").splitlines()) == 1
# non-question thought is untouched by the skip
run(RAW_S)
assert calls["g"] == 1 and calls["i"] == 1
# audit draw fires -> full pulse, guard discards the statement-integration and logs a guard row
D._question_audit_draw = lambda: True
out, prov = run(RAW_Q)
assert out == RAW_Q and prov is None and calls["g"] == 2
assert (tmp / "guard.jsonl").exists()
# flag off -> prior behaviour exactly
D.QUESTION_SKIP_UPFRONT = False
D._question_audit_draw = lambda: False
run(RAW_Q)
assert calls["g"] == 3
# real draw rate ~1 in N
import importlib; importlib.reload(D)
hits = sum(D._question_audit_draw() for _ in range(20000))
assert 1500 < hits < 2500, hits
print("OK J-3809")

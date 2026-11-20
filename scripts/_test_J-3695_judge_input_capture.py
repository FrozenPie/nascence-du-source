"""J-3695: judge input capture is sampled, split-complete, additive, and read by lab_j3410_order_replay.
Hermetic: _DATA/_LOG/_INPUTS_LOG are pointed at a temp dir and both hubs are stubbed; no network.
Run from the worktree: python scripts/_test_J-3695_judge_input_capture.py"""
import asyncio, json, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # before anything path-resolving
assert Path(core.__file__).resolve().parent.parent == HERE
from core import judge_panel as jp
sys.path.insert(0, str(HERE / "scripts"))
import lab_j3410_order_replay as lab

fails = []
def check(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c: fails.append(m)

tmp = Path(tempfile.mkdtemp(prefix="J3695_"))
jp._DATA, jp._LOG, jp._INPUTS_LOG = tmp, tmp / "judge_panel_log.jsonl", tmp / "judge_inputs_log.jsonl"
votes = {"agree": (True, True), "split": (True, False)}
mode = ["agree"]
async def fake_ask(session, url, system, user, key, **kw):
    v = votes[mode[0]][0 if url == jp.JUDGE_1 else 1]
    return v, "w", None, 0.1
async def fake_shadow(*a, **k):
    return None, None
jp._ask, jp._order_shadow_ask = fake_ask, fake_shadow
jp.SKIP_CONSTANT_TIEBREAK = False
SYS = 'Answer {"held": true} or {"held": false}'
def go(user="u" * 3000):
    return asyncio.run(jp._rule_detail_impl(SYS, user, "held", "ctx"))

jp.JUDGE_INPUT_SAMPLE_EVERY = 10
res = [go() for _ in range(25)]
rows = [json.loads(x) for x in jp._INPUTS_LOG.read_text(encoding="utf-8").splitlines()]
check(len(rows) == 2, "25 agreed rulings at 1-in-10 -> 2 captured (got %d)" % len(rows))
check(all(len(r["user"]) == 1200 and r["user_len"] == 3000 for r in rows), "user text capped at 1200, true length kept")
check(rows[0]["sys_sha"] == lab.sys_sha(SYS) and "system" not in rows[0], "system stored as hash only")
mode[0] = "split"
n0 = len(rows); go(); go()
rows = [json.loads(x) for x in jp._INPUTS_LOG.read_text(encoding="utf-8").splitlines()]
check(len(rows) - n0 >= 2 and all(r["split"] for r in rows[n0:n0 + 2]), "every split captured regardless of sampling")
check(len(jp._LOG.read_text(encoding="utf-8").splitlines()) == 27, "existing log still one row per ruling")
check(set(res[0]) >= {"verdict", "how", "v1", "v2"}, "return dict unchanged")
jp.JUDGE_INPUT_CAPTURE_ON = False
n1 = len(jp._INPUTS_LOG.read_text(encoding="utf-8").splitlines()); go()
check(len(jp._INPUTS_LOG.read_text(encoding="utf-8").splitlines()) == n1, "flag off -> nothing written")
jp.JUDGE_INPUT_CAPTURE_ON = True
jp._INPUTS_LOG = tmp / "nodir" / "x" / "f.jsonl"; jp._DATA = tmp / "nodir"
jp._INPUTS_LOG = Path("\0bad")
check(jp._capture_inputs(SYS, "u", "k", "", True, False, None, "x") is False, "write failure swallowed")

# reader
known = [{"station": "S", "case": "1", "key": "held", "system": SYS, "user": "x", "label": True, "label_raw": "H"}]
p = tmp / "cap.jsonl"
good = {"ts": 1.0, "key": "held", "user": "hello", "user_len": 5, "sys_sha": lab.sys_sha(SYS)}
p.write_text("\n".join(json.dumps(x) for x in [good, dict(good, sys_sha="deadbeef"), dict(good, user_len=3000)]) + "\n", encoding="utf-8")
cs, unres, n = lab.load_captured(p, known)
check(n == 3 and len(cs) == 1 and unres == 2, "reader: 1 replayable, unknown hash + truncated user unresolved")
check(cs[0]["system"] == SYS and cs[0]["label"] is None and lab.reverse_order(cs[0]["system"]) != SYS, "reader case replayable with reversed order")
print("FAILED" if fails else "ALL OK"); sys.exit(1 if fails else 0)

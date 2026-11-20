"""J-2867: offline test of librarian memo + parse-fail log. call_node stubbed; log paths temp; no model, no live data.
    python scripts/_test_J-2867_librarian_memo.py"""
import sys, asyncio, json, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import librarian, model_client  # core BEFORE lab_env

tmp = Path(tempfile.mkdtemp(prefix="j2867_"))
librarian._PARSE_FAIL_LOG = tmp / "fail.jsonl"
fails = []


def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c:
        fails.append(n)


replies = []
calls = []


async def fake(hub, *a, **k):
    calls.append(hub)
    return replies.pop(0)


model_client.call_node = fake
run = lambda q: asyncio.run(librarian.subjects_for(q))
ok = json.dumps({"subjects": ["Ethics", "Liberty"]})
replies[:] = [ok]
check("first ask hits model", run("q one") == ["Ethics", "Liberty"] and len(calls) == 1)
check("repeat ask memoised, no call", run("q  one") == ["Ethics", "Liberty"] and len(calls) == 1)
librarian._memo_put("old", ["X"], now=0)
check("expired entry dropped", librarian._memo_get("old", now=librarian._MEMO_TTL_SECS + 1) is None)
calls.clear()
replies[:] = ["not json", '{"subjects": []}']
check("failures -> []", run("q two") == [] and len(calls) == 2)
check("failure not cached", librarian._memo_get("q two") is None)
rows = [json.loads(l) for l in open(librarian._PARSE_FAIL_LOG, encoding="utf-8")]
check("two parse-fail rows", len(rows) == 2 and rows[0]["reason"].startswith("json_decode") and rows[1]["reason"] == "no_subjects")
check("row shape", set(rows[0]) == {"ts", "src", "hub", "raw", "reason"} and rows[0]["raw"] == "not json")
calls.clear()
replies[:] = ["[1]", ok]
check("non-object logged, falls to next hub", run("q three") == ["Ethics", "Liberty"] and len(calls) == 2)
print("FAILS:", fails or "none")
sys.exit(1 if fails else 0)

"""J-3029 / F-3733 (P-0082): the deep-memory instrument and the per-question memo.

PROVES (this tree, temp paths only, urlopen stubbed: no network, no model, no live store touched):
  [1] key        memo_key lowercases, strips punctuation, collapses spaces, cuts at 80 chars
  [2] ask        consult_sync sends the SAME payload as before (system "/no_think\\n"+_LIBRARY_PROMPT, user query, temp 0.3, 220 tokens, timeout 20)
  [3] log        every attempt writes one row: ts, caller, question (full), answer, ms, outcome; ok / short / timeout (read and connect) / error
  [4] memo       an ok answer is stored; memo_lookup returns it with no model call and logs outcome "memo" (no answer text); a different
                 question misses; a short/error answer is not stored; expiry after 6 h; memo_peek logs nothing
  [5] flags      DEEPMEM_MEMO_ON False disables lookup and store; DEEPMEM_LOG_ON False writes nothing
  [6] cap        the memo never holds more than DEEPMEM_MEMO_MAX entries
  [7] failopen   a log path that raises never reaches the caller and the answer is still returned
  [8] fence      a non-live process pointed at the real data/ path is refused before any I/O; the answer is still returned
  [9] wiring     the monologue block asks memo_lookup first, passes the caller, restarts the cooldown only for a real call, and
                 reads the DEEPMEM_MEMO_BYPASS_COOLDOWN flag; the reader script runs on a sample log

  python scripts/_test_j3029_deepmem_log_memo.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE lab_env)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env  # noqa: E402,F401

assert ROOT in Path(core.__file__).resolve().parents, core.__file__

import urllib.request  # noqa: E402
from core import profile, scholar  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


class _Resp:
    def __init__(self, text):
        self._b = json.dumps({"message": {"content": text}}).encode("utf-8")

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


CALLS = []
MODE = {"v": "ok"}
LONG = "Mottainai is a Japanese term for regret over waste; it carries a sense of gratitude for the things used."


def fake_urlopen(req, timeout=None):
    CALLS.append((json.loads(req.data.decode("utf-8")), timeout))
    m = MODE["v"]
    if m == "ok":
        return _Resp(LONG)
    if m == "short":
        return _Resp("Too short.")
    if m == "timeout_read":
        raise socket.timeout("timed out")
    if m == "timeout_connect":
        raise urllib.error.URLError(socket.timeout("timed out"))
    raise ConnectionRefusedError("refused")


urllib.request.urlopen = fake_urlopen

tmp = Path(tempfile.mkdtemp(prefix="j3029_"))
LOG = tmp / "deep_memory_log.jsonl"
scholar._DEEPMEM_LOG = LOG


def rows():
    if not LOG.exists():
        return []
    return [json.loads(ln) for ln in LOG.read_text(encoding="utf-8").splitlines()]


def reset():
    scholar._memo.clear()
    CALLS.clear()
    if LOG.exists():
        LOG.unlink()


# [1]
check("key normalises", scholar.memo_key("  What IS 'Mottainai'?!  ") == "what is mottainai")
check("key cuts at 80", len(scholar.memo_key("word " * 40)) <= 80)
check("key same for punctuation variants", scholar.memo_key("Why does mottainai matter?") == scholar.memo_key("why does mottainai matter"))

# [2][3]
reset()
Q = "What does the Japanese idea of mottainai mean about waste?"
res = scholar.consult_sync(Q)
check("ok returns (title, text)", bool(res) and res[1] == LONG and res[0].startswith("On "), str(res))
body, tmo = CALLS[0]
check("payload unchanged", body["messages"][0]["content"] == "/no_think\n" + scholar._LIBRARY_PROMPT
      and body["messages"][1]["content"] == Q and body["options"] == {"temperature": 0.3, "num_predict": 220}
      and body["think"] is False and body["stream"] is False and tmo == 20, str(body)[:200])
r = rows()
check("one ok row with all fields", len(r) == 1 and set(r[0]) == {"ts", "caller", "question", "answer", "ms", "outcome"}
      and r[0]["outcome"] == "ok" and r[0]["caller"] == "monologue" and r[0]["question"] == Q and r[0]["answer"] == LONG
      and isinstance(r[0]["ms"], float), str(r))
scholar.consult_sync("another question about something else entirely", caller="curiosity")
check("caller recorded", rows()[-1]["caller"] == "curiosity")

for mode, want in (("short", "short"), ("timeout_read", "timeout"), ("timeout_connect", "timeout"), ("error", "error")):
    reset()
    MODE["v"] = mode
    out = scholar.consult_sync("question number " + mode)
    rr = rows()
    check(f"{mode}: outcome {want}, returns None, row logged", out is None and len(rr) == 1 and rr[0]["outcome"] == want, str(rr))
    check(f"{mode}: not memoised", not scholar.memo_peek("question number " + mode))
reset()
MODE["v"] = "timeout_read"
scholar.consult_sync("whatever happened to the question")
check("error rows carry the exception text", "timed out" in (rows()[0]["answer"] or ""))
MODE["v"] = "ok"
reset()
scholar.consult_sync("   ")
check("empty query logs nothing", rows() == [])

# [4]
reset()
scholar.consult_sync(Q)
n = len(CALLS)
check("peek true after ok", scholar.memo_peek(Q.upper() + "??"))
check("peek logged nothing extra", len(rows()) == 1)
hit = scholar.memo_lookup(Q.lower(), "monologue")
check("memo hit returns stored tuple, no model call", bool(hit) and hit[1] == LONG and len(CALLS) == n)
check("memo row logged without text", rows()[-1]["outcome"] == "memo" and rows()[-1]["answer"] is None and rows()[-1]["ms"] == 0.0, str(rows()[-1]))
check("different question misses", scholar.memo_lookup("a wholly different matter of fact") is None)
key = scholar.memo_key(Q)
scholar._memo[key] = (time.time() - scholar.DEEPMEM_MEMO_TTL_S - 5, scholar._memo[key][1])
check("expired after 6 h", scholar.memo_lookup(Q) is None and not scholar.memo_peek(Q) and key not in scholar._memo)

# [5]
reset()
scholar.DEEPMEM_MEMO_ON = False
scholar.consult_sync(Q)
check("memo off: nothing stored, lookup None, peek False", not scholar._memo and scholar.memo_lookup(Q) is None and not scholar.memo_peek(Q))
scholar.DEEPMEM_MEMO_ON = True
reset()
scholar.DEEPMEM_LOG_ON = False
out = scholar.consult_sync(Q)
check("log off: nothing written, answer returned", rows() == [] and bool(out))
scholar.DEEPMEM_LOG_ON = True

# [6]
reset()
for i in range(scholar.DEEPMEM_MEMO_MAX + 20):
    scholar._memo_store(f"distinct question number {i} about lighthouses", ("t", "x" * 50))
check("memo capped", len(scholar._memo) == scholar.DEEPMEM_MEMO_MAX, str(len(scholar._memo)))
check("oldest dropped, newest kept", scholar.memo_peek(f"distinct question number {scholar.DEEPMEM_MEMO_MAX + 19} about lighthouses")
      and not scholar.memo_peek("distinct question number 0 about lighthouses"))

# [7]
reset()
(tmp / "a_file").write_text("not a directory", encoding="utf-8")
scholar._DEEPMEM_LOG = tmp / "a_file" / "x.jsonl"
out = scholar.consult_sync(Q)
check("log failure fail-open, answer returned and memoised", bool(out) and scholar.memo_peek(Q))
scholar._DEEPMEM_LOG = LOG

# [8]
reset()
real = ROOT / "data" / "deep_memory_log.jsonl"
existed = real.exists()
check("this process is not live", profile.LIVE is False)
scholar._DEEPMEM_LOG = real
out = scholar.consult_sync(Q)
check("non-live write refused before I/O, answer still returned", bool(out) and real.exists() == existed)
scholar._DEEPMEM_LOG = LOG

# [9]
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
i = src.index("J-3029 / F-3733: a question answered in the last 6 h")
blk = src[i:i + 3600]
check("flag defined", "DEEPMEM_MEMO_BYPASS_COOLDOWN = False" in src)
check("peek feeds the cooldown gate", "or _dmemo_free) and len(_bq) > 12" in blk)
check("lookup before the call, caller passed", blk.index('_dmemo(_bq, "monologue")') < blk.index('_idle_off(_dsch, _bq, "monologue")'))
check("cooldown restarted only for a real call", "if not _dm_reused:" in blk
      and blk.index("if not _dm_reused:") < blk.index("self._last_deepmem_ts = time.time()   # a reused"))
check("seed text and feed log untouched", "WHAT YOU ALREADY KNOW ABOUT THIS (rising from your own deep memory" in blk
      and "[deep-memory] fed his thinking on" in blk)
reset()
scholar.consult_sync(Q)
scholar.memo_lookup(Q)
rd = subprocess.run([sys.executable, str(ROOT / "scripts" / "deepmem_log_read.py"), "--log", str(LOG)],
                    capture_output=True, text=True, encoding="utf-8")
check("reader runs and counts the memo save", rd.returncode == 0 and '"calls_saved_by_memo": 1' in rd.stdout
      and '"timeout_rate_pct": 0.0' in rd.stdout, rd.stdout[:300] + rd.stderr[:300])

print("\nALL OK" if not FAILS else f"\nFAILED: {FAILS}")
sys.exit(0 if not FAILS else 1)

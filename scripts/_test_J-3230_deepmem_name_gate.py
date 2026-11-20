"""J-3230 / D-0619: deep-memory questions that name him or his name are excluded at the monologue's consult_sync gate
(counted, never sent to the model); every other question still goes through. Isolated: the exclusion log points into a
temp dir; consult_sync is stubbed so no model is called; no live data is read or written."""
import asyncio
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import core  # noqa: E402,F401
from core import scholar  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j3230_"))
scholar._EXCLUDED_LOG = tmp / "excluded.jsonl"
fails = []


def chk(cond, msg):
    if not cond:
        fails.append(msg)


# 1. the real question shapes from nascence.log (F-3733/F-3734) and the self-reference forms
for q in ("What is the origin of the name '渡' in Japanese culture?",
          "How does the concept of '渡' relate to the transformation of",
          "What does wataru mean as a given name?", "What is the kanji Watari etymology?",
          "What is the meaning of my name?", "Why did you choose your own name?",
          "What is the name I chose and what does it say about me?", "Who is Du, really?",
          "How does Nascence relate to memory?"):
    chk(scholar.name_question_marker(q) is not None, f"should exclude: {q}")
# 2. world questions are untouched (including the two other October monocultures and look-alikes)
for q in ("What is the Continental System of Napoleon?", "What does mottainai mean in Japanese culture?",
          "Who was Gabriel-Julien Ouvrard?", "Who was Du Fu?", "What did Du Bois argue about double consciousness?",
          "Quel est le role du sel dans la cuisine?", "What was his name, the explorer who crossed the strait?",
          "How do rivers cross a watershed?", "", None):
    chk(scholar.name_question_marker(q) is None, f"should NOT exclude: {q!r}")
# 3. the flag turns it off
scholar.DEEPMEM_EXCLUDE_NAME = False
chk(scholar.name_question_marker("What is the origin of the name '渡'?") is None, "flag off should pass through")
scholar.DEEPMEM_EXCLUDE_NAME = True
# 4. counter rows
scholar.log_name_exclusion("What is '渡'?", "渡")
scholar.log_name_exclusion("What is my name?", "my name")
rows = [json.loads(x) for x in scholar._EXCLUDED_LOG.read_text(encoding="utf-8").splitlines()]
chk(len(rows) == 2 and rows[0]["marker"] == "渡" and rows[1]["q"] == "What is my name?", f"log rows wrong: {rows}")
good = scholar._EXCLUDED_LOG
scholar._EXCLUDED_LOG = tmp / "excluded.jsonl" / "nope" / "x.jsonl"   # unwritable: must not raise
scholar.log_name_exclusion("q", "m")
scholar._EXCLUDED_LOG = good

# 5. the call-site wiring as inner_monologue_node.py does it, consult_sync stubbed
calls = []


def stub_consult(q):
    calls.append(q)
    return ("On x", "y" * 60)


async def gate(self_, q):
    _dmark = scholar.name_question_marker(q)
    if _dmark:
        scholar.log_name_exclusion(q, _dmark)
        self_.ts = time.time()
    _dm = None if _dmark else stub_consult(q)
    if _dm:
        self_.ts = time.time()
    return _dm


class S:
    ts = 0.0


s = S()
chk(asyncio.run(gate(s, "What is the cultural significance of the name '渡'?")) is None and not calls,
    "name question reached the model")
chk(s.ts > 0, "cooldown not advanced on an exclusion (would count every tick)")
chk(asyncio.run(gate(s, "What is the Continental System?")) is not None and calls == ["What is the Continental System?"],
    "world question did not reach the model")
# guard: the wiring text is really in the node, so the mirror above cannot drift from the real code
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
chk("_dnm(_bq)" in src and "if not _dmark:" in src and '_dm = await _idle_off(_dsch, _bq, "monologue")' in src, "call-site wiring missing in node")   # J-3029 reshaped the call line (memo lookup first)

# 6. the reader runs over a temp log + exclusion file
spec = importlib.util.spec_from_file_location("rd", ROOT / "scripts" / "deepmem_name_exclusion_read.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)
log = tmp / "n.log"
log.write_text("2999-01-01 00:00:00,1 [nascence.monologue] [deep-memory] fed his thinking on: What is the Continental System?\n"
               "2999-01-01 00:00:01,1 [nascence.monologue] [deep-memory] fed his thinking on: What is '渡'?\n", encoding="utf-8")
out = rd.read(log, scholar._EXCLUDED_LOG, 20)
chk(out["excluded"] == 3 and out["fed_since_first_exclusion"] == 2 and out["fed_after_but_names_him (defeater if >0)"] == 1,
    f"reader wrong: {out}")

print("FAILS:", fails if fails else "none")
sys.exit(1 if fails else 0)

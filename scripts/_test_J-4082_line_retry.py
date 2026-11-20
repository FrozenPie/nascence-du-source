"""J-4082 (J-3897 ruled c, F-4506): line composer prompt fix + one retry + us/our/we as first person. Hermetic: temp SHADOW_LOG,
stubbed store/edges, stub composer. Run: python scripts/_test_J-4082_line_retry.py (from the tree under test)."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.closure as cl
import core.memory.store as _st
import core.memory_edges as _me
ok_all = True
def check(n, c):
    global ok_all
    ok_all = ok_all and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")
tmp = Path(tempfile.mkdtemp(prefix="J-4082_"))
cl.SHADOW_LOG = tmp / "closure_shadow.jsonl"
_st.store_fragment = lambda **kw: "fid-1"
_me.add_edge = lambda *a, **kw: True
cl.CLOSURE_WRITE_LIVE = False
words = lambda n, s="I": " ".join([s] + ["word"] * (n - 1))
ent = {"id": "F-x", "q": "Is it so?"}; cargo = {"grounds": [{"origin": "m", "text": "t"}]}
sy, us = cl._line_prompts(ent, cargo, "settled")
check("prompt says first person, 40 to 90, has an example", "begin with" in sy and "40 to 90" in sy and "Example" in sy)
check("us/our/we count for line only", cl.validate_composed("line", words(50, "We")) is None and cl.validate_composed("dream", words(50, "We")) == "no-first-person")
check("plural flag off restores reject", (setattr(cl, "LINE_PLURAL_FIRST_PERSON", False), cl.validate_composed("line", words(50, "We")))[1] == "no-first-person")
cl.LINE_PLURAL_FIRST_PERSON = True
def run(seq, sid, retry=True):
    cl.LINE_RETRY_ON_INVALID = retry; calls = []
    def fn(s, u):
        calls.append(u); return {"resolution": seq[min(len(calls) - 1, len(seq) - 1)]}
    cl._compose_fn = fn
    return cl.record_line_settled({"id": sid, "q": "q"}, cargo, "t"), calls
r, c = run([words(50)], "a")
check("valid first -> one call, no retry", len(c) == 1 and r["would_be"] and "compose_retry" not in r)
r, c = run([words(20, "The"), words(50)], "b")
check("invalid then valid -> two calls, composed, ok", len(c) == 2 and r["would_be"] and r["compose_how"] == "ok" and r["compose_retry"] and r["first_compose_how"] == "invalid:words-under-40")
check("retry message names the reason", "refused because" in c[1] and "too short" in c[1])
r, c = run([words(20, "The")], "c")
check("invalid twice -> exactly two calls, still invalid, nothing live", len(c) == 2 and r["would_be"] is None and r["compose_how"].startswith("invalid:") and r.get("rejected_text_retry"))
r, c = run([words(20, "The"), words(50)], "d", retry=False)
check("flag off -> one call, invalid", len(c) == 1 and r["would_be"] is None)
r, c = run(["  "], "e")
check("empty compose does not retry", len(c) == 1)
print("ALL PASS" if ok_all else "FAILURES"); sys.exit(0 if ok_all else 1)

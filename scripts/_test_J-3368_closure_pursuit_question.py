"""
J-3368 (D-0554 follow-up to J-3165): the closure PURSUIT arm quotes pursuits.driving_question(p) -- the extracted
question_text for pursuits born under D-0554 (question_kind in question/done_when), the birth thought for old ones.

Hermetic: SHADOW_LOG in a temp dir, store/edge writers stubbed, composer stubbed. Input-only change: no prompt wording.
Run:  python scripts/_test_J-3368_closure_pursuit_question.py   (from the tree under test)
"""
from __future__ import annotations
import sys, tempfile, json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE anything lab-ish
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.closure as cl
import core.done_when as dw
import core.memory.store as _st
import core.memory_edges as _me

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="J-3368_"))
cl.SHADOW_LOG = tmp / "closure_shadow.jsonl"
assert Path(cl.SHADOW_LOG).resolve().is_relative_to(tmp.resolve())
_st.store_fragment = lambda **kw: "fid-1"
_me.add_edge = lambda *a, **kw: True
cl.CLOSURE_WRITE_LIVE = False
cl.CLOSURE_ARMS.discard("pursuit")

BIRTH = "the lamp hummed and I thought about the sea"
REAL_Q = "Why does the lamp hum only at dusk?"
new_p = {"id": "P-T1", "question": BIRTH, "question_kind": "question", "question_text": REAL_Q,
         "standing": "it is the cooling glass", "open": "", "advances": 3, "status": "active"}
dw_p = dict(new_p, id="P-T2", question_kind="done_when")
obs_p = dict(new_p, id="P-T3", question_kind="observation")
old_p = {"id": "P-T4", "question": BIRTH, "standing": "x", "advances": 2, "status": "active"}
empty_q = dict(new_p, id="P-T5", question_text="  ")

print("_pursuit_question")
check("new pursuit -> extracted question", cl._pursuit_question(new_p) == REAL_Q)
check("done_when kind -> extracted question", cl._pursuit_question(dw_p) == REAL_Q)
check("observation kind -> birth thought", cl._pursuit_question(obs_p) == BIRTH)
check("old pursuit (no key) -> birth thought", cl._pursuit_question(old_p) == BIRTH)
check("blank question_text -> birth thought", cl._pursuit_question(empty_q) == BIRTH)
check("non-dict never raises", cl._pursuit_question({}) == "")

print("_pursuit_prompts (user line only; wording of system unchanged)")
for faded in (False, True):
    _, u = cl._pursuit_prompts(new_p, faded)
    check(f"faded={faded}: new pursuit quotes extracted question", u.startswith(f"The question: {REAL_Q}\n") and BIRTH not in u)
    _, u2 = cl._pursuit_prompts(old_p, faded)
    check(f"faded={faded}: old pursuit quotes birth thought", u2.startswith(f"The question: {BIRTH}\n"))
s_met, _ = cl._pursuit_prompts(new_p, False)
check("system prompt has no new wording", "extracted" not in s_met and "A question you kept returning to is" in s_met)

print("shadow row 'q' extra")
dw.get = lambda kind, sid: {"text": "done"}       # a done_when exists
cl._compose_fn = lambda s, u: {"resolution": "I now hold that it is the cooling glass, because the hum only comes when the air cools at dusk and the pane contracts."}
r = cl.record_pursuit_met(new_p, {"why": "w"}, now=1.0)
rows = [json.loads(l) for l in cl.SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()] if cl.SHADOW_LOG.exists() else []
check("met row recorded", len(rows) >= 1)
check("met row q = extracted question", rows and rows[-1].get("q") == REAL_Q)
r2 = cl.record_pursuit_met(old_p, {"why": "w"}, now=2.0)
rows = [json.loads(l) for l in cl.SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
check("old pursuit row q = birth thought", rows[-1].get("q") == BIRTH)
fp = dict(new_p, id="P-T6", status="saturated")
cl.record_pursuit_faded(fp, {"why": "w"}, now=3.0)
rows = [json.loads(l) for l in cl.SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
check("faded row q = extracted question", rows[-1].get("q") == REAL_Q)

print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

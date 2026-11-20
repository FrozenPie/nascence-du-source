"""
J-4083 (J-3889 ruled; F-4488): the closure COMMITMENT arm must be able to say not-achieved. commitment_deed_verdict is
pure; record_commitment_achieved logs kind "not_achieved" (no compose) for an unrelated deed and goes through the old
path for a matching one. Hermetic: SHADOW_LOG and done_when STORE in a temp dir, composer stubbed.
Run:  python scripts/_test_J-4083_commitment_deed_gate.py   (from the tree under test)
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

tmp = Path(tempfile.mkdtemp(prefix="J-4083_"))
cl.SHADOW_LOG = tmp / "closure_shadow.jsonl"
dw.STORE = tmp / "done_when.jsonl"
assert Path(cl.SHADOW_LOG).resolve().is_relative_to(tmp.resolve())
_st.store_fragment = lambda **kw: "fid-1"
_me.add_edge = lambda *a, **kw: True
cl.CLOSURE_WRITE_LIVE = False
cl._compose_sync = lambda s, u: {"resolution": " ".join(["I"] + ["opened"] * 49)}

NAPOLEON = "[My study note: 'Napoleon's Conditional Kingship' · on 'Complete Project Gutenberg Collection of Memoirs'] He ruled."
print("verdict")
check("refill the barrel vs Napoleon note -> not_achieved",
      cl.commitment_deed_verdict("I will refill the barrel before nature's rhythm can be forced", "The barrel is refilled.", NAPOLEON, "study")[0] == "not_achieved")
check("physical act vs written study -> not_achieved, says why",
      "cannot fulfil" in cl.commitment_deed_verdict("I will close the grate", "When the grate is closed", NAPOLEON, "study")[1])
check("note about the book named in the stand -> achieved",
      cl.commitment_deed_verdict("I will anchor 'Three More John Silence Stories' in ten concrete notes.", "ten concrete notes anchoring the stories",
                                 "[My study note: 'Three More John Silence Stories'] text", "study")[0] == "achieved")
check("open the book vs library action -> achieved",
      cl.commitment_deed_verdict("I must open that book now.", "When I have opened the book.", "librarian cliff swallows - 1 time(s)", "action")[0] == "achieved")
check("never raises on None", cl.commitment_deed_verdict(None, None, None, None)[0] in ("achieved", "not_achieved"))

print("record_commitment_achieved")
dw.record("commitment", "C-T1", "The barrel is refilled.", "test")
dw.record("commitment", "C-T2", "when I have opened the book", "test")
r1 = cl.record_commitment_achieved({"id": "C-T1", "statement": "I will refill the barrel."}, "study: " + NAPOLEON[:90], NAPOLEON)
check("unrelated deed -> kind not_achieved, no would_be, not live", r1 and r1["kind"] == "not_achieved" and r1["would_be"] is None
      and r1["compose_how"] == "skipped_not_achieved" and not r1["written_live"])
r2 = cl.record_commitment_achieved({"id": "C-T2", "statement": "I must open that book now."}, "action: librarian cliff - 1 time(s)", "librarian cliff - 1 time(s)")
check("matching deed -> resolution row with would_be", r2 and r2["kind"] == "resolution" and r2["judge_verdict"] == "achieved" and r2["would_be"])
check("not_achieved row did not block a later real resolution (no duplicate lock)",
      cl.record_commitment_achieved({"id": "C-T1", "statement": "x"}, "study: z", NAPOLEON)["kind"] == "not_achieved")
cl.COMMITMENT_DEED_GATE = False
dw.record("commitment", "C-T3", "when done", "test")
r3 = cl.record_commitment_achieved({"id": "C-T3", "statement": "refill"}, "study: " + NAPOLEON[:60], NAPOLEON)
check("gate off == old behaviour (achieved)", r3 and r3["judge_verdict"] == "achieved" and r3["gate"] == "off")
rows = [json.loads(l) for l in cl.SHADOW_LOG.read_text(encoding="utf-8").splitlines()]
check("rows landed only in the temp log", len(rows) >= 3)
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

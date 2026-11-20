"""J-3137 / D-0531: the human-turn self-claim scan no longer arms the next-cycle think license.

Offline, no model calls, no live data (sitting is stubbed). Covers:
  1. flag default is False; a contradicting scan result does NOT set _s2_license_next, logs the 'self-claim
     contradicted' line (closure_index.py's read path) with no 'licensing deliberate thought' text, and still
     calls sitting.note_difficulty (kind self-claim).
  2. non-contradicting / None results do nothing.
  3. with the flag flipped True the old grant is restored (revertible per the defeater).
  4. source: the only assignment of `_s2_license_next = True` sits behind the flag; the callback still creates
     the scan task and calls scan_conversation_shadow.
"""
import logging
import os
import re
import sys
import types
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["NASCENCE_TRAINING_LOG"] = "0"
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                             # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import core.orchestrator as orch                        # noqa: E402
from core import sitting                                # noqa: E402

calls = []
sitting.note_difficulty = lambda text, kind="": calls.append((text, kind))   # stub: never touch the live store


class _H(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, rec):
        self.lines.append(rec.getMessage())


h = _H()
lg = logging.getLogger("nascence.orchestrator")
lg.addHandler(h)
lg.setLevel(logging.INFO)

R = {"contradicts": True, "contradicted_claim": "I hold that the lamp is mine"}

assert orch.CONV_SCAN_ARMS_THINK_LICENSE is False
o = types.SimpleNamespace(_s2_license_next=False)
orch._conv_scan_apply(o, R)
assert o._s2_license_next is False, "license was armed"
assert any("self-claim contradicted" in l for l in h.lines), h.lines
assert not any("licensing deliberate" in l or "think-license" in l.lower() for l in h.lines), h.lines
assert len(calls) == 1 and calls[0][1] == "self-claim" and "Travis contradicted a stand you hold" in calls[0][0], calls

for r in (None, {}, {"contradicts": False, "contradicted_claim": "x"}):
    o2 = types.SimpleNamespace(_s2_license_next=False)
    n = len(calls)
    orch._conv_scan_apply(o2, r)
    assert o2._s2_license_next is False and len(calls) == n

orch.CONV_SCAN_ARMS_THINK_LICENSE = True
o3 = types.SimpleNamespace(_s2_license_next=False)
orch._conv_scan_apply(o3, R)
assert o3._s2_license_next is True
orch.CONV_SCAN_ARMS_THINK_LICENSE = False

src = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
sites = [m.start() for m in re.finditer(r"_s2_license_next\s*=\s*True", src)]
assert len(sites) == 1, sites
assert "if CONV_SCAN_ARMS_THINK_LICENSE:" in src[sites[0] - 120:sites[0]]
assert "scan_conversation_shadow(" in src and "_conv_scan_apply(self, t.result())" in src
print("J-3137 OK")

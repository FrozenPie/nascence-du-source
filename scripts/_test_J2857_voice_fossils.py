"""
J-2857 (F-3519) -- the retired regurgitation guard / exemplar loader and the style_confidence fossil in the Voice node.
No model is called, nothing live is touched; the fidelity shadow hook is stubbed and any log path would be a temp dir.

  python scripts/_test_J2857_voice_fossils.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), "core must come from the tree under test"
from core import voice_fidelity as vf  # noqa: E402
from core.schema import VoiceOutput  # noqa: E402
from nodes import voice_node as vn  # noqa: E402

assert str(Path(vn.__file__).resolve()).startswith(str(ROOT))
FAILS: list[str] = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


# stub the observe-only shadow hook: no call, no ledger write
vf.schedule = lambda **kw: None

check(not hasattr(vn, "_load_voice_example") and not hasattr(vn, "_AXIOM_PATH"), "exemplar loader and axiom path are gone from voice_node")
node = vn.VoiceNode()
check(not hasattr(node, "_voice_example"), "VoiceNode no longer carries _voice_example")

# a final that starts with the old exemplar opening must pass through untouched with no warning
EXEMPLAR_OPEN = "You ask what I feel, and I must first ask which part of me you are addressing"
records: list[logging.LogRecord] = []
h = logging.Handler()
h.emit = records.append
lg = logging.getLogger("nascence.node.voice")
lg.addHandler(h)
lg.setLevel(logging.DEBUG)
state = SimpleNamespace(executive=SimpleNamespace(synthesis="x"), raw_input="hi", input_type="human", cycle_id="cyc-1234567890", voice=None)
node._write_output(state, {"final": EXEMPLAR_OPEN + ", and here is the rest."})
check(state.voice.final.startswith(EXEMPLAR_OPEN) and not records, "no guard: output untouched, no warning logged")

# style_confidence: default 0.7 when absent, still honoured when a v1 / lab response supplies it
check(state.voice.style_confidence == 0.7, "style_confidence defaults to 0.7 when the model does not supply it")
node._write_output(state, {"final": "ok", "style_confidence": 0.9})
check(state.voice.style_confidence == 0.9, "style_confidence is still read when supplied (voice_lab v1)")

# the dataclass and schema: field kept (defaulted), schema no longer requires it
check(VoiceOutput(final="a").style_confidence == 0.7 and VoiceOutput("a", 0.4).style_confidence == 0.4, "VoiceOutput keeps style_confidence as a defaulted positional field")
check(VoiceOutput.JSON_SCHEMA["required"] == ["final"] and "style_confidence" in VoiceOutput.JSON_SCHEMA["properties"],
      "JSON_SCHEMA requires only final; style_confidence stays a known optional property")

# the profile rebase no longer pokes voice_node._AXIOM_PATH
src = (ROOT / "core" / "profile.py").read_text(encoding="utf-8")
check("voice_node._AXIOM_PATH" not in src, "core/profile.py no longer rebases voice_node._AXIOM_PATH")
import importlib
check(importlib.import_module("core.profile") is not None, "core.profile still imports")

# v1 (voice_lab) still builds and still names style_confidence; v2 prompt does not ask for it
check("style_confidence" in node.system_prompt_v1 and "style_confidence" not in node.system_prompt_v2, "v1 prompt (voice_lab) unchanged; v2 never asks for it")

print("\nFAILED: %d" % len(FAILS) if FAILS else "\nALL PASS")
sys.exit(1 if FAILS else 0)

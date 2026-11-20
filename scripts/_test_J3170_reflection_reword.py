"""J-3170 (D-0559): Reflection STRICT RULE 3 reworded and content_mode NOTE reconciled with the axiom.

  [1] rule 3 no longer depends on earlier drafts and the old wording is gone.
  [2] the NOTE no longer says 'resist lifting it into a metaphor' / 'LITERAL and the sensory' and lets symbol arise from the subject.
  [3] no banned-word list was planted (neither text names the collapsed vocabulary).
  [4] the other STRICT RULES (1, 2, 4) and the NOTE's opening/closing are untouched.
Pure source + prompt read; builds the system prompt only; touches no live data.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

from nodes.reflection_node import ReflectionNode  # noqa: E402

src = (ROOT / "nodes" / "reflection_node.py").read_text(encoding="utf-8")
sp = ReflectionNode().system_prompt

assert "3. Let this reflection take a different angle from the one you would reach for first." in sp
for old in ("reflected on something similar before", "go deeper or sideways"):
    assert old not in sp and old not in src, old
print("[1] ok: rule 3 reworded")

assert "resist lifting it into a metaphor" not in src
assert "LITERAL and the sensory" not in src
assert "let it arise from the subject, not be laid over it" in src.replace('"\n                "', "").replace('"\r\n                "', "")
print("[2] ok: NOTE reconciled")

i = src.index("NOTE: this is a concrete question")
j = src.index("just be with it.", i)
note = src[i:j].lower()
for bad in ("strangl", "suffoc", "vein", "starv", "metabol", "not just", "did not just", "artery", "paradox"):
    assert bad not in note and bad not in sp.lower(), bad
print("[3] ok: no banned list planted")

for keep in ("1. Never begin the draft by repeating or rephrasing the input",
             "2. Explore the genuine internal reaction. Surprise yourself.",
             "4. Keep the draft TIGHT",
             "Think INTO the ",
             "insight comes AFTER the immersion, not during it. For now, just be with it."):
    assert keep in src or keep in sp, keep
print("[4] ok: neighbours untouched")
print("ALL OK")

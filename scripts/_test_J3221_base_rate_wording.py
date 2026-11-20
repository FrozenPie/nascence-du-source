"""J-3221 (D-0610): the idle system prompt stops claiming a base rate the model does not honour.

  [1] the removed claims are gone from nodes/inner_monologue_node.py and core/follow_line.py
      ("Most quiet thoughts are NOT unresolved", "Reserve true for genuine inner conflict only",
       act "almost all thoughts", ask "for almost all thoughts") and no digit-percentage was added.
  [2] the schema-field meanings survive: the unresolved definition, the act kinds list, the object rule,
      the intention rule (behaves as written, 5.6%, untouched byte-for-byte), the schema fragments.
  [3] follow_line.rule_fragment() (FOLLOW_LINE forced on) states the meaning of ask without a base rate, keeps
      the slot kinds, the settled rule; with FOLLOW_LINE off it is still "".
Pure source plus a pure function; touches no live data.   python scripts/_test_J3221_base_rate_wording.py
"""
from __future__ import annotations

import re
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

node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
fl_src = (ROOT / "core" / "follow_line.py").read_text(encoding="utf-8")

# [1]
for gone in ("Most quiet", "NOT unresolved", "Reserve true for genuine inner conflict only",
             "unresolved: true ONLY if", "-- almost all thoughts. Set a real"):
    assert gone not in node, gone
    assert gone not in fl_src, gone
assert "for almost all thoughts. Set it ONLY when this thought" not in fl_src
i0 = node.index('"unresolved: true if this thought')
i1 = node.index("+ _ask_rule")
block = node[i0:i1] + node[node.index("+ _ask_rule"):node.index("+ _ask_rule") + 1500]
assert not re.search(r"\d+\s*%|\bpercent\b", block), "a number crept into the prompt"
print("[1] ok")

# [2]
for kept in ('"unresolved: true if this thought sits on something you are ACTIVELY wrestling "',
             "a real conflict between two things you believe, a fear about",
             "false if it is ", "a calm reflection, an observation, or a peaceful wondering. ",
             'intention: leave as \\"\\" for almost all thoughts. Set it ONLY when this thought "',
             "crystallises into a genuine resolve",
             '\\"observe\\" (turn to look at something in the world',
             '\\"recall\\" (search your own PAST',
             "Set a non-none kind only ",
             "ALWAYS fill object",
             "_state_schema", "+ _dw_rule +", "+ _ask_rule"):
    assert kept in node, kept
assert 'act: {\\"kind\\": \\"none\\", \\"object\\": \\"\\"} when this thought does not mean to do anything ' in node
assert "kind names the deed. kind is " in node
print("[2] ok")

# [3]
from core import follow_line as fl  # noqa: E402
assert Path(fl.__file__).resolve().parent.parent == ROOT, fl.__file__
orig = fl.FOLLOW_LINE
try:
    fl.FOLLOW_LINE = "off"
    assert fl.rule_fragment() == "" and fl.schema_fragment() == ""
    fl.FOLLOW_LINE = "live"
    r = fl.rule_fragment()
    assert "almost all" not in r and "leave as" not in r, r
    assert 'ask: {"q": "", "slot": ""} when this thought asks nothing.' in r, r
    assert "q is the question in your own words." in r, r
    assert fl.ASK_SLOT_KINDS in r or not fl.ASK_SLOT_KINDS
    assert "settled:" not in r
    rd = fl.rule_fragment(True)
    assert "settled:" in rd and '"yes" if what came back' in rd, rd
    assert not re.search(r"\d+\s*%", r + rd)
    print("    rule_fragment:", r)
finally:
    fl.FOLLOW_LINE = orig
print("[3] ok")
print("ALL OK")

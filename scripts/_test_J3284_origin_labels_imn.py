"""J-3284 (D-0631 review J-3243) IMN half: the shock seed names its source and the curiosity memory-ask frame does not
call a looked-up Wikipedia page something he lived or read.

  [1] shock seed line names 'a random Wikipedia page'; the old unlabelled wording is gone; the tail concatenation
      (_shock[0], ' -- ', _shock[1][:260]) is untouched.
  [2] the memory-ask frame: content starting '[Looked up:' gets the PAGE frame; every other content keeps the ORIGINAL
      frame BYTE-IDENTICAL (asserted against the pre-change literal); executed from the real source lines.
  [3] core.schema.MemoryFragment.readable_label (the non-IMN half) on sample fragments: shock / pursuit / asked / peer.
Pure source + temp-free; touches no live data.   python scripts/_test_J3284_origin_labels_imn.py
"""
from __future__ import annotations

import sys
import textwrap
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
from core.schema import MemoryFragment  # noqa: E402

src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

# [1]
assert "Uninvited, from the world outside (a random Wikipedia page; you did not choose this): '" in src
assert "Uninvited, from the world outside (you did not choose this)" not in src
assert "+ _shock[0] + \"' — \" + _seed_cut(_shock[1], 260))" in src   # J-4052: re-pinned, slice became _seed_cut
print("[1] ok")

# [2]
ORIG = ("A MEMORY THIS QUESTION CALLS UP (something you actually lived or read, "
        "found in your own fragment store -- not innate knowledge, an actual "
        "remembered moment; hold it as a real memory, not a fact): ")
a = src.index("_ctop_txt = (_ctop.get('content') or '')")
b = src.index("seed_parts.append(_ctop_frame", a)
snippet = textwrap.dedent(" " * 24 + src[a:b].rstrip()) 
def frame(content):
    ns = {"_ctop": {"content": content}, "_ctop_own": False}   # J-3188 adds _ctop_own (computed before this span)
    exec(snippet, ns)
    return ns["_ctop_frame"]
assert frame("I walked on the shore") == ORIG, "non-research frame changed"
assert frame("") == ORIG
page = frame("[Looked up: 'Tide' (asked by him)] Tides are ...")
assert page.startswith("A PAGE THIS QUESTION CALLS UP") and "lived or read as your own memory" in page
assert "A MEMORY THIS QUESTION" not in page
assert frame("  [Looked up: 'X' (external shock)] x").startswith("A PAGE")
print("[2] ok")

# [3]
def lab(origin, content=""):
    return MemoryFragment("f", content, "episodic", 0.5, time.time(), origin=origin).readable_label()
assert "uninvited" in lab("research", "[Looked up: 'Tide' (external shock)] x")
assert "keyword match" in lab("research", "[Looked up: 'Tide' (pursuit keyword)] x")
assert lab("research", "[Looked up: 'Tide' (asked by him)] x") == "Something I looked up (external fact - Wikipedia)"
assert lab("research", "plain old row") == "Something I looked up (external fact - Wikipedia)"
assert "friend" in lab("peer")
print("[3] ok")
print("ALL OK")

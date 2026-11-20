"""J-3156 (D-0543): the standing open-book offer seed line is removed from the idle prompt.

  [1] none of the four offer phrasings, nor the 'open_book' phrasing key, remain in nodes/inner_monologue_node.py.
  [2] what the ruling says to LEAVE is still there: the reread invitation (_ph.vary("reread")), the reading-train
      seed ("If you would read ON, say: OPEN THE BOOK"), the school directive (core/school.py OPEN THE BOOK) and the
      _wants_read latch.
  [3] seed_parts.append sites in the node: 45 (was 46 at HEAD~ of this job); the census (this tree) agrees.
  [4] the study scene line (core/sensorium.py) still states that the book lies open on the desk, and the study is
      excluded from the spatial whole-line swap (so that line is always the study's base).
Pure source; touches no live data.   python scripts/_test_J3156_open_book_offer_removed.py
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

src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

# [1]
for gone in ("An open book waits for you", "There is a book open and waiting", "A book lies ready for you",
             "sits open, waiting. If you would sooner read", 'vary("open_book"', "_bk = repr(current_book()"):
    assert gone not in src, gone
code_lines = [l for l in src.splitlines() if not l.lstrip().startswith("#")]
assert not any("make your thought exactly: OPEN THE BOOK" in l for l in code_lines)   # only the comment names it
assert any("Make your thought exactly: OPEN THE BOOK." in l for l in code_lines)       # line ~2017, a different seed: untouched
print("[1] ok")

# [2]
assert '_ph.vary("reread"' in src
assert "If you would read ON, say: OPEN THE BOOK." in src
assert "OPEN THE BOOK" in (ROOT / "core" / "school.py").read_text(encoding="utf-8")
assert "_wants_read" in src
print("[2] ok")

# [3]
n = len(re.findall(r"seed_parts\.append", src))
assert n == 45, n
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("_census_j3156", ROOT / "scripts" / "prompt_site_census.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
assert cm.ROOT == ROOT, cm.ROOT
print("[3] ok  seed_parts.append sites =", n)

# [4]
sens = (ROOT / "core" / "sensorium.py").read_text(encoding="utf-8")
assert "'{book}' lies open on the desk; your shelf holds " in sens
assert 'if loc in ("garden", "shore", "wood"):' in sens   # study is not whole-line swapped by the renderer
print("[4] ok  scene line: \"'<book>' lies open on the desk; your shelf holds <n> of your own written works ...\"")
print("ALL OK")

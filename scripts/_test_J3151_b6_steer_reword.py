"""J-3151 (D-0542): the B6 hard-feeling steer no longer supplies a feeling word.

  [1] the steer text is exactly the reworded invitation (no 'frustrat', 'heaviness', 'name the feeling').
  [2] the edge trigger and threshold are untouched: steer_edge.fires("b6_hard", ... <= B6_VALENCE_THRESHOLD, rearm_s=600.0), -0.57.
  [3] the J-1955 replay regex still recognises the new opening.
Pure source read; touches no live data.   python scripts/_test_J3151_b6_steer_reword.py
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
import ast  # noqa: E402

i = src.index('"Something in you is hard right now')
j = src.index("except Exception:", i)
chunk = src[i:j].rstrip()
assert chunk.endswith(")")
steer = ast.literal_eval("(" + chunk)
want = ("Something in you is hard right now. Before you make any meaning of it or turn it toward the good, "
        "say plainly what it is. You are allowed to simply feel it; you do not have to make it into wisdom.")
assert steer == want, steer
low = steer.lower()
for bad in ("frustrat", "heavi", "name the feeling", "a frustration"):
    assert bad not in low, bad
print("[1] ok: reworded, no supplied feeling word")

assert src.count('_se_b.fires("b6_hard", bool(_val is not None and _val <= B6_VALENCE_THRESHOLD), rearm_s=600.0)') == 1
assert re.search(r"^B6_VALENCE_THRESHOLD = -0\.57$", src, re.M)
print("[2] ok: edge trigger + threshold unchanged")

assert re.compile(r"^\s*Something in you is hard right now").match(steer)
assert src.count("Something in you is hard right now") == 1
print("[3] ok")
print("ALL OK")

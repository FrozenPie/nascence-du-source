"""J-2930 (F-3618 part i; P-0032): the curiosity memory.ask() line does not re-offer the same fragment for a question's
whole life.

  [1] helper: first not-yet-offered result is picked in ask() order; all offered -> None; a keyless result is never dropped.
  [2] the REAL source block (executed from nodes/inner_monologue_node.py): 5 results for one question over 7 ticks ->
      5 distinct offers in order, then 2 skipped ticks (no line); a new lingering question starts a fresh ledger;
      returning to the first question after a change is also fresh (reset on change).
  [3] flag off -> always results[0] (pre-J-2930 behaviour), nothing recorded.
  [4] the ask() call, the clock write, the Scholar block and DEEPMEM_COOLDOWN are untouched in the source.
Temp-free; stubs memory_service entirely; touches no live data.   python scripts/_test_J2930_curiosity_no_reoffer.py
"""
from __future__ import annotations

import sys
import textwrap
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

# pull the module-level helpers/consts from the real source
h0 = src.index("CURIOSITY_NO_REOFFER_ON = True")
h1 = src.index("# WHAT TRAVIS HAS TOLD HIM, in IDLE", h0)
helpers = src[h0:h1]
ns: dict = {}
exec(compile(helpers, "helpers", "exec"), ns)

# [1] helper
F = lambda i: {"fragment_id": f"f{i}", "content": f"c{i}"}
frs = [F(i) for i in range(5)]
assert ns["_curiosity_pick_unoffered"](frs, set())["fragment_id"] == "f0"
assert ns["_curiosity_pick_unoffered"](frs, {"f0", "f1"})["fragment_id"] == "f2"
assert ns["_curiosity_pick_unoffered"](frs, {f"f{i}" for i in range(5)}) is None
assert ns["_curiosity_pick_unoffered"]([], set()) is None
nokey = {"content": "no id here"}
k = ns["_curiosity_frag_key"](nokey)
assert k.startswith("c:"), k
assert ns["_curiosity_pick_unoffered"]([nokey], {k}) is None          # same content hash is tracked
assert ns["_curiosity_pick_unoffered"]([{"fragment_id": "", "content": ""}], set()) is not None
print("[1] helper ok")

# [2]/[3] the real in-line block
a = src.index("# J-2930 (F-3618 part i): never re-offer")
b = src.index("if _cfrags and _c_skip:", a)
blk = textwrap.dedent(" " * 24 + src[a:b].rstrip())


class Node:
    pass


def tick(node, bq, cfrags, flag=True):
    g = dict(ns)
    g["CURIOSITY_NO_REOFFER_ON"] = flag
    loc = {"self": node, "_bq": bq, "_cfrags": cfrags, "_ctop": cfrags[0]}   # the real code sets _ctop just before the block
    g.update(loc)
    exec(blk, g)
    return g["_ctop"], g["_c_skip"]


n = Node()
Q1, Q2 = "How does Ouvrard's financial success shape Na's moral choices?", "How did the Continental System end?"
seq = []
for _ in range(7):
    top, skip = tick(n, Q1, frs)
    seq.append(None if skip else top["fragment_id"])
assert seq == ["f0", "f1", "f2", "f3", "f4", None, None], seq
top, skip = tick(n, Q2, frs)                      # new question -> fresh ledger
assert (top["fragment_id"], skip) == ("f0", False)
top, skip = tick(n, Q1, frs)                      # back to Q1 after a change -> reset on change
assert (top["fragment_id"], skip) == ("f0", False)
# a partly different result set: next-best unoffered is taken even if it ranks lower
n2 = Node()
tick(n2, Q1, frs)
top, skip = tick(n2, Q1, [F(0), F(9), F(1)])
assert (top["fragment_id"], skip) == ("f9", False)
print("[2] block sequence ok:", seq)

n3 = Node()
for _ in range(3):
    top, skip = tick(n3, Q1, frs, flag=False)
    assert (top["fragment_id"], skip) == ("f0", False)
assert not hasattr(n3, "_curiosity_offered")
print("[3] flag off = results[0], no ledger")

# [4] untouched pieces
assert '_cmemsvc.ask, "curiosity", _bq, k=5, grounded_only=True, descend=True' in src
assert "self._last_curiosity_ask_ts = time.time()" in src
assert "DEEPMEM_COOLDOWN   = 300.0" in src
assert src.count("_idle_off(_dsch, _bq") == 1   # J-3029 added a third arg, "monologue"
# the clock is written BEFORE the pick, so a skipped tick keeps the 300 s ask cadence
assert src.index("self._last_curiosity_ask_ts = time.time()", src.index("_cfrags = await _idle_off2")) < a + 200
print("[4] ask call, clock, Scholar, cooldown intact")
print("ALL OK")

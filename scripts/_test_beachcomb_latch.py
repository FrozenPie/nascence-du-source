"""Regression for J-0542 / F-0737 (2026-09-04): the beachcomb fallback latch in nodes/inner_monologue_node.py.
(1) hands.wants() must read both word forms ('beachcomb', 'beachcombing') and still refuse a wish/negation;
(2) the latch must be gated on sensorium.where() == 'shore' (in the wood, sensorium.act('beachcomb') gathers
    deadfall while the latch would have logged COMB THE TIDELINE).
Part 1 is pure (hands.wants) with every store hands/literal_will touch redirected into a temp dir; part 2 is a
static read of the latch source — the node is never imported and the live data/ is never written.
    python scripts/_test_beachcomb_latch.py
"""
from __future__ import annotations
import re, sys, tempfile
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

TMP = Path(tempfile.mkdtemp(prefix="beachcomb_latch_"))
_LIVE = [ROOT / "data" / n for n in ("hands_trace.jsonl", "literal_will_shadow.jsonl", "literal_will_state.json")]
_LIVE_BEFORE = [(f.stat().st_mtime_ns, f.stat().st_size) if f.exists() else None for f in _LIVE]
from core import hands as h, literal_will as lw
h._DATA = TMP; h._TRACE = TMP / "hands_trace.jsonl"
lw._DATA = TMP; lw._LOG = TMP / "literal_will_shadow.jsonl"; lw._STATE = TMP / "literal_will_state.json"

SRC = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
# J-0745/F-0958: the 12-site blocker-bleed fix (commit a92320b, J-0657) renamed this call site's
# join variable from the bare `_tl` to the clause-safe `_tl_cs` -- the latch itself is unchanged
# (same phrase tuple, same shore-only gate below), this regex just tracks the real call shape now.
m = re.search(r"_hands\.wants\(_tl_cs, \((?P<tuple>[^)]*\"search the rock-pools\"[^)]*)\)\)", SRC, re.S)
assert m, "beachcomb latch phrase tuple not found"
PHRASES = tuple(re.findall(r'"([^"]+)"', m.group("tuple")))
print(f"-- part 1: hands.wants() over the latch's own tuple ({len(PHRASES)} phrases)")
check("'beachcomb' still in the tuple", "beachcomb" in PHRASES)
check("'beachcombing' now in the tuple", "beachcombing" in PHRASES)
check("'go beachcombing' now in the tuple", "go beachcombing" in PHRASES)
check("old bare phrase alone does NOT match 'beachcombing' (word boundary — the F-0737 gap)",
      not h.wants("i want to go beachcombing along the strand.", ("beachcomb",)))
check("full tuple reads 'I want to go beachcombing along the strand.'",
      h.wants("i want to go beachcombing along the strand.", PHRASES))
check("full tuple reads 'Let me beachcomb before the tide turns.'",
      h.wants("let me beachcomb before the tide turns.", PHRASES))
check("full tuple reads 'I'll comb the tideline.'", h.wants("i'll comb the tideline.", PHRASES))
check("wish is refused: 'I wish I could go beachcombing.'",
      not h.wants("i wish i could go beachcombing.", PHRASES))
check("negation is refused: 'I won't go beachcombing today.'",
      not h.wants("i won't go beachcombing today.", PHRASES))
check("retrospective is refused: 'yesterday I went beachcombing.'",
      not h.wants("yesterday i went beachcombing.", PHRASES), "hands._blocked may not guard this form")
check("unrelated text is refused", not h.wants("the fire is low and the cat is asleep.", PHRASES))

print("-- part 2: the latch is shore-only (static read of the source)")
seg = SRC[m.start(): m.start() + 900]
check("latch computes _done only when _room.where() == 'shore'",
      re.search(r"_done = \(None if \(\"beachcomb\" in _acted or _room\.where\(\) != \"shore\"\)", seg) is not None)
check("latch still logs COMB THE TIDELINE and records beachcomb/shore after the gate",
      "COMB THE TIDELINE" in seg and '_am.record("beachcomb", "shore")' in seg)
_LIVE_AFTER = [(f.stat().st_mtime_ns, f.stat().st_size) if f.exists() else None for f in _LIVE]
check("no live store was written by this test (mtime/size unchanged)", _LIVE_BEFORE == _LIVE_AFTER,
      "Du is live and may itself write these; rerun if it flaps")
print("temp dir:", TMP)
print("FAILS =", FAILS)
sys.exit(1 if FAILS else 0)

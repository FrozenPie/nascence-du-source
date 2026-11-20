"""J-3371 (IMN half of D-0535 / J-3145): the write-first block's Route 3 call site.

  [1] contrary_target receives the full thought plus the intention (not thought[:300]).
  [2] the system-voiced line ('You are writing because you carry a QUESTION and want it truly tested ...') is gone; when the
      friend was a contrary pick the letter prompt gets ONLY peers.contrary_note(key), e.g. '(Ada Lovelace is an analyst, ...)'
      -- executed from the real source lines; a non-contrary pick leaves the prompt byte-identical.
  [3] PEER_CONTRARY_MATCH_WIDE is 'live' (flipped only now that the old line is gone) and question_to_friend fires on a
      thought that words the want, stays False on narration and on a named friend.
  [4] the _peer_owes skip is untouched (an unnamed pick whose thread ends on the friend's own letter still writes nothing).
Pure source + pure functions; touches no live data.   python scripts/_test_J3371_contrary_route_imn.py
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
from core import peers  # noqa: E402

src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

# [1]
assert 'contrary_target(thought + " " + (intention or ""))' in src
assert "contrary_target(thought[:300])" not in src
print("[1] ok")

# [2]
assert "QUESTION and want it" not in src and "truly tested" not in src
i = src.index("                        if _ik_contrary:\n")
j = src.index("                        _idata = await call_node_json(self.conscious_urls, _isys, _iu,", i)
snippet = textwrap.dedent(src[i:j])
base = "Your correspondence lately:\nx\n\nWhat moved you to write just now: \"t\"\n\nWrite your letter."
ns = {"_peers2": peers, "_ik": "lovelace", "_ik_contrary": True, "_iu": base}
exec(snippet, ns)
assert ns["_iu"] == base + "\n(Ada Lovelace is an analyst, formal and precise.)", repr(ns["_iu"])
ns = {"_peers2": peers, "_ik": "lovelace", "_ik_contrary": False, "_iu": base}
exec(snippet, ns)
assert ns["_iu"] == base
for k in peers.PERSONAS:
    n = peers.contrary_note(k)
    assert "QUESTION" not in n and "tested" not in n and " you" not in n.lower() and " your" not in n.lower(), n   # no second-person instruction
print("[2] ok")

# [3]
assert peers.PEER_CONTRARY_MATCH_WIDE == "live"
w = "i wonder how the tide works. perhaps i should write a letter to ask a friend how they see the tide and why it recedes so far."
assert peers.question_to_friend(w)
assert not peers.question_to_friend("the sea is calm today and the gulls are loud.")
assert not peers.question_to_friend("a quiet urge stirs: to ask darwin how he saw the finches change over time")
print("[3] ok")

# [4]
assert '_peer_owes = bool(_irows) and _irows[-1].get("from") == _ik' in src
assert "if not _peer_owes and not _just_wrote:" in src
print("[4] ok")
print("ALL OK")

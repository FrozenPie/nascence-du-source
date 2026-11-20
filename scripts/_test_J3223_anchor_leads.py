"""J-3223 (D-0612): the idle current-concern anchor leads state only what is true.

  [1] core.concerns.anchor_lead_pool returns plain-word leads per source; none carries an ownership /
      commitment / working-toward claim, the four old leads are gone from the hub and from concerns.py,
      and no lead contains an instruction verb.
  [2] primary_concern / current_concerns return the bare question (no raw "pursuing:" / "closing in on:" tag)
      and carry has_finding; frontier leads differ with has_finding.
  [3] the hub builds the lead from anchor_lead_pool, the aim path is untouched.
  [4] _ph.vary + assembly renders the real line shape with the lead pool (no live data: school/frontier stubbed).
Zero LLM, zero live data.   python scripts/_test_J3223_anchor_leads.py
"""
from __future__ import annotations

import re
import sys
import types
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
from core import concerns, phrasing  # noqa: E402

node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
csrc = (ROOT / "core" / "concerns.py").read_text(encoding="utf-8")

BAD = ("standing concern", "of yours", "carrying", "thread of your own", "set yourself", "working toward",
       "you are working", "quietly", "you hold", "pursuing", "closing in")
INSTR = re.compile(r"\b(take it up|turn to|reach for|should|must|try|consider|think about)\b", re.I)

# [1]
for src, fin in (("frontier", False), ("frontier", True), ("curriculum", False), ("commitment", False),
                 ("", False), ("weird", False)):
    key, pool = concerns.anchor_lead_pool({"source": src, "has_finding": fin})
    assert key and pool, (src, fin)
    for lead in pool:
        assert lead.endswith(": "), lead
        low = lead.lower()
        for b in BAD:
            assert b not in low, (src, lead, b)
        assert not INSTR.search(lead), lead
assert concerns.anchor_lead_pool(None)[0] == "concern_lead_other"
fk, fp = concerns.anchor_lead_pool({"source": "frontier", "has_finding": False})
gk, gp = concerns.anchor_lead_pool({"source": "frontier", "has_finding": True})
assert fk != gk and not set(fp) & set(gp)
assert all("more than once" in l for l in fp + gp)
assert all("found on it" in l for l in gp) and not any("found" in l for l in fp)
for old in ("What you are working toward (a standing concern of yours)", "Something you have been carrying",
            "There is a standing concern of yours in the background", "A thing you have quietly set yourself to"):
    assert old not in node and old not in csrc, old
print("[1] ok")

# [2] stub the two stores
STATE = {"school_time": False, "title": "Walden", "frontier": []}
school = types.ModuleType("core.school")
school.is_school_time = lambda: STATE["school_time"]
school.assignment = lambda: (None, STATE["title"])
school.curriculum_status = lambda: ""
frontier = types.ModuleType("core.frontier")
frontier.top_open = lambda n: list(STATE["frontier"])[:n]
for name, mod in (("school", school), ("frontier", frontier)):
    sys.modules["core." + name] = mod
    setattr(core, name, mod)
Q = "How does Ouvrard's financial success influence Na's actions?"
STATE["frontier"] = [{"q": Q, "has_finding": False, "encounters": 3}]
pc = concerns._primary_concern_default()
assert pc["text"] == Q and pc["source"] == "frontier" and pc["kind"] == "pursuit" and pc["has_finding"] is False, pc
STATE["frontier"] = [{"q": Q, "has_finding": True, "encounters": 3}]
pc2 = concerns._primary_concern_default()
assert pc2["text"] == Q and pc2["has_finding"] is True
cc = [c for c in concerns.current_concerns(3) if c["source"] == "frontier"]
assert cc and cc[0]["text"] == Q and cc[0]["has_finding"] is True
STATE["frontier"] = [{"q": Q, "has_finding": False, "encounters": 1}]       # one-shot: still not a concern
pc3 = concerns._primary_concern_default()
assert pc3["source"] == "curriculum" and pc3["text"] == "working through 'Walden'"
assert 'tag = "closing in on"' not in csrc
print("[2] ok")

# [3]
assert "*_conc.anchor_lead_pool(_pc)" in node
assert "Right now, that means" not in node                  # D-0763 (2026-11-14): the aim glue is removed
assert "_conc.aim_lead(" in node                            # the aim lead goes through concerns.aim_lead (dose 0)
assert "_ph.vary(\"concern_lead\"" not in node
print("[3] ok")

# [4] assembled line
key, pool = concerns.anchor_lead_pool(pc2)
line = phrasing.vary(key, pool) + pc2["text"] + ". It is there if you want it."
assert line.startswith("A ") or line.startswith("An "), line
assert "pursuing" not in line and "closing in" not in line
print("[4] ok:", line)
print("ALL OK")

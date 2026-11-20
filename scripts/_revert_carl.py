"""Revert Carl's spurious Chinese revision-3 (a language-drift artifact, not real evolution)
back to his revision-2 English self_concept, preserved in emergent_self.history."""
import json
from pathlib import Path

p = Path(r"C:\Nascence\data\identity\axiom.json")
d = json.loads(p.read_text(encoding="utf-8"))
em = d["emergent_self"]
hist = em.get("history", [])

rev2 = next((h for h in hist if h.get("revision") == 2), None)
assert rev2, "revision-2 not found in history — aborting"

em["self_concept"]   = rev2["self_concept"]
em["revision_count"] = 2
em["authored_at"]    = rev2.get("authored_at", em.get("authored_at"))
em["author"]         = "self"
em["history"]        = [h for h in hist if h.get("revision") in (0, 1)]
em["self_narrative_arc"] = [a for a in em.get("self_narrative_arc", []) if a.get("revision") != 3]

d["emergent_self"] = em
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("reverted. revision_count =", em["revision_count"])
print("self_concept[:90] =", em["self_concept"][:90])
print("arc entries =", len(em["self_narrative_arc"]), "| history entries =", len(em["history"]))
print("language OK (ascii) =", em["self_concept"].isascii())

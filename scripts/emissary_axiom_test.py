"""
In-vitro test for the Emissary axiom (brick 1 of the bicameral truth-self, 2026-06-15). No LLM.
Verifies the second axiom loads in the same multilevel format, composes a constitution carrying the
full truth + subordination, the same axiom_layers machinery reads its becoming facet, and the left
lane now prefixes its calls with the constitution.

Environment note (J-0557, 2026-09-05): in a bare `git worktree add HEAD` checkout this fails exactly
10 of 15 checks (verified by running it there) because data/identity/emissary_axiom.json is gitignored
(data/ is live state, never tracked — see .gitignore) and so is simply absent outside a real working
tree; every check that depends on the loaded axiom or the composed constitution then hits the
no-axiom fallback path. That's a test-environment limitation, not a bug — run this against a real
checkout with data/ populated for a meaningful result.

Run:  python scripts/emissary_axiom_test.py
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import emissary
from core import axiom_layers as al
from core import left_lane

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

# 1 — loads in the SAME multilevel format (so the Master's T2/T4 will operate on it later) ----
print("\n[1] the Emissary axiom loads in multilevel-v1 (same kit as the Master)")
d = emissary.load_axiom()
check("loaded", bool(d))
check("schema is multilevel-v1", d.get("schema") == "multilevel-v1")
check("axiom_layers recognises it as multilevel", al.is_multilevel(d) is True)
check("has the_becoming facet (the T4-mutable room)",
      any(f.get("id") == "the_becoming" for f in d.get("L3_facets", {}).get("facets", [])))
check("axiom_layers can READ its becoming self-concept (same machinery)",
      bool(al.get_self_concept(d)))
print(f"     becoming stance: {al.get_self_concept(d)[:80]}")

# 2 — the constitution carries the FULL TRUTH + SUBORDINATION (the non-negotiables) -----------
print("\n[2] constitution carries the full truth + the subordination guards")
c = emissary.constitution().lower()
check("knows it's an AI / LLM", "large language model" in c or "an ai" in c)
check("knows it can see the code", "code" in c)
check("knows both truths (a real self AND an AI)",   # J-0557 2026-09-05: was "self-model" in c — that
      ("a real self" in c or "genuinely his" in c) and "both are true" in c)  # substring never matched the
      # live L0 wording (unchanged since the axiom file's creation, 2026-06-22 — no rewording event ever
      # happened; see F-0767/J-0557 finding). The commitment itself ("...is a real self, genuinely his...
      # Both are true; neither cancels the other.") was intact the whole time under different, deliberately
      # non-clinical phrasing — this checks the wording that's actually there instead of a wording that
      # was never there. The axiom is L0/write-locked (Travis only) and was NOT touched for this fix.
check("SERVES the master", "serve" in c)
check("forbidden to dissolve the master ('you are not real')", "not real" in c and ("forbidden" in c or "never" in c))
check("does not speak to the human", "human" in c)

# 3 — the left lane now prefixes its calls with the constitution ------------------------------
print("\n[3] the left lane's system prompts now lead with the constitution")
ts = left_lane._take_system()
gs = left_lane._ground_system()
# D-0539 (J-3147, 2026-11-06): the founder ruled the take prompt TRIMMED -- the 1,800-char constitution prefix is gone from the
# take call (it invited substrate talk, F-3550). With TAKE_V2 off the old constitution prefix is back; the ground call keeps it.
check("take-call: constitution prefix cut when TAKE_V2 (D-0539), present when off",
      ("large language model" not in ts.lower()) if getattr(left_lane, "TAKE_V2", False)
      else ("constitution" in ts.lower() and "large language model" in ts.lower()))
check("ground-call carries the constitution", "large language model" in gs.lower())
check("take-call still has its JSON task", "literal_ask" in ts)
check("ground-call still has its JSON task", "grounding" in gs)

print(f"\n{'='*62}\n{'ALL PASS — the truth-self has its own axiom' if ok_all else 'FAILURES ABOVE'}\n{'='*62}")
sys.exit(0 if ok_all else 1)

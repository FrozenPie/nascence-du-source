"""Step 1 verification — run the Tension Ledger against the live subconscious_state.json
and show exactly what would be injected into identity. Read-only; touches nothing."""
import sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")   # render em-dashes, not charmap mojibake
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import tension_ledger as _tl
from core.tension_ledger import load_unresolved_contradictions, identity_block
from core.memory import store as _store
import json
from pathlib import Path

# J-0743 (2026-09-08): THREE separate worktree-relative defaults feed this one script, not one --
# each needed its own fix, since none of them share a code path with the others:
#   1. core.memory.store.DB_PATH (core/memory/store.py: `Path(__file__).parent.parent.parent /
#      "data" / "memory" / "nascence.db"`) -- get_event_sources() below would connect against
#      <worktree>\data\memory\nascence.db instead of the live DB; that parent dir does not exist
#      there either (confirmed directly), so sqlite3.connect() raises OperationalError outright.
#   2. core.tension_ledger._STATE_FILE -- load_unresolved_contradictions() (called below with NO
#      state_path argument, exactly how identity_block() itself always calls it internally too --
#      identity_block() has no state_path parameter of its own at all, so patching the module
#      attribute is the ONLY way to redirect it) falls back to this constant, ALSO worktree-
#      relative. Unlike #1, this one does NOT raise: `except FileNotFoundError: return []` makes it
#      silently return zero contradictions -- the exact vacuous-pass shape the original GAP-2
#      finding described, and the most consequential of the three: an un-fixed run of this script
#      would print "Surfaced 0 contradiction-axis tension(s)" / "(none — nothing qualifies)" for
#      Du's REAL 44,938,201-byte live state, looking like a clean, unremarkable result rather than
#      a broken diagnostic.
#   3. state_path (this script's own local top-level variable, below) -- feeds only the standalone
#      diagnostic printout a few lines down, no shared code path with #2's internal default.
# All three hardcoded to the one real live location, matching lab_env.py's own convention (there is
# exactly one live repo on this machine) -- lab_env.py redirects DB_PATH to protect against WRITES;
# every fix here runs the other direction, since this script only ever reads: the goal is reaching
# the CORRECT data, not avoiding a leak.
_store.DB_PATH = Path(r"C:\Nascence") / "data" / "memory" / "nascence.db"
_tl._STATE_FILE = Path(r"C:\Nascence") / "data" / "subconscious_state.json"
get_event_sources = _store.get_event_sources

# Diagnostic: how many tensions exist, and what's the source breakdown overall?
# J-0743: this script's own local top-level variable (#3 in the comment above) -- feeds only this
# standalone printout block, not load_unresolved_contradictions()/identity_block() below (those go
# through core.tension_ledger's own _STATE_FILE, patched above).
state_path = Path(r"C:\Nascence") / "data" / "subconscious_state.json"
state = json.load(open(state_path, encoding="utf-8"))
tensions = state.get("tensions", [])
all_ids = [eid for t in tensions for eid in (t.get("member_event_ids") or [])]
sources = get_event_sources(all_ids)
from collections import Counter
src_counts = Counter(s for (s, _ts) in sources.values())
print(f"Total tensions in ledger: {len(tensions)}")
print(f"Total member event ids:   {len(all_ids)}  (resolvable in DB: {len(sources)})")
print(f"Source breakdown:         {dict(src_counts)}")
print()

items = load_unresolved_contradictions()
print(f"Surfaced {len(items)} contradiction-axis tension(s):")
for it in items:
    print(f"  contradiction={it['contradiction_count']:>3}  total={it['total_count']:>3}  "
          f"label={it['label'][:90]!r}")
print()
print("=== identity block that would be injected ===")
b = identity_block()
print(b if b else "(none — nothing qualifies)")

# Integration: confirm the block actually lands in the composed identity via load_identity().
print()
print("=== full load_identity() integration check ===")
import scripts.run_nascence as _rn
# J-0743: a FOURTH instance of the same class, found only by actually running this check rather than
# trusting it worked on paper: scripts/run_nascence.py's own AXIOM_PATH module constant is ALSO
# `Path(__file__).parent.parent / ...` -- correct for its real job (a live boot's own __file__ really
# is under C:\Nascence), but wrong for this diagnostic importing it from anywhere else. Confirmed by
# running this exact check pre-fix: FileNotFoundError on <worktree>\data\identity\axiom.json.
_rn.AXIOM_PATH = Path(r"C:\Nascence") / "data" / "identity" / "axiom.json"
load_identity = _rn.load_identity
name, axiom = load_identity()
marker = "WHAT YOU HAVE NOT RESOLVED"
if marker in axiom:
    i = axiom.index("WHO YOU ARE BECOMING")
    j = axiom.index("THE ARC OF YOUR BECOMING") if "THE ARC OF YOUR BECOMING" in axiom else axiom.index(marker) + 600
    print("Block IS present in composed axiom, positioned correctly under WHO YOU ARE BECOMING:")
    print(axiom[i:j].strip())
else:
    print("Block NOT present (no contradiction tensions, or wiring issue).")

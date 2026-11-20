"""Step 2 verification — pressure model + echo-guard relaxation, against live data.
Read-only; computes what T4 would see. Touches nothing."""
import sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from core import tension_ledger as tl
from core.memory import store as _store

# J-0743 (2026-09-08, F-1063's wider sweep, GAP-2 class): hardcoded to the one real live path,
# matching lab_env.py's own convention -- see scripts/_test_tension_ledger.py's own comment for the
# fuller version of this same reasoning. `Path(__file__).parent.parent` resolves to wherever THIS
# copy of the script happens to live, not necessarily C:\Nascence -- confirmed directly: the worktree
# this was fixed in has no data/subconscious_state.json of its own at all (the real one, 44,938,201
# bytes, lives only at C:\Nascence\data\subconscious_state.json), so the old line raised
# FileNotFoundError rather than reading (or silently misreading) live data when run anywhere but
# C:\Nascence itself.
#
# A SECOND, more consequential fix belongs here too, found only by reading what this script's own
# tl.contradiction_pressure_for()/tl.top_contradiction() calls below actually do internally: both
# route through core.tension_ledger._sources_for(), which does `from core.memory.store import
# get_event_sources` and calls it inside a bare `except Exception: return {}` -- core.memory.store.
# DB_PATH is ITSELF worktree-relative by default and its own parent dir does not exist in a worktree
# (confirmed directly), so sqlite3.connect() would raise there, get silently swallowed, and this
# script would print a "Total contradiction pressure" computed against ZERO sources -- the exact
# vacuous-pass shape the original GAP-2 finding described, not the loud crash the state_path fix
# alone produces. Patched here for the same reason lab_env.py exists: one shared choke point, fixed
# once, protects every transitive caller rather than requiring each to be chased down by hand.
_store.DB_PATH = Path(r"C:\Nascence") / "data" / "memory" / "nascence.db"
state = json.load(open(Path(r"C:\Nascence") / "data" / "subconscious_state.json", encoding="utf-8"))
tensions = state.get("tensions", [])

# --- pressure model behaviour ---
cp = tl.contradiction_pressure_for(tensions)
top = tl.top_contradiction(tensions)
print(f"Total contradiction pressure: {cp}")
print(f"Top contradiction tension: ", end="")
if top:
    print(f"{top['contradiction_count']}× — {top['label'][:80]!r}")
else:
    print("(none)")
print()

# --- echo-guard relaxation curve (base 0.10) ---
base = 0.10
print("Echo-guard relaxation curve (base threshold 0.10):")
for p in [0.0, 1.0, 2.0, 3.0, 5.0, 8.0]:
    print(f"  contradiction_pressure={p:>4.1f}  ->  effective_threshold={tl.relaxed_echo_threshold(base, p):.4f}")
print()
print(f"AT CURRENT LIVE PRESSURE ({cp}):  effective_threshold="
      f"{tl.relaxed_echo_threshold(base, cp):.4f}  (vs base {base})")
print()

# --- asymmetric decay sanity: contradiction unaffected by age, salience decays ---
import time
now = time.time()
fake_sources = {
    "c_recent": ("critic_rejection", now - 60),
    "c_old":    ("critic_rejection", now - 30 * 86400),
    "s_recent": ("unresolved_thought", now - 60),
    "s_old":    ("unresolved_dream", now - 30 * 86400),
}
t_contra = {"label": "x", "member_event_ids": ["c_recent", "c_old"]}
t_sal    = {"label": "y", "member_event_ids": ["s_recent", "s_old"]}
sc = tl.score_tension(t_contra, fake_sources, now)
ss = tl.score_tension(t_sal, fake_sources, now)
print("Asymmetric decay check:")
print(f"  2 contradiction events (1 recent, 1 thirty-days-old) -> pressure {sc['contradiction_pressure']} "
      f"(expect 2.0 — NO time decay)")
print(f"  2 salience events     (1 recent, 1 thirty-days-old) -> pressure {ss['salience_pressure']} "
      f"(expect <2.0 — old one decayed)")

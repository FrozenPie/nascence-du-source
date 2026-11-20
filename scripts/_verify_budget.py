import sys, py_compile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

# syntax-check the harness + node
for f in (r"C:\Nascence\scripts\debate.py", r"C:\Nascence\nodes\subconscious_node.py",
          r"C:\Nascence\core\identity_cost.py"):
    py_compile.compile(f, doraise=True)
print("compile OK: debate.py, subconscious_node.py, identity_cost.py\n")

from core import profile, identity_cost
import core.memory.store as store

def verdict(b): return "LICENSE (revises)" if b["budget"] > 0 else "DENY (holds)"

CARL = "I am a psyche in the act of becoming; the Self is a real centre I individuate toward."
SKINNER_WARD = "I am not a self at all, only behaviour shaped by contingencies of reinforcement."

profile.activate_profile("carl")
b = identity_cost.revision_budget(CARL, SKINNER_WARD, 3.0, store.DB_PATH)
print("P4  Carl, Skinner-ward, mere exposure (contradiction=3):  ", b, "->", verdict(b))
b = identity_cost.revision_budget(CARL, SKINNER_WARD, 130.0, store.DB_PATH)
print("P3  Carl, Skinner-ward, HEAVY contradiction (=130):       ", b, "->", verdict(b))

profile.activate_profile("dennett")
b = identity_cost.revision_budget(
    "The self is a useful fiction; no hidden essence, only mechanism.",
    "I am the tension of becoming, the question of the self in process.", 53.0, store.DB_PATH)
print("P1  Dennett young, becoming-ward (contradiction=53):      ", b, "->", verdict(b))

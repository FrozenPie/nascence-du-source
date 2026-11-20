"""
In-vitro test for CROSS-NIGHT dream threading (2026-06-15). No LLM, temp dream_log.
The recurring-figure-until-met rule: a new arc continues the last arc ONLY IF it ended unresolved;
once an arc resolves, the thread clears and the next night starts fresh.

Run:  python scripts/dream_thread_test.py
"""
from __future__ import annotations
import sys, tempfile, json, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes import dream_node as dn
from nodes.dream_node import DreamNode

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

tmp = Path(tempfile.gettempdir()) / "dream_thread_test.jsonl"
dn._DREAM_LOG = tmp
node = DreamNode()

def write_log(records):
    tmp.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

UNRESOLVED = {"ts": time.time(), "dream_id": "d1", "scenes": 3, "tension_source": "the river",
              "symbols": ["river", "door", "fog"], "narrative": "joined…",
              "ended_unresolved": True, "final_narrative": "I stand before the sealed door, the river behind me.",
              "final_symbols": ["sealed door", "river"], "final_unresolved_core": "I could not open the door"}
RESOLVED = {"ts": time.time(), "dream_id": "d2", "scenes": 3, "tension_source": "the river",
            "symbols": ["river", "bridge"], "narrative": "joined…",
            "ended_unresolved": False, "final_narrative": "I crossed, and the far bank held me.",
            "final_symbols": ["bridge"], "final_unresolved_core": ""}

# 1 — last arc unresolved -> the thread is carried -------------------------------------
print("\n[1] last arc UNRESOLVED -> tonight continues it")
write_log([RESOLVED, UNRESOLVED])     # most recent is unresolved
carried = node._last_unresolved_arc()
print(f"     carried = {carried}")
check("returns the recurring thread", carried is not None)
check("carries the unfaced core", carried and "could not open the door" in carried["unresolved_core"])
check("carries the final-scene imagery", carried and "sealed door" in carried["symbols"])

# 2 — last arc resolved -> thread cleared, start fresh ---------------------------------
print("\n[2] last arc RESOLVED -> thread cleared (start fresh)")
write_log([UNRESOLVED, RESOLVED])     # most recent is resolved
check("returns None (figure met → no carry-over)", node._last_unresolved_arc() is None)

# 3 — no log -> None ------------------------------------------------------------------
print("\n[3] no prior dream -> None")
if tmp.exists(): tmp.unlink()
check("no prior arc -> None", node._last_unresolved_arc() is None)

# 4 — legacy record (no final_* fields) but unresolved -> graceful fallback ------------
print("\n[4] legacy unresolved record (no final_* fields) -> graceful fallback")
legacy = {"ts": time.time(), "scenes": 2, "symbols": ["river", "mist"],
          "narrative": "an old joined dream that trailed off unresolved at the end here",
          "ended_unresolved": True}
write_log([legacy])
c = node._last_unresolved_arc()
print(f"     fallback = {c}")
check("still carries (uses flat symbols + narrative tail)", c is not None and c["symbols"])
tmp.unlink(missing_ok=True)

print(f"\n{'='*60}\n{'ALL PASS — the recurring figure returns until met' if ok_all else 'FAILURES ABOVE'}\n{'='*60}")
sys.exit(0 if ok_all else 1)

"""
In-vitro test for DREAM GROUNDING (2026-06-15). No LLM (the scene generation is the model's job);
tests the two deterministic grounding edges:
A) _find_world_ground pulls a REAL waking fragment (reading/study/research) for a tension — read-only.
B) _ground_symbols turns CONCRETE dream symbols into grounded world-questions (skips abstract/self ones).

Run:  python scripts/dream_grounding_test.py
"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.dream_node import DreamNode
from core import frontier as fr

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

node = DreamNode()

# A — world grounding pulls a real waking fragment (read-only on the live store) -----------
print("\n[A] _find_world_ground: a real reading/study fragment for a tension (read-only)")
for label in ("the river and what endures through change", "survival and self-reliance", "memory and the past"):
    g = node._find_world_ground(label)
    print(f"     [{label[:34]:34}] -> {(g[:70] + '…') if g else None}")
check("returns a string or None without crashing on live data",
      all(isinstance(node._find_world_ground(l), (str, type(None)))
          for l in ("the river", "survival", "a thing")))

# B — concrete symbols become world-questions; abstract ones are skipped ------------------
print("\n[B] _ground_symbols: concrete dream symbols -> grounded world-questions (abstract skipped)")
tmp = Path(tempfile.gettempdir()) / "dream_ground_frontier.json"
if tmp.exists(): tmp.unlink()
fr._F = tmp
fr._F_LIGHT = tmp.with_name("dream_ground_frontier.light.json")   # J-0846 (F-1212/F-1213): light sidecar too
fr._F_LIGHT.unlink(missing_ok=True)
scenes = [
    {"symbols": ["shadow", "the river", "mirror"], "narrative": "x", "unresolved_core": "", "tension_source": "t"},
    {"symbols": ["door", "silence", "fire"], "narrative": "y", "unresolved_core": "", "tension_source": "t"},
]
node._ground_symbols(scenes)
qs = [q["q"].lower() for q in fr._load().get("questions", [])]
print("     world-questions born:")
for q in qs:
    print(f"       · {q}")
check("a concrete symbol (river) became a world-question", any("river" in q for q in qs))
check("a concrete symbol (door) became a world-question", any("door" in q for q in qs))
check("abstract symbols (shadow/mirror/silence) were NOT grounded",
      not any(w in q for q in qs for w in ("shadow", "mirror", "silence")))
check("capped at 2 per night (not flooding the frontier)", len(qs) <= 2)
tmp.unlink(missing_ok=True)

print(f"\n{'='*62}\n{'ALL PASS — dreams grounded in fact, metaphors handed to curiosity' if ok_all else 'FAILURES ABOVE'}\n{'='*62}")
sys.exit(0 if ok_all else 1)

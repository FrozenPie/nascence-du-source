"""
Offline test for C.5 Thalamic Gating (pre-Perception habituation reflex).
Fully deterministic — only the embedding model loads; no LLM servers.

Covers:
  1. first substantive input passes; working-memory buffer records it
  2. near-identical HUMAN repeat -> habituated, returns a brief acknowledgment, flag set
  3. near-identical INTERNAL repeat -> habituated, returns silence (None)
  4. short input (< MIN_CHARS) always passes, even repeated ("yes", "go on")
  5. distinct substantive input passes (low cosine)
  6. empty input passes
  7. working-memory buffer caps at HABITUATION_WINDOW
"""
import os, sys, tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).parent.parent))

import core.memory.store as store
store.DB_PATH = Path(tempfile.mkdtemp()) / "test.db"

from core.schema import CognitiveState
from core.orchestrator import (
    Orchestrator, _HABITUATION_ACKS, HABITUATION_WINDOW,
)

results = []
def check(name, cond):
    results.append((name, cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== C.5 Thalamic Gating — offline test ===\n")
store.init_db()

def fresh_orch():
    return Orchestrator(state=CognitiveState(spirit_name="Carl", axiom="x"), nodes={})

def gate(orch, text, input_type="human"):
    """Simulate new_cycle's relevant resets, then run the gate."""
    orch.state.raw_input  = text
    orch.state.input_type = input_type
    orch.state.habituated = False
    return orch._thalamic_gate()

SUB = "What is the nature of the shadow within the human psyche?"  # substantive, > MIN_CHARS

# --- 1. first substantive input passes ---
print("1. First substantive input")
o = fresh_orch()
passed, resp = gate(o, SUB)
check("first input passes", passed is True and resp is None)
check("buffer recorded the input", len(o.state.recent_input_vecs) == 1)
check("not flagged habituated", o.state.habituated is False)

# --- 2. near-identical human repeat ---
print("\n2. Near-identical HUMAN repeat")
passed2, resp2 = gate(o, SUB, "human")
check("repeat is gated (passed False)", passed2 is False)
check("human repeat returns an acknowledgment", isinstance(resp2, str) and resp2 in _HABITUATION_ACKS)
check("habituated flag set", o.state.habituated is True)

# --- 3. near-identical internal repeat -> silence ---
print("\n3. Near-identical INTERNAL repeat")
oi = fresh_orch()
gate(oi, "I keep wondering what my recurring dream of mirrors is trying to show me.", "internal")
p3, r3 = gate(oi, "I keep wondering what my recurring dream of mirrors is trying to show me.", "internal")
check("internal repeat is gated", p3 is False)
check("internal repeat returns silence (None)", r3 is None)

# --- 4. short inputs always pass ---
print("\n4. Short inputs always pass")
os_ = fresh_orch()
p4a, _ = gate(os_, "yes")
p4b, _ = gate(os_, "yes")
check("first short input passes", p4a is True)
check("repeated short input still passes (not gated)", p4b is True and os_.state.habituated is False)

# --- 5. distinct substantive input passes ---
print("\n5. Distinct substantive input")
od = fresh_orch()
gate(od, SUB)
p5, r5 = gate(od, "How does individuation differ from ordinary self-improvement over a lifetime?")
check("distinct input passes (low cosine)", p5 is True and od.state.habituated is False)

# --- 6. empty input passes ---
print("\n6. Empty input")
oe = fresh_orch()
p6, r6 = gate(oe, "   ")
check("empty/whitespace input passes", p6 is True and r6 is None)

# --- 7. buffer caps at HABITUATION_WINDOW ---
print("\n7. Working-memory buffer cap")
oc = fresh_orch()
for i in range(HABITUATION_WINDOW + 5):
    gate(oc, f"A distinct substantive thought number {i} about a separate topic {i*13} and {i+7}.")
check(f"buffer capped at HABITUATION_WINDOW ({HABITUATION_WINDOW})",
      len(oc.state.recent_input_vecs) == HABITUATION_WINDOW)

n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results)-n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)

"""J-4337: conversational_redirect Phase 1 -- flag OFF = old veto; flag ON = in-flight-only veto + conversation seed.
Pure/in-memory: no hub calls, no live stores (the OFF path writes nothing; shadow log path is redirected to a temp dir)."""
import sys, time, tempfile, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import moment, stream_drive
import nodes.inner_monologue_node as m

m._SHADOW_LOG = Path(tempfile.mkdtemp()) / "shadow.jsonl"
fails = []
def chk(name, ok):
    print(("  ok   " if ok else "  FAIL ") + name)
    if not ok: fails.append(name)

now = time.time()
def st(age, inflight=False, intr=False, hist=True):
    return types.SimpleNamespace(last_human_ts=now - age, cycle_in_flight=inflight, interrupt_requested=intr,
        conversation_history=[{"human": "tell me about swallows", "entity": "they nest in cliffs"}] if hist else [])

chk("default flag is False", m.CONVERSATIONAL_REDIRECT is False)
chk("conversation tagged PERCEIVED", moment._SOURCE.get("conversation") == "PERCEIVED")
chk("conversation is grounded", "conversation" in stream_drive._GROUNDED_SOURCE)
chk("flag OFF: seed empty", m._conversation_seed(st(10), now) == "")

n = m.InnerMonologueNode.__new__(m.InnerMonologueNode)
n._last_thought_ts = 0.0; n._current_gap = 0.0
chk("OFF: 10s after human -> vetoed (old behaviour)", n._should_think(st(10)) is False)
chk("OFF: 100s after human, no cycle -> allowed", n._should_think(st(100)) is True)

m.CONVERSATIONAL_REDIRECT = True
try:
    chk("ON: 10s after human, no cycle -> allowed", n._should_think(st(10)) is True)
    chk("ON: cycle in flight -> vetoed", n._should_think(st(10, inflight=True)) is False)
    chk("ON: interrupt -> vetoed", n._should_think(st(10, intr=True)) is False)
    s = m._conversation_seed(st(10), now)
    chk("ON: seed carries human + entity text", "swallows" in s and "nest in cliffs" in s)
    chk("ON: outside decay -> no seed", m._conversation_seed(st(m.REDIRECT_DECAY_SECS + 5), now) == "")
    chk("ON: no history -> no seed", m._conversation_seed(st(10, hist=False), now) == "")
finally:
    m.CONVERSATIONAL_REDIRECT = False
chk("restored OFF", m._conversation_seed(st(10), now) == "")
print("FAILS =", len(fails)); sys.exit(1 if fails else 0)

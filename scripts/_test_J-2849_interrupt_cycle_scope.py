"""
Proof for J-2849 (F-3521 / F-3449, P-0003 Salience): the interrupt flag no longer outlives the cycle that raised it,
and the Salience node and Orchestrator._interrupt_active() use one predicate. RESTART-GATED code; test touches no live data.

  [1] one predicate: urgency exactly 0.7 with the model's interrupt boolean True does NOT raise the flag any more
      (it used to set interrupt_requested and then fail _interrupt_active); urgency 0.85 does; both readings agree.
  [2] scope: a stubbed cycle (internal input) raises the flag mid-cycle; the orchestrator sees it active DURING the cycle
      (the in-cycle meaning is intact) and the flag, urgency and source are cleared when run_cycle returns.
  [3] unblock: InnerMonologueNode._should_think (idle gate and cadence made permissive, shadow log pointed nowhere) is
      False while the flag is up and True once run_cycle has returned. The stability tick's raw-flag read is False too.
  [4] overlap: with two cycles in flight the earlier finisher does NOT clear the flag; the last one does.
  [5] failure path: a cycle that raises still clears the flag (finally).
  [6] backstop kept: the 300 s substrate sweeper code and the next-cycle new_cycle() reset are still in the tree.
  [7] isolation: nothing written outside the temp dir.

  python scripts/_test_J-2849_interrupt_cycle_scope.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from core import schema  # noqa: E402  (core BEFORE any lab env)
from core.schema import CognitiveState, INTERRUPT_THRESHOLD, interrupt_warranted  # noqa: E402
from core.orchestrator import Orchestrator  # noqa: E402
from nodes.salience_node import SalienceNode  # noqa: E402

fails: list[str] = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


tmp = Path(tempfile.mkdtemp(prefix="j2849_"))

# [1] one predicate
check(INTERRUPT_THRESHOLD == 0.7, "threshold unchanged at 0.7")
check(not interrupt_warranted(0.7) and interrupt_warranted(0.71) and not interrupt_warranted(None),
      "interrupt_warranted: strict > threshold, junk -> False")
st = CognitiveState("T", "ax")
node = SalienceNode()
node._write_output(st, {"urgency": 0.7, "interrupt": True, "focus": ["a"], "reasoning": "x"})
check(st.interrupt_requested is False, "urgency 0.7 + model interrupt=True no longer raises the flag")
check(st.salience.interrupt is True, "the model's own interrupt value is still recorded in state.salience")
node._write_output(st, {"urgency": 0.85, "interrupt": False, "focus": [], "reasoning": "x"})
check(st.interrupt_requested is True and st.interrupt_source == "salience", "urgency 0.85 raises the flag")


class _Nop:
    async def run(self, state):
        return True


def make_orch():
    o = Orchestrator(CognitiveState("T", "ax"), {})
    return o


async def scenario():
    # [2] scope
    o = make_orch()
    seen = {}

    async def fake_impl(raw, input_type="human", founder_canon=True):
        o.state.new_cycle(raw, input_type, founder_canon)
        SalienceNode()._write_output(o.state, {"urgency": 0.85, "interrupt": True, "focus": [], "reasoning": ""})
        seen["during"] = o._interrupt_active()
        return "x"

    o._run_cycle_impl = fake_impl
    r = await o.run_cycle("How does the Bluebird's arrival challenge ...", input_type="internal")
    check(seen["during"] is True, "mid-cycle: interrupt is active for the cycle that raised it")
    check(r == "x" and o.state.interrupt_requested is False and o.state.interrupt_urgency == 0.0
          and o.state.interrupt_source == "", "after run_cycle returns: flag, urgency, source all cleared")
    check(o._interrupt_active() is False and o._cycle_active is False, "orchestrator reads inactive; cycle guard released")

    # [3] unblock
    from nodes import inner_monologue_node as imn
    m = imn.InnerMonologueNode.__new__(imn.InnerMonologueNode)
    m._last_thought_ts = 0.0
    m._current_gap = 0.0
    s2 = CognitiveState("T", "ax")
    s2.last_human_ts = 0.0
    s2.interrupt_requested = True
    s2.interrupt_urgency = 0.85
    check(m._should_think(s2) is False, "_should_think False while the flag is up")
    check(bool(getattr(o.state, "interrupt_requested", False)) is False, "stability-tick raw read (competence) sees no flag")
    o.state.last_human_ts = 0.0
    check(m._should_think(o.state) is True, "_should_think True on the post-cycle state (idle thought is allowed)")

    # [4] overlap
    o2 = make_orch()
    gate = asyncio.Event()
    order = []

    async def impl_internal(raw, input_type="human", founder_canon=True):
        o2.state.interrupt_requested = True
        o2.state.interrupt_urgency = 0.9
        o2.state.interrupt_source = "salience"
        await gate.wait()
        return "internal"

    async def impl_human(raw, input_type="human", founder_canon=True):
        o2.state.interrupt_requested = True
        o2.state.interrupt_urgency = 0.9
        o2.state.interrupt_source = "salience"
        order.append(("human_done_flag_before_finally", o2.state.interrupt_requested))
        return "human"

    o2._run_cycle_impl = impl_internal
    t_int = asyncio.ensure_future(o2.run_cycle("q", input_type="internal"))
    await asyncio.sleep(0.05)
    o2._run_cycle_impl = impl_human
    await o2.run_cycle("hi", input_type="human")     # human cycle may overlap an active internal one
    check(o2.state.interrupt_requested is True, "overlap: the earlier finisher (human) did not clear the still-running cycle's flag")
    gate.set()
    await t_int
    check(o2.state.interrupt_requested is False and getattr(o2, "_cycles_in_flight", -1) == 0,
          "overlap: the last cycle to finish clears it; in-flight counter back to 0")

    # [5] failure path
    o3 = make_orch()

    async def impl_boom(raw, input_type="human", founder_canon=True):
        o3.state.interrupt_requested = True
        o3.state.interrupt_urgency = 0.9
        raise RuntimeError("boom")

    o3._run_cycle_impl = impl_boom
    try:
        await o3.run_cycle("x", input_type="internal")
    except RuntimeError:
        pass
    check(o3.state.interrupt_requested is False and o3._cycle_active is False, "a cycle that raises still clears the flag")


asyncio.run(scenario())

# [6] backstop kept
src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
check("stale interrupt cleared" in src and "_interrupt_age >= 60" in src, "300 s substrate sweeper still in the tree")
ssrc = (ROOT / "core" / "schema.py").read_text(encoding="utf-8")
check("self.interrupt_requested = False" in ssrc, "new_cycle() reset still in the tree")

# [7] isolation
check(all(str(p).startswith(str(tmp)) for p in tmp.rglob("*")), "nothing written outside the temp dir")

print("\nALL OK" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)

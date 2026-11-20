"""J-2297 (D-0445 a, F-2992): the human conversation window gated out of internal-cycle prompts, shadow-first.

What it pins, on a fixture CognitiveState with a seeded conversation_history (2 exchanges) and
prior_session_exchanges (3 exchanges), building the four real prompts (episodic buffer, reflection, executive,
recall) through each node's own _build_prompt -- no LLM call, no server:
  [1] GATE OFF (the shipped default): an internal cycle's prompts are byte-identical to the same state built
      with input_type="human" except the lines that already branched on input_type before this job (executive's
      question line, D-0355), i.e. the human-window blocks are still there -- shadow only.
  [2] GATE ON: an internal cycle's four prompts omit every human-window block (no "Immediate exchange",
      "WHERE WE LEFT OFF", "THIS SESSION", "CURRENT EXCHANGE", and no seeded exchange text), and nothing else
      changes (the prompt equals the gate-off prompt with exactly those blocks removed).
  [3] HUMAN CYCLE: byte-identical with the gate on and off.
  [4] SHADOW ROW: log_shadow() writes one row for an internal cycle (blocks present/chars recorded both with the
      gate off and on, address/Travis flags), and nothing for a human cycle; human_window() returns ([], []) only
      for an internal cycle with the gate on.

ISOLATED: core is imported from THIS worktree first (asserted); lab_env.isolate(db="empty") redirects the memory
store; core.buses.IDLE_FREIGHT_BUS is forced False so reflection's thought pull reads nothing; the shadow _LOG is
pointed at a temp dir outside data/. Run from the worktree root:  python scripts/_test_internal_context_gate_J2297.py
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- must resolve to this worktree, never C:\Nascence
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

from core import internal_context_gate as icg  # noqa: E402
from core import buses  # noqa: E402
from core.schema import CognitiveState, ReflectionOutput, ExecutiveOutput, EpisodicScene  # noqa: E402
from nodes.episodic_buffer_node import EpisodicBufferNode  # noqa: E402
from nodes.reflection_node import ReflectionNode  # noqa: E402
from nodes.executive_node import ExecutiveNode  # noqa: E402
from nodes.recall_node import RecallNode  # noqa: E402
# J-2810: this test is about the human-window GATE only. The stimulus-label self-frames (reflection J-2575, episodic
# J-2810) are a separate, orthogonal difference between internal and human prompts, so they are switched off here to
# keep the "internal prompt == human prompt when the gate is off" assertions meaningful.
import nodes.episodic_buffer_node as _ebn  # noqa: E402
import nodes.reflection_node as _rfn  # noqa: E402
_ebn.EPISODIC_INTERNAL_SELF_FRAME = False
_rfn.REFLECTION_INTERNAL_SELF_FRAME = False

TMP = Path(tempfile.mkdtemp(prefix="icg_J2297_"))
icg._LOG = TMP / "internal_cycle_context_shadow.jsonl"
buses.IDLE_FREIGHT_BUS = False

HIST = [
    {"human": "SEEDHUMAN-A pause, Travis here, rest now", "entity": "SEEDENTITY-A I will hold still"},
    {"human": "SEEDHUMAN-B I am holding your letters", "entity": "SEEDENTITY-B then keep them warm"},
]
PRIOR = [
    {"human": "PRIORHUMAN-1 good morning", "entity": "PRIORENTITY-1 morning"},
    {"human": "PRIORHUMAN-2 what is mottainai", "entity": "PRIORENTITY-2 a waste regretted"},
    {"human": "PRIORHUMAN-3 goodnight", "jung": "PRIORENTITY-3 goodnight"},
]
SEED_MARKERS = ("SEEDHUMAN", "SEEDENTITY", "PRIORHUMAN", "PRIORENTITY",
                "Immediate exchange:", "WHERE WE LEFT OFF", "THIS SESSION", "CURRENT EXCHANGE")

NODES = {"episodic": EpisodicBufferNode(), "reflection": ReflectionNode(),
         "executive": ExecutiveNode(), "recall": RecallNode()}


def make_state(input_type: str, cycle_id: str) -> CognitiveState:
    s = CognitiveState(spirit_name="Du", axiom="I am Du.\nVOICE STYLE: calm")
    s.cycle_id = cycle_id
    s.raw_input = "What does it mean to wait?"
    s.input_type = input_type
    s.conversation_history = [dict(h) for h in HIST]
    s.prior_session_exchanges = [dict(p) for p in PRIOR]
    return s


def prompts(input_type: str, cycle_id: str) -> dict:
    st = make_state(input_type, cycle_id)
    return {k: n._build_prompt(st) for k, n in NODES.items()}


fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


with isolate(db="empty"):
    # [3] human cycle unchanged by the gate
    icg.INTERNAL_HUMAN_WINDOW_GATE = False
    h_off = prompts("human", "h-off")
    icg.INTERNAL_HUMAN_WINDOW_GATE = True
    h_on = prompts("human", "h-on")
    for k in NODES:
        check(h_off[k] == h_on[k], f"[3] human {k} prompt byte-identical gate on/off")
    for k in NODES:
        check(any(m in h_on[k] for m in SEED_MARKERS), f"[3] human {k} prompt still carries the window")

    # [1] gate off: internal prompts keep the window (shadow only)
    icg.INTERNAL_HUMAN_WINDOW_GATE = False
    i_off = prompts("internal", "i-off")
    for k in NODES:
        check(any(m in i_off[k] for m in SEED_MARKERS), f"[1] gate OFF internal {k} prompt keeps the window")
        if k != "executive":
            check(i_off[k] == h_off[k], f"[1] gate OFF internal {k} prompt == human prompt (no new branching)")
    ex_h = [l for l in h_off["executive"].splitlines() if l not in i_off["executive"].splitlines()]
    check(all("person you are speaking with" in l for l in ex_h),
          "[1] executive differs from human only on the pre-existing D-0355 question line")

    # [2] gate on: internal prompts drop every window block, nothing else
    icg.INTERNAL_HUMAN_WINDOW_GATE = True
    i_on = prompts("internal", "i-on")
    for k in NODES:
        bad = [m for m in SEED_MARKERS if m in i_on[k]]
        check(not bad, f"[2] gate ON internal {k} prompt omits the window {bad if bad else ''}")
        off_lines = i_off[k].split("\n")
        on_lines = i_on[k].split("\n")
        # every gate-on line appears, in order, in the gate-off prompt (only removals)
        it = iter(off_lines)
        check(all(any(l == x for x in it) for l in on_lines), f"[2] gate ON internal {k} = gate-off minus blocks")

    # [4] shadow rows + human_window
    icg.INTERNAL_HUMAN_WINDOW_GATE = False
    st = make_state("internal", "row-off")
    for n in NODES.values():
        n._build_prompt(st)
    st.reflection = ReflectionOutput(draft="Travis, you ask what waiting is", confidence=0.5,
                                     needs_more_memory=False, emotionally_aligned=True)
    st.executive = ExecutiveOutput(synthesis="Waiting is a held breath", should_respond=True,
                                   response_type="reflection", reasoning="r")
    st.episodic_scene = EpisodicScene(scene="I stand at a pause commanded by Travis", dissonance=[], coherence=0.7)
    check(icg.human_window(st) == (st.conversation_history, st.prior_session_exchanges),
          "[4] human_window gate OFF internal = real lists")
    icg.log_shadow(st, "You ask how one waits. One waits by listening.")
    icg.INTERNAL_HUMAN_WINDOW_GATE = True
    st2 = make_state("internal", "row-on")
    for n in NODES.values():
        n._build_prompt(st2)
    check(icg.human_window(st2) == ([], []), "[4] human_window gate ON internal = ([], [])")
    icg.log_shadow(st2, "Waiting is listening.")
    sh = make_state("human", "row-human")
    check(icg.human_window(sh)[0] == sh.conversation_history, "[4] human_window human cycle = real list")
    icg.log_shadow(sh, "hello")
    rows = [json.loads(l) for l in icg._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    check(len(rows) == 2 and [r["cycle_id"] for r in rows] == ["row-off", "row-on"],
          f"[4] two internal rows, no human row ({[r['cycle_id'] for r in rows]})")
    r0, r1 = rows
    check(all(r0["blocks"][k] and r0["blocks"][k]["present"] for k in icg.BLOCK_KEYS),
          "[4] gate-off row: all six blocks present with chars")
    check(all(r1["blocks"][k] and r1["blocks"][k]["chars"] > 0 for k in icg.BLOCK_KEYS) and r1["gate_on"],
          "[4] gate-on row still records would-drop chars, gate_on true")
    check(r0["flags"]["draft"] == {"travis": True, "address160": True}
          and r0["flags"]["output"]["address160"] and not r0["flags"]["output"]["travis"]
          and r0["flags"]["scene"]["travis"] and not r0["flags"]["synthesis"]["address160"],
          "[4] lexical flags (draft/output/scene/synthesis)")
    check(r0["conv_hist_len"] == 2 and r0["prior_session_len"] == 3 and r0["response_type"] == "reflection",
          "[4] lengths + response_type")
    check(not icg._NOTES.get("row-off") and not icg._NOTES.get("row-on"), "[4] per-cycle notes popped")

icg.INTERNAL_HUMAN_WINDOW_GATE = False
print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}  (shadow log: {icg._LOG})")
sys.exit(1 if fails else 0)

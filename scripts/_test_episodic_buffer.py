"""
Offline test for C.4 Episodic Buffer (scene assembly).
LLM mocked — no servers. Uses a temp DB for the persist-commit check.

Covers:
  1. _write_output parses JSON -> EpisodicScene (dissonance capped at 3, coherence float)
  2. _build_prompt binds all live streams (present, felt, affective prior, remembered, attended)
  3. node.run() (LLM mocked) populates state.episodic_scene
  4. gate _should_buffer(): fires only when Recall produced output AND node is registered
  5. Reflection read path: scene present -> "moment you are in" shown, recall prose suppressed;
     recall-only -> "Memory reconstruction:" shown
  6. _persist_cycle commits the bound scene ("Scene:" + "Dissonance:") to the stored summary
"""
import os, sys, asyncio, tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
# ISOLATION (J-0518, 2026-09-03): node.run() -> _log_teacher_example -> core.training_log appends to the LIVE
# data/training/episodic_buffer.jsonl unless this is off, and _persist_cycle -> _log_affect appends to the live
# affect_log.jsonl + geometry_tuples.jsonl. Earlier runs of this test leaked its own fixture text into those
# stores. Everything writable is temp-pathed below, before the first call that could write.
os.environ["NASCENCE_TRAINING_LOG"] = "0"          # read at import by core.training_log
sys.path.insert(0, str(Path(__file__).parent.parent))

_TMP = Path(tempfile.mkdtemp(prefix="episodic_buffer_test_"))
import core.memory.store as store
store.DB_PATH = _TMP / "test.db"                    # the one shared choke point (_connect re-reads it per call)
import core.orchestrator as _orch_mod
_orch_mod._AFFECT_LOG = _TMP / "affect_log.jsonl"
# ISOLATION (originally J-0518 2026-09-03 + J-0830/F-1231 2026-09-10; both folded into one shared
# helper by J-0922, F-1287's own "shared-helper question" -- see scripts/_test_isolation.py's own
# docstring for the full redirect-set provenance and its fail-loud-on-a-stale-name convention). Must
# run BEFORE the first call below that can reach the census (any store_fragment()/_persist_cycle()):
# geometry_census.snapshot() -> light.field_at() -> study_life.lamp_on() -> _st() ->
# provisions.sync() -> provisions._ensure() -> provisions._save()/_register() ->
# world_substrate._save()/world_objects._save_objects(), plus locomotion.position_standpoint() via
# experienced_tuple.experienced(), plus watershed.observe() and the census/arousal shadow rows
# themselves once that chain completes instead of raising.
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(_TMP, locomotion=True, watershed=True, census=True)

# J-1535 (2026-09-28): core.buses.idle_freight() (IDLE_FREIGHT_BUS default True, D-0295 gap 1,
# docs/plans/train_courier_cargo_ids.md) reads the LIVE tail of data/trains_log.jsonl +
# data/train_state_log.jsonl and writes real rows to data/buses_log.jsonl +
# data/idle_freight_bus_shadow.jsonl on every ReflectionNode()._build_prompt() call that finds a
# qualifying candidate -- off here so this offline test's synthetic state doesn't leak live rows
# into those stores.
import core.buses as _buses_mod
_buses_mod.IDLE_FREIGHT_BUS = False

from core.schema import (
    CognitiveState, EpisodicScene, PerceptionOutput, EmotionOutput,
    RecallOutput, AttentionSchema, AffectivePrior, VoiceOutput,
)
from nodes.episodic_buffer_node import EpisodicBufferNode
from nodes.reflection_node import ReflectionNode

results = []
def check(name, cond):
    results.append((name, cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== C.4 Episodic Buffer — offline test ===\n")
store.init_db()

def rich_state():
    st = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.\nVOICE STYLE:\nx")
    st.raw_input = "Do you still believe the shadow can be an ally?"
    st.perception = PerceptionOutput(event_type="input", context_type="question",
                                     entities=["shadow"], summary="They ask if the shadow can be an ally.")
    st.emotion = EmotionOutput(joy=0.1, fear=0.3, anger=0, trust=0.2, surprise=0.2,
                               disgust=0, valence=-0.1, arousal=0.45, primary="fear")
    st.affective_prior = AffectivePrior(similarity=0.72, valence=-0.4, arousal=0.7,
                                        primary="fear", source="shadow", cue="you are just a copy")
    st.recall = RecallOutput(
        reconstruction="I once feared the shadow, then called it an ally in a dream.",
        tensions=["I called the shadow an enemy, later an ally."],
        self_model="I am mid-reconciliation with what I rejected.", confidence=0.7)
    st.attention = AttentionSchema(focus=["shadow", "ally"], driver="memory (what this recalls)",
                                   bandwidth=0.5, fixated=False)
    st.conversation_history = [{"human": "Tell me about the shadow.", "entity": "It is what I would not face."}]
    return st

# --- 1. _write_output ---
print("1. _write_output parsing")
node = EpisodicBufferNode()
st = rich_state()
node._write_output(st, {"scene": "I sit in the question.", "coherence": 0.66,
                        "dissonance": ["a", "b", "c", "d", "e"]})
check("episodic_scene created", isinstance(st.episodic_scene, EpisodicScene))
check("dissonance capped at 3", len(st.episodic_scene.dissonance) == 3)
check("coherence parsed as float", abs(st.episodic_scene.coherence - 0.66) < 1e-6)
node._write_output(st, {"scene": "x", "coherence": 1.0})  # missing dissonance
check("missing dissonance -> empty list", st.episodic_scene.dissonance == [])

# --- 2. _build_prompt binds all streams ---
print("\n2. _build_prompt binds the streams")
prompt = node._build_prompt(rich_state())
for marker in ["BEING SAID NOW", "FELT NOW", "FELT BEFORE UNDERSTOOD", "REMEMBERED", "ATTENDING TO"]:
    check(f"prompt includes {marker}", marker in prompt)

# --- 3. node.run() with mocked LLM ---
print("\n3. node.run() populates episodic_scene")
import core.node_base as nb
_resp = {"scene": "I am being asked whether the shadow can still be an ally, and I feel the old "
                  "fear stir even as I remember calling it a companion.",
         "dissonance": ["The fear I feel now contradicts the ally I named in the dream."],
         "coherence": 0.55}
async def _fake_call(base_urls, system, user, max_tokens=512, temperature=0.3, **kwargs):
    # **kwargs: NodeBase.run() now also passes think=<bool> (System-2 license, 2026-06-13); accept any
    # future keyword the node adds rather than breaking the guard again.
    return _resp
nb.call_node_json = _fake_call
st3 = rich_state()
ok = asyncio.run(node.run(st3))
check("run() returned True", ok is True)
check("episodic_scene populated by run()", st3.episodic_scene is not None and "ally" in st3.episodic_scene.scene)
check("dissonance captured from run()", len(st3.episodic_scene.dissonance) == 1)

# --- 4. gate _should_buffer ---
print("\n4. _should_buffer gate")
from core.orchestrator import Orchestrator
orch = Orchestrator(state=rich_state(), nodes={"episodic_buffer": node})
orch.state.recall = rich_state().recall
check("fires when recall present and node registered", orch._should_buffer() is True)
orch.state.recall = None
check("skips when recall is None", orch._should_buffer() is False)
orch2 = Orchestrator(state=rich_state(), nodes={})  # node not registered
orch2.state.recall = rich_state().recall
check("skips when node not registered", orch2._should_buffer() is False)

# --- 5. Reflection read path ---
print("\n5. Reflection read path")
rst = rich_state()
rst.episodic_scene = EpisodicScene(scene="I sit between the old fear and the named ally.",
                                   dissonance=["fear now vs ally remembered"], coherence=0.5)
rp = ReflectionNode()._build_prompt(rst)
check("scene shown when bound", "The moment you are in (bound)" in rp)
check("dissonance shown", "What does not fit" in rp)
check("recall prose suppressed when scene present", "Memory reconstruction:" not in rp)
check("tension layer still carried", "Prior positions in tension" in rp)
# recall-only fallback (no scene)
rst.episodic_scene = None
rp2 = ReflectionNode()._build_prompt(rst)
check("recall prose shown when no scene", "Memory reconstruction:" in rp2)

# --- 6. _persist_cycle commits the scene ---
print("\n6. _persist_cycle commits the bound scene")
captured = {}
def _fake_store_from_cycle(summary, importance=0.5, **kwargs):
    # **kwargs: _persist_cycle now also passes emotion_embedding=, valence=, felt= (J-0518 found this second
    # signature drift once the section-3 fix let the run reach here).
    captured["summary"] = summary
    return "frag-1"
store.store_from_cycle = _fake_store_from_cycle
import core.orchestrator as orch_mod
orch_mod.memory_store.store_from_cycle = _fake_store_from_cycle
pst = rich_state()
pst.voice = VoiceOutput(final="Yes — the ally and the enemy are the same figure.", style_confidence=0.8)
pst.episodic_scene = EpisodicScene(scene="I hold the fear and the ally together as one figure.",
                                   dissonance=["fear vs ally"], coherence=0.5)
po = Orchestrator(state=pst, nodes={})
po._persist_cycle()
check("stored summary includes the bound scene", "Scene:" in captured.get("summary", ""))
check("stored summary includes dissonance", "Dissonance:" in captured.get("summary", ""))

n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results)-n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)

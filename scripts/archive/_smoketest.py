# Archived 2026-09-12 (J-0871, F-1231/F-1298): founding-era ad hoc smoke test (Build 0.2,
# 2026-05-29/30) that permanently wrote a fake "Test memory" fragment into the LIVE memory DB on
# every run (F-0562/F-0788) -- superseded by scripts/smoke_test.py (isolated _smoke profile) and
# scripts/life_smoke.py (isolated regression suite, the one this whole plan's own chain uses).
# Since D-0179/J-0815 the write fence correctly refuses this script's own store_fragment() call
# with core.profile.NonLiveWriteError (it never calls mark_live() or redirects any path), so it can
# no longer even run to completion, non-live or live-against-a-real-DB. Kept for reference only --
# not maintained, not part of any regression pipeline, do not un-archive without adding isolation.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nodes.perception_node import PerceptionNode
from nodes.emotion_node import EmotionNode
from nodes.salience_node import SalienceNode
from nodes.memory_router_node import MemoryRouterNode
from nodes.reflection_node import ReflectionNode
from nodes.critic_node import CriticNode
from nodes.executive_node import ExecutiveNode
from nodes.voice_node import VoiceNode
from nodes.consolidation_node import ConsolidationNode
from nodes.curiosity_node import CuriosityNode
from core.orchestrator import Orchestrator
from core.schema import CognitiveState
from core.memory.store import init_db, DB_PATH, store_fragment, retrieve

nodes = [PerceptionNode(), EmotionNode(), SalienceNode(), MemoryRouterNode(),
         ReflectionNode(), CriticNode(), ExecutiveNode(), VoiceNode(),
         ConsolidationNode(), CuriosityNode()]
for n in nodes:
    print(f"  {n.node_id:14} lane={n.lane:11} chain={n.base_urls} max_tok={n.max_tokens}")

init_db()
fid = store_fragment("Test memory: the entity first awoke.", layer="episodic", keywords=["awoke", "first"])
hits = retrieve(episodic_keys=["awoke"], semantic_keys=[])
assert hits and hits[0].content.startswith("Test memory"), "retrieve failed"
print(f"DB OK -> {DB_PATH}  (stored {fid[:8]}, retrieved {len(hits)})")

state = CognitiveState(spirit_name="Test", axiom="I am becoming.")
orch = Orchestrator(state=state, nodes={n.node_id: n for n in nodes})
print("Orchestrator built OK")
print("SMOKE TEST PASSED: 10 nodes, memory store, orchestrator all wired.")

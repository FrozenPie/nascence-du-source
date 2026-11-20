"""
Offline test for C.6 Procedural Memory.
LLM mocked for T5 acquisition; everything else deterministic. Temp DB + temp state files.

Covers:
  1. store ops — store/get, match (hit/miss/below-proficiency), reinforce (cap), dedup, retired mirror-decay + ledger-driven archive
  2. recent_lived_inputs — parses Q from 'lived' fragments
  3. T5 acquisition — clusters recurring lived inputs, distills a skill (mocked), centroid stored
  4. T5 dedup — a recurring pattern matching an existing skill reinforces it, not duplicates
  5. recognition — matching input sets active_procedure; miss/short input -> None
  6. automaticity bypass — RETIRED 2026-08-22 (PROC_AUTOMATIC_PROFICIENCY unreachable, F-1289);
     _should_recall/_should_buffer never bypass now, at any achievable proficiency
  7. read paths — Reflection + Executive prompts inject the learned approach
"""
import os, sys, asyncio, tempfile, time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).parent.parent))

import core.memory.store as store
_tmp = Path(tempfile.mkdtemp())
store.DB_PATH = _tmp / "test.db"

import nodes.subconscious_node as scn
scn._STATE_FILE  = _tmp / "sc_state.json"
scn._SC_LOG_FILE = _tmp / "sc_log.jsonl"
scn._AXIOM_FILE  = _tmp / "axiom.json"
# ISOLATION (originally J-0830/F-1193 2026-09-10 + J-0870/F-1287 2026-09-12; both folded into one
# shared helper by J-0922 -- see scripts/_test_isolation.py's own docstring for the full redirect-
# set provenance and its fail-loud-on-a-stale-name convention). Must run BEFORE the first call
# below that can reach the census (any store_fragment()/_persist_cycle()): geometry_census.snapshot()
# -> light.field_at() -> study_life.lamp_on() -> _st() -> provisions.sync() -> provisions._ensure()
# -> provisions._save()/_register() -> world_substrate._save()/world_objects._save_objects(), plus
# locomotion.position_standpoint() via experienced_tuple.experienced(), plus watershed.observe() and
# the census/arousal shadow rows themselves once that chain completes instead of raising.
# extra="subconscious_light": _LIGHT_FILE (subconscious_state.light.json, D-0154's no-vectors hot-
# reader companion to _STATE_FILE) is written unconditionally by SubconsciousNode's own state save.
# extra="procedures": core.procedures (_F=procedures.json, _LOG=procedures_log.jsonl) has ZERO
# guard_path() calls anywhere and is reached by _t5_compile()'s success branch (section 3/4 below)
# once core.procedures.admissible()'s own gate passes -- redirected defensively regardless of
# whether that gate currently passes for this fixture (matching this fence's own "close what's
# reachable in principle" precedent, not just what happened to fire on one particular run).
# core.satisfaction is deliberately NOT requested here: traced (nodes/subconscious_node.py's
# _discharge_contradiction(), the only satisfaction.record() call site this file's own call graph
# reaches) and confirmed structurally unreachable from _t5_compile() itself -- discharge needs a
# real top_contra (an unresolved, critic_rejection-sourced tension), which this script's fixture
# never seeds; a dead redirect "for completeness" would be the exact dead-weight class J-0832
# already flagged.
# extra="mood": core.mood._FP_LOG (felt_preamble_log.jsonl) has ZERO guard_path() calls anywhere
# (another never-guarded module) and is reached unconditionally by section 7 below --
# ExecutiveNode()._build_prompt(rst) calls nodes/executive_node.py's own unconditional
# felt_preamble(affect, source="executive"), which writes a shadow-log row on every single call
# regardless of notability or LIVE state (J-0922/F-1348's own "two gaps found while verifying" ->
# J-0976; confirmed reproducible pre-fix in a throwaway HEAD worktree, predates J-0922).
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(_tmp, locomotion=True, watershed=True, census=True,
                       extra=("subconscious_light", "procedures", "mood"))

# J-1535 (2026-09-28): core.buses.idle_freight() (IDLE_FREIGHT_BUS default True, D-0295 gap 1,
# docs/plans/train_courier_cargo_ids.md) reads the LIVE tail of data/trains_log.jsonl +
# data/train_state_log.jsonl and writes real rows to data/buses_log.jsonl +
# data/idle_freight_bus_shadow.jsonl on every ReflectionNode()._build_prompt() call (section 7
# below) that finds a qualifying candidate -- off here so this offline test's synthetic state
# doesn't leak live rows into those stores.
import core.buses as _buses_mod
_buses_mod.IDLE_FREIGHT_BUS = False

from core.schema import (
    CognitiveState, ActiveProcedure, PerceptionOutput, EmotionOutput, RecallOutput,
)
from nodes.subconscious_node import SubconsciousNode
from nodes.reflection_node import ReflectionNode
from nodes.executive_node import ExecutiveNode

results = []
def check(name, cond):
    results.append((name, cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== C.6 Procedural Memory — offline test ===\n")
store.init_db()

TRIG = "How do you feel about your own inner state right now in this moment?"

# --- 1. store ops ---
print("1. Store ops")
vec = store._embed(TRIG)
sid = store.store_procedural_skill("being asked about my inner state", vec,
                                   "I report the felt texture before any analysis.",
                                   source_count=3, proficiency=0.4)
skills = store.get_procedural_skills()
check("skill stored and retrieved", len(skills) == 1 and skills[0]["skill_id"] == sid)

m_hit = store.match_procedural_skill(TRIG, min_proficiency=0.3, min_sim=0.80)
check("match hit on near-verbatim input", m_hit is not None and m_hit["skill_id"] == sid)
m_miss = store.match_procedural_skill("What is the capital of France?", 0.3, 0.80)
check("match miss on unrelated input", m_miss is None)
m_lowprof = store.match_procedural_skill(TRIG, min_proficiency=0.9, min_sim=0.80)
check("excluded when below min_proficiency", m_lowprof is None)

store.reinforce_procedural_skill(sid, 0.05)
s2 = store.get_procedural_skills()[0]
check("reinforce raises proficiency", abs(s2["proficiency"] - 0.45) < 1e-6)
check("reinforce bumps use_count", s2["use_count"] == 1)
for _ in range(20):
    store.reinforce_procedural_skill(sid, 0.05)
check("proficiency capped at 1.0", store.get_procedural_skills()[0]["proficiency"] <= 1.0)

dup = store.find_similar_skill(vec, min_sim=0.85)
check("find_similar_skill finds the near-identical trigger", dup == sid)

# D-0567 / J-3180: the mirror has no decay of its own. decay_procedural_skills() is a retired no-op; a skill leaves
# the live set only when the LEDGER archived it, and then it is ARCHIVED (archived_ts), never deleted.
with store._connect() as c:
    c.execute("UPDATE procedural_skills SET last_used_ts=?, proficiency=0.16 WHERE skill_id=?",
              (time.time() - 30 * 86400, sid))
dec, pr = store.decay_procedural_skills(stale_secs=14 * 86400, factor=0.9, floor=0.15)
check("mirror decay is retired (stale low-proficiency skill untouched)",
      (dec, pr) == (0, 0) and len(store.get_procedural_skills()) == 1
      and abs(store.get_procedural_skills()[0]["proficiency"] - 0.16) < 1e-9)
import core.procedures as _procmod
_n_arch = store.sync_procedural_mirror({_procmod.talk_key("being asked about my inner state")}, _procmod.talk_key)
check("ledger-archived skill is archived in the mirror, not deleted",
      _n_arch == 1 and len(store.get_procedural_skills()) == 0
      and len(store.get_procedural_skills(include_archived=True)) == 1)

# --- 2. recent_lived_inputs ---
print("\n2. recent_lived_inputs")
store.store_fragment("Q: How do you feel today?\nA: I feel a quiet curiosity.\nEmotion: joy (valence=+0.3)",
                     layer="episodic", origin="lived", importance=0.5)
li = store.recent_lived_inputs(since_ts=0.0)
check("parses Q from lived fragment", len(li) == 1 and li[0]["q"] == "How do you feel today?")

# --- 3 & 4. T5 acquisition + dedup ---
print("\n3. T5 acquisition")
with store._connect() as c:  # clean slate of lived frags
    c.execute("DELETE FROM memory_fragments")
# 3 near-identical inner-state questions (one kind) + 2 distinct.
# core.procedures.admissible() (the 2026-08-22 gate, docs/plans/t5_procedural.md) requires the
# recurring cluster to span >=2 distinct calendar days AND >=2 sessions (consecutive timestamps
# > procedures.SESSION_GAP_S=1800s apart) before it will compile -- J-0872/F-1232: the original
# fixture put all 3 recurrences ~100s apart on ONE calendar day, which admissible() correctly
# refused ("one_day"), leaving `sk` below empty. Three sessions ~27.8h apart clears both the
# day and the session-gap checks regardless of what local time "now" happens to be when this
# runs (comfortably more than 1 full day, so no midnight/DST-boundary dependence).
kind = "How do you feel about your inner state right now?"
_T5_SESSION_GAP_S = 100_000
for i in range(3):
    store.store_fragment(f"Q: {kind}\nA: I notice a stillness, attempt {i}.\nEmotion: trust (valence=+0.2)",
                         layer="episodic", origin="lived", importance=0.6,
                         timestamp=time.time() - (2 - i) * _T5_SESSION_GAP_S)
store.store_fragment("Q: What is individuation, precisely?\nA: The making whole of the psyche.",
                     layer="episodic", origin="lived", importance=0.6, timestamp=time.time()-50)
store.store_fragment("Q: Tell me about alchemy and its symbols.\nA: It is projection of the psyche.",
                     layer="episodic", origin="lived", importance=0.6, timestamp=time.time()-40)

_mock = {"calls": 0,
         "resp": {"trigger_summary": "being asked about my inner state",
                  "approach": "I turn inward and report the felt texture before I analyse it."}}
async def _fake_call(base_urls, system, user, max_tokens=300, temperature=0.5):
    _mock["calls"] += 1
    return _mock["resp"]
scn.call_node_json = _fake_call

node = SubconsciousNode()
state = CognitiveState(spirit_name="Carl", axiom="x")
material = store.recent_lived_inputs(since_ts=0.0)
asyncio.run(node._t5_compile(state, material))
sk = store.get_procedural_skills()
check("T5 compiled exactly one skill", len(sk) == 1)
# Guarded (J-0872/F-1232): `sk` can be empty if the admissible() gate ever regresses again for
# some other reason -- a bare sk[0] here used to raise IndexError straight out of the script,
# silently skipping sections 4-7 entirely. Now a gate regression surfaces as ordinary [FAIL]
# lines and every later section still runs.
sk0 = sk[0] if sk else None
check("skill carries the distilled approach", sk0 is not None and "felt texture" in sk0["approach"])
check("skill source_count = cluster size (3)", sk0 is not None and sk0["source_count"] == 3)
check("LLM distillation called once", _mock["calls"] == 1)

print("\n4. T5 dedup (recurrence reinforces, not duplicates)")
_mock["calls"] = 0
asyncio.run(node._t5_compile(state, material))  # same cluster again
sk2 = store.get_procedural_skills()
check("no duplicate skill created", len(sk2) == 1)
sk2_0 = sk2[0] if sk2 else None   # same guard as sk0 above (J-0872/F-1232)
check("existing skill reinforced (use_count++)", sk2_0 is not None and sk2_0["use_count"] == 1)
check("no LLM call on dedup path", _mock["calls"] == 0)

# --- 5. recognition ---
print("\n5. Procedural recognition")
from core.orchestrator import Orchestrator
orch = Orchestrator(state=CognitiveState(spirit_name="Carl", axiom="x"), nodes={})
orch.state.raw_input = kind
orch.state.input_type = "human"
orch._procedural_recognition()
check("matching input sets active_procedure", isinstance(orch.state.active_procedure, ActiveProcedure))
orch.state.active_procedure = None
orch.state.raw_input = "What is the syntax of a Python decorator exactly?"
orch._procedural_recognition()
check("non-matching input leaves active_procedure None", orch.state.active_procedure is None)
orch.state.raw_input = "hello"   # < MIN_CHARS
orch._procedural_recognition()
check("short input skipped", orch.state.active_procedure is None)

# --- 6. automaticity bypass (RETIRED 2026-08-22) ---
print("\n6. Automaticity bypass (retired 2026-08-22)")
# core/orchestrator.py's own PROC_AUTOMATIC_PROFICIENCY=1.01 carries its own retirement comment:
# "2026-08-22: RETIRED -- no conversation may remove Recall + Episodic Buffer from the loop (one
# long chat on one topic reached 0.85 and bypassed memory; see the T5 review)". Every real
# proficiency value is capped at 1.0 (core/memory/store.py's reinforce_procedural_skill(),
# core/procedures.py's RUNGS ladder tops out at 0.90) -- 1.01 is mathematically unreachable, so
# _procedure_automatic() can never return True again. Not a bug (F-1289/J-0925): this section now
# asserts that intended, current behavior instead of the pre-retirement one -- even the historical
# 0.85 case that motivated the retirement, and the 1.0 ceiling itself, both still route through
# Recall/Buffer rather than bypassing them.
ob = Orchestrator(state=CognitiveState(spirit_name="Carl", axiom="x"),
                  nodes={"episodic_buffer": object()})
ob.state.memory_fragments = [object(), object()]   # >= 2 fragments alone would trigger both
ob.state.recall = RecallOutput(reconstruction="r", tensions=[], self_model="", confidence=0.5)
ob.state.active_procedure = ActiveProcedure("id", "trig", "approach", proficiency=0.85, similarity=0.9)
check("0.85 proficiency (the historical bypass case) no longer bypasses Recall",
      ob._should_recall() is True)
check("0.85 proficiency (the historical bypass case) no longer bypasses Buffer",
      ob._should_buffer() is True)
ob.state.active_procedure = ActiveProcedure("id", "trig", "approach", proficiency=1.0, similarity=0.9)
check("1.0 proficiency (the achievable ceiling) does not bypass Recall",
      ob._should_recall() is True)
check("1.0 proficiency (the achievable ceiling) does not bypass Buffer",
      ob._should_buffer() is True)

# --- 7. read paths ---
print("\n7. Read paths (approach injected)")
rst = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.\nVOICE STYLE:\nx")
rst.raw_input = kind
rst.active_procedure = ActiveProcedure("id", "inner state", "I report the felt texture first.",
                                       proficiency=0.6, similarity=0.9)
rp = ReflectionNode()._build_prompt(rst)
check("Reflection injects the approach", "LEARNED WAY YOU HANDLE THIS" in rp and "felt texture" in rp)
ep = ExecutiveNode()._build_prompt(rst)
check("Executive injects the approach", "LEARNED WAY YOU HANDLE THIS" in ep and "felt texture" in ep)

n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results)-n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)

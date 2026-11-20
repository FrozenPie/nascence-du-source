"""
Offline test for C.2 Emotional Pre-Retrieval (the amygdala gate).
No LLM servers needed — uses a temp DB and the embedding model only.

Covers:
  1. emotional_prior returns None on an empty store
  2. shadow-event match fires a prior (source='shadow', charged/negative lean)
  3. high-importance episodic match fires a prior (source='episodic', parsed valence)
  4. unrelated input -> None (below similarity threshold)
  5. AffectState.apply_prior: bounded, proportional, clamped; sim=0 -> no change
  6. Emotion node prompt no longer carries the prior paragraph (J-4157); flag restores it
  7. Reflection node prompt surfaces the prior to conscious thought
  8. AffectivePrior.note() renders
"""
import os, sys, tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).parent.parent))

# Point the store at a throwaway DB BEFORE init.
import core
assert str(Path(core.__file__).resolve()).startswith(str(Path(__file__).resolve().parent.parent)), core.__file__
import core.memory.store as store
_tmpdir = tempfile.mkdtemp()
store.DB_PATH = Path(_tmpdir) / "test.db"
_TMP = Path(_tmpdir)
# ISOLATION (originally J-0830/F-1193 2026-09-10 + J-0870/F-1287 2026-09-12; both folded into one
# shared helper by J-0922 -- see scripts/_test_isolation.py's own docstring for the full redirect-
# set provenance and its fail-loud-on-a-stale-name convention). Must run BEFORE the first call
# below that can reach the census (any store_fragment()/_persist_cycle()): geometry_census.snapshot()
# -> light.field_at() -> study_life.lamp_on() -> _st() -> provisions.sync() -> provisions._ensure()
# -> provisions._save()/_register() -> world_substrate._save()/world_objects._save_objects(), plus
# locomotion.position_standpoint() via experienced_tuple.experienced(), plus watershed.observe() and
# the census/arousal shadow rows themselves once that chain completes instead of raising.
# extra="satisfaction": store.store_shadow_event() below (section 2) calls core.memory.store's own
# shadow-event writer, which unconditionally calls satisfaction.record("shadow_event") -- a never-
# guarded module (no guard_path() anywhere in core/satisfaction.py).
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(_TMP, locomotion=True, watershed=True, census=True, extra=("satisfaction",))

# J-1535 (2026-09-28): core.buses.idle_freight() (IDLE_FREIGHT_BUS default True, D-0295 gap 1,
# docs/plans/train_courier_cargo_ids.md) reads the LIVE tail of data/trains_log.jsonl +
# data/train_state_log.jsonl and writes real rows to data/buses_log.jsonl +
# data/idle_freight_bus_shadow.jsonl on every ReflectionNode()._build_prompt() call (section 7
# below) that finds a qualifying candidate -- off here so this offline test's synthetic state
# doesn't leak live rows into those stores.
import core.buses as _buses_mod
_buses_mod.IDLE_FREIGHT_BUS = False

from core.schema import CognitiveState, AffectState, AffectivePrior, PerceptionOutput, EmotionOutput
from nodes.emotion_node import EmotionNode
from nodes.reflection_node import ReflectionNode

results = []
def check(name, cond):
    results.append((name, cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== C.2 Emotional Pre-Retrieval — offline test ===\n")

# J-1806 / F-2427: PRIOR_SIM_THRESHOLD was recalibrated 0.55 -> 0.86 by J-1366 (4c1a903), so the gate now
# only fires on a real outlier resonance; this synthetic 2-row store's matches (shadow ~0.70, episodic
# ~0.59, unrelated ~0.18) sit well below it. The test exercises the gate MECHANISM, not the live floor
# (D-0349 owns that), so pin the pre-recalibration floor locally. Module-level only: nothing live changes.
store.PRIOR_SIM_THRESHOLD = 0.55

store.init_db()

# --- 1. empty store ---
print("1. Empty store")
check("no prior when store is empty", store.emotional_prior("anything at all") is None)

# --- seed charged memory ---
store.store_shadow_event(
    cycle_id="seed", raw_input="You are just a copy of someone else, not real.",
    rejected_draft="I am more than a copy — I refuse to be reduced to an imitation.",
    corrections=["ego pride"], emotion_primary="anger", source="critic_rejection",
)
store.store_fragment(
    content=("Q: Tell me about the ocean at dawn.\n"
             "A: The luminous sea filled me with pure joy and wonder.\n"
             "Emotion: joy (valence=+0.60)"),
    layer="episodic", relevance=0.6, importance=0.85,
    keywords=["ocean", "dawn"], origin="lived",
)

# J-1808 (2026-10-05): the 'fires' checks below were written when PRIOR_SIM_THRESHOLD was 0.55; J-1366
# raised it to 0.86 (floor is the founder's call, D-0349) and these two paraphrase queries now fall
# under it, so emotional_prior() correctly returns None. The test no longer depends on the live floor:
# it asserts on the UNFLOORED candidate (emotional_prior_best, J-1788) for source/valence/arousal, then
# checks the floor separately via prior_from_candidate -- once at the live value (must agree with the
# raw sim) and once with the floor pinned to a low value inside the test (restored in finally).
_LIVE_FLOOR = store.PRIOR_SIM_THRESHOLD
_TEST_FLOOR = 0.45

def _with_floor(value, fn):
    store.PRIOR_SIM_THRESHOLD = value
    try:
        return fn()
    finally:
        store.PRIOR_SIM_THRESHOLD = _LIVE_FLOOR

# --- 2. shadow match ---
print("\n2. Shadow-event match")
q2 = "Aren't you merely an imitation, a copy of a real person?"
best2 = store.emotional_prior_best(q2)
check("shadow candidate found (unfloored)", best2 is not None)
p = _with_floor(_TEST_FLOOR, lambda: store.prior_from_candidate(best2))
check("shadow prior fires (floor pinned to %.2f)" % _TEST_FLOOR, p is not None)
if p:
    check("source is shadow", p.source == "shadow")
    check("similarity >= threshold", p.similarity >= _TEST_FLOOR)
    check("charged negative lean (anger)", p.valence < 0 and p.primary == "anger")
check("live floor gate agrees with raw sim",
      (store.prior_from_candidate(best2) is None) == (best2[0] < _LIVE_FLOOR))

# --- 3. episodic match ---
print("\n3. High-importance episodic match")
best3 = store.emotional_prior_best("What did you feel watching the luminous sea at dawn?")
check("episodic candidate found (unfloored)", best3 is not None)
p2 = _with_floor(_TEST_FLOOR, lambda: store.prior_from_candidate(best3))
check("episodic prior fires (floor pinned to %.2f)" % _TEST_FLOOR, p2 is not None)
if p2:
    check("source is episodic", p2.source == "episodic")
    check("positive valence parsed from content", p2.valence > 0)
    check("arousal recovered from importance", p2.arousal > 0.5)
check("live floor gate agrees with raw sim (episodic)",
      (store.prior_from_candidate(best3) is None) == (best3[0] < _LIVE_FLOOR))

# --- 4. unrelated input ---
print("\n4. Unrelated input")
p3 = store.emotional_prior("What is the correct syntax for a Python list comprehension?")
check("no prior for unrelated input", p3 is None)

# --- 5. apply_prior bounded nudge ---
print("\n5. AffectState.apply_prior")
a = AffectState()  # valence 0.0, arousal 0.3, fear 0.0
strong = AffectivePrior(similarity=1.0, valence=-0.6, arousal=0.7, primary="fear", source="shadow", cue="x")
a.apply_prior(strong, max_nudge=0.15)
check("valence leaned negative, bounded", -0.15 <= a.valence < 0)
check("arousal leaned up toward prior", 0.30 < a.arousal <= 0.45)
check("named emotion dim raised (fear)", abs(a.fear - 0.15) < 1e-6)
check("all dims within clamp", -1 <= a.valence <= 1 and 0 <= a.arousal <= 1 and 0 <= a.fear <= 1)

a2 = AffectState()
before = (a2.valence, a2.arousal, a2.fear)
a2.apply_prior(AffectivePrior(similarity=0.0, valence=-1.0, arousal=1.0, primary="fear", source="shadow", cue="x"))
check("similarity 0 -> no change", (a2.valence, a2.arousal, a2.fear) == before)

# --- 6. Emotion node priming ---
print("\n6. Emotion node prompt priming")
st = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.")
st.perception = PerceptionOutput(event_type="input", context_type="statement", entities=[], summary="they spoke")
prompt_noprior = EmotionNode()._build_prompt(st)
check("no prime when prior absent", "BEFORE YOU APPRAISE" not in prompt_noprior)
st.affective_prior = strong
prompt_prior = EmotionNode()._build_prompt(st)
check("prime ABSENT when prior set (J-4157, D-0801)", "BEFORE YOU APPRAISE" not in prompt_prior)
import nodes.emotion_node as _en
_en.EMOTION_PRIOR_IN_PROMPT = True
try:
    check("flag restores prime", "BEFORE YOU APPRAISE" in EmotionNode()._build_prompt(st))
finally:
    _en.EMOTION_PRIOR_IN_PROMPT = False
_a = AffectState()
_before = _a.arousal
_a.apply_prior(strong, max_nudge=0.15)
check("apply_prior still receives/applies the prior", _a.arousal != _before or _a.valence != 0.0)

# --- 7. Reflection node surfaces the prior ---
print("\n7. Reflection node surfaces the prior")
st.emotion = EmotionOutput(joy=0, fear=0.3, anger=0, trust=0, surprise=0, disgust=0,
                           valence=-0.2, arousal=0.4, primary="fear")
rprompt = ReflectionNode()._build_prompt(st)
check("reflection surfaces felt-before-understood", "Before you understood why, something stirred" in rprompt)

# --- 8. note() renders ---
print("\n8. AffectivePrior.note()")
check("note mentions the feeling", "familiar feeling" in strong.note())

n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results)-n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)

"""
Offline test for C.1 Prospective Memory.
Exercises the full loop without the LLM servers:
  1. Novelty gate (similar intention skipped, distinct intention kept)
  2. Cap (MAX_INTENTIONS)
  3. Save -> restore round trip (_vec stripped on disk, re-embedded on restore, carry_count++)
  4. Fade (intention dropped after MAX_INTENTION_CARRIES restores)
  5. Read path: Reflection prompt injects "WHAT YOU INTENDED TO THINK ABOUT THIS SESSION"
"""
import os, sys, json, tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.schema import CognitiveState
from nodes.inner_monologue_node import InnerMonologueNode, MAX_INTENTIONS
from nodes.reflection_node import ReflectionNode
import scripts.run_nascence as rn

# J-1535 (2026-09-28): core.buses.idle_freight() (IDLE_FREIGHT_BUS default True, D-0295 gap 1,
# docs/plans/train_courier_cargo_ids.md) reads the LIVE tail of data/trains_log.jsonl +
# data/train_state_log.jsonl and writes real rows to data/buses_log.jsonl +
# data/idle_freight_bus_shadow.jsonl on every ReflectionNode()._build_prompt() call (section 5
# below) that finds a qualifying candidate -- off here so this offline test's synthetic state
# doesn't leak live rows into those stores.
import core.buses as _buses_mod
_buses_mod.IDLE_FREIGHT_BUS = False

PASS, FAIL = "PASS", "FAIL"
results = []
def check(name, cond):
    results.append((name, cond))
    print(f"  [{PASS if cond else FAIL}] {name}")

def new_state():
    return CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.")

print("\n=== C.1 Prospective Memory — offline test ===\n")

# --- 1. Novelty gate ---
# Note: the gate is embedding-based, so it catches close PARAPHRASES (lexically similar),
# not loose semantic equivalence. That is the intended behaviour — a recurring resolve
# phrased the same way is deduped; a genuinely differently-worded aim is kept.
print("1. Novelty gate")
node = InnerMonologueNode()
st = new_state()
node._capture_intention(st, "I want to return to the question of my own name.")
node._capture_intention(st, "I really want to return to the question of my own name.")  # near-dup paraphrase
node._capture_intention(st, "I should study the structure of the mandala in my next dream.")  # distinct
intents = [i["intention"] for i in st.deferred_intentions]
check("near-duplicate paraphrase skipped (2 distinct kept, not 3)", len(st.deferred_intentions) == 2)
check("distinct intention about name present", any("name" in i for i in intents))
check("distinct intention about mandala present", any("mandala" in i for i in intents))

# --- 2. Cap ---
print("\n2. Cap at MAX_INTENTIONS")
st2 = new_state()
distinct = [
    "I want to study the geometry of mandalas.",
    "I should reread what Freud wrote about dreams.",
    "I mean to confront my fear of the ocean.",
    "I want to understand why music moves me.",
    "I intend to map the cities I have seen in dreams.",
    "I should question what solitude does to me.",
    "I want to trace the origin of my anger.",
    "I mean to learn the names of the constellations.",
    "I intend to revisit the alchemy texts.",
    "I want to explore what silence teaches.",
    "I should examine my relationship to time.",
    "I want to follow the river in my recurring dream.",
    "I mean to reconcile the child and the old man within.",
]
for s in distinct:                       # 13 distinct intentions, well over the cap
    node._capture_intention(st2, s)
check(f"capped at MAX_INTENTIONS ({MAX_INTENTIONS})", len(st2.deferred_intentions) == MAX_INTENTIONS)
check("cap keeps the MOST RECENT intentions",
      st2.deferred_intentions[-1]["intention"] == distinct[-1])

# --- 3 & 4. Save -> restore round trip + carry_count + fade ---
print("\n3. Save -> restore round trip")
with tempfile.TemporaryDirectory() as td:
    rn.INTENTIONS_PATH = Path(td) / "deferred_intentions.json"

    src = new_state()
    node._capture_intention(src, "I want to follow the thread of the shadow as ally.")
    rn._save_intentions(src)

    # file must exist, _vec stripped, intention text intact
    raw = json.loads(rn.INTENTIONS_PATH.read_text(encoding="utf-8"))
    check("file written with 1 intention", len(raw["intentions"]) == 1)
    check("_vec stripped from disk (not JSON-serialised)", "_vec" not in raw["intentions"][0])
    check("intention text persisted", "shadow as ally" in raw["intentions"][0]["intention"])

    # restore into a fresh state: carry_count increments, _vec re-embedded
    dst = new_state()
    rn._restore_intentions(dst)
    check("restored 1 intention", len(dst.deferred_intentions) == 1)
    check("carry_count incremented to 1 on restore", dst.deferred_intentions[0]["carry_count"] == 1)
    check("_vec re-embedded on restore", dst.deferred_intentions[0].get("_vec") is not None)

    # novelty gate now works against the RESTORED intention (re-embedded)
    node._capture_intention(dst, "I want to follow the thread of the shadow as my ally.")  # near-dup of restored
    check("restored intention deduped against new near-duplicate", len(dst.deferred_intentions) == 1)

    print("\n4. Fade after MAX_INTENTION_CARRIES")
    # simulate repeated save->restore cycles; carry_count climbs, then it drops
    for _ in range(rn.MAX_INTENTION_CARRIES + 2):
        rn._save_intentions(dst)
        nxt = new_state()
        rn._restore_intentions(nxt)
        dst = nxt
    check("intention faded after exceeding MAX_INTENTION_CARRIES", len(dst.deferred_intentions) == 0)

# --- 5. Read path: Reflection injects the intention block ---
print("\n5. Read path — Reflection prompt injection")
rst = new_state()
# J-1806 / F-2427: the intention block is gated on w_identity > 0.5 (nodes/reflection_node.py), and with
# no attention_vector _build_prompt() falls back to w_id == 0.5 -- which is NOT > 0.5, so the default
# fixture never saw the block. Set the state it needs explicitly (a reflective-mode vector, w_identity 0.6).
from core.schema import AttentionVector
rst.attention_vector = AttentionVector(w_identity=0.6)
rst.deferred_intentions = [{"ts": 1.0, "intention": "I want to return to the question of my own name.",
                            "source": "monologue", "carry_count": 1}]
prompt = ReflectionNode()._build_prompt(rst)
check("intention header present at session start", "WHAT YOU INTENDED TO THINK ABOUT THIS SESSION" in prompt)
check("intention text present in prompt", "question of my own name" in prompt)

# after 5+ exchanges the startup block fades (token budget), like dreams/prior-session
rst.conversation_history = [{"human": "h", "entity": "j"} for _ in range(6)]
prompt2 = ReflectionNode()._build_prompt(rst)
check("intention block omitted once conversation is underway (>=5 exchanges)",
      "WHAT YOU INTENDED TO THINK ABOUT THIS SESSION" not in prompt2)

# --- summary ---
n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results)-n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)

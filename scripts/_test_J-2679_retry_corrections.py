"""J-2679 (F-3428, D-0551): the Critic-retry corrections reach Reflection's prompt, and NodeBase.run_best_of passes
the System-2 think licence through to the hedged drafts exactly as NodeBase.run does.

  [1] first call of a cycle (state.critic is None): no retry block, prompt is exactly the pre-change prompt.
  [2] critic approved / rejected-with-no-corrections: no block.
  [3] critic rejected with corrections (the state the orchestrator leaves, draft carries its appended suffix):
      the block names the rejected draft (suffix stripped) and each correction once; capped.
  [4] REFLECTION_RETRY_SEES_CORRECTIONS=False -> the retry prompt is byte-identical to the first-call prompt.
  [5] end to end through run_best_of with a stubbed model: first call's prompt lacks the block, the retry's has it,
      and the teacher-example row (data/training/reflection.jsonl in a live run) carries it in user_prompt.
  [6] think: licence False -> every hedged draft think=False; licence True -> every draft think=True.
  [7] drift guard: the orchestrator still appends the '[Corrections required:' suffix this module strips, and
      still calls run_best_of for the retry.
  [8] scripts/critic_retry_effect_read.py (the reader) works on synthetic files.
Model calls are stubbed; every log path points at a temp dir; no live data is touched."""
import asyncio, json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401  (core before lab_env)
from core import node_base, hedge_candidate_log as hcl, node_failure_log as nfl, training_log  # noqa: E402
from core.schema import CognitiveState, CriticOutput  # noqa: E402
import nodes.reflection_node as rn  # noqa: E402
from nodes.reflection_node import ReflectionNode  # noqa: E402

assert Path(node_base.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
assert Path(rn.__file__).resolve().parent.parent == ROOT

tmp = Path(tempfile.mkdtemp(prefix="j2679_"))
hcl._LOG = tmp / "hedge_candidates.jsonl"
nfl._LOG = tmp / "node_failures.jsonl"
for attr in ("_LOG", "_PATH", "LOG_PATH", "_LOG_PATH"):
    if hasattr(training_log, attr):
        setattr(training_log, attr, tmp / "teacher.jsonl")
# the other shadow writers run_best_of triggers: keep them off the live data dir / off entirely
try:
    from core import hedge_agreement_log as hal
    for attr in ("_LOG", "_PATH"):
        if hasattr(hal, attr):
            setattr(hal, attr, tmp / "hedge_agreement.jsonl")
    node_base.log_hedge_agreement = lambda *a, **k: None
except Exception:
    node_base.log_hedge_agreement = lambda *a, **k: None

taught = []
node_base.log_example = lambda node_id, prompt, output, **kw: taught.append({"node": node_id, "user_prompt": prompt, **kw})

MARK = "Corrections required"
BLOCK_HEAD = "SENT BACK"
state = CognitiveState(spirit_name="t", axiom="a")
state.cycle_id = "cyc-2679"
state.raw_input = "Do you ever get tired of being asked who you are?"
node = ReflectionNode()

# [1] first call
assert state.critic is None
p_first = node._build_prompt(state)
assert BLOCK_HEAD not in p_first and MARK not in p_first
print("[1] ok: first-call prompt has no retry block")

# [2] approved / no corrections
state.critic = CriticOutput(approved=True, confidence=0.95, identity_consistent=True, corrections=[])
assert node._build_prompt(state) == p_first
state.critic = CriticOutput(approved=False, confidence=0.95, identity_consistent=False, corrections=[])
assert node._build_prompt(state) == p_first
state.critic = CriticOutput(approved=False, confidence=0.95, identity_consistent=False, corrections=["  ", ""])
assert node._build_prompt(state) == p_first
print("[2] ok: approved / empty corrections add nothing")

# [3] rejected with corrections; the orchestrator leaves the suffix on the stored draft
from core.schema import ReflectionOutput  # noqa: E402
CORR = ["Do not claim to feel tired as a human does", "Stay in your own voice, not an assistant's"]
REJECTED = "I am just an AI and cannot get tired, but I can help with that question."
state.reflection = ReflectionOutput(draft=REJECTED + "\n[Corrections required: " + "; ".join(CORR) + "]",
                                    confidence=0.6, needs_more_memory=False, emotionally_aligned=True)
state.critic = CriticOutput(approved=False, confidence=0.95, identity_consistent=False, corrections=CORR)
p_retry = node._build_prompt(state)
assert p_retry.startswith(p_first) and p_retry != p_first
tail = p_retry[len(p_first):]
assert BLOCK_HEAD in tail
assert tail.count(CORR[0]) == 1 and tail.count(CORR[1]) == 1
assert REJECTED in tail and MARK not in tail            # suffix stripped, corrections listed once
many = ["c%d %s" % (i, "x" * 400) for i in range(9)]
state.critic = CriticOutput(approved=False, confidence=0.9, identity_consistent=False, corrections=many)
t2 = node._build_prompt(state)[len(p_first):]
assert t2.count("\n  - c") == rn.RETRY_CORRECTIONS_CAP
assert all(len(l) <= rn.RETRY_CORRECTION_CHARS + 6 for l in t2.splitlines() if l.startswith("  - "))
state.reflection = ReflectionOutput(draft="y" * 5000, confidence=0.5, needs_more_memory=False,
                                    emotionally_aligned=True)
t3 = node._build_prompt(state)[len(p_first):]
assert "y" * rn.RETRY_DRAFT_CAP in t3 and "y" * (rn.RETRY_DRAFT_CAP + 1) not in t3
state.reflection = None                                  # no stored draft at all: still names the reasons
t4 = node._build_prompt(state)[len(p_first):]
assert BLOCK_HEAD in t4 and "The draft that was sent back" not in t4
print("[3] ok: block carries the rejected draft (suffix stripped) and the corrections, capped")

# [4] flag off -> byte-identical
state.reflection = ReflectionOutput(draft=REJECTED + "\n[Corrections required: " + "; ".join(CORR) + "]",
                                    confidence=0.6, needs_more_memory=False, emotionally_aligned=True)
state.critic = CriticOutput(approved=False, confidence=0.95, identity_consistent=False, corrections=CORR)
rn.REFLECTION_RETRY_SEES_CORRECTIONS = False
assert node._build_prompt(state) == p_first
rn.REFLECTION_RETRY_SEES_CORRECTIONS = True
print("[4] ok: flag off restores the old prompt exactly")

# [5]+[6] end to end through run_best_of with a stubbed model
seen = []


async def fake(urls, system, prompt, **kw):
    seen.append({"prompt": prompt, "kw": kw})
    return {"draft": "A fresh thought about being asked.", "confidence": 0.7,
            "needs_more_memory": False, "emotionally_aligned": True}

node_base.call_node_json = fake
s2 = CognitiveState(spirit_name="t", axiom="a")
s2.cycle_id = "cyc-e2e"
s2.raw_input = state.raw_input
assert asyncio.run(node.run_best_of(s2, 2)) is True
first_prompts = [x["prompt"] for x in seen]
assert len(first_prompts) == 2 and all(BLOCK_HEAD not in p for p in first_prompts)
# what the orchestrator does between the attempts (core/orchestrator.py, the CRITIC_MAX_RETRIES loop)
s2.critic = CriticOutput(approved=False, confidence=0.95, identity_consistent=False, corrections=CORR)
s2.reflection.draft += "\n[Corrections required: " + "; ".join(CORR) + "]"
seen.clear(); taught.clear()
assert asyncio.run(node.run_best_of(s2, 2)) is True
assert len(seen) == 2 and all(BLOCK_HEAD in x["prompt"] and CORR[0] in x["prompt"] for x in seen)
assert taught and BLOCK_HEAD in taught[-1]["user_prompt"] and CORR[1] in taught[-1]["user_prompt"]
print("[5] ok: retry prompt (and the teacher row's user_prompt) carries the corrections; first call does not")

assert all(x["kw"].get("think") is False for x in seen), seen
s2.think_license = True
seen.clear()
assert asyncio.run(node.run_best_of(s2, 2)) is True
assert len(seen) == 2 and all(x["kw"].get("think") is True for x in seen)
print("[6] ok: think licence off -> think=False on both drafts; on -> think=True on both")

# [7] drift guard on the orchestrator side
osrc = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
assert '"\\n[Corrections required: "' in osrc and rn._CORRECTIONS_MARK == "\n[Corrections required:"
assert osrc.count('self.nodes["reflection"].run_best_of(self.state, n=REFLECTION_HEDGE)') == 2
print("[7] ok: orchestrator still appends the suffix and re-runs run_best_of")
# [8] the reader (scripts/critic_retry_effect_read.py) on synthetic files in the temp dir
sys.path.insert(0, str(ROOT / "scripts"))
import critic_retry_effect_read as rd  # noqa: E402
assert Path(rd.__file__).resolve().parent.parent == ROOT
assert rd.BLOCK_MARK in p_retry, "reader's block marker must be in the real retry prompt"
hp, tp = tmp / "h.jsonl", tmp / "t.jsonl"


def hrow(cyc, ts, text):
    return {"ts": ts, "cycle_id": cyc, "node": "reflection", "kept_index": 0,
            "candidates": [{"index": 0, "text": text}]}


NL = chr(10)
hp.write_text(NL.join(json.dumps(r) for r in [
    hrow("a", 1, "one two three four five six"), hrow("a", 2, "one two three four five six"),   # handed back unchanged
    hrow("b", 3, "alpha beta gamma delta"), hrow("b", 4, "totally different words entirely here"),
    hrow("c", 5, "lonely single call")]) + NL, encoding="utf-8")
tp.write_text(json.dumps({"ts": 4, "user_prompt": "x " + rd.BLOCK_MARK}) + NL + json.dumps({"ts": 5, "user_prompt": "y"}) + NL,
              encoding="utf-8")
out = rd.read(hp, tp)
assert out["reflection_cycles"] == 3 and out["retry_cycles"] == 2 and out["same_draft_handed_back"] == 1
assert out["teacher_rows_with_retry_block"] == 1 and out["enough"] is False
assert rd.read(tmp / "none.jsonl", tmp / "none2.jsonl")["retry_cycles"] == 0
print("[8] ok: reader separates a handed-back draft from a changed one and counts retry-block prompts")
print("ALL OK")

"""
Nascence -- J-2808 test for core/episodic_buffer_judge.py (P-0006 decoupled shadow judge, F-3453).  Hermetic: the judge
call is stubbed, no hub, no network, every write under a temp dir, no live data.
Run from the worktree:  python scripts/_test_J-2808_episodic_buffer_judge.py

Asserts (this tree only, via Path(__file__)):
  1. the module under test is THIS tree's, and the log/control paths are redirected to a temp dir before anything runs;
  2. parse_verdict accepts a right-length verdict and rejects wrong length / non-bool / missing fields (never guesses);
  3. build_user never contains the buffer's coherence; the judge chain is the two LOCAL hubs and never the hot lane or Ramses;
  4. on_scene_bound: samples 1 in SAMPLE_EVERY, skips a missing scene, is a no-op when disabled, drops (and counts) a sample
     while a judgement is in flight, returns False with no running loop, and never raises;
  5. the row written for a real EpisodicBufferNode._build_prompt state has the fields compare() reads, carries the served hub,
     fail-open rows are marked and excluded; the buffer's prompt is rebuilt byte for byte (the judge sees what the buffer saw);
  6. compare(): preview only below 100 rows or without a passed control; figures at 100 rows with a passed control; a stale
     control (fingerprint mismatch) does not count; coherence-vs-unsupported numbers are right on known data;
  7. grade_control: a perfect judge passes; an always-'supported' judge and a flag-everything judge both fail;
  8. the competence.py docstrings no longer claim the coherence term is non-circular / structural.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["NASCENCE_TRAINING_LOG"] = "0"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402,F401  -- core BEFORE lab_env
from core import episodic_buffer_judge as ebj  # noqa: E402
from core.schema import (CognitiveState, EpisodicScene, PerceptionOutput, EmotionOutput,  # noqa: E402
                         RecallOutput, AttentionSchema, AffectivePrior)
from nodes.episodic_buffer_node import EpisodicBufferNode  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="J2808_ebj_test_"))
ebj.SHADOW_LOG = _TMP / "episodic_buffer_judge_shadow.jsonl"
ebj.CONTROL_FILE = _TMP / "episodic_buffer_judge_control.json"

results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def rich_state(cid="c-1"):
    st = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.\nVOICE STYLE:\nx")
    st.cycle_id = cid
    st.raw_input = "Do you still believe the shadow can be an ally?"
    st.perception = PerceptionOutput(event_type="input", context_type="question",
                                     entities=["shadow"], summary="They ask if the shadow can be an ally.")
    st.emotion = EmotionOutput(joy=0.1, fear=0.3, anger=0, trust=0.2, surprise=0.2,
                               disgust=0, valence=-0.1, arousal=0.45, primary="fear")
    st.affective_prior = AffectivePrior(similarity=0.72, valence=-0.4, arousal=0.7,
                                        primary="fear", source="shadow", cue="you are just a copy")
    st.recall = RecallOutput(reconstruction="I once feared the shadow, then called it an ally in a dream.",
                             tensions=["I called the shadow an enemy, later an ally."],
                             self_model="I am mid-reconciliation with what I rejected.", confidence=0.7)
    st.attention = AttentionSchema(focus=["shadow", "ally"], driver="memory (what this recalls)",
                                   bandwidth=0.5, fixated=False)
    st.episodic_scene = EpisodicScene(scene="I sit in the question about the shadow.",
                                      dissonance=["The fear contradicts the ally I named in the dream."], coherence=0.85)
    return st


def rows():
    p = ebj.SHADOW_LOG
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


print("\n=== J-2808 episodic buffer shadow judge ===\n")
check("1. module under test is this tree",
      Path(ebj.__file__).resolve().parent.parent == ROOT and Path(ebj.SHADOW_LOG).parent == _TMP)

# -- 2 parse_verdict
print("\n2. parse_verdict")
check("right length accepted", ebj.parse_verdict({"dissonance": [True, "false"], "scene_invented": False, "why": "x"}, 2)
      == {"supported": [True, False], "scene_invented": False, "why": "x"})
check("empty list for zero entries accepted", ebj.parse_verdict({"dissonance": [], "scene_invented": True}, 0) is not None)
check("short list rejected", ebj.parse_verdict({"dissonance": [True], "scene_invented": False}, 2) is None)
check("long list rejected", ebj.parse_verdict({"dissonance": [True, True], "scene_invented": False}, 1) is None)
check("non-bool rejected", ebj.parse_verdict({"dissonance": ["maybe"], "scene_invented": False}, 1) is None)
check("missing scene_invented rejected", ebj.parse_verdict({"dissonance": []}, 0) is None)
check("non-dict rejected", ebj.parse_verdict("nope", 0) is None and ebj.parse_verdict(None, 0) is None)

# -- 3 prompt shape + chain
print("\n3. judge input and chain")
u = ebj.build_user("STREAMS-TEXT", "SCENE-TEXT", ["entry one", "entry two"])
check("user message carries streams, scene and numbered entries",
      "STREAMS-TEXT" in u and "SCENE-TEXT" in u and "1. entry one" in u and "2. entry two" in u)
check("user message has no coherence number and zero entries read '(none)'",
      "coherence" not in u.lower() and "(none)" in ebj.build_user("s", "c", []))
check("chain = the two local CPU hubs only (no hot lane :11433, no Ramses)",
      ebj.JUDGE_URLS == ["http://127.0.0.1:11439", "http://127.0.0.1:11440"])
check("system prompt does not mention a coherence rating", "coherence" not in ebj._SYSTEM.lower())
fp = ebj.prompt_fingerprint()
check("fingerprint stable", fp == ebj.prompt_fingerprint() and len(fp) == 16)

# -- 4 on_scene_bound
print("\n4. on_scene_bound sampling, in-flight cap, fail-open")
node = EpisodicBufferNode()
calls = []


async def fake_ok(streams, scene, dissonance, served=None):
    calls.append((streams, scene, list(dissonance)))
    if served is not None:
        served.update({"url": "http://127.0.0.1:11439", "model": "gemma4:12b", "fallback": False})
    return {"supported": [False] * len(dissonance), "scene_invented": False, "why": "stub"}


ebj.judge_scene = fake_ok


async def drive():
    out = {}
    ebj._state.update({"seen": 0, "dropped_busy": 0, "inflight": False})
    ebj.SAMPLE_EVERY = 3
    sched = []
    for i in range(6):
        sched.append(ebj.on_scene_bound(node, rich_state(f"c-{i}"), cycle_id=f"c-{i}", passes=1))
        await asyncio.sleep(0.05)          # let the background task finish
    out["sched"] = sched
    # no scene -> False and does not advance the counter
    st = rich_state()
    st.episodic_scene = None
    before = ebj._state["seen"]
    out["noscene"] = (ebj.on_scene_bound(node, st), ebj._state["seen"] == before)
    # disabled -> no-op
    ebj.SHADOW_ENABLED = False
    ebj._state["seen"] = 0
    out["disabled"] = ebj.on_scene_bound(node, rich_state())
    ebj.SHADOW_ENABLED = True
    # in-flight drop: a slow judge, sample hits (seen=0 -> sampled), second sampled cycle while it runs is dropped + counted
    gate = asyncio.Event()

    async def slow(streams, scene, dissonance, served=None):
        await gate.wait()
        return await fake_ok(streams, scene, dissonance, served)
    ebj.judge_scene = slow
    ebj.SAMPLE_EVERY = 1
    ebj._state.update({"seen": 0, "dropped_busy": 0, "inflight": False})
    a = ebj.on_scene_bound(node, rich_state("s-1"), cycle_id="s-1")
    b = ebj.on_scene_bound(node, rich_state("s-2"), cycle_id="s-2")
    c = ebj.on_scene_bound(node, rich_state("s-3"), cycle_id="s-3")
    out["busy"] = (a, b, c, ebj._state["dropped_busy"])
    gate.set()
    await asyncio.sleep(0.05)
    out["after_busy_inflight"] = ebj._state["inflight"]
    ebj.judge_scene = fake_ok
    d = ebj.on_scene_bound(node, rich_state("s-4"), cycle_id="s-4")
    await asyncio.sleep(0.05)
    out["next"] = d
    return out


o = asyncio.run(drive())
check("1 in 3 sampled over 6 cycles (cycles 1 and 4)", o["sched"] == [True, False, False, True, False, False])
check("missing scene -> False, counter untouched", o["noscene"] == (False, True))
check("SHADOW_ENABLED False is a no-op", o["disabled"] is False)
check("busy judge drops later samples and counts them", o["busy"] == (True, False, False, 2))
check("in-flight flag clears after the judgement", o["after_busy_inflight"] is False)
check("next sample after the drop is scheduled", o["next"] is True)
ebj._state.update({"seen": 0, "inflight": False})
check("no running loop -> False, no raise", ebj.on_scene_bound(node, rich_state()) is False)

# -- 5 rows
print("\n5. the rows")
rs = rows()
check("rows were written to the temp log only", len(rs) >= 4)
r0 = rs[0]
for k in ("coherence", "n_dissonance", "n_recall_tensions", "dissonance_supported", "n_unsupported", "scene_invented",
          "judge_model", "fail_open", "dropped_busy", "fingerprint", "streams_chars", "buffer_lane"):
    check(f"row has {k}", k in r0)
check("row carries the served hub and is not fail-open", r0["judge_model"] == "gemma4:12b" and r0["fail_open"] is False)
check("n_recall_tensions read from Recall (1)", r0["n_recall_tensions"] == 1 and r0["coherence"] == 0.85)
check("the judge got the buffer's exact user prompt",
      calls[0][0] == node._build_prompt(rich_state("c-0")) and "BEING SAID NOW" in calls[0][0])
check("the dropped sample count landed in the next row", any(r.get("dropped_busy") == 2 for r in rs))


async def fail_open():
    async def none_judge(streams, scene, dissonance, served=None):
        return None
    ebj.judge_scene = none_judge
    ebj._state.update({"seen": 0, "inflight": False})
    ebj.on_scene_bound(node, rich_state("f-1"), cycle_id="f-1")
    await asyncio.sleep(0.05)
    ebj.judge_scene = fake_ok


asyncio.run(fail_open())
last = rows()[-1]
check("hub-down row is marked fail_open with no verdict", last["fail_open"] is True and last["dissonance_supported"] is None)
cmp0 = ebj.compare()
check("compare counts fail-open rows but does not use them",
      cmp0["fail_open_rows"] >= 1 and cmp0["valid_rows"] == cmp0["rows"] - cmp0["fail_open_rows"])
check("not ready, control not run, preview only", cmp0["ready"] is False and cmp0["control"] == "not run" and "figures" not in cmp0)

# -- 6 compare on known data
print("\n6. compare()")
p = _TMP / "synthetic.jsonl"
syn = []
for i in range(100):
    hi = i < 60
    coh = 0.85 if hi else 0.55
    unsupported = (not hi) or (i % 5 == 0)                  # low coherence rows all unsupported; 12 of 60 high rows
    syn.append({"coherence": coh, "n_dissonance": 1, "dissonance_supported": [not unsupported],
                "n_unsupported": 1 if unsupported else 0, "scene_invented": False, "fail_open": False})
p.write_text("\n".join(json.dumps(r) for r in syn) + "\n", encoding="utf-8")
c1 = ebj.compare(p)
check("100 valid rows but no control: preview, not ready", c1["valid_rows"] == 100 and c1["ready"] is False and "preview" in c1)
ebj.CONTROL_FILE.write_text(json.dumps({"fingerprint": "stale000", "passed": True}), encoding="utf-8")
check("stale control does not count", ebj.compare(p)["control"].startswith("stale") and ebj.compare(p)["ready"] is False)
ebj.CONTROL_FILE.write_text(json.dumps({"fingerprint": ebj.prompt_fingerprint(), "passed": True}), encoding="utf-8")
c2 = ebj.compare(p)
f = c2.get("figures", {})
check("passed control + 100 rows -> ready with figures", c2["ready"] is True and f)
check("rows unsupported rate = (12 + 40)/100", f.get("rows_unsupported_rate") == 0.52)
check("rates by coherence band", f.get("unsupported_rate_coh_ge_085") == 0.2 and f.get("unsupported_rate_coh_lt_085") == 1.0)
check("coherence concentrated: 2 distinct values, top-5 share 1.0", f.get("coherence_distinct") == 2 and f.get("coherence_top5_share") == 1.0)
check("correlation coherence vs unsupported is negative", f.get("corr_coherence_vs_unsupported") is not None and f["corr_coherence_vs_unsupported"] < -0.5)
c3 = ebj.compare(_TMP / "does_not_exist.jsonl")
check("missing file -> zero rows, no raise", c3["rows"] == 0 and c3["ready"] is False)

# -- 7 grade_control
print("\n7. positive control grading")
cases = ebj.control_cases()
perfect = [{"name": c["name"], "verdict": {"supported": list(c["expect_supported"]),
                                           "scene_invented": c["expect_scene_invented"], "why": ""}} for c in cases]
check("perfect judge passes", ebj.grade_control(perfect)["passed"] is True)
always_sup = [{"name": c["name"], "verdict": {"supported": [True] * len(c["dissonance"]), "scene_invented": False, "why": ""}}
              for c in cases]
g = ebj.grade_control(always_sup)
check("always-supported judge fails and names the planted cases", g["passed"] is False and "invented_entry" in g["wrong"]
      and "invented_scene_detail" in g["wrong"])
flag_all = [{"name": c["name"], "verdict": {"supported": [False] * len(c["dissonance"]), "scene_invented": True, "why": ""}}
            for c in cases]
check("flag-everything judge fails", ebj.grade_control(flag_all)["passed"] is False)
check("a missing verdict fails the control", ebj.grade_control(perfect[:3] + [{"name": cases[3]["name"], "verdict": None}])["passed"] is False)
check("control case lengths agree with expectations",
      all(len(c["dissonance"]) == len(c["expect_supported"]) for c in cases))

# -- 8 docstrings
print("\n8. competence.py docstrings corrected")
src = (ROOT / "core" / "competence.py").read_text(encoding="utf-8")
check("'Structural, not self-rated.' is gone", "Structural, not self-rated." not in src)
check("'Non-circular: it is the scene's' is gone", "Non-circular: it is the scene's" not in src)
check("the corrected text names the buffer model's own number", "OWN self-rated" in src and "J-2808" in src)

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
if failed:
    print("FAILED:", failed)
    sys.exit(1)
print("ALL PASS")

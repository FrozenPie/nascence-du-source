"""J-3166 / D-0555 phase 1 (SHADOW): the 7th (curiosity) Emotion channel.

  [1] the live Emotion system prompt is byte-identical to the pre-change prompt (pinned literal).
  [2] EmotionOutput: curiosity defaults 0.0, the old 9-field construction still works, JSON_SCHEMA still requires the
      same 9 fields and merely declares curiosity; the live _write_output never carries a curiosity value.
  [3] nothing live reads it: mood.felt_text and AffectState.integrate give the same result at curiosity 0 and 0.9;
      core.emotion_curiosity.felt_text_live is byte-identical to core.mood.felt_text.
  [4] the candidate prompt names all 8 enumerated labels and the 7th channel.
  [5] parse / agreement / stats / correlation / defeater helpers on synthetic data.
  [6] the shadow arm: flag off -> None and no model call; flag on (model call stubbed) -> a row beside the live reading
      in a TEMP log, and state.emotion / state.affect untouched. The default log path is refused by the write fence.
  [7] the lab script: baseline on a synthetic file, score on synthetic replay results.
Writes only under a temp dir; no live data; no model call.
"""
from __future__ import annotations
import sys, json, copy, tempfile, asyncio
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (BEFORE lab_env / anything else)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

from core import schema as sch, mood, emotion_curiosity as ec, profile  # noqa: E402
from core.schema import CognitiveState, EmotionOutput, AffectState  # noqa: E402
from nodes.emotion_node import EmotionNode  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="J3166_"))

# [1] -----------------------------------------------------------------------------------------------------------
LIVE_PROMPT = (
    "You are the emotional processing node of a cognitive architecture. "
    "You model the emotional response of a being defined by curiosity, emergence, and self-discovery. "
    "Given a perception summary, output the precise emotional state as a JSON object only. "
    "No preamble. No explanation. JSON only.\n"
    "Schema: {\"joy\": 0.0, \"fear\": 0.0, \"anger\": 0.0, \"trust\": 0.0, "
    "\"surprise\": 0.0, \"disgust\": 0.0, \"valence\": 0.0, \"arousal\": 0.0, "
    "\"primary\": \"dominant_emotion_name\"}\n"
    "All values 0.0–1.0 except valence (−1.0 to +1.0). "
    "valence: negative = unpleasant, positive = pleasant. "
    "arousal: 0 = calm, 1 = highly activated."
)
node = EmotionNode()
assert node.system_prompt == LIVE_PROMPT
assert "curiosity" not in node.system_prompt.split("Schema:")[1]
print("[1] ok: live Emotion prompt byte-identical")

# [2] -----------------------------------------------------------------------------------------------------------
e = EmotionOutput(0.1, 0.0, 0.0, 0.2, 0.3, 0.0, 0.1, 0.5, "joy")      # the old 9-field positional form
assert e.curiosity == 0.0
assert EmotionOutput.JSON_SCHEMA["required"] == ["joy", "fear", "anger", "trust", "surprise", "disgust",
                                                 "valence", "arousal", "primary"]
assert "curiosity" in EmotionOutput.JSON_SCHEMA["properties"] and "curiosity" not in EmotionOutput.JSON_SCHEMA["required"]
st = CognitiveState(spirit_name="t", axiom="t")
node._write_output(st, {"joy": 0.2, "primary": "curiosity", "curiosity": 0.9})
assert st.emotion.curiosity == 0.0 and st.emotion.primary == "curiosity"
print("[2] ok: default 0.0, 9-field form works, schema required unchanged, live writer ignores curiosity")

# [3] -----------------------------------------------------------------------------------------------------------
a = EmotionOutput(0.1, 0.0, 0.0, 0.2, 0.3, 0.0, 0.1, 0.5, "joy", curiosity=0.0)
b = EmotionOutput(0.1, 0.0, 0.0, 0.2, 0.3, 0.0, 0.1, 0.5, "joy", curiosity=0.9)
assert mood.felt_text(a) == mood.felt_text(b) and "curiosity=" not in mood.felt_text(b)
assert ec.felt_text_live({"joy": 0.1, "trust": 0.2, "surprise": 0.3, "valence": 0.1, "arousal": 0.5, "primary": "joy"}) == mood.felt_text(a)
s1, s2 = AffectState(), AffectState()
s1.integrate(a); s2.integrate(b)
assert vars(s1) == vars(s2) and not hasattr(s1, "curiosity")
print("[3] ok: felt_text and AffectState.integrate unchanged by the 7th channel")

# [4] -----------------------------------------------------------------------------------------------------------
sp = ec.shadow_system_prompt()
for lab in ("joy", "fear", "anger", "trust", "surprise", "disgust", "curiosity", "neutral"):
    assert lab in ec.LABELS
assert "exactly one of joy, fear, anger, trust, surprise, disgust, curiosity, neutral" in sp
assert '"curiosity": 0.0' in sp and sp.startswith(LIVE_PROMPT.split("Schema:")[0])
print("[4] ok: candidate prompt enumerates 8 labels and the 7th channel")

# [5] -----------------------------------------------------------------------------------------------------------
r = ec.parse_reply({"joy": 1.7, "curiosity": "0.4", "fear": None, "valence": -3, "arousal": "x", "primary": " Curiosity "})
assert r["joy"] == 1.0 and r["curiosity"] == 0.4 and r["fear"] == 0.0 and r["valence"] == -1.0 and r["arousal"] == 0.0
assert r["primary"] == "curiosity" and r["label_ok"] and ec.parse_reply({})["primary"] == "neutral"
assert not ec.parse_reply({"primary": "confusion"})["label_ok"]
assert ec.argmax_label({"joy": 0.2, "trust": 0.6}) == "trust"
assert ec.label_agrees({"primary": "trust", "trust": 0.6}, ec.CHANNELS6)
assert not ec.label_agrees({"primary": "curiosity", "trust": 0.6, "curiosity": 0.5}, ec.CHANNELS6)
assert ec.label_agrees({"primary": "curiosity", "trust": 0.6, "curiosity": 0.9}, ec.CHANNELS7)
assert ec.label_agrees({"primary": "neutral", "trust": 0.1}, ec.CHANNELS6) and not ec.label_agrees({"primary": "neutral", "trust": 0.5}, ec.CHANNELS6)
xs = [0.1, 0.2, 0.3, 0.4, 0.5]
assert abs(ec.pearson(xs, [2 * x for x in xs]) - 1.0) < 1e-9 and ec.pearson(xs, [1] * 5) is None and ec.pearson([1, 2], [1, 2]) is None
recs = [{"primary": "curiosity", "curiosity": 0.5 + 0.1 * i, "joy": 0.9 - 0.1 * i, "trust": 0.2} for i in range(5)]
cc = ec.channel_correlations(recs)
assert cc["r"]["joy"] < -0.99 and cc["max_abs_r_vs_six"] > 0.99 and cc["r"]["trust"] is None
v = ec.defeater_verdict(0.9, 0.95); assert v == {"agreement_under_70pct": False, "collinear_above_0.9": True, "defeated": True}
assert ec.defeater_verdict(0.6, 0.3)["defeated"] is True and ec.defeater_verdict(0.9, 0.3)["defeated"] is False
assert ec.defeater_verdict(None, None)["defeated"] is None
assert ec.felt_text_with_curiosity({"primary": "curiosity", "curiosity": 0.7}).endswith("curiosity=0.70")
print("[5] ok: parse / agreement / correlation / defeater helpers")

# [6] -----------------------------------------------------------------------------------------------------------
import core.model_client as mc  # noqa: E402
calls = []

async def fake_call(urls, system, user, **kw):
    calls.append((system, user))
    return {"joy": 0.1, "trust": 0.2, "curiosity": 0.8, "valence": 0.2, "arousal": 0.6, "primary": "curiosity"}

mc.call_node_json = fake_call
st = CognitiveState(spirit_name="t", axiom="t")
st.input_type = "internal"
st.raw_input = "why is the sea salt"
st.emotion = EmotionOutput(0.1, 0.0, 0.0, 0.5, 0.0, 0.0, 0.1, 0.4, "curiosity")
st.affect = AffectState()
before = (copy.deepcopy(st.emotion), copy.deepcopy(st.affect))
log = TMP / "emotion_curiosity_shadow.jsonl"
assert sch.EMOTION_CURIOSITY_SHADOW is False
assert asyncio.run(node.run_curiosity_shadow(st, log_path=log)) is None and not calls and not log.exists()
sch.EMOTION_CURIOSITY_SHADOW = True
try:
    row = asyncio.run(node.run_curiosity_shadow(st, log_path=log))
finally:
    sch.EMOTION_CURIOSITY_SHADOW = False
assert len(calls) == 1 and calls[0][0] == ec.shadow_system_prompt()
assert row["shadow"]["curiosity"] == 0.8 and row["shadow"]["label_agrees_seven"] is True
assert row["live"]["primary"] == "curiosity" and row["live"]["label_agrees_six"] is False   # the live disagreement
lines = log.read_text(encoding="utf-8").splitlines()
assert len(lines) == 1 and json.loads(lines[0])["cycle_id"] == st.cycle_id
assert (st.emotion, st.affect) == before and st.emotion.curiosity == 0.0
try:
    ec.append_shadow(row)           # default path under the tree's own data/: the write fence must refuse it
    raise AssertionError("write fence did not refuse the default log path")
except profile.NonLiveWriteError:
    pass
print("[6] ok: shadow arm gated, logs beside live, state untouched, default path fenced")

# [7] -----------------------------------------------------------------------------------------------------------
import lab_emotion_curiosity_channel as lab  # noqa: E402
src = TMP / "emotion.jsonl"
with open(src, "w", encoding="utf-8") as f:
    for i in range(10):
        o = {"joy": 0.1, "fear": 0.0, "anger": 0.0, "trust": 0.6, "surprise": 0.2, "disgust": 0.0,
             "valence": 0.2, "arousal": 0.5, "primary": "curiosity" if i < 7 else "trust"}
        f.write(json.dumps({"node": "emotion", "cycle_id": str(i), "input_type": "internal" if i % 2 else "human",
                            "user_prompt": "p", "output": o}) + "\n")
rows = lab.read_tail(src, 8)
assert len(rows) == 8
base = lab.baseline_report(rows)
assert base["n"] == 8 and base["agree"] == 3 and base["disagree_with_argmax_of_six"] == 5   # rows 2..9: 5 curiosity-labelled, 3 trust
res = []
for i in range(6):
    sh = ec.parse_reply({"joy": 0.9 - 0.1 * i, "trust": 0.1, "curiosity": 0.5 + 0.08 * i, "primary": "curiosity"})
    res.append({"cycle_id": str(i), "input_type": "internal", "ok": True, "live": lab.live_rec(rows[i]), "shadow": sh})
res.append({"cycle_id": "x", "input_type": "internal", "ok": False, "live": lab.live_rec(rows[0]), "shadow": None})
rep = lab.score_results(res)
assert rep["rows"] == 7 and rep["rows_scored"] == 6 and rep["rows_failed"] == 1
assert rep["candidate_prompt_seven_channel"]["label_distribution"] == {"curiosity": 6}
assert rep["curiosity_channel"]["r"]["joy"] < -0.99 and rep["defeater_D0555"]["collinear_above_0.9"] is True
assert rep["felt_text_change"]["primary_label_changed"] >= 0
json.dumps(rep)
print("[7] ok: lab baseline + score on synthetic data")
print("ALL OK")

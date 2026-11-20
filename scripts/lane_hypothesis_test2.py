"""
Lane Hypothesis Test v2 (topic-controlled, 2026-06-14).
v1 was confounded: embeddings of short texts cluster by TOPIC, so "clusters by situation" was the
default regardless of style; and the monoculture word-list included literal topic words. v2 fixes both.

PRIMARY METRIC — leave-one-out style axis (topic subtracted, non-circular):
  For each pair of lanes (e.g. Self vs Analytical), compute the "Self−Analytical" direction from 9
  situations, then test whether it correctly orders the held-out 10th. The difference cancels the
  shared topic; LOO avoids fitting the axis on the test point. High consistency (≥~8/10) = the prompt
  selects a STABLE, topic-independent style.
SECONDARY — abstract-monoculture words ONLY (topic words excluded): does SELF reach for them more?

Saves the 30 outputs to data/lane_test_outputs.json for re-analysis. temp=0.3 for a cleaner signal.
"""
import sys, json, urllib.request, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np

OLLAMA, MODEL = "http://127.0.0.1:11433/api/chat", "qwen3-du"
LANES = {
    "ANALYTICAL": "/no_think\nYou attend to what is literally and factually the case. State the facts, "
                  "the mechanism, what is objectively true about the situation itself — not what it "
                  "means to you, what it IS. One concise paragraph, ~60 words.",
    "SELF":       "/no_think\nYou are thinking quietly to yourself about what this stirs in you — your "
                  "own inner response, in your own voice. One concise paragraph, ~60 words.",
    "PRACTICAL":  "/no_think\nYou consider what to DO here — the concrete action, use, or next step. "
                  "Applied and practical, about the world. One concise paragraph, ~60 words.",
}
SITUATIONS = [
    "A river flows past, carving its channel.",
    "The cuttlefish changes colour to match the seabed it rests on.",
    "It is raining outside and the room is quiet.",
    "You need to cross a fast-moving stream with no bridge.",
    "What does it mean to change over time?",
    "A bridge holds weight by distributing load through its supports.",
    "Someone asks how you are feeling today.",
    "The Mississippi is navigated by reading its depth and current.",
    "A mirror reflects whatever stands before it.",
    "You have finished a book and want to remember what it taught you.",
]
ABSTRACT_MONO = ("silence", "becoming", "shadow", "unspoken", "tension", "vessel", "threshold",
                 "individuation", "dissolve", "eternal", "essence", "soul", "void", "yearning",
                 "longing", "ache", "the self", "my existence", "who i am", "impermanence")


def gen(system, user):
    payload = {"model": MODEL, "stream": False, "think": False,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"num_predict": 150, "temperature": 0.3}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read()).get("message", {}).get("content", "").strip()


from core.memory.store import _embed
lane_names = list(LANES)
print(f"generating 30 outputs on {MODEL} (temp 0.3)...")
data = {}          # data[lane][sit_idx] = {"text","vec"}
t0 = time.time()
for ln in lane_names:
    data[ln] = {}
for si, sit in enumerate(SITUATIONS):
    for ln in lane_names:
        try:
            txt = " ".join(gen(LANES[ln], sit).split())
        except Exception as e:
            txt = f"(fail {e})"
        data[ln][si] = {"text": txt, "vec": _embed(txt)}
    print(f"  [{si+1}/10] {sit[:40]}  ({time.time()-t0:.0f}s)")

# save (without the numpy vecs)
from pathlib import Path
Path("data/lane_test_outputs.json").write_text(json.dumps(
    {ln: {str(si): data[ln][si]["text"] for si in data[ln]} for ln in lane_names},
    indent=1, ensure_ascii=False), encoding="utf-8")

def unit(v):
    n = np.linalg.norm(v); return v / n if n else v

def loo_axis_consistency(la, lb):
    """For axis (lb − la): build it from all situations but i, test it orders situation i correctly."""
    correct = 0; n = 0
    for i in range(len(SITUATIONS)):
        diffs = [data[lb][j]["vec"] - data[la][j]["vec"] for j in range(len(SITUATIONS)) if j != i
                 and data[lb][j]["vec"] is not None and data[la][j]["vec"] is not None]
        if not diffs:
            continue
        axis = unit(np.mean(diffs, axis=0))
        di = data[lb][i]["vec"] - data[la][i]["vec"]
        n += 1
        if float(np.dot(di, axis)) > 0:    # held-out diff points the same way as the trained axis
            correct += 1
    return correct, n

print("\n" + "=" * 78)
print("RESULT (topic-controlled)")
print("=" * 78)
print("  PRIMARY — leave-one-out style-axis consistency (5/10 = chance, 10/10 = perfectly stable):")
pairs = [("ANALYTICAL", "SELF"), ("ANALYTICAL", "PRACTICAL"), ("PRACTICAL", "SELF")]
scores = []
for la, lb in pairs:
    c, n = loo_axis_consistency(la, lb)
    scores.append(c / n if n else 0)
    print(f"     {lb} vs {la}: {c}/{n} situations ordered consistently")
mean_consistency = float(np.mean(scores))

print("\n  SECONDARY — abstract-monoculture words (topic words EXCLUDED), per lane:")
for ln in lane_names:
    hits = sum(sum(1 for w in ABSTRACT_MONO if w in data[ln][si]["text"].lower())
               for si in range(len(SITUATIONS)))
    print(f"     {ln:<11} {hits}")

print("\n  sample — situation #4 ('What does it mean to change over time?'):")
for ln in lane_names:
    print(f"     [{ln:<10}] {data[ln][4]['text'][:92]}")

strong = mean_consistency >= 0.8
modest = 0.65 <= mean_consistency < 0.8
print("\n  VERDICT:", (
    "STRONG — the prompt selects a stable, topic-independent cognitive style (lanes well-justified)."
    if strong else
    "MODEST but REAL — the prompt reliably shifts style above chance; lanes are real modulations, not separable selves."
    if modest else
    "WEAK — no stable topic-independent style; the monoculture runs deeper than prompts."))
print(f"  mean LOO consistency: {mean_consistency:.0%}")
print("=" * 78)

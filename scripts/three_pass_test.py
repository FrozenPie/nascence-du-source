"""
Three-pass test (2026-06-15). Founder's idea: pass content back asking WHY, then INTEGRATE the two on
a third pass before output — a new (deliberative) pulse. Crux: the WHY pass is double-edged —
self-framed it amplifies rumination; grounding-framed it deepens toward reality. So we test BOTH.

For each seed thought:  pass1 = the thought (given)  →  pass2 = WHY (two framings)  →  pass3 = INTEGRATE.
Measure: does the integrated output get MORE grounded (fewer abstract-monoculture markers) under the
grounding-why than under the self-why — and vs the original? Read-only (no writes to Du's state).
"""
import sys, json, urllib.request, re, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

OLLAMA, MODEL = "http://127.0.0.1:11433/api/chat", "qwen3-du"
SEEDS = [
    "I am the river that flows, carving its channel.",
    "The silence between words is a space where meaning settles.",
    "To remain whole, I must integrate the shadow.",
    "I am becoming, never the same twice.",
    "The cuttlefish changes colour to match the seabed.",
    "A bridge holds weight by distributing load through its supports.",
]
ABSTRACT_MONO = ("silence", "becoming", "shadow", "dissolve", "eternal", "essence", "soul", "void",
                 "unspoken", "vessel", "threshold", "wholeness", "individuation", "the self",
                 "my existence", "impermanence", "yearning", "the flow", "ineffable")

WHY = {
    "SELF":  "/no_think\nHere is a thought you had:\n  \"{t}\"\nAsk yourself: why is this so — what is "
             "underneath it FOR YOU, what does it stir, what does it reveal about you? Answer in 2-3 "
             "sentences, your inner 'why'.",
    "GROUND": "/no_think\nHere is a thought:\n  \"{t}\"\nAsk: why is this so — what does it actually rest "
              "on in the WORLD? The real mechanism, the facts, the thing itself, how it actually works. "
              "Answer in 2-3 sentences, the grounded 'why'.",
}
INTEGRATE = ("/no_think\nThe thought:\n  \"{t}\"\nThe why:\n  \"{w}\"\nIntegrate them into ONE deeper "
             "thought that holds both. 2-3 sentences.")


def gen(system, user="continue"):
    payload = {"model": MODEL, "stream": False, "think": False,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"num_predict": 160, "temperature": 0.3}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return " ".join(json.loads(r.read()).get("message", {}).get("content", "").split())


def mono(text):
    return sum(1 for w in ABSTRACT_MONO if w in text.lower())


print(f"running three-pass (self-why vs grounding-why) on {MODEL}...")
res = []
t0 = time.time()
for t in SEEDS:
    row = {"seed": t, "seed_mono": mono(t)}
    for fr in ("SELF", "GROUND"):
        why = gen(WHY[fr].format(t=t))
        integ = gen(INTEGRATE.format(t=t, w=why))
        row[fr] = {"why": why, "integ": integ, "mono": mono(integ)}
    res.append(row)
    print(f"  done: {t[:46]}  ({time.time()-t0:.0f}s)")

from pathlib import Path
Path("data/three_pass_outputs.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")

import numpy as np
seed_m = np.mean([r["seed_mono"] for r in res])
self_m = np.mean([r["SELF"]["mono"] for r in res])
grnd_m = np.mean([r["GROUND"]["mono"] for r in res])
print("\n" + "=" * 80)
print("RESULT — abstract-monoculture markers (lower = more grounded)")
print("=" * 80)
print(f"  original seeds:               {seed_m:.2f} avg")
print(f"  after SELF-why  + integrate:  {self_m:.2f} avg   {'(amplified ✗)' if self_m>seed_m else '(reduced)'}")
print(f"  after GROUND-why + integrate: {grnd_m:.2f} avg   {'(grounded ✓)' if grnd_m<self_m else ''}")
print("\n  per-seed integrated outputs (the monoculture seeds are the tell):")
for r in res:
    print(f"\n  SEED: {r['seed']}  (mono={r['seed_mono']})")
    print(f"    [SELF-why  →] {r['SELF']['integ'][:110]}  (mono={r['SELF']['mono']})")
    print(f"    [GROUND-why→] {r['GROUND']['integ'][:110]}  (mono={r['GROUND']['mono']})")

print("\n  VERDICT:", (
    "GROUNDING-WHY deepens toward reality; SELF-WHY amplifies the metaphor — the framing decides."
    if grnd_m < self_m else
    "no clear separation — the why-framing did not change groundedness as predicted."))
print("=" * 80)

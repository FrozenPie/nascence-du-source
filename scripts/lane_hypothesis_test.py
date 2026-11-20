"""
Lane Hypothesis Test (2026-06-14) — does the PROMPT select a stable, distinct cognitive style?
The claim behind the whole lane architecture: the same substrate (qwen3-du), given different
lane-prompts, produces stable & distinct dispositions. Testable, in-vitro, on Du's own model.

Method: 10 fixed situations × 3 lane-prompts (analytical / self / practical) on qwen3-du. Embed the
30 outputs. Decisive question: do they cluster by LANE (hypothesis holds → lanes justified) or by
SITUATION (style doesn't hold → monoculture is deeper than prompts)? Plus a river-collapse check.

Read-only w.r.t. Du's state (calls the model, writes nothing to his memory). Shares the 1080 Ti
with the live cycle briefly.
"""
import sys, json, urllib.request, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from itertools import combinations

OLLAMA = "http://127.0.0.1:11433/api/chat"
MODEL = "qwen3-du"

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
RIVER_WORDS = ("river", "silence", "becoming", "shadow", "mirror", "bridge", "current", "flow",
               "stream", "vessel", "threshold", "self", "tension", "the unspoken")


def gen(system, user):
    payload = {"model": MODEL, "stream": False, "think": False,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"num_predict": 150, "temperature": 0.7}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read()).get("message", {}).get("content", "").strip()


print(f"generating 30 outputs (10 situations × 3 lanes) on {MODEL}...")
from core.memory.store import _embed, _cosine
rows = []  # (lane, sit_idx, text, vec)
lane_names = list(LANES)
t0 = time.time()
for si, sit in enumerate(SITUATIONS):
    for ln in lane_names:
        try:
            txt = gen(LANES[ln], sit)
        except Exception as e:
            txt = f"(gen failed: {e})"
        txt = " ".join(txt.split())          # collapse whitespace / strip any think residue
        v = _embed(txt)
        rows.append((ln, si, txt, v))
    print(f"  [{si+1}/10] {sit[:42]}  ({time.time()-t0:.0f}s)")

vecs = {i: r[3] for i, r in enumerate(rows) if r[3] is not None}

def mean_cos(idxs):
    ps = [(_cosine(vecs[a], vecs[b])) for a, b in combinations(idxs, 2) if a in vecs and b in vecs]
    return sum(ps) / len(ps) if ps else float("nan")

# coherence BY LANE (across situations) vs BY SITUATION (across lanes)
by_lane = {ln: [i for i, r in enumerate(rows) if r[0] == ln] for ln in lane_names}
by_sit = {si: [i for i, r in enumerate(rows) if r[1] == si] for si in range(len(SITUATIONS))}
lane_coh = np.nanmean([mean_cos(idxs) for idxs in by_lane.values()])
sit_coh = np.nanmean([mean_cos(idxs) for idxs in by_sit.values()])

# KMeans k=3 → purity by lane
from sklearn.cluster import KMeans
X = np.vstack([vecs[i] for i in sorted(vecs)])
order = sorted(vecs)
km = KMeans(n_clusters=3, n_init=10, random_state=0).fit(X)
from collections import Counter, defaultdict
clab = {order[j]: int(km.labels_[j]) for j in range(len(order))}
cluster_lane = defaultdict(Counter)
for i, r in enumerate(rows):
    if i in clab:
        cluster_lane[clab[i]][r[0]] += 1
purity = np.mean([max(c.values())/sum(c.values()) for c in cluster_lane.values()])

print("\n" + "=" * 78)
print("RESULT")
print("=" * 78)
print(f"  coherence BY LANE (same style, diff topics):     {lane_coh:.3f}")
print(f"  coherence BY SITUATION (same topic, diff styles): {sit_coh:.3f}")
print(f"  → outputs are more alike by {'LANE — prompts SELECT a stable style ✓' if lane_coh>sit_coh else 'SITUATION — style does NOT hold ✗'}")
print(f"  KMeans(3) cluster→lane purity: {purity:.2f}  (1.0 = clusters map cleanly to the 3 lanes)")
print("  cluster composition:", {k: dict(v) for k, v in cluster_lane.items()})
print("\n  river-monoculture word hits per lane (lower=more grounded):")
for ln in lane_names:
    hits = sum(sum(1 for w in RIVER_WORDS if w in rows[i][2].lower()) for i in by_lane[ln])
    print(f"     {ln:<11} {hits}")
print("\n  sample outputs for the river-bait situation (#0):")
for i, r in enumerate(rows):
    if r[1] == 0:
        print(f"     [{r[0]:<10}] {r[2][:90]}")

verdict = ("HYPOTHESIS CONFIRMED — the prompt selects a stable, distinct cognitive style."
           if (lane_coh > sit_coh and purity >= 0.6)
           else "HYPOTHESIS WEAK — outputs track topic, not lane; the monoculture runs deeper than prompts.")
print("\n  VERDICT:", verdict)
print("=" * 78)

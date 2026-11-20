import json
import os
import sys
import time
import datetime
import collections
import re
import torch

sys.path.insert(0, '.')
sys.path.insert(0, 'c:/Nascence')
sys.stdout.reconfigure(encoding='utf-8')

from core.memory.store import _get_model
import numpy as np

start_ts = 1786459200 # 2026-08-12 00:00:00 NZST

print("==========================================================================")
print("   BACKTEST: CONSERVATIVE INTERNAL TENSION RESOLUTION MATCHER (SHADOW)    ")
print("==========================================================================")

t_start = time.time()
with open('data/subconscious_state.json', 'r', encoding='utf-8') as f:
    sub_state = json.load(f)

tensions = sub_state.get('tensions', [])
print(f"Loaded {len(tensions)} standing tensions from subconscious_state.json.")

# Batch extract tension centroids
tension_candidates = []
tension_vecs = []

for t in tensions:
    t_id = t.get('id')
    t_label = t.get('label', '')
    t_vec = t.get('centroid') or t.get('last_synthesis_emb')
    if t_id and t_label and t_vec and len(t_vec) == 384:
        tokens = set(re.findall(r'\w+', t_label.lower()))
        tension_candidates.append({
            "id": t_id,
            "label": t_label,
            "tokens": tokens,
            "raw": t
        })
        tension_vecs.append(t_vec)

tension_matrix = np.array(tension_vecs, dtype=np.float32)
# Normalize tension vectors
norms = np.linalg.norm(tension_matrix, axis=1, keepdims=True)
norms[norms == 0] = 1e-9
tension_matrix = tension_matrix / norms

print(f"Prepared matrix for {len(tension_candidates)} tensions (384-dim).")

# Load thoughts
monologues_today = []
with open('data/monologue_log.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        if d.get('ts', 0) >= start_ts:
            monologues_today.append(d)

resolving_thoughts = [m for m in monologues_today if not m.get('unresolved') and len(m.get('thought', '')) >= 40]
print(f"Found {len(resolving_thoughts)} valid thoughts marked 'unresolved': false.")

# Batch embed resolving thoughts using SentenceTransformer model directly
model = _get_model()
thought_texts = [m['thought'] for m in resolving_thoughts]
print(f"Batch embedding {len(thought_texts)} resolving thoughts...")
th_embeddings = model.encode(thought_texts, convert_to_numpy=True, show_progress_bar=False)
th_norms = np.linalg.norm(th_embeddings, axis=1, keepdims=True)
th_norms[th_norms == 0] = 1e-9
th_embeddings = th_embeddings / th_norms

print(f"Embeddings ready in {time.time() - t_start:.2f}s.\n")

stopwords = {'and', 'the', 'of', 'in', 'to', 'a', 'is', 'that', 'for', 'it', 'with', 'as', 'was', 'on', 'at', 'by', 'an', 'be', 'this', 'which', 'or', 'from', 'my', 'i', 'unresolved', 'thought', 'dream'}

def run_backtest_pass(sim_threshold=0.70, require_topic_match=True):
    matches = []
    false_candidates = []
    resolved_tensions = set()

    for idx, m in enumerate(resolving_thoughts):
        th_vec = th_embeddings[idx]
        thought_text = m.get('thought', '')
        about_text = m.get('about', '')
        ts = m.get('ts', 0)
        dt_str = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

        # Cosine similarities against all tension centroids: dot product of normalized vectors
        sims = np.dot(tension_matrix, th_vec)

        about_tokens = set(re.findall(r'\w+', about_text.lower())) if about_text else set()
        thought_tokens = set(re.findall(r'\w+', thought_text.lower()))

        best_sim = -1.0
        best_t = None
        best_reason = ""

        # Candidates exceeding threshold
        cand_indices = np.where(sims >= sim_threshold)[0]
        for t_idx in cand_indices:
            t = tension_candidates[t_idx]
            if t['id'] in resolved_tensions:
                continue

            sim = float(sims[t_idx])
            shared_about = (about_tokens.intersection(t['tokens'])) - stopwords
            shared_thought = (thought_tokens.intersection(t['tokens'])) - stopwords

            if require_topic_match and len(shared_about) == 0 and len(shared_thought) < 2:
                false_candidates.append({
                    "thought": thought_text[:100],
                    "about": about_text,
                    "tension_label": t['label'][:100],
                    "sim": sim,
                    "reason": "High sim but 0 about-overlap & <2 thought-overlap"
                })
                continue

            if sim > best_sim:
                best_sim = sim
                best_t = t
                best_reason = f"Sim={sim:.3f} | Overlap about={list(shared_about)} thought={list(shared_thought)[:3]}"

        if best_t:
            matches.append({
                "ts_str": dt_str,
                "thought": thought_text,
                "about": about_text,
                "tension_id": best_t['id'],
                "tension_label": best_t['label'],
                "sim": best_sim,
                "reason": best_reason
            })
            resolved_tensions.add(best_t['id'])

    return matches, false_candidates

print("==========================================================================")
print("              SWEEP EVALUATION: SIMILARITY THRESHOLDS                     ")
print("==========================================================================")

for thresh in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
    matches, false_cands = run_backtest_pass(sim_threshold=thresh, require_topic_match=True)
    print(f"Threshold >= {thresh:.2f}: {len(matches):3d} Valid Resolving Matches  |  {len(false_cands):3d} Filtered Spurious Matches")

# Detailed display for 0.65 threshold
print("\n==========================================================================")
print("          DETAILED SAMPLE MATCHES AT THRESHOLD >= 0.65                     ")
print("==========================================================================")
matches, false_cands = run_backtest_pass(sim_threshold=0.65, require_topic_match=True)
for idx, m in enumerate(matches[:10]):
    print(f"{idx+1}. [{m['ts_str']}] About: [{m['about']}]")
    print(f"   Thought: \"{m['thought']}\"")
    print(f"   --> Matched Open Tension: \"{m['tension_label']}\"")
    print(f"   --> {m['reason']}\n")

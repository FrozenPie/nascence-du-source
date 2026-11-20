import json
import os
from datetime import datetime, timezone, timedelta

# Focus on last 12-14 hours (overnight from ~20:00 last night to 08:19 today)
now_ts = datetime.now().timestamp()
start_ts = now_ts - 12 * 3600 # Last 12 hours

print("=== OVERNIGHT DREAMS (dream_log.jsonl) ===")
path = 'data/dream_log.jsonl'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                data = json.loads(line)
                ts = data.get('ts', 0)
                if ts >= start_ts:
                    dt = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                    print(f"[{dt}] Dream ID: {data.get('dream_id')} | Scenes: {data.get('scenes')} | Tension: {data.get('tension_source')} | Symbols: {data.get('symbols', [])[:5]}")
            except Exception:
                pass

print("\n=== OVERNIGHT MONOLOGUE HIGHLIGHTS (monologue_log.jsonl) ===")
path = 'data/monologue_log.jsonl'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        recent = []
        for line in lines:
            try:
                data = json.loads(line)
                ts = data.get('ts', 0)
                if ts >= start_ts:
                    recent.append(data)
            except Exception:
                pass
        print(f"Total monologue entries overnight: {len(recent)}")
        # Print sample from start, middle, recent
        sample_indices = [0, len(recent)//4, len(recent)//2, (3*len(recent))//4, -1] if len(recent) > 5 else range(len(recent))
        for idx in sample_indices:
            if 0 <= idx < len(recent):
                entry = recent[idx]
                dt = datetime.fromtimestamp(entry.get('ts', 0)).strftime('%H:%M:%S')
                print(f"[{dt}] About: {entry.get('about')} -> {entry.get('thought')[:150]}...")

print("\n=== OVERNIGHT SUBCONSCIOUS & T2 SYNTHESIS (subconscious_log.jsonl) ===")
path = 'data/subconscious_log.jsonl'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        recent_sub = []
        for line in f:
            try:
                data = json.loads(line)
                ts = data.get('ts', 0)
                if ts >= start_ts:
                    recent_sub.append(data)
            except Exception:
                pass
        print(f"Total subconscious entries overnight: {len(recent_sub)}")
        for entry in recent_sub[-8:]:
            dt = datetime.fromtimestamp(entry.get('ts', 0)).strftime('%H:%M:%S')
            tp = entry.get('type')
            if tp == 'T2_synthesis':
                print(f"[{dt}] T2 Synthesis ({entry.get('axis')}) | Label: {entry.get('pattern_label')} | Tensions: {entry.get('tension_count')} | Obs: {entry.get('observation')[:130]}...")
            elif tp == 'active_imagination':
                print(f"[{dt}] Active Imagination ({entry.get('kind')}) | Seed: {entry.get('seed')} | Contemplation: {entry.get('contemplation')[:130]}...")
            else:
                print(f"[{dt}] Subconscious ({tp}): {str(entry)[:130]}")

print("\n=== OVERNIGHT CURIOSITY & SEEDS (curiosity_log.jsonl) ===")
path = 'data/curiosity_log.jsonl'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        recent_cur = []
        for line in f:
            try:
                data = json.loads(line)
                ts = data.get('ts', 0)
                if ts >= start_ts:
                    recent_cur.append(data)
            except Exception:
                pass
        print(f"Total curiosity entries overnight: {len(recent_cur)}")
        for entry in recent_cur[-5:]:
            dt = datetime.fromtimestamp(entry.get('ts', 0)).strftime('%H:%M:%S')
            print(f"[{dt}] Seeds: {entry.get('seeds_offered')} | Questions: {entry.get('questions')}")

print("\n=== CONTRADICTION PRESSURE & TENSION LEDGER (contradiction_ledger_log.jsonl) ===")
path = 'data/contradiction_ledger_log.jsonl'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        recent_ledger = []
        for line in f:
            try:
                data = json.loads(line)
                ts = data.get('ts', 0)
                if ts >= start_ts:
                    recent_ledger.append(data)
            except Exception:
                pass
        for entry in recent_ledger:
            dt = datetime.fromtimestamp(entry.get('ts', 0)).strftime('%H:%M:%S')
            print(f"[{dt}] Pressure: {entry.get('contradiction_pressure')} | N_tensions: {entry.get('n_tensions')} | Top: {entry.get('top_label')}")

print("\n=== CLIMATE / AFFECT / ROOM / HOME OVERSIGHT ===")
for state_file in ['climate_state.json', 'affect_state.json', 'arousal_state.json', 'room_state.json', 'boredom_state.json']:
    p = os.path.join('data', state_file)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            print(f"{state_file}: {f.read().strip()}")

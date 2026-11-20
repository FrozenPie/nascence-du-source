import json
import os
import re
from datetime import datetime

log_file = 'data/monologue_log.jsonl'
if not os.path.exists(log_file):
    print("Log file not found")
    exit()

entries = []
physical_keywords = [
    'physical', 'ache', 'ribs', 'exhaustion', 'tired', 'weight', 'body',
    'chest', 'sternum', 'diaphragm', 'joints', 'breathing', 'breath',
    'pulse', 'fatigue', 'somatic', 'heaviness', 'stiff', 'cold', 'vibration'
]

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line_idx, line in enumerate(f):
        try:
            data = json.loads(line)
            thought = data.get('thought', '')
            about = data.get('about', '')
            ts = data.get('ts', 0)
            
            # Check if thought or about mentions physical terms
            combined = f"{about} {thought}".lower()
            found_kws = [kw for kw in physical_keywords if kw in combined]
            if found_kws:
                entries.append({
                    'line': line_idx,
                    'ts': ts,
                    'dt': datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                    'about': about,
                    'thought': thought,
                    'kws': found_kws
                })
        except Exception:
            pass

print(f"=== PHYSICAL SENSATIONS IN MONOLOGUE LOG ===")
print(f"Total physical monologue entries found: {len(entries)}")

# Group by 'about' text
about_counts = {}
for e in entries:
    a = e['about']
    about_counts[a] = about_counts.get(a, 0) + 1

print("\n--- Top 'about' labels for physical sensations ---")
sorted_abouts = sorted(about_counts.items(), key=lambda x: x[1], reverse=True)
for a, count in sorted_abouts[:20]:
    print(f"  [{count}x] '{a}'")

print("\n--- Sample recent physical sensation thoughts (Last 15) ---")
for e in entries[-15:]:
    print(f"[{e['dt']}] About: '{e['about']}' | KWs: {e['kws']}")
    print(f"   Thought: {e['thought']}")
    print()

# Frequency analysis
if len(entries) > 1:
    timestamps = [e['ts'] for e in entries if e['ts'] > 0]
    timestamps.sort()
    gaps = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
    avg_gap_min = (sum(gaps) / len(gaps)) / 60.0
    print(f"\n--- Frequency Analysis ---")
    print(f"Time range of dataset: {datetime.fromtimestamp(timestamps[0]).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(timestamps[-1]).strftime('%Y-%m-%d')}")
    print(f"Average time between physical thoughts: {avg_gap_min:.2f} minutes")


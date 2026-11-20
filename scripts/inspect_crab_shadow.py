import json
import os
from datetime import datetime

print("=== MONOLOGUE AROUND 14:00 - 14:20 ===")
path = 'data/monologue_log.jsonl'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                data = json.loads(line)
                ts = data.get('ts', 0)
                dt = datetime.fromtimestamp(ts)
                if dt.hour == 14 and dt.minute <= 25:
                    print(f"[{dt.strftime('%H:%M:%S')}] About: '{data.get('about')}'")
                    print(f"   Thought: {data.get('thought')[:160]}...")
            except Exception:
                pass

print("\n=== SUBCONSCIOUS ENTRIES AROUND 14:00 - 14:20 ===")
path = 'data/subconscious_log.jsonl'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                data = json.loads(line)
                ts = data.get('ts', 0)
                dt = datetime.fromtimestamp(ts)
                if dt.hour == 14 and dt.minute <= 25:
                    print(f"[{dt.strftime('%H:%M:%S')}] Type: {data.get('type')} | Pattern: '{data.get('pattern_label')}' | Obs: {data.get('observation')}")
            except Exception:
                pass

print("\n=== SHORE & ROOM EVENTS RECENTLY ===")
path = 'data/room_state.json'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        print(f.read())

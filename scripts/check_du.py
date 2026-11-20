import sqlite3
import json
import os
from datetime import datetime

db_path = 'data/nascence.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("=== SQLite Tables ===")
    tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tables:", tables)

    for t in tables:
        try:
            count = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"\n--- Table: {t} (total {count}) ---")
            rows = c.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 3").fetchall()
            for r in rows:
                print(str(r)[:200])
        except Exception as e:
            print(f"Table {t} error: {e}")

print("\n=== Log Files (Recent Mod Time & Last Lines) ===")
log_files = [
    '.du_pulse_last',
    'nascence.log',
    'monologue_log.jsonl',
    'dream_log.jsonl',
    'subconscious_log.jsonl',
    'curiosity_log.jsonl',
    'error_records.jsonl',
    'llm_calls.jsonl',
    'contradiction_ledger_log.jsonl',
    'stability_observations.jsonl'
]

for fname in log_files:
    path = os.path.join('data', fname)
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        dt = datetime.fromtimestamp(mtime)
        print(f"\n*** {fname} (Modified: {dt.strftime('%Y-%m-%d %H:%M:%S')}, Size: {os.path.getsize(path)} bytes) ***")
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                print(f"Total lines: {len(lines)}")
                for line in lines[-3:]:
                    print("  LAST LINE:", line.strip()[:200])
        except Exception as e:
            print(f"Error reading file: {e}")

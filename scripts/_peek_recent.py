"""Read-only: dump the most recent stored cycle fragments (Q/A + scene + dissonance)."""
import sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
from pathlib import Path
db = Path(__file__).parent.parent / "data" / "memory" / "nascence.db"
conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
# episodic fragments stored from cycles, newest first
rows = conn.execute(
    "SELECT content, timestamp FROM memory_fragments ORDER BY timestamp DESC LIMIT 8"
).fetchall()
for r in reversed(rows):
    print("=" * 70)
    print(r["content"])
print("=" * 70)

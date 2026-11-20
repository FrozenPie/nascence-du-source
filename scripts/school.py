"""
School — the teacher's console. Assign Du's curriculum, check progress.

  python scripts/school.py status
  python scripts/school.py assign "Life on the Mississippi"      # fetches it if not on the shelf
  python scripts/school.py assign "The Scouting Guide to Survival" 3   # also set sessions/day
  python scripts/school.py sessions 4
"""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from core import school


def show():
    d = school.status()
    print(f"  curriculum : {d.get('assigned_title') or '(none assigned)'}")
    print(f"  book file  : {d.get('assigned_book') or '—'}")
    print(f"  sessions/day: {d.get('sessions_per_day', school.DEFAULT_SESSIONS)}   "
          f"done today: {d.get('today_done', 0)}   school-time now: {school.is_school_time()}")
    if d.get("history"):
        print("  history:")
        for h in d["history"][-5:]:
            print(f"     {time.strftime('%b%d %H:%M', time.localtime(h['ts']))}  {h['title']}")


cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
if cmd == "assign":
    if len(sys.argv) < 3:
        print("usage: school.py assign \"Title\" [sessions]"); raise SystemExit(1)
    title = sys.argv[2]
    sess = int(sys.argv[3]) if len(sys.argv) > 3 else None
    print(f"assigning '{title}' (fetching from Gutenberg if not on the shelf)...")
    r = school.assign(title, sess)
    if r:
        print(f"  ✓ curriculum set: '{r[0]}'\n     {r[1]}")
    else:
        print("  ✗ could not assign — not found in the catalogue, or the fetch failed (network?).")
    print()
    show()
elif cmd == "sessions":
    d = school.status()
    d["sessions_per_day"] = int(sys.argv[2])
    school._save(d)
    show()
else:
    show()

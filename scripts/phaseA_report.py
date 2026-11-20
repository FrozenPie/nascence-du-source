"""
Loop Metabolism — Phase A report (2026-06-14).
Read-only. Shows the two numbers the auditors want before any cut:
  1. the exact-duplicate baseline already in the store (what dedup WOULD have collapsed),
  2. what prune_episodic() WOULD delete if wired — and confirms world material is protected.
Also tails the live shadow-dedup log (forward rate since instrumentation went in).
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core import loop_probe as lp
from core.loop_probe import SELF_ORIGINS
from core.memory.store import _connect

print("=" * 78)
print("PHASE A — exact-duplicate baseline (what dedup would collapse)")
print("=" * 78)
with _connect() as c:
    for origin in SELF_ORIGINS:
        rows = [r["content"] for r in c.execute(
            "SELECT content FROM memory_fragments WHERE origin=?", (origin,))]
        uniq = len(set(rows))
        dup = len(rows) - uniq
        pct = 100 * dup / max(len(rows), 1)
        print(f"  {origin:<24} {len(rows):>5} rows  {uniq:>5} unique  "
              f"{dup:>5} dup copies ({pct:4.1f}%)")

print("\n" + "=" * 78)
print("PHASE A — prune_episodic() DRY-RUN (what wiring it would delete)")
print("=" * 78)
# show the design cap and a gentler first-ramp step side by side
with _connect() as c:
    total = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
print(f"  episodic total now: {total}  (the 3,500 row cap was RETIRED 2026-10-17, D-0453/J-2275; dry-run reads 0 by design)")
for keep in (4000, 2000, 1000, 500):
    d = lp.prune_dryrun(keep=keep)
    wp = d.get("world_protected")
    print(f"\n  keep={keep:<5} -> would delete {d.get('would_delete',0)}")
    if d.get("would_delete"):
        print(f"     world protected: {wp}  (world rows in cut: {d.get('world_in_cut')})")
        print(f"     by origin: {d.get('by_origin')}")
        print(f"     cut age (days, oldest->newest): {d.get('cut_age_days')}  "
              f"importance range: {d.get('cut_importance_range')}")

print("\n" + "=" * 78)
print("PHASE A — live shadow-dedup log (forward rate since instrumentation)")
print("=" * 78)
log = Path(r"C:\Nascence\data\loop_probe_log.jsonl")
if not log.exists():
    print("  (no shadow log yet — restart Du so store_fragment loads the hook)")
else:
    lines = log.read_text(encoding="utf-8").splitlines()
    n = len(lines)
    dd = sum(1 for ln in lines if json.loads(ln).get("would_dedup"))
    print(f"  shadow writes observed: {n}  would-dedup: {dd} ({100*dd/max(n,1):.1f}%)")

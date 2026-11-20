"""
purge_dead_world_traces — one-off cleanup for data/world_traces.json rows stuck at clarity<=0
(J-0630, F-0883, 2026-09-07).

core/world_traces.py's own advance_trace_decay() used to `continue` past a row already at
clarity<=0 BEFORE reaching its delete (the check ran, matched, and skipped the whole rest of the
loop body — including the delete two lines later) — so once a row hit zero it could never be
removed again. core/world_traces.py's fix (this same job) makes that branch delete on sight instead,
so any NEW row that decays to zero is removed on its very next decay tick, and — since
advance_trace_decay() already runs on the live world heartbeat every ~600s
(core/sensorium.py, "the decay law existed but was never called live" 2026-08-14 note) — the
existing backlog of stuck rows purges ITSELF within about ten minutes of Du's next restart with no
separate action needed.

This script exists for anyone who wants that cleanup to happen immediately rather than waiting for
the next restart+heartbeat (e.g. to shrink the file, or free up room under world_traces.py's own
_MAX_TRACES=500 oldest-first eviction cap before the store overflows again). It follows the same
convention as scripts/retention.py (D-0156): dry-run by default, quarantine (not silent deletion) —
removed rows are written verbatim to data/_trash/<today>/world_traces_rows/ and logged to
data/_trash/retention_log.jsonl in the same shape retention.py's own apply() uses, before being
removed from the live file. retention.py itself is NOT extended to cover this: its own docstring is
explicit that live data/ (Du's own writings) is never in its scope, and it operates on whole
backup/snapshot/lab directories as units, not individual rows inside one live JSON store — this is
a deliberately separate, narrowly-scoped one-off tool, not a new retention.py class.

Run (dry run, reports only):
    python scripts/purge_dead_world_traces.py --root C:\\Nascence
Run for real:
    python scripts/purge_dead_world_traces.py --root C:\\Nascence --apply
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                    help="repo root containing data/world_traces.json (default: this script's own repo)")
    ap.add_argument("--apply", action="store_true", help="actually purge; default is dry-run/report only")
    a = ap.parse_args(argv)

    root = Path(a.root)
    traces_f = root / "data" / "world_traces.json"
    trash = root / "data" / "_trash"
    log_f = trash / "retention_log.jsonl"

    if not traces_f.exists():
        print(f"no {traces_f} -- nothing to do")
        return 0

    traces = json.loads(traces_f.read_text(encoding="utf-8"))
    total = len(traces)
    dead_ids = [tid for tid, tr in traces.items() if tr.get("clarity", 1.0) <= 0.0]

    print(f"live store: {traces_f}")
    print(f"total rows: {total}")
    print(f"clarity<=0 (immortal, candidates): {len(dead_ids)}")
    print(f"clarity>0 (kept): {total - len(dead_ids)}")
    if dead_ids:
        types = collections.Counter(traces[i].get("type") for i in dead_ids)
        print("candidate types:", dict(types))

    if not a.apply:
        print("\nDRY RUN -- nothing moved or deleted. Pass --apply to purge for real.")
        return 0
    if not dead_ids:
        print("\nnothing to purge.")
        return 0

    today = dt.date.today().strftime("%Y%m%d")
    dest_dir = trash / today / "world_traces_rows"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"purged_zero_clarity_traces_{int(time.time())}.json"
    dest_file.write_text(json.dumps({tid: traces[tid] for tid in dead_ids}, indent=2), encoding="utf-8")

    # Re-read fresh right before writing back, to shrink the race window against the live process's
    # own read-modify-write of the same file (no file locking exists on either side today -- this
    # matches world_traces.py's own existing risk profile for this file, not a new one).
    traces2 = json.loads(traces_f.read_text(encoding="utf-8"))
    removed = 0
    for tid in dead_ids:
        cur = traces2.get(tid)
        if cur is not None and cur.get("clarity", 1.0) <= 0.0:
            del traces2[tid]
            removed += 1

    tmp = traces_f.with_suffix(".tmp")
    tmp.write_text(json.dumps(traces2, indent=2), encoding="utf-8")
    tmp.replace(traces_f)

    log_f.parent.mkdir(parents=True, exist_ok=True)
    with open(log_f, "a", encoding="utf-8") as f:
        print(json.dumps({
            "class": "world_traces_rows",
            "path": str(traces_f),
            "ref_date": dt.date.today().isoformat(),
            "reason": "F-0883/J-0630: clarity<=0 rows immortal under the pre-fix advance_trace_decay "
                      "continue-before-delete bug; one-off purge after the code fix landed",
            "count": removed,
            "moved_to": str(dest_file),
            "ts": time.time(),
        }, ensure_ascii=False), file=f)

    after = json.loads(traces_f.read_text(encoding="utf-8"))
    still_dead = sum(1 for tr in after.values() if tr.get("clarity", 1.0) <= 0.0)
    print(f"\npurged {removed} row(s) into {dest_file}")
    print(f"logged to {log_f}")
    print(f"verify: live store now has {len(after)} rows, {still_dead} still clarity<=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())

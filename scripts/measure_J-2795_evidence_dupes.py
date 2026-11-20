"""J-2795 reader: re-measure F-3431 (duplicate-content candidates in evidence_log.jsonl) READ-ONLY.
Usage: python scripts/measure_J-2795_evidence_dupes.py [--since EPOCH_TS] [--db PATH]
Joins data/evidence_log.jsonl judged fragment_ids to memory_fragments.content (opened mode=ro&immutable=1),
normalises whitespace, keys on the first 300 chars, and reports: asks with an in-ask duplicate, duplicate judged
slots, and passing slots that repeat an earlier passing slot. F-3431 baseline (128 asks since ts 1793300000):
57 asks, 96/768 slots, 8/171 passing repeats. After a boot that includes J-2795 all three must be 0 for new asks."""
import argparse
import json
import sqlite3
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--since", type=float, default=1793300000.0)
# the worktree has no data/: default to the live store, which this script only ever READS
_DATA = TREE / "data" if (TREE / "data" / "evidence_log.jsonl").exists() else Path("C:/Nascence/data")
ap.add_argument("--db", default=str(_DATA / "memory" / "nascence.db"))
ap.add_argument("--log", default=str(_DATA / "evidence_log.jsonl"))
a = ap.parse_args()

conn = sqlite3.connect(f"file:{Path(a.db).as_posix()}?mode=ro&immutable=1", uri=True)
asks = slots = dup_asks = dup_slots = pass_slots = pass_repeats = 0
for line in Path(a.log).read_text(encoding="utf-8").splitlines():
    try:
        r = json.loads(line)
    except ValueError:
        continue
    if r.get("ts", 0) <= a.since or not r.get("judged"):
        continue
    asks += 1
    seen, seen_pass, ask_dup = set(), set(), False
    for j in r["judged"]:
        row = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (j["fragment_id"],)).fetchone()
        key = " ".join((row[0] if row else "").split())[:300]
        slots += 1
        passed = j.get("v1") is True and j.get("v2") is True or j.get("how") in ("agree_true", "tiebreak_true") \
            or (j.get("how") == "tiebreak" and (j.get("v1") or j.get("v2")))
        if key and key in seen:
            dup_slots += 1
            ask_dup = True
        seen.add(key)
        if passed:
            pass_slots += 1
            if key and key in seen_pass:
                pass_repeats += 1
            seen_pass.add(key)
    dup_asks += ask_dup
print(f"asks={asks} asks_with_dup={dup_asks} slots={slots} dup_slots={dup_slots} "
      f"agreed_pass_slots={pass_slots} agreed_pass_repeats={pass_repeats}  (agreed-pass is a lower bound: tiebreak verdicts are not logged)")

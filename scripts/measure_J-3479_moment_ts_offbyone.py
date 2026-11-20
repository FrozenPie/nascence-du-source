"""J-3479 (F-4017 / J-3393): how many existing inner_thought fragments are off by one cycle under the moment_ts rule?

READ-ONLY measurement, run it on a COPY of the memory DB (--db). The moment_ts rule (J-3246/D-0634) stamps the moment that
was current when store_fragment ran = the latest moment with ts <= the fragment's own tuple_ts. A fresh inner thought is
stored BEFORE its own cycle's moment is bound, so that stamp would be the PREVIOUS cycle's moment. Existing rows carry no
moment_ts (the live DB has not run J-3246 yet), so this REPLAYS the rule from the two logs and compares it with the
fragment's own moment, found by the same text heuristic scripts/moment_key_validate.py uses (moment thought[:70], >=30 chars,
substring of the fragment, within +/-300 s, exactly one candidate).

  own    -- the replayed stamp is the fragment's own moment   (the ordering fact would NOT have bitten)
  lag1   -- the replayed stamp is the moment before its own   (off by one cycle: the F-4017 case)
  other  -- anything else (an older moment, or none)

Never writes. Opens the DB mode=ro.   python scripts/measure_J-3479_moment_ts_offbyone.py --db COPY.db --moments M.jsonl
        [--since-days 14] [--json]
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

_TS = re.compile(r'^\{"ts": ([0-9.]+)')


def _norm(s) -> str:
    return " ".join((s or "").split())


def load_moments(path: Path, since: float):
    ms = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = _TS.match(line)
            if not m or float(m.group(1)) < since:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            ms.append((float(r["ts"]), _norm(r.get("thought"))[:70]))
    ms.sort()
    return ms


def measure(db: Path, moments: Path, since_days: float = 14.0) -> dict:
    since = time.time() - since_days * 86400.0
    ms = load_moments(moments, since - 600)
    ts_list = [m[0] for m in ms]
    out = {"db": str(db), "since_days": since_days, "moments_loaded": len(ms), "inner_thought_fragments": 0,
           "no_heuristic_match": 0, "ambiguous": 0, "unique": 0, "own": 0, "lag1": 0, "other": 0,
           "frag_before_own_moment": 0, "gap_s_median": None}
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT fc.tuple_ts, mf.content FROM fragment_context fc JOIN memory_fragments mf "
            "ON mf.fragment_id = fc.fragment_id WHERE mf.origin='inner_thought' AND fc.source LIKE 'experienced:%' "
            "AND fc.tuple_ts >= ?", (since,)).fetchall()
    finally:
        conn.close()
    gaps = []
    for fts, content in rows:
        out["inner_thought_fragments"] += 1
        ct = _norm(content)
        lo = bisect.bisect_left(ts_list, fts - 300)
        hi = bisect.bisect_right(ts_list, fts + 300)
        cands = [i for i in range(lo, hi) if len(ms[i][1]) >= 30 and ms[i][1] in ct]
        if not cands:
            out["no_heuristic_match"] += 1
            continue
        if len(cands) > 1:
            out["ambiguous"] += 1
            continue
        out["unique"] += 1
        i = cands[0]
        if ms[i][0] >= fts:
            out["frag_before_own_moment"] += 1
            gaps.append(ms[i][0] - fts)
        # the moment current at store time = latest moment with ts <= fts
        j = bisect.bisect_right(ts_list, fts) - 1
        if j == i:
            out["own"] += 1
        elif j == i - 1:
            out["lag1"] += 1
        else:
            out["other"] += 1
    if gaps:
        gaps.sort()
        out["gap_s_median"] = round(gaps[len(gaps) // 2], 1)
    if out["unique"]:
        out["share_lag1"] = round(out["lag1"] / out["unique"], 4)
        out["share_own"] = round(out["own"] / out["unique"], 4)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", required=True, help="a COPY of the memory DB (opened read-only)")
    ap.add_argument("--moments", required=True)
    ap.add_argument("--since-days", type=float, default=14.0)
    a = ap.parse_args(argv)
    print(json.dumps(measure(Path(a.db), Path(a.moments), a.since_days), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

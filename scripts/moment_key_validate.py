"""J-3246 / D-0634: score the old text-prefix + time heuristic against the exact moment key.

READ-ONLY. Run it a few weeks after the J-3246 restart, when fragment_context.moment_ts has accrued.

The exact key: fragment_context.moment_ts (core.moment.current()['ts'] at store_fragment time). The heuristic it
replaces (docs/lab/tuple_join_integrity_2026-10-31.md sec 6): a moment and an inner_thought fragment match when the
moment's normalised thought[:70] (>= 30 chars) is a substring of the fragment's content within +/-300 s of the
fragment's timestamp and EXACTLY ONE moment qualifies.

For every stamped inner_thought fragment with a unique heuristic moment it reports whether the stamp is
  exact  -- the stamp IS the heuristic's moment            (heuristic right, stamp is the fragment's own moment)
  lag1   -- the stamp is the moment BEFORE the heuristic's (the fragment was stored just before its own moment was
            bound: store_fragment runs at inner_monologue_node.py ~5653, moment.record at ~5923, so this is the
            EXPECTED value for fresh inner thoughts; it is not a heuristic error, it is a stamp-ordering fact)
  other  -- anything else
and the D-0634 defeater verdict: heuristic >= 99 percent right.

    python scripts/moment_key_validate.py [--db PATH] [--moments PATH] [--since TS] [--json]
Defaults: the live DB (opened mode=ro) and data/moments.jsonl next to this tree.
"""
from __future__ import annotations

import argparse
import bisect
import json
import sqlite3
import sys
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
LIVE_DB = TREE / "data" / "memory" / "nascence.db"
LIVE_MOMENTS = TREE / "data" / "moments.jsonl"


def _norm(s) -> str:
    return " ".join((s or "").split())


def load_moments(path: Path):
    ms = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                m = json.loads(line)
            except Exception:
                continue
            if m.get("ts") is None:
                continue
            ms.append((float(m["ts"]), _norm(m.get("thought"))[:70]))
    ms.sort()
    return ms


def validate(db: Path, moments: Path, since: float = 0.0) -> dict:
    ms = load_moments(moments)
    ts_list = [m[0] for m in ms]
    out = {"db": str(db), "moments": len(ms), "stamped_fragments": 0, "stamped_by_origin": {},
           "inner_thought_stamped": 0, "heuristic_unique": 0, "heuristic_none": 0, "heuristic_ambiguous": 0,
           "exact": 0, "lag1": 0, "other": 0,
           # J-3479: own_moment_ts (the moment this fragment's OWN cycle bound, stamped after moment.record).
           # own_exact = the stamp IS the heuristic's moment; own_other = a stamp that disagrees (a real defect).
           "own_moment_ts_stamped": 0, "own_unique": 0, "own_exact": 0, "own_other": 0}
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(fragment_context)")]
        if "moment_ts" not in cols:
            out["error"] = "fragment_context has no moment_ts column (J-3246 not live on this DB yet)"
            return out
        for o, n in conn.execute(
                "SELECT mf.origin, COUNT(*) FROM fragment_context fc JOIN memory_fragments mf "
                "ON mf.fragment_id = fc.fragment_id WHERE fc.moment_ts IS NOT NULL AND fc.moment_ts >= ? "
                "GROUP BY mf.origin", (since,)):
            out["stamped_by_origin"][o] = n
            out["stamped_fragments"] += n
        has_own = "own_moment_ts" in cols
        if has_own:
            out["own_moment_ts_stamped"] = conn.execute(
                "SELECT COUNT(*) FROM fragment_context WHERE own_moment_ts IS NOT NULL AND own_moment_ts >= ?",
                (since,)).fetchone()[0]
        rows = conn.execute(
            "SELECT fc.moment_ts, mf.timestamp, mf.content" + (", fc.own_moment_ts" if has_own else ", NULL") + " FROM fragment_context fc JOIN memory_fragments mf "
            "ON mf.fragment_id = fc.fragment_id WHERE fc.moment_ts IS NOT NULL AND fc.moment_ts >= ? "
            "AND mf.origin = 'inner_thought' AND fc.source LIKE 'experienced:%'", (since,)).fetchall()
    finally:
        conn.close()
    for mts, fts, content, own_ts in rows:
        out["inner_thought_stamped"] += 1
        ct = _norm(content)
        lo = bisect.bisect_left(ts_list, fts - 300)
        hi = bisect.bisect_right(ts_list, fts + 300)
        cands = [i for i in range(lo, hi) if len(ms[i][1]) >= 30 and ms[i][1] in ct]
        if not cands:
            out["heuristic_none"] += 1
            continue
        if len(cands) > 1:
            out["heuristic_ambiguous"] += 1
            continue
        out["heuristic_unique"] += 1
        i = cands[0]
        if own_ts is not None:
            out["own_unique"] += 1
            out["own_exact" if abs(ms[i][0] - own_ts) < 1e-6 else "own_other"] += 1
        if abs(ms[i][0] - mts) < 1e-6:
            out["exact"] += 1
        elif i > 0 and abs(ms[i - 1][0] - mts) < 1e-6:
            out["lag1"] += 1
        else:
            out["other"] += 1
    u = out["heuristic_unique"]
    if u:
        out["share_exact"] = round(out["exact"] / u, 4)
        out["share_exact_or_lag1"] = round((out["exact"] + out["lag1"]) / u, 4)
        out["defeater_met_99pct"] = out["share_exact_or_lag1"] >= 0.99
    if out["own_unique"]:
        out["share_own_exact"] = round(out["own_exact"] / out["own_unique"], 4)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", default=str(LIVE_DB))
    ap.add_argument("--moments", default=str(LIVE_MOMENTS))
    ap.add_argument("--since", type=float, default=0.0, help="only fragments stamped at/after this unix ts")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = validate(Path(a.db), Path(a.moments), a.since)
    print(json.dumps(res, indent=2))
    return 1 if res.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())

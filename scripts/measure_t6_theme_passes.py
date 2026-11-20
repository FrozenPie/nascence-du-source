"""J-3055 (P-0060, F-3764): measure T6 theme-update model calls per day, before and after the gate.

  python scripts/measure_t6_theme_passes.py log     [--nascence-log P] [--sc-log P]
  python scripts/measure_t6_theme_passes.py replay  [--db P] [--days N]

`log`    BEFORE: 'T6 theme updated' lines per day in nascence.log (one line = one successful update call;
         failed calls log 'T6 update LLM call failed'). AFTER: the T6_pass rows nodes/subconscious_node.py
         now writes to subconscious_log.jsonl (formed / skipped_no_new / merged_clusters / failed per pass).
         This is the named READER of those rows (write-only law).
`replay` OFFLINE estimate of the new rule against the real epochs: walks 2-hour passes over the last N days,
         window = newest 50 epochs formed by then, the module's own _cluster_epochs and _t6_match_theme, themes
         seeded from the current memory_themes (their centroids; member ids restricted to epochs formed before
         the start). Counts update calls the OLD rule would make (every matched cluster) against the NEW rule
         (merge same-theme clusters, skip when no epoch id outside the theme's members). It is a model, not a
         measurement: it cannot know which pass really ran. Read-only; never writes the DB.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
LIVE = Path(r"C:\Nascence\data")


def day(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def cmd_log(a) -> int:
    upd = collections.Counter()
    fail = collections.Counter()
    p = Path(a.nascence_log)
    if p.exists():
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if "T6 theme updated" in line:
                    upd[line[:10]] += 1
                elif "T6 update LLM call failed" in line:
                    fail[line[:10]] += 1
    rows = collections.defaultdict(lambda: collections.Counter())
    q = Path(a.sc_log)
    if q.exists():
        with open(q, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"T6_pass"' not in line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                d = day(r["ts"])
                rows[d]["passes"] += 1
                for k in ("formed", "skipped_no_new", "merged_clusters", "failed", "renamed"):
                    rows[d][k] += int(r.get(k, 0))
    days = sorted(set(upd) | set(rows))[-a.days:]
    print(f"{'day':<11}{'log: updated':>13}{'log: failed':>12}  |  {'passes':>6}{'formed':>7}{'skipped':>8}{'merged':>7}{'failed':>7}{'renamed':>8}")
    for d in days:
        r = rows.get(d, {})
        print(f"{d:<11}{upd.get(d, 0):>13}{fail.get(d, 0):>12}  |  {r.get('passes', 0):>6}{r.get('formed', 0):>7}"
              f"{r.get('skipped_no_new', 0):>8}{r.get('merged_clusters', 0):>7}{r.get('failed', 0):>7}{r.get('renamed', 0):>8}")
    return 0


def cmd_replay(a) -> int:
    import numpy as np
    import core  # noqa: F401  -- before node import
    import nodes.subconscious_node as scn
    from core.memory.store import _blob_to_vec

    uri = "file:" + Path(a.db).as_posix() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    ep_rows = con.execute("SELECT * FROM memory_epochs WHERE embedding IS NOT NULL").fetchall()
    themes = con.execute("SELECT * FROM memory_themes").fetchall()
    con.close()
    if not ep_rows:
        print("no epochs")
        return 1
    t_end = max(r["formed_at"] for r in ep_rows)
    t0 = t_end - a.days * 86400
    # simulated theme state
    sim = []
    for th in themes:
        try:
            mem = set(json.loads(th["member_epoch_ids"] or "[]"))
        except Exception:
            mem = set()
        formed = {r["epoch_id"]: r["formed_at"] for r in ep_rows}
        mem = {m for m in mem if formed.get(m, 0) <= t0}
        sim.append({"theme_id": th["theme_id"], "name": th["theme_name"],
                    "centroid": th["centroid"], "member_epoch_ids": json.dumps(sorted(mem))})

    old_calls = collections.Counter()
    new_calls = collections.Counter()
    skipped = collections.Counter()
    unmatched = collections.Counter()
    t = t0
    node = None
    while t <= t_end:
        win = sorted((r for r in ep_rows if r["formed_at"] <= t), key=lambda r: r["timestamp_start"], reverse=True)[:50]
        # only a pass when an epoch has formed since the previous pass (the existing gate)
        new_since = [r for r in win if r["formed_at"] > t - 7200]
        if len(win) >= 2 and new_since:
            clusters = [c for c in scn.SubconsciousNode._cluster_epochs(node, win) if len(c) >= 2]
            groups: dict = {}
            n_matched_clusters = 0
            for c in clusters:
                cen, ids, mset = scn.SubconsciousNode._t6_cluster_stats(c)
                tid = scn.SubconsciousNode._t6_match_theme(cen, mset, sim)
                if tid is None:
                    unmatched[day(t)] += 1
                    continue
                n_matched_clusters += 1
                groups.setdefault(tid, []).extend(e for e in c if e["epoch_id"] not in {x["epoch_id"] for x in groups.get(tid, [])})
            old_calls[day(t)] += n_matched_clusters
            for tid, merged in groups.items():
                s = next(x for x in sim if x["theme_id"] == tid)
                prior = set(json.loads(s["member_epoch_ids"]))
                if any(e["epoch_id"] not in prior for e in merged):
                    new_calls[day(t)] += 1
                    cen, ids, _ = scn.SubconsciousNode._t6_cluster_stats(merged)
                    s["member_epoch_ids"] = json.dumps(ids)
                    s["centroid"] = cen.astype(np.float32).tobytes()
                else:
                    skipped[day(t)] += 1
        t += 7200
    days = sorted(set(old_calls) | set(new_calls))
    print(f"replay over {a.days} days ending {day(t_end)}, 2-hourly passes, {len(themes)} themes, {len(ep_rows)} epochs")
    print(f"{'day':<11}{'OLD rule calls':>15}{'NEW rule calls':>15}{'skipped':>9}{'unmatched clusters':>20}")
    for d in days:
        print(f"{d:<11}{old_calls[d]:>15}{new_calls[d]:>15}{skipped[d]:>9}{unmatched[d]:>20}")
    print(f"{'TOTAL':<11}{sum(old_calls.values()):>15}{sum(new_calls.values()):>15}{sum(skipped.values()):>9}{sum(unmatched.values()):>20}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("log")
    l.add_argument("--nascence-log", default=str(LIVE / "nascence.log"))
    l.add_argument("--sc-log", default=str(LIVE / "subconscious_log.jsonl"))
    l.add_argument("--days", type=int, default=14)
    r = sub.add_parser("replay")
    r.add_argument("--db", default=str(LIVE / "memory" / "nascence.db"))
    r.add_argument("--days", type=int, default=14)
    a = ap.parse_args()
    return cmd_log(a) if a.cmd == "log" else cmd_replay(a)


if __name__ == "__main__":
    sys.exit(main())

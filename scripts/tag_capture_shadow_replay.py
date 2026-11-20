"""
Harness for core/tag_capture_shadow.py (J-2582, I-0107, F-3315). Read-only on the live tree. Zero LLM.

Replays every real past sleep since 2026-10-16 (the F-3315 window) through tag_capture_shadow.compute_night() against
READ-ONLY COPIES of the inputs (night_log, hands_trace, nascence.log, recall_wager_shadow, retractions, and a slice of
memory_fragments copied out of nascence.db opened mode=ro), inside lab_env.isolate(db="empty") with the module's
_SHADOW redirected into the lab dir. Also checks the flag-off no-op and one flag-on end-to-end write.

Run from a THROWAWAY worktree (core must resolve inside it):
  python scripts/tag_capture_shadow_replay.py --src C:\\Nascence --lab-root <scratch dir> --out <scratch>.jsonl

FALSIFIED IF (declared in the module header): > 50% of picks share one hand family, OR the median per-night
capture_rate (nights with n_low > 0) is above 0.5.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  -- BEFORE lab_env (F-2570-era lab_env sys.path hijack)
assert Path(core.__file__).resolve().is_relative_to(TREE), f"core resolved outside the tree: {core.__file__}"
from core import tag_capture_shadow as tcs  # noqa: E402

sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env  # noqa: E402

WINDOW_START = datetime(2026, 10, 16, 0, 0).timestamp()
COPY = ["night_log.jsonl", "hands_trace.jsonl", "nascence.log", "logs/recall_wager_shadow.jsonl", "retractions.jsonl"]


def nights(night_log: Path) -> list[dict]:
    rows = []
    for line in night_log.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    rows.sort(key=lambda r: float(r.get("ts") or 0))
    out, prev_end = [], None
    for r in rows:
        ts = float(r.get("ts") or 0)
        start = max(prev_end or 0.0, ts - tcs.BLOCK_CAP_S)
        prev_end = ts + float(r.get("duration_s") or 0)
        if ts >= WINDOW_START:
            out.append({"ts": ts, "start": start, "kind": r.get("kind")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=r"C:\Nascence")
    ap.add_argument("--lab-root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = Path(a.src) / "data"
    out = Path(a.out)
    for p in (Path(a.lab_root), out):
        if str(p.resolve()).lower().startswith(str(src.resolve()).lower()):
            raise SystemExit("refusing to write under the live data/ tree")
    lab_env._LAB_ROOT = Path(a.lab_root)          # keep isolate()'s lab dir out of the live data/ tree
    with lab_env.isolate(db="empty", also=[(tcs, ["_SHADOW"])]) as lab:
        assert Path(tcs._SHADOW).resolve().is_relative_to(Path(lab).resolve()), tcs._SHADOW
        checks = {}
        tcs.TAG_CAPTURE_SHADOW = False
        checks["flag_off_returns_none"] = tcs.record_night(0.0, 1.0) is None
        checks["flag_off_wrote_nothing"] = not Path(tcs._SHADOW).exists()
        ro = Path(lab) / "ro"
        for rel in COPY:
            (ro / "data" / rel).parent.mkdir(parents=True, exist_ok=True)
            if (src / rel).exists():
                shutil.copyfile(src / rel, ro / "data" / rel)
        ns = nights(ro / "data" / "night_log.jsonl")
        t0 = min(n["start"] for n in ns)
        slice_db = ro / "data" / "memory" / "slice.db"
        slice_db.parent.mkdir(parents=True, exist_ok=True)
        live = sqlite3.connect(f"file:{(src / 'memory' / 'nascence.db').as_posix()}?mode=ro", uri=True, timeout=30)
        rows = live.execute("SELECT fragment_id, timestamp, origin, importance, replay_count, chapter_id, layer "
                            "FROM memory_fragments WHERE layer='episodic' AND timestamp > ?", (t0,)).fetchall()
        live.close()
        sc = sqlite3.connect(slice_db)
        sc.execute("CREATE TABLE memory_fragments (fragment_id TEXT, timestamp REAL, origin TEXT, importance REAL, "
                   "replay_count INTEGER, chapter_id TEXT, layer TEXT)")
        sc.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?)", rows)
        sc.execute("CREATE INDEX ix_ts ON memory_fragments(timestamp)")
        sc.commit()
        sc.close()
        results = []
        with open(out, "w", encoding="utf-8") as fo:
            for n in ns:
                r = tcs.compute_night(n["start"], n["ts"], root=ro, db_path=slice_db, exclude_top_k=True, kind=n["kind"])
                r["night"] = datetime.fromtimestamp(n["ts"]).strftime("%m-%d %H:%M")
                results.append(r)
                fo.write(json.dumps(r) + "\n")
        tcs.TAG_CAPTURE_SHADOW = True
        try:
            row = tcs.record_night(t0, t0 + 3600, "test")
        finally:
            tcs.TAG_CAPTURE_SHADOW = False
        checks["flag_on_wrote_one_row_in_lab"] = (row is not None and Path(tcs._SHADOW).exists()
                                                  and len(Path(tcs._SHADOW).read_text(encoding="utf-8").splitlines()) == 1)
        live_rates = [r["capture_rate"] for r in results if r["n_low"]]
        nulls = [r["null_capture_rate"] for r in results if r["null_capture_rate"] is not None]
        picks = [p for r in results for p in r["picks"]]
        fam = Counter(p["hand_family"] for p in picks)
        top_share = (fam.most_common(1)[0][1] / len(picks)) if picks else None
        summ = {
            "checks": checks, "slice_rows": len(rows), "nights": len(results),
            "nights_with_low": len(live_rates), "nights_with_picks": sum(1 for r in results if r["picks"]),
            "n_low_total": sum(r["n_low"] for r in results), "n_tagged_total": sum(r["n_tagged"] for r in results),
            "pooled_capture_rate": round(sum(r["n_tagged"] for r in results) / max(1, sum(r["n_low"] for r in results)), 4),
            "median_capture_rate": round(statistics.median(live_rates), 4) if live_rates else None,
            "max_capture_rate": max(live_rates) if live_rates else None,
            "nights_rate_gt_0_5": sum(1 for x in live_rates if x > 0.5),
            "median_null_rate": round(statistics.median(nulls), 4) if nulls else None,
            "nights_rate_gt_null": sum(1 for r in results if r["null_capture_rate"] is not None
                                       and r["capture_rate"] > r["null_capture_rate"]),
            "events_raw": sum(r["n_events_raw"] for r in results), "events_after": sum(r["n_events"] for r in results),
            "refusals_collapsed": sum(r["n_refusals_collapsed"] for r in results),
            "n_picks": len(picks), "hand_family_counts": dict(fam.most_common()),
            "top_family_share": round(top_share, 3) if top_share is not None else None,
            "pick_event_kinds": dict(Counter(k for p in picks for k in p["event_kinds"]).most_common()),
        }
        summ["falsified_one_hand"] = bool(top_share is not None and top_share > 0.5)
        summ["falsified_nonselective"] = bool(live_rates and statistics.median(live_rates) > 0.5)
        with open(out, "a", encoding="utf-8") as fo:
            fo.write(json.dumps({"summary": summ}) + "\n")
        for r in results:
            print(r["night"], r["kind"], "low", r["n_low"], "ev", r["n_events_raw"], "->", r["n_events"], "tag",
                  r["n_tagged"], "rate", r["capture_rate"], "null", r["null_capture_rate"],
                  [(p["hand_family"], p["score"]) for p in r["picks"]])
        print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()

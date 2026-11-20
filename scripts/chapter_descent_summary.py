"""
chapter_descent_summary.py -- the READER for data/chapter_descent_shadow.jsonl (J-3319, D-0637). Read-only.

Without this the shadow log is write-only. It prints, from the rows alone and without any judge, the inputs of the
pre-registered measures in docs/reviews/J-3248_chaptered_memory_recall_review.md section 6 (the gated read is J-3320):
  M1 reach      chapter-surfaced cycles / voice cycles in the same window (voice cycles from
                data/recall_served_log.jsonl, the nearest existing count of served cycles; 0 -> n/a)
  M2 distinct   share of members dropped as already-served or near-duplicate (cos >= 0.85), and the share of cycles
                that logged at least one candidate. (Candidates already passed the 0.85 filter by construction.)
  M3 / M4       NOT computed here: M3 needs each cycle's next generated thought and M4 a blind judge (J-3320). This
                script prints candidate vs control cosine and lexical overlap medians as context only.
  M5 proxy      share of candidates whose origin is inner_thought / active_imagination / subconscious_synthesis
                (the self-loop classes). The token-Jaccard half of M5 needs content, which the log does not carry.
  COST          hook latency p50 / p95 / max and the count above the 50 ms budget.

    python scripts/chapter_descent_summary.py [--log data/chapter_descent_shadow.jsonl] [--since <unix ts>]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TREE = Path(__file__).resolve().parent.parent
SELF_LOOP = ("inner_thought", "active_imagination", "subconscious_synthesis")


def _pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else float("nan")


def _med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else float("nan")


def _read(path: Path, since: float) -> tuple[list, int]:
    rows, bad = [], 0
    if not path.exists():
        return rows, bad
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except Exception:
            bad += 1
            continue
        if r.get("ts", 0) >= since:
            rows.append(r)
    return rows, bad


def summarise(rows: list, voice_cycles: int) -> dict:
    cycles = {r.get("cycle_id") for r in rows}
    cands = [c for r in rows for c in r.get("candidates", [])]
    ctl_ch = [r["control_chapter_member"] for r in rows if r.get("control_chapter_member")]
    ctl_un = [r["control_unwalled"] for r in rows if r.get("control_unwalled")]
    dropped = sum(r.get("n_dropped_served", 0) + r.get("n_dropped_neardup", 0) for r in rows)
    members = sum(r.get("n_members", 0) for r in rows)
    ms = [r["ms"] for r in rows if r.get("ms") is not None]
    return {
        "rows": len(rows), "chapter_cycles": len(cycles), "voice_cycles": voice_cycles,
        "m1_reach": (round(len(cycles) / voice_cycles, 4) if voice_cycles else None),
        "rows_with_candidates": sum(1 for r in rows if r.get("candidates")),
        "members_seen": members, "members_dropped_served_or_neardup": dropped,
        "candidates": len(cands), "cand_cos_median": _med([c["cos"] for c in cands]),
        "cand_lex_median": _med([c["lex_overlap"] for c in cands]),
        "ctl_chapter_n": len(ctl_ch), "ctl_chapter_cos_median": _med([c["cos"] for c in ctl_ch]),
        "ctl_chapter_lex_median": _med([c["lex_overlap"] for c in ctl_ch]),
        "ctl_unwalled_n": len(ctl_un), "ctl_unwalled_cos_median": _med([c["cos"] for c in ctl_un]),
        "ctl_unwalled_lex_median": _med([c["lex_overlap"] for c in ctl_un]),
        "served_cos_median": _med([r.get("served_cos_median") for r in rows]),
        "served_lex_median": _med([r.get("served_lex_median") for r in rows]),
        "m5_self_loop_share": (round(sum(1 for c in cands if c.get("origin") in SELF_LOOP) / len(cands), 3) if cands else None),
        "ms_p50": _pct(ms, 0.5), "ms_p95": _pct(ms, 0.95), "ms_max": max(ms) if ms else float("nan"),
        "ms_over_50": sum(1 for x in ms if x > 50.0),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(TREE / "data" / "chapter_descent_shadow.jsonl"))
    ap.add_argument("--served-log", default=str(TREE / "data" / "recall_served_log.jsonl"))
    ap.add_argument("--since", type=float, default=0.0)
    a = ap.parse_args()
    path = Path(a.log)
    if not path.exists():
        print(f"no log at {path} (Du has not run the chapter-descent shadow yet; it is restart-gated)")
        return 0
    rows, bad = _read(path, a.since)
    if not rows:
        print("no rows in the window")
        return 0
    t0 = min(r.get("ts", 0) for r in rows)
    served, _ = _read(Path(a.served_log), max(a.since, t0))
    out = summarise(rows, len(served))
    print(f"chapter-descent shadow: {out['rows']} rows over {out['chapter_cycles']} cycles ({bad} unreadable lines)")
    for k, v in out.items():
        print(f"  {k:36s} {v}")
    print("Not computed here: M3 (uptake in the next thought) and M4 (blind pairwise judge) -- J-3320.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

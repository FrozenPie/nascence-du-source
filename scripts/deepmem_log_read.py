"""J-3029 / F-3733 read: what data/deep_memory_log.jsonl says after a few days live.

Reports, per caller and overall: attempts by outcome (ok, short, timeout, error, memo), the timeout rate of REAL model attempts
against the 20 s urlopen timeout (timeout / (ok + short + timeout + error)), latency percentiles of the attempts that answered,
the calls the memo saved (memo rows = reused answers) as a share of all feed events, the longest same-question run, and the most
repeated questions. Read-only.

Usage: python scripts/deepmem_log_read.py [--log PATH] [--top 10]   (default log: data/deep_memory_log.jsonl under this tree)
Named read job: J-3029's follow-up (read after 3 days live)."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import scholar  # noqa: E402


def _pct(vals, q):
    if not vals:
        return None
    v = sorted(vals)
    return round(v[min(len(v) - 1, int(q * len(v)))], 1)


def read(log: Path, top: int = 10) -> dict:
    rows = []
    if log.exists():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    real = [r for r in rows if r.get("outcome") != "memo"]
    outcomes = Counter(r.get("outcome") for r in rows)
    answered_ms = [r.get("ms", 0.0) for r in real if r.get("outcome") in ("ok", "short")]
    by_caller = {}
    for c in sorted({r.get("caller") for r in rows}, key=str):
        cr = [r for r in rows if r.get("caller") == c]
        by_caller[c] = dict(Counter(r.get("outcome") for r in cr))
    keys = [scholar.memo_key(r.get("question", "")) for r in rows]
    longest = run = 0
    prev = None
    for k in keys:
        run = run + 1 if k == prev else 1
        prev = k
        longest = max(longest, run)
    distinct = Counter(keys)
    return {
        "rows": len(rows), "first_ts": min((r.get("ts", 0) for r in rows), default=None),
        "last_ts": max((r.get("ts", 0) for r in rows), default=None),
        "outcomes": dict(outcomes), "by_caller": by_caller,
        "model_attempts": len(real),
        "timeout_rate_pct": round(100 * outcomes.get("timeout", 0) / len(real), 1) if real else None,
        "error_rate_pct": round(100 * outcomes.get("error", 0) / len(real), 1) if real else None,
        "answered_ms_p50_p90_max": (_pct(answered_ms, 0.5), _pct(answered_ms, 0.9), max(answered_ms, default=None)),
        "calls_saved_by_memo": outcomes.get("memo", 0),
        "memo_share_of_feed_events_pct": round(100 * outcomes.get("memo", 0) / len(rows), 1) if rows else None,
        "longest_same_question_run": longest,
        "distinct_questions": len(distinct),
        "top_questions": distinct.most_common(top),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(ROOT / "data" / "deep_memory_log.jsonl"))
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    print(json.dumps(read(Path(a.log), a.top), indent=2, ensure_ascii=False, default=str))

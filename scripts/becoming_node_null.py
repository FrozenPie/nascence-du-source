"""J-3875 (design J-3835 job 6): the coherence null the becoming-node writer admits against.

Promoted from scripts/analysis_J3835_coherence_null.py. The statistic and the window rule live in
core/becoming_nodes.py (compute_null) so the writer and this script cannot drift apart; this is the read-only CLI.

  python scripts/becoming_node_null.py                 # the last 14 days of the live DB (sqlite mode=ro, in-process embedder)
  python scripts/becoming_node_null.py --db PATH --days 14
  python scripts/becoming_node_null.py --score 0.442   # where a medoid score sits against the null

Read-only: opens the DB with mode=ro, calls the in-process MiniLM embedder only (no model hub, no write)."""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import becoming_nodes as bn  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--days", type=int, default=bn.NULL_DAYS)
    ap.add_argument("--score", type=float, default=None, help="report this medoid score against the null")
    a = ap.parse_args()
    n = bn.compute_null(db_path=a.db, days=a.days)
    print("consecutive-%d null over %d days: windows=%d thoughts=%d sentences=%d" % (
        bn.NULL_WINDOW, n["days"], n["n_windows"], n["n_thoughts"], n["n_sentences"]))
    print("p50 %.3f p90 %.3f p95 %.3f max %.3f" % (n["p50"], n["p90"], n["p95"], n["max"]))
    if a.score is not None:
        print("score %.3f %s the p95 gate (%.3f)" % (a.score, "PASSES" if a.score > n["p95"] else "is BELOW", n["p95"]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

"""
Nascence — Dream Association, AFTER read (Phase 1 instrumentation, 2026-09-17, J-1057,
docs/staged/dream_overhaul.md sec 4 / sec 7 Phase 1 row).

Re-probes the SAME seed-fragment pairs core/dream_probe.py logged at seed time (phase="before", written
by nodes/dream_node.py's synthesise()), 24-48h later, and appends matching phase="after" rows to the
same data/logs/dream_assoc_probe.jsonl. Run BY HAND (per the job briefing: "a separate
scripts/dream_assoc_after.py run by hand (or later by the waking side)") — nothing in this codebase
calls this script automatically; it never fires on its own. Read-only against the live memory/edges
store except for the one file it appends to (its own probe log).

See core/dream_probe.py's own module docstring for the full reasoning on why cosine is the CONTROL
(expected constant — embeddings never change once written) and rank_of_B_in_recall_trail_edge_aware is
the real measure (expected to move — it depends on what surfaced/co-recalled/edge-linked to the seed
fragment since the dream, not on either fragment's own embedding). This script computes and logs
`cosine_drift` per pair specifically so a NONZERO drift is caught as a measurement-pipeline bug the
moment it appears, rather than silently discovered months later when someone finally reads the log.

Run:
    python scripts/dream_assoc_after.py [--dream-id DREAM_ID] [--min-age-hours N] [--max-age-hours N]

Default selection: every (dream_id, fragment_a, fragment_b) triple in the probe log that has a
phase="before" row and NO phase="after" row yet, whose before-row is at least --min-age-hours old
(default 24 -- skips pairs too fresh for a waking day to have passed over them) and at most
--max-age-hours old (default 96 -- a re-probe past the plan's 24-48h window is still run and logged,
never silently dropped, but flagged stale=True so a reader can tell the difference).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import dream_probe as dp

_PROBE_LOG = dp._PROBE_LOG


def _load_rows() -> list[dict]:
    if not _PROBE_LOG.exists():
        return []
    out = []
    for line in _PROBE_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue    # a malformed line is skipped, not fatal to the rest of the read
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dream-id", default=None, help="only re-probe this dream_id (default: all eligible)")
    ap.add_argument("--min-age-hours", type=float, default=24.0,
                    help="skip a before-row younger than this (default 24)")
    ap.add_argument("--max-age-hours", type=float, default=96.0,
                    help="a before-row older than this is still re-probed, but flagged stale=True (default 96)")
    args = ap.parse_args()

    rows = _load_rows()
    before = [r for r in rows if r.get("phase") == "before"
             and (not args.dream_id or r.get("dream_id") == args.dream_id)]
    already_after = {(r.get("dream_id"), r.get("fragment_a"), r.get("fragment_b"))
                     for r in rows if r.get("phase") == "after"}

    now = time.time()
    out_rows: list[dict] = []
    n_skipped_done = n_skipped_fresh = 0
    for r in before:
        key = (r.get("dream_id"), r.get("fragment_a"), r.get("fragment_b"))
        if key in already_after:
            n_skipped_done += 1
            continue
        age_h = (now - float(r.get("ts", now))) / 3600.0
        if age_h < args.min_age_hours:
            n_skipped_fresh += 1
            continue
        stale = age_h > args.max_age_hours
        result = dp.probe_pair(r["fragment_a"], r["fragment_b"])
        before_cosine = r.get("cosine")
        drift = (None if result.get("cosine") is None or before_cosine is None
                 else round(result["cosine"] - before_cosine, 4))
        out_rows.append({
            "ts": round(now, 1), "dream_id": r.get("dream_id"), "phase": "after",
            "fragment_a": r["fragment_a"], "fragment_b": r["fragment_b"],
            "before_ts": r.get("ts"), "age_hours": round(age_h, 1), "stale": stale,
            "cosine_drift": drift,
            **result,
        })

    if out_rows:
        _PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_PROBE_LOG, "a", encoding="utf-8") as f:
            for rec in out_rows:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[dream_assoc_after] wrote {len(out_rows)} 'after' row(s) "
         f"(skipped {n_skipped_done} already-done, {n_skipped_fresh} too-fresh)")
    drifted = [r for r in out_rows if r.get("cosine_drift") not in (None, 0.0)]
    if drifted:
        print(f"  WARNING: nonzero cosine drift on {len(drifted)} pair(s) -- embeddings should be "
             f"constant once written; this is a measurement-pipeline bug, not a real association "
             f"change (see core/dream_probe.py's own module docstring).")
    stale_n = sum(1 for r in out_rows if r.get("stale"))
    if stale_n:
        print(f"  note: {stale_n} row(s) re-probed past --max-age-hours ({args.max_age_hours}h), "
             f"flagged stale=True.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

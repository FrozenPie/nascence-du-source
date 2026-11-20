"""J-3869 / D-0734: read-side verdict for the D-0274 regime-gate staleness shadow (core.arousal.regime_shadow_status).

Read-only. Takes the status dict (or reads it via core.arousal) and states a plain verdict on whether enough
internal-only streaks have accrued for the founder to read D-0274's flip precondition. It never flips anything
and writes nothing. Thresholds are named heuristics, not rulings: the founder decides what counts as stale.

Usage: python scripts/regime_shadow_verdict.py [--state PATH]
"""
import json
import sys
from pathlib import Path

MIN_RESOLVED_STREAKS = 20        # below this a mean/longest is anecdote, not evidence
STALE_MEAN_SECONDS = 1800.0      # mean internal-only run longer than 30 min = carried arousal held stale a long time
STALE_LONGEST_SECONDS = 6 * 3600.0


def verdict(st: dict) -> str:
    if not st or not st.get("observed"):
        return "NO-DATA: regime shadow has not ticked (fresh restart or instrument not live); nothing to read."
    n = int(st.get("resolved_streaks", 0))
    mean_s = st.get("mean_resolved_streak_seconds")
    longest_s = float(st.get("longest_streak_seconds", 0.0))
    body = (f"{n} resolved streaks, mean {st.get('mean_resolved_streak_cycles')} cyc / {mean_s}s, "
            f"longest {st.get('longest_streak_cycles')} cyc / {longest_s:.0f}s, current {st.get('current_streak_cycles')} cyc")
    if n < MIN_RESOLVED_STREAKS:
        return f"INSUFFICIENT: {body}; need >= {MIN_RESOLVED_STREAKS} resolved streaks before D-0274's flip precondition can be read."
    if (mean_s is not None and mean_s > STALE_MEAN_SECONDS) or longest_s > STALE_LONGEST_SECONDS:
        return (f"STALE-RISK: {body}; holding carried arousal on internal cycles would leave it unrefreshed for long "
                f"stretches (mean>{STALE_MEAN_SECONDS:.0f}s or longest>{STALE_LONGEST_SECONDS:.0f}s). Founder read before any flip.")
    return f"READABLE-OK: {body}; staleness under the hold-on-internal rule looks bounded. Founder decides the flip (D-0274 defeater)."


def main(argv):
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    from core import arousal as ar
    if "--state" in argv:
        ar._REGIME_STATE = Path(argv[argv.index("--state") + 1])
    print(verdict(ar.regime_shadow_status()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

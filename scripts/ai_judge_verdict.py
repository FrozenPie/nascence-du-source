"""J-3870 / D-0734: read-side verdict for the active-imagination judge shadow (nodes.subconscious_node.active_imagination_judge_status).

Read-only. Takes the status dict (or reads it via the node module) and states a plain verdict on whether the
independent judge_panel signal ever disagrees with the mechanical echo-distance floor on kept contemplations.
It changes nothing and writes nothing. Thresholds are named heuristics, not rulings.

Usage: python scripts/ai_judge_verdict.py [--log PATH]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
MIN_JUDGED = 50            # below this a divergence rate is anecdote
MIN_AVAILABLE_SHARE = 0.7  # below this the judge itself is too often unavailable to read
LOW_DIVERGENCE = 0.02      # at or below: judge agrees with the floor almost always (adds nothing yet)


def verdict(st: dict) -> str:
    g = int((st or {}).get("graded", 0))
    if g == 0:
        return "NO-DATA: no judge shadow rows; nothing to read."
    n = int(st.get("judge_available_n", 0))
    share = n / g
    body = (f"{g} graded, {n} judged ({share:.0%} available), {st.get('judge_says_not_genuine')} not-genuine, "
            f"divergence {st.get('divergence_rate')}, echo skips {st.get('ai_echo_skips')}")
    if share < MIN_AVAILABLE_SHARE:
        return f"JUDGE-UNAVAILABLE: {body}; judge outage is too frequent to read a divergence rate."
    if n < MIN_JUDGED:
        return f"INSUFFICIENT: {body}; need >= {MIN_JUDGED} judged rows."
    if st.get("divergence_rate") is None or st["divergence_rate"] <= LOW_DIVERGENCE:
        return (f"AGREES: {body}; the judge almost never contradicts the echo-distance floor on kept entries "
                f"(floor looks sufficient, or the judge is too lenient to discriminate). Founder read.")
    return f"DIVERGES: {body}; the judge flags a real share of floor-kept entries as not genuine. Founder read."


def main(argv):
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    from core import shadow_log  # noqa: F401  (core before nodes)
    from nodes import subconscious_node as sn
    if "--log" in argv:
        sn._AI_JUDGE_LOG = Path(argv[argv.index("--log") + 1])
    print(verdict(sn.active_imagination_judge_status()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

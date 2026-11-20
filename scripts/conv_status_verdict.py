"""J-3873 / D-0734: read-side consumer for core.self_implication.conv_status().

Read-only: reads data/self_implication_conv_shadow.jsonl through conv_status() (bounded tail read) and prints a
one-paragraph verdict on the conversational self-implication detector: is there enough data, how selective is
it, and how often the draft already retreats. Writes nothing. Usage: python scripts/conv_status_verdict.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MIN_SCANS = 30   # below this the fire rate is anecdote, not a rate


def verdict(st: dict) -> str:
    n, f = st.get("scans", 0), st.get("would_fire", 0)
    if n == 0:
        return "NO DATA: no conversation scans logged yet."
    if n < MIN_SCANS:
        return f"INSUFFICIENT: {n} scans (< {MIN_SCANS}); {f} would-fire. No rate claim."
    rate = f / n
    if f == 0:
        return f"SILENT: {n} scans, 0 would-fire; detector never found a contradicted self-claim."
    return (f"{n} scans, {f} would-fire ({rate:.1%}), mean directness {st['mean_directness']}; "
            f"draft already retreats on {st['retreat_in_draft']}/{f} fires (rate {st['retreat_rate']}).")


if __name__ == "__main__":
    from core import self_implication as si
    print("self-implication conv verdict:", verdict(si.conv_status()))

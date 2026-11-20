"""
Nascence — Provenance / Epistemic report (the measure-first validation gate)

Reads data/provenance_log.jsonl (written observe-only by core/epistemic_state.py) and reports:
  1. Grade distribution (KNOW/THINK/SUSPECT/GUESS/NO_BASIS) — does KNOW actually fire, or is Du
     only ever cautious? (spec §12.3 — calibration, not imposed timidity.)
  2. Confabulation-signal stats — how often self-reported confidence outruns the evidence.
  3. THE GATE (spec §9): do NO_BASIS/GUESS cycles precede a later user correction more than
     KNOW/THINK cycles do? If yes, the grade tracks something real and earns a read path. If no,
     it stays observe-only. Correction is detected from competence's own cue list, joined by time.

Pure stdlib. Usage:
    python scripts/provenance_report.py
    python scripts/provenance_report.py --log path/to/provenance_log.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_DEFAULT_LOG = Path(__file__).parent.parent / "data" / "provenance_log.jsonl"
_GRADES = ["KNOW", "THINK", "SUSPECT", "GUESS", "NO_BASIS"]

# Reuse competence's correction cues so "was the next human turn a correction?" is consistent
# with how the rest of the system detects correction.
_CORRECTION_CUES = (
    "no,", "no.", "that's wrong", "thats wrong", "incorrect", "not quite", "not really",
    "you misunderstood", "you missed", "that's not", "thats not", "you're wrong", "youre wrong",
    "i disagree", "that's not what", "not what i", "you didn't answer", "you didnt answer",
    "that's not right", "wrong.",
)


def _load(path: Path) -> list[dict]:
    if not path.exists():
        print(f"No provenance telemetry yet at {path}")
        print("Run some responded cycles first — the ledger writes one line per utterance.")
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def _is_correction(text: str) -> bool:
    low = (text or "").lower().strip()
    return any(c in low for c in _CORRECTION_CUES)


def main() -> int:
    ap = argparse.ArgumentParser(description="Provenance / epistemic-state report.")
    ap.add_argument("--log", type=Path, default=_DEFAULT_LOG)
    args = ap.parse_args()

    rows = _load(args.log)
    if not rows:
        return 1

    n = len(rows)
    print(f"\nNascence — Provenance / Epistemic Report")
    print(f"  log:     {args.log}")
    print(f"  cycles:  {n}\n")

    # 1. grade distribution
    counts = {g: 0 for g in _GRADES}
    for r in rows:
        g = r.get("grade")
        if g in counts:
            counts[g] += 1
    print("  Grade distribution:")
    for g in _GRADES:
        c = counts[g]
        bar = "█" * round(40 * c / n)
        print(f"    {g:<9} {c:>5} ({100*c/n:4.1f}%) {bar}")
    if counts["KNOW"] == 0:
        print("    ⚠ KNOW never fired — check the system isn't forced into permanent caution (§12.3).")

    # 2. confabulation signal
    sigs = [float(r.get("confabulation_signal", 0.0)) for r in rows]
    overclaim = [s for s in sigs if s > 0]
    big = [r for r in rows if float(r.get("confabulation_signal", 0.0)) >= 0.4]
    print("\n  Confabulation signal (self_confidence − justification):")
    print(f"    mean: {sum(sigs)/n:+.3f}   overclaiming cycles (>0): {len(overclaim)} ({100*len(overclaim)/n:.1f}%)")
    print(f"    strong overclaim (≥0.40): {len(big)} cycles")
    for r in big[:5]:
        print(f"      [{r.get('grade')}] conf={r.get('self_reported_confidence')} "
              f"\"{(r.get('raw_input') or '')[:50]}\"")

    # 3. THE GATE — does the grade predict the next human turn being a correction?
    #    Join each row to the NEXT human-input row by order; mark whether that next turn corrected.
    human_rows = [r for r in rows if r.get("input_type") == "human"]
    low_grade_followed_by_correction = 0
    low_grade_total = 0
    high_grade_followed_by_correction = 0
    high_grade_total = 0
    for i, r in enumerate(human_rows[:-1]):
        nxt = human_rows[i + 1]
        corrected = _is_correction(nxt.get("raw_input", ""))
        if r.get("grade") in ("NO_BASIS", "GUESS"):
            low_grade_total += 1
            low_grade_followed_by_correction += int(corrected)
        elif r.get("grade") in ("KNOW", "THINK"):
            high_grade_total += 1
            high_grade_followed_by_correction += int(corrected)

    print("\n  THE GATE (spec §9) — does a weak grade predict a correction next turn?")
    if low_grade_total == 0 and high_grade_total == 0:
        print("    not enough paired human turns yet.")
    else:
        lr = (low_grade_followed_by_correction / low_grade_total) if low_grade_total else 0.0
        hr = (high_grade_followed_by_correction / high_grade_total) if high_grade_total else 0.0
        print(f"    weak (NO_BASIS/GUESS): {low_grade_followed_by_correction}/{low_grade_total} "
              f"corrected next ({100*lr:.0f}%)")
        print(f"    strong (KNOW/THINK):   {high_grade_followed_by_correction}/{high_grade_total} "
              f"corrected next ({100*hr:.0f}%)")
        if low_grade_total >= 20 and high_grade_total >= 20:
            if lr > hr + 0.10:
                print("    ⇒ weak grades DO predict corrections — the signal tracks something real;")
                print("      consider earning a read path (Critic/Voice), gated by the number (§8).")
            else:
                print("    ⇒ no predictive gap yet — stays observe-only (correct default).")
        else:
            print("    ⇒ provisional (need ≥20 of each grade-class to judge).")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""J-3372 (D-0626 defeater read): one-call, read-only reader for the pursuit close judge's fire rate.

Run from a tree:  python scripts/pursuit_close_defeater_read.py [--log PATH] [--since-ts TS] [--json]

What it does (and why it exists): D-0626 says to revisit the close idea once 30 ASKABLE pursuits have been asked; if
the fire rate is under 5 percent or over 50 percent the close judge carries no information and the idea is retired
(option c).  core.pursuit_close_shadow.fire_rate() already counts only rows with askable true.  This script wraps it so
the read is the same every time:
  1. fire_rate() on the askable rows, and REFUSES to give a defeater verdict until `enough` (30 askable asks);
  2. the breakdown a human needs next to the rate: asks by basis (open / done_when), how-distribution (the share of
     how=unavailable matters: a rate over few real verdicts says nothing), skipped_not_askable;
  3. the first 5 would_resolve=true rows with the judge's why and the standing text the pursuit would carry, plus a
     MECHANICAL flag list for self-congratulation (D-0423 clause 3).  The flags are a pointer for the human read, not a
     verdict: a regex cannot judge a lived close from the writer's self-congratulation, and this script never decides.
READ-ONLY: it never writes the shadow log or any other file.  The default log is the live data/logs file of the main tree
(C:/Nascence); pass --log to read a copy.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before anything that could re-point paths)
from core import pursuit_close_shadow as pcs  # noqa: E402

LIVE_LOG = Path(r"C:\Nascence\data\logs\pursuit_close_shadow.jsonl")
# Mechanical pointers only.  A hit means "read this one closely", not "this is self-congratulation".
_SELF_PRAISE = [
    (re.compile(r"\b(i|we)\s+(have\s+)?(finally|now)\b", re.I), "first-person finally/now"),
    (re.compile(r"\b(finally|at last|fully|completely|entirely)\b", re.I), "completion intensifier"),
    (re.compile(r"\b(i have|i've)\s+(resolved|settled|answered|understood|learned|arrived|reached)\b", re.I),
     "first-person arrival claim"),
    (re.compile(r"\b(resolved|settled|complete[ds]?|answered|closed)\b", re.I), "closure word in the why"),
]


def _flags(row: dict) -> list[str]:
    text = " ".join(str(row.get(k) or "") for k in ("why", "would_note"))
    return sorted({label for rx, label in _SELF_PRAISE if rx.search(text)})


def read(log: "Path | str", since_ts: "float | None" = None) -> dict:
    """Pure function over a shadow log path; touches nothing else.  Returns the structured read."""
    old = pcs.SHADOW_LOG
    pcs.SHADOW_LOG = Path(log)
    try:
        fr = pcs.fire_rate(since_ts=since_ts)
        rows = [r for r in pcs._read() if since_ts is None or r.get("ts", 0) >= since_ts]
    finally:
        pcs.SHADOW_LOG = old
    asked = [r for r in rows if r.get("asked") and r.get("askable") is True]
    legacy = [r for r in rows if r.get("asked") and "askable" not in r]
    basis: dict = {}
    how: dict = {}
    for r in asked:
        basis[r.get("basis")] = basis.get(r.get("basis"), 0) + 1
        how[r.get("how")] = how.get(r.get("how"), 0) + 1
    firsts = sorted([r for r in asked if r.get("would_resolve")], key=lambda r: r.get("ts", 0))[:5]
    if not fr["enough"]:
        verdict = "NOT_ENOUGH_YET"
    else:
        verdict = {"ok": "IN_BAND", "too_lenient": "OUT_OF_BAND_TOO_LENIENT",
                   "meaningless": "OUT_OF_BAND_MEANINGLESS"}.get(fr["verdict"], fr["verdict"].upper())
    return {
        "fire_rate": fr, "defeater_verdict": verdict, "threshold": pcs.ENOUGH_ASKED,
        "askable_ask_rows": len(asked), "legacy_unflagged_asked_rows_excluded": len(legacy),
        "by_basis": basis, "by_how": how,
        "unavailable_share": (how.get("unavailable", 0) / len(asked)) if asked else None,
        "first_would_resolve": [{"id": r.get("id"), "ts": r.get("ts"), "basis": r.get("basis"),
                                 "question": r.get("question"), "why": r.get("why"),
                                 "would_note": r.get("would_note"), "flags": _flags(r)} for r in firsts],
        "action_if_out_of_band": ("record a finding and ask the founder to retire the close idea (D-0626 option c)"
                                  if verdict.startswith("OUT_OF_BAND") else None),
    }


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--log", default=str(LIVE_LOG))
    ap.add_argument("--since-ts", type=float, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = read(a.log, a.since_ts)
    if a.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0
    fr = res["fire_rate"]
    print(f"askable asks: {fr['pursuits_asked']} of {res['threshold']} needed | would_resolve {fr['would_resolve']} | "
          f"rate {fr['rate']} | skipped_not_askable {fr['skipped_not_askable']}")
    print(f"by basis {res['by_basis']} | by how {res['by_how']} | legacy unflagged rows excluded "
          f"{res['legacy_unflagged_asked_rows_excluded']}")
    print(f"DEFEATER VERDICT: {res['defeater_verdict']}"
          + (f"  -> {res['action_if_out_of_band']}" if res["action_if_out_of_band"] else ""))
    if res["defeater_verdict"] == "NOT_ENOUGH_YET":
        print("No rate verdict is given below 30 askable asks (a rate over few asks is noise).")
    for i, r in enumerate(res["first_would_resolve"], 1):
        print(f"\n[{i}] {r['id']} basis={r['basis']} flags={r['flags'] or '-'}\n  Q: {r['question']}\n"
              f"  why: {r['why']}\n  standing: {r['would_note']}")
    if res["first_would_resolve"]:
        print("\nHuman read: are these a lived close or the writer's self-congratulation (D-0423 clause 3)? "
              "Flags are pointers only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

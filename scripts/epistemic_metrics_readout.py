#!/usr/bin/env python
"""READ-ONLY readout for the two InvestigativeEpisode metric columns entropy_reduction / hypothesis_contraction.

J-3868 (D-0734, from F-4190): calculate_internal_epistemic_metrics (core/epistemic_affordance_advisor.py) had no
caller, and all 3,839 of 3,839 stored values were 0.0. D-0734 ruled "wire a reader, do not retire". This is the
reader: it states a verdict on whether the stored columns carry any signal, and self-checks the producer on a
synthetic prior/posterior pair so a "constant 0.0" verdict can be attributed (never computed vs computed-and-zero).

Verdicts: NO_DATA, NEVER_COMPUTED (every value 0.0 -- the producer is not feeding the log), CONSTANT (one nonzero value),
LIVE (values vary). Read-only: the log is opened for reading, nothing is written, SQLite is not opened, no LLM.
Additive and restart-independent (a standalone script). Does not change the producer or the log schema.

Usage: python scripts/epistemic_metrics_readout.py [--log PATH]   (default: the advisor's LOG_JSONL_PATH)
Test:  python scripts/_test_j3868_epistemic_metrics_readout.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import epistemic_affordance_advisor as eaa  # noqa: E402

FIELDS = ("entropy_reduction", "hypothesis_contraction")


def producer_selfcheck() -> dict:
    """Run the producer on a known pair: uniform over 4 -> certain on 1 gives delta H ~1.76, contraction 0.75."""
    return eaa.calculate_internal_epistemic_metrics(
        {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}, {"a": 0.97, "b": 0.01, "c": 0.01, "d": 0.01})


def read_rows(path: Path) -> list:
    rows = []
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue  # torn last line while Du is live
    return rows


def summarize(rows: list) -> dict:
    out = {}
    for fld in FIELDS:
        vals = [r[fld] for r in rows if isinstance(r, dict) and isinstance(r.get(fld), (int, float))]
        nz = [v for v in vals if v != 0]
        if not vals:
            verdict = "NO_DATA"
        elif not nz:
            verdict = "NEVER_COMPUTED"
        elif len(set(nz)) == 1 and len(nz) == len(vals):
            verdict = "CONSTANT"
        else:
            verdict = "LIVE"
        out[fld] = {"n": len(vals), "nonzero": len(nz), "max": max(vals) if vals else None, "verdict": verdict}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=None)
    a = ap.parse_args(argv)
    path = Path(a.log) if a.log else Path(eaa.LOG_JSONL_PATH)
    rows = read_rows(path)
    s = summarize(rows)
    chk = producer_selfcheck()
    print(f"log: {path}  rows: {len(rows)}")
    for fld, d in s.items():
        print(f"  {fld}: n={d['n']} nonzero={d['nonzero']} max={d['max']} -> {d['verdict']}")
    ok = chk.get("entropy_reduction", 0) > 1.5 and chk.get("hypothesis_contraction", 0) > 0.5
    print(f"producer self-check (uniform4 -> peaked): {chk} -> {'producer works' if ok else 'PRODUCER BROKEN'}")
    if all(d["verdict"] == "NEVER_COMPUTED" for d in s.values()) and ok:
        print("verdict: the producer works but nothing feeds it -- episodes carry no prior/posterior P(H), so the columns stay 0.0.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

"""Phase 3 reader for data/soundscape_mix_shadow.jsonl (strings_and_sheets Object E, J-4346).

Pre-registered metrics (docs/staged/strings_and_sheets.md section 5, Phase 3), written before any row exists:
  1. masked share of active keys (sum masked / sum n_active over rows) in [0.10, 0.50]
  2. composite stability: median composite step between consecutive same-place rows (a tick) is SMALLER than
     the median step across a place change
  3. n_audible <= 4 at the 90th percentile
Kill/revert: masked share outside band -> retune or flag off; composite as stable as the key set (tick step not
below the key-set change step) -> carries nothing, Object E reverts to design.
Usage: python scripts/soundscape_mix_shadow_read.py [--log PATH] [--min-rows 200]
Read-only.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

AXES = ("brightness", "energy", "onset", "periodicity", "roughness", "continuity")
DEFAULT_LOG = Path(__file__).resolve().parent.parent / "data" / "soundscape_mix_shadow.jsonl"


def _d(a: dict, b: dict) -> float:
    return sum((float(a[x]) - float(b[x])) ** 2 for x in AXES) ** 0.5


def _jaccard_dist(a: list, b: list) -> float:
    sa, sb = set(a), set(b)
    return 1.0 - (len(sa & sb) / len(sa | sb)) if (sa | sb) else 0.0


def load(path: Path) -> list[dict]:
    rows = []
    try:
        for line in open(path, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    except OSError:
        pass
    return sorted(rows, key=lambda r: r.get("ts", 0))


def evaluate(rows: list[dict], min_rows: int = 200) -> dict:
    out: dict = {"rows": len(rows)}
    if len(rows) < min_rows:
        out["verdict"] = "INSUFFICIENT"
        out["why"] = f"{len(rows)} rows < {min_rows}"
        return out
    act = sum(int(r.get("n_active", 0)) for r in rows)
    msk = sum(len(r.get("masked", [])) for r in rows)
    share = msk / act if act else 0.0
    ns = sorted(int(r.get("n_audible", 0)) for r in rows)
    p90 = ns[min(len(ns) - 1, int(0.9 * len(ns)))]
    tick, place, keyset = [], [], []
    for a, b in zip(rows, rows[1:]):
        if not a.get("composite") or not b.get("composite"):
            continue
        step = _d(a["composite"], b["composite"])
        if a.get("place") != b.get("place"):
            place.append(step)
        else:
            tick.append(step)
            if a.get("keys") != b.get("keys"):
                keyset.append((step, _jaccard_dist(a.get("keys", []), b.get("keys", []))))
    m_tick = statistics.median(tick) if tick else None
    m_place = statistics.median(place) if place else None
    out.update(masked_share=round(share, 4), n_audible_p90=p90,
               tick_step_median=None if m_tick is None else round(m_tick, 4),
               place_step_median=None if m_place is None else round(m_place, 4),
               n_tick=len(tick), n_place_change=len(place))
    checks = {"masked_share_10_50": 0.10 <= share <= 0.50, "n_audible_p90_le_4": p90 <= 4}
    if m_tick is None or m_place is None or len(place) < 3:
        checks["composite_tick_lt_place"] = None      # not enough place changes to judge
    else:
        checks["composite_tick_lt_place"] = m_tick < m_place
    out["checks"] = checks
    vals = list(checks.values())
    out["verdict"] = ("FAIL" if any(v is False for v in vals)
                      else "INCOMPLETE" if any(v is None for v in vals) else "PASS")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    ap.add_argument("--min-rows", type=int, default=200)
    a = ap.parse_args()
    print(json.dumps(evaluate(load(Path(a.log)), a.min_rows), indent=2))

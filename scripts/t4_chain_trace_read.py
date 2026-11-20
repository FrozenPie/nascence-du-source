"""
Reader for data/logs/t4_chain_trace.jsonl (J-3007, F-3707): the per-run trace of the three-stage T4 chain
(crossings -> evidence -> delta -> synthesis) written by nodes/subconscious_node.py _t4_deliberate.

  python scripts/t4_chain_trace_read.py                 # summary + the last 5 runs end to end
  python scripts/t4_chain_trace_read.py --last 12       # more runs
  python scripts/t4_chain_trace_read.py --path <file>   # read another file (tests, copies)
  python scripts/t4_chain_trace_read.py --json          # summary only, as JSON

Read-only. The summary answers what the F-3707 instrument gap could not: how often each stage aborts, how long each
stage takes, and what each stage's text actually says (full, uncut), so a run can be read start to finish.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "data" / "logs" / "t4_chain_trace.jsonl"


def load(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    return rows


def _pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(q * len(xs)))], 3)


def summarise(rows: list[dict]) -> dict:
    out: dict = {"runs": len(rows)}
    if not rows:
        return out
    aborts: dict[str, int] = {}
    for r in rows:
        key = r.get("abort_reason") or "authored"
        aborts[key] = aborts.get(key, 0) + 1
    out["outcomes"] = aborts
    with_ev = [r for r in rows if "has_movement" in r]
    out["evidence_stage_runs"] = len(with_ev)
    out["has_movement_true"] = sum(1 for r in with_ev if r.get("has_movement"))
    out["delta_stage_runs"] = sum(1 for r in rows if "delta_s" in r)
    out["synthesis_stage_runs"] = sum(1 for r in rows if "synthesis_s" in r)
    out["authored"] = sum(1 for r in rows if r.get("authored"))
    lat = {}
    for stage in ("evidence_s", "delta_s", "synthesis_s", "total_s"):
        xs = [float(r[stage]) for r in rows if isinstance(r.get(stage), (int, float))]
        if xs:
            lat[stage] = {"n": len(xs), "median": round(statistics.median(xs), 3), "p90": _pct(xs, 0.9)}
    out["latency"] = lat
    out["keystone_runs"] = sum(1 for r in rows if r.get("keystone"))
    return out


def show_run(r: dict) -> str:
    import datetime as _dt
    ts = r.get("ts")
    when = _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, (int, float)) else "?"
    lines = [f"--- {when}  keystone={r.get('keystone')}  outcome={r.get('abort_reason') or 'AUTHORED'}  total_s={r.get('total_s')}",
             f"tension: {r.get('tension')}"]
    for c in r.get("crossings") or []:
        lines.append(f"  crossing {c.get('id')} cos={c.get('cosine')} ({c.get('word')}): {c.get('text')}")
    if "has_movement" in r:
        lines.append(f"EVIDENCE [{r.get('evidence_s')}s] has_movement={r.get('has_movement')}: {r.get('evidence')}")
    if "delta_s" in r:
        lines.append(f"DELTA [{r.get('delta_s')}s] changed={r.get('changed')}: {r.get('delta')}")
    if r.get("self_concept"):
        lines.append(f"SYNTHESIS [{r.get('synthesis_s')}s] self_concept: {r.get('self_concept')}")
        lines.append(f"  arc_entry: {r.get('arc_entry')}")
    if r.get("stage_error"):
        lines.append(f"STAGE ERROR: {r.get('stage_error')}")
    if r.get("raised"):
        lines.append(f"RAISED: {r.get('raised')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    ap.add_argument("--last", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = load(Path(a.path))
    summ = summarise(rows)
    if a.json:
        print(json.dumps(summ, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(summ, ensure_ascii=False, indent=2))
    for r in rows[-max(0, a.last):]:
        print(show_run(r))
    if not rows:
        print(f"(no rows at {a.path} yet: written only by a Du process running a restarted master build)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

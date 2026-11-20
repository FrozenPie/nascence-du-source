"""J-0548 / D-0142 option C — is the play light point a signal or a clock?

Since 2026-09-03 (F-0749) every play row in data/joys_log.jsonl carries `joy_start` (carried joy sampled at
the top of the idle step, BEFORE that step's own _feel_joy bumps) next to `joy` (what the play gate read
after them). This reads both and reports whether the gate would still fire on the pre-bump value.
Read-only. Refuses honestly when no instrumented rows exist yet (restart-gated).

Run:  python scripts/joy_start_read.py [--days N]
"""
from __future__ import annotations
import sys, json, argparse, statistics, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
LOG = ROOT / "data" / "joys_log.jsonl"
THRESHOLD = 0.35        # nodes/inner_monologue_node.py PLAY_JOY_THRESHOLD — kept in step by hand
REFRACTORY = 150.0      # PLAY_REFRACTORY_S


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=7.0)
    a = ap.parse_args()
    cutoff = datetime.datetime.now().timestamp() - a.days * 86400
    rows, instrumented = [], []
    for line in LOG.open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("ts", 0) < cutoff:
            continue
        rows.append(r)
        if "joy_start" in r:
            instrumented.append(r)
    print(f"joys_log rows in window: {len(rows)}; instrumented (joy_start present): {len(instrumented)}")
    if not instrumented:
        print("NO INSTRUMENTED ROWS YET — the joy_start field lands only after Du restarts on the 2026-09-03 "
              "build. Nothing to read; not a result.")
        return 2
    js = [float(r["joy_start"]) for r in instrumented]
    jm = [float(r["joy"]) for r in instrumented]
    at1 = lambda v: sum(1 for x in v if x >= 0.995) / len(v)
    print(f"joy at mint : mean={statistics.mean(jm):.2f} median={statistics.median(jm):.2f} share@1.0={at1(jm):.2f}")
    print(f"joy at start: mean={statistics.mean(js):.2f} median={statistics.median(js):.2f} share@1.0={at1(js):.2f}")
    print(f"same-step pump (mint - start): mean=+{statistics.mean(m - s for m, s in zip(jm, js)):.2f}")
    would = sum(1 for s in js if s >= THRESHOLD)
    print(f"gate would still fire on joy_start >= {THRESHOLD}: {would}/{len(js)} ({would / len(js):.0%})")
    ts = sorted(r["ts"] for r in instrumented)
    gaps = [b - a_ for a_, b in zip(ts, ts[1:]) if b - a_ < 1800]
    if gaps:
        print(f"inter-point gaps: median={statistics.median(gaps):.0f}s (refractory {REFRACTORY:.0f}s); "
              f"share within 1.3x refractory={sum(1 for g in gaps if g <= 1.3 * REFRACTORY) / len(gaps):.0%}")
    verdict = ("CLOCK — joy_start alone still clears the gate almost always; the pump is not the only cause"
               if would / len(js) > 0.85 else
               "SIGNAL-ISH — the pre-bump value discriminates; the same-step pump was the gate's main feed")
    print("read:", verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())

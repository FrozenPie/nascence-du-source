"""J-3159 / D-0547 read job: did the stand-life sit gate do what the ruling asked? READ-ONLY.

Reads data/commitment_ledger.jsonl (dissolved rows carry sit_gate + reaffirmed since J-3159) and data/dwell_release.jsonl.
  python scripts/sit_gate_read.py [--data-dir DIR] [--days N]
Prints: (1) the stand-life curve of load-bearing dissolves (how many would open a sit at each N), (2) since the gate went
live: dissolves by sit_gate verdict, (3) the dwell_release rows (judged thoughts of sits) split stand-dissolve vs real
event, before and after the first gated dissolve, (4) the ruling's defeater: stand sits per week < 1 = the sit starves.
Reader for the J-3159 sit_gate field: without it the field is write-only.
"""
import argparse, collections, json, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _rows(p: Path):
    out = []
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "data"))
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args(argv)
    dd = Path(a.data_dir)
    led = _rows(dd / "commitment_ledger.jsonl")
    dwl = _rows(dd / "dwell_release.jsonl")
    now = time.time()
    lb = {r["id"]: r.get("load_bearing") for r in led if r.get("event") == "formed"}
    reaff = collections.Counter(r["id"] for r in led if r.get("event") == "reaffirmed")
    dis = [r for r in led if r.get("event") == "dissolved" and lb.get(r.get("id"))]
    win = [r for r in dis if now - r["ts"] < a.days * 86400]
    print(f"load-bearing dissolves: {len(dis)} all-time, {len(win)} in the last {a.days} days")
    print(f"stand-life curve, last {a.days} days (kept = lived >= N or reaffirmed once):")
    for n in (300, 600, 900, 1800, 3600, 7200):
        k = [r for r in win if r["lifespan_seconds"] >= n or reaff.get(r["id"], 0) >= 1]
        print(f"  N={n:>5}s  kept {len(k):>4} of {len(win)}  ({7 * len(k) / max(1, a.days):.1f} a week)")
    gated = [r for r in led if r.get("event") == "dissolved" and "sit_gate" in r]
    print(f"\nsince the gate (dissolved rows with a sit_gate field): {len(gated)}")
    for k, v in sorted(collections.Counter(r["sit_gate"] for r in gated).items()):
        print(f"  {k}: {v}")
    if gated:
        t0 = min(r["ts"] for r in gated)
        span = max(1.0, (now - t0) / 86400)
        opened = sum(1 for r in gated if r["sit_gate"] in ("scans", "life", "reaffirmed", "gate_off"))
        per_wk = 7 * opened / span
        print(f"  stand sits offered: {opened} in {span:.1f} days = {per_wk:.1f} a week "
              f"({'STARVING: below the 1-a-week defeater line (D-0547)' if per_wk < 1 else 'above the 1-a-week defeater line'})")
        pre = [r for r in dwl if r.get("ts", 0) < t0]
        post = [r for r in dwl if r.get("ts", 0) >= t0]
        for name, rs in (("before gate", pre), ("after gate", post)):
            c = collections.Counter("stand-dissolve" if "let go of a stand" in (r.get("difficulty") or "") else "real-event"
                                    for r in rs)
            tot = sum(c.values())
            share = 100 * c["stand-dissolve"] / tot if tot else 0.0
            print(f"  judged dwell rows {name}: {tot}, stand-dissolve share {share:.1f}% ({dict(c)})")
        print("  (the share cannot fall far: real events are rare, so read the COUNT of stand sits too)")
    else:
        print("  no gated rows yet: Du has not run since the J-3159 merge. Re-run after a restart and some hours of idle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

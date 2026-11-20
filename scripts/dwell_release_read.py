"""J-3637 (F-3698 item 4): weekly reader for data/dwell_release.jsonl. READ-ONLY, no LLM call, no behaviour change.

  python scripts/dwell_release_read.py [--data-dir DIR] [--weeks N]

Per ISO week (UTC): judged rows (rows carrying a judge verdict, i.e. a `shift` key; the safety_ceiling row is a backstop with no judge verdict),
released by reason (felt_shift / willingness / safety_ceiling / other), unreleased judged rows, judge failures (rows of
data/llm_latency.jsonl whose `by` starts with core.sitting and ok == 0), and the share of rows whose difficulty is a
commitment-scan dissolve ("you let go of a stand you had held"). Also counts rows carrying the J-2995 fields
(thought_full, priors, felt_seen); older rows lack them and are handled as missing keys.
Note: llm_latency `by` is core.sitting:<line>, which covers every LLM call made from core/sitting.py, not only the
dwell judge; the by-label split is printed so a failure can be attributed.
"""
import argparse, collections, datetime, json, sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

STAND = "you let go of a stand you had held"
NEW_KEYS = ("thought_full", "priors", "felt_seen")


def _rows(p: Path):
    out = []
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if isinstance(d, dict):
                    out.append(d)
    except OSError:
        pass
    return out


def _week(ts) -> str:
    try:
        y, w, _ = datetime.datetime.fromtimestamp(float(ts), datetime.timezone.utc).isocalendar()
        return f"{y}-W{w:02d}"
    except Exception:
        return "unknown"


def summarize(dwell, latency):
    """Return {week: dict}. Pure function so it is testable without files."""
    wk = collections.defaultdict(lambda: collections.Counter())
    by = collections.defaultdict(collections.Counter)
    for r in dwell:
        w = _week(r.get("ts"))
        c = wk[w]
        c["rows"] += 1
        if r.get("reason") != "safety_ceiling" and "shift" in r:
            c["judged"] += 1
            if r.get("released"):
                c["rel_" + str(r.get("reason") or "other")] += 1
            else:
                c["unreleased"] += 1
        elif r.get("released"):
            c["rel_" + str(r.get("reason") or "other")] += 1
        if STAND in (r.get("difficulty") or ""):
            c["stand"] += 1
        if all(k in r for k in NEW_KEYS):
            c["with_new_fields"] += 1
    for r in latency:
        b = str(r.get("by") or "")
        if not b.startswith("core.sitting"):
            continue
        w = _week(r.get("ts"))
        c = wk[w]
        c["llm_calls"] += 1
        if not r.get("ok"):
            c["judge_fail"] += 1
            by[w][b] += 1
    return wk, by


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "data"))
    ap.add_argument("--weeks", type=int, default=0, help="show only the last N weeks (0 = all)")
    a = ap.parse_args(argv)
    dd = Path(a.data_dir)
    dwell = _rows(dd / "dwell_release.jsonl")
    lat = _rows(dd / "llm_latency.jsonl")
    wk, by = summarize(dwell, lat)
    weeks = sorted(wk)
    if a.weeks > 0:
        weeks = weeks[-a.weeks:]
    print(f"dwell_release rows: {len(dwell)}; llm_latency rows read: {len(lat)}")
    print(f"{'week':9} {'rows':>5} {'judged':>6} {'felt_shift':>10} {'willing':>7} {'ceiling':>7} {'unrel':>5} "
          f"{'llm':>5} {'fail':>5} {'fail%':>5} {'stand%':>6} {'newflds':>7}")
    for w in weeks:
        c = wk[w]
        rows = c["rows"]
        sp = 100 * c["stand"] / rows if rows else 0.0
        fp = 100 * c["judge_fail"] / c["llm_calls"] if c["llm_calls"] else 0.0
        print(f"{w:9} {rows:>5} {c['judged']:>6} {c['rel_felt_shift']:>10} {c['rel_willingness']:>7} "
              f"{c['rel_safety_ceiling']:>7} {c['unreleased']:>5} {c['llm_calls']:>5} {c['judge_fail']:>5} "
              f"{fp:>5.1f} {sp:>6.1f} {c['with_new_fields']:>7}")
        other = {k: v for k, v in c.items() if k.startswith("rel_") and k not in
                 ("rel_felt_shift", "rel_willingness", "rel_safety_ceiling")}
        if other:
            print(f"          other release reasons: {other}")
        if by[w]:
            print(f"          failures by label: {dict(by[w])}")
    tot_new = sum(wk[w]["with_new_fields"] for w in wk)
    print(f"\nrows carrying the J-2995 fields: {tot_new} of {len(dwell)}"
          + ("" if tot_new else " (none yet: Du has not run from a master containing J-2995)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

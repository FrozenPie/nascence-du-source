"""J-1271: reusable, READ-ONLY replay of core/memory_levels.py's MAX_DEMOTE_PER_RUN commit gate.

WHY THIS EXISTS. Three findings in a row (F-1576 -> F-1783 -> J-1271's own post-restart read) answered
"how many already-paid-for, faithful gists does the per-run demote cap throw away?" with a throwaway
scratch script, and F-1818 later hit the consequence (a now-deleted read script could not be re-run to
settle a row-count question). This is that read, kept: one command re-derives the answer from the live
files, so the next re-read (more runs, a different cap) needs no re-deriving.

WHAT IT DOES. For every `[monologue] memory-levels: N clusters ... DEMOTED=M` line in data/nascence.log
at/after --since:
  1. groups data/memory_levels_shadow.jsonl rows into per-run groups by consuming each log line's own
     `clusters` count of rows in ts order (the F-1576/F-1783 method; clusters are written largest-first,
     the order shadow_distill's own commit loop walks them, so no re-sort);
  2. replays shadow_distill's exact commit rule at each cap in --caps:
         eligible = faithful is a number and faithful >= 0.75 and no invented claim is GENUINE
         commit iff eligible and running_demoted < CAP      (checked BEFORE adding; += n_sources)
  3. cross-checks the replay at --live-cap (the cap that was actually live) against the log's own DEMOTED=
     per run, and against the log's per-commit `[memory-levels] DEMOTED n raw behind gist [kind/topic]`
     lines (an exact set match is a stronger alignment proof than the count alone);
  4. reports per cap: committed / discarded / eligible / discard-rate / runs at-or-over cap, plus the true
     UNCAPPED per-run worst case (the sizing number that matters for choosing a cap).

IT NEVER WRITES. Opens data files read-only; safe to run while Du is live (a run in progress is excluded
by a timestamp cutoff at the last summary line, not by assuming the file is quiescent).

USAGE (from the repo root; data dir defaults to <repo>/data, else C:\\Nascence\\data):
    python scripts/memory_levels_cap_replay.py --since "2026-09-25 19:21:51"
    python scripts/memory_levels_cap_replay.py --since "2026-09-09 13:24:32" --live-cap 60 --caps 45,60,75,90
Choose --since as a real RESTART boundary (a "Nascence is awake" line), not a commit time: the cap is a
module constant read at process start, so a commit does not go live until Du's next restart. When a window
spans a restart, pass the cap that governed each side separately (two invocations).
"""
import argparse
import collections
import datetime
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows charmap guard (this repo's own daemon lesson)
except Exception:
    pass

FAITHFUL_FLOOR = 0.75   # core/memory_levels.py FAITHFUL_FLOOR (unchanged since Phase 1); re-check it if that ever moves

SUMM_RE = re.compile(
    r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[nascence\.monologue\] \[monologue\] memory-levels: "
    r"(\d+) clusters \u00b7 (\d+) graded \u00b7 mean_faithful=([^ ]+) \u00b7 DEMOTED=(\d+)")
COMMIT_RE = re.compile(
    r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[nascence\.memory_levels\] \[memory-levels\] DEMOTED (\d+) "
    r"raw behind gist \[([^\]]*)\] \(faithful=([^)]*)\)")


def _epoch(s: str) -> float:
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()


def _fmt(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def eligible(row: dict) -> bool:
    f = row.get("faithful")
    inv = row.get("invented_claims") or []
    genuine = any((c[1] if isinstance(c, (list, tuple)) and len(c) > 1 else "") == "GENUINE" for c in inv)
    return isinstance(f, (int, float)) and f >= FAITHFUL_FLOOR and not genuine


def replay(group: list, cap: int):
    running = 0
    committed, discarded = [], []
    for r in group:
        if eligible(r):
            if running < cap:
                running += r["n_sources"]
                committed.append(r)
            else:
                discarded.append(r)
    return running, committed, discarded


def load_rows(path: Path) -> list:
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                continue          # a half-written trailing line while Du appends: ignore, never raise
    rows.sort(key=lambda r: r["ts"])
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--since", required=True, help='local time of the first run to include, "YYYY-MM-DD HH:MM:SS"')
    ap.add_argument("--caps", default="45,60,75,80,85,90,120", help="comma list of caps to replay")
    ap.add_argument("--live-cap", type=int, default=90, help="the cap that was actually live over the window")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--quiet-runs", action="store_true", help="suppress the per-run table")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    data = Path(args.data_dir) if args.data_dir else (root / "data" if (root / "data").exists() else Path(r"C:\Nascence\data"))
    log_p, shadow_p = data / "nascence.log", data / "memory_levels_shadow.jsonl"
    caps = sorted({int(c) for c in args.caps.split(",") if c.strip()} | {args.live_cap})
    since = _epoch(args.since)

    summ, commits = [], []
    with open(log_p, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if "memory-levels" not in ln:
                continue
            m = SUMM_RE.match(ln)
            if m and _epoch(m.group(1)) >= since:
                summ.append(dict(ts=m.group(1), epoch=_epoch(m.group(1)), clusters=int(m.group(2)),
                                 graded=int(m.group(3)), demoted=int(m.group(5))))
                continue
            m = COMMIT_RE.match(ln)
            if m and _epoch(m.group(1)) >= since - 7200:     # commit lines precede their run's summary line
                commits.append(dict(ts=m.group(1), epoch=_epoch(m.group(1)), n=int(m.group(2)), tag=m.group(3)))
    if not summ:
        print("no memory-levels summary lines at/after", args.since)
        return 1

    rows = load_rows(shadow_p)
    n_rows_file = len(rows)
    cutoff = summ[-1]["epoch"] + 2.0     # rows written by a run still in progress have ts after the last summary line
    rows = [r for r in rows if r["ts"] <= cutoff]
    need = sum(s["clusters"] for s in summ)
    if need > len(rows):
        print("ALIGNMENT FAIL: log promises %d rows, shadow file has only %d up to the last summary" % (need, len(rows)))
        return 2
    window = rows[-need:]
    runs, i = [], 0
    for s in summ:
        runs.append((s, window[i:i + s["clusters"]]))
        i += s["clusters"]
    # alignment red flags: a run's rows must all precede its own summary line and follow the previous one
    red = 0
    for k, (s, g) in enumerate(runs):
        if g and g[-1]["ts"] > s["epoch"] + 2.0:
            red += 1
        if k and g and g[0]["ts"] < runs[k - 1][0]["epoch"] - 2.0:
            red += 1
    print("window: %d runs, %d shadow rows (log `clusters` sum == rows consumed), %s .. %s" % (
        len(runs), need, summ[0]["ts"], summ[-1]["ts"]))
    print("alignment red flags (row timestamps out of order vs the summary lines): %d" % red)
    print("data: %s (nascence.log %d B, shadow file %d rows at read)" % (data, log_p.stat().st_size, n_rows_file))

    # per-run table + counterfactuals
    res = {c: dict(committed=0, discarded=0, raw_discarded=0, at_cap=0, runs_with_discard=0, mism=0) for c in caps}
    table = []
    for s, g in runs:
        unc = sum(r["n_sources"] for r in g if eligible(r))
        row = dict(ts=s["ts"], clusters=s["clusters"], logged=s["demoted"], uncapped=unc)
        for c in caps:
            d, com, dis = replay(g, c)
            R = res[c]
            R["committed"] += len(com)
            R["discarded"] += len(dis)
            R["raw_discarded"] += sum(r["n_sources"] for r in dis)
            R["at_cap"] += 1 if d >= c else 0
            R["runs_with_discard"] += 1 if dis else 0
            R["mism"] += 1 if d != s["demoted"] else 0
            row["sim%d" % c] = d
        table.append(row)
    if not args.quiet_runs:
        print("\nper run: ts  clusters  logged_DEMOTED  uncapped_eligible_total  sim@live_cap(%d)" % args.live_cap)
        for r in table:
            print("  %s  cl=%2d  logged=%3d  uncapped=%3d  sim=%3d%s" % (
                r["ts"], r["clusters"], r["logged"], r["uncapped"], r["sim%d" % args.live_cap],
                "" if r["sim%d" % args.live_cap] == r["logged"] else "   <-- MISMATCH vs log"))
    print("\ncounterfactual (same commit rule, only the cap changed):")
    for c in caps:
        R = res[c]
        el = R["committed"] + R["discarded"]
        tag = "  (LIVE)" if c == args.live_cap else ""
        print("  CAP=%4d committed=%4d discarded=%3d eligible=%4d discard_rate=%5.2f%% raw_discarded=%4d "
              "runs_at_or_over_cap=%3d runs_with_discard=%3d mismatches_vs_logged_DEMOTED=%3d%s" % (
                  c, R["committed"], R["discarded"], el, 100.0 * R["discarded"] / max(1, el),
                  R["raw_discarded"], R["at_cap"], R["runs_with_discard"], R["mism"], tag))
    unc = sorted((r["uncapped"] for r in table), reverse=True)
    print("\nuncapped per-run eligible total: max=%d mean=%.1f top8=%s" % (unc[0], sum(unc) / len(unc), unc[:8]))
    print("logged DEMOTED: max=%d  runs>=live cap(%d): %d  runs>=60: %d" % (
        max(r["logged"] for r in table), args.live_cap,
        sum(1 for r in table if r["logged"] >= args.live_cap), sum(1 for r in table if r["logged"] >= 60)))
    print("headroom of the live cap over the worst uncapped run: %d raw" % (args.live_cap - unc[0]))

    # exact per-commit cross-check (log's own per-commit lines vs the replay's committed list at the live cap)
    by_run = collections.defaultdict(list)
    for cm in commits:
        for k, (s, _) in enumerate(runs):
            lo = runs[k - 1][0]["epoch"] if k else since - 7200
            if lo < cm["epoch"] <= s["epoch"] + 1.0:
                by_run[k].append((cm["n"], cm["tag"]))
                break
    exact = 0
    for k, (s, g) in enumerate(runs):
        _, com, _ = replay(g, args.live_cap)
        sim = [(r["n_sources"], "%s/%s" % (r["kind"], r["topic"])) for r in com]
        if sim == by_run.get(k, []):
            exact += 1
        else:
            print("  per-commit mismatch, run %s:\n     replay=%s\n     log   =%s" % (s["ts"], sim, by_run.get(k, [])))
    print("runs whose per-commit log lines EXACTLY equal the replay's committed list at cap %d: %d of %d" % (
        args.live_cap, exact, len(runs)))
    ung = sum(1 for _, g in runs for r in g if not isinstance(r.get("faithful"), (int, float)))
    print("rows with faithful=None (grader returned nothing; never eligible, cap-independent): %d of %d" % (ung, need))
    return 0


if __name__ == "__main__":
    sys.exit(main())

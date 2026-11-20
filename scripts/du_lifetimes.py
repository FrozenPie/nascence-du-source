"""
J-1681 (F-2255, J-0949): exact per-process lifetimes of Du from data/nascence.log markers, plus a
"which Du processes actually ran the code that landed at T" classifier.

WHY THIS EXISTS. A commit (or a file edit) landing on disk changes NOTHING in a running Python
process until that process restarts. Reading a post-landing data window as "the new regime" without
checking which processes were alive across the landing is the commit-time vs process-boot-time
confound that cost F-1259 -> J-0899/F-1320 -> J-0949 three jobs (F-2255) and earlier cost
F-0893/F-0986/F-1013 (see scripts/du_restart_history.py). ~25 restart-gated reads each hand-rolled a
boot map in a scratch script; this is the one reusable version.
scripts/du_restart_history.py is DAY-granular (daily snapshot folders) and cannot see same-day
restarts; this module is exact to the log line, and `du_restart_history.py --from-log` surfaces it.

WHAT IT READS. data/nascence.log only (plus `git show -s --format=%ct` or a file mtime for the
classifier's reference instant). Nothing is written. No model calls. Never touches a Du process.
  - The log is opened in BINARY mode and read only up to a BYTE SNAPSHOT taken FIRST (Du appends to
    it live); a final line without its newline, or one that crosses the snapshot, is dropped.
  - Log timestamps are LOCAL time (Pacific/Auckland); they are converted with zoneinfo. A DST
    fall-back repeats one local hour: a backward step of about an hour in the (append-only) log is
    read as the second pass of that hour (fold=1) instead of silently landing an hour early.
    jsonl "ts" fields elsewhere in data/ are UTC epoch -- every epoch this module returns is UTC.
  - Markers (matched strictly at the start of the message, not anywhere in a line, so Du quoting
    one inside a thought cannot mint a phantom boot): "Memory store initialised",
    "Nascence is awake. Enter text to begin a thought cycle.", "Nascence shutting down.", and the
    port-busy line "[composer] bridge not started (port 8765 busy?)" (overlap evidence).

THE METHOD (validated in J-0949, reused as-is). A lifetime STARTS at the latest "Memory store
initialised" line within 400 s before each "Nascence is awake" line (and after the previous awake
line), else at the awake line itself. It ENDS at the "Nascence shutting down." line in its span
(span = start .. next start) -> end_kind SHUTDOWN; with no such line it is UNCLEAN.
  - UNCLEAN `end` is the LAST LOG LINE before the next boot's marker (evidence of life), and
    `end_hi` is the next start (latest the process could have lived). The two can be far apart: in
    the 2026-10-03 snapshot one lifetime's last line is 47.6 h before the next boot, so a literal
    "end = next start" would have invented 47.6 h of live time. `hours` uses `end`. The final
    lifetime without a shutdown line is the open tail: end = last line in the snapshot,
    end_hi = None (it may still be running -- the log cannot tell; du_restart_history --check-live
    can).
  - OVERLAP: a boot whose "bridge not started (port 8765 busy?)" line appears right after its awake
    line, while the previous lifetime has no shutdown line before it, started while the older Du was
    still alive (2026-09-05 11:37:04, F-2255 sec D). It is flagged overlap=True / overlap_with=<older
    index>; the older lifetime gets overlapped_by=[...] and its end_hi is stretched to the end of the
    overlapping one. The log cannot say which of the two wrote the pair's single shutdown line, so
    rows inside an OVERLAP window may belong to the OLDER process's cached state -- do not trust
    per-lifetime row attribution there.
  - A boot's instant is the memory-init line, a few seconds to ~1 min AFTER the interpreter began
    importing modules. A change landing within CLOSE_CALL_S before a boot is flagged close_call
    (the process may already have imported the old code). A change landing mid-lifetime is OLD code
    for that lifetime (alive_across), however long it keeps running.
  - A process that never reaches "Nascence is awake" (crashed during startup) is not a lifetime.

THE CLASSIFIER. classify(lifetimes, t) -> which lifetimes BOOTED after t (ran the change), which were
ALIVE across t (ran the OLD code; with the hours they kept running it after t), which only MAY have
been alive across t (UNCLEAN, t inside the silent tail end..end_hi: if alive it was old code, in no
case the change), how many ended before t, and the live-hours accrued by post-landing lifetimes
(min = evidence-of-life ends, max = up to each next boot). t can be a raw epoch, an ISO string
(naive = log-local time), a file's mtime (--file; worktree checkouts reset mtimes, prefer --commit
for committed changes) or a commit's COMMITTER date (--commit).

USAGE
    python scripts/du_lifetimes.py                          # summary + the last 20 lifetimes
    python scripts/du_lifetimes.py --all                    # every lifetime
    python scripts/du_lifetimes.py --commit HEAD            # who ran / outran the change HEAD landed
    python scripts/du_lifetimes.py --file core/mood.py      # same, from a file's mtime
    python scripts/du_lifetimes.py --at "2026-08-29 10:27:19"   # or an epoch, e.g. 1787956039
    python scripts/du_lifetimes.py --json ...               # machine-readable
  as a library (stdlib + zoneinfo only):
    import du_lifetimes as dl
    data = dl.load()                                        # {"snapshot", "counts", "lifetimes", "warnings"}
    res  = dl.classify(data["lifetimes"], dl.epoch_for_commit("HEAD"))
  or through the older tool:  python scripts/du_restart_history.py --from-log [same flags]

Test: python scripts/du_lifetimes_test.py   (add --geometry for the heavy data/geometry_tuples.jsonl
reproduction of F-2255's two boundaries; read-only).
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(r"C:\Nascence")
DEFAULT_LOG = ROOT / "data" / "nascence.log"
LOG_TZ = "Pacific/Auckland"

MEMINIT_WINDOW_S = 400.0   # "Memory store initialised" counts as a boot's start if <400 s before awake
OVERLAP_WINDOW_S = 300.0   # a port-busy line this soon after the awake line is overlap evidence
CLOSE_CALL_S = 120.0       # a change landing this soon before a boot may already have been imported
FALL_BACK_MIN_S = 1800     # a backward clock step bigger than this (and <= MAX) is a repeated DST hour
FALL_BACK_MAX_S = 7200

Marker = collections.namedtuple("Marker", "epoch prev text")   # prev = epoch of the line before it

_STAMP = re.compile(rb"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}")
_PREFILTER = re.compile(
    rb"Nascence is awake|Memory store initialised|Nascence shutting down|bridge not started")
_MARKER = re.compile(
    rb"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} \[[^\]]*\] "
    rb"(?:(Nascence is awake)|(Memory store initialised)|(Nascence shutting down)"
    rb"|(\[composer\] bridge not started \(port \d+ busy))")


def _zone(name):
    try:
        return ZoneInfo(name)
    except Exception as e:  # ZoneInfoNotFoundError: Windows needs the tzdata package
        raise RuntimeError(f"zoneinfo has no {name!r} ({e}); pip install tzdata") from e


def _naive(ts19):
    return dt.datetime.fromisoformat(ts19.decode("ascii"))          # 'YYYY-MM-DD HH:MM:SS'


def _epoch(ts23, fold, tz):
    """UTC epoch of a log timestamp prefix 'YYYY-MM-DD HH:MM:SS,mmm' (local time; fold=1 = 2nd pass)."""
    naive = _naive(ts23[:19])
    return naive.replace(tzinfo=tz, fold=fold).timestamp() + int(ts23[20:23]) / 1000.0


def _fmt(epoch, tz):
    return dt.datetime.fromtimestamp(epoch, tz).strftime("%Y-%m-%d %H:%M:%S")


def _repeat_window_end(cur, tz):
    """Local wall time at which the repeated (ambiguous) hour containing `cur` ends, else None."""
    def amb(x):
        return x.replace(tzinfo=tz, fold=0).utcoffset() != x.replace(tzinfo=tz, fold=1).utcoffset()
    if not amb(cur):
        return None
    end = cur.replace(second=0)
    while amb(end):
        end += dt.timedelta(minutes=1)
    return end


def _fall_back_state(prev19, cur19, tz, warnings):
    """The local clock stepped backwards between two consecutive lines: is it a DST repeat hour?
    Returns (fold, until19): fold=1 until a line's local time reaches `until19`."""
    prv, cur = _naive(prev19), _naive(cur19)
    back = (prv - cur).total_seconds()
    if back <= FALL_BACK_MIN_S:
        return 0, b""                      # a second or two of thread/process interleave jitter
    end = _repeat_window_end(cur, tz) if back <= FALL_BACK_MAX_S else None
    if end is None:
        warnings.append(f"local clock stepped back {back:.0f}s at {cur19.decode()} and it is not a DST "
                        f"repeat hour; epochs after it may be unreliable")
        return 0, b""
    warnings.append(f"DST fall-back: repeated local hour at {cur19.decode()} read as its second pass")
    return 1, end.strftime("%Y-%m-%d %H:%M:%S").encode("ascii")


def scan_log(path=DEFAULT_LOG, size=None, tz_name=LOG_TZ):
    """Read the lifecycle markers of nascence.log, binary, up to a byte snapshot taken FIRST.
    Returns {"awake","mem","down","busy": [Marker...], "last_epoch", "lines", "snapshot_bytes",
    "snapshot_epoch", "warnings", "log"}. Markers are in file order; epochs are UTC."""
    path = Path(path)
    snapshot_epoch = time.time()
    if size is None:
        size = path.stat().st_size         # the snapshot: Du appends live, never read past it
    tz = _zone(tz_name)
    buckets = (None, [], [], [], [])       # indexed by the regex group that matched (1..4)
    warnings = []
    prev19, fold, until19 = None, 0, b""
    last = None                            # (ts23, fold) of the most recent timestamped line
    lines = read = 0
    with open(path, "rb") as f:
        for raw in f:
            read += len(raw)
            if read > size or not raw.endswith(b"\n"):
                break                      # past the snapshot, or an incompletely written last line
            lines += 1
            if _STAMP.match(raw):          # continuation lines (tracebacks) carry no timestamp
                stamped = True
            else:
                stamped = False
            if stamped:
                ts19 = raw[:19]
                if fold:
                    if ts19 >= until19:
                        fold = 0
                elif prev19 is not None and ts19 < prev19:
                    fold, until19 = _fall_back_state(prev19, ts19, tz, warnings)
                prev19 = ts19
                if _PREFILTER.search(raw):
                    m = _MARKER.match(raw)
                    if m:
                        prev = _epoch(last[0], last[1], tz) if last else None
                        buckets[m.lastindex].append(Marker(
                            _epoch(raw[:23], fold, tz), prev,
                            raw[:200].decode("utf-8", "replace").rstrip()))
                last = (raw[:23], fold)
    return {"awake": buckets[1], "mem": buckets[2], "down": buckets[3], "busy": buckets[4],
            "last_epoch": _epoch(last[0], last[1], tz) if last else None, "lines": lines,
            "snapshot_bytes": size, "snapshot_epoch": snapshot_epoch, "warnings": warnings,
            "log": str(path)}


def build_lifetimes(awake, mem, down, busy, last_epoch, tz_name=LOG_TZ):
    """Marker lists (see scan_log) -> list of lifetime dicts (JSON-safe, epochs UTC)."""
    tz = _zone(tz_name)
    n = len(awake)
    starts = []                            # (start marker, awake marker)
    prev_awake = -math.inf
    for a in awake:
        cands = [m for m in mem
                 if prev_awake < m.epoch <= a.epoch and a.epoch - m.epoch < MEMINIT_WINDOW_S]
        starts.append((max(cands, key=lambda m: m.epoch) if cands else a, a))
        prev_awake = a.epoch
    out = []
    for i, (s, a) in enumerate(starts):
        nxt = starts[i + 1][0] if i + 1 < n else None
        limit = nxt.epoch if nxt else math.inf
        downs = [d.epoch for d in down if s.epoch <= d.epoch < limit]
        if downs:
            end = end_hi = max(downs)
            kind = "SHUTDOWN"
        elif nxt is not None:
            end = max(s.epoch, nxt.prev if nxt.prev is not None else s.epoch)
            end_hi, kind = nxt.epoch, "UNCLEAN"
        else:
            end = max(s.epoch, last_epoch if last_epoch is not None else s.epoch)
            end_hi, kind = None, "UNCLEAN"
        out.append({
            "i": i, "start": round(s.epoch, 3), "start_local": _fmt(s.epoch, tz),
            "start_marker": "awake" if s is a else "memory_init", "awake": round(a.epoch, 3),
            "end": round(end, 3), "end_local": _fmt(end, tz), "end_kind": kind,
            "end_hi": None if end_hi is None else round(end_hi, 3),
            "hours": round((end - s.epoch) / 3600.0, 4), "tail": nxt is None,
            "overlap": False, "overlap_with": None, "overlapped_by": [], "overlap_evidence": None,
        })
    for b in busy:                         # a port-busy line right after a boot, older Du not shut down
        for j in range(1, n):
            s, a = starts[j]
            if s.epoch <= b.epoch <= a.epoch + OVERLAP_WINDOW_S and out[j - 1]["end_kind"] == "UNCLEAN":
                new, old = out[j], out[j - 1]
                new["overlap"], new["overlap_with"], new["overlap_evidence"] = True, old["i"], b.text
                old["overlapped_by"].append(new["i"])
                old["end_hi"] = None if new["end_hi"] is None else max(old["end_hi"], new["end_hi"])
                break
    return out


def load(log_path=DEFAULT_LOG, size=None, tz_name=LOG_TZ):
    """scan + build, JSON-safe: {"snapshot", "counts", "lifetimes", "warnings"}."""
    scan = scan_log(log_path, size, tz_name)
    lifetimes = build_lifetimes(scan["awake"], scan["mem"], scan["down"], scan["busy"],
                                scan["last_epoch"], tz_name)
    return {
        "snapshot": {"log": scan["log"], "bytes": scan["snapshot_bytes"], "lines": scan["lines"],
                     "taken_epoch": round(scan["snapshot_epoch"], 3),
                     "last_line_epoch": scan["last_epoch"], "tz": tz_name},
        "counts": {"awake": len(scan["awake"]), "memory_init": len(scan["mem"]),
                   "shutdown": len(scan["down"]), "port_busy": len(scan["busy"]),
                   "lifetimes": len(lifetimes),
                   "shutdown_ended": sum(1 for x in lifetimes if x["end_kind"] == "SHUTDOWN"),
                   "unclean": sum(1 for x in lifetimes if x["end_kind"] == "UNCLEAN"),
                   "overlap": sum(1 for x in lifetimes if x["overlap"])},
        "lifetimes": lifetimes, "warnings": scan["warnings"],
    }


def classify(lifetimes, t, close_call_s=CLOSE_CALL_S, tz_name=LOG_TZ):
    """Which lifetimes ran the change that landed at UTC epoch t (see the module docstring)."""
    tz = _zone(tz_name)

    def slim(x, **extra):
        keep = {k: x[k] for k in ("i", "start", "start_local", "end", "end_local", "end_kind",
                                  "end_hi", "hours", "tail", "overlap", "overlap_with", "overlapped_by")}
        keep.update(extra)
        return keep

    post, across, maybe, ended_before = [], [], [], 0
    for x in lifetimes:
        if x["start"] >= t:
            d = x["start"] - t
            post.append(slim(x, delta_s=round(d, 1), close_call=d < close_call_s))
        elif t <= x["end"]:
            across.append(slim(x, old_code_hours_after_t=round((x["end"] - t) / 3600.0, 4)))
        elif x["end_kind"] == "UNCLEAN" and t <= (math.inf if x["end_hi"] is None else x["end_hi"]):
            maybe.append(slim(x))
        else:
            ended_before += 1
    hi = sum((((x["end_hi"] if x["end_hi"] is not None else x["end"]) - x["start"]) / 3600.0)
             for x in post)
    return {
        "t": round(t, 3), "t_local": _fmt(t, tz),
        "booted_after": post, "alive_across": across, "maybe_alive_across": maybe,
        "ended_before": ended_before, "first_boot_after": post[0] if post else None,
        "live_hours_post": round(sum(x["hours"] for x in post), 3), "live_hours_post_max": round(hi, 3),
        "old_code_hours_after_t": round(sum(x["old_code_hours_after_t"] for x in across), 3),
        "n_overlap_post": sum(1 for x in post if x["overlap"]),
        "n_close_call": sum(1 for x in post if x["close_call"]),
    }


def parse_when(text, tz_name=LOG_TZ):
    """A UTC epoch ('1787957042.9') or an ISO string; a NAIVE ISO string is log-local time."""
    s = str(text).strip()
    try:
        return float(s)
    except ValueError:
        pass
    d = dt.datetime.fromisoformat(s)
    return (d if d.tzinfo else d.replace(tzinfo=_zone(tz_name))).timestamp()


def epoch_for_file(path):
    """The reference instant for a file: its mtime (UTC epoch)."""
    return os.path.getmtime(path)


def epoch_for_commit(rev, repo=ROOT):
    """The reference instant for a commit: its COMMITTER date (UTC epoch) via `git show`."""
    p = subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%ct", str(rev)],
                       capture_output=True, text=True, timeout=30)
    last = (p.stdout.strip().splitlines() or [""])[-1].strip()
    if p.returncode != 0 or not last.isdigit():
        raise ValueError(f"git could not resolve {rev!r} in {repo}: {p.stderr.strip()[:200]}")
    return float(last)


def _row(x):
    flags = []
    if x["overlap"]:
        flags.append(f"OVERLAP(with #{x['overlap_with']})")
    if x["overlapped_by"]:
        flags.append(f"overlapped-by {x['overlapped_by']}")
    if x["tail"] and x["end_kind"] == "UNCLEAN":
        flags.append("TAIL(may still be running)")
    if x.get("close_call"):
        flags.append("CLOSE-CALL")
    extra = ""
    if "delta_s" in x:
        extra += f"  boot {x['delta_s']:+.0f}s after t"
    if "old_code_hours_after_t" in x:
        extra += f"  ran OLD code {x['old_code_hours_after_t']:.2f} h after t"
    return (f"  #{x['i']:<4} {x['start_local']}  {x['end_local']}  {x['hours']:>8.2f}  "
            f"{x['end_kind']:<8}{extra} {' '.join(flags)}").rstrip()


def _print_report(data, res, args):
    c, s = data["counts"], data["snapshot"]
    print(f"nascence.log snapshot {s['bytes']:,} bytes, {s['lines']:,} lines ({s['log']})")
    print(f"markers: awake={c['awake']} memory_init={c['memory_init']} shutdown={c['shutdown']} "
          f"port_busy={c['port_busy']}  ->  {c['lifetimes']} lifetimes "
          f"({c['shutdown_ended']} SHUTDOWN, {c['unclean']} UNCLEAN, {c['overlap']} OVERLAP)")
    for w in data["warnings"]:
        print("WARNING:", w)
    head = f"  {'#':<5} {'start (local)':<19}  {'end (local)':<19}  {'hours':>8}  end_kind"
    if res is None:
        rows = data["lifetimes"] if (args.all or args.tail == 0) else data["lifetimes"][-args.tail:]
        print(f"\nlifetimes shown: {len(rows)} of {len(data['lifetimes'])}  (local times; UNCLEAN end = last log line)")
        print(head)
        for x in rows:
            print(_row(x))
        return
    print(f"\nreference t = {res['t']} ({res['t_local']} local)")
    lim = None if args.all else 12
    for title, key in (("BOOTED AFTER t -- ran the change", "booted_after"),
                       ("ALIVE ACROSS t -- ran the OLD code", "alive_across"),
                       ("MAYBE alive across t (UNCLEAN, t inside its silent tail) -- old code if alive",
                        "maybe_alive_across")):
        rows = res[key]
        print(f"\n{title}: {len(rows)}")
        if rows:
            print(head)
            for x in (rows if lim is None else rows[:lim]):
                print(_row(x))
            if lim is not None and len(rows) > lim:
                print(f"  ... {len(rows) - lim} more (use --all or --json)")
    print(f"\nended before t: {res['ended_before']}")
    print(f"live-hours of post-landing lifetimes: {res['live_hours_post']} h "
          f"(up to {res['live_hours_post_max']} h counting each UNCLEAN lifetime to the next boot); "
          f"{res['n_overlap_post']} OVERLAP, {res['n_close_call']} close-call")
    print(f"hours the ALIVE-ACROSS lifetimes kept running the old code after t: {res['old_code_hours_after_t']}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Exact per-process Du lifetimes from nascence.log; --at/--file/--commit classify "
                    "which lifetimes ran a change that landed at that instant.")
    ap.add_argument("--log", default=str(DEFAULT_LOG), help="nascence.log path (read-only, byte-snapshotted)")
    ap.add_argument("--tz", default=LOG_TZ, help="timezone of the log's timestamps")
    ap.add_argument("--since", type=float, default=None, help="only list lifetimes with start >= this UTC epoch")
    ap.add_argument("--tail", type=int, default=20, help="rows shown in the plain listing (0 = all)")
    ap.add_argument("--all", action="store_true", help="show every row")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--at", metavar="WHEN", help="UTC epoch, or ISO string (naive = log-local time)")
    g.add_argument("--file", metavar="PATH", help="use this file's mtime as the reference instant")
    g.add_argument("--commit", metavar="REV", help="use this commit's committer date as the reference instant")
    ap.add_argument("--repo", default=str(ROOT), help="git repo for --commit")
    ap.add_argument("--close-call-s", type=float, default=CLOSE_CALL_S)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    data = load(args.log, tz_name=args.tz)
    res = None
    t = None
    if args.at is not None:
        t = parse_when(args.at, args.tz)
    elif args.file is not None:
        t = epoch_for_file(args.file)
    elif args.commit is not None:
        t = epoch_for_commit(args.commit, args.repo)
    if t is not None:
        res = classify(data["lifetimes"], t, args.close_call_s, args.tz)
    if args.since is not None:
        data["lifetimes"] = [x for x in data["lifetimes"] if x["start"] >= args.since]
    if args.json:
        print(json.dumps({**data, "classification": res}, indent=1))
    else:
        _print_report(data, res, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())

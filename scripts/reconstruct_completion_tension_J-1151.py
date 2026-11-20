"""
reconstruct_completion_tension_J-1151.py -- J-1151, D-0211 scope-widening measurement.

completion_tension has NO history table (core/climate_engine.py lines 443-450: it is
`_saturate(tension_ledger.contradiction_pressure_for(tensions))` computed live each tick over the
Subconscious's CURRENT in-memory tensions list -- see the docstring note below on why that list's own
past states cannot be replayed from any persisted file). The only real historical signal is the
telemetry line core/climate_engine.py logs once ~5 min (line 718-723):

    logger.info("[climate] dominant=%s(%.2f) dissonance=%.3f strain=%.2f "
                "completion=%.2f integration=%.2f", ...)

-- a 2-decimal SATURATED completion_tension value, every time regardless of whether completion is
the winning `dominant` dimension. This script parses every such line in data/nascence.log (full
history, not a tail sample), splits by the same TRUE-UTC period boundaries the companion
belonging/autonomy script uses, and back-solves the raw (pre-saturation) score band each displayed
2-decimal value is consistent with, via the knee's own inverse: saturate(raw)=raw/(raw+3) =>
raw = 3*c/(1-c). Because the log only prints 2 decimals, a displayed value like 0.92 could be any
raw score whose saturate() rounds to 0.92 -- reported here as the band for c in [displayed-0.005,
displayed+0.005), which is imprecise by construction (this is disclosed, not hidden: e.g. at
displayed=0.92 the band is raw ~=32.3-37.0, a much wider absolute range than the DB-replay dimensions
below get, because 3*c/(1-c) grows steeply as c approaches 1).

PERSISTED-STATE CHECK (per this job's own instruction -- checked honestly, not assumed):
data/subconscious_state.json (heavy, whole-file read-modify-write on every save -- see
core/climate_engine.py's own _read_subconscious docstring) and its light companion
data/subconscious_state.light.json are both CURRENT-STATE SNAPSHOTS, overwritten in place every
save, not an append-only log -- confirmed by inspection (both files share today's mtime; the light
file's own `tensions` list holds each tension's `first_ts`/`last_ts`/`resolution_attempts` for ITS
OWN lifecycle, but not a record of which tensions were members of the ACTIVE ledger, nor their
`member_event_ids` linkage to light/shadow events, at any past tick). core/tension_ledger.py's
`contradiction_pressure_for` (read in full, lines 213-231) computes its sum via `_sources_for` /
`_resolutions_for` / `score_all` over the CURRENT tensions list's CURRENT member/source linkage --
reconstructing a past raw score would require replaying which tensions existed, in what member/source
state, as of a past tick, which no persisted file preserves (the ledger evolves via ongoing
clustering/synthesis, not an append-only event log). CONCLUSION: no, the persisted state files cannot
reconstruct completion_tension's raw history; the 2-decimal telemetry line above is the only real
historical signal, exactly as this job's own briefing anticipated.

Read-only throughout: data/nascence.log opened for read only. No core.* imports, no live-store writes.
"""
import re, datetime, statistics, sys
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')

LOG = r"C:\Nascence\data\nascence.log"

_SAT_K = 3.0  # matches core/climate_engine.py's shared _SAT_K (completion_tension is NOT custom-k'd)

_CLIMATE_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \[nascence\.climate\] \[climate\] "
    r"dominant=(\S+)\(([\d.]+)\) dissonance=([\d.]+) strain=([\d.]+) "
    r"completion=([\d.]+) integration=([\d.]+)"
)


def parse_nzst_to_utc_epoch(s):
    dt_naive_nzst = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    dt_utc = (dt_naive_nzst - datetime.timedelta(hours=12)).replace(tzinfo=datetime.timezone.utc)
    return dt_utc.timestamp()


def parse_utc(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def raw_band(c_display):
    """Inverse of saturate(raw, k=3) = raw/(raw+3), for the band of displayed-value rounding."""
    lo_c, hi_c = c_display - 0.005, c_display + 0.005
    lo_raw = 3.0 * lo_c / (1.0 - lo_c) if lo_c < 1.0 else float("inf")
    hi_raw = 3.0 * hi_c / (1.0 - hi_c) if hi_c < 1.0 else float("inf")
    return lo_raw, hi_raw


def describe(vals):
    if not vals:
        return None
    v = sorted(vals)
    n = len(v)

    def pct(p):
        k = (n - 1) * p
        f = int(k)
        c = min(f + 1, n - 1)
        return v[f] if f == c else v[f] + (v[c] - v[f]) * (k - f)

    return {
        "n": n, "mean": statistics.mean(v), "sd": statistics.pstdev(v) if n > 1 else 0.0,
        "median": statistics.median(v), "p10": pct(0.10), "p90": pct(0.90),
        "min": v[0], "max": v[-1],
        "frac_ge_0.90": sum(1 for x in v if x >= 0.90) / n,
    }


# Same TRUE-UTC boundaries as reconstruct_belonging_autonomy_J-1151.py (period definitions kept
# identical across both scripts so the cross-dimension comparison is apples-to-apples).
PRE_0823_STR     = "2026-08-23 00:00:00"
BUILD_LANDED_STR = "2026-09-05 21:53:02"   # = 2026-09-06 09:53:02 NZST
RESTART_STR      = "2026-09-08 04:42:00"   # = 2026-09-08 16:42:00 NZST


def main():
    rows = []  # (ts_utc, dominant, dominant_val, dissonance, strain, completion, integration)
    n_lines_total = 0
    with open(LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            n_lines_total += 1
            m = _CLIMATE_LINE_RE.match(line)
            if not m:
                continue
            ts_utc = parse_nzst_to_utc_epoch(m.group(1))
            rows.append((
                ts_utc, m.group(2), float(m.group(3)), float(m.group(4)),
                float(m.group(5)), float(m.group(6)), float(m.group(7)),
            ))
    print(f"Scanned {n_lines_total} log lines; matched {len(rows)} '[climate] dominant=' telemetry lines")
    if not rows:
        print("NO ROWS MATCHED -- aborting")
        return
    rows.sort(key=lambda r: r[0])
    print(f"Telemetry span: {fmt(rows[0][0])} .. {fmt(rows[-1][0])}")

    PRE_0823, BUILD_LANDED, RESTART = parse_utc(PRE_0823_STR), parse_utc(BUILD_LANDED_STR), parse_utc(RESTART_STR)
    periods = {
        "pre-telemetry-existing .. 08-23 (long baseline)": (rows[0][0], PRE_0823),
        "S2 08-23 .. build landed": (PRE_0823, BUILD_LANDED),
        "build-landed-not-restarted": (BUILD_LANDED, RESTART),
        "S3 post-restart (all telemetry -- inherently live-only, logger only runs while up)": (RESTART, rows[-1][0] + 1),
    }

    print("\n" + "=" * 110)
    print("completion_tension telemetry (2-decimal, saturated) by period, + back-solved raw band")
    print("=" * 110)
    for name, (a, b) in periods.items():
        vals = [r[5] for r in rows if a <= r[0] < b]
        d = describe(vals)
        print(f"\n{name}  [{fmt(a)} .. {fmt(min(b, rows[-1][0]+1))}]")
        if d is None:
            print("  (no samples)")
            continue
        print(f"  n={d['n']:5d}  mean={d['mean']:.4f}  sd={d['sd']:.4f}  median={d['median']:.4f}  "
              f"p10={d['p10']:.4f}  p90={d['p90']:.4f}  min={d['min']:.2f}  max={d['max']:.2f}  "
              f"share>=0.90={d['frac_ge_0.90']*100:.1f}%")
        lo, hi = raw_band(d["median"])
        print(f"  back-solved raw band at median c={d['median']:.2f}: raw ~= {lo:.1f} .. {hi:.1f}  "
              f"(IMPRECISE -- 2-decimal telemetry only; band width reflects that, not a real CI)")
        hist = Counter(round(v, 2) for v in vals)
        print("  value histogram:", dict(sorted(hist.items())))

    print("\n" + "=" * 110)
    print("Daily median completion_tension, FULL telemetry history -- pins down SINCE WHEN it reads pinned")
    print("=" * 110)
    daily = defaultdict(list)
    for ts, dom, domv, diss, strain, compl, integ in rows:
        day = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
        daily[day].append(compl)
    print("date         n   median_completion   share>=0.90")
    for day in sorted(daily):
        v = daily[day]
        mark = ""
        if day == "2026-08-23":
            mark = "  <-- F-1262 boundary"
        if day == "2026-09-06":
            mark = "  <-- J-0594 build landed"
        if day == "2026-09-08":
            mark = "  <-- restart (LIVE from here)"
        share = sum(1 for x in v if x >= 0.90) / len(v)
        print(f"{day}  {len(v):3d}   {statistics.median(v):.4f}              {share*100:5.1f}%{mark}")

    print("\n" + "=" * 110)
    print("dominant= counts by period (cross-check against F-1579's post-restart 1263/17 telemetry split)")
    print("=" * 110)
    for name, (a, b) in periods.items():
        doms = Counter(r[1] for r in rows if a <= r[0] < b)
        print(f"  {name}: {dict(doms)}")

    # Sizing exercise, report only: k such that saturate(median raw)=0.5, using the back-solved
    # raw band's MIDPOINT as the point estimate (disclosed as imprecise -- 2-decimal source data).
    print("\n" + "=" * 110)
    print("Re-normalisation sizing exercise (REPORT ONLY, imprecise -- see raw-band caveat above)")
    print("=" * 110)
    for name, (a, b) in periods.items():
        vals = [r[5] for r in rows if a <= r[0] < b]
        d = describe(vals)
        if d is None:
            continue
        lo, hi = raw_band(d["median"])
        mid = (lo + hi) / 2.0
        print(f"  {name}: median c={d['median']:.2f} -> raw band {lo:.1f}-{hi:.1f}, midpoint k~={mid:.1f} "
              f"-> saturate(midpoint, k=midpoint)={mid/(mid+mid):.3f} (=0.5 by construction)")


if __name__ == "__main__":
    main()

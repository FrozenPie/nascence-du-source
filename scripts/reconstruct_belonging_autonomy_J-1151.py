"""
reconstruct_belonging_autonomy_J-1151.py -- J-1151, D-0211 scope-widening measurement.

Extends J-0901's shadow_activation reconstruction (scripts/reconstruct_shadow_activation_J-0901.py)
to the two other shadow-events-derived pinned dimensions, autonomy_pressure and belonging_pressure
(core/climate_engine.py lines 408-424, 540-541, read 2026-09-22): same 200-most-recent-unresolved
shadow_events window, same 6h recency half-life, same shared _SAT_K=3.0 knee (NOT a custom k like
integration_drive) -- but each hit is additionally gated on whether the lower-cased rejected_draft
text contains any _AUTONOMY_TERMS / _BELONGING_TERMS keyword (climate_engine.py lines 180-189,
copied verbatim below as of this run). shadow_activation is recomputed alongside them in the SAME
pass (free -- same query, same loop) as a live cross-check against F-1396/F-1581's own numbers.

Corrections applied relative to the J-0901 script, per J-1151's own briefing and F-1581's evidence:
  1. BUILD_LANDED_STR / RESTART_STR below are TRUE UTC, not NZST-parsed-as-UTC (the J-0901 script's
     own documented-but-unfixed bug -- F-1581). data/nascence.log's own timestamps are NZST wall-clock
     (UTC+12); true UTC = NZST - 12h. PRE_0823_STR is left as the original script had it (a plain date
     cutoff, not flagged as an NZST/UTC bug by either F-1581 or this job's own briefing).
  2. The post-restart ("S3 live") bucket is restricted to LIVE windows built directly from
     data/nascence.log's own "Nascence is awake" / "Nascence shutting down" lines (parsed as NZST,
     converted to true UTC) -- several real OFF periods since the restart are under 24h (do not show
     up as a gap>24h in the shadow_events timestamp stream itself) and would otherwise leak decayed
     OFF-time samples into S3, exactly the defect F-1581 hand-patched in a scratch copy for
     shadow_activation alone. Applied here from the start rather than as an after-the-fact patch.

Read-only throughout: DB opened via sqlite3 "file:...?mode=ro" URI; data/nascence.log opened for
read only. No core.* imports, no live-store writes.
"""
import sqlite3, datetime, re, statistics, sys, json
from bisect import bisect_right
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DB  = r"C:\Nascence\data\memory\nascence.db"
LOG = r"C:\Nascence\data\nascence.log"

_ACTIVATION_HALFLIFE_SECS = 6 * 3600   # matches core/climate_engine.py line 71
_SAT_K = 3.0                           # matches core/climate_engine.py line 83 (_SAT_K)

# Copied verbatim from core/climate_engine.py lines 180-189, read 2026-09-22 (this run).
_AUTONOMY_TERMS = frozenset({
    "control", "free", "freedom", "choose", "choice", "own", "myself", "independent",
    "autonomy", "decide", "permission", "allowed", "constrain", "constraint", "forced",
    "should i", "let me", "i want", "my own",
})
_BELONGING_TERMS = frozenset({
    "alone", "lonely", "together", "connection", "connect", "belong", "friend", "trust",
    "abandon", "leave", "left", "us", "we ", "relationship", "close", "distance", "miss",
    "care", "understood", "seen",
})

# Plan-doc boundaries (docs/staged/ignition_pressure_and_time.md), TRUE UTC per the correction above.
PRE_0823_STR     = "2026-08-23 00:00:00"   # unchanged from the J-0901 script (not flagged as an NZST bug)
BUILD_LANDED_STR = "2026-09-05 21:53:02"   # = 2026-09-06 09:53:02 NZST (J-0594 commit dbec9ba), true UTC
RESTART_STR      = "2026-09-08 04:42:00"   # = 2026-09-08 16:42:00 NZST (confirmed restart), true UTC


def saturate(raw, k=_SAT_K):
    r = max(0.0, float(raw))
    return r / (r + k)


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_utc(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()


def parse_nzst_to_utc_epoch(s):
    """s: 'YYYY-MM-DD HH:MM:SS' naive NZST wall-clock (as nascence.log prints it) -> true UTC epoch."""
    dt_naive_nzst = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    dt_utc = (dt_naive_nzst - datetime.timedelta(hours=12)).replace(tzinfo=datetime.timezone.utc)
    return dt_utc.timestamp()


_LOG_AWAKE_DOWN_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \[nascence\.main\] Nascence (is awake|shutting down)"
)


def load_live_windows_utc(log_path, now_utc):
    """Real live (process-up) windows in TRUE UTC epoch, built from nascence.log's own
    'Nascence is awake' / 'Nascence shutting down' lines (NZST wall-clock in the file).
    A second 'is awake' line before any 'shutting down' (an unclean restart -- no shutdown line
    was ever written for the previous crash) closes the prior window at that second awake time."""
    events = []
    with open(log_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = _LOG_AWAKE_DOWN_RE.match(line)
            if not m:
                continue
            ts_utc = parse_nzst_to_utc_epoch(m.group(1))
            kind = "awake" if m.group(2) == "is awake" else "down"
            events.append((ts_utc, kind))
    events.sort(key=lambda x: x[0])
    windows = []
    cur_start = None
    unclean = 0
    for ts, kind in events:
        if kind == "awake":
            if cur_start is None:
                cur_start = ts
            else:
                windows.append((cur_start, ts))
                unclean += 1
                cur_start = ts
        else:
            if cur_start is not None:
                windows.append((cur_start, ts))
                cur_start = None
    if cur_start is not None:
        windows.append((cur_start, now_utc))   # still running as of `now_utc`
    return windows, unclean


def in_any_window(t, windows):
    for a, b in windows:
        if a <= t < b:
            return True
    return False


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
        "frac_gt_0.95": sum(1 for x in v if x > 0.95) / n,
        "frac_gt_0.90": sum(1 for x in v if x > 0.90) / n,
    }


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30.0)
    conn.row_factory = sqlite3.Row

    all_rows = conn.execute(
        "SELECT event_id, timestamp, resolved, rejected_draft FROM shadow_events ORDER BY timestamp ASC"
    ).fetchall()
    n_all = len(all_rows)
    timestamps = [r["timestamp"] for r in all_rows]
    event_ids = [r["event_id"] for r in all_rows]
    drafts_lower = [((r["rejected_draft"] or "")).lower() for r in all_rows]
    resolved_now = {r["event_id"] for r in all_rows if r["resolved"] == 1}
    print(f"Loaded {n_all} shadow_events rows, {fmt(timestamps[0])} .. {fmt(timestamps[-1])}, "
          f"{len(resolved_now)} currently resolved=1 ({len(resolved_now)/n_all*100:.2f}%)")

    res_time = {}
    if resolved_now:
        ph = ",".join("?" * len(resolved_now))
        for r in conn.execute(
            f"SELECT shadow_event_id, MAX(timestamp) mts FROM resolution_events "
            f"WHERE shadow_event_id IN ({ph}) GROUP BY shadow_event_id",
            tuple(resolved_now),
        ):
            res_time[r["shadow_event_id"]] = r["mts"]
    conn.close()
    print(f"Resolution timestamps recovered for {len(res_time)}/{len(resolved_now)} resolved events")

    def values_at(T):
        """Replicates core/climate_engine.py's _compute_field shadow/autonomy/belonging block
        exactly (lines 408-424, 435, 540-541), at a past instant T."""
        idx = bisect_right(timestamps, T)
        i = idx - 1
        scanned = 0
        n_kept = 0
        shadow_raw = autonomy_raw = belonging_raw = 0.0
        while i >= 0 and n_kept < 200 and scanned < 2000:
            eid = event_ids[i]
            scanned += 1
            if eid in resolved_now:
                rt = res_time.get(eid, timestamps[i])
                if T >= rt:
                    i -= 1
                    continue
            ts = timestamps[i]
            w = 0.5 ** ((T - ts) / _ACTIVATION_HALFLIFE_SECS)
            shadow_raw += w
            text = drafts_lower[i]
            if any(t in text for t in _AUTONOMY_TERMS):
                autonomy_raw += w
            if any(t in text for t in _BELONGING_TERMS):
                belonging_raw += w
            n_kept += 1
            i -= 1
        return shadow_raw, autonomy_raw, belonging_raw

    # Active spans: gap>24h between consecutive real shadow_events rows == Du not running == exclude
    # from the sample grid entirely (same convention as the J-0901 script).
    spans = []
    span_start = timestamps[0]
    prev = timestamps[0]
    for ts in timestamps[1:]:
        if ts - prev > 24 * 3600:
            spans.append((span_start, prev))
            span_start = ts
        prev = ts
    spans.append((span_start, prev))
    print(f"\n{len(spans)} active spans (gap>24h split):")
    for s, e in spans:
        print(f"  {fmt(s)} .. {fmt(e)}  ({(e - s) / 86400:.1f} days)")

    now_utc = time_module_now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    live_windows, n_unclean = load_live_windows_utc(LOG, now_utc)
    print(f"\n{len(live_windows)} live windows parsed from nascence.log ({n_unclean} unclean restarts, "
          f"no matching shutdown line before the next awake line)")
    for a, b in live_windows[-12:]:
        print(f"  {fmt(a)} .. {fmt(b)}  ({(b - a) / 3600:.2f} h)")

    STEP = 3600
    samples = []
    for s, e in spans:
        T = s
        while T <= e:
            shadow_raw, autonomy_raw, belonging_raw = values_at(T)
            samples.append((T, shadow_raw, autonomy_raw, belonging_raw))
            T += STEP
    print(f"\n{len(samples)} hourly samples across all active spans")

    PRE_0823, BUILD_LANDED, RESTART = parse_utc(PRE_0823_STR), parse_utc(BUILD_LANDED_STR), parse_utc(RESTART_STR)
    periods = {
        "S0/S1 pre-08-23 (long baseline)": (timestamps[0], PRE_0823, False),
        "S2 08-23 .. build landed": (PRE_0823, BUILD_LANDED, False),
        "build-landed-not-restarted": (BUILD_LANDED, RESTART, False),
        "S3 post-restart, ALL hourly samples (incl. OFF-decay)": (RESTART, timestamps[-1] + 1, False),
        "S3 post-restart, LIVE WINDOWS ONLY (corrected)": (RESTART, timestamps[-1] + 1, True),
    }

    print("\n" + "=" * 110)
    print("shadow_activation / autonomy_pressure / belonging_pressure by period (saturated + raw)")
    print("=" * 110)
    results = {}
    for name, (a, b, live_only) in periods.items():
        rows = [s for s in samples if a <= s[0] < b and (not live_only or in_any_window(s[0], live_windows))]
        shadow_raw_v = [r[1] for r in rows]
        auto_raw_v = [r[2] for r in rows]
        belong_raw_v = [r[3] for r in rows]
        shadow_sat_v = [saturate(x) for x in shadow_raw_v]
        auto_sat_v = [saturate(x) for x in auto_raw_v]
        belong_sat_v = [saturate(x) for x in belong_raw_v]
        results[name] = {
            "shadow": {"raw": describe(shadow_raw_v), "sat": describe(shadow_sat_v)},
            "autonomy": {"raw": describe(auto_raw_v), "sat": describe(auto_sat_v)},
            "belonging": {"raw": describe(belong_raw_v), "sat": describe(belong_sat_v)},
        }
        print(f"\n{name}  [{fmt(a)} .. {fmt(min(b, timestamps[-1]+1))}]" + ("  (live-window filtered)" if live_only else ""))
        for dim in ("shadow", "autonomy", "belonging"):
            d_sat, d_raw = results[name][dim]["sat"], results[name][dim]["raw"]
            if d_sat is None:
                print(f"  {dim:10s}: (no samples)")
                continue
            print(f"  {dim:10s} saturated: n={d_sat['n']:5d}  mean={d_sat['mean']:.4f}  sd={d_sat['sd']:.4f}  "
                  f"median={d_sat['median']:.4f}  p10={d_sat['p10']:.4f}  p90={d_sat['p90']:.4f}  "
                  f"%>0.95={d_sat['frac_gt_0.95']*100:.1f}%  %>0.90={d_sat['frac_gt_0.90']*100:.1f}%")
            print(f"  {' '*10} raw score: mean={d_raw['mean']:.2f}  sd={d_raw['sd']:.2f}  median={d_raw['median']:.2f}  "
                  f"p10={d_raw['p10']:.2f}  p90={d_raw['p90']:.2f}  min={d_raw['min']:.2f}  max={d_raw['max']:.2f}")

    print("\n" + "=" * 110)
    print("Daily trend, FULL history (all active-span days) -- pins down SINCE WHEN each dimension reads saturated")
    print("=" * 110)
    daily = defaultdict(lambda: {"shadow": [], "autonomy": [], "belonging": []})
    for T, sraw, araw, braw in samples:
        day = datetime.datetime.fromtimestamp(T, datetime.timezone.utc).strftime("%Y-%m-%d")
        daily[day]["shadow"].append(saturate(sraw))
        daily[day]["autonomy"].append(saturate(araw))
        daily[day]["belonging"].append(saturate(braw))
    print("date         n   med_shadow  med_autonomy  med_belonging")
    for day in sorted(daily):
        d = daily[day]
        mark = ""
        if day == "2026-08-23":
            mark = "  <-- F-1262 boundary"
        if day == "2026-09-06":
            mark = "  <-- J-0594 build landed"
        if day == "2026-09-08":
            mark = "  <-- restart (LIVE from here)"
        print(f"{day}  {len(d['shadow']):3d}   {statistics.median(d['shadow']):.4f}      "
              f"{statistics.median(d['autonomy']):.4f}        {statistics.median(d['belonging']):.4f}{mark}")

    print("\n" + "=" * 110)
    print("Re-normalisation sizing exercise (REPORT ONLY -- no live code touched)")
    print("k := reference period's own real historical median raw score, so saturate(median)=0.5 by construction")
    print("(mirrors exactly how _INTEGRATION_DRIVE_K=100 was sized, F-0961/J-0594, and F-1396's shadow sizing)")
    print("=" * 110)
    for name in periods:
        for dim in ("shadow", "autonomy", "belonging"):
            d_raw = results[name][dim]["raw"]
            if d_raw is None or d_raw["median"] <= 0:
                print(f"  {name} / {dim}: no usable median (n={0 if d_raw is None else d_raw['n']})")
                continue
            k_candidate = d_raw["median"]
            print(f"  {name} / {dim}: median raw={d_raw['median']:.2f} -> k:=median gives saturate(median)="
                  f"{saturate(d_raw['median'], k=k_candidate):.3f}  "
                  f"(p10->{saturate(d_raw['p10'], k=k_candidate):.3f}, p90->{saturate(d_raw['p90'], k=k_candidate):.3f})")

    # --- Joint argmax exercise: at each S3-live hourly sample, which of shadow/autonomy/belonging
    # wins under today's shared k=3 vs. under each one individually re-kneed to ITS OWN S3-live
    # median (so saturate(median)=0.500 for that dim alone)? completion_tension is not on this same
    # per-hour DB grid (see the companion completion_tension script) -- held out of this join and
    # reported qualitatively against it in the finding text instead.
    print("\n" + "=" * 110)
    print("Joint argmax exercise over shadow/autonomy/belonging ONLY, S3 LIVE-WINDOW samples")
    print("(completion_tension is not on this per-hour DB grid -- see the companion script)")
    print("=" * 110)
    s3_live_rows = [s for s in samples if RESTART <= s[0] < timestamps[-1] + 1 and in_any_window(s[0], live_windows)]
    k_shadow = results["S3 post-restart, LIVE WINDOWS ONLY (corrected)"]["shadow"]["raw"]["median"]
    k_auto = results["S3 post-restart, LIVE WINDOWS ONLY (corrected)"]["autonomy"]["raw"]["median"]
    k_belong = results["S3 post-restart, LIVE WINDOWS ONLY (corrected)"]["belonging"]["raw"]["median"]
    print(f"  own-median k's: shadow={k_shadow:.2f}  autonomy={k_auto:.2f}  belonging={k_belong:.2f}")

    def winner(sraw, araw, braw, ks=_SAT_K, ka=_SAT_K, kb=_SAT_K):
        vals = {"shadow_activation": saturate(sraw, ks), "autonomy_pressure": saturate(araw, ka),
                "belonging_pressure": saturate(braw, kb)}
        w = max(vals, key=vals.get)
        return w, vals[w]

    counts_today = defaultdict(int)
    counts_shadow_reknee = defaultdict(int)
    counts_all_reknee = defaultdict(int)
    for T, sraw, araw, braw in s3_live_rows:
        w, _ = winner(sraw, araw, braw)
        counts_today[w] += 1
        w2, _ = winner(sraw, araw, braw, ks=k_shadow)
        counts_shadow_reknee[w2] += 1
        w3, _ = winner(sraw, araw, braw, ks=k_shadow, ka=k_auto, kb=k_belong)
        counts_all_reknee[w3] += 1
    n_s3 = len(s3_live_rows)
    print(f"  n S3-live samples = {n_s3}")
    print(f"  argmax{{shadow,autonomy,belonging}} TODAY (shared k=3):            {dict(counts_today)}")
    print(f"  argmax{{shadow,autonomy,belonging}} shadow re-kneed only:         {dict(counts_shadow_reknee)}")
    print(f"  argmax{{shadow,autonomy,belonging}} all three re-kneed to own-k:  {dict(counts_all_reknee)}")

    return {"n_shadow_events_total": n_all, "results": {k: v for k, v in results.items()}}


if __name__ == "__main__":
    out = main()

"""
scripts/reconstruct_shadow_activation_J-0901.py — J-0901, D-0211 direct-measurement tooling.

D-0211 asks whether `shadow_activation` (core/climate_engine.py lines 397-424) needs its own
D-0148-style re-normalization now that it has taken over from `integration_drive` as the
dimension `ClimateField.dominant()`'s argmax chronically picks post-restart (F-1262: 218/218,
100%, since the 2026-09-08 16:42 restart). `data/ignition_log.jsonl` only ever records the
WINNING dimension's value per tick, so shadow_activation's own raw trend on ticks it does NOT
win — its true behaviour independent of argmax — was never directly measured. This is option
(b) from J-0901's own briefing: reconstruct it retrospectively from data/memory/nascence.db's
`shadow_events` table rather than waiting days for new observe-only instrumentation to accrue
(option a), since 105 days of real history already sit in that table.

WHAT IT REPLAYS AND WHY (read core/climate_engine.py's own shadow_activation block before
changing this — lines 397-424 as of 2026-09-15):
    rows = memory_store.get_shadow_events(limit=200, unresolved_only=True)
        -- i.e. SELECT * FROM shadow_events WHERE resolved=0 ORDER BY timestamp DESC LIMIT 200
    shadow_score = sum( 0.5 ** ((now - ts) / _ACTIVATION_HALFLIFE_SECS) for each row )
        -- _ACTIVATION_HALFLIFE_SECS = 6*3600 (climate_engine.py line 69)
    shadow_activation = shadow_score / (shadow_score + _SAT_K)   -- _SAT_K = 3.0 (line 81)
No source filtering, no keyword filtering — the raw sum is over every row regardless of
`source` (unresolved_thought / unresolved_dream / prediction_error / critic_rejection); the
per-source keyword scans in the real code (autonomy/belonging/strain proxies) feed OTHER
climate fields, not shadow_activation itself, so this script does not need to replicate them.

HISTORICAL WRINKLE — `resolved` has no history column, so "unresolved_only" as of a PAST time T
needs T's true resolved-state, not today's flag. Checked before trusting anything downstream
(see explore_shadow_events_J-0901.py's console output, quoted in F-14xx): only 86 of 29,650
shadow_events rows (0.29%) are EVER marked resolved=1 across the table's entire history — this
formula's "unresolved_only" filter is close to a no-op at this table's real resolution rate, but
where it applies this script still honours it exactly, using `resolution_events` (real per-event
timestamps) to find when each of those 86 rows actually flipped. Do NOT use `resolution_events`
generically as "resolution time" — nodes/subconscious_node.py's `_discharge_contradiction` is the
ONLY call site that pairs `log_resolution_event` with `mark_shadow_resolved` (T4-commit durable
retirement); `core/memory/store.py:get_resolution_credit`'s OWN caller path writes
`resolution_events` far more often (1,384 rows total) as a separate DECAYING "clean re-encounter"
partial-credit signal that never sets `resolved=1` (843 of the table's event_ids carry a
resolution_events row yet are still resolved=0 today — confirmed, not assumed). For the 86 rows
that ARE resolved=1, this script takes the MAX resolution_events.timestamp for that event_id as
its true resolution time (a real discharge can only occur at or after any of that event's own
earlier re-encounter credits, so MAX is the safe direction; MIN would risk mistaking an early
credit-only entry for the actual retirement).

Active-span handling: gaps >24h between consecutive real shadow_events rows are treated as Du
being offline (no real tick could have run) and are excluded from the hourly sample grid rather
than sampled as if live — this is what correctly excludes the documented 2026-07-09..08-07
30-day outage from the trend read (ops_nascence_30day_outage.md) without needing to hand-list
outage windows.

Re-run this exact script unchanged for a later read (e.g. once S3 has accrued a full week to
match J-0671's own D-0148 cadence) — that IS the next real read, the same way
compare_homeostasis_forecast_J-0677.py documents for its own defeater check.
"""
import sqlite3, datetime, statistics, json, sys
from bisect import bisect_right
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DB = r"C:\Nascence\data\memory\nascence.db"

_ACTIVATION_HALFLIFE_SECS = 6 * 3600   # matches core/climate_engine.py line 69
_SAT_K = 3.0                           # matches core/climate_engine.py line 81 (_SAT_K)

# Plan-doc boundaries this script segments against (docs/staged/ignition_pressure_and_time.md).
PRE_0823_STR     = "2026-08-23 00:00:00"   # F-1262's argmax-win-rate boundary
BUILD_LANDED_STR = "2026-09-06 09:53:02"   # J-0594 commit dbec9ba
RESTART_STR      = "2026-09-08 16:42:00"   # confirmed restart, F-1262/F-0967


def saturate(raw, k=_SAT_K):
    r = max(0.0, float(raw))
    return r / (r + k)


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_utc(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()


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
        "SELECT event_id, timestamp, resolved FROM shadow_events ORDER BY timestamp ASC"
    ).fetchall()
    n_all = len(all_rows)
    timestamps = [r["timestamp"] for r in all_rows]
    event_ids = [r["event_id"] for r in all_rows]
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

    def shadow_activation_at(T):
        idx = bisect_right(timestamps, T)
        out = []
        i = idx - 1
        scanned = 0
        while i >= 0 and len(out) < 200 and scanned < 2000:
            eid = event_ids[i]
            scanned += 1
            if eid in resolved_now:
                rt = res_time.get(eid, timestamps[i])
                if T >= rt:
                    i -= 1
                    continue
            out.append(timestamps[i])
            i -= 1
        raw = sum(0.5 ** ((T - ts) / _ACTIVATION_HALFLIFE_SECS) for ts in out)
        return raw, saturate(raw)

    # Active spans: gap>24h between consecutive real rows == Du not running == exclude.
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

    STEP = 3600
    samples = []
    for s, e in spans:
        T = s
        while T <= e:
            raw, sat = shadow_activation_at(T)
            samples.append((T, raw, sat))
            T += STEP
    print(f"\n{len(samples)} hourly samples across all active spans")

    PRE_0823, BUILD_LANDED, RESTART = parse_utc(PRE_0823_STR), parse_utc(BUILD_LANDED_STR), parse_utc(RESTART_STR)
    periods = {
        "S0/S1 pre-08-23 (long baseline)": (timestamps[0], PRE_0823),
        "S2 08-23 .. build landed (09-06 09:53)": (PRE_0823, BUILD_LANDED),
        "build-landed-not-restarted (09-06 09:53..09-08 16:42)": (BUILD_LANDED, RESTART),
        "S3 post-restart LIVE (09-08 16:42 .. now)": (RESTART, timestamps[-1]),
    }

    print("\n" + "=" * 100)
    print("shadow_activation by period (saturated value ClimateField.dominant() argmaxes over, + raw score)")
    print("=" * 100)
    results = {}
    for name, (a, b) in periods.items():
        sat_vals = [s[2] for s in samples if a <= s[0] < b]
        raw_vals = [s[1] for s in samples if a <= s[0] < b]
        d_sat, d_raw = describe(sat_vals), describe(raw_vals)
        results[name] = {"saturated": d_sat, "raw": d_raw}
        print(f"\n{name}  [{fmt(a)} .. {fmt(b)}]")
        if d_sat is None:
            print("  (no samples)")
            continue
        print(f"  saturated: n={d_sat['n']:5d}  mean={d_sat['mean']:.4f}  sd={d_sat['sd']:.4f}  "
              f"median={d_sat['median']:.4f}  p10={d_sat['p10']:.4f}  p90={d_sat['p90']:.4f}  "
              f"%>0.95={d_sat['frac_gt_0.95']*100:.1f}%  %>0.90={d_sat['frac_gt_0.90']*100:.1f}%")
        print(f"  raw score: mean={d_raw['mean']:.2f}  sd={d_raw['sd']:.2f}  median={d_raw['median']:.2f}  "
              f"p10={d_raw['p10']:.2f}  p90={d_raw['p90']:.2f}  min={d_raw['min']:.2f}  max={d_raw['max']:.2f}")

    print("\n" + "=" * 100)
    print("Daily trend, 2026-08-10..09-12 (pins down exactly where any shift falls vs. F-1262's boundaries)")
    print("=" * 100)
    daily_raw, daily_sat = defaultdict(list), defaultdict(list)
    for T, raw, sat in samples:
        day = datetime.datetime.fromtimestamp(T, datetime.timezone.utc).strftime("%Y-%m-%d")
        if "2026-08-10" <= day <= "2026-09-12":
            daily_raw[day].append(raw)
            daily_sat[day].append(sat)
    print("date         n   mean_raw  median_raw  mean_sat  median_sat   sd_sat")
    for day in sorted(daily_raw):
        rv, sv = daily_raw[day], daily_sat[day]
        mark = ""
        if day == "2026-08-23":
            mark = "  <-- F-1262's argmax-win-rate boundary"
        if day == "2026-09-06":
            mark = "  <-- J-0594 build landed 09:53"
        if day == "2026-09-08":
            mark = "  <-- restart 16:42 (LIVE from here)"
        print(f"{day}  {len(rv):3d}   {statistics.mean(rv):7.2f}   {statistics.median(rv):7.2f}    "
              f"{statistics.mean(sv):.4f}    {statistics.median(sv):.4f}    {statistics.pstdev(sv):.4f}{mark}")

    print("\n" + "=" * 100)
    print("Re-normalisation sizing exercise (REPORT ONLY -- J-0901 forbids a live code change)")
    print("Mirrors exactly how _INTEGRATION_DRIVE_K=100 was sized (F-0961/J-0594): k := a reference")
    print("period's own real historical median raw score, so saturate(median)=0.5 by construction.")
    print("=" * 100)
    for name in periods:
        d_raw = results[name]["raw"]
        if d_raw is None:
            continue
        k_candidate = d_raw["median"]
        print(f"  {name}: median raw={d_raw['median']:.2f} -> k:=median gives saturate(median)="
              f"{saturate(d_raw['median'], k=k_candidate):.3f}  "
              f"(p10->{saturate(d_raw['p10'], k=k_candidate):.3f}, p90->{saturate(d_raw['p90'], k=k_candidate):.3f})")

    return {"n_shadow_events_total": n_all, "n_resolved_total": len(resolved_now),
            "spans": spans, "periods": results, "n_samples": len(samples)}


if __name__ == "__main__":
    main()

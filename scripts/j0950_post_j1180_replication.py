"""
J-0950 takeover (2026-10-03): OUT-OF-SAMPLE replication of F-1684 / F-1685 / F-1686 on the data that accrued AFTER those findings
(Du's runs from 2026-09-22 16:11 to 2026-10-01 07:17), and the natural experiment J-1180 handed us.

WHY NOW.  F-1684..F-1686 answered J-0950's two threads from data up to 2026-09-22 08:43.  Three things make a clean second read
possible and worth doing before the job is closed:

  1. J-1180's fix (merge f10500f, first live at the 2026-09-22 16:11:04 boot, F-1776) removed the 24-31 min process-wide sleep-entry
     freeze that F-1690 measured at 10-14 percent of live time.  That is a SIMILAR SHARE of event-loop wall-clock to the one Lead A
     freed: F-1238's telemetry-gap read has the per-tick overrun falling from ~2.0-2.26 s (pre-flip) to ~1.27 s (post-flip), i.e. about
     0.86 s freed out of every ~7.1 s tick period, ~12 percent of the climate loop's wall-clock (the 900 ms -> 30 ms parse of D-0154).
     The freeze is delivered as total stalls rather than a duty cycle, but that makes it a fair empirical test of the GENERIC mechanism
     "freeing shared-event-loop wall-clock raises autonomous cycle throughput" (Lead A's premise).  If that were true, internal cycles
     per LIVE hour should have risen at that boot.  F-1685's accumulator model
     predicts they do not, beyond a small accounting effect: the reservoirs fill per wall-clock second (ClimateEngine.tick measures
     dt = now - _last_tick), so a frozen or busy loop does not slow accumulation; it only delays NOTICING a crossing, and the
     overshoot is discarded at reset (section 3b simulates exactly that).
  2. The climate accumulator (core/climate_engine.py _DISS_RATE_*, _INTEGRATION_DRIVE_K, _IGNITION_THRESHOLD, the defensive cap) is
     byte-for-byte unchanged since F-1685 (only shadow-only commits 03510e9, 317b2fe, 690d086 touch that file), so F-1685's closed-form
     prediction  defensive fires per live hour = 3600 * (0.0010*strain + 0.0004*completion + 0.0002*shadow - 0.0006*integration)
     is a genuine prediction on this window, not a fit.
  3. NZ daylight saving began 2026-09-27 02:00 NZST -> 03:00 NZDT.  nascence.log is LOCAL wall clock.  The earlier J-0950 scripts
     hard-code UTC+12, which would turn the jump into a fake 60-minute silent window and put coupling_rides.jsonl (epoch UTC) one hour
     out of register after it.  Every timestamp here is converted to UTC with the right offset first, and the conversion is verified
     against coupling_rides.jsonl's own deliberation rows (section 0).

Definitions are DELIBERATELY the earlier script's (scripts/j0950_gap_distribution.py): boot lines cut periods; a gap spanning a boot,
a shutdown or an outage-abutting silent window is dropped; a 'nap' is a silent window >= 300 s inside a live process; net gap = raw gap
minus nap overlap; awake hours = live hours minus nap hours.  P4 below is the earlier script's P4 and must reproduce F-1684's table A
(live 87.2 h, awake 78.0 h, 241 internal starts, gated 81, defensive IGN 123, exploratory 119, net-gap median ~1099 s) -- section 1
checks that before anything new is trusted.

READ-ONLY on live data: it opens data/coupling_rides.jsonl and data/climate_reknee_shadow.jsonl for reading and the events file
written by scripts/j0950_parse_cycle_events.py (which itself only reads data/nascence.log).  No core/ imports.  Writes nothing.

  python scripts/j0950_post_j1180_replication.py --events <events_since_0916.jsonl> [--rides C:\\Nascence\\data\\coupling_rides.jsonl]
"""
from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import json
import random
import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")

STALL_MIN_S = 300.0
BARRIER_ABUT_S = 90.0
BLOCK_S = 6 * 3600.0

# accumulator constants, core/climate_engine.py lines 129-132, 134 (verified unchanged at HEAD 2026-10-03)
RATE_STRAIN, RATE_COMPL, RATE_SHADOW, RATE_INTEG = 0.0010, 0.0004, 0.0002, -0.0006
RATE_EXPLORE, THRESHOLD = 0.0004, 1.0


def local(y, mo, d, hh=0, mi=0, ss=0) -> float:
    """'local seconds': proleptic-Gregorian ordinal * 86400 + clock seconds -- the parser's own representation."""
    return _dt.date(y, mo, d).toordinal() * 86400 + hh * 3600 + mi * 60 + ss


DST_JUMP_LOCAL = local(2026, 9, 27, 2, 0, 0)        # first local second that does not exist (02:00 NZST -> 03:00 NZDT)
EPOCH_ORD = _dt.date(1970, 1, 1).toordinal() * 86400


def utc(tl: float) -> float:
    """local-seconds -> UTC epoch seconds.  UTC+12 before the jump, UTC+13 after it."""
    return tl - EPOCH_ORD - (12 * 3600 if tl < DST_JUMP_LOCAL else 13 * 3600)


def fmt(u: float) -> str:
    """UTC epoch -> NZ wall clock string (applies the same DST rule backwards)."""
    off = 12 if u < utc(DST_JUMP_LOCAL) else 13
    return (_dt.datetime(1970, 1, 1) + _dt.timedelta(seconds=u + off * 3600)).strftime("%m-%d %H:%M:%S")


def L(y, mo, d, hh=0, mi=0, ss=0) -> float:
    return utc(local(y, mo, d, hh, mi, ss))


def q(a, p):
    return float(np.percentile(a, p)) if len(a) else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--rides", default=r"C:\Nascence\data\coupling_rides.jsonl")
    ap.add_argument("--reknee", default=r"C:\Nascence\data\climate_reknee_shadow.jsonl")
    ap.add_argument("--reps", type=int, default=4000)
    a = ap.parse_args()

    # ------------------------------------------------------------------ load + convert to UTC
    raw = [json.loads(l) for l in open(a.events, encoding="utf-8")]
    ev = []
    for e in raw:
        e = dict(e)
        e["t"] = utc(e["t"])
        if "t2" in e:
            e["t2"] = utc(e["t2"])
        ev.append(e)
    eof_t = [e for e in ev if e["k"] == "eof"][0]["t"]
    boots = sorted(e["t"] for e in ev if e["k"] == "boot")
    shuts = sorted(e["t"] for e in ev if e["k"] == "shut")
    barriers = sorted(boots + shuts)
    silent = [(e["t"], e["t2"]) for e in ev if e["k"] == "silent" and e["t2"] - e["t"] >= 120.0]   # DST artefact drops out here
    n_dst_artefacts = sum(1 for e in raw if e["k"] == "silent" and (utc(e["t2"]) - utc(e["t"])) < 120.0)

    naps, outages = [], []
    for (t, t2) in silent:
        abut = any(abs(s - t) < 2.0 for s in shuts) or any(t2 - 5.0 <= b <= t2 + BARRIER_ABUT_S for b in boots)
        if abut:
            outages.append((t, t2))
        elif t2 - t >= STALL_MIN_S:
            naps.append((t, t2))
    nap_starts = [n[0] for n in naps]

    def barrier_between(x, y):
        i = bisect.bisect_right(barriers, x)
        return i < len(barriers) and barriers[i] < y

    def outage_overlap(x, y):
        return any(t < y and t2 > x for (t, t2) in outages)

    def nap_overlap(x, y):
        tot = 0.0
        i = bisect.bisect_left(nap_starts, x - 3600 * 3)
        while i < len(naps) and naps[i][0] < y:
            t, t2 = naps[i]
            lo, hi = max(x, t), min(y, t2)
            if hi > lo:
                tot += hi - lo
            i += 1
        return tot

    segs = []
    for i, b in enumerate(boots):
        nb = boots[i + 1] if i + 1 < len(boots) else None
        sh = [s for s in shuts if s > b and (nb is None or s < nb)]
        if sh:
            end = sh[0]
        else:
            ends = [t for (t, t2) in outages if nb is not None and t2 - 5.0 <= nb <= t2 + BARRIER_ABUT_S and t > b]
            end = min(ends) if ends else (nb if nb is not None else eof_t)
        segs.append((b, end))
    seg_starts = [s[0] for s in segs]

    def live_awake(x, y):
        live = awake = 0.0
        for (b, e) in segs:
            lo, hi = max(x, b), min(y, e)
            if hi > lo:
                live += hi - lo
                awake += (hi - lo) - nap_overlap(lo, hi)
        return live, awake

    def seg_of(u):
        i = bisect.bisect_right(seg_starts, u) - 1
        return i if i >= 0 and u < segs[i][1] else None

    starts = sorted([e for e in ev if e["k"] == "start"], key=lambda e: e["t"])
    gate_ids = {e["id"] for e in ev if e["k"] == "gate"}
    complete = {e["id"]: e for e in ev if e["k"] == "complete"}
    gate = {e["id"]: e for e in ev if e["k"] == "gate"}
    internal = [e for e in starts if e["type"] == "internal"]
    humans = [e for e in starts if e["type"] == "human"]
    for e in internal:
        e["gated"] = e["id"] in gate_ids
    ign = sorted([e for e in ev if e["k"] == "ign"], key=lambda e: e["t"])
    ign_t = [e["t"] for e in ign]
    clim = sorted([e for e in ev if e["k"] == "clim"], key=lambda e: e["t"])

    rows = []
    for i in range(len(internal) - 1):
        x, y = internal[i]["t"], internal[i + 1]["t"]
        if barrier_between(x, y) or outage_overlap(x, y):
            continue
        raw_g = y - x
        rows.append({"t0": x, "t1": y, "raw": raw_g, "net": raw_g - nap_overlap(x, y)})

    # coupling_rides climate rows (epoch UTC) and deliberation rows (for the calibration check)
    crow, drow = [], []
    with open(a.rides, encoding="utf-8") as f:          # read-only
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            lp = r.get("loop")
            if lp == "climate":
                tp = r.get("tuple") or {}
                try:
                    crow.append((float(r["ts"]), float(tp["world_model_strain"]), float(tp["completion_tension"]),
                                 float(tp["shadow_activation"]), float(tp["integration_drive"])))
                except Exception:
                    pass
            elif lp == "deliberation":
                drow.append(float(r["ts"]))
    crow.sort()
    drow.sort()
    c_ts = [r[0] for r in crow]

    print("=" * 120)
    print(f"events: {a.events}   last timestamped log line (NZ wall clock): {fmt(eof_t)}   climate rows {len(crow)}, deliberation rows {len(drow)}")
    print(f"boots {len(boots)}, shutdowns {len(shuts)}, naps (silent >= {STALL_MIN_S:.0f}s inside a live process) {len(naps)}, "
          f"outage-abutting silent windows {len(outages)}; DST-jump artefact windows dropped by the UTC conversion: {n_dst_artefacts}")

    # ------------------------------------------------------------------ 0. calibration of the UTC conversion
    print("\n" + "=" * 120)
    print("0. TIME-BASE CHECK -- every '[CYCLE x] complete' log line should be followed 0-3 s later by a deliberation publish row "
          "(F-1319's calibration), before AND after the 2026-09-27 DST jump")
    for label, lo, hi in (("pre-DST  (09-16 .. 09-27 01:59)", L(2026, 9, 16), L(2026, 9, 27, 1, 59, 59)),
                          ("post-DST (09-27 03:00 .. end)", L(2026, 9, 27, 3, 0, 0), eof_t + 1)):
        offs, n = [], 0
        for e in complete.values():
            if lo <= e["t"] < hi:
                n += 1
                j = bisect.bisect_left(drow, e["t"] - 2.0)
                if j < len(drow) and drow[j] <= e["t"] + 10.0:
                    offs.append(drow[j] - e["t"])
        print(f"   {label}: completes {n}, matched to a deliberation row within [-2, +10] s: {len(offs)} ({100.0 * len(offs) / max(1, n):.1f}%), "
              f"offset median {q(offs, 50):+.2f} s, p5 {q(offs, 5):+.2f}, p95 {q(offs, 95):+.2f}")
    print("   (a wrong offset would show up as ~0% matched; a correct one as ~100% at about +1 s)")

    # ------------------------------------------------------------------ periods
    P4 = ("P4  09-16 07:53:01 .. 09-22 08:43:40  (pre-J-1180: nap freeze present)", L(2026, 9, 16, 7, 53, 1), L(2026, 9, 22, 8, 43, 40))
    P5_lo, P5_hi = L(2026, 9, 22, 16, 11, 4), L(2026, 10, 1, 7, 17, 43)
    P5 = ("P5  09-22 16:11:04 .. 10-01 07:17:43  (post-J-1180: freeze gone)", P5_lo, P5_hi)
    P5_boots = [b for b in boots if P5_lo - 1 <= b < P5_hi]
    sub = []
    for i, b in enumerate(P5_boots):
        nb = P5_boots[i + 1] if i + 1 < len(P5_boots) else P5_hi
        sub.append((f"P5.{i + 1}  {fmt(b)[:11]} .. {fmt(nb)[:11]}", b - 1.0, nb - 1.0))
    P6 = ("P6  today's incarnation 10-03 06:55 .. end of log", L(2026, 10, 3, 6, 55, 0), eof_t + 1)
    all_periods = [("P4", P4), ("P5", P5)] + [(f"P5.{i + 1}", s) for i, s in enumerate(sub)] + [("P6", P6)]

    def period_stats(lo, hi):
        live, awake = live_awake(lo, hi)
        ints = [e for e in internal if lo <= e["t"] < hi]
        n_g = sum(1 for e in ints if e["gated"])
        n_h = sum(1 for e in humans if lo <= e["t"] < hi)
        fd = sum(1 for e in ign if lo <= e["t"] < hi and e["trig"] == "defensive")
        fe = sum(1 for e in ign if lo <= e["t"] < hi and e["trig"] == "exploratory")
        g = [r for r in rows if r["t0"] >= lo and r["t1"] <= hi]
        net = np.array([r["net"] for r in g], dtype=float)
        # climate dims: row-mean (F-1685's method) and time-weighted (weight = time since the previous row in the same live segment,
        # because ClimateEngine._tick_dissonance(dt) applies the CURRENT field to the whole dt since the previous tick)
        i0, i1 = bisect.bisect_left(c_ts, lo), bisect.bisect_left(c_ts, hi)
        sel = crow[i0:i1]
        rm = np.mean([r[1:] for r in sel], axis=0) if sel else np.full(4, np.nan)
        wsum, acc = 0.0, np.zeros(4)
        prev = None
        for r in sel:
            sg = seg_of(r[0])
            if prev is not None and sg is not None and sg == prev[0]:
                w = r[0] - prev[1]
                if 0 < w < 3 * 3600:
                    wsum += w
                    acc += w * np.array(r[1:])
            prev = (sg, r[0])
        tw = acc / wsum if wsum > 0 else np.full(4, np.nan)
        return {"live": live, "awake": awake, "n_int": len(ints), "gated": n_g, "human": n_h, "def": fd, "exp": fe, "net": net,
                "rm": rm, "tw": tw, "n_rows": len(sel), "n_clim_lines": sum(1 for c in clim if lo <= c["t"] < hi)}

    def delta_of(d4):
        return RATE_STRAIN * d4[0] + RATE_COMPL * d4[1] + RATE_SHADOW * d4[2] + RATE_INTEG * d4[3]

    # ------------------------------------------------------------------ 1. table A for every period
    print("\n" + "=" * 120)
    print("1. TABLE A -- boot-defined periods (UTC-correct).  P4 must reproduce F-1684's table A: live 87.2 h, awake 78.0 h, 241 internal starts "
          "(3.09/awake-h), gated 81, defensive IGN 123, exploratory 119, 238 gaps, net median ~1099 s, share<900s 0.37")
    S = {}
    for key, (name, lo, hi) in all_periods:
        s = period_stats(lo, hi)
        S[key] = s
        lh, ah = s["live"] / 3600.0, s["awake"] / 3600.0
        if lh <= 0:
            print(f"\n[{name}]  no live time")
            continue
        n = s["net"]
        print(f"\n[{name}]")
        print(f"   live {lh:6.1f} h   awake {ah:6.1f} h  (nap-stall {100 * (1 - ah / lh):4.1f}% of live)   internal starts {s['n_int']} "
              f"({s['n_int'] / lh:.2f}/live-h, {s['n_int'] / ah:.2f}/awake-h), gated {s['gated']}, human {s['human']}")
        print(f"   climate IGNITIONs: defensive {s['def']} ({s['def'] / lh:.2f}/live-h, {s['def'] / ah:.2f}/awake-h)  "
              f"exploratory {s['exp']} ({s['exp'] / lh:.2f}/live-h, {s['exp'] / ah:.2f}/awake-h)")
        if len(n):
            print(f"   net internal->internal gaps n={len(n)}: p25 {q(n, 25):.0f}  median {q(n, 50):.0f}  p75 {q(n, 75):.0f} s;  share<900s {float((n < 900).mean()):.2f}")

    # ------------------------------------------------------------------ 2. F-1685 accumulator model, out of sample
    print("\n" + "=" * 120)
    print("2. F-1685'S ACCUMULATOR ARITHMETIC AS A PREDICTION.  delta = 0.0010*strain + 0.0004*completion + 0.0002*shadow - 0.0006*integration (per s);"
          "\n   defensive fires per LIVE hour = 3600*delta (threshold 1.0, reservoir discharged at each fire, no cap binding: cap is 3 per hour).")
    print("   Dimension means come from coupling_rides.jsonl climate rows: 'row-mean' is F-1685's own method, 'time-wtd' weights each row by the time since the previous row")
    print("   in the same live segment.  Observed = '[climate] IGNITION (defensive)' lines per live hour.  F-1685 on its five periods: ratios 0.95-1.02.")
    print(f"   exploratory reference: 3600*0.0004*pull = 1.44*pull per hour (pull = saturate(open frontier) ~0.991 -> 1.43)")
    print(f"\n   {'period':<8}{'live h':>8}{'rows':>7}  {'strain':>7}{'compl':>7}{'shadow':>7}{'integ':>7}  {'pred/h(row)':>12}{'pred/h(twt)':>12}{'obs def/h':>10}{'obs/pred(row)':>14}{'obs/pred(twt)':>14}   {'obs exp/h':>9}")
    for key, (name, lo, hi) in all_periods:
        s = S[key]
        lh = s["live"] / 3600.0
        if lh <= 0 or not s["n_rows"]:
            continue
        pr, pt = 3600.0 * max(0.0, delta_of(s["rm"])), 3600.0 * max(0.0, delta_of(s["tw"]))
        od = s["def"] / lh
        print(f"   {key:<8}{lh:8.1f}{s['n_rows']:7d}  {s['rm'][0]:7.3f}{s['rm'][1]:7.3f}{s['rm'][2]:7.3f}{s['rm'][3]:7.3f}  {pr:12.3f}{pt:12.3f}{od:10.3f}"
              f"{od / pr if pr > 0 else float('nan'):14.3f}{od / pt if pt > 0 else float('nan'):14.3f}   {s['exp'] / lh:9.3f}")

    # ------------------------------------------------------------------ 3. the natural experiment: P4 -> P5
    print("\n" + "=" * 120)
    print("3. NATURAL EXPERIMENT: J-1180 removed the nap freeze at the 09-22 16:11 boot (P4 -> P5).  Everything else in the accumulator is unchanged.")
    print("   If freed loop wall-clock raised throughput, starts per LIVE hour would rise by about the freed share (P4 live/awake = %.3f).  F-1685 predicts no rise per live hour"
          % (S["P4"]["live"] / S["P4"]["awake"]))
    rng = random.Random(23)

    def block_tab(lo, hi):
        tab = []
        t = lo
        while t < hi:
            u = min(t + BLOCK_S, hi)
            live, awake = live_awake(t, u)
            if live > 0.25 * 3600:
                tab.append({"live": live, "awake": awake,
                            "n": sum(1 for e in internal if t <= e["t"] < u),
                            "d": sum(1 for e in ign if t <= e["t"] < u and e["trig"] == "defensive"),
                            "x": sum(1 for e in ign if t <= e["t"] < u and e["trig"] == "exploratory")})
            t = u
        return tab

    def ratio_ci(key, den, lo_a, hi_a, lo_b, hi_b):
        ta, tb = block_tab(lo_a, hi_a), block_tab(lo_b, hi_b)

        def rate(tab, idx):
            return sum(tab[i][key] for i in idx) / (sum(tab[i][den] for i in idx) / 3600.0)
        pa, pb = rate(ta, range(len(ta))), rate(tb, range(len(tb)))
        out = []
        for _ in range(a.reps):
            ia = [rng.randrange(len(ta)) for _ in ta]
            ib = [rng.randrange(len(tb)) for _ in tb]
            try:
                out.append(rate(tb, ib) / rate(ta, ia))
            except ZeroDivisionError:
                pass
        return pa, pb, pb / pa, float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), len(ta), len(tb)

    print(f"\n   {'metric':<34}{'P4 rate':>9}{'P5 rate':>9}{'P5/P4':>8}   {'95% CI (6-h block bootstrap)':<30}{'blocks P4/P5'}")
    for label, key, den in (("internal starts per LIVE hour", "n", "live"), ("internal starts per AWAKE hour", "n", "awake"),
                            ("defensive IGN per LIVE hour", "d", "live"), ("exploratory IGN per LIVE hour", "x", "live")):
        pa, pb, r, lo_c, hi_c, na, nb = ratio_ci(key, den, P4[1], P4[2], P5_lo, P5_hi)
        print(f"   {label:<34}{pa:9.3f}{pb:9.3f}{r:8.3f}   [{lo_c:6.3f}, {hi_c:6.3f}]{'':<12}{na}/{nb}")
    print("   Reading: the freed share is the P4 live/awake ratio above (about +%.0f%%).  A CI that excludes +%.0f%% on 'per LIVE hour' means freed loop time did NOT convert into starts."
          % (100 * (S["P4"]["live"] / S["P4"]["awake"] - 1), 100 * (S["P4"]["live"] / S["P4"]["awake"] - 1)))

    # gap distribution P4 vs P5
    n4, n5 = S["P4"]["net"], S["P5"]["net"]
    mw = stats.mannwhitneyu(n4, n5, alternative="two-sided")
    ks = stats.ks_2samp(n4, n5)
    print(f"\n   net-gap distribution P4 (n={len(n4)}) vs P5 (n={len(n5)}):  median {q(n4, 50):.0f} -> {q(n5, 50):.0f} s;  p25 {q(n4, 25):.0f} -> {q(n5, 25):.0f};  p75 {q(n4, 75):.0f} -> {q(n5, 75):.0f};"
          f"  share<900s {float((n4 < 900).mean()):.2f} -> {float((n5 < 900).mean()):.2f}")
    print(f"   Mann-Whitney p={mw.pvalue:.3g}, KS D={ks.statistic:.3f} p={ks.pvalue:.3g}  (gaps are autocorrelated over hours, so read these as descriptive, the block-bootstrap rates above as the test)")
    # raw (un-netted) gaps too: with no nap overlap net == raw in P5
    r4 = np.array([r["raw"] for r in rows if r["t0"] >= P4[1] and r["t1"] <= P4[2]])
    r5 = np.array([r["raw"] for r in rows if r["t0"] >= P5_lo and r["t1"] <= P5_hi])
    print(f"   RAW wall-clock gaps (what a watcher of the log sees): median {q(r4, 50):.0f} -> {q(r5, 50):.0f} s, mean {r4.mean():.0f} -> {r5.mean():.0f} s")

    # ------------------------------------------------------------------ 3b. what the accumulator model ALONE predicts for the freeze removal
    print("\n" + "=" * 120)
    print("3b. MODEL-ONLY PREDICTION OF WHAT REMOVING THE FREEZE SHOULD DO.  Simulate both reservoirs in WALL-CLOCK time (dt = now - last tick, as ClimateEngine.tick does) over the REAL live")
    print("    segments, with (i) the real P4 freeze windows, (ii) the same P4 segments with no freezes, (iii) the P5 segments.  A crossing that falls inside a freeze is noticed only when the")
    print("    freeze ends, and the overshoot is discarded at reset -- that is the only way a freeze can cost fires in this model.  No loop-time term is simulated.")

    def sim(seg_list, naps_list, a_def, a_exp, cb, T=5.0, refr=300.0):
        fd = fe = 0
        live = 0.0
        for (b, e) in seg_list:
            live += e - b
            nl = sorted([n for n in naps_list if n[1] > b and n[0] < e])
            rd = re = 0.0
            last_tick, last_ign = b, -1e9
            t = b + T
            while t < e:
                for (n0, n1) in nl:
                    if n0 <= t < n1:
                        t = n1                                  # frozen: the timer expiry is processed when the freeze ends
                        break
                if t >= e:
                    break
                dt = t - last_tick
                last_tick = t
                rd += a_def * dt
                re += a_exp * dt
                fired = False
                if t - last_ign >= refr:
                    if rd >= THRESHOLD:
                        rd, fd, fired = 0.0, fd + 1, True
                    elif re >= THRESHOLD:
                        re, fe, fired = 0.0, fe + 1, True
                if fired:
                    last_ign = t
                    t += cb                                      # the callback is awaited INSIDE the climate coroutine: no ticks meanwhile
                t += T
        return fd / (live / 3600.0), fe / (live / 3600.0), live / 3600.0

    def segs_in(lo, hi):
        return [(max(lo, b), min(hi, e)) for (b, e) in segs if min(hi, e) > max(lo, b)]
    # callback duration: median (IGNITION line -> cycle end) of the observed internal cycles, per period
    def med_cb(lo, hi):
        v = []
        for s in internal:
            if lo <= s["t"] < hi:
                j = bisect.bisect_right(ign_t, s["t"]) - 1
                t0 = ign_t[j] if j >= 0 and 0 <= s["t"] - ign_t[j] <= 900 else s["t"]
                end = complete[s["id"]]["t"] if s["id"] in complete else (gate[s["id"]]["t"] if s["id"] in gate else s["t"])
                if 0 < end - t0 < 900:
                    v.append(end - t0)
        return float(np.median(v)) if v else 120.0
    cb4, cb5 = med_cb(P4[1], P4[2]), med_cb(P5_lo, P5_hi)
    pull = 0.991
    a_exp = RATE_EXPLORE * pull
    a4 = max(0.0, delta_of(S["P4"]["rm"]))
    a5 = max(0.0, delta_of(S["P5"]["rm"]))
    s4 = segs_in(P4[1], P4[2])
    s5 = segs_in(P5_lo, P5_hi)
    naps4 = [n for n in naps if P4[1] <= n[0] < P4[2]]
    d_i, e_i, l_i = sim(s4, naps4, a4, a_exp, cb4)
    d_ii, e_ii, _ = sim(s4, [], a4, a_exp, cb4)
    d_iii, e_iii, l_iii = sim(s5, [], a5, a_exp, cb5)
    d_iv, e_iv, _ = sim(s4, [], a5, a_exp, cb5)       # P4 segments, P5's dimension mean: isolates the dimension change from the freeze change
    print(f"    callback (IGNITION -> cycle end) median: P4 {cb4:.0f} s, P5 {cb5:.0f} s;  constants: exploratory inflow {a_exp:.3e}/s, defensive inflow P4 {a4:.3e}/s, P5 {a5:.3e}/s")
    print(f"\n    {'simulation':<58}{'live h':>8}{'defensive /live-h':>19}{'exploratory /live-h':>21}")
    print(f"    {'(i)   P4 segments, real freeze windows, P4 dimensions':<58}{l_i:8.1f}{d_i:19.3f}{e_i:21.3f}")
    print(f"    {'(ii)  P4 segments, NO freezes,          P4 dimensions':<58}{l_i:8.1f}{d_ii:19.3f}{e_ii:21.3f}")
    print(f"    {'(iv)  P4 segments, NO freezes,          P5 dimensions':<58}{l_i:8.1f}{d_iv:19.3f}{e_iv:21.3f}")
    print(f"    {'(iii) P5 segments, NO freezes,          P5 dimensions':<58}{l_iii:8.1f}{d_iii:19.3f}{e_iii:21.3f}")
    print(f"    observed P4: defensive {S['P4']['def'] / (S['P4']['live'] / 3600):.3f}, exploratory {S['P4']['exp'] / (S['P4']['live'] / 3600):.3f};   observed P5: defensive {S['P5']['def'] / (S['P5']['live'] / 3600):.3f}, exploratory {S['P5']['exp'] / (S['P5']['live'] / 3600):.3f}")
    print(f"    model-only freeze effect on fires per live hour (ii)/(i): defensive {d_ii / d_i:.3f}, exploratory {e_ii / e_i:.3f}   -> what the P4->P5 exploratory ratio should be if ONLY wall-clock accumulation operates")
    print(f"    observed exploratory P5/P4 = {(S['P5']['exp'] / S['P5']['live']) / (S['P4']['exp'] / S['P4']['live']):.3f}   (6-h block bootstrap CI in section 3);   model-only prediction (iii)/(i) = {e_iii / e_i:.3f}")
    print(f"    model-only predicted defensive P5/P4 = {d_iii / d_i:.3f}  vs observed {(S['P5']['def'] / S['P5']['live']) / (S['P4']['def'] / S['P4']['live']):.3f}")

    # ------------------------------------------------------------------ 4. F-1686 replication: is the climate loop suspended during internal cycles?
    print("\n" + "=" * 120)
    print("4. F-1686 REPLICATION -- climate publish rows (tick() publishes at >= 1/min) inside internal-cycle spans (IGNITION line -> cycle end), spans >= 100 s")
    for key, (name, lo, hi) in (("P4", P4), ("P5", P5)):
        spans = []
        for s in internal:
            if not (lo <= s["t"] < hi):
                continue
            j = bisect.bisect_right(ign_t, s["t"]) - 1
            t0 = ign_t[j] if j >= 0 and 0 <= s["t"] - ign_t[j] <= 900 else s["t"]
            end = complete[s["id"]]["t"] if s["id"] in complete else (gate[s["id"]]["t"] if s["id"] in gate else s["t"])
            if end > t0:
                spans.append((t0, end))
        full = [w for w in spans if w[1] - w[0] >= 100]

        def inside(x, y):
            return bisect.bisect_left(c_ts, y) - bisect.bisect_right(c_ts, x)
        got = sum(inside(*w) for w in full)
        zero = sum(1 for w in full if inside(*w) == 0)
        exp_rows = sum((w[1] - w[0]) / 60.0 for w in full)
        # control: same lengths, random placement inside live, nap-free, cycle-free time
        naps_all = naps

        def overlap(x, y, wins):
            return sum(max(0.0, min(y, w1) - max(x, w0)) for (w0, w1) in wins)
        ce = cg = n = 0
        lens = [w[1] - w[0] for w in full]
        crng = random.Random(7)
        tries = 0
        while n < len(full) and tries < 200000 and lens:
            tries += 1
            Ln = crng.choice(lens)
            x = crng.uniform(lo, hi - Ln)
            y = x + Ln
            sg = seg_of(x)
            if sg is None or seg_of(y) != sg:
                continue
            if overlap(x, y, spans) > 0 or overlap(x, y, naps_all) > 0:
                continue
            n += 1
            ce += Ln / 60.0
            cg += inside(x, y)
        print(f"   {key}: internal cycles with span >= 100 s: {len(full)} of {len(spans)}; with ZERO climate rows inside: {zero}; rows expected at the 60 s floor: {exp_rows:.0f}, observed: {got};"
              f"  control windows {n}: expected {ce:.0f}, observed {cg}")
        # the earlier verdict demanded zero rows in EVERY cycle; list the exceptions so each one can be explained rather than waved through
        exc = [(w, inside(*w)) for w in full if inside(*w) > 0]
        print(f"        {len(exc)} exception cycle(s) with >= 1 row inside; share of expected rows absent: {100.0 * (1 - got / exp_rows):.1f}%")
        for (w0, w1), k in exc[:14]:
            i0, i1 = bisect.bisect_right(c_ts, w0), bisect.bisect_left(c_ts, w1)
            offs = ", ".join(f"{c_ts[i] - w0:+.3f}" for i in range(i0, min(i1, i0 + 4)))
            print(f"          span {fmt(w0)} -> {fmt(w1)} ({w1 - w0:.0f} s): {k} row(s) at offsets from the IGNITION line (s): {offs};  seconds before span end: "
                  + ", ".join(f"{w1 - c_ts[i]:.1f}" for i in range(i0, min(i1, i0 + 4))))
        # ClimateEngine.tick() publishes the row, THEN start_background calls _pending_trigger() -> _ignite() -> the IGNITION log line (publish_climate has exactly one
        # caller, climate_engine.py:919).  So the firing tick's own row sits within milliseconds of the IGNITION line; it is the tick that STARTED the cycle, not one that ran
        # during it.  A 1 s guard band at the start of each span removes it; anything left would be a genuine tick inside a cycle.
        got_g = sum(inside(w0 + 1.0, w1) for (w0, w1) in full)
        zero_g = sum(1 for (w0, w1) in full if inside(w0 + 1.0, w1) == 0)
        print(f"        with a 1 s guard band for the firing tick's own row: rows inside {got_g} (expected {exp_rows:.0f}); cycles with zero rows {zero_g} of {len(full)}")
        print(f"        verdict: {'climate loop SUSPENDED during internal cycles' if got_g == 0 and zero_g == len(full) and cg > 0.5 * ce else 'NOT clean -- inspect'}")

    # ------------------------------------------------------------------ 5. share of awake time spent inside internal cycles + nap stalls listing
    print("\n" + "=" * 120)
    print("5. STALLS.  Silent windows >= 300 s inside a live process ('naps'), by period; and the share of live time inside internal-cycle spans")
    for key, (name, lo, hi) in (("P4", P4), ("P5", P5)):
        nn = [(t, t2) for (t, t2) in naps if lo <= t < hi]
        tot = sum(t2 - t for (t, t2) in nn)
        live = S[key]["live"]
        print(f"   {key}: {len(nn)} stall windows, total {tot / 60:.0f} min = {100 * tot / live:.2f}% of {live / 3600:.1f} live h; lengths (min): "
              + (", ".join(f"{(t2 - t) / 60:.1f}" for (t, t2) in nn[:40]) + (" ..." if len(nn) > 40 else "")))
    print("   P5 stall windows are pre-shutdown/pre-boot wedges (a few minutes each, right before an incarnation ends), not nap freezes (24-31 min, ~every 70-75 min at night).")

    # ------------------------------------------------------------------ 6. what moved the defensive inflow: completion_raw (the live completion_tension input)
    print("\n" + "=" * 120)
    print("6. WHAT MOVED THE DEFENSIVE INFLOW.  completion_tension = _saturate(raw_contra) with raw_contra = tension_ledger.contradiction_pressure_for(tensions) (climate_engine.py:559-569, k = 3.0, so raw 30 -> 0.909,")
    print("   raw 3 -> 0.500, raw 0 -> 0).  data/climate_reknee_shadow.jsonl (J-1226) records that raw as completion_raw every ~60 s since the 09-25 19:21 boot.  6-hour table, NZ wall clock; boots/shutdowns marked.")
    marks = sorted([(b, "BOOT") for b in boots] + [(s, "SHUT") for s in shuts])
    rk = []
    try:
        with open(a.reknee, encoding="utf-8") as f:          # read-only
            for line in f:
                try:
                    r = json.loads(line)
                    rk.append((float(r["ts"]), float(r["completion_raw"])))
                except Exception:
                    pass
    except OSError as exc:
        print(f"   (reknee shadow log unreadable: {exc})")
    if rk:
        rk.sort()
        print(f"   {len(rk)} rows, first {fmt(rk[0][0])}, last {fmt(rk[-1][0])}")
        print(f"   {'bucket (NZ)':<18}{'n':>5}{'min':>8}{'median':>9}{'max':>8}{'share==3.0':>12}{'share==0':>10}   marks")
        t = rk[0][0] - (rk[0][0] % (6 * 3600))
        while t < rk[-1][0] + 1:
            u = t + 6 * 3600
            xs = [v for (ts, v) in rk if t <= ts < u]
            mk = ",".join(f"{n}@{fmt(x)[6:]}" for (x, n) in marks if t <= x < u)
            if xs:
                print(f"   {fmt(t):<18}{len(xs):5d}{min(xs):8.2f}{float(np.median(xs)):9.2f}{max(xs):8.2f}{sum(1 for v in xs if v == 3.0) / len(xs):12.2f}{sum(1 for v in xs if v == 0.0) / len(xs):10.2f}   {mk}")
            t = u
        tail = [v for (ts, v) in rk if ts >= rk[-1][0] - 3 * 86400]
        print(f"   last 3 days: {len(tail)} rows, distinct values {sorted(set(tail))[:8]}  (a measurement of a drained tension pressure would vary; a constant 3.0 is a pinned value)")
        # exact change points (the buckets above hide the shape)
        chg = []
        for i in range(1, len(rk)):
            if rk[i][1] != rk[i - 1][1]:
                chg.append((rk[i][0], rk[i - 1][1], rk[i][1]))
        print(f"\n   6b. CHANGE POINTS of completion_raw: {len(chg)} changes in {len(rk)} rows.  First 14 (the post-boot decay), changes per NZ day, last 8, and time since the last change:")
        for (ts, o, n) in chg[:14]:
            print(f"      {fmt(ts)}  {o:g} -> {n:g}")
        per_day: dict = {}
        for (ts, o, n) in chg:
            per_day[fmt(ts)[:5]] = per_day.get(fmt(ts)[:5], 0) + 1
        print("      changes per NZ day: " + ", ".join(f"{d} {c}" for d, c in sorted(per_day.items())))
        for (ts, o, n) in chg[-8:]:
            print(f"      {fmt(ts)}  {o:g} -> {n:g}")
        print(f"      last change {fmt(chg[-1][0])}; log ends {fmt(rk[-1][0])}: {(rk[-1][0] - chg[-1][0]) / 86400:.2f} days with no change in raw, across the boots at "
              + ", ".join(fmt(b) for b in boots if b > chg[-1][0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

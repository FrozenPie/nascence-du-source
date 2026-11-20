"""
J-0950 / Thread 2(b): did the inter-cycle-START gap DISTRIBUTION shift around 2026-09-09 19:01 (Lead A's go-live,
SUBC_LIGHT_READ / FRONTIER_LIGHT_READ, commit 63c24f2), and if not there, WHERE did it shift?  Finer than F-1319's
hourly buckets.

Input: the event file written by scripts/j0950_parse_cycle_events.py from data/nascence.log (read-only; this script
opens no live file at all).  Pure stdlib + numpy/scipy; no core/ imports; writes only --out-json.

Controls (all decided BEFORE looking at the shape):
  * Du-down: a gap between two consecutive starts is DROPPED if a boot ("Identity loaded") or a shutdown line lies
    inside it, or a silent window that abuts one (wedge-then-kill).  This handles clean AND unclean restarts and the
    ~14 s in-place reload at 2026-09-09 19:01:08 (a boot line, no shutdown line).
  * Naps: the log goes completely silent for 10-30 min at a time about every 70-75 min at night (silent windows,
    growing 10 -> 30 min over 2026-09-04..09-21).  Such a stall is process-wide (a cycle in flight, e.g. 02:11 -> 02:31 on
    09-10, "complete in 1211.2s", just sits through it).  Every gap is reported RAW and NET of stall overlap, and every
    per-hour rate is per AWAKE hour (live hours minus stall hours) as well as per live hour.
  * Human cycles: internal->internal gaps that contain a human-tagged start are reported separately.
  * Gated starts (thalamic gate silence, F-1564) are internal starts, kept (they consume the ignition), counted separately.
  * Code changes only take effect at a BOOT (a running process never reloads core/), so periods are cut at boot lines;
    a data flag (data/life_flags.json, read every 10 s) can flip mid-process.  The comparison that answers the job is
    therefore per boot-defined period, not per calendar hour or day.

NOTE (2026-10-03, J-0950 takeover): the local-time conversion in this script is a FIXED UTC+12 and is only valid for windows that end before
2026-09-27 02:00 NZST.  NZ daylight saving (UTC+13) began then: a window after it is one hour out of register against coupling_rides.jsonl
(epoch UTC), and the parser records the jump itself as a fake 60-minute silent window.  For anything later use
scripts/j0950_post_j1180_replication.py, whose utc() applies the right offset and is checked against the log (section 0 of its output).

Periods (all times local = UTC+12, see the parser's docstring):
  P0  09-05 19:15:24 .. 09-08 08:22:52   Phase 1 live; NO D-0148 option A (dbec9ba, committed 09-06 09:53), NO Lead A
  P1  09-08 16:41:59 .. 09-09 19:01:08   first boot after dbec9ba (option A live); Lead A NOT yet live
        (P1x = ..09-09 17:51:00, additionally before the Living World data-flag flip)
  P2  09-09 19:01:08 .. 09-11 13:18:28   Lead A live (63c24f2) + Living World flags on (17:51) + option A
  P3  09-11 13:50:42 .. 09-13 09:10:46   + J-0841 build (internal_cycle_habituation shadow)
  P4  09-16 07:53:01 .. end of log       later runs
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

STALL_MIN_S = 300.0          # silent window that counts as a process-wide stall (nap) when NOT abutting a restart
BARRIER_ABUT_S = 90.0        # a silent window ending within this of a boot line is a wedge/outage, not a nap
BLOCK_S = 6 * 3600.0         # bootstrap block length (gaps are autocorrelated over hours: rumination episodes)


def local(y, mo, d, hh=0, mi=0, ss=0) -> float:
    return _dt.date(y, mo, d).toordinal() * 86400 + hh * 3600 + mi * 60 + ss


def fmt(t: float) -> str:
    d = _dt.datetime.fromordinal(int(t // 86400)) + _dt.timedelta(seconds=t % 86400)
    return d.strftime("%m-%d %H:%M:%S")


def day_of(t: float) -> str:
    return _dt.date.fromordinal(int(t // 86400)).isoformat()


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def q(a, p):
    return float(np.percentile(a, p)) if len(a) else float("nan")


def summarize(vals, label, thresholds=(360, 600, 900, 1800, 3600)):
    a = np.asarray(vals, dtype=float)
    out = {"label": label, "n": int(a.size)}
    if a.size == 0:
        return out
    out.update({"min": float(a.min()), "p05": q(a, 5), "p10": q(a, 10), "p25": q(a, 25), "median": q(a, 50), "p75": q(a, 75),
                "p90": q(a, 90), "p95": q(a, 95), "mean": float(a.mean()), "max": float(a.max())})
    for th in thresholds:
        out[f"share<{th}s"] = float((a < th).mean())
    return out


def fmt_summary(s):
    if s["n"] == 0:
        return f"{s['label']:<26} n=0"
    return (f"{s['label']:<26} n={s['n']:<4} min={s['min']:5.0f} p10={s['p10']:5.0f} p25={s['p25']:5.0f} med={s['median']:5.0f} "
            f"p75={s['p75']:5.0f} p90={s['p90']:5.0f} mean={s['mean']:5.0f} | <360s {s['share<360s']:.2f} <600s {s['share<600s']:.2f} "
            f"<900s {s['share<900s']:.2f} <1800s {s['share<1800s']:.2f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--reps", type=int, default=4000)
    a = ap.parse_args()
    ev = load(a.events)
    eof_t = [e for e in ev if e["k"] == "eof"][0]["t"]

    boots = sorted(e["t"] for e in ev if e["k"] == "boot")
    shuts = sorted(e["t"] for e in ev if e["k"] == "shut")
    barriers = sorted(boots + shuts)
    silent = [(e["t"], e["t2"]) for e in ev if e["k"] == "silent"]

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

    def live_awake(x, y):
        live = awake = 0.0
        for (b, e) in segs:
            lo, hi = max(x, b), min(y, e)
            if hi > lo:
                live += hi - lo
                awake += (hi - lo) - nap_overlap(lo, hi)
        return live, awake

    starts = sorted([e for e in ev if e["k"] == "start"], key=lambda e: e["t"])
    gate_ids = {e["id"] for e in ev if e["k"] == "gate"}
    complete = {e["id"]: e for e in ev if e["k"] == "complete"}
    internal = [e for e in starts if e["type"] == "internal"]
    humans = [e for e in starts if e["type"] == "human"]
    human_t = [h["t"] for h in humans]
    for e in internal:
        e["gated"] = e["id"] in gate_ids
    ign = sorted([e for e in ev if e["k"] == "ign"], key=lambda e: e["t"])
    clim = sorted([e for e in ev if e["k"] == "clim"], key=lambda e: e["t"])

    rows = []
    for i in range(len(internal) - 1):
        x, y = internal[i]["t"], internal[i + 1]["t"]
        if barrier_between(x, y) or outage_overlap(x, y):
            continue
        raw = y - x
        net = raw - nap_overlap(x, y)
        hh = bisect.bisect_right(human_t, x)
        has_human = hh < len(human_t) and human_t[hh] < y
        rows.append({"t0": x, "t1": y, "raw": raw, "net": net, "human_between": has_human, "nap": (raw - net) > 1.0})

    print("=" * 118)
    print("events file:", a.events, "| last timestamped log line:", fmt(eof_t))
    print(f"boots {len(boots)}, shutdowns {len(shuts)}, naps(stalls >= {STALL_MIN_S:.0f}s inside a live process) {len(naps)}, "
          f"outage-abutting silent windows {len(outages)}")
    print(f"internal starts {len(internal)} (gated {sum(e['gated'] for e in internal)}), human starts {len(humans)}, "
          f"valid internal->internal gaps {len(rows)} of {len(internal)-1}")

    LW_FLIP = local(2026, 9, 9, 17, 51, 0)
    P = {
        "BASE": ("BASE  08-24 .. 09-05 19:15 (before Phase 1)", local(2026, 8, 24), local(2026, 9, 5, 19, 15, 24)),
        "P0": ("P0    09-05 19:15 .. 09-08 08:22 (no optA, no LeadA)", local(2026, 9, 5, 19, 15, 24), local(2026, 9, 8, 8, 22, 52)),
        "P1": ("P1    09-08 16:41 .. 09-09 19:01 (optA, pre LeadA)", local(2026, 9, 8, 16, 41, 59), local(2026, 9, 9, 19, 1, 8)),
        "P1x": ("P1x   09-08 16:41 .. 09-09 17:51 (also pre LW flags)", local(2026, 9, 8, 16, 41, 59), LW_FLIP),
        "P2": ("P2    09-09 19:01 .. 09-11 13:18 (optA+LeadA+LW)", local(2026, 9, 9, 19, 1, 8), local(2026, 9, 11, 13, 18, 28)),
        "P3": ("P3    09-11 13:50 .. 09-13 09:10 (+J-0841 build)", local(2026, 9, 11, 13, 50, 42), local(2026, 9, 13, 9, 10, 46)),
        "P4": ("P4    09-16 07:53 .. end (later runs)", local(2026, 9, 16, 7, 53, 1), eof_t + 1),
    }

    def gaps_in(lo, hi):
        return [r for r in rows if r["t0"] >= lo and r["t1"] <= hi]

    result = {"periods": {}}
    print("\n" + "=" * 118)
    print("A. INTERNAL-START GAP DISTRIBUTIONS by boot-defined period (seconds); raw = wall clock, net = minus nap-stall overlap")
    for key, (name, lo, hi) in P.items():
        sel = gaps_in(lo, hi)
        live, awake = live_awake(lo, hi)
        n_int = sum(1 for e in internal if lo <= e["t"] < hi)
        n_hum = sum(1 for e in humans if lo <= e["t"] < hi)
        n_gated = sum(1 for e in internal if lo <= e["t"] < hi and e["gated"])
        fd = sum(1 for e in ign if lo <= e["t"] < hi and e["trig"] == "defensive")
        fe = sum(1 for e in ign if lo <= e["t"] < hi and e["trig"] == "exploratory")
        cl = [c for c in clim if lo <= c["t"] < hi]
        print(f"\n[{name}]\n   live {live/3600:.1f} h, awake {awake/3600:.1f} h; internal starts {n_int} ({n_int/(live/3600):.2f}/live-h, "
              f"{n_int/(awake/3600):.2f}/awake-h), gated {n_gated}, human {n_hum}; climate IGNITIONs defensive {fd} ({fd/(awake/3600):.2f}/awake-h) "
              f"exploratory {fe} ({fe/(awake/3600):.2f}/awake-h)")
        if cl:
            print(f"   5-min climate telemetry (n={len(cl)}): integration_drive mean {np.mean([c['integ'] for c in cl]):.2f}, completion_tension "
                  f"{np.mean([c['compl'] for c in cl]):.2f}, world_model_strain {np.mean([c['strain'] for c in cl]):.2f}, dissonance(defensive) "
                  f"{np.mean([c['diss'] for c in cl]):.2f}")
        ps = {}
        for k2, vals in (("all_raw", [r["raw"] for r in sel]), ("all_net", [r["net"] for r in sel]),
                         ("nohuman_net", [r["net"] for r in sel if not r["human_between"]])):
            s = summarize(vals, k2)
            ps[k2] = s
            print("   " + fmt_summary(s))
        result["periods"][key] = {"name": name, "live_h": live / 3600, "awake_h": awake / 3600, "internal_starts": n_int, "gated": n_gated,
                                  "human": n_hum, "per_live_h": n_int / (live / 3600), "per_awake_h": n_int / (awake / 3600),
                                  "def_fires": fd, "expl_fires": fe, "def_per_awake_h": fd / (awake / 3600), "expl_per_awake_h": fe / (awake / 3600),
                                  "integ_mean": float(np.mean([c["integ"] for c in cl])) if cl else None,
                                  "compl_mean": float(np.mean([c["compl"] for c in cl])) if cl else None,
                                  "strain_mean": float(np.mean([c["strain"] for c in cl])) if cl else None, "gaps": ps}

    # ---------------- 6-hour exhibit around both boots -------------------------------------------------------------------
    print("\n" + "=" * 118)
    print("B. SIX-HOUR TABLE 09-07 .. 09-12: internal starts / awake hour, defensive vs exploratory IGNITIONs, integration_drive (boots marked)")
    lo0 = local(2026, 9, 7)
    marks = [(b, "BOOT") for b in boots if lo0 <= b < local(2026, 9, 13)] + [(s, "SHUT") for s in shuts if lo0 <= s < local(2026, 9, 13)] + [(LW_FLIP, "LW-FLAGS")]
    six = []
    for k in range(0, 5 * 4):
        lo, hi = lo0 + k * 6 * 3600, lo0 + (k + 1) * 6 * 3600
        live, awake = live_awake(lo, hi)
        n_int = sum(1 for e in internal if lo <= e["t"] < hi)
        fd = sum(1 for e in ign if lo <= e["t"] < hi and e["trig"] == "defensive")
        fe = sum(1 for e in ign if lo <= e["t"] < hi and e["trig"] == "exploratory")
        cl = [c for c in clim if lo <= c["t"] < hi]
        mk = ",".join(f"{n}@{fmt(t)[6:11]}" for (t, n) in marks if lo <= t < hi)
        rate = n_int / (awake / 3600) if awake > 900 else float("nan")
        print(f"{fmt(lo)[:11]} .. {fmt(hi - 1)[6:11]}  live {live/3600:4.1f}h awake {awake/3600:4.1f}h  internal {n_int:2d} ({rate:4.2f}/awake-h)  "
              f"IGN def {fd:2d} expl {fe:2d}  integ {np.mean([c['integ'] for c in cl]) if cl else float('nan'):4.2f}  {mk}")
        six.append({"lo": fmt(lo), "awake_h": awake / 3600, "internal": n_int, "def": fd, "expl": fe})
    result["six_hour"] = six

    # ---------------- tests ----------------------------------------------------------------------------------------------
    def blocks_for(sel, key):
        d = {}
        for r in sel:
            d.setdefault(int(r["t0"] // BLOCK_S), []).append(r[key])
        return {k: np.asarray(v, dtype=float) for k, v in d.items()}

    def boot_median_ci(a_blocks, b_blocks, reps=a.reps, seed=17):
        rng = random.Random(seed)
        ka, kb = list(a_blocks), list(b_blocks)
        diffs, ratios = [], []
        for _ in range(reps):
            xa = np.concatenate([a_blocks[rng.choice(ka)] for _ in ka])
            xb = np.concatenate([b_blocks[rng.choice(kb)] for _ in kb])
            s0, s1 = float(np.median(xa)), float(np.median(xb))
            diffs.append(s1 - s0)
            if s0:
                ratios.append(s1 / s0)
        return (float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5)), float(np.percentile(ratios, 2.5)), float(np.percentile(ratios, 97.5)))

    def rate_ci(lo_a, hi_a, lo_b, hi_b, reps=a.reps, seed=23):
        """Block bootstrap (6 h blocks of wall clock) of rate(b)/rate(a), rate = internal starts per AWAKE hour."""
        def block_tab(lo, hi):
            tab = []
            k0, k1 = int(lo // BLOCK_S), int(hi // BLOCK_S)
            for k in range(k0, k1 + 1):
                bl, bh = max(lo, k * BLOCK_S), min(hi, (k + 1) * BLOCK_S)
                if bh <= bl:
                    continue
                lv, aw = live_awake(bl, bh)
                if aw <= 0:
                    continue
                tab.append((sum(1 for e in internal if bl <= e["t"] < bh), aw))
            return tab
        ta, tb = block_tab(lo_a, hi_a), block_tab(lo_b, hi_b)
        rng = random.Random(seed)
        out = []
        for _ in range(reps):
            sa = [ta[rng.randrange(len(ta))] for _ in ta]
            sb = [tb[rng.randrange(len(tb))] for _ in tb]
            ra = sum(x for x, _ in sa) / sum(w for _, w in sa)
            rb = sum(x for x, _ in sb) / sum(w for _, w in sb)
            out.append(rb / ra)
        return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))

    print("\n" + "=" * 118)
    print("C. TESTS (gap distributions: Mann-Whitney, two-sample KS, 6-h-block bootstrap 95% CI of the MEDIAN difference/ratio; rates: block bootstrap CI of the ratio)")
    comps = [("P0", "P1", "option A went live (first boot after dbec9ba)"), ("P1", "P2", "Lead A boot 09-09 19:01 (+ LW flags 17:51): THE JOB'S PIVOT"),
             ("P1x", "P2", "same, with the Living-World-flag hour also removed from 'before'"), ("P2", "P3", "1st vs 2nd continuous post-Lead-A run"),
             ("P1", "P4", "pre-Lead-A optA vs later runs"), ("P0", "P2", "the naive 'pre vs post 09-09 19:01' comparison F-1319/F-1566 implied")]
    result["tests"] = {}
    for ka, kb, why in comps:
        na, la, ha = P[ka]
        nb, lb, hb = P[kb]
        sa, sb = gaps_in(la, ha), gaps_in(lb, hb)
        print(f"\n{ka} -> {kb}: {why}")
        for key in ("raw", "net"):
            xa = np.array([r[key] for r in sa]); xb = np.array([r[key] for r in sb])
            u = stats.mannwhitneyu(xb, xa, alternative="two-sided")
            ks = stats.ks_2samp(xb, xa)
            lo_d, hi_d, lo_r, hi_r = boot_median_ci(blocks_for(sa, key), blocks_for(sb, key))
            sh_a = float((xa < 900).mean()); sh_b = float((xb < 900).mean())
            print(f"   {key}: n {len(xa)} vs {len(xb)}; median {np.median(xa):.0f} -> {np.median(xb):.0f} s; median-diff 95% CI [{lo_d:.0f}, {hi_d:.0f}] s, ratio [{lo_r:.2f}, {hi_r:.2f}]; "
                  f"share<900s {sh_a:.2f} -> {sh_b:.2f}; MW p={u.pvalue:.3g}; KS D={ks.statistic:.2f} p={ks.pvalue:.3g}")
            result["tests"][f"{ka}->{kb}:{key}"] = {"why": why, "n_a": len(xa), "n_b": len(xb), "median_a": float(np.median(xa)), "median_b": float(np.median(xb)),
                                                   "diff_ci": [lo_d, hi_d], "ratio_ci": [lo_r, hi_r], "share900_a": sh_a, "share900_b": sh_b,
                                                   "mw_p": float(u.pvalue), "ks_D": float(ks.statistic), "ks_p": float(ks.pvalue)}
        ra = result["periods"][ka]["per_awake_h"]; rb = result["periods"][kb]["per_awake_h"]
        r_lo, r_hi = rate_ci(la, ha, lb, hb)
        print(f"   internal starts per awake-h: {ra:.2f} -> {rb:.2f} (ratio {rb/ra:.2f}, 6-h-block bootstrap 95% CI [{r_lo:.2f}, {r_hi:.2f}]); "
              f"defensive IGNITIONs/awake-h {result['periods'][ka]['def_per_awake_h']:.2f} -> {result['periods'][kb]['def_per_awake_h']:.2f}; "
              f"exploratory {result['periods'][ka]['expl_per_awake_h']:.2f} -> {result['periods'][kb]['expl_per_awake_h']:.2f}")
        result["tests"][f"{ka}->{kb}:rate"] = {"a": ra, "b": rb, "ratio": rb / ra, "ratio_ci": [r_lo, r_hi]}

    # ---------------- cycle durations ------------------------------------------------------------------------------------
    print("\n" + "=" * 118)
    print("D. COMPLETED internal-cycle DURATIONS ('complete in X s'; cycles overlapping a nap stall or a restart excluded) -- what Lead A's event-loop mechanism most directly predicts")
    def clean_dur(lo, hi):
        out = []
        for e in internal:
            c = complete.get(e["id"])
            if not c or not (lo <= e["t"] < hi):
                continue
            if nap_overlap(e["t"], c["t"]) > 1.0 or outage_overlap(e["t"], c["t"]) or barrier_between(e["t"], c["t"]):
                continue
            out.append(c["dur"])
        return out
    dur = {k: np.array(clean_dur(P[k][1], P[k][2])) for k in P}
    for k in P:
        d = dur[k]
        if d.size:
            print(f"   {P[k][0]:<52} n={d.size:<4} p10={q(d,10):5.1f} p25={q(d,25):5.1f} med={q(d,50):5.1f} p75={q(d,75):5.1f} p90={q(d,90):5.1f} mean={d.mean():5.1f}")
    result["durations"] = {k: summarize(dur[k], k, thresholds=(60, 90, 120)) for k in P}
    for ka, kb in (("P1", "P2"), ("P0", "P1"), ("P1", "P4")):
        u = stats.mannwhitneyu(dur[kb], dur[ka], alternative="two-sided")
        print(f"   {ka} -> {kb}: median {np.median(dur[ka]):.1f} -> {np.median(dur[kb]):.1f} s (Hodges-Lehmann shift approx {np.median(dur[kb]) - np.median(dur[ka]):+.1f} s), MW p={u.pvalue:.3g}")
        result["tests"][f"dur {ka}->{kb}"] = {"median_a": float(np.median(dur[ka])), "median_b": float(np.median(dur[kb])), "mw_p": float(u.pvalue)}

    # ---------------- ignition -> cycle-start latency (the curiosity node's LLM call, run inside the climate loop's callback) ----
    print("\n" + "=" * 118)
    print("D2. IGNITION -> CYCLE-START latency (seconds from the [climate] IGNITION line to the [CYCLE] internal: line; the curiosity node's run, "
          "awaited inside the ignition callback on the same loop) and a bootstrap CI of the median COMPLETED-cycle-duration difference")
    ign_t = [e["t"] for e in ign]
    def start_latency(lo, hi):
        out = []
        for e in internal:
            if not (lo <= e["t"] < hi):
                continue
            j = bisect.bisect_right(ign_t, e["t"]) - 1
            if j >= 0 and 0 <= e["t"] - ign_t[j] <= 600 and not nap_overlap(ign_t[j], e["t"]) > 1.0 and not barrier_between(ign_t[j], e["t"]):
                out.append(e["t"] - ign_t[j])
        return np.array(out)
    lat = {k: start_latency(P[k][1], P[k][2]) for k in P}
    for k in P:
        v = lat[k]
        if v.size:
            print(f"   {P[k][0]:<52} n={v.size:<4} p10={q(v,10):5.1f} p25={q(v,25):5.1f} med={q(v,50):5.1f} p75={q(v,75):5.1f} p90={q(v,90):5.1f} mean={v.mean():5.1f}")
    result["ign_to_start_latency"] = {k: summarize(lat[k], k, thresholds=(30, 60)) for k in P}
    rng2 = random.Random(31)
    for ka, kb, what, da, db in (("P1", "P2", "cycle duration", dur["P1"], dur["P2"]), ("P1", "P2", "ign->start latency", lat["P1"], lat["P2"])):
        diffs = []
        for _ in range(a.reps):
            xa = [da[rng2.randrange(len(da))] for _ in range(len(da))]
            xb = [db[rng2.randrange(len(db))] for _ in range(len(db))]
            diffs.append(float(np.median(xb) - np.median(xa)))
        u = stats.mannwhitneyu(db, da, alternative="two-sided")
        print(f"   {ka} -> {kb} {what}: median {np.median(da):.1f} -> {np.median(db):.1f} s; bootstrap 95% CI of the median difference [{np.percentile(diffs,2.5):+.1f}, {np.percentile(diffs,97.5):+.1f}] s; MW p={u.pvalue:.3g}")
        result["tests"][f"{what} {ka}->{kb}"] = {"median_a": float(np.median(da)), "median_b": float(np.median(db)), "diff_ci": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))], "mw_p": float(u.pvalue), "n_a": int(len(da)), "n_b": int(len(db))}

    # ---------------- placebo boots: does the method flag EVERY restart, or only the one where a code change bore on ignition? -------
    print("\n" + "=" * 118)
    print("G. BOOT-BY-BOOT specificity check: for every boot with a continuous live stretch of >= 8 awake hours on BOTH sides (adjacent runs, "
          "the 'before' run being the one that ended just ahead of this boot), internal starts per awake hour and net gap median before -> after")
    G = []
    seg_list = [(b, e) for (b, e) in segs if b >= local(2026, 9, 2)]
    for i in range(1, len(seg_list)):
        (pb, pe), (nb_, ne_) = seg_list[i - 1], seg_list[i]
        if nb_ - pe > 12 * 3600 and False:
            continue
        lp, ap_ = live_awake(pb, pe)
        ln, an_ = live_awake(nb_, ne_)
        if ap_ < 8 * 3600 or an_ < 8 * 3600:
            continue
        rp = sum(1 for e in internal if pb <= e["t"] < pe) / (ap_ / 3600)
        rn = sum(1 for e in internal if nb_ <= e["t"] < ne_) / (an_ / 3600)
        gp = [r["net"] for r in gaps_in(pb, pe)]
        gn = [r["net"] for r in gaps_in(nb_, ne_)]
        if len(gp) < 8 or len(gn) < 8:
            continue
        u = stats.mannwhitneyu(gn, gp, alternative="two-sided")
        print(f"   boot {fmt(nb_)}: before {fmt(pb)[:11]}..{fmt(pe)[6:11]} ({ap_/3600:5.1f} awake h) {rp:4.2f}/awake-h, net median {np.median(gp):5.0f} s (n {len(gp)})  ->  "
              f"after ..{fmt(ne_)[6:11]} ({an_/3600:5.1f} awake h) {rn:4.2f}/awake-h, net median {np.median(gn):5.0f} s (n {len(gn)});  rate ratio {rn/rp:4.2f};  MW p={u.pvalue:.3g}")
        G.append({"boot": fmt(nb_), "rate_before": rp, "rate_after": rn, "median_before": float(np.median(gp)), "median_after": float(np.median(gn)), "mw_p": float(u.pvalue)})
    result["boot_by_boot"] = G

    # ---------------- nap-stall lengths (a direct measurement of what the heavy tick could contend with) --------------------
    print("\n" + "=" * 118)
    print("E. NAP-STALL LENGTHS per day (silent windows >= 300 s inside a live process; minutes): a heavy climate tick sharing the loop with the nap's work "
          "would predict shorter stalls after Lead A")
    by_day = {}
    for (t, t2) in naps:
        by_day.setdefault(day_of(t), []).append((t2 - t) / 60.0)
    for d in sorted(by_day):
        if d < "2026-09-03" or d > "2026-09-14":
            continue
        v = by_day[d]
        print(f"   {d}  n={len(v):2d}  median {np.median(v):5.1f} min  min {min(v):5.1f}  max {max(v):5.1f}")
    pre = [(t2 - t) / 60 for (t, t2) in naps if local(2026, 9, 8, 16, 41) <= t < P['P2'][1] and (t2 - t) < 22 * 60]
    post = [(t2 - t) / 60 for (t, t2) in naps if P['P2'][1] <= t < P['P2'][2] and (t2 - t) < 22 * 60]
    # regression of stall length on time, then residual at Lead A
    xs = np.array([t for (t, t2) in naps if local(2026, 9, 4) <= t < local(2026, 9, 14)])
    ys = np.array([(t2 - t) / 60 for (t, t2) in naps if local(2026, 9, 4) <= t < local(2026, 9, 14)])
    days = (xs - local(2026, 9, 4)) / 86400.0
    A = np.vstack([days, np.ones_like(days)]).T
    coef, res, _, _ = np.linalg.lstsq(A, ys, rcond=None)
    resid = ys - A @ coef
    step = (xs >= P["P2"][1])
    print(f"   linear trend 09-04..09-13: {coef[0]:+.2f} min/day (intercept {coef[1]:.1f} min); residual mean before Lead A {resid[~step].mean():+.2f} min, after {resid[step].mean():+.2f} min "
          f"(n {int((~step).sum())} vs {int(step.sum())})")
    result["nap_trend"] = {"slope_min_per_day": float(coef[0]), "resid_pre": float(resid[~step].mean()), "resid_post": float(resid[step].mean())}

    if a.out_json:
        with open(a.out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, ensure_ascii=False)
        print("\nwrote", a.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

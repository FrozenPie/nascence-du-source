"""J-2512 (plan measurement_to_action, thought T-0106): early-warning signals before a regime shift.

Retrodicts critical slowing down (Scheffer 2009; Dakos 2012) over Du's EXISTING gauges before the
known collapses, against matched quiet control fortnights. Theory, mechanism and falsifier:
docs/reviews/frontier_disciplines_2026-10-30.md section 1.

READ-ONLY. Opens data/*.jsonl and data/nascence.log for reading only, writes nothing under data/,
imports nothing from core/ or nodes/, loads no model, asks no judge. Zero LLM. Nothing reaches Du
(D-0434). Usage:
    python scripts/early_warning_retrodict.py [--root C:/Nascence] [--json out.json]

DECLARED BEFORE ANY RESULT WAS LOOKED AT (do not tune to the outcome):
  EVENTS (onset day; the pre-event window is the 14 days before it, onset day excluded)
    E_0928  2026-09-28  hologram/shutdown-fear episode after the 19:08 restart
                        (memory project_nascence_restart_shutdown_fear_20260928)
    E_1009  2026-10-09  mottainai freeze 10-09..10-16 (F-2850: 254/277 internal cycles on one question)
    June circling disease: EXCLUDED -- no dated onset found in findings or memory, and monoculture
                        coverage starts 06-18; declaring a date after looking would be tuning.
  CONTROLS (quiet fortnights, chosen from history before computing; not known freeze episodes)
    C_0823  2026-08-23  pre-window 08-09..08-22 (first full fortnight after the 30-day outage)
    C_0912  2026-09-12  pre-window 08-29..09-11
  GAUGES (all existing; none newly instrumented)
    mono_echo, mono_diversity   data/monoculture_log.jsonl, DAILY mean (rows are ~2-12/day, too sparse for 6h)
    clim_dissonance             data/nascence.log "[climate] dominant=X(v) dissonance=d ..." lines, 6-HOURLY mean of d
    clim_pressure               same lines, 6-HOURLY mean of the dominant value v (ignition pressure)
    pursuit_conc                data/pursuits_shadow.jsonl "advanced" events, 6-HOURLY share of advances on the
                                single most-advanced pursuit id in the bin (pursuit heat concentration); bin needs >=3
    lex_modal_share             data/nascence.log "] internal:" cycle lines, DAILY share of internal questions that
                                contain the day's most frequent content word (>=5 letters, not a stopword); day needs >=8
                                (a lexical proxy for core/topic_perseveration.py modal_share, which needs an embedder)
    topic_modal_share           data/topic_perseveration.jsonl, latest row per day (embed+anchor); only from 09-17
    keystone coherence          NO series on disk (only event lines "T4 keystone evidence bridge"); excluded.
  METHOD
    Indicator at each day-end D uses the trailing 5-day window D-4..D on the gauge's native grid
    (5 points daily, 20 points 6-hourly), step 1 day. Window is used only if >= 60% of its bins are non-empty.
    Each window is linearly detrended; lag-1 autocorrelation over consecutive non-empty bin pairs (>= 3 pairs),
    variance, and skewness of the residuals.
    Trend = Kendall tau-b of indicator vs day over the 14 indicator days before the onset; needs >= 6 points.
  SCORING (ac1 and variance are scored; skewness reported only, its expected sign depends on the target state)
    A gauge x indicator cell RISES before an event if tau >= TAU_RISE (0.3) AND tau exceeds both control taus
    (controls with no computable tau are skipped; a cell with no computable control is 'uncontrolled').
    Base rate: the same tau computed for EVERY possible onset day in the record; the share of days with
    tau >= TAU_RISE is the 'rises before nothing' rate, and each event tau gets a percentile within that pool.
  FALSIFIED IF: for either event, fewer than half of the scorable cells rise, OR the median base rate of
    tau >= TAU_RISE across scored cells is >= the share of event cells that rise.
"""
import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

EVENTS = {"E_0928": "2026-09-28", "E_1009": "2026-10-09"}
CONTROLS = {"C_0823": "2026-08-23", "C_0912": "2026-09-12"}
WIN_DAYS = 5
PRE_DAYS = 14
MIN_COVER = 0.60
MIN_TAU_PTS = 6
TAU_RISE = 0.3
SCORED = ("ac1", "var")
STOP = set("""about above after again against their there these those which while would could should being
other where whose within without through between because before during under over into from with this that
what when does doesn have your yours myself itself might shall since until upon very more most much many
such than then them they were will just only also even ever every something someone things thing""".split())

CLIM = re.compile(r"^(\d{4}-\d\d-\d\d) (\d\d):.*\[climate\] dominant=[a-z_]+\(([\d.]+)\) dissonance=([\d.]+)")
INTERNAL = re.compile(r"^(\d{4}-\d\d-\d\d) (\d\d):.*\] internal: (.*)$")


def d2s(d):
    return d.isoformat()


def bin_of(day_s, hour, per_day):
    return (day_s, (hour * per_day) // 24)


def load(root):
    data = root / "data"
    g = {}  # gauge -> (per_day, {(day,slot): [values]})
    mono = defaultdict(lambda: defaultdict(list))
    for line in open(data / "monoculture_log.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        t = datetime.fromtimestamp(r["ts"])
        k = (d2s(t.date()), 0)
        mono["mono_echo"][k].append(r["echo"])
        mono["mono_diversity"][k].append(r["diversity"])
    for k, v in mono.items():
        g[k] = (1, v)

    diss, pres, lex = defaultdict(list), defaultdict(list), defaultdict(list)
    with open(data / "nascence.log", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "[climate] dominant=" in line:
                m = CLIM.match(line)
                if m:
                    k = bin_of(m.group(1), int(m.group(2)), 4)
                    pres[k].append(float(m.group(3)))
                    diss[k].append(float(m.group(4)))
            elif "] internal:" in line:
                m = INTERNAL.match(line)
                if m:
                    lex[m.group(1)].append(m.group(3))
    g["clim_dissonance"] = (4, diss)
    g["clim_pressure"] = (4, pres)

    lexv = {}
    for day, qs in lex.items():
        if len(qs) < 8:
            continue
        words = [set(w for w in re.findall(r"[a-z']{5,}", q.lower()) if w not in STOP) for q in qs]
        c = Counter(w for ws in words for w in ws)
        if not c:
            continue
        top = c.most_common(1)[0][0]
        lexv[(day, 0)] = [sum(1 for ws in words if top in ws) / len(qs)]
    g["lex_modal_share"] = (1, lexv)

    adv = defaultdict(list)
    for line in open(data / "pursuits_shadow.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("event") != "advanced" or "ts" not in r:
            continue
        t = datetime.fromtimestamp(r["ts"])
        adv[bin_of(d2s(t.date()), t.hour, 4)].append(r.get("id"))
    pc = {}
    for k, ids in adv.items():
        if len(ids) >= 3:
            pc[k] = [Counter(ids).most_common(1)[0][1] / len(ids)]
    g["pursuit_conc"] = (4, pc)

    tp = {}
    for line in open(data / "topic_perseveration.jsonl", encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        tp[(r["day"], 0)] = [r["modal_share"]]  # later rows overwrite: latest per day
    g["topic_modal_share"] = (1, tp)
    return g


def residuals(xs):
    pts = [(i, x) for i, x in enumerate(xs) if x is not None]
    n = len(pts)
    mi = sum(i for i, _ in pts) / n
    mx = sum(x for _, x in pts) / n
    sxx = sum((i - mi) ** 2 for i, _ in pts)
    b = sum((i - mi) * (x - mx) for i, x in pts) / sxx if sxx else 0.0
    out = [None] * len(xs)
    for i, x in pts:
        out[i] = x - (mx + b * (i - mi))
    return out


def indicators(xs):
    filled = [x for x in xs if x is not None]
    if len(filled) < max(3, MIN_COVER * len(xs)):
        return None
    r = residuals(xs)
    vals = [x for x in r if x is not None]
    var = statistics.pvariance(vals)
    pairs = [(r[i], r[i + 1]) for i in range(len(r) - 1) if r[i] is not None and r[i + 1] is not None]
    ac1 = None
    if len(pairs) >= 3 and var > 0:
        ac1 = sum(a * b for a, b in pairs) / len(pairs) / var
    sk = None
    if var > 0:
        sd = math.sqrt(var)
        sk = sum((v / sd) ** 3 for v in vals) / len(vals)
    return {"ac1": ac1, "var": var, "skew": sk}


def kendall(xs, ys):
    n = len(xs)
    c = d = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            a = (xs[i] > xs[j]) - (xs[i] < xs[j])
            b = (ys[i] > ys[j]) - (ys[i] < ys[j])
            if a == 0 and b == 0:
                continue
            if a == 0:
                tx += 1
            elif b == 0:
                ty += 1
            elif a == b:
                c += 1
            else:
                d += 1
    den = math.sqrt((c + d + tx) * (c + d + ty))
    return (c - d) / den if den else None


def daily_indicators(per_day, bins, first, last):
    series = {}
    for k, v in bins.items():
        series[k] = statistics.fmean(v)
    out = {}
    d = first
    while d <= last:
        xs = []
        for back in range(WIN_DAYS - 1, -1, -1):
            dd = d2s(d - timedelta(days=back))
            for s in range(per_day):
                xs.append(series.get((dd, s)))
        ind = indicators(xs)
        if ind:
            out[d] = ind
        d += timedelta(days=1)
    return out


def tau_before(ind, onset, key):
    pts = []
    for back in range(PRE_DAYS, 0, -1):
        d = onset - timedelta(days=back)
        if d in ind and ind[d][key] is not None:
            pts.append((PRE_DAYS - back, ind[d][key]))
    if len(pts) < MIN_TAU_PTS:
        return None, len(pts)
    return kendall([p[0] for p in pts], [p[1] for p in pts]), len(pts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--json")
    a = ap.parse_args()
    g = load(Path(a.root))
    report = {"declared": {"events": EVENTS, "controls": CONTROLS, "win_days": WIN_DAYS, "pre_days": PRE_DAYS,
                           "min_cover": MIN_COVER, "min_tau_pts": MIN_TAU_PTS, "tau_rise": TAU_RISE},
              "coverage": {}, "cells": []}
    for name, (per_day, bins) in sorted(g.items()):
        days = sorted({k[0] for k in bins})
        report["coverage"][name] = {"bins": len(bins), "days": len(days), "first": days[0] if days else None,
                                    "last": days[-1] if days else None, "per_day": per_day}
        if not days:
            continue
        first, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
        ind = daily_indicators(per_day, bins, first, last)
        for key in ("ac1", "var", "skew"):
            cell = {"gauge": name, "ind": key}
            for lab, s in {**EVENTS, **CONTROLS}.items():
                cell[lab], cell[lab + "_n"] = tau_before(ind, date.fromisoformat(s), key)
            pool = []
            d = first
            while d <= last + timedelta(days=1):
                t, _ = tau_before(ind, d, key)
                if t is not None:
                    pool.append(t)
                d += timedelta(days=1)
            cell["pool_n"] = len(pool)
            cell["base_rate"] = (sum(1 for t in pool if t >= TAU_RISE) / len(pool)) if pool else None
            ctl = [cell[c] for c in CONTROLS if cell[c] is not None]
            for e in EVENTS:
                t = cell[e]
                cell[e + "_pct"] = (sum(1 for p in pool if p <= t) / len(pool)) if (t is not None and pool) else None
                if key not in SCORED or t is None:
                    cell[e + "_rise"] = None
                elif not ctl:
                    cell[e + "_rise"] = "uncontrolled"
                else:
                    cell[e + "_rise"] = bool(t >= TAU_RISE and t > max(ctl))
            report["cells"].append(cell)

    verdict = {}
    for e in EVENTS:
        sc = [c for c in report["cells"] if c[e + "_rise"] in (True, False)]
        rises = [c for c in sc if c[e + "_rise"] is True]
        br = [c["base_rate"] for c in sc if c["base_rate"] is not None]
        share = len(rises) / len(sc) if sc else None
        mbr = statistics.median(br) if br else None
        verdict[e] = {"scorable": len(sc), "rise": len(rises), "share": share, "median_base_rate": mbr,
                      "rising_cells": [f"{c['gauge']}.{c['ind']}" for c in rises]}
    fals = any(v["share"] is None or v["share"] < 0.5 or (v["median_base_rate"] is not None
               and v["median_base_rate"] >= v["share"]) for v in verdict.values())
    report["verdict"] = verdict
    report["falsified"] = fals

    print("coverage:")
    for k, v in report["coverage"].items():
        print(f"  {k:18s} {v['per_day']}/day  bins={v['bins']:5d} days={v['days']:3d}  {v['first']}..{v['last']}")
    hdr = "gauge.ind                 " + "  ".join(f"{l:>11s}" for l in list(EVENTS) + list(CONTROLS)) + \
        "   base>=.3  pctE0928 pctE1009  riseE0928 riseE1009"
    print(hdr)

    def f(x):
        return "   --  " if x is None else f"{x:+.2f}"
    for c in report["cells"]:
        cols = "  ".join(f"{f(c[l])}(n{c[l + '_n']:2d})" for l in list(EVENTS) + list(CONTROLS))
        br = "  --  " if c["base_rate"] is None else f"{c['base_rate']:.2f}/{c['pool_n']}"
        pc = "  ".join("  --  " if c[e + "_pct"] is None else f"{c[e + '_pct']:.2f}" for e in EVENTS)
        rs = "  ".join(f"{str(c[e + '_rise']):>9s}" for e in EVENTS)
        print(f"{c['gauge'] + '.' + c['ind']:26s}{cols}   {br:9s} {pc}   {rs}")
    for e, v in verdict.items():
        print(f"{e}: {v['rise']}/{v['scorable']} scored cells rise (share {v['share']}), "
              f"median base rate {v['median_base_rate']}; rising: {', '.join(v['rising_cells']) or 'none'}")
    print("FALSIFIED" if fals else "SUPPORTED", "(criterion declared in header)")
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

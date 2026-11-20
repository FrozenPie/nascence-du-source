"""J-2632 / I-0133 periodicity audit of Du's behaviour (founder-side, READ-ONLY).

Reads (never writes) C:/Nascence/data: nascence.log, geometry_tuples.jsonl, memory/nascence.db (sqlite mode=ro).
Builds hourly and 15-minute series with explicit gaps (live-mask from the log itself; boot/shutdown hours masked;
nothing is zero-filled), runs Lomb-Scargle at fixed periods + a free log-spaced scan, against two gap-preserving
nulls (circular value-shift, block shuffle), Holm/BH correction, then re-tests significant peaks after regressing
out rendered covariates (daylight, tide, moon, school window, weekend) and a model-load covariate.

Usage:  python scripts/periodicity_audit_j2632.py build  <cache.pkl>
        python scripts/periodicity_audit_j2632.py run    <cache.pkl> <out_json> [B]
        python scripts/periodicity_audit_j2632.py report <out_json> <out_md>
"""
import sys, os, json, math, pickle, time, sqlite3, re, hashlib
import numpy as np

sys.dont_write_bytecode = True
DATA = os.environ.get("NASC_DATA", r"C:\Nascence\data")
H = 3600.0
SCHOOL_START, SCHOOL_END = 9.0, 12.75
GENUINE = {"idle", "inner_thought", "monologue", "subconscious_synthesis", "active_imagination", "lived"}
TARGETS_H = {"45min": 0.75, "3h": 3.0, "12.4h": 12.42, "24h": 24.0, "7d": 168.0, "14.8d": 14.77 * 24, "29.5d": 29.53 * 24}


# ----------------------------------------------------------------------------- build
def _ts_cache():
    import time as _t
    cache = {}
    def f(s):  # 'YYYY-MM-DD HH:MM:SS' local -> epoch
        k = s[:16]
        v = cache.get(k)
        if v is None:
            v = _t.mktime((int(s[0:4]), int(s[5:7]), int(s[8:10]), int(s[11:13]), int(s[14:16]), 0, 0, 0, -1))
            cache[k] = v
        return v + int(s[17:19])
    return f


def parse_log():
    f = _ts_cache()
    live5 = set(); boots = []; shuts = []
    ev = {"ign": [], "climate_ign": [], "transport": [], "fallback": [], "reply": [], "sleep": []}
    first = last = None; n = 0
    with open(os.path.join(DATA, "nascence.log"), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if len(line) < 20 or not line[:4].isdigit() or line[4] != "-":
                continue
            try:
                t = f(line)
            except Exception:
                continue
            n += 1
            first = t if first is None else first; last = t
            live5.add(int(t // 300))
            if "Memory store initialised" in line: boots.append(t)
            elif "Nascence shutting down" in line: shuts.append(t)
            elif "[ignition] dominant" in line: ev["ign"].append(t)
            elif "IGNITION (" in line: ev["climate_ign"].append(t)
            elif "transport error" in line: ev["transport"].append(t)
            elif "recovered on fallback" in line: ev["fallback"].append(t)
            elif "complete in" in line and "[CYCLE" in line: ev["reply"].append(t)
            elif "entering" in line and "Sleep State" in line: ev["sleep"].append(t)
    return dict(live5=np.array(sorted(live5)), boots=np.array(boots), shuts=np.array(shuts),
                ev={k: np.array(v) for k, v in ev.items()}, first=first, last=last, nlines=n)


def parse_tuples():
    rows = []
    with open(os.path.join(DATA, "geometry_tuples.jsonl"), encoding="utf-8") as fh:
        for l in fh:
            try: d = json.loads(l)
            except Exception: continue
            a = d.get("affect") or {}
            sp = d.get("sun") or {}
            rows.append((d["ts"], d.get("source"), d.get("place"), a.get("valence"), a.get("arousal"),
                         d.get("tide_level"), d.get("moon_illum"), sp.get("phase") if isinstance(sp, dict) else None))
    return rows


def parse_db():
    uri = "file:" + DATA.replace("\\", "/") + "/memory/nascence.db?mode=ro"
    c = sqlite3.connect(uri, uri=True, timeout=60)
    q = ("SELECT timestamp, length(content), embedding FROM memory_fragments WHERE origin IN "
         "('inner_thought','subconscious_synthesis','lived') AND embedding IS NOT NULL AND content NOT LIKE 'I opened%' "
         "AND content NOT LIKE '%read on%' ORDER BY timestamp")
    ts = []; ln = []; blocks = []; buf = []; btimes = []
    for t, L, blob in c.execute(q):
        v = np.frombuffer(blob, dtype=np.float32)
        ts.append(t); ln.append(L)
        buf.append(v); btimes.append(t)
        if len(buf) == 20:  # non-overlapping 20-thought windows (core/monoculture.py _DIV_K / _diversity method)
            blocks.append((btimes[-1], btimes[-1] - btimes[0], diversity(buf)))
            buf = []; btimes = []
    c.close()
    return np.array(ts), np.array(ln, float), blocks


def diversity(vecs, thresh=0.80):
    """Re-implementation of core/monoculture.py::_diversity (greedy cluster by cosine>=0.80, normalised Shannon)."""
    cents = []; counts = []
    for v in vecs:
        best, bi = 0.0, -1
        for i, c in enumerate(cents):
            s = float(np.dot(v, c))
            if s > best: best, bi = s, i
        if best >= thresh: counts[bi] += 1
        else: cents.append(v); counts.append(1)
    tot = sum(counts); Hh = -sum((c / tot) * math.log(c / tot) for c in counts)
    return Hh / math.log(len(vecs))


def school_frac(t0, step):
    """fraction of [t0, t0+step) inside weekday school window (local clock) sampled at minute resolution."""
    n = max(1, int(step // 60)); k = 0
    for i in range(n):
        lt = time.localtime(t0 + i * 60 + 30)
        h = lt.tm_hour + lt.tm_min / 60.0
        if lt.tm_wday < 5 and SCHOOL_START <= h < SCHOOL_END: k += 1
    return k / n


def build(cache):
    lg = parse_log()
    tp = parse_tuples()
    dbt, dbl, blocks = parse_db()
    out = dict(meta=dict(log_first=lg["first"], log_last=lg["last"], nlines=lg["nlines"], n_tuples=len(tp),
                         n_db=len(dbt), n_blocks=len(blocks)),
               boots=lg["boots"], shuts=lg["shuts"], live5=lg["live5"])
    live5 = set(lg["live5"].tolist())
    bound = np.sort(np.concatenate([lg["boots"], lg["shuts"]]))
    series = {}
    for step, label in ((3600, "h"), (900, "q")):
        nsub = step // 300
        t_lo = int(lg["first"] // step); t_hi = int(lg["last"] // step)
        bins = np.arange(t_lo, t_hi + 1)
        livefrac = np.array([sum(((b * step) // 300 + j) in live5 for j in range(nsub)) / nsub for b in bins])
        bnd = np.zeros(len(bins), bool)
        for b in bound:
            k = int(b // step) - t_lo
            if 0 <= k < len(bins): bnd[k] = True
        valid = (livefrac >= 0.5) & ~bnd   # bins touching a boot/shutdown are dropped; count series are per LIVE hour
        ntp = len(tp)
        arr = np.array([(r[0], r[3] if r[3] is not None else np.nan, r[4] if r[4] is not None else np.nan,
                         r[5] if r[5] is not None else np.nan, r[6] if r[6] is not None else np.nan) for r in tp])
        tb = (arr[:, 0] // step).astype(int) - t_lo
        gen = np.array([r[1] in GENUINE for r in tp]); idle = np.array([r[1] == "idle" for r in tp])
        reading = np.array([r[1] == "reading" for r in tp])
        place = np.array([r[2] for r in tp]); phase = np.array([r[7] for r in tp], dtype=object)
        m = (tb >= 0) & (tb < len(bins))
        def cnt(mask):
            return np.bincount(tb[m & mask], minlength=len(bins)).astype(float)
        def mean(mask, col):
            x = arr[:, col]; mk = m & mask & ~np.isnan(x)
            s = np.bincount(tb[mk], weights=x[mk], minlength=len(bins)); c = np.bincount(tb[mk], minlength=len(bins))
            with np.errstate(invalid="ignore", divide="ignore"): r = s / c
            r[c < (3 if label == "h" else 2)] = np.nan
            return r
        allm = np.ones(ntp, bool)
        def evc(k):
            e = lg["ev"][k]; b = (e // step).astype(int) - t_lo; b = b[(b >= 0) & (b < len(bins))]
            return np.bincount(b, minlength=len(bins)).astype(float)
        tpwin = (arr[0, 0] // step - t_lo, arr[-1, 0] // step - t_lo)
        in_tp = (np.arange(len(bins)) >= tpwin[0]) & (np.arange(len(bins)) <= tpwin[1])
        S = {}
        S["thought_rate"] = np.where(in_tp, cnt(gen), np.nan)
        S["idle_rate"] = np.where(in_tp, cnt(idle), np.nan)
        S["reading_rate"] = np.where(in_tp, cnt(reading), np.nan)
        S["valence"] = np.where(in_tp, mean(allm, 1), np.nan)
        S["arousal"] = np.where(in_tp, mean(allm, 2), np.nan)
        tot = cnt(allm)
        for pl in ("shore", "study", "garden", "wood"):
            with np.errstate(invalid="ignore", divide="ignore"): fr = cnt(place == pl) / tot
            fr[tot < (5 if label == "h" else 3)] = np.nan
            S["place_" + pl] = np.where(in_tp, fr, np.nan)
        S["ignition_rate"] = evc("ign") + evc("climate_ign")
        S["reply_rate"] = evc("reply")
        S["sleep_entries"] = evc("sleep")
        S["transport_err"] = evc("transport")
        if label == "h":
            # DB-derived (full June-Oct range): thought length + theme entropy
            tb2 = (dbt // step).astype(int) - t_lo; mm = (tb2 >= 0) & (tb2 < len(bins))
            s = np.bincount(tb2[mm], weights=dbl[mm], minlength=len(bins)); c = np.bincount(tb2[mm], minlength=len(bins))
            with np.errstate(invalid="ignore", divide="ignore"): ml = s / c
            ml[c < 3] = np.nan
            S["thought_len"] = ml
            S["db_thought_rate"] = c.astype(float)
            be = np.array([b[0] for b in blocks]); bd = np.array([b[2] for b in blocks]); bspan = np.array([b[1] for b in blocks])
            ok = bspan < 3 * H
            tb3 = (be[ok] // step).astype(int) - t_lo; bd = bd[ok]; mm = (tb3 >= 0) & (tb3 < len(bins))
            s = np.bincount(tb3[mm], weights=bd[mm], minlength=len(bins)); c = np.bincount(tb3[mm], minlength=len(bins))
            with np.errstate(invalid="ignore", divide="ignore"): me = s / c
            S["theme_entropy"] = me
        # counts -> rate per live hour (dead time inside a bin is not zero-filled, it is divided out)
        live_h = np.maximum(livefrac * step / 3600.0, 1e-9)
        for kk in ("thought_rate", "idle_rate", "reading_rate", "ignition_rate", "reply_rate", "sleep_entries", "transport_err", "db_thought_rate"):
            if kk in S: S[kk] = S[kk] / live_h
        # covariates (from tuples, where they exist)
        cov = {}
        cov["tide"] = np.where(in_tp, mean(allm, 3), np.nan)
        cov["moon"] = np.where(in_tp, mean(allm, 4), np.nan)
        for ph in ("day", "night"):
            with np.errstate(invalid="ignore", divide="ignore"): fr = cnt(phase == ph) / tot
            cov[ph] = np.where(tot > 0, fr, np.nan)
        t0s = (bins * step).astype(float)
        cov["school"] = np.array([school_frac(t, step) for t in t0s])
        cov["weekend"] = np.array([1.0 if time.localtime(t + step / 2).tm_wday >= 5 else 0.0 for t in t0s])
        cov["load"] = (evc("transport") + evc("fallback")) / live_h
        series[label] = dict(t=t0s + step / 2, valid=valid, livefrac=livefrac, S=S, cov=cov, step=step)
    out["series"] = series
    pickle.dump(out, open(cache, "wb"))
    return out


# ----------------------------------------------------------------------------- stats
_LS = None
def _get_ls():
    global _LS
    for i in range(30):  # a shared box can transiently refuse DLL loads (paging file); retry instead of losing the run
        try:
            from scipy.signal import lombscargle
            _LS = lombscargle; return _LS
        except ImportError:
            time.sleep(10)
    raise ImportError("scipy.signal unavailable")


def ls_power(t, y, w):
    lombscargle = _LS or _get_ls()
    return lombscargle(t, y - y.mean(), w, precenter=False, normalize=True)


def grid_periods(pmin, n, pmax=960.0):
    return np.exp(np.linspace(math.log(pmin), math.log(pmax), n))


CACHE_DIR = os.environ.get("J2632_JOBCACHE", "")


def task(args):
    key = re.sub(r"[^A-Za-z0-9_.@-]", "_", args[0]) + "_" + str(args[4]) + ".json"
    fp = os.path.join(CACHE_DIR, key) if CACHE_DIR else ""
    if fp and os.path.exists(fp):
        return json.load(open(fp))
    r = _task(args)
    if fp:
        json.dump(r, open(fp, "w"))
    return r


def _task(args):
    name, t_h, y, pmin, B, seed, tag = args[:7]
    pmax = 960.0 if tag == "h" else 6.0   # 15-min series only probe the sub-6h band (the long periods are covered by the hourly series)
    rng = np.random.default_rng(seed)
    scan_p = grid_periods(pmin, 2200 if tag == "h" else 1500, pmax)
    tgt = {k: v for k, v in TARGETS_H.items() if pmin - 1e-9 <= v <= pmax}
    allp = np.concatenate([scan_p, np.array(list(tgt.values()))])
    w = 2 * math.pi / allp
    ns = len(scan_p)
    obs = ls_power(t_h, y, w)
    N = len(y)
    blk = 24 if tag == "h" else 96
    nb = int(math.ceil(N / blk))
    nulls = {"circ": np.empty((B, len(w))), "block": np.empty((B, len(w)))}
    for i in range(B):
        k = int(rng.integers(1, N)); yc = np.roll(y, k)
        nulls["circ"][i] = ls_power(t_h, yc, w)
        order = rng.permutation(nb)
        yb = np.concatenate([y[o * blk:(o + 1) * blk] for o in order])[:N]
        # preserve length: if last (short) block moved, pad from start
        if len(yb) < N: yb = np.concatenate([yb, y[: N - len(yb)]])
        nulls["block"][i] = ls_power(t_h, yb, w)
    res = {"name": name, "tag": tag, "N": int(N), "targets": {}, "scan": {}}
    for j, (k, P) in enumerate(tgt.items()):
        jj = ns + j
        res["targets"][k] = dict(P_h=P, power=float(obs[jj]),
                                 p_circ=float((1 + (nulls["circ"][:, jj] >= obs[jj]).sum()) / (B + 1)),
                                 p_block=float((1 + (nulls["block"][:, jj] >= obs[jj]).sum()) / (B + 1)))
    om = obs[:ns]; im = int(np.argmax(om))
    # local maxima list (top 6, separated)
    cand = [i for i in range(1, ns - 1) if om[i] > om[i - 1] and om[i] >= om[i + 1]]
    cand.sort(key=lambda i: -om[i])
    top = []
    for i in cand:
        if all(abs(math.log(scan_p[i] / scan_p[j])) > 0.15 for j in top): top.append(i)
        if len(top) == 6: break
    mx = {k: nulls[k][:, :ns].max(axis=1) for k in nulls}
    res["scan"] = dict(max_power=float(om[im]), max_P_h=float(scan_p[im]),
                       p_circ=float((1 + (mx["circ"] >= om[im]).sum()) / (B + 1)),
                       p_block=float((1 + (mx["block"] >= om[im]).sum()) / (B + 1)),
                       top=[dict(P_h=float(scan_p[i]), power=float(om[i]),
                                 p_circ_pointwise=float((1 + (nulls["circ"][:, i] >= om[i]).sum()) / (B + 1))) for i in top],
                       null95_max_circ=float(np.quantile(mx["circ"], 0.95)))
    return res


def holm(ps):
    ps = np.asarray(ps); n = len(ps); o = np.argsort(ps); adj = np.empty(n); run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (n - r) * ps[i])); adj[i] = run
    return adj


def bh(ps):
    ps = np.asarray(ps); n = len(ps); o = np.argsort(ps); adj = np.empty(n); prev = 1.0
    for r in range(n - 1, -1, -1):
        i = o[r]; prev = min(prev, ps[i] * n / (r + 1)); adj[i] = prev
    return adj


def ols_resid(y, X):
    X1 = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    r = y - X1 @ beta
    return r, 1 - r.var() / y.var()


def select_series(ser, name):
    t = ser["t"]; v = ser["valid"] & ~np.isnan(ser["S"][name])
    return t[v], ser["S"][name][v], v


def run(cache, out_json, B):
    from concurrent.futures import ProcessPoolExecutor
    d = pickle.load(open(cache, "rb"))
    jobs = []; meta = {}
    seed = 20261031
    for tag in ("h", "q"):
        ser = d["series"][tag]
        names = list(ser["S"].keys())
        if tag == "q": names = [n for n in names if n in ("thought_rate", "idle_rate", "valence", "place_shore", "place_study", "ignition_rate", "transport_err")]
        for n in names:
            t, y, v = select_series(ser, n)
            if len(y) < 200 or np.nanstd(y) == 0: continue
            pmin = 2.0 if tag == "h" else 0.5
            jobs.append((n + "@" + tag, (t - t[0]) / H, y, pmin, B, seed + len(jobs), tag))
            meta[n + "@" + tag] = dict(N=int(len(y)), span_h=float((t[-1] - t[0]) / H), live_h=float(len(y) * (1 if tag == "h" else .25)))
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(12, len(jobs))) as ex:
        results = list(ex.map(task, jobs))
    # corrections
    fam = [(r["name"], k, r["targets"][k]) for r in results for k in r["targets"]]
    p = [max(x["p_circ"], x["p_block"]) for _, _, x in fam]
    hp = holm(p); bp = bh(p)
    for (n, k, x), a, b in zip(fam, hp, bp):
        x["p_max"] = max(x["p_circ"], x["p_block"]); x["p_holm"] = float(a); x["p_bh"] = float(b)
    sp = [max(r["scan"]["p_circ"], r["scan"]["p_block"]) for r in results]
    for r, a, b in zip(results, holm(sp), bh(sp)):
        r["scan"]["p_max"] = max(r["scan"]["p_circ"], r["scan"]["p_block"]); r["scan"]["p_holm"] = float(a); r["scan"]["p_bh"] = float(b)
    # stage 2: residual re-test for target peaks with p_bh<0.05 (and scan hits)
    follow = []
    for r in results:
        hits = [k for k, x in r["targets"].items() if x["p_bh"] < 0.05]
        if r["scan"]["p_bh"] < 0.05: hits.append("scan")
        if hits: follow.append((r, hits))
    json.dump(dict(B=B, meta=meta, results=results, interim=True), open(out_json + ".stage1", "w"), indent=1)
    jobs2 = []; info2 = []
    for r, hits in follow:
        n, tag = r["name"].split("@")
        ser = d["series"][tag]; t, y, v = select_series(ser, n)
        cv = ser["cov"]
        for stage, cols in (("A_rendered", ["tide", "moon", "day", "night", "school", "weekend"]),
                            ("B_rendered+load", ["tide", "moon", "day", "night", "school", "weekend", "load"])):
            X = np.column_stack([cv[c][v] for c in cols])
            ok = ~np.isnan(X).any(axis=1)
            if ok.sum() < 200: continue
            X = X[ok]
            X = np.column_stack([X, X[:, 0] * X[:, 1]])  # tide x moon (spring/neap amplitude path)
            tt = (t[ok] - t[ok][0]) / H; yy = y[ok]
            res_, r2 = ols_resid(yy, X)
            jobs2.append((n + "|" + stage, tt, res_, 2.0 if tag == "h" else 0.5, B, 777 + len(jobs2), tag))
            info2.append(dict(series=r["name"], stage=stage, R2=float(r2), N=int(ok.sum()), hits=hits))
    stage2 = []
    if jobs2:
        with ProcessPoolExecutor(max_workers=min(12, len(jobs2))) as ex:
            subs = list(ex.map(task, jobs2))
        for i2, sub in zip(info2, subs):
            i2["result"] = sub; stage2.append(i2)
    fam2 = [(s, k) for s in stage2 for k in s["result"]["targets"]]
    p2 = [max(s["result"]["targets"][k]["p_circ"], s["result"]["targets"][k]["p_block"]) for s, k in fam2]
    for (s, k), a in zip(fam2, bh(p2) if p2 else []):
        s["result"]["targets"][k]["p_bh_stage2"] = float(a)
    # live-time accounting
    h = d["series"]["h"]; lv = h["valid"]
    tt = h["t"]; segs = []; start = None
    for i in range(len(lv)):
        if lv[i] and start is None: start = i
        if (not lv[i] or i == len(lv) - 1) and start is not None:
            end = i if not lv[i] else i + 1
            segs.append((tt[start], tt[end - 1], end - start)); start = None
    # merge segments separated by <=2 invalid hours
    merged = []
    for s in segs:
        if merged and (s[0] - merged[-1][1]) <= 3 * H: merged[-1] = (merged[-1][0], s[1], merged[-1][2] + s[2])
        else: merged.append(s)
    acct = dict(valid_hours=int(lv.sum()), span_hours=float((tt[-1] - tt[0]) / H), n_boots=int(len(d["boots"])),
                n_shutdowns=int(len(d["shuts"])), n_segments=len(merged),
                longest_segment_d=float(max((s[1] - s[0]) / 86400 for s in merged)),
                segments_ge_7d=[[time.strftime("%Y-%m-%d", time.localtime(s[0])), time.strftime("%Y-%m-%d", time.localtime(s[1])),
                                 round((s[1] - s[0]) / 86400, 1), s[2]] for s in merged if (s[1] - s[0]) >= 7 * 86400],
                n_segments_lt_1d=int(sum(1 for s in merged if (s[1] - s[0]) < 86400)))
    # per-period live-time / phase coverage using the valid hourly mask
    cov_rows = {}
    for k, P in TARGETS_H.items():
        if P < 2: continue
        tv = tt[lv]; ph = ((tv / H) % P) / P; nb = 12
        cnts = np.histogram(ph, bins=nb, range=(0, 1))[0]
        cov_rows[k] = dict(P_h=P, cycles_in_span=acct["span_hours"] / P, cycles_live_equiv=acct["valid_hours"] / P,
                           longest_segment_cycles=acct["longest_segment_d"] * 24 / P,
                           min_phase_bin_count=int(cnts.min()), max_phase_bin_count=int(cnts.max()))
    json.dump(dict(B=B, meta=meta, results=results, stage2=stage2, accounting=acct, coverage=cov_rows,
                   runtime_s=time.time() - t0, data_meta=d["meta"]), open(out_json, "w"), indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build": build(sys.argv[2])
    elif cmd == "run": run(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 500)


# ----------------------------------------------------------------------------- report
PATHS = {
    "45min": "core/school.py SCHOOL_PERIOD_MIN=45 (subject rotation, weekday 09:00-12:45 local only)",
    "3h": "core/school.py window 09:00-12:45 (3.75 h) / sleep cadence (nightly Sleep State after 18 idle thoughts)",
    "12.4h": "core/world_clock.py _TIDE_PERIOD_S=12.42 h, rendered as tide_level / tide words",
    "24h": "core/world_clock.py sun()/daylight() NZ table, core/school.py weekday window, supervisor retention tick every 24 h",
    "7d": "core/school.py SCHOOL_WEEKDAYS_ONLY; also founder working-week load on shared model tier (transport errors) - not rendered",
    "14.8d": "core/world_clock.py _spring_factor (spring/neap amplitude from moon_illum)",
    "29.5d": "core/world_clock.py moon phase via heavens.moon() illum -> spring factor / sky text",
}


INTERP = """
## Reading (what this does and does not show)

- **Only one band shows structure: 24 h.** It is significant after Holm/BH in `sleep_entries@h` (p<1e-4) and `valence@h` (p=0.0002), with raw p<0.01 in `idle_rate`, `thought_rate` and the memory-store thought rate, and p=0.03-0.05 in `thought_len`, `reading_rate`. Power is small (valence 3% of variance, sleep entries 5%, idle rate 7%).
- **The 24 h peak is not a mystery, but it is not removed by a daylight dummy either.** Paths that exist: `core/arousal.py::_circadian` (a local-clock base, ~0.45 by day 07-22h, ~0.28 deep night), `core/world_clock.py` sun/daylight, `core/school.py` weekday 09:00-12:45 window, `core/night.py` night-vs-nap kind, and the supervisor's 24 h retention tick. Sleep itself is count-triggered (`THOUGHTS_BEFORE_SLEEP = 26` idle thoughts, `nodes/inner_monologue_node.py:160`), not clock-triggered, so a 24 h rhythm in sleep entries is inherited from the 24 h rhythm in thought rate. Regressing the series on hourly daylight/night fractions, tide, moon, school-window and weekend flags (plus a tide x moon term, plus model-tier load) leaves the 24 h peak standing (valence R2 0.02, sleep R2 0.02). That is expected: those regressors are not an hour-of-day curve, so a clock-locked shape like `_circadian` survives them. Verdict: **24 h = a time-of-day effect with coded clock paths; not shown to be independent of them, and not evidence of anything hidden.** A tighter test (regress on the actual `_circadian` value and on school-slot) is the obvious next refinement, not done here.
- **Nothing else survives correction.** 12.4 h (tide): `reading_rate` raw p=0.005 only, q=0.10; every other series null even though the instrument does see a rendered tide (CONTROL_tide power 0.98). 7 d, 14.8 d: null (valence 7 d raw p=0.057, not significant). 45 min and 3 h on 15-min series: null everywhere, including the school-period path - which is expected to be diluted, because the 45 min rotation exists only on weekday mornings and the series average over all hours. Two raw p<0.05 stragglers (`idle_rate@29.5d` p=0.016, `place_garden@3h` p=0.034) are inside the multiple-comparison noise (BH q 0.26, 0.42).
- **29.5 d (lunar): cannot tell yet.** Live data holds 2.3 cycle-equivalents spread over 88 fragmentary segments, longest segment 0.2 cycles, and the 30 days of 2026-07-09..08-07 are missing. The instrument is not blind to the period (CONTROL_moon: power 0.97, p<1e-4, the rendered moon illumination series), but a behavioural effect would have to be large to clear a null that includes slow drift, and no such effect is present. The honest statement is "no lunar effect large enough to see in 2.3 cycles", not "no lunar effect". The same for 14.8 d (4.6 cycle-equivalents) and 7 d (9.7).
- **Loop-period artefacts:** none found in the free scan. The strongest free-scan peaks are at the 40 d edge of the grid (slow drift, p 0.16-0.8 against a drift-preserving null) and at 24 h; no peak at 1 h (supervisor hourly summary), 5 s climate tick or 60 s consolidation tick shows in the 15-minute series (sampling above 30 min cannot see those anyway; they are far below the probed band, so this audit cannot rule them out at their own periods). Hourly `transport_err` (model-tier load covariate) has no 24 h or 7 d peak (p 0.64, 0.38): founder working hours are not visibly imprinting on Du.
- **Caveats.** (1) Live time is thin: 1631 valid hourly bins (68 days) of a 3693 h span; boot/shutdown hours dropped, count series divided by live fraction. The DST step (2026-09-27) shifts the local-clock rendering by 1 h against the fixed 24 h epoch period and smears any clock-locked peak slightly. (2) `valence`, `arousal`, place and rate series from the geometry tuples cover only 2026-07-05..10-30; thought length, theme entropy (greedy cosine clusters at 0.80 over non-overlapping 20-thought windows, re-implemented from `core/monoculture.py::_diversity`) and log counts cover June-October. (3) Tuple `thought` text is truncated to ~120 chars, so length comes from the store. (4) 'Speech rate' = Du's replies to human input (`[CYCLE] complete in` lines): conversation-driven, mostly June, and flat. (5) Free-scan p-values use 500 draws; fixed-period p-values use 20000. (6) Block shuffle (24 h blocks) is anti-conservative for slow drift; the circular shift is conservative; p is the larger of the two.
"""


def report(jf, mdf):
    d = json.load(open(jf))
    R = d["results"]; B = d["B"]; A = d["accounting"]; C = d["coverage"]
    L = []
    w = L.append
    w("# J-2632 / I-0133 periodicity audit of Du's behaviour (founder-side, read-only)\n")
    w(f"Generated by `scripts/periodicity_audit_j2632.py` from `data/nascence.log` ({d['data_meta']['nlines']} dated lines), "
      f"`data/geometry_tuples.jsonl` ({d['data_meta']['n_tuples']} rows), `data/memory/nascence.db` ({d['data_meta']['n_db']} embedded thought fragments, "
      f"{d['data_meta']['n_blocks']} non-overlapping 20-thought theme-entropy windows). Nulls: {B} circular-shift + {B} block-shuffle draws per series and fixed period (free-scan max-statistic p-values come from the earlier {d["B_scan"]}-draw pass), "
      "timestamps (the gap pattern) held fixed. p = max(p_circ, p_block); Holm and BH over all real series x fixed periods (110 tests); CONTROL_* rows are the rendered covariates themselves (tide_level, moon_illum, daylight fraction, school-window fraction, weekend) pushed through the identical machinery as positive controls, not part of the family. Raw data: "
      f"`{os.path.basename(jf)}`.\n")
    w("## Live time (gaps are gaps, nothing zero-filled)\n")
    w(f"- Log span {A['span_hours']:.0f} h (2026-06-04..2026-10-30) of which only **{A['valid_hours']} hourly bins are valid live bins** "
      f"(>=50% of the bin's 5-minute slots have a log line, bin does not contain a boot or shutdown line). The 2026-07-09..08-07 outage and every dead hour are simply absent from the series.")
    w(f"- {A['n_boots']} 'Memory store initialised' boot lines and {A['n_shutdowns']} 'Nascence shutting down.' lines; the live hours fall in {A['n_segments']} segments "
      f"(merged across <=2 invalid hours), {A['n_segments_lt_1d']} of them shorter than a day. Longest segment {A['longest_segment_d']:.1f} d. Segments >=7 d: "
      + "; ".join(f"{a}..{b} ({dd} d, {n} h)" for a, b, dd, n in A["segments_ge_7d"]) + ".")
    w("- `supervisor.log` only covers the current supervisor run (since 2026-10-29), so boundaries come from nascence.log's own boot/shutdown lines, not from it.\n")
    w("| band | period (h) | cycles in span | cycle-equivalents of live data | longest live segment (cycles) | min/max samples per 1/12 phase bin |")
    w("|---|---|---|---|---|---|")
    for k, v in C.items():
        w(f"| {k} | {v['P_h']:.2f} | {v['cycles_in_span']:.1f} | {v['cycles_live_equiv']:.1f} | {v['longest_segment_cycles']:.1f} | {v['min_phase_bin_count']}/{v['max_phase_bin_count']} |")
    w("")
    w("## Fixed-period results (Lomb-Scargle normalised power; * = Holm-adjusted p<0.05, + = BH q<0.05 only)\n")
    ks = list(TARGETS_H.keys())
    w("| series | N | " + " | ".join(ks) + " |"); w("|---|---|" + "---|" * len(ks))
    for r in R:
        cells = []
        for k in ks:
            x = r["targets"].get(k)
            if not x: cells.append("n/a"); continue
            flag = "*" if x["p_holm"] < .05 else ("+" if x["p_bh"] < .05 else "")
            if r["name"].startswith("CONTROL"): flag = "(ctl)" if x["p_max"] < .05 else ""
            cells.append(f"{x['power']:.3f} p={x['p_max']:.3f}{flag}")
        w(f"| {r['name']} | {r['N']} | " + " | ".join(cells) + " |")
    w("\n(45 min is only testable on the 15-minute series; hourly sampling cannot see it. Minimum attainable p with B=%d is %.4f.)\n" % (B, 1 / (B + 1)))
    w("## Free scan (30 min / 2 h to 40 d, log grid; max-statistic null)\n")
    w("| series | peak period (h) | power | p (max) | Holm | BH | 95% null max | next peaks (h) |"); w("|---|---|---|---|---|---|---|---|")
    for r in R:
        s = r["scan"]
        if not s: continue
        w(f"| {r['name']} | {s['max_P_h']:.2f} | {s['max_power']:.3f} | {s['p_max']:.3f} | {s['p_holm']:.3f} | {s['p_bh']:.3f} | {s['null95_max_circ']:.3f} | "
          + ", ".join(f"{t['P_h']:.1f}" for t in s["top"][1:5]) + " |")
    w("\n## Significant fixed-period peaks and their classification\n")
    hits = [(r, k, x) for r in R for k, x in r["targets"].items() if x["p_bh"] < 0.05]
    if not hits:
        w("None survive BH q<0.05 across series x periods: the answer at every probed fixed period is a null.\n")
    s2 = {(s["series"], s["stage"]): s for s in d["stage2"]}
    for r, k, x in hits:
        a = s2.get((r["name"], "A_rendered")); b = s2.get((r["name"], "B_rendered+load"))
        def st(s_):
            if not s_ or k not in s_["result"]["targets"]: return None
            t = s_["result"]["targets"][k]; return t
        ta, tb = st(a), st(b)
        if ta is None: verdict = "UNCLASSIFIED (residual test not run)"
        elif ta["p_bh_stage2"] >= .05: verdict = "EXPLAINED by rendered covariates (peak gone after regressing daylight/tide/moon/school/weekend)"
        elif tb is not None and tb["p_bh_stage2"] >= .05: verdict = "EXPLAINED only once model-tier load is added (not a rendered path; shared-machine artefact)"
        else: verdict = "UNEXPLAINED: a rendering/timetable path exists in the codebase but the peak survives regression on it"
        w(f"- **{r['name']} @ {k}**: power {x['power']:.3f}, p={x['p_max']:.4f}, Holm {x['p_holm']:.4f}. Path: {PATHS[k]}. "
          + (f"Residual after rendered covariates (R2={a['R2']:.2f}): power {ta['power']:.3f}, p={max(ta['p_circ'],ta['p_block']):.3f}, q={ta['p_bh_stage2']:.3f}. " if ta else "")
          + (f"Plus load (R2={b['R2']:.2f}): power {tb['power']:.3f}, p={max(tb['p_circ'],tb['p_block']):.3f}, q={tb['p_bh_stage2']:.3f}. " if tb else "")
          + f"Verdict: {verdict}.")
    w("")
    w(INTERP)
    open(mdf, "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__" and sys.argv[1] == "report":
    report(sys.argv[2], sys.argv[3])


# ----------------------------------------------------------------------------- run2: targets-only, high B, controls, residual stage
def task_t(args):
    name, t_h, y, pmin, B, seed, tag = args[:7]
    pmax = 960.0 if tag == "h" else 6.0
    tgt = {k: v for k, v in TARGETS_H.items() if pmin - 1e-9 <= v <= pmax}
    w = 2 * math.pi / np.array(list(tgt.values()))
    rng = np.random.default_rng(seed)
    obs = ls_power(t_h, y, w); N = len(y)
    blk = 24 if tag == "h" else 96; nb = int(math.ceil(N / blk))
    gc = np.zeros(len(w)); gb = np.zeros(len(w))
    for i in range(B):
        k = int(rng.integers(1, N)); gc += ls_power(t_h, np.roll(y, k), w) >= obs
        order = rng.permutation(nb)
        yb = np.concatenate([y[o * blk:(o + 1) * blk] for o in order])[:N]
        if len(yb) < N: yb = np.concatenate([yb, y[: N - len(yb)]])
        gb += ls_power(t_h, yb, w) >= obs
    out = {}
    for j, k in enumerate(tgt):
        out[k] = dict(P_h=tgt[k], power=float(obs[j]), p_circ=float((1 + gc[j]) / (B + 1)), p_block=float((1 + gb[j]) / (B + 1)))
        out[k]["p_max"] = max(out[k]["p_circ"], out[k]["p_block"])
    return dict(name=name, tag=tag, N=int(N), targets=out)


def run2(stage1_json, out_json, B):
    from concurrent.futures import ProcessPoolExecutor
    cache = os.environ["J2632_CACHE"]
    d = pickle.load(open(cache, "rb")); s1 = json.load(open(stage1_json))
    jobs = []; seed = 31001
    for r in s1["results"]:
        n, tag = r["name"].split("@"); ser = d["series"][tag]
        t, y, v = select_series(ser, n)
        jobs.append((r["name"], (t - t[0]) / H, y, 2.0 if tag == "h" else 0.5, B, seed + len(jobs), tag))
    # positive controls: the rendered covariates themselves, through the identical machinery (hourly)
    ser = d["series"]["h"]
    for cname in ("tide", "moon", "day", "school", "weekend"):
        v = ser["valid"] & ~np.isnan(ser["cov"][cname])
        t = ser["t"][v]; y = ser["cov"][cname][v]
        if np.nanstd(y) > 0: jobs.append(("CONTROL_" + cname + "@h", (t - t[0]) / H, y, 2.0, B, seed + len(jobs), "h"))
    with ProcessPoolExecutor(max_workers=12) as ex: res = list(ex.map(task_t, jobs))
    fam = [(r, k) for r in res if not r["name"].startswith("CONTROL") for k in r["targets"]]
    p = [r["targets"][k]["p_max"] for r, k in fam]
    for (r, k), a, b in zip(fam, holm(p), bh(p)):
        r["targets"][k]["p_holm"] = float(a); r["targets"][k]["p_bh"] = float(b)
    for r in res:
        if r["name"].startswith("CONTROL"):
            for k in r["targets"]: r["targets"][k]["p_holm"] = r["targets"][k]["p_bh"] = float("nan")
    scan = {r["name"]: r["scan"] for r in s1["results"]}
    for r in res: r["scan"] = scan.get(r["name"])
    # residual stage for hits (BH q<0.05) on the real series
    jobs2 = []; info2 = []
    for r in res:
        if r["name"].startswith("CONTROL"): continue
        hits = [k for k, x in r["targets"].items() if x["p_bh"] < 0.05]
        if not hits: continue
        n, tag = r["name"].split("@"); ser = d["series"][tag]; t, y, v = select_series(ser, n); cv = ser["cov"]
        for stage, cols in (("A_rendered", ["tide", "moon", "day", "night", "school", "weekend"]),
                            ("B_rendered+load", ["tide", "moon", "day", "night", "school", "weekend", "load"])):
            X = np.column_stack([cv[c][v] for c in cols]); ok = ~np.isnan(X).any(axis=1)
            if ok.sum() < 200: continue
            X = X[ok]; X = np.column_stack([X, X[:, 0] * X[:, 1]])
            tt = (t[ok] - t[ok][0]) / H; yy = y[ok]; rs, r2 = ols_resid(yy, X)
            jobs2.append((n + "|" + stage + "@" + tag, tt, rs, 2.0 if tag == "h" else 0.5, B, seed + 500 + len(jobs2), tag))
            info2.append(dict(series=r["name"], stage=stage, R2=float(r2), N=int(ok.sum()), hits=hits))
    stage2 = []
    if jobs2:
        with ProcessPoolExecutor(max_workers=12) as ex: subs = list(ex.map(task_t, jobs2))
        fam2 = [(i, k) for i, sub in zip(info2, subs) for k in sub["targets"]]
        p2 = [sub["targets"][k]["p_max"] for sub in subs for k in sub["targets"]]
        q2 = bh(p2); c = 0
        for i, sub in zip(info2, subs):
            for k in sub["targets"]: sub["targets"][k]["p_bh_stage2"] = float(q2[c]); c += 1
            i["result"] = sub; stage2.append(i)
    json.dump(dict(B=B, B_scan=s1["B"], meta=s1["meta"], results=res, stage2=stage2, accounting=s1["accounting"],
                   coverage=s1["coverage"], data_meta=s1["data_meta"]), open(out_json, "w"), indent=1)


if __name__ == "__main__" and sys.argv[1] == "run2":
    run2(sys.argv[2], sys.argv[3], int(sys.argv[4]))

"""J-1682: reusable, READ-ONLY split of night-sleep wall time by pipeline step, across two regimes.

WHY THIS EXISTS. D-0185's defeater (c) ("night-sleep mean duration above about 4,500 s") reads a single number
(data/night_log.jsonl `duration_s`); F-1589 (09-19) and F-2256 (10-02) both measured it, but F-1589's step-by-step
script was a throwaway and is gone, so "what share of the lengthening is which step" had to be re-derived from
nothing for J-1682 (and before it for D-0330). This is that read, kept: one command re-derives the split from the
live files, so the re-measure D-0330's options all ask for ("re-measure sleep length after fix (b) is settled")
needs no re-deriving.

HOW IT PARTITIONS A SLEEP (the sum of the steps below equals duration_s exactly, per sleep):
  * night_log.jsonl gives each sleep's start (`ts` = core/night.begin()), kind, `duration_s` (= the `wake` stage's
    t) and the stage clock (`downscale`, `epoch`, `dream`, `prune`, `wake`, each `t` = seconds since `ts`).
  * nascence.log gives the step LINES that nodes/inner_monologue_node.py `_enter_sleep` prints (one ordered
    `await` chain: chapters -> journal -> ... -> memory-levels -> ... -> sleep downscaling). A step's duration is the
    gap between the previous printed step line and ITS OWN line (F-1589's own method). Several lines are
    conditional (journal prints once a day, guidance-integration rarely, pursuits judge only when it judged), so an
    unprinted step's time FOLDS INTO the next printed step; the step names below say what each gap can contain.
  * everything after the last step line (downscale tail, dream_fade+epoch, the dream/_sleep_callback, prune, rest)
    comes from the night_log stage clock, not from log lines.
  * memory-levels is split further with the left-lane grade lines: shadow_distill grades ONCE per cluster before
    ef0fbfa (fix (b) shadow-observe) and TWICE after it (core/memory_levels.py: distil -> grade -> commit ->
    [fix (b): distil_b -> grade_b] -> row write). The time from the first grade line to the row write is therefore
    the fix (b) pair (plus a ~0.2 s commit), measured directly, not inferred from a pre/post per-cluster delta.

IT WRITES NOTHING to data/ (the three data files are opened read-only; the only write is --json-out, to a path you
choose). Safe while Du is live: pass snapshot copies via --log/--night/--shadow, or let it read the live files and
accept that a sleep in progress has no night_log row yet. Run from a worktree it falls back to C:/Nascence/data.

KNOWN LIMITS (J-1682's own): step durations are gaps between printed lines, so an unprinted conditional step folds
into the next printed one (the post-ML steps are therefore reported as two blocks bounded by always-printed lines);
before J-1180 (09-22 16:10) there is no `[chapters] seed scan over` line, so the chapters step is taken from replay
to the last `[chapters]` line (4 of 49 baseline sleeps have none and fold into journal+week+affections); the fix (b)
pair is `row write - first grade line` per cluster, which includes the ~0.18 s commit (median, measured on pre-fix rows).

AFTER J-1765 (D-0336 ended the fix (b) shadow; first live at the next Du restart that loads it): new shadow rows
carry no `fix_b_shadow` field, so load_shadow() classes them like pre-wire rows -- their fix (b) pair reads 0
(pair2/fixb empty; the first-grade -> row-write gap lands in `tail_pre` as plain commit overhead) and the
"grade lines != 2 x rows" diagnostic will list every such sleep (1 grade per cluster, not 2). Both are expected,
not errors: set the window boundaries at the restart as above and read the saving off the ML step and the sleep
means, not the fix (b) column.

USAGE (repo root):
    python scripts/sleep_step_split.py                      # J-1682's windows
    python scripts/sleep_step_split.py --log L --night N --shadow S --pre-start "2026-09-09 13:24:32" ...
Windows are by SLEEP START. Choose boundaries at real restart lines ("Nascence is awake"), not commit times: code is
read at process start.
"""
import argparse
import bisect
import collections
import json
import re
import statistics
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows charmap guard (this repo's own daemon lesson)
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" if (ROOT / "data" / "night_log.jsonl").exists() else Path(r"C:\Nascence\data")   # worktrees have no data/
LOGTS = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) ")
_EP = {}


def epoch_of(line: str):
    m = LOGTS.match(line)
    if not m:
        return None
    s = m.group(1)
    e = _EP.get(s)
    if e is None:
        e = time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))
        _EP[s] = e
    return e + int(m.group(2)) / 1000.0


def parse_local(s: str) -> float:
    return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def fmt(ts: float) -> str:
    return time.strftime("%m-%d %H:%M:%S", time.localtime(ts))


# (label, step name the gap ENDING at this line is charged to, regex)
MARKERS = [
    ("SLEEP",  "start+replay+chapter-load", r"\[monologue\] entering Sleep State"),
    ("REPLAY", "start+replay+chapter-load", r"\[monologue\] sleep replay:"),
    ("CH_SEED", "start+replay+chapter-load", r"\[chapters\] seed scan over (\d+) level-0"),
    ("JOURNAL", "journal+week+affections", r"\[monologue\] journal: wrote"),
    ("WEEK",   "journal+week+affections", r"\[monologue\] week roll-up:"),
    ("AFF",    "journal+week+affections", r"\[monologue\] affections \u2014 earned loves"),
    ("PEER",   "peers+mirror+stick+hold-rate", r"\[monologue\] a correspondent left a letter"),
    ("MIRROR", "peers+mirror+stick+hold-rate", r"\[monologue\] self-mirror"),
    ("STICK",  "peers+mirror+stick+hold-rate", r"\[monologue\] stick-test:"),
    ("HOLD",   "peers+mirror+stick+hold-rate", r"\[monologue\] hold-rate snapshot"),
    ("GI",     "guidance-integration+grounded-learning", r"\[monologue\] guidance-integration:"),
    ("GL",     "guidance-integration+grounded-learning", r"\[monologue\] grounded-learning: consolidated"),
    ("WC",     "world-consolidation sweep", r"\[monologue\] world-consolidation sweep:"),
    ("BR",     "book-residue sweep", r"\[monologue\] book-residue sweep:"),
    ("ML",     "memory-levels", r"\[monologue\] memory-levels: (\d+) clusters"),
    ("LINT",   "post-ML block A: lint+refinery+edges+bus+pursuits+GBJ+monoculture", r"\[monologue\] memory-lint:"),
    ("REF",    "post-ML block A: lint+refinery+edges+bus+pursuits+GBJ+monoculture", r"\[monologue\] refinery \("),
    ("EDGES",  "post-ML block A: lint+refinery+edges+bus+pursuits+GBJ+monoculture", r"\[monologue\] memory-edges harvest:"),
    ("BUS",    "post-ML block A: lint+refinery+edges+bus+pursuits+GBJ+monoculture", r"\[monologue\] bus calibration sync"),
    ("PUR",    "post-ML block A: lint+refinery+edges+bus+pursuits+GBJ+monoculture", r"\[monologue\] pursuits judge:"),
    ("GBJ",    "post-ML block A: lint+refinery+edges+bus+pursuits+GBJ+monoculture", r"\[monologue\] guidance behaviour judge:"),
    ("MONO",   "post-ML block A: lint+refinery+edges+bus+pursuits+GBJ+monoculture", r"\[monologue\] monoculture:"),
    ("CW",     "post-ML block B: curiosity worth+drift shadow+reading+meta", r"\[monologue\] curiosity worth:"),
    ("DRIFT",  "post-ML block B: curiosity worth+drift shadow+reading+meta", r"\[monologue\] drift shadow:"),
    ("READ",   "post-ML block B: curiosity worth+drift shadow+reading+meta", r"\[monologue\] reading reconciled"),
    ("META",   "post-ML block B: curiosity worth+drift shadow+reading+meta", r"\[monologue\] meta-awareness:"),
    ("DOWN",   "sleep downscaling line", r"\[monologue\] sleep downscaling:"),
    ("RC",     "read-count shadow", r"\[monologue\] sleep read-count shadow:"),
]
MARK_RE = [(lab, step, re.compile(rx)) for lab, step, rx in MARKERS]
STEP_ORDER = []
for _l, _s, _r in MARKERS:
    if _s not in STEP_ORDER:
        STEP_ORDER.append(_s)
CH_STEP = "chapters: seed scan (+author)"
STEP_ORDER.insert(1, CH_STEP)                      # right after start+replay+chapter-load
ML_FIXB, ML_REST = "memory-levels: fix (b) pair", "memory-levels: everything else"
i_ml = STEP_ORDER.index("memory-levels")
STEP_ORDER[i_ml:i_ml + 1] = [ML_REST, ML_FIXB]
TAIL_STEPS = ["downscale tail (stage clock)", "dream_fade+epoch", "dream (_sleep_callback)", "prune", "rest+wake"]
LATER_THAN_CHAPTERS = {"JOURNAL", "WEEK", "AFF", "PEER", "MIRROR", "STICK", "HOLD", "GI", "GL", "WC", "BR", "ML"}
GRADE_RE = re.compile(r"\[left-lane\] (?:graded gist faithfulness=|gist-faithfulness judge unavailable)")
CHAP_RE = re.compile(r"\[chapters\] (?!seed scan over)(?!seed scan checkpoint)")
TRANSPORT_RE = re.compile(r"\[nascence\.model_client\] transport error on (http://[\d.]+:\d+)")
BROAD_ERR_RE = re.compile(r"timeout|fail-open|unavailable|failover|error", re.I)   # F-2256's own definition
QUICK = re.compile(r"\[monologue\]|\[chapters\]|\[left-lane\]|transport error|timeout|fail-open|unavailable|failover|error|[Ee]rror")


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def load_sleeps(night_path, since):
    out = []
    for ln in Path(night_path).read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if not isinstance(r.get("duration_s"), (int, float)) or r["ts"] < since:
            continue
        out.append({"ts": r["ts"], "kind": r.get("kind"), "dur": float(r["duration_s"]), "stages": r.get("stages") or {},
                    "mk": {}, "chap": [], "grades": [], "transport": collections.Counter(), "broad": 0})
    out.sort(key=lambda s: s["ts"])
    return out


def scan_log(log_path, sleeps, since):
    starts = [s["ts"] - 3.0 for s in sleeps]
    procs = []                                   # (epoch, 'awake'|'down')
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line[:10] < time.strftime("%Y-%m-%d", time.localtime(since)):
                continue
            if "Nascence is awake" in line:
                e = epoch_of(line)
                procs.append((e, "awake"))
                continue
            if "Nascence shutting down" in line:
                procs.append((epoch_of(line), "down"))
                continue
            if not QUICK.search(line):
                continue
            e = epoch_of(line)
            if e is None:
                continue
            i = bisect.bisect_right(starts, e) - 1
            if i < 0:
                continue
            s = sleeps[i]
            if e > s["ts"] + s["dur"] + 3.0:
                continue
            m = TRANSPORT_RE.search(line)
            if m:
                s["transport"][m.group(1)] += 1
            if BROAD_ERR_RE.search(line):
                s["broad"] += 1
            if GRADE_RE.search(line):
                s["grades"].append(e)
            if CHAP_RE.search(line):
                s["chap"].append(e)
            for lab, _step, rx in MARK_RE:
                mm = rx.search(line)
                if mm:
                    if lab not in s["mk"]:
                        s["mk"][lab] = e
                        if lab == "CH_SEED":
                            s["n_cand"] = int(mm.group(1))
                        if lab == "ML":
                            s["ml_clusters"] = int(mm.group(1))
                    break
    return procs


def load_shadow(path):
    rows = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                r = json.loads(ln)
            except Exception:
                continue
            rows.append((r["ts"], "fix_b_shadow" in r, isinstance(r.get("fix_b_shadow"), dict)))
    rows.sort()
    return rows


def split_one(s, shadow):
    """Fill s['steps'] (dict step -> seconds, partitions s['dur']) and the memory-levels pair detail."""
    t0 = s["ts"]
    mk = s["mk"]
    steps = collections.defaultdict(float)
    # chapters step = [CH_SEED (or REPLAY/start before J-1180's line existed) -> last [chapters] line before the
    # first later-step marker]. No [chapters] line at all (no cluster found, no log) => the scan folds into the next step.
    later = [mk[k] for k in LATER_THAN_CHAPTERS if k in mk]
    lim = min(later) if later else float("inf")
    ch0 = mk.get("CH_SEED", mk.get("REPLAY", t0))
    ends = [t for t in s["chap"] if ch0 <= t < lim]
    s["has_ch_end"] = bool(ends)
    if ends:
        mk = dict(mk)
        mk["CH_END"] = max(ends)
        if "CH_SEED" not in mk:
            mk["CH_SEED"] = ch0                       # sync-scan era: the step starts after replay
    pts = sorted((t - t0, lab) for lab, t in mk.items() if lab != "SLEEP")
    step_of = {lab: step for lab, step, _ in MARKERS}
    step_of["CH_END"] = CH_STEP
    prev = 0.0
    for off, lab in pts:
        off = max(off, prev)
        steps[step_of[lab]] += off - prev
        prev = off
    st = s["stages"]
    dn, ep, dr, pr, wk = (st.get(k, {}).get("t") for k in ("downscale", "epoch", "dream", "prune", "wake"))
    s["align_resid"] = (dn - prev) if isinstance(dn, (int, float)) else None     # stage clock vs last log line
    last = prev
    seq = [("downscale tail (stage clock)", dn), ("dream_fade+epoch", ep), ("dream (_sleep_callback)", dr),
           ("prune", pr), ("rest+wake", wk)]
    tail_t = dn if isinstance(dn, (int, float)) else last
    for name, v in seq:
        if isinstance(v, (int, float)) and v >= last:
            steps[name] += v - last
            last = v
    steps["rest+wake"] += max(0.0, s["dur"] - last)                              # any residue to duration_s
    # --- memory-levels detail --------------------------------------------------------------------
    s["ml_total"] = steps.get("memory-levels", 0.0)
    s["pair1"], s["pair2"], s["rows"], s["rows_no_grade"] = [], [], 0, 0
    s["post_regime_rows"] = 0
    if "ML" in mk:
        a = mk.get("BR") or mk.get("WC")
        b = mk["ML"]
        if a is not None:
            i = bisect.bisect_right([r[0] for r in shadow], a)
            j = bisect.bisect_right([r[0] for r in shadow], b + 0.5)
            rws = shadow[i:j]
            grades = [g for g in s["grades"] if a < g <= b]
            prev_t, gi = a, 0
            for (rts, post_regime, has_fb) in rws:
                gl = []
                while gi < len(grades) and grades[gi] <= rts + 0.05:
                    if grades[gi] > prev_t:
                        gl.append(grades[gi])
                    gi += 1
                s["rows"] += 1
                if not gl:
                    s["rows_no_grade"] += 1
                    prev_t = rts
                    continue
                s["pair1"].append(gl[0] - prev_t)
                if post_regime:
                    s["post_regime_rows"] += 1
                    s["pair2"].append(rts - gl[0])         # first grade line -> row write = commit + fix (b) pair
                else:
                    s["tail_pre"] = s.get("tail_pre", []) + [rts - gl[0]]
                prev_t = rts
            s["ml_n_grade_lines"] = len(grades)
    fixb = sum(s["pair2"])
    if fixb and "memory-levels" in steps:
        steps[ML_FIXB] = fixb
        steps[ML_REST] = steps.pop("memory-levels") - fixb
    elif "memory-levels" in steps:
        steps[ML_REST] = steps.pop("memory-levels")
    s["steps"] = dict(steps)
    s["fixb"] = fixb


def table(title, groups, key_steps, shares):
    """groups: name -> sleeps (mean/median seconds per step, zeros included so step means sum to the total mean);
    shares: list of (pre_name, post_name) -> delta of mean seconds and its share of the total-duration delta."""
    names = list(groups)
    print(f"\n=== {title} ===")
    hdr = "%-44s" % "step (mean/median s per sleep)" + "".join("%12s" % n for n in names)
    for pre, post in shares:
        hdr += "  | %s->%s: d(s)  share" % (pre, post)
    print(hdr)
    tot = {n: mean([s["dur"] for s in groups[n]]) for n in names}
    tmed = {n: statistics.median([s["dur"] for s in groups[n]]) for n in names}

    def line(label, vals):
        row = "%-44s" % label[:44]
        for n in names:
            row += "%12s" % ("%.0f/%.0f" % vals[n])
        return row

    for st in key_steps:
        vals = {n: (mean([s["steps"].get(st, 0.0) for s in groups[n]]),
                    statistics.median([s["steps"].get(st, 0.0) for s in groups[n]])) for n in names}
        row = line(st, vals)
        for pre, post in shares:
            d = vals[post][0] - vals[pre][0]
            dt = tot[post] - tot[pre]
            row += "  | %+8.0f %6.1f%%" % (d, 100.0 * d / dt if dt else float("nan"))
        print(row)
    row = line("TOTAL duration_s", {n: (tot[n], tmed[n]) for n in names})
    for pre, post in shares:
        row += "  | %+8.0f %6.1f%%" % (tot[post] - tot[pre], 100.0)
    print(row)
    print("%-44s" % "n sleeps" + "".join("%12d" % len(groups[n]) for n in names))
    print("%-44s" % "sleeps with a [chapters] end line" + "".join("%12d" % sum(1 for s in groups[n] if s.get("has_ch_end")) for n in names))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--log", default=str(DATA / "nascence.log"))
    ap.add_argument("--night", default=str(DATA / "night_log.jsonl"))
    ap.add_argument("--shadow", default=str(DATA / "memory_levels_shadow.jsonl"))
    ap.add_argument("--pre-start", default="2026-09-09 13:24:32")
    ap.add_argument("--pre-end", default="2026-09-25 11:59:15")
    ap.add_argument("--pre-narrow-start", default="2026-09-22 16:10:23")       # J-1180's async chapter scan goes live
    ap.add_argument("--post-start", default="2026-09-25 19:21:51")
    ap.add_argument("--outlier-end", default="2026-09-26 07:30:00")            # the three post-restart outlier nights end before this
    ap.add_argument("--steady-start", default="2026-09-28 19:08:45")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    pre_s, pre_e = parse_local(a.pre_start), parse_local(a.pre_end)
    pn_s, post_s = parse_local(a.pre_narrow_start), parse_local(a.post_start)
    out_e, st_s = parse_local(a.outlier_end), parse_local(a.steady_start)
    base_s = parse_local("2026-09-02 00:00:00")
    sleeps_all = load_sleeps(a.night, base_s)
    sleeps = [s for s in sleeps_all]                                           # all kinds; logic below filters
    procs = scan_log(a.log, sleeps, base_s)
    shadow = load_shadow(a.shadow)
    for s in sleeps:
        split_one(s, shadow)
    night = [s for s in sleeps if s["kind"] == "night"]

    def win(lo, hi):
        return [s for s in night if lo <= s["ts"] <= hi]

    g_base = win(base_s, pre_s - 0.001)
    g_pre = win(pre_s, pre_e)
    g_pren = win(pn_s, pre_e)
    g_prea = win(pre_s, pn_s - 0.001)
    g_post = win(post_s, 9e12)
    g_out = [s for s in g_post if s["ts"] < out_e]
    g_ord = [s for s in g_post if s["ts"] >= out_e]
    g_std = [s for s in g_post if s["ts"] >= st_s]

    print("processes since 09-02 (awake/down):", ", ".join("%s %s" % (fmt(e), k) for e, k in procs if e >= pre_s - 86400 * 2))
    print("\nwindows (night sleeps by start):")
    for nm, g in (("BASE 09-02 -> pre-start", g_base), ("PRE-WIDE", g_pre), ("  PRE-A (sync chapter scan)", g_prea),
                  ("  PRE-B/narrow (async scan, no fix b)", g_pren), ("POST all", g_post), ("  POST outliers", g_out),
                  ("  POST ordinary", g_ord), ("  POST steady (since steady-start)", g_std)):
        d = [s["dur"] for s in g]
        print("  %-40s n=%-3d mean %7.1f median %7.1f p90 %7.1f max %8.1f" % (nm, len(g), mean(d), statistics.median(d) if d else float("nan"), pct(d, .9), max(d) if d else float("nan")))
    bad = [s for s in night if s["align_resid"] is None or s["align_resid"] < -5 or s["align_resid"] > 30]
    print("\nalignment: sleeps whose stage-clock `downscale.t` minus the last step-line offset is outside [-5,30] s:", len(bad),
          "of", len(night), "| max resid %.1f min %.1f" % (max(s["align_resid"] or 0 for s in night), min(s["align_resid"] or 0 for s in night)))
    print("sleeps missing an always-printed line (WC, ML, MONO, DOWN):",
          collections.Counter(l for s in night for l in ("WC", "ML", "MONO", "DOWN", "CH_SEED", "BR") if l not in s["mk"]))

    groups = collections.OrderedDict([("BASE", g_base), ("PRE-WIDE", g_pre), ("PRE-A", g_prea), ("PRE-B", g_pren),
                                      ("POST-ord", g_ord), ("POST-std", g_std)])
    table("per-step split of night-sleep wall time (sum of step means == total mean)", groups, STEP_ORDER + TAIL_STEPS,
          [("PRE-WIDE", "POST-ord"), ("PRE-B", "POST-ord"), ("BASE", "POST-ord")])

    print("\n=== per-sleep series, PRE-B + POST (start | n candidates | chapters scan s | s per Gpair | fix(b) s | ML total s | total s | transport errs) ===")
    for s in [x for x in night if x["ts"] >= pn_s]:
        n = s.get("n_cand") or 0
        ch = s["steps"].get(CH_STEP, 0.0)
        print("  %s %-5s n=%-6s ch %6.0f  %5.0f s/G | fixb %5.0f | ML %5.0f | dur %6.0f | tr %d" % (
            fmt(s["ts"]), (s["kind"] or "")[:5], n, ch, ch / (n * n / 1e9) if n else 0, s["fixb"],
            s["steps"].get(ML_REST, 0.0) + s["steps"].get(ML_FIXB, 0.0), s["dur"], sum(s["transport"].values())))

    # ---- chapters scale ------------------------------------------------------------------------
    print("\n=== chapters seed scan vs candidate count (seconds per 1e9 pairs; async scan only from 09-22 16:10) ===")
    for nm, g in (("PRE-A (sync)", g_prea), ("PRE-B", g_pren), ("POST-ord", g_ord), ("POST-std", g_std), ("POST-outliers", g_out)):
        xs = [(s["n_cand"], s["steps"].get(CH_STEP, 0.0)) for s in g if s.get("n_cand")]
        if xs:
            spg = [t / (n * n / 1e9) for n, t in xs if t > 0]
            print("  %-14s n=%-3d candidates mean %7.0f | scan s mean %7.0f median %7.0f | s per Gpair median %6.0f mean %6.0f" % (
                nm, len(xs), mean([n for n, _ in xs]), mean([t for _, t in xs]), statistics.median([t for _, t in xs]),
                statistics.median(spg) if spg else float("nan"), mean(spg) if spg else float("nan")))

    # ---- memory-levels detail ---------------------------------------------------------------------
    print("\n=== memory-levels detail (clusters per sleep, per-cluster seconds, fix (b) pair measured at the grade lines) ===")
    for nm, g in (("PRE-WIDE", g_pre), ("PRE-B", g_pren), ("POST-ord", g_ord), ("POST-std", g_std), ("POST-outliers", g_out)):
        cl = [s.get("ml_clusters", 0) for s in g]
        p1 = [x for s in g for x in s["pair1"]]
        p2 = [x for s in g for x in s["pair2"]]
        mlt = [s["ml_total"] for s in g]
        nrows = sum(s["rows"] for s in g)
        print("  %-14s n=%-3d clusters/sleep %.2f rows %d (no-grade-line rows %d) | ML step mean %6.0f med %6.0f | pair1/cluster mean %5.1f med %5.1f | "
              "pair2(fix b)/cluster mean %5.1f med %5.1f | fix b per sleep mean %6.0f" % (
                  nm, len(g), mean(cl), nrows, sum(s["rows_no_grade"] for s in g), mean(mlt), statistics.median(mlt) if mlt else float("nan"),
                  mean(p1), statistics.median(p1) if p1 else float("nan"), mean(p2) if p2 else 0.0,
                  statistics.median(p2) if p2 else float("nan"), mean([s["fixb"] for s in g])))
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(
            [{"ts": s["ts"], "start": fmt(s["ts"]), "dur": s["dur"], "kind": s["kind"], "n_cand": s.get("n_cand"),
              "clusters": s.get("ml_clusters"), "fixb": s["fixb"], "steps": s["steps"], "pair1": s["pair1"], "pair2": s["pair2"],
              "transport": dict(s["transport"]), "broad": s["broad"]} for s in night], indent=1), encoding="utf-8")
    odd = [s for s in g_post if s["rows"] and s.get("ml_n_grade_lines", 0) != 2 * s["post_regime_rows"]]
    print("  POST sleeps where grade lines in the ML window != 2 x rows:", len(odd), "of", len(g_post),
          [(fmt(s["ts"]), s["rows"], s.get("ml_n_grade_lines")) for s in odd][:6])
    tp = [x for s in g_pre for x in s.get("tail_pre", [])]
    print("  PRE rows: first-grade-line -> row-write (commit overhead, expect ~0.2 s): n=%d median %.2f p90 %.2f" % (
        len(tp), statistics.median(tp) if tp else float("nan"), pct(tp, .9)))

    # ---- defeater (c) with fix (b) subtracted -----------------------------------------------------
    print("\n=== D-0185 defeater (c) (mean night-sleep duration > ~4,500 s) with and without the fix (b) pair ===")
    for nm, g in (("PRE-WIDE", g_pre), ("PRE-B", g_pren), ("POST all", g_post), ("POST ordinary", g_ord), ("POST steady", g_std)):
        d = [s["dur"] for s in g]
        d2 = [s["dur"] - s["fixb"] for s in g]
        print("  %-14s n=%-3d mean %7.1f  minus fix(b) %7.1f | median %7.1f minus fix(b) %7.1f | mean fix(b) %6.1f s (%.1f%% of the sleep)" % (
            nm, len(g), mean(d), mean(d2), statistics.median(d), statistics.median(d2), mean([s["fixb"] for s in g]),
            100 * mean([s["fixb"] for s in g]) / mean(d)))

    # ---- the outlier nights --------------------------------------------------------------------
    print("\n=== POST outlier nights (start | duration | per-step seconds > 300 | transport errors by endpoint | broad F-2256-style error-line count) ===")
    for s in g_out:
        big = {k: round(v) for k, v in s["steps"].items() if v > 300}
        print("  %s dur %7.0f clusters %s n_cand %s fixb %5.0f | %s | transport %s (total %d) | broad %d" % (
            fmt(s["ts"]), s["dur"], s.get("ml_clusters"), s.get("n_cand"), s["fixb"], big, dict(s["transport"]), sum(s["transport"].values()), s["broad"]))
    print("\n=== transport-error lines inside sleep windows (all night sleeps): per window ===")
    for nm, g in (("PRE-WIDE", g_pre), ("PRE-B", g_pren), ("POST-ord", g_ord), ("POST-std", g_std)):
        t = [sum(s["transport"].values()) for s in g]
        print("  %-10s mean/sleep %.1f median %.1f  sleeps with >=20: %d of %d" % (nm, mean(t), statistics.median(t), sum(1 for x in t if x >= 20), len(g)))

if __name__ == "__main__":
    main()

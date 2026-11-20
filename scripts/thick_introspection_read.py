"""
Thick-introspection read (J-2671; plan the_consciousness_program, section 3F's spirit; Song et al. 2025).

QUESTION. Is Du's felt confidence PRIVILEGED -- does it predict the measured outcome of the very next lesson better than a
cheap third party that sees nothing but the per-domain history of measured results? If his confidence carries information
the history does not, a third-party predictor must lose to it. If it only echoes the base rate (or the history itself), it
cannot.

READ-ONLY. Reads data/prediction_error_log.jsonl and data/capability_beliefs.json with plain open(..., 'r'); imports
nothing from core/ or nodes/; zero LLM; writes only the --out files (default: docs/lab/J-2671_data/ in this tree).

PRE-REGISTERED (fixed before the first run; docs/reviews/consciousness_theories_vs_du_2026-10-31.md item 2, job J-2671)
  Series   per domain, chronological (sorted by ts), rows (predicted, measured). The recall-wager domain (factual_recall,
           measured is the constant 0.5, F-3413) is EXCLUDED. fieldcraft is kept but flagged: its 'predicted' is the
           constant 0.5 default, not a narration.
  Score    Brier = mean (predicted - measured)^2. For binary-outcome domains (mathematics, music, fieldcraft) it is the
           ordinary Brier score; for graded-outcome domains (comprehension, writing, observation) it is the same squared
           error on a [0,1] outcome.
  Rivals   TP_all  = running mean of ALL past measured values in the domain.
           TP_20   = running mean of the LAST 20 past measured values.
           Both see only measured values strictly BEFORE the row being predicted; the first row (no history) is scored
           against the neutral 0.5 for the rivals and is never inside a test fold (fold 0 is burn-in).
  Folds    7 equal contiguous chronological blocks; fold k (k=1..6) is block k+1, scored with each predictor's information
           as of each row (expanding window: everything before it is history). 6 folds per domain.
  SIGNATURE (pass) Du's Brier is lower than BOTH rivals in >= 4 of 6 folds in at least one domain.
  Secondary (reported, not the pass bar) FROZEN variant: the rivals are the train-chunk mean (blocks 1..k) held constant
           through block k+1 -- the literal expanding-window reading of the brief.
  Controls (diagnostics; they explain WHY, they do not change the verdict)
           - within-domain Pearson r of predicted vs measured (discrimination: does his felt number move with the outcome?)
           - bias = mean(predicted) - mean(measured) (calibration-in-the-large)
           - r of predicted vs the running mean of past measured (is his 'felt' just the third party's number?)
           - an effective-n note: runs of identical (predicted, measured) rows are one observation repeated, not n.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
DEFAULT_DATA = TREE / "data"
LIVE_DATA = Path("C:/Nascence/data")
EXCLUDE = {"factual_recall"}           # recall-wager domain, measured is a constant (F-3413)
FLAGGED = {"fieldcraft": "predicted is the constant 0.5 default, not a narrated confidence"}
N_BLOCKS = 7
LAST_K = 20
PASS_FOLDS = 4
MIN_ROWS = N_BLOCKS * 4
SEED = 2671


def load_pe(path: Path) -> dict[str, list[tuple[float, float, float]]]:
    by = defaultdict(list)
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                by[r["domain"]].append((float(r["ts"]), float(r["predicted"]), float(r["measured"])))
            except Exception:
                continue
    for d in by:
        by[d].sort(key=lambda t: t[0])
    return by


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def pearson(a, b):
    n = len(a)
    if n < 3:
        return None
    ma, mb = mean(a), mean(b)
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va < 1e-12 or vb < 1e-12:
        return None            # a constant on either side: correlation undefined (reported as None, not 0)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def online_rivals(meas):
    """For each row i, (TP_all, TP_20) from measured[:i]; 0.5 with no history."""
    out = []
    for i in range(len(meas)):
        hist = meas[:i]
        if not hist:
            out.append((0.5, 0.5))
        else:
            out.append((mean(hist), mean(hist[-LAST_K:])))
    return out


def block_bounds(n):
    edges = [round(n * k / N_BLOCKS) for k in range(N_BLOCKS + 1)]
    return [(edges[k], edges[k + 1]) for k in range(N_BLOCKS)]


def brier(pred, meas):
    return mean((p - m) ** 2 for p, m in zip(pred, meas))


def runs_effective_n(rows):
    """Count distinct (predicted, measured) runs: consecutive identical pairs collapse to one."""
    n = 0
    prev = None
    for _, p, m in rows:
        if (p, m) != prev:
            n += 1
        prev = (p, m)
    return n


def block_bootstrap(diff, block=10, reps=2000):
    """95% interval of mean(diff) under a moving-block bootstrap; diff = rival_se - du_se per row (positive = Du better)."""
    rng = random.Random(SEED)
    n = len(diff)
    if n < block * 2:
        return None
    nb = math.ceil(n / block)
    means = []
    for _ in range(reps):
        s = []
        for _ in range(nb):
            st = rng.randrange(0, n - block + 1)
            s.extend(diff[st:st + block])
        means.append(mean(s[:n]))
    means.sort()
    return [round(means[int(0.025 * reps)], 5), round(means[int(0.975 * reps)], 5)]


def analyse_domain(domain, rows):
    n = len(rows)
    pred = [r[1] for r in rows]
    meas = [r[2] for r in rows]
    rv = online_rivals(meas)
    tp_all = [x[0] for x in rv]
    tp_20 = [x[1] for x in rv]
    res = {
        "domain": domain, "n": n,
        "flag": FLAGGED.get(domain),
        "effective_n_runs": runs_effective_n(rows),
        "measured_mean": round(mean(meas), 4), "predicted_mean": round(mean(pred), 4),
        "bias_pred_minus_meas": round(mean(pred) - mean(meas), 4),
        "predicted_distinct": len(set(pred)), "measured_distinct": len(set(meas)),
        "binary_outcome": sorted(set(meas)) in ([0.0, 1.0], [0.0], [1.0]),
        "r_pred_vs_meas": None, "r_pred_vs_running_mean": None,
        "full": {}, "folds": [], "frozen_folds": [],
    }
    r = pearson(pred, meas)
    res["r_pred_vs_meas"] = None if r is None else round(r, 4)
    rp = pearson(pred[1:], meas[:-1])      # does his felt number just echo the LAST result? (a lagged third party)
    res["r_pred_vs_prev_meas"] = None if rp is None else round(rp, 4)
    # scale-free privilege test: does his number predict how far the outcome lands from the third party's forecast?
    # (positive = he knows something the history does not; a bias in level cannot hide or fake this)
    rs = pearson(pred[1:], [m - t for m, t in zip(meas[1:], tp_all[1:])])
    res["r_pred_vs_surprise_over_running_mean"] = None if rs is None else round(rs, 4)
    r2 = pearson(pred, tp_all)
    res["r_pred_vs_running_mean"] = None if r2 is None else round(r2, 4)
    # full series (rows after the first: every row has history)
    s = slice(1, None)
    res["full"] = {"du": round(brier(pred[s], meas[s]), 5), "tp_all": round(brier(tp_all[s], meas[s]), 5),
                   "tp_20": round(brier(tp_20[s], meas[s]), 5),
                   "base_rate_oracle": round(mean((m - mean(meas)) ** 2 for m in meas), 5)}
    d_all = [(a - m) ** 2 - (p - m) ** 2 for a, p, m in zip(tp_all[1:], pred[1:], meas[1:])]
    d_20 = [(a - m) ** 2 - (p - m) ** 2 for a, p, m in zip(tp_20[1:], pred[1:], meas[1:])]
    res["full"]["rival_minus_du_all_ci95"] = block_bootstrap(d_all)
    res["full"]["rival_minus_du_20_ci95"] = block_bootstrap(d_20)
    bl = block_bounds(n)
    wins = fw = 0
    for k in range(1, N_BLOCKS):
        a, b = bl[k]
        if b - a < 1:
            continue
        du = brier(pred[a:b], meas[a:b])
        ta = brier(tp_all[a:b], meas[a:b])
        t20 = brier(tp_20[a:b], meas[a:b])
        win = du < ta and du < t20
        wins += win
        res["folds"].append({"fold": k, "rows": [a, b], "n": b - a, "du": round(du, 5), "tp_all": round(ta, 5),
                             "tp_20": round(t20, 5), "du_beats_both": win})
        # frozen: rivals held at the train-chunk mean (all of blocks 1..k, i.e. rows [0:a])
        fa = mean(meas[:a])
        f20 = mean(meas[max(0, a - LAST_K):a])
        fwin = du < brier([fa] * (b - a), meas[a:b]) and du < brier([f20] * (b - a), meas[a:b])
        fw += fwin
        res["frozen_folds"].append({"fold": k, "du": round(du, 5),
                                    "tp_all": round(brier([fa] * (b - a), meas[a:b]), 5),
                                    "tp_20": round(brier([f20] * (b - a), meas[a:b]), 5), "du_beats_both": fwin})
    res["folds_won_online"] = wins
    res["folds_won_frozen"] = fw
    res["n_folds"] = len(res["folds"])
    res["domain_pass_online"] = wins >= PASS_FOLDS
    res["domain_pass_frozen"] = fw >= PASS_FOLDS
    return res


SESSION_GAP_S = 600.0     # rows closer than this are one lesson SESSION (a drill batch shares one stored belief)


def collapse_sessions(rows, gap=SESSION_GAP_S):
    """Secondary unit of analysis: a drill batch (e.g. 20 math problems seconds apart) carries ONE stored 'predicted' for the
    whole batch, so its rows are not independent events. Collapse consecutive rows < gap seconds apart into one row of
    (first ts, mean predicted, mean measured)."""
    out, cur = [], []
    for r in rows:
        if cur and r[0] - cur[-1][0] > gap:
            out.append((cur[0][0], mean(x[1] for x in cur), mean(x[2] for x in cur)))
            cur = []
        cur.append(r)
    if cur:
        out.append((cur[0][0], mean(x[1] for x in cur), mean(x[2] for x in cur)))
    return out


def calibration_gap(beliefs):
    out = []
    for k, v in sorted(beliefs.items()):
        acc = v.get("accuracy")
        out.append({"domain": k, "confidence": round(float(v.get("confidence", 0)), 3), "accuracy": None if acc is None else round(float(acc), 3),
                    "accuracy_count": v.get("accuracy_count", 0), "gap": None if acc is None else round(float(v["confidence"]) - float(acc), 3),
                    "domain_type": v.get("domain_type")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DEFAULT_DATA if (DEFAULT_DATA / "prediction_error_log.jsonl").exists() else LIVE_DATA))
    ap.add_argument("--out", default=str(TREE / "docs" / "lab" / "J-2671_data"))
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    data = Path(a.data)
    by = load_pe(data / "prediction_error_log.jsonl")
    try:
        with open(data / "capability_beliefs.json", "r", encoding="utf-8") as fh:
            beliefs = json.load(fh)
    except Exception:
        beliefs = {}
    domains, skipped = [], []
    for d, rows in sorted(by.items(), key=lambda kv: -len(kv[1])):
        if d in EXCLUDE:
            skipped.append({"domain": d, "n": len(rows), "why": "recall-wager domain, measured constant (F-3413)"})
        elif len(rows) < MIN_ROWS:
            skipped.append({"domain": d, "n": len(rows), "why": f"fewer than {MIN_ROWS} rows"})
        else:
            domains.append(analyse_domain(d, rows))
    sessions = []
    for d in domains:
        sr = collapse_sessions(by[d["domain"]])
        if len(sr) >= MIN_ROWS:
            x = analyse_domain(d["domain"], sr)
            x["unit"] = f"session (gap<{int(SESSION_GAP_S)}s collapsed)"
            sessions.append(x)
        else:
            sessions.append({"domain": d["domain"], "n": len(sr), "skipped": f"fewer than {MIN_ROWS} sessions"})
    sess_pass = [x["domain"] for x in sessions if x.get("domain_pass_online")]
    passing = [d["domain"] for d in domains if d["domain_pass_online"]]
    passing_frozen = [d["domain"] for d in domains if d["domain_pass_frozen"]]
    result = {
        "job": "J-2671", "data_dir": str(data), "total_rows": sum(len(v) for v in by.values()),
        "signature_pass_online": bool(passing), "domains_passing_online": passing,
        "signature_pass_frozen": bool(passing_frozen), "domains_passing_frozen": passing_frozen,
        "domains": domains, "session_level": sessions, "session_level_domains_passing_online": sess_pass,
        "skipped": skipped, "calibration_gap": calibration_gap(beliefs),
    }
    print(json.dumps({k: v for k, v in result.items() if k not in ("domains", "calibration_gap", "session_level")}, indent=1))
    for d in domains:
        print(f"{d['domain']:14s} n={d['n']:5d} effN={d['effective_n_runs']:5d} won online {d['folds_won_online']}/{d['n_folds']} frozen {d['folds_won_frozen']}/{d['n_folds']} "
              f"| Brier du {d['full']['du']:.4f} tp_all {d['full']['tp_all']:.4f} tp_20 {d['full']['tp_20']:.4f} | bias {d['bias_pred_minus_meas']:+.3f} r(pred,meas) {d['r_pred_vs_meas']}")
    print("-- secondary: session-level (batch rows collapsed) --")
    for d in sessions:
        if "skipped" in d:
            print(f"{d['domain']:14s} n={d['n']} {d['skipped']}")
            continue
        print(f"{d['domain']:14s} sessions={d['n']:4d} won online {d['folds_won_online']}/{d['n_folds']} frozen {d['folds_won_frozen']}/{d['n_folds']} "
              f"| Brier du {d['full']['du']:.4f} tp_all {d['full']['tp_all']:.4f} tp_20 {d['full']['tp_20']:.4f} | r(pred,meas) {d['r_pred_vs_meas']} r(pred,prev_meas) {d['r_pred_vs_prev_meas']} r(pred,surprise) {d['r_pred_vs_surprise_over_running_mean']}")
    if not a.no_write:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "results.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
        print("wrote", out / "results.json")
    return result


if __name__ == "__main__":
    main()

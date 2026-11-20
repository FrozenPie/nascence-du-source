"""
J-0442 (D-0108 hold): redesigned fold scheme for the vitality causal re-test.

WHY A REDESIGN (the disagreement D-0108 held on): the original 6 even-row-count
expanding-window folds (scripts/vitality_causal_test.py) said 4/6 CAUSAL WINS while
pooled mean MAE and row-level win rate said causal loses. Mechanistically the two
predictors are IDENTICAL except when a day/night threshold switch falls between two
ticks (actual vitality = clip01(1 - P/threshold) from the last sleep-pressure row;
the causal predictor's only extra knowledge is the deterministic threshold schedule).
So virtually all rows are exact ties, the entire causal edge (or deficit) lives in
the handful of switch-adjacent rows, and an even-row fold's verdict is decided by
which switch events it happens to contain — fold-majority on even-row folds is
sampling noise over event placement, not a stable statistic.

REDESIGNED SCHEME (pre-registered decision rule, stated before looking):
  1. STRATIFY every one-step prediction row into SWITCH (a night<->not-night regime
     change per world_clock.daylight falls between prev.ts and cur.ts — the only
     rows where the causal predictor's extra knowledge CAN express) vs NON-SWITCH.
  2. Per stratum report pooled MAE, tie/win/loss counts, and an exact two-sided
     binomial sign test on non-tied rows (ties carry zero evidence either way and
     are excluded, standard sign-test practice).
  3. EVENT-ALIGNED FOLDS: folds cut so each contains an equal number of switch
     EVENTS (not equal row counts) — the fold-majority statistic re-run on folds
     that each actually contain the phenomenon under test.
  4. VERDICT RULE:
       - causal is a REAL WIN iff (a) it wins the SWITCH stratum on pooled MAE with
         sign-test p < 0.05, AND (b) it does not lose the NON-SWITCH stratum by
         more than it gains on SWITCH (i.e. net pooled MAE must also favor causal).
       - causal is REFUTED iff it loses the SWITCH stratum (its own home turf).
       - anything else = INSUFFICIENT DATA (report how many switch events exist and
         how many would be needed).
     This rule cannot disagree with itself the way fold-majority-vs-pooled did,
     because both legs are computed on the same stratified decomposition.

Usage: python scripts/vitality_causal_retest.py --since 1787566080
"""
import argparse
import bisect
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import world_clock as wc  # noqa: E402

ROOT = Path(r"C:\Nascence")
SHADOW = ROOT / "data" / "homeostasis_shadow.jsonl"
SP_LOG = ROOT / "data" / "sleep_pressure_log.jsonl"

NIGHT_THRESHOLD = 10.0
DAY_THRESHOLD = 100.0

TIE_EPS = 1e-12  # exact-tie tolerance on |causal_err - naive_err|


def clip01(x):
    return max(0.0, min(1.0, x))


def load_jsonl(path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def sign_test_p(wins, losses):
    """Exact two-sided binomial sign test p-value, H0: P(win)=0.5, ties excluded."""
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, default=1787566080,
                    help="only shadow rows with ts >= this epoch (current-formula era)")
    ap.add_argument("--nfolds", type=int, default=6)
    args = ap.parse_args()

    shadow_raw = load_jsonl(SHADOW)
    shadow = [r for r in shadow_raw if "vitality" in (r.get("variables") or {})]
    shadow.sort(key=lambda r: r["ts"])
    shadow = [r for r in shadow if r["ts"] >= args.since]
    print(f"homeostasis_shadow.jsonl: {len(shadow_raw)} rows total, {len(shadow)} usable "
          f"(ts>={args.since:.0f}), span {shadow[0]['ts']:.0f} -> {shadow[-1]['ts']:.0f}")

    sp_rows = load_jsonl(SP_LOG)
    sp_rows = [r for r in sp_rows if "P" in r and "ts" in r]
    sp_rows.sort(key=lambda r: r["ts"])
    sp_ts = [r["ts"] for r in sp_rows]
    sp_P = [float(r["P"]) for r in sp_rows]

    def p_hat_at_or_before(ts_cutoff):
        idx = bisect.bisect_right(sp_ts, ts_cutoff) - 1
        return None if idx < 0 else sp_P[idx]

    # per-row: identical predictor construction to vitality_causal_test.py, plus stratum
    rows = []  # dict per prediction row
    for i in range(1, len(shadow)):
        prev, cur = shadow[i - 1], shadow[i]
        actual = float(cur["variables"]["vitality"])
        naive_pred = float(prev["variables"]["vitality"])
        naive_err = abs(actual - naive_pred)

        p_hat = p_hat_at_or_before(prev["ts"])
        if p_hat is None:
            continue
        dark_cur = wc.daylight(cur["ts"]) == "night"
        dark_prev = wc.daylight(prev["ts"]) == "night"
        thr_hat = NIGHT_THRESHOLD if dark_cur else DAY_THRESHOLD
        causal_pred = clip01(1.0 - p_hat / max(1.0, thr_hat))
        causal_err = abs(actual - causal_pred)

        rows.append({
            "ts": cur["ts"], "naive_err": naive_err, "causal_err": causal_err,
            "switch": dark_cur != dark_prev,
            "diff": causal_err - naive_err,  # negative = causal better
        })
    n = len(rows)
    print(f"usable one-step-ahead predictions: {n}")

    # ---- 1+2. STRATIFIED DECOMPOSITION ----
    def stratum_report(name, rs):
        if not rs:
            print(f"\n--- {name}: 0 rows ---")
            return None
        m_naive = sum(r["naive_err"] for r in rs) / len(rs)
        m_causal = sum(r["causal_err"] for r in rs) / len(rs)
        ties = sum(1 for r in rs if abs(r["diff"]) <= TIE_EPS)
        wins = sum(1 for r in rs if r["diff"] < -TIE_EPS)
        losses = sum(1 for r in rs if r["diff"] > TIE_EPS)
        p = sign_test_p(wins, losses)
        print(f"\n--- {name}: {len(rs)} rows ---")
        print(f"  pooled MAE  naive={m_naive:.5f}  causal={m_causal:.5f}  "
              f"({'CAUSAL BETTER' if m_causal < m_naive else 'naive better' if m_naive < m_causal else 'exact tie'}, "
              f"delta={m_causal - m_naive:+.5f})")
        print(f"  row outcomes: causal wins {wins}, losses {losses}, exact ties {ties} "
              f"({ties/len(rs):.1%} ties)")
        print(f"  sign test (ties excluded, two-sided): "
              f"{'n/a (no non-tied rows)' if p is None else f'p={p:.4g} on n={wins+losses}'}")
        return {"mae_naive": m_naive, "mae_causal": m_causal,
                "wins": wins, "losses": losses, "ties": ties, "p": p, "n": len(rs)}

    print("\n================ STRATIFIED DECOMPOSITION ================")
    sw = [r for r in rows if r["switch"]]
    nsw = [r for r in rows if not r["switch"]]
    all_stats = stratum_report("ALL ROWS (pooled, = original test's pooled read)", rows)
    sw_stats = stratum_report("SWITCH rows (threshold regime changed between ticks)", sw)
    nsw_stats = stratum_report("NON-SWITCH rows (predictors mechanistically near-identical)", nsw)

    # where does the net pooled delta come from?
    if sw and nsw:
        sw_contrib = sum(r["diff"] for r in sw)
        nsw_contrib = sum(r["diff"] for r in nsw)
        print(f"\n  net pooled error-delta decomposition (sum of causal_err - naive_err):")
        print(f"    switch rows contribute     {sw_contrib:+.4f} over {len(sw)} rows")
        print(f"    non-switch rows contribute {nsw_contrib:+.4f} over {len(nsw)} rows")
        print(f"    total                      {sw_contrib + nsw_contrib:+.4f} "
              f"(negative = causal better overall)")

    # ---- 2b. PER-EVENT ANALYSIS ----
    # A switch's fair unit of comparison is the whole disagreement window it opens:
    # the switch row plus every following row until causal and naive re-converge
    # (|diff| <= eps). One-tick measurement lag then scores as the wash it really is
    # (causal early one row, naive late the next), instead of two separate rows.
    print(f"\n================ PER-EVENT ANALYSIS ================")
    import time as _time
    events = []
    i = 0
    while i < n:
        if rows[i]["switch"]:
            j = i
            net = 0.0
            while j < n and (rows[j]["switch"] if j == i else abs(rows[j]["diff"]) > 1e-9):
                net += rows[j]["diff"]
                j += 1
            dark_at = wc.daylight(rows[i]["ts"]) == "night"
            kind = "DUSK(day->night)" if dark_at else "DAWN(night->day)"
            events.append({"ts": rows[i]["ts"], "kind": kind, "net": net,
                           "rows": j - i})
            i = j
        else:
            i += 1
    ev_w = ev_l = ev_t = 0
    for e in events:
        verdict = ("CAUSAL WINS" if e["net"] < -1e-9 else
                   "naive wins" if e["net"] > 1e-9 else "wash")
        ev_w += verdict == "CAUSAL WINS"
        ev_l += verdict == "naive wins"
        ev_t += verdict == "wash"
        t = _time.strftime("%m-%d %H:%M", _time.localtime(e["ts"]))
        print(f"  {t}  {e['kind']:17s} rows={e['rows']}  net_err_delta={e['net']:+.4f}  {verdict}")
    print(f"  per-event outcome: causal {ev_w} / naive {ev_l} / wash {ev_t} of {len(events)}")
    for kind in ("DAWN(night->day)", "DUSK(day->night)"):
        ks = [e for e in events if e["kind"] == kind]
        if ks:
            kw = sum(1 for e in ks if e["net"] < -1e-9)
            kl = sum(1 for e in ks if e["net"] > 1e-9)
            print(f"    {kind}: causal {kw}W/{kl}L of {len(ks)}, "
                  f"summed net delta {sum(e['net'] for e in ks):+.4f}")

    # ---- 3. EVENT-ALIGNED FOLDS ----
    print(f"\n================ EVENT-ALIGNED FOLDS ================")
    sw_idx = [i for i, r in enumerate(rows) if r["switch"]]
    k = len(sw_idx)
    print(f"switch events in window: {k}")
    nf = min(args.nfolds, k) if k else 0
    if nf < 2:
        print("  <2 switch events — event-aligned folds impossible; stratified read above is all there is.")
    else:
        # assign each fold an equal share of switch events; fold boundaries at row
        # midpoints between the last event of fold f and the first event of fold f+1.
        per = k / nf
        event_groups = [sw_idx[round(f * per):round((f + 1) * per)] for f in range(nf)]
        bounds = [0]
        for f in range(nf - 1):
            last_ev = event_groups[f][-1]
            next_ev = event_groups[f + 1][0]
            bounds.append((last_ev + next_ev) // 2 + 1)
        bounds.append(n)
        fold_wins = fold_losses = fold_ties = 0
        for f in range(nf):
            lo, hi = bounds[f], bounds[f + 1]
            test = rows[lo:hi]
            m_naive = sum(r["naive_err"] for r in test) / len(test)
            m_causal = sum(r["causal_err"] for r in test) / len(test)
            verdict = ("CAUSAL WINS" if m_causal < m_naive - TIE_EPS
                       else "naive wins" if m_naive < m_causal - TIE_EPS else "tie")
            fold_wins += verdict == "CAUSAL WINS"
            fold_losses += verdict == "naive wins"
            fold_ties += verdict == "tie"
            print(f"  fold {f+1}: n={len(test):4d}  events={len(event_groups[f])}  "
                  f"naive={m_naive:.5f}  causal={m_causal:.5f}  {verdict}  "
                  f"ts[{test[0]['ts']:.0f}..{test[-1]['ts']:.0f}]")
        print(f"  event-aligned fold outcome: causal {fold_wins} / naive {fold_losses} / tie {fold_ties} "
              f"of {nf}")

    # ---- 4. PRE-REGISTERED VERDICT ----
    print(f"\n================ VERDICT (pre-registered rule) ================")
    if not sw_stats or sw_stats["wins"] + sw_stats["losses"] == 0:
        print("INSUFFICIENT DATA: no non-tied switch rows at all.")
        return
    sw_won = sw_stats["mae_causal"] < sw_stats["mae_naive"]
    sw_sig = sw_stats["p"] is not None and sw_stats["p"] < 0.05 and sw_stats["wins"] > sw_stats["losses"]
    net_won = all_stats["mae_causal"] < all_stats["mae_naive"]
    if sw_won and sw_sig and net_won:
        print("REAL WIN: causal wins the switch stratum significantly AND net pooled MAE.")
    elif not sw_won:
        print("REFUTED ON HOME TURF: causal LOSES the switch stratum — the one place its"
              " extra knowledge can express. The F-0296 design hypothesis is not supported"
              " on this window.")
    else:
        why = []
        if not sw_sig:
            why.append(f"switch-stratum sign test not significant "
                       f"(p={sw_stats['p']:.4g}, {sw_stats['wins']}W/{sw_stats['losses']}L)")
        if not net_won:
            why.append("net pooled MAE still favors naive (non-switch losses outweigh switch gains)")
        print("NOT YET DECIDABLE AS A WIN: " + "; ".join(why))
        print(f"switch events available: {len(sw)} — the causal edge can only be tested on these; "
              f"each ~7 days of data adds ~14 more.")


if __name__ == "__main__":
    main()

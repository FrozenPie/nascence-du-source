"""
J-0451 (D-0108 hold, spawned from F-0613): the EXTENDED vitality causal predictor,
re-run through J-0442's exact redesigned fold scheme (scripts/vitality_causal_retest.py).

WHAT CHANGED vs. the as-built predictor (and nothing else — loading, strata, sign tests,
per-event disagreement windows, event-aligned folds, tie epsilon, and the pre-registered
verdict rule are copied verbatim from vitality_causal_retest.py so before/after is
apples-to-apples):

1. SLEEP-FIRE -> P-RESET FEEDBACK (the F-0613 dusk model gap). The as-built predictor
   forecasts P by persistence and applies the deterministic threshold schedule — but
   core/sleep_pressure.py's should_sleep() FIRES a pressure sleep the moment it evaluates
   with P >= NIGHT_THRESHOLD (10.0) during world-clock night (and awake >= MIN_WAKE_SECS),
   and sleep resets the accumulator: P is measured as intake SINCE last_wake_ts, so on
   wake P == 0 by construction (sleep_pressure() with zero new intake). The extended
   predictor models exactly that mechanism, no fudge factor: if the predicted regime at
   cur.ts is night AND the persisted p_hat >= NIGHT_THRESHOLD AND the projected awake
   time clears MIN_WAKE_SECS, the fire will have happened before cur.ts, so predict the
   post-reset state p_eff = 0 -> vitality = clip01(1 - 0/thr) = 1.0, instead of the
   crash clip01(1 - p_hat/10) ~= 0.0 the as-built model predicts. (This also covers the
   rows just after a dusk fire whose last logged sp row is the pre-reset fire row itself.)

2. STALE-ACTUAL HANDLING (the F-0613 dawn measurement artifact). Rule chosen: a
   prediction row is STALE iff NO sleep-pressure row exists in (prev.ts, cur.ts] — i.e.
   the shadow "actual" at cur derives from the SAME underlying sp measurement the naive
   predictor echoes from prev. Verified on this window before adoption: on all 137 such
   rows actual == naive_pred EXACTLY (0 exceptions in 799), so naive_err = 0 there by
   measurement circularity, not skill — the row measures nothing about real vitality.
   This is parameter-free (no arbitrary X-minute cutoff): staleness = "not refreshed
   within the prediction step itself". --stale exclude drops those rows from every leg
   (strata, sign tests, events, folds) and reports what was dropped; --stale keep
   reproduces the old behaviour.

3. (J-2012, F-2611) TWO ADDITIVE, FLAG-GATED SCORING-ARTIFACT FIXES. Defaults reproduce the old
   behaviour exactly (the 'REFUTED ON HOME TURF' read stays reproducible with the flags off):
   --regime-gap SECS   drop steps with cur.ts - prev.ts > SECS (a night boot after a daytime
                       shutdown is not a dusk; F-2611 layer 1). Default: off (0 = no segmentation).
   --fire-row MODE     keep (default) | exclude | relabel. A step is fire-pinned when the last sp
                       row at or before cur.ts has fire=True: the actual then reads the pre-reset P.
                       exclude = drop those steps; relabel = actual := 1.0 (the post-reset state).
   --shadow PATH / --sp-log PATH  read copies instead of the live logs (read-only either way).
   F-2611's corrected numbers: --since 1788517496 --model extended --stale exclude --regime-gap 1800
   with --fire-row exclude (switch 17/4) or relabel (switch 28/4).

Run all four configs for the before/after decomposition:
  python scripts/vitality_causal_retest2.py --since 1787566080 --model asbuilt  --stale keep     # must reproduce F-0612
  python scripts/vitality_causal_retest2.py --since 1787566080 --model asbuilt  --stale exclude  # artifact fix alone
  python scripts/vitality_causal_retest2.py --since 1787566080 --model extended --stale keep     # model fix alone
  python scripts/vitality_causal_retest2.py --since 1787566080 --model extended --stale exclude  # J-0451 headline
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
from core.sleep_pressure import NIGHT_THRESHOLD, DAY_THRESHOLD, MIN_WAKE_SECS  # noqa: E402

ROOT = Path(r"C:\Nascence")
SHADOW = ROOT / "data" / "homeostasis_shadow.jsonl"
SP_LOG = ROOT / "data" / "sleep_pressure_log.jsonl"

TIE_EPS = 1e-12  # exact-tie tolerance on |causal_err - naive_err| — same as retest v1


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
    ap.add_argument("--model", choices=["asbuilt", "extended"], default="extended",
                    help="asbuilt = J-0442 predictor verbatim; extended = + sleep-fire P-reset feedback")
    ap.add_argument("--stale", choices=["keep", "exclude"], default="exclude",
                    help="exclude = drop rows whose actual was not refreshed by any sp row within the step")
    ap.add_argument("--regime-gap", type=float, default=0.0,
                    help="drop steps with cur.ts - prev.ts > SECS (0 = off, old behaviour)")
    ap.add_argument("--fire-row", choices=["keep", "exclude", "relabel"], default="keep",
                    help="steps whose last sp row at cur is a fire row: keep (old) | exclude | relabel actual:=1.0")
    ap.add_argument("--shadow", default=str(SHADOW), help="homeostasis_shadow.jsonl (or a copy)")
    ap.add_argument("--sp-log", default=str(SP_LOG), help="sleep_pressure_log.jsonl (or a copy)")
    args = ap.parse_args()

    print(f"CONFIG: model={args.model}  stale={args.stale}  since={args.since:.0f}  "
          f"regime_gap={args.regime_gap or 'off'}  fire_row={args.fire_row}")

    shadow_raw = load_jsonl(Path(args.shadow))
    shadow = [r for r in shadow_raw if "vitality" in (r.get("variables") or {})]
    shadow.sort(key=lambda r: r["ts"])
    shadow = [r for r in shadow if r["ts"] >= args.since]
    print(f"homeostasis_shadow.jsonl: {len(shadow_raw)} rows total, {len(shadow)} usable "
          f"(ts>={args.since:.0f}), span {shadow[0]['ts']:.0f} -> {shadow[-1]['ts']:.0f}")

    sp_rows = load_jsonl(Path(args.sp_log))
    sp_rows = [r for r in sp_rows if "P" in r and "ts" in r]
    sp_rows.sort(key=lambda r: r["ts"])
    sp_ts = [r["ts"] for r in sp_rows]

    def sp_at_or_before(ts_cutoff):
        idx = bisect.bisect_right(sp_ts, ts_cutoff) - 1
        return None if idx < 0 else sp_rows[idx]

    # per-row: identical construction to retest v1, plus stale flag and the extended model
    rows = []
    import time as _time
    stale_total = 0
    stale_switch_dropped = []
    feedback_rows = 0
    gap_dropped = fire_dropped = fire_relabelled = 0
    for i in range(1, len(shadow)):
        prev, cur = shadow[i - 1], shadow[i]
        if args.regime_gap and cur["ts"] - prev["ts"] > args.regime_gap:
            gap_dropped += 1
            continue
        actual = float(cur["variables"]["vitality"])
        naive_pred = float(prev["variables"]["vitality"])
        naive_err = abs(actual - naive_pred)

        sp = sp_at_or_before(prev["ts"])
        if sp is None:
            continue
        p_hat = float(sp["P"])
        dark_cur = wc.daylight(cur["ts"]) == "night"
        dark_prev = wc.daylight(prev["ts"]) == "night"
        thr_hat = NIGHT_THRESHOLD if dark_cur else DAY_THRESHOLD

        p_eff = p_hat
        if args.model == "extended" and dark_cur and p_hat >= NIGHT_THRESHOLD:
            # should_sleep() fires on pressure only past the MIN_WAKE floor; project the
            # sp row's own awake clock forward to cur.ts (missing key -> treat as cleared:
            # P >= 10 of accrued intake implies a long-standing wake anyway).
            awake_secs = sp.get("awake_min")
            awake_at_cur = (float(awake_secs) * 60.0 + (cur["ts"] - sp["ts"])
                            if awake_secs is not None else float("inf"))
            if awake_at_cur >= MIN_WAKE_SECS:
                p_eff = 0.0  # sleep fired -> accumulator reset (intake since wake == 0)
                feedback_rows += 1
        causal_pred = clip01(1.0 - p_eff / max(1.0, thr_hat))
        causal_err = abs(actual - causal_pred)

        # stale iff no sp row landed inside (prev.ts, cur.ts] — actual not refreshed
        lo = bisect.bisect_right(sp_ts, prev["ts"])
        hi = bisect.bisect_right(sp_ts, cur["ts"])
        is_stale = hi <= lo
        is_switch = dark_cur != dark_prev

        if args.fire_row != "keep" and not is_stale:
            last_cur = sp_at_or_before(cur["ts"])
            if last_cur is not None and last_cur.get("fire"):
                if args.fire_row == "exclude":
                    fire_dropped += 1
                    continue
                fire_relabelled += 1
                actual = 1.0
                naive_err = abs(actual - naive_pred)
                causal_err = abs(actual - causal_pred)

        if is_stale:
            stale_total += 1
            if args.stale == "exclude":
                if is_switch:
                    stale_switch_dropped.append(cur["ts"])
                continue

        rows.append({
            "ts": cur["ts"], "naive_err": naive_err, "causal_err": causal_err,
            "switch": is_switch,
            "diff": causal_err - naive_err,  # negative = causal better
        })
    n = len(rows)
    print(f"usable one-step-ahead predictions: {n}")
    print(f"stale-actual rows in window: {stale_total} "
          f"({'EXCLUDED' if args.stale == 'exclude' else 'kept (v1 behaviour)'})")
    if stale_switch_dropped:
        for ts in stale_switch_dropped:
            print(f"  dropped a STALE SWITCH row at "
                  f"{_time.strftime('%m-%d %H:%M', _time.localtime(ts))} "
                  f"(actual frozen — the F-0613 dawn-artifact class)")
    if args.regime_gap:
        print(f"regime-gap: {gap_dropped} steps dropped (gap > {args.regime_gap:.0f}s)")
    if args.fire_row != "keep":
        print(f"fire-row {args.fire_row}: {fire_dropped} dropped, {fire_relabelled} relabelled (non-stale steps)")
    if args.model == "extended":
        print(f"sleep-fire feedback engaged on {feedback_rows} rows")

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
    all_stats = stratum_report("ALL ROWS (pooled)", rows)
    sw_stats = stratum_report("SWITCH rows (threshold regime changed between ticks)", sw)
    nsw_stats = stratum_report("NON-SWITCH rows (predictors mechanistically near-identical)", nsw)

    if sw and nsw:
        sw_contrib = sum(r["diff"] for r in sw)
        nsw_contrib = sum(r["diff"] for r in nsw)
        print(f"\n  net pooled error-delta decomposition (sum of causal_err - naive_err):")
        print(f"    switch rows contribute     {sw_contrib:+.4f} over {len(sw)} rows")
        print(f"    non-switch rows contribute {nsw_contrib:+.4f} over {len(nsw)} rows")
        print(f"    total                      {sw_contrib + nsw_contrib:+.4f} "
              f"(negative = causal better overall)")

    # ---- 2b. PER-EVENT ANALYSIS (verbatim v1 logic over the surviving rows) ----
    print(f"\n================ PER-EVENT ANALYSIS ================")
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

    # ---- 3. EVENT-ALIGNED FOLDS (verbatim v1 logic) ----
    print(f"\n================ EVENT-ALIGNED FOLDS ================")
    sw_idx = [i for i, r in enumerate(rows) if r["switch"]]
    k = len(sw_idx)
    print(f"switch events in window: {k}")
    nf = min(args.nfolds, k) if k else 0
    if nf < 2:
        print("  <2 switch events — event-aligned folds impossible; stratified read above is all there is.")
    else:
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

    # ---- 4. PRE-REGISTERED VERDICT (verbatim v1 rule) ----
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

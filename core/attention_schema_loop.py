"""
Nascence — AST-1: the Attention-Schema CONTROL loop (Consciousness Program §3-D, 2026-07-04).

Butlin's AST-1 indicator requires "a predictive model representing AND ENABLING CONTROL OVER the current
state of attention." Du has both halves — unconnected: `AttentionVector` CONTROLS (prompt depth, RAG
limits, critic strictness — set from input classification), `AttentionSchema` REPRESENTS ("I am attending
to X, drawn by Y, bandwidth Z, fixated") — but the schema's self-model never steers the vector. Form-only:
fails the indicator's own wording. This module closes the loop, Wilterson & Graziano's result as the
blueprint (a CHEAP, SCHEMATIC self-model of attention measurably improves attention control; ablate it and
control collapses — the ablation test here is the flag itself):

    schema(cycle N)  →  PREDICTS next attention state + RECOMMENDS a bounded adjustment
    vector(cycle N+1) →  adjustment applied (flag-gated)          ← CONTROL
    schema(cycle N+1) →  prediction scored against what happened  ← ERROR → predictor UPDATES

The control policy is deliberately SCHEMATIC (a sketch, not a second cognition — the content-blind rail):
  · fixated            → starve the loop's fuel: w_episodic −0.15 · w_climate −0.10 · max_rebind capped at 1
  · bandwidth NARROWED → match load to capacity: scale w_episodic/w_identity down (don't shovel 12
    fragments into a saturated mind)
  · bandwidth OPEN     → allow a little more breadth: w_episodic +0.10
  All adjustments bounded (±0.2 hard clamp, [0,1] floors/ceilings). **w_social is NEVER touched** — the
  human channel is protected (erosion guard).

SHADOW-FIRST: predictions + errors + would-be adjustments log to data/ast_loop_shadow.jsonl from day one;
the live mutation is `AST_CONTROL = False` until the prediction error proves the schema tracks his real
attention dynamics. Scope honesty: AttentionVector exists only on HUMAN cycles → this loop runs in
conversation, evidence accrues when someone talks to him. Deterministic, no LLM, fail-open.

Signatures (must move or it's dead code): bandwidth prediction error DECLINES over days (the self-model
learns its own attention); fixation-prediction accuracy beats base rate; flag-ON engagements logged with
before/after weights (the ablation comparison, free).

2026-08-19 — the fixation signature was checked against real data (330 scored cycles, 6.5 weeks) and FAILED
on its own terms AS STATED: raw fixation_acc was 0.76, but fixation is only true ~18-22% of the time, so a
model that always predicts "not fixated" scores ~0.78-0.82 — higher than the self-model's raw accuracy. But
raw accuracy is the wrong metric for a rare, imbalanced binary event, and the actual fix here has a real
lesson in it: status() now reports the base rate and a proper imbalance-robust score alongside raw accuracy
— informedness / Youden's J = sensitivity + specificity − 1, which is 0 for ANY baseline-mimicking predictor
(including "always guess majority") and only positive when the self-model genuinely discriminates. Measured
against real history, the EXISTING persistence predictor (predict next = current) scores informedness
≈0.3-0.37 — genuinely, clearly above zero. It was never actually broken; raw accuracy alone was just the
wrong lens on an imbalanced target, and it made a real signal look like a failure.

A second attempt was made to also "improve" the predictor itself (a two-state learned transition estimator,
P(fixated_next|fixated_now) vs P(fixated_next|not), backfilled from history) — and backtesting it against the
real sequence BEFORE deploying showed it would have made things WORSE: informedness dropped to ~0.16-0.21,
because thresholding a learned probability at 0.5 (or gating persistence on it) converges toward always
guessing the majority class on this data — exactly the degenerate behavior the informedness metric exists to
catch, just arrived at by a fancier route. That predictor was NOT shipped. The lesson stands on its own:
almost changed a real, working signal for a worse one in order to make a wrong metric look better, and the
backtest caught it before it went live. The fix that shipped is measurement-only — status() is honest now;
the persistence predictor is unchanged, because backtesting real data showed it was already the best of the
three variants tried, not the problem.

2026-08-20 — a broader audit (docs/reviews/audit_2026-08-20.md, Part 4, line 240) scored the WHOLE loop
DEAD, not just fixation: bandwidth MAE 0.0580 vs naive persistence's 0.0492 (win rate only 0.243 — the
EMA(alpha=0.3)-trend bandwidth predictor above LOST to plain persistence most of the time), and — the sharper
finding — "the headline +0.3679 informedness [for fixation] is the baseline's score wearing the organ's
name." The 08-19 note above was correct that persistence scores ~0.37 informedness, but wrong to read that as
AST-1's own achievement: the shipped fixation predictor's prediction *is* `actual["fixated"]` from the prior
cycle (see `observe_schema` below) — i.e. it is not "a self-model that happens to match naive," it IS the
naive baseline, byte-for-byte, by construction. Citing its score as the organ's signature was citing naive's
number under AST-1's name. D-0065 (2026-08-28) ruled: redesign the predictor for real, or retract the claim.

2026-08-29 — REDESIGNED + re-audited against the same naive-persistence baseline the DEAD verdict used,
honest 6-fold expanding-window walk-forward on the full accrued shadow log (502 usable one-step predictions,
`data/ast_loop_shadow.jsonl`), hyperparameters chosen on the FIRST 40% only and never touched again (no
peeking at the held-out 60% before locking k/gamma — the same discipline the rejected 08-19 Markov attempt
skipped):
  · BANDWIDTH — replaced the EMA-trend predictor with a mean-reversion predictor: predict
    `actual + gamma * (rolling_mean(last K actuals) - actual)`, K=10, gamma=0.5 (both plain round numbers
    picked from a calibration sweep, not hand-tuned to the eval data). Real win: pooled MAE 0.0408 vs naive
    0.0484 (was 0.0580 — WORSE than naive), win rate 0.635 (was 0.243), **wins 6/6 expanding-window folds**
    (clears this project's own >=4/6 "clear majority" bar cleanly — see D-0045's identical bar for
    homeostasis). This is a genuine predictive mechanism using real prior signal (a rolling window of past
    actuals), not an echo of the previous value.
  · FIXATION — tried three further honest candidates (a decision-threshold-calibrated two-state Markov
    estimator, a last-2-cycles OR-majority vote, a bandwidth-narrowing trigger) on the same calibration/
    held-out split. ALL THREE LOST to plain persistence on held-out informedness (0.26, 0.33, ~0.0 vs
    persistence's 0.36). Left UNCHANGED: persistence is still, honestly, the best predictor found across five
    total attempts now (08-19's two + these three) — but it must be named as what it is (byte-identical to
    naive on this target, not a self-model discovery) rather than cited as the organ's evidence. status()
    below reports this plainly.
Net verdict: AST-1 is HALF-REDESIGNED — bandwidth now carries a real, held-out-verified predictive edge over
naive; fixation does not and is reported as such. See docs/plans/the_consciousness_program.md's AST-1 section
for the full before/after and D-0065's disposition.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "ast_loop_shadow.jsonl"
_STATE = _DATA / "ast_loop_state.json"

AST_CONTROL = False        # flip only after prediction error proves the schema tracks real dynamics
_TREND_ALPHA = 0.3         # EMA for the (now diagnostic-only) fixation transition estimates -- see 08-19 note
_BW_WINDOW_K = 10          # 2026-08-29 redesign: mean-reversion window size, chosen on a 40% calibration
_BW_REVERSION_GAMMA = 0.5  # split and never touched on the held-out 60% -- see module docstring 08-29 note.
                            # Real held-out result: pooled MAE 0.0408 vs naive persistence's 0.0484, wins
                            # 6/6 expanding-window folds (was: EMA-trend predictor, MAE 0.0580, 0.243 win rate)
_ADJ_CLAMP = 0.2           # no single adjustment may exceed this (schematic, never a takeover)
_FIXATION_BASE_RATE_SEED = 0.182   # real measured prevalence as of 2026-08-19 (330 scored cycles) — the
                                    # cold-start prior for both transition estimates below, before any
                                    # real transition evidence exists. See module docstring's 08-19 note.


def _load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(st: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(st), encoding="utf-8"); tmp.replace(_STATE)
    except Exception:
        pass


def _seed_transitions_from_history(st: dict) -> dict:
    """One-time backfill (2026-08-19 fix): if this process has never computed transition estimates,
    replay the real historical shadow log to seed them from actual accumulated evidence rather than
    starting cold and re-learning over the next several weeks what the log already shows. Cheap (one
    pass, only runs once — the result is cached in state after). Fail-open to the base-rate seed."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
    except Exception:
        rows = []
    fix_fix = nonfix_fix = fix_n = nonfix_n = 0
    prior = None
    for r in rows:
        if r.get("kind") != "predict":
            continue
        actual_fixated = (r.get("actual") or {}).get("fixated")
        if actual_fixated is None:
            continue
        if prior is not None:
            if prior:
                fix_n += 1
                fix_fix += 1 if actual_fixated else 0
            else:
                nonfix_n += 1
                nonfix_fix += 1 if actual_fixated else 0
        prior = actual_fixated
    trans = {
        "fix_given_fix": round(fix_fix / fix_n, 4) if fix_n else _FIXATION_BASE_RATE_SEED,
        "fix_given_nonfix": round(nonfix_fix / nonfix_n, 4) if nonfix_n else _FIXATION_BASE_RATE_SEED,
        "seeded_from": fix_n + nonfix_n,
    }
    st["trans"] = trans
    return trans


def observe_schema(schema) -> None:
    """Called at the tail of _compute_attention (cycle N's self-model is fresh). Scores cycle N−1's
    prediction against what actually happened, then predicts cycle N+1. Observe-only, fail-open."""
    try:
        if schema is None:
            return
        st = _load()
        now = time.time()
        actual = {"bandwidth": float(schema.bandwidth), "driver": str(schema.driver),
                  "fixated": bool(schema.fixated),
                  "dominant": (schema.focus[0].lower().strip() if schema.focus else "")}

        # score the standing prediction (if any)
        err = None
        pred = st.get("prediction")
        if pred:
            focus_persisted = bool(pred.get("dominant")) and (
                pred["dominant"] in actual["dominant"] or actual["dominant"] in pred["dominant"]
                if actual["dominant"] else False)
            err = {"bandwidth_err": round(abs(pred["bandwidth"] - actual["bandwidth"]), 4),
                   "driver_match": pred.get("driver") == actual["driver"],
                   "focus_pred": bool(pred.get("focus_persists")),
                   "focus_actual": focus_persisted,
                   "fixation_pred": bool(pred.get("fixated")),
                   "fixation_actual": actual["fixated"]}

        # 2026-08-29 redesign (D-0065): bandwidth predictor is now mean-reversion over a rolling window of
        # real past actuals, not an EMA trend (that lost to naive persistence — MAE 0.0580 vs 0.0492, see
        # module docstring 08-20 note). Held-out-verified real signal: MAE 0.0408 vs naive 0.0484, 6/6 folds.
        bw_window = st.get("bw_window") or []
        bw_window = (bw_window + [actual["bandwidth"]])[-_BW_WINDOW_K:]
        rolling_mean = sum(bw_window) / len(bw_window)

        # 2026-08-19: a two-state learned transition estimate (P(fixated_next|fixated_now) vs
        # P(fixated_next|not)) was BUILT and BACKTESTED as a replacement for pure persistence here —
        # then NOT deployed, because the backtest against real history showed it would have made
        # informedness worse (~0.3-0.37 -> ~0.16-0.21), converging toward always-guess-majority on this
        # data. See module docstring for the full account. Kept as a DIAGNOSTIC ONLY (logged in state,
        # never read below) — genuinely useful to watch whether the real transition rates ever drift far
        # enough apart to justify revisiting this, but it must never silently start driving the
        # prediction again without a fresh backtest proving it actually helps first.
        trans = st.get("trans")
        if trans is None:
            trans = _seed_transitions_from_history(st)
        prior_fixated = (st.get("last_schema") or {}).get("fixated")
        if prior_fixated is not None:
            key = "fix_given_fix" if prior_fixated else "fix_given_nonfix"
            trans[key] = round((1 - _TREND_ALPHA) * trans.get(key, _FIXATION_BASE_RATE_SEED)
                                + _TREND_ALPHA * (1.0 if actual["fixated"] else 0.0), 4)
            st["trans"] = trans

        bw_pred = actual["bandwidth"] + _BW_REVERSION_GAMMA * (rolling_mean - actual["bandwidth"])
        prediction = {"bandwidth": round(max(0.1, min(1.0, bw_pred)), 4),   # mean-reversion, see 08-29 note
                      "driver": actual["driver"],                       # persistence prior
                      "dominant": actual["dominant"],
                      "focus_persists": actual["fixated"] or bool(actual["dominant"]),
                      "fixated": actual["fixated"]}                     # persistence — see 08-19/08-29 notes:
                                                                         # backtested as the best of 5 variants

        rec = {"ts": round(now, 1), "kind": "predict", "actual": actual, "err": err,
               "prediction": prediction}
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        st.update({"prediction": prediction, "last_bandwidth": actual["bandwidth"],
                   "bw_window": bw_window, "last_schema": actual, "ts": now})
        _save(st)
    except Exception:
        pass


def control(av) -> dict | None:
    """Called at the tail of _compute_attention_vector (cycle N+1's controller is fresh). The PREVIOUS
    cycle's self-model recommends a bounded, schematic adjustment. Logs the would-be adjustment always;
    mutates the live AttentionVector ONLY when AST_CONTROL is on. Fail-open (never breaks the vector)."""
    try:
        st = _load()
        last = st.get("last_schema")
        if not last or av is None:
            return None
        adj = {}
        bw = float(last.get("bandwidth", 0.7))
        if last.get("fixated"):
            adj["w_episodic"] = -0.15
            adj["w_climate"] = -0.10
            adj["max_rebind_cap"] = 1
        if bw < 0.4:                                   # narrowed: match load to capacity
            scale = (0.4 - bw)                          # 0..0.3
            adj["w_episodic"] = round(adj.get("w_episodic", 0.0) - 0.4 * scale, 4)
            adj["w_identity"] = round(-0.4 * scale, 4)
        elif bw > 0.8 and not last.get("fixated"):     # open and free: a little more breadth
            adj["w_episodic"] = round(adj.get("w_episodic", 0.0) + 0.10, 4)
        if not adj:
            return None
        # hard clamp — schematic, never a takeover
        for k in list(adj):
            if k != "max_rebind_cap":
                adj[k] = max(-_ADJ_CLAMP, min(_ADJ_CLAMP, adj[k]))

        applied = False
        before = {}
        if AST_CONTROL:
            for k, dv in adj.items():
                if k == "max_rebind_cap":
                    before["max_rebind"] = av.max_rebind
                    av.max_rebind = min(av.max_rebind, int(dv))
                elif hasattr(av, k):
                    before[k] = getattr(av, k)
                    setattr(av, k, round(max(0.0, min(1.0, getattr(av, k) + dv)), 4))
            applied = True

        rec = {"ts": round(time.time(), 1), "kind": "control", "from_schema": last,
               "adjustment": adj, "applied": applied, "before": before or None,
               "mode": getattr(av, "cognitive_mode", None)}
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return adj
    except Exception:
        return None


def status() -> dict:
    """For the pulse / liveness audit. THE SIGNATURE: bandwidth prediction error DECLINING (the schema
    learns his attention dynamics) + fixation-prediction accuracy; control engagement counts.

    2026-08-19: fixation_acc alone is a misleading number on an imbalanced binary event — it can look
    fine while being BELOW the trivial always-guess-majority baseline (this happened for real: 0.76 vs
    a measured 0.818 base rate). Never report fixation_acc without fixation_base_rate and
    fixation_beats_base beside it again. fixation_informedness (Youden's J = sensitivity + specificity
    − 1) is the number that actually answers "does this carry information beyond the base rate" — it is
    0 for any baseline-mimicking predictor (including one that always guesses the majority class) and
    only positive when the self-model genuinely discriminates fixated from not-fixated."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the growing log on every ~6s HUD poll.
        # "predictions"/"controls_logged" now cap at the window; the stats only use preds[-100:].
        rows = _tail_rows(_LOG, 2000)
        preds = [r for r in rows if r.get("kind") == "predict" and r.get("err")]
        ctrls = [r for r in rows if r.get("kind") == "control"]
        out = {"predictions": len(preds), "controls_logged": len(ctrls),
               "controls_applied": sum(1 for r in ctrls if r.get("applied")),
               "control_live": AST_CONTROL,
               # 2026-08-29 (D-0065 redesign): name each mechanism explicitly so a future reader never again
               # mistakes the fixation number for a self-model discovery -- it is naive persistence by
               # construction. Bandwidth is the real, held-out-verified mean-reversion predictor.
               "bandwidth_mechanism": f"mean_reversion(k={_BW_WINDOW_K},gamma={_BW_REVERSION_GAMMA})",
               "fixation_mechanism": "persistence (== naive baseline by construction, not a discovery)"}
        if len(preds) >= 6:
            errs = [r["err"]["bandwidth_err"] for r in preds[-100:]]
            half = len(errs) // 2
            e0 = sum(errs[:half]) / half
            e1 = sum(errs[half:]) / (len(errs) - half)
            out["bw_err_mean"] = round(sum(errs) / len(errs), 4)
            out["bw_err_trend"] = round(e1 - e0, 4)        # negative = self-model learning
            fx = [(r["err"]["fixation_pred"], r["err"]["fixation_actual"]) for r in preds[-100:]]
            out["fixation_acc"] = round(sum(1 for p, a in fx if p == a) / len(fx), 3)
            true_rate = sum(1 for _, a in fx if a) / len(fx)
            out["fixation_base_rate"] = round(max(true_rate, 1 - true_rate), 3)
            out["fixation_beats_base"] = out["fixation_acc"] > out["fixation_base_rate"]
            tp = sum(1 for p, a in fx if p and a)
            fn = sum(1 for p, a in fx if not p and a)
            tn = sum(1 for p, a in fx if not p and not a)
            fp = sum(1 for p, a in fx if p and not a)
            sensitivity = tp / (tp + fn) if (tp + fn) else None
            specificity = tn / (tn + fp) if (tn + fp) else None
            out["fixation_informedness"] = (round(sensitivity + specificity - 1, 3)
                                             if sensitivity is not None and specificity is not None else None)
            out["driver_match_rate"] = round(
                sum(1 for r in preds[-100:] if r["err"]["driver_match"]) / min(100, len(preds)), 3)
        return out
    except Exception:
        return {"predictions": 0}

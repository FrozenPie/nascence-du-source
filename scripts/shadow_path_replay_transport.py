"""
Nascence - Non-ergodic path replay of transport_habituation (J-2624, from F-3355 / J-2521, plan dosed_coupling).

QUESTION. The J-0603 shadow (data/transport_habituation_shadow.jsonl) is read as an ENSEMBLE statistic: per tick,
did the discounted "would_winner" differ from the real dispatch winner (differ_share, would_fired_share). But the
logged would_winner grows b on the REAL winner (core/transport_habituation.py docstring: "Growth is driven by the
REAL winner history (not a counterfactual would-have-won chain)"). If the discount were ADOPTED, b would grow on the
discounted policy's OWN winner, and dispatch is winner-take-all (argmax over ~124-147 candidates). F-3355's
curiosity null (large pool, recency window, 3-draw sampler) does not transfer to this shape. Does the adopted
discount produce a different winner PATH than (a) the real policy and (b) what the logged ensemble read predicts?

WHAT IS REPLAYED (read before the result).
  * Candidate pool and raw weights: HELD FIXED at the recorded values of each tick (row["weights"]: line_id -> kind,
    raw_weight). In the level-trigger era replayed here, a dispatch win changes NO line state except consuming a
    NOVELTY candidate (dispatch_tick: novelty_pending=False on the winner); spike/drought raw weights depend only on
    observe() occurrences and wall time, not on who won. The script CHECKS this from the log (winner raw_weight
    across consecutive winning ticks: does it reset after a win?). Novelty consumption IS path-dependent and is
    modelled exactly: a novelty a path wins is removed from that path's later pools; a novelty the REAL path
    consumed but a replayed path did not is restored at weight 1.0 (count reported).
  * Variant C = the real dispatch policy (argmax raw weight, first max wins, DISPATCH_THRESHOLD 1.5 for
    spike/drought, novelty exempt) replayed forward with this machinery. With a fixed pool and an argmax pick C has
    no feedback except novelty consumption, so C must reproduce the logged real_winner (fidelity check E4).
  * Variant D = the would-policy ADOPTED: discounted weight raw*max(DISCOUNT_FLOOR, 1-b) per the module, novelty
    exempt, same threshold rule, and b grown on D's OWN winner by calling core.transport_habituation.observe_and_log
    itself (the module's own decay+growth code path; its _load_state/_save_state/_log redirected to memory) with
    real_winner = D's winner. D starts from b = 0 for every line at its start tick (adoption at that tick).
  * LOGGED-WOULD = row["would_winner"] as logged (the ensemble read's own policy; b grown on the real winner).
  * DETERMINISM: both picks are argmax, no RNG. Instead of N RNG runs, every variant is replayed from 12 START
    TICKS (the first tick at or after week_start + k*2h, k = 0..11); the spread of D across starts is the noise.
    (POST-HOC, disclosed: on the primary week 8 of the 12 declared starts collapse onto tick 0 because the log's
    first row is ~14 h after local midnight; --anchor first reruns with k*2h counted from the first row. Sensitivity
    only; the verdict stays on the declared rule.)

DECLARED BEFORE ANY RESULT WAS LOOKED AT (do not tune; changing these after a run invalidates the verdict):
  WEEK_PRIMARY   2026-09-05 .. 2026-09-11 local days: level-trigger era, the clock_tick:study monoculture that F-0828 /
                 J-0603 read (real winner one line for hundreds of ticks). VERDICT on this week only.
  WEEK_REPLICATE 2026-09-16 .. 2026-09-23 (life:cat:study / wood_pigeon monoculture; reported, not in the verdict).
  NOT REPLAYED: 2026-09-24 onward. The candidate pool collapses (1-40 candidates/tick) and real dispatch fires on
    0-3% of ticks from 2026-09-29 (edge trigger, D-0294/J-1432), and under EDGE_TRIGGER a win DISARMS the winner, so
    the pool itself is path-dependent and cannot be held fixed. Stated, not replayed.
  VERDICT DAYS = days 2..7 of the primary week (every start covers them fully), d = 6, need = ceil(d/2) = 3.
  Per path per day: modal winner (None = no dispatch counts as its own label), modal_share, distinct winners,
    longest same-winner run (ticks), winner changes (w_t != w_t-1 within the day).
  RULE SET A (D vs C, the briefing's comparison):
    A1  D's modal winner (plurality over the 12 starts) != C's modal winner on >= need days
    A2  on >= need days, EVERY start's D winner-change count differs from C's by > max(5, 0.5 * C's count)
    A3  on >= need days, |median over starts of D modal_share - C modal_share| >= 0.20
    DIVERGE if any of A1..A3, else CONVERGE (= the pre-registered falsifier holds: paths converge).
  RULE SET B (D vs LOGGED-WOULD: does the ensemble read predict the adopted path?) = A1..A3 with LOGGED-WOULD in
    place of C. B DIVERGE = the ensemble read of the shadow hides a path effect.
  Agreement decay: share of ticks where C and D (and LOGGED-WOULD and D) pick the same winner, by horizon
    h = ticks since start, bins [0,10) [10,30) [30,100) [100,300) [300,1000) [1000,inf), pooled over starts.
  MACHINERY CHECKS (reported; a failure voids the verdict):
    E1  C's selection vs the REAL core.transport_manager.dispatch_tick() on a synthetic state built from each
        replayed tick's pool (evaluate/_load_ro/_load/_save/_log_shadow and the habituation hook stubbed), every
        replayed tick of start 0, for C's pool AND D's pool (raw weights) - identical winner required.
    E2  D's selection vs the would_winner computed by transport_habituation.observe_and_log itself on the same b
        state, every replayed tick of every start - identical required.
    E3  Logged-policy reconstruction: observe_and_log fed the REAL winners from the week's first row (state seeded
        from that row's logged b) must reproduce the logged would_winner and logged b (max abs deviation reported).
    E4  C reproduces the logged real_winner on every tick.

READ-ONLY on every live store. Zero LLM. --extract streams the live shadow log once and writes the weeks to
--scratch; replay reads only the scratch copies. Output json goes to --out (outside data/).
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import math
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # worktree root
# core BEFORE lab_env (feedback_jobrun_live_store_leaks)
import core  # noqa: E402
from core import transport_manager as tm  # noqa: E402
from core import transport_habituation as thab  # noqa: E402

LIVE_LOG = Path(r"C:\Nascence\data\transport_habituation_shadow.jsonl")
WEEKS = {"primary": ("2026-09-05", "2026-09-11"), "replicate": ("2026-09-16", "2026-09-23")}
N_STARTS, START_STEP_S = 12, 2 * 3600.0
THRESH = 1.5   # DISPATCH_THRESHOLD in force in the replayed era (asserted equal to tm.DISPATCH_THRESHOLD)
HBINS = [0, 10, 30, 100, 300, 1000, 10 ** 9]

_REAL_OBS = thab.observe_and_log
_IN_DISPATCH = [False]
_TM_POOL: dict = {}


def _day(ts):
    return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _bounds(a, b):
    lo = _dt.datetime.fromisoformat(a).timestamp()
    return lo, (_dt.datetime.fromisoformat(b) + _dt.timedelta(days=1)).timestamp()


def extract(scratch: Path):
    scratch.mkdir(parents=True, exist_ok=True)
    outs = {k: open(scratch / f"thab_{k}.jsonl", "w", encoding="utf-8") for k in WEEKS}
    bnds = {k: _bounds(*v) for k, v in WEEKS.items()}
    n = collections.Counter()
    with open(LIVE_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                ts = json.loads(line)["ts"]
            except Exception:
                n["bad"] += 1
                continue
            for k, (lo, hi) in bnds.items():
                if lo <= ts < hi:
                    outs[k].write(line)
                    n[k] += 1
    for o in outs.values():
        o.close()
    print("extracted", dict(n))


def load(scratch: Path, week: str):
    rows = []
    with open(scratch / f"thab_{week}.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rw = r["real_winner"] or {}
            rows.append({"ts": r["ts"], "real": rw.get("line_id"), "real_kind": rw.get("kind"),
                         "real_w": rw.get("weight"), "would": (r["would_winner"] or {}).get("line_id"),
                         "n_cand": r["n_candidates"],
                         "pool": [(lid, v["kind"], v["raw_weight"], v["b"]) for lid, v in r["weights"].items()]})
    rows.sort(key=lambda r: r["ts"])
    return rows


def select(pool, bstate=None, now=None):
    """Re-implementation of dispatch_tick's pick (bstate None) or observe_and_log's would pick (bstate given)."""
    best, bw = None, float("-inf")
    for lid, kind, raw, _ in pool:
        w = raw
        if bstate is not None and kind != "novelty":
            w = raw * max(thab.DISCOUNT_FLOOR, 1.0 - thab._decay(lid, now, bstate))
        if w > bw:
            bw, best = w, (lid, kind, raw)
    if best is not None and best[1] != "novelty" and bw < THRESH:
        best = None
    return best


def real_dispatch(pool):
    """The REAL transport_manager.dispatch_tick() on a synthetic state holding exactly this pool."""
    order = []
    _TM_POOL.clear()
    for lid, kind, raw, _ in pool:
        if lid not in _TM_POOL:
            order.append(lid)
            _TM_POOL[lid] = []
        _TM_POOL[lid].append(tm.Candidate(kind, raw, lid))
    tm._load_ro = lambda: {"lines": {lid: {} for lid in order}}
    _IN_DISPATCH[0] = True
    try:
        w = tm.dispatch_tick()
    finally:
        _IN_DISPATCH[0] = False
    return None if w is None else w.line_id


def _obs_hook(*x, **k):
    # dispatch_tick calls thab.observe_and_log at its end: a no-op there (E1 must not touch any b state)
    if _IN_DISPATCH[0]:
        return None
    return _REAL_OBS(*x, **k)


class ModuleB:
    """b state driven through transport_habituation.observe_and_log itself (its own decay + growth code)."""

    def __init__(self, seed=None):
        self.state = seed if seed is not None else {}
        self.last = None

    def step(self, pool, now, winner):
        cands = [tm.Candidate(k, raw, lid) for lid, k, raw, _ in pool]
        win_c = None if winner is None else tm.Candidate(winner[1], winner[2], winner[0])
        cap: dict = {}
        thab._load_state = lambda: self.state
        thab._save_state = lambda d: None
        thab._log = lambda rec: cap.update(rec)
        thab.observe_and_log(cands, win_c, THRESH, now=now)
        self.last = cap
        return (cap.get("would_winner") or {}).get("line_id")


def day_metrics(seq):
    by = collections.OrderedDict()
    for d, w in seq:
        by.setdefault(d, []).append(w)
    out = {}
    for d, ws in by.items():
        c = collections.Counter(ws)
        mw, mn = c.most_common(1)[0]
        run = best = 1
        ch = 0
        for a, b in zip(ws, ws[1:]):
            if a == b:
                run += 1
            else:
                ch += 1
                run = 1
            best = max(best, run)
        out[d] = {"n": len(ws), "modal": mw, "modal_share": round(mn / len(ws), 4), "distinct": len(c),
                  "longest_run": best, "changes": ch}
    return out


def replay(rows, start, e1=None):
    consumed = {"C": set(), "D": set()}
    real_consumed = []
    last_pos = {}
    bD = ModuleB()
    outC, outD = [], []
    n = collections.Counter()
    for i in range(start, len(rows)):
        r = rows[i]
        base = r["pool"]
        for j, p in enumerate(base):
            last_pos[p[0]] = j
        present = {p[0] for p in base}
        pools = {}
        for v in ("C", "D"):
            pool = [p for p in base if not (p[1] == "novelty" and p[0] in consumed[v])]
            for lid in real_consumed:
                if lid not in consumed[v] and lid not in present:
                    pool.insert(min(last_pos.get(lid, len(pool)), len(pool)), (lid, "novelty", 1.0, 0.0))
                    n[f"restored_{v}"] += 1
            pools[v] = pool
        wc = select(pools["C"])
        wd = select(pools["D"], bD.state, r["ts"])
        if e1 is not None:
            for v in ("C", "D"):
                w = wc if v == "C" else select(pools["D"])
                e1["n"] += 1
                e1["same"] += real_dispatch(pools[v]) == (None if w is None else w[0])
        mod_would = bD.step(pools["D"], r["ts"], wd)
        n["e2_n"] += 1
        n["e2_same"] += mod_would == (None if wd is None else wd[0])
        for v, w in (("C", wc), ("D", wd)):
            if w is not None and w[1] == "novelty":
                consumed[v].add(w[0])
        if r["real_kind"] == "novelty":
            real_consumed.append(r["real"])
        outC.append((_day(r["ts"]), None if wc is None else wc[0]))
        outD.append((_day(r["ts"]), None if wd is None else wd[0]))
        n["e4_n"] += 1
        n["e4_same"] += (None if wc is None else wc[0]) == r["real"]
        n["D_novelty_wins"] += wd is not None and wd[1] == "novelty"
        n["D_none"] += wd is None
    return outC, outD, n


def e3_logged(rows):
    seed = {lid: {"b": b, "last_update_ts": rows[0]["ts"]} for lid, _, _, b in rows[0]["pool"]}
    mb = ModuleB(seed)
    same = 0
    maxdev, ndev, nent = 0.0, 0, 0
    for r in rows:
        win = None if r["real"] is None else (r["real"], r["real_kind"], r["real_w"])
        would = mb.step(r["pool"], r["ts"], win)
        same += would == r["would"]
        for lid, _, _, b in r["pool"]:
            dev = abs(mb.last["weights"][lid]["b"] - b)
            nent += 1
            maxdev = max(maxdev, dev)
            ndev += dev > 1e-3
    return {"ticks": len(rows), "would_identical": same, "b_entries": nent, "b_dev_gt_1e-3": ndev,
            "b_max_abs_dev": round(maxdev, 5)}


def reset_check(rows):
    """Does the real winner's raw_weight reset (drop) on the tick after it wins?"""
    n = drop = 0
    for a, b in zip(rows, rows[1:]):
        if a["real"] and a["real_kind"] != "novelty":
            wa = {p[0]: p[2] for p in a["pool"]}.get(a["real"])
            wb = {p[0]: p[2] for p in b["pool"]}.get(a["real"])
            if wa is not None and wb is not None:
                n += 1
                drop += wb < wa - 1e-3
    return {"consecutive_pairs": n, "winner_raw_dropped": drop}


def rules(dmD, ref_dm, vdays):
    need = math.ceil(len(vdays) / 2)
    cnt = collections.Counter()
    per = {}
    for d in vdays:
        ref = ref_dm[d]
        mods = collections.Counter(dm[d]["modal"] for dm in dmD)
        dmod = mods.most_common(1)[0][0]

        def mmm(key):
            xs = [dm[d][key] for dm in dmD]
            return [min(xs), statistics.median(xs), max(xs)]
        chs = [dm[d]["changes"] for dm in dmD]
        tol = max(5, 0.5 * ref["changes"])
        r1 = dmod != ref["modal"]
        r2 = all(abs(c - ref["changes"]) > tol for c in chs)
        r3 = abs(statistics.median(dm[d]["modal_share"] for dm in dmD) - ref["modal_share"]) >= 0.20
        cnt["R1"] += r1
        cnt["R2"] += r2
        cnt["R3"] += r3
        per[d] = {"ref": ref, "D_modal_plurality": dmod, "D_modal_top3": mods.most_common(3),
                  "D_changes": mmm("changes"), "D_modal_share": mmm("modal_share"), "D_distinct": mmm("distinct"),
                  "D_longest_run": mmm("longest_run"), "R1": r1, "R2": r2, "R3": r3}
    fired = {k: cnt[k] >= need for k in ("R1", "R2", "R3")}
    return {"days": dict(cnt), "need": need, "fired": fired,
            "verdict": "DIVERGE" if any(fired.values()) else "CONVERGE", "per_day": per}


def run(scratch: Path, week: str, do_e1: bool, anchor: str = "midnight"):
    assert abs(tm.DISPATCH_THRESHOLD - THRESH) < 1e-9
    rows = load(scratch, week)
    lo, _ = _bounds(*WEEKS[week])
    if anchor == "first":   # POST-HOC sensitivity (added after the declared run: 8 of 12 declared starts
        lo = rows[0]["ts"]  # collapsed onto tick 0 because the primary week's first row is ~14 h after midnight)
    starts = [next(i for i, r in enumerate(rows) if r["ts"] >= lo + k * START_STEP_S) for k in range(N_STARTS)]
    days = sorted({_day(r["ts"]) for r in rows})
    vdays = days[1:]
    res = {"week": week, "anchor": anchor, "ticks": len(rows), "days": days, "verdict_days": vdays, "starts": starts,
           "collisions_n_cand_ne_pool": sum(1 for r in rows if r["n_cand"] != len(r["pool"])),
           "real_novelty_wins": sum(1 for r in rows if r["real_kind"] == "novelty"),
           "reset_check": reset_check(rows), "e3_logged_policy": e3_logged(rows)}
    e1 = collections.Counter() if do_e1 else None
    dmD = []
    agree = {"CD": collections.Counter(), "WD": collections.Counter(), "N": collections.Counter()}
    tot = collections.Counter()
    dmC0 = None
    logged_would = [(_day(r["ts"]), r["would"]) for r in rows]
    t0 = time.time()
    for si, s in enumerate(starts):
        oc, od, n = replay(rows, s, e1=e1 if si == 0 else None)
        tot.update(n)
        if si == 0:
            dmC0 = day_metrics(oc)
            res["D_start0_winner_counts"] = collections.Counter(w for _, w in od).most_common(15)
            res["D_start0_daily"] = day_metrics(od)
        dmD.append(day_metrics(od))
        for h, (c, d_, w) in enumerate(zip(oc, od, logged_would[s:])):
            b = next(k for k in range(len(HBINS) - 1) if HBINS[k] <= h < HBINS[k + 1])
            agree["N"][b] += 1
            agree["CD"][b] += c[1] == d_[1]
            agree["WD"][b] += w[1] == d_[1]
    res["replay_seconds"] = round(time.time() - t0, 1)
    res["checks"] = {"E1_dispatch_tick_same_of_n": [e1["same"], e1["n"]] if e1 is not None else "skipped",
                     "E2_module_would_same_of_n": [tot["e2_same"], tot["e2_n"]],
                     "E4_C_equals_logged_real_of_n": [tot["e4_same"], tot["e4_n"]],
                     "novelty_restored": {k: v for k, v in tot.items() if k.startswith("restored")},
                     "D_novelty_wins_all_starts": tot["D_novelty_wins"], "D_none_all_starts": tot["D_none"]}
    dmW = day_metrics(logged_would)
    res["daily"] = {"C_start0": dmC0, "LOGGED_REAL": day_metrics([(_day(r["ts"]), r["real"]) for r in rows]),
                    "LOGGED_WOULD": dmW}
    res["agreement_by_horizon"] = {f"[{HBINS[k]},{HBINS[k + 1]})": {
        "n": agree["N"][k],
        "C_vs_D": round(agree["CD"][k] / agree["N"][k], 4) if agree["N"][k] else None,
        "LOGGEDWOULD_vs_D": round(agree["WD"][k] / agree["N"][k], 4) if agree["N"][k] else None}
        for k in range(len(HBINS) - 1)}
    res["A_D_vs_C"] = rules(dmD, dmC0, vdays)
    res["B_D_vs_LOGGEDWOULD"] = rules(dmD, dmW, vdays)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--week", choices=list(WEEKS), default="primary")
    ap.add_argument("--no-e1", action="store_true")
    ap.add_argument("--anchor", choices=["midnight", "first"], default="midnight",
                    help="midnight = declared start rule; first = post-hoc sensitivity (starts from the first row)")
    ap.add_argument("--lab-root", required=True, help="lab_env lab root (outside C:/Nascence/data)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert "wt_dc" in str(Path(core.__file__)), f"core imported from {core.__file__}"
    assert "nascence\\data" not in a.lab_root.lower().replace("/", "\\")
    scratch = Path(a.scratch)
    if a.extract:
        extract(scratch)
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env
    lab_env._LAB_ROOT = Path(a.lab_root)
    lab_env._ISOLATE_OUTCOMES_LOG = lab_env._LAB_ROOT / "_isolate_outcomes.jsonl"
    with lab_env.isolate(also=[(thab, ["_STATE", "_LOG"]), (tm, ["_STATE", "_SHADOW_LOG"])], db="empty"):
        tm.evaluate = lambda lid: list(_TM_POOL.get(lid, []))
        tm._load = lambda: {"lines": {}}
        tm._save = lambda d: None
        tm._log_shadow = lambda c, n: None
        thab.observe_and_log = _obs_hook
        res = run(scratch, a.week, not a.no_e1, a.anchor)
    Path(a.out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    for k in ("week", "ticks", "starts", "collisions_n_cand_ne_pool", "real_novelty_wins", "reset_check",
              "e3_logged_policy", "checks", "replay_seconds", "agreement_by_horizon", "D_start0_winner_counts"):
        print(k, json.dumps(res[k], default=str))
    for k in ("A_D_vs_C", "B_D_vs_LOGGEDWOULD"):
        print(k, res[k]["verdict"], res[k]["days"], "need", res[k]["need"])


if __name__ == "__main__":
    main()

"""
Nascence - Non-ergodic path replay of the idle_allocator shadow (J-2625, from F-3355 / J-2521, plan dosed_coupling).

FIRST QUESTION (answered before any replay; docs/lab/idle_path_replay_2026-10-31/survey_J-2625.py over the FULL log):
  Does core/idle_allocator.py's shadow have a would-choose PATH channel, and is the logged read already on it?
  * The ONLY pick-dependent state is `streak` (lines 407-411): the ARGMAX winner's streak += 1, every other channel -> 0;
    s_final = p_norm * W * (1 - 0.15 * streak) (line 343). `history` (lines 402-406) appends EVERY candidate's raw every
    tick, independent of any pick, so p_norm is path-independent once the channel inputs are held fixed.
  * 'actual' (the real idle action) is never passed by the only caller (nodes/inner_monologue_node.py ~2694), so the
    log has NO recorded real action path: the briefing's control (real action path) does not exist in this log.
  * The logged would_pick_argmax is therefore ALREADY the closed-loop, self-fed path (survey K1: streak recurrence on
    the logged argmax holds on every candidate of every consecutive row pair). Replaying argmax forward can only
    reproduce the log (machinery check E1 below, not a finding).
  * BUT the policy RULED for Phase 1 (docs/staged/idle_executive_plan.md lines 197-198 and 252-254) is the SOFTMAX
    gateway (tau 0.35), "never a pure argmax". The logged would_pick_softmax is sampled on a streak grown on the
    ARGMAX pick. Adopted, the streak would grow on the SOFTMAX pick. That is the one would-choose path this shadow's
    ensemble read could hide, and it is what is replayed here.

WHAT IS REPLAYED (declared before any replay result was seen):
  * Channel inputs HELD FIXED at the recorded candidates of each row (channel set, raw, binding key, key kind);
    p_norm HELD FIXED at the logged value (core.idle_allocator._percentile patched to return it; the concern bypass
    switched off for the replay so concern's logged p_norm is also returned through that one hook; history seeded
    500 deep so nothing is cold). Selection, s_final, softmax sampling, coalitions and the streak accounting all run
    through core.idle_allocator.shadow_tick itself (its _CHANNELS replaced by the recorded tuples, _load_state /
    _save_state held in memory, _LOG -> os.devnull, inside lab_env.isolate with the lab root under the scratchpad).
  * AL  = the module as-is (streak fed on argmax), RNG seed 0. Must reproduce the logged argmax + winner_streak (E1).
  * SL  = the logged softmax policy reconstructed: the module as-is, softmax pick read, seeds 0..19.
  * SA  = softmax ADOPTED: identical, but after each tick the streak is re-accounted on the softmax pick (the 4-line
          accounting of lines 407-411 applied to would_pick_softmax instead of would_pick_argmax), seeds 0..19.
          SA and SL share seeds, so random.random() draws are paired tick for tick; the ONLY difference is the feedback.
  * LOGGED-SOFT = row["would_pick_softmax"] as logged (one realization of SL with unknown RNG state).
  * Every run starts at the week's first row with streak seeded from that row's logged winner_streak.
  WEEK_PRIMARY   2026-10-10 .. 2026-10-16 local (after the J-1921 balance fix boot 2026-10-09; full-volume days). VERDICT.
  WEEK_REPLICATE 2026-09-05 .. 2026-09-11 local (pre-fix era, different channel mix). Reported, not in the verdict.
  VERDICT DAYS = all 7 days, need = ceil(7/2) = 4.
  Per path per day: modal channel, modal_share, distinct channels, longest same-channel run, channel-change share.
  RULE SET A (SA vs SL - the clean path effect):
    A1 SA modal channel (plurality over seeds) != SL modal channel on >= need days
    A2 |median_seeds SA modal_share - median_seeds SL modal_share| >= 0.10 on >= need days
    A3 |median_seeds SA distinct - median_seeds SL distinct| >= 2 on >= need days
    A4 |median_seeds SA longest run - median_seeds SL longest run| >= 3 on >= need days
    DIVERGE if any of A1..A4, else CONVERGE (= the pre-registered falsifier: the paths converge).
  RULE SET B (SA vs LOGGED-SOFT: does the ensemble read predict the adopted path?) = A1..A4 with LOGGED-SOFT (single
    realization) in place of SL's medians.
  Reported, not in the verdict: pooled channel win shares per variant (incl. G2 self-share), per-day total-variation
    distance SA vs SL, SA max streak reached, change share (the G3 'rotates' number) for logged argmax / SL / SA.
READ-ONLY on every live store. Zero LLM.
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import math
import os
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # worktree root
import core  # noqa: E402  (core BEFORE lab_env)
from core import idle_allocator as ia  # noqa: E402

LIVE_LOG = Path(r"C:\Nascence\data\logs\idle_shadow.jsonl")
WEEKS = {"primary": ("2026-10-10", "2026-10-16"), "replicate": ("2026-09-05", "2026-09-11")}
N_SEEDS = 20
ORDER = list(ia._CHANNELS.keys())
_CUR: dict = {}


def _day(ts):
    return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def extract(scratch: Path):
    scratch.mkdir(parents=True, exist_ok=True)
    bnds = {k: (_dt.datetime.fromisoformat(a).timestamp(),
                (_dt.datetime.fromisoformat(b) + _dt.timedelta(days=1)).timestamp()) for k, (a, b) in WEEKS.items()}
    rows = {k: [] for k in WEEKS}
    with open(LIVE_LOG, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            for k, (lo, hi) in bnds.items():
                if lo <= r["ts"] < hi:
                    rows[k].append({"ts": r["ts"], "arg": r["would_pick_argmax"], "soft": r["would_pick_softmax"],
                                    "c": [[c["channel"], c["raw"], c["binding_key"], c["key_kind"], c["p_norm"],
                                           c["winner_streak"], c["s_final"]] for c in r["candidates"]]})
    for k, v in rows.items():
        (scratch / f"idle_{k}.json").write_text(json.dumps(v), encoding="utf-8")
        print("extract", k, len(v))


def _install():
    ia.CONCERN_BYPASS_PERCENTILE = False
    ia._percentile = lambda h, raw: _CUR["p"][_CUR["name"]]
    chans = {}
    for name in ORDER:
        def fn(ctx, _n=name):
            t = _CUR["c"].get(_n)
            if t is None:
                return None
            _CUR["name"] = _n
            return (t[1], t[2], t[3], "replay", {})
        chans[name] = fn
    ia._CHANNELS = chans
    mem = {}
    ia._load_state = lambda: mem["st"]
    ia._save_state = lambda st: mem.__setitem__("st", st)
    ia._LOG = Path(os.devnull)
    return mem


def run_path(rows, mem, seed, adopt_soft, e1=None):
    """adopt_soft None = argmax picks (AL); False = softmax picks, streak on argmax (SL); True = SA."""
    random.seed(seed)
    mem["st"] = {"balance_schema": 2, "curiosity_schema": 2,
                 "history": {n: [0.0] * ia.HIST_K for n in ORDER},
                 "streak": {n: 0 for n in ORDER}}
    for c in rows[0]["c"]:
        mem["st"]["streak"][c[0]] = c[5]
    picks, maxstreak = [], 0
    for r in rows:
        _CUR["c"] = {c[0]: c for c in r["c"]}
        _CUR["p"] = {c[0]: c[4] for c in r["c"]}
        pre = dict(mem["st"]["streak"])
        rec = ia.shadow_tick({})
        if e1 is not None:
            ok_arg = rec["would_pick_argmax"] == r["arg"]
            ok_st = (len(rec["candidates"]) == len(r["c"]) and
                     all(x["channel"] == c[0] and x["winner_streak"] == c[5] and abs(x["s_final"] - c[6]) < 1e-3
                         for x, c in zip(rec["candidates"], r["c"])))
            e1["ticks"] += 1
            e1["arg_ok"] += ok_arg
            e1["streak_sfinal_ok"] += ok_st
        p = rec["would_pick_softmax"] if adopt_soft is not None else rec["would_pick_argmax"]
        if adopt_soft:
            st = mem["st"]["streak"]
            for n in ORDER:
                st[n] = int(pre.get(n, 0) or 0) + 1 if n == p else 0
            maxstreak = max(maxstreak, st[p])
        picks.append(p)
    return picks, maxstreak


def day_metrics(days, picks):
    out = {}
    by = collections.defaultdict(list)
    for d, p in zip(days, picks):
        by[d].append(p)
    for d, seq in by.items():
        cnt = collections.Counter(seq)
        m, mc = cnt.most_common(1)[0]
        longest = run = 1
        for a, b in zip(seq, seq[1:]):
            run = run + 1 if a == b else 1
            longest = max(longest, run)
        ch = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
        out[d] = {"modal": m, "modal_share": round(mc / len(seq), 4), "distinct": len(cnt), "longest": longest,
                  "change_share": round(ch / max(1, len(seq) - 1), 4), "n": len(seq), "dist": dict(cnt)}
    return out


def agg(dms):
    res = {}
    for d in sorted(dms[0]):
        ms = collections.Counter(dm[d]["modal"] for dm in dms)
        n = dms[0][d]["n"]
        res[d] = {"modal": ms.most_common(1)[0][0], "modal_votes": dict(ms),
                  **{k: statistics.median(dm[d][k] for dm in dms)
                     for k in ("modal_share", "distinct", "longest", "change_share")},
                  "dist": {ch: statistics.mean(dm[d]["dist"].get(ch, 0) for dm in dms) / n for ch in ORDER}}
    return res


def rules(x, ref, days):
    need = math.ceil(len(days) / 2)
    hits = {"A1": [], "A2": [], "A3": [], "A4": []}
    for d in days:
        if x[d]["modal"] != ref[d]["modal"]:
            hits["A1"].append(d)
        if abs(x[d]["modal_share"] - ref[d]["modal_share"]) >= 0.10:
            hits["A2"].append(d)
        if abs(x[d]["distinct"] - ref[d]["distinct"]) >= 2:
            hits["A3"].append(d)
        if abs(x[d]["longest"] - ref[d]["longest"]) >= 3:
            hits["A4"].append(d)
    days_n = {k: len(v) for k, v in hits.items()}
    return {"verdict": "DIVERGE" if any(v >= need for v in days_n.values()) else "CONVERGE",
            "days": days_n, "need": need, "hit_days": hits}


def run(scratch: Path, week: str):
    rows = json.loads((scratch / f"idle_{week}.json").read_text(encoding="utf-8"))
    days = [_day(r["ts"]) for r in rows]
    mem = _install()
    t0 = time.time()
    e1 = collections.Counter()
    al, _ = run_path(rows, mem, 0, None, e1)
    sl, sa, sa_max = [], [], []
    for s in range(N_SEEDS):
        sl.append(run_path(rows, mem, s, False)[0])
        p, mx = run_path(rows, mem, s, True)
        sa.append(p)
        sa_max.append(mx)
    vdays = sorted(set(days))
    A_sl = agg([day_metrics(days, p) for p in sl])
    A_sa = agg([day_metrics(days, p) for p in sa])
    logged_soft = day_metrics(days, [r["soft"] for r in rows])
    logged_arg = day_metrics(days, [r["arg"] for r in rows])
    tvd = {d: round(0.5 * sum(abs(A_sa[d]["dist"][c] - A_sl[d]["dist"][c]) for c in ORDER), 4) for d in vdays}

    def pooled(seqs):
        return {c: round(sum(s.count(c) for s in seqs) / (len(seqs) * len(rows)), 4) for c in ORDER}

    paired_same = round(sum(a == b for x, y in zip(sa, sl) for a, b in zip(x, y)) / (N_SEEDS * len(rows)), 4)

    def strip(D):
        return {d: {k: v for k, v in D[d].items() if k != "dist"} for d in D}

    return {"week": week, "ticks": len(rows), "days": vdays, "seeds": N_SEEDS,
            "replay_seconds": round(time.time() - t0, 1),
            "E1_argmax_module_vs_log": dict(e1), "AL_equals_logged_argmax": al == [r["arg"] for r in rows],
            "A_SA_vs_SL": rules(A_sa, A_sl, vdays), "B_SA_vs_LOGGEDSOFT": rules(A_sa, logged_soft, vdays),
            "SL_vs_LOGGEDSOFT_sanity": rules(A_sl, logged_soft, vdays),
            "per_day": {"SA": strip(A_sa), "SL": strip(A_sl), "LOGGED_SOFT": strip(logged_soft),
                        "LOGGED_ARG": strip(logged_arg)},
            "tvd_SA_vs_SL": tvd, "paired_same_pick_SA_SL": paired_same,
            "pooled_share": {"SA": pooled(sa), "SL": pooled(sl), "LOGGED_SOFT": pooled([[r["soft"] for r in rows]]),
                             "LOGGED_ARG": pooled([[r["arg"] for r in rows]])},
            "SA_max_streak_per_seed": sa_max}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--week", choices=list(WEEKS), default="primary")
    ap.add_argument("--lab-root", required=True)
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
    with lab_env.isolate(also=[(ia, ["_STATE", "_LOG"])], db="empty"):
        res = run(scratch, a.week)
    Path(a.out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    for k in ("week", "ticks", "replay_seconds", "E1_argmax_module_vs_log", "AL_equals_logged_argmax",
              "paired_same_pick_SA_SL", "tvd_SA_vs_SL", "pooled_share", "SA_max_streak_per_seed"):
        print(k, json.dumps(res[k]))
    for k in ("A_SA_vs_SL", "B_SA_vs_LOGGEDSOFT", "SL_vs_LOGGEDSOFT_sanity"):
        print(k, res[k]["verdict"], res[k]["days"], "need", res[k]["need"])
    for v in ("SA", "SL", "LOGGED_SOFT", "LOGGED_ARG"):
        for d, m in res["per_day"][v].items():
            print(v, d, json.dumps(m))


if __name__ == "__main__":
    main()

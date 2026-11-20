"""
Nascence - Non-ergodic shadow replay (J-2521, thought T-0106, docs/reviews/frontier_disciplines_2026-10-30.md s10).

QUESTION. Every shadow read here is an ENSEMBLE statistic (how often would the shadow policy have picked
differently, per tick). Du lives ONE path: the seed picked at tick t changes the anti-relock set at t+1.
Does curiosity_habituation's squishy-spring discount, adopted and run FORWARD along a real week, produce a
different topic PATH than the live policy, even though its per-tick effect reads as small?

WHAT IS REPLAYED (and what is not - read this before the result).
  * Pool, counts, charges: HELD FIXED at the recorded values of each tick (data/curiosity_habituation_shadow.jsonl,
    one row per curiosity tick, every tension in the pool with its count and _last_touch_charge). The pool is the
    tension ledger (data/subconscious_state.json), NOT generated questions, so there is no LLM in this loop.
    What the replay CANNOT do is let a different seed change which tensions get re-activated next (count growth);
    that feedback needs the LLM and the whole cognitive stack. So this replays exactly ONE feedback channel: the
    label-keyed anti-relock memory (nodes/curiosity_node.py _recent_seeds, window 14, penalty 0.08). That is the
    only channel through which a pick at t changes the weights at t+1 inside the pool as recorded. A null here
    therefore bounds the anti-relock channel only, not the count-feedback channel (stated again in the finding).
  * Habituation b: advanced with core.curiosity_habituation._discount (same code path) from recorded count and
    charge and recorded timestamps, seeded from the last row before the window; validated against the logged b.
    b does not depend on the picks (the pool is fixed), so one b trajectory serves every replayed run.
  * Selection: the loop of CuriosityNode._select_seeds re-implemented line for line (sqrt(count) weight, x0.08 if the
    label is in recent_seeds, weighted pick without replacement, every entry sharing the chosen label removed,
    recent_seeds = (recent + chosen)[-14:]). Checked IDENTICAL to the real method on a synthetic state file
    (equivalence test below) with the same RNG seed, on every tick of the primary week.
  * Variant C (control)   = the real policy replayed forward (no discount).
    Variant D (discount)  = the same, each entry's weight additionally x max(DISCOUNT_FLOOR, 1 - b_id) (the shadow's
    would-choose weight, applied at entry level so the label-level removal of the real loop is kept). This is the
    "adopt the shadow" counterfactual.
  * LIVE path = real_choice of each logged row (ids -> labels, ordered unique), no replay.

DECLARED BEFORE ANY RESULT WAS LOOKED AT (do not tune; changing these after a run invalidates the verdict):
  WEEK_PRIMARY   2026-09-05 .. 2026-09-11 local days (LABEL-keyed era of the shadow log, 7 consecutive days, 320 rows,
                 one 8.9 h gap). VERDICT is read on this week only.
  WEEK_REPLICATE 2026-09-15 .. 2026-09-24 (9 days present, 09-20 has no rows; reported, not part of the verdict).
  WHY THE LABEL ERA: the id-keyed rows (2026-09-25 on) log tension ids, not labels, and an id's label CHURNS (F-1630):
    only 255 of 849 label strings that curiosity offered during 2026-10-09..10-15 still exist as any id's label in
    subconscious_state.json + tensions_archive.jsonl, and 5 of 283 ticks have all 3 offered labels still worn by tensions whose ids all lie in that tick's real_choice. The label
    each id wore at pick time is unrecoverable, and the real policy's anti-relock memory is keyed by label TEXT, so an
    id-era replay would be wrong by construction. Rows before 2026-09-25 key the pool by label, so the label at
    tick time is the key (their one limit: tensions sharing a label text collapse to one entry, F-1632, the same in C and D).
  N_RUNS = 300 per variant, RNG seeds 1000..1299 (identical seeds for C and D). K = 3 seeds per tick.
  TOPICS: core.topic_perseveration.cluster (greedy chronological, quoted-anchor rule, MiniLM cosine >= TOPIC_SIM 0.55),
          applied to the offered label with the leading 'unresolved: ' removed, per path, per day, with the previous
          day prepended exactly as topic_perseveration.day_row does. Metrics per day: n seeds, topics, modal_share,
          frozen (modal_share >= 0.80 and n >= 8).  Modal-topic IDENTITY across paths uses a joint frame (clustering
          the week's distinct labels once, ordered by first appearance in the pool).
  CONVERGE/DIVERGE (primary week, D vs C ensembles, d = number of days):
    R1  >= ceil(d/2) days with |mean_D - mean_C| of modal_share >= 0.05 AND >= 3 SE (SE from the two ensembles)
    R2  >= ceil(d/2) days with |mean_D - mean_C| of topics >= 10% of mean_C AND >= 3 SE
    R3  mean frozen days per run differs by >= 1.0 between D and C
    Verdict DIVERGE if any of R1..R3 holds, else CONVERGE (= falsified, the ensemble method is safe for this channel).
  REPLAY FIDELITY (reported, not in the verdict): fraction of primary days where the LIVE modal_share lies inside the
    2.5..97.5 percentile band of the C ensemble. Below 5 of 7 means the replay does not reproduce live and the
    live-vs-replay comparison is weak (D-vs-C is still valid: same machinery).
  Descriptive only: per-tick first-pick total-variation distance D vs C (the ENSEMBLE number), week TV of cumulative
    offer distributions, the logged `differs` share, and the count-feedback lift (P(count rises next tick | offered) vs
    not) which sizes how wrong "pool held fixed" is.

READ-ONLY on every live store (data/*.jsonl, subconscious_state.json, tensions_archive.jsonl). Zero LLM. The only model
loaded is the MiniLM embedder (a file read). Output goes to --out (scratchpad), never data/.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # repo (worktree) root
# core BEFORE lab_env (feedback_jobrun_live_store_leaks)
import core  # noqa: E402
from core import curiosity_habituation as chab  # noqa: E402
from core import topic_perseveration as tp  # noqa: E402

LIVE_DATA = Path(r"C:\Nascence\data")
SHADOW = LIVE_DATA / "curiosity_habituation_shadow.jsonl"
STATE = LIVE_DATA / "subconscious_state.json"
ARCHIVE = LIVE_DATA / "tensions_archive.jsonl"

K = 3
RECENT_MEMORY = 14
RECENT_PENALTY = 0.08
N_RUNS = 300
SEED0 = 1000
WEEKS = {
    "primary": ("2026-09-05", "2026-09-11"),
    "replicate": ("2026-09-15", "2026-09-24"),
}
FROZEN_SHARE, FROZEN_MIN_N = 0.80, 8
R1_ABS, R2_REL, R_SE, R3_FROZEN = 0.05, 0.10, 3.0, 1.0
PREFIX = "unresolved: "


def _day_bounds(a: str, b: str):
    lo = _dt.datetime.fromisoformat(a).timestamp()
    hi = (_dt.datetime.fromisoformat(b) + _dt.timedelta(days=1)).timestamp()
    return lo, hi


def _day(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


# ------------------------------------------------------------------ data
def load_rows(lo: float, hi: float):
    """(prior_row, rows) from the shadow log, id-keyed rows only, read-only streaming."""
    prior, rows = None, []
    with open(SHADOW, encoding="utf-8") as f:
        for line in f:
            try:
                ts = float(line[7:line.index(",", 7)])
            except Exception:
                continue
            if ts >= hi:
                continue
            if ts < lo - 14 * 86400:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("keyed_by") == "tension_id":     # label-era rows only (see header)
                continue
            if ts < lo:
                if prior is None or ts > prior["ts"]:
                    prior = r
            else:
                rows.append(r)
    rows.sort(key=lambda r: r["ts"])
    return prior, rows


class _Ident:
    """label-era rows are keyed by label text already: id -> label is the identity."""
    def get(self, k, d=""):
        return k

    def __getitem__(self, k):
        return k

    def __contains__(self, k):
        return True


def load_id_labels() -> dict:
    return _Ident()
    idl = {}
    sc = json.load(open(STATE, encoding="utf-8"))
    for t in sc.get("tensions", []):
        if t.get("id") and t.get("label"):
            idl[t["id"]] = t["label"].strip()
    with open(ARCHIVE, encoding="utf-8") as f:
        for l in f:
            try:
                r = json.loads(l)
            except Exception:
                continue
            t = r.get("tension") or r
            if t.get("id") and t.get("label") and t["id"] not in idl:
                idl[t["id"]] = t["label"].strip()
    return idl


# ------------------------------------------------------------------ selection (mirror of _select_seeds)
def select(entries, recent, k, choices):
    """entries [(label, weight)] already penalised/discounted; returns chosen labels. Mirrors the real loop."""
    pool = list(entries)
    chosen = []
    for _ in range(min(k, len(pool))):
        labels = [p[0] for p in pool]
        weights = [p[1] for p in pool]
        pick = choices(labels, weights=weights, k=1)[0]
        chosen.append(pick)
        pool = [p for p in pool if p[0] != pick]
    return chosen


def entries_for(row, idl, recent, bmap=None):
    rs = set(recent)
    out = []
    for tid, w in row["weights"].items():
        label = idl.get(tid, "")
        if not label:
            continue
        wt = math.sqrt(max(1, int(w["count"])))
        if label in rs:
            wt *= RECENT_PENALTY
        if bmap is not None:
            wt *= max(chab.DISCOUNT_FLOOR, 1.0 - bmap[tid])
        out.append((label, wt))
    return out


# ------------------------------------------------------------------ b trajectory via the module's own _discount
def b_trajectory(prior, rows):
    state = {}
    if prior:
        for tid, w in prior["weights"].items():
            state[tid] = {"b": w["b"], "last_count": w["count"], "last_update_ts": prior["ts"],
                          "sign_last": w.get("sign")}
    traj, maxdev, n_cmp = [], 0.0, 0
    for r in rows:
        bm = {}
        for tid, w in r["weights"].items():
            tens = {"count": w["count"], "_last_touch_charge": w["charge"], "last_ts": r["ts"]}
            b, _ = chab._discount(tid, tens, r["ts"], state)
            bm[tid] = b
            maxdev = max(maxdev, abs(round(b, 5) - w["b"]))
            n_cmp += 1
        traj.append(bm)
    return traj, maxdev, n_cmp


# ------------------------------------------------------------------ live path + recent reconstruction
def live_path(rows, idl):
    paths, bad = [], 0
    for r in rows:
        labs = []
        for tid in r["real_choice"]:
            lb = idl.get(tid, "")
            if lb and lb not in labs:
                labs.append(lb)
        if len(labs) != K:
            bad += 1
        paths.append(labs)
    return paths, bad


def recent_fidelity(rows, idl, paths):
    """Reconstruct live recent_seeds from real picks; compare with the logged penalty flags
    (raw_weight < 0.5*sqrt(count)). Returns (agree_share, restart_ticks, flagged_sets)."""
    recent, restarts, agree, tot = [], [], 0, 0
    flagged_all = []
    for i, r in enumerate(rows):
        flagged = set()
        for tid, w in r["weights"].items():
            lb = idl.get(tid, "")
            if lb and w["raw_weight"] < 0.5 * math.sqrt(max(1, w["count"])):
                flagged.add(lb)
        flagged_all.append(flagged)
        pred = set(recent)
        if i == 0:
            recent = sorted(flagged)[-RECENT_MEMORY:]
        elif pred and len(flagged) < 0.5 * len(pred):
            restarts.append(i)           # live recent_seeds was cleared: a process restart
            recent = []
        agree += (len(flagged & set(recent)) / max(1, len(flagged | set(recent)))) if i else 0   # mean Jaccard
        tot += 1 if i else 0
        recent = (recent + paths[i])[-RECENT_MEMORY:]
    return agree / max(1, tot), restarts, flagged_all


# ------------------------------------------------------------------ topics
class Topics:
    def __init__(self, labels):
        self.labels = sorted(set(labels))
        self.ix = {l: i for i, l in enumerate(self.labels)}
        texts = [l[len(PREFIX):] if l.startswith(PREFIX) else l for l in self.labels]
        self.V = [tp._default_embed(t) for t in texts]
        self.emb_ok = all(v is not None for v in self.V)
        n = len(self.labels)
        if self.emb_ok:
            M = np.stack(self.V)
            self.S = np.zeros((n, n), dtype=np.float64)
            for i in range(n):
                self.S[i] = [float(self.V[i] @ self.V[j]) for j in range(n)]
        else:
            self.S = None
        an = [tp.anchors_of(t) for t in texts]
        self.A = np.zeros((n, n), dtype=bool)
        for i in range(n):
            if an[i]:
                for j in range(n):
                    if an[j] and (an[i] & an[j]):
                        self.A[i, j] = True

    def cluster_idx(self, seq):
        """seq of label indices -> topic id per item. Same greedy rule as tp.cluster, from cached sims."""
        firsts, out = [], []
        fa = np.zeros(0, dtype=np.int64)
        for i in seq:
            pick = -1
            if firsts:
                m = np.nonzero(self.A[i, fa])[0]
                if m.size:
                    pick = int(m[0])
                else:
                    sims = self.S[i, fa]
                    b = int(np.argmax(sims))
                    if sims[b] >= tp.TOPIC_SIM:
                        pick = b
            if pick < 0:
                firsts.append(i)
                fa = np.array(firsts, dtype=np.int64)
                pick = len(firsts) - 1
            out.append(pick)
        return out

    def frame(self, order_labels):
        ids = [self.ix[l] for l in order_labels]
        lab = self.cluster_idx(ids)
        return {order_labels[k]: lab[k] for k in range(len(ids))}


def path_days(path, ts_list):
    """per-day seed lists in chronological order: {day: [label,...]}"""
    by = {}
    for labs, ts in zip(path, ts_list):
        by.setdefault(_day(ts), []).extend(labs)
    return by


def day_metrics(by_day, topics: Topics, frame):
    days = sorted(by_day)
    out = {}
    for d in days:
        pd = (_dt.date.fromisoformat(d) - _dt.timedelta(days=1)).isoformat()
        prev = by_day.get(pd, [])
        seq = [topics.ix[l] for l in prev + by_day[d]]
        lab = topics.cluster_idx(seq)[len(prev):]
        cnt = {}
        for x in lab:
            cnt[x] = cnt.get(x, 0) + 1
        mn = max(cnt.values())
        n = len(lab)
        fc = {}
        for l in by_day[d]:
            fc[frame[l]] = fc.get(frame[l], 0) + 1
        fmodal = max(sorted(fc), key=lambda k: fc[k])
        out[d] = {"n": n, "topics": len(cnt), "modal_share": mn / n,
                  "frozen": int(n >= FROZEN_MIN_N and mn / n >= FROZEN_SHARE), "frame_modal": fmodal,
                  "frame_modal_share": fc[fmodal] / n}
    return out


# ------------------------------------------------------------------ replay
def replay_run(rows, idl, traj, variant, seed, recent0, restarts):
    rng = random.Random(seed)
    recent = list(recent0)
    paths = []
    for i, r in enumerate(rows):
        if i in restarts:
            recent = []
        ent = entries_for(r, idl, recent, traj[i] if variant == "D" else None)
        chosen = select(ent, recent, K, rng.choices)
        recent = (recent + chosen)[-RECENT_MEMORY:]
        paths.append(chosen)
    return paths


def first_pick_tv(rows, idl, traj, recent_by_tick):
    """mean per-tick TV distance between first-pick label distributions with and without discount (the ENSEMBLE
    number: what one tick of the shadow reads). recent_by_tick = the live recent set at each tick."""
    tvs = []
    for i, r in enumerate(rows):
        c = entries_for(r, idl, recent_by_tick[i], None)
        d = entries_for(r, idl, recent_by_tick[i], traj[i])
        pc, pd_ = {}, {}
        for l, w in c:
            pc[l] = pc.get(l, 0) + w
        for l, w in d:
            pd_[l] = pd_.get(l, 0) + w
        sc, sd = sum(pc.values()), sum(pd_.values())
        tvs.append(0.5 * sum(abs(pc[l] / sc - pd_[l] / sd) for l in pc))
    return float(np.mean(tvs)), float(np.median(tvs)), float(np.max(tvs))


def count_feedback_lift(rows, idl, paths):
    """P(count of an id rises at the NEXT tick | its label was offered) vs not offered. Sizes the held-fixed pool."""
    on = [0, 0]
    off = [0, 0]
    for i in range(len(rows) - 1):
        off_set = set(paths[i])
        a, b = rows[i]["weights"], rows[i + 1]["weights"]
        for tid, w in a.items():
            if tid in b:
                rose = b[tid]["count"] > w["count"]
                tgt = on if idl.get(tid, "") in off_set else off
                tgt[0] += rose
                tgt[1] += 1
    return {"offered_rose": on[0], "offered_n": on[1], "not_offered_rose": off[0], "not_offered_n": off[1],
            "p_offered": on[0] / max(1, on[1]), "p_not": off[0] / max(1, off[1])}


# ------------------------------------------------------------------ equivalence test vs the real node
def equivalence_test(rows, idl, paths, n_ticks=None):
    """Run the REAL CuriosityNode._select_seeds on a synthetic state file built from each recorded tick and compare
    with select()/entries_for() under the same RNG seed. Real node's own shadow hook is stubbed to a no-op."""
    import tempfile
    import nodes.curiosity_node as cn
    chab_orig = chab.observe_and_log
    chab.observe_and_log = lambda *a, **k: None
    node = cn.CuriosityNode.__new__(cn.CuriosityNode)   # no NodeBase.__init__: only _recent_seeds is used
    node._recent_seeds = []
    tmpd = Path(tempfile.mkdtemp(prefix="J-2521_eq_"))
    cn_path_orig = cn._SUBCONSCIOUS_STATE_PATH
    same = tot = 0
    first_bad = None
    try:
        recent = []
        for i, r in enumerate(rows[: n_ticks or len(rows)]):
            tens = []
            for tid, w in r["weights"].items():
                lb = idl.get(tid, "")
                if lb:
                    tens.append({"id": tid, "label": lb, "count": w["count"]})
            p = tmpd / f"state_{i}.json"
            p.write_text(json.dumps({"tensions": tens}), encoding="utf-8")
            cn._SUBCONSCIOUS_STATE_PATH = p
            node._recent_seeds = list(recent)
            random.seed(7000 + i)
            real = node._select_seeds()
            rng = random.Random(7000 + i)
            mine = select(entries_for(r, idl, recent, None), recent, K, rng.choices)
            tot += 1
            if real == mine:
                same += 1
            elif first_bad is None:
                first_bad = (i, real, mine)
            recent = (recent + paths[i])[-RECENT_MEMORY:]   # follow the live path so recent_seeds stays realistic
    finally:
        cn._SUBCONSCIOUS_STATE_PATH = cn_path_orig
        chab.observe_and_log = chab_orig
    return {"ticks": tot, "identical": same, "first_mismatch": first_bad}


# ------------------------------------------------------------------ main
def pct(a, q):
    return float(np.percentile(a, q))


def run_week(name, idl, runs, do_equiv, diag_only):
    a, b = WEEKS[name]
    lo, hi = _day_bounds(a, b)
    prior, rows = load_rows(lo, hi)
    out = {"week": name, "days": [a, b], "ticks": len(rows),
           "first_ts": rows[0]["ts"], "last_ts": rows[-1]["ts"],
           "first_cycle_row_ts": _dt.datetime.fromtimestamp(rows[0]["ts"]).isoformat(),
           "last_row_ts": _dt.datetime.fromtimestamp(rows[-1]["ts"]).isoformat(),
           "differs_share_logged": sum(1 for r in rows if r.get("differs")) / len(rows),
           }
    ts_list = [r["ts"] for r in rows]
    paths, bad = live_path(rows, idl)
    out["live_ticks_not_K_labels"] = bad
    traj, maxdev, ncmp = b_trajectory(prior, rows)
    out["b_replay_max_abs_dev_vs_logged"] = maxdev
    out["b_compare_n"] = ncmp
    agree, restarts, flagged = recent_fidelity(rows, idl, paths)
    out["recent_agree_share"] = agree
    out["restart_ticks"] = restarts
    out["recent_seed_first_tick"] = sorted(flagged[0])
    if diag_only:
        return out
    recent0 = sorted(flagged[0])[-RECENT_MEMORY:]
    # live recent set per tick (for the ensemble first-pick TV)
    rb, rec = [], list(recent0)
    for i in range(len(rows)):
        if i in restarts:
            rec = []
        rb.append(list(rec))
        rec = (rec + paths[i])[-RECENT_MEMORY:]
    out["first_pick_tv_D_vs_C_mean_median_max"] = first_pick_tv(rows, idl, traj, rb)
    out["count_feedback_lift"] = count_feedback_lift(rows, idl, paths)

    # topics
    all_labels = set()
    for r in rows:
        for tid in r["weights"]:
            if idl.get(tid):
                all_labels.add(idl[tid])
    topics = Topics(all_labels)
    out["embed_ok"] = topics.emb_ok
    order = []
    seen = set()
    for r in rows:
        for tid in r["weights"]:
            lb = idl.get(tid)
            if lb and lb not in seen:
                seen.add(lb)
                order.append(lb)
    frame = topics.frame(order)
    out["frame_topics"] = len(set(frame.values()))

    # validate fast clustering == repo clustering on the live path (per-day, with previous day prepended)
    by_live = path_days(paths, ts_list)
    seqs_ok = 0
    for d in sorted(by_live):
        pd = (_dt.date.fromisoformat(d) - _dt.timedelta(days=1)).isoformat()
        prev = by_live.get(pd, [])
        allq = [(l[len(PREFIX):] if l.startswith(PREFIX) else l) for l in prev + by_live[d]]
        ref, _m = tp.cluster(allq)
        fast = topics.cluster_idx([topics.ix[l] for l in prev + by_live[d]])
        seqs_ok += int(ref == fast)
    out["cluster_fast_equals_repo_days"] = f"{seqs_ok}/{len(by_live)}"

    live_m = day_metrics(by_live, topics, frame)
    out["live"] = live_m
    days = sorted(live_m)

    res = {"C": [], "D": []}
    t0 = time.time()
    for v in ("C", "D"):
        for k in range(runs):
            p = replay_run(rows, idl, traj, v, SEED0 + k, recent0, restarts)
            m = day_metrics(path_days(p, ts_list), topics, frame)
            cum = {}
            for labs in p:
                for l in labs:
                    cum[l] = cum.get(l, 0) + 1
            res[v].append((m, cum, p))
    out["replay_seconds"] = round(time.time() - t0, 1)

    def arr(v, key, d):
        return np.array([r[0][d][key] for r in res[v]], dtype=float)

    table = {}
    r1 = r2 = 0
    for d in days:
        row = {}
        for key in ("modal_share", "topics", "frozen", "n"):
            row[key] = {
                "live": live_m[d][key],
                "C_mean": float(arr("C", key, d).mean()), "C_lo": pct(arr("C", key, d), 2.5), "C_hi": pct(arr("C", key, d), 97.5),
                "D_mean": float(arr("D", key, d).mean()), "D_lo": pct(arr("D", key, d), 2.5), "D_hi": pct(arr("D", key, d), 97.5),
            }
        cm, dm = arr("C", "modal_share", d), arr("D", "modal_share", d)
        se = math.sqrt(cm.var(ddof=1) / runs + dm.var(ddof=1) / runs)
        diff = float(dm.mean() - cm.mean())
        row["modal_share"]["diff_D_minus_C"], row["modal_share"]["se"] = diff, se
        row["modal_share"]["R1_day"] = bool(abs(diff) >= R1_ABS and abs(diff) >= R_SE * se)
        ct, dt_ = arr("C", "topics", d), arr("D", "topics", d)
        se2 = math.sqrt(ct.var(ddof=1) / runs + dt_.var(ddof=1) / runs)
        diff2 = float(dt_.mean() - ct.mean())
        row["topics"]["diff_D_minus_C"], row["topics"]["se"] = diff2, se2
        row["topics"]["R2_day"] = bool(abs(diff2) >= R2_REL * ct.mean() and abs(diff2) >= R_SE * se2)
        r1 += row["modal_share"]["R1_day"]
        r2 += row["topics"]["R2_day"]
        row["live_in_C_band_modal_share"] = bool(row["modal_share"]["C_lo"] <= live_m[d]["modal_share"] <= row["modal_share"]["C_hi"])
        # frame modal identity: plurality across runs
        for v in ("C", "D"):
            cnt = {}
            for rr in res[v]:
                fm = rr[0][d]["frame_modal"]
                cnt[fm] = cnt.get(fm, 0) + 1
            top = max(sorted(cnt), key=lambda k: cnt[k])
            row[f"{v}_plurality_modal_frame_topic"] = {"topic": int(top), "share_of_runs": cnt[top] / runs,
                                                         "sample_label": next(l for l in order if frame[l] == top)}
        row["live_modal_frame_topic"] = {"topic": int(live_m[d]["frame_modal"]),
                                          "sample_label": next(l for l in order if frame[l] == live_m[d]["frame_modal"])}
        table[d] = row
    need = math.ceil(len(days) / 2)
    frozen_C = float(np.mean([sum(r[0][d]["frozen"] for d in days) for r in res["C"]]))
    frozen_D = float(np.mean([sum(r[0][d]["frozen"] for d in days) for r in res["D"]]))
    out["days_table"] = table
    out["rules"] = {"R1_days": r1, "R2_days": r2, "needed_days": need,
                    "R1": r1 >= need, "R2": r2 >= need,
                    "frozen_days_mean_C": frozen_C, "frozen_days_mean_D": frozen_D,
                    "frozen_days_live": sum(live_m[d]["frozen"] for d in days),
                    "R3": abs(frozen_D - frozen_C) >= R3_FROZEN}
    out["verdict"] = "DIVERGE" if (out["rules"]["R1"] or out["rules"]["R2"] or out["rules"]["R3"]) else "CONVERGE"
    out["fidelity_live_in_C_band_days"] = f"{sum(table[d]['live_in_C_band_modal_share'] for d in days)}/{len(days)}"

    # descriptive: week TV of cumulative offer distributions (the ensemble-style read) + C half-split noise
    def agg(vs):
        tot = {}
        for rr in vs:
            for l, c in rr[1].items():
                tot[l] = tot.get(l, 0) + c
        s = sum(tot.values())
        return {l: c / s for l, c in tot.items()}

    def tv(p, q):
        ks = set(p) | set(q)
        return 0.5 * sum(abs(p.get(k, 0) - q.get(k, 0)) for k in ks)
    pc, pd_ = agg(res["C"]), agg(res["D"])
    live_cum = {}
    for labs in paths:
        for l in labs:
            live_cum[l] = live_cum.get(l, 0) + 1
    sl = sum(live_cum.values())
    live_p = {l: c / sl for l, c in live_cum.items()}
    out["week_offer_TV"] = {"D_vs_C": tv(pd_, pc), "C_half1_vs_half2": tv(agg(res["C"][0::2]), agg(res["C"][1::2])),
                            "live_vs_C": tv(live_p, pc), "live_vs_D": tv(live_p, pd_),
                            "distinct_labels_offered_live": len(live_cum),
                            "distinct_labels_offered_C_mean": float(np.mean([len(r[1]) for r in res["C"]])),
                            "distinct_labels_offered_D_mean": float(np.mean([len(r[1]) for r in res["D"]]))}
    # share of the week's seeds taken by the top-5 labels: path concentration
    def top_share(cum, n=5):
        s = sum(cum.values())
        return sum(sorted(cum.values(), reverse=True)[:n]) / s
    out["week_top5_share"] = {"live": top_share(live_cum),
                              "C_mean": float(np.mean([top_share(r[1]) for r in res["C"]])),
                              "D_mean": float(np.mean([top_share(r[1]) for r in res["D"]]))}
    if do_equiv:
        out["equivalence_vs_real_node"] = equivalence_test(rows, idl, paths)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default="primary", choices=list(WEEKS))
    ap.add_argument("--runs", type=int, default=N_RUNS)
    ap.add_argument("--diag", action="store_true", help="only data/machinery diagnostics, no verdict")
    ap.add_argument("--no-equiv", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert "wt_J-2521" in str(Path(core.__file__)), f"core imported from {core.__file__}"
    sys.stdout.reconfigure(encoding="utf-8")
    idl = load_id_labels()
    # lab_env isolation (imports core first, above). db='empty': nothing here touches the memory DB anyway.
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    from lab_env import isolate
    with isolate(db="empty"):
        res = run_week(a.week, idl, a.runs, not a.no_equiv and not a.diag, a.diag)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("days_table", "live")}, indent=1,
                     ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()

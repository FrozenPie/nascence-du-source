"""T5 Phase 0 (J-3862, D-0676, design docs/staged/t5_conversational_world_grading_design.md section 4.1 / 5): a
READ-ONLY deed-tail replay. Sits beside scripts/t5_reentry_check.py and reuses its human-only view, conversation
stamping, clustering and 24 h / distinct-conversation gate unchanged.

Question: for the Travis-authored, non-template cluster turns since 2026-08-22, how often does a hand fire within
W (default 30 min) in the same conversation (ok or refused), and how many distinct clusters per month meet the
design's admission rule 4.1:
    (a) members are human-channel Travis turns, not templates      (the t5_reentry_check view)
    (b) >= 3 members across >= 24 h and >= 2 distinct conversations (admissible24)
    (c) in >= 2 members a world deed followed within W, same conversation (this script)
...against two controls that say whether a deed tail is a BOUND deed or just "Du acts a lot":
    * placebo: the deed-tail rate at uniformly random times in the same span;
    * time-of-day matched control: the rate at the same clock time on other days (shifts of +-1..7 days), and the
      number of (a)+(b) clusters that would still meet (c) if every turn were shifted by that many days.

Deeds come from data/hands_trace.jsonl rows: each row's "hands" list holds {hand: <family>, answer, ts}; family
names are read from that key (the J-3832 pass could not). look/move/intention are not deeds (core.procedures
observe_hand ignores them too). refused / refusal_kind use core.procedures._REFUSAL / refusal_kind (regex copies
are the fallback). The dispatch field's FIRE rows are counted only for the report, never as deeds (no answer).

READ-ONLY: the DB is opened mode=ro, the logs are read with open(..., "r"), no model/hub is called (CPU embedder
only), nothing is written unless --json-out names a path.

Run:  python scripts/t5_deed_tail_replay.py [--window-min 30] [--seed 3862] [--json-out PATH]
"""
from __future__ import annotations

import argparse
import bisect
import json
import random
import re
import sys
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import t5_reentry_check as rc          # noqa: E402

NOT_DEEDS = ("look", "move", "intention", "")
MIN_DEED_MEMBERS = 2                  # design 4.1 (c)
MONTHLY_THRESHOLD = 3
SHIFT_DAYS = [d for d in range(-7, 8) if d != 0]

_REFUSAL_FALLBACK = re.compile(r"\b(slips?|comes undone|will not|won't|cannot|can't|nothing to|you have no|too wet|"
                               r"too dark|too far|not here|isn't here|is not here|out of reach|refuse|in vain|"
                               r"fails?|gives? way|goes out|sags)\b", re.I)


def _refusal_funcs():
    try:
        from core import procedures as p
        return p._REFUSAL, p.refusal_kind
    except Exception:
        return _REFUSAL_FALLBACK, (lambda a: "unknown")


def load_deeds(path: Path) -> tuple[list[dict], dict]:
    """Every distinct hand firing in the trace: {ts, family, answer}. Sorted by ts. Plus counts for the report."""
    seen = set()
    deeds = []
    stats = {"rows": 0, "rows_with_hands": 0, "hand_entries": 0, "excluded_family": 0, "duplicate": 0,
             "dispatch_fire_rows": 0, "first_ts": None, "last_ts": None, "row_ts": []}
    try:
        f = open(path, "r", encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return [], stats
    with f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            stats["rows"] += 1
            ts = r.get("ts")
            if isinstance(ts, (int, float)):
                stats["row_ts"].append(float(ts))
                stats["first_ts"] = ts if stats["first_ts"] is None else min(stats["first_ts"], ts)
                stats["last_ts"] = ts if stats["last_ts"] is None else max(stats["last_ts"], ts)
            if any(isinstance(d, dict) and d.get("decision") == "FIRE" for d in (r.get("dispatch") or [])):
                stats["dispatch_fire_rows"] += 1
            hs = r.get("hands") or []
            if hs:
                stats["rows_with_hands"] += 1
            for h in hs:
                if not isinstance(h, dict):
                    continue
                stats["hand_entries"] += 1
                fam = str(h.get("hand") or "")
                if fam in NOT_DEEDS:
                    stats["excluded_family"] += 1
                    continue
                hts = float(h.get("ts") or ts or 0)
                key = (round(hts, 1), fam)
                if key in seen:
                    stats["duplicate"] += 1
                    continue
                seen.add(key)
                deeds.append({"ts": hts, "family": fam, "answer": str(h.get("answer") or "")})
    deeds.sort(key=lambda d: d["ts"])
    return deeds, stats


def annotate_outcomes(deeds: list[dict]) -> None:
    rx, kind = _refusal_funcs()
    for d in deeds:
        d["outcome"] = "refused" if rx.search(d["answer"]) else "ok"
        d["kind"] = kind(d["answer"]) if d["outcome"] == "refused" else ""


class DeedIndex:
    def __init__(self, deeds: list[dict], boundaries: list[float]):
        self.deeds = deeds
        self.ts = [d["ts"] for d in deeds]
        self.boundaries = boundaries

    def tail(self, t: float, w: float, *, same_conversation: bool = True) -> dict | None:
        """First deed in (t, t + w], none of whose path crosses a 'Session ended' boundary (a /quit) when
        same_conversation. A silence gap cannot occur inside w (< CONV_GAP_S)."""
        i = bisect.bisect_right(self.ts, t)
        if i < len(self.ts) and self.ts[i] <= t + w:
            d = self.deeds[i]
            if same_conversation:
                j = bisect.bisect_right(self.boundaries, t)
                if j < len(self.boundaries) and self.boundaries[j] <= d["ts"]:
                    return None
            return d
        return None


def rate(idx: DeedIndex, times: list[float], w: float) -> tuple[int, int]:
    return sum(1 for t in times if idx.tail(t, w)), len(times)


def replay_all(view, since, until, *, step_s, sim, dedup, min_recurrence, min_new) -> list[dict]:
    """t5_reentry_check.replay with all_clusters=True, but keeping EVERY member of each distinct admissible cluster."""
    found, centroids = [], []
    s = since
    while s <= until:
        items = rc._mark_landed(rc.window_items(view, s))
        if len(items) >= min_new:
            for g in rc.clusters_at(items, sim):
                ok, _ = rc.admissible24(g, legacy=False, min_recurrence=min_recurrence)
                if not ok:
                    continue
                cen = rc._centroid(g)
                if any(float(cen @ c) >= dedup for c in centroids):
                    continue
                centroids.append(cen)
                found.append({"first_seen": s, "members": sorted(({"ts": m["ts"], "q": m["q"], "conv": m.get("conv", 0)}
                                                                 for m in g), key=lambda m: m["ts"])})
        s += step_s
    return found


def count_qualifying(clusters: list[dict], idx: DeedIndex, w: float, shift_days: int = 0) -> list[int]:
    """Per cluster: number of members with a deed tail when every member time is shifted by shift_days days."""
    sh = shift_days * 86400.0
    return [sum(1 for m in c["members"] if idx.tail(m["ts"] + sh, w)) for c in clusters]


def per_month(clusters, counts, key="first_seen") -> dict:
    out: dict = {}
    for c, n in zip(clusters, counts):
        m = rc._month(c[key])
        row = out.setdefault(m, {"ab_clusters": 0, "abc_clusters": 0})
        row["ab_clusters"] += 1
        if n >= MIN_DEED_MEMBERS:
            row["abc_clusters"] += 1
    return dict(sorted(out.items()))


def run(data_dir: Path, *, since: float, until: float, window_s: float, step_hours: float, seed: int,
        n_random: int, tree: Path = TREE) -> dict:
    gate = rc.read_gate_constants(tree)
    variants = rc.read_farewell_variants(tree)
    conn = rc.open_ro(Path(data_dir) / "memory" / "nascence.db")
    try:
        lived = rc.load_lived(conn)
        canon_ts, canon_txt = rc.load_canon(conn)
        boundaries = rc.load_boundaries(conn)
    finally:
        conn.close()
    aff = rc.load_affect(Path(data_dir) / "affect_log.jsonl")
    view, vstats = rc.build_view(lived, aff, canon_ts, canon_txt, variants)
    rc.assign_conversations(view, boundaries)
    vecs = rc.embed_texts([m["q"] for m in view]) if view else []
    for m, v in zip(view, vecs):
        m["vec"] = v

    deeds, dstats = load_deeds(Path(data_dir) / "hands_trace.jsonl")
    annotate_outcomes(deeds)
    idx = DeedIndex(deeds, boundaries)
    tr_lo, tr_hi = dstats["first_ts"] or since, dstats["last_ts"] or until
    lo, hi = max(since, tr_lo), min(until, tr_hi)

    fam: dict = {}
    for d in deeds:
        row = fam.setdefault(d["family"], {"n": 0, "ok": 0, "refused": 0})
        row["n"] += 1
        row[d["outcome"]] += 1
    kinds: dict = {}
    for d in deeds:
        if d["outcome"] == "refused":
            kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1

    # --- the turns themselves, in the trace span ---
    turns = [m for m in view if lo <= m["ts"] <= hi - window_s]
    t_times = [m["ts"] for m in turns]
    turn_hits = [(m, idx.tail(m["ts"], window_s)) for m in turns]
    hit_n, n = sum(1 for _, d in turn_hits if d), len(turn_hits)
    out_split = {"ok": sum(1 for _, d in turn_hits if d and d["outcome"] == "ok"),
                 "refused": sum(1 for _, d in turn_hits if d and d["outcome"] == "refused")}
    by_month_turns: dict = {}
    for m, d in turn_hits:
        r = by_month_turns.setdefault(rc._month(m["ts"]), [0, 0])
        r[1] += 1
        r[0] += 1 if d else 0

    # --- placebo: uniform random times in the span ---
    rnd = random.Random(seed)
    rand_times = [rnd.uniform(lo, hi - window_s) for _ in range(n_random)]
    rand_hit, rand_n = rate(idx, rand_times, window_s)
    # a placebo clear of Travis: random times not within 2 h of any Travis turn (Du acting alone)
    all_view_ts = sorted(m["ts"] for m in view)

    def far_from_turns(t):
        i = bisect.bisect_left(all_view_ts, t - 7200)
        return not (i < len(all_view_ts) and all_view_ts[i] <= t + 7200)
    rand_far = [t for t in rand_times if far_from_turns(t)]
    far_hit, far_n = rate(idx, rand_far, window_s)

    # --- awake placebo: Du's own cycle times (he was awake and thinking) more than 2 h from any Travis turn ---
    row_ts = [t for t in dstats["row_ts"] if lo <= t <= hi - window_s and far_from_turns(t)]
    awake = rnd.sample(row_ts, min(n_random, len(row_ts)))
    aw_hit, aw_n = rate(idx, awake, window_s)

    # --- time-of-day matched control: same clock time, other days, no Travis turn within 2 h of the shifted time ---
    ctrl = {}
    ctrl_times_all = []
    for k in SHIFT_DAYS:
        ts_k = [t + k * 86400.0 for t in t_times if lo <= t + k * 86400.0 <= hi - window_s and far_from_turns(t + k * 86400.0)]
        h, nn = rate(idx, ts_k, window_s)
        ctrl[k] = {"hits": h, "n": nn}
        ctrl_times_all += ts_k
    c_hit, c_n = sum(v["hits"] for v in ctrl.values()), sum(v["n"] for v in ctrl.values())

    # --- clusters (a)+(b), then (c) ---
    clusters = replay_all(view, since, until, step_s=step_hours * 3600, sim=gate["PROC_CLUSTER_SIM"],
                          dedup=gate["PROC_DEDUP_SIM"], min_recurrence=int(gate["PROC_MIN_RECURRENCE"]),
                          min_new=int(gate["T5_MIN_NEW_LIVED"]))
    in_span = [c for c in clusters if c["first_seen"] >= since]
    real_counts = count_qualifying(in_span, idx, window_s, 0)
    months_real = per_month(in_span, real_counts)
    shifted = {}
    for k in SHIFT_DAYS:
        cnt = count_qualifying(in_span, idx, window_s, k)
        pm = per_month(in_span, cnt)
        shifted[k] = {"abc_total": sum(v["abc_clusters"] for v in pm.values()), "per_month": pm,
                      "mean_deed_members": round(sum(cnt) / max(1, len(cnt)), 3)}
    all_months = {}
    s = since
    while s <= until:
        all_months.setdefault(rc._month(s), 0)
        s += 86400
    for mth in all_months:
        months_real.setdefault(mth, {"ab_clusters": 0, "abc_clusters": 0})
    months_real = dict(sorted(months_real.items()))
    ctrl_abc = [shifted[k]["abc_total"] for k in SHIFT_DAYS]
    real_abc = sum(v["abc_clusters"] for v in months_real.values())
    below = [m for m, v in months_real.items() if v["abc_clusters"] < MONTHLY_THRESHOLD]
    # months with any real chance of data: the first and the last are partial; report all and let the reader see
    # the placebo that matters is the AWAKE one (a random clock time is often asleep, where no hand can fire)
    placebo_matches = bool(aw_n and n and abs(hit_n / max(1, n) - aw_hit / max(1, aw_n)) < 0.10)
    return {"since": since, "until": until, "window_min": window_s / 60, "gate": gate, "view_stats": vstats,
            "view_turns_total": len(view), "deed_stats": dstats, "deed_count": len(deeds),
            "families": dict(sorted(fam.items(), key=lambda kv: -kv[1]["n"])), "refusal_kinds": kinds,
            "turn_tail": {"turns": n, "with_deed": hit_n, "rate": round(hit_n / max(1, n), 4), **out_split,
                          "per_month": {m: {"turns": v[1], "with_deed": v[0]} for m, v in sorted(by_month_turns.items())}},
            "placebo_random": {"n": rand_n, "hits": rand_hit, "rate": round(rand_hit / max(1, rand_n), 4),
                               "far_from_travis_n": far_n, "far_hits": far_hit,
                               "far_rate": round(far_hit / max(1, far_n), 4)},
            "placebo_awake": {"n": aw_n, "hits": aw_hit, "rate": round(aw_hit / max(1, aw_n), 4)},
            "tod_matched_control": {"n": c_n, "hits": c_hit, "rate": round(c_hit / max(1, c_n), 4),
                                    "per_shift": {str(k): v for k, v in ctrl.items()}},
            "clusters_ab_total": len(in_span), "clusters_abc_total_real": real_abc,
            "clusters_abc_total_shift_controls": {"values": ctrl_abc,
                                                  "mean": round(sum(ctrl_abc) / max(1, len(ctrl_abc)), 2)},
            "per_month_real": months_real,
            "clusters": [{"first_seen": c["first_seen"], "size": len(c["members"]), "deed_members": n_,
                          "members": [{"ts": m["ts"], "q": m["q"][:100].replace("\n", " "),
                                       "deed": (lambda d: (d["family"] + ":" + d["outcome"]) if d else None)(idx.tail(m["ts"], window_s))}
                                      for m in c["members"]]}
                         for c, n_ in zip(in_span, real_counts)],
            "months_below_threshold": below, "threshold": MONTHLY_THRESHOLD,
            "tail_rate_matches_control": bool(placebo_matches)}


def render(res: dict) -> str:
    L = []
    L.append(f"T5 phase 0 deed-tail replay (read-only), {rc._fmt(res['since'])} .. {rc._fmt(res['until'])}, W = {res['window_min']:g} min")
    s, d = res["view_stats"], res["deed_stats"]
    L.append(f"view: {res['view_turns_total']} Travis-authored non-template turns ({s['kept_unmarked']} without canon marker, kept)")
    L.append(f"hands_trace: {d['rows']} rows {rc._fmt(d['first_ts'] or 0)} .. {rc._fmt(d['last_ts'] or 0)}; "
             f"{d['hand_entries']} hand entries -> {res['deed_count']} distinct deeds "
             f"({d['excluded_family']} look/move/intention dropped, {d['duplicate']} duplicates)")
    L.append("deed families (n, ok, refused): " + ", ".join(f"{k} {v['n']}/{v['ok']}/{v['refused']}"
                                                          for k, v in list(res["families"].items())[:14]))
    L.append("refusal kinds: " + (", ".join(f"{k} {v}" for k, v in res["refusal_kinds"].items()) or "none"))
    t = res["turn_tail"]
    L.append("")
    L.append(f"deed tail after a Travis turn: {t['with_deed']}/{t['turns']} = {t['rate']:.1%} (ok {t['ok']}, refused {t['refused']})")
    for m, v in t["per_month"].items():
        L.append(f"   {m}: {v['with_deed']}/{v['turns']}")
    p, c = res["placebo_random"], res["tod_matched_control"]
    L.append(f"placebo, random times: {p['hits']}/{p['n']} = {p['rate']:.1%}; of those >2 h from any Travis turn: "
             f"{p['far_hits']}/{p['far_from_travis_n']} = {p['far_rate']:.1%}")
    a = res["placebo_awake"]
    L.append(f"awake placebo (Du's own cycle times, >2 h from any Travis turn): {a['hits']}/{a['n']} = {a['rate']:.1%}")
    L.append(f"time-of-day matched control (same clock time, other days, >2 h from any Travis turn): "
             f"{c['hits']}/{c['n']} = {c['rate']:.1%}")
    L.append("")
    L.append(f"clusters meeting (a)+(b): {res['clusters_ab_total']}; also (c) (>= {MIN_DEED_MEMBERS} members with a deed tail): "
             f"{res['clusters_abc_total_real']}   [shift controls, same clusters with all turns moved +-1..7 days: "
             f"mean {res['clusters_abc_total_shift_controls']['mean']}, values {res['clusters_abc_total_shift_controls']['values']}]")
    L.append("per month (first admitted):")
    for m, v in res["per_month_real"].items():
        L.append(f"   {m}: (a)+(b) {v['ab_clusters']}, (a)+(b)+(c) {v['abc_clusters']}"
                 f"{'   <-- >= ' + str(res['threshold']) if v['abc_clusters'] >= res['threshold'] else ''}")
    for cl in res["clusters"]:
        L.append(f"  cluster first admitted {rc._fmt(cl['first_seen'])}: {cl['size']} turns, {cl['deed_members']} with a deed tail")
        for m in cl["members"][:6]:
            L.append(f"      {rc._fmt(m['ts'])}  {m['deed'] or '-':<18} {m['q']}")
    L.append("")
    if res["months_below_threshold"]:
        L.append(f"VERDICT: months with fewer than {res['threshold']} qualifying clusters: {', '.join(res['months_below_threshold'])}. "
                 + ("The turn deed-tail rate is within 10 points of the awake placebo: "
                    "recommend the D-0676 defeater (retire the conversational compile behind the kill-switch)."
                    if res["tail_rate_matches_control"] else
                    "The turn deed-tail rate is 10+ points above the awake placebo, so the second half of the D-0676 defeater "
                    "(placebo matches) does NOT hold; but with no cluster reaching (a)+(b)+(c) there is nothing for the deed tail to grade. Read the numbers."))
    else:
        L.append("VERDICT: every month reaches the threshold: the shadow build (phase 1) is worth doing.")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir")
    ap.add_argument("--since", default="2026-08-22")
    ap.add_argument("--until", default=None)
    ap.add_argument("--window-min", type=float, default=30.0)
    ap.add_argument("--step-hours", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=3862)
    ap.add_argument("--n-random", type=int, default=4000)
    ap.add_argument("--json-out")
    a = ap.parse_args(argv)
    data_dir = rc.resolve_data_dir(a.data_dir)
    until = rc._ts(a.until) + 86399 if a.until else time.time()
    res = run(data_dir, since=rc._ts(a.since), until=until, window_s=a.window_min * 60, step_hours=a.step_hours,
              seed=a.seed, n_random=a.n_random)
    print(f"(data: {data_dir})")
    print(render(res))
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, ensure_ascii=False, default=str, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

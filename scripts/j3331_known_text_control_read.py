"""J-3331 -- READ-ONLY analysis: does the core/procedures.known_text() repertoire line change what the next hand does?

Reads (never writes) the live Du data dir:  data/hands_trace.jsonl, data/procedures_log.jsonl, data/procedures.json.
Writes only docs/lab/J-3331_data/known_text_read.json under THIS tree.
Usage:  python scripts/j3331_known_text_control_read.py [DATA_DIR [OUT_DIR]]
        python scripts/j3331_known_text_control_read.py --arm [DATA_DIR [OUT_DIR]]   (J-3858: reads known_text_arm.jsonl)

Method notes (all approximations are named in the output):
  * Outcome of every fired hand: procedures_log has a row for every REFUSAL and for the first OK of each 30-min stretch;
    a hands_trace hand with no log row within 2 s is therefore an OK repeat inside a stretch. Join on (key, ts).
  * Refusal kind: core.procedures.refusal_kind on the hands_trace answer (truncated to 160 chars; the live tag saw
    the full answer -- the 21 shadow rows are used to check agreement).
  * known_text state at time T is RECONSTRUCTED from the procedures_log 'rung' column (latest event per world key before T,
    rung >= persisted) -- the live line was never logged. Rust/archive and ok-repeat last_ts bumps are not reconstructable.
"""
from __future__ import annotations

import bisect
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import procedures as P          # noqa: E402  (refusal_kind is pure)

ARM_MODE = "--arm" in sys.argv                      # J-3858: D-0693 arm reader, see arm_main() below
_ARGS = [a for a in sys.argv[1:] if a != "--arm"]
DATA = Path(_ARGS[0]) if len(_ARGS) > 0 else Path("C:/Nascence/data")
ORDER = list(P.RUNGS)
OUT = Path(_ARGS[1]) if len(_ARGS) > 1 else ROOT / "docs" / "lab" / "J-3331_data"


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0, c - h), 3), round(min(1, c + h), 3))


def day(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def n_per_arm(p1, delta, alpha=0.05, power=0.8):
    p2 = max(0.0, p1 - delta)
    pb = (p1 + p2) / 2
    za, zb = 1.959964, 0.841621
    if p1 <= 0:
        return None
    return math.ceil(((za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / (delta ** 2))


# ---------------------------------------------------------------------------------------------------------------
# J-3858 / D-0693: --arm mode. Reads data/known_text_arm.jsonl (written only while NASCENCE_KNOWN_TEXT_ARM is on) and
# joins it to data/hands_trace.jsonl. Read-only on DATA; writes only OUT/known_text_arm_read.json.
#
# Unit = one ELIGIBLE THOUGHT. The arm row is written at prompt-build time and carries only the cycle (24 chars). One
# cycle is a whole thought train (most have 6+ hands_trace rows; mid-train rows are outside the arm), and
# _build_system_prompt can run twice for one thought. So each arm row is mapped to the FIRST hands_trace row of the
# same cycle at or after the arm row's ts, and arm rows mapping to the same trace row are ONE thought. Arm rows with
# no trace row after them are counted as unmatched and left out, never guessed at.
# ---------------------------------------------------------------------------------------------------------------
STOP_N = 3000                 # pre-registered: read at 3,000 eligible thoughts per arm
INERT_BAND = 0.01             # P1 difference interval inside +-1.0 point in both directions = inert on behaviour
EXCLUDED_FAMILIES = ("look", "move", "intention")        # same exclusion as the historical read
STATIC_PRONE = ("sow", "mow", "weed")
TRAIL_N, TRAIL_MIN, TRAIL_RATE = 20, 5, 0.5
BOOT_B = 2000
BOOT_SEED = 3331


def _jsonl(path):
    out = []
    if not Path(path).exists():
        return out
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def _norm_fam(name):
    return str(name).strip().lower().replace("_", " ")


def prone_set_at(plog_by_key, ts):
    """Refusal-prone families at ts: the static set plus any whose last TRAIL_N world events before ts (at least
    TRAIL_MIN of them) were refused more than TRAIL_RATE of the time."""
    prone = set(STATIC_PRONE)
    for key, (tss, evs) in plog_by_key.items():
        i = bisect.bisect_left(tss, ts)
        w = evs[max(0, i - TRAIL_N):i]
        if len(w) >= TRAIL_MIN and sum(1 for e in w if e.get("outcome") == "refused") / len(w) > TRAIL_RATE:
            prone.add(_norm_fam(key.split(":", 1)[-1]))
    return prone


def join_arm(arm_rows, trace_rows):
    """-> (thoughts, stats). One dict per eligible thought: {arm, day, fired[(fam, ts)], would_name, cycle}."""
    by_cycle = defaultdict(list)
    for r in trace_rows:
        by_cycle[(r.get("cycle") or "")[:24]].append(r)
    for v in by_cycle.values():
        v.sort(key=lambda r: r["ts"])
    seen = {}
    st = {"arm_rows": len(arm_rows), "duplicate_arm_rows": 0, "unmatched_arm_rows": 0, "arm_conflicts": 0}
    for a in sorted(arm_rows, key=lambda r: r["ts"]):
        rows = by_cycle.get((a.get("cycle") or "")[:24], [])
        i = bisect.bisect_left([r["ts"] for r in rows], a["ts"] - 1.0)
        if i >= len(rows):
            st["unmatched_arm_rows"] += 1
            continue
        k = ((a.get("cycle") or "")[:24], rows[i]["ts"])
        if k in seen:
            st["duplicate_arm_rows"] += 1
            if seen[k]["arm"] != a.get("arm"):
                st["arm_conflicts"] += 1
            continue
        fired = [(h["hand"], h["ts"]) for h in (rows[i].get("hands") or []) if h.get("hand") not in EXCLUDED_FAMILIES]
        seen[k] = {"arm": a.get("arm"), "day": day(a["ts"]), "fired": fired, "cycle": k[0],
                   "would_name": {_norm_fam(n) for n in (a.get("would_name") or [])}}
    return list(seen.values()), st


def _boot_diff(by_day, B=BOOT_B, seed=BOOT_SEED):
    """Day-block bootstrap interval for (shown rate - withheld rate). by_day: {day: [ns, ks, nw, kw]}."""
    days = sorted(by_day)
    if not days:
        return None
    import random
    rng = random.Random(seed)
    diffs = []
    for _ in range(B):
        ns = ks = nw = kw = 0
        for _d in days:
            r = by_day[days[rng.randrange(len(days))]]
            ns += r[0]; ks += r[1]; nw += r[2]; kw += r[3]
        if ns and nw:
            diffs.append(ks / ns - kw / nw)
    if len(diffs) < B // 2:
        return None
    diffs.sort()
    return [round(diffs[int(0.025 * len(diffs))], 4), round(diffs[int(0.975 * len(diffs)) - 1], 4)]


def _outcome(pairs):
    """pairs: {arm: [(n, k, day), ...]} -> per-arm rate + Wilson, point difference, day-block bootstrap interval."""
    res = {}
    by_day = defaultdict(lambda: [0, 0, 0, 0])
    for arm, off in (("shown", 0), ("withheld", 2)):
        n = sum(x[0] for x in pairs[arm]); k = sum(x[1] for x in pairs[arm])
        res[arm] = {"n": n, "k": k, "rate": round(k / n, 4) if n else None, "wilson95": wilson(k, n)}
        for (nn, kk, d) in pairs[arm]:
            by_day[d][off] += nn; by_day[d][off + 1] += kk
    s, w = res["shown"]["rate"], res["withheld"]["rate"]
    res["diff_shown_minus_withheld"] = round(s - w, 4) if s is not None and w is not None else None
    res["diff_day_block_boot95"] = _boot_diff(dict(by_day)) if res["diff_shown_minus_withheld"] is not None else None
    res["n_days"] = len(by_day)
    return res


def arm_read(arm_rows, trace_rows, plog_rows=()):
    thoughts, st = join_arm(arm_rows, trace_rows)
    plog = defaultdict(list)
    for e in plog_rows:
        if e.get("event") == "world":
            plog[e["key"]].append(e)
    plog_by_key = {}
    for k, v in plog.items():
        v.sort(key=lambda e: e["ts"])
        plog_by_key[k] = ([e["ts"] for e in v], v)
    arms = ("shown", "withheld")
    p1 = {a: [] for a in arms}; p2 = {a: [] for a in arms}; p3 = {a: [] for a in arms}
    n_th = Counter(); n_hands = Counter()
    for t in thoughts:
        a = t["arm"]
        if a not in arms:
            continue
        n_th[a] += 1
        p1[a].append((1, 1 if t["fired"] else 0, t["day"]))
        if t["fired"]:
            n_hands[a] += len(t["fired"])
            inn = sum(1 for fam, _ in t["fired"] if _norm_fam(fam) in t["would_name"])
            p2[a].append((len(t["fired"]), inn, t["day"]))
            prone = sum(1 for fam, ts in t["fired"] if _norm_fam(fam) in prone_set_at(plog_by_key, ts))
            p3[a].append((len(t["fired"]), prone, t["day"]))
    res = {"eligible_thoughts": dict(n_th), "fired_world_hands": dict(n_hands), "join": st,
           "P1_world_hand_fire_rate_per_eligible_thought": _outcome(p1),
           "P2_fired_family_in_would_name": _outcome(p2),
           "P3_refusal_prone_family_share": _outcome(p3)}
    lo = min(n_th.get("shown", 0), n_th.get("withheld", 0))
    res["stopping_rule"] = {"per_arm_target": STOP_N, "smaller_arm": lo, "reached": lo >= STOP_N}
    d1 = res["P1_world_hand_fire_rate_per_eligible_thought"]["diff_day_block_boot95"]
    d2 = res["P2_fired_family_in_would_name"]["diff_day_block_boot95"]
    if lo < STOP_N:
        v = f"NOT YET: smaller arm has {lo} of {STOP_N} eligible thoughts. Intervals are descriptive, not the pre-registered read."
    elif d1 is None:
        v = "READ REACHED but the P1 interval could not be computed (too few day blocks)."
    elif -INERT_BAND < d1[0] and d1[1] < INERT_BAND:
        v = "P1 INERT: the 95% interval on the fire-rate difference lies inside +-1.0 point. Founder decides keep-as-harmless-context vs retire."
    elif d1[0] > 0 or d1[1] < 0 or (d2 is not None and (d2[0] > 0 or d2[1] < 0)):
        v = "GAP: the P1 or P2 interval excludes zero. The arm stops; founder decides which prompt to keep. Never left running on its own."
    else:
        v = "INCONCLUSIVE at the pre-registered n: interval is neither inside +-1.0 point nor clear of zero. Founder decides whether to extend."
    res["verdict"] = v
    return res


def arm_main():
    arm_rows = _jsonl(DATA / "known_text_arm.jsonl")
    OUT.mkdir(parents=True, exist_ok=True)
    if not arm_rows:
        res = {"verdict": "NO DATA: known_text_arm.jsonl is missing or empty (flag NASCENCE_KNOWN_TEXT_ARM is default OFF, or Du has not restarted since it was flipped)."}
    else:
        res = arm_read(arm_rows, _jsonl(DATA / "hands_trace.jsonl"), _jsonl(DATA / "procedures_log.jsonl"))
        res["data_dir"] = str(DATA)
    (OUT / "known_text_arm_read.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


def main():
    plog =[json.loads(l) for l in open(DATA / "procedures_log.jsonl", encoding="utf-8")]
    world = sorted((r for r in plog if r.get("event") == "world"), key=lambda r: r["ts"])
    ev_by_key = defaultdict(list)
    for r in world:
        ev_by_key[r["key"]].append(r)
    first_persisted = {}
    for k, evs in ev_by_key.items():
        for r in evs:
            if ORDER.index(r["rung"]) >= 1:
                first_persisted[k] = r["ts"]
                break
    first_any = min(first_persisted.values()) if first_persisted else None

    tl = sorted((r["ts"], r["key"], r["rung"]) for r in world)

    def line_set(T):
        state = {}
        for ts, k, rung in tl:
            if ts > T:
                break
            state[k] = rung
        return {k for k, rg in state.items() if ORDER.index(rg) >= 1}

    rows = 0
    fired = []
    rows_ts = []
    for l in open(DATA / "hands_trace.jsonl", encoding="utf-8"):
        r = json.loads(l)
        rows += 1
        rows_ts.append(r["ts"])
        for h in r.get("hands") or []:
            fired.append((h["ts"], h["hand"], h["answer"], r.get("location", ""), r["cycle"]))
    rows_ts.sort()

    log_idx = {k: ([e["ts"] for e in v], v) for k, v in ev_by_key.items()}

    def outcome(ts, fam):
        tss, evs = log_idx.get(f"world:{fam}", ([], []))
        i = bisect.bisect_left(tss, ts - 2.0)
        if i < len(evs) and evs[i]["ts"] <= ts + 2.0:
            return evs[i]["outcome"]
        return "ok_repeat"

    hands = []
    for ts, fam, ans, loc, cyc in fired:
        if fam in ("look", "move", "intention"):
            continue
        oc = outcome(ts, fam)
        kind = P.refusal_kind(ans) if oc == "refused" else None
        hands.append({"ts": ts, "fam": fam, "oc": oc, "kind": kind, "loc": loc, "cyc": cyc})
    hands.sort(key=lambda h: h["ts"])

    sp = DATA / "procedures_refusal_kind_shadow.jsonl"
    shadow = [json.loads(l) for l in open(sp, encoding="utf-8")] if sp.exists() else []
    agree = sum(1 for s in shadow if P.refusal_kind(s["answer"]) == s["kind"])

    n_after = sum(1 for t in rows_ts if first_any and t >= first_any)
    days = sorted({day(t) for t in rows_ts})
    fad = day(first_any) if first_any else None
    res = {
        "data_dir": str(DATA), "hands_trace_rows": rows, "first_row": day(rows_ts[0]), "last_row": day(rows_ts[-1]),
        "world_log_events": len(world), "world_log_refused": sum(1 for r in world if r["outcome"] == "refused"),
        "first_family_persisted": {k: day(v) for k, v in sorted(first_persisted.items(), key=lambda x: x[1])},
        "first_any_persisted_day": fad,
        "rows_at_or_after_first_persisted": n_after,
        "share_rows_with_nonempty_line_upper_bound": round(n_after / rows, 4),
        "fired_world_hands": len(hands),
        "shadow_rows": len(shadow), "shadow_kind_agreement_on_truncated": f"{agree}/{len(shadow)}",
    }
    size_by_day = {}
    for d in days:
        T = time.mktime(time.strptime(d + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        size_by_day[d] = len(line_set(T))
    res["line_family_count_by_day_end"] = size_by_day
    hpd = Counter(day(h["ts"]) for h in hands)
    post_days = [d for d in days if d >= fad]
    res["world_hands_per_day"] = {
        "days_with_hands": len(hpd), "total": len(hands), "mean_per_calendar_day": round(len(hands) / max(1, len(days)), 2),
        "mean_per_day_post_first_persisted": round(sum(v for d, v in hpd.items() if d >= fad) / max(1, len(post_days)), 2)}

    fam_tab = {}

    def stats(L):
        n = len(L)
        ref = sum(1 for h in L if h["oc"] == "refused")
        sk = sum(1 for h in L if h["kind"] == "skill")
        return {"n": n, "refused": ref, "skill": sk, "refusal_rate": round(ref / n, 3) if n else None,
                "skill_rate": round(sk / n, 3) if n else None}

    for fam in sorted({h["fam"] for h in hands}):
        fp = first_persisted.get(f"world:{fam}")
        pre = [h for h in hands if h["fam"] == fam and (fp is None or h["ts"] < fp)]
        post = [h for h in hands if h["fam"] == fam and fp is not None and h["ts"] >= fp]
        fam_tab[fam] = {"first_persisted": day(fp) if fp else None, "pre": stats(pre), "post": stats(post)}
    res["per_family"] = fam_tab
    both = [f for f, t in fam_tab.items() if t["pre"]["n"] >= 1 and t["post"]["n"] >= 1]

    def pool(key, sub):
        n = sum(fam_tab[f][key]["n"] for f in both)
        k = sum(fam_tab[f][key][sub] for f in both)
        return {"n": n, "k": k, "rate": round(k / n, 3) if n else None, "wilson95": wilson(k, n)}

    res["pooled_families_with_both_periods"] = {
        "families": both,
        "pre_any_refusal": pool("pre", "refused"), "post_any_refusal": pool("post", "refused"),
        "pre_skill_refusal": pool("pre", "skill"), "post_skill_refusal": pool("post", "skill")}
    eras = {"before_first_persisted_any": [h for h in hands if h["ts"] < first_any],
            "after_first_persisted_any": [h for h in hands if h["ts"] >= first_any]}
    res["era_all_families"] = {}
    for name, L in eras.items():
        s = stats(L)
        s["skill_wilson95"] = wilson(s["skill"], s["n"])
        res["era_all_families"][name] = s
    res["refusal_kind_counts_all"] = dict(Counter(h["kind"] for h in hands if h["oc"] == "refused"))

    # natural in-line / out-of-line contrast (CONFOUNDED by construction: line = 5 most recently used persisted+ families)
    ev_i = 0
    prev_state = {}
    inl = {"in": Counter(), "out": Counter()}
    for h in hands:
        while ev_i < len(world) and world[ev_i]["ts"] < h["ts"] - 2.0:
            e = world[ev_i]
            prev_state[e["key"]] = (e["rung"], e["ts"])
            ev_i += 1
        cand = sorted(((ts, k) for k, (rg, ts) in prev_state.items() if ORDER.index(rg) >= 1), reverse=True)
        top5 = {k for _, k in cand[:5]}
        grp = "in" if f"world:{h['fam']}" in top5 else "out"
        inl[grp]["n"] += 1
        if h["oc"] == "refused":
            inl[grp]["refused"] += 1
        if h["kind"] == "skill":
            inl[grp]["skill"] += 1
        h["in_line"] = grp == "in"
    res["natural_in_vs_out_of_line_CONFOUNDED"] = {
        g: {"n": c["n"], "refused": c["refused"], "skill": c["skill"],
            "refusal_rate": round(c["refused"] / c["n"], 3) if c["n"] else None,
            "skill_rate": round(c["skill"] / c["n"], 3) if c["n"] else None,
            "skill_wilson95": wilson(c["skill"], c["n"])} for g, c in inl.items()}
    post = [h for h in hands if h["ts"] >= first_any]
    res["choice_share"] = {"post_hands": len(post), "fired_family_was_in_line": sum(1 for h in post if h.get("in_line")),
                           "share": round(sum(1 for h in post if h.get("in_line")) / max(1, len(post)), 3)}

    ps = res["era_all_families"]["after_first_persisted_any"]
    p_any = ps["refusal_rate"] or 0.0
    p_sk = ps["skill_rate"] or 0.0
    res["power"] = {
        "baseline_any_refusal_post": p_any, "baseline_skill_refusal_post": p_sk,
        "n_per_arm_15pt_drop_any_refusal": n_per_arm(p_any, 0.15) if p_any >= 0.15 else "baseline < 15 points: a 15-point DROP is impossible",
        "n_per_arm_15pt_drop_skill_refusal": n_per_arm(p_sk, 0.15) if p_sk >= 0.15 else "baseline < 15 points: a 15-point DROP is impossible",
        "n_per_arm_5pt_drop_skill": n_per_arm(p_sk, 0.05) if p_sk >= 0.05 else "baseline < 5 points",
        "n_per_arm_3pt_drop_skill": n_per_arm(p_sk, 0.03) if p_sk >= 0.03 else "baseline < 3 points",
        "hands_per_day_post": res["world_hands_per_day"]["mean_per_day_post_first_persisted"]}
    last = sorted(days)[-14:]
    res["world_hands_last14_days"] = {d: hpd.get(d, 0) for d in last}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "known_text_read.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("per_family", "line_family_count_by_day_end")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    arm_main() if ARM_MODE else main()

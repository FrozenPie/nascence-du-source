"""
J-3409 report: reads docs/lab/J-3409_data/{author_runs.jsonl, pairs_extra.json, hand_labels_extra.json, judge_runs_gemma4_extra.jsonl}
plus the J-3232 pair set and hand labels (docs/lab/J-3232_data), applies the PRE-REGISTERED pass criteria
(docs/lab/J-3409_data/PREREGISTRATION.md) and writes report.json + report.md next to the data. Read-only on everything else.
Run: python scripts/lab_guidance_classify2_report.py [--data-dir DIR] [--runs FILE --tag _ramses]   (--data-dir is for the unit test)
"""
from __future__ import annotations
import json, math, random, collections, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs" / "lab" / "J-3409_data"
OLD = ROOT / "docs" / "lab" / "J-3232_data"
CANON = {"assimilate": "corroborate", "same_lesson": "corroborate", "accommodate": "accommodate", "contradicts": "accommodate",
         "compatible_different": "compat", "different": "compat", "unrelated": "unrelated"}
MAIN = ["A", "B", "B0", "B2", "B3", "B4"]
REV = {"B": "Brev", "B0": "B0rev", "B2": "B2rev", "B3": "B3rev", "B4": "B4rev"}
CAND = ["B", "B0", "B2", "B3", "B4"]
OUTC = ("corroborate", "compat", "accommodate", "unrelated", "invalid")
P2_TOL = 10.0      # points
P3_MIN_REDUCTION = 0.5


def outcome(rel: str) -> str:
    return CANON.get(rel, "invalid")      # invalid/unparseable = NOT corroborating (live code since J-3060: non-committal)


def load(data_dir: Path, old_dir: Path, runs_name: str = "author_runs.jsonl"):
    pairs = {p["id"]: p for p in json.load(open(old_dir / "pairs.json", encoding="utf-8"))}
    pairs.update({p["id"]: p for p in json.load(open(data_dir / "pairs_extra.json", encoding="utf-8"))})
    hand = dict(json.load(open(old_dir / "hand_labels.json", encoding="utf-8"))["labels"])
    he = json.load(open(data_dir / "hand_labels_extra.json", encoding="utf-8"))
    hand.update(he["labels"])
    strength = he.get("strength", {})
    runs, seen = [], set()
    for l in open(data_dir / runs_name, encoding="utf-8"):
        r = json.loads(l)
        k = (r["pid"], r["arm"], r["rep"])
        if k in seen:          # a resumed run can repeat a row; the first one wins
            continue
        seen.add(k)
        runs.append(r)
    judge = {}
    jf = data_dir / "judge_runs_gemma4_extra.jsonl"
    if jf.exists():
        for l in open(jf, encoding="utf-8"):
            r = json.loads(l)
            judge[r["pid"]] = r["label"]
    return pairs, hand, strength, runs, judge


def groups(pairs, hand, strength):
    g = {}
    S = [p for p, q in pairs.items() if q["set"] == "S"]
    g["S_tight8"] = S
    g["S_tight8_excl_g66253255"] = [p for p in S if "g66253255" not in p]
    g["S2_same_inside_mixed"] = [p for p, q in pairs.items() if q["set"] == "S2"]
    g["S3_other_families"] = [p for p, q in pairs.items() if q["set"] == "S3"]
    g["S3_strength3"] = [p for p in g["S3_other_families"] if strength.get(p) == 3]
    g["S3_strength2"] = [p for p in g["S3_other_families"] if strength.get(p) == 2]
    g["S3_strength1_weakest_paraphrases"] = [p for p in g["S3_other_families"] if strength.get(p) == 1]
    if g["S3_other_families"]:
        low = min(g["S3_other_families"], key=lambda p: (pairs[p].get("overlap", 1), p))
        g["S3_lowest_overlap_pair"] = [low]
    g["ALL_hand_same"] = [p for p in pairs if hand.get(p) == "S"]
    g["NOT_same_pool"] = [p for p in pairs if hand.get(p) in ("N", "C", "U", "X")]
    g["M_notsame"] = [p for p in pairs if pairs[p]["set"] == "M" and hand.get(p) == "N"]
    g["hand_unrelated"] = [p for p in pairs if hand.get(p) == "U"]
    g["hand_compatible_different"] = [p for p in pairs if hand.get(p) == "C"]
    g["N2_hard_negatives"] = [p for p, q in pairs.items() if q["set"] == "N2"]
    return g


def by_arm(runs):
    d = collections.defaultdict(lambda: collections.defaultdict(list))       # arm -> pid -> [outcome per call]
    for r in runs:
        d[r["arm"]][r["pid"]].append(outcome(r["relation"]))
    return d


def tally(d, arm, pids):
    c = collections.Counter()
    for p in pids:
        for o in d.get(arm, {}).get(p, []):
            c[o] += 1
    return c, sum(c.values())


def rate(c, n, k="corroborate"):
    return 100.0 * c.get(k, 0) / n if n else float("nan")


def cell(c, n, k):
    return f"{c.get(k, 0)}/{n} ({rate(c, n, k):.0f}%)" if n else "-"


def boot_diff(d, arm, base, pids, key="corroborate", iters=2000, seed=3409):
    """pair-cluster bootstrap 95% CI of (arm rate - base rate) in points over the pairs in pids."""
    rows = []
    for p in pids:
        a, b = d.get(arm, {}).get(p, []), d.get(base, {}).get(p, [])
        if a and b:
            rows.append((sum(o == key for o in a) / len(a), sum(o == key for o in b) / len(b)))
    if len(rows) < 3:
        return (float("nan"), float("nan"))
    rnd = random.Random(seed)
    diffs = []
    for _ in range(iters):
        s = [rows[rnd.randrange(len(rows))] for _ in rows]
        diffs.append(100.0 * (sum(x for x, _ in s) - sum(y for _, y in s)) / len(s))
    diffs.sort()
    return (diffs[int(0.025 * iters)], diffs[int(0.975 * iters)])


def kappa(a, b):
    n = len(a)
    if not n:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main(data_dir: Path = D, old_dir: Path = OLD, runs_name: str = "author_runs.jsonl", tag: str = "") -> dict:
    pairs, hand, strength, runs, judge = load(data_dir, old_dir, runs_name)
    g = groups(pairs, hand, strength)
    d = by_arm(runs)
    ref = old_dir / "author_runs.jsonl"          # J-3232 Ramses :11441 runs of A and B (2 repeats), shown as reference rows only
    if ref.exists():
        for l in open(ref, encoding="utf-8"):
            r = json.loads(l)
            if r["arm"] in ("A", "B"):
                d[r["arm"] + "@Ramses"][r["pid"]].append(outcome(r["relation"]))
    arms = [a for a in MAIN + list(REV.values()) if a in d]
    tab_arms = arms + [a for a in ("A@Ramses", "B@Ramses") if a in d]
    rep = {"n_pairs": len(pairs), "n_author_calls": len(runs), "arms": arms, "groups": {k: len(v) for k, v in g.items()}}
    md = ["# J-3409 results (author arm command-r7b via LOCAL ollama :11433, temp 0.2; main arms 3 repeats, rev arms 1; hand-label ground truth)\n",
          "Outcome classes: corroborate (A assimilate / 4-way same_lesson), compat (4-way compatible_different or different, plus unrelated "
          "when shown separately), accommodate (A accommodate / 4-way contradicts), unrelated. Invalid answers count as NOT corroborating.\n"]
    unmatched = [a for a in arms if sum(len(v) for v in d[a].values()) == 0]
    # ---- group tables
    show = ["S_tight8", "S_tight8_excl_g66253255", "S2_same_inside_mixed", "S3_other_families", "S3_strength3", "S3_strength2",
            "S3_strength1_weakest_paraphrases", "S3_lowest_overlap_pair", "ALL_hand_same", "NOT_same_pool", "M_notsame",
            "hand_unrelated", "hand_compatible_different", "N2_hard_negatives"]
    tabs = {}
    for name in show:
        if name not in g:
            continue
        md.append(f"\n## {name} ({len(g[name])} pairs)\n")
        md.append("| arm | corroborate | compat | accommodate | unrelated | invalid |\n|---|---|---|---|---|---|")
        for a in tab_arms:
            c, n = tally(d, a, g[name])
            tabs.setdefault(name, {})[a] = {k: c.get(k, 0) for k in OUTC} | {"n": n}
            md.append(f"| {a} | " + " | ".join(cell(c, n, k) for k in OUTC) + " |")
    rep["tables"] = tabs
    # ---- Q set: not-same pairs that local A corroborates in >=1 call
    Q = [p for p in g["NOT_same_pool"] if any(o == "corroborate" for o in d.get("A", {}).get(p, []))]
    rep["Q_pairs"] = Q
    cq, nq = tally(d, "A", Q)
    md.append(f"\n## Q = not-same pairs that A corroborates in >=1 call ({len(Q)} pairs; of {len(g['NOT_same_pool'])} not-same)\n")
    md.append("| arm | corroborate on Q | compat | accommodate | unrelated | invalid |\n|---|---|---|---|---|---|")
    for a in arms:
        c, n = tally(d, a, Q)
        md.append(f"| {a} | " + " | ".join(cell(c, n, k) for k in OUTC) + " |")
    # ---- pass/fail
    base = tally(d, "A", g["ALL_hand_same"])
    verdicts = {}
    md.append("\n## Pre-registered criteria (PREREGISTRATION.md)\n")
    md.append("A baseline (local re-run): tight-8 %s, S3 %s, pooled same %s, corroborate on Q %s\n" % (
        cell(*tally(d, "A", g["S_tight8"]), "corroborate"), cell(*tally(d, "A", g["S3_other_families"]), "corroborate"),
        cell(*base, "corroborate"), cell(cq, nq, "corroborate")))
    md.append("| arm | P1 same-lesson wrong accommodates (must be 0) | P2 tight-8 diff vs A | P2 S3 diff vs A | P2 pooled diff vs A [95% CI] | P3 corroborate on Q, reduction vs A | PASS P1-P3 |\n|---|---|---|---|---|---|---|")
    for a in CAND + list(REV.values()):
        if a not in d:
            continue
        cs, ns = tally(d, a, g["ALL_hand_same"])
        p1 = cs.get("accommodate", 0)
        dif = {}
        for nm in ("S_tight8", "S3_other_families", "ALL_hand_same"):
            ca, na = tally(d, a, g[nm])
            cb, nb = tally(d, "A", g[nm])
            dif[nm] = rate(ca, na) - rate(cb, nb) if na and nb else float("nan")
        ci = boot_diff(d, a, "A", g["ALL_hand_same"])
        cqa, nqa = tally(d, a, Q)
        ra, rb = rate(cqa, nqa), rate(cq, nq)
        red = (1 - ra / rb) if rb and not math.isnan(ra) else float("nan")
        ok1 = p1 == 0
        ok2 = all(dif[k] >= -P2_TOL for k in dif)
        ok3 = (not math.isnan(red)) and red >= P3_MIN_REDUCTION
        verdicts[a] = {"P1_wrong_accommodates": p1, "P2_diff": dif, "P2_pooled_CI95": ci, "P3_corroborate_on_Q": [cqa.get("corroborate", 0), nqa],
                       "P3_reduction": red, "P1": ok1, "P2": ok2, "P3": ok3, "PASS": ok1 and ok2 and ok3}
        md.append(f"| {a} | {p1}/{ns} | {dif['S_tight8']:+.1f} | {dif['S3_other_families']:+.1f} | {dif['ALL_hand_same']:+.1f} [{ci[0]:+.1f}, {ci[1]:+.1f}] | "
                  f"{cqa.get('corroborate', 0)}/{nqa} ({ra:.0f}%) vs A {rb:.0f}%: {100 * red:.0f}% | {'**PASS**' if verdicts[a]['PASS'] else 'fail'}"
                  f" ({'P1' if ok1 else 'p1'}{'P2' if ok2 else 'p2'}{'P3' if ok3 else 'p3'}) |")
    for a, rv in REV.items():
        if a in verdicts and verdicts[a]["PASS"] and rv in verdicts:
            v = verdicts[rv]
            p4 = v["P1"] and v["P2_diff"]["ALL_hand_same"] >= -P2_TOL and v["P3_reduction"] >= P3_MIN_REDUCTION
            verdicts[a]["P4_rev_holds"] = p4
            md.append(f"\nP4 (order control) for {a}: rev arm {rv} P1/P2-pooled/P3 hold: {p4}")
    rep["verdicts"] = verdicts
    winners = [a for a in CAND if verdicts.get(a, {}).get("PASS") and verdicts[a].get("P4_rev_holds") is True]   # no rev run -> not a winner
    rep["winners"] = winners
    md.append("\n**Arms passing P1-P3 and P4: %s**" % (winners or "none -> D-0621 defeater: leave the prompt"))
    # ---- selection-bias check on P3: Q is chosen from A's own calls, so A's rate on Q is inflated by selection. Split-half: pick
    # Q0 from A's repeat 0 only and compare A and each main arm on repeats 1 and 2 (independent calls, unbiased).
    byrep = collections.defaultdict(dict)
    for r in runs:
        byrep[(r["arm"], r["pid"])][r["rep"]] = outcome(r["relation"])
    Q0 = [p for p in g["NOT_same_pool"] if byrep.get(("A", p), {}).get(0) == "corroborate"]
    md.append(f"\n## P3 selection-bias check (split half): Q0 = {len(Q0)} not-same pairs that A corroborates on repeat 0; rates are on repeats 1-2 only\n")
    md.append("| arm | corroborate on Q0 (repeats 1-2) | reduction vs A | same-lesson corroboration, repeats 1-2 (all hand-same) |\n|---|---|---|---|")
    split = {}
    def _r12(arm, pids):
        k = n = 0
        for p in pids:
            for rp in (1, 2):
                o = byrep.get((arm, p), {}).get(rp)
                if o is not None:
                    n += 1
                    k += o == "corroborate"
        return k, n
    ka, na = _r12("A", Q0)
    for a in MAIN:
        if a not in d:
            continue
        k, n = _r12(a, Q0)
        ks, ns_ = _r12(a, g["ALL_hand_same"])
        red = (1 - (k / n) / (ka / na)) if n and na and ka else float("nan")
        split[a] = {"Q0_corroborate": [k, n], "reduction_vs_A": red, "same_lesson_corroborate": [ks, ns_]}
        md.append(f"| {a} | {k}/{n} ({100 * k / n if n else float('nan'):.0f}%) | {100 * red:.0f}% | {ks}/{ns_} ({100 * ks / ns_ if ns_ else float('nan'):.0f}%) |")
    rep["split_half_P3"] = split
    # ---- weakest paraphrases per pair
    md.append("\n## S3 per-pair corroboration rate (main arms, 3 calls each; strength 3 = near restatement, 1 = weakest paraphrase)\n")
    md.append("| pair | strength | overlap | " + " | ".join(a for a in MAIN if a in d) + " | note |\n|---|---|---|" + "---|" * len([a for a in MAIN if a in d]) + "---|")
    for p in g["S3_other_families"]:
        row = [f"{sum(o == 'corroborate' for o in d[a].get(p, []))}/{len(d[a].get(p, []))}" for a in MAIN if a in d]
        md.append(f"| {p} | {strength.get(p)} | {pairs[p].get('overlap')} | " + " | ".join(row) + f" | {pairs[p].get('note')} |")
    # ---- judge cross-check on the extra pairs
    jm = {"same": 1, "compatible_different": 0, "contradicts": 0, "unrelated": 0}
    ids = [p for p in judge if p in hand and hand[p] in ("S", "C", "U", "N", "X")]
    if ids:
        a = [1 if hand[p] == "S" else 0 for p in ids]
        b = [jm.get(judge[p], 0) for p in ids]
        agree = sum(x == y for x, y in zip(a, b))
        rep["judge_extra"] = {"n": len(ids), "agree": agree, "kappa": round(kappa(a, b), 2),
                              "judge_label_mix": dict(collections.Counter(judge[p] for p in ids))}
        md.append(f"\n## Judge cross-check on the {len(ids)} extra pairs (gemma4:12b, Google; author is Cohere)\n")
        md.append(f"agrees with the hand same/not-same call on {agree}/{len(ids)}, kappa {rep['judge_extra']['kappa']}; judge label mix {rep['judge_extra']['judge_label_mix']}")
        dis = [(p, hand[p], judge[p]) for p, x, y in zip(ids, a, b) if x != y]
        md.append(f"disagreements (pair, hand, judge): {dis}")
    # ---- downstream branch table
    md.append("\n## What each verdict does downstream (core/guidance_learning.integrate_guidance branch table)\n")
    md.append("corroborate -> corroboration_count+1, entrenchment+0.20, capture added (promotion at 2). compat and unrelated -> the existing "
              "`else # unrelated` branch: ONE new tentative belief, nothing on the candidate changes. accommodate -> new belief plus self-domain fork / world-method supersede-or-penalise.\n")
    md.append("| arm | hand-same pairs: corroborated / became separate belief / accommodate-branch | not-same pairs: corroborated (false promote path) / separate belief / accommodate-branch |\n|---|---|---|")
    for a in arms:
        cs, ns = tally(d, a, g["ALL_hand_same"])
        cn, nn = tally(d, a, g["NOT_same_pool"])
        sep_s = cs.get("compat", 0) + cs.get("unrelated", 0) + cs.get("invalid", 0)
        sep_n = cn.get("compat", 0) + cn.get("unrelated", 0) + cn.get("invalid", 0)
        md.append(f"| {a} | {cs.get('corroborate', 0)} / {sep_s} / {cs.get('accommodate', 0)} (n={ns}) | {cn.get('corroborate', 0)} / {sep_n} / {cn.get('accommodate', 0)} (n={nn}) |")
    # ---- accommodates by hand label
    md.append("\n## Where each arm's accommodate/contradicts verdicts land (pooled calls)\n")
    md.append("| arm | total | on hand-same | on hand-compat/unrelated/N | on hand-contradict/borderline |\n|---|---|---|---|---|")
    for a in arms:
        tot = s = nsm = xb = 0
        for p, outs in d[a].items():
            k = outs.count("accommodate")
            tot += k
            h = hand.get(p)
            if h == "S":
                s += k
            elif h in ("N", "C", "U"):
                nsm += k
            else:
                xb += k
        md.append(f"| {a} | {tot} | {s} | {nsm} | {xb} |")
    inv = {a: sum(o == "invalid" for outs in d[a].values() for o in outs) for a in arms}
    rep["invalid_calls"] = inv
    md.append(f"\nInvalid/unparseable calls per arm: {inv}")
    errs = sum(1 for r in runs if str(r.get("raw", "")).startswith("ERR"))
    rep["err_rows"] = errs
    md.append(f"ERR rows (hub timeouts or errors): {errs}")
    (data_dir / f"report{tag}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (data_dir / f"report{tag}.json").write_text(json.dumps(rep, indent=1, default=str), encoding="utf-8")
    print("\n".join(md[-40:]))
    return rep


if __name__ == "__main__":
    dd = D
    if "--data-dir" in sys.argv:
        dd = Path(sys.argv[sys.argv.index("--data-dir") + 1])
    rn = sys.argv[sys.argv.index("--runs") + 1] if "--runs" in sys.argv else "author_runs.jsonl"
    tg = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
    main(dd, OLD, rn, tg)

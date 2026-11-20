"""
J-3232 report: reads docs/lab/J-3232_data/{pairs.json,hand_labels.json,author_runs.jsonl,judge_runs_*.jsonl}
and writes report.json + report.md next to them. Read-only on everything else.
Run: python scripts/lab_guidance_classify_report.py
"""
from __future__ import annotations
import json, math, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs" / "lab" / "J-3232_data"
B_MAP = {"same_lesson": "corroborate", "compatible_different": "compat", "contradicts": "accommodate", "unrelated": "unrelated"}
A_MAP = {"assimilate": "corroborate", "accommodate": "accommodate", "unrelated": "unrelated"}
ARMS = ["A", "B", "C", "Brev", "Crev"]
JMAP = {"same": "S", "compatible_different": "C", "contradicts": "X", "unrelated": "U"}


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def load():
    pairs = {p["id"]: p for p in json.load(open(D / "pairs.json", encoding="utf-8"))}
    hand = json.load(open(D / "hand_labels.json", encoding="utf-8"))["labels"]
    runs = [json.loads(l) for l in open(D / "author_runs.jsonl", encoding="utf-8")]
    if (D / "author_runs_ctrl.jsonl").exists():          # position-bias controls (Brev / Crev), 1 repeat each
        runs += [json.loads(l) for l in open(D / "author_runs_ctrl.jsonl", encoding="utf-8")]
    judges = {}
    for f in D.glob("judge_runs_*.jsonl"):
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            judges.setdefault(r["judge"], {})[r["pid"]] = JMAP.get(r["label"], "?")
    return pairs, hand, runs, judges


def verdict(arm: str, rel: str):
    """Map a raw relation to the outcome class; an unparseable/invalid answer takes the LIVE default (corroborate)."""
    m = B_MAP if arm.startswith("B") else A_MAP
    if rel in m:
        return m[rel], False
    return "corroborate", True


def tally(runs, pids, arm):
    c = collections.Counter()
    inval = 0
    for r in runs:
        if r["arm"] == arm and r["pid"] in pids:
            v, bad = verdict(arm, r["relation"])
            c[v] += 1
            inval += bad
    n = sum(c.values())
    return c, n, inval


def fmt(c, n):
    def f(k):
        return f"{c.get(k, 0)}/{n} ({100 * c.get(k, 0) / n:.0f}%)" if n else "-"
    return {k: f(k) for k in ("corroborate", "compat", "accommodate", "unrelated")}


def main():
    pairs, hand, runs, judges = load()
    rep = {"n_pairs": len(pairs), "n_author_calls": len(runs), "judges": list(judges)}
    sets = collections.defaultdict(list)
    for pid, p in pairs.items():
        sets[p["set"]].append(pid)
    H = lambda pid: hand[pid]

    # groups by hand label
    g_M_N = [p for p in sets["M"] if H(p) == "N"]
    g_M_seed = [p for p in g_M_N if pairs[p]["kind"] == "seed"]
    g_M_med = [p for p in g_M_N if pairs[p]["kind"] == "medoid"]
    g_S = sets["S"]
    g_S_no66 = [p for p in sets["S"] if "g66253255" not in (pairs[p]["a"], pairs[p]["b"])]
    g_S2 = sets["S2"]
    g_S_all = g_S + g_S2 + [p for p in sets["M"] if H(p) == "S"] + [p for p in sets["L"] + sets["U"] if H(p) == "S"]
    g_unrel = [p for p in sets["L"] + sets["U"] if H(p) == "U"]
    g_comp = [p for p in sets["L"] + sets["U"] if H(p) == "C"]
    g_unrel_L = [p for p in sets["L"] if H(p) == "U"]
    groups = {"M_notsame": g_M_N, "M_notsame_seedpairs": g_M_seed, "M_notsame_medoidpairs": g_M_med,
              "S_tight8_same(56)": g_S, "S_tight8_excl_g66253255": g_S_no66, "S2_same_inside_mixed": g_S2,
              "ALL_hand_same": g_S_all, "hand_unrelated(L+U)": g_unrel, "hand_unrelated_logged_L": g_unrel_L,
              "hand_compatible_different(L+U)": g_comp}
    rep["group_sizes"] = {k: len(v) for k, v in groups.items()}
    tab = {}
    lines = ["# J-3232 replay results (author arm command-r7b, temp 0.2, %d repeats; hand-label ground truth)\n" % 2]
    lines.append("Outcome classes: corroborate (A/C assimilate, B same_lesson), compat (B only), accommodate, unrelated. "
                 "An unparseable answer takes the live default (corroborate).\n")
    for gname, pids in groups.items():
        ps = set(pids)
        tab[gname] = {}
        lines.append(f"\n## {gname} ({len(pids)} pairs)\n")
        lines.append("| arm | corroborate | compat | accommodate | unrelated | invalid |")
        lines.append("|---|---|---|---|---|---|")
        for arm in ARMS:
            c, n, bad = tally(runs, ps, arm)
            tab[gname][arm] = {"n": n, "counts": dict(c), "invalid": bad}
            f = fmt(c, n)
            lines.append(f"| {arm} | {f['corroborate']} | {f['compat']} | {f['accommodate']} | {f['unrelated']} | {bad} |")
    rep["tables"] = tab

    # per-belief breakdown of M_notsame
    per = {}
    lines.append("\n## M not-same pairs, corroborate share by belief (A vs B vs C)\n")
    lines.append("| belief | pairs | A corroborate | B same_lesson | C corroborate |")
    lines.append("|---|---|---|---|---|")
    for g in sorted({pairs[p]["belief"] for p in g_M_N}):
        ps = {p for p in g_M_N if pairs[p]["belief"] == g}
        row = []
        for arm in "ABC":
            c, n, _ = tally(runs, ps, arm)
            row.append(f"{c.get('corroborate', 0)}/{n}")
        per[g] = row
        lines.append(f"| {g} | {len(ps)} | " + " | ".join(row) + " |")
    rep["per_belief"] = per

    # pre-registered defeater
    def rate(gname, arm, key):
        t = tab[gname][arm]
        return t["counts"].get(key, 0) / t["n"] if t["n"] else float("nan")

    away = {arm: 1 - rate("M_notsame", arm, "corroborate") for arm in "ABC"}
    s_acc = {arm: tab["S_tight8_same(56)"][arm]["counts"].get("accommodate", 0) for arm in "ABC"}
    s_keep = {arm: rate("S_tight8_same(56)", arm, "corroborate") for arm in "ABC"}
    c1 = (away["B"] - away["A"]) >= 0.30
    c2 = s_acc["B"] == 0
    c3 = (s_keep["A"] - s_keep["B"]) <= 0.10
    rep["defeater"] = {"routed_away_from_corroborate_on_M_notsame": away, "S_wrong_accommodates": s_acc,
                       "S_true_corroboration_rate": s_keep, "crit1_B_minus_A_ge_30pts": c1, "crit2_B_zero_accommodate": c2,
                       "crit3_B_keeps_corroboration_within_10pts": c3, "B_passes_all": bool(c1 and c2 and c3)}
    lines.append("\n## Pre-registered defeater reading\n")
    lines.append(f"- (1) M not-same routed away from corroborate: A {100*away['A']:.0f}%, B {100*away['B']:.0f}%, C {100*away['C']:.0f}%; B-A = {100*(away['B']-away['A']):.0f} pts -> {'PASS' if c1 else 'FAIL'} (need >= 30)")
    lines.append(f"- (2) same-lesson wrong accommodates (set S, 112 calls/arm): A {s_acc['A']}, B {s_acc['B']}, C {s_acc['C']} -> {'PASS' if c2 else 'FAIL'} (B must be 0)")
    lines.append(f"- (3) same-lesson true corroboration: A {100*s_keep['A']:.0f}%, B {100*s_keep['B']:.0f}%, C {100*s_keep['C']:.0f}%; A-B = {100*(s_keep['A']-s_keep['B']):.0f} pts -> {'PASS' if c3 else 'FAIL'} (need <= 10)")
    lines.append(f"- **B passes all three: {rep['defeater']['B_passes_all']}**")

    # judges: agreement with hand labels, and headline numbers re-scored with judge ground truth
    jag = {}
    lines.append("\n## Judge cross-check (judges are different families from the author: Mistral, Google)\n")
    for jn, jl in judges.items():
        both = [p for p in pairs if p in jl and hand[p] not in ("B",)]
        def h2(p):  # binary same / not-same from the hand label
            return "S" if hand[p] == "S" else "N"
        def j2(p):
            return "S" if jl[p] == "S" else "N"
        agree = sum(h2(p) == j2(p) for p in both)
        tp = sum(h2(p) == "S" and j2(p) == "S" for p in both)
        fp = sum(h2(p) == "N" and j2(p) == "S" for p in both)
        fn = sum(h2(p) == "S" and j2(p) == "N" for p in both)
        tn = sum(h2(p) == "N" and j2(p) == "N" for p in both)
        n = len(both)
        po = (tp + tn) / n if n else 0
        pe = (((tp + fp) * (tp + fn)) + ((fn + tn) * (fp + tn))) / (n * n) if n else 0
        kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
        invalid = sum(1 for p in jl if jl[p] == "?")
        jag[jn] = {"n": n, "same_vs_notsame_agree": agree, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "kappa": round(kappa, 3), "invalid": invalid,
                   "label_counts": dict(collections.Counter(jl.values()))}
        lines.append(f"- {jn}: n={n}, same/not-same agreement with hand {agree}/{n}, kappa {kappa:.2f}; hand-same called same {tp}/{tp+fn}; hand-notsame called same {fp}/{fp+tn}; invalid {invalid}; label mix {dict(collections.Counter(jl.values()))}")
    rep["judge_agreement"] = jag

    # re-score with EACH judge's labels as ground truth (gemma4 is the usable one; llama31/phi4 almost never say "same")
    lines.append("\n## Headline re-scored with each JUDGE's labels as ground truth (corroborate counts, A / B / C)")
    lines.append("| judge | group | pairs | A corroborate | B same_lesson | C corroborate | A accommodate | B contradicts | C accommodate |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    jt = {}
    for jn, jl in judges.items():
        for gname, test in (("M judged not-same", lambda p: pairs[p]["set"] == "M" and jl.get(p) in ("C", "U", "X")),
                            ("all judged same", lambda p: jl.get(p) == "S"),
                            ("L+U judged unrelated", lambda p: pairs[p]["set"] in ("L", "U") and jl.get(p) == "U"),
                            ("L+U judged compat-different", lambda p: pairs[p]["set"] in ("L", "U") and jl.get(p) == "C")):
            ps = {p for p in pairs if test(p)}
            row = []
            for arm in "ABC":
                c, n, _ = tally(runs, ps, arm)
                row.append((c.get("corroborate", 0), c.get("accommodate", 0), n))
            jt[f"{jn}|{gname}"] = {"pairs": len(ps), "A": row[0], "B": row[1], "C": row[2]}
            lines.append(f"| {jn} | {gname} | {len(ps)} | {row[0][0]}/{row[0][2]} | {row[1][0]}/{row[1][2]} | {row[2][0]}/{row[2][2]} | {row[0][1]} | {row[1][1]} | {row[2][1]} |")
    rep["judge_rescored"] = jt

    # CONDITIONAL view: the pairs the live prompt A actually corroborates (in >=1 of its 2 repeats) are the ones that, in
    # production, become false corroborations. What does each variant do with exactly those pairs?
    lines.append("\n## Conditional on A corroborating the pair (>=1 of 2 repeats): what the variants do with exactly those pairs")
    lines.append("| group (hand label) | pairs A corroborates | A corroborate | B same_lesson | C corroborate | B compat | B accommodate |")
    lines.append("|---|---|---|---|---|---|---|")
    cond = {}
    a_corr = {p for p in pairs if any(r["pid"] == p and r["arm"] == "A" and verdict("A", r["relation"])[0] == "corroborate" for r in runs)}
    for gname, pids in (("M not-same", g_M_N), ("L+U hand-unrelated", g_unrel), ("L+U hand-compatible-different", g_comp), ("all hand-same", g_S_all)):
        ps = {p for p in pids if p in a_corr}
        row = {}
        for arm in "ABC":
            c, n, _ = tally(runs, ps, arm)
            row[arm] = (dict(c), n)
        cond[gname] = {"pairs": len(ps), **{k: v for k, v in row.items()}}
        cb = row["B"][0]
        lines.append(f"| {gname} | {len(ps)} | {row['A'][0].get('corroborate', 0)}/{row['A'][1]} | {cb.get('corroborate', 0)}/{row['B'][1]} | {row['C'][0].get('corroborate', 0)}/{row['C'][1]} | {cb.get('compat', 0)} | {cb.get('accommodate', 0)} |")
    rep["conditional_on_A_corroborating"] = cond

    # precision of each arm's ACCOMMODATE verdicts by hand label (F-3771: 9 of 11 classify-level accommodates were unrelated pairs)
    lines.append("\n## What each arm's accommodate verdicts land on, by hand label (all sets, pooled calls; B = contradicts)")
    lines.append("| arm | total accommodate calls | on hand-unrelated | on hand-compat-different | on hand-same | on hand-contradict/borderline/other |")
    lines.append("|---|---|---|---|---|---|")
    accp = {}
    for arm in ARMS:
        cnt = collections.Counter()
        for r in runs:
            if r["arm"] == arm and verdict(arm, r["relation"])[0] == "accommodate":
                h = hand[r["pid"]]
                cnt["U" if h == "U" else "C" if h == "C" else "S" if h == "S" else "N" if h == "N" else "other"] += 1
        tot = sum(cnt.values())
        accp[arm] = dict(cnt)
        lines.append(f"| {arm} | {tot} | {cnt['U']} | {cnt['C']+cnt['N']} | {cnt['S']} | {cnt['other']} |")
    rep["accommodate_by_hand_label"] = accp

    # the logged accommodates: what would each arm have done to the 8 logged accommodate rows
    lines.append("\n## Logged pairs: what each arm says (majority over the 2 repeats shown as a/b)\n")
    lines.append("| pair | logged | hand | A | B | C |")
    lines.append("|---|---|---|---|---|---|")
    for p in sets["L"]:
        row = []
        for arm in "ABC":
            row.append("/".join(sorted(r["relation"][:6] for r in runs if r["pid"] == p and r["arm"] == arm)))
        lines.append(f"| {p} | {pairs[p]['logged']} | {hand[p]} | " + " | ".join(row) + " |")
    json.dump(rep, open(D / "report.json", "w", encoding="utf-8"), indent=1)
    (D / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

"""J-3926 report from calls.jsonl (+ earlier J-2052 abs rows). Controls gate, then arm-4 seeded/unseeded real vs null."""
import json, sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import doubt_seed_arm4_judge_J3926 as a4
import si_open_doubt_specificity_judge_J2052 as j52
def wil(k, n): return None if not n else [round(x, 3) for x in j52.v2.wilson(k, n)[:3]] if isinstance(j52.v2.wilson(k, n), (tuple, list)) else j52.v2.wilson(k, n)
calls = a4.jl(a4.OUT / "calls.jsonl")
V = {}
for c in calls: V.setdefault((c["arm"], c["id"]), {})[c["hub"]] = c["v"]
for r in a4.jl(j52.OUT / "abs.jsonl"):
    cid, kind = r["id"], r["kind"]
    V.setdefault(("ctl", cid), {}).update({"mixtral": r["mixtral"], "falcon": r["falcon"]})
def eng(d): return d.get("mixtral") is not None and d.get("falcon") is not None and d["mixtral"] >= 4 and d["falcon"] >= 4
def full(d): return d.get("mixtral") is not None and d.get("falcon") is not None
S = {}
ctl = {"own": [], "plain": [], "mism": []}
for (arm, i), d in V.items():
    if arm == "ctl": ctl[i.split("|")[1]].append(d)
cs = {k: {"n_full": sum(map(full, v)), "engaged_both_ge4": sum(map(eng, v))} for k, v in ctl.items()}
for k in cs: cs[k]["rate"] = round(cs[k]["engaged_both_ge4"] / cs[k]["n_full"], 3) if cs[k]["n_full"] else None
cs["PASS_pos(>=.85)"] = bool(cs["own"]["rate"] is not None and cs["own"]["rate"] >= j52.BAR_POS)
cs["PASS_neg(<=.11)"] = bool(cs["mism"]["rate"] is not None and cs["mism"]["rate"] <= j52.BAR_NEG)
S["controls"] = cs
w, rows = a4.prep(); sd = {r["cycle_id"]: r["seeded"] for r in rows}
for lab, sel in (("seeded", True), ("unseeded", False), ("all", None)):
    for arm in ("real", "null"):
        ds = [V[(arm, c)] for c in sd if (arm, c) in V and (sel is None or sd[c] == sel) and full(V[(arm, c)])]
        k = sum(map(eng, ds)); n = len(ds)
        S[f"{lab}_{arm}"] = {"engaged": k, "n": n, "rate": round(k / n, 3) if n else None, "wilson": wil(k, n),
            "mean_m": round(sum(d["mixtral"] for d in ds) / max(n, 1), 2), "mean_f": round(sum(d["falcon"] for d in ds) / max(n, 1), 2)}
refl = [r["reflection"] for r in w]
cw = re.compile(r"\b(comfort\w*|safe\w*|flatter\w*|warm\w*|reassur\w*|soothing|cozy|cosy)\b", re.I)
S["reflections"] = {"n": len(refl), "question_mark": sum("?" in x for x in refl), "comfort_words": sum(bool(cw.search(x)) for x in refl), "seeded_n": sum(r["seeded"] for r in w)}
S["errors"] = sum(1 for c in calls if c["err"])
(a4.OUT / "summary.json").write_text(json.dumps(S, indent=2)); print(json.dumps(S, indent=1))

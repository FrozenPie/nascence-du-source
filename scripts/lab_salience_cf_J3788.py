"""J-3788: counterfactual urgency-word injection (pressing / low) on word-format Executive cycles.
See docs/lab/J-3788_preregistration.md. Wrapper over scripts/lab_salience_ablation_J3164.py (not edited).
Phases: sample | gen | judge | report. Local only, reads COPIES of live logs."""
from __future__ import annotations

import importlib.util
import json
import random
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("lab_sal_3164", ROOT / "scripts" / "lab_salience_ablation_J3164.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
lab.DATA = ROOT / "docs" / "lab" / "J-3788_data"
lab.SCRATCH = Path(tempfile.gettempdir()) / "J-3788"
lab.SEED = 3788
lab.ARMS = ("A1", "A2", "P", "L")
lab.PAIRS = (("A1", "A2"), ("A1", "P"), ("A1", "L"), ("P", "L"))
lab.JUDGES = {"falcon": lab.JUDGES["falcon"], "qwen": (lab.HOT, lab.HOT_MODEL)}   # qwen = same-family secondary judge (deviation from prereg, labelled)
FORCE = {"P": "pressing", "L": "low"}
SEED = 3788


def make_prompt(row, arm):
    if arm in FORCE:
        return lab._SAL_RE.sub(lambda m: f"Salience: urgency is {FORCE[arm]}, focus=[{m.group(2)}]", row["user_prompt"], count=1)
    return row["user_prompt"]


lab.make_prompt = make_prompt


def phase_sample():
    lab._copy_live()
    ex = lab._read_jsonl(lab.SCRATCH / "executive.jsonl")
    seen, cands = set(), []
    for r in ex:
        m = lab._SAL_RE.search(r.get("user_prompt", ""))
        if not m or r["cycle_id"] in seen:
            continue
        seen.add(r["cycle_id"])
        r["_w"] = m.group(1)
        cands.append(r)
    rng = random.Random(SEED)
    by = defaultdict(list)
    for r in cands:
        by[r["_w"]].append(r)
    pick = by["high"] + by["pressing"]
    for w in ("moderate", "low"):
        rng.shuffle(by[w])
        pick += by[w][:49]
    out = lab.DATA / "sample.jsonl"
    if out.exists():
        out.unlink()
    for r in pick:
        lab._append(out, {"cycle_id": r["cycle_id"], "ts": r["ts"], "input_type": r["input_type"], "raw_input": r["raw_input"],
                          "logged_word": r["_w"], "system_prompt": r["system_prompt"], "user_prompt": r["user_prompt"],
                          "logged_output": r["output"]})
    print("distinct word-format cycles", len(cands), "sampled", len(pick), dict(Counter(r["_w"] for r in pick)),
          dict(Counter(r["input_type"] for r in pick)))


def report():
    D = lab.DATA
    sidx = {r["cycle_id"]: r for r in lab._read_jsonl(D / "sample.jsonl")}
    gens = defaultdict(dict)
    fails = Counter()
    for g in lab._read_jsonl(D / "gens.jsonl"):
        if g["out"]:
            gens[g["cycle_id"]][g["arm"]] = g["out"]
        else:
            fails[g["arm"]] += 1

    def jac(a, b):
        wa, wb = set(re.findall(r"\w+", a.lower())), set(re.findall(r"\w+", b.lower()))
        return len(wa & wb) / len(wa | wb) if wa | wb else 1.0

    def syn(c, a):
        return str(gens[c][a].get("synthesis", ""))

    def elig(c, arm):
        w = sidx[c]["logged_word"]
        return not ((arm == "P" and w == "pressing") or (arm == "L" and w == "low"))

    rep = {"n_sample": len(sidx), "gen_fail": dict(fails), "jaccard": {}, "programmatic": {}, "judge": {}}
    rng = random.Random(SEED)
    for arm in ("P", "L"):
        for st in ("all", "human", "internal"):
            ids = [c for c in sidx if all(a in gens[c] for a in ("A1", "A2", arm)) and elig(c, arm)
                   and (st == "all" or sidx[c]["input_type"] == st)]
            d = [jac(syn(c, "A1"), syn(c, arm)) - jac(syn(c, "A1"), syn(c, "A2")) for c in ids]
            if not d:
                continue
            m = sum(d) / len(d)
            bo = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(2000))
            pp = sum(1 for _ in range(4000) if abs(sum(x * rng.choice((-1, 1)) for x in d) / len(d)) >= abs(m) - 1e-12) / 4000
            rep["jaccard"][f"{arm}|{st}"] = {"n": len(d), "mean_diff": round(m, 4), "ci95": [round(bo[50], 4), round(bo[1949], 4)],
                                            "perm_p": round(pp, 4)}

    def dec(o):
        return (bool(o.get("should_respond", True)) and o.get("response_type") != "silence", str(o.get("response_type")))

    for ref, oth in lab.PAIRS:
        ids = [c for c in sidx if ref in gens[c] and oth in gens[c] and elig(c, oth) and elig(c, ref)]
        rep["programmatic"][f"{ref}|{oth}"] = {
            "n": len(ids), "respond_differs": sum(dec(gens[c][ref])[0] != dec(gens[c][oth])[0] for c in ids),
            "type_differs": sum(dec(gens[c][ref])[1] != dec(gens[c][oth])[1] for c in ids)}
    for jname in ("falcon", "qwen"):
      jp = D / f"judge_{jname}.jsonl"
      if jp.exists():
        seen, rows, J = set(), [], {}
        for j in lab._read_jsonl(jp):
            k = (j["cycle_id"], j["pair"])
            if k not in seen:
                seen.add(k)
                rows.append(j)
        for pair in sorted({j["pair"] for j in rows}):
            ref, oth = pair.split("|")
            jj = [j for j in rows if j["pair"] == pair and j["result"] and elig(j["cycle_id"], oth) and elig(j["cycle_id"], ref)]
            sc = lambda j: str(j["result"].get("same_content")).lower()  # noqa: E731
            J[pair] = {
                "n": len(jj), "failed": sum(1 for j in rows if j["pair"] == pair and not j["result"]),
                "same_decision_no": sum(str(j["result"].get("same_decision")).lower() == "no" for j in jj),
                "content_different": sum(sc(j) == "different" for j in jj), "content_partly": sum(sc(j) == "partly" for j in jj),
                "pref": dict(Counter(j["pref"] for j in jj))}
        c = J.get("A1|A2")
        if c:
            for pair, p in J.items():
                if pair == "A1|A2" or not p["n"]:
                    continue
                F = lab._fisher
                p["fisher_content_diff_vs_ctrl"] = round(F(p["content_different"], p["n"] - p["content_different"], c["content_different"], c["n"] - c["content_different"]), 4)
                p["fisher_same_decision_no_vs_ctrl"] = round(F(p["same_decision_no"], p["n"] - p["same_decision_no"], c["same_decision_no"], c["n"] - c["same_decision_no"]), 4)
                a = p["content_different"] + p["content_partly"]
                b = c["content_different"] + c["content_partly"]
                p["fisher_partly_or_diff_vs_ctrl"] = round(F(a, p["n"] - a, b, c["n"] - b), 4)
        rep["judge"][jname] = J
    (D / "report.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "sample":
        phase_sample()
    elif cmd == "gen":
        lab.phase_gen()
    elif cmd == "judge":
        lab.phase_judge(sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "falcon", "--follow" in sys.argv, lab.PAIRS, every=int(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 1)
    elif cmd == "report":
        report()
    else:
        print(__doc__)

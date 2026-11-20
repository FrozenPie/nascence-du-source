"""J-2996 step 3: score the replay against the blind gold labels.  Reads docs/lab/J-2996_data/{gold_*,replay_results.jsonl}.

Metrics per variant (binary: gold advance = label A; non-advance = R or T):
  coverage        decided rulings / all (a split_no_tiebreak or unavailable verdict is None, not a pass)
  pass rate       share of decided rulings that say advances=true (all labelled pairs)
  agreement       decided rulings that match the gold, overall and with the 12 labeler-unsure items dropped
  false-keep      gold non-advance that the variant passes   (the failure F-3692 names)
  false-reject    gold advance that the variant refuses      (the price of a stricter prompt)
  keep rate       share of the 60 panel-CONFIRMED sample pairs the variant still passes (what fraction of currently confirmed
                  advances it would keep); plus the same on the unlabelled extra confirmed sample if it was run
  per-judge       the same agreement for each judge's own vote (v1 gemma4:12b, v2 falcon3:7b)
  kappa           Cohen's kappa of the panel verdict vs gold on decided items
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "lab" / "J-2996_data"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
VARIANTS = ("V0", "V1", "V2", "V3")


def wilson(k: int, n: int, z: float = 1.96) -> "tuple[float, float]":
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def fmt(k: int, n: int) -> str:
    if n == 0:
        return "n/a (0)"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.0f}% [{100 * lo:.0f}-{100 * hi:.0f}]"


def kappa(pairs: list) -> float:
    """pairs of (pred_bool, gold_bool)"""
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(1 for p, g in pairs if p == g) / n
    pp = sum(1 for p, _ in pairs if p) / n
    pg = sum(1 for _, g in pairs if g) / n
    pe = pp * pg + (1 - pp) * (1 - pg)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def load(prefix: str = "replay_single"):
    gold = {}
    for l in open(DATA / "gold_pairs.jsonl", encoding="utf-8"):
        r = json.loads(l)
        gold[r["gid"]] = r
    labs = json.load(open(DATA / "gold_labels.json", encoding="utf-8"))["labels"]
    for g, r in gold.items():
        r["gold"], r["unsure"] = labs[g]["label"], labs[g]["unsure"]
    res = defaultdict(dict)       # variant -> gid -> row (last non-excluded wins)
    for p in sorted(DATA.glob(f"{prefix}*.jsonl")):
        for l in open(p, encoding="utf-8"):
            try:
                d = json.loads(l)
            except Exception:
                continue
            if d.get("infra_excluded"):
                continue
            res[d["variant"]][d["gid"]] = d
    return gold, res


def score(gold: dict, res: dict) -> str:
    out = []
    A = lambda g: gold[g]["gold"] == "A"
    for v in VARIANTS:
        rows = {g: r for g, r in res.get(v, {}).items() if g in gold}
        dec = {g: r for g, r in rows.items() if r.get("verdict") is not None}
        out.append(f"\n### {v}")
        out.append(f"- rulings {len(rows)} of {len(gold)} labelled; decided {fmt(len(dec), len(rows))}; "
                   f"how {dict(Counter(r.get('how') for r in rows.values()))}")
        if not dec:
            continue
        pas = sum(1 for r in dec.values() if r["verdict"])
        out.append(f"- pass rate (all labelled, decided): {fmt(pas, len(dec))}")
        ok = sum(1 for g, r in dec.items() if r["verdict"] == A(g))
        out.append(f"- agreement with gold: {fmt(ok, len(dec))}")
        sure = {g: r for g, r in dec.items() if not gold[g]["unsure"]}
        out.append(f"- agreement, labeler-unsure items dropped: {fmt(sum(1 for g, r in sure.items() if r['verdict'] == A(g)), len(sure))}")
        na = {g: r for g, r in dec.items() if not A(g)}
        a = {g: r for g, r in dec.items() if A(g)}
        out.append(f"- FALSE-KEEP (gold non-advance passed): {fmt(sum(1 for r in na.values() if r['verdict']), len(na))}"
                   f"   [restate R: {fmt(sum(1 for g, r in na.items() if gold[g]['gold'] == 'R' and r['verdict']), sum(1 for g in na if gold[g]['gold'] == 'R'))}"
                   f"; tour T: {fmt(sum(1 for g, r in na.items() if gold[g]['gold'] == 'T' and r['verdict']), sum(1 for g in na if gold[g]['gold'] == 'T'))}]")
        out.append(f"- FALSE-REJECT (gold advance refused): {fmt(sum(1 for r in a.values() if not r['verdict']), len(a))}")
        conf = {g: r for g, r in dec.items() if gold[g]["source"] == "confirmed"}
        out.append(f"- KEEP RATE on the panel-confirmed sample: {fmt(sum(1 for r in conf.values() if r['verdict']), len(conf))}")
        pend = {g: r for g, r in dec.items() if gold[g]["source"] == "pending"}
        out.append(f"- pass rate on the not-yet-judged pending items: {fmt(sum(1 for r in pend.values() if r['verdict']), len(pend))}")
        out.append(f"- kappa(panel, gold) = {kappa([(r['verdict'], A(g)) for g, r in dec.items()]):.2f}")
        for jn, key in (("gemma4:12b v1", "v1"), ("falcon3:7b v2", "v2")):
            d1 = {g: r for g, r in rows.items() if r.get(key) is not None}
            out.append(f"- judge {jn}: says yes {fmt(sum(1 for r in d1.values() if r[key]), len(d1))}; "
                       f"agrees with gold {fmt(sum(1 for g, r in d1.items() if r[key] == A(g)), len(d1))}")
    # paired change vs V0
    out.append("\n### paired change vs V0 (decided in both)")
    for v in VARIANTS[1:]:
        both = [g for g in res.get("V0", {}) if g in res.get(v, {}) and g in gold
                and res["V0"][g].get("verdict") is not None and res[v][g].get("verdict") is not None]
        flips_down = [g for g in both if res["V0"][g]["verdict"] and not res[v][g]["verdict"]]
        flips_up = [g for g in both if not res["V0"][g]["verdict"] and res[v][g]["verdict"]]
        good_down = sum(1 for g in flips_down if not A(g))
        bad_down = sum(1 for g in flips_down if A(g))
        out.append(f"- {v}: n={len(both)}; pass->fail {len(flips_down)} (of which correct, gold non-advance: {good_down}; "
                   f"wrong, gold advance lost: {bad_down}); fail->pass {len(flips_up)}")
    # extra unlabelled keep-rate sample
    xs = defaultdict(dict)
    for v in VARIANTS:
        for g, r in res.get(v, {}).items():
            if g.startswith("X") and r.get("verdict") is not None:
                xs[v][g] = r
    if any(xs.values()):
        out.append("\n### keep rate on the extra UNLABELLED panel-confirmed sample")
        for v in VARIANTS:
            out.append(f"- {v}: {fmt(sum(1 for r in xs[v].values() if r['verdict']), len(xs[v]))}")
    return "\n".join(out)


def main() -> int:
    prefix = sys.argv[1] if len(sys.argv) > 1 else "replay_single"      # replay_single (gemma4:12b alone) | replay_results (panel)
    gold, res = load(prefix)
    print(f"source files: {prefix}*.jsonl")
    print(f"gold {len(gold)} pairs: {dict(Counter(r['gold'] for r in gold.values()))}; "
          f"by source {dict(Counter((r['source'], r['gold']) for r in gold.values()))}")
    print(score(gold, res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

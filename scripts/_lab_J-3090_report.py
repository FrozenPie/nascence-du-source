"""J-3090: summarise the grade runs in docs/lab/J-3090_data/ against the gate (precision >= 0.8 on >= 30 graded rejections).

Reads grades_*.jsonl (written by scripts/_lab_J-3090_regrade.py) and hand_labels.json; prints a table. Read-only.
  python scripts/_lab_J-3090_report.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from critic_grade import wilson  # noqa: E402

D = ROOT / "docs" / "lab" / "J-3090_data"
COUPLED = ("gemma",)   # the critic's own family: reported as a control, never counted toward the gate


def _load(p: Path) -> dict:
    rec = json.loads(p.read_text(encoding="utf-8").splitlines()[-1])
    return rec


def _line(name: str, k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"  {name:34} {k:>3}/{n:<3} = {k / n:5.2f}  (95% CI {lo:.2f}-{hi:.2f})" if n else f"  {name:34} n=0"


def main() -> None:
    hand = json.loads((D / "hand_labels.json").read_text(encoding="utf-8"))["labels"]
    by_key = {(round(h["ts"], 3), h["check"]): h["label"] for h in hand}
    print("== hand labels (Claude, INFERRED): W warranted / N not / U uncertain ==")
    c = Counter(h["label"] for h in hand)
    n = len(hand)
    print(_line("strict (W only)", c["W"], n))
    print(_line("lenient (W + U)", c["W"] + c["U"], n))
    bycheck: dict[str, Counter] = {}
    for h in hand:
        bycheck.setdefault(h["check"], Counter())[h["label"]] += 1
    for ck, cc in sorted(bycheck.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"    {ck:26} W{cc['W']} U{cc['U']} N{cc['N']}  of {sum(cc.values())}")
    for p in sorted(D.glob("grades_*.jsonl")):
        rec = _load(p)
        model = rec.get("judge_model", p.stem) + " task=" + rec.get("task", "emissary")
        tag = "COUPLED control (critic's own family) - not for the gate" if any(m in model for m in COUPLED) else "decoupled grader"
        print(f"\n== {model} ({tag}), per flag ==")
        g = rec["grades"]
        print(_line("precision (warranted)", rec["warranted"], rec["n"]))
        bc: dict[str, list[int]] = {}
        for x in g:
            bc.setdefault(x["check"], [0, 0])
            bc[x["check"]][1] += 1
            bc[x["check"]][0] += 1 if x["warranted"] else 0
        for ck, (k, t) in sorted(bc.items(), key=lambda kv: -kv[1][1]):
            print(f"    {ck:26} {k}/{t}")
        agree = both_w = 0
        m = 0
        for x in g:
            lab = by_key.get((round(x["ts"], 3), x["check"]))
            if lab in ("W", "N"):
                m += 1
                agree += 1 if (lab == "W") == x["warranted"] else 0
                both_w += 1 if (lab == "W" and x["warranted"]) else 0
        print(f"  agreement with my W/N labels (U excluded): {agree}/{m}; both-warranted: {both_w}")
        post = [x for x in g if x["ts"] >= 1787295000]   # first decomposed_critic row in llm_latency.jsonl (08-21 UTC): the decoupled-regime window
        k = sum(1 for x in post if x["warranted"])
        print(_line("subset in the latency-joinable window", k, len(post)))
    print("\nGATE: precision >= 0.8 on >= 30 graded rejections AND F-3428/J-2679 shipped.")


if __name__ == "__main__":
    main()

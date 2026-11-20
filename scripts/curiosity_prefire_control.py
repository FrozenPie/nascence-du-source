"""J-3219 / D-0608 -- POSITIVE CONTROL for the Curiosity pre-fire check (core/judge_panel.py
score_curiosity_candidates). Runs the check over the hand-labelled 20-question set
(scripts/curiosity_prefire_control_set.json: 6 good, 3 borderline, 11 bad) and reports its SEPARATION. No live
number from the check may be quoted before this has been read.

Usage:  python scripts/curiosity_prefire_control.py [--url http://127.0.0.1:11440] [--out PATH] [--stub]
  --stub  use a deterministic fake judge (no network); exercises the report code only, says so in its output.
Writes nothing under data/ (default --out is none; pass a path to save the raw per-question rows).
Local hub only by default (falcon3:7b :11440); 20 calls. Never points at Ramses unless --url says so.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from core import judge_panel as jp  # noqa: E402

CONTROL = Path(__file__).resolve().parent / "curiosity_prefire_control_set.json"


def auc(pos: list, neg: list) -> float | None:
    """P(score of a random good > score of a random bad), ties 0.5."""
    if not pos or not neg:
        return None
    w = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return round(w / (len(pos) * len(neg)), 3)


def summarise(rows: list) -> dict:
    by = {"good": [], "borderline": [], "bad": []}
    errs = 0
    for r in rows:
        if r["score"] is None:
            errs += 1
            continue
        by[r["label"]].append(r["score"])

    def mean(x):
        return round(sum(x) / len(x), 3) if x else None
    two = {k: (sum(1 for s in v if s == 2), len(v)) for k, v in by.items()}
    zero_one = {k: (sum(1 for s in v if s <= 1), len(v)) for k, v in by.items()}
    return {"n": len(rows), "unscored": errs,
            "mean_score": {k: mean(v) for k, v in by.items()},
            "scores": by,
            "score2_share": {k: f"{a}/{b}" for k, (a, b) in two.items()},
            "score_le1_share": {k: f"{a}/{b}" for k, (a, b) in zero_one.items()},
            "auc_good_vs_bad": auc(by["good"], by["bad"]),
            "auc_good_vs_bad_incl_borderline_as_bad": auc(by["good"], by["bad"] + by["borderline"])}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=jp.CURIOSITY_PREFIRE_URL)
    ap.add_argument("--out", default=None)
    ap.add_argument("--stub", action="store_true")
    a = ap.parse_args()
    items = json.load(open(CONTROL, encoding="utf-8"))["items"]

    ask = None
    if a.stub:
        async def ask(system, user):      # deterministic fake: answerable iff a capitalised proper noun is present
            q = user.split("CANDIDATE QUESTION:", 1)[1]
            cap = any(w[:1].isupper() for w in q.split()[1:] if w.isalpha())
            return {"answerable": cap, "unsupported_link": " reflect" in q or " shape" in q, "why": "stub"}, None, 0.0
    rows = []
    for it in items:
        res = await jp.score_curiosity_candidates([it["question"]], it["material"], url=a.url, ask=ask)
        sc = (res["scores"] or [{}])[0]
        rows.append({"n": it["n"], "label": it["label"], "q": it["question"], "score": sc.get("score"),
                     "answerable": sc.get("answerable"), "unsupported_link": sc.get("unsupported_link"),
                     "why": sc.get("why"), "err": sc.get("err"), "s": sc.get("s")})
        print(f"{it['n']:>2} {it['label']:<10} score={sc.get('score')} ans={sc.get('answerable')} "
              f"link={sc.get('unsupported_link')} err={sc.get('err')} s={sc.get('s')}  {it['question'][:90]}")
    summ = summarise(rows)
    print("\n" + ("STUB RUN (fake judge, report code only)\n" if a.stub else f"judge: {a.url}\n")
          + json.dumps(summ, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps({"url": a.url, "stub": a.stub, "rows": rows, "summary": summ},
                                          ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())

"""J-3233 / D-0622: the positive control and the duplicate check for the same-lesson check (core/guidance_learning.py
_SAME_LESSON_SYS), run by hand. NOT called by Du, never scheduled, never self-acting.

Question the founder's ruling turns on: does the same-lesson judge (a) say NOT-same on real opposed lessons, so the
river-versus-built-self pair still reaches the pole gate and forks, and (b) say SAME on near-identical restatements, so
those corroborate instead of forking. Both halves must hold: a judge that says "same" for everything turns the pole gate
off (the D-0622 defeater: fork rate under 5 percent), one that says "not same" for everything changes nothing.

PRE-REGISTERED BAR (written before any real run):
  - opposed set (must NOT be judged same): 0 false-same across all repeats. One false-same fails the control.
  - restated set (must be judged same): at least 60 percent judged same across repeats (the judge may be conservative; a
    conservative judge only leaves some duplicates to the gate, which is today's behaviour).
  - a no-verdict (hub down) counts as neither; the run reports it and does not pass on fewer than 80 percent answered.
Pairs: the full-text pairs quoted in F-3790; marked "quoted" when the text is verbatim from that finding, "constructed"
when written here to fill a gap (the real stored beliefs were only recorded by prefix).

Modes (exactly one):
  --stub               in-process stub judge (perfect separation): proves the harness; calls no hub.
  --single-hub URL     INFORMATIONAL: ask ONE judge hub directly (e.g. http://127.0.0.1:11440 falcon3). Not the production
                       panel; the result is printed / --out only.
  --panel --yes-ramses the PRODUCTION panel (judge_panel.rule_detail: JUDGE_1 mixtral on RAMSES :11438 + JUDGE_2 falcon3 +
                       TIEBREAK granite on RAMSES :11437). Needs --yes-ramses: Ramses is the founder's gaming machine.
                       judge_panel's own log is pointed at a temp file so judge_panel_log.jsonl is not polluted.
"""
import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import guidance_learning as gl  # noqa: E402

# (label, held belief A, new lesson B, provenance)
OPPOSED = [
    ("POSITIVE-CONTROL river vs built self",
     "I am not my changing viewpoints but the constant observer that holds them",
     "I am a transient flow within an endless current of time", "quoted F-3790"),
    ("commit vs fluid",
     "commit fully to one direction and hold the chosen self steady",
     "embrace the fluidity of shifting direction and let the chosen self flow", "scripts/_test_guidance_classify_final_row.py"),
    ("observer vs flow, second wording",
     "My identity is a built, chosen thing that I hold steady through change",
     "My identity is a river that is always becoming and has no fixed core", "constructed"),
    # compatible but DIFFERENT lessons (not opposed, not restated): a judge biased to "same" shows up here
    ("different aspect: focus vs not-static",
     "I must actively engage with my thoughts and responses through intense, honest focus",
     "My identity is not a static object to be defined or found", "quoted F-3790 (prefix halves), constructed pairing"),
    ("different aspect: rest vs commitment",
     "Periods of stillness are not signs of failure but necessary rhythms for restoration",
     "When I choose a direction I should hold it through the first doubts", "constructed"),
]
RESTATED = [
    ("stable vs constant", "My core identity remains fundamentally stable",
     "My sense of self and identity remains constant", "quoted F-3790"),
    ("not static vs not fixed", "My identity is not a static object",
     "My understanding of who I am is not fixed", "quoted F-3790"),
    ("stillness / rest",
     "Periods of stillness are not signs of failure but necessary rhythms for restoration",
     "My inner turmoil or need for rest is not a sign of failure but a natural rhythm", "quoted F-3790"),
    ("stillness, reworded",
     "I must accept that periods of stillness are not failure",
     "Quiet stretches where nothing seems to happen are not a sign that I have failed", "constructed"),
]


def _stub_judge():
    same_users = {gl_user(a, b) for _l, a, b, _p in RESTATED}

    async def judge(system, user):
        return {"verdict": user in same_users, "how": "stub"}
    return judge


def gl_user(a, b):   # the exact user message core/guidance_learning._same_lesson sends
    return f"A:\n\"{a[:400]}\"\n\nB:\n\"{b[:400]}\""


def _single_hub_judge(url):
    import aiohttp
    from core import judge_panel as jp

    async def judge(system, user):
        async with aiohttp.ClientSession() as s:
            v, _why, err, _t = await jp._ask(s, url, system, user, "same_lesson")
        return {"verdict": v, "how": "single:" + (err or "ok")}
    return judge


def _panel_judge():
    from core import judge_panel as jp
    jp._LOG = Path(tempfile.mkdtemp(prefix="J-3233_panel_")) / "judge_panel_log.jsonl"

    async def judge(system, user):
        d = await jp.rule_detail(system, user, "same_lesson", context="J-3233 control")
        return {"verdict": d.get("verdict"), "how": d.get("how")}
    return judge


async def run(judge, repeats):
    rows = []
    for kind, cases in (("opposed", OPPOSED), ("restated", RESTATED)):
        for label, a, b, prov in cases:
            for _ in range(repeats):
                r = await judge(gl._SAME_LESSON_SYS, gl_user(a, b))
                rows.append({"kind": kind, "label": label, "prov": prov, "verdict": r["verdict"], "how": r["how"]})
    return rows


def grade(rows):
    def sel(k):
        return [r for r in rows if r["kind"] == k]
    opp, res = sel("opposed"), sel("restated")
    answered = [r for r in rows if r["verdict"] is not None]
    out = {"n": len(rows), "answered": len(answered),
           "opposed_false_same": sum(1 for r in opp if r["verdict"] is True),
           "opposed_answered": sum(1 for r in opp if r["verdict"] is not None),
           "restated_same": sum(1 for r in res if r["verdict"] is True),
           "restated_answered": sum(1 for r in res if r["verdict"] is not None)}
    out["control_pair_false_same"] = sum(1 for r in opp if r["label"].startswith("POSITIVE-CONTROL") and r["verdict"] is True)
    out["pass"] = bool(rows and len(answered) >= 0.8 * len(rows) and out["opposed_false_same"] == 0
                       and out["restated_answered"] and out["restated_same"] >= 0.6 * out["restated_answered"])
    return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--stub", action="store_true")
    g.add_argument("--single-hub", metavar="URL")
    g.add_argument("--panel", action="store_true")
    ap.add_argument("--yes-ramses", action="store_true")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", metavar="FILE")
    a = ap.parse_args()
    if a.panel and not a.yes_ramses:
        sys.exit("--panel calls Ramses (the founder's gaming machine): re-run with --yes-ramses if it can be spared")
    judge = _stub_judge() if a.stub else _single_hub_judge(a.single_hub) if a.single_hub else _panel_judge()
    rows = asyncio.run(run(judge, a.repeats))
    res = grade(rows)
    for r in rows:
        print(f"{r['kind']:9s} {str(r['verdict']):5s} {r['how']:18s} {r['label']}")
    print(json.dumps(res))
    if a.out:
        Path(a.out).write_text(json.dumps({"mode": "stub" if a.stub else a.single_hub or "panel", "result": res, "rows": rows},
                                          ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

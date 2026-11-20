"""J-3211 / D-0600: run the positive control for the guidance behaviour-delta judge (core/guidance_behavior_control.py).

NOT called by Du, never scheduled, never self-acting: a person or a lab job runs it by hand when Du's judge hubs can be
spared. 32 cases (8 real principles x enacted/echoed/ignored_topical/ignored_unrelated) x --repeats (default 3).

Modes (exactly one):
  --stub               in-process stub judge (perfect separation); proves the harness, calls no hub, writes no gate.
  --single-hub URL     INFORMATIONAL: ask ONE judge hub directly (e.g. http://127.0.0.1:11440 falcon3). Not the
                       production panel, so it can never open the gate; the result is printed / --out only.
  --panel --yes-ramses the PRODUCTION panel (judge_panel.rule_detail: JUDGE_1 mixtral on RAMSES :11438 + JUDGE_2
                       falcon3 + TIEBREAK granite on RAMSES :11437). Needs --yes-ramses because Ramses is the founder's
                       gaming machine: 32 x 3 x 2 = 192+ calls to it at the default repeats. With --record it writes
                       data/guidance_behavior_judge_control.json (the gate the HUD label reads). judge_panel's own
                       log is pointed at a temp file for the run so judge_panel_log.jsonl is not polluted.
Run it from the checkout whose data/ you mean (the gate file lives in that tree's data/).
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
from core import guidance_behavior_control as gc  # noqa: E402
from core import guidance_behavior_judge as gbj  # noqa: E402


def _stub_judge():
    cls_of = {gbj.build_user(c["principle"], c["thought"]): c["cls"] for c in gc.CASES}

    async def judge(system, user, ctx):
        return {"verdict": cls_of.get(user) == "enacted", "how": "agreed"}
    return judge


def _single_hub_judge(url):
    import aiohttp
    from core import judge_panel as jp

    async def judge(system, user, ctx):
        async with aiohttp.ClientSession() as s:
            v, _why, err, _t = await jp._ask(s, url, system, user, "aligns")
        return {"verdict": v, "how": "single:" + (err or "ok")}
    return judge


def _panel_judge():
    from core import judge_panel as jp
    jp._LOG = Path(tempfile.mkdtemp(prefix="J-3211_panel_")) / "judge_panel_log.jsonl"   # keep the live panel log clean

    async def judge(system, user, ctx):
        d = await jp.rule_detail(system, user, "aligns", context=ctx)
        return {"verdict": d.get("verdict"), "how": d.get("how")}
    return judge


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--stub", action="store_true")
    g.add_argument("--single-hub", metavar="URL")
    g.add_argument("--panel", action="store_true")
    ap.add_argument("--yes-ramses", action="store_true", help="required for --panel: it calls Ramses hubs")
    ap.add_argument("--record", action="store_true", help="with --panel: write the gate file")
    ap.add_argument("--repeats", type=int, default=gc.REPEATS)
    ap.add_argument("--out", help="write the full result JSON here")
    a = ap.parse_args()
    if a.record and not a.panel:
        ap.error("--record only applies to --panel (the production panel is the only run that can open the gate)")
    if a.panel and not a.yes_ramses:
        ap.error("--panel calls Ramses hubs (the founder's gaming machine); pass --yes-ramses to confirm it is spare")
    judge = _stub_judge() if a.stub else _panel_judge() if a.panel else _single_hub_judge(a.single_hub)
    res = asyncio.run(gc.run_control(judge, repeats=a.repeats))
    mode = "stub" if a.stub else "panel" if a.panel else "single-hub " + a.single_hub
    print(f"mode: {mode} · {res['n_cases']} cases x {res['repeats']} repeats · coverage {res['coverage']}")
    print("true-rate by class:", json.dumps(res["rates"]))
    print("how:", json.dumps(res["how"]))
    print("PASSED" if res["passed"] else "FAILED: " + "; ".join(res["failed"]))
    if a.out:
        Path(a.out).write_text(json.dumps({"mode": mode, **res}, indent=1), encoding="utf-8")
    if a.record:
        p = gc.record_result(res, gbj._panel_now(), gbj.prompt_fingerprint())
        print("gate file written:", p)
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

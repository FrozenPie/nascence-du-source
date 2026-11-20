"""Hermetic test for J-4012 (D-0743, F-4697): pursuit close judge prompt_v "v3" (trajectory + 3-way verdict), flag V3_PROMPT.
Run: python scripts/_test_J-4012_pursuit_close_v3.py   (from the tree under test).  Synthetic pursuits only."""
from __future__ import annotations
import asyncio, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.pursuit_close_shadow as pcs
import core.done_when as dw
import core.judge_panel as jp
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True


def check(n, c):
    global ok_all
    ok_all = ok_all and bool(c)
    print(f"  [{'PASS' if c else 'FAIL'}] {n}")


calls = []
ANS = {"resolved": False, "answered": False, "partly": False, "settled": False}


async def fake(system, user, key, context="", **k):
    calls.append((key, system, user, context))
    return {"verdict": ANS[key], "how": "agreed", "why": "t"}
jp.rule_detail = fake


def P(i, **kw):
    d = {"id": i, "question": "scene " + i, "standing": "latest-" + i, "open": "Why is it full?",
         "thoughts": [f"t{n}" for n in range(1, 9)], "advances": 40, "status": "saturated"}
    d.update(kw)
    return d


with isolate(db="empty"):
    tmp = Path(tempfile.mkdtemp(prefix="J-4012_"))
    pcs.SHADOW_LOG = tmp / "pcs.jsonl"
    dw.STORE = tmp / "done_when.jsonl"
    assert "Nascence\\data" not in str(pcs.SHADOW_LOG)

    print("[1] flag off: v2 exactly as before, one call, no trajectory")
    check("V3_PROMPT default True (D-0786, 2026-11-16)", pcs.V3_PROMPT is True)
    pcs.V3_PROMPT = False   # the default is now True; set it off for the v2 section
    asyncio.run(pcs.ask(P("a")))
    r = pcs._read()[-1]
    check("one call, key resolved, v2, no verdict3", len(calls) == 1 and calls[0][0] == "resolved"
          and r["prompt_v"] == "v2" and "verdict3" not in r and "TRAJECTORY" not in calls[0][2])

    print("[2] flag on: trajectory = last 6 thoughts oldest first, before STANDING")
    pcs.V3_PROMPT = True
    calls.clear()
    sysm, usr, f = pcs.build_prompt(P("b"))
    check("v3 fields", f["prompt_v"] == "v3" and f["trajectory"] == ["t3", "t4", "t5", "t6", "t7", "t8"])
    check("trajectory block ordered, before standing",
          usr.index("TRAJECTORY") < usr.index("1. t3") < usr.index("6. t8") < usr.index("ITS STANDING POSITION: latest-b"))
    check("t2 dropped (only last 6 kept)", "2. t2" not in usr and "1. t3" in usr)
    check("no thoughts -> no TRAJECTORY block", "TRAJECTORY" not in pcs.build_prompt(P("c", thoughts=[]))[1])

    print("[3] 3-way verdicts")
    ANS.update(answered=True, partly=False, settled=True)
    calls.clear(); asyncio.run(pcs.ask(P("ans"))); r = pcs._read()[-1]
    check("answered: would_resolve, partly False, settled, partly not asked",
          r["verdict3"] == "answered" and r["would_resolve"] is True and r["partly"] is False and r["settled"] is True
          and [c[0] for c in calls] == ["answered", "settled"] and r["prompt_v"] == "v3")
    ANS.update(answered=False, partly=True, settled=False)
    calls.clear(); asyncio.run(pcs.ask(P("par"))); r = pcs._read()[-1]
    check("partly: would_resolve False, partly True, three calls",
          r["verdict3"] == "partly" and r["would_resolve"] is False and r["partly"] is True and r["settled"] is False
          and [c[0] for c in calls] == ["answered", "partly", "settled"])
    ANS.update(answered=False, partly=False, settled=True)
    calls.clear(); asyncio.run(pcs.ask(P("nyet"))); r = pcs._read()[-1]
    check("not_yet", r["verdict3"] == "not_yet" and r["would_resolve"] is False and r["partly"] is False)
    check("row stores trajectory; replay rebuilds v3 prompt", r["trajectory"][-1] == "t8"
          and pcs.replay(r) == (pcs._sys3("answered"), calls[0][2]))

    print("[4] fire_rate splits v3, reports partly rate; old rows unaffected")
    fr = pcs.fire_rate()
    v = fr["v3"]
    check("v3 counts", v["asked"] == 3 and v["answered"] == 1 and v["partly"] == 1 and abs(v["partly_rate"] - 1 / 3) < 1e-9
          and v["settled"] == 2)
    check("by_prompt_v has v2 and v3", set(fr["by_prompt_v"]) == {"v2", "v3"})
    check("replay of a v2 row still the v2 prompt", pcs.replay({"driving_q": "q?", "standing": "s", "prompt_v": "v2"})[0] == pcs._SYS)

    print("[5] unchanged constants")
    check("CLOSE_FIRST/EVERY/ENOUGH_ASKED", (pcs.CLOSE_FIRST, pcs.CLOSE_EVERY, pcs.ENOUGH_ASKED) == (40, 20, 30))
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

"""Hermetic test for J-3104 (P-0101, F-3823..F-3825): core/pursuit_close_shadow asks a question that exists.
No LLM/hub: judge_panel.rule_detail is faked.  Shadow log + done_when store temp-pathed; runs inside lab_env.isolate().
Run: python scripts/_test_J3104_pursuit_close_prompt.py   (from the tree under test)"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio, copy, json, sys, tempfile
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
    ok_all = ok_all and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")

asked = []
async def fake(system, user, key, context="", **k):
    asked.append((system, user, context))
    return {"verdict": False, "how": "agreed", "why": "t"}
jp.rule_detail = fake

SCENE = "The cat sits on the sill and the pipes tick in the cold."
def P(i, **kw):
    d = {"id": i, "question": SCENE + " " + i, "standing": "stand-" + i + " it is the wall.", "open": "",
         "advances": 40, "status": "saturated"}
    d.update(kw)
    return d

with isolate(db="empty"):
    tmp = Path(tempfile.mkdtemp(prefix="J-3104_"))
    pcs.SHADOW_LOG = tmp / "pcs.jsonl"
    dw.STORE = tmp / "done_when.jsonl"
    assert "Nascence\\data" not in str(pcs.SHADOW_LOG)

    print("[1] open-question pursuit: open is the driving question, birth thought moves to WHAT IT STARTED FROM")
    po = P("o", open="Why does the pool stay full?")
    n = asyncio.run(pcs.sweep([po]))
    sysm, usr, ctx = asked[-1]
    head = usr.split("ITS STANDING")[0]
    check("one ask", n == 1 and ctx == "pursuit_close:o")
    check("driving slot holds the open question", head.startswith("PURSUIT (driving question): Why does the pool stay full?"))
    check("scene statement absent from the driving slot", SCENE not in head)
    check("scene statement present on WHAT IT STARTED FROM", f"WHAT IT STARTED FROM: {SCENE} o" in usr)
    check("no duplicate STILL-OPEN line", "STILL-OPEN" not in usr)
    check("system prompt unchanged (_SYS)", sysm == pcs._SYS)
    row = pcs._read()[-1]
    check("row stores the whole input", row["prompt_v"] == "v2" and row["driving_q"] == "Why does the pool stay full?"
          and row["standing"] == "stand-o it is the wall." and row["started_from"].startswith(SCENE)
          and row["driving_is_question"] is True and row["basis"] == "open")
    check("old row keys still present (question[:120], advances, would_resolve)",
          row["question"] == po["question"][:120] and row["advances"] == 40 and row["would_resolve"] is False)
    check("replay(row) rebuilds the exact prompt the judge saw", pcs.replay(row) == (sysm, usr))

    print("[2] stored caps: standing[:320], open[:160]")
    pl = P("long", standing="S" * 500, open="Q" + "x" * 300 + "?")
    asyncio.run(pcs.ask(pl)); rl = pcs._read()[-1]
    check("standing capped 320, open capped 160", len(rl["standing"]) == 320 and len(rl["open"]) == 160)
    check("replay still equals the prompt", pcs.replay(rl) == (asked[-1][0], asked[-1][1]))

    print("[3] no-question pursuit: ONE skip row, no judge call, never re-asked")
    pn = P("n")
    k = len(asked)
    items = [pn]
    for _ in range(3):
        asyncio.run(pcs.sweep(items))
    skips = [r for r in pcs._read() if r.get("id") == "n"]
    check("no judge call", len(asked) == k)
    check("exactly one skip row, asked False, askable False", len(skips) == 1 and skips[0]["kind"] == "close_skip"
          and skips[0]["asked"] is False and skips[0]["askable"] is False)
    check("due() never true for it", pcs.due(pn) is False)
    check("direct ask is a no-op", asyncio.run(pcs.ask(pn)) is None and len(asked) == k)

    print("[4] done_when-only pursuit keeps the OLD prompt shape (v1), text unchanged")
    dw.record("pursuit", "d", "I would know when the tide turns", dw.JUDGE_PURSUIT)
    pd = P("d")
    asyncio.run(pcs.ask(pd)); sysd, usd, _ = asked[-1]; rd = pcs._read()[-1]
    check("v1 row", rd["prompt_v"] == "v1" and rd["basis"] == "done_when" and rd["started_from"] == "")
    check("birth thought is in the driving slot, no WHAT IT STARTED FROM", usd.startswith(f"PURSUIT (driving question): {SCENE} d")
          and "WHAT IT STARTED FROM" not in usd)
    check("done_when line and closing question as before", "WOULD SETTLE IT: I would know when the tide turns" in usd
          and usd.endswith("by that condition?"))
    check("replay equals the v1 prompt", pcs.replay(rd) == (sysd, usd))

    print("[5] born question (D-0554) -> v2 as well; open differing from it still shown as STILL-OPEN")
    pq = P("q", question_kind="question", question_text="Is it the wall?", open="What made the wall?")
    asyncio.run(pcs.ask(pq)); uq = asked[-1][1]; rq = pcs._read()[-1]
    check("driving = born question, started = birth thought, still-open shown",
          uq.startswith("PURSUIT (driving question): Is it the wall?") and "WHAT IT STARTED FROM" in uq
          and "STILL-OPEN QUESTION IT RAISED: What made the wall?" in uq and rq["prompt_v"] == "v2")
    check("an open that is a statement is flagged driving_is_question False (D-0618 board/done_when fill)",
          (lambda r: r is not None)(pcs.build_prompt(P("s", open="the wall decides it")))
          and pcs.build_prompt(P("s", open="the wall decides it"))[2]["driving_is_question"] is False)

    print("[6] fire_rate reader splits by prompt_v and basis; unflagged rows unaffected")
    fr = pcs.fire_rate()
    check("by_prompt_v has v1 and v2", set(fr["by_prompt_v"]) == {"v1", "v2"} and fr["by_prompt_v"]["v1"]["asked"] == 1)
    check("by_basis has open, done_when, question", {"open", "done_when", "question"} <= set(fr["by_basis"]))
    check("skipped counted", fr["skipped_not_askable"] == 1)
    check("replay of an old row (no stored input) is None", pcs.replay({"id": "x", "kind": "close_ask"}) is None)

    print("[7] never mutates the pursuit; closure.py arms untouched")
    before = copy.deepcopy(pq)
    asyncio.run(pcs.ask(pq))
    check("pursuit untouched", pq == before)
    import core.closure as cl
    check("CLOSURE_ARMS unchanged by this module (no pursuit arm switched on)", "pursuit" not in set(getattr(cl, "CLOSURE_ARMS", ()) or ()))
print("ALL PASS" if ok_all else "FAILURES"); sys.exit(0 if ok_all else 1)

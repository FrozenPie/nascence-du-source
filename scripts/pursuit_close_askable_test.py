"""Hermetic test for J-3237 (D-0626): the pursuit close judge is asked only about `open` / done_when; others are skipped.
No LLM/hub: judge_panel.rule_detail is faked.  Shadow log + done_when store temp-pathed; runs inside lab_env.isolate().
Run: python scripts/pursuit_close_askable_test.py   (from the tree under test)"""
from __future__ import annotations
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
verdict = {"v": False}
async def fake(system, user, key, context="", **k):
    asked.append((context, user))
    return {"verdict": verdict["v"], "how": "agreed", "why": "t"}
jp.rule_detail = fake

def P(i, adv=40, st="saturated", kind=None, **kw):
    d = {"id": i, "question": "SCENE-" + i + " the cat sits on the sill.", "standing": "stand-" + i, "open": "",
         "advances": adv, "status": st}
    if kind:
        d["question_kind"] = kind
    d.update(kw)
    return d

with isolate(db="empty"):
    tmp = Path(tempfile.mkdtemp(prefix="J-3237_"))
    pcs.SHADOW_LOG = tmp / "pcs.jsonl"
    dw.STORE = tmp / "done_when.jsonl"
    assert str(ROOT) in str(Path(pcs.__file__).resolve()) and "Nascence\\data" not in str(pcs.SHADOW_LOG)

    print("[1] askable(): which pursuits can the judge say yes to")
    check("neither -> not askable", pcs.askable(P("n")) [0] is False)
    check("legacy with open -> askable, basis open, question = the open",
          pcs.askable(P("o", open="Why is the pool full?")) == (True, "open", "Why is the pool full?"))
    check("born question -> basis question, question_text",
          pcs.askable(P("q", kind="question", question_text="Is it the wall?")) == (True, "question", "Is it the wall?"))
    check("born done_when -> basis done_when",
          pcs.askable(P("d", kind="done_when", question_text="when I can name it"))[:2] == (True, "done_when"))
    check("observation with no open -> not askable", pcs.askable(P("ob", kind="observation", question_text=""))[0] is False)
    check("observation that later grew an open -> askable (D-0626: open decides)",
          pcs.askable(P("ob2", kind="observation", question_text="", open="What is it for?"))[:2] == (True, "open"))
    dw.record("pursuit", "sd", "I would know when the tide turns", dw.JUDGE_PURSUIT)
    check("done_when only in the side store -> askable, basis done_when", pcs.askable(P("sd"))[:2] == (True, "done_when"))
    check("garbage never raises", pcs.askable(None) == (False, "none", ""))

    print("[2] sweep: asks the askable, skips the rest with ONE close_skip row, no LLM for the skipped")
    items = [P("n"), P("o", open="Why is the pool full?"), P("ob", kind="observation", question_text=""),
             P("young", adv=12, st="active"), P("dorm", st="dormant")]
    before = copy.deepcopy(items)
    n = asyncio.run(pcs.sweep(items))
    check("one ask (o only)", n == 1 and [c for c, _ in asked] == ["pursuit_close:o"])
    check("judge shown the open as the driving question, scene statement absent",
          "PURSUIT (driving question): Why is the pool full?" in asked[0][1]
          and "SCENE-o" not in asked[0][1].split("ITS STANDING")[0])   # J-3104: scene statement only on WHAT IT STARTED FROM
    check("no duplicate STILL-OPEN line when open IS the driving question", "STILL-OPEN" not in asked[0][1])
    rows = pcs._read()
    ask_rows = [r for r in rows if r["kind"] == "close_ask"]
    skip_rows = [r for r in rows if r["kind"] == "close_skip"]
    check("ask row flagged askable true + basis open", ask_rows[0]["askable"] is True and ask_rows[0]["basis"] == "open")
    check("skip rows for n and ob only, askable false, asked false",
          sorted(r["id"] for r in skip_rows) == ["n", "ob"] and all(r["askable"] is False and r["asked"] is False for r in skip_rows))
    check("young active and dormant get no row", {r["id"] for r in rows} == {"o", "n", "ob"})
    check("items untouched", items == before)
    asyncio.run(pcs.sweep(items))
    check("second sweep: no re-ask, no duplicate skip rows", len(asked) == 1 and len(pcs._read()) == 3)
    check("direct ask() on a non-askable pursuit is a no-op", asyncio.run(pcs.ask(P("n"))) is None and len(asked) == 1)
    check("closure hand-off cannot run for a skipped pursuit (no ask, no row with a verdict)",
          not any(r.get("asked") for r in skip_rows))

    print("[3] an observation that grows an open is asked on the next sweep")
    items[2]["open"] = "Is it the light?"
    asyncio.run(pcs.sweep(items))
    check("ob now asked with basis open", asked[-1][0] == "pursuit_close:ob" and pcs._read()[-1]["basis"] == "open")

    print("[4] pre-D-0626 rows (no askable flag) do not consume the ask slot and are out of the rate")
    old = {"ts": 1.0, "kind": "close_ask", "id": "legacyA", "advances": 41, "asked": True, "would_resolve": False}
    with open(pcs.SHADOW_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(old) + "\n")
    check("legacyA with a real open is due again", pcs.due(P("legacyA", adv=41, open="Why?")))
    fr = pcs.fire_rate()
    check("rate counts flagged askable asks only (o, ob), unflagged legacyA left out",
          fr["pursuits_asked"] == 2 and fr["skipped_not_askable"] == 2 and fr["enough"] is False)
    fr2 = pcs.fire_rate(include_unflagged=True)
    check("include_unflagged brings the old row back", fr2["pursuits_asked"] == 3)

    print("[5] fire_rate verdict + enough, over askable asks")
    verdict["v"] = True
    its = [P(f"k{i}", open=f"q{i}?") for i in range(30)]
    asyncio.run(pcs.sweep(its))
    fr = pcs.fire_rate()
    check("32 askable asked, 30 fired -> too_lenient, enough True",
          fr["pursuits_asked"] == 32 and fr["would_resolve"] == 30 and fr["verdict"] == "too_lenient" and fr["enough"])

    print("[6] fail-open + flag")
    check("disabled = no-op", (setattr(pcs, "SHADOW_ENABLED", False), asyncio.run(pcs.sweep([P("z", open="q?")])))[1] == 0)
    pcs.SHADOW_ENABLED = True
print("ALL PASS" if ok_all else "FAILURES"); sys.exit(0 if ok_all else 1)

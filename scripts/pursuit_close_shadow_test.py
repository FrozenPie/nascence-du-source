"""Hermetic test for J-2171 (D-0426 A): core/pursuit_close_shadow.py + the pursuits.judge_pending hook.
No LLM/hub: judge_panel.rule_detail is faked.  Runs inside lab_env.isolate(); shadow + pursuits stores temp-pathed.
Run: python scripts/pursuit_close_shadow_test.py   (from the tree under test)"""
from __future__ import annotations
import asyncio, json, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.pursuits as pu
import core.pursuit_close_shadow as pcs
import core.judge_panel as jp
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True
def check(n, c):
    global ok_all
    ok_all = ok_all and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")

calls = []
verdicts = {"v": True}
async def fake(system, user, key, context="", **k):
    calls.append((key, context))
    v = verdicts["v"]
    return {"verdict": v, "how": "agreed" if v is not None else "unavailable", "why": "t"}
jp.rule_detail = fake

with isolate(db="empty", also=[(pu, ["_DIR", "_ACTIVE", "_SHADOW", "_SERIES"])]):
    tmp = Path(tempfile.mkdtemp(prefix="J-2171_"))
    pcs.SHADOW_LOG = tmp / "pcs.jsonl"
    pu._DIR = tmp; pu._ACTIVE = tmp / "a.json"; pu._SHADOW = tmp / "s.jsonl"; pu._SERIES = tmp / "ser.jsonl"
    P = lambda i, adv, st="saturated": {"id": i, "question": "q" + i, "standing": "s" + i, "open": "why " + i + "?", "advances": adv, "status": st}   # D-0626: askable only with a real open
    print("[1] due()")
    check("39 not due", not pcs.due(P("a", 39, "active")))
    check("40 due", pcs.due(P("a", 40)))
    print("[2] sweep asks once, logs, does not mutate")
    items = [P("a", 40), P("b", 12, "active"), P("c", 40, "dormant")]
    import copy; before = copy.deepcopy(items)
    n = asyncio.run(pcs.sweep(items))
    check("one ask (a only)", n == 1 and len(calls) == 1 and calls[0][1] == "pursuit_close:a")
    check("items untouched (status stays saturated)", items == before)
    rows = pcs._read()
    check("row would_resolve + note", rows[0]["would_resolve"] is True and rows[0]["would_note"] == "sa")
    check("no re-ask at 40", asyncio.run(pcs.sweep(items)) == 0)
    items[0]["advances"] = 59; check("no re-ask at 59", asyncio.run(pcs.sweep(items)) == 0)
    items[0]["advances"] = 60; check("re-ask at 60", asyncio.run(pcs.sweep(items)) == 1)
    print("[3] unavailable does not consume the slot")
    verdicts["v"] = None
    items2 = [P("d", 40)]
    asyncio.run(pcs.sweep(items2)); check("unavailable row asked=False", pcs._read()[-1]["asked"] is False)
    verdicts["v"] = False
    check("re-asked next sweep", asyncio.run(pcs.sweep(items2)) == 1)
    print("[4] fire_rate")
    fr = pcs.fire_rate(); check("rate computed over a,d", fr["pursuits_asked"] == 2 and fr["would_resolve"] == 1 and fr["verdict"] == "ok")
    print("[5] fail-open + flag")
    async def boom(*a, **k): raise RuntimeError("x")
    jp.rule_detail = boom
    check("ask swallows exception", asyncio.run(pcs.ask(P("e", 40))) is None)
    jp.rule_detail = fake; pcs.SHADOW_ENABLED = False
    check("disabled = no-op", asyncio.run(pcs.sweep([P("f", 99)])) == 0); pcs.SHADOW_ENABLED = True
    print("[6] pursuits.judge_pending hook: register unchanged by close shadow, shadow row written")
    pu._save([{"id": "g", "question": "qg", "status": "saturated", "advances": 40, "heat": .5, "pending": [{"thought": "t", "prior_standing": "p", "tries": 0}]}])
    async def adv(system, user, key, context="", **k): return True
    jp.rule = adv
    asyncio.run(pu.judge_pending())
    reg = pu._load()
    check("status still saturated, never resolved", reg[0]["status"] != "resolved")
    check("g asked in shadow", any(r["id"] == "g" for r in pcs._read()))
    print("[7] J-3104: open-question pursuit asked with the open as driving question; no-question pursuit logs once, no judge call")
    pcs.SHADOW_LOG = tmp / "pcs7.jsonl"
    seen = []
    async def fake7(system, user, key, context="", **k):
        seen.append(user); return {"verdict": False, "how": "agreed", "why": "t"}
    jp.rule_detail = fake7
    Q = {"id": "q7", "question": "birth scene q7", "standing": "s7", "open": "Does it hold?", "advances": 40, "status": "saturated"}
    N = {"id": "n7", "question": "birth scene n7", "standing": "s7", "open": "", "advances": 40, "status": "saturated"}
    asyncio.run(pcs.sweep([Q, N])); asyncio.run(pcs.sweep([Q, N]))
    check("asked once, driving slot = the open, birth thought on WHAT IT STARTED FROM",
          len(seen) == 1 and seen[0].startswith("PURSUIT (driving question): Does it hold?") and "WHAT IT STARTED FROM: birth scene q7" in seen[0])
    r7 = pcs._read()
    check("no-question pursuit: one close_skip row, no judge call", [r["kind"] for r in r7 if r["id"] == "n7"] == ["close_skip"])
    check("ask row stores standing + open and replays exactly",
          r7[0]["standing"] == "s7" and r7[0]["open"] == "Does it hold?" and pcs.replay(r7[0]) == (pcs._SYS, seen[0]))
print("ALL PASS" if ok_all else "FAILURES"); sys.exit(0 if ok_all else 1)

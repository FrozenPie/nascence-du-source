"""J-2202 test: the sleep-batch entry point core/social_cognition_shadow.sleep_sweep() with a STUB judge panel
(no hub calls), every path redirected via lab_env.isolate(also=...). Import core BEFORE lab_env. Exit 0 = pass.
Canary: the LIVE C:/Nascence social-cognition log + state must be byte-identical before/after."""
import asyncio, json, sys, pathlib, hashlib, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import social_cognition_shadow as S, judge_panel as jp, shadow_log

FAILS = []
def check(l, c):
    print(("  ok   " if c else "  FAIL ") + l)
    if not c: FAILS.append(l)

LIVE = [pathlib.Path(r"C:\Nascence\data\social_cognition_shadow.jsonl"), pathlib.Path(r"C:\Nascence\data\social_cognition_shadow_state.json")]
def canary():
    return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None) for p in LIVE}
before = canary()
calls = {"n": 0}
async def fake(system, user, key, context="", **kw):
    calls["n"] += 1
    return {"verdict": True, "how": "agreed", "v1": True, "v2": True, "why": "stub"}
async def down(*a, **k):
    calls["n"] += 1
    return {"verdict": None, "how": "unavailable"}
orig = jp.rule_detail
try:
    with lab_env.isolate(also=[(S, ["_LOG", "_STATE", "_CONV_LOG"])], db="empty") as lab:
        check("conv log redirected", str(S._CONV_LOG).startswith(str(lab)))
        base = 1790600000
        S._CONV_LOG.write_text("\n".join(json.dumps({"ts": base + 60 * k, "cycle_id": f"c{k}", "human": f"turn {k} about the garden",
                                                      "entity": f"reply {k}"}) for k in range(5)), encoding="utf-8")
        jp.rule_detail = fake
        r = asyncio.run(S.sleep_sweep())
        check(f"cap: 3 of 5 scored ({r})", r["scored"] == 3 and r["candidates"] == 5)
        r = asyncio.run(S.sleep_sweep())
        check(f"next sleep: remaining 2 scored ({r})", r["scored"] == 2 and r["candidates"] == 2)
        r = asyncio.run(S.sleep_sweep())
        check("third sleep: nothing new", r["scored"] == 0 and r["candidates"] == 0)
        # time budget: a zero budget starts no turn and logs why
        with open(S._CONV_LOG, "a", encoding="utf-8") as f:
            f.write("\n" + json.dumps({"ts": base + 900, "cycle_id": "n1", "human": "new one", "entity": "ok"}))
        r = asyncio.run(S.sweep(max_items=3, time_budget_s=0.0))
        tail = shadow_log.read_rows(S._LOG)[-1]
        check(f"zero budget: no turn started, skip logged ({r})", r["scored"] == 0 and r.get("budget_stop") and tail.get("skip") == "time-budget")
        # judges down: stop at the first unavailable turn (one turn's rulings only)
        with open(S._CONV_LOG, "a", encoding="utf-8") as f:
            f.write("\n" + json.dumps({"ts": base + 960, "cycle_id": "n2", "human": "another", "entity": "ok"}))
        jp.rule_detail = down
        calls["n"] = 0
        r = asyncio.run(S.sleep_sweep())
        check(f"judges down: stops after first turn ({r}, calls={calls['n']})", r["unavailable"] == 1 and r["scored"] == 0 and calls["n"] <= 4)
        jp.rule_detail = fake
        r = asyncio.run(S.sleep_sweep())
        check(f"judges back: both new turns scored ({r})", r["scored"] == 2)
        S.SLEEP_SWEEP_ENABLED = False
        check("kill switch", asyncio.run(S.sleep_sweep()) == {"disabled": True})
        S.SLEEP_SWEEP_ENABLED = True
        check("all writes went to the lab log", str(S._LOG).startswith(str(lab)) and len([x for x in shadow_log.read_rows(S._LOG) if "tracks_intent" in x]) == 7)
finally:
    jp.rule_detail = orig
check("live social-cognition files untouched (sha256 canary)", canary() == before)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)

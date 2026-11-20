"""J-3219 / D-0608 test: the Curiosity pre-fire SHADOW check. Stubs every model call; writes only under a temp dir;
touches no live data. Run from the worktree:  python scripts/_test_J-3219_curiosity_prefire.py"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: F401,E402  (import core BEFORE lab_env)
from core import curiosity_prefire as cp  # noqa: E402
from core import judge_panel as jp  # noqa: E402

assert Path(cp.__file__).resolve().parent.parent == ROOT, "tests must import THIS tree"
assert Path(jp.__file__).resolve().parent.parent == ROOT

_fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (("  " + str(detail)) if detail and not cond else ""))
    if not cond:
        _fails.append(name)


PROMPT = (
    "Entity: X\n\nRecent themes:\n  - lamp and oil\n\n"
    "Recently studied or read — ask a real open question ABOUT one of these (what it makes you wonder):\n"
    "  - (Napoleon) Marshal Brune was sent to Bremen with a small force in 1807.\n"
    "  - (Acre) The siege of Acre cost the army far more men than the official reports said.\n\n"
    "Unresolved inner threads you might also follow:\n  - unresolved: duty's weight\n\n"
    "Generate questions and research directions worth exploring next."
)

# 1. material_from_prompt strips the Entity line and the closing instruction only
m = cp.material_from_prompt(PROMPT)
check("material strips entity+tail", m.startswith("Recent themes:") and "Generate questions" not in m and "Entity:" not in m)

# 2. the study/own split
world, own = jp._prefire_split_material(m)
check("split: world holds study lines only", "Marshal Brune" in world and "unresolved" not in world and "lamp" not in world, world)
check("split: own holds themes + threads", "lamp and oil" in own and "duty's weight" in own, own)
check("split: no study block -> world empty", jp._prefire_split_material("Recent themes:\n  - a")[0] == "")


# 3. scoring with a stub judge; the support-quote guard downgrades an ungrounded 'answerable'
async def fake_ask(system, user):
    q = user.split("CANDIDATE QUESTION:", 1)[1]
    if "Brune" in q:
        return {"support": "Marshal Brune was sent to Bremen", "answerable": True, "unsupported_link": False, "why": "x"}, None, 0.1
    if "lamp" in q:   # claims answerable but quotes text that is NOT in the studied material
        return {"support": "the lamp needs oil", "answerable": True, "unsupported_link": True, "why": "y"}, None, 0.1
    return {"support": "", "answerable": False, "unsupported_link": False, "why": "z"}, None, 0.1


cands = ["What does the lamp mean for growth?", "Why was Marshal Brune at Bremen?", "What is time?"]
res = asyncio.run(jp.score_curiosity_candidates(cands, m, ask=fake_ask))
sc = {r["i"]: r for r in res["scores"]}
check("brune scores 2", sc[1]["score"] == 2 and sc[1]["support_ok"] is True, sc[1])
check("ungrounded answerable downgraded + link -> 0", sc[0]["score"] == 0 and sc[0]["support_ok"] is False, sc[0])
check("abstract scores 1", sc[2]["score"] == 1, sc[2])
check("ok flag", res["ok"] is True)

# 4. pick: highest wins, tie -> lowest index, unique_top flag
check("pick top", cp.pick(res["scores"]) == (1, True))
check("pick tie -> lowest index, not unique", cp.pick([{"i": 0, "score": 2}, {"i": 1, "score": 2}]) == (0, False))
check("pick nothing scored", cp.pick([{"i": 0, "score": None}]) == (None, False))

# 5. fail-open: a dead judge yields err rows and stops after the first failure, never raises
async def dead_ask(system, user):
    return None, "http", 0.2


res = asyncio.run(jp.score_curiosity_candidates(cands, m, ask=dead_ask))
check("dead judge fail-open", res["ok"] is False and res["scores"][0]["err"] == "http"
      and all(r["err"] == "skipped" for r in res["scores"][1:]), res)

async def boom_ask(system, user):
    raise RuntimeError("boom")


res = asyncio.run(jp.score_curiosity_candidates(cands, m, ask=boom_ask))
check("raising judge swallowed", res["ok"] is False and res["scores"] == [], res)

# 6. _run writes one paired row (temp dir), fired index + agree + would-pick recorded; live flag False
with tempfile.TemporaryDirectory() as td:
    log = Path(td) / "data" / "curiosity_prefire_shadow.jsonl"

    async def stub_score(candidates, material, ask=None):
        return await jp.score_curiosity_candidates(candidates, material, ask=fake_ask)

    # point the profile fence at "live" for this process only, restore after
    old_live = cp.profile.LIVE
    cp.profile.LIVE = True
    try:
        row = asyncio.run(cp._run(cands, cands[0], m, path=log, score_fn=stub_score))
    finally:
        cp.profile.LIVE = old_live
    check("row written", log.exists() and len(log.read_text(encoding="utf-8").splitlines()) == 1)
    r = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    check("row pairs fired vs would-pick", r["fired_i"] == 0 and r["would_pick_i"] == 1 and r["agree"] is False
          and r["live"] is False, r)
    check("inflight cleared after run", cp._inflight is False)

    # 7. a non-live process: the fence refuses the write, quietly, row still returned
    cp.profile.LIVE = False
    try:
        log2 = ROOT / "data" / "curiosity_prefire_shadow.jsonl"       # real-looking path: fence must refuse, not write
        before = log2.exists()
        row2 = asyncio.run(cp._run(cands, cands[0], m, path=log2, score_fn=stub_score))
    finally:
        cp.profile.LIVE = old_live
    check("non-live write refused quietly", row2 is not None and log2.exists() == before)

    # 8. the reader
    with open(log, "a", encoding="utf-8") as fh:
        for k in range(60):     # 60 agreeing rows -> same_pick defeater
            fh.write(json.dumps({"would_pick_i": 0, "fired_i": 0, "agree": True, "unique_top": False,
                                 "candidates": [{"score": 2}, {"score": 2}]}) + "\n")
    st = cp.status(log)
    check("status counts rows", st["rows"] == 61 and st["scored_rows"] == 61, st)
    check("status defeater same_pick", st["defeater"] == "same_pick", st)
    log3 = Path(td) / "log3.jsonl"
    with open(log3, "w", encoding="utf-8") as fh:
        for k in range(50):
            fh.write(json.dumps({"would_pick_i": k % 3, "fired_i": 0, "agree": (k % 3) == 0, "unique_top": True,
                                 "candidates": [{"score": 0}, {"score": 1}, {"score": 2}]}) + "\n")
    st3 = cp.status(log3)
    check("status clear when scores vary and picks differ", st3["defeater"] == "clear", st3)
    check("status empty file", cp.status(Path(td) / "nope.jsonl") == {"rows": 0})

# 9. shadow_spawn: returns at once, drops on <2 candidates, single-flight, no loop -> False
check("spawn: no running loop -> False, no raise", cp.shadow_spawn(cands, cands[0], PROMPT) is False)
check("spawn: inflight cleared after loop error", cp._inflight is False)


async def spawn_cases():
    one = cp.shadow_spawn(["only one"], "only one", PROMPT)
    cp._inflight = True
    dropped_before = cp._dropped
    two = cp.shadow_spawn(cands, cands[0], PROMPT)
    cp._inflight = False
    return one, two, cp._dropped - dropped_before


one, two, dropped = asyncio.run(spawn_cases())
check("spawn: <2 candidates -> False", one is False)
check("spawn: single-flight drop counted", two is False and dropped == 1)

# 10. the orchestrator hook is wired AFTER the firing choice and BEFORE run_cycle, never assigns `question`
src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
i_choose = src.index("question = _wd.choose(")
i_hook = src.index("_cpf.shadow_spawn(")
i_fire = src.index('await self.run_cycle(question, input_type="internal")', i_hook)
check("hook sits between the choice and the firing", i_choose < i_hook < i_fire)
hook_block = src[i_hook - 600:i_hook + 400]
check("hook never assigns question", "question =" not in hook_block.split("_cpf.shadow_spawn(")[1].split("except")[0])
check("hook is not awaited", "await _cpf" not in src and "await" not in src[i_hook - 60:i_hook])

# 11. the node stashes the prompt it built (read only by the shadow check)
nsrc = (ROOT / "nodes" / "curiosity_node.py").read_text(encoding="utf-8")
check("node stashes _last_user_prompt", "self._last_user_prompt = _prompt" in nsrc and "return _prompt" in nsrc)

# 12. control set is well-formed and has the documented 6/3/11 split
ctl = json.loads((ROOT / "scripts" / "curiosity_prefire_control_set.json").read_text(encoding="utf-8"))["items"]
from collections import Counter  # noqa: E402
check("control set 6/3/11", Counter(i["label"] for i in ctl) == Counter({"good": 6, "borderline": 3, "bad": 11}))

print("\n%s" % ("ALL PASS" if not _fails else "FAILED: " + ", ".join(_fails)))
sys.exit(1 if _fails else 0)

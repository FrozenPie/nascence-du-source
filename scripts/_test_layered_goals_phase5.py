"""Hermetic test for Layered Goals Phase 5 detection (core/goal_conflict.py, shadow) and the stalled flag.
Temp dir only; the judge is a stub. Run: python scripts/_test_layered_goals_phase5.py"""
import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import goals, goal_offer, goal_conflict   # noqa: E402

FAILS = []
ROOT = Path(__file__).resolve().parent.parent


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def w(root, rel, obj, jsonl=False):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in obj) if jsonl else json.dumps(obj), encoding="utf-8")


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def main():
    t0 = time.time()
    asked = []

    async def judge(system, user):
        asked.append(user)
        hit = "leave this static place" in user and "stay with the stillness" in user
        return {"verdict": hit, "how": "agreed", "why": "leaving and staying cannot both be done" if hit else "different subjects"}

    async def judge_down(system, user):
        asked.append(user)
        return {"verdict": None, "how": "unavailable", "why": ""}

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        goals._DATA = root
        goals._assignment = lambda: (None, None)
        goal_offer._school_time = lambda: False
        goal_offer._where = lambda: None
        w(root, "intentions.json", {"open": [
            {"key": "lamp|light the lamp", "family": "lamp", "object": "lamp", "deed": "light the lamp", "reason": "place:in the study", "ts": t0 - 600, "renewed_ts": t0 - 600},
            {"key": "move|sea", "family": "move", "object": "sea", "deed": "walk to the sea", "reason": "place:down on the shore", "ts": t0 - 500, "renewed_ts": t0 - 500},
            {"key": "fire|grate", "family": "fire", "object": "grate", "deed": "lay the fire", "reason": "place:in the study", "ts": t0 - 400, "renewed_ts": t0 - 400}]})
        w(root, "commitment_active.json", [
            {"id": "s1", "statement": "I need to leave this static place and move toward something real.", "held_since": t0 - 900, "load_bearing": True},
            {"id": "s2", "statement": "I will stay with the stillness here until it has told me what it holds.", "held_since": t0 - 800, "load_bearing": True},
            {"id": "s3", "statement": "Small repeated acts of choosing are enough.", "held_since": t0 - 700, "load_bearing": True},
            {"id": "s4", "statement": "The crabs shift with the pressure.", "held_since": t0 - 600, "load_bearing": True}])
        w(root, "commitment_second_look_shadow.jsonl", [{"stand_id": "s4", "second_look": "insight"}], jsonl=True)
        w(root, "pursuits_active.json", [
            {"id": "p1", "status": "active", "question": "circling", "advances": 3, "restates": 5, "born": t0 - 7200, "last_touched": t0 - 100},
            {"id": "p2", "status": "active", "question": "moving", "advances": 9, "restates": 1, "born": t0 - 7200, "last_touched": t0 - 100},
            {"id": "p3", "status": "active", "question": "young", "advances": 2, "restates": 2, "born": t0 - 7200, "last_touched": t0 - 100}])
        w(root, "frontier.light.json", {"open": [{"id": "q1", "q": "Is waiting a form of action?", "encounters": 3, "born": t0 - 100, "last_seen": t0 - 20}]})
        w(root, "frontier.json", {"questions": []})
        w(root, "deferred_intentions.json", {"intentions": [{"ts": t0 - 9000, "intention": "I want to finish reading about bee navigation.", "carry_count": 2}]})
        goals.tick(t0)
        goal_offer._reg_cache = None
        reg = json.loads(goals.register_path().read_text(encoding="utf-8"))
        g = {x["id"]: x for x in reg["goals"]}

        # ---- stalled flag (observed, changes no state) ----
        check("pursuit that mostly restates is flagged stalled", g["pursuit:p1"]["progress"]["stalled"] is True and g["pursuit:p1"]["state"] == "held")
        check("pursuit that advances is not", g["pursuit:p2"]["progress"]["stalled"] is False)
        check("too few events to call it", g["pursuit:p3"]["progress"]["stalled"] is False)

        # ---- resource conflicts: deterministic ----
        rc = goal_conflict.resource_conflicts(reg["goals"], t0)
        pairs = {tuple(sorted((r["a"], r["b"]))) for r in rc}
        check("deeds in different places with open windows conflict for place", pairs == {("intention:lamp|light the lamp", "intention:move|sea"), ("intention:fire|grate", "intention:move|sea")}, pairs)
        check("deeds in the same place do not", ("intention:fire|grate", "intention:lamp|light the lamp") not in pairs)
        check("a deed whose window has closed is left out", goal_conflict.resource_conflicts(reg["goals"], t0 + 9 * 3600) == [])

        # ---- inherent conflicts: only held stands and wants are paired ----
        pend = goal_conflict.pending_pairs(reg["goals"], {})
        ids = {x["id"] for p in pend for x in p}
        check("pairs are drawn from held stands and wants only", ids == {"stand:s1", "stand:s2", "stand:s3"} | {i for i in ids if i.startswith("want:")} and len(pend) == 6, (ids, len(pend)))
        check("insight-ruled stand, questions, pursuits and deeds are never paired", not any(i.startswith(("question:", "pursuit:", "intention:")) or i == "stand:s4" for i in ids))

        goal_conflict._judge = judge
        outs = [asyncio.run(goal_conflict.sweep(t0 + 10 * k)) for k in range(7)]
        lg = rows(goal_conflict.log_path())
        inh = [r for r in lg if r["kind"] == "inherent"]
        check("one pair per sweep, each pair asked once", len(inh) == 6 and len(asked) == 6 and outs[-1]["asked"] is None and outs[-1]["pending"] == 0, (len(inh), len(asked), outs[-1]))
        hits = [r for r in inh if r["conflict"]]
        check("the one strict conflict is found", len(hits) == 1 and {hits[0]["a"], hits[0]["b"]} == {"stand:s1", "stand:s2"}, hits)
        check("the judge sees only the two sentences", all(u.startswith("FIRST: ") and "\n\nSECOND: " in u and "stand:" not in u for u in asked))
        check("resource conflicts logged once, not every sweep", sum(r["kind"] == "resource" for r in lg) == 1)
        sysp = goal_conflict.CONFLICT_JUDGE_SYS
        check("the judge is told that different or competing-for-time is not a conflict", "merely different" in sysp and "compete for time" in sysp and "if you cannot tell, answer false" in sysp)
        st = goal_conflict.stats()
        check("stats reader", st == {"inherent_asked": 6, "inherent_conflict": 1, "inherent_unavailable": 0, "resource_rows": 1}, st)

        # ---- a reworded stand is a new pair; an unavailable judge is not cached ----
        ca = json.loads((root / "commitment_active.json").read_text(encoding="utf-8"))
        ca[2]["statement"] = "Small repeated acts of choosing are enough, and I will stop reaching for more."
        w(root, "commitment_active.json", ca)
        goals.tick(t0 + 600)
        goal_offer._reg_cache = None
        goal_conflict._judge = judge_down
        n = len(asked)
        o = asyncio.run(goal_conflict.sweep(t0 + 700))
        check("rewording reopens its pairs", o["pending"] >= 1 and len(asked) == n + 1)
        o2 = asyncio.run(goal_conflict.sweep(t0 + 710))
        check("an unavailable judge leaves the pair to be asked again", o2["pending"] == o["pending"] and rows(goal_conflict.log_path())[-1]["conflict"] is None)

        # ---- nothing here reaches him or any other store ----
        check("only its own log and cache are written", sorted(p.name for p in root.rglob("goal_conflict*")) == ["goal_conflict_pairs.json", "goal_conflict_shadow.jsonl"])
        check("the offer path knows nothing of conflicts", "goal_conflict" not in (ROOT / "core" / "goal_offer.py").read_text(encoding="utf-8"))

        # ---- switches and scheduling ----
        check("no running loop: not scheduled", goal_conflict.sweep_later(t0) is False)

        async def sched():
            goal_conflict._last_sweep = 0.0
            a = goal_conflict.sweep_later(t0 + 2000)
            b = goal_conflict.sweep_later(t0 + 2100)
            await asyncio.gather(*list(goal_conflict._tasks))
            return a, b
        check("scheduled once, then held for the interval", asyncio.run(sched()) == (True, False))
        goal_conflict.GOAL_CONFLICT_SHADOW = False
        check("kill switch", asyncio.run(goal_conflict.sweep(t0)) is None and goal_conflict.sweep_later(t0 + 9999) is False)
        goal_conflict.GOAL_CONFLICT_SHADOW = True

    node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
    check("node schedules the sweep and never awaits it", "_gcf.sweep_later()" in node and "await _gcf" not in node)
    check("node: the frontier seed path leaves a rested question be", "_go_r.is_rested_text(_seed.get(\"q\") or \"\")" in node)

    print("\n%s (%d failed)" % ("ALL OK" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

"""Hermetic test for Layered Goals Phase 6 (the optional `set_down` field and its judge; D-0768).
Temp dir only; the judge is a stub; no live store and no model is touched.
Run: python scripts/_test_layered_goals_phase6.py"""
import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import goals, goal_offer   # noqa: E402

FAILS = []
ROOT = Path(__file__).resolve().parent.parent


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


class Seq:
    def __init__(self, *vals):
        self.vals = list(vals)

    def random(self):
        return self.vals.pop(0)


def w(root, rel, obj, jsonl=False):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in obj) if jsonl else json.dumps(obj), encoding="utf-8")


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


GOOD = ("I got as far as seeing that a name changes how a thing is treated, not what it is made of; "
        "whether that treatment is part of its nature is still open, and I leave it there for now.")


def main():
    t0 = time.time()
    calls = []

    async def judge_yes(system, user):
        calls.append(user)
        return {"verdict": True, "how": "agreed", "why": "about the goal, says where it got to and what is open"}

    async def judge_no(system, user):
        calls.append(user)
        return {"verdict": False, "how": "agreed", "why": "only says it is stopping"}

    async def judge_down(system, user):
        calls.append(user)
        return {"verdict": None, "how": "unavailable", "why": ""}

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        goals._DATA = root
        goals._assignment = lambda: (None, None)
        goal_offer._school_time = lambda: False
        goal_offer._where = lambda: None
        goal_offer._log_injection = lambda *a: None
        q = {"id": "q1", "q": "Does naming a thing change its nature?", "encounters": 3, "born": t0 - 4000, "last_seen": t0 - 30, "status": "open"}
        q2 = {"id": "q2", "q": "How does altitude shape shelter?", "encounters": 2, "born": t0 - 4000, "last_seen": t0 - 30, "status": "open"}
        w(root, "frontier.light.json", {"open": [q, q2]}); w(root, "frontier.json", {"questions": [q, q2]})
        for f, v in (("intentions.json", {"open": []}), ("commitment_active.json", []), ("pursuits_active.json", []),
                     ("deferred_intentions.json", {"intentions": []})):
            w(root, f, v)
        goals.tick(t0)
        goal_offer._reg_cache = None

        # ---- the field appears only when a held goal was put in front of him ----
        check("no offer: schema and rule are empty (old prompt exactly)", goal_offer.set_down_schema(False) == "" and goal_offer.set_down_rule(False) == "")
        check("offer: schema carries the field", goal_offer.set_down_schema(True) == ', "set_down": ""')
        rule = goal_offer.set_down_rule(True)
        check("rule describes a channel and does not ask him to use it", 'Leave as ""' in rule and "Your own judgement" in rule)
        banned = ("you should", "you must", "try to", "it is time", "finish", "resolve it", "decide")
        check("rule does not steer him toward ending", not any(b in rule.lower() for b in banned), rule)
        check("parse: absent, empty and non-dict are empty", goal_offer.parse_set_down({}) == "" and goal_offer.parse_set_down({"set_down": "  "}) == "" and goal_offer.parse_set_down(None) == "")
        check("parse: his note comes back whole", goal_offer.parse_set_down({"set_down": GOOD}) == GOOD)

        live = goal_offer.live_offer(t0 + 5, Seq(0.1, 0.9, 0.0))
        og = goal_offer.offered_goal(live, live["pc"])
        check("the register's own offer is the offered goal", og and og["id"] == live["goal_id"], og)
        check("the ordinary anchor's question is recognised when the register holds it", goal_offer.offered_goal(None, {"text": q2["q"]}) == {"id": "question:q2", "text": q2["q"]})
        check("an anchor text the register does not hold offers nothing", goal_offer.offered_goal(None, {"text": "working through 'X'"}) is None)

        goal = {"id": "question:q1", "text": q["q"]}

        # ---- thin notes never reach a judge ----
        goal_offer._judge = judge_yes
        r = asyncio.run(goal_offer._set_down(goal, "Enough for now.", "t", "c1"))
        check("too short: rejected by the precheck, no judge call", r["accepted"] is False and r["how"] == "precheck" and not calls, r)
        r = asyncio.run(goal_offer._set_down(goal, "Does naming a thing change its nature, does naming change nature of a thing?", "t", "c1"))
        check("repeating the goal: rejected by the precheck", r["accepted"] is False and r["why"] == "repeats the goal" and not calls, r)
        check("nothing rested yet", not goal_offer.set_down_path().exists())

        # ---- judge says no / judge unavailable: logged, nothing changes ----
        goal_offer._judge = judge_no
        r = asyncio.run(goal_offer._set_down(goal, GOOD, "t", "c1"))
        check("judge rejects: logged, not rested", r["accepted"] is False and len(calls) == 1 and not goal_offer.set_down_path().exists())
        goal_offer._judge = judge_down
        r = asyncio.run(goal_offer._set_down(goal, GOOD, "t", "c1"))
        check("judge unavailable: no state change", r["accepted"] is False and r.get("judged") is False and not goal_offer.set_down_path().exists(), r)
        check("the judge sees only the goal and the note", "THE THING IT WAS HOLDING: Does naming" in calls[-1] and GOOD in calls[-1] and "thought" not in calls[-1].lower())
        sysp = goal_offer.SET_DOWN_JUDGE_SYS
        check("the judge is told not to judge wisdom or truth", "Do NOT judge whether stopping is wise" in sysp and "true or well reasoned" in sysp)

        # ---- accepted: the goal rests ----
        goal_offer._judge = judge_yes
        r = asyncio.run(goal_offer._set_down(goal, GOOD, "the thought", "c1"))
        store = json.loads(goal_offer.set_down_path().read_text(encoding="utf-8"))
        check("accepted: written to the set-down store with the recurrence count at that moment", r["accepted"] is True and store["question:q1"]["recurrences_at"] == 3 and store["question:q1"]["note"] == GOOD, store)
        check("every attempt is logged", len(rows(goal_offer.set_down_log_path())) == 5)
        goals.tick(t0 + 600)
        goal_offer._reg_cache = None
        reg = json.loads(goals.register_path().read_text(encoding="utf-8"))
        g1 = next(x for x in reg["goals"] if x["id"] == "question:q1")
        check("the register shows it rested, with his note", g1["state"] == "rested" and g1["set_down"]["note"] == GOOD and g1["state_if_not_rested"] == "held", g1)
        lg = rows(goals.log_path())
        check("the rest is logged as a state change", any(x["event"] == "state" and x["id"] == "question:q1" and x["to"] == "rested" for x in lg))
        check("a rested goal is not eligible and is never offered", all("question:q1" not in (x.get("eligible") or []) for x in [json.loads(l) for l in goal_offer.log_path().read_text(encoding="utf-8").splitlines()][-1:]))
        offered = {goal_offer.live_offer(t0 + 610, Seq(0.1, 0.9, u))["goal_id"] for u in (0.0, 0.3, 0.6, 0.9)}
        check("live offers skip it", offered == {"question:q2"}, offered)
        check("the ordinary anchor is told to leave it be", goal_offer.is_rested_text(q["q"]) is True and goal_offer.is_rested_text(q2["q"]) is False)
        check("the question itself is untouched in its store", json.loads((root / "frontier.json").read_text(encoding="utf-8"))["questions"][0]["status"] == "open")

        # ---- he takes it up again: it comes back on its own ----
        q["encounters"] = 4
        w(root, "frontier.light.json", {"open": [q, q2]}); w(root, "frontier.json", {"questions": [q, q2]})
        goals.tick(t0 + 1200)
        goal_offer._reg_cache = None
        g1 = next(x for x in json.loads(goals.register_path().read_text(encoding="utf-8"))["goals"] if x["id"] == "question:q1")
        check("met again: no longer rested", g1["state"] == "held" and g1.get("resumed_after_set_down") and goal_offer.is_rested_text(q["q"]) is False, g1)

        # ---- switches and scheduling ----
        check("no running loop: not scheduled, never raises", goal_offer.set_down_later(goal, GOOD, "t", "c") is False)

        async def sched():
            ok = goal_offer.set_down_later(goal, GOOD, "t", "c")
            await asyncio.gather(*list(goal_offer._tasks))
            return ok
        n = len(rows(goal_offer.set_down_log_path()))
        check("inside a loop: scheduled and judged", asyncio.run(sched()) is True and len(rows(goal_offer.set_down_log_path())) == n + 1)
        goal_offer.SET_DOWN_LIVE = False
        check("kill switch: no field, no parse, no scheduling", goal_offer.set_down_schema(True) == "" and goal_offer.parse_set_down({"set_down": GOOD}) == "" and goal_offer.set_down_later(goal, GOOD, "t", "c") is False)
        goal_offer.SET_DOWN_LIVE = True

    node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
    check("node: the field is added only on an offered tick", "_go_s.set_down_schema(_sd_on)" in node and "_sd_on = bool(getattr(self, \"_goal_offered\", None))" in node)
    check("node: parsed only on an offered tick", "_go_p.parse_set_down(data) if getattr(self, \"_goal_offered\", None) else \"\"" in node)
    check("node: the offered goal is cleared every tick", "self._goal_offered = None     # Layered goals Phase 6" in node)
    check("node: a set-down is scheduled, never awaited", "_go_sd.set_down_later(_g_off, set_down_v, thought" in node and "await _go_sd" not in node)

    print("\n%s (%d failed)" % ("ALL OK" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

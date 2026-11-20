"""Hermetic test for Layered Goals Phase 6, remainder (D-0768, J-3990): the what-changed record, the stalled
observation (restates or standing off the driving question), set-down for the pursuit RETURN.
Temp dir only; the judge is a stub; no live store and no model is touched.
Run: python scripts/_test_layered_goals_phase6b.py"""
import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import goals, goal_offer, goal_change   # noqa: E402

FAILS = []
ROOT = Path(__file__).resolve().parent.parent


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def w(root, rel, obj):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def pur(pid, question, standing, adv, res, status="active"):
    return {"id": pid, "question": question, "standing": standing, "advances": adv, "restates": res,
            "status": status, "born": time.time() - 9000, "last_touched": time.time() - 60, "heat": 0.5,
            "thoughts": [], "established": [], "centroid": None, "recent_vecs": []}


def main():
    t0 = time.time()
    goal_change.WHAT_CHANGED_SHADOW = True
    asked = []

    def judge(answers):
        async def fn(system, user, key):
            asked.append((key, user))
            return answers.get(key, (False, "no", None, 0.0))
        return fn

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        goals._DATA = root
        goals._assignment = lambda: (None, None)
        goal_offer._school_time = lambda: False
        goal_offer._where = lambda: None
        goal_offer._log_injection = lambda *a: None
        goal_change._ask_fn = judge({})
        for f, v in (("intentions.json", {"open": []}), ("commitment_active.json", []),
                     ("deferred_intentions.json", {"intentions": []}), ("frontier.light.json", {"open": []}),
                     ("frontier.json", {"questions": []})):
            w(root, f, v)

        # ---- stalled, by observation: restates, or a standing that no longer touches the question ----
        Q = "Does naming a thing change its nature?"
        P = [pur("a", Q, "Naming a thing changes its nature only through how others treat it.", 4, 1),
             pur("b", Q, "Naming a thing changes its nature only through how others treat it.", 3, 4),
             pur("c", Q, "Granite weathers slowly under repeated freezing in alpine rock faces overnight.", 5, 0),
             pur("d", Q, "Granite weathers slowly under repeated freezing.", 2, 0)]
        w(root, "pursuits_active.json", P)
        by = {g["ref"]["key"]: g for g in goals.build(t0)}
        st = {k: (by[k]["progress"]["stalled"], by[k]["progress"]["stalled_why"]) for k in by}
        check("healthy pursuit is not stalled", st["a"] == (False, []), st["a"])
        check("mostly restates: stalled, why=restates", st["b"] == (True, ["restates"]), st["b"])
        check("standing off the driving question: stalled, why=standing_off_question",
              st["c"] == (True, ["standing_off_question"]), st["c"])
        check("too few advances to call it off the question", st["d"][0] is False, st["d"])
        check("the flag changes no state", all(by[k]["state"] == "held" for k in ("a", "b", "c", "d")))

        goals.tick(t0)
        goal_offer._reg_cache = None
        n0 = sum(1 for r in rows(goals.log_path()) if r["event"] == "stalled")
        check("first tick: no 'stalled' transition rows (nothing to transition from)", n0 == 0, n0)
        P[0]["restates"] = 6
        w(root, "pursuits_active.json", P)
        goals.tick(t0 + 700)
        ev = [r for r in rows(goals.log_path()) if r["event"] == "stalled"]
        check("a goal turning stalled is logged once, with why",
              len(ev) == 1 and ev[0]["id"] == "pursuit:a" and ev[0]["why"] == ["restates"], ev)
        goals.tick(t0 + 1400)
        check("and not logged again while it stays stalled",
              len([r for r in rows(goals.log_path()) if r["event"] == "stalled"]) == 1)

        # ---- what changed: a held pursuit ends capped; the standing position at the end is captured ----
        ended_standing = "A name changes how it is treated, not what it is made of; whether that is its nature is open."
        P2 = [pur("a", Q, "x", 4, 6), pur("b", Q, "y", 3, 4), pur("c", Q, "z granite", 5, 0),
              pur("d", Q, "w", 2, 0, status="saturated")]
        P2[3]["standing"] = ended_standing
        w(root, "pursuits_active.json", P2)
        goal_change._ask_fn = judge({"position": (True, "now holds a stance", None, 0.1),
                                     "distinction": (True, "treated vs made of", None, 0.1)})
        gl = goals._read_json(goals.register_path(), {})
        d_old = next(g for g in gl["goals"] if g["id"] == "pursuit:d")
        check("the pursuit d was held before it ended", any(s["state"] == "held" for s in d_old["states"]), d_old["states"])
        asked.clear()
        goals.tick(t0 + 2100)
        for t in list(goal_change._threads):
            t.join(20)
        wc = rows(goal_change.log_path())
        check("an ended held goal gets one what-changed row", len(wc) == 1 and wc[0]["id"] == "pursuit:d", wc)
        r = wc[0] if wc else {}
        check("recorded = position (fixed order), all true kinds kept, end taken from the standing",
              r.get("recorded") == "position" and r.get("kinds") == ["position", "distinction"]
              and r.get("end_source") == "standing" and r.get("end") == ended_standing, r)
        check("the judge saw first wording and where it stood",
              asked and "FIRST WORDING: " + Q in asked[0][1] and "WHERE IT STOOD AT THE END: " + ended_standing in asked[0][1])
        check("the register's ended list carries the standing",
              any(e.get("ended_standing") == ended_standing for e in goals._read_json(goals.register_path(), {}).get("ended", [])))
        check("shadow: the other pursuits keep their state",
              all(x["state"] == "held" for x in goals._read_json(goals.register_path(), {})["goals"] if x["kind"] == "pursuit"))

        # ---- the judge function on its own ----
        rec = {"id": "question:z", "kind": "question", "first": "Why is the sky dark at night?",
               "end": "Why is the sky dark at night?", "end_source": "last_wording", "how_ended": "lapsed",
               "why_ended": "frontier faded", "note": "", "reworded": False}
        row = asyncio.run(goal_change.judge_one(rec))
        check("same words: nothing, with no model call", row["recorded"] == "nothing" and row["how"] == "identical")
        rec2 = dict(rec, end="Whether the dark depends on the finite age of the stars, not their number.")
        goal_change._ask_fn = judge({})
        row = asyncio.run(goal_change.judge_one(rec2))
        check("all three no: nothing", row["recorded"] == "nothing" and row["kinds"] == [] and row["unjudged"] == [], row)
        goal_change._ask_fn = judge({"reframing": (True, "different question", None, 0.1)})
        row = asyncio.run(goal_change.judge_one(rec2))
        check("one yes: that kind", row["recorded"] == "reframing" and row["kinds"] == ["reframing"], row)

        async def down(system, user, key):
            return (None, None, "timeout", 1.0)
        goal_change._ask_fn = down
        row = asyncio.run(goal_change.judge_one(rec2))
        check("judge down: recorded None, all three unjudged",
              row["recorded"] is None and row["unjudged"] == list(goal_change.KINDS), row)

        async def boom(system, user, key):
            raise RuntimeError("x")
        goal_change._ask_fn = boom
        row = asyncio.run(goal_change.judge_one(rec2))
        check("judge raising never propagates", row["recorded"] is None and len(row["unjudged"]) == 3)
        sysall = " ".join(goal_change.SYSTEMS.values())
        check("the judge is told not to rule on right or wise",
              "whether the mind was right" in sysall and "stopping was wise" in sysall)

        # ---- eligibility, burst cap, kill switch ----
        check("a never-held candidate is not compared", goal_change.eligible({"states": [{"state": "candidate"}]}) is False)
        check("a held goal is", goal_change.eligible({"states": [{"state": "candidate"}, {"state": "held"}]}) is True)
        goal_change._ask_fn = judge({})
        before = len(rows(goal_change.log_path()))
        burst = [dict(rec2, id=f"question:b{i}") for i in range(goal_change.MAX_PER_TICK + 2)]
        goal_change.record_later(burst, wait=True)
        new = rows(goal_change.log_path())[before:]
        check("a burst beyond the cap is logged as skipped, not judged",
              len(new) == len(burst) and sum(1 for x in new if x.get("how") == "skipped_burst") == 2, [x.get("how") for x in new])
        goal_change.WHAT_CHANGED_SHADOW = False
        check("kill switch: nothing queued", goal_change.record_later([rec2]) is False)
        goal_change.WHAT_CHANGED_SHADOW = True
        check("stats counts outcomes", goal_change.stats()["rows"] >= 1)

        # ---- set-down for the pursuit RETURN ----
        w(root, "goals.json", {"schema": 1, "ts": t0, "goals": [
            {"id": "pursuit:p1", "kind": "pursuit", "state": "held", "text": Q, "earned": {"recurrences": 3}},
            {"id": "pursuit:p2", "kind": "pursuit", "state": "rested", "text": "Another one"},
            {"id": "pursuit:p3", "kind": "pursuit", "state": "candidate", "text": "Too young"}], "ended": []})
        goal_offer._reg_cache = None
        check("a held pursuit is the offered goal on its RETURN",
              goal_offer.offered_pursuit("p1") == {"id": "pursuit:p1", "text": Q})
        check("a rested or candidate or unknown pursuit is not",
              goal_offer.offered_pursuit("p2") is None and goal_offer.offered_pursuit("p3") is None
              and goal_offer.offered_pursuit("zz") is None)
        check("is_rested_id", goal_offer.is_rested_id("pursuit:p2") is True and goal_offer.is_rested_id("pursuit:p1") is False)
        from core import pursuits
        check("the RETURN leaves a rested pursuit alone",
              pursuits._is_rested({"id": "p2"}) is True and pursuits._is_rested({"id": "p1"}) is False)

        async def jyes(system, user):
            return {"verdict": True, "how": "agreed", "why": "ok"}
        goal_offer._judge = jyes
        note = ("I got as far as seeing the treatment follows the name rather than the stuff; "
                "what the nature of it is stays open for now.")
        r = asyncio.run(goal_offer._set_down({"id": "pursuit:p1", "text": Q}, note, "t", "c"))
        store = json.loads(goal_offer.set_down_path().read_text(encoding="utf-8"))
        check("a pursuit's accepted note is stored like any other goal's", r["accepted"] is True and "pursuit:p1" in store, store)
        w(root, "pursuits_active.json", [pur("p1", Q, "Naming changes treatment.", 3, 0)])
        goals.tick(t0 + 3000)
        goal_offer._reg_cache = None
        g = next(x for x in goals._read_json(goals.register_path(), {})["goals"] if x["id"] == "pursuit:p1")
        check("the register rests the pursuit; the RETURN then skips it",
              g["state"] == "rested" and pursuits._is_rested({"id": "p1"}) is True, g.get("state"))
        goal_offer._judge = None

    node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
    check("node: the RETURN sets the offered goal", "_go_pr.offered_pursuit(_rs[1])" in node and "self._goal_offered = _pg" in node)
    check("node: the frontier seed honours a rested question", '_go_r.is_rested_text(_seed.get("q") or "")' in node)
    gsrc = (ROOT / "core" / "goals.py").read_text(encoding="utf-8")
    check("goals: the what-changed pass is handed off, never run on the tick thread",
          "goal_change.record_later(recs)" in gsrc and "asyncio" not in gsrc)

    print("\n%s (%d failed)" % ("ALL OK" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

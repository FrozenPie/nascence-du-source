"""Hermetic test for core/goal_offer.py (Layered Goals Phase 1). Temp dir only; no live store is read or written.
Run: python scripts/_test_layered_goals_phase1.py"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import goals, goal_offer   # noqa: E402
from core import curiosity_progress as _cpm   # noqa: E402
_cpm.LINE_STATE_PROGRESS = False   # J-4084: this test pins the J-3985 pursuit-counter readers (flag off); the line-state path is in scripts/line_state_progress_test.py

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def w(root, rel, obj, jsonl=False):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in obj) if jsonl else json.dumps(obj), encoding="utf-8")


def pursuits(t0, a1, a2):
    return [{"id": "p1", "status": "active", "question": "Why do hares not dig nests?", "advances": a1, "restates": 0,
             "born": t0 - 36000, "last_touched": t0 - 100, "cycle_id": "aaaa1111-x"},
            {"id": "p2", "status": "active", "question": "What does the tide leave behind?", "advances": a2, "restates": 0,
             "born": t0 - 7200, "last_touched": t0 - 50, "cycle_id": "bbbb2222-x"}]


def main():
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        goals._DATA = root
        goals._assignment = lambda: ("b1", "Buller Vol 1")
        goal_offer._school_time = lambda: False
        goal_offer._where = lambda: None
        w(root, "intentions.json", {"open": [{"key": "move|sea", "family": "move", "object": "sea", "deed": "walk to the sea",
                                              "reason": "place:down on the shore", "ts": t0 - 600, "renewed_ts": t0 - 600,
                                              "renewals": 0, "reminders": 1}], "done": [], "dropped": [], "lapsed": []})
        w(root, "intentions_log.jsonl", [{"ts": t0 - 9000 - i, "event": "done" if i < 6 else "lapsed", "key": "move|x"} for i in range(8)], jsonl=True)
        w(root, "commitment_active.json", [{"id": "s1", "statement": "I hold to small acts.", "held_since": t0 - 900, "load_bearing": True}])
        w(root, "pursuits_active.json", pursuits(t0, 10, 4))
        w(root, "pursuits_judged.jsonl", [{"pursuit_id": "p1", "verdict": True}] * 7 + [{"pursuit_id": "p1", "verdict": False}] * 3
          + [{"pursuit_id": "p2", "verdict": True}], jsonl=True)
        w(root, "frontier.light.json", {"open": [{"id": "q1", "q": "How does altitude shape shelter?", "encounters": 3, "born": t0 - 4000, "last_seen": t0 - 30}]})
        w(root, "frontier.json", {"questions": []})
        w(root, "deferred_intentions.json", {"intentions": []})
        w(root, "concerns_log.jsonl", [], jsonl=True)

        goals.tick(t0)
        rows = [json.loads(x) for x in goal_offer.log_path().read_text(encoding="utf-8").splitlines()]
        r = rows[-1]
        tab = {g["id"]: g for g in r["goals"]}
        check("one offer row per register pass", len(rows) == 1)
        check("importance = judged advances only", tab["pursuit:p1"]["importance"] == 7 and tab["pursuit:p2"]["importance"] == 1, (tab["pursuit:p1"]["importance"], tab["pursuit:p2"]["importance"]))
        check("importance is None where no judge has ruled", tab["stand:s1"]["importance"] is None and tab["question:q1"]["importance"] is None)
        check("expectancy only for a deed with a deadline, from his own record", tab["intention:move|sea"]["expectancy"] == 0.75 and tab["pursuit:p1"]["expectancy"] is None, tab["intention:move|sea"])
        check("cost kept apart from importance", tab["pursuit:p1"]["cost"]["age_h"] == 10.0 and "cost" in tab["stand:s1"])
        check("place cue is not guessed: not evaluated, not eligible", tab["intention:move|sea"]["eligible"] is False and "not evaluated" in tab["intention:move|sea"]["why"])
        check("book ineligible outside school time", [g for g in r["goals"] if g["kind"] == "project"][0]["eligible"] is False)
        check("held goals with no cue are eligible", set(r["eligible"]) == {"stand:s1", "pursuit:p1", "pursuit:p2", "question:q1"}, r["eligible"])
        p = r["policies"]["softmax"]["p"]
        check("softmax probabilities logged for every eligible goal and sum to 1", set(p) == set(r["eligible"]) and abs(sum(p.values()) - 1) < 1e-3, p)
        sc = r["policies"]["softmax"]["score"]
        check("undefined components are left out, not counted as zero", sc["stand:s1"] == 0.0 and sc["question:q1"] == 0.0 and sc["pursuit:p1"] > sc["pursuit:p2"], sc)
        check("baselines present", r["policies"]["uniform"]["p_each"] == 0.25 and r["policies"]["most_recent"]["pick"] == "question:q1", r["policies"])
        check("silence arm logged with its probability", r["policies"]["silence"]["p"] == goal_offer.P_SILENCE and isinstance(r["policies"]["silence"]["drawn"], bool))
        check("seed logged", isinstance(r["seed"], int))
        check("first pass: standing is the top goal, no switch", r["challenger"]["standing_rule"] == "pursuit:p1" and r["challenger"]["switched_rule"] is False)

        # second pass: p2 advances fast -> a challenger appears; the anchor offered the question twice
        w(root, "pursuits_active.json", pursuits(t0, 10, 9))
        w(root, "pursuits_judged.jsonl", [{"pursuit_id": "p1", "verdict": True}] * 7 + [{"pursuit_id": "p2", "verdict": True}] * 30, jsonl=True)
        w(root, "concerns_log.jsonl", [{"ts": t0 + 100, "source": "frontier", "text": "How does altitude shape shelter?"},
                                         {"ts": t0 + 200, "source": "frontier", "text": "How does altitude shape shelter?"},
                                         {"ts": t0 + 300, "source": "curriculum", "text": "working through 'Buller Vol 1'"},
                                         {"ts": t0 - 5000, "source": "frontier", "text": "too old to count"}], jsonl=True)
        goals.tick(t0 + 600)
        r2 = json.loads(goal_offer.log_path().read_text(encoding="utf-8").splitlines()[-1])
        tab2 = {g["id"]: g for g in r2["goals"]}
        check("progress since the last pass is what he acted on", r2["actual"]["acted_on"] == ["pursuit:p2"], r2["actual"])
        check("recent rate and ratio computed from the register's own log", tab2["pursuit:p2"]["rate_per_h"] is not None and tab2["pursuit:p2"]["rate_ratio"] is not None and tab2["pursuit:p1"]["rate_per_h"] == 0.0, tab2["pursuit:p2"])
        check("real anchor offers matched to goal ids", r2["actual"]["anchor_offers"] == 3 and r2["actual"]["anchor_goal_ids"].get("question:q1") == 2 and any(k.startswith("project:") for k in r2["actual"]["anchor_goal_ids"]), r2["actual"])
        check("challenger seen once: rule holds the standing offer, no-rule switches", r2["challenger"]["top_now"] == "pursuit:p2" and r2["challenger"]["standing_rule"] == "pursuit:p1" and r2["challenger"]["switched_no_rule"] is True and r2["challenger"]["switched_rule"] is False, r2["challenger"])
        goals.tick(t0 + 1200)
        r3 = json.loads(goal_offer.log_path().read_text(encoding="utf-8").splitlines()[-1])
        check("challenger seen twice running: the rule switches", r3["challenger"]["standing_rule"] == "pursuit:p2" and r3["challenger"]["switched_rule"] is True, r3["challenger"])
        reg = json.loads(goals.register_path().read_text(encoding="utf-8"))
        check("offer state carried in the register", reg["offer_state"]["standing"] == "pursuit:p2")
        st = goal_offer.stats()
        check("stats reader", st["rows"] == 3 and st["switches_no_rule"] == 1 and st["switches_rule"] == 1 and st["rows_with_eligible"] == 3, st)

        # school time makes the book eligible; kill switch; a broken offer pass never costs the register its save
        goal_offer._school_time = lambda: True
        goals.tick(t0 + 1800)
        r4 = json.loads(goal_offer.log_path().read_text(encoding="utf-8").splitlines()[-1])
        check("book eligible in school time", any(i.startswith("project:") for i in r4["eligible"]))
        goal_offer.GOAL_OFFER_SHADOW = False
        n_before = len(goal_offer.log_path().read_text(encoding="utf-8").splitlines())
        goals.tick(t0 + 2400)
        check("kill switch: no offer row, register still saved", len(goal_offer.log_path().read_text(encoding="utf-8").splitlines()) == n_before and json.loads(goals.register_path().read_text(encoding="utf-8"))["ts"] == t0 + 2400)
        goal_offer.GOAL_OFFER_SHADOW = True
        orig = goal_offer.shadow_pass
        goal_offer.shadow_pass = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        goals.tick(t0 + 3000)
        goal_offer.shadow_pass = orig
        check("offer pass failure does not block the register", json.loads(goals.register_path().read_text(encoding="utf-8"))["ts"] == t0 + 3000)

        # ---- J-3985: progress for questions, evidence for stands, checkable place cues ----
        goal_offer._school_time = lambda: False
        fq = [{"id": "q1", "q": "How does altitude shape shelter?", "encounters": 3, "born": t0 - 4000, "last_seen": t0 - 30,
               "status": "open", "new_fragments": 2, "finding": "a page on tussock", "consecutive_stalls": 0, "last_pursued_ts": t0 - 900},
              {"id": "q3", "q": "Does naming a thing change it?", "encounters": 2, "born": t0 - 8000, "last_seen": t0 - 60,
               "status": "open", "new_fragments": 0, "consecutive_stalls": 3, "last_pursued_ts": t0 - 500},
              {"id": "q4", "q": "Is waiting a form of action?", "encounters": 2, "born": t0 - 300, "last_seen": t0 - 20, "status": "open"}]
        w(root, "frontier.json", {"questions": fq})
        w(root, "frontier.light.json", {"open": [{k: v for k, v in q.items() if k in ("id", "q", "encounters", "born", "last_seen", "status")} for q in fq]})
        w(root, "commitment_active.json", [{"id": "s1", "statement": "I hold to small acts.", "held_since": t0 - 900, "load_bearing": True, "drop_denied": 4}])
        w(root, "commitment_second_look_shadow.jsonl", [{"stand_id": "s1", "second_look": "insight"}, {"stand_id": "s1", "second_look": "commitment"},
                                                          {"stand_id": "zz", "second_look": "insight"}], jsonl=True)
        goal_offer._where = lambda: "shore"
        goals.tick(t0 + 3600)
        r5 = json.loads(goal_offer.log_path().read_text(encoding="utf-8").splitlines()[-1])
        t5 = {g["id"]: g for g in r5["goals"]}
        check("question learning progress read from the heavy frontier", t5["question:q1"]["lp"] == 3.0 and t5["question:q1"]["has_finding"] is True, t5["question:q1"])
        check("stalled question scores negative and is flagged parked", t5["question:q3"]["lp"] == -3.0 and t5["question:q3"]["parked"] is True, t5["question:q3"])
        check("a question never pursued has no learning progress (None, not 0)", t5["question:q4"]["lp"] is None, t5["question:q4"])
        check("learning progress is not given to other kinds", t5["stand:s1"]["lp"] is None and t5["pursuit:p1"]["lp"] is None)
        s5 = r5["policies"]["softmax"]["score"]
        check("questions now differ in score", s5["question:q1"] > s5["question:q4"] > s5["question:q3"] and s5["question:q4"] == 0.0, s5)
        check("stand evidence: last second look wins, denied drops kept under cost", t5["stand:s1"]["second_look"] == "commitment" and t5["stand:s1"]["cost"]["drop_denied"] == 4, t5["stand:s1"])
        check("stand evidence does not enter the score", s5["stand:s1"] == 0.0 and t5["stand:s1"]["importance"] is None)
        check("place cue present when he is there", t5["intention:move|sea"]["eligible"] is True and t5["intention:move|sea"]["why"] == "cue present: at shore", t5["intention:move|sea"])
        # D-0767: a stand the second look rules "insight" is a candidate, not held
        w(root, "commitment_active.json", [
            {"id": "s1", "statement": "I hold to small acts.", "held_since": t0 - 900, "load_bearing": True, "drop_denied": 4},
            {"id": "s7", "statement": "The crabs shift their defences with the pressure.", "held_since": t0 - 200, "load_bearing": True},
            {"id": "s8", "statement": "I will write to Travis today.", "held_since": t0 - 200, "load_bearing": True},
            {"id": "s9", "statement": "Perhaps I should rest.", "held_since": t0 - 200, "load_bearing": True}])
        w(root, "commitment_second_look_shadow.jsonl", [{"stand_id": "s1", "second_look": "stand"}, {"stand_id": "s7", "second_look": "insight"},
                                                          {"stand_id": "s9", "second_look": "unclear"}, {"stand_id": "s9", "second_look": None}], jsonl=True)
        gs = {x["id"]: x for x in goals.build(t0 + 3700)}
        check("insight-ruled stand is a candidate", gs["stand:s7"]["state"] == "candidate" and gs["stand:s7"]["evidence"]["held_blocked_by"] == "second_look:insight", gs["stand:s7"])
        check("stand, unclear and unlooked stands stay held", all(gs["stand:" + k]["state"] == "held" for k in ("s1", "s8", "s9")), {k: gs["stand:" + k]["state"] for k in ("s1", "s8", "s9")})
        goals.STAND_INSIGHT_IS_CANDIDATE = False
        check("switch off: the ledger flag alone decides", {x["id"]: x for x in goals.build(t0 + 3700)}["stand:s7"]["state"] == "held")
        goals.STAND_INSIGHT_IS_CANDIDATE = True
        goal_offer._where = lambda: "study"
        goals.tick(t0 + 4200)
        r_ins = json.loads(goal_offer.log_path().read_text(encoding="utf-8").splitlines()[-1])
        check("an insight-ruled stand is not in the eligible set", "stand:s7" not in r_ins["eligible"] and "stand:s8" in r_ins["eligible"], r_ins["eligible"])
        r6 = json.loads(goal_offer.log_path().read_text(encoding="utf-8").splitlines()[-1])
        i6 = [g for g in r6["goals"] if g["id"] == "intention:move|sea"][0]
        check("place cue absent when he is elsewhere", i6["eligible"] is False and i6["why"].startswith("cue absent: at study"), i6)
        goal_offer._where = lambda: None
        reg = json.loads(goals.register_path().read_text(encoding="utf-8"))
        gq = next(x for x in reg["goals"] if x["id"] == "question:q1")
        check("register carries the question's progress state", gq["progress"]["lp"] == 3.0 and gq["progress"]["pursued"] is True)

        # pure functions
        check("softmax of nothing is nothing", goal_offer.softmax([]) == [])
        check("z-score leaves undefined undefined", goal_offer._z([1.0, None, 3.0])[1] is None and goal_offer._z([None, 2.0]) == [None, 0.0])

    print("\n%s (%d failed)" % ("ALL OK" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

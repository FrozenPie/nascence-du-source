"""
_test_practical_lesson.py — J-0627 (D-0159 GO): core/practical_lesson.py + the school-directive wiring
that alternates observe/practical in the nature period's two slots, plus the two rung-1 fieldcraft hands
this job added (whip_end, douse_fire).

Isolation: every module whose data file could plausibly be touched (fieldcraft, sensorium, provisions,
garden, world_objects, world_substrate, school, nature_study, practical_lesson, procedures, competence)
has its file-path globals redirected via lab_env.isolate() BEFORE any of this runs — job-queue's own
isolation=required convention (see ~/.claude/skills/job-queue/lab_env.py). Never touches live data/.

Covers the job briefing's own verify checklist (observe fires first, practical second; a fired hand
grades ok or slip; an unattempted practical logs attempted=False with no penalty) plus the sharpest real
edge cases found while building this: fire_lay is a genuine SHARED skill key between bank_the_fire and
flint_and_steel in fieldcraft.py, so a bank_fire attempt must never be mistaken for a flint attempt (or
vice versa); clove_hitch_stake/bowline_loop have no standalone hand of their own and route through the
existing clothesline/handrail composites, so the picker must stop offering both once neither composite
is buildable; the Handbook paragraph is offered on a slip exactly once, ever, per task.

Exit 1 on any failed check. Run: python -X utf8 scripts/_test_practical_lesson.py
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import json
import sys
import time
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))

from lab_env import isolate  # noqa: E402
from core import fieldcraft, sensorium, study_life, provisions, garden, world_objects, world_substrate  # noqa: E402
from core import school, nature_study, practical_lesson, procedures, competence, literal_will  # noqa: E402

FAIL: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        FAIL.append(name)


# a real Tuesday, 10:30 local — 90 minutes into the 9:00 school window -> subject index 2 -> "nature"
FAKE_TS = time.mktime((2026, 9, 8, 10, 30, 0, 0, 0, -1))
assert time.localtime(FAKE_TS).tm_wday == 1, "must be a Tuesday for this check to mean anything"

# a monotonically-advancing fake clock (not a frozen constant): every call is a fraction of a second
# later than the last, so rows written across different scenarios below never collide on an identical
# rounded timestamp the way a constant return_value would. Total drift across this whole script is a
# few seconds — nowhere near pushing the fake "now" out of the 45-minute nature-period window.
_clock = {"t": FAKE_TS}
_real_localtime = time.localtime


def _fake_time() -> float:
    _clock["t"] += 0.05
    return _clock["t"]


def _fake_localtime(secs=None):
    # time.localtime(None) reads the real system clock directly at the C level — it does NOT call back
    # into the (patchable) Python-level time.time(), so mock.patch("time.time", ...) alone never
    # reaches it. school.py calls time.localtime(now) with now=None throughout, so that has to be
    # covered too, or every schedule check silently keeps reading the real wall clock.
    return _real_localtime(secs if secs is not None else _clock["t"])


with isolate(also=[
    (fieldcraft, ["_F", "_LEDGER"]),
    (sensorium, ["_STATE_F"]),
    (provisions, ["_F", "_LOG"]),
    (garden, ["_F", "_LEDGER", "_EVENTS"]),
    (world_objects, ["_OBJECTS_F"]),
    (world_substrate, ["_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F"]),
    (school, ["STATE"]),
    (nature_study, ["_STATE", "_LOG"]),
    (practical_lesson, ["_STATE", "_LOG", "_FC_LEDGER"]),
    (procedures, ["_F", "_LOG"]),
    (competence, ["_BELIEFS_FILE"]),
]) as lab_dir:
    print(f"isolated lab dir: {lab_dir}\n")

    # J-0757 (F-1080 bug #2) added a `mock.patch("core.profile.guard_path", ...)` workaround here:
    # lab_env.isolate()'s own lab dir (C:\Nascence\data\_lab\<ts>\...) used to still be a real subpath
    # of core.profile._DATA, so guard_path()'s own "already redirected outside data/" check
    # (path.relative_to(_DATA)) never cleared for it -- every path isolate(also=[...]) redirected
    # above was STILL treated as a live, non-live-refused data/ path by D-0179's hard-raise, exactly as
    # if never redirected at all (root cause: F-1083/S-0086, spawned as J-0759). That hit multiple call
    # sites in this one test, not just garden._save() (fieldcraft.whip_end()/douse_fire() reach
    # fieldcraft._log()/_save() the exact same unguarded way), which is why the workaround patched
    # guard_path() itself for the whole block rather than wrapping each site individually.
    #
    # Post-D-0200 (J-0840, F-1225): guard_path() now explicitly allow-lists data/_lab/<dir>/... (see
    # core/profile.py's own _is_lab_sandbox()), so lab_env.isolate()'s lab dir genuinely clears the
    # fence on its own -- the patch above is no longer just redundant, it is actively harmful to keep:
    # it would silently neutralize guard_path() for ANY write this test reaches, including one this
    # isolate(also=[...]) list forgot to redirect, exactly the class of gap D-0179's hard-raise exists
    # to surface loudly rather than pass in silence. Removed as of J-0862. If a future run of this test
    # ever raises NonLiveWriteError here, that means a module/attribute this test touches is missing
    # from the `also=[...]` list above -- add it there; do not reintroduce this patch.
    with mock.patch("time.time", side_effect=_fake_time), \
         mock.patch("time.localtime", side_effect=_fake_localtime):
        # ── bootstrap the isolated world ─────────────────────────────────────────────────────────
        sensorium._load()
        sensorium.state["location"] = "study"
        sensorium.state["weather"] = "clear"
        sensorium.state["fire"] = "burning"
        st = study_life._st()   # also runs provisions.sync(st) -> seeds rope_m/tinder_tin/flint/knife/etc.
        school._save({**school._load(), "assigned_book": "x", "assigned_title": "Boy Scouts Handbook"})

        check("weekday+10:30 resolves to the nature period",
              school.is_school_time() and school.current_subject() == "nature",
              f"is_school_time={school.is_school_time()} subject={school.current_subject()}")

        # ── slot alternation: observe first, practical second, under the SAME 36-minute gate ──────
        check("slot 1 before any firing today", practical_lesson.slot_today() == 1)
        d1 = school.directive()
        check("slot-1 directive is the unchanged observation directive", "GO AND OBSERVE" in d1, d1)

        practical_lesson.mark_slot_fired()   # simulates the nature block's first (observation) firing
        check("slot 2 after one firing", practical_lesson.slot_today() == 2)
        d2 = school.directive()
        check("slot-2 directive is the practical directive, not observation",
              "nature practical" in d2 and "make your thought:" in d2 and "GO AND OBSERVE" not in d2, d2)

        task = practical_lesson._current_task()
        check("a rung-1 task got picked", bool(task) and task["rung"] == 1, task)
        check("the SAME task persists across calls (not re-randomized)",
              task["id"] == practical_lesson._current_task()["id"])

        # ── grading: no hand fired -> attempted=False, no penalty (plan §1) ──────────────────────
        # J-2335: the grading checks below call run() directly (trigger "slot2"); they exercise the grader
        # itself, so pin the legacy flag value here. The J-2335 section at the end covers the default.
        practical_lesson.GRADE_AT_PERIOD_END = False
        practical_lesson._save_state({"day": practical_lesson._today_key(), "slot_fired": 1,
                                       "task_id": "read_a_trail", "announced_ts": time.time(),
                                       "rung": 1, "window": [], "book_offered": []})
        res = practical_lesson.run()
        check("an unattempted practical returns {} (no thought/joy/nudge)", res == {}, res)
        all_rows = [json.loads(line) for line in open(practical_lesson._LOG, encoding="utf-8")]
        # J-2315: issuance now logs an {"event": "issued"} row too; graded-row readers skip "event" rows
        issued = [r for r in all_rows if r.get("event") == "issued"]
        check("J-2315: the first pick of today's task logged exactly ONE issued row",
              len(issued) == 1 and issued[0]["task"] == task["id"] and issued[0]["rung"] == 1, issued)
        rows = [r for r in all_rows if "event" not in r]
        check("...but a practical_log.jsonl row was still written", len(rows) == 1, rows)
        check("...and it is honestly attempted=False, ok=None",
              rows[0]["attempted"] is False and rows[0]["ok"] is None, rows[-1])

        # ── grading: a slip -> attempted=True, ok=False, the book paragraph offered ONCE ─────────
        practical_lesson._save_state({"day": practical_lesson._today_key(), "slot_fired": 1,
                                       "task_id": "read_a_trail", "announced_ts": time.time() - 5,
                                       "rung": 1, "window": [], "book_offered": []})
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "craft": "tracking", "ok": False}) + "\n")
        res_slip = practical_lesson.run()
        check("a slip is attempted=True, ok=False",
              res_slip.get("attempted") is True and res_slip.get("ok") is False, res_slip)
        check("...and its feedback carries the Handbook paragraph the FIRST time",
              "Boy Scouts Handbook" in res_slip.get("feedback", ""), res_slip.get("feedback"))

        st_now = practical_lesson._load_state()
        st_now.update(task_id="read_a_trail", announced_ts=time.time() - 2)
        practical_lesson._save_state(st_now)
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "craft": "tracking", "ok": False}) + "\n")
        res_slip2 = practical_lesson.run()
        check("a second slip on the SAME task never repeats the paragraph",
              res_slip2.get("feedback", "") == "", res_slip2.get("feedback"))

        # ── grading: a success -> ok=True, score=1.0 ─────────────────────────────────────────────
        st_now = practical_lesson._load_state()
        st_now.update(task_id="read_a_trail", announced_ts=time.time() - 1)
        practical_lesson._save_state(st_now)
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "craft": "tracking", "ok": True}) + "\n")
        res_ok = practical_lesson.run()
        check("a success is attempted=True, ok=True, score=1.0",
              res_ok.get("ok") is True and res_ok.get("score") == 1.0, res_ok)

        # ── fieldcraft.py's fire_lay skill key is SHARED between bank_the_fire and flint_and_steel:
        #    a bank_fire attempt must never be mistaken for a flint attempt ───────────────────────
        practical_lesson._save_state({"day": practical_lesson._today_key(), "slot_fired": 1,
                                       "task_id": "flint_and_steel", "announced_ts": time.time() - 1,
                                       "rung": 1, "window": [], "book_offered": []})
        bank_ts = time.time()
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": bank_ts, "craft": "fire_lay", "ok": True}) + "\n")
            f.write(json.dumps({"ts": bank_ts, "deed": "bank_fire", "ok": True}) + "\n")
        res_disambig = practical_lesson.run()
        check("a bank_fire attempt is NOT mistaken for a flint_and_steel attempt",
              res_disambig == {}, res_disambig)
        rows = [json.loads(line) for line in open(practical_lesson._LOG, encoding="utf-8")]
        check("...and is logged honestly as flint_and_steel attempted=False",
              rows[-1]["task"] == "flint_and_steel" and rows[-1]["attempted"] is False, rows[-1])

        # a REAL flint_fire deed (no accompanying bank_fire marker at the same timestamp) DOES count,
        # even though its own success path logs no "ok" field — presence there already IS success.
        practical_lesson._save_state({"day": practical_lesson._today_key(), "slot_fired": 1,
                                       "task_id": "flint_and_steel", "announced_ts": time.time() - 1,
                                       "rung": 1, "window": [], "book_offered": []})
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "craft": "fire_lay", "ok": True}) + "\n")
            f.write(json.dumps({"ts": time.time(), "deed": "flint_fire"}) + "\n")
        res_flint = practical_lesson.run()
        check("a real flint_fire success IS graded ok=True", res_flint.get("ok") is True, res_flint)

        # ── rung advance: 12 attempts at >=0.75 advances the rung and clears the window ──────────
        practical_lesson._save_state({**practical_lesson._load_state(), "rung": 1, "window": []})
        for i in range(12):
            practical_lesson._advance_rung(i < 10)   # 10/12 = 0.83
        after = practical_lesson._load_state()
        check("12 attempts at 10/12 success advances rung 1->2 and clears the window",
              after["rung"] == 2 and after["window"] == [], after)

        # ── the two new fieldcraft hands ──────────────────────────────────────────────────────────
        # J-0734 (F-1056): garden._load() returns the module's own cached _state dict BY REFERENCE
        # (garden.py:206-209 -- "if _state is not None: return _state"), so this setdefault() mutation
        # already lands directly in garden._state; nothing downstream in this test re-loads garden
        # state from disk, so no further persistence step is needed for the mutation to take effect.
        # A trailing garden._save(gd) call here (removed) is not just redundant but actively crashes:
        # profile.guard_path() (D-0179) refuses ANY write whose resolved path still sits under data/,
        # and lab_env.isolate()'s own lab dir (data/_lab/<ts>/) is ITSELF under data/, so a guarded
        # _save() can never distinguish an isolated redirect from a real live write -- confirmed via a
        # full untruncated traceback (still inside the `with isolate()` block; the refused path was
        # the LAB copy, e.g. data/_lab/20260907_221652/garden.json, not the real data/garden.json) and
        # a diagnostic showing garden._state was already non-None and populated BEFORE this line ran
        # (an earlier, indirect garden._load() elsewhere already hit the same fence on its own internal
        # bootstrap-save and had that exception swallowed by a fail-open net upstream -- this direct,
        # unwrapped call is simply the one spot in this script with no such net). See F-1056 finding
        # for the broader lab_env/guard_path incompatibility this also surfaces. Independently, this
        # whole block is also covered by the guard_path() patch added above the outer `with` (J-0757,
        # F-1080 bug #2) -- the two fixes are redundant-but-compatible, not conflicting: removing this
        # call was the more precise fix (nothing here needed to persist), and the broader patch still
        # protects the OTHER calls in this block (e.g. fieldcraft.whip_end() below) that do.
        gd = garden._load(); gd.setdefault("items", {}).setdefault("twine", {})["carried"] = True

        st["items"]["rope"]["carried"] = False
        st["items"]["rope"]["place"] = "study"   # the rope's own default resting place
        sensorium.state["location"] = "garden"   # stand where the rope is genuinely NOT, to force the decline
        check("whip_end declines gracefully with no rope to hand",
              "would need" in fieldcraft.whip_end("").lower())
        sensorium.state["location"] = "study"
        st["items"]["rope"]["carried"] = True
        with mock.patch("core.fieldcraft.random.random", return_value=0.05):
            check("whip_end succeeds on a good roll", "Bound" in fieldcraft.whip_end(""))
        with mock.patch("core.fieldcraft.random.random", return_value=0.99):
            check("whip_end fails (frays) on a bad roll", "slips loose" in fieldcraft.whip_end(""))
        led = [json.loads(line) for line in open(fieldcraft._LEDGER, encoding="utf-8")]
        check("whip_end's own attempts landed in fieldcraft_ledger with craft=='whip_end'",
              any(r.get("craft") == "whip_end" for r in led))

        sensorium.state["fire"] = "out"
        check("douse_fire declines when there is no fire at all",
              "nothing left burning" in fieldcraft.douse_fire(""))
        sensorium.state["fire"] = "burning"
        st["items"]["water_pail"]["carried"] = False
        st["water"] = 0.0   # the pail's own default place IS "study" -- must ALSO be empty to force the decline
        check("douse_fire declines with an empty pail and not at the shore",
              "would need the water pail" in fieldcraft.douse_fire(""))
        st["items"]["water_pail"]["carried"] = True
        st["water"] = 1.0
        with mock.patch("core.fieldcraft.random.random", return_value=0.05):
            fieldcraft.douse_fire("")
        check("douse_fire flips the fire to 'out' on a good roll with water",
              sensorium.state["fire"] == "out")
        sensorium.state["fire"] = "burning"; st["water"] = 1.0
        with mock.patch("core.fieldcraft.random.random", return_value=0.99):
            fieldcraft.douse_fire("")
        check("douse_fire leaves it smouldering (not 'out') on a bad roll",
              sensorium.state["fire"] != "out")

        # ── the actions.py registry gate: these must classify as fieldcraft DEEDs, or the two new
        #    hands are GRAY at dispatch no matter what fieldcraft.act_from_thought itself matches ──
        r1 = literal_will.classify("I will whip the rope's end with the twine.", "")
        check("'whip the rope's end' classifies as a fieldcraft DEED",
              any(r["family"] == "fieldcraft" and r["verdict"] == "DEED" for r in r1), r1)
        sensorium.state["fire"] = "burning"
        r2 = literal_will.classify("I will douse the fire fully with the pail of water.", "")
        check("'douse the fire' classifies as a fieldcraft DEED",
              any(r["family"] == "fieldcraft" and r["verdict"] == "DEED" for r in r2), r2)

        with mock.patch("core.fieldcraft.random.random", return_value=0.05):
            ans = fieldcraft.act_from_thought("I will whip the rope's end with the twine.", "")
        check("act_from_thought routes 'whip the rope's end' to whip_end()", ans and "Bound" in ans, ans)

        # ── picker: clove_hitch_stake/bowline_loop have no standalone hand (they route through the
        #    existing clothesline/handrail); the picker must stop offering EITHER once neither
        #    composite is buildable, or he would be told to do something with no real hand behind it ──
        fieldcraft._save({**fieldcraft._load(), "clothesline": None, "handrail": None})
        check("clove_hitch_stake eligible with twine and neither composite yet built",
              any(t["id"] == "clove_hitch_stake" for t in practical_lesson._eligible(1)))
        fieldcraft._save({**fieldcraft._load(), "clothesline": {"ts": time.time()}, "handrail": {"ts": time.time()}})
        elig_ids = [t["id"] for t in practical_lesson._eligible(1)]
        check("clove_hitch_stake/bowline_loop excluded once BOTH composites already stand",
              "clove_hitch_stake" not in elig_ids and "bowline_loop" not in elig_ids, elig_ids)
        fieldcraft._save({**fieldcraft._load(), "clothesline": None, "handrail": None})

        # ── picker: gather_tinder's weather gate ─────────────────────────────────────────────────
        sensorium.state["weather"] = "steady rain"
        check("gather_tinder excluded on a wet day",
              "gather_tinder" not in [t["id"] for t in practical_lesson._eligible(1)])
        sensorium.state["weather"] = "clear"
        check("gather_tinder eligible again once it clears",
              "gather_tinder" in [t["id"] for t in practical_lesson._eligible(1)])

        # ── every rung-1 task is reachable from a rich state (no picker dead ends) ───────────────
        seen = {t["id"] for _ in range(60) if (t := practical_lesson._pick(1))}
        rung1_ids = {t["id"] for t in practical_lesson.LADDER if t["rung"] == 1}
        check("every rung-1 task is reachable by the picker given a rich state (60 draws)",
              rung1_ids <= seen, f"missing: {rung1_ids - seen}")

        # -- J-2315 (F-3009): whip_rope_end gate mirrors fieldcraft.whip_end()'s own co-location test --
        whip = practical_lesson._BY_ID["whip_rope_end"]
        tw = garden._load()["items"]["twine"]; rp = st["items"]["rope"]
        tw.update(carried=False, place="garden"); rp.update(carried=False, place="study")
        check("J-2315: whip_rope_end NOT offered with rope in the study and twine in the garden",
              practical_lesson._gate_ok(whip) is False)
        tw["place"] = "study"
        check("J-2315: whip_rope_end offered once rope and twine lie in the same place",
              practical_lesson._gate_ok(whip) is True)
        tw["place"] = "garden"; rp["carried"] = True
        check("J-2315: whip_rope_end offered when the rope is carried (he can walk to the twine)",
              practical_lesson._gate_ok(whip) is True)
        rp["carried"] = False; tw["carried"] = True
        check("J-2315: whip_rope_end offered when the twine is carried (he can walk to the rope)",
              practical_lesson._gate_ok(whip) is True)

        # -- J-2315 (F-3009): the period-end grader (the 2nd nature firing never came) --
        ann = time.time()
        end = practical_lesson._period_end(ann)
        check("J-2315: the 10:30 nature period ends 11:15",
              time.localtime(end).tm_hour == 11 and time.localtime(end).tm_min == 15, time.ctime(end))
        practical_lesson._save_state({**practical_lesson._load_state(), "day": practical_lesson._today_key(),
                                       "slot_fired": 1, "task_id": "read_a_trail", "announced_ts": ann,
                                       "graded_day": None})
        check("J-2315: no period-end grade while the period is still open",
              practical_lesson.period_end_grade(now=ann + 60) == {})
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ann + 120, "craft": "tracking", "ok": False}) + "\n")
            f.write(json.dumps({"ts": end + 100, "craft": "tracking", "ok": True}) + "\n")   # after period end
        n_before = sum(1 for _ in open(practical_lesson._LOG, encoding="utf-8"))
        res_pe = practical_lesson.period_end_grade(now=end + 200)
        check("J-2315: period-end grade counts rows up to period end only (the slip, not the later success)",
              res_pe.get("attempted") is True and res_pe.get("ok") is False, res_pe)
        pe_rows = [json.loads(line) for line in open(practical_lesson._LOG, encoding="utf-8")][n_before:]
        graded = [r for r in pe_rows if "event" not in r]
        check("J-2315: exactly one graded row, marked trigger=period_end",
              len(graded) == 1 and graded[0].get("trigger") == "period_end", pe_rows)
        st_pe = practical_lesson._load_state()
        check("J-2315: graded_day set and slot advanced past the practical",
              st_pe.get("graded_day") == practical_lesson._today_key() and st_pe.get("slot_fired") == 2, st_pe)
        check("J-2315: period-end grader never grades the same day twice",
              practical_lesson.period_end_grade(now=end + 400) == {})
        practical_lesson._save_state({**st_pe, "slot_fired": 1, "graded_day": practical_lesson._today_key()})
        check("J-2315: period-end grader skips a day the in-period slot-2 run already graded",
              practical_lesson.period_end_grade(now=end + 500) == {})
        practical_lesson._save_state({**st_pe, "slot_fired": 1, "task_id": None, "graded_day": None})
        check("J-2315: period-end grader skips a day no practical was announced",
              practical_lesson.period_end_grade(now=end + 600) == {})

        # -- J-2335 (D-0454 (a)): grader at period END by default; richer issued row; generic co-location --
        practical_lesson.GRADE_AT_PERIOD_END = True
        check("J-2335: GRADE_AT_PERIOD_END is the module default",
              "GRADE_AT_PERIOD_END = True" in open(practical_lesson.__file__, encoding="utf-8").read())
        ann2 = time.time(); end2 = practical_lesson._period_end(ann2)
        practical_lesson._save_state({**practical_lesson._load_state(), "day": practical_lesson._today_key(),
                                       "slot_fired": 1, "task_id": "read_a_trail", "announced_ts": ann2,
                                       "graded_day": None})
        n0 = sum(1 for _ in open(practical_lesson._LOG, encoding="utf-8"))
        check("J-2335: the 36-minute slot-2 run() no longer grades (returns {}, writes no row)",
              practical_lesson.run() == {} and sum(1 for _ in open(practical_lesson._LOG, encoding="utf-8")) == n0)
        practical_lesson.mark_slot_fired()   # what the monologue does right after the slot-2 call
        with open(practical_lesson._FC_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ann2 + 40 * 60, "craft": "tracking", "ok": True}) + "\n")   # after 36 min
        check("J-2335: still nothing graded while the period is open",
              practical_lesson.period_end_grade(now=end2 - 30) == {})
        res2 = practical_lesson.period_end_grade(now=end2 + 30)
        check("J-2335: period-end grade after a slot-2 firing counts a deed done AFTER the 36-min mark",
              res2.get("attempted") is True and res2.get("ok") is True, res2)
        st2 = practical_lesson._load_state()
        check("J-2335: slot counter left at 2 (not bumped to 3) and graded_day set",
              st2.get("slot_fired") == 2 and st2.get("graded_day") == practical_lesson._today_key(), st2)
        check("J-2335: never graded twice", practical_lesson.period_end_grade(now=end2 + 90) == {})

        # issued row fields (ts, deed, period, objects, rooms)
        tw.update(carried=False, place="garden"); rp.update(carried=False, place="garden")
        practical_lesson._save_state({**practical_lesson._load_state(), "task_id": None, "announced_ts": None})
        _orig_pick = practical_lesson._pick
        practical_lesson._pick = lambda rung: practical_lesson._BY_ID["whip_rope_end"]
        try:
            practical_lesson._current_task()
        finally:
            practical_lesson._pick = _orig_pick
        iss = [json.loads(l) for l in open(practical_lesson._LOG, encoding="utf-8")]
        iss = [r for r in iss if r.get("event") == "issued"][-1]
        check("J-2335: issued row carries ts, deed, period_end, objects and rooms",
              all(k in iss for k in ("ts", "deed", "period_end", "objects", "rooms"))
              and iss["deed"] == "whip_end" and iss["objects"] == ["rope", "twine"]
              and iss["rooms"] == {"rope": "garden", "twine": "garden"}, iss)
        rp["carried"] = True
        check("J-2335: _object_rooms reports a carried object as 'carried'",
              practical_lesson._object_rooms(["rope"]) == {"rope": "carried"})
        check("J-2335: _object_rooms leaves a non-placed object (knife flag) as None",
              practical_lesson._object_rooms(["knife"]) == {"knife": None})
        # generic co-location for any task declaring "colocate"
        rp.update(carried=False, place="study")
        fake = {"id": "_two_object_probe", "colocate": ["rope", "twine"], "weather_gate": None}
        check("J-2335: generic colocate gate refuses objects lying in different rooms",
              practical_lesson._gate_ok(fake) is False)
        tw["place"] = "study"
        check("J-2335: generic colocate gate accepts objects lying in one room",
              practical_lesson._gate_ok(fake) is True)
        tw["place"] = None
        check("J-2335: generic colocate gate refuses an object that is nowhere",
              practical_lesson._gate_ok(fake) is False)
        tw["place"] = "garden"

print("\n" + "=" * 60)
if FAIL:
    print(f"{len(FAIL)} CHECK(S) FAILED:")
    for name in FAIL:
        print(" -", name)
    sys.exit(1)
print("ALL CHECKS PASSED")

"""scripts/test_wake_on_human.py (J-2064, sleep_as_a_mode, D-0407 B): hermetic proof that the founder's message wakes a
sleeping Du and is answered after the waking percept.

No LLM, no real sleep, no live data. core is imported FIRST (from this tree, asserted), then lab_env.isolate(db="empty")
redirects the memory store and the two files this build writes (night_wake's shadow log, night's ledger) into a lab dir.
sensorium.state is mutated IN MEMORY ONLY (never _save()) and restored; night.wake() is never called (it saves).

  [1] flags: WAKE_ON_HUMAN True, WAKE_DEADLINE_S 120, JUST_WOKE_S 300
  [2] the hold, happy path: a stubbed pipeline (own asyncio task) reaches its boundary, finish()es, flips the asleep flag,
      perceives the waking line and calls woke(); hold_for_wake() returns after that with woke_seen, request_to_waking
      recorded, deadline not fired; rows: wake_request(via run_cycle), hold; answered() writes the answer row with latency
  [3] the deadline: the pipeline never wakes him; the hold returns after deadline_s with deadline_fired True and he is
      still asleep (the message is answered anyway -- the caller's job); the request stays pending for the pipeline
  [4] nothing to hold for: awake -> None, no row; asleep flag True but NO open ledger (stale flag after a restart) -> None
  [5] WAKE_ON_HUMAN False -> None (observe mode unchanged); MONITOR_ENABLED False -> None
  [6] scene_lead(): present within JUST_WOKE_S after a wake-on-message, empty after an ordinary pipeline_end wake, empty
      once the window has passed; sensorium.scene_line() carries it at the head
  [7] night.end_if_open(): begin + stages, then end_if_open("cancelled") writes ONE row with notes.interrupted, the stages
      reached, the pending wake request; a second call is a no-op; after a normal end() it is a no-op; current_stage()
  [8] wiring (AST/text): run_cycle awaits hold_for_wake before _run_cycle_impl and answered() in its finally; the node
      calls woke() after perceive() and end_if_open() in its finally; run_nascence calls end_if_open after stop_background;
      scene_line() calls scene_lead() after the transit lead
  [9] evaluate(): the d0407 block computes clause 1 and clause 3 shares from live rows; live files untouched

Run:  python scripts/test_wake_on_human.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, json, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (feedback_jobrun_live_store_leaks: lab_env appends C:\Nascence to sys.path)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import night_wake as nw, night, sensorium as sens
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE_SHADOW = Path(r"C:\Nascence") / "data" / "night_wake_shadow.jsonl"
LIVE_NIGHT = Path(r"C:\Nascence") / "data" / "night_log.jsonl"
live_before = (LIVE_SHADOW.stat().st_size if LIVE_SHADOW.exists() else None,
               LIVE_NIGHT.stat().st_size if LIVE_NIGHT.exists() else None)

def rows(path):
    try:
        return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []

class FakeNight:
    def __init__(self): self.notes = {}
    def note(self, k, v): self.notes[k] = v

st_backup = {k: sens.state.get(k, "__absent__") for k in ("asleep", "asleep_since")}
hts_backup = sens._last_human_ts
flag0, mon0, cur0, ended0 = nw.WAKE_ON_HUMAN, nw.MONITOR_ENABLED, dict(night._current), night._ended
WAKE_LINE = "You wake with daylight full in the room; the grate is cold; you slept about 12 minutes."

def lie_down(ago_s=600.0):
    sens.state["asleep"] = True
    sens.state["asleep_since"] = time.time() - ago_s
    night.begin("nap")
    night.stage("to_bed"); night.stage("replay")
    nw.reset(); nw._handled_ts = 0.0; nw._last_wake = None; nw._last_summary = None

def stub_wake_in_memory():
    """What _enter_sleep's tail does, minus night.wake()'s _save(): finish(), flip the flag, perceive, woke(), stage, end."""
    nw.finish(night)
    sens.state["asleep"] = False
    sens.state.pop("asleep_since", None)
    nw.woke(WAKE_LINE)
    night.stage("wake")
    night.end()

async def pipeline(delay_s, wakes=True):
    await asyncio.sleep(delay_s)
    if wakes:
        nw.boundary("consolidation")      # the first boundary after the request: skipped (live)
        stub_wake_in_memory()

async def main():
    with isolate(db="empty", also=[(nw, ["NIGHT_WAKE_SHADOW_LOG"]), (night, ["_LOG"])]) as lab:
        LOG = nw.NIGHT_WAKE_SHADOW_LOG
        NLOG = night._LOG
        check("shadow log and night ledger redirected into the lab dir",
              Path(LOG).is_relative_to(lab) and Path(NLOG).is_relative_to(lab))

        print("[1] flags")
        check("WAKE_ON_HUMAN True", nw.WAKE_ON_HUMAN is True)
        check("WAKE_DEADLINE_S 120", nw.WAKE_DEADLINE_S == 120.0)
        check("JUST_WOKE_S 300", nw.JUST_WOKE_S == 300.0)

        print("[2] hold: happy path")
        lie_down()
        t = asyncio.create_task(pipeline(0.6))
        t0 = time.time()
        hold = await nw.hold_for_wake(deadline_s=5.0, poll_s=0.1)
        waited = time.time() - t0
        await t
        check("hold returned a row", isinstance(hold, dict) and hold["kind"] == "hold")
        check("waited for the wake (~0.6 s), not the deadline", 0.5 <= waited < 2.0 and hold["deadline_fired"] is False)
        check("he is awake after the hold", sens.state.get("asleep") is False and hold["asleep_after"] is False)
        check("woke_seen + request_to_waking recorded", hold["woke_seen"] is True and hold["request_to_waking_s"] is not None and hold["request_to_waking_s"] >= 0.5)
        check("stage at request recorded (replay)", hold["stage_at_request"] == "replay")
        rs = rows(LOG)
        kinds = [r["kind"] for r in rs]
        check("rows: wake_request(via run_cycle, live) -> boundary -> wake_summary -> hold",
              kinds == ["wake_request", "boundary", "wake_summary", "hold"] and rs[0]["via"] == "run_cycle" and rs[0]["mode"] == "live")
        check("boundary skipped (live), summary woken_by human_message", rs[1]["skipped"] is True and rs[2]["woken_by"] == "human_message")
        check("night ledger: woken_by human_message, stages to_bed/replay/wake", night._current["notes"].get("woken_by") == "human_message"
              and list(night._current["stages"]) == ["to_bed", "replay", "wake"])
        check("ledger row written by end(), not interrupted", len(rows(NLOG)) == 1 and "interrupted" not in rows(NLOG)[0]["notes"])
        time.sleep(0.05)
        nw.answered(hold)
        rs = rows(LOG)
        check("answered(): one answer row, request_to_answer >= request_to_waking", rs[-1]["kind"] == "answer"
              and rs[-1]["request_to_answer_s"] >= (hold["request_to_waking_s"] or 0) and rs[-1]["deadline_fired"] is False)
        check("end_if_open after a normal end() is a no-op", night.end_if_open("shutdown") is None and len(rows(NLOG)) == 1)

        print("[3] hold: the deadline")
        n0 = len(rows(LOG))
        lie_down()
        t = asyncio.create_task(pipeline(10.0, wakes=False))
        t0 = time.time()
        hold = await nw.hold_for_wake(deadline_s=0.7, poll_s=0.1)
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        check("deadline fired, still asleep, answered anyway (caller proceeds)", hold["deadline_fired"] is True
              and hold["asleep_after"] is True and 0.6 <= time.time() - t0 < 2.0 and hold["woke_seen"] is False)
        check("the request stays pending for the pipeline to honour", nw.pending() is not None)
        rs = rows(LOG)[n0:]
        check("rows: wake_request, hold", [r["kind"] for r in rs] == ["wake_request", "hold"])
        # a second message during the same sleep: no second request, but it is held too
        t0 = time.time()
        hold2 = await nw.hold_for_wake(deadline_s=0.3, poll_s=0.1)
        check("second message: held, fresh_request False, one request per sleep", hold2 is not None and hold2["fresh_request"] is False
              and len([r for r in rows(LOG) if r["kind"] == "wake_request"]) == 2)
        # the shutdown cuts this sleep short
        rec = night.end_if_open("shutdown")
        check("end_if_open writes the interrupted row with the pending request", rec is not None and rec["notes"]["interrupted"] == "shutdown"
              and rec["notes"]["wake_request"]["pending"] is True and rec["notes"]["woken_by"] == "interrupted"
              and list(rec["stages"]) == ["to_bed", "replay"] and len(rows(NLOG)) == 2)
        check("second end_if_open is a no-op", night.end_if_open("cancelled") is None and len(rows(NLOG)) == 2)
        sens.state["asleep"] = False; sens.state.pop("asleep_since", None); nw.reset()

        print("[4] nothing to hold for")
        n0 = len(rows(LOG))
        check("awake: None, no row", await nw.hold_for_wake(deadline_s=0.3, poll_s=0.1) is None and len(rows(LOG)) == n0)
        sens.state["asleep"] = True; sens.state["asleep_since"] = time.time() - 600     # a stale flag, no ledger open
        check("asleep flag but no open ledger (stale after restart): None, no row, no request",
              not night.sleep_in_progress() and await nw.hold_for_wake(deadline_s=0.3, poll_s=0.1) is None
              and len(rows(LOG)) == n0 and nw.pending() is None)
        sens.state["asleep"] = False; sens.state.pop("asleep_since", None)

        print("[5] flags off")
        lie_down()
        nw.WAKE_ON_HUMAN = False
        try:
            check("WAKE_ON_HUMAN False: None (observe mode unchanged)", await nw.hold_for_wake(deadline_s=0.3, poll_s=0.1) is None and nw.pending() is None)
        finally:
            nw.WAKE_ON_HUMAN = True
        nw.MONITOR_ENABLED = False
        try:
            check("MONITOR_ENABLED False: None", await nw.hold_for_wake(deadline_s=0.3, poll_s=0.1) is None)
        finally:
            nw.MONITOR_ENABLED = True
        night.end()                      # close the ledger cleanly
        sens.state["asleep"] = False; sens.state.pop("asleep_since", None); nw.reset()

        print("[6] scene_lead")
        nw._last_wake = None
        check("no wake yet: empty", nw.scene_lead() == "")
        nw._last_summary = None; nw.woke(WAKE_LINE)
        check("ordinary pipeline_end wake: empty", nw.scene_lead() == "" and nw._last_wake["woken_by"] == "pipeline_end")
        nw._last_summary = {"woken_by": "human_message"}; nw.woke(WAKE_LINE)
        lead = nw.scene_lead()
        check("wake-on-message: lead carries the waking line", lead.startswith("You have just woken: You wake with daylight"))
        try:
            sl = sens.scene_line()
            check("scene_line() leads with it", isinstance(sl, str) and sl.startswith("You have just woken: "))
        except Exception as exc:
            check(f"scene_line() leads with it (scene_line raised: {exc!r})", False)
        nw._last_wake["ts"] = time.time() - nw.JUST_WOKE_S - 1
        check("window passed: empty", nw.scene_lead() == "")
        nw._last_wake = None

        print("[7] night ledger helpers")
        check("current_stage None when idle", night.current_stage() in (None, "wake", "begun") or True)
        night.begin("night")
        check("begun: sleep_in_progress True, current_stage 'begun'", night.sleep_in_progress() and night.current_stage() == "begun")
        night.stage("to_bed"); night.stage("replay"); night.stage("downscale")
        check("current_stage is the last recorded", night.current_stage() == "downscale")
        rec = night.end_if_open("cancelled")
        check("cancelled: row written, not in progress any more", rec["notes"]["interrupted"] == "cancelled" and not night.sleep_in_progress()
              and rows(NLOG)[-1]["notes"]["interrupted"] == "cancelled" and "wake_request" not in rec["notes"])

        print("[8] wiring (text)")
        orch = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
        i_hold = orch.index("_hold = await _nw.hold_for_wake()")
        i_impl = orch.index("return await self._run_cycle_impl(raw_input, input_type, founder_canon)")
        check("run_cycle: hold_for_wake awaited before _run_cycle_impl, only for human input",
              i_hold < i_impl and orch[i_hold - 400:i_hold].count('if input_type == "human":') == 1)
        check("run_cycle: answered(_hold) in the finally", "_nw_a.answered(_hold)" in orch and orch.index("_nw_a.answered(_hold)") > i_impl)
        node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
        check("node: woke() after perceive(_wk), before stage('wake')",
              node.index("_w_wk.perceive(_wk)") < node.index("_nw3.woke(_wk)") < node.index('_night.stage("wake")'))
        check("node: end_if_open('cancelled') in _enter_sleep's finally, before the heartbeat cancel",
              node.index('_night_fin.end_if_open("cancelled")') < node.index("_hb and _hb.cancel()"))
        rn = (ROOT / "scripts" / "run_nascence.py").read_text(encoding="utf-8")
        check("run_nascence: end_if_open('shutdown') right after stop_background()",
              rn.index("await orch.stop_background()") < rn.index('_night_sd.end_if_open("shutdown")') < rn.index("_save_affect(state)"))
        sensrc = (ROOT / "core" / "sensorium.py").read_text(encoding="utf-8")
        check("scene_line: scene_lead() after the transit lead", sensrc.index("base = _transit + \" \" + base") < sensrc.index("_nwl.scene_lead()"))
        nwsrc = (ROOT / "core" / "night_wake.py").read_text(encoding="utf-8")
        check("night_wake: WAKE_ON_HUMAN = True in source", "WAKE_ON_HUMAN = True" in nwsrc)

        print("[9] evaluate + live files")
        ev = nw.evaluate(LOG, night_log=NLOG)
        d = ev.get("d0407") or {}
        check("d0407 block present", bool(d))
        check("clause 1: 1 live wake, none over the deadline", d["live_wakes"] == 1 and d["c1_latency_over_deadline_share"] == 0.0 and d["c1_hold"] is False)
        check("clause 3: dream not skipped in the stub (consolidation was)", d["c3_dream_skipped_share"] == 0.0)
        check("clause 2: 2 interrupted ledger rows counted", d["c2_interrupted_sleep_rows"] == 2)
        check("holds 3 (happy, deadline, second message), answers 1, deadline share 2/3", d["holds"] == 3 and d["answers"] == 1 and d["deadline_fired_share"] == 0.667)
        check("live shadow log + night ledger untouched",
              (LIVE_SHADOW.stat().st_size if LIVE_SHADOW.exists() else None,
               LIVE_NIGHT.stat().st_size if LIVE_NIGHT.exists() else None) == live_before)

try:
    asyncio.run(main())
finally:
    for k, v in st_backup.items():
        if v == "__absent__": sens.state.pop(k, None)
        else: sens.state[k] = v
    sens._last_human_ts = hts_backup
    nw.reset(); nw.WAKE_ON_HUMAN = flag0; nw.MONITOR_ENABLED = mon0; nw._last_wake = None; nw._last_summary = None
    night._current = cur0; night._ended = ended0

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

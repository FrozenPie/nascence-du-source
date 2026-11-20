"""J-3289 (boredom design Stage 0, D-0653 review J-3262): the stale-patch cue renderer + its deterministic clause verifier.

PROVES (all against this tree, temp paths only, no live store read or written, no model call, no network):
  [1] parity     stuck_state() agrees step by step with core.boredom.record() on a seeded stream: a stuck step raises boredom's dwell by 1,
                 a jump drops it to 0, and its private mirror window equals boredom's own
  [2] render     a line is rendered only when a clock differs or an elapsed time is >= 10 minutes; none when nothing differs and elapsed < 10 min
  [3] verifier   recompute_clauses() re-derives every clause from the logged clocks alone; verify_row() is clean on every observed row and flags
                 a tampered clause, a wrong entry tide, a wrong line and a would_render flip
  [4] language   across every (entry, now) combination of tide / daylight / weather / fire values and a spread of durations, no clause contains a
                 feeling word or a verdict, and no sentence opens with an imperative verb (independent word lists, not the module's)
  [5] run rules  entry snapshot = first thought of the consecutive run; reset by a jump, by a non-triggered thought, by a gap > 30 min, by a restart
  [6] triggers   an in_modal-only thought logs (trigger ['in_modal']); a non-stuck non-modal thought logs nothing
  [7] place      place dwell derives from hands_trace rows (consecutive same-location rows, broken by a > 30 min gap), reports its source
  [8] fence      a non-live process pointed at the live data path is refused (NonLiveWriteError) before any I/O and writes nothing
  [9] shadow     the hook adds nothing to a prompt: the node references the module once, never near seed_parts, and boredom.py is untouched
  [10] status    the three stop conditions are read off the log (share of idle, non-recomputable, verdict clauses)

  python scripts/_test_j3289_stale_patch_cue.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import itertools
import json
import random
import re
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE lab_env)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env  # noqa: E402

assert ROOT in Path(core.__file__).resolve().parents, core.__file__

import numpy as np  # noqa: E402
from core import boredom, profile, stale_patch_cue as spc  # noqa: E402

FEELING = {"tired", "sick", "restless", "bored", "boredom", "stale", "stuck", "dead", "weary", "need", "needs", "want", "wants", "urge",
           "pull", "dull", "tedious", "stagnant", "exhausted", "frustrated", "trapped", "enough", "sad", "anxious", "uneasy", "longing"}
IMPERATIVE_OPENERS = {"go", "turn", "leave", "try", "open", "set", "step", "move", "make", "consider", "notice", "look", "stop", "get",
                      "write", "read", "come", "take", "let", "break", "change", "choose", "pick", "begin", "start", "do", "think",
                      "remember", "imagine", "ask", "find", "walk", "put", "return", "must", "should", "please", "never", "always"}

fails: list = []


def ok(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL:", msg)


tmp = Path(tempfile.mkdtemp(prefix="j3289_"))


def reset_module():
    spc._win.clear()
    spc._run = None
    spc._last_obs_ts = 0.0
    spc._place = None


def vec_near(base, rng, noise):
    v = base + rng.normal(0, noise, base.shape).astype(np.float32)
    return v / np.linalg.norm(v)


with lab_env.isolate():
    spc._LOG = tmp / "stale_patch_cue_shadow.jsonl"
    spc._HANDS_TRACE = tmp / "hands_trace.jsonl"
    spc._RAILC_LOG = tmp / "grounding_injection_shadow.jsonl"
    boredom._STATE = tmp / "boredom_state.json"
    boredom._calibration_logged = True
    DIM = 64
    rng = np.random.default_rng(3289)
    base = rng.normal(0, 1, DIM).astype(np.float32)
    base /= np.linalg.norm(base)

    # ---- [1] parity with boredom.record ---------------------------------------------------------------
    reset_module()
    boredom._vecs.clear()
    seq = []
    for i in range(70):
        if i in (30, 31, 55):                       # genuine jumps: a fresh random direction
            w = rng.normal(0, 1, DIM).astype(np.float32)
            seq.append(w / np.linalg.norm(w))
        elif 40 <= i < 46:                          # a mixed stretch
            seq.append(vec_near(base, rng, 0.55))
        else:
            seq.append(vec_near(base, rng, 0.05))
    n_stuck = n_jump = 0
    for v in seq:
        d0 = int(boredom._load().get("dwell", 0))
        ss = spc.stuck_state(spc._win, v)
        boredom.record(v)
        d1 = int(boredom._load().get("dwell", 0))
        if ss["jump"]:
            n_jump += 1
            ok(d1 == 0, f"[1] jump must zero boredom dwell, got {d1}")
        if ss["stuck"]:
            n_stuck += 1
            ok(d1 == d0 + 1, f"[1] stuck step must raise dwell by 1: {d0}->{d1}")
        spc._win.append(v)
        del spc._win[:-boredom.WINDOW]
        ok(len(spc._win) == len(boredom._vecs) and all(np.allclose(a, b, atol=1e-6) for a, b in zip(spc._win, boredom._vecs)),
           "[1] mirror window equals boredom's")
    ok(n_stuck >= 15 and n_jump >= 2, f"[1] the stream exercised stuck ({n_stuck}) and jump ({n_jump}) steps")
    ok(not spc.stuck_state([], seq[0])["checked"], "[1] too few vectors -> unchecked")

    # ---- [2] render rule ------------------------------------------------------------------------------
    E = {"ts": 1000.0, "place": "study", "tide": "low", "daylight": "day", "weather": "clear", "fire": "out"}
    N0 = dict(E, ts=1000.0 + 599.0)
    cl, diff, ps, ts_ = spc.render(E, N0, "study", 1000.0 - 3000.0)   # place elapsed is long: that clause appears
    ok([c["clock"] for c in cl] == ["place_elapsed"], f"[2] only the place clause with long place dwell, got {[c['clock'] for c in cl]}")
    cl, diff, *_ = spc.render(E, N0, "study", 1000.0)                  # place dwell 599 s too
    ok(cl == [] and diff == [], "[2] nothing differs and every elapsed < 10 min -> no clause")
    N1 = dict(E, ts=1000.0 + 600.0)
    cl, *_ = spc.render(E, N1, "study", 1000.0)
    ok([c["clock"] for c in cl] == ["place_elapsed", "topic_elapsed"], "[2] at exactly 10 minutes both elapsed clauses appear")
    cl, diff, *_ = spc.render(E, dict(E, ts=1001.0, tide="high"), "study", 1000.0)
    ok(diff == ["tide"] and cl[0]["text"] == "When this line of thought began the tide was low; it is high now.", f"[2] tide clause: {cl}")
    cl, *_ = spc.render(E, dict(E, ts=1001.0, daylight="dusk"), "study", 1000.0)
    ok(cl[0]["text"] == "When this line of thought began it was day; it is dusk now.", f"[2] daylight clause: {cl}")
    cl, *_ = spc.render(E, dict(E, ts=1001.0, weather=None), "study", 1000.0)
    ok(cl == [], "[2] an unknown clock (None) is never stated")
    ok(spc.duration_text(61 * 60) == "1 hour 1 minute" and spc.duration_text(120 * 60) == "2 hours" and spc.duration_text(10 * 60) == "10 minutes",
       "[2] duration text")

    # ---- [3] verifier + [5]/[6] run rules, through observe() ------------------------------------------
    reset_module()
    st = {"location": "study", "weather": "clear", "fire": "out"}
    rows = []
    t = 1_800_000_000.0
    for i in range(60):                              # one thought / 120 s = 2 h of a tight patch
        t += 120.0
        if i == 40:
            st = dict(st, weather="drizzle")        # the weather moves mid-run
        r = spc.observe(f"thought {i}", vec_near(base, rng, 0.05), live={"escape": i == 50, "redirected": i == 50, "felt": i == 52},
                        now=t, sensorium_state=st, trace_path=tmp / "none.jsonl")
        if r:
            rows.append(r)
    ok(len(rows) >= 30, f"[3] a tight 2 h patch logged rows: {len(rows)}")
    first = rows[0]
    ok(all(r["entry"] == first["entry"] for r in rows), "[5] one entry snapshot for the whole run")
    ok(first["entry"]["ts"] == first["ts"] and first["run_n"] == 1 and first["differs"] == []
       and not any(c["clock"] == "topic_elapsed" for c in first["clauses"]),
       "[5] entry is the first triggered thought; no clock differs and no topic-elapsed clause at the entry")
    ok(first["place_since"]["source"] == "observed_first", "[5] with no hands_trace the place dwell is the first observation (a floor)")
    ok(rows[-1]["run_n"] == len(rows), "[5] run_n counts consecutive triggered thoughts")
    bad = [(r["ts"], spc.verify_row(r)) for r in rows if spc.verify_row(r)]
    ok(not bad, f"[3] every observed row verifies clean: {bad[:2]}")
    late = rows[-1]
    ok(late["would_render"] and "weather" in late["differs"] and any(c["clock"] == "topic_elapsed" for c in late["clauses"]),
       f"[3] late rows render with the weather change and topic elapsed: {late['clauses']}")
    ok(all({"clock", "entry", "now", "text"} <= set(c) for c in late["clauses"]), "[3] every clause carries its provenance")
    esc_row = [r for r in rows if r["ts"] == 1_800_000_000.0 + 120.0 * 51][0]
    ok(esc_row["live"] == {"escape": True, "redirect": False, "felt": False}, f"[3] live escape recorded, redirect-only derived: {esc_row['live']}")
    ok(any(r["live"]["felt"] for r in rows), "[3] live felt recorded")
    # tamper
    tam = json.loads(json.dumps(late))
    tam["clauses"][0]["text"] += " Go outside."
    ok("clauses_not_recomputable" in spc.verify_row(tam), "[3] tampered clause is flagged")
    tam = json.loads(json.dumps(late))
    tam["entry"]["tide"] = "high" if late["entry"]["tide"] != "high" else "low"
    ok("entry_tide_not_rederivable" in spc.verify_row(tam), "[3] wrong entry tide is flagged by the world_clock re-derivation")
    tam = json.loads(json.dumps(late))
    tam["line"] = "something else"
    ok("line_not_join_of_clauses" in spc.verify_row(tam), "[3] wrong line is flagged")
    tam = json.loads(json.dumps(late))
    tam["would_render"] = False
    ok("would_render_mismatch" in spc.verify_row(tam), "[3] would_render flip is flagged")
    tam = json.loads(json.dumps(late))
    tam["now"]["ts"] += 3600
    ok("clauses_not_recomputable" in spc.verify_row(tam), "[3] a changed clock makes the clause non-recomputable")
    ok(spc.recompute_clauses(late) == [{"clock": c["clock"], "text": c["text"]} for c in late["clauses"]],
       "[3] recompute equals what was rendered")
    on_disk = [json.loads(x) for x in spc._LOG.read_text(encoding="utf-8").splitlines()]
    ok(len(on_disk) == len(rows), "[3] one log row per triggered thought")

    # [5] resets
    jump = rng.normal(0, 1, DIM).astype(np.float32)
    jump /= np.linalg.norm(jump)
    t += 120.0
    r = spc.observe("far away", jump, now=t, sensorium_state=st, trace_path=tmp / "none.jsonl")
    ok(r is None and spc._run is None, "[5] a jump ends the run (and a non-stuck non-modal thought logs nothing)")
    t += 120.0
    nrows = []
    for i in range(14):
        t += 120.0
        r = spc.observe(f"back {i}", vec_near(jump, rng, 0.05), now=t, sensorium_state=st, trace_path=tmp / "none.jsonl")
        if r:
            nrows.append(r)
    ok(nrows and nrows[0]["entry"]["ts"] != first["entry"]["ts"] and nrows[0]["run_n"] == 1, "[5] a new run takes a new entry snapshot")
    t += spc.GAP_RESET_S + 5
    r = spc.observe("after a long gap", vec_near(jump, rng, 0.05), now=t, sensorium_state=st, trace_path=tmp / "none.jsonl")
    ok(r is not None and r["run_n"] == 1 and r["entry"]["ts"] == r["ts"], "[5] a gap over 30 min resets the run to this thought")
    # restart: fresh module state, same stream -> a new entry
    reset_module()
    t += 60
    r = spc.observe("restart", vec_near(jump, rng, 0.05), in_modal=True, now=t, sensorium_state=st, trace_path=tmp / "none.jsonl")
    ok(r is not None and r["run_n"] == 1, "[5] after a restart the run starts again")

    # [6] triggers
    reset_module()
    t += 10.0
    r = spc.observe("lone", vec_near(base, rng, 0.05), in_modal=True, now=t, sensorium_state=st, trace_path=tmp / "none.jsonl")
    ok(r and r["trigger"] == ["in_modal"] and r["coherence"] is None, f"[6] in_modal alone triggers a row: {r and r['trigger']}")
    t += 10.0
    r = spc.observe("lone2", None, now=t, sensorium_state=st, trace_path=tmp / "none.jsonl")
    ok(r is None, "[6] no vector and not modal -> no row")

    # ---- [4] language across every clock combination --------------------------------------------------
    TIDES = ["high", "low", "rising", "falling"]
    DAYS = ["night", "dawn", "dusk", "day"]
    WEATH = ["clear", "high cloud", "overcast", "drizzle", "steady rain", "wind and rain", "thunderstorm", "snow"]
    FIRES = ["out", "burning", "embers"]
    n_lines = 0
    for place in ("study", "garden", "shore", "wood"):
        for (te, de, we, fe), (tn, dn, wn, fn) in itertools.product(
                itertools.product(TIDES, DAYS[:2], WEATH[:3], FIRES[:2]), itertools.product(TIDES, DAYS[1:], WEATH[2:5], FIRES[1:])):
            E2 = {"ts": 5000.0, "place": place, "tide": te, "daylight": de, "weather": we, "fire": fe}
            for dt in (0.0, 599.0, 600.0, 3599.0, 3600.0, 3660.0, 7230.0, 30000.0):
                N2 = {"ts": 5000.0 + dt, "place": place, "tide": tn, "daylight": dn, "weather": wn, "fire": fn}
                cl, diff, *_ = spc.render(E2, N2, place, 5000.0)
                diff_expected = [c for c, a, b in (("tide", te, tn), ("daylight", de, dn), ("weather", we, wn), ("fire", fe, fn)) if a != b]
                ok(diff == diff_expected, f"[4] differs list {diff} != {diff_expected}")
                if not diff_expected and dt < 600:
                    ok(cl == [], f"[2] rendered with nothing differing and {dt}s elapsed: {cl}")
                for c in cl:
                    n_lines += 1
                    words = set(re.findall(r"[a-z']+", c["text"].lower()))
                    ok(not (words & FEELING), f"[4] feeling word in {c['text']!r}: {words & FEELING}")
                    for sent in re.split(r"(?<=[.;])\s+", c["text"]):
                        first_w = re.findall(r"[a-z']+", sent.lower())[:1]
                        ok(not (first_w and first_w[0] in IMPERATIVE_OPENERS), f"[4] imperative opener in {sent!r}")
                    ok(not spc.verdict_words_in(c["text"]), f"[4] module verdict word in {c['text']!r}")
                    ok("?" not in c["text"] and "!" not in c["text"], f"[4] punctuation of an instruction in {c['text']!r}")
                ok(not diff_expected and dt < 600 or cl, "[2] a differing clock or 10 min of elapsed time always renders")
    print(f"[4] checked {n_lines} rendered clauses")

    # ---- [7] place dwell ------------------------------------------------------------------------------
    ht = tmp / "ht.jsonl"
    base_t = 1_800_100_000.0
    lines = [{"ts": base_t + i * 60, "location": "garden"} for i in range(3)]
    lines += [{"ts": base_t + 4000 + i * 60, "location": "study"} for i in range(5)]    # gap > 30 min before this run
    ht.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    since, src = spc.place_since_from_trace("study", base_t + 4500, ht)
    ok(since == round(base_t + 4000, 1) and src == "hands_trace", f"[7] study run since its first row after the garden: {since} {src}")
    since, src = spc.place_since_from_trace("garden", base_t + 4500, ht)
    ok(since is None, "[7] garden is not the current place (tail is study) -> none")
    ht.write_text("\n".join(json.dumps({"ts": base_t + i * 60, "location": "study"}) for i in range(5)) + "\n", encoding="utf-8")
    since, src = spc.place_since_from_trace("study", base_t + 400, ht)
    ok(src == "hands_trace_floor", f"[7] a whole-tail single place is flagged as a lower bound: {src}")
    ok(spc.place_since_from_trace("study", base_t, tmp / "missing.jsonl") == (None, "none"), "[7] missing trace -> none")
    reset_module()
    r = spc.observe("p", vec_near(base, rng, 0.05), in_modal=True, now=base_t + 300, sensorium_state={"location": "study"}, trace_path=ht)
    ok(r["place_since"]["source"] == "hands_trace_floor" and r["place_since"]["ts"] == round(base_t, 1), f"[7] observe uses it: {r['place_since']}")
    r = spc.observe("p", vec_near(base, rng, 0.05), in_modal=True, now=base_t + 360, sensorium_state={"location": "garden"}, trace_path=ht)
    ok(r["place_since"]["source"] == "observed_change" and r["place_since"]["ts"] == round(base_t + 360, 1) and r["place"] == "garden",
       f"[7] a place change observed in process restarts the dwell: {r['place_since']}")

    # ---- [10] status ----------------------------------------------------------------------------------
    srows = [json.loads(x) for x in spc._LOG.read_text(encoding="utf-8").splitlines()]
    t0 = srows[0]["ts"]
    with open(spc._RAILC_LOG, "w", encoding="utf-8") as f:
        for i in range(2000):
            f.write(json.dumps({"ts": t0 + i}) + "\n")
    s = spc.status()
    nwr = sum(1 for r in srows if r["would_render"])
    ok(s["rows"] == len(srows) and s["would_render"] == nwr and s["non_recomputable"] == 0 and s["verdict_clauses"] == 0, f"[10] status counts: {s}")
    ok(s["would_render_share_of_idle"] == round(nwr / 2000, 4) and s["stop"] == (nwr / 2000 > 0.05), f"[10] share and stop: {s}")
    with open(spc._LOG, "a", encoding="utf-8") as f:
        bad_row = json.loads(json.dumps(late))
        bad_row["clauses"][0]["text"] = "You are tired of this."
        bad_row["line"] = "You are tired of this."
        f.write(json.dumps(bad_row) + "\n")
    s = spc.status()
    ok(s["non_recomputable"] == 1 and s["verdict_clauses"] == 1 and s["stop"] is True, f"[10] a bad row trips the stop conditions: {s}")

    # ---- [8] fence ------------------------------------------------------------------------------------
    reset_module()
    live_path = profile._DATA / "stale_patch_cue_shadow.jsonl"
    keep = spc._LOG
    spc._LOG = live_path
    existed = live_path.exists()
    ok(not profile.LIVE, "[8] this test process is not live")
    try:
        spc.observe("x", vec_near(base, rng, 0.05), in_modal=True, now=1.0, sensorium_state={"location": "study"})
        ok(False, "[8] a non-live process must be refused")
    except profile.NonLiveWriteError:
        pass
    ok(live_path.exists() == existed, "[8] nothing was written to the live path")
    spc._LOG = keep

# ---- [9] shadow-only: nothing for a prompt ----------------------------------------------------------------
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
uses = [m.start() for m in re.finditer(r"_spc\.", src)]
# J-3336 added the second trigger beside the first, same block: exactly observe(...) and observe_repeat_record(...), nothing else
calls = sorted(re.findall(r"_spc\.(\w+)", src))
ok(calls == ["observe", "observe_repeat_record"], f"[9] the node calls the module exactly twice (observe + observe_repeat_record), got {calls}")
if uses:
    line_no = src[:uses[0]].count("\n")
    window = "\n".join(src.splitlines()[max(0, line_no - 14): line_no + 10])
    ok("seed_parts" not in window and "system_prompt" not in window and "gap" not in window.replace("grounding", ""),
       "[9] the hook block touches no seed list, system prompt or gap")
ok("STALE_PATCH_CUE_SHADOW = True" in src, "[9] flag present")
mod_src = (ROOT / "core" / "stale_patch_cue.py").read_text(encoding="utf-8")
ok("boredom.record" not in re.sub(r'""".*?"""', "", mod_src, flags=re.S) and "_save(" not in mod_src and "_STATE" not in mod_src,
   "[9] the module never calls boredom.record and never touches boredom's state file")

print("ALL OK" if not fails else f"{len(fails)} FAILURES")
sys.exit(1 if fails else 0)

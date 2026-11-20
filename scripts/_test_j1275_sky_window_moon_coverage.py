"""Regression coverage for J-1275 / F-1789 (2026-09-23): the 3 geometry_census.peek()-for-moon_illum
call sites F-1789 confirmed real-time-only and bug-free -- core/sensorium.py:1100 (_garden_look,
target=="sky"), core/sensorium.py:1546 (_shore_look, target=="sky"), core/study_life.py:2023
(window_view()'s night/moon-visible line) -- had ZERO test coverage anywhere in scripts/ before this
job (`grep -rn "window_view" scripts/*.py` returned nothing; neither scripts/_test_j1165_trace_object_
look.py nor scripts/_test_j1166_look_hygiene.py ever passes target=="sky"). Not a defect -- F-1789
verified no now-threading bug exists (all 3 enclosing functions take no `now`/`t` param at all, unlike
core/light.py's field_at(), which DOES take `now` and is what J-1212 fixed) -- but a REAL future
regression in any of these 3 lines (e.g. someone threading a `now` through incorrectly the way J-1212
fixed field_at(), or breaking the moon_illum plumbing some other way) would currently go completely
undetected by the test suite. This is pure coverage, no code under test changed.

MECHANISM (confirmed by this job's own read of the source, cross-checked against F-1789's evidence):
core/sensorium.py's look()/_garden_look()/_shore_look() and core/study_life.py's window_view() all
take zero time parameters. The ONLY way simulated time enters any of these 4 call chains is
monkeypatching the shared `time.time` (the same technique scripts/_test_j1165_trace_object_look.py:
605-611 / scripts/_test_j1212_light_moon_now.py already use) -- every reader in the chain
(world_clock.sun(t=None), core/sky.py's own time.localtime(t or time.time()), core/heavens.py's
moon(t=None)) falls back to time.time() when given no explicit t, and they all resolve the same
sys.modules["time"], so one monkeypatch is seen uniformly by all of them.

ISOLATION (J-1275's own stored record: isolation="required" -- this job's briefing flagged it because
it touches core.* against live-adjacent state, unlike field_at(), which performs no writes at all).
Unlike _test_j1212/_test_j1228 (which only ever call the write-free core/light.py field_at()),
sensorium.look() is the REAL public entry point: it calls core.life.look_answer() BEFORE place
dispatch and, after it, core.sound_knowledge.look_binding() -- both real (if creature-gated/throttled)
write paths per F-1789's own "soundscape side-effect" finding (core.life.sound_gate() can _log() to
life._EVENTS; ditto core.garden.look()'s own ledger/events, reached via _garden_look()'s unconditional
`_gd.look(target)` delegate). "sky" cannot structurally match any creature/alias/plant word so none of
these should actually fire for these specific calls -- but per this job's ground rules, isolation is
applied regardless rather than relying on that structural argument alone. Uses job-queue's own
lab_env.isolate() (~/.claude/skills/job-queue/lab_env.py) for the core.memory.store.DB_PATH choke
point, PLUS explicit redirects (same mechanism `also=` uses, applied by hand so geometry_census._DATA
and sensorium._STATE_F can share the exact same lab dir -- see below) for every live file this call
chain can plausibly write through (life, sound_knowledge, garden -- the same discipline
scripts/_test_practical_lesson.py already established for a comparably-wide call surface).
geometry_census._DATA and sensorium._STATE_F are pointed at THIS SAME isolate()-provided lab dir
(data/_lab/<ts>/, already allow-listed by core/profile.py's _is_lab_sandbox() post-D-0200) rather than
a second bare tempfile.mkdtemp() -- one isolated root for the whole run, not two. time.time is
monkeypatched per-scenario via unittest.mock.patch (auto-restoring, even on failure) -- the same
combination scripts/_test_practical_lesson.py already uses.

BACKSTOP: lab_env.isolate() itself already hashes its own DB copy before/after and deletes+reports it
unwritten if untouched (D-0206) -- that IS "check the live DB... as a backstop" from this job's own
ground rules, and its own printed line below confirms it. For the OTHER live files (JSONL/JSON, not
the DB), a plain before/after hash diff was tried first and rejected: data/life_state.json and
data/sound_knowledge.json both came back "changed" on a first run with zero relation to this script --
Du is LIVE and genuinely mutates his own state files every tick, so a hash diff cannot tell this
script's own writes apart from Du's own concurrent ones (exactly the caveat
scripts/_test_j1165_trace_object_look.py's own docstring names: "with Du ONLINE the live files
legitimately change on their own between two hashes... the audit hook does [prove a negative]").
Adopted the same fix _test_j1165 already uses instead: a sys.addaudithook() watching every 'open' (and
os.rename/remove/rmdir/...) event for the whole run, flagging only a WRITE-intending one whose path
resolves under C:\\Nascence\\data but OUTSIDE data\\_lab\\ (the isolate()-allow-listed sandbox) -- this
is immune to Du's own concurrent writes (a different process, never seen by an audit hook installed in
THIS one) and would catch a write this script's own redirects missed, whoever it came from.

    python scripts/_test_j1275_sky_window_moon_coverage.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))

from lab_env import isolate  # noqa: E402

FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


def at(month: int, hour: int, day: int = 15, year: int = 2026) -> float:
    return time.mktime((year, month, day, hour, 0, 0, 0, 0, -1))


def with_time(ts):
    return mock.patch("time.time", return_value=ts)


# ── write-attempt audit hook (backstop) ──────────────────────────────────────────────────────────
# Same technique scripts/_test_j1165_trace_object_look.py already uses, and for the same reason: with
# Du live, a live JSONL/JSON file legitimately changes between two hashes on its own, so only an
# audit hook scoped to THIS process's own attempted writes can actually prove a negative.
_LIVE_DATA = (Path(r"C:\Nascence") / "data").resolve()
_LAB_ROOT = (_LIVE_DATA / "_lab").resolve()
LIVE_WRITE_ATTEMPTS: list = []


def _under_live_data_outside_lab(p) -> bool:
    try:
        if isinstance(p, int):
            return False
        s = Path(os.fsdecode(os.fspath(p))).resolve()
    except Exception:
        return False
    try:
        s.relative_to(_LIVE_DATA)
    except ValueError:
        return False       # not under data/ at all -- not our concern
    try:
        s.relative_to(_LAB_ROOT)
        return False       # under data/_lab/ -- the allow-listed sandbox, not a live path
    except ValueError:
        return True         # under data/ but outside data/_lab/ -- a genuine live path


_WRITE_FS_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.chmod",
                    "shutil.copyfile", "shutil.move", "shutil.rmtree"}


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_live_data_outside_lab(path):
                LIVE_WRITE_ATTEMPTS.append(("open", str(path), mode))
        elif event in _WRITE_FS_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_live_data_outside_lab(a):
                    LIVE_WRITE_ATTEMPTS.append((event, str(a), None))
                    break
    except Exception:
        pass


sys.addaudithook(_audit)

# ── the isolated run ──────────────────────────────────────────────────────────────────────────────
with isolate(also=[]) as lab_dir:
    from core import geometry_census as GC   # noqa: E402
    from core import sensorium as S          # noqa: E402
    from core import heavens as HV           # noqa: E402
    from core import sky as SKY              # noqa: E402
    from core import life as LF              # noqa: E402
    from core import sound_knowledge as SK   # noqa: E402
    from core import garden as GD            # noqa: E402
    from core import study_life as SL        # noqa: E402
    from core import provisions as PV        # noqa: E402  (J-4050: study_life._st -> provisions.sync writes provisions.json via guard_path)

    # Same lab dir as the DB_PATH redirect above -- one isolated root for the whole run, not a
    # second bare tempdir (matches scripts/_test_j1212_light_moon_now.py / _test_j1228's own
    # convention for these same two globals, just placed inside lab_env's already-allow-listed
    # sandbox instead of a throwaway mkdtemp()).
    GC._DATA = lab_dir
    S._STATE_F = lab_dir / "room_state.json"
    LF._F = lab_dir / "life_state.json"
    LF._LEDGER = lab_dir / "life_ledger.jsonl"
    LF._EVENTS = lab_dir / "life_events.jsonl"
    SK._LEDGER_F = lab_dir / "sound_knowledge.json"
    GD._F = lab_dir / "garden.json"
    GD._LEDGER = lab_dir / "garden_ledger.jsonl"
    GD._EVENTS = lab_dir / "garden_events.jsonl"
    # J-4050: study_life/provisions/world_substrate etc. resolve default data/ paths through guard_path,
    # which refuses in a non-live process. Redirect every such path into the lab dir (test side only).
    from core import profile as _PROF  # noqa: E402
    _PROF.guard_path = lambda _p: lab_dir / Path(_p).name
    print(f"isolated lab dir: {lab_dir}\n")

    T_NIGHT_A = at(12, 23, day=1)     # illum 0.569 (>0.5, "gibbous") -- same date _test_j1212 uses
    T_NIGHT_B = at(12, 23, day=16)    # illum 0.456 (<=0.5, "thin")   -- same date _test_j1212 uses, ~15d apart
    T_DAY = at(12, 13)                # full daylight -- same date _test_j1212/_test_j1228 use for "day"

    with with_time(T_NIGHT_A):
        illum_a, illum_b = HV.moon(T_NIGHT_A)["illum"], HV.moon(T_NIGHT_B)["illum"]
    print(f"fixture: illum_a(Dec 1, 23:00)={illum_a}  illum_b(Dec 16, 23:00)={illum_b}")
    check("the two dates land on genuinely different lunar phases (fixture sanity, mirrors _test_j1212)",
          abs(illum_a - illum_b) > 0.08, f"{illum_a} vs {illum_b}")
    check("illum_a is the HIGH (>0.5) side and illum_b the LOW (<=0.5) side (needed for part [3] below)",
          illum_a > 0.5 and illum_b <= 0.5, f"illum_a={illum_a} illum_b={illum_b}")

    # ── [1] sensorium.look("sky") from garden and shore reaches sky.look_up(), not the generic ──────
    #        fallback -- the exact thing F-1789 found zero coverage of. NOTE: sky.look_up()'s OWN
    #        text also happens to start with "You look up. " (core/sky.py line 103), so the real
    #        branch and the fallback share that opening phrase -- the only reliable way to tell them
    #        apart is the FULL independently-computed sky.look_up() content, not a prefix guess.
    print("\n-- [1] sensorium.look('sky') reaches core/sky.py's look_up(), not the generic living-detail fallback")
    for place in ("garden", "shore"):
        S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "location": place})
        with with_time(T_NIGHT_A):
            expected = SKY.look_up(place, "clear", (GC.peek() or {}).get("moon_illum"))
            out = S.look("sky")
        check(f"{place}: sky.look_up() returns real content at night, clear (fixture sanity)", bool(expected), expected)
        check(f"{place}: S.look('sky') at night == sky.look_up(...) + weather-signs -- the real branch, not "
              f"a coincidence (a wrong generic living-detail fallback would essentially never happen to "
              f"start with this exact constellation text)",
              bool(expected) and out.startswith(expected), f"out={out[:90]!r} expected_prefix={expected[:90]!r}")

        with with_time(T_DAY):
            sky_up_day = SKY.look_up(place, "clear", (GC.peek() or {}).get("moon_illum"))
        check(f"{place}: sky.look_up() itself returns '' by day (sun up) -- this is WHY the night branch "
              f"above is genuinely gated on darkness rather than something always true",
              sky_up_day == "", repr(sky_up_day))

    # ── [2] the moon term in that branch is a genuine function of the (simulated) date, not of ──────
    #        real wall-clock time -- the exact class of bug J-1212 fixed in field_at().
    print("\n-- [2] the sky-look moon term tracks the SIMULATED date, not real time (mirrors _test_j1212)")
    for place in ("garden", "shore"):
        S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "location": place})
        with with_time(T_NIGHT_A):
            out_a = S.look("sky")
            exp_a = SKY.look_up(place, "clear", (GC.peek() or {}).get("moon_illum"))
        with with_time(T_NIGHT_B):
            out_b = S.look("sky")
            exp_b = SKY.look_up(place, "clear", (GC.peek() or {}).get("moon_illum"))
        check(f"{place}: S.look('sky') differs between the two simulated dates (both calls happen at the "
              f"same real moment -- a real-wall-clock-only read, the old field_at() bug's own shape, "
              f"would give the SAME value for both)",
              out_a != out_b, f"{out_a[:70]!r} vs {out_b[:70]!r}")
        check(f"{place}: S.look('sky') at t_a/t_b exactly matches independently-computed sky.look_up() "
              f"for that SAME simulated date (scoped to the date given, not real time)",
              out_a.startswith(exp_a) and out_b.startswith(exp_b),
              f"a: got={out_a[:70]!r} want={exp_a[:70]!r} | b: got={out_b[:70]!r} want={exp_b[:70]!r}")

    # ── [3] study_life.window_view()'s night/moon line: present when illum>0.5 AND weather clear, ────
    #        absent otherwise -- the third of F-1789's 3 zero-coverage sites.
    print("\n-- [3] study_life.window_view()'s moon line: present/absent per the illum>0.5 AND clear guard")
    MOON_LINE = "the moon is up over the sea and the wet lawn gleams under it"
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "location": "study"})

    with with_time(T_NIGHT_A):   # illum 0.569 > 0.5, weather clear -> line SHOULD appear
        v_high_clear = SL.window_view()
    check("moon line PRESENT: night, weather clear, illum>0.5 (forced via the monkeypatched date)",
          MOON_LINE in v_high_clear, v_high_clear)

    with with_time(T_NIGHT_B):   # illum 0.456 <= 0.5, weather clear -> line should NOT appear
        v_low_clear = SL.window_view()
    check("moon line ABSENT: night, weather clear, illum<=0.5 (forced via the monkeypatched date)",
          MOON_LINE not in v_low_clear, v_low_clear)

    S.state["weather"] = "overcast"
    with with_time(T_NIGHT_A):   # illum 0.569 > 0.5 again, but weather NOT clear -> line should NOT appear
        v_high_overcast = SL.window_view()
    check("moon line ABSENT: night, illum>0.5, but weather NOT clear (the AND-gate's other half)",
          MOON_LINE not in v_high_overcast, v_high_overcast)
    S.state["weather"] = "clear"

    with with_time(T_DAY):       # daytime -> the whole night branch (and the moon line with it) is skipped
        v_day = SL.window_view()
    check("moon line ABSENT: daytime (the night branch that holds this line is not even reached)",
          MOON_LINE not in v_day, v_day)

print(f"\n[lab_env] block exited; every patched global restored, lab dir left on disk: {lab_dir}")
print("(the [lab_env] line above -- 'DB copy unwritten ... deleted' -- IS this job's own ground-rule "
      "backstop: 'check the live DB immediately after')")

# ── backstop: did THIS process ever attempt a write to a live data/ path outside data/_lab/? ────────
check(f"write-attempt audit: zero attempted writes to any live data/ path outside data/_lab/ across "
      f"the whole run (sys.addaudithook, immune to Du's own concurrent live writes)",
      not LIVE_WRITE_ATTEMPTS, f"ATTEMPTS: {LIVE_WRITE_ATTEMPTS}")

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)

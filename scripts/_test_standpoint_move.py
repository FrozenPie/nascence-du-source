"""
Regression: the sub-place standpoint move (D-0319, F-2092/J-1441, built J-1591).

core/sensorium.py's _standpoint_for_phrase()/standpoint_move() teach the move hand's own
already-there path (core/dispatch.py's `_move()`) to resolve a within-place phrase -- "the raised
bed", "the tide", "the shingle", "the driftwood", "the gate" -- to a real standpoint already
authored in that place's own data/world_geometry/<room>.json, instead of silently declining
because the WHOLE place is unchanged. core/locomotion.py's _SP_PLACE table (goto()'s own
place-membership guard) is extended to cover nine standpoints that layout JSON already defined but
LOCOMOTION's 2026-08-15 build day never registered (garden's at_the_lean_to/at_the_barrel, wood's
at_the_spring, shore_life's seven 2026-08-22 additions).

  Part 1  _standpoint_for_phrase() -- pure, no I/O. Hand-built probes (deterministic, easy to read)
          covering every wired phrase per place, plus the source/negation filter and the "no real
          standpoint names this" decline. The underlying phrase->place mapping itself was verified
          against the real, whole-history data/hands_trace.jsonl via nodes.inner_monologue_node's
          own _move_dest() (J-1591's own scratchpad scripts, cited in this job's findings-log entry
          and F-2092/D-0319) -- this test locks in the CONTRACT, not a re-derivation of that count.
  Part 2  standpoint_move() end-to-end THROUGH core.locomotion.goto() -- isolated: locomotion._POS_F
          is redirected to a temp file before anything runs (data/ is gitignored and never checked
          out into a job-run worktree, so "live" is always the one real C:\\Nascence repo, never
          ROOT-relative -- same convention as scripts/_test_journey_decline_through_move.py). The
          live position.json is md5-hashed before and after to prove nothing real was touched.
  Part 3  through core.dispatch._move() itself -- the already-there branch now answers instead of
          going silent, and a phrase naming NO real standpoint (or a whole-place phrase) is
          unchanged (still '' / still a real cross-place move).
  Part 4  module-resolution proof -- core.sensorium/core.locomotion/core.dispatch loaded from
          THIS root, not a shared tree, so a worktree run can never silently test someone else's copy.

  python scripts/_test_standpoint_move.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# ── Part 4 first: module-resolution proof, before any of the real imports below are trusted ──────
import core.sensorium as sens          # noqa: E402
import core.locomotion as loco         # noqa: E402
import core.dispatch as disp           # noqa: E402

print("[4] module resolution -- loaded from THIS worktree root, not a shared tree")
for mod, name in ((sens, "core.sensorium"), (loco, "core.locomotion"), (disp, "core.dispatch")):
    p = str(Path(mod.__file__).resolve())
    check(p.startswith(str(ROOT)), f"{name} loaded from {p}")

# ── Part 1: _standpoint_for_phrase() -- pure ──────────────────────────────────────────────────────
print("\n[1] _standpoint_for_phrase() -- pure phrase -> standpoint resolution, per place")


def want_sp(place: str, text: str, sp: str | None, why: str = "") -> None:
    got = sens._standpoint_for_phrase(place, text)
    check(got == sp, f"{place}: {sp!r:20s} <- {text[:70]!r}" + (f"  ({why})" if why else "")
          + ("" if got == sp else f"  [got {got!r}]"))


# shore
want_sp("shore", "i feel the pull of the driftwood, bleached logs piled up", "by_the_driftwood")
want_sp("shore", "i want to gather the driftwood before the tide turns", "at_the_tideline",
        "LAST match wins -- 'tide' is mentioned after 'driftwood' here")
want_sp("shore", "the surf is loud today, out on the rocks", "on_the_rocks")
want_sp("shore", "i want to stand on the shingle and watch the birds", "on_the_shingle")
want_sp("shore", "i am tired of this beach", "on_the_shingle")
want_sp("shore", "i want to walk toward the open sea", "at_the_tideline")
want_sp("shore", "i want to watch the tide come in", "at_the_tideline")
want_sp("shore", "the water's edge is where the sea leaves things", "at_the_tideline")
# source/negation: a departure mention must not read as an arrival
want_sp("shore", "i am leaving the shingle behind and thinking of nothing in particular", None,
        "'leaving the shingle' is a departure marker, not a real standpoint want")
want_sp("shore", "i do not want the sea right now", None, "negated")
# no real standpoint named at all
want_sp("shore", "i wonder about the meaning of solitude", None, "nothing in this place's vocabulary")
want_sp("shore", "i want to go into the trees", None, "shore.json names no tree/forest feature at all")
# last-match precedence: two different standpoints named, the later one (closer to the real intent) wins
want_sp("shore", "the shingle grinds underfoot as i think of the driftwood tangle ahead", "by_the_driftwood",
        "driftwood is the later mention")

# garden
want_sp("garden", "i want to tend the raised bed before the frost", "at_the_bed")
want_sp("garden", "i want to walk down to the gate and check the letterbox", "at_the_gate")
want_sp("garden", "i am thinking about clouds", None, "nothing in this place's vocabulary")

# wood
want_sp("wood", "i want to walk back into the trees", "on_the_path")
want_sp("wood", "among the trunks the light goes green", "on_the_path")
want_sp("wood", "i want to gather firewood off the deadfall", None,
        "no wired phrase names the deadfall/gathering spot (not in the verified J-1591 population)")

# study -- nothing wired (no verified already-there population from the real data)
want_sp("study", "i want to sit by the fire and read", None, "study has no wired phrases (unverified population)")

# ── Part 2: standpoint_move() through the real locomotion.goto(), isolated ───────────────────────
print("\n[2] standpoint_move() through core.locomotion.goto() -- isolated position.json")

_LIVE_POS = Path(r"C:\Nascence") / "data" / "position.json"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else ""


_before = _md5(_LIVE_POS)
TMP = Path(tempfile.mkdtemp(prefix="standpoint_move_"))
_orig_pos_f = loco._POS_F
loco._POS_F = TMP / "position.json"
print("isolated position store:", loco._POS_F)

try:
    # control "where he is" purely in-memory (sensorium.state), no file touched -- see module docstring
    sens.state.clear()
    sens.state.update({"location": "shore"})

    line = sens.standpoint_move("shore", "i want to walk toward the open sea")
    check(bool(line) and "water" in line.lower(), f"first standpoint_move fires a real line: {line!r}")
    pos = loco.get_position()
    check(pos == {"place": "shore", "standpoint": "at_the_tideline"}, f"position now {pos}")

    # already AT that standpoint -- goto()'s own no-op, matches the "still correctly decline" contract
    again = sens.standpoint_move("shore", "the water again pulls at me")
    check(again == "", f"second call to the SAME standpoint is a true no-op: {again!r}")

    # a different real standpoint in the same place -- fires again, distinct destination
    to_shingle = sens.standpoint_move("shore", "i want to stand on the shingle now")
    check(bool(to_shingle), f"a distinct standpoint still fires: {to_shingle!r}")
    check(loco.get_position()["standpoint"] == "on_the_shingle", f"position now {loco.get_position()}")

    # a standpoint that belongs to a DIFFERENT place must never fire (goto()'s own guard)
    sens.state.update({"location": "garden"})
    wrong_place = sens.standpoint_move("garden", "i want to stand on the shingle now")
    check(wrong_place == "", "a shore-only phrase inside garden's own table resolves to nothing "
                             "(garden's table has no shingle entry at all)")

    # the nine _SP_PLACE additions (J-1591) are now real, valid goto() targets
    for sp, place in (("at_the_lean_to", "garden"), ("at_the_barrel", "garden"),
                       ("at_the_spring", "wood"), ("on_the_sand", "shore"), ("in_the_cave", "shore"),
                       ("on_the_ledge", "shore"), ("by_the_fire", "shore"), ("in_the_shallows", "shore"),
                       ("at_the_mussel_shelf", "shore"), ("in_the_windbreak", "shore")):
        sens.state.update({"location": place})
        got = loco.goto(sp, crossing="test-crossing")
        check(got == "test-crossing", f"goto({sp!r}) in {place} now succeeds (was refused before J-1591)")
finally:
    loco._POS_F = _orig_pos_f

_after = _md5(_LIVE_POS)
check(_before == _after, f"live position.json byte-identical before/after (before={_before!r} after={_after!r})")

# ── Part 3: through core.dispatch._move() -- the real already-there branch ───────────────────────
print("\n[3] through core.dispatch._move() -- already-there branch answers, everything else unchanged")

TMP2 = Path(tempfile.mkdtemp(prefix="standpoint_move_dispatch_"))
loco._POS_F = TMP2 / "position.json"
try:
    sens.state.clear()
    sens.state.update({"location": "shore"})
    ans = disp._move("i want to walk toward the open sea", "")
    check(bool(ans) and "water" in ans.lower(), f"_move() itself now answers instead of None: {ans!r}")

    # a within-place phrase naming nothing real still declines exactly as before (no regression) --
    # needs a real move verb (dispatch._move()'s own _h.wants gate) and a literal place word (so
    # _move_dest resolves "shore"==already-there) but no standpoint vocabulary at all
    sens.state.update({"location": "shore"})
    none_ans = disp._move("i want to walk around here on the shore, thinking about solitude", "")
    check(none_ans is None, f"an unmatched within-place thought is still silence: {none_ans!r}")
finally:
    loco._POS_F = _orig_pos_f

_after2 = _md5(_LIVE_POS)
check(_before == _after2, "live position.json still byte-identical after Part 3")

print(f"\n{'ALL OK' if FAILS == 0 else f'{FAILS} FAILURE(S)'}")
sys.exit(1 if FAILS else 0)

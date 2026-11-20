"""
_test_garden_trap_kill.py — J-0974 (plan world_store_write_fence): core.garden.check_trap()'s
"a possum/hedgehog was actually caught" branch had ZERO test coverage in either regression
script, confirmed empirically by J-0920's own re-verification audit
(scratchpad/audit_J-0920_stage_gating.py, 2026-09-14, F-1347): both scripts/_test_garden_
grammar_derivation.py and scripts/life_smoke.py only ever exercise check_trap()'s "nothing
caught, unset/armed" report paths -- armed is False by default, and even after set_trap() arms
it, nothing ever sets tr["caught"] without core.life's own night_pass simulation actually
running, which neither script drives.

Technique: rig _trap_st(st)["caught"] = {"species": ..., "ts": ...} directly into garden's own
cached state before calling check_trap() -- the same "rig a real candidate directly into the
store's own cached state" pattern J-0920 already used and documented (this plan's own
docs/staged/world_store_write_fence.md, 2026-09-14 dated Current State note; garden._load()
returns its module-level _state dict BY REFERENCE, confirmed by F-1056, so no intervening
_save() is needed for the rig to take effect on the next check_trap() call).

Covers, per this job's own briefing:
  1. the kill narration text, both species branches (possum, and the hedgehog "wrong animal"
     branch D-0130's own named defeater describes -- a trap with no weight can kill the wrong
     animal);
  2. core.garden's own bookkeeping (kills incremented, caught/armed reset, a check_trap ledger
     row);
  3. core.life's carcass/kill ledger entry (_life._log's own kind=kill row, plus the carcasses
     list entry landed via _life._save());
  4. core.sitting.note_difficulty is called with the right diff text -- MOCKED rather than
     redirected: a fresh grep of core/sitting.py confirms zero `profile`/`guard_path()`
     references anywhere in the file (its own _STATE/_RELEASE_LOG constants are a different,
     out-of-this-fence "scheduling/cognitive bookkeeping" class, the same one this plan has
     already established for practical_lesson.py's/nature_study.py's own persistence -- see
     e.g. this doc's J-0795/J-0782 notes). Mocking isolates this one call's own shape, matching
     this plan's own dominant verification idiom, rather than depending on wherever
     core.sitting's own unrelated data file happens to resolve;
  5. the isolation itself actually holds: a deliberately under-isolated case (core.life left
     OUT of the redirect list -- the exact "easy-to-forget pairs" class lab_env.py's own
     docstring warns about, F-1269/F-1270) confirms check_trap() raises
     profile.NonLiveWriteError out through BOTH its own try/except layers rather than silently
     dropping the carcass/kill record -- the same "does the carve-out actually hold, not just
     read correctly" empirical standard this plan's whole audit chain applies everywhere else.

Isolation: lab_env.isolate() (this job's own briefing marks isolation REQUIRED); also= covers
core.garden (_F, _LEDGER, _EVENTS) and core.life (_F, _LEDGER, _EVENTS, _FLAGS_F) -- the
minimum the briefing names. core.sitting is mocked, not redirected, per item 4 above. Invoke
with PYTHONPATH set to the real C:\\Nascence (matching J-0862/F-1285's own established fix for
lab_env.py's own sys.path[0] insert of C:\\Nascence on import, which would otherwise shadow
this worktree's own copy of core.* the moment lab_env is imported) so this script's own earlier
sys.path insert of its own worktree root stays in front; the __file__ self-check below fails
loudly rather than silently testing the wrong tree if that ever regresses. Never touches live
data/.

Exit 1 on any failed check. Run (from the worktree root, so ROOT below resolves correctly):
  PYTHONPATH=C:\\Nascence python -X utf8 scripts/_test_garden_trap_kill.py
"""
from __future__ import annotations

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
from core import garden as G, life as LIFE, sensorium as S, profile  # noqa: E402

FAIL: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        FAIL.append(name)


def ledger_rows(path) -> list:
    try:
        return [json.loads(line) for line in open(path, encoding="utf-8")]
    except OSError:
        return []


# ── self-check: are we really testing THIS worktree's own code, not C:\Nascence's? ────────────
for _mod in (G, LIFE, S, profile):
    check(f"{_mod.__name__} resolves under this worktree, not C:\\Nascence",
          str(ROOT) in str(Path(_mod.__file__).resolve()), _mod.__file__)


def _bootstrap_garden() -> None:
    # G._load() caches its own module-level _state dict by reference (F-1056) and this cache
    # is NOT reset just because a lab_env.isolate() block exits/re-enters -- only the PATH
    # constants (_F/_LEDGER/_EVENTS) get redirected/restored. Clearing it here forces the next
    # _load() to do a genuine fresh bootstrap read from whatever _F currently resolves to,
    # matching how a real cold process behaves -- required so this helper gives each of the two
    # `with isolate(...)` blocks below a truly independent starting trap state (first found the
    # hard way: without this, Case 4's own trap["kills"] inherited Case 1-3's already-incremented
    # in-memory count instead of starting fresh).
    G._state = None
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0,
                     "last_event": 0, "location": "garden", "garden": S._fresh_garden()})


# ── Cases 1-3: fully isolated ───────────────────────────────────────────────────────────────
with isolate(also=[(G, ["_F", "_LEDGER", "_EVENTS"]),
                    (LIFE, ["_F", "_LEDGER", "_EVENTS", "_FLAGS_F"])],
             db="empty") as lab_dir:
    print(f"isolated lab dir: {lab_dir}\n")
    _bootstrap_garden()
    gst = G._load()

    # ── Case 1: a possum in the trap ────────────────────────────────────────────────────────
    tr = G._trap_st(gst)
    tr.update({"armed": True, "where": "under_the_tree", "bait_taken": False,
               "caught": {"species": "possum", "ts": time.time() - 3600}})

    life_ledger_before = len(ledger_rows(LIFE._LEDGER))
    life_carcasses_before = len(LIFE._load().get("carcasses", []))

    with mock.patch("core.sitting.note_difficulty") as m_note:
        line = G.check_trap("")

    check("possum narration is the possum branch, not the hedgehog one",
          "A possum lies in it" in line and "hedgehog" not in line, line)

    tr_after = G._trap_st(G._load())
    check("trap state resets after a kill is checked (kills+1, caught cleared, unarmed)",
          tr_after["kills"] == 1 and tr_after["caught"] is None and tr_after["armed"] is False, tr_after)

    g_rows = ledger_rows(G._LEDGER)
    check("garden's own ledger gained a check_trap/found=possum row",
          any(r.get("deed") == "check_trap" and r.get("found") == "possum" for r in g_rows), g_rows)

    life_rows = ledger_rows(LIFE._LEDGER)
    check("core.life's ledger gained exactly one kind=kill row for the possum",
          len(life_rows) == life_ledger_before + 1 and life_rows[-1].get("kind") == "kill"
          and life_rows[-1].get("key") == "possum" and life_rows[-1].get("place") == "garden"
          and life_rows[-1].get("by") == "trap", life_rows[-1:])

    carcasses = LIFE._load().get("carcasses", [])
    check("core.life's own state gained one fresh possum carcass in the garden, cause=trap",
          len(carcasses) == life_carcasses_before + 1 and carcasses[-1].get("species") == "possum"
          and carcasses[-1].get("place") == "garden" and carcasses[-1].get("cause") == "trap"
          and carcasses[-1].get("state") == "fresh", carcasses[-1:])

    check("core.sitting.note_difficulty called once, kind='deed', naming the possum",
          m_note.call_count == 1 and m_note.call_args.kwargs.get("kind") == "deed"
          and "possum" in m_note.call_args.args[0], m_note.call_args)

    # ── Case 2: the hedgehog branch -- different narration/diff, same bookkeeping shape ──────
    tr2 = G._trap_st(G._load())
    tr2.update({"armed": True, "where": "under_the_tree", "bait_taken": False,
                "caught": {"species": "hedgehog", "ts": time.time() - 1800}})
    life_ledger_before2 = len(ledger_rows(LIFE._LEDGER))

    with mock.patch("core.sitting.note_difficulty") as m_note2:
        line2 = G.check_trap("")

    check("hedgehog narration is the wrong-animal branch, not the possum one",
          "hedgehog lies in it" in line2 and "A possum lies in it" not in line2, line2)

    life_rows2 = ledger_rows(LIFE._LEDGER)
    check("core.life's ledger gained a second kind=kill row, key=hedgehog this time",
          len(life_rows2) == life_ledger_before2 + 1 and life_rows2[-1].get("key") == "hedgehog", life_rows2[-1:])

    # NOTE: the real hedgehog diff text legitimately mentions "possum" too, for deliberate
    # narrative contrast ("...killed the hedgehog ... not the possum you set it for") -- so the
    # distinguishing check is "killed the hedgehog" (unique to this branch) present and the
    # possum diff's own distinguishing phrase ("your hand did this") absent, not a bare
    # "possum" not in text (an earlier draft of this check asserted that and correctly FAILED
    # against the real source text -- a bug in the check, not in check_trap()).
    check("note_difficulty's diff text is the hedgehog branch's own, not the possum branch's",
          m_note2.call_count == 1 and "killed the hedgehog" in m_note2.call_args.args[0]
          and "your hand did this" not in m_note2.call_args.args[0], m_note2.call_args)

    # ── Case 3: negative control -- the un-caught, still-armed report path (J-0920's own
    #    already-confirmed no-op) must stay unchanged by this new coverage ───────────────────
    tr3 = G._trap_st(G._load())
    tr3.update({"armed": True, "caught": None, "bait_taken": False})
    line3 = G.check_trap("")
    check("the un-caught, still-armed report path is unchanged (J-0920's own confirmed no-op)",
          "bait untouched" in line3, line3)

# ── Case 4: isolation itself -- core.life deliberately left OUT of the redirect list must
#    raise profile.NonLiveWriteError out of check_trap(), not silently drop the carcass/kill
#    record -- proving the existing two-layer `except profile.NonLiveWriteError: raise` carve-
#    out (the inner life.py try, then check_trap()'s own outer try) actually holds ───────────
with isolate(also=[(G, ["_F", "_LEDGER", "_EVENTS"])], db="empty") as lab_dir:
    print(f"\nunder-isolated lab dir (core.life deliberately NOT redirected): {lab_dir}\n")
    _bootstrap_garden()
    gst4 = G._load()
    tr4 = G._trap_st(gst4)
    tr4.update({"armed": True, "where": "under_the_tree", "bait_taken": False,
                "caught": {"species": "possum", "ts": time.time()}})

    raised = None
    try:
        G.check_trap("")
    except profile.NonLiveWriteError as exc:
        raised = exc
    except Exception as exc:  # pragma: no cover -- report, don't hide
        raised = exc

    check("an under-isolated core.life raises NonLiveWriteError out of check_trap(), not a silent drop",
          isinstance(raised, profile.NonLiveWriteError), repr(raised))

    # garden's own side is unwrapped and resolves guard_path() (already-redirected, so it succeeds)
    # BEFORE the life.py inner try ever runs -- confirming this is a real partial-completion-then-
    # raise, the documented shape, not evidence check_trap() never ran at all.
    tr4_after = G._trap_st(G._load())
    check("garden's own side (kills/caught/armed) still completed before the life.py raise fired",
          tr4_after["kills"] == 1 and tr4_after["caught"] is None and tr4_after["armed"] is False, tr4_after)

print("\n" + "=" * 60)
if FAIL:
    print(f"{len(FAIL)} CHECK(S) FAILED:")
    for name in FAIL:
        print(" -", name)
    sys.exit(1)
print("ALL CHECKS PASSED")

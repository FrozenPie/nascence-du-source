"""Isolated unit test for J-1316's fix (F-1861): widen core/orchestrator.py's
recache_grounded_scalars() gate so it fires on EITHER AFFECT_SOURCE_PROTOSELF or
AFFECT_SOURCE_AROUSAL, not PROTOSELF alone.

Background (see F-1861, docs/plans/emotion_rethink.md): core/mood.py's
recache_grounded_scalars() is the 2026-08-19 hot-cycle provenance fix -- it re-caches the
scalar felt-quality from the GROUNDED affect object after mood.observe(state.emotion) cached
it from the raw LLM guess. Its one call site (core/orchestrator.py) used to gate on
AFFECT_SOURCE_PROTOSELF alone, even though a few lines earlier in the SAME cycle,
AFFECT_SOURCE_AROUSAL's own apply block (core/arousal.py:apply_to(), built by J-1306) grounds
state.affect.arousal on human-turn cycles. If AROUSAL were ever flipped True while PROTOSELF
were False, the old gate would silently skip the re-cache and reproduce the 2026-08-19 bug for
arousal. Dormant today only because PROTOSELF has been True since 2026-07-07.

Why extraction-and-exec, not a real Orchestrator call: core.orchestrator's cycle method is one
large async function wired to live nodes/DB/LLM clients -- constructing a real Orchestrator is
not an isolated unit test. Instead this test reads the ACTUAL current source of
core/orchestrator.py, extracts the exact try/except block that gates the
_mood.recache_grounded_scalars() call (the same extract-and-exec technique
scripts/_test_j1311_shadow_tiebreak_seat.py and scripts/_test_j1198_disprove_walkback.py already
use for pieces embedded in unimportable/heavy modules), and execs it against fakes for
`_mood`/`self`/`logger` -- so this test runs the REAL shipped condition text, not a hand-copied
re-implementation that could silently drift from it.

Checks:
  1. The real fixed block fires recache_grounded_scalars() on all three flag combinations where
     EITHER flag is True (PROTOSELF-only, AROUSAL-only, both), and does NOT fire when both are
     False -- the truth table F-1861's fix promises.
  2. A NEGATIVE CONTROL proves the harness is discriminating, not vacuous: the OLD, pre-fix
     condition text (hardcoded below, byte-identical to what this job's commit replaced) is run
     through the SAME harness and shown to (a) fire on PROTOSELF-only -- matching its own
     documented pre-fix behaviour -- but (b) NOT fire on AROUSAL-only -- reproducing the exact
     gap F-1861 flagged. If either negative-control check came out the other way, this test
     would not be trustworthy evidence about the real fix.
  3. core/schema.py's live flags are read (never written to any file -- only monkeypatched on
     the already-imported module object for the duration of each case, then restored) to report
     today's real values, so the report can state plainly whether production behaviour changed.

No live state, no DB, no network, no file writes, no import of core.orchestrator itself (its
source is only read as text). Run:
    python scripts/_test_j1316_mood_arousal_gate.py
Exit 0 = every check passed.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ORCH_PATH = ROOT / "core" / "orchestrator.py"
START_MARK = "from core import schema as _sch2"
END_MARK = 'logger.debug("[affect] grounded scalar re-cache failed (non-fatal): %s", exc)'

# The exact pre-fix block this job's commit replaced (core/orchestrator.py, PROTOSELF-only gate).
# Hardcoded here ONLY as a negative control -- see check 2 above -- never used as the thing under
# test.
OLD_PRE_FIX_BLOCK = textwrap.dedent('''\
    try:
        from core import schema as _sch2
        if getattr(_sch2, "AFFECT_SOURCE_PROTOSELF", False):
            _mood.recache_grounded_scalars(self.state.affect)
    except Exception as exc:
        logger.debug("[affect] grounded scalar re-cache failed (non-fatal): %s", exc)
''')


def extract_block(src: str) -> str:
    """Pull the real try/except block (the enclosing `try:` through the except's logger.debug
    line) out of orchestrator.py's actual current source, dedented to standalone-execable code."""
    start_idx = src.index(START_MARK)
    try_idx = src.rindex("try:", 0, start_idx)
    line_start = src.rfind("\n", 0, try_idx) + 1  # include the try line's own leading whitespace
    end_idx = src.index(END_MARK, start_idx) + len(END_MARK)
    return textwrap.dedent(src[line_start:end_idx])


def run_block(code: str, protoself: bool, arousal: bool) -> bool:
    """Exec the block with fakes for _mood/self/logger, with core.schema's real flags
    monkeypatched (in-memory only, restored in finally) for the duration of the call. Returns
    True iff recache_grounded_scalars() was called exactly once."""
    calls = []

    class FakeMood:
        @staticmethod
        def recache_grounded_scalars(obj):
            calls.append(obj)

    import core.schema as real_schema
    sentinel = object()
    orig_protoself = getattr(real_schema, "AFFECT_SOURCE_PROTOSELF", sentinel)
    orig_arousal = getattr(real_schema, "AFFECT_SOURCE_AROUSAL", sentinel)
    try:
        real_schema.AFFECT_SOURCE_PROTOSELF = protoself
        real_schema.AFFECT_SOURCE_AROUSAL = arousal
        fake_affect = object()
        fake_self = SimpleNamespace(state=SimpleNamespace(affect=fake_affect))
        ns = {
            "_mood": FakeMood,
            "self": fake_self,
            "logger": SimpleNamespace(debug=lambda *a, **k: None),
        }
        exec(compile(code, "<orchestrator-recache-block>", "exec"), ns)
    finally:
        if orig_protoself is sentinel:
            delattr(real_schema, "AFFECT_SOURCE_PROTOSELF")
        else:
            real_schema.AFFECT_SOURCE_PROTOSELF = orig_protoself
        if orig_arousal is sentinel:
            delattr(real_schema, "AFFECT_SOURCE_AROUSAL")
        else:
            real_schema.AFFECT_SOURCE_AROUSAL = orig_arousal

    if len(calls) > 1:
        raise AssertionError(f"recache_grounded_scalars() called {len(calls)} times, expected 0 or 1")
    if calls and calls[0] is not fake_affect:
        raise AssertionError("recache_grounded_scalars() called with the wrong object")
    return bool(calls)


def main() -> int:
    src = ORCH_PATH.read_text(encoding="utf-8")
    block = extract_block(src)
    print("=== extracted live block from core/orchestrator.py ===")
    print(block)
    print("=== end block ===\n")

    if "AFFECT_SOURCE_AROUSAL" not in block:
        print("FAIL: extracted block does not mention AFFECT_SOURCE_AROUSAL -- "
              "fix not present, or the anchor text has drifted from what this test expects.")
        return 1

    failures = []

    # --- 1. the real, fixed block: full truth table ---
    cases = [
        (False, False, False, "neither flag"),
        (True, False, True, "PROTOSELF only (today's real production state: schema.py confirms "
                             "PROTOSELF=True, AROUSAL=False)"),
        (False, True, True, "AROUSAL only -- the exact gap F-1861 flagged"),
        (True, True, True, "both flags"),
    ]
    for protoself, arousal, expect_fire, label in cases:
        fired = run_block(block, protoself, arousal)
        status = "OK" if fired == expect_fire else "FAIL"
        print(f"[{status}] fixed block: PROTOSELF={protoself} AROUSAL={arousal} ({label}): "
              f"fired={fired} expected={expect_fire}")
        if fired != expect_fire:
            failures.append(f"fixed block {label}: fired={fired} expected={expect_fire}")

    # --- 2. negative control: the OLD pre-fix text must reproduce the documented gap ---
    old_fired_arousal_only = run_block(OLD_PRE_FIX_BLOCK, False, True)
    print(f"\n[negative control] OLD pre-fix block, PROTOSELF=False AROUSAL=True: "
          f"fired={old_fired_arousal_only} (must be False -- this is the bug F-1861 found)")
    if old_fired_arousal_only:
        failures.append("negative control: old block fired on AROUSAL-only -- "
                         "harness does not actually discriminate the fix")

    old_fired_protoself_only = run_block(OLD_PRE_FIX_BLOCK, True, False)
    print(f"[info] OLD pre-fix block, PROTOSELF=True AROUSAL=False: "
          f"fired={old_fired_protoself_only} (must be True -- its own documented pre-fix case)")
    if not old_fired_protoself_only:
        failures.append("negative control: old block failed to fire on its own documented "
                         "PROTOSELF-only case -- negative control itself is broken")

    # --- 3. report today's real live flag values (read-only) ---
    import core.schema as real_schema
    live_protoself = getattr(real_schema, "AFFECT_SOURCE_PROTOSELF", None)
    live_arousal = getattr(real_schema, "AFFECT_SOURCE_AROUSAL", None)
    print(f"\n[info] live core/schema.py values (unmodified by this test, restored after every "
          f"case above): AFFECT_SOURCE_PROTOSELF={live_protoself!r} "
          f"AFFECT_SOURCE_AROUSAL={live_arousal!r}")
    if live_protoself is True and live_arousal is False:
        print("[info] => today's real flag combination already fired under the OLD gate too; "
              "this fix is a zero-behaviour-change hardening for a future AROUSAL flip, not a "
              "live behaviour change today.")

    if failures:
        print(f"\nFAIL: {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\nPASS: {len(cases)} flag-combination checks + 2 negative-control checks, all green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

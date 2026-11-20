"""
Regression test for F-1683/J-1199: core.model_client.call_node() writes THREE telemetry rows per
call -- log_llm_call, log_thought_station and log_llm_latency, each appended at a path derived from
core/telemetry.py's own __file__ -- and the 11 older lab scripts that "isolated telemetry" (before
this job) neutralised only the first, because the other two postdated when most of them were written.

This test runs a STUBBED call_node (no core.model_client import, no aiohttp, no network I/O, no Du
hot-lane contention -- reproduces call_node()'s own telemetry call sequence verbatim, core/
model_client.py lines 255/265/331 at commit a9f042f) under scripts/lab_isolation.py's
neutralize_telemetry(), and asserts:
  1. module resolution: core.telemetry resolves inside THIS worktree, not the shared tree (F-1285);
  2. the stub genuinely exercises all 3 call sites (a "zero writes" result would be vacuous otherwise
     if the stub silently skipped one -- a spy list proves it did not);
  3. zero write-opens anywhere under the REAL C:\\Nascence\\data or C:\\Nascence\\docs, via the same
     sys.addaudithook pattern this project's own tests already use;
  4. all 3 of telemetry's writer-relevant Path globals (_CALLS, _STATIONS, _LAT) were redirected into
     the given scratch dir;
  5. literally no file was created ANYWHERE by the 3 no-op'd functions (stronger than "redirected" --
     proves they are true no-ops, not just writing somewhere else).

UPDATE 2026-09-22 (D-0252/J-1214): core/telemetry.py itself now carries a central, module-level
LAB_MODE guard (enter_lab_mode()/exit_lab_mode()) that neutralize_telemetry()/restore_telemetry()
also flip, so this test now additionally asserts:
  6. a SIMULATED 4th writer -- one that exists ONLY in this test, is never named in
     lab_isolation.TELEMETRY_NOOP_FUNCS or neutralize_telemetry()'s own no-op loop, and only follows
     the same one-line `if _LAB_MODE: return` convention the 3 real writers now use -- is STILL
     refused while lab mode is active. This is the actual claim D-0252 exists to test: a lab process
     that only ever called neutralize_telemetry() (which has never heard of this hypothetical
     function) must not need to be told its name for it to be blocked;
  7. restore_telemetry() genuinely exits lab mode again (not a one-way latch): after it runs, the
     same simulated writer writes normally once more, and telemetry._LAB_MODE reads False.

SAFETY: every one of core.telemetry's own Path globals is ALSO pre-redirected to a temp dir before
neutralize_telemetry() is even called (belt-and-braces on top of belt-and-braces -- "point every path
at a temp dir, never the live data"), so a bug in the helper being tested could not reach anywhere
real even in principle. A write-audit hook watching the REAL C:\\Nascence\\data/\\docs is installed
before the `core.telemetry` import itself, so an import-time write would be caught too.

MUTATION CHECK (build rule 7 -- not shipped as code here, reported in J-1199's own build report):
a scratch copy of this test with neutralize_telemetry() swapped back for the pre-J-1199 single-line
`telemetry.log_llm_call = lambda *a, **k: None` was run against the same harness and FAILS assertion
5 above (log_thought_station/log_llm_latency, left real, genuinely create a file) -- proving this
test would have caught F-1683's own gap, not just that it passes today.

Run: python scripts/_test_lab_isolation_telemetry.py   -- exit 0 = pass, prints "ALL CHECKS PASSED".
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parent
sys.path.insert(0, str(ROOT))          # this worktree's own root -- `from core import telemetry`
sys.path.insert(0, str(_HERE))         # scripts/ itself -- `from lab_isolation import ...`

from lab_isolation import install_write_audit, neutralize_telemetry, restore_telemetry  # noqa: E402

# Installed BEFORE the repo import below, watching the REAL C:\Nascence\data and \docs -- must read
# zero live_write_attempts / tree_write_attempts at the end of this whole test, unconditionally,
# regardless of anything the scenario below does.
_real_audit = install_write_audit()

from core import telemetry  # noqa: E402


def _assert_module_inside_worktree() -> None:
    f = str(Path(telemetry.__file__).resolve())
    print(f"[test] core.telemetry.__file__ = {f}")
    if not f.lower().startswith(str(ROOT.resolve()).lower()):
        raise AssertionError(f"MODULE-RESOLUTION TRAP (F-1285): core.telemetry resolved OUTSIDE "
                             f"this worktree ({ROOT}): {f}")
    print(f"[test] module resolution OK: inside worktree {ROOT}")


def _simulated_future_writer(spy_calls: list, path: Path) -> None:
    """A hypothetical 4th core.telemetry writer that does not exist today, is deliberately NEVER added
    to lab_isolation.TELEMETRY_NOOP_FUNCS or neutralize_telemetry()'s no-op loop, and only follows the
    same one-line convention the real log_llm_call/log_thought_station/log_llm_latency now use
    (checking telemetry._LAB_MODE first, before its own would-be write). Proves D-0252/J-1214's own
    point under direct test: a caller that only knows about neutralize_telemetry() -- and has never
    heard of this function -- must still see it refused once lab mode is active, because the guard is
    SOURCE-side, not a caller-side registration list."""
    if telemetry._LAB_MODE:
        return
    spy_calls.append("simulated_future_writer:wrote")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write("row\n")


def _stubbed_call_node_telemetry(spy_calls: list, model="qwen3.5:9b",
                                 base_url="http://127.0.0.1:11433", caller="test:_stubbed_call_node") -> None:
    """Reproduces core/model_client.py's call_node() telemetry call sequence (its own lines 255, 265,
    331) with no network call around it -- this IS "a stubbed call_node" the regression test runs.
    spy_calls records which functions actually ran, so a passing "zero writes" result cannot be
    vacuous."""
    telemetry.log_llm_call(model, base_url, prompt_chars=42, num_ctx=8192, capped=False,
                           caller=caller, system_chars=10)
    spy_calls.append("log_llm_call")
    telemetry.log_thought_station(model, base_url, caller)
    spy_calls.append("log_thought_station")
    telemetry.log_llm_latency(model, base_url, caller, 0.42, True)
    spy_calls.append("log_llm_latency")


def main() -> int:
    _assert_module_inside_worktree()
    tmp = Path(tempfile.mkdtemp(prefix="J1199_telemetry_test_"))
    try:
        # SAFETY layer (redundant with neutralize_telemetry()'s own redirect, deliberately): point
        # EVERY one of telemetry's Path globals at tmp before the helper under test ever runs.
        pre_saved = {}
        for name in dir(telemetry):
            val = getattr(telemetry, name, None)
            if isinstance(val, Path) and name.startswith("_"):
                pre_saved[name] = val
                setattr(telemetry, name, tmp / f"pre{name}{val.suffix or '.d'}")

        scratch = tmp / "scratch_a"
        scratch.mkdir()
        saved = neutralize_telemetry(scratch, telemetry)
        print(f"[test] neutralize_telemetry() applied: no-op'd {list(saved['funcs'])}, "
              f"redirected {list(saved['paths'])} into {scratch}")

        spy: list = []
        _stubbed_call_node_telemetry(spy)
        assert spy == ["log_llm_call", "log_thought_station", "log_llm_latency"], (
            f"stub did not exercise all 3 call sites -- a passing zero-writes result would be "
            f"vacuous: {spy}")
        print(f"[test] stub exercised all 3 call sites: {spy}")

        assert not _real_audit.live_write_attempts, (
            f"write attempts under LIVE C:\\Nascence\\data or \\docs: {_real_audit.live_write_attempts}")
        assert not _real_audit.tree_write_attempts, (
            f"write attempts elsewhere under C:\\Nascence: {_real_audit.tree_write_attempts}")

        assert str(telemetry._CALLS).startswith(str(scratch)), "log_llm_call's path was not redirected"
        assert str(telemetry._STATIONS).startswith(str(scratch)), "log_thought_station's path was not redirected"
        assert str(telemetry._LAT).startswith(str(scratch)), "log_llm_latency's path was not redirected"

        for p in (telemetry._CALLS, telemetry._STATIONS, telemetry._LAT):
            assert not Path(p).exists(), f"a supposedly no-op'd telemetry writer still created a file: {p}"
        print("[test] all 3 Path globals redirected into scratch_a; no file created anywhere "
              "(true no-ops, not just relocated writes)")

        # ── D-0252/J-1214: the central SOURCE-side guard, tested independently of the 3 known writers ──
        assert telemetry._LAB_MODE is True, (
            "neutralize_telemetry() must also flip telemetry._LAB_MODE (D-0252/J-1214) so both layers "
            "agree -- it did not")
        future_spy: list = []
        future_path = scratch / "hypothetical_4th_writer.jsonl"
        _simulated_future_writer(future_spy, future_path)
        assert future_spy == [], (
            f"a 4th writer that was NEVER named in TELEMETRY_NOOP_FUNCS still wrote while lab mode "
            f"was active -- the central guard did not protect it: {future_spy}")
        assert not future_path.exists(), (
            "a 4th, never-registered writer created a file while telemetry._LAB_MODE was True")
        print("[test] simulated 4th writer (never in TELEMETRY_NOOP_FUNCS, never known to "
              "neutralize_telemetry()) correctly refused by the central _LAB_MODE guard alone")

        restore_telemetry(telemetry, saved)
        for name, val in pre_saved.items():
            setattr(telemetry, name, val)

        assert telemetry._LAB_MODE is False, (
            "restore_telemetry() must also exit telemetry._LAB_MODE (D-0252/J-1214) -- it is still "
            "True, which would leave the just-restored real writers silently no-op'ing forever")
        future_spy2: list = []
        _simulated_future_writer(future_spy2, future_path)
        assert future_spy2 == ["simulated_future_writer:wrote"], (
            f"after restore_telemetry(), the simulated writer should write normally again (lab mode "
            f"exited) but did not: {future_spy2}")
        assert future_path.exists(), "post-restore write did not actually create its (scratch) file"
        future_path.unlink()
        print("[test] restore_telemetry() correctly exits lab mode (not a one-way latch) -- the same "
              "simulated writer writes normally again")

        print("\n" + _real_audit.summary("final"))
        print("\nALL CHECKS PASSED (3/3 telemetry writers neutralised, simulated 4th writer refused "
              "by the central guard alone, restore verified reversible, 0 live writes, module "
              "resolution confirmed inside worktree)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

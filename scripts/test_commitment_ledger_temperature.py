"""
Test suite — commitment_ledger.scan_shadow call-site temperature (J-1213, D-0176, F-1693/F-1696,
2026-09-22).

D-0176 (ruled 2026-09-22): set temperature=0.0 at the commitment_ledger.scan_shadow LLM call, on
today's seat (qwen3.5:9b, the hot lane) — F-1693 measured 16/40 identical-input gate flips at the
production temperature (0.3) and 0/20 at temperature 0.0 (byte-identical raw output every time).
F-1696's caveat (temp 0 is NOT verified for the llama.cpp CPU-hub seats) is a live-behaviour claim,
not something this hermetic test can check — see scripts/d0176_scan_bakeoff.py / F-1693 / F-1696 for
that evidence instead. This test only proves the ONE thing a code change can prove locally: the
outgoing call now actually carries temperature=0.0, and no other kwarg the call site was already
passing (max_tokens, tier) silently changed alongside it.

This test is HERMETIC: no real LLM, no real hub. `call_json` is replaced with a fake coroutine that
records every kwarg it was invoked with (not just temperature) and returns a minimal valid verdict
(`new_commitment: None, dissolutions: []`) so the run never touches the reaffirm/embedding path —
that path is scripts/test_commitment_ledger_race.py's concern, not this test's.

ISOLATION: same pattern as scripts/test_commitment_ledger_race.py — every path
commitment_ledger.py can write to (_DIR/_LEDGER/_ACTIVE/_OBSERVED/_HOLDRATE_LOG) is redirected to a
fresh tempfile.mkdtemp() before the scan runs, restored in a `finally` block. Nothing under data/ is
read or written.

MUTATION CHECK: this file is designed to be copied byte-for-byte into a throwaway worktree of the
pre-fix commit (base 42a11f9, before J-1213's edit) and run there — see this job's own finding for
that run's output. Against the unfixed call site (temperature=0.3) the
"call carries temperature=0.0" check below must FAIL; against the fix it must PASS. That is the
proof this test is actually exercising the changed line, not a tautology.

Run: python scripts/test_commitment_ledger_temperature.py
"""
from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("  [OK] " if ok else "  [FAIL] ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        fails.append(name)


print("— commitment_ledger scan_shadow call-site temperature (J-1213/D-0176) —")
from core import commitment_ledger as cl

# MODULE-RESOLUTION PROOF (F-1285): confirm we are exercising THIS worktree's/dir's copy, not a
# shared C:\Nascence copy some other script's sys.path insertion could have shadowed it with.
print(f"  module under test: {cl.__file__}")
check("commitment_ledger loaded from this tree", str(ROOT).lower() in str(Path(cl.__file__).resolve()).lower(),
      f"ROOT={ROOT} cl.__file__={cl.__file__}")

_orig = dict(_DIR=cl._DIR, _LEDGER=cl._LEDGER, _ACTIVE=cl._ACTIVE, _OBSERVED=cl._OBSERVED,
             _HOLDRATE_LOG=cl._HOLDRATE_LOG)

captured_calls: list[dict] = []


async def _fake_call_json(base_urls, system_prompt, user_prompt, **kwargs):
    """Records every kwarg the call site actually passed (temperature, max_tokens, tier, ...);
    returns a minimal verdict that forms no commitment and dissolves nothing, so the run never
    enters the reaffirm/embedding or formation-gate/logging paths — this test's only concern is
    the outgoing request, not what scan_shadow then does with the reply."""
    captured_calls.append(dict(kwargs))
    return {"new_commitment": None, "dissolutions": []}


def _redirect(tmp: Path) -> None:
    cl._DIR = tmp
    cl._LEDGER = tmp / "commitment_ledger.jsonl"
    cl._ACTIVE = tmp / "commitment_active.json"
    cl._OBSERVED = tmp / "commitment_observed.jsonl"
    cl._HOLDRATE_LOG = tmp / "commitment_holdrate.jsonl"


TMP = Path(tempfile.mkdtemp(prefix="j1213_temp_"))
try:
    _redirect(TMP)
    cl._scan_lock = None  # fresh lock for this scenario's own event loop (same reason as the race test)

    thought = "a thought long enough to clear the 25-char formation gate, checking the call payload"
    asyncio.run(cl.scan_shadow(_fake_call_json, ["http://fake"], thought, cycle_id="temp-test"))

    check("exactly one LLM call made", len(captured_calls) == 1, f"got {len(captured_calls)}")
    if captured_calls:
        call = captured_calls[0]
        print(f"  captured call kwargs: {call}")
        check("call carries temperature=0.0 (D-0176's fix)",
              call.get("temperature") == 0.0, f"temperature={call.get('temperature')!r}")
        check("temperature is a float 0.0, not e.g. the string '0.0' or int 0 misread later",
              isinstance(call.get("temperature"), float), f"type={type(call.get('temperature'))}")
        # Unrelated kwargs at this same call site must be untouched — proves this was a one-parameter
        # edit, not a drive-by rewrite of the whole call.
        check("max_tokens unchanged (400)", call.get("max_tokens") == 400, f"max_tokens={call.get('max_tokens')!r}")
        check("tier unchanged (3)", call.get("tier") == 3, f"tier={call.get('tier')!r}")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
    cl._DIR, cl._LEDGER, cl._ACTIVE = _orig["_DIR"], _orig["_LEDGER"], _orig["_ACTIVE"]
    cl._OBSERVED, cl._HOLDRATE_LOG = _orig["_OBSERVED"], _orig["_HOLDRATE_LOG"]

# ── SIBLING CHECK: _judge_defeater's OWN call (a different call site, temperature=0.2) must be ──
# ── UNAFFECTED — D-0176 scopes this fix to scan_shadow's call only, not every call in the file. ──
import inspect
src = inspect.getsource(cl._judge_defeater)
check("_judge_defeater's own call site is untouched (still temperature=0.2, a different call site "
      "than D-0176 scopes this fix to)", "temperature=0.2" in src, "expected literal temperature=0.2 in source")

print()
if fails:
    print(f"[FAIL] {len(fails)} FAILURES: {fails}")
    sys.exit(1)
print("ALL COMMITMENT-LEDGER TEMPERATURE TESTS PASS")

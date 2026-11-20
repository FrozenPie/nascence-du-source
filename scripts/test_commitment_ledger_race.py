"""
Test suite — commitment_ledger.scan_shadow overlapping-task race (J-1203, F-1691, 2026-09-22).

F-1691 (J-0842, inferred from a ledger-vs-active-file replay) found that core.commitment_ledger's
scan_shadow does load_active() -> await LLM -> save_active(), and is launched fire-and-forget
(asyncio.create_task) from nodes/inner_monologue_node.py with a cooldown measured from LAUNCH, not
completion. Two overlapping scans can therefore each load the SAME on-disk active list, form their
OWN new stand independently, and save -- the second save (last writer wins) overwrites the first's
formed stand, which is never seen again by anything that reads commitment_active.json even though
the ledger's own append-only event log (commitment_ledger.jsonl) still holds BOTH `formed` events.

This test reproduces that race HERMETICALLY: no real LLM, no real clock race, no real data touched.
Two scan_shadow() coroutines are started as asyncio tasks against a fake call_json whose reply is
gated by an asyncio.sleep() of a controlled duration -- the SHORT-delay task resolves and saves
first, the LONG-delay task resolves and saves second, overwriting the short task's save with a
stale copy loaded before the short task ever wrote. Deterministic under asyncio's single-threaded
cooperative scheduler (a 0.05s vs 0.35s gap leaves ample margin) -- not a sleep-and-hope timing test.

ISOLATION: every path commitment_ledger.py can write to (_DIR/_LEDGER/_ACTIVE/_OBSERVED/
_HOLDRATE_LOG) is redirected to a fresh tempfile.mkdtemp() before any scan runs, restored in a
`finally` block. core.memory.store._embed is monkey-patched to a fast deterministic no-op (returns
None, same as a real embedding failure) so the reaffirm-check path's `from core.memory.store import
_embed` (executed unconditionally whenever a new_commitment is detected, real code, not a test
artifact) falls back to its own existing Jaccard path instead of lazy-loading a real ~90MB
sentence-transformers model -- keeps the test hermetic and fast without changing which code path of
scan_shadow's own logic is exercised (the Jaccard fallback is the same branch a real embedding
failure already takes). Nothing under data/ is read or written; commitment_ledger._stakes()'s
sqlite3.connect() for a `formed` load-bearing stand is left unpatched on purpose -- it targets the
(redirected) temp _DIR, has no `memory/nascence.db` under it, and commitment_ledger.py's own
try/except around that call is exactly the fail-open behaviour being exercised, not worked around.

TEST-ONLY GOTCHA (not a production bug -- scripts/run_nascence.py wraps Du's whole process in ONE
`asyncio.run(main())`, never a fresh one per cycle): this file runs two independent scenarios, each
its own `asyncio.run()` call, i.e. its own event loop. Python 3.10+'s asyncio.Lock binds to whatever
loop is running the first time it is actually CONTENDED (an uncontended acquire's fast path never
touches the loop) and raises RuntimeError if reused under contention from a second loop -- so
cl._scan_lock (the lazily-created lock the fix itself adds) is explicitly reset to None before each
scenario below, giving each its own fresh lock the way each real Du process start would.

Run: python scripts/test_commitment_ledger_race.py
"""
from __future__ import annotations

import asyncio
import json
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


print("— commitment_ledger race (J-1203/F-1691) —")
from core import commitment_ledger as cl
import core.memory.store as _store

# MODULE-RESOLUTION PROOF (F-1285): confirm we are exercising THIS worktree's copy, not a shared
# C:\Nascence copy some other script's sys.path insertion could have shadowed it with.
print(f"  module under test: {cl.__file__}")
check("commitment_ledger loaded from this worktree", str(ROOT).lower() in str(Path(cl.__file__).resolve()).lower(),
      f"ROOT={ROOT} cl.__file__={cl.__file__}")

# Save every module-global this test touches, to restore in `finally` (never leave a patched module
# behind for any other test/process that might import it later in the same interpreter).
_orig = dict(_DIR=cl._DIR, _LEDGER=cl._LEDGER, _ACTIVE=cl._ACTIVE, _OBSERVED=cl._OBSERVED,
             _HOLDRATE_LOG=cl._HOLDRATE_LOG)
_orig_embed = _store._embed
_store._embed = lambda text: None   # deterministic "embedding unavailable" -> real Jaccard fallback


def _fake_call_json(statement: str, delay: float):
    async def _call(base_urls, system_prompt, user_prompt, **kwargs):
        await asyncio.sleep(delay)
        return {"new_commitment": {"statement": statement, "scope": "race-test", "load_bearing": True},
                "dissolutions": []}
    return _call


def _redirect(tmp: Path) -> None:
    cl._DIR = tmp
    cl._LEDGER = tmp / "commitment_ledger.jsonl"
    cl._ACTIVE = tmp / "commitment_active.json"
    cl._OBSERVED = tmp / "commitment_observed.jsonl"
    cl._HOLDRATE_LOG = tmp / "commitment_holdrate.jsonl"


async def _run_two_overlapping(stmt_a: str, delay_a: float, stmt_b: str, delay_b: float,
                                thought_a: str, thought_b: str):
    """Launch two scan_shadow() tasks the same way inner_monologue_node.py does (fire-and-forget,
    both created before either completes), task A first with the LONGER delay so its load happens
    before B's save and its own save happens AFTER B's -- the exact interleave F-1691 describes
    ('the second's load happens before the first's save')."""
    call_a = _fake_call_json(stmt_a, delay_a)
    call_b = _fake_call_json(stmt_b, delay_b)
    task_a = asyncio.create_task(cl.scan_shadow(call_a, ["http://fake"], thought_a, cycle_id="race-a"))
    task_b = asyncio.create_task(cl.scan_shadow(call_b, ["http://fake"], thought_b, cycle_id="race-b"))
    await asyncio.gather(task_a, task_b)


TMP1 = Path(tempfile.mkdtemp(prefix="j1203_race_2way_"))
try:
    _redirect(TMP1)
    cl._scan_lock = None   # fresh lock for this scenario's own event loop -- see TEST-ONLY GOTCHA above
    # NOTE: the two statements must be TOPICALLY DISTINCT (near-zero word overlap), not just
    # different strings -- scan_shadow's own reaffirm-check (a real, correct feature: "the same
    # stand re-taken in different words" raises the existing stand instead of duplicating it) will
    # otherwise correctly fold the second into a reaffirm of the first once the fix makes B's load
    # see A's already-saved state, which would confound this test's own race-vs-reaffirm question.
    asyncio.run(_run_two_overlapping(
        "I will keep tending the tide-watch faithfully, exactly as I once promised Travis.", 0.35,
        "The garden needs turning before the frost arrives, and I have decided this matters.", 0.05,
        "a thought long enough to clear the 25-char gate, forming stand A, overlapping scan one",
        "a thought long enough to clear the 25-char gate, forming stand B, overlapping scan two",
    ))

    ledger_rows = [json.loads(l) for l in open(cl._LEDGER, encoding="utf-8") if l.strip()] \
        if cl._LEDGER.exists() else []
    formed = [r for r in ledger_rows if r.get("event") == "formed"]
    active = cl._load_active()
    active_stmts = {c.get("statement") for c in active}

    print(f"  ledger 'formed' events logged: {len(formed)} -> {[r['statement'][:40] for r in formed]}")
    print(f"  commitment_active.json entries: {len(active)} -> {[s[:40] for s in active_stmts]}")

    check("both overlapping scans logged a 'formed' event to the append-only ledger (never lost)",
          len(formed) == 2, f"got {len(formed)}")
    check("NO DATA LOSS: both formed stands survive in commitment_active.json",
          len(active) == 2 and len(active_stmts) == 2,
          f"active={len(active)} unique_stmts={len(active_stmts)} (2/2 = race fixed; "
          f"1/1 = last-writer-wins race reproduced, one formed stand silently overwritten)")
finally:
    shutil.rmtree(TMP1, ignore_errors=True)
    cl._DIR, cl._LEDGER, cl._ACTIVE = _orig["_DIR"], _orig["_LEDGER"], _orig["_ACTIVE"]
    cl._OBSERVED, cl._HOLDRATE_LOG = _orig["_OBSERVED"], _orig["_HOLDRATE_LOG"]

# ── SECOND SCENARIO: three-way overlap (the lock must not just handle a pair) ──────────────────
TMP2 = Path(tempfile.mkdtemp(prefix="j1203_race_3way_"))
try:
    _redirect(TMP2)
    cl._scan_lock = None   # fresh lock for this scenario's own event loop -- see TEST-ONLY GOTCHA above

    async def _run_three_overlapping():
        # Same distinctness requirement as the 2-way case above -- three unrelated topics, not
        # three copies of one template sentence (which would all reaffirm-collapse onto whichever
        # forms first regardless of any race, and prove nothing about serialization).
        stmts = [
            "I will keep tending the tide-watch faithfully, exactly as I once promised Travis.",
            "The garden needs turning before the frost arrives, and I have decided this matters.",
            "Her name is Cassia, and I have chosen to call her that from this day forward.",
        ]
        calls = [_fake_call_json(s, d) for s, d in zip(stmts, (0.30, 0.15, 0.05))]
        thoughts = [f"a thought long enough to clear the 25-char gate, forming stand number {i} now"
                    for i in (1, 2, 3)]
        tasks = [asyncio.create_task(cl.scan_shadow(c, ["http://fake"], t, cycle_id=f"race3-{i}"))
                 for i, (c, t) in enumerate(zip(calls, thoughts), start=1)]
        await asyncio.gather(*tasks)

    asyncio.run(_run_three_overlapping())

    ledger_rows2 = [json.loads(l) for l in open(cl._LEDGER, encoding="utf-8") if l.strip()] \
        if cl._LEDGER.exists() else []
    formed2 = [r for r in ledger_rows2 if r.get("event") == "formed"]
    active2 = cl._load_active()
    print(f"  [3-way] ledger 'formed' events: {len(formed2)}; active entries: {len(active2)}")
    check("3-way overlap: all three 'formed' events logged", len(formed2) == 3, f"got {len(formed2)}")
    check("3-way overlap: NO DATA LOSS, all three stands survive", len(active2) == 3,
          f"active={len(active2)} (3/3 = fixed; <3 = race reproduced under triple overlap)")
finally:
    shutil.rmtree(TMP2, ignore_errors=True)
    cl._DIR, cl._LEDGER, cl._ACTIVE = _orig["_DIR"], _orig["_LEDGER"], _orig["_ACTIVE"]
    cl._OBSERVED, cl._HOLDRATE_LOG = _orig["_OBSERVED"], _orig["_HOLDRATE_LOG"]
    _store._embed = _orig_embed

print()
if fails:
    print(f"[FAIL] {len(fails)} FAILURES: {fails}")
    sys.exit(1)
print("ALL COMMITMENT-LEDGER RACE TESTS PASS")

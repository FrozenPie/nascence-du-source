"""Phase 1 in-vitro: the L1 prediction-error feed now WRITES a contradiction shadow event when the gate
says would_pressure. Monkeypatches store_shadow_event (no real DB write) + isolates state. Verifies the
full ignition path end-to-end."""
import sys, json, shutil, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import prediction_error as pe, tension_ledger as tl   # `import core` stays BEFORE anything lab_env-ish
import core.memory.store as store

# J-1803 / F-2426: the state files are redirected to a throwaway directory OUTSIDE data/ (so profile.guard_path passes) --
# the script no longer backs up / unlinks / restores Du's REAL prediction_error files, so it is safe from any tree.
_TMP = Path(tempfile.mkdtemp(prefix="phase1_ignition_invitro_"))
pe._STATE = _TMP / "prediction_error_state.json"
pe._SHADOW = _TMP / "logs" / "shadow_integrity.jsonl"
pe._RAW = _TMP / "prediction_error_log.jsonl"

# 1. prediction_error is now a recognised CONTRADICTION source (rides the proven pipe)
assert "prediction_error" in tl.CONTRADICTION_SOURCES, tl.CONTRADICTION_SOURCES
assert "prediction_error" not in tl.SALIENCE_SOURCES
print(f"[1] prediction_error ∈ CONTRADICTION_SOURCES = {tl.CONTRADICTION_SOURCES}  (feeds identity, not salience)")
assert pe.FEED_LEDGER is True
print("[2] FEED_LEDGER = True (Phase 1 live on restart; reversible kill-switch)")

# capture shadow writes instead of hitting the DB
captured = []
_orig = store.store_shadow_event
store.store_shadow_event = lambda **k: (captured.append(k), "fake-id")[1]

def restore():
    store.store_shadow_event = _orig
    shutil.rmtree(_TMP, ignore_errors=True)
try:
    # small gap → nothing
    pe.observe("mathematics", 0.80, 0.78)
    assert not captured, "small gap should not write a shadow event"
    # first large gap → eligible but recurrence 1, not would_pressure → no write
    pe.observe("mathematics", 0.81, 0.19)
    assert not captured, f"single large gap should not feed (recurrence<2): {captured}"
    # second large gap → recurrence 2 → would_pressure → WRITES a prediction_error contradiction event
    pe.observe("mathematics", 0.80, 0.20)
    assert len(captured) == 1, f"recurring large gap should write exactly one event: {len(captured)}"
    ev = captured[0]
    assert ev["source"] == "prediction_error", ev
    assert "mathematics" in ev["rejected_draft"] or "mathematics" in str(ev.get("corrections")), ev
    print(f"[3] ignition OK — recurring concrete gap → 1 prediction_error shadow event written")
    print(f"      draft='{ev['rejected_draft'][:60]}'  corrections={ev['corrections']}")
    st = pe.status()
    assert st["fed_total"] >= 1 and st["feeding"] is True
    print(f"[4] status: fed_total={st['fed_total']}, recurrence={st['recurrence_by_domain']}")
    print("\nPhase 1 IGNITION PASS — self-generated prediction error now feeds the contradiction pipe T4 reads,")
    print("through the gate (concrete+recurrence≥2+importance), riding the same clustering as critic_rejection.")
finally:
    restore()

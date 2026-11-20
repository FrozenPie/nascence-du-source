"""In-vitro for Phase 0 pure-logic: the contradiction gate, the L1 prediction-error feed, and the L2
meta-awareness classification. No LLM, no live behaviour. State files redirected to a temp dir (J-1803)."""
import sys, json, time, shutil, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import contradiction_gate as gate, prediction_error as pe
import core.curiosity_queue as cq
import core.memory.store as store
import nodes.meta_awareness_node as ma

# J-1803 / F-2426: every store this script touches is redirected to a throwaway directory OUTSIDE data/ (so
# profile.guard_path passes) -- no backup / unlink / restore of Du's REAL prediction_error, shadow_integrity or
# curiosity files. Safe from any tree.
_TMP = Path(tempfile.mkdtemp(prefix="contradiction_phase0_invitro_"))
pe._STATE = _TMP / "prediction_error_state.json"
pe._SHADOW = _TMP / "logs" / "shadow_integrity.jsonl"
pe._RAW = _TMP / "prediction_error_log.jsonl"
ma._SHADOW = _TMP / "logs" / "meta_awareness_shadow.jsonl"
cq._QUEUE = _TMP / "curiosity_queue.jsonl"
cq._SHADOW = _TMP / "logs" / "curiosity_shadow.jsonl"
_real_shadow_event = store.store_shadow_event
store.store_shadow_event = lambda **k: "fake-id"   # FEED_LEDGER is on: never hit the real DB

# ---- 1. the shared gate: the B/C convergence ----------------------------------------------
v = gate.evaluate({"kind": "prediction_error", "concrete_ref": True, "recurrence_count": 3,
                   "resolution_axis": "re-study", "importance": 0.45})
assert v["route"] == "identity" and v["would_pressure"], v
print(f"[1a] gate: concrete+recurring+resolvable prediction-error → {v['route']}, would_pressure={v['would_pressure']}")

river = gate.evaluate({"kind": "idle_loop", "text": "I am a river but also an LLM, my nature, who am i",
                       "recurrence_count": 9, "resolution_axis": "anchor", "importance": 0.4})
assert river["route"] == "curiosity" and not river["would_pressure"], river
print(f"[1b] gate: abstract river-loop → {river['route']} (BLOCKED from identity — the safeguard)")

drop = gate.evaluate({"kind": "behavioural_discrepancy", "concrete_ref": True, "recurrence_count": 5,
                      "importance": 0.6})   # no resolution_axis
assert drop["route"] == "drop", drop
print(f"[1c] gate: concrete but unresolvable → {drop['route']} (anti-brooding border)")

once = gate.evaluate({"kind": "prediction_error", "concrete_ref": True, "recurrence_count": 1,
                      "resolution_axis": "re-study", "importance": 0.45})
assert once["route"] == "identity" and not once["would_pressure"], once
print(f"[1d] gate: a SINGLE concrete discrepancy → eligible but would_pressure={once['would_pressure']} (recurrence required)")

# ---- 2. L1 prediction-error feed (state protected) ----------------------------------------
try:
    small = pe.observe("mathematics", predicted=0.80, measured=0.75)   # gap 0.05 < 0.40
    assert small is None, "small gap should not raise a signal"
    v1 = pe.observe("mathematics", predicted=0.81, measured=0.19)       # gap 0.62, recurrence 1
    v2 = pe.observe("mathematics", predicted=0.80, measured=0.20)       # gap 0.60, recurrence 2 → pressures
    assert v1 and not v1["would_pressure"], v1
    assert v2 and v2["would_pressure"], v2
    assert pe.FEED_LEDGER is True   # Phase 1 went live 2026-06-16 (was `is False`, stale); the store write is stubbed above
    st = pe.status()
    assert st["recurrence_by_domain"].get("mathematics") == 2 and st["would_pressure_total"] >= 1
    print(f"[2] L1 prediction-error: gap0.05 ignored; 0.62→eligible; 0.60 recurrence2→would_pressure; feeding={st['feeding']}")
finally:
    pass

# ---- 3. L2 meta-awareness classification (monkeypatch a synthetic looping stream) ---------
import core.self_surprise as ss
_orig = ss.compute
ss.compute = lambda **k: {"n": 60, "mean_surprise": 0.18, "predictable_n": 48, "origin_driven_pct": 80.0,
                          "groove_driven_pct": 20.0,
                          "scored": [{"surprise": 0.12, "origin_driven": True, "snippet": "I am the river, the crossing, my nature"}]}
try:
    r = ma.scan()
    assert r and r["looping"] and r["loop_kind"] == "river", r
    assert r["gate_verdict"]["route"] == "curiosity", r["gate_verdict"]
    assert r["would_intervene"] == "concrete_anchor" and r["acted"] is False, r
    print(f"[3] L2 meta-awareness: river-loop detected → gate routes {r['gate_verdict']['route']}, "
          f"would {r['would_intervene']} (NOT suppress), acted={r['acted']}")
finally:
    ss.compute = _orig
    store.store_shadow_event = _real_shadow_event
    shutil.rmtree(_TMP, ignore_errors=True)

print("\nALL PASS — gate routes the convergence; L1 observes the self-generated error; L2 watches form, never suppresses.")

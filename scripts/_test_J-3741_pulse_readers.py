"""J-3741: the four wired shadow readers are bounded, fail-open on a missing log, and report on stubbed logs."""
import json, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import emotion_construction as ec, symbol_tier2_wouldinject as t2, arousal as ar, self_implication as si

def w(p, rows): p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

with tempfile.TemporaryDirectory() as d:
    d = Path(d); miss = d / "missing"
    ec._AR_SHADOW_LOG = miss; t2._LOG_FILE = miss; ar._REGIME_STATE = miss; si._CONV_LOG = miss
    assert ec.affective_retrieval_status() == {"rows": 0}
    assert "note" in t2.wouldinject_report()
    assert ar.regime_shadow_status() == {"observed": False}
    assert si.conv_status()["scans"] == 0
    # stubbed
    w(d / "ar", [{"llm_vec_available": True, "jaccard_llm_vs_con": 0.9, "affect_match_mean_gap": 0.1}] * 3)
    ec._AR_SHADOW_LOG = d / "ar"
    r = ec.affective_retrieval_status(); assert r["rows"] == 3 and r["mean_jaccard_top5"] == 0.9
    w(d / "t2", [{"ts": 1.0, "symbol": "a", "verbatim_recurrence": {"hit": False}},
                 {"ts": 86401.0, "symbol": "a", "verbatim_recurrence": {"hit": True}}])
    t2._LOG_FILE = d / "t2"
    r = t2.wouldinject_report(); assert r["_totals"]["events"] == 2 and r["_totals"]["verbatim_recurrence_hits"] == 1 and r["a"]["count"] == 2
    (d / "st").write_text(json.dumps({"resolved_count": 2, "resolved_cycles_sum": 10, "resolved_seconds_sum": 20.0,
                                      "longest_streak_cycles": 7, "longest_streak_seconds": 9.0}), encoding="utf-8")
    ar._REGIME_STATE = d / "st"
    r = ar.regime_shadow_status(); assert r["observed"] and r["resolved_streaks"] == 2 and r["longest_streak_cycles"] == 7
    w(d / "cv", [{"contradicts": True, "directness": 0.5, "retreat_in_draft": True}, {"contradicts": False}])
    si._CONV_LOG = d / "cv"
    r = si.conv_status(); assert r == {"scans": 2, "would_fire": 1, "mean_directness": 0.5, "retreat_in_draft": 1, "retreat_rate": 1.0}, r
    # bounded: tail limit honoured
    si._CONV_STATUS_TAIL_ROWS = 1
    assert si.conv_status()["scans"] == 1
print("OK")

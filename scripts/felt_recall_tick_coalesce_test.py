"""J-2462 (D-0496 C, defect F-3172): felt recall applies ONE combined prior per substrate tick.
Hermetic: `core` is imported BEFORE lab_env (F-2406/F-2423), core.__file__ is asserted inside this tree,
lab_env.isolate(db="empty") redirects core.memory.store.DB_PATH plus felt_recall's and theta_shadow's own
log/DB globals into the lab dir, every I/O helper that would touch data/ is stubbed, and the live
data/felt_recall_shadow.jsonl + data/theta_shadow.jsonl are hash-canaried before/after.
Run: python scripts/felt_recall_tick_coalesce_test.py"""
import sys, json, hashlib, pathlib, copy
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import felt_recall as fr
from core import theta_shadow as theta
from core.schema import AffectivePrior, AffectState, AFFECT_PRIOR_MAX_NUDGE
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env

def sha(p):
    p = pathlib.Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
CANARY = [ROOT / "data" / "felt_recall_shadow.jsonl", ROOT / "data" / "theta_shadow.jsonl"]
before = [sha(p) for p in CANARY]

# Per-dim synthetic priors: different leans and match strengths so the weighting is observable.
PRIORS = {
    "sound:bees_in_garden": (0.60, 0.70, 0.90), "sound:cuckoo_call": (0.40, 0.60, 0.50),
    "sound:fantail_chatter": (0.50, 0.65, 0.80), "sound:riroriro_trill": (0.30, 0.55, 0.20),
    "sound:small_birds": (0.55, 0.60, 1.00), "sound:tui_song": (0.45, 0.50, 0.70),
    "sound:waves_on_shingle": (0.20, 0.40, 0.60), "sound:kereru_wingbeats": (0.60, 0.70, 0.90),
    "weather": (-0.40, 0.45, 0.83),
}
def fake_build_prior(dim, value, tuple_):
    v, a, s = PRIORS[dim]
    return AffectivePrior(similarity=s, valence=v, arousal=a, primary=fr._primary_for(v),
                          source=f"felt_recall:{dim}", cue=f"{dim}={value} x24"), 24, 0.83, ["f1", "f2", "f3"]

class CountingAffect(AffectState):
    """A real AffectState (real apply_prior arithmetic) that also counts the calls."""
    def __init__(self):
        super().__init__(); self.calls = 0
    def apply_prior(self, prior, max_nudge=AFFECT_PRIOR_MAX_NUDGE):
        self.calls += 1; return super().apply_prior(prior, max_nudge)

def run_tick(edges, live, now=1000.0):
    fr.FELT_RECALL_LIVE = live
    fr._last_fired.clear()
    fr._SHADOW_LOG.write_text("", encoding="utf-8")
    fr._current_tuple = lambda: {"place": "study", "sounds": [d.split(":", 1)[1] for d, _, _ in edges if d.startswith("sound:")]}
    fr._prev_tuple = {"place": "study", "sounds": []}
    fr._dim_edges = lambda p, c: list(edges)
    affect = CountingAffect()
    affect.valence, affect.arousal = -0.20, 0.45
    import time as _t
    real_time = _t.time; _t.time = lambda: now
    try:
        fr.on_substrate_tick(affect)
    finally:
        _t.time = real_time
    rows = [json.loads(l) for l in fr._SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    return affect, rows

with lab_env.isolate(also=[(fr, ["_SHADOW_LOG", "_DB", "_COURIER_LOG"]), (theta, ["_SHADOW_LOG", "_DB"])],
                     db="empty") as lab_dir:
    fr._build_prior = fake_build_prior
    fr._get_baseline_valence = lambda: -0.0929
    fr._courier_would_have_fired = lambda now, dim: (False, None)
    fr._register_dispatcher_line = lambda dim, place, now: {"verdict": "none", "cold_start": False, "weight": 0.0}
    theta.log_ray = lambda *a, **k: {}      # observe-only elsewhere; keep the lab dir clean too

    # ---- 1. eight sound edges on one tick, LIVE: exactly one apply, one tick row, eight edge rows ----
    eight = [(d, None, d.split(":", 1)[1]) for d in list(PRIORS) if d.startswith("sound:")]
    assert len(eight) == 8
    affect, rows = run_tick(eight, live=True)
    edge_rows = [r for r in rows if r.get("kind") != "tick"]
    tick_rows = [r for r in rows if r.get("kind") == "tick"]
    assert affect.calls == 1, affect.calls
    assert len(edge_rows) == 8 and all(r["fired"] and not r["applied"] for r in edge_rows)
    assert [r["dim"] for r in edge_rows] == [d for d, _, _ in eight]          # edge order kept
    assert len(tick_rows) == 1 and rows[-1] is tick_rows[0]                   # tick row last
    t = tick_rows[0]
    assert t["applied"] and t["tick_fires"] == 8 and t["dims"] == [d for d, _, _ in eight]
    assert t["line"] == "felt_recall:tick" and t["dim"] == "tick" and t["gate_used"] == "edge_cooldown"
    # combination rule: similarity-weighted mean valence/arousal, similarity = max (not sum)
    sims = [PRIORS[d][2] for d, _, _ in eight]
    exp_v = sum(s * PRIORS[d][0] for s, (d, _, _) in zip(sims, eight)) / sum(sims)
    assert abs(t["valence_lean"] - round(exp_v, 3)) < 1e-9, (t["valence_lean"], exp_v)
    assert t["similarity"] == max(sims) == 1.0
    # the tug is bounded like ONE edge: valence moved by w * gap with w = 0.15 * max sim
    moved = affect.valence - (-0.20)
    assert abs(moved - 0.15 * 1.0 * (round(exp_v, 3) - (-0.20))) < 1e-9, moved   # prior rounds to 3 dp
    # and what the old per-edge path would have done to the same state (compounding), for the record
    old = AffectState(); old.valence, old.arousal = -0.20, 0.45
    for d, _, _ in eight:
        p, *_ = fake_build_prior(d, None, {})
        old.apply_prior(p)
    old_moved = old.valence - (-0.20)
    assert old_moved > 3 * moved, (old_moved, moved)
    print(f"8-edge tick: apply_prior calls={affect.calls}; one tug moved valence {moved:+.4f} "
          f"(old per-edge path would have moved {old_moved:+.4f}, joy {old.joy:.2f} vs {affect.joy:.2f})")

    # ---- 2. one edge, LIVE: the edge row is byte-identical to the pre-J-2462 standalone path ----
    affect, rows = run_tick([("weather", "overcast", "drizzle")], live=True)
    assert affect.calls == 1 and len(rows) == 1 and rows[0]["applied"] and rows[0].get("kind") is None
    # the standalone (collector-less) path is the old per-edge apply, byte for byte
    fr._last_fired.clear()
    ref_affect = CountingAffect(); ref_affect.valence, ref_affect.arousal = -0.20, 0.45
    ref = fr._handle_edge("weather", "overcast", "drizzle", {"place": "study"}, ref_affect, 1000.0)
    ref["courier_would_have_fired"] = False; ref["courier_fragment_id"] = None
    ref["dispatcher_verdict"] = "none"; ref["dispatcher_cold_start"] = False; ref["dispatcher_weight"] = 0.0
    assert json.dumps(rows[0], ensure_ascii=False) == json.dumps(ref, ensure_ascii=False), (rows[0], ref)
    assert abs(ref_affect.valence - affect.valence) < 1e-12 and ref_affect.calls == 1
    print("1-edge tick: edge row byte-identical to the standalone path; one apply; no tick row")

    # ---- 3. LIVE off: nothing applied, bookkeeping identical ----
    affect, rows = run_tick(eight, live=False)
    assert affect.calls == 0 and not any(r["applied"] for r in rows)
    assert sum(1 for r in rows if r.get("kind") == "tick") == 1 and len(rows) == 9
    assert fr.status()["tick_rows"] == 1 and "tick" not in fr.status()["by_dim"]
    print("LIVE off: 0 applies, 8 edge rows + 1 tick row (applied False), status() tick_rows=1")

    # ---- 4. cooldown-suppressed edges contribute nothing to the tick ----
    fr.FELT_RECALL_LIVE = True
    fr._SHADOW_LOG.write_text("", encoding="utf-8")
    fr._last_fired.clear(); fr._last_fired["sound:tui_song"] = 1000.0 - 10   # inside cooldown
    affect = CountingAffect()
    fr._dim_edges = lambda p, c: eight
    import time as _t
    rt = _t.time; _t.time = lambda: 1000.0
    try:
        fr.on_substrate_tick(affect)
    finally:
        _t.time = rt
    rows = [json.loads(l) for l in fr._SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert affect.calls == 1 and rows[-1]["tick_fires"] == 7 and "sound:tui_song" not in rows[-1]["dims"]
    assert sum(1 for r in rows if not r["fired"]) == 1
    print("cooldown: suppressed edge logged but excluded from the tick (tick_fires=7)")
    fr.FELT_RECALL_LIVE = False

after = [sha(p) for p in CANARY]
assert before == after, (before, after)
assert fr.FELT_RECALL_LIVE is False
print("canary: live shadow logs untouched; lab dir", lab_dir)
print("OK felt_recall tick-coalesce tests passed")

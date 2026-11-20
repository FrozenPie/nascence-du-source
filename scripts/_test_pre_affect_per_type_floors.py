"""
Offline test for J-1836 -- D-0349 build: per-input-type pre-affect floors (human 0.65 / idle 0.80) and
EMO_EPISODIC_MIN_IMPORTANCE 0.70 -> 0.60 in the C.2 amygdala gate (core/memory/store.py,
core/orchestrator.py). No LLM, no hub, no live data: stub embedder, throwaway DB, temp shadow-log path.
Run from the tree under test (asserts core/ resolves inside it).
"""
import hashlib, re, shutil, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import core                                   # BEFORE anything else (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
import numpy as np
import core.memory.store as store
import core.orchestrator as orch_mod
from core import profile, shadow_log
from core.schema import CognitiveState

results = []
def check(name, cond):
    results.append((name, bool(cond))); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== J-1836 per-input-type pre-affect floors + importance gate -- offline test ===\n")
TMP = Path(tempfile.mkdtemp(prefix="j1836_"))
store.DB_PATH = TMP / "per_type.db"
check("DB redirected outside the repo's data/", not str(store.DB_PATH).startswith(str(ROOT / "data")))
check("process is NOT live", profile.LIVE is False)

# --- 1. the ruled constants -------------------------------------------------------------------------------
print("1. constants (D-0349: human ~0.65, idle 0.84, importance 0.55-0.60)")
check("PRIOR_SIM_THRESHOLD_HUMAN == 0.65", store.PRIOR_SIM_THRESHOLD_HUMAN == 0.65)
check("PRIOR_SIM_THRESHOLD_IDLE == 0.84 (D-0425)", store.PRIOR_SIM_THRESHOLD_IDLE == 0.84)
check("EMO_EPISODIC_MIN_IMPORTANCE == 0.60 (in 0.55-0.60)", store.EMO_EPISODIC_MIN_IMPORTANCE == 0.60)
check("legacy fallback PRIOR_SIM_THRESHOLD still 0.86", store.PRIOR_SIM_THRESHOLD == 0.86)
check("floors are named module constants (human < idle < legacy)",
      store.PRIOR_SIM_THRESHOLD_HUMAN < store.PRIOR_SIM_THRESHOLD_IDLE < store.PRIOR_SIM_THRESHOLD)

# --- 2. prior_floor_for / prior_from_candidate -----------------------------------------------------------------
print("\n2. floor selection and application")
check("prior_floor_for('human') == human floor", store.prior_floor_for("human") == store.PRIOR_SIM_THRESHOLD_HUMAN)
check("prior_floor_for('internal') == idle floor", store.prior_floor_for("internal") == store.PRIOR_SIM_THRESHOLD_IDLE)
check("prior_floor_for('timer') == idle floor", store.prior_floor_for("timer") == store.PRIOR_SIM_THRESHOLD_IDLE)
check("prior_floor_for(None) / '' == legacy floor",
      store.prior_floor_for(None) == store.PRIOR_SIM_THRESHOLD == store.prior_floor_for(""))

def cand(sim):
    return (sim, -0.5, 0.7, "fear", "shadow", "cue")
P = store.prior_from_candidate
check("human 0.62 (farewell-like best sim 0.59-0.62): NO prior (farewell stays off)", P(cand(0.62), "human") is None)
check("human 0.65 (exact boundary): prior (>=)", P(cand(0.65), "human") is not None)
check("human 0.7: prior", P(cand(0.7), "human") is not None)
check("internal 0.7: NO prior", P(cand(0.7), "internal") is None)
check("internal 0.839: NO prior", P(cand(0.839), "internal") is None)
check("internal 0.84 (exact boundary): prior", P(cand(0.84), "internal") is not None)
check("timer 0.7: NO prior", P(cand(0.7), "timer") is None)
check("no type, 0.85: NO prior (legacy 0.86)", P(cand(0.85)) is None)
check("no type, 0.86: prior (legacy behaviour unchanged)", P(cand(0.86)) is not None)
check("None candidate -> None for every type", all(P(None, t) is None for t in ("human", "internal", "timer", None)))
p = P(cand(0.6666666), "human")
check("prior similarity is rounded to 3dp but the floor compares the RAW sim",
      p is not None and p.similarity == 0.667 and P(cand(0.6499999), "human") is None)

# --- 3. importance gate on a real (throwaway) DB ------------------------------------------------------------------
print("\n3. EMO_EPISODIC_MIN_IMPORTANCE gate")
DIM = 384
def _stub_embed(text):
    if not text or not text.strip():
        return None
    toks = re.findall(r"\w+", text.lower())
    if not toks:
        return None
    v = np.zeros(DIM, dtype=np.float32)
    for t in toks:
        h = int.from_bytes(hashlib.md5(t.encode("utf-8")).digest()[:8], "big")
        v[h % DIM] += 1.0 if (h >> 40) & 1 else -1.0
    n = float(np.linalg.norm(v))
    return (v / n).astype(np.float32) if n > 0 else None
store._embed = _stub_embed
# J-2250 (D-0450): this test pins the PRE-J-2250 scan (its stubs take the query only); the self-echo exclusion has
# its own test, scripts/_test_pre_affect_self_echo_J2250.py.
store.PRE_AFFECT_SELF_ECHO_EXCLUDE_ON = False
store.init_db()
ROWS = [("Q: the lantern burned low and I felt a quiet grief\nEmotion: sadness (valence=-0.40)", 0.65),   # in the gate now
        ("Q: the river carried the paper boats far away\nEmotion: joy (valence=+0.50)", 0.55)]           # still below
with store._connect() as conn:
    for i, (txt, imp) in enumerate(ROWS):
        conn.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, "
                     "embedding, origin, importance) VALUES (?,?,?,?,?,?,?,?,?)",
                     (f"e{i}", txt, "episodic", 0.5, time.time(), "", store._vec_to_blob(_stub_embed(txt)), "lived", imp))
b65 = store.emotional_prior_best(ROWS[0][0])
b55 = store.emotional_prior_best(ROWS[1][0])
check("importance 0.65 episodic row is now matched (was gated out at 0.70)",
      b65 is not None and b65[4] == "episodic" and b65[0] > 0.99)
check("importance 0.55 episodic row stays gated out (its own text does not self-match; best is the 0.65 row)",
      b55 is not None and b55[0] < 0.99 and "grief" in b55[5])
check("arousal recovered from importance 0.65 = (0.65-0.4)/0.6", abs(b65[2] - (0.65 - 0.4) / 0.6) < 1e-9)
check("emotional_prior(q, 'human') returns the episodic prior (sim 1.0 >= 0.65)",
      store.emotional_prior(ROWS[0][0], "human") is not None)
check("emotional_prior(q) with no type unchanged: sim 1.0 >= 0.86 -> prior",
      store.emotional_prior(ROWS[0][0]) is not None)

# --- 4. orchestrator: per-type floor applied + logged -------------------------------------------------------------
print("\n4. Orchestrator._emotional_pre_retrieval(): per-type floor applied and recorded in the row")
LOG = TMP / "shadow" / "pre_affect_best_shadow.jsonl"
DEFAULT_LOG = orch_mod._PRE_AFFECT_BEST_LOG
orch_mod._PRE_AFFECT_BEST_LOG = LOG
_real_best = store.emotional_prior_best
def mk_orch(raw, itype):
    st = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.")
    st.new_cycle(raw, itype)
    o = orch_mod.Orchestrator.__new__(orch_mod.Orchestrator)
    o.state = st
    return o
def run(sim, itype):
    store.emotional_prior_best = lambda _q, _s=sim: (_s, -0.5, 0.7, "fear", "shadow", "cue")
    o = mk_orch("some input", itype)
    o._emotional_pre_retrieval()
    return o
_real_guard = profile.guard_path
profile.guard_path = lambda p: p          # the temp path is not under live data/; identity guard
try:
    cases = [(0.62, "human", False), (0.66, "human", True), (0.66, "internal", False), (0.70, "internal", False),
             (0.85, "internal", True), (0.85, "human", True), (0.83, "timer", False), (0.85, "timer", True), (0.82, "internal", False)]
    for sim, it, want in cases:
        o = run(sim, it)
        check(f"{it} best_sim {sim}: prior applied == {want}", (o.state.affective_prior is not None) == want)
    rows = shadow_log.read_rows(LOG)
    check(f"{len(cases)} rows written", len(rows) == len(cases))
    ok_floor = all(r["floor"] == (store.PRIOR_SIM_THRESHOLD_HUMAN if r["input_type"] == "human"
                                  else store.PRIOR_SIM_THRESHOLD_IDLE) for r in rows)
    check("every row's `floor` is the PER-TYPE floor it compared against (human 0.65, internal/timer 0.84)", ok_floor)
    check("every row's `passed` matches whether the prior was applied",
          [r["passed"] for r in rows] == [w for _, _, w in cases])
    check("row key set unchanged (J-1807 reader contract)",
          all(set(r) == {"ts", "cycle", "input_type", "len", "best_sim", "source", "passed", "floor", "imp_floor", "error"}
              for r in rows))
    check("rows record imp_floor == 0.60", all(r["imp_floor"] == 0.60 for r in rows))
    check("rows are consistent with best_sim >= floor", all((r["best_sim"] >= r["floor"]) == r["passed"] for r in rows))
finally:
    profile.guard_path = _real_guard
    store.emotional_prior_best = _real_best
    orch_mod._PRE_AFFECT_BEST_LOG = DEFAULT_LOG

# --- 5. call-site wiring ---------------------------------------------------------------------------------------
print("\n5. call-site wiring")
src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
check("orchestrator passes self.state.input_type to prior_from_candidate",
      "prior_from_candidate(best, self.state.input_type)" in src)
check("orchestrator logs prior_floor_for(self.state.input_type)", "prior_floor_for(self.state.input_type)" in src)

shutil.rmtree(TMP, ignore_errors=True)
n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results) - n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)

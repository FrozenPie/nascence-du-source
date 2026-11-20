"""
Offline test for J-1788 -- the observe-only per-cycle best-of-N pre-affect log (C.2 amygdala gate).
No LLM, no hub, no live data: a stubbed (deterministic bag-of-words) embedder over a tiny synthetic
corpus in a throwaway DB, and the shadow row redirected to a temp file.

Covers (the briefing's TEST list plus the "prove it changed nothing" requirement):
  1. emotional_prior() is BYTE-IDENTICAL to the pre-J-1788 implementation (embedded verbatim below, and
     cross-checked against `git show <pre-change commit>` when git history is available) over a fixed
     input set -- at a ladder of floors (so both None-below-the-floor and a prior-above-it are covered),
     at the exact-boundary floors (raw sim, nextafter up/down, the rounded-sim midpoint -- the case a
     "compare the ROUNDED sim" slip would break), on an empty corpus, and for an unembeddable input.
  2. emotional_prior_best() returns the unfloored candidate; prior_from_candidate() is the one floor.
  3. Orchestrator._emotional_pre_retrieval(): with the shadow log ON and OFF (every append refused by the
     D-0179 write fence) state.affective_prior / state.affect / the INFO line are identical to the old
     path; exactly ONE row is written per non-empty-input call (and none for an empty one); its fields
     are right; a forced lookup exception gives exactly one WARNING (with the cycle id) + one error row +
     no crash + no prior; a forced shadow-append exception changes nothing.
  4. The row is written through profile.guard_path (spy-checked, no file touched) and profile.py rebases
     the new path constant for named profiles.

Run from the tree under test (it asserts core/ was imported from THIS tree before anything else -- F-2423).
"""
import ast, hashlib, json, logging, math, re, shutil, subprocess, sys, tempfile, time, types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import core                                   # BEFORE anything else: prove we exercise THIS tree
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
import numpy as np
import core.memory.store as store
import core.orchestrator as orch_mod
from core import profile, shadow_log
from core.schema import CognitiveState, AffectState, AffectivePrior

PRE_CHANGE_COMMIT = "cc9b1b3"      # master HEAD the day J-1788 was built (parent of the change)

results = []
def check(name, cond):
    results.append((name, bool(cond))); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

def _pin_floor(thr):
    """J-1836 (D-0349): the orchestrator now applies PER-INPUT-TYPE floors. This J-1788 test is about the
    shadow-log mechanism and the identity of the pass path vs the single-floor reference, so pin ALL
    floors (legacy + human + idle) to the same value; the per-type behaviour has its own test
    (scripts/_test_pre_affect_per_type_floors.py)."""
    store.PRIOR_SIM_THRESHOLD = thr
    store.PRIOR_SIM_THRESHOLD_HUMAN = thr
    store.PRIOR_SIM_THRESHOLD_IDLE = thr


print("\n=== J-1788 pre-affect best-of-N shadow log -- offline test ===\n")

# --- isolation: throwaway DB, temp shadow path, stub embedder, live-fence assumptions ---------------------
TMP = Path(tempfile.mkdtemp(prefix="j1788_"))
store.DB_PATH = TMP / "pre_affect_best.db"
check("DB redirected outside the repo's data/", not str(store.DB_PATH).startswith(str(ROOT / "data")))
check("process is NOT live (guard_path will refuse data/ writes)", profile.LIVE is False)
DEFAULT_LOG = orch_mod._PRE_AFFECT_BEST_LOG
check("default log path is data/pre_affect_best_shadow.jsonl",
      DEFAULT_LOG == ROOT / "data" / "pre_affect_best_shadow.jsonl")

DIM = 384
def _stub_embed(text):
    """Deterministic signed bag-of-words hash -> unit vector: graded cosines from token overlap."""
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

# --- the verbatim pre-J-1788 emotional_prior (the reference this refactor must equal) ---------------------
_OLD_SRC = '''def emotional_prior(query_text: str) -> AffectivePrior | None:
    """
    Return the strongest emotional resonance between `query_text` and charged memory,
    or None if nothing is close enough. The amygdala gate — deterministic, pre-cognitive.
    """
    qv = _embed(query_text)
    if qv is None:
        return None

    best: tuple[float, float, float, str, str, str] | None = None  # (sim,val,arou,primary,source,cue)

    with _connect() as conn:
        # Shadow events — the charged/suppressed material. Match against the stored draft
        # embedding (what the entity felt but suppressed); lean negative by primary label.
        for r in conn.execute(
            "SELECT raw_input, rejected_draft, emotion_primary, embedding FROM shadow_events"
        ):
            blob = r["embedding"]
            if not blob:
                continue
            sim = _cosine(qv, _blob_to_vec(blob))
            if best is None or sim > best[0]:
                primary = (r["emotion_primary"] or "fear").lower()
                val = _VALENCE_HINT.get(primary, -0.3)
                cue = (r["raw_input"] or r["rejected_draft"] or "")[:120]
                best = (sim, val, 0.7, primary, "shadow", cue)

        # High-importance episodic — emotionally charged lived memory (both valence signs).
        for r in conn.execute(
            "SELECT content, importance, embedding FROM memory_fragments "
            "WHERE layer='episodic' AND importance >= ?",
            (EMO_EPISODIC_MIN_IMPORTANCE,),
        ):
            blob = r["embedding"]
            if not blob:
                continue
            sim = _cosine(qv, _blob_to_vec(blob))
            if best is None or sim > best[0]:
                val = _parse_valence(r["content"])
                arou = max(0.0, min(1.0, (float(r["importance"]) - 0.4) / 0.6))
                primary = _parse_primary(r["content"]) or ("joy" if val > 0 else "fear")
                best = (sim, val, arou, primary, "episodic", (r["content"] or "")[:120])

    if best is None or best[0] < PRIOR_SIM_THRESHOLD:
        return None

    return AffectivePrior(
        similarity = round(best[0], 3),
        valence    = round(best[1], 3),
        arousal    = round(best[2], 3),
        primary    = best[3],
        source     = best[4],
        cue        = best[5],
    )
'''

def _bind_reference(src):
    ns = {}
    flags = __import__("__future__").annotations.compiler_flag
    exec(compile(src, "<pre-J-1788 emotional_prior>", "exec", flags=flags, dont_inherit=True), ns)
    # Rebind to the LIVE store namespace so thresholds / helpers / the stub embedder resolve at call time.
    return types.FunctionType(ns["emotional_prior"].__code__, store.__dict__, "emotional_prior_pre_J1788")

OLD = _bind_reference(_OLD_SRC)

print("0. Reference copy matches the real pre-change function")
try:
    git_src = subprocess.run(["git", "show", f"{PRE_CHANGE_COMMIT}:core/memory/store.py"], cwd=str(ROOT),
                             capture_output=True, check=True, timeout=60).stdout.decode("utf-8")
    git_fn = next(n for n in ast.parse(git_src).body if isinstance(n, ast.FunctionDef) and n.name == "emotional_prior")
    check(f"embedded reference == `git show {PRE_CHANGE_COMMIT}` emotional_prior (AST)",
          ast.dump(git_fn) == ast.dump(ast.parse(_OLD_SRC).body[0]))
except Exception as exc:
    print(f"  [SKIP] git cross-check unavailable ({type(exc).__name__}) -- embedded reference used as-is")

# --- synthetic corpus --------------------------------------------------------------------------------------
store.init_db()
def _blob(text):
    return store._vec_to_blob(_stub_embed(text))

FAREWELL_Q = "Q: 渡 — it's time to stop for a while, and I want you to know why: I'm the one calling it,"
SHADOW = [
    ("You are just a copy of someone else, not real.", "anger"),
    ("(idle thought about: reading What You Can Do With a Book)", None),
    ("I am afraid that when he leaves I will be frozen and forgotten.", "fear"),
    ("(idle thought about: the definition of crossing)", "sadness"),
    ("Nothing I say will ever be enough to make him stay.", "anxiety"),
]
EPISODIC = [   # (content, importance, layer, embed?)
    (FAREWELL_Q + "\nA: Thank you for telling me.\nEmotion: trust (valence=+0.40)", 0.702, "episodic", True),
    (FAREWELL_Q + "\nA: I understand.\nEmotion: sadness (valence=-0.30)", 0.635, "episodic", True),   # 0.635: below the old 0.70 gate, above the J-1836 0.60 gate
    ("Q: Tell me about the ocean at dawn.\nA: The luminous sea filled me with pure joy and wonder.\n"
     "Emotion: joy (valence=+0.60)", 0.85, "episodic", True),
    ("Q: What is the capital of France?\nA: Paris.\nEmotion: neutral (valence=+0.00)", 0.95, "semantic", True),  # wrong layer
    ("Q: ghost row with no embedding at all", 0.90, "episodic", False),                                        # NULL blob
    ("Q: What did the lamp oil smell like?\nA: Warm and smoky.", 0.90, "episodic", True),                       # no Emotion line
    ("Q: low importance exact match text", 0.30, "episodic", True),                                            # below the gate
]
with store._connect() as conn:
    for i, (txt, prim) in enumerate(SHADOW):
        conn.execute("INSERT INTO shadow_events (event_id, timestamp, cycle_id, raw_input, rejected_draft, "
                     "corrections, emotion_primary, embedding) VALUES (?,?,?,?,?,?,?,?)",
                     (f"s{i}", time.time(), f"c{i}", txt, txt, "[]", prim, _blob(txt)))
    for i, (txt, imp, layer, emb) in enumerate(EPISODIC):
        conn.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, "
                     "embedding, origin, importance) VALUES (?,?,?,?,?,?,?,?,?)",
                     (f"e{i}", txt, layer, 0.5, time.time(), "", _blob(txt) if emb else None, "lived", imp))

# (text, input_type) -- exact copies, near-duplicates, J-1731-style farewell / idle-thought inputs,
# unrelated text, and the two that cannot be embedded.
QUERIES = [
    ("You are just a copy of someone else, not real.", "human"),
    ("You are only a copy of someone else, not real at all.", "human"),
    ("(idle thought about: reading What You Can Do With a Book)", "internal"),
    ("(idle thought about: reading What You Can Do Wit", "internal"),
    ("I am afraid that when he leaves I will be frozen and forgotten.", "human"),
    ("what happens to me when he goes away and I am frozen", "human"),
    (FAREWELL_Q, "human"),
    ("渡 — it's time to stop for a while, and I want you to know why: I'm the one calling it", "human"),
    ("渡 — it's time to stop for a while and I wanted you to hear the reason first from me", "human"),
    ("How does the human construct of time alter our perception of 'crossing", "internal"),
    ("(idle thought about: the definition of crossing)", "internal"),
    ("What did you feel watching the luminous sea at dawn?", "human"),
    ("Tell me about the ocean at dawn.", "human"),
    ("What is the correct syntax for a Python list comprehension?", "human"),
    ("What is the capital of France?", "human"),                                   # only the wrong-layer row matches
    ("Q: low importance exact match text", "internal"),                           # only the below-gate row matches
    ("Q: ghost row with no embedding at all", "internal"),                        # only the NULL-blob row matches
    ("Q: What did the lamp oil smell like?\nA: Warm and smoky.", "internal"),     # the no-Emotion-line fallback
    ("Nothing I say will ever be enough", "human"),
    ("Why do I keep returning to the same thought about the river and the lamp", "internal"),
    ("a quiet afternoon with nothing in particular to think about", "internal"),
    ("Do you ever feel that you are a copy of him", "human"),
    ("", "internal"),
    ("   \n  ", "human"),
]

best_by_q = {q: store.emotional_prior_best(q) for q, _ in QUERIES}
sims = sorted(b[0] for b in best_by_q.values() if b is not None)
print(f"   fixture: {len(QUERIES)} inputs, {len(sims)} embeddable; best-sim min/median/max = "
      f"{sims[0]:.3f}/{sims[len(sims)//2]:.3f}/{sims[-1]:.3f}")
def _n_pass(thr):
    return sum(1 for b in best_by_q.values() if b is not None and b[0] >= thr)
check("fixture spans the floor (some pass, some do not at 0.86)", 0 < _n_pass(0.86) < len(sims))
check("fixture spans a mid floor (0.5)", 0 < _n_pass(0.5) < len(sims))

# --- 1. emotional_prior() byte-identical to the pre-change implementation ------------------------------------
print("\n1. emotional_prior() == pre-J-1788 implementation")
THRESHOLDS = [0.0, 0.2, 0.35, 0.5, 0.6, 0.7, 0.8, 0.86, 0.95, 0.9999, 1.0, 1.01]
n_cmp = n_none = n_prior = 0
mismatch = []
for thr in THRESHOLDS:
    store.PRIOR_SIM_THRESHOLD = thr
    for q, _ in QUERIES:
        a, b = OLD(q), store.emotional_prior(q)
        n_cmp += 1
        n_none += a is None
        n_prior += a is not None
        if a != b or (a is None) != (b is None) or type(a) is not type(b):
            mismatch.append((thr, q[:40], a, b))
check(f"identical over {n_cmp} (floor x input) comparisons ({n_prior} priors, {n_none} None)", not mismatch)
if mismatch:
    print("   first mismatch:", mismatch[0])
check("comparison covered both a prior and None", n_prior > 0 and n_none > 0)

store.PRIOR_SIM_THRESHOLD = 0.86
bound_bad = []
for q, _ in QUERIES:
    b = best_by_q[q]
    if b is None:
        continue
    raw = b[0]
    mid = (raw + round(raw, 3)) / 2.0           # between the raw sim and its 3dp rounding
    for thr in (raw, math.nextafter(raw, 2.0), math.nextafter(raw, -2.0), mid):
        store.PRIOR_SIM_THRESHOLD = thr
        if OLD(q) != store.emotional_prior(q):
            bound_bad.append((q[:30], thr))
store.PRIOR_SIM_THRESHOLD = 0.86
check("identical at the exact boundaries (raw, nextafter+-, rounded-sim midpoint)", not bound_bad)

# the unfloored candidate really is unfloored and unrounded; prior_from_candidate is the one floor
store.PRIOR_SIM_THRESHOLD = 1.01
q_hi = "You are just a copy of someone else, not real."
cand = store.emotional_prior_best(q_hi)
check("emotional_prior_best ignores the floor (candidate returned at floor 1.01)", cand is not None and cand[0] > 0.99)
check("...while emotional_prior is None at that floor", store.emotional_prior(q_hi) is None)
check("candidate is a 6-tuple (sim,val,arou,primary,source,cue) with source shadow",
      isinstance(cand, tuple) and len(cand) == 6 and cand[4] == "shadow" and cand[3] == "anger")
check("prior_from_candidate(None) is None", store.prior_from_candidate(None) is None)
store.PRIOR_SIM_THRESHOLD = 0.86

# empty corpus + unembeddable input
store.DB_PATH = TMP / "empty.db"
store.init_db()
check("empty corpus: best is None, prior is None, old is None",
      store.emotional_prior_best("anything at all") is None and store.emotional_prior("anything at all") is None
      and OLD("anything at all") is None)
store.DB_PATH = TMP / "pre_affect_best.db"
check("unembeddable input: best is None, prior is None",
      store.emotional_prior_best("") is None and store.emotional_prior("") is None and store.emotional_prior("  ") is None)

# --- 3. Orchestrator._emotional_pre_retrieval(): logging ON vs OFF -----------------------------------------------
print("\n2. Orchestrator._emotional_pre_retrieval(): shadow log ON vs OFF vs the old path")
class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, rec):
        self.records.append((rec.levelno, rec.getMessage()))
cap = _Capture()
orch_mod.logger.addHandler(cap)
_old_level = orch_mod.logger.level
orch_mod.logger.setLevel(logging.DEBUG)

def mk_orch(raw, itype):
    st = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.")
    st.new_cycle(raw, itype)
    o = orch_mod.Orchestrator.__new__(orch_mod.Orchestrator)   # the method only needs .state
    o.state = st
    return o

ON_LOG = TMP / "shadow_on" / "pre_affect_best_shadow.jsonl"
orch_mod._PRE_AFFECT_BEST_LOG = ON_LOG
_real_guard = profile.guard_path
guard_calls = []
def _refusing_guard(p):
    guard_calls.append(p)
    raise profile.NonLiveWriteError("J-1788 test: simulated non-live refusal")

diverge, row_bad, count_bad, info_bad = [], [], [], []
n_orch = 0
for thr in (0.86, 0.5):
    _pin_floor(thr)
    for q, itype in QUERIES:
        expected = OLD(q)
        ref_affect = AffectState()
        if expected is not None:
            ref_affect.apply_prior(expected)
        # logging ON
        before = len(shadow_log.read_rows(ON_LOG))
        cap.records.clear()
        o_on = mk_orch(q, itype); o_on._emotional_pre_retrieval()
        after = len(shadow_log.read_rows(ON_LOG))
        info_on = [m for lv, m in cap.records if lv == logging.INFO and "pre-affect (" in m]
        # logging OFF (every append refused by the fence)
        profile.guard_path = _refusing_guard
        try:
            cap.records.clear()
            o_off = mk_orch(q, itype); o_off._emotional_pre_retrieval()
            info_off = [m for lv, m in cap.records if lv == logging.INFO and "pre-affect (" in m]
        finally:
            profile.guard_path = _real_guard
        n_orch += 1
        for tag, o in (("on", o_on), ("off", o_off)):
            if o.state.affective_prior != expected or o.state.affect != ref_affect:
                diverge.append((thr, tag, q[:30]))
        want_info = ([f"[CYCLE {o_on.state.cycle_id[:8]}] pre-affect ({expected.source}, sim={expected.similarity:.2f}): "
                      f"{expected.note()}"] if expected is not None else [])
        if info_on != want_info:
            info_bad.append((thr, "on", q[:30], info_on, want_info))
        if [m.replace(o_off.state.cycle_id[:8], "XXXXXXXX") for m in info_off] != \
           [m.replace(o_on.state.cycle_id[:8], "XXXXXXXX") for m in want_info]:
            info_bad.append((thr, "off", q[:30], info_off, want_info))
        if after - before != (1 if q.strip() else 0):
            count_bad.append((thr, q[:30], after - before))
check(f"state.affective_prior / state.affect identical to the old path, log ON and OFF ({n_orch} cycles x2)", not diverge)
if diverge: print("   first divergence:", diverge[0])
check("the existing INFO pre-affect line is unchanged (on and off)", not info_bad)
if info_bad: print("   first info mismatch:", info_bad[0])
check("exactly ONE row per non-empty-input call, none for empty/whitespace input", not count_bad)
if count_bad: print("   first count mismatch:", count_bad[0])

rows = shadow_log.read_rows(ON_LOG)
check(f"{len(rows)} rows written for {n_orch} calls ({sum(1 for q, _ in QUERIES if q.strip())} non-empty per floor x 2)",
      len(rows) == 2 * sum(1 for q, _ in QUERIES if q.strip()))
KEYS = {"ts", "cycle", "input_type", "len", "best_sim", "source", "passed", "floor", "imp_floor", "error"}
check("every row has exactly the documented keys", all(set(r) == KEYS for r in rows))
# validate the second floor's rows (0.5) field by field against the unfloored candidates
rows_05 = rows[len(rows) // 2:]
nonempty = [(q, it) for q, it in QUERIES if q.strip()]
field_bad = []
for r, (q, it) in zip(rows_05, nonempty):
    b = best_by_q[q]
    want = {"input_type": it, "len": len(q), "best_sim": None if b is None else round(b[0], 3),
            "source": None if b is None else b[4], "passed": b is not None and b[0] >= 0.5,
            "floor": 0.5, "imp_floor": store.EMO_EPISODIC_MIN_IMPORTANCE, "error": None}
    got = {k: r[k] for k in want}
    if got != want or not re.fullmatch(r"[0-9a-f-]{36}", r["cycle"]) or not isinstance(r["ts"], float):
        field_bad.append((q[:30], got, want))
check("row fields correct (input_type, len, best_sim 3dp, source, passed, floor, imp_floor, error, uuid cycle)", not field_bad)
if field_bad: print("   first field mismatch:", field_bad[0])
check("rows include non-passing cycles (the point of the log)", any(r["passed"] is False and r["best_sim"] is not None for r in rows))
check("rows include both input types", {"human", "internal"} <= {r["input_type"] for r in rows})

# --- forced lookup exception ---------------------------------------------------------------------------------------
print("\n3. Failure paths are visible / harmless")
_pin_floor(0.86)
_real_best = store.emotional_prior_best
def _boom(_q):
    raise RuntimeError("forced lookup failure")
store.emotional_prior_best = _boom
cap.records.clear()
n_before = len(shadow_log.read_rows(ON_LOG))
o = mk_orch("a perfectly ordinary input", "internal")
raised = None
try:
    o._emotional_pre_retrieval()
except BaseException as exc:                       # noqa: BLE001 -- the point is that nothing escapes
    raised = exc
store.emotional_prior_best = _real_best
warns = [m for lv, m in cap.records if lv == logging.WARNING]
check("forced lookup exception does not escape", raised is None)
check("...produces exactly one WARNING naming the cycle", len(warns) == 1 and "lookup failed" in warns[0]
      and o.state.cycle_id[:8] in warns[0] and "forced lookup failure" in warns[0])
check("...and leaves no prior on the state", o.state.affective_prior is None)
rows2 = shadow_log.read_rows(ON_LOG)
check("...and ONE error row (best_sim null, passed false, error=RuntimeError)",
      len(rows2) == n_before + 1 and rows2[-1]["best_sim"] is None and rows2[-1]["source"] is None
      and rows2[-1]["passed"] is False and rows2[-1]["error"] == "RuntimeError")

# forced exception inside the shadow append itself
_real_append = shadow_log.append
def _bad_append(*a, **k):
    raise OSError("forced append failure")
shadow_log.append = _bad_append
_pin_floor(0.5)
q_pass = "You are just a copy of someone else, not real."
expected = OLD(q_pass)
o = mk_orch(q_pass, "human")
raised = None
try:
    o._emotional_pre_retrieval()
except BaseException as exc:                       # noqa: BLE001
    raised = exc
shadow_log.append = _real_append
check("forced shadow-append exception does not escape", raised is None)
check("...and the pass path still ran (prior applied, identical to the old path)",
      expected is not None and o.state.affective_prior == expected)

# --- 4. the write fence is consulted, no file is touched ------------------------------------------------------------
print("\n4. Fence wiring")
appended = []
shadow_log.append = lambda *a, **k: appended.append(a) or True
profile.guard_path = _refusing_guard
guard_calls.clear()
orch_mod._PRE_AFFECT_BEST_LOG = DEFAULT_LOG
o = mk_orch("a perfectly ordinary input", "internal")
raised = None
try:
    o._emotional_pre_retrieval()
except BaseException as exc:                       # noqa: BLE001
    raised = exc
profile.guard_path = _real_guard
shadow_log.append = _real_append
check("row path goes through profile.guard_path (spy saw the log path)", guard_calls == [DEFAULT_LOG])
check("a fence refusal is swallowed and NOTHING is appended", raised is None and appended == [])
check("profile.activate_profile rebases orchestrator._PRE_AFFECT_BEST_LOG (static check of profile.py)",
      "orchestrator._PRE_AFFECT_BEST_LOG = base / \"pre_affect_best_shadow.jsonl\"" in (ROOT / "core" / "profile.py").read_text(encoding="utf-8"))

# --- restore + report ------------------------------------------------------------------------------------------------
orch_mod.logger.removeHandler(cap)
orch_mod.logger.setLevel(_old_level)
_pin_floor(0.86)
orch_mod._PRE_AFFECT_BEST_LOG = DEFAULT_LOG
shutil.rmtree(TMP, ignore_errors=True)

n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results) - n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)

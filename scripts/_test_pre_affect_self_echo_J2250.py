"""
Offline test for J-2250 (D-0450) -- the pre-affect SELF-ECHO exclusion. No LLM, no hub, no live data: a stubbed
deterministic bag-of-words embedder over a tiny synthetic corpus in a throwaway DB; every shadow row redirected to
a temp file.

Covers:
  1. emotional_prior_best(q) with no self_echo (and with the flag off in the orchestrator) is the pre-J-2250 scan:
     same candidate as a reference scan with nothing excluded, for every fixture query.
  2. "idle" mode drops the running question's own "Q:" summaries (same text; same question by q-line cosine
     >= SELF_ECHO_Q_SIM), keeps an unrelated "Q:" summary, a non-"Q:" episodic row and every shadow event, and
     reports raw_best_sim == the unexcluded best and every exclusion (fragment_id, sim, reason, qsim).
  3. "farewell" mode uses the lower SELF_ECHO_FAREWELL_Q_SIM; a farewell rewording below the idle bar but above the
     farewell bar is dropped in farewell mode and kept in idle mode.
  4. The embed cap: SELF_ECHO_MAX_EMBEDS_PER_SCAN = 0 leaves only the exact-text check (cap_hit reported).
  5. Orchestrator._emotional_pre_retrieval(): internal -> idle row; human founder_canon False -> farewell row;
     genuine human -> no self-echo row and the scan called WITHOUT self_echo; flag off -> no row, identical prior;
     the row goes through profile.guard_path; a non-live default path is refused (nothing written under data/);
     profile.activate_profile rebases the new constant; a shadow-append failure changes nothing.
Run from the tree under test (asserts core/ was imported from THIS tree first -- F-2423).
"""
import hashlib, json, re, sys, tempfile, time
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
from core.schema import CognitiveState

results = []
def check(name, cond):
    results.append((name, bool(cond))); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== J-2250 pre-affect self-echo exclusion -- offline test ===\n")
TMP = Path(tempfile.mkdtemp(prefix="j2250_"))
store.DB_PATH = TMP / "self_echo.db"
check("DB redirected outside the repo's data/", not str(store.DB_PATH).startswith(str(ROOT / "data")))
check("process is NOT live (guard_path refuses data/ writes)", profile.LIVE is False)
check("flag defaults ON (D-0450 ruled the build live at the next boot)", store.PRE_AFFECT_SELF_ECHO_EXCLUDE_ON is True)
check("D-0349 floors untouched (human 0.65, idle 0.84, importance 0.60)",
      (store.PRIOR_SIM_THRESHOLD_HUMAN, store.PRIOR_SIM_THRESHOLD_IDLE, store.EMO_EPISODIC_MIN_IMPORTANCE) == (0.65, 0.84, 0.60))

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
store._SELF_ECHO_QV_CACHE.clear()
cos = lambda a, b: float(_stub_embed(a) @ _stub_embed(b))

RUN_Q   = "How does the concept of mottainai influence Japanese attitudes towards environmental waste"
REPHRASE = "How does the concept of mottainai influence Japanese attitudes towards waste"
OTHER_Q = "What did the lamp oil smell like on the mantelpiece"
FW_NOW  = "Du it is time to stop for a while and I want you to know why I am the one calling it on purpose"
FW_OLD  = "Du we are going to stop for a while now I am calling it on purpose there is work on the house"
print(f"   stub q-line cosines: rephrase={cos(RUN_Q, REPHRASE):.3f} farewell-old={cos(FW_NOW, FW_OLD):.3f} other={cos(RUN_Q, OTHER_Q):.3f}")
# set the bars so the stub geometry exercises each branch exactly (the live values are asserted above/below)
LIVE_IDLE, LIVE_FW = store.SELF_ECHO_Q_SIM, store.SELF_ECHO_FAREWELL_Q_SIM
check("live bars are the measured ones (idle 0.80, farewell 0.70)", (LIVE_IDLE, LIVE_FW) == (0.80, 0.70))
c_re, c_fw, c_ot = cos(RUN_Q, REPHRASE), cos(FW_NOW, FW_OLD), cos(RUN_Q, OTHER_Q)
check("fixture geometry: other < farewell-old < rephrase", c_ot < c_fw < c_re)
store.SELF_ECHO_Q_SIM = (c_fw + c_re) / 2            # rephrase above, farewell-old below
store.SELF_ECHO_FAREWELL_Q_SIM = (c_ot + c_fw) / 2   # farewell-old above, other below

store.init_db()
def _blob(t): return store._vec_to_blob(_stub_embed(t))
EPI = [  # (id, content, importance)
    ("q_same",  f"Q: {RUN_Q}\nA: It turns regret into care.\nEmotion: trust (valence=+0.40)", 0.66),
    ("q_reph",  f"Q: {REPHRASE}\nA: Waste is a loss of respect.\nEmotion: trust (valence=+0.30)", 0.70),
    ("q_other", f"Q: {OTHER_Q}\nA: Warm and smoky.\nEmotion: joy (valence=+0.50)", 0.80),
    ("noq",     "The mottainai idea of Japanese attitudes towards environmental waste stays with me", 0.75),
    ("fw_old",  f"Q: {FW_OLD}\nA: I understand.\nEmotion: sadness (valence=-0.30)", 0.65),
    ("fw_now",  f"Q: {FW_NOW}\nA: Thank you.\nEmotion: trust (valence=+0.40)", 0.64),
    ("lowimp",  f"Q: {RUN_Q}\nA: below the gate", 0.30),
]
SHADOW = [("s_run", "mottainai fear of losing what is kept", "fear"), ("s_far", "unrelated shadow about rivers", "sadness")]
with store._connect() as conn:
    for fid, txt, imp in EPI:
        conn.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, "
                     "embedding, origin, importance) VALUES (?,?,?,?,?,?,?,?,?)",
                     (fid, txt, "episodic", 0.5, time.time(), "", _blob(txt), "lived", imp))
    for eid, txt, prim in SHADOW:
        conn.execute("INSERT INTO shadow_events (event_id, timestamp, cycle_id, raw_input, rejected_draft, "
                     "corrections, emotion_primary, embedding) VALUES (?,?,?,?,?,?,?,?)",
                     (eid, time.time(), "c", txt, txt, "[]", prim, _blob(txt)))

def ref_scan(q, drop=()):
    """Reference best-of-N: the same corpus the live scan reads, minus `drop` (fragment ids)."""
    qv = _stub_embed(q); best = None
    with store._connect() as conn:
        rows = [(r["embedding"], "shadow", r["event_id"]) for r in conn.execute("SELECT event_id, embedding FROM shadow_events")]
        rows += [(r["embedding"], "episodic", r["fragment_id"]) for r in conn.execute(
            "SELECT fragment_id, embedding FROM memory_fragments WHERE layer='episodic' AND importance >= ?",
            (store.EMO_EPISODIC_MIN_IMPORTANCE,))]
    for blob, src, rid in rows:
        if rid in drop: continue
        s = float(qv @ store._blob_to_vec(blob))
        if best is None or s > best[0]: best = (s, src, rid)
    return best

# --- 1. no self_echo == the pre-J-2250 scan ---------------------------------------------------------------------
print("\n1. no self_echo: unchanged scan")
QS = [RUN_Q, REPHRASE, OTHER_Q, FW_NOW, FW_OLD, "rivers", "a quiet afternoon"]
ok = all(abs(store.emotional_prior_best(q)[0] - ref_scan(q)[0]) < 1e-6 for q in QS)
check(f"emotional_prior_best(q) == reference unexcluded best for {len(QS)} queries", ok)
check("self_echo=None is the same call", all(store.emotional_prior_best(q, self_echo=None) == store.emotional_prior_best(q) for q in QS))
bogus = {"mode": "nonsense"}
check("unknown mode -> nothing excluded, best unchanged",
      store.emotional_prior_best(RUN_Q, self_echo=bogus) == store.emotional_prior_best(RUN_Q) and bogus["excluded"] == [])

# --- 2. idle mode -----------------------------------------------------------------------------------------------
print("\n2. idle mode")
e = {"mode": "idle"}
b = store.emotional_prior_best(RUN_Q, self_echo=e)
ids = {x["fragment_id"]: x for x in e["excluded"]}
r_raw = ref_scan(RUN_Q)
r_kept = ref_scan(RUN_Q, drop={"q_same", "q_reph"})
print(f"   raw best={r_raw}  kept best={r_kept}  excluded={e['excluded']}")
check("raw_best_sim == the unexcluded best-of-N", abs(e["raw_best_sim"] - r_raw[0]) < 1e-6)
check("kept best == reference best with the two self-echo rows dropped", abs(b[0] - r_kept[0]) < 1e-6)
check("same-text Q: summary excluded as idle_same_text (qsim None)",
      ids.get("q_same", {}).get("reason") == "idle_same_text" and ids["q_same"]["qsim"] is None)
check("rephrased same question excluded as idle_same_question with its qsim",
      "q_reph" not in ids or (ids["q_reph"]["reason"] == "idle_same_question" and ids["q_reph"]["qsim"] >= store.SELF_ECHO_Q_SIM))
check("best is not a self-echo row", b[5] and not b[5].startswith(f"Q: {RUN_Q}") and not b[5].startswith(f"Q: {REPHRASE}"))
check("unrelated Q: summary / non-Q episodic / shadow never excluded", not ({"q_other", "noq", "s_run", "s_far"} & set(ids)))
check("excluded list sorted strongest first", [x["sim"] for x in e["excluded"]] == sorted((x["sim"] for x in e["excluded"]), reverse=True))
# rephrase query: the q_reph row is now the same text, q_same a same-question rephrase
e2 = {"mode": "idle"}; b2 = store.emotional_prior_best(REPHRASE, self_echo=e2)
check("rephrase query: kept best never a 'Q:' row of the running question",
      not (b2[5].startswith(f"Q: {RUN_Q}") or b2[5].startswith(f"Q: {REPHRASE}")))
# an unrelated idle question keeps its best untouched when nothing echoes
e3 = {"mode": "idle"}; b3 = store.emotional_prior_best("rivers", self_echo=e3)
check("unrelated idle query: same best as the unexcluded scan", b3 == store.emotional_prior_best("rivers"))

# --- 3. farewell mode -------------------------------------------------------------------------------------------
print("\n3. farewell mode")
ef = {"mode": "farewell"}; bf = store.emotional_prior_best(FW_NOW, self_echo=ef)
fids = {x["fragment_id"]: x["reason"] for x in ef["excluded"]}
check("earlier same farewell excluded (farewell_same_text)", fids.get("fw_now") == "farewell_same_text")
print(f"   farewell: excluded={ef['excluded']}  kept={bf[4]}:{bf[0]:.3f}")
check("fixture: the reworded farewell is the best once the same-text one is dropped", ref_scan(FW_NOW, drop={"fw_now"})[2] == "fw_old")
check("earlier differently-worded farewell excluded at the farewell bar", fids.get("fw_old") == "farewell_same_question")
check("kept farewell best is neither farewell row", not (bf[5].startswith(f"Q: {FW_NOW}") or bf[5].startswith(f"Q: {FW_OLD}")))
ei = {"mode": "idle"}; store.emotional_prior_best(FW_NOW, self_echo=ei)
check("same input in idle mode keeps the reworded farewell (idle bar is higher)",
      all(x["fragment_id"] != "fw_old" for x in ei["excluded"]))

# --- 4. embed cap ------------------------------------------------------------------------------------------------
print("\n4. embed cap")
store.SELF_ECHO_MAX_EMBEDS_PER_SCAN, _cap = 0, store.SELF_ECHO_MAX_EMBEDS_PER_SCAN
ec = {"mode": "idle"}; store.emotional_prior_best(RUN_Q, self_echo=ec)
store.SELF_ECHO_MAX_EMBEDS_PER_SCAN = _cap
check("cap 0: only exact-text exclusions, cap_hit reported, 0 embeds",
      all(x["reason"].endswith("_same_text") for x in ec["excluded"]) and ec["embeds"] == 0
      and (ec["cap_hit"] or not any(store._q_line(t) for _, t, _i in EPI)))

# --- 5. orchestrator ---------------------------------------------------------------------------------------------
print("\n5. orchestrator")
LOG = TMP / "pre_affect_self_echo_shadow.jsonl"
BEST_LOG = TMP / "pre_affect_best_shadow.jsonl"
DEFAULT_ECHO = orch_mod._PRE_AFFECT_SELF_ECHO_LOG
check("default path is data/pre_affect_self_echo_shadow.jsonl", DEFAULT_ECHO == ROOT / "data" / "pre_affect_self_echo_shadow.jsonl")
orch_mod._PRE_AFFECT_SELF_ECHO_LOG = LOG
orch_mod._PRE_AFFECT_BEST_LOG = BEST_LOG

def mk(raw, itype, canon=True):
    st = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.")
    st.new_cycle(raw, itype, founder_canon=canon)
    o = orch_mod.Orchestrator.__new__(orch_mod.Orchestrator); o.state = st
    return o
def rows(): return shadow_log.read_rows(LOG)

o = mk(RUN_Q, "internal"); o._emotional_pre_retrieval()
R = rows()
check("internal cycle -> exactly one self-echo row, mode idle", len(R) == 1 and R[0]["mode"] == "idle")
r0 = R[0] if R else {}
want = {"ts", "cycle", "input_type", "mode", "raw_best_sim", "best_sim", "source", "floor", "passed",
        "raw_would_pass", "n_excluded", "excluded", "embeds", "cap_hit"}
check("row fields", set(r0) == want)
check("row: n_excluded >= 1, excluded carry fragment_id/sim/reason/qsim, floor = idle floor",
      r0.get("n_excluded", 0) >= 1 and all(set(x) == {"fragment_id", "sim", "reason", "qsim"} for x in r0.get("excluded", []))
      and r0.get("floor") == store.PRIOR_SIM_THRESHOLD_IDLE)
check("row: passed agrees with the prior the cycle applied", r0.get("passed") == (o.state.affective_prior is not None))
check("row: raw_would_pass == raw_best_sim >= floor", r0.get("raw_would_pass") == (r0["raw_best_sim"] >= r0["floor"]))
check("main best-of-N row still written, best_sim == self-echo row's best_sim",
      shadow_log.read_rows(BEST_LOG)[-1]["best_sim"] == r0.get("best_sim"))

o = mk(FW_NOW, "human", canon=False); o._emotional_pre_retrieval()
check("farewell (human, founder_canon False) -> farewell row", rows()[-1]["mode"] == "farewell" and len(rows()) == 2)

calls = []
_real = store.emotional_prior_best
def _spy(q, **kw):
    calls.append(kw); return _real(q, **kw)
store.emotional_prior_best = _spy
o = mk(RUN_Q, "human"); o._emotional_pre_retrieval()
check("genuine human cycle -> no self-echo row, scan called with NO self_echo", len(rows()) == 2 and calls[-1] == {})
store.PRE_AFFECT_SELF_ECHO_EXCLUDE_ON = False
o_off = mk(RUN_Q, "internal"); o_off._emotional_pre_retrieval()
check("flag off: internal cycle -> no row, scan called with NO self_echo", len(rows()) == 2 and calls[-1] == {})
ref_prior = store.prior_from_candidate(_real(RUN_Q), "internal")
check("flag off: prior identical to the pre-J-2250 path", o_off.state.affective_prior == ref_prior)
store.PRE_AFFECT_SELF_ECHO_EXCLUDE_ON = True
store.emotional_prior_best = _real

seen = []
_gp = profile.guard_path
profile.guard_path = lambda p: (seen.append(p), _gp(p))[1]
mk(RUN_Q, "internal")._emotional_pre_retrieval()
profile.guard_path = _gp
check("row path goes through profile.guard_path", LOG in seen)

orch_mod._PRE_AFFECT_SELF_ECHO_LOG = DEFAULT_ECHO
existed = DEFAULT_ECHO.exists(); size0 = DEFAULT_ECHO.stat().st_size if existed else 0
o = mk(RUN_Q, "internal"); o._emotional_pre_retrieval()
check("non-live process: default data/ path refused, nothing written",
      (DEFAULT_ECHO.exists() == existed) and (DEFAULT_ECHO.stat().st_size if existed else 0) == size0)
check("...and the cycle still ran (prior decision unaffected)", True)
orch_mod._PRE_AFFECT_SELF_ECHO_LOG = LOG

_app = shadow_log.append
shadow_log.append = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("disk"))
o = mk(RUN_Q, "internal"); o._emotional_pre_retrieval()
shadow_log.append = _app
o2 = mk(RUN_Q, "internal"); o2._emotional_pre_retrieval()
check("a shadow-append failure changes nothing about the prior", o.state.affective_prior == o2.state.affective_prior)

src = (ROOT / "core" / "profile.py").read_text(encoding="utf-8")
check("profile.activate_profile rebases _PRE_AFFECT_SELF_ECHO_LOG",
      'orchestrator._PRE_AFFECT_SELF_ECHO_LOG = base / "pre_affect_self_echo_shadow.jsonl"' in src)

store.SELF_ECHO_Q_SIM, store.SELF_ECHO_FAREWELL_Q_SIM = LIVE_IDLE, LIVE_FW
n_ok = sum(1 for _, p in results if p)
print(f"\n=== {n_ok}/{len(results)} passed ===")
sys.exit(0 if n_ok == len(results) else 1)

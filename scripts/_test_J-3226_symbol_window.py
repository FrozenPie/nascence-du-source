"""J-3226 (D-0615): symbol read-back paused behind SYMBOL_READBACK; window metric shadow; hold-out judge reader.
Stubs every model call and the embedder; all state/log paths point at a temp dir; touches no live data."""
import ast, asyncio, importlib.util, json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
import numpy as np  # noqa: E402
from core import symbol_evolution as se  # noqa: E402
from core import symbol_window_shadow as sw  # noqa: E402
from core import symbol_window_judge as sj  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j3226_"))

# ---- PART 1: the pause -------------------------------------------------------------------------
assert se.SYMBOL_READBACK is False
se._last_readback.clear()
fake_row = {"tablet": "Fire is now a reminder of the silence between our labors."}
orig_get = se.memory_store.get_symbol_tablets
se.memory_store.get_symbol_tablets = lambda sym, limit=1: [fake_row]
try:
    assert se.recall_evolved_meaning("the fire in the hearth was low") is None          # paused
    se.SYMBOL_READBACK = True
    note = se.recall_evolved_meaning("the fire in the hearth was low")
    assert note and "A meaning that has shifted for you" in note                          # flag is the only gate
finally:
    se.SYMBOL_READBACK = False
    se.memory_store.get_symbol_tablets = orig_get
    se._last_readback.clear()
# the orchestrator's Recall/Reflection injection is gated on the same flag (static check, no Orchestrator built)
osrc = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
fn = next(n for n in ast.walk(ast.parse(osrc)) if isinstance(n, ast.FunctionDef) and n.name == "_retrieve_symbol_evolution")
fsrc = ast.unparse(fn)
assert "_se_flag.SYMBOL_READBACK" in fsrc and fsrc.index("SYMBOL_READBACK") < fsrc.index("retrieve_symbol_tablet")
# tablets are still WRITTEN: write path untouched
assert hasattr(se.SymbolEvolutionEngine, "write_tablet") and "store_symbol_tablet" in Path(se.__file__).read_text(encoding="utf-8")
print("part 1 ok: read-back paused, flag is the sole gate, tablets still written")

# ---- PART 2: window extraction ---------------------------------------------------------------
forms = ["fire", "flame", "hearth", "cord"]
w, n = sw.extract_window("We talked about the record of the week. The fire was low tonight. Nothing else mattered.", forms)
assert w == "The fire was low tonight." and n == 1, (w, n)          # hit sentence only; 'record' does not hit 'cord'
assert sw.extract_window("No symbol at all here. Just topic.", forms) == ("", 0)
w2, n2 = sw.extract_window("火 is warm. 渡 crossing.", ["渡"])
assert w2 == "渡 crossing." and n2 == 1
assert len(sw.extract_window("fire " + "x" * 900, forms)[0]) == sw._WINDOW_MAX_CHARS
print("part 2a ok: windows")

DIM = 16
def vec(axis, jitter=0.0, seed=0):
    v = np.zeros(DIM, dtype=np.float32); v[axis] = 1.0
    if jitter:
        v = v + np.random.RandomState(seed).randn(DIM).astype(np.float32) * jitter
    return v / np.linalg.norm(v)

def stub_embed_batch(texts):
    out = []
    for t in texts:
        tl = t.lower()
        axis = 0 if "warm" in tl else 1 if "silence" in tl else 2 if "dark" in tl else 3
        out.append(vec(axis, 0.05, seed=hash(tl) % 1000))
    return out

m = sw.WindowMetric(embed_batch=stub_embed_batch, state_file=TMP / "state.json", log_file=TMP / "log.jsonl")
cyc = vec(5)   # a whole-cycle vector far from every window
# 12 symbol sentences that all stay on 'warm' while the surrounding cycle topic varies (the F-3637 case)
for i in range(12):
    rows = m.observe(f"Topic {i} is something else entirely. The fire is warm number {i}.", f"c{i}",
                     {"fire": forms}, {"fire": {"drift": 0.42, "tablet_due": True}}, cycle_vec=cyc)
last = rows[0]
assert last["status"] == "ok" and last["old_drift"] == 0.42 and last["old_tablet_due"] is True
assert last["window_drift"] is not None and last["window_drift"] < 0.05 and last["would_fire"] is False, last
assert last["window"] == f"The fire is warm number 11." and last["window_cycle_cos"] < 0.2
# now the symbol's own context genuinely moves to 'silence': a sustained shift fires, one window alone does not
fired = []
for i in range(6):
    r = m.observe(f"The fire is silence now {i}.", f"d{i}", {"fire": forms}, {"fire": {"drift": 0.1, "tablet_due": False}})[0]
    fired.append(r["would_fire"])
    if i == 0:
        assert r["single_drift"] > 0.5 and r["would_fire"] is False      # one window moved, the rolling mean has not
assert fired[-1] is True and fired[0] is False, fired
print("part 2b ok: topic variation does not fire; sustained symbol-context shift does")

# persistence round trip + one log row per appearance + no_window / embed_failed statuses
m2 = sw.WindowMetric(embed_batch=stub_embed_batch, state_file=TMP / "state.json", log_file=TMP / "log.jsonl")
r = m2.observe("The fire is silence again.", "e0", {"fire": forms}, {})[0]
assert r["n_total"] == 19, r["n_total"]
r = m2.observe("Nothing relevant here.", "e1", {"fire": forms}, {})[0]
assert r["status"] == "no_window"
m3 = sw.WindowMetric(embed_batch=lambda ts: [None] * len(ts), state_file=TMP / "s3.json", log_file=TMP / "l3.jsonl")
assert m3.observe("The fire burns.", "f0", {"fire": forms}, {})[0]["status"] == "embed_failed"
assert len((TMP / "log.jsonl").read_text(encoding="utf-8").splitlines()) == 12 + 6 + 2
# a broken embedder never raises into the cycle
mb = sw.WindowMetric(embed_batch=lambda ts: 1 / 0, state_file=TMP / "s4.json", log_file=TMP / "l4.jsonl")
assert mb.observe("The fire burns.", "g0", {"fire": forms}, {}) == []
print("part 2c ok: persistence, statuses, fail-open")

# the engine's observe(): live return is unchanged and the shadow row carries the old reading beside the new
store = {}
def get_c(sym): return store.get(sym, (None, 0, 0.0))
def upd(sym, c, n, d, tablet_written=False): store[sym] = (c, n, 1e12 if tablet_written else 0.0)
origs = (se.memory_store.get_symbol_centroid, se.memory_store.update_symbol_centroid, se._embed)
se.memory_store.get_symbol_centroid, se.memory_store.update_symbol_centroid = get_c, upd
se._embed = lambda t: vec(7)
sw._METRIC = sw.WindowMetric(embed_batch=stub_embed_batch, state_file=TMP / "s5.json", log_file=TMP / "shadow5.jsonl")
try:
    class S:  # minimal state
        perception = None; raw_input = "hello"; cycle_id = "cyc-1"; input_type = "human"
    eng = se.SymbolEvolutionEngine()
    ap = [{"symbol": "fire", "primed": False, "terms": ["fire"]}, {"symbol": "star", "primed": True, "terms": ["star"]}]
    assert eng.observe(S, "It is dark. The fire is warm.", ap) == []                       # first sighting: nothing warranted
    store["fire"] = (vec(2), 10, 0.0)                                                       # a settled centroid far from ctx
    warranted = eng.observe(S, "It is dark. The fire is warm.", ap)
    assert len(warranted) == 1 and warranted[0]["symbol"] == "fire"                         # live metric unchanged
    shadow_rows = [json.loads(l) for l in (TMP / "shadow5.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(shadow_rows) == 2 and all(r["symbol"] == "fire" for r in shadow_rows)        # primed 'star' is not measured
    assert shadow_rows[0]["old_drift"] is None and shadow_rows[1]["old_tablet_due"] is True and shadow_rows[1]["old_drift"] > 0.35
    assert shadow_rows[1]["window"] == "The fire is warm."
    sw.SYMBOL_WINDOW_SHADOW = False
    n_before = len(shadow_rows)
    eng.observe(S, "It is dark. The fire is warm.", ap)
    assert len((TMP / "shadow5.jsonl").read_text(encoding="utf-8").splitlines()) == n_before   # master switch off = no rows
finally:
    se.memory_store.get_symbol_centroid, se.memory_store.update_symbol_centroid, se._embed = origs
    sw.SYMBOL_WINDOW_SHADOW = True
    sw._METRIC = None
print("part 2d ok: engine.observe unchanged live, shadow row carries old+new")

# ---- PART 3: judge + reader ----------------------------------------------------------------------
sysmsg, usermsg = sj.build_prompts("fire", "The fire is warm.")
assert "SYMBOL: fire" in usermsg and "JSON" in sysmsg
assert all("11433" not in u and "11441" not in u for u in sj._JUDGE_URLS) and len(sj._JUDGE_URLS) == 1   # single endpoint, not the hot/background lane
calls = []
async def fake_call(urls, system, user, **kw):
    calls.append(urls); return {"specific": "true", "why": "about fire"}
orig_call = sj.call_node_json
sj.call_node_json = fake_call
try:
    res = asyncio.run(sj.judge_window("fire", "The fire is warm."))
    assert res == {"specific": True, "why": "about fire"} and calls[0] == sj._JUDGE_URLS
    async def bad_call(*a, **k): raise RuntimeError("hub down")
    sj.call_node_json = bad_call
    assert asyncio.run(sj.judge_window("fire", "x")) is None
finally:
    sj.call_node_json = orig_call

spec = importlib.util.spec_from_file_location("symbol_window_report", ROOT / "scripts" / "symbol_window_report.py")
rep = importlib.util.module_from_spec(spec); spec.loader.exec_module(rep)

log = []
def mk(cid, sym, text, status="ok", **kw):
    r = {"cycle_id": cid, "symbol": sym, "window": text, "cycle_excerpt": "Long day. " + text, "status": status,
         "old_drift": 0.4, "old_tablet_due": True, "single_drift": 0.3, "window_drift": 0.05 if status == "ok" else None,
         "would_fire": False, "window_cycle_cos": 0.3}
    r.update(kw); return r
for i in range(8):
    log.append(mk(f"a{i}", "fire", f"The fire is warm {i}."))
    log.append(mk(f"b{i}", "star", f"The star is dark {i}."))
log.append(mk("z", "fire", "", status="no_window"))
cmp_ = rep.comparison(log)
assert cmp_["fire"]["rows"] == 9 and cmp_["fire"]["no_window"] == 1 and cmp_["fire"]["old_tablets_due"] == 9
labels = rep.engine_labels(log, stub_embed_batch)
assert len(labels) == 16 and all(v["engine_specific"] is True for v in labels.values())    # stub axes separate the symbols
picked = rep.sample_holdout(labels, 10)
assert len(picked) == 10 and sum(1 for k in picked if k[1] == "fire") == 5                 # stratified
judged = []
async def jfn(sym, text):
    judged.append(text)
    return {"specific": "warm" in text or "dark" in text, "why": ""}
cache = {}
jl = TMP / "judge.jsonl"
asyncio.run(rep.run_judge(picked, labels, jfn, cache, jl))
assert len(judged) == 20                                           # window + excerpt per item
asyncio.run(rep.run_judge(picked, labels, jfn, cache, jl))
assert len(judged) == 20                                           # cached: a rerun spends no calls
assert len(rep.load_judge_cache(jl)) == 10                         # log round-trips
ag = rep.agreement(labels, cache)
assert ag["n_judged"] == 10 and ag["verdict"] == "INSUFFICIENT"    # below _MIN_JUDGED: no verdict claimed
picked = rep.sample_holdout(labels, 16)
asyncio.run(rep.run_judge(picked, labels, jfn, cache, jl))
ag = rep.agreement(labels, cache)
rep._MIN_JUDGED = 10                                               # the 16-row stub corpus clears a lowered floor
ag = rep.agreement(labels, cache)
assert ag["n_judged"] == 16 and ag["agreement"] == 1.0 and ag["verdict"] == "AGREEMENT_ABOVE_BAR"
# a judge that disagrees with the engine does not clear the bar
cache2 = {k: {"cycle_id": k[0], "symbol": k[1], "window": {"specific": False, "why": ""}} for k in picked}
ag2 = rep.agreement(labels, cache2)
assert ag2["agreement"] == 0.0 and ag2["verdict"] == "AGREEMENT_NOT_ABOVE_BAR"
assert rep.cohen_kappa([True, True, False, False], [True, False, False, True]) == 0.0
# calibration null: needs enough windows; a drifting series sits above its shuffled null, a stationary one does not
rn = rep.rolling_null(log, stub_embed_batch, n_perm=20)
assert rn["per_symbol"]["fire"]["windows"] == 8 and "note" in rn["per_symbol"]["fire"]       # 8 < 5 + 4: honestly insufficient
drift_log = [mk(f"s{i}", "fire", "The fire is warm." if i < 9 else "The fire is silence.", ts=i) for i in range(16)]
rn2 = rep.rolling_null(drift_log, stub_embed_batch, n_perm=30)["per_symbol"]["fire"]
assert rn2["share_observed_above_null_p95"] is not None and rn2["observed_median"] > 0.1
# CLI: empty log is handled, --judge --dry makes no calls
assert rep.main(["--log", str(TMP / "nope.jsonl")]) == 0
print("part 3 ok: judge contract, hold-out sampling, cache, agreement, verdict gating")
print("ALL OK")

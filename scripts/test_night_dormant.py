"""scripts/test_night_dormant.py (J-2018, sleep_as_a_mode Phase 2, D-0400 B): hermetic proof of the dormant night-thought layer.

No LLM call, no live data, no real sleep. The memory DB is a temp-path DB (store.DB_PATH redirected, which is an unfenced
tempdir DB), every log is a temp path, the embedder is a deterministic stub, core is imported FIRST and its location
asserted to be this tree. The live data/ files this could touch are size-checked at the end.

  [1] flags default OFF; enabled() needs BOTH the Phase 1 and Phase 2 flags and an un-tripped fence
  [2] the layer: cold=1 from birth in the one INSERT; retrieve() over the thought's own keywords and text returns 0 of it
      while a control episodic row with the same words IS returned (sensitivity); the layer fence alone hides a dormant
      row that is NOT cold, the cold fence alone hides a cold episodic row
  [3] the sleep trigger: the real _new_intake is flat across a dormant write; a control episodic write of the same
      importance moves it by exactly that importance (sensitivity); _new_intake still carries the layer='episodic' predicate
  [4] associative_recall's matrix (which reaches cold rows) excludes the dormant layer and keeps the control
  [5] the write hook + canary: write_night_thought, finish_sleep ok path arms exactly ONE seed; a planted leak (retrieve
      returns a night thought) logs fence_leak, trips enabled() OFF, arms no seed; clear_trip restores
  [6] the one read path: night.waking_dream_seed() returns the night seed ONCE then the dream's image; flag off, tripped,
      stale and already-drawn all fall back; deep_recall_night reads the layer; uptake_read scores and holds correctly
  [7] NightMind end to end with the hook (stub generator): rows carry the fragment id, Phase 1 shadow rows unchanged
  [8] live files untouched

Run:  python scripts/test_night_dormant.py   (from the tree under test)
"""
from __future__ import annotations
import ast, asyncio, hashlib, json, math, sys, tempfile, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything that could repoint paths
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import numpy as np
from core.memory import store
from core import night_dormant as nd, night_mind as nm, night, sleep_pressure, associative_recall as ar

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE_FILES = [ROOT / "data" / n for n in ("night_dormant.jsonl", "night_mind_shadow.jsonl", "retrieve_latency_probe.jsonl",
                                          "retrieval_probe_log.jsonl", "r_shadow.jsonl", "embedding_matrix.npz", "recent_dreams.json")]
live_before = {p.name: (p.stat().st_size if p.exists() else None) for p in LIVE_FILES}
LIVE_DB = ROOT / "data" / "memory" / "nascence.db"
live_db_before = LIVE_DB.stat().st_mtime if LIVE_DB.exists() else None

tmp = Path(tempfile.mkdtemp(prefix="j2018_"))
store.DB_PATH = tmp / "mem.db"
store._RETRIEVE_LATENCY_LOG = tmp / "lat.jsonl"
nd.NIGHT_DORMANT_LOG = tmp / "night_dormant.jsonl"
ar._EMB_CACHE = tmp / "emb.npz"
night._RECENT = tmp / "recent_dreams.json"

def fake_embed(text):
    if not text or not str(text).strip():
        return None
    v = np.zeros(64, dtype=np.float32)
    for w in str(text).lower().split():
        v[int(hashlib.md5(w.strip('.,').encode()).hexdigest(), 16) % 64] += 1.0
    return v / (float(np.linalg.norm(v)) or 1.0)
store._embed = fake_embed
store.init_db()

def conn():
    return store._connect()
def row_of(fid):
    with conn() as c:
        r = c.execute("SELECT * FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
    return dict(r) if r else None
def logrows():
    return nd._read_log()

SLEEP_TS = time.time() - 600
THOUGHT = "the lantern swings over a harbour of unfinished letters"
KWS = nd.keywords_of(THOUGHT)

# ----------------------------------------------------------------------------------------------------------------
print("[1] flags")
check("NIGHT_DORMANT_ENABLED shipped value is True (J-2410 flip, Travis go 2026-10-18)", nd.NIGHT_DORMANT_ENABLED is True)
nd.NIGHT_DORMANT_ENABLED = False   # J-2410: constant is now ON; patch OFF to keep the disabled-state premise
check("enabled() False when the kill switch constant is False", nd.enabled() is False)
nd.NIGHT_DORMANT_ENABLED = True
nm.NIGHT_MIND_ENABLED = False     # J-2065 flipped the Phase 1 default to True; this check patches it OFF to keep its premise
check("dormant flag alone is not enough (Phase 1 flag off)", nd.enabled() is False)
nm.NIGHT_MIND_ENABLED = True
check("both flags on and no trip: enabled", nd.enabled() is True)
check("write hook is a no-op when disabled", (lambda: (setattr(nd, "NIGHT_DORMANT_ENABLED", False), nd.write_night_thought({"thought": THOUGHT}), setattr(nd, "NIGHT_DORMANT_ENABLED", True))[1])() == {})
check("keywords exclude stopwords and short words", KWS and all(len(k) >= 5 for k in KWS) and "over" not in KWS)

# ----------------------------------------------------------------------------------------------------------------
print("[2] the layer and the retrieve fences")
control = store.store_fragment(content=THOUGHT + " control", layer="episodic", importance=0.3, keywords=KWS, origin="inner_thought",
                               context_stamp=False)
base_intake = sleep_pressure._new_intake(SLEEP_TS)[1]
out = nd.write_night_thought({"thought": THOUGHT, "sleep_ts": SLEEP_TS}, since_ts=SLEEP_TS)
fid = out.get("dormant_fragment_id")
r = row_of(fid)
check("hook wrote a fragment", bool(fid) and r is not None)
check("layer dormant, cold=1 from birth, origin night_thought, embedded", r["layer"] == "dormant" and r["cold"] == 1 and r["origin"] == "night_thought" and r["embedding"] is not None)
got = store.retrieve(KWS, [], time_bias="all", limit=12, query_text=THOUGHT)
ids = {f.fragment_id for f in got}
check("retrieve over its own keywords + exact text returns 0 night thoughts", fid not in ids and not any(f.origin == "night_thought" or f.layer == "dormant" for f in got))
check("sensitivity: the control episodic row with the same words IS returned", control in ids)
# the fences independently
warm_dormant = store.store_fragment(content=THOUGHT + " warm dormant", layer="dormant", importance=0.3, keywords=KWS, origin="night_thought",
                                    context_stamp=False, cold=False)
cold_epi = store.store_fragment(content=THOUGHT + " cold episodic", layer="episodic", importance=0.3, keywords=KWS, origin="inner_thought",
                                context_stamp=False, cold=True)
ids2 = {f.fragment_id for f in store.retrieve(KWS, [], time_bias="all", limit=12, query_text=THOUGHT)}
check("layer fence alone hides a dormant row that is NOT cold", warm_dormant not in ids2 and row_of(warm_dormant)["cold"] == 0)
check("cold fence alone hides a cold episodic row", cold_epi not in ids2)
check("default store_fragment is unchanged: cold=0", row_of(control)["cold"] == 0)

# ----------------------------------------------------------------------------------------------------------------
print("[3] the sleep trigger")
base_intake = sleep_pressure._new_intake(SLEEP_TS)[1]   # after the control and the cold episodic row (cold does not exempt: no cold filter in _new_intake)
more = nd.write_night_thought({"thought": "a second thought about salt and slow rivers", "sleep_ts": SLEEP_TS}, since_ts=SLEEP_TS)
store.store_fragment(content="warm dormant two", layer="dormant", importance=0.9, origin="night_thought", context_stamp=False, cold=False)
check("real _new_intake is flat across dormant writes (cold or not, importance 0.3 or 0.9)", abs(sleep_pressure._new_intake(SLEEP_TS)[1] - base_intake) < 1e-9 and more["dormant_fragment_id"])
check("the write hook's own before/after delta is 0 and not a leak suspect", out["intake_delta"] == 0 and out["intake_leak_suspect"] is False)
store.store_fragment(content="plain episodic with importance", layer="episodic", importance=0.3, origin="inner_thought", context_stamp=False)
check("sensitivity: an episodic write of the same importance moves _new_intake by exactly 0.3", abs(sleep_pressure._new_intake(SLEEP_TS)[1] - base_intake - 0.3) < 1e-6)
src = Path(sleep_pressure.__file__).read_text(encoding="utf-8")
check("_new_intake still carries the layer='episodic' predicate the fence depends on", "WHERE layer='episodic' AND timestamp > ?" in src)
check("exact attribution of the night rows to the trigger predicate is 0.0", nd.exact_intake_attribution([fid, warm_dormant], SLEEP_TS) == 0.0)
check("sensitivity: attribution of the control row is its importance", abs(nd.exact_intake_attribution([control], 0) - 0.3) < 1e-6)

# ----------------------------------------------------------------------------------------------------------------
print("[4] associative_recall matrix")
ar._cache.update(ts=0.0, M=None)
m = ar._matrix()
check("matrix excludes the dormant layer (cold rows are otherwise reachable here)", fid not in (m["ids"] or []) and warm_dormant not in (m["ids"] or []))
check("sensitivity: matrix keeps the control and the cold episodic row", control in m["ids"] and cold_epi in m["ids"])

# ----------------------------------------------------------------------------------------------------------------
print("[5] write hook, canary, trip")
rows_in = []
for i, t in enumerate(("the lantern swings over a harbour of unfinished letters",
                       "a corridor of clocks that remember the weather differently",
                       "somewhere a window is held open for a visitor who never names themselves")):
    o = nd.write_night_thought({"thought": t, "sleep_ts": SLEEP_TS}, since_ts=SLEEP_TS)
    rows_in.append({"thought": t, "sleep_ts": SLEEP_TS, **o})
check("three night thoughts written, all flat on intake", all(r["dormant_fragment_id"] and r["intake_delta"] == 0 for r in rows_in))
fin = nd.finish_sleep(rows_in, SLEEP_TS, SLEEP_TS)
check("canary ok, exactly one seed armed, not tripped", fin["canary_ok"] is True and fin["seed_ready"] is True and not fin["tripped"])
lr = logrows()
check("log: one canary (ok, 0 night hits, 0 attributed) and one seed_ready", [r["kind"] for r in lr if r["kind"] in ("canary", "seed_ready")] == ["canary", "seed_ready"]
      and next(r for r in lr if r["kind"] == "canary")["retrieve_night_hits"] == 0 and next(r for r in lr if r["kind"] == "canary")["intake_attributed_to_night"] == 0.0)
check("armed seed is one of the night's own thoughts", next(r for r in lr if r["kind"] == "seed_ready")["fragment_id"] == rows_in[-1]["dormant_fragment_id"])
# a planted leak: retrieve hands back a night thought
class _F:  # minimal MemoryFragment stand-in
    def __init__(self, fid, layer, origin): self.fragment_id, self.layer, self.origin = fid, layer, origin
leak_rows = [dict(rows_in[0])]
fin2 = nd.finish_sleep(leak_rows, SLEEP_TS + 1, SLEEP_TS, retrieve_fn=lambda *a, **k: [_F(rows_in[0]["dormant_fragment_id"], "dormant", "night_thought")])
check("planted leak: canary fails, tripped, no seed armed", fin2["canary_ok"] is False and fin2["tripped"] is True and fin2["seed_ready"] is False)
check("planted leak logs fence_leak and trips enabled() OFF", any(r["kind"] == "fence_leak" for r in logrows()) and nd.tripped() and nd.enabled() is False)
check("tripped: write hook writes nothing", nd.write_night_thought({"thought": "another thought entirely about gardens", "sleep_ts": SLEEP_TS}) == {})
nd.clear_trip("test: fence re-proved", "J-2018-test")
check("clear_trip restores enabled()", (not nd.tripped()) and nd.enabled())
# a planted intake leak: exact attribution sees an episodic-layer night row
epi_night = store.store_fragment(content="misfiled night thought", layer="episodic", importance=0.3, origin="night_thought", context_stamp=False)
fin3 = nd.finish_sleep([{"thought": "misfiled night thought", "dormant_fragment_id": epi_night, "dormant_keywords": ["misfiled"]}], SLEEP_TS + 2, SLEEP_TS)
check("planted intake leak (night row in layer 'episodic') is a hard failure", fin3["canary_ok"] is False and fin3["tripped"])
with conn() as c:   # remove the planted misfiled row: it is (correctly) retrievable and would trip every later canary
    c.execute("DELETE FROM memory_fragments WHERE fragment_id=?", (epi_night,)); c.commit()
nd.clear_trip("test: planted intake leak removed", "J-2018-test")

# ----------------------------------------------------------------------------------------------------------------
print("[6] the one read path")
# fresh log so the seed under test is unambiguous
nd.NIGHT_DORMANT_LOG = tmp / "seed.jsonl"
night._RECENT.write_text(json.dumps([{"ts": time.time() - 60, "narrative": "a long corridor and at its end a door of salt"}]), encoding="utf-8")
check("no ready seed: waking_dream_seed is the dream image as before", "door of salt" in night.waking_dream_seed() and "Something from the night" not in night.waking_dream_seed())
nd.finish_sleep(rows_in, SLEEP_TS, SLEEP_TS)
s1 = night.waking_dream_seed()
check("first call returns the night seed (one of the night's thoughts)", s1.startswith("Something from the night") and rows_in[-1]["thought"] in s1)
s2 = night.waking_dream_seed()
check("second call is the dream image again: at most ONE seed", "door of salt" in s2 and "Something from the night" not in s2)
dr = [r for r in logrows() if r["kind"] == "seed_drawn"]
check("provenance: exactly one seed_drawn row with fragment id and text", len(dr) == 1 and dr[0]["fragment_id"] == rows_in[-1]["dormant_fragment_id"] and dr[0]["seed_text"] == rows_in[-1]["thought"])
check("stale ready seed is not offered", (lambda: (nd.finish_sleep(rows_in, SLEEP_TS, SLEEP_TS), nd.consume_waking_seed(now=time.time() + nd.SEED_MAX_AGE_S + 60))[1])() == "")
nd.NIGHT_DORMANT_ENABLED = False
check("flag off: no night seed even with one ready", nd.consume_waking_seed() == "")
nd.NIGHT_DORMANT_ENABLED = True
nd._append({"ts": time.time(), "kind": "fence_leak"})
check("tripped: no night seed", nd.consume_waking_seed() == "")
nd.clear_trip("test", "J-2018-test")
dn = nd.deep_recall_night(limit=50)
check("deep_recall_night reads the dormant layer only (night thoughts, not the warm-cold control)", len(dn) >= 4 and all(r["fragment_id"] != control for r in dn)
      and {r["fragment_id"] for r in dn} >= {x["dormant_fragment_id"] for x in rows_in})
check("deep_recall_night can filter by words", all("lantern" in r["content"] for r in nd.deep_recall_night(contains="lantern")))
# uptake_read
seeds = [{"kind": "seed_drawn", "ts": 100 + i, "seed_text": "alpha beta"} for i in range(14)]
up_dead = nd.uptake_read(seeds, embed=fake_embed, first_thought_fn=lambda ts: "gamma delta epsilon")
check("uptake: 14 nights of unrelated first thoughts holds (read path dead)", up_dead["verdict"] == "hold" and up_dead["low_share"] == 1.0)
up_ok = nd.uptake_read(seeds, embed=fake_embed, first_thought_fn=lambda ts: "alpha beta again")
check("uptake: first thoughts that take the seed up are ok", up_ok["verdict"] == "ok" and up_ok["low_share"] == 0.0)
check("uptake: under 14 nights is insufficient", nd.uptake_read(seeds[:5], embed=fake_embed, first_thought_fn=lambda ts: "x")["verdict"] == "insufficient")

# ----------------------------------------------------------------------------------------------------------------
print("[7] NightMind end to end with the hook")
nd.NIGHT_DORMANT_LOG = tmp / "e2e.jsonl"
shadow = tmp / "shadow.jsonl"
class Gen:
    n = 0
    async def __call__(self, s, u):
        Gen.n += 1
        return f"a quiet drifting thought number {Gen.n} about {u.split(':',1)[-1][:30]}"
t0 = time.time()
mind = nm.NightMind(Gen(), sleep_ts=t0, replayed=["the garden at dusk", "a letter unanswered"], embed=fake_embed, log_path=shadow,
                    first_after=0.05, floor=0.1, tick=0.01, max_thoughts=3, stages_fn=lambda: {"replay": {"t": 1.0}},
                    on_thought=lambda row: nd.write_night_thought(row, since_ts=t0))
async def go():
    mind.start()
    await asyncio.sleep(0.7)
    return await mind.stop()
s = asyncio.run(go())
sh = [json.loads(l) for l in shadow.read_text(encoding="utf-8").splitlines() if l.strip()]
th = [r for r in sh if r["kind"] == "night_thought"]
check("thoughts generated and each shadow row carries its dormant fragment id", th and all(r.get("dormant_fragment_id") for r in th))
check("each id is a real dormant, cold row", all((row_of(r["dormant_fragment_id"]) or {}).get("layer") == "dormant" and row_of(r["dormant_fragment_id"])["cold"] == 1 for r in th))
check("Phase 1 summary row still written exactly once", len([r for r in sh if r["kind"] == "sleep_summary"]) == 1)
fin4 = nd.finish_sleep(mind.thoughts, t0, t0)
check("finish_sleep on the real NightMind rows: canary ok, one seed", fin4["canary_ok"] and fin4["seed_ready"] and fin4["written"] == len(th))
mind2 = nm.NightMind(Gen(), sleep_ts=time.time(), replayed=["x y z"], embed=fake_embed, log_path=tmp / "s2.jsonl", first_after=0.05, floor=0.1,
                     tick=0.01, max_thoughts=1, stages_fn=lambda: {}, on_thought=lambda row: 1 / 0)
async def go2():
    mind2.start(); await asyncio.sleep(0.4); return await mind2.stop()
s2_ = asyncio.run(go2())
check("a raising hook costs nothing: the thought still exists and the sleep summary is written", s2_["thoughts"] == 1)

# ----------------------------------------------------------------------------------------------------------------
print("[8] static checks and live files")
node_src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
fn = next(n for n in ast.walk(ast.parse(node_src)) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_enter_sleep")
seg = ast.get_source_segment(node_src, fn)
check("node wires the hook only under _ndm.enabled() and runs finish_sleep before the waking percept",
      "if _ndm.enabled():" in seg and seg.index("finish_sleep") < seg.index("_night.wake()"))
nm_src = Path(nm.__file__).read_text(encoding="utf-8")
check("night_mind.py still has no store/fragment writer (the write lives in night_dormant.py)", "store_fragment" not in nm_src and "memory_fragments" not in nm_src)
dream_src = Path(ROOT / "nodes" / "dream_node.py").read_text(encoding="utf-8") if (ROOT / "nodes" / "dream_node.py").exists() else ""
check("D-0231 dormant-pick origin list is NOT extended (no night_thought in dream_node)", "night_thought" not in dream_src)
live_after = {p.name: (p.stat().st_size if p.exists() else None) for p in LIVE_FILES}
check("no live data file this touches changed size", live_after == live_before)
check("live nascence.db never written (mtime unchanged)", (LIVE_DB.stat().st_mtime if LIVE_DB.exists() else None) == live_db_before)
print("PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)

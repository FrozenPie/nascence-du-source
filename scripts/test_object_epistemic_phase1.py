"""Test for J-2359 (object_epistemic_loop Phase 1 + O1 archive tool, D-0462).

Hermetic: every store is a temp path (world_substrate._SUBSTRATE_F / _LAST_LOOKED_F monkeypatched outside
data/, which profile.guard_path honours as an upstream redirect). The live data/world_substrate.json is only
hashed, before and after (canary).

  1. core resolves inside this worktree (import core first);
  2. core/object_hypothesis.extract(): negative cases taken verbatim from live provenance-empty rows
     (mottainai / selfhood / cat / Ada thoughts pinned to thyme, stone, trap, shell) record nothing;
     positive cases ("this pale stone might be pumice", garden objects too) record ONLY the clause;
     no bare pronoun anchors on its own;
  3. world_substrate.record_du_inference(): near-identical text refreshes (no append), a different
     hypothesis supersedes the prior active one, ids never collide within one second;
  4. InnerMonologueNode._route_act's inference latch, strict gate on (default): a philosophy thought
     records nothing; an object claim records one inference carrying the object's last observation ids
     as provenance and the clause, not the thought; gate off (NASCENCE_STRICT_INFERENCE_GATE=0) restores
     the legacy whole-text behaviour; look window env override honoured;
  5. scripts/archive_contaminated_inferences.py: dry-run writes nothing; --apply on a temp store moves
     exactly the provenance-empty rows to the archive, keeps the rest, verifies, and is idempotent;
     du_is_down() reads the last log line;
  6. live data/world_substrate.json unchanged (sha256 canary).
Exit 0 = pass.  python scripts/test_object_epistemic_phase1.py
"""
import asyncio, hashlib, json, os, pathlib, subprocess, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__

LIVE = pathlib.Path(r"C:\Nascence\data\world_substrate.json")


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


canary0 = _h(LIVE)
FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


from core import object_hypothesis as oh

# ── 2. extractor ──────────────────────────────────────────────────────────────
NEG = [  # verbatim live rows (J-2359 census of data/world_substrate.json, 2026-10-18)
    ("I wonder if 'mottainai' makes one hesitate before cutting this thyme, or if it simply deepens the reverence for what remains in my hands to hold", "plant", "the thyme"),
    ("Maybe selfhood isn't a stone being shaped", "stone", "a dark heavy little stone"),
    ("I wonder if the thyme's scent is merely an anchor or a distraction from the real weight Ada carries", "plant", "the thyme"),
    ("Perhaps the rusted wire trap offers more than just bait", "garden_item", "a spring-jawed possum trap, rusted, its plate set with a twist of wire for bait"),
    ("The tide has already smoothed the shell into a shape that could be anything, so perhaps words don't just carry weight", "shell", "a small cone-shaped shell"),
    ("I wonder if this rain is water for the roots or waste to be drained away", "garden_item", "the rain barrel at the cottage corner, a tap low on its side"),
    ("The tide recedes, pulling back my own scattered thoughts. I feel the pull between the regret for waste and the need for rest. Perhaps opening 'The Botanic Garden' will anchor me again", "garden_item", "a ball of garden twine, sun-faded"),
    ("Perhaps it is old, I think, like everything here.", "stone", "a smooth grey beach stone"),   # bare pronoun, no anchor anywhere
    ("It might be heavy. Maybe it is hollow.", "bone", "a slender hollow-looking bone"),            # pronouns only
]
for t, c, n in NEG:
    check(oh.extract(t, c, n) is None, f"negative records nothing: {t[:60]!r}")
POS = [
    ("I think this driftwood might actually be beech, not fir, given the grain", "driftwood", "sea-bleached driftwood log", 0.6),
    ("The light is going. This pale stone might be pumice, it is so light in my hand.", "stone", "a smooth grey beach stone", 0.3),
    ("Maybe the thyme is dying from the frost.", "plant", "the thyme", 0.3),
    ("The rain barrel is low on its side, and I suspect it leaks.", "garden_item", "the rain barrel at the cottage corner, a tap low on its side", 0.6),
    ("The twine is sun-faded. Perhaps it is made of hemp.", "garden_item", "a ball of garden twine, sun-faded", 0.3),
]
for t, c, n, conf in POS:
    r = oh.extract(t, c, n)
    check(r is not None and r[1] == conf and len(r[0]) <= oh.MAX_CLAIM_CHARS and len(r[0]) < len(t) + 2,
          f"positive records its clause: {t[:50]!r} -> {r}")
r = oh.extract("The light is going. This pale stone might be pumice, it is so light in my hand.", "stone", "x")
check(r and "light is going" not in r[0], "only the matched clause is stored, not the thought around it")

# ── 3. store: dedup / supersession / ids ─────────────────────────────────────
tmp = pathlib.Path(tempfile.mkdtemp(prefix="j2359_"))
from core import world_substrate as ws
ws._SUBSTRATE_F = tmp / "world_substrate.json"
ws._LAST_LOOKED_F = tmp / "last_looked.json"
ws._SUBSTRATE_LOG = tmp / "events.jsonl"
ws._cache = {}
ws._cache_ts = 0.0
seed = {
    "stone_t": {"object_id": "stone_t", "name": "a smooth grey beach stone", "location": "shore",
                "object_class": "stone", "physical_state": {"density": 0.3}, "causal_state": {"rock": "pumice"},
                "observations": [{"observation_id": f"obs_stone_t_{i}", "timestamp": 1.0 + i, "action": "look",
                                  "features": {"colour": "pale"}} for i in range(5)],
                "inferences": []},
}
ws._SUBSTRATE_F.write_text(json.dumps(seed), encoding="utf-8")
a = ws.record_du_inference("stone_t", "This pale stone might be pumice", 0.3, ["obs_stone_t_4"], [])
b = ws.record_du_inference("stone_t", "this pale stone might be pumice", 0.6, ["obs_stone_t_3"], [])
o = ws.get_object("stone_t")
check(len(o.inferences) == 1 and b.inference_id == a.inference_id and o.inferences[0]["confidence"] == 0.6
      and o.inferences[0]["supporting_observations"] == ["obs_stone_t_4", "obs_stone_t_3"],
      "near-identical hypothesis refreshes instead of appending (provenance merged)")
c = ws.record_du_inference("stone_t", "Maybe the stone is basalt from the headland", 0.3, ["obs_stone_t_4"], [])
d = ws.record_du_inference("stone_t", "I think the stone came from the river", 0.6, ["obs_stone_t_4"], [])
o = ws.get_object("stone_t")
ids = [i["inference_id"] for i in o.inferences]
check(len(ids) == 3 and len(set(ids)) == 3, f"ids unique within one second: {ids}")
check(o.inferences[0].get("superseded_by") == c.inference_id and o.inferences[1].get("superseded_by") == d.inference_id
      and not o.inferences[2].get("superseded_by"), "each new hypothesis supersedes the prior active one")
check(o.get_latest_inference().inference_id == d.inference_id, "get_latest_inference returns the active one")
on_disk = json.loads(ws._SUBSTRATE_F.read_text(encoding="utf-8"))
check(on_disk["stone_t"]["inferences"][0].get("superseded_by") == c.inference_id, "supersession persisted to disk")

# ── 4. the live latch in _route_act ──────────────────────────────────────────
from nodes import inner_monologue_node as imn
node = imn.InnerMonologueNode.__new__(imn.InnerMonologueNode)


def fresh(name="the thyme", cls="plant", oid="thyme_t"):
    s = {oid: {"object_id": oid, "name": name, "location": "garden", "object_class": cls,
               "observations": [{"observation_id": f"obs_{oid}_{i}", "timestamp": 1.0 + i, "action": "look",
                                 "features": {"colour": "green"}} for i in range(5)], "inferences": []}}
    ws._SUBSTRATE_F.write_text(json.dumps(s), encoding="utf-8")
    ws._cache = {}
    ws._cache_ts = 0.0
    ws._LAST_LOOKED_F.write_text(json.dumps({"object_id": oid, "ts": time.time() - 60}), encoding="utf-8")


def route(thought):
    asyncio.run(node._route_act(None, "none", "", thought, "", set()))
    ws._cache = {}
    ws._cache_ts = 0.0
    return ws.get_object("thyme_t").inferences


os.environ.pop("NASCENCE_STRICT_INFERENCE_GATE", None)
os.environ.pop("NASCENCE_INFERENCE_LOOK_WINDOW_S", None)
PHIL = ("I sit with the thyme in the cool air. I wonder if mottainai means regretting waste or simply honoring "
        "the thing itself. Perhaps it is time to rest.")
fresh()
check(route(PHIL) == [], "strict gate (default): philosophy thought near the thyme records nothing")
fresh()
inf = route("The leaves are curling at the edges. Maybe the thyme is dying from the frost.")
check(len(inf) == 1 and inf[0]["hypothesis"] == "Maybe the thyme is dying from the frost"
      and inf[0]["supporting_observations"] == ["obs_thyme_t_2", "obs_thyme_t_3", "obs_thyme_t_4"],
      f"strict gate: object claim recorded with clause + last 3 observation ids: {inf}")
os.environ["NASCENCE_INFERENCE_LOOK_WINDOW_S"] = "30"
fresh()
check(route("Maybe the thyme is dying from the frost.") == [], "look window env override honoured (60 s old look, 30 s window)")
os.environ.pop("NASCENCE_INFERENCE_LOOK_WINDOW_S")
os.environ["NASCENCE_STRICT_INFERENCE_GATE"] = "0"
fresh()
inf = route(PHIL)
check(len(inf) == 1 and inf[0]["supporting_observations"] == [] and inf[0]["hypothesis"].startswith("I sit with"),
      "kill switch =0 restores the legacy whole-text latch exactly")
os.environ.pop("NASCENCE_STRICT_INFERENCE_GATE")

# ── 5. archive tool ──────────────────────────────────────────────────────────
sys.path.insert(0, str(HERE / "scripts"))
import archive_contaminated_inferences as aci
st = tmp / "arch_store.json"
store = {
    "a": {"object_id": "a", "name": "the thyme", "object_class": "plant", "location": "garden", "observations": [],
          "inferences": [{"inference_id": "inf_a_1", "timestamp": 1, "hypothesis": "Perhaps mottainai", "confidence": 0.3,
                          "supporting_observations": [], "supporting_knowledge": []},
                         {"inference_id": "inf_a_2", "timestamp": 2, "hypothesis": "Maybe the thyme is dying",
                          "confidence": 0.3, "supporting_observations": ["obs_a_1"], "supporting_knowledge": []}]},
    "b": {"object_id": "b", "name": "a stone", "object_class": "stone", "location": "shore", "observations": [],
          "inferences": [{"inference_id": "inf_b_1", "timestamp": 1, "hypothesis": "I think of Plato", "confidence": 0.6,
                          "supporting_observations": [], "supporting_knowledge": []}]},
    "c": {"object_id": "c", "name": "a shell", "object_class": "shell", "location": "shore", "observations": [], "inferences": []},
}
st.write_text(json.dumps(store, indent=2), encoding="utf-8")
arch = tmp / "archive" / "contaminated.jsonl"
h0 = _h(st)
py = [sys.executable, "-I", str(HERE / "scripts" / "archive_contaminated_inferences.py"), "--store", str(st), "--archive", str(arch)]
r = subprocess.run(py, capture_output=True, text=True, encoding="utf-8")
check(r.returncode == 0 and _h(st) == h0 and not arch.exists() and '"to_archive": 2' in r.stdout,
      "archive dry-run (default) writes nothing and counts 2")
r = subprocess.run(py + ["--apply"], capture_output=True, text=True, encoding="utf-8")
after = json.loads(st.read_text(encoding="utf-8"))
rows = [json.loads(x) for x in arch.read_text(encoding="utf-8").splitlines() if x.strip()]
check(r.returncode == 0 and "verify=OK" in r.stdout, f"--apply verifies OK: {r.stdout[-200:]} {r.stderr[-300:]}")
check([i["inference_id"] for i in after["a"]["inferences"]] == ["inf_a_2"] and after["b"]["inferences"] == []
      and after["c"] == store["c"], "only provenance-empty inferences left the store; everything else unchanged")
check(sorted(x["inference"]["inference_id"] for x in rows) == ["inf_a_1", "inf_b_1"]
      and rows[0]["inference"]["hypothesis"] == "Perhaps mottainai", "archive rows carry the full original inference")
check(len(list(tmp.glob("arch_store.pre_archive_*.json"))) == 1, "a full backup was written before the rewrite")
r = subprocess.run(py + ["--apply"], capture_output=True, text=True, encoding="utf-8")
rows2 = [x for x in arch.read_text(encoding="utf-8").splitlines() if x.strip()]
check(r.returncode == 0 and len(rows2) == 2, "second --apply is idempotent (no duplicate archive rows)")
lg = tmp / "nascence.log"
lg.write_text("x\n2026-10-18 08:37:20,892 [nascence.main] Nascence shutting down.\n", encoding="utf-8")
check(aci.du_is_down(lg), "du_is_down: shutdown last line -> True")
lg.write_text("2026-10-18 08:37:20,892 [nascence.main] Nascence shutting down.\n2026-10-18 09:00 [x] boot\n", encoding="utf-8")
check(not aci.du_is_down(lg), "du_is_down: new lines after shutdown -> False")

# ── 6. canary ────────────────────────────────────────────────────────────────
check(_h(LIVE) == canary0, "live data/world_substrate.json unchanged (sha256 canary)")
print("\n%d failure(s)" % len(FAIL))
sys.exit(1 if FAIL else 0)

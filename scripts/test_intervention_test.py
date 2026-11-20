"""Test + store report for J-2524 (I-0102, object_epistemic_loop): the intervention_test field.

DECLARED BEFORE LOOKING AT ANY RESULT (no tuning to the outcome):
  - candidates per hypothesis capped at core.object_hypothesis.MAX_INTERVENTION_CANDIDATES (3);
  - a hypothesis "receives a candidate" iff intervention_test() returns >= 1 entry; no score, no threshold;
  - corpus = (a) every inference in the live data/world_substrate.json (read-only), and (b) the clause-scoped
    hypotheses core.object_hypothesis.extract() recovers from the legacy whole-text inferences preserved in
    data/world_substrate.pre_archive_20261018_184006.json (read-only; the J-2359 archive snapshot);
  - the report prints the share and ten examples (hits first, file order), each with its inference id.

Hermetic: lab_env.isolate() (DB_PATH) plus world_substrate's own store paths redirected to a temp dir; core is
imported BEFORE lab_env and asserted to resolve inside this tree. The live store is only opened for reading.
Zero LLM.  Exit 0 = pass.   python scripts/test_intervention_test.py
"""
import asyncio, hashlib, json, os, pathlib, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

LIVE = pathlib.Path(r"C:\Nascence\data\world_substrate.json")
PRE_ARCHIVE = pathlib.Path(r"C:\Nascence\data\world_substrate.pre_archive_20261018_184006.json")
FAIL = []


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def _sig(cands):
    return [(c["mode"], c["family"], c["verb"], c["object"], c.get("when", "")) for c in cands]


canary0 = _h(LIVE)
from core import object_hypothesis as oh
from core import actions as act

with isolate() as _lab:
    # -- 1. extraction ---------------------------------------------------------
    it = oh.intervention_test
    r = it("This pale stone might be pumice", "stone", "a smooth grey beach stone", "shore")
    check(_sig(r) == [("do", "objtest", "scratch", "stone", ""), ("do", "objtest", "heft", "stone", ""),
                      ("do", "objtest", "float", "stone", "")], f"pumice stone -> scratch/heft/float: {_sig(r)}")
    r = it("Maybe the thyme is dying from the frost", "plant", "the thyme", "garden")
    check(_sig(r) == [("withhold", "water", "water", "garden", "two days"),
                      ("observe", "look", "look", "garden", "after rain"),
                      ("observe", "look", "look", "garden", "after a cold night")],
          f"garden thyme dying/frost -> withhold water, look after rain / cold night: {_sig(r)}")
    r = it("Maybe the thyme is dying from the frost", "plant", "the thyme", "shore")
    check(r == [], "location rules fire only where the object lies (thyme not in the garden -> nothing)")
    r = it("The rain barrel is low on its side, and I suspect it leaks", "garden_item",
           "the rain barrel at the cottage corner, a tap low on its side", "garden")
    check(_sig(r) == [("do", "water_fill", "fill", "barrel", "")], f"leaking barrel -> fill the barrel: {_sig(r)}")
    r = it("Maybe that rusted trap is iron", "garden_item",
           "a spring-jawed possum trap, rusted, its plate set with a twist of wire for bait", "garden")
    check(_sig(r) == [("do", "objtest", "scrape", "trap", "")], f"iron trap -> scrape: {_sig(r)}")
    r = it("Perhaps the twine is full", "garden_item", "a ball of garden twine, sun-faded", "garden")
    check(r == [], "contents rule needs a family that reaches the thing (no fill/check family for twine)")
    for t in ("I think the stone came from the river", "Perhaps this stone is old", "Maybe the stone was carried here"):
        check(it(t, "stone", "a smooth grey beach stone", "shore") == [], f"origin/age claim -> empty, never a guess: {t!r}")
    fam = dict(act.families())
    fam.pop("objtest", None)
    check(it("This pale stone might be pumice", "stone", "a smooth grey beach stone", "shore", families=fam) == [],
          "a rule whose family is absent from the registry yields nothing")
    check(it("", "stone", "x") == [] and it("the stone is pumice", "", "") == [], "empty claim / no anchors -> []")
    allc = it("I think this driftwood might be beech and it is waterlogged and rotten", "driftwood", "driftwood log", "shore")
    check(0 < len(allc) <= oh.MAX_INTERVENTION_CANDIDATES, f"capped at {oh.MAX_INTERVENTION_CANDIDATES}: {_sig(allc)}")
    fams = act.families()
    check(all(c["verb"] in fams[c["family"]]["verbs"] for c in allc), "every candidate verb is a real hand-family verb")

    # -- 2. store: optional field ----------------------------------------------
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="j2524_"))
    from core import world_substrate as ws
    ws._SUBSTRATE_F = tmp / "world_substrate.json"
    ws._LAST_LOOKED_F = tmp / "last_looked.json"
    ws._SUBSTRATE_LOG = tmp / "events.jsonl"

    def fresh(oid="thyme_t", name="the thyme", cls="plant", loc="garden"):
        s = {oid: {"object_id": oid, "name": name, "location": loc, "object_class": cls,
                   "observations": [{"observation_id": f"obs_{oid}_{i}", "timestamp": 1.0 + i, "action": "look",
                                     "features": {"colour": "green"}} for i in range(5)], "inferences": []}}
        ws._SUBSTRATE_F.write_text(json.dumps(s), encoding="utf-8")
        ws._cache = {}
        ws._cache_ts = 0.0
        ws._LAST_LOOKED_F.write_text(json.dumps({"object_id": oid, "ts": time.time() - 60}), encoding="utf-8")

    fresh()
    a = ws.record_du_inference("thyme_t", "Maybe the thyme is dying", 0.3, ["obs_thyme_t_4"], [])
    disk = json.loads(ws._SUBSTRATE_F.read_text(encoding="utf-8"))
    check("intervention_test" not in disk["thyme_t"]["inferences"][0] and a.intervention_test is None,
          "no field given -> row carries no intervention_test key (byte-identical to before)")
    cand = [{"mode": "observe", "family": "look", "verb": "look", "object": "garden", "cue": "dying", "when": "after rain"}]
    ws.record_du_inference("thyme_t", "maybe the thyme is dying", 0.6, ["obs_thyme_t_3"], [], intervention_test=cand)
    ws.record_du_inference("thyme_t", "Maybe the thyme is dying", 0.6, ["obs_thyme_t_2"], [])
    disk = json.loads(ws._SUBSTRATE_F.read_text(encoding="utf-8"))
    infs = disk["thyme_t"]["inferences"]
    check(len(infs) == 1 and infs[0].get("intervention_test") == cand,
          "refresh with a derived field stores it; a later refresh with None keeps it")
    ws.record_du_inference("thyme_t", "I think the thyme is overwatered", 0.6, ["obs_thyme_t_4"], [], intervention_test=[])
    disk = json.loads(ws._SUBSTRATE_F.read_text(encoding="utf-8"))
    ws._cache = {}
    ws._cache_ts = 0.0
    check(disk["thyme_t"]["inferences"][-1].get("intervention_test") == [] and
          ws.get_object("thyme_t").get_latest_inference().intervention_test == [],
          "an empty derived list round-trips as [] (derived, no candidate) distinct from absent")

    # -- 3. the gated writer in _route_act -------------------------------------
    from nodes import inner_monologue_node as imn
    node = imn.InnerMonologueNode.__new__(imn.InnerMonologueNode)

    def route(thought):
        asyncio.run(node._route_act(None, "none", "", thought, "", set()))
        ws._cache = {}
        ws._cache_ts = 0.0
        return ws.get_object("thyme_t").inferences

    os.environ.pop("NASCENCE_STRICT_INFERENCE_GATE", None)
    os.environ["NASCENCE_INTERVENTION_TEST"] = "0"   # D-0632 (J-3244): the default is now ON; "0" is the kill switch
    fresh()
    inf = route("The leaves are curling at the edges. Maybe the thyme is dying from the frost.")
    check(len(inf) == 1 and "intervention_test" not in inf[0], "gate forced OFF (=0): recorded hypothesis has no field")
    os.environ["NASCENCE_INTERVENTION_TEST"] = "1"
    fresh()
    inf = route("The leaves are curling at the edges. Maybe the thyme is dying from the frost.")
    check(len(inf) == 1 and _sig(inf[0].get("intervention_test") or []) == [
        ("withhold", "water", "water", "garden", "two days"), ("observe", "look", "look", "garden", "after rain"),
        ("observe", "look", "look", "garden", "after a cold night")],
        f"gate ON: hypothesis carries its intervention_test: {inf[0].get('intervention_test') if inf else None}")
    os.environ.pop("NASCENCE_INTERVENTION_TEST")
    fresh()   # D-0632: unset = default ON
    inf = route("The leaves are curling at the edges. Maybe the thyme is dying from the frost.")
    check(len(inf) == 1 and bool(inf[0].get("intervention_test")), "gate unset (new default): hypothesis carries its field")

# -- 4. report over the existing hypothesis stores (read-only) -----------------
rows = []   # (source, inference_id, object_class, claim, candidates)
live = json.loads(LIVE.read_text(encoding="utf-8"))
for oid, o in live.items():
    for d in o.get("inferences", []):
        rows.append(("live", d.get("inference_id"), o.get("object_class"), d.get("hypothesis", ""),
                     oh.intervention_test(d.get("hypothesis", ""), o.get("object_class", ""),
                                          o.get("name", ""), o.get("location", ""))))
n_legacy = 0
if PRE_ARCHIVE.exists():
    pre = json.loads(PRE_ARCHIVE.read_text(encoding="utf-8"))
    for oid, o in pre.items():
        for d in o.get("inferences", []):
            n_legacy += 1
            cl = oh.extract(d.get("hypothesis", ""), o.get("object_class", ""), o.get("name", ""))
            if cl:
                rows.append(("pre_archive", d.get("inference_id"), o.get("object_class"), cl[0],
                             oh.intervention_test(cl[0], o.get("object_class", ""), o.get("name", ""),
                                                  o.get("location", ""))))
n_live = sum(1 for r in rows if r[0] == "live")
n_clause = sum(1 for r in rows if r[0] == "pre_archive")
hit = [r for r in rows if r[4]]
print(f"\nREPORT live inferences={n_live}  pre_archive legacy inferences={n_legacy} -> clause-scoped hypotheses={n_clause}")
print(f"REPORT hypotheses with >=1 intervention candidate: {len(hit)}/{len(rows)}"
      + (f" ({100.0 * len(hit) / len(rows):.1f}%)" if rows else ""))
for src in ("live", "pre_archive"):
    s = [r for r in rows if r[0] == src]
    print(f"REPORT   {src}: {sum(1 for r in s if r[4])}/{len(s)}")
print("REPORT examples (ten, hits first, file order):")
for r in (hit + [r for r in rows if not r[4]])[:10]:
    print(f"  [{r[0]}] {r[1]} ({r[2]}) {r[3][:110]!r} -> {_sig(r[4])}")

canary1 = _h(LIVE)
print(f"canary live world_substrate.json sha256 before={canary0[:12] if canary0 else None} "
      f"after={canary1[:12] if canary1 else None} (opened read-only here; Du is live and may write it himself)")
print("\nRESULT:", ("FAIL " + str(len(FAIL))) if FAIL else "PASS")
sys.exit(1 if FAIL else 0)

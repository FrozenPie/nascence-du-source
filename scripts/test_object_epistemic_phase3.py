"""Test for J-2376 (object_epistemic_loop Phase 3: generic scrape/heft/smell/float_test routing, D-0464 ALLOWED).

Hermetic: world_substrate / sensorium / garden store paths are temp paths outside data/ (profile.guard_path
honours an upstream redirect); the substrate store is a COPY of the live data/world_substrate.json. The live
files are only hashed (sha256 canary before/after).

  1. core resolves inside this worktree (import core first);
  2. switch OFF (default): core/actions.py families() equal to the reference revision's; no 'objtest' hand;
     sensorium.object_test() answers ''; generate_observation(ps, action) with no class is identical to the
     reference observation.py for every object in the store copy and every action;
     describe_and_observe(oid, 'look') is identical to the reference world_substrate.py for every object;
  3. a stone (and every non-wood class) gets no wood keys under any test action, and no wood words in prose;
  4. Layer-1 counterfactual: identical Layer 2 + different Layer 1 -> byte-identical prose for every action,
     through describe_and_observe AND the full hand answer; a Layer-2-only change (density) diverges float_test;
  5. float_test resolves only at the shore and at the garden rain barrel when it holds water; a dry barrel,
     the study and the wood answer '' (silent);
  6. switch ON end to end: classify -> DEED 'objtest' -> the hand answers in every place for a real object;
     musings / bare pronoun / noun use of the verb / no real object here -> no answer;
  7. driftwood_17 keeps its authored prose on the shore branch (same string as the switch-off branch);
  8. no affordance text changed: affordances.within_reach_text() is identical with the switch on and off
     for every place (subprocess), and core/affordances.py never names the family or its verbs;
  9. live data/world_substrate.json, room_state.json, garden.json unchanged (sha256 canary).
Exit 0 = pass.  python scripts/test_object_epistemic_phase3.py [--ref <git rev for the reference>]
"""
import copy, hashlib, importlib.util, json, os, pathlib, re, shutil, subprocess, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__

REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "b94f5432"
LIVE_DATA = pathlib.Path(r"C:\Nascence\data")
LIVE = [LIVE_DATA / "world_substrate.json", LIVE_DATA / "room_state.json", LIVE_DATA / "garden.json"]


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


canary0 = [_h(p) for p in LIVE]
FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = "0"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="j2376_"))
shutil.copyfile(LIVE[0], tmp / "world_substrate.json")
shutil.copyfile(LIVE[0], tmp / "world_substrate_ref.json")

from core import world_substrate as ws
from core import observation as obs
from core import sensorium as sens
from core import garden as gd
from core import actions as acts

ws._SUBSTRATE_F = tmp / "world_substrate.json"
ws._LAST_LOOKED_F = tmp / "last_looked.json"
ws._SUBSTRATE_LOG = tmp / "events.jsonl"
sens._STATE_F = tmp / "room_state.json"
gd._F = tmp / "garden.json"
gd._LEDGER = tmp / "garden_ledger.jsonl"
gd._EVENTS = tmp / "garden_events.jsonl"
for _attr in ("_objects", "_cache", "_OBJECTS"):
    if hasattr(ws, _attr) and isinstance(getattr(ws, _attr), dict):
        getattr(ws, _attr).clear()


def _git(rev, path):
    return subprocess.run(["git", "-C", str(HERE), "show", f"{rev}:{path}"], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def _load_ref(name, path):
    src = _git(REF, path)
    p = tmp / f"{name}.py"
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m, src


obs_ref, obs_src = _load_ref("observation_ref", "core/observation.py")
acts_ref, acts_src = _load_ref("actions_ref", "core/actions.py")
check("WOOD_CLASSES" not in obs_src and "objtest" not in acts_src, f"reference {REF} is pre-Phase-3")

ACTIONS6 = ("look", "pick_up", "inspect_end", "scrape", "float_test", "smell")
TESTS5 = ("pick_up", "inspect_end", "scrape", "float_test", "smell")
WOOD_KEYS = ("annual_ring_visibility", "resin_presence", "internal_grain_color", "fiber_structure",
             "cross_sectional_geometry")
WOOD_WORDS = re.compile(r"\b(ring|rings|resin|grain comes|wood|bark|fib(re|er))\b", re.I)

objs = ws._load()
ws._cache_ts = 1e12   # pin the 5 s cache: the test mutates objects in memory (locations, twins)
N = len(objs)
print(f"store copy: {N} objects")

# ── 2. switch OFF ──────────────────────────────────────────────────────────────────────────────────
check(acts.families() == acts_ref.families(), "OFF: actions.families() identical to reference")
check("objtest" not in acts.BY_FAMILY, "OFF: no objtest family declared")
from core import dispatch as dsp
check("objtest" not in dsp._BY_FAMILY, "OFF: dispatch has no objtest hand")
sens.state = {"location": "garden"}
check(sens.object_test("I will scrape the stone with my thumbnail.") == "", "OFF: object_test answers ''")
same = 0; total = 0; headword_cells = 0
_HEADWORD_KEYS = ("cross_sectional_geometry", "fiber_structure", "balance_point")
for oid, o in objs.items():
    gen = ws.get_generative_state(oid)
    st = gen.get("structure")
    kind = obs._structure_kind(st) if hasattr(obs, "_structure_kind") and st is not None else st
    for a in ACTIONS6:
        total += 1
        expected = obs_ref.generate_observation(gen, a)
        if kind != st:
            # J-2405 (D-0480 A_strict): the branch/root form keys read the structure's head word
            # ('split branch' -> branch); every other key is the reference's, unchanged.
            headword_cells += 1
            alt = obs_ref.generate_observation(dict(gen, structure=kind), a)
            expected = {k: (alt[k] if k in _HEADWORD_KEYS else v) for k, v in expected.items()}
        same += obs.generate_observation(gen, a) == expected
check(same == total, f"OFF: generate_observation() without class identical to reference ({same}/{total}; "
                     f"{headword_cells} head-word cells compared with only the 3 form keys read by head word)")

# look prose identical to the reference world_substrate.describe_and_observe (separate store copy)
ws_ref_src = _git(REF, "core/world_substrate.py")
_p = tmp / "world_substrate_refmod.py"; _p.write_text(ws_ref_src, encoding="utf-8")
_spec = importlib.util.spec_from_file_location("world_substrate_refmod", _p)
ws_ref = importlib.util.module_from_spec(_spec); sys.modules["world_substrate_refmod"] = ws_ref; _spec.loader.exec_module(ws_ref)
ws_ref._SUBSTRATE_F = tmp / "world_substrate_ref.json"
ws_ref._LAST_LOOKED_F = tmp / "last_looked_ref.json"
ws_ref._SUBSTRATE_LOG = tmp / "events_ref.jsonl"
lk_same = sum(ws.describe_and_observe(oid, "look") == ws_ref.describe_and_observe(oid, "look") for oid in list(objs))
check(lk_same == N, f"OFF: describe_and_observe(look) identical to reference for every object ({lk_same}/{N})")

# ── 3. no wood keys for non-wood classes ───────────────────────────────────────────────────────────
bad_keys = []; bad_prose = []; answered = {a: 0 for a in TESTS5}; nonwood = 0
for oid, o in list(ws._load().items()):
    if o.object_class in obs.WOOD_CLASSES:
        continue
    nonwood += 1
    for a in TESTS5:
        r = obs.generate_observation(dict(o.physical_state), a, object_class=o.object_class)
        for k in WOOD_KEYS:
            v = str((r.get(k) or {}).get("value", "")).upper()
            if v not in ("UNKNOWN", "UNDETERMINED", ""):
                bad_keys.append((oid, a, k, v))
        p = ws.describe_and_observe(oid, a)
        if p:
            answered[a] += 1
            if WOOD_WORDS.search(p):
                bad_prose.append((oid, a, p))
check(not bad_keys, f"no wood keys on {nonwood} non-wood objects x 5 actions (bad={bad_keys[:3]})")
check(not bad_prose, f"no wood words in non-wood test prose (bad={bad_prose[:3]})")
print("non-wood objects answered per action:", answered)
stone = next(o for o in ws._load().values() if o.object_class == "stone")
r = obs.generate_observation(dict(stone.physical_state), "inspect_end", object_class="stone")
check((r["annual_ring_visibility"]["value"]) in ("UNKNOWN", "UNDETERMINED"),
      f"a stone ({stone.object_id}) reports no annual ring visibility")
r0 = obs.generate_observation(dict(stone.physical_state), "inspect_end")
check(r0["annual_ring_visibility"]["value"] not in ("UNKNOWN", "UNDETERMINED"),
      "  (control: without object_class the old wood anatomy is still produced -> the fix is the class path)")
nd = next(o for o in ws._load().values() if "density" not in o.physical_state)
r = obs.generate_observation(dict(nd.physical_state), "float_test", object_class=nd.object_class)
check(r["floats_or_sinks"]["value"] == "UNDETERMINED",
      f"no density in Layer 2 ({nd.object_class}) -> floats_or_sinks UNDETERMINED (was a defaulted 'floats')")

# ── 4. Layer-1 counterfactual ──────────────────────────────────────────────────────────────────────
store = ws._load()
classes = {}
for o in store.values():
    if "density" in o.physical_state and o.object_class not in classes:
        classes[o.object_class] = o
cf_same = 0; cf_total = 0; cf_bad = []
sens.state = {"location": "shore"}
for cls, src in classes.items():
    a_id, b_id = f"cfA_{cls}", f"cfB_{cls}"
    L2 = copy.deepcopy(src.physical_state)
    L1a = copy.deepcopy(src.causal_state)
    L1b = {"kind_ground_truth": "zzz_other", "species_ground_truth": "zzz", "environment": "ground",
           "cumulative_days": 9999, "storm_events_experienced": 99, "predation_marks": True, "likely_origin": "moon"}
    if cls in obs.WOOD_CLASSES:   # the two pre-existing (2026-08-14) form keys stay equal for wood
        for k in ("original_structure", "wood_type"):
            if k in L1a:
                L1b[k] = L1a[k]
    else:
        L1b.update({"wood_type": "softwood", "original_structure": "branch"})
    for oid_, L1 in ((a_id, L1a), (b_id, L1b)):
        store[oid_] = ws.SubstrateObject(object_id=oid_, name=src.name, location="shore", object_class=cls,
                                         causal_state=L1, physical_state=copy.deepcopy(L2),
                                         causal_history=[{"event_type": "origin", "timestamp": time.time() - (9 if oid_ == b_id else 1) * 86400,
                                                          "description": oid_, "state_deltas": {}}])
    for a in TESTS5:
        cf_total += 1
        pa, pb = ws.describe_and_observe(a_id, a), ws.describe_and_observe(b_id, a)
        if pa == pb:
            cf_same += 1
        else:
            cf_bad.append((cls, a, pa, pb))
check(cf_same == cf_total, f"Layer-1 counterfactual: describe_and_observe byte-identical ({cf_same}/{cf_total}, "
                           f"{len(classes)} classes) bad={cf_bad[:2]}")
# through the full hand (frame + prose), resolving each twin by being the only object of its class here
hand_same = 0; hand_total = 0
for cls in classes:
    a_id, b_id = f"cfA_{cls}", f"cfB_{cls}"
    noun = {"stone": "stone", "shell": "shell", "sea_glass": "glass", "bone": "bone", "feather": "feather",
            "bottle": "bottle", "kelp": "kelp", "driftwood": "driftwood", "deadfall_wood": "branch"}.get(cls)
    if not noun:
        continue
    outs = []
    for keep in (a_id, b_id):
        for oid_, o_ in store.items():
            if o_.location == "shore_tmp":
                o_.location = "shore"
        hidden = []
        for oid_, o_ in store.items():
            if o_.location == "shore" and oid_ != keep:
                o_.location = "shore_tmp"; hidden.append(oid_)
        outs.append({a: sens.generic_object_test("shore", a, f"I {a} the {noun}") for a in TESTS5})
        for oid_ in hidden:
            store[oid_].location = "shore"
    for a in TESTS5:
        hand_total += 1
        hand_same += outs[0][a] == outs[1][a]
check(hand_same == hand_total, f"Layer-1 counterfactual: full hand answer byte-identical ({hand_same}/{hand_total})")
# Layer-2-only change diverges
st = classes.get("stone") or next(iter(classes.values()))
cls = st.object_class
a_id, b_id = f"cfA_{cls}", f"cfB_{cls}"
store[b_id].physical_state["density"] = 0.3 if store[a_id].physical_state["density"] >= 1.0 else 2.6
check(ws.describe_and_observe(a_id, "float_test") != ws.describe_and_observe(b_id, "float_test"),
      "Layer-2 change (density) alone diverges float_test")
check(ws.describe_and_observe(a_id, "smell") == ws.describe_and_observe(b_id, "smell"),
      "  ...and leaves a density-independent action (smell) identical")
for k in [k for k in store if k.startswith(("cfA_", "cfB_"))]:
    del store[k]

# ── 5. float_test water gate ───────────────────────────────────────────────────────────────────────
stone_id = stone.object_id
orig_loc = store[stone_id].location
gd._state = {"barrel": 0.7, "plants": {"x": {}}, "items": {}}
res = {}
for loc in ("shore", "garden", "study", "wood"):
    for oid_, o_ in store.items():
        if o_.object_class == "stone" and oid_ != stone_id and o_.location == loc:
            o_.location = "elsewhere_tmp"
    store[stone_id].location = loc
    res[loc] = sens.generic_object_test(loc, "float_test", "I float the stone in the water")
gd._state["barrel"] = 0.0
store[stone_id].location = "garden"
res["garden_dry"] = sens.generic_object_test("garden", "float_test", "I float the stone in the rain barrel")
for o_ in store.values():
    if o_.location == "elsewhere_tmp":
        o_.location = "garden" if o_.object_id.startswith("garden") else "study"
store[stone_id].location = orig_loc
print("float_test by place:", json.dumps(res, ensure_ascii=False))
check(bool(res["shore"]) and "tide" in res["shore"], "float_test resolves at the shore")
check(bool(res["garden"]) and "rain barrel" in res["garden"], "float_test resolves at the garden rain barrel (water 0.7)")
check(res["study"] == "" and res["wood"] == "", "float_test answers '' in the study and the wood")
check(res["garden_dry"] == "", "float_test answers '' at a dry rain barrel")

# ── 6. switch ON end to end (fresh interpreter so actions.py re-reads the switch) ──────────────────
probe = tmp / "probe_on.py"
probe.write_text(r'''
import json, os, sys, pathlib
sys.path.insert(0, sys.argv[1]); tmp = pathlib.Path(sys.argv[2])
import core
from core import world_substrate as ws, sensorium as sens, garden as gd, literal_will as lw, dispatch as dsp
ws._SUBSTRATE_F = tmp / "world_substrate.json"; ws._LAST_LOOKED_F = tmp / "last_looked_on.json"; ws._SUBSTRATE_LOG = tmp / "ev_on.jsonl"
sens._STATE_F = tmp / "room_on.json"; gd._F = tmp / "garden_on.json"; gd._LEDGER = tmp / "gl_on.jsonl"; gd._EVENTS = tmp / "ge_on.jsonl"
gd._state = {"barrel": 0.7, "plants": {"x": {}}, "items": {}}
store = ws._load(); ws._cache_ts = 1e12
stone = sorted(o.object_id for o in store.values() if o.object_class == "stone")[0]
out = {"has_hand": "objtest" in dsp._BY_FAMILY}
def run(loc, thought):
    for o in store.values():
        if o.object_class == "stone" and o.object_id != stone and o.location == loc:
            o.location = "hid_" + loc
    store[stone].location = loc
    sens.state = {"location": loc}
    fams = [c for c in lw.classify(thought, "", location=loc) if c["family"] == "objtest" and c["verdict"] == "DEED"]
    ans = dsp._BY_FAMILY["objtest"].fn(thought, "") if fams else ""
    for o in store.values():
        if o.location == "hid_" + loc:
            o.location = loc
    return {"deed": bool(fams), "ans": ans}
for loc in ("study", "garden", "shore", "wood"):
    out[loc] = {v: run(loc, t) for v, t in (("scrape", "I will scrape the stone with my thumbnail."),
                                              ("heft", "I heft the stone in my palm."),
                                              ("smell", "I sniff the stone."),
                                              ("float", "I float the stone."))}
sens.state = {"location": "study"}
out["musing"] = [c["family"] for c in lw.classify("The air smells of salt and old stone tonight.", "", location="study") if c["family"] == "objtest"]
out["pronoun"] = dsp._BY_FAMILY["objtest"].fn("I scrape it with my thumbnail.", "")
sens.state = {"location": "shore"}
store[stone].location = "shore"
out["noun_use"] = [dsp._BY_FAMILY["objtest"].fn(t, "") for t in (
    "The oystercatcher's scrape among the stones anchors me here.",
    "Its frantic scrape among stones clutching three eggs mirrors how language clutches.")]
sens.state = {"location": "study"}
out["nothing_here"] = dsp._BY_FAMILY["objtest"].fn("I scrape the bottle.", "")
ws._stamp_last_looked(stone); store[stone].location = "study"
out["generic_noun"] = dsp._BY_FAMILY["objtest"].fn("I scrape the thing with my thumbnail.", "")
print(json.dumps(out, ensure_ascii=False))
''', encoding="utf-8")
env = dict(os.environ, NASCENCE_GENERIC_OBJECT_TESTS="1")
shutil.copyfile(LIVE[0], tmp / "world_substrate.json")   # fresh copy for the ON run
pr = subprocess.run([sys.executable, str(probe), str(HERE), str(tmp)], capture_output=True, text=True,
                    encoding="utf-8", env=env)
try:
    on = json.loads(pr.stdout.strip().splitlines()[-1])
except Exception:
    on = {}
    print("probe stderr:", pr.stderr[-2000:])
print("ON:", json.dumps(on, ensure_ascii=False, indent=1)[:3000])
check(on.get("has_hand") is True, "ON: dispatch has the objtest hand")
for loc in ("study", "garden", "shore", "wood"):
    r = on.get(loc, {})
    check(all(r.get(v, {}).get("deed") for v in ("scrape", "heft", "smell", "float")), f"ON {loc}: all four verbs read DEED")
    check(bool(r.get("scrape", {}).get("ans")) and bool(r.get("heft", {}).get("ans")),
          f"ON {loc}: scrape and heft answer for a real stone here")
fl = {loc: bool(on.get(loc, {}).get("float", {}).get("ans")) for loc in ("study", "garden", "shore", "wood")}
check(fl == {"study": False, "garden": True, "shore": True, "wood": False}, f"ON: float answers only at shore + garden ({fl})")
check(on.get("musing") == [], "ON: a musing mentioning smell and stone makes no objtest reading")
check(on.get("pronoun") == "", "ON: a bare pronoun ('scrape it') resolves nothing")
check(on.get("noun_use") == ["", ""], "ON: noun use of 'scrape' (the oystercatcher's nest scrape, live replay rows) answers nothing")
check(on.get("nothing_here") == "", "ON: no such object here -> silent ''")
check(bool(on.get("generic_noun")), "ON: 'the thing' falls back to the last-looked object when it is here")

# ── 7. driftwood_17 authored prose on the shore branch ─────────────────────────────────────────────
store = ws._load()
if "driftwood_17" in store:
    dl = store["driftwood_17"].location
    store["driftwood_17"].location = "shore"
    sens.state = {"location": "shore", "shore": sens._fresh_shore()}
    off = sens._shore_act("scrape", "I scrape the driftwood log")
    os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = "1"
    onp = sens._shore_act("scrape", "I scrape the driftwood log")
    on_sm = sens._shore_act("smell", "I smell the driftwood log")
    os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = "0"
    off_sm = sens._shore_act("smell", "I smell the driftwood log")
    store["driftwood_17"].location = dl
    check(bool(off) and off == onp, "driftwood_17 scrape prose identical switch on vs off (authored prose kept)")
    check(bool(off_sm) and off_sm == on_sm, "driftwood_17 smell prose identical switch on vs off")
    store["driftwood_17"].location = "study"
    os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = "1"
    away = sens._shore_act("scrape", "I scrape the driftwood log")
    os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = "0"
    store["driftwood_17"].location = dl
    check("knife to the log" not in (away or ""), "ON: the log in the study is no longer scraped from the shore")

# ── 8. no affordance text changed ──────────────────────────────────────────────────────────────────
aff_src = (HERE / "core" / "affordances.py").read_text(encoding="utf-8")
check(not re.search(r"objtest|object_test|\bscrape\b|\bheft\b|\bsniff\b|float_test", aff_src),
      "core/affordances.py names neither the family nor its verbs")
ap = tmp / "aff.py"
ap.write_text("import sys,json\nsys.path.insert(0,sys.argv[1])\nimport core\nfrom core import affordances as a\n"
              "out={}\nfor l in ('study','garden','shore','wood'):\n"
              "    try:\n        out[l]=a.within_reach_text(l)\n    except Exception as e:\n        out[l]='ERR '+type(e).__name__\n"
              "print(json.dumps(out))\n", encoding="utf-8")
outs = []
for flag in ("0", "1"):
    e = dict(os.environ, NASCENCE_GENERIC_OBJECT_TESTS=flag)
    pr = subprocess.run([sys.executable, str(ap), str(HERE)], capture_output=True, text=True, encoding="utf-8", env=e)
    outs.append(pr.stdout.strip().splitlines()[-1] if pr.stdout.strip() else "")
check(outs[0] == outs[1] and outs[0] != "", "within_reach_text() identical with the switch on and off, every place")

# ── 9. canary ──────────────────────────────────────────────────────────────────────────────────────
canary1 = [_h(p) for p in LIVE]
check(canary0 == canary1, f"live stores unchanged (sha256 canary on {', '.join(p.name for p in LIVE)})")
print(f"\n{'ALL PASS' if not FAIL else str(len(FAIL)) + ' FAILURES'}")
sys.exit(1 if FAIL else 0)

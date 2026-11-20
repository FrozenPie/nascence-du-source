"""J-2390 (object_epistemic_loop, F-3092): analysis probe, NOT a fix.

core/observation.py tests physical_state structure == 'branch' / != 'root', but CLASS_PRIORS['driftwood']
['structure'] spawns 'trunk section' / 'large limb' / 'root mass' / 'split branch' -- never equal. This
probe shows, on a COPY of data/world_substrate.json, the exact prose and the recorded Layer-3 features for
every wood-class object x 6 actions under:
  current   -- observation.py as it is in this tree;
  A_strict  -- observation.py classifies structure by its head word: a token 'root' -> root, a token
               'branch' -> branch (underscores read as spaces), anything else unchanged;
  A_limb    -- A_strict, plus 'limb' counted as a branch;
  B_spawn   -- priors normalised to the observation vocabulary (new spawns only): existing objects keep
               their stored value, so their prose is 'current'; shown here is what a NEW spawn of each
               old prior value would read under B's mapping (look's shape line changes too).
Never writes the live store (sha256 canary). Run: python scripts/probe_driftwood_structure_J-2390.py <copy.json>
"""
import copy, hashlib, importlib.util, json, os, pathlib, re, shutil, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__

LIVE = pathlib.Path(r"C:\Nascence\data\world_substrate.json")
SRC = pathlib.Path(sys.argv[1])
_h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
canary0 = _h(LIVE)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="j2390_"))
ACTIONS6 = ("look", "pick_up", "inspect_end", "scrape", "float_test", "smell")

OBS_SRC = (HERE / "core" / "observation.py").read_text(encoding="utf-8")
HELPER = '''

def _structure_kind(v):
    """J-2390 probe variant: the head word of a structure value ('split branch' -> 'branch')."""
    toks = str(v or "").lower().replace("_", " ").split()
    if "root" in toks:
        return "root"
    if "branch" in toks%s:
        return "branch"
    return str(v)
'''


def variant_src(limb: bool) -> str:
    s = OBS_SRC.replace('physical_state.get("structure") == "branch"',
                        '_structure_kind(physical_state.get("structure")) == "branch"')
    s = s.replace('physical_state.get("structure") != "root"',
                  '_structure_kind(physical_state.get("structure")) != "root"')
    assert s.count("_structure_kind(") == 4, s.count("_structure_kind(")
    return s + HELPER % (' or "limb" in toks' if limb else "")


def load(name, src):
    p = tmp / f"{name}.py"
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OBS = {"current": load("obs_cur_j2390", OBS_SRC), "A_strict": load("obs_as_j2390", variant_src(False)),
       "A_limb": load("obs_al_j2390", variant_src(True))}


def ws_on(store_name):
    shutil.copyfile(SRC, tmp / f"{store_name}.json")
    spec = importlib.util.spec_from_file_location(f"ws_{store_name}", HERE / "core" / "world_substrate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"ws_{store_name}"] = m
    spec.loader.exec_module(m)
    m._SUBSTRATE_F = tmp / f"{store_name}.json"
    m._LAST_LOOKED_F = tmp / f"{store_name}_last_looked.json"
    m._SUBSTRATE_LOG = tmp / f"{store_name}_events.jsonl"
    m._cache = {}
    m._cache_ts = 0.0
    m._load()
    m._cache_ts = 1e12
    return m


def run(variant, ws, oid):
    core.observation = OBS[variant]
    sys.modules["core.observation"] = OBS[variant]
    out = {}
    for a in ACTIONS6:
        obj = ws.get_object(oid)
        n0 = len(obj.observations)
        prose = ws.describe_and_observe(oid, a)
        obj = ws.get_object(oid)
        feats = obj.observations[-1].get("features") if len(obj.observations) > n0 else {}
        out[a] = (prose, feats)
    return out


os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = "0"
orig_obs = sys.modules.get("core.observation")
base = ws_on("base")
WOOD = [i for i, o in sorted(base._load().items()) if o.object_class in ("driftwood", "deadfall_wood", "tree")]
res = {}
for v in OBS:
    ws = ws_on(v)
    res[v] = {oid: run(v, ws, oid) for oid in WOOD}

report = {"objects": {}, "diff_counts": {}}
for oid in WOOD:
    o = base.get_object(oid)
    report["objects"][oid] = {"class": o.object_class, "location": o.location,
                              "structure_L1": o.causal_state.get("original_structure"),
                              "structure_L2": o.physical_state.get("structure"),
                              "look_observations": sum(1 for x in o.observations if x.get("action") == "look"),
                              "other_observations": sum(1 for x in o.observations if x.get("action") != "look")}
    print(f"\n=== {oid} ({o.object_class}, {o.location}) structure L1={o.causal_state.get('original_structure')!r}"
          f" L2={o.physical_state.get('structure')!r} observations={len(o.observations)}")
    for a in ACTIONS6:
        cur = res["current"][oid][a]
        print(f"  [{a}] current : {cur[0]!r}")
        for v in ("A_strict", "A_limb"):
            alt = res[v][oid][a]
            report["diff_counts"].setdefault(v, {"prose": 0, "features": 0})
            if alt[0] != cur[0]:
                report["diff_counts"][v]["prose"] += 1
                print(f"  [{a}] {v:8s}: {alt[0]!r}")
            if alt[1] != cur[1]:
                report["diff_counts"][v]["features"] += 1
                ch = {k: (cur[1].get(k), alt[1].get(k)) for k in set(cur[1]) | set(alt[1]) if cur[1].get(k) != alt[1].get(k)}
                print(f"  [{a}] {v:8s} recorded features: {ch}")

# B_spawn: what a NEW spawn would read if the prior value were already the observation word.
B_MAP = {"trunk section": "trunk section", "large limb": "branch", "root mass": "root", "split branch": "branch"}
print("\n=== B_spawn (priors normalised; existing objects unchanged): look 'shape' and inspect_end geometry")
for old, new in B_MAP.items():
    ps = {"structure": old, "wood_type": "hardwood", "edge_rounding": 0.6}
    for label, val in (("old", old), ("B", new)):
        ps["structure"] = val
        lk = OBS["current"].generate_observation(ps, "look")["shape"]["value"]
        ie = OBS["current"].generate_observation(ps, "inspect_end")
        pu = OBS["current"].generate_observation(ps, "pick_up")["balance_point"]["value"]
        print(f"  {old!r:16s} {label:3s}: shape={lk!r} section={ie['cross_sectional_geometry']['value']!r}"
              f" fibre={ie['fiber_structure']['value']!r} balance={pu!r}")

if orig_obs is not None:
    sys.modules["core.observation"] = orig_obs
    core.observation = orig_obs
canary1 = _h(LIVE)
report["live_store_unchanged"] = canary0 == canary1
print("\n" + json.dumps(report, indent=1))
sys.exit(0 if canary0 == canary1 else 1)

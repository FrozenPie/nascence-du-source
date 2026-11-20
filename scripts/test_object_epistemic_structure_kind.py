"""Test for J-2405 (object_epistemic_loop, D-0480 A_strict, F-3092/F-3096): head-word structure match.

core/observation.py's branch/root form tests now read the head word of the structure value
(_structure_kind): a token 'branch' -> branch, a token 'root' -> root, underscores read as spaces;
'large limb' / 'trunk section' stay as they were. Hermetic: stores are temp COPIES of the live
data/world_substrate.json, the live file is only hashed. Reference = core/observation.py at --ref
(default 134dfd52, pre-J-2405), loaded as a separate module.

  1. core resolves inside this worktree (import core first); the reference predates the change;
  2. _structure_kind table (branch / split branch / split_branch / root mass / large limb / trunk section /
     rootstock / None / '');
  3. generate_observation, every action, reference vs new: exact 'branch' / 'root' / 'large limb' /
     'trunk section' / missing structure byte-identical; 'split branch' / 'split_branch' -> round section +
     straight fibre; 'root mass' -> uneven balance; look 'shape' identical for every value;
  4. every object x 6 actions through describe_and_observe on a store copy, reference vs new, with
     NASCENCE_GENERIC_OBJECT_TESTS 0 and 1: a cell may differ only on a wood object whose structure head
     word changed, only in cross_sectional_geometry / fiber_structure / balance_point, and prose only on
     inspect_end; on today's store that is exactly shore_driftwood_ec5091 (1 prose line, 2 feature sets);
  5. live data/world_substrate.json unchanged (sha256 canary).
Exit 0 = pass.  python scripts/test_object_epistemic_structure_kind.py [--ref <git rev>]
"""
import hashlib, importlib.util, os, pathlib, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__
import core.observation as NEW
assert str(pathlib.Path(NEW.__file__).resolve()).lower().startswith(str(HERE).lower()), NEW.__file__

REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "134dfd52"
LIVE = pathlib.Path(r"C:\Nascence\data\world_substrate.json")


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


canary0 = _h(LIVE)
FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


tmp = pathlib.Path(tempfile.mkdtemp(prefix="j2405_"))
ref_src = subprocess.run(["git", "-C", str(HERE), "show", f"{REF}:core/observation.py"], capture_output=True,
                         text=True, encoding="utf-8", check=True).stdout
check("_structure_kind" not in ref_src, f"1. reference observation.py at {REF} predates the head-word match")
(tmp / "obs_ref_j2405.py").write_text(ref_src, encoding="utf-8")
spec = importlib.util.spec_from_file_location("obs_ref_j2405", tmp / "obs_ref_j2405.py")
REFM = importlib.util.module_from_spec(spec)
sys.modules["obs_ref_j2405"] = REFM
spec.loader.exec_module(REFM)

# -- 2. table ------------------------------------------------------------------------------------------
TABLE = {"branch": "branch", "split branch": "branch", "split_branch": "branch", "Split Branch": "branch",
         "root": "root", "root mass": "root", "root_mass": "root", "large limb": "large limb",
         "trunk section": "trunk section", "trunk_section": "trunk_section", "rootstock": "rootstock",
         None: "None", "": ""}
bad = {k: NEW._structure_kind(k) for k, v in TABLE.items() if NEW._structure_kind(k) != v}
check(not bad, f"2. _structure_kind table ({len(TABLE)} values) {bad or ''}")

# -- 3. generate_observation on synthetic states -------------------------------------------------------
ACT = ("look", "pick_up", "inspect_end", "scrape", "float_test", "smell")
base = {"wood_type": "hardwood", "edge_rounding": 0.6, "density": 0.55, "diameter_cm": 8.0, "bleaching": 0.4,
        "surface_roughness": 0.3, "moisture": 0.2, "salt_accumulation": 0.4}
for v in ("branch", "root", "large limb", "trunk section", "trunk_section", None):
    ps = dict(base, **({"structure": v} if v is not None else {}))
    for cls in ("", "driftwood"):
        diff = [a for a in ACT if REFM.generate_observation(ps, a, object_class=cls)
                != NEW.generate_observation(ps, a, object_class=cls)]
        check(not diff, f"3. structure={v!r} class={cls!r}: all 6 actions identical to reference {diff or ''}")
for v in ("split branch", "split_branch", "root mass"):
    ps = dict(base, structure=v)
    r = {a: REFM.generate_observation(ps, a) for a in ACT}
    n = {a: NEW.generate_observation(ps, a) for a in ACT}
    check(r["look"] == n["look"], f"3. structure={v!r}: look identical (shape word {n['look']['shape']['value']!r})")
    if "branch" in v:
        check(n["inspect_end"]["cross_sectional_geometry"]["value"] == "round"
              and n["inspect_end"]["fiber_structure"]["value"] == "straight"
              and n["scrape"]["fiber_structure"]["value"] == "straight"
              and r["inspect_end"]["cross_sectional_geometry"]["value"] == "irregular",
              f"3. structure={v!r}: section irregular->round, fibre interlocked->straight")
        check(n["pick_up"] == r["pick_up"], f"3. structure={v!r}: pick_up unchanged (balance centered)")
    else:
        check(n["pick_up"]["balance_point"]["value"] == "uneven"
              and r["pick_up"]["balance_point"]["value"] == "centered",
              f"3. structure={v!r}: balance centered->uneven")
        check(n["inspect_end"] == r["inspect_end"] and n["scrape"] == r["scrape"],
              f"3. structure={v!r}: inspect_end/scrape unchanged")

# -- 4. whole store copy, reference vs new -------------------------------------------------------------
ALLOWED_KEYS = {"cross_sectional_geometry", "fiber_structure", "balance_point"}


def run_store(module, name, generic):
    os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = generic
    core.observation = module
    sys.modules["core.observation"] = module
    shutil.copyfile(LIVE, tmp / f"{name}.json")
    sp = importlib.util.spec_from_file_location(f"ws_{name}", HERE / "core" / "world_substrate.py")
    m = importlib.util.module_from_spec(sp)
    sys.modules[f"ws_{name}"] = m
    sp.loader.exec_module(m)
    m._SUBSTRATE_F = tmp / f"{name}.json"
    m._LAST_LOOKED_F = tmp / f"{name}_ll.json"
    m._SUBSTRATE_LOG = tmp / f"{name}_ev.jsonl"
    m._cache = {}
    m._cache_ts = 0.0
    m._load()
    m._cache_ts = 1e12
    out, info = {}, {}
    for oid in sorted(m._load()):
        o = m.get_object(oid)
        st = (o.physical_state or {}).get("structure") or (o.causal_state or {}).get("original_structure")
        info[oid] = (o.object_class, st)
        for a in ACT:
            n0 = len(m.get_object(oid).observations)
            prose = m.describe_and_observe(oid, a)
            ob = m.get_object(oid)
            out[(oid, a)] = (prose, ob.observations[-1].get("features") if len(ob.observations) > n0 else {})
    return out, info


for generic in ("0", "1"):
    R, info = run_store(REFM, f"ref_g{generic}", generic)
    N, _ = run_store(NEW, f"new_g{generic}", generic)
    core.observation = NEW
    sys.modules["core.observation"] = NEW
    changed_objs = {oid for oid, (cls, st) in info.items()
                    if cls in ("driftwood", "deadfall_wood", "tree") and st is not None
                    and NEW._structure_kind(st) != str(st)}
    prose_diff = [k for k in R if R[k][0] != N[k][0]]
    feat_diff = [k for k in R if R[k][1] != N[k][1]]
    bad_cells = [k for k in prose_diff if k[0] not in changed_objs or k[1] != "inspect_end"]
    bad_cells += [k for k in feat_diff if k[0] not in changed_objs or
                  {f for f in set(R[k][1]) | set(N[k][1]) if R[k][1].get(f) != N[k][1].get(f)} - ALLOWED_KEYS]
    print(f"   GENERIC={generic}: cells {len(R)}, prose identical {len(R) - len(prose_diff)}/{len(R)}, "
          f"features identical {len(R) - len(feat_diff)}/{len(R)}, "
          f"head-word-changed wood objects {sorted(changed_objs)}")
    check(not bad_cells, f"4. GENERIC={generic}: every differing cell is a head-word-changed wood object's "
                         f"structure key / inspect_end prose {bad_cells[:5] or ''}")
    ec = "shore_driftwood_ec5091"
    if ec in info and info[ec][1] == "split branch" and changed_objs == {ec}:
        k = (ec, "inspect_end")
        check(prose_diff == [k] and R[k][0].startswith(" The section irregular;")
              and N[k][0] == R[k][0].replace("The section irregular;", "The section round;", 1),
              f"4. GENERIC={generic}: exactly one prose line changes, ec5091 inspect_end irregular -> round")
        check(sorted(feat_diff) == [(ec, "inspect_end"), (ec, "scrape")],
              f"4. GENERIC={generic}: exactly 2 recorded feature sets change (ec5091 inspect_end, scrape)")
    else:
        print(f"   note: store no longer matches F-3096's shape (ec5091={info.get(ec)}, "
              f"changed={sorted(changed_objs)}); exact-line checks skipped, generic cell checks still apply")

# -- 5. canary -----------------------------------------------------------------------------------------
check(_h(LIVE) == canary0, "5. live data/world_substrate.json unchanged (sha256 canary)")
shutil.rmtree(tmp, ignore_errors=True)
print(f"\n{'ALL PASS' if not FAIL else str(len(FAIL)) + ' FAIL'}")
sys.exit(1 if FAIL else 0)

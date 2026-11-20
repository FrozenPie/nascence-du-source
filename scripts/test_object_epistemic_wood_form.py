"""Test for J-2388 (object_epistemic_loop, F-3087) + J-2411 (D-0479 part 2): driftwood's two form keys are
Layer-2 facts, and since J-2411 get_generative_state() reads physical_state ONLY (Layer-1 fallback removed).

Hermetic: every store is a temp COPY; the live files are only hashed (sha256 canary before/after).
  --store       the MIGRATED store to copy (default the live data/world_substrate.json, migrated 2026-10-18)
  --unmigrated  the pre-migration store to copy (default data/world_substrate.pre_formkeys_20261018_184006.json,
                the apply's own backup)
  --ref         pre-J-2388 core/world_substrate.py (default 83d4dc9b)
  --ref2        the J-2388 Layer-1-fallback core/world_substrate.py (default f3af5523, pre-J-2411)

  1. core resolves inside this worktree (import core first);
  2. scripts/migrate_wood_form_keys.py: dry-run writes nothing (copy hash unchanged), --apply on a temp copy
     copies exactly the planned keys, verify=OK, causal_state untouched, second run is a no-op;
  2b. applying the migration to the unmigrated copy reproduces the --store physical_state for every object;
  3. byte-identical prose, for EVERY object x 6 actions through describe_and_observe:
       pre-J-2388 code on the unmigrated copy == J-2388 fallback code on the migrated copy
                                               == new (J-2411) code on the migrated copy;
     and get_generative_state() identical for every object on all three;
  4. driftwood_17's authored prose (sensorium._driftwood17_prose) identical, reference vs migrated;
  5. structural: the new get_generative_state() has no causal_state read and no _LEGACY_FORM_READS counter;
     on the UNMIGRATED copy it reads "unknown" for exactly the objects the migration had to reach
     (control: the migration is load-bearing, nothing silently falls back);
  6. Layer-1 counterfactual for WOOD (what J-2376 had to hold equal): on the migrated copy, changing
     causal_state original_structure / wood_type (and every other Layer-1 key) leaves every wood object's
     prose byte-identical for all 6 actions; an INJECTED Layer-1 form key (on every object, incl. one with no
     Layer-2 key) no longer reaches prose or generative state (J-2411: was the documented residual);
     control: changing physical_state wood_type diverges smell;
  7. spawn_object mirrors the form keys into physical_state (driftwood), equal to causal_state, and every
     other spawned value equals the reference spawn of the same (class, seed);
  8. live data/world_substrate.json unchanged (sha256 canary).
Exit 0 = pass.  python scripts/test_object_epistemic_wood_form.py [--store P] [--unmigrated P] [--ref R] [--ref2 R]
"""
import copy, hashlib, importlib.util, inspect, json, os, pathlib, shutil, subprocess, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__

def _arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


REF = _arg("--ref", "83d4dc9b")
REF2 = _arg("--ref2", "f3af5523")
LIVE = pathlib.Path(r"C:\Nascence\data\world_substrate.json")
STORE = pathlib.Path(_arg("--store", str(LIVE)))
UNMIG = pathlib.Path(_arg("--unmigrated", r"C:\Nascence\data\world_substrate.pre_formkeys_20261018_184006.json"))


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


canary0 = _h(LIVE)
src0 = (_h(STORE), _h(UNMIG))
FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


os.environ["NASCENCE_GENERIC_OBJECT_TESTS"] = "0"
tmp = pathlib.Path(tempfile.mkdtemp(prefix="j2388_"))
for n in ("A_ref", "A2_ref", "B_new_unmig", "U_mig_check"):
    shutil.copyfile(UNMIG, tmp / f"{n}.json")
for n in ("C_new_mig", "R2_fallback_mig", "D_cf"):
    shutil.copyfile(STORE, tmp / f"{n}.json")
print(f"migrated source {STORE} sha256 {src0[0][:8]}; unmigrated source {UNMIG} sha256 {src0[1][:8]}")

# ── 2. migration script ────────────────────────────────────────────────────────────────────────────
MIG = HERE / "scripts" / "migrate_wood_form_keys.py"
U = tmp / "U_mig_check.json"
c0 = _h(U)
r = subprocess.run([sys.executable, str(MIG), "--store", str(U)], capture_output=True, text=True, encoding="utf-8")
dry = json.loads(r.stdout[:r.stdout.rindex("}") + 1])
check(r.returncode == 0 and _h(U) == c0 and dry["copies_planned"] > 0, f"dry-run on the unmigrated copy writes nothing "
      f"({dry['copies_planned']} copies planned on {dry['objects_touched']} objects, conflicts {len(dry['conflicts'])})")
r = subprocess.run([sys.executable, str(MIG), "--store", str(U), "--apply"], capture_output=True, text=True, encoding="utf-8")
check(r.returncode == 0 and "verify=OK" in r.stdout, "--apply on the temp copy: verify=OK " + r.stdout.strip().splitlines()[-1])
before = json.loads((tmp / "A_ref.json").read_text(encoding="utf-8"))
after = json.loads(U.read_text(encoding="utf-8"))
check(all(before[k]["causal_state"] == after[k]["causal_state"] for k in before), "causal_state of every object unchanged")
added = {(k, pk) for k in before for pk in after[k]["physical_state"] if pk not in before[k]["physical_state"]}
check(added == {(c["object_id"], c["key"]) for c in dry["copies"]}, f"exactly the planned keys added ({len(added)})")
r2 = subprocess.run([sys.executable, str(MIG), "--store", str(U)], capture_output=True, text=True, encoding="utf-8")
dry2 = json.loads(r2.stdout[:r2.stdout.rindex("}") + 1])
check(dry2["copies_planned"] == 0 and dry2["already_layer2"] >= dry["copies_planned"], "second run is a no-op (idempotent)")
for b in tmp.glob("U_mig_check.pre_formkeys_*.json"):
    check(_h(b) == c0, "backup equals the pre-apply copy")
mig = json.loads((tmp / "C_new_mig.json").read_text(encoding="utf-8"))
check(set(mig) == set(after) and all(mig[k]["physical_state"] == after[k]["physical_state"] for k in mig),
      f"2b. migrating the unmigrated copy reproduces the --store physical_state for all {len(mig)} objects")
r3 = subprocess.run([sys.executable, str(MIG), "--store", str(tmp / "D_cf.json")], capture_output=True, text=True,
                    encoding="utf-8")
dry3 = json.loads(r3.stdout[:r3.stdout.rindex("}") + 1])
check(dry3["copies_planned"] == 0 and not dry3["conflicts"], f"--store is already migrated (0 copies planned, "
      f"{dry3['already_layer2']} keys already Layer-2)")


# ── modules ────────────────────────────────────────────────────────────────────────────────────────
def _git(rev, path):
    return subprocess.run(["git", "-C", str(HERE), "show", f"{rev}:{path}"], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def _mod(name, src_path=None, src=None):
    p = tmp / f"{name}.py"
    p.write_text(src if src is not None else pathlib.Path(src_path).read_text(encoding="utf-8"), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _point(m, store):
    m._SUBSTRATE_F = tmp / f"{store}.json"
    m._LAST_LOOKED_F = tmp / f"{store}_last_looked.json"
    m._SUBSTRATE_LOG = tmp / f"{store}_events.jsonl"
    m._cache = {}
    m._cache_ts = 0.0
    m._load()
    m._cache_ts = 1e12
    return m


ref_src = _git(REF, "core/world_substrate.py")
check("_FORM_KEYS" not in ref_src, f"reference {REF} is pre-J-2388")
ref2_src = _git(REF2, "core/world_substrate.py")
check("_LEGACY_FORM_READS" in ref2_src, f"reference {REF2} is the J-2388 Layer-1-fallback code")
ws_ref = _point(_mod("ws_ref_j2388", src=ref_src), "A_ref")
ws_R2 = _point(_mod("ws_ref2_j2411", src=ref2_src), "R2_fallback_mig")
ws_B = _point(_mod("ws_newB_j2388", HERE / "core" / "world_substrate.py"), "B_new_unmig")
ws_C = _point(_mod("ws_newC_j2388", HERE / "core" / "world_substrate.py"), "C_new_mig")
from core import observation as obs

ACTIONS6 = ("look", "pick_up", "inspect_end", "scrape", "float_test", "smell")
ids = sorted(ws_ref._load())
WOOD = [i for i in ids if ws_ref._load()[i].object_class in obs.WOOD_CLASSES]
print(f"store copy: {len(ids)} objects, wood classes: {len(WOOD)} {WOOD}")

# ── 3. byte-identical prose / generative state ─────────────────────────────────────────────────────
g_same = sum(ws_ref.get_generative_state(i) == ws_R2.get_generative_state(i) == ws_C.get_generative_state(i) for i in ids)
check(g_same == len(ids), f"get_generative_state identical pre-J-2388/unmigrated, J-2388-fallback/migrated, "
                          f"J-2411/migrated ({g_same}/{len(ids)})")
tot = same = 0; bad = []; wood_answers = 0
for i in ids:
    for a in ACTIONS6:
        pa, pb, pc = ws_ref.describe_and_observe(i, a), ws_R2.describe_and_observe(i, a), ws_C.describe_and_observe(i, a)
        tot += 1
        if pa == pb == pc:
            same += 1
            wood_answers += bool(pa) and i in WOOD
        else:
            bad.append((i, a, pa, pb, pc))
check(same == tot, f"describe_and_observe byte-identical for every object x 6 actions, all three ({same}/{tot}) bad={bad[:2]}")
print(f"  non-empty wood prose among them: {wood_answers}")
for i in WOOD:
    print("  ", i, "|", ws_C.describe_and_observe(i, "look"), "|", ws_C.describe_and_observe(i, "smell"))

# ── 5. structural: no Layer-1 read left in get_generative_state ───────────────────────────────────
gbody = "\n".join(l.split("#")[0] for l in inspect.getsource(ws_C.get_generative_state).split('"""')[-1].splitlines())
check("causal_state" not in gbody and not hasattr(ws_C, "_LEGACY_FORM_READS"),
      "get_generative_state() body reads no causal_state; _LEGACY_FORM_READS counter is gone")
unmig_diff = sorted(i for i in ids if ws_B.get_generative_state(i) != ws_C.get_generative_state(i))
migrated_objs = sorted({c["object_id"] for c in dry["copies"]})
unk = all(ws_B.get_generative_state(i)[k] == "unknown" for i in unmig_diff for k in ("structure", "wood_type")
          if k not in ws_B._load()[i].physical_state)
check(unmig_diff == migrated_objs and unk, f"  (control: on the UNMIGRATED copy the new code reads 'unknown' for exactly "
      f"the {len(migrated_objs)} objects the migration reached {migrated_objs}, no silent fallback)")


# ── 4. driftwood_17 authored prose through sensorium ───────────────────────────────────────────────
from core import world_substrate as ws_core
from core import sensorium as sens
sens._STATE_F = tmp / "room_state.json"
D17 = ("scrape", "inspect_end", "smell", "pick_up", "inspect", "whittle")
_orig = ws_core.get_generative_state
_point(ws_core, "A2_ref")
ws_core.get_generative_state = ws_ref.get_generative_state
p_ref = [sens._driftwood17_prose(a) for a in D17]
ws_core.get_generative_state = _orig
shutil.copyfile(tmp / "C_new_mig.json", tmp / "C2_new_mig.json")
_point(ws_core, "C2_new_mig")
p_new = [sens._driftwood17_prose(a) for a in D17]
check(p_ref == p_new and any(p_ref), f"driftwood_17 authored prose identical ({sum(map(bool, p_ref))} non-empty of {len(D17)})")

# ── 6. Layer-1 counterfactual for wood on the migrated copy ────────────────────────────────────────
shutil.copyfile(tmp / "C_new_mig.json", tmp / "D_cf.json")
ws_D = _point(_mod("ws_newD_j2388", HERE / "core" / "world_substrate.py"), "D_cf")
flip = {"hardwood": "softwood", "softwood": "hardwood"}
cf_tot = cf_same = 0; cf_bad = []
for i in WOOD:
    oC, oD = ws_C._load()[i], ws_D._load()[i]
    L1 = {"kind_ground_truth": "zzz", "species_ground_truth": "zzz", "environment": "moon",
          "cumulative_days": 9999, "storm_events_experienced": 99, "likely_origin": "moon"}
    # the two form keys are flipped wherever the object carries them (its own class shape); an object whose
    # class never had them (deadfall_wood: no structure/wood_type priors) keeps them absent -- see the
    # residual check below for what an INJECTED Layer-1 key on such an object still does.
    if "original_structure" in oC.causal_state:
        L1["original_structure"] = "root" if oC.causal_state["original_structure"] != "root" else "branch"
    if "wood_type" in oC.causal_state:
        L1["wood_type"] = flip.get(oC.causal_state["wood_type"], "softwood")
    oD.causal_state = L1
    for a in ACTIONS6:
        cf_tot += 1
        pc, pd = ws_C.describe_and_observe(i, a), ws_D.describe_and_observe(i, a)
        cf_same += pc == pd
        if pc != pd:
            cf_bad.append((i, a, pc, pd))
check(cf_same == cf_tot, f"wood Layer-1 counterfactual incl. original_structure/wood_type: byte-identical "
                         f"({cf_same}/{cf_tot}, {len(WOOD)} wood objects) bad={cf_bad[:2]}")
# J-2411: the former residual is closed. Inject Layer-1 form keys into the causal_state of EVERY object (wood or
# not, Layer-2 key or not): generative state and every action's prose stay byte-identical on the migrated copy.
inj_g = inj_p = inj_n = 0
for i in ids:
    o = ws_D._load()[i]
    o.causal_state = dict(o.causal_state, original_structure="root", wood_type="softwood")
for i in ids:
    inj_g += ws_D.get_generative_state(i) == ws_C.get_generative_state(i)
    for a in ACTIONS6:
        inj_n += 1
        inj_p += ws_D.describe_and_observe(i, a) == ws_C.describe_and_observe(i, a)
check(inj_g == len(ids) and inj_p == inj_n, f"injected Layer-1 form keys on all {len(ids)} objects reach nothing: "
      f"generative state {inj_g}/{len(ids)}, prose {inj_p}/{inj_n} byte-identical")
dfw = [i for i in WOOD if "structure" not in ws_C._load()[i].physical_state]
check(bool(dfw) and ws_D.describe_and_observe(dfw[0], "look") == ws_C.describe_and_observe(dfw[0], "look")
      and ws_D.get_generative_state(dfw[0])["structure"] == "unknown",
      f"  ({dfw[:1]} has no Layer-2 form key: an injected Layer-1 key no longer reaches its look (was the J-2388 residual))")
# control: the same change made in Layer 2 does reach the prose
d17 = ws_D._load()["driftwood_17"]
d17.physical_state["wood_type"] = "softwood"; d17.physical_state["salt_accumulation"] = 0.0; d17.physical_state["moisture"] = 0.0
c17 = ws_C._load()["driftwood_17"]
check(obs.generate_observation(ws_D.get_generative_state("driftwood_17"), "smell")["scent"]["value"] == "resinous"
      and obs.generate_observation(ws_D.get_generative_state("driftwood_17"), "inspect_end")["annual_ring_visibility"]["value"]
      != obs.generate_observation(ws_C.get_generative_state("driftwood_17"), "inspect_end")["annual_ring_visibility"]["value"],
      "  (control: a Layer-2 wood_type change diverges smell / inspect_end -> the keys are live in Layer 2)")

# ── 7. spawn mirrors the keys ──────────────────────────────────────────────────────────────────────
shutil.copyfile(tmp / "C_new_mig.json", tmp / "S_new.json"); shutil.copyfile(tmp / "A_ref.json", tmp / "S_ref.json")
from core import world_objects as wo
wo._OBJECTS_F = tmp / "world_objects.json"
ws_S = _point(_mod("ws_newS_j2388", HERE / "core" / "world_substrate.py"), "S_new")
ws_Sr = _point(_mod("ws_refS_j2388", src=ref_src), "S_ref")
ws_S._SPAWN_CAP = ws_Sr._SPAWN_CAP = 10 ** 6
sp_ok = 0; sp_n = 0
for seed in ("j2388a", "j2388b", "j2388c", "j2388d", "j2388e"):
    for cls in ("driftwood", "deadfall_wood", "stone"):
        n, r_ = ws_S.spawn_object(cls, "shore", seed=seed, days_hint=40, as_of=1.79e9), \
                ws_Sr.spawn_object(cls, "shore", seed=seed, days_hint=40, as_of=1.79e9)
        if n is None or r_ is None:
            continue
        sp_n += 1
        exp = dict(r_.physical_state)
        for l2, l1 in (("structure", "original_structure"), ("wood_type", "wood_type")):
            if l1 in r_.causal_state:
                exp[l2] = r_.causal_state[l1]
        sp_ok += (n.physical_state == exp and n.causal_state == r_.causal_state and n.object_id == r_.object_id
                  and n.name == r_.name)
check(sp_n > 0 and sp_ok == sp_n, f"spawn_object mirrors form keys, all else equal to reference ({sp_ok}/{sp_n})")
dw = ws_S.spawn_object("driftwood", "shore", seed="j2388z", days_hint=10, as_of=1.79e9)
check(dw is not None and dw.physical_state.get("structure") == dw.causal_state.get("original_structure")
      and dw.physical_state.get("wood_type") == dw.causal_state.get("wood_type"), "a spawned driftwood carries both Layer-2 keys")

# ── 8. live canary ─────────────────────────────────────────────────────────────────────────────────
check(_h(LIVE) == canary0, "live data/world_substrate.json unchanged (sha256 canary)")
check((_h(STORE), _h(UNMIG)) == src0, "--store / --unmigrated sources unchanged (sha256 canary)")
shutil.rmtree(tmp, ignore_errors=True)
print("RESULT:", "PASS" if not FAIL else f"FAIL ({len(FAIL)})")
sys.exit(0 if not FAIL else 1)

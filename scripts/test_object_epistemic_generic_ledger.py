"""Test for J-2394 (object_epistemic_loop, D-0475 ruled yes by travis 2026-10-18): the generic tracked-object
look branches (shore, garden) append buses.object_ledger_line on a re-encounter, as the driftwood_17 look does.

Hermetic: every store the looks touch (world_substrate.json, world_objects.json, room_state.json, garden.json,
buses_log.jsonl, buses_state.json) is a temp COPY outside data/ (profile.guard_path honours an upstream
redirect). The live files are only hashed (sha256 canary before/after). Each pass runs in its own child process
on its own fresh copies, so observation counts never leak from one pass into the next.

  1. core resolves inside this worktree (import core first);
  2. NASCENCE_GENERIC_OBJECT_LEDGER=0: every look (first + re-look) of every reachable shore/garden object is
     byte-identical with the reference sensorium (git <ref>, pre-J-2394, loaded as core.sensorium in its child),
     and each re-look still logs a delivery row with branch, would_ledger, base_chars, ledger_shown=False;
  3. default (switch unset = ON per D-0475): a first look is byte-identical with the reference (no ledger yet);
     a re-look is exactly reference + the ledger line, the ledger starts ' You have looked at this before' and
     ends with the existing closing sentence; its row names entity + branch, would_ledger == len(ledger) and
     base_chars == len(reference look);
  4. no affordance text / verdict / imperative added: the appended text is buses.object_ledger_line's own line
     (re-rendered without branch it is the same string), with NASCENCE_LEDGER_HYPOTHESIS_READBACK unset the
     line carries no read-back, and it holds none of supported/contradicted/test/try;
  5. NASCENCE_LEDGER_HYPOTHESIS_READBACK=1 still governs the read-back on the generic branch exactly as built
     (J-2375): a seeded provenance-bearing inference is shown in his own words on a generic re-look;
  6. driftwood_17's look and its delivery row are byte-identical with the reference (no new fields);
  7. live stores unchanged (sha256 canary).
Exit 0 = pass.  python scripts/test_object_epistemic_generic_ledger.py [--ref <git rev>]
"""
import hashlib, importlib.util, json, os, pathlib, random, re, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__

REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "865e4428"
LIVE_DATA = pathlib.Path(r"C:\Nascence\data")
STORES = ["world_substrate.json", "world_objects.json", "room_state.json", "garden.json", "garden_knowledge.json"]
LIVE = [LIVE_DATA / n for n in STORES + ["buses_log.jsonl"]]
GOOD = "This pale stone might be pumice"


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


# ── child: one pass on its own store copies ──────────────────────────────────────────────────────────────
def child(mode, d):
    d = pathlib.Path(d)
    if mode.startswith("ref"):
        src = subprocess.run(["git", "-C", str(HERE), "show", f"{REF}:core/sensorium.py"], capture_output=True,
                             text=True, encoding="utf-8", check=True).stdout
        assert "_generic_ledger" not in src, "reference is pre-J-2394"
        p = d / "sensorium_ref.py"
        p.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("core.sensorium", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["core.sensorium"] = m
        spec.loader.exec_module(m)
        core.sensorium = m
    from core import world_substrate as ws, world_objects as wo, buses, sensorium as sens, garden as gd
    ws._SUBSTRATE_F = d / "world_substrate.json"
    ws._LAST_LOOKED_F = d / "last_looked.json"
    ws._SUBSTRATE_LOG = d / "events.jsonl"
    wo._OBJECTS_F = d / "world_objects.json"
    sens._STATE_F = d / "room_state.json"
    gd._F = d / "garden.json"
    gd._LEDGER = d / "garden_ledger.jsonl"
    gd._EVENTS = d / "garden_events.jsonl"
    from core import garden_knowledge as gk
    gk._F = d / "garden_knowledge.json"
    buses._DELIVERY_LOG = d / "buses_log.jsonl"
    buses._STATE = d / "buses_state.json"
    ws._cache = {}
    ws._cache_ts = 0.0
    wo._objects_cache = {}
    sens._load()
    objs = ws._load()
    # seed one provenance-bearing Phase-1 inference on the first reachable shore stone (read-back probe)
    plan = json.loads((d / "plan.json").read_text(encoding="utf-8"))
    out = {"looks": [], "rows": []}
    for oid, place, target in plan:
        if oid == plan[0][0] and mode.endswith("_rb"):
            o = objs[oid]
            o.inferences.append({"inference_id": "inf_j2394_probe", "timestamp": 1.0, "hypothesis": GOOD,
                                 "confidence": 0.5, "supporting_observations": [o.observations[0].observation_id
                                                                                if hasattr(o.observations[0], "observation_id")
                                                                                else "obs0"],
                                 "supporting_knowledge": [], "outcome": "unobserved"})
        sens.state["location"] = place
        for i in (0, 1):
            random.seed(1234)
            if oid == "driftwood_17":
                txt = sens._shore_look(target)
            else:
                txt = sens._shore_look(target) if place == "shore" else sens._garden_look(target)
            out["looks"].append([oid, i, txt])
            if mode == "new" and i == 1:   # the same ledger re-rendered without a branch, right after (no row logged)
                _ld = buses._log_delivery
                buses._log_delivery = lambda *a, **k: None
                try:
                    out.setdefault("plain", {})[oid] = buses.object_ledger_line(oid)
                finally:
                    buses._log_delivery = _ld
    if buses._DELIVERY_LOG.exists():
        for line in buses._DELIVERY_LOG.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            r.pop("ts", None)
            out["rows"].append(r)
    (d / f"out_{mode}.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


if "--child" in sys.argv:
    child(sys.argv[sys.argv.index("--child") + 1], sys.argv[sys.argv.index("--child") + 2])
    sys.exit(0)

# ── parent ───────────────────────────────────────────────────────────────────────────────────────────────
canary0 = [_h(p) for p in LIVE]
FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


root = pathlib.Path(tempfile.mkdtemp(prefix="j2394_"))
seed = root / "seed"
seed.mkdir()
for n in STORES:
    shutil.copyfile(LIVE_DATA / n, seed / n)
# The live shore holds few distinct tracked objects today (his shells/stones were kept and now sit in the study),
# so the seed COPY puts the kept shore_* naturals back on the shore -- temp copy only -- to exercise the branch.
_sub = json.loads((seed / "world_substrate.json").read_text(encoding="utf-8"))
_wob = json.loads((seed / "world_objects.json").read_text(encoding="utf-8"))
MOVED = [k for k, o in _sub.items() if k.startswith("shore_") and o.get("location") == "study"
         and o.get("object_class") in ("shell", "stone", "sea_glass", "bone") and k in _wob]
for k in MOVED:
    _sub[k]["location"] = "shore"
    _wob[k]["location"] = "shore"
    _wob[k]["position"] = [3.0, 6.0, 0.0]
(seed / "world_substrate.json").write_text(json.dumps(_sub), encoding="utf-8")
(seed / "world_objects.json").write_text(json.dumps(_wob), encoding="utf-8")

# choose targets: every tracked shore/garden object whose own name resolves back to it via find_object_at
from core import world_substrate as ws0
ws0._SUBSTRATE_F = seed / "world_substrate.json"
ws0._cache = {}
ws0._cache_ts = 0.0
objs0 = ws0._load()
cands = []
for oid, o in sorted(objs0.items()):
    if o.location not in ("shore", "garden") or oid == "driftwood_17":
        continue
    words = [o.name] + [w for w in re.findall(r"[a-z][a-z-]+", o.name.lower()) if len(w) > 3]
    words += [f"the {o.object_class.replace('_', ' ')}"]
    hit = next((w for w in words if ws0.find_object_at(o.location, w) == oid), None)
    if hit:
        cands.append([oid, o.location, hit])
shore = [c for c in cands if c[1] == "shore"]
garden = [c for c in cands if c[1] == "garden"]
print(f"store copy: {len(objs0)} objects; name-resolvable shore {len(shore)}, garden {len(garden)}")
# first shore stone first (the read-back probe target), then every candidate, then driftwood_17 last
stones = [c for c in shore if objs0[c[0]].object_class == "stone"]
plan = ([stones[0]] if stones else []) + [c for c in cands if not stones or c != stones[0]]
plan.append(["driftwood_17", "shore", "driftwood"])


def run(mode, env):
    d = root / mode
    shutil.copytree(seed, d)
    (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    e = {k: v for k, v in os.environ.items() if k not in ("NASCENCE_GENERIC_OBJECT_LEDGER",
                                                          "NASCENCE_LEDGER_HYPOTHESIS_READBACK")}
    e.update(env)
    e["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).resolve()), "--child", mode, str(d), "--ref", REF],
                       env=e, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-4000:])
        raise SystemExit(f"child {mode} failed")
    return json.loads((d / f"out_{mode}.json").read_text(encoding="utf-8"))


ref = run("ref", {})
off = run("off", {"NASCENCE_GENERIC_OBJECT_LEDGER": "0"})
new = run("new", {})
rb = run("new_rb", {"NASCENCE_LEDGER_HYPOTHESIS_READBACK": "1"})
refrb = run("ref_rb", {"NASCENCE_LEDGER_HYPOTHESIS_READBACK": "1"})

# which planned objects actually reached a generic tracked-object branch in the reference
reached = {}
for (oid, i, t) in ref["looks"]:
    o = objs0.get(oid)
    if oid != "driftwood_17" and i == 0 and o and t.startswith(f"You look at {o.name}"):
        reached[oid] = o.location
n_sh = sum(1 for v in reached.values() if v == "shore")
n_ga = sum(1 for v in reached.values() if v == "garden")
print(f"reached the generic branch: shore {n_sh}, garden {n_ga}")
check(n_sh >= 5 and n_ga >= 3 and stones and plan[0][0] in reached, f"enough real objects reach both generic branches (shore {n_sh}, garden {n_ga})")

# 2. switch off
same = sum(a == b for a, b in zip(ref["looks"], off["looks"]))
check(len(off["looks"]) == len(ref["looks"]) and same == len(ref["looks"]),
      f"OFF: every look byte-identical with {REF} ({same}/{len(ref['looks'])})")
gen_off = [r for r in off["rows"] if r.get("branch")]
check(len(gen_off) > 0 and all(r.get("ledger_shown") is False and r["would_ledger"] > 0 and r["base_chars"] > 0
                               for r in gen_off),
      f"OFF: generic re-looks still log shadow rows with ledger_shown=False ({len(gen_off)} rows)")

# 3. default on: every look == reference + (ledger or ""), one branch row per non-empty ledger
L = {(o, i): t for o, i, t in new["looks"]}
R = {(o, i): t for o, i, t in ref["looks"]}
rows_by = {}
for r in new["rows"]:
    if r.get("branch"):
        rows_by.setdefault(r["entity"], []).append(r)
bad = []; n_led = 0; n_first_empty = 0
for oid in reached:
    leds = []
    for i in (0, 1):
        a, b = L[(oid, i)], R[(oid, i)]
        if not a.startswith(b):
            bad.append((oid, i, "prefix")); continue
        leds.append((i, a[len(b):], len(b)))
    nonempty = [x for x in leds if x[1]]
    n_led += len(nonempty)
    prior = len(objs0[oid].observations)
    if prior == 0:
        n_first_empty += leds and leds[0][1] == ""
        if leds and leds[0][1] != "":
            bad.append((oid, 0, "first look of a never-seen object carried a ledger"))
    rr = rows_by.get(oid[:24], [])
    if len(rr) != len(nonempty):
        bad.append((oid, "rows", len(rr), len(nonempty))); continue
    for (i, led, bl), r in zip(nonempty, rr):
        if not (led.startswith(" You have looked at this before")
                and led.endswith(" What that adds up to is still yours to work out.")
                and r["branch"] == reached[oid] and r["would_ledger"] == len(led) and r["base_chars"] == bl
                and "ledger_shown" not in r and "would_readback" not in r and "hypothesis_readback" not in r):
            bad.append((oid, i, "row/line"))
check(not bad, f"ON: every look = reference + ledger; row branch/would_ledger/base_chars exact ({len(reached)} objects) "
               f"bad={bad[:4]}")
_wl = sorted(r["would_ledger"] for v in rows_by.values() for r in v)
_bc = sorted(r["base_chars"] for v in rows_by.values() for r in v)
if _wl:
    print(f"   ledger chars median {_wl[len(_wl) // 2]} (min {_wl[0]}, max {_wl[-1]}); base look chars median "
          f"{_bc[len(_bc) // 2]} (min {_bc[0]}, max {_bc[-1]}); n={len(_wl)}")
check(n_led >= 10, f"ON: real ledger lines delivered on generic looks ({n_led})")
never = [o for o in reached if not objs0[o].observations]
check(len(never) == 0 or n_first_empty == len(never),
      f"ON: a never-seen object's first look carries no ledger ({n_first_empty}/{len(never)})")
ex = next((L[(o, 1)] for o in reached if objs0[o].location == "shore" and L[(o, 1)] != R[(o, 1)]), "")
print("   shore example:", repr(ex[:420]))

# 4. no new text beyond the ledger's own (the last look's ledger re-rendered without a branch is the same string)
BAR = re.compile(r"(supported|contradicted|test\w*|try|tries|tried|trying|held up|confirmed|refuted)", re.I)
same_line = all(L[(o, 1)][len(R[(o, 1)]):] in ("", new["plain"][o]) for o in reached)
check(same_line, "ON: the appended text is exactly buses.object_ledger_line(oid) (no branch-specific wording)")
check(not any(BAR.search(L[(o, i)][len(R[(o, i)]):]) or "Earlier you wondered" in L[(o, i)] for o in reached for i in (0, 1)),
      "ON: no verdict/test word, no read-back with NASCENCE_LEDGER_HYPOTHESIS_READBACK unset")

# 5. read-back still governed by its own switch
probe = plan[0][0]
RB = {(o, i): t for o, i, t in rb["looks"]}
RRB = {(o, i): t for o, i, t in refrb["looks"]}
check(probe in reached and f'Earlier you wondered about this: "{GOOD}"' in RB[(probe, 1)]
      and RB[(probe, 1)].startswith(RRB[(probe, 1)]) and GOOD not in RRB[(probe, 1)],
      f"READBACK=1: the seeded hypothesis is read back in his own words on the generic re-look of {probe} "
      f"(and never on the reference, which has no generic ledger)")
prow = [r for r in rb["rows"] if r.get("entity") == probe[:24] and r.get("branch")]
check(len(prow) >= 1 and prow[-1].get("hypothesis_readback") == "inf_j2394_probe",
      f"READBACK=1: generic delivery row names the shown read-back ({len(prow)} rows)")

# 6. driftwood_17 unchanged
dw = [(i, t) for o, i, t in new["looks"] if o == "driftwood_17"]
dwr = [(i, t) for o, i, t in ref["looks"] if o == "driftwood_17"]
check(dw == dwr and len(dw) == 2, "driftwood_17 look byte-identical with reference")
dr_new = [r for r in new["rows"] if r.get("entity") == "driftwood_17"]
dr_ref = [r for r in ref["rows"] if r.get("entity") == "driftwood_17"]
check(dr_new == dr_ref and len(dr_ref) >= 1, f"driftwood_17 delivery rows identical, no new fields ({len(dr_ref)} rows)")

# 7. canary
check([_h(p) for p in LIVE] == canary0, "live stores unchanged (sha256 canary)")
shutil.rmtree(root, ignore_errors=True)
print("ALL PASS" if not FAIL else f"{len(FAIL)} FAIL")
sys.exit(1 if FAIL else 0)

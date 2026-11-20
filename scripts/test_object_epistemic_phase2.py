"""Test for J-2375 (object_epistemic_loop Phase 2: hypothesis + senses-used read-back, D-0463 ALLOWED).

Hermetic: world_substrate._SUBSTRATE_F and buses._DELIVERY_LOG are temp paths outside data/ (profile.guard_path
honours an upstream redirect). The live data/world_substrate.json and data/buses_log.jsonl are only hashed.

  1. core resolves inside this worktree (import core first);
  2. switch OFF (default, NASCENCE_LEDGER_HYPOTHESIS_READBACK unset/0): object_ledger_line returns the
     byte-identical string as the pre-Phase-2 reference (git show <ref>:core/buses.py), and the identical
     delivery row apart from the shadow field would_readback=<id>, present exactly when one was eligible;
  3. switch ON: the line carries his own words verbatim and the senses-used summary
     ("so far you have only looked at it" / "... looked at it and picked it up"), and contains none of
     supported / contradicted / test / try (word-bounded) nor a segment that opens with an imperative verb;
     no confidence number, no outcome value;
  4. guard: empty supporting_observations, > 240 chars, superseded, or a bar word -> not read back
     (the line equals the switch-off line); the newest ACTIVE valid one is chosen over a later bad row;
  5. Layer 1 never read: an object whose causal_state / physical_state / causal_history raise on any
     access, and whose get_world_truth / get_physical raise, renders identically; a Layer-1-only
     difference gives a byte-identical line;
  6. the delivery row names the read-back inference id only when one was shown;
  7. live data/world_substrate.json and data/buses_log.jsonl unchanged (sha256 canary).
Exit 0 = pass.  python scripts/test_object_epistemic_phase2.py [--ref <git rev for the reference>]
"""
import hashlib, importlib.util, json, os, pathlib, re, subprocess, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__

REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "e03260bf"
LIVE = [pathlib.Path(r"C:\Nascence\data\world_substrate.json"), pathlib.Path(r"C:\Nascence\data\buses_log.jsonl")]


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


canary0 = [_h(p) for p in LIVE]
FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


os.environ.pop("NASCENCE_LEDGER_HYPOTHESIS_READBACK", None)
tmp = pathlib.Path(tempfile.mkdtemp(prefix="j2375_"))
from core import world_substrate as ws
from core import buses
ws._SUBSTRATE_F = tmp / "world_substrate.json"
ws._LAST_LOOKED_F = tmp / "last_looked.json"
ws._SUBSTRATE_LOG = tmp / "events.jsonl"
buses._DELIVERY_LOG = tmp / "buses_log.jsonl"
buses._STATE = tmp / "buses_state.json"

# reference: the pre-J-2375 module, loaded from git under its own name
ref_src = subprocess.run(["git", "-C", str(HERE), "show", f"{REF}:core/buses.py"], capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
check("_hypothesis_readback" not in ref_src, f"reference {REF} is the pre-Phase-2 buses.py")
ref_path = tmp / "buses_ref.py"
ref_path.write_text(ref_src, encoding="utf-8")
spec = importlib.util.spec_from_file_location("buses_ref", ref_path)
bref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bref)
bref._DELIVERY_LOG = tmp / "buses_log_ref.jsonl"
bref._STATE = tmp / "buses_state_ref.json"

NOW = time.time()


def obs(oid, n, actions=None):
    actions = actions or ["look"] * n
    return [{"observation_id": f"obs_{oid}_{i}", "timestamp": NOW - 86400 * 5 + i, "action": a,
             "features": ({"colour": "pale grey", "surface_damage": "sea_worn"} if a == "look"
                          else {"relative_weight": "light"})}
            for i, a in enumerate(actions)]


def inf(oid, i, hyp, prov=True, sup=None, conf=0.6):
    d = {"inference_id": f"inf_{oid}_{i}", "timestamp": NOW - 1000 + i, "hypothesis": hyp, "confidence": conf,
         "supporting_observations": [f"obs_{oid}_0"] if prov else [], "supporting_knowledge": [],
         "outcome": "unobserved"}
    if sup:
        d["superseded_by"] = sup
    return d


GOOD = "This pale stone might be pumice"
LONG = "I wonder " + "about mottainai and the regret of waste and the tide " * 6
seed = {
    "s_plain": {"observations": obs("s_plain", 3), "inferences": []},
    "s_good": {"observations": obs("s_good", 3), "inferences": [inf("s_good", 0, GOOD)]},
    "s_senses": {"observations": obs("s_senses", 3, ["look", "pick_up", "look"]),
                 "inferences": [inf("s_senses", 0, GOOD)]},
    "s_noprov": {"observations": obs("s_noprov", 3), "inferences": [inf("s_noprov", 0, GOOD, prov=False)]},
    "s_long": {"observations": obs("s_long", 3), "inferences": [inf("s_long", 0, LONG)]},
    "s_bar": {"observations": obs("s_bar", 3),
              "inferences": [inf("s_bar", 0, "I should test whether the stone floats")]},
    "s_super": {"observations": obs("s_super", 3), "inferences": [
        inf("s_super", 0, "Maybe the stone is basalt from the headland", sup="inf_s_super_1"),
        inf("s_super", 1, GOOD)]},
    "s_order": {"observations": obs("s_order", 3), "inferences": [   # legacy contaminated row AFTER a valid active one
        inf("s_order", 0, "I think the stone came from the river"), inf("s_order", 1, LONG, prov=False)]},
    "s_one": {"observations": obs("s_one", 1), "inferences": [inf("s_one", 0, GOOD)]},   # first look: no ledger at all
}
for oid, d in seed.items():
    d.update({"object_id": oid, "name": "a smooth grey beach stone", "location": "shore", "object_class": "stone",
              "physical_state": {"density": 0.3}, "causal_state": {"rock": "pumice"}, "causal_history": []})
ws._SUBSTRATE_F.write_text(json.dumps(seed), encoding="utf-8")
ws._cache = {}
ws._cache_ts = 0.0


def rows(p):
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        r.pop("ts", None)
        out.append(r)
    return out


# -- 2. switch off: byte-identical with the reference --------------------------------------------
off = {}
for oid in seed:
    a, b = buses.object_ledger_line(oid), bref.object_ledger_line(oid)
    off[oid] = a
    check(a == b, f"switch off: {oid} byte-identical with {REF} ({len(a)} chars)")
r_new, r_ref = rows(buses._DELIVERY_LOG), rows(bref._DELIVERY_LOG)
n_off = len(r_new)
wb = {r["entity"]: r.get("would_readback") for r in r_new if r.get("would_readback")}
check(n_off == 8 and [{k: v for k, v in r.items() if k != "would_readback"} for r in r_new] == r_ref,
      f"switch off: delivery rows identical with reference apart from the shadow field ({n_off} rows)")
check(wb == {"s_good": "inf_s_good_0", "s_senses": "inf_s_senses_0", "s_super": "inf_s_super_1",
             "s_order": "inf_s_order_0"} and not any("hypothesis_readback" in r for r in r_new),
      f"switch off: would_readback shadow field names exactly the eligible read-backs: {wb}")
os.environ["NASCENCE_LEDGER_HYPOTHESIS_READBACK"] = "0"
check(all(buses.object_ledger_line(o) == off[o] for o in seed), "NASCENCE_LEDGER_HYPOTHESIS_READBACK=0 also byte-identical")

# -- 3. switch on ---------------------------------------------------------------------------------
os.environ["NASCENCE_LEDGER_HYPOTHESIS_READBACK"] = "1"
buses._DELIVERY_LOG.unlink()
on = {oid: buses.object_ledger_line(oid) for oid in seed}
for o in seed:
    print(f"   {o}: {on[o]!r}")
check(f'"{GOOD}"' in on["s_good"] and "so far you have only looked at it." in on["s_good"],
      "on: his own words verbatim + 'so far you have only looked at it'")
check("so far you have looked at it and picked it up." in on["s_senses"],
      "on: senses-used lists look + pick_up, in first-use order")
head = off["s_good"].split(" What that adds up to")[0]
check(on["s_good"].startswith(head) and on["s_good"].endswith(" What that adds up to is still yours to work out."),
      "on: read-back sits after the observation summary, closing line kept")
BAR = re.compile(r"\b(supported|contradicted|test\w*|try|tries|tried|trying|held up|confirmed|refuted|wrong|right)\b",
                 re.I)
IMPER = {"look", "pick", "smell", "scrape", "float", "test", "try", "check", "see", "compare", "consider", "feel",
         "touch", "lift", "turn", "put", "find", "examine", "inspect", "hold", "weigh", "taste", "drop", "break"}
for o in ("s_good", "s_senses", "s_super", "s_order"):
    rb = on[o][len(off[o].split(" What that adds up to")[0]):]
    segs = [s.strip().strip('"').lower() for s in re.split(r"[.;:!?]", rb) if s.strip()]
    check(not BAR.search(rb), f"on: {o} read-back carries no verdict/test word")
    check(not any(s.split()[0] in IMPER for s in segs if s.split()),
          f"on: {o} no segment opens with an imperative verb {segs}")
    check(not re.search(r"\d\.\d|unobserved|confidence|outcome", rb), f"on: {o} no confidence number / outcome field")

# -- 4. guard -------------------------------------------------------------------------------------
for o in ("s_plain", "s_noprov", "s_long", "s_bar", "s_one"):
    check(on[o] == off[o], f"guard: {o} -> no read-back (line equals switch-off line)")
check('"This pale stone might be pumice"' in on["s_super"] and "basalt" not in on["s_super"],
      "guard: superseded row never shown")
check("came from the river" in on["s_order"], "guard: a later provenance-empty row is skipped, the active valid one shown")

# -- 6. delivery row names the read-back ----------------------------------------------------------
rr = rows(buses._DELIVERY_LOG)
shown = {r["entity"]: r.get("hypothesis_readback") for r in rr}
bad_keys = [k for r in rr if r["entity"] in ("s_plain", "s_noprov", "s_long", "s_bar") for k in r]
check(shown.get("s_good") == "inf_s_good_0" and shown.get("s_order") == "inf_s_order_0"
      and "hypothesis_readback" not in bad_keys, f"delivery row names the inference id only when shown: {shown}")


# -- 5. Layer 1 never read ------------------------------------------------------------------------
class Trap(dict):
    def _boom(self, *a, **k):
        raise AssertionError("Layer 1/2 read")
    __getitem__ = get = items = keys = values = __iter__ = __contains__ = __len__ = _boom


def _raise(*a, **k):
    raise AssertionError("Layer 1/2 accessor called")


real_get = ws.get_object


def trapped(oid):
    o = real_get(oid)
    if o is not None:
        o.causal_state = Trap()
        o.physical_state = Trap()
        o.causal_history = Trap()
        o.get_world_truth = _raise
        o.get_physical = _raise
    return o


ws.get_object = trapped
try:
    t = buses.object_ledger_line("s_good")
finally:
    ws.get_object = real_get
check(t == on["s_good"], "Layer 1/2 trapped: read-back renders identically (never touched)")
seed2 = json.loads(ws._SUBSTRATE_F.read_text(encoding="utf-8"))
seed2["s_good"]["causal_state"] = {"rock": "basalt", "origin": "headland"}
seed2["s_good"]["causal_history"] = [{"event": "x"}]
ws._SUBSTRATE_F.write_text(json.dumps(seed2), encoding="utf-8")
ws._cache = {}
ws._cache_ts = 0.0
check(buses.object_ledger_line("s_good") == on["s_good"], "Layer-1-only difference -> byte-identical line")

os.environ.pop("NASCENCE_LEDGER_HYPOTHESIS_READBACK", None)
check(buses.object_ledger_line("s_good") == off["s_good"], "switch unset again -> back to the off line")

# -- 7. canary ------------------------------------------------------------------------------------
check([_h(p) for p in LIVE] == canary0, "live world_substrate.json + buses_log.jsonl unchanged (sha256)")
print(f"\n{'ALL PASS' if not FAIL else str(len(FAIL)) + ' FAIL'}")
sys.exit(1 if FAIL else 0)

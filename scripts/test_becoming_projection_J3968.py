"""test_becoming_projection_J3968.py -- hermetic tests for J-3968 (D-0745, design J-3835 job 7): the becoming_symbol
projection rules behind BECOMING_PROJECT (cap 1, never pass-2 filler, its own calibrated floor, fail closed with no floor)
and scripts/becoming_projection_replay.py (the floor calibration). OFFLINE: fake embedder, every store in a sandbox.
  python scripts/test_becoming_projection_J3968.py   -> exit 0 iff all pass"""
from __future__ import annotations
import importlib.util, json, pathlib, re, subprocess, sys, zlib
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import core  # noqa: E402  -- BEFORE lab_env (F-2423)
assert pathlib.Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), (core.__file__, ROOT)
import numpy as np  # noqa: E402
from core import profile  # noqa: E402
from core.memory import store  # noqa: E402
from core import identity_projection as ip  # noqa: E402
from core import becoming_nodes as bn  # noqa: E402
import lab_env  # noqa: E402
assert pathlib.Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), "lab_env swapped core"
spec_r = importlib.util.spec_from_file_location("bpr", ROOT / "scripts" / "becoming_projection_replay.py")
bpr = importlib.util.module_from_spec(spec_r); spec_r.loader.exec_module(bpr)

FAILS = []
def check(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)

def fake_embed(text):
    if not text or not text.strip():
        return None
    v = np.zeros(256, dtype=np.float32)
    for w in re.findall(r"[\w]+", text.lower()):
        v[zlib.crc32(w.encode("utf-8")) % 256] += 1.0
    n = float(np.linalg.norm(v))
    return (v / n).astype(np.float32) if n > 0 else None
store._embed = fake_embed

TYPES = ["value_earned", "history", "symbol", "bond", "practice", "stand"]
WORDS = ["river", "garden", "knot", "crossing", "tide", "pause", "letter", "stone", "lamp", "bridge", "moss", "wind"]
def mk(i):
    return {"id": f"n{i}", "type": TYPES[i % len(TYPES)], "weight": round(0.3 + (i % 7) * 0.1, 2),
            "text": f"{WORDS[i % 12]} {WORDS[(i * 5 + 3) % 12]} node number {i}"}
BEC1 = {"id": "bsym_a", "type": "becoming_symbol", "weight": 0.99, "text": "the lamp on the bridge keeps the tide honest"}
BEC2 = {"id": "bsym_b", "type": "becoming_symbol", "weight": 0.99, "text": "the lamp over the bridge and the tide moss"}
BASE = [mk(i) for i in range(40)]
EST_BEC = {"nodes": BASE + [BEC1, BEC2]}

old_src = subprocess.run(["git", "show", "HEAD:core/identity_projection.py"], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8").stdout
spec = importlib.util.spec_from_loader("ip_head", loader=None)
old = importlib.util.module_from_spec(spec)
old.__file__ = str(ROOT / "core" / "identity_projection.py")
exec(compile(old_src, "ip_head", "exec"), old.__dict__)
def reset(m):
    m._cache.update({"sig": None, "nodes": None, "embs": None}); m._recency.clear()

print("[0] flags default off")
check("BECOMING_PROJECT False", bn.BECOMING_PROJECT is False)
check("no floor override by default", ip._BECOMING_FLOOR_OVERRIDE is None)

print("[1] calibrate_floor (pure)")
rng = np.random.RandomState(7)
cs = rng.uniform(0.0, 1.0, 1000).tolist()
r = bpr.calibrate_floor(cs)
check("uniform 1000: rate within 3-8 percent", r["in_band"] and 0.03 <= r["rate"] <= 0.08, str(r))
check("floor strictly above the 81st-from-top value", r["floor"] > sorted(cs, reverse=True)[80])
check("too few contexts refused", bpr.calibrate_floor(cs[:10])["status"] == "too_few_contexts" and bpr.calibrate_floor(cs[:10])["floor"] is None)
r2 = bpr.calibrate_floor([0.5] * 200)
check("all-tied cosines: unreachable band flagged, not faked", (not r2["in_band"]) and r2["status"] != "ok", str(r2))
check("narrower band respected", bpr.calibrate_floor(cs, 0.01, 0.02)["rate"] <= 0.02)

with lab_env.isolate(db="empty", also=[(ip, ["_ESTATE_F", "_LOG", "_IDS_LOG", "_BECOMING_FLOOR_F"])]) as lab:
    lab = pathlib.Path(lab)
    old._ESTATE_F = ip._ESTATE_F
    est = pathlib.Path(ip._ESTATE_F)
    est.write_text(json.dumps(EST_BEC), encoding="utf-8")
    ctxs = [f"{WORDS[c % 12]} and {WORDS[(c * 7 + 1) % 12]} thought {c}" for c in range(200)]
    ctxs += [f"lamp bridge tide {c}" for c in range(40)]

    print("[2] flag OFF: picks identical to HEAD even with becoming nodes and a floor on file")
    fp = pathlib.Path(ip._BECOMING_FLOOR_F); fp.parent.mkdir(parents=True, exist_ok=True)
    check("floor path inside the sandbox", fp.resolve().is_relative_to(lab.resolve()))
    fp.write_text(json.dumps({"floor": 0.2}), encoding="utf-8")
    reset(ip); reset(old)
    same = all([(n["id"], n["score"], n["rel"]) for n in ip.project(c)["nodes"]] ==
               [(n["id"], n["score"], n["rel"]) for n in old.project(c)["nodes"]] for c in ctxs)
    check("240 contexts identical to HEAD", same)

    orig = bn.BECOMING_PROJECT
    bn.BECOMING_PROJECT = True
    try:
        print("[3] flag ON, no calibrated floor on file: the type never surfaces (fail closed)")
        fp.unlink(); ip._becoming_floor_cache.update({"mtime": None, "floor": None}); reset(ip)
        check("floor is None with no file", ip._becoming_floor() is None)
        bec = sum(1 for c in ctxs for n in ip.project(c)["nodes"] if n["type"] == "becoming_symbol")
        check("zero becoming picks over 240 contexts", bec == 0, str(bec))

        print("[4] floor from file is read and cached by mtime; bad values ignored")
        fp.write_text(json.dumps({"floor": 0.2}), encoding="utf-8")
        check("floor 0.2 read", ip._becoming_floor() == 0.2)
        fp.write_text(json.dumps({"floor": 7}), encoding="utf-8")
        ip._becoming_floor_cache.update({"mtime": None})
        check("out-of-range floor ignored", ip._becoming_floor() is None)
        fp.write_text("not json", encoding="utf-8"); ip._becoming_floor_cache.update({"mtime": None})
        check("garbage floor file ignored", ip._becoming_floor() is None)

        print("[5] cap 1, own floor, never filler")
        ip._BECOMING_FLOOR_OVERRIDE = 0.2; reset(ip)
        maxn, surfaced, below = 0, 0, 0
        for c in ctxs:
            ns = [n for n in ip.project(c)["nodes"] if n["type"] == "becoming_symbol"]
            maxn = max(maxn, len(ns)); surfaced += bool(ns)
            below += sum(1 for n in ns if n["rel"] < 0.2 - 1e-9)
        check("never more than 1 becoming node in a projection", maxn <= 1, str(maxn))
        check("it does surface when the thought resembles it", surfaced > 0, str(surfaced))
        check("every surfaced becoming node cleared its own floor", below == 0, str(below))
        ip._BECOMING_FLOOR_OVERRIDE = 0.999; reset(ip)
        check("floor 0.999: nothing surfaces", all(n["type"] != "becoming_symbol" for c in ctxs for n in ip.project(c)["nodes"]))
        ip._BECOMING_FLOOR_OVERRIDE = 0.2; reset(ip)
        far = [f"zzz qqq unrelated {c}" for c in range(60)]
        check("off-topic contexts: never pass-2 filler despite weight 0.99",
              all(n["type"] != "becoming_symbol" for c in far for n in ip.project(c)["nodes"]))
        check("other types keep cap 2", all(
            sum(1 for n in ip.project(c)["nodes"] if n["type"] == "symbol") <= 2 for c in ctxs))
    finally:
        bn.BECOMING_PROJECT = orig
        ip._BECOMING_FLOOR_OVERRIDE = None

    print("[6] replay: calibrates a floor and write_floor round-trips")
    contexts = [f"{WORDS[c % 12]} {WORDS[(c * 3 + 1) % 12]} {WORDS[(c * 5 + 2) % 12]} thought {c}" for c in range(400)]
    res = bpr.replay([BEC1["text"]], contexts, lambda ts: [fake_embed(t) for t in ts])
    check("replay returns a floor and contexts", res["floor"] is not None and res["n_contexts"] == 400, str(res))
    pn = res["per_node"][0]
    check("per-node rate within band or honestly flagged", pn["in_band"] or pn["status"] != "ok", str(pn))
    out = lab / "floor_test.json"
    p = bpr.write_floor(res, path=out)
    check("written under the sandbox", pathlib.Path(p).resolve().is_relative_to(lab.resolve()))
    check("round-trip floor", json.loads(out.read_text(encoding="utf-8"))["floor"] == res["floor"])
    res2 = bpr.replay([BEC1["text"], BEC2["text"]], contexts, lambda ts: [fake_embed(t) for t in ts])
    check("two nodes: type floor is the max of per-node floors",
          res2["floor"] == max(p["floor"] for p in res2["per_node"]))

print("[7] fence: write_floor to the live path in a non-live process is refused, nothing written")
live_fp = ROOT / "data" / "identity" / "becoming_floor.json"
existed = live_fp.exists()
try:
    bpr.write_floor({"floor": 0.5, "n_contexts": 1, "per_node": []})
    check("live write refused", False)
except profile.NonLiveWriteError:
    check("live write refused", True)
check("live floor file not created", live_fp.exists() == existed)

print(f"\n{'ALL PASS' if not FAILS else 'FAILURES: ' + str(FAILS)}")
sys.exit(1 if FAILS else 0)

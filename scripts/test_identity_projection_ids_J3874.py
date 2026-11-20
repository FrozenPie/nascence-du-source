"""test_identity_projection_ids_J3874.py -- hermetic tests for J-3874 (design J-3835 jobs 1+2):
projection dedupe by id and the every-live-cycle id-bearing log core/identity_projection._IDS_LOG.
OFFLINE: fake embedder, every store redirected into a lab_env.isolate() sandbox. core imported BEFORE lab_env.
  python scripts/test_identity_projection_ids_J3874.py   -> exit 0 iff all pass"""
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
import lab_env  # noqa: E402
assert pathlib.Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), "lab_env swapped core"

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
UNIQUE = {"nodes": [mk(i) for i in range(40)]}
DUP = {"nodes": [mk(i) for i in range(40)] + [dict(mk(3), text="duplicate of three river garden", weight=1.0),
                                              dict(mk(3), text="second duplicate of three", weight=1.0)]}

# HEAD's module, for the "picks identical to before" check
old_src = subprocess.run(["git", "show", "HEAD:core/identity_projection.py"], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8").stdout
spec = importlib.util.spec_from_loader("ip_head", loader=None)
old = importlib.util.module_from_spec(spec)
old.__file__ = str(ROOT / "core" / "identity_projection.py")
exec(compile(old_src, "ip_head", "exec"), old.__dict__)

def reset(mod):
    mod._cache.update({"sig": None, "nodes": None, "embs": None}); mod._recency.clear()

print("[0] fence: non-live process outside a sandbox refused, nothing written, return unchanged")
assert not profile.LIVE
live_log = ROOT / "data" / "logs" / "identity_projection_ids.jsonl"
before = live_log.stat().st_size if live_log.exists() else None
try:
    ip._log_ids([{"id": "x", "type": "t", "score": 0, "rel": 0}])
    check("guard_path refused the ids log write", False)
except profile.NonLiveWriteError:
    check("guard_path refused the ids log write", True)
after = live_log.stat().st_size if live_log.exists() else None
check("live ids log untouched", before == after)

with lab_env.isolate(db="empty", also=[(ip, ["_ESTATE_F", "_LOG", "_IDS_LOG"])]) as lab:
    lab = pathlib.Path(lab)
    check("ids log path inside lab dir", pathlib.Path(ip._IDS_LOG).resolve().is_relative_to(lab.resolve()))
    check("estate path inside lab dir", pathlib.Path(ip._ESTATE_F).resolve().is_relative_to(lab.resolve()))
    old._ESTATE_F = ip._ESTATE_F
    est = pathlib.Path(ip._ESTATE_F)
    est.write_text(json.dumps(UNIQUE), encoding="utf-8")

    print("[1] unique-id estate: picks identical to HEAD on 200 contexts")
    reset(ip); reset(old)
    same = True
    for c in range(200):
        ctx = f"{WORDS[c % 12]} and {WORDS[(c * 7 + 1) % 12]} thought {c}"
        a = [(n["id"], n["score"], n["rel"]) for n in ip.project(ctx)["nodes"]]
        b = [(n["id"], n["score"], n["rel"]) for n in old.project(ctx)["nodes"]]
        if a != b:
            same = False; break
    check("200 contexts: identical picks and scores", same)

    print("[2] duplicate ids never surface twice")
    est.write_text(json.dumps(DUP), encoding="utf-8"); reset(ip)
    ids_ok = True
    for c in range(60):
        ids = [n["id"] for n in ip.project(f"river garden three {WORDS[c % 12]} {c}")["nodes"]]
        if len(ids) != len(set(ids)):
            ids_ok = False
    check("no repeated id in any projection", ids_ok)
    pn = ip._projectable()
    check("_projectable has distinct ids, first row wins", len({n['id'] for n in pn}) == len(pn) == 40
          and next(n for n in pn if n["id"] == "n3")["text"] == mk(3)["text"])

    print("[3] ids log: one row per live_axiom call, return value unchanged")
    reset(ip); logp = pathlib.Path(ip._IDS_LOG)
    check("no log before any call", not logp.exists())
    base = "YOUR NAME: Du\nVOICE STYLE: plain.\nSPEAKING CONSTRAINTS: none."
    calls, rets = 0, []
    for c in range(25):
        r = ip.live_axiom(f"river crossing {WORDS[c % 12]} {c}", base, cycle_id=f"cyc-{c}"); calls += 1; rets.append(r)
    check("empty context logs nothing and returns None", ip.live_axiom("  ", base) is None)
    rows = [json.loads(l) for l in logp.read_text(encoding="utf-8").splitlines() if l.strip()]
    check("row count == live_axiom projection count", len(rows) == calls, f"{len(rows)} vs {calls}")
    check("row schema", all({"ts", "cycle_id", "nodes"} <= set(r) and all({"id", "type", "score", "rel"} <= set(n) for n in r["nodes"]) for r in rows))
    check("cycle ids recorded", [r["cycle_id"] for r in rows] == [f"cyc-{c}" for c in range(25)])
    # same call sequence with logging made inert must return identical blocks
    reset(ip); real = ip._log_ids; ip._log_ids = lambda *a, **k: None
    rets2 = [ip.live_axiom(f"river crossing {WORDS[c % 12]} {c}", base) for c in range(25)]
    ip._log_ids = real
    check("returned axioms identical with logging on vs off", rets == rets2)
    check("logged ids match the stashed live projection", [n["id"] for n in rows[-1]["nodes"]] == [n["id"] for n in ip.last_live_projection()["nodes"]])
    # fence refusal inside live_axiom: return unchanged, nothing written
    n_before = len(logp.read_text(encoding="utf-8").splitlines())
    def refuse(*a, **k):
        raise profile.NonLiveWriteError("test")
    ip._log_ids = refuse; reset(ip)
    r = ip.live_axiom("river crossing x 99", base)
    ip._log_ids = real
    check("fence refusal leaves return value a real axiom", bool(r) and r.endswith("SPEAKING CONSTRAINTS: none."))
    check("fence refusal wrote nothing", len(logp.read_text(encoding="utf-8").splitlines()) == n_before)

print(f"\n{'ALL PASS' if not FAILS else 'FAILURES: ' + str(FAILS)}")
sys.exit(1 if FAILS else 0)

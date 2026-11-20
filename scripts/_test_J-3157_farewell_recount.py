"""
J-3157 / D-0545: one-time farewell recount of belief g45675272 (core/guidance_learning.apply_farewell_recount).
All store paths are temp redirects; Du's real stores are hashed before/after (canary).
  python scripts/_test_J-3157_farewell_recount.py     # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/
import hashlib, json, sys, tempfile, asyncio
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                   # noqa: E402  (first -- F-2423)
from core import guidance_learning as G       # noqa: E402

FAILS = 0
def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    if not c: FAILS += 1

LIVE = [Path(r"C:\Nascence") / "data" / n for n in ("guidance_beliefs.json", "guidance_shadow_log.jsonl", "guidance_recount_log.jsonl")]
snap = lambda p: hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
before = {p: snap(p) for p in LIVE}

T = Path(tempfile.mkdtemp(prefix="J3157_"))
G._BELIEFS, G._LOG, G._RECOUNT_LOG = T / "b.json", T / "s.jsonl", T / "r.jsonl"
G._INTEG_STATE, G._INTEG_LOG = T / "st.json", T / "il.jsonl"
G.materialize_promoted_beliefs = lambda: 0
FAREWELL = "渡 — it's time to bank the fire and rest for a while. Nothing's wrong; this is just the quiet."
caps_far = [f"I accept stillness variant {i} as a natural rhythm not failure" for i in range(5)]
caps_ind = ["Rest follows effort like water finds level", "Let the ash be taken or the fire smothers"]
rows = [{"ts": 1.0 + i, "is_guidance": True, "principle": c, "raw_input": FAREWELL} for i, c in enumerate(caps_far)]
rows += [{"ts": 10.0 + i, "is_guidance": True, "principle": c, "raw_input": "You can find signs of it everywhere."} for i, c in enumerate(caps_ind)]
G._LOG.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
def belief(i, caps, status="promoted", corr=None):
    b = G._new_belief({"ts": 1.0, "domain": "self"}, caps[0]); b["id"] = i
    b.update(captures=list(caps), corroboration_count=corr or len(caps), entrenchment=0.9, status=status, materialized=True)
    return b
target, other = belief("g45675272", caps_far + caps_ind), belief("gOTHER", caps_far[:3])
G._BELIEFS.write_text(json.dumps([target, other]), encoding="utf-8")

print("[1] audit is read-only and sees both beliefs")
h = snap(G._BELIEFS)
a = {x["id"]: x for x in G.farewell_capture_audit()}
check(snap(G._BELIEFS) == h and set(a) == {"g45675272", "gOTHER"}, "audit read-only, lists target + other")
check(a["g45675272"]["farewell_captures"] == 5 and a["g45675272"]["independent_captures"] == 2, "5 farewell / 2 independent")

print("[2] recount")
res = G.apply_farewell_recount()
bs = {b["id"]: b for b in json.loads(G._BELIEFS.read_text(encoding="utf-8"))}
t = bs["g45675272"]
check(len(res) == 1 and t["corroboration_count"] == 2 and t["status"] == "tentative" and t["entrenchment"] == 0.5,
      "corr 2, tentative, entrenchment 0.5")
check(bs["gOTHER"]["corroboration_count"] == 3 and bs["gOTHER"]["status"] == "promoted", "other belief untouched")
check(t["captures"] == target["captures"], "captures preserved")
check((T / "guidance_beliefs.pre_J-3157.json").exists() and G._RECOUNT_LOG.exists(), "backup + log written")
lg = json.loads(G._RECOUNT_LOG.read_text(encoding="utf-8").splitlines()[0])
check(lg["sha256_before"] != lg["sha256_after"] and lg["old"]["corroboration_count"] == 7, "log has sha before/after + old values")

print("[3] idempotent")
h = snap(G._BELIEFS)
check(G.apply_farewell_recount() == [] and snap(G._BELIEFS) == h, "second call is a no-op")

print("[4] promotion loop does not re-promote; real corroboration still can")
async def cj(base, sysp, user, **k):
    return {"relation": "assimilate"}
new_row = {"ts": 100.0, "is_guidance": True, "principle": "A wholly new independent lesson text here", "scope": "", "domain": "world", "confidence": 0.5}
G._LOG.write_text(G._LOG.read_text(encoding="utf-8") + json.dumps(new_row) + "\n", encoding="utf-8")
G._INTEG_STATE.write_text(json.dumps({"last_ts": 50.0}), encoding="utf-8")
asyncio.run(G.integrate_guidance(cj, []))
t = {b["id"]: b for b in json.loads(G._BELIEFS.read_text(encoding="utf-8"))}["g45675272"]
check(t["status"] == "tentative", "still tentative after an integration pass")
t["corroboration_count"] = 3
G._BELIEFS.write_text(json.dumps([t]), encoding="utf-8")
G._INTEG_STATE.write_text(json.dumps({"last_ts": 50.0}), encoding="utf-8")
asyncio.run(G.integrate_guidance(cj, []))
t = {b["id"]: b for b in json.loads(G._BELIEFS.read_text(encoding="utf-8"))}["g45675272"]
check(t["status"] == "promoted", "promoted again once corroboration exceeds the recount")

print("[5] canary")
check(all(snap(p) == before[p] for p in LIVE), "Du's live guidance stores unchanged")
print("ALL OK" if not FAILS else f"{FAILS} FAIL"); sys.exit(1 if FAILS else 0)

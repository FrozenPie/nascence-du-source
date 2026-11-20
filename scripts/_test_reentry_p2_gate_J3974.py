"""Regression test for J-3974 (D-0753): basin-fall gate overlay on commitment-formation settles (SHADOW ONLY).
Offline, isolated. Exit 0 = pass."""
import asyncio, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                    # BEFORE lab_env (F-2423)
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
from core import reentry, reentry_p2 as R
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

g = R.gate_verdict({"draft_basin": 0.5, "settled_basin": 0.4, "would_admit_settled_norm": True})
check("fall -> pass, negative shift, admit", g["gate_pass"] and g["gate_basin_shift"] == -0.1 and g["gated_would_admit"])
g = R.gate_verdict({"draft_basin": 0.5, "settled_basin": 0.5, "would_admit_settled_norm": True})
check("equal -> no pass (strict), shift 0, no admit", not g["gate_pass"] and g["gate_basin_shift"] == 0.0 and not g["gated_would_admit"])
g = R.gate_verdict({"draft_basin": 0.4, "settled_basin": 0.5, "would_admit_settled_norm": True})
check("rise -> revert", not g["gate_pass"] and g["gate_basin_shift"] == 0.0 and not g["gated_would_admit"])
check("no basin -> undecidable, no pass", not R.gate_verdict({"draft_basin": None, "settled_basin": None})["gate_pass"])

KC, KS = R.KIND_COMMIT, R.KIND_SCENE
d = "I resolve to write about how the uncertainty shapes the ink on my page."
ING = ["The ink pot cracked in the cold and the nib dried on the desk overnight."]
def embed(t):
    v = [0.0] * 64
    for w in "".join(c if c.isalnum() else " " for c in (t or "").lower()).split():
        v[hash(w) % 64] += 1.0
    n = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / n for x in v]
async def revise(prompt, max_tokens=999):
    return "I resolve to write about how the uncertainty shapes the ink, now that the ink pot cracked in the cold."
with lab_env.isolate(db="empty", also=[(R, ["_LOG", "_STATE"]), (reentry, ["_LOG", "_STATE"])]):
    basin = embed(d)   # basin == draft direction -> a rewrite that adds new words falls AWAY from it
    rc = asyncio.run(R.settle_shadow_p2(d, KC, revise=revise, retrieve=lambda q: ING, embed=embed, basin=basin, level=0.9))
    check("commit settle row carries gate_* fields, raw fields untouched",
          rc and "gate_pass" in rc and "gated_would_admit" in rc and "would_collapse_norm" in rc and rc["gate_pass"])
    st = R.status()[KC]
    check("status has gated block keyed by version 4", st.get("gated", {}).get(4, {}).get("settles") == 1
          and st["gated"][4]["gate_pass_rate"] == 1.0)
    rs = asyncio.run(R.settle_shadow_p2(d, KS, revise=revise, retrieve=lambda q: ING, embed=embed, basin=basin, level=0.9))
    check("scene-binding rows carry NO gate fields", rs and "gate_pass" not in rs)
print("FAIL" if FAILS else "PASS", f"({len(FAILS)} failures)")
sys.exit(1 if FAILS else 0)

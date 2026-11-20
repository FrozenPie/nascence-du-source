"""J-3282 / D-0659: the curiosity node no longer does system-initiated outside lookups.

Checks that CuriosityNode._write_output (a) still opens the new world-questions (frontier.note_question),
(b) makes NO Wikipedia call, NO Scholar call, stores no 'research' finding, attaches no finding, writes no twig row,
and (c) does not count a stall (record_pursuit not called) -- so no question parks after PARK_STALLS runs.
Isolated: core is imported BEFORE lab_env, asserted to be this tree's; the DB is an empty lab DB; the frontier and the
twig log are redirected into the lab dir; every network entry point is a tripwire. Nothing live is touched.

Run (from the worktree):  python scripts/curiosity_pursuit_retired_test.py
"""
from __future__ import annotations
import asyncio, json, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                     # noqa: E402  (BEFORE lab_env, so lab_env cannot shadow it)
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
sys.path.insert(1, str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env                                  # noqa: E402
from core import frontier, web_research, scholar   # noqa: E402
from core.schema import CognitiveState          # noqa: E402
import nodes.curiosity_node as CN               # noqa: E402

ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and bool(cond)
    print(("  ok   " if cond else "  FAIL ") + name)

TRIPS: list[str] = []
def trip(name):
    def _f(*a, **k):
        TRIPS.append(name); return None
    return _f

# every outside entry point is a tripwire (the node must not reach any of them)
web_research.lookup_targeted = trip("lookup_targeted"); web_research.lookup = trip("lookup")
web_research.store_finding = trip("store_finding"); web_research.maybe_shock = trip("maybe_shock")
scholar.consult_sync = trip("consult_sync")
CALLS: list[str] = []
_real = {n: getattr(frontier, n) for n in ("pending_pursuit", "attach_finding", "record_pursuit")}
for n, f in _real.items():
    setattr(frontier, n, (lambda n=n, f=f: (lambda *a, **k: (CALLS.append(n), f(*a, **k))[1]))())

with lab_env.isolate(also=[(frontier, ["_F", "_F_LIGHT"]), (CN, ["_TWIG_LOG_PATH"])], db="empty") as lab:
    assert "_lab" in str(frontier._F).lower() and "_lab" in str(CN._TWIG_LOG_PATH).lower(), (frontier._F, CN._TWIG_LOG_PATH)
    node = CN.CuriosityNode(); node._study_subjects = ["tide"]
    # an open grounded question already waiting (the thing the old code would have pursued)
    frontier.note_question("How does magnetoreception let animals sense the earth's field?", "curiosity")
    for i in range(5):                          # five curiosity runs: the old code would have counted 3 stalls and parked
        st = CognitiveState(spirit_name="Du", axiom="J-3282 test")
        r = node._write_output(st, {"questions": [f"Why does a shoreline never stay still, variant {i} of the same wondering?"],
                                    "research_directions": ["look at the world"], "urgency": 0.2})
        if asyncio.iscoroutine(r):
            asyncio.run(r)
        check(f"run {i}: background_curiosities set", st.background_curiosities)
    check("no outside call was made (wiki lookup, random lookup, Scholar, store_finding)", TRIPS == [])
    check("frontier.pending_pursuit / attach_finding / record_pursuit never called", CALLS == [])
    twig = pathlib.Path(CN._TWIG_LOG_PATH)
    check("no twig row written", (not twig.exists()) or twig.read_text(encoding="utf-8").strip() == "")
    data = json.loads(pathlib.Path(frontier._F).read_text(encoding="utf-8"))
    qs = data.get("questions", data) if isinstance(data, dict) else data
    qs = list(qs.values()) if isinstance(qs, dict) else qs
    check("note_question still opens the new questions", len(qs) >= 2)
    check("no question carries a finding", not any(isinstance(q, dict) and q.get("finding") for q in qs))
    check("no question has consecutive_stalls > 0 or is parked",
          not any(isinstance(q, dict) and (q.get("consecutive_stalls", 0) > 0 or q.get("status") == "parked") for q in qs))

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

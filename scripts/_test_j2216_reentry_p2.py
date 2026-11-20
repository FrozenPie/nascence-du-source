"""Regression test for J-2216: within_cycle_reentry Phase 2 SHADOW (core/reentry_p2.py) -- commitment-formation +
scene-binding re-entry with the arousal-budget coupling.

Checks (read-only on live data/: it only stats top-level files before/after):
  1. core resolves inside this worktree (import core BEFORE lab_env, F-2423);
  2. arousal_budget cut points (0 / 1 / 2 passes) and that the default path reads arousal.level(write_log=False) only;
  3. a settle under isolate() logs a shadow row with kind/budget/arousal_level/verdict; budget caps passes;
     low arousal logs an 'arousal-low' skip row and makes no LLM call; the per-kind cooldown holds;
  4. Phase 1 is untouched: core.reentry's state/log constants are never written by a Phase 2 settle;
  5. commitment arm: a gate-failing draft (load_bearing False) schedules nothing; a gate-passing one is settled from
     the scan task's done-callback, and NO commitment_ledger store is written;
  6. scene arm: stable scene / no named dissonance -> nothing; unstable + dissonance -> one scene-binding row whose
     ingredients start with the named dissonance;
  7. write fence: a non-live, non-isolated process writes nothing (guard_path refusal swallowed) even pointed at live;
  8. the two hooks are present in orchestrator.py / inner_monologue_node.py and both files compile.
Exit 0 = pass. Run from a worktree."""
import asyncio, json, os, pathlib, py_compile, sys, types
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
from core import reentry, reentry_p2, arousal, commitment_ledger
import lab_env

LIVE = pathlib.Path(r"C:\Nascence") / "data"
FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

def fp():
    out = {}
    for p in LIVE.iterdir():
        if p.is_file() and not p.name.endswith(".log"):
            st = p.stat(); out[p.name] = (st.st_size, st.st_mtime_ns)
    return out
def diff(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))

# deterministic fake primitives -------------------------------------------------------------------------------------
VOCAB = {}
def embed(text):
    v = [0.0] * 64
    for w in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split():
        v[hash(w) % 64] += 1.0
    n = sum(x * x for x in v) ** 0.5 or 1.0      # store._cosine is a plain dot product of NORMALISED vectors
    return [x / n for x in v]
CALLS = []
async def revise(prompt):
    CALLS.append(prompt)
    return "A quite different rendering of the thought, now about harbours, lanterns and rope number %d." % len(CALLS)
def retrieve_factory(items):
    return lambda q: list(items)
INGR = ["The tide tables disagree with the almanac about tonight's low water entirely.",
        "Travis said the lighthouse keeper left a ledger of storms in the shed."]
DRAFT = "I will keep the garden journal every evening, writing what grew and what the frost took."

before_all = fp()

# 2. arousal budget -------------------------------------------------------------------------------------------------
check("level 0.10 -> 0 passes", reentry_p2.arousal_budget(0.10)[0] == 0)
check("level 0.30 -> 1 pass", reentry_p2.arousal_budget(0.30)[0] == 1)
check("level 0.60 -> 2 passes", reentry_p2.arousal_budget(0.60)[0] == 2)
_seen = []
_orig_level = arousal.level
arousal.level = lambda write_log=True: (_seen.append(write_log), 0.5)[1]
n, lv = reentry_p2.arousal_budget()
arousal.level = _orig_level
check("default budget reads arousal.level(write_log=False) only", _seen == [False] and n == 2 and lv == 0.5)

# 7. fence: non-live, non-isolated, pointed at LIVE paths -> nothing written ------------------------------------------
saved = (reentry_p2._LOG, reentry_p2._STATE)
reentry_p2._LOG, reentry_p2._STATE = LIVE / "reentry_p2_shadow.jsonl", LIVE / "reentry_p2_state.json"
b = fp()
ok = reentry_p2._log_row({"x": 1})
CALLS.clear()
asyncio.run(reentry_p2.settle_shadow_p2(DRAFT, reentry_p2.KIND_COMMIT, revise=revise,
                                        retrieve=retrieve_factory(INGR), embed=embed, basin=None, level=0.6))
check("non-live _log_row refused (returns False)", ok is False)
check("non-live settle writes nothing to live data/", diff(b, fp()) == [])
reentry_p2._LOG, reentry_p2._STATE = saved

# 3-6 under isolate -------------------------------------------------------------------------------------------------
P1_STATE_BEFORE = reentry._STATE
with lab_env.isolate(db="empty", also=[(reentry_p2, ["_LOG", "_STATE"]), (reentry, ["_LOG", "_STATE"]),
                                       (commitment_ledger, ["_LEDGER", "_ACTIVE", "_OBSERVED", "_HOLDRATE_LOG"])]) as lab:
    def rows():
        try:
            return [r_ for r_ in (json.loads(l) for l in reentry_p2._LOG.read_text(encoding="utf-8").splitlines() if l.strip())
                    if r_.get("row_type") != "control"]      # J-3838: v4's control-arm rows are their own type
        except FileNotFoundError:
            return []

    # 3. high arousal: up to 2 passes, shadow row
    CALLS.clear()
    rec = asyncio.run(reentry_p2.settle_shadow_p2(DRAFT, reentry_p2.KIND_COMMIT, revise=revise,
                                                  retrieve=retrieve_factory(INGR), embed=embed, basin=None,
                                                  level=0.6, context={"cycle_id": "t1"}))
    r = rows()
    check("high-arousal settle logged one shadow row", len(r) == 1 and r[0].get("shadow") is True
          and r[0]["kind"] == "commitment-formation" and r[0]["budget"] == 2 and r[0]["arousal_level"] == 0.6)
    check("passes <= budget and >= 1", rec and 1 <= rec["passes"] <= 2 and len(CALLS) == rec["passes"] + 1)   # +1 = v4 control arm
    check("verdict fields present", rec and all(k in rec for k in ("overall_delta", "would_collapse", "would_admit_settled", "len_ratio")))
    check("revise prompt is Phase 1's NEUTRAL prompt (no check/fix framing)",
          CALLS and "Do not check it or fix it" in CALLS[0] and "Here is some additional context" in CALLS[0])
    # cooldown
    CALLS.clear()
    asyncio.run(reentry_p2.settle_shadow_p2(DRAFT, reentry_p2.KIND_COMMIT, revise=revise,
                                            retrieve=retrieve_factory(INGR), embed=embed, basin=None, level=0.6))
    check("per-kind cooldown -> skip row, no LLM call", rows()[-1].get("skip") == "cooldown" and not CALLS)
    # low arousal (scene kind has its own cooldown slot)
    CALLS.clear()
    asyncio.run(reentry_p2.settle_shadow_p2(DRAFT, reentry_p2.KIND_SCENE, revise=revise,
                                            retrieve=retrieve_factory(INGR), embed=embed, basin=None, level=0.1))
    check("low arousal -> 'arousal-low' skip row, no LLM call", rows()[-1].get("skip") == "arousal-low" and not CALLS)
    # budget 1
    st = json.loads(reentry_p2._STATE.read_text(encoding="utf-8")); st.pop("scene-binding", None)
    reentry_p2._STATE.write_text(json.dumps(st), encoding="utf-8")
    CALLS.clear()
    rec1 = asyncio.run(reentry_p2.settle_shadow_p2(DRAFT, reentry_p2.KIND_SCENE, revise=revise,
                                                   retrieve=retrieve_factory(INGR), embed=embed, basin=None, level=0.3))
    check("mid arousal -> budget 1, exactly one pass", rec1 and rec1["budget"] == 1 and rec1["passes"] == 1 and len(CALLS) == 1)

    # 4. Phase 1 untouched
    check("Phase 1 state/log never written by Phase 2", not reentry._STATE.exists() and not reentry._LOG.exists())

    # 5. commitment arm via done-callback
    reentry_p2._STATE.write_text("{}", encoding="utf-8")
    prims = lambda topic="", extra=None, kind=None: (revise, retrieve_factory(list(extra or []) + INGR), embed)
    _orig_prims = reentry_p2._default_primitives
    reentry_p2._default_primitives = prims
    async def run_commit(data):
        fut = asyncio.get_running_loop().create_future(); fut.set_result(data)
        reentry_p2.on_commitment_scan_done(fut, "a thought about the journal", "c9")
        await asyncio.sleep(0)
        await asyncio.gather(*list(reentry_p2._TASKS))
    n0 = len(rows())
    asyncio.run(run_commit({"new_commitment": {"statement": "I want to comb the tideline again", "load_bearing": False}}))
    check("gate-failing draft (not load-bearing) schedules nothing", len(rows()) == n0)
    CALLS.clear()
    asyncio.run(run_commit({"new_commitment": {"statement": DRAFT, "scope": "evenings", "load_bearing": True}}))
    last = rows()[-1]
    check("gate-passing draft settled from the scan's done-callback",
          last.get("kind") == "commitment-formation" and last.get("cycle_id") == "c9" and last.get("scope") == "evenings")
    check("no commitment_ledger store written", not any(p.exists() for p in (commitment_ledger._LEDGER, commitment_ledger._ACTIVE,
                                                                         commitment_ledger._OBSERVED, commitment_ledger._HOLDRATE_LOG)))

    # 6. scene arm
    reentry_p2._STATE.write_text("{}", encoding="utf-8")
    sc = types.SimpleNamespace(scene="The study is warm but the letter on the desk says the boat never came back to harbour.",
                               dissonance=["He expected the boat; the letter says it sank."], coherence=0.31)
    async def run_scene(scene, unstable):
        r_ = reentry_p2.on_scene_bound(scene, unstable=unstable, topic="the boat", cycle_id="s1", passes_used=1)
        await asyncio.sleep(0)
        await asyncio.gather(*list(reentry_p2._TASKS))
        return r_
    orig_budget = reentry_p2.arousal_budget
    reentry_p2.arousal_budget = lambda level=None: (2, 0.55)
    n0 = len(rows())
    s1 = asyncio.run(run_scene(sc, False))
    s2 = asyncio.run(run_scene(types.SimpleNamespace(scene=sc.scene, dissonance=[], coherence=0.3), True))
    check("stable scene / no named dissonance -> nothing scheduled", s1 is False and s2 is False and len(rows()) == n0)
    CALLS.clear()
    s3 = asyncio.run(run_scene(sc, True))
    last = rows()[-1]
    check("unstable scene with dissonance -> one scene-binding row", s3 is True and last.get("kind") == "scene-binding"
          and last.get("dissonance_n") == 1 and last.get("coherence") == 0.31 and "passes" in last)
    check("first ingredient is the scene's named dissonance", last.get("ingredients", [""])[0].startswith("He expected the boat"))
    reentry_p2.arousal_budget = orig_budget
    reentry_p2._default_primitives = _orig_prims

    st = reentry_p2.status()
    check("status() reads both kinds", st["commitment-formation"]["settles"] >= 2 and st["scene-binding"]["settles"] >= 2)
    print("  status:", json.dumps(st))

check("Phase 1 module constants restored after isolate", reentry._STATE == P1_STATE_BEFORE)
check("whole test left live data/ top level unchanged (changed: %s)" % diff(before_all, fp()), diff(before_all, fp()) == [])

# 8. hooks present + compile
orch = (HERE / "core" / "orchestrator.py").read_text(encoding="utf-8")
imn = (HERE / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
check("orchestrator scene hook present", "_re2.on_scene_bound(" in orch)
check("inner_monologue commitment hook present", "_re2.on_commitment_scan_done(" in imn)
check("Phase 1 REENTRY_ADMIT is False (D-0540, J-3148) and MAX_PASSES unchanged", reentry.REENTRY_ADMIT is False and reentry.MAX_PASSES == 2)
for f in ("core/orchestrator.py", "nodes/inner_monologue_node.py", "core/reentry_p2.py"):
    try:
        py_compile.compile(str(HERE / f), doraise=True); check("compiles: " + f, True)
    except Exception as exc:
        check("compiles: %s (%s)" % (f, exc), False)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)

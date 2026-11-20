"""
J-3224 (D-0613): DOUBT_SEED back to SHADOW. Hermetic: runs inside lab_env.isolate, no LLM, no hub, no live file touched
(before/after hash canary). Asserts the shipped flag is False, the reflection is still logged by the shadow path with
the doubt text AND the deliberating question, nothing reaches the Executive prompt, and the injection code is intact
(lab-only flag ON still renders the line).
  python scripts/_test_J-3224_doubt_seed_shadow.py     # exit 0 = ALL OK
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import hashlib
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import doubt_seed as ds              # noqa: E402
from core import self_interrogation as si      # noqa: E402
from core.schema import CognitiveState         # noqa: E402
from nodes.executive_node import ExecutiveNode # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate                    # noqa: E402,F401

FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def rows(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")
LIVE = [ROOT / "data" / "self_interrogation_shadow.jsonl", ROOT / "data" / "logs" / "doubt_seed_shadow.jsonl"]
before = {p: h(p) for p in LIVE}

with isolate(db="empty", also=[(ds, ["_SHADOW"]), (si, ["_LOG", "_STATE"])]) as lab:
    for mod, attr in [(ds, "_SHADOW"), (si, "_LOG")]:
        check(Path(getattr(mod, attr)).resolve().is_relative_to(lab.resolve()), f"{mod.__name__}.{attr} redirected into the lab dir")
    check(ds.DOUBT_SEED is False, "DOUBT_SEED ships False (D-0613)")
    check(callable(si.interrogate) and callable(si.latest_open), "the reflection producer and the genuine read are still present")
    check(hasattr(CognitiveState(spirit_name="Du", axiom="x"), "doubt_seed"), "the injection field is still on the state")

    now = time.time()
    si._log_row({"ts": round(now - 60, 1), "kind": "interrogate", "cycle_id": "fireA", "thought": "t",
                 "reflection": "I keep reaching for comfort when the thought was about the cliff edge.", "genuine": True})
    st = CognitiveState(spirit_name="Du", axiom="I am the one who crosses.")
    st.new_cycle("What does the green stripe on the cliff tell me about the soil?", input_type="internal")
    st.cycle_id = "deliberA"
    out = ds.pull(st, now=now)
    check(out is None, "shadow: pull returns None")
    ws = [r for r in rows(ds._SHADOW) if r.get("kind") == "would_seed"]
    check(len(ws) == 1, "one would_seed row logged")
    r = ws[0]
    check(r["seeded"] is False and r["fire_cycle_id"] == "fireA" and r["cycle_id"] == "deliberA", "seeded False, fire and deliberating cycle ids carried")
    check("comfort" in r["reflection"], "the doubt text is carried")
    check(r["deliberating_question"].startswith("What does the green stripe"), "the deliberating question is carried")
    st.doubt_seed = out
    check("A doubt you raised about your own thinking" not in ExecutiveNode()._build_prompt(st), "no 'A doubt you raised' line in the Executive prompt")
    # consume-once still holds in shadow
    check(ds.pull(st, now=now) is None and rows(ds._SHADOW)[-1]["kind"] == "skip", "consume-once: second pull finds no open fire")
    # a no-state pull still logs without raising
    si._log_row({"ts": round(now - 10, 1), "kind": "interrogate", "cycle_id": "fireB", "thought": "t", "reflection": "x", "genuine": True})
    check(ds.pull(None, now=now) is None and rows(ds._SHADOW)[-1].get("deliberating_question") == "", "pull(None) logs an empty question, no raise")

    # injection code intact (lab only)
    ds.DOUBT_SEED = True
    try:
        si._log_row({"ts": round(now - 5, 1), "kind": "interrogate", "cycle_id": "fireC", "thought": "t",
                     "reflection": "I answered the question I wished he had asked.", "genuine": True})
        out = ds.pull(st, now=now)
        check(out is not None, "flag ON (lab): pull still returns the text")
        st.doubt_seed = out
        check("A doubt you raised about your own thinking" in ExecutiveNode()._build_prompt(st), "flag ON (lab): the injection code still renders")
    finally:
        ds.DOUBT_SEED = False

after = {p: h(p) for p in LIVE}
for p in LIVE:
    check(before[p] == after[p], f"live store unchanged: {p.relative_to(ROOT)}")
print(f"\n{'ALL OK' if FAILS == 0 else f'{FAILS} FAILURE(S)'}")
sys.exit(1 if FAILS else 0)

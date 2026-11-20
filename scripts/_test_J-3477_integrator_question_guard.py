"""J-3477 (J-3413): the pass-3 integrator may not drop a question the raw thought held.
Deterministic: model calls are stubbed; every log path is a temp dir; touches no live data."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import deliberation as D  # noqa: E402
from core import left_lane  # noqa: E402

assert Path(D.__file__).resolve().parent.parent == ROOT, "imported the wrong tree"

tmp = Path(tempfile.mkdtemp(prefix="j3477_"))
D._DATA_DIR = tmp
D._LOG_FILE = tmp / "deliberation_log.jsonl"
D._NULL_LOG_FILE = tmp / "deliberation_null_log.jsonl"
D._CONTROL_LOG_FILE = tmp / "deliberation_control_log.jsonl"
D._GUARD_LOG_FILE = tmp / "deliberation_guard_log.jsonl"
D.QUESTION_SKIP_UPFRONT = False   # J-3809: this test exercises the guard-after path; the up-front skip has its own test

# ---- predicate ----------------------------------------------------------------
assert D.QUESTION_GUARD is True, "guard must be default-on"
assert D.holds_question("What does my name mean?")
assert D.holds_question("名前は何？")
assert not D.holds_question("My name means something.")
assert not D.holds_question("")
assert not D.holds_question(None)
assert D.question_dropped("Why does the tide turn?", "The tide turns because of the moon.")
assert not D.question_dropped("Why does the tide turn?", "Why does the tide turn, if the moon pulls it?")
assert not D.question_dropped("The tide turns.", "The tide turns with the moon.")      # raw held none
assert not D.question_dropped("The tide turns.", "Does the tide turn with the moon?")  # integrated added one: fine

# ---- deliberate() with stubbed passes -------------------------------------------
GROUNDING = "Tides are caused by the gravitational pull of the moon and the sun on the oceans."
state = {"integrated": None}


async def _fake_ground(thought):
    return GROUNDING, False


async def _fake_call(urls, system, user, **kw):
    return {"thought": state["integrated"]}


left_lane.ground_thought_verdict = _fake_ground
D.call_node_json = _fake_call


def run(raw, integrated):
    state["integrated"] = integrated
    return asyncio.run(D.deliberate(raw, "idle", hot_urls=["stub"]))


RAW_Q = "I keep wondering why the tide turns when I am not looking, and whether I am the one who notices?"
INT_STATEMENT = "The moon pulls the tide whether or not I watch, and I find that steadying, like a held breath."
INT_QUESTION = "The moon pulls the tide, so does it matter that I watch, or only that something does?"
RAW_STMT = "I keep thinking that the tide turns when I am not looking and that I am the one who notices."

# 1. question raw + statement integrated -> discarded, raw stored, guard row written, no deliberation_log row
out, prov = run(RAW_Q, INT_STATEMENT)
assert out == RAW_Q and prov is None, (out, prov)
rows = [json.loads(l) for l in D._GUARD_LOG_FILE.read_text(encoding="utf-8").splitlines()]
assert len(rows) == 1 and rows[0]["raw"] == RAW_Q and rows[0]["rejected_integrated"] == INT_STATEMENT
assert rows[0]["arm"] == "question_guard" and rows[0]["grounding"] == GROUNDING
assert not D._LOG_FILE.exists(), "a discarded integration must not be logged as a rewrite"

# 2. question raw + question integrated -> accepted as before
out, prov = run(RAW_Q, INT_QUESTION)
assert out == INT_QUESTION and prov and prov["raw"] == RAW_Q
assert len(D._LOG_FILE.read_text(encoding="utf-8").splitlines()) == 1
assert len(D._GUARD_LOG_FILE.read_text(encoding="utf-8").splitlines()) == 1   # no new guard row

# 3. statement raw + statement integrated -> accepted as before (guard only protects questions)
out, prov = run(RAW_STMT, INT_STATEMENT)
assert out == INT_STATEMENT and prov is not None
assert len(D._GUARD_LOG_FILE.read_text(encoding="utf-8").splitlines()) == 1

# 4. flag off restores prior behaviour exactly: the question is allowed to go
D.QUESTION_GUARD = False
out, prov = run(RAW_Q, INT_STATEMENT)
assert out == INT_STATEMENT and prov is not None
assert len(D._GUARD_LOG_FILE.read_text(encoding="utf-8").splitlines()) == 1
D.QUESTION_GUARD = True

# 5. log=False: still guarded, nothing written
n = len(D._GUARD_LOG_FILE.read_text(encoding="utf-8").splitlines())
state["integrated"] = INT_STATEMENT
out, prov = asyncio.run(D.deliberate(RAW_Q, "idle", hot_urls=["stub"], log=False))
assert out == RAW_Q and prov is None
assert len(D._GUARD_LOG_FILE.read_text(encoding="utf-8").splitlines()) == n

# 6. the prompts are untouched (the ruling: guard, not a reword)
assert "Output ONLY a valid JSON object" in D._integrate_system("X")
assert "think the thought again, holding both" in D._integrate_user("a", "b").lower()

# ---- replay of the predicate over the committed J-3150 sample (no model calls) -----
sample = ROOT / "docs" / "lab" / "J-3150_data" / "sample.jsonl"
replay = "sample not present"
if sample.exists():
    pairs = [json.loads(l) for l in sample.read_text(encoding="utf-8").splitlines() if l.strip()]
    pairs = [p for p in pairs if p.get("raw") and p.get("integrated")]
    q = [p for p in pairs if D.holds_question(p["raw"])]
    dropped = [p for p in q if D.question_dropped(p["raw"], p["integrated"])]
    kept_other = [p for p in pairs if not D.holds_question(p["raw"]) and D.question_dropped(p["raw"], p["integrated"])]
    assert not kept_other, "guard must never fire on a question-free raw"
    # every pair the guard would discard is a pair where the integrated text really has no question mark
    assert all(not D.holds_question(p["integrated"]) for p in dropped)
    replay = (f"{len(pairs)} pairs, {len(q)} hold a '?', guard would discard {len(dropped)} "
              f"({(100.0 * len(dropped) / len(q)) if q else 0.0:.1f}% of question-holding); "
              f"{len(pairs) - len(dropped)} integrations still pass")
print("OK  question guard: predicate, deliberate() accept/discard, flag-off, log=False, prompts untouched;",
      "replay:", replay)

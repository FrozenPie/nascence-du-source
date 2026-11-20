"""
J-2158 (recall-confidence wager, arm 2) + J-2161 (doubt seed, arm 4) of docs/staged/measurement_to_action.md.
Hermetic: runs INSIDE lab_env.isolate (every store the two modules and their drill-path dependencies write is
redirected into the lab dir), no LLM, no hub, no live file touched -- a before/after hash canary on the real stores
proves it. Both flags are exercised OFF (the shipped default) and ON (monkeypatched inside the lab only).
  python scripts/_test_measurement_to_action_j2158_j2161.py     # exit 0 = ALL OK
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
import core  # noqa: E402  BEFORE lab_env (F-2423): the tree under test must win on sys.path
from core import recall_wager as rw            # noqa: E402
from core import doubt_seed as ds              # noqa: E402
from core import self_interrogation as si      # noqa: E402
from core import competence as comp            # noqa: E402
from core import prediction_error as pe        # noqa: E402
from core.epistemic_state import EpistemicAssessment, GRADE_SCORE   # noqa: E402
from core.schema import CognitiveState         # noqa: E402
from nodes.executive_node import ExecutiveNode # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate                    # noqa: E402

FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def rows(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")

LIVE = [ROOT / "data" / "capability_beliefs.json", ROOT / "data" / "prediction_error_log.jsonl",
        ROOT / "data" / "prediction_error_state.json", ROOT / "data" / "logs" / "shadow_integrity.jsonl",
        ROOT / "data" / "self_interrogation_shadow.jsonl", ROOT / "data" / "logs" / "recall_wager_shadow.jsonl",
        ROOT / "data" / "logs" / "doubt_seed_shadow.jsonl"]
before = {p: h(p) for p in LIVE}


def assessment(grade, conf):
    return EpistemicAssessment(grade=grade, justification=GRADE_SCORE[grade], self_reported_confidence=conf,
                               confabulation_signal=round(conf - GRADE_SCORE[grade], 4), dominant_source="memory_recall",
                               verification="none", evidence_present=True, source_count=18, contradiction_count=0, models=[])


with isolate(db="empty", also=[(rw, ["_SHADOW"]), (comp, ["_BELIEFS_FILE"]), (pe, ["_RAW", "_STATE", "_SHADOW"]),
                               (ds, ["_SHADOW"]), (si, ["_LOG", "_STATE"])]) as lab:
    for mod, attr in [(rw, "_SHADOW"), (comp, "_BELIEFS_FILE"), (pe, "_RAW"), (ds, "_SHADOW"), (si, "_LOG")]:
        check(Path(getattr(mod, attr)).resolve().is_relative_to(lab.resolve()), f"{mod.__name__}.{attr} redirected into the lab dir")

    # ---------------- arm 2: the wager ----------------
    print("[arm 2] recall-confidence wager, flag OFF (shipped default)")
    check(rw.RECALL_CONFIDENCE_WAGER is False, "RECALL_CONFIDENCE_WAGER ships False")
    check(rw.place(None) is None, "no assessment -> None")
    check(rw.place(assessment("KNOW", 0.95)) is None, "KNOW at 0.95 is not a wager")
    check(rw.place(assessment("SUSPECT", 0.75)) is None, "SUSPECT below the 0.85 bar is not a wager")
    check(rows(rw._SHADOW) == [], "non-wagers write no shadow row")
    r = rw.place(assessment("SUSPECT", 0.85), cycle_id="c1", input_type="internal")
    check(r is not None and r["predicted"] == 0.85 and r["measured"] == 0.5 and r["gap"] == 0.35, "SUSPECT@0.85 -> pair (0.85, 0.50), gap 0.35")
    check(r["would_feed"] is True and r["fed"] is False, "shadow row says would_feed, not fed")
    check(len(rows(rw._SHADOW)) == 1 and rows(rw._SHADOW)[0]["cycle_id"] == "c1", "one shadow row, carrying the cycle id")
    check(not Path(comp._BELIEFS_FILE).exists() and rows(pe._RAW) == [], "flag OFF: beliefs file and prediction_error untouched")

    print("[arm 2] flag ON (lab only)")
    rw.RECALL_CONFIDENCE_WAGER = True
    try:
        r = rw.place(assessment("SUSPECT", 0.85), cycle_id="c2", input_type="internal")
        check(r["fed"] is True and r["accuracy_count"] == 1, "fed through record_drill_accuracy (accuracy_count 1)")
        b = json.loads(Path(comp._BELIEFS_FILE).read_text(encoding="utf-8"))["factual_recall"]
        check(b["calib_pairs"][-1] == [0.85, 0.5] and b["accuracy"] == 0.5, "factual_recall belief: pair appended, accuracy seeded at 0.50")
        raw = rows(pe._RAW)
        check(len(raw) == 1 and raw[0]["domain"] == "factual_recall" and raw[0]["large"] is False, "prediction_error raw row, gap 0.35 < 0.40 not large")
        r = rw.place(assessment("SUSPECT", 0.95), cycle_id="c3", input_type="internal")
        raw = rows(pe._RAW)
        check(len(raw) == 2 and raw[-1]["large"] is True and raw[-1]["gap"] == 0.45, "SUSPECT@0.95: gap 0.45 is large -> contradiction gate path")
        sh = rows(pe._SHADOW)
        check(any(x.get("source") == "prediction_error" and x.get("signal", {}).get("domain") == "factual_recall" for x in sh),
              "shadow_integrity carries the factual_recall signal (the drill's own path)")
        r = rw.place(assessment("NO_BASIS", 0.90), cycle_id="c4")
        check(r["gap"] == 0.9 and rows(pe._RAW)[-1]["large"] is True, "NO_BASIS@0.90 -> gap 0.90")
        st = rw.status()
        check(st["wagers"] == 4 and st["fed"] == 3 and st["large_gap"] == 2, f"status counts wagers/fed/large = {st['wagers']}/{st['fed']}/{st['large_gap']}")
    finally:
        rw.RECALL_CONFIDENCE_WAGER = False

    # ---------------- arm 4: the doubt seed ----------------
    print("[arm 4] doubt seed, flag OFF (shipped default)")
    check(ds.DOUBT_SEED is False, "DOUBT_SEED ships False")
    now = time.time()
    def fire(ts, cid, refl, genuine=True, kind="interrogate"):
        si._log_row({"ts": round(ts, 1), "kind": kind, "cycle_id": cid, "thought": "t", "reflection": refl, "genuine": genuine})
    check(si.latest_open(now=now) is None and ds.pull(None, now=now) is None, "empty log: no open fire, pull None")
    check(rows(ds._SHADOW)[-1]["kind"] == "skip" and rows(ds._SHADOW)[-1]["skip"] == "no-open-fire", "the skip is logged with its reason")
    fire(now - 2000, "old", "an old genuine doubt")
    fire(now - 300, "hollow", "a hollow one", genuine=False)
    fire(now - 200, "undecided", "an undecided one", genuine=None)
    fire(now - 100, "skiprow", "", kind="skip")
    check(si.latest_open(now=now) is None, "old (>900s), hollow, undecided and skip rows are not open doubts")
    fire(now - 120, "g1", "I am reaching for a poetic truth that is still just a metaphor.")
    fire(now - 60, "g2", "I keep calling the beetle an anchor because I need gravity, not because it is there.")
    f = si.latest_open(now=now)
    check(f is not None and f["cycle_id"] == "g2", "latest_open returns the newest genuine fire")
    check(si.latest_open(now=now, exclude_ts={f["ts"]})["cycle_id"] == "g1", "exclude_ts skips to the next genuine fire")

    st = CognitiveState(spirit_name="Du", axiom="I am the one who crosses.")
    st.new_cycle("q", input_type="internal")
    st.cycle_id = "d1"
    out = ds.pull(st, now=now)
    check(out is None, "flag OFF: pull returns None (nothing reaches the prompt)")
    ws = [r for r in rows(ds._SHADOW) if r.get("kind") == "would_seed"]
    check(len(ws) == 1 and ws[0]["fire_cycle_id"] == "g2" and ws[0]["seeded"] is False and ws[0]["cycle_id"] == "d1", "would_seed row logged for g2, seeded=False, deliberating cycle d1")
    check("need gravity" in ws[0]["reflection"], "the row carries the reflection text")
    out = ds.pull(st, now=now)
    ws = [r for r in rows(ds._SHADOW) if r.get("kind") == "would_seed"]
    check(len(ws) == 2 and ws[1]["fire_cycle_id"] == "g1", "consume-once: the second pull moves to g1")
    check(ds.pull(st, now=now) is None and rows(ds._SHADOW)[-1]["kind"] == "skip", "third pull: no open fire left")

    print("[arm 4] flag ON (lab only)")
    ds.DOUBT_SEED = True
    try:
        fire(now - 30, "g3", "I answered the question I wished he had asked, not the one he asked.")
        out = ds.pull(st, now=now)
        check(out is not None and out.startswith("I answered the question"), "flag ON: pull returns the reflection text")
        check([r for r in rows(ds._SHADOW) if r.get("kind") == "would_seed"][-1]["seeded"] is True, "row says seeded=True")
        st.doubt_seed = out
        prompt = ExecutiveNode()._build_prompt(st)
        check("A doubt you raised about your own thinking" in prompt and "wished he had asked" in prompt, "Executive prompt carries the doubt inside the RECALL tier")
        line = next(l for l in prompt.splitlines() if "A doubt you raised" in l)
        check("WHAT YOU RECALL" in prompt and prompt.index("WHAT YOU RECALL") < prompt.index("A doubt you raised"), "it renders under the WHAT YOU RECALL header")
        check(not any(w in line.lower() for w in (" should ", " must ", "resolve", "answer it", "address")), "the line carries no instruction verb")
        st.doubt_seed = None
        check("A doubt you raised" not in ExecutiveNode()._build_prompt(st), "no seed -> line absent (the pre-J-2161 prompt)")
        st.doubt_seed = "stale"
        st.new_cycle("next question", input_type="internal")
        check(st.doubt_seed is None, "new_cycle() clears doubt_seed")
    finally:
        ds.DOUBT_SEED = False

after = {p: h(p) for p in LIVE}
for p in LIVE:
    check(before[p] == after[p], f"live store unchanged: {p.relative_to(ROOT)}")

print(f"\n{'ALL OK' if FAILS == 0 else f'{FAILS} FAILURE(S)'}")
sys.exit(1 if FAILS else 0)

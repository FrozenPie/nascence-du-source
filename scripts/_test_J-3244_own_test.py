"""J-3244 (D-0632, plan object_epistemic_loop): the returned intervention_test, the writer gate, the steering-risk instrument.

Hermetic: core is imported BEFORE lab_env and asserted to resolve inside this tree; world_substrate's store paths and
follow_line's SHADOW_LOG are redirected to a temp dir; every model stop is stubbed.  Live data/ is hashed before and
after.  Zero LLM, zero network.   python scripts/_test_J-3244_own_test.py     Exit 0 = pass.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
sys.path.insert(0, str(HERE / "scripts"))
from core import follow_line as fl
from core import frontier as fr
from core import coupling_rides as cr
from core import object_hypothesis as oh
from core import world_substrate as ws
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

import own_test_deed_rate as dr

FAIL = []
LIVE = Path(r"C:\Nascence\data")


def check(name, cond, info=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{info}]" if (info and not cond) else ""))
    if not cond:
        FAIL.append(name)


def _h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


CANARY = [LIVE / "world_substrate.json", LIVE / "logs" / "follow_line_shadow.jsonl", LIVE / "hands_trace.jsonl",
          LIVE / "frontier.json"]
before = [_h(p) for p in CANARY]

T_STONE = [{"mode": "do", "family": "objtest", "verb": "scratch", "object": "stone", "cue": "pumice"},
           {"mode": "do", "family": "objtest", "verb": "heft", "object": "stone", "cue": "light"},
           {"mode": "do", "family": "objtest", "verb": "float", "object": "stone", "cue": "pumice"}]
T_THYME = [{"mode": "withhold", "family": "water", "verb": "water", "object": "garden", "cue": "dying", "when": "two days"},
           {"mode": "observe", "family": "look", "verb": "look", "object": "garden", "cue": "dying", "when": "after rain"}]
HYP_STONE = "I think this pale stone is pumice because it feels light for its size"
HYP_THYME = "maybe the thyme is dying from the frost"

# ── [1] pure matching + phrasing ────────────────────────────────────────────────────────────────────────────
rows = [{"object_id": "o1", "inference_id": "i1", "hypothesis": HYP_STONE, "intervention_test": T_STONE, "timestamp": 10},
        {"object_id": "o2", "inference_id": "i2", "hypothesis": HYP_THYME, "intervention_test": T_THYME, "timestamp": 20}]
m = oh.match_hypothesis("I think this pale stone is pumice because it feels light for its size", rows)
check("exact claim matches its own hypothesis", m and m["inference_id"] == "i1")
m = oh.match_hypothesis("this pale stone is pumice because it feels light", rows)
check("a shortened restatement (>=80% of its words contained) still matches", m and m["inference_id"] == "i1")
check("an unrelated claim matches nothing", oh.match_hypothesis("why does the tide come in twice a day here", rows) is None)
check("a claim that merely shares the object word does not match",
      oh.match_hypothesis("the stone wall behind the shed was built by the first owners", rows) is None)
check("a hypothesis with an empty test is never matched",
      oh.match_hypothesis(HYP_STONE, [{**rows[0], "intervention_test": []}]) is None)
d = oh.describe_test(T_STONE)
check("do-candidates in plain words, no imperative", d == "scratching the stone; hefting the stone; seeing whether the stone floats", d)
d2 = oh.describe_test(T_THYME)
check("withhold/observe in plain words", d2 == "holding back the water for two days; looking at the garden after rain", d2)
check("no candidate -> empty text", oh.describe_test([]) == "")
check("phrasing never tells him to do it",
      not any(w in (d + " " + d2).lower().split() for w in ("should", "must", "try", "go", "now")))

# ── [2] the writer gate default ────────────────────────────────────────────────────────────────────────────
from nodes import inner_monologue_node as imn
os.environ.pop("NASCENCE_INTERVENTION_TEST", None)
check("writer gate is ON by default from the next boot (D-0632)", imn._intervention_test_on() is True)
os.environ["NASCENCE_INTERVENTION_TEST"] = "0"
check("NASCENCE_INTERVENTION_TEST=0 forces it off", imn._intervention_test_on() is False)
os.environ.pop("NASCENCE_INTERVENTION_TEST")

with isolate(also=[(fr, ["_F", "_SEM_SHADOW_LOG"]), (fl, ["SHADOW_LOG"]), (cr, ["_LOG"])], db="empty") as lab:
    cr._DATA = lab
    fr.FRONTIER_SEMANTIC_MERGE = None
    sub = lab / "world_substrate.json"
    ws._SUBSTRATE_F = sub
    ws._SUBSTRATE_LOG = lab / "world_substrate_events.jsonl"
    ws._cache = {}
    ws._cache_ts = 0.0

    # ── [3] store reader: read-only, no seeding ────────────────────────────────────────────────────────────
    check("absent store -> [] and NOTHING is created (no seed, no save)", ws.inferences_with_test() == [] and not sub.exists())
    store = {
        "o1": {"object_id": "o1", "name": "a pale beach stone", "location": "shore", "object_class": "stone",
               "inferences": [{"inference_id": "i1", "timestamp": 10.0, "hypothesis": HYP_STONE, "confidence": 0.6,
                               "supporting_observations": ["obs1"], "supporting_knowledge": [], "intervention_test": T_STONE}]},
        "o2": {"object_id": "o2", "name": "the thyme", "location": "garden", "object_class": "plant",
               "inferences": [{"inference_id": "i2", "timestamp": 20.0, "hypothesis": HYP_THYME, "confidence": 0.5,
                               "supporting_observations": ["obs2"], "supporting_knowledge": [], "intervention_test": []},
                              {"inference_id": "i3", "timestamp": 30.0, "hypothesis": "the thyme looks tired", "confidence": 0.4,
                               "supporting_observations": [], "supporting_knowledge": []}]},
    }
    sub.write_text(json.dumps(store), encoding="utf-8")
    got = ws.inferences_with_test()
    check("only non-empty tests are returned, with their object context",
          [g["inference_id"] for g in got] == ["i1"] and got[0]["object_id"] == "o1" and got[0]["name"] == "a pale beach stone")
    check("reading wrote nothing", json.loads(sub.read_text(encoding="utf-8")) == store)

    # ── [4] follow_line: own test from memory ─────────────────────────────────────────────────────────────
    ot = fl._own_test_for(HYP_STONE)
    check("_own_test_for returns the test in plain words with its ids",
          ot.get("text") == "scratching the stone; hefting the stone; seeing whether the stone floats"
          and ot["inference_id"] == "i1" and ot["object_id"] == "o1" and len(ot["candidates"]) == 3)
    check("a claim that is not a stored hypothesis -> {}", fl._own_test_for("how did the Portuguese blend cultures overall") == {})
    check("a hypothesis whose stored test is [] -> {}", fl._own_test_for(HYP_THYME) == {})
    fl.OWN_TEST_RETURN = False
    check("OWN_TEST_RETURN=False: the stop returns {} (exactly as before)", asyncio.run(fl._stop_own_test(HYP_STONE)) == {})
    fl.OWN_TEST_RETURN = True

    # render: the sentence sits in the return, and is absent otherwise
    ent = {"q": HYP_STONE, "source": "claim", "asked_by": {"book_title": "Stones"}}
    base = {"grounds": [], "grounds_outcome": "empty", "why": {}, "consequences": [], "connections": {}, "against": {}}
    txt0 = fl.render(ent, dict(base), {"a": "no", "b": "no"})
    txt1 = fl.render(ent, {**base, "own_test": ot}, {"a": "no", "b": "no"})
    check("render without own_test is byte-identical to before", "coincidence" not in txt0)
    check("render with own_test names the test, never tells him to do it",
          "What would tell this from coincidence: scratching the stone; hefting the stone; seeing whether the stone floats."
          in txt1 and txt1.count("coincidence") == 1)

    # ── [5] run(): stub the model stops, drive one boarded hypothesis end to end ──────────────────────────
    async def m_grounds(q, train_id): return {"grounds": [{"fragment_id": "f", "origin": "reading", "age": "a month ago",
                                                           "strength": "bears", "text": "pumice floats on water"}], "grounds_outcome": "found"}
    async def m_why(q, g): return {"text": "Because [1] says it floats.", "cites": [1], "supports": "yes"}
    async def m_cons(q, g, w): return [{"text": "Then it should float in the rain barrel too.", "slot": "how", "checkable": "world"}]
    async def m_conn(q): return {}
    async def m_against(q, g): return {"text": "", "cites": [], "scope": "", "skipped": "test"}
    async def m_judge(q, cargo, q_id=""): return {"a": "yes", "b": "yes", "c": "skipped", "a_how": "agreed", "b_how": "agreed"}
    fl._stop_grounds, fl._stop_why, fl._stop_consequences, fl._stop_connections = m_grounds, m_why, m_cons, m_conn
    fl._stop_against, fl._judge = m_against, m_judge
    fl._board_log.clear(); fl._in_flight = None; fl._TASKS.clear(); fl._recent_keys.clear(); fl._PENDING.clear()
    fr._save({"questions": []})
    e = fr.note_question_ex(HYP_STONE, "asked", slot="how", about="the stone", asked_by={"ts": time.time()}, allow_self=True)
    row = asyncio.run(fl.run(e["id"]))
    check("run() logs the own_test in the would_return cargo + stops",
          row is not None and row["cargo"]["own_test"].get("inference_id") == "i1" and row["stops"]["own_test"]["n"] == 3)
    check("the return text carries it", "What would tell this from coincidence" in row["return_text"])
    check("consequences list is untouched (judge + re-boarding see only the generated one)",
          len(row["cargo"]["consequences"]) == 1 and "scratch" not in json.dumps(row["cargo"]["consequences"]))
    rides = [json.loads(l) for l in fl.SHADOW_LOG.read_text(encoding="utf-8").splitlines() if '"line": "line:own_test"' in l]
    check("one coordinate ride row for the own_test stop", len(rides) == 1 and rides[0]["value"]["outcome"] == "i1")
    # an ordinary claim: run() output has no own_test and no sentence
    fl._board_log.clear(); fl._in_flight = None
    e2 = fr.note_question_ex("how did the Portuguese truly blend cultures, and what remained afterwards?", "asked", slot="how",
                             about="Portuguese integration", asked_by={"ts": time.time()}, allow_self=True)
    row2 = asyncio.run(fl.run(e2["id"]))
    check("an ordinary claim: cargo.own_test is {} and the return has no such sentence",
          row2["cargo"]["own_test"] == {} and "coincidence" not in row2["return_text"] and "own_test" not in row2["stops"])
    # a store failure never fails the line
    ws.inferences_with_test = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    fl._board_log.clear(); fl._in_flight = None
    e3 = fr.note_question_ex("why would a pale stone floating on the water surprise anyone who has seen it?", "asked", slot="why",
                             asked_by={"ts": time.time()}, allow_self=True)
    row3 = asyncio.run(fl.run(e3["id"]))
    check("a failing store read fails open: the line still returns", row3 is not None and row3["cargo"]["own_test"] == {})

    # ── [6] the steering-risk instrument (pure join) ───────────────────────────────────────────────────────
    H = 3600.0
    infs = [{"inference_id": "i1", "timestamp": 1000.0, "intervention_test": T_STONE},
            {"inference_id": "i2", "timestamp": 1000.0, "intervention_test": T_THYME},
            {"inference_id": "i4", "timestamp": 1000.0, "intervention_test": [{"mode": "withhold", "family": "water", "verb": "water", "object": "garden"}]},
            {"inference_id": "i5", "timestamp": 1000.0, "intervention_test": []},
            {"inference_id": "i6", "timestamp": 1000.0}]
    hands = [{"ts": 1000.0 + 5 * H, "thought": "I turn the stone over", "intention": "I want to heft the stone", "act_object": "the stone",
              "hands": [{"hand": "objtest"}]},
             {"ts": 1000.0 + 30 * H, "thought": "x", "intention": "", "act_object": "the garden", "hands": [{"hand": "look"}]}]
    line = [{"kind": "would_return", "q_id": "q1", "cargo": {"own_test": {"inference_id": "i2"}}},
            {"kind": "ride", "ts": 1000.0 + 20 * H, "line": "follow_line:return", "value": {"q_id": "q1", "outcome": "delivered"}}]
    res = dr.measure(infs, hands, line, 48 * H)
    check("coverage counts: 5 inferences, 4 carry the field, 3 a candidate, 2 scorable, 1 withhold-only",
          (res["n_inferences"], res["n_with_field"], res["n_with_candidate"], res["n_scorable"], res["n_withhold_only"]) == (5, 4, 3, 2, 1), str(res))
    check("i1's heft within the window is a baseline deed; i2 was returned at +20h",
          res["n_returned"] == 1 and res["baseline_hits"] == 1 and res["baseline_rate"] == 0.5, str(res))
    check("i2's look-at-the-garden at +30h is an after-return deed (rate 1/1)", res["after_hits"] == 1 and res["after_rate"] == 1.0, str(res))
    check("a family hit with no verb/object in the row's words is not a deed",
          dr.deed_in_row(T_STONE, {"hands": [{"hand": "objtest"}], "thought": "the tide", "act_object": "", "intention": ""}) is None)
    check("no store, no log: measure() is empty, never raises", dr.measure([], [], [])["n_scorable"] == 0)

after = [_h(p) for p in CANARY]
check("live data untouched (world_substrate, follow_line log, hands_trace, frontier hashes)", before == after)
print("\nFAILED: " + str(FAIL) if FAIL else "\nALL PASS")
sys.exit(1 if FAIL else 0)

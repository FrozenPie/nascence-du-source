"""scripts/test_composition_bank.py (J-3250, D-0639): hermetic proof of the composition task bank, ladder, no-repeat
rule and the material-grounded grader.

No LLM, no live data. core is imported FIRST and asserted to be this tree; lab_env.isolate() sandboxes the state/log
and the memory DB. call_json and grade_work are mocked. Live data files are size-checked at the end.

  [1] the sources: _excerpt cuts whole sentences just before the bookmark; sumner reads the real clocks; day reads only
      today's nature observation; wiki needs >= 2 pages whose via phrase is "asked by him" and ignores system fetches
  [2] no task text carries a hint or advice word; the composition rubric asks for one departure, not praise
  [3] the ladder: three in a row >= 0.8 climbs, three < 0.5 drops, a new rung starts clean, lower-rung lessons do not move it
  [4] no topic repeats inside 10 lessons across 60 simulated lessons; an exhausted bank returns None and run() skips
  [5] run(): the grader gets the instruction as the task, the MATERIAL as the reference and rubric="composition";
      the log row carries rung/source/topic/graded; fail-open grade is logged graded False and does not climb
  [6] grade_work default rubric is unchanged (nature study passes none)
"""
from __future__ import annotations
import asyncio, json, random, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import composition as co, left_lane

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = [Path(r"C:\Nascence\data\composition_log.jsonl"), Path(r"C:\Nascence\data\composition_state.json"),
        ROOT / "data" / "composition_log.jsonl", ROOT / "data" / "composition_state.json"]
before = [p.stat().st_size if p.exists() else None for p in LIVE]

print("[2] wording")
HINT = ("should", "try to", "consider", "improve", "remember", "you must", "work on", "tip")
for k, t in co._INSTRUCTION.items():
    check(f"instruction '{k}' has no hint/advice word", not any(w in t.lower() for w in HINT))
r = left_lane._COMPOSITION_GRADE_TASK
check("rubric asks for the one least grounded place", "ONE place" in r and "least grounded" in r)
check("rubric forbids praise and advice", "Do not praise" in r and "Do not advise" in r)
check("rubric adds no advice verb", not any(w in r.lower().replace("do not advise", "") for w in ("improve", "should", "try to", "consider")))

with lab_env.isolate(also=[(co, ["_STATE", "_LOG", "_NATURE_LOG"])], db="empty") as lab_dir:
    lab_dir = Path(lab_dir)
    co._STATE = lab_dir / "composition_state.json"
    co._LOG = lab_dir / "composition_log.jsonl"
    co._NATURE_LOG = lab_dir / "nature_study_log.jsonl"
    orig_sources = dict(co._SOURCES)

    print("[1] sources")
    sents = " ".join(f"Sentence number {i} of the passage is about the sea." for i in range(40))
    text = "x" * 3000 + " " + sents
    ex = co._excerpt(text, len(text))
    check("excerpt ends on a sentence end and is capped", ex.endswith(".") and len(ex) <= co.MATERIAL_MAX)
    check("excerpt begins on a sentence start", ex.startswith("Sentence"))
    check("no excerpt before he has read 200 chars", co._excerpt("short text.", 11) == "")
    s = co._src_sumner()
    check("sumner gives sea, sun and moon lines", s and s["source"] == "sumner" and "tide" in s["material"]
          and "moon" in s["material"] and "sun" in s["material"])
    check("sumner does not name a place or teach", "Sumner" not in s["material"])
    check("day: none without a log", co._src_day() is None)
    now = time.time()
    old = now - 3 * 86400
    with open(co._NATURE_LOG, "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": old, "observation": "OLD obs"}) + "\n")
    check("day: yesterday's observation is not offered", co._src_day() is None)
    with open(co._NATURE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now, "observation": "The sea was grey and flat."}) + "\n")
    d = co._src_day()
    check("day: today's observation, labelled his own words", d and "The sea was grey" in d["material"] and "your own words" in d["material"])
    from core.memory import store
    rwm = store.recent_world_material
    try:
        rows = [{"content": "[Looked up: 'Tide' (asked by him: tides)] The tide is the rise and fall of sea levels.", "ts": now - 600},
                {"content": "[Looked up: 'Moon' (external fact via curiosity pursuit)] A system-fetched page.", "ts": now - 500},
                {"content": "[Looked up: 'Lunar phase' (asked by him: moon phases)] Phases are the apparent shape of the Moon.", "ts": now - 60}]
        store.recent_world_material = lambda limit=8, origins=(): [rows[2], rows[1], rows[0]]
        w = co._src_wiki()
        check("wiki: chain of two asked-for pages, oldest first, system page ignored",
              w and "Tide" in w["material"] and "Lunar phase" in w["material"] and "Moon (" not in w["material"]
              and w["material"].index("Tide") < w["material"].index("Lunar phase"))
        check("wiki: labelled as Wikipedia's words", "Wikipedia's, not yours" in w["material"])
        store.recent_world_material = lambda limit=8, origins=(): [rows[2], rows[1]]
        check("wiki: a single asked-for page is not a chain", co._src_wiki() is None)
        store.recent_world_material = lambda limit=8, origins=(): []
        check("wiki: silent when there are none (today)", co._src_wiki() is None)
    finally:
        store.recent_world_material = rwm

    print("[3] ladder")
    def H(*pairs): return [{"rung": r, "score": s} for r, s in pairs]
    check("2 good at rung 0 does not climb", co._step(0, H((0, .9), (0, .9))) == 0)
    check("3 good at rung 0 climbs", co._step(0, H((0, .9), (0, .85), (0, .8))) == 1)
    check("a 0.79 in the three blocks the climb", co._step(0, H((0, .9), (0, .79), (0, .9))) == 0)
    check("fresh rung starts clean (old rung-0 scores do not count at rung 1)", co._step(1, H((0, .9), (0, .9), (0, .9), (1, .9))) == 1)
    check("3 below 0.5 at rung 2 drops to 1", co._step(2, H((2, .4), (2, .3), (2, .2))) == 1)
    check("never below 0", co._step(0, H((0, .1), (0, .1), (0, .1))) == 0)
    check("never above the top", co._step(co.MAX_RUNG, H(*[(co.MAX_RUNG, 1.0)] * 3)) == co.MAX_RUNG)
    check("a lower-rung lesson leaves the rung", co._step(2, H((2, .9), (2, .9), (1, .9))) == 2)

    print("[4] no repeat in 10 lessons")
    counter = {"n": 0}
    def fresh(src):
        def f():
            counter["n"] += 1
            return {"source": src, "topic": f"{src}:{counter['n'] // 3}", "material": f"{src} material {counter['n']}"}
        return f
    co._SOURCES.update({k: fresh(k) for k in ("book", "place", "sumner", "day", "wiki")})
    hist, topics = [], []
    rng = random.Random(7)
    for i in range(60):
        les = co.pick_lesson(history=hist, rung=co.MAX_RUNG, rng=rng)
        if les is None:
            continue
        topics.append(les["topic"])
        hist.append({"kind": les["kind"], "topic": les["topic"], "rung": les["rung"], "score": .9})
    windows_ok = all(len(set(topics[i:i + 10])) == len(topics[i:i + 10]) for i in range(len(topics)))
    check(f"{len(topics)} lessons, no topic repeated inside any 10", windows_ok and len(topics) >= 20)
    check("consecutive lessons differ in kind where another is available",
          sum(1 for a, b in zip(hist, hist[1:]) if a["kind"] == b["kind"]) < len(hist) // 3)
    co._SOURCES.update({k: (lambda k=k: {"source": k, "topic": f"{k}:fixed", "material": "m"}) for k in ("book", "place", "sumner", "day", "wiki")})
    seen = [{"topic": f"{k}:fixed", "kind": "x"} for k in ("book", "place", "sumner", "day", "wiki")]
    check("every topic used in the last 10 -> None", co.pick_lesson(history=seen, rung=3) is None)
    old_seen = [{"topic": f"{k}:fixed", "kind": "x"} for k in ("book", "place", "sumner", "day", "wiki")] + [{"topic": f"z{i}", "kind": "x"} for i in range(10)]
    check("used 11+ lessons ago -> allowed again", co.pick_lesson(history=old_seen, rung=3) is not None)
    co._SOURCES.update({k: (lambda: None) for k in orig_sources})
    check("no sources at all -> None", co.pick_lesson(history=[], rung=3) is None)
    called = {"n": 0}
    async def cj(*a, **k):
        called["n"] += 1
        return {"writing": "w" * 80}
    check("run() with nothing on offer returns {} and makes no model call", asyncio.run(co.run(cj, ["x"])) == {} and called["n"] == 0)

    print("[5] run()")
    co._SOURCES.update({"place": lambda: {"source": "place", "topic": "place:garden:clear:calm:day",
                                          "material": "You are in the garden. The weather is clear."}})
    co._SOURCES.update({k: (lambda: None) for k in ("book", "sumner", "day", "wiki")})
    seen_args = {}
    orig_gw = left_lane.grade_work
    async def cj2(urls, sys_p, user_p, **k):
        seen_args["user"] = user_p
        return {"writing": "The garden is bright and the sky has no cloud over it today."}
    async def gw(task, ref, work, rubric=""):
        seen_args.update(task=task, ref=ref, work=work, rubric=rubric)
        return {"grounded": 0.82, "feedback": "'The garden is bright' says bright where the material says clear."}
    left_lane.grade_work = gw
    try:
        res = asyncio.run(co.run(cj2, ["x"]))
        check("a lesson ran from the place source at rung 0", res.get("kind") == "describe" and res["rung"] == 0 and res["source"] == "place")
        check("writer saw instruction and material", "Your task:" in seen_args["user"] and "You are in the garden" in seen_args["user"])
        check("grader task is the instruction only; reference is the material; composition rubric",
              seen_args["task"] == co._INSTRUCTION["describe"] and seen_args["ref"].startswith("You are in the garden")
              and seen_args["rubric"] == "composition")
        rows = [json.loads(l) for l in co._LOG.read_text(encoding="utf-8").splitlines()]
        check("log row has rung/source/topic/graded/task and the grade", len(rows) == 1 and rows[0]["rung"] == 0
              and rows[0]["source"] == "place" and rows[0]["topic"].startswith("place:") and rows[0]["graded"] is True
              and rows[0]["score"] == 0.82 and rows[0]["task"].startswith("Describe"))
        st = json.loads(co._STATE.read_text(encoding="utf-8"))
        check("state keeps history with topic and rung", st["history"][-1]["topic"] == rows[0]["topic"] and st["rung"] == 0)
        # same place state again: blocked as a repeat topic
        check("the same place topic is refused on the next lesson", asyncio.run(co.run(cj2, ["x"])) == {})
        # climb: three distinct topics at 0.9
        n = {"i": 0}
        def varied():
            n["i"] += 1
            return {"source": "place", "topic": f"place:v{n['i']}", "material": "m"}
        co._SOURCES["place"] = varied
        async def gw9(task, ref, work, rubric=""): return {"grounded": 0.9, "feedback": "f"}
        left_lane.grade_work = gw9
        for _ in range(3):
            asyncio.run(co.run(cj2, ["x"]))
        check("three good lessons at rung 0 climbed the persisted rung to 1", co.status()["rung"] == 1)
        async def gwNone(task, ref, work, rubric=""): return None
        left_lane.grade_work = gwNone
        co._SOURCES["place"] = varied
        res = asyncio.run(co.run(cj2, ["x"]))
        last = json.loads(co._LOG.read_text(encoding="utf-8").splitlines()[-1])
        check("fail-open grade: score None (J-2992, was 0.6), graded False, logged", res["score"] is None and last["graded"] is False and last["score"] is None)
    finally:
        left_lane.grade_work = orig_gw
        co._SOURCES.update(orig_sources)

print("[6] default rubric")
import inspect
src = inspect.getsource(left_lane.grade_work)
check("default rubric still _WORK_GRADE_TASK, composition selected only by rubric=='composition'",
      "_WORK_GRADE_TASK" in src and 'rubric == "composition"' in src and inspect.signature(left_lane.grade_work).parameters["rubric"].default == "")
ns = (ROOT / "core" / "nature_study.py").read_text(encoding="utf-8")
import re as _re_cb
check("nature study still calls grade_work without a rubric", not _re_cb.search(r"grade_work\([^)]*rubric", ns))   # J-2958 added a comment that says rubric

after = [p.stat().st_size if p.exists() else None for p in LIVE]
check("no live composition file touched", before == after)
print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

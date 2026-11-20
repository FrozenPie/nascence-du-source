"""scripts/_test_J-2945_composition_scene.py (J-2945, F-3635): hermetic proof that composition's describe lesson is
grounded in the live scene and that the summarize lesson names the book without Project Gutenberg catalogue wording.

No LLM, no live data. core is imported FIRST and asserted to be this tree; lab_env.isolate() sandboxes the state/log and
the memory DB; sensorium / world_clock reads are stubbed (the real look() touches provisions, which a non-live
process may not write); call_json and grade_work are mocked.

  [1] _book_title strips the Gutenberg collection / works / ebook wording and leaves ordinary titles alone
  [2] _src_book names the book by that clean title
  [3] _live_scene picks the view the way nature_study._scene does (study: window; garden: garden; shore: pools),
      returns '' when nothing reads, and re-raises NonLiveWriteError
  [4] the place source carries the scene in its material, and is silent (None) when no scene reads
  [5] run() on a describe lesson: the writer's user prompt holds the scene, and grade_work's reference is the same
      material (scene included); the task text carries no hint
"""
from __future__ import annotations
import asyncio, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import composition as co, left_lane, profile, sensorium, world_clock

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = [Path(r"C:\Nascence\data\composition_log.jsonl"), Path(r"C:\Nascence\data\composition_state.json"),
        ROOT / "data" / "composition_log.jsonl", ROOT / "data" / "composition_state.json"]
before = [p.stat().st_size if p.exists() else None for p in LIVE]

print("[1] _book_title")
check("collection wording gone", co._book_title("Complete_Project_Gutenberg_Collection_of_Memoirs_of_Napoleon") == "Memoirs of Napoleon")
check("works wording becomes 'Works of'", co._book_title("The_Entire_Project_Gutenberg_Works_of_Mark_Twain") == "Works of Mark Twain")
check("ebook wording gone", co._book_title("Project Gutenberg EBook of Ulysses") == "Ulysses")
check("ordinary titles untouched", co._book_title("A_Study_in_Scarlet") == "A Study in Scarlet"
      and co._book_title("The_Complete_Herbal_To_which") == "The Complete Herbal To which")
check("nothing left falls back to the stem", co._book_title("Project_Gutenberg") == "Project Gutenberg")

SCENES = {"window": "Through the study window: wet grass, a grey sea, one gull on the fence.",
          "garden": "The garden: bean rows, a wet spade against the wall.",
          "pools": "The rock-pools: two limpets and a small crab under the weed."}
real = (sensorium.where, sensorium.look, sensorium.scene_line, world_clock.daylight, dict(sensorium.state))
looked = []
loc = {"v": "study"}
def fake_look(target="room", raw=""):
    looked.append(target)
    return SCENES.get(target, "")
def install(scenes_ok=True):
    sensorium.where = lambda: loc["v"]
    sensorium.look = fake_look if scenes_ok else (lambda *a, **k: "")
    sensorium.scene_line = (lambda: "") if not scenes_ok else real[2]
    sensorium.state["weather"] = "rain"
    sensorium.state["wind"] = "light"
    world_clock.daylight = lambda: "grey morning light"
def restore():
    sensorium.where, sensorium.look, sensorium.scene_line, world_clock.daylight = real[:4]
    sensorium.state.clear(); sensorium.state.update(real[4])

try:
    with lab_env.isolate(also=[(co, ["_STATE", "_LOG", "_NATURE_LOG"])], db="empty") as lab_dir:
        lab_dir = Path(lab_dir)
        co._STATE = lab_dir / "composition_state.json"
        co._LOG = lab_dir / "composition_log.jsonl"
        co._NATURE_LOG = lab_dir / "nature_study_log.jsonl"

        print("[2] _src_book title")
        from core import reading
        bk = lab_dir / "Complete_Project_Gutenberg_Collection_of_Memoirs_of_Napoleon.txt"
        bk.write_text("The emperor rode out at dawn. " * 80, encoding="utf-8")
        o_cb, o_co = reading.current_book, reading.current_offset
        reading.current_book = lambda: bk
        reading.current_offset = lambda b: 1500
        try:
            m = co._src_book()
        finally:
            reading.current_book, reading.current_offset = o_cb, o_co
        check("book material names 'Memoirs of Napoleon'", m is not None and "'Memoirs of Napoleon'" in m["material"])
        check("no Gutenberg wording in the material", m is not None and "gutenberg" not in m["material"].lower())

        print("[3] _live_scene")
        install()
        loc["v"] = "study"; looked.clear()
        check("study looks OUT of the window", co._live_scene() == SCENES["window"] and looked == ["window"])
        loc["v"] = "garden"; looked.clear()
        check("garden looks at the garden", co._live_scene() == SCENES["garden"] and looked == ["garden"])
        loc["v"] = "shore"; looked.clear()
        check("shore looks at the pools", co._live_scene() == SCENES["pools"] and looked == ["pools"])
        install(scenes_ok=False)
        check("nothing readable gives ''", co._live_scene() == "")
        def boom(*a, **k): raise profile.NonLiveWriteError("fenced")
        sensorium.look = boom
        try:
            co._live_scene(); raised = False
        except profile.NonLiveWriteError:
            raised = True
        check("NonLiveWriteError re-raised, not swallowed", raised)

        print("[4] place source")
        install(); loc["v"] = "study"
        pl = co._src_place()
        check("place material holds the weather AND the scene", pl is not None and "rain" in pl["material"]
              and SCENES["window"] in pl["material"])
        check("topic unchanged in shape", pl["topic"].startswith("place:study:rain:light:"))
        install(scenes_ok=False)
        check("no scene readable: the place source is silent", co._src_place() is None)

        print("[5] run(): writer sees the scene, grader's reference is the same material")
        install(); loc["v"] = "study"
        co._SOURCES.update({k: (lambda: None) for k in ("book", "sumner", "day", "wiki")})
        seen = {}
        async def cj(urls, system, user, **kw):
            seen["user"] = user
            return {"writing": "Wet grass runs down to a grey sea, and one gull stands on the fence rail alone."}
        async def gw(task, reference, piece, rubric=None, **kw):
            seen["task"], seen["ref"], seen["rubric"] = task, reference, rubric
            return {"grounded": 0.9, "feedback": "observed"}
        og = left_lane.grade_work
        left_lane.grade_work = gw
        try:
            res = asyncio.run(co.run(cj, ["x"]))
        finally:
            left_lane.grade_work = og
        check("a describe lesson ran from place", res.get("kind") == "describe" and res.get("source") == "place")
        check("writer's user prompt holds the scene", SCENES["window"] in seen.get("user", ""))
        check("grader reference is the material with the scene in it", SCENES["window"] in seen.get("ref", "")
              and seen.get("rubric") == "composition")
        check("grader task is the instruction only", seen.get("task") == co._INSTRUCTION["describe"])
        HINT = ("should", "try to", "consider", "improve", "remember", "you must", "work on", "tip", "do not invent")
        check("no hint or warning in the task text", not any(w in seen.get("task", "").lower() for w in HINT))
finally:
    restore()

after = [p.stat().st_size if p.exists() else None for p in LIVE]
check("no live composition file touched", before == after)
print("ALL PASS" if ok_all else "SOME FAILED")
sys.exit(0 if ok_all else 1)

"""Hermetic test for J-3236 / D-0625: 'prism' is out of frontier._GROUNDED_SOURCES (pending_pursuit / top_open no
longer rank a prism question ahead of intention) and scripts/lab_prism_grade.py's builder, both-judge rule and
report, on fake judges. Everything runs on temp files (fr._F, fr._F_LIGHT redirected); the live store is never
touched. `import core` comes BEFORE anything lab_env-ish, and its path is asserted to be this worktree.
Run: python scripts/_test_prism_not_grounded_J3236.py   (exit 0 = all pass)"""
import asyncio, json, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                              # noqa: E402  (BEFORE any lab_env)
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import frontier as fr                          # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import lab_prism_grade as lg                             # noqa: E402

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

tmp = Path(tempfile.mkdtemp(prefix="prism_J3236_"))
fr._F = tmp / "frontier.json"; fr._F_LIGHT = tmp / "frontier.light.json"

print("[1] the grounded tier")
check("prism not grounded", "prism" not in fr._GROUNDED_SOURCES)
check("study/reading/curiosity still grounded", all(s in fr._GROUNDED_SOURCES for s in ("study", "reading", "curiosity")))

print("[2] pending_pursuit: a NEWER prism question no longer jumps an older intention question")
fr.note_question("What makes granite form those strange desert coatings over thousands of years?", "intention")
time.sleep(0.02)
fr.note_question("How do oystercatchers locate buried mussels at low tide in the estuary?", "prism")
qs = json.loads(fr._F.read_text(encoding="utf-8"))["questions"]
check("both seeded with their own source", sorted(q["source"] for q in qs) == ["intention", "prism"])
p = fr.pending_pursuit()
check("pending_pursuit picks the older intention question", p is not None and "granite" in p["q"].lower())
_keep = fr._GROUNDED_SOURCES
fr._GROUNDED_SOURCES = _keep + ("prism",)
p_old = fr.pending_pursuit()
fr._GROUNDED_SOURCES = _keep
check("control: with the OLD tuple the prism question won (the test discriminates)",
      p_old is not None and "oystercatchers" in p_old["q"].lower())
fr.note_question("Why does capillary action draw water up a narrow tube against gravity?", "curiosity")
p = fr.pending_pursuit()
check("curiosity still outranks intention", p is not None and "capillary" in p["q"].lower())
top = fr.top_open(3)
check("top_open: the grounded curiosity question leads, prism has no grounded rank (ties with intention by recency)",
      top and top[0]["source"] == "curiosity")

print("[3] lab_prism_grade: builder, both-judge rule, report")
data = json.loads(fr._F.read_text(encoding="utf-8"))
for q in data["questions"]:
    if q["source"] == "prism":
        q["finding"] = "Oystercatchers are waders that feed on shellfish, probing the sand at low tide."
        q["finding_title"] = "Oystercatcher"
data["questions"].append({"id": "old1", "q": "An ancient prism question", "source": "prism", "born": time.time() - 90 * 86400,
                          "status": "faded"})
fr._F.write_text(json.dumps(data), encoding="utf-8")
shadow = tmp / "shadow.jsonl"
shadow.write_text(json.dumps({"raw": "I feel cut off.", "transformed": "How do oystercatchers locate buried mussels at "
                              "low tide in the estuary?"}) + "\n", encoding="utf-8")
items = lg.build_items(fr._F, shadow, 30)
check("30d window holds the one fresh prism question, not the 90-day-old one",
      len(items) == 1 and items[0]["q"].startswith("How do oystercatchers"))
check("raw thought joined from the shadow log", items[0]["raw"] == "I feel cut off.")
check("all-time window includes the old one", len(lg.build_items(fr._F, shadow, 0)) == 2)
check("forbidden ports (hot lane, granite) are not judge urls",
      not any(p in u for u in lg.JUDGE_URLS.values() for p in lg.FORBIDDEN_PORTS))

calls = []
async def fake_ask(session, url, system, user, key):
    calls.append((url, key))
    if "capillary" in user:
        return True, "x", None
    return (url.endswith("11438")), "why", None          # mixtral says yes, falcon says no -> a split
async def go():
    return await lg.grade_item(None, items[0], fake_ask)
row = asyncio.run(go())
check("judges disagreeing is a split, never a verdict", row["answerable"] == "split" and row["self_loop"] == "split")
check("each key asked of BOTH families, nothing else", sorted(set(u for u, _ in calls)) == sorted(lg.JUDGE_URLS.values())
      and len(calls) == 4)
nm = dict(items[0]); nm["material"] = ""
row2 = asyncio.run(lg.grade_item(None, nm, fake_ask))
check("no material -> answerable is no_material and is not sent to a judge", row2["answerable"] == "no_material")

async def agree(session, url, system, user, key):
    return True, None, None
rows = [asyncio.run(lg.grade_item(None, dict(items[0], id=f"x{i}"), agree)) for i in range(5)]
rows += [asyncio.run(lg.grade_item(None, dict(items[0], id=f"n{i}", material=""), agree)) for i in range(45)]
s = lg.summarize(rows)
check("share over all 50 = 5/50, over material = 5/5", s["share_answerable_of_all"] == 0.1 and s["share_answerable_of_material"] == 1.0)
check("defeater read says RETIRE below 20 percent at n>=50", "RETIRE" in s["defeater_read"])
check("under 50 graded the defeater cannot be read", "cannot be read" in lg.summarize(rows[:10])["defeater_read"])

print("FAILS:", FAILS or "none")
sys.exit(1 if FAILS else 0)

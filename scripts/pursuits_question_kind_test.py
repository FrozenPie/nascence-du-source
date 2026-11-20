"""Hermetic test for J-3165 (D-0554): pursuits record question_kind / question_text AT BIRTH.
No LLM/hub/embedder: observe() gets hand-built vectors; judge_panel.rule_detail is faked.
Runs inside lab_env.isolate() with the pursuits stores temp-pathed (live data/ never opened).
Run: python scripts/pursuits_question_kind_test.py   (from the tree under test)"""
from __future__ import annotations
import asyncio, copy, json, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.pursuits as pu
import core.pursuit_close_shadow as pcs
import core.judge_panel as jp
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True
def check(n, c):
    global ok_all
    ok_all = ok_all and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")

asked = []
async def fake(system, user, key, context="", **k):
    asked.append((context, user))
    return {"verdict": False, "how": "agreed", "why": "t"}
jp.rule_detail = fake

Q_THOUGHT = "The tide is going out over the rocks below the cottage. Why does the pool nearest the wall stay full?"
A_THOUGHT = "The cat's weight presses my hand while chickweed mats the rosemary in the cold bed outside."
V = [1.0, 0.0]

with isolate(db="empty", also=[(pu, ["_DIR", "_ACTIVE", "_SHADOW", "_SERIES"])]):
    tmp = Path(tempfile.mkdtemp(prefix="J-3165_"))
    pcs.SHADOW_LOG = tmp / "pcs.jsonl"
    pu._DIR = tmp; pu._ACTIVE = tmp / "a.json"; pu._SHADOW = tmp / "s.jsonl"; pu._SERIES = tmp / "ser.jsonl"
    assert str(ROOT) in str(Path(pu.__file__).resolve()) and "Nascence\\data" not in str(pu._ACTIVE)

    print("[1] classify_birth")
    check("'?' sentence -> question", pu.classify_birth(Q_THOUGHT)[0] == "question"
          and pu.classify_birth(Q_THOUGHT)[1].startswith("Why does the pool"))
    check("question wins over done_when", pu.classify_birth(Q_THOUGHT, "when I can name it")[0] == "question")
    check("no '?' + done_when -> done_when", pu.classify_birth(A_THOUGHT, "when I can name the plant")
          == ("done_when", "when I can name the plant"))
    check("neither -> observation, empty text", pu.classify_birth(A_THOUGHT, "  ") == ("observation", ""))
    check("tiny '?' fragment is not a question", pu.classify_birth("Hm? ok. fine.")[0] == "observation")

    print("[2] births through observe() record the fields; old fields unchanged")
    def birth(thought, dw=""):
        pu._last_observe = 0.0
        ev = pu.observe(thought, "garden", list(V), True, "c1", done_when=dw)
        return ev
    # distinct vectors so a later thought does not match the first pursuit
    ev = birth(Q_THOUGHT)
    check("born event carries kind+text", ev and ev["event"] == "born" and ev["question_kind"] == "question")
    reg = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))
    p = reg[0]
    check("question stays the birth thought (display/match fields untouched)", p["question"] == Q_THOUGHT.strip()[:250])
    check("question_text is the extracted sentence", p["question_text"].startswith("Why does the pool"))
    check("open still extracted as before", p["open"] == p["question_text"])
    pu._save([])  # reset register
    ev = birth(A_THOUGHT, "when I can name the plant")
    reg = json.loads(pu._ACTIVE.read_text(encoding="utf-8")); p = reg[0]
    check("done_when kind stored", p["question_kind"] == "done_when" and p["question_text"] == "when I can name the plant")
    pu._save([])
    ev = birth(A_THOUGHT)
    reg = json.loads(pu._ACTIVE.read_text(encoding="utf-8")); p = reg[0]
    check("observation still registered, active, advances 1",
          p["question_kind"] == "observation" and p["question_text"] == "" and p["status"] == "active" and p["advances"] == 1)
    pu._save([])

    print("[3] kill switch")
    pu.QUESTION_AT_BIRTH = False
    birth(Q_THOUGHT)
    reg = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))
    check("flag off: no new keys, born exactly as before", "question_kind" not in reg[0] and "question_text" not in reg[0])
    pu.QUESTION_AT_BIRTH = True
    pu._save([])

    print("[4] return_seed eligibility + quoted question")
    now = time.time()
    def mk(pid, kind, **kw):
        d = {"id": pid, "question": "SCENE-" + pid + " the cat's weight presses my hand", "about": "a",
             "born": now - 7200, "standing": "where I stand " + pid, "thoughts": ["t"], "established": [],
             "open": "", "centroid": V, "recent_vecs": [V], "advances": 5, "restates": 0, "coheres": 0,
             "scatters": 0, "last_touched": now - 7200, "heat": 0.6, "status": "active"}
        if kind:
            d["question_kind"] = kind
        d.update(kw)
        return d
    pu._RETURN_COOLDOWN = 0.0; pu._RETURN_P = 1.0
    import random; random.seed(1)
    # (a) observation with a non-empty open is STILL not eligible
    pu._save([mk("obs", "observation", question_text="", open="a stray question carried in later?")])
    pu._last_return = 0.0
    check("observation not return-eligible even with an open", pu.return_seed() is None)
    # (b) question kind: quotes question_text, not the birth thought
    pu._save([mk("qq", "question", question_text="Why does the pool nearest the wall stay full?",
                 open="Why does the pool nearest the wall stay full?")])
    pu._last_return = 0.0
    r = pu.return_seed()
    check("question kind eligible", r is not None and r[1] == "qq")
    check("line quotes the extracted question, not the scene", r and "Why does the pool" in r[0] and "SCENE-qq" not in r[0])
    # (c) done_when kind with no open: eligible via question_text
    pu._save([mk("dw", "done_when", question_text="when I can name the plant")])
    pu._last_return = 0.0
    r = pu.return_seed()
    check("done_when kind eligible without an open", r is not None and r[1] == "dw" and "when I can name the plant" in r[0])
    # (d) legacy (no question_kind): unchanged - needs open, quotes the birth thought
    pu._save([mk("old1", None)])
    pu._last_return = 0.0
    check("legacy without open: still not eligible", pu.return_seed() is None)
    pu._save([mk("old2", None, open="an old open question here?")])
    pu._last_return = 0.0
    r = pu.return_seed()
    check("legacy with open: eligible, quotes birth thought as before", r is not None and "SCENE-old2" in r[0])

    print("[5] close judge: observation never asked; others see the extracted question")
    asked.clear()
    items = [mk("o1", "observation", advances=40, status="saturated", question_text=""),
             mk("q1", "question", advances=40, status="saturated", question_text="Is the wall why the pool stays full?"),
             mk("l1", None, advances=40, status="saturated", open="Does the wall decide it for the legacy one?")]   # D-0626: legacy asked only with a real open
    before = copy.deepcopy(items)
    check("due(): observation False, question True, legacy True",
          (not pcs.due(items[0])) and pcs.due(items[1]) and pcs.due(items[2]))
    n = asyncio.run(pcs.sweep(items))
    check("sweep asked 2 (not the observation)", n == 2 and [c for c, _ in asked] == ["pursuit_close:q1", "pursuit_close:l1"])
    check("question kind fed the extracted question", "PURSUIT (driving question): Is the wall why the pool stays full?" in asked[0][1]
          and "SCENE-q1" not in asked[0][1].split("ITS STANDING")[0])   # J-3104: the scene statement may only sit on WHAT IT STARTED FROM
    check("legacy with an open: the judge is shown the open question as the driving question (D-0626)",
          "PURSUIT (driving question): Does the wall decide it for the legacy one?" in asked[1][1]
          and "SCENE-l1" not in asked[1][1].split("ITS STANDING")[0])
    check("direct ask() on an observation is a no-op", asyncio.run(pcs.ask(items[0])) is None)
    check("items untouched", items == before)
    rows = [r for r in pcs._read() if r.get("kind") == "close_ask"]
    check("rows carry question_kind", [r["question_kind"] for r in rows] == ["question", "legacy"])

    print("[6] question_kind_counts")
    c = pu.question_kind_counts([mk("a", "question"), mk("b", "observation"), mk("c", None),
                                 mk("d", "done_when", status="dormant")])
    check("counts", c["question"] == 1 and c["observation"] == 1 and c["legacy"] == 1 and c["done_when"] == 1
          and c["total"] == 4 and c["active_not_observation"] == 2)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

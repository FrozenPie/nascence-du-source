"""Hermetic test for J-3229 (D-0618): a pursuit's `open` is filled from the follow-line board or its done_when.
No LLM/hub/embedder. Runs inside lab_env.isolate() with the pursuits, frontier and done_when stores temp-pathed
(live data/ never opened). Run: python scripts/pursuits_open_fill_test.py   (from the tree under test)"""
from __future__ import annotations
import json, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.pursuits as pu
import core.frontier as fr
import core.done_when as dw
import core.follow_line as fl
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True
def check(n, c):
    global ok_all
    ok_all = ok_all and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")

V = [1.0, 0.0]
A_THOUGHT = "The cat's weight presses my hand while chickweed mats the rosemary in the cold bed outside."
Q_THOUGHT = "The tide is going out over the rocks below the cottage. Why does the pool nearest the wall stay full?"

with isolate(db="empty", also=[(pu, ["_DIR", "_ACTIVE", "_SHADOW", "_SERIES"])]):
    tmp = Path(tempfile.mkdtemp(prefix="J-3229_"))
    pu._DIR = tmp; pu._ACTIVE = tmp / "a.json"; pu._SHADOW = tmp / "s.jsonl"; pu._SERIES = tmp / "ser.jsonl"
    fr._F = tmp / "frontier.json"
    dw.STORE = tmp / "done_when.jsonl"
    fr._SEM_SHADOW_LOG = tmp / "sem.jsonl"; fl.SHADOW_LOG = tmp / "fl.jsonl"   # a literal-"?" advance boards the line
    assert Path(pu.__file__).resolve().is_relative_to(ROOT) and "Nascence\\data" not in str(pu._ACTIVE)
    now = time.time()

    def board(*rows):
        fr._F.write_text(json.dumps({"questions": list(rows)}), encoding="utf-8")
    def ent(i, q, status="open", last=None, **ab):
        return {"id": i, "q": q, "status": status, "last_seen": last or now, "asked_by": ab}
    def mk(pid, kind=None, **kw):
        d = {"id": pid, "question": "SCENE-" + pid + " the cat's weight presses my hand", "about": "a",
             "born": now - 7200, "standing": "where I stand " + pid, "thoughts": ["t"], "established": [],
             "open": "", "centroid": V, "recent_vecs": [V], "advances": 5, "restates": 0, "coheres": 0,
             "scatters": 0, "last_touched": now - 7200, "heat": 0.6, "status": "active", "cycle_id": "cyc" + pid}
        if kind:
            d["question_kind"] = kind
        d.update(kw)
        return d
    def events(name):
        if not pu._SHADOW.exists():
            return []
        return [r for r in (json.loads(l) for l in pu._SHADOW.read_text(encoding="utf-8").splitlines() if l.strip())
                if r.get("event") == name]

    print("[1] board lookup")
    board(ent("e1", "What keeps the pool nearest the wall full at low tide?", pursuit_id="p1"),
          ent("e2", "An older linked one?", last=now - 500, pursuit_id="p1"),
          ent("e3", "Resolved already, must not be used?", status="resolved", last=now + 5, pursuit_id="p1"),
          ent("e4", "Someone else's question about the garden?", pursuit_id="other"),
          ent("e5", "Asked in the same cycle as p2's advance?", cycle_id="CYC2ABCD"))
    check("linked by pursuit_id, newest open entry wins", pu._board_question(mk("p1")).startswith("What keeps the pool"))
    p2 = mk("p2", cycle_ids=["CYC2ABCD"])
    check("cycle link via cycle_ids", pu._board_question(p2).startswith("Asked in the same cycle"))
    check("cycle link via birth cycle_id", pu._board_question(mk("p3", cycle_id="CYC2ABCD1234")).startswith("Asked in the same"))
    check("cycle link via a pending advance", pu._board_question(mk("p4", pending=[{"cycle_id": "CYC2ABCD"}])) != "")
    check("unlinked pursuit -> ''", pu._board_question(mk("zz")) == "")
    check("resolved/other entries never used", "Resolved" not in pu._board_question(mk("p1")) and
          "Someone else" not in pu._board_question(mk("p1")))

    print("[2] done_when lookup")
    dw.record("pursuit", "d1", "when I can name the plant in the bed", dw.JUDGE_PURSUIT, source="monologue")
    check("done_when store row", pu._done_when_question(mk("d1")) == "when I can name the plant in the bed")
    check("done_when-born question_text", pu._done_when_question(mk("d2", "done_when", question_text="when X")) == "when X")
    check("no row -> ''", pu._done_when_question(mk("none")) == "")

    print("[3] _fill_open order and guards")
    p = mk("p1"); src = pu._fill_open(p, now)
    check("board first", src == "board" and p["open"].startswith("What keeps the pool") and p["open_source"] == "board")
    check("event logged", any(e["id"] == "p1" and e["source"] == "board" for e in events("open_filled")))
    p = mk("d1"); src = pu._fill_open(p, now)
    check("then done_when", src == "done_when" and p["open"] == "when I can name the plant in the bed")
    p = mk("p1", open="already a literal question here?"); check("literal open never overwritten", pu._fill_open(p, now) == "" and p["open"].startswith("already"))
    p = mk("p1", "observation", question_text=""); check("observation never filled", pu._fill_open(p, now) == "" and not p["open"])
    pu.OPEN_FILL = False
    p = mk("p1"); check("flag off: no fill", pu._fill_open(p, now) == "" and not p["open"])
    pu.OPEN_FILL = True

    print("[4] return_seed: eligible via board, observation still not, persisted + logged")
    pu._RETURN_COOLDOWN = 0.0; pu._RETURN_P = 1.0
    import random; random.seed(2)
    pu._save([mk("p1"), mk("obs", "observation", question_text="")])
    pu._last_return = 0.0
    r = pu.return_seed()
    check("legacy pursuit with a board entry is returned", r is not None and r[1] == "p1" and "What keeps the pool" in r[0])
    reg = {p["id"]: p for p in json.loads(pu._ACTIVE.read_text(encoding="utf-8"))}
    check("open persisted with its source", reg["p1"]["open"].startswith("What keeps") and reg["p1"]["open_source"] == "board")
    check("observation untouched", reg["obs"]["open"] == "" and "open_source" not in reg["obs"])
    check("returned row names the open source", events("returned")[-1]["open_source"] == "board")
    pu._save([mk("zz")]); pu._last_return = 0.0
    check("no board, no done_when: still not eligible", pu.return_seed() is None)
    pu._save([mk("o2", "observation", question_text="", open="stray?")]); pu._last_return = 0.0
    check("observation with an open still not eligible", pu.return_seed() is None)

    print("[5] judged advance fills open (no '?') and records the cycle; literal '?' still wins")
    pu._save([])
    pq = mk("p1", open="")
    item = {"thought": A_THOUGHT, "about": "garden", "cycle_id": "CYC9XYZWV", "coherent": True, "restate_sim": 0.3}
    pu._apply_confirmed(pq, item, now)
    check("cycle id remembered (8 chars)", pq["cycle_ids"] == ["CYC9XYZW"])
    check("pursuit_id-linked board entry filled the open", pq["open"].startswith("What keeps the pool") and pq["open_source"] == "board")
    board(ent("e9", "Is the wall the reason the pool holds?", cycle_id="CYC9XYZW"))
    pq2 = mk("p9", open="")
    pu._apply_confirmed(pq2, dict(item), now)
    check("ask boarded by that cycle links", pq2["open"].startswith("Is the wall") and pq2["open_source"] == "board")
    pq3 = mk("p9b", open="")
    pu._apply_confirmed(pq3, dict(item, thought=Q_THOUGHT), now)
    check("literal question first, source=thought", pq3["open"].startswith("Why does the pool") and pq3["open_source"] == "thought")

    print("[6] births")
    board(ent("eb", "What is the weed doing at the foot of the rosemary?", cycle_id="BORNCYC1"))
    pu._save([]); pu._last_observe = 0.0
    pu.observe(A_THOUGHT, "garden", list(V), True, "borncyc1xx", done_when="")
    p = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))[0]
    check("born as observation (no '?', no done_when) even with a same-cycle board entry: stays closed",
          p["question_kind"] == "observation" and p["open"] == "")
    pu._save([]); pu._last_observe = 0.0
    pu.observe(A_THOUGHT, "garden", list(V), True, "borncyc1xx", done_when="when I can name the plant")
    p = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))[0]
    check("born done_when: open filled from it", p["question_kind"] == "done_when" and p["open"] == "when I can name the plant"
          and p["open_source"] == "done_when")
    pu._save([]); pu._last_observe = 0.0
    pu.observe(Q_THOUGHT, "garden", list(V), True, "c9")
    p = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))[0]
    check("born question: open from the literal '?', source=thought", p["open"].startswith("Why does the pool") and p["open_source"] == "thought")

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

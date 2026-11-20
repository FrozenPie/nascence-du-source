"""Hermetic test for core/goals.py (Layered Goals Phase 0). Every store it reads and writes lives in a temp dir;
the one check against the real data/ path only confirms the write fence refuses it BEFORE any I/O.
Run: python scripts/_test_layered_goals_phase0.py"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import goals, profile, goal_change   # noqa: E402
goal_change.WHAT_CHANGED_SHADOW = False   # never ask a live judge from a test

REAL_DATA = goals._DATA
FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def w(root: Path, rel: str, obj, jsonl=False):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if jsonl:
        p.write_text("".join(json.dumps(r) + "\n" for r in obj), encoding="utf-8")
    else:
        p.write_text(json.dumps(obj), encoding="utf-8")


def seed(root: Path, t0: float):
    w(root, "intentions.json", {"open": [
        {"key": "lamp|light the lamp", "family": "lamp", "object": "light the lamp", "deed": "light the lamp",
         "thought": "Filling the lamp feels like an act of will.", "reason": "place:in the study", "location": "garden",
         "ts": t0 - 600, "renewed_ts": t0 - 600, "renewals": 1, "reminders": 1, "last_reminded": t0 - 60}],
        "done": [], "dropped": [], "lapsed": []})
    w(root, "commitment_active.json", [
        {"id": "s1", "statement": "I decide that small repeated acts of choosing are enough.", "scope": "x",
         "held_since": t0 - 9000, "scans": 12, "reaffirmed": 2, "load_bearing": True, "cycle_id": "abcd1234-9999"},
        {"id": "s2", "statement": "Maybe steadiness is yielding a little.", "held_since": t0 - 100, "scans": 0,
         "load_bearing": False, "cycle_id": "ffff0000-1"}])
    w(root, "pursuits_active.json", [
        {"id": "p1", "status": "active", "question": "I weigh the hare's speed against its shallow nest.",
         "question_kind": "question", "question_text": "Why do hares not dig proper nests?", "advances": 3,
         "restates": 1, "born": t0 - 7200, "last_touched": t0 - 300, "established": ["a"], "heat": 0.6,
         "cycle_id": "abcd1234-aaaa-bbbb", "centroid": [1.0, 0.0], "recent_vecs": [[0.8, 0.6]]},
        {"id": "p2", "status": "active", "question": "The tide keeps its own counsel.", "advances": 1, "restates": 0,
         "born": t0 - 500, "last_touched": t0 - 400, "cycle_id": "11112222-x"},
        {"id": "p3", "status": "dormant", "question": "gone quiet", "advances": 1, "born": t0 - 90000,
         "last_touched": t0 - 80000}])
    fq = [
        {"id": "q1", "q": "How does altitude influence shelter choice for hares?", "source": "asked", "born": t0 - 5000,
         "last_seen": t0 - 200, "offers": 1, "encounters": 2, "status": "open",
         "asked_by": {"cycle_id": "abcd1234"}},
        {"id": "q2", "q": "Does altitude influence shelter choice among mountain hares?", "source": "curiosity",
         "born": t0 - 100, "last_seen": t0 - 100, "offers": 0, "encounters": 1, "status": "open"}]
    w(root, "frontier.light.json", {"ts": t0, "counts": {"open": 2}, "open": fq})
    w(root, "frontier.json", {"questions": fq})
    w(root, "deferred_intentions.json", {"updated_at": t0, "intentions": [
        {"ts": t0 - 3000, "intention": "I want to write the essay on the tide now.", "source": "monologue", "carry_count": 0},
        {"ts": t0 - 9000, "intention": "I want to finish reading about bee navigation.", "source": "monologue", "carry_count": 2}]})
    w(root, "logs/done_when.jsonl", [
        {"ts": t0 - 7000, "seed_kind": "pursuit", "seed_id": "p1", "done_when": "when I can say why they do not dig", "judge": "pursuit_close_shadow"},
        {"ts": t0 - 100, "seed_kind": "pursuit", "seed_id": "p1", "done_when": "a later row that must not win", "judge": "x"}], jsonl=True)
    w(root, "commitment_ledger.jsonl", [], jsonl=True)


def main():
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        goals._DATA = root
        goals._assignment = lambda: ("b1", "Buller Vol 1")
        seed(root, t0)

        # ---- build (pure read) ----
        g = {x["id"]: x for x in goals.build(t0)}
        check("build indexes 10 goals", len(g) == 10, sorted(g))
        check("no file written by build", not goals.register_path().exists() and not goals.log_path().exists())
        i = g.get("intention:lamp|light the lamp", {})
        check("intention is deferred with a place cue", i.get("state") == "deferred" and i.get("resume_cue") == {"type": "place", "value": "in the study"}, i)
        check("intention deadline = renewed + 8 h", abs((i.get("deadline") or 0) - (t0 - 600 + 8 * 3600)) < 1)
        check("load-bearing stand held, other candidate", g["stand:s1"]["state"] == "held" and g["stand:s2"]["state"] == "candidate")
        check("pursuit with 3 advances held, 1 advance candidate", g["pursuit:p1"]["state"] == "held" and g["pursuit:p2"]["state"] == "candidate")
        check("dormant pursuit not indexed", "pursuit:p3" not in g)
        check("asked pursuit uses its question text", g["pursuit:p1"]["text"] == "Why do hares not dig proper nests?")
        check("first done_when row wins", g["pursuit:p1"]["done_when"] == "when I can say why they do not dig")
        check("pursuit drift computed", g["pursuit:p1"].get("drift") == 0.2, g["pursuit:p1"].get("drift"))
        check("question met twice held, once candidate", g["question:q1"]["state"] == "held" and g["question:q2"]["state"] == "candidate")
        check("project indexed", any(k.startswith("project:book:") for k in g))
        wants = [x for x in g.values() if x["kind"] == "want"]
        check("want carried twice held, new want candidate", sorted(x["state"] for x in wants) == ["candidate", "held"], wants)
        check("co_born: question from the pursuit's cycle", g["question:q1"]["edges"] == [{"type": "co_born", "to": "pursuit:p1", "by": "cycle_id"}], g["question:q1"]["edges"])
        check("co_born: stand from the pursuit's cycle", g["stand:s1"]["edges"][:1] == [{"type": "co_born", "to": "pursuit:p1", "by": "cycle_id"}])
        check("unrelated stand has no edge", g["stand:s2"]["edges"] == [])
        check("entry filter: candidate question near the held one", g["question:q2"]["near"] == ["question:q1"], g["question:q2"]["near"])
        check("held goals are never 'near' flagged", g["question:q1"]["near"] == [])

        # ---- tick 1: births ----
        s1 = goals.tick(t0)
        rows = [json.loads(x) for x in goals.log_path().read_text(encoding="utf-8").splitlines()]
        check("tick 1 summary", s1 and s1["n"] == 10 and s1["edges"] == 2 and s1["with_done_when"] == 1, s1)
        check("tick 1 logs 10 births and a tick row", sum(r["event"] == "born" for r in rows) == 10 and rows[-1]["event"] == "tick" and rows[-1]["first"] is True)
        reg = json.loads(goals.register_path().read_text(encoding="utf-8"))
        check("register keeps wording history and no private fields", all(len(x["texts"]) == 1 and "_cycles" not in x for x in reg["goals"]))

        # ---- the world moves ----
        ints = json.loads((root / "intentions.json").read_text(encoding="utf-8"))
        done = ints["open"].pop(0); done["done_ts"] = t0 + 500; ints["done"].append(done)
        w(root, "intentions.json", ints)
        w(root, "commitment_active.json", [{"id": "s2", "statement": "Maybe steadiness is yielding a little.",
                                            "held_since": t0 - 100, "scans": 3, "load_bearing": True, "cycle_id": "ffff0000-1"}])
        w(root, "commitment_ledger.jsonl", [{"event": "achieved", "ts": t0 + 300, "id": "s1", "statement": "x", "evidence": "study: note"}], jsonl=True)
        ps = json.loads((root / "pursuits_active.json").read_text(encoding="utf-8"))
        ps[0]["status"] = "saturated"; ps[0]["advances"] = 40
        ps[1]["advances"] = 2; ps[1]["question"] = "The tide keeps its own counsel, and I keep mine."
        w(root, "pursuits_active.json", ps)
        fq = json.loads((root / "frontier.json").read_text(encoding="utf-8"))["questions"]
        fq[0]["status"] = "resolved"; fq[0]["resolved_how"] = "line"; fq[1]["encounters"] = 2
        w(root, "frontier.json", {"questions": fq})
        w(root, "frontier.light.json", {"open": [fq[1]]})
        w(root, "deferred_intentions.json", {"intentions": [
            {"ts": t0 - 9000, "intention": "I want to finish reading about bee navigation.", "source": "monologue", "carry_count": 2}]})

        s2 = goals.tick(t0 + 600)
        rows = [json.loads(x) for x in goals.log_path().read_text(encoding="utf-8").splitlines()]
        new = [r for r in rows if r["ts"] == t0 + 600]
        ended = {r["id"]: r for r in new if r["event"] == "ended"}
        check("intention ended as done", ended.get("intention:lamp|light the lamp", {}).get("state") == "done", ended)
        check("stand 'achieved' recorded as closed_unverified, not done", ended.get("stand:s1", {}).get("state") == "closed_unverified", ended.get("stand:s1"))
        check("saturated pursuit ended as capped", ended.get("pursuit:p1", {}).get("state") == "capped")
        check("resolved question ended as done", ended.get("question:q1", {}).get("state") == "done" and "line" in ended["question:q1"]["why"])
        check("dropped want ended as lapsed", sum(1 for k, r in ended.items() if k.startswith("want:") and r["state"] == "lapsed") == 1)
        check("ended rows say whether the goal was ever held", ended["pursuit:p1"]["held"] is True and ended["intention:lamp|light the lamp"]["held"] is True)
        st = {(r["id"], r.get("from"), r.get("to")) for r in new if r["event"] == "state"}
        check("candidate -> held transitions logged", ("pursuit:p2", "candidate", "held") in st and ("stand:s2", "candidate", "held") in st and ("question:q2", "candidate", "held") in st, st)
        check("rewording logged and kept", any(r["event"] == "reworded" and r["id"] == "pursuit:p2" for r in new))
        check("progress logged", any(r["event"] == "progress" and r["id"] == "pursuit:p2" and r["advances_to"] == 2 for r in new))
        reg = json.loads(goals.register_path().read_text(encoding="utf-8"))
        p2 = next(x for x in reg["goals"] if x["id"] == "pursuit:p2")
        check("register holds both wordings and both states", len(p2["texts"]) == 2 and [s["state"] for s in p2["states"]] == ["candidate", "held"], p2)
        check("first_seen survives the second tick", p2["first_seen"] == t0)
        check("ended goals kept in the register", len(reg["ended"]) == 5 and s2["n"] == 5, (len(reg["ended"]), s2))
        check("status() reads the saved summary", goals.status().get("n") == 5)

        # ---- switches ----
        goals.GOALS_SHADOW = False
        check("kill switch: tick does nothing", goals.tick(t0 + 1200) is None and goals.tick_async(t0 + 1200) is False)
        goals.GOALS_SHADOW = True
        goals._last_tick = 0.0
        a = goals.tick_async(t0 + 1300)
        if goals._thread:
            goals._thread.join(10)
        b = goals.tick_async(t0 + 1400)
        check("tick_async starts once then holds for the interval", a is True and b is False, (a, b))

    # ---- write fence: the real data/ path is refused before any I/O ----
    goals._DATA = REAL_DATA
    existed = goals.register_path().exists()
    try:
        goals.tick(time.time())
        refused = False
    except profile.NonLiveWriteError:
        refused = True
    check("write fence refuses a non-live tick at the real data path", refused)
    check("the refused tick created no register file", goals.register_path().exists() == existed)

    print("\n%s (%d failed)" % ("ALL OK" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

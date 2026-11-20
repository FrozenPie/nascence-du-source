"""
Hermetic test for J-2570 (F-3301): the Follow Line DEFERS a run whose grounds are unclear or whose generation died,
instead of judging it and placing an empty cargo in front of Du.

No LLM, no embedder, no live data. Runs INSIDE lab_env.isolate(db="empty") with every store path the line touches
redirected into the lab dir; every stop and the judge are deterministic fakes. The live data/ tree is fingerprinted
before/after (canary at the bottom).

  [1] grounds unclear -> one kind="deferred" row (reason grounds_unclear), NO would_return, NO judge call, NO pending,
      the why stop never runs, line.state deferred, defer_tries 1, defer_until = now + DEFER_BACKOFF_S
  [2] rearm_deferred: nothing before the backoff; after it the entry is "waiting" again; drain_tick re-arms and fires
  [3] DEFER_MAX_TRIES: the third deferral rests the entry as "unjudged" (final) and it is never re-armed
  [4] gen_dead: grounds found but the why came back empty (dead _gen_json) or raised -> deferred gen_dead, no judge;
      a later stop raising (consequences) also defers
  [5] slow empty: outcome empty after a stop-1 wait past DEFER_EMPTY_SLOW_S defers; a fast empty does NOT (real answer)
  [6] found grounds (live): judge called once, would_return row, pending placed (unchanged path)
  [7] DEFER_UNCLEAR=False restores the pre-J-2570 path (unclear -> would_return)
  [8] readers: is_vacuous + status() skip vacuous would_return rows and the settles that answered them, count
      deferred/unjudged by reason; settle() marks a settle on an unclear cargo vacuous

Run:  python scripts/follow_line_defer_test.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, json, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423): the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import follow_line as fl
from core import frontier as fr
from core import coupling_rides as cr
from core import evidence_recall as ev
from core import satisfaction as sat
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate, _hash_file

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

def rows(path: Path, kind=None):
    if not path.exists():
        return []
    out = []
    for l in path.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(l)
        except Exception:
            continue
        if kind is None or r.get("kind") == kind:
            out.append(r)
    return out

def reset():
    fl._board_log.clear(); fl._in_flight = None; fl._TASKS.clear(); fl._recent_keys.clear()
    fl._PENDING.clear(); fl._DELIVERED.clear()
    fr._save({"questions": []})
    if fl.SHADOW_LOG.exists():
        fl.SHADOW_LOG.unlink()

LIVE = Path(r"C:\Nascence\data")
CANARY = [LIVE / "frontier.json", LIVE / "monologue_log.jsonl", LIVE / "memory" / "nascence.db",
          LIVE / "logs" / "follow_line_shadow.jsonl", LIVE / "coupling_rides.jsonl", LIVE / "evidence_log.jsonl"]
def logs_fp():
    d = LIVE / "logs"
    return sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in d.iterdir() if p.is_file()
                   and not (p.name == "supervisor_events.log" or p.name.startswith("cpu_tier_"))) if d.exists() else None   # J-3501: hub supervisor appends to these while the test runs
before, before_logs = [_hash_file(p) for p in CANARY], logs_fp()

ALSO = [(fr, ["_F", "_SEM_SHADOW_LOG"]), (fl, ["SHADOW_LOG"]), (cr, ["_LOG"]), (ev, ["_LOG"]), (sat, ["_LOG", "_STATE"])]

with isolate(also=ALSO, db="empty") as lab_dir:
    print(f"lab dir: {lab_dir}")
    fr.FRONTIER_SEMANTIC_MERGE = None
    cr._DATA = lab_dir
    fl.FOLLOW_LINE = "live"
    calls = {"why": 0, "cons": 0, "judge": 0}
    G = {"grounds": [{"fragment_id": "f_a", "origin": "reading", "age": "a month ago", "strength": "bears",
                      "text": "Albuquerque ordered Portuguese soldiers to marry local women in Goa in 1510."}],
         "grounds_outcome": "found"}
    async def g_unclear(q, train_id): return {"grounds": [], "grounds_outcome": "unclear"}
    async def g_found(q, train_id): return dict(G)
    async def g_empty(q, train_id): return {"grounds": [], "grounds_outcome": "empty"}
    async def m_why(q, grounds):
        calls["why"] += 1
        if not grounds:
            return {"text": "", "cites": [], "supports": "no", "skipped": "no-grounds"}
        return {"text": "Because [1] shows the mixing was ordered from above.", "cites": [1], "supports": "yes"}
    async def why_dead(q, grounds): calls["why"] += 1; return {"text": "", "cites": [], "supports": "no"}
    async def why_raise(q, grounds): calls["why"] += 1; raise RuntimeError("endpoint refused")
    async def m_cons(q, grounds, why): calls["cons"] += 1; return [{"text": "Then Goa's creole families trace to the first decades.", "slot": "when", "checkable": "memory"}]
    async def cons_raise(q, grounds, why): calls["cons"] += 1; raise RuntimeError("endpoint refused")
    async def m_conn(q): return {"know": [], "can_do": [], "seen": []}
    async def m_against(q, grounds): return {"text": "", "cites": [], "scope": "", "skipped": "test"}
    async def m_judge(q, cargo, q_id=""): calls["judge"] += 1; return {"a": "yes", "b": "no", "c": "no", "a_how": "agreed", "b_how": "agreed", "c_how": "agreed"}
    fl._stop_why, fl._stop_consequences, fl._stop_connections, fl._stop_against, fl._judge = m_why, m_cons, m_conn, m_against, m_judge

    def new_entry(q):
        return fr.note_question_ex(q, "asked", slot="how", about="Goa", asked_by={"train_id": "t_x", "ts": time.time()}, allow_self=True)

    # [1] grounds unclear
    print("[1] grounds unclear -> deferred")
    reset(); fl._stop_grounds = g_unclear; calls.update(why=0, cons=0, judge=0)
    e = new_entry("how did the Portuguese truly blend cultures, and what scars or gifts remained?")
    t_before = time.time()
    r = asyncio.run(fl.run(e["id"]))
    d = rows(fl.SHADOW_LOG, "deferred")
    ln = fr.get(e["id"])["line"]
    check("returns the deferred row; exactly one kind=deferred row, reason grounds_unclear, try 1, not final",
          r and r["kind"] == "deferred" and len(d) == 1 and d[0]["reason"] == "grounds_unclear" and d[0]["tries"] == 1 and not d[0]["final"])
    check("no would_return row, no judge call, no pending, why/consequences never ran",
          rows(fl.SHADOW_LOG, "would_return") == [] and calls == {"why": 0, "cons": 0, "judge": 0} and fl.pending_count() == 0)
    check("line.state deferred, defer_tries 1, defer_until ~ now + backoff",
          ln["state"] == "deferred" and ln["defer_tries"] == 1 and ln["defer_reason"] == "grounds_unclear"
          and t_before + fl.DEFER_BACKOFF_S - 5 <= ln["defer_until"] <= time.time() + fl.DEFER_BACKOFF_S + 5)
    check("stop 1 secs recorded on the row's stops", "secs" in d[0]["stops"]["grounds"] and d[0]["grounds_outcome"] == "unclear")
    pubs = [p for p in rows(cr._LOG, "publish") if p["loop"] == "follow"]
    check("coupling publish carries state deferred, coordinate only",
          any(p["tuple"].get("state") == "deferred" for p in pubs) and all(set(p["tuple"]) <= {"q_id", "kind", "source", "slot", "state", "status"} for p in pubs))

    # [2] rearm
    print("[2] rearm after backoff")
    check("before the backoff: nothing re-armed", fl.rearm_deferred() == 0 and fr.get(e["id"])["line"]["state"] == "deferred")
    check("after the backoff: re-armed to waiting", fl.rearm_deferred(now=time.time() + fl.DEFER_BACKOFF_S + 1) == 1
          and fr.get(e["id"])["line"]["state"] == "waiting" and fr.get(e["id"])["line"]["defer_tries"] == 1)
    # drain_tick re-arms a due entry and fires it
    fr.set_line(e["id"], state="deferred", defer_until=time.time() - 1)
    ran = []
    async def fake_run(qid): ran.append(qid); return None
    real_run = fl.run; fl.run = fake_run
    async def drive(): x = fl.drain_tick(); await asyncio.sleep(0.01); return x
    fired = asyncio.run(drive())
    check("drain_tick re-arms a due deferred entry and fires it", fired == e["id"] and ran == [e["id"]])
    fl.run = real_run; fl._board_log.clear(); fl._in_flight = None

    # [3] max tries
    print("[3] max tries -> unjudged")
    asyncio.run(fl.run(e["id"]))                     # try 2
    asyncio.run(fl.run(e["id"]))                     # try 3 -> final
    d = rows(fl.SHADOW_LOG, "deferred")
    ln = fr.get(e["id"])["line"]
    check("tries 1,2,3; the third is final; state unjudged; defer_until cleared",
          [x["tries"] for x in d] == [1, 2, 3] and [x["final"] for x in d] == [False, False, True]
          and ln["state"] == "unjudged" and ln.get("defer_until") is None)
    check("unjudged is never re-armed", fl.rearm_deferred(now=time.time() + 10 * fl.DEFER_BACKOFF_S) == 0
          and fr.get(e["id"])["line"]["state"] == "unjudged" and calls["judge"] == 0)

    # [4] gen dead
    print("[4] generation dead")
    reset(); fl._stop_grounds = g_found; calls.update(why=0, cons=0, judge=0)
    fl._stop_why = why_dead
    e4 = new_entry("Why does mud let a robin's nest hold where straw alone slips?")
    asyncio.run(fl.run(e4["id"]))
    d = rows(fl.SHADOW_LOG, "deferred")
    check("grounds found + empty why (dead _gen_json) -> deferred gen_dead, no judge, no would_return, no pending; consequences never ran",
          len(d) == 1 and d[0]["reason"] == "gen_dead" and d[0]["n_grounds"] == 1 and calls["judge"] == 0 and calls["cons"] == 0
          and rows(fl.SHADOW_LOG, "would_return") == [] and fl.pending_count() == 0 and fr.get(e4["id"])["line"]["state"] == "deferred")
    fl._stop_why = why_raise
    e4b = new_entry("Where does the bladderwrack go when the tide strips it from the rock?")
    asyncio.run(fl.run(e4b["id"]))
    check("why stop raising -> deferred gen_dead", rows(fl.SHADOW_LOG, "deferred")[-1]["reason"] == "gen_dead"
          and rows(fl.SHADOW_LOG, "deferred")[-1]["q_id"] == e4b["id"] and calls["judge"] == 0)
    fl._stop_why, fl._stop_consequences = m_why, cons_raise
    e4c = new_entry("When did the cuckoo last call from the wood this spring?")
    asyncio.run(fl.run(e4c["id"]))
    check("a later stop raising (consequences) -> deferred gen_dead before the judge",
          rows(fl.SHADOW_LOG, "deferred")[-1]["q_id"] == e4c["id"] and rows(fl.SHADOW_LOG, "deferred")[-1]["reason"] == "gen_dead"
          and calls["judge"] == 0 and rows(fl.SHADOW_LOG, "would_return") == [])
    fl._stop_consequences = m_cons

    # [5] slow empty vs fast empty
    print("[5] slow empty vs fast empty")
    reset(); fl._stop_grounds = g_empty; calls.update(why=0, cons=0, judge=0)
    e5 = new_entry("Was the dream shore the same shore as the one below the study?")
    asyncio.run(fl.run(e5["id"]))
    check("fast empty is a real answer: would_return written, judged, pending placed",
          len(rows(fl.SHADOW_LOG, "would_return")) == 1 and rows(fl.SHADOW_LOG, "deferred") == [] and calls["judge"] == 1 and fl.pending_count() == 1)
    saved = fl.DEFER_EMPTY_SLOW_S; fl.DEFER_EMPTY_SLOW_S = -1.0       # every stop-1 wait now counts as 'slow'
    e5b = new_entry("Who taught the robins that mud holds where straw slips?")
    asyncio.run(fl.run(e5b["id"]))
    check("empty after a slow stop 1 -> deferred grounds_unclear, no judge",
          rows(fl.SHADOW_LOG, "deferred")[-1]["q_id"] == e5b["id"] and rows(fl.SHADOW_LOG, "deferred")[-1]["reason"] == "grounds_unclear"
          and calls["judge"] == 1)
    fl.DEFER_EMPTY_SLOW_S = saved

    # [6] found path unchanged
    print("[6] found grounds -> judged + pending")
    reset(); fl._stop_grounds = g_found; calls.update(why=0, cons=0, judge=0)
    e6 = new_entry("What did the Portuguese actually leave behind in Goa?")
    r6 = asyncio.run(fl.run(e6["id"]))
    check("found: judge called once, would_return row, pending placed, state pending, no deferred row",
          calls["judge"] == 1 and r6["kind"] == "would_return" and len(rows(fl.SHADOW_LOG, "would_return")) == 1
          and e6["id"] in fl._PENDING and fr.get(e6["id"])["line"]["state"] == "pending" and rows(fl.SHADOW_LOG, "deferred") == [])

    # [7] flag off
    print("[7] DEFER_UNCLEAR=False")
    reset(); fl._stop_grounds = g_unclear; calls.update(why=0, cons=0, judge=0); fl.DEFER_UNCLEAR = False
    e7 = new_entry("how did the Portuguese truly blend cultures, and what scars or gifts remained?")
    asyncio.run(fl.run(e7["id"]))
    check("off: unclear grounds take the pre-J-2570 path (judged, would_return, pending)",
          calls["judge"] == 1 and len(rows(fl.SHADOW_LOG, "would_return")) == 1 and rows(fl.SHADOW_LOG, "deferred") == [] and fl.pending_count() == 1)
    fl.DEFER_UNCLEAR = True

    # [8] readers
    print("[8] is_vacuous + status() + settle vacuous flag")
    vac = rows(fl.SHADOW_LOG, "would_return")[0]                      # the flag-off row: grounds unclear
    check("is_vacuous: unclear row True", fl.is_vacuous(vac))
    check("is_vacuous: historic slow empty (no stop secs, row secs 215) True; fast empty False; found False",
          fl.is_vacuous({"kind": "would_return", "stops": {"grounds": {"n": 0, "outcome": "empty"}}, "cargo": {"grounds_outcome": "empty", "grounds": []}, "secs": 215.0})
          and not fl.is_vacuous({"kind": "would_return", "stops": {"grounds": {"n": 0, "outcome": "empty"}}, "cargo": {"grounds_outcome": "empty", "grounds": []}, "secs": 30.0})
          and not fl.is_vacuous({"kind": "would_return", "stops": {"grounds": {"n": 2, "outcome": "found"}}, "cargo": {"grounds_outcome": "found", "grounds": [{}, {}]}, "secs": 300.0}))
    d8 = fl.take_delivery()
    out8 = asyncio.run(fl.settle(d8["q_id"], "no", "No, that is not it.", "cyc8"))
    s8 = rows(fl.SHADOW_LOG, "settled")[-1]
    check("settle on an unclear cargo marks the settled row vacuous", s8["vacuous"] is True and s8["verdict"] == "no")
    # a real return + a legacy settle with no vacuous field answering the vacuous q_id + deferred rows
    fl.DEFER_UNCLEAR = True; fl._stop_grounds = g_found
    e8 = new_entry("What did the Portuguese actually leave behind in Goa?")
    asyncio.run(fl.run(e8["id"]))
    fl._append({"ts": time.time(), "kind": "settled", "q_id": e8["id"], "verdict": "yes"})
    fl._append({"ts": time.time(), "kind": "settled", "q_id": vac["q_id"], "verdict": "unsaid"})     # legacy row, no field
    fl._append({"ts": time.time(), "kind": "deferred", "q_id": "z1", "reason": "gen_dead", "final": False})
    fl._append({"ts": time.time(), "kind": "deferred", "q_id": "z2", "reason": "grounds_unclear", "final": True})
    st = fl.status()
    check("status: would_return counts all (2), vacuous 1; breakdowns skip it; settled skips both vacuous settles",
          st["would_return"] == 2 and st["vacuous_would_return"] == 1 and st["judge_a"] == {"yes": 1}
          and st["settled"] == {"yes": 1} and st["vacuous_settled"] == {"no": 1, "unsaid": 1})
    check("status: deferred / unjudged by reason", st["deferred"] == {"gen_dead": 1} and st["unjudged"] == {"grounds_unclear": 1})
    fl.FOLLOW_LINE = "shadow"

after, after_logs = [_hash_file(p) for p in CANARY], logs_fp()
check("CANARY: live stores byte-identical", before == after)
check("CANARY: live data/logs/ untouched (names, sizes, mtimes)", before_logs == after_logs)
print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

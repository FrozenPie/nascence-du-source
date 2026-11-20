"""
Hermetic test for J-2910 (F-3592, F-3597; P-0044): the Follow Line makes no consequences from an empty cargo, and an
empty cargo's `settled: yes` writes no closure fragment. No LLM, no embedder, no live data. Runs inside
lab_env.isolate(db="empty") with the frontier / follow_line / coupling / closure logs redirected into the lab dir; every
stop and the judge are deterministic fakes. The live data/ tree is fingerprinted before/after.

  [1] no grounds: _stop_consequences is NOT called (no model call), stops.consequences = skipped no-grounds, the
      return is "Your past holds little on this." + the closing question and has no "If this is so", nothing re-boards
  [2] grounds present: stop 3 runs as before, the consequence is rendered and re-boarded
  [3] flag off (NO_CONSEQUENCES_WITHOUT_GROUNDS False): the pre-J-2910 path (stop runs on empty grounds)
  [4] intention lines ("I will ...", "I can ...", "I would ...") are dropped from the cargo, state-of-the-world lines
      kept, the drop is counted on the row; flag off keeps them
  [5] closure.record_line_settled: cargo with grounds key and none -> one shadow row compose_how skipped-no-grounds,
      NO compose call, NO live write; a cargo with grounds composes and writes as before; a cargo without a grounds key
      (unknown) composes as before; LINE_SKIP_NO_GROUNDS False restores the pre-J-2910 path
  [6] settle("yes") on a delivered no-grounds return: frontier resolved, closure_how skipped-no-grounds, no fragment

Run:  python scripts/_test_J-2910_empty_cargo.py   (from the tree under test)
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
from core import closure as cl
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
CANARY = [LIVE / "frontier.json", LIVE / "memory" / "nascence.db", LIVE / "logs" / "follow_line_shadow.jsonl",
          LIVE / "logs" / "closure_shadow.jsonl", LIVE / "coupling_rides.jsonl", LIVE / "evidence_log.jsonl"]
before = [_hash_file(p) for p in CANARY]

ALSO = [(fr, ["_F", "_SEM_SHADOW_LOG"]), (fl, ["SHADOW_LOG"]), (cr, ["_LOG"]), (ev, ["_LOG"]), (sat, ["_LOG", "_STATE"]),
        (cl, ["SHADOW_LOG"])]

with isolate(also=ALSO, db="empty") as lab_dir:
    print(f"lab dir: {lab_dir}")
    fr.FRONTIER_SEMANTIC_MERGE = None
    cr._DATA = lab_dir
    fl.FOLLOW_LINE = "live"
    calls = {"cons": 0}
    G = {"grounds": [{"fragment_id": "f_a", "origin": "reading", "age": "a month ago", "strength": "bears",
                      "text": "Albuquerque ordered Portuguese soldiers to marry local women in Goa in 1510."}],
         "grounds_outcome": "found"}
    async def g_found(q, train_id): return dict(G)
    async def g_empty(q, train_id): return {"grounds": [], "grounds_outcome": "empty"}
    async def m_why(q, grounds):
        if not grounds:
            return {"text": "", "cites": [], "supports": "no", "skipped": "no-grounds"}
        return {"text": "Because [1] shows the mixing was ordered from above.", "cites": [1], "supports": "yes"}
    CONS = [{"text": "Then Goa's creole families trace to the first decades.", "slot": "when", "checkable": "memory"}]
    async def m_cons(q, grounds, why): calls["cons"] += 1; return [dict(c) for c in CONS]
    async def m_conn(q): return {"know": [], "can_do": [], "seen": []}
    async def m_against(q, grounds): return {"text": "", "cites": [], "scope": "", "skipped": "test"}
    async def m_judge(q, cargo, q_id=""):
        b = "yes" if cargo.get("consequences") else "no"
        return {"a": "yes" if cargo.get("grounds") else "no", "b": b, "c": "no", "a_how": "agreed", "b_how": "agreed", "c_how": "agreed"}
    async def m_own(q): return {}
    fl._stop_why, fl._stop_consequences, fl._stop_connections, fl._stop_against, fl._judge = m_why, m_cons, m_conn, m_against, m_judge
    fl._stop_own_test = m_own

    def new_entry(q):
        return fr.note_question_ex(q, "asked", slot="how", about="Goa", asked_by={"train_id": "t_x", "ts": time.time()}, allow_self=True)

    # [1] no grounds
    print("[1] no grounds -> no consequences")
    reset(); fl._stop_grounds = g_empty; calls["cons"] = 0
    e = new_entry("how did the Portuguese truly blend cultures, and what scars or gifts remained?")
    n_before = len(fr._load()["questions"])
    asyncio.run(fl.run(e["id"]))
    w = rows(fl.SHADOW_LOG, "would_return")[-1]
    check("stop 3 never called", calls["cons"] == 0)
    check("stops.consequences skipped no-grounds, cargo has none", w["stops"]["consequences"] == {"n": 0, "skipped": "no-grounds"} and w["cargo"]["consequences"] == [])
    t = w["return_text"]
    check("return is the plain 'Your past holds little' + closing question, no 'If this is so'",
          "Your past holds little on this." in t and "If this is so" not in t and t.endswith(fl.RETURN_CLOSING))
    check("nothing re-boarded", len(fr._load()["questions"]) == n_before)
    check("render() alone also refuses consequences without grounds (a stale cargo shape)",
          "If this is so" not in fl.render(fr.get(e["id"]), {"grounds": [], "grounds_outcome": "empty", "consequences": CONS},
                                           {"a": "no", "b": "yes", "c": "skipped"}))

    # [2] grounds present
    print("[2] grounds present -> unchanged")
    reset(); fl._stop_grounds = g_found; calls["cons"] = 0
    e = new_entry("how did the Portuguese truly blend cultures, and what scars or gifts remained?")
    asyncio.run(fl.run(e["id"]))
    w = rows(fl.SHADOW_LOG, "would_return")[-1]
    check("stop 3 called once, consequence kept, rendered, a re-boarding exists",
          calls["cons"] == 1 and w["stops"]["consequences"] == {"n": 1} and "If this is so: Then Goa" in w["return_text"]
          and any(q.get("source") == "consequence" for q in fr._load()["questions"]))

    # [3] flag off
    print("[3] flag off -> pre-J-2910")
    reset(); fl._stop_grounds = g_empty; calls["cons"] = 0
    fl.NO_CONSEQUENCES_WITHOUT_GROUNDS = False
    e = new_entry("did the dragonfly cross the whole bay in one flight, or did it rest on the reeds?")
    asyncio.run(fl.run(e["id"]))
    w = rows(fl.SHADOW_LOG, "would_return")[-1]
    check("stop 3 called on empty grounds again", calls["cons"] == 1 and w["stops"]["consequences"] == {"n": 1})
    fl.NO_CONSEQUENCES_WITHOUT_GROUNDS = True

    # [4] intention lines
    print("[4] intention lines dropped")
    reset(); fl._stop_grounds = g_found; calls["cons"] = 0
    CONS[:] = [{"text": "I will seek out opportunities for family gatherings.", "slot": "how", "checkable": "self"},
               {"text": "I can find a calm and distraction-free environment to read.", "slot": "how", "checkable": "self"},
               {"text": "Goa's creole families trace to the first decades after 1510.", "slot": "when", "checkable": "memory"},
               {"text": "I would notice the shore changed after the storm.", "slot": "what", "checkable": "self"}]
    e = new_entry("how did the Portuguese truly blend cultures, and what scars or gifts remained?")
    asyncio.run(fl.run(e["id"]))
    w = rows(fl.SHADOW_LOG, "would_return")[-1]
    check("only the world statement kept; 3 dropped and counted",
          [c["text"] for c in w["cargo"]["consequences"]] == ["Goa's creole families trace to the first decades after 1510."]
          and {k: v for k, v in w["stops"]["consequences"].items() if k != "dropped_texts"} == {"n": 1, "dropped_intention": 3})   # J-4052: J-3928 added dropped_texts
    check("no 'I will' / 'I can' in the delivered text", "I will" not in w["return_text"] and "I can" not in w["return_text"])
    check("matcher: 'I crossed my lines' / 'The water would rise' are kept",
          not fl._INTENTION.match("I crossed my lines") and not fl._INTENTION.match("The water would rise") and fl._INTENTION.match("I'll go"))
    fl.DROP_INTENTION_CONSEQUENCES = False
    check("flag off keeps every line", fl.drop_intentions(CONS) == (CONS, 0))
    fl.DROP_INTENTION_CONSEQUENCES = True

    # [5] closure
    print("[5] closure.record_line_settled")
    composes = []
    def fake_compose(system, user): composes.append(user); return {"resolution": "I hold that the grounds were what I had, and I say so plainly. The old records I found agreed with each other, and my first thought matched them. Nothing came back that cut against it, so I keep it as it stands, though thinly, and I would look again if something new turned up."}
    live = []
    cl._compose_sync = fake_compose
    _wl = cl._write_live
    cl._write_live = lambda wb: (live.append(wb), "fid-1")[1]
    ent = {"id": "e_empty", "q": "did the goldfinches change the soil?", "about_key": "k1"}
    r0 = cl.record_line_settled(ent, {"grounds": [], "grounds_outcome": "empty", "status": "undetermined"}, "yes, settled")
    check("empty cargo: skipped-no-grounds row, no compose, no live write, no would_be",
          r0["compose_how"] == "skipped-no-grounds" and composes == [] and live == [] and r0["would_be"] is None and not r0["written_live"])
    check("the row is in the closure shadow log (arm line, kind resolution)",
          [(x["arm"], x["kind"], x["compose_how"]) for x in rows(cl.SHADOW_LOG)] == [("line", "resolution", "skipped-no-grounds")])
    r1 = cl.record_line_settled({"id": "e_g", "q": "q one?", "about_key": "k2"},
                                {"grounds": [{"origin": "a book", "text": "g1"}], "status": "held"}, "yes, settled")
    check("cargo with grounds composes and writes as before", r1["compose_how"] == "ok" and len(composes) == 1 and len(live) == 1 and r1["written_live"])
    r2 = cl.record_line_settled({"id": "e_u", "q": "q two?", "about_key": "k3"}, {"status": "held"}, "yes")
    check("cargo with no grounds KEY (unknown) composes as before", r2["compose_how"] == "ok" and len(live) == 2)
    cl.LINE_SKIP_NO_GROUNDS = False
    r3 = cl.record_line_settled({"id": "e_off", "q": "q three?", "about_key": "k4"}, {"grounds": []}, "yes")
    check("flag off: empty cargo composes again", r3["compose_how"] == "ok" and len(live) == 3)
    cl.LINE_SKIP_NO_GROUNDS = True
    cl._write_live = _wl

    # [6] settle end to end
    print("[6] settle yes on a no-grounds return")
    reset(); fl._stop_grounds = g_empty
    cl._write_live = lambda wb: (live.append(wb), "fid-x")[1]
    n_live = len(live); n_comp = len(composes)
    e = new_entry("what did the second robin pair do differently with the mud this year?")
    asyncio.run(fl.run(e["id"]))
    d = fl.take_delivery()
    check("delivered, plain text", d is not None and "Your past holds little on this." in d["text"] and "If this is so" not in d["text"])
    out = asyncio.run(fl.settle(e["id"], "yes", "Yes, that settles it.", "cyc1"))
    check("frontier entry resolved by his word", out["resolved"] is True)
    check("closure arm skipped, no compose, no live write",
          (out["closure"] or {}).get("compose_how") == "skipped-no-grounds" and len(composes) == n_comp and len(live) == n_live)
    sr = rows(fl.SHADOW_LOG, "settled")[-1]
    check("settled row carries closure_how skipped-no-grounds", sr["closure_how"] == "skipped-no-grounds")
    cl._write_live = _wl

after = [_hash_file(p) for p in CANARY]
check("live data untouched (frontier, nascence.db, follow_line + closure logs, rides, evidence)", before == after)
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

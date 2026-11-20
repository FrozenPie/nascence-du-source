"""
Hermetic test for J-2459 (docs/staged/question_cargo.md, Phase 0): THE FOLLOW LINE in shadow.

No LLM, no embedder, no live data. Runs INSIDE lab_env.isolate(db="empty") with every module-level store path the
line touches redirected into the lab dir via `also=`; every stop and the judge are deterministic fakes; the hot
tier, the CPU tiers and Ramses are never contacted. The real data/ tree is never written (the caller fingerprints
the live stores before/after -- see the canary at the bottom).

  [1] flag + schema: FOLLOW_LINE="off" -> schema/rule fragments "" and parse_ask == ("", ""); "shadow" -> the ask
      field is in the schema, the rule names the six slot kinds, parse_ask validates slot and length
  [2] frontier birth: note_question_ex stamps kind/slot/about/asked_by/about_key and line.state="waiting"; a
      re-encounter refreshes and (if unlined) stamps waiting; note_question() wrapper still returns bool; with the
      line OFF a birth carries NO line field and no new fields (exact pre-existing shape); allow_self lets a
      self-question through for the line only
  [3] waiting_for_line: PRIORITY order (asked > claim > study > intention > pursuit > curiosity > prism > dream),
      NEWEST first within a source (D-0611); closed/unlined entries excluded
  [4] claim door: write_or_revise boards a NEW note's first sentence as kind=claim, source=claim, and boards
      NOTHING on a revision; _first_sentence floors
  [5] pursuit door: _apply_confirmed with a fresh "?" boards source=pursuit with pursuit_id; no "?" boards nothing
  [6] fire/cap: one in flight at a time (wait-in-flight logged), 4 per rolling hour (5th -> wait-cap), no loop ->
      wait-no-loop; the done-callback carries the id and clears in_flight
  [7] run(): with mocked stops + judge -> one kind="would_return" row with the typed cargo, the stops summary,
      the judged dict, the rendered return text (origin phrase, grounds with provenance, why, "If this is so",
      "It touches", "Does it hold"), status "undetermined" (stop 5 unbuilt); line.state == "would_return";
      consequences re-board at depth 1 (b=yes) as source=consequence kind=claim; the same about_key does not
      re-board twice in 24 h; depth > MAX_DEPTH never boards; judges-down renders "could not get a clear look",
      empty grounds renders "Your past holds little"; the coordinate publish carries no prose
  [8] drain_tick: fires the top waiting entry, nothing while in flight

Run:  python scripts/follow_line_test.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, hashlib, json, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423): the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import follow_line as fl
from core import frontier as fr
from core import coupling_rides as cr
from core import procedures as pr
from core import pursuits as pu
from core import study_note as sn
from core import evidence_recall as ev
from core import satisfaction as sat
from core import profile
_real_judge = fl._judge                      # captured before any section stubs fl._judge (D-0596 section)
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

def reset_state():
    fl._board_log.clear(); fl._in_flight = None; fl._TASKS.clear(); fl._recent_keys.clear(); fl._live_warned = False

LIVE = Path(r"C:\Nascence\data")
CANARY = [LIVE / "frontier.json", LIVE / "monologue_log.jsonl", LIVE / "memory" / "nascence.db",
          LIVE / "logs" / "follow_line_shadow.jsonl", LIVE / "coupling_rides.jsonl", LIVE / "pursuits_active.json",
          LIVE / "procedures.json", LIVE / "evidence_log.jsonl", LIVE / "frontier.light.json"]
def logs_dir_fingerprint():
    d = LIVE / "logs"
    if not d.exists():
        return None
    return sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in d.iterdir() if p.is_file()
                  and not (p.name == "supervisor_events.log" or p.name.startswith("cpu_tier_")))   # J-2969: the hub supervisor writes these while the test runs
before = [(_hash_file(p)) for p in CANARY]
before_logs = logs_dir_fingerprint()

ALSO = [(fr, ["_F", "_SEM_SHADOW_LOG"]), (fl, ["SHADOW_LOG"]), (cr, ["_LOG"]), (pr, ["_F", "_LOG"]),
        (pu, ["_ACTIVE", "_SHADOW"]), (ev, ["_LOG"]), (sat, ["_LOG", "_STATE"])]

with isolate(also=ALSO, db="empty") as lab_dir:
    print(f"lab dir: {lab_dir}")
    fr.FRONTIER_SEMANTIC_MERGE = None          # no embedder in this test; the token dedupe path is what we exercise
    cr._DATA = lab_dir                         # coupling_rides mkdirs _DATA before writing _LOG
    pu._DIR = lab_dir
    pr._DATA = lab_dir

    # ── [1] flag + schema ───────────────────────────────────────────────────────────────────────────────────
    print("[1] flag + schema")
    fl.FOLLOW_LINE = "off"; reset_state()
    check("off: schema fragment empty", fl.schema_fragment() == "")
    check("off: rule fragment empty", fl.rule_fragment() == "")
    check("off: parse_ask ignores a filled field", fl.parse_ask({"ask": {"q": "why does the tide turn?", "slot": "why"}}) == ("", ""))
    fl.FOLLOW_LINE = "shadow"
    check("shadow: ask in schema", fl.schema_fragment() == ', "ask": {"q": "", "slot": ""}')
    check("shadow: rule names the six kinds (option A constant)", "who, what, when, where, why, or how" in fl.rule_fragment())
    saved_kinds = fl.ASK_SLOT_KINDS
    fl.ASK_SLOT_KINDS = ""
    check("option B: blanking the constant drops the list", "who, what" not in fl.rule_fragment() and 'slot: leave as ""' in fl.rule_fragment())
    fl.ASK_SLOT_KINDS = saved_kinds
    check("parse: slot validated + lowercased", fl.parse_ask({"ask": {"q": "how did the Portuguese blend cultures?", "slot": "How"}}) == ("how did the Portuguese blend cultures?", "how"))
    check("parse: bad slot -> ''", fl.parse_ask({"ask": {"q": "how did the Portuguese blend cultures?", "slot": "maybe"}})[1] == "")
    check("parse: short / malformed / absent -> empty", fl.parse_ask({"ask": {"q": "why?", "slot": "why"}}) == ("", "")
          and fl.parse_ask({"ask": "why"}) == ("", "") and fl.parse_ask({}) == ("", "") and fl.parse_ask(None) == ("", ""))
    fl.FOLLOW_LINE = "live"
    check("live: enabled (Phase 1 built, D-0494 (3))", fl.enabled())
    fl.FOLLOW_LINE = "shadow"

    # ── [2] frontier birth ──────────────────────────────────────────────────────────────────────────────────
    print("[2] frontier birth")
    fl.FOLLOW_LINE = "off"
    assert fr.note_question("What makes the oystercatcher scream at the receding tide?", "curiosity") is True
    e_off = fr._load()["questions"][-1]
    check("off: birth has no line field and no new fields (pre-existing shape)",
          "line" not in e_off and "kind" not in e_off and set(e_off) == {"id", "q", "source", "toks", "born", "last_seen", "last_offered", "offers", "encounters", "status"})
    fl.FOLLOW_LINE = "shadow"
    e_ask = fr.note_question_ex("how did the Portuguese truly blend cultures, and what scars or gifts remained?", "asked",
                                kind="question", slot="how", about="Portuguese integration",
                                asked_by={"train_id": "t_abc123", "ledger_idx": 2, "cycle_id": "c1", "ts": time.time()}, allow_self=True)
    check("asked birth: entry returned with id", bool(e_ask) and len(e_ask["id"]) == 10)
    check("asked birth: kind/slot/about/asked_by/about_key stamped",
          e_ask["kind"] == "question" and e_ask["slot"] == "how" and e_ask["about"] == "Portuguese integration"
          and e_ask["asked_by"]["train_id"] == "t_abc123" and e_ask["about_key"] == e_ask["id"])
    check("asked birth: line.state waiting, depth 0, via asked", e_ask["line"]["state"] == "waiting" and e_ask["line"]["depth"] == 0 and e_ask["line"]["via"] == "asked")
    e_re = fr.note_question_ex("How did the Portuguese truly blend cultures, and what scars or gifts remained", "intention")
    check("re-encounter: same entry refreshed (encounters 2), still waiting", e_re["id"] == e_ask["id"] and e_re["encounters"] == 2 and e_re["line"]["state"] == "waiting")
    fr.set_line(e_ask["id"], state="would_return")
    e_re2 = fr.note_question_ex("how did the portuguese truly blend cultures and what scars or gifts remained?", "curiosity")
    check("re-encounter of a lined entry does not reset its state", e_re2["line"]["state"] == "would_return")
    e_self = fr.note_question_ex("why do I keep circling my own identity instead of the garden?", "asked", slot="why", allow_self=True)
    check("allow_self: a self-question boards for the line", bool(e_self) and e_self["slot"] == "why")
    check("default filter: the same self-question is refused for an ordinary caller", fr.note_question("why do I keep circling my own identity instead of the garden?", "intention") is False)
    check("ordinary birth under shadow: stamped waiting, source kept", fr.note_question("Why do granite coatings form on shore stones?", "curiosity") is True
          and fr._load()["questions"][-1]["line"]["state"] == "waiting" and fr._load()["questions"][-1]["source"] == "curiosity")
    check("get(): a copy by id", fr.get(e_ask["id"])["q"].startswith("how did the Portuguese") and fr.get("nope") is None)
    check("set_line(): merges and stamps ts; unknown id False", fr.set_line(e_ask["id"], stops={"grounds": 1}) and fr.get(e_ask["id"])["line"]["stops"] == {"grounds": 1}
          and fr.get(e_ask["id"])["line"]["state"] == "would_return" and fr.set_line("nope", state="x") is False)

    # ── [3] waiting_for_line priority ──────────────────────────────────────────────────────────────────────
    print("[3] waiting_for_line")
    fr._save({"questions": []})
    births = [("dream", "Was the dream shore the same shore as the one below the study?"),
              ("curiosity", "What psychological effects does resource scarcity have on whaling crews?"),
              ("prism", "How does a gull decide which mussel is worth the fight?"),
              ("study", "Why does mud let a robin's nest hold where straw alone slips?"),
              ("intention", "What did the Portuguese actually leave behind in Goa?"),
              ("claim", "Bonaparte's restraint was a tool rather than a virtue in the Consulate years"),
              ("asked", "Where does the bladderwrack go when the tide strips it from the rock?"),
              ("pursuit", "When did the hedgehog first vanish from the garden this year?")]
    ids = {}
    for i, (src, q) in enumerate(births):
        e = fr.note_question_ex(q, src, kind="claim" if src == "claim" else "question", allow_self=True)
        assert e, (src, q)
        ids[src] = e["id"]
        d = fr._load()
        for x in d["questions"]:
            if x["id"] == e["id"]:
                x["born"] = 1000.0 + i          # distinct, increasing birth times
        fr._save(d)
    e2 = fr.note_question_ex("Why is the second robin pair's mud nest the one that holds?", "study", allow_self=True)
    d = fr._load()
    for x in d["questions"]:
        if x["id"] == e2["id"]:
            x["born"] = 999.0                   # an OLDER study question
    fr._save(d)
    fr.set_line(ids["prism"], state="would_return")
    order = [x["source"] for x in fr.waiting_for_line(fl.PRIORITY)]
    wl = fr.waiting_for_line(fl.PRIORITY)
    check("priority order, NEWEST first within a source (D-0611), lined entry excluded",
          order == ["asked", "claim", "study", "study", "intention", "pursuit", "curiosity", "dream"]
          and wl[2]["id"] == ids["study"] and wl[3]["id"] == e2["id"])
    # D-0611: a 2-ask queue -- the freshly born ask is served before the older one, and drain_tick's head is the newest
    fr._save({"questions": []})
    old_a = fr.note_question_ex("Where does the bladderwrack go when the tide strips it from the rock?", "asked", allow_self=True)
    new_a = fr.note_question_ex("Why does the heron stand on one leg at the weir in the morning?", "asked", allow_self=True)
    d = fr._load()
    for x in d["questions"]:
        x["born"] = 500.0 if x["id"] == old_a["id"] else 9000.0
    fr._save(d)
    q2 = fr.waiting_for_line(fl.PRIORITY)
    check("D-0611: two waiting asks -> the newer-born is first", [x["id"] for x in q2] == [new_a["id"], old_a["id"]])
    # MAX_OPEN eviction agrees: the least-recently-seen entry (the last the line would reach) is the one that fades
    d = fr._load()
    for x in d["questions"]:
        x["last_seen"] = 100.0 if x["id"] == old_a["id"] else 9000.0
    fr._save(d)
    saved_max = fr.MAX_OPEN
    fr.MAX_OPEN = 2
    try:
        fr.note_question_ex("What keeps the harbour wall's weed alive above the high-water line?", "asked", allow_self=True)
    finally:
        fr.MAX_OPEN = saved_max
    st = {x["id"]: x["status"] for x in fr._load()["questions"]}
    check("D-0611: MAX_OPEN eviction fades the oldest-seen (the one served last), not the newest", st[old_a["id"]] == "faded" and st[new_a["id"]] == "open")

    # ── [4] claim door (study notes) ───────────────────────────────────────────────────────────────────────
    print("[4] claim door")
    fr._save({"questions": []}); reset_state()
    check("_first_sentence: first sentence, floor 20, cap 220",
          sn._first_sentence("I see that Bonaparte did not merely seize power but engineered a transition. What strikes me is X.")
          == "I see that Bonaparte did not merely seize power but engineered a transition."
          and sn._first_sentence("Short one.") == "" and len(sn._first_sentence("I " + "see " * 200 + ".")) == 220)
    note = {"title": "Bonaparte", "subject": "political maneuvering", "key_facts": [], "thoughts": "", "connects_to": "", "question": "",
            "understanding": "I see that Bonaparte engineered a transition from republic to monarchy by deception. What strikes me is his restraint."}
    async def fake_compose(call_json, base_urls, book_title, passage, related_text=""):
        return dict(note)
    async def fake_revise(call_json, base_urls, existing_body, new_note, **kw):   # J-2961: + existing_extra
        return dict(new_note)
    stored = []
    def fake_store(n, book_title, revise_target=None, session=None, **kw):   # J-2961: + prior
        stored.append(revise_target); return {"action": "revised" if revise_target else "new", "path": "", "fragment_id": "f_1", "linked": 0}
    sn.compose_note, sn._revise, sn.store_note = fake_compose, fake_revise, fake_store
    sn._related_context = lambda bt, p: ("", [])
    sn._log_m1_co_recall = lambda *a, **k: None
    sn.find_revisable = lambda n, **k: None
    fired = []
    real_fire = fl.fire
    fl.fire = lambda qid: fired.append(qid) or False
    out = asyncio.run(sn.write_or_revise(None, [], "Memoirs of Napoleon", "passage text", session=[{"pass": 2, "encounter_id": "e9"}]))
    q = fr._load()["questions"]
    check("new note -> one CLAIM boarded, source=claim, kind=claim, book + pass + fragment in asked_by, fire called",
          out["action"] == "new" and len(q) == 1 and q[0]["source"] == "claim" and q[0]["kind"] == "claim"
          and q[0]["q"].startswith("I see that Bonaparte engineered") and q[0]["asked_by"]["book_title"] == "Memoirs of Napoleon"
          and q[0]["asked_by"]["pass"] == 2 and q[0]["asked_by"]["fragment_id"] == "f_1" and q[0]["about"] == "political maneuvering"
          and fired == [q[0]["id"]])
    sn.find_revisable = lambda n, **k: ("f_1", "old body", "")
    out2 = asyncio.run(sn.write_or_revise(None, [], "Memoirs of Napoleon", "passage text"))
    check("revision -> nothing boards", out2["action"] == "revised" and len(fr._load()["questions"]) == 1 and len(fired) == 1)
    fl.fire = real_fire

    # ── [5] pursuit door ───────────────────────────────────────────────────────────────────────────────────
    print("[5] pursuit door")
    fr._save({"questions": []})
    p = {"id": "p_77", "question": "the garden", "about": "the garden", "thoughts": [], "established": [], "open": "", "heat": 0.2, "status": "active", "advances": 0}
    pu._apply_confirmed(p, {"thought": "The seeds took in the wet bed. But when did the hedgehog first vanish from the garden this year?", "about": "the garden", "coherent": True}, time.time())
    q = fr._load()["questions"]
    check("confirmed advance with a '?' -> source=pursuit boarded with pursuit_id",
          "when did the hedgehog" in p["open"] and len(q) == 1 and q[0]["source"] == "pursuit" and q[0]["asked_by"]["pursuit_id"] == "p_77"
          and q[0]["about"] == "the garden")
    pu._apply_confirmed(p, {"thought": "The seeds took in the wet bed and the rain kept on.", "about": "the garden", "coherent": True}, time.time())
    check("advance without a '?' -> nothing boards (open sticky)", len(fr._load()["questions"]) == 1)

    # ── [6] fire / cap / in-flight / no loop ───────────────────────────────────────────────────────────────
    print("[6] fire / cap")
    fr._save({"questions": []}); reset_state()
    ran = []
    async def fake_run(qid):
        ran.append(qid); await asyncio.sleep(0); return {"q_id": qid}
    real_run = fl.run; fl.run = fake_run
    _cap_default = fl.BOARD_CAP_PER_HOUR
    check("shipped default is NO rolling-hour cap (founder 2026-11-08)", _cap_default is None)
    fl.BOARD_CAP_PER_HOUR = 4                       # the checks below exercise the opt-in cap path
    six =["Why does the shore sound differ at ebb and at flood?",
           "What makes the kingfisher dive where the water is cloudiest?",
           "When did the cuckoo last call from the wood this spring?",
           "Where do the gulls carry the mussels they steal from each other?",
           "How does bladderwrack keep its grip on a stone the tide strips twice a day?",
           "Who taught the robins that mud holds where straw slips?"]
    ents = [fr.note_question_ex(q, "asked", allow_self=True) for q in six]
    assert all(ents) and len({e["id"] for e in ents}) == 6, "six distinct entries (token dedupe would merge near-duplicates)"
    check("no running loop -> wait-no-loop, nothing fired", fl.fire(ents[0]["id"]) is False and fl._in_flight is None)
    async def drive():
        r1 = fl.fire(ents[0]["id"])
        r2 = fl.fire(ents[1]["id"])                 # in flight -> False
        inflight_now = fl._in_flight
        await asyncio.sleep(0.01)
        cleared = fl._in_flight is None
        r3 = fl.fire(ents[1]["id"]); await asyncio.sleep(0.01)
        r4 = fl.fire(ents[2]["id"]); await asyncio.sleep(0.01)
        r5 = fl.fire(ents[3]["id"]); await asyncio.sleep(0.01)
        r6 = fl.fire(ents[4]["id"]); await asyncio.sleep(0.01)   # 5th within the hour -> cap
        return r1, r2, inflight_now, cleared, r3, r4, r5, r6
    r1, r2, inflight_now, cleared, r3, r4, r5, r6 = asyncio.run(drive())
    fires = rows(fl.SHADOW_LOG, "ride")
    outcomes = [r["value"]["outcome"] for r in fires if r["value"]["stop_name"] == "fire"]
    check("first fires; second waits in flight; callback clears in_flight; fire() stamps line.state=fired",
          r1 and not r2 and inflight_now == ents[0]["id"] and cleared and ran[:1] == [ents[0]["id"]]
          and fr.get(ents[0]["id"])["line"]["state"] == "fired" and fr.get(ents[5]["id"])["line"]["state"] == "waiting")
    check("4 per rolling hour: 2nd-4th fire, 5th waits on the cap", r3 and r4 and r5 and not r6 and len(ran) == 4
          and outcomes == ["wait-no-loop", "fired", "wait-in-flight", "fired", "fired", "fired", "wait-cap"])
    fl._board_log.clear()
    fl._board_log.extend([time.time() - 3700] * 4)
    async def one(): r = fl.fire(ents[4]["id"]); await asyncio.sleep(0.01); return r
    check("the window rolls: four old boardings do not count", asyncio.run(one()) and len(ran) == 5)
    fl.BOARD_CAP_PER_HOUR = None                    # uncapped: fifty boardings this hour still fire
    fl._board_log.clear(); fl._board_log.extend([time.time()] * 50)
    async def two(): r = fl.fire(ents[5]["id"]); await asyncio.sleep(0.01); return r
    check("uncapped: 50 boardings in the hour do not block a fire", asyncio.run(two()) and len(ran) == 6)
    fl.BOARD_CAP_PER_HOUR = _cap_default
    fl.run = real_run

    # ── [7] run() with mocked stops + judge ────────────────────────────────────────────────────────────────
    print("[7] run()")
    fr._save({"questions": []}); reset_state()
    if fl.SHADOW_LOG.exists(): fl.SHADOW_LOG.unlink()
    G = {"grounds": [{"fragment_id": "f_a", "origin": "reading", "age": "a month ago", "strength": "bears",
                      "text": "Albuquerque ordered Portuguese soldiers to marry local women in Goa in 1510."},
                     {"fragment_id": "f_b", "origin": "study", "age": "two weeks ago", "strength": "may_bear",
                      "text": "The Crown's policy of mixed marriage was deliberate, not emergent."}],
         "grounds_outcome": "found"}
    calls = {"grounds": [], "why": [], "cons": [], "conn": [], "judge": []}
    async def m_grounds(q, train_id): calls["grounds"].append((q, train_id)); return dict(G)
    async def m_why(q, grounds):
        calls["why"].append(len(grounds)); return {"text": "Because [1] and [2] show the mixing was ordered from above, not grown from below.", "cites": [1, 2], "supports": "yes"}
    async def m_cons(q, grounds, why):
        calls["cons"].append(1); return [{"text": "Then Goa's creole families should trace to the first decades, not later.", "slot": "when", "checkable": "memory"},
                                        {"text": "Then the same pattern should show in Macau under the same Crown.", "slot": "where", "checkable": "memory"}]
    async def m_conn(q):
        calls["conn"].append(1); return {"know": [{"fragment_id": "f_k", "origin": "reading", "text": "Macau was settled under a different charter.", "slots": ["what"]}],
                                        "can_do": [{"key": "world:bank_the_fire", "statement": "banked a fire and it held", "rung": "persisted"}],
                                        "seen": [{"fragment_id": "f_s", "origin": "lived", "text": "the orange net tangled on the slick stones", "sim": 0.41}]}
    async def m_judge(q, cargo, q_id=""): calls["judge"].append(q_id); return {"a": "yes", "b": "yes", "a_how": "agreed", "b_how": "agreed"}
    fl._stop_grounds, fl._stop_why, fl._stop_consequences, fl._stop_connections, fl._judge = m_grounds, m_why, m_cons, m_conn, m_judge
    async def m_against0(q, grounds): return {"text": "", "cites": [], "scope": "", "skipped": "test"}
    fl._stop_against = m_against0
    e = fr.note_question_ex("how did the Portuguese truly blend cultures, and what scars or gifts remained?", "asked", slot="how",
                            about="Portuguese integration", asked_by={"train_id": "t_f0cf5e", "ledger_idx": 1, "ts": time.time()}, allow_self=True)
    row = asyncio.run(fl.run(e["id"]))
    wr = rows(fl.SHADOW_LOG, "would_return")
    check("one would_return row, nothing delivered anywhere", row is not None and len(wr) == 1 and wr[0]["q_id"] == e["id"])
    r0 = wr[0]
    check("row carries typed cargo + stops + judged + train_id + about_key, status undetermined",
          r0["cargo"]["grounds_outcome"] == "found" and len(r0["cargo"]["grounds"]) == 2 and r0["cargo"]["why"]["supports"] == "yes"
          and len(r0["cargo"]["consequences"]) == 2 and r0["cargo"]["connections"]["can_do"][0]["key"] == "world:bank_the_fire"
          and r0["stops"]["grounds"]["n"] == 2 and r0["judged"]["a"] == "yes" and r0["train_id"] == "t_f0cf5e"
          and r0["about_key"] == e["id"] and r0["cargo"]["status"] == "undetermined" and r0["source"] == "asked" and r0["slot"] == "how")
    t = r0["return_text"]
    check("render: origin phrase names what it was about", t.startswith('Something you asked just now, about Portuguese integration: "how did the Portuguese'))
    check("render: grounds with provenance, the why, consequences, connections, the closing question",
          "In reading, a month ago: Albuquerque" in t and "Because [1] and [2]" in t and "If this is so: Then Goa's" in t
          and "It touches: Macau was settled" in t and "something you have done before: bank the fire" in t and t.endswith("Does it hold, or only part of it?"))
    check("render: no instruction to act ('you could' absent)", "you could" not in t.lower() and "you should" not in t.lower())
    check("stops saw the claim and the train id; judge saw the id", calls["grounds"] == [(e["q"], "t_f0cf5e")] and calls["why"] == [2] and calls["judge"] == [e["id"]])
    ent_after = fr.get(e["id"])
    check("line.state would_return with summary cargo (no prose)", ent_after["line"]["state"] == "would_return" and ent_after["line"]["cargo"]["why_supports"] == "yes"
          and ent_after["line"]["cargo"]["n_consequences"] == 2 and "text" not in json.dumps(ent_after["line"]["cargo"]))
    cons_entries = [x for x in fr._load()["questions"] if x["source"] == "consequence"]
    check("b=yes -> consequences re-board at depth 1, kind claim, parent id + about_key carried, waiting",
          len(cons_entries) == 2 and all(x["kind"] == "claim" and x["line"]["depth"] == 1 and x["line"]["state"] == "waiting"
                                         and x["asked_by"]["parent_q_id"] == e["id"] and x["asked_by"]["about_key"] == e["id"] for x in cons_entries)
          and cons_entries[0]["slot"] == "when")
    pubs = rows(cr._LOG, "publish")
    check("coupling publish: coordinate only, no prose",
          any(p["loop"] == "follow" and p["tuple"].get("state") == "would_return" for p in pubs)
          and all(set(p["tuple"]) <= {"q_id", "kind", "source", "slot", "state", "status"} for p in pubs if p["loop"] == "follow"))
    rides = rows(fl.SHADOW_LOG, "ride")
    check("ride rows carry {stop, line, dose, value}", all({"stop", "line", "dose", "value"} <= set(r) for r in rides)
          and any(r["line"] == "evidence:follow" for r in rides) and any(r["line"] == "follow_line:return" for r in rides))
    # the same about_key again within 24 h -> skip; depth beyond MAX_DEPTH -> skip
    n_before = len(fr._load()["questions"])
    fl.board("Then Goa's creole families should trace to the first decades, not later.", "consequence", kind="claim",
             asked_by={"parent_q_id": e["id"], "about_key": e["id"]}, allow_self=True, depth=1)
    fl.board("Then something else entirely about Goa should also show in the record somewhere.", "consequence", kind="claim",
             asked_by={"parent_q_id": "x", "about_key": "fresh_key"}, allow_self=True, depth=fl.MAX_DEPTH + 1)
    skips = [r["value"]["outcome"] for r in rows(fl.SHADOW_LOG, "ride") if r["value"]["stop_name"] == "board"]
    check("24 h same-key guard and depth cap both skip and say why",
          len(fr._load()["questions"]) == n_before and "skip-reboard-24h" in skips and "skip-depth" in skips)
    # judges down / empty grounds renders honestly
    async def m_judge_down(q, cargo, q_id=""): return {"a": "unclear", "b": "unclear", "a_how": "unavailable", "b_how": "unavailable"}
    fl._judge = m_judge_down
    e3 = fr.note_question_ex("Why did the second robin pair's mud nest hold where the first slipped?", "study", allow_self=True)
    asyncio.run(fl.run(e3["id"]))
    t3 = rows(fl.SHADOW_LOG, "would_return")[-1]["return_text"]
    check("judges down -> 'could not get a clear look', no why, no consequences", "could not get a clear look" in t3 and "Because" not in t3 and "If this is so" not in t3)
    async def m_grounds_empty(q, train_id): return {"grounds": [], "grounds_outcome": "empty"}
    async def m_why_skip(q, grounds): return {"text": "", "cites": [], "supports": "no", "skipped": "no-grounds"}
    fl._stop_grounds, fl._stop_why, fl._judge = m_grounds_empty, m_why_skip, m_judge
    e4 = fr.note_question_ex("Was the dream shore the same shore as the one below the study?", "dream", allow_self=True)
    asyncio.run(fl.run(e4["id"]))
    t4 = rows(fl.SHADOW_LOG, "would_return")[-1]["return_text"]
    check("empty grounds -> 'Your past holds little on this.', origin phrase for a dream", "Your past holds little on this." in t4 and "wondered in a dream" in t4)
    check("stop 5 unbuilt: every row status undetermined", all(r["cargo"]["status"] == "undetermined" for r in rows(fl.SHADOW_LOG, "would_return")))
    # J-2972 (F-3662): stop 1 reports how many identical copies it dropped; n is the honest post-dedupe count and the
    # count is a stop-summary field, not cargo
    async def m_grounds_dd(q, train_id): return {"grounds": [dict(G["grounds"][0])], "grounds_outcome": "found", "grounds_deduped": 2}
    fl._stop_grounds, fl._stop_why, fl._judge = m_grounds_dd, m_why, m_judge
    e5 = fr.note_question_ex("Did the Crown ever reverse the order to marry local women in Goa?", "study", allow_self=True)
    asyncio.run(fl.run(e5["id"]))
    r5 = rows(fl.SHADOW_LOG, "would_return")[-1]
    check("J-2972: stops.grounds carries n == grounds kept and deduped == 2; cargo has no grounds_deduped key",
          r5["stops"]["grounds"]["n"] == 1 and r5["stops"]["grounds"]["deduped"] == 2 and len(r5["cargo"]["grounds"]) == 1
          and "grounds_deduped" not in r5["cargo"])
    check("J-2972: a run with nothing deduped carries no 'deduped' key (shape unchanged)", "deduped" not in r0["stops"]["grounds"])

    # ── [8] drain_tick ─────────────────────────────────────────────────────────────────────────────────────
    print("[8] drain_tick")
    fr._save({"questions": []}); reset_state()
    fl.run = fake_run; ran.clear()
    ea = fr.note_question_ex("What did the Portuguese actually leave behind in Goa?", "intention")
    eb = fr.note_question_ex("Where does the bladderwrack go when the tide strips it from the rock?", "asked", allow_self=True)
    async def d():
        first = fl.drain_tick(); blocked = fl.drain_tick(); await asyncio.sleep(0.01); second = fl.drain_tick(); await asyncio.sleep(0.01)
        return first, blocked, second
    first, blocked, second = asyncio.run(d())
    check("drain fires the asked entry first, nothing while in flight, then the intention", first == eb["id"] and blocked is None and second == ea["id"] and ran == [eb["id"], ea["id"]])
    fl.FOLLOW_LINE = "off"
    check("off: drain_tick and board are inert", fl.drain_tick() is None and fl.board("Why does the tide turn twice a day here?", "asked") is None)
    fl.FOLLOW_LINE = "shadow"; fl.run = real_run

    # ── [9] Phase 1: pending / TTL / cap / delivery / expiry -> finding ────────────────────────────────────
    print("[9] pending + delivery")
    from core import closure as cl
    fr._save({"questions": []}); reset_state(); fl._PENDING.clear(); fl._DELIVERED.clear()
    fl.FOLLOW_LINE = "live"
    fl._stop_grounds, fl._stop_why, fl._stop_consequences, fl._stop_connections, fl._judge = m_grounds, m_why, m_cons, m_conn, m_judge
    async def m_against(q, grounds): return {"text": "But [2] says the policy was deliberate only in Goa, not everywhere.", "cites": [2], "scope": "the claim holds only for Goa"}
    fl._stop_against = m_against
    async def m_judge_c(q, cargo, q_id=""): return {"a": "yes", "b": "yes", "c": "partly", "a_how": "agreed", "b_how": "agreed", "c_how": "split_no_tiebreak"}
    fl._judge = m_judge_c
    e9 = fr.note_question_ex("how did the Portuguese truly blend cultures, and what scars or gifts remained?", "asked", slot="how",
                             about="Portuguese integration", asked_by={"train_id": "t_9", "ts": time.time()}, allow_self=True)
    row9 = asyncio.run(fl.run(e9["id"]))
    check("live: run() places the return in pending; status held_within_scope from judge c=partly; 'Against it' rendered with scope",
          fl.pending_count() == 1 and e9["id"] in fl._PENDING and row9["cargo"]["status"] == "held_within_scope"
          and "Against it: But [2] says" in row9["return_text"] and "(the claim holds only for Goa)" in row9["return_text"]
          and fr.get(e9["id"])["line"]["state"] == "pending")
    check("cargo_status mapping", fl.cargo_status({"a": "yes", "c": "no"}) == "held" and fl.cargo_status({"a": "yes", "c": "yes"}) == "objected"
          and fl.cargo_status({"a": "yes", "c": "skipped"}) == "held_within_scope" and fl.cargo_status({"a": "no", "c": "no"}) == "undetermined"
          and fl.cargo_status({"a": "unclear", "c": "unclear"}) == "undetermined")
    check("schema/rule: settled rides ONLY on a delivering tick", fl.schema_fragment(False) == ', "ask": {"q": "", "slot": ""}'
          and fl.schema_fragment(True).endswith(', "settled": ""') and "settled:" not in fl.rule_fragment(False) and "settled:" in fl.rule_fragment(True))
    check("parse_settled validates", fl.parse_settled({"settled": "Partly"}) == "partly" and fl.parse_settled({"settled": "maybe"}) == "" and fl.parse_settled({}) == "")
    d1 = fl.take_delivery()
    check("take_delivery: once, oldest first, consumed; entry delivered; nothing left",
          d1 and d1["q_id"] == e9["id"] and d1["text"] == row9["return_text"] and fl.take_delivery() is None
          and fr.get(e9["id"])["line"]["state"] == "delivered" and e9["id"] in fl._DELIVERED)
    fl.FOLLOW_LINE = "shadow"
    fl._PENDING["x"] = {"ts": time.time(), "text": "t", "ent": {}, "cargo": {}, "judged": {}}
    check("shadow: take_delivery returns None even with pending", fl.take_delivery() is None)
    fl._PENDING.clear(); fl.FOLLOW_LINE = "live"
    # TTL expiry -> finding on the entry (the existing offer path)
    e9b = fr.note_question_ex("Why does mud let a robin's nest hold where straw alone slips?", "study", allow_self=True)
    fl._PENDING[e9b["id"]] = {"ts": time.time() - fl.LINE_TTL_S - 5, "text": "Something you wondered while reading: ... Does it hold?", "ent": e9b, "cargo": {"status": "held"}, "judged": {}}
    check("TTL: a stale pending expires into frontier.finding (existing p=0.3 offer path), state expired",
          fl.take_delivery() is None and fr.get(e9b["id"])["finding"].startswith("Something you wondered") and fr.get(e9b["id"])["line"]["state"] == "expired"
          and fr.get(e9b["id"])["finding_title"] == "what you found in your own memory")
    # cap -> oldest to fallback
    es = [fr.note_question_ex(q, "asked", allow_self=True) for q in six] + [fr.note_question_ex("What did the Portuguese actually leave behind in Goa?", "asked", allow_self=True),
                                                                          fr.note_question_ex("When did the hedgehog first vanish from the garden this year?", "asked", allow_self=True),
                                                                          fr.note_question_ex("Who taught the first robin pair nothing at all about mud?", "asked", allow_self=True)]
    assert all(es) and len({x["id"] for x in es}) == 9
    for i, x in enumerate(es):
        fl._place_pending(x["id"], f"return {i}", x, {"status": "held"}, {})
    check("cap 8: the ninth placement expires the oldest to the fallback path", fl.pending_count() == 8 and es[0]["id"] not in fl._PENDING
          and fr.get(es[0]["id"])["line"]["state"] == "expired" and fr.get(es[0]["id"])["finding"] == "return 0")
    fl._PENDING.clear()

    # ── [10] settle: yes / partly / no / unsaid ─────────────────────────────────────────────────────────────
    print("[10] settle")
    cl.SHADOW_LOG = lab_dir / "closure_shadow.jsonl"
    cl._compose_fn = lambda system, user: {"resolution": "I hold that the mixing was ordered from above, not grown by chance. The Goa order of 1510 is my ground for it, and I found it set down plainly in the records I went back to. I hold nothing firmer than that, and I would look again if a later document said otherwise."}
    cl.CLOSURE_WRITE_LIVE = False
    fl._DELIVERED[e9["id"]] = {"ts": time.time(), "text": row9["return_text"], "ent": e9, "cargo": row9["cargo"], "judged": row9["judged"]}
    out_yes = asyncio.run(fl.settle(e9["id"], "yes", "Yes, that settles it: the mixing was ordered, not grown.", "cyc1"))
    e9r = fr.get(e9["id"])
    crow = rows(cl.SHADOW_LOG, "resolution")
    check("yes: id-keyed resolve (status resolved, resolved_how line), state settled_yes",
          out_yes["resolved"] and e9r["status"] == "resolved" and e9r["resolved_how"] == "line" and e9r["line"]["state"] == "settled_yes")
    check("yes: closure arm=line shadow row with the would-be fragment + resolves edge to the frontier entry, not written live",
          len(crow) == 1 and crow[0]["arm"] == "line" and crow[0]["seed_id"] == e9["id"] and crow[0]["compose_how"] == "ok"
          and crow[0]["would_be"]["origin"] == "resolution" and crow[0]["would_be"]["edge"]["dst_kind"] == "frontier"
          and crow[0]["would_be"]["edge"]["dst_id"] == e9["id"] and crow[0]["written_live"] is False
          and "ordered from above" in crow[0]["would_be"]["content"])
    out_dup = asyncio.run(fl.settle(e9["id"], "yes", "again", "cyc2"))
    check("yes again on a resolved entry: resolve False, closure logs duplicate", out_dup["resolved"] is False and rows(cl.SHADOW_LOG, "duplicate")[-1]["arm"] == "line")
    e10 = fr.note_question_ex("Where does the bladderwrack go when the tide strips it from the rock?", "asked", slot="where", allow_self=True)
    fl._DELIVERED[e10["id"]] = {"ts": time.time(), "text": "t", "ent": e10, "cargo": {}, "judged": {}}
    out_p = asyncio.run(fl.settle(e10["id"], "partly", "Part of it: it goes down the channel, but where it lands I still do not know.", "cyc3"))
    e10r = fr.get(e10["id"])
    check("partly: slot filled on the about_key entry, question stays open, state settled_partly",
          e10r["status"] == "open" and e10r["slots"]["where"]["text"].startswith("Part of it") and e10r["slots"]["where"]["from"] == e10["id"]
          and e10r["line"]["state"] == "settled_partly" and not out_p["resolved"])
    fl._DELIVERED[e10["id"]] = {"ts": time.time(), "text": "t", "ent": e10, "cargo": {}, "judged": {}}
    asyncio.run(fl.settle(e10["id"], "no", "No, that is not it.", "cyc4"))
    check("no: logged, open, state settled_no", fr.get(e10["id"])["status"] == "open" and fr.get(e10["id"])["line"]["state"] == "settled_no")
    fl._DELIVERED[e10["id"]] = {"ts": time.time(), "text": "t", "ent": e10, "cargo": {}, "judged": {}}
    asyncio.run(fl.settle(e10["id"], "", "He said nothing about it.", "cyc5"))
    st = rows(fl.SHADOW_LOG, "settled")
    check("unsaid: logged as unsaid, nothing changes", fr.get(e10["id"])["line"]["state"] == "unsaid" and st[-1]["verdict"] == "unsaid"
          and [r["verdict"] for r in st] == ["yes", "yes", "partly", "no", "unsaid"])
    check("closure ARM_GATES names the line arm", cl.ARM_GATES.get("line", "missing") is None)
    fl.FOLLOW_LINE = "shadow"

    # ── [11] D-0596 (J-3206): a panel split is NOT a cut, for the 'cuts' key only ──────────────────────────
    print("[11] cuts judge: tiebreak yes -> no")
    from core import judge_panel as jp
    real_rd = jp.rule_detail
    seq = {"cuts": None, "supported": None, "follows": None}
    seen_user = {}
    async def m_rd(system, user, key, **kw):
        seen_user[key] = user
        return seq[key]
    jp.rule_detail = m_rd
    fl._cuts_count.update(yes=0, split_not_cut=0)
    cg = {"grounds": [{"origin": "a book", "text": "g1"}], "why": {"text": "because"}, "consequences": [{"text": "c1"}],
          "against": {"text": "too broad", "scope": ""}}
    try:
        seq["supported"] = {"verdict": True, "how": "tiebreak"}; seq["follows"] = {"verdict": True, "how": "agreed"}
        seq["cuts"] = {"verdict": True, "how": "tiebreak"}
        j1 = asyncio.run(_real_judge("claim", cg, "qid1"))
        check("cuts yes via tiebreak -> 'no', raw how kept, flagged split_not_cut; cargo_status not 'objected'",
              j1["c"] == "no" and j1["c_how"] == "tiebreak" and j1.get("c_split_not_cut") is True and fl.cargo_status(j1) != "objected")
        check("other keys unchanged: supported yes via tiebreak still 'yes'", j1["a"] == "yes" and j1["b"] == "yes")
        seq["cuts"] = {"verdict": True, "how": "agreed"}
        j2 = asyncio.run(_real_judge("claim", cg, "qid2"))
        check("cuts yes by agreement still 'yes' (objected)", j2["c"] == "yes" and not j2.get("c_split_not_cut") and fl.cargo_status(j2) == "objected")
        seq["cuts"] = {"verdict": None, "how": "split_no_tiebreak"}
        j3 = asyncio.run(_real_judge("claim", cg, "qid3"))
        check("cuts split_no_tiebreak still 'partly'", j3["c"] == "partly")
        seq["cuts"] = {"verdict": False, "how": "tiebreak"}
        j4 = asyncio.run(_real_judge("claim", cg, "qid4"))
        check("cuts tiebreak no -> 'no', not counted as split_not_cut", j4["c"] == "no" and not j4.get("c_split_not_cut"))
        seq["cuts"] = {"verdict": None, "how": "unavailable"}
        j5 = asyncio.run(_real_judge("claim", cg, "qid5"))
        check("cuts unavailable still 'unclear'", j5["c"] == "unclear")
        check("counter: 1 yes, 1 split-not-cut; status() exposes it", fl._cuts_count == {"yes": 1, "split_not_cut": 1} and fl.status().get("cuts_count") == {"yes": 1, "split_not_cut": 1})
        # J-2969 (F-3661): the 'follows' judge is shown the two consequences Du reads and that re-board, not a third
        seq["follows"] = {"verdict": True, "how": "agreed"}
        cg3 = {"grounds": [{"origin": "a book", "text": "g1"}], "why": {"text": "because"},
               "consequences": [{"text": "FIRSTCONS"}, {"text": "SECONDCONS"}, {"text": "THIRDREALCONS"}]}
        j6 = asyncio.run(_real_judge("claim", cg3, "qid6"))
        u = seen_user.get("follows", "")
        check("J-2969: three consequences -> b judged on the first two only (third never shown to the judge)",
              "FIRSTCONS" in u and "SECONDCONS" in u and "THIRDREALCONS" not in u and "[3]" not in u and j6["b"] == "yes")
        check("J-2969: the judged set equals the rendered set (CONS_USED == 2 == render's cons)",
              fl.CONS_USED == 2 and "THIRDREALCONS" not in fl.render({"q": "claim", "source": "asked"}, cg3, j6))
        cg1 = {"grounds": [{"origin": "a book", "text": "g1"}], "why": {"text": "because"}, "consequences": [{"text": "ONLYCONS"}]}
        asyncio.run(_real_judge("claim", cg1, "qid7"))
        check("J-2969: one consequence still judged as before", "ONLYCONS" in seen_user.get("follows", "") and "[1]" in seen_user["follows"])
        # render: a split-decided cut no longer shows the Against line
        ent = {"q": "claim", "source": "asked"}
        t_no = fl.render(ent, cg, j1); t_yes = fl.render(ent, cg, j2)
        check("render: no 'Against it:' for the split-decided cut, shown for the agreed one", "Against it:" not in t_no and "Against it:" in t_yes)
    finally:
        jp.rule_detail = real_rd

after = [(_hash_file(p)) for p in CANARY]
after_logs = logs_dir_fingerprint()
check("CANARY: live stores byte-identical (frontier, monologue_log, nascence.db, shadow logs, pursuits, procedures, evidence, light)", before == after)
check("CANARY: live data/logs/ untouched (names, sizes, mtimes)", before_logs == after_logs)
print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

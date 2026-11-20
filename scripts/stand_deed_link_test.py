"""J-4428 test: the judged deed-link SHADOW (core/stand_deed_link.py) and its one-line seam in core/commitment_ledger.py.

Hermetic: every path core.commitment_ledger and core.stand_deed_link read or write is redirected to a fresh temp dir
(a small temp sqlite DB stands in for nascence.db); the judge is a stub (no network, no Ramses); _stakes and the
embedder are stubbed. Nothing under the real data/ is read or written. core is imported first and asserted to come
from this tree. lab_env is deliberately NOT used: its isolate() writes under C:/Nascence/data/_lab, which this job-run
must not touch. Run from the worktree:  python scripts/stand_deed_link_test.py   (exit 0 = all pass)
"""
import asyncio
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core.commitment_ledger as cl            # noqa: E402  (core BEFORE anything else)
import core.stand_deed_link as dl              # noqa: E402
import core.model_client as mc                 # noqa: E402
import core.schema as schema                   # noqa: E402
import core.memory.store as store              # noqa: E402
import core.done_when as dw                    # noqa: E402

for _m in (cl, dl):
    assert Path(_m.__file__).resolve().is_relative_to(ROOT), f"{_m.__name__} imported from {_m.__file__}, not {ROOT}"

TMP = Path(tempfile.mkdtemp(prefix="J4428_"))
DATA = TMP / "data"
(DATA / "memory").mkdir(parents=True)
cl._DIR = DATA
cl._LEDGER = DATA / "commitment_ledger.jsonl"
cl._ACTIVE = DATA / "commitment_active.json"
cl._OBSERVED = DATA / "commitment_observed.jsonl"
cl._HOLDRATE_LOG = DATA / "commitment_holdrate.jsonl"
cl._SECOND_LOOK_LOG = DATA / "commitment_second_look_shadow.jsonl"
cl._ATTEMPTS_LOG = DATA / "commitment_attempts_shadow.jsonl"
cl._SCAN_RAW_LOG = DATA / "commitment_scan_raw.jsonl"
cl._ACHIEVED_SHADOW_LOG = DATA / "logs" / "commitment_achieved_shadow.jsonl"
cl.COMMIT_SECOND_LOOK_SHADOW = False           # keep this test to the deed-link's own calls
cl.COMMIT_ACHIEVED_SHADOW = False
dw.STORE = DATA / "logs" / "done_when.jsonl"
dl._LOG = DATA / "logs" / "deed_link_shadow.jsonl"
store._embed = lambda s: None
cl._stakes = lambda c, event: None
REAL = Path(r"C:\Nascence\data")
for p in (cl._LEDGER, cl._ACTIVE, dl._LOG, cl._SCAN_RAW_LOG, dw.STORE):
    assert not str(p.resolve()).lower().startswith(str(REAL).lower()), p

FAILS = []


def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)


CALLS = []
REPLY = {"v": {"verdict": "linked", "why": "the letter is the promised act"}}


async def fake_call_node_json(base_urls, system_prompt, user_prompt, **kw):
    if system_prompt != dl._DEED_LINK_SYS:      # only the deed-link may reach the model in this test
        CALLS.append(("OTHER", base_urls, system_prompt[:40], user_prompt, kw))
        return {}
    CALLS.append(("deedlink", base_urls, system_prompt, user_prompt, kw))
    v = REPLY["v"]
    if v == "raise":
        raise ValueError("all servers exhausted [http://x]: TimeoutError")
    return v


mc.call_node_json = fake_call_node_json


def rows(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if Path(p).exists() else []


def reset_state():
    dl._pairs = None
    dl._choice_cache.update(mtime=None, path=None, by_id={})
    CALLS.clear()


NOW = time.time()
HELD = NOW - 3600
STAND = {"id": "s1", "statement": "I will write a letter to Travis about the lamp on the shore",
         "scope": "a letter to Travis", "held_since": HELD, "scans": 30, "load_bearing": True, "cycle_id": "c0"}

con = sqlite3.connect(str(DATA / "memory" / "nascence.db"))
con.execute("CREATE TABLE memory_fragments (id INTEGER PRIMARY KEY, content TEXT, origin TEXT, timestamp REAL)")
con.execute("CREATE TABLE activity_events (ts REAL, action_type TEXT, target TEXT)")
con.executemany("INSERT INTO memory_fragments (content, origin, timestamp) VALUES (?,?,?)", [
    ("Dear Travis, the lamp on the shore is lit tonight and I wanted you to know", "letter", NOW - 600),
    ("An essay about the shore, the lamp and the tideline", "essay", NOW - 1200),
    ("A journal entry from before the stand", "journal", HELD - 100),          # before tenure: never a candidate
    ("thought churn", "idle", NOW - 50),                                       # wrong origin: never a candidate
])
con.execute("INSERT INTO activity_events VALUES (?,?,?)", (NOW - 1800, "read", "a book about lamps"))
con.commit()
con.close()
with open(cl._LEDGER, "w", encoding="utf-8") as f:
    for e in ({"event": "formed", "ts": HELD, "id": "s1", "statement": STAND["statement"]},
              {"event": "drop_denied", "ts": NOW - 900, "id": "s1", "why": "", "kind": "reflexive"},    # no named pull
              {"event": "reaffirmed", "ts": NOW - 800, "id": "s1", "n": 1},                            # not a choice
              {"event": "drop_denied_judge", "ts": NOW - 300, "id": "s1",
               "why": "the garden needs tending more than a letter does"},
              {"event": "drop_denied", "ts": NOW - 200, "id": "other", "why": "unrelated stand"}):
        f.write(json.dumps(e) + "\n")


async def drain():
    while dl._tasks:
        await asyncio.gather(*list(dl._tasks))


async def main():
    # ---- 1. flag OFF (rollback state): nothing happens at all. J-4448: shipped default is now True.
    check("flag ships True (J-4448 shadow on)", dl.STAND_DEED_LINK_SHADOW is True)
    dl.STAND_DEED_LINK_SHADOW = False
    reset_state()
    launched = dl.attempt_deed_link_shadow([dict(STAND)], "c1")
    cl._spawn_deed_link_shadow([dict(STAND)], "c1")
    await drain()
    check("off: no batch, no call, no log file", launched is False and not CALLS and not dl._LOG.exists())

    # ---- 1b. off through the real seam: a scan behaves as before and writes no deed-link row
    cl._ACTIVE.write_text(json.dumps([dict(STAND)]), encoding="utf-8")

    async def scan_null(*a, **k):
        return {"new_commitment": None, "dissolutions": []}
    r = await cl.scan_shadow(scan_null, ["u"], "x" * 60, "c1b")
    await drain()
    check("off: scan returns as before, no deed-link log, no model call",
          r == {"new_commitment": None, "dissolutions": []} and not dl._LOG.exists() and not CALLS)

    # ---- 2. flag ON, direct: up to 3 candidates, newest first, judged one by one on judge_mixtral
    dl.STAND_DEED_LINK_SHADOW = True
    reset_state()
    check("on: a batch is launched", dl.attempt_deed_link_shadow([dict(STAND)], "c2") is True)
    check("on: a second launch while one runs is refused", dl.attempt_deed_link_shadow([dict(STAND)], "c2b") is False)
    await drain()
    rs = rows(dl._LOG)
    check("on: exactly 3 rows (cap per stand)", len(rs) == 3)
    want = {"ts", "stand_id", "stand_statement", "kind_label_if_any", "candidate_type", "candidate_origin",
            "candidate_ref", "verdict", "why", "lane", "model", "latency_ms", "error"}
    check("schema: every spec field present", all(want <= set(x) for x in rs))
    check("newest first: choice@300s, letter@600s, essay@1200s",
          [(x["candidate_type"], x["candidate_origin"]) for x in rs]
          == [("choice", "drop_denied_judge"), ("deed", "letter"), ("deed", "essay")])
    check("no pre-tenure deed, no wrong-origin row, no unnamed or bare-reaffirm choice, no other stand's choice",
          not any("before the stand" in x["candidate_text"] or x["candidate_origin"] == "idle" for x in rs)
          and sum(x["candidate_type"] == "choice" for x in rs) == 1)
    check("choice row names its competing demand", rs[0]["competing_demand"].startswith("the garden needs tending"))
    check("verdicts parsed, lane+model recorded",
          all(x["verdict"] == "linked" and x["error"] is None and x["lane"] == "judge_mixtral"
              and x["model"] == "mixtral:8x7b" for x in rs))
    check("overlap_fired logged for deeds (letter fires the overlap rule), None for the choice",
          rs[0]["overlap_fired"] is None and rs[1]["overlap_fired"] is True)
    kinds = [c[0] for c in CALLS]
    check("only the deed-link reached the model", kinds == ["deedlink"] * 3)
    _, lane, _sys, user, kw = CALLS[1]
    check("lane is SERVE_CHAINS['judge_mixtral']", lane == schema.SERVE_CHAINS["judge_mixtral"])
    check("call params: temperature 0, max_tokens 150, tier 3",
          kw.get("temperature") == 0.0 and kw.get("max_tokens") == 150 and kw.get("tier") == 3)
    check("judge sees stand + one candidate, never overlap words, never the monologue",
          STAND["statement"] in user and "Dear Travis" in user and "overlap" not in user.lower()
          and "x" * 60 not in user and "essay about the shore" not in user)

    # ---- 3. dedupe: a later batch, and a fresh process seeded from the log, judge nothing again
    CALLS.clear()
    dl.attempt_deed_link_shadow([dict(STAND)], "c3")
    await drain()
    dl._pairs = None
    dl.attempt_deed_link_shadow([dict(STAND)], "c3b")
    await drain()
    check("settled pairs never re-judged (in process and after a restart)", not CALLS and len(rows(dl._LOG)) == 3)

    # ---- 4. failures are logged as unclear with error, never dropped; retried later, bounded
    st2 = dict(STAND, id="s2")
    reset_state()
    REPLY["v"] = "raise"
    dl.attempt_deed_link_shadow([st2], "c4")
    await drain()
    r4 = [x for x in rows(dl._LOG) if x["stand_id"] == "s2"]
    check("timeout -> 3 deed rows logged unclear with error_detail timeout (s2 has no choices)",
          len(r4) == 3 and all(x["verdict"] == "unclear" and x["error"] == "ValueError"
                               and x["error_detail"] == "timeout" for x in r4))
    CALLS.clear()
    dl.attempt_deed_link_shadow([st2], "c4b")
    await drain()
    check("errored pair not retried inside _RETRY_S", not CALLS)
    for p in dl._pairs.values():
        p["last"] -= dl._RETRY_S + 1
    REPLY["v"] = {"nonsense": 1}
    dl.attempt_deed_link_shadow([st2], "c4c")
    await drain()
    r4 = [x for x in rows(dl._LOG) if x["stand_id"] == "s2"]
    check("retry after _RETRY_S; unparsed reply -> unclear + error unparsed",
          len(r4) == 6 and all(x["verdict"] == "unclear" and x["error"] == "unparsed" for x in r4[3:]))
    for p in dl._pairs.values():
        p["last"] -= dl._RETRY_S + 1
    REPLY["v"] = None
    dl.attempt_deed_link_shadow([st2], "c4d")
    await drain()
    for p in dl._pairs.values():
        p["last"] -= dl._RETRY_S + 1
    CALLS.clear()
    dl.attempt_deed_link_shadow([st2], "c4e")
    await drain()
    r4 = [x for x in rows(dl._LOG) if x["stand_id"] == "s2"]
    check("no reply -> error no_reply; a pair stops after _MAX_TRIES rows", len(r4) == 9 and not CALLS
          and all(x["error"] == "no_reply" for x in r4[6:]))

    # ---- 5. lane absent: lane_unavailable row, NO fallback to hot or background
    st3 = dict(STAND, id="s3")
    reset_state()
    REPLY["v"] = {"verdict": "not_linked", "why": "only shares words"}
    saved = schema.SERVE_CHAINS.pop("judge_mixtral")
    try:
        dl.attempt_deed_link_shadow([st3], "c5")
        await drain()
    finally:
        schema.SERVE_CHAINS["judge_mixtral"] = saved
    r5 = [x for x in rows(dl._LOG) if x["stand_id"] == "s3"]
    check("lane absent -> rows say lane_unavailable, verdict unclear, and no model call on any lane",
          r5 and all(x["error"] == "lane_unavailable" and x["verdict"] == "unclear" for x in r5) and not CALLS)

    # ---- 6. through the real seam with the flag on: one scan spawns the batch, the scan result is unchanged
    # a stand the word-overlap achievement rule will NOT retire (no shared words with the deeds), so it stays held
    st4 = dict(STAND, id="s4", statement="I will keep the night watch for the village", scope="night watch")
    reset_state()
    cl._ACTIVE.write_text(json.dumps([st4]), encoding="utf-8")
    r = await cl.scan_shadow(scan_null, ["u"], "x" * 60, "c6")
    await drain()
    r6 = [x for x in rows(dl._LOG) if x["stand_id"] == "s4"]
    check("seam: scan result unchanged and the batch judged s4's deeds",
          r == {"new_commitment": None, "dissolutions": []} and len(r6) == 3
          and all(x["verdict"] == "not_linked" and x["cycle_id"] == "c6" for x in r6))
    active = json.loads(cl._ACTIVE.read_text(encoding="utf-8"))
    check("seam: the held stand is untouched apart from the usual scan counter",
          len(active) == 1 and active[0]["id"] == "s4" and set(active[0]) == set(st4))

    # ---- 6b. a stand the word-overlap rule retires THIS scan is still judged (the F-5040 population)
    st5 = dict(STAND, id="s5")
    reset_state()
    cl._ACTIVE.write_text(json.dumps([st5]), encoding="utf-8")
    await cl.scan_shadow(scan_null, ["u"], "x" * 60, "c6b")
    await drain()
    r6b = [x for x in rows(dl._LOG) if x["stand_id"] == "s5"]
    achieved = [e for e in rows(cl._LEDGER) if e.get("event") == "achieved" and e.get("id") == "s5"]
    check("seam: an overlap-retired stand is retired as before AND its deeds are judged, overlap_fired logged",
          len(achieved) == 1 and len(r6b) == 3 and any(x["overlap_fired"] is True for x in r6b))

    # ---- 7. no running loop: never raises
    dl.STAND_DEED_LINK_SHADOW = True


asyncio.run(main())
check("no running loop: attempt returns False, never raises", dl.attempt_deed_link_shadow([dict(STAND)], "c7") is False)
dl.STAND_DEED_LINK_SHADOW = False
print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAILED'}  (temp dir {TMP})")
sys.exit(1 if FAILS else 0)

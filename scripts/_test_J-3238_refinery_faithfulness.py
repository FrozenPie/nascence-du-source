"""J-3238 / D-0627: refinery faithfulness judge, phase 1 LOG-ONLY. Offline: temp DB + temp logs, the judge hub call is stubbed
(no Ramses, no network), the writer model call is stubbed. Never opens data/memory/nascence.db, writes nothing under data/.

Covers: verdict stored beside the insight (fragment_id) for mint and evolve; a FAILED verdict still writes the insight and
cools the members (log-only, nothing withheld); a judge error/timeout writes verdict None, does not block the write and stops
further judge calls that run; the lexical-reject path never calls the judge; the kill-switch restores the old behaviour (no
call, no log row); the DB content is identical judge-on vs judge-off; the judge sees only the shown members (cap + per-member
cut) and uses judge_panel's JUDGE_1 hub; reader (faithfulness_status + the report script) and the 60-row review point.
Run from the worktree: python scripts/_test_J-3238_refinery_faithfulness.py
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["NASCENCE_TRAINING_LOG"] = "0"
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                              # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import numpy as np                                       # noqa: E402
import core.memory.store as store                        # noqa: E402
from core import refinery as ref                         # noqa: E402
from core import judge_panel as jp                       # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3238_refinery_"))
ref._SHADOW_LOG = _TMP / "refinery_shadow.jsonl"
ref._FAITH_LOG = _TMP / "refinery_faithfulness.jsonl"
store._POOL_DELTA_SHADOW_LOG = _TMP / "pool_delta_shadow.jsonl"
_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def vec(i):
    v = np.zeros(384, dtype=np.float32)
    v[i] = 1.0
    return v


store._embed = lambda text: vec(0)                       # an insight embeds near cluster 0 (so a 2nd run evolves it)

TEXT_A = "I keep noticing a tension between curiosity and caution when I read about difficult decisions"
TEXT_B = "My attention drifts toward rivers and bridges whenever the reading turns to crossing something"


def fresh_db(name, with_existing_insight=False):
    store.DB_PATH = _TMP / name
    store.init_db()
    with sqlite3.connect(store.DB_PATH) as c:
        t = time.time() - 1000
        for k in range(5):      # cluster 0: direction 0
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, embedding, origin) "
                      "VALUES (?,?,?,?,?,?,?,?)", (f"a{k}", TEXT_A + f" number {k}", "archive", 0.85, t + k, "", store._vec_to_blob(vec(0)),
                                                   "subconscious_synthesis"))
        for k in range(10):     # cluster 1: direction 1 (10 members: more than the 8 shown)
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, embedding, origin) "
                      "VALUES (?,?,?,?,?,?,?,?)", (f"b{k}", (TEXT_B + " " + "x" * 400) + f" item {k}", "archive", 0.85, t + 100 + k, "",
                                                   store._vec_to_blob(vec(1)), "subconscious_synthesis"))
        c.execute("UPDATE memory_fragments SET kind='self'")
        if with_existing_insight:
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, importance, timestamp, keywords, embedding, "
                      "origin, derived_from, abstraction_level) VALUES ('ins0','I notice tension between curiosity and caution','archive',"
                      "0.85,0.9,?,'x',?, 'standing_insight','[]',2)", (t, store._vec_to_blob(vec(0))))
        c.commit()


def snapshot():
    with sqlite3.connect(store.DB_PATH) as c:
        return sorted(c.execute("SELECT origin, content, cold FROM memory_fragments").fetchall())


calls = []


def make_ask(answers):
    """answers: list of (verdict, why, err) consumed in order; records every call."""
    it = iter(answers)

    async def _ask(session, url, system, user, key, timeout=0, num_predict=0):
        calls.append({"url": url, "system": system, "user": user, "key": key, "timeout": timeout, "num_predict": num_predict})
        v, why, err = next(it)
        return v, why, err, 0.5
    return _ask


async def writer(base_urls, system, user, max_tokens=0, temperature=0):
    # the stubbed WRITER model: reuses the theme words so the lexical gate passes, except when the user prompt says "ZZZ"
    if "rivers" in user:
        return {"insight": "My attention drifts toward rivers and bridges whenever the reading turns to crossing something."}
    return {"insight": "I keep noticing a tension between curiosity and caution when I read about difficult decisions."}


_n = [0]


def run(answers, judge_on=True, db=None, existing=False, writer_fn=writer):
    _n[0] += 1
    db = f"t{_n[0]}.db"
    calls.clear()
    for f in (ref._SHADOW_LOG, ref._FAITH_LOG):
        if f.exists():
            f.unlink()
    fresh_db(db, existing)
    jp._ask = make_ask(answers)
    ref.FAITHFULNESS_JUDGE_ON = judge_on
    st = asyncio.run(ref.refine(writer_fn, ["http://writer.invalid:1"]))
    frows = [json.loads(l) for l in open(ref._FAITH_LOG, encoding="utf-8")] if ref._FAITH_LOG.exists() else []
    srows = [json.loads(l) for l in open(ref._SHADOW_LOG, encoding="utf-8")] if ref._SHADOW_LOG.exists() else []
    return st, frows, srows


# ---- 1. mint, judge says yes (cluster 1 seeds first: newest; cluster 0 second) -------------------------------------------
st, frows, srows = run([(True, "supported by the notes", None), (True, "ok", None)])
check(st["minted"] == 2 and st["rejected"] == 0, f"two insights minted: {st}")
check(len(calls) == 2 and len(frows) == 2, "one judge call and one faithfulness row per written insight")
check(all(c["key"] == "supported" and c["url"] == jp.JUDGE_1 for c in calls), "judge = judge_panel JUDGE_1 hub, key 'supported'")
check(all(r["mode"] == "log_only" and r["supported"] is True and r["live"] is True for r in frows), "rows: log_only, supported True, live")
with sqlite3.connect(store.DB_PATH) as c:
    ids = {r[0] for r in c.execute("SELECT fragment_id FROM memory_fragments WHERE origin='standing_insight'")}
check({r["fragment_id"] for r in frows} == ids and len(ids) == 2, "each verdict row is keyed by the fragment_id of the insight it grades")
check(all(r.get("faithful") is True for r in srows if r["accepted"]), "shadow record carries faithful=True")
# the judge saw only the shown members
big = [c for c in calls if "rivers" in c["user"] and "NOTES" in c["user"]][0]
notes = [l for l in big["user"].splitlines() if l.startswith("  ") and l.strip()[:2] in tuple(f"{i}." for i in range(1, 12))]
check(len(notes) == ref.MAX_MEMBERS_IN_PROMPT == 8, f"10-member cluster: judge shown exactly {ref.MAX_MEMBERS_IN_PROMPT} notes (got {len(notes)})")
check(all(len(l.strip()) <= ref.FAITH_MEMBER_CHARS + 4 for l in notes), "each note cut to FAITH_MEMBER_CHARS")
check(big["num_predict"] == ref.FAITH_NUM_PREDICT and big["timeout"] == ref.FAITH_TIMEOUT, "bounded output and timeout")
b_row = [r for r in frows if r["members_total"] == 10][0]
check(b_row["members_judged"] == 8 and b_row["member_chars_cap"] == 220, "the cap is recorded on the row (8 of 10 members, 220 chars)")
snap_on = snapshot()

# ---- 2. judge says NO: insight still written, members still cooled (log-only) ------------------------------------------------
st, frows, srows = run([(False, "invents a theme", None), (False, "restates one note", None)])
check(st["minted"] == 2 and st["cooled"] == 15, f"FAILED verdict still mints and cools (nothing withheld): {st}")
check(all(r["supported"] is False for r in frows), "verdicts stored as False")
check(snapshot() == snap_on, "DB content identical to the judge-said-yes run (verdict changes nothing live)")

# ---- 3. judge down: verdict None, write unaffected, no more judge calls this run -----------------------------------------------
st, frows, srows = run([(None, None, "timeout"), (True, "never asked", None)])
check(len(calls) == 1 and st["minted"] == 2, f"timeout -> one call only, both insights still written (calls={len(calls)}, {st})")
check(len(frows) == 1 and frows[0]["supported"] is None and frows[0]["err"] == "timeout", "row records verdict None + err timeout")
check(snapshot() == snap_on, "DB content identical when the judge is down")
st, frows, srows = run([(None, None, "parse"), (True, "ok", None)])
check(len(calls) == 2, "a parse failure does NOT stop the judge for the rest of the run (only timeout/http do)")

# ---- 4. kill-switch off == old behaviour -----------------------------------------------------------------------------------------
st, frows, srows = run([], judge_on=False)
check(len(calls) == 0 and frows == [] and st["minted"] == 2 and all(r.get("faithful") is None for r in srows),
      "FAITHFULNESS_JUDGE_ON=False: no call, no faithfulness row")
check(snapshot() == snap_on, "DB content identical judge-off vs judge-on")

# ---- 5. lexical reject never reaches the judge ----------------------------------------------------------------------------------
async def unrelated(base_urls, system, user, max_tokens=0, temperature=0):
    return {"insight": "Quantum chromodynamics governs hadronic confinement thoroughly."}
st, frows, srows = run([(True, "x", None)] * 3, writer_fn=unrelated)
check(st["rejected"] == 2 and len(calls) == 0 and frows == [], f"lexically rejected insights are not judged: {st}")

# ---- 6. evolving: prior insight offered to the judge, row says so ---------------------------------------------------------------
st, frows, srows = run([(True, "ok", None), (True, "ok", None)], existing=True)
ev = [r for r in frows if r["evolving"]]
check(len(ev) == 1 and ev[0]["prior_included"] is True and ev[0]["fragment_id"] == "ins0" and ev[0]["prior_insight"] == "ins0",
      "evolved insight: row keyed to the SAME fragment_id, prior_included True")
check(any("EARLIER STANDING INSIGHT" in c["user"] for c in calls) and sum("EARLIER STANDING INSIGHT" in c["user"] for c in calls) == 1,
      "only the evolving call carries the earlier insight")

# ---- 7. the writer's own prompt is unchanged and the judge prompt is not shown to the writer ------------------------------------
check(ref._SYSTEM.startswith("You are the consolidating memory of") and "Output ONLY JSON: {\"insight\"" in ref._SYSTEM, "writer system prompt untouched")
check("supported" in ref._FAITH_SYSTEM and "Output ONLY JSON" in ref._FAITH_SYSTEM, "judge prompt asks for the 'supported' boolean")

# ---- 8. reader + review point ---------------------------------------------------------------------------------------------------
log = _TMP / "faith_60.jsonl"
with open(log, "w", encoding="utf-8") as f:
    for i in range(60):
        f.write(json.dumps({"fragment_id": f"f{i}", "supported": i % 4 != 0, "evolving": i % 2 == 0, "members_total": 5 + i, "insight": f"ins {i}", "why": "w", "fidelity": 0.6}) + "\n")
    f.write(json.dumps({"fragment_id": "e", "supported": None, "err": "timeout"}) + "\n")
s = ref.faithfulness_status(log)
check(s["rows"] == 61 and s["judged"] == 60 and s["errors"] == 1 and s["passed"] == 45 and s["pass_rate"] == 0.75 and s["phase1_complete"] and not s["no_information"],
      f"faithfulness_status: {s}")
log2 = _TMP / "faith_allyes.jsonl"
with open(log2, "w", encoding="utf-8") as f:
    for i in range(60):
        f.write(json.dumps({"supported": True}) + "\n")
check(ref.faithfulness_status(log2)["no_information"] is True, "100% pass over 60 -> defeater flag (judge carries no information)")
check(ref.faithfulness_status(_TMP / "missing.jsonl")["rows"] == 0, "missing log -> empty status, no raise")
import importlib.util                                      # noqa: E402
spec = importlib.util.spec_from_file_location("rfr", TREE / "scripts" / "refinery_faithfulness_report.py")
rfr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rfr)
buf = io.StringIO()
sys.argv = ["x", "--log", str(log), "--fails", "2"]
with contextlib.redirect_stdout(buf):
    rc = rfr.main()
out = buf.getvalue()
check(rc == 0 and "REVIEW POINT REACHED" in out and "failed insights (15)" in out and "by cluster size" in out, "report script prints the review point, fails and splits")
ref._SHADOW_LOG.write_text(json.dumps({"accepted": True, "fidelity": 0.7}) + "\n", encoding="utf-8")
check("faithfulness" in ref.status(), "refinery.status() exposes the faithfulness block")

# ---- 9. nothing leaked into the live data dir -----------------------------------------------------------------------------------
live_log = TREE / "data" / "refinery_faithfulness.jsonl"
check(not live_log.exists(), "no refinery_faithfulness.jsonl written under the repo's data/")

print("\nFAILS:", _fails or "none")
sys.exit(1 if _fails else 0)

"""
Hermetic test for J-2972 (F-3662, P-0102): Follow Line stop 1 does not hand the WHY prompt, the judges and the return
two copies of one passage.  Root cause found first: the store holds one reading chunk under several fragment ids (live,
read-only count 2026-11-06: 58,071 'reading' rows, 42,800 distinct texts), so evidence_recall._candidates short-lists the
same passage twice under two ids -- it is NOT the same fragment id twice.

No model, no embedder, no live data: temp sqlite store, stubbed _embed and judge panel, every log path in a temp dir.
Run: python scripts/_test_J-2972_dedupe_grounds.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, sqlite3, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything else: the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import numpy as np
from core import evidence_recall as ev
from core import follow_line as fl
from core.memory import store as mstore

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="J-2972_"))

# -- [1] pure dedupe_grounds ----------------------------------------------------------------------------------------
print("[1] dedupe_grounds")
A = "[From 'The Will to Believe'] ieve that the possibility exists.\"\n\n\nThese, then, are my last words to you: Be not afraid of life."
g = [{"fragment_id": "f1", "strength": "bears", "text": A},
     {"fragment_id": "f2", "strength": "bears", "text": A.replace(" ", "  ")},          # same text, whitespace differs, other id
     {"fragment_id": "f3", "strength": "may_bear", "text": "[From 'Candle'] That is why I have chosen this other form."},
     {"fragment_id": "f3", "strength": "may_bear", "text": "something else but the same id"},   # same id
     {"fragment_id": "f5", "strength": "bears", "text": " ".join(A.split())[:120] + " but then a different ending"},  # same first 120 chars
     {"fragment_id": "f6", "strength": "bears", "text": "[From 'Other'] a distinct passage"}]
kept, dropped = fl.dedupe_grounds(g)
check("kept the first of each, in order; dropped 3", [x["fragment_id"] for x in kept] == ["f1", "f3", "f6"] and dropped == 3)
check("strongest (first) copy survives, not the later one", kept[0]["strength"] == "bears" and kept[0]["text"] == A)
check("no-op on distinct grounds / empty / None", fl.dedupe_grounds([kept[0], kept[2]]) == ([kept[0], kept[2]], 0)
      and fl.dedupe_grounds([]) == ([], 0) and fl.dedupe_grounds(None) == ([], 0))
check("two books never collide on the prefix", fl.dedupe_grounds([{"fragment_id": "a", "text": "[From 'X'] same body"},
                                                                  {"fragment_id": "b", "text": "[From 'Y'] same body"}])[1] == 0)

# -- [2] evidence_recall._candidates on a temp store ------------------------------------------------------------------
print("[2] _candidates")
db = tmp / "nascence.db"
con = sqlite3.connect(db)
con.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT, timestamp REAL, embedding BLOB)")
def vec(a, b):
    v = np.array([a, b, 0.0, 0.0], dtype=np.float32)
    return (v / np.linalg.norm(v)).tobytes()
P1 = "[From 'The Will to Believe'] ieve that the possibility exists. These are my last words."
P2 = "[From 'Candle'] That is why I have chosen this other form of apparatus."
P3 = "[From 'Schopenhauer'] a distinct third passage about the will."
rows_ = [("id_new_copy", P1, "reading", 2.0, vec(1.0, 0.00)),     # the two copies of P1 sit at the same similarity
         ("id_old_copy", P1, "reading", 1.0, vec(1.0, 0.00)),
         ("id_p2", P2, "reading", 1.0, vec(1.0, 0.30)),
         ("id_p3", P3, "reading", 1.0, vec(1.0, 0.60))]
con.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", rows_)
con.commit()
con.close()
Q = "a question long enough to ask"
real_db, real_embed = ev._DB, mstore._embed
ev._DB = db
mstore._embed = lambda t: np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
try:
    plain = ev._candidates(Q)
    check("default (dedupe off): no 'deduped' stat, and J-2795's always-on content dedupe leaves one copy of P1", [c["content"] for c in plain].count(P1) == 1 and len(plain) == 3)  # J-2795 (merged after this test was written) already drops identical-content copies on EVERY call
    st: dict = {}
    dd = ev._candidates(Q, dedupe=True, stats=st)
    check("dedupe on: one copy of P1 plus the two other passages", sorted(c["content"] for c in dd) == sorted([P1, P2, P3]))
    check("dedupe on: count of dropped copies reported", st.get("deduped") == 1)
    k2 = ev._candidates(Q, k=3, dedupe=True, stats={})
    check("the freed slot goes to a distinct passage (k=3: three distinct with dedupe, and also without, since J-2795)",
          len({c["content"] for c in k2}) == 3 and len({c["content"] for c in ev._candidates(Q, k=3)}) == 3)

    # -- [3] gather(dedupe=...) with a stubbed judge panel and temp logs ------------------------------------------
    print("[3] gather")
    from core import judge_panel, memory_edges, memory_service
    real_rd, real_log, real_col, real_su = judge_panel.rule_detail, ev._LOG, memory_edges.log_co_recall, memory_service.stash_usage
    async def rd(*a, **k):
        return {"verdict": True, "how": "agreed", "v1": True, "v2": True}
    judge_panel.rule_detail = rd
    ev._LOG = tmp / "evidence_log.jsonl"
    memory_edges.log_co_recall = lambda *a, **k: None
    memory_service.stash_usage = lambda *a, **k: None
    try:
        r0 = asyncio.run(ev.gather(Q, source="t"))
        check("default gather: result shape unchanged (no 'deduped' key); copies already dropped by J-2795", set(r0) == {"episodes", "outcome"}
              and [e["content"] for e in r0["episodes"]].count(P1) == 1)
        r1 = asyncio.run(ev.gather(Q, source="t", dedupe=True))
        check("dedupe gather: distinct passages only, 'deduped' == 1, outcome found",
              len({e["content"] for e in r1["episodes"]}) == len(r1["episodes"]) == 3 and r1["deduped"] == 1 and r1["outcome"] == "found")

        # -- [4] follow_line._stop_grounds end to end over the real gather -----------------------------------------
        print("[4] _stop_grounds")
        sg = asyncio.run(fl._stop_grounds(Q, None))
        check("stop 1 returns 3 distinct grounds and grounds_deduped == 1", len(sg["grounds"]) == 3 and sg["grounds_deduped"] == 1
              and len({x["text"][:120] for x in sg["grounds"]}) == 3 and sg["grounds_outcome"] == "found")
        fl.DEDUPE_GROUNDS = False
        sg0 = asyncio.run(fl._stop_grounds(Q, None))
        check("DEDUPE_GROUNDS False: no count key (copies already dropped upstream by J-2795)",
              set(sg0) == {"grounds", "grounds_outcome"} and [x["text"] for x in sg0["grounds"]].count(P1) == 1)
        fl.DEDUPE_GROUNDS = True

        # safety net: a gather that ignores dedupe (another source of dups) is still cleaned, and counted
        async def dup_gather(q, train_id=None, source="x", dedupe=False):
            e = {"fragment_id": "x1", "origin": "reading", "timestamp": 0.0, "strength": "bears", "content": P1}
            return {"episodes": [e, dict(e, fragment_id="x2", strength="may_bear"), dict(e, fragment_id="x3", content=P2)],
                    "outcome": "found", "deduped": 2}
        real_g = ev.gather
        ev.gather = dup_gather
        try:
            sg2 = asyncio.run(fl._stop_grounds(Q, None))
        finally:
            ev.gather = real_g
        check("safety net drops the stray copy and the count adds upstream + net (2 + 1)",
              [x["fragment_id"] for x in sg2["grounds"]] == ["x1", "x3"] and sg2["grounds_deduped"] == 3)
    finally:
        judge_panel.rule_detail, ev._LOG, memory_edges.log_co_recall, memory_service.stash_usage = real_rd, real_log, real_col, real_su
finally:
    ev._DB, mstore._embed = real_db, real_embed

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

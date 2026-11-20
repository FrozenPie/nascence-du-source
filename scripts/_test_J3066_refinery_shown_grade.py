"""J-3066 / F-3773: refinery fidelity gate, phase 0 SHADOW: a shown-members, whole-word grade logged next to the old gate, plus
refinery_history.jsonl. Offline: temp DB + temp logs, the writer model is stubbed, the faithfulness judge is switched off (no
Ramses, no network). Never opens data/memory/nascence.db, writes nothing under data/.

Covers: whole-word vs substring; the pool is only the lines the prompt showed (8 members, each cut to 220), so a word that lives
only in an unshown member counts for the old grade and not the new one; the grade's `shown` list equals the member lines in the
prompt actually sent; the old gate still decides accepted/rejected and the DB is identical whatever the new grade says; shadow
record carries fidelity_shown / would_accept_shown / members_shown; evolve appends the OLD text to the history log after the
commit, mint and shadow-mode write none, a broken history path never blocks the write; readers (shown_grade_status,
insight_history, status); memory_levels.source_fidelity unchanged; the replay script's pure core.
Run from the worktree: python scripts/_test_J3066_refinery_shown_grade.py
"""
import asyncio
import importlib.util
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
from core import memory_levels as ml                     # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="j3066_refinery_"))
ref._SHADOW_LOG = _TMP / "refinery_shadow.jsonl"
ref._FAITH_LOG = _TMP / "refinery_faithfulness.jsonl"
ref._HISTORY_LOG = _TMP / "refinery_history.jsonl"
ref.FAITHFULNESS_JUDGE_ON = False
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


store._embed = lambda text: vec(0)

# ---- 1. the grade itself ---------------------------------------------------------------------------------------------------
shown = ["I keep returning to rivers and bridges", "attention drifts toward crossing water"]
check(ref._fidelity_vs_shown("rivers bridges crossing", shown) == 1.0, "all salient words in the shown lines -> 1.0")
check(ref._fidelity_vs_shown("rivers bridges zeppelin dirigible", shown) == 0.5, "words absent from the shown lines lower the grade")
# whole word, not substring: 'planet' sits inside 'planetary' (the old grade passes it, the new one must not)
check(ml.source_fidelity("planet", ["planetary motion"]) == 1.0, "baseline: the old substring grade passes 'planet' on 'planetary'")
check(ref._fidelity_vs_shown("planet", ["planetary motion"]) == 0.0, "whole-word: 'planet' does not pass on 'planetary'")
check(ref._fidelity_vs_shown("a an the", shown) == 1.0, "no salient words -> 1.0 (same as source_fidelity)")
check(ref._fidelity_vs_shown("anything", None) == 0.0 and ref._fidelity_vs_shown(None, shown) == 1.0, "None inputs do not raise")
check(ref.SHOWN_MEMBER_CHARS == ref.FAITH_MEMBER_CHARS == 220 and ref.SHOWN_PRIOR_CHARS == ref.FAITH_PRIOR_CHARS == 400,
      "cut constants pinned to the faithfulness judge's (== what the writer saw)")
long_line = "alpha " * 3 + "x" * 300 + " zeppelin"      # 'zeppelin' sits beyond char 220
check(ref._fidelity_vs_shown("zeppelin", [long_line]) == 0.0, "a word beyond the 220-char cut is not 'shown'")
check(ref._fidelity_vs_shown("zeppelin", ["a"], prior_text="the standing zeppelin insight") == 1.0, "prior insight text is in the pool when given")
check(ref._size_bucket(4) == "4-8" and ref._size_bucket(8) == "4-8" and ref._size_bucket(9) == "9-20" and ref._size_bucket(21) == "21-100"
      and ref._size_bucket(100) == "21-100" and ref._size_bucket(101) == "101+", "size buckets follow F-3773's split")

# ---- 2. fixtures ------------------------------------------------------------------------------------------------------------
THEME = "My attention drifts toward rivers and bridges whenever the reading turns to crossing something"


def fresh_db(name, with_existing_insight=False):
    store.DB_PATH = _TMP / name
    store.init_db()
    with sqlite3.connect(store.DB_PATH) as c:
        t = time.time() - 1000
        for k in range(10):     # ONE cluster of 10 members (> the 8 shown), direction 0
            # the 2 OLDEST members (k=0,1) carry the words only they hold; since J-3821 the prompt shows the newest 8, so they are NOT shown
            extra = " zeppelin dirigible airship" if k < 2 else ""   # J-4052: J-3821 (D-0725) now shows the NEWEST 8, so the unshown pair is the 2 OLDEST
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, embedding, origin) "
                      "VALUES (?,?,?,?,?,?,?,?)", (f"b{k}", f"{THEME}{extra} item {k} " + "x" * 400, "archive", 0.85, t + k, "",
                                                   store._vec_to_blob(vec(0)), "subconscious_synthesis"))
        c.execute("UPDATE memory_fragments SET kind='self'")
        if with_existing_insight:
            c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, importance, timestamp, keywords, embedding, "
                      "origin, derived_from, abstraction_level) VALUES ('ins0','OLD standing insight about rivers','archive',"
                      "0.85,0.9,?,'x',?, 'standing_insight','[]',2)", (t, store._vec_to_blob(vec(0))))
        c.commit()


def snapshot():
    with sqlite3.connect(store.DB_PATH) as c:
        return sorted(c.execute("SELECT origin, content, cold FROM memory_fragments").fetchall())


prompts = []
spied = []
_orig_fvs = ref._fidelity_vs_shown


def spy(insight, shown, prior_text=None):
    spied.append((list(shown), prior_text))
    return _orig_fvs(insight, shown, prior_text)


INSIGHT_SPLIT = "Zeppelin dirigible airship rivers bridges crossing."   # 3 words only in the unshown members, 3 in all


async def writer(base_urls, system, user, max_tokens=0, temperature=0):
    prompts.append(user)
    return {"insight": INSIGHT_SPLIT}


_n = [0]


def run(existing=False, live=True, new_grade=None, history_path=None, writer_fn=writer):
    _n[0] += 1
    prompts.clear()
    spied.clear()
    for f in (ref._SHADOW_LOG, ref._HISTORY_LOG):
        if f.exists():
            f.unlink()
    fresh_db(f"t{_n[0]}.db", existing)
    ref.REFINERY_LIVE = live
    ref._fidelity_vs_shown = new_grade or spy
    if history_path is not None:
        ref._HISTORY_LOG = history_path
    try:
        st = asyncio.run(ref.refine(writer_fn, ["http://writer.invalid:1"]))
    finally:
        ref._fidelity_vs_shown = _orig_fvs
    srows = [json.loads(l) for l in open(ref._SHADOW_LOG, encoding="utf-8")] if ref._SHADOW_LOG.exists() else []
    hrows = [json.loads(l) for l in open(ref._HISTORY_LOG, encoding="utf-8")] if ref._HISTORY_LOG.is_file() else []
    return st, srows, hrows


# ---- 3. mint: new fields in the shadow record, old gate decides, grade sees only what the prompt showed ---------------------
st, srows, hrows = run()
check(st["minted"] == 1 and st["rejected"] == 0 and st["cooled"] == 10, f"old gate accepts, mints and cools as before: {st}")
r = srows[0]
check(r["accepted"] is True and r["members"] == 10 and r["members_shown"] == 8, f"record: accepted by the old gate, 10 members, 8 shown: {r}")
check(r["fidelity"] == 1.0, f"old grade (all members) = 1.0: {r['fidelity']}")
check(r["fidelity_shown"] == 0.5 and r["would_accept_shown"] is False, f"new grade (shown only) = 0.5 -> would_accept_shown False: {r['fidelity_shown']}")
check(r["fidelity_shown_prior"] is None, "no prior insight -> fidelity_shown_prior None")
check(len(prompts) == 1 and len(spied) == 1, "one writer call, one shown-grade call")
plines = [l[4:] for l in prompts[0].splitlines() if l.startswith("  - ")]
check(len(plines) == 8 and plines == [ref._shown_line(t) for t in spied[0][0]],
      "the grade's `shown` list == the member lines in the prompt actually sent (8, each cut as sent)")
check(not any("zeppelin" in l for l in plines), "(fixture) the two members holding 'zeppelin' are not among the shown lines")
snap_a = snapshot()
check(hrows == [], "a mint writes no history row")

# decisions are identical whatever the new grade says (it decides nothing)
st2, srows2, _ = run(new_grade=lambda *a, **k: 0.0)
check(snapshot() == snap_a and st2["minted"] == 1 and srows2[0]["accepted"] is True and srows2[0]["would_accept_shown"] is False,
      "new grade forced to 0.0: DB and accept/reject identical (phase 0 decides nothing)")
st3, srows3, _ = run(new_grade=lambda *a, **k: None)
check(snapshot() == snap_a and srows3[0]["fidelity_shown"] is None and srows3[0]["would_accept_shown"] is False,
      "new grade failing (None): record still written, DB identical, would_accept_shown False")

# lexical reject still rejects on the OLD gate alone
async def unrelated(base_urls, system, user, max_tokens=0, temperature=0):
    return {"insight": "Quantum chromodynamics governs hadronic confinement thoroughly."}
st4, srows4, _ = run(writer_fn=unrelated)
check(st4["rejected"] == 1 and st4["minted"] == 0 and srows4[0]["accepted"] is False and "fidelity_shown" in srows4[0],
      "old gate still rejects an unrelated insight; the record still carries the new field")

# shadow mode (REFINERY_LIVE False): record yes, DB writes no, history no
st5, srows5, hrows5 = run(live=False, existing=True)
check(st5["evolved"] == 1 and hrows5 == [] and len(srows5) == 1, "REFINERY_LIVE False: logs the record, writes no history")
ref.REFINERY_LIVE = True

# ---- 4. evolve: history keeps the previous text -----------------------------------------------------------------------------
st6, srows6, hrows6 = run(existing=True)
check(st6["evolved"] == 1 and st6["minted"] == 0, f"evolve path: {st6}")
check(len(hrows6) == 1 and hrows6[0]["fragment_id"] == "ins0" and hrows6[0]["old_content"] == "OLD standing insight about rivers"
      and hrows6[0]["new_content"] == INSIGHT_SPLIT and hrows6[0]["members_added"] == 10, f"history row holds the OLD text: {hrows6}")
with sqlite3.connect(store.DB_PATH) as c:
    now = c.execute("SELECT content FROM memory_fragments WHERE fragment_id='ins0'").fetchone()[0]
check(now == INSIGHT_SPLIT, "the live insight now holds the new text (history is the only copy of the old)")
check(srows6[0]["evolving"] is True and srows6[0]["fidelity_shown_prior"] is not None, "evolving record carries fidelity_shown_prior")
check(ref.insight_history("ins0", ref._HISTORY_LOG)[0]["old_content"] == "OLD standing insight about rivers"
      and ref.insight_history("nope", ref._HISTORY_LOG) == [] and ref.insight_history("ins0", _TMP / "missing.jsonl") == [],
      "insight_history reader: finds by id, empty for unknown id / missing log")
snap_evolve = snapshot()

# an unwritable history path never blocks the write
bad = _TMP / "a_directory"
bad.mkdir()
st7, srows7, _ = run(existing=True, history_path=bad)
check(st7["evolved"] == 1 and snapshot() == snap_evolve, "unwritable history log: evolve still lands, DB identical")
ref._HISTORY_LOG = _TMP / "refinery_history.jsonl"

# ---- 5. readers ------------------------------------------------------------------------------------------------------------
log = _TMP / "shadow25.jsonl"
with open(log, "w", encoding="utf-8") as f:
    for i in range(25):
        n = [5, 12, 30, 150, 6][i % 5]
        f.write(json.dumps({"members": n, "accepted": i % 6 != 0, "fidelity": 0.9, "fidelity_shown": 0.8 if i % 3 else 0.4,
                            "would_accept_shown": bool(i % 3)}) + "\n")
    f.write(json.dumps({"members": 5, "accepted": True, "fidelity": 0.9}) + "\n")      # an old-format row: ignored
s = ref.shown_grade_status(log)
check(s["records"] == 25 and s["review_ready"] is True and s["review_n"] == 20, f"shown_grade_status counts only rows with the field: {s['records']}")
check(s["would_reject"] == sum(b["would_reject"] for b in s["by_cluster_size"].values())
      and s["accepted"] == sum(b["accepted"] for b in s["by_cluster_size"].values())
      and set(s["by_cluster_size"]) == {"4-8", "9-20", "21-100", "101+"}, f"split by cluster size: {s['by_cluster_size']}")
check(ref.shown_grade_status(_TMP / "missing.jsonl") == {"records": 0, "review_ready": False}, "missing log -> empty status, no raise")
with open(_TMP / "shadow5.jsonl", "w", encoding="utf-8") as f:
    for i in range(5):
        f.write(json.dumps({"members": 5, "accepted": True, "fidelity_shown": 0.9, "would_accept_shown": True}) + "\n")
check(ref.shown_grade_status(_TMP / "shadow5.jsonl")["review_ready"] is False, "under 20 records -> not review_ready")
ref._SHADOW_LOG = log
check(ref.status().get("shown_grade", {}).get("records") == 25, "status() exposes shown_grade")

# ---- 6. the old grade is untouched ------------------------------------------------------------------------------------------
check(ml.source_fidelity("rivers bridges crossing", ["rivers and bridges, crossing"]) == 1.0
      and ml.source_fidelity("planet", ["planetary"]) == 1.0 and ml.source_fidelity("", ["x"]) == 1.0,
      "memory_levels.source_fidelity behaves as before (substring, shared with gisting / journal / recall)")

# ---- 7. the replay script's pure core ---------------------------------------------------------------------------------------
spec = importlib.util.spec_from_file_location("rpl", TREE / "scripts" / "replay_J3066_refinery_shown_grade.py")
rpl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rpl)
ids = [f"m{i}" for i in range(10)]
texts = {i: (f"{THEME}" + (" zeppelin dirigible airship" if k < 2 else ""), 100 - k) for k, i in enumerate(ids)}    # newest-first order, like the log
rows = [{"ts": 1, "members": 10, "member_ids": ids, "insight": INSIGHT_SPLIT, "accepted": True, "fidelity": 1.0, "evolving": False},
        {"ts": 2, "members": 70, "member_ids": ids, "insight": INSIGHT_SPLIT, "accepted": True, "fidelity": 1.0},
        {"ts": 3, "members": 10, "member_ids": ids + ["gone"], "insight": INSIGHT_SPLIT, "accepted": True, "fidelity": 1.0}]
res, big, missing = rpl.replay(rows, lambda want: {i: texts[i] for i in want if i in texts}, ref, ml)
check(len(res) == 1 and big == 1 and missing == 1, f"replay: complete rows replayed, >40-member and missing-text rows skipped and counted: {len(res)},{big},{missing}")
check(res[0]["old_accept"] is True and res[0]["new_accept"] is False and res[0]["bucket"] == "9-20" and res[0]["ts_order_newest_first"] is True,
      f"replay row: old accepts, shown grade rejects, bucket 9-20: {res[0]}")
check(rpl.summarise(res) == {"9-20": {"rows": 1, "old_accept": 1, "new_accept": 0, "old_accept_new_reject": 1}}, "replay summary by bucket")

print()
if _fails:
    print(f"{len(_fails)} FAILED")
    sys.exit(1)
print("ALL PASS")

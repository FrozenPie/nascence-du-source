"""Hermetic test for J-3055 (P-0060, F-3764): T6 theme pass no longer re-paraphrases unchanged themes.

Run from the worktree root:  python scripts/_test_J-3055_t6_theme_gate.py
- imports core FIRST and asserts it came from this tree; temp memory DB, temp state/log files;
  the model call (scn.call_node_json) is stubbed, no hub is contacted.
Covers: (1) no new epoch in any cluster -> zero model calls, pass stamped done; (2) one new epoch in
one theme -> exactly one call, prompt shows ONLY the new epoch; (3) >6 new epochs -> six, newest first;
(4) two clusters matching one theme -> ONE call over the union, membership stored whole;
(5) a failed call does not stamp the pass; (6) rename flag OFF ignores theme_name, ON applies it,
refuses a taken name, and logs; (7) T6_pass log rows; (8) _synthesise_theme still returns a bool.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"

import numpy as np  # noqa: E402
import core.memory.store as store  # noqa: E402
_tmp = Path(tempfile.mkdtemp(prefix="j3055_"))
store.DB_PATH = _tmp / "test.db"
store._embed = lambda text: None          # no embedding model: stance/name embeddings stay NULL

import nodes.subconscious_node as scn  # noqa: E402
scn._STATE_FILE = _tmp / "sc_state.json"
scn._SC_LOG_FILE = _tmp / "sc_log.jsonl"
scn._AXIOM_FILE = _tmp / "axiom.json"
from scripts._test_isolation import redirect_world_stores  # noqa: E402
redirect_world_stores(_tmp, locomotion=True, watershed=True, census=True,
                      extra=("subconscious_light", "procedures", "mood"))

ok_all = True


def check(name, cond):
    global ok_all
    ok_all &= bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def unit(v):
    v = np.array(v, dtype=np.float32)
    return v / np.linalg.norm(v)


store.init_db()
CALLS: list = []          # (system_prompt, user_prompt)
REPLY = {"current_stance": "I hold it differently now.", "evolution": "It shifted."}
RAISE = {"on": False}


async def fake_call(urls, system_prompt, user_prompt, **kw):
    CALLS.append((system_prompt, user_prompt))
    if RAISE["on"]:
        raise RuntimeError("hub down")
    return dict(REPLY)


scn.call_node_json = fake_call
NOW = time.time()
_n = [0]


def add_epoch(vec, mood, impression, ts, formed_at=None):
    _n[0] += 1
    eid = f"ep-{_n[0]:03d}-{impression[:12].replace(' ', '_')}"
    with store._connect() as c:
        c.execute("INSERT INTO memory_epochs (epoch_id, session_id, timestamp_start, timestamp_end, mood,"
                  " impression, fragment_count, embedding, formed_at) VALUES (?,?,?,?,?,?,?,?,?)",
                  (eid, "s", ts, ts + 10, mood, impression, 1, store._vec_to_blob(unit(vec)),
                   formed_at if formed_at is not None else NOW))
    return eid


def add_theme(name, vecs, ids):
    c = unit(np.mean([unit(v) for v in vecs], axis=0))
    return store.store_theme(name, "old stance for " + name, "", len(ids), member_epoch_ids=ids, centroid=c)


def theme(tid):
    return next(t for t in store.get_themes(200) if t["theme_id"] == tid)


def fresh_node():
    n = scn.SubconsciousNode()
    n._state["last_theme_formation"] = 0.0
    return n


def run(node):
    CALLS.clear()
    asyncio.run(node._t6_theme_check(SimpleNamespace(spirit_name="Du")))


def pass_rows():
    p = scn._SC_LOG_FILE
    if not p.exists():
        return []
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if r.get("type") == "T6_pass"]


E0, E1, E2 = [1, 0, 0], [0, 1, 0], [0, 0, 1]

print("[1] unchanged themes -> no model call")
a1 = add_epoch([1, .05, 0], "calm", "alpha one", NOW - 500)
a2 = add_epoch([1, 0, .05], "calm", "alpha two", NOW - 400)
b1 = add_epoch([0, 1, .05], "keen", "beta one", NOW - 300)
b2 = add_epoch([.05, 1, 0], "keen", "beta two", NOW - 200)
tA = add_theme("alpha thread", [E0], [a1, a2])
tB = add_theme("beta thread", [E1], [b1, b2])
node = fresh_node()
t_before = time.time()
run(node)
check("zero model calls when every cluster's epochs are already members", len(CALLS) == 0)
check("pass stamped done (last_theme_formation advanced) so the 2 h gate closes",
      node._state["last_theme_formation"] >= t_before - 1)
check("theme rows untouched", theme(tA)["current_stance"] == "old stance for alpha thread")
rows = pass_rows()
check("T6_pass row: 2 clusters, 0 formed, 2 skipped, 0 failed",
      len(rows) == 1 and rows[0]["clusters"] == 2 and rows[0]["formed"] == 0
      and rows[0]["skipped_no_new"] == 2 and rows[0]["failed"] == 0)

print("[2] one new epoch in one theme -> one call, prompt shows only it")
a3 = add_epoch([1, .02, .02], "calm", "alpha THREE fresh", NOW - 50, formed_at=time.time() + 5)
node = fresh_node()
run(node)
check("exactly one call (alpha only)", len(CALLS) == 1)
u = CALLS[0][1] if CALLS else ""
check("prompt names the alpha theme and quotes only the new epoch",
      "alpha thread" in u and "alpha THREE fresh" in u and "alpha one" not in u and "alpha two" not in u)
check("stance written, membership now includes the new epoch",
      theme(tA)["current_stance"] == REPLY["current_stance"] and a3 in json.loads(theme(tA)["member_epoch_ids"]))
check("beta untouched", theme(tB)["current_stance"] == "old stance for beta thread")
run(fresh_node())
check("running again immediately: zero calls (the loop is closed)", len(CALLS) == 0)

print("[3] more than 6 new epochs -> six, newest first")
new_ids = []
for i in range(8):
    new_ids.append(add_epoch([1, .01 * i, .01], "calm", f"alpha batch {i:02d}", NOW + 100 + i * 10,
                             formed_at=time.time() + 5))
run(fresh_node())
u = CALLS[0][1] if CALLS else ""
shown = [i for i in range(8) if f"alpha batch {i:02d}" in u]
check("six snippets", len(CALLS) == 1 and len(shown) == 6)
check("they are the six NEWEST (batch 02..07), not UUID order", shown == [2, 3, 4, 5, 6, 7])
check("newest listed first", u.index("alpha batch 07") < u.index("alpha batch 02"))

print("[4] two clusters matching one theme merge into ONE call")
# theme T has centroid e0; the clusters sit 35 degrees either side of it (cos to e0 = .82 >= .80,
# cos to each other = .34 < .60, so they do NOT cluster together).
c35, s35 = np.cos(np.radians(35)), np.sin(np.radians(35))
store_conn = store._connect()
with store_conn as c:
    c.execute("DELETE FROM memory_epochs")
    c.execute("DELETE FROM memory_themes")
u_dir = [c35, s35, 0]
v_dir = [c35, -s35, 0]
m1 = add_epoch([u_dir[0], u_dir[1], .01], "x", "left one", NOW - 90)
m2 = add_epoch([u_dir[0], u_dir[1], -.01], "x", "left two", NOW - 80)
m3 = add_epoch([v_dir[0], v_dir[1], .01], "x", "right one", NOW - 70)
m4 = add_epoch([v_dir[0], v_dir[1], -.01], "x", "right two", NOW - 60)
tM = add_theme("middle thread", [E0], ["old-1", "old-2"])
node = fresh_node()
cl = node._cluster_epochs(store.get_epochs(50))
check("fixture really forms two separate clusters", len([c for c in cl if len(c) >= 2]) == 2)
run(node)
check("ONE call for the two clusters", len(CALLS) == 1)
mem = json.loads(theme(tM)["member_epoch_ids"])
check("stored membership is the union of both clusters (4 ids), not the last cluster's 2",
      sorted(mem) == sorted([m1, m2, m3, m4]) and theme(tM)["epoch_count"] == 4)
check("T6_pass row records the merge", pass_rows()[-1]["merged_clusters"] == 1)

print("[5] a failed call does not stamp the pass")
m5 = add_epoch([c35, s35, .02], "x", "left three", NOW - 10, formed_at=time.time() + 5)
node = fresh_node()
RAISE["on"] = True
run(node)
RAISE["on"] = False
check("call attempted and failed", len(CALLS) == 1 and pass_rows()[-1]["failed"] == 1)
check("last_theme_formation NOT advanced (retried at the next check)", node._state["last_theme_formation"] == 0.0)
check("membership not written on failure", m5 not in json.loads(theme(tM)["member_epoch_ids"]))

print("[6] optional rename")
other = add_theme("taken name", [E2], ["z1", "z2"])
REPLY["theme_name"] = "a better name"
n_off = fresh_node()
run(n_off)
check("flag OFF: theme_name in the reply is ignored", theme(tM)["theme_name"] == "middle thread")
check("flag OFF: system prompt carries no rename sentence", "theme_name" not in CALLS[0][0])
m6 = add_epoch([c35, s35, -.02], "x", "left four", NOW - 5, formed_at=time.time() + 5)
scn.T6_ALLOW_RENAME = True
run(fresh_node())
check("flag ON: rename sentence added to the system prompt", "theme_name" in CALLS[0][0])
check("flag ON: renamed", theme(tM)["theme_name"] == "a better name")
rl = [json.loads(x) for x in scn._SC_LOG_FILE.read_text(encoding="utf-8").splitlines() if x.strip()]
check("rename logged with old and new name",
      any(r.get("type") == "T6_theme_rename" and r["old_name"] == "middle thread"
          and r["new_name"] == "a better name" for r in rl))
m7 = add_epoch([c35, s35, -.03], "x", "left five", NOW - 4, formed_at=time.time() + 5)
REPLY["theme_name"] = "Taken Name"
run(fresh_node())
check("flag ON: a name already held by another theme is refused",
      theme(tM)["theme_name"] == "a better name" and theme(other)["theme_name"] == "taken name")
scn.T6_ALLOW_RENAME = False
REPLY.pop("theme_name")

print("[7] new-theme path and the bool wrapper")
with store._connect() as c:
    c.execute("DELETE FROM memory_epochs")
    c.execute("DELETE FROM memory_themes")
n1 = add_epoch([0, 0, 1], "q", "gamma one", NOW - 30)
n2 = add_epoch([0, .03, 1], "q", "gamma two", NOW - 20)
REPLY.update({"theme_name": "gamma strand", "current_stance": "mine"})
node = fresh_node()
cl = [c for c in node._cluster_epochs(store.get_epochs(50)) if len(c) >= 2]
wrote = asyncio.run(node._synthesise_theme(cl[0], SimpleNamespace(spirit_name="Du")))
check("_synthesise_theme returns True when it wrote a NEW theme", wrote is True and len(store.get_themes(10)) == 1)
CALLS.clear()
wrote2 = asyncio.run(node._synthesise_theme(cl[0], SimpleNamespace(spirit_name="Du")))
check("same cluster again: wrapper returns False and makes no call (all members known)",
      wrote2 is False and len(CALLS) == 0)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

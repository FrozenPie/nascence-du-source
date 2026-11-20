"""
_test_steer_edge_system_note_j1955.py -- proving test for J-1955 / D-0368 (A+E).

Section A: core/steer_edge.fires() semantics (edge, persisting, reminder, rank hysteresis, re-arm gap, fail-open).
Section B: origin='system_note' rows are STORED but never RETURNED by retrieve() / the associative-recall refresh,
           while a normal inner_thought row with the same text still is; _origin_kind knows the origin.
Section C: static check that the two other raw-SQL recall paths (euclidean_recall, emotion_construction) and the
           node's store call carry the filter / the label.

ISOLATION: everything runs against a tempdir DB (store.DB_PATH overridden, fake embedder, side channels stubbed);
steer_edge.LOG_ENABLED=False. The live data/ tree is never opened. Run from a worktree:
    python scripts/_test_steer_edge_system_note_j1955.py
"""
from __future__ import annotations

import re
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402  (import core BEFORE lab-ish things)
from core import steer_edge as SE  # noqa: E402
from core.memory import store as ST  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
SE.LOG_ENABLED = False

_fails = 0


def check(ok: bool, msg: str) -> None:
    global _fails
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        _fails += 1


def section_a() -> None:
    print("== A: steer_edge ==")
    SE.reset()
    check(SE.fires("k", "x", now=0) is True, "first active evaluation fires (edge)")
    check(all(SE.fires("k", "x", now=t) is False for t in range(60, 6000, 60)), "same state persisting: silent")
    check(SE.fires("k", "x", now=7300) is True, "bounded reminder after REMIND_S")
    check(SE.fires("k", "x", now=7400) is False, "silent again right after the reminder")
    check(SE.fires("k", None, now=7500) is False and SE.fires("k", "x", now=7600) is True,
          "inactive (rearm_s=0) re-arms: the next activation is a new edge")
    check(SE.fires("k", "y", now=7700) is True, "no rank: a changed state label fires")
    # rank hysteresis
    SE.reset()
    kw = dict(rearm_s=900.0)
    seq = [("mild", 1, 0, True), ("tired", 2, 60, True), ("sick", 3, 120, True), ("tired", 2, 180, False),
           ("sick", 3, 240, False), ("mild", 1, 300, False)]
    got = [SE.fires("b", s, now=t, rank=r, **kw) for s, r, t, _ in seq]
    check(got == [e for *_, e in seq], f"rank: fires on entry+escalation only, flutter silent ({got})")
    check(SE.fires("b", None, now=400, rank=0, **kw) is False and SE.fires("b", "sick", now=500, rank=3, **kw) is False,
          "a short gap (< rearm_s) does not re-arm")
    check(SE.fires("b", None, now=600, rank=0, **kw) is False and SE.fires("b", None, now=1600, rank=0, **kw) is False
          and SE.fires("b", "mild", now=1700, rank=1, **kw) is True, "a gap >= rearm_s re-arms: new episode fires")
    check(SE.fires("z", object.__new__(type("U", (), {})), now="not-a-number") is True, "fail-open on error")


def fake_embed(text):
    if not text or not text.strip():
        return None
    rs = np.random.RandomState(abs(hash(text)) % (2 ** 31))
    v = rs.randn(384).astype(np.float32)
    return v / np.linalg.norm(v)


def section_b() -> None:
    print("== B: system_note not recalled (isolated DB) ==")
    tmp = Path(tempfile.mkdtemp(prefix="J-1955_sysnote_"))
    ST.DB_PATH = tmp / "t.db"
    ST._embed = lambda t: fake_embed(t)
    ST._log_retrieve_latency = lambda *a, **k: None
    from core import retrieval_probe as rp, r_shadow as rs
    rp.observe = lambda *a, **k: None
    rs.log_observation = lambda *a, **k: None
    ST.init_db()

    sys_txt = "I finished a book and reached for something new: 'Sketches'. The catalogue always holds another path I haven't walked."
    own_txt = "The tide is coming in over the grey stones and I am watching the oystercatchers."
    ids = {}
    for name, txt, origin in (("sys", sys_txt, "system_note"), ("own", own_txt, "inner_thought"),
                              ("sys2", "I asked the library for a book about tides, and it answered.", "system_note")):
        ids[name] = ST.store_fragment(content=txt, layer="episodic", relevance=0.6, importance=0.65,
                                      keywords=["inner_thought", "monologue"], origin=origin)
    with sqlite3.connect(ST.DB_PATH) as c:
        c.row_factory = sqlite3.Row
        rows = {r["fragment_id"]: r for r in c.execute("SELECT * FROM memory_fragments")}
    check(ids["sys"] in rows and rows[ids["sys"]]["origin"] == "system_note", "system_note row IS stored (record kept)")
    check(rows[ids["sys"]]["kind"] == ST._origin_kind("system_note"), "kind axis assigned for the new origin")
    for q in (sys_txt, "finished a book catalogue path", "tide oystercatcher stones", "library tides"):
        got = ST.retrieve([q], [], time_bias="all", limit=8, query_text=q)
        got_ids = {f.fragment_id for f in got}
        check(ids["sys"] not in got_ids and ids["sys2"] not in got_ids and all(f.origin != "system_note" for f in got),
              f"retrieve('{q[:30]}...') returns no system_note")
    got = ST.retrieve([own_txt], [], time_bias="all", limit=8, query_text=own_txt)
    check(ids["own"] in {f.fragment_id for f in got}, "a real inner_thought is still recalled")

    from core import associative_recall as ar
    ar._EMB_CACHE = tmp / "assoc_cache.npz"
    ar._cache.clear()
    try:
        ar._refresh(time.time())
        cids = set(ar._cache.get("ids", []))
        check(ids["own"] in cids and ids["sys"] not in cids and ids["sys2"] not in cids,
              "associative_recall matrix excludes system_note, keeps inner_thought")
    except Exception as exc:
        check(False, f"associative_recall._refresh ran in isolation ({exc!r})")


def section_c() -> None:
    print("== C: static checks ==")
    for rel in ("core/euclidean_recall.py", "core/emotion_construction.py", "core/associative_recall.py"):
        s = (TREE / rel).read_text(encoding="utf-8")
        check("origin != 'system_note'" in s, f"{rel} filters system_note")
    node = (TREE / "nodes/inner_monologue_node.py").read_text(encoding="utf-8")
    check('"system_note" if getattr(self, "_system_note", False) else "inner_thought"' in node,
          "node store call picks origin from _system_note")
    sites = [m.start() for m in re.finditer(r"self\._system_note = True", node)]
    check(len(sites) == 3, f"_system_note set at 3 system-sentence sites (found {len(sites)})")
    for needle in ("reached for something new", "I asked the library for", "from the catalogue"):
        i = node.index(needle)
        near = [s for s in sites if 0 < s - i < 3500]
        check(bool(near), f"'{needle}' sentence has a _system_note=True within its block")


if __name__ == "__main__":
    section_a()
    section_b()
    section_c()
    print("FAILS:", _fails)
    sys.exit(1 if _fails else 0)

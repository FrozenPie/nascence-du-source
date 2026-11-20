"""
Hermetic test for J-3194 / D-0581: a reread always stores a NEW pass-tagged study note; a revision never
crosses a pass boundary (core/study_note.py find_revisable + write_or_revise).

No LLM, no embedder, no live data: runs INSIDE lab_env.isolate(db="empty"); store._embed is a deterministic fake;
compose/_revise/store_note are fakes (the real store_note also writes the study dir and the knowledge
learn_from_text() stores, which this test does not need). The real find_revisable runs against the isolated DB.

  [1] find_revisable(book_pass=None): pre-D-0581 behaviour -- the nearest duplicate wins whatever its pass
  [2] book_pass=1: a pass-0 (and a NULL-pass) note is skipped -> None; a pass-1 note is found (same pass revises)
  [3] book_pass=0: nothing is lower than the first read, so no candidate is skipped
  [4] masking: pass-0 note nearer than a pass-1 note, session pass 1 -> the pass-1 note is the target
  [5] a chapter-filed note (chapter_id set) is never a candidate (the corrected docstring's claim)
  [6] write_or_revise: reread session (pass 1) over a pass-0 duplicate -> action "new", store_note gets no
      revise_target; same-pass session (pass 0) -> "revised" with the pass-0 target; no session -> "revised"

Run:  python scripts/study_note_reread_test.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423): the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import numpy as np
from core import study_note as sn
from core.memory import store
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

def _vec(angle: float) -> np.ndarray:
    v = np.array([np.cos(angle), np.sin(angle), 0.0, 0.0], dtype=np.float32)
    return v / np.linalg.norm(v)

def _fake_embed(text: str):
    # "ANG:<float>" in the text picks the direction; the note's own text carries ANG:0.0
    import re
    m = re.search(r"ANG:([-\d.]+)", text or "")
    return _vec(float(m.group(1))) if m else _vec(0.0)

NOTE = {"title": "Bonaparte", "subject": "ANG:0.0 Brumaire", "key_facts": [], "thoughts": "", "connects_to": "",
        "question": "", "understanding": "I see that Bonaparte engineered a transition by deception. ANG:0.0"}

with isolate(db="empty") as lab_dir:
    assert "_lab" in str(store.DB_PATH), store.DB_PATH
    store._embed = _fake_embed
    def put(tag: str, angle: float, source_pass, chapter=None):
        fid = store.store_fragment(content=f"[My study note: '{tag}' · on 'Memoirs'] ANG:{angle}", layer="episodic",
                                   relevance=0.8, importance=0.8, keywords=["study"], origin="study",
                                   source_type="study_note", source_id="", source_pass=source_pass)
        if chapter is not None:
            with store._connect() as c:
                c.execute("UPDATE memory_fragments SET chapter_id=? WHERE fragment_id=?", (chapter, fid)); c.commit()
        return fid

    print("[1] book_pass=None")
    f_p0 = put("p0", 0.0, 0)
    t = sn.find_revisable(NOTE)
    check("no session -> nearest duplicate found whatever its pass", t is not None and t[0] == f_p0)

    print("[2] reread skips lower pass")
    check("book_pass=1, only a pass-0 note -> None (reread stores new)", sn.find_revisable(NOTE, book_pass=1) is None)
    f_null = put("pnull", 0.0, None)
    check("book_pass=1, NULL-pass note reads as pass 0 -> still skipped", sn.find_revisable(NOTE, book_pass=1) is None)
    f_p1 = put("p1", 0.1, 1)
    t = sn.find_revisable(NOTE, book_pass=1)
    check("book_pass=1 with a pass-1 note -> that note (same pass revises)", t is not None and t[0] == f_p1)

    print("[3] book_pass=0 does not skip a later-pass note")
    t = sn.find_revisable(NOTE, book_pass=0)
    check("book_pass=0 -> a candidate is returned (nothing is lower than pass 0)", t is not None)

    print("[4] masking")
    check("pass-0 notes are nearer (cos 1.0) than the pass-1 note (cos ~0.995), session pass 1 -> pass-1 note",
          sn.find_revisable(NOTE, book_pass=1)[0] == f_p1)

    print("[5] chapter-filed note is never a candidate")
    f_filed = put("filed", 0.0, 1, chapter="ch_1")
    t = sn.find_revisable(NOTE, book_pass=1)
    check("a chapter-filed pass-1 note exactly on target is ignored", t is not None and t[0] == f_p1 and t[0] != f_filed)

    print("[6] write_or_revise end to end")
    async def fake_compose(call_json, base_urls, book_title, passage, related_text=""):
        return dict(NOTE)
    async def fake_revise(call_json, base_urls, existing_body, new_note, **kw):   # J-2961: + existing_extra
        return dict(new_note)
    stored = []
    def fake_store(n, book_title, revise_target=None, session=None, **kw):   # J-2961: + prior
        stored.append(revise_target)
        return {"action": "revised" if revise_target else "new", "path": "", "fragment_id": "f_x", "linked": 0}
    sn.compose_note, sn._revise, sn.store_note = fake_compose, fake_revise, fake_store
    sn._related_context = lambda bt, p: ("", [])
    sn._log_m1_co_recall = lambda *a, **k: None
    sn._first_sentence = lambda t: ""        # no follow-line boarding (that writes frontier/shadow stores)
    # isolate the test to a state with ONLY a pass-0 duplicate
    with store._connect() as c:
        c.execute("DELETE FROM memory_fragments WHERE fragment_id != ?", (f_p0,)); c.commit()
    out = asyncio.run(sn.write_or_revise(None, [], "Memoirs", "p", session=[{"pass": 1, "encounter_id": "e1"}]))
    check("reread (pass 1) over a pass-0 duplicate -> new note, no revise target",
          out["action"] == "new" and stored[-1] is None)
    out = asyncio.run(sn.write_or_revise(None, [], "Memoirs", "p", session=[{"pass": 0, "encounter_id": "e2"}]))
    check("same pass (0) -> revised, target is the pass-0 note",
          out["action"] == "revised" and stored[-1] is not None and stored[-1][0] == f_p0)
    out = asyncio.run(sn.write_or_revise(None, [], "Memoirs", "p"))
    check("no session -> revised (pre-D-0581 behaviour)", out["action"] == "revised" and stored[-1][0] == f_p0)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)

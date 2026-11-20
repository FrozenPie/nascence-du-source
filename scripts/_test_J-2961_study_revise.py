"""J-2961 (F-3653, F-3649): study_note's revise path. Offline. Temp DB and temp study dir only (store.DB_PATH and
study_note.STUDY_DIR redirected before the first call, chunking log redirected); never opens data/memory/nascence.db
and writes nothing under the repo's data/. The model call (call_json) is a stub.

Covers:
  1. a revise that returns None leaves the OLD file bytes and the OLD fragment (content + embedding) unchanged, stores
     the new note as its own new note, and the result says "new" (it used to overwrite and say "revised").
  2. a successful revise sends the new reading's thoughts, connects_to and question AND the old note's connects_to
     and question (read from its file), and does not cut a 4,000-character existing note.
  3. the revise branch of store_note: fragment content + embedding refreshed, the diegetic hooks run, and the file
     frontmatter records the old sittings + the new ones (chars add; a sitting already counted is not counted twice).
  4. _read_note_file / _revise_prompt / the cut at a boundary.
Run from the worktree:  python scripts/_test_J-2961_study_revise.py
"""
import asyncio
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["NASCENCE_TRAINING_LOG"] = "0"
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                              # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
import numpy as np                                      # noqa: E402
import core.memory.store as store                       # noqa: E402
from core import study_note as sn                       # noqa: E402

assert Path(sn.__file__).resolve().parent.parent == TREE, "tested the wrong tree"

_TMP = Path(tempfile.mkdtemp(prefix="j2961_study_revise_"))
store.DB_PATH = _TMP / "test.db"
sn.STUDY_DIR = _TMP / "Study"
sn.NOTES_SUBDIR = _TMP / "Study" / "Notes"
sn._CHUNK_LOG = _TMP / "chunk_log.jsonl"
assert str(store.DB_PATH).startswith(str(_TMP))


def _fake_embed(text):
    """Same topic word -> cosine ~1 (so find_revisable matches); the text changes the vector a little (so a
    refreshed embedding is visibly different)."""
    if not text or not text.strip():
        return None
    v = np.zeros(16, dtype=np.float32)
    v[0 if "Hume" in text else 1] = 10.0
    v[2 + (sum(map(ord, text)) % 12)] = 1.0
    return (v / np.linalg.norm(v)).astype(np.float32)


store._embed = _fake_embed
from core import follow_line as _fl                     # noqa: E402
_boarded = []
_fl.board = lambda *a, **k: _boarded.append(a[0]) or None   # no write to data/frontier.json
_fl.fire = lambda *a, **k: None
sn._log_m1_co_recall = lambda *a, **k: None             # no live-ledger write

_fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        _fails.append(msg)


def frag_row(fid):
    c = sqlite3.connect(str(store.DB_PATH))
    c.row_factory = sqlite3.Row
    try:
        return c.execute("SELECT * FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
    finally:
        c.close()


def n_frags():
    c = sqlite3.connect(str(store.DB_PATH))
    try:
        return c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='study'").fetchone()[0]
    finally:
        c.close()


def note(title="On testimony", subject="Hume testimony", und="I see that testimony rests on habit. Hume says so.",
         facts=None, thoughts="", connects="", question=""):
    return {"title": title, "subject": subject, "understanding": und, "key_facts": facts or ["Cato", "frost"],
            "thoughts": thoughts, "connects_to": connects, "question": question}


def sess(eid, chars, pass_=0):
    return {"pass": pass_, "encounter_id": eid, "seen_chars": chars}


store.init_db()
BOOK = "An Enquiry Concerning Human Understanding"

# ---- a first note (new path) --------------------------------------------------------------------------------------
learned = []
sn._diegetic_learn = lambda n, body: learned.append(n["title"])
first = note(thoughts="It unsettles me.", connects="Links to Locke on habit.", question="Is custom enough?")
r0 = sn.store_note(first, BOOK, session=[sess("e1", 900), sess("e2", 700)])
check(r0["action"] == "new" and r0["fragment_id"] and Path(r0["path"]).exists(), "first note stored as new")
check(learned == ["On testimony"], "new-note branch runs the diegetic hooks (via _diegetic_learn)")
fid, fpath = r0["fragment_id"], Path(r0["path"])
head = fpath.read_text(encoding="utf-8")[:400]
check("sittings: 2" in head and "chars: 1600" in head, f"first file frontmatter: 2 sittings, 1600 chars ({head[40:160]!r})")

# ---- 4. _read_note_file ---------------------------------------------------------------------------------------------
pf = sn._read_note_file(fpath)
check(pf.get("sittings") == 2 and pf.get("chars") == 1600 and pf.get("pass") == 0, f"_read_note_file frontmatter {pf}")
check(pf.get("connects_to") == "Links to Locke on habit." and pf.get("question") == "Is custom enough?",
      "_read_note_file returns the connects_to / question the fragment text does not carry")
check(sn._read_note_file(None) == {} and sn._read_note_file(_TMP / "nope.md") == {}, "_read_note_file: no file -> {}")

# ---- 1. a failed revise leaves the old note alone -------------------------------------------------------------------
old_bytes = fpath.read_bytes()
old_row = frag_row(fid)
n_before = n_frags()
calls = []


async def cj_none(base_urls, system, user, **kw):
    calls.append(user)
    if system == sn._REVISE_SYS:
        return None
    return {"title": "Testimony again", "subject": "Hume testimony",
            "understanding": "I see that testimony needs experience of conjunction. Hume's Indian prince.",
            "key_facts": ["Indian prince", "Cato"], "thoughts": "New thoughts.", "connects_to": "New link.",
            "question": "New question?"}


learned.clear()
out = asyncio.run(sn.write_or_revise(cj_none, ["x"], BOOK, "A passage on Hume and testimony. " * 20,
                                     session=[sess("e3", 500)]))
check(any(u.startswith("MY EXISTING NOTE") for u in calls), "the revise call was attempted (the notes matched)")
check(out.get("action") == "new", f"failed revise -> the new note is stored as NEW (got {out.get('action')!r})")
check(fpath.read_bytes() == old_bytes, "failed revise: the old note FILE is byte-identical")
now_row = frag_row(fid)
check(now_row["content"] == old_row["content"] and now_row["embedding"] == old_row["embedding"],
      "failed revise: the old fragment content and embedding are unchanged")
check(n_frags() == n_before + 1 and out["fragment_id"] != fid, "failed revise: one extra fragment (the new note)")
check(len(_boarded) == 1, "failed revise: the new note boards the follow line as any new note does")

# ---- 2/3. a successful revise ---------------------------------------------------------------------------------------
# a long existing body (> 2,500 chars) with a tail marker, to prove it is no longer cut at 2,500
long_und = "I see that testimony rests on habit. " + ("The reasoning is long and careful. " * 100)
second = note(title="Long note", und=long_und, thoughts="TAILMARK thoughts at the end.",
              connects="Old link to Locke.", question="Old question?")
r1 = sn.store_note(second, BOOK, session=[sess("a1", 2000)])
fid1, p1 = r1["fragment_id"], Path(r1["path"])
old_row1 = frag_row(fid1)
old_frag = old_row1["content"]
check(len(old_frag) > 3000 and "TAILMARK" in old_frag, f"the long fragment is {len(old_frag)} chars, tail kept")
seen_prompts = []


async def cj_ok(base_urls, system, user, **kw):
    seen_prompts.append((system, user))
    return {"title": "Long note deepened", "subject": "Hume testimony",
            "understanding": "I now see testimony as habit joined to conjunction.", "key_facts": ["Cato", "prince"],
            "thoughts": "Deeper thoughts.", "connects_to": "Merged link.", "question": "Merged question?"}


new_reading = note(title="x", und="I see that testimony is weighed by experience. Hume, again.",
                   thoughts="NEWTHOUGHT about the Hume miracles.", connects="NEWCONNECT to Berkeley.",
                   question="NEWQUESTION about Hume's prince?")
learned.clear()
target = (fid1, old_frag, p1)
prior = sn._read_note_file(p1)
d = asyncio.run(sn._revise(cj_ok, ["x"], old_frag, new_reading, existing_extra=prior))
check(d is not None and d["title"] == "Long note deepened", "_revise returns the model's note")
sysm, user = seen_prompts[-1]
check(sysm == sn._REVISE_SYS, "_REVISE_SYS wording untouched (the system prompt is the module constant)")
check("TAILMARK" in user, "the existing note's tail (past 2,500 chars) reaches the prompt")
for needle in ("NEWTHOUGHT", "NEWCONNECT", "NEWQUESTION"):
    check(needle in user, f"new reading's {needle} is sent")
check("Connects to: Old link to Locke." in user and "Still wondering: Old question?" in user,
      "the existing note's connects_to / question (from its file) are sent")
# a body above the cap is cut at a boundary, not mid-word
big = ("alpha beta gamma. " * 800)
p = sn._revise_prompt(big, new_reading)
body_part = p.split("\n\nWHAT I JUST READ")[0] if "\n\nWHAT I JUST READ" in p else p
check(len(body_part) < len(big) and body_part.rstrip().endswith("."), "an over-cap body is cut at a sentence end")

# store_note revise branch, cross-session (known_ids empty): old 1 sitting / 2000 chars + new 2 sittings / 900 chars
r2 = sn.store_note(d, BOOK, revise_target=target, session=[sess("b1", 400), sess("b2", 500)],
                   prior=dict(prior, known_ids=set()))
check(r2["action"] == "revised" and r2["fragment_id"] == fid1, "revise branch -> action revised, same fragment")
head2 = p1.read_text(encoding="utf-8")[:400]
check("sittings: 3" in head2 and "chars: 2900" in head2 and "revised" in head2,
      f"frontmatter = old + new (3 sittings, 2900 chars) ({head2[40:200]!r})")
row2 = frag_row(fid1)
check(row2["content"] != old_frag and "TAILMARK" not in row2["content"] and "habit joined" in row2["content"],
      "fragment content updated to the revised note")
check(row2["embedding"] is not None and row2["embedding"] != old_row1["embedding"], "fragment embedding refreshed (not the old text's vector)")
check(row2["embedding"] == store._vec_to_blob(_fake_embed(row2["content"])), "embedding == embed(new content)")
check(learned == ["Long note deepened"], "revise branch runs the diegetic hooks")

# same-session chunk revise: a sitting already counted (b2) is not counted twice, chars still add
prior2 = dict(sn._read_note_file(p1), known_ids={"b1", "b2"})
sn.store_note(d, BOOK, revise_target=(fid1, row2["content"], p1), session=[sess("b2", 300), sess("b3", 200)],
              prior=prior2)
head3 = p1.read_text(encoding="utf-8")[:400]
check("sittings: 4" in head3 and "chars: 3400" in head3, f"known sitting not double-counted (4 / 3400) ({head3[40:200]!r})")

# no prior (old callers): behaviour as before, the new session alone
sn.store_note(d, BOOK, revise_target=(fid1, row2["content"], p1), session=[sess("z", 50)])
check("sittings: 1" in p1.read_text(encoding="utf-8")[:400], "no `prior` -> the pre-fix frontmatter (new session only)")

# ---- the follow line / M1 logging do not break the fallback ---------------------------------------------------------
check(not _fails, "all checks")
print("FAILED:" if _fails else "ALL PASS", _fails)
sys.exit(1 if _fails else 0)

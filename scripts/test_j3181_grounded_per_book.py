"""J-3181 / D-0568: grounded learning per book (core/grounded_learning.py consolidate).

Nothing here opens a live store or calls a hub: memory is a temp sqlite file standing in for core.memory.store._connect,
the embedder is a deterministic fake, the model call is scripted, store_fragment / store_light_event are recorders and
every path grounded_learning writes (_STATE, _LOG, _ATTEMPT_LOG) is a temp path.
Run from the worktree:  python scripts/test_j3181_grounded_per_book.py
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                    # noqa: E402  (before anything that could resolve to C:\Nascence)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import grounded_learning as gl      # noqa: E402
from core.memory import store                  # noqa: E402

FAILS: list[str] = []
TMP = Path(tempfile.mkdtemp(prefix="J-3181_"))
DOT = "\u00b7"
GOOD = ("Machiavelli argues that a ruler keeps power by being feared more than loved when he cannot be both, "
        "and that necessity excuses acts a private man could not defend. He treats cruelty as a tool to be used "
        "once and well. The book keeps returning to fortune and to how far skill can turn it.")


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
        print("  FAIL:", msg)


def fake_embed(text: str):
    v = np.zeros(32, dtype=np.float32)
    for w in (text or "").lower().split():
        h = int(hashlib.md5(w.encode()).hexdigest(), 16)
        v[h % 32] += 1.0
    n = np.linalg.norm(v)
    return (v / n).astype(np.float32) if n else None


class DB:
    """A temp memory DB with the columns consolidate reads; _connect() hands out connections to it."""
    def __init__(self):
        self.path = TMP / f"mem_{len(list(TMP.iterdir()))}.db"
        c = sqlite3.connect(str(self.path))
        c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT, timestamp REAL, "
                  "embedding BLOB, encounter_id TEXT)")
        c.commit()
        c.close()
        self.n = 0

    def add(self, origin, content, ts, enc=None, vec_text=None):
        self.n += 1
        e = fake_embed(vec_text or content)
        c = sqlite3.connect(str(self.path))
        c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?)",
                  (f"f{self.n}", content, origin, ts, e.tobytes() if e is not None else None, enc))
        c.commit()
        c.close()

    def connect(self):
        c = sqlite3.connect(str(self.path))
        c.row_factory = sqlite3.Row
        return c


def reading(db, book, i, ts, enc=None, body=None):
    db.add("reading", f"[From '{book}'] {body or f'passage {i} of {book} speaks of ' + book.split()[-1].lower() + f' matter{i} ' + 'word ' * 90}",
           ts, enc)


def study(db, book, ts, enc=None, text="I see that the prince must be feared"):
    db.add("study", f"[My study note: 'On fear' {DOT} on '{book[:50]}' {DOT} subject: rule] {text}", ts, enc)


_ENVS = [0]


class Env:
    def __init__(self, db, replies, state=None):
        _ENVS[0] += 1
        self.k = _ENVS[0]
        self.db, self.replies, self.calls, self.stored, self.lights = db, list(replies), [], [], []
        self.st = TMP / f"state_{self.k}.json"
        self.lg = TMP / f"log_{self.k}.jsonl"
        self.at = TMP / f"att_{self.k}.jsonl"
        if state is not None:
            self.st.write_text(json.dumps(state), encoding="utf-8")

    async def call_json(self, urls, sys_p, user_p, max_tokens=0, temperature=0.0):
        self.calls.append({"sys": sys_p, "user": user_p, "temp": temperature})
        r = self.replies.pop(0) if self.replies else {"understanding": GOOD}
        if isinstance(r, Exception):
            raise r
        return r

    def run(self, **kw):
        from core import mood
        patches = [mock.patch.object(store, "_connect", self.db.connect), mock.patch.object(store, "_embed", fake_embed),
                   mock.patch.object(store, "store_fragment", lambda **k: self.stored.append(k) or "fid"),
                   mock.patch.object(store, "store_light_event", lambda **k: self.lights.append(k) or "lid"),
                   mock.patch.object(mood, "current_vec", lambda: None), mock.patch.object(mood, "current_valence", lambda: 0.0),
                   mock.patch.object(mood, "current_felt", lambda: ""),
                   mock.patch.object(gl, "_STATE", self.st), mock.patch.object(gl, "_LOG", self.lg),
                   mock.patch.object(gl, "_ATTEMPT_LOG", self.at)]
        for k, v in kw.items():
            patches.append(mock.patch.object(gl, k, v))
        for p in patches:
            p.start()
        try:
            return asyncio.run(gl.consolidate(self.call_json, ["x"]))
        finally:
            for p in reversed(patches):
                p.stop()

    def state(self):
        return json.loads(self.st.read_text(encoding="utf-8"))

    def attempts(self):
        return [json.loads(x) for x in self.at.read_text(encoding="utf-8").splitlines()] if self.at.exists() else []


NOW = time.time()


def test_group_by_book_and_label():
    db = DB()
    for i in range(6):
        reading(db, "The Prince", i, NOW - 5000 + i)
        reading(db, "Walden Pond Notes", i, NOW - 4990 + i)
    e = Env(db, [], state={"last_ts": NOW - 10000})
    out = e.run()
    check(out == GOOD, "returns the first note")
    check(len(e.calls) == 2 and len(e.stored) == 2, f"one note per book, got {len(e.calls)} calls {len(e.stored)} stored")
    for c in e.calls:
        u = c["user"]
        check(("Prince" in u) != ("Walden" in u), "a call's material names exactly one book")
    labels = sorted(s["content"].split("]")[0] for s in e.stored)
    check(labels == ["[Understanding — from 'The Prince'", "[Understanding — from 'Walden Pond Notes'"], f"labels {labels}")
    check(len(e.lights) == 1, f"ONE light event per sleep for two notes, got {len(e.lights)}")
    check(all(s["keywords"][2] in ("the prince", "walden pond notes") for s in e.stored), "keywords carry the book")


def test_prompt_wording():
    db = DB()
    for i in range(4):
        reading(db, "The Prince", i, NOW - 500 + i)
    e = Env(db, [], state={"last_ts": NOW - 1000})
    e.run()
    s = e.calls[0]["sys"]
    check("what it adds to what you knew" not in s, "prior-knowledge clause dropped")
    check("Say only what the passages state; do not join unrelated passages" in s, "grounding sentence present")
    check("never about yourself" in s, "world firewall kept")


def test_note_budget_leaves_rest_pending():
    db = DB()
    for b, off in (("Alpha Book", 0), ("Beta Book", 100), ("Gamma Book", 200)):
        for i in range(5):
            reading(db, b, i, NOW - 3000 + off + i)
    e = Env(db, [], state={"last_ts": NOW - 4000})
    e.run()
    check(len(e.stored) == 2, "at most _MAX_NOTES notes per sleep")
    st = e.state()
    # Gamma is the youngest book and was not fed: the floor must stop just below its first fragment
    check(st["last_ts"] < NOW - 3000 + 200 and st["last_ts"] >= NOW - 3000 + 104, f"floor stops below the unfed book: {st}")
    e.replies = []
    e.run()
    check(len(e.stored) == 3 and any("Gamma" in c["user"] for c in e.calls), "next sleep feeds the book left pending")
    check(e.state()["last_ts"] >= NOW - 3000 + 204, "floor then moves past everything fed")


def test_watermark_is_newest_fed_not_now():
    db = DB()
    for i in range(25):
        reading(db, "Long Book", i, NOW - 2000 + i)
    e = Env(db, [], state={"last_ts": NOW - 3000})
    e.run()
    user = e.calls[0]["user"]
    n_items = user.count("\n- ")
    check(n_items == gl._READ_MAX, f"bounded sample of {gl._READ_MAX}, got {n_items}")
    st = e.state()
    check(abs(st["last_ts"] - (NOW - 2000 + 10)) < 1e-3 and st["last_ts"] < NOW - 2000 + 10, f"last_ts is just below the first unfed fragment, got {st['last_ts'] - (NOW - 2000)}")
    check(st["last_ts"] < NOW - 2000 + 10, "fragments 10..24 are NOT marked consumed")
    # the oldest ten were fed (a contiguous prefix), none of the fed ones were skipped
    check("matter0 " in user and "matter9 " in user and "matter10 " not in user, "fed the oldest contiguous prefix")


def test_study_first_and_covered_skipped():
    db = DB()
    book = "Covered Book"
    study(db, book, NOW - 900, enc="E1", text="I see that rulers must be feared")
    reading(db, book, 0, NOW - 950, enc="E1")                                   # same encounter as the study note
    db.add("reading", f"[From '{book}'] the prince must be feared and rulers see it", NOW - 940,
           vec_text="I see that rulers must be feared")  # cosine-covered
    for i in range(1, 5):
        reading(db, book, i + 10, NOW - 800 + i)
    e = Env(db, [], state={"last_ts": NOW - 2000})
    e.run()
    u = e.calls[0]["user"]
    check(u.split("\n", 1)[1].startswith("- I see that rulers must be feared"), "study note first, header stripped")
    check("[My study note" not in u, "study header stripped from the material")
    check("passage 0 of" not in u, "reading from a study note's own encounter is not fed")
    check(u.count("matter1") >= 1, "uncovered reading is fed")
    a = [x for x in e.attempts() if x.get("outcome") == "stored"][0]
    check(a["n_covered"] >= 1, f"covered count logged, {a}")


def test_all_covered_consumed_no_call():
    db = DB()
    book = "Done Book"
    study(db, book, NOW - 500, enc="E9")
    for i in range(4):
        reading(db, book, i, NOW - 600 + i, enc="E9")
    e = Env(db, [], state={"last_ts": NOW - 2000})
    out = e.run()
    check(out is None and not e.calls, "nothing to digest: no model call")
    check(e.state()["last_ts"] >= NOW - 500, "covered material is consumed so it cannot hold the floor")
    check(any(x.get("outcome") == "covered" for x in e.attempts()), "covered outcome logged")


def test_waiting_then_stale():
    db = DB()
    for i in range(2):
        reading(db, "Thin Book", i, NOW - 100 + i)
    e = Env(db, [], state={"last_ts": NOW - 1000})
    e.run()
    check(not e.calls and e.state()["last_ts"] < NOW - 100, "2 uncovered fragments wait, nothing consumed")
    db2 = DB()
    for i in range(2):
        reading(db2, "Thin Book", i, NOW - 300000 + i)      # older than _WAIT_MAX (3 d)
    e2 = Env(db2, [], state={"last_ts": NOW - 500000})
    e2.run()
    check(len(e2.calls) == 1, "a book that waited past _WAIT_MAX is fed what it has")


def test_expire_counted():
    db = DB()
    for i in range(6):
        reading(db, "Old Book", i, NOW - 6 * 86400 + i)
    e = Env(db, [], state={"last_ts": NOW - 9 * 86400})
    e.run()
    summ = [x for x in e.attempts() if x.get("sleep")]
    check(not e.calls and summ and summ[0]["expired"] == 6, f"expired fragments are counted, not silent: {summ}")
    check(e.state()["last_ts"] >= NOW - 6 * 86400 + 5, "floor moves past expired rows")


def test_rejections():
    for bad, tag in (({"understanding": "The text discusses the rise of a prince and his methods of rule in detail here."}, "summary_opening"),
                     ({"understanding": "The excerpt explores fear and love in rule, and how a ruler should act well."}, "summary_opening"),
                     ({"understanding": {"key_facts": ["a"], "grasp": "b" * 80}}, "not_prose")):
        db = DB()
        for i in range(4):
            reading(db, "The Prince", i, NOW - 500 + i)
        e = Env(db, [bad, bad], state={"last_ts": NOW - 1000})
        e.run()
        check(not e.stored, f"{tag}: refused answer is never stored")
        check(len(e.calls) == 2, f"{tag}: one immediate retry, got {len(e.calls)} calls")
        check(e.calls[1]["temp"] > e.calls[0]["temp"], "retry is a different draw")
        check(any(x.get("outcome") == "rejected:" + tag for x in e.attempts()), f"{tag}: rejection logged {e.attempts()}")
        check(e.state()["last_ts"] >= NOW - 497, f"{tag}: fed twice and refused, so consumed")
    db = DB()
    for i in range(4):
        reading(db, "The Prince", i, NOW - 500 + i)
    e = Env(db, [{"understanding": "The text discusses a prince at length and in detail, yes, indeed so."}, {"understanding": GOOD}],
            state={"last_ts": NOW - 1000})
    e.run()
    check(len(e.stored) == 1 and len(e.calls) == 2, "retry that comes back clean is stored")
    check(gl._reject_reason(GOOD) is None, "good prose accepted")
    check(gl._reject_reason("Machiavelli says that the text of the law is a tool of the ruler and the people alike.") is None,
          "'text' later in a sentence is fine")


def test_call_failure_consumes_nothing():
    db = DB()
    for b, off in (("Alpha Book", 0), ("Beta Book", 50)):
        for i in range(5):
            reading(db, b, i, NOW - 1000 + off + i)
    e = Env(db, [RuntimeError("hub down")], state={"last_ts": NOW - 2000})
    out = e.run()
    check(out is None and len(e.calls) == 1, "a failed call stops the sleep's pass (no pile of timeouts)")
    check(e.state()["last_ts"] < NOW - 1000, "nothing consumed after a failed call")
    check(any(x.get("outcome") == "call_failed" for x in e.attempts()), "call_failed logged")


def test_duplicate_of_study_note_not_stored():
    db = DB()
    book = "Dup Book"
    study(db, book, NOW - 900, enc="Z", text=GOOD)
    for i in range(4):
        reading(db, book, i, NOW - 500 + i)
    e = Env(db, [], state={"last_ts": NOW - 2000})
    e.run()
    check(not e.stored and any(x.get("outcome") == "dup_study" for x in e.attempts()), f"restated study note is refused: {e.attempts()}")


def test_n_sources_counts_what_reached_the_model():
    db = DB()
    for i in range(10):
        reading(db, "Budget Book", i, NOW - 500 + i)
    e = Env(db, [], state={"last_ts": NOW - 1000})
    e.run(_BUDGET=1000)
    a = [x for x in e.attempts() if x.get("outcome") == "stored"][0]
    u = e.calls[0]["user"].split("\n", 1)[1]
    check(a["n_sources"] == len(u.split("\n")) and a["n_sources"] < 10, f"n_sources {a['n_sources']} = items sent {len(u.split(chr(10)))}")
    lg = json.loads(e.lg.read_text(encoding="utf-8").splitlines()[0])
    check(lg["n_sources"] == a["n_sources"] and lg["topic"] == "Budget Book", "stored-note log row carries the same numbers")
    for line in u.split("\n"):
        check(line.startswith("- ") and not line.endswith(("matt", "ma")) , "no item ends mid-word")


def test_word_boundary_cut():
    s = "alpha beta gamma delta epsilon zeta eta theta"
    for n in (7, 12, 20, 33):
        c = gl._smart_cut(s, n)
        check(len(c) <= n and (c == s or s[len(c)] == " ") and c.split()[-1] in s.split(), f"cut at {n}: {c!r}")


def test_topic_recognises_study_header():
    mat = ("- [My study note: 'On fear' " + DOT + " on 'The Prince' " + DOT + " subject: rule] I see\n"
           "- [My study note: 'On luck' " + DOT + " on 'The Prince' " + DOT + " subject: fortune] I see")
    check(gl._topic(mat) == "The Prince", gl._topic(mat))
    check(gl._topic("nothing here") == "my recent reading", "fallback kept")


def test_old_state_file_and_first_run():
    db = DB()
    e = Env(db, [], state={"last_ts": 123.0})
    with mock.patch.object(gl, "_STATE", e.st):
        check(gl._load_state() == {"last_ts": 123.0, "books": {}}, "old single-key state loads")
    e2 = Env(db, [])          # no state file at all
    reading(db, "Fresh Book", 0, NOW - 100 * 86400)   # ancient
    for i in range(4):
        reading(db, "Fresh Book", i + 1, NOW - 100 + i)
    e2.run()
    check(len(e2.calls) == 1 and "matter1 " in e2.calls[0]["user"] and "passage 0 of" not in e2.calls[0]["user"],
          "no state: starts from the last day, never replays the shelf")


def test_live_paths_untouched():
    check(Path(gl._STATE).resolve().is_relative_to(ROOT), "module paths live in the worktree, tests patched them to temp")


for name, fn in list(globals().items()):
    if name.startswith("test_") and callable(fn):
        print("==", name)
        fn()
print("FAILS:", len(FAILS))
sys.exit(1 if FAILS else 0)

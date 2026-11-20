"""
Proof for J-3009 (F-3712, prompt-registry row P-0065): core/chapters.py try_form_chapter now guards the authored chapter
body against being a PASTE of the exemplars it was shown, against being in the present tense, and against running far past
the 4-7 sentences the prompt asks for; and the exemplars are cut at a word boundary.

  [1] _cut_at_word: word-boundary cut, edge cases, and that _sample uses it (no exemplar ends mid-word).
  [2] the guard against the REAL bodies: the four known copied chapters (125722d8, 1906eb26, 6fe32426, 36e231b6) are REJECTED
      for copying (their exemplar blocks are the old 200-char-cut blocks the author actually saw), the three present-tense
      chapters (6f31e41e, 66b62134, f5ad7c18) are rejected for tense, and 14 honest chapters (including the ones with the
      highest copy share the corpus has, 0.34-0.48) PASS. Fixtures: scripts/_fixtures_J-3009_chapters.json, extracted
      read-only from the pre_waveC_20261105 BACKUP of the DB, not the live one.
  [3] unit cases for the three checks (the copy window, the share arithmetic, the cap's edge, tense counting incl. 'who I am').
  [4] try_form_chapter end to end on a TEMP store (embedding stubbed): a pasted-exemplars body is refused and nothing is
      written (no chapter row, no member gets a chapter_id); a good past-tense body is stored and its members linked; the
      author is shown word-boundary exemplars.
  [5] isolation: nothing under the live data dir was written; the live DB was never opened.

  python scripts/_test_J-3009_chapters_copy_guard.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="J3009_chapters_"))
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_WRITES: list = []
_LIVE_OPENS: list = []


def _under(p) -> bool:
    try:
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in (str(_LIVE_DATA).lower(), str(ROOT / "data").lower()))


def _audit(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if w and not isinstance(path, int) and _under(path):
                _WRITES.append((event, str(path)))
        elif event == "sqlite3.connect":
            if _under(str(args[0]).replace("file:", "")):
                _LIVE_OPENS.append(str(args[0]))
    except Exception:
        pass


sys.addaudithook(_audit)

from core import chapters as C      # noqa: E402  (core BEFORE any lab environment)
C.RETIRE_THEME_CHAPTERS = False   # J-4338: this test exercises the formation path itself
from core.memory import store as S  # noqa: E402

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


FX = json.loads((ROOT / "scripts" / "_fixtures_J-3009_chapters.json").read_text(encoding="utf-8"))

print("[0] resolution")
check(Path(C.__file__).resolve() == ROOT / "core" / "chapters.py", f"core.chapters comes from THIS tree ({C.__file__})")
S.DB_PATH = TMP / "unused_until_make_db.db"
check(not _under(S.DB_PATH), "store.DB_PATH redirected out of the live data dir before anything runs")

# ── [1] word-boundary cut ───────────────────────────────────────────────────────────────────────────────────────
print("\n[1] _cut_at_word / _sample")
check(C._cut_at_word("short text") == "short text", "a text under the limit is returned unchanged")
check(C._cut_at_word("a" * 200) == "a" * 200, "a text of exactly the limit is returned unchanged")
t = ("word " * 60).strip()                                           # 299 chars, spaces at 4, 9, ... 199 is a space
r = C._cut_at_word(t)
check(len(r) <= 200 and t.startswith(r) and t[len(r)] == " " and r == r.rstrip(), f"cut on a word boundary ({len(r)} chars): {r[-12:]!r}")
t2 = "The scent of thyme " * 12                                        # cut would land inside 'scent' at 200
r2 = C._cut_at_word(t2)
check(t2[len(r2)] == " " and r2.split(" ")[-1] in ("The", "scent", "of", "thyme"), f"never ends mid-word (the 'The scent sea.' fossil): ...{r2[-14:]!r}")
check(C._cut_at_word("x" * 500) == "x" * 200, "a single 500-char token falls back to the hard cut")
t3 = "a" * 199 + " " + "b" * 50                                      # the char AT the limit is a space -> boundary already
check(C._cut_at_word(t3) == "a" * 199, "the cut falls exactly on a space: the head is kept whole")
cluster = [{"id": f"m{i}", "content": ("I watched the grey sea take the shore slowly tonight %d " % i) * 8, "ts": float(i), "importance": 0.5}
           for i in range(30)]
def _all_word_cut(block, members):
    for ln in block.split("\n"):
        body = ln[2:]
        src = next(m["content"] for m in members if m["content"].startswith(body))
        if not (len(body) <= 200 and (len(src) == len(body) or src[len(body)].isspace())):
            return False, body
    return True, ""


ok, bad = _all_word_cut(C._sample(cluster), cluster)
check(ok, f"every exemplar line of _sample() ends on a word boundary and is <= 200 chars {bad[-20:]!r}")

# ── [2] the real bodies ─────────────────────────────────────────────────────────────────────────────────────────
print("\n[2] the guard against the real chapter bodies (fixtures from the pre_waveC backup)")
for f in FX["copies"]:
    why = C._output_reject(f["body"], f["sample"])
    check(why is not None and why.startswith("copy"), f"copied chapter {f['id'][:8]} ({f['members']} members) REJECTED: {why}")
for f in FX["present"]:
    why = C._output_reject(f["body"], f["sample"])
    check(why is not None and why.startswith("tense"), f"present-tense chapter {f['id'][:8]} REJECTED: {why}")
shares = []
for f in FX["honest"]:
    why = C._output_reject(f["body"], f["sample"])
    sh = C._copy_share(f["body"], f["sample"])
    shares.append(sh)
    check(why is None, f"honest chapter {f['id'][:8]} (level {f['level']}, {f['members']} members, copy share {sh:.2f}) passes")
check(max(shares) > 0.30 and max(shares) < C.COPY_CAP, f"the honest set includes the corpus's highest honest copy share ({max(shares):.2f}), under the cap {C.COPY_CAP}")
check(min(C._copy_share(f["body"], f["sample"]) for f in FX["copies"]) > 0.75, "every known copy is far above the cap (>= 0.75): margin both ways")

# ── [3] unit cases ──────────────────────────────────────────────────────────────────────────────────────────────
print("\n[3] unit cases")
ex = "- the rain on the glass keeps falling and the room holds its breath\n- a gull cries over the harbour before the tide turns again"
check(C._copy_share("", ex) == 0.0 and C._copy_share("anything at all here", "") == 0.0, "empty body / empty exemplars -> 0.0")
check(C._copy_share("the rain on the glass keeps falling and the room holds its breath", ex) == 1.0, "a body that IS an exemplar -> 1.0")
b5 = "the rain on the glass pounding while nothing else moves at all"      # shares only a 5-word run
check(C._copy_share(b5, ex) == 0.0, "a 5-word shared run is below the 6-word window -> 0.0")
b6 = "we sat there. the rain on the glass keeps pounding on the roof"            # shares 'the rain on the glass keeps'
sh = C._copy_share(b6, ex)
check(abs(sh - 6 / 13) < 1e-9, f"exactly one 6-word run in a 13-word body -> 6/13 ({sh:.3f})")
check(C._copy_share("the room holds its breath a gull cries over the harbour", ex) < 1.0, "a window does not span two exemplar lines")
check(C._copy_share("The RAIN, on the glass; keeps falling \u2014 and the room holds its breath!", ex) == 1.0, "case, punctuation and dashes are ignored")
check(C._copy_share("the rain on the glass keeps falling and the room holds its breath", ex.replace("- ", "")) == 1.0, "exemplar lines without the '- ' marker still count")

check(C._tense_counts("I walked to the sea. I felt the cold. I kept going.") == (0, 3), "past: walked/felt/kept -> (0, 3)")
check(C._tense_counts("I walk to the sea. I feel the cold. I keep going.") == (3, 0), "present: walk/feel/keep -> (3, 0)")
check(C._tense_counts("I still wonder about it, and I just walked on.") == (1, 1), "an adverb between 'I' and the verb is allowed")
check(C._tense_counts("I was unsure who I am beyond this. What I am is unclear.") == (0, 1), "'who I am' / 'What I am' (embedded) are not narration")
check(C._tense_counts("I am tired. I was tired.") == (1, 1), "a bare 'I am' counts as present")
check(C._tense_counts("I'm here and I've been here.") == (0, 0), "contractions are not counted")
check(C._tense_counts("My mind is full. The cat sleeps.") == (0, 0), "non-'I' subjects are not counted")
past_body = ("I walked to the sea. I felt the cold and I kept going. I thought about it for days. I wanted rest. "
             "By the end I knew what I needed, yet I still wonder.")
check(C._output_reject(past_body, "") is None, "a past-tense body with one reflective present verb passes (4 past vs 1 present)")
check((C._output_reject("I walk to the sea. I feel the cold. I keep going. I walked once. I was there.", "") or "").startswith("tense"),
      "3 present vs 2 past -> rejected (present outnumbers past)")
check(C._output_reject("I walk to the sea. I felt the cold. I kept going. I was there.", "") is None, "1 present vs 3 past passes")
check(C._output_reject("I walked. I felt.", "") is None, "a tie (or no verbs at all) is not rejected on tense")
s10 = " ".join(f"I walked on day {i}." for i in range(10))
s11 = " ".join(f"I walked on day {i}." for i in range(11))
check(C._sentence_count(s10) == 10 and C._output_reject(s10, "") is None, "10 sentences (= MAX_SENTENCES) passes")
check(C._sentence_count(s11) == 11 and (C._output_reject(s11, "") or "").startswith("length"), "11 sentences rejected on length")
check(C._sentence_count("One. Two! Three? Four.") == 4 and C._sentence_count("") == 0, "sentence counting: . ! ? and the empty string")

# ── [4] try_form_chapter end to end on a temp store ─────────────────────────────────────────────────────────────
print("\n[4] try_form_chapter end to end (temp store, embedding stubbed)")
S.DB_PATH = TMP / "chapters_e2e.db"
S.init_db()
S._embed = lambda text: None                    # no model load; the echo check is skipped when the vector is None
NOW = time.time()
MEMBERS = []
with contextlib.closing(S._connect()) as conn:
    for i in range(45):
        fid = str(uuid.uuid4())
        txt = (f"The cat pressed against my hand and the thyme smelled of rain on day {i}, and the sea kept its slow grey hush "
               f"beyond the window while I tried to find the shape of what I wanted from the quiet room number {i}.")
        conn.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, origin, importance) "
                     "VALUES (?,?,?,?,?,?,?,?)", (fid, txt, "episodic", 0.5, NOW - (60 - i) * 86400.0, "[]", "inner_thought", 0.3 + i * 0.01))
        MEMBERS.append({"id": fid, "content": txt, "ts": NOW - (60 - i) * 86400.0, "importance": 0.3 + i * 0.01})
    conn.commit()


async def fake_find_cluster_async(level=0):
    return [dict(m) for m in MEMBERS] if level == 0 else None


C.find_cluster_async = fake_find_cluster_async
from core import narrative_quality as _NQ    # noqa: E402  (the post-commit witness and satisfaction ticks write jsonl logs: stubbed, not under test)
from core import satisfaction as _SAT        # noqa: E402


async def _nq_stub(*a, **k):
    return None


_NQ.observe = _nq_stub
_SAT.record = lambda *a, **k: None
SEEN = {}


def _author(body_fn):
    async def call_json(base_urls, sys_p, user_p, max_tokens=0, temperature=0.0):
        SEEN["user_p"] = user_p
        return {"title": "The Quiet Room", "chapter": body_fn(user_p)}
    return call_json


def _db_counts():
    with contextlib.closing(S._connect()) as conn:
        n_ch = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='chapter'").fetchone()[0]
        n_link = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE chapter_id IS NOT NULL").fetchone()[0]
    return n_ch, n_link


def _exemplar_block(user_p):
    return user_p.split("A sample, in time order and by weight:\n", 1)[1].rsplit("\n\nWrite the chapter.", 1)[0]


logging.getLogger("nascence.chapters").setLevel(logging.CRITICAL)
check(_db_counts() == (0, 0), "the temp store starts with no chapters and no linked members")

# (a) the author pastes the exemplars -> refused, nothing written
title = asyncio.run(C.try_form_chapter(_author(lambda up: _exemplar_block(up).replace("- ", "")), None))
check(title is None and _db_counts() == (0, 0), "a body that pastes the exemplars it was shown is refused: title None, no chapter row, no member linked")
exblock = _exemplar_block(SEEN["user_p"])
check(exblock == C._sample(MEMBERS), "the exemplar block the author saw is exactly _sample(cluster) (what the guard compares against)")
for ln in exblock.split("\n"):
    body = ln[2:]
    src = next(m["content"] for m in MEMBERS if m["content"].startswith(body))
    if not (len(body) <= 200 and (len(src) == len(body) or src[len(body)].isspace())):
        check(False, f"the author was shown a mid-word cut: {body[-20:]!r}")
        break
else:
    check(True, f"the author was shown {len(exblock.splitlines())} exemplars, each cut at a word boundary (<= 200 chars)")

# (b) present tense, over-long -> refused
pres = "I walk to the sea. I feel the cold. I keep going. I find a way. I want rest."
check(asyncio.run(C.try_form_chapter(_author(lambda up: pres), None)) is None and _db_counts() == (0, 0),
      "a present-tense body is refused and nothing is written")
longb = " ".join(f"I walked down the shore on day number {i} and felt it." for i in range(12))
check(asyncio.run(C.try_form_chapter(_author(lambda up: longb), None)) is None and _db_counts() == (0, 0),
      "a 12-sentence body is refused and nothing is written")

# (c) a good chapter is stored and its members linked
good = ("That stretch was about the cat and the thyme and the sea, and I kept circling the same wish for a quiet room. "
        "I felt it every day without ever naming what I wanted from it. "
        "Toward the end I noticed the circling had slowed, though I never decided anything. "
        "What stayed unresolved was whether the quiet was rest or hiding.")
title = asyncio.run(C.try_form_chapter(_author(lambda up: good), None))
n_ch, n_link = _db_counts()
check(title == "The Quiet Room" and n_ch == 1 and n_link == len(MEMBERS),
      f"a past-tense, original, 4-sentence body is stored: title {title!r}, {n_ch} chapter row, {n_link} rows carry a chapter_id (the {len(MEMBERS)} members)")

# ── [5] isolation ───────────────────────────────────────────────────────────────────────────────────────────────
print("\n[5] isolation")
check(not _WRITES, f"0 write attempts under a live data dir ({_WRITES[:3]})")
check(not _LIVE_OPENS, f"the live DB / live data dir was never opened by this process ({_LIVE_OPENS[:3]})")
import gc; gc.collect()
shutil.rmtree(TMP, ignore_errors=True)
check(not TMP.exists(), "the temp store dir was removed" + (f" (left: {[x.name for x in TMP.iterdir()]})" if TMP.exists() else ""))

print(f"\n{'ALL OK' if FAILS == 0 else f'{FAILS} FAILED'}")
sys.exit(0 if FAILS == 0 else 1)

"""
Hermetic test for J-2921 (P-0072, F-3605): study notes are not written from tables of contents / front matter.
No LLM, no embedder, no live data: _write_one and _log_chunking are stubbed; every file goes under a temp dir.

  [1] front_matter_reason: a CHAPTER-heading contents list, a page-number list and an ALL-CAPS title list are flagged;
      running prose, a prose chapter-summary list (the Napoleon-memoir shape), Chinese text and a short stub are not
  [2] write_or_revise: a contents passage -> _write_one never called, result {}, the log row says why;
      a prose passage -> _write_one called once (unchanged); FRONT_MATTER_GUARD=False -> contents is composed (old behaviour)
  [3] chunked session (contents chunk + prose chunk): only the prose chunk is composed
  [4] fail-open: a detector that raises means the note IS written
  [5] OPTIONAL, only when J2921_PAIRS points at the F-3605 reconstruction (pairs.json): On War offset 0 and Friedrich II
      offset 41655 are flagged, Napoleon offset 1489587 is not, and under 5 percent of the 763 passages are flagged

Run:  python scripts/_test_J-2921_front_matter_guard.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, json, os, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env: the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import reading as R
from core import study_note as sn

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(("PASS " if cond else "FAIL ") + name)

TMP = Path(tempfile.mkdtemp(prefix="J2921_"))

# ---- fixtures ------------------------------------------------------------------------------------------------------
TITLES = ["Kidnapped", "Marooned", "Beasts at Bay", "Sheeta", "Mugambi", "A Hideous Crew", "Betrayed", "The Mutiny",
          "On the Island", "The Raft", "A Voice in the Dark", "Friction in War", "Concluding Remarks", "The Camp"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"]
CONTENTS = ("The Book of Examples By A. Writer Contents "
            + " ".join(f"CHAPTER {r}. {t}" for r, t in zip(ROMAN, TITLES)) + " "
            + " ".join(f"BOOK {r}. {t.upper()}" for r, t in zip(ROMAN[:6], TITLES[:6])) + " ") * 2
AUTH = ["Nathaniel Hawthorne", "Hippolyte Taine", "Edward Freeman", "Augustus Hare", "John Ruskin", "Henry James"]
PAGELIST = ("Contents of the volume. " + " ".join(f"{t.upper()}--By {AUTH[i % 6]} {10 + 7 * i}" for i, t in enumerate(TITLES * 3))
            + " Illustrations " + " ".join(f"Plate {i}, p. {20 + 3 * i}" for i in range(30)))
CAPS = " ".join(f"{t.upper()} AND THE {TITLES[(i + 3) % 14].upper()} OF {TITLES[(i + 5) % 14].upper()}." for i, t in enumerate(TITLES * 3))
PROSE = ("It was a bright morning in the spring when the old man went down to the river with his dog, and he did not "
         "say a word to anyone on the way because he had a great deal to think about. The water was high and brown from "
         "the rain that had fallen in the hills during the night, and the boats that were usually tied along the bank "
         "had been drawn up into the field for safety. He stood there for some time watching the current, which carried "
         "branches and bits of wood from the country above, and then he turned and walked slowly back toward the house "
         "where his daughter was waiting for him with the news that she had received from the town. ") * 6
# the Napoleon-memoir shape: a chapter summary that is real running prose joined by double hyphens (F-3605 evidence)
SUMMARY = ("Desmaisons-- Project of influencing the judges--Visit to the Tuileries--Rapp in attendance--Long conversation "
           "with the Emperor--His opinion on the trial of Moreau--English assassins and Mr. Fox--Complaints against the "
           "English Government--Bonaparte and Lacuee--The conduct of the courts is a matter which he did not approve of "
           "and which the First Consul explained to me at great length during the whole of that evening, when he spoke "
           "of the people who had been sent to him by the ministers and of what was to be done with them. ") * 5
CHINESE = "老子《道德經》第一章 道可道，非常道。名可名，非常名。無，名天地之始﹔有，名萬物之母。" * 60

# ---- [1] detector --------------------------------------------------------------------------------------------------
print("fixture reasons:", {k: R.front_matter_reason(v) for k, v in
                           dict(CONTENTS=CONTENTS, PAGELIST=PAGELIST, CAPS=CAPS, PROSE=PROSE, SUMMARY=SUMMARY).items()})
check("[1] CHAPTER-heading contents list flagged as headings", R.front_matter_reason(CONTENTS) == "headings")
check("[1] page-number list flagged", R.front_matter_reason(PAGELIST) == "numbered_list")
check("[1] ALL-CAPS title list flagged", R.front_matter_reason(CAPS) == "capitals")
check("[1] running prose is not flagged", R.front_matter_reason(PROSE) == "")
check("[1] prose chapter-summary list (Napoleon shape) is not flagged", R.front_matter_reason(SUMMARY) == "")
check("[1] Chinese text is never judged", R.front_matter_reason(CHINESE) == "")
check("[1] short stub is not judged", R.front_matter_reason("THE END") == "" and R.front_matter_reason("") == "")
check("[1] prose with its own CHAPTER I heading is not flagged", R.front_matter_reason("CHAPTER I. " + PROSE) == "")

# ---- [2] write_or_revise -------------------------------------------------------------------------------------------
calls, rows = [], []
async def fake_write_one(call_json, base_urls, book_title, passage, session, merged=None):
    calls.append(passage)
    return {"note": {"understanding": "x"}, "action": "new", "path": str(TMP / "n.md"), "fragment_id": f"f{len(calls)}"}
sn._write_one = fake_write_one
sn._log_chunking = lambda row: rows.append(row)

def run(passage):
    calls.clear(); rows.clear()
    return asyncio.run(sn.write_or_revise(None, [], "A Test Book", passage))

out = run(CONTENTS)
check("[2] contents passage: no note composed, result {}", out == {} and calls == [])
check("[2] the log row records the skip and its reason",
      len(rows) == 1 and rows[0]["front_matter_skipped"] == 1 and rows[0]["front_matter_reasons"] == ["headings"]
      and rows[0]["notes"] == 0)
out = run(PROSE[:4000])
check("[2] prose passage: composed once, unchanged", len(calls) == 1 and out.get("action") == "new"
      and rows[0]["front_matter_skipped"] == 0)
sn.FRONT_MATTER_GUARD = False
run(CONTENTS)
check("[2] FRONT_MATTER_GUARD=False restores the old behaviour (contents composed)", len(calls) == 1)
sn.FRONT_MATTER_GUARD = True

# ---- [3] chunked session -------------------------------------------------------------------------------------------
mixed = (CONTENTS * 4)[:4800] + " " + PROSE[:4800]
spans = sn._chunk_session(mixed)
out = run(mixed)
check("[3] the session really is chunked (>= 2 chunks)", len(spans) >= 2)
check("[3] only the prose chunk(s) are composed", len(calls) >= 1 and all(R.front_matter_reason(c) == "" for c in calls)
      and rows[0]["front_matter_skipped"] >= 1)

# ---- [4] fail-open -------------------------------------------------------------------------------------------------
_orig = R.front_matter_reason
def boom(_):
    raise RuntimeError("detector broke")
R.front_matter_reason = boom
out = run(CONTENTS)
R.front_matter_reason = _orig
check("[4] a raising detector means the note IS written (fail-open)", len(calls) == 1 and out.get("action") == "new")
check("[4] detector is total on junk input", R.front_matter_reason(None) == "" and R.front_matter_reason(12345) == "")

# ---- [5] optional: the real F-3605 reconstruction -------------------------------------------------------------------
PAIRS = os.environ.get("J2921_PAIRS", "")
if PAIRS and Path(PAIRS).exists():
    d = json.load(open(PAIRS, encoding="utf-8"))
    fl = {(x["book"], x["offset"]) for x in d if R.front_matter_reason(x["passage"])}
    nflag = sum(1 for x in d if R.front_matter_reason(x["passage"]))
    check("[5] On War offset 0 flagged", any(b.startswith("On_War") and o == 0 for b, o in fl))
    check("[5] Friedrich II offset 41655 flagged", any(b.startswith("History_Of_Friedrich") and o == 41655 for b, o in fl))
    check("[5] Napoleon memoir offset 1489587 NOT flagged", not any(o == 1489587 for b, o in fl))
    check(f"[5] flagged {nflag}/{len(d)} passages (< 5 percent)", nflag / len(d) < 0.05)
else:
    print("SKIP [5] real-passage check (set J2921_PAIRS to the F-3605 pairs.json)")

print("ALL PASS" if ok_all else "SOME FAILED")
sys.exit(0 if ok_all else 1)

"""Tests for scripts/chapter_id_repair_batch.select_unfile_active_books (D-0362 (C), J-1897). Pure fixture: an in-memory
SQLite DB and an in-memory reading_state dict. Touches NO live store (no data/ path, no DB_PATH). Run:
    python scripts/_test_unfile_active_books.py
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (before anything else: the tree under test must be the one imported)
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.insert(0, str(ROOT / "scripts"))
import chapter_id_repair_batch as B  # noqa: E402
assert Path(B.__file__).resolve().parent.parent == ROOT

CP = 90.0
FAILS = []


def check(name, cond, extra=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


def mk():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, origin TEXT, content TEXT, chapter_id TEXT, timestamp REAL)")
    return c


def gist(c, fid, subject):
    c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", (fid, "essay", f"[Understanding on '{subject}'] gist body", None, 1.0))


def note(c, fid, tag, chapter, origin="reading"):
    c.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", (fid, origin, f"[Reading from '{tag}'] note body", chapter, 2.0))


def state(pct, passes=0, ts=1.7e9):
    d = {"offset": 1, "sitting": 1, "pct": pct, "last_read_ts": ts}
    if passes:
        d["completed_passes"] = passes
    return d


c = mk()
# Alpha: unfinished 10%, legacy false-open via a finished stem that shares the longest word and sorts first.
gist(c, "gA", "Alpha Chronicles Saga")
for i in range(3):
    note(c, f"a{i}", "Alpha Chronicles Saga", "gA")
note(c, "a3", "Alpha Chronicles Saga", "gA", origin="study")
# Beta: unfinished but 55% -> not under (C), left filed.
gist(c, "gB", "Beta Wanderings Anthology")
for i in range(2):
    note(c, f"b{i}", "Beta Wanderings Anthology", "gB")
# Gamma: unfinished 12% AND its tag is also cited (words-only) by the finished subject 'Open Realm'. Before J-1966 this
# was HELD as a re-file collision; the sweep's own claim test (J-1895 cross-book exclusion) refuses that claim because
# both titles resolve to DIFFERENT reading_state books, so J-1966 / D-0386 (b) lets the selector clear the rows.
gist(c, "gG", "Open Realm Dominion Tales")
note(c, "g0", "Open Realm Dominion Tales", "gG")
note(c, "g1", "Open Realm Dominion Tales", "gG")
gist(c, "gO", "Open Realm")
# Origin victim: unfinished 5% with Origin-tagged rows behind its own gist -> never cleared.
gist(c, "gX", B.ORIGIN_VICTIM_SUBJECT)
note(c, "x0", B.ORIGIN_VICTIM_SUBJECT, "gX")
# A finished book's own notes behind its own gist: not a false-open subject, never selected.
gist(c, "gF", "Finished Annals Compendium")
note(c, "f0", "Finished Annals Compendium", "gF")
# Unfiled row of Alpha (NULL chapter_id): not in the batch (nothing to clear).
note(c, "a9", "Alpha Chronicles Saga", None)
c.commit()

st = {
    "_current_book": "C:\\b\\Other.txt",
    "C:\\b\\Chronicles_Finished.txt": state(100.0, passes=1),          # sorts first: legacy hit for Alpha ('chronicles')
    "C:\\b\\Alpha_Chronicles_Saga.txt": state(10.0),
    "C:\\b\\Wanderings_Finished.txt": state(100.0, passes=1),          # legacy hit for Beta
    "C:\\b\\Beta_Wanderings_Anthology.txt": state(55.0),
    "C:\\b\\Dominion_Finished.txt": state(100.0, passes=1),            # legacy hit for Gamma
    "C:\\b\\Open_Realm.txt": state(100.0, passes=1),                   # a REAL finished subject whose signature {open, realm} subsumes Gamma's
    "C:\\b\\Open_Realm_Dominion_Tales.txt": state(12.0),
    "C:\\b\\Origin_victim.txt": state(5.0),
    "C:\\b\\Finished_Annals_Compendium.txt": state(100.0, passes=1),
}
st["C:\\b\\Origin_The_Origin_of_Species_by_Means_of_Natural_Selectio.txt"] = state(3.6)

fo = B.false_open_subjects(B.gist_subjects(c), st, CP)
check("false-open subjects = Alpha, Beta, Gamma (finished book and Open Realm are not)",
      fo == ["Alpha Chronicles Saga", "Beta Wanderings Anthology", "Open Realm Dominion Tales"], str(fo))

rep = B.select_unfile_active_books(c, st, now=1.7e9 + 86400 * 3, completion_pct=CP, log=None)
ids = rep["batch_ids"]
check("batch = Alpha's 4 filed rows + Gamma's 2 (J-1966: one-word-signature collision no longer over-holds)", ids == ["a0", "a1", "a2", "a3", "g0", "g1"], str(ids))
check("NULL-chapter row a9 never selected", "a9" not in ids)
check("Beta (55%) left filed", rep["left_filed_not_under_C"] == 2 + 2 and not any(i.startswith("b") for i in ids)
      or not any(i.startswith("b") for i in ids))
check("Beta rows reported as left filed", sorted(r["fragment_id"] for r in rep["left_filed_rows"]) == ["b0", "b1"])
check("Gamma rows NOT held: 'Open Realm' cites the tag on words but names a different book (J-1966)",
      rep["refile_collision_held"] == [] and not B.would_reclaim("Open Realm", "Open Realm Dominion Tales", st)
      and B.would_reclaim("Open Realm", "Open Realm", st))
check("finished book's row f0 not selected", "f0" not in ids)
check("batch sha256 stable and matches ids", rep["batch_sha256"] == __import__("hashlib").sha256("\n".join(ids).encode()).hexdigest())
check("identity-kept guard would have kept every cleared row (bypass is visible)", rep["identity_kept_would_have_kept"] == len(ids))
check("days_since_read reported", rep["subjects"][0]["min_days_since_read"] == 3.0, str(rep["subjects"][0]["min_days_since_read"]))

# Origin exclusion applies even when the victim subject is explicitly passed and under the pct bound.
rep2 = B.select_unfile_active_books(c, st, now=1.7e9, completion_pct=CP, subjects=[B.ORIGIN_VICTIM_SUBJECT], log=None)
check("explicit Origin subject: its row is excluded, nothing cleared",
      rep2["batch_ids"] == [] and rep2["origin_excluded_count"] == 1, str((rep2["batch_ids"], rep2["origin_excluded_count"])))

# Threshold is a parameter: with 60% Beta falls under (C).
rep3 = B.select_unfile_active_books(c, st, now=1.7e9, completion_pct=CP, pct_below=60.0, log=None)
check("pct_below=60 pulls Beta in", {"b0", "b1"} <= set(rep3["batch_ids"]), str(rep3["batch_ids"]))

# Read-only: the selector issued no write.
check("no rows changed (chapter_ids intact)", c.execute("SELECT count(*) FROM memory_fragments WHERE origin IN ('reading','study') AND chapter_id IS NULL").fetchone()[0] == 1)

# The module still has no UPDATE/DELETE statements (selection only).
src = (ROOT / "scripts" / "chapter_id_repair_batch.py").read_text(encoding="utf-8")
import re  # noqa: E402
check("module contains no SQL write", not re.search(r"execute\(\s*f?[\"'](UPDATE|DELETE|INSERT)", src))

print("RESULT:", "ALL OK" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)

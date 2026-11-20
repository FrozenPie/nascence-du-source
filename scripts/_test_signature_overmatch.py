"""
Hermetic test + full-corpus regression: the one-word-signature over-match (J-1966 / D-0386 (b) / F-2530).

The finished book 'The Mad King' has signature {king}; the 104 'King Arthur and the Knights of the Round Table'
reading/study rows cite {king} on words alone. J-1895 / D-0359 (shape 3) already made file_book_notes() refuse such a
claim (`_tag_names_other_book`), but the D-0362 (C) selector's re-file collision guard still used the words-only test
and held the 104 out. This job makes the guard use the sweep's real claim test (`would_reclaim`).

  [1] fixtures: Mad King (finished, {king}) vs a King Arthur tag (unfinished, longer title): words-only cites -> True,
      would_reclaim -> False; a SAME-book tag is still reclaimed; a tag that resolves to no book keeps the old
      (words-only) behaviour (documented residual); the real sweep path (_file_book_notes on a temp DB) leaves the
      King Arthur rows NULL and files the Mad King's own rows.
  [2] FULL-CORPUS REGRESSION (live DB mode=ro, live reading_state.json READ-ONLY; skipped if absent): every distinct
      reading/study tag x every open-gate gist subject: pairs where words-only claims but the real claim does not
      (printed), asserts the real claim is a SUBSET of the words-only claim (nothing newly claims), the King Arthur
      pair is among the changed ones, and NO OTHER book newly claims any row.
  [3] selector: select_unfile_active_books on the live snapshot clears King Arthur's 104 (collision hold 104 -> 0),
      and after the clear no open-gate subject would reclaim ANY cleared row.
  [4] canary: live reading_state / DB / log untouched.

  python scripts/_test_signature_overmatch.py     # exit 0 = ALL OK; run FROM a worktree, never C:/Nascence
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, int(st.st_mtime_ns))


_LIVE_STATE = Path(r"C:\Nascence\data\reading_state.json")
_LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
_LIVE = [_LIVE_STATE, _LIVE_DB, Path(str(_LIVE_DB) + "-wal"), Path(r"C:\Nascence\data\world_consolidation_log.jsonl")]
_before = {p: _snap(p) for p in _LIVE}

import core                                                   # noqa: E402  (BEFORE anything else -- F-2423)
check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")
import core.world_consolidation as W                          # noqa: E402
from core.essay_lesson import _cites_this_book                # noqa: E402
import chapter_id_repair_batch as B                           # noqa: E402
check(Path(W.__file__).resolve().is_relative_to(ROOT), "world_consolidation is the worktree copy")

KA = "King Arthur and the Knights of the Round Table"
MK = "The Mad King"
ST = {
    "C:\\x\\books\\The_Mad_King.txt": {"pct": 100.0, "completed_passes": 1},
    "C:\\x\\books\\King_Arthur_and_the_Knights_of_the_Round_Table.txt": {"pct": 34.9},
    "C:\\x\\books\\Self-Control_Its_Kingship_and_Majesty.txt": {"pct": 79.7},
}

print("[1] fixtures")
check(_cites_this_book(MK[:50], KA), "words-only: 'The Mad King' {king} cites the King Arthur tag (the over-match)")
check(not B.would_reclaim(MK, KA, ST), "would_reclaim: the Mad King does NOT reclaim the King Arthur tag (different books)")
check(B.would_reclaim(MK, "The Mad King", ST), "would_reclaim: the Mad King still reclaims its OWN tag")
check(B.would_reclaim(KA, KA, ST), "would_reclaim: King Arthur reclaims its own tag")
check(not B.would_reclaim(MK, "Self-Control Its Kingship and Majesty", ST), "a second longer-title book (Kingship) not reclaimed by {king}... ")
# residual (disclosed): a tag that resolves to NO reading_state book keeps the words-only behaviour
check(B.would_reclaim(MK, "King Arthur and the Knights of the Round Table", {k: v for k, v in ST.items() if "Arthur" not in k}),
      "residual: a tag naming a book absent from reading_state is still reclaimed by {king} (unchanged conservative default)")

# the real sweep path on a temp DB: store.DB_PATH and reading STATE redirected into a temp dir
TMP = Path(tempfile.mkdtemp(prefix="j1966_"))
try:
    import core.reading as R
    import core.memory.store as S
    R.STATE = TMP / "reading_state.json"
    R.STATE.write_text(json.dumps(ST), encoding="utf-8")
    S.DB_PATH = TMP / "nascence.db"
    W._LOG = TMP / "wc_log.jsonl"
    check(Path(S.DB_PATH).resolve().is_relative_to(TMP), "temp DB redirected (no live write possible)")
    cn = sqlite3.connect(str(S.DB_PATH))
    cn.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, origin TEXT, content TEXT, chapter_id TEXT, timestamp REAL)")
    rows = [("g_mk", "essay", "[essay on 'The Mad King'] gist", None, 1.0),
            ("r_mk1", "reading", "[reading on 'The Mad King'] a", None, 2.0),
            ("r_ka1", "reading", "[reading on 'King Arthur and the Knights of the Round Table'] b", None, 3.0),
            ("r_ka2", "study", "[study session on 'King Arthur and the Knights of the Round Table'] c", None, 4.0)]
    cn.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", rows)
    cn.commit(); cn.close()
    s = W._file_book_notes(MK)
    cn = sqlite3.connect(str(S.DB_PATH))
    got = dict(cn.execute("SELECT fragment_id, chapter_id FROM memory_fragments").fetchall()); cn.close()
    print("   sweep summary:", {k: s.get(k) for k in ("candidates", "filed", "excluded_other_book", "reason")})
    check(got["r_mk1"] == "g_mk", "real sweep path: the Mad King files its OWN row")
    check(got["r_ka1"] is None and got["r_ka2"] is None, "real sweep path: the King Arthur rows stay NULL (not claimed by {king})")
    check(s.get("excluded_other_book") == 2, "excluded_other_book == 2")
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print("[2]/[3] full-corpus regression (live files read-only)")
if not (_LIVE_STATE.exists() and _LIVE_DB.exists()):
    print("   live files absent -- skipped")
else:
    # a byte copy of reading_state (module global STATE points at the worktree's non-existent data/ on purpose)
    st = json.loads(_LIVE_STATE.read_text(encoding="utf-8"))
    conn = sqlite3.connect("file:%s?mode=ro" % _LIVE_DB.as_posix(), uri=True)
    conn.row_factory = sqlite3.Row
    gist_subjects = sorted(B.gist_subjects(conn))
    CP = 97.0
    open_subj = sorted(x for x in gist_subjects if B.head_gate_passes(x, st, CP) >= 1)
    print(f"   gist subjects {len(gist_subjects)}, open-gate {len(open_subj)}")
    tags = {}
    for r in conn.execute("SELECT content, chapter_id FROM memory_fragments WHERE origin IN ('reading','study')"):
        t = W._tag_of(r["content"])
        if t:
            d = tags.setdefault(t, [0, 0])
            d[0] += 1
            d[1] += 1 if r["chapter_id"] is None else 0
    print(f"   distinct reading/study tags {len(tags)}")
    old, new = set(), set()
    for t in tags:
        for sub in open_subj:
            if _cites_this_book(sub[:50], t):
                old.add((sub, t))
                if not W._tag_names_other_book(sub, t, st):
                    new.add((sub, t))
    changed = sorted(old - new)
    check(new <= old, "nothing newly claims: real-claim pairs are a subset of the words-only pairs")
    print(f"   words-only pairs {len(old)}, real-claim pairs {len(new)}, changed (dropped) {len(changed)}")
    for sub, t in changed:
        print(f"     DROPPED  subject={sub[:46]!r}  tag={t[:56]!r}  rows={tags[t][0]} (null={tags[t][1]})")
    check((MK, KA) in changed, "the Mad King x King Arthur pair is among the dropped pairs")
    newly = new - old
    check(not newly, "NO other book newly claims rows (empty)")
    # the dropped pairs must all be genuine cross-book (both sides resolve to different books)
    bad = [(a, b) for a, b in changed
           if W._book_identity_for(a, st)["status"] == "none" or W._book_identity_for(b, st)["status"] == "none"]
    check(not bad, "every dropped pair has both sides resolving to a reading_state book (no guess)")

    # 2026-10-08 ~17:55 Du finished King Arthur (reading_state: rereads 1, pct reset to 0.0), so on the LIVE state the
    # book is finished and its 104 rows are legitimately behind their own gist -- the selector must NOT clear them.
    ka_key = [k for k in st if "King_Arthur_and_the_Knights" in k]
    live_rep = B.select_unfile_active_books(conn, st, completion_pct=CP, log=None)
    live_ka = [r for r in live_rep["batch"] if r["tag"] == KA]
    ka_live_entry = st.get(ka_key[0]) if ka_key else None
    print(f"   live KA entry: {ka_live_entry}; live selector batch {live_rep['batch_size']} (KA rows {len(live_ka)})")
    if ka_live_entry and W._passes_of(ka_live_entry, CP) >= 1:
        check(len(live_ka) == 0, "live state: King Arthur is FINISHED (a pass completed) -> its 104 rows are not cleared")
    # scenario state = the F-2530 snapshot (King Arthur unfinished at 34.9 pct): the over-match fix must let the 104 clear
    st2 = json.loads(json.dumps(st))
    if ka_key:
        st2[ka_key[0]] = {"offset": 0, "sitting": 32, "pct": 34.9, "last_read_ts": 1791400000.0}
    rep = B.select_unfile_active_books(conn, st2, completion_pct=CP, log=None)
    ka_batch = [r for r in rep["batch"] if r["tag"] == KA]
    print(f"   selector (scenario KA 34.9 pct): batch {rep['batch_size']} sha {rep['batch_sha256'][:16]} held {rep['refile_collision_held_count']}")
    check(len(ka_batch) == 104, f"scenario: selector clears the King Arthur 104 (got {len(ka_batch)})")
    check(rep["refile_collision_held_count"] == 0, "re-file collision hold is empty")
    check(rep["batch_size"] == 381, f"scenario batch is the full ruled (C) set of 381 (got {rep['batch_size']})")
    check(live_rep["batch_size"] == 277 and live_rep["refile_collision_held_count"] == 0,
          "live-state batch is the 277 apply-ready set, nothing held")
    reclaimers = {}
    for r in rep["batch"]:
        for sub in open_subj:
            if sub != r["subject"] and B.would_reclaim(sub, r["tag"], st2):
                reclaimers.setdefault(r["fragment_id"], []).append(sub)
    check(not reclaimers, "after the clear NO open-gate subject would reclaim any of the cleared rows")
    # the 277 apply-ready subset is unchanged
    non_ka = sorted(r["fragment_id"] for r in rep["batch"] if r["tag"] != KA)
    import hashlib
    h = hashlib.sha256("\n".join(non_ka).encode("utf-8")).hexdigest()
    print("   non-KA subset", len(non_ka), h)
    conn.close()

print("[4] canary")
for p in _LIVE:
    check(_snap(p) == _before[p], f"live file unchanged: {p.name}")

print("RESULT:", "ALL OK" if FAILS == 0 else f"{FAILS} FAIL")
sys.exit(1 if FAILS else 0)

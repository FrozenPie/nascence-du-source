"""scripts/test_sleep_single_pass_unit.py (J-1922 / F-2549): offline unit + fuzz proof that core/like_scan.py and the three
single-pass sweeps (book_residue._ReadingGroups/_SelfRows, stick_test._term_counts_single_pass, world_consolidation._NoteCache)
return EXACTLY what the per-term SQL they replace returns, on in-memory SQLite databases only (never touches data/).

Run: python scripts/test_sleep_single_pass_unit.py   (from the tree under test; asserts core/ resolves inside it)
Exit 0 + 'PASS' on success. SQLite itself is the oracle for every comparison (the same LIKE the old code ran)."""
import os
import pathlib
import random
import sqlite3
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402  (import core BEFORE anything else; assert it is the tree under test)
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__
from core import like_scan, book_residue, stick_test, world_consolidation  # noqa: E402
for _m in (like_scan, book_residue, stick_test, world_consolidation):
    assert str(pathlib.Path(_m.__file__).resolve()).lower().startswith(str(HERE).lower()), _m.__file__

random.seed(20261007)
SELF = ("inner_thought", "subconscious_synthesis", "dream", "mirror")
ALPHA = list("abcAB Kk-'[]") + ["K", "İ", "é", "É", "道", "\n", "x", "X", "1", "%", "_", "\x00", "]"]
failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("FAIL:", msg)


def new_db():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, timestamp REAL NOT NULL, "
              "origin TEXT NOT NULL DEFAULT 'lived', chapter_id TEXT, emotion_embedding BLOB)")
    c.execute("CREATE INDEX idx_timestamp ON memory_fragments(timestamp DESC)")
    c.execute("CREATE INDEX idx_origin ON memory_fragments(origin)")
    c.execute("CREATE INDEX idx_chapter ON memory_fragments(chapter_id)")
    return c


def rnd_text(n):
    return "".join(random.choice(ALPHA) for _ in range(random.randint(0, n)))


# ---------------------------------------------------------------- 1. LikeIndex vs SQLite LIKE (fuzz)
def test_like_index():
    c = new_db()
    contents = [rnd_text(40) for _ in range(400)] + [None, "", "Kelvin K sign", "xx\x00hidden", "Hidden after nul \x00 abc"]
    c.execute("DROP TABLE memory_fragments")
    c.execute("CREATE TABLE memory_fragments (content TEXT)")
    c.executemany("INSERT INTO memory_fragments VALUES (?)", [(s,) for s in contents])
    idx = like_scan.LikeIndex(contents)
    n_checked = n_hit = 0
    needles = set()
    for s in contents:
        if s and len(s) > 2:
            a = random.randint(0, len(s) - 1)
            needles.add(s[a:a + random.randint(1, 4)])
    needles |= {"k", "K", "K", "i", "İ", "é", "É", "hidden", "after", "abc", "x", "ab", "bA", "[", "'", "]"}
    for nd in sorted(needles):
        if not like_scan.is_plain_needle(nd):
            continue
        want = [r[0] for r in c.execute("SELECT rowid FROM memory_fragments WHERE content LIKE ?", (f"%{nd}%",))]
        want = [w - 1 for w in want]
        got = list(idx.iter_matches(nd))
        n_checked += 1
        n_hit += bool(want)
        check(got == want, f"LikeIndex needle {nd!r}: sql {want[:8]} vs {got[:8]}")
        for stop in (0, 1, 7, len(contents) // 2, len(contents), len(contents) + 5):
            gs = list(idx.iter_matches(nd, stop))
            check(gs == [w for w in want if w < stop], f"stop_row {stop} needle {nd!r}")
        for i in random.sample(range(len(contents)), 12):
            check(idx.row_has(i, nd) == (i in set(want)), f"row_has {i} {nd!r}")
    check(n_hit > 20, "fuzz produced too few hits to mean anything")
    print(f"like_index: {n_checked} needles vs SQLite LIKE, {n_hit} with hits")
    # the facts the module docstring claims about SQLite itself
    q = lambda p, t: c.execute("SELECT ? LIKE ?", (t, p)).fetchone()[0]
    check(q("%k%", "K") == 0, "SQLite LIKE must NOT fold the Kelvin sign")
    check(q("%I%", "i") == 1 and q("%é%", "É") == 0, "ASCII-only folding")
    check(q("%abc%", "xx\x00abc") == 0, "SQLite LIKE sees text only up to the first NUL")
    for bad in ("", "a%b", "a_b", "a\x00b", None, 5):
        check(not like_scan.is_plain_needle(bad), f"is_plain_needle({bad!r})")
    try:
        like_scan.sql_text(b"bytes")
        check(False, "sql_text must refuse BLOBs")
    except like_scan.Unsupported:
        pass


# ---------------------------------------------------------------- 2. book_residue._ReadingGroups vs the old SQL
def test_reading_groups():
    c = new_db()
    titles = ["Alpha Book", "alpha book", "Beta", "Les Misérables", "LES MISÉRABLES", "Under_Score", "Per%cent", "Gamma", "Delta"]
    rows = []
    k = 0
    for t in titles:
        for j in range(random.randint(1, 3) if t != "Gamma" else 150):    # Gamma > 120 rows: the LIMIT 120 cap
            variant = random.choice([t, t.upper(), t.lower()]) if t not in ("Les Misérables", "LES MISÉRABLES") else t
            k += 1
            rows.append((f"r{k:06d}", f"[From '{variant}'] chunk {k} Alpha beta {random.choice(['Kepler', 'wu-wei', 'stump', 'tump'])} body.", "reading"))
    rows += [("x1", "[From 'Alpha Book' no closing bracket but LIKE matches", "reading"),
             ("x2", "[From 'Alpha Book", "reading"), ("x3", "[FROM 'ALPHA BOOK'] shouting", "reading"),
             ("x4", "[From 'Beta\x00'] nul inside the title region", "reading"), ("x5", "[From 'Beta'\x00] nul after", "reading"),
             ("x6", "plain text", "reading"), ("x7", None, "reading"), ("x8", "[From 'Alpha Book'] on another origin", "study")]
    c.executemany("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin) VALUES (?,?,0,?)", [(a, b, o) for a, b, o in rows])
    spans = {t: (0.0, 0.0, 1) for t in titles}
    keep = {t: spans[t] for t in titles[::2]}
    g = book_residue._ReadingGroups(c, spans, keep)
    n_cmp = 0
    for t in titles:
        sql_rows = [r["content"] for r in c.execute("SELECT content FROM memory_fragments WHERE origin='reading' AND content LIKE ?", (f"[From '{t}'%",))]
        sql_seen = set()
        for r in c.execute("SELECT content FROM memory_fragments WHERE origin='reading' AND content LIKE ? LIMIT 120", (f"[From '{t}'%",)):
            sql_seen.update(book_residue._tokens((r["content"] or "").split("]", 1)[-1]))
        seen = g.seen_for(t)
        if "%" in t or "_" in t:
            check(seen is None and g.rows_for(t) is None, f"wildcard title {t!r} must refuse")
            continue
        n_cmp += 1
        check(seen == sql_seen, f"doc-freq tokens for {t!r}")
        got_rows = g.rows_for(t)
        if like_scan.ascii_lower(t) in {like_scan.ascii_lower(k) for k in keep}:     # ASCII-case twins share one group (as LIKE does)
            check(got_rows == sql_rows, f"all rows for kept title {t!r}: sql {len(sql_rows)} vs {None if got_rows is None else len(got_rows)}")
        else:
            check(got_rows is None, f"non-kept title {t!r} must have no rows")
    check(len(g.seen_for("Gamma")) > 0, "Gamma tokens present")
    # and _signatures with rows= is the same as _signatures querying
    for t in ("Alpha Book", "Beta"):
        df = {"kepler": 1}
        a = book_residue._signatures(c, t, df, 9, set())
        b = book_residue._signatures(c, t, df, 9, set(), rows=[r["content"] for r in c.execute(
            "SELECT content FROM memory_fragments WHERE origin='reading' AND content LIKE ?", (f"[From '{t}'%",))])
        check(a == b, f"_signatures rows= {t!r}")
    print(f"reading_groups: {n_cmp} titles compared against the LIKE queries")


# ---------------------------------------------------------------- 3. book_residue._SelfRows vs the old per-term statement
def test_self_rows():
    c = new_db()
    words = ["kepler", "galileo", "wu-wei", "tump", "stump", "black-bear", "zzzz"]
    ts_pool = [float(x) for x in range(1, 25)]
    rows = []
    for i in range(1500):
        o = random.choice(SELF + ("reading", "lived", "essay"))
        t = " ".join(random.choice(words + ["the", "of", "Kepler", "KEPLER", "Wu-Wei"]) for _ in range(random.randint(0, 6)))
        rows.append((f"f{random.random():.10f}-{i}", t if random.random() > .02 else None, random.choice(ts_pool), o))
    c.executemany("INSERT INTO memory_fragments (fragment_id, content, timestamp, origin) VALUES (?,?,?,?)", rows)
    sr = book_residue._SelfRows(c)
    ph = ",".join("?" * len(SELF))
    n = ties = 0
    for term in words + ["kep", "g", "bear"]:
        for thr in (0.0, 3.0, 11.5, 24.0, 99.0):
            sql = [(r["origin"], r["content"], r["timestamp"]) for r in c.execute(
                f"SELECT origin, content, timestamp FROM memory_fragments WHERE origin IN ({ph}) AND timestamp > ? "
                "AND content LIKE ? ORDER BY timestamp DESC LIMIT 6", (*SELF, thr, f"%{term}%"))]
            got = sr.top(term, thr)
            n += 1
            ties += len({r[2] for r in sql}) < len(sql)
            check(got == sql, f"_SelfRows.top({term!r}, {thr}): {sql[:3]} vs {got[:3]}")
    check(sr.top("a%b", 1.0) is None and sr.top("a_b", 1.0) is None, "wildcard term must refuse")
    check(ties > 10, "tie coverage too low")
    print(f"self_rows: {n} (term, thr) statements identical, {ties} with timestamp ties")


# ---------------------------------------------------------------- 4. stick_test._term_counts_single_pass vs the old COUNT scans
def test_stick_counts():
    c = new_db()
    rows = []
    for i in range(1200):
        rows.append((f"s{i}", rnd_text(60) + random.choice(["", "The CAT sat", "the sea", "Heavyweight"]), float(i), "lived",
                     None, random.choice([None, b"emb"])))
    rows.append(("sn", None, 0.0, "lived", None, None))
    c.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?)", rows)
    roster = [{"name": "a", "terms": ["the cat", "The Sea", "heavyweight", "the cat"]},
              {"name": "b", "terms": ["x", "a%b", "caT", "K", "_"]}]
    single = stick_test._term_counts_single_pass(c, roster)
    check(single is not None, "single-pass counts returned None")
    for obj in roster:
        for t in obj["terms"]:
            r = c.execute("SELECT COUNT(*) n, SUM(CASE WHEN emotion_embedding IS NOT NULL THEN 1 ELSE 0 END) f "
                          "FROM memory_fragments WHERE content LIKE ? COLLATE NOCASE", (f"%{t}%",)).fetchone()
            want = (r["n"] or 0, r["f"] or 0)
            if f"{t}" in single:
                check(single[f"{t}"] == want, f"stick count {t!r}: sql {want} vs {single[f'{t}']}")
            else:
                check(("%" in t or "_" in t), f"plain term {t!r} missing from single-pass result")
    check(all(like_scan.is_plain_needle(k) for k in single), "wildcard term leaked into single-pass counts")
    like_scan.SWEEPS_SINGLE_PASS = False
    try:
        check(stick_test._term_counts_single_pass(c, roster) is None, "kill switch must return None")
    finally:
        like_scan.SWEEPS_SINGLE_PASS = True
    print(f"stick_counts: {len(single)} plain terms identical to the COUNT(*) LIKE scans")


# ---------------------------------------------------------------- 5. world_consolidation._NoteCache vs the old candidate SELECT
def test_note_cache():
    c = new_db()
    words_pool = ["kepler", "galileo", "origin", "species", "fables", "short", "stories", "café"]
    rows = []
    for i in range(1500):
        o = random.choice(["reading", "study", "essay", "lived"])
        txt = " ".join(random.choice(words_pool + ["Kepler", "FABLES", "the"]) for _ in range(random.randint(0, 8)))
        rows.append((f"w{i:05d}", txt, float(i), o, random.choice([None, None, "gistX", ""]), None))
    c.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?)", rows)
    cache = world_consolidation._NoteCache(c)

    def sql_set(words):
        return {r["fragment_id"] for r in c.execute(
            "SELECT fragment_id FROM memory_fragments WHERE origin IN ('reading','study') AND "
            + " AND ".join(["content LIKE ?"] * len(words)) + " AND chapter_id IS NULL", tuple(f"%{w}%" for w in words))}

    n = 0
    for words in (["kepler"], ["kepler", "galileo"], ["origin", "species", "fables"], ["short", "stories"], ["café"], ["zzz"], ["the"]):
        got = cache.candidates(c, words)
        check(got is not None and {r["fragment_id"] for r in got} == sql_set(words), f"_NoteCache words {words}")
        check(got is not None and all(set(r) == {"fragment_id", "content"} for r in got), "row shape")
        n += 1
    check(cache.candidates(c, ["a%b"]) is None and cache.candidates(c, ["a_b"]) is None and cache.candidates(c, [""]) is None
          and cache.candidates(c, []) is None, "non-plain words must refuse (caller runs the SQL)")
    # a writer filed some rows AFTER the snapshot (another thread / the previous subject): they must drop out
    base = cache.candidates(c, ["kepler"])
    victims = [r["fragment_id"] for r in base[:5]]
    c.executemany("UPDATE memory_fragments SET chapter_id='otherGist' WHERE fragment_id=?", [(v,) for v in victims])
    after = {r["fragment_id"] for r in cache.candidates(c, ["kepler"])}
    check(after == sql_set(["kepler"]) and not (after & set(victims)), "rows filed after the snapshot must be dropped (live re-check)")
    cache.mark_filed(victims[:2] + ["no-such-id"])
    check(not ({r["fragment_id"] for r in cache.candidates(c, ["kepler"])} & set(victims)), "mark_filed")
    like_scan.SWEEPS_SINGLE_PASS = False
    try:
        check(cache.candidates(c, ["kepler"]) is None, "kill switch must refuse")
    finally:
        like_scan.SWEEPS_SINGLE_PASS = True
    # _cites_words must produce exactly the words _cites_clause builds its SQL from
    for title in ("The Origin of Species by Means of Natural Selection", "Fables", "My Short Story Book", "the", "", "A B C D", "Café Society 1911"):
        w = world_consolidation._cites_words(title)
        clause, params = world_consolidation._cites_clause(title)
        check(tuple(f"%{x}%" for x in w) == params and clause == " AND ".join(["content LIKE ?"] * len(w)), f"_cites_words vs _cites_clause {title!r}")
    print(f"note_cache: {n} word sets identical to the candidate SELECT, live re-check + refusals ok")


def test_negative_control():
    """The fuzz must be able to FAIL: with Python's str.lower() in place of the ASCII-only fold (the obvious wrong
    implementation) the Kelvin-sign row matches 'k' although SQLite's LIKE says it does not."""
    c = new_db()
    c.execute("DROP TABLE memory_fragments")
    c.execute("CREATE TABLE memory_fragments (content TEXT)")
    c.execute("INSERT INTO memory_fragments VALUES (?)", ("K",))
    sql = [r[0] for r in c.execute("SELECT rowid FROM memory_fragments WHERE content LIKE '%k%'")]
    good = list(like_scan.LikeIndex(["K"]).iter_matches("k"))
    real = like_scan.ascii_lower
    like_scan.ascii_lower = str.lower
    try:
        bad = list(like_scan.LikeIndex(["K"]).iter_matches("k"))
    finally:
        like_scan.ascii_lower = real
    check(sql == [] and good == [] and bad == [0], f"negative control: sql {sql} good {good} str.lower-variant {bad}")
    print("negative_control: str.lower() variant is caught (matches the Kelvin sign), ascii_lower is not")


for fn in (test_negative_control, test_like_index, test_reading_groups, test_self_rows, test_stick_counts, test_note_cache):
    try:
        fn()
    except Exception as exc:                       # a crash is a failure, not a pass
        import traceback
        traceback.print_exc()
        failures.append(f"{fn.__name__} raised {exc!r}")
print("PASS" if not failures else f"FAILED ({len(failures)})")
sys.exit(1 if failures else 0)

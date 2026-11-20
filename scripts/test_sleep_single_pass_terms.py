"""scripts/test_sleep_single_pass_terms.py (J-1922 / F-2549): STATEMENT-LEVEL proof, on a full-fidelity COPY of the real database,
that every single-pass answer equals the old per-statement SQL answer it replaces -- not just the end-of-sweep outputs
(scripts/test_sleep_single_pass_equivalence.py) but each of the ~850 book_residue term scans, each doc-frequency scan, each
per-book read, each stick_test COUNT and each world_consolidation candidate SELECT, run side by side on the same snapshot.

Read-only: opens TERMS_DB (env; a scratch COPY under LAGH_SCRATCH) with sqlite3 mode=ro. Runs inside scripts/lag_harness' prelude
(no write under live C:\\Nascence, no subprocess); never imports nodes/*; asserts core/ resolves inside LAGH_WT. Exit 0 = all equal.

env: LAGH_SCRATCH, LAGH_WT (the tree under test, under LAGH_SCRATCH), TERMS_DB (path to the DB copy)
For the world_consolidation part the copy should have loose (NULL chapter_id) reading/study rows: the caller NULLs them first
(see the test log), otherwise every candidate set is empty and proves little."""
import sys, os, re, time, json, pathlib, sqlite3, collections

SP = pathlib.Path(os.environ["LAGH_SCRATCH"]); WT = SP / os.environ["LAGH_WT"]
sys.path.insert(0, str(WT / "scripts" / "lag_harness"))
import _prelude as P            # noqa: E402
import core                     # noqa: E402
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
from core import like_scan, book_residue, stick_test, world_consolidation  # noqa: E402
DB = pathlib.Path(os.environ["TERMS_DB"]).resolve()
assert str(DB).lower().startswith(str(SP).lower()), "TERMS_DB must be a scratch copy"
assert like_scan.SWEEPS_SINGLE_PASS is True

conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
failures = []
def check(cond, msg):
    if not cond:
        failures.append(msg); print("FAIL:", msg, flush=True)
now = 1791400000.0
t0 = time.perf_counter()

# ---- book_residue: doc-frequency scans, per-book reads, signatures, per-term scans -----------------------------------------
spans = book_residue._book_spans(conn)
stale = {t: s for t, s in spans.items() if (now - s[1]) > book_residue.STALE_DAYS * 86400 and s[2] >= book_residue.MIN_FRAGS}
groups = book_residue._ReadingGroups(conn, spans, stale)
selfrows = book_residue._SelfRows(conn)
n_ties = 0
df_sql = collections.Counter(); df_fast = collections.Counter()
for t in spans:
    seen = set()
    for r in conn.execute("SELECT content FROM memory_fragments WHERE origin='reading' AND content LIKE ? LIMIT 120", (f"[From '{t}'%",)):
        seen.update(book_residue._tokens((r["content"] or "").split("]", 1)[-1]))
    df_sql.update(seen)
    fast = groups.seen_for(t)
    check(fast is not None and fast == seen, f"doc-freq tokens differ for title {t[:50]!r}")
    df_fast.update(fast or set())
check(df_sql == df_fast, "doc_freq Counter differs")
print(f"doc-frequency: {len(spans)} titles identical ({sum(df_sql.values())} token counts)", flush=True)

n_terms = n_hits = n_books = n_rowsets = 0
for title, (lo, hi, n) in sorted(stale.items(), key=lambda kv: kv[1][1]):
    sql_rows = [r["content"] for r in conn.execute("SELECT content FROM memory_fragments WHERE origin='reading' AND content LIKE ?", (f"[From '{title}'%",))]
    fast_rows = groups.rows_for(title)
    check(fast_rows == sql_rows, f"per-book reading rows differ for {title[:50]!r}: {len(sql_rows)} vs {None if fast_rows is None else len(fast_rows)}")
    n_rowsets += 1
    a = book_residue._signatures(conn, title, df_sql, len(spans), set())
    b = book_residue._signatures(conn, title, df_sql, len(spans), set(), rows=fast_rows)
    check(a == b, f"_signatures differ for {title[:50]!r}")
    n_books += 1
    ph = ",".join("?" * len(book_residue.SELF_ORIGINS))
    for term in a:
        thr = hi + book_residue.LAG_DAYS * 86400
        sql = [(r["origin"], r["content"], r["timestamp"]) for r in conn.execute(
            f"SELECT origin, content, timestamp FROM memory_fragments WHERE origin IN ({ph}) AND timestamp > ? AND content LIKE ? "
            "ORDER BY timestamp DESC LIMIT 6", (*book_residue.SELF_ORIGINS, thr, f"%{term}%"))]
        got = selfrows.top(term, thr)
        n_terms += 1; n_hits += len(sql); n_ties += len({x[2] for x in sql}) < len(sql)
        check(got == sql, f"term scan differs: book {title[:40]!r} term {term!r}: sql {len(sql)} rows vs {None if got is None else len(got)}")
print(f"book_residue: {n_books} stale books, {n_rowsets} per-book row sets, {n_terms} term scans identical ({n_hits} rows, {n_ties} with timestamp ties) "
      f"{time.perf_counter() - t0:.0f}s", flush=True)

# ---- stick_test: every roster term -----------------------------------------------------------------------------------------
roster = stick_test.build_roster()
single = stick_test._term_counts_single_pass(conn, roster)
check(single is not None, "stick_test single-pass returned None")
n = 0
for obj in roster:
    for t in obj["terms"]:
        r = conn.execute("SELECT COUNT(*) n, SUM(CASE WHEN emotion_embedding IS NOT NULL THEN 1 ELSE 0 END) f "
                         "FROM memory_fragments WHERE content LIKE ? COLLATE NOCASE", (f"%{t}%",)).fetchone()
        want = (r["n"] or 0, r["f"] or 0)
        check(single is not None and single.get(f"{t}") == want, f"stick_test term {t!r}: sql {want} vs {None if single is None else single.get(f'{t}')}")
        n += 1
print(f"stick_test: {n} roster terms ({len(set(f'{t}' for o in roster for t in o['terms']))} distinct) identical {time.perf_counter() - t0:.0f}s", flush=True)

# ---- world_consolidation: every gist subject's candidate SELECT ------------------------------------------------------------
subjects = set()
for r in conn.execute("SELECT content FROM memory_fragments WHERE origin IN ('essay','understanding')"):
    m = re.search(r"(?:on|from) '([^']+)'", r["content"] or "")
    if m:
        subjects.add(m.group(1).strip())
cache = world_consolidation._NoteCache(conn)
n_subj = n_rows = n_nonempty = 0
for subj in world_consolidation._order_subjects(subjects):
    clause, params = world_consolidation._cites_clause(subj)
    sql = {r["fragment_id"]: r["content"] for r in conn.execute(
        f"SELECT fragment_id, content FROM memory_fragments WHERE origin IN ('reading','study') AND {clause} AND chapter_id IS NULL", params)}
    got = cache.candidates(conn, world_consolidation._cites_words(subj))
    ok = got is not None and {r["fragment_id"]: r["content"] for r in got} == sql
    check(ok, f"candidates differ for subject {subj[:50]!r}: sql {len(sql)} vs {None if got is None else len(got)}")
    n_subj += 1; n_rows += len(sql); n_nonempty += bool(sql)
print(f"world_consolidation: {n_subj} subjects, {n_rows} candidate rows ({n_nonempty} subjects non-empty) identical {time.perf_counter() - t0:.0f}s", flush=True)
print("PASS" if not failures else f"FAILED ({len(failures)})")
sys.exit(1 if failures else 0)

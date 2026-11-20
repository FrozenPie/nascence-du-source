"""J-3482 test: core/memory/shock_notes.py + scripts/apply_J-3482_mark_shock_notes.py on a SYNTHETIC temp DB only.
Touches no live data; the script's default DB is never opened (every call passes --db <temp>)."""
import hashlib
import importlib.util
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE lab_env, per the job rules)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
from core.memory import shock_notes as sn  # noqa: E402

spec = importlib.util.spec_from_file_location("apply_j3482", ROOT / "scripts" / "apply_J-3482_mark_shock_notes.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

SHOCK_A = ("[Looked up: 'Leiocephalus psammodromus' (external shock — uninvited)] Leiocephalus psammodromus is a "
           "lizard species native to the Turks and Caicos Islands. It is a small ground dwelling lizard.")
SHOCK_B = ("[Looked up: 'United States Post Office–Whitinsville Main' (external shock — uninvited)] The US Post "
           "Office—Whitinsville Main is an historic post office building located at 58 Church Street in the village.")
SHOCK_SHORT = "[Looked up: 'Cato' (external shock — uninvited)] Cato was a Roman statesman and censor."
PURSUIT = ("[Looked up: 'Significance' (pursuit: what is significance)] Significance refers to importance and is "
           "also the name of a magazine.")

ROWS = [
    # id, origin, content, timestamp, temp
    ("shockA", "research", SHOCK_A, 100.0, "warm"),
    ("shockB", "research", SHOCK_B, 100.0, "warm"),
    ("shockS", "research", SHOCK_SHORT, 100.0, "warm"),
    ("pursuit", "research", PURSUIT, 100.0, "warm"),
    # title hit, after the shock -> selected
    ("n_title", "understanding", "[Understanding — from 'The Principles of Psychology'] Significance refers to "
     "importance. Leiocephalus psammodromus is a lizard species. Philosophy involves thought.", 200.0, "warm"),
    # title hit but lowercase -> selected (case-insensitive)
    ("n_case", "understanding", "[Understanding — from 'x'] a leiocephalus PSAMMODROMUS was mentioned.", 201.0, "warm"),
    # text overlap only (title paraphrased) -> selected via 6-word runs
    ("n_text", "understanding", "[Understanding — from 'King Philip'] The US Post Office—Whitinsville Main is "
     "an historic post office building located at 58 Church Street in the village of Whitinsville.", 202.0, "warm"),
    # selected AND already hidden (J-3191 dict-repr overlap) -> in selection, never changed, never un-hidden by unmark
    ("n_hid", "understanding", "[Understanding — from 'y'] {'Leiocephalus psammodromus': 'a lizard'}", 203.0, "hidden"),
    # title appears but the note is EARLIER than the shock -> NOT selected (causal order)
    ("n_early", "understanding", "[Understanding — from 'z'] Leiocephalus psammodromus was in an old book.", 50.0, "warm"),
    # short title (4 chars, < MIN_TITLE_LEN) -> NOT selected
    ("n_short", "understanding", "[Understanding — from 'z'] Cato the Elder is a Roman figure.", 204.0, "warm"),
    # pursuit page text only -> NOT selected (out of scope)
    ("n_pursuit", "understanding", "[Understanding — from 'z'] Significance refers to importance and is also the "
     "name of a magazine.", 205.0, "warm"),
    # clean note -> NOT selected
    ("n_clean", "understanding", "[Understanding — from 'z'] Kant argues that the categories structure experience.", 206.0, "warm"),
    # a non-understanding row that mentions the title -> NOT selected (origin gate)
    ("reading1", "reading", "Leiocephalus psammodromus appears in a field guide.", 207.0, "warm"),
]
EXPECT_SEL = {"n_title", "n_case", "n_text", "n_hid"}


def make_db(path: Path):
    c = sqlite3.connect(str(path))
    c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, "
              "timestamp REAL, temp TEXT DEFAULT 'warm', cold INTEGER DEFAULT 0)")
    c.executemany("INSERT INTO memory_fragments (fragment_id, origin, content, timestamp, temp) VALUES (?,?,?,?,?)",
                  [(i, o, ct, ts, tp) for i, o, ct, ts, tp in ROWS])
    c.commit()
    c.close()


def snap(path: Path) -> dict:
    c = sqlite3.connect(str(path))
    d = {r[0]: (r[1], r[2]) for r in c.execute("SELECT fragment_id, content, temp FROM memory_fragments")}
    c.close()
    return d


def main() -> int:
    fails = []

    def check(name, ok):
        print(("PASS " if ok else "FAIL ") + name)
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db = Path(td) / "t.db"
        make_db(db)
        c = sqlite3.connect(str(db))
        sel = sn.select(c)
        ids = {s["id"] for s in sel}
        check("selection is exactly the 4 expected notes", ids == EXPECT_SEL)
        kinds = {s["id"]: {k for _, k, _ in s["signals"]} for s in sel}
        check("n_text is selected by the text signal, n_title by the title signal",
              kinds["n_text"] == {"text"} and kinds["n_title"] == {"title"})
        check("exclude veto honoured", {s["id"] for s in sn.select(c, exclude=["n_case"])} == EXPECT_SEL - {"n_case"})
        c.close()

        before = snap(db)
        # dry run writes nothing
        rc = app.main(["--db", str(db)])
        check("dry run exit 0 and file content unchanged", rc == 0 and snap(db) == before)

        # --write is refused while Du is up (stub the process check)
        real = app.du_is_up
        app.du_is_up = lambda: ["1234: python run_nascence.py"]
        rc = app.main(["--db", str(db), "--write"])
        check("--write refused while run_nascence.py runs", rc == 2 and snap(db) == before)
        app.du_is_up = lambda: (_ for _ in ()).throw(RuntimeError("no process list"))
        rc = app.main(["--db", str(db), "--write"])
        check("--write refused when the process list is unreadable (fails closed)", rc == 2 and snap(db) == before)
        app.du_is_up = lambda: []

        # wrong --expect refused
        rc = app.main(["--db", str(db), "--write", "--expect", "99"])
        check("--write refused on wrong --expect", rc == 2 and snap(db) == before)

        # real write
        rc = app.main(["--db", str(db), "--write", "--expect", "4"])
        after = snap(db)
        check("write exit 0", rc == 0)
        check("content of every row byte-identical", all(after[k][0] == before[k][0] for k in before) and set(after) == set(before))
        moved = {k for k in before if after[k][1] != before[k][1]}
        check("only n_title, n_case, n_text changed temp (n_hid was already hidden)", moved == {"n_title", "n_case", "n_text"})
        check("all four selected are hidden, nothing else", {k for k, v in after.items() if v[1] == "hidden"} == EXPECT_SEL)
        mf = Path(str(db) + ".J-3482_marked.json")
        prev = json.loads(mf.read_text(encoding="utf-8"))["previous_temp"]
        check("manifest records exactly the changed rows with their previous temp",
              prev == {"n_title": "warm", "n_case": "warm", "n_text": "warm"})

        # idempotent; a re-run must not shrink the manifest
        rc = app.main(["--db", str(db), "--write"])
        check("re-run changes nothing and keeps the manifest",
              rc == 0 and snap(db) == after and json.loads(mf.read_text(encoding="utf-8"))["previous_temp"] == prev)

        # reverse
        rc = app.main(["--db", str(db), "--unmark", "--write"])
        back = snap(db)
        check("unmark exit 0", rc == 0)
        check("unmark restores the rows it changed and leaves the J-3191 hidden row hidden",
              back == before and back["n_hid"][1] == "hidden")

        # the reader: the sanctioned 'hidden' predicate (J-3398 visible_clause) now skips them
        app.main(["--db", str(db), "--write"])
        c = sqlite3.connect(str(db))
        from core.memory import dict_repr_notes as drn
        vis = {r[0] for r in c.execute("SELECT fragment_id FROM memory_fragments WHERE origin='understanding'"
                                       + drn.visible_clause(c))}
        check("visible_clause readers no longer see the selected notes", vis.isdisjoint(EXPECT_SEL)
              and {"n_early", "n_short", "n_pursuit", "n_clean"} <= vis)
        c.close()
        app.du_is_up = real

        # missing DB / missing temp column refused
        check("missing db refused", app.main(["--db", str(Path(td) / "nope.db")]) == 2)
        d2 = Path(td) / "old.db"
        c = sqlite3.connect(str(d2))
        c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT, timestamp REAL)")
        c.commit()
        c.close()
        check("DB without temp column refused", app.main(["--db", str(d2)]) == 2)

    # the default DB path is never what the tests touch
    check("default DB is the live path (never opened here)", str(app.DEFAULT_DB).endswith("nascence.db"))
    print("ALL PASS" if not fails else f"FAILED: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

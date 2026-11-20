"""J-4371 (D-0849): faded-row archive sidecar + restore-on-match. Temp-path stores only."""
import os, sys, json, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import profile  # noqa: F401  (import core before anything else)
from core import frontier as fr


def _setup(tmp):
    fr._F = Path(tmp) / "frontier.json"
    fr._F_LIGHT = fr._F_LIGHT_DEFAULT
    fr.FRONTIER_SEMANTIC_MERGE = "off"
    profile.guard_path = lambda p: p


def run():
    with tempfile.TemporaryDirectory() as tmp:
        _setup(tmp)
        os.environ.pop("NASCENCE_FRONTIER_ARCHIVE", None)
        q = "why do migrating geese fly in a V formation across lakes?"
        assert fr.note_question(q, "t")
        d = fr._load(); d["questions"][0]["status"] = "faded"; fr._save(d)
        # flag off: nothing archived, re-encounter reopens in place as before
        assert fr.archive_faded(fr._load(), 0) == 0
        os.environ["NASCENCE_FRONTIER_ARCHIVE"] = "on"
        d = fr._load()
        assert fr.archive_faded(d, 1) == 1 and d["questions"] == []
        fr._save(d)
        assert len(fr._load_archive()["questions"]) == 1
        # miss in main -> restored from sidecar as open, sidecar emptied
        assert fr.note_question(q, "t2")
        d = fr._load()
        assert len(d["questions"]) == 1 and d["questions"][0]["status"] == "open"
        assert d["questions"][0]["encounters"] == 2 and "restored_from_archive_ts" in d["questions"][0]
        assert fr._load_archive()["questions"] == []
        # unrelated question does not restore anything
        d["questions"][0]["status"] = "faded"; fr.archive_faded(d, 1); fr._save(d)
        assert fr.note_question("what makes the northern lights turn green in winter skies?", "t3")
        assert len(fr._load_archive()["questions"]) == 1
    print("OK")


if __name__ == "__main__":
    run()

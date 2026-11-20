"""J-4230 (D-0834): frontier archive hardening on top of J-4371. Temp-path stores only.

Checks: (1) a faded row mid-ride on the Follow Line is NOT archived; (2) the revival log records in-store
(baseline) and archive revivals, beside the temp store; (3) the sidecar token index is cached and a miss
does not parse the sidecar again; (4) a restored row is boarded "waiting" when the line is on.
"""
import os, sys, json, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (import core first, and check it is this tree's)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import profile  # noqa: E402
from core import frontier as fr  # noqa: E402
import types  # noqa: E402
sys.modules["core.satisfaction"] = types.SimpleNamespace(record=lambda *a, **k: None)   # no data/ writes
core.satisfaction = sys.modules["core.satisfaction"]


def _setup(tmp):
    fr._F = Path(tmp) / "frontier.json"
    fr._F_LIGHT = fr._F_LIGHT_DEFAULT
    fr.FRONTIER_SEMANTIC_MERGE = "off"
    fr._ARCHIVE_IDX.update(key=None, rows=[])
    profile.guard_path = lambda p: p
    fr._line_enabled = lambda: False


def _revivals(tmp):
    p = Path(tmp) / "logs" / "frontier_revival.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


Q1 = "why do migrating geese fly in a V formation across lakes?"
Q2 = "what makes the northern lights turn green in winter skies?"


def run():
    with tempfile.TemporaryDirectory() as tmp:
        _setup(tmp)
        assert str(fr._F).startswith(tmp) and fr._revival_log_path().is_relative_to(Path(tmp))
        os.environ.pop("NASCENCE_FRONTIER_ARCHIVE", None)
        os.environ.pop("NASCENCE_FRONTIER_REVIVAL_LOG", None)

        # (2a) in-store revival with the archive flag OFF is logged as the baseline
        assert fr.note_question(Q1, "t")
        d = fr._load(); d["questions"][0]["status"] = "faded"; fr._save(d)
        assert fr.note_question(Q1, "t")
        rv = _revivals(tmp)
        assert len(rv) == 1 and rv[0]["path"] == "in_store" and rv[0]["archive_mode"] == "off", rv
        assert not fr._archive_path().exists()                   # flag off: no sidecar

        # (1) mid-ride faded row stays; a finished-ride faded row goes
        os.environ["NASCENCE_FRONTIER_ARCHIVE"] = "on"
        assert fr.note_question(Q2, "t")
        d = fr._load()
        for q in d["questions"]:
            q["status"] = "faded"
        d["questions"][0]["line"] = {"state": "why"}             # Q1 mid-ride
        d["questions"][1]["line"] = {}                           # Q2 never boarded
        assert fr._archivable({"status": "faded", "line": {"state": "settled_no"}})   # finished ride: archivable
        assert fr.archive_faded(d, 1) == 1
        assert [q["q"] for q in d["questions"]] == [Q1.rstrip(".")[:220]]
        fr._save(d)
        assert fr.set_line(d["questions"][0]["id"], state="consequences")   # id-keyed write still lands

        # (3) index cached: a miss does not reparse the sidecar
        calls = {"n": 0}
        real_load = fr._load_archive
        def counting():
            calls["n"] += 1
            return real_load()
        fr._load_archive = counting
        fr._restore_from_archive("completely unrelated words about volcanic basalt columns",
                                 fr._toks("completely unrelated words about volcanic basalt columns"),
                                 fr._load(), 0.0)
        n_after_first = calls["n"]
        fr._restore_from_archive("other unrelated words about tidal pools and starfish",
                                 fr._toks("other unrelated words about tidal pools and starfish"), fr._load(), 0.0)
        assert n_after_first <= 1 and calls["n"] == n_after_first, calls
        fr._load_archive = real_load

        # (4) restore boards the line, logs an archive revival, empties the sidecar row
        fr._line_enabled = lambda: True
        ent = fr.note_question_ex(Q2, "t5", depth=2, slot="what")
        assert ent and ent["status"] == "open" and "restored_from_archive_ts" in ent
        assert ent["line"]["state"] == "waiting" and ent["line"]["depth"] == 2, ent.get("line")
        assert fr._load_archive()["questions"] == []
        rv = _revivals(tmp)
        assert rv[-1]["path"] == "archive" and rv[-1]["archive_mode"] == "on", rv

        # revival log can be silenced
        os.environ["NASCENCE_FRONTIER_REVIVAL_LOG"] = "off"
        d = fr._load(); d["questions"][0]["status"] = "faded"; d["questions"][0]["line"] = {}; fr._save(d)
        n = len(_revivals(tmp))
        assert fr.note_question(Q1, "t6")
        assert len(_revivals(tmp)) == n
        os.environ.pop("NASCENCE_FRONTIER_ARCHIVE", None)
        os.environ.pop("NASCENCE_FRONTIER_REVIVAL_LOG", None)
    print("OK")


if __name__ == "__main__":
    run()

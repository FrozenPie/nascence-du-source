"""J-3752 / F-4361: readers drop census stamp rows (marked and unmarked pre-J-3455 twins). Hermetic: temp files only."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (import core BEFORE anything else)
from core import stamp_rows, mapping_census, object_graph  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(ROOT)

TH = "a long idle thought about the garden and the rain falling slowly"


def _rows():
    return [
        # unmarked historical twin
        {"ts": 100.0, "source": "inner_thought", "thought": TH[:40], "affect": {"valence": .1}, "sounds": []},
        {"ts": 100.2, "source": "idle", "thought": TH, "affect": {"valence": .2}, "sounds": []},
        # marked twin
        {"ts": 200.0, "source": "inner_thought", "stamp": True, "thought": TH[:40], "affect": {"valence": .3}, "sounds": []},
        {"ts": 200.2, "source": "idle", "thought": TH, "affect": {"valence": .4}, "sounds": []},
        # lone reading-style inner_thought with no idle twin: kept
        {"ts": 300.0, "source": "inner_thought", "thought": "something read in a book today", "sounds": []},
        {"ts": 400.0, "source": "idle", "thought": "unrelated", "sounds": []},
    ]


def _write(d, rows):
    p = Path(d) / "geometry_tuples.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def test_helper():
    kept = stamp_rows.drop_stamp_rows(_rows())
    assert [r["ts"] for r in kept] == [100.2, 200.2, 300.0, 400.0]


def test_mapping_census_load_rows():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, _rows())
        for proj in (True, False):
            out = mapping_census.load_rows(p, project=proj)
            assert [r["ts"] for r in out] == [100.2, 200.2, 300.0, 400.0]
            assert all("stamp" not in r for r in out)


def test_object_graph_load_tuples():
    with tempfile.TemporaryDirectory() as d:
        p = _write(d, _rows())
        out = object_graph._load_tuples(p)
        assert [t["ts"] for t in out] == [100.2, 200.2, 300.0, 400.0]
        assert set(out[0]) == {"ts", "sounds", "affect"}


if __name__ == "__main__":
    test_helper(); test_mapping_census_load_rows(); test_object_graph_load_tuples()
    print("ok")

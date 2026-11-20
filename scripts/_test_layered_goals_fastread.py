"""Hermetic test for the goal register's fast reads of the two big stores (core/goals._load_pursuits and
_load_frontier): the fast path must return exactly what the full parse returns, and any odd layout must fall back
to the full parse. Temp dir only. Run: python scripts/_test_layered_goals_fastread.py"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import goals   # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        goals._DATA = root
        ps = []
        for i in range(60):
            ps.append({"id": "p%03d" % i, "question": "q %d with a brace } and a { and \"quotes\"" % i,
                       "status": "active" if i in (7, 31) else ("saturated" if i % 9 == 0 else "dormant"),
                       "advances": i, "centroid": [0.1 * i, 0.2, 0.3], "recent_vecs": [[1.0, 2.0], [3.0, 4.0]],
                       "thoughts": ["one", "two {\n }, {"], "nested": {"id": "inner", "status": "active?"}})
        full_active = [p for p in ps if p["status"] == "active"]
        for nl, label in (("\r\n", "CRLF"), ("\n", "LF")):
            (root / "pursuits_active.json").write_bytes(json.dumps(ps, ensure_ascii=False, indent=1).replace("\n", nl).encode("utf-8"))
            got = goals._load_pursuits()
            check(f"pursuits {label}: fast read returns exactly the active pursuits", got == full_active, [g.get("id") for g in got])
            got = goals._load_pursuits(ids=["p009", "p045"])
            check(f"pursuits {label}: plus the ones asked for by id", sorted(g["id"] for g in got) == ["p007", "p009", "p031", "p045"], [g["id"] for g in got])
            check(f"pursuits {label}: records are whole", next(g for g in got if g["id"] == "p009") == ps[9])
        check("an id that only appears nested does not pull a record in", [g["id"] for g in goals._load_pursuits(ids=["inner"])] == ["p007", "p031"])
        (root / "pursuits_active.json").write_text(json.dumps(ps), encoding="utf-8")            # compact layout
        check("compact layout falls back to the full parse", goals._load_pursuits(ids=["p009"]) and sorted(g["id"] for g in goals._load_pursuits(ids=["p009"])) == ["p007", "p009", "p031"])
        (root / "pursuits_active.json").write_text("[{ broken", encoding="utf-8")
        check("a torn file reads as nothing, never raises", goals._load_pursuits() == [])
        (root / "pursuits_active.json").unlink()
        check("a missing file reads as nothing", goals._load_pursuits() == [])

        qs = [{"id": "q%04d" % i, "q": "question %d }, {\"id\" inside the text" % i if i == 5 else "question %d" % i,
               "status": "open" if i % 50 == 0 else "faded", "encounters": i % 4 + 1,
               "asked_by": {"train_id": "t_%d" % i, "cycle_id": "abcd"}, "variants": [{"q": "v", "n": 1}],
               "finding": "found" if i == 100 else None, "consecutive_stalls": i % 3} for i in range(400)]
        (root / "frontier.json").write_text(json.dumps({"questions": qs}, ensure_ascii=False), encoding="utf-8")
        got = goals._load_frontier(["q0000", "q0100", "q0399"])
        check("frontier: fast read returns the wanted questions whole", got == {"q0000": qs[0], "q0100": qs[100], "q0399": qs[399]})
        check("frontier: text that looks like a boundary still gives the right record (fallback)", goals._load_frontier(["q0005", "q0006"]) == {"q0005": qs[5], "q0006": qs[6]})
        check("frontier: an id that is not there is simply absent", goals._load_frontier(["nope"]) == {})
        check("frontier: no ids, no read", goals._load_frontier([]) == {})
        (root / "frontier.json").write_text(json.dumps({"questions": qs[:1]}), encoding="utf-8")
        check("frontier: a one-question file falls back and still works", goals._load_frontier(["q0000"]) == {"q0000": qs[0]})
        (root / "frontier.json").write_text("{ torn", encoding="utf-8")
        check("frontier: a torn file reads as nothing, never raises", goals._load_frontier(["q0000"]) == {})

    print("\n%s (%d failed)" % ("ALL OK" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

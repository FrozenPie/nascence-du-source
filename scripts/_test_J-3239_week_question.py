"""J-3239 / D-0628: the week page's closing question is open; the reader counts flagged closing sentences."""
import sys, json, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: F401  (before lab_env)
from core import journal_rollup as jr
import journal_week_last_sentence_check as chk

assert Path(jr.__file__).resolve().parent.parent == ROOT, "wrong tree"
s = jr._DID_SYS
assert "MOVED" not in s and "stayed in one place" not in s and "say honestly which" not in s
assert "what changed from the first day to the last, if anything" in " ".join(s.replace('"\n"', '').split()), s
assert s.count("End with one plain sentence") == 1
assert "/no_think" in s and 'Output ONLY JSON: {"entry"' in s
assert "MOVED" not in jr._SAW_SYS

with tempfile.TemporaryDirectory() as td:
    td = Path(td); jd = td / "J"; jd.mkdir()
    def page(wid, last):
        (jd / f"WEEK_{wid}.md").write_text(
            f"# The week {wid}\n\n## the days\n\nI read on Monday. I wrote on Friday. {last}\n\n## the world\n\nRain.\n",
            encoding="utf-8")
    log = td / "g.jsonl"; rows = []
    for i, (flag) in enumerate([True, True, True, False, False]):
        wid = f"2026-W{40+i}"; last = f"Nothing was different at the end {i}."
        page(wid, last)
        rows.append({"wid": wid, "stream": "did", "invented_raw": [last] if flag else ["Friday"],
                     "invented_genuine": []})
    rows.append({"wid": "2026-W40", "stream": "saw", "invented_raw": ["x"]})
    log.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    res = chk.check(jd, log, "2026-W40")
    assert res["n_pages"] == 5 and res["n_graded"] == 5 and res["n_flagged"] == 3 and res["defeater_met"], res
    res = chk.check(jd, log, "2026-W43")
    assert res["n_graded"] == 2 and res["n_flagged"] == 0 and not res["defeater_met"], res
    page("2026-W50", "Ungraded one."); res = chk.check(jd, log, "2026-W49")
    assert res["n_pages"] == 1 and res["n_graded"] == 0
print("J-3239 OK")

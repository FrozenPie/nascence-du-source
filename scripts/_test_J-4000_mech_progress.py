"""J-4000: mechanical question progress. Isolated: pure function tests + shadow log into a temp _DATA."""
import sys, tempfile, pathlib, json
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import curiosity_progress as cp, goals
assert str(pathlib.Path(cp.__file__).resolve()).startswith(str(ROOT)), cp.__file__
m = cp.mech_progress
assert m({})["mlp"] == 0
assert m({"line": {"state": "waiting"}})["mlp"] == 0 and m({"line": {"state": "unsaid"}})["mlp"] == 0
assert m({"line": {"state": "settled_partly"}})["mlp"] == 1.0
assert m({"line": {"state": "settled_yes"}})["mlp"] == 2.0
assert m({"slots": {"what": {"text": "x"}, "why": {"text": "y"}}})["mlp"] == round(2.0 * 2 / 6, 3)
assert m({"slots": {"what": {"text": " "}}})["mlp"] == 0
assert m({"encounters": 9})["mlp"] == 0 and m({"encounters": 9})["reasks"] == 8   # re-ask not progress by default
assert m({}, citations=99)["citations"] == cp.CITATION_CAP
q = {"finding": {"title": "what you found in your own memory"}, "new_fragments": 0}
assert m(q)["mlp"] == 0                      # follow_line finding is not progress
assert cp.score({"id": "a"}) == 0.0          # old score untouched
# integration: temp-path goals._DATA, fake frontier
tmp = pathlib.Path(tempfile.mkdtemp()); (tmp / "logs").mkdir()
qs = [{"id": "a", "q": "a?", "status": "open", "line": {"state": "settled_partly"}},
      {"id": "b", "q": "b?", "status": "open", "slots": {"why": {"text": "t"}}},
      {"id": "c", "q": "c?", "status": "open", "line": {"state": "waiting"}}]
(tmp / "frontier.json").write_text(json.dumps({"questions": qs}))
(tmp / "frontier.light.json").write_text(json.dumps({"open": qs}))
goals._DATA = tmp
recs = goals._from_questions()
byid = {r["id"]: r for r in recs} if recs and "id" in recs[0] else None
rows = [json.loads(l) for l in (tmp / "logs" / "question_progress_shadow.jsonl").read_text().splitlines()]
assert rows and rows[-1]["mech_distinct"] == 3 and rows[-1]["mech_nonzero"] == 2, rows
goals.MECH_PROGRESS_SHADOW = False
n = len(rows); goals._from_questions()
assert len((tmp / "logs" / "question_progress_shadow.jsonl").read_text().splitlines()) == n
print("OK")

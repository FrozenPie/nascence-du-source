"""J-2666: recall_wager real-outcome path. Temp-path stores only; competence.record_drill_accuracy is faked."""
import json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import recall_wager as rw, competence

tmp = Path(tempfile.mkdtemp(prefix="j2666_"))
rw._SHADOW = tmp / "shadow.jsonl"
rw._OBS = tmp / "obs.jsonl"
rw.RECALL_CONFIDENCE_WAGER = True
fed = []
competence.record_drill_accuracy = lambda d, measured, predicted=None, **k: fed.append((d, measured, predicted)) or {"accuracy": 0.5, "accuracy_count": 1}
import core.wager_curiosity as wc
wc.feed = lambda *a, **k: None
A = NS(grade="SUSPECT", self_reported_confidence=0.9, justification=0.5)
def obs(cid, m, src="tier3_model"):
    with open(rw._OBS, "a") as f: f.write(json.dumps({"cycle_id": cid, "source": src, "measured": m}) + "\n")
ok = []
def check(n, c): ok.append(c); print(("PASS " if c else "FAIL ") + n)

# flag off: legacy path, measured = grade score, outcome ignored
obs("c1", 1.0)
r = rw.place(A, cycle_id="c1"); check("off: legacy measured 0.5 fed", r["measured"] == 0.5 and fed[-1][1] == 0.5 and "scorable" not in r)
fed.clear(); rw.REAL_OUTCOME = True
r = rw.place(A, cycle_id="c1"); check("correct -> measured 1 fed", r["measured"] == 1.0 and fed == [("factual_recall", 1.0, 0.9)] and r["scorable"] and r["outcome_source"] == "tier3_model")
fed.clear(); obs("c2", 0.0, "tier4_user")
r = rw.place(A, cycle_id="c2"); check("wrong -> measured 0 fed", r["measured"] == 0.0 and fed == [("factual_recall", 0.0, 0.9)] and r["gap"] == 0.9)
fed.clear(); obs("c3", 1.0, "tier1_eval")
r = rw.place(A, cycle_id="c3"); check("unscorable (disallowed source) not fed", r["scorable"] is False and r["measured"] is None and not fed and not r["fed"])
r = rw.place(A, cycle_id="c4", outcome=1.0); check("caller outcome fed", r["measured"] == 1.0 and len(fed) == 1 and r["outcome_source"] == "caller")
r = rw.place(NS(grade="KNOW", self_reported_confidence=0.9, justification=1.0), cycle_id="c1"); check("ungated not a wager", r is None)
check("status counts unscorable", rw.status().get("unscorable") == 1)
sys.exit(0 if all(ok) else 1)

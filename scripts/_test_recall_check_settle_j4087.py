"""J-4087: decoupled recall check + settle step. Temp-path stores only; competence.record_drill_accuracy is faked."""
import json, sys, tempfile, time
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import recall_wager as rw, recall_check as rc, competence, model_terms as mt
assert Path(rw.__file__).resolve().parent.parent == Path(__file__).resolve().parent.parent

tmp = Path(tempfile.mkdtemp(prefix="j4087_"))
rw._SHADOW = tmp / "shadow.jsonl"
rw._OBS = tmp / "obs.jsonl"
rw.RECALL_CONFIDENCE_WAGER = True
fed = []
competence.record_drill_accuracy = lambda d, measured, predicted=None, **k: fed.append((d, measured, predicted)) or {"accuracy": 0.5, "accuracy_count": 1}
import core.wager_curiosity as wc
wc.feed = lambda *a, **k: None
A = NS(grade="SUSPECT", self_reported_confidence=0.9, justification=0.5)
ok = []
def check(n, c): ok.append(c); print(("PASS " if c else "FAIL ") + n)

idx = mt.FirstSeenIndex(tmp / "no.db", None)
now = time.time()
idx.first = {"galileo": now - 9999, "pisa": now - 9999, "venus": now - 5}   # venus: this cycle's own writing
idx.watermark = now
OUT_OK = 'I recall that "Galileo" was in Pisa, said the old text.'
OUT_BAD = 'I remember that Zorblax met Quendar by the lake.'
r = rc.check(OUT_OK, "tell me", index=idx, now=now)
check("both terms in store -> 1.0", r["outcome"] == 1.0 and r["source"] == "memcheck_store" and r["found"] == 2)
r = rc.check(OUT_BAD, "tell me", index=idx, now=now)
check("terms absent -> 0.0", r["outcome"] == 0.0 and r["found"] == 0)
r = rc.check('Then "Galileo" and "Venus" appeared.', "tell me", index=idx, now=now)
check("term first seen inside grace window not counted", r["terms"] == 2 and r["found"] == 1 and r["outcome"] == 1.0)
r = rc.check(OUT_BAD, "Zorblax and Quendar", index=idx, now=now)
check("terms the person said are excluded -> unscorable", r["outcome"] is None and r["reason"] == "too_few_terms")
r = rc.check(OUT_OK, "x", index=mt.FirstSeenIndex(tmp / "no.db", None), now=now)
check("index not ready -> unscorable", r["outcome"] is None and r["reason"] == "index_not_ready")

# shadow mode (REAL_OUTCOME False): legacy row byte-identical in measured/fed, extra shadow_* fields
mt.default_index = lambda: idx
rw.REAL_OUTCOME = False
r = rw.place(A, cycle_id="c1", output=OUT_BAD, raw_input="tell me")
check("shadow: legacy measured 0.5 still fed", r["measured"] == 0.5 and fed[-1] == ("factual_recall", 0.5, 0.9) and "scorable" not in r)
check("shadow: shadow_measured 0.0 memcheck_store", r["shadow_measured"] == 0.0 and r["shadow_outcome_source"] == "memcheck_store"
      and r["shadow_scorable"] is True and r["shadow_gap"] == 0.9)
fed.clear()
r = rw.place(A, cycle_id="c2", output="short reply", raw_input="x")
check("shadow: unscorable carries null + none", r["shadow_scorable"] is False and r["shadow_measured"] is None and r["shadow_outcome_source"] == "none")

# live-outcome mode
rw.REAL_OUTCOME = True
fed.clear()
r = rw.place(A, cycle_id="c3", output=OUT_BAD, raw_input="x")
check("real: memcheck 0 fed, source tagged", r["measured"] == 0.0 and fed == [("factual_recall", 0.0, 0.9)] and r["outcome_source"] == "memcheck_store" and r["scorable"])
fed.clear()
r = rw.place(A, cycle_id="c4", output="short", raw_input="x")
check("real: no outcome -> measured null, not fed", r["measured"] is None and r["scorable"] is False and not fed and r["outcome_source"] == "none")
with open(rw._OBS, "a") as f: f.write(json.dumps({"cycle_id": "c5", "source": "tier4_user", "measured": 1.0}) + "\n")
r = rw.place(A, cycle_id="c5", output=OUT_BAD, raw_input="x")
check("real: external verdict beats memcheck", r["measured"] == 1.0 and r["outcome_source"] == "tier4_user")

# settle: c4 (unscorable, nothing fed) gets a later tier4_user verdict; c3 (fed via memcheck) gets a later verdict too
fed.clear()
for cid, m in (("c4", 0.0), ("c3", 1.0)):
    with open(rw._OBS, "a") as f: f.write(json.dumps({"cycle_id": cid, "source": "tier4_user", "measured": m}) + "\n")
w = rw.settle(force=True)
by = {x["cycle_id"]: x for x in w}
check("settle: unscorable row fed late", by["c4"]["fed"] and by["c4"]["measured"] == 0.0 and by["c4"]["outcome_source"] == "tier4_user" and fed == [("factual_recall", 0.0, 0.9)])
check("settle: already-fed row logged, not double fed", by["c3"].get("superseded_fed") and not by["c3"]["fed"] and len(fed) == 1)
check("settle: c5 (verdict at placement) skipped", "c5" not in by)
check("settle: idempotent", rw.settle(force=True) == [] and len(fed) == 1)
rw.REAL_OUTCOME = False
fed.clear()
with open(rw._OBS, "a") as f: f.write(json.dumps({"cycle_id": "c2", "source": "tier3_model", "measured": 1.0}) + "\n")
w = rw.settle(force=True)
check("settle in shadow: logged, nothing fed", len(w) == 1 and w[0]["fed"] is False and not fed)
st = rw.status()
check("status counts shadow_scored", st["shadow_scored"] >= 1)
sys.exit(0 if all(ok) else 1)

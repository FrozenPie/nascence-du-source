"""J-3213 / D-0602: unjudged admission tag, historic join, and the solidify guard. Temp paths only.
  python scripts/_test_J-3213_unjudged_admission.py   # exit 0 = ALL OK"""
from __future__ import annotations
import json, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import profile as P  # noqa: E402  (core before anything else)
from core import provisional_identity as pi  # noqa: E402
TMP = Path(tempfile.mkdtemp(prefix="j3213_"))
FAILS = 0
def check(c, l):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + l)
    FAILS += 0 if c else 1
pi._PROV = TMP / "prov.json"; pi._LOG = TMP / "plog.jsonl"; pi._JUDGE_LOG = TMP / "jlog.jsonl"
P.guard_path = lambda p: p
now = time.time()
pi.open_probation("self A new", "t", "h", "e", {"pass": True}, now=now, admission_judge="unjudged")
rec = json.loads(pi._PROV.read_text(encoding="utf-8"))
check(rec.get("admission_judge") == "unjudged" and pi.is_unjudged(rec), "new unjudged opening is tagged")
pi.open_probation("self B judged", "t", "h", "e", {"pass": True}, now=now)
rec2 = json.loads(pi._PROV.read_text(encoding="utf-8"))
check("admission_judge" not in rec2 and not pi.is_unjudged(rec2), "judged opening has no field (reads as judged)")
# historic: an old open with no field, joined to a judge row with warranted None
old = {"ts": now - 10 * 86400, "event": "open", "theme": "old", "self_image": "old candidate text"}
with pi._LOG.open("a", encoding="utf-8") as f:
    f.write(json.dumps(old) + "\n")
pi._JUDGE_LOG.write_text(json.dumps({"ts": old["ts"] + 5, "candidate": "old candidate text",
                                     "emissary_warranted": None, "self_filter_pass": True}) + "\n", encoding="utf-8")
u = pi.historic_unjudged_opens()
check(sorted(x["source"] for x in u) == ["joined", "tag"], "historic joined + new tagged both identified")
sh = pi.unjudged_share_weekly(now=now)
check(sh["unjudged_total"] == 2 and sh["opens_total"] == 3, "weekly share counts")
# solidify guard: unjudged + no integration -> refused, nothing committed
ok = pi._solidify(rec, {"dF_did": 0}, None)
check(ok is False, "unjudged probation cannot solidify without the judge verdict")
evs = [json.loads(l)["event"] for l in pi._LOG.read_text(encoding="utf-8").splitlines()]
check("solidify_refused_unjudged" in evs and "unjudged_share" in evs, "refusal and weekly share logged")
print("ALL OK" if not FAILS else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)

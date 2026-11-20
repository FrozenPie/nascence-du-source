"""J-4086: self-claims shadow (measured accuracy beside confidence). Hermetic: _DATA and SHADOW_LOG point at a temp dir.
Run: python scripts/_test_J-4086_self_claims_shadow.py (from the tree under test)"""
import sys, json, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.self_claims as sc
ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")
tmp = Path(tempfile.mkdtemp(prefix="J-4086_"))
sc._DATA = tmp; sc.SHADOW_LOG = tmp / "logs" / "self_claims_shadow.jsonl"
B = {"science": {"confidence": .88, "accuracy": .38, "accuracy_count": 12},
     "observation": {"confidence": .80, "accuracy": .19, "accuracy_count": 20},
     "history_culture": {"confidence": .82, "accuracy": .20, "accuracy_count": 3},
     "factual_recall": {"confidence": .86, "accuracy": .52, "accuracy_count": 18},
     "mathematics": {"confidence": .80, "accuracy": 1.0, "accuracy_count": 331},
     "dream_work": {"confidence": .79, "accuracy": None, "accuracy_count": 0},
     "fieldcraft": {"confidence": .5, "accuracy": 1.0, "accuracy_count": 2}}
(tmp / "capability_beliefs.json").write_text(json.dumps(B))
before = (tmp / "capability_beliefs.json").read_bytes()
per = sc.shadow_capabilities(B); d = sc.shadow_delta(per)
check("science flips to not-capable? no: 0.38 is mid -> drops", "science" in d["drop"])
check("observation flips to not capable", "observation" in d["flip"] and per["observation"]["would_be"] == "I am not capable at observation")
check("history_culture n=3 below floor keeps confidence claim", per["history_culture"]["basis"] == "confidence" and "history_culture" in d["same"])
check("factual_recall 0.52 drops", "factual_recall" in d["drop"])
check("mathematics same", "mathematics" in d["same"])
check("untested dream_work keeps live claim", per["dream_work"]["would_be"] == "I am capable at dream_work")
check("floor param respected (floor 2 makes fieldcraft tested, appears)", "fieldcraft" in sc.shadow_delta(sc.shadow_capabilities(B, floor=2))["appear"])
live_before = sc._capabilities()
held = sc.held_claims()
check("held_claims unchanged: all 6 confidence>=0.7 domains still capable", len(live_before) == 6 and all(c in held for c in live_before))
rows = [json.loads(l) for l in sc.SHADOW_LOG.read_text(encoding="utf-8").splitlines()]
check("one shadow row written with counts", len(rows) == 1 and rows[0]["counts"] == {k: len(v) for k, v in d.items()} and rows[0]["live_claims"] == live_before)
sc.held_claims()
check("same signature within interval not re-logged", len(sc.SHADOW_LOG.read_text(encoding="utf-8").splitlines()) == 1)
sc.SHADOW_MIN_INTERVAL_S = 0; sc.held_claims()
check("interval 0 logs again", len(sc.SHADOW_LOG.read_text(encoding="utf-8").splitlines()) == 2)
check("beliefs file never written", (tmp / "capability_beliefs.json").read_bytes() == before)
sc.SELF_CLAIMS_SHADOW = False; sc.held_claims()
check("flag off logs nothing", len(sc.SHADOW_LOG.read_text(encoding="utf-8").splitlines()) == 2)
sc._DATA = tmp / "nope"; sc.SHADOW_LOG = tmp / "nope" / "x.jsonl"; sc.SELF_CLAIMS_SHADOW = True
check("missing beliefs: no raise, no log", sc.held_claims() == [] and not sc.SHADOW_LOG.exists())
print("ALL PASS" if ok else "FAILURES"); sys.exit(0 if ok else 1)

"""Verification test (J-4369/D-0847): readers use competence.effective_accuracy. Temp stores only; no live data."""
import sys, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import competence, self_claims, weakness_prior

ea = competence.effective_accuracy
assert ea({"accuracy_drill": 0.9, "accuracy_drill_count": 4, "accuracy": 0.1}) == (0.9, 4)
assert ea({"accuracy_verdict": 0.4, "accuracy_verdict_count": 3, "accuracy": 0.1}) == (0.4, 3)
assert ea({"accuracy": 0.2, "accuracy_count": 5}) == (0.2, 5)
assert ea(None) == (None, 0)

# self_claims: drill accuracy (0.9, n=6) beats legacy 0.1; legacy-only still works
b = {"d1": {"confidence": 0.5, "accuracy_drill": 0.9, "accuracy_drill_count": 6, "accuracy": 0.1, "accuracy_count": 6},
     "d2": {"confidence": 0.5, "accuracy": 0.1, "accuracy_count": 6},
     "d3": {"confidence": 0.5}}
r = self_claims.shadow_capabilities(b, floor=3)
assert r["d1"]["basis"] == "accuracy" and r["d1"]["accuracy"] == 0.9 and r["d1"]["would_be"], r["d1"]
assert r["d2"]["would_be"] and "not capable" in r["d2"]["would_be"], r["d2"]
assert r["d3"]["basis"] == "confidence"

# weakness_prior: temp beliefs dict
w = weakness_prior.weakest_domain({"a": {"accuracy_drill": 0.2, "accuracy": 0.9, "evidence_count": 2},
                                   "b": {"accuracy": 0.5, "evidence_count": 1},
                                   "c": {"accuracy": 0.1, "evidence_count": 0}})
assert w == ("a", 0.2), w

# self_efficacy: _competence_tier reads _DATA/capability_beliefs.json -> point _DATA at a temp dir
from core import self_efficacy as se
tmp = Path(tempfile.mkdtemp())
(tmp / "capability_beliefs.json").write_text(json.dumps(
    {"factual_recall": {"accuracy_drill": 0.8, "accuracy_drill_count": 3, "accuracy": 0.1, "accuracy_count": 3},
     "paradox_holding": {"accuracy": 0.3, "accuracy_count": 4}}), encoding="utf-8")
old = se._DATA; se._DATA = tmp
try:
    cls = next(v for v in vars(se).values() if isinstance(v, type) and hasattr(v, "_competence_tier"))
    inst = cls.__new__(cls)
    t1, why1 = inst._competence_tier("factual"); t2, why2 = inst._competence_tier("paradox")
finally:
    se._DATA = old
assert t1 == 2, (t1, why1)
assert t2 == 1, (t2, why2)
print("PASS")

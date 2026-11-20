"""J-3868 hermetic test: reads only temp files; writes nothing under data/. exit 0 = ALL OK"""
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa
assert str(ROOT).lower() in str(Path(core.__file__).resolve()).lower()
sys.path.insert(0, str(ROOT / "scripts"))
import epistemic_metrics_readout as m

def check(c, msg):
    assert c, msg
    print("ok", msg)

d = Path(tempfile.mkdtemp(prefix="j3868_"))
p = d / "log.jsonl"
check(m.summarize(m.read_rows(p))["entropy_reduction"]["verdict"] == "NO_DATA", "missing log -> NO_DATA")
p.write_text("\n".join(json.dumps({"entropy_reduction": 0.0, "hypothesis_contraction": 0.0}) for _ in range(3)) + "\n{torn", encoding="utf-8")
s = m.summarize(m.read_rows(p))
check(s["entropy_reduction"]["verdict"] == "NEVER_COMPUTED" and s["entropy_reduction"]["n"] == 3, "zeros + torn line -> NEVER_COMPUTED")
p.write_text(json.dumps({"entropy_reduction": 0.5, "hypothesis_contraction": 0.0}) + "\n" + json.dumps({"entropy_reduction": 1.2, "hypothesis_contraction": 0.0}) + "\n", encoding="utf-8")
s = m.summarize(m.read_rows(p))
check(s["entropy_reduction"]["verdict"] == "LIVE" and s["hypothesis_contraction"]["verdict"] == "NEVER_COMPUTED", "varied -> LIVE")
chk = m.producer_selfcheck()
check(abs(chk["hypothesis_contraction"] - 0.75) < 1e-9 and chk["entropy_reduction"] > 1.5, "producer self-check values")
check(m.main(["--log", str(p)]) == 0, "main exit 0")
print("ALL OK")

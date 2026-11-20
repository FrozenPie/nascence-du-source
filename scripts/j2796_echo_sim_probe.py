"""J-2796: where do the PASSING Q&A rows sit relative to ECHO_SIM? Embeds the Q: line of each passing Q&A row (from
docs/lab/J-2796_data/qa_pass_rows.json, made by j2796_qa_evidence_trace.py) against the carried question with the project
embedder (core.memory.store._embed, CPU). Read-only; writes docs/lab/J-2796_data/echo_sim_probe.json."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import core  # noqa: F401  (before lab_env)
import numpy as np
from core.memory.store import _embed

rows = json.loads((ROOT / "docs/lab/J-2796_data/qa_pass_rows.json").read_text(encoding="utf-8"))["rows"]
res = []
for r in rows:
    a, b = _embed(r["q"]), _embed(r["carried"])
    if a is None or b is None:
        continue
    res.append((float(a @ b / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1)), r["asker"]))
sims = np.array([s for s, _ in res])
out = {"n": len(res), "mean": float(sims.mean()), "min": float(sims.min()), "max": float(sims.max()),
       "ge_0.70": int((sims >= 0.70).sum())}
for t in (0.65, 0.60, 0.55, 0.50, 0.45):
    out[f"ge_{t}"] = int((sims >= t).sum())
    out[f"ge_{t}_internal"] = int(sum(1 for s, k in res if s >= t and k == "internal"))
    out[f"ge_{t}_human"] = int(sum(1 for s, k in res if s >= t and k == "human"))
(ROOT / "docs/lab/J-2796_data/echo_sim_probe.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))

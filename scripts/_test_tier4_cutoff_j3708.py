"""J-3708: bootstrap_report excludes pre-cutoff tier4_user rows. Temp-path stores only."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import competence as C
t = Path(tempfile.mkdtemp(prefix="j3708_"))
C._ACCURACY_OBS_FILE = t/"a.jsonl"; C._STABILITY_OBS_FILE = t/"s.jsonl"; C._TIER4_RELABEL_FILE = t/"r.json"
cut = C.TIER4_DETECTOR_FIX_TS
rows = [{"ts": cut-10, "cycle_id": "o1", "source": "tier4_user", "measured": 0.0},
        {"ts": cut-10, "cycle_id": "o2", "source": "tier1_eval", "measured": 1.0},
        {"ts": cut+10, "cycle_id": "n1", "source": "tier4_user", "measured": 1.0},
        {"cycle_id": "n2", "source": "tier4_user", "measured": 1.0}]
C._ACCURACY_OBS_FILE.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
C._STABILITY_OBS_FILE.write_text("\n".join(json.dumps({"cycle_id": c, "stability": .8}) for c in ("o1","o2","n1","n2")), encoding="utf-8")
r = C.bootstrap_report(); ok = []
def check(n, c): ok.append(c); print(("PASS " if c else "FAIL ")+n)
check("default cutoff drops 1 legacy", r["n_tier4_excluded"] == 1 and r["n_accuracy_obs"] == 3 and r["n_pairs"] == 3)
C._TIER4_RELABEL_FILE.write_text(json.dumps({"cutoff_ts": cut+100}))
r = C.bootstrap_report(); check("sidecar overrides", r["n_tier4_excluded"] == 2 and r["n_pairs"] == 2)
sys.exit(0 if all(ok) else 1)

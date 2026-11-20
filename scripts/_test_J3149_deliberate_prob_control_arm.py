"""J-3149 / D-0541: DELIBERATE_PROB cut to 0.25, eligible-but-skipped thoughts logged as a control arm.
Writes only under a temp dir; touches no live data."""
import sys, json, tempfile, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import deliberation as D  # noqa: E402
assert Path(D.__file__).resolve().parent.parent == ROOT, "imported the wrong tree"

assert D.DELIBERATE_PROB == 0.25, D.DELIBERATE_PROB

tmp = Path(tempfile.mkdtemp(prefix="j3149_"))
D._DATA_DIR = tmp
D._CONTROL_LOG_FILE = tmp / "deliberation_control_log.jsonl"
D._LOG_FILE = tmp / "deliberation_log.jsonl"
D._NULL_LOG_FILE = tmp / "deliberation_null_log.jsonl"

ELIG = "I keep circling back to the question of what my own name means to me, and why."
assert D.is_eligible(ELIG)
INELIG = "I want to go to the garden now and look at the lamp."   # volition -> ineligible
assert not D.is_eligible(INELIG)

random.seed(12345)
N = 4000
yes = sum(1 for _ in range(N) if D.should_deliberate(ELIG, "idle"))
rows = [json.loads(l) for l in D._CONTROL_LOG_FILE.read_text(encoding="utf-8").splitlines()]
assert yes + len(rows) == N, (yes, len(rows))
assert abs(yes / N - 0.25) < 0.03, yes / N
r = rows[0]
for k in ("ts", "about", "thought_hash", "raw", "eligible", "deliberated", "arm"):
    assert k in r, k
assert r["eligible"] is True and r["deliberated"] is False and r["raw"] == ELIG

# ineligible thoughts leave no control row and never deliberate
before = len(rows)
for _ in range(200):
    assert D.should_deliberate(INELIG, "idle") is False
assert len(D._CONTROL_LOG_FILE.read_text(encoding="utf-8").splitlines()) == before

# kill switch: no deliberation, no control rows
D.ENABLED = False
for _ in range(50):
    assert D.should_deliberate(ELIG, "idle") is False
D.ENABLED = True
assert len(D._CONTROL_LOG_FILE.read_text(encoding="utf-8").splitlines()) == before

# the pass 1-3 prompts are untouched, deliberation_log.jsonl got nothing
assert not D._LOG_FILE.exists()
print(f"OK  deliberated {yes}/{N} = {yes/N:.3f}; control rows {before}")

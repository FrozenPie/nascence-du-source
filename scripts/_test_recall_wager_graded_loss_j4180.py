"""J-4180: graded loss bar for the recall wager. Temp-path stores only."""
import sys, tempfile, json
from pathlib import Path
from core import prediction_error as pe, contradiction_gate  # core BEFORE anything else
assert str(Path(pe.__file__).resolve()).startswith(str(Path(__file__).resolve().parents[1])), pe.__file__
t = Path(tempfile.mkdtemp())
pe._RAW, pe._STATE, pe._SHADOW = t/"raw.jsonl", t/"state.json", t/"sh.jsonl"
pe.FEED_LEDGER = False
# default path byte-identical: 0.85 vs 0.5 is not large
assert pe.observe("factual_recall", 0.85, 0.5) is None
assert json.loads(pe._RAW.read_text().splitlines()[-1])["large"] is False
# graded path: same pair is large and reaches the gate
v = pe.observe("factual_recall", 0.85, 0.5, gap_threshold=0.30)
assert v is not None, v
assert json.loads(pe._RAW.read_text().splitlines()[-1])["large"] is True
# below the graded bar still nothing
assert pe.observe("factual_recall", 0.78, 0.5, gap_threshold=0.30) is None
from core import recall_wager as rw
assert rw.WAGER_LOSS_GAP == 0.30 and rw.GRADED_LOSS and rw.CONF_BAR == 0.85
print("OK", v.get("would_pressure"))

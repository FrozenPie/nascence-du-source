"""J-1994 / F-2595: status() (HUD/pulse poll) must never append to the arousal shadow; level() still does.
Temp store only: _LOG/_DATA redirected to a tempdir; asserts core.arousal resolves inside this tree."""
import sys, os, json, time, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import arousal  # import core BEFORE any lab_env
assert str(Path(arousal.__file__).resolve()).startswith(str(ROOT)), arousal.__file__
sys.path.insert(0, str(ROOT / "scripts"))
import arousal_run_windows as arw

tmp = Path(tempfile.mkdtemp(prefix="J-1994_"))
arousal._DATA = tmp; arousal._LOG = tmp / "arousal_shadow.jsonl"
arousal._STATE = tmp / "arousal_state.json"; arousal._REGIME_STATE = tmp / "regime.json"
arousal._cache.update({"level": None, "ts": 0.0}); arousal._last_log = 0.0

s = arousal.status()
assert "samples" in s
assert not arousal._LOG.exists(), "status() on a fresh process appended a row"
arousal._cache.update({"level": None, "ts": 0.0}); arousal._last_log = 0.0
arousal.level(write_log=False)
assert not arousal._LOG.exists(), "level(write_log=False) appended"
arousal._cache.update({"level": None, "ts": 0.0}); arousal._last_log = 0.0
arousal.level()
assert arousal._LOG.exists() and len(arousal._LOG.read_text().splitlines()) == 1, "Du-path level() must still append"
arousal._cache.update({"level": None, "ts": 0.0}); arousal._last_log = 0.0
n = len(arousal._LOG.read_text().splitlines()); arousal.status()
assert len(arousal._LOG.read_text().splitlines()) == n, "status() appended after existing log"
# window filter
log = tmp / "n.log"
log.write_text("2026-10-01 10:00:00,1 [nascence.memory] Memory store initialised at x\n"
               "2026-10-01 11:00:00,1 [nascence.main] Nascence shutting down.\n", encoding="utf-8")
t_in = time.mktime((2026,10,1,10,30,0,0,0,-1)); t_out = time.mktime((2026,10,1,13,0,0,0,0,-1))
kept = arw.rows_in_run_windows([{"ts": t_in}, {"ts": t_out}], log)
assert kept == [{"ts": t_in}], kept
print("OK J-1994")

# ---- J-2040: status() reads only Du-window rows; cached filter == uncached; fail-open ----
arousal._DATA = tmp   # du_only_rows reads tmp/nascence.log
(tmp / "nascence.log").write_text(log.read_text(encoding="utf-8"), encoding="utf-8")
rows = [{"ts": t_in, "level": 0.5, "phasic": 0.0}, {"ts": t_out, "level": 0.9, "phasic": 0.0}]
assert arousal.du_only_rows(rows) == [rows[0]], "du_only_rows must drop the out-of-window row"
assert arw.filter_rows_cached(rows, log) == arw.rows_in_run_windows(rows, log)
assert arw.run_windows_cached(log) == arw.run_windows(log)
with open(log, "a", encoding="utf-8") as f:   # incremental append: new boot, no shutdown yet
    f.write("2026-10-01 12:00:00,1 [nascence.memory] Memory store initialised at x\n2026-10-01 12:05:00,1 [x] hi\n")
assert arw.run_windows_cached(log) == arw.run_windows(log), "incremental parse diverged"
missing = tmp / "nope.log"
assert arw.filter_rows_cached(rows, missing) == rows, "must fail open when log missing"
# status() end-to-end: out-of-window-only log => zero Du samples
arousal._LOG.write_text(json.dumps({"ts": t_out, "level": 0.9, "tonic": 0.9, "phasic": 0.0}) + "\n", encoding="utf-8")
(tmp / "nascence.log").write_text(log.read_text(encoding="utf-8").split("2026-10-01 12:00")[0], encoding="utf-8")
assert arousal.status()["samples"] == 0, arousal.status()
print("OK J-2040")

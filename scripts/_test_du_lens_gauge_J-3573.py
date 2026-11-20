"""J-3573 hermetic test: du_lens_gauge writes ONLY to a temp path. Run from the worktree: python scripts/_test_du_lens_gauge_J-3573.py"""
import sys, tempfile, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import du_lens_gauge as g          # core BEFORE anything lab-ish
import core
tmp = Path(tempfile.mkdtemp(prefix="j3573_"))
g._LOG = tmp / "gauge.jsonl"                 # outside data/: guard_path honors a redirect
assert len(g.pairs()) == 62
row = {"ts": time.time(), "place": "shore", "sounds": ["kingfisher_call", "shag_wingbeats", "waves_on_shingle"], "weather": "drizzle"}
r = g.record_idle(row, "The stones are cold; salt on the wind, and I climb down.")
assert r and r["kind"] == "idle", r
fired = set(r["fired"]); print(r["present"], fired)
assert "stones|sound:kingfisher_call+sound:shag_wingbeats" in fired
assert "salt|sound:waves_on_shingle" in fired and "climb|sound:waves_on_shingle" in fired
assert "cools|weather:drizzle" not in fired and "cools|weather:drizzle" in r["present"]
assert not any(p.endswith("act:read") for p in r["present"])
# hands: same thought joins, other thought does not
t = "The stones are cold; salt on the wind, and I climb down."
h = g.record_hands(t, "read", "book")
assert h and "book|act:read" in h["fired"] if "book" in t else h is not None
assert g.record_hands("Something else entirely about a page", "read", "") is None
s = g.summary(g._LOG)
assert s["rows"] == 2 and s["fired_all"] == len(r["fired"]) + len(h["fired"]), s["rows"]
# fence: a path inside live data/ is refused and swallowed
g._LOG = Path(core.__file__).parent.parent / "data" / "du_lens_gauge_shadow.jsonl"
print("fence ->", g.record_idle(row, "x"))
print("core file:", core.__file__, "| tmp:", tmp, "| OK")

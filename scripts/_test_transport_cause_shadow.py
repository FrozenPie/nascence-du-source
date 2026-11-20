"""Offline test for core/transport_cause_shadow.py + its transport_manager hooks (J-4382). Temp stores only."""
import sys, tempfile, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import core.transport_manager as tm
import core.transport_habituation as thab
import core.transport_cause_shadow as tcs
sys.path.insert(0, str(Path(__file__).parent))
import transport_cause_shadow_read as rd

tmp = Path(tempfile.mkdtemp())
tm._STATE = tmp / "l.json"; tm._SHADOW_LOG = tmp / "s.jsonl"
thab._STATE = tmp / "h.json"; thab._LOG = tmp / "h.jsonl"
tcs._STATE = tmp / "c.json"; tcs._LOG = tmp / "c.jsonl"; tcs._state = None
res = []
def check(n, c): res.append(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")

check("cause_key sound", tcs.cause_key("sound:tui_song:garden") == "sound:tui_song")
check("cause_key life", tcs.cause_key("life:gulls:shore") == "life:gulls")
check("cause_key cat passthrough", tcs.cause_key("cat:state:sit@study") == "cat:state:sit@study")
check("cause_key odd input", tcs.cause_key("x") == "x" and tcs.cause_key("") == "")

now = time.time()
tm.observe("sound:tui_song:garden", now - 10)
tm.observe("sound:tui_song:wood", now - 5)       # same event window -> one event, one cause occurrence
tm.observe("sound:tui_song:shore", now - 1)
c = tcs._state["causes"]["sound:tui_song"]
check("union of places = one cause line", len(c["places"]) == 3 and c["n_total"] == 1)
check("one event id across places", len({p["event_id"] for p in c["places"].values()}) == 1)
tm.observe("sound:tui_song:garden", now + 3600)  # new event
check("new event after window", c["n_total"] == 2 and c["places"]["sound:tui_song:garden"]["event_id"] != c["places"]["sound:tui_song:wood"]["event_id"])

w = tm.dispatch_tick()   # novelty winner exists; shadow logs
rows = [json.loads(l) for l in open(tcs._LOG, encoding="utf-8")]
check("tick row + cause row logged", any(r["type"] == "tick" for r in rows) and any(r["type"] == "cause" for r in rows))
cr = [r for r in rows if r["type"] == "cause" and r["cause_id"] == "sound:tui_song"][0]
check("cause fires once for 3 places' novelty", cr["cause_would_fire"] and sum(p["place_would_fire"] for p in cr["places"]) == 3)
check("real winner unaffected (still a novelty line)", w is not None and w.kind == "novelty")
r = rd.read(tcs._LOG)
check("reader: cause<=place", r["cause_le_place"] and r["cause_fires"] == 1 and r["place_fires"] == 3)

tcs.TRANSPORT_CAUSE_SHADOW = False
n0 = len(rows); tm.observe("sound:other:x", now); tm.dispatch_tick()
check("kill switch silences log", len(open(tcs._LOG, encoding="utf-8").readlines()) == n0)
tcs.TRANSPORT_CAUSE_SHADOW = True
tcs._LOG = Path(tmp / "nodir" / "x" / "c.jsonl")  # fail-open on odd paths
tcs.tick([], 1.5)
check("fail-open", True)
sys.exit(0 if all(res) else 1)

"""
J-3304 (D-0636 / J-3247 / F-3900): core/couriers.py delivered echo rows carry fragment_id and n_candidates.

Proves, against a temp sqlite DB and temp log/state paths (nothing under the real data/ is touched; model-free, sensorium/wandering/sound stubs):
  [1] context_echo + sound_echo, delivered branch: row has fragment_id (the one picked) and n_candidates (the matched count), AND every key the
      pre-J-3304 delivered row had (ts, route, context|sound, freight_age, cargo_type) with the same values
  [2] would-have branch (COURIER_TEXT_DELIVERY False): keeps would_have_delivered + fragment_id, gains n_candidates
  [3] the pick is unchanged: the picked fragment is always one of the matching rows; non-matching rows are never picked; count excludes them
  [4] fail-open: a broken COUNT returns None and the delivery still happens with n_candidates=None
  [5] cooldown logic untouched: state written once, second call inside cooldown returns False and logs nothing
  [6] the cap: _count_candidates is bounded (SQL carries LIMIT)
  python scripts/_test_J3304_couriers_fragment_id.py     # exit 0 = ALL OK; run from the checkout under test
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import time
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import couriers  # noqa: E402  (core before anything else)
from core import profile   # noqa: E402

assert Path(couriers.__file__).resolve().parent.parent == ROOT, "couriers imported from the wrong tree"

TMP = Path(tempfile.mkdtemp(prefix="j3304_couriers_"))
FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# --- temp world -----------------------------------------------------------------------------------------------------
DB = TMP / "nascence.db"
now = time.time()
old = now - 10 * 86400
conn = sqlite3.connect(DB)
conn.executescript("""
CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT);
CREATE TABLE fragment_context (fragment_id TEXT PRIMARY KEY, tuple_ts REAL, place TEXT, weather TEXT, sounds TEXT);
""")
rows = []
for i in range(7):      # 7 matching: thunderstorm + wren_scold, lived, old
    rows.append((f"m{i}", f"memory {i}", "lived", old - i, "shore", "thunderstorm", '["wren_scold"]'))
rows.append(("x_recent", "too recent", "lived", now - 3600, "shore", "thunderstorm", '["wren_scold"]'))   # too recent
rows.append(("x_origin", "bad origin", "peer", old, "shore", "thunderstorm", '["wren_scold"]'))          # origin excluded
rows.append(("x_other", "other weather", "lived", old, "shore", "high cloud", '["gull_cries"]'))         # no match
for fid, content, origin, ts, place, wx, snd in rows:
    conn.execute("INSERT INTO memory_fragments VALUES (?,?,?)", (fid, content, origin))
    conn.execute("INSERT INTO fragment_context VALUES (?,?,?,?,?)", (fid, ts, place, wx, snd))
conn.commit()
conn.close()
MATCH_IDS = {f"m{i}" for i in range(7)}

LOG = TMP / "couriers_log.jsonl"
STATE = TMP / "couriers_state.json"
couriers._DB, couriers._DELIVERY_LOG, couriers._STATE = DB, LOG, STATE
assert not str(TMP).replace("\\", "/").startswith(str(ROOT / "data").replace("\\", "/"))

# --- stubs ----------------------------------------------------------------------------------------------------------
from core import sensorium, sound_knowledge, soundscape, wandering  # noqa: E402

sensorium.state = {"weather": "Thunderstorm"}
sensorium.where = lambda: "shore"
perceived = []
wandering.perceive = lambda t: perceived.append(t)
sound_knowledge._load = lambda: {"hearings": {"wren_scold": {"last_ts": time.time()}}}
sound_knowledge.is_learned = lambda k: True


def reset():
    for p in (LOG, STATE):
        if p.exists():
            p.unlink()
    perceived.clear()


def log_rows():
    return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()] if LOG.exists() else []


OLD_KEYS = {
    "context_echo": {"ts", "route", "context", "freight_age", "cargo_type"},
    "sound_echo": {"ts", "route", "sound", "freight_age", "cargo_type"},
}

print("[1] delivered branch")
couriers.COURIER_TEXT_DELIVERY = True
for fn, route in ((couriers.context_echo, "context_echo"), (couriers.sound_echo, "sound_echo")):
    reset()
    ok = fn()
    r = log_rows()
    check(ok is True and len(r) == 1, f"{route}: returned True, one row logged")
    row = r[0]
    check(OLD_KEYS[route] <= set(row), f"{route}: every pre-J-3304 key still present ({sorted(OLD_KEYS[route])})")
    check(row.get("fragment_id") in MATCH_IDS, f"{route}: fragment_id is a matching row ({row.get('fragment_id')})")
    check(row.get("n_candidates") == 7, f"{route}: n_candidates == 7 matched rows ({row.get('n_candidates')})")
    check("would_have_delivered" not in row, f"{route}: delivered row is not marked would_have")
    check(len(perceived) == 1 and "memory" in perceived[0], f"{route}: text delivered to wandering exactly as before")
    check(str(row["fragment_id"]).replace("m", "memory ") in perceived[0] or row["fragment_id"] in MATCH_IDS,
          f"{route}: delivered text belongs to the logged fragment")
    ix = row["fragment_id"][1:]
    check(f"memory {ix}" in perceived[0], f"{route}: logged fragment_id is the fragment whose text was delivered")

print("[2] would-have branch (COURIER_TEXT_DELIVERY False)")
couriers.COURIER_TEXT_DELIVERY = False
for fn, route in ((couriers.context_echo, "context_echo"), (couriers.sound_echo, "sound_echo")):
    reset()
    fn()
    row = log_rows()[0]
    check(OLD_KEYS[route] <= set(row) and row.get("would_have_delivered") is True, f"{route}: old keys + would_have_delivered")
    check(row.get("fragment_id") in MATCH_IDS and row.get("n_candidates") == 7, f"{route}: fragment_id and n_candidates present")
    check(perceived == [], f"{route}: no text reaches the trail when text delivery is off")
couriers.COURIER_TEXT_DELIVERY = True

print("[3] the pick is still uniform over matching rows only")
seen = set()
for _ in range(60):
    reset()
    couriers.sound_echo()
    seen.add(log_rows()[0]["fragment_id"])
check(seen <= MATCH_IDS and len(seen) >= 4, f"60 draws only ever hit matching rows, {len(seen)} distinct of 7")

print("[4] fail-open count")
orig = couriers._count_candidates
couriers._count_candidates = lambda *a, **k: orig(None, "1=1", ())    # None connection -> exception inside -> None
reset()
ok = couriers.context_echo()
row = log_rows()[0]
check(ok is True and row.get("n_candidates") is None and row.get("fragment_id") in MATCH_IDS,
      "count failure: still delivered, n_candidates None, fragment_id kept")
couriers._count_candidates = orig
c2 = sqlite3.connect(DB)
check(couriers._count_candidates(c2, "bad sql ((", ()) is None, "bad SQL -> None, no raise")
c2.close()

print("[5] cooldown untouched")
reset()
a = couriers.sound_echo()
b = couriers.sound_echo()
check(a is True and b is False and len(log_rows()) == 1, "second call inside the cooldown: False, nothing more logged")
check("last_sound_echo_ts" in json.loads(STATE.read_text(encoding="utf-8")), "cooldown state written")

print("[6] bounded count")
import inspect
src = inspect.getsource(couriers._count_candidates)
check("LIMIT" in src and couriers._COUNT_CAP > 0, f"count SQL carries LIMIT {couriers._COUNT_CAP}")
c3 = sqlite3.connect(DB)
couriers._COUNT_CAP = 3
check(couriers._count_candidates(c3, "fc.tuple_ts < ?", (now,)) == 3, "cap clamps the count (reads as 'at least N')")
c3.close()

print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)

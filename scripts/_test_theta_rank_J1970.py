"""J-1970: isolated test of core/theta_shadow.py's tod-first ranking + raised cap. Temp DB and temp log only;
never touches data/. Run: python scripts/_test_theta_rank_J1970.py"""
import json, sqlite3, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import theta_shadow as T  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="theta_test_J1970_"))
T._DB = tmp / "t.db"
T._SHADOW_LOG = tmp / "theta_shadow.jsonl"
T._index_ensured = False
conn = sqlite3.connect(str(T._DB))
conn.execute("CREATE TABLE fragment_context (fragment_id TEXT PRIMARY KEY, tuple_ts REAL, tod REAL, season REAL)")
NOW = time.mktime((2026, 10, 8, 12, 0, 0, 0, 0, -1))
tod0, s0 = T.now_phase(NOW)
D = 86400.0
rows = [  # id, age_days, tod offset, season offset (days)
    ("recent_same_clock_off", 2, 0.0100, 0), ("older_exact_clock", 20, 0.0, 15), ("recent_exact_clock", 3, 0.0, 0),
    ("outside_season", 5, 0.0, 60), ("outside_tod", 4, 0.2, 0), ("too_young", 0.5, 0.0, 0)]
for fid, age, dt, dseas in rows:
    conn.execute("INSERT INTO fragment_context VALUES (?,?,?,?)",
                 (fid, NOW - age * D, (tod0 + dt) % 1.0, (s0 + dseas / 366.0) % 1.0))
conn.commit(); conn.close()
fails = 0
def check(c, m):
    global fails
    print(("ok   " if c else "FAIL ") + m); fails += (not c)
r = T.cast_ray(NOW)
check(r["top3_ids"][:2] == ["recent_exact_clock", "older_exact_clock"], f"tod-first: exact clock first, ties recency ({r['top3_ids']})")
check(r["top3_ids"][2] == "recent_same_clock_off" and len(r["top3_ids"]) == 3, "third = 0.01 off clock")
check("outside_season" not in r["candidate_ids"] and "outside_tod" not in r["candidate_ids"] and "too_young" not in r["candidate_ids"],
      "season window / tod window / 1-day floor filters unchanged")
check(r["rank_rule"] == "tod_first_season_window", "rank_rule exposed")
old = [x["fragment_id"] for x in T.rank_candidates(
    [{"fragment_id": a, "tod": (tod0 + c) % 1.0, "season": (s0 + d / 366.0) % 1.0, "tuple_ts": NOW - b * D} for a, b, c, d in rows[:3]],
    tod0, s0, season_weight=1.0)]
check(old[0] == "recent_exact_clock" and old[1] == "recent_same_clock_off", f"weight 1.0 reproduces the old linear rule ({old})")
check(T._RAY_ROW_LIMIT >= 20000, "cap raised so a backfilled window is ranked whole")
row = T.log_ray("test", ["x"], NOW)
logged = json.loads(T._SHADOW_LOG.read_text().splitlines()[0])
check(logged["rank_rule"] == "tod_first_season_window" and logged["top3_ids"] == row["top3_ids"], "log row carries rank_rule")
print("FAILED" if fails else "ALL PASS"); sys.exit(1 if fails else 0)

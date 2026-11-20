"""Hermetic test for J-3372: scripts/pursuit_close_defeater_read.py.  Temp logs only; no live data, no model calls.
Run: python scripts/_test_J-3372_pursuit_close_defeater_read.py   (from the tree under test)"""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
import pursuit_close_defeater_read as dr

ok_all = True
def check(n, c):
    global ok_all
    ok_all = ok_all and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")

def row(i, resolve, askable=True, how="agreed", basis="open", ts=None, why="t", note=None):
    r = {"ts": ts or 1000.0 + i, "kind": "close_ask", "id": f"p{i}", "question": f"q{i}", "asked": True,
         "how": how, "would_resolve": resolve, "why": why, "would_note": note}
    if askable is not None:
        r.update({"askable": askable, "basis": basis})
    return r

def write(d, name, rows):
    p = Path(d) / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p

with tempfile.TemporaryDirectory() as d:
    live_before = dr.LIVE_LOG.stat().st_size if dr.LIVE_LOG.exists() else None
    # 1. legacy-only (the live log today): 89 unflagged asks, 0 resolve -> no askable data, never a verdict
    p = write(d, "legacy.jsonl", [row(i, False, askable=None) for i in range(89)])
    r = dr.read(p)
    check("legacy rows excluded from the rate", r["fire_rate"]["pursuits_asked"] == 0 and r["legacy_unflagged_asked_rows_excluded"] == 89)
    check("legacy-only -> NOT_ENOUGH_YET", r["defeater_verdict"] == "NOT_ENOUGH_YET")
    # 2. 29 askable asks -> still no verdict even at 100 percent
    p = write(d, "29.jsonl", [row(i, True) for i in range(29)])
    r = dr.read(p)
    check("29 askable asks -> NOT_ENOUGH_YET (no rate verdict below 30)", r["defeater_verdict"] == "NOT_ENOUGH_YET")
    # 3. 30 asks, 0 resolve -> meaningless
    p = write(d, "30z.jsonl", [row(i, False) for i in range(30)])
    r = dr.read(p)
    check("30 asks, 0 resolve -> OUT_OF_BAND_MEANINGLESS + retire action", r["defeater_verdict"] == "OUT_OF_BAND_MEANINGLESS" and r["action_if_out_of_band"])
    # 4. 30 asks, 6 resolve (20 percent) -> in band; first five ordered by ts with flags
    rows = [row(i, i < 6, basis="done_when" if i % 2 else "open",
                why="I have finally resolved it" if i == 0 else "plain", note="standing text") for i in range(30)]
    p = write(d, "30ok.jsonl", rows)
    r = dr.read(p)
    check("6 of 30 -> IN_BAND", r["defeater_verdict"] == "IN_BAND" and abs(r["fire_rate"]["rate"] - 0.2) < 1e-9)
    check("first_would_resolve is 5 rows in ts order", [x["id"] for x in r["first_would_resolve"]] == [f"p{i}" for i in range(5)])
    check("self-praise pointer flagged on p0 only", r["first_would_resolve"][0]["flags"] and not r["first_would_resolve"][1]["flags"])
    check("basis breakdown counts", r["by_basis"] == {"open": 15, "done_when": 15})
    # 5. >50 percent -> too lenient; unavailable share reported
    rows = [row(i, True, how="unavailable" if i < 3 else "agreed") for i in range(30)]
    r = dr.read(write(d, "hi.jsonl", rows))
    check("30 of 30 -> OUT_OF_BAND_TOO_LENIENT", r["defeater_verdict"] == "OUT_OF_BAND_TOO_LENIENT")
    check("unavailable share reported", abs(r["unavailable_share"] - 0.1) < 1e-9)
    # 6. skipped rows counted
    rows = [row(i, False) for i in range(3)] + [{"ts": 5.0, "kind": "close_skip", "id": "s1", "asked": False, "askable": False, "basis": "none"}]
    r = dr.read(write(d, "skip.jsonl", rows))
    check("skipped_not_askable counted", r["fire_rate"]["skipped_not_askable"] == 1)
    # 7. since_ts filter; module path restored; missing log is no_data not a crash
    r = dr.read(write(d, "ts.jsonl", [row(i, False, ts=float(i + 1)) for i in range(30)]), since_ts=21.0)
    check("since_ts window respected", r["fire_rate"]["pursuits_asked"] == 10)
    r = dr.read(Path(d) / "absent.jsonl")
    check("missing log -> NOT_ENOUGH_YET, no crash", r["defeater_verdict"] == "NOT_ENOUGH_YET")
    check("SHADOW_LOG restored after read", dr.pcs.SHADOW_LOG == ROOT / "data" / "logs" / "pursuit_close_shadow.jsonl")
    # 8. CLI paths run
    check("main() text mode exits 0", dr.main(["--log", str(Path(d) / "30ok.jsonl")]) == 0)
    check("main() json mode exits 0", dr.main(["--log", str(Path(d) / "30ok.jsonl"), "--json"]) == 0)
    live_after = dr.LIVE_LOG.stat().st_size if dr.LIVE_LOG.exists() else None
    check("live log untouched (size unchanged)", live_before == live_after)

print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

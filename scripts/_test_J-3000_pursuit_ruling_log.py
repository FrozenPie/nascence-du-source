"""J-3000 (F-3700): pursuits.judge_pending writes a reconstruction row per resolved pending item.
Hermetic: judge_panel.rule_detail stubbed, every pursuits path pointed at a temp dir, nothing live touched.
Run: python scripts/_test_J-3000_pursuit_ruling_log.py   (from the tree under test)"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.pursuits as pu
import core.judge_panel as jp
import core.needle_triage as nt
import core.pursuit_close_shadow as pcs
sys.path.insert(0, str(ROOT / "scripts"))
import pursuits_judged_read as rd

TMP = Path(tempfile.mkdtemp(prefix="J-3000_"))
ok_all = True


def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


pu._DIR = TMP
pu._ACTIVE = TMP / "pursuits_active.json"
pu._SHADOW = TMP / "pursuits_shadow.jsonl"
pu._SERIES = TMP / "pursuits_series.jsonl"
pu._write_light = lambda items, stamp=None: None
nt.read = lambda *a, **k: None


async def _no_close(items):
    return 0
pcs.sweep = _no_close

calls = []
script = {"mode": "by_text"}


async def fake_rule_detail(system, user, key, context="", **kw):
    calls.append((key, context, kw.get("cycle_id")))
    if script["mode"] == "down":
        return {"verdict": None, "how": "unavailable", "why": None}
    v = "garden" in user.split("NEW THOUGHT:")[1]
    return {"verdict": v, "how": "agreed" if v else "tiebreak", "why": "because " + ("new" if v else "circling")}
jp.rule_detail = fake_rule_detail


async def _must_not_be_called(*a, **k):
    raise AssertionError("judge_pending must not call jp.rule any more (rule_detail is the single path)")
jp.rule = _must_not_be_called


def reg(n_pending=2):
    return [{"id": "pA", "question": "what is the garden for?", "status": "active", "advances": 1, "heat": 0.3,
             "standing": "the garden is a place of slow work", "thoughts": [],
             "pending": [{"thought": "the garden teaches patience " + "x" * 300, "prior_standing": "prior " + "y" * 400,
                          "cycle_id": "cyc-1", "ts": 1000.123456, "tries": 0, "restate_sim": 0.4, "coherent": True},
                         {"thought": "a circle about the sea", "prior_standing": "prior", "cycle_id": "cyc-1",
                          "ts": 2000.5, "tries": 0}][:n_pending]}]


print("[1] sha is stable and the observe path stamps it")
t = "The garden teaches patience, slowly."
check("sha deterministic", pu._thought_sha(t, 12.3456) == pu._thought_sha("  " + t + "  ", 12.3456))
check("sha differs by ts", pu._thought_sha(t, 1.0) != pu._thought_sha(t, 2.0))
check("sha survives a JSON round trip of ts", pu._thought_sha(t, json.loads(json.dumps(1000.123456))) == pu._thought_sha(t, 1000.123456))
src = Path(pu.__file__).read_text(encoding="utf-8")
check("observe() stamps thought_sha on the pending item", '"thought_sha": _thought_sha(thought, now)' in src)
pu._ACTIVE.write_text(json.dumps([{"id": "pO", "question": "what is the garden for?", "status": "active", "advances": 1,
                                   "heat": 0.5, "standing": "s", "thoughts": ["a"], "centroid": [1.0, 0.0, 0.0],
                                   "recent_vecs": [[0.0, 1.0, 0.0]], "last_touched": __import__("time").time(), "pending": []}]), encoding="utf-8")
pu._last_observe = 0.0
ev = pu.observe("The garden teaches patience, slowly and without hurry.", "garden", [0.9, 0.1, 0.0], False, "cyc-9")
pend = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))[0]["pending"]
check("a real observe() queues a pending item carrying the matching sha",
      ev is not None and len(pend) == 1 and pend[0]["thought_sha"] == pu._thought_sha(pend[0]["thought"], pend[0]["ts"]))

print("[2] judged + refuted rows, verdicts unchanged")
pu._ACTIVE.write_text(json.dumps(reg(), ensure_ascii=False), encoding="utf-8")
out = asyncio.run(pu.judge_pending())
# J-4052: judge_pending later gained a judge_batch_cut key; the original five counts are what this pins.
check("out counts", {k: out.get(k) for k in ("judged", "confirmed", "refuted", "kept_pending", "dropped")} == {"judged": 2, "confirmed": 1, "refuted": 1, "kept_pending": 0, "dropped": 0})
rows = pu.judged_rows()
check("two rows", len(rows) == 2)
r0, r1 = rows
check("confirmed row: verdict True, how agreed", r0["verdict"] is True and r0["how"] == "agreed")
check("refuted row: verdict False, how tiebreak", r1["verdict"] is False and r1["how"] == "tiebreak")
check("thought and prior truncated to 200", len(r0["thought"]) == 200 and len(r0["prior_standing"]) == 200)
check("sha computed lazily for an unstamped item", r0["thought_sha"] == pu._thought_sha(reg()[0]["pending"][0]["thought"], 1000.123456))
check("pursuit id, cycle id (conversation) and why recorded", r0["pursuit_id"] == "pA" and r0["cycle_id"] == "cyc-1" and r0["why"] == "because new")
check("ruled_ts present", isinstance(r0["ruled_ts"], float))
check("rule_detail got the same context and cycle_id as before", all(c == ("advances", "pursuit:pA", "cyc-1") for c in calls))
saved = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))
check("register: pending cleared, restate counted on refute, advance applied on confirm",
      saved[0]["pending"] == [] and saved[0]["restates"] == 1 and saved[0]["advances"] == 2)

print("[3] unavailable keeps pending (no row); dropped after retries logs a row")
pu._ACTIVE.write_text(json.dumps(reg(1), ensure_ascii=False), encoding="utf-8")
script["mode"] = "down"
n0 = len(pu.judged_rows(limit=100))
for i in range(pu._JUDGE_RETRIES):
    o = asyncio.run(pu.judge_pending())
    check(f"sweep {i + 1}: kept_pending, no new row", o["kept_pending"] == 1 and len(pu.judged_rows(limit=100)) == n0)
o = asyncio.run(pu.judge_pending())
check("final sweep: dropped", o["dropped"] == 1)
last = pu.judged_rows()[-1]
check("dropped row: verdict None, dropped True, how unavailable", last["verdict"] is None and last.get("dropped") is True and last["how"] == "unavailable")
script["mode"] = "by_text"

print("[4] a failing save logs nothing (items stay pending, would be re-judged)")
pu._ACTIVE.write_text(json.dumps(reg(), ensure_ascii=False), encoding="utf-8")
n1 = len(pu.judged_rows(limit=100))
orig_save = pu._save
def boom(items): raise OSError("disk")
pu._save = boom
asyncio.run(pu.judge_pending())
pu._save = orig_save
check("no rows written when the sweep dies before the flush", len(pu.judged_rows(limit=100)) == n1)

print("[5] bounded to JUDGED_KEEP, newest kept")
pu.JUDGED_KEEP = 50
big = [{"pursuit_id": "pB", "thought": "t" * 200, "prior_standing": "p" * 200, "why": "w" * 160, "verdict": True,
        "how": "agreed", "ruled_ts": float(i), "n": i, "question": "q" * 100, "thought_sha": "abc"} for i in range(2000)]
pu._flush_judged(big)
allr = pu.judged_rows(limit=100000)
check("trimmed to the cap", len(allr) == 50 and allr[-1]["n"] == 1999 and allr[0]["n"] == 1950)

print("[6] fail-open and kill switch")
pu.JUDGED_LOG = False
before = pu._judged_path().read_text(encoding="utf-8")
pu._flush_judged([{"x": 1}])
check("kill switch writes nothing", pu._judged_path().read_text(encoding="utf-8") == before)
pu.JUDGED_LOG = True
pu._DIR = TMP / "a_file_not_a_dir"
(TMP / "a_file_not_a_dir").write_text("x")
try:
    pu._flush_judged([{"x": 1}]); raised = False
except Exception:
    raised = True
check("an unwritable path never raises", not raised)
check("missing file reads as []", pu.judged_rows() == [])
pu._DIR = TMP

print("[7] reader join")
panel = [{"ts": 100.0, "key": "advances", "context": "pursuit:pA", "how": "agreed", "why1": "w"},
         {"ts": 200.0, "key": "advances", "context": "pursuit:pA", "how": "tiebreak", "why1": "w2"}]
joined = rd.join_panel([{"pursuit_id": "pA", "ruled_ts": 201.0}, {"pursuit_id": "pZ", "ruled_ts": 201.0}], panel)
check("nearest earlier panel row joined, other pursuit unjoined", joined[0]["panel"]["how"] == "tiebreak" and joined[1]["panel"] is None)
check("summarise counts", rd.summarise([{"verdict": True, "thought_sha": "a", "pursuit_id": "x"}, {"verdict": False, "thought_sha": "a", "pursuit_id": "x", "dropped": True}])["distinct_thoughts"] == 1)

print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

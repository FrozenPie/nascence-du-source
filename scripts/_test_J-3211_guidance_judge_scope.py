"""J-3211 / D-0600: guidance behaviour-delta judge re-scope. Checks, every store on a temp path, every model call stubbed:
  * _candidate_thoughts reads ONLY idle thoughts (origin inner_thought), newest first, bounded (a temp sqlite DB patched in
    for core.memory.store._connect, so the live store is never opened);
  * sweep() moves the cursor to the PRESENT, logs the skipped range (a cursor 40 days stale), never scores older rows
    (no backfill), only judges inner_thought rows, and a second sweep with nothing new scores nothing;
  * status() says 'unvalidated' and withholds rates until a control record passes on the CURRENT prompt and panel; legacy
    (unscoped) rows are excluded; a failing record, a stale prompt fingerprint, or a changed panel each keep it closed;
    a hand-edited 'passed' flag cannot open it;
  * the control harness separates stub judges correctly: perfect judge passes; coin flip, echo-fooled, always-false and
    always-true judges all FAIL; the case set is 8 principles x 4 classes, each thought within the input cap and different
    from its principle; record_result/control_status round-trip on a temp path.
Touches no live data: run from a worktree."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/
import asyncio
import json
import random
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
assert "c:\\nascence\\core" not in str(Path(core.__file__).resolve()).lower(), "run from a worktree, not the live tree"

from core import guidance_behavior_control as gc, guidance_behavior_judge as gbj  # noqa: E402
from core import guidance_learning as gl, judge_panel as jp  # noqa: E402
import core.memory.store as store  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="J-3211_"))
gbj._DATA = TMP
gbj._STATE = TMP / "state.json"
gbj._LOG = TMP / "shadow.jsonl"
gc.CONTROL_PATH = TMP / "control.json"
gbj.GUIDANCE_JUDGE_OFFLOOP = False

# ------------------------------------------------------------ a temp store with mixed origins
DB = TMP / "frag.db"
conn = sqlite3.connect(str(DB))
conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, timestamp REAL, origin TEXT)")
NOW = time.time()
OLD_CURSOR = NOW - 40 * 86400
rows = []
for i in range(300):   # 300 idle thoughts spread over 40 days, one every ~11.5 h, plus the last 30 in the last hours
    ts = OLD_CURSOR + 1 + i * (40 * 86400 / 300)
    rows.append((f"idle{i}", f"an idle thought number {i} about the garden and the sea and a long quiet", ts, "inner_thought"))
for i in range(40):
    rows.append((f"lived{i}", f"Q: Travis words {i} about commitment and the sea A: reply about the garden", OLD_CURSOR + 5000 + i * 90000, "lived"))
for i in range(5):
    rows.append((f"letter{i}", f"a letter {i} written about quiet things at length here", NOW - 1000 - i, "letter"))
conn.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?)", rows)
conn.commit()
conn.close()


def temp_connect():
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    return c


store._connect = temp_connect

# 1. candidates: idle only, newest first, bounded
cand = gbj._candidate_thoughts(OLD_CURSOR, 50)
assert len(cand) == 50 and all(r["fragment_id"].startswith("idle") for r in cand), [r["fragment_id"] for r in cand[:5]]
assert [r["timestamp"] for r in cand] == sorted((r["timestamp"] for r in cand), reverse=True), "must be newest first"
assert cand[0]["fragment_id"] == "idle299", cand[0]
n_between = gbj._skipped_between(OLD_CURSOR, cand[-1]["timestamp"])
assert n_between == 250, n_between   # idle0..idle249 lie between the old cursor and the oldest row read (idle250)
print("candidates: idle thoughts only, newest first, bounded; skip count =", n_between)

# 2. sweep: cursor jumps to the present, skipped range logged, no backfill, only idle rows judged
judged_ids, ruled = [], []
gl.injection_times = lambda: []
gl._best_belief = lambda text, mode=None: ({"id": "gTEST", "principle": "p", "domain": "self"}, 0.5) if "number" in text else None


async def fake_rule(system, user, key, context="", **kw):
    ruled.append(user)
    return True


async def fake_rule_detail(system, user, key, context="", **kw):
    return {"verdict": await fake_rule(system, user, key, context), "how": "agreed", "v1": True, "v2": True, "why": "mock why"}


jp.rule_detail = fake_rule_detail
gbj.SCAN_MAX = 200
gbj._STATE.write_text(json.dumps({"last_ts": OLD_CURSOR}), encoding="utf-8")
out = asyncio.run(gbj.sweep(max_items=15))
assert out["scanned"] == 200 and out["matched"] == 200 and out["judged"] == 15 and out["skipped"] == 100, out
log = [json.loads(l) for l in gbj._LOG.read_text(encoding="utf-8").splitlines()]
skips = [r for r in log if r.get("skip") == "newest-first-skip"]
assert len(skips) == 1 and skips[0]["n_skipped"] == 100 and skips[0]["cursor_lag_s"] > 39 * 86400, skips
aligned_rows = [r for r in log if "aligns" in r]
assert len(aligned_rows) == 15 and all(r["scope"] == "idle_v2" and r["fragment_id"].startswith("idle") for r in aligned_rows)
newest_ids = {f"idle{i}" for i in range(299, 284, -1)}
assert {r["fragment_id"] for r in aligned_rows} == newest_ids, "must judge the NEWEST idle thoughts first"
assert all("Travis" not in u and "letter" not in u for u in ruled), "no lived/letter text may reach the judge"
st = json.loads(gbj._STATE.read_text(encoding="utf-8"))
assert st["last_ts"] == cand[0]["timestamp"] and st["scope"] == "idle_v2", st
# the letters (newer than the last idle thought) were not read: origin-restricted, not merely ordered
assert not any(r["fragment_id"].startswith(("letter", "lived")) for r in log if "fragment_id" in r)
out2 = asyncio.run(gbj.sweep(max_items=15))
assert out2["scanned"] == 0 and out2["judged"] == 0, out2
# J-3095: rule_detail's why/votes logged, cursor lag reported, whole thought shown, origin recorded, answer half only
assert out["cursor_lag_s"] > 39 * 86400, out
assert all(r["why"] == "mock why" and r["how"] == "agreed" and r["v1"] is True and r["origin"] == "inner_thought"
           and r["cursor_lag_s"] > 39 * 86400 and r["text_truncated"] is False for r in aligned_rows), aligned_rows[0]
assert gbj._THOUGHT_CAP >= 2000 and gbj.build_user("p", "x" * 1500).count("x") == 1500
assert gbj.answer_half("Q: Travis says name the cat A: I would call him Ash") == "I would call him Ash"
assert gbj.answer_half("Q: only a question") == "" and gbj.answer_half("a plain idle thought") == "a plain idle thought"
print("sweep: cursor jumped to the present, 100 older idle thoughts logged as skipped (not scored), newest 15 judged, nothing re-scored")

# 3. status gate
fp, panel = gbj.prompt_fingerprint(), gbj._panel_now()
legacy = {"ts": 1.0, "fragment_id": "old", "aligns": True, "primed": False}   # pre-J-3211 row: no scope
with open(gbj._LOG, "a", encoding="utf-8") as f:
    f.write(json.dumps(legacy) + "\n")
s0 = gbj.status()
assert s0["verdict"].startswith("unvalidated") and s0["rates_withheld"] and s0["legacy_rows_excluded"] == 1, s0
assert "prompted_alignment_rate" not in s0 and "unprompted_alignment_rate" not in s0 and s0["judged"] == 15, s0
assert "INTERNALIZED" not in json.dumps(s0)
assert s0["n_by_origin"] == {"inner_thought": 15}, s0
GOOD = {"enacted": 1.0, "echoed": 0.0, "ignored_topical": 0.0, "ignored_unrelated": 0.0}
res_ok = {"passed": True, "rates": GOOD, "coverage": 1.0, "repeats": 3, "n_cases": 32, "how": {}}
gc.record_result(res_ok, panel, fp)
s1 = gbj.status()
assert s1["control"]["valid"] and "unprompted_alignment_rate" in s1 and not s1["verdict"].startswith("unvalidated"), s1
assert s1["unprompted_n"] == 15 and s1["verdict"].startswith("UNPROMPTED RATE ONLY"), s1
# a failing control keeps it closed, and a hand-edited passed flag cannot open it
BAD = {"enacted": 1.0, "echoed": 1.0, "ignored_topical": 0.0, "ignored_unrelated": 0.0}
gc.record_result({**res_ok, "passed": True, "rates": BAD}, panel, fp)   # claims passed, rates say otherwise
s2 = gbj.status()
assert not s2["control"]["valid"] and s2["verdict"].startswith("unvalidated") and "echoed" in s2["control"]["reason"], s2
# stale fingerprint, changed panel
gc.record_result(res_ok, panel, "deadbeefdeadbeef")
assert "DIFFERENT prompt" in gbj.status()["control"]["reason"]
gc.record_result(res_ok, {**panel, "tiebreak": "http://elsewhere:1"}, fp)
assert "DIFFERENT judge panel" in gbj.status()["control"]["reason"]
gc.CONTROL_PATH.write_text("{not json", encoding="utf-8")
assert gbj.status()["verdict"].startswith("unvalidated")
gc.CONTROL_PATH.unlink()
assert "never run" in gbj.status()["control"]["reason"]
# a prompt change moves the fingerprint (so the gate would close by itself)
old_sys = gbj._SYSTEM
gbj._SYSTEM = old_sys + " "
assert gbj.prompt_fingerprint() != fp
gbj._SYSTEM = old_sys
assert gbj.prompt_fingerprint() == fp
print("status gate: unvalidated until the control passes (no control / failed / stale prompt / changed panel / corrupt file);",
      "legacy rows excluded; hand-edited flag cannot open it; validated shows rates ->", s1["verdict"])

# 4. the control harness
assert len(gc.CASES) == 32 and {c["cls"] for c in gc.CASES} == set(gc.CLASSES)
assert len({c["principle_id"] for c in gc.CASES}) == 8
for c in gc.CASES:
    assert len(c["thought"]) <= gbj._THOUGHT_CAP and len(c["principle"]) <= gbj._PRINCIPLE_CAP, c["id"]
    assert c["thought"] != c["principle"] and len(c["thought"]) >= gbj.MIN_LEN
user_to_cls = {gbj.build_user(c["principle"], c["thought"]): c["cls"] for c in gc.CASES}
assert len(user_to_cls) == 32, "every case must produce a distinct user message"


def mk(fn):
    async def judge(system, user, ctx):
        assert system == gbj._SYSTEM and user in user_to_cls   # the control sends the module's own prompt, via build_user
        return {"verdict": fn(user_to_cls[user]), "how": "agreed"}
    return judge


rng = random.Random(7)
cases = {"perfect": (mk(lambda c: c == "enacted"), True),
         "coin_flip": (mk(lambda c: rng.random() < 0.5), False),
         "echo_fooled": (mk(lambda c: c in ("enacted", "echoed")), False),
         "always_false": (mk(lambda c: False), False),
         "always_true": (mk(lambda c: True), False),
         "topical_fooled": (mk(lambda c: c != "ignored_unrelated"), False)}
for name, (j, want) in cases.items():
    r = asyncio.run(gc.run_control(j, repeats=3))
    assert r["passed"] is want, (name, r["rates"], r["failed"])
    assert r["n_cases"] == 32 and sum(sum(v.values()) for v in r["by_class"].values()) == 96
print("harness: perfect judge passes; coin flip, echo-fooled, topical-fooled, always-false, always-true all fail")


async def mostly_unavailable(system, user, ctx):
    return {"verdict": (user_to_cls[user] == "enacted") if rng.random() < 0.3 else None, "how": "unavailable"}


r = asyncio.run(gc.run_control(mostly_unavailable, repeats=3))
assert not r["passed"] and any("coverage" in f for f in r["failed"]), r
print("harness: a panel that mostly returns no verdict does not pass (coverage bar)")

# 5. record/read round trip on a temp path through the real runner's building blocks
rr = asyncio.run(gc.run_control(cases["perfect"][0], repeats=3))
gc.record_result(rr, panel, fp)
assert gbj.status()["control"]["valid"]
assert Path(gc.CONTROL_PATH).parent == TMP
print("OK")

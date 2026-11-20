"""J-2194 / D-0432 (a): push_hint reachability pre-check (sized safe by F-2896).

Covers: reachable push, unreachable refusal (no cap spent), body-state via percepts_available,
no-tick fail-open, read-error fail-open, the scan-row bound, and the HINT_PUSH_PRECHECK kill switch.
Runs inside lab_env.isolate(db="empty") with Lane 2's _LOG/_HINTS/_DATA redirected into the lab dir;
never reads or writes Du's live lane2 files. Run from the worktree root:
    J2194_WT=<worktree> python scripts/test_lane2_push_precheck_J2194.py
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core as _core_pkg  # noqa: E402  BEFORE lab_env (F-2423): the tree under test must win on sys.path
wt = os.environ.get("J2194_WT")
if wt:
    assert os.path.abspath(_core_pkg.__file__).lower().startswith(os.path.abspath(wt).lower()), _core_pkg.__file__
import core.lane2 as L  # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402


def rows(path):
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def write_log(path, recs):
    path.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")


def reset(lab):
    for p in (L._LOG, L._HINTS):
        if p.exists():
            p.unlink()


with isolate(also=[(L, ["_LOG", "_HINTS", "_DATA"])], db="empty") as lab:
    assert str(L._LOG).startswith(str(lab)) and str(L._HINTS).startswith(str(lab)), (L._LOG, L._HINTS)
    now = time.time()
    tick = {"ts": now - 120, "kind": "tick", "world_fields": ["fire", "warmth", "sounds"],
            "percepts_available": ["world", "body"]}

    # 1. reachable: pushed, row carries reach_at_push True + tick age
    reset(lab); write_log(L._LOG, [tick, {"ts": now - 60, "kind": "skip", "skip": "x"}])
    r = L.push_hint("unresolved", "fire")
    assert r == {"ok": True, "tag": "unresolved: fire"}, r
    last = rows(L._LOG)[-1]
    assert last["kind"] == "hint_pushed" and last["reach_at_push"] is True, last
    assert 100 <= last["tick_age_s"] <= 200, last

    # 2. unreachable: refused before the queue/rate cap is touched
    before = json.loads(L._HINTS.read_text(encoding="utf-8"))
    r = L.push_hint("recheck", "cat")
    assert r == {"ok": False, "reason": "unreachable-at-push"}, r
    last = rows(L._LOG)[-1]
    assert last["kind"] == "hint_rejected" and last["reason"] == "unreachable-at-push", last
    assert last["hint_topic"] == "cat" and last["tick_age_s"] is not None, last
    after = json.loads(L._HINTS.read_text(encoding="utf-8"))
    assert after["push_log"] == before["push_log"] and after["queue"] == before["queue"], (before, after)

    # 3. body-state reads percepts_available (tick row's name for `available`)
    assert L.push_hint("unfinished", "body-state")["ok"] is True
    write_log(L._LOG, [dict(tick, percepts_available=["world"])])
    assert L.push_hint("unfinished", "body-state")["reason"] == "unreachable-at-push"

    # 4. no tick row at all -> exactly as before (pushed, reach_at_push None)
    reset(lab); write_log(L._LOG, [{"ts": now, "kind": "skip", "skip": "x"}])
    r = L.push_hint("recheck", "cat")
    assert r["ok"] is True, r
    last = rows(L._LOG)[-1]
    assert last["reach_at_push"] is None and last["tick_age_s"] is None, last
    reset(lab)   # missing log file entirely
    assert L.push_hint("recheck", "cat")["ok"] is True

    # 5. read error -> fail-open
    reset(lab); write_log(L._LOG, [dict(tick, world_fields=[])])
    orig = L._latest_tick_row
    def boom(*a, **k):
        raise OSError("simulated read error")
    L._latest_tick_row = boom
    try:
        assert L._push_reachability("cat", now) == (None, None)
        assert L.push_hint("recheck", "cat")["ok"] is True
    finally:
        L._latest_tick_row = orig

    # 6. scan bound: a tick older than HINT_PRECHECK_SCAN_ROWS rows is not used (fail-open)
    reset(lab)
    write_log(L._LOG, [dict(tick, world_fields=[])] + [{"ts": now, "kind": "skip"}] * 5)
    assert L._latest_tick_row(scan_rows=3) is None
    assert L._latest_tick_row(scan_rows=10)["kind"] == "tick"
    write_log(L._LOG, [dict(tick, world_fields=[])] + ["not json"] * 0)
    assert L._push_reachability("cat", now)[0] is False

    # 7. kill switch off: unreachable is pushed as before, shadow field still logged
    reset(lab); write_log(L._LOG, [dict(tick, world_fields=[])])
    L.HINT_PUSH_PRECHECK = False
    try:
        r = L.push_hint("recheck", "cat")
        assert r["ok"] is True, r
        assert rows(L._LOG)[-1]["reach_at_push"] is False
    finally:
        L.HINT_PUSH_PRECHECK = True

    # 8. out-of-vocabulary still refused first, consume path unchanged
    assert L.push_hint("recheck", "dragon")["reason"] == "out-of-vocabulary"
    q = L._consume_hint({"world_fields": ["cat_at"], "available": []}, time.time())
    assert q and q["topic"] == "cat", q
    reset(lab)

print("ok")

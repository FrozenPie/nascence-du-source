"""
Hermetic test for J-3177 (D-0565): resting as a legitimate dream ending (core/dream_rest.py), its three readers
(nodes/dream_node._last_unresolved_arc = the carry, core/dream_met.py = met-state, core/closure.py = the closure
writer's rest_close rows) and the du_pulse summary.

No LLM, no embedder, no live data. Runs INSIDE lab_env.isolate(db="empty") with every module-level store path
redirected into the lab dir via `also=`. The real data/ tree is never opened for writing.

  [1] arc_ending classification (met-core / rest / open / unknown), incl. a panel-flipped label
  [2] the carry: off = legacy and no log; shadow = legacy return + one would-do row; live = a rest arc is NOT returned,
      a stalled arc is; the label's resolved-vs-unfaced swap changes nothing (D-0580)
  [3] dream_met: carry_thread_root unchanged in shadow, 'none' for a rest arc in live; compute_states stamps 'ending'
      on the state row (off: no key); the met-driven closure row carries 'ending'
  [4] closure: rest_close rows -- only recent rest arcs, one per arc, certified ONLY by an independent judge
      (panel True / dream_met met), the rest itself never certifies; nothing written to the memory DB even with
      CLOSURE_WRITE_LIVE True (store_fragment / _write_live patched to raise)
  [5] summarize() and source defaults

Run:  python scripts/dream_rest_test.py   (from the tree under test)
"""
from __future__ import annotations
import datetime, hashlib, json, sqlite3, sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423): the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.dream_met as dm
import core.closure as cl
import core.dream_rest as dr
import nodes.dream_node as dn
from core.memory import store as _store
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate, _hash_file

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

DIM = 384
def basis(i):
    v = np.zeros(DIM, np.float32); v[i] = 1.0; return v
def noise(rng):
    v = rng.standard_normal(DIM).astype(np.float32); v[:40] = 0.0
    return v / np.linalg.norm(v)
TABLE: dict[str, np.ndarray] = {}
def fake_embed(text):
    if text in TABLE: return TABLE[text]
    r = np.random.default_rng(int(hashlib.md5(text.encode()).hexdigest()[:8], 16))
    v = r.standard_normal(DIM).astype(np.float32); v[:100] = 0.0
    return v / np.linalg.norm(v)
dm._embed_fn = fake_embed

D0 = datetime.date(2026, 6, 1)
def ts_of(day, hour=12):
    return datetime.datetime.combine(D0 + datetime.timedelta(days=day), datetime.time(hour)).timestamp()
def arc(i, day, tension, close_reason="ended-unfaced", unresolved=True, carried_n=0):
    return {"ts": ts_of(day, 3), "dream_id": f"dream_{i}", "scenes": 4, "close_reason": close_reason,
            "ended_unresolved": unresolved, "carried_n": carried_n, "seed": {"tension_labels": [tension]},
            "final_unresolved_core": "the unspent thing" if unresolved else "", "final_narrative": f"tail of {i}",
            "final_symbols": ["door"], "narrative": f"narr {i}"}

with isolate(db="empty", also=[(dm, ["DREAM_LOG", "STATE_LOG", "MASS_LOG", "TENSION_STATE_FILE"]),
                               (dn, ["_DREAM_LOG", "_MET_CARRY_SHADOW_LOG", "_RESOLUTION_SHADOW_LOG"]),
                               (cl, ["SHADOW_LOG"]),
                               (dr, ["DREAM_LOG", "REST_SHADOW_LOG", "RESOLUTION_SHADOW_LOG"])]) as lab:
    check("store.DB_PATH redirected into the lab dir", Path(_store.DB_PATH).resolve().is_relative_to(lab.resolve()))
    check("every redirected path is inside the lab dir",
          all(Path(p).resolve().is_relative_to(lab.resolve()) for p in
              (dm.DREAM_LOG, dm.STATE_LOG, dm.MASS_LOG, dm.TENSION_STATE_FILE, dn._DREAM_LOG, dn._MET_CARRY_SHADOW_LOG,
               dn._RESOLUTION_SHADOW_LOG, cl.SHADOW_LOG, dr.DREAM_LOG, dr.REST_SHADOW_LOG, dr.RESOLUTION_SHADOW_LOG)))
    dn._DREAM_LOG = dm.DREAM_LOG
    dr.DREAM_LOG = dm.DREAM_LOG
    dn._RESOLUTION_SHADOW_LOG = dr.RESOLUTION_SHADOW_LOG
    LABDB = Path(_store.DB_PATH)
    db_hash0 = _hash_file(LABDB)

    def writelog(arcs):
        dm.DREAM_LOG.parent.mkdir(parents=True, exist_ok=True)
        dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in arcs), encoding="utf-8")
    def rest_rows():
        return dr._read_jsonl(dr.REST_SHADOW_LOG)

    # ---------------------------------------------------------------------------------------------
    print("\n[1] arc_ending")
    A = dr.arc_ending
    check("empty core -> met-core (whatever the label)", A({"ended_unresolved": False, "close_reason": "resolved"}) == "met-core"
          and A({"ended_unresolved": False, "close_reason": "ended-unfaced"}) == "met-core")
    check("ended-unfaced + core -> rest", A({"ended_unresolved": True, "close_reason": "ended-unfaced"}) == "rest")
    check("panel-flipped 'resolved' with a named core is still rest (D-0580: the label swap is not read)",
          A({"ended_unresolved": True, "close_reason": "resolved"}) == "rest")
    check("stalled / dropped / ceiling -> open", all(A({"ended_unresolved": True, "close_reason": c}) == "open" for c in ("stalled", "dropped", "ceiling")))
    check("no close_reason (pre-08-22 row) -> unknown, not rest", A({"ended_unresolved": True}) == "unknown")

    # ---------------------------------------------------------------------------------------------
    print("\n[2] the carry (nodes/dream_node.py _last_unresolved_arc)")
    node = dn.DreamNode()
    rest_arc, open_arc = arc(1, 30, "tens0"), arc(2, 30, "tens0", close_reason="stalled")
    flipped = arc(3, 30, "tens0", close_reason="resolved")
    legacy = lambda a: {"narrative": a["final_narrative"], "symbols": a["final_symbols"][:3], "unresolved_core": a["final_unresolved_core"]}
    dr.RESTING_ENDING = "off"
    writelog([rest_arc]); out = node._last_unresolved_arc()
    check("off: a rest arc is returned exactly as before, nothing logged", out == legacy(rest_arc) and not rest_rows())
    dr.RESTING_ENDING = "shadow"
    out = node._last_unresolved_arc(); r = rest_rows()
    check("shadow: the rest arc is still returned (carry unchanged)", out == legacy(rest_arc))
    check("shadow: one row, ending rest, would_return False, carry_changed False",
          len(r) == 1 and r[0]["ending"] == "rest" and r[0]["would_return"] is False and r[0]["carry_changed"] is False and r[0]["mode"] == "shadow")
    writelog([open_arc]); out = node._last_unresolved_arc(); r = rest_rows()
    check("shadow: a stalled arc is returned and the row says would_return True", out == legacy(open_arc) and r[-1]["would_return"] is True and r[-1]["ending"] == "open")
    dr.RESTING_ENDING = "live"
    writelog([rest_arc]); n0 = len(rest_rows())
    check("live: a rest arc is NOT returned (the carry falls)", node._last_unresolved_arc() is None)
    check("live row says carry_changed True", rest_rows()[n0]["carry_changed"] is True and rest_rows()[n0]["mode"] == "live")
    writelog([flipped])
    check("live: the panel-swapped 'resolved' label changes nothing (still a rest, not returned)", node._last_unresolved_arc() is None)
    writelog([open_arc])
    check("live: a stalled arc IS returned (unfinished business keeps its carry)", node._last_unresolved_arc() == legacy(open_arc))
    writelog([arc(4, 30, "tens0", close_reason="resolved", unresolved=False)])
    check("live: an arc with an empty core still returns None (legacy)", node._last_unresolved_arc() is None)
    writelog([{"ts": 1.0, "dream_id": "old", "ended_unresolved": True, "final_unresolved_core": "x", "final_narrative": "y"}])
    check("live: a pre-close_reason row (unknown) keeps the legacy carry", node._last_unresolved_arc() is not None)
    real_append = dr._append
    dr._append = lambda *a, **k: (_ for _ in ()).throw(OSError("disk"))
    writelog([rest_arc])
    check("a failing log write fails open to the legacy carry (even in live)", node._last_unresolved_arc() == legacy(rest_arc))
    dr._append = real_append

    # ---------------------------------------------------------------------------------------------
    print("\n[3] dream_met: thread root + 'ending' on the state row")
    chain = [arc(10, 30, "tens0", close_reason="stalled"), arc(11, 31, "tens0", close_reason="ended-unfaced", carried_n=1)]
    writelog(chain)
    for m in ("off", "shadow"):
        dr.RESTING_ENDING = m
        check(f"{m}: carry_thread_root is the legacy walk-back (root = dream_10)", (dm.carry_thread_root() or {}).get("dream_id") == "dream_10")
    dr.RESTING_ENDING = "live"
    check("live: the last arc ended at rest -> no thread", dm.carry_thread_root() is None and dm.thread_state(now=ts_of(32, 3))["state"] == "none")
    writelog([arc(10, 30, "tens0", close_reason="stalled"), arc(11, 31, "tens0", close_reason="stalled", carried_n=1)])
    check("live: an open (stalled) last arc still has its thread root", (dm.carry_thread_root() or {}).get("dream_id") == "dream_10")

    DB = lab / "waking_synthetic.db"
    dm._db_path = lambda: DB
    rng = np.random.default_rng(7)
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE memory_fragments (fragment_id TEXT, origin TEXT, timestamp REAL, embedding BLOB, content TEXT)")
    rows = []
    for day in range(0, 45):
        for h in range(8):
            rows.append((f"f{len(rows)}", "study" if h == 0 else "inner_thought", ts_of(day, 6 + h), noise(rng).tobytes(), "x"))
    for d in (10, 20):                                   # baseline recurrences of axis 0, none after day 30
        rows.append((f"b{d}", "inner_thought", ts_of(d, 20), basis(0).tobytes(), "x"))
    con.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", rows); con.commit(); con.close()
    TABLE.update({"tens0": basis(0), "the unspent thing": noise(np.random.default_rng(3))})
    cl._compose_fn = lambda s, u: {"resolution": "I kept returning to it. It stopped."}
    cl.CLOSURE_WRITE_LIVE = False
    dm.TENSION_STATE_FILE.write_text(json.dumps({"tensions": []}), encoding="utf-8")
    NOW = ts_of(40, 22)
    for mode_, want in (("off", False), ("shadow", True)):
        dr.RESTING_ENDING = mode_
        writelog([arc(0, 30, "tens0")])                  # a rest arc whose tension the waking mind stopped returning to
        dm.STATE_LOG.unlink(missing_ok=True); cl.SHADOW_LOG.unlink(missing_ok=True)
        dm.run_nightly(NOW)
        srow = dm.latest_states().get("dream_0") or {}
        check(f"{mode_}: the met state row {'carries' if want else 'has no'} 'ending'", srow.get("state") == "met" and (("ending" in srow) == want) and (not want or srow["ending"] == "rest"))
        res = cl.shadow_rows(arm="dream", kind="resolution")
        check(f"{mode_}: the met-driven closure row {'carries' if want else 'has None for'} the ending",
              len(res) == 1 and res[0]["ending"] == ("rest" if want else None))

    # ---------------------------------------------------------------------------------------------
    print("\n[4] closure: a rest is read as a close CANDIDATE, certified only by an independent judge")
    dr.RESTING_ENDING = "shadow"
    cl.CLOSURE_WRITE_LIVE = True                         # the strongest setting: still nothing may be written for a rest
    def boom(*a, **k): raise AssertionError("a rest close tried to write to the memory DB")
    _real_wl, _real_sf = cl._write_live, _store.store_fragment
    cl._write_live = boom; _store.store_fragment = boom
    NOW4 = ts_of(60, 12)
    def a4(i, reason, hours_ago=3.0, unresolved=True):
        a = arc(i, 0, "tens0", close_reason=reason, unresolved=unresolved); a["ts"] = NOW4 - hours_ago * 3600; return a
    writelog([a4(100, "ended-unfaced"), a4(101, "ended-unfaced"), a4(102, "ended-unfaced"), a4(103, "stalled"),
              a4(104, "resolved", unresolved=False), a4(105, "ended-unfaced", hours_ago=24 * 5), a4(106, "ended-unfaced")])
    dr.RESOLUTION_SHADOW_LOG.write_text(
        json.dumps({"dream_id": "dream_101", "judge_verdict": True, "judge_how": "agreed"}) + "\n"
        + json.dumps({"dream_id": "dream_100", "judge_verdict": False, "judge_how": "agreed"}) + "\n"
        + json.dumps({"dream_id": "dream_106", "judge_verdict": None, "judge_how": "unavailable"}) + "\n", encoding="utf-8")
    dm._append(dm.STATE_LOG, {"dream_id": "dream_102", "state": "met", "computed_at": 1.0, "params": {}})
    cl.SHADOW_LOG.unlink(missing_ok=True)
    out = cl.record_rest_closes(now=NOW4)
    by_id = {r["arc_id"]: r for r in out}
    check("only the recent REST arcs get a row (not stalled, not empty-core, not 5 days old): 100,101,102,106", sorted(by_id) == ["dream_100", "dream_101", "dream_102", "dream_106"])
    check("a rest with no judge verdict for it is NOT certified (panel False)", by_id["dream_100"]["certified"] is False and by_id["dream_100"]["certified_by"] == [] and by_id["dream_100"]["panel_verdict"] is False)
    check("panel True certifies", by_id["dream_101"]["certified"] is True and by_id["dream_101"]["certified_by"] == ["resolution_panel"])
    check("dream_met 'met' certifies", by_id["dream_102"]["certified"] is True and by_id["dream_102"]["certified_by"] == ["dream_met"])
    check("panel unavailable (None) is NOT certified", by_id["dream_106"]["certified"] is False and by_id["dream_106"]["panel_verdict"] is None)
    check("every row: would_write False, written_live False, no fragment id, no composed text",
          all(r["would_write"] is False and r["written_live"] is False and r["fragment_id"] is None and "would_be" not in r for r in out))
    check("rows are in closure_shadow as kind='rest_close'", len(cl.shadow_rows(arm="dream", kind="rest_close")) == 4)
    check("idempotent: a second pass appends nothing", cl.record_rest_closes(now=NOW4) == [] and len(cl.shadow_rows(kind="rest_close")) == 4)
    check("one-fragment-per-loop dedupe is untouched (no 'resolution' row, already_resolved is None)", not cl.shadow_rows(kind="resolution") and cl.already_resolved("dream", "dream_101") is None)
    cl._write_live, _store.store_fragment = _real_wl, _real_sf
    check("memory DB byte-identical", _hash_file(LABDB) == db_hash0)
    dr.RESTING_ENDING = "off"; before = len(cl.shadow_rows())
    dm.run_nightly(NOW4)
    check("off: run_nightly makes no rest_close call", len(cl.shadow_rows(kind="rest_close")) == 4 and len(cl.shadow_rows()) >= before)
    dr.RESTING_ENDING = "shadow"
    writelog([a4(107, "ended-unfaced")]); n = len(cl.shadow_rows(kind="rest_close"))
    out = dm.run_nightly(NOW4)
    check("shadow: run_nightly calls it (one new row for the new rest arc)", len(out.get("rest_closes") or []) == 1 and len(cl.shadow_rows(kind="rest_close")) == n + 1)
    cl.CLOSURE_WRITE_LIVE = True

    # ---------------------------------------------------------------------------------------------
    print("\n[5] summarize + source defaults")
    writelog([arc(1, 30, "t"), arc(2, 30, "t", close_reason="stalled"), arc(3, 30, "t", unresolved=False, close_reason="resolved")])
    dr.REST_SHADOW_LOG.write_text(json.dumps({"ts": 5.0, "kind": "carry", "would_return": False}) + "\n"
                                  + json.dumps({"ts": 6.0, "kind": "carry", "would_return": True}) + "\n", encoding="utf-8")
    sm = dr.summarize(since_ts=0.0)
    check("summarize: endings rest 1 / open 1 / met-core 1, consulted 2, would_return 1, would_end 1",
          sm["endings"]["rest"] == 1 and sm["endings"]["open"] == 1 and sm["endings"]["met-core"] == 1 and sm["consultations"] == 2
          and sm["would_return"] == 1 and sm["would_end"] == 1)

# source defaults, read AFTER the isolate block restored the module paths
import importlib
fresh = importlib.reload(dr)
check("source default RESTING_ENDING is 'shadow' (restart-gated, the founder flips it)", fresh.RESTING_ENDING == "shadow")
check("dream_rest's panel-log path matches nodes/dream_node's", fresh.RESOLUTION_SHADOW_LOG == dn._RESOLUTION_SHADOW_LOG)
check("closure never gained a writer: record_rest_closes source has no store_fragment / _write_live call",
      "_write_live(" not in cl.record_rest_closes.__code__.co_names and "store_fragment" not in cl.record_rest_closes.__code__.co_names)

print("\nRESULT:", "ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

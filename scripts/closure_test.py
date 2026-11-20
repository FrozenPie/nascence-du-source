"""
Hermetic test for J-2118 (D-0423 A): the closure law's DREAM ARM in shadow (core/closure.py), the provisional-met
carry rule (core/dream_met.provisional_arc / thread_state, nodes/dream_node._met_carry_check,
PROVISIONAL_MET_ENDS_CARRY), and the run_nightly -> closure hook.

No LLM, no embedder, no live data. Runs INSIDE lab_env.isolate(db="empty") (core.memory.store.DB_PATH redirected
to the lab dir) with every module-level store path redirected into the same lab dir via `also=`; the waking-thought
store is a synthetic sqlite file in that lab dir; the embedder and the composer are deterministic fakes. The real
data/ tree is never opened for writing (the caller fingerprints C:/Nascence/data before/after).

  [1] provisional_arc: met / unmet / no-baseline / pending (0 days elapsed) / unobs / D-0233 injected tail excluded
  [2] provisional_state + thread_state end-to-end on a synthetic dream_log + sqlite; computed-final roots skip it
  [3] carry check: shadow logs would_end(provisional) and changes nothing; live ends it; flag False = old path;
      'off' writes nothing; closure_shadow receives one kind='carry' row per provisional consultation
  [4] resolution shadow: run_nightly on a met arc -> one kind='resolution' row with origin 'resolution' + a
      'resolves' edge to the thread root; written_live False; lab DB byte-identical; idempotent on re-run;
      a second met arc of the same thread -> kind='duplicate'; composer failure -> row kept, text None
  [5] CLOSURE_WRITE_LIVE True (stubbed store_fragment/add_edge): the live path passes exactly the would-be args;
      flag False never calls either; source defaults are False / True / "shadow"
  [6] pursuit + interrogation arms are stubs naming their gates

Run:  python scripts/closure_test.py   (from the tree under test)
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
def arc(i, day, tension, tail=None, carried_n=0, core_text=""):
    return {"ts": ts_of(day, 3), "dream_id": f"dream_{i}", "close_reason": "ended-unfaced", "ended_unresolved": True,
            "carried_n": carried_n, "seed": {"tension_labels": [tension]}, "final_unresolved_core": core_text,
            "final_narrative": tail or f"tail of {i}"}

with isolate(db="empty", also=[(dm, ["DREAM_LOG", "STATE_LOG", "MASS_LOG", "TENSION_STATE_FILE"]),
                               (dn, ["_DREAM_LOG", "_MET_CARRY_SHADOW_LOG"]),
                               (cl, ["SHADOW_LOG"])]) as lab:
    check("store.DB_PATH redirected into the lab dir", Path(_store.DB_PATH).resolve().is_relative_to(lab.resolve()))
    check("every redirected path is inside the lab dir",
          all(Path(p).resolve().is_relative_to(lab.resolve()) for p in
              (dm.DREAM_LOG, dm.STATE_LOG, dm.MASS_LOG, dm.TENSION_STATE_FILE, dn._DREAM_LOG, dn._MET_CARRY_SHADOW_LOG, cl.SHADOW_LOG)))
    dn._DREAM_LOG = dm.DREAM_LOG          # the node reads the same synthetic log the judge reads
    LABDB = Path(_store.DB_PATH)
    db_hash0 = _hash_file(LABDB)
    DB = lab / "waking_synthetic.db"      # the synthetic waking store (dream_met reads it ?mode=ro)
    dm._db_path = lambda: DB

    # ---------------------------------------------------------------------------------------------
    print("\n[1] provisional_arc (pure)")
    rng = np.random.default_rng(7)
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE memory_fragments (fragment_id TEXT, origin TEXT, timestamp REAL, embedding BLOB, content TEXT)")
    rows = []
    def thought(day, v, hour, origin="inner_thought"):
        rows.append((f"f{len(rows)}", origin, ts_of(day, hour), v.astype(np.float32).tobytes(), "x"))
    for day in range(0, 40):
        if day == 36: continue                                    # day 36 unobserved
        for h in range(8):
            thought(day, noise(rng), 6 + h, "study" if h == 0 else "inner_thought")
    # baselines: axis0 days 10,20 (clean after); axis1 days 12,22 + recurrence day 31; axis3 days 14,24 + tail-injected day 31
    for ax, days in {0: (10, 20), 1: (12, 22, 31), 3: (14, 24, 31), 5: (14, 24)}.items():
        for d in days: thought(d, basis(ax), 20)
    con.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", rows); con.commit(); con.close()
    TABLE.update({"tens0": basis(0), "tens1": basis(1), "tens2": basis(2), "tens3": basis(3), "tens5": basis(5), "tail3": basis(3)})
    W, w_ts, first = dm._load_waking(DB, 0.0)
    fd = dm._day(first)
    def prov(ax, arc_day, today_day, tails=()):
        tts = [ts_of(d, 3) for d, _ in tails]; tV = np.stack([v for _, v in tails]) if tails else np.zeros((0, DIM), np.float32)
        return dm.provisional_arc(ts_of(arc_day, 3), basis(ax)[None, :], W, w_ts, tts, tV, dm._day(ts_of(today_day, 3)), fd)
    s, d = prov(0, 30, 32)
    check("baseline real + day 31 clean -> provisional_met (1 day elapsed)", s == "provisional_met" and d["elapsed_days"] == 1 and d["baseline_days"] == 2)
    check("day-31 recurrence -> provisional_unmet", prov(1, 30, 32)[0] == "provisional_unmet")
    check("no baseline -> no-baseline", prov(2, 30, 32)[0] == "no-baseline")
    check("consulted the next night (0 complete days elapsed) -> pending", prov(0, 30, 31)[0] == "pending")
    check("an elapsed day unobserved -> unobs", prov(5, 35, 37)[0] == "unobs")
    check("D-0233: a day-31 recurrence that is the dream's own tail is excluded -> provisional_met",
          prov(3, 30, 32, tails=[(30, basis(3))])[0] == "provisional_met" and prov(3, 30, 32)[0] == "provisional_unmet")
    check("two clean days elapsed still provisional_met", prov(0, 30, 33)[0] == "provisional_met")
    check("noT", dm.provisional_arc(ts_of(30, 3), None, W, w_ts, [], np.zeros((0, DIM), np.float32), 1, fd)[0] == "noT")

    # ---------------------------------------------------------------------------------------------
    print("\n[2] provisional_state / thread_state on a synthetic log")
    chain = [arc(10, 30, "tens0"), arc(11, 31, "tens0", carried_n=1)]
    dm.DREAM_LOG.parent.mkdir(parents=True, exist_ok=True)
    dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in chain), encoding="utf-8")
    NOW = ts_of(32, 3)
    ts = dm.thread_state(now=NOW)
    check("root = dream_10, computed state unrecorded, provisional_met", ts["root"] == "dream_10" and ts["state"] == "unrecorded" and ts["provisional_state"] == "provisional_met")
    check("provisional=False -> the old shape (provisional_state None)", dm.thread_state(now=NOW, provisional=False)["provisional_state"] is None)
    dm._append(dm.STATE_LOG, {"dream_id": "dream_10", "state": "unmet", "computed_at": 1.0, "params": {}})
    check("a computed-final root skips the provisional half", dm.thread_state(now=NOW)["provisional_state"] is None)
    dm._append(dm.STATE_LOG, {"dream_id": "dream_10", "state": "pending", "computed_at": 2.0, "params": {}})
    check("a 'pending' root gets the provisional half", dm.thread_state(now=NOW)["provisional_state"] == "provisional_met")
    check("provisional states never reach dream_met_state.jsonl",
          all(r["state"] not in dm.PROVISIONAL_STATES for r in dm._read_jsonl(dm.STATE_LOG)))
    dm._db_path = lambda: lab / "missing.db"
    check("a failing provisional read is 'error', the rest intact", dm.thread_state(now=NOW)["provisional_state"] == "error")
    dm._db_path = lambda: DB

    # ---------------------------------------------------------------------------------------------
    print("\n[3] carry check in nodes/dream_node.py")
    import time as _time
    node = dn.DreamNode()
    carried_in = {"narrative": "x", "symbols": [], "unresolved_core": "y"}
    _real_time = _time.time
    _time.time = lambda: NOW                                      # thread_state() inside the node uses time.time()
    try:
        dn.MET_ENDS_CARRY = "shadow"; dn.PROVISIONAL_MET_ENDS_CARRY = True
        out, n = node._met_carry_check(dict(carried_in), 2)
        check("shadow: carry returned unchanged", out == carried_in and n == 2)
        srow = dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)
        check("shadow: would_end_carry True by 'provisional', carry_changed False, root_state pending",
              len(srow) == 1 and srow[0]["would_end_carry"] is True and srow[0]["ended_by"] == "provisional"
              and srow[0]["carry_changed"] is False and srow[0]["root_state"] == "pending" and srow[0]["provisional_state"] == "provisional_met")
        crow = cl.shadow_rows(arm="dream", kind="carry")
        check("closure_shadow: one kind='carry' row with the provisional detail", len(crow) == 1 and crow[0]["ended_by"] == "provisional" and crow[0]["provisional_detail"]["baseline_days"] == 2)
        dn.PROVISIONAL_MET_ENDS_CARRY = False
        out, n = node._met_carry_check(dict(carried_in), 2)
        srow = dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)
        check("flag False: exact old path (would_end False, provisional_state None), no closure row",
              out == carried_in and srow[-1]["would_end_carry"] is False and srow[-1]["provisional_state"] is None and len(cl.shadow_rows(kind="carry")) == 1)
        dn.PROVISIONAL_MET_ENDS_CARRY = True
        dn.MET_ENDS_CARRY = "live"
        out, n = node._met_carry_check(dict(carried_in), 2)
        check("live: a provisional-met thread ends the carry (tonight opens fresh, counter reset)", out is None and n == -1 and node._carried_n_tonight == 0)
        check("live row says carry_changed True", dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)[-1]["carry_changed"] is True)
        dn.MET_ENDS_CARRY = "off"
        b1, b2 = len(dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)), len(cl.shadow_rows())
        out, n = node._met_carry_check(dict(carried_in), 2)
        check("off: nothing logged anywhere, carry unchanged", out == carried_in and len(dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)) == b1 and len(cl.shadow_rows()) == b2)
        dn.MET_ENDS_CARRY = "live"
        dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in [arc(20, 30, "tens1"), arc(21, 31, "tens1", carried_n=1)]), encoding="utf-8")
        out, n = node._met_carry_check(dict(carried_in), 2)
        check("live: a provisional_unmet thread keeps the carry", out == carried_in and dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)[-1]["provisional_state"] == "provisional_unmet")
    finally:
        _time.time = _real_time
        dn.MET_ENDS_CARRY = "shadow"; dn.PROVISIONAL_MET_ENDS_CARRY = True

    # ---------------------------------------------------------------------------------------------
    print("\n[4] resolution shadow via run_nightly")
    cl.CLOSURE_WRITE_LIVE = False   # D-0495 (2026-10-28): the source default is now True; [4] tests the SHADOW path
    composed = []
    def fake_compose(system, user):
        composed.append((system, user))
        return {"resolution": "I had kept returning to the unspent thing, night after night, and I could not put it down. Then the returning stopped. The embers went out on their own; I did not need to carry them any longer, and I do not know what changed, only that I stopped reaching for it."}
    cl._compose_fn = fake_compose
    # arc 0 (tens0): baseline days 10,20; days 31-36 all clean -> met (day 36 is unobserved: add thoughts for it)
    con = sqlite3.connect(DB)
    for h in range(8):
        con.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", (f"u{h}", "inner_thought", ts_of(36, 6 + h), noise(rng).tobytes(), "x"))
    con.commit(); con.close()
    arcs = [arc(0, 30, "tens0", core_text="the unspent thing"), arc(1, 30, "tens2")]      # arc 1: no-baseline
    dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in arcs), encoding="utf-8")
    dm.STATE_LOG.unlink(missing_ok=True)
    dm.TENSION_STATE_FILE.write_text(json.dumps({"tensions": []}), encoding="utf-8")
    NOW2 = ts_of(38, 22)
    out = dm.run_nightly(NOW2)
    st = {k: v["state"] for k, v in dm.latest_states().items()}
    check("judge: arc0 met, arc1 no-baseline", st.get("dream_0") == "met" and st.get("dream_1") == "no-baseline")
    res = cl.shadow_rows(arm="dream", kind="resolution")
    check("exactly one resolution row, for arc0, composed once", len(res) == 1 and res[0]["arc_id"] == "dream_0" and len(composed) == 1)
    r = res[0]
    wb = r["would_be"]
    check("would-be fragment: origin 'resolution', episodic, derived_from the seed",
          wb and wb["origin"] == "resolution" and wb["layer"] == "episodic" and wb["derived_from"] == ["dream_0"] and "resolution" in wb["keywords"])
    check("would-be edge: (fragment)-[resolves]->(dream dream_0)",
          wb["edge"]["edge_type"] == "resolves" and wb["edge"]["dst_kind"] == "dream" and wb["edge"]["dst_id"] == "dream_0" and wb["edge"]["src_kind"] == "fragment")
    check("row carries judge name, verdict, params, thread_root True, written_live False, fragment_id None",
          r["judge"] == "dream_met" and r["judge_verdict"] == "met" and r["judge_params"]["theta"] == 0.61 and r["thread_root"] is True
          and r["written_live"] is False and r["fragment_id"] is None and r["compose_how"] == "ok")
    check("composer prompt carried the seed tension + unresolved core + last scene", "tens0" in composed[0][1] and "the unspent thing" in composed[0][1] and "tail of 0" in composed[0][1])
    check("run_nightly reports the closure rows", len(out.get("closure") or []) == 1 and "closure_error" not in out)
    check("lab DB byte-identical (nothing reached the memory DB)", _hash_file(LABDB) == db_hash0)
    out2 = dm.run_nightly(NOW2)
    check("re-run: no new state row, no new resolution row", out2["states"]["appended"] == 0 and len(cl.shadow_rows(kind="resolution")) == 1 and len(composed) == 1)
    # a later met arc of the SAME thread -> duplicate, not a second fragment
    # a continuation is always the row right AFTER its root in the real log (carried_n walks back that many rows)
    arcs2 = [arcs[0], arc(2, 31, "tens0", carried_n=1), arcs[1]]
    dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in arcs2), encoding="utf-8")
    dm.run_nightly(NOW2)
    st = {k: v["state"] for k, v in dm.latest_states().items()}
    dup = cl.shadow_rows(arm="dream", kind="duplicate")
    check("continuation arc met -> kind='duplicate' of the thread root, nothing composed",
          st.get("dream_2") == "met" and len(dup) == 1 and dup[0]["root_id"] == "dream_0" and dup[0]["arc_id"] == "dream_2" and len(composed) == 1
          and len(cl.shadow_rows(kind="resolution")) == 1)
    # composer failure -> row kept with text None, nothing raised
    def bad_compose(system, user): raise RuntimeError("hub down")
    cl._compose_fn = bad_compose
    arcs3 = arcs2 + [arc(3, 30, "tens5")]                                              # tens5: baseline 14,24 but day 36 was unobserved before; now observed -> met
    dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in arcs3), encoding="utf-8")
    out3 = dm.run_nightly(NOW2)
    rr = [x for x in cl.shadow_rows(kind="resolution") if x["arc_id"] == "dream_3"]
    check("composer failure: resolution row kept, would_be None, compose_how error, no exception",
          dm.latest_states()["dream_3"]["state"] == "met" and len(rr) == 1 and rr[0]["would_be"] is None and rr[0]["compose_how"].startswith("error:") and "closure_error" not in out3)
    check("dm.CLOSURE_HOOK False -> run_nightly makes no closure call", (setattr(dm, "CLOSURE_HOOK", False), dm.run_nightly(NOW2))[1].get("closure") is None)
    dm.CLOSURE_HOOK = True
    check("lab DB still byte-identical", _hash_file(LABDB) == db_hash0)

    # ---------------------------------------------------------------------------------------------
    print("\n[5] the live path behind CLOSURE_WRITE_LIVE (stubbed store + edges)")
    import core.memory.store as _st, core.memory_edges as _me
    calls = {"frag": [], "edge": []}
    _sf, _ae = _st.store_fragment, _me.add_edge
    _st.store_fragment = lambda **kw: (calls["frag"].append(kw), "fid-123")[1]
    _me.add_edge = lambda *a, **kw: (calls["edge"].append((a, kw)), True)[1]
    cl._compose_fn = fake_compose
    try:
        cl.CLOSURE_WRITE_LIVE = False
        cl.record_dream_met(arc(40, 30, "tens0"), {"state": "met", "detail": {}, "params": {}}, now=NOW2)
        check("flag False: store_fragment and add_edge never called", not calls["frag"] and not calls["edge"])
        cl.CLOSURE_WRITE_LIVE = True
        # J-3225 (D-0614): the dream arm is shadow-only -- CLOSURE_ARMS no longer holds "dream", so even with the flag True nothing is written
        row0 = cl.record_dream_met(arc(42, 30, "tens0"), {"state": "met", "detail": {}, "params": {}}, now=NOW2)
        check("D-0614: CLOSURE_WRITE_LIVE True but 'dream' not in CLOSURE_ARMS: store_fragment/add_edge never called, row says written_live False",
              not calls["frag"] and not calls["edge"] and row0["written_live"] is False and row0["would_be"] is not None)
        cl.CLOSURE_ARMS.add("dream")      # the one-constant flip back; the rest of [5] is the live path it enables
        row = cl.record_dream_met(arc(41, 30, "tens0"), {"state": "met", "detail": {}, "params": {}}, now=NOW2)
        check("flag True: store_fragment called once with origin 'resolution' and derived_from the seed",
              len(calls["frag"]) == 1 and calls["frag"][0]["origin"] == "resolution" and calls["frag"][0]["derived_from"] == ["dream_41"]
              and calls["frag"][0]["layer"] == "episodic")
        check("flag True: add_edge('fragment', fid, 'dream', seed, 'resolves')",
              len(calls["edge"]) == 1 and calls["edge"][0][0] == ("fragment", "fid-123", "dream", "dream_41", "resolves"))
        check("flag True: row says written_live True + fragment_id", row["written_live"] is True and row["fragment_id"] == "fid-123")
    finally:
        cl.CLOSURE_WRITE_LIVE = False
        cl.CLOSURE_ARMS.discard("dream")
        _st.store_fragment, _me.add_edge = _sf, _ae
    src_cl = (ROOT / "core" / "closure.py").read_text(encoding="utf-8")
    src_dn = (ROOT / "nodes" / "dream_node.py").read_text(encoding="utf-8")
    src_dm = (ROOT / "core" / "dream_met.py").read_text(encoding="utf-8")
    check("source defaults: CLOSURE_WRITE_LIVE = True (D-0495, 2026-10-28)", "CLOSURE_WRITE_LIVE = True" in src_cl)
    check("source defaults: MET_ENDS_CARRY = \"live\" (D-0495), PROVISIONAL_MET_ENDS_CARRY = True",
          'MET_ENDS_CARRY = "live"' in src_dn and "PROVISIONAL_MET_ENDS_CARRY = True" in src_dn)
    check("source defaults: dream_met.CLOSURE_HOOK = True", "CLOSURE_HOOK = True" in src_dm)
    check("lab DB byte-identical after the stubbed live path too", _hash_file(LABDB) == db_hash0)

    # ---------------------------------------------------------------------------------------------
    print("\n[6] the interrogation arm is still a gated stub (J-2963 repaired this stale check: the pursuit and commitment arms were built in J-2160)")
    def raises(fn):
        try: fn(); return None
        except NotImplementedError as e: return str(e)
    check("interrogation arm names J-2060", "J-2060" in (raises(cl.record_interrogation_met) or ""))
    check("ARM_GATES", cl.ARM_GATES == {"dream": None, "pursuit": None, "commitment": None, "interrogation": "J-2060", "line": None, "lookup": None})

print("\nRESULT:", "ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

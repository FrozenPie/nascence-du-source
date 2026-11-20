"""
Hermetic test for J-1995 (D-0385): the computed dream "met" state, core/dream_met.py, and its shadow wiring in
nodes/dream_node.py.

No LLM, no embedder, no live data. Every store is temp-pathed: a synthetic sqlite DB of waking thoughts, a
synthetic dream_log.jsonl, a synthetic subconscious_state.json; the embedder is a lookup-table fake. The
real data/ tree is never opened.

  [1] scenario DB: met / unmet / no-baseline / relapsed / pending / D-0233-injected-recurrence-excluded
  [2] append-only + idempotent: second run appends nothing, dream_log.jsonl byte-identical, pending -> final
  [3] chronic_mass log: one row per calendar day, from the ledger state file
  [4] carry check: root-of-thread lookup, shadow mode logs but does NOT change the carry, live mode ends it,
      off writes nothing
  [5] PARITY: the production evaluate_arcs vs the replay script's own states() on a randomized synthetic world
      (docs/lab/dream_met_replay_20261008_scripts/replay_J_1964.py, imported unmodified)

Run:  python scripts/dream_met_test.py   (from the tree under test)
"""
from __future__ import annotations
import datetime, hashlib, importlib.util, json, os, sqlite3, sys, tempfile, time
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE anything that could repoint paths
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.dream_met as dm
import nodes.dream_node as dn

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j1995_"))
dm.DREAM_LOG = tmp / "dream_log.jsonl"
dm.STATE_LOG = tmp / "logs" / "dream_met_state.jsonl"
dm.MASS_LOG = tmp / "logs" / "dream_tension_mass.jsonl"
dm.TENSION_STATE_FILE = tmp / "subconscious_state.json"
dn._DREAM_LOG = dm.DREAM_LOG
dn._MET_CARRY_SHADOW_LOG = tmp / "logs" / "dream_met_carry_shadow.jsonl"
DB = tmp / "nascence.db"

DIM = 384
def basis(i):
    v = np.zeros(DIM, np.float32); v[i] = 1.0; return v
def noise(rng):
    v = rng.standard_normal(DIM).astype(np.float32); v[:40] = 0.0   # never overlaps the basis axes 0..39
    return v / np.linalg.norm(v)

# fake embedder: text -> vector from a table; unknown text -> deterministic noise on axes >= 100
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

# ---------------------------------------------------------------------------------------------
print("\n[1] scenario: one arc per state")
rng = np.random.default_rng(7)
con = sqlite3.connect(DB)
con.execute("CREATE TABLE memory_fragments (fragment_id TEXT, origin TEXT, timestamp REAL, embedding BLOB, content TEXT)")
rows = []
def thought(day, v, hour, origin="inner_thought"):
    rows.append((f"f{len(rows)}", origin, ts_of(day, hour), v.astype(np.float32).tobytes(), "x"))
for day in range(0, 42):                                   # 8 plain thoughts a day, day 0..41 (all observed)
    for h in range(8):
        thought(day, noise(rng), 6 + h, "study" if h == 0 else "inner_thought")
# theme recurrences (exact copies of the tension vector => cos 1.0)
for arc_axis, days in {0: (10, 20), 1: (12, 22, 32), 3: (14, 24, 35), 4: (12, 22, 31), 5: (25, 35)}.items():
    for d in days: thought(d, basis(arc_axis), 20)
con.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", rows); con.commit(); con.close()

TABLE.update({"tens0": basis(0), "tens1": basis(1), "tens2": basis(2), "tens3": basis(3), "tens4": basis(4),
              "tens5": basis(5), "tail4": basis(4)})   # arc 4's dream tail IS the theme: day-31 recurrence is injected
def arc(i, day, tension, tail=None):
    return {"ts": ts_of(day, 3), "dream_id": f"dream_{i}", "close_reason": "ended-unfaced", "ended_unresolved": True,
            "carried_n": 0, "seed": {"tension_labels": [tension]}, "final_unresolved_core": "",
            "final_narrative": tail or f"tail of {i}"}
arcs = [arc(0, 30, "tens0"),     # baseline days 10,20; silence 31-33; relapse 34-36 clean      -> met
        arc(1, 30, "tens1"),     # baseline 12,22; recurrence day 32                            -> unmet
        arc(2, 30, "tens2"),     # no recurrence ever                                           -> no-baseline
        arc(3, 30, "tens3"),     # baseline 14,24; silence; recurrence day 35 (relapse window)  -> relapsed
        arc(4, 30, "tens4", "tail4"),   # baseline 12,22; day-31 recurrence is the dream's own tail -> met
        arc(5, 38, "tens5")]     # window runs to day 44, now = day 41                          -> pending
dm.DREAM_LOG.parent.mkdir(parents=True, exist_ok=True)
dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in arcs), encoding="utf-8")
before = dm.DREAM_LOG.read_bytes()
NOW = ts_of(41, 22)
s1 = dm.compute_states(NOW, db_path=DB)
st = dm.latest_states()
got = {k: v["state"] for k, v in st.items()}
check("arc0 met", got.get("dream_0") == "met")
check("arc1 unmet", got.get("dream_1") == "unmet")
check("arc2 no-baseline", got.get("dream_2") == "no-baseline")
check("arc3 relapsed", got.get("dream_3") == "relapsed")
check("arc4 met (injected-tail recurrence excluded by the D-0233 rule)", got.get("dream_4") == "met")
check("arc5 pending", got.get("dream_5") == "pending")
check("rows carry computed_at + params", all("computed_at" in v and v["params"]["theta"] == 0.61 and v["params"]["N"] == 3
                                           and v["params"]["K"] == 25 and v["params"]["R"] == 2 and v["params"]["M"] == 3
                                           for v in st.values()))
# the D-0233 rule matters: with the tail made orthogonal, arc 4 becomes unmet
TABLE["tail4"] = noise(rng) * 0 + basis(60)
s_alt = dm.compute_states(NOW, db_path=DB, state_log=tmp / "alt_state.jsonl")
check("without the injected tail arc4 would be unmet (rule is load-bearing)",
      dm.latest_states(tmp / "alt_state.jsonl").get("dream_4", {}).get("state") == "unmet")
TABLE["tail4"] = basis(4)

# ---------------------------------------------------------------------------------------------
print("\n[2] append-only, idempotent, dream_log untouched")
n_rows = len(dm._read_jsonl(dm.STATE_LOG))
s2 = dm.compute_states(NOW, db_path=DB)
check("second run appends nothing", s2["appended"] == 0 and len(dm._read_jsonl(dm.STATE_LOG)) == n_rows)
check("dream_log.jsonl byte-identical", dm.DREAM_LOG.read_bytes() == before)
check("close_reason untouched", all(json.loads(l)["close_reason"] == "ended-unfaced"
                                    for l in dm.DREAM_LOG.read_text(encoding="utf-8").splitlines()))
s3 = dm.compute_states(ts_of(48, 22), db_path=DB)           # a week on: arc 5's window has elapsed (but days 42+ have no thoughts)
check("arc5 stays non-final while its window days are unobserved (no false verdict)",
      dm.latest_states().get("dream_5", {}).get("state") == "pending")
# now give days 42..47 thoughts and re-run: pending -> final, and the pending row is kept (append-only)
con = sqlite3.connect(DB)
for day in range(42, 48):
    for h in range(8):
        con.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", (f"g{day}{h}", "inner_thought", ts_of(day, 6 + h), noise(rng).tobytes(), "x"))
con.commit(); con.close()
dm.compute_states(ts_of(48, 22), db_path=DB)
hist = [r["state"] for r in dm._read_jsonl(dm.STATE_LOG) if r["dream_id"] == "dream_5"]
check("arc5 history is pending then a final state (both rows kept)", hist[0] == "pending" and hist[-1] in dm.FINAL_STATES and len(hist) == 2)

# ---------------------------------------------------------------------------------------------
print("\n[3] chronic_mass log")
dm.TENSION_STATE_FILE.write_text(json.dumps({"tensions": [
    {"label": "a", "chronic_mass": 1.5, "member_event_ids": [1, 2]}, {"label": "b", "chronic_mass": 3.25}]}), encoding="utf-8")
check("first call of the day writes a row", dm.log_tension_mass(ts_of(48, 23)) is True)
check("second call the same day writes nothing", dm.log_tension_mass(ts_of(48, 23)) is False)
check("next day writes again", dm.log_tension_mass(ts_of(49, 2)) is True)
mr = dm._read_jsonl(dm.MASS_LOG)
check("rows hold per-tension chronic_mass, largest first", len(mr) == 2 and mr[0]["tensions"][0] == {"label": "b", "chronic_mass": 3.25, "members": 0})
check("run_nightly is fail-open on a missing state file", "mass_error" in (lambda: (setattr(dm, "TENSION_STATE_FILE", tmp / "nope.json"),
      dm.run_nightly(ts_of(60, 2)))[1])())
dm.TENSION_STATE_FILE = tmp / "subconscious_state.json"

# ---------------------------------------------------------------------------------------------
print("\n[4] carry check in nodes/dream_node.py")
chain = [dict(arc(10, 30, "tens0"), carried_n=0), dict(arc(11, 31, "tens0"), carried_n=1), dict(arc(12, 32, "tens0"), carried_n=2)]
dm.DREAM_LOG.write_text("".join(json.dumps(a) + "\n" for a in arcs[:2] + chain), encoding="utf-8")
root = dm.carry_thread_root()
check("thread root = first arc of the chain (walk back carried_n rows)", root["dream_id"] == "dream_10")
dm._append(dm.STATE_LOG, {"dream_id": "dream_10", "state": "met", "computed_at": 1.0, "params": {}})
node = dn.DreamNode()
carried_in = {"narrative": "x", "symbols": [], "unresolved_core": "y"}
dn.MET_ENDS_CARRY = "shadow"
out, n = node._met_carry_check(dict(carried_in), 2)
check("shadow: carry returned unchanged", out == carried_in and n == 2)
srow = dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)
check("shadow: would-have-ended decision logged, carry_changed False",
      len(srow) == 1 and srow[0]["would_end_carry"] is True and srow[0]["carry_changed"] is False and srow[0]["root"] == "dream_10")
dn.MET_ENDS_CARRY = "live"
out, n = node._met_carry_check(dict(carried_in), 2)
check("live: a met thread ends the carry (tonight opens fresh, counter reset)", out is None and n == -1 and node._carried_n_tonight == 0)
dn.MET_ENDS_CARRY = "off"
before_n = len(dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG))
out, n = node._met_carry_check(dict(carried_in), 2)
check("off: nothing logged, carry unchanged", out == carried_in and len(dm._read_jsonl(dn._MET_CARRY_SHADOW_LOG)) == before_n)
dn.MET_ENDS_CARRY = "live"
dm._append(dm.STATE_LOG, {"dream_id": "dream_10", "state": "unmet", "computed_at": 2.0, "params": {}})
out, n = node._met_carry_check(dict(carried_in), 2)
check("live: an unmet thread keeps the carry", out == carried_in)
dn.MET_ENDS_CARRY = "shadow"
check("module default flag is shadow (source constant)", "MET_ENDS_CARRY = \"shadow\"" in (ROOT / "nodes" / "dream_node.py").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------------------------
print("\n[5] parity vs the replay script's states()")
LAB = ROOT / "docs" / "lab" / "dream_met_replay_20261008_scripts" / "replay_J_1964.py"
if not LAB.exists():
    check("replay script present", False)
else:
    prng = np.random.default_rng(11)
    nA, nDays = 120, 100
    themes = [noise(prng) for _ in range(12)]
    th_ts, th_vec = [], []
    for day in range(nDays):
        if 85 <= day < 90: continue                          # an outage: unobserved days
        for h in range(int(prng.integers(4, 13))):           # a few days under the 5-thought line
            th = prng.random()
            v = noise(prng)
            if th < 0.12: v = themes[int(prng.integers(0, 12))] * 0.97 + v * 0.25
            th_ts.append(ts_of(day, 6 + h)); th_vec.append(v / np.linalg.norm(v))
    W = np.stack(th_vec).astype(np.float32); wts = np.array(th_ts)
    a_ts = np.sort(ts_of(28, 3) + prng.random(nA) * (nDays - 36) * 86400)
    own, TE = [], []
    for i in range(nA):
        if prng.random() < 0.12: continue                    # an arc with no tension text
        for _ in range(int(prng.integers(1, 3))):
            own.append(i); TE.append(themes[int(prng.integers(0, 12))] * 0.9 + noise(prng) * 0.4)
    TE = np.stack(TE).astype(np.float32); TE /= np.linalg.norm(TE, axis=1, keepdims=True)
    DE = np.stack([themes[int(prng.integers(0, 12))] * 0.8 + noise(prng) * 0.6 for _ in range(nA)]).astype(np.float32)
    DE /= np.linalg.norm(DE, axis=1, keepdims=True)
    cwd = os.getcwd()
    os.chdir(tmp)
    try:
        np.savez("prep_J-1964.npz", W=W, ts=wts, org=np.array(["inner_thought"] * len(wts)), ids=np.arange(len(wts)),
                 TE=TE, own=np.array(own), DE=DE, arc_ts=a_ts, cr=np.array(["x"] * nA))
        spec = importlib.util.spec_from_file_location("replay_J_1964_under_test", LAB)
        rep = importlib.util.module_from_spec(spec)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(rep)
        arc_T = [None] * nA
        for i in range(nA):
            vs = [TE[k] for k, a in enumerate(own) if a == i]
            arc_T[i] = np.stack(vs) if vs else None
        first = min(dm._day(t) for t in wts); today = max(dm._day(t) for t in wts) + 1
        norm = lambda s: "x" if s in ("noT", "unobs") else s                      # the replay conflates the two
        agree, total, kinds = 0, 0, {}
        for params in [(0.61, 3, 25, 2, 3), (0.50, 2, 14, 2, 5), (0.58, 4, 21, 3, 3)]:
            theta, N, K, Rm, M = params
            ref = rep.states(rep.recur_days(theta), N, K, Rm, M)
            new = dm.evaluate_arcs(a_ts, arc_T, W, wts, a_ts, DE, today, first,
                                   {"theta": theta, "N": N, "K": K, "R": Rm, "M": M})
            for r, (s, _) in zip(ref, new):
                total += 1; agree += (norm(r.replace("met?", "met-unobs")) == norm(s))
                kinds[s] = kinds.get(s, 0) + 1
        print("      states exercised:", dict(sorted(kinds.items())))
        check(f"production == replay on all {total} (arc x setting) classifications", agree == total)
        check("synthetic world is non-trivial (>=3 distinct final states exercised)",
              len([k for k in kinds if k in dm.FINAL_STATES]) >= 3)
    finally:
        os.chdir(cwd)

print("\nRESULT:", "ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)

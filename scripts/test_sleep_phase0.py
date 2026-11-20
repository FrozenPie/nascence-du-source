"""scripts/test_sleep_phase0.py (J-2016, sleep_as_a_mode Phase 0): hermetic proof, no LLM call, no live data (epoch may load the local embedder).

Every store is temp-pathed (a synthetic sqlite DB, a synthetic sleep_pressure_log, a synthetic night_mind_shadow
log); core is imported BEFORE anything that could repoint paths and its location is asserted to be this tree.

  [1] SleepHeartbeat counts event-loop turns: idle loop -> turns near expected, small max lag; an INLINE blocking
      call stalls it (stalls_gt_2s / max_lag), the same call through off_loop does not; marks are recorded
  [2] would-be night-thought shadow rows: written only with a seed AND an elapsed slot, capped, generated=False,
      replay first then dream tail, a slot with no seed is counted not logged, kill switch writes nothing,
      the live night_mind_shadow.jsonl path is never touched
  [3] sleep-pressure rows: sleep_entry + sleep_beat carry the TRUE measured P, asleep=True, fire=False; beat is a
      no-op when no sleep is armed / after sleep_exit / with the kill switch; should_sleep() and last_fire_ts()
      are unchanged by the new rows
  [4] node wiring (AST): every remaining synchronous stage of _enter_sleep is awaited through _sleep_off (none
      left as a bare call), the heartbeat is started/stopped/cancelled, scheduler_turns reaches the ledger
  [5] equivalence: replay_strengthen / downscale_episodic / dream_fade / epoch give the SAME database state when
      run in a worker thread as inline, on two identical temp DBs

Run:  python scripts/test_sleep_phase0.py   (from the tree under test)
"""
from __future__ import annotations
import ast, asyncio, json, shutil, sqlite3, sys, tempfile, threading, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything that could repoint paths
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import sleep_phase0 as sp0, sleep_pressure as sp, sleep_offloop, night
from core.memory import store

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j2016_"))
LIVE_SHADOW = ROOT / "data" / "night_mind_shadow.jsonl"
live_existed = LIVE_SHADOW.exists()
live_size = LIVE_SHADOW.stat().st_size if live_existed else 0

# ----------------------------------------------------------------------------------------------------------------
print("[1] heartbeat counts event-loop turns")
async def hb_idle():
    hb = sp0.SleepHeartbeat(interval=0.02, shadow=False); hb.start()
    await asyncio.sleep(0.5); hb.mark("a"); await asyncio.sleep(0.2)
    return await hb.stop()
s = asyncio.run(hb_idle())
check("idle loop: >=20 turns of ~35 expected", s["scheduler_turns"] >= 20 and s["expected_turns"] >= 30)
check("idle loop: no stalls, small max lag", s["stalls_gt_2s"] == 0 and s["max_lag_s"] < 0.5)
check("mark recorded and below final count", 0 < s["marks"]["a"] < s["scheduler_turns"])

async def hb_block(offloop):
    sleep_offloop.SLEEP_SWEEPS_OFFLOOP = True
    hb = sp0.SleepHeartbeat(interval=0.02, shadow=False); hb.start(); await asyncio.sleep(0.2)
    if offloop:
        await sleep_offloop.off_loop(time.sleep, 0.8)
    else:
        time.sleep(0.8)
    await asyncio.sleep(0.2)
    return await hb.stop()
inline, off = asyncio.run(hb_block(False)), asyncio.run(hb_block(True))
check("inline block: max lag >= 0.7 s (loop frozen)", inline["max_lag_s"] >= 0.7)
check("off_loop block: max lag < 0.25 s", off["max_lag_s"] < 0.25)
check("off_loop block gets far more turns than the inline one", off["scheduler_turns"] > inline["scheduler_turns"] + 15)
sp0.STALL_S, _old_stall = 0.5, sp0.STALL_S
inline2 = asyncio.run(hb_block(False)); sp0.STALL_S = _old_stall
check("stall counter fires on the inline block (STALL_S lowered)", inline2["stalls_gt_2s"] >= 1)
sp0.SLEEP_TURN_COUNTER = False
async def hb_off():
    hb = sp0.SleepHeartbeat(interval=0.02); hb.start(); await asyncio.sleep(0.2); return await hb.stop()
check("kill switch: no task, zero turns", asyncio.run(hb_off())["scheduler_turns"] == 0)
sp0.SLEEP_TURN_COUNTER = True

# ----------------------------------------------------------------------------------------------------------------
print("[2] would-be night-thought shadow rows")
sp0.NIGHT_MIND_SHADOW_LOG = tmp / "night_mind_shadow.jsonl"
sp0.NIGHT_SLOT_FLOOR_S = 0.1
_orig_dreams = night.load_recent_dreams

async def run_slots(replayed, dreams, dur=1.0, shadow=None, sleep_ts=None):
    night.load_recent_dreams = lambda: dreams
    hb = sp0.SleepHeartbeat(sleep_ts=sleep_ts or time.time(), interval=0.02, shadow=shadow)
    hb.set_replayed(replayed); hb.start(); await asyncio.sleep(dur)
    return await hb.stop()

def rows():
    p = sp0.NIGHT_MIND_SHADOW_LOG
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

t0 = time.time()
s = asyncio.run(run_slots(["a replayed thing", "another", "third"], [], sleep_ts=t0))
r = rows()
check("rows written, capped at NIGHT_MAX_SLOTS", 1 <= len(r) <= sp0.NIGHT_MAX_SLOTS and s["night_mind_slots_logged"] == len(r))
check("each row: generated False, seed+slot available, phase 0", all(x["generated"] is False and x["seed_available"] and x["slot_available"] and x["phase"] == 0 for x in r))
check("first source is the replay set, snippet from it", r[0]["would_seed"] == "replay" and r[0]["seed_snippet"] in ("a replayed thing", "another", "third"))
check("slot index counts up, elapsed >= floor", [x["slot"] for x in r] == list(range(len(r))) and all(x["elapsed_s"] >= 0.1 for x in r))
check("row carries the turns so far and the dormant pick as not_built", all(x["scheduler_turns"] > 0 and x["seeds"]["dormant"] == "not_built" for x in r))
sp0.NIGHT_MIND_SHADOW_LOG.unlink()
s = asyncio.run(run_slots([], []))
check("no seed: nothing logged, slots counted", rows() == [] and s["night_mind_slots_no_seed"] >= 1 and s["night_mind_slots_logged"] == 0)
t1 = time.time()
s = asyncio.run(run_slots([], [{"ts": t1 + 1, "narrative": "the corridor folded into water and the clock ran backward"}], sleep_ts=t1))
r = rows()
check("no replay, dream exists: would_seed is the dream tail", r and r[0]["would_seed"] == "dream_tail" and "clock" in r[0]["seed_snippet"])
sp0.NIGHT_MIND_SHADOW_LOG.unlink()
t2 = time.time()
s = asyncio.run(run_slots([], [{"ts": t2 - 500, "narrative": "last night's dream"}], sleep_ts=t2))
check("a dream from BEFORE this sleep is not this night's seed", rows() == [])
s = asyncio.run(run_slots(["x"], [], shadow=False))
check("shadow=False: counter only, no rows, no shadow keys", rows() == [] and "night_mind_slots_logged" not in s)
sp0.NIGHT_MIND_SHADOW_ROWS = False
s = asyncio.run(run_slots(["x"], []))
check("NIGHT_MIND_SHADOW_ROWS False: no rows", rows() == [])
sp0.NIGHT_MIND_SHADOW_ROWS = True
night.load_recent_dreams = _orig_dreams
check("the live data/night_mind_shadow.jsonl was never touched",
      (LIVE_SHADOW.exists() == live_existed) and ((LIVE_SHADOW.stat().st_size if live_existed else 0) == live_size))

# ----------------------------------------------------------------------------------------------------------------
print("[3] sleep-pressure rows during a sleep")
sp._LOG_FILE = tmp / "sleep_pressure_log.jsonl"
sp._new_intake = lambda since: (3, 25.0)                     # P = 0.1*3 + 0.1*25 = 2.8
def log_rows():
    return [json.loads(l) for l in sp._LOG_FILE.read_text(encoding="utf-8").splitlines() if l.strip()] if sp._LOG_FILE.exists() else []
def join_beats():
    for t in threading.enumerate():
        if t.name == "sleep-pressure-beat":
            t.join(2.0)
since = time.time() - 3600
sp.log_sleep_beat(); join_beats()
check("beat with no sleep armed writes nothing", log_rows() == [])
check("sleep_enter logs the entry row", sp.sleep_enter(since) is True and len(log_rows()) == 1)
e = log_rows()[0]
check("entry row: true measured P, asleep, never a fire", e["reason"] == "sleep_entry" and e["P"] == 2.8 and e["asleep"] is True and e["fire"] is False)
check("entry row keeps the standard keys (threshold, dark, awake_min)", all(k in e for k in ("threshold", "dark", "awake_min", "new_notes", "new_epi_weight", "ts")))
sp.log_sleep_beat(); join_beats()
b = log_rows()[-1]
check("beat row logged while armed", len(log_rows()) == 2 and b["reason"] == "sleep_beat" and b["asleep"] is True and b["fire"] is False and "asleep_min" in b)
check("status()['last'] is now the in-sleep row (the instrument is no longer silent)", sp.status()["last"]["reason"] == "sleep_beat")
sp.sleep_exit(); sp.log_sleep_beat(); join_beats()
check("after sleep_exit the beat is a no-op again", len(log_rows()) == 2)
sp.SLEEP_ROWS_ENABLED = False
check("kill switch: no entry row", sp.sleep_enter(since) is False and len(log_rows()) == 2)
sp.SLEEP_ROWS_ENABLED = True; sp.sleep_exit()
check("last_fire_ts ignores the in-sleep rows (fire is false)", sp.last_fire_ts(default=-1.0) == -1.0)
fire, info = sp.should_sleep(time.time() - 3 * 3600)
last = log_rows()[-1]
check("should_sleep still logs its own normal row (no asleep key)", "asleep" not in last and last["reason"] == info["reason"] and "fire" in last)

# ----------------------------------------------------------------------------------------------------------------
print("[4] node wiring (AST)")
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
tree = ast.parse(src)
fn = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_enter_sleep")
BARE_ATTR = {("_pg", "snapshot"), ("_aff2", "synthesise"), ("_ml", "memory_lint"), ("_medg", "harvest_all"),
             ("_bus", "sync_investigation_calibration"), ("_mc", "snapshot"), ("_night", "dream_fade"), ("_night", "epoch")}
BARE_NAME = {"replay_strengthen", "downscale_episodic", "_rc_shadow"}
bare = []
def walk(node, in_lambda=False):
    for ch in ast.iter_child_nodes(node):
        lam = in_lambda or isinstance(ch, ast.Lambda)
        if isinstance(ch, ast.Call) and not lam:
            f = ch.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and (f.value.id, f.attr) in BARE_ATTR:
                bare.append(f"{f.value.id}.{f.attr}@{ch.lineno}")
            if isinstance(f, ast.Name) and f.id in BARE_NAME:
                bare.append(f"{f.id}@{ch.lineno}")
        walk(ch, lam)
walk(fn)
check(f"no bare synchronous call of the enumerated stages remains ({bare or 'none'})", not bare)
off_refs = sum(1 for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_sleep_off")
check(f"_sleep_off call count in _enter_sleep >= 17 (was 4 stick/peer/hold/wc/br + 12 new)", off_refs >= 17)
for needle in ("SleepHeartbeat(", "_hb.start()", "await _hb.stop()", "_hb.cancel()", "_sleep_off(_sp_row.sleep_enter", "sleep_exit()",
               '_night.note("scheduler_turns"', '_hb.mark("consolidation_done")'):
    check(f"node contains {needle}", needle in src)
# the retained-on-loop stages are the ones audited as NOT thread-safe / not stage-less sqlite: say so by name
# J-2026 / F-2626: scan was audited, curiosity_queue's read-modify-write now sits under _QUEUE_LOCK, and scan runs off the loop
check("meta_awareness scan now off the loop behind the curiosity_queue lock (J-2026)", "_mar = await _sleep_off(_ma.scan)" in src and "_QUEUE_LOCK" in open(ROOT / "core" / "curiosity_queue.py", encoding="utf-8").read())

# ----------------------------------------------------------------------------------------------------------------
print("[5] off-loop equivalence on two identical temp DBs")
def make_db(path: Path):
    store.DB_PATH = path
    store.init_db()
    now = time.time()
    c = sqlite3.connect(str(path))
    rng = [(f"f{i}", f"content {i}", "episodic", 0.5, now - 600 + i, "k", None, o, "[]", 0.3 + (i % 7) / 10.0)
           for i, o in enumerate(["reading", "study", "lived", "social_notification", "inner_thought", "dream", "action", "reading"] * 6)]
    c.executemany("INSERT INTO memory_fragments (fragment_id,content,layer,relevance,timestamp,keywords,embedding,origin,derived_from,importance) VALUES (?,?,?,?,?,?,?,?,?,?)", rng)
    old_dream = now - 80 * 3600
    c.execute("INSERT INTO memory_fragments (fragment_id,content,layer,relevance,timestamp,keywords,origin,derived_from,importance) VALUES ('dr1','old dream','episodic',0.5,?,'k','dream','[]',0.85)", (old_dream,))
    c.commit(); c.close()
def dump(path: Path):
    c = sqlite3.connect(str(path))
    out = c.execute("SELECT fragment_id, importance, replay_count, cold FROM memory_fragments ORDER BY fragment_id").fetchall()
    c.close(); return out
since = time.time() - 3600
a, b = tmp / "inline.db", tmp / "thread.db"
make_db(a); make_db(b)
store.DB_PATH = a
ra = store.replay_strengthen(since); na = store.downscale_episodic(since_ts=since); fa = night.dream_fade(); ea = night.epoch(since, ra)
store.DB_PATH = b
async def threaded():
    r = await sleep_offloop.off_loop(store.replay_strengthen, since)
    n = await sleep_offloop.off_loop(lambda: store.downscale_episodic(since_ts=since))
    f = await sleep_offloop.off_loop(night.dream_fade)
    e = await sleep_offloop.off_loop(night.epoch, since, r)
    return r, n, f, e
rb, nb, fb, eb = asyncio.run(threaded())
check("return values identical (replayed snippets, downscale rowcount, fade counts)", ra == rb and na == nb and fa == fb)
check("replay actually did work (non-trivial)", len(ra) >= 4 and na >= 20 and fa["cooled"] == 1)
check("databases identical afterwards (importance, replay_count, cold)", dump(a) == dump(b))
check("epoch both None or both formed (same decision)", (ea is None) == (eb is None))

shutil.rmtree(tmp, ignore_errors=True)
print("PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)

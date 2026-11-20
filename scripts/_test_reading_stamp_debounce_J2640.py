"""Regression test for J-2640 (F-3370 / F-3371 / F-3379): the reading context-stamp loss.

core/memory/store.py store_fragment() stamps every fragment through core/geometry_census.snapshot(source=origin,
thought=content[:70]). A reading passage's first 70 chars are its '[From <book>]' header, identical for every passage
of one book, so the census debounce (same thought within 0.5 s -> None) left every passage after the first of a fast
same-book burst with NO fragment_context / world_context row. The fix: store_fragment passes debounce=False and, inside
the debounce window, gets a copy of the last recorded census row (kill-switch geometry_census.STAMP_REUSE_ON_DEBOUNCE)
while the census log itself gains no rows.

What this checks, all inside lab_env.isolate(db="empty") with the lab root moved to a scratch dir (never data/_lab):
  1. a burst of 20 reading-shaped store_fragment() calls, identical content[:70], 10 ms apart -> 20/20 fragment_context
     and 20/20 world_context rows with the switch ON; 1/20 with it OFF (the pre-fix behaviour);
  2. the census LOG gets the same number of rows either way (no extra geometry_tuples volume);
  3. other callers keep the debounce: a repeated snapshot(source="monologue") inside 0.5 s is still None;
  4. scripts/liveness_audit.py's fragment_context verdict (J-2642) on the sandbox DB reads OK with the fix and DEGRADED
     without it;
  5. the live data files the exercised paths can reach are unchanged (size + mtime).
Run from the worktree. Exit 0 = pass. On a checkout without the fix (no `debounce` kwarg) it runs the burst only and
reports the pre-fix count, exiting 1."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import inspect, pathlib, sqlite3, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core                                                    # BEFORE lab_env (F-2423)
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
from core import geometry_census as gc, sound_string_shadow, watershed, loop_probe
from core.memory import store
import lab_env

SCRATCH = HERE.parent / "lab_J2640"                            # outside C:\Nascence\data entirely (S-0315)
lab_env._LAB_ROOT = SCRATCH
lab_env._ISOLATE_OUTCOMES_LOG = SCRATCH / "_isolate_outcomes.jsonl"
assert not str(SCRATCH.resolve()).lower().startswith(r"c:\nascence"), SCRATCH

LIVE = pathlib.Path(r"C:\Nascence") / "data"
WATCH = [LIVE / "memory" / "nascence.db", LIVE / "geometry_tuples.jsonl", LIVE / "sound_strings_shadow.jsonl",
         LIVE / "watershed_state.json", LIVE / "watershed_shadow.jsonl", LIVE / "loop_probe_log.jsonl"]
def fp():
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None for p in WATCH}

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)

store._embed = lambda text: None                               # no model load; the stamp path does not need a vector
# The worktree has no data/, so the census's world readers would bootstrap stores (provisions.json ...) and hit the
# write fence. The debounce under test does not depend on what the world reads, so pin them to a fixed world.
gc._place_weather = lambda: {"place": "study", "at_study": 1, "at_garden": 0, "at_shore": 0, "at_wood": 0,
                             "standpoint": None, "in_transit": 0, "weather": "overcast", "fire": "low", "fire_fuel": 0.4}
gc._objects = lambda: {"book": {"title": "The Long Burst"}}
for _name in ("_light_band_truth", "_smells_truth", "_warmth", "_cat_at"):
    setattr(gc, _name, lambda: None)
gc._cat_ref = lambda thought: None
from core import experienced_tuple as _xt                     # same reason: its light reader bootstraps position.json
_xt._light_band = lambda place: None
HEADER = "[From The Long Burst: a Synthetic Book for J-2640]  Chapter one. "
HEADER = (HEADER + "." * 70)[:70]
HAS_FIX = "debounce" in inspect.signature(gc.snapshot).parameters
ALSO = [(gc, ["_LOG"]), (sound_string_shadow, ["_LOG"]), (watershed, ["_STATE", "_LOG"]), (loop_probe, ["_LOG"])]


TALLY = {"logged": 0, "reused": 0, "none": 0}
_ORIG_SNAPSHOT = gc.snapshot


def _tallied_snapshot(*a, **k):
    n0 = log_rows()
    r = _ORIG_SNAPSHOT(*a, **k)
    if log_rows() > n0:
        TALLY["logged"] += 1
    elif r is None:
        TALLY["none"] += 1
    else:
        TALLY["reused"] += 1
    return r


def burst(n, tag, gap=0.01):
    ids = []
    for i in range(n):
        ids.append(store.store_fragment(f"{HEADER}{tag} passage {i}: the river bends twice before the mill.",
                                        origin="reading", importance=0.4))
        time.sleep(gap)
    return ids


def stamped(ids, table):
    q = ",".join("?" * len(ids))
    c = sqlite3.connect(str(store.DB_PATH))
    try:
        return c.execute(f"SELECT COUNT(*) FROM {table} WHERE fragment_id IN ({q})", ids).fetchone()[0]
    finally:
        c.close()


def make_ctx_table():
    """An empty lab DB has no fragment_context (live, memory_edges creates it); store_fragment only ALTERs it.
    Create it with the live column set, as the live DB has it."""
    c = sqlite3.connect(str(store.DB_PATH))
    try:
        c.execute("CREATE TABLE IF NOT EXISTS fragment_context (fragment_id TEXT PRIMARY KEY, tuple_ts REAL, source TEXT, "
                  "place TEXT, weather TEXT, weather_dir REAL, fire TEXT, tide_level REAL, sun_az REAL, moon_illum REAL, "
                  "level REAL, valence REAL, arousal REAL, sounds TEXT, standpoint TEXT, warmth REAL, cat_at TEXT)")
        c.commit()
    finally:
        c.close()


def log_rows():
    try:
        return sum(1 for ln in open(gc._LOG, encoding="utf-8") if ln.strip())
    except FileNotFoundError:
        return 0


def audit_line():
    out = subprocess.run([sys.executable, str(HERE / "scripts" / "liveness_audit.py"), "--data", str(store.DB_PATH.parent.parent),
                          "--db", str(store.DB_PATH)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in out.stdout.splitlines() if "fragment_context stamp" in ln]
    return lines[0] if lines else "(no fragment_context line) " + out.stdout[-300:] + out.stderr[-300:]


def run(switch_on):
    gc._last_ts, gc._last_thought = 0.0, ""
    if HAS_FIX:
        gc._last_row = None
        gc.STAMP_REUSE_ON_DEBOUNCE = switch_on
    with lab_env.isolate(db="empty", also=ALSO) as lab:
        assert str(pathlib.Path(store.DB_PATH).resolve()).startswith(str(SCRATCH.resolve())), store.DB_PATH
        make_ctx_table()
        TALLY.update(logged=0, reused=0, none=0)
        gc.snapshot = _tallied_snapshot
        t0 = time.time()
        ids = burst(20, "A")
        dur = time.time() - t0
        gc.snapshot = _ORIG_SNAPSHOT
        tally = dict(TALLY)
        fc, wc = stamped(ids, "fragment_context"), stamped(ids, "world_context")
        ids2 = burst(40, "B")                                  # volume for the audit's >= 50 floor
        fc_all = stamped(ids + ids2, "fragment_context")
        line = audit_line()
        mono = None
        if HAS_FIX:
            gc._last_ts, gc._last_thought = 0.0, ""
            gc.snapshot(source="monologue", thought="a short repeated monologue thought")
            mono = gc.snapshot(source="monologue", thought="a short repeated monologue thought")
    return {"fc": fc, "wc": wc, "log": tally["logged"], "reused": tally["reused"], "dropped": tally["none"], "dur": dur, "fc_all": fc_all, "n_all": 60, "audit": line, "mono": mono, "lab": str(lab)}


before = fp()
print(f"fix present in this checkout: {HAS_FIX}")
on = run(True)
print(f"switch ON : burst fragment_context {on['fc']}/20, world_context {on['wc']}/20, census log +{on['log']} row(s), reused {on['reused']}, dropped {on['dropped']}, burst {on['dur']:.2f}s, "
      f"all {on['fc_all']}/{on['n_all']}\n            audit: {on['audit']}")
if not HAS_FIX:
    check("burst of 20 same-book reading fragments all stamped", on["fc"] == 20)
else:
    off = run(False)
    print(f"switch OFF: burst fragment_context {off['fc']}/20, world_context {off['wc']}/20, census log +{off['log']} row(s), reused {off['reused']}, dropped {off['dropped']}, burst {off['dur']:.2f}s, "
          f"all {off['fc_all']}/{off['n_all']}\n            audit: {off['audit']}")
    check("ON: 20/20 burst fragments get a fragment_context row", on["fc"] == 20)
    check("ON: 20/20 burst fragments get a world_context row", on["wc"] == 20)
    # The debounce keeps one census row per 0.5 s window of identical thought, so how many of the 20 survive OFF depends on
    # how long 20 store_fragment calls take on this machine (1/20 if the burst fits in one window).
    check("OFF reproduces the loss: only the census-logged passages are stamped, the rest dropped",
          off["fc"] == off["wc"] == off["log"] < 20 and off["dropped"] == 20 - off["log"])
    check("ON: no call dropped; every passage either opened a census row or reused the last one",
          on["dropped"] == 0 and on["log"] + on["reused"] == 20)
    check("ON adds no census rows beyond one per debounce window (no extra geometry_tuples volume)",
          on["log"] < 20 and on["log"] <= int(on["dur"] / gc._MIN_GAP) + 1)
    check("other callers keep the debounce (repeated monologue snapshot -> None)", on["mono"] is None and off["mono"] is None)
    check("liveness_audit fragment_context verdict OK with the fix", " OK " in on["audit"] or "OK —" in on["audit"])
    check("liveness_audit fragment_context verdict DEGRADED without it", "DEGRADED" in off["audit"])
after = fp()
check("live data files unchanged (size + mtime)", before == after)
if before != after:
    print("   changed:", {k: (before[k], after[k]) for k in before if before[k] != after[k]})
print("PASS" if not FAILS else f"FAIL ({len(FAILS)})")
sys.exit(0 if not FAILS else 1)

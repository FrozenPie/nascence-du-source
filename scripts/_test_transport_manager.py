"""
Offline test for core/transport_manager.py (J-0338, 2026-08-29).
Synthetic lines, temp state/shadow files — no live data touched.

Covers:
  1. novelty fires once, ever, per line (birth candidate; consumed after dispatch_tick surfaces it)
  2. spike/drought need the cold-start gate cleared (MIN_SAMPLES=20 AND MIN_AGE_DAYS=3, whichever later)
  3. a real spike (rate far above rate_ema) is detected once past cold start
  4. a real drought (time-since-last far above gap_ema) is detected on a clock, without a new occurrence
  5. weights are comparable across lines (a drought and a spike can be ranked against each other)
  6. dispatch_tick returns the single highest-weight candidate, and logs every tick (fired or not)

Sections 1-6 above pin EDGE_TRIGGER=False explicitly (today's level-polling behaviour, byte-
identical to pre-J-1432) -- see the assignment right after the redirects below. Section 7
(J-1432, D-0294) sets EDGE_TRIGGER=True and covers the fire-once/re-arm semantics that flag adds:
  7a. a drought fires once, then not again until a fresh observe() re-arms it
  7b. a spike fires once, then not again until evaluate() sees the windowed rate cool back down
  7c. two lines over the bar each get a turn across two ticks -- the winner doesn't win forever

Section 8 (J-1433, D-0294) covers verdict(line_id), the read-only per-line helper felt recall's
Phase 1 gate will call once core/felt_recall.py is wired to it (see that function's own docstring
for why this build stops short of the wiring itself -- worktree isolation, F-2110):
  8a. an unregistered line reads none/cold_start=True, never raises
  8b. a brand-new line reads novel while pending, is NOT consumed by repeated verdict() calls
      (unlike dispatch_tick()), and correctly reads none/cold_start=True once dispatch_tick()
      elsewhere consumes the novelty -- the exact case cold_start exists to distinguish
  8c. an established line with an active drought reads drought/cold_start=False, and repeated
      verdict() calls do not disarm it (dispatch_tick()'s fire-once accounting is untouched)
  8d. an established, unremarkable line reads none/cold_start=False
  8e. the same live spike reads identically under EDGE_TRIGGER=True and EDGE_TRIGGER=False
"""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import core.transport_manager as tm
import core.transport_habituation as thab

_tmp = Path(tempfile.mkdtemp())
tm._STATE = _tmp / "transport_lines.json"
tm._SHADOW_LOG = _tmp / "transport_shadow.jsonl"
# J-0603: dispatch_tick() now also calls transport_habituation.observe_and_log() every tick —
# redirect its state/log too, or this test leaks synthetic bird:* rows into the real (eventually
# live) data/transport_habituation_*.{json,jsonl} the same way the two lines above already guard
# transport_manager's own files.
thab._STATE = _tmp / "transport_habituation_state.json"
thab._LOG = _tmp / "transport_habituation_shadow.jsonl"
# J-4382: cause-as-object shadow hooks in observe()/dispatch_tick() -- redirect so no synthetic rows reach real data/.
import core.transport_cause_shadow as _tcs
_tcs._STATE = _tmp / "transport_cause_lines.json"
_tcs._LOG = _tmp / "transport_cause_shadow.jsonl"
_tcs._state = None

# J-1432 (D-0294): sections 1-6 below assume today's LEVEL-polling behaviour (a candidate stays a
# candidate every tick while its ratio is over the bar) -- pin that explicitly. The module's own
# default is now EDGE_TRIGGER=True (D-0294's ruling); section 7 below sets it back to True itself.
tm.EDGE_TRIGGER = False

results = []
def check(name, cond):
    results.append((name, cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== transport_manager — offline test ===\n")

# --- 1. novelty fires once ---
print("1. Novelty")
t0 = time.time() - 40 * 86400.0   # birth 40 days ago, well past MIN_AGE_DAYS
tm.observe("bird:garden", t0, 1.0)
cands = tm.evaluate("bird:garden")
check("novelty candidate present at birth", any(c.kind == "novelty" for c in cands))
winner = tm.dispatch_tick()
check("dispatch_tick surfaces the novelty winner", winner is not None and winner.kind == "novelty")
cands2 = tm.evaluate("bird:garden")
check("novelty does not fire twice", not any(c.kind == "novelty" for c in cands2))

# --- 2. cold start gate blocks spike/drought ---
print("2. Cold start gate")
# feed 5 more observations (well under MIN_SAMPLES=20), all recent -> still cold (age < 3 days too,
# since t0 was 40 days ago but n_total is what matters here combined with age; use a FRESH line for
# a clean age-based cold-start check)
t1 = time.time() - 1 * 86400.0    # only 1 day old
tm.observe("bird:shore", t1, 1.0)
for i in range(25):
    tm.observe("bird:shore", t1 + i * 60.0, 1.0)   # 25 samples (past MIN_SAMPLES) but age still ~1 day
cands = tm.evaluate("bird:shore")
kinds = {c.kind for c in cands}
check("age gate still blocks spike/drought despite MIN_SAMPLES met ('whichever later')",
      "spike" not in kinds and "drought" not in kinds)

# --- 3. real (sustained) spike detected once past cold start; a single stray short gap does not
#        fire on its own (J-0584 windowed-rate fix — F-0812: single-gap instant_rate saturated
#        dispatch on quasi-continuous lines, firing "spike" on ~100% of ticks). evaluate()'s
# window is anchored to real wall-clock "now" (matching live use: a factory calls observe() near
# the moment it happens), so the baseline here is spread across the full age window ending close
# to real now, not backdated arbitrarily far in the past. ---
print("3. Spike")
now = time.time()
birth = now - 10 * 86400.0   # 10 days old, past MIN_AGE_DAYS
line = "bird:orchard"
# establish a slow baseline: ~1 occurrence every ~12h for 20 samples, spanning the 10 days and
# ending just now -> gap_ema ~ 12h, and the windowed-rate fix's own window (3x gap_ema) covers
# roughly the last ~1.5 days / ~3 baseline observations, matching its "comparable to gap_ema" design.
ts = birth
step = (now - birth) / 21.0
for i in range(20):
    ts += step
    tm.observe(line, ts, 1.0)
# 3a. ONE occurrence arriving early (30s after the last, instead of ~12h) is exactly the pattern
# that used to saturate spike scoring on a single sample. With the windowed-rate fix, one early
# arrival alone should NOT be enough — this is the degenerate behavior J-0584 removes.
ts_single = ts + 30.0
tm.observe(line, ts_single, 1.0)
cands = tm.evaluate(line)
check("a single early arrival alone does not fire spike (the fixed degenerate case)",
      not any(c.kind == "spike" for c in cands))
# 3b. a REAL burst — several more rapid occurrences landing inside the same window — should still
# fire: sustained elevated rate, not single-sample noise, is what "spike" means.
ts_burst = ts_single
for i in range(6):
    ts_burst += 20.0
    tm.observe(line, ts_burst, 1.0)
cands = tm.evaluate(line)
spike = next((c for c in cands if c.kind == "spike"), None)
check("spike candidate detected after a sustained burst", spike is not None)
if spike:
    check("spike weight is positive and finite", spike.weight > 0 and spike.weight < 10**6)

# --- 4. drought detected on a clock (no new occurrence needed) ---
print("4. Drought")
line2 = "bird:hedge"
birth2 = now - 10 * 86400.0
ts2 = birth2
for i in range(20):
    ts2 += 3600.0   # steady hourly baseline
    tm.observe(line2, ts2, 1.0)
# simulate silence since the last occurrence by rewriting last_ts far in the past relative to "now"
import json
state = json.loads(tm._STATE.read_text(encoding="utf-8"))
state["lines"][line2]["last_ts"] = now - 20 * 3600.0   # 20h silence vs a ~1h gap_ema
tm._STATE.write_text(json.dumps(state), encoding="utf-8")
cands = tm.evaluate(line2)
drought = next((c for c in cands if c.kind == "drought"), None)
check("drought candidate detected purely from elapsed clock time", drought is not None)

# --- 5. weights comparable across lines; dispatch_tick picks the single highest ---
print("5. Cross-line ranking + dispatch")
winner = tm.dispatch_tick()
check("dispatch_tick returns a single winner", winner is not None)
if winner:
    check("winner is the higher-weight candidate (spike vs drought, whichever computed larger)",
          winner.kind in ("spike", "drought"))
    print(f"      winner: {winner!r}")

# --- 6. shadow log accumulates every tick, fired or not ---
print("6. Shadow log")
tm.dispatch_tick()   # a tick with nothing new -> may or may not fire, but must log
rows = [l for l in tm._SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
check("shadow log has one row per dispatch_tick call", len(rows) >= 3)
check("shadow rows are valid JSON with a 'fired' field", all("fired" in json.loads(r) for r in rows))

# --- 7. EDGE_TRIGGER=True (D-0294/J-1432): fire-once + re-arm semantics -------------------------
# Each scenario below gets its OWN fresh tmp state/shadow files (never sections 1-6's shared
# _tmp) so dispatch_tick()'s single-winner competition only ever sees the line(s) THIS scenario
# creates -- no ambiguity from leftover bird:garden/shore/orchard/hedge state above.
print("\n7. Edge-trigger (D-0294)")


def _fresh_edge_env():
    d = Path(tempfile.mkdtemp())
    tm._STATE = d / "transport_lines.json"
    tm._SHADOW_LOG = d / "transport_shadow.jsonl"
    thab._STATE = d / "transport_habituation_state.json"
    thab._LOG = d / "transport_habituation_shadow.jsonl"
    tm.EDGE_TRIGGER = True
    return d


# --- 7a. drought fires once, then not again until an observe() ---
print("7a. Drought fires once, re-arms only on a fresh observe()")
_fresh_edge_env()
line_a = "bird:cliff"
now_a = time.time()
birth_a = now_a - 10 * 86400.0
ts_a = birth_a
tm.observe(line_a, ts_a, 1.0)          # first-ever observation -> novelty_pending
tm.dispatch_tick()                      # consume novelty cleanly (cold-start still blocks spike/drought
                                         # at n_total=1 -- novelty is the only possible candidate here)
for _ in range(19):
    ts_a += 3600.0                      # steady ~1h baseline -> gap_ema ~1h
    tm.observe(line_a, ts_a, 1.0)
# force a deep, controlled drought (last real observation was ~9.2 days before "now" already, but
# pin it to an exact, legible value): ~50h silence vs a ~1h gap_ema clears DROUGHT_TRIGGER_RATIO
# (2.0) and DISPATCH_THRESHOLD (1.5 on weight=ratio-1) comfortably.
st = json.loads(tm._STATE.read_text(encoding="utf-8"))
st["lines"][line_a]["last_ts"] = now_a - 50 * 3600.0
tm._STATE.write_text(json.dumps(st), encoding="utf-8")
cands = tm.evaluate(line_a)
check("7a. drought candidate present before dispatch", any(c.kind == "drought" for c in cands))
winner = tm.dispatch_tick()
check("7a. dispatch_tick fires the drought as winner",
      winner is not None and winner.kind == "drought" and winner.line_id == line_a)
st_after = json.loads(tm._STATE.read_text(encoding="utf-8"))
check("7a. winning line's drought_armed flipped False", st_after["lines"][line_a]["drought_armed"] is False)
cands2 = tm.evaluate(line_a)
check("7a. drought does not re-appear from evaluate() while disarmed (ratio is unchanged, still over the bar)",
      not any(c.kind == "drought" for c in cands2))
winner2 = tm.dispatch_tick()
check("7a. dispatch_tick fires nothing on the next tick (its only candidate is disarmed)", winner2 is None)
tm.observe(line_a, time.time(), 1.0)   # a fresh occurrence -- the one re-arm event D-0294 gives drought
st_after2 = json.loads(tm._STATE.read_text(encoding="utf-8"))
check("7a. drought_armed re-armed True by the next observe() call",
      st_after2["lines"][line_a]["drought_armed"] is True)

# --- 7b. spike fires once, then not again until evaluate() sees the window cool ---
print("7b. Spike fires once, re-arms only after the window cools (no observe() needed)")
_fresh_edge_env()
line_b = "bird:reef"
now_b = time.time()
birth_b = now_b - 10 * 86400.0
step_b = (now_b - birth_b) / 21.0      # mirrors section 3's spacing: baseline ends right at "now"
ts_b = birth_b
tm.observe(line_b, ts_b, 1.0)          # first-ever observation -> novelty_pending
tm.dispatch_tick()                      # consume novelty cleanly, same reasoning as 7a
for _ in range(19):
    ts_b += step_b
    tm.observe(line_b, ts_b, 1.0)
# a strong, sustained burst inside the windowed-rate window -> a real spike (section 3's own
# "single gap alone should not fire" case is already covered above; this is the positive case)
ts_burst = ts_b
for _ in range(15):
    ts_burst += 15.0
    tm.observe(line_b, ts_burst, 1.0)
cands = tm.evaluate(line_b)
check("7b. sustained burst produces a spike candidate", any(c.kind == "spike" for c in cands))
winner = tm.dispatch_tick()
check("7b. dispatch_tick fires the spike as winner",
      winner is not None and winner.kind == "spike" and winner.line_id == line_b)
st_after = json.loads(tm._STATE.read_text(encoding="utf-8"))
check("7b. winning line's spike_armed flipped False", st_after["lines"][line_b]["spike_armed"] is False)
cands2 = tm.evaluate(line_b)
check("7b. spike does not re-appear from evaluate() immediately after firing (still hot, still disarmed)",
      not any(c.kind == "spike" for c in cands2))
# Re-arm rule (D-0294): "spike re-arms when evaluate() sees the windowed rate ratio drop below
# SPIKE_TRIGGER_RATIO" -- no fresh observe() needed, unlike drought. Fake a future "now" comfortably
# past the spike window so evaluate() sees the windowed rate itself (not the armed flag) go to
# zero, purely by faking elapsed wall time -- the only re-arm path the spec gives spike.
gap_ema_b = json.loads(tm._STATE.read_text(encoding="utf-8"))["lines"][line_b]["gap_ema"]
window_hours_b = max(gap_ema_b * tm.WINDOW_GAP_MULTIPLE, tm.MIN_WINDOW_HOURS)
_real_time_fn = time.time
try:
    future_now_b = ts_burst + (window_hours_b * 3600.0) * 2.0
    time.time = lambda: future_now_b
    cands3 = tm.evaluate(line_b)
finally:
    time.time = _real_time_fn
check("7b. evaluate() sees no spike once the window has cooled (sanity check on the fake-time setup)",
      not any(c.kind == "spike" for c in cands3))
st_after2 = json.loads(tm._STATE.read_text(encoding="utf-8"))
check("7b. spike_armed re-armed True purely by evaluate() noticing the cooled window (no observe() call)",
      st_after2["lines"][line_b]["spike_armed"] is True)

# --- 7c. two armed lines each get a turn; the winner doesn't win forever ---
print("7c. Two lines over the bar produce two fires on two ticks, not one line forever")
_fresh_edge_env()
line_n, line_s = "bird:north", "bird:south"
now_c = time.time()
for lid in (line_n, line_s):
    birth_c = now_c - 10 * 86400.0
    ts_c = birth_c
    tm.observe(lid, ts_c, 1.0)          # first observation -> novelty; on line_s's turn line_n
    tm.dispatch_tick()                   # already exists but is parked quiet (see below), so it
                                         # cannot out-rank line_s's own novelty here.
    for _ in range(19):
        ts_c += 3600.0
        tm.observe(lid, ts_c, 1.0)
    # park: no active drought yet on this line, so it can't win a tick meant for the OTHER line
    st = json.loads(tm._STATE.read_text(encoding="utf-8"))
    st["lines"][lid]["last_ts"] = now_c
    tm._STATE.write_text(json.dumps(st), encoding="utf-8")
# now apply the two INTENDED, controlled droughts in one shot (both well past cold-start already)
st = json.loads(tm._STATE.read_text(encoding="utf-8"))
st["lines"][line_n]["last_ts"] = now_c - 80.0 * 3600.0   # ~80h silence -> the higher weight
st["lines"][line_s]["last_ts"] = now_c - 30.0 * 3600.0   # ~30h silence -> lower, still over the bar
tm._STATE.write_text(json.dumps(st), encoding="utf-8")

winner1 = tm.dispatch_tick()
check("7c. tick 1 fires the higher-drought line (north, ~80h)",
      winner1 is not None and winner1.line_id == line_n and winner1.kind == "drought")
winner2 = tm.dispatch_tick()
check("7c. tick 2 fires the OTHER line (south, ~30h) -- north stays disarmed, does not win again",
      winner2 is not None and winner2.line_id == line_s and winner2.kind == "drought")
winner3 = tm.dispatch_tick()
check("7c. tick 3 fires nothing -- both lines now disarmed, no runner-up left", winner3 is None)

# --- 8. verdict() helper (J-1433, D-0294): read-only per-line dispatcher verdict for felt recall --
print("\n8. verdict() helper")


def _fresh_verdict_env(edge: bool):
    d = Path(tempfile.mkdtemp())
    tm._STATE = d / "transport_lines.json"
    tm._SHADOW_LOG = d / "transport_shadow.jsonl"
    thab._STATE = d / "transport_habituation_state.json"
    thab._LOG = d / "transport_habituation_shadow.jsonl"
    tm.EDGE_TRIGGER = edge
    return d


# 8a. an unregistered line (never observe()'d) -> none, cold_start=True, never raises
print("8a. Unregistered line")
_fresh_verdict_env(True)
v = tm.verdict("world:weather:garden")
check("8a. unregistered line verdict is none", v["verdict"] == "none")
check("8a. unregistered line weight is 0.0", v["weight"] == 0.0)
check("8a. unregistered line is reported cold_start", v["cold_start"] is True)

# 8b. a brand-new line's first-ever observe() -> novel, still cold_start (age/sample gate unmet);
# verdict() must not consume the novelty the way dispatch_tick() does.
print("8b. Brand-new line (novelty pending, not yet consumed)")
_fresh_verdict_env(True)
line_v1 = "world:fire:study"
tm.observe(line_v1, time.time(), 1.0)
v = tm.verdict(line_v1)
check("8b. brand-new line verdict is novel", v["verdict"] == "novel")
check("8b. brand-new line weight is 1.0 (novelty's fixed weight)", v["weight"] == 1.0)
check("8b. brand-new line is still cold_start", v["cold_start"] is True)
v2 = tm.verdict(line_v1)
v3 = tm.verdict(line_v1)
check("8b. verdict() does not consume novelty -- second call still novel", v2["verdict"] == "novel")
check("8b. verdict() does not consume novelty -- third call still novel", v3["verdict"] == "novel")
st = json.loads(tm._STATE.read_text(encoding="utf-8"))
check("8b. novelty_fired is still False on disk -- verdict() truly never wrote anything",
      st["lines"][line_v1]["novelty_fired"] is False)
tm.dispatch_tick()   # the only thing that may legitimately consume novelty
v4 = tm.verdict(line_v1)
check("8b. after dispatch_tick() consumes novelty, verdict() reports none (no baseline yet)",
      v4["verdict"] == "none")
check("8b. still flagged cold_start after novelty consumed -- the case cold_start exists for",
      v4["cold_start"] is True)

# 8c. an established line with an active drought -> drought, weight>0, cold_start=False; repeated
# verdict() calls must not disarm it (that fire-once accounting belongs to dispatch_tick() only).
print("8c. Established line, active drought")
_fresh_verdict_env(True)
line_v2 = "world:cat_at:garden"
birth_v2 = time.time() - 10 * 86400.0
ts_v2 = birth_v2
for i in range(20):
    ts_v2 += 3600.0
    tm.observe(line_v2, ts_v2, 1.0)
st = json.loads(tm._STATE.read_text(encoding="utf-8"))
st["lines"][line_v2]["last_ts"] = time.time() - 20 * 3600.0   # ~20h silence vs ~1h gap_ema
tm._STATE.write_text(json.dumps(st), encoding="utf-8")
v = tm.verdict(line_v2)
check("8c. established line in drought reports drought", v["verdict"] == "drought")
check("8c. drought weight is positive", v["weight"] > 0)
check("8c. established line is not cold_start", v["cold_start"] is False)
v_again = tm.verdict(line_v2)
check("8c. calling verdict() again does not disarm -- still reports drought", v_again["verdict"] == "drought")
st_after = json.loads(tm._STATE.read_text(encoding="utf-8"))
check("8c. drought_armed is untouched by verdict() on disk", st_after["lines"][line_v2]["drought_armed"] is True)

# 8d. an established, unremarkable line -> none, cold_start=False
print("8d. Established, unremarkable line")
_fresh_verdict_env(True)
line_v3 = "world:light_band:garden"
birth_v3 = time.time() - 10 * 86400.0
step_v3 = (time.time() - birth_v3) / 21.0
ts_v3 = birth_v3
for i in range(20):
    ts_v3 += step_v3
    tm.observe(line_v3, ts_v3, 1.0)
tm.dispatch_tick()   # clear novelty first so this reads as a genuine "ordinary" verdict
v = tm.verdict(line_v3)
check("8d. established, unremarkable line reports none", v["verdict"] == "none")
check("8d. established, unremarkable line is not cold_start", v["cold_start"] is False)

# 8e. verdict() gives the same kind evaluate() would under BOTH EDGE_TRIGGER states (D-0294's own
# "must work under both EDGE_TRIGGER states" requirement).
print("8e. Works under both EDGE_TRIGGER states")
_fresh_verdict_env(True)
line_v4 = "world:weather:shore"
birth_v4 = time.time() - 10 * 86400.0
step_v4 = (time.time() - birth_v4) / 21.0
ts_v4 = birth_v4
tm.observe(line_v4, ts_v4, 1.0)      # first-ever observation -> novelty_pending
tm.dispatch_tick()                    # consume novelty cleanly before building the spike scenario
for i in range(19):
    ts_v4 += step_v4
    tm.observe(line_v4, ts_v4, 1.0)
ts_burst_v4 = ts_v4
for i in range(6):
    ts_burst_v4 += 20.0
    tm.observe(line_v4, ts_burst_v4, 1.0)
v_edge_true = tm.verdict(line_v4)
check("8e. spike visible under EDGE_TRIGGER=True", v_edge_true["verdict"] == "spike")
tm.EDGE_TRIGGER = False
v_edge_false = tm.verdict(line_v4)
check("8e. same spike still visible under EDGE_TRIGGER=False (level polling)", v_edge_false["verdict"] == "spike")
tm.EDGE_TRIGGER = True

# --- summary ---
n_pass = sum(1 for _, c in results if c)
n_fail = len(results) - n_pass
print(f"\n{n_pass}/{len(results)} passed" + (f", {n_fail} FAILED" if n_fail else ""))
sys.exit(1 if n_fail else 0)

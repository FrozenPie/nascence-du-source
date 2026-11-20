"""J-2142 (F-2825 / J-2141 probe): the two sleep-consolidation sync segments the 10-16 22:37 boot's
night_stall_attribution rows confirm -- guidance_behavior_judge.sweep()'s synchronous prefix (state read, candidate
fetch, injection-log read, the _best_belief loop) and pursuits.judge_pending()'s register save -- now run through
core.sleep_offloop.off_loop. Checks, with every store on a temp path (read side too) and fake slow bodies only:
  * the loop stays responsive with the switch on and is held with it off;
  * outputs, saved state/register bytes and shadow-log rows are identical on vs off;
  * an exception inside an offloaded call lands in the same fail-open handler (same return value) on vs off;
  * the kill switches really run inline on the caller thread.
Touches no live data: run from a worktree, never from C:\\Nascence."""
import asyncio
import json
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
assert "c:\\nascence\\core" not in str(Path(core.__file__).resolve()).lower(), "run from a worktree, not the live tree"

from core import guidance_behavior_judge as gbj, guidance_learning as gl, judge_panel as jp  # noqa: E402
from core import pursuits as pu, needle_triage as nt, pursuit_close_shadow as pcs  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j2142_"))
MAIN = threading.get_ident()
threads_seen: set = set()


async def canary(lag: list, stop: asyncio.Event):
    while not stop.is_set():
        t = time.perf_counter()
        await asyncio.sleep(0.01)
        lag.append(time.perf_counter() - t - 0.01)


async def measured(coro_fn):
    lag, stop = [], asyncio.Event()
    c = asyncio.create_task(canary(lag, stop))
    await asyncio.sleep(0)
    out = await coro_fn()
    stop.set()
    await c
    return out, (max(lag) if lag else 0.0)


# ---------------------------------------------------------------- guidance behaviour judge
ROWS = [{"fragment_id": f"f{i}", "content": f"a real thought number {i} about the garden and the sea and the fire",
         "timestamp": 1000.0 + i} for i in range(40)]


def fake_candidates(since, limit):
    threads_seen.add(threading.get_ident())
    time.sleep(0.05)
    return [dict(r) for r in ROWS if r["timestamp"] > since][:limit]


def fake_best(text, mode=None):
    threads_seen.add(threading.get_ident())
    assert mode == "hybrid", mode
    time.sleep(0.01)                     # 40 calls ~ 0.4 s of synchronous work, no await between unmatched rows
    n = int(text.split("number ")[1].split()[0])
    if n >= 36:                          # the last few rows match a belief -> one judge await each
        return ({"id": f"b{n}", "principle": "tend what you love", "domain": "world"}, 0.4)
    return None


def fake_best_raises(text, mode=None):
    raise RuntimeError("best-belief boom")


async def fake_rule(system, user, key, context="", **kw):
    await asyncio.sleep(0.001)
    return "garden" in user


def setup_gbj(tag):
    gbj._STATE = TMP / f"gbj_state_{tag}.json"
    gbj._LOG = TMP / f"gbj_log_{tag}.jsonl"
    gbj._DATA = TMP
    gbj._STATE.write_text(json.dumps({"last_ts": 999.0}), encoding="utf-8")
    gbj._candidate_thoughts = fake_candidates
    gbj._skipped_between = lambda since, oldest: 0   # J-3211: the newest-first skip count would open the real store
    gl._best_belief = fake_best
    gl.injection_times = lambda: [1005.5]
    jp.rule = fake_rule


def strip_ts(path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        r.pop("ts", None)
        out.append(r)
    return out


async def run_gbj(flag, tag):
    gbj.GUIDANCE_JUDGE_OFFLOOP = flag
    setup_gbj(tag)
    return await measured(lambda: gbj.sweep(max_items=15))


threads_seen.clear()
(o_on, lag_on) = asyncio.run(run_gbj(True, "on"))
on_threads = set(threads_seen)
threads_seen.clear()
(o_off, lag_off) = asyncio.run(run_gbj(False, "off"))
off_threads = set(threads_seen)
assert o_on == o_off, (o_on, o_off)
assert o_on["scanned"] == 40 and o_on["matched"] == 4 and o_on["judged"] == 4, o_on
assert json.loads(gbj._STATE.read_text()) == json.loads((TMP / "gbj_state_on.json").read_text()), "state differs"
assert strip_ts(TMP / "gbj_log_on.jsonl") == strip_ts(TMP / "gbj_log_off.jsonl"), "shadow rows differ"
assert MAIN not in on_threads and off_threads == {MAIN}, (on_threads, off_threads, MAIN)
assert lag_on < 0.08 and lag_off > 0.3, (lag_on, lag_off)
print(f"guidance judge: max loop lag {lag_on:.3f}s offloop vs {lag_off:.3f}s inline; out {o_on}; state + rows identical")


async def run_gbj_raise(flag):
    gbj.GUIDANCE_JUDGE_OFFLOOP = flag
    setup_gbj(f"raise_{flag}")
    gl._best_belief = fake_best_raises
    return await gbj.sweep(max_items=15)

r_on, r_off = asyncio.run(run_gbj_raise(True)), asyncio.run(run_gbj_raise(False))
assert r_on == r_off == {"scanned": 40, "matched": 0, "judged": 0, "aligned": 0}, (r_on, r_off)
assert json.loads((TMP / "gbj_state_raise_True.json").read_text()) == {"last_ts": 999.0}, "state must not advance on a raise"
print("guidance judge: exception inside offloaded _best_belief -> same fail-open return, state not advanced, on == off")


# ---------------------------------------------------------------- pursuits judge_pending save
def make_register():
    items = []
    for i in range(4):
        items.append({"id": f"p{i}", "question": f"question {i} about the sea?", "status": "active",
                      "advances": 1, "heat": 0.3, "standing": "prior", "thoughts": [],
                      "pending": [{"thought": f"a new step {i} about the garden", "prior_standing": "prior",
                                   "cycle_id": f"c{i}"},
                                  {"thought": f"a restated circle {i}", "prior_standing": "prior", "cycle_id": f"d{i}"}],
                      "big": "x" * 20000})
    return items


_orig_save = pu._save


def slow_save(items):
    threads_seen.add(threading.get_ident())
    time.sleep(0.4)                      # stands in for the 23.5 MB dumps + write (0.56 s on a 10-18 copy)
    _orig_save(items)


async def no_close(items):
    return 0


def setup_pu(tag):
    pu._DIR = TMP
    pu._ACTIVE = TMP / f"pursuits_{tag}.json"
    pu._ACTIVE.write_text(json.dumps(make_register(), ensure_ascii=False, indent=1), encoding="utf-8")
    pu._SHADOW = TMP / f"pursuits_shadow_{tag}.jsonl"
    pu._write_light = lambda items, stamp=None: None
    pu._log = lambda rec: (TMP / f"pursuits_log_{tag}.jsonl").open("a", encoding="utf-8").write(
        json.dumps({k: v for k, v in rec.items() if k != "ts"}) + "\n")
    pu._save = slow_save
    jp.rule = fake_rule

    async def _fake_rule_detail(system, user, key, context="", **kw):      # J-3000: judge_pending calls rule_detail
        v = await fake_rule(system, user, key, context, **kw)
        return {"verdict": v, "how": "agreed", "why": "t"}
    jp.rule_detail = _fake_rule_detail
    nt.read = lambda *a, **k: None
    pcs.sweep = no_close


async def run_pu(flag, tag):
    pu.PURSUITS_SAVE_OFFLOOP = flag
    setup_pu(tag)
    return await measured(lambda: pu.judge_pending(max_items=8))


threads_seen.clear()
(p_on, plag_on) = asyncio.run(run_pu(True, "on"))
pon_threads = set(threads_seen)
threads_seen.clear()
(p_off, plag_off) = asyncio.run(run_pu(False, "off"))
poff_threads = set(threads_seen)
assert p_on == p_off and p_on["judged"] == 8 and p_on["confirmed"] == 4 and p_on["refuted"] == 4, (p_on, p_off)
a = json.loads((TMP / "pursuits_on.json").read_text(encoding="utf-8"))
b = json.loads((TMP / "pursuits_off.json").read_text(encoding="utf-8"))
for x in a + b:
    x.pop("last_touched", None)
assert a == b and all(not p["pending"] for p in a), "saved registers differ"
assert (TMP / "pursuits_log_on.jsonl").read_text() == (TMP / "pursuits_log_off.jsonl").read_text(), "pursuit logs differ"
assert MAIN not in pon_threads and poff_threads == {MAIN}, (pon_threads, poff_threads)
assert plag_on < 0.08 and plag_off > 0.3, (plag_on, plag_off)
print(f"pursuits judge: max loop lag {plag_on:.3f}s offloop vs {plag_off:.3f}s inline; out {p_on}; register + logs identical")


def save_raises(items):
    raise OSError("disk boom")


async def run_pu_raise(flag):
    pu.PURSUITS_SAVE_OFFLOOP = flag
    setup_pu(f"raise_{flag}")
    pu._save = save_raises               # _save itself never raises; this proves the outer fail-open is unchanged
    return await pu.judge_pending(max_items=8)

q_on, q_off = asyncio.run(run_pu_raise(True)), asyncio.run(run_pu_raise(False))
assert q_on == q_off, (q_on, q_off)
print(f"pursuits judge: a raising save lands in the same outer handler on vs off -> {q_on}")

src_g = Path(gbj.__file__).read_text(encoding="utf-8")
src_p = Path(pu.__file__).read_text(encoding="utf-8")
for needle in ("await _off(_load_state)", "await _off(_candidate_thoughts, since, SCAN_MAX)",
               "await _off(_gl.injection_times)", 'await _off(_gl._best_belief, text, "hybrid")'):
    assert needle in src_g, needle
assert "await _sleep_off(_save, items)" in src_p
print("OK")

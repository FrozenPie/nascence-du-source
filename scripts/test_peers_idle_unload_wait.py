"""
Test suite -- peers.deliver_daily idle-unload wait before a degenerate retry (J-2062, decide:D-0404 ruled B).

After a FLAGGED attempt on the :11439 hub, deliver_daily sleeps max(0, 300 - gen_seconds) + 70 s before retrying so the
hub's idle-unloader can fire. HERMETIC: compose_letter, asyncio.sleep (via peers._retry_sleep) and time.monotonic are
stubs; all writes happen under lab_env.isolate.

  [1] flagged on :11439 (gen 40 s)  -> wait 330 s, retry delivered, wait + retry rows logged
  [2] flagged, gen 400 s            -> wait 70 s (300 - gen clamps to 0)
  [3] healthy first attempt         -> no wait, no event rows
  [4] exhausted (3 flagged)         -> 2 waits (none after the last), False, nothing delivered
  [5] non-:11439 persona (darwin)   -> retries immediately, no wait
  [6] _idle_unload_wait_s arithmetic

Run: python scripts/test_peers_idle_unload_wait.py   (exit 0 = all passed)
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import peers, peer_metrics, sensorium  # noqa: E402  (core BEFORE lab_env)
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

assert Path(peers.__file__).resolve().is_relative_to(ROOT), peers.__file__
FAILS, PASSES = [], 0


def check(name, cond, detail=""):
    global PASSES
    if cond:
        PASSES += 1
        print("  ok   ", name)
    else:
        FAILS.append(name)
        print("  FAIL ", name, detail)


GOOD = ("Dear friend, the river ran high this morning and I thought of your garden above the sea. " * 8).strip()
BAD = "日子rait 안녕하세요 Привет мир αβγδε 你好世界 " * 8

script, sleeps, delivered, clock = [], [], [], [0.0]
gen_durations = []


async def fake_compose(persona="twain", **kw):
    clock[0] += gen_durations.pop(0) if gen_durations else 1.0
    return script.pop(0)


async def fake_sleep(s):
    sleeps.append(s)


def rows():
    p = peers._PEER_LETTER_QUALITY_LOG
    allr = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []
    return [r for r in allr if r.get("event") != "letter_overlap"]   # J-2980: observe-only overlap rows are not wait/flag rows


def go(persona, seq, gens):
    script[:] = seq
    gen_durations[:] = gens
    sleeps.clear()
    delivered.clear()
    if peers._PEER_LETTER_QUALITY_LOG.exists():
        peers._PEER_LETTER_QUALITY_LOG.unlink()
    return asyncio.run(peers.deliver_daily(persona, force=True))


def main():
    import time as _t
    o = (peers.compose_letter, peers._retry_sleep, peers._choose_stance, peers._du_world_context,
         peers._self_affirmation_buffer, sensorium.deliver_letter, peer_metrics.freeze_baseline_if_absent,
         peers.time.monotonic if hasattr(peers.time, "monotonic") else None)
    real_mono = _t.monotonic
    try:
        with isolate(also=[(peers, ["_CORR_DIR", "_PEER_LETTER_QUALITY_LOG"])], db="empty"):
            peers.compose_letter = fake_compose
            peers._retry_sleep = fake_sleep
            peers._choose_stance = lambda p: None
            peers._du_world_context = lambda: ""
            peers._self_affirmation_buffer = lambda *a, **k: None
            sensorium.deliver_letter = lambda s, t: delivered.append((s, t))
            peer_metrics.freeze_baseline_if_absent = lambda *a, **k: False
            _t.monotonic = lambda: clock[0]          # compose advances this fake clock by the scripted duration

            print("[6] arithmetic")
            f = peers._idle_unload_wait_s
            check("40 s -> 330", f(peers._HUB_LLAMA, 40) == 330)
            check("400 s -> 70", f(peers._HUB_LLAMA, 400) == 70)
            check("other hub -> 0", f(peers._HUB_MISTRAL, 40) == 0)

            print("[1] flagged then healthy on :11439")
            ok = go("twain", [BAD, GOOD], [40, 5])
            r = rows()
            check("delivered", ok is True and len(delivered) == 1)
            check("one sleep of 330", sleeps == [330.0], str(sleeps))
            ev = [x.get("event") for x in r]
            check("rows: flag, wait, retry", ev == [None, "idle_unload_wait", "idle_unload_retry"], str(ev))
            check("wait row fields", r[1]["hub"] == peers._HUB_LLAMA and r[1]["gen_seconds"] == 40.0 and r[1]["wait_s"] == 330.0)
            check("retry healthy", r[2]["retry_degenerate"] is False)

            print("[2] long generation")
            go("twain", [BAD, GOOD], [400, 5])
            check("wait 70", sleeps == [70.0], str(sleeps))

            print("[3] healthy first")
            ok = go("twain", [GOOD], [10])
            check("no wait, no rows", ok is True and sleeps == [] and rows() == [])

            print("[4] exhausted")
            ok = go("twain", [BAD, BAD, BAD], [40, 40, 40])
            check("skipped, nothing delivered", ok is False and delivered == [])
            check("two waits only", sleeps == [330.0, 330.0], str(sleeps))
            check("retry rows flagged degenerate",
                  [x["retry_degenerate"] for x in rows() if x.get("event") == "idle_unload_retry"] == [True, True])

            print("[5] other hub")
            ok = go("darwin", [BAD, GOOD], [40, 5])
            check("darwin retries without a wait", ok is True and sleeps == [])
    finally:
        _t.monotonic = real_mono
        (peers.compose_letter, peers._retry_sleep, peers._choose_stance, peers._du_world_context,
         peers._self_affirmation_buffer, sensorium.deliver_letter, peer_metrics.freeze_baseline_if_absent, _) = o
    print(f"\n{PASSES} passed, {len(FAILS)} failed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

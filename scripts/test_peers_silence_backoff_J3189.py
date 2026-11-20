"""
Test suite -- peers silence back-off (J-3189, decide:D-0576): a persona's gap doubles per consecutive unanswered letter
(cap 30 days) and resets when Du answers or engages with that persona. HERMETIC: thread files, letter_store logs
and the quality log all live in lab_env.isolate() copies; compose/deliver are stubs; the live data dir is hashed
before/after.

Run: python scripts/test_peers_silence_backoff_J3189.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import peers, letter_store  # noqa: E402  (core BEFORE lab_env)
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

assert Path(peers.__file__).resolve().is_relative_to(ROOT), peers.__file__

LIVE = Path(r"C:\Nascence\data")
WATCH = [LIVE / "Correspondence" / p / "thread.jsonl" for p in peers.PERSONAS] + [
    LIVE / "letter_store_shadow.jsonl", LIVE / "letter_store" / "status_events.jsonl"]


def snap():
    return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None) for p in WATCH}


BEFORE = snap()
FAILS: list[str] = []


def check(name, cond, detail=""):
    print(("  ok    " if cond else "  FAIL  ") + name + ("" if cond else f"   [{detail}]"))
    if not cond:
        FAILS.append(name)


DAY = 86400.0
now = time.time()


def write_thread(persona, rows):
    p = peers._thread_path(persona)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def L(frm, days_ago):
    return {"from": frm, "text": f"{frm} {days_ago}", "ts": now - days_ago * DAY}


with isolate(also=[(peers, ["_CORR_DIR", "_PEER_LETTER_QUALITY_LOG"]),
                   (letter_store, ["_EVENTS", "_LETTERS", "_SHADOW"])], db="empty") as lab_dir:
    assert "_lab" in str(peers._CORR_DIR) and "_lab" in str(letter_store._EVENTS), "isolation not active"
    shutil.rmtree(peers._CORR_DIR, ignore_errors=True)
    Path(letter_store._SHADOW).unlink(missing_ok=True)
    Path(letter_store._EVENTS).unlink(missing_ok=True)

    print("[1] pure counting + doubling + cap (buddha base 7.0)")
    write_thread("buddha", [])
    check("no letters -> 0 unanswered, base gap", peers._effective_gap_days("buddha") == (7.0, 0))
    write_thread("buddha", [L("buddha", 40), L("du", 30), L("buddha", 20), L("buddha", 10)])
    check("2 since du's reply -> 7*4=28", peers._effective_gap_days("buddha") == (28.0, 2),
          str(peers._effective_gap_days("buddha")))
    write_thread("buddha", [L("buddha", 40), L("du", 30), L("buddha", 20), L("buddha", 10), L("buddha", 5)])
    check("3 since du's reply -> capped at 30", peers._effective_gap_days("buddha") == (30.0, 3))
    write_thread("buddha", [L("buddha", 20), L("buddha", 10), L("du", 1)])
    check("du answered last -> reset to base", peers._effective_gap_days("buddha") == (7.0, 0))
    write_thread("marcus", [L("marcus", 9)])
    check("marcus (base 8) 1 unanswered -> 16", peers._effective_gap_days("marcus") == (16.0, 1))

    print("[2] engagement resets (fetch / persona-named look), tray-wide look does not")
    write_thread("smith", [L("smith", 12), L("smith", 8), L("smith", 4)])
    check("smith base 3, 3 unanswered -> 24", peers._effective_gap_days("smith") == (24.0, 3))
    letter_store._append(letter_store._SHADOW, {"ts": now - DAY, "kind": "visit", "via": "letterbox", "peer": None})
    check("tray-wide look (peer None) does NOT reset", peers._unanswered_count("smith") == 3)
    letter_store._append(letter_store._SHADOW, {"ts": now - 10 * DAY, "kind": "visit", "via": "look_letters", "peer": "smith"})
    check("look at smith 10 d ago -> only the letters after it count (2)", peers._unanswered_count("smith") == 2)
    letter_store._append(letter_store._EVENTS, {"letter_id": "smith-1-abc", "status": "read", "ts": now - 6 * DAY,
                                                 "basis": "fetched"})
    check("fetch of a smith letter 6 d ago -> 1 later letter", peers._unanswered_count("smith") == 1)
    letter_store._append(letter_store._EVENTS, {"letter_id": "darwin-1-abc", "status": "read", "ts": now,
                                                 "basis": "fetched"})
    check("another persona's fetch does not reset smith", peers._unanswered_count("smith") == 1)

    Path(letter_store._EVENTS).unlink(missing_ok=True); Path(letter_store._SHADOW).unlink(missing_ok=True)
    print("[3] deliver_due honours the lengthened gap; delivery line logs it")
    import logging
    recs = []

    class H(logging.Handler):
        def emit(self, r):
            recs.append(r.getMessage())
    lg = logging.getLogger("nascence.peers"); lg.addHandler(H()); lg.setLevel(logging.DEBUG); lg.propagate = False
    orig = peers.PERSONAS
    saved = (peers._GLOBAL_MIN_GAP_H, peers.compose_letter, peers._du_world_context,
             peers._self_affirmation_buffer, peers._flag_if_degenerate)
    delivered = []
    async def fake_compose(persona="x", **kw):
        return f"Dear friend, a fresh letter from {persona}, written after a long and quiet while."
    from core import sensorium, peer_metrics
    s_del, s_frz = sensorium.deliver_letter, peer_metrics.freeze_baseline_if_absent
    sensorium.deliver_letter = lambda sender, text: delivered.append(sender)
    peer_metrics.freeze_baseline_if_absent = lambda: None
    peers.compose_letter = fake_compose
    peers._du_world_context = lambda: ""
    peers._self_affirmation_buffer = lambda *a, **k: None
    peers._GLOBAL_MIN_GAP_H = 0
    try:
        # buddha: base 7, last letter 10 d ago, one unanswered -> eff 14 d -> NOT due; smith base 3 answered -> due
        peers.PERSONAS = {"buddha": orig["buddha"], "smith": orig["smith"]}
        shutil.rmtree(peers._CORR_DIR, ignore_errors=True)
        write_thread("buddha", [L("du", 30), L("buddha", 10)])
        write_thread("smith", [L("du", 6), L("smith", 5)])
        ok = asyncio.run(peers.deliver_due())
        check("buddha (10 d, eff 14 d) not due; smith (5 d, base 3 answered long ago, 1 unans -> 6 d) not due either",
              ok is False and delivered == [], str(delivered))
        write_thread("smith", [L("du", 9), L("smith", 7)])         # 7 d >= eff 6 d
        ok = asyncio.run(peers.deliver_due())
        check("smith (7 d >= 6 d) delivers, buddha still waits", ok is True and delivered == ["John Smith"], str(delivered))
        check("due-scan line lists every persona's effective gap",
              any("effective gaps:" in m and "buddha=14d(base 7, unanswered 1)" in m for m in recs), str(recs)[:300])
        check("delivery line carries gap and unanswered",
              any("delivered a letter" in m and "[gap=6d unanswered=1]" in m for m in recs), str(recs)[-300:])
        # kill switch
        peers._SILENCE_BACKOFF = False
        check("kill switch -> base gap", peers._effective_gap_days("buddha") == (7.0, 0))
    finally:
        peers.PERSONAS = orig
        (peers._GLOBAL_MIN_GAP_H, peers.compose_letter, peers._du_world_context,
         peers._self_affirmation_buffer, peers._flag_if_degenerate) = saved
        sensorium.deliver_letter, peer_metrics.freeze_baseline_if_absent = s_del, s_frz
        peers._SILENCE_BACKOFF = True

check("live stores untouched", snap() == BEFORE)
print("FAILED: %s" % FAILS if FAILS else "ALL PASSED")
sys.exit(1 if FAILS else 0)

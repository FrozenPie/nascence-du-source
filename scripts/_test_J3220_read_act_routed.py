"""J-3220 (D-0609, F-3467): act.kind == "read" is routed to the existing read latch in _think(), additive, behind
READ_ACT_ROUTED, with a per-hour cap on routed sittings that actually start.

  [1] _route_act(kind="read") flags the read latch for THIS thought; kind none/letter/other do not; the flag resets on
      every call (never stale).
  [2] READ_ACT_ROUTED False -> never flagged (old behaviour exactly).
  [3] The hourly cap: READ_ACT_MAX_PER_HOUR started sittings in the last hour hold the next read act; sittings older
      than an hour stop counting.
  [4] The latch in _think(): the original condition (_switched or _rereading or _wants_read(_tl)) is kept verbatim as
      _phrase_read, the act only ORs in; with the flag off the condition is the old one; the act schema line and the
      system prompt are untouched (no new hint to Du); 'letter' is not routed.
  [5] Each routed read act logs the sitting it started; only an act-alone sitting is recorded against the cap.
Pure source + a bare-instance call of _route_act; no LLM, no server, no live data (lab_env isolate, empty db).
Run from the worktree root:  python scripts/_test_J3220_read_act_routed.py
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE lab_env)

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


SRC = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

with isolate(db="empty"):
    from nodes import inner_monologue_node as imn  # noqa: E402

    def fresh():
        return imn.InnerMonologueNode.__new__(imn.InnerMonologueNode)

    def route(node, kind, obj="a book"):
        acted = set()
        asyncio.run(node._route_act(None, kind, obj, "The tide is out and the page waits.", "", acted))
        return bool(getattr(node, "_read_act_pending", False)), acted

    # ---- [1] ----
    check(imn.READ_ACT_ROUTED is True and imn.READ_ACT_MAX_PER_HOUR >= 1, "[1] flag default True, cap >= 1")
    n = fresh()
    pend, acted = route(n, "read")
    check(pend and not acted, "[1] read act -> latch flagged, nothing added to `acted` (the latch does the deed)")
    for k in ("none", "letter", "think"):   # kinds with no world-touching branch
        n = fresh()
        n._read_act_pending = True   # a stale flag must be cleared by the next call
        pend, _ = route(n, k)
        check(not pend, f"[1] kind={k!r} -> read latch NOT flagged (stale flag cleared)")

    # ---- [2] ----
    imn.READ_ACT_ROUTED = False
    n = fresh()
    pend, _ = route(n, "read")
    check(not pend, "[2] flag off -> read act never flagged")
    imn.READ_ACT_ROUTED = True

    # ---- [3] ----
    n = fresh()
    cap = imn.READ_ACT_MAX_PER_HOUR
    n._read_act_ts = [time.time() - 60 * i for i in range(cap)]       # cap sittings inside the hour
    pend, _ = route(n, "read")
    check(not pend, f"[3] {cap} routed sittings in the last hour -> next read act held")
    n._read_act_ts = [time.time() - 3700.0] + [time.time() - 60 * i for i in range(cap - 1)]   # one aged out
    pend, _ = route(n, "read")
    check(pend, "[3] a sitting older than an hour no longer counts -> flagged")
    check(len(n._read_act_ts) == cap - 1, "[3] aged-out entry pruned")

# ---- [4] source anchors ----
check("_phrase_read = bool(_switched or _rereading or _wants_read(_tl))" in SRC,
      "[4] original latch condition kept verbatim as _phrase_read")
check("if not _booked and (_phrase_read or _read_act_now):" in SRC, "[4] latch = phrase OR routed act (additive)")
check("if not _booked and (_switched or _rereading or _wants_read(_tl)):" not in SRC,
      "[4] old inline condition replaced (single latch)")
check('elif kind == "read" and READ_ACT_ROUTED:' in SRC and 'kind == "letter"' not in SRC.split("async def _route_act")[1].split("async def _observe_journal")[0],
      "[4] only read is routed in _route_act; letter untouched")
# ---- [5] logging / cap accounting ----
check('"[monologue] READ ACT routed -> sitting started: \'%s\' (act object: %s)%s"' in SRC, "[5] sitting-started log line present")
check("if not _phrase_read:\n                            self._read_act_ts" in SRC,
      "[5] only an act-alone sitting is recorded against the cap")
check("READ ACT routed, no sitting started" in SRC and "READ ACT held by the hourly cap" in SRC,
      "[5] dark/finished and capped outcomes logged")

print("\nFAILS:", fails)
sys.exit(1 if fails else 0)

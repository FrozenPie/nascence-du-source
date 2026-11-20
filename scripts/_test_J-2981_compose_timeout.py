"""J-2981 (F-3668, P-0083): peers.compose_letter timeout budget per hub + compose_timeout logging.
HERMETIC: core.model_client.call_node is a stub (no hub, no network); the quality log is pointed at a temp dir.
  python scripts/_test_J-2981_compose_timeout.py     (exit 0 = all passed)"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                        # BEFORE lab_env (F-2423)
from core import peers, model_client
assert Path(peers.__file__).resolve().is_relative_to(ROOT), peers.__file__

FAILS = []


def check(name, cond, detail=""):
    print("  ok   " if cond else "  FAIL ", name, "" if cond else detail)
    if not cond:
        FAILS.append(name)


tmp = Path(tempfile.mkdtemp(prefix="j2981_"))
peers._PEER_LETTER_QUALITY_LOG = tmp / "peer_letter_quality_log.jsonl"
seen = []
mode = {"raise": False}


async def fake_call_node(url, system, user, **kw):
    seen.append((url, kw.get("timeout")))
    if mode["raise"]:
        raise asyncio.TimeoutError()
    return "  Dear friend, all is well.  "


model_client.call_node = fake_call_node


def rows():
    p = peers._PEER_LETTER_QUALITY_LOG
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


print("[1] timeout resolution")
check("darwin (yi hub :11442) -> 1500", peers._compose_timeout_s("darwin") == 1500)
check("keats/lovelace/buddha -> 1500", all(peers._compose_timeout_s(k) == 1500 for k in ("keats", "lovelace", "buddha")))
check("twain (gemma :11439) -> 600", peers._compose_timeout_s("twain") == 600)
check("marcus/smith/shackleton -> 600", all(peers._compose_timeout_s(k) == 600 for k in ("marcus", "smith", "shackleton")))
check("unknown persona fails open to 600", peers._compose_timeout_s("nobody") == 600)
peers.PERSONAS["twain"]["compose_timeout_s"] = 777
check("per-persona compose_timeout_s beats the hub map", peers._compose_timeout_s("twain") == 777)
del peers.PERSONAS["twain"]["compose_timeout_s"]

print("[2] compose_letter passes the resolved timeout; explicit timeout wins")
t = asyncio.run(peers.compose_letter("darwin"))
check("darwin default -> call_node timeout 1500", seen[-1][1] == 1500, str(seen[-1]))
check("text stripped as before", t == "Dear friend, all is well.", repr(t))
asyncio.run(peers.compose_letter("darwin", timeout=580))
check("explicit timeout=580 wins over the 1500 hub budget", seen[-1][1] == 580, str(seen[-1]))
asyncio.run(peers.compose_letter("darwin", timeout=600))
check("explicit timeout=600 on a yi persona still wins (None sentinel)", seen[-1][1] == 600, str(seen[-1]))
asyncio.run(peers.compose_letter("twain"))
check("twain default -> 600 (shipped value unchanged)", seen[-1][1] == 600, str(seen[-1]))

print("[3] timeout is logged (WARNING + quality-log row) and re-raised")
peers._last_compose_end.clear()
mode["raise"] = True
import logging
class H(logging.Handler):
    def __init__(self): super().__init__(); self.recs = []
    def emit(self, r): self.recs.append(r)
h = H(); peers.logger.addHandler(h)
raised = False
try:
    asyncio.run(peers.compose_letter("darwin", attempt=2))
except (asyncio.TimeoutError, TimeoutError):
    raised = True
peers.logger.removeHandler(h)
check("TimeoutError re-raised unchanged", raised)
r = [x for x in rows() if x.get("event") == "compose_timeout"]
check("one compose_timeout row", len(r) == 1, str(rows()))
if r:
    x = r[0]
    check("row has persona/hub/timeout_s/attempt", x["persona"] == "darwin" and x["hub"] == peers._HUB_MISTRAL
          and x["timeout_s"] == 1500 and x["attempt"] == 2, str(x))
    check("cold_load_likely True on the first call this process", x["cold_load_likely"] is True, str(x))
    check("elapsed_s present", isinstance(x.get("elapsed_s"), float))
check("WARNING logged", any(rec.levelno == logging.WARNING and "TIMED OUT" in rec.getMessage() for rec in h.recs))
mode["raise"] = False
check("a successful call marks the hub warm (cold_load_likely False right after)",
      (asyncio.run(peers.compose_letter("darwin")) and peers._cold_load_likely(peers._HUB_MISTRAL) is False))
check("cold again once idle past the threshold",
      peers._cold_load_likely(peers._HUB_MISTRAL, now=__import__("time").monotonic() + peers._IDLE_UNLOAD_THRESHOLD_S + 5))

print("[4] deliver_daily: a compose timeout still returns False, delivers nothing")
from core import sensorium
delivered = []
sensorium.deliver_letter = lambda name, text: delivered.append(name)
mode["raise"] = True
peers._thread_context = lambda p: ""
peers._du_world_context = lambda: ""
peers._choose_stance = lambda p: None
peers._read_thread = lambda p: []
peers._effective_gap_days = lambda p: (0.0, 0)
ok = asyncio.run(peers.deliver_daily("darwin", force=True))
check("deliver_daily returns False on a timeout", ok is False)
check("nothing delivered", delivered == [])

print("\nFAILED:", FAILS if FAILS else "none")
sys.exit(1 if FAILS else 0)

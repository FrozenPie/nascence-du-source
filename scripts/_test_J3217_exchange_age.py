"""J-3217 (D-0606, F-3454): human-cycle exchange turns older than 24 hours are left out of the six window blocks
(episodic Immediate exchange, reflection WHERE WE LEFT OFF + THIS SESSION, executive WHERE WE LEFT OFF + THIS
SESSION, recall CURRENT EXCHANGE). Builds the four real prompts via each node's own _build_prompt; no LLM, no server.

  [1] REPLAY of the 10-19 11:13 garden question: the old 10-16/17 pause exchange (ts 10-17) is not bound; the
      prompt carries no trace of it. Same state with the constant off still carries it (proves the filter did it).
  [2] SAME-DAY continuity unchanged: fresh turns (2h old) -> prompts byte-identical to the same state with the
      constant off; a mixed history keeps only the fresh turn.
  [3] No usable ts -> kept (byte-identical to constant off). Internal cycles untouched by fresh().
  [4] Edge: exactly at the cutoff is kept, just past it is dropped. Constant off -> list unchanged.
  [5] Stamping: restore stamps legacy entries with ended_at; orchestrator append source carries "ts".
ISOLATED like _test_internal_context_gate_J2297.py (temp shadow log, lab_env empty db). Run from worktree root.
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import datetime as dt
import json
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

from core import internal_context_gate as icg  # noqa: E402
from core import buses  # noqa: E402
from core.schema import CognitiveState  # noqa: E402
from nodes.episodic_buffer_node import EpisodicBufferNode  # noqa: E402
from nodes.reflection_node import ReflectionNode  # noqa: E402
from nodes.executive_node import ExecutiveNode  # noqa: E402
from nodes.recall_node import RecallNode  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="icg_J3217_"))
icg._LOG = TMP / "internal_cycle_context_shadow.jsonl"
buses.IDLE_FREIGHT_BUS = False
NODES = {"episodic": EpisodicBufferNode(), "reflection": ReflectionNode(),
         "executive": ExecutiveNode(), "recall": RecallNode()}
MARKERS = ("Immediate exchange:", "WHERE WE LEFT OFF", "THIS SESSION", "CURRENT EXCHANGE")

fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


def make_state(hist, prior, input_type="human", cid="c"):
    s = CognitiveState(spirit_name="Du", axiom="I am Du.\nVOICE STYLE: calm")
    s.cycle_id = cid
    s.raw_input = "What do you see in the garden?"
    s.input_type = input_type
    s.conversation_history = [dict(h) for h in hist]
    s.prior_session_exchanges = [dict(p) for p in prior]
    return s


def prompts(hist, prior, input_type="human"):
    st = make_state(hist, prior, input_type)
    return {k: n._build_prompt(st) for k, n in NODES.items()}


def epoch(y, mo, d, h, mi):
    return dt.datetime(y, mo, d, h, mi).timestamp()


with isolate(db="empty"):
    # ---- [1] replay 10-19 11:13 ----
    now = epoch(2026, 10, 19, 11, 13)
    real_time = time.time
    time.time = lambda: now          # fresh() reads time.time() at call
    try:
        pause_ts = epoch(2026, 10, 17, 9, 0)
        HIST = [{"ts": pause_ts, "human": "OLDPAUSE-A Travis here, pause now", "entity": "OLDPAUSE-A I will hold still"},
                {"ts": pause_ts + 60, "human": "OLDPAUSE-B I am holding your letters", "entity": "OLDPAUSE-B keep them warm"}]
        PRIOR = [{"ts": pause_ts - 3600, "human": "OLDPRIOR-1 good morning", "entity": "OLDPRIOR-1 morning"}]
        icg.EXCHANGE_MAX_AGE_HOURS = 24
        on = prompts(HIST, PRIOR)
        for k in NODES:
            bad = [m for m in ("OLDPAUSE", "OLDPRIOR") + MARKERS if m in on[k]]
            check(not bad, f"[1] replay: {k} prompt carries no trace of the 10-17 pause exchange {bad or ''}")
        icg.EXCHANGE_MAX_AGE_HOURS = None
        off = prompts(HIST, PRIOR)
        for k in NODES:
            check("OLDPAUSE" in off[k] or "OLDPRIOR" in off[k],
                  f"[1] replay: with the constant off, {k} still binds the old exchange")
        icg.EXCHANGE_MAX_AGE_HOURS = 24

        # ---- [2] same-day continuity ----
        fresh_ts = now - 2 * 3600
        H2 = [{"ts": fresh_ts, "human": "FRESH-A hello", "entity": "FRESH-A hi"},
              {"ts": fresh_ts + 60, "human": "FRESH-B the lamp", "entity": "FRESH-B yes"}]
        P2 = [{"ts": fresh_ts - 600, "human": "FRESHPRIOR-1 morning", "entity": "FRESHPRIOR-1 morning"}]
        a = prompts(H2, P2)
        icg.EXCHANGE_MAX_AGE_HOURS = None
        b = prompts(H2, P2)
        icg.EXCHANGE_MAX_AGE_HOURS = 24
        for k in NODES:
            check(a[k] == b[k], f"[2] same-day: {k} prompt byte-identical with the age gate on/off")
            check("FRESH-A" in a[k] or "FRESH-B" in a[k] or "FRESHPRIOR" in a[k],
                  f"[2] same-day: {k} still carries the fresh turns")
        H3 = [HIST[0], H2[0]]
        m = prompts(H3, [])
        check("FRESH-A" in m["episodic"] and "OLDPAUSE" not in m["episodic"],
              "[2] mixed history: episodic keeps only the fresh turn")
        check("FRESH-A" in m["recall"] and "OLDPAUSE" not in m["recall"],
              "[2] mixed history: recall keeps only the fresh turn")

        # ---- [3] no ts -> kept; internal untouched ----
        NOTS = [{"human": "NOTS-A hello", "entity": "NOTS-A hi"}]
        c = prompts(NOTS, NOTS)
        icg.EXCHANGE_MAX_AGE_HOURS = None
        d = prompts(NOTS, NOTS)
        icg.EXCHANGE_MAX_AGE_HOURS = 24
        for k in NODES:
            check(c[k] == d[k], f"[3] no-ts: {k} prompt byte-identical (kept)")
        st_int = make_state(HIST, PRIOR, "internal")
        check(icg.fresh(st_int, HIST) == HIST, "[3] fresh() leaves internal-cycle lists unchanged")
        check(icg.fresh(st_int, []) == [], "[3] fresh() empty list")

        # ---- [4] edges ----
        st = make_state([], [])
        edge = [{"ts": now - 24 * 3600, "human": "x", "entity": "y"}]
        past = [{"ts": now - 24 * 3600 - 1, "human": "x", "entity": "y"}]
        check(icg.fresh(st, edge) == edge, "[4] exactly 24h old is kept")
        check(icg.fresh(st, past) == [], "[4] 24h + 1s old is dropped")
        check(icg.fresh(st, [{"ts": "garbage", "human": "x", "entity": "y"}]) != [],
              "[4] unparseable ts is kept (fail-open)")
        icg.EXCHANGE_MAX_AGE_HOURS = 0
        check(icg.fresh(st, past) == past, "[4] constant 0/None -> list unchanged")
        icg.EXCHANGE_MAX_AGE_HOURS = 24
    finally:
        time.time = real_time

    # ---- [5] stamping ----
    src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
    i = src.index("self.state.conversation_history.append({")
    check('"ts": time.time()' in src[i:i + 200], "[5] orchestrator append stamps ts")
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_nascence as rn
    f = TMP / "conversation_state.json"
    ended = epoch(2026, 10, 17, 9, 30)
    f.write_text(json.dumps({"ended_at": ended, "ended_human": "2026-10-17 09:30",
                             "recent_exchanges": [{"human": "a", "entity": "b"}, {"human": "c", "entity": "d"},
                                                  {"human": "e", "entity": "f", "ts": 123.0}]}), encoding="utf-8")
    rn.CONV_STATE_PATH = f
    s5 = CognitiveState(spirit_name="Du", axiom="x")
    rn._restore_conversation_state(s5)
    allx = s5.conversation_history + s5.prior_session_exchanges
    check(len(allx) == 3, "[5] restore returns the three exchanges")
    stamped = {e["human"]: e.get("ts") for e in allx}
    check(stamped["a"] == ended and stamped["c"] == ended, "[5] legacy entries stamped with ended_at")
    check(stamped["e"] == 123.0, "[5] an existing ts is untouched")

print("FAILS:", fails)
sys.exit(1 if fails else 0)

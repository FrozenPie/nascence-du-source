"""
Proof for J-3007 (F-3707): nodes/subconscious_node.py _t4_deliberate (via _t4_deliberate_traced, which its caller now uses) appends one row per invocation to
data/logs/t4_chain_trace.jsonl with the full evidence / delta / synthesis text and per-stage latency, without
changing any prompt, parameter or return value.

  [1] full chain (mocked call_node_json): result identical to the core's own return; one row with tension (uncut),
      keystone flag, crossings (id, cosine, relevance word), has_movement, evidence, changed, delta, self_concept,
      arc_entry, per-stage latency, abort_reason None, authored True.
  [2] has_movement=false run: row still carries the FULL evidence text and no delta/synthesis keys; abort_reason set.
  [3] no-delta abort, evidence-stage transport failure and no-crossings abort each write a row with the right reason.
  [4] the three stage calls got exactly the prompts/parameters the source specifies (max_tokens 256/200/768,
      temperature 0.4/0.4/0.6): captured from the mock, compared with the wrapper bypassed (core called directly).
  [5] fail-open: an unwritable log path (a directory) and a raising writer never change the chain's return value.
  [6] the tension label is stored uncut (200+ chars); the keystone flag follows the primary tension.
  [7] scripts/t4_chain_trace_read.py loads the rows, summarises outcomes/latency, and renders a run.
  [8] isolation: log path, memory_edges and world-material are stubbed; nothing under the live data dir is written.

  python scripts/_test_J-3007_t4_chain_trace.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import core  # noqa: E402,F401  (core BEFORE lab_env)
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass
from nodes import subconscious_node as sn  # noqa: E402

assert Path(sn.__file__).resolve().parent.parent == ROOT, f"imported subconscious_node from {sn.__file__}, not {ROOT}"

TMP = Path(tempfile.mkdtemp(prefix="J3007_"))
LOG = TMP / "logs" / "t4_chain_trace.jsonl"
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  ok   " if cond else "  FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---- stubs -----------------------------------------------------------------------------------------------------
sn._T4_CHAIN_TRACE_LOG = LOG
sn.recent_world_material = lambda limit=6: []
import core.memory_edges as _me  # noqa: E402
_me.add_edge = lambda *a, **k: None

CALLS: list[dict] = []
SCRIPT: list = []   # queue of dict-or-Exception, one per stage call


async def fake_call(urls, sys_p, user_p, max_tokens=0, temperature=0.0, **kw):
    CALLS.append({"max_tokens": max_tokens, "temperature": temperature, "sys": sys_p, "user": user_p})
    nxt = SCRIPT.pop(0)
    if isinstance(nxt, Exception):
        raise nxt
    return nxt


sn.call_node_json = fake_call


class _CS:
    spirit_name = "Du"


def make_node(crossings):
    n = object.__new__(sn.SubconsciousNode)
    n._state = {}
    n._t4_retrieve_crossings = lambda q, k=None: list(crossings)
    return n


def rows() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]


def reset():
    CALLS.clear()
    SCRIPT.clear()
    if LOG.exists():
        LOG.unlink()


def run(node, distinct, old="old channel"):
    return asyncio.run(node._t4_deliberate_traced(_CS(), old, "arc", distinct, []))


CROSS = [("ev1", "the bird sang in the draft", 0.62), ("ev2", "I stopped to listen to the wind", 0.47)]
LONG_LABEL = "an unresolved tension about being a built mind " + "x" * 250
PRIM = {"_label": LONG_LABEL, "_keystone": True}
OTHER = {"_label": "second tension"}

# [1] full chain
reset()
SCRIPT += [{"evidence": "EVIDENCE FULL TEXT here", "has_movement": True},
           {"delta": "DELTA FULL TEXT here", "changed": True},
           {"self_concept": "SELF FULL", "arc_entry": "ARC FULL", "changed": True}]
res = run(make_node(CROSS), [PRIM, OTHER])
check("[1] result is the chain's own dict", res.get("changed") is True and res.get("self_concept") == "SELF FULL"
      and res.get("arc_entry") == "ARC FULL" and res.get("abort_reason") is None and res.get("evidence") == "EVIDENCE FULL TEXT here")
rs = rows()
check("[1] exactly one row", len(rs) == 1, str(len(rs)))
r = rs[0] if rs else {}
check("[1] tension uncut + keystone + other count", r.get("tension") == LONG_LABEL and r.get("keystone") is True and r.get("n_other_tensions") == 1)
check("[1] crossings carry id, cosine, relevance word", [c["id"] for c in r.get("crossings", [])] == ["ev1", "ev2"]
      and r["crossings"][0]["cosine"] == 0.62 and isinstance(r["crossings"][0]["word"], str) and r["crossings"][0]["word"])
check("[1] has_movement + full evidence", r.get("has_movement") is True and r.get("evidence") == "EVIDENCE FULL TEXT here")
check("[1] changed + full delta", r.get("changed") is True and r.get("delta") == "DELTA FULL TEXT here")
check("[1] full self_concept + arc_entry", r.get("self_concept") == "SELF FULL" and r.get("arc_entry") == "ARC FULL")
check("[1] per-stage latency numbers", all(isinstance(r.get(k), (int, float)) for k in ("evidence_s", "delta_s", "synthesis_s", "total_s")))
check("[1] authored True, abort_reason None", r.get("authored") is True and r.get("abort_reason") is None)
check("[1] ts present", isinstance(r.get("ts"), float))
full_calls = [dict(c) for c in CALLS]

# [4] parameters / prompts: call the chain body directly (bypassing the wrapper) and compare the captured calls
reset()
SCRIPT += [{"evidence": "EVIDENCE FULL TEXT here", "has_movement": True},
           {"delta": "DELTA FULL TEXT here", "changed": True},
           {"self_concept": "SELF FULL", "arc_entry": "ARC FULL", "changed": True}]
direct = asyncio.run(make_node(CROSS)._t4_deliberate(_CS(), "old channel", "arc", [PRIM, OTHER], []))
check("[4] core called directly writes no row", rows() == [])
check("[4] wrapper and core make identical calls (prompts and params)", full_calls == CALLS)
check("[4] max_tokens 256/200/768, temperature 0.4/0.4/0.6",
      [(c["max_tokens"], c["temperature"]) for c in CALLS] == [(256, 0.4), (200, 0.4), (768, 0.6)])
check("[4] core return equals wrapper return", direct == res)

# [2] has_movement false keeps the evidence text
reset()
SCRIPT += [{"evidence": "still circling, nothing moved", "has_movement": False}]
res2 = run(make_node(CROSS), [PRIM])
r = rows()[0]
check("[2] abort returned unchanged", res2["changed"] is False and "no genuine movement" in res2["abort_reason"])
check("[2] row holds the FULL evidence of a no-movement run", r.get("evidence") == "still circling, nothing moved" and r.get("has_movement") is False)
check("[2] no delta / synthesis keys, abort_reason set", "delta" not in r and "synthesis_s" not in r and r.get("self_concept") is None
      and r.get("abort_reason") == res2["abort_reason"] and r.get("authored") is False)

# [3] other aborts
reset()
SCRIPT += [{"evidence": "moved", "has_movement": True}, {"delta": "", "changed": False}]
run(make_node(CROSS), [PRIM])
r = rows()[0]
check("[3] no-delta abort row", r.get("abort_reason", "").startswith("no specific delta") and r.get("changed") is False and "delta_s" in r)

reset()
SCRIPT += [RuntimeError("all servers exhausted")]
res3 = run(make_node(CROSS), [PRIM])
r = rows()[0]
check("[3] evidence-stage failure row", res3["abort_reason"] == "evidence stage failed" and "all servers exhausted" in r.get("stage_error", "")
      and "evidence_s" in r)

reset()
res3b = run(make_node([]), [{"_label": "t"}])
r = rows()[0]
check("[3] no-crossings row", res3b["abort_reason"].startswith("no lived crossing") and r.get("crossings") == [] and r.get("keystone") is False
      and not CALLS)

# [6] second keystone check: non-keystone primary
check("[6] non-keystone primary -> keystone False", r.get("keystone") is False)

# [5] fail-open
reset()
bad = TMP / "isdir"
bad.mkdir()
sn._T4_CHAIN_TRACE_LOG = bad          # a directory: open(..., "a") raises
SCRIPT += [{"evidence": "e", "has_movement": False}]
res5 = run(make_node(CROSS), [PRIM])
check("[5] unwritable log: chain return unchanged", res5["changed"] is False and "no genuine movement" in res5["abort_reason"])
sn._T4_CHAIN_TRACE_LOG = LOG
orig_w = sn._t4_trace_write
sn._t4_trace_write = lambda row: (_ for _ in ()).throw(RuntimeError("writer boom"))
SCRIPT += [{"evidence": "e", "has_movement": False}]
res5b = run(make_node(CROSS), [PRIM])
check("[5] raising writer: chain return unchanged", res5b["changed"] is False)
sn._t4_trace_write = orig_w

# [7] reader
import t4_chain_trace_read as rd  # noqa: E402
reset()
SCRIPT += [{"evidence": "EVIDENCE FULL TEXT here", "has_movement": True},
           {"delta": "DELTA FULL TEXT here", "changed": True},
           {"self_concept": "SELF FULL", "arc_entry": "ARC FULL", "changed": True}]
run(make_node(CROSS), [PRIM, OTHER])
SCRIPT += [{"evidence": "nothing", "has_movement": False}]
run(make_node(CROSS), [PRIM])
loaded = rd.load(LOG)
sm = rd.summarise(loaded)
check("[7] reader loads 2 rows and summarises", len(loaded) == 2 and sm["runs"] == 2 and sm["authored"] == 1
      and sm["has_movement_true"] == 1 and "evidence_s" in sm["latency"] and sm["outcomes"].get("authored") == 1)
txt = rd.show_run(loaded[0])
check("[7] show_run renders every stage's full text", all(t in txt for t in ("EVIDENCE FULL TEXT here", "DELTA FULL TEXT here", "SELF FULL", "ARC FULL", LONG_LABEL)))
check("[7] reader tolerates a missing file", rd.load(TMP / "nope.jsonl") == [])

# [8] isolation
live = ROOT / "data" / "logs" / "t4_chain_trace.jsonl"
check("[8] live trace file untouched", not live.exists())

print("\nALL OK" if not FAILS else f"\nFAILED: {FAILS}")
sys.exit(0 if not FAILS else 1)

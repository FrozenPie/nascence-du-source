"""
J-3013 (F-3705, F-3708, P-0014): guidance capture hardening. No model is called (call_json is a stub) and the only file
written is a temp-dir log (G._LOG is pointed there; the live data/guidance_shadow_log.jsonl is never opened for write).

  [1] prompt text: no filled-in answers, no connects_to, quote required, enums described in words
  [2] quote_anchored: substring, case, whitespace, curly quotes; rejects invented / reworded / too short quotes; ellipsis joins pass only if every piece is verbatim
  [3] is_pure_question: bare questions dropped, a question WITH a statement kept
  [4] capture_shadow (stub model): anchored -> accepted, no connects_to key, status CAPTURED, quote stored;
      unanchored -> is_guidance False + reason no_anchor logged; pure question -> reason question_only, model never called;
      model negative -> unchanged negative row
  [5] old rows (with connects_to, status SHADOW) still read by _iter_shadow
  [6] live log byte-identical

  python scripts/_test_J-3013_guidance_capture_anchor.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/

import asyncio
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402,F401  (BEFORE anything that could hijack sys.path)
from core import guidance_learning as G  # noqa: E402

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def _snap(p: Path):
    return None if not p.exists() else hashlib.sha256(p.read_bytes()).hexdigest()


_LIVE = (ROOT / "data" / "guidance_shadow_log.jsonl", Path(r"C:\Nascence") / "data" / "guidance_shadow_log.jsonl")
_before = [_snap(p) for p in _LIVE]

tmp = Path(tempfile.mkdtemp(prefix="J-3013_"))
G._LOG = tmp / "guidance_shadow_log.jsonl"

RAW = ("Lets first sow some seeds in what is there. You have a bag of seeds. "
       "This growth is not just a metaphor, but a physical act you can watch and learn from.")

print("[1] prompt text")
s = G._SELF_EXPLAIN_SYS
check("connects_to" not in s, "connects_to is gone from the prompt")
check('"is_guidance": true' not in s and '"domain": "self"' not in s, "no filled-in is_guidance / domain value in the schema line")
check('"quote"' in s and "exactly" in s, "quote is requested, verbatim")
check("self, world or method" in s, "domain enum is described in words")

print("[2] quote_anchored")
check(G.quote_anchored("growth is not just a metaphor", RAW), "verbatim span passes")
check(G.quote_anchored("GROWTH   is not just\n a METAPHOR", RAW), "case and whitespace insensitive")
check(G.quote_anchored('\u201cgrowth is not just a metaphor\u201d', RAW), "outer curly quotes stripped")
check(G.quote_anchored("Travis\u2019s idea is fine", "travis's idea is fine indeed"), "curly apostrophe folded")
check(not G.quote_anchored("waiting for conditions to be perfect first", RAW), "an invented span fails")
check(G.quote_anchored("sow some seeds ... physical act you can watch", RAW), "two real spans joined by an ellipsis pass (each piece verbatim)")
check(G.quote_anchored("sow some seeds… physical act you can watch", RAW), "unicode ellipsis handled the same")
check(not G.quote_anchored("sow some seeds ... waiting for conditions to be perfect", RAW), "an ellipsis join with one invented piece fails")
check(not G.quote_anchored("seeds", RAW), "a too-short span fails")
check(not G.quote_anchored("", RAW) and not G.quote_anchored(None, RAW), "empty / None fails")
long_raw = "x " * 400 + "the lesson is here in the tail of a long message"
check(G.quote_anchored("the lesson is here in the tail", long_raw), "checked against the FULL raw_input, not the first 400 chars")

print("[3] is_pure_question")
check(G.is_pure_question("Is it burning? Have you listened to it yet?"), "all questions -> pure question")
check(G.is_pure_question("Now look at the fire in the study, do you notice anything different when you watch it burn?"),
      "single long question")
check(not G.is_pure_question("That was not the question. You have a record player in the study. Have you listened to it yet?"),
      "a question WITH a statement is not pure")
check(not G.is_pure_question("What you see is a representation of me, like I am on live TV"), "no trailing ? -> not a question")
check(not G.is_pure_question(""), "empty is not a question")


class Stub:
    def __init__(self, ans):
        self.ans, self.calls = ans, 0

    async def __call__(self, *a, **k):
        self.calls += 1
        return self.ans


def run(ans, raw, ctx=None):
    st = Stub(ans)
    G._LOG.write_text("", encoding="utf-8") if G._LOG.exists() else None
    rec = asyncio.run(G.capture_shadow(st, ["http://stub"], raw, "cyc-1", ctx))
    rows = [json.loads(x) for x in G._LOG.read_text(encoding="utf-8").splitlines()] if G._LOG.exists() else []
    return rec, rows, st.calls


print("[4] capture_shadow")
good = {"is_guidance": True, "quote": "This growth is not just a metaphor", "principle": "Growth is a physical act to watch.",
        "why": "w", "scope": "s", "domain": "world", "confidence": 0.8, "connects_to": "something confabulated"}
rec, rows, calls = run(good, RAW)
check(rec is not None and rows and rows[-1]["is_guidance"] is True, "anchored capture accepted and logged")
check("connects_to" not in rec and "connects_to" not in rows[-1], "no connects_to in the record even if the model sends one")
check(rec["status"] == "CAPTURED" and rec["capture_v"] == 2 and rec["quote"].startswith("This growth"),
      "status CAPTURED, capture_v 2, quote stored")
check(rec["domain"] == "world" and rec["origin"] == "guidance_from_travis" and rec["source"] == "Travis",
      "the fields integrate_guidance reads are unchanged")

bad = dict(good, quote="you should not wait for conditions to be perfect", principle="Plant your intentions now.")
rec, rows, calls = run(bad, RAW)
check(rec is None and rows[-1]["is_guidance"] is False and rows[-1]["reason"] == "no_anchor", "invented quote -> no_anchor logged")
check(rows[-1]["principle_rejected"].startswith("Plant") and "quote_claimed" in rows[-1], "the loss is visible: rejected principle + claimed quote kept")

noq = {k: v for k, v in good.items() if k != "quote"}
rec, rows, _ = run(noq, RAW)
check(rec is None and rows[-1]["reason"] == "no_anchor", "missing quote -> no_anchor")

rec, rows, calls = run(good, "Is it burning? Have you listened to the record player in the study yet or not?")
check(rec is None and calls == 0 and rows[-1]["reason"] == "question_only", "pure question: model not called, question_only logged")

rec, rows, calls = run({"is_guidance": False}, RAW)
check(rec is None and rows[-1] == {**rows[-1], "is_guidance": False} and "reason" not in rows[-1] and calls == 1,
      "model negative: plain negative row, no reason")

rec, rows, calls = run(good, "too short")
check(rec is None and calls == 0 and not rows, "the existing length gate is unchanged")

print("[5] old rows still read")
G._LOG.write_text(json.dumps({"ts": 1.0, "cycle_id": "old", "raw_input": "x", "is_guidance": True, "principle": "p",
                              "connects_to": "old text", "status": "SHADOW", "domain": "self"}) + "\n", encoding="utf-8")
old = list(G._iter_shadow())
check(len(old) == 1 and old[0]["connects_to"] == "old text", "an old row with connects_to / status SHADOW is read intact")

print("[6] live log untouched")
check([_snap(p) for p in _LIVE] == _before, "live guidance_shadow_log.jsonl byte-identical (this tree and C:/Nascence)")

print("ALL OK" if FAILS == 0 else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)

"""J-2980 (F-3665): checks for the P-0083 no-reply letter change in core/peers.py. Zero LLM, hermetic.
  python scripts/_test_J2980_letter_recycling.py        (exit 0 = every check passed)
Covers: the capped last-own-letter thread context, the no_reply user prompt (and that the default prompt is
byte-for-byte unchanged), the deterministic overlap measure, and deliver_daily end to end with a stub model
(overlap row logged, delivery NOT gated by it, compose_letter not given no_reply when Du replied)."""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import peers  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -- " + detail))
    if not ok:
        FAILS.append(name)


TMP = Path(tempfile.mkdtemp(prefix="j2980_"))
peers._CORR_DIR = TMP / "Correspondence"
peers._PEER_LETTER_QUALITY_LOG = TMP / "q.jsonl"


def write_thread(persona, rows):
    d = peers._CORR_DIR / persona
    d.mkdir(parents=True, exist_ok=True)
    (d / "thread.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


S = [f"Sentence number {i} of a letter that is certainly longer than forty characters long." for i in range(30)]
LONG = " ".join(S)                                    # > 600 chars
row = lambda frm, text, t=0: {"ts": t, "from": frm, "text": text}

# --- 1. _cap_letter
c = peers._cap_letter(LONG)
check("cap: long letter shortened to the cap", len(c) <= peers._NO_REPLY_LETTER_CAP + 6, str(len(c)))
check("cap: ends at a sentence end plus marker", c.endswith(". [...]"), c[-30:])
check("cap: short letter unchanged", peers._cap_letter("Short one.") == "Short one.")
check("cap: no sentence end -> word end", peers._cap_letter("word " * 200).endswith(" [...]"))

# --- 2. _thread_context
write_thread("smith", [row("smith", "A1 " + LONG), row("du", "His own letter, kept whole."),
                       row("smith", "B2 " + LONG), row("smith", "C3 " + LONG)])
full = peers._thread_context("smith")
check("default context: all four rows in full (unchanged)", full.count("Sentence number 29") == 3 and "His own letter" in full)
nr = peers._thread_context("smith", no_reply=True)
check("no_reply context: only the LAST own letter", "C3 " in nr and "B2 " not in nr and "A1 " not in nr, nr[:80])
check("no_reply context: that letter is capped", "[...]" in nr and "Sentence number 29" not in nr)
check("no_reply context: Du's row kept whole", "His own letter, kept whole." in nr)
write_thread("smith", [])
check("no_reply on empty thread -> empty string", peers._thread_context("smith", no_reply=True) == "")

# --- 3. _build_user
d = peers._build_user("T", "D", "R", None)
check("default _build_user unchanged (no new line, old label)",
      peers._NO_REPLY_LINE not in d and "Your correspondence so far" in d)
check("default signature output identical with no_reply=False",
      peers._build_user("T", "D", "", "challenge") == peers._build_user("T", "D", "", "challenge", no_reply=False))
n = peers._build_user("T", "D", "", None, no_reply=True)
check("no_reply _build_user: new label + the plain line, before 'Write your letter now.'",
      peers._NO_REPLY_THREAD_LABEL in n and n.index(peers._NO_REPLY_LINE) < n.index("Write your letter now."))
check("no_reply line asks for something new, adds no wanted outcome",
      "something new from your own world" in peers._NO_REPLY_LINE)
check("no_reply with empty thread (first letter) adds nothing",
      peers._NO_REPLY_LINE not in peers._build_user("", "D", "", None, no_reply=True))

# --- 4. overlap measure
own = [row("smith", " ".join(S[:10])), row("du", S[20] + " " + S[21]), row("smith", " ".join(S[10:20]))]
ov = peers._letter_overlap("smith", " ".join(S[5:15]), own)
check("overlap: 10 of 10 sentences copied across two own letters", (ov["sentences"], ov["copied"]) == (10, 10), str(ov))
ov = peers._letter_overlap("smith", " ".join(S[:5] + ["A brand new sentence that is definitely forty characters long, yes."]), own)
check("overlap: 5 of 6", (ov["sentences"], ov["copied"]) == (6, 5) and abs(ov["copied_share"] - 0.8333) < 1e-3, str(ov))
check("overlap: Du's own sentences are not counted as own letters",
      peers._letter_overlap("smith", S[20] + " " + S[21], own)["copied"] == 0)
check("overlap: case/whitespace normalised",
      peers._letter_overlap("smith", S[0].upper().replace(" ", "  "), own)["copied"] == 1)
check("overlap: short sentences ignored", peers._letter_overlap("smith", "Hello there. Yes. No.", own)["sentences"] == 0)
check("overlap: only the last 4 rows count",
      peers._letter_overlap("smith", S[0], [row("smith", S[0])] + [row("du", "x")] * 4)["copied"] == 0)

# --- 5. deliver_daily end to end (stubbed model, delivery, side stores)
from core import sensorium, peer_metrics  # noqa: E402
calls, delivered = [], []


async def fake_compose(persona="x", **kw):
    calls.append(kw)
    return " ".join(S[:6])                                 # a letter that is 100 % copy of the thread


sensorium.deliver_letter = lambda name, text: delivered.append(text)
peer_metrics.freeze_baseline_if_absent = lambda *a, **k: None
peers.compose_letter = fake_compose
peers._du_world_context = lambda: "ctx"
peers._self_affirmation_buffer = lambda *a, **k: None
peers._choose_stance = lambda persona: None
peers._effective_gap_days = lambda persona: (0.0, 0)
peers._last_delivery_ts = lambda persona: 0.0

write_thread("smith", [row("smith", " ".join(S[:6]), 1), row("smith", " ".join(S[6:12]), 2)])
ok = asyncio.run(peers.deliver_daily("smith", force=True))
q = [json.loads(l) for l in peers._PEER_LETTER_QUALITY_LOG.read_text(encoding="utf-8").splitlines()]
ovr = [r for r in q if r.get("event") == "letter_overlap"]
check("e2e no-reply: copied letter is STILL delivered (observe-only)", ok is True and len(delivered) == 1)
check("e2e no-reply: compose_letter told no_reply=True", calls and calls[-1].get("no_reply") is True, str(calls))
check("e2e no-reply: one overlap row, share 1.0, no_reply true",
      len(ovr) == 1 and ovr[0]["copied_share"] == 1.0 and ovr[0]["no_reply"] is True and ovr[0]["persona"] == "smith", str(ovr))

write_thread("smith", [row("smith", " ".join(S[:6]), 1), row("du", "A reply from him to answer.", 2)])
calls.clear()
asyncio.run(peers.deliver_daily("smith", force=True))
ovr = [json.loads(l) for l in peers._PEER_LETTER_QUALITY_LOG.read_text(encoding="utf-8").splitlines()
       if '"letter_overlap"' in l]
check("e2e replied: compose_letter NOT given no_reply", "no_reply" not in calls[-1], str(calls[-1].keys()))
check("e2e replied: overlap row says no_reply false", ovr[-1]["no_reply"] is False)

write_thread("smith", [])
calls.clear()
asyncio.run(peers.deliver_daily("smith", force=True))
check("e2e first letter: compose_letter NOT given no_reply", "no_reply" not in calls[-1])

# a broken log path must not change delivery
peers._PEER_LETTER_QUALITY_LOG = TMP / "afile" / "q.jsonl"
(TMP / "afile").write_text("block", encoding="utf-8")
delivered.clear()
write_thread("smith", [row("smith", " ".join(S[:6]), 1)])
check("e2e: a failing overlap log write never blocks delivery",
      asyncio.run(peers.deliver_daily("smith", force=True)) is True and len(delivered) == 1)

print("\n%d failed" % len(FAILS) if FAILS else "\nall checks passed")
sys.exit(1 if FAILS else 0)

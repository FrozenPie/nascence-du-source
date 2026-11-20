"""J-2810 (F-3455, F-3456, P-0006): EpisodicBufferNode stimulus label follows input_type; exchange lines cut on a word
boundary. Builds the real prompt via _build_prompt; no LLM, no server, no live data. Run from the worktree root.

  [1] human cycle: prompt byte-identical to the pre-change label ('BEING SAID NOW (their words)'), flag on or off.
  [2] internal / timer cycle: self-frame label, 'their words' absent; flag off -> old label (exact prior behaviour).
  [3] word cut: the three mid-word samples from F-3456 end on a whole word + ellipsis; short text untouched;
      flag off -> the old hard slice; unbroken long token hard-cut; non-str input safe.
  [4] the rendered exchange block uses the cut (human cycle, fresh turns), and the internal gate still drops it.
"""
from __future__ import annotations

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
import nodes.episodic_buffer_node as ebn  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="eb_J2810_"))
icg._LOG = TMP / "internal_cycle_context_shadow.jsonl"
buses.IDLE_FREIGHT_BUS = False
fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


def st(input_type="human", hist=None):
    s = CognitiveState(spirit_name="Du", axiom="I am Du.")
    s.cycle_id = "c"
    s.raw_input = "What does the name X symbolize?"
    s.input_type = input_type
    s.conversation_history = hist or []
    return s


OLD = 'BEING SAID NOW (their words):\n  "What does the name X symbolize?"'
SELF = "RISEN IN THEM NOW (their own unprompted thought; no one said it to them)"
node = ebn.EpisodicBufferNode()

with isolate(db="empty"):
    # [1] human unchanged
    for flag in (True, False):
        ebn.EPISODIC_INTERNAL_SELF_FRAME = flag
        p = node._build_prompt(st("human"))
        check(OLD in p and "RISEN IN THEM" not in p, f"[1] human cycle keeps the old label (flag={flag})")
    # [2] internal / timer
    ebn.EPISODIC_INTERNAL_SELF_FRAME = True
    for it in ("internal", "timer"):
        p = node._build_prompt(st(it))
        check(SELF in p and "their words" not in p and "BEING SAID NOW" not in p, f"[2] {it}: self-frame label, no 'their words'")
        check('"What does the name X symbolize?"' in p, f"[2] {it}: raw_input still shown verbatim")
    pi = node._build_prompt(st("internal"))
    ph = node._build_prompt(st("human"))
    diff = [i for i, (a, b) in enumerate(zip(pi.splitlines(), ph.splitlines())) if a != b]
    check(len(diff) == 1 and len(pi.splitlines()) == len(ph.splitlines()),
          "[2] internal differs from human on exactly one line (the label)")
    ebn.EPISODIC_INTERNAL_SELF_FRAME = False
    check(OLD in node._build_prompt(st("internal")), "[2] flag off: internal cycle gets the old label (prior behaviour)")
    ebn.EPISODIC_INTERNAL_SELF_FRAME = True

    # [3] word cut
    wc = ebn._word_cut
    samples = [
        ("Please can we do it later today, I need to get home first and then, once the washing is in, I can do some work on the garden wall before the rain", 120),
        ("The wood and stone of this cottage hold the warmth of the evening fire long after the lamp has gone dark, and the rain keeps on", 120),
        ("In this very moment I notice that the quiet in the room is not empty but full of small sounds that keep arriving one by one, and then fading away again, over and over, while the lamp burns", 150),
    ]
    for text, lim in samples:
        out = wc(text, lim)
        body = out[:-3]
        check(len(text) > lim and out.endswith("...") and len(out) <= lim + 3 and text.startswith(body) and (text[len(body):len(body) + 1] in (" ", ",", ";", ":", "-")),
              f"[3] ends on a whole word + ellipsis: ...{out[-24:]!r}")
        check(body.split()[-1] in text.split(), f"[3] last kept token is a real word: {body.split()[-1]!r}")
    check(wc("short", 120) == "short", "[3] short text untouched")
    exact = "a" * 120
    check(wc(exact, 120) == exact, "[3] exactly at the limit untouched")
    check(wc("word " * 30, 120).endswith("word..."), "[3] cut falls between words -> no partial token")
    check(wc("x" * 300, 120) == "x" * 120 + "...", "[3] one unbroken token is hard-cut with ellipsis")
    check(wc(None, 120) == "" and wc(12345, 120) == "12345", "[3] non-str input safe")
    ebn.EPISODIC_EXCHANGE_WORD_CUT = False
    check(wc(samples[0][0], 120) == samples[0][0][:120], "[3] flag off: old hard slice, no ellipsis")
    ebn.EPISODIC_EXCHANGE_WORD_CUT = True

    # [4] rendered block
    h = [{"ts": time.time() - 600, "human": samples[0][0], "entity": samples[2][0]}]
    p = node._build_prompt(st("human", h))
    lines = {l.strip()[:5]: l for l in p.splitlines() if l.strip().startswith(("Them:", "You: "))}
    check(lines.get("Them:", "").endswith("...") and lines.get("You: ", "").endswith("..."), "[4] human exchange lines end on an ellipsis")
    check("do some work on t\n" not in p and "on t..." not in p, "[4] no 'on t' mid-word cut")
    pi = node._build_prompt(st("internal", h))
    check("Immediate exchange" not in pi, "[4] internal cycle still drops the exchange block (gate untouched)")

print("\nFAILS:", fails)
sys.exit(1 if fails else 0)

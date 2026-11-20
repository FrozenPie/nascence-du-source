"""J-2949 (F-3644): the seeded doubt is no longer cut mid-word. Hermetic: pure functions only, no LLM, no live file.
  python scripts/_test_J-2949_si_truncation.py     # exit 0 = ALL OK"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core  # noqa: E402
from core import doubt_seed as ds, self_interrogation as si  # noqa: E402
F = 0
def check(c, l):
    global F
    print(("  ok   " if c else "  FAIL ") + l); F += 0 if c else 1
short = "Am I sure this is real? Maybe not."
check(ds.cap_on_sentence(short) == short, "short text unchanged")
long = ("I keep assuming the pattern holds because it feels familiar. " * 4 + "Perhaps that familiarity is the only evidence I have. "
        "And what if the familiarity itself is borrowed from somewhere I have not looked at closely enough yet to say")
out = ds.cap_on_sentence(long, 400)
check(len(out) <= 400 and out[-1] in ".!?", "long text ends on a sentence boundary: " + out[-30:])
nos = "wordy " * 100
o2 = ds.cap_on_sentence(nos, 400)
check(len(o2) <= 401 and o2.endswith("\u2026") and not o2[:-1].endswith("wor"), "no sentence end: cut on space with ellipsis")
check(si.REFLECTION_STORE_CHARS >= 700, "stored reflection cap covers max_tokens=180 output")
print("ALL OK" if not F else f"{F} FAILED"); sys.exit(1 if F else 0)

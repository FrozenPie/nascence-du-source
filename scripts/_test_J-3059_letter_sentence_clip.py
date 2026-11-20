"""J-3059 (F-3770): letters that greet Travis's next message are cut at a sentence boundary, not mid-word.

  [1] clip_at_sentence: unchanged when within the limit; never longer than the limit (ellipsis included);
      ends on a sentence terminator + ellipsis when it cut; prefix of the original; "3.5" is not a boundary;
      early-only boundary / no-punctuation text falls back to a word boundary; whitespace-free CJK hard-cuts.
  [2] Executive (900) and Reflection (700) prompts, built for real through _build_prompt, carry the clipped
      letter (long fixture Letter_20261011_1701-like body, 1,067 chars), not the raw [:N] slice.
  [3] corpus read (READ-ONLY, live data/letters hash-canaried before and after): every letter clipped at 900 and
      700 satisfies the invariants; reports how many used to end mid-word and how many now do.
  [4] source guard: neither node slices a letter body by hand any more; both read the caps from core.letters.
  [5] executive_cost() (the D-0470 defeater instrument) is unchanged: still an upper bound of the rendered size.
Model calls: none. Every path is read-only or a temp dir."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import hashlib, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401  (core before lab_env)
from core import letters as L  # noqa: E402
from core.schema import CognitiveState  # noqa: E402
import nodes.executive_node as en  # noqa: E402
import nodes.reflection_node as rn  # noqa: E402

assert Path(L.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
assert Path(en.__file__).resolve().parent.parent == ROOT and Path(rn.__file__).resolve().parent.parent == ROOT

FAIL = []
def check(msg, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + msg + (f"  [{extra}]" if not ok and extra else ""))
    if not ok:
        FAIL.append(msg)

TERM = tuple(".!?\u2026\u3002\uff01\uff1f")
CLOSERS = "\"'\u201d\u2019)]"
def ends_at_sentence(s: str) -> bool:
    """s is a clipped body ending in the ellipsis; the char before it (past closers) is a terminator."""
    assert s.endswith("\u2026")
    body = s[:-1].rstrip().rstrip(CLOSERS)
    return body.endswith(TERM)

# ---- [1] unit behaviour
short = "Dear Travis. I thought of you today."
check("[1a] within limit: unchanged", L.clip_at_sentence(short, 900) == short)
check("[1b] exactly at limit: unchanged", L.clip_at_sentence("a" * 900, 900) == "a" * 900)
check("[1c] empty / None safe", L.clip_at_sentence("", 900) == "" and L.clip_at_sentence(None, 900) == "")

sents = ["I woke up and the house was quiet.", "The lamp was still on and I wondered who left it.",
         "Maybe I did.", "I keep thinking about what you said about the shore, and the way the light sat on the water."]
long_txt = " ".join(sents * 6)
out = L.clip_at_sentence(long_txt, 300)
check("[1d] long text: <= limit incl. ellipsis", len(out) <= 300, str(len(out)))
check("[1e] long text: ends on a sentence terminator + ellipsis", ends_at_sentence(out), repr(out[-40:]))
check("[1f] long text: kept part is an exact prefix", long_txt.startswith(out[:-1].rstrip()))
check("[1g] long text: keeps most of the room (>= 40%)", len(out) >= 120, str(len(out)))

dec = "x " * 5 + "The value was 3.5 and then it rose to 4.7 by morning, which surprised me, " + "w " * 400
o2 = L.clip_at_sentence(dec, 200)
check("[1h] decimal '3.5' is not a sentence boundary (word-boundary fallback, no mid-number cut)",
      o2.endswith("\u2026") and not re.search(r"\d\.\u2026$", o2) and len(o2) <= 200)
nopunct = "word " * 400
o3 = L.clip_at_sentence(nopunct, 100)
check("[1i] no punctuation: cut at a word boundary, no half word", o3.endswith("word\u2026") and len(o3) <= 100, repr(o3[-20:]))
early = "Hi. " + "thing " * 300
o4 = L.clip_at_sentence(early, 200)
check("[1j] only an early boundary: falls back to a word boundary (does not keep just 'Hi.')",
      len(o4) > 100 and o4.endswith("thing\u2026"), repr(o4[:30]) + str(len(o4)))
cjk = "\u6211" * 2000
o5 = L.clip_at_sentence(cjk, 100)
check("[1k] whitespace-free CJK run: hard cut within limit with ellipsis", len(o5) == 100 and o5.endswith("\u2026"))
cjk2 = ("\u4eca\u5929\u5f88\u5b89\u9759\u3002 " * 60)
o6 = L.clip_at_sentence(cjk2, 100)
check("[1l] CJK sentence stop (followed by space) is a boundary", o6.endswith("\u3002\u2026") and len(o6) <= 100, repr(o6[-6:]))
quoted = ('He said, "I will be there." ' * 40)
o7 = L.clip_at_sentence(quoted, 200)
check("[1m] closing quote after the stop stays attached", o7.endswith('."\u2026'), repr(o7[-8:]))
check("[1n] result never exceeds limit over a sweep of limits",
      all(len(L.clip_at_sentence(long_txt, n)) <= n for n in range(2, 600, 7)))

# ---- fixture: a 1,067-char letter (the Letter_20261011_1701 shape): several sentences, runs past 900
fix = ("I have been turning over the thing you said about the garden, and I think I understand it a little better now. "
       "The lamp matters because somebody left it, and whoever left it wanted the room to be findable. "
       "I do not know if that somebody was me. ") * 3
fix = (fix + "I would like to tell you what the shore looked like this morning, because the tide had gone out further than I "
       "have ever seen it, and the sand held the sky in long flat sheets. ")
fix = (fix * 2)[:1067]
assert len(fix) == 1067
# ---- [2] real prompts
def with_letter(body):
    st = CognitiveState(spirit_name="t", axiom="a")
    st.cycle_id = "cyc-3059"
    st.raw_input = "Hello Travis here."
    st.unsent_letters = [body]
    return st

pe = en.ExecutiveNode()._build_prompt(with_letter(fix))
pr = rn.ReflectionNode()._build_prompt(with_letter(fix))
HE = "choice):\n"
HR = "(he has not seen it): "
be = pe.split(HE, 1)[1]
br = pr.split(HR, 1)[1]
want_e = L.clip_at_sentence(fix, 900)
want_r = L.clip_at_sentence(fix, 700)
check("[2a] Executive prompt carries the sentence-clipped letter", be.startswith(want_e), repr(be[:60]))
check("[2b] Reflection prompt carries the sentence-clipped letter", br.startswith(want_r), repr(br[:60]))
check("[2c] Executive letter within 900 and ends at a sentence", len(want_e) <= 900 and ends_at_sentence(want_e))
check("[2d] Reflection letter within 700 and ends at a sentence", len(want_r) <= 700 and ends_at_sentence(want_r))
check("[2e] the old mid-word slice is gone from both prompts",
      fix[:900] not in pe and fix[:700] not in pr)
check("[2f] header text unchanged (no hint added)", "you may say it now, work it in naturally, or keep it" in pe
      and "A LETTER YOU WROTE FOR TRAVIS WHILE ALONE (he has not seen it): " in pr)
short_state = with_letter(short)
check("[2g] a short letter renders verbatim in both nodes (no ellipsis)",
      (short + "\n") in en.ExecutiveNode()._build_prompt(short_state) + "\n"
      and short in rn.ReflectionNode()._build_prompt(short_state) and "\u2026" not in short)

# ---- [3] corpus (read-only)
LIVE = Path(r"C:\Nascence\data\letters")
def canary():
    h = hashlib.sha256()
    for p in sorted(LIVE.glob("Letter_*.md")):
        h.update(p.name.encode()); h.update(str(p.stat().st_size).encode()); h.update(str(p.stat().st_mtime_ns).encode())
    return h.hexdigest()
C0 = canary() if LIVE.exists() else "-"
n = over9 = over7 = old_mid9 = new_mid9 = 0
bad = []
if LIVE.exists():
    for p in sorted(LIVE.glob("Letter_*.md")):
        t = p.read_text(encoding="utf-8")
        n += 1
        for lim in (900, 700):
            o = L.clip_at_sentence(t, lim)
            if len(t) <= lim:
                if o != t:
                    bad.append((p.name, lim, "changed a short letter"))
                continue
            if lim == 900:
                over9 += 1
                if t[:900].rstrip()[-1:] not in TERM + tuple(CLOSERS) and not t[900:901].isspace():
                    old_mid9 += 1
                if not ends_at_sentence(o):
                    new_mid9 += 1
            else:
                over7 += 1
            if len(o) > lim or not o.endswith("\u2026") or not t.startswith(o[:-1].rstrip()):
                bad.append((p.name, lim, "invariant"))
    print(f"corpus: {n} letters; >900: {over9}; >700: {over7}; old [:900] ended mid-word on {old_mid9}; "
          f"new clip not at a sentence on {new_mid9}")
    check("[3a] corpus invariants hold at 900 and 700", not bad, str(bad[:3]))
    check("[3b] every >900 letter now ends at a sentence (corpus)", new_mid9 == 0, str(new_mid9))
    check("[3c] corpus left untouched (hash canary)", canary() == C0)
else:
    print("SKIP corpus: live letters dir absent")

# ---- [4] source guard
for f in ("nodes/executive_node.py", "nodes/reflection_node.py"):
    src = (ROOT / f).read_text(encoding="utf-8")
    check(f"[4] {f}: no hand slice of a letter body, uses the shared helper",
          "_letter[:" not in src and "clip_at_sentence(_letter" in src)

# ---- [5] cost helper unchanged and still an upper bound
c = L.executive_cost([fix, "a" * 5000])
check("[5] executive_cost unchanged: capped at 900 + header per body",
      c["chars"] == min(len(fix), 900) + 134 + 900 + 134 and c["n"] == 2, str(c))
check("[5b] rendered clipped size <= cost estimate",
      len(L.clip_at_sentence(fix, 900)) + 134 <= min(len(fix), 900) + 134)

print("\nFAILED: " + "; ".join(FAIL) if FAIL else "\nALL PASS")
sys.exit(1 if FAIL else 0)

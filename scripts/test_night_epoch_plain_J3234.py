"""scripts/test_night_epoch_plain_J3234.py (J-3234, D-0623, F-3776): night.epoch writes plain words for NEW rows.

No LLM, no live data. core is imported FIRST and asserted to be this tree; lab_env.isolate() sandboxes the stores.
  [1] mood is the felt label only: no digit, no '=', from a real felt_text() string
  [2] impression from real-shape replay snippets (taken from stored night_ rows): no bracket, no key=number, no digit-eq, ends on a sentence boundary, <= 300
  [3] nothing readable -> the plain fallback; never raises on odd input
  [4] epoch() end to end in the sandbox store: the stored row carries no 'valence=' / '[' ; retrieve_epoch path untouched (still returns it)
"""
from __future__ import annotations
import re, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import night, mood

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

BAD = re.compile(r"\[|\]|\w=[-+]?\d|valence|arousal")
_FULL = [   # real shapes (night_ rows in a 11-02 backup), widened, then cut at 90 chars exactly as replay_strengthen does
    "[My study note: 'The Methodical Mind: Navigating Fact and Method in Science'] The method matters more than the fact.",
    "[My study note: 'Understanding Telephone Technology' \ufffd on 'How it Works' \ufffd subject: wires and switchboards]",
    "[From 'How it Works Dealing in simple language with steam electricity'] The engine turns. Then the wheel turns slowly.",
    "[From 'About You Second Edition'] individuate \ufffd and that this was the beginning of something larger than he knew\n",
    "[Looked up: 'Environment' (pursuit: How do environmental sounds, such as rain, shape attention?)] Rain is steady.",
    "[My study note: 'The Uncertainty of Historical Narratives'] *Historical accounts are made, not found.*",
    "[From 'Symbolic Logic'] pg-xix\n\n\ufffd 4.\n\n\n\n_What is implied, in a Proposition, by the word all_",
]
SNIPS = [t[:90] for t in _FULL] + ["I walked to the shore. The tide was out and the stones were warm."]

class _Felt:
    primary = "unsettled"; valence = -0.15; arousal = 0.43; joy = 0.25; fear = 0.13; trust = 0.1; anger = 0.0; surprise = 0.0; disgust = 0.0

print("[1] mood word")
raw = mood.felt_text(_Felt())
check("the raw felt string has the numbers (premise)", "valence=" in raw)
w = night._epoch_mood_word(raw)
check("felt label only", w == "unsettled")
check("no digit, no '='", not re.search(r"[\d=]", w))
check("None / garbage -> quiet", night._epoch_mood_word(None) == "quiet" and night._epoch_mood_word("0.3 = x: y") == "quiet")

print("[2] impression")
for i in range(0, len(SNIPS) - 2):
    imp = night._epoch_impression(SNIPS[i:i + 3])
    check(f"window {i}: clean, <=300, sentence end: {imp[:70]!r}", not BAD.search(imp) and len(imp) <= 300 and imp[-1] in ".!?")
imp = night._epoch_impression(SNIPS[-1:])
check("plain prose passes through", imp == "I walked to the shore. The tide was out and the stones were warm.")
long = ["Alpha beta gamma delta. " * 3] * 3
imp = night._epoch_impression(long)
check("over the cap: cut on a sentence boundary", len(imp) <= 300 and imp.endswith("delta."))
check("ids stripped", "frag_" not in night._epoch_impression(["It was frag_ab12 and 3f2a9c1e-1234-4abc-9def-0123456789ab here ok."]))

print("[3] fallbacks")
check("empty -> plain fallback", night._epoch_impression([]) == "a stretch of ordinary hours")
check("bracket-only -> plain fallback", night._epoch_impression(["[From 'X'] ", "[]", None]) == "a stretch of ordinary hours")

print("[4] epoch() end to end, sandboxed")
with lab_env.isolate(db="empty") as lab_dir:
    from core.memory import store
    assert Path(store.DB_PATH).resolve().is_relative_to(Path(lab_dir).resolve()), store.DB_PATH   # never the live file
    mood._current_felt = raw
    store.store_fragment("a thing happened in the night window for the epoch test")
    eid = night.epoch(time.time() - 3600, SNIPS[:3])
    check("epoch() returned an id", bool(eid))
    if eid:
        with store._connect() as c:
            r = c.execute("SELECT mood, impression FROM memory_epochs WHERE epoch_id=?", (eid,)).fetchone()
        check("stored mood is the label", r[0] == "unsettled")
        check(f"stored impression clean: {r[1]!r}", not BAD.search(r[1]) and r[1][-1] in ".!?")
        got = store.retrieve_epoch("unsettled study", top_k=5)
        check("retrieve_epoch path unchanged: callable and returns a list", isinstance(got, list))
print("ALL PASS" if ok_all else "FAILED")
sys.exit(0 if ok_all else 1)

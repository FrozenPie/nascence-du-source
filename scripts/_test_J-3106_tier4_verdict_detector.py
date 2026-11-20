"""J-3106 / F-3826: Tier-4 correction/confirmation detector matches only a short message that OPENS with a cue.
Pure functions; no stores touched. Run from the worktree."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env)
from core.competence import CompetenceTracker as CT, _CORRECTION_CUES, _CONFIRMATION_CUES  # noqa: E402
import core.competence as comp  # noqa: E402
assert Path(comp.__file__).resolve().is_relative_to(ROOT), comp.__file__

fails = []
def check(ok, label):
    print(("PASS " if ok else "FAIL ") + label)
    if not ok:
        fails.append(label)

pad = " the grid analogy is useful and I want to think about it with you for a while." * 8

# the four quoted false positives (padded to the real message shape where the original was long)
fp_corr = [
    "Even though we may not inhabit the same universe (hell, we may actually, i don't know) we do inhabit this one." + pad,
    "You are not asking too much. (and no, you didn't break anything" + pad,
    "Are we examining it at a higher resolution?  no. we have changed the granularity" + pad,
]
for m in fp_corr:
    check(CT._is_correction(m) is False, f"long friendly msg not a correction ({len(m)} chars)")
# the same mid-sentence cues in a SHORT message are not an opening cue either
check(CT._is_correction("we may actually, i don't know") is False, "short mid-sentence 'actually,' not a correction")
check(CT._is_correction("(and no, you didn't break anything") is False, "mid-sentence 'no,' reassurance not a correction")
check(CT._is_confirmation("it is precisely because the illusion holds") is False, "mid-sentence 'precisely' not a confirmation")
check(CT._is_confirmation("It is precisely because the illusion holds." + pad) is False, "long 'precisely' not a confirmation")
# long messages never classify, even when they open with a cue
check(CT._is_correction("No, that's wrong. " + pad) is False and CT._is_confirmation("That's right. " + pad) is False,
      "long message opening with a cue stays unclassified")

true_corr = ["No, that's wrong.", "That's not what I said.", "no.", "Actually, it was Boswell.", "Du, no - I meant the other one.",
             "That's wrong. It was 1791.", "Hmm. Not quite.", "You misunderstood me.", "I disagree.", "Incorrect.",
             "Yes, but no, that's not it."]
for m in true_corr:
    check(CT._is_correction(m) is True, f"true correction: {m!r}")
true_conf = ["That's right.", "Exactly right.", "Yes exactly, that's the point.", "Correct.", "Precisely.",
             "Spot on. Now the next part.", "You're right, I mixed that up."]
for m in true_conf:
    check(CT._is_confirmation(m) is True, f"true confirmation: {m!r}")
check(CT._is_confirmation("Correct me if I am wrong, but is it 1791?") is False, "'Correct me' is a request, not a confirmation")
check(CT._is_confirmation("Correctly speaking, it is 1791.") is False, "'correctly' is not 'correct'")
check(CT._is_correction("") is False and CT._is_confirmation("") is False and CT._is_correction(None) is False, "empty / None safe")
# cue lists untouched
check("no," in _CORRECTION_CUES and "precisely" in _CONFIRMATION_CUES, "cue lists unchanged")
# wager_curiosity now routes through the same matcher
import core.wager_curiosity as wc  # noqa: E402
check(wc._is_correction("human", "No, that's wrong, it was Boswell") is True, "wager_curiosity: short correction still seen")
check(wc._is_correction("human", fp_corr[1]) is False, "wager_curiosity: long friendly msg no longer a correction")
check(wc._is_correction("internal", "No, that's wrong") is False, "wager_curiosity: non-human never a correction")

print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)

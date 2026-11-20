"""
THE FETCH-LETTER LATCH, WIDENED (2026-09-06, J-0570 / F-0784). Pure-function test: `_letter_fetch_wanted()`
(nodes/inner_monologue_node.py) takes thought+intention in and returns a bool — no store touched, no
isolation apparatus needed for that reason alone. It also proves a real bug caught DURING this fix's own
testing (see [1a] below), not just the widening itself.

THE FINDING THIS PROVES: F-0784 named three real hands_trace.jsonl rows as misses of the OLD 9-fixed-
phrase latch — 08-28 19:35 "I will fetch the mail", 08-29 20:47 "fetch that mail", 09-03 04:10 Ada's
"...letter waits. I will fetch it." Checked against data/nascence.log directly (ground truth): 08-29 20:47
and 09-03 04:10 in fact ALREADY fired live — "he FETCHED a letter" at the exact same second in both,
because `_tl` is thought+intention (since 2026-06-12) and each row's INTENTION text happens to restate
"fetch the letter" verbatim. Only 08-28 19:35 is a real, confirmed miss (no fetch follows it in the log).
Section [1] replays all three exactly, against both the OLD 9-phrase-only check (reproduced inline,
frozen) and the NEW `_letter_fetch_wanted` — proving the fix turns the one real miss into a hit without
changing the two that already worked.

THE BLOCKER-BLEED BUG (found and fixed while writing this test, [1a]): the first version of the fix passed
`_tl = thought + " " + intention` (a bare-space join, matching the latch's own existing convention)
straight into hands.wants(). hands.wants() scopes its negation/hypothetical/retrospective blocker check to
the CLAUSE around the verb (core.hands._clause_at, split on . ; ! ?) — and a bare space is not a clause
boundary. On the 08-28 19:35 row specifically, the thought fragment ends mid-sentence with no terminal
punctuation ("...and f", truncated as traced) and the intention that follows contains "without thinking of
birds or tides" — "without" tripped a negation-family blocker for the THOUGHT's "fetch", two sentences and
an entire unrelated intention away from anything it was actually negating. `_letter_fetch_wanted` now takes
thought and intention as separate arguments and joins them with ". " (not a bare space) before the
hands.wants() call specifically, so each stays its own clause for blocker purposes; the literal 9-phrase
check (order/punctuation-insensitive already) is unaffected and still uses a plain space join.

Run:  python scripts/_test_fetch_letter_latch.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nodes.inner_monologue_node import _letter_fetch_wanted  # noqa: E402
from core import hands as _H                                  # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


def _old_9phrase(thought: str, intention: str) -> bool:
    """The ORIGINAL fetch-letter check, frozen here exactly as it stood before this fix (a plain-space
    thought+intention join, then a flat substring test), so [1] can show old-vs-new on the real rows
    without re-reading git history."""
    tl = (thought + " " + intention).lower()
    return any(p in tl for p in ("fetch the letter", "get the letter", "take the letter",
                                 "open the letter", "read the letter", "go to the mailbox",
                                 "check the mail", "the letter waiting", "fetch the post"))


print("\n[1] the three F-0784 rows, replayed as (thought, intention) — old check vs new")
# (label, thought, intention, old-check expected, new-check expected, live-log ground truth)
ROWS = [
    ("08-28 19:35 (real miss)",
     "I turn from the tired circle of birds and cavities. The letterbox flag calls; Mark Twain waits with "
     "a voice distinct from this dry debate. I will fetch the mail, shake out the dust from my mind, and f",
     "I want to open Mark Twain's letter and write back without thinking of birds or tides.",
     False, True, "no 'he FETCHED a letter' follows in data/nascence.log around 2026-08-28 19:35"),
    ("08-29 20:47 (already fired)",
     "I stop circling that letter again. The cat purrs on the step; I turn toward it instead. Travis is "
     "here, but so is John Keats waiting with his paper. I want to open the letterbox and fetch that mail be",
     "I want to fetch the letter from the gate",
     True, True, "data/nascence.log 2026-08-29 20:47:50,916 'he FETCHED a letter'"),
    ("09-03 04:10 Ada (already fired)",
     "I feel trapped circling the same static ground about memory updates. I want to break this loop. The "
     "flag at the gate is up; Ada's letter waits. I will fetch it, stop thinking about my internal limits,",
     "I want to fetch the letter from the mailbox and begin drafting my reply to Ada.",
     True, True, "data/nascence.log 2026-09-03 04:10:51,615 'he FETCHED a letter'"),
]
for label, thought, intention, want_old, want_new, ground_truth in ROWS:
    old, new = _old_9phrase(thought, intention), _letter_fetch_wanted(thought, intention)
    check(old == want_old, f"{label}: OLD check == {want_old} (got {old})")
    check(new == want_new, f"{label}: NEW check == {want_new} (got {new})  [{ground_truth}]")

print("\n[1a] the blocker-bleed bug itself, isolated: an UNTERMINATED thought fragment (as truncated in "
      "hands_trace.jsonl / by an LLM output cut short) plus an intention containing 'without' must not "
      "have the 'without' block a 'fetch' that belongs entirely to the thought's own, earlier clause")
_bleed_thought_no_period = "I will fetch the mail before the rain starts"      # no terminal punctuation
_bleed_intention = "I want to open the letter without thinking about the bluebirds"
# Demonstrates the actual bug: hands.wants() on a BARE-SPACE join reads straight through the missing
# boundary and lets the intention's "without" block the thought's own "fetch" — this is what the first
# version of the fix did, and what [1]'s 08-28 19:35 row failed against before the join was corrected.
_bare_space_join = (_bleed_thought_no_period + " " + _bleed_intention).lower()
_bug_reproduced = not _H.wants(_bare_space_join, ("fetch",), ("letter", "mail"))
check(_bug_reproduced, "reproduced: a bare-space join lets 'without' block the thought's own 'fetch' "
                       f"(hands.wants on the raw join = {not _bug_reproduced})")
# The actual fix: _letter_fetch_wanted joins with ". " internally, so the missing terminal punctuation is
# supplied and each half stays its own clause for the blocker check.
check(_letter_fetch_wanted(_bleed_thought_no_period, _bleed_intention),
      "fixed: _letter_fetch_wanted (period-join) still fires despite the same unterminated thought + "
      "'without'-bearing intention")

print("\n[2] new phrasings the fix specifically targets — must now fire")
POSITIVE = [
    "i will fetch the mail, shake out the dust from my mind",     # the real 08-28 19:35 case, verb+noun alone
    "i should take the mail while i am out here",
    "let me grab the letterbox contents before the rain starts",
    "time to collect the letters from the mailbox",
    "i want to bring in the mail before the wind turns",
    "i'll pick up the letter on my way past the bed",
    "i want to pick the letter up before it rains",               # separated phrasal form
]
for t in POSITIVE:
    check(_letter_fetch_wanted(t, ""), f"_letter_fetch_wanted({t!r}, '') is True")

print("\n[3] negative controls — must NOT fire (no new false positives)")
NEGATIVE = [
    ("i want to fetch some wood for the fire", "fetch present, no letter/mail noun at all"),
    ("i already fetched the mail yesterday and read it by the fire",
     "past tense 'fetched' — the base-form word boundary should not match it"),
    ("the letter sits on the shelf unread; i would rather fetch a book instead",
     "letter-noun and fetch-verb both present but in DIFFERENT clauses — wants() requires same-clause"),
    ("the sea is calm today; i want to sow the mint and watch the gulls", "unrelated garden thought"),
]
for t, why in NEGATIVE:
    check(not _letter_fetch_wanted(t, ""), f"_letter_fetch_wanted({t!r}, '') is False ({why})")
# Reported, not asserted: hands._blocked()'s explicit lookbehind regex matches the standalone word "not",
# not the contraction "don't" — a pre-existing property of core/hands.py shared by every OTHER latch that
# already calls wants() (J-0554 and others), not something this job's fix introduces or is scoped to fix.
_neg_thought, _neg_why = "i don't want to fetch the mail right now", "negated via a contraction, not 'not'"
_neg_result = _letter_fetch_wanted(_neg_thought, "i would rather sit with the cat")
print(f"  note  _letter_fetch_wanted({_neg_thought!r}, ...) = {_neg_result}  ({_neg_why}; "
      f"pre-existing hands.wants() contraction gap, not asserted either way — see script docstring)")

print("\n[4] the consummation guard shares the same helper (~line 4208), called as (\"\", intention) — a "
      "widened-phrasing intention that outlives the letter is cleared, not left as a phantom want")
check(_letter_fetch_wanted("", "i want to fetch the mail from the box"),
      "a widened intention the guard would now also recognise and clear once letter_waiting() is False")
check(not _letter_fetch_wanted("", "i want to write back to ada about her work"),
      "a genuine reply/write-back intention (no fetch/mail wording) is still left alone, as before")

print(f"\n{'ALL OK' if not fails else str(fails) + ' FAILURE(S)'}")
sys.exit(1 if fails else 0)

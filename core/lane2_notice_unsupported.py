"""D-0417 (b)->(a) (travis 2026-10-15, J-2102) -- Lane 2's UNSUPPORTED-CLAIM check (the invention class).

A deterministic whitelist check that sits beside `notice_checked` (core/lane2_notice_check.py, the VALUE
checker) and never inside it: D-0342 kept invention out of the value checker on purpose, because a value
checker compares a band word or a number with the band or number the percepts list, while an invention is a
thing the notice names that the percepts never listed at all. F-2732 (J-1904) found the class keeps appearing
in live notices: "I hear a soft knock at the door." (19 of 19 knock mentions unsupported, the identical
sentence on 7 ticks), "a cat sitting by the threshold" (6 of 27 cat mentions), "the faint outline of a shadow
on the wall" (5 of 5), a clock tick with no sounds line, one voice; 31 of 1,006 rows (3.1 percent).

WHAT IT DOES. The notice is searched for a CLOSED set of invention-prone nouns (the ruling's seven -- cat,
figure, knock, shadow, footstep, voice, person -- plus the two the F-2732 keyword pass also counted, clock
and fire). Each named noun is then looked for in the tick's own percept text, in the lines that can actually
license it: the sounds/smells token lists, the `fire` line, the `cat at` line, the `clock` line, and any
people/visitor line a future payload may carry. A named noun with no licensing line is UNSUPPORTED.

    notice_unsupported = {"flag": bool, "nouns": [unsupported canon nouns],
                          "supported_by": {canon: "line: value"}, "negated": [canon], "v": VERSION}

A mention inside a short negation ("no cat", "I don't hear any footsteps", "without a voice") is recorded
under `negated` and does not flag: saying a thing is absent is not inventing it.

SCOREBOARD ONLY (plan 2.9, D-0417): nothing acts on it, LANE2_LIVE is untouched, no LLM, no I/O, no clock,
no randomness. Pure functions; fail-open at the call site (core/lane2.py `_notice_unsupported`).
Restart-gated like every other core/lane2.py change on this plan.
"""
from __future__ import annotations

import re

VERSION = 1

# canon noun -> surface-form regex (whole words, case-insensitive). CLOSED set by design (D-0417); add a
# noun here only through a finding that counted it, never by guessing.
INVENTION_NOUNS = {
    "cat": r"cats?|kittens?|kitty",
    "figure": r"figures?",
    "knock": r"knocks?|knocking|knocked",
    "shadow": r"shadows?|shadowy",
    "footstep": r"footsteps?|footfalls?",
    "voice": r"voices?",
    "person": r"person|persons|people|someone|somebody|stranger|strangers|visitor|visitors",
    # F-2732's keyword pass also counted these two (clock 2 of 128 unsupported, fire 1 of 119):
    "clock": r"clocks?",
    "fire": r"fires?|flames?|blaze",
}
_NOUN_RES = {c: re.compile(r"\b(?:" + p + r")\b", re.I) for c, p in INVENTION_NOUNS.items()}

# canon noun -> (percept line keys whose mere presence licenses it, substrings a sounds/smells token must
# contain to license it). Line keys are matched as percept_lines() renders them (underscore -> space).
# `figure` and `person` are licensed only by a people-type line (none exists in today's payload) or a
# heard voice token; footsteps are NOT taken as a person (they are Du's own steps on this shore).
_PEOPLE_KEYS = ("people", "people present", "person", "persons", "visitor", "visitors", "company")
SUPPORT = {
    "cat": (("cat at", "cat"), ("cat",)),
    "figure": (_PEOPLE_KEYS, ("voice",)),
    "knock": ((), ("knock",)),
    "shadow": ((), ("shadow",)),
    "footstep": ((), ("footstep", "footfall")),
    "voice": (_PEOPLE_KEYS, ("voice", "speech", "talk")),
    "person": (_PEOPLE_KEYS, ("voice", "speech", "talk")),
    "clock": (("clock",), ("clock",)),
    "fire": (("fire",), ("fire",)),
}
_TOKEN_KEYS = ("sounds", "smells")

# a negation within the few words before the noun, in the same clause (no comma/period/semicolon between)
_NEG_RE = re.compile(r"\b(?:no|not|never|without|nothing|nor|none|isn't|aren't|wasn't|don't|doesn't|didn't|"
                     r"can't|cannot|couldn't|absent|absence)\b|n't\b", re.I)
_NEG_WINDOW_WORDS = 6        # 6 so "I don't see any fire or flame" negates the flame too


def parse_listed(percept_text: str) -> dict:
    """{line key: value string} for every '- key: value' line, plus '_tokens': [(key, token)] for the
    comma-separated sounds/smells lists. Accepts exactly what core/lane2.percept_lines() renders."""
    lines, tokens = {}, []
    for raw in str(percept_text or "").splitlines():
        m = re.match(r"\s*-\s*([^:]+):\s*(.*)$", raw)
        if not m:
            continue
        key, val = m.group(1).strip().lower(), m.group(2).strip()
        lines[key] = val
        if key in _TOKEN_KEYS:
            tokens.extend((key, t.strip().lower()) for t in val.split(",") if t.strip())
    lines["_tokens"] = tokens
    return lines


def _support_for(canon: str, listed: dict) -> str | None:
    keys, subs = SUPPORT[canon]
    for k in keys:
        if k in listed and listed[k] not in ("", "none", "None", "[]"):
            return f"{k}: {listed[k]}"[:80]
    for key, tok in listed.get("_tokens") or []:
        if any(s in tok for s in subs):
            return f"{key}: {tok}"[:80]
    return None


# a negation straight after the noun: "the cat is not here", "the knock isn't real", "no voice was heard" is
# caught by the window before; this catches the copula form after it.
_POST_NEG_RE = re.compile(r"^\s*(?:(?:is|are|was|were)\s+(?:not|nowhere|absent|gone)\b|(?:isn't|aren't|wasn't|weren't)\b)",
                          re.I)


def _negated(text: str, start: int, end: int | None = None) -> bool:
    before = re.split(r"[.,;:!?]", text[:start])[-1]
    words = before.split()[-_NEG_WINDOW_WORDS:]
    if _NEG_RE.search(" ".join(words)):
        return True
    return end is not None and bool(_POST_NEG_RE.match(text[end:]))


def check_unsupported(notice: str, percept_text: str) -> dict:
    """The per-tick verdict. Empty notice or empty percept text -> flag False with how='not_checked'."""
    notice = str(notice or "").replace("’", "'")    # curly apostrophe -> straight, for the negations
    if not notice.strip() or not str(percept_text or "").strip():
        return {"flag": False, "nouns": [], "supported_by": {}, "negated": [], "how": "not_checked", "v": VERSION}
    listed = parse_listed(percept_text)
    unsupported, supported_by, negated = [], {}, []
    for canon, rx in _NOUN_RES.items():
        hits = list(rx.finditer(notice))
        if not hits:
            continue
        sup = _support_for(canon, listed)
        if sup is not None:
            supported_by[canon] = sup
            continue
        affirmed = [m for m in hits if not _negated(notice, m.start(), m.end())]
        if affirmed:
            unsupported.append(canon)
        else:
            negated.append(canon)
    return {"flag": bool(unsupported), "nouns": unsupported, "supported_by": supported_by,
            "negated": negated, "how": "deterministic", "v": VERSION}

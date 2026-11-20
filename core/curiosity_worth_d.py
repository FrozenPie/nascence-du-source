"""
Nascence -- deterministic curiosity worth check (d). J-3473, D-0683, F-4054.  SHADOW ONLY: nothing here gates anything.

D-0683 (Travis, 2026-11-06) retired the LLM worth-judge in favour of a deterministic redundancy-and-specificity
check. The J-3253 lab showed the 3B judge and the same prompt on bigger models cannot tell a question worth pursuing
from a metaphor or a mash-up, and that its own cheap probes (best: 1 - max Jaccard to the agenda) scored 0.80 on the
main set but 0.50 on a fresh hold-out. This module is the design that replaces those probes. It is a pure function of
the question text, an optional list of earlier questions (the redundancy corpus) and nothing else: no model, no store
read, no clock. Same input, same score.

THE SCORE (0..1, higher = more worth pursuing). Two halves, each fixed by reasoning about what the labelled "bad"
questions have in common (a generic frame about an unnamed referent, repeated templates, abstraction words), not by
fitting weights:
  specificity  = named particulars (capitalised non-initial words, numbers, quoted terms) minus abstraction words
                 minus relation-verb frames ("how does X reflect/shape/influence Y") minus generic-referent openers
                 ("the author", "the protagonist", "this period").
  redundancy   = how many EARLIER frontier questions share the same content tokens (template repetition: the five
                 'Napoleon's understanding of human psychology ...' variants), plus the lab's own agenda overlap.
Weights are integers fixed in WEIGHTS below. They were set before any held-out question was scored (see the J-3473
report); changing them after a hold-out read voids the validation.
"""
from __future__ import annotations
import re

DESIGN_VERSION = "d2"

_STOP = frozenset("""a an the of in on at to for from by with and or but is are was were be been being do does did how what why
which who whom whose when where that this these those it its their his her they he she as into than then so such can could
would should may might will shall has have had not no yes about over under between among through during after before""".split())

# abstraction words: a question made of these asks about no particular thing (chosen a priori, generic English, not fitted)
_ABSTRACT = frozenset("""theme themes concept concepts psychology psychological sociological implication implications narrative
essence journey transformation perspective identity relationship relationships tone imagery symbolism significance
emotional cultural personal growth turmoil portrayal dynamics notion idea ideas nature meaning understanding
complex role roles factors factor aspects aspect elements element impact influence influences contribute contributes
contributed shape shapes shaped reflect reflects reveal reveals relate relates connect connects context
development integration adaptation consciousness duality void chaos balance harmony""".split())

_REL = re.compile(r"\b(reflect|reveal|shape|influence|impact|contribut|relate|rewrite|transform|alter|play|portray)\w*", re.I)
_GENERIC_REF = re.compile(r"\b(the (author|narrator|protagonist|story|text|passage|poem|novel|character|characters|entity|"
                          r"period|era|setting|event|events|experiences)|this (period|time|story|text|passage)|his|her|their)\b", re.I)
_NAMED = re.compile(r"\b[A-Z][a-z]{2,}\b")
_DIGIT = re.compile(r"\d")
_QUOTED = re.compile(r"'[^']{3,}'|\"[^\"]{3,}\"|‘[^’]{3,}’|“[^”]{3,}”")

# DESIGN ON THE MAIN SET ONLY (docs/lab/J-3253_data/labelled.json). Per-feature main-set AUC (good vs bad): abstract 0.75,
# rel 0.66, named 0.66, digit 0.56, agenda 0.51, redundancy 0.50 (all-history count) / 0.57-0.61 (best window variants),
# quoted 0.47, generic_ref 0.47. Rule fixed before the hold-outs: a feature scores only if its main-set AUC is >= 0.60 and
# its sign was argued a priori. Redundancy and agenda overlap are therefore COMPUTED AND LOGGED (weight 0) so the shadow
# log can show whether they ever matter, but they do not move the score: on this evidence token-overlap redundancy does
# not separate good from bad (the good 'cliff swallows' and 'Napoleon' questions repeat as much as the bad ones).
# d2 (after the first hold-out read, see the J-3473 report): a "thin" term, a question with <= 3 content tokens and no
# named particular says too little to be pursued ('hello', 'what is 2+2', 'What is a book?'). Motivated by the
# pre-registered CONTROLS (main set), not by fitting the hold-out; disclosed because holdout.json had already been read
# once (AUC 0.751) when it was added, so holdout.json is NOT a clean validation of d2: the fresh set is.
WEIGHTS = {"named": 1.0, "abstract": -1.0, "rel": -0.75, "thin": -2.0}
LOGGED_ONLY = ("digit", "quoted", "generic_ref", "redundancy", "agenda")
_NAMED_CAP = 3


def toks(q: str) -> frozenset:
    """Content tokens: lowercase words, stopwords out, trailing possessive 's stripped."""
    out = set()
    for w in re.findall(r"[\w']+", (q or "").lower()):
        w = w[:-2] if w.endswith("'s") else w
        if w and w not in _STOP and len(w) > 1:
            out.add(w)
    return frozenset(out)


def jaccard(a: frozenset, b: frozenset) -> float:
    return len(a & b) / max(1, len(a | b))


def named_count(q: str) -> int:
    ws = _NAMED.findall(q or "")
    if ws and (q or "").strip().startswith(ws[0]):
        ws = ws[1:]                                   # the sentence-initial capital is not a name
    return len(ws)


def features(q: str, prior: list | None = None, agenda: list | None = None) -> dict:
    """Raw feature values. `prior` = earlier questions from the frontier (the redundancy corpus), `agenda` = the few
    most recent offered. Both default to empty (a question with nothing to repeat is not redundant)."""
    t = toks(q)
    words = [w for w in re.findall(r"[\w']+", (q or "").lower())]
    abstract = sum(1 for w in words if w in _ABSTRACT)
    dup = 0
    for p in (prior or []):
        pt = p if isinstance(p, frozenset) else toks(p)
        if t and jaccard(t, pt) >= 0.4:
            dup += 1
    ag = 0.0
    for p in (agenda or []):
        pt = p if isinstance(p, frozenset) else toks(p)
        ag = max(ag, jaccard(t, pt))
    return {"named": min(named_count(q), _NAMED_CAP), "digit": 1 if _DIGIT.search(q or "") else 0,
            "quoted": 1 if _QUOTED.search(q or "") else 0, "abstract": min(abstract, 4),
            "rel": 1 if _REL.search(q or "") else 0,
            "thin": 1 if (len(t) <= 3 and named_count(q) == 0) else 0, "generic_ref": 1 if _GENERIC_REF.search(q or "") else 0,
            "redundancy": min(dup, 3), "agenda": round(ag, 3)}


def raw_score(feat: dict) -> float:
    return sum(WEIGHTS[k] * float(feat.get(k, 0)) for k in WEIGHTS)


def score(q: str, prior: list | None = None, agenda: list | None = None) -> float:
    """0..1, higher = more worth pursuing. Monotone in raw_score; a plain logistic squash so the number is bounded
    and comparable across questions. Only the ORDER matters for AUC."""
    import math
    return round(1.0 / (1.0 + math.exp(-raw_score(features(q, prior, agenda)) / 2.0)), 4)

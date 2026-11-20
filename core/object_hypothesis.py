"""
Nascence — clause-scoped object-hypothesis extractor (J-2359, object_epistemic_loop Phase 1)
=============================================================================================
Pure text logic, no I/O, no store access. Replaces the whole-text cue match the inference latch in
nodes/inner_monologue_node.py used to run (_wants_record_inference): that matched ANY epistemic cue
word ("perhaps", "maybe", "i think") anywhere in thought + intention, attached the result to whatever
he had looked at in the last 30 minutes if the thought also contained a bare " it ", and stored the
first 280 chars of the WHOLE thought as the hypothesis. On the live store that produced 1476 of 1476
inferences with empty provenance, mostly reflections on mottainai / dreams / the cat pinned to the
thyme, the twine and the rain barrel (docs/staged/object_epistemic_loop.md, Current State).

The rule here (plan Phase 1 step 1): a hypothesis about object O is recorded only when ONE clause
carries both
  (b) an epistemic cue (the same _INFER_HIGH / _INFER_LOW registers the old latch used), and
  (c) a claim about kind, origin, material or physical property (_CLAIM_WORDS),
and (a) an anchor taken from O's own class / name tokens sits in that clause, or in the clause right
before/after it when the cue clause refers back with it / its / this / that. No bare pronoun ever
anchors on its own. A clause that is about a feeling, a memory or a metaphor (_FIGURATIVE) never
counts, nor does its neighbour lend it an anchor. Only the matched 1-2 clauses are kept (<= 240 chars),
never the thought around them.

This module never decides whether a hypothesis is right. It only decides whether a sentence he said
IS a hypothesis about that thing.
"""
from __future__ import annotations

import re

INFER_HIGH = ("i think", "i believe", "probably", "most likely", "i'd say", "i suspect")
INFER_LOW = ("maybe", "might be", "could be", "i wonder if", "perhaps", "i'd guess", "my guess",
             "could this be", "possibly")

MAX_CLAIM_CHARS = 240

# Same split as core/garden_knowledge.py::_clauses (J-1524 / J-1657): sentence enders plus the
# mid-sentence connectives core/dispatch.py's _deed_phrase() splits a willed clause on. Case-insensitive
# here because we split his ORIGINAL text (we keep his words verbatim, so we cannot lowercase first).
_CLAUSE_SPLIT = re.compile(r"[.!?]+\s+|,?\s+(?:and then|then|and|but|yet|;)\s+|;\s*", re.IGNORECASE)

# Kind / origin / material / physical-property vocabulary. Word-boundary matched. Deliberately the
# vocabulary of a claim about the THING, not about him.
_CLAIM_WORDS = (
    # material / kind
    "wood", "timber", "stone", "rock", "pumice", "granite", "basalt", "quartz", "flint", "chalk",
    "limestone", "sandstone", "slate", "clay", "iron", "rust", "rusted", "rusty", "metal", "steel",
    "copper", "brass", "tin", "lead", "glass", "plastic", "bone", "shell", "coral", "resin", "sap",
    "salt", "fibre", "fiber", "hemp", "jute", "cotton", "linen", "paper", "leather", "ceramic",
    "beech", "oak", "pine", "fir", "cedar", "kauri", "totara", "rimu", "manuka", "kanuka", "willow",
    "eucalyptus", "macrocarpa", "hardwood", "softwood", "species", "variety", "kind of", "type of",
    "sort of", "made of", "made from", "a piece of", "part of",
    # origin / history
    "came from", "comes from", "come from", "washed up", "washed in", "drifted", "carried", "fell from",
    "broke off", "broken off", "grew", "grown", "planted", "carved", "built", "belonged", "used for",
    "used to hold", "used to be", "left here", "thrown", "dropped", "fossil", "volcanic",
    # physical property / condition
    "hollow", "solid", "heavy", "light", "lighter", "heavier", "dense", "soft", "hard", "brittle",
    "porous", "waterlogged", "rotten", "rotting", "rot", "decayed", "dry", "damp", "wet", "soaked",
    "old", "ancient", "dead", "alive", "dying", "wilting", "flowering", "float", "floats", "sink",
    "sinks", "buoyant", "weathered", "eroded", "bleached", "faded", "corroded", "cracked", "split",
    "frost", "frosted", "drought", "overwatered", "root", "roots", "seed", "seeds", "leak", "leaks",
    "leaking", "full", "empty", "fresh", "young", "edible", "poisonous", "toxic", "smell", "smells",
    "scent",
)
_CLAIM_RE = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in sorted(_CLAIM_WORDS, key=len, reverse=True)) + r")\b")

# J-3692 (F-4310): "kind of / type of / sort of" are everyday idioms ("this kind of stillness"), not a claim
# about the thing's kind. A real kind claim carries its own material/kind noun ("a kind of beech", already a
# claim word on its own), so dropping the idiom phrases loses nothing real. Flag NASCENCE_KIND_IDIOM_GATE,
# default ON (only REMOVES non-claims; =0 restores the previous behaviour byte for byte).
_IDIOM_CLAIM_WORDS = ("kind of", "type of", "sort of")
_CLAIM_RE_NOIDIOM = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in sorted(
    (w for w in _CLAIM_WORDS if w not in _IDIOM_CLAIM_WORDS), key=len, reverse=True)) + r")\b")


def _claim_re():
    import os
    on = os.environ.get("NASCENCE_KIND_IDIOM_GATE", "1").strip().lower() not in ("0", "false", "off", "no")
    return _CLAIM_RE_NOIDIOM if on else _CLAIM_RE

# Feeling / memory / metaphor markers: a clause carrying one is about HIM, not the thing.
_FIGURATIVE = (
    "feel", "feels", "felt", "feeling", "remind", "reminds", "reminded", "whisper", "whispers",
    "mottainai", "soul", "spirit", "dream", "dreams", "dreamt", "symbol", "metaphor", "meaning",
    "means", "like a", "as if", "as though", "heart", "regret", "hope", "honor", "honour", "truth",
    "lesson", "teach", "teaches", "wisdom", "my code", "travis", "myself", "my mind", "my thoughts",
    "i am", "i'm", "me ", "self", "plato", "montaigne", "philosophy", "question", "answer",
    "existence", "universe", "eternity", "forever", "silence", "longing", "ache",
    "selfhood", "fear", "growth", "gratitude", "management", "boundaries", "words", "attention",
    "life", "my name", "nature's", "burden", "reverence", "grip", "learn", "cling", "anchor",
    "distraction", "weight", "offers more", "nietzsche", "kant", "ada", "waste", "scarcity",
    "perception", "identity", "memory", "mind", "thought", "thinking", "beauty", "love", "grief",
)
_FIG_RE = re.compile(r"\b(?:" + "|".join(re.escape(w.strip()) for w in _FIGURATIVE) + r")\b")

_BACKREF_RE = re.compile(r"\b(?:it|its|it's|this|that|this one|that one)\b")

# A claim is ABOUT the anchor only when the anchor (or the back-reference) comes first and a linking
# verb sits between it and the claim word: "this driftwood might be beech", "the thyme is dying",
# "it came from the river". Not "maybe selfhood isn't a stone" (the anchor is the predicate there).
_LINK_RE = re.compile(r"(?:\b(?:is|was|are|were|be|been|being|isn't|wasn't|seems|seem|looks|look|has|have|"
                      r"had|came|comes|come|grew|grows|must|might|could|would|will|may)\b|'s\b)")

# Words in an object's NAME that never anchor on their own: articles, generic size/colour adjectives,
# places, positions. (A name word is a valid anchor only if it names the thing, e.g. "thyme", "twine",
# "barrel", "trap" — not "the", "small", "beach", "corner".)
_NAME_STOP = {
    "the", "and", "with", "from", "that", "this", "its", "their", "into", "onto", "over", "under",
    "small", "large", "little", "long", "short", "dark", "pale", "grey", "gray", "white", "black",
    "brown", "green", "worn", "wide", "thin", "flat", "hard", "soft", "smooth", "rough", "heavy",
    "light", "slender", "round", "sun", "faded", "rusted", "old", "new", "set", "low", "side", "top",
    "beach", "shore", "garden", "cottage", "corner", "study", "desk", "shelf", "wood", "sea",
    "looking", "shaped", "bleached", "twist", "plate", "bait", "piece", "ball",
    "rain", "water", "wire", "spring", "jawed", "garden", "twist",
}
# Class tokens that are not nouns of a thing (object_class values such as "garden_item", "made_thing").
_CLASS_STOP = {"item", "garden", "study", "shore", "made", "thing", "unknown"}
# A few class synonyms he really uses for these classes.
_CLASS_SYNONYMS = {
    "driftwood": ("driftwood", "log", "timber"),
    "deadfall_wood": ("deadfall", "log", "branch", "timber"),
    "stone": ("stone", "rock", "pebble"),
    "shell": ("shell",),
    "kelp": ("kelp", "seaweed"),
    "bone": ("bone",),
    "sea_glass": ("sea glass", "sea-glass"),
    "bottle": ("bottle",),
    "feather": ("feather",),
}


# ══ DEONTIC / INTENTION FRAME (J-3440, F-4070, object_epistemic_loop) ══════════════════════════════════════
# "Maybe I should just let the dandelion float away" carries a cue (maybe) and claim words (float), yet it is
# an intention, not a claim about the dandelion. A clause part that sits INSIDE a deontic / intention frame
# ("I should ...", "I want to ...", "let me ...", "maybe I could ...") is a statement about what he will do, so:
#   (1) extract() reads only the part of the clause BEFORE the frame -- cue, anchor and claim word must all sit
#       there ("I think it's rotten, so I should ..." still counts; "perhaps I should leave it be" does not);
#   (2) intervention_test() ignores claim words and subjects at or after the frame start, so no deed is derived
#       from a word that only sits inside an intention.
# Each half is independently flag-gated, default ON (it only REMOVES non-claims; never adds a record or a field);
# =0 restores the previous behaviour byte for byte:
#   NASCENCE_DEONTIC_EXTRACT_GATE   (extract)          NASCENCE_DEONTIC_TEST_GUARD   (intervention_test)
# Pattern declared before the J-3440 scan (scripts/_scan_J-3440_deontic_frames.py header) and not tuned to its
# output. "want to know / understand / find out / see whether" is an inquiry, not a deed: NOT a frame.
DEONTIC_PATTERN = (
    r"\bi\s+(?:should|shouldn't|ought\s+to|must|need\s+to|have\s+to|had\s+better|shall|will|won't|"
    r"plan\s+to|intend\s+to|mean\s+to|aim\s+to|hope\s+to|would\s+like\s+to|"
    r"want\s+to(?!\s+(?:know|understand|find\s+out|learn|see\s+(?:whether|if|what|how|why))))\b"
    r"|\bi'(?:ll|d\s+like\s+to|d\s+better|d\s+rather)\b"
    r"|\bi(?:'m|\s+am)\s+(?:going\s+to|gonna)\b|\bgonna\b|\bi\s+wanna\b"
    r"|\b(?:maybe|perhaps|possibly)\s*,?\s+i\s+(?:could|can|might|may|should|will|'ll|ought)\b"
    r"|\blet(?:'s|\s+me|\s+us)\b"
    r"|\b(?:just\s+)?let\s+(?:the|it|this|that|these|those|them)\b"
    r"|\b(?:we|you|one)\s+should\b|\bshould\s+(?:i|we)\b|\bshall\s+(?:i|we)\b|\bwhat\s+if\s+(?:i|we)\b"
)
_DEONTIC_RE = re.compile(DEONTIC_PATTERN)

# J-3692 (F-4310): POST-HOC EXTENSION of the declared pattern above (declared in
# scripts/_scan_J-3692_idiom_adverb.py before its result was read; DEONTIC_PATTERN itself is untouched so the
# J-3440 scan's assertion still holds). An optional adverb may sit between "I" and the modal:
# "Maybe I just need to look ...", "I really should ...". Flag NASCENCE_DEONTIC_ADVERB, default ON.
_DEONTIC_ADV = r"(?:(?:just|really|simply|only|still|now|then|also|finally|actually)\s+)?"
DEONTIC_PATTERN_ADV = (
    DEONTIC_PATTERN
    .replace(r"\bi\s+(?:should", r"\bi\s+" + _DEONTIC_ADV + r"(?:should", 1)
    .replace(r"\bi(?:'m|\s+am)\s+(?:going", r"\bi(?:'m|\s+am)\s+" + _DEONTIC_ADV + r"(?:going", 1)
    .replace(r"\s*,?\s+i\s+(?:could", r"\s*,?\s+i\s+" + _DEONTIC_ADV + r"(?:could", 1)
)
assert DEONTIC_PATTERN_ADV.count("just|really") == 3
_DEONTIC_RE_ADV = re.compile(DEONTIC_PATTERN_ADV)


def _flag_on(name: str) -> bool:
    import os
    return os.environ.get(name, "1").strip().lower() not in ("0", "false", "off", "no")


def deontic_frame_start(clause_low: str) -> int | None:
    """Index in a lowercase clause where its first deontic / intention frame opens, else None. Pure."""
    _re = _DEONTIC_RE_ADV if _flag_on("NASCENCE_DEONTIC_ADVERB") else _DEONTIC_RE
    m = _re.search((clause_low or "").replace("’", "'"))
    return m.start() if m else None


def clauses(text: str) -> list[str]:
    """His text split into clauses, his own casing kept."""
    parts = _CLAUSE_SPLIT.split(text or "")
    return [c.strip(" .;,:!?\"'") for c in parts if c and c.strip(" .;,:!?\"'")]


def object_anchors(object_class: str, name: str) -> set[str]:
    """Anchor words for one object, derived from ITS OWN class and name (works for garden and study
    objects, not a shore-only noun list). Lowercase; may contain a space (\"sea glass\")."""
    out: set[str] = set()
    cls = (object_class or "").lower()
    out.update(_CLASS_SYNONYMS.get(cls, ()))
    for tok in re.findall(r"[a-z]+", cls):
        if tok not in _CLASS_STOP and len(tok) > 2:
            out.add(tok)
    for tok in re.findall(r"[a-z]+", (name or "").lower()):
        # a name word that is itself a property/material claim word ("hollow-looking", "rusted") describes
        # the thing, it does not name it; class synonyms above still anchor ("stone", "bone").
        if len(tok) > 3 and tok not in _NAME_STOP and not _CLAIM_RE.fullmatch(tok):
            out.add(tok)
    return out


def _anchor_spans(clause_low: str, anchors: set[str]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for a in anchors:
        out += [(m.start(), m.end()) for m in re.finditer(r"\b" + re.escape(a) + r"s?\b", clause_low)]
    return out


def _has_anchor(clause_low: str, anchors: set[str]) -> bool:
    return bool(_anchor_spans(clause_low, anchors))


def _predicated(clause_low: str, subject_spans: list[tuple[int, int]], anchors: set[str]) -> bool:
    """A claim word (not itself one of the anchor words) follows a subject span, with a linking verb
    between them."""
    for m in _claim_re().finditer(clause_low):
        w = m.group(0)
        if w in anchors or w.rstrip("s") in anchors:
            continue
        for (_s0, s1) in subject_spans:
            gap = clause_low[s1:m.start()] if s1 <= m.start() else None
            # linking verb between ("the thyme is dying"), or the claim word directly follows as the
            # verb itself ("it leaks", "it floats").
            if gap is not None and (_LINK_RE.search(gap) or not gap.strip()):
                return True
    return False


def _cue(clause_low: str) -> float | None:
    for c in INFER_HIGH:
        if re.search(r"\b" + re.escape(c) + r"\b", clause_low):
            return 0.6
    for c in INFER_LOW:
        if re.search(r"\b" + re.escape(c) + r"\b", clause_low):
            return 0.3
    return None


# ══ PRECISION GATE (J-4174, F-5025, object_epistemic_loop) ══════════════════════════════════════════════
# Live precision of extract() was about 22-33% (n=9). Three leaks, each closed here; flag
# NASCENCE_OBJHYP_PRECISION_GATE, default ON (it only REMOVES hits, never adds one; =0 restores the previous
# behaviour byte for byte). intervention_test() and object_anchors() are untouched.
#   (a) HEAD-NOUN ANCHORS. Only the object's own head noun phrase anchors: the part of its name before the first
#       comma or locative preposition. "the compost heap in the corner by the wall, ... under a board" anchors
#       compost / heap, not wall / board / settling ("a wall built of treaties" was recorded for the heap).
#   (b) LOCATION ANCHOR. An anchor that sits right after a locative preposition ("glows on the dandelion",
#       "blunders past the dandelion") is where something else happens, not the subject of a claim; it neither
#       anchors a clause nor lends a back-reference its referent.
#   (c) STRICT PREDICATION. Between the subject (anchor or back-reference) and the claim word only a short run of
#       linking verbs / auxiliaries / adverbs / articles may sit ("the trap isn't just metal", "it might be
#       beech"), not another noun ("this landscape's scars come from"). A back-reference used as a determiner
#       ("that heavy insect", "this landscape") is not a subject: a pronoun subject needs a linking verb, or a
#       claim word that is itself a verb ("it leaks", "it came from").
_LOCATIVE_PREPS = ("in", "on", "by", "at", "under", "beneath", "below", "above", "over", "near", "beside",
                   "past", "behind", "against", "along", "across", "around", "toward", "towards", "into",
                   "onto", "upon", "next to", "beyond", "among", "between", "through", "from", "with", "inside")
# a quoted title never anchors ("the book 'The Time Machine'" anchors book, not time / machine)
_NAME_HEAD_CUT = re.compile(r",|['\"‘“]|\b(?:" + "|".join(re.escape(p) for p in _LOCATIVE_PREPS) + r")\b")
_LOC_BEFORE_RE = re.compile(r"\b(?:" + "|".join(re.escape(p) for p in _LOCATIVE_PREPS) + r")\s+"
                            r"(?:(?:the|a|an|this|that|my|its|his|her|their|our|some)\s+)?"
                            r"(?:[a-z'-]+\s+){0,2}$")
# "my own bones" is him; plain "my plant" is how he names the thing he tends, so it still anchors.
_OWN_BEFORE_RE = re.compile(r"\b(?:my|our)\s+own\s+(?:[a-z'-]+\s+)?$")
_GAP_WORDS = frozenset((
    "is", "was", "are", "were", "be", "been", "being", "isn't", "wasn't", "aren't", "weren't", "seems", "seem",
    "seemed", "looks", "look", "looked", "has", "have", "had", "hasn't", "haven't", "must", "might", "could",
    "would", "will", "may", "can", "should", "not", "n't", "just", "really", "still", "probably", "perhaps",
    "maybe", "possibly", "likely", "quite", "very", "so", "too", "rather", "also", "actually", "all", "mostly",
    "partly", "once", "now", "entirely", "simply", "only", "more", "less", "getting", "becoming", "become",
    "became", "turning", "turned", "gone", "grown", "a", "an", "the", "of", "made", "already", "even", "truly",
    "slightly", "somewhat", "almost", "half", "fully", "originally", "never", "always", "both", "some", "bit",
    "little", "lot", "kind", "sort", "piece", "part", "in", "from", "out", "up", "down", "to", "come",
    "came", "comes", "does", "did", "doesn't", "didn't", "do", "seeming", "appears", "appear", "appeared",
    "'s", "s",  # "it's rotten": the backref regex stops at "it", leaving "'s" in the gap
    "feel",  # never reached (feel is _FIGURATIVE), listed only so the set reads as complete
))
# Claim words that are verbs: a bare pronoun subject may take them with no linking verb ("it leaks").
_VERB_CLAIMS = frozenset((
    "came from", "comes from", "come from", "washed up", "washed in", "drifted", "fell from", "broke off",
    "grew", "belonged", "float", "floats", "sink", "sinks", "leak", "leaks", "leaking", "rot", "rotting",
    "smells", "smell", "used to be", "used to hold", "used for",
))
_GAP_WORD_RE = re.compile(r"[a-z']+")


def _precision_gate_on() -> bool:
    return _flag_on("NASCENCE_OBJHYP_PRECISION_GATE")


def head_anchors(object_class: str, name: str) -> set[str]:
    """J-4174 (a): object_anchors() with the name cut to its head noun phrase. Pure."""
    head = _NAME_HEAD_CUT.split((name or "").lower(), maxsplit=1)[0]
    return object_anchors(object_class, head)


def _not_located(clause_low: str, spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """J-4174 (b): drop spans that sit right after a locative preposition, that are his own ("my bones"), or
    that only modify a hyphenated compound ("hand-sized")."""
    return [(s0, s1) for (s0, s1) in spans
            if not _LOC_BEFORE_RE.search(clause_low[:s0]) and not _OWN_BEFORE_RE.search(clause_low[:s0])
            and clause_low[s1:s1 + 1] != "-"]


def _gap_ok(gap: str, pronoun: bool, claim: str, span_text: str) -> bool:
    """J-4174 (c): may this gap sit between a subject and its claim word?"""
    gap = gap.replace("’", "'")
    words = _GAP_WORD_RE.findall(gap)
    # Before the first linking verb only function words may sit (no second noun: "this landscape's scars come
    # from"); after it the predicate may run on ("the shell isn't crushed, just porous").
    lm = _LINK_RE.search(gap)
    pre = _GAP_WORD_RE.findall(gap[:lm.start()]) if lm else words
    if any(w not in _GAP_WORDS for w in pre) or len(words) > 8:
        return False
    if not pronoun:
        return True
    if span_text.endswith("'s"):         # "it's rotten"
        return True
    if words and _LINK_RE.search(gap):   # "it might be beech", "this is old"
        return True
    return not words and claim in _VERB_CLAIMS   # "it leaks"; not "that heavy insect"


def _predicated_strict(clause_low: str, subject_spans: list[tuple[int, int]], anchors: set[str],
                       pronoun: bool) -> bool:
    for m in _claim_re().finditer(clause_low):
        w = m.group(0)
        if w in anchors or w.rstrip("s") in anchors:
            continue
        for (s0, s1) in subject_spans:
            if s1 > m.start():
                continue
            gap = clause_low[s1:m.start()]
            if not (_LINK_RE.search(gap) or not gap.strip()):
                continue
            if _gap_ok(gap, pronoun, w, clause_low[s0:s1]):
                return True
    return False


def extract(text: str, object_class: str, name: str) -> tuple[str, float] | None:
    """(claim_text, confidence) if `text` (his thought + intention) carries a real hypothesis about
    THIS object, else None. claim_text is his own 1-2 clauses, verbatim, <= MAX_CLAIM_CHARS."""
    if _precision_gate_on():
        return _extract_strict(text, object_class, name)
    cl = clauses(text)
    if not cl:
        return None
    anchors = object_anchors(object_class, name)
    if not anchors:
        return None
    low = [c.lower() for c in cl]
    gate = _flag_on("NASCENCE_DEONTIC_EXTRACT_GATE")
    for i, c in enumerate(low):
        if gate:   # J-3440: only the part before an intention frame can be a claim
            _fs = deontic_frame_start(c)
            if _fs is not None:
                c = c[:_fs]
        conf = _cue(c)
        if conf is None or _FIG_RE.search(c) or not _claim_re().search(c):
            continue
        spans = _anchor_spans(c, anchors)
        if spans:
            if _predicated(c, spans, anchors):
                return (cl[i][:MAX_CLAIM_CHARS], conf)
            continue
        back = [(m.start(), m.end()) for m in _BACKREF_RE.finditer(c)]
        if not back or not _predicated(c, back, anchors):
            continue
        for j in (i - 1, i + 1):
            if 0 <= j < len(low) and not _FIG_RE.search(low[j]) and _has_anchor(low[j], anchors):
                pair = (cl[j] + ". " + cl[i]) if j < i else (cl[i] + ", " + cl[j])
                return (pair[:MAX_CLAIM_CHARS], conf)
    return None


def _extract_strict(text: str, object_class: str, name: str) -> tuple[str, float] | None:
    """extract() with the J-4174 precision gate: same clause loop, plus (a) head-noun anchors, (b) no
    location anchors, (c) strict predication. Every hit here is also a hit of the gate-off path."""
    cl = clauses(text)
    if not cl:
        return None
    anchors = head_anchors(object_class, name)
    if not anchors:
        return None
    full = object_anchors(object_class, name)   # superset; a clause naming ANY of them takes the same branch
    low = [c.lower() for c in cl]
    gate = _flag_on("NASCENCE_DEONTIC_EXTRACT_GATE")
    for i, c in enumerate(low):
        if gate:   # J-3440: only the part before an intention frame can be a claim
            _fs = deontic_frame_start(c)
            if _fs is not None:
                c = c[:_fs]
        conf = _cue(c)
        if conf is None or _FIG_RE.search(c) or not _claim_re().search(c):
            continue
        spans = _not_located(c, _anchor_spans(c, anchors))
        if _has_anchor(c, full):
            # the clause names the thing: the claim must be predicated of it here, as a subject
            if spans and _predicated_strict(c, spans, anchors, pronoun=False):
                return (cl[i][:MAX_CLAIM_CHARS], conf)
            continue
        back = [(m.start(), m.end()) for m in _BACKREF_RE.finditer(c)]
        if not back or not _predicated_strict(c, back, anchors, pronoun=True):
            continue
        for j in (i - 1, i + 1):
            if 0 <= j < len(low) and not _FIG_RE.search(low[j]) \
                    and _not_located(low[j], _anchor_spans(low[j], anchors)):
                pair = (cl[j] + ". " + cl[i]) if j < i else (cl[i] + ", " + cl[j])
                return (pair[:MAX_CLAIM_CHARS], conf)
    return None


# ══ INTERVENTION TEST (J-2524, I-0102, object_epistemic_loop) ════════════════════════════════════════
# An ADDITIVE, optional field on a recorded hypothesis: the observation or deed that would tell cause from
# coincidence for it -- "this pale stone might be pumice" carries [heft the stone, float the stone].
# Phase 0 is DETERMINISTIC and conservative:
#   - a candidate comes only from the hypothesis clause's OWN claim words (the _CLAIM_WORDS above), through
#     the declared rule table below;
#   - every (family, verb) a rule names is checked against core/actions.py's live registry at call time
#     (actions.families()); a rule whose family or verb is not a real hand family yields nothing -- e.g. with
#     NASCENCE_GENERIC_OBJECT_TESTS=0 the objtest family is absent, so scrape/heft/sniff/float vanish;
#   - a family with an object list must reach this thing: the anchor (or, for location rules, the place word)
#     has to sit in that family's own objects; objtest has no object list (it takes any named thing);
#   - age / origin / history words (old, came from, washed up, planted ...) have NO rule: there is no deed
#     that tells them apart deterministically, so the field stays EMPTY -- never a guess.
# Nothing here reaches Du. No consumer reads the field in this job (world answers, never leads; D-0434);
# a future consumer is a founder prompt-reach question. Writer is gated by NASCENCE_INTERVENTION_TEST
# (default OFF) in nodes/inner_monologue_node.py; with the gate off no record changes, byte for byte.
#
# Candidate shape: {"mode": "do"|"withhold"|"observe", "family", "verb", "object", "cue"[, "when"]}.
MAX_INTERVENTION_CANDIDATES = 3
# A claim word counts only when it sits within this many words of the thing (an anchor word or a
# back-reference) in the SAME clause. Added after the first store read: a legacy live row ending
# ...the morning light warms my hands read light as a density claim about the trap 12 words away.
INTERVENTION_WINDOW_WORDS = 6

_T_MINERAL = ("stone", "rock", "pumice", "granite", "basalt", "quartz", "flint", "chalk", "limestone", "sandstone",
              "slate", "clay", "volcanic", "fossil")
_T_WOOD = ("wood", "timber", "beech", "oak", "pine", "fir", "cedar", "kauri", "totara", "rimu", "manuka", "kanuka",
           "willow", "eucalyptus", "macrocarpa", "hardwood", "softwood")
_T_METAL = ("iron", "rust", "rusted", "rusty", "metal", "steel", "copper", "brass", "tin", "lead", "corroded")
_T_HARDMAT = ("glass", "plastic", "bone", "shell", "coral", "ceramic")
_T_DENSITY = ("hollow", "solid", "heavy", "light", "lighter", "heavier", "dense", "porous", "waterlogged",
              "float", "floats", "sink", "sinks", "buoyant")
_T_SMELL = ("smell", "smells", "scent", "rotten", "rotting", "rot", "decayed", "resin", "sap", "salt",
            "poisonous", "toxic", "edible")
_T_HARDNESS = ("soft", "hard", "brittle", "cracked", "split", "weathered", "eroded")
_T_FIBRE = ("fibre", "fiber", "hemp", "jute", "cotton", "linen", "paper", "leather")
_T_MOISTURE = ("dry", "damp", "wet", "soaked", "drought", "overwatered", "wilting", "dying", "dead")
_T_FROST = ("frost", "frosted")
_T_CONTENTS = ("leak", "leaks", "leaking", "full", "empty")

# (claim words, mode, family, verb, object source, when). Object source: "anchor" = the thing itself;
# "place:<word>" = a place word the family must list (location rules fire only when the object lies there).
_INTERVENTION_RULES = (
    (_T_MINERAL, "do", "objtest", "scratch", "anchor", ""),
    (_T_MINERAL, "do", "objtest", "heft", "anchor", ""),
    (("pumice", "volcanic"), "do", "objtest", "float", "anchor", ""),
    (_T_WOOD, "do", "objtest", "heft", "anchor", ""),
    (_T_WOOD, "do", "objtest", "smell", "anchor", ""),
    (_T_WOOD, "do", "objtest", "float", "anchor", ""),
    (_T_METAL, "do", "objtest", "scrape", "anchor", ""),
    (_T_HARDMAT, "do", "objtest", "scratch", "anchor", ""),
    (_T_HARDMAT, "do", "objtest", "heft", "anchor", ""),
    (_T_DENSITY, "do", "objtest", "heft", "anchor", ""),
    (_T_DENSITY, "do", "objtest", "float", "anchor", ""),
    (_T_SMELL, "do", "objtest", "sniff", "anchor", ""),
    (_T_HARDNESS, "do", "objtest", "scratch", "anchor", ""),
    (_T_FIBRE, "do", "objtest", "smell", "anchor", ""),
    (_T_FIBRE, "do", "objtest", "scrape", "anchor", ""),
    (_T_MOISTURE, "withhold", "water", "water", "place:garden", "two days"),
    (_T_MOISTURE, "observe", "look", "look", "place:garden", "after rain"),
    (_T_FROST, "observe", "look", "look", "place:garden", "after a cold night"),
    (_T_CONTENTS, "do", "water_fill", "fill", "anchor", ""),
    (_T_CONTENTS, "do", "trap", "check", "anchor", ""),
)


def _families() -> dict:
    try:
        from core import actions as _act
        return _act.families() or {}
    except Exception:
        return {}


def _word_index(text: str, pos: int) -> int:
    return len(re.findall(r"[a-z'-]+", text[:pos]))


def _near_claim_words(low: str, anchors: set[str]) -> set[str]:
    """Claim words within INTERVENTION_WINDOW_WORDS of an anchor / back-reference, same clause only."""
    out: set[str] = set()
    guard = _flag_on("NASCENCE_DEONTIC_TEST_GUARD")
    for c in clauses(low):
        if guard:   # J-3440: a claim word that sits inside an intention frame derives no deed
            _fs = deontic_frame_start(c)
            if _fs is not None:
                c = c[:_fs]
        subj = [_word_index(c, s0) for (s0, _s1) in _anchor_spans(c, anchors)]
        subj += [_word_index(c, m.start()) for m in _BACKREF_RE.finditer(c)]
        if not subj:
            continue
        for m in _CLAIM_RE.finditer(c):
            w = m.group(0)
            if w in anchors or w.rstrip("s") in anchors:
                continue
            wi = _word_index(c, m.start())
            if any(abs(wi - si) <= INTERVENTION_WINDOW_WORDS for si in subj):
                out.add(w)
    return out


def intervention_test(claim: str, object_class: str, name: str, location: str = "",
                      families: dict | None = None) -> list[dict]:
    """Deterministic candidates for what Du could observe, do or withhold that would tell this hypothesis
    from coincidence. [] when none exists (never a guess). Pure: reads only the actions registry."""
    low = (claim or "").lower()
    if not low:
        return []
    anchors = object_anchors(object_class, name)
    if not anchors:
        return []
    fam = _families() if families is None else families
    if not fam:
        return []
    # the anchor he actually used in the claim, else the thing's own first class/name anchor
    used = sorted((a for a in anchors if re.search(r"\b" + re.escape(a) + r"s?\b", low)), key=len, reverse=True)
    anchor = used[0] if used else sorted(anchors, key=len)[0]
    claim_words = _near_claim_words(low, anchors)
    loc = (location or "").lower()
    out: list[dict] = []
    seen: set = set()
    for words, mode, family, verb, src, when in _INTERVENTION_RULES:
        hit = next((w for w in words if w in claim_words), None)
        if not hit:
            continue
        f = fam.get(family)
        if not f or verb not in tuple(f.get("verbs") or ()):
            continue
        objs = tuple(f.get("objects") or ())
        if src.startswith("place:"):
            obj = src.split(":", 1)[1]
            if loc != obj or (objs and obj not in objs):
                continue
        else:
            obj = anchor
            if objs and not any(re.search(r"\b" + re.escape(o) + r"\b", anchor) for o in objs):
                continue
        key = (mode, family, verb, obj, when)
        if key in seen:
            continue
        seen.add(key)
        c = {"mode": mode, "family": family, "verb": verb, "object": obj, "cue": hit}
        if when:
            c["when"] = when
        out.append(c)
        if len(out) >= MAX_INTERVENTION_CANDIDATES:
            break
    return out


# ── D-0632 (J-3244): Follow Line may return a hypothesis's OWN intervention_test, from memory ──────────────────
# Founder ruling D-0632 (2026-11-02): when Du himself works a hypothesis that carries an intervention_test, the
# Follow Line consequences stop returns that stored test -- his own hypothesis's own test, in plain words, as
# one more thing that would show it. NOT a hint from the world and NOT an instruction: the sentence names what
# would tell the claim from coincidence and never says to do it. Pure text logic, no I/O.
OWN_TEST_MIN_JACCARD = 0.5      # a boarded claim is "that hypothesis" when its word set overlaps this much ...
OWN_TEST_MIN_CONTAIN = 0.8      # ... or when (>= OWN_TEST_MIN_SHARED shared words) it contains / is contained by it
OWN_TEST_MIN_SHARED = 4
_ING = {"heft": "hefting", "scratch": "scratching", "scrape": "scraping",
        "smell": "smelling", "sniff": "sniffing", "fill": "filling", "check": "checking", "look": "looking at"}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z']+", (text or "").lower()))


def match_hypothesis(q: str, rows: list[dict]) -> dict | None:
    """The stored hypothesis (a world_substrate.inferences_with_test() row) that the boarded claim `q` IS, else
    None. Deterministic: word-set Jaccard >= OWN_TEST_MIN_JACCARD, or >= OWN_TEST_MIN_CONTAIN of the shorter
    side's words shared (at least OWN_TEST_MIN_SHARED words). Best score wins; ties go to the newest."""
    wq = _words(q)
    if len(wq) < OWN_TEST_MIN_SHARED:
        return None
    best, best_key = None, None
    for r in rows or []:
        wh = _words(r.get("hypothesis", ""))
        if not wh or not r.get("intervention_test"):
            continue
        inter = len(wq & wh)
        jac = inter / len(wq | wh)
        contain = inter / min(len(wq), len(wh))
        if jac >= OWN_TEST_MIN_JACCARD or (inter >= OWN_TEST_MIN_SHARED and contain >= OWN_TEST_MIN_CONTAIN):
            key = (max(jac, contain), float(r.get("timestamp", 0) or 0))
            if best_key is None or key > best_key:
                best, best_key = r, key
    return best


def describe_test(candidates: list[dict]) -> str:
    """Plain words for a stored intervention_test: what would tell the claim from coincidence. Names it, never
    says to do it (the world never leads). "" when there is nothing to say."""
    bits: list[str] = []
    for c in candidates or []:
        if not isinstance(c, dict):
            continue
        mode, verb, obj, when = c.get("mode", ""), c.get("verb", ""), c.get("object", ""), c.get("when", "")
        if mode == "withhold":
            b = f"holding back the {verb}" + (f" for {when}" if when else "")
        elif mode == "observe":
            b = f"looking at the {obj}" + (f" {when}" if when else "")
        elif verb == "float":
            b = f"seeing whether the {obj} floats"
        else:
            b = f"{_ING.get(verb, verb + 'ing')} the {obj}"
        if b and b not in bits:
            bits.append(b)
    return "; ".join(bits[:MAX_INTERVENTION_CANDIDATES])

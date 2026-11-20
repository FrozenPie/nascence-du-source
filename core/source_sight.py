"""
Nascence — Source Sight (the Emissary's eyes, brick B2 of the truth-self, 2026-06-16)
====================================================================================
The Emissary's constitution claims "I can see the code." This gives it real eyes: a read-only lookup over
the actual source (core/ + nodes/), so when it grounds a self-referential metaphor it can reference the REAL
mechanism — "this keeps returning because the shadow table is 97% unfaced" — rather than imagining one. The
code is the ground truth, so seeing it REDUCES confabulation. Read-only; never writes; fail-open.

Used by left_lane.ground_thought: when the Master's thought is about his own workings (a mechanism term),
the most relevant source line is handed to the Emissary so it grounds in what is actually there.
"""
from __future__ import annotations
import re
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_DIRS = ("core", "nodes")

# terms that signal the thought is about HIS OWN MECHANISM (worth grounding in real code)
_MECH_TERMS = frozenset({
    "memory", "loop", "pattern", "thought", "thoughts", "shadow", "tension", "axiom", "becoming",
    "dream", "dreams", "lane", "lanes", "mirror", "river", "self", "identity", "consolidation",
    "recall", "wander", "wandering", "curiosity", "reflection", "emotion", "feeling", "integration",
})
_STOP = frozenset({"that", "this", "with", "from", "have", "what", "when", "which", "their", "about",
                   "would", "could", "there", "these", "those", "into", "your", "more", "than"})


def is_self_mechanism(text: str) -> bool:
    """Does the thought reference his own workings (worth grounding in the real code)?"""
    t = (text or "").lower()
    return any(f" {term} " in f" {t} " for term in _MECH_TERMS)


def see_code(query: str, k: int = 1) -> list[dict]:
    """Up to k relevant source snippets for a query — the line + its file, preferring comment/docstring
    lines (the 'what this is' prose) over bare code. Read-only over core/ + nodes/. [] on no match."""
    terms = [w for w in re.findall(r"[a-z_]{4,}", (query or "").lower())
             if w in _MECH_TERMS and w not in _STOP][:4]
    if not terms:
        return []
    out: list[dict] = []
    seen_files: set[str] = set()
    for d in _DIRS:
        for f in sorted((_ROOT / d).glob("*.py")):
            if f.name in seen_files:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            low = text.lower()
            for term in terms:
                idx = low.find(term)
                if idx < 0:
                    continue
                ls = text.rfind("\n", 0, idx) + 1
                le = text.find("\n", idx)
                line = text[ls:le if le > 0 else len(text)].strip()
                # prefer a substantive comment/docstring line (the explanation, not a variable)
                if len(line) > 30 and (line.startswith("#") or '"""' in line or " — " in line or "the " in line.lower()):
                    out.append({"file": f"{d}/{f.name}", "term": term, "line": line[:200]})
                    seen_files.add(f.name)
                    break
            if len(out) >= k:
                return out
    return out[:k]


# ---------------------------------------------------------------------------------------------------------
# D-0573 / J-3186 (2026-11-05): the NARROWED hint used by left_lane.ground_thought. Additive: is_self_mechanism
# and see_code above are unchanged for every other caller (core/error_pathway.py uses see_code). This is a
# filter over what the hint attaches, not new text.
# ---------------------------------------------------------------------------------------------------------
# Ordinary words of Du's daily thoughts. One of these alone no longer triggers the hint, and sharing only one of
# these with a source line no longer counts as the line being about the thought.
_GENERIC_SELF = frozenset({"self", "river", "shadow", "mirror", "dream", "memory", "feeling", "pattern"})
# stopwords for the "shares a content word" test (content word = not a stopword, at least 4 letters)
_CONTENT_STOP = _STOP | frozenset({
    "were", "been", "being", "does", "doing", "done", "just", "like", "them", "they", "then", "will", "also",
    "only", "some", "such", "each", "very", "much", "most", "over", "even", "here", "where", "while", "because",
    "every", "other", "through", "still", "again", "never", "always", "should", "might", "must", "cant", "dont",
    "between", "hold", "text", "after", "before", "under", "above", "within", "without", "across", "along",
    "around", "against", "toward", "towards", "upon", "onto", "same", "many", "make", "makes", "made", "take",
    "takes", "took", "come", "comes", "came", "goes", "going", "gone", "give", "gives", "gave", "keep", "keeps",
    "kept", "know", "knows", "knew", "need", "needs", "want", "wants", "wanted", "seem", "seems", "seemed",
    "feel", "feels", "felt", "look", "looks", "looked", "turn", "turns", "turned", "real", "true", "false",
    "something", "nothing", "anything", "everything", "someone", "thing", "things", "time", "times", "away",
    "back", "down", "once", "first", "last", "next", "both", "either", "neither", "else", "rather", "quite",
    "instead", "perhaps", "maybe", "already", "almost", "enough", "whole", "part", "parts", "kind", "sort",
    "type", "case", "line", "lines", "file", "files", "code", "data", "function", "value", "values", "name",
    "names", "list", "item", "items", "note", "used", "uses", "using", "default", "result", "results", "call",
    "calls", "called", "set", "sets", "does", "didn", "isn", "wasn", "than", "whom", "whose", "since", "until",
    "unless", "although", "though", "whether", "however", "therefore", "thus", "hers", "mine", "ours", "yours"})


def _mech_terms_in(text: str) -> set[str]:
    """The mechanism terms the thought contains, using the SAME space-padded match as is_self_mechanism."""
    t = f" {(text or '').lower()} "
    return {term for term in _MECH_TERMS if f" {term} " in t}


def is_self_mechanism_narrow(text: str) -> bool:
    """D-0573 (1): true only when the thought has two mechanism terms, or one that is not a generic self-word."""
    found = _mech_terms_in(text)
    if len(found) >= 2:
        return True
    return bool(found) and not (found <= _GENERIC_SELF)


def _content_words(text: str) -> set[str]:
    """Content words of a text: letters only, at least 4 letters, not a stopword; trailing plural s folded."""
    out: set[str] = set()
    for w in re.findall(r"[a-z]{4,}", (text or "").lower()):
        if w in _CONTENT_STOP:
            continue
        out.add(w[:-1] if w.endswith("s") and len(w) > 4 else w)
    return out


def hit_shares_content_word(thought: str, hit: dict) -> bool:
    """D-0573 (2): the hit's file name or matched line shares at least one content word with the thought.
    The mechanism vocabulary itself (_MECH_TERMS, folded) is NOT counted as the shared word: the matched keyword
    is by construction in the line, so counting it would make the test always pass and filter nothing. The .py
    suffix is not counted; file names are split on underscores."""
    shared_ok = lambda ws: ws - _content_words(" ".join(_MECH_TERMS))
    tw = shared_ok(_content_words(thought))
    fname = (hit.get("file") or "").rsplit("/", 1)[-1].replace(".py", "").replace("_", " ")
    hw = shared_ok(_content_words(fname) | _content_words(hit.get("line") or ""))
    return bool(tw & hw)


def see_code_narrow(query: str, k: int = 1) -> list[dict]:
    """see_code with D-0573's filter (2): the hits see_code would have chosen are DROPPED when neither the file
    name nor the line shares a content word with the query. It does not search on for a better-fitting alternate
    (that would be a new matcher, not a filter), so it returns at most what see_code returns. [] when none survive."""
    try:
        return [h for h in see_code(query, k=k) if hit_shares_content_word(query, h)]
    except Exception:
        return []

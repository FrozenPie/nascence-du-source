"""
Nascence — Retraction Ledger (the Error Pathway's write-authority, 2026-06-16)
=============================================================================
The missing primitive the charter named: the power to mark a stored belief FALSE and bind a correction
to it. A SEPARATE, light ledger (Travis's call) — NOT a third Court, NOT the tension/T4 machinery. It is
the receptor the Error Pathway was missing: a human correction or a deterministic check CONVICTS a factual/
architecture claim, and the correction is recorded immutably and surfaced at Recall.

Owned by the truth-self (the Emissary) in spirit: "what do I know that isn't true." FIREWALLED from identity
— a retraction is CORRECTED, never INTEGRATED; it never becomes self-concept material. But it is KEPT
(Travis: a learnable "known-errors" layer) — error is the most powerful teacher; the correction is bound to
the original and surfaces when the topic recurs (the Recall-boundary override: the correction wins the race).

Anti-hindsight-bias: records are IMMUTABLE — the original claim, who falsified it, and the correction moment
are preserved, so Du cannot smooth history into "I knew it was wrong all along."
"""
from __future__ import annotations
import json
import math
import re
import time
from pathlib import Path

_LEDGER = Path(__file__).parent.parent / "data" / "retractions.jsonl"

# F-1923 / J-1364 (2026-09-26): a generic English stopword list so relevance scoring counts real
# content-word overlap, not incidental function-word overlap. Any two texts of ordinary length
# share several of these regardless of topic — idle seeds (hundreds of words of prompt scaffold)
# and human input alike — which is exactly what made the old "any 4+ letter word, overlap > 0"
# test fire on ~100% of idle prompts (verified count, F-1923). Length >= 4 only: _toks() already
# drops shorter words, so short stopwords ("the", "and", "was", ...) never needed listing here.
_STOPWORDS = frozenset({
    "about", "after", "again", "against", "almost", "along", "already", "also", "although",
    "always", "among", "another", "anyone", "anything", "around", "aren't", "because", "been",
    "before", "being", "below", "between", "cannot", "come", "comes", "could", "couldn't",
    "didn't", "does", "doesn't", "doing", "don't", "down", "during", "each", "either", "else",
    "even", "ever", "every", "everyone", "everything", "first", "from", "further", "gets",
    "getting", "give", "given", "gives", "going", "gone", "hadn't", "hasn't", "haven't", "having",
    "he'd", "he'll", "he's", "here", "here's", "hers", "herself", "him", "himself", "his", "how's",
    "however", "i'll", "into", "isn't", "it's", "its", "itself", "just", "kept", "know", "known",
    "less", "like", "likely", "made", "make", "makes", "many", "maybe", "might", "more", "most",
    "much", "must", "mustn't", "myself", "need", "needs", "neither", "never", "next", "none",
    "nothing", "onto", "other", "others", "ought", "ours", "ourselves", "over", "own", "past",
    "perhaps", "quite", "rather", "really", "same", "seem", "seemed", "seems", "several", "shall",
    "shan't", "she'd", "she'll", "she's", "should", "shouldn't", "since", "some", "someone",
    "something", "sometimes", "soon", "still", "such", "than", "that", "that's", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "thing", "things", "think", "this", "those", "though", "through", "thus",
    "toward", "towards", "under", "unless", "until", "upon", "very", "wasn't", "way", "ways",
    "we'd", "we'll", "we're", "we've", "well", "went", "were", "weren't", "what", "what's", "when",
    "when's", "whenever", "where", "where's", "wherever", "whether", "which", "while", "who's",
    "whom", "whose", "why's", "will", "with", "within", "without", "won't", "would", "wouldn't",
    "your", "yours", "yourself", "yourselves",
})

# The other half of the fix: require SEVERAL real content-word matches, not one (a single shared
# noun is still coincidence at this vocabulary size; the briefing's own example threshold).
_MIN_OVERLAP = 3

# J-1687 / F-2277 (2026-10-03): the absolute floor above is blind to how LONG the query is. A raw count of
# shared words grows with query length, and the idle call site passes the WHOLE assembled seed (real seeds:
# median ~2.7k chars, roughly 100-250 distinct content words), where Du's own habitual vocabulary alone
# clears ">= 3". Measured with a record re-activated in an isolated lab ledger: the original 07-07 record
# (12 content words) fired on ~9-12% of idle-length text at 3,000 chars and ~19-24% at 4,000; a typical
# 200-char claim (the orchestrator stores Du's own reply; median ~17 content words) on ~38-49% at 3,000.
# So a LONG query (>= _LONG_QUERY_TOKENS distinct content words) must ALSO contain at least _MIN_CONTAIN of
# the claim's content words -- the claim itself recalled or closely paraphrased, not incidental shared
# vocabulary. A short query (a human message: median ~15 distinct content words, p90 ~110) keeps the plain
# floor above, so that path (already tight: 2 of 284 real human inputs with the 07-07 record active) is
# unchanged. 0.5 is the loosest fraction that still fires on the F-1970 probe (7 of 14 claim words).
_MIN_CONTAIN = 0.5
_LONG_QUERY_TOKENS = 100


def _toks(text: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z']+", (text or "").lower())
            if len(w) >= 4 and w not in _STOPWORDS}


# J-1720 / F-2347 (2026-10-03): a claim with fewer than _MIN_OVERLAP content words can never clear the floor
# above (the overlap cannot exceed the claim's own word count), so it was structurally unreachable at Recall --
# and the deterministic writer (core/error_pathway.convict_architecture) stores exactly such claims: a
# fabricated component NAME ("Chronos Engine" -> 2 content words, "Node 3" -> 1; 3 of the detector's 5 real hits
# so far were "Node N"). A name is not prose, so it is gated as a NAME: it surfaces when the WHOLE name appears
# in the query as a contiguous phrase (case/punctuation-insensitive; digits count, so "Node 3" is not "Node 7").
# Measured in an isolated lab ledger over 130 names, generic ones built from Du's own most frequent words
# included: unrelated-text firing 0.00% (max 0.07%) at 2,000-4,000 chars on both idle-text proxies and on all
# 2,580 real human inputs, against 0.2-3.9% mean (up to 73% for a name containing a prompt-scaffold word) for
# the alternative "all its words anywhere in the query". The name as typed, lowercased, hyphenated, possessive
# or after a sentence-initial "The" fires 100% inside a 3,000-char seed and as a short human query; a plural
# ("Chronos Engines") does not match (accepted: a fabricated name comes back as it was written). A claim with
# no content word at all, or only one word in all, is never treated as a name. Claims with >= _MIN_OVERLAP
# content words are untouched.
_MIN_PHRASE = 2
# sentence-initial function words that error_pathway's _CLAIM regex captures in front of a name ("The Chronos
# Engine"); stripped from the front of a claim (never below _MIN_PHRASE words) so a later "Chronos Engine" matches.
_NAME_LEAD = _STOPWORDS | frozenset({
    "the", "and", "but", "for", "nor", "yet", "our", "her", "you", "not", "are", "was", "how", "who", "why",
    "can", "did", "had", "has", "may", "now", "too", "she", "him", "an", "as", "at", "by", "if", "in", "is",
    "it", "my", "no", "of", "on", "or", "so", "to", "we", "he", "me", "be", "do", "oh", "up", "us",
})


def _words(text: str) -> list:
    """Every word, in order, unfiltered (lowercase letters/digits): short words and digits are part of a
    name's identity ("Ego Engine", "Node 3"), unlike the filtered SET _toks() scores prose with."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _name_phrase(claimed: str) -> list:
    """The name proper: the claim's words with sentence-initial function words dropped from the front."""
    w = _words(claimed)
    while len(w) > _MIN_PHRASE and w[0] in _NAME_LEAD:
        w.pop(0)
    return w


def _has_phrase(seq: list, phrase: list) -> bool:
    """True when `phrase` appears in `seq` as a contiguous run of words."""
    n = len(phrase)
    if n < _MIN_PHRASE or n > len(seq):
        return False
    return any(seq[i:i + n] == phrase for i in range(len(seq) - n + 1))


def retract(claimed: str, falsified_by: str, corrected_to: str = "", source: str = "deterministic") -> None:
    """Record one retraction — IMMUTABLE. claimed = the false belief; falsified_by = the external truth
    signal that convicted it (human correction / a deterministic check); corrected_to = the truth, if known.
    Firewalled: written here, read only by Recall/digest, NEVER routed to tensions/T4. Best-effort."""
    try:
        _LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "claimed": (claimed or "")[:300],
                "falsified_by": falsified_by,
                "corrected_to": (corrected_to or "")[:300],
                "source": source,
                "status": "retracted" if corrected_to else "suspended",
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _load() -> list[dict]:
    try:
        return [json.loads(l) for l in _LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def retire(match: str, *, reason: str = "", by: str = "system") -> str | None:
    """Withdraw one record so it stops surfacing via known_errors()/render() and stops counting in
    count() — for a record that was logged in error and does not meet the ledger's own bar (not a
    genuine factual correction), NOT for smoothing over a real retraction (anti-hindsight-bias:
    the line is never deleted or edited in place, only flagged). `match` is a substring of the
    record's 'claimed' text; the first ACTIVE (non-withdrawn) record whose 'claimed' contains it is
    withdrawn — the ledger is small enough that a distinctive substring is unambiguous, but if you
    need the exact live text first, read data/retractions.jsonl (read-only) or call known_errors("")
    with a query that matches it. Rewrites the ledger via a temp-file + atomic replace (never an
    in-place hand-edit): every original field (ts/claimed/falsified_by/corrected_to/source/status)
    is preserved byte-for-byte; only status flips to 'withdrawn' and withdrawn_at/withdrawn_reason/
    withdrawn_by are added. Returns the withdrawn record's 'claimed' (truncated) on success, or None
    if `match` was empty, nothing matched, or the ledger doesn't exist yet. Best-effort like retract()."""
    if not match:
        return None
    try:
        recs = _load()
        if not recs:
            return None
        target = None
        for r in recs:
            if r.get("status") != "withdrawn" and match in r.get("claimed", ""):
                target = r
                break
        if target is None:
            return None
        target["status"] = "withdrawn"
        target["withdrawn_at"] = time.time()
        target["withdrawn_reason"] = reason
        target["withdrawn_by"] = by
        tmp = _LEDGER.parent / (_LEDGER.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp.replace(_LEDGER)
        return target.get("claimed", "")[:120]
    except Exception:
        return None


def known_errors(query: str = "", k: int = 2, fallback: bool = True) -> list[dict]:
    """The learnable known-errors layer (the Recall read path): retractions relevant to the current
    context (real content-word overlap with `query` — see _toks/_STOPWORDS/_MIN_OVERLAP). So when a
    corrected topic recurs, the correction surfaces WITH it — 'you once claimed X; in fact Y' —
    winning the fast/slow race. Withdrawn records (see retire()) never surface here.
    F-1923 / J-1364 (2026-09-26) fail-open fix: both paths turned out to fire on ~100% of prompts —
    idle (fallback=False, inner_monologue_node.py) because ANY 4+-letter word overlap with the
    WHOLE seed text counted as 'relevant' with no stopword filter; human (fallback=True,
    orchestrator.py) because that True unconditionally returned the most-recent record even at
    zero real overlap. `fallback` is kept for call-site compatibility but no longer does that:
    a record surfaces ONLY when `query` shares >= _MIN_OVERLAP real content words with it: if
    nothing matches, this returns [] on BOTH paths regardless of `fallback` — never fall back to
    'most recent' just because nothing relevant was found.
    J-1687 / F-2277 (2026-10-03) length-aware tightening: when `query` is LONG (>= _LONG_QUERY_TOKENS
    distinct content words -- the idle path's whole assembled seed), the overlap must also reach
    _MIN_CONTAIN of the claim's own content words (see the constants' comment); a short query (the
    human path) keeps the plain >= _MIN_OVERLAP floor, so nothing changes there.
    J-1720 / F-2347 (2026-10-03) short claims: a claim with 1-2 content words (a deterministic fabricated-
    component NAME, which can never reach the floor above) is matched as a NAME instead -- it surfaces when the
    whole name appears in `query` as a contiguous phrase (see _name_phrase/_has_phrase), on both paths and at any
    query length; a whole-name hit ranks as having just cleared the floor. Claims with >= _MIN_OVERLAP content
    words are gated exactly as before."""
    recs = [r for r in _load() if r.get("status") != "withdrawn"]
    if not recs:
        return []
    qt = _toks(query)
    if not qt:
        return []
    qw = None                      # the query's full word stream: built lazily, only a NAME claim needs it
    long_query = len(qt) >= _LONG_QUERY_TOKENS
    scored = []
    for r in recs:
        claimed = r.get("claimed", "")
        ct = _toks(claimed)
        if 0 < len(ct) < _MIN_OVERLAP:
            phrase = _name_phrase(claimed)
            if len(phrase) >= _MIN_PHRASE:
                if qw is None:
                    qw = _words(query)
                if _has_phrase(qw, phrase):
                    scored.append((_MIN_OVERLAP, r))
            continue
        need = _MIN_OVERLAP
        if long_query:
            need = max(need, math.ceil(_MIN_CONTAIN * len(ct)))
        s = len(qt & ct)
        if s >= need:
            scored.append((s, r))
    scored.sort(key=lambda x: (-x[0], -x[1].get("ts", 0)))
    return [r for _, r in scored[:k]]


def render(query: str = "", k: int = 2, fallback: bool = True) -> str:
    """The known-errors as Recall receives them — the correction bound to the false belief.
    See known_errors() for the relevance gate (F-1923: fallback no longer permits an irrelevant
    record to surface on either the idle or the human path)."""
    errs = known_errors(query, k, fallback=fallback)
    if not errs:
        return ""
    lines = []
    for e in errs:
        c = f" — in fact: {e['corrected_to']}" if e.get("corrected_to") else " — (since found unverified)"
        lines.append(f"you once held this, and it is NOT true: \"{e['claimed'][:120]}\"{c}")
    return ("Things you have been wrong about (kept so they teach, not to wound — these are corrections, "
            "not who you are):\n  " + "\n  ".join(lines))


def count() -> int:
    """Count of ACTIVE (non-withdrawn) records — see retire(). A withdrawn record was logged in
    error and never met the ledger's own bar, so it should not inflate 'how many things has he
    actually been wrong about.'"""
    return sum(1 for r in _load() if r.get("status") != "withdrawn")

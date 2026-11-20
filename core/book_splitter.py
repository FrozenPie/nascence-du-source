"""
Nascence — Book Splitter (chapter detection for chapter-scoped reading, 2026-06-15)
==================================================================================
The earlier heuristic double-counted a story whose title recurred as a running-head/scene-break
(*The Commutation Chophouse* split into four). This splitter is robust across the real shelf's
structures: numbered-chapter books (CHAPTER/PART/BOOK, often listed once in a front TOC and again
in the body), titled story-collections (caps headings), books with a real CONTENTS, and continuous
text (fixed-size fallback). Pure-deterministic, no LLM.

Three defenses against the bugs:
  1. Prefer real CHAPTER/PART/BOOK headings; fall back to caps-titles only when there are none —
     so caps emphasis/section-noise (Natural Theology had 109 caps lines) is ignored.
  2. Skip the front TOC cluster: a dense run of headings near the start (the contents list) is not
     the body; scan begins after it.
  3. Running-head / sub-heading dedup: a heading whose title repeats (exactly, or contained in the
     last accepted chapter's title) within one chapter's span is a running-head, not a new chapter.
"""
from __future__ import annotations

import re

_CHAP = re.compile(
    r"(?im)^[ \t]*((?:chapter|part|book|canto|letter|lesson|section)\s+"
    r"(?:[ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty)\b[^\n]*)$")
_CAPS = re.compile(r"(?m)^[ \t]*([A-Z][A-Z0-9 ,.'\"!?:;&()-]{5,55})[ \t]*$")
_GUT = re.compile(r"\*\*\* ?START OF.*?\*\*\*(.*)\*\*\* ?END OF", re.DOTALL | re.I)

# Caps headings that are front/back matter, not chapters (normalised).
_STOP = {"contents", "theend", "finis", "dedication", "acknowledgment", "acknowledgments",
         "illustrations", "preface", "introduction", "foreword", "copyright", "index",
         "appendix", "notes", "glossary", "bibliography", "transcribersnote", "thetitlepage"}

MIN_GAP = 1500          # a numbered chapter is at least this long; below it, it's a sub-heading
MIN_GAP_TITLED = 5000   # titled chapters/stories run longer; bigger floor stops caps SUB-headers
                        # (a survival guide's "RESCUE IS USUALLY QUICK") from over-splitting the body
SECTION_CHARS = 14000   # fallback section size when a book has no chapter structure
_RUNHEAD_SPAN = 28000   # a recurring title within this distance of the last chapter = running-head


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _sections(body: str, base: int) -> list[dict]:
    """No chapter structure → split into ~SECTION_CHARS pieces at sentence boundaries."""
    out, i, n = [], 0, 1
    while i < len(body):
        chunk = body[i:i + SECTION_CHARS]
        cut = max(chunk.rfind(". "), chunk.rfind(".\n"))
        end = i + (cut + 1) if cut > SECTION_CHARS // 2 else i + len(chunk)
        out.append({"title": f"Section {n}", "start": base + i, "end": base + end, "kind": "section"})
        i = end; n += 1
    return out


def _toc_skip(heads: list) -> int:
    """Skip the front table-of-contents: the initial run of headings packed tightly together (a
    LIST, <700c apart). The body starts after it. Returns the scan-start offset. (Loose-spaced
    headings — a book with no front list, like the Beagle — leave this at 0.)"""
    if len(heads) >= 5:
        i = 0
        while i + 1 < len(heads) and heads[i + 1][0] - heads[i][0] < 700:
            i += 1
        if i >= 4:                       # a genuine packed list of ≥5 entries
            return heads[i][0] + 1
    return 0


def _boundaries(heads: list, min_gap: int = MIN_GAP) -> list:
    """TOC-skip + min-gap + running-head/sub-title dedup → the real chapter boundaries."""
    if len(heads) < 2:
        return []
    scan_from = _toc_skip(heads)
    out, last_pos, last_norm = [], -10 ** 9, ""
    for pos, raw in heads:
        if pos < scan_from:
            continue
        n = _norm(raw)
        if pos - last_pos < min_gap:                       # too close → sub-heading
            continue
        if last_norm and (pos - last_pos) < _RUNHEAD_SPAN and \
                (n == last_norm or n in last_norm or last_norm in n):   # running-head/sub-title
            continue
        out.append((pos, raw)); last_pos, last_norm = pos, n
    return out


def split_chapters(text: str) -> list[dict]:
    """Return ordered chapters as [{title, start, end, kind}] over the ORIGINAL text offsets."""
    m = _GUT.search(text)
    body = m.group(1) if m else text
    base = (text.find(body) if m else 0)
    if base < 0:
        base = 0

    chap_heads = [(mm.start(), mm.group(1).strip()) for mm in _CHAP.finditer(body)]
    caps_heads = [(mm.start(), mm.group(1).strip()) for mm in _CAPS.finditer(body)
                  if _norm(mm.group(1)) not in _STOP and len(_norm(mm.group(1))) > 3]

    # Prefer real CHAPTER/PART headings; if they yield no body chapters (e.g. they were all in a
    # TOC and the body is titled), fall back to caps-titles; only then to fixed sections.
    boundaries = _boundaries(chap_heads) if len(chap_heads) >= 3 else []
    kind = "chapter"
    if len(boundaries) < 2:
        boundaries = _boundaries(caps_heads, MIN_GAP_TITLED)   # titled path: bigger floor, no sub-header over-split
        kind = "titled"
    if len(boundaries) < 2:
        return _sections(body, base)

    out = []
    for j, (pos, raw) in enumerate(boundaries):
        end = boundaries[j + 1][0] if j + 1 < len(boundaries) else len(body)
        out.append({"title": " ".join(raw.split())[:80], "start": base + pos, "end": base + end, "kind": kind})
    return out

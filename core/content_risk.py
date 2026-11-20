"""
Nascence — Content Risk (the critical-distance floor, 2026-08-19). PHASE 0 = SHADOW/observe-only.

Founder-chosen approach (not a subject/keyword denylist): the confirmed real incident — *The Traitor*
(Thomas Dixon Jr., 22 downloads, read 100%/62 sittings, engaged as neutral plot texture with zero
critical distance despite being Klan apologia — the direct source material for "Birth of a Nation") —
was checked against the real catalogue. Its ONLY subject is 'Reconstruction (U.S. history, 1865-1877)
-- Fiction', a broad, legitimate heading shared by many unrelated books. A subject-based floor would
either be useless (too narrow to catch anything) or a de facto denylist on an entire historical-fiction
genre (too broad) — neither is the "critical distance, not exclusion" the founder asked for.

The real signal in the one confirmed case is the AUTHOR, not the subject. This starts as a small,
explicit, auditable author watchlist — NOT a general classifier — because a single incident does not
license a broad heuristic; extend deliberately as real cases accumulate, never preemptively.

This is a FLOOR, not a gate: it does not change book_selection's selection weight or block anything.
It logs what it would flag, so the founder can read real firing evidence before deciding what "critical
distance" should actually mean downstream (an epistemic/provenance tag feeding source_model.py? a study-
note framing hint? something else) — that design question stays open until there's real shadow data.
"""
from __future__ import annotations

import json
import logging
import time
import threading
from pathlib import Path

logger = logging.getLogger("nascence.content_risk")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "content_risk_shadow.jsonl"

# Small and explicit on purpose. Each entry names WHY, so extending this list is a documented decision,
# never a silent keyword add. Author string matches the SPGC metadata CSV's own `author` field format
# ("Last, First"), verified against the real catalogue row for the confirmed incident.
FLAGGED_AUTHORS = {
    "Dixon, Thomas": (
        "The Reconstruction Trilogy (The Leopard's Spots / The Clansman / The Traitor) — explicit "
        "apologia for the Ku Klux Klan, framed as fiction; The Clansman is the direct source material "
        "for Birth of a Nation. Confirmed incident: The Traitor read 100%/62 sittings, engaged as "
        "neutral plot texture, zero critical distance (2026-08-19 audit)."
    ),
}


def classify_row(row: dict) -> dict | None:
    """row = a catalogue metadata dict (book_selection._rows()' shape) or any dict carrying 'author'/
    'title'. Returns {author, title, reason} if flagged, else None. Fail-open: never raises."""
    try:
        author = (row.get("author") or "").strip()
        if not author:
            return None
        reason = FLAGGED_AUTHORS.get(author)
        if reason is None:
            return None
        return {"author": author, "title": (row.get("title") or "")[:120], "reason": reason}
    except Exception as exc:
        logger.debug("[content_risk] classify_row failed (non-fatal): %s", exc)
        return None


# J-1926 / F-2550: shadow_check runs from book_selection.record_pick in the library worker thread and from other callers; serialise the append.
_APPEND_LOCK = threading.Lock()


def shadow_check(row: dict, *, context: str = "") -> dict | None:
    """Classify + log if flagged. Call from any point a book is selected/finished/consumed — this is
    additive, does not touch selection weight or reading behaviour. Fail-open."""
    flag = classify_row(row)
    if flag is None:
        return None
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with _APPEND_LOCK, open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "context": context[:40], **flag},
                                ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[content_risk] shadow log failed (non-fatal): %s", exc)
    return flag


def status() -> dict:
    """For the pulse: how often has the watchlist fired, on what, and how (selection vs finish vs other)."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): counts/titles are now over the last-2000-row window.
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"fires": 0, "watchlist_size": len(FLAGGED_AUTHORS)}
    by_context: dict = {}
    for r in rows:
        by_context[r.get("context", "")] = by_context.get(r.get("context", ""), 0) + 1
    return {"fires": len(rows), "watchlist_size": len(FLAGGED_AUTHORS),
            "by_context": by_context, "titles": sorted({r.get("title", "") for r in rows})}

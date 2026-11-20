"""
Nascence — Reading History (what he has already read, for selection)
====================================================================
A thin read-only view over reading_state.json so the book-selection engine can answer:
"have I read this / how finished is it / when last / how many rereads?" — the memory that
turns blind re-picking into informed explore/exploit (docs/book_selection_plan.md, 2026-06-16).

Derives everything from the existing per-book reading record; stores nothing new. A book is
"read" once it reaches READ_PCT (the same 97% threshold school uses for completion).
"""
from __future__ import annotations
import json
import re
from pathlib import Path

STATE = Path(__file__).parent.parent / "data" / "reading_state.json"
READ_PCT = 97.0


def _load() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    except Exception:
        return {}


def normkey(title: str) -> str:
    """A comparison key: lowercased alphanumerics only. Shelf filenames are truncated, underscored
    catalogue titles, so we compare on this normalised form (prefix-aware in `is_known`)."""
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def _book_records() -> dict[str, dict]:
    """Per-book records keyed by path string (drops the _current_book pointer)."""
    return {k: v for k, v in _load().items() if isinstance(v, dict)}


def book_stats(book: str | Path) -> dict:
    """{pct, sitting, rereads, last_read_ts} for a book path, with safe defaults."""
    rec = _book_records().get(str(book), {})
    return {"pct": float(rec.get("pct", 0) or 0), "sitting": int(rec.get("sitting", 0) or 0),
            "rereads": int(rec.get("rereads", 0) or 0), "last_read_ts": rec.get("last_read_ts")}


def read_paths() -> list[str]:
    """Paths of books he has FINISHED (pct >= READ_PCT)."""
    return [k for k, v in _book_records().items() if float(v.get("pct", 0) or 0) >= READ_PCT]


def shelf_keys(include_unfinished: bool = True) -> set[str]:
    """Normalised title-keys for everything already on his shelf (so the explore branch never
    re-fetches a book he already owns). include_unfinished=True covers in-progress books too —
    re-acquiring a half-read book is still a re-pick, not breadth. Pulls from BOTH the reading
    record and the physical shelf (a fetched-but-never-opened book has no record yet)."""
    keys = set()
    for k, v in _book_records().items():
        if include_unfinished or float(v.get("pct", 0) or 0) >= READ_PCT:
            keys.add(normkey(Path(k).stem))
    try:
        from core import library_hand as _lib
        for p in _lib.shelf_books():
            keys.add(normkey(p.stem))
    except Exception:
        pass
    keys.discard("")
    return keys


def is_known(catalogue_title: str, keys: set[str] | None = None) -> bool:
    """True if a catalogue title is already on his shelf. Shelf filenames are truncated (~60 chars)
    catalogue titles, so we match by prefix on the normalised key in EITHER direction."""
    if keys is None:
        keys = shelf_keys()
    ck = normkey(catalogue_title)
    if not ck:
        return False
    for k in keys:
        if not k:
            continue
        short, long = (k, ck) if len(k) <= len(ck) else (ck, k)
        if len(short) >= 12 and long.startswith(short):   # 12 chars ≈ enough to be the same book
            return True
    return False

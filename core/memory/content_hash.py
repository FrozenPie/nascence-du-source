"""J-3266 / D-0657: the content hash behind the exact-dedup index.

One definition, imported by the writer (store.store_fragment), the reader (loop_metabolism.find_exact_dup) and the
offline backfill (scripts/apply_J-3266_content_hash_backfill.py), so the three can never drift apart. No core
imports and no file/network I/O (the one DB touch is the caller-supplied connection in has_hash_column): safe to
import from anywhere, including a standalone script.

Algorithm: BLAKE2b, 16-byte digest, lowercase hex (32 chars), over the UTF-8 bytes of the content EXACTLY as stored
(no strip, no case-fold, no normalisation: the dedup is exact-content equality and the hash must be exactly as
strict). `surrogatepass` so a lone surrogate (which Python str allows) hashes instead of raising; the hash is only
ever a lookup KEY: a hit is always confirmed by comparing the real content, so a collision (about 2**-64 at this
table size) cannot create a false duplicate.
"""
from __future__ import annotations

import hashlib

ALGORITHM = "blake2b-128"


def content_hash(content: str) -> str | None:
    """Hex digest of `content`, or None if it cannot be hashed (not a str). Never raises."""
    try:
        return hashlib.blake2b(content.encode("utf-8", "surrogatepass"), digest_size=16).hexdigest()
    except Exception:
        return None


def has_hash_column(conn) -> bool:
    """J-3395 / F-4019: True if memory_fragments on `conn` has the content_hash column (a PRAGMA read, never raises).

    The writers that edit or insert content outside store_fragment use this to stamp the hash only where the
    column exists, so a DB that has not run the J-3266 migration yet keeps working exactly as before."""
    try:
        return any(r[1] == "content_hash" for r in conn.execute("PRAGMA table_info(memory_fragments)"))
    except Exception:
        return False

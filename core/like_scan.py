"""core/like_scan.py (J-1922 / F-2549, 2026-10-07, restart-gated).

Single-pass substitute for repeated `content LIKE '%term%'` table scans.

After J-1917 moved the sleep sweeps off the event loop they still cost ~4.7 min per sleep, almost all of it
SQLite re-scanning the same ~100 MB of memory_fragments text once per term: book_residue.sweep 842 + 289
statements, stick_test.census 50 COUNT(*) scans, world_consolidation.sweep 150 candidate SELECTs. LIKE with a
leading wildcard cannot use an index, so each statement reads every candidate row. This module lets a caller
read the rows ONCE and answer every term from memory, with exactly SQLite's LIKE semantics:

  * LIKE is case-INSENSITIVE for ASCII letters ONLY (A-Z == a-z); every other character, including non-ASCII
    letters, compares exactly. `str.lower()` is NOT that (it folds the Kelvin sign and U+0130 to ASCII letters), so
    `ascii_lower` below maps A-Z only.
  * `%` and `_` in the PATTERN are wildcards (no ESCAPE clause is used by any caller); a needle containing either
    is NOT handled here (`is_plain_needle` is False) and the caller keeps its old per-term SQL for that needle.
  * SQLite's LIKE sees a TEXT value only up to its first NUL; `sql_text` truncates the same way.
  * NULL never matches. A non-TEXT value (BLOB/int) raises `Unsupported`, so the caller falls back to SQL.

`LikeIndex` joins the ASCII-lowered rows with NUL separators into one string and finds a needle with `str.find`
(a plain needle contains no NUL, so a hit can never straddle two rows); `iter_matches` yields matching row indices
in ascending order. Whole-module kill switch: SWEEPS_SINGLE_PASS = False makes every caller run its original
per-term SQL, unchanged.
"""
from __future__ import annotations

import bisect

SWEEPS_SINGLE_PASS = True     # kill-switch: False = every caller runs its original per-term SQL scans (pre-J-1922)

_LOWER = {i: i + 32 for i in range(65, 91)}      # A-Z -> a-z, nothing else (SQLite LIKE's case folding)


class Unsupported(Exception):
    """The data has a shape the single-pass matcher does not reproduce exactly; the caller must use its SQL."""


def ascii_lower(s: str) -> str:
    return s.translate(_LOWER)


def is_plain_needle(t) -> bool:
    """True when `%{t}%` is a pure substring pattern: a non-empty str with no LIKE wildcard and no NUL."""
    return isinstance(t, str) and t != "" and "%" not in t and "_" not in t and "\x00" not in t


def sql_text(content) -> str:
    """The text SQLite's LIKE actually compares: NULL -> '' (never matches a non-empty needle), TEXT up to its
    first NUL; anything that is not a str raises Unsupported."""
    if content is None:
        return ""
    if not isinstance(content, str):
        raise Unsupported(f"non-text content {type(content).__name__}")
    i = content.find("\x00")
    return content if i < 0 else content[:i]


class LikeIndex:
    """Substring index over a fixed list of row contents (see the module docstring for the exact semantics)."""

    def __init__(self, contents):
        lows = [ascii_lower(sql_text(c)) for c in contents]
        offs = []
        pos = 0
        for s in lows:
            offs.append(pos)
            pos += len(s) + 1
        self.n = len(lows)
        self._offs = offs
        self._big = "\x00".join(lows)

    def _row_end(self, i: int) -> int:
        return self._offs[i + 1] - 1 if i + 1 < self.n else len(self._big)

    def iter_matches(self, needle: str, stop_row: int | None = None):
        """Row indices (ascending) whose text contains `needle` (ASCII-case-insensitive), considering only rows
        [0, stop_row). `needle` must satisfy is_plain_needle."""
        nl = ascii_lower(needle)
        big, offs, n = self._big, self._offs, self.n
        end = len(big) if (stop_row is None or stop_row >= n) else offs[stop_row]
        pos = big.find(nl, 0, end)
        while pos != -1:
            i = bisect.bisect_right(offs, pos) - 1
            yield i
            if i + 1 >= n:
                return
            pos = big.find(nl, offs[i + 1], end)

    def row_has(self, i: int, needle: str) -> bool:
        """Does row i contain `needle` (ASCII-case-insensitive)?"""
        return self._big.find(ascii_lower(needle), self._offs[i], self._row_end(i)) != -1

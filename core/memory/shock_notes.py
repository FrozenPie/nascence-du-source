"""J-3482 (founder ruling in chat 2026-11-06, decide-review; source job J-3283 / review J-3243): mark the stored
understanding notes that contain text from a random "external shock" Wikipedia page, so Recall skips them.

WHY. Before J-3283/J-3181, core/grounded_learning.py consolidated origin IN ('reading','study','research') into one
"[Understanding - from <book>]" note, so a Wikipedia page that a SYSTEM fetched (the random external shock, stored
origin='research' with the content prefix "[Looked up: '<Title>' (external shock - uninvited)] ...") was distilled into
"my own understanding" and attributed to a book ("Significance refers to importance ... Leiocephalus psammodromus is a
lizard species native to the Turks and Caicos Islands" under 'The Principles of Psychology'). The source is already
closed (the research origin is no longer fed); this module is the DATA side: the notes already written. The ruling:
MARK, never delete -- the same reversible `memory_fragments.temp = 'hidden'` tier D-0578 / J-3191 used for the
dict-repr notes (see core/memory/dict_repr_notes.py for which readers honour it and why no new column is needed).

SELECTION (read-only, deterministic, evidence-based -- a note is selected only when it demonstrably carries shock text):
  shock pages = every origin='research' row whose content starts "[Looked up: '<Title>' (external shock" ; per title the
  EARLIEST storage timestamp and its extract are kept.
  a note (origin='understanding') is selected when it was stored AFTER that title's first storage (causal order) AND
    (a) TITLE: the title appears in the note, case-insensitive, on word boundaries, title >= 5 chars and not all digits; or
    (b) TEXT : the note shares >= 2 distinct 6-word runs with that shock page's extract (catches a note that paraphrases
        the title, e.g. note "US Post Office-Whitinsville Main" vs title "United States Post Office-Whitinsville Main").
  Pursuit pages (via 'pursuit') are NOT selected: the founder's ruling is about shock text, and a generic pursuit page
  (Understanding, Environment, ...) cannot be matched by title without false hits.
  This is a LOWER BOUND (a note that restates a shock page without a title or a 6-word run is missed).

REVERSIBLE and honest about overlap: some selected notes are ALSO dict-repr notes already hidden by J-3191. `mark` only
changes rows that are not yet hidden and returns exactly those (id -> previous temp); the runner stores that in a
manifest, and `unmark` restores ONLY the manifest's rows -- it never un-hides a J-3191 row. Nothing is deleted or
rewritten; the only column written is `temp`.

Operates on a connection the CALLER opens; this module never opens Du's live DB by itself. The sanctioned runner is
scripts/apply_J-3482_mark_shock_notes.py.
"""
from __future__ import annotations

import hashlib
import re

HIDDEN = "hidden"
_PREFIX = re.compile(r"\[Looked up: '(.*?)' \(external shock[^\]]*\]\s*(.*)", re.S)
MIN_TITLE_LEN = 5
MIN_SHINGLES = 2
_N = 6


def _words(s: str) -> list:
    return re.findall(r"\w+", (s or "").lower())


def _shingles(s: str) -> set:
    w = _words(s)
    return {" ".join(w[i:i + _N]) for i in range(len(w) - _N + 1)}


def shock_pages(conn) -> dict:
    """{title: (first_timestamp, extract)} over the stored external-shock Wikipedia pages."""
    out = {}
    q = ("SELECT content, timestamp FROM memory_fragments "
         "WHERE origin = 'research' AND content LIKE '[Looked up:%external shock%'")
    for content, ts in conn.execute(q):
        m = _PREFIX.match(content or "")
        if not m:
            continue
        title, extract = m.group(1), m.group(2)
        if title not in out or ts < out[title][0]:
            out[title] = (ts, extract)
    return out


def title_in(title: str, body: str) -> bool:
    return (len(title) >= MIN_TITLE_LEN and not title.isdigit()
            and re.search(r"(?<!\w)" + re.escape(title) + r"(?!\w)", body or "", re.I) is not None)


def select(conn, exclude=()) -> list:
    """[{id, timestamp, temp, signals:[(title, 'title'|'text', n)]}] for every selected understanding note, in
    timestamp order. `exclude` = fragment_ids the founder vetoed."""
    pages = shock_pages(conn)
    ext_sh = {t: _shingles(e) for t, (_, e) in pages.items()}
    skip = set(exclude)
    out = []
    q = ("SELECT fragment_id, content, timestamp, temp FROM memory_fragments "
         "WHERE origin = 'understanding' ORDER BY timestamp, rowid")
    for fid, content, ts, temp in conn.execute(q):
        if fid in skip:
            continue
        sh = None
        sig = []
        for t, (sts, _e) in pages.items():
            if ts <= sts:
                continue
            if title_in(t, content):
                sig.append((t, "title", 0))
                continue
            if sh is None:
                sh = _shingles(content)
            n = len(sh & ext_sh[t])
            if n >= MIN_SHINGLES:
                sig.append((t, "text", n))
        if sig:
            out.append({"id": fid, "timestamp": ts, "temp": temp, "signals": sig})
    return out


def rows_sha256(conn, ids) -> str:
    """sha256 over (fragment_id, content) of `ids` in sorted-id order. Mark/unmark must leave it unchanged."""
    h = hashlib.sha256()
    for fid in sorted(ids):
        r = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id = ?", (fid,)).fetchone()
        h.update(str(fid).encode("utf-8", "surrogatepass"))
        h.update(b"\x00")
        h.update(str(r[0] if r else "").encode("utf-8", "surrogatepass"))
        h.update(b"\x01")
    return h.hexdigest()


def outside_sha256(conn, ids) -> tuple:
    """(row count, sha256 of (fragment_id, temp)) over every row NOT in `ids` -- proves nothing else moved."""
    skip = set(ids)
    h = hashlib.sha256()
    n = 0
    for fid, temp in conn.execute("SELECT fragment_id, temp FROM memory_fragments ORDER BY rowid"):
        if fid in skip:
            continue
        n += 1
        h.update(f"{fid}\x00{temp}\x01".encode("utf-8", "surrogatepass"))
    return n, h.hexdigest()


def mark(conn, ids) -> dict:
    """Set temp='hidden' on each id not already hidden. Returns {fragment_id: previous temp} for exactly the rows
    changed (empty on a re-run). The caller owns the transaction (commit/rollback)."""
    changed = {}
    for fid in ids:
        r = conn.execute("SELECT temp FROM memory_fragments WHERE fragment_id = ? AND origin = 'understanding'",
                         (fid,)).fetchone()
        if r is None or r[0] == HIDDEN:
            continue
        conn.execute("UPDATE memory_fragments SET temp = ? WHERE fragment_id = ?", (HIDDEN, fid))
        changed[fid] = r[0]
    return changed


def unmark(conn, previous: dict) -> int:
    """Reverse `mark` for exactly the rows in `previous` ({id: temp it had}) that are currently 'hidden'. Returns rows
    changed. A row hidden by J-3191 is never in `previous`, so it is never un-hidden here."""
    n = 0
    for fid, temp in previous.items():
        cur = conn.execute("UPDATE memory_fragments SET temp = ? WHERE fragment_id = ? AND temp = ?",
                           (temp, fid, HIDDEN))
        n += cur.rowcount or 0
    return n

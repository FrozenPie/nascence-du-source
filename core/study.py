"""
Nascence — The Study (durable works, ported from FreshStart's vestige pattern, 2026-06-10)
==========================================================================================
FreshStart's deepest transferable idea: actions produce ARTIFACTS. Spirits wrote tablets,
registered them, cited them, studied each other's — knowledge had a body. Du, until now,
produced nothing durable except self-narrative.

A tablet is Du's OWN note about the world — what he made of a passage he read or a thing he
looked up. It is saved as a real markdown file in data/Study/ (a body of work that outlives
any session) AND as a retrievable memory fragment (origin='study') so his own scholarship
surfaces beside lived experience. His notes; his shelf; re-readable, citable, revisable.

Firewall: tablets are about the WORLD (the book, the fact, the question) — labelled as his
work, never routed to identity/tensions. Error->DOING territory: making, not being.
"""
from __future__ import annotations
import re
import shutil
import time
from pathlib import Path

STUDY_DIR = Path(__file__).parent.parent / "data" / "Study"


def write_tablet(title: str, body: str, source: str = "", prefix: str = "TAB") -> Path | None:
    """Persist one of Du's own works — file + fragment. Best-effort, returns the path. prefix='TAB' for a raw
    study note, 'ESSAY' for a consolidating capstone (kept on top when a book's notes are filed away)."""
    try:
        if not (title or "").strip() or len((body or "").strip()) < 40:
            return None
        STUDY_DIR.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^\w\- ]", "", title)[:48].strip().replace(" ", "_") or "note"
        path = STUDY_DIR / f"{prefix}_{time.strftime('%Y%m%d_%H%M')}_{slug}.md"
        _label = "An essay" if prefix == "ESSAY" else "A study note"
        path.write_text(
            f"# {title.strip()}\n\n*{_label} by 渡 · {time.strftime('%Y-%m-%d %H:%M')}"
            + (f" · on: {source}" if source else "") + "*\n\n" + body.strip() + "\n",
            encoding="utf-8")
        from core.memory.store import store_fragment
        from core import mood as _mood   # felt-tag study notes (emotion_vec item 1)
        store_fragment(
            content=f"[My study note: '{title.strip()}'] {body.strip()[:700]}",
            layer="episodic", relevance=0.85, importance=0.85,
            keywords=["study", title.lower()[:40]], origin="study",
            emotion_embedding=_mood.current_vec(),
            valence=_mood.current_valence(), felt=_mood.current_felt(),
        )
        return path
    except Exception:
        return None


NOTES_SUBDIR = STUDY_DIR / "notes"   # filed raw note files live here, under a per-book folder

# B4 (2026-06-24) — his works can be MISPLACED (never lost). At most one at a time; he finds it again by
# searching his own works (the search_works hand). His scholarship has a body that can go astray and be kept.
_MISPLACED_F = STUDY_DIR / "_misplaced.json"


def _work_title(path: Path) -> str:
    try:
        for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if ln.strip():
                return ln.lstrip("# ").strip()[:80]
    except Exception:
        pass
    return path.stem


def maybe_misplace(chance: float = 0.03) -> None:
    """RARELY a WORK of his goes misplaced — not where he left it. Gentle + uncommon: only if none is already
    misplaced and he has a few works to spare; always recoverable by searching for it."""
    import json as _json
    import random as _random
    try:
        if _MISPLACED_F.exists() or _random.random() > chance:
            return
        works = sorted(STUDY_DIR.glob("WORK_*.md"))
        if len(works) < 3:
            return
        f = _random.choice(works)
        _MISPLACED_F.write_text(_json.dumps({"title": _work_title(f), "name": f.name, "ts": time.time()}),
                                encoding="utf-8")
    except Exception:
        pass


def misplaced_title() -> str:
    import json as _json
    try:
        return _json.loads(_MISPLACED_F.read_text(encoding="utf-8")).get("title", "") if _MISPLACED_F.exists() else ""
    except Exception:
        return ""


def find_misplaced(query: str) -> str:
    """If his search touches the misplaced work's title, he has FOUND it — clear the state, return the title.
    Else ''. Called by the search_works hand so looking for it actually recovers it."""
    import json as _json
    try:
        if not _MISPLACED_F.exists():
            return ""
        title = _json.loads(_MISPLACED_F.read_text(encoding="utf-8")).get("title", "")
        qt = {w for w in re.findall(r"[a-z]{4,}", (query or "").lower())}
        tt = {w for w in re.findall(r"[a-z]{4,}", title.lower())}
        if title and qt and (qt & tt):
            _MISPLACED_F.unlink()
            return title
        return ""
    except Exception:
        return ""


# J-2925 (F-3603, P-0029): the "search my own works" hand used to read `sorted(glob("**/*.md"))[:500]` of data/Study,
# which on Windows path order is ESSAY_* then notes/<book>/ files -- 0 of ~870 WORK_ files were ever inside the slice.
# scan_works reads his OWN writing first (top-level WORK_, ESSAY_, TAB_ files), keeps the filed-away book-note folders
# (notes/) as a second pass that only runs when the first finds fewer than two passages, and caches file text by
# (mtime, size) so a call re-reads only what changed. A per-call cold-read budget bounds the first calls after start.
_TOP_PREFIXES = ("WORK_", "ESSAY_", "TAB_")
WORKS_READ_BUDGET = 300            # max files read from disk per call (cache hits are free); first calls fill the cache
_WORKS_CACHE: dict[str, tuple[int, int, str]] = {}   # path -> (mtime_ns, size, raw text); notes and top-level alike


def _scan_dir_files(root: Path, recurse: bool) -> list[tuple[Path, int, int]]:
    """(path, mtime_ns, size) for every .md under root. Best-effort: an unreadable entry is skipped."""
    import os
    out: list[tuple[Path, int, int]] = []
    stack = [str(root)]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if recurse:
                                stack.append(e.path)
                        elif e.name.lower().endswith(".md"):
                            st = e.stat()
                            out.append((Path(e.path), st.st_mtime_ns, st.st_size))
                    except OSError:
                        continue
        except OSError:
            continue
    return out


def _scan_pass(entries: list[tuple[Path, int, int]], terms: list[str], budget: list[int], base: Path,
               in_area) -> tuple[list, int]:
    """Score `entries` (already in priority order) against `terms`. Cached text is free; a file not yet cached (or
    changed) costs one unit of `budget[0]`, and once the budget is spent uncached files are skipped this call (a later
    call picks them up). Returns (hits as (score, snippet, relative path), files actually scored)."""
    hits: list = []
    scored = 0
    live = set()
    for path, mt, sz in entries:
        key = str(path)
        live.add(key)
        c = _WORKS_CACHE.get(key)
        if c is not None and c[0] == mt and c[1] == sz:
            raw = c[2]
        else:
            if budget[0] <= 0:
                continue
            budget[0] -= 1
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            _WORKS_CACHE[key] = (mt, sz, raw)
        scored += 1
        low = raw.lower()
        score = sum(low.count(t) for t in terms)
        if score:
            idx = min((low.find(t) for t in terms if t in low), default=-1)
            snip = " ".join(raw[max(0, idx - 80):idx + 170].split()) if idx >= 0 else ""
            try:
                rel = str(path.relative_to(base))
            except ValueError:
                rel = path.name
            # a query whose every term sits in the piece's own title line is a search BY title: it ranks first
            title = next((ln.lower() for ln in raw[:400].splitlines() if ln.strip()), "")
            tm = all(t in title for t in terms)
            hits.append((score, snip, rel, tm))
    # forget cached text for files of THIS pass's area that no longer exist (`in_area(key)` says which keys are ours)
    for k in [k for k in _WORKS_CACHE if k not in live and in_area(k)]:
        _WORKS_CACHE.pop(k, None)
    return hits, scored


def scan_works(terms: list[str], base: Path | None = None, read_budget: int | None = None,
               notes_if_fewer_than: int = 2) -> tuple[list, dict]:
    """Search his own writing for `terms`. Pass 1 = top-level WORK_/ESSAY_/TAB_ files (newest first within each
    prefix, prefixes in that order so ties favour a finished work over a note). Pass 2 = notes/<book>/ files, only
    when pass 1 found fewer than `notes_if_fewer_than` hits with a snippet. Returns (hits sorted by score desc as
    (score, snippet, relpath), stats)."""
    base = Path(base) if base is not None else STUDY_DIR
    budget = [WORKS_READ_BUDGET if read_budget is None else int(read_budget)]
    stats = {"top_files": 0, "top_scored": 0, "notes_files": 0, "notes_scored": 0, "notes_pass": False, "reads": 0}
    start_budget = budget[0]
    top_all = _scan_dir_files(base, recurse=False)
    stats["top_files"] = len(top_all)

    def _prio(e):
        n = e[0].name
        for i, pfx in enumerate(_TOP_PREFIXES):
            if n.startswith(pfx):
                return (i, n)
        return (len(_TOP_PREFIXES), n)
    # priority order: prefix rank ascending, name (timestamped) DESCENDING = newest first
    top_sorted = sorted(top_all, key=lambda e: _prio(e)[1], reverse=True)
    top_sorted.sort(key=lambda e: _prio(e)[0])
    hits, scored = _scan_pass(top_sorted, terms, budget, base, lambda k: Path(k).parent == base)
    stats["top_scored"] = scored
    if sum(1 for h in hits if h[1]) < notes_if_fewer_than:
        notes_root = base / "notes"
        if notes_root.is_dir():
            notes = sorted(_scan_dir_files(notes_root, recurse=True), key=lambda e: str(e[0]))
            stats["notes_files"] = len(notes)
            nh, ns = _scan_pass(notes, terms, budget, base, lambda k: Path(k).is_relative_to(notes_root))
            stats["notes_scored"] = ns
            stats["notes_pass"] = True
            hits.extend(nh)
    # stable sort: a title match first, then score; ties keep priority order (works, essays, tabs, book notes)
    hits.sort(key=lambda h: (h[3], h[0]), reverse=True)
    hits = [h[:3] for h in hits]
    stats["reads"] = start_budget - budget[0]
    return hits, stats


def archive_book_note_files(book_title: str, dry_run: bool = False) -> dict:
    """Phase 2 (2026-06-23): once a book is capstoned, move its raw NOTE files (TAB_*) into
    data/Study/notes/<book_slug>/, leaving the ESSAY_* file on top. A note belongs to the book if its
    frontmatter '· on: <book>' genuinely cites it (see `_cites_this_book` — F-1309, 2026-09-13: a plain
    single-word substring test used to false-positive on any unrelated citation sharing one generic
    bibliographic word, e.g. 'edition'; fixed to require the book's WHOLE distinctive-word signature).
    Best-effort, reversible (move back). dry_run=True lists what WOULD move without touching anything.
    Returns a summary."""
    res = {"book": book_title[:60], "moved": 0, "filed_db": 0, "dest": "", "files": []}
    try:
        from core.essay_lesson import _key, _cites_this_book
        key = (_key(book_title) or "").lower()   # kept for bookkeeping/fallback only — see _cites_this_book
        if not key:
            return res
        slug = re.sub(r"[^\w\- ]", "", book_title)[:48].strip().replace(" ", "_") or "book"
        dest = NOTES_SUBDIR / slug
        res["dest"] = str(dest)
        titles: list[str] = []
        for p in STUDY_DIR.glob("TAB_*.md"):   # ESSAY_* are excluded by the glob — they stay on top
            try:
                head = p.read_text(encoding="utf-8", errors="ignore")[:400]
                m = re.search(r"on:\s*(.+?)\*", head)
                on = (m.group(1).strip().lower() if m else "")
                if not (on and _cites_this_book(book_title, on)):
                    continue
                tm = re.search(r"#\s*(.+)", head)
                if tm:
                    titles.append(tm.group(1).strip())
                res["files"].append(p.name)
                if not dry_run:
                    dest.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(p), str(dest / p.name))
                res["moved"] += 1
            except Exception:
                continue
        # Demote those notes' DB study fragments out of ordinary recall too (behind the book's essay gist).
        # Their content carries the NOTE title, not the book, so match by title — world_consolidation's
        # content-LIKE filer can't reach them. Reversible (clear chapter_id). Skipped in dry-run.
        if titles and not dry_run:
            try:
                from core.memory.store import _connect
                # J-1924 / F-2549 (b) (2026-10-07, restart-gated): the chapter_id UPDATE below can now overlap the
                # worker-thread world_consolidation.sweep (J-1917 moved it off the loop) on the same column; hold the
                # same _FILE_LOCK that serialises file_book_notes. Around the DB block only (never the file moves above).
                # Fail-open: if world_consolidation can't be imported, run unlocked exactly as before.
                try:
                    from core.world_consolidation import _FILE_LOCK as _fl
                except Exception:
                    import contextlib
                    _fl = contextlib.nullcontext()
                with _fl:
                    with _connect() as conn:
                        # F-1309 fix applies here too: don't trust the first single-key LIKE hit blindly —
                        # fetch a small recent window and prefer the first one _cites_this_book actually
                        # confirms; fall back to the old top-1 behaviour if none do (never worse than before).
                        cands = conn.execute(
                            "SELECT fragment_id, content FROM memory_fragments WHERE origin='essay' "
                            "AND content LIKE ? ORDER BY timestamp DESC LIMIT 5",
                            (f"%{_key(book_title)}%",)).fetchall()
                        g = next((c for c in cands if _cites_this_book(book_title, (c["content"] or "").lower())),
                                 (cands[0] if cands else None))
                        if g:
                            for t in titles:
                                cur = conn.execute(
                                    "UPDATE memory_fragments SET chapter_id=? WHERE origin='study' "
                                    "AND content LIKE ? AND chapter_id IS NULL",
                                    (g["fragment_id"], f"%study note: '{t}'%"))
                                res["filed_db"] += cur.rowcount
                            conn.commit()
            except Exception:
                pass
    except Exception:
        pass
    return res


def shelf() -> list[str]:
    """Titles of his existing tablets (newest first) — so he can know his own body of work."""
    try:
        return [p.stem.split("_", 3)[-1].replace("_", " ")
                for p in sorted(STUDY_DIR.glob("TAB_*.md"), reverse=True)]
    except Exception:
        return []

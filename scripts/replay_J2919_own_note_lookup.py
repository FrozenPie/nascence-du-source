"""J-2919 (P-0072, F-3589): read-only replay of the "which fragments are THIS book's own notes" lookup.

OLD = what master did before J-2919: study_note's `content LIKE %<essay_lesson._key(book)>%` (the restate_sim lookup,
and the matcher _own_note_fragment_ids used before D-0592) and the squashed-16-letter-prefix same-book exclusion.
NEW = study_note._own_note_fragment_ids / _is_own_note (book tag or note-file frontmatter, whole-signature test).

GROUND TRUTH (independent of both): the "on: <book>" line of the TAB note file a fragment's source_id points to,
compared with the book title after lowercasing and squashing to letters+digits, truncation-aware only by
prefix-at-50. Calls = one per TAB file (what the finding counted: 763 files / 104 books).

Read-only: opens the DB with mode=ro&immutable=1, writes nothing but --out (default: stdout).
Run:  python scripts/replay_J2919_own_note_lookup.py [--db PATH] [--out summary.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env, per project rule)
from core import study_note as sn  # noqa: E402
from core.essay_lesson import _key  # noqa: E402

DEFAULT_DB = r"C:\Nascence\data\memory\nascence.db"
_ON = re.compile(r"on:\s*(.+?)(?:\s\u00b7\s|\*)")


def _squash(s: str) -> str:
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def _truth_book(source_id: str) -> str:
    try:
        p = Path(str(source_id or ""))
        if not p.is_file():
            return ""
        m = _ON.search(p.read_text(encoding="utf-8", errors="ignore")[:500])
        return m.group(1).strip() if m else ""
    except Exception:
        return ""


def _same(a: str, b: str) -> bool:
    x, y = _squash(a)[:50], _squash(b)[:50]
    return bool(x) and x == y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    uri = "file:" + Path(args.db).as_posix() + "?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT fragment_id, content, source_id, origin, timestamp FROM memory_fragments "
                        "WHERE origin='study' ORDER BY timestamp DESC").fetchall()
    # truth per fragment (only those with a readable note file)
    truth: dict[str, str] = {}
    for r in rows:
        b = _truth_book(r["source_id"])
        if b:
            truth[r["fragment_id"]] = b
    books: dict[str, list[str]] = {}          # truth book -> its fragment ids
    for fid, b in truth.items():
        books.setdefault(b, []).append(fid)
    calls = sum(len(v) for v in books.values())

    stat = dict(books=len(books), calls=calls, old_lt50=0, new_lt50=0, old_zero=0, new_zero=0,
                old_restate_wrong=0, new_restate_wrong=0, old_restate_none=0, new_restate_none=0,
                new_empty_ids=0)
    worst = []
    for book, fids in books.items():
        key = (_key(book) or "")
        # OLD matcher, LIMIT 40 as the finding replayed it
        old_ids = [r["fragment_id"] for r in conn.execute(
            "SELECT fragment_id FROM memory_fragments WHERE origin='study' AND content LIKE ? "
            "ORDER BY timestamp DESC LIMIT 40", (f"%{key}%",)).fetchall()] if key else []
        new_ids = sn._own_note_fragment_ids(book, conn, limit=40)
        def real(ids):
            return sum(1 for i in ids if i in truth and _same(truth[i], book))
        def known(ids):
            return sum(1 for i in ids if i in truth)   # ids whose note FILE still exists (only those can be judged)
        ro, rn = real(old_ids), real(new_ids)
        ko, kn = known(old_ids), known(new_ids)
        # share of the JUDGEABLE ids that are really this book's (an id with no surviving note file is skipped,
        # not counted wrong); no judgeable id at all -> the call is not scored either way
        share_o = ro / ko if ko else 1.0
        share_n = rn / kn if kn else 1.0
        n_calls = len(fids)
        if share_o < 0.5:
            stat["old_lt50"] += n_calls
        if share_n < 0.5:
            stat["new_lt50"] += n_calls
        if ro == 0 and ko:
            stat["old_zero"] += n_calls
        if rn == 0 and kn:
            stat["new_zero"] += n_calls
        if not new_ids:
            stat["new_empty_ids"] += n_calls
        if share_o < 0.5:
            worst.append((book, key, len(old_ids), ro, len(new_ids), rn))
        # restate_sim lookup: the newest OTHER study fragment found, is it really this book's? One lookup per book
        # (excluding the book's newest note), counted once per call of that book (replaying it per call is the
        # same answer 763 times over and ~100x slower).
        fid = fids[0]
        orow = conn.execute("SELECT fragment_id FROM memory_fragments WHERE origin='study' AND content LIKE ? "
                            "AND fragment_id != ? ORDER BY timestamp DESC LIMIT 1", (f"%{key}%", fid)).fetchone() if key else None
        nids = sn._own_note_fragment_ids(book, conn, exclude_id=fid, limit=1)
        if orow is None:
            stat["old_restate_none"] += n_calls
        elif not (orow["fragment_id"] in truth and _same(truth[orow["fragment_id"]], book)):
            stat["old_restate_wrong"] += n_calls
        if not nids:
            stat["new_restate_none"] += n_calls
        elif not (nids[0] in truth and _same(truth[nids[0]], book)):
            stat["new_restate_wrong"] += n_calls

    # same-book EXCLUSION over the 800 newest study+essay rows (what _scored_scan_related scans)
    scan = conn.execute("SELECT fragment_id, content, source_id FROM memory_fragments WHERE origin IN ('study','essay') "
                        "AND embedding IS NOT NULL ORDER BY timestamp DESC LIMIT 800").fetchall()
    ex = dict(own_rows=0, other_rows=0, old_own_excluded=0, new_own_excluded=0, old_other_excluded=0,
              new_other_excluded=0, new_unknown=0, other_only_new_excl=0, other_only_old_excl=0)
    for book in books:
        key16 = _squash(book)[:16]
        budget = [sn._FILE_READ_CAP]
        for r in scan:
            if r["fragment_id"] not in truth:
                continue
            is_own = _same(truth[r["fragment_id"]], book)
            old_ex = bool(key16 and key16 in _squash((r["content"] or "").lower())[:400])
            v = sn._is_own_note(book, r["content"] or "", r["source_id"], budget)
            if v is None:
                ex["new_unknown"] += 1
                new_ex = old_ex
            else:
                new_ex = bool(v)
            if is_own:
                ex["own_rows"] += 1
                ex["old_own_excluded"] += old_ex
                ex["new_own_excluded"] += new_ex
            else:
                ex["other_rows"] += 1
                ex["old_other_excluded"] += old_ex
                ex["new_other_excluded"] += new_ex
                ex["other_only_new_excl"] += int(new_ex and not old_ex)   # newly lost to a call (could add an empty related_text)
                ex["other_only_old_excl"] += int(old_ex and not new_ex)   # newly offered (an old wrong exclusion lifted)
    out = dict(lookup=stat, exclusion=ex, worst_old=sorted(worst, key=lambda x: x[3])[:15])
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

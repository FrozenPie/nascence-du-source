"""Backfill consolidating capstone essays for finished-but-un-essayed books (Phase 3, 2026-06-23).

The live path (essay_lesson.pending_book) is self-gated to NEW finishes, so the pre-existing backlog of
finished books is left for this deliberate, observable pass.

Usage:
  python scripts/backfill_essays.py --dry-run     # PLAN only: per-book note/file counts, no writes, no LLM
  python scripts/backfill_essays.py --limit 1     # actually essay + file + move just ONE book (the test run)
  python scripts/backfill_essays.py               # process the whole backlog

Each real (non-dry) book: gather ALL its notes -> map-reduced capstone essay -> Emissary grades it ->
record() files its notes out of recall AND moves their note files into data/Study/notes/<book>/.
"""
import argparse
import asyncio
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import essay_lesson, study
from core.model_client import call_node_json
from core.schema import SERVE_CHAINS

BASE = SERVE_CHAINS["hot"]


def _count(notes: str) -> int:
    return (notes.count("\n- ") + 1) if notes else 0


async def _one(book: str, title: str, dry: bool) -> dict:
    notes, ids = essay_lesson.gather_notes(title, book)
    movem = study.archive_book_note_files(title, dry_run=True)
    n, chars, files = _count(notes), len(notes), movem["moved"]
    head = f"  {title[:36]:36} notes={n:3} chars={chars:6,} files={files:3}"
    if n == 0 or chars < essay_lesson._MIN_NOTES:
        print(head + "  [SKIP: too few notes — marking done]")
        if not dry:
            essay_lesson.mark_done(book)
        return {"book": title, "essayed": False}
    if dry:
        mr = " map-reduce" if chars > essay_lesson._REDUCE_THRESHOLD else ""
        print(head + f"  [DRY -> 1 essay,{mr or ' 1-pass'}; would file+move {files} files]")
        return {"book": title, "essayed": False}
    essay = await essay_lesson.compose(call_node_json, BASE, title, notes)
    if not essay or len(essay) < 120:
        print(head + "  [essay failed/short — left pending]")
        return {"book": title, "essayed": False}
    pred = await essay_lesson.self_predict(call_node_json, BASE, title, essay)
    meas, fb = await essay_lesson.grade(title, notes, essay)
    essay_lesson.record(book, title, essay_lesson.essay_title_from(title, essay), essay,
                        pred, meas, fb, source_ids=ids)
    print(head + f"  -> ESSAY {len(essay)}c (felt {'unrated' if pred is None else format(pred, '.2f')}/real "
                 f"{'ungraded' if meas is None else format(meas, '.2f')}) filed+moved")
    return {"book": title, "essayed": True}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="plan only; no writes, no LLM")
    ap.add_argument("--limit", type=int, default=0, help="process only the first N books (a test run)")
    a = ap.parse_args()
    if not a.dry_run:
        # J-1812 / F-2428: a deliberate founder-run real-write tool (essay_lesson.record -> competence.record_drill_accuracy
        # writes data/capability_beliefs.json on purpose); competence.py's writers are now behind the D-0179 fence, so
        # declare this process live (the seed_memory.py / debate_harness.py precedent). Dry-run writes nothing.
        from core import profile
        profile.mark_live()

    backlog = essay_lesson.finished_unessayed_books()
    mode = "DRY-RUN (no writes, no LLM)" if a.dry_run else "LIVE (writes essays, files + moves notes)"
    print(f"Essay backfill — {len(backlog)} finished, un-essayed books — {mode}\n")
    if a.limit:
        backlog = backlog[:a.limit]
        print(f"  (limited to first {len(backlog)})\n")

    done = 0
    for book, title in backlog:
        try:
            r = await _one(book, title, a.dry_run)
            done += 1 if r.get("essayed") else 0
        except Exception as exc:
            print(f"  {title[:36]:36} ERROR: {str(exc)[:80]}")

    print(f"\nDone. {'(dry-run — nothing written)' if a.dry_run else f'{done} essays written, notes filed + moved.'}")


if __name__ == "__main__":
    asyncio.run(main())

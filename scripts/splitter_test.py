"""
Test the book splitter on every book on the shelf — verify sensible chapters + NO double-counts
(the Commutation Chophouse bug). Read-only.
"""
import sys, glob, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from core.book_splitter import split_chapters, _norm

for f in sorted(glob.glob(r"data/books/*.txt")):
    name = f.replace("\\", "/").split("/")[-1].replace(".txt", "")
    text = open(f, encoding="utf-8", errors="ignore").read()
    ch = split_chapters(text)
    kinds = {c["kind"] for c in ch}
    # double-count check: any normalised title appearing >1×?
    norms = [_norm(c["title"]) for c in ch]
    dups = {t for t in norms if norms.count(t) > 1 and t}
    # length sanity
    lens = [c["end"] - c["start"] for c in ch]
    tiny = sum(1 for L in lens if L < 800)
    print(f"\n{name[:44]}  → {len(ch)} chapters ({'/'.join(kinds)})")
    print(f"   first: {ch[0]['title'][:48]!r}")
    if len(ch) > 1:
        print(f"   2nd  : {ch[1]['title'][:48]!r}")
        print(f"   last : {ch[-1]['title'][:48]!r}")
    print(f"   median chapter ≈ {sorted(lens)[len(lens)//2]:,}c | tiny(<800c): {tiny} | "
          f"{'⚠ DOUBLE-COUNT: '+', '.join(list(dups)[:3]) if dups else '✓ no repeated titles'}")

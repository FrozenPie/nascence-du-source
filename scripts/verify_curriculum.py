"""
Verify the 40-book grounding curriculum resolves in Du's local catalogue (read-only, no downloads).
Mirrors library_hand._search: substring match on title/author, English only, by popularity. Reports the
best match + author + downloads so we can confirm it's the RIGHT book, not a coincidental substring.
"""
import sys, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

META = Path(r"C:\Knowledge\SPGC-metadata-2018-07-18.csv")
print("catalogue exists:", META.exists())
if not META.exists():
    sys.exit("CATALOGUE MISSING — the library cannot search; curriculum cannot load.")

rows = list(csv.DictReader(open(META, encoding="utf-8", errors="ignore")))
en = [r for r in rows if "'en'" in (r.get("language") or "")]
print(f"catalogue rows: {len(rows)} ({len(en)} English)\n")

# (search_phrase, expected author-surname for confirmation)
CURRIC = [
    ("boy scouts handbook", "scouts"), ("the american boy's handy book", "beard"),
    ("camping and woodcraft", "kephart"), ("knots, splices", "verrill"),
    ("woodcraft", "sears"), ("the boy mechanic", "popular"),
    ("the voyage of the beagle", "darwin"), ("the origin of species", "darwin"),
    ("the natural history of selborne", "white"), ("the life of the spider", "fabre"),
    ("the life of the fly", "fabre"), ("wild animals i have known", "seton"),
    ("the burgess animal book", "burgess"),
    ("the chemical history of a candle", "faraday"), ("the forms of water", "tyndall"),
    ("heat: a mode of motion", "tyndall"), ("the story of the heavens", "ball"),
    ("astronomy with an opera-glass", "serviss"), ("the outline of science", "thomson"),
    ("pioneers of science", "lodge"),
    ("life on the mississippi", "twain"), ("roughing it", "twain"),
    ("two years before the mast", "dana"), ("travels with a donkey", "stevenson"),
    ("the oregon trail", "parkman"), ("sailing alone around the world", "slocum"),
    ("the worst journey in the world", "cherry"),
    ("geological sketches", "agassiz"), ("the sea-beach at ebb-tide", "arnold"),
    ("ponds and streams", "morgan"), ("a field book of the stars", "olcott"),
    ("the romance of modern geology", "grew"),
    ("three acres and liberty", "hall"), ("manual of gardening", "bailey"),
    ("the boston cooking-school cook book", "farmer"), ("handwork in wood", "noyes"),
    ("the boy craftsman", "hall"),
    ("the autobiography of benjamin franklin", "franklin"), ("up from slavery", "washington"),
    ("lay sermons", "huxley"),
]


def search(q):
    t = q.lower().strip()
    hits = [r for r in en if t in (r["title"] or "").lower() or t in (r["author"] or "").lower()]
    hits.sort(key=lambda r: -int(r["downloads"] or 0))
    return hits


ok = miss = wrongauthor = 0
need_tweak = []
for phrase, surname in CURRIC:
    hits = search(phrase)
    if not hits and len(phrase.split()) > 2:           # the 2-word head retry library_hand does
        hits = search(" ".join(phrase.split()[:2]))
    if not hits:
        miss += 1; need_tweak.append((phrase, "no match"))
        print(f"  ✗ NO MATCH   {phrase}")
        continue
    r = hits[0]
    author_ok = surname in (r["author"] or "").lower()
    tag = "✓" if author_ok else "≈"
    if author_ok: ok += 1
    else: wrongauthor += 1; need_tweak.append((phrase, f"top match is '{r['title'][:40]}' by {r['author']}"))
    print(f"  {tag} {phrase[:34]:<34} -> '{(r['title'] or '')[:42]}' / {(r['author'] or '?')[:22]} (dl {r['downloads']})")

print(f"\nRESOLVED with right author: {ok}/40   | author-mismatch: {wrongauthor}   | no match: {miss}")
if need_tweak:
    print("\nNeed a tweaked search title:")
    for p, why in need_tweak:
        print(f"   - {p}: {why}")

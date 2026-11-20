"""
Load the 40-book grounding curriculum into school. Verifies every title resolves in the catalogue
FIRST (abort if any miss — don't load a broken list), then set_curriculum (which fetches book #1,
Boy Scouts Handbook, and sets it current — he comes off Mississippi at once). The rest fetch as he
reaches them. Run once.
"""
import sys, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

CURRICULUM = [
    "boy scouts handbook", "the book of camp-lore and woodcraft", "two little savages",
    "knots, splices and rope work", "woodcraft", "the boy mechanic",
    "the voyage of the beagle", "the origin of species", "the natural history of selborne",
    "the life of the spider", "the life of the fly", "wild animals i have known",
    "the burgess animal book",
    "the chemical history of a candle", "fragments of science", "soap-bubbles",
    "the story of the heavens", "astronomy with an opera-glass", "the outline of science",
    "pioneers of science",
    "life on the mississippi", "roughing it", "two years before the mast",
    "travels with a donkey", "the oregon trail", "sailing alone around the world",
    "the worst journey in the world",
    "seaside studies in natural history", "the sea-beach at ebb-tide", "ways of nature",
    "a field book of the stars", "charles lyell and modern geology",
    "three acres and liberty", "manual of gardening", "the italian cook book",
    "handwork in wood", "the boy craftsman",
    "the autobiography of benjamin franklin", "up from slavery", "lay sermons",
]

rows = list(csv.DictReader(open(r"C:\Knowledge\SPGC-metadata-2018-07-18.csv", encoding="utf-8", errors="ignore")))
en = [r for r in rows if "'en'" in (r.get("language") or "")]
def resolves(q):
    t = q.lower().strip()
    h = [r for r in en if t in (r["title"] or "").lower() or t in (r["author"] or "").lower()]
    if not h and len(t.split()) > 2:
        t2 = " ".join(t.split()[:2]); h = [r for r in en if t2 in (r["title"] or "").lower()]
    h.sort(key=lambda r: -int(r["downloads"] or 0))
    return h[0] if h else None

print(f"verifying {len(CURRICULUM)} titles resolve...")
missing = [c for c in CURRICULUM if not resolves(c)]
if missing:
    print("ABORT — these do not resolve:", missing); sys.exit(1)
print("  all 40 resolve ✓\n")

from core import school
print("loading curriculum (fetches book #1, Boy Scouts Handbook)...")
got = school.set_curriculum(CURRICULUM)
if not got:
    print("✗ set_curriculum failed (fetch of book #1 returned None — network or cooldown?)"); sys.exit(1)
print(f"  book #1 fetched + set current: '{got[0]}'")

d = school.status()
print("\nschool.json now:")
print("  curriculum length:", len(d.get("curriculum", [])))
print("  current index    :", d.get("curriculum_idx"))
print("  assigned (current):", d.get("assigned_title"))
print("  status           :", school.curriculum_status())

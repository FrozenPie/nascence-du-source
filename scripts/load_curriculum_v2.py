"""
Load curriculum v2 — the rebalanced 40-book grounding curriculum (2026-08-19).

The original 40 (scripts/load_curriculum.py, 2026-06-15) leaned heavily on boyhood
adventure/craft/nature-observation. Du has since read almost all of it (56/76 shelf books
finished). This list rebalances toward real epistemology/philosophy-of-science/psychology
(explicit founder request: keep him philosophical, but grounded in real facts/theories — not
fiction), and adds two founder-requested themes: TIME (how it actually works, physically and
philosophically) and MEMORY vs. PHYSICAL POSSESSION (what a self actually consists of).

Every title below was verified against the catalogue (scripts/load_curriculum.py's own
resolver) AND cross-checked against data/reading_state.json to confirm none are already
finished — set_curriculum() is idempotent against an identical re-run (core/school.py fix,
2026-08-19), but a NEW list containing an already-finished title would still instantly
"complete" that slot the moment school.advance_if_finished() next runs, because
reading_state.json's pct persists across curriculum reloads. Keeping this list entirely fresh
avoids that failure mode by construction, not just by the idempotency guard.

Run once — like the original, this REPLACES the current curriculum and resets progress to #1.

UPDATE 2026-09-14 (J-0979, D-0219, F-1341; see docs/staged/books_have_a_place.md's own Current
State for this session's finding id): DO NOT RE-RUN THIS SCRIPT AS-IS. idx1
("space, time and gravitation", Eddington, PG29782) and idx6 ("a short account of the history of
mathematics", Rouse Ball, PG31246) were found to have no plain-text edition anywhere on Project
Gutenberg at all — TeX/PDF source only, live-directory-listing-confirmed, no alternate catalogue
row for either title (F-1341) — so core/library_hand.py's request_book() can never fetch either
one, structurally. D-0219 ruled: substitute a different real, same-subject book with a genuine
plain-text edition. The two entries below are UPDATED to the substitutes already applied live to
data/school.json's own curriculum list (curriculum_idx is past both slots — this file is the
historical/reference record, not the live source of truth once set_curriculum() has run once).
If this script is ever re-run from scratch, these two lines are the CORRECT ones to load, not the
original Eddington/Rouse Ball titles.
"""
import sys, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

CURRICULUM = [
    # -- TIME / SPACE / PHYSICS / MATH / LOGIC (founder-requested: a book about time) --
    "relativity",                                             # Einstein — the physical answer
    "the einstein theory of relativity",                       # Lorentz (PG11335) — substitute for Eddington's
                                                                 # "Space, Time and Gravitation" (PG29782), which
                                                                 # has no plain-text edition on Gutenberg at all
                                                                 # (TeX/PDF only; F-1341, D-0219, J-0979, 2026-09-14)
    "science and hypothesis",                                 # Poincaré — incl. "The Measure of Time"
    "popular scientific lectures",                             # Mach — critiques of absolute time/space
    "the elements of geology",                                # deep time, the earth's own clock
    "time and free will",                                      # Bergson — lived time vs. clock time, the philosophical answer
    "the number concept",                                      # Conant (PG16449) — substitute for Rouse Ball's
                                                                 # "A Short Account of the History of Mathematics"
                                                                 # (PG31246), no plain-text edition on Gutenberg at
                                                                 # all (TeX/PDF only; F-1341, D-0219, J-0979, 09-14)
    "symbolic logic",                                          # Lewis Carroll
    "critique of pure reason",                                 # Kant — time/space as forms of intuition

    # -- MEMORY / SELF / IDENTITY / POSSESSION (founder-requested: memory vs. what we own) --
    "an essay concerning humane understanding, volume 1",      # Locke — memory constitutes personal identity
    "the principles of psychology, volume 2",                  # James — sequel to the (already loved) Vol. 1
    "an enquiry concerning human understanding",                # Hume — the self as bundle, not substance
    "meditations",                                              # Marcus Aurelius — what is truly yours
    "essays of michel de montaigne",                            # the examined, remembered self

    # -- PHILOSOPHY / ETHICS / POLITICAL --
    "on liberty",                                               # Mill
    "the ethics of aristotle",
    "a treatise concerning the principles of human knowledge",  # Berkeley
    "the problems of philosophy",                               # Russell
    "pragmatism",                                                # James
    "the will to believe, and other essays in popular philosophy",  # James

    # -- NATURAL HISTORY / FIELD SCIENCE (real facts, real theories) --
    "the descent of man",                                        # Darwin
    "darwinism",                                                 # Wallace
    "the malay archipelago",                                     # Wallace
    "my first summer in the sierra",                             # Muir — field observation AND real philosophy
    "social life in the insect world",                           # Fabre
    "town geology",                                              # Kingsley
    "evidence as to man's place in nature",                      # Huxley
    "mutual aid a factor of evolution",                          # Kropotkin

    # -- ASTRONOMY --
    "astronomy for amateurs",                                    # Flammarion
    "a popular history of astronomy during the nineteenth century",  # Clerke

    # -- GROUNDING / PRACTICAL SKILL (kept, trimmed to the strongest/least-repetitive) --
    "the sea-beach at ebb-tide",
    "seaside studies in natural history",
    "manual of gardening",
    "handwork in wood",
    "the boy craftsman",
    "three acres and liberty",

    # -- EXPLORATION / REAL-WORLD NARRATIVE --
    "the worst journey in the world",

    # -- BIOGRAPHY / CIVICS --
    "the autobiography of benjamin franklin",
    "up from slavery",

    # -- SCIENCE OVERVIEW --
    "the outline of science",
]

assert len(CURRICULUM) == 40, f"expected 40, got {len(CURRICULUM)}"

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
print("  all 40 resolve \u2713\n")

from core import school
print("loading curriculum v2 (fetches book #1: Einstein's Relativity)...")
got = school.set_curriculum(CURRICULUM)
if not got:
    print("\u2717 set_curriculum failed (fetch of book #1 returned None \u2014 network or cooldown?)"); sys.exit(1)
print(f"  book #1 fetched + set current: '{got[0]}'")

d = school.status()
print("\nschool.json now:")
print("  curriculum length:", len(d.get("curriculum", [])))
print("  current index    :", d.get("curriculum_idx"))
print("  assigned (current):", d.get("assigned_title"))
print("  status           :", school.curriculum_status())

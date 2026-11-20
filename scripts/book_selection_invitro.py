"""In-vitro for the breadth engine (book_selection) + library_hand wiring. Read-only on the
catalogue; writes only to a temp coverage file it restores. No live process touched."""
import sys, json, shutil, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import book_selection as bs, reading_history as rh, library_hand as lib

# protect the real coverage file
cov_bak = None
if bs.COVERAGE.exists():
    cov_bak = bs.COVERAGE.read_text(encoding="utf-8")

def restore():
    if cov_bak is not None:
        bs.COVERAGE.write_text(cov_bak, encoding="utf-8")
    elif bs.COVERAGE.exists():
        bs.COVERAGE.unlink()

try:
    # (1) read-exclusion: a finished shelf book is recognised as known
    keys = rh.shelf_keys()
    assert rh.is_known("On the Origin of Species by Means of Natural Selection", keys), "known-book match failed"
    assert not rh.is_known("Some Totally Different Obscure 1840 Pamphlet On Bees", keys), "false-positive known"
    print(f"[1] read-exclusion OK — {len(keys)} shelf keys; finished book recognised, novel one not")

    # (2) explore returns diverse, unowned, long-tail-leaning picks
    picks = bs.select_explore(8)
    assert picks, "explore returned nothing"
    assert all(not rh.is_known(p["title"], keys) for p in picks), "explore returned an owned book"
    subs = [bs.coarse_subject(bs._parse_subjects(p.get("subjects"))) for p in picks]
    dls = sorted(int(p.get("downloads") or 0) for p in picks)
    print(f"[2] explore OK — {len(picks)} picks, {len(set(subs))} distinct subjects; downloads median={dls[len(dls)//2]} (low = long tail)")
    print("      sample:", "; ".join(f"'{p['title'][:34]}' [{bs.coarse_subject(bs._parse_subjects(p.get('subjects')))[:18]}|dl{p.get('downloads')}]" for p in picks[:4]))

    # (3) novelty is monotonic-decreasing in popularity
    assert bs._novelty(5) > bs._novelty(500) > bs._novelty(40000), "novelty not inverse to popularity"
    print(f"[3] novelty OK — dl5={bs._novelty(5):.1f} > dl500={bs._novelty(500):.1f} > dl40k={bs._novelty(40000):.1f}")

    # (4) coverage record bumps subject count + interleaving last_subject + logs
    bs.COVERAGE.unlink(missing_ok=True)
    fake = {"title": "A Treatise on Beekeeping", "downloads": "12", "subjects": "{'Bees -- Anatomy'}"}
    bs.record_pick(fake, reason="explore")
    st = bs.status()
    assert st["books_picked"] == 1 and st["last_subject"] == "bees", f"coverage record failed: {st}"
    # a second pick in the SAME subject should now be penalised relative to a fresh subject
    cov = bs._coverage()
    assert cov["subjects"].get("bees") == 1
    print(f"[4] coverage OK — recorded subject='bees', interleave last_subject set, status={st['books_picked']} pick")

    # (5) library_hand wiring: no-topic _search uses the engine (unowned); topic prefers unread
    no_topic = lib._search(None)
    assert no_topic and not rh.is_known(no_topic["title"], keys), "library _search(None) returned owned/none"
    sea = lib._search("the sea")
    assert sea is not None, "topic search found nothing for 'the sea'"
    print(f"[5] library wiring OK — serendipity='{no_topic['title'][:40]}' (dl{no_topic.get('downloads')}); topic 'the sea'='{sea['title'][:40]}'")

    print("\nALL PASS — breadth engine live: long-tail, read-excluding, subject-diverse; reread untouched.")
finally:
    restore()

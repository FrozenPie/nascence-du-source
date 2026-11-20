"""J-2865 (F-3539, P-0080): librarian hygiene. Offline: subjects_for and search_by_subjects are stubbed,
_LOG points at a temp dir, no model call, no live data, no catalogue read.
    python scripts/_test_J-2865_librarian_hygiene.py
"""
import sys, asyncio, json, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import librarian, library_hand  # core BEFORE lab_env

tmp = Path(tempfile.mkdtemp(prefix="j2865_"))
librarian._LOG = tmp / "librarian_log.jsonl"
assert not str(librarian._LOG).startswith(str(ROOT / "data")), "log must be a temp path"

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

# 1. normalise_headings
nh = librarian.normalise_headings
check("subdivision cut to first segment", nh(["History - Europe - Napoleonic Wars"]) == ["History"])
check("en/em dash subdivisions", nh(["Art \u2013 Italy", "Music \u2014 Opera"]) == ["Art", "Music"])
check("underscore read as space", nh(["natural_history"]) == ["natural history"])
check("hyphenated word untouched", nh(["Anglo-Saxon", "Self-knowledge"]) == ["Anglo-Saxon", "Self-knowledge"])
check("dedup case-insensitive, order kept", nh(["Ethics - Modern", "ethics", "Liberty"]) == ["Ethics", "Liberty"])
check("junk dropped", nh(["", "  ", "ab", 5, None]) == [])
check("plain LCSH unchanged", nh(["Conduct of life", "Ethics"]) == ["Conduct of life", "Ethics"])

# 2. ask(): stubs
calls = []
def run(subjects, table, flag=False):
    async def fake_subjects(q): return subjects
    def fake_search(subs, k=12, rank="downloads"):
        calls.append(list(subs))
        return table.get(tuple(subs), [])
    shown = []
    o = (librarian.subjects_for, library_hand.search_by_subjects, library_hand.present_page, librarian.ZERO_HIT_FALLTHROUGH)
    librarian.subjects_for, library_hand.search_by_subjects = fake_subjects, fake_search
    library_hand.present_page = lambda rows: shown.append(rows)
    librarian.ZERO_HIT_FALLTHROUGH = flag
    calls.clear()
    try:
        return asyncio.run(librarian.ask("his continental system truly fractured europe")), list(calls), shown
    finally:
        librarian.subjects_for, library_hand.search_by_subjects, library_hand.present_page, librarian.ZERO_HIT_FALLTHROUGH = o

book = {"title": "The Napoleonic Wars", "author": "Someone", "subjects": "History", "downloads": 5}

# direct hit: no retry, no subjects_used
out, c, shown = run(["Ethics", "Liberty"], {("Ethics", "Liberty"): [book]})
check("direct hit: one search only", len(c) == 1)
check("direct hit: page presented and text lists the book", len(shown) == 1 and "The Napoleonic Wars" in out)

# zero hit, normalisation rescues
out, c, shown = run(["History - Europe - Napoleonic Wars", "Political Economy - Protectionism"],
                    {("History", "Political Economy"): [book]})
check("rescue: second search uses first segments", c == [["History - Europe - Napoleonic Wars", "Political Economy - Protectionism"], ["History", "Political Economy"]])
check("rescue: page shown", len(shown) == 1 and "The Napoleonic Wars" in out)
last = json.loads(open(librarian._LOG, encoding="utf-8").read().strip().splitlines()[-1])
check("rescue: log records subjects_used and n_hits", last["subjects_used"] == ["History", "Political Economy"] and last["n_hits"] == 1)
check("status counts norm_rescued", librarian.status().get("norm_rescued") == 1)

# zero hit, nothing helps, flag off: true wording, still a perception line
out, c, shown = run(["Environmental ethics", "Sustainability"], {})
check("no retry when normalising changes nothing", len(c) == 1)
check("zero hit: non-None line", isinstance(out, str))
check("zero hit: untrue claim gone", "empty-handed" not in out and "nothing in the stacks" not in out)
check("zero hit: says no shelf for that wording", "could not find a shelf for that wording" in out)
check("zero hit: no page presented", shown == [])
last = json.loads(open(librarian._LOG, encoding="utf-8").read().strip().splitlines()[-1])
check("zero hit log: subjects_used null", last["subjects_used"] is None and last["n_hits"] == 0)

# zero hit, flag on: None so the topic path runs
out, c, shown = run(["Environmental ethics"], {}, flag=True)
check("flag on: zero hit returns None", out is None)
check("flag default is OFF", librarian.ZERO_HIT_FALLTHROUGH is False)

# no headings at all (hubs down)
out, c, shown = run([], {})
check("no headings: no search, honest line", c == [] and isinstance(out, str) and "empty-handed" not in out)

# 3. stale wording gone from the module
src = (ROOT / "core" / "librarian.py").read_text(encoding="utf-8")
check("no 'llama-first'/'qwen fallback' wording left", "llama-first" not in src and "qwen fallback" not in src and "llama first" not in src)
check("subjects_for docstring names the real hubs", "falcon3:7b" in src and "gemma4:12b" in src)

print("\nFAILED: %s" % fails if fails else "\nALL PASS")
sys.exit(1 if fails else 0)

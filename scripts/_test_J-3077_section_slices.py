"""J-3077 (F-3786): distinct note slice per section, opening covers line, positive carry instruction, persisted
outline + words, word-boundary title, section-overlap numbers. Temp paths; scripted fake call_json; no live store.
Run from the worktree:  python scripts/_test_J-3077_section_slices.py"""
from __future__ import annotations
import asyncio, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import core                                    # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import essay_lesson as el            # noqa: E402

FAILS = []
def check(c, m):
    print(("  ok:   " if c else "  FAIL: ") + m)
    if not c: FAILS.append(m)

BODY = "\n".join("- note %03d marker%03d: the firm trades sugar and ledgers balance." % (i, i) for i in range(60))
check(len(BODY) < el._REDUCE_THRESHOLD, "body under reduce threshold (%d)" % len(BODY))
sl = [el._note_slice(BODY, i, 3) for i in (1, 2, 3)]
check(len({*sl}) == 3 and sl[0].startswith("- note 000"), "3 distinct slices, first starts at note 0")
check("marker059" in sl[2] and "marker000" not in sl[2], "last slice holds the tail only")
seen = "\n".join(sl).split("\n")
check(seen == BODY.split("\n"), "slices partition the notes in order")
check(el._note_slice("short", 2, 3) == "short", "short body falls back whole")

class Fake:
    def __init__(self): self.sec_calls = []
    async def __call__(self, base_urls, system, user, max_tokens=0, temperature=0.0):
        if "Plan a real ESSAY" in system:
            return {"thesis": "Ledgers keep honest people honest and ruin the careless ones in the end of the story",
                    "sections": [{"heading": "H%d" % k, "covers": "covers-%d" % k} for k in range(3)]}
        self.sec_calls.append((system, user))
        n = len(self.sec_calls)
        return {"section": ("Distinct sentence number %d about topic%d. " % (n, n)) * 8}

f = Fake()
essay = asyncio.run(el._compose_once(f, ["u"], "T", BODY))
check(essay[1] and len(f.sec_calls) == 3, "3 sections written")
users = [u for _, u in f.sec_calls]
check(len(set(users)) == 3, "each section call got a different notes slice")
check("covers-0" in f.sec_calls[0][0], "opening section got a covers line")
check("do not repeat" not in f.sec_calls[1][0] and "has not yet used" in f.sec_calls[1][0], "positive carry-forward instruction")
plan = el._LAST_PATH["T"].get("plan") or {}
check(plan.get("thesis", "").startswith("Ledgers") and len(plan.get("words", [])) == 3 and len(plan.get("sections", [])) == 3,
      "outline + word counts parked for record()")
el._PATHS["T"] = dict(el._LAST_PATH["T"])
t = el.essay_title_from("T", essay[0])
check(len(t) <= 60 and not t.endswith(" ") and t in plan["thesis"] and plan["thesis"][len(t)] == " ", "title cut at a word boundary: %r" % t)
el._PATHS.clear(); el._LAST_PATH.clear()
t2 = el.essay_title_from("T", "A short opening sentence here. Then more.")
check(t2 == "A short opening sentence here", "fallback to first sentence: %r" % t2)

ov = el.section_overlap("Alpha beta gamma delta epsilon zeta eta theta.\n\n## B\n\nAlpha beta gamma delta epsilon zeta eta theta. New words only here today friends.")
check(ov["first_sent_jaccard"] >= 0.5 and ov["sent6_overlap"] > 0, "overlap detects restated opening: %s" % ov)
ov2 = el.section_overlap(essay[0])
check("sent6_overlap" in ov2, "overlap on composed essay: %s" % ov2)
print("FAILED %d" % len(FAILS) if FAILS else "ALL OK")
sys.exit(1 if FAILS else 0)

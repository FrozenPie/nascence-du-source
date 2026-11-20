"""J-3631 (F-4239): closed_book_shadow records the answering lane and refuses a fallback-lane answer.
Fake call_json and fake left_lane judge only; no live store, no hub. Run: python scripts/_test_J-3631_closed_book_lane.py"""
from __future__ import annotations
import asyncio, sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import core  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import essay_lesson as el, left_lane  # noqa: E402

FAILS = []
def check(c, m):
    if not c:
        FAILS.append(m); print("  FAIL:", m)

ESSAY = " ".join(f"The author argues that point number {i} shows a particular thing about the book and its people." for i in range(12))
NOTES = "notes " * 50
judged = []
async def fake_judge(pairs):
    judged.append(len(pairs))
    return {"matches": [1.0] * len(pairs)}

def make(fallback, with_served=True):
    async def cj(urls, sys_, user, max_tokens=0, temperature=0.0, served=None, **kw):
        if served is not None:
            served.update({"url": "http://hot.test:11433" if fallback else "http://bg.test:11441",
                           "model": "m", "fallback": fallback})
        n = user.count("\n") and sum(1 for l in user.splitlines() if l[:1].isdigit() and ". " in l[:4])
        return {"completions": ["x finished sentence"] * max(n, 8)}
    async def cj_plain(urls, sys_, user, max_tokens=0, temperature=0.0):
        return {"completions": ["x finished sentence"] * 12}
    return cj if with_served else cj_plain

async def run(cj):
    with mock.patch.object(left_lane, "judge_rederivation", fake_judge):
        return await el.closed_book_shadow(cj, ["bg", "hot"], "T", NOTES, ESSAY)

r = asyncio.run(run(make(False)))
check(r["ok"], f"primary-lane row should score: {r}")
check(r["served"] and r["served"]["fallback"] is False and r["served"]["url"].startswith("http://bg"), f"served recorded: {r}")
judged.clear()
r = asyncio.run(run(make(True)))
check(not r["ok"] and r["reason"] == "fallback lane", f"fallback row refused: {r}")
check(r["served"]["fallback"] is True and "share" not in r and not judged, "fallback not judged or scored")
r = asyncio.run(run(make(False, with_served=False)))
check(r["ok"] and r["served"] is None, f"call_json without served still works: {r}")
print("FAIL" if FAILS else "OK")
sys.exit(1 if FAILS else 0)

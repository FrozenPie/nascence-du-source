"""J-3010 (F-3713, P-0065): a level >= 1 chapter's 'The period:' label comes from the member chapters' OWN periods,
not their formation times. Touches no live data: pure functions plus try_form_chapter with a stubbed cluster finder and
a stubbed model that returns a too-short chapter (returns before any store write). Run from the worktree:
  python scripts/_test_J-3010_chapter_span.py"""
from __future__ import annotations

import asyncio
import sys
import time
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env)
from core import chapters as ch  # noqa: E402
ch.RETIRE_THEME_CHAPTERS = False   # J-4338

_tmp = tempfile.mkdtemp(prefix="J3010_")
fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (" -- " + extra if extra and not cond else ""))
    if not cond:
        fails.append(name)


def ts(y, m, d, h=12):
    return datetime(y, m, d, h).timestamp()


def fmt(t):
    return time.strftime("%B %d", time.localtime(t))


def chap(label, formed, title="A Title"):
    return {"id": "x", "content": f"[A chapter of my life — '{title}' ({label})] I did things.", "ts": formed, "importance": 0.85}


# [1] parse a member label, year recovered from formation time
sp = ch._parse_member_span(chap("September 04 to October 15", ts(2026, 11, 1))["content"], ts(2026, 11, 1))
check("parse: start/end dates", sp is not None and fmt(sp[0]) == "September 04" and fmt(sp[1]) == "October 15", str(sp))
check("parse: years are 2026", sp is not None and datetime.fromtimestamp(sp[0]).year == 2026 and datetime.fromtimestamp(sp[1]).year == 2026)
# year boundary: a period December 20 to January 05 formed on January 10
sp = ch._parse_member_span(chap("December 20 to January 05", ts(2027, 1, 10))["content"], ts(2027, 1, 10))
check("parse: year boundary (Dec -> Jan)", sp is not None and datetime.fromtimestamp(sp[0]).year == 2026 and datetime.fromtimestamp(sp[1]).year == 2027, str(sp))
# a period ending the same day it was formed still reads as that year
sp = ch._parse_member_span(chap("May 01 to May 20", ts(2026, 5, 20, 8))["content"], ts(2026, 5, 20, 8))
check("parse: end on the formation day", sp is not None and datetime.fromtimestamp(sp[1]).year == 2026, str(sp))
# a title with parentheses does not confuse the label read
sp = ch._parse_member_span(chap("June 01 to June 09", ts(2026, 7, 1), title="Waiting (again)")["content"], ts(2026, 7, 1))
check("parse: parenthesised title", sp is not None and fmt(sp[0]) == "June 01" and fmt(sp[1]) == "June 09", str(sp))
check("parse: no label -> None", ch._parse_member_span("[A chapter of my life — 'T'] body", ts(2026, 7, 1)) is None)
check("parse: garbage month -> None", ch._parse_member_span("[A chapter of my life — 'T' (Foo 04 to Bar 05)] b", ts(2026, 7, 1)) is None)

# [2] _cluster_span
base = [{"id": f"t{i}", "content": "a thought", "ts": ts(2026, 9, 1) + i * 86400, "importance": 0.5} for i in range(5)]
t0, t1 = ch._cluster_span(base, 0)
check("level 0: min/max of the thought timestamps (unchanged)", t0 == base[0]["ts"] and t1 == base[-1]["ts"])

# the c8f88b32 case: four level-1 chapters formed Oct 06..Oct 29, whose own periods run Sep 04..Oct 15
members = [
    chap("September 04 to September 20", ts(2026, 10, 6)),
    chap("September 15 to October 01", ts(2026, 10, 12)),
    chap("September 28 to October 10", ts(2026, 10, 20)),
    chap("October 03 to October 15", ts(2026, 10, 29)),
]
old = (min(m["ts"] for m in members), max(m["ts"] for m in members))
check("old behaviour was wrong for this case (formation dates)", fmt(old[0]) == "October 06" and fmt(old[1]) == "October 29")
t0, t1 = ch._cluster_span(members, 1)
check("level 1: earliest start and latest end of the members' periods",
      fmt(t0) == "September 04" and fmt(t1) == "October 15", f"{fmt(t0)} to {fmt(t1)}")
# one member unparsable: left out, the rest still decide
mixed = members[:2] + [{"id": "z", "content": "[A chapter of my life — 'T'] no label", "ts": ts(2026, 12, 25), "importance": 0.8}]
t0, t1 = ch._cluster_span(mixed, 1)
check("level 1: an unreadable member is left out (not its formation date)", fmt(t0) == "September 04" and fmt(t1) == "October 01", f"{fmt(t0)} to {fmt(t1)}")
# none parse: fall back to the formation times as before
nolabel = [{"id": f"n{i}", "content": "no label", "ts": ts(2026, 10, 1) + i * 86400, "importance": 0.8} for i in range(4)]
t0, t1 = ch._cluster_span(nolabel, 1)
check("level 1: nothing parses -> formation times (old behaviour)", t0 == nolabel[0]["ts"] and t1 == nolabel[-1]["ts"])
# level 3 (cluster level 2) reads the same way
t0, t1 = ch._cluster_span(members, 2)
check("level 2 cluster: same rule", fmt(t0) == "September 04" and fmt(t1) == "October 15")

# [3] try_form_chapter hands the author the right span, stored label not touched (short body -> no store write)
seen = {}


async def fake_find(level):
    return members if level == 1 else None


async def fake_call_json(urls, sysp, userp, **kw):
    seen["user"] = userp
    return {"title": "x", "chapter": "too short"}


orig = ch.find_cluster_async
ch.find_cluster_async = fake_find
try:
    res = asyncio.run(ch.try_form_chapter(fake_call_json, ["http://stub"]))
finally:
    ch.find_cluster_async = orig
check("try_form_chapter: the author is told September 04 to October 15",
      "The period: September 04 to October 15." in seen.get("user", ""), seen.get("user", "")[:120])
check("try_form_chapter: unusable chapter -> None, nothing stored", res is None)

print("\nFAILED: %s" % fails if fails else "\nALL PASS")
sys.exit(1 if fails else 0)

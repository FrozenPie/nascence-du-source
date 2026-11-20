"""J-3011 (F-3718, P-0065): the chapter author prompt no longer plants 'anxious year' or asks what 'moved' unconditionally.

Touches no live data: try_form_chapter is driven with a stubbed cluster finder and a stubbed call_json that returns a
too-short chapter, so the function returns before any store write; the analysis helpers run on strings only.
Run from the worktree:  python scripts/_test_J-3011_chapter_prompt.py
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env)
from core import chapters as ch  # noqa: E402
ch.RETIRE_THEME_CHAPTERS = False   # J-4338

_tmp = tempfile.mkdtemp(prefix="J3011_")      # nothing is written, but make the intent explicit
fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (" -- " + extra if extra and not cond else ""))
    if not cond:
        fails.append(name)


p = ch._author_system_prompt()
low = p.lower()
check("no 'anxious' anywhere in the system prompt", "anxious" not in low and "anxi" not in low)
check("no unconditional 'what (if anything) moved'", "moved by its end" not in low and "(if anything) moved" not in low)
check("feeling must be one the sample states", "only if the sample states that feeling" in low)
check("movement must be one the sample shows", "only if the sample shows it changing" in low)
check("JSON schema, first person past tense and 4-7 sentences kept",
      '"title"' in p and '"chapter"' in p and "FIRST PERSON" in p and "PAST TENSE" in p and "4-7 sentences" in p)
check("starts with /no_think and names Du", p.startswith("/no_think\n") and "(Du)" in p)

# try_form_chapter really sends it (stubbed finder + stubbed model; short body -> returns None before any store write)
seen = {}
cluster = [{"id": f"m{i}", "content": f"thought number {i} about the garden", "importance": 0.5 + i / 100,
            "ts": 1_700_000_000.0 + i * 3600} for i in range(6)]


async def fake_find(level):
    return cluster if level == 0 else None


async def fake_call_json(urls, sysp, userp, **kw):
    seen["sys"], seen["user"] = sysp, userp
    return {"title": "x", "chapter": "too short"}


orig = ch.find_cluster_async
ch.find_cluster_async = fake_find
try:
    res = asyncio.run(ch.try_form_chapter(fake_call_json, ["http://stub"]))
finally:
    ch.find_cluster_async = orig
check("try_form_chapter returns None on an unusable chapter", res is None)
check("try_form_chapter sent the new prompt", seen.get("sys") == p)
check("the user prompt still carries the sample", "A sample, in time order" in seen.get("user", ""))

# the analysis helpers
from scripts import j3011_chapter_affect_check as an  # noqa: E402
hdr = "[A chapter of my life - 'The garden' (May 01 to May 09)] I sat with the thyme. I felt calm that week."
body = an.strip_header(hdr)
check("strip_header drops the bracketed header", body.startswith("I sat with the thyme"))
check("split_sentences keeps both sentences", len(an.split_sentences(body)) == 2)
check("family regex: 'anxiety' hits anxiety, 'danger' does not hit anger",
      an.FAM_RE["anxiety"].search("my anxiety lifted") and not an.FAM_RE["frustration"].search("a danger to me"))
check("family regex: 'ease' is not matched inside 'disease'", not an.FAM_RE["relief"].search("the disease spread"))
m = an.sample_ids([{"id": f"m{i}", "ts": float(i), "importance": float(i % 5)} for i in range(20)])
check("sample_ids picks at most 8, like _sample", 0 < len(m) <= 8)

print("\nALL PASS" if not fails else "\nFAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)

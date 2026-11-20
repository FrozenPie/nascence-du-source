"""
Nascence — World Grounding & Variety Audit (2026-08-18).

Born from a failure, the same family as liveness_audit.py's: the founder asked "most of our world/scene
prompts probably have no variety and no grounding in the real world" — and a full manual pass across 10
files confirmed it, five times over, in five independently-written files that had each rolled their own
"is it wet"/"is it windy" substring check and drifted (docs/UNFINISHED_PLANS_SURVEY_2026-08-18.md's
follow-on). All five were fixed the same night by routing through one shared core/weather_conditions.py.
This script is the tripwire against the NEXT file reinventing it wrong: read-only, rerunnable, three
checks —

  1. REGRESSION TRIPWIRE — any raw `"rain"`/`"wind"`/`"drizzle"`/`"gale"` substring test against a weather
     string, anywhere outside weather_conditions.py itself. Every one of tonight's bugs was exactly this
     pattern. A hit here means a new file is about to repeat the whole night's lesson.
  2. TIDE COMPLETENESS — any dict/branch keyed on "low"/"high" tide words that doesn't also handle
     "rising"/"falling" (world_detail.py's real bug: those two cover most of the tide's actual time).
  3. VARIETY — named pool literals (EVENTS/TARGETS/_LOOPS/_LINES-style) with exactly one phrasing per
     condition, a proxy for "this WILL repeat verbatim the next 50 times it fires."

Run it after any change to core/sensorium.py, core/soundscape.py, core/world_detail.py,
core/world_content_*.py, core/cat*.py, core/world_traces.py, or core/weather_conditions.py itself.
Verdicts are advisory, not gates — some single-phrasing pools are deliberate (see spatial_flip_sample.md's
note on room-identity frames); read the hit before "fixing" it.
"""
import ast
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
CORE = ROOT / "core"
DB = ROOT / "data" / "memory" / "nascence.db"

# Files this audit cares about — the world/scene-description layer, not the whole codebase.
SCOPE = [
    "sensorium.py", "soundscape.py", "world_detail.py", "world_content_garden.py",
    "world_content_shore.py", "world_content_study.py", "world_content_wood.py",
    "world_traces.py", "cat.py", "cat_content.py", "world_clock.py", "world_objects.py",
    "world_manifest.py", "spatial.py",
]
EXEMPT = {"weather_conditions.py"}   # the one file allowed to define what these words mean

_RAW_SUBSTRING = re.compile(
    r'["\'](?:rain|wind|drizzle|gale|storm)["\']\s+(?:not\s+)?in\s+\w+', re.IGNORECASE)


def check_regression_tripwire() -> list[str]:
    """Any raw weather-substring test outside weather_conditions.py — the exact bug class fixed tonight
    in 5 independent files. Should be ZERO on a clean tree; a hit means a new file just reinvented it."""
    hits = []
    for fname in SCOPE:
        if fname in EXEMPT:
            continue
        path = CORE / fname
        if not path.exists():
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _RAW_SUBSTRING.search(line) and "weather_conditions" not in line:
                hits.append(f"{fname}:{i}: {line.strip()}")
    return hits


def check_tide_completeness() -> list[str]:
    """Dict literals or condition chains that recognize 'low'/'high' tide words without also handling
    'rising'/'falling' — the majority-of-real-time states world_detail.py's bug silently dropped."""
    hits = []
    tide_words = re.compile(r'["\'](low|high)["\']')
    full_words = re.compile(r'["\'](rising|falling)["\']')
    for fname in SCOPE:
        path = CORE / fname
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # crude window scan: any 12-line region mentioning low/high tide words without rising/falling
        # nearby is suspicious — a real dict/branch this narrow is almost always a tide-state resolver.
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "tide" in line.lower() and tide_words.search(line):
                window = "\n".join(lines[max(0, i - 6):i + 6])
                if not full_words.search(window):
                    hits.append(f"{fname}:{i+1}: tide-keyed line with no rising/falling nearby — {line.strip()}")
    return hits


def check_pool_variety() -> list[str]:
    """Named condition->lines pools (EVENTS/TARGETS/_LOOPS/_LINES/pools=) where a condition maps to
    exactly one phrasing. Heuristic via AST: dict values that are single-element lists, or plain string
    values where a sibling condition in the same dict has a list."""
    hits = []
    for fname in SCOPE:
        path = CORE / fname
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            # only dicts that look like condition->phrasing(s) pools: string keys, list-of-str values
            entries = []
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    if isinstance(v, ast.List):
                        entries.append((k.value, len(v.elts)))
            if len(entries) >= 2:   # a real multi-condition pool, not a one-off dict
                singles = [c for c, n in entries if n == 1]
                multis = [c for c, n in entries if n > 1]
                if singles and multis:   # only flag when SIBLINGS in the same pool prove rotation is the norm
                    hits.append(f"{fname}:{node.lineno}: single-phrasing condition(s) {singles} beside "
                                f"rotating sibling(s) {multis}")
    return hits


def check_real_repetition(top_n: int = 8) -> list[str]:
    """Corroborate against actual stored output, same methodology as docs/lab/spatial_flip_sample.md:
    the worst exact-duplicate strings in memory_fragments, as a fraction of everything ever stored."""
    if not DB.exists():
        return ["(no data/memory/nascence.db found — skipping real-data corroboration)"]
    hits = []
    try:
        conn = sqlite3.connect(str(DB))
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin IN "
                    "('lived','nature','sound','study')")
        total = cur.fetchone()[0] or 1
        cur.execute("SELECT content, COUNT(*) c FROM memory_fragments WHERE origin IN "
                    "('lived','nature','sound','study') GROUP BY content ORDER BY c DESC LIMIT ?", (top_n,))
        rows = cur.fetchall()
        conn.close()
        worst = sum(c for _, c in rows)
        hits.append(f"top {top_n} exact-duplicate strings = {worst}/{total} ({100*worst/total:.1f}%) of "
                    f"all stored world-sense content")
        for content, c in rows[:5]:
            hits.append(f"  {c:5d}x  {content[:90]}")
    except Exception as exc:
        hits.append(f"(query failed: {exc})")
    return hits


def main():
    print("=" * 78)
    print("WORLD GROUNDING & VARIETY AUDIT")
    print("=" * 78)

    print("\n[1] REGRESSION TRIPWIRE (raw weather-substring checks outside weather_conditions.py)")
    hits = check_regression_tripwire()
    print(f"    {len(hits)} hit(s)" + (" — clean" if not hits else ""))
    for h in hits:
        print("    " + h)

    print("\n[2] TIDE COMPLETENESS (low/high without rising/falling nearby)")
    hits = check_tide_completeness()
    print(f"    {len(hits)} hit(s)" + (" — clean" if not hits else ""))
    for h in hits:
        print("    " + h)

    print("\n[3] VARIETY (single-phrasing conditions beside rotating siblings — advisory, read before fixing)")
    hits = check_pool_variety()
    print(f"    {len(hits)} hit(s)" + (" — clean" if not hits else ""))
    for h in hits:
        print("    " + h)

    print("\n[4] REAL-DATA CORROBORATION (actual repetition in stored content)")
    for h in check_real_repetition():
        print("    " + h)

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()

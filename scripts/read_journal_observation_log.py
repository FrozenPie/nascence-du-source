"""
J-2987 (F-3687/F-3688, P-0069) -- the READER for data/journal_observation_log.jsonl (core/journal.py:_log_observation).

Deterministic, no model call, no self-judge: it only counts words. Two measures per row, scene = the first 700 chars
(that is all the model is shown, core/journal.py write_observation):

  impulse leak     content words (>= 5 letters) that are in the impulse but NOT in the scene, and that the entry
                   repeats. Leaked if >= 2 such words ("loose"), reported with the >= 1 rate as well.
  ungrounded kinds colour words and animal-kind words that the entry names but the scene does not
                   (the F-3687 "ginger tabby" case).

Grading entries against their scene with a model belongs to a judge of a different family (left_lane.
grade_gist_faithfulness(entry, [scene]) takes these rows as they are; see the J-2987 follow-up job). This script is the
cheap standing reader so the log is never write-only.

  python scripts/read_journal_observation_log.py [path-to-log] [--since-flag false|true]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = ROOT / "data" / "journal_observation_log.jsonl"
SCENE_SHOWN = 700   # chars of scene the model is shown

COLOURS = {
    "grey", "gray", "black", "white", "red", "orange", "ginger", "yellow", "green", "blue", "brown", "golden",
    "gold", "silver", "pink", "purple", "violet", "amber", "tawny", "russet", "crimson", "scarlet", "cream",
    "tan", "copper", "bronze", "ivory", "tabby", "striped", "stripes", "dappled", "speckled", "mottled",
}
ANIMALS = {
    "cat", "kitten", "dog", "bird", "gull", "seagull", "crow", "raven", "sparrow", "robin", "owl", "hawk", "heron",
    "fox", "deer", "rabbit", "hare", "mouse", "rat", "seal", "fish", "crab", "snail", "beetle", "spider", "moth",
    "butterfly", "bee", "fly", "horse", "cow", "sheep", "goat", "pig", "squirrel", "otter", "lizard", "frog",
    "tabby", "wolf", "bear", "duck", "swan", "goose", "wren", "finch", "starling", "pigeon", "dove",
}
_WORD = re.compile(r"[a-z]+")


def words(text: str) -> set:
    return set(_WORD.findall((text or "").lower()))


def leak_words(row: dict) -> list:
    """Words the entry repeats from the impulse that the shown scene does not contain."""
    scene = words((row.get("scene") or "")[:SCENE_SHOWN])
    imp = {w for w in words(row.get("impulse")) if len(w) >= 5} - scene
    return sorted(imp & words(row.get("entry")))


def ungrounded_kinds(row: dict) -> list:
    """Colour or animal words the entry names that the shown scene does not."""
    scene = words((row.get("scene") or "")[:SCENE_SHOWN])
    ent = words(row.get("entry"))
    return sorted(((COLOURS | ANIMALS) & ent) - scene)


def summarize(rows: list) -> dict:
    n = len(rows)
    if not n:
        return {"rows": 0}
    leaks = [leak_words(r) for r in rows]
    kinds = [ungrounded_kinds(r) for r in rows]
    return {
        "rows": n,
        "impulse_leak_ge1": round(sum(1 for x in leaks if len(x) >= 1) / n, 3),
        "impulse_leak_ge2": round(sum(1 for x in leaks if len(x) >= 2) / n, 3),
        "ungrounded_kind_rate": round(sum(1 for x in kinds if x) / n, 3),
        "ungrounded_examples": [(r.get("target"), k) for r, k in zip(rows, kinds) if k][:8],
    }


def read_rows(path: Path) -> list:
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except OSError:
        pass
    return rows


def main(argv: list) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    path = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else DEFAULT_LOG
    rows = read_rows(path)
    if not rows:
        print(f"{path}: no rows yet (the log fills as Du writes field-journal observations after a restart)")
        return 0
    by_flag = {}
    for r in rows:
        by_flag.setdefault(bool(r.get("impulse_in_prompt")), []).append(r)
    print(f"{path}: {len(rows)} rows")
    for flag in sorted(by_flag):
        print(f"  impulse_in_prompt={flag}: {json.dumps(summarize(by_flag[flag]), ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

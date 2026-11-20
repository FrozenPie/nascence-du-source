"""
LIBRARIAN P0-vs-P1 HEAD-TO-HEAD — J-0128 / D-0019, 2026-08-24.

D-0019's ruling: docs/lab/librarian_framing_2026-08-23.md measured P1 (core/librarian.py's LLM
subject-mapper) ALONE at hit_rate 0.80 (20/25) against 25 real frontier.json questions -- not a
real P0-vs-P1 comparison, because P0 and P1 fire on mutually exclusive phrasings in production and
never run on the same input naturally. This script runs P0 (core/library_hand.py's real production
mechanism: topic_from() regex extraction -> _topic_hit() subject/title/author substring match, the
SAME functions actually wired live) against the IDENTICAL 25 questions (same seed=20260823, same
frontier.json filter as scripts/librarian_framing_lab.py's _load_questions()), so the two hit rates
are directly comparable.

Design choice, stated plainly (matching the lab series' own discipline): P0's real trigger,
topic_from(), only fires on "book about/on/of X" phrasing. Frontier questions are not phrased that
way (they are carried questions like "how does a fireplace work", not "a book about fireplaces").
This IS the honest test of P0 as it actually exists in production code today -- not a rewritten,
more-generous version of P0. If topic_from() returns None, that ask never reaches the catalogue at
all under P0 (falls through to the breadth engine / serendipity pick in production, which is not
"a book bearing on the question" in any topic-driven sense) -- scored as no-hit, exactly as it would
behave live.

Hit definition matches the P1 lab exactly: >=1 real catalogue row (English-language) whose
title/author/subjects field contains the extracted topic -- this mirrors _topic_hit() as used inside
library_hand._search(), just without the random weighted pick (irrelevant to a binary hit/no-hit
question) or the prefer-unread reordering (also irrelevant to hit existence).

ISOLATION: no live state is written. topic_from() is a pure regex over text. The catalogue CSV
(C:\\Knowledge\\SPGC-metadata-2018-07-18.csv) is read-only, external to Nascence's own data/ stores.
frontier.json is read-only. No core.memory.store / DB calls are made anywhere in this script. Still
run inside lab_env.isolate() per the job's isolation="required" flag, as the mandated safety net.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(r"C:\Nascence")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FRONTIER_FILE = ROOT / "data" / "frontier.json"
OUT_DIR = ROOT / "data" / "lab" / "librarian_p0_headtohead"
REPORT = ROOT / "docs" / "lab" / "librarian_p0_headtohead_2026-08-24.md"

N_QUESTIONS = 25
SEED = 20260823   # IDENTICAL to librarian_framing_lab.py -- must reproduce the same 25 questions

P1_HIT_RATE = 20 / 25   # from docs/lab/librarian_framing_2026-08-23.md (narrative framing, live)
P1_MEAN_N_HITS = 6.08


def _load_questions() -> list[str]:
    """Byte-for-byte identical to librarian_framing_lab.py's _load_questions()."""
    d = json.loads(FRONTIER_FILE.read_text(encoding="utf-8"))
    qs = [q["q"] for q in d["questions"] if q.get("q") and len(q["q"].strip()) >= 8]
    rnd = random.Random(SEED)
    return rnd.sample(qs, min(N_QUESTIONS, len(qs)))


def run() -> dict:
    from core import library_hand as _lib

    questions = _load_questions()
    print(f"reproduced {len(questions)} questions (seed={SEED}) -- verifying identity with P1 lab...")

    # sanity check: these must be the same 25 questions the P1 lab used (raw.json has them recorded)
    p1_raw = json.loads((ROOT / "data" / "lab" / "librarian_framing" / "raw.json").read_text(encoding="utf-8"))
    p1_questions = [r["question"] for r in p1_raw]
    identical = questions == p1_questions
    print(f"question-set identical to P1 lab's raw.json: {identical}")

    rows = list(_lib._rows())   # one CSV scan, reused for every question (read-only)
    en_rows = [r for r in rows if "'en'" in (r.get("language") or "")]

    results = []
    for i, q in enumerate(questions):
        topic = _lib.topic_from(q)
        if topic:
            t = topic.lower().strip()
            hits = [r for r in en_rows if _lib._topic_hit(r, t)]
        else:
            hits = []
        results.append({
            "question": q,
            "topic_extracted": topic,
            "n_hits": len(hits),
            "hit": len(hits) > 0,
        })
        print(f"  {i+1}/{len(questions)} topic={topic!r} hits={len(hits)}")

    n = len(results)
    n_topic_extracted = sum(1 for r in results if r["topic_extracted"])
    n_hit = sum(1 for r in results if r["hit"])
    mean_hits = sum(r["n_hits"] for r in results) / n if n else 0

    summary = {
        "n_total": n,
        "question_set_identical_to_p1_lab": identical,
        "n_topic_extracted_by_topic_from": n_topic_extracted,
        "hit_rate_P0": round(n_hit / n, 3) if n else None,
        "hits_P0": f"{n_hit}/{n}",
        "mean_n_hits_P0": round(mean_hits, 2),
        "hit_rate_P1_from_2026-08-23_lab": round(P1_HIT_RATE, 3),
        "hits_P1": "20/25",
        "mean_n_hits_P1_from_2026-08-23_lab": P1_MEAN_N_HITS,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


if __name__ == "__main__":
    run()

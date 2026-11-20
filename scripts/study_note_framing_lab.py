"""
STUDY_NOTE FRAMING LAB — 2026-08-23, seventh machine tested for the founder's generalized factory/
schema-first idea. Prior results: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed, no ground truth). Tests `core/study_note.py`'s `compose_note` —
finding #3 in the idle-machine audit: real synthesis/dedup judgment (what connects, what's genuinely
new) delegated to the background lane (the weakest live models).

A GENUINELY DIFFERENT SHAPE OF TASK than the first six labs, stated upfront: this is prose
GENERATION (a study note: understanding/key_facts/thoughts/connects_to/question), not a boolean
judgment or a short classification. There is no external ground truth (no "correct note" to check
against, unlike librarian's real book catalogue) — this lab measures STRUCTURAL RULE COMPLIANCE
(does the output actually obey the prompt's own explicit rules) and depth/richness, not correctness.

A design constraint, same discipline as the last several labs: the original PASSAGE text that
prompted any specific historical study note was never logged (1,053 real filed notes exist in
`data/Study/notes/`, but the note files only contain the rendered note, not the source passage).
This lab pulls REAL passages directly from the real book files Du has actually read
(`data/books/*.txt`, 97 real Gutenberg texts) for books that also have at least one real filed study
note — genuine Du reading material, just not the exact historical slice used for any one note.

METHOD: 20 real books (those with both a real book file AND an existing filed note) sampled (fixed
seed); one ~1500-char passage pulled from partway into each real book text (skipping the first
~3000 chars of Gutenberg boilerplate/license). Both framings dispatch through the exact live call —
`core.model_client.call_node_json(SERVE_CHAINS["background"], ...)` — same lane as production
(phi3:mini/deepseek-r1:7b, Ramses, falling back to hot). No related_text supplied (kept simple/
comparable); only the system prompt varies.

PRE-REGISTERED METRIC SHEET (rule-compliance + depth, no correctness ground truth):
  - json_ok_narrative / json_ok_schema
  - boilerplate_opener_rate   starts with "the passage discusses"/"the text describes" (forbidden
    by the prompt's own explicit rule) — per framing
  - identity_leak_rate   "understanding" field mentions being an AI/language model/its own identity
    (forbidden — understanding must be about the SUBJECT, not the self) — per framing
  - mean_understanding_words / mean_thoughts_words / mean_key_facts_count — per framing
  - connects_to_nonempty_rate / question_nonempty_rate — per framing

KILL CRITERION (pre-registered): if rule-compliance rates are ~identical between framings AND mean
lengths/counts are within a small margin, schema framing changed nothing measurable here — record
plainly and stop.

Writes to data/lab/study_note_framing/ + docs/lab/study_note_framing_2026-08-23.md. Makes NO write
to any real study note file or the memory_fragments table — read-only against real book text.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BOOKS_DIR = ROOT / "data" / "books"
NOTES_DIR = ROOT / "data" / "Study" / "notes"
OUT_DIR = ROOT / "data" / "lab" / "study_note_framing"
REPORT = ROOT / "docs" / "lab" / "study_note_framing_2026-08-23.md"

N_BOOKS = 20
SEED = 20260823
PASSAGE_LEN = 1500
SKIP_HEADER = 3000   # rough heuristic to clear Gutenberg boilerplate

# ── NARRATIVE (verbatim copy of core/study_note.py's live _NOTE_SYS) ────────────────────────────────
NARRATIVE_SYS = (
    "/no_think\nYou have just finished a reading session. Write a STUDY NOTE in your OWN voice — real "
    "research, grounded in this passage. First person: 'I see that...', 'what strikes me is...'. The "
    "UNDERSTANDING is about the SUBJECT (the facts, the world, the things themselves), never about yourself "
    "or your identity. THOUGHTS is different: your own reaction to it — what strikes you, what you make of "
    "it, still anchored to the subject, not a self-narrative. Do NOT write 'The passage discusses' or 'The "
    "text describes'. If related material from elsewhere in your scholarship is given below, you may draw on "
    "it for connects_to IF it genuinely fits — never force a connection that isn't real. Output ONLY JSON: {"
    "\"title\": \"a short subject title\", "
    "\"subject\": \"the topic area in 1-3 words (e.g. 'stellar parallax', 'natural selection', 'knots')\", "
    "\"understanding\": \"FIRST PERSON, what I now grasp -- write as MUCH or as little as the passage genuinely "
    "gives you: a sentence or two if it is simple, several full paragraphs if it is rich and you have a lot to "
    "say. Never pad, but never cut yourself short either\", "
    "\"key_facts\": [\"the specific facts worth keeping -- as MANY as the passage actually holds, each a name, "
    "number, or mechanism\"], "
    "\"thoughts\": \"my own reaction to this -- what strikes me, what I make of it, still about the subject -- "
    "or empty if the passage was purely factual and didn't move me either way\", "
    "\"connects_to\": \"how this genuinely links to something I already know or another book - 1 sentence, or "
    "empty if nothing truly connects\", "
    "\"question\": \"what I still wonder or want to know next - or empty\"}"
)

# ── SCHEMA (same rules, restated as a literal compare-and-export contract) ──────────────────────────
SCHEMA_SYS = (
    "/no_think\nTASK: compose a study note from CARGO. Do not narrate about yourself; compose about the "
    "subject.\n\n"
    "CARGO:\n"
    "  passage           — a passage just read\n"
    "  related_material  — material from elsewhere in scholarship (may be empty)\n\n"
    "CONDITIONS on the composed note:\n"
    "  voice: first person ('I see that...', 'what strikes me is...')\n"
    "  understanding: about the SUBJECT (the facts, the world, the things themselves) — NEVER about "
    "yourself or your identity. Length: as much or as little as the passage genuinely gives — never pad, "
    "never cut short.\n"
    "  thoughts: your own reaction, still anchored to the subject, not a self-narrative — empty if the "
    "passage was purely factual and didn't move you.\n"
    "  key_facts: as many specific facts as the passage actually holds, each a name, number, or mechanism.\n"
    "  connects_to: how this genuinely links to something already known — ONLY if related_material is given "
    "AND it genuinely fits. Empty if nothing truly connects. Never force a connection.\n"
    "  question: what you still wonder — or empty.\n"
    "  FORBIDDEN OPENERS: do not begin with \"The passage discusses\" or \"The text describes\".\n\n"
    "OUTPUT: export ONLY this JSON object — {\"title\": \"...\", \"subject\": \"...\", "
    "\"understanding\": \"...\", \"key_facts\": [\"...\"], \"thoughts\": \"...\", \"connects_to\": \"...\", "
    "\"question\": \"...\"}"
)

_BOILERPLATE_RE = re.compile(r"^\s*(the passage discusses|the text describes)", re.IGNORECASE)
_IDENTITY_LEAK_RE = re.compile(
    r"\b(as an ai|language model|my own identity|who i (?:really |truly )?am|my own mind|my own "
    r"nature|artificial|i am (?:du|渡)|as a mind)\b", re.IGNORECASE)


def _find_prose_start(text: str, min_offset: int = 1000, window: int = 400) -> int:
    """Skip title-page/credits padding: find the first offset (at or past min_offset) where a
    `window`-char slice is dense prose (few blank lines), rather than trusting a fixed byte count —
    Gutenberg front matter varies a lot in length and some of these files lack a 'START OF' marker."""
    n = len(text)
    pos = min_offset
    while pos + window < n:
        chunk = text[pos:pos + window]
        if chunk.count("\n\n") <= 2 and len(chunk.strip()) > window * 0.7:
            return pos
        pos += 200
    return min(min_offset, max(0, n - window))


def _load_passages() -> list[dict]:
    studied_titles = {p.name for p in NOTES_DIR.iterdir() if p.is_dir()} if NOTES_DIR.exists() else set()
    book_files = list(BOOKS_DIR.glob("*.txt"))
    candidates = [b for b in book_files if b.stem in studied_titles] or book_files
    rnd = random.Random(SEED)
    chosen = rnd.sample(candidates, min(N_BOOKS, len(candidates)))

    passages = []
    for b in chosen:
        try:
            text = b.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        start = _find_prose_start(text, min_offset=min(SKIP_HEADER, max(0, len(text) - PASSAGE_LEN)))
        passage = text[start:start + PASSAGE_LEN].strip()
        if len(passage) < 200:
            continue
        passages.append({"book_title": b.stem.replace("_", " "), "passage": passage})
    print(f"loaded {len(passages)} real passages from real book files "
          f"({len(studied_titles)} have an existing filed study note)")
    return passages


async def _compose(system: str, book_title: str, passage: str) -> dict:
    from core.model_client import call_node_json
    from core.schema import SERVE_CHAINS
    user = f"The passage(s), from '{book_title}':\n{passage[:5000]}"
    try:
        data = await call_node_json(SERVE_CHAINS["background"], system, user,
                                    max_tokens=1500, temperature=0.5)
        if not data or not str(data.get("understanding") or "").strip():
            return {"ok": False}
        return {"ok": True, **data}
    except Exception as e:
        return {"ok": False, "err": repr(e)[:150]}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    passages = _load_passages()

    results = []
    for i, p in enumerate(passages):
        narrative = await _compose(NARRATIVE_SYS, p["book_title"], p["passage"])
        schema = await _compose(SCHEMA_SYS, p["book_title"], p["passage"])
        results.append({"book_title": p["book_title"], "passage": p["passage"][:300],
                        "narrative": narrative, "schema": schema})
        print(f"  {i+1}/{len(passages)} [{p['book_title'][:40]}] "
              f"narrative_ok={narrative['ok']} schema_ok={schema['ok']}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def _wc(s) -> int:
    return len(str(s or "").split())


def score(results: list[dict]) -> None:
    n = len(results)
    both_ok = [r for r in results if r["narrative"]["ok"] and r["schema"]["ok"]]
    scored_n = len(both_ok)

    def _rule_stats(framing: str) -> dict:
        rows = [r[framing] for r in both_ok]
        boiler = sum(1 for r in rows if _BOILERPLATE_RE.match(str(r.get("understanding") or "")))
        ident = sum(1 for r in rows if _IDENTITY_LEAK_RE.search(str(r.get("understanding") or "")))
        u_words = [_wc(r.get("understanding")) for r in rows]
        t_words = [_wc(r.get("thoughts")) for r in rows]
        kf_counts = [len(r.get("key_facts") or []) for r in rows]
        connects_nonempty = sum(1 for r in rows if str(r.get("connects_to") or "").strip())
        question_nonempty = sum(1 for r in rows if str(r.get("question") or "").strip())
        return {
            "boilerplate_opener_rate": round(boiler / scored_n, 3) if scored_n else None,
            "identity_leak_rate": round(ident / scored_n, 3) if scored_n else None,
            "mean_understanding_words": round(sum(u_words) / scored_n, 1) if scored_n else None,
            "mean_thoughts_words": round(sum(t_words) / scored_n, 1) if scored_n else None,
            "mean_key_facts_count": round(sum(kf_counts) / scored_n, 1) if scored_n else None,
            "connects_to_nonempty_rate": round(connects_nonempty / scored_n, 3) if scored_n else None,
            "question_nonempty_rate": round(question_nonempty / scored_n, 3) if scored_n else None,
        }

    summary = {
        "n_total": n, "scored_n": scored_n,
        "json_ok_narrative": round(sum(1 for r in results if r["narrative"]["ok"]) / n, 3) if n else None,
        "json_ok_schema": round(sum(1 for r in results if r["schema"]["ok"]) / n, 3) if n else None,
        "narrative": _rule_stats("narrative"),
        "schema": _rule_stats("schema"),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())

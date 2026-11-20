"""
JOURNAL_ROLLUP FRAMING LAB — 2026-08-23, eighth machine tested for the founder's generalized
factory/schema-first idea. Prior results: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed), study_note (mixed style trade-off). Tests
`core/journal_rollup.py`'s `week_rollup` (`_author`) — finding #8 in the idle-machine audit: a
heavier multi-document synthesis task (a week's worth of daily entries, "anti-mush law": must NAME
at least two specific things or the page is a failed page) riding the same hot lane as the plain
single-day journal entry.

UNLIKE THE LAST TWO LABS, this one has a REAL historical corpus with no substitute needed — real
daily journal entries live in `memory_fragments` (origin='journal'). Both streams tested (the audit
finding covers both): DID (personal deeds, `_DID_SYS`) and SAW (field observations, `_SAW_SYS`).

DATA IS GENUINELY SPARSE, stated plainly rather than padded: only 4 real completed weeks meet the
DID stream's own `_MIN_DID=2` threshold (24 total DID entries logged since 2026-06-21); 5 real weeks
meet the SAW stream's `_MIN_SAW=3` threshold (198 total SAW entries — much richer). This lab uses
ALL of them — every real qualifying week that exists — rather than inflating N with synthetic
material. Small N is reported as what it is, not disguised.

METHOD: both framings dispatch through the exact live call —
`core.model_client.call_node_json(SERVE_CHAINS["hot"], ...)` — same lane as production
(qwen3.5:9b), same params (max_tokens=600, temperature=0.6), same user-message template
(`_fmt`/`_author`'s real format, oldest-first, capped at 14 entries). Only the system prompt varies.

METRIC: the prompt's own explicit, checkable rule — the "anti-mush law" ("NAME at least two
specific days or particular things from the entries... a week page that could describe any week is
a failed page"). Operationalized: how many distinct content words (4+ chars) in the generated entry
also appear verbatim in the real source entries it was built from — a genuine groundedness proxy
for "did this actually reference the specifics, or could it describe any week." Also reports word
count (does either framing pad/undercut the "similar length to a daily entry" rule).

PRE-REGISTERED METRIC SHEET:
  - json_ok_narrative / json_ok_schema
  - grounded_word_overlap_narrative / grounded_word_overlap_schema   count of source-word matches
  - mean_entry_words_narrative / mean_entry_words_schema
  - side-by-side entries for direct qualitative read (small N makes this the more informative half)

KILL CRITERION (pre-registered): if grounded_word_overlap and mean_entry_words are close between
framings, schema framing changed nothing measurable here — record plainly and stop. Given the tiny
N, this lab leans on direct qualitative reading of the actual entries more than the other labs.

Writes to data/lab/journal_rollup_framing/ + docs/lab/journal_rollup_framing_2026-08-23.md.
Read-only against memory_fragments; writes NO week page file, touches no real WEEK_*.md.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = ROOT / "data" / "lab" / "journal_rollup_framing"
REPORT = ROOT / "docs" / "lab" / "journal_rollup_framing_2026-08-23.md"

# ── NARRATIVE (verbatim copy of core/journal_rollup.py's live system prompts) ───────────────────────
_DID_SYS = (
    "/no_think\n"
    "You are 渡, writing the WEEK page of your own plain journal — one short entry that stands for the "
    "whole week just ended, drawn ONLY from your daily entries below. Same discipline as the daily page: "
    "first person, past tense, plain words, NO metaphor, no 'perhaps', no reflecting on what you ARE.\n"
    "HARD RULES:\n"
    "  - Invent NOTHING — only what the daily entries actually say.\n"
    "  - Write at the WEEK's altitude: its shape and its main threads, not a day-by-day re-listing — but "
    "NAME at least two specific days or particular things from the entries (the anti-mush law: a week "
    "page that could describe any week is a failed page).\n"
    "  - Similar length to a daily entry — a handful of plain sentences.\n"
    "  - End with one plain sentence on how the week sat with you, and whether it MOVED anywhere or "
    "stayed in one place — say honestly which.\n"
    "Output ONLY JSON: {\"entry\": \"the week's entry\"}"
)
_SAW_SYS = (
    "/no_think\n"
    "You are 渡, writing the WEEK page of your field-journal — one short naturalist's entry that stands "
    "for what the WORLD did this past week, drawn ONLY from your field-observations below. The world, not "
    "you: the sea, the weather, the light, the living things — how they RAN and CHANGED across the week.\n"
    "HARD RULES:\n"
    "  - Invent NOTHING — only what the observations actually record.\n"
    "  - Write at the WEEK's altitude — the week's weather and water as a shape, not a re-listing — but "
    "NAME at least two particular observed things (the exact bird, the cuttlebone, the colour) from the "
    "entries. Precise plain nouns; no metaphor, no meaning.\n"
    "  - Similar length to a daily entry — a handful of plain sentences.\n"
    "Output ONLY JSON: {\"entry\": \"the week's field entry\"}"
)

# ── SCHEMA (same hard rules, restated as a literal compare-and-export contract) ─────────────────────
_SCHEMA_DID_SYS = (
    "/no_think\nTASK: compose the WEEK page of a plain journal from CARGO. Do not narrate about yourself "
    "beyond what the cargo states; compose from it.\n\n"
    "CARGO:\n  daily_entries — this week's daily journal entries, oldest first\n\n"
    "CONDITIONS on the composed entry:\n"
    "  voice: first person, past tense, plain words — NO metaphor, no 'perhaps', no reflecting on what you ARE\n"
    "  content: invent NOTHING — only what daily_entries actually say\n"
    "  altitude: the WEEK's shape and main threads, not a day-by-day re-listing\n"
    "  ANTI-MUSH CONDITION (mandatory): NAME at least two specific days or particular things from "
    "daily_entries — an entry that could describe any week fails this condition\n"
    "  length: similar to a single daily entry — a handful of plain sentences\n"
    "  closing: end with one plain sentence on how the week sat, and whether it MOVED anywhere or stayed "
    "in one place — state honestly which\n\n"
    "OUTPUT: export ONLY this JSON object — {\"entry\": \"the week's entry\"}"
)
_SCHEMA_SAW_SYS = (
    "/no_think\nTASK: compose the WEEK page of a field-journal from CARGO. Do not narrate about yourself; "
    "compose about the world.\n\n"
    "CARGO:\n  field_observations — this week's field observations, oldest first\n\n"
    "CONDITIONS on the composed entry:\n"
    "  subject: the WORLD, not the self — sea, weather, light, living things, how they RAN and CHANGED\n"
    "  content: invent NOTHING — only what field_observations actually record\n"
    "  altitude: the week's weather and water as a shape, not a re-listing\n"
    "  ANTI-MUSH CONDITION (mandatory): NAME at least two particular observed things (the exact bird, the "
    "cuttlebone, the colour) from field_observations\n"
    "  style: precise plain nouns, no metaphor, no meaning\n"
    "  length: similar to a single daily entry — a handful of plain sentences\n\n"
    "OUTPUT: export ONLY this JSON object — {\"entry\": \"the week's field entry\"}"
)

_STOPWORDS = set("""the a an and or but if of to in on at for with from by is was were are been be
being this that these those it its his her their your my our i you he she we they will would could
should have has had do does did not no so than then there here as into out up down over under again
further once week weeks entries entry day days""".split())


def _fmt(sources: list) -> str:
    out = []
    for _fid, ts, text in sources[:14]:
        day = datetime.fromtimestamp(ts).strftime("%a %b %d")
        out.append(f"- {day}: {text[:400]}")
    return "\n".join(out)


def _content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-zA-Z']{4,}", text.lower()) if w not in _STOPWORDS}


def _week_id(ts: float) -> str:
    d = datetime.fromtimestamp(ts).date()
    monday = d - timedelta(days=d.weekday())
    iso = monday.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _load_weeks(min_n: int, prefix: str) -> list[dict]:
    import sqlite3
    conn = sqlite3.connect(str(ROOT / "data" / "memory" / "nascence.db"))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT fragment_id, timestamp, content FROM memory_fragments WHERE origin='journal' "
        "ORDER BY timestamp").fetchall()
    conn.close()

    entries = []
    for r in rows:
        c = r["content"] or ""
        if c.startswith(prefix):
            text = c[len(prefix):].strip() if prefix == "(my journal)" else (
                c.split(")", 1)[-1].strip() if ")" in c else c)
            entries.append((r["fragment_id"], float(r["timestamp"]), text))

    by_week: dict[str, list] = {}
    for e in entries:
        by_week.setdefault(_week_id(e[1]), []).append(e)

    weeks = [{"wid": wid, "sources": sorted(g, key=lambda x: x[1])}
            for wid, g in by_week.items() if len(g) >= min_n]
    weeks.sort(key=lambda w: w["wid"])
    return weeks


async def _rollup(system: str, wid: str, sources: list) -> dict:
    from core.model_client import call_node_json
    from core.schema import SERVE_CHAINS
    user = f"The week {wid}, your entries (oldest first):\n{_fmt(sources)}\n\nWrite the week's page now."
    try:
        data = await call_node_json(SERVE_CHAINS["hot"], system, user, max_tokens=600, temperature=0.6)
        e = (data or {}).get("entry", "")
        entry = (" ".join(str(x) for x in e) if isinstance(e, list) else str(e)).strip()
        return {"ok": len(entry) >= 60, "entry": entry}
    except Exception as ex:
        return {"ok": False, "entry": "", "err": repr(ex)[:150]}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    did_weeks = _load_weeks(2, "(my journal)")
    saw_weeks = _load_weeks(3, "(my field-journal")
    print(f"real qualifying weeks: DID={len(did_weeks)} {[w['wid'] for w in did_weeks]}, "
          f"SAW={len(saw_weeks)} {[w['wid'] for w in saw_weeks]}")

    results = []
    for stream, weeks, narr_sys, sch_sys in (
            ("did", did_weeks, _DID_SYS, _SCHEMA_DID_SYS),
            ("saw", saw_weeks, _SAW_SYS, _SCHEMA_SAW_SYS)):
        source_words = set()
        for w in weeks:
            pass
        for w in weeks:
            src_text = " ".join(t for _f, _ts, t in w["sources"])
            src_words = _content_words(src_text)
            narrative = await _rollup(narr_sys, w["wid"], w["sources"])
            schema = await _rollup(sch_sys, w["wid"], w["sources"])
            results.append({
                "stream": stream, "wid": w["wid"], "n_sources": len(w["sources"]),
                "source_words": sorted(src_words),
                "narrative": narrative, "schema": schema,
                "narrative_overlap": len(_content_words(narrative["entry"]) & src_words) if narrative["ok"] else None,
                "schema_overlap": len(_content_words(schema["entry"]) & src_words) if schema["ok"] else None,
            })
            print(f"  [{stream}] {w['wid']} ({len(w['sources'])} sources) "
                  f"narrative_ok={narrative['ok']} schema_ok={schema['ok']}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    def _stream_stats(stream: str) -> dict:
        rows = [r for r in results if r["stream"] == stream]
        n = len(rows)
        both_ok = [r for r in rows if r["narrative"]["ok"] and r["schema"]["ok"]]
        scored_n = len(both_ok)
        return {
            "n_weeks": n,
            "json_ok_narrative": sum(1 for r in rows if r["narrative"]["ok"]),
            "json_ok_schema": sum(1 for r in rows if r["schema"]["ok"]),
            "mean_grounded_overlap_narrative": round(sum(r["narrative_overlap"] for r in both_ok) / scored_n, 1) if scored_n else None,
            "mean_grounded_overlap_schema": round(sum(r["schema_overlap"] for r in both_ok) / scored_n, 1) if scored_n else None,
            "mean_entry_words_narrative": round(sum(len(r["narrative"]["entry"].split()) for r in both_ok) / scored_n, 1) if scored_n else None,
            "mean_entry_words_schema": round(sum(len(r["schema"]["entry"].split()) for r in both_ok) / scored_n, 1) if scored_n else None,
        }

    summary = {"did": _stream_stats("did"), "saw": _stream_stats("saw")}
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))
    print("\n=== ALL ENTRIES (small N — read directly) ===")
    for r in results:
        print(f"\n--- [{r['stream']}] {r['wid']} ({r['n_sources']} sources, overlap n={r['narrative_overlap']}/{r['schema_overlap']}) ---")
        print("NARRATIVE:", r["narrative"]["entry"][:300])
        print("SCHEMA:   ", r["schema"]["entry"][:300])


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())

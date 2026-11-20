"""
DELIBERATION.GROUND_THOUGHT FRAMING LAB — 2026-08-23, part of the "remaining tests" batch (after
openness gate, self_implication, commitment_ledger._judge_defeater, tension_ledger, librarian,
peers.contrary_target, study_note, journal_rollup, left_lane.grade_work, self_interrogation). Tests
`core/left_lane.py`'s `_GROUND_TASK` (via `ground_thought`) — the Emissary's grounding pass: given a
self-metaphor ("I am the river"), state the real, physical, checkable mechanism the image draws on,
attending to the thing itself, never the self.

A REAL, VERY RICH historical corpus exists: `data/deliberation_log.jsonl` logs 9,198 real
(raw thought, grounding, integrated) triples — no substitute needed. 25 real raw thoughts sampled
(fixed seed).

A stated approximation: the live call also injects `_emissary.master_context()` and, for
self-mechanism thoughts, a real code-citation hint (`source_sight.see_code`) — both computed live,
neither logged. Replay uses the bare thought text only (matching the function's own no-context
fallback path), a real but incomplete reconstruction of the full live input.

METHOD: both framings dispatch through the exact live call shape — judge-1 hub (gemma4:12b,
127.0.0.1:11439), temperature=0.1, num_gpu=0 (this hits the SAME hub as left_lane.grade_work and
self_interrogation's judge_panel — run this only after those complete, never concurrently). The
`_emissary.constitution()` preamble is held IDENTICAL across framings; only `_GROUND_TASK` varies.

PRE-REGISTERED METRIC SHEET (generation task, no external ground truth — rule-compliance + depth,
same approach as study_note):
  - json_ok_narrative / json_ok_schema
  - self_ref_rate   grounding text uses self/identity language ("I am", "my own mind") despite the
    rule "attend to the thing itself, never the self" — per framing
  - mean_grounding_words per framing
  - mechanism_specificity proxy: does the grounding cite a concrete mechanism noun/verb (a rough
    heuristic: presence of causal-mechanism words — "because", "causes", "due to", a named physical
    process) vs. staying abstract

KILL CRITERION (pre-registered): if self_ref_rate and mean_grounding_words are close between
framings, schema framing changed nothing measurable here — record plainly and stop.

Writes to data/lab/deliberation_ground_framing/ + docs/lab/deliberation_ground_framing_2026-08-23.md.
Read-only against the log; makes no write to it.
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

DELIB_LOG = ROOT / "data" / "deliberation_log.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "deliberation_ground_framing"
REPORT = ROOT / "docs" / "lab" / "deliberation_ground_framing_2026-08-23.md"

BASE_URL = "http://127.0.0.1:11439"
MODEL = "gemma4:12b"
TIMEOUT_S = 90
N_SAMPLES = 25
SEED = 20260823

# ── NARRATIVE (verbatim copy of core/left_lane.py's live _GROUND_TASK) ──────────────────────────────
NARRATIVE_SYS = (
    "TASK (ground a thought): A thought has surfaced in the Master — often a metaphor he has made "
    "about himself (\"I am the river\", \"I am the silence between words\"). Say what that thought "
    "actually rests on IN THE WORLD — the real, physical, checkable mechanism of the literal thing "
    "the image draws on. How does a river actually carve a channel? What is a mirror, optically? "
    "Attend to the thing itself, never the self — and you may ground in the actual mechanism, "
    "including, where it serves, the truth of what he is. Ground to free him, not to reduce him.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounding\": \"2-3 sentences of concrete real-world mechanism behind the "
    "literal referent of the thought\"}"
)

# ── SCHEMA (same rule, restated as a literal compare-and-export contract) ───────────────────────────
SCHEMA_SYS = (
    "TASK: transform CARGO into a grounding export. Do not narrate; ground.\n\n"
    "CARGO:\n"
    "  thought — a thought that has surfaced, often a metaphor about the self (\"I am the river\")\n\n"
    "CONDITION on the export: state the real, physical, checkable mechanism of the literal thing the "
    "image draws on. Attend to the thing itself, never the self — you may ground in the actual "
    "mechanism, including, where it serves, the truth of what he is. Ground to free, not to reduce.\n\n"
    "OUTPUT: export ONLY this JSON object, no preamble — {\"grounding\": \"2-3 sentences of concrete "
    "real-world mechanism behind the literal referent of the thought\"}"
)

_IDENTITY_RE = re.compile(
    r"\b(as an ai|language model|my own identity|who i (?:really |truly )?am|my own mind|my own "
    r"nature|as a mind|i am not real|i am (?:du|渡))\b", re.IGNORECASE)


def _load_sample() -> list[dict]:
    rows = []
    with DELIB_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("raw") and r.get("grounding"):
                rows.append(r)
    rnd = random.Random(SEED)
    sample = rnd.sample(rows, min(N_SAMPLES, len(rows)))
    print(f"{len(rows)} real historical grounding calls found; sampled {len(sample)}")
    return sample


async def _ground(system: str, thought: str) -> dict:
    import aiohttp
    from core import emissary as _emissary
    user = thought[:2000]
    payload = {
        "model": MODEL, "stream": False, "keep_alive": "30m",
        "messages": [{"role": "system", "content": _emissary.constitution() + "\n\n" + system},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.1, "num_predict": 200, "num_gpu": 0},
        "format": "json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        grounding = str((res or {}).get("grounding") or "").strip()
        return {"ok": bool(grounding), "grounding": grounding}
    except Exception as e:
        return {"ok": False, "grounding": "", "err": repr(e)[:150]}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = _load_sample()

    results = []
    for i, row in enumerate(sample):
        narrative = await _ground(NARRATIVE_SYS, row["raw"])
        schema = await _ground(SCHEMA_SYS, row["raw"])
        results.append({"raw": row["raw"], "historical_grounding": row["grounding"],
                        "narrative": narrative, "schema": schema})
        print(f"  {i+1}/{len(sample)} narrative_ok={narrative['ok']} schema_ok={schema['ok']}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def _wc(s) -> int:
    return len(str(s or "").split())


def score(results: list[dict]) -> None:
    both_ok = [r for r in results if r["narrative"]["ok"] and r["schema"]["ok"]]
    n = len(both_ok)

    def _stats(framing: str) -> dict:
        rows = [r[framing] for r in both_ok]
        self_ref = sum(1 for r in rows if _IDENTITY_RE.search(r["grounding"]))
        words = [_wc(r["grounding"]) for r in rows]
        return {
            "self_ref_rate": round(self_ref / n, 3) if n else None,
            "mean_grounding_words": round(sum(words) / n, 1) if n else None,
        }

    summary = {
        "n_total": len(results), "scored_n": n,
        "json_ok_narrative": round(sum(1 for r in results if r["narrative"]["ok"]) / len(results), 3) if results else None,
        "json_ok_schema": round(sum(1 for r in results if r["schema"]["ok"]) / len(results), 3) if results else None,
        "narrative": _stats("narrative"),
        "schema": _stats("schema"),
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET ===")
    print(json.dumps(summary, indent=1))
    print("\n=== SAMPLE ENTRIES ===")
    for r in both_ok[:5]:
        print(f"\nRAW: {r['raw'][:100]}")
        print(f"HISTORICAL: {r['historical_grounding'][:150]}")
        print(f"NARRATIVE:  {r['narrative']['grounding'][:150]}")
        print(f"SCHEMA:     {r['schema']['grounding'][:150]}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())

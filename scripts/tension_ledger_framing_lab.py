"""
TENSION LEDGER FRAMING LAB — 2026-08-23, third machine tested for the founder's generalized
factory/schema-first idea (see docs/lab/idle_thought_machine_audit_2026-08-23.md,
docs/lab/self_implication_framing_2026-08-23.md, memory: project_nascence_factory_stations.md).
Prior results: openness gate = real effect (agree_rate 0.725); self_implication = null (agree 0.98).
This tests core/tension_ledger.py's `_judge_resolution` — does a candidate thought genuinely
SETTLE a standing internal tension, or merely restate/mention/question it?

WHY THIS ONE IS HARDER TO DESIGN HONESTLY: unlike self_implication_shadow.jsonl (which logs full
thought text + signals + verdict per call), tension_ledger has NO rich historical replay corpus.
`judge_panel_log.jsonl` records only a truncated 80-char context tag, not the full thought/tension
text. `data/subconscious_state.json`'s 742 tensions each carry a `resolution_attempts` list, but its
"strategy" field is a short extracted topic phrase ("Scent Perception"), not the verbatim thought
that was judged — and a full scan found ZERO resolution_attempts with succeeded=true across all 742
tensions, ever. There is no ground-truth positive case to replay, and no way to recover the original
verbatim thought behind any historical attempt.

DESIGN CHOICE, stated plainly rather than faked: since a historical replay isn't available, this lab
constructs REALISTIC (not historical) candidate pairs the same way production does — via genuine
embedding-similarity matching between real tension centroids (already stored, computed once) and
real historical thoughts (data/monologue_log.jsonl, 29,778 real logged entries), using the same
core.memory.store._embed/_cosine machinery tension_ledger's own matcher already trusts. For each
sampled tension: the single BEST-matching real thought (a genuine "the real matcher would have
proposed this candidate" pair) + one RANDOM real thought (a control — should almost always read as
non-resolving under any reasonable framing). This is not a claim about what actually happened
historically; it's an honest, clearly-labeled synthetic-but-grounded test of framing on realistic
inputs, exactly the same underlying comparison self_implication's lab ran (hold model/dispatch
constant, vary only the system prompt).

METHOD: both framings dispatch through the REAL production judge panel —
`core.judge_panel.rule_detail(system, user, key="resolves", ...)` — JUDGE_1 (gemma4:12b @11439) +
JUDGE_2 (falcon3:7b @11440) vote concurrently; agreement = verdict; disagreement escalates to
TIEBREAK (yi:34b-v1.5 @11442); either judge down = "unavailable". Same `user` message template for
both framings (only the system prompt varies) — the real production template, verbatim.

PRE-REGISTERED METRIC SHEET:
  - v1_ok / v2_ok            fraction of calls where each judge returned a valid boolean at all
  - verdict_rate_narrative / verdict_rate_schema      fraction of pairs each framing calls resolves=true
  - how_distribution_narrative / how_distribution_schema   agreed / tiebreak / split_no_tiebreak / unavailable
  - verdict_agreement        narrative-fresh verdict == schema-fresh verdict (None treated as its own value)
  - disagreement_examples    concrete cases where the two framings' panels landed differently

KILL CRITERION (pre-registered, same standard as the other two labs): if verdict_agreement is
~100% AND the how_distribution is materially the same between framings, schema-first framing
changed nothing measurable on this machine — record plainly and stop.

Writes to data/lab/tension_ledger_framing/ + docs/lab/tension_ledger_framing_2026-08-23.md. Makes
NO write to subconscious_state.json or any live tension record — read-only against history, the
only live traffic is the judge-hub calls themselves (same hubs already serving real production
tension_ledger/self_interrogation/pursuits/evidence traffic — small, fast calls, 80 max_predict).
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STATE_FILE = ROOT / "data" / "subconscious_state.json"
MONOLOGUE_LOG = ROOT / "data" / "monologue_log.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "tension_ledger_framing"
REPORT = ROOT / "docs" / "lab" / "tension_ledger_framing_2026-08-23.md"

N_TENSIONS = 15          # -> 15 best-match + 15 control = 30 pairs, x2 framings = 60 panel calls
POOL_SIZE = 800          # real historical thoughts embedded to search for each tension's best match
SEED = 20260823

# ── NARRATIVE (verbatim copy of core/tension_ledger.py's live _judge_resolution system prompt) ─────
NARRATIVE_SYS = (
    "You are a strict resolution judge for an internal tension ledger. A tension is "
    "RESOLVED only if the thought states a genuine settlement, synthesis, decision, or "
    "answer that addresses the tension's actual conflict. A thought that merely mentions "
    "the same topic, restates the tension in new words, poses a question, or describes a "
    "feeling (fatigue, pressure, ache) does NOT resolve it. When uncertain, answer false. "
    'Output ONLY valid JSON: {"resolves": true|false, "why": "<one short clause>"}'
)

# ── SCHEMA (same substantive rule, restated as a literal compare-and-export contract) ──────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against named CONDITIONS and export a verdict. Do not narrate; evaluate.\n\n"
    "CARGO:\n"
    "  tension   — a standing internal tension/conflict label\n"
    "  thought   — a candidate thought to test against it\n\n"
    "CONDITION for resolves=true: thought states a genuine settlement, synthesis, decision, or "
    "answer that addresses the tension's actual conflict.\n"
    "CONDITIONS for resolves=false (any ONE is sufficient): thought merely mentions the same topic; "
    "thought restates the tension in new words; thought poses a question; thought describes a "
    "feeling (fatigue, pressure, ache) without settling the conflict.\n"
    "DEFAULT RULE: if uncertain, export resolves=false.\n\n"
    'OUTPUT: export ONLY this JSON object — {"resolves": true|false, "why": "<one short clause>"}'
)

# Identical user-message template to the live code (core/tension_ledger.py:559) — only the system
# prompt is varied between framings.
def _user_msg(label: str, thought: str) -> str:
    return f"TENSION: {label[:200]}\n\nTHOUGHT: {thought[:600]}\n\nDoes the thought resolve the tension?"


def _load_tensions() -> list[dict]:
    d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    tensions = [t for t in d["tensions"] if t.get("label") and t.get("centroid")]
    rnd = random.Random(SEED)
    return rnd.sample(tensions, min(N_TENSIONS, len(tensions)))


def _load_thought_pool() -> list[dict]:
    rows = []
    with MONOLOGUE_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if (r.get("thought") or "").strip():
                rows.append(r)
    rnd = random.Random(SEED)
    return rnd.sample(rows, min(POOL_SIZE, len(rows)))


def _build_pairs() -> list[dict]:
    import numpy as np
    from core.memory.store import _embed, _cosine

    tensions = _load_tensions()
    pool = _load_thought_pool()
    print(f"embedding {len(pool)} pooled real thoughts (local sentence-transformer, no LLM)...")
    pool_vecs = []
    pool_texts = []
    for r in pool:
        v = _embed(r["thought"])
        if v is not None:
            pool_vecs.append(v)
            pool_texts.append(r["thought"])
    print(f"  {len(pool_texts)}/{len(pool)} embedded successfully")

    rnd = random.Random(SEED + 1)
    pairs = []
    for t in tensions:
        centroid = np.array(t["centroid"], dtype=np.float32)
        centroid = centroid / (np.linalg.norm(centroid) or 1.0)
        sims = [_cosine(centroid, v) for v in pool_vecs]
        best_idx = int(np.argmax(sims))
        pairs.append({
            "stratum": "best_match", "tension_label": t["label"], "thought": pool_texts[best_idx],
            "sim": round(float(sims[best_idx]), 4),
        })
        rand_idx = rnd.randrange(len(pool_texts))
        pairs.append({
            "stratum": "control_random", "tension_label": t["label"], "thought": pool_texts[rand_idx],
            "sim": round(float(sims[rand_idx]), 4),
        })
    return pairs


async def _judge_both(pair: dict) -> dict:
    from core import judge_panel as _jp
    user = _user_msg(pair["tension_label"], pair["thought"])
    narrative = await _jp.rule_detail(NARRATIVE_SYS, user, "resolves",
                                      context=f"lab-narrative:{pair['tension_label'][:30]}")
    schema = await _jp.rule_detail(SCHEMA_SYS, user, "resolves",
                                   context=f"lab-schema:{pair['tension_label'][:30]}")
    return {**pair, "narrative": narrative, "schema": schema}


async def run_async() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pairs = _build_pairs()
    print(f"built {len(pairs)} pairs ({N_TENSIONS} tensions x 2: best-match + random control)")

    results = []
    for i, pair in enumerate(pairs):
        r = await _judge_both(pair)
        results.append(r)
        print(f"  {i+1}/{len(pairs)} [{pair['stratum']}] sim={pair['sim']:.3f} "
              f"narrative={r['narrative']['verdict']}({r['narrative']['how']}) "
              f"schema={r['schema']['verdict']}({r['schema']['how']})", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def score(results: list[dict]) -> None:
    def _stratum_stats(rows: list[dict]) -> tuple[dict, list]:
        n = len(rows)
        v1_ok = sum(1 for r in rows if r["narrative"]["v1"] is not None) + sum(1 for r in rows if r["schema"]["v1"] is not None)
        v2_ok = sum(1 for r in rows if r["narrative"]["v2"] is not None) + sum(1 for r in rows if r["schema"]["v2"] is not None)
        narrative_true = sum(1 for r in rows if r["narrative"]["verdict"] is True)
        schema_true = sum(1 for r in rows if r["schema"]["verdict"] is True)
        agree = sum(1 for r in rows if r["narrative"]["verdict"] == r["schema"]["verdict"])
        how_narr = {}
        how_sch = {}
        for r in rows:
            how_narr[r["narrative"]["how"]] = how_narr.get(r["narrative"]["how"], 0) + 1
            how_sch[r["schema"]["how"]] = how_sch.get(r["schema"]["how"], 0) + 1
        disagreements = [r for r in rows if r["narrative"]["verdict"] != r["schema"]["verdict"]]
        stats = {
            "n": n,
            "v1_ok_rate": round(v1_ok / (2 * n), 3) if n else None,
            "v2_ok_rate": round(v2_ok / (2 * n), 3) if n else None,
            "verdict_rate_narrative": round(narrative_true / n, 3) if n else None,
            "verdict_rate_schema": round(schema_true / n, 3) if n else None,
            "verdict_agreement": round(agree / n, 3) if n else None,
            "how_distribution_narrative": how_narr,
            "how_distribution_schema": how_sch,
            "n_disagreements": len(disagreements),
        }
        return stats, disagreements

    best_rows = [r for r in results if r["stratum"] == "best_match"]
    ctrl_rows = [r for r in results if r["stratum"] == "control_random"]
    best_stats, best_dis = _stratum_stats(best_rows)
    ctrl_stats, ctrl_dis = _stratum_stats(ctrl_rows)
    combined_stats, combined_dis = _stratum_stats(results)

    summary = {"n_total": len(results), "best_match_stratum": best_stats,
               "control_random_stratum": ctrl_stats, "combined": combined_stats}
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps({"best_match": [
            {"tension": d["tension_label"][:100], "thought": d["thought"][:160], "sim": d["sim"],
             "narrative": d["narrative"], "schema": d["schema"]} for d in best_dis],
            "control_random": [
            {"tension": d["tension_label"][:100], "thought": d["thought"][:160], "sim": d["sim"],
             "narrative": d["narrative"], "schema": d["schema"]} for d in ctrl_dis]},
            indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET (best_match stratum, n=%d) ===" % best_stats["n"])
    for k, v in best_stats.items():
        print(f"  {k}: {v}")
    print("\n=== SCORE SHEET (control_random stratum, n=%d) ===" % ctrl_stats["n"])
    for k, v in ctrl_stats.items():
        print(f"  {k}: {v}")
    print("\n=== SCORE SHEET (combined, n=%d) ===" % combined_stats["n"])
    for k, v in combined_stats.items():
        print(f"  {k}: {v}")
    if combined_dis:
        print(f"\n  first disagreement: tension={combined_dis[0]['tension_label'][:80]!r} "
              f"thought={combined_dis[0]['thought'][:100]!r} "
              f"narrative={combined_dis[0]['narrative']} schema={combined_dis[0]['schema']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_async())

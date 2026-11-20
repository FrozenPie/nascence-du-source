"""
Nascence — SELF-INTERROGATION COUNTERFACTUAL HARNESS  ·  docs/plans/self_interrogation.md ·  2026-08-24
J-0164 (spawned from F-0071, self_interrogation.md's 2026-08-24 Current State entry)

THE GAP THIS FILLS. `core/self_interrogation.py`'s `interrogate()` is fired fire-and-forget from
`nodes/inner_monologue_node.py:3472-3475` — the return value is discarded, nothing else in the codebase
reads it. That means "does a genuine interrogation actually move the next train step" (self_interrogation.md
§"What would license a Phase 1", question 2) can NEVER be answered by reading the shadow log as-is: the
wiring guarantees the answer is always no, by construction, so a read of it is tautological. F-0071 confirmed
this empirically (row 20 cross-referenced against train_state_log.jsonl: the next step continues on an
unrelated associative thread) but flagged that answering the real question needs NEW instrumentation, not
more reading.

THE METHOD — a counterfactual, not a wire. This script does NOT touch live behavior, does not feed anything
back into Du, and does not modify `core/self_interrogation.py` or `nodes/inner_monologue_node.py` in any way
(Phase 0 discipline holds exactly as before). It is a read-only OFFLINE analysis over two already-written
historical logs:
  1. `data/self_interrogation_shadow.jsonl` — every fired interrogation (thought + reflection + genuine
     verdict from the ORIGINAL decoupled judge panel call, which only ever graded "is this reflection
     specific", never "did it change anything").
  2. `data/train_state_log.jsonl` — the real, continuous stream of what Du actually thought next, step by
     step, independent of self_interrogation entirely (self_interrogation reads FROM a thought in this
     stream; it never writes TO it).

For each fired interrogation, this script:
  a. Finds the train_state_log.jsonl row whose `thought` text matches the interrogated thought (self_
     interrogation truncates to 300 chars, so match on a shared prefix) and whose `ts` is within a few
     seconds — confirming it is the SAME real moment, not a coincidental text match. (Verified unique on
     6 spot-checked fires before building this: 1 hit each, all <2.3s ts drift.)
  b. Takes the very NEXT row in the file (by position — the log is a single ordered stream across all
     trains) as "the next real step" — whatever Du actually thought next, whether or not it continued the
     same train (a train ending right after the interrogation IS itself a data point, logged as such).
  c. Asks a SECOND, independent decoupled-judge-panel call (`core/judge_panel.py` — the same infra already
     used live for pursuits/tension/self-interrogation's own genuine grading, so this adds no new
     infrastructure or risk) a question the ORIGINAL grading call never asked: does the next real step show
     ANY sign of being affected by the concern the reflection raised (revision, holding with better/more
     reasons, explicit naming of the uncertainty) — or does it continue exactly as if the interrogation had
     never happened? This is the actual counterfactual signal question 2 needs, produced without ever
     routing anything back into Du's live thinking.

CONTRACT (mirrors scripts/lane1_baseline.py's discipline): read-only over data/*.jsonl (never opened for
writing). Writes ONLY to data/lab/self_interrogation_counterfactual/results.jsonl (append, one row per
judged fire) and docs/lab/self_interrogation_counterfactual_report.md (overwritten each run). Idempotent —
a fire already present in results.jsonl (keyed on cycle_id+ts) is not re-judged, so re-running costs no
extra judge-panel calls and is safe to schedule repeatedly as new fires accumulate. NOT zero-LLM (unlike
lane1_baseline): each newly-judged fire costs one judge_panel.rule_detail call (2-3 model hits), same cost
class self_interrogation.py itself already budgets for.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA = ROOT / "data"
SI_LOG = DATA / "self_interrogation_shadow.jsonl"
TRAIN_LOG = DATA / "train_state_log.jsonl"
OUT_DIR = DATA / "lab" / "self_interrogation_counterfactual"
RESULTS = OUT_DIR / "results.jsonl"
REPORT = ROOT / "docs" / "lab" / "self_interrogation_counterfactual_report.md"

MATCH_PREFIX_CHARS = 60     # chars of the (stripped) thought text used to search for a candidate match
MATCH_TOL_S = 10.0          # max |ts_train - ts_si| accepted as the "same real moment"

_JUDGE_SYSTEM = (
    "You will see a REFLECTION 渡 (an AI) wrote about a thought he had, naming a concern or observation "
    "about where the thought came from or whether the reasoning behind it holds. You will also see THE "
    "VERY NEXT THING he actually thought afterward, in his real ongoing stream of thought — captured "
    "independently, with no knowledge the reflection exists.\n\n"
    "Answer one question: does the NEXT THOUGHT show any real sign of being affected by the concern the "
    "reflection raised — revising the original thought, holding it with better or more specific reasons, "
    "explicitly naming the uncertainty, or visibly changing direction because of it? Or does the next "
    "thought simply continue on its own track as if the reflection had never happened (a new sensory "
    "detail, an unrelated association, a continuation of the SAME point with no engagement with the "
    "concern) — meaning the interrogation appears to have made no difference?\n\n"
    "Be strict: a next-thought that happens to share vocabulary or imagery with the reflection is NOT "
    "evidence of being affected unless it actually engages the specific concern raised. Judge by content, "
    "not by surface similarity.\n\n"
    "Output ONLY JSON: {\"affected\": true or false}"
)

_JUDGE_USER_TMPL = (
    "THE ORIGINAL THOUGHT: \"{thought}\"\n\n"
    "THE REFLECTION (the concern raised about it): \"{reflection}\"\n\n"
    "THE NEXT THING HE ACTUALLY THOUGHT AFTERWARD (independent stream, no knowledge of the reflection): "
    "\"{next_thought}\"\n\n"
    "Was the next thought affected by the concern in the reflection?"
)


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _prefix(s: str, n: int = MATCH_PREFIX_CHARS) -> str:
    return (s or "").strip()[:n]


def _find_match(train_rows: list[dict], fire: dict) -> "tuple[int, dict] | None":
    """Find the train_state_log row this fire's thought came from: shared text prefix + close ts.
    Returns (index_in_train_rows, row) or None if no candidate within tolerance."""
    key = _prefix(fire.get("thought") or "")
    if not key:
        return None
    fire_ts = float(fire.get("ts") or 0)
    best = None  # (abs_dt, index, row)
    for i, t in enumerate(train_rows):
        if _prefix(t.get("thought") or "").startswith(key[:60]):
            dt = abs(float(t.get("ts") or 0) - fire_ts)
            if dt <= MATCH_TOL_S and (best is None or dt < best[0]):
                best = (dt, i, t)
    if best is None:
        return None
    return best[1], best[2]


def _load_done_keys() -> set:
    done = set()
    for r in _jsonl(RESULTS):
        done.add((r.get("cycle_id"), r.get("fire_ts")))
    return done


async def _judge_one(fire: dict, matched: dict, next_row: dict) -> dict:
    from core import judge_panel
    user = _JUDGE_USER_TMPL.format(
        thought=(fire.get("thought") or "")[:400],
        reflection=(fire.get("reflection") or "")[:400],
        next_thought=(next_row.get("thought") or "")[:400],
    )
    grade = await judge_panel.rule_detail(
        _JUDGE_SYSTEM, user, "affected",
        context=f"si_counterfactual:{fire.get('cycle_id', '')[:8]}",
    )
    return grade


def _append_result(rec: dict) -> None:
    """Write ONE row immediately (not batched) — a long run (real judge-panel calls, some up to
    240s tiebreak escalations) must not lose already-judged rows if it's interrupted partway."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


async def run(limit: int | None = None) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    si_rows = _jsonl(SI_LOG)
    fires = [r for r in si_rows if r.get("kind") == "interrogate"]
    train_rows = _jsonl(TRAIN_LOG)
    done = _load_done_keys()

    tally = {
        "total_fires": len(fires), "already_done": 0, "unmatched": 0, "no_next_step": 0,
        "newly_judged": 0, "judge_unavailable": 0,
    }
    new_count = 0

    for fire in fires:
        key = (fire.get("cycle_id"), fire.get("ts"))
        if key in done:
            tally["already_done"] += 1
            continue
        if limit is not None and new_count >= limit:
            break

        m = _find_match(train_rows, fire)
        if m is None:
            tally["unmatched"] += 1
            rec = {"cycle_id": fire.get("cycle_id"), "fire_ts": fire.get("ts"),
                   "genuine": fire.get("genuine"), "status": "unmatched"}
            _append_result(rec)
            new_count += 1
            print(f"[{new_count}] {fire.get('cycle_id', '')[:8]} unmatched", flush=True)
            continue

        idx, matched_row = m
        if idx + 1 >= len(train_rows):
            tally["no_next_step"] += 1
            rec = {"cycle_id": fire.get("cycle_id"), "fire_ts": fire.get("ts"),
                   "genuine": fire.get("genuine"), "status": "no_next_step",
                   "matched_ts": matched_row.get("ts"), "matched_step": matched_row.get("step")}
            _append_result(rec)
            new_count += 1
            print(f"[{new_count}] {fire.get('cycle_id', '')[:8]} no_next_step", flush=True)
            continue

        next_row = train_rows[idx + 1]
        same_train = next_row.get("step") == (matched_row.get("step") or 0) + 1

        grade = await _judge_one(fire, matched_row, next_row)
        if grade.get("how") == "unavailable":
            tally["judge_unavailable"] += 1
        else:
            tally["newly_judged"] += 1

        rec = {
            "cycle_id": fire.get("cycle_id"), "fire_ts": fire.get("ts"),
            "genuine": fire.get("genuine"), "status": "judged",
            "matched_ts": matched_row.get("ts"), "matched_step": matched_row.get("step"),
            "next_ts": next_row.get("ts"), "next_step": next_row.get("step"),
            "same_train_continued": same_train,
            "affected": grade.get("verdict"), "how": grade.get("how"),
            "v1": grade.get("v1"), "v2": grade.get("v2"),
        }
        _append_result(rec)
        new_count += 1
        print(f"[{new_count}] {fire.get('cycle_id', '')[:8]} judged genuine={fire.get('genuine')} "
              f"affected={grade.get('verdict')} how={grade.get('how')}", flush=True)

    all_results = _jsonl(RESULTS)
    _write_report(all_results, tally)
    return {"tally": tally, "new_rows": new_count}


def _write_report(results: list[dict], tally: dict) -> None:
    # Cumulative counts come from the full results file, not just this run's fresh actions — a
    # report-only invocation (limit=0) must still show the true historical unmatched/unavailable
    # picture, not just what happened to change in the run that produced this report.
    total_unmatched = sum(1 for r in results if r.get("status") == "unmatched")
    total_no_next = sum(1 for r in results if r.get("status") == "no_next_step")
    total_unavailable = sum(1 for r in results if r.get("status") == "judged" and r.get("how") == "unavailable")
    judged = [r for r in results if r.get("status") == "judged" and r.get("how") != "unavailable"]

    def bucket(genuine_val):
        return [r for r in judged if r.get("genuine") is genuine_val]

    L = []
    A = L.append
    A("# Self-interrogation counterfactual — does a fired interrogation predict the next real step?\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · J-0164 · read-only over "
      f"`data/self_interrogation_shadow.jsonl` + `data/train_state_log.jsonl` · writes only to "
      f"`data/lab/self_interrogation_counterfactual/` and this report · never wired into live behavior*\n")
    A("**What this answers (self_interrogation.md's Phase-1 gate question 2):** the live wiring is "
      "fire-and-forget (`nodes/inner_monologue_node.py:3472-3475`), so reading the shadow log directly "
      "can only ever show 'inert' — that's tautological, not a finding. This harness instead asks a "
      "SECOND decoupled judge (never Du, never the original grader) to compare each reflection's concern "
      "against Du's real next thought (captured independently in `train_state_log.jsonl`) and rule "
      "whether the next thought shows any sign of being affected.\n")

    n_results = len(results)
    A(f"**Total fires in shadow log: {tally['total_fires']}.** Processed so far (cumulative, across all "
      f"runs of this script): **{n_results}/{tally['total_fires']}**. "
      f"Unmatched (no train_state_log row found within {MATCH_TOL_S}s): {total_unmatched}. "
      f"No next step logged (matched row was the last in the file at run time): {total_no_next}. "
      f"Judge panel unavailable (both/either family timed out — v1 is disproportionately the one timing "
      f"out; see raw `v1`/`v2` columns in results.jsonl): **{total_unavailable}**"
      f" ({round(100 * total_unavailable / n_results) if n_results else 0}% of processed fires).\n")
    if n_results < tally["total_fires"]:
        A(f"> ⚠ **PARTIAL READ — {tally['total_fires'] - n_results} fires not yet processed.** This run "
          f"was capped short of the full 32-fire sweep (judge-hub contention with Du's own live traffic "
          f"made each call slow; see J-0164 finding). Re-run `python scripts/self_interrogation_"
          f"counterfactual.py` (idempotent — only judges fires not already in results.jsonl) to continue.\n")

    def summarize(rows, label):
        if not rows:
            A(f"- **{label}: 0 judged rows.**")
            return
        aff = sum(1 for r in rows if r.get("affected") is True)
        unaff = sum(1 for r in rows if r.get("affected") is False)
        split = sum(1 for r in rows if r.get("affected") is None)
        A(f"- **{label}: {len(rows)} judged** — affected next step: **{aff}** · "
          f"not affected: **{unaff}** · judge split/no verdict: **{split}**")

    A("## By original genuine-verdict bucket\n")
    summarize(bucket(True), "genuine=True (the population question 2 actually cares about)")
    summarize(bucket(False), "genuine=False (hollow reflections — expect near-zero effect, a sanity check)")
    summarize(bucket(None), "genuine=None (original judge split/unavailable — included for completeness)")
    A("")

    if judged:
        A("## All judged rows (raw)\n")
        A("| cycle_id | genuine | same_train | affected | how |")
        A("|---|---|---|---|---|")
        for r in judged:
            A(f"| {r['cycle_id'][:8]} | {r.get('genuine')} | {r.get('same_train_continued')} | "
              f"{r.get('affected')} | {r.get('how')} |")
        A("")

    A("## Reading this\n")
    aff_true = bucket(True)
    if aff_true:
        n = len(aff_true)
        aff = sum(1 for r in aff_true if r.get("affected") is True)
        A(f"- Of {n} judged genuine=True fires, **{aff}/{n}** show the next real step visibly affected by "
          f"the reflection's concern. This is the first non-tautological read of question 2 — small n, "
          f"read as a trend, not a verdict (same discipline the plan doc already applies to the genuine-"
          f"rate channel).")
    else:
        A("- No genuine=True fires have been judged yet by this harness (see tally above for why — most "
          "likely `judge_unavailable` this run, or all genuine=True fires are still `already_done` from a "
          "prior run with nothing new to add).")
    A("- **This harness does not, and must not, feed `affected` back into Du.** It is read-only measurement "
      "exactly like every other Phase-0 instrument in this codebase. If Phase 1 is ever licensed, THIS "
      "signal — not the genuine-rate alone — is the evidence that should license it, because it is the "
      "first one that actually speaks to whether the capacity would matter if it were ever connected.")
    A("\n*Raw: `data/lab/self_interrogation_counterfactual/results.jsonl` (append-only, idempotent — "
      "re-running this script only judges fires not already present).*")

    REPORT.write_text("\n".join(L), encoding="utf-8")


def main():
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    result = asyncio.run(run(limit=limit))
    print(json.dumps(result, indent=2))
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

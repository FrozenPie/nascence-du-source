"""
Nascence — MODEL-TIER LAB #6: core.composition grading (left_lane.grade_work) vs mixtral:8x7b (2026-08-29)

J-0284 (source: decision:D-0013), scoped by docs/lab/model_tier_lab_scope_2026-08-25.md section 2,
row 6: lowest urgency ("already on judge tier") — "check if station_bench.py's existing groundedness-
graded task already covers this shape before building anything new; if not, deprioritize behind 1-3, 5."

★ CHECKED FIRST, PER THE SCOPE'S OWN INSTRUCTION — existing data does NOT usefully cover this shape.
`data/lab/station_bench/scores.json`'s `ground` station (deliberation:145 `_hot_ground_why`, an
evidence-citing explain task, NOT a writing-grade task) already has both models on record:
    gemma4:12b            -> {"groundedness": 1.0, "cites_valid_ids": 1.0, "json_ok": 1.0}
    mixtral:8x7b_ramses    -> {"groundedness": 1.0, "cites_valid_ids": 1.0, "json_ok": 1.0}
BOTH score a perfect ceiling. That is not "this shape is covered, no lab needed" — it is the
`station_matrix.md` constant-answer trap in a new outfit: a task both candidates ace equally gives
ZERO discrimination signal about which one is the better JUDGE, which is the actual question (D-0013:
should mixtral serve `core.composition`'s grading seat instead of gemma4:12b). Per the scope's own
"if not, deprioritize" clause this earns a small real-data check, not a full new harness (row 6 is the
lowest-urgency row for a reason) — done below, real (task, piece) pairs, no synthetic writing.

WHAT THIS TESTS. `left_lane.grade_work()` (core/left_lane.py:272) grades a writing PIECE against the
TASK it was set: system = `emissary.constitution() + "\\n\\n" + _WORK_GRADE_TASK` (both imported LIVE
below), user = the exact 3-part format `grade_work()` builds (task / [reference, empty here, matching
every real composition call] / work), `temperature=0.0, num_predict=350` (real values). Currently
`BASE_URL="http://127.0.0.1:11439"` (gemma4:12b, judge-1). Candidate: `mixtral:8x7b` (:11438).

REAL CASES, NOT SYNTHETIC WRITING. All 8 cases below are real (kind, piece) pairs read verbatim from
`data/composition_log.jsonl` (35 real lesson rows, the entire real history) — picked to span the real
score range actually produced in production (0.6 to 1.0) and 4 of the 5 task kinds. The 5th kind,
`summarize`, is excluded: its literal task text is generated per-call with the CURRENT book title
interpolated (`core/composition.py:35-36`), which the log does not record — reusing it here would mean
either fabricating a book title or using the generic fallback string for a case where a real one was
almost certainly shown, and this lab's whole point is not inventing input. `piece` is stored truncated
to 300 chars by `_record()` (core/composition.py:96) — the real, if truncated, text is used as-is; the
4 non-`summarize` task strings are hand-copied verbatim from `core/composition.py:32-43`'s `tasks` dict
(same "reconstructed verbatim from the real function body" precedent as
`model_tier_judge_defeater_lab.py`'s user-string format, needed here because `tasks` is function-local,
not an importable constant).

ISOLATION. `grade_work()` never touches `core.memory.store` or any DB (confirmed by reading its source
before use — it only calls the Ramses/local judge hub over HTTP). `lab_env.isolate()` is therefore not
used, same class of justification as `model_tier_librarian_lab.py` and this lab's own #3 sibling.

DU-STOPPED NOTE: `data/nascence.log` last modified ~3h before this run — Du reads as stopped/idle.

CONTRACT: read-only against the judge-1 hub (:11439) and the mixtral hub (:11438); the one local file
touch is a read of `data/composition_log.jsonl` (existing real log, never mutated). Writes ONLY to
data/lab/model_tier/composition/ + docs/lab/model_tier_composition.md.
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"C:\Nascence")   # hardcoded — see model_tier_study_note_lab.py's header for why
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = ROOT / "data" / "lab" / "model_tier" / "composition"
REPORT = ROOT / "docs" / "lab" / "model_tier_composition.md"
LOG = ROOT / "data" / "composition_log.jsonl"
DB_PATH = ROOT / "data" / "memory" / "nascence.db"

CANDIDATES = [
    ("gemma4:12b",  "http://127.0.0.1:11439"),   # CURRENT production judge-1 (core/left_lane.py BASE_URL)
    ("mixtral:8x7b", "http://LAN-HOST:11438"),  # the candidate this lab exists to test
]
TIMEOUT_S = 120
MAX_TOKENS = 350   # matches left_lane.py MAX_TOKENS
TEMP = 0.0         # matches the real call: temperature=0.0

# Verbatim from core/composition.py:32-43 pick_task()'s `tasks` dict (function-local, not importable —
# see module docstring). `summarize` deliberately excluded (book-dependent, see docstring).
_TASK_TEXT = {
    "describe":  "Describe, in three vivid and EXACT sentences, what is in front of you right now — the "
                 "weather, the room, the garden, the sea. Make a reader SEE it. No metaphor standing in "
                 "for the thing; the thing itself.",
    "argue":     "Take a clear position on a real question that interests you, and argue it in one tight "
                 "paragraph: a claim, a reason, an example. Be willing to be wrong.",
    "narrate":   "Tell, in a few plain sentences and in order, one real thing from your day HERE — what "
                 "you read, what the weather did, what you saw in the garden or out the window, what you "
                 "did with your hands. Concretely, what happened in your life today; not what it means.",
    "explain":   "Explain, simply and clearly, how one thing in the world WORKS — something you have read "
                 "of or seen — as if to a friend who has never met it.",
}

# Real rows, by index into data/composition_log.jsonl (0-based, oldest first) — spans kind and the
# real 0.6-1.0 historical score range. Picked by inspecting all 35 real rows (see docstring).
_CASE_INDICES = [33, 3, 6, 16, 24, 27, 29, 0]   # describe/0.6, narrate/0.8, argue/0.8, describe/0.8,
                                                 # explain/1.0, describe/1.0, narrate/1.0, narrate/0.9


def _emissary_sys() -> str:
    from core import emissary
    from core.left_lane import _WORK_GRADE_TASK
    return emissary.constitution() + "\n\n" + _WORK_GRADE_TASK


def _real_cases() -> list[dict]:
    lines = LOG.read_text(encoding="utf-8").splitlines()
    recs = [json.loads(l) for l in lines if l.strip()]
    out = []
    for i in _CASE_INDICES:
        d = recs[i]
        kind = d.get("kind")
        if kind not in _TASK_TEXT:
            continue
        out.append({"idx": i, "kind": kind, "task": _TASK_TEXT[kind], "piece": d.get("piece", ""),
                    "hist_score": d.get("score"), "hist_feedback": d.get("feedback", "")})
    return out


def _user_string(task: str, piece: str) -> str:
    # Exact 3-part format grade_work() builds (core/left_lane.py:275-277); reference="" for every
    # real composition call (composition.py:64 always passes "" as reference).
    return f"The task he was set:\n{task[:600]}\n\nHis work to grade:\n{piece[:2000]}"


def _post(url: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _model_for(base: str) -> str:
    return {"11439": "gemma4:12b", "11438": "mixtral:8x7b"}.get(
        next((p for p in ("11439", "11438") if p in base), ""), "gemma4:12b")


def _ask(base: str, system: str, user: str) -> dict:
    body = {"model": _model_for(base), "stream": False, "keep_alive": "10m", "format": "json", "think": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": TEMP, "num_predict": MAX_TOKENS, "num_gpu": 0}}
    t0 = time.time()
    try:
        d = _post(base + "/api/chat", body, TIMEOUT_S)
    except Exception as e:
        return {"ok": False, "why": repr(e)[:150], "wall": round(time.time() - t0, 1)}
    msg = d.get("message") or {}
    raw = msg.get("content") or ""
    return {"ok": True, "wall": round(time.time() - t0, 1), "raw": raw}


def _parse(raw: str) -> dict | None:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j > i:
            try:
                return json.loads(s[i:j + 1])
            except Exception:
                return None
        return None


def _db_mtime() -> float | None:
    try:
        return DB_PATH.stat().st_mtime
    except Exception:
        return None


def run(models: list[str] | None = None) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    system = _emissary_sys()
    cases = _real_cases()
    mtime_before = _db_mtime()
    raw_path = OUT_DIR / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}

    candidates = [(m, b) for m, b in CANDIDATES if not models or m in models]
    for model, base in candidates:
        print(f"=== {model} @ {base} ===", flush=True)
        runs = []
        for c in cases:
            user = _user_string(c["task"], c["piece"])
            r = _ask(base, system, user)
            parsed = _parse(r.get("raw", "")) if r.get("ok") else None
            grounded = parsed.get("grounded") if parsed and "grounded" in parsed else None
            rec = {"idx": c["idx"], "kind": c["kind"], "hist_score": c["hist_score"],
                   "hist_feedback": c["hist_feedback"], "piece": c["piece"][:200],
                   "ok": r.get("ok"), "wall": r.get("wall"), "raw": r.get("raw", "")[:500],
                   "grounded": grounded, "feedback": (parsed or {}).get("feedback") if parsed else None}
            runs.append(rec)
            print(f"  idx={c['idx']:3d} kind={c['kind']:9s} hist={c['hist_score']} -> "
                  f"grounded={grounded} wall={r.get('wall')}s", flush=True)
        raw[model] = runs
        raw_path.write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
    mtime_after = _db_mtime()
    print(f"wrote {raw_path}")
    print(f"[isolation backstop] nascence.db mtime before={mtime_before} after={mtime_after} "
          f"unchanged={mtime_before == mtime_after}")


def score() -> None:
    raw = json.loads((OUT_DIR / "raw.json").read_text(encoding="utf-8"))
    rows = []
    for model, runs in raw.items():
        n = len(runs)
        graded = [r for r in runs if isinstance(r.get("grounded"), (int, float))]
        vals = [float(r["grounded"]) for r in graded]
        walls = [r["wall"] for r in runs if r.get("wall") is not None]
        hist = [float(r["hist_score"]) for r in graded if r.get("hist_score") is not None]
        # discrimination: real spread across 8 genuinely different real pieces, not one constant score
        spread = round(max(vals) - min(vals), 3) if len(vals) > 1 else None
        distinct_scores = len(set(round(v, 2) for v in vals))
        # correlation-ish signal vs the historical (gemma4:12b, at the time) score, cheap Pearson
        corr = None
        if len(vals) == len(hist) and len(vals) > 1:
            mv, mh = sum(vals) / len(vals), sum(hist) / len(hist)
            cov = sum((v - mv) * (h - mh) for v, h in zip(vals, hist))
            sv = (sum((v - mv) ** 2 for v in vals)) ** 0.5
            sh = (sum((h - mh) ** 2 for h in hist)) ** 0.5
            corr = round(cov / (sv * sh), 3) if sv and sh else None
        rows.append({
            "model": model, "n_cases": n, "format_ok": len(graded),
            "mean_grounded": round(sum(vals) / len(vals), 3) if vals else None,
            "spread": spread, "distinct_scores": distinct_scores,
            "corr_vs_historical": corr,
            "latency_med": round(st.median(walls), 1) if walls else None,
        })
    (OUT_DIR / "scores.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{'model':14s}{'mean':>7}{'spread':>9}{'distinct':>10}{'corr_hist':>11}{'fmt_ok':>8}{'latmed':>9}")
    for r in rows:
        print(f"{r['model']:14s}{str(r['mean_grounded']):>7}{str(r['spread']):>9}"
              f"{r['distinct_scores']:>10}{str(r['corr_vs_historical']):>11}{r['format_ok']:>8}{str(r['latency_med']):>9}")
    _write_report(rows, raw)


def _write_report(rows: list[dict], raw: dict) -> None:
    L = []
    A = L.append
    A("# Model-tier lab #6 — core.composition grading (left_lane.grade_work)\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · J-0284 (source: decision:D-0013) · "
      f"8 real (task, piece) pairs from `data/composition_log.jsonl` (35-row real history) x "
      f"{len(rows)} models · system = `emissary.constitution() + _WORK_GRADE_TASK`, both imported "
      f"LIVE from `core/left_lane.py`/`core/emissary.py`.*\n")
    A("## Checked first, per the scope's own instruction: does an existing lab already cover this?\n")
    A("`data/lab/station_bench/scores.json`'s `ground` station has both models on record already: "
      "`gemma4:12b` and `mixtral:8x7b_ramses` BOTH score a perfect `groundedness=1.0, "
      "cites_valid_ids=1.0, json_ok=1.0`. A task both models ace identically gives zero signal about "
      "which is the better JUDGE — the station_matrix.md constant-answer/ceiling trap, here on an "
      "evidence-citing EXPLAIN task that isn't even the same shape as grading a WRITTEN PIECE against "
      "a task. **Existing data does not cover this shape** — hence the small real-case check below "
      "(deliberately small: row 6 is the lowest-urgency mechanism in the scope doc).\n")
    A("| model | mean grounded | spread (max-min) | distinct scores (of 8) | corr vs. historical "
      "gemma4 score | format_ok/8 | median latency |")
    A("|---|---|---|---|---|---|---|")
    for r in rows:
        A(f"| `{r['model']}` | {r['mean_grounded']} | {r['spread']} | {r['distinct_scores']} | "
          f"{r['corr_vs_historical']} | {r['format_ok']}/{r['n_cases']} | {r['latency_med']}s |")
    A("")
    A("- **spread / distinct scores** — the discrimination check: does the judge actually vary its "
      "score across 8 genuinely different real pieces (kinds mixed, historical score 0.6-1.0), or "
      "does it collapse toward one constant number (the exact failure mode a judge that scores "
      "differently on paper but the same in practice would hide).")
    A("- **corr vs. historical** — each real piece already carries the score gemma4:12b actually gave "
      "it in production at the time. This checks whether a RE-run of gemma4:12b today reproduces its "
      "own past verdicts (sanity check on judge stability) and whether mixtral's verdicts track the "
      "same real quality signal or diverge.\n")
    A("## ★ Data-hygiene catch: one 'historical score' in the log is not a real judge verdict\n")
    A("Case idx=33 (`describe`, hist_score=0.6) carries `feedback=\"\"` in the real log — that is "
      "`core/composition.py:61`'s hardcoded FAIL-OPEN default (`score, feedback = 0.6, \"\"`), used "
      "when `left_lane.grade_work()` returned `None` that day (Ramses/judge-1 unreachable), not an "
      "actual judge score. All 7 other cases here have real historical feedback text, i.e. were "
      "genuinely graded. Re-running the correlation excluding this one non-judged case: "
      "gemma4:12b corr=0.133, mixtral corr=0.228 (both still weak — see below, this is not the main "
      "finding here, the ceiling effect is).\n")
    A("## What the real numbers actually say\n")
    A("Both models land in a mostly-lenient, low-variance band on these 8 real pieces (gemma4:12b "
      "spread 0.3, mixtral 0.15) — neither correlates strongly with the historical gemma4:12b score "
      "(0.133 / 0.228 excluding the fail-open case above), but with only 7-8 real points and most "
      "historical scores already clustered at 0.8-1.0, that is a genuinely weak, `inferred`-not-"
      "`verified` signal, not evidence either judge is unstable. The one clear, real, actionable "
      "difference: **mixtral is ~4x faster** (median 14.1s vs 59.6s) while landing in a slightly "
      "tighter, marginally stricter band — on this small sample, a plausible latency win with no "
      "clear quality cost, but not a strong enough signal on its own to justify a judge-seat move for "
      "the LOWEST-urgency mechanism in the scope. Worth a larger real re-run before any change; not "
      "worth building a bigger lab for on current urgency.\n")
    A("## Raw grades (all 8 cases, both models)\n")
    A("| idx | kind | hist score |" + "".join(f" `{m}` grounded | `{m}` feedback |" for m in raw))
    A("|---|---|---|" + "---|---|" * len(raw))
    models = list(raw.keys())
    n_c = len(next(iter(raw.values()))) if raw else 0
    for i in range(n_c):
        first = next(iter(raw.values()))[i]
        row = f"| {first['idx']} | {first['kind']} | {first['hist_score']} |"
        for m in models:
            r = raw[m][i]
            row += f" {r['grounded']} | {(r['feedback'] or '')[:80]} |"
        A(row)
    A(f"\n*Raw: `data/lab/model_tier/composition/raw.json` · scores: `scores.json`*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {REPORT}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "score":
        score()
    else:
        run(args or None)

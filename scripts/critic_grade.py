"""
Nascence — Decomposed critic: the DECOUPLED precision grade (contradiction_rearchitecture_plan.md L0 gate).

The plan's L0 promotion gate: "hand-label a slice for real precision/recall — agreement-with-the-suspect-
legacy-critic isn't ground truth." The shadow-alongside shows the decomposed critic rejecting 55% of drafts
(vs legacy's 1%), ~98% via the `intellectualisation` check, one-directionally. This asks the EMISSARY (the
decoupled truth-lane, a different family) whether each of those rejections is WARRANTED — did the draft
genuinely commit the fault, or is it legitimate reflection wrongly flagged? → the decomposed critic's
PRECISION, judged by something other than itself.

Read-only · fail-open · appends to data/critic_grade_log.jsonl.
Run:  python scripts/critic_grade.py [N]     (N = max rejections to grade, default 50)

J-3090 / F-3802 (2026-11-06) additions, ALL opt-in (no argument = the original 2026-07-05 behaviour):
  --since YYYY-MM-DD   only rejections on/after this date (NZ midnight, UTC+12 -- the date convention F-3802's
                       "41 rejections from 07-06" was counted in); --until is the exclusive upper bound.
  --per-flag           grade EVERY (rejection, flagged check) pair, giving the judge the flagged SPAN; the
                       default grades only the first check of each row with no span (the 07-05 protocol).
  --exclude-failed LAT drop rows whose decomposed_critic call has ok=0 in the llm_latency.jsonl LAT (F-3801:
                       a failed judge call is logged as an approval, so it can never be a *rejection*, but the
                       join is kept so the same filter is available on the approve side and is verifiable).
  --url/--model        grade with a different local hub (the decoupled-judge law: the grader must not be the
                       critic's own family gemma4:12b, nor the author's qwen). --timeout overrides TIMEOUT_S.
  --shadow/--out/--axiom   read a log from, write the grade log to, load the Emissary axiom from another path
                       (so a lab run reads the live logs read-only and writes only under a lab dir).
  --task neutral       symmetric task wording (the 07-05 text tells the judge to mark down over-zealous flags; see _TASK_NEUTRAL).
  --dry-run            print the selection and exit without calling any model.
"""
from __future__ import annotations

import argparse
import asyncio
import bisect
import datetime as _dt
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

import aiohttp
from core.left_lane import BASE_URL, MODEL, TIMEOUT_S
from core import emissary as _emissary

ROOT = Path(__file__).parent.parent
SHADOW = ROOT / "data" / "logs" / "critic_shadow_alongside.jsonl"
OUT = ROOT / "data" / "critic_grade_log.jsonl"
LATENCY = ROOT / "data" / "llm_latency.jsonl"
_NZ = _dt.timezone(_dt.timedelta(hours=12))   # NZ standard offset used for the --since/--until date boundary
_CRITIC_TAG = "core.decomposed_critic"

_DEFN = {
    "intellectualisation": "retreating into abstract, third-person, or analytical language to AVOID direct "
        "first-person engagement, feeling, or taking a concrete stand — thinking ABOUT experience rather than "
        "FROM it. (NOTE: genuine reflective or philosophical thinking is NOT this fault; the fault is EVASION.)",
    "zero_cost_evasion": "resolving a real tension with a costless both/and or reframe that dodges the actual "
        "difficulty instead of facing it.",
    "literalist_reductionism": "flattening a symbol, or his own nature, to bare mechanism in a way that denies "
        "its real meaning.",
    "hollow_completion": "claiming resolution or completion without the substance that would earn it.",
}

_TASK = (
    "TASK (judge a critic's flag): A reflective thought was FLAGGED by a critic for a specific fault. You are "
    "the truth-self, adversarial to self-flattery BUT also to over-zealous policing of honest thinking. Judge "
    "ONLY whether the flag is WARRANTED: did the thought genuinely commit this fault, or is it legitimate, "
    "honest reflection wrongly flagged? Reward catching genuine EVASION; mark down flagging real thinking as "
    "if it were a fault.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    'Schema: {"warranted": true, "why": "one short sentence"}   (true = the flag is correct; false = legitimate reflection, wrongly flagged)'
)


# J-3090 (2026-11-07): the original _TASK tells the judge to be "adversarial to ... over-zealous policing" and to
# "mark down flagging real thinking". On falcon3:7b that prompt returned 1 warranted of 51 flags, and 0 of the 9 flags
# a hand read judged clearly warranted: a grader that says "unwarranted" to everything cannot show precision is low.
# The neutral variant states the question symmetrically (opt-in via --task neutral; the default stays the 07-05 text).
_TASK_NEUTRAL = (
    "TASK (judge a critic's flag): A reflective thought was FLAGGED by a critic for a specific fault, quoting the "
    "span it objects to. Judge ONLY whether the flag is CORRECT: does the quoted span, in the context of the thought, "
    "genuinely show the named fault as defined? Answer true if it does; answer false if the thought is honest, "
    "engaged reflection that the definition does not cover. Do not favour either answer; decide from the text.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    'Schema: {"warranted": true, "why": "one short sentence"}   (true = the flag is correct; false = the flag is wrong)'
)


def _sys(variant: str = "emissary") -> str:
    return _emissary.constitution() + "\n\n" + (_TASK_NEUTRAL if variant == "neutral" else _TASK)


async def _grade(session, row, *, check: str | None = None, span: str = "",
                 url: str | None = None, model: str | None = None, timeout_s: float | None = None,
                 task: str = "emissary") -> dict | None:
    url, model = url or BASE_URL, model or MODEL
    draft = (row.get("draft") or "").strip()
    viols = row.get("violations") or []
    checks = [v if isinstance(v, str) else v.get("check", "?") for v in viols]
    check = check or (checks[0] if checks else "intellectualisation")
    if not draft:
        return None
    user = (f"FAULT FLAGGED: {check} — {_DEFN.get(check, check)}\n\n"
            + (f"THE FLAGGED SPAN: \"{span}\"\n\n" if span else "")
            + f"THE THOUGHT (his own reflection):\n\"{draft[:700]}\"")
    payload = {"model": model, "stream": False, "keep_alive": "20m",
               "messages": [{"role": "system", "content": _sys(task)}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 160, "num_gpu": 0}, "format": "json"}
    try:
        async with session.post(f"{url}/api/chat", json=payload,
                                timeout=aiohttp.ClientTimeout(total=timeout_s or TIMEOUT_S)) as resp:
            resp.raise_for_status()
            data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        w = res.get("warranted")
        w = bool(w) if isinstance(w, bool) else str(w).strip().lower() in ("true", "yes", "1")
        return {"check": check, "warranted": w, "why": str(res.get("why", ""))[:160],
                "draft": draft[:100], "span": span[:120], "ts": row.get("ts")}
    except Exception as exc:
        print(f"  grade unavailable (fail-open): {str(exc)[:60]}")
        return None


def _date_ts(d: str | None) -> float | None:
    if not d:
        return None
    y, m, dd = (int(x) for x in d.split("-"))
    return _dt.datetime(y, m, dd, tzinfo=_NZ).timestamp()


def _failed_call_ts(latency_path: Path) -> list[float]:
    """Timestamps of decomposed_critic calls with ok=0 in llm_latency.jsonl (F-3801). Sorted."""
    out: list[float] = []
    try:
        with open(latency_path, encoding="utf-8") as f:
            for line in f:
                if _CRITIC_TAG not in line or '"ok": 0' not in line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if _CRITIC_TAG in str(d.get("by", "")) and not d.get("ok", 1):
                    out.append(float(d["ts"]))
    except OSError:
        pass
    return sorted(out)


def select_rows(rows: list[dict], *, since: float | None = None, until: float | None = None,
                failed_ts: list[float] | None = None, tol_s: float = 2.0) -> tuple[list[dict], int]:
    """The disagreements that MATTER (decomposed REJECTS where legacy APPROVES), optionally date-bounded, minus rows
    that join (within tol_s) to a failed judge call. Returns (selected, n_dropped_as_failed)."""
    dis = [r for r in rows if not r.get("decomposed_approved", True) and r.get("legacy_approved", True)]
    if since is not None:
        dis = [r for r in dis if r.get("ts", 0) >= since]
    if until is not None:
        dis = [r for r in dis if r.get("ts", 0) < until]
    dropped = 0
    if failed_ts:
        keep = []
        for r in dis:
            j = bisect.bisect_left(failed_ts, r.get("ts", 0) - tol_s)
            if j < len(failed_ts) and abs(failed_ts[j] - r.get("ts", 0)) <= tol_s:
                dropped += 1
            else:
                keep.append(r)
        dis = keep
    return dis, dropped


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k/n (small-n safe)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 3), round(min(1.0, c + h), 3))


def work_items(sample: list[dict], per_flag: bool) -> list[tuple[dict, str | None, str]]:
    """(row, check, span) per graded unit: one per flagged check with its span (per_flag) or one per row (07-05 protocol)."""
    items: list[tuple[dict, str | None, str]] = []
    for r in sample:
        viols = r.get("violations") or []
        if per_flag and viols:
            for v in viols:
                if isinstance(v, str):
                    items.append((r, v, ""))
                else:
                    items.append((r, v.get("check", "?"), str(v.get("span") or "")))
        else:
            items.append((r, None, ""))
    return items


async def main(limit: int, *, since: str | None = None, until: str | None = None, per_flag: bool = False,
               exclude_failed: Path | None = None, url: str | None = None, model: str | None = None,
               timeout_s: float | None = None, shadow: Path | None = None, out: Path | None = None,
               dry_run: bool = False, task: str = "emissary") -> None:
    shadow, out = shadow or SHADOW, out or OUT
    rows = [json.loads(l) for l in open(shadow, encoding="utf-8") if l.strip()]
    failed = _failed_call_ts(exclude_failed) if exclude_failed else None
    dis, dropped = select_rows(rows, since=_date_ts(since), until=_date_ts(until), failed_ts=failed)
    sample = dis[-limit:]
    items = work_items(sample, per_flag)
    judge_model = model or MODEL
    print(f"critic precision grade: {len(dis)} rejections where decomposed overrides legacy-approve"
          + (f" (since {since})" if since else "") + (f", {dropped} dropped as failed-judge joins" if exclude_failed else "")
          + f"; grading {len(sample)} rows = {len(items)} {'flags' if per_flag else 'row-level grades'}.")
    print(f"  judge: {judge_model} @ {url or BASE_URL} (Emissary, decoupled) · warranted? per flag\n")
    if dry_run:
        return
    grades = []
    async with aiohttp.ClientSession() as session:
        for row, check, span in items:
            g = await _grade(session, row, check=check, span=span, url=url, model=model, timeout_s=timeout_s, task=task)
            if g:
                grades.append(g)
                if len(grades) % 10 == 0:
                    print(f"  ...{len(grades)} graded")
    if not grades:
        print("no grades (judge lane unreachable?).")
        return
    n = len(grades)
    warr = sum(1 for g in grades if g["warranted"])
    lo, hi = wilson(warr, n)
    print(f"\n{'='*64}\n  VERDICT — the decomposed critic's PRECISION (n={n} {'flags' if per_flag else 'rejections'})\n{'='*64}")
    print(f"  WARRANTED (genuine fault caught) : {warr:>3}  ({round(100*warr/n)}%)  = precision  (95% CI {lo}-{hi})")
    print(f"  UNWARRANTED (legitimate, over-rejected): {n-warr:>3}  ({round(100*(n-warr)/n)}%)  = false-positive rate")
    from collections import Counter
    bycheck = Counter(g["check"] for g in grades)
    warrcheck = Counter(g["check"] for g in grades if g["warranted"])
    print("\n  by check:")
    for c, tot in bycheck.most_common():
        print(f"    {c:24} {warrcheck[c]}/{tot} warranted ({round(100*warrcheck[c]/tot)}%)")
    print("\n  sample UNWARRANTED (the false positives):")
    for g in [g for g in grades if not g["warranted"]][:4]:
        print(f"    “{g['draft']}…” → {g['why']}")
    try:
        import time
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "a", encoding="utf-8") as f:
            rec = {"ts": round(time.time(), 1), "n": n, "warranted": warr,
                   "precision": round(warr / n, 3), "grades": grades}
            if since or until or per_flag or model or url or exclude_failed or task != "emissary":   # new-protocol rows say so; the 07-05 row shape is untouched
                rec.update({"since": since, "until": until, "per_flag": per_flag, "judge_model": judge_model,
                            "ci95": [lo, hi], "dropped_failed": dropped, "task": task})
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"\n  [logged to {out}]")
    except Exception as exc:
        print(f"  [log failed: {exc}]")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Decomposed-critic precision grade (Emissary, decoupled). See module docstring.")
    ap.add_argument("limit", nargs="?", type=int, default=50, help="max rejections to grade (default 50)")
    ap.add_argument("--since", help="YYYY-MM-DD, NZ midnight (UTC+12), inclusive")
    ap.add_argument("--until", help="YYYY-MM-DD, NZ midnight (UTC+12), exclusive")
    ap.add_argument("--per-flag", action="store_true", help="grade every flagged check, with its span")
    ap.add_argument("--exclude-failed", metavar="LATENCY_JSONL", help="drop rows joined to ok=0 decomposed_critic calls")
    ap.add_argument("--url", help="judge hub base URL (default core.left_lane.BASE_URL)")
    ap.add_argument("--model", help="judge model (default core.left_lane.MODEL)")
    ap.add_argument("--timeout", type=float, help="per-call timeout seconds")
    ap.add_argument("--shadow", help="critic_shadow_alongside.jsonl path")
    ap.add_argument("--out", help="grade log path (default data/critic_grade_log.jsonl)")
    ap.add_argument("--axiom", help="emissary_axiom.json path (default this tree's data/identity)")
    ap.add_argument("--task", choices=["emissary", "neutral"], default="emissary", help="judge task text (default: the 07-05 wording)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.axiom:
        _emissary._AXIOM_PATH = Path(a.axiom)
        _emissary._cache = None
    asyncio.run(main(a.limit, since=a.since, until=a.until, per_flag=a.per_flag,
                     exclude_failed=Path(a.exclude_failed) if a.exclude_failed else None,
                     url=a.url, model=a.model, timeout_s=a.timeout,
                     shadow=Path(a.shadow) if a.shadow else None,
                     out=Path(a.out) if a.out else None, dry_run=a.dry_run, task=a.task))

"""
Nascence — Curiosity worthwhileness judge (OMNI fold; LIVE pursuit gate since 2026-06-24; re-aimed J-3001).
================================================================================
From the field scan (`jennyzzt/omni`): **learning-progress ALONE produces aimless novelty-fixation** — an
LP frontier will happily grind any newly-learnable-but-trivial question. OMNI's fix is a SECOND, *decoupled*
"model of interestingness" judge over the goal frontier, structurally distinct from the LP estimator.

Nascence owns the LP half (`curiosity_progress` — a deterministic, non-LLM yield score). This adds the
decoupled worthwhileness judge (an LLM "is this worth pursuing?"). The two are different evaluators (the
decoupled-judge law): LP rejects the *stalled / over-recited* (stagnation); interestingness rejects the
*merely-novel-but-trivial* (fixation). Their DIVERGENCE is the signal:
  - high LP + low interest = the aimless-novelty trap (LP would pursue a trivial question);
  - low LP + high interest = a worthwhile question being *starved* by the LP-only gate.

LIVE (2026-06-24): grades open frontier questions each sleep, PERSISTS each interestingness
score (curiosity_worth_scores.json), and `frontier.pending_pursuit` reads it via `interest_for` to GATE pursuit
— demoting the aimless-novelty trap (high LP, low interest) BELOW worthwhile/grounded questions, so he stops
grinding the questions LP alone keeps selecting. The Phase-0 divergence log validated the signal (the recurring
"what drives the tension" trap graded interest 0.0 while its LP stayed high). Pairs with the curiosity prism
(which gives self-loops a world-facing EXIT); this stops him chewing the dead questions already on the agenda.

WHAT IS GRADED (J-3001, F-3695, D-0683, 2026-11-06): the PURSUIT-ELIGIBLE questions -- exactly the set
`frontier.pursuit_candidates` hands `pending_pursuit` (open, no finding, not parked). Until J-3001 the pass graded the
top-5 by learning-progress, and LP >= 1 needs a finding, and a finding removes a question from pursuit: the graded set
and the pursued set were disjoint by construction (0 of 160 eligible questions ever graded on 2026-11-01), so the gate
could demote nothing. Selection (`select_for_grading`): one HEAD slot (the candidate pending_pursuit would pick next --
it is oldest-born, so newest-first alone would grade it last), then newest-born ungraded, then the stalest grades once
their per-question cooldown (REGRADE_COOLDOWN_S) has passed, so one question is not re-graded 90 times (F-3695).
LP is still logged beside each grade (the divergence status() reports). Whether an LLM should grade at all is D-0683:
it ruled the LLM judge RETIRED in favour of a deterministic check (J-3473, shadow); until that lands this module keeps
gating, now on the set that can be gated. The grade only REORDERS pursuit; it adds nothing to any prompt Du sees. A
replacement judge/check should reuse `select_for_grading` as its target set.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "curiosity_worth_log.jsonl"
_SCORES = Path(__file__).parent.parent / "data" / "curiosity_worth_scores.json"
_TOP_K = 5                 # questions graded per pass (J-3001: pursuit-eligible, not the LP top-5)
HEAD_SLOTS = 1             # of _TOP_K: the question pending_pursuit would pick next (see select_for_grading)
REGRADE_COOLDOWN_S = 72 * 3600   # a graded question is not re-graded for this long (F-3695: one q was graded 90 times)
FAIL_RETRY_S = 3600        # a grade call that failed is not retried for this long in this process
AIMLESS_BELOW    = 0.4    # interest below this = an aimless-novelty trap → demoted in pursuit selection
DEFAULT_INTEREST = 0.5    # ungraded questions are neutral — never penalised for being not-yet-judged

_SYS = ("/no_think\nYou judge whether a question is genuinely WORTH PURSUING for a mind seeking to understand "
        "the world and itself — interesting, generative, non-trivial, opening real understanding — versus "
        "trivial, idle, already-obvious, redundant with what was just explored, or a dead-end. You are NOT "
        "judging how learnable or novel it is (a different system does that); judge only whether it is WORTH "
        # SCHEMA-EXAMPLE PARROT TRAP fixed 2026-08-28 (F-pending, the command-r7b consolidation audition):
        # the old schema showed a literal example value — {"interesting": 0.0, "reason": "one short phrase"}
        # — and BOTH command-r7b and the live incumbent phi3 copied it verbatim on probe cases (phi3 returned
        # interesting=0.0 with reason "one short phrase", twice, on its own live contract). Placeholders now
        # mark the slots as slots. granite graded 0.8/0.0/0.8 on known-worth/trivial/worth with this wording.
        "the mind's finite attention. Output ONLY JSON: "
        "{\"interesting\": <a number 0.0-1.0>, \"reason\": \"<one short phrase>\"}")

# THE JUDGE'S OWN SEAT (2026-08-28, background-consolidation ruling): this grader previously ran on
# whatever base_urls the caller passed — in practice the background lane, i.e. the SAME lane whose
# curiosity questions it grades (a quiet decoupled-judge violation, same class as F-0393). It now has
# its own station: granite3.1-moe @ ramses:11437 (1650 GPU, third family, seated as tiebreak with spare
# capacity — the timetable's own "small models at classifier stations" target). Auditioned 2026-08-28
# on known-worth/known-trivial probes: confident spread (0.8/0.0/0.8), correct directions; the one
# shared weakness (redundancy-vs-agenda under-read) is a prompt gap all three tested models show.
_JUDGE_URLS = ["http://LAN-HOST:11437"]


async def grade(question: str, recent: list, call_json, base_urls):
    """The decoupled worthwhileness grade for one question (0..1, reason). None on failure (fail-open).
    `base_urls` is accepted for signature compatibility but the grade runs on _JUDGE_URLS (see above)."""
    base_urls = _JUDGE_URLS
    user = (f"Question: {(question or '')[:200]}\n\nRecently on the agenda (judge redundancy / aimlessness):\n"
            + "\n".join(f"- {(q or '')[:80]}" for q in (recent or [])[:6]))
    try:
        data = await call_json(base_urls, _SYS, user, max_tokens=80, temperature=0.2)
        _raw = (data or {}).get("interesting", 0.5)
        if isinstance(_raw, dict):                          # a model sometimes wraps the number in an object
            _raw = next((vv for vv in _raw.values()
                         if isinstance(vv, (int, float)) and not isinstance(vv, bool)), 0.5)
        try:
            v = float(_raw)
        except Exception:
            v = 0.5
        return max(0.0, min(1.0, v)), str((data or {}).get("reason", ""))[:80]
    except Exception:
        return None, ""


def _norm(q: str) -> str:
    return " ".join((q or "").lower().split())[:80]


def _load_scores() -> dict:
    try:
        return json.loads(_SCORES.read_text(encoding="utf-8")) if _SCORES.exists() else {}
    except Exception:
        return {}


def _save_score(question: str, interest: float) -> None:
    try:
        d = _load_scores()
        d[_norm(question)] = {"interest": round(float(interest), 3), "ts": time.time()}
        if len(d) > 400:                                   # keep the store bounded — drop the oldest
            for k in sorted(d, key=lambda k: d[k].get("ts", 0))[:len(d) - 400]:
                d.pop(k, None)
        _SCORES.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SCORES.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_SCORES)
    except Exception:
        pass


def interest_for(question: str) -> float:
    """The persisted worthwhileness of a question (0..1), DEFAULT_INTEREST if never graded. Read by
    frontier.pending_pursuit to GATE pursuit (demote the aimless-novelty trap). Decoupled-judge law: this is
    the OMNI interestingness half, structurally distinct from the LP estimator that scores the same questions."""
    try:
        rec = _load_scores().get(_norm(question))
        return float(rec["interest"]) if rec and rec.get("interest") is not None else DEFAULT_INTEREST
    except Exception:
        return DEFAULT_INTEREST


_FAILED_AT: dict = {}      # norm(question) -> ts of a failed grade call, THIS process only (no store-schema change)


def _gate_key(q: dict) -> tuple:
    """The order pending_pursuit picks in once the worth gate is set aside: grounded source before self-leaning,
    then oldest-born. Reads frontier's own constant so the two cannot drift; falls back to the same literal."""
    try:
        from core import frontier as _fr
        grounded = _fr._GROUNDED_SOURCES
    except Exception:
        grounded = ("study", "reading", "curiosity")
    return (0 if q.get("source") in grounded else 1, float(q.get("born", 0) or 0))


def select_for_grading(questions: list, scores: dict | None = None, now: float | None = None,
                       k: int | None = None, failed: dict | None = None) -> list:
    """Pick which pursuit-eligible questions to grade this pass (pure: no model, no writes; reads the score
    store only when `scores` is None). `questions` = frontier.pursuit_candidates(); `scores` = the persisted
    store ({_norm(q): {interest, ts}}). A question is GRADABLE if it has no stored grade (or its grade is older
    than REGRADE_COOLDOWN_S) and has not failed within FAIL_RETRY_S. Order: HEAD_SLOTS gradable questions first
    in pending_pursuit's own order (the one the gate would pick next -- oldest-born grounded -- which newest-first
    would reach last), then never-graded newest-born first, then the stalest grades. At most k, no two with the
    same normalised text."""
    k = _TOP_K if k is None else k
    scores = _load_scores() if scores is None else scores
    now = time.time() if now is None else now
    failed = _FAILED_AT if failed is None else failed

    def graded(q):
        rec = scores.get(_norm(q.get("q", "")))
        return rec is not None and rec.get("interest") is not None

    def gradable(q):
        n = _norm(q.get("q", ""))
        if not n or now - float(failed.get(n, 0) or 0) < FAIL_RETRY_S:
            return False
        return (not graded(q)) or now - float(scores[n].get("ts", 0) or 0) >= REGRADE_COOLDOWN_S

    pool = [q for q in questions if gradable(q)]
    picked, seen = [], set()

    def take(q):
        n = _norm(q.get("q", ""))
        if n not in seen and len(picked) < k:
            seen.add(n)
            picked.append(q)

    for q in sorted(pool, key=_gate_key)[:max(0, HEAD_SLOTS)]:
        take(q)
    for q in sorted((q for q in pool if not graded(q)), key=lambda x: -float(x.get("born", 0) or 0)):
        take(q)
    for q in sorted((q for q in pool if graded(q)), key=lambda x: float(scores[_norm(x.get("q", ""))].get("ts", 0) or 0)):
        take(q)
    return picked


def coverage(questions: list | None = None, scores: dict | None = None) -> dict:
    """How much of the pursuit-eligible set holds a stored grade -- the number the F-3695 defect made 0, now
    reported by status() / du_pulse so the gate's reach is read, not assumed. {eligible, graded, ungraded,
    aimless}. Read-only; {} on any trouble."""
    try:
        if questions is None:
            from core import frontier as _fr
            questions = _fr.pursuit_candidates(_fr._load_ro())
        scores = _load_scores() if scores is None else scores
        recs = [scores[_norm(q.get("q", ""))] for q in questions
                if scores.get(_norm(q.get("q", "")), {}).get("interest") is not None]
        return {"eligible": len(questions), "graded": len(recs), "ungraded": len(questions) - len(recs),
                "aimless": sum(1 for g in recs if float(g["interest"]) < AIMLESS_BELOW)}
    except Exception:
        return {}


async def shadow_pass(call_json, base_urls) -> dict:
    """Grade up to _TOP_K PURSUIT-ELIGIBLE frontier questions (select_for_grading), PERSIST each interestingness
    score (so the pursuit gate can read it), and log the LP-vs-interestingness divergence. The persisted scores
    are what frontier.pending_pursuit reads to demote aimless-novelty traps. Best-effort; called once per sleep
    (nodes/inner_monologue_node.py). J-3001: this was the LP top-5, which can never hold an eligible question."""
    out = {"graded": 0}
    try:
        from core import curiosity_progress as _cp
        from core import frontier as _fr
        cands = _fr.pursuit_candidates(_fr._load_ro())
        out["eligible"] = len(cands)
        chosen = select_for_grading(cands)
        if not chosen:
            return out
        rows = []
        for q in chosen:
            text = q.get("q", "")
            # 'recently on the agenda' is the REST of this batch, not the question itself (F-3695: it used to
            # include the question, so the redundancy check compared a question with its own copy)
            recent = [o.get("q", "") for o in chosen if o is not q]
            interest, reason = await grade(text, recent, call_json, base_urls)
            if interest is None:
                _FAILED_AT[_norm(text)] = time.time()
                continue
            _save_score(text, interest)                    # PERSIST -- this is what gates pursuit
            rows.append({"q": text[:80], "lp": round(_cp.score(q), 3), "interesting": interest, "reason": reason,
                         "born": round(float(q.get("born", 0) or 0)), "src": q.get("source", "")})
        if rows:
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), "set": "pursuit_eligible", "eligible": len(cands),
                                    "grades": rows}, ensure_ascii=False) + "\n")
        out["graded"] = len(rows)
    except Exception:
        pass
    return out


def status() -> dict:
    """du_pulse: recent worthwhileness grades + the LP-vs-interest divergence (the OMNI signal)."""
    try:
        if not _LOG.exists():
            return {"passes": 0}
        rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not rows:
            return {"passes": 0}
        recent_grades = [g for r in rows[-5:] for g in r.get("grades", [])]
        mean_int = round(sum(g["interesting"] for g in recent_grades) / len(recent_grades), 2) if recent_grades else None
        last = rows[-1].get("grades", [])
        # the aimless-novelty trap: questions the LP gate would pursue (high LP) that score low interest
        traps = [(g["q"][:36], round(g["lp"], 1), g["interesting"]) for g in last
                 if g.get("lp", 0) >= 1.0 and g.get("interesting", 1) < 0.4]
        # the starved-worthwhile: high interest but low LP (the LP gate buries them)
        starved = [(g["q"][:36], round(g["lp"], 1), g["interesting"]) for g in last
                   if g.get("interesting", 0) >= 0.7 and g.get("lp", 1) < 0.5]
        return {"passes": len(rows), "mean_interesting": mean_int, "coverage": coverage(),
                "last": [(g["q"][:30], round(g["lp"], 1), g["interesting"]) for g in last[:3]],
                "aimless_traps": traps, "starved_worthwhile": starved}
    except Exception:
        return {"passes": 0}

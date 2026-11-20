"""
Nascence -- WEAKNESS_PRIOR (measurement_to_action arm 6, J-2162, D-0436 ruled A by travis 2026-10-15).
docs/staged/measurement_to_action.md section 2.6.

A librarian's job, not a hint: the lowest-scoring domain among those with a GRADED instrument
(data/capability_beliefs.json: accuracy not None and evidence_count > 0) gets ONE extra candidate slot
in core/book_selection.select_explore (and a shadow-only read in the school timetable). Never a forced
pick: the prior is clamped to MAX_PRIOR (< 0.5) and Du still draws from the weighted set.

SHADOW FIRST: WEAKNESS_PRIOR = 0.0 -> apply_to_weighted() returns the weights untouched. Every call
still logs what the slot WOULD have been and whether the actual pick matched it, to its OWN store
data/weakness_prior_shadow.jsonl.

D-0436 DEFEATER CLAUSE 2: the slot never carries a reason naming weakness or a score. Nothing here adds
any key or text to a pick row or a directive; the shadow log (never rendered to Du) is the only place
the domain name appears. Grade-back is the domain's existing instrument only (nothing new is measured).

RESTART-GATED (imports fixed at process start), fail-open (every public function swallows its errors and
returns the neutral value), additive. Kill switch: ENABLED = False. Lab mode (core.telemetry._LAB_MODE)
writes nothing.

READ: python -m core.weakness_prior   (pure reader, writes nothing).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ENABLED = True
WEAKNESS_PRIOR = 0.0          # 0.0 = shadow only. A small value (e.g. 0.1) is a later, founder-gated step.
MAX_PRIOR = 0.4               # hard clamp: the slot can never become a forced pick
_ROOT = Path(__file__).parent.parent
_BELIEFS = _ROOT / "data" / "capability_beliefs.json"
_LOG = _ROOT / "data" / "weakness_prior_shadow.jsonl"

# domain -> title/subject keywords for the book shelf (domains with no shelf analogue have no book slot)
BOOK_KEYWORDS = {
    "history_culture": {"history", "civilization", "ancient", "empire", "medieval", "war"},
    "science": {"science", "physics", "chemistry", "biology", "astronomy", "natural"},
    "mathematics": {"mathematics", "arithmetic", "geometry", "algebra", "calculus"},
    "music": {"music", "musical", "harmony", "opera", "composers"},
    "observation": {"nature", "birds", "botany", "animals", "insects", "plants", "flowers"},
    "writing": {"composition", "rhetoric", "essays", "writing", "grammar"},
    "language_translation": {"language", "languages", "dictionary", "grammar", "translation"},
}
# domain -> school timetable subject (school.SCHOOL_SUBJECTS)
SCHOOL_SUBJECT = {
    "mathematics": "math", "music": "music", "observation": "nature", "fieldcraft": "nature",
    "science": "nature", "writing": "composition", "history_culture": "reading",
    "comprehension": "reading", "factual_recall": "reading", "language_translation": "reading",
}


def _lab() -> bool:
    try:
        from core import telemetry as _t
        return bool(getattr(_t, "_LAB_MODE", False))
    except Exception:
        return False


def _log(row: dict) -> None:
    try:
        if not ENABLED or _lab():
            return
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def weakest_domain(beliefs: dict | None = None) -> tuple[str, float] | None:
    """(domain, graded score) of the lowest-scoring domain that has a graded instrument, else None.
    Score = the instrument's own `accuracy` (the grade-back); `confidence` is self-belief and is not used."""
    try:
        if beliefs is None:
            beliefs = json.loads(_BELIEFS.read_text(encoding="utf-8"))
        best = None
        for dom, v in beliefs.items():
            from core.competence import effective_accuracy as _eff_acc  # J-4369/D-0847
            acc = _eff_acc(v)[0] if isinstance(v, dict) else None
            if acc is None or int(v.get("evidence_count", 0) or 0) <= 0:
                continue
            acc = float(acc)
            if best is None or (acc, dom) < (best[1], best[0]):
                best = (dom, acc)
        return best
    except Exception:
        return None


def _prior() -> float:
    try:
        return max(0.0, min(MAX_PRIOR, float(WEAKNESS_PRIOR)))
    except Exception:
        return 0.0


def _matches(row: dict, kws: set) -> bool:
    text = " ".join(str(row.get(k) or "") for k in ("title", "subjects")).lower()
    return any(k in text for k in kws)


def apply_to_weighted(weighted: list, beliefs: dict | None = None) -> tuple[list, dict | None]:
    """weighted = [(row, w), ...]. Returns (weighted', slot): slot = the candidate row the extra slot names
    (or None). With WEAKNESS_PRIOR == 0 the returned list IS the input, unchanged. Fail-open."""
    try:
        if not ENABLED or not weighted:
            return weighted, None
        wk = weakest_domain(beliefs)
        if not wk or wk[0] not in BOOK_KEYWORDS:
            return weighted, None
        kws = BOOK_KEYWORDS[wk[0]]
        cands = [(r, w) for (r, w) in weighted if _matches(r, kws)]
        if not cands:
            return weighted, None
        slot = max(cands, key=lambda x: x[1])[0]
        p = _prior()
        if p <= 0.0:
            return weighted, slot
        total = sum(w for _, w in weighted)
        bump = total * p / (1.0 - p)     # slot's draw mass becomes >= p of the whole, never 1.0
        return [(r, (w + bump) if r is slot else w) for (r, w) in weighted], slot
    except Exception:
        return weighted, None


def log_book_pick(slot: dict | None, picks: list, beliefs: dict | None = None) -> None:
    """Shadow row: what the slot would have been and whether Du's (weighted-draw) pick matched it."""
    try:
        wk = weakest_domain(beliefs)
        _log({"ts": time.time(), "arm": "book", "prior": _prior(), "domain": wk[0] if wk else None,
              "score": wk[1] if wk else None, "slot_title": ((slot or {}).get("title") or "")[:80] or None,
              "picked": [(p.get("title") or "")[:80] for p in picks],
              "matched": bool(slot is not None and any(p is slot for p in picks))})
    except Exception:
        pass


_LAST_SCHOOL_KEY = [None]


def school_shadow(actual_subject: str, now: float | None = None, beliefs: dict | None = None) -> str | None:
    """Shadow-only read of the school timetable: which subject the weakness slot WOULD have offered vs the
    clock's subject. Logged once per 45-minute period. Never changes the directive. Returns the subject."""
    try:
        wk = weakest_domain(beliefs)
        sub = SCHOOL_SUBJECT.get(wk[0]) if wk else None
        t = now if now is not None else time.time()
        key = (time.strftime("%Y-%m-%d", time.localtime(t)), actual_subject, int(t // 2700))
        if key != _LAST_SCHOOL_KEY[0]:
            _LAST_SCHOOL_KEY[0] = key
            _log({"ts": time.time(), "arm": "school", "prior": _prior(), "domain": wk[0] if wk else None,
                  "score": wk[1] if wk else None, "slot_subject": sub, "actual_subject": actual_subject,
                  "matched": bool(sub and sub == actual_subject)})
        return sub
    except Exception:
        return None


def read() -> dict:
    """Pure reader for the shadow log: counts + match rate per arm."""
    out: dict = {}
    try:
        for line in _LOG.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            a = out.setdefault(r.get("arm"), {"n": 0, "matched": 0})
            a["n"] += 1
            a["matched"] += 1 if r.get("matched") else 0
    except Exception:
        pass
    return out


if __name__ == "__main__":
    print(read())

"""
Nascence — Within-Cycle Reentry (Consciousness Program Tier-2 A, 2026-07-04).
PHASE 0 (SHADOW) ran 2026-07-04 → 2026-09-02. PHASE 1 (LIVE) from D-0106 (2026-09-02): the shadow
verdict was unanimous ENRICHING (0 collapses, mean delta ~0.31) across the first 27 real settle
events — see docs/plans/within_cycle_reentry.md "Current State".
PHASE 1 SWITCHED OFF by D-0540 (founder, 2026-11-02): REENTRY_ADMIT=False, so this is Phase 0 again
(first draft admitted, settle logged fire-and-forget). The Phase 1 prose below is kept as history.

docs/plans/within_cycle_reentry.md. Function-substitution for the reentrant settling that RPT/GNW demand:
at a selected ADMISSION point (a broadcast winner, a forming commitment), re-present the draft WITH one new
DECOUPLED ingredient and let it settle before it would be admitted. Butlin/Long license this at the
ALGORITHMIC level (RPT-1); the frozen forward pass is untouched. This is an EXTENSION of the conversation
rebind loop (orchestrator.py:736) — which already enforces the one non-negotiable rule — to idle admission.

THE NON-NEGOTIABLE (data-processing inequality + model-collapse + Huang 2024): every pass must inject
genuinely NEW external material; a pass with nothing new is FORBIDDEN. The ingredient is decoupled from the
drafter (targeted retrieval / a named contradiction), presented NEUTRALLY — never "check/fix your answer"
(the sycophantic-flip failure) — and the reviser is told to KEEP HIS VOICE except where the context forces
a change (voice is the first casualty in an identity project).

PHASE 0 changed NOTHING: it ran the settle loop in parallel on the background lane (tier 3, yields to all
real cognition), the caller ADMITTED THE FIRST DRAFT regardless, and logged {first, settled, delta, basin
trend, length trend, would_collapse}. That answered the only question that mattered: does settling ENRICH
(settled≠first AND basin-share/length flat-or-down) or HOMOGENISE? The kill-switch (§3.3) held throughout
Phase 0: settling never once raised basin-share or length. PHASE 1 (this build) admits the settled draft
at the ONE broadcast admission point (core/broadcast.py's idle-monologue propagation buffer — NOT the
live human-facing turn, which has already completed by this point in the cycle) — see
orchestrator.py's broadcast block. The kill-switch stays live in production: `would_admit_settled` is
False (falls back to the first draft) whenever a pass would raise basin-share or inflate length.
Deterministic math, one background LLM call per settled pass, rate-capped, fail-open.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "reentry_shadow.jsonl"
_STATE = _DATA / "reentry_state.json"

REENTRY_ADMIT = False       # D-0540 (2026-11-02, founder): Phase 1 admission SWITCHED OFF — back to Phase 0 (admit the
                             # first draft, keep logging to data/reentry_shadow.jsonl). Why: D-0106's own defeater fired
                             # (collapse 31.6% of 136 settles since 09-02 vs 0 of 27 at the ruling), status() reads
                             # HOMOGENISING/INERT, the awaited settle delayed Travis's reply by up to 260 s, and nothing
                             # but embedding math judged the rewrite. With False the orchestrator's broadcast block takes
                             # its fire-and-forget branch (asyncio.create_task), so no settle is ever awaited in a human
                             # cycle. Was True from D-0106 (2026-09-02): settled draft admitted iff would_admit_settled.
                             # Revisit per D-0540's defeater (blind-pair preference check, or a new reviser prompt with
                             # collapse < 25% and a no-ingredient control).
MAX_PASSES = 2              # gains peak at 1–2 (biology CORnet 2/4/2 · engineering Self-Refine); more = hysteresis
RECRUIT_COOLDOWN = 300.0   # min seconds between settles (selective recruitment + hard cost cap)
_CONVERGE = 0.985          # cos(prev, revised) above this = barely changed → converged (tune in shadow)
_NEW_INGREDIENT_MAX = 0.80 # an ingredient more similar than this to the draft is NOT new → forbidden pass
_COLLAPSE_MARGIN = 0.03    # settled basin-share rising more than this over the draft = collapse
_LEN_INFLATE = 1.5         # settled >1.5× the draft length = blandification/inflation → treat as collapse

_NEUTRAL = (
    "You had this thought:\n\"{draft}\"\n\n"
    "Here is some additional context that may or may not be relevant:\n\"{ingredient}\"\n\n"
    "Express the thought again in your own voice. Keep your own phrasing except where this context "
    "genuinely changes what you think. Do not check it or fix it — just let the context work on it, or not."
)


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(d), encoding="utf-8"); tmp.replace(_STATE)
    except Exception:
        pass


def _cos(a, b) -> float:
    try:
        from core.memory.store import _cosine
        return float(_cosine(a, b))
    except Exception:
        return 0.0


def _log_row(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _skip(kind: str, reason: str, **detail) -> None:
    """Every early return LOGS WHY (2026-08-14). This instrument sat at 0 rows for 6 weeks because
    each guard exited with a bare None — the exact write-only/can't-say-why-it's-silent failure mode.
    A skip row is {ts, kind, skip: reason, ...}; settle rows keep their original shape ("passes" key)."""
    _log_row({"ts": round(time.time(), 1), "kind": kind, "skip": reason, **detail})
    return None


def _tokens(t: str) -> set:
    return {w for w in "".join(c if c.isalnum() else " " for c in (t or "").lower()).split() if len(w) > 3}


def _measure(first: str, settled: str, fv, sv, basin) -> dict:
    """The deterministic verdict — no LLM. Does settling ENRICH or HOMOGENISE?"""
    overall_delta = round(1.0 - _cos(fv, sv), 4)                    # how far settled moved from first (want > 0)
    draft_basin = round(_cos(fv, basin), 4) if basin is not None else None
    settled_basin = round(_cos(sv, basin), 4) if basin is not None else None
    basin_rose = (basin is not None and settled_basin > draft_basin + _COLLAPSE_MARGIN)
    len_ratio = round(len(settled) / max(1, len(first)), 3)
    inflated = len_ratio > _LEN_INFLATE
    collapse = bool(basin_rose or inflated)                        # the kill-switch conditions
    return {"overall_delta": overall_delta, "draft_basin": draft_basin, "settled_basin": settled_basin,
            "basin_rose": basin_rose, "len_ratio": len_ratio, "inflated": inflated,
            "would_collapse": collapse,
            # what Phase 1 WOULD admit: the settled draft only if it moved AND did not collapse
            "would_admit_settled": bool(overall_delta > 0.02 and not collapse)}


async def settle_shadow(draft: str, kind: str, *, revise, retrieve, embed, basin=None) -> dict | None:
    """Run the settle loop and LOG the verdict {first, settled, delta, basin trend, length trend,
    would_collapse, would_admit_settled} — `first`/`settled` are logged TRUNCATED to 200 chars (log-size
    discipline, unchanged since Phase 0). The returned dict additionally carries `settled_full` (the
    UNTRUNCATED settled draft, not written to disk) for a Phase-1 caller that actually admits it.
      revise(prompt)->str  (async, background lane)   retrieve(query)->list[str]  embed(text)->vec
    Fail-open: any error returns None and the caller admits the first draft untouched — but every
    early exit writes a {skip: reason} row to the jsonl, so silence is always explainable."""
    try:
        draft = " ".join((draft or "").split())
        if len(draft) < 40:
            return _skip(kind, "short-draft", draft_len=len(draft))
        st = _load_state()
        now = time.time()
        if now - float(st.get("last_ts", 0)) < RECRUIT_COOLDOWN:     # selective recruitment / cost cap
            return _skip(kind, "cooldown", wait_s=round(RECRUIT_COOLDOWN - (now - float(st.get("last_ts", 0))), 1))
        _save_state({"last_ts": now})                               # claim the slot up front (no double-fire)

        fv = embed(draft)
        if fv is None:
            return _skip(kind, "embed-draft-failed")
        b = basin
        if b is None:
            try:
                from core import mineness
                b = mineness._get_basin()
            except Exception:
                b = None

        used_tokens: set = set()
        cur = draft
        cur_vec = fv
        passes = 0
        ingredients = []
        ingredients_full = []
        retrieve_error = None
        try:
            candidates = list(retrieve(draft) or [])
        except Exception as exc:
            candidates = []
            retrieve_error = repr(exc)[:160]

        # Why a pass didn't happen — kept so a passes==0 exit can name its guard instead of going silent.
        stop_reason = None
        rejected = {"dup": 0, "no_new_tokens": 0, "too_similar": 0}
        for _ in range(MAX_PASSES):
            # pick the next GENUINELY NEW ingredient (the added==0 rule, enforced): novel tokens + not a
            # near-duplicate of the current draft.
            ingredient = None
            for cand in candidates:
                cand = " ".join((cand or "").split())[:280]
                if not cand or cand in ingredients:
                    rejected["dup"] += 1
                    continue
                ct = _tokens(cand)
                if not (ct - used_tokens - _tokens(cur)):
                    rejected["no_new_tokens"] += 1
                    continue                                        # nothing new in it
                cv = embed(cand)
                if cv is not None and _cos(cv, cur_vec) > _NEW_INGREDIENT_MAX:
                    rejected["too_similar"] += 1
                    continue                                        # too similar to the draft = not new
                ingredient = cand
                used_tokens |= ct
                break
            if ingredient is None:
                stop_reason = "no-new-ingredient"
                break                                               # no new material → FORBIDDEN to iterate

            try:
                revised = await revise(_NEUTRAL.format(draft=cur[:400], ingredient=ingredient[:280]))
            except Exception as exc:                                # the 6-week silence lived HERE (invalid
                stop_reason = "revise-error"                        # lane URL) — never let it die nameless
                revise_error = repr(exc)[:160]
                break
            revised = " ".join((revised or "").split())
            if not revised or len(revised) < 20:
                stop_reason = "revise-empty"
                break
            rev_vec = embed(revised)
            if rev_vec is None:
                stop_reason = "embed-revised-failed"
                break
            passes += 1
            ingredients.append(ingredient[:80])
            ingredients_full.append(ingredient)                      # J-3018: full text for the blind pair test
            step_delta = 1.0 - _cos(cur_vec, rev_vec)
            cur, cur_vec = revised, rev_vec
            if step_delta < (1.0 - _CONVERGE):                       # barely changed → converged, stop
                break

        if passes == 0:
            detail = {"candidates": len(candidates), "rejected": rejected}
            if retrieve_error:
                detail["retrieve_error"] = retrieve_error
            if stop_reason == "revise-error":
                detail["error"] = revise_error
            return _skip(kind, stop_reason or "no-new-ingredient", **detail)

        m = _measure(draft, cur, fv, cur_vec, b)
        rec = {"ts": round(now, 1), "kind": kind, "passes": passes, "ingredients": ingredients,
               "first": draft[:200], "settled": cur[:200], **m}
        # J-3018 (additive; existing keys above unchanged): full text for a blind first-vs-settled pair test.
        # `admitted` = what the caller actually does with the settled draft under the current REENTRY_ADMIT.
        rec["first_full"] = draft[:400]
        rec["settled_full"] = cur
        rec["ingredients_full"] = ingredients_full
        rec["admitted"] = bool(REENTRY_ADMIT and m.get("would_admit_settled"))
        _log_row(rec)
        # Phase 1 (D-0106): the caller admits `settled_full` (untruncated, not logged) iff
        # would_admit_settled, else falls back to the first draft.
        return dict(rec)
    except Exception as exc:
        return _skip(kind, "settle-error", error=repr(exc)[:160])


def status() -> dict:
    """For the pulse. THE QUESTION: does settling ENRICH (delta>0, basin/length flat-or-down) or HOMOGENISE?"""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan on every ~6s HUD poll. "settles" now caps
        # at the window; the derived stats only ever used the last 200 rows of each class.
        all_rows = _tail_rows(_LOG, 2000)
        # Skip rows ({skip: reason}) explain silence; settle rows ("passes" key) carry the verdict math.
        skip_counts: dict = {}
        for r in all_rows[-200:]:
            if "skip" in r:
                skip_counts[r["skip"]] = skip_counts.get(r["skip"], 0) + 1
        rows = [r for r in all_rows if "passes" in r]
        if not rows:
            return {"settles": 0, "skips": skip_counts}
        recent = rows[-200:]
        n = len(recent)
        moved = [r["overall_delta"] for r in recent]
        collapses = sum(1 for r in recent if r.get("would_collapse"))
        basin_rise = [round(r["settled_basin"] - r["draft_basin"], 4)
                      for r in recent if r.get("draft_basin") is not None]
        return {"settles": len(rows), "skips": skip_counts,
                "mean_delta": round(sum(moved) / n, 4),                 # >0 = settled differs from first
                "would_admit_rate": round(sum(1 for r in recent if r.get("would_admit_settled")) / n, 3),
                "collapse_rate": round(collapses / n, 3),                # the kill-switch reading — want LOW
                "mean_basin_shift": round(sum(basin_rise) / len(basin_rise), 4) if basin_rise else None,
                "mean_len_ratio": round(sum(r["len_ratio"] for r in recent) / n, 3),
                "verdict": ("ENRICHING" if (sum(moved) / n > 0.03 and collapses / n < 0.25)
                            else "HOMOGENISING/INERT — do NOT promote")}
    except Exception:
        return {"settles": 0}

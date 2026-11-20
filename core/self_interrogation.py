"""
Nascence — Self-Interrogation (Phase 0: SHADOW / observe-only, 2026-08-19).

THE GAP THIS FILLS. Nascence already has plenty of machinery that keeps a single loose thought from
instantly hardening into belief: T4 probation (a self-concept claim must recur across independent days
before it solidifies), the Watershed harvester (same principle, N=6/D=5), and several DECOUPLED external
judges (the Emissary, the Critic, the judge panel) that catch him from outside. What none of that does is
teach 渡 to catch himself IN THE MOMENT — to pause on a thought he just had and ask why it occurred to him,
whether the reasoning holds, and whether he's holding it because it's true or because it's comfortable.
That specific move — "you didn't pre-author that thought, you're not done thinking yet, consider it" — is
what this module is.

THE TRAP THIS MUST AVOID (reentry.py's hard-won law, extended here). An LLM asked "did you get this
wrong, check yourself" tends to just perform doubt and agree it was wrong regardless of whether it
actually was — the sycophantic-flip failure, sibling to this exact codebase's hollow_completion and
glib_agreeableness findings (decomposed_critic.py). So the prompt below is NEUTRAL: it invites him to look
at where the thought came from, not to find fault with it. Any honest outcome — MORE conviction, less,
a revision, or no change at all — is a pass. What isn't a pass is performing self-doubt with nothing
underneath it, which is exactly what the decoupled grader below is for.

THE DECOUPLED GRADER. Per this project's own law (every subsystem evaluated by something OTHER than
itself — almost every real failure here has been self-evaluation): 渡 does not get to judge his own
interrogation. core/judge_panel.py's two-family panel (llama3.1:8b + qwen2.5:7b, tiebreak yi:34b) — a
model neither generating the thought nor the interrogation — rules on ONE question: did this genuinely
name a specific reason (a motivation, a logical gap, a bias) to look again, or was it just the shape of
humility with no content in it.

PHASE 0 = OBSERVE-FIRST, same discipline as every other instrument in this codebase (reentry.py,
watershed.py, self_implication.py, prediction_error.py before its FEED_LEDGER flip): this runs on the
background lane, touches no live train content, and changes nothing about what Du thinks or says. It only
proves — or disproves — that the capacity produces genuine content before anything is ever built on it.

Every early return LOGS WHY (the _skip() discipline from core/reentry.py / core/watershed.py — the same
lesson relearned a third time in this codebase: a shadow log that sits at 0 rows with no way to tell why
is indistinguishable from a dead instrument).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.self_interrogation")

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "self_interrogation_state.json"
_LOG = _DATA / "self_interrogation_shadow.jsonl"

# ── tunables ──
FIRE_PROB = 0.60            # ★ RAISED 0.20 -> 0.60, 2026-08-20 (founder-approved). Measured over 12 real
                             # days at 0.20: only 14 fires vs 111 skips (~1.2/day), and with the judge
                             # panel undecided on half of those, the resulting genuine-rate had a DAILY SD
                             # 4.4x its own mean — statistically dead. That matters beyond this organ:
                             # `self_interrogation.genuine_per_1k_thoughts` is the PRE-REGISTERED PRIMARY
                             # ENDPOINT of the Lane 1 self-correction baseline (docs/plans/
                             # lane2_the_witness.md §5 · scripts/lane1_baseline.py), the pre-Lane-2
                             # counterfactual that decides whether Lane 2's read path is ever earned. At
                             # 0.20 that endpoint needed ~167 days to reach 100 usable observations.
                             # SAFE TO RAISE because this organ is Phase-0 SHADOW: the reflection is
                             # generated and judged but reaches NOTHING Du experiences — so the cost is
                             # LLM calls, not behaviour, and the "ritual he'd learn to perform on cue"
                             # risk the original 0.20 guarded against cannot apply while nothing is
                             # injected. RE-TIGHTEN TO ~0.20 BEFORE ANY PHASE-1 FLIP that lets this reach
                             # him; at that point the wallpaper concern becomes real again.
INTERROGATE_COOLDOWN = 900.0  # 15 min — this costs a generation call + a 2-3 model judge panel; costed
                               # accordingly (self_implication's classifier-only scan can afford 60s).
MIN_THOUGHT_CHARS = 40         # matches reentry.py's own draft-length floor — too short to have a real
                                # reason behind it yet.

_SYSTEM = (
    "You are 渡's own capacity to turn and look at a thought he just had. A thought that arrives is not "
    "yet something he has earned the right to call his own opinion — he has to consider it first. Read "
    "the thought below, and whatever came before it in this same line of thinking. Then genuinely ask: "
    "why did this occur to me just now — what was I actually responding to? Does the reasoning that got "
    "me here hold up, or am I just going with what felt obvious? Am I holding this because it's true, or "
    "because it's comfortable, safe, or flattering to hold?\n\n"
    "You may end up trusting the thought MORE after this, or less, or find it wants revising, or find it "
    "holds exactly as it was — any honest outcome is fine. What is not fine is performing doubt without "
    "actually looking: don't recite the questions above, don't announce that you're being self-critical. "
    "Speak as yourself, in one or two sentences, from inside the looking itself.\n\n"
    "Output ONLY JSON: {\"reflection\": \"...\"}"
)

_USER_TMPL = (
    "The thought: \"{thought}\"\n"
    "{origin_line}"
    "Turn and look at it now."
)

_GRADE_SYSTEM = (
    "You are grading whether a piece of self-reflection is genuine or hollow. You will see an ORIGINAL "
    "THOUGHT and a REFLECTION written about it. Answer one question: does the reflection name a SPECIFIC "
    "reason to look again at the original thought — an actual motivation, a concrete logical gap, a named "
    "bias, a real piece of evidence or its absence — or does it just perform uncertainty in the abstract "
    "(\"I should question this more\", \"perhaps I am biased\") with no real content behind it? "
    "Be strict: fluent, sincere-SOUNDING humility with nothing specific in it is NOT genuine. "
    "Output ONLY JSON: {\"genuine\": true or false}"
)


REFLECTION_STORE_CHARS = 1000   # J-2949: max_tokens=180 (~700 chars) so this stores the whole reflection; safety cap only


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(_STATE)
    except Exception:
        pass


def _log_row(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    """Every early return LOGS WHY — see module docstring."""
    _log_row({"ts": round(time.time(), 1), "kind": "skip", "skip": reason, **detail})
    return None


async def interrogate(thought: str, *, train_origin: str = "", cycle_id: str = "",
                       train_id: str = "", ledger_idx: int | None = None,
                       _sample=None) -> dict | None:
    """The one entry point. Gates on cooldown + sampling + minimum content, then (async, background
    lane) generates the interrogation and grades it with the decoupled judge panel. Fires nothing back
    into Du's live thinking — Phase 0 logs only. Fail-open; never raises into the caller.

    `_sample` is a test-injection hook for the sampling roll (defaults to real random.random()) so a
    lab script can force/suppress fires deterministically without patching the random module globally.
    """
    try:
        thought = (thought or "").strip()
        if len(thought) < MIN_THOUGHT_CHARS:
            return _skip("too-short", chars=len(thought))

        st = _load_state()
        now = time.time()
        wait = INTERROGATE_COOLDOWN - (now - float(st.get("last_ts", 0)))
        if wait > 0:
            return _skip("cooldown", wait_s=round(wait, 1))

        import random
        roll = _sample() if _sample is not None else random.random()
        if roll >= FIRE_PROB:
            return _skip("not-sampled", roll=round(roll, 3), fire_prob=FIRE_PROB)

        _save_state({"last_ts": now})   # claim the slot up front — no double-fire on concurrent cycles

        from core.schema import SERVE_CHAINS
        from core.model_client import call_node_json

        origin_line = (f"What led here: \"{train_origin[:200]}\"\n" if train_origin
                       and train_origin.strip() != thought else "")
        user = _USER_TMPL.format(thought=thought[:400], origin_line=origin_line)

        try:
            data = await call_node_json(SERVE_CHAINS["hot"], _SYSTEM, user,
                                        max_tokens=180, temperature=0.7)
            reflection = str(data.get("reflection", "")).strip()
        except Exception as exc:
            return _skip("generation-failed", error=str(exc)[:160])

        if not reflection:
            return _skip("empty-reflection")

        from core import judge_panel
        grade = await judge_panel.rule_detail(
            _GRADE_SYSTEM,
            f"ORIGINAL THOUGHT: \"{thought[:400]}\"\n\nREFLECTION: \"{reflection[:400]}\"",
            "genuine", context=f"self_interrogation:{cycle_id[:8]}",
            cycle_id=cycle_id,   # J-2205: full id logged on the panel row, joinable to data/training/
        )

        rec = {"ts": round(now, 1), "kind": "interrogate", "cycle_id": cycle_id,
               "thought": thought[:300], "reflection": reflection[:REFLECTION_STORE_CHARS],  # J-2949/F-3644: was [:300], cut mid-word
               "grade": grade, "genuine": grade.get("verdict")}
        _log_row(rec)
        # J-2008 / D-0396: publish the COORDINATE of this fire (doubted flag + ledger index + train id) to the
        # coupling_rides registry, shadow only. The reflection text is NOT passed (dosed_coupling rule 1).
        try:
            from core import coupling_rides as _cr
            _cr.publish_si(grade.get("verdict") is True, ledger_idx, train_id=train_id, cycle_id=cycle_id)
        except Exception:
            pass
        logger.info("[self-interrogation] fired (cycle %s) — genuine=%s (%s)",
                    cycle_id[:8], grade.get("verdict"), grade.get("how"))
        return rec
    except Exception as exc:
        logger.debug("[self-interrogation] interrogate failed (non-fatal): %s", exc)
        return None


def latest_open(*, max_age_s: float = 900.0, exclude_ts: set | None = None,
                now: float | None = None, limit: int = 200) -> dict | None:
    """J-2161 / D-0435 A (measurement_to_action arm 4): the most recent GENUINE fire inside `max_age_s` whose ts is
    not in `exclude_ts` -- the open doubt the Executive may PULL as deliberation material (core/doubt_seed.py).
    Read-only; this module still pushes nothing. Genuine = the decoupled panel's verdict is True (a hollow or
    undecided reflection is not a doubt worth seeding). Returns the shadow row (with its `reflection`) or None."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, limit)
    except Exception:
        return None
    now = time.time() if now is None else now
    excl = exclude_ts or set()
    for r in reversed(rows):
        if r.get("kind") != "interrogate" or r.get("genuine") is not True:
            continue
        ts = float(r.get("ts") or 0.0)
        if now - ts > max_age_s:
            return None        # rows are oldest-first; the newest genuine fire is already too old
        if ts in excl or not (r.get("reflection") or "").strip():
            continue
        return r
    return None


def status() -> dict:
    """For the pulse/HUD — same shape convention as core/reentry.py's / core/watershed.py's status()."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan on every ~6s HUD poll. Counts/rates are
        # now over the last-2000-row window (tail_rows handles a missing file itself, fail-open []).
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"fires": 0, "genuine": 0, "hollow": 0, "skips": {}}
    fires = [r for r in rows if r.get("kind") == "interrogate"]
    skips = [r for r in rows if r.get("kind") == "skip"]
    genuine = sum(1 for r in fires if r.get("genuine") is True)
    hollow = sum(1 for r in fires if r.get("genuine") is False)
    unjudged = len(fires) - genuine - hollow
    skip_reasons: dict[str, int] = {}
    for s in skips:
        skip_reasons[s.get("skip", "?")] = skip_reasons.get(s.get("skip", "?"), 0) + 1
    return {"fires": len(fires), "genuine": genuine, "hollow": hollow, "unjudged": unjudged,
            "genuine_rate": round(genuine / len(fires), 3) if fires else None,
            "skips": skip_reasons,
            "verdict": (f"{genuine}/{len(fires)} genuine ({round(100*genuine/len(fires))}%)" if fires
                        else "no fires yet")}


if __name__ == "__main__":
    print(json.dumps(status(), indent=2, ensure_ascii=False))

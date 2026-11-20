"""
GROUND GRADE SHADOW (J-2890, finding F-3558, prompt row P-0088; log-only, observe-only).

The P-0088 grounder (core/left_lane.py ground_thought, mixtral:8x7b on Ramses :11438) is checked by exactly one thing:
a title-leak regex. That measures a vocabulary slip, not whether a grounding is true or useful, and nothing else reads a
grounding (F-3558). This module is the missing evaluator: for about 1 in 20 successful groundings it asks ONE model from a
different family than the grounder (falcon3:7b / TII on the local CPU hub :11440, the judge_panel JUDGE_2 hub; not
mixtral, not Ramses, which is the founder's gaming machine) two blind questions over (raw thought, grounding), and appends
one row to data/ground_grade_shadow.jsonl:

  Q1 adds_detail      does the grounding name a concrete detail (an object, place, person, file or number) that the raw
                      thought does not contain? The judge must quote it.
  Q2 names_mechanism  does the grounding name a real mechanism of the thing the thought refers to (a part, a process, a
                      cause), or does it only restate or interpret the thought?

The model call goes through judge_panel's own single-judge primitive (judge_panel._ask against judge_panel.JUDGE_2), not a new
HTTP client. judge_panel.rule()/rule_detail() are deliberately NOT used: they always include JUDGE_1, which is mixtral, the
grounder's own family, and the decoupled-judge law forbids a mixtral vote on a mixtral output.

OBSERVE-ONLY BY CONSTRUCTION (founder laws: nothing is fed back; no system acts later on its own):
  * schedule() returns None always, takes only immutable strings, and its only write is one append per graded grounding to
    its own ledger via core.shadow_log. Nothing reads the row to change the grounder, pass 3, a prompt, a threshold or any
    store. The only reader is scripts/read_ground_grade.py (base rates, the control hit rate, the outcome reconcile).
  * deliberation.deliberate() calls schedule() from a finally AFTER the three passes have finished (the pulse is over),
    so the idle step never waits on, and never shares a result with, the grader. The model call is a fire-and-forget
    asyncio task bounded to MAX_INFLIGHT; a draw while busy logs a {"skipped": "busy"} row and is not graded.
  * fail-open and quiet: any error is swallowed (debug log); once past the gates a model failure is recorded as a
    {"failed": ...} row so the failure rate is readable.

JUDGE-HONESTY GUARDS (the judge is a 7B model, so its own output is checked deterministically, never trusted as written):
  * Q1 counts as a VERIFIED detail only if the quote really is in the grounding (normalised substring) and is NOT in the raw
    thought. A judge that invents or misattributes a quote cannot raise the share.
  * a standing POSITIVE CONTROL: on the first graded grounding of each process and every CONTROL_EVERY-th after, Q1 is
    asked again on the real grounding with one invented concrete sentence appended; `control_hit` records whether the judge
    quoted something from that sentence. A judge that misses its control carries no information.
  * BASE RATE: the reader reports the share of true answers to each question. A judge that says the same thing nine times in
    ten measures nothing (docs/guidelines/prompt_registry.md section 5); read that number first.

Founder laws: the grounder is judged by something other than itself; log only; transfer the function, not the mechanism.
RESTART-GATED: nothing here runs until Du restarts from a merged master. Kill switch: GROUND_GRADE_SHADOW = False.
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
import time
import uuid
from pathlib import Path

logger = logging.getLogger("nascence.ground_grade")

GROUND_GRADE_SHADOW = True            # J-2890: shadow, observe-only. Kill = False (takes effect at the next boot).
SAMPLE_P = 0.05                       # 1 in 20 successful groundings (briefing); a module constant so a test can set it
LEDGER = Path(__file__).resolve().parent.parent / "data" / "ground_grade_shadow.jsonl"
JUDGE_TIMEOUT_S = 120                 # the lazy local CPU hub can need a cold load; nothing waits on this call
JUDGE_NUM_PREDICT = 200
MAX_INFLIGHT = 1
CONTROL_EVERY = 5                     # positive control on graded grounding 0, 5, 10, ... of each process
JUDGE_VERSION = 1
_THOUGHT_CAP = 1500
_GROUNDING_CAP = 2000

Q1_KEY = "adds_detail"
Q2_KEY = "names_mechanism"

Q1_SYSTEM = (
    "You compare two texts. THOUGHT is a short private thought. GROUNDING is a note written about it by someone else. "
    "Question: does the GROUNDING name a specific, concrete detail (a particular object, place, person, file or number) "
    "that the THOUGHT does not contain? A general idea, a theme, a feeling or a rewording of the THOUGHT is not a detail. "
    "If yes, copy the detail from the GROUNDING exactly, at most 20 words, into \"why\". If no, put an empty string in \"why\".\n"
    "Output ONLY JSON: {\"adds_detail\": true or false, \"why\": \"exact quote from the GROUNDING, or empty\"}"
)
Q2_SYSTEM = (
    "You compare two texts. THOUGHT is a short private thought. GROUNDING is a note written about it by someone else. "
    "Question: does the GROUNDING name a real mechanism of the thing the THOUGHT refers to, meaning how that thing "
    "actually works or is built (a part, a process, a cause)? Answer false if the GROUNDING only restates the THOUGHT in "
    "other words, interprets it, or gives its meaning. Put a short reason into \"why\".\n"
    "Output ONLY JSON: {\"names_mechanism\": true or false, \"why\": \"one short sentence\"}"
)

# One invented concrete detail per control, none of them anything a grounding could contain by accident.
CONTROL_SENTENCES = (
    "The spare key hangs on the third brass hook in the Hartley cellar, behind crate number 4417.",
    "Ingrid Solvang keeps the ledger in a tin box under the northern pier of Marrow Quay.",
    "The file is called quillfeather_manifest_9082.dat and it was last written on a Tuesday at 03:41.",
)

_inflight = 0
_graded = 0                           # per-process count of graded groundings (drives the control cadence)
_tasks: set = set()                   # strong refs so a fire-and-forget task is not garbage collected mid-call


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", (s or "").lower()).split())


def _family(model: str) -> str:
    m = re.match(r"[a-z]+", (model or "").lower())
    return m.group(0) if m else (model or "").lower()


def _judge_url() -> str:
    from core import judge_panel
    return judge_panel.JUDGE_2


def families_differ() -> bool:
    """True if the judge's model family is not the grounder's. Reads the router's own url->model map and left_lane's
    GROUND_MODEL; fails closed (False)."""
    try:
        from core.model_client import _model_for
        from core import left_lane
        a, b = _family(_model_for(_judge_url())), _family(left_lane.GROUND_MODEL)
        return bool(a) and bool(b) and a != b
    except Exception:
        return False


def build_user(thought: str, grounding: str) -> str:
    """The judge's user prompt. Pure. Blind: no model names, no hint of what is expected."""
    return f"THOUGHT:\n{str(thought)[:_THOUGHT_CAP]}\n\nGROUNDING:\n{str(grounding)[:_GROUNDING_CAP]}"


def verify_quote(quote: str, thought: str, grounding: str) -> dict:
    """Deterministic check of Q1's quote. Pure; never raises. in_grounding: the normalised quote is a substring of the
    normalised grounding. in_thought: it is also a substring of the raw thought (so not new). A detail counts as verified
    only if in_grounding and not in_thought."""
    nq = _norm(quote)
    if len(nq) < 3:
        return {"in_grounding": False, "in_thought": False, "verified": False}
    in_g = nq in _norm(grounding)
    in_t = nq in _norm(thought)
    return {"in_grounding": in_g, "in_thought": in_t, "verified": bool(in_g and not in_t)}


def control_hit(quote: str, inserted: str) -> bool:
    """True if the quote lies inside (or is the same text as) the inserted control sentence, or shares >= 60 percent of
    its words with it."""
    nq, ni = _norm(quote), _norm(inserted)
    if len(nq) < 3 or not ni:
        return False
    if nq in ni or ni in nq:
        return True
    tq, ti = set(nq.split()), set(ni.split())
    return bool(tq) and len(tq & ti) / float(len(tq)) >= 0.6


async def _ask(session, system: str, user: str, key: str):
    """One judge call through judge_panel's own primitive: (verdict|None, why|None, err|None, elapsed_s)."""
    from core import judge_panel
    return await judge_panel._ask(session, _judge_url(), system, user, key,
                                  timeout=JUDGE_TIMEOUT_S, num_predict=JUDGE_NUM_PREDICT)


async def grade_one(thought: str, grounding: str, *, control_text: str = "", ask=None) -> dict:
    """Grade one (thought, grounding) pair and return the ledger row. With control_text, Q1 only is asked on the grounding
    with that sentence appended and the row is a control row. `ask` is a test seam: an async callable
    (system, user, key) -> (verdict, why, err, elapsed_s); the default opens one aiohttp session and uses judge_panel._ask.
    Never raises: a model failure returns a {"failed": ...} row."""
    from core.model_client import _model_for
    from core import left_lane
    jurl = _judge_url()
    shown = (grounding.rstrip() + " " + control_text) if control_text else grounding
    row = {"ts": round(time.time(), 1), "row_id": uuid.uuid4().hex[:12], "jv": JUDGE_VERSION,
           "control": bool(control_text), "judge_model": _model_for(jurl), "judge_hub": jurl.rsplit(":", 1)[-1],
           "grounder_model": left_lane.GROUND_MODEL, "thought_chars": len(thought), "grounding_chars": len(grounding)}
    t0 = time.monotonic()
    own = None
    try:
        if ask is None:
            import aiohttp
            own = aiohttp.ClientSession()

            async def ask(system, user, key, _s=own):             # noqa: E306 -- default seam
                return await _ask(_s, system, user, key)
        user = build_user(thought, shown)
        v1, why1, err1, _ = await ask(Q1_SYSTEM, user, Q1_KEY)
        quote = str(why1 or "").strip() if v1 else ""
        vq = verify_quote(quote, thought, shown) if v1 else {"in_grounding": False, "in_thought": False, "verified": False}
        row.update({"q1_detail": v1, "q1_quote": quote[:240], "q1_quote_in_grounding": vq["in_grounding"],
                    "q1_quote_in_thought": vq["in_thought"], "q1_verified": bool(v1 and vq["verified"]), "q1_err": err1})
        if control_text:
            row["control_inserted"] = control_text
            row["control_hit"] = bool(v1 and control_hit(quote, control_text))
        else:
            v2, why2, err2, _ = await ask(Q2_SYSTEM, user, Q2_KEY)
            row.update({"q2_mechanism": v2, "q2_why": str(why2 or "")[:300], "q2_err": err2,
                        "thought": thought[:600], "grounding": grounding[:1200]})
            if v1 is None and v2 is None:
                row["failed"] = str(err1 or err2 or "no_answer")
        if control_text and v1 is None:
            row["failed"] = str(err1 or "no_answer")
    except Exception as exc:     # noqa: BLE001 -- fail-open; the failure itself is a readable signal
        row["failed"] = type(exc).__name__
    finally:
        if own is not None:
            try:
                await own.close()
            except Exception:    # noqa: BLE001
                pass
    row["latency_s"] = round(time.monotonic() - t0, 2)
    return row


async def _run(thought: str, grounding: str) -> None:
    global _inflight, _graded
    from core import shadow_log
    try:
        k = _graded
        _graded += 1
        shadow_log.append(LEDGER, await grade_one(thought, grounding))
        if k % CONTROL_EVERY == 0:
            ctl = CONTROL_SENTENCES[(k // CONTROL_EVERY) % len(CONTROL_SENTENCES)]
            shadow_log.append(LEDGER, await grade_one(thought, grounding, control_text=ctl))
    except Exception as exc:     # noqa: BLE001
        logger.debug("[ground_grade] grade skipped (fail-open): %s", exc)
    finally:
        _inflight -= 1


def schedule(thought: str, grounding, source: str = "emissary", *, rng=None) -> None:
    """Called by deliberation.deliberate() from a finally, after the pulse. Samples 1 in 20 successful groundings,
    schedules the grader on the running loop and returns at once. ALWAYS returns None. Fail-open: no running loop, a
    disabled switch, no grounding, a same-family judge or any error -> nothing happens."""
    global _inflight
    try:
        if not GROUND_GRADE_SHADOW:
            return None
        thought, grounding = str(thought or "").strip(), str(grounding or "").strip()
        if not thought or not grounding or source != "emissary":
            return None
        if (rng or random).random() >= SAMPLE_P:
            return None
        if not families_differ():
            return None
        loop = asyncio.get_running_loop()
        if _inflight >= MAX_INFLIGHT:
            from core import shadow_log
            shadow_log.append(LEDGER, {"ts": round(time.time(), 1), "jv": JUDGE_VERSION, "skipped": "busy"})
            return None
        _inflight += 1
        try:
            task = loop.create_task(_run(thought, grounding))
        except Exception:
            _inflight -= 1
            raise
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    except Exception as exc:     # noqa: BLE001 -- fail-open is the contract
        logger.debug("[ground_grade] not scheduled (fail-open): %s", exc)
    return None

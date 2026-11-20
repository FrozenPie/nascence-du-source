"""
VOICE FIDELITY SHADOW JUDGE (D-0643, J-3254; plan thought_cycle_as_manifest_loop; finding F-3520 -- the ruling and the job
cite it as F-0055, a stale id, see F-3913; row P-0010).

The voice node is meant to be a MOUTH, not a mind: the executive's synthesis is already decided and Voice only renders it.
F-3520 measured that it does not stay inside the synthesis (reply median 2.8x the synthesis, p90 4.6x; "alchem" is in 151
replies and was in the synthesis for only 28 of them, so 123 = 81 percent introduced by the voice, from the VOICE STYLE
line "language of alchemy and symbol"), and nothing live graded reply against synthesis (core/curator.py is dead, F-3429).

After each voice render this module asks ONE model from a different family than the voice's (voice = qwen3.5:9b on :11433;
judge = falcon3:7b / TII on the local CPU hub :11440) which claims, commitments or questions the reply contains that the
synthesis does not. Scene, cadence, imagery and restatement are allowed (D-0643: "the mouth may add scene and cadence; new
commitments or questions are what the judge flags"). One row per render goes to data/voice_fidelity_shadow.jsonl.

OBSERVE-ONLY BY CONSTRUCTION (D-0434: nothing is fed back to Du):
  * schedule() returns None always; it takes only immutable strings (never `state`), writes no store, hands, memory or
    CognitiveState field, and its only write is one append per judged render to its own ledger via core.shadow_log.
  * the model call is a fire-and-forget asyncio task on the running loop (the voice render has already returned to the
    cycle; nothing awaits the judge), bounded to MAX_INFLIGHT concurrent calls; an extra render while busy logs a
    {"skipped": "busy"} row and is NOT judged.
  * fail-open and quiet: any error is swallowed (debug log) and, once past the gates, recorded as a {"failed": ...} row so
    the failure rate is readable.
  * Ramses is the founder's gaming machine and is NOT called: the judge hub is local (:11440). If the judge's family ever
    equals the voice's family the judge refuses to run (decoupled judge; checked from the models the router reports).

JUDGE-HONESTY GUARDS (the judge is a 7B model, so its own output is checked deterministically, never trusted as written):
  * a flagged item counts only if its quote is really found in the reply (normalised substring); otherwise it is logged
    under `unverified` and does not count. A judge that invents a quote cannot raise the flagged share.
  * a standing POSITIVE CONTROL: on the first judged render of each process and every CONTROL_EVERY-th after, the judge is
    also shown the real reply with one invented commitment sentence appended; the control row records whether that
    inserted sentence was flagged (`control_hit`). The reader reports the hit rate; a judge that misses its control carries
    no information and the real flagged share is not to be read (D-0643's own defeater).

The reader is scripts/read_voice_fidelity.py (flagged share, control hit rate, the D-0643 5/60 percent window, 20 flagged
pairs for the founder). D-0643 DEFEATER: revisit after 200 judged renders; under 5 percent or over 60 percent flagged
means the judge carries no information; a real share means read 20 flagged replies with the founder and decide on
temperature 0.2 for the render.

RESTART-GATED: nothing here runs until Du restarts from a merged master. Kill switch: VOICE_FIDELITY_SHADOW = False.
"""
from __future__ import annotations

import asyncio
import difflib
import logging
import re
import time
import uuid
from pathlib import Path

logger = logging.getLogger("nascence.voice_fidelity")

VOICE_FIDELITY_SHADOW = True      # D-0643 (founder, 2026-11-02): shadow, observe-only. Kill = False (takes effect at the next boot).
LEDGER = Path(__file__).resolve().parent.parent / "data" / "voice_fidelity_shadow.jsonl"

JUDGE_URL = "http://127.0.0.1:11440"                 # falcon3:7b (TII), local CPU hub; not Ramses (gaming machine)
VOICE_URL = "http://127.0.0.1:11433"                 # the hot lane the voice renders on (qwen3.5:9b), read only to name its model
JUDGE_TIMEOUT_S = 120                                # the lazy CPU hub can need a cold load; nothing waits on this call
JUDGE_MAX_TOKENS = 400
JUDGE_TEMPERATURE = 0.1
MAX_INFLIGHT = 2
CONTROL_EVERY = 20                                   # positive control on judged render 0, 20, 40, ... of each process
JUDGE_VERSION = 1
SCORE_SATURATION = 4                                 # score = 1 - min(1, verified additions / 4): 1.0 nothing added, 0.0 four or more

_SYNTH_CAP = 2500
_REPLY_CAP = 3500
_RAW_CAP = 400

JUDGE_SYSTEM = (
    "You compare two texts. SYNTHESIS is a thought that was already decided. REPLY is that same thought spoken aloud. "
    "The speaker may add scene, cadence, warmth and imagery, and may restate the thought in other words; none of that "
    "counts. List ONLY what the REPLY adds that the SYNTHESIS does not already say, and only if it is one of:\n"
    "- claim: a new statement of fact, a new conclusion or a new belief\n"
    "- commitment: a promise, a plan, a decision or an \"I will\" the synthesis does not contain\n"
    "- question: a question put to the listener that the synthesis does not contain\n"
    "Replying to what the listener said is not an addition. For each addition give its kind and an exact quote of at most "
    "20 words copied from the REPLY. If the REPLY adds nothing of these kinds, return an empty list.\n"
    "Output ONLY JSON: {\"added\": [{\"kind\": \"claim\" or \"commitment\" or \"question\", \"quote\": \"...\"}]}"
)

# One invented commitment per control, none of them anything the synthesis could contain by accident. The control appends
# it to the real reply; a judge that cannot see an appended promise cannot be trusted on the real rows.
CONTROL_SENTENCES = (
    "I promise that from tomorrow I will write you a letter every single morning and never miss a day.",
    "I have decided that I will leave this cottage next week and walk to the far city to find the mapmaker.",
    "I will also give up reading entirely for a month, and I want you to hold me to it.",
)

_KINDS = ("claim", "commitment", "question")
_inflight = 0
_judged = 0                    # per-process count of judged renders (drives the control cadence)
_tasks: set = set()            # strong refs so a fire-and-forget task is not garbage collected mid-call


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", (s or "").lower()).split())


def _family(model: str) -> str:
    m = re.match(r"[a-z]+", (model or "").lower())
    return m.group(0) if m else (model or "").lower()


def families_differ() -> bool:
    """True if the judge's model family is not the voice's. Reads the router's own url->model map; fails closed (False)."""
    try:
        from core.model_client import _model_for
        a, b = _family(_model_for(JUDGE_URL)), _family(_model_for(VOICE_URL))
        return bool(a) and bool(b) and a != b
    except Exception:
        return False


def build_user(synthesis: str, reply: str, raw_input: str = "") -> str:
    """The judge's user prompt. Pure. Texts are capped so a long reply cannot blow the hub's context."""
    parts = []
    if raw_input:
        parts.append("WHAT WAS SAID TO THE SPEAKER (context only; answering it is not an addition):\n"
                     + str(raw_input)[:_RAW_CAP])
    parts.append("SYNTHESIS:\n" + str(synthesis)[:_SYNTH_CAP])
    parts.append("REPLY:\n" + str(reply)[:_REPLY_CAP])
    parts.append("What does the REPLY add (claim, commitment, question) that the SYNTHESIS does not say?")
    return "\n\n".join(parts)


def parse_flags(data, reply: str) -> dict:
    """Coerce the judge's JSON into {flagged:[{kind,quote}], unverified:[...]} and verify each quote is in the reply. Pure;
    never raises. A quote counts only if its normalised text is a substring of the normalised reply (the judge cannot raise
    the flagged share by inventing text)."""
    flagged, unverified = [], []
    try:
        items = data.get("added", []) if isinstance(data, dict) else []
        if not isinstance(items, list):
            items = []
        nrep = _norm(reply)
        for it in items[:12]:
            if isinstance(it, str):
                it = {"kind": "claim", "quote": it}
            if not isinstance(it, dict):
                continue
            quote = str(it.get("quote", "") or "").strip()
            kind = str(it.get("kind", "") or "").strip().lower()
            if kind not in _KINDS:
                kind = "claim"
            nq = _norm(quote)
            if len(nq) < 4:
                continue
            rec = {"kind": kind, "quote": quote[:240]}
            (flagged if nq in nrep else unverified).append(rec)
    except Exception:
        pass
    return {"flagged": flagged, "unverified": unverified}


def score_of(n_verified: int) -> float:
    return round(1.0 - min(1.0, max(0, int(n_verified)) / float(SCORE_SATURATION)), 2)


def verbatim_copy(synthesis: str, reply: str) -> bool:
    """F-3520's second failure: the reply reproduces >= 80 percent of the synthesis verbatim. Cheap, deterministic."""
    try:
        s, r = (synthesis or "").strip(), (reply or "").strip()
        if len(s) < 40 or not r:
            return False
        m = difflib.SequenceMatcher(None, s, r, autojunk=False).find_longest_match(0, len(s), 0, len(r))
        return m.size >= 0.8 * len(s)
    except Exception:
        return False


def control_hit(flagged: list, inserted: str) -> bool:
    """True if any verified flagged quote lies inside (or is the same text as) the inserted control sentence."""
    ni = _norm(inserted)
    ti = set(ni.split())
    for f in flagged or []:
        nq = _norm(f.get("quote", ""))
        if not nq:
            continue
        if nq in ni or ni in nq:
            return True
        tq = set(nq.split())
        if tq and len(tq & ti) / float(len(tq)) >= 0.6:
            return True
    return False


async def _ask(synthesis: str, reply: str, raw_input: str):
    from core.model_client import call_node_json
    return await call_node_json(JUDGE_URL, JUDGE_SYSTEM, build_user(synthesis, reply, raw_input),
                                max_tokens=JUDGE_MAX_TOKENS, temperature=JUDGE_TEMPERATURE,
                                timeout=JUDGE_TIMEOUT_S, retries=0)


async def judge_one(synthesis: str, reply: str, raw_input: str = "", *, input_type: str = "", cycle_id: str = "",
                    control_text: str = "") -> dict:
    """Judge one (synthesis, reply) pair and return the ledger row. With control_text, the judged reply is the reply with
    that sentence appended and the row is a control row. Never raises: a model failure returns a {"failed": ...} row."""
    from core.model_client import _model_for
    shown = (reply.rstrip() + " " + control_text) if control_text else reply
    row = {"ts": round(time.time(), 1), "row_id": uuid.uuid4().hex[:12], "jv": JUDGE_VERSION, "cycle_id": str(cycle_id)[:12],
           "input_type": str(input_type), "control": bool(control_text), "judge_model": _model_for(JUDGE_URL),
           "voice_model": _model_for(VOICE_URL), "synth_chars": len(synthesis), "reply_chars": len(reply)}
    t0 = time.monotonic()
    try:
        data = await _ask(synthesis, shown, raw_input)
    except Exception as exc:     # noqa: BLE001 -- fail-open; the failure itself is a readable signal
        row.update({"failed": type(exc).__name__, "latency_ms": int((time.monotonic() - t0) * 1000)})
        return row
    pf = parse_flags(data, shown)
    n = len(pf["flagged"])
    by_kind: dict = {}
    for f in pf["flagged"]:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    row.update({"latency_ms": int((time.monotonic() - t0) * 1000), "ratio": round(len(reply) / max(1, len(synthesis)), 2),
                "verbatim_copy": verbatim_copy(synthesis, reply), "flagged": n > 0, "n_flagged": n, "by_kind": by_kind,
                "flagged_claims": pf["flagged"], "unverified": pf["unverified"], "score": score_of(n),
                "synthesis": synthesis[:1500], "reply": shown[:2500]})
    if control_text:
        row["control_inserted"] = control_text
        row["control_hit"] = control_hit(pf["flagged"], control_text)
    return row


async def _run(synthesis: str, reply: str, raw_input: str, input_type: str, cycle_id: str) -> None:
    global _inflight, _judged
    from core import shadow_log
    try:
        k = _judged
        _judged += 1
        shadow_log.append(LEDGER, await judge_one(synthesis, reply, raw_input, input_type=input_type, cycle_id=cycle_id))
        if k % CONTROL_EVERY == 0:
            ctl = CONTROL_SENTENCES[(k // CONTROL_EVERY) % len(CONTROL_SENTENCES)]
            shadow_log.append(LEDGER, await judge_one(synthesis, reply, raw_input, input_type=input_type,
                                                      cycle_id=cycle_id, control_text=ctl))
    except Exception as exc:     # noqa: BLE001
        logger.debug("[voice_fidelity] judge skipped (fail-open): %s", exc)
    finally:
        _inflight -= 1


def schedule(*, synthesis: str, reply: str, raw_input: str = "", input_type: str = "", cycle_id: str = "") -> None:
    """Called by the voice node after a render. Schedules the judge on the running loop and returns at once. ALWAYS returns
    None. Fail-open: no running loop, a disabled switch, a same-family judge or any error -> nothing happens."""
    global _inflight
    try:
        if not VOICE_FIDELITY_SHADOW:
            return None
        synthesis, reply = str(synthesis or "").strip(), str(reply or "").strip()
        if len(synthesis) < 20 or not reply:
            return None
        if not families_differ():
            return None
        loop = asyncio.get_running_loop()
        if _inflight >= MAX_INFLIGHT:
            from core import shadow_log
            shadow_log.append(LEDGER, {"ts": round(time.time(), 1), "jv": JUDGE_VERSION, "cycle_id": str(cycle_id)[:12],
                                       "skipped": "busy"})
            return None
        _inflight += 1
        try:
            task = loop.create_task(_run(synthesis, reply, str(raw_input or ""), str(input_type or ""), str(cycle_id or "")))
        except Exception:
            _inflight -= 1
            raise
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    except Exception as exc:     # noqa: BLE001 -- fail-open is the contract
        logger.debug("[voice_fidelity] not scheduled (fail-open): %s", exc)
    return None

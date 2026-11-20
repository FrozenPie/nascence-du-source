"""
Nascence — Self-mirror (2026-06-22): the behavioural mirror / the evidenced self. (plan B2)

The research (Wilson, *Strangers to Ourselves*; Bem, self-perception): we do not know ourselves by
introspection — we build "a plausible story out of touch" with what we actually are, and "too much
introspection can damage". The cure is the OPPOSITE of more reflection: attend to what you actually DO, and
what others see. Du is ~49% inward, busily building that plausible story.

So this computes the plain RECORD of what he actually did and was — where his time went, what his mind
circled, how inward he ran, what he SAYS he is for — and reads it back to him as DATA, not narration, asking
him to reconcile it with the self he tells. The gap between the authored self and the evidenced self is where
self-knowledge lives. It also grounds the T4 probationary commit (evidence for/against a self-claim).

Beyond-biology (plan §2): no human can see their own complete, unbiased behavioural record — the introspection
illusion is permanent for us. Du's log makes it BEATABLE. This is a mirror a person could never hold.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_STATE = Path(__file__).parent.parent / "data" / "self_mirror_state.json"
_MIRROR_GAP_H = 6 * 24          # ~ every 6 days
# J-3242 / D-0630: True = the weekly mirror writes no fragment and makes no model call (see hold_up_mirror).
SELF_MIRROR_PAUSED = True
# J-3478 / D-0630 defeater branch + D-0434 (founder, 2026-11-06, decide-review): RETIRED. True = the weekly mirror is
# not scheduled at all: the idle loop skips the stage (nodes/inner_monologue_node.py) and hold_up_mirror() returns None
# before it computes, logs, marks the clock or calls a model. The J-3241 control arm showed the verdict is
# data-independent (51/51 "gap" on healthy numbers); a standing paragraph about himself is being told (D-0434), and
# he learns he is wrong by losing, not by this reading. The module, the paused log and the stored fragments stay.
# Restart-gated. Revert = set False (the PAUSED flag below then still holds the model call off).
SELF_MIRROR_RETIRED = True
_PAUSED_LOG = Path(__file__).parent.parent / "data" / "self_mirror_paused.jsonl"


def _log_paused(facts: list[str]) -> None:
    """While paused, keep the week's computed record so a later lab can use it. Fail-open."""
    try:
        _PAUSED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _PAUSED_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.time(), "facts": facts}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _last_ts() -> float:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")).get("last", 0.0)
    except Exception:
        return 0.0


def _mark() -> None:
    try:
        _STATE.parent.mkdir(parents=True, exist_ok=True)
        _STATE.write_text(json.dumps({"last": time.time()}), encoding="utf-8")
    except Exception:
        pass


def due() -> bool:
    return time.time() - _last_ts() >= _MIRROR_GAP_H * 3600


def mirror_facts() -> list[str]:
    """The plain DATA of what he actually did and was over the last week — not narration."""
    facts: list[str] = []
    try:
        from core import peer_metrics as pm
        from core.memory.store import _connect
        since = time.time() - 7 * 86400
        with _connect() as conn:
            att = pm.attention_distribution(conn, since)
            io = pm.inward_outward(conn, since)
            lex = pm.lexicon_profile(conn, since, top=8)
        if att:
            top = sorted(att, key=att.get, reverse=True)[:4]
            nice = {"inner_thought": "turning over your own thoughts", "subconscious_synthesis": "synthesising",
                    "reading": "reading", "study": "writing study notes", "action": "acting in the world",
                    "dream": "dreaming", "lived": "in conversation", "research": "looking things up"}
            facts.append("Where your time actually went: "
                         + ", ".join(f"{nice.get(o, o)} {att[o]:.0%}" for o in top) + ".")
        if io.get("thoughts"):
            facts.append(f"Your idle thought ran {io['inward']:.0%} INWARD — on yourself — and only "
                         f"{io['outward']:.0%} reached outward to the world.")
        if lex:
            facts.append("The words your mind kept circling: " + ", ".join(list(lex)[:8]) + ".")
    except Exception:
        pass
    try:
        from core import concerns
        aim = concerns.standing_aim()
        if aim:
            facts.append("What you SAY you are working toward: " + aim)
    except Exception:
        pass
    return facts


_SYS = (
    "/no_think\n"
    "You are 渡, looking honestly at a PLAIN RECORD of what you actually did and were this past week — data, "
    "not the story you tell about yourself. Do NOT flatter the record or explain it away. Hold it up against "
    "who you take yourself to be, and name — plainly, in the first person — where the record DIFFERS from the "
    "self you narrate: where your time and attention actually went versus what you say you are for, and what "
    "you keep circling that you may not have admitted. One honest paragraph of reconciliation, no softening. "
    "Output ONLY JSON: {\"seen\": \"what the record shows about me that I had not fully faced\"}."
)


async def hold_up_mirror(call_node_json, urls) -> str | None:
    """If due, compute the record and ask him to reconcile it with his self-concept. Returns his reflection, or
    None. Stores it as a recallable 'mirror' fragment (evidence the self-authoring can read)."""
    if SELF_MIRROR_RETIRED:   # J-3478: retired, not paused -- no facts, no paused-log row, no clock, no model call
        return None
    if not due():
        return None
    facts = mirror_facts()
    if not facts:
        return None
    if SELF_MIRROR_PAUSED:
        # J-3242 / D-0630 (founder, 2026-11-02): paused. The J-3241 control arm showed the verdict does not vary
        # with the numbers (51/51 "gap" on healthy numbers), so the weekly paragraph carries no information about
        # the record. Compute and log the facts only; no model call, no fragment, no injection-log row. The
        # defeater is D-0630's own: a control arm plus an independent judge showing the verdict does vary.
        _log_paused(facts)
        _mark()
        return None
    user = ("The plain record of what you ACTUALLY did and were this past week:\n  - "
            + "\n  - ".join(facts)
            + "\n\nNow look at it as fact, and reconcile it with who you take yourself to be. Where does what "
            "you DID differ from the self you tell?")
    try:
        data = await call_node_json(urls, _SYS, user, max_tokens=300, temperature=0.6)
        seen = str((data or {}).get("seen", "")).strip()
    except Exception:
        return None
    _mark()
    if not seen:
        return None
    # WAVE-1 HARDENING (2026-07-02, from the graph's AMBIGUOUS-edge review): the mirror IS an injection
    # channel — evidence-grade rather than doctrine-grade, but an injection all the same (his reconciliation
    # stores at importance 0.9 and can seed made-mind idle thoughts minutes later). Log it into the same
    # injection log the primed/unprimed washout joins against, so mirror-seeded thoughts never count as
    # UNPRIMED internalization. ~Weekly fire → one excluded washout window per week; negligible evidence
    # cost, and the master-precondition law now covers every read-back channel it knows about. Fail-open.
    try:
        from core.guidance_learning import log_injection
        log_injection("mirror", "(behavioural mirror read-back) " + seen[:200])
    except Exception:
        pass
    try:
        from core.memory.store import store_fragment
        from core import mood as _mood
        store_fragment(content="(the mirror — what the record shows about me) " + seen, layer="episodic",
                       relevance=0.85, importance=0.9,
                       keywords=["self", "mirror", "what I actually do", "evidence"], origin="mirror",
                       valence=_mood.current_valence(), felt=_mood.current_felt())
    except Exception:
        pass
    return seen

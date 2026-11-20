"""
CONDENSED THOUGHT — Phase 0 shadow twin (docs/staged/condensed_thought.md §4; J-2281, 2026-10-17).

On a fraction TWIN_RATE of idle ticks, AFTER the live paragraph thought has been generated and parsed,
the twin makes ONE extra short call on the same hot model with the SAME user prompt (same seed parts)
and a different instruction: hold the thought in the fewest words it needs, or none. Its output is
written to data/logs/condensed_thought_shadow.jsonl and NOWHERE ELSE.

OBSERVE-ONLY BY CONSTRUCTION (plan §4.2, §6 last kill line):
  * shadow_tick() always returns None — the caller has nothing to assign.
  * it receives only immutable values (strings, numbers) from the caller, never `state`, never self.
  * it imports no store, hands, trains, deliberation, moment or CognitiveState writer; its only write is
    one append to its own ledger via core.shadow_log.append.
  * scripts/_test_condensed_thought.py asserts all of the above, plus fail-open and the rate gate.

Founder rulings binding this module: D-0460 (live on :11433, TWIN_RATE 0.25, idle tick only, cost kill at
+5 s on the idle-gap median), D-0434 (nothing here is ever rendered to Du). The judge does NOT run here:
it runs offline on the Ramses judge panel (scripts/judge_condensed_thought.py) so the live tick never
waits on a CPU judge hub; verdicts go to a sibling ledger joined by row_id (the §4.3 `judge` field is
left null in the shadow row and filled at read time).

D-0633 (J-3245, 2026-11-06): TWIN FIX + RESTART OF THE CLOCK. The v1 twin (a 430-char system prompt against the live
thought's 3.7 to 6.7k) parroted the book invitation that sits in ~94 percent of seeds ("make your thought exactly:
OPEN THE BOOK"): ~18 percent of v1 rows are the invitation or its first word. v2 hands the twin the SAME system text the
live thought was given (the caller passes the string it actually sent) plus a twin instruction that names an invitation
phrase as a way of acting, not a thought, and the live user prompt's closing question is swapped for the twin's own (without
the swap the live system text pulled 26 of 60 replies back to the paragraph JSON; replay 2026-11-06, scripts/_replay_J3245_twin_prompt.py).
Every v2 row carries twin_v=2 and the first v2 tick of each process writes one
marker row {"marker": "twin_restart"}; the judge and the reader score only twin_v >= 2 by default, the 2,700-odd v1 rows
stay in the ledger as history. twin.echo_invite is the deterministic echo flag (the D-0633 defeater reads it: > 5 percent
of v2 rows echoing means revisit).

RESTART-GATED: CONDENSED_TWIN was flipped to True by D-0471 (travis, 2026-10-17, J-2349); it takes effect at the next boot only.
COST KILL (D-0460): the +5 s idle-gap-median check is a READ-TIME check (scripts/read_condensed_thought.py kill.cost_kill_gap_gt_5s),
not a runtime auto-trip; the response is a human/job setting CONDENSED_TWIN=False (or TWIN_RATE=0).
"""
from __future__ import annotations

import logging
import random
import re
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

CONDENSED_TWIN = True           # D-0471 (J-2349): True = the shadow twin runs from the next boot (nothing reaches Du either way). Kill = set False.
TWIN_RATE = 0.25                # D-0460 / D-0458: a quarter of idle ticks
TWIN_MAX_TOKENS = 48
TWIN_TIMEOUT_S = 30             # one short call; a slow hot model must not stall the idle tick for long

LEDGER = Path(__file__).resolve().parent.parent / "data" / "logs" / "condensed_thought_shadow.jsonl"

TWIN_VERSION = 2                # D-0633 (J-3245): v1 = standalone 430-char system prompt (rows before the restart); v2 = live system text + TWIN_INSTRUCTION

# v1, kept verbatim as the HISTORY constant (the ledger's pre-restart rows were produced by this as the WHOLE system
# prompt; scripts/_replay_J3245_twin_prompt.py replays it against v2 on recorded seeds). Not used by the live path.
TWIN_INSTRUCTION_V1 = (
    "One thought, in the fewest words it needs — a few words, a single word, or none at all if the thought "
    "has no words and is only a sense of something. Never a sentence for its own sake. If there are no "
    "words, say so.\n\n"
    "Output ONLY JSON: {\"kind\": \"fragment\" or \"tick\" or \"silent\", \"words\": \"...\", "
    "\"about\": \"2-5 words\", \"open\": true or false}\n"
    "kind: fragment = a few words; tick = a single word or mark; silent = no words (words empty)."
)

# v2: appended AFTER the live system text (so the twin is in the same mind-state as the paragraph that was just written).
# The live system text asks for the paragraph JSON and for acts; the first paragraph below switches that off for this one
# call. The second names the book invitation as an action phrase so it is not mistaken for the thought (F-0043: v1 echoed
# it). It says nothing about what to think; the twin's output never reaches Du (shadow, D-0434).
TWIN_INSTRUCTION = (
    "\n\n---\n"
    "A SECOND, PRIVATE READING OF THIS SAME MOMENT. For this one call, ignore the JSON object described above: do not "
    "write the thought paragraph and do not do anything (no act, no intention, no question). Hold the thought you are "
    "having in the fewest words it needs — a few words, a single word, or none at all if the thought has no words and is "
    "only a sense of something. Never a sentence for its own sake. If there are no words, say so.\n"
    "If a line in what you were given offers you a phrase to say in order to DO something (to read, to open, to go), "
    "that phrase is a way of acting, not a thought. Do not copy it. What you hold is what you notice or feel about "
    "what is there.\n\n"
    "Output ONLY JSON: {\"kind\": \"fragment\" or \"tick\" or \"silent\", \"words\": \"...\", "
    "\"about\": \"2-5 words\", \"open\": true or false}\n"
    "kind: fragment = a few words; tick = a single word or mark; silent = no words (words empty)."
)

# v2, user side: the live user prompt ends "What moves in you now? One quiet thought." — on its own that last line drags a
# 6k-char live system text back to the paragraph JSON (replay 2026-11-06: 26 of 60 replies answered the live schema when the
# twin instruction lived in the system text alone; 0 of 40 once this line replaced the live one). Everything before it, the
# seed parts and any divergent-memory line after it, is byte-identical to what the live thought was given.
_LIVE_TAIL = "What moves in you now? One quiet thought."
TWIN_ASK = (
    "What moves in you now? Hold it in the fewest words it needs: a few words, one word, or none. "
    "Answer with the small JSON {\"kind\": \"fragment\" or \"tick\" or \"silent\", \"words\": \"...\", "
    "\"about\": \"2-5 words\", \"open\": true or false} and NOT the paragraph JSON."
)

_KINDS = ("fragment", "tick", "silent")

# per-process memory of the previous twin/paragraph `about` vectors (for the transition-rate metric).
_prev = {"twin": None, "paragraph": None}


_INVITE_RE = re.compile(r"(?:exactly|thought|say|says)\s*:\s*([A-Z][A-Z' ]{3,40})")
_restart_marked = False   # per-process: the v2 restart marker is written once, at the first sampled twin tick


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", (s or "").lower()).split())


def invite_echo(words: str, seed: str) -> bool:
    """True if the twin's words ARE the action invitation the seed carries ("make your thought exactly: OPEN THE BOOK"):
    the phrase itself, a continuation of it, or its first word ("open"). Pure, deterministic, never raises. Also reads the
    default phrase when the stored seed tail cut the invitation off. Undercounts paraphrase ("the book waits") on purpose:
    this is the D-0633 defeater's definition, not a semantic judgement."""
    try:
        w = _norm(words)
        if not w:
            return False
        phrases = {_norm(m) for m in _INVITE_RE.findall(seed or "")}
        phrases.add("open the book")
        for p in phrases:
            if p and (w == p or w.startswith(p + " ") or w == p.split()[0]):
                return True
    except Exception:
        pass
    return False


def _rng() -> float:
    return random.random()


def _words_n(s: str) -> int:
    return len(re.findall(r"\S+", s or ""))


def _valence(s: str) -> float:
    try:
        from core.narrative_quality import _seg_valence
        return round(float(_seg_valence(s or "")), 3)
    except Exception:
        return 0.0


def _grounded_tag(about: str, source) -> bool | None:
    try:
        from core.stream_drive import _is_grounded
        return bool(_is_grounded(about, source))
    except Exception:
        return None


def _embed(s: str):
    try:
        from core.memory.store import _embed as _e   # the same embedder stream_drive's redundancy reads
        return _e(s) if s and s.strip() else None
    except Exception:
        return None


def _cos(a, b):
    if a is None or b is None:
        return None
    try:
        import numpy as _np
        return round(float(_np.dot(a, b)), 4)
    except Exception:
        return None


def normalize(data: dict) -> dict:
    """Coerce a twin response into {kind, words, about, open}. Pure; never raises."""
    if not isinstance(data, dict):
        data = {}
    words = str(data.get("words", "") or "").strip()
    kind = str(data.get("kind", "") or "").strip().lower()
    # v2 sees the live system text, which asks for the paragraph JSON: a reply with neither twin key is a format slip
    # (the model answered the live schema), recorded so the reader can leave it out of the silent share.
    slip = bool(data) and "words" not in data and "kind" not in data
    if kind not in _KINDS:
        kind = "fragment" if words else "silent"
    if kind == "silent":
        words = ""
    out = {"kind": kind, "words": words[:200], "about": str(data.get("about", "") or "").strip()[:80],
           "open": bool(data.get("open", False))}
    if slip:
        out["format_slip"] = True
    return out


def build_row(*, twin: dict, paragraph: str, p_about: str, p_open: bool, source, train_id, step,
              user_prompt: str, latency_ms: int, now: float | None = None) -> dict:
    """The §4.3 row. Pure apart from the embedder and the per-process _prev memory."""
    tv, pv = _embed(twin.get("about", "")), _embed(p_about)
    bt, bp = _embed(twin.get("words", "")), _embed(paragraph)
    row = {
        "ts": round(now if now is not None else time.time(), 1),
        "row_id": uuid.uuid4().hex[:12],
        "twin_v": TWIN_VERSION,                  # D-0633: rows without this (or < 2) are v1 history, not judged by default
        "train_id": train_id, "step": step, "tick_source": source,
        "paragraph": {"words": paragraph[:1200], "words_n": _words_n(paragraph), "about": p_about[:80],
                      "open": bool(p_open), "valence_regex": _valence(paragraph),
                      "grounded_tag": _grounded_tag(p_about, source)},
        "twin": {**twin, "words_n": _words_n(twin.get("words", "")), "valence_regex": _valence(twin.get("words", "")),
                 "grounded_tag": _grounded_tag(twin.get("about", ""), source),
                 "echo_invite": invite_echo(twin.get("words", ""), user_prompt)},
        "about_cos_prev_twin": _cos(tv, _prev["twin"]),
        "about_cos_prev_paragraph": _cos(pv, _prev["paragraph"]),
        "body_cos_paragraph_vs_twin": _cos(bt, bp),
        "latency_ms": int(latency_ms),
        "seed": (user_prompt or "")[-1500:],     # what the judge needs for `grounded`; never read back by Du
        "judge": None,                           # filled offline (scripts/judge_condensed_thought.py)
        "ride": {"stop": "idle_seed", "line": "twin", "dose": "bucket"},
    }
    if tv is not None:
        _prev["twin"] = tv
    if pv is not None:
        _prev["paragraph"] = pv
    return row


def build_prompts(system_prompt: str, user_prompt: str) -> tuple[str, str]:
    """(system, user) for the v2 twin call. Pure. System = the live system text the caller sent + TWIN_INSTRUCTION (or the
    instruction alone when no live text was handed in); user = the live user prompt with its closing question swapped for
    TWIN_ASK (appended if the closing question is not found). Never raises."""
    try:
        sysp = (str(system_prompt).rstrip() + TWIN_INSTRUCTION) if system_prompt else TWIN_INSTRUCTION.split("---" + chr(10), 1)[1]
        head, sep, rest = str(user_prompt).rpartition(_LIVE_TAIL)
        usr = (head + TWIN_ASK + rest) if sep else (str(user_prompt) + chr(10) * 2 + TWIN_ASK)
        return sysp, usr
    except Exception:
        return TWIN_INSTRUCTION, str(user_prompt)


def _mark_restart(system_chars: int) -> None:
    """Write the v2 restart marker once per process, before this process's first twin row (D-0633: the clock restarts)."""
    global _restart_marked
    if _restart_marked:
        return
    _restart_marked = True
    from core import shadow_log
    shadow_log.append(LEDGER, {"ts": round(time.time(), 1), "marker": "twin_restart", "twin_v": TWIN_VERSION,
                               "decision": "D-0633", "job": "J-3245", "system_chars": int(system_chars),
                               "note": "twin v2 starts here; rows without twin_v>=2 are v1 history"})


async def shadow_tick(*, urls, user_prompt: str, paragraph: str, p_about: str, p_open: bool,
                      temperature: float, source=None, train_id=None, step=None, system_prompt: str = "") -> None:
    """Run the twin on this idle tick (if enabled and sampled) and log one row. ALWAYS returns None.
    Fail-open: any error is logged at debug and swallowed — the live thought proceeds unchanged."""
    try:
        if not CONDENSED_TWIN or not paragraph:
            return None
        if _rng() >= TWIN_RATE:
            return None
        from core.model_client import call_node_json
        from core import shadow_log
        # D-0633: the SAME system text the live paragraph was generated under (a string the caller already sent) + the twin
        # instruction, and the live user prompt with its closing question swapped for the twin's (build_prompts). No live
        # system text handed in -> the instruction alone (the marker's system_chars shows which case a process ran in).
        _sys, _usr = build_prompts(system_prompt, str(user_prompt))
        _mark_restart(len(str(system_prompt or "")))
        t0 = time.monotonic()
        try:
            data = await call_node_json(urls, _sys, _usr, max_tokens=TWIN_MAX_TOKENS,
                                        temperature=float(temperature), timeout=TWIN_TIMEOUT_S, retries=0)
        except Exception as exc:   # a failed twin call is itself a §6 cost signal: log it, then stop
            shadow_log.append(LEDGER, {"ts": round(time.time(), 1), "twin_v": TWIN_VERSION, "failed": type(exc).__name__,
                                       "latency_ms": int((time.monotonic() - t0) * 1000)})
            return None
        lat = int((time.monotonic() - t0) * 1000)
        row = build_row(twin=normalize(data), paragraph=str(paragraph), p_about=str(p_about or ""),
                        p_open=bool(p_open), source=source, train_id=train_id, step=step,
                        user_prompt=str(user_prompt), latency_ms=lat)
        shadow_log.append(LEDGER, row)
    except Exception as exc:   # noqa: BLE001 — fail-open is the contract
        logger.debug("[condensed_thought] twin skipped (fail-open): %s", exc)
    return None

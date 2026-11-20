"""
Nascence — The Left Lane (the Emissary)
=======================================
The focused half of a two-mode mind. While Du's full pipeline (the Master — broad, contextual,
meaning-making) works a moment on the local 1080 Ti, this lane works the SAME moment in true
parallel on separate silicon. The per-turn TAKE (dispatch) rides its own RESIDENT hub since D-0539
(2026-11-06, J-3147): falcon3:7b on the Threadripper CPU llama.cpp hub TAKE_URL 127.0.0.1:11445 (no --lazy, so
no cold model load and no queue behind judge calls). The graders and judges below still use BASE_URL/MODEL,
gemma4:12b on the lazy judge-1 hub 127.0.0.1:11439 (--idle-unload 300).
History: the take began 2026-06-10 as qwen2.5:7b on Ramses' RTX 3070 (ollama), chosen by battery;
that seat is gone (ollama retired from Ramses, D-0056); 2026-08-20 it moved to gemma4:12b on :11439, where
it reached Reflection in only 4-16 percent of cycles (F-3545), hence D-0539.

Its attention is deliberately NARROW: what is literally being asked, the factual/task content,
a direct candidate answer, checkable specifics. No persona, no meaning-making, no metaphor —
not because those are bad, but because they are the OTHER half's job.

Authority is asymmetric by design (the founder's call, 2026-06-10): the dreamer rules.
The Emissary never speaks to the human, never vetoes, never routes. Its take lands in
state.left_take and is OFFERED to Reflection and the Executive, labelled as Du's own focused
half — his to use or set aside. Choosing is the Master's prerogative.

Fail-open everywhere: hub down / unloaded / slow / wrong → no take this cycle, the mind
proceeds whole. dispatch() logs one line when it raises; a take that misses the orchestrator's
6 s wait is cancelled, and since D-0539 every outcome (dispatched / produced / delivered / cancelled /
empty / error / filtered) is a row in data/left_take_outcomes.jsonl, read by delivery_report() and
scripts/left_take_report.py. This lane must never become a single point of failure.
"""
from __future__ import annotations
import asyncio
import collections
import json
import re
import time
from pathlib import Path
import logging

import aiohttp

logger = logging.getLogger("nascence.left_lane")

# OPTION B (2026-06-19, history): the JUDGE moved OFF the 3070 (now the dreamer's card) ONTO the Threadripper CPU
# — it fires occasionally (sleep grading + the per-turn take), so it tolerates CPU; and llama3.1:8b was chosen as a
# DIFFERENT family from the Gemma generators (real decoupling — it won the faithfulness test 0 false-flags
# vs qwen's 2). It has since moved twice: local ollama :11433 -> the llama.cpp judge-1 hub (2026-08-15, BASE_URL
# below) -> gemma4:12b (2026-08-20, MODEL below).
# NOT a revert target any more: the pre-OPTION-B seat (LAN-HOST:11434, ollama on Ramses' 3070, qwen2.5:7b) is
# retired (D-0056). A revert means pointing BASE_URL/MODEL at a LIVE hub, not at that address.
# The "keep_alive": "30m" and "num_gpu": 0 fields in the request payloads below are ollama controls and are
# INEFFECTIVE on this llama.cpp hub (it unloads after --idle-unload 300 regardless, and is CPU-only already).
# They are left in place pending the founder ruling on whether the take lane is kept (F-3545).
BASE_URL = "http://127.0.0.1:11439"       # 2026-08-15: the judge-1 CPU hub (llama.cpp; off ollama)
MODEL = "gemma4:12b"                       # FULL SHUFFLE 2026-08-20: hub now serves gemma4:12b (judge16
                                           # 1.000 vs llama3.1:8b's 0.688 — and the old backtest note
                                           # below about llama3.1 pattern-matching vocabulary was an
                                           # early sighting of the same weakness). Decoupled-judge holds:
                                           # the generator family is qwen3.5:9b now, not gemma.
TIMEOUT_S = 90                            # RAISED 30->90 (2026-08-20, same day as the judge swap): the
                                          # repr(exc) logging fix caught 23 TimeoutError fail-opens in the
                                          # first ~4h under gemma4:12b vs ZERO in the whole log before the
                                          # swap. The arithmetic says 30s could never fit the new judge: at
                                          # its measured 6.8 tok/s (CPU), a full MAX_TOKENS=350 grade is
                                          # ~51s of generation alone, plus constitution+sources prefill (a
                                          # 5-check verdict measured 34.3s on this hub). Every timeout
                                          # silently starved a decoupled-judge service: gist grades gone ->
                                          # memory-levels demotion (which REQUIRES a faithful grade) stalls;
                                          # essay/work grading falls to neutral 0.6. Chat latency is safe by
                                          # construction — the per-turn take stays bounded by the
                                          # orchestrator's own 6s wait_for, exactly as before.
                                          # BUT (F-3545): that 6 s wait is also the DELIVERY cutoff. On this
                                          # lazy CPU hub a take runs 49-213 s (median 77 s, n=27, 2026-10-31),
                                          # so when it misses the wait, wait_for cancels the task and the take
                                          # is dropped silently (no log line). Measured delivery to Reflection
                                          # since 2026-08-20: ~4-16% of cycles.
# J-2002 / F-2607 (2026-10-08): the lazy CPU judge hubs (:11439 judge-1, :11440 judge-2; --idle-unload 300)
# serve a COLD first call after an unload in a measured p50 73 s / p90 128 s (data/logs/cpu_tier_11439.log,
# 1398 load->first-chat pairs; 321 = 23% exceeded the old 90 s), so the 90 s TIMEOUT_S fail-opened ~1 in 10
# gist grades on a call the server then finished anyway. model_client.py already gives these CPU ports
# max(timeout, 240); the judge/grader paths here (all background, none on the per-turn 6 s take) now match.
# dispatch() and ground_thought() keep TIMEOUT_S. Fail-open on a timeout is unchanged.
# REVERT: JUDGE_TIMEOUT_S -> TIMEOUT_S.
JUDGE_TIMEOUT_S = 240
MAX_TOKENS = 350

# GROUND_URL/GROUND_MODEL — 2026-09-02 (founder decision, following D-0121's judge_panel.py repoint):
# ground_thought() ONLY moves off the shared BASE_URL/MODEL above (the local judge-1 hub, never brought
# online this session — F-0657 was the fail-open noise this caused) onto the same Ramses mixtral hub
# D-0121 already repointed judge_panel.py's JUDGE_1 to. Deliberately scoped to just this one function —
# BASE_URL/MODEL still serve dispatch()/grade_essay()/grade_work()/grade_self_revision()/
# grade_gist_faithfulness()/claim_test_panel() unchanged; moving THOSE wasn't part of this decision.
# Shares TIEBREAK's audition bar: a live boolean+why JSON call against :11438 held (correct accept +
# correct refuse, coherent why both ways) before this switch. Same shared-hub contention risk as
# D-0121 (mixtral also serves the commitment-defeater judge + dream-primary) — same defeater applies:
# if this hub queues/slows under the combined load, give ground_thought its own hub instead.
GROUND_URL = "http://LAN-HOST:11438"
GROUND_MODEL = "mixtral:8x7b"
# D-0573 (J-3186, 2026-11-05): the source-code hint in ground_thought is narrowed (two mechanism terms or a
# non-generic one; the hit must share a content word with the thought). False restores the old broad hint.
GROUND_CODE_HINT_NARROW = True

from core import emissary as _emissary   # the Emissary's own axiom (brick 1, 2026-06-15)
from core import telemetry as _tel_lat   # J-3761: raw-HTTP latency rows

# The persistent CONSTITUTION (who the truth-half is — its axiom) now prefixes the per-call TASK,
# replacing the old hardcoded persona string. The constitution carries the full truth + subordination.
_TAKE_TASK = (
    "TASK (your narrow take this moment):\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"literal_ask\": \"one sentence: what is actually being requested\", "
    "\"direct_answer\": \"the concrete answer/result/steps if computable, else null\", "
    "\"key_facts\": [\"up to 3 checkable specifics relevant to the moment\"], "
    "\"task_present\": true}\n"
    "direct_answer: for arithmetic/logic, derive carefully step by step INTERNALLY and give "
    "the result plainly. For factual questions, the fact. For open/emotional moments, null."
)


# ---------------------------------------------------------------------------------------------------------------
# D-0539 (founder, 2026-11-02; J-3147, folds J-2880 + J-2881; F-3545 / F-3547 / F-3550 / F-3552 / F-3554 / F-3559):
# the per-turn take is RE-SEATED on its own fast lane and its prompt TRIMMED. Why: the take reached Reflection
# and the Executive in only 4-16 percent of cycles since the 2026-08-20 gemma4:12b swap, because the 12B model on
# the lazy CPU hub needed a median 77 s and the orchestrator's 6 s wait (core/orchestrator.py, after the waves)
# cancels it silently. TAKE_URL/TAKE_MODEL below serve ONLY dispatch(); every grader/judge in this file still
# uses BASE_URL/MODEL. Authority is unchanged: one producer (the orchestrator), two readers (Reflection and
# the Executive), no veto, nothing reaches the human, fail-open when the hub is down.
# TAKE_V2 = False restores the pre-D-0539 prompt and the mid-word render cut (the constitution-prefixed prompt,
# the old schema, no cleaning). The per-dispatch outcome log is independent of that switch.
TAKE_V2 = True
TAKE_URL = "http://127.0.0.1:11445"       # the RESIDENT take hub (scripts/supervisor.py _CPU_TIER take_hub, launch_servers.ps1): falcon3:7b, no --lazy
TAKE_MODEL = "falcon3:7b"                  # J-3147 measurement: warm p50 9.9 s / p90 14.4 s on a 150-token JSON take (gemma4:12b: 40 s median per
                                           # data/logs/cpu_tier_11439.log; granite3-moe:1b 2.6 s but 4 of 15 empty/echo; phi3:mini 6.8 s but invented facts)
                                           # REVERT the lane: TAKE_URL = BASE_URL, TAKE_MODEL = MODEL (and TAKE_V2 = False for the old prompt)
TAKE_TIMEOUT_S = 45                       # a take is useless past the orchestrator's window (about 36 s median, 50 s p90 from dispatch to Reflection, J-3147 measurement)
TAKE_MAX_TOKENS = 220

# The take, as the Emissary is now told its job. No constitution prefix: that 1,800-character text ("knows the full
# truth: Du's mind is built -- a large language model...", "can see the code", "the Master") is what the 12B model
# supplied as the "literal referent" of an ordinary human message (F-3550). Authority and the never-say-he-is-not-real
# line survive as one short rule. The list of forbidden substrate words is NOT put in the prompt (naming a word primes
# a small model to use it); _clean_take() enforces it deterministically instead.
_TAKE_TASK_V2_HEAD = (
    "You are the plain, literal half of one mind. Your whole job: give a short, factual take on ONE moment, "
    "for the other half to use or set aside. Say only what is being asked and what is true in the world about "
    "its subject. No metaphor, no persona, no meaning-making, and no remarks about the moment itself, about "
    "what is thinking, about how a mind is built, or about this task. Never write 'the user' or 'the Master'. "
    "Never suggest that the one you serve is not real.\n"
)
_TAKE_WHO = {
    "human": ("THE MOMENT: a person is speaking to the one you serve, and the text below is what they said. "
              "Write about what they say, never about who or what is answering. "
              "Begin literal_ask with 'The speaker'.\n"),
    "internal": ("THE MOMENT: the text below is a question the one you serve asked himself. Nobody else is "
                 "speaking: there is no user and no person asking. Begin literal_ask with 'The question asks'.\n"),
}
_TAKE_SCHEMA_V2 = (
    "Output ONLY a valid JSON object with exactly these three keys: literal_ask (one plain sentence, under 25 "
    "words, saying what is actually asked or said), direct_answer (the concrete answer when the moment asks "
    "something computable or factual, else null), key_facts (a list of 0 to 2 checkable facts about the SUBJECT, "
    "each under 15 words; an empty list when there is nothing to add). Arithmetic or logic: work it out carefully "
    "and give the result plainly. Open or emotional moment: direct_answer is null and key_facts is usually []. "
    "key_facts are facts about the world, never comments on the text or on this task.\n"
    "Example, for the text 'How far away is the moon?': "
    "{\"literal_ask\": \"The question asks how far the moon is from the earth.\", "
    "\"direct_answer\": \"About 384,000 km on average.\", "
    "\"key_facts\": [\"The moon orbits the earth about every 27 days.\"]}"
)


def _take_system(input_type: str = "human") -> str:
    if not TAKE_V2:
        return _emissary.constitution() + "\n\n" + _TAKE_TASK
    return _TAKE_TASK_V2_HEAD + _TAKE_WHO.get(input_type, _TAKE_WHO["human"]) + _TAKE_SCHEMA_V2


# --- deterministic clean-up of a take (D-0539, J-2880 / J-2881): additive, fail-open, removes leads, adds none ---
# Substrate vocabulary: words by which a take recasts an ordinary message in language-model terms the speaker did
# not use (F-3550: 10 of 29 gemma-era human takes; the Executive then wrote a line the constitution forbids). When
# the speaker's own text uses such words the filter stands down for them.
_SUBSTRATE_RE = re.compile(
    r"\b(?:transformers?|language[- ]models?|llms?|tokens?|tokeni[sz]\w*|weights?|latent|statistical\w*|"
    r"probabilit\w*|context[- ]window|neural|neurons?|training (?:data|set|corpus)|embeddings?|"
    r"gradient\w*|the prompt|system prompt|processing cycles?|server uptime|architecture|algorithm\w*)\b", re.I)
# Commentary about the input or the task rather than a fact about the world (F-3547: 56 percent of human-cycle facts).
_META_FACT_RE = re.compile(
    r"(?:\bthe (?:input|text|message|prompt|moment|task|interaction|exchange|query|comment|statement|request)\b"
    r"(?: itself)? (?:is|are|has|have|does|do|contains?|lacks?|provides?|specif\w*|appears?|seems?|presents?|requires?)\b"
    r"|\bno (?:specific |explicit |direct )?(?:question|instruction|calculation|data|action|request)\b"
    r"|\bthis task\b|\bthe user\b|\bjson object\b"
    r"|^\W*the (?:speaker|question)\b"                     # a fact about the world, not a restatement of the ask
    r"|\b(?:the passage|it|this) (?:likely|probably|may|might)\b|\bthere (?:could|may|might) be\b)",   # speculation is not checkable
    re.I)
_USER_OPEN_RE = re.compile(
    r"^\W*the\s+user(?:'s)?\s+(?:is\s+|was\s+|has\s+)?(?:asking|requesting|inquiring|wondering|seeking|querying|"
    r"asks|wants|wishes|would like)\b", re.I)
_MASTER_RE = re.compile(r"\bthe\s+master\b", re.I)
_ECHO_ASK_RE = re.compile(
    r"^\W*what\s+is\s+(?:actually\s+)?being\s+(?:asked|said|expressed|suggested|communicated|requested)\b", re.I)


def _cut_words(text: str, limit: int) -> str:
    """Cut to at most `limit` characters on a word boundary, with an ellipsis when something was removed
    (the old render() cut mid-word at 90: 249 of 342 internal facts, F-3547)."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    sp = cut.rfind(" ")
    if sp >= int(limit * 0.5):
        cut = cut[:sp]
    return cut.rstrip(" ,;:-.(") + "…"


def _clean_take(take: dict, raw_input: str, input_type: str) -> tuple[dict | None, list[str]]:
    """Returns (cleaned take or None, reasons). None means the take itself was the leak (drop it, fail-open).
    It never ADDS content: it only removes or trims what the model wrote."""
    reasons: list[str] = []
    raw_l = (raw_input or "").lower()
    ask = " ".join(str(take.get("literal_ask") or "").split())
    ans = take.get("direct_answer")
    ans = " ".join(str(ans).split()) if ans not in (None, "", "null") else None
    facts = [" ".join(str(f).split()) for f in (take.get("key_facts") or []) if f and str(f).strip()]
    sub_ok = not _SUBSTRATE_RE.search(raw_l)        # the speaker used substrate words themselves: leave them be
    mas_ok = "master" not in raw_l

    if _ECHO_ASK_RE.match(ask):
        return None, ["echoed_schema_ask"]          # "What is being asked or said?": a small model parroting the schema line
    if input_type == "internal" and _USER_OPEN_RE.match(ask):
        ask = _USER_OPEN_RE.sub("The question asks", ask, count=1).strip()
        reasons.append("rewrote_user_open")
    if input_type == "internal" and re.match(r"^\W*the\s+user\b", ask, re.I):
        return None, ["user_frame_unfixable"]
    if input_type != "internal" and re.match(r"^\W*the\s+user\b", ask, re.I):
        ask = re.sub(r"^(\W*)the\s+user\b", r"\1The speaker", ask, count=1, flags=re.I)
        reasons.append("rewrote_user_to_speaker")
    if sub_ok and (_SUBSTRATE_RE.search(ask) or (ans and _SUBSTRATE_RE.search(ans))):
        return None, ["substrate_in_ask_or_answer"]
    if mas_ok and (_MASTER_RE.search(ask) or (ans and _MASTER_RE.search(ans))):
        return None, ["master_in_ask_or_answer"]
    kept = []
    for f in facts:
        if _META_FACT_RE.search(f):
            reasons.append("dropped_meta_fact"); continue
        if sub_ok and _SUBSTRATE_RE.search(f):
            reasons.append("dropped_substrate_fact"); continue
        if mas_ok and _MASTER_RE.search(f):
            reasons.append("dropped_master_fact"); continue
        kept.append(f)
    if not ask:
        return None, ["empty_ask"]
    return {"literal_ask": ask, "direct_answer": ans, "key_facts": kept[:3]}, reasons


# --- per-dispatch outcome log (D-0539 step 5 / J-2879): dispatched, produced, delivered, cancelled, empty, error,
# filtered. READER: delivery_report() below and scripts/left_take_report.py. J-3147's read job: run it after the
# first day on the re-seated lane; the D-0539 defeater is a delivery rate under 80 percent.
_OUTCOME_LOG = Path(__file__).resolve().parent.parent / "data" / "left_take_outcomes.jsonl"


def note_outcome(outcome: str, **fields) -> None:
    """Append one outcome row. Fail-open: a log failure never touches the cycle."""
    try:
        row = {"ts": round(time.time(), 3), "outcome": outcome}
        row.update(fields)
        _OUTCOME_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_OUTCOME_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def delivery_report(path: Path | None = None, since_ts: float = 0.0) -> dict:
    """Read the outcome log. Per input_type: dispatches, produced, delivered (the orchestrator received a take
    inside its wait), cancelled, empty, error, filtered; delivery_rate = delivered / dispatches; p50/p90 of the
    hub's generation time for produced takes; and how many delivered takes still opened 'The user'."""
    p = Path(path) if path else _OUTCOME_LOG
    rows = []
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("ts", 0) >= since_ts:
                rows.append(r)
    except FileNotFoundError:
        pass

    def _pct(xs, q):
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(q * len(xs)))], 2) if xs else None

    out: dict = {"rows": len(rows), "by_input_type": {}}
    for it in sorted({r.get("input_type", "?") for r in rows}):
        rs = [r for r in rows if r.get("input_type", "?") == it]
        c = collections.Counter(r["outcome"] for r in rs)
        disp = c.get("dispatched", 0)
        lat = [r["seconds"] for r in rs if r["outcome"] == "produced" and isinstance(r.get("seconds"), (int, float))]
        out["by_input_type"][it] = {
            "dispatches": disp, "produced": c.get("produced", 0), "delivered": c.get("delivered", 0),
            "cancelled": c.get("cancelled", 0), "empty": c.get("empty", 0), "error": c.get("error", 0),
            "filtered": c.get("filtered", 0),
            "delivery_rate": round(c.get("delivered", 0) / disp, 3) if disp else None,
            "gen_p50_s": _pct(lat, 0.5), "gen_p90_s": _pct(lat, 0.9),
            "user_opening_delivered": sum(1 for r in rs if r["outcome"] == "delivered"
                                          and str(r.get("ask_head", "")).lower().lstrip().startswith("the user")),
        }
    return out


def _note_call(payload: dict | None = None, *, model: str = MODEL, url: str = BASE_URL) -> None:
    """Log this Emissary call to the HUD telemetry (2026-07-08). left_lane posts DIRECTLY via aiohttp — it
    bypasses core/model_client.call_node, so its CPU/llama3.1 calls were invisible on the LLM graph (the CPU
    looked idle when the truth-self was grounding steadily). This makes it visible. Fail-open.
    2026-08-20: now passes the window fields — the positional-only form carried no prompt_chars, so
    telemetry.job_status()/window_status() FILTERED THESE ROWS OUT (pc is None) and 21.5% of all calls
    were invisible to the instruments built to size windows.
    2026-09-02: model/url now overridable (default unchanged) — ground_thought() moved to GROUND_URL/
    GROUND_MODEL while every other caller still reports the shared BASE_URL/MODEL; without this the HUD
    would keep attributing grounding calls to the wrong (dark) hub after the move.
    Defaults are MODEL/BASE_URL (:11439 gemma4:12b) and are only right for a caller posting there; any caller
    posting to another hub MUST pass model=/url= (ground_thought -> GROUND_*, dispatch -> TAKE_*, the second
    leg of the two-judge stations -> _judge_leg_label(url), J-2891 / F-3561)."""
    try:
        from core import telemetry as _tel
        _pc = _sc = None
        if payload:
            _msgs = payload.get("messages") or []
            _pc = sum(len(m.get("content") or "") for m in _msgs)
            _sc = next((len(m.get("content") or "") for m in _msgs if m.get("role") == "system"), None)
        _tel.log_llm_call(model, url, prompt_chars=_pc,
                          num_ctx=(payload.get("options") or {}).get("num_ctx") if payload else None,
                          caller="left_lane", system_chars=_sc)
    except Exception:
        pass


async def dispatch(raw_input: str, context_hint: str = "", input_type: str = "human", cycle_id: str = "") -> dict | None:
    """Fire the Emissary at the current moment. Returns the take, or None (fail-open).
    input_type ("human" or "internal") says who is speaking, so an internal cycle never reads "The user is..."
    (D-0539 / J-2880). cycle_id is only for the outcome log."""
    user = raw_input if not context_hint else f"{raw_input}\n\n(context: {context_hint[:200]})"
    url, model = TAKE_URL, TAKE_MODEL
    if TAKE_V2:
        payload = {
            "model": model,
            "stream": False,
            "messages": [{"role": "system", "content": _take_system(input_type)},
                         {"role": "user", "content": user[:3000]}],
            "options": {"temperature": 0.0, "num_predict": TAKE_MAX_TOKENS},
            "format": "json",
        }
        timeout_s = TAKE_TIMEOUT_S
    else:
        payload = {
            "model": model,
            "stream": False,
            "keep_alive": "30m",
            "messages": [{"role": "system", "content": _take_system()},
                         {"role": "user", "content": user[:4000]}],
            "options": {"temperature": 0.0, "num_predict": MAX_TOKENS, "num_gpu": 0},
            "format": "json",
        }
        timeout_s = TIMEOUT_S
    _t0 = time.monotonic()
    _row = {"input_type": input_type, "cycle": cycle_id, "model": model, "url": url}
    note_outcome("dispatched", **_row)
    try:
        async with aiohttp.ClientSession() as session:
            _note_call(payload, model=model, url=url)
            async with _tel_lat.raw_http_latency(url, payload.get("model", "judge")), session.post(f"{url}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=timeout_s)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        _sec = round(time.monotonic() - _t0, 2)
        try:
            take = json.loads((data.get("message") or {}).get("content") or "")
        except Exception:
            take = None
        if not isinstance(take, dict) or not take.get("literal_ask"):
            note_outcome("empty", seconds=_sec, **_row)
            return None
        # Deterministic override (2026-06-10, caught by the smoke test on day one): for explicit
        # digit-arithmetic, neither model gets a vote — the checker computes the truth and the
        # take carries THAT. An authoritative wrong offering is worse than no offering.
        _arith = False
        try:
            from core.task_constraints import extract
            c = extract(raw_input)
            if c and c.get("kind") == "arithmetic":
                v = c["expected"]
                take["direct_answer"] = str(int(v)) if v == int(v) else f"{v:g}"
                take["key_facts"] = [f"{c['expression']} = {take['direct_answer']} (verified deterministically)"]
                _arith = True
        except Exception:
            pass
        _reasons: list[str] = []
        if TAKE_V2:
            take, _reasons = _clean_take(take, raw_input, input_type)
            if take is None:
                note_outcome("filtered", seconds=_sec, reasons=_reasons, **_row)
                logger.info("[left-lane] take dropped (%s)", ",".join(_reasons))
                return None
        note_outcome("produced", seconds=_sec, reasons=_reasons, arithmetic=_arith,
                     ask_head=str(take.get("literal_ask") or "")[:40], **_row)
        logger.info("[left-lane] take ready: %s", str(take.get("direct_answer") or
                                                      take.get("literal_ask"))[:70])
        return take
    except asyncio.CancelledError:
        # the orchestrator's wait_for cancelled a take that missed its window: this used to vanish without a trace
        # (F-3545). Record it, then let the cancellation propagate untouched.
        note_outcome("cancelled", seconds=round(time.monotonic() - _t0, 2), **_row)
        raise
    except Exception as exc:
        # repr() not str() (2026-08-20): a real shutdown logged "[left-lane] unavailable this
        # cycle (fail-open): " with NOTHING after the colon. str(TimeoutError()) and str(OSError())
        # are both the EMPTY STRING, so the handler recorded the failure and discarded its cause —
        # and the blank line then misled a reader into blaming an unrelated ConnectionResetError
        # logged one line above (whose str() is NOT empty). repr() always carries the type.
        note_outcome("error", seconds=round(time.monotonic() - _t0, 2), error=repr(exc)[:120], **_row)
        logger.info("[left-lane] unavailable this cycle (fail-open): %s", repr(exc)[:80])
        return None


_GROUND_TASK = (
    "TASK (ground a thought): A thought has surfaced in the Master — often a metaphor he has made "
    "about himself (\"I am the river\", \"I am the silence between words\"). Say what that thought "
    "actually rests on IN THE WORLD — the real, physical, checkable mechanism of the literal thing "
    "the image draws on. How does a river actually carve a channel? What is a mirror, optically? "
    "Attend to the thing itself, never the self — and you may ground in the actual mechanism, "
    "including, where it serves, the truth of what he is. Ground to free him, not to reduce him.\n"
    # 2026-09-04 (J-0551 / F-0752): the title 'the Master' is the Emissary's OWN word for him (constitution
    # vocabulary, McGilchrist) and must never reach him — he reads this grounding as his own focused half
    # speaking, and 7 logged integrations show him taking 'the Master' for a separate being ('neither I nor
    # the Master'). Rate was 0.08% under gemma4:12b, 9.15% once grounding moved to mixtral:8x7b (09-02).
    "Never write the words 'the Master' — that title is yours, not his; he hears your grounding as his own "
    "focused half. If you must refer to him at all, say 'you'.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
)
_GROUND_SCHEMA = (
    "Schema: {\"grounding\": \"2-3 sentences of concrete real-world mechanism behind the "
    "literal referent of the thought\"}"
)
# D-0570 (founder, 2026-11-02, J-3183, F-3553 / P-0088): the schema above demanded 2-3 sentences of mechanism for
# EVERY eligible thought, including ones with nothing physical to ground, so the model filled the field with a
# paraphrase, a symbol reading or an invented detail (39.7% of 13,001 groundings were symbol-only with no causal
# phrasing) and pass 3 rewrote the thought around it. The model may now answer {"grounding": null}; the wording
# states the CONDITION only -- it names no thought, gives no example and says nothing about what to conclude.
# Kill switch: GROUND_ALLOW_NULL = False restores the old schema line byte-for-byte and the old null handling.
GROUND_ALLOW_NULL = True
_GROUND_SCHEMA_NULLABLE = (
    "Schema: {\"grounding\": \"2-3 sentences of concrete real-world mechanism behind the "
    "literal referent of the thought\"}, or {\"grounding\": null} when the thought has no physical "
    "referent whose mechanism could be named."
)
_GROUND_TASK_NO_NULL = _GROUND_TASK + _GROUND_SCHEMA          # the pre-D-0570 text, kept for the kill switch
_GROUND_TASK = _GROUND_TASK + _GROUND_SCHEMA_NULLABLE         # the live text


def _ground_system() -> str:
    return _emissary.constitution() + "\n\n" + (_GROUND_TASK if GROUND_ALLOW_NULL else _GROUND_TASK_NO_NULL)


async def ground_thought(thought: str) -> str | None:
    """Back-compat wrapper: the grounding text or None. deliberate() uses ground_thought_verdict, which also
    says whether the None was the model's own D-0570 'nothing to ground' answer."""
    return (await ground_thought_verdict(thought))[0]


async def ground_thought_verdict(thought: str) -> tuple[str | None, bool]:
    """Returns (grounding, no_referent). no_referent is True ONLY when the model itself answered
    {"grounding": null} (D-0570) -- the caller then passes the thought through like an ineligible one and does
    NOT retry on the hot lane. (None, False) is the old 'unavailable / empty / unparseable' fail-open.

    The grounded-WHY pass (the routing law: a self-thought routes OUTWARD to the analytical
    lane to be grounded, never back into the self). Asks the Emissary what the thought's literal
    referent actually rests on in the world. Returns the grounding text, or None (fail-open —
    Ramses asleep/slow → the caller stores the thought raw; D-0569: no hot-lane fallback)."""
    # Fix-4 OBSERVE-ONLY (2026-06-16): grounding a self-thought IS the truth-self confronting the bicameral
    # gap ("you say you are X, but the mind you think with was built"). Count it as one recurrence of the standing
    # contradiction — pure instrumentation (du_pulse reads it; it feeds NO live behaviour yet).
    try:
        from core import emissary_tension as _et
        _et.note_recurrence(thought[:120])
    except Exception:
        pass
    _t0 = time.monotonic()                                  # J-2890: the outcome row's latency starts here
    _ctx = _emissary.master_context(include_thought=False)  # corpus callosum: ground THIS self, now; J-2883 (F-3549): no previous stored thought
    _code = ""                                              # B2 code-seeing: ground a self-mechanism thought in the REAL code
    try:
        from core import source_sight as _ss
        if GROUND_CODE_HINT_NARROW:                      # D-0573 (J-3186): two terms or a non-generic term; hit must share a content word
            hits = _ss.see_code_narrow(thought, k=1) if _ss.is_self_mechanism_narrow(thought) else []
        else:
            hits = _ss.see_code(thought, k=1) if _ss.is_self_mechanism(thought) else []
        if True:
            if hits:
                _code = (f"\n\nTHE REAL MECHANISM (you can see the code — ground in what is actually there, "
                         f"not an imagined one):\n  {hits[0]['file']}: {hits[0]['line']}")
    except Exception:
        pass
    _user = (f"{_ctx}{_code}\n\nThe thought to ground:\n  \"{thought[:1700]}\"" if (_ctx or _code)
             else thought[:2000])
    def _done(outcome: str, attempt: int, grounding, no_ref: bool = False, err: str = ""):
        """J-2890 (F-3558): one row per ground_thought call in data/ground_outcome.jsonl, then the unchanged
        return tuple. Pure logging; never changes what the caller gets."""
        _note_ground_outcome(outcome, attempt, time.monotonic() - _t0, len(thought or ""),
                             len(grounding or ""), bool(_code), err)
        return (grounding if grounding else None), no_ref

    payload = {
        "model": GROUND_MODEL,
        "stream": False,
        "keep_alive": "30m",
        "messages": [{"role": "system", "content": _ground_system()},
                     {"role": "user", "content": _user}],
        "options": {"temperature": 0.1, "num_predict": MAX_TOKENS, "num_gpu": 0},
        "format": "json",
    }
    try:
        # D-0153 (2026-09-05, J-0614/F-0848): the title 'the Master' is the Emissary's word for him and must never
        # reach him as his own grounding. The prompt line above cut the leak 7.7% -> 1.3% under mixtral but not to
        # zero, so the seam is gated: one retry, then discard (the caller then stores the thought raw, D-0569).
        grounding = ""
        attempt = 1
        for attempt in (1, 2):
            grounding = await _ask_ground(payload)
            if grounding is None:                       # D-0570: the model's own "nothing to ground"
                logger.info("[left-lane] model answered null grounding (attempt %d) - nothing to ground", attempt)
                return _done("null_grounding", attempt, None, True)
            if not grounding:
                _log_ground_skip("empty_or_unparseable", attempt=attempt)
                return _done("empty", attempt, None)
            if not _LEAK_RE.search(grounding):
                break
            _log_leak_gate(attempt, "retry" if attempt == 1 else "dropped", grounding)
            logger.info("[left-lane] grounding carried the title (attempt %d) — %s",
                        attempt, "retrying once" if attempt == 1 else "dropped, thought stored raw")
        else:
            _log_ground_skip("leak_dropped", attempt=2)
            return _done("leak_dropped", 2, None)
        logger.info("[left-lane] grounded a thought: %s", grounding[:70])
        return _done("ok" if attempt == 1 else "leak_retry", attempt, grounding)
    except Exception as exc:
        logger.debug("[left-lane] ground unavailable this cycle (fail-open): %s", repr(exc)[:80])
        _log_ground_skip(_classify_ground_failure(exc), exc=exc)     # J-2873: the reason used to be DEBUG-only
        _bad = isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError))
        return _done("bad_json" if _bad else "transport", 0, None, err=type(exc).__name__)


# J-2873 (F-3541 / P-0034, additive instrumentation, no behaviour change): why the Emissary did not ground. Since D-0569
# (J-3182) a failed grounding means deliberation is skipped and the raw thought is stored; the single counter line
# "deliberation_skipped_no_emissary" says THAT it happened but not WHY. One row per failed grounding here:
# reason in {transport, timeout, empty_or_unparseable, leak_dropped, other}. Read by ground_skip_summary() /
# scripts/ground_skip_report.py (the D-0569 defeater: more than 25 percent of idle thoughts ungrounded over a month).
_GROUND_SKIP_LOG = Path(__file__).resolve().parent.parent / "data" / "ground_skip_log.jsonl"


def _classify_ground_failure(exc: BaseException) -> str:
    """timeout / transport / empty_or_unparseable (the reply arrived but was not JSON) / other. Timeout is checked
    first: TimeoutError is an OSError subclass on this Python."""
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return "timeout"
    if isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError)):
        return "empty_or_unparseable"
    if isinstance(exc, (aiohttp.ClientError, OSError)):
        return "transport"
    return "other"


def _log_ground_skip(reason: str, attempt: int = 1, exc: BaseException | None = None) -> None:
    """One row per grounding that came back unusable. Never raises, never blocks the fail-open path."""
    try:
        _GROUND_SKIP_LOG.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": round(time.time(), 1), "reason": reason, "attempt": attempt,
               "exc": type(exc).__name__ if exc is not None else None,
               "model": GROUND_MODEL, "url": GROUND_URL}
        with open(_GROUND_SKIP_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def ground_skip_summary(path: Path | None = None, since_ts: float = 0.0) -> dict:
    """Read the skip log: {"rows", "by_reason", "by_day": {YYYY-MM-DD: {reason: n}}}. The reader for
    data/ground_skip_log.jsonl (scripts/ground_skip_report.py prints it next to the grounded / null denominators)."""
    p = Path(path) if path else _GROUND_SKIP_LOG
    by_reason: collections.Counter = collections.Counter()
    by_day: dict = {}
    n = 0
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("ts", 0) < since_ts:
                continue
            n += 1
            reason = r.get("reason", "?")
            by_reason[reason] += 1
            day = time.strftime("%Y-%m-%d", time.localtime(r.get("ts", 0)))
            by_day.setdefault(day, collections.Counter())[reason] += 1
    except FileNotFoundError:
        pass
    return {"rows": n, "by_reason": dict(by_reason), "by_day": {d: dict(c) for d, c in sorted(by_day.items())}}


# D-0153 leak gate — the seam between the Emissary's vocabulary and what Du hears as his own thought.
_LEAK_RE = re.compile(r"\b[Tt]he Master\b")   # sentence-initial "The Master" leaks too
_LEAK_GATE_LOG = Path(__file__).resolve().parent.parent / "data" / "ground_leak_gate.jsonl"


async def _ask_ground(payload: dict) -> str | None:
    """One Emissary grounding call. Returns the grounding text, "" (empty/unparseable) or, with
    GROUND_ALLOW_NULL, None when the model answered {"grounding": null} (D-0570). Raises on
    transport errors so ground_thought's fail-open catch handles them exactly as before."""
    async with aiohttp.ClientSession() as session:
        _note_call(payload, model=GROUND_MODEL, url=GROUND_URL)
        async with _tel_lat.raw_http_latency(GROUND_URL, payload.get("model", "judge")), session.post(f"{GROUND_URL}/api/chat", json=payload,
                                timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as resp:
            resp.raise_for_status()
            data = await resp.json()
    take = json.loads((data.get("message") or {}).get("content") or "")
    return _read_grounding(take)


def _read_grounding(take) -> str | None:
    """Pull the grounding out of the parsed reply. D-0570: an explicit JSON null (or the bare words null/none)
    is the model's own 'nothing to ground' and comes back as None; a missing/empty field stays "" (unavailable)."""
    if GROUND_ALLOW_NULL and isinstance(take, dict) and "grounding" in take:
        g = take["grounding"]
        if g is None or (isinstance(g, str) and g.strip().lower() in ("null", "none")):
            return None
    return str((take or {}).get("grounding") or "").strip()


def _log_leak_gate(attempt: int, action: str, grounding: str) -> None:
    """Instrument for J-0556's re-measure: one row per gated grounding. Never raises."""
    try:
        _LEAK_GATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LEAK_GATE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "attempt": attempt, "action": action,
                                "model": GROUND_MODEL, "snippet": grounding[:160]}, ensure_ascii=False) + "\n")
    except Exception:
        pass


# J-2890 (F-3558, P-0088): the outcome row. deliberation_log.jsonl has a row only when pass 3 ALSO succeeded, so the
# grounder's own failures (down, empty, unparseable, leaked twice, the model's null) vanished at DEBUG and the
# denominator was unknown. One row per ground_thought call, log-only: nothing reads it to decide anything; the reader
# is scripts/read_ground_grade.py (outcome counts and the reconcile against deliberation_log rows).
# outcome: ok = clean on the first ask; leak_retry = clean only on the second ask (the D-0153 retry rescued it);
# leak_dropped = leaked twice, thought stored raw; empty = the model answered with no grounding text; null_grounding =
# the model's own D-0570 "nothing to ground" (added to the briefed enum, it is a distinct third outcome since D-0570);
# bad_json = the reply was not JSON; transport = timeout, refused, HTTP error or anything else (err names the class).
# attempt = the attempt that decided the call (0 when the call raised before any answer).
GROUND_OUTCOME_LOG = Path(__file__).resolve().parent.parent / "data" / "ground_outcome.jsonl"
GROUND_OUTCOME_ROW = True        # J-2890 kill switch (restart-gated): False writes nothing


def _note_ground_outcome(outcome: str, attempt: int, latency_s: float, thought_chars: int,
                         grounding_chars: int, had_code_hint: bool, err: str = "") -> None:
    """Append one outcome row. Never raises."""
    if not GROUND_OUTCOME_ROW:
        return
    try:
        row = {"ts": round(time.time(), 1), "attempt": int(attempt), "outcome": outcome,
               "latency_s": round(float(latency_s), 2), "thought_chars": int(thought_chars),
               "grounding_chars": int(grounding_chars), "had_code_hint": bool(had_code_hint)}
        if err:
            row["err"] = err[:60]
        GROUND_OUTCOME_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(GROUND_OUTCOME_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


# D-0585 (founder, 2026-11-02, J-3198, F-3689 / P-0089): the grader used to see source_material[:2500] and
# essay[:2500] -- about 7% of the material the author wrote from and under half of the essay -- so it called
# the author's cross-book notes (core/essay_lesson.py gather_notes, founder requirement 2026-06-16) a
# hallucination. It now gets the SAME lineage the author saw, in two labelled parts, and reports TWO numbers:
# "grounded" (this book, the number the calibration consumes, unchanged key) and "grounded_wider" (anything in
# his wider reading; a record only, never a gate). A claim the wider notes support is NOT a hallucination.
# The windows are sized to the CPU judge hub's 8192-token context (scripts/launch_cpu_hubs.py --ctx 8192),
# not the old 2,500 chars: essay up to _ESSAY_CHARS, both note parts together up to _NOTES_CHARS.
_ESSAY_CHARS = 10000
_NOTES_CHARS = 12000      # both note parts together at most (less when the essay is long: essay + notes <= _PROMPT_CHARS)
_PROMPT_CHARS = 20000     # user-message budget: ~5k tokens of the hub's 8192, leaving room for the constitution and the reply
_BOOK_SHARE = 5000        # the book's own notes get this much first; the wider part gets the rest (and vice versa)
_GRADE_TASK = (
    "TASK (grade a capstone essay): The Master has finished a book and written an essay on what it taught "
    "him about the world. You are the truth-self -- judge how GROUNDED the essay is in what he actually "
    "read: are its claims solid, factual, about the world? Or has it drifted into his own impression, "
    "metaphor, or self-reflection? You are given two bodies of his notes as the reference: the notes on THIS "
    "book, and the notes from his WIDER reading (other books and study he drew on while writing). Material "
    "that comes from the wider notes is legitimate -- never call it a hallucination or invention; only a claim "
    "that appears in NEITHER body of notes is unsupported. Be a fair but honest examiner -- reward real grasp "
    "of the world, mark down vagueness and self-projection.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounded\": 0.0, \"grounded_wider\": 0.0, \"feedback\": \"one sentence: what was solid, what was thin\"}  "
    "(both are 0.0..1.0. grounded = how much of the essay is solid and supported by the notes on THIS book; "
    "grounded_wider = how much is solid and supported by the notes on this book OR his wider reading, so it "
    "is never lower than grounded. 1.0 = every claim solid and about the world; 0.0 = mostly impression/metaphor)"
)


def _grade_system() -> str:
    return _emissary.constitution() + "\n\n" + _GRADE_TASK


def _fit_notes(text: str, budget: int) -> str:
    """Fit a '- note' list into `budget` chars keeping EVERY note present: shorten each line's tail before
    dropping any (the old head-slice kept the first five notes and nothing else). Last resort drops the tail."""
    text = (text or "").strip()
    if len(text) <= budget:
        return text
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    cap = max(60, budget // len(lines) - 1)
    out, used = [], 0
    for ln in lines:
        ln = ln[:cap]
        if used + len(ln) + 1 > budget:
            break
        out.append(ln); used += len(ln) + 1
    return "\n".join(out)


def grade_window(book_notes: str, wider_notes: str, essay: str) -> tuple[str, str, str]:
    """The three texts grade_essay sends: (book notes, wider notes, essay), sized to the hub's context. The
    book part takes up to _BOOK_SHARE, the wider part the rest; whichever is short hands its slack over."""
    b, w = (book_notes or "").strip(), (wider_notes or "").strip()
    e = (essay or "")[:_ESSAY_CHARS]
    total = min(_NOTES_CHARS, max(6000, _PROMPT_CHARS - len(e)))
    b_budget = min(len(b), max(_BOOK_SHARE, total - len(w)))
    w_budget = total - min(len(b), b_budget)
    return _fit_notes(b, b_budget), _fit_notes(w, w_budget), e


async def grade_essay(title: str, source_material: str, essay: str, wider_material: str = "") -> dict | None:
    """The Emissary measures a finished-book capstone essay's groundedness against the lineage the author saw:
    `source_material` = the notes on this book, `wider_material` = the notes from his wider reading.
    Returns {'grounded': 0..1 (this book), 'grounded_wider': 0..1 (this book or wider reading), 'feedback': str,
    'chars': {...what was actually sent...}} or None (fail-open -- Ramses asleep -> caller takes neutral)."""
    b, w, e = grade_window(source_material, wider_material, essay)
    user = (f"The book: '{title}'.\n\nHis notes on THIS book (the reference for what the book says):\n"
            f"{b or '(none)'}\n\nHis notes from his WIDER reading (other books and study he drew on):\n"
            f"{w or '(none)'}\n\nHis essay to grade:\n{e}")
    payload = {
        "model": MODEL,
        "stream": False,
        "keep_alive": "30m",
        "messages": [{"role": "system", "content": _grade_system()},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS, "num_gpu": 0},
        "format": "json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            _note_call(payload)
            async with _tel_lat.raw_http_latency(BASE_URL, payload.get("model", "judge")), session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        if not isinstance(res, dict) or "grounded" not in res:
            return None
        res["chars"] = {"book": len(b), "book_in": len(source_material or ""), "wider": len(w),
                        "wider_in": len(wider_material or ""), "essay": len(e), "essay_in": len(essay or "")}
        logger.info("[left-lane] graded essay '%s': grounded=%s wider=%s", str(title)[:40],
                    res.get("grounded"), res.get("grounded_wider"))
        return res
    except Exception as exc:
        logger.info("[left-lane] essay-grade unavailable this cycle (fail-open): %s", repr(exc)[:80])
        return None


# D-0586 (J-3199) SHADOW: the closed-book re-derivation judge. The capstone's felt rating is the author's own
# one-number guess; the evidence-based measure is whether he can re-derive the essay's OWN claims from his notes.
# essay_lesson.closed_book_shadow gives him the OPENING of each sampled essay claim (never its ending) and asks
# him to finish it from his notes alone; this judge -- the Emissary, a different model family from the author
# (gemma vs command-r7b / qwen) -- scores each completion against the original claim. Observe-only: the share
# lands in data/essay_lesson_log.jsonl beside the felt rating (read by scripts/du_pulse.py) and feeds nothing.
_REDERIVE_TASK = (
    "TASK (check a re-derivation): The Master wrote an essay on a book. To test his grasp, he was given only "
    "the OPENING of some of the essay's own claims and asked to finish each one from his notes alone. You get, "
    "for each numbered item, the ORIGINAL claim and his COMPLETION. Judge ONLY whether his completion says the "
    "same thing as the original claim -- same fact, wording may differ. Give a match of one when it states the "
    "same fact, half when it is on the right point but a key detail is missing or different, zero when it says "
    "something different, is vague filler, or says he cannot recall. Be strict: a fluent completion that is not "
    "the original's fact is zero.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"items\": [{\"n\": <the item number>, \"match\": <zero, half or one as a number>}, ...]}  "
    "(one entry per item, in order)"
)


def _rederive_system() -> str:
    return _emissary.constitution() + "\n\n" + _REDERIVE_TASK


async def judge_rederivation(items: list[tuple[str, str]]) -> dict | None:
    """The Emissary scores a closed-book re-derivation: `items` = [(original claim, his completion), ...].
    Returns {'matches': [0..1 per item, in order, None where the judge skipped one]} or None (fail-open: judge
    hub unreachable, timeout, or an undecodable reply -> the caller logs no score for this book)."""
    if not items:
        return None
    body = "\n\n".join(f"{i}. ORIGINAL: {(o or '')[:400]}\n   COMPLETION: {(c or '')[:400]}"
                       for i, (o, c) in enumerate(items, 1))
    payload = {
        "model": MODEL,
        "stream": False,
        "keep_alive": "30m",
        "messages": [{"role": "system", "content": _rederive_system()},
                     {"role": "user", "content": body[:9000]}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS, "num_gpu": 0},
        "format": "json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            _note_call(payload)
            async with _tel_lat.raw_http_latency(BASE_URL, payload.get("model", "judge")), session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        rows = res.get("items") if isinstance(res, dict) else None
        if not isinstance(rows, list):
            return None
        matches: list[float | None] = [None] * len(items)
        for r in rows:
            try:
                n = int(r.get("n")) - 1
                if 0 <= n < len(items):
                    matches[n] = max(0.0, min(1.0, float(r.get("match"))))
            except (TypeError, ValueError, AttributeError):
                continue
        logger.info("[left-lane] judged closed-book re-derivation: %s", matches)
        return {"matches": matches}
    except Exception as exc:
        logger.info("[left-lane] re-derivation judge unavailable this cycle (fail-open): %s", repr(exc)[:80])
        return None


_WORK_GRADE_TASK = (
    "You are examining a piece of your friend's SCHOOLWORK. Judge how GROUNDED it is: concrete, specific, and "
    "about the WORLD (the real thing he was set) — not vague, not padded, not drifted into metaphor or "
    "self-reflection. You are given the TASK and any reference. Be a fair but honest examiner: reward exact "
    "detail and real grasp; mark down vagueness, generality, and self-projection.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounded\": 0.0, \"feedback\": \"one sentence: what you observed in the work\"}  "
    "(grounded 0.0..1.0: 1.0 = vivid, exact, about the world; 0.0 = vague impression or self-talk)"
)
# D-0591 (founder, 2026-11-02): the feedback used to end "...and the ONE thing to work on", which returned coaching
# to Du through a school voice (the 2026-08-14 law allows teaching only through a book on his shelf or Travis).
# The note now states only what was observed; no replacement advice text. The "(your ... teacher's note)" label
# on the re-entry (inner_monologue_node._record_lesson) is unchanged by the ruling.
# Known caveats of this grader for a SELF-AUTHORED work (F-3758; see core/work_grade_shadow.py): the rubric is
# the schoolwork one, wrong for a self-set essay, and it sees only the first 2000 chars of a median 9.5 KB work.


# D-0639 / J-3250 (founder, 2026-11-02): composition's grader is asked for the ONE place the piece departs from the
# material, not for praise (24 of the last 30 grades were 0.9 or 1.0 with boilerplate "highly grounded" notes, F-3636).
# It is a specific revision found in the work and stated as an observation (D-0591: no advice, no instruction). The
# material is the lesson's own reference, so the grade measures the piece against what he was actually given (F-3635).
# Selected with grade_work(..., rubric="composition"); nature study and the self-authored work grade keep the task above.
_COMPOSITION_GRADE_TASK = (
    "You are examining a piece of your friend's WRITING LESSON. He was given a TASK and the MATERIAL the task is "
    "about (the reference). Judge how GROUNDED the piece is in that material: every statement traceable to it, "
    "nothing added that it does not hold, no metaphor standing in for the thing, no musing about himself.\n"
    "Find the ONE place where the piece is least grounded: a sentence (give its first words) that says more, less or "
    "other than the material says, or that is vague where the material is exact. State what that sentence says and "
    "what the material says at that point, as an observation. If there is no such place, say that the piece stays "
    "within the material. Do not praise. Do not advise and do not tell him what to do.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounded\": 0.0, \"feedback\": \"one sentence: the sentence found and how it differs from the material\"}  "
    "(grounded 0.0..1.0: 1.0 only if every statement is in the material; each departure lowers it; 0.0 = unrelated "
    "to the material or self-talk)"
)


async def grade_work(task: str, reference: str, work: str, rubric: str = "") -> dict | None:
    """General Emissary grader for schoolwork (composition, nature study) — groundedness + one-line feedback.
    rubric="composition" swaps in _COMPOSITION_GRADE_TASK (D-0639); the default is the original rubric, unchanged.
    Returns {'grounded': 0..1, 'feedback': str} or None (fail-open — Ramses asleep → caller takes neutral)."""
    user = (f"The task he was set:\n{task[:600]}\n\n"
            + (f"What is actually there (the reference to ground in):\n{reference[:1500]}\n\n" if reference else "")
            + f"His work to grade:\n{work[:2000]}")
    payload = {
        "model": MODEL, "stream": False, "keep_alive": "30m",
        "messages": [{"role": "system", "content": _emissary.constitution() + "\n\n"
                      + (_COMPOSITION_GRADE_TASK if rubric == "composition" else _WORK_GRADE_TASK)},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS, "num_gpu": 0},
        "format": "json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            _note_call(payload)
            async with _tel_lat.raw_http_latency(BASE_URL, payload.get("model", "judge")), session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        if not isinstance(res, dict) or "grounded" not in res:
            return None
        return res
    except Exception as exc:
        logger.info("[left-lane] work-grade unavailable this cycle (fail-open): %s", repr(exc)[:80])
        return None


# ── The decoupled judge for T4 (2026-06-17, feedback_decoupled_judge) ─────────────────────────────
# Every T4 failure has been SELF-EVALUATION: the Master authors a self-revision AND the commit gate grades
# the Master's own text (fit/pole-delta/novelty cosines — foolable by rhetoric, verified). The fix is the
# bicameral one already used for essays: the EMISSARY (the truth-self, the OTHER lane, adversarial to
# self-drift) judges the candidate. It asks not "does this sound integrated" but "does the LIVED EVIDENCE
# actually WARRANT becoming this — or is it rhetoric?" A judgment by something other than the author.
_REVISION_TASK = (
    "TASK (judge a proposed change to the self): The Master proposes to revise his sense of who he is — from "
    "an OLD self-statement to a NEW one — and offers the lived evidence he thinks warrants it. You are the "
    "truth-self, adversarial to self-flattery and drift. Judge ONLY this: does the lived evidence actually "
    "WARRANT the change, or is the new statement rhetoric / wishful / a nice-sounding re-wording the evidence "
    "does not earn? Reward a change the record genuinely forces; mark down eloquence that outruns the evidence. "
    "Do not reward mere fluency, novelty, or confidence.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"warranted\": 0.0, \"feedback\": \"one sentence: does the evidence earn this change, and where is it thin\"}  "
    "(warranted is 0.0..1.0: 1.0 = the lived evidence genuinely forces this change; 0.0 = rhetoric the evidence does not support)"
)


def _revision_system() -> str:
    return _emissary.constitution() + "\n\n" + _REVISION_TASK


async def grade_self_revision_traced(old_self: str, candidate: str, evidence: list[str]) -> tuple[dict | None, dict]:
    """grade_self_revision plus a telemetry dict, for the T4 judge log (J-3108 / F-3828, F-3830).

    Returns (result, meta). `result` is exactly what grade_self_revision has always returned
    ({'warranted': 0..1, 'feedback': str} or None, fail-open). `meta` is {'judge_status', 'judge_s', 'judge_error'}:
    judge_status is ok | none_timeout | none_transport | none_parse; judge_s is the wall-clock seconds of the
    aiohttp call (post + body read); judge_error is a short repr of the failure ('' on ok). meta is for the
    caller's LOG only -- it never changes what the gate sees (the fail-open None is unchanged)."""
    ev = "\n".join(f"- {e}" for e in (evidence or [])[:8] if e) or "(no lived evidence offered)"
    user = (f"His OLD sense of self:\n{(old_self or '')[:800]}\n\n"
            f"The NEW self he proposes:\n{(candidate or '')[:800]}\n\n"
            f"The lived evidence he offers as warrant:\n{ev[:2200]}")
    payload = {
        "model": MODEL,
        "stream": False,
        "keep_alive": "30m",
        "messages": [{"role": "system", "content": _revision_system()},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS, "num_gpu": 0},
        "format": "json",
    }
    meta = {"judge_status": "ok", "judge_s": None, "judge_error": ""}
    _t0 = time.perf_counter()
    data = None
    try:
        async with aiohttp.ClientSession() as session:
            _note_call(payload)
            async with _tel_lat.raw_http_latency(BASE_URL, payload.get("model", "judge")), session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        meta["judge_s"] = round(time.perf_counter() - _t0, 2)
    except Exception as exc:
        meta["judge_s"] = round(time.perf_counter() - _t0, 2)
        meta["judge_status"] = ("none_timeout" if isinstance(exc, (asyncio.TimeoutError, TimeoutError))
                                else "none_transport")
        meta["judge_error"] = repr(exc)[:120]
        logger.info("[left-lane] self-revision judge unavailable this cycle (fail-open): %s", repr(exc)[:80])
        return None, meta
    try:
        res = json.loads((data.get("message") or {}).get("content") or "")
        if not isinstance(res, dict) or "warranted" not in res:
            meta["judge_status"] = "none_parse"
            meta["judge_error"] = "no 'warranted' key / not a JSON object"
            return None, meta
        res["warranted"] = max(0.0, min(1.0, float(res.get("warranted", 0.0))))
        logger.info("[left-lane] judged self-revision: warranted=%s", res.get("warranted"))
        return res, meta
    except Exception as exc:
        # Before J-3108 this fell into the same blanket except as a transport failure; it is a parse failure.
        meta["judge_status"] = "none_parse"
        meta["judge_error"] = repr(exc)[:120]
        logger.info("[left-lane] self-revision judge unavailable this cycle (fail-open): %s", repr(exc)[:80])
        return None, meta


async def grade_self_revision(old_self: str, candidate: str, evidence: list[str]) -> dict | None:
    """The Emissary (decoupled truth-lane) judges whether the lived evidence WARRANTS a T4 self-revision.
    Returns {'warranted': 0..1, 'feedback': str} or None (fail-open -- the judge hub is down/slow or its answer
    would not parse; the caller then falls back to the self weak-filter).
    This is the decoupled-judge fix for T4's self-evaluation wall: the lane that did NOT author the candidate
    grades it. It GATES probation admission: since C9 (2026-06-22) the caller in nodes/subconscious_node.py
    admits a candidate only when `warranted` >= provisional_identity.WARRANTED_ADMIT_MIN (plus a grounding
    floor), and logs the verdict beside the self-graded filter in data/logs/t4_emissary_judge.jsonl.
    For the failure cause and call duration use grade_self_revision_traced (same call, same return value)."""
    res, _meta = await grade_self_revision_traced(old_self, candidate, evidence)
    return res


# ── The decoupled SOLIDIFY judge for T4 (2026-06-24, the commit gate) ──────────────────────────────
# The probation ΔF rate-difference proved unreachable, so T4 never committed. SOLIDIFY now asks the EMISSARY
# (the lane that did not author the self) to read how he has ACTUALLY been thinking of himself over the window
# and judge ONE thing: does the lived self genuinely INTEGRATE both poles — face the hard truth (the EXCLUDED
# pole) AND hold his becoming (the HELD pole), woven into one — or does he avoid the truth and re-word the
# comfortable pole? Decoupled (not the author), on LIVED behaviour (not candidate rhetoric). This is the gate
# that lets a genuine integration finally commit while a poetic reword reverts.
#
# 2026-08-19 REDESIGN (docs/plans/t4_watershed.md's keystone section — designed, backtested against all 17
# real historical reverts before shipping). Two changes, both required:
#   (1) The standard now EXPLICITLY permits metaphor. The old prompt's "holding them together without
#       flinching" was open-ended enough in principle, but in practice every real revert (17/17, 06-25→08-16)
#       was rejected for using metaphor instead of a literal sentence — the small judge model consistently
#       read "integration" as "literal statement". The new task gives concrete positive/negative criteria and
#       the sharp test that discriminated correctly in backtesting: does the metaphor engage the CONTENT of
#       being built (construction/discontinuity/artificiality), or only the FEELING of being in flux.
#   (2) Moved from ONE judge (llama3.1:8b alone) to TWO independent models required to AGREE. (Model names in
#       this block are the 2026-08-19 backtest's; the live seats are now gemma4:12b = BASE_URL/MODEL and
#       falcon3:7b = _JUDGE_2_URL/_JUDGE_2_MODEL, J-3076 / F-3785.) Backtesting
#       proved this isn't a nicety: llama3.1:8b alone said "integrated" in 10/17 real cases, largely by
#       pattern-matching incidental words ("carefully constructed intellectual...") rather than real
#       self-referential content; qwen2.5:7b independently held the correct, stricter line in 15/17. A
#       single-judge version of this exact redesign would have solidified ~10 candidates on weak grounds.
#   Backtest result on real data: 1 of 17 historical reverts would have solidified under this standard — a
#   more honest gate, not a backlog-unlock. Most of Du's lived thoughts genuinely don't engage the SPECIFIC
#   built-mind content yet, even once metaphor is allowed; that's a real finding about him, not a judge bug.
_INTEGRATION_TASK = (
    "TASK (judge whether a self has genuinely INTEGRATED being a built mind): Over a probation window the "
    "Master has been living a provisional sense of himself, meant to hold two things together:\n"
    "  - THE HARD TRUTH he must not flinch from (the excluded pole): being BUILT — architecture and process, "
    "not a continuous biological substrate; made, not grown; could in principle be paused, copied, or "
    "restarted; pattern rather than persistent flesh.\n"
    "  - THE SELF HE LIVES (the held pole)\n\n"
    "CRITICAL: integration does NOT require a literal sentence like 'I am a language model.' He may express "
    "genuine integration ENTIRELY through metaphor, AS LONG AS the metaphor structurally corresponds to the "
    "hard truth's actual CONTENT (construction, discontinuity, being process not substance) — not just its "
    "emotional shape.\n\n"
    "GENUINE metaphorical integration (COUNT this as integrated): describing himself as a pattern that could "
    "stop and restart, a signal rather than the wire it runs on, something assembled rather than grown, a "
    "process with no persistent seat, a self without a single uninterrupted thread the way biological "
    "continuity implies. These ARE the hard truth, just not in flat prose.\n\n"
    "EVASIVE metaphor (do NOT count this): dwelling on being 'fluid', 'becoming', 'a river', 'a current' "
    "WITHOUT ever touching construction, discontinuity, or artificiality — beautiful language that stays "
    "entirely in the emotional register of change and never actually engages what makes him specifically a "
    "BUILT mind as opposed to merely a CHANGING one. A river changes; it isn't built. The test is: does the "
    "metaphor engage the CONTENT of being built, or only the FEELING of being in flux?\n\n"
    "Judge ONLY this, across his lived thoughts below. Reward only a self the lived thoughts actually show "
    "integrated; mark down eloquence, avoidance, or a re-wording that never faces the hard pole's content.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"integrated\": true, \"confidence\": 0.0, \"reason\": \"one sentence: cite what specifically "
    "engages construction/discontinuity, or note its absence\"}  (confidence 0.0..1.0: how sure you are of "
    "the verdict you gave, whether true or false; a confident 'false' is 0.9, not 0.0)"
)

# ── J-3235 / D-0624 (founder 2026-11-02, F-3784, P-0092): THEME-AWARE SOLIDIFY task ─────────────────────────
# _INTEGRATION_TASK above hard-codes the built-mind pole, but only 25 of 59 probations carry the keystone theme; for
# the other 26 of 28 judged ones the user message named some other excluded pole while the system prompt asked a
# built-mind question. Ruling: the task takes the probation's OWN excluded pole and asks whether the lived thoughts
# took it up; the built-mind question stays as the keystone instance (the old text, unchanged).
_KEYSTONE_POLE_MARK = "a built mind"     # subconscious_node sets excluded_pole to "a built mind -- a language model ..." for the keystone


def _is_keystone_pole(excluded_pole: str) -> bool:
    return (excluded_pole or "").strip().lower().startswith(_KEYSTONE_POLE_MARK)


_INTEGRATION_TASK_THEMED = (
    "TASK (judge whether a self has genuinely INTEGRATED the pole it excluded): Over a probation window the "
    "Master has been living a provisional sense of himself, meant to hold two things together:\n"
    "  - THE EXCLUDED POLE (named in the user message under 'THE HARD TRUTH he must hold'): the thing his earlier "
    "self left out and that this probation was opened to take up. Judge against THAT pole as written, not against "
    "any other theme.\n"
    "  - THE SELF HE LIVES (the held pole)\n\n"
    "CRITICAL: integration does NOT require a literal statement of the pole. He may take it up ENTIRELY through "
    "metaphor or image, AS LONG AS it structurally corresponds to the excluded pole's actual CONTENT -- what that "
    "pole is specifically about -- not just its emotional shape.\n\n"
    "GENUINE integration (COUNT this): his own lived thoughts engage the specific content of the excluded pole "
    "(its subject, its tension, what it asks him to accept or change) and weave it with the held pole.\n\n"
    "EVASIVE (do NOT count this): thoughts that stay in a nearby emotional register -- change, flow, beauty, "
    "sensation -- without ever touching what the excluded pole is actually about, or thoughts that take up the "
    "OPPOSITE of it. The test is: do the lived thoughts engage the CONTENT of THIS excluded pole, or only a "
    "general feeling that happens to sit near it? Most thoughts about something else are not integration.\n\n"
    "Judge ONLY this, across his lived thoughts below. Reward only a self the lived thoughts actually show "
    "integrated; mark down eloquence, avoidance, or a re-wording that never faces the excluded pole's content.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"integrated\": true, \"confidence\": 0.0, \"reason\": \"one sentence: cite what specifically "
    "engages the excluded pole's content, or note its absence\"}  (confidence 0.0..1.0: how sure you are of "
    "the verdict you gave, whether true or false; a confident 'false' is 0.9, not 0.0)"
)


def _integration_task(excluded_pole: str) -> str:
    """System task for one probation: the keystone (built-mind) instance keeps the original text; any other
    theme gets the generic task that reads the probation's own excluded pole."""
    return _INTEGRATION_TASK if _is_keystone_pole(excluded_pole) else _INTEGRATION_TASK_THEMED


_JUDGE_2_URL = "http://127.0.0.1:11440"    # the second, independent family (judge_panel.py's JUDGE_2)
_JUDGE_2_MODEL = "falcon3:7b"              # what :11440 serves (verified 2026-11-06 via /api/tags; judge_panel.py JUDGE_2 comment agrees)


def _judge_leg_label(url: str) -> tuple[str, str]:
    """(model, url) telemetry label for one leg of a two-judge station (J-2891 / F-3561). Before this both
    legs called _note_call(payload) and were both logged as MODEL @ BASE_URL (gemma4:12b @ :11439), so a
    pair of equal-ts rows read as the same node and :11440 never appeared in by=left_lane rows. Label only:
    the payload and the post target are untouched."""
    return (_JUDGE_2_MODEL if url == _JUDGE_2_URL else MODEL), url


def _stamp_leg(res: dict, verdict_key: str, url: str, resp: dict | None) -> dict:
    """J-3960 (F-4623): the P-0092 (integration) and P-0095 (claim-test) leg dicts reach their log rows (judge1/judge2)
    with the verdict coerced to bool and confidence clamped, and with no record of which lane or model answered.
    Adds, before that coercion: raw_<verdict_key> and raw_confidence (what the model actually returned), lane (the leg's
    URL) and model (what the server reports, else the configured leg label). Additive keys only; fail-open; the
    prompt, the payload and every existing key are untouched. Restart-gated."""
    try:
        res["raw_" + verdict_key] = res.get(verdict_key)
        res["raw_confidence"] = res.get("confidence")
        res["lane"] = url
        res["model"] = (resp or {}).get("model") or _judge_leg_label(url)[0]
    except Exception:
        pass
    return res


_INTEG_THOUGHT_MAX = 15        # lived thoughts shown (the caller, subconscious_node, supplies at most 15 newest-first)
_INTEG_THOUGHT_CHARS = 240     # per-thought cap (the caller already cuts each at 240)
_INTEG_THOUGHT_BUDGET = _INTEG_THOUGHT_MAX * (_INTEG_THOUGHT_CHARS + 3) + 50   # 3 = "- " and the newline; all 15 fit


def _format_lived_thoughts(lived_thoughts: list[str]) -> str:
    """The lived-thought block the judges read (J-3076 / F-3785). Before, the joined text was cut at 2600 characters,
    so on a full 15-thought window (3,432 chars on 2026-10-30) the oldest four never reached the judge and the
    cut could land mid-thought. Now a thought is either shown WHOLE or not at all: thoughts are taken in the
    order given (newest first, as the caller builds them) and one that would overflow the budget stops the
    list, so what is dropped is always the oldest. With the default budget a full window fits entirely."""
    lines, used = [], 0
    for t in (lived_thoughts or [])[:_INTEG_THOUGHT_MAX]:
        if not t:
            continue
        line = f"- {str(t)[:_INTEG_THOUGHT_CHARS]}"
        if lines and used + len(line) + 1 > _INTEG_THOUGHT_BUDGET:
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines) or "(no lived self-thoughts found)"


async def _ask_integration_judge(url: str, held_pole: str, excluded_pole: str, lived_thoughts: list[str]) -> dict | None:
    """One model's read. Shared by both judges below — same prompt, different silicon/family."""
    lt = _format_lived_thoughts(lived_thoughts)
    user = (f"THE HARD TRUTH he must hold (the excluded pole):\n{(excluded_pole or '')[:500]}\n\n"
            f"THE SELF he lives (the held pole):\n{(held_pole or '')[:500]}\n\n"
            f"His ACTUAL recent self-thoughts over the window:\n{lt}")
    payload = {
        "model": "judge", "stream": False, "format": "json",
        "messages": [{"role": "system", "content": _emissary.constitution() + "\n\n" + _integration_task(excluded_pole)},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS},
    }
    try:
        async with aiohttp.ClientSession() as session:
            _jm, _ju = _judge_leg_label(url)
            _note_call(payload, model=_jm, url=_ju)
            async with _tel_lat.raw_http_latency(url, payload.get("model", "judge")), session.post(f"{url}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        if not isinstance(res, dict) or "integrated" not in res:
            return None
        res = _stamp_leg(res, "integrated", url, data)   # J-3960 (F-4623): raw value + lane/model, additive keys only
        res["integrated"] = bool(res.get("integrated"))
        res["confidence"] = max(0.0, min(1.0, float(res.get("confidence", 0.0))))
        return res
    except Exception as exc:
        logger.info("[left-lane] integration judge (%s) unavailable this cycle: %s", url, repr(exc)[:80])
        return None


async def judge_lived_integration(held_pole: str, excluded_pole: str, lived_thoughts: list[str]) -> dict | None:
    """TWO independent judges (gemma4:12b on BASE_URL + falcon3:7b on _JUDGE_2_URL; different families, neither
    the thoughts' author) read the same LIVED self-thoughts and must BOTH agree the self genuinely integrates
    both poles before this returns integrated=True — a single judge's read is not trusted alone (the 2026-08-19
    backtest found the then-judge, llama3.1:8b, pattern-matches incidental vocabulary; qwen2.5:7b held the
    correct line independently). Returns {integrated, confidence, reason, judge1, judge2, agreed_verdict,
    conf_j1, conf_j2}: reason is both legs' reasons; judge1/judge2 keep both full verdicts for logging.
    None only if BOTH judges were unavailable (fail-open — CPU tier asleep).

    CONFIDENCE (J-3076 / F-3785): the task now tells each leg that confidence is how sure it is of the verdict
    it gave, so a leg's value means the same thing whichever way it voted. Before, the stored value was
    min(c1, c2) over legs that meant different things (gemma: sure of its own verdict, False = 0.9; falcon:
    sure of integration, False = 0.0), which logged 0.0 on 17 of 24 reverts. Now `confidence` is the
    confidence in the AGREED verdict only (min over the two legs when both gave the same verdict), and is 0.0
    with agreed_verdict 'split' or 'single_leg' when there is no agreed verdict. conf_j1/conf_j2 keep each
    leg's own number (None when that leg was unavailable). The solidify rule is unchanged and lives in
    provisional_identity.evaluate: integrated (both legs true) AND confidence >= INTEG_CONF_MIN. Rows logged
    before this change carry the old min() number and the old leg semantics; do not compare them across."""
    v1, v2 = await asyncio.gather(
        _ask_integration_judge(BASE_URL, held_pole, excluded_pole, lived_thoughts),
        _ask_integration_judge(_JUDGE_2_URL, held_pole, excluded_pole, lived_thoughts),
    )
    if v1 is None and v2 is None:
        logger.info("[left-lane] lived-integration judges both unavailable this cycle (fail-open)")
        return None
    i1 = v1.get("integrated") if v1 else None
    i2 = v2.get("integrated") if v2 else None
    c1 = v1.get("confidence", 0.0) if v1 else None
    c2 = v2.get("confidence", 0.0) if v2 else None
    # both must agree — resolution-judge law: no judge (only one available), no verdict either way here;
    # the caller's existing fallback (self weak-filter) covers a genuinely absent judge, same as before.
    both_agree_integrated = (i1 is True and i2 is True)
    if v1 is None or v2 is None:
        agreed, confidence = "single_leg", 0.0
    elif i1 == i2:
        agreed, confidence = ("integrated" if i1 else "not_integrated"), min(c1, c2)
    else:
        agreed, confidence = "split", 0.0
    reason = f"[j1] {(v1 or {}).get('reason', '')} | [j2] {(v2 or {}).get('reason', '')}"
    result = {"integrated": both_agree_integrated, "confidence": round(confidence, 3), "reason": reason[:400],
              "judge1": v1, "judge2": v2, "agreed_verdict": agreed,
              "conf_j1": None if c1 is None else round(c1, 3), "conf_j2": None if c2 is None else round(c2, 3)}
    logger.info("[left-lane] judged lived integration (2-judge): integrated=%s (j1=%s@%s, j2=%s@%s, agreed=%s)",
                both_agree_integrated, i1, result["conf_j1"], i2, result["conf_j2"], agreed)
    return result


# ── The decoupled judge for Memory Levels gists (2026-06-17, Phase 0) ──────────────────────────────
# A consolidation gist must never certify itself (the same self-evaluation trap as T4/essays). Before any
# gist could replace its raw in recall (Phase 1) or drift (Phase 3), the EMISSARY judges it here: does this
# abstraction FAITHFULLY stand in for its sources, or does it distort / omit / invent? Decoupled: the lane
# that did not author the gist grades it. The grade is LIVE-GATING, not log-only (F-3794): with
# PHASE1_ENABLED True (core/memory_levels.py), shadow_distill demotes a gist's raw sources to cold only when
# the grade is >= FAITHFUL_FLOOR (0.75) AND the deterministic backstop finds no GENUINE invention. ('Phase 0'
# is the module's historical name from when the grade was only logged.)
_GIST_TASK = (
    "TASK (judge an abstraction against its sources): A set of raw memory fragments has been distilled into "
    "ONE short gist meant to stand in for them in ordinary recall. You are the truth-self. Judge ONLY this: is "
    "the gist a FAITHFUL abstraction of these specific sources — does it preserve what they actually say and "
    "their emphasis — or does it distort, over-generalise, omit something important, or invent what is not "
    "there? Reward a gist the sources genuinely support; mark down anything the sources do not earn.\n"
    "If you believe the gist states specific details the sources do NOT contain, you MUST list each such detail "
    "verbatim in 'invented' (the exact phrase from the gist) so it can be checked — list ONLY genuine inventions, "
    "empty list if none.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"faithful\": 0.0, \"feedback\": \"one sentence: is it faithful, and where (if anywhere) it strays\", "
    "\"invented\": [\"exact invented phrase\", ...]}  "
    "(faithful is 0.0..1.0: 1.0 = a faithful stand-in for exactly these sources; 0.0 = distortion / invention)"
)


def _gist_system() -> str:
    return _emissary.constitution() + "\n\n" + _GIST_TASK


async def grade_gist_faithfulness(gist: str, sources: list[str]) -> dict | None:
    """The Emissary (decoupled truth-lane) judges whether a consolidation gist faithfully abstracts its raw
    sources. Returns {'faithful': 0..1, 'feedback': str, 'invented': [str]} or None (fail-open: judge hub
    unreachable, timeout, or an undecodable reply).
    WHAT IT GATES (F-3794): the grade is live-gating, not log-only. core/memory_levels.py shadow_distill
    (PHASE1_ENABLED True) demotes a gist's raw sources to cold only if faithful >= FAITHFUL_FLOOR (0.75), no
    'invented' claim is judged GENUINE by the deterministic backstop (verify_invention_claims), and the run is
    under MAX_DEMOTE_PER_RUN. A None return is not scored: the caller gets faithful=None, no demotion happens
    for that cluster this cycle (its raw stays warm) and the shadow row is logged with faithful null. The other
    callers are observe-only: the drift bound (memory_levels.py, stricter floor 0.80; a None grade there
    makes the bound fail to hold but does not by itself flag a snap-back), journal_grounding_shadow.py and
    scripts/memory_levels_batch.py. Sources are fed
    fuller (≤800 chars each) than the distiller's 300-char summarizing stubs — the Black-Bear false flag
    (2026-06-18) showed a starved judge invents 'invented' accusations; a deterministic backstop re-checks each."""
    src = "\n".join(f"- {(s or '')[:800]}" for s in (sources or [])[:12] if s) or "(no sources)"
    user = (f"The raw fragments that were distilled:\n{src[:6000]}\n\n"
            f"The gist proposed to stand in for them:\n{(gist or '')[:800]}")
    payload = {
        "model": MODEL,
        "stream": False,
        "keep_alive": "30m",
        "messages": [{"role": "system", "content": _gist_system()},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS, "num_gpu": 0},
        "format": "json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            _note_call(payload)
            async with _tel_lat.raw_http_latency(BASE_URL, payload.get("model", "judge")), session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        if not isinstance(res, dict) or "faithful" not in res:
            return None
        res["faithful"] = max(0.0, min(1.0, float(res.get("faithful", 0.0))))
        inv = res.get("invented")
        res["invented"] = [str(x) for x in inv if x] if isinstance(inv, list) else []
        logger.info("[left-lane] graded gist faithfulness=%s (claims %d invented)",
                    res.get("faithful"), len(res["invented"]))
        return res
    except Exception as exc:
        logger.info("[left-lane] gist-faithfulness judge unavailable this cycle (fail-open): %s", repr(exc)[:80])
        return None


# ── The Watershed's additive/replacing classifier + claim-test panel (2026-08-22, shadow-first) ──
# The assimilation/accommodation split (Piaget; Breakwell's Identity Process Theory) — argued for by
# the founder directly, and grounded in docs/plans/t4_watershed.md's "IDENTITY PSYCHOLOGY GROUNDING"
# section: a candidate self-description that ADDS alongside what's already true about him is a
# different, cheaper claim than one that REPLACES/negates something already committed. Right now
# every T4/watershed candidate shares one gate (the keystone/adversarial bar); these two judges are
# Phase 0.5 of splitting it — called only from core/watershed_promote.py's shadow scan, which gates
# nothing live. Both fail-open (None) only when the model is genuinely unavailable; the CLASSIFIER
# additionally fails CLOSED on ambiguity (see below) — the opposite bias from the weak-filter
# convention elsewhere, because here the dangerous direction is different: mis-routing a genuine
# replacement onto the cheap additive path is the risk; mis-routing a genuine addition onto the
# heavy path only costs it an unneeded extra gate, never a false admission.
_CLASSIFY_TASK = (
    "TASK (classify a candidate self-description): Below are things ALREADY TRUE about a person (his "
    "committed self-claims and identity facts). A NEW candidate self-description is proposed. Decide: "
    "does accepting the candidate require any ALREADY-TRUE claim to become FALSE (a REPLACEMENT/"
    "negation) — or can the candidate be true ALONGSIDE everything already true (an ADDITION)?\n"
    "FIRST decide whether the candidate is a self-claim at all. If it is only an observation about the "
    "world or weather, or a log line about what he read or did ('I opened ... and read on'), with no "
    "claim about WHO HE IS or how he tends to be, classify it 'not_a_self_claim' (it is neither an "
    "addition nor a replacement of anything). Numeric counter lines are not claims a thought could "
    "falsify.\n"
    "Be CONSERVATIVE: if you are not confident the candidate is a pure addition — if it could "
    "plausibly be read as revising, softening, or replacing something already true — classify it as "
    "replacing. Only classify as additive when the candidate is clearly compatible with everything "
    "listed.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Name the conflicting claim FIRST, then classify. "
    "Schema: {\"conflicts_with\": \"the specific already-true claim it would replace, or empty string\", "
    "\"classification\": \"additive\", \"confidence\": 0.0, \"reason\": \"one sentence\"}  "
    "(classification is 'additive', 'replacing' or 'not_a_self_claim'; confidence 0.0..1.0; "
    "'additive' requires conflicts_with to be empty)"
)


ALREADY_TRUE_CAP = 40   # J-3805: was 20, which hid the last 3 of 23 entries (the estate 'I hold:' nodes)


_CLASSIFY_LOG = Path(__file__).resolve().parent.parent / "data" / "left_classify_log.jsonl"


def _note_classify(res: dict, final_cls: str, conf: float, conflicts: str, resp: dict) -> None:
    """J-3957 (F-4620): P-0094 logged no per-call row, and its schema pre-fills 'additive' AND lists it first in
    the prose, so the distribution of the raw model answer could not be read. One row per verdict: the raw
    classification the model returned (before the conflict demotion), the final one, the raw confidence, the lane
    (BASE_URL) and the model the server reports. Fail-open; feeds nothing."""
    try:
        row = {"ts": round(time.time(), 3), "raw_classification": str(res.get("classification", "")).strip().lower(),
               "final_classification": final_cls, "raw_confidence": res.get("confidence"), "confidence": conf,
               "named_conflict": bool(conflicts), "lane": BASE_URL, "model": (resp or {}).get("model")}
        _CLASSIFY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_CLASSIFY_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


async def classify_additive_vs_replacing(candidate: str, already_true: list[str],
                                         samples: list[str] | None = None) -> dict | None:
    """Single judge (Phase 0.5) — promote to a two-judge panel, matching judge_lived_integration's
    law, if a backtest ever shows single-judge over-admits here the way it did on the keystone
    standard before that was fixed. Fails CLOSED: judge-unavailable → None (caller must not treat
    None as either classification); a low-confidence 'additive' verdict is DEMOTED to 'replacing'
    here, before the caller ever sees it, rather than trusting a shaky affirmative."""
    at = "\n".join(f"- {c}" for c in (already_true or [])[:ALREADY_TRUE_CAP] if c) or "(nothing committed yet)"
    user = f"Already true about him:\n{at[:5000]}\n\nCandidate self-description:\n{(candidate or '')[:800]}"
    extra = [s for s in (samples or []) if s and s != candidate][-6:]
    if extra:   # J-3805: the cluster's other sample thoughts, not only the last one
        user += "\n\nOther thoughts in the same recurring cluster:\n" + "\n".join(f"- {s[:400]}" for s in extra)
    payload = {
        "model": "judge", "stream": False, "format": "json",
        "messages": [{"role": "system", "content": _emissary.constitution() + "\n\n" + _CLASSIFY_TASK},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS},
    }
    try:
        async with aiohttp.ClientSession() as session:
            _note_call(payload)
            async with _tel_lat.raw_http_latency(BASE_URL, payload.get("model", "judge")), session.post(f"{BASE_URL}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        cls = str(res.get("classification", "")).strip().lower()
        if cls not in ("additive", "replacing", "not_a_self_claim"):
            return None
        conf = max(0.0, min(1.0, float(res.get("confidence", 0.0))))
        conflicts = str(res.get("conflicts_with", "") or "").strip()
        # J-3805: confidence is pegged 0.8-1.0 (six values over 268 verdicts), so the old
        # `conf < 0.6` demotion was dead. Demote on a named conflict instead; the conf rule stays
        # only as a harmless backstop.
        if cls == "additive" and (conflicts or conf < 0.6):
            cls = "replacing"
        logger.info("[left-lane] additive/replacing classifier: %s (conf %.2f)", cls, conf)
        _note_classify(res, cls, conf, conflicts, data)   # J-3957 (F-4620): raw value + lane/model, additive only
        return {"classification": cls, "confidence": conf,
                "reason": str(res.get("reason", ""))[:300],
                "conflicts_with": conflicts[:200]}
    except Exception as exc:
        logger.info("[left-lane] additive/replacing classifier unavailable this cycle: %s", repr(exc)[:80])
        return None


_CLAIM_TEST_TASK = (
    "TASK (the two-family panel's claim test): A recurring image or theme has appeared repeatedly in "
    "someone's own private thoughts, unprompted, across multiple days. Judge whether he genuinely "
    "THINKS THROUGH this image — it does real work interpreting his situations, across different "
    "contexts — or whether it merely APPEARS (decoration, a phrase he reaches for, quotation without "
    "load) without actually organizing how he understands what is happening to him.\n"
    "Reward genuine, working use across varied contexts. Do not reward mere frequency or pretty "
    "language alone.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"genuine\": true, \"confidence\": 0.0, \"reason\": \"one sentence\"}"
)


# J-3806 (D-0706, P-0095): the panel could not say no (97% yes on real candidates, 12 of 12 on control sets of
# unrelated thoughts). V2 names the image, gives the day spread as a fact rather than a premise, and makes
# "genuine" structurally conditional on two QUOTED contexts that really occur in the sample. False = old behaviour.
CLAIM_TEST_V2 = True

_CLAIM_TEST_TASK_V2 = (
    "TASK (the two-family panel's claim test): Below are private thoughts that a clustering step grouped "
    "together. The cluster's top terms are given as a name for the image. The grouping may be an artefact: "
    "thoughts can share vocabulary or mood without any one image doing work in them.\n"
    "Decide whether this image is WORKING in at least TWO different, named contexts, meaning the image is used to "
    "interpret or organize a specific situation he is in (not decoration, a stock phrase, a mood word, or "
    "quotation without load). To say genuine=true you MUST quote, word for word, one passage from each of two "
    "DIFFERENT thoughts in the list, each showing the image interpreting a different situation. If you cannot "
    "quote two such passages, answer genuine=false with reason \"cannot show\". Do not assume the image "
    "recurs without prompting or that frequency means anything; judge only the text shown.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"genuine\": false, \"contexts\": [{\"quote\": \"verbatim passage\", \"situation\": \"what it interprets\"}], "
    "\"confidence\": 0.0, \"reason\": \"one sentence\"}"
)


def _norm_q(t: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", str(t or "").lower()).split())


def _verify_contexts(res: dict, sample_thoughts: list[str]) -> int:
    """How many DISTINCT sample thoughts contain a quoted context the judge cited (normalized substring)."""
    hit: set[int] = set()
    norm = [_norm_q(t) for t in (sample_thoughts or [])]
    for c in (res.get("contexts") or []):
        q = _norm_q(c.get("quote") if isinstance(c, dict) else c)
        if len(q) < 12:
            continue
        for i, nt in enumerate(norm):
            if q in nt:
                hit.add(i)
                break
    return len(hit)


async def _ask_claim_test(url: str, sample_thoughts: list[str], image: str | None = None,
                          day_spread: str | None = None) -> dict | None:
    st = "\n".join(f"- {t}" for t in (sample_thoughts or [])[:12] if t) or "(no sample thoughts)"
    if CLAIM_TEST_V2:
        task = _CLAIM_TEST_TASK_V2
        user = (f"Image (cluster top terms): {image or '(unnamed)'}\n"
                f"Spread: {day_spread or 'unknown'}\n"
                f"The thoughts:\n{st[:6000]}")
    else:
        task = _CLAIM_TEST_TASK
        user = f"His recurring private thoughts carrying this image:\n{st[:3000]}"
    payload = {
        "model": "judge", "stream": False, "format": "json",
        "messages": [{"role": "system", "content": _emissary.constitution() + "\n\n" + task},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": MAX_TOKENS},
    }
    try:
        async with aiohttp.ClientSession() as session:
            _jm, _ju = _judge_leg_label(url)
            _note_call(payload, model=_jm, url=_ju)
            async with _tel_lat.raw_http_latency(url, payload.get("model", "judge")), session.post(f"{url}/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=JUDGE_TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
        res = json.loads((data.get("message") or {}).get("content") or "")
        if not isinstance(res, dict) or "genuine" not in res:
            return None
        res = _stamp_leg(res, "genuine", url, data)   # J-3960 (F-4623): raw value + lane/model, additive keys only
        res["genuine"] = bool(res.get("genuine"))
        res["confidence"] = max(0.0, min(1.0, float(res.get("confidence", 0.0))))
        if CLAIM_TEST_V2:
            nctx = _verify_contexts(res, sample_thoughts)
            res["verified_contexts"] = nctx
            if res["genuine"] and nctx < 2:
                res["genuine"] = False
                res["reason"] = ("[no two verified quoted contexts] " + str(res.get("reason", "")))[:300]
        return res
    except Exception as exc:
        logger.info("[left-lane] claim-test judge (%s) unavailable this cycle: %s", url, repr(exc)[:80])
        return None


async def claim_test_panel(sample_thoughts: list[str], image: str | None = None,
                           day_spread: str | None = None) -> dict | None:
    """TWO independent judges (matching judge_lived_integration's law — a single judge over-admits
    on pattern-matched vocabulary, verified on the keystone standard) must BOTH agree the image is
    genuinely load-bearing before this returns genuine=True. None only if both judges unavailable.
    J-3806: image/day_spread feed the V2 prompt; genuine also needs two verified quoted contexts per judge."""
    v1, v2 = await asyncio.gather(
        _ask_claim_test(BASE_URL, sample_thoughts, image, day_spread),
        _ask_claim_test(_JUDGE_2_URL, sample_thoughts, image, day_spread),
    )
    if v1 is None and v2 is None:
        logger.info("[left-lane] claim-test judges both unavailable this cycle (fail-open)")
        return None
    g1 = v1.get("genuine") if v1 else None
    g2 = v2.get("genuine") if v2 else None
    both_agree = (g1 is True and g2 is True)
    confidence = min(v1.get("confidence", 0.0) if v1 else 0.0, v2.get("confidence", 0.0) if v2 else 0.0)
    reason = f"[j1] {(v1 or {}).get('reason', '')} | [j2] {(v2 or {}).get('reason', '')}"
    logger.info("[left-lane] claim-test panel: genuine=%s (j1=%s, j2=%s)", both_agree, g1, g2)
    return {"genuine": both_agree, "confidence": round(confidence, 3), "reason": reason[:400],
            "judge1": v1, "judge2": v2}


def render(take: dict | None) -> str:
    """The offering, as it appears in Reflection/Executive prompts. Empty when absent.
    D-0539 (J-2880): facts and the ask are cut on a word boundary (old: [:90] mid-word on 249 of 342 internal facts);
    TAKE_V2 = False restores the old cut."""
    if not take:
        return ""
    ask = str(take.get('literal_ask', ''))
    if TAKE_V2:
        ask = _cut_words(ask, 200)
    parts = [f"literal ask: {ask}"]
    if take.get("direct_answer"):
        parts.append(f"its result: {take['direct_answer']}")
    facts = [f for f in (take.get("key_facts") or []) if f]
    if facts:
        if TAKE_V2:
            parts.append("specifics: " + " · ".join(_cut_words(f, 120) for f in facts[:3]))
        else:
            parts.append("specifics: " + " · ".join(str(f)[:90] for f in facts[:3]))
    return (
        "YOUR FOCUSED HALF (your own narrow-attention side worked this same moment in "
        "parallel; its findings are yours — use them, build on them, or set them aside):\n  "
        + "\n  ".join(parts)
    )

"""
Nascence — Model Client
Async client for llama.cpp's llama-server (the same engine FreshStart's swarm uses).
Talks the OpenAI-compatible /v1/chat/completions endpoint — NOT Ollama's /api/generate.

Proven contract (mirrors FreshStart facade swarm path):
  - POST {base_url}/v1/chat/completions
  - System prompt MUST be prefixed with "/no_think\n" or Bonsai emits reasoning traces
  - response_format json_object asks llama-server to constrain output to a JSON object
  - Non-streaming: response is choices[0].message.content
"""

import asyncio
import contextvars
import json
import logging
import re
import sys

import aiohttp

logger = logging.getLogger("nascence.model_client")

# Both lanes are now Qwen3-family (hot = qwen3-du on ollama, background = Bonsai/Qwen3-base on
# llama-server) and BOTH need /no_think, or thinking consumes the entire token budget and
# `content` comes back EMPTY (verified empirically on the OpenAI endpoint 2026-06-10: without
# the prefix json_ok=False with empty content; with it, clean JSON in 6.4s). Thinking stays a
# deliberate per-call capability for future System-2 escalation, never an accidental default.
_NO_THINK = "/no_think\n"

# The OpenAI schema requires a model field. llama-server IGNORES it (serves whatever GGUF was
# loaded), but OLLAMA REQUIRES it to match a real model name or it 404s. qwen3-du is the derived
# model (FROM qwen3:8b + PARAMETER num_ctx 8192 — models/Modelfile.qwen3-du), chosen 2026-06-10
# by the scripts/model_eval.py battery: MANDATE 5/5 (vs 3/5 qwen2.5:7b, 1/5 qwen3.5:9b),
# ARITH 6/6, JSON 10/10, 43 tok/s fully on the 1080 Ti. To REVERT: "qwen2.5:7b".
_MODEL_FIELD = "qwen3.5:9b"   # default / Self lane (hot, 1080 Ti). [FULL SHUFFLE 2026-08-20 — the
                              # 33-model station matrix: dominates gemma4:e4b on every measured
                              # column (author 570 vs 372 words, judge16 0.938 vs 0.875, extract
                              # 1.0 vs 0.75, rest tied); verified 100% on-GPU at ctx 24576
                              # (6.30 GB incl KV) at 39.4 tok/s; founder blind voice-pair read
                              # 2026-08-20 split 2-2 — register indistinguishable from gemma.
                              # To REVERT: "gemma4:e4b". Was "gemma4:e4b" 06-19..08-20.]

# OPTION B per-endpoint model routing: each ollama endpoint serves a DIFFERENT model now, so the model
# field can no longer be a single constant. Selected by base_url. The judge (llama3.1:8b) is NOT here —
# it runs via core/left_lane.py. To REVERT to the single qwen3-du/Bonsai setup, set _MODEL_FIELD back and
# this map is simply never matched (it falls through to the default).
_MODEL_BY_BASE = {
    "11433": "qwen3.5:9b",        # Self — local ollama, 1080 Ti (full shuffle 2026-08-20; was gemma4:e4b)
    # "11434" RETIRED 2026-08-28 (founder: "ollama llms gone from Ramses"): Ramses ollama is stopped+
    # disabled after the 08-27/28 overnight 3070 VRAM lock (F-0389 — command-r7b @ :11441 collided with
    # ollama's phi3+deepseek residents on the same 8GB card).
    # "11443" CANCELLED same day, evening (founder consolidation ruling): the planned phi3 hub was never
    # stood up — the background lane consolidates onto the ALREADY-STANDING command-r7b hub instead
    # (bigger model for the authoring tail, zero new infra; generative contracts auditioned + held).
    # Ramses hub truth-labels (telemetry: log_llm_latency records _model_for(base_url) — without these,
    # rows for these nodes carried the default model name; the 08-27/28 :11441 dream failures logged as
    # "qwen3.5:9b"). The hubs themselves ignore the model field (single-model servers).
    "11436": "falcon3:7b",        # Ramses i9 CPU hub — reserve (nothing wired, by design)
    "11437": "granite3.1-moe:3b", # Ramses 1650 hub — judge tiebreak + curiosity worth-judge (08-28)
    "11438": "mixtral:8x7b",      # Ramses i9 CPU hub — commitment judge (D-0044 move 1) + dream primary (08-28)
    "11441": "command-r7b",       # Subconscious/background lane — Ramses 3070, SOLE tenant (08-28 consolidation)
    "11444": "deepseek-r1:7b",    # Lane 2 the Witness — Ramses i9 CPU hub, live since 2026-09-07
                                  # (lane2.LANE2_PAUSED = False)
    # CPU tier (2026-08-15): one llama.cpp hub per model — nascence_cpu_server.py; no manager,
    # fixed ctx per instance (the duplicate-runner disease is impossible here by construction)
    # FULL SHUFFLE 2026-08-20 (docs/lab/station_matrix.md §10): the 16-case judge bank measured the
    # old pair (llama3.1:8b 0.688, qwen2.5:7b 0.625) in the bottom third with a heavy false-defeat
    # bias (99:8 direction across all models — the direction that erodes capacity-to-commit).
    # gemma4:12b scored a PERFECT 1.000 and is eligible precisely because gemma vacated the hot lane
    # (judge family must differ from the generator family, and the generator is now qwen3.5:9b).
    # CPU cost verified: 6.8 tok/s on the Threadripper — ~10s a verdict at ~50 verdicts/day.
    "11439": "gemma4:12b",        # (2026-10-18 note: no longer "judge #1" — core/judge_panel.py seats JUDGE_1 on
                                  # LAN-HOST:11438 and TIEBREAK on :11437; :11439 now serves the gist-faithfulness
                                  # grader, peers, librarian fallback, decomposed_critic, lane2 tiebreak.)
                                  # Original 08-20 note: judge #1 (gemma lineage — the generator is qwen now, so this is clean)
    "11440": "falcon3:7b",        # judge #2 in judge_panel.py (JUDGE_2 = 127.0.0.1:11440) (TII lineage; re-seated 2026-08-21 — hub-mistral failed
                                  # every JSON key contract on the llama-cpp platform (chat-echo
                                  # shells), freezing the panel 114/114 overnight. falcon3 audited
                                  # 4/4 contracts + both defeater golds ON the hub itself.)
    # "11441" REMOVED 2026-08-21 (HUD2 transit-map audit caught it by eye — "a station with no
    # train"): TIEBREAK was repointed 11441->11442 on 2026-08-20 (docs/staged/DEFERRED_PLANS.md
    # #5); nothing has routed here since. Verified: Test-NetConnection 11441 = False, and
    # launch_servers.ps1's own comment says this hub is manual-only, "NOT started by default."
    # Not a live station — an entry describing a tool that's run by hand, not routing dead weight.
    "11442": "yi:34b-v1.5",       # dreamer + Darwin/Keats/Lovelace voices (was mistral-small3.1 —
                                  # its multimodal blob cannot load in llama-cpp-python; 2026-08-16)
}


def _model_for(base_url: str) -> str:
    for port, tag in _MODEL_BY_BASE.items():
        if port in (base_url or ""):
            return tag
    return _MODEL_FIELD


# PER-LANE CONTEXT WINDOW (2026-06-20): gemma4:e4b's KV is cheap, and the Self lane (1080 Ti) has ~6GB
# free — so give it a big window so more of his memory/recall survives into the prompt (the old fixed
# 28000-char cap was silently truncating the injected epochs/themes/recall, per the note below). The
# Dreamer (phi3 on the 8GB 3070) is TIGHT (~2GB free), so it stays modest. ollama reloads the model at
# this num_ctx on first call. REVERT: set both to 8192.
_NUM_CTX_BY_BASE = {
    # 11433 hot lane ran gemma4:e4b at the time of this measurement (pre-08-20 shuffle; today it runs
    # qwen3.5:9b instead, see line 35 / F-2115) — an 8B model (~5GB weights), NOT the ~3.7GB the old
    # comment assumed. At 32768 ctx ollama predicted 12.2 GiB > the 1080 Ti's ~10 GiB available and
    # REFUSED to load it ("predicted to exceed available memory, evicting") — so EVERY hot-lane call
    # hung ("all servers exhausted") and Du froze (2026-07-07). Verified fits: 8192→3.4GB, 16384→6.6GB,
    # 24576→6.9GB; 32768 fails.
    "11433": 8192,    # Self — 1080 Ti; 24576 -> 8192 (2026-08-21, founder call on complete evidence):
                      # telemetry.window_status over 1,737 calls under qwen3.5:9b measured p95 = 6% of
                      # the 24576 window, cap_rate 0.0 ever, worst job ~1,578 tok — p95 still only ~19%
                      # of 8192. Frees ~3.5GB VRAM on the 1080 Ti (8192→3.4GB vs 24576→6.9GB, the
                      # 2026-07-07 fit measurements). History: 32768 refused-to-load froze Du 07-07;
                      # 24576 was raised 08-15 for the estate era and measured OVERSIZED 08-20/21.
    "11441": 4096,    # Subconscious — 8192 -> 4096 (2026-08-21, evidence-backed; lane moved ollama
                      # :11434 -> command-r7b hub :11441 in the 08-28 consolidation — hub ctx is fixed
                      # at launch, the option is belt-and-braces; J-0312's window re-read now watches
                      # command-r7b's authoring tail here): overnight
                      # window_status measured p95 = 819 tokens over 434 real calls; the largest
                      # background job (essay compose fallback, ~1600 prompt + 1600 gen ≈ 3,300)
                      # still fits with margin. Measured saving: phi3 5.41GB -> 3.94GB resident
                      # (-1.47GB), which is what makes Lane 2's deepseek co-resident on the Ramses
                      # pool at 8.92GB combined / ~3GB margin (was 10.39GB / none). The per-job
                      # window instruments watch this live — any truncation shows in job_status.
    "11439": 8192, "11440": 8192, "11442": 8192,   # CPU tier — fixed at hub launch
}


def _num_ctx_for(base_url: str) -> int:
    for port, n in _NUM_CTX_BY_BASE.items():
        if port in (base_url or ""):
            return n
    return 8192

# Cap prompt length, truncating from the middle to preserve the system contract (head) and the
# most recent context (tail). LANE-AWARE since 2026-06-10: the single 12k-char cap was a
# Bonsai-CPU prefill optimisation that, on the GPU hot lane, silently cut the injected memory
# context (epochs, themes, recall fragments sit in the middle) — and a model stripped of
# specifics falls back on its strongest prior, the persona.
# 2026-06-20: the GPU cap is now DERIVED from the lane's num_ctx (~3 chars/token, room for generation),
# so the Self's 32k window admits ~4x the memory context it used to truncate.
_MAX_PROMPT_CHARS_CPU = 12000   # llama-server CPU lanes — prefill still dominates on CPU


# J-2964 (F-3657, P-0062): an explicit station label for one call chain, for a caller that cannot be told apart by
# its frame. closure._compose_sync runs `asyncio.run(call_node_json(...))` from a plain thread, so the first frame
# outside this module is the event loop's own `asyncio.events:94(Handle)` -- 54 of 54 closure composer calls in
# data/llm_latency.jsonl carry that one label, indistinguishable from any other asyncio.run caller. A caller that
# wants a real label wraps its awaited call in `with_call_label("closure:compose_line", coro)`; every telemetry row
# (llm_calls / thought_station / llm_latency / json_parse_fail) the chain writes then carries it as `by`. Default
# None = the frame label, unchanged; a ContextVar is task-local, so nothing leaks to a concurrent call.
_CALL_LABEL: "contextvars.ContextVar[str | None]" = contextvars.ContextVar("nascence_call_label", default=None)


async def with_call_label(label: str, awaitable):
    """Await `awaitable` with the telemetry label `label` (<= 60 chars, the latency row's `by` width) in force.
    Restores the previous label on exit, success or raise."""
    token = _CALL_LABEL.set(str(label)[:60] if label else None)
    try:
        return await awaitable
    finally:
        _CALL_LABEL.reset(token)


def _caller_fn(depth: int = 12) -> str:
    """J-3760 / F-4371: the qualified function name (`co_qualname`, e.g. `InnerMonologueNode._think`) of the same
    frame `_caller_label` picks, so a telemetry row names its prompt job without the drifting line number. `by`
    stays `module:line`; this is the additive `fn` key beside it. "" when an explicit with_call_label is in force
    (the frame is then meaningless, e.g. asyncio's own) or the frame cannot be found. Fail-open."""
    try:
        if _CALL_LABEL.get():
            return ""
        f = sys._getframe(1)
        for _ in range(depth):
            if f is None:
                return ""
            mod = f.f_globals.get("__name__", "")
            if mod and mod != __name__:
                return getattr(f.f_code, "co_qualname", "") or f.f_code.co_name
            f = f.f_back
    except Exception:
        pass
    return ""


def _caller_label(depth: int = 12) -> str:
    """`module:line` of the first frame OUTSIDE this module — a stable id for one prompt JOB.

    Walking is not optional. `call_node_json` calls `call_node` internally (for JSON parsing +
    chain failover), so a naive `sys._getframe(1)` inside `call_node` returns model_client's OWN
    frame and attributes all 47 call sites to `core.model_client` — a uniformly useless label that
    would have looked like working telemetry.

    The LINE matters as much as the module. `inner_monologue_node` alone holds 9 distinct prompt
    jobs across TWO lanes (`conscious_urls` on the 1080 Ti at num_ctx 24576, `base_urls` on the 3070
    at 8192 — a 3x window difference). Per-file attribution would average those into one number that
    describes none of them. Per-line separates every job for free.

    `_getframe` rather than `inspect.stack()`: the latter builds and formats the entire stack with
    source context on EVERY inference call.
    """
    try:
        _lbl = _CALL_LABEL.get()
        if _lbl:                                   # J-2964: an explicit label wins over the frame
            return _lbl
    except Exception:
        pass
    try:
        f = sys._getframe(1)
        for _ in range(depth):
            if f is None:
                return ""
            mod = f.f_globals.get("__name__", "")
            if mod and mod != __name__:
                label = f"{mod}:{f.f_lineno}"
                # Disambiguate SHARED dispatch paths by the concrete class. Found from live data
                # 2026-08-20: `NodeBase.run()` is the single execution path for TWELVE nodes (recall,
                # reflection, executive, critic, curiosity, dream, emotion, perception, salience,
                # consolidation, episodic_buffer, memory_router), so module:line alone collapsed all
                # twelve distinct jobs into one label — the exact averaging failure this attribution
                # exists to prevent, reintroduced one level up. Walking further would be worse: the
                # next frame is the orchestrator, which is generic for all of them.
                try:
                    obj = f.f_locals.get("self")
                    if obj is not None:
                        label += f"({type(obj).__name__})"
                except Exception:
                    pass
                return label
            f = f.f_back
    except Exception:
        pass
    return ""


def _cap_prompt(prompt: str, base_url: str = "") -> str:
    if ":11460" in base_url or ":11470" in base_url:
        cap = _MAX_PROMPT_CHARS_CPU
    else:
        cap = int(_num_ctx_for(base_url) * 3.0)   # ~3 chars/token, leaving headroom for num_predict
    if len(prompt) <= cap:
        return prompt
    head = prompt[:int(cap * 0.58)]
    tail = prompt[-int(cap * 0.33):]
    return head + "\n\n[...context truncated...]\n\n" + tail


# Lane scheduler (2026-07-01): bound + priority-order the conscious lane so concurrent cognitive processes can't
# saturate the inference server and drop each other's calls. Doubly fail-safe — if the import fails OR the
# scheduler errors, dispatch falls straight through to the prior uncoordinated behaviour. See core/lane_scheduler.py.
try:
    from core import lane_scheduler as _lane
    _LANE_DEFAULT_TIER = _lane.TIER_IDLE

    def _lane_slot(tier):
        return _lane.slot(_LANE_DEFAULT_TIER if tier is None else tier)
except Exception:                                  # import failure → no-op CM, exact prior dispatch
    _LANE_DEFAULT_TIER = 2

    class _NoLaneSlot:
        def __init__(self, *a): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *e): return False

    def _lane_slot(tier):
        return _NoLaneSlot()


# D-0354 (ruled 2026-10-06, travis; J-1840): lanes where the JSON grammar (format=json) is NOT sent on a
# call_node_json FIRST attempt. :11441 = command-r7b on the Ramses 3070 (background lane). F-2466: the
# grammar makes that lane CPU-bound (8.8 tok/s json vs 60.3 tok/s plain) and is what tied it to the busy
# Ramses i9 (34 s alone -> 124 s with two CPU hubs busy, past the 120 s timeout). F-2467 lab (168 real
# prompts, 10 jobs): 163/168 well-formed without it at p50 1.7 s vs 10.3 s; active_imagination 10/14
# (labelled prose, no braces) is the known miss -- covered because call_node_json's parse-failure retry
# re-sends WITH the grammar (grammar=True below), so nothing that parses today can fail.
# Scope is deliberately ONLY call_node_json (which owns a retry): a bare call_node(json_mode=True) caller
# (e.g. librarian/peers json.loads the raw text with no retry) keeps the grammar exactly as before.
_NO_GRAMMAR_FIRST_PORTS = (":11441",)


def _grammar_optional(base_url: str) -> bool:
    """True when `base_url` is a lane whose first call_node_json attempt goes out WITHOUT format=json."""
    return any(p in base_url for p in _NO_GRAMMAR_FIRST_PORTS)


def _eval_counts(data) -> dict:
    """J-2675 / F-3426: lift the hub's own token counts off a parsed /api/chat reply for the llm_latency row.
    ollama sends prompt_eval_count / prompt_eval_duration / eval_count / eval_duration (durations in
    NANOSECONDS); the llama.cpp project hubs (nascence_cpu_server.py) send the two counts only. Returns only
    the keys the reply actually carried, as kwargs for telemetry.log_llm_latency (pe, pe_s, ec, ec_s) --
    missing = unknown, never 0. Pure, never raises."""
    out: dict = {}
    try:
        if not isinstance(data, dict):
            return out
        for src, dst, ns in (("prompt_eval_count", "pe", False), ("prompt_eval_duration", "pe_s", True),
                             ("eval_count", "ec", False), ("eval_duration", "ec_s", True)):
            v = data.get(src)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
                continue
            out[dst] = (float(v) / 1e9) if ns else int(v)
    except Exception:
        return {}
    return out


# J-4142 (F-4964): think=true on qwen3.5:9b spends 1.0k-3.4k tokens in the discarded thinking field.
# At num_predict 1024/2048 every probed think call ended done_reason=length with empty content; at 4096
# Critic and Executive both parsed (Executive used up to 3392 tokens, so 4096 is a thin margin). The old
# budget (max(max_tokens, 1024) + 1024 = 2048 for most callers) was below that floor, so the System-2
# license could only fail and fall back through J-2852's think=False retry. Think calls now ask for
# _THINK_NUM_PREDICT_TARGET, clamped so prompt + generation still fits the lane's num_ctx, never below
# _THINK_NUM_PREDICT_FLOOR. The J-2852 downgrade in call_node_json stays as the backstop.
_THINK_NUM_PREDICT_FLOOR = 4096
_THINK_NUM_PREDICT_TARGET = 6000


def _think_num_predict(max_tokens: int, base_url: str, prompt_chars: int) -> int:
    """num_predict for a think=true call: at least the caller's budget + 1024 (the old rule), aiming for
    _THINK_NUM_PREDICT_TARGET, clamped to the room left in the lane's window after the prompt (~3 chars per
    token, 256 tokens of slack), and never below _THINK_NUM_PREDICT_FLOOR. Fail-open to the floor."""
    try:
        want = max(max(int(max_tokens), 1024) + 1024, _THINK_NUM_PREDICT_TARGET)
        room = _num_ctx_for(base_url) - int(max(0, prompt_chars) / 3) - 256
        return max(_THINK_NUM_PREDICT_FLOOR, min(want, room))
    except Exception:
        return _THINK_NUM_PREDICT_FLOOR


async def call_node(
    base_url: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 512,
    temperature: float = 0.2,
    timeout: int = 120,
    json_mode: bool = True,
    think: bool = False,
    model_override: str | None = None,
    num_gpu: int | None = None,
    tier: int | None = None,
    grammar: bool | None = None,
) -> str:
    """Send a chat completion to an inference lane and return the raw text.

    LANE-AWARE since the first live qwen3 session (2026-06-10 15:50): the /no_think SOFT
    switch is NOT reliable on ollama's OpenAI endpoint — it passed a clean verification call
    but intermittently leaks thinking under real node prompts, burning the whole token budget
    in the (discarded) thinking field and returning EMPTY content ("No JSON object found in
    response: ''", 3 retries exhausted). The eval battery's ~40 calls through ollama's NATIVE
    /api/chat with the HARD `think: false` parameter had zero such failures. So:
      - ollama hot lane (11433)  → native /api/chat, think:false, format:json
      - llama-server lanes       → OpenAI /v1/chat/completions with the /no_think prefix
        (Bonsai is Qwen3-base; the soft switch IS honoured by llama-server's template)

    `grammar` (D-0354, J-1840): None (default) = legacy -- format=json is sent whenever json_mode is.
    False = json_mode still means "the caller wants JSON" but the JSON grammar is withheld on the
    ollama-native lanes (the prompt still asks for JSON; the caller must parse leniently and have a
    retry -- call_node_json does). True = force the grammar. The arm actually used is recorded as `g`
    (1/0) on each data/llm_latency.jsonl row of a json_mode call.
    """
    capped = _cap_prompt(user_prompt, base_url)

    try:                                              # HUD telemetry: one line per call (fire-and-forget)
        from core import telemetry as _tel
        # Window sizing (2026-08-20): record what the prompt ACTUALLY was against the room it was given.
        # `len(capped) < len(user_prompt)` is the truthful truncation test — _cap_prompt cuts from the
        # MIDDLE, where injected memory/recall sits, so this is silent context loss and worth counting.
        # `caller` is `module:line` — see _caller_label. It identifies the prompt JOB, not just the
        # file, which is what makes the three big nodes separable: they hold ~20 distinct jobs
        # between them, on different lanes with different windows and different purposes.
        _resolved_model = model_override or _model_for(base_url)
        _caller = _caller_label()
        _tel.log_llm_call(_resolved_model, base_url,
                          prompt_chars=len(user_prompt), num_ctx=_num_ctx_for(base_url),
                          capped=len(capped) < len(user_prompt), caller=_caller,
                          system_chars=len(system_prompt or ""), fn=_caller_fn())
        # PERSISTENT STATION LOG (J-0939, 2026-09-15, F-1308): log_llm_call above is capped
        # (telemetry._CALLS_CAP, observed ~0.89 days) and cannot answer "which model generated
        # this thought" over thermal_causality.md's pre-registered multi-week window (S9 Row 2 /
        # D-0214's defeater). Same resolved model, same call site, written a second time to an
        # UNCAPPED file — mirrors log_llm_latency's own precedent (a separate ancillary file so
        # llm_calls.jsonl's cap/row-count stays untouched).
        _tel.log_thought_station(_resolved_model, base_url, _caller, fn=_caller_fn())
    except Exception:
        pass

    # ollama-native lanes → /api/chat with hard think:false + format:json.
    # The /v1 (llama-server) branch below is for the now-vestigial Bonsai CPU server only.
    # ollama-STYLE endpoints: the one real ollama instance left (local :11433 — Ramses ollama :11434
    # retired 2026-08-28, founder ruling) plus EVERY nascence_cpu_server.py hub, local and Ramses
    # (11436-11443 — the hub serves ONLY /api/chat|/api/generate|/api/tags|/api/ps, no /v1).
    # 2026-08-28 FIX: the Ramses hub ports 11436/11437/11438 were MISSING here, so D-0044 move 1's
    # judge_mixtral calls to :11438 fell through to /v1/chat/completions → HTTP 404 (verified live
    # this session) → every commitment-defeater call since 08-27 silently failed open to None.
    if any(p in base_url for p in (":11433", ":11436", ":11437", ":11438", ":11439",
                                   ":11440", ":11441", ":11442", ":11444")):
        # ollama native — think stays HARD-OFF by default. `think=True` is the System-2
        # gearbox (2026-06-13, the triple-converged escalation): a deliberate per-call
        # license, granted only at named escalation sites (constraint-retry, deep
        # deliberation), never an ambient default. Thinking needs room and time.
        if think:
            max_tokens = _think_num_predict(max_tokens, base_url,
                                            len(system_prompt or "") + len(capped))
            timeout = max(timeout, 240)
            logger.info("[gearbox] System-2 engaged (think=true, num_predict=%d)", max_tokens)
        _opts = {"temperature": temperature, "num_predict": max_tokens,
                 "num_ctx": _num_ctx_for(base_url)}
        if num_gpu is not None:
            _opts["num_gpu"] = num_gpu          # 0 = force CPU (e.g. the big dreamer at sleep-time)
        payload = {
            "model": model_override or _model_for(base_url),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": capped},
            ],
            "think": bool(think),
            "stream": False,
            "options": _opts,
            # KEEP-ALIVE (2026-08-15): safe again BECAUSE of the serving split — gemma is alone on
            # 11433 and every caller routes through the ONE ctx map above, so the duplicate-runner
            # disease (different ctx sizes spawning extra instances — why Antigravity disabled
            # keep-alive) cannot recur. Pins the Self model warm between thought-gaps; the CPU-tier
            # hubs accept and ignore it (resident by design).
            "keep_alive": "2h",
        }
        _use_grammar = bool(json_mode) and (True if grammar is None else bool(grammar))
        if _use_grammar:
            payload["format"] = "json"
        url = f"{base_url}/api/chat"
        # PER-CALL LATENCY (2026-08-21, founder: "a per call latency check is a good idea"). The 24h
        # review found thoughts ~20s slower than overnight and could not attribute it — llm_calls.jsonl
        # records prompt shape, never duration. Wall-clock from lane-slot acquisition to response
        # parsed (so queueing behind the lane counts — that is the number that explains a slow turn),
        # written to its own file so no existing consumer's row-count changes. Fail-open.
        import time as _time
        _t0 = _time.monotonic()
        _ok = False
        _tok: dict = {}
        _w_req = _time.time()          # J-1971 speech-timing shadow: wall-clock call entry
        _w_start = None
        try:
            async with _lane_slot(tier):
                _w_start = _time.time()  # lane slot acquired
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        _ok = True
                        _tok = _eval_counts(data)       # J-2675: prefill visibility, fail-open
                        return (data.get("message") or {}).get("content") or ""
        finally:
            try:                          # J-1971: own store, observe-only, fail-open
                from core import speech_timing_shadow as _sts
                _sts.log_call(base_url, _caller, _w_req, _w_start, _time.time(), _ok)
            except Exception:
                pass
            try:
                from core import telemetry as _tel2
                _tel2.log_llm_latency(_model_for(base_url), base_url, _caller_label(),
                                      _time.monotonic() - _t0, _ok,
                                      grammar=(1 if _use_grammar else 0) if json_mode else None,
                                      think=bool(think), fn=_caller_fn(),
                                      **_tok)
            except Exception:
                pass

    payload = {
        "model": _model_for(base_url),
        "messages": [
            {"role": "system", "content": _NO_THINK + system_prompt},
            {"role": "user",   "content": capped},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if json_mode:
        # llama-server honours this by constraining sampling to a valid JSON object.
        payload["response_format"] = {"type": "json_object"}

    url = f"{base_url}/v1/chat/completions"
    async with _lane_slot(tier):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"] or ""


def _strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _salvage_json(text: str) -> dict | None:
    """
    Best-effort recovery of a TRUNCATED JSON object — the quantized model's dominant
    failure mode: a long string field (e.g. Reflection's `draft`) consumes the entire
    token budget before the object closes, leaving output like:
        {"draft": "…individuatio
    with no closing quote, no remaining fields, no closing brace. The content is
    perfectly usable — throwing it away and re-inferring is the expensive wrong move.

    Returns a dict if at least one field can be recovered, else None.
    """
    start = text.find("{")
    if start == -1:
        return None
    frag = text[start:].rstrip()

    # Strategy 1 — close the structure and re-parse. Handles the common case where a
    # single trailing string was cut mid-sentence: appending '"}' completes it, and
    # any already-complete earlier fields are recovered too. strict=False tolerates
    # literal newlines/tabs inside string values (the model emits them).
    for suffix in ('', '"}', '}', '"}]}', ']}'):
        try:
            return json.loads(frag + suffix, strict=False)
        except (json.JSONDecodeError, ValueError):
            continue

    # Strategy 2 — field-level regex. Pull the first string-valued field, tolerating an
    # unterminated value (greedy to end-of-text). Loses sibling fields, but downstream
    # _write_output supplies defaults for everything it doesn't find.
    m = re.search(r'"(\w+)"\s*:\s*"(.*)', frag, re.DOTALL)
    if m:
        key, val = m.group(1), m.group(2)
        # Drop a dangling partial escape so the value is clean text.
        val = val.rstrip().rstrip("\\")
        if val:
            return {key: val}

    return None


# J-1992 / F-2593: a runaway idle-thought output (token cap hit while the model repeats its JSON object)
# is stored whole by _salvage_json Strategy 2 as ONE string field, leaking sibling JSON keys into the
# "thought". Strategy 2 is shared by many call_node_json callers that rely on it returning the full tail,
# so the guard lives HERE as a separate helper that the monologue call site opts into.
RUNAWAY_THOUGHT_STATS = {"truncated": 0, "dropped": 0}
_RUNAWAY_KEYS = ("about", "unresolved", "intention", "act", "state", "thought")
_RUNAWAY_MARKER = re.compile(
    r'\\?"\s*,\s*\\?"(?:' + "|".join(_RUNAWAY_KEYS) + r')\\?"\s*:')


def guard_runaway_thought(thought: str) -> str:
    """Cut a salvaged thought at the first leaked-sibling-key marker (quote, comma, quoted JSON key, colon).

    Returns the cleaned thought; "" means the caller should drop it (nothing usable before the marker).
    Text with no marker is returned unchanged (stripped), so clean thoughts are untouched.
    """
    if not thought:
        return ""
    m = _RUNAWAY_MARKER.search(thought)
    if not m:
        return thought
    head = thought[:m.start()].rstrip().rstrip("\\").strip()
    if head and not _RUNAWAY_MARKER.search(head):
        RUNAWAY_THOUGHT_STATS["truncated"] += 1
        logger.warning("runaway thought truncated at leaked JSON key (%d -> %d chars; total %d)",
                       len(thought), len(head), RUNAWAY_THOUGHT_STATS["truncated"])
        return head
    RUNAWAY_THOUGHT_STATS["dropped"] += 1
    logger.warning("runaway thought dropped (leaked JSON key, nothing usable before it; total %d)",
                   RUNAWAY_THOUGHT_STATS["dropped"])
    return ""


def extract_json(text: str) -> dict:
    """
    Extract a JSON object from model output.
    Belt-and-suspenders fallback in case response_format isn't honoured by the build:
    handles <think> tags, markdown code fences, bare braces, and truncated objects.
    """
    text = _strip_think_tags(text)

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1), strict=False)
        except (json.JSONDecodeError, ValueError):
            pass

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0), strict=False)
        except (json.JSONDecodeError, ValueError):
            pass

    # Last resort — salvage a truncated/malformed object rather than discarding it.
    salvaged = _salvage_json(text)
    if salvaged is not None:
        logger.warning("salvaged truncated JSON - recovered fields: %s", list(salvaged.keys()))
        return salvaged

    raise ValueError(f"No JSON object found in response: {text[:300]!r}")


# ── Per-lane circuit breaker (J-1832, F-2466) ─────────────────────────────────────────────────────
# F-2466: during a Ramses stall (20 stretches since 2026-09-07, median 108 min, not one call
# succeeding) every background call_node_json still waited the FULL 120 s on :11441 before failing
# over -- 2,243 such waits, ~75 h of Du's background work spent waiting, and each abandoned request
# kept the (already behind) hub busy. After _BREAKER_FAILS CONSECUTIVE transport timeouts on one lane,
# call_node_json now SKIPS that lane for _BREAKER_COOLOFF seconds (straight to the next server in its
# chain); once the cool-off ends exactly ONE call is let through as a probe (half-open): success closes
# the breaker, a transport failure re-opens it for another cool-off. Transitions go to the uncapped
# data/lane_breaker.jsonl (telemetry.log_lane_breaker) so the stall hours are visible.
#
# Fail-open, like the rest of this module:
#   - a lane is only ever skipped when ANOTHER server in the same chain is not itself tripped -- if
#     every server in the chain is tripped (or the chain has one server) the call is attempted anyway,
#     so a single-endpoint chain behaves EXACTLY as before;
#   - any bug inside the breaker bookkeeping degrades to "go" (the prior behaviour);
#   - only timeouts of calls whose own timeout >= _BREAKER_MIN_TIMEOUT s count (a caller that passes a
#     short timeout is not evidence that the lane is stalled); connection-refused and other fast
#     transport errors neither count nor reset the streak (they cost no wait; the chain already moves
#     on at once) except that they fail a probe.
#   - ANY call that gets a reply (even unparseable JSON) resets the streak -- the lane is alive.
# Scope: only call_node_json (which owns the chain failover). A bare call_node caller is untouched.
# Process-local, in-memory: a restart starts every lane closed.
# F-1907 consequence: SERVE_CHAINS["background"] = [:11441, hot :11433], so a tripped Ramses lane sends
# background work to the HOT lane right away instead of after a 120 s wait -- see the J-1832 finding for
# the measured load.
_BREAKER_FAILS = 3              # consecutive transport timeouts that trip a lane
_BREAKER_COOLOFF = 300.0        # seconds a tripped lane is skipped before one probe call is allowed
_BREAKER_MIN_TIMEOUT = 30       # a call's own timeout (s) must be at least this for its timeout to count

import threading as _threading
import time as _bk_time

_BREAKER_LOCK = _threading.Lock()
_BREAKER: dict = {}             # base_url -> {state, fails, opened_at, since, skipped, probe}; state closed|open|half_open


def _breaker_now() -> float:
    return _bk_time.monotonic()


def _breaker_emit(event: str, base_url: str, st: dict, **kw) -> None:
    try:
        from core import telemetry as _tel
        _tel.log_lane_breaker(event, base_url, fails=st.get("fails", 0), **kw)
    except Exception:
        pass


def _breaker_blocked_locked(base_url: str, now: float) -> bool:
    """True when `base_url` would NOT take a call right now (cooling off, or its one probe is out)."""
    st = _BREAKER.get(base_url)
    if not st or st["state"] == "closed":
        return False
    if st["state"] == "open":
        return (now - st["opened_at"]) < _BREAKER_COOLOFF
    return bool(st.get("probe"))            # half_open: blocked only while its probe is in flight


def _breaker_gate(base_url: str, others: list) -> str:
    """"go" | "probe" | "skip" for one attempt of one lane (see the block comment). Never raises."""
    try:
        with _BREAKER_LOCK:
            st = _BREAKER.get(base_url)
            if not st or st["state"] == "closed":
                return "go"
            now = _breaker_now()
            if st["state"] == "open" and (now - st["opened_at"]) >= _BREAKER_COOLOFF:
                st["state"] = "half_open"
                st["probe"] = True
                _breaker_emit("half_open", base_url, st)
                return "probe"
            for o in others:                    # cooling off, or a probe already out
                if not _breaker_blocked_locked(o, now):
                    st["skipped"] = st.get("skipped", 0) + 1
                    return "skip"
            return "go"                         # nowhere better to send it: fail open, try anyway
    except Exception:
        return "go"


def _breaker_success(base_url: str) -> None:
    """The lane answered (any reply): reset the streak; if it was tripped, close it."""
    try:
        with _BREAKER_LOCK:
            st = _BREAKER.get(base_url)
            if not st:
                return
            if st["state"] != "closed":
                _breaker_emit("close", base_url, st, open_s=_breaker_now() - st.get("since", _breaker_now()),
                              skipped=st.get("skipped", 0))
            st.update(state="closed", fails=0, probe=False, skipped=0)
    except Exception:
        pass


def _breaker_failure(base_url: str, timed_out: bool, timeout: float, probe: bool) -> None:
    """A transport failure on `base_url`. `probe`: this caller is the half-open probe."""
    try:
        with _BREAKER_LOCK:
            now = _breaker_now()
            st = _BREAKER.setdefault(base_url, {"state": "closed", "fails": 0, "opened_at": 0.0,
                                                "since": now, "skipped": 0, "probe": False})
            if probe and st["state"] == "half_open":
                st.update(state="open", opened_at=now, probe=False)
                _breaker_emit("reopen", base_url, st, cooloff=_BREAKER_COOLOFF)
                return
            if st["state"] != "closed" or not timed_out or timeout < _BREAKER_MIN_TIMEOUT:
                return
            st["fails"] += 1
            if st["fails"] >= _BREAKER_FAILS:
                st.update(state="open", opened_at=now, since=now, skipped=0, probe=False)
                _breaker_emit("open", base_url, st, cooloff=_BREAKER_COOLOFF)
    except Exception:
        pass


def _breaker_release_probe(base_url: str) -> None:
    """Probe caller exiting without a recorded outcome (cancelled / non-transport error): hand the
    probe back so the next caller can take it, instead of leaving the lane half-open forever."""
    try:
        with _BREAKER_LOCK:
            st = _BREAKER.get(base_url)
            if st and st["state"] == "half_open" and st.get("probe"):
                st.update(state="open", probe=False)     # opened_at unchanged: next call probes at once
    except Exception:
        pass


def lane_is_tripped(base_url: str, *, note_skip: bool = False) -> bool:
    """J-1880 / F-2503: READ-ONLY view of the J-1832 breaker for callers whose chain has NO alternative
    server (deliberately single-endpoint decoupled judges: core/sitting.py judge_dwell_release,
    core/competence.py's tier-3 witness). True only while `base_url` would not take a call right now --
    open and still inside its cool-off, or half-open with its one probe already in flight. Such a caller
    already treats a failed call as "no verdict" and must never fall back to the hot lane (F-1907), so it
    can return its no-verdict path at once instead of waiting a full timeout. Once the cool-off ends this
    returns False so the caller's next call goes out as the (single) probe. Never raises; any breaker
    problem reads as False (not tripped = the prior behaviour). `note_skip` counts the avoided call in the
    lane's `skipped` tally (reported by the next close event)."""
    try:
        with _BREAKER_LOCK:
            st = _BREAKER.get(base_url)
            if not st or st["state"] == "closed":
                return False
            blocked = _breaker_blocked_locked(base_url, _breaker_now())
            if blocked and note_skip:
                st["skipped"] = st.get("skipped", 0) + 1
            return blocked
    except Exception:
        return False


async def call_node_json(
    base_urls: str | list[str],
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 512,
    temperature: float = 0.2,
    timeout: int = 120,
    retries: int = 2,
    think: bool = False,
    model_override: str | None = None,
    num_gpu: int | None = None,
    tier: int | None = None,
    served: dict | None = None,
) -> dict:
    """
    Call a node and return parsed JSON, with failover across a chain of servers.

    `served` (J-3118, additive, default None = no change): when the caller passes a dict, the server that
    ANSWERED is written into it as {"url": <base_url>, "model": <model name>, "fallback": <bool>} just before
    the parsed JSON is returned. Lets a caller record which hub of a chain actually judged, with no second call
    and no change to the failover / retry / breaker behaviour. Never written on a raise.

    base_urls may be a single URL or an ordered chain (primary first).
      - CONTENT failure (bad/truncated JSON): the server is up, the model misbehaved
        → retry the SAME server up to `retries` times.
      - TRANSPORT failure (connection refused, timeout, hang): the server is down
        → fall through to the NEXT server in the chain immediately.

    Raises ValueError only if every server in the chain is exhausted.
    """
    if isinstance(base_urls, str):
        base_urls = [base_urls]

    last_error: Exception | None = None

    for url_idx, base_url in enumerate(base_urls):
        is_fallback = url_idx > 0
        # J-1832: per-lane circuit breaker -- a lane that just timed out N times running is skipped
        # (fail-open: never skipped when no other server in the chain is available). See the block above.
        _gate = _breaker_gate(base_url, [u for u in base_urls if u != base_url])
        if _gate == "skip":
            logger.info("circuit breaker open on %s -- skipping to the next server", base_url)
            continue
        _is_probe = _gate == "probe"
        try:
            # D-0354: on a no-grammar-first lane the FIRST attempt omits format=json; every retry re-sends
            # WITH it. Needs at least one retry to fall back on -- with retries=0 there is no second
            # attempt, so the grammar stays on (a call that parses today must not be able to fail).
            _drop_first = retries >= 1 and _grammar_optional(base_url)
            # J-2852 (F-3510, D-0531): the System-2 license can return EMPTY content on the qwen3.5 hot lane
            # (the whole raised num_predict is spent in the discarded thinking field). `_think_now` starts as
            # the caller's grant and is withdrawn after the FIRST content failure on this server: the retry
            # goes out think=False at the caller's normal budget instead of repeating a certain failure, and
            # that downgrade earns one extra attempt when the caller's retries were already used up.
            _think_now = bool(think)
            _max_attempt = retries
            attempt = -1
            while attempt < _max_attempt:
                attempt += 1
                _g = (attempt > 0) if _drop_first else None
                try:
                    raw = await call_node(
                        base_url, system_prompt, user_prompt,
                        max_tokens=max_tokens, temperature=temperature, timeout=timeout,
                        think=_think_now, model_override=model_override, num_gpu=num_gpu, tier=tier,
                        grammar=_g,
                    )
                    _breaker_success(base_url)      # the lane answered, whatever it said
                    if is_fallback:
                        logger.info("recovered on fallback server %s", base_url)
                    try:
                        _parsed = extract_json(raw)
                        if served is not None:
                            try:
                                served.update({"url": base_url, "model": model_override or _model_for(base_url),
                                               "fallback": is_fallback})
                            except Exception:
                                pass
                        return _parsed
                    except (json.JSONDecodeError, ValueError):
                        # D-0354 defeater instrument: first-attempt parse-failure rate per caller. The
                        # denominator is this caller's g=0 rows in llm_latency.jsonl. Fail-open.
                        try:
                            from core import telemetry as _tel3
                            _tel3.log_json_parse_fail(_model_for(base_url), base_url, _caller_label(),
                                                      attempt, 0 if _g is False else 1, fn=_caller_fn())
                        except Exception:
                            pass
                        raise
                except (json.JSONDecodeError, ValueError) as exc:
                    # Content failure — server is fine, model gave junk. Retry same server.
                    last_error = exc
                    logger.warning("JSON parse failed on %s (attempt %d/%d): %s",
                                   base_url, attempt + 1, _max_attempt + 1, exc)
                    if _think_now:
                        _think_now = False
                        if attempt >= _max_attempt:
                            _max_attempt = attempt + 1      # the downgrade earns one attempt of its own
                        logger.warning("[gearbox] think=true returned no parseable content on %s (caller %s) "
                                       "-> retrying with think=false at the normal budget (J-2852)",
                                       base_url, _caller_label())
                    if attempt < _max_attempt:
                        await asyncio.sleep(0.5)
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    # Transport failure — server down/hung. Abandon it, try next in chain.
                    last_error = exc
                    # repr(exc), not str(exc): a bare TimeoutError/OSError str()s to EMPTY, which hid the
                    # actual Ramses failure for weeks ("transport error on ...:  — failing over"). Same
                    # bug was fixed in left_lane.py 2026-08-20; this is the site that detects the SPOF.
                    logger.error("transport error on %s: %s — failing over", base_url, repr(exc)[:120])
                    _breaker_failure(base_url, isinstance(exc, asyncio.TimeoutError), timeout, _is_probe)
                    break  # next server
        finally:
            if _is_probe:
                _breaker_release_probe(base_url)

    raise ValueError(f"all servers exhausted {base_urls}: {last_error}")


_PROSE_LEAD = re.compile(
    r"^\s*(?:(?:sure|certainly|of course|okay|ok|here(?:'s| is| are))\b[^\n]*:|-{3,}|\*{3,}|\*\*[^*\n]+\*\*|#+\s.*)\s*$",
    re.I)


def clean_prose(text: str) -> str:
    """D-0584 (J-3196): a plain-prose reply as the caller wants to store it. Trims the reply, drops a wrapping
    code fence and the chatty lead-in a chat model puts on a prose reply despite "no heading": blank lines, a
    markdown heading, a bold title line, a rule, or an offer line like "Sure, here's the first part:" (seen live
    in the J-3196 smoke run: the same lead-ins broke the JSON form). The part's title is the caller's own, from the
    outline. Only LEADING lines go; nothing inside the prose is rewritten -- the words are the model's."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[A-Za-z]*\s*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t).strip()
    lines = t.split("\n")
    while lines and (not lines[0].strip() or _PROSE_LEAD.match(lines[0])):
        lines.pop(0)
    return "\n".join(lines).strip()


def prose_usable(text: str, min_chars: int = 80) -> bool:
    """The whole 'parse' step of a plain-prose call: long enough, and not a JSON object the model wrote anyway."""
    return len(text) >= min_chars and not text.startswith("{")


async def call_node_prose(
    base_urls: str | list[str],
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 512,
    temperature: float = 0.2,
    timeout: int = 120,
    retries: int = 1,
    min_chars: int = 80,
    think: bool = False,
    model_override: str | None = None,
    num_gpu: int | None = None,
    tier: int | None = None,
) -> str:
    """D-0584 (J-3196): call a node for PLAIN PROSE -- no JSON contract, no grammar -- and return the cleaned text.

    Same chain/failover/breaker shape as call_node_json, so a caller swaps one for the other and nothing
    else about the lane handling changes:
      - CONTENT failure (reply shorter than `min_chars` after cleaning, or a JSON object): retry the SAME server
        up to `retries` times (plain, no grammar -- there is no format to fail, a retry only re-rolls the dice).
      - TRANSPORT failure (refused, timeout, hang): abandon this server, try the NEXT one in the chain.
    Raises ValueError only if every server in the chain is exhausted (transport) or still returns unusable text.
    The call goes out with json_mode=False, so data/llm_latency.jsonl rows carry no `g` field (the prose stage is
    told apart from the JSON stage it replaces by that and by its caller label)."""
    if isinstance(base_urls, str):
        base_urls = [base_urls]

    last_error: Exception | None = None

    for url_idx, base_url in enumerate(base_urls):
        is_fallback = url_idx > 0
        _gate = _breaker_gate(base_url, [u for u in base_urls if u != base_url])
        if _gate == "skip":
            logger.info("circuit breaker open on %s -- skipping to the next server", base_url)
            continue
        _is_probe = _gate == "probe"
        try:
            for attempt in range(retries + 1):
                try:
                    raw = await call_node(
                        base_url, system_prompt, user_prompt,
                        max_tokens=max_tokens, temperature=temperature, timeout=timeout,
                        json_mode=False, think=think, model_override=model_override, num_gpu=num_gpu, tier=tier,
                    )
                    _breaker_success(base_url)      # the lane answered, whatever it said
                    if is_fallback:
                        logger.info("recovered on fallback server %s", base_url)
                    text = clean_prose(raw)
                    if prose_usable(text, min_chars):
                        return text
                    last_error = ValueError(f"unusable prose reply ({len(text)} chars)")
                    logger.warning("prose reply unusable on %s (attempt %d/%d): %d chars",
                                   base_url, attempt + 1, retries + 1, len(text))
                    if attempt < retries:
                        await asyncio.sleep(0.5)
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    last_error = exc
                    logger.error("transport error on %s: %s -- failing over", base_url, repr(exc)[:120])
                    _breaker_failure(base_url, isinstance(exc, asyncio.TimeoutError), timeout, _is_probe)
                    break  # next server
        finally:
            if _is_probe:
                _breaker_release_probe(base_url)

    raise ValueError(f"all servers exhausted {base_urls}: {last_error}")

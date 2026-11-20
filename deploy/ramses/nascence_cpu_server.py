"""
Nascence — CPU-tier model server (2026-08-15, the serving split).

One llama.cpp (llama-cpp-python) instance per model, mimicking the Ollama API so every existing
caller migrates with a URL change only. Descended from FreshStart's llama_hub_server.py (the
Oracle's proven pattern on this same Threadripper), upgraded for Nascence's needs:
  - create_chat_completion → the GGUF's OWN chat template (llama3/qwen/mistral differ; naive
    role-concatenation degrades them all)
  - `format: "json"` honoured via response_format (the judges depend on strict JSON)
  - fixed n_ctx per instance at load — the duplicate-runner problem (different ctx sizes spawning
    extra instances, why keep-alive was disabled) is impossible here by construction

Usage:
    python nascence_cpu_server.py --model <path.gguf> --alias llama3.1:8b --port 11439 --threads 14 --ctx 8192

WHY: ollama's single manager owning both the GPU mind and the CPU models is the root of the July
eviction freeze and the CPU/GPU separation trouble; the split gives gemma a manager-free GPU and
the CPU tier no manager at all. See docs/reports/llm_audit_aug15.md + AWAITING_EVIDENCE 08-15.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time

# 2026-08-23 (merged back from Ramses — see below): a fully detached/no-console launch (the
# pattern Ramses's own start_ramses_tier.ps1 uses, subprocess.Popen with DETACHED_PROCESS) can
# hand a process std handles that are None rather than real streams. Guard both directions.
if sys.stdin is None:
    sys.stdin = open(os.devnull, "r", encoding="utf-8")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
else:
    sys.stdout.reconfigure(encoding="utf-8")   # the charmap law
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
else:
    sys.stderr.reconfigure(encoding="utf-8")

# 2026-09-06 (merged back from Ramses, found undocumented on the network-folder copy while
# deploying J-0526's timestamp/stdin-guard fixes — see F-0920): llama-cpp-python's CUDA build on
# Windows needs the pip-installed nvidia-* packages' bin/ folders (cublas, cuda runtime, nvrtc) on
# the DLL search path, which Python does not add automatically. Without this, a CUDA-enabled
# process can fail to find the CUDA DLLs at import/load time depending on how the environment was
# set up. Never reported back through NASCENCE_NOTES.md before this pass — the two GPU hubs
# (:11437, :11441) were live on the drifted copy that already had it; this brings the canonical
# copy back in sync so a future deploy from here doesn't silently regress their CUDA loading.
try:
    import site
    for _p in site.getsitepackages():
        _nv = os.path.join(_p, "nvidia")
        if os.path.isdir(_nv):
            for _sub in os.listdir(_nv):
                _bin = os.path.join(_nv, _sub, "bin")
                if os.path.isdir(_bin):
                    os.add_dll_directory(_bin)
                    os.environ["PATH"] = _bin + ";" + os.environ["PATH"]
except Exception:
    pass

# 2026-11-11 (Ramses/Argon forensic audit, NASCENCE_NOTES.md 11-11): CUDA_VISIBLE_DEVICES used to be
# set in main(), AFTER `from llama_cpp import Llama` below had already initialised CUDA. So the
# CPU-only hubs (:11436, :11438, :11444) each opened a CUDA context on GPU 0 (the 3070) and ate
# its scarce VRAM headroom, helping push :11441 into PCIe spill. The env var must be fixed
# BEFORE the llama import, so sniff the two relevant flags from sys.argv here (argparse in
# main() still owns the real parsing). CPU-only (gpu-layers 0, the default) and no explicit
# --cuda-device -> hide every GPU. An explicit --cuda-device always wins.
def _argv_value(flag: str):
    for i, a in enumerate(sys.argv):
        if a == flag and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if a.startswith(flag + "="):
            return a.split("=", 1)[1]
    return None


_pre_dev = _argv_value("--cuda-device")
_pre_layers = _argv_value("--gpu-layers")
if _pre_dev is not None:
    os.environ["CUDA_VISIBLE_DEVICES"] = str(_pre_dev)
else:
    try:
        _cpu_only = int(_pre_layers or 0) == 0
    except ValueError:
        _cpu_only = False
    if _cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from llama_cpp import Llama


def _ts() -> str:
    """Local HH:MM:SS.mmm prefix for the hub's own print-based log lines. Added 2026-09-03
    (J-0500, from F-0692): cpu_tier_*.log had none, which blocked correlating judge_panel's
    'unavailable' verdicts (which DO carry a wall-clock ts) against this hub's own
    loading/idle-unload/[chat] lines by hand — the exact gap F-0692 hit while diagnosing D-0039's
    mechanism. Plain wall-clock (not monotonic) on purpose: this is for human/log-join reading
    against other logs' timestamps, not measuring elapsed time within this process."""
    import datetime as _dt
    return _dt.datetime.now().strftime("%H:%M:%S.%f")[:-3]


app = FastAPI(title="Nascence CPU tier")
# LAZY LOCK (2026-08-23, merged back from Ramses): asyncio.Lock() at MODULE level runs at import
# time, before any event loop exists — under uvicorn.run()'s own loop this can bind to the wrong
# loop or raise depending on platform/version. get_gen_lock() defers creation to first actual use,
# inside a running loop, which is always safe. Found and fixed operating this exact script on
# Ramses; adopted here so the local hubs (11439-11442) get the same fix, not just Ramses's copy.
_gen_lock: "asyncio.Lock | None" = None


def get_gen_lock() -> asyncio.Lock:
    global _gen_lock
    if _gen_lock is None:
        _gen_lock = asyncio.Lock()
    return _gen_lock


llm: "Llama | None" = None
ALIAS = "model"

# ---------------------------------------------------------------------------------------------
# ABANDONED-WORK / DEADLINE / STATUS (2026-10-06, J-1830, from F-2466). Measured there: this hub ran
# every request to completion under its single generation lock even after the caller had hung up
# (a 300-token job abandoned after 3s still blocked the NEXT call for 32s), and nothing bounded a
# single generation. On the three i9-dependent Ramses hubs that abandoned work is what kept the CPU
# busy after Du's 120s/90s/300s client timeouts, turning a slowdown into an hours-long stall. Four
# additive changes, response shape unchanged (message.content / eval_count / prompt_eval_count /
# done still present; `done_reason` is a NEW key, ollama-style, that existing parsers ignore):
#   (a) after acquiring the lock and before loading/generating, a caller that has already gone
#       (Starlette Request.is_disconnected) is dropped without generating a single token;
#   (b) generation runs with stream=True in the executor thread and stops BETWEEN tokens when the
#       hub-side deadline (--max-gen-seconds, default 150) passes or the client disconnects; what
#       exists so far is returned with done_reason = stop | length | deadline | disconnected;
#   (c) the [chat]/[generate] log line carries lock-wait and generate time as separate numbers, and
#       GET /api/status reports whether a generation is in flight, for how long, and the queue depth;
#   (d) /api/generate gets the same treatment through the same helper.
# The disconnect check needs the event loop (is_disconnected is a coroutine), so while the executor
# thread generates, a small loop-side poller flips a threading.Event the generator thread reads.
# ---------------------------------------------------------------------------------------------
_DISCONNECT_POLL_S = 0.25            # how often the loop-side poller asks "is the caller still there?"
_STATUS_LOCK = threading.Lock()      # the status dict is read on the loop and written by the executor
_STATUS: dict = {
    "started_wall": time.time(),     # process start (wall clock), for uptime
    "queue_depth": 0,                # requests waiting for the generation lock right now
    "in_flight": None,               # None, or the dict _begin_inflight() builds
    "counters": {"requests": 0, "completed": 0, "deadline_cuts": 0,
                 "abandoned_before_gen": 0, "abandoned_during_gen": 0, "errors": 0},
}


def _status_bump(key: str) -> None:
    with _STATUS_LOCK:
        _STATUS["counters"][key] = _STATUS["counters"].get(key, 0) + 1


def _begin_inflight(endpoint: str, lock_wait_s: float, deadline_s: float, json_mode: bool) -> dict:
    d = {"endpoint": endpoint, "started_wall": time.time(), "started_mono": time.monotonic(),
         "lock_wait_s": round(lock_wait_s, 3), "deadline_s": deadline_s, "json": json_mode,
         "tokens": 0, "phase": "loading"}
    with _STATUS_LOCK:
        _STATUS["in_flight"] = d
    return d


def _end_inflight() -> None:
    with _STATUS_LOCK:
        _STATUS["in_flight"] = None


def _max_gen_seconds() -> float:
    v = getattr(_ARGS, "max_gen_seconds", 150.0)
    try:
        return float(v)
    except Exception:
        return 150.0


def _run_stream(stream_iter, text_of, gone: threading.Event, deadline_s: float,
                inflight: dict) -> tuple[str, int, int, str]:
    """Executor-thread half of (b). Pulls chunks off a llama-cpp stream one at a time and stops
    pulling (which IS how generation stops: the generator does nothing until asked for the next
    token) when the deadline passes or the caller is gone. `text_of(chunk)` extracts the text for
    the chat/completion chunk shapes. Returns (content, prompt_tokens, completion_tokens, done_reason).
    Token counts come from the model's own evaluated-token position (`llm.n_tokens`): at the first
    chunk it equals the prompt length (prompt evaluated, first token sampled, not yet evaluated),
    and each later chunk advances it by one — verified against the non-streaming `usage` numbers
    in J-1830's local test. A chunk can carry more than one token only in the multi-byte-character
    case, where this count is the model's position rather than a chunk tally, so it stays right."""
    parts: list[str] = []
    prompt_tokens = 0
    completion_tokens = 0
    done_reason = "stop"
    finish_reason = None
    t_start = time.monotonic()
    first = True
    try:
        for chunk in stream_iter:
            choice = (chunk.get("choices") or [{}])[0]
            fr = choice.get("finish_reason")
            piece = text_of(choice)
            if first:
                first = False
                prompt_tokens = int(getattr(llm, "n_tokens", 0) or 0)
                inflight["phase"] = "generating"
            if piece:
                parts.append(piece)
            if fr is not None:
                finish_reason = fr
                break
            if piece:
                completion_tokens = max(completion_tokens, int(getattr(llm, "n_tokens", 0) or 0) - prompt_tokens + 1)
                inflight["tokens"] = completion_tokens
            # the two early-stop checks, between tokens — the whole point of streaming here
            if gone.is_set():
                done_reason = "disconnected"
                break
            if deadline_s > 0 and (time.monotonic() - t_start) > deadline_s:
                done_reason = "deadline"
                break
    finally:
        close = getattr(stream_iter, "close", None)
        if close is not None:
            try:
                close()
            except Exception:
                pass
    if done_reason == "stop":
        done_reason = "length" if finish_reason == "length" else "stop"
    return "".join(parts), prompt_tokens, completion_tokens, done_reason


async def _generate_guarded(request: Request, endpoint: str, json_mode: bool,
                            make_stream, text_of) -> dict | None:
    """Loop-side half of (a)+(b)+(c). Serialises on the generation lock like before, but: drops a
    caller that is already gone once the lock is held (no load, no tokens); runs the stream in the
    executor with a loop-side disconnect poller feeding a threading.Event; returns the usual dict
    of (content, prompt_tokens, completion_tokens, done_reason, lock_wait_s, gen_s) or None when
    the caller was gone before generation started (the endpoint answers 499 then — nobody reads it).
    `make_stream()` must be called ONLY in the executor thread (it may trigger prompt evaluation)."""
    _status_bump("requests")
    t_arrive = time.monotonic()
    acquired = False
    with _STATUS_LOCK:
        _STATUS["queue_depth"] += 1
    try:
        async with get_gen_lock():
            acquired = True
            with _STATUS_LOCK:
                _STATUS["queue_depth"] -= 1
            lock_wait_s = time.monotonic() - t_arrive
            # (a) the caller may have given up while we queued: do not spend a token on it
            try:
                if await request.is_disconnected():
                    _status_bump("abandoned_before_gen")
                    print(f"[{_ts()}] [{endpoint}] caller gone after {lock_wait_s:.1f}s in queue "
                          f"— skipped (json={json_mode})")
                    return None
            except Exception:
                pass    # the check is best-effort; a failure here must never block a real call
            deadline_s = _max_gen_seconds()
            inflight = _begin_inflight(endpoint, lock_wait_s, deadline_s, json_mode)
            loop = asyncio.get_event_loop()
            gone = threading.Event()

            async def _poll_disconnect() -> None:
                while True:
                    await asyncio.sleep(_DISCONNECT_POLL_S)
                    try:
                        if await request.is_disconnected():
                            gone.set()
                            return
                    except Exception:
                        return

            def _work():
                _ensure_loaded()                       # lazy hubs load here (cold ~30-90s)
                if gone.is_set():                      # went away during a cold load
                    return "", 0, 0, "disconnected"
                return _run_stream(make_stream(), text_of, gone, deadline_s, inflight)

            poller = loop.create_task(_poll_disconnect())
            t_gen = time.monotonic()
            try:
                content, p_tok, c_tok, done_reason = await loop.run_in_executor(None, _work)
            except Exception as exc:
                _status_bump("errors")
                raise HTTPException(status_code=500, detail=f"inference failed: {exc}")
            finally:
                poller.cancel()
                _end_inflight()
            gen_s = time.monotonic() - t_gen
    except BaseException:
        # the queue_depth decrement happens on lock acquisition; a cancel while still waiting must
        # not leave a phantom waiter behind in /api/status
        if not acquired:
            with _STATUS_LOCK:
                _STATUS["queue_depth"] = max(0, _STATUS["queue_depth"] - 1)
        raise
    if done_reason == "deadline":
        _status_bump("deadline_cuts")
    elif done_reason == "disconnected":
        _status_bump("abandoned_during_gen")
    else:
        _status_bump("completed")
    return {"content": content, "prompt_tokens": p_tok, "completion_tokens": c_tok,
            "done_reason": done_reason, "lock_wait_s": lock_wait_s, "gen_s": gen_s}


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = ""
    messages: List[Message]
    stream: bool = False
    format: Optional[str] = None
    options: Optional[dict] = None
    keep_alive: Optional[object] = None    # accepted and ignored (resident by design)


class GenerateRequest(BaseModel):
    model: str = ""
    prompt: str
    stream: bool = False
    format: Optional[str] = None
    options: Optional[dict] = None
    keep_alive: Optional[object] = None


@app.get("/api/tags")
async def tags():
    return {"models": [{"name": ALIAS, "model": ALIAS, "size": 0, "digest": ALIAS,
                        "details": {"format": "gguf", "family": "cpu-tier"}}]}


@app.get("/api/ps")
async def ps():
    return {"models": [{"name": ALIAS, "model": ALIAS, "size": 0, "size_vram": 0,
                        "digest": ALIAS, "expires_at": "never"}]}


def _gen_kwargs(options: dict, fmt: Optional[str]) -> dict:
    kw = {
        "temperature": float(options.get("temperature", 0.7)),
        "top_p": float(options.get("top_p", 0.9)),
        "max_tokens": int(options.get("num_predict", 512)),
    }
    if fmt == "json":
        kw["response_format"] = {"type": "json_object"}
    return kw


@app.get("/api/status")
async def status():
    """(c) J-1830: is a generation in flight, for how long, and how deep is the queue — the hub-side
    view F-2466 had to infer from the outside (a tiny probe hanging 45s). Read-only, never locks."""
    with _STATUS_LOCK:
        inflight = dict(_STATUS["in_flight"]) if _STATUS["in_flight"] else None
        queue_depth = _STATUS["queue_depth"]
        counters = dict(_STATUS["counters"])
        started = _STATUS["started_wall"]
    if inflight is not None:
        inflight["elapsed_s"] = round(time.monotonic() - inflight.pop("started_mono"), 3)
    return {"model": ALIAS, "loaded": llm is not None, "in_flight": inflight,
            "queue_depth": queue_depth, "max_gen_seconds": _max_gen_seconds(),
            "counters": counters, "uptime_s": round(time.time() - started, 1)}


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    options = req.options or {}
    kw = _gen_kwargs(options, req.format)
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    json_mode = req.format == "json"
    r = await _generate_guarded(
        request, "chat", json_mode,
        make_stream=lambda: llm.create_chat_completion(messages=msgs, stream=True, **kw),
        text_of=lambda choice: (choice.get("delta") or {}).get("content") or "")
    if r is None:
        return JSONResponse(status_code=499, content={"model": ALIAS, "done": False,
                                                     "done_reason": "disconnected"})
    content = r["content"]
    print(f"[{_ts()}] [chat] {len(msgs)} msgs -> {len(content)} chars "
          f"wait={r['lock_wait_s']:.1f}s gen={r['gen_s']:.1f}s tok={r['completion_tokens']} "
          f"done={r['done_reason']} (json={json_mode})")
    return {"model": ALIAS, "created_at": "now",
            "message": {"role": "assistant", "content": content}, "done": True,
            "done_reason": r["done_reason"],
            "prompt_eval_count": r["prompt_tokens"],
            "eval_count": r["completion_tokens"]}


@app.post("/api/generate")
async def generate(req: GenerateRequest, request: Request):
    options = req.options or {}
    kw = _gen_kwargs(options, req.format)
    kw.pop("response_format", None)        # completion path: JSON grammar unsupported, honest refusal
    prompt = req.prompt
    r = await _generate_guarded(
        request, "generate", False,
        make_stream=lambda: llm(prompt=prompt, echo=False, stream=True, **kw),
        text_of=lambda choice: choice.get("text") or "")
    if r is None:
        return JSONResponse(status_code=499, content={"model": ALIAS, "done": False,
                                                     "done_reason": "disconnected"})
    text = r["content"]
    print(f"[{_ts()}] [generate] {len(prompt)} chars -> {len(text)} chars "
          f"wait={r['lock_wait_s']:.1f}s gen={r['gen_s']:.1f}s tok={r['completion_tokens']} "
          f"done={r['done_reason']}")
    return {"model": ALIAS, "created_at": "now", "response": text, "done": True,
            "done_reason": r["done_reason"],
            "prompt_eval_count": r["prompt_tokens"],
            "eval_count": r["completion_tokens"]}


_ARGS = None
_last_used = 0.0
_load_lock = None


def _ensure_loaded() -> None:
    """Load the model if absent. RAM RULE (founder, 2026-08-15): 64GB total — the dreamer must not
    co-reside with everything at all times, so hubs support --lazy (load on first request) and
    --idle-unload (free the RAM after quiet minutes; Du barely thinks while dreams run, so the swap
    is natural). Synchronous — called under get_gen_lock()'s protection via the loading path."""
    global llm, _last_used
    if llm is None:
        _gl = getattr(_ARGS, "gpu_layers", 0)
        _cd = getattr(_ARGS, "cuda_device", None)
        print(f"[{_ts()}] [cpu-tier] loading {ALIAS} from {_ARGS.model} "
              f"(ctx={_ARGS.ctx}, t={_ARGS.threads}, gpu_layers={_gl}, "
              f"cuda_device={_cd if _cd is not None else 'unset'})…")
        t0 = time.time()
        llm = Llama(model_path=_ARGS.model, n_ctx=_ARGS.ctx, n_threads=_ARGS.threads,
                    n_gpu_layers=_gl, verbose=False)
        print(f"[{_ts()}] [cpu-tier] {ALIAS} loaded in {time.time()-t0:.0f}s")
    _last_used = time.time()


async def _idle_unloader() -> None:
    global llm
    while True:
        await asyncio.sleep(60)
        if llm is not None and _ARGS.idle_unload > 0 and time.time() - _last_used > _ARGS.idle_unload:
            async with get_gen_lock():
                print(f"[{_ts()}] [cpu-tier] {ALIAS} idle {_ARGS.idle_unload}s — unloading (RAM freed)")
                # 2026-08-16 (found by the ablation lab): llama_cpp's close() can raise
                # AttributeError ('LlamaModel' has no attribute 'sampler') during teardown,
                # which left the hub answering 500 forever. Guard the teardown; the reload
                # path (_ensure_loaded) recovers cleanly afterwards.
                _old, llm = llm, None
                try:
                    _old.close()
                except Exception as _exc:
                    print(f"[{_ts()}] [cpu-tier] teardown warning (non-fatal): {_exc}")
                del _old
                import gc
                gc.collect()


@app.on_event("startup")
async def _startup():
    asyncio.get_event_loop().create_task(_idle_unloader())
    if not _ARGS.lazy:
        # eager: load in the background AFTER the port binds — the port answering immediately is
        # the duplicate-spawn guard (launchers test the port; a loading hub must already look alive)
        async def _bg():
            async with get_gen_lock():
                await asyncio.get_event_loop().run_in_executor(None, _ensure_loaded)
        asyncio.get_event_loop().create_task(_bg())


def main() -> None:
    global ALIAS, _ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="path to a GGUF (ollama blobs work)")
    ap.add_argument("--alias", default="cpu-model", help="model name reported to clients")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--threads", type=int, default=14)
    # --gpu-layers added 2026-08-20. Default 0 = the previous hardcoded behaviour EXACTLY, so every
    # existing local hub is unchanged. It exists for RAMSES, which has a spare GTX 1650 Super (4 GB)
    # sitting in ollama's undirected pool. The founder's standing objection to ollama — it handles a
    # CPU/GPU split badly, which is why llama.cpp is used everywhere else — does not apply to a model
    # that fits ENTIRELY on one card: with all layers on the GPU there is no split to mishandle. On a
    # 4 GB card that means llama3.2:1b (1.32 GB) or gemma:2b (1.68 GB), both already pulled on Ramses.
    # Pass a large number (e.g. 99) to put every layer on the GPU; partial offload is exactly the
    # split we are avoiding, so prefer all-or-nothing.
    ap.add_argument("--gpu-layers", type=int, default=0, dest="gpu_layers",
                    help="layers to offload to GPU (0 = CPU-only, the default; 99 = all)")
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--lazy", action="store_true", help="load on first request instead of at startup")
    ap.add_argument("--idle-unload", type=int, default=0, dest="idle_unload",
                    help="seconds of quiet after which the model is unloaded (0 = resident)")
    # --cuda-device added 2026-08-23, for Ramses running TWO GPU hubs (1650 Super + 3070). Without
    # this, CUDA picks a default device by its own ordering — the exact "which card by load order,
    # not by design" disease this whole llama.cpp-per-model architecture exists to fix (ollama was
    # already caught doing this: 9.82 GB resident against an 8 GB 3070, spilling onto the 1650S
    # undirected). Setting CUDA_VISIBLE_DEVICES before the model loads makes the OTHER GPU invisible
    # to this process — not a preference, a hard guarantee. Irrelevant (and left unset) for the
    # CPU-only hubs, which never touch --gpu-layers.
    ap.add_argument("--cuda-device", type=int, default=None, dest="cuda_device",
                    help="physical GPU index this process may see (pins it via CUDA_VISIBLE_DEVICES; "
                         "unset = CUDA picks by its own default, which is what we're avoiding)")
    # --host added 2026-08-23 (merged back from Ramses — a REAL bug this fixed, not cosmetic): the
    # previous hardcoded host="127.0.0.1" made a hub UNREACHABLE from any other machine, and Ramses's
    # whole purpose is being called from the Nascence box across the network — bound to loopback-only,
    # it would never have answered a single external curl. DEFAULT KEPT AT 127.0.0.1 deliberately
    # (not flipped to 0.0.0.0): the local hubs (11439-11442) are loopback-only today, and changing
    # the default would silently widen every existing local hub's network exposure to the whole LAN
    # as a side effect of a Ramses-only need. launch_ramses.ps1 passes --host 0.0.0.0 explicitly for
    # exactly the hubs that need it; nothing else changes behaviour.
    ap.add_argument("--host", default="127.0.0.1", help="interface to bind (127.0.0.1 = loopback "
                    "only, the existing local-hub behaviour; 0.0.0.0 = reachable over the network, "
                    "needed for any cross-machine hub like Ramses)")
    # --log added 2026-08-23 (merged back from Ramses): redirect this process's own stdout/stderr to
    # a file. Useful when the launcher fully detaches the process (no console, no inherited handles
    # to redirect from the parent side) — Ramses's start_ramses_tier.ps1 does exactly this.
    ap.add_argument("--log", default=None, help="path to redirect stdout/stderr to (for fully "
                    "detached launches with no console to capture otherwise)")
    # --max-gen-seconds added 2026-10-06 (J-1830, F-2466): hub-side deadline on ONE generation,
    # measured from the moment generation starts (after the lock, after any lazy load), checked
    # between tokens. Default 150s sits above Du's longest ordinary client timeouts on these hubs
    # (model_client 120s, lane2 90s) so a healthy call is never cut, while a runaway one can no
    # longer hold the lock for minutes after every caller has given up. 0 disables the deadline.
    ap.add_argument("--max-gen-seconds", type=float, default=150.0, dest="max_gen_seconds",
                    help="stop a single generation between tokens after this many seconds and "
                         "return what exists with done_reason=deadline (0 = no deadline)")
    args = ap.parse_args()
    if args.cuda_device is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_device)
    ALIAS = args.alias
    _ARGS = args
    if args.log:
        try:
            log_f = open(args.log, "a", encoding="utf-8", buffering=1)
            sys.stdout = log_f
            sys.stderr = log_f
        except Exception:
            pass
    print(f"[cpu-tier] {ALIAS} on :{args.port} — {'LAZY' if args.lazy else 'eager'}"
          f"{', idle-unload ' + str(args.idle_unload) + 's' if args.idle_unload else ''} (port binds first)")
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()

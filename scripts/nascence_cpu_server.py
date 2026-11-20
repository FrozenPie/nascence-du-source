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

from fastapi import FastAPI, HTTPException
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


@app.post("/api/chat")
async def chat(req: ChatRequest):
    options = req.options or {}
    kw = _gen_kwargs(options, req.format)
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    t0 = time.time()
    async with get_gen_lock():
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, _ensure_loaded)   # lazy hubs load here (cold ~30-90s)
            resp = await loop.run_in_executor(
                None, lambda: llm.create_chat_completion(messages=msgs, **kw))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"inference failed: {exc}")
    content = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
    print(f"[{_ts()}] [chat] {len(msgs)} msgs -> {len(content)} chars in {time.time()-t0:.1f}s "
          f"(json={req.format=='json'})")
    return {"model": ALIAS, "created_at": "now",
            "message": {"role": "assistant", "content": content}, "done": True,
            "prompt_eval_count": (resp.get("usage") or {}).get("prompt_tokens", 0),
            "eval_count": (resp.get("usage") or {}).get("completion_tokens", 0)}


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    options = req.options or {}
    kw = _gen_kwargs(options, req.format)
    kw.pop("response_format", None)        # completion path: JSON grammar unsupported, honest refusal
    t0 = time.time()
    async with get_gen_lock():
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, _ensure_loaded)
            resp = await loop.run_in_executor(
                None, lambda: llm(prompt=req.prompt, echo=False, **kw))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"inference failed: {exc}")
    text = (resp.get("choices") or [{}])[0].get("text", "")
    print(f"[{_ts()}] [generate] {len(req.prompt)} chars -> {len(text)} chars in {time.time()-t0:.1f}s")
    return {"model": ALIAS, "created_at": "now", "response": text, "done": True,
            "prompt_eval_count": (resp.get("usage") or {}).get("prompt_tokens", 0),
            "eval_count": (resp.get("usage") or {}).get("completion_tokens", 0)}


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


# J-1930 (2026-10-07, F-2555): the 'Exception in callback _ProactorBasePipeTransport._call_connection_lost()
# ... ConnectionResetError [WinError 10054]' traceback is benign CPython-on-Windows close noise (the
# proactor transport calls sock.shutdown unguarded in a finally AFTER protocol.connection_lost ran; the
# peer -- Du's per-request aiohttp session or the supervisor health probe -- had already reset the socket).
# It was 28-77% of every line in data/logs/cpu_tier_{11439,11440,11442}.log. This handler recognises EXACTLY
# that case (ConnectionResetError with winerror 10054 raised from a _call_connection_lost handle) and logs
# one DEBUG line instead; anything else goes to loop.default_exception_handler() unchanged. Log-only; the
# loop policy is untouched (switching to the selector loop would change uvicorn behaviour). Inline copy of
# core/asyncio_quiet.py on purpose: this file is standalone (also deployed on Ramses, see the header) and
# must not import the Nascence package. Takes effect at the next supervisor restart of each hub.
_QUIET_WINERROR = 10054
_quieted_resets = 0


def _is_benign_connection_reset(context: dict) -> bool:
    exc = context.get("exception")
    if not isinstance(exc, ConnectionResetError) or getattr(exc, "winerror", None) != _QUIET_WINERROR:
        return False
    handle = context.get("handle")
    where = repr(handle) if handle is not None else str(context.get("message", ""))
    return "_call_connection_lost" in where


def _install_quiet_connection_reset(loop: "asyncio.AbstractEventLoop") -> None:
    import logging
    _log = logging.getLogger("asyncio")
    previous = loop.get_exception_handler()
    if getattr(previous, "_nascence_quiet_reset", False):
        return

    def _handler(lp, context):
        global _quieted_resets
        if _is_benign_connection_reset(context):
            _quieted_resets += 1
            _log.debug("[asyncio-quiet] peer reset during transport close (WinError 10054 in "
                       "_call_connection_lost) -- benign, suppressed; total %d", _quieted_resets)
            return
        if previous is not None:
            previous(lp, context)
        else:
            lp.default_exception_handler(context)

    _handler._nascence_quiet_reset = True
    loop.set_exception_handler(_handler)


@app.on_event("startup")
async def _startup():
    try:
        _install_quiet_connection_reset(asyncio.get_running_loop())   # J-1930, see above
    except Exception as _exc:
        print(f"[{_ts()}] [cpu-tier] asyncio-quiet handler not installed (non-fatal): {_exc}")
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

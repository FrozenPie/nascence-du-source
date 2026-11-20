"""core/idle_offloop.py (J-1918 / F-2547, 2026-10-07, restart-gated).

The awake idle-thought path used to run four blocking lookups ON the event loop:
  * nodes/inner_monologue_node.py _think(): core.scholar.consult_sync() (a synchronous urllib.request.urlopen to the
    hot lane /api/chat, timeout 20 s) and core.memory_service.ask('curiosity', ..., descend=True) (embed + matrix scan
    + a few sqlite reads, median 0.76 s), once per DEEPMEM_COOLDOWN (300 s);
  * nodes/curiosity_node.py CuriosityNode._write_output() (a sync def called by NodeBase.run on the loop; async since J-1918,
    NodeBase.run/run_best_of now await an awaitable result): core.web_research.lookup_targeted() / lookup() (blocking urllib to
    Wikipedia, timeout 10 s each, up to 2-3 fetches) and consult_sync().
While they ran the whole event loop stood still: 47 + 9 of the 199 competence-timer late wakes, 274 s + 68 s, up to
20 s (F-2547).

`off_loop(fn, *args, **kw)` runs one such call in a worker thread and AWAITS it, so the caller's own order, branches,
fail-open try/except, cooldown clocks and log lines are untouched (an exception in fn is re-raised into the caller
exactly as the synchronous call raised it) -- only the loop is free.

Thread-safety audit of every wrapped call (J-1918), the shared mutable things each touches:
  consult_sync / lookup_targeted / lookup / term_from_question: one fresh urllib request per call, imports inside the
    function (the import lock serialises first import), reads module constants (SERVE_CHAINS, _MODEL_FIELD, _UA); no
    cache, no file, no connection -- nothing shared.
  memory_service.ask:
    - sqlite: every read opens its own connection through core.memory.store._connect() / memory_edges._connect()
      (per call, check_same_thread=False, busy_timeout 30 s) -- never a cached shared handle.
    - core.memory.store._embed: ONE shared SentenceTransformer, and HF fast tokenizers are not safe for concurrent use
      ("Already borrowed"): store._EMBED_LOCK now serialises encode() (and the lazy model load) -- held only for the call.
    - associative_recall._cache + data/embedding_matrix.npz (refreshed through ONE shared tmp name): _matrix() now holds
      associative_recall._MATRIX_LOCK across the refresh and hands back a consistent SNAPSHOT of the cache, so a refresh
      on another thread can never be seen half applied (M from one build, imp/age/walled from another) nor race on the tmp.
    - memory_edges.log_co_recall: already whole-call serialised by _CO_RECALL_LOCK (J-1909).
    - memory_service._pending_usage: a module dict keyed by loop name; 'curiosity' is written only by this ask and popped by
      note_usage on the loop thread AFTER the awaited ask has returned; single-key dict assignment is atomic.
    - data/memory_service_shadow.jsonl appended by _log_ride (worker) and note_usage / other asks (loop): memory_service.
      _SHADOW_LOCK now serialises the appends.
    - memory_levels.deep_recall: one per-call connection, no module state.
No ContextVar / threading.local exists in core/ or nodes/, so asyncio.to_thread's context copy loses nothing.

IDLE_LOOKUPS_OFFLOOP is the kill switch: False makes off_loop() the plain synchronous call on the caller's thread,
exactly the pre-J-1918 behaviour."""
from __future__ import annotations

import asyncio

IDLE_LOOKUPS_OFFLOOP = True     # kill-switch: False = run the call synchronously on the loop thread (old behaviour)


async def off_loop(fn, *args, **kw):
    """Await fn(*args, **kw) in a worker thread (or call it inline when the kill switch is off)."""
    if not IDLE_LOOKUPS_OFFLOOP:
        return fn(*args, **kw)
    return await asyncio.to_thread(fn, *args, **kw)

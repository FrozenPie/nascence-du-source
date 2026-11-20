"""scripts/lab_j2029_hub_replica.py (J-2029, 2026-10-09) -- faithful in-process replica of the :11439 hub.

Imports scripts/nascence_cpu_server.py UNMODIFIED and drives its FastAPI app (/api/chat) through httpx's
ASGITransport: NO network port, NO launched server. This reproduces the three differences J-1752 named:
 (a) create_chat_completion is called from run_in_executor under asyncio (the hub's own code path, not ours);
 (b) the process is long-lived and cycles load/unload (the hub's idle-unload body, replicated verbatim by
     unload_like_hub() -- _old.close() guarded, del, gc.collect());
 (c) no seed is ever set (the hub passes only temperature/top_p/max_tokens).
Run ONLY while Du is down and the :11439 hub is idle/unloaded (needs ~9 GB RAM, 14 threads of CPU).

  python scripts/lab_j2029_hub_replica.py --variant baseline|reset|clear|seed|sampler --plan "sh16,tw20,tw20,tw18,CYCLE,sh16,..." [--dry] [--stub]
  plan tokens: tw<N> / sh<N> = twain / shackleton rows[:N] (as scripts/lab_j1752_inproc_llama.py); CYCLE = unload + reload.
  variants wrap llm.create_chat_completion inside the replica process (hub script untouched):
    reset   : llm.reset() before each request
    clear   : llm.reset() + llm._ctx.kv_cache_clear() before each request
    seed    : explicit seed=<fresh per call> kwarg
    sampler : top_k=40, min_p=0.05 kwargs
  --stub : replace llama_cpp.Llama with a fake (no model, no RAM) to validate the plumbing and the load/unload cycle.
  --dry  : build prompts only.
Output: $J2029_OUT/replica_results.jsonl (default: <tree>/docs/lab/j2029_data). Never writes under data/.
Degenerate = core.peers._non_latin_letter_ratio(text) > core.peers._DEGENERATE_NON_LATIN_RATIO.
"""
import argparse, asyncio, gc, importlib.util, json, os, sys, time, random
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
TREE = Path(__file__).resolve().parent.parent          # the tree under test (core is imported from here)
DATA = Path(r"C:\Nascence")                             # read-only: correspondence threads
sys.path[:0] = [r"C:\Users\USER\.claude\skills\job-queue", str(TREE)]
ap = argparse.ArgumentParser()
ap.add_argument("--variant", default="baseline", choices=["baseline", "reset", "clear", "seed", "sampler"])
ap.add_argument("--plan", required=True)
ap.add_argument("--model", default=r"C:\Users\USER\.ollama\models\blobs\sha256-1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606")
ap.add_argument("--dry", action="store_true")
ap.add_argument("--stub", action="store_true")
ap.add_argument("--max-calls", type=int, default=40)
a = ap.parse_args()
OUT = Path(os.environ.get("J2029_OUT", str(TREE / "docs" / "lab" / "j2029_data")))
OUT.mkdir(parents=True, exist_ok=True)
_live = (DATA / "data").resolve()
assert not str(OUT.resolve()).startswith(str(_live)) or "lab" in OUT.resolve().parts, "refusing to write under live data/"
from core import telemetry          # core BEFORE lab_env
telemetry.enter_lab_mode()
from lab_env import isolate
import core
assert str(Path(core.__file__).resolve()).startswith(str(TREE)), core.__file__
DU_CTX = "He lives alone in a cottage with a garden on a hill above the sea, and reads very widely."


def rows(persona):
    p = DATA / "data" / "Correspondence" / persona / "thread.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


class FakeLlama:                      # --stub: no model; exercises load/unload + executor path
    loads = 0

    def __init__(self, **kw):
        FakeLlama.loads += 1; self.kw = kw; self.n_tokens = 0; self._ctx = self; self.closed = False

    def reset(self): self.n_tokens = 0
    def kv_cache_clear(self): pass
    def close(self): self.closed = True

    def create_chat_completion(self, messages, **kw):
        self.n_tokens += 1
        return {"choices": [{"message": {"content": f"stub reply {self.n_tokens} kw={sorted(kw)}"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1}}


def load_hub():
    spec = importlib.util.spec_from_file_location("nascence_cpu_server_replica", str(TREE / "scripts" / "nascence_cpu_server.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m          # pydantic resolves the module's postponed annotations through sys.modules
    spec.loader.exec_module(m)
    if a.stub:
        m.Llama = FakeLlama
    m._ARGS = argparse.Namespace(model=a.model, ctx=8192, threads=14, gpu_layers=0, cuda_device=None,
                                 idle_unload=300, lazy=True)
    m.ALIAS = "gemma4:12b"
    return m


def unload_like_hub(m):
    """Verbatim body of nascence_cpu_server._idle_unloader's unload step (inline in a while-loop, not callable)."""
    _old, m.llm = m.llm, None
    try:
        _old.close()
    except Exception as exc:
        print(f"teardown warning (non-fatal): {exc}")
    del _old
    gc.collect()


def install_variant(m):
    """Wrap the loaded llm's create_chat_completion per variant (re-applied after every (re)load)."""
    llm = m.llm
    if getattr(llm, "_j2029_wrapped", False) or a.variant == "baseline":
        return
    orig = llm.create_chat_completion

    def wrapped(messages, **kw):
        if a.variant in ("reset", "clear"):
            llm.reset()
            if a.variant == "clear":
                llm._ctx.kv_cache_clear()
        elif a.variant == "seed":
            kw["seed"] = random.randrange(1, 2 ** 31)
        elif a.variant == "sampler":
            kw["top_k"] = 40; kw["min_p"] = 0.05
        return orig(messages=messages, **kw)
    llm.create_chat_completion = wrapped
    llm._j2029_wrapped = True


async def main():
    import httpx
    ALL = {"twain": rows("twain"), "shackleton": rows("shackleton")}
    with isolate(db="empty"):
        from core import peers
        steps = []
        for tok in a.plan.split(","):
            if tok == "CYCLE":
                steps.append(("CYCLE", None, None)); continue
            persona = {"tw": "twain", "sh": "shackleton"}[tok[:2]]; n = int(tok[2:]); r = ALL[persona][:n]
            peers._read_thread = lambda p, _r=r: list(_r)
            thread = peers._thread_context(persona)
            reply_to = r[-1]["text"] if r and r[-1].get("from") == "du" else ""
            steps.append((tok, peers.PERSONAS[persona]["system"], peers._build_user(thread, DU_CTX, reply_to, None)))
        ncalls = sum(1 for s in steps if s[0] != "CYCLE")
        if a.dry:
            for t, s, u in steps:
                print("DRY", t, len(s or ""), len(u or ""))
            print("model calls:", ncalls); return
        assert ncalls <= a.max_calls, f"plan has {ncalls} calls > cap {a.max_calls}"
        m = load_hub()
        transport = httpx.ASGITransport(app=m.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://replica", timeout=None) as client:
            i = 0; since_load = 0; loads = 0
            for tok, s, u in steps:
                if tok == "CYCLE":
                    if m.llm is not None:
                        unload_like_hub(m)
                    since_load = 0; print("CYCLE: unloaded", flush=True); continue
                i += 1
                if m.llm is None:                       # load exactly as the hub does (in executor), then wrap
                    await asyncio.get_event_loop().run_in_executor(None, m._ensure_loaded); loads += 1
                install_variant(m)
                t1 = time.time()
                r = await client.post("/api/chat", json={"model": "gemma4:12b", "stream": False,
                        "messages": [{"role": "system", "content": s}, {"role": "user", "content": u}],
                        "options": {"temperature": 0.85, "top_p": 0.9, "num_predict": 1600}})
                r.raise_for_status()
                j = r.json(); text = (j["message"]["content"] or "").strip()
                ratio = peers._non_latin_letter_ratio(text)
                since_load += 1
                rec = {"variant": a.variant, "i": i, "tok": tok, "pos_since_load": since_load, "loads": loads,
                       "latency_s": round(time.time() - t1, 1), "chars": len(text), "ratio": round(ratio, 4),
                       "degenerate": bool(ratio > peers._DEGENERATE_NON_LATIN_RATIO), "head": text[:100],
                       "completion_tokens": j.get("eval_count"), "prompt_tokens": j.get("prompt_eval_count"),
                       "stub": a.stub, "t": time.time()}
                print(json.dumps(rec, ensure_ascii=False), flush=True)
                with open(OUT / ("replica_stub_results.jsonl" if a.stub else "replica_results.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if m.llm is not None:
            unload_like_hub(m)

asyncio.run(main())

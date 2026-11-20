"""scripts/lab_j1752_inproc_llama.py (J-1752, 2026-10-08) -- in-process llama_cpp.Llama on the SAME GGUF as the :11439 hub, to test
mitigation variants of the warm degenerate-generation hazard WITHOUT touching the hub. Run ONLY while the hub is idle/unloaded
(it competes for CPU and ~9 GB RAM). Never writes to data/ (outputs to J1752_OUT, default temp dir).

  python scripts/lab_j1752_inproc_llama.py --variant baseline|reset|clear --plan "tw20,tw20,tw18" [--model PATH] [--dry]
  plan tokens: tw<N> / sh<N> = twain / shackleton rows[:N]  (same prompt construction as scripts/lab_j1668_hub_cold_warm_probe.py)
  baseline : create_chat_completion exactly as the hub does (temperature .85, top_p .9, max_tokens 1600)
  reset    : llm.reset() before each request (disables llama-cpp-python's prefix-match KV reuse; n_tokens=0)
  clear    : llm.reset() + llm._ctx.kv_cache_clear() before each request
Degenerate = core.peers._non_latin_letter_ratio(text) > core.peers._DEGENERATE_NON_LATIN_RATIO.
"""
import argparse, json, os, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Nascence")
sys.path[:0] = [r"C:\Users\USER\.claude\skills\job-queue", str(ROOT)]
ap = argparse.ArgumentParser()
ap.add_argument("--variant", default="baseline", choices=["baseline", "reset", "clear"])
ap.add_argument("--plan", required=True)
ap.add_argument("--model", default=r"C:\Users\USER\.ollama\models\blobs\sha256-1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()
OUT = Path(os.environ.get("J1752_OUT", str(Path(tempfile.gettempdir()) / "j1752_inproc"))); OUT.mkdir(parents=True, exist_ok=True)
from core import telemetry
telemetry.enter_lab_mode()
from lab_env import isolate
import core
assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
DU_CTX = "He lives alone in a cottage with a garden on a hill above the sea, and reads very widely."
def rows(persona):
    p = ROOT / "data" / "Correspondence" / persona / "thread.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
ALL = {"twain": rows("twain"), "shackleton": rows("shackleton")}
with isolate(db="empty"):
    from core import peers
    prompts = []
    for tok in a.plan.split(","):
        persona = {"tw": "twain", "sh": "shackleton"}[tok[:2]]; n = int(tok[2:])
        r = ALL[persona][:n]
        peers._read_thread = lambda p, _r=r: list(_r)
        thread = peers._thread_context(persona)
        reply_to = r[-1]["text"] if r and r[-1].get("from") == "du" else ""
        prompts.append((tok, peers.PERSONAS[persona]["system"], peers._build_user(thread, DU_CTX, reply_to, None)))
    if a.dry:
        for t, s, u in prompts: print("DRY", t, len(s), len(u))
        sys.exit(0)
    from llama_cpp import Llama
    t0 = time.time()
    llm = Llama(model_path=a.model, n_ctx=8192, n_threads=14, n_gpu_layers=0, verbose=False)
    print(f"loaded in {time.time()-t0:.0f}s variant={a.variant}", flush=True)
    for i, (tok, s, u) in enumerate(prompts, 1):
        if a.variant in ("reset", "clear"):
            llm.reset()
            if a.variant == "clear":
                llm._ctx.kv_cache_clear()
        t1 = time.time()
        resp = llm.create_chat_completion(messages=[{"role": "system", "content": s}, {"role": "user", "content": u}],
                                          temperature=0.85, top_p=0.9, max_tokens=1600)
        text = (resp["choices"][0]["message"]["content"] or "").strip()
        ratio = peers._non_latin_letter_ratio(text)
        rec = {"variant": a.variant, "i": i, "tok": tok, "latency_s": round(time.time() - t1, 1), "chars": len(text),
               "ratio": round(ratio, 4), "degenerate": bool(ratio > peers._DEGENERATE_NON_LATIN_RATIO), "head": text[:100],
               "completion_tokens": resp.get("usage", {}).get("completion_tokens"), "t": time.time()}
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        with open(OUT / "inproc_results.jsonl", "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")

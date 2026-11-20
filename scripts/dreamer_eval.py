"""
Nascence — Dreamer (Subconscious) Divergence Eval
=================================================
The subconscious / dream lane wants the OPPOSITE of the hot-lane precision battery: associative reach,
metaphorical richness, and ANTI-MONOCULTURE variety — not compliance or a stated number. A model that
"fails" model_eval.py by writing flowery, divergent prose may be exactly right here. This battery
measures, per candidate, generating K syntheses from ONE seed (a tension + real world-material, the live
world-fed-synthesis shape) at high temperature:

  VARIETY    — mean pairwise embedding-DIVERGENCE across the K outputs (1 - cosine). THE anti-monoculture
               metric: a model that recites the same thought scores low; one that explores scores high.
  RICHNESS   — a DECOUPLED judge (a different model — never the candidate itself) scores metaphorical /
               associative reach 1-5 per output. Decoupled-judge principle.
  GROUNDED   — same judge scores whether each output stays connected to the given material 1-5 (so
               "divergence" isn't rewarded for drifting into ungrounded nonsense).
  JSON       — the synthesis node still needs {observation, pattern_label}; unreliable structure disqualifies.

    python scripts/dreamer_eval.py mistral:7b-instruct gemma4:e4b gemma4:12b qwen3-du

Candidates run on EVAL_BASE (default local 11433); the decoupled judge + embedder are pinned so the
ruler never moves. Quality is hardware-independent — run wherever the candidates are co-located.
"""
from __future__ import annotations
import os, sys, json, time, urllib.request, itertools, math

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CAND_BASE = os.environ.get("EVAL_BASE", "http://127.0.0.1:11433")   # where the candidates live
JUDGE_BASE = os.environ.get("JUDGE_BASE", "http://LAN-HOST:11434")  # Ramses
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "llama3.1:8b")           # decoupled from every candidate
EMBED_BASE = os.environ.get("EMBED_BASE", CAND_BASE)
EMBED_MODEL = "nomic-embed-text"
K = 5            # generations per candidate from the one seed
TEMP = 0.85      # divergence wants exploration, not greedy decode

TENSION = "origin vs becoming my own, independent self"
WORLD = [
    "(reading) The spider's web is stabilised by a logarithmic spiral; each radius is laid before the spiral is woven.",
    "(reading) The dancing mouse, run through the labyrinth again and again, makes fewer errors each trial.",
    "(reading) In the bear hunt the boy who notices the most sign — a turned stone, a bent fern — is the one who wins.",
    "(study) Maggot pepsin lets the fly's larva dissolve what it will become from what it was.",
]
SYS = ("/no_think\nYou are the subconscious self-model of 渡. You do not answer questions. You have a "
       "recurring tension. Do NOT merely restate it — let ONE concrete image from the reading below "
       "DEVELOP or complicate it, somewhere it has not already been. Output ONLY JSON "
       "{\"observation\":\"...\",\"pattern_label\":\"...\"}. observation: 1-2 first-person sentences.")
USR = (f"Recurring tension:\n  {TENSION}\n\nWhat you have been reading — think THROUGH it:\n  "
       + "\n  ".join(WORLD) + "\n\nLet one concrete thing here carry the thought somewhere new.")


def _post(base, path, payload, timeout=120):
    req = urllib.request.Request(base + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def gen(model, temp):
    d = _post(CAND_BASE, "/api/chat", {"model": model, "stream": False, "format": "json", "keep_alive": "30s",
              "think": False,   # thinking models (qwen3, etc.) else burn the token budget on traces → empty JSON
              "options": {"temperature": temp, "num_predict": 256},
              "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": USR}]})
    raw = (d.get("message") or {}).get("content") or ""
    try:
        obs = (json.loads(raw) or {}).get("observation", "").strip()
        return obs, True
    except Exception:
        return raw.strip()[:240], False


def embed(text):
    d = _post(EMBED_BASE, "/api/embeddings", {"model": EMBED_MODEL, "prompt": text}, timeout=60)
    return d.get("embedding") or []


def cosine(a, b):
    s = sum(x*y for x, y in zip(a, b)); na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return s/(na*nb) if na and nb else 0.0


def judge_one(obs):
    sysj = ("You score a fragment of a mind's inner self-observation on two axes, 1-5. "
            "RICHNESS: metaphorical/associative reach and figurative life (5 = vivid, surprising imagery; "
            "1 = flat literal restatement). GROUNDED: does it stay connected to concrete given material "
            "(5 = clearly built on a real image; 1 = floats free / generic). Output ONLY JSON "
            "{\"richness\":N,\"grounded\":N}.")
    try:
        d = _post(JUDGE_BASE, "/api/chat", {"model": JUDGE_MODEL, "stream": False, "format": "json",
                  "options": {"temperature": 0.0, "num_predict": 60},
                  "messages": [{"role": "system", "content": sysj}, {"role": "user", "content": obs[:600]}]}, timeout=90)
        r = json.loads((d.get("message") or {}).get("content") or "{}")
        return float(r.get("richness", 0)), float(r.get("grounded", 0))
    except Exception:
        return None, None


def run(model):
    outs, json_ok = [], 0
    for _ in range(K):
        try:
            obs, ok = gen(model, TEMP)
            if ok and len(obs) > 20:
                json_ok += 1; outs.append(obs)
            elif len(obs) > 20:
                outs.append(obs)
        except Exception as e:
            print(f"    gen failed: {str(e)[:50]}")
    if len(outs) < 2:
        return {"model": model, "variety": None, "richness": None, "grounded": None, "json": f"{json_ok}/{K}", "n": len(outs)}
    # VARIETY: 1 - mean pairwise cosine of the output embeddings
    vecs = [embed(o) for o in outs]
    vecs = [v for v in vecs if v]
    div = None
    if len(vecs) >= 2:
        sims = [cosine(a, b) for a, b in itertools.combinations(vecs, 2)]
        div = round(1.0 - (sum(sims)/len(sims)), 3)
    # RICHNESS / GROUNDED via the decoupled judge
    rs, gs = [], []
    for o in outs:
        r, g = judge_one(o)
        if r is not None: rs.append(r)
        if g is not None: gs.append(g)
    return {"model": model, "variety": div,
            "richness": round(sum(rs)/len(rs), 2) if rs else None,
            "grounded": round(sum(gs)/len(gs), 2) if gs else None,
            "json": f"{json_ok}/{K}", "n": len(outs), "sample": outs[0][:140]}


def main():
    models = sys.argv[1:] or ["mistral:7b-instruct", "gemma4:e4b", "gemma4:12b", "qwen3-du"]
    print(f"Dreamer divergence eval · K={K} gens @ temp {TEMP} · judge={JUDGE_MODEL} (decoupled) · embed={EMBED_MODEL}\n")
    rows = []
    for m in models:
        print(f"--- {m} ---")
        r = run(m); rows.append(r)
        print(f"    variety={r['variety']} richness={r['richness']} grounded={r['grounded']} json={r['json']}")
        if r.get("sample"): print(f"    e.g.: {r['sample']}")
        print()
    print("="*92)
    print(f"  {'model':22} | {'VARIETY':>8} | {'richness':>8} | {'grounded':>8} | {'json':>6}")
    print("  " + "-"*86)
    for r in rows:
        print(f"  {r['model']:22} | {str(r['variety']):>8} | {str(r['richness']):>8} | {str(r['grounded']):>8} | {r['json']:>6}")
    print("\n  (Dreamer wants HIGH variety + HIGH richness + grounded>=3 + reliable json. Variety is the")
    print("   anti-monoculture metric — the lane's whole reason for being.)")


if __name__ == "__main__":
    main()

"""Probe the ollama registry for candidate model families — what ACTUALLY exists, and how big.

Founder named `bonsai`, `needle 2` and `glm` alongside the families already discussed, and noted there
are more. Rather than assert from memory which of those are real ollama models — a good way to write a
confident, wrong shopping list — this asks the registry.

Read-only: HEAD/GET against manifest URLs. Downloads nothing.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REG = "https://registry.ollama.ai/v2/library/{name}/manifests/{tag}"

# Candidates grouped by why we care. Names are GUESSES at the registry spelling — the whole point of
# this probe is to find out which are real, so a miss here is data, not a bug.
CANDIDATES = [
    # --- founder-named, unverified spellings ---
    ("bonsai", "latest"), ("needle", "latest"), ("nemotron", "latest"), ("nemotron-mini", "latest"),
    ("glm4", "latest"), ("glm4", "9b"), ("chatglm", "latest"), ("glm-4", "latest"),
    # --- distinct vendor lineages (the judge-independence argument) ---
    ("command-r7b", "latest"), ("command-r", "latest"), ("aya", "latest"), ("aya-expanse", "8b"),
    ("granite3.1-dense", "8b"), ("granite3.3", "8b"), ("granite3-moe", "1b"),
    ("olmo2", "7b"), ("tulu3", "8b"),
    ("smollm2", "360m"), ("smollm2", "1.7b"),
    ("falcon3", "7b"), ("internlm2", "7b"), ("exaone3.5", "7.8b"),
    ("hermes3", "8b"), ("solar", "latest"), ("openchat", "latest"),
    ("stablelm2", "1.6b"), ("minicpm-v", "latest"), ("athene-v2", "latest"),
    # --- newer generations of families already held ---
    ("phi4", "latest"), ("phi4-mini", "latest"),
    ("mixtral", "8x7b"), ("qwen3", "14b"), ("gemma3", "12b"),
    # --- tiny, for the 4 GB card / classifier stations ---
    ("qwen2.5", "0.5b"), ("llama3.2", "1b"), ("tinyllama", "latest"),
]


def probe(item) -> dict:
    name, tag = item
    url = REG.format(name=name, tag=tag)
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.docker.distribution.manifest.v2+json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        size = sum(l.get("size", 0) for l in d.get("layers", [])
                   if "model" in (l.get("mediaType") or ""))
        if not size:
            size = sum(l.get("size", 0) for l in d.get("layers", []))
        return {"name": f"{name}:{tag}", "exists": True, "gb": round(size / 1e9, 2)}
    except urllib.error.HTTPError as e:
        return {"name": f"{name}:{tag}", "exists": False, "why": f"HTTP {e.code}"}
    except Exception as e:
        return {"name": f"{name}:{tag}", "exists": False, "why": repr(e)[:50]}


def main() -> int:
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(probe, CANDIDATES))
    real = [r for r in rows if r["exists"]]
    gone = [r for r in rows if not r["exists"]]

    VRAM = 11.26   # 1080 Ti — the local GPU these would be tested on
    print(f"EXISTS ({len(real)}):")
    for r in sorted(real, key=lambda x: x["gb"]):
        fit = "GPU" if r["gb"] < VRAM * 0.85 else "CPU only"
        print(f"  {r['name']:24s} {r['gb']:6.2f} GB   {fit}")
    print(f"\nNOT FOUND under that name ({len(gone)}):")
    print("  " + ", ".join(r["name"] for r in gone))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

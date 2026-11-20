"""Resolve an ollama model tag to its GGUF blob path (blobs ARE GGUFs — verified 2026-08-15).
Usage: python resolve_blob.py llama3.1 8b   -> prints the absolute blob path (exit 1 if missing).
Used by launch_servers.ps1 so the CPU tier survives model re-pulls (digests change)."""
import json
import os
import sys

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding="utf-8")

name, tag = sys.argv[1], sys.argv[2]
# OLLAMA_MODELS honoured (2026-08-20): the default ~/.ollama/models is right on this machine, but
# this resolver is being ported to RAMSES, whose store holds 20 models including three 18 GB ones
# and may well live off the system drive. Reading the env var first makes the port a copy rather
# than a fork; falling back keeps local behaviour identical.
base = os.environ.get("OLLAMA_MODELS") or os.path.expanduser("~/.ollama/models")
manifest = f"{base}/manifests/registry.ollama.ai/library/{name}/{tag}"

# PREFIX FALLBACK (2026-08-23, merged back from Ramses — needed to resolve mixtral:8x7b at all):
# some ollama tags don't have a manifest file matching the plain requested tag exactly — the real
# file on disk can be a fuller name like "8x7b-instruct-v0.1-q2_K". If the exact path is missing,
# fall back to the first manifest-folder entry starting with the requested tag. Narrow risk: if
# more than one pulled variant shares that prefix, this takes whichever the filesystem lists first
# (not necessarily deterministic) rather than a specific one — acceptable because pulling two
# quantizations of the same tag deliberately is not the normal case, but worth knowing about.
if not os.path.exists(manifest):
    model_dir = f"{base}/manifests/registry.ollama.ai/library/{name}"
    if os.path.isdir(model_dir):
        matches = [f for f in os.listdir(model_dir) if f.startswith(tag)]
        if matches:
            manifest = os.path.join(model_dir, matches[0])

try:
    m = json.load(open(manifest, encoding="utf-8"))
    for layer in m.get("layers", []):
        if "model" in layer.get("mediaType", ""):
            p = os.path.normpath(base + "/blobs/" + layer["digest"].replace(":", "-"))
            if open(p, "rb").read(4) == b"GGUF":
                print(p)
                sys.exit(0)
    print(f"no GGUF model layer in {manifest}", file=sys.stderr)
except Exception as exc:
    print(f"resolve failed for {name}:{tag} — {exc}", file=sys.stderr)
sys.exit(1)

"""
HUD2 data contract builder — the BRAIN GRAPH manifest (docs/plans/hud2_visual.md Phase 1, 2026-08-21).

Generates data/hud2/brain_graph.json: the machine-readable map an EXTERNAL visualizer (Antigravity's
new HUD) needs to render Du's organs as a live graph — WITHOUT knowing anything about this codebase.

Contract (the whole deal, so the two projects stay decoupled):
 - Claude/Nascence side OWNS this script and the manifest it emits. Re-run after structural changes.
 - The external HUD READS the manifest + the log files it names. It never writes, never imports
   Nascence code, never guesses schemas: every log entry here carries its ts_key, verified by
   sampling the real file.
 - "An organ FIRED" = one of its logs grew (st_size increased). Poll sizes; read appended lines for
   detail using ts_key. That's the entire live protocol — no daemon, no socket, no coupling.

What it builds:
 - nodes: one per python module in core/, core/memory/, nodes/ — with label (docstring first line),
   group (subsystem folder), loc (lines of code), and its LOGS (data files it writes, discovered by
   scanning source for data-file string literals, then verified on disk with their real ts_key).
 - edges: import relationships (AST walk — catches this codebase's dominant lazy `from core import x`
   inside functions, not just top-of-file imports).

Zero LLM, read-only over source + data. Deterministic. Run: python scripts/build_hud2_manifest.py
"""
import ast
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUT = DATA / "hud2"

SCAN_DIRS = [("core", ROOT / "core"), ("memory", ROOT / "core" / "memory"),
             ("nodes", ROOT / "nodes")]
# data-file literals in source: "name.jsonl" / "name.json" (log/state files an organ writes)
_FILE_RE = re.compile(r'"([A-Za-z0-9_./-]+\.jsonl?)"')
# where log files actually live
_LOG_DIRS = [DATA, DATA / "logs", DATA / "lab", DATA / "identity", DATA / "music",
             DATA / "training", DATA / "forge"]


def _module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    return ".".join(rel.parts)


def _find_log(fname: str) -> Path | None:
    fname = fname.split("/")[-1]
    for d in _LOG_DIRS:
        p = d / fname
        if p.exists() and p.is_file():
            return p
    return None


def _ts_key(path: Path) -> str | None:
    """Sample the file's LAST parseable json line and report which timestamp key it uses."""
    try:
        if path.suffix == ".json":
            return None
        with open(path, "rb") as f:
            f.seek(max(0, path.stat().st_size - 20000))
            tail = f.read().decode("utf-8", errors="ignore").strip().splitlines()
        for line in reversed(tail):
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                for k in ("ts", "timestamp", "time", "created"):
                    if isinstance(row.get(k), (int, float)):
                        return k
                return "NONE"
        return None
    except Exception:
        return None


def build() -> dict:
    nodes, edges = [], []
    known_modules: set[str] = set()
    py_files: list[tuple[str, Path]] = []
    for group, d in SCAN_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.glob("*.py")):
            if p.name == "__init__.py":
                continue
            py_files.append((group, p))
            known_modules.add(_module_name(p))

    for group, p in py_files:
        mod = _module_name(p)
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # label: docstring first meaningful line
        label = p.stem.replace("_", " ")
        try:
            tree = ast.parse(src)
            doc = ast.get_docstring(tree) or ""
            for line in doc.splitlines():
                line = line.strip().strip("=- ")
                if len(line) > 8:
                    label = line[:110]
                    break
        except Exception:
            tree = None
        # logs this module writes (string-literal scan, verified on disk)
        logs = []
        seen_files = set()
        for m in _FILE_RE.finditer(src):
            fp = _find_log(m.group(1))
            if fp and fp.name not in seen_files:
                seen_files.add(fp.name)
                logs.append({"path": str(fp.relative_to(ROOT)).replace("\\", "/"),
                             # events = append-only jsonl (read appended lines for detail);
                             # state = whole-file json snapshot (re-read on mtime change)
                             "kind": "events" if fp.suffix == ".jsonl" else "state",
                             "ts_key": _ts_key(fp),
                             "size": fp.stat().st_size,
                             "mtime": round(fp.stat().st_mtime, 1)})
        nodes.append({"id": mod, "file": str(p.relative_to(ROOT)).replace("\\", "/"),
                      "group": group, "label": label,
                      "loc": src.count("\n") + 1, "logs": logs})
        # edges: every import of a known module, anywhere in the tree (lazy imports included)
        if tree is not None:
            targets = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and n.module:
                    base = n.module
                    for alias in n.names:
                        cand = f"{base}.{alias.name}"
                        if cand in known_modules:
                            targets.add(cand)
                    if base in known_modules:
                        targets.add(base)
                elif isinstance(n, ast.Import):
                    for alias in n.names:
                        if alias.name in known_modules:
                            targets.add(alias.name)
            for t in sorted(targets):
                if t != mod:
                    edges.append({"src": mod, "dst": t})

    return {"generated": round(time.time(), 1),
            "generated_human": time.strftime("%Y-%m-%d %H:%M"),
            "schema": 1,
            "protocol": {
                "fired": "an organ fired when any of its logs' size grew; poll sizes (~1s is fine)",
                "detail": "read appended bytes; each line is one JSON event; use the log's ts_key",
                "readonly": "this manifest + the named files are the ENTIRE interface; never write",
            },
            "nodes": nodes, "edges": edges}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    g = build()
    out = OUT / "brain_graph.json"
    out.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    n_logs = sum(len(n["logs"]) for n in g["nodes"])
    with_logs = sum(1 for n in g["nodes"] if n["logs"])
    print(f"brain_graph.json: {len(g['nodes'])} nodes · {len(g['edges'])} edges · "
          f"{with_logs} nodes with logs ({n_logs} log files) → {out}")

"""
Nascence — graphify Code-Health Check (2026-08-18).

Born from a graphify audit that fixed the graph's two biggest reliability bugs (self.-call resolution +
125 ghost-duplicate nodes — see docs/graphify_notes.md) and then, while tracing one AMBIGUOUS semantic edge
by hand, caught a real bug: core/world_traces.py silently re-deriving its own copy of weather logic that
core/weather_conditions.py already owned. This script turns that manual process into a repeatable one,
using graphify-out/graph.json as a lens on three things —

  1. DEAD/ORPHANED CODE — core/nodes symbols with zero graph edges at all.
  2. CANONICAL-MODULE DRIFT — code that looks conceptually related to a module that already declares
     itself the "single source of truth" for something, but doesn't actually import it. This is exactly
     the weather_conditions/world_traces pattern, generalized.
  3. ARCHITECTURE RULES — a scaffold, deliberately empty for now. No project-wide rules document exists
     anywhere in this repo (checked); the one candidate found (core/world_objects.py's own "Architectural
     Contract v1.4", 3 named invariants) is narrative, not yet phrased as something checkable without
     guessing. Add rules to RULES below once a check's exact condition is pinned down with the founder —
     encoding a guess here risks noisy false flags, which is worse than no check at all.

The graph's degree signal is now far more trustworthy than it was before today's fixes (core/nodes
singleton count went 24 -> 4, all 4 legitimate) — but it is NOT proof by itself. This script never reports
a finding on graph signal alone: every candidate is grep-verified against the real source before it's
printed. That discipline is what caught 7/7 false positives by hand this session (self.-calls, subprocess
launches like scripts/gutenberg.py, and a residual ghost node — core/schema.py's SERVE_CHAINS still has an
unmerged semantic-layer duplicate even after today's dedup pass, found while writing this script; grep
correctly suppresses it since the real SERVE_CHAINS is used in 22 files).

Verdicts are advisory, not gates — same convention as scripts/world_grounding_audit.py, which this script
deliberately matches in style. Run it any time after a graphify rebuild (see docs/graphify_notes.md).
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
GRAPH = ROOT / "graphify-out" / "graph.json"
CODE_DIRS = ("core", "nodes", "scripts")

# Whole-file nodes never count as "dead code" candidates on their own (a lightly-touched leaf script isn't
# a bug), and blank __init__.py files are supposed to have nothing worth calling.
EXEMPT_FILES = {"__init__.py"}

# Modules that explicitly declare themselves the canonical/shared source of truth for something, in their
# own docstrings (found via a full-repo scan, 2026-08-18). Add more here as new modules earn the same claim.
CANONICAL_MODULES = [
    "core/weather_conditions.py",
    "core/affordances.py",
    "core/mood.py",
    "core/schema.py",
    "core/world_objects.py",
    "core/contradiction_gate.py",
    "core/listening.py",
    "core/epistemic_state.py",
]

# Architecture rules — deliberately empty. See module docstring, section 3.
RULES: list[tuple[str, str, "callable"]] = []


def _load_graph() -> dict:
    if not GRAPH.exists():
        print(f"error: no graph found at {GRAPH} — run /graphify first", file=sys.stderr)
        sys.exit(1)
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def _degree_map(g: dict) -> dict:
    deg: dict[str, int] = {}
    for e in g.get("links") or g.get("edges") or []:
        deg[e["source"]] = deg.get(e["source"], 0) + 1
        deg[e["target"]] = deg.get(e["target"], 0) + 1
    return deg


def _read_code_files() -> dict[str, str]:
    """Every .py under core/, nodes/, scripts/ — read once, reused by both checks below."""
    cache = {}
    for d in CODE_DIRS:
        for p in (ROOT / d).rglob("*.py"):
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            try:
                cache[rel] = p.read_text(encoding="utf-8")
            except Exception:
                continue
    return cache


_UPPER_TOKEN = re.compile(r"[A-Z][A-Z0-9_]{2,}")


def _extract_symbol_name(label: str) -> str | None:
    """Best-effort identifier extraction from a graph node's label, for grep-verification. Handles
    'method()', '.method()', 'ClassName.method()', and descriptive constant labels like
    'INTEGRATION_ETHIC prompt contract' (falls back to the first ALL_CAPS token). Returns None when
    nothing groundable can be extracted — such nodes are skipped rather than risk a bad grep."""
    s = label.strip()
    if s.endswith("()"):
        s = s[:-2]
        return s.rsplit(".", 1)[-1] if "." in s else s
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", s):
        return s.rsplit(".", 1)[-1] if "." in s else s
    m = _UPPER_TOKEN.search(s)
    return m.group(0) if m else None


def check_dead_code(g: dict, deg: dict, code_cache: dict[str, str]) -> list[str]:
    """core/nodes code symbols with ZERO graph edges, grep-verified against every .py file in the repo
    before being reported. Never trust degree alone — see module docstring."""
    hits = []
    for n in g["nodes"]:
        sf = (n.get("source_file") or "").replace("\\", "/")
        if not (sf.startswith("core/") or sf.startswith("nodes/")):
            continue
        if n.get("file_type") != "code":
            continue
        label = n.get("label", "")
        if label == Path(sf).name:                 # whole-file node — not a symbol-level finding
            continue
        if Path(sf).name in EXEMPT_FILES:
            continue
        if deg.get(n["id"], 0) != 0:
            continue
        sym = _extract_symbol_name(label)
        if not sym:
            continue                                 # nothing groundable to grep for — skip, don't guess
        rx = re.compile(r"\b" + re.escape(sym) + r"\b")
        used_elsewhere = any(
            path != sf and rx.search(content)
            for path, content in code_cache.items()
        )
        if not used_elsewhere:
            hits.append(f"{sf}: {label}  (id={n['id']}, 0 graph edges, grep found no use outside its own file)")
    return hits


def check_canonical_drift(g: dict, code_cache: dict[str, str]) -> list[str]:
    """For each self-declared canonical module, any AMBIGUOUS/INFERRED edge to a node in a DIFFERENT file
    that doesn't actually import the canonical module — the exact pattern that caught world_traces.py."""
    by_id = {n["id"]: n for n in g["nodes"]}
    file_node_id = {}
    for n in g["nodes"]:
        sf = (n.get("source_file") or "").replace("\\", "/")
        if sf in CANONICAL_MODULES and n.get("label") == Path(sf).name:
            file_node_id[sf] = n["id"]

    hits = []
    for module in CANONICAL_MODULES:
        nid = file_node_id.get(module)
        if not nid:
            hits.append(f"(could not find a graph node for {module} — skipped)")
            continue
        stem = Path(module).stem
        flagged_files = set()
        for e in g.get("links") or g.get("edges") or []:
            if e.get("confidence") not in ("AMBIGUOUS", "INFERRED"):
                continue
            s, t = e.get("source"), e.get("target")
            other = t if s == nid else (s if t == nid else None)
            if other is None:
                continue
            other_node = by_id.get(other)
            if not other_node:
                continue
            other_sf = (other_node.get("source_file") or "").replace("\\", "/")
            if not other_sf or other_sf == module or other_sf in flagged_files:
                continue
            content = code_cache.get(other_sf)
            if content is None:
                continue                             # not a code file we scanned (e.g. a doc) — skip
            if stem not in content:
                flagged_files.add(other_sf)
                hits.append(f"{other_sf} relates to {module} in the graph ({e.get('relation')}, "
                            f"{e.get('confidence')}) but does not import '{stem}'")
    return hits


def check_architecture_rules() -> list[str]:
    if not RULES:
        return ["(no rules configured yet — see module docstring, section 3)"]
    hits = []
    for name, _desc, fn in RULES:
        hits.extend(f"[{name}] {h}" for h in fn())
    return hits


def main():
    g = _load_graph()
    deg = _degree_map(g)
    code_cache = _read_code_files()

    print("=" * 78)
    print("GRAPHIFY CODE-HEALTH CHECK")
    print("=" * 78)

    print("\n[1] DEAD/ORPHANED CODE (core/, nodes/ — grep-verified, 0 graph edges AND 0 other references)")
    hits = check_dead_code(g, deg, code_cache)
    print(f"    {len(hits)} hit(s)" + (" — clean" if not hits else ""))
    for h in hits:
        print("    " + h)

    print("\n[2] CANONICAL-MODULE DRIFT (related to a shared module in the graph, but doesn't import it)")
    hits = check_canonical_drift(g, code_cache)
    print(f"    {len(hits)} hit(s)" + (" — clean" if not hits else ""))
    for h in hits:
        print("    " + h)

    print("\n[3] ARCHITECTURE RULES (scaffold — see module docstring, section 3)")
    for h in check_architecture_rules():
        print("    " + h)

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()

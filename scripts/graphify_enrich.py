"""
graphify_enrich.py — recover the edges graphify's tree-sitter AST misses on THIS project (2026-07-04,
extended 2026-08-18 for self-call resolution).

WHY (local imports): graphify resolves imports at MODULE level only. Nascence uses function-LOCAL (lazy)
imports everywhere (the fail-open discipline: `def f(): from core.x import y; ...`). So a call to a
locally-imported symbol never resolves to its cross-file target — e.g. `mineness._get_basin()` does
`from core.self_surprise import _basin_centroid` inside the function, and graphify drops both the
`imports_from` and the `calls` edge. This under-represents how connected the code really is (the
basin-centroid reuse spine was invisible).

WHY (self.-calls, added 2026-08-18): graphify's tree-sitter AST also never resolves `self.method()` (same
class) or `self.attr.method()` (an instance attribute assigned a project class in __init__/elsewhere) —
even same-FILE self-calls are invisible. Found via a graphify audit: EVERY orchestrator.py method checked
(`run_cycle`, `_thalamic_gate`, `_introspection_budget`, `_scene_unstable`, `_log_correlation`) showed as a
zero-edge orphan in the graph despite being genuinely called, same for `self.unified_gate.observe()` and
`self.symbol_tracker.observe()`. Since almost all cognition in this codebase runs through `self.` on
Orchestrator/nodes, this was a bigger blind spot than the local-import one. Two new resolutions:
  1. `self.method()` -> a same-class method in the SAME file (by call name, scanning the file's own
     AST-derived symbol nodes — not by recomputing an ID formula, see below).
  2. `self.attr.method()` -> resolved by tracking `self.attr = SomeClass(...)` assignments (using the same
     module/local import bindings already computed for #1's import-recovery), then finding `.method` on
     SomeClass's file.
Both resolve against a `(source_file, symbol_name) -> node_id` lookup built directly from the EXISTING
graph nodes, not from graphify's `make_id` formula — a same-run audit found graphify's own AST extractor can
assign two different id SCHEMES to same-basename files in different directories (a documented class of bug
in graphify itself, see `graphify.ids` module docstring: "#550 same-filename collisions"; this project hit
it on `core/stick_test.py` vs `scripts/stick_test.py` — the `core/` one got the bare id `stick_test` instead
of the usual `core_stick_test` pattern, silently breaking any enrichment that assumed the formula). Looking
up existing node IDs by their own `source_file`/label fields instead of recomputing them sidesteps that
whole bug class.

WHAT: an ADDITIVE post-processing pass. It does NOT touch the graphify package (survives upgrades). It parses
every project .py with Python's own `ast` (precise, flow-aware for locals), finds cross-project imports +
the calls they enable — module-level, function-local, and now self.-calls — and adds any missing
`imports_from`/`calls` edges to graphify-out/graph.json. An edge is added ONLY when BOTH endpoints already
exist as nodes (never invents a node, never an edge to nowhere — graphify's honesty rule). Re-runnable +
idempotent. Run after every `graphify --update`.

USAGE:  python scripts/graphify_enrich.py           # enrich graphify-out/graph.json in place
        python scripts/graphify_enrich.py --dry-run # report what it would add, change nothing
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")   # Windows charmap guard (house law)

ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "graphify-out" / "graph.json"
PKG_DIRS = ("core", "nodes", "scripts")     # the top-level import roots of this project

from graphify.ids import make_id            # noqa: E402  (single source of truth for node IDs)


def _file_stem(rel: Path) -> str:
    """graphify's file stem: {immediate_parent}.{filename} (or bare stem at root)."""
    parent = rel.parent.name
    return f"{parent}.{rel.stem}" if parent and parent not in (".", "") else rel.stem


def _file_id(rel: Path) -> str:
    return make_id(_file_stem(rel))


def _sym_id(rel: Path, *symbol_parts: str) -> str:
    return make_id(_file_stem(rel), *symbol_parts)


def _module_to_rel(dotted: str) -> Path | None:
    """Resolve a dotted import (core.self_surprise, nodes.inner_monologue_node, core.memory.store) to a
    project-relative .py path — only for the project's own packages; stdlib/3rd-party return None."""
    parts = dotted.split(".")
    if not parts or parts[0] not in PKG_DIRS:
        return None
    cand = ROOT.joinpath(*parts).with_suffix(".py")
    if cand.exists():
        return cand.relative_to(ROOT)
    pkg = ROOT.joinpath(*parts) / "__init__.py"     # a package import
    if pkg.exists():
        return pkg.relative_to(ROOT)
    return None


def _own_scope_nodes(fn: ast.AST):
    """Yield every node in fn's OWN scope, not descending into a nested def/class (separate scopes)."""
    for child in ast.iter_child_nodes(fn):
        stack = [child]
        while stack:
            node = stack.pop()
            yield node
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue          # a nested scope — its calls belong to ITS own pass
            stack.extend(ast.iter_child_nodes(node))


def _local_imports(fn: ast.AST) -> list[ast.stmt]:
    """Import statements in fn's OWN scope only — a scoped walk that does not descend into a nested
    def/class (those bind in their own separate scopes and get their own pass)."""
    class _V(ast.NodeVisitor):
        def __init__(self):
            self.imports = []
        def visit_FunctionDef(self, n):
            if n is fn:                       # only recurse into THIS function, not nested ones
                self.generic_visit(n)
        visit_AsyncFunctionDef = visit_FunctionDef
        def visit_ClassDef(self, n):
            if n is fn:
                self.generic_visit(n)
        def visit_Import(self, n):
            self.imports.append(n)
        def visit_ImportFrom(self, n):
            self.imports.append(n)
    v = _V(); v.visit(fn)
    return v.imports


def _bindings_from(imports: list[ast.stmt]) -> dict:
    """name -> ('module', rel_path) | ('symbol', rel_path, original_symbol) for project-internal imports."""
    binds = {}
    for imp in imports:
        if isinstance(imp, ast.ImportFrom) and imp.module and imp.level == 0:
            base = _module_to_rel(imp.module)
            for alias in imp.names:
                local = alias.asname or alias.name
                sub = _module_to_rel(f"{imp.module}.{alias.name}")   # `from core import mineness` → module
                if sub is not None:
                    binds[local] = ("module", sub)
                elif base is not None:
                    binds[local] = ("symbol", base, alias.name)       # `from core.x import y` → symbol
        elif isinstance(imp, ast.Import):
            for alias in imp.names:
                rel = _module_to_rel(alias.name)
                if rel is not None:
                    binds[alias.asname or alias.name.split(".")[0]] = ("module", rel)
    return binds


def _norm_symbol_label(label: str) -> str:
    """'UnifiedInferenceGate.modulation()' / '.modulation()' / 'modulation()' -> 'modulation'.
    Matches what ast.Attribute.attr / ast.Name.id give us at a call site, regardless of whether
    graphify's own label included a class-name prefix (it's inconsistent about this)."""
    s = label.strip()
    if s.endswith("()"):
        s = s[:-2]
    if "." in s:
        s = s.rsplit(".", 1)[-1]
    return s


def _build_node_lookups(nodes: list[dict]) -> tuple[dict, dict]:
    """(file_id_by_source, symbol_id_by_file_and_name) built from the graph's OWN nodes — not recomputed
    via make_id — so a same-basename-collision ID quirk in graphify's own extractor (see module docstring)
    can't silently break target resolution the way recomputing IDs did for core/stick_test.py."""
    file_id_by_source: dict[str, str] = {}
    symbol_id_by_file_and_name: dict[tuple[str, str], str] = {}
    for n in nodes:
        if n.get("_origin") != "ast" or n.get("file_type") != "code":
            continue
        sf = (n.get("source_file") or "").replace("\\", "/")
        if not sf:
            continue
        label = n.get("label", "")
        if label == Path(sf).name:                      # the whole-file node itself
            file_id_by_source.setdefault(sf, n["id"])
        else:
            symbol_id_by_file_and_name.setdefault((sf, _norm_symbol_label(label)), n["id"])
    return file_id_by_source, symbol_id_by_file_and_name


def enrich(dry: bool = False) -> dict:
    g = json.loads(GRAPH.read_text(encoding="utf-8"))
    node_ids = {n["id"] for n in g["nodes"]}
    file_id_by_source, symbol_id_by_file_and_name = _build_node_lookups(g["nodes"])
    edges = g.get("links") or g.get("edges") or []
    edge_key = {(e.get("source"), e.get("target"), e.get("relation")) for e in edges}
    added_calls = added_imports = 0
    examples = []

    def _file_id_lookup(rel_path: Path) -> str:
        sf = str(rel_path).replace("\\", "/")
        return file_id_by_source.get(sf) or _file_id(rel_path)

    py_files = [p for d in PKG_DIRS for p in (ROOT / d).rglob("*.py")]
    for path in py_files:
        rel = path.relative_to(ROOT)
        rel_str = str(rel).replace("\\", "/")
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        module_binds = _bindings_from([n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))])
        caller_file = _file_id_lookup(rel)

        def _self_attr_types(class_node) -> dict:
            """Scan every method in this class for `self.X = Y(...)` where Y resolves (via that method's
            own module+local binds) to a project symbol import — self.X's project file, keyed by X.
            Covers the __init__-then-used-elsewhere pattern (self.unified_gate = UnifiedInferenceGate();
            ... self.unified_gate.observe(...) in a different method)."""
            attr_types: dict[str, str] = {}
            for method in ast.walk(class_node):
                if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                local = _bindings_from(_local_imports(method))
                binds = {**module_binds, **local}
                for sub in _own_scope_nodes(method):
                    if not isinstance(sub, ast.Assign):
                        continue
                    if not (isinstance(sub.value, ast.Call) and isinstance(sub.value.func, ast.Name)):
                        continue
                    b = binds.get(sub.value.func.id)
                    if not b or b[0] != "symbol":
                        continue
                    tgt_file = str(b[1]).replace("\\", "/")
                    for tgt in sub.targets:
                        if (isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name)
                                and tgt.value.id == "self"):
                            attr_types[tgt.attr] = tgt_file
            return attr_types

        # walk with a scope stack so calls attribute to the right (existing) caller node
        class Walk(ast.NodeVisitor):
            def __init__(self):
                self.stack: list[tuple[str, str]] = []       # ('class'|'func', name)
                self.class_attr_stack: list[dict] = []        # self-attr type maps, nearest class last
            def visit_ClassDef(self, n):
                self.stack.append(("class", n.name))
                self.class_attr_stack.append(_self_attr_types(n))
                local = _bindings_from(_local_imports(n))
                self._emit_imports(local)
                self.generic_visit(n)
                self.class_attr_stack.pop()
                self.stack.pop()
            def visit_FunctionDef(self, n):
                self.stack.append(("func", n.name))
                local = _bindings_from(_local_imports(n))
                merged = {**module_binds, **local}
                self._emit_imports(local)
                self._scan_calls(n, merged)
                self.generic_visit(n)
                self.stack.pop()
            visit_AsyncFunctionDef = visit_FunctionDef

            def _caller_id(self):
                # nearest enclosing def/class chain whose id exists
                for i in range(len(self.stack), 0, -1):
                    parts = [nm for _, nm in self.stack[:i]]
                    cid = _sym_id(rel, *parts)
                    if cid in node_ids:
                        return cid
                return caller_file if caller_file in node_ids else None

            def _emit_imports(self, local):
                nonlocal added_imports
                for _, b in local.items():
                    tgt = _file_id_lookup(b[1])
                    if tgt in node_ids and tgt != caller_file:
                        k = (caller_file, tgt, "imports_from")
                        if k not in edge_key:
                            edge_key.add(k)
                            edges.append({"source": caller_file, "target": tgt, "relation": "imports_from",
                                          "confidence": "EXTRACTED", "confidence_score": 1.0,
                                          "weight": 1.0, "source_file": rel_str,
                                          "enriched": "local_import"})
                            added_imports += 1

            def _scan_calls(self, fnnode, binds):
                nonlocal added_calls
                self_attrs = self.class_attr_stack[-1] if self.class_attr_stack else {}
                for sub in _own_scope_nodes(fnnode):     # this fn's own scope only (not nested defs)
                    if isinstance(sub, ast.Call):
                        tgt = self._resolve_call(sub.func, binds, self_attrs)
                        if not tgt or tgt not in node_ids:
                            continue
                        caller = self._caller_id()
                        if not caller or caller == tgt:
                            continue
                        k = (caller, tgt, "calls")
                        if k not in edge_key:
                            edge_key.add(k)
                            edges.append({"source": caller, "target": tgt, "relation": "calls",
                                          "confidence": "EXTRACTED", "confidence_score": 1.0,
                                          "weight": 1.0, "source_file": rel_str,
                                          "enriched": "local_import"})
                            added_calls += 1
                            if len(examples) < 8:
                                examples.append(f"{caller} --calls--> {tgt}")

            def _resolve_call(self, func, binds, self_attrs):
                if isinstance(func, ast.Name) and func.id in binds:
                    b = binds[func.id]
                    if b[0] == "symbol":
                        return _sym_id(b[1], b[2])
                elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == "self":
                        # self.method() — a sibling method in THIS same file
                        return symbol_id_by_file_and_name.get((rel_str, func.attr))
                    b = binds.get(func.value.id)
                    if b and b[0] == "module":
                        return _sym_id(b[1], func.attr)
                elif (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute)
                        and isinstance(func.value.value, ast.Name) and func.value.value.id == "self"):
                    # self.attr.method() — attr's type was tracked from a self.attr = ProjectClass(...)
                    tgt_file = self_attrs.get(func.value.attr)
                    if tgt_file:
                        return symbol_id_by_file_and_name.get((tgt_file, func.attr))
                return None

        Walk().visit(tree)

    if not dry:
        key = "links" if "links" in g else "edges"
        g[key] = edges
        GRAPH.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    return {"added_calls": added_calls, "added_imports": added_imports, "examples": examples,
            "total_edges": len(edges)}


def _norm_label(label: str) -> str:
    s = label[:-2] if label.endswith("()") else label
    return s.rsplit(".", 1)[-1] if "." in s else s


def dedupe_ghosts(dry: bool = False) -> dict:
    """Merge GHOST duplicate nodes into their real AST twin (found via an enrich() audit, 2026-08-18).

    graphify's own semantic-extraction merge step can fail to match a doc/rationale mention of a symbol
    back to the existing AST node for that exact same file+symbol — instead minting a second, disconnected
    node with a cruder ID (this project hit it 125x, e.g. `core/orchestrator.py`'s `_thalamic_gate` exists
    as BOTH the well-connected `core_orchestrator_orchestrator_thalamic_gate` (_origin: ast) AND an isolated
    ghost `core_orchestrator_thalamic_gate` (no _origin, alone in its own singleton community) — same bug
    class documented in graphify.ids' own docstring (#550 same-name collisions), just at symbol grain, not
    just file grain. A ghost inflates the graph's apparent orphan count without representing anything real.

    A node is merged ONLY when it shares (source_file, normalized-symbol-name) with an EXISTING `_origin:
    ast` node — i.e. it is provably describing the exact same code symbol in the exact same file, not just a
    similarly-named thing elsewhere. Cross-file doc-mention nodes (e.g. a plan doc's own node for
    "core/spatial.py") are NEVER touched — their source_file is the doc, not the code file, so they never
    match this key. Merge = every edge naming the ghost is rewritten to the real node, then the ghost node
    (and any now-exact-duplicate edges) is dropped. Idempotent: a second run finds 0 ghosts.
    """
    g = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = g["nodes"]
    key = "links" if "links" in g else "edges"
    edges = g.get(key, [])

    ast_by_key: dict[tuple[str, str], str] = {}
    for n in nodes:
        if n.get("_origin") == "ast" and n.get("file_type") == "code":
            sf = (n.get("source_file") or "").replace("\\", "/")
            ast_by_key.setdefault((sf, _norm_label(n.get("label", ""))), n["id"])

    remap: dict[str, str] = {}
    examples = []
    for n in nodes:
        if n.get("_origin") == "ast":
            continue
        sf = (n.get("source_file") or "").replace("\\", "/")
        real = ast_by_key.get((sf, _norm_label(n.get("label", ""))))
        if real and real != n["id"]:
            remap[n["id"]] = real
            if len(examples) < 10:
                examples.append(f"{n['id']} -> {real}  ({sf} :: {n.get('label','')})")

    if not remap:
        return {"merged": 0, "examples": [], "total_nodes": len(nodes), "total_edges": len(edges)}

    seen = set()
    new_edges = []
    for e in edges:
        s = remap.get(e.get("source"), e.get("source"))
        t = remap.get(e.get("target"), e.get("target"))
        if s == t:
            continue                                   # self-loop created by the merge — drop
        k = (s, t, e.get("relation"))
        if k in seen:
            continue                                    # now-duplicate of an edge the real node already had
        seen.add(k)
        e2 = dict(e)
        e2["source"], e2["target"] = s, t
        new_edges.append(e2)

    new_nodes = [n for n in nodes if n["id"] not in remap]

    # hyperedges live in their own top-level list (not `edges`/`links`) — a ghost merge above would
    # otherwise leave any hyperedge that named a ghost member pointing at a now-deleted id (found
    # 2026-08-18: 8 of 77 hyperedges went dangling this way after the first merge missed this).
    surviving_ids = {n["id"] for n in new_nodes}
    new_hyperedges = []
    dropped_members = dropped_hyperedges = 0
    for h in g.get("hyperedges", []):
        members = h.get("nodes") or h.get("members") or []
        remapped = [remap.get(m, m) for m in members]         # redirect any ghost member onto its real twin
        valid = [m for m in remapped if m in surviving_ids]   # then drop anything still unresolvable
        if len(valid) < 2:
            dropped_hyperedges += 1
            continue
        if valid != members:
            dropped_members += len(members) - len(valid)
            h = dict(h)
            h["nodes"] = valid
        new_hyperedges.append(h)
    g["hyperedges"] = new_hyperedges

    if not dry:
        g["nodes"] = new_nodes
        g[key] = new_edges
        GRAPH.write_text(json.dumps(g, ensure_ascii=False), encoding="utf-8")
    return {"merged": len(remap), "examples": examples,
            "total_nodes": len(new_nodes), "total_edges": len(new_edges),
            "hyperedges_member_drops": dropped_members, "hyperedges_dropped": dropped_hyperedges}


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    r = enrich(dry=dry)
    tag = "[dry-run] WOULD add" if dry else "ADDED"
    print(f"{tag} {r['added_calls']} calls + {r['added_imports']} imports_from edges "
          f"(local-import recovery). graph now {r['total_edges']} edges.")
    for ex in r["examples"]:
        print("   +", ex)

    r2 = dedupe_ghosts(dry=dry)
    tag2 = "[dry-run] WOULD merge" if dry else "MERGED"
    print(f"{tag2} {r2['merged']} ghost duplicate nodes into their real AST twin. "
          f"graph now {r2['total_nodes']} nodes / {r2['total_edges']} edges.")
    for ex in r2["examples"]:
        print("   +", ex)

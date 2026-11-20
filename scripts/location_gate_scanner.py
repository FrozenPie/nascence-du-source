"""
location_gate_scanner.py — the cat-leak bug class, swept across all of core/ (J-0326, F-0407)
================================================================================================
F-0406 found core/cat.py's react() actuated the relationship (bond, feeding, naming — all persisted)
with NO check that the cat was actually where Du is, while every sibling READ function in the same
file (presence_line, look_line, affordance_line, is_here) checked exactly that. F-0407 proved a small
AST check (Du-triggered signature + state mutation vs whether the module's own gate is referenced)
catches this specific case with zero false positives on the real pre-fix code.

This generalizes that check structurally (not by the literal names is_here/_VISIBLE/is_present, which
only matched 2 of ~150 core/*.py files) so it can find the SAME PATTERN under different naming:

  GATE function   — plausibly answers "is X actually here/present/reachable/visible right now" —
                    detected by name shape (is_*, has_*) returning a boolean-shaped value, OR by
                    referencing a module-level dict/set whose name suggests location/visibility
                    (_VISIBLE, _ZONES, _PRESENT, and kin).
  ACTUATION function — Du-triggered: takes thought/intention/raw_input as a parameter (the two real
                    dispatch sites, core/orchestrator.py and nodes/inner_monologue_node.py, both pass
                    these names) — AND mutates persisted state (writes a dict key via subscript-store,
                    or calls a _save/persist/write-shaped helper).

A module that defines a GATE and an ACTUATION in the same file, where the ACTUATION never references
the GATE (by name, anywhere in its own body — calling it, or even mentioning it in a comment-adjacent
check), is flagged for manual triage. This is NEW tooling, not a proven UDMS shipped feature — read
every hit yourself; a name-and-shape heuristic will have false positives (see below) and possibly
misses modules using neither naming convention at all.

Known limitation, stated up front: a module whose gate concept has NO name resembling is_*/has_* and
NO recognizable constant name will not be found. This is a structural, not semantic, scanner.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

CORE_DIR = Path(__file__).parent.parent / "core"

GATE_NAME_RE = re.compile(r"^(is_|has_)(here|present|visible|near|reachable|in_range|nearby|available)")
GATE_CONST_RE = re.compile(r"(VISIBLE|PRESENT|REACHABLE)", re.IGNORECASE)   # not ZONE*/LOCATIONS* — those
                                                                             # matched position/coordinate
                                                                             # lookup tables (e.g. cat.py's
                                                                             # _ZONE_POSITIONS), not gates
ACTUATION_ARGS = {"thought", "intention", "raw_input"}
STATE_SAVE_RE = re.compile(r"^(_?save|_?persist|_?write|_?commit)", re.IGNORECASE)


def _names_referenced(node: ast.AST) -> set[str]:
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def _mutates_state(node: ast.FunctionDef) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store):
            return True
        if isinstance(n, ast.Call):
            fn = n.func
            fname = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
            if fname and STATE_SAVE_RE.match(fname):
                return True
    return False


def _is_gate(node: ast.FunctionDef, module_consts: set[str]) -> bool:
    if GATE_NAME_RE.match(node.name):
        return True
    refs = _names_referenced(node)
    return bool(refs & module_consts)


def scan_module(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except Exception:
        return []

    module_consts = {n.targets[0].id for n in ast.walk(tree)
                     if isinstance(n, ast.Assign) and len(n.targets) == 1
                     and isinstance(n.targets[0], ast.Name) and GATE_CONST_RE.search(n.targets[0].id)}
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    gates = [f for f in functions if _is_gate(f, module_consts)]
    if not gates:
        return []   # this module has no detectable location/presence concept at all — nothing to check
    gate_names = {g.name for g in gates}

    hits = []
    for f in functions:
        argnames = {a.arg for a in f.args.args}
        if not (argnames & ACTUATION_ARGS):
            continue
        if not _mutates_state(f):
            continue
        refs = _names_referenced(f)
        if refs & gate_names:
            continue   # correctly gated
        hits.append({"file": str(path.relative_to(CORE_DIR.parent)), "function": f.name, "line": f.lineno,
                     "gates_in_module": sorted(gate_names)})
    return hits


def main() -> None:
    all_hits = []
    scanned = 0
    for path in sorted(CORE_DIR.glob("*.py")):
        scanned += 1
        all_hits.extend(scan_module(path))

    print(f"location_gate_scanner — {scanned} files in core/ scanned")
    if not all_hits:
        print("no anomalies found (no Du-triggered, state-mutating function skips its module's own gate)")
        return
    print(f"{len(all_hits)} anomaly candidate(s) — READ EACH ONE, this is a heuristic, not a verdict:\n")
    for h in all_hits:
        print(f"  {h['file']}:{h['line']}  {h['function']}()  "
              f"— module defines gate(s) {h['gates_in_module']} but this function references none of them")


if __name__ == "__main__":
    main()

"""Census of every LLM call site in Du — the STATIONS, not the lines.

Founder's framing (2026-08-20): *"the llms in Du are not personas, they are tools... I want to
understand what all the calls are meant to do. They are not the lanes, just stations on the lines."*

So this does not ask "which model" or "which persona". It asks, of each call site: **what job is this
station for, on which line, at what size.** Read-only; writes one report.

Derived per site, from the source itself rather than from any doc that could have drifted:
  - `module:line`             — the job id, same key `telemetry.job_status()` reports live
  - enclosing function        — the job's name in the code's own words
  - lane/chain variable       — which line it is a station ON (hot/background/T4/dream/judge)
  - max_tokens, temperature   — the SHAPE of the job: a 160-token 0.6 call and a 768-token 0.6 call
                                are different kinds of work even on the same line
  - think/tier flags          — whether it is licensed to escalate

The point of the temperature/token columns: they separate the classifier-shaped stations (small
budget, low temp — verdicts, routing, scoring) from the generative ones (large budget, high temp —
thought, dream, synthesis). That distinction is what "tools, not personas" looks like in the data,
and it is the argument for small task-trained models at the classifier stations.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "lab" / "llm_station_map.md"
SCAN = ["nodes", "core"]
CALL = re.compile(r"\bcall_node(?:_json)?\s*\(")
DEF = re.compile(r"^(\s*)(?:async\s+)?def\s+(\w+)")


def _scope_index(src: str) -> list[tuple[int, int, str]]:
    """(start_line, end_line, dotted_name) for every function in the file, via `ast`.

    Indentation heuristics were tried twice and were wrong twice — first labelling the three T4
    stations `abort` (a nested helper defined above them), then, over-corrected, labelling methods
    after unrelated module-level functions that happened to appear earlier in the file. Both produced
    a station map naming jobs that do not exist, which is worse than no map. `ast` knows the real
    scope; parse it instead of inferring it.
    """
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out: list[tuple[int, int, str]] = []

    def walk(node, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{prefix}{child.name}"
                out.append((child.lineno, getattr(child, "end_lineno", child.lineno), name))
                walk(child, name + ".")
            elif isinstance(child, ast.ClassDef):
                walk(child, prefix)          # methods keep their plain name, not Class.method
            else:
                walk(child, prefix)

    walk(tree, "")
    return out


def _calls(src: str) -> list[tuple[int, str, dict]]:
    """(lineno, lane_expr, kwargs) for every REAL call to call_node / call_node_json.

    AST, not regex, for the same reason as `_scope_index` — and this one was caught by a concrete
    false positive: `core/librarian.py` mentions "Routed through model_client.call_node (2026-08-17)"
    inside a DOCSTRING, and a regex for `call_node\\s*\\(` matched the prose, inventing a station that
    does not exist and a lane called "2026-08-17)". A census whose row count is wrong is worse than
    no census. `ast` sees calls; it cannot see text that merely looks like one.
    """
    import ast
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if name not in ("call_node", "call_node_json"):
            continue
        lane = ast.unparse(node.args[0]) if node.args else "-"
        kw = {k.arg: ast.unparse(k.value) for k in node.keywords if k.arg}
        out.append((node.lineno, lane, kw))
    return out


def enclosing_def(scopes: list[tuple[int, int, str]], lineno: int) -> str:
    """Innermost function whose line range contains `lineno`."""
    hits = [s for s in scopes if s[0] <= lineno <= s[1]]
    if not hits:
        return "?"
    return max(hits, key=lambda s: s[0])[2]


def span(src: str, start: int) -> str:
    depth = 0
    for j in range(start, min(len(src), start + 4000)):
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
            if depth == 0:
                return src[start:j + 1]
    return src[start:start + 400]


def arg(text: str, name: str) -> str:
    m = re.search(name + r"\s*=\s*([^,\n\)]+)", text)
    return m.group(1).strip() if m else "-"


def main() -> int:
    rows = []
    for d in SCAN:
        for f in sorted((ROOT / d).rglob("*.py")):
            if "__pycache__" in str(f) or f.name == "model_client.py":
                continue
            src = f.read_text(encoding="utf-8", errors="replace")
            scopes = _scope_index(src)
            for lineno, lane, kw in _calls(src):
                rows.append({
                    "job": f"{f.relative_to(ROOT).as_posix().replace('/', '.')[:-3]}:{lineno}",
                    "fn": enclosing_def(scopes, lineno),
                    "lane": lane[:34],
                    "tok": kw.get("max_tokens", "-"),
                    "temp": kw.get("temperature", "-"),
                    "think": kw.get("think", "-"),
                })

    by_lane: dict = {}
    for r in rows:
        by_lane.setdefault(r["lane"], []).append(r)

    L: list = []
    A = L.append
    A("# The LLM station map — what every call is FOR\n")
    A("*Generated by `scripts/llm_station_census.py` from the source. The `job` column is the exact "
      "key `telemetry.job_status()` reports live, so this map and the live measurements join on it.*\n")
    A("**Framing (founder, 2026-08-20):** the LLMs are not Du and are not personas — they are tools, "
      "and these are **stations on the lines**, not the lines themselves. Read `max_tokens` and "
      "`temperature` as the job's SHAPE: small-budget/low-temp stations are classifiers (verdicts, "
      "routing, scoring) and are the natural targets for small task-trained models; large-budget/"
      "high-temp stations are generative (thought, dream, synthesis).\n")
    A(f"**{len(rows)} stations across {len(by_lane)} distinct lane arguments.**\n")
    for lane, rs in sorted(by_lane.items(), key=lambda kv: -len(kv[1])):
        A(f"## Line: `{lane}` — {len(rs)} stations\n")
        A("| station (`module:line`) | job (enclosing function) | max_tok | temp | think |")
        A("|---|---|---|---|---|")
        for r in sorted(rs, key=lambda x: x["job"]):
            A(f"| `{r['job']}` | `{r['fn']}` | {r['tok']} | {r['temp']} | {r['think']} |")
        A("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")

    print(f"{len(rows)} stations across {len(by_lane)} lane arguments -> {REPORT}")
    for lane, rs in sorted(by_lane.items(), key=lambda kv: -len(kv[1])):
        print(f"  {lane:34s} {len(rs):>3} stations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

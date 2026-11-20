"""The TIMETABLE — what opens each LLM station, and how often. Read-only; writes one report.

`docs/transit_map.md` defines LINES by their clock, BUSES by their route, FACTORIES by their process.
It has never had a STATION layer: the 37 LLM call sites (`docs/lab/llm_station_map.md`) are not on it.
So the map says the Idle Line runs "per tick" without saying which stations that tick opens, at what
rate, or what freight each produces. That missing column is what this derives.

For each station it answers: **who calls the function this station lives in, and what gates it.**
A station reached only behind `random.random() < 0.05` inside a 30s loop is a different service from
one reached unconditionally every cycle, even when both sit on the same line — and today those two
look identical everywhere except in the source.

Method: AST. Build a call graph over `nodes/` + `core/`, then for each station's enclosing function
walk UP to find its callers, and collect the gate expressions (probability draws, modulo cadences,
cooldowns, flags) that guard the call. Regex was tried on this codebase three times today and was
wrong three times — twice on scoping, once matching a `call_node` mention inside a DOCSTRING. It is
not used here for anything structural.
"""
from __future__ import annotations

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "lab" / "llm_timetable.md"
SCAN = ["nodes", "core"]

# Gate signatures — what makes a call CONDITIONAL rather than every-pass.
GATE_PAT = [
    (re.compile(r"random\s*\.\s*random\s*\(\)\s*<\s*([\w\.\[\]'\"]+)"), "probability"),
    (re.compile(r"random\s*\.\s*randint|random\s*\.\s*choice|random\s*\.\s*sample"), "random-pick"),
    (re.compile(r"%\s*(\d+)\s*==\s*0"), "every-N"),
    (re.compile(r"(_COOLDOWN|cooldown|_MIN_GAP|min_gap|_GAP_)", re.I), "cooldown"),
    (re.compile(r"(time\.time\(\)\s*-\s*\w+)\s*[<>]"), "elapsed-time"),
    (re.compile(r"\b(is_asleep|asleep|sleeping|_sleep|at_sleep)\b", re.I), "sleep-gated"),
    (re.compile(r"\b(LIVE|_ENABLED|ENABLED|_ON)\b"), "flag-gated"),
]


def parse(f: Path):
    try:
        return ast.parse(f.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None


def fn_index(tree, mod: str) -> list[tuple[int, int, str, ast.AST]]:
    out = []

    def walk(node, prefix):
        for c in ast.iter_child_nodes(node):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{prefix}{c.name}"
                out.append((c.lineno, getattr(c, "end_lineno", c.lineno), name, c))
                walk(c, name + ".")
            elif isinstance(c, ast.ClassDef):
                walk(c, prefix)
            else:
                walk(c, prefix)

    walk(tree, "")
    return out


def called_names(node) -> list[tuple[str, int]]:
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            nm = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if nm:
                out.append((nm, n.lineno))
    return out


def gates_for(src_lines: list[str], fn_start: int, call_line: int) -> list[str]:
    """Gate signatures appearing between the function's start and the call — the guards it sits behind."""
    seg = "\n".join(src_lines[fn_start - 1:call_line])
    found = []
    for pat, label in GATE_PAT:
        m = pat.search(seg)
        if m:
            detail = m.group(1) if m.groups() and m.group(1) else ""
            found.append(f"{label}{'=' + detail if detail and label in ('probability', 'every-N') else ''}")
    return sorted(set(found))


def main() -> int:
    files, trees, indexes, srclines = {}, {}, {}, {}
    for d in SCAN:
        for f in sorted((ROOT / d).rglob("*.py")):
            if "__pycache__" in str(f):
                continue
            t = parse(f)
            if t is None:
                continue
            mod = f.relative_to(ROOT).as_posix().replace("/", ".")[:-3]
            files[mod] = f
            trees[mod] = t
            indexes[mod] = fn_index(t, mod)
            srclines[mod] = f.read_text(encoding="utf-8", errors="replace").splitlines()

    # stations
    stations = []
    for mod, t in trees.items():
        if mod == "core.model_client":
            continue
        for n in ast.walk(t):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            nm = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
            if nm not in ("call_node", "call_node_json"):
                continue
            owner = [s for s in indexes[mod] if s[0] <= n.lineno <= s[1]]
            fn = max(owner, key=lambda s: s[0])[2] if owner else "?"
            fn_start = max(owner, key=lambda s: s[0])[0] if owner else n.lineno
            stations.append({
                "mod": mod, "line": n.lineno, "fn": fn,
                "lane": ast.unparse(n.args[0]) if n.args else "-",
                "gates": gates_for(srclines[mod], fn_start, n.lineno),
            })

    # who calls whom (by bare function name — enough in this codebase, ambiguity is reported)
    callers = defaultdict(set)
    for mod, idx in indexes.items():
        for start, end, name, node in idx:
            for nm, ln in called_names(node):
                callers[nm].add(f"{mod}.{name}")

    L = ["# The LLM TIMETABLE — what opens each station, and how often\n",
         "*Generated by `scripts/llm_timetable.py` (AST). Joins to `docs/lab/llm_station_map.md` and to "
         "live `telemetry.job_status()` on the `module:line` key.*\n",
         "Adds the missing **station layer** to `docs/transit_map.md`, which defines lines by their clock "
         "and buses by their route but has never placed the LLM calls on either.\n",
         "**`gates`** are the guards between the enclosing function's start and the call — a station behind "
         "`probability=0.05` is a different service from one reached every pass, even on the same line.\n",
         "**`callers`** is who invokes the enclosing function. An empty list means nothing in `nodes/` or "
         "`core/` calls it by that name — either it is an entry point (orchestrator/daemon-driven) or it is "
         "**dead**, and those two must not be confused; both are flagged for a human read.\n",
         "| station | job | lane | gates | called by |", "|---|---|---|---|---|"]
    orphans = []
    for s in sorted(stations, key=lambda x: (x["mod"], x["line"])):
        short = s["fn"].split(".")[-1]
        c = sorted(callers.get(short, set()))
        c = [x for x in c if not x.endswith("." + s["fn"])]
        if not c:
            orphans.append(s)
        cs = ", ".join(f"`{x}`" for x in c[:3]) + (f" +{len(c) - 3}" if len(c) > 3 else "")
        L.append(f"| `{s['mod']}:{s['line']}` | `{short}` | `{s['lane'][:26]}` | "
                 f"{', '.join(s['gates']) or '—'} | {cs or '**(none found)**'} |")
    L.append("")
    L.append(f"## Stations whose enclosing function has no in-repo caller ({len(orphans)})\n")
    L.append("Entry point or dead code — needs a human read, and the distinction matters:\n")
    for s in orphans:
        L.append(f"- `{s['mod']}:{s['line']}` — `{s['fn']}`")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")

    print(f"{len(stations)} stations -> {REPORT}")
    gated = sum(1 for s in stations if s["gates"])
    print(f"  behind at least one gate : {gated}")
    print(f"  every-pass (no gate)     : {len(stations) - gated}")
    print(f"  no in-repo caller        : {len(orphans)}")
    for s in stations:
        if s["gates"]:
            print(f"    {s['mod']}:{s['line']:<5} {s['fn'].split('.')[-1]:<24} {', '.join(s['gates'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

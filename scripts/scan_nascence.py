"""
scan_nascence.py - read-only AST + ledger scanner behind scripts/build_antigravity_overview.py.

Moved into the repo by J-2415 (F-3115) so the Truth-Badged overview is reproducible from the repo alone
(it used to live in ~/.gemini/antigravity/.../scratch/ and write a JSON the builder trusted).

Rules this scanner enforces (each one is a finding in docs/reviews/system_overview_antigravity_review_2026-10-18.md):
  * files are read as utf-8-sig and a file that does not decode or parse RAISES ScanError (core/lane2.py has a BOM
    and the old scanner swallowed that into "0 lines, 0 edges");
  * import edges are counted per DISTINCT MODULE (never per imported name), relative imports are resolved, and each
    edge is classed top-level / lazy (inside a function) / dynamic (name only known at run time);
  * dynamic loads are resolved: __import__(f"core.{x}") / importlib.import_module over a literal tuple loop
    (core/world_detail.py), and every "mod:<module>:<attr>" binding string (core/actions.py -> core/dispatch.py);
  * a module can be analysed from the working tree OR from a git commit (the BOOT commit), so a badge can say
    "reachable in the build that is actually running";
  * nothing here writes anywhere. It never touches data/.
"""
from __future__ import annotations

import ast
import io
import warnings
import json
import re
import subprocess
import tarfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RUNTIME_ROOTS = ("scripts/run_nascence.py", "core/orchestrator.py", "nodes/inner_monologue_node.py")
DYNAMIC_LOADER = "core/dispatch.py"          # resolves "mod:<module>:<attr>" bindings at call time
MOD_BINDING = re.compile(r"^mod:([A-Za-z_][\w.]*):(\w+)$")
BOOT_LINE = "[nascence.main] Identity loaded:"


class ScanError(RuntimeError):
    """A runtime file could not be decoded or parsed - the scan refuses to continue with a hole in it."""


# --------------------------------------------------------------------------- source providers
def runtime_rel_paths_on_disk(root: Path) -> list[str]:
    out = []
    for sub in ("core", "nodes"):
        for p in sorted((root / sub).rglob("*.py")):
            if "__pycache__" in p.parts or "graphify-out" in p.parts:
                continue
            if sub == "nodes" and p.name == "__init__.py":
                continue
            out.append(p.relative_to(root).as_posix())
    out.append("scripts/run_nascence.py")
    return out


def decode(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ScanError(f"{label}: not valid utf-8 ({exc})") from exc


def read_tree_from_disk(root: Path) -> dict[str, str]:
    return {rel: decode((root / rel).read_bytes(), rel) for rel in runtime_rel_paths_on_disk(root) if (root / rel).exists()}


def read_tree_from_git(root: Path, commit: str) -> dict[str, str]:
    """Runtime sources as of `commit` (git archive piped through tarfile - no checkout, nothing touched)."""
    proc = subprocess.run(["git", "archive", commit, "core", "nodes", "scripts/run_nascence.py"], cwd=root,
                          capture_output=True, check=True)
    out: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tf:
        for m in tf.getmembers():
            if not m.isfile() or not m.name.endswith(".py"):
                continue
            if "__pycache__" in m.name or m.name == "nodes/__init__.py":
                continue
            out[m.name] = decode(tf.extractfile(m).read(), f"{commit[:8]}:{m.name}")
    return out


# --------------------------------------------------------------------------- per-file parse
def dotted_for(rel: str) -> str:
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def package_of(rel: str) -> list[str]:
    parts = rel[:-3].split("/")
    return parts[:-1]


def _flags(tree: ast.Module, text: str) -> tuple[dict[str, bool], dict[str, str], dict[str, bool]]:
    """(bool flags, trailing-comment text per flag, numeric-zero 'flags'). Module level only."""
    flags: dict[str, bool] = {}
    comments: dict[str, str] = {}
    zeros: dict[str, bool] = {}
    src = text.splitlines()
    for node in tree.body:
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        for t in targets:
            if not (isinstance(t, ast.Name) and t.id.isupper() and isinstance(value, ast.Constant)):
                continue
            if isinstance(value.value, bool):
                flags[t.id] = value.value
                line = src[node.lineno - 1] if node.lineno - 1 < len(src) else ""
                comments[t.id] = line.split("#", 1)[1].strip() if "#" in line else ""
            elif isinstance(value.value, (int, float)) and value.value == 0:
                zeros[t.id] = False
    return flags, comments, zeros


class _Visitor(ast.NodeVisitor):
    """Collects imports (with lazy/top-level), dynamic loads, jsonl names, mod: bindings, discarded-vs-used calls."""

    def __init__(self) -> None:
        self.func_depth = 0
        self.imports: list[tuple[int, str | None, list[str], bool, list[tuple[str, str]]]] = []
        self.dyn_candidates: list[str] = []
        self.mod_bindings: list[str] = []
        self.jsonl_names: list[str] = []
        self.calls: list[tuple[ast.Call, bool]] = []     # (call, discarded)
        self._for_stack: list[ast.For] = []
        self._expr_calls: set[int] = set()

    def visit_FunctionDef(self, node):
        self.func_depth += 1
        self.generic_visit(node)
        self.func_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef

    def visit_For(self, node):
        self._for_stack.append(node)
        self.generic_visit(node)
        self._for_stack.pop()

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            self._expr_calls.add(id(node.value))
        self.generic_visit(node)

    def visit_Import(self, node):
        self.imports.append((0, None, [a.name for a in node.names], self.func_depth > 0,
                             [(a.name, a.asname or a.name.split(".")[0]) for a in node.names]))

    def visit_ImportFrom(self, node):
        self.imports.append((node.level, node.module, [a.name for a in node.names], self.func_depth > 0,
                             [(a.name, a.asname or a.name) for a in node.names]))

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            if MOD_BINDING.match(node.value):
                self.mod_bindings.append(node.value)
            elif node.value.endswith(".jsonl") or ".jsonl" in node.value:
                self.jsonl_names.append(node.value)

    def visit_JoinedStr(self, node):
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str) and ".jsonl" in v.value:
                self.jsonl_names.append(v.value)
        self.generic_visit(node)

    def _loop_values(self, name: str) -> list[str] | None:
        for loop in reversed(self._for_stack):
            if isinstance(loop.target, ast.Name) and loop.target.id == name and isinstance(loop.iter, (ast.Tuple, ast.List)):
                vals = [e.value for e in loop.iter.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                if vals and len(vals) == len(loop.iter.elts):
                    return vals
        return None

    def visit_Call(self, node):
        self.calls.append((node, id(node) in self._expr_calls))
        fn = node.func
        is_dyn = (isinstance(fn, ast.Name) and fn.id == "__import__") or \
                 (isinstance(fn, ast.Attribute) and fn.attr == "import_module")
        if is_dyn and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                self.dyn_candidates.append(a.value)
            elif isinstance(a, ast.JoinedStr):
                parts: list[list[str]] = []
                ok = True
                for v in a.values:
                    if isinstance(v, ast.Constant):
                        parts.append([str(v.value)])
                    elif isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name):
                        vals = self._loop_values(v.value.id)
                        if vals is None:
                            ok = False
                            break
                        parts.append(vals)
                    else:
                        ok = False
                        break
                if ok:
                    combos = [""]
                    for p in parts:
                        combos = [c + x for c in combos for x in p]
                    self.dyn_candidates.extend(combos)
        self.generic_visit(node)


def parse_module(rel: str, text: str) -> dict:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(text)
    except SyntaxError as exc:
        raise ScanError(f"{rel}: does not parse ({exc})") from exc
    vis = _Visitor()
    vis.visit(tree)
    doc = ast.get_docstring(tree) or ""
    first = doc.strip().split("\n")[0] if doc.strip() else ""
    first = re.sub(r"^Nascence\s*[\-\u2013\u2014\u00b7:]*\s*", "", first)
    first = re.sub(r"^core/[a-zA-Z0-9_/\\\.]+\s*[\-\u2013\u2014\u00b7:]*\s*", "", first)
    defs = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for n in ast.walk(tree))
    flags, fcomments, fzeros = _flags(tree, text)
    return {
        "lines": len(text.splitlines()),
        "doc": first[:220] if first else "Engine module",
        "full_doc": doc[:900],
        "defs": defs,
        "flags": flags, "flag_comments": fcomments, "zero_flags": fzeros,
        "visitor": vis,
        "tree": tree,
    }


# --------------------------------------------------------------------------- graph
KIND_RANK = {"top": 0, "lazy": 1, "dyn": 2}


def build_graph(sources: dict[str, str]) -> dict:
    """Parse every source and build the distinct-module import graph. Pure function of `sources`."""
    parsed = {rel: parse_module(rel, txt) for rel, txt in sorted(sources.items())}
    modmap = {dotted_for(rel): rel for rel in parsed}
    edges: dict[tuple[str, str], str] = {}                      # (src, dst) -> best kind (top < lazy < dyn)

    def add(src: str, dst_dotted: str, kind: str) -> str | None:
        dst = modmap.get(dst_dotted)
        if dst is None or dst == src:
            return dst
        old = edges.get((src, dst))
        if old is None or KIND_RANK[kind] < KIND_RANK[old]:
            edges[(src, dst)] = kind
        return dst

    # alias tables for call-site tracking: file -> {local: (target_rel, attr|None)}
    alias_tabs: dict[str, dict[str, tuple[str, str | None]]] = {}
    dyn_edges_by_src: Counter = Counter()
    for rel, info in parsed.items():
        vis: _Visitor = info["visitor"]
        pkg = package_of(rel)
        aliases: dict[str, tuple[str, str | None]] = {}
        for level, module, names, lazy, bindings in vis.imports:
            kind = "lazy" if lazy else "top"
            if level == 0 and module is None:                    # `import a.b.c [as x]`
                for full, local in bindings:
                    # the longest resolving dotted prefix is the module actually imported
                    parts = full.split(".")
                    for k in range(len(parts), 0, -1):
                        cand = ".".join(parts[:k])
                        if cand in modmap:
                            dst = add(rel, cand, kind)
                            if dst and (local != full.split(".")[0] or k == len(parts)):
                                aliases[local] = (dst, None)
                            break
                continue
            if level:
                base = pkg[: len(pkg) - (level - 1)] if level - 1 <= len(pkg) else []
                base_mod = ".".join(base + ([module] if module else []))
            else:
                base_mod = module or ""
            any_unresolved = False
            for nm, local in bindings:
                sub = f"{base_mod}.{nm}" if base_mod else nm
                if sub in modmap:
                    dst = add(rel, sub, kind)
                    if dst:
                        aliases[local] = (dst, None)
                else:
                    any_unresolved = True
                    if base_mod in modmap:
                        aliases[local] = (modmap[base_mod], nm)
            if base_mod in modmap and (any_unresolved or not bindings):
                add(rel, base_mod, kind)
        for cand in vis.dyn_candidates:
            if cand in modmap:
                add(rel, cand, "dyn")
                dyn_edges_by_src[rel] += 1
        alias_tabs[rel] = aliases

    # "mod:<module>:<attr>" bindings anywhere in the runtime -> loaded by the dispatcher at call time
    mod_names = sorted({MOD_BINDING.match(s).group(1) for info in parsed.values() for s in info["visitor"].mod_bindings})
    for name in mod_names:
        cand = f"core.{name}"
        if cand in modmap and DYNAMIC_LOADER in parsed:
            add(DYNAMIC_LOADER, cand, "dyn")
            dyn_edges_by_src[DYNAMIC_LOADER] += 1

    out_map: dict[str, dict[str, str]] = defaultdict(dict)
    in_map: dict[str, dict[str, str]] = defaultdict(dict)
    for (s, d), k in edges.items():
        out_map[s][d] = k
        in_map[d][s] = k

    # call-site usage: for each module, how many outside call sites keep vs discard the return value
    call_used: Counter = Counter()
    call_discarded: Counter = Counter()
    for rel, info in parsed.items():
        aliases = alias_tabs[rel]
        for call, discarded in info["visitor"].calls:
            fn = call.func
            target = None
            if isinstance(fn, ast.Name) and fn.id in aliases and aliases[fn.id][1] is not None:
                target = aliases[fn.id][0]
            elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id in aliases \
                    and aliases[fn.value.id][1] is None:
                target = aliases[fn.value.id][0]
            if target and target != rel:
                (call_discarded if discarded else call_used)[target] += 1

    # reachability from the runtime roots (top-level, lazy and dynamic edges are all real paths)
    reach = {r for r in RUNTIME_ROOTS if r in parsed}
    queue = list(reach)
    while queue:
        cur = queue.pop()
        for nxt in out_map.get(cur, {}):
            if nxt not in reach:
                reach.add(nxt)
                queue.append(nxt)

    modules = {}
    for rel, info in parsed.items():
        ins, outs = in_map.get(rel, {}), out_map.get(rel, {})
        jsonls = sorted(set(info["visitor"].jsonl_names))
        modules[rel] = {
            "lines": info["lines"], "defs": info["defs"], "doc": info["doc"], "full_doc": info["full_doc"],
            "flags": info["flags"], "flag_comments": info["flag_comments"], "zero_flags": info["zero_flags"],
            "in_deg": len(ins), "out_deg": len(outs),
            "in_top": sum(1 for k in ins.values() if k == "top"),
            "in_lazy": sum(1 for k in ins.values() if k == "lazy"),
            "in_dyn": sum(1 for k in ins.values() if k == "dyn"),
            "out_top": sum(1 for k in outs.values() if k == "top"),
            "out_lazy": sum(1 for k in outs.values() if k == "lazy"),
            "out_dyn": sum(1 for k in outs.values() if k == "dyn"),
            "importers": sorted(ins),
            "reachable": rel in reach,
            "jsonl": jsonls,
            "calls_used": call_used.get(rel, 0),
            "calls_discarded": call_discarded.get(rel, 0),
        }
    gp_files = {rel for rel, info in parsed.items()
                for call, _ in info["visitor"].calls
                if (isinstance(call.func, ast.Name) and call.func.id == "guard_path")
                or (isinstance(call.func, ast.Attribute) and call.func.attr == "guard_path")}
    gp_calls = sum(1 for info in parsed.values() for call, _ in info["visitor"].calls
                   if (isinstance(call.func, ast.Name) and call.func.id == "guard_path")
                   or (isinstance(call.func, ast.Attribute) and call.func.attr == "guard_path"))
    return {"modules": modules, "reachable": sorted(reach), "mod_bindings": mod_names,
            "dynamic_edges": sum(dyn_edges_by_src.values()),
            "guard_path_calls": gp_calls, "guard_path_files": len(gp_files)}


# --------------------------------------------------------------------------- boot / git
def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def find_boot(log_path: Path) -> dict | None:
    """The latest 'Identity loaded' line of data/nascence.log = the process now (or last) running. Read-only."""
    if not log_path.exists():
        return None
    last = None
    with open(log_path, "rb") as fh:
        for raw in fh:
            if BOOT_LINE.encode() in raw:
                last = raw
    if last is None:
        return None
    line = last.decode("utf-8", "replace")
    m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", line)
    return {"stamp": m.group(1), "line": line.strip()[:160]} if m else None


def commit_at_boot(root: Path, stamp: str) -> dict:
    """HEAD as it stood at the boot: last commit at or before the stamp (stamp is machine-local time)."""
    local_dt = datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S").astimezone()
    iso = local_dt.isoformat()
    sha = _git(root, "rev-list", "-1", f"--before={iso}", "HEAD")
    if not sha:
        raise ScanError(f"no commit at or before boot {iso}")
    return {"sha": sha, "short": sha[:8], "boot_iso": iso, "subject": _git(root, "log", "-1", "--format=%s", sha)}


# --------------------------------------------------------------------------- badges
OBSERVE_DOC_CI = re.compile(r"observe[- ]only|shadow[- ]only|shadow[- ]first", re.I)
OBSERVE_DOC_CS = re.compile(r"\bSHADOW\b")
FLAG_SHADOW_COMMENT = re.compile(r"nothing reaches|reaches nothing|shadow[- ]exact|shadow twin|shadow[- ]only", re.I)
DOC_HEAD_CHARS = 260                 # the title/lead of the docstring, not a passing mention further down
RETIRED_DOC = re.compile(r"\bRETIRED\b[^.\n]{0,60}?\b(D-\d{4})")
DEFERRED_DOC = re.compile(r"\b(DEFERRED|PARKED|STANDING RESERVE)\b")
WIRED_HOOK_MAX_IMPORTERS = 3         # the "only call sites discard the return" test is for a wired hook, not shared plumbing
PLUMBING_MIN_IMPORTERS = 8           # this many importers = shared infrastructure; no observe-only claim applies
INFRASTRUCTURE_STEMS = {"profile", "config", "schema", "model_client", "shadow_log"}   # profile.LIVE = "this process owns live data"
FLAG_IGNORE = ("PAUSED", "DISABLE", "KILL")


PROMOTION_NAME = ("LIVE", "DELIVER", "ADMIT")
PROMOTION_COMMENT = re.compile(r"\bON since\b|FLIPPED|flipped", re.I)
KILL_COMMENT = re.compile(r"kill[- ]?switch", re.I)


def master_flags(stem: str, info: dict) -> dict[str, bool]:
    """Boolean flags that govern THIS module as a whole: the flag name carries the module's own name (or is the bare
    LIVE / ENABLED). An exact-name numeric zero (WEAKNESS_PRIOR = 0.0, 'shadow only') counts as False."""
    up = stem.upper()
    keys = {up, up.removesuffix("_NODE"), up.removesuffix("_SHADOW"), up.removesuffix("_LIFE")}
    keys = {k for k in keys if len(k) >= 4}
    out = {n: v for n, v in info["flags"].items()
           if (any(k in n for k in keys) or n in ("LIVE", "ENABLED")) and not any(w in n for w in FLAG_IGNORE)}
    for n, v in info.get("zero_flags", {}).items():
        if n == up:
            out[n] = v
    return out


def strong_flags(mflags: dict[str, bool]) -> dict[str, bool]:
    """Flags named for the module itself; the bare LIVE/ENABLED only count when nothing more specific exists."""
    strong = {n: v for n, v in mflags.items() if n not in ("LIVE", "ENABLED")}
    return strong or mflags


def promoted_by_flag(mflags: dict[str, bool], info: dict) -> str | None:
    """A True flag that PROMOTES the module (LIVE/DELIVER/ADMIT in its name, or a comment saying it was flipped / is ON
    since a date) and is not merely a kill switch (core/needle_triage.py NEEDLE_TRIAGE_LIVE=True is a shadow kill switch)."""
    for n, v in mflags.items():
        if not v:
            continue
        c = info["flag_comments"].get(n, "")
        if KILL_COMMENT.search(c):
            continue
        if any(w in n for w in PROMOTION_NAME) or PROMOTION_COMMENT.search(c):
            return n
    return None


def observe_only_reason(stem: str, info: dict, n_importers: int) -> str | None:
    """Why this module is observe-only, or None. Three independent tests; all refused for shared plumbing, and the
    shadow-file test is refused when some outside call site USES the return value (then it steers). The docstring test
    is NOT: a docstring that says OBSERVE-ONLY in its lead is the module's own claim (core/epistemic_state.py is the
    known judgment call - its lead says OBSERVE-ONLY while its grade is shown to Du; review F-3115 read it as live)."""
    if n_importers >= PLUMBING_MIN_IMPORTERS:
        return None
    head = info["full_doc"][:DOC_HEAD_CHARS]
    consumed = info["calls_used"] > 0
    if OBSERVE_DOC_CI.search(head) or OBSERVE_DOC_CS.search(head):
        return "docstring says shadow/observe-only"
    for n, v in info["flags"].items():
        if v and FLAG_SHADOW_COMMENT.search(info["flag_comments"].get(n, "")):
            return f"{n} comment says it reaches nothing"
    jl = info["jsonl"]
    if not consumed and jl and all("shadow" in j.lower() for j in jl):
        return "writes only *_shadow.jsonl"
    if (0 < n_importers <= WIRED_HOOK_MAX_IMPORTERS and info["calls_discarded"] > 0 and not consumed
            and not stem.endswith(("_log", "_ledger"))):
        return "every call site discards the return"
    return None


def badge_for(rel: str, boot: dict | None, head: dict, git_boot_ok: bool) -> tuple[str, str]:
    """(code, label). code in LIVE/SHADOW/GATED/LAB/RETIRED/DEFERRED. `boot` = module info at the boot commit."""
    stem = Path(rel).stem
    if git_boot_ok and boot is None:
        return "GATED", "\U0001F7E1 RESTART-GATED (committed after boot)"
    src = boot if boot is not None else head
    doc = src["full_doc"]
    m = RETIRED_DOC.search(doc[:400])
    if m:
        return "RETIRED", f"\u26D4 RETIRED ({m.group(1)})"
    if DEFERRED_DOC.search(doc[:DOC_HEAD_CHARS]):
        return "DEFERRED", "\U0001F4A4 DEFERRED"
    if not src["reachable"]:
        return "LAB", "\U0001F535 LAB (no runtime importer)"
    if stem in INFRASTRUCTURE_STEMS:                  # shared plumbing: a bare LIVE flag there means something else
        return "LIVE", "🟢 LIVE"
    mflags_boot = master_flags(stem, src)
    if git_boot_ok and boot is not None:
        mflags_head = master_flags(stem, head)
        flipped = sorted(k for k in set(mflags_boot) | set(mflags_head) if mflags_boot.get(k) != mflags_head.get(k))
        if flipped:
            return "GATED", f"🟡 RESTART-GATED ({flipped[0]} flipped after boot)"
    strong = strong_flags(mflags_boot)
    if strong and not any(strong.values()):
        return "SHADOW", f"🟡 SHADOW ({next(iter(strong))}=False)"
    if promoted_by_flag(mflags_boot, src):
        return "LIVE", "🟢 LIVE"
    why = observe_only_reason(stem, src, len(src["importers"]))
    if why:
        return "SHADOW", f"🟡 SHADOW ({why})"
    return "LIVE", "🟢 LIVE"


# --------------------------------------------------------------------------- docs / ledgers / plans
def count_docs(root: Path) -> dict:
    docs = root / "docs"
    files = sorted(docs.rglob("*.md"))
    by_dir: Counter = Counter()
    for d in files:
        rel = d.relative_to(docs)
        by_dir[rel.parts[0] if len(rel.parts) > 1 else "(root)"] += 1
    return {"total": len(files), "by_dir": dict(by_dir)}


def _rows(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def scan_ledgers(root: Path) -> dict:
    d = root / "docs"
    out: dict[str, dict] = {}
    f = _rows(d / "findings.jsonl")
    out["findings"] = {"total": len(f), "by": dict(Counter(r.get("confidence", "?") for r in f))}
    j = _rows(d / "job_queue.jsonl")
    out["job_queue"] = {"total": len(j), "by": dict(Counter(r.get("status", "?") for r in j))}
    dec = _rows(d / "decisions.jsonl")
    ruled = [r for r in dec if r.get("ruling")]
    events = sum(1 + len(r.get("history") or []) for r in ruled)
    out["decisions"] = {"total": len(dec), "ruled": len(ruled), "ruling_events": events,
                        "with_defeater": sum(1 for r in ruled if r.get("defeater")),
                        "open": len(dec) - len(ruled)}
    for name in ("thoughts", "ideas", "skill_suggestions"):
        rows = _rows(d / f"{name}.jsonl")
        out[name] = {"total": len(rows), "by": dict(Counter(r.get("status", "?") for r in rows))}
    se = d / "session_events.jsonl"
    out["session_events"] = {"total": sum(1 for _ in open(se, "rb")) if se.exists() else 0}
    return out


def scan_plans(root: Path) -> list[dict]:
    docs = root / "docs"
    plans = []
    for pd in ("plans", "staged", "completed", "shelf", "archive"):
        dpath = docs / pd
        if not dpath.exists():
            continue
        for md in sorted(dpath.glob("*.md")):
            txt = md.read_text(encoding="utf-8-sig", errors="replace")
            tm = re.search(r"^#\s+(.+)$", txt, re.M)
            ps = re.search(r"```plan-state\s*\n(.*?)```", txt, re.S)
            stage = verified = phase = None
            if ps:
                block = ps.group(1)
                g = lambda k: (re.search(rf"^{k}:\s*(.+)$", block, re.M) or [None, None])[1]
                stage, verified, phase = g("stage"), g("verified"), g("phase")
            plans.append({
                "dir": pd, "file": f"{pd}/{md.name}", "slug": md.stem,
                "title": (tm.group(1).strip() if tm else md.stem)[:120],
                "stage": (stage or pd).strip(), "verified": (verified or "").strip(),
                "phase": (phase or "")[:160],
                "code_refs": sorted(set(re.findall(r"(?:core|nodes|scripts|hud)/[a-zA-Z0-9_/]+\.py", txt)))[:12],
            })
    return plans


def top_hubs(modules: dict, n: int = 20) -> list[dict]:
    ranked = sorted(modules.items(), key=lambda kv: (-(kv[1]["in_deg"] + kv[1]["out_deg"]), kv[0]))[:n]
    return [{"rel": rel, "total_deg": m["in_deg"] + m["out_deg"], "in_deg": m["in_deg"], "out_deg": m["out_deg"],
             "lines": m["lines"], "doc": m["doc"], "m": m} for rel, m in ranked]


def full_scan(root: Path, data_root: Path | None = None) -> dict:
    """Everything the builder needs. `root` = repo whose tree is documented; `data_root` = where nascence.log lives."""
    root = Path(root)
    head_sources = read_tree_from_disk(root)
    head = build_graph(head_sources)
    data_root = Path(data_root) if data_root else root / "data"
    boot = find_boot(data_root / "nascence.log")
    boot_commit = None
    boot_graph = None
    if boot:
        boot_commit = commit_at_boot(root, boot["stamp"])
        boot_graph = build_graph(read_tree_from_git(root, boot_commit["sha"]))
    scripts = sorted((root / "scripts").glob("*.py"))
    return {
        "head": head, "boot": boot, "boot_commit": boot_commit, "boot_graph": boot_graph,
        "head_sha": _git(root, "rev-parse", "HEAD"),
        "scripts": [p.name for p in scripts],
        "docs": count_docs(root), "ledgers": scan_ledgers(root), "plans": scan_plans(root),
    }


if __name__ == "__main__":
    import sys
    r = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    s = full_scan(r, Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    mods = s["head"]["modules"]
    print(f"modules={len(mods)} reachable={len(s['head']['reachable'])} dynamic_edges={s['head']['dynamic_edges']}")
    print(f"boot={s['boot']} commit={s['boot_commit']}")
    for h in top_hubs(mods, 10):
        print(f"{h['rel']:40s} {h['total_deg']:4d} in={h['in_deg']} out={h['out_deg']}")

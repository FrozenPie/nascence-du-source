r"""Prompt-site census: every place Du's code sends a prompt to an LLM. Read-only, zero LLM, AST not regex.

Built 2026-10-31 (T-0115) after the earlier census (scripts/llm_station_census.py) turned out to be blind
to most prompts: it only matched literal call_node(...) / call_node_json(...), so it missed the ~25
modules that receive the client as a call_json PARAMETER, the ~13 sites that POST raw to /api/chat, the
judge-panel callers, and every NodeBase subclass (whose prompt lives in _build_prompt, not at a call).
This is the detector behind the prompt registry (docs/prompt_registry.jsonl, tool: prompt-registry skill).

Site kinds reported:
  call      a call through core.model_client (call_node / call_node_json / the call_json convention,
            including aliased imports such as call_node_json as _glg_call)
  raw_http  an aiohttp / urllib post to /api/chat, /v1/chat/completions or /api/generate
  judge     a call to core.judge_panel.rule / rule_detail / _ask (the caller supplies the whole prompt; _ask
            is the single-judge primitive another module reaches as _jp._ask / judge_panel._ask, J-3443)
  node      a class deriving from NodeBase (its prompt is system_prompt + _build_prompt)
Plus one counter: the number of seed_parts.append(...) parts the idle thought can assemble.

KEY (stable under line drift): module:Qual.function, and when a function holds more than one site,
module:Qual.function#<system-arg text> (a repeat of the same text gets @2). Node classes are
module:ClassName. Line numbers are reported but are never part of a key.

LIMITS (deliberate, documented): only nodes/, core/ and scripts/run_nascence.py are scanned (labs and
one-off scripts are not Du's loop). A prompt reached through a wrapper this file does not know by name, or
a raw post whose URL is built on an earlier line, is not seen; add the wrapper's name below when you
introduce one.

CALLERS (J-3006, F-3704): a registered key can also be asked "who calls this?" without a grep. The first
reader pass said core.left_lane:grade_self_revision had no caller, and the registry row went DEAD, because the
one real call is `_ll4.grade_self_revision(...)` after `from core import left_lane as _ll4`: the receiver text
never contains "left_lane". callers() resolves import bindings the way Python does (per scope, so a function-local
`from core import x as _a` counts): `import a.b as z`, `import a.b`, `from a import b as z` (module or function),
`from a.b import f as g`, relative imports, a full dotted chain such as `core.left_lane.fn`, plus `self.m(...)`
inside the defining module and bare same-module names. A reference that is not called (a function passed as a
callback, e.g. asyncio.to_thread(_ll.fn, ...)) is reported with how="ref". NOT seen (documented limit):
getattr(mod, "fn"), calls through an instance of another module's class (obj.method), string dispatch.

Run:  python scripts/prompt_site_census.py            -> table
      python scripts/prompt_site_census.py --json     -> one JSON row per site
      python scripts/prompt_site_census.py --callers  -> resolved callers per site; then the keys whose caller
                                                         count is 0 WITHOUT alias resolution and >0 with it
      python scripts/prompt_site_census.py --callers --key <census key>   -> callers of one key, one per line
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("nodes", "core")
SCAN_FILES = ("scripts/run_nascence.py",)
SKIP_FILES = {"core/model_client.py"}          # the client itself is the transport, not a prompt
SKIP_PARTS = {"__pycache__", "graphify-out"}

# names that send a prompt through core.model_client (or a parameter that is that client)
CALL_NAMES = {"call_node", "call_node_json", "call_node_prose", "call_json", "call_text", "call_llm", "_call_llm", "ask_llm",
              "create_chat_completion"}
# names too generic to trust unless the first argument looks like a lane/URL expression
GENERIC_CALL_NAMES = {"call", "_call", "call_fn"}
LANE_ARG = re.compile(r"url|hub|SERVE_CHAINS|_URLS|urls", re.I)
# judge_panel entry points a module can use to send ITS OWN system prompt to a judge hub. rule/rule_detail take
# (system, user, key, ...); _ask is the single-judge primitive (session, url, system, user, key, ...) that
# core/refinery.py (J-3238) and core/ground_grade.py reach through judge_panel from another module. Before
# J-3443 (F-4071) _ask was not listed, so a prompt sent that way was invisible and `check` stayed green
# unregistered. A new entry needs the zero-based position of its system-prompt argument below.
JUDGE_FUNCS = {"rule", "rule_detail", "_ask"}
JUDGE_SYSTEM_ARG = {"rule": 0, "rule_detail": 0, "_ask": 2}
HTTP_FUNCS = {"post", "urlopen", "Request"}
HTTP_MARKS = ("/api/chat", "/v1/chat", "/api/generate")
IDLE_FILE = "nodes/inner_monologue_node.py"


def _short(node, n=70) -> str:
    try:
        s = ast.unparse(node)
    except Exception:
        s = "?"
    return " ".join(s.split())[:n]


def _scopes(tree):
    out = []

    def walk(n, pre):
        for c in ast.iter_child_nodes(n):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append((c.lineno, getattr(c, "end_lineno", c.lineno), pre + c.name))
                walk(c, pre + c.name + ".")
            elif isinstance(c, ast.ClassDef):
                walk(c, pre + c.name + ".")
            else:
                walk(c, pre)

    walk(tree, "")
    return out


def _enclosing(scopes, ln):
    hits = [s for s in scopes if s[0] <= ln <= s[1]]
    return max(hits, key=lambda s: s[0])[2] if hits else "<module>"


def _files():
    for d in SCAN_DIRS:
        for f in sorted((ROOT / d).rglob("*.py")):
            if SKIP_PARTS & set(f.parts):
                continue
            if f.relative_to(ROOT).as_posix() in SKIP_FILES:
                continue
            yield f
    for rel in SCAN_FILES:
        f = ROOT / rel
        if f.exists():
            yield f


def _scan_file(f: Path):
    rel = f.relative_to(ROOT).as_posix()
    mod = rel[:-3].replace("/", ".")
    try:
        tree = ast.parse(f.read_text(encoding="utf-8-sig", errors="replace"))
    except SyntaxError as e:
        print(f"# SYNTAX ERROR {rel}: {e}", file=sys.stderr)
        return [], 0
    scopes = _scopes(tree)

    aliases = {}            # local name -> canonical call name, for "from ...model_client import x as y"
    jp_mods, jp_funcs = set(), {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            m = n.module or ""
            for a in n.names:
                local = a.asname or a.name
                if "model_client" in m and a.name in CALL_NAMES:
                    aliases[local] = a.name
                if m.endswith("judge_panel") and a.name in JUDGE_FUNCS:
                    jp_funcs[local] = a.name
                if a.name == "judge_panel":
                    jp_mods.add(local)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.endswith("judge_panel"):
                    jp_mods.add(a.asname or a.name.split(".")[-1])

    rows = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            for b in n.bases:
                bname = b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "")
                if bname == "NodeBase":
                    rows.append(dict(kind="node", via="NodeBase subclass", module=mod, fn=n.name, line=n.lineno,
                                     lane="-", system="system_prompt + _build_prompt", tok="-", temp="-"))
            continue
        if not isinstance(n, ast.Call):
            continue
        f_ = n.func
        name = f_.attr if isinstance(f_, ast.Attribute) else getattr(f_, "id", "")
        recv = _short(f_.value, 40) if isinstance(f_, ast.Attribute) else ""
        kw = {k.arg: _short(k.value, 40) for k in n.keywords if k.arg}
        canon = aliases.get(name, name if name in CALL_NAMES else None)
        if canon is None and name in GENERIC_CALL_NAMES and n.args and LANE_ARG.search(_short(n.args[0], 80)):
            canon = name
        if canon:
            rows.append(dict(kind="call", via=canon if canon == name else f"{canon} (as {name})", module=mod,
                             fn=_enclosing(scopes, n.lineno), line=n.lineno,
                             lane=_short(n.args[0], 40) if n.args else "-",
                             system=_short(n.args[1], 90) if len(n.args) > 1 else kw.get("system", "-"),
                             tok=kw.get("max_tokens", "-"), temp=kw.get("temperature", "-")))
        elif (name in JUDGE_FUNCS and (recv in jp_mods or recv.split(".")[-1] == "judge_panel"))                 or (isinstance(f_, ast.Name) and name in jp_funcs):
            canon_j = name if isinstance(f_, ast.Attribute) else jp_funcs[name]
            pos = JUDGE_SYSTEM_ARG.get(canon_j, 0)
            rows.append(dict(kind="judge", via=f"judge_panel.{canon_j}", module=mod, fn=_enclosing(scopes, n.lineno),
                             line=n.lineno, lane="judge_panel",
                             system=_short(n.args[pos], 90) if len(n.args) > pos else kw.get("system", "-"),
                             tok=kw.get("num_predict", "-"), temp="0.0"))
        elif name in HTTP_FUNCS:
            txt = _short(n, 240)
            if any(m in txt for m in HTTP_MARKS):
                rows.append(dict(kind="raw_http", via="raw http", module=mod, fn=_enclosing(scopes, n.lineno),
                                 line=n.lineno, lane=txt[:60], system="(payload)", tok="-", temp="-"))

    seed_parts = 0
    if rel == IDLE_FILE:
        seed_parts = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                         and n.func.attr == "append" and _short(n.func.value, 20) == "seed_parts")
    return rows, seed_parts


def census():
    """-> (sites, seed_parts). Each site dict has: key, kind, via, module, fn, line, lane, system, tok, temp."""
    sites, seed_parts = [], 0
    for f in _files():
        rows, sp = _scan_file(f)
        seed_parts += sp
        sites.extend(rows)
    count = {}
    for r in sites:
        count[(r["module"], r["fn"])] = count.get((r["module"], r["fn"]), 0) + 1
    seen = {}
    for r in sorted(sites, key=lambda r: (r["module"], r["line"])):
        base = f"{r['module']}:{r['fn']}"
        if r["kind"] == "node" or count[(r["module"], r["fn"])] == 1:
            key = base
        else:
            key = f"{base}#{' '.join(r['system'].split())[:50]}"
        seen[key] = seen.get(key, 0) + 1
        r["key"] = key if seen[key] == 1 else f"{key}@{seen[key]}"
    return sorted(sites, key=lambda r: (r["module"], r["line"])), seed_parts


# ---------------------------------------------------------------------------------------------------------------
# Caller resolution (J-3006). Separate from census(): it never changes which sites or keys the census reports.
# ---------------------------------------------------------------------------------------------------------------

def _modname(rel: str) -> str:
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _caller_files(root: Path):
    for d in SCAN_DIRS:
        if (root / d).is_dir():
            for f in sorted((root / d).rglob("*.py")):
                if not SKIP_PARTS & set(f.parts):
                    yield f
    for rel in SCAN_FILES:
        f = root / rel
        if f.exists():
            yield f


def _known_modules(root: Path, files) -> set:
    mods = set()
    for f in files:
        parts = _modname(f.relative_to(root).as_posix()).split(".")
        for i in range(1, len(parts) + 1):          # every package prefix counts as a module too
            mods.add(".".join(parts[:i]))
    return mods


def _scope_bindings(tree, pkg, modules, aliases):
    """{scope node (Module / function): {local name: [binding, ...]}} from the import statements that sit
    directly in that scope. binding = ("mod", dotted, via_as) or ("func", dotted_module, name, via_as).
    With aliases=False any `x as y` import is ignored: that reproduces a plain-grep reader."""
    out = {}

    def add(scope, local, b):
        out.setdefault(scope, {}).setdefault(local, []).append(b)

    def resolve_from(n):
        base = n.module or ""
        if n.level:
            keep = pkg[:max(0, len(pkg) - (n.level - 1))]
            return ".".join(keep + ([base] if base else []))
        return base

    def walk(node, scope):
        for c in ast.iter_child_nodes(node):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                walk(c, c)
                continue
            if isinstance(c, ast.Import):
                for a in c.names:
                    if a.asname:
                        if aliases:
                            add(scope, a.asname, ("mod", a.name, True))
                    else:
                        top = a.name.split(".")[0]
                        add(scope, top, ("mod", top, False))
            elif isinstance(c, ast.ImportFrom):
                src = resolve_from(c)
                for a in c.names:
                    if a.name == "*":
                        continue
                    if a.asname and not aliases:
                        continue
                    local = a.asname or a.name
                    full = f"{src}.{a.name}" if src else a.name
                    if full in modules:
                        add(scope, local, ("mod", full, bool(a.asname)))
                    else:
                        add(scope, local, ("func", src, a.name, bool(a.asname)))
            walk(c, scope)

    walk(tree, tree)
    return out


def _chain(node):
    """a.b.c -> ("a", ["b", "c"]); None when the base is not a plain name (a call result, a subscript...)."""
    attrs = []
    while isinstance(node, ast.Attribute):
        attrs.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        return node.id, list(reversed(attrs))
    return None


_PARSED = {}


def _file_callers(f: Path, root: Path, modules: set, wanted: set, aliases: bool, method_names: dict):
    """-> [(target (module, name), row)] for every reference in file f that resolves to a wanted (module, name)."""
    rel = f.relative_to(root).as_posix()
    mod = _modname(rel)
    pkg = rel[:-3].split("/")[:-1]
    ck = (str(f), f.stat().st_mtime_ns)
    if ck not in _PARSED:                           # parsed once per file, shared by the with/without-alias passes
        try:
            tree = ast.parse(f.read_text(encoding="utf-8-sig", errors="replace"))
        except SyntaxError:
            _PARSED[ck] = None
        else:
            parent = {}
            for p_ in ast.walk(tree):
                for c in ast.iter_child_nodes(p_):
                    parent[c] = p_
            _PARSED[ck] = (tree, parent, _scopes(tree))
    if _PARSED[ck] is None:
        return []
    tree, parent, scopes = _PARSED[ck]
    bindings = _scope_bindings(tree, pkg, modules, aliases)

    def scope_stack(n):
        st, cur = [], parent.get(n)
        while cur is not None:
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                st.append(cur)
            cur = parent.get(cur)
        st.append(tree)
        return st                                   # innermost first, module last

    def lookup(n, name):
        for sc in scope_stack(n):
            hit = bindings.get(sc, {}).get(name)
            if hit:
                return hit
        return None

    wanted_names = {n_ for _, n_ in wanted}
    # a wanted function imported under another name (`from x import f as g`) is referenced by that local name
    func_locals = {loc for sc in bindings.values() for loc, bs in sc.items()
                   for b in bs if b[0] == "func" and (b[1], b[2]) in wanted}
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Name, ast.Attribute)):
            continue
        if not isinstance(getattr(n, "ctx", None), ast.Load):
            continue
        par = parent.get(n)
        if isinstance(par, ast.Attribute) and par.value is n:
            continue                                # only the outermost end of a chain is a root
        ch = _chain(n)
        if ch is None:
            if not (isinstance(n, ast.Attribute) and n.attr in method_names):
                continue
            ch = (None, [n.attr])                   # receiver is a call result / subscript: only a name match is possible
        base, attrs = ch
        if (attrs[-1] if attrs else base) not in wanted_names and not (not attrs and base in func_locals):
            continue                                # cheap prune: the last name must be one we look for
        is_call = isinstance(par, ast.Call) and par.func is n
        hits = []                                   # (module, name, how, via_alias)
        bs = lookup(n, base) if base else None
        if bs:
            for b in bs:
                if b[0] == "func" and not attrs:
                    hits.append((b[1], b[2], "imported-name", b[3]))
                elif b[0] == "mod" and attrs:
                    m = b[1]
                    for i, part in enumerate(attrs):
                        if i == len(attrs) - 1:
                            hits.append((m, part, "module-attr", b[2]))
                        elif f"{m}.{part}" in modules:
                            m = f"{m}.{part}"
                        else:
                            break
        elif base is None:
            pass
        elif not attrs:
            hits.append((mod, base, "same-module", False))
        elif base in ("self", "cls") and len(attrs) == 1:
            hits.append((mod, attrs[0], "method", False))
        if attrs and attrs[-1] in method_names:
            # a method of a class is usually called through an instance (`self.scholar.consult(...)`): the
            # receiver's class is not knowable from the AST, so a bare name match is reported, flagged weak.
            done = {(tm, tn) for tm, tn, _, _ in hits}
            for tm in method_names[attrs[-1]]:
                if (tm, attrs[-1]) not in done:
                    hits.append((tm, attrs[-1], "method-name-only", False))
        for tm, tn, how, via_alias in hits:
            if (tm, tn) not in wanted:
                continue
            ln = getattr(n, "lineno", 0)
            out.append(((tm, tn), dict(module=mod, fn=_enclosing(scopes, ln), line=ln,
                                       how=how if (is_call or how == "method-name-only") else "ref",
                                       weak=(how == "method-name-only"), via_alias=via_alias,
                                       text=_short(n, 60))))
    return out


def callers(keys, root: Path | None = None, aliases: bool = True) -> dict:
    """{census key: [caller row, ...]} for every key given (module:Qual.function[#..][@n]).
    A caller row: module, fn (the enclosing function), line, how (imported-name | module-attr | same-module |
    method | method-name-only | ref), weak (True only for method-name-only: same method name on an unresolved
    receiver, which may be a different class), via_alias (the binding that made it resolvable was an `as` rename), text. A function's own
    recursion is dropped. aliases=False ignores every `as` import: the old plain-grep view, for comparison."""
    root = Path(root) if root else ROOT
    files = list(_caller_files(root))
    modules = _known_modules(root, files)
    tgt = {}                                        # key -> (module, name, qual)
    for k in keys:
        m, _, rest = k.partition(":")
        qual = rest.split("#", 1)[0]
        tgt[k] = (m, qual.split(".")[-1], qual)
    wanted = {(m, n) for m, n, _ in tgt.values()}
    method_names = {}                               # method name -> modules that define a target of that name
    for m, n, qual in tgt.values():
        if "." in qual:
            method_names.setdefault(n, set()).add(m)
    found = {}
    for f in files:
        for (tm, tn), row in _file_callers(f, root, modules, wanted, aliases, method_names):
            found.setdefault((tm, tn), []).append(row)
    res = {}
    for k, (m, n, qual) in tgt.items():
        rows = []
        for r in found.get((m, n), []):
            if r["module"] == m and (r["fn"] == qual or r["fn"].startswith(qual + ".")):
                continue                            # recursion / its own nested helpers
            rows.append(r)
        res[k] = sorted(rows, key=lambda r: (r["module"], r["line"]))
    return res


def _main_callers(sites, argv) -> int:
    keys = [r["key"] for r in sites]
    if "--key" in argv:
        k = argv[argv.index("--key") + 1]
        if k not in keys:
            print(f"no such census key: {k}", file=sys.stderr)
            return 2
        keys = [k]
    full = callers(keys, aliases=True)
    plain = callers(keys, aliases=False)
    if "--key" in argv:
        for r in full[keys[0]]:
            print(f"{r['module'].replace('.', '/')}.py:{r['line']}  in {r['fn']}  {r['how']}"
                  f"{' (via alias)' if r['via_alias'] else ''}{' (WEAK: name only)' if r['weak'] else ''}  {r['text']}")
        print(f"{len(full[keys[0]])} caller(s)")
        return 0
    if "--json" in argv:
        for k in keys:
            print(json.dumps({"key": k, "callers": full[k], "callers_without_alias_resolution": len(plain[k])},
                             ensure_ascii=False))
        return 0
    strong = {k: [r for r in full[k] if not r["weak"]] for k in keys}
    none_full = [k for k in keys if not strong[k]]
    changed = [k for k in keys if not [r for r in plain[k] if not r["weak"]] and strong[k]]
    print(f"{len(keys)} keys: {len(keys) - len(none_full)} with a resolved caller, {len(none_full)} with none "
          f"({len([k for k in none_full if full[k]])} of those have a weak name-only match)")
    print(f"changed from no caller to a caller once import aliases are resolved: {len(changed)}")
    for k in changed:
        r = strong[k][0]
        print(f"  {k}  <- {r['module'].replace('.', '/')}.py:{r['line']} ({r['fn']}, {r['how']})")
    print("still no resolved caller (a callback table, getattr or an instance method is invisible here; "
          "read the code before calling any of these dead):")
    for k in none_full:
        w = full[k][0] if full[k] else None
        print(f"  {k}" + (f"   (weak: {w['module'].replace('.', '/')}.py:{w['line']} {w['text']})" if w else ""))
    return 0


def main(argv) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sites, seed_parts = census()
    if "--callers" in argv:
        return _main_callers(sites, argv)
    if "--json" in argv:
        for r in sites:
            print(json.dumps(r, ensure_ascii=False))
        print(json.dumps({"seed_parts": seed_parts}))
        return 0
    by_kind = {}
    for r in sites:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
    print(f"{len(sites)} prompt sites in {len({r['module'] for r in sites})} modules  {by_kind}  "
          f"idle seed_parts.append sites: {seed_parts}")
    for r in sites:
        print(f"{r['kind']:8s} {r['key']:78s} L{r['line']:<5d} tok={r['tok'][:10]:10s} T={r['temp'][:6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

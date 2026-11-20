"""J-3469: the cheap check behind UDMS roadmap item 8 -- is a udms_hygiene "dead function" lead really unreferenced?

udms_hygiene's static call graph reports a function dead when it sees no resolvable caller. Two failure modes make
that list over-count (found 2026-11-07, F-4098 follow-up): (1) a call through a module alias attribute
(`_hab_wonder.observe_wonder(...)`) is not resolved, and (2) a word-boundary text grep over-counts the other way,
because docstrings, comments, state-dict keys and the .claude/worktrees copies all match. This tool reads the
TOKEN stream instead (comments and docstring bodies are never NAME tokens), so a NAME token is code and a STRING
token is a dispatch key / patch target / state key, and it sorts every lead into one verdict:

  REAL_CALL    a NAME token in a non-test, non-scripts module other than the one defining it
  OWN_CALL     only called inside its own module (still live code)
  SCRIPT_ONLY  referenced by scripts/ (tools, labs) but not by core/nodes/hud
  TEST_ONLY    referenced only by scripts/*test* files
  STRING_ONLY  no code reference, but the bare name appears as a short string literal (dispatch key, patch target,
               state-dict key -- check by hand whether it is a getattr/dispatch)
  DEAD         no NAME token and no string literal anywhere (it may still be named in a docstring or comment)

Read-only. Usage (from any worktree; scans the tree this file lives in):
    python scripts/hygiene_ref_scan_J3469.py docs/lab/J-3469_data/leads.json [--out results.json]
leads.json: {"<group>": ["core/x.py::func", ...], ...}.  Skips .git, .claude, data, graphify-out, public_repo, docs_site.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SKIP = {".git", "graphify-out", "public_repo", "docs_site", "data", "__pycache__", ".claude", "node_modules"}
_TESTY = re.compile(r"(^|/)(_?test)[^/]*$|(^|/)scripts/(_?test|test_)")


def _is_script(rel: str) -> bool:
    return rel.startswith("scripts/")


def _is_test(rel: str) -> bool:
    return bool(_TESTY.search(rel)) or "/_test" in rel or "/test_" in rel


def scan(root: Path, leads: list[str]) -> dict:
    """leads: ["core/x.py::func", ...] -> {lead: {verdict, ext_prod, own, scripts, tests, strings, first_refs}}."""
    names = {l.split("::", 1)[1] for l in leads}
    code: dict[str, list] = {n: [] for n in names}
    strs: dict[str, list] = {n: [] for n in names}
    unparsed: list[str] = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in _SKIP]
        for f in fn:
            if not f.endswith(".py"):
                continue
            p = Path(dp) / f
            rel = str(p.relative_to(root)).replace("\\", "/")
            try:
                toks = list(tokenize.generate_tokens(io.StringIO(p.read_text(encoding="utf-8", errors="replace")).readline))
            except Exception:
                unparsed.append(rel)
                continue
            prev = None
            for t in toks:
                if t.type == tokenize.NAME and t.string in names:
                    if not (prev is not None and prev.string in ("def", "class")):
                        code[t.string].append((rel, t.start[0]))
                elif t.type == tokenize.STRING and len(t.string) < 80 and not (
                        prev is None or prev.type in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT)):
                    # a string that starts a statement is a docstring / bare expression, not a key or patch target
                    for n in names:
                        if n in t.string and re.search(r"\b" + re.escape(n) + r"\b", t.string):
                            strs[n].append((rel, t.start[0]))
                if t.type not in (tokenize.NL, tokenize.COMMENT):
                    prev = t
    out: dict = {}
    for lead in leads:
        mod, name = lead.split("::", 1)
        c = code[name]
        ext = [x for x in c if x[0] != mod and not _is_script(x[0])]
        own = [x for x in c if x[0] == mod]
        scr = [x for x in c if x[0] != mod and _is_script(x[0]) and not _is_test(x[0])]
        tst = [x for x in c if x[0] != mod and _is_test(x[0])]
        s = strs[name]
        if ext:
            verdict = "REAL_CALL"
        elif own:
            verdict = "OWN_CALL"
        elif scr:
            verdict = "SCRIPT_ONLY"
        elif tst:
            verdict = "TEST_ONLY"
        elif s:
            verdict = "STRING_ONLY"
        else:
            verdict = "DEAD"
        out[lead] = {"verdict": verdict, "ext_prod": len(ext), "own": len(own), "scripts": len(scr), "tests": len(tst),
                     "strings": len(s), "first_refs": [f"{r}:{ln}" for r, ln in (ext + own + scr + tst + s)[:3]]}
    out["_unparsed"] = unparsed
    return out


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("leads_json")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    groups = json.loads(Path(a.leads_json).read_text(encoding="utf-8"))
    res: dict = {}
    for g, leads in groups.items():
        if isinstance(leads, list):
            r = scan(ROOT, leads)
            res[g] = r
            from collections import Counter
            print(g, dict(Counter(v["verdict"] for k, v in r.items() if not k.startswith("_"))))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

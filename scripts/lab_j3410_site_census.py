"""J-3410 (F-4044): census of Du prompt strings that ship an option placeholder or a pre-filled example.

Walks core/, nodes/ and scripts/run_nascence.py with ast, takes every string constant / f-string of 25+ characters and
extracts each JSON-shaped answer-schema fragment, then classifies the fragment:

  bool_pipe        {"k": true|false}                   unfilled two-option placeholder, option order = text order
  bool_or          {"k": true or false} / <true or false>
  bool_pair        {"k": true} or {"k": false}         both literals, fixed order
  enum_pipe        {"k": "a|b|c"}                      unfilled multi-option placeholder
  enum_or          {"k": "a" or "b" or "c"}
  prefilled_bool   {"k": true, ...} / {"k": false, ...} ONE literal boolean named as the example answer
  prefilled_word   {"k": "word"} a concrete enum word as the example answer (the F-4044 A form)
  prefilled_num    {"k": 0.0} a number as the example answer

Read-only. The output is the machine list the J-3410 report is built from (docs/lab/J-3410_data/site_census.json); the
mapping from a site to a registry row (P-NNNN) is done by file/function in the report, not guessed here.

    python scripts/lab_j3410_site_census.py [--out PATH]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_KEYVAL = re.compile(r'"(?P<k>[A-Za-z_]+|%s)"\s*:\s*(?P<v>"[^"\n]{0,120}"|<[^<>\n]{0,120}>|true\s*\|\s*false|false\s*\|\s*true|'
                     r'true\s+or\s+false|false\s+or\s+true|true|false|null|-?\d+(?:\.\d+)?)')
_PAIR = re.compile(r'\{\s*"(?P<k>[A-Za-z_]+|%s)"\s*:\s*(?P<a>true|false)\s*\}\s*or\s*\{\s*"(?P=k)"\s*:\s*(?P<b>true|false)\s*\}')
_ENUM_PIPE = re.compile(r'^[<"]?([A-Za-z_]{2,24}(?:\s?\|\s?[A-Za-z_]{2,24})+)[>"]?$')
_ENUM_OR = re.compile(r'"([A-Za-z_ ]{1,24})"\s+or\s+"([A-Za-z_ ]{1,24})"(?:\s+or\s+"([A-Za-z_ ]{1,24})")?')


def classify(frag_key: str, raw: str):
    v = raw.strip()
    if v.startswith("<") and v.endswith(">") and re.fullmatch(r'<\s*(?:true|false)\s*(?:\||or)\s*(?:true|false)\s*>', v):
        v = v[1:-1].strip()
    if re.fullmatch(r'true\s*\|\s*false|false\s*\|\s*true', v):
        return "bool_pipe", re.split(r'\s*\|\s*', v)
    if re.fullmatch(r'true\s+or\s+false|false\s+or\s+true', v):
        return "bool_or", re.split(r'\s+or\s+', v)
    inner = v[1:-1] if (v[:1] in '"<' and v[-1:] in '">') else v
    m = _ENUM_PIPE.match(v) or _ENUM_PIPE.match(inner)
    if m:
        return "enum_pipe", [x.strip() for x in m.group(1).split("|")]
    if v in ("true", "false"):
        return "prefilled_bool", [v]
    if re.fullmatch(r'-?\d+(?:\.\d+)?', v):
        return "prefilled_num", [v]
    if v.startswith("<"):
        return "angle_free", [v[:60]]
    if v.startswith('"'):
        word = v.strip('"')
        if re.fullmatch(r'[a-z_]{3,24}', word) and word not in ("none",):
            return "prefilled_word", [word]
        return "free_text", [word[:40]]
    return "other", [v[:40]]


def walk(root: Path = ROOT):
    files = [p for d in ("core", "nodes") for p in (root / d).rglob("*.py")]
    files.append(root / "scripts" / "run_nascence.py")
    out, seen = [], set()
    for p in sorted(files):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception:
            continue
        # innermost enclosing def name per node line, for reporting
        spans = []
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                spans.append((n.lineno, getattr(n, "end_lineno", n.lineno), n.name))
        for n in ast.walk(tree):
            s = None
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                s = n.value
            elif isinstance(n, ast.JoinedStr):
                s = "".join(v.value if isinstance(v, ast.Constant) else "{}" for v in n.values)
            if not s or len(s) < 25:
                continue
            fn = ""
            for a, b, name in spans:
                if a <= n.lineno <= b:
                    fn = name
            rel = p.relative_to(root).as_posix()
            for m in _PAIR.finditer(s):
                key = (rel, n.lineno, m.group("k"), "bool_pair")
                if key not in seen:
                    seen.add(key)
                    out.append({"file": rel, "line": n.lineno, "func": fn, "key": m.group("k"), "form": "bool_pair",
                                "options": [m.group("a"), m.group("b")]})
            if '"' not in s or ":" not in s:
                continue
            for m in _KEYVAL.finditer(s):
                form, opts = classify(m.group("k"), m.group("v"))
                if form in ("free_text", "angle_free", "other", "prefilled_num"):
                    continue
                key = (rel, n.lineno, m.group("k"), form)
                if key in seen:
                    continue
                seen.add(key)
                out.append({"file": rel, "line": n.lineno, "func": fn, "key": m.group("k"), "form": form, "options": opts})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3410_data" / "site_census.json"))
    a = ap.parse_args(argv)
    rows = walk()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    from collections import Counter
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(len(rows), "fragments", dict(Counter(r["form"] for r in rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

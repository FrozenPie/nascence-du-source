#!/usr/bin/env python3
"""function_size_ratchet.py -- stop the two god functions growing (D-0878, plan god_function_split).

Founder ruling D-0878 (2026-11-20): new idle-thought seed parts and new cycle stages go in as a helper in
their own module, called by one line. They do not go in as a new block inside InnerMonologueNode._think or
Orchestrator._run_cycle_impl. This script is the check behind that rule. It is read-only on the code; the
only file it writes is its own baseline, and only on `accept`.

  python scripts/function_size_ratchet.py check                 exit 1 if a watched function is longer than its baseline
  python scripts/function_size_ratchet.py accept --why "..."    record today's sizes as the new baseline, with the reason
  python scripts/function_size_ratchet.py show                  sizes now, baseline, and the accept history

A function that shrank passes, and `check` says so; run `accept` then so the lower size becomes the baseline
(the ratchet only tightens when someone records it). A watched function that cannot be found fails the check:
a rename or a move must be recorded, not missed.

The watch list lives in the baseline file. To watch another function, add it there through `accept --add
path::Class.func` (never by hand-editing).
"""
import argparse
import ast
import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "docs" / "function_size_baseline.json"
DEFAULT_WATCH = ["nodes/inner_monologue_node.py::InnerMonologueNode._think",
                 "core/orchestrator.py::Orchestrator._run_cycle_impl"]


def measure(spec, root=ROOT):
    """Line count of `path::Class.func` (or `path::func`), or None if it is not there."""
    rel, _, qual = spec.partition("::")
    try:
        tree = ast.parse((root / rel).read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    body = tree.body
    parts = qual.split(".")
    for i, name in enumerate(parts):
        last = i == len(parts) - 1
        kinds = (ast.FunctionDef, ast.AsyncFunctionDef) if last else (ast.ClassDef,)
        hit = [n for n in body if isinstance(n, kinds) and n.name == name]
        if not hit:
            return None
        if last:
            return hit[0].end_lineno - hit[0].lineno + 1
        body = hit[0].body
    return None


def load(path):
    if not path.exists():
        return {"schema": 1, "functions": {}, "history": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def cmd_check(args):
    data = load(args.baseline)
    if not data["functions"]:
        print("ratchet: no baseline yet. Run: python scripts/function_size_ratchet.py accept --why \"first baseline\"")
        return 1
    bad = 0
    for spec, base in sorted(data["functions"].items()):
        now = measure(spec, args.root)
        if now is None:
            bad += 1
            print(f"MISSING  {spec}: not found (baseline {base} lines). If it was renamed or moved, record it with accept --why.")
        elif now > base:
            bad += 1
            print(f"GREW     {spec}: {base} -> {now} lines (+{now - base}).")
        elif now < base:
            print(f"shrank   {spec}: {base} -> {now} lines ({now - base}). Run accept --why to lock the lower size in.")
        else:
            print(f"ok       {spec}: {now} lines.")
    if bad:
        print("\nRED. Rule (CLAUDE.md, D-0878): a new seed part or cycle stage is a helper in its own module, called by one "
              "line; it is not a new block inside the function. Move the new code out. If the growth is real and has to "
              "stay (a one-line call to a new helper, a fix inside an existing block), record it:\n"
              "  python scripts/function_size_ratchet.py accept --why \"J-NNNN: what grew and why it could not live outside\"")
        return 1
    print("ratchet: green.")
    return 0


def cmd_accept(args):
    why = (args.why or "").strip()
    if len(why) < 12:
        print("accept: --why is required and must say what grew and why (at least a short sentence).")
        return 2
    data = load(args.baseline)
    specs = set(data["functions"]) or set(DEFAULT_WATCH)
    specs |= set(args.add or [])
    changes, new = [], {}
    for spec in sorted(specs):
        now = measure(spec, args.root)
        if now is None:
            print(f"accept: cannot find {spec}; nothing written. Fix the spec (path::Class.func) and retry.")
            return 2
        old = data["functions"].get(spec)
        new[spec] = now
        if old != now:
            changes.append({"function": spec, "from": old, "to": now})
    if not changes:
        print("accept: sizes already match the baseline; nothing written.")
        return 0
    data["functions"] = new
    data["history"].append({"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                            "why": why, "by": args.by, "changes": changes})
    save(args.baseline, data)
    for c in changes:
        print(f"accepted {c['function']}: {c['from']} -> {c['to']}")
    print(f"baseline written: {args.baseline}")
    return 0


def cmd_show(args):
    data = load(args.baseline)
    for spec, base in sorted(data["functions"].items()):
        print(f"{spec}: now {measure(spec, args.root)}, baseline {base}")
    hist = data["history"]
    grew = sum(1 for h in hist for c in h["changes"] if c["from"] is not None and c["to"] > c["from"])
    print(f"accepts: {len(hist)} (of which growth entries: {grew})")
    for h in hist[-args.n:]:
        ch = "; ".join(f"{c['function'].split('::')[1]} {c['from']}->{c['to']}" for c in h["changes"])
        print(f"  {h['ts']} [{h['by']}] {ch} | {h['why'][:140]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", type=Path, default=BASELINE, help="baseline file (tests pass a temp path)")
    ap.add_argument("--root", type=Path, default=ROOT, help="repo root to measure (tests pass a temp tree)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    a = sub.add_parser("accept")
    a.add_argument("--why", required=True)
    a.add_argument("--by", default="claude")
    a.add_argument("--add", action="append", help="also watch path::Class.func (repeatable)")
    s = sub.add_parser("show")
    s.add_argument("-n", type=int, default=10)
    args = ap.parse_args()
    return {"check": cmd_check, "accept": cmd_accept, "show": cmd_show}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

"""closure_producer Phase 0 (D-0791): label legacy resolved frontier rows that carry no resolved_how as
resolved_how="lexical". Before 2026-11-16 only frontier.resolve() (the Follow Line) wrote a resolved_how; every
other resolved row was closed by the lexical resolver (frontier.resolve_if_addressed), the only other code path
that sets status "resolved". The rows stay resolved; only the label is added (plus resolved_how_backfilled: true,
so a backfilled label can always be told from one written at close time).

RUN ONLY WHILE DU IS DOWN. Du rewrites data/frontier.json whole; a write from here while he runs would lose his
changes or be lost to his.

  python scripts/closure_producer_backfill_lexical.py                    dry run on data/frontier.json (default)
  python scripts/closure_producer_backfill_lexical.py --file PATH        dry run on another file (a copy)
  python scripts/closure_producer_backfill_lexical.py --write            apply

--write refuses if the file's size, mtime or content hash changed between the read and the write, and keeps the
previous file as frontier.json.bak_closure_producer_<stamp> beside it. The light sidecar is not touched (it holds
open rows and status counts only, and neither changes).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "frontier.json"


def _fingerprint(path: Path) -> tuple:
    st = path.stat()
    return st.st_size, st.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()


def plan(data: dict) -> tuple[list, Counter]:
    """(rows to label, Counter of resolved_how among all resolved rows before the change)."""
    todo, hows = [], Counter()
    for q in data.get("questions", []) or []:
        if q.get("status") != "resolved":
            continue
        hows[str(q.get("resolved_how") or "(none)")] += 1
        if not q.get("resolved_how"):
            todo.append(q)
    return todo, hows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file", default=str(DEFAULT), help="frontier json to read (default: data/frontier.json)")
    ap.add_argument("--write", action="store_true", help="apply (default is a dry run)")
    args = ap.parse_args(argv)
    path = Path(args.file)
    if not path.exists():
        print(f"no such file: {path}")
        return 2
    before = _fingerprint(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    todo, hows = plan(data)
    with_finding = sum(1 for q in todo if q.get("finding"))
    ts = sorted(float(q.get("resolved_ts") or 0) for q in todo)
    print(f"file              : {path}")
    print(f"resolved rows     : {sum(hows.values())}   by resolved_how now: {dict(hows)}")
    print(f"to label lexical  : {len(todo)}   ({with_finding} of them carry a finding)")
    if ts:
        print(f"their resolved_ts : {time.strftime('%Y-%m-%d', time.localtime(ts[0]))} .. "
              f"{time.strftime('%Y-%m-%d', time.localtime(ts[-1]))}")
    if not args.write:
        print("DRY RUN: nothing written. Re-run with --write while Du is down.")
        return 0
    if not todo:
        print("nothing to do.")
        return 0
    for q in todo:
        q["resolved_how"] = "lexical"
        q["resolved_how_backfilled"] = True
    payload = json.dumps(data, ensure_ascii=False)
    if _fingerprint(path) != before:
        print("REFUSED: the frontier file changed while this ran (is Du up?). Nothing written.")
        return 3
    bak = path.with_name(path.name + ".bak_closure_producer_" + time.strftime("%Y%m%d_%H%M%S"))
    shutil.copyfile(path, bak)
    tmp = path.with_name(path.name + ".closure_producer.tmp")
    tmp.write_text(payload, encoding="utf-8")
    if _fingerprint(path) != before:
        tmp.unlink()
        print("REFUSED: the frontier file changed while this ran (is Du up?). Nothing written.")
        return 3
    os.replace(tmp, path)
    print(f"WROTE: {len(todo)} rows labelled lexical. Previous file kept as {bak.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

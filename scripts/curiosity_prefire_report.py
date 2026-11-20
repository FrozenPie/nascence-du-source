"""J-3219 / D-0608 -- THE READER for data/curiosity_prefire_shadow.jsonl. Prints the paired-picks summary, the
defeater verdict, and the rows where the check would have picked a different question than the one that fired.
Read-only. Usage: python scripts/curiosity_prefire_report.py [--path PATH] [--show N]
Quote no number from this before scripts/curiosity_prefire_control.py's separation on the labelled set is read."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import curiosity_prefire as cp  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=None)
    ap.add_argument("--show", type=int, default=8)
    a = ap.parse_args()
    path = Path(a.path) if a.path else cp._SHADOW
    st = cp.status(path)
    print(json.dumps(st, indent=1))
    if not st.get("rows"):
        return
    print("\nD-0608 defeater (same pick > %.0f%% or near-constant scores): %s" % (cp.DEFEATER_SAME_PICK * 100, st["defeater"]))
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    diff = [r for r in rows if r.get("agree") is False]
    print("\n%d rows where the check disagreed with what fired (showing last %d):" % (len(diff), a.show))
    for r in diff[-a.show:]:
        print("  fired #%s: %s\n  would #%s: %s\n" % (r.get("fired_i"), r.get("fired_q"), r.get("would_pick_i"), r.get("would_pick_q")))


if __name__ == "__main__":
    main()

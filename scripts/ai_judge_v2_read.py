"""
J-3128 reader for data/active_imagination_judge_v2_shadow.jsonl (the 'seeded' active-imagination judge, SHADOW).

  python scripts/ai_judge_v2_read.py            # counts + the importance split + the 6 newest rows (entry[:160], both whys)

Read-only. This is the named read path for the new log (write-only is the #1 failure): a read job is queued to run it
after the first real accrual and ask whether 'seeded' separates anything the mechanical guard keeps.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from nodes import subconscious_node as sn
    from core import shadow_log as sl
    print(json.dumps(sn.active_imagination_judge_v2_status(), ensure_ascii=False))
    rows = sl.read_rows(sn._AI_JUDGE_V2_LOG)
    for r in rows[-6:]:
        print("-", r.get("verdict"), r.get("how"), "v1=%s v2=%s" % (r.get("v1"), r.get("v2")), "imp=%s" % r.get("kept_importance"))
        print("   seed:", r.get("seed"))
        print("   entry:", str(r.get("entry"))[:160].replace("\n", " | "))
        print("   why1:", r.get("why1"), "(in entry: %s)" % r.get("phrase_ok1"))
        print("   why2:", r.get("why2"), "(in entry: %s)" % r.get("phrase_ok2"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

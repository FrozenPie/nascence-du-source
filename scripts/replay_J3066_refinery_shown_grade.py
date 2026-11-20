"""
J-3066 / F-3773: OFFLINE replay of the refinery's shown-members fidelity grade over the existing shadow log. Read-only.

For each row of data/refinery_shadow.jsonl whose member_ids are COMPLETE (members <= the 40 ids the log keeps), reload those
members' text from nascence.db (opened mode=ro; no write, no model call, no network), rebuild exactly what the distil prompt
showed (the LAST MAX_MEMBERS_IN_PROMPT of the member list, each cut), re-grade the logged insight with
refinery._fidelity_vs_shown and compare with the old all-members grade. Rows from clusters over 40 members are skipped (the
log keeps only the first 40 ids, which are not the ones shown) and counted.

Caveats printed with the result: the log keeps insight[:300], so both grades are on the truncated insight (the old grade is
recomputed the same way for a like-for-like comparison, and the logged `fidelity` is shown beside it); a member whose text
has since changed or been deleted is counted as missing.

Run from the repo root:  python scripts/replay_J3066_refinery_shown_grade.py [--db PATH] [--log PATH] [--out PATH]
--out (optional) writes the per-row replay as jsonl; nothing is written by default.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def replay(rows, get_texts, ref, ml):
    """Pure core (the test drives it with stubs). get_texts(ids)->{id: (content, timestamp)}."""
    out, skipped_big, skipped_missing = [], 0, 0
    for r in rows:
        ids = r.get("member_ids") or []
        n = int(r.get("members") or 0)
        if n > len(ids):
            skipped_big += 1
            continue
        got = get_texts(ids)
        if any(i not in got for i in ids):
            skipped_missing += 1
            continue
        texts = [got[i][0] or "" for i in ids]
        shown = texts[-ref.MAX_MEMBERS_IN_PROMPT:]
        ins = r.get("insight") or ""
        old = ml.source_fidelity(ins, texts)
        new = ref._fidelity_vs_shown(ins, shown)
        newp = ref._fidelity_vs_shown(ins, shown, None)
        out.append({"ts": r.get("ts"), "members": n, "bucket": ref._size_bucket(n), "accepted": bool(r.get("accepted")),
                    "logged_fidelity": r.get("fidelity"), "old_recomputed": old, "fidelity_shown": new,
                    "old_accept": old is not None and old >= ref.FIDELITY_MIN,
                    "new_accept": new is not None and new >= ref.FIDELITY_MIN,
                    "evolving": bool(r.get("evolving")), "ts_order_newest_first":
                        (got[ids[0]][1] >= got[ids[-1]][1]) if len(ids) > 1 else None})
    return out, skipped_big, skipped_missing


def summarise(res):
    by = {}
    for x in res:
        b = by.setdefault(x["bucket"], {"rows": 0, "old_accept": 0, "new_accept": 0, "old_accept_new_reject": 0})
        b["rows"] += 1
        b["old_accept"] += x["old_accept"]
        b["new_accept"] += x["new_accept"]
        b["old_accept_new_reject"] += (x["old_accept"] and not x["new_accept"])
    return by


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "memory" / "nascence.db"))
    ap.add_argument("--log", default=str(ROOT / "data" / "refinery_shadow.jsonl"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    from core import refinery as ref
    from core import memory_levels as ml
    rows = [json.loads(l) for l in open(a.log, encoding="utf-8") if l.strip()]
    conn = sqlite3.connect("file:" + Path(a.db).as_posix() + "?mode=ro", uri=True)

    def get_texts(ids):
        res = {}
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            q = "SELECT fragment_id, content, timestamp FROM memory_fragments WHERE fragment_id IN (%s)" % ",".join("?" * len(chunk))
            for fid, c, ts in conn.execute(q, chunk):
                res[fid] = (c, ts)
        return res

    res, big, missing = replay(rows, get_texts, ref, ml)
    conn.close()
    print(f"shadow rows {len(rows)}; replayed {len(res)}; skipped (>{40} members, shown ids not logged) {big}; "
          f"skipped (member text missing) {missing}")
    order = [x["ts_order_newest_first"] for x in res if x["ts_order_newest_first"] is not None]
    print(f"member_ids order newest-first in {sum(order)}/{len(order)} replayed rows "
          f"(if true, the 'last 8' the prompt shows are the OLDEST members, see F-4242)")
    print(f"{'bucket':>8} {'rows':>5} {'old_acc':>8} {'new_acc':>8} {'old_acc->new_rej':>17} {'rate':>6}")
    for k, b in sorted(summarise(res).items(), key=lambda kv: int(kv[0].split('-')[0].rstrip('+').lstrip('<'))):
        rate = round(b["old_accept_new_reject"] / b["old_accept"], 3) if b["old_accept"] else None
        print(f"{k:>8} {b['rows']:>5} {b['old_accept']:>8} {b['new_accept']:>8} {b['old_accept_new_reject']:>17} {rate!s:>6}")
    tot_old = sum(1 for x in res if x["old_accept"])
    tot_rej = sum(1 for x in res if x["old_accept"] and not x["new_accept"])
    print(f"TOTAL old-accepted {tot_old}; would be rejected under the shown-members grade: {tot_rej}")
    drift = [abs((x["logged_fidelity"] or 0) - (x["old_recomputed"] or 0)) for x in res]
    if drift:
        print(f"logged fidelity vs recomputed (truncated insight): mean abs diff {sum(drift)/len(drift):.3f}, max {max(drift):.3f}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            for x in res:
                f.write(json.dumps(x) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

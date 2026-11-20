"""
key_shadow_summary.py -- the READER for data/key_shadow.jsonl (J-3310, D-0552, row P-0004). Read-only.

Without this the log is write-only. It answers, from the rows alone and without any judge:
  1. VALIDITY: does the shadow's own recomputation of the plain arm sit inside what retrieve() really returned
     (plain_matches_live)? Design section 3.3: below about 95 percent over the first 50 rows, the arms are not
     comparable to live and the shadow read is invalid until fixed. Farewell cycles are excluded (retrieve() takes
     its legacy path there, D-0442) and counted separately.
  2. MOVEMENT: how many of the plain 9 each arm keeps, whether the top-1 hit survives, how many items arm B adds,
     and the origin mix of what each arm adds versus what it drops (guard metrics a/b, design section 4.4).
  3. CONTROL: how often arm N had identical keys to arm A (control void for that row).
  4. COST: the added per-cycle time (embed + prep + matvec + select).
It does NOT judge quality: whether the moved items are better is the judged read (J-3309's offline replay, then a
live confirmation), not this script.

    python scripts/key_shadow_summary.py [--log data/key_shadow.jsonl] [--since <unix ts>]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TREE = Path(__file__).resolve().parent.parent


def _pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(TREE / "data" / "key_shadow.jsonl"))
    ap.add_argument("--since", type=float, default=0.0)
    a = ap.parse_args()
    path = Path(a.log)
    if not path.exists():
        print(f"no log at {path} (Du has not run the key shadow yet; it is restart-gated)")
        return 0
    rows = []
    bad = 0
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except Exception:
            bad += 1
            continue
        if r.get("ts", 0) >= a.since:
            rows.append(r)
    skipped = Counter(r["skipped"] for r in rows if r.get("skipped"))
    scored = [r for r in rows if not r.get("skipped")]
    farewell = [r for r in scored if r.get("farewell")]
    body = [r for r in scored if not r.get("farewell")]
    print(f"log {path}")
    print(f"rows {len(rows)} (unparsable {bad}); skipped {dict(skipped) or 0}; scored {len(scored)} "
          f"(farewell-flagged {len(farewell)}, analysed {len(body)}); by input_type "
          f"{dict(Counter(r.get('input_type') for r in body))}")
    if not body:
        print("nothing to analyse yet")
        return 0

    # 1 validity
    with_live = [r for r in body if r.get("plain_matches_live") is not None]
    ok = sum(1 for r in with_live if r["plain_matches_live"])
    rate = ok / len(with_live) if with_live else float("nan")
    verdict = ("INSUFFICIENT (<50 rows)" if len(with_live) < 50 else ("VALID" if rate >= 0.95 else "INVALID: arms not comparable to live"))
    print(f"\n1. plain_matches_live: {ok}/{len(with_live)} = {rate:.3f}  -> {verdict}")
    miss = [r for r in with_live if not r["plain_matches_live"]]
    if miss:
        print(f"   mismatches: mean plain_missing_from_live {statistics.mean(r.get('plain_missing_from_live') or 0 for r in miss):.2f}; "
              f"rows with no_emb_n>0: {sum(1 for r in miss if (r.get('no_emb_n') or 0) > 0)}")
    print(f"   live_extra_n (recency rows + trail + deep recall) median {statistics.median(r.get('live_extra_n') or 0 for r in with_live):.0f}"
          if with_live else "")

    # 2 movement
    print("\n2. movement against the plain 9 (items kept / top-1 kept / origin mix of added vs dropped)")
    for name, label in (("A05", "A05_9"), ("A025", "A025_9"), ("B", "B_9"), ("N", "N_9")):
        rs = [r for r in body if r.get(label)]
        if not rs:
            print(f"   {name}: no rows")
            continue
        kept, top1, added_o, dropped_o, changed = [], [], Counter(), Counter(), []
        for r in rs:
            plain = {e[0]: e for e in r["plain9"]}
            arm = {e[0]: e for e in r[label]}
            kept.append(len(set(plain) & set(arm)))
            changed.append(len(set(arm) - set(plain)))
            if r["plain9"]:
                top1.append(r["plain9"][0][0] in arm)
            for i in set(arm) - set(plain):
                added_o[arm[i][3]] += 1
            for i in set(plain) - set(arm):
                dropped_o[plain[i][3]] += 1
        print(f"   {name}: n={len(rs)} mean slots changed {statistics.mean(changed):.2f}; zero-change rows "
              f"{sum(1 for c in changed if c == 0)}; top-1 kept {sum(top1)}/{len(top1)}")
        print(f"        added origins   {dict(added_o.most_common(6))}")
        print(f"        dropped origins {dict(dropped_o.most_common(6))}")
        if name == "A05":
            ai, di = added_o.get("inner_thought", 0) / max(1, sum(added_o.values())), dropped_o.get("inner_thought", 0) / max(1, sum(dropped_o.values()))
            print(f"        guard (a) inner_thought share added {ai:.2f} vs dropped {di:.2f}")

    # 3 control
    n_rows = [r for r in body if r.get("N_9")]
    if n_rows:
        same = sum(1 for r in n_rows if r.get("N_same_keys"))
        print(f"\n3. arm N rows {len(n_rows)}; identical keys to the current call on {same} (control void on those)")
    cos = [r["cos_query_keys"] for r in body if r.get("cos_query_keys") is not None]
    if cos:
        print(f"   cos(query, keys) mean {statistics.mean(cos):.3f}; rows with no usable keys "
              f"{sum(1 for r in body if r.get('no_usable_keys'))}; junk key tokens per row {statistics.mean(r.get('junk_keys_n', 0) for r in body):.2f}")

    # 4 cost
    print("\n4. added per-cycle time (ms): embed / prep / matvec / select / total (median, p90)")
    for k in ("embed_ms", "prep_ms", "matvec_ms", "select_ms", "total_ms"):
        xs = [r[k] for r in body if r.get(k) is not None]
        if xs:
            print(f"   {k:10s} median {statistics.median(xs):7.1f}  p90 {_pct(xs, 0.9):7.1f}  max {max(xs):7.1f}")
    print("\nThis log says what MOVED, never whether it is better. Quality is the judged read (J-3309 replay, then live confirmation).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

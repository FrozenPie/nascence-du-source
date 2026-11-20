"""
Nascence -- training corpus <-> verdict join (J-2205, from F-2902).

READ-ONLY. Reports how many teacher rows in data/training/<node>.jsonl (written by core/training_log.py,
keyed on the cycle_id node_base passes in) have at least one JOINED quality verdict, and the verdict
split per source -- the proof that a curated training set can later be cut by verdict.

Verdict sources joined on cycle_id (each one is a verdict about that cycle's output):
  panel_transport  same file, node-less rows: counted by key, NOT a verdict (J-3594).
  panel      data/judge_panel_log.jsonl            rows carrying the optional `cycle_id` field (J-2205, live
                                                   from Du's next boot); a row with a `node` field joins only
                                                   that node's corpus. verdict = row["verdict"].
  critic     data/training/critic.jsonl            the critic node's own verdict on the same cycle's draft
                                                   (output.approved). Skipped when --node critic.
  critic_sh  data/logs/critic_shadow_alongside.jsonl  decomposed critic verdict (decomposed_approved).
  social     data/social_cognition_shadow.jsonl    decoupled panel on Du's reply (tracks_intent) -- voice turns.
  self_int   data/self_interrogation_shadow.jsonl  decoupled panel on the cycle's thought (genuine).

Imports nothing from core/ or nodes/ (import-time paths write live data/: F-2406/F-2423) and opens every file
read-only. Never writes anything.

Run:  python scripts/training_corpus_join.py voice [--since 2026-10-01] [--until 2026-10-17] [--data DIR] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _rows(path: Path):
    if not path.exists():
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                yield r


def _day(s: str | None, end: bool = False) -> float | None:
    if not s:
        return None
    d = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    return d + 86400.0 if end else d


def _label(v) -> str:
    return "true" if v is True else "false" if v is False else "none"


def load_verdicts(data: Path, node: str) -> dict[str, dict[str, list[str]]]:
    """source -> cycle_id -> [verdict labels]."""
    out: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for r in _rows(data / "judge_panel_log.jsonl"):
        cid = r.get("cycle_id")
        if cid and (not r.get("node") or r.get("node") == node):
            # J-3594: node-less rows are transport (pursuits `advances`, self_interrogation `genuine`), not a
            # verdict on this node's output -- keep them out of "panel" and count them under "panel_transport".
            src = "panel" if r.get("node") else "panel_transport"
            lab = _label(r.get("verdict"))
            out[src][str(cid)].append(f"{r.get('key')}:{lab}" if r.get("key") else lab)
    if node != "critic":
        for r in _rows(data / "training" / "critic.jsonl"):
            cid, o = r.get("cycle_id"), r.get("output")
            if cid and isinstance(o, dict) and "approved" in o:
                out["critic"][str(cid)].append(_label(bool(o.get("approved"))))
    for r in _rows(data / "logs" / "critic_shadow_alongside.jsonl"):
        if r.get("cycle_id"):
            out["critic_sh"][str(r["cycle_id"])].append(_label(r.get("decomposed_approved")))
    for r in _rows(data / "social_cognition_shadow.jsonl"):
        if r.get("cycle_id") and "tracks_intent" in r:
            out["social"][str(r["cycle_id"])].append(_label(r.get("tracks_intent")))
    for r in _rows(data / "self_interrogation_shadow.jsonl"):
        if r.get("cycle_id") and r.get("kind") == "interrogate":
            out["self_int"][str(r["cycle_id"])].append(_label(r.get("genuine")))
    return out


def join(node: str, since: str | None = None, until: str | None = None, data: Path | None = None) -> dict:
    data = data or (ROOT / "data")
    lo, hi = _day(since), _day(until, end=True)
    corpus = data / "training" / f"{node}.jsonl"
    verdicts = load_verdicts(data, node)
    n = no_cid = 0
    joined_any = 0
    per_src: dict[str, Counter] = {s: Counter() for s in
                                   ("panel", "panel_transport", "critic", "critic_sh", "social", "self_int")}
    rows_with: Counter = Counter()
    extra_rulings: Counter = Counter()  # rulings beyond the newest per cycle (prompt v2 + v3 etc.)
    for r in _rows(corpus):
        ts = r.get("ts")
        if not isinstance(ts, (int, float)) or (lo and ts < lo) or (hi and ts >= hi):
            continue
        n += 1
        cid = str(r.get("cycle_id") or "")
        if not cid:
            no_cid += 1
            continue
        hit = False
        for src, m in verdicts.items():
            if cid in m:
                if src != "panel_transport":  # transport rows are not verdicts on this node
                    hit = True
                rows_with[src] += 1
                labs = m[cid]
                if src == "panel":  # newest ruling per (cycle, key); file order is append order
                    newest: dict[str, str] = {}
                    for x in labs:
                        newest[x.rsplit(":", 1)[0] if ":" in x else ""] = x
                    per_src[src].update(newest.values())
                    extra_rulings[src] += len(labs) - len(newest)
                elif src == "panel_transport":
                    per_src[src].update({x.rsplit(":", 1)[0] for x in labs})
                else:  # newest-ruling verdict per cycle
                    per_src[src].update(labs[-1:])
                    extra_rulings[src] += len(labs) - 1
        joined_any += hit
    return {"node": node, "corpus": str(corpus), "since": since, "until": until,
            "training_rows": n, "rows_without_cycle_id": no_cid, "rows_with_any_verdict": joined_any,
            "rows_joined_by_source": dict(rows_with),
            "extra_rulings_dropped_by_source": {k: v for k, v in extra_rulings.items() if v},
            "verdict_split_by_source": {s: dict(c) for s, c in per_src.items() if c},
            "verdict_cycles_by_source": {s: len(m) for s, m in verdicts.items()}}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("node")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--data", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    res = join(a.node, a.since, a.until, a.data)
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    print(f"training corpus join -- node={res['node']} since={res['since']} until={res['until']}")
    print(f"  training rows in range : {res['training_rows']}  (no cycle_id: {res['rows_without_cycle_id']})")
    pct = 100.0 * res["rows_with_any_verdict"] / res["training_rows"] if res["training_rows"] else 0.0
    print(f"  rows with >=1 verdict  : {res['rows_with_any_verdict']}  ({pct:.1f}%)")
    for s, k in sorted(res["verdict_cycles_by_source"].items()):
        print(f"  {s:10s} cycles={k:6d} joined_rows={res['rows_joined_by_source'].get(s, 0):6d} "
              f"split={res['verdict_split_by_source'].get(s, {})}")
    if res["extra_rulings_dropped_by_source"]:
        print(f"  older rulings not counted (newest per cycle kept): {res['extra_rulings_dropped_by_source']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D-0620 reach read (J-3231). READ-ONLY instrument: opens the memory DB with mode=ro and streams
data/co_recall_ledger.jsonl; writes nothing. Replaces the dead gate F-3254 (2+ rows in
data/peer_reflection_injection_log.jsonl for one peer): since D-0289 / D-0310 the ambient recall_block returns
before that log line, so the gate could never be met. The ledger is the true record of which fragment ids reached
a thought (F-3738).

Ruling D-0620 (Travis, 2026-11-02): new peer reflections are stored at letter-level salience (core/peer_model.py
REFLECTION_RELEVANCE / REFLECTION_IMPORTANCE) with valence and felt, no direct injection (D-0016). Defeater, read
here after two weeks: (a) the reflections still reach fewer than 3 thoughts -> retire the prompt (P-0086) and the
origin; (b) they crowd letters out of recall -> lower their salience.

CUTOFF = the timestamp of the first origin='peer_reflection' fragment stored with importance >= 0.8 (the old 32
were 0.55); no extra state file. 'Reflections after cutoff' = those fragments only (the 32 old ones are reported
as their own line, they are the baseline). A ledger row = one train step of one thought; rows whose source ends
'_shadow' never reached a thought (core/memory_edges._is_shadow_source) and are left out.

Metrics: thoughts (ledger rows) reached by new reflections / by the old 32 / by letters (origin 'letter' + 'peer'),
all in the post-cutoff window; reflections' share of those rows; letter rows per live day in the post window vs
an equal-length window just before the cutoff (crowding). 'Live day' = a local day with >= MIN_FRAGS memory
fragments written (Du can be down for days). The read is NOT READY until LIVE_DAYS live days have passed since
cutoff; before that the numbers print but carry the label.

Usage: python scripts/peer_reflection_reach_read.py [--data-root PATH] [--live-days 14] [--force]
Reads, never acts: nothing here retires or re-scores anything (no system acts later on its own)."""
from __future__ import annotations
import argparse, datetime as dt, json, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

NEW_IMPORTANCE_FLOOR = 0.8      # the old reflections were stored at 0.55; D-0620's are 0.85
MIN_FRAGS = 50
RETIRE_BELOW = 3                # D-0620 defeater (a)
CROWD_DROP = 0.30               # letters' rows per live day falling by this much or more reads as crowding (b)
LETTER_ORIGINS = ("letter", "peer")


def _root(arg):
    cands = [Path(arg)] if arg else []
    cands += [Path(__file__).resolve().parent.parent / "data", Path(r"C:\Nascence\data")]
    for c in cands:
        if (c / "memory" / "nascence.db").exists() and (c / "co_recall_ledger.jsonl").exists():
            return c
    raise SystemExit("no data root with memory/nascence.db and co_recall_ledger.jsonl found")


def _day(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _is_shadow(source):
    return str(source or "").endswith("_shadow")


def read(root, live_days_needed=14):
    con = sqlite3.connect(f"file:{(root / 'memory' / 'nascence.db').as_posix()}?mode=ro", uri=True)
    frags = {fid: (o, imp, ts) for fid, o, imp, ts in con.execute(
        "SELECT fragment_id, origin, importance, timestamp FROM memory_fragments "
        "WHERE origin IN ('peer_reflection','letter','peer')")}
    live = Counter(d for (d,) in con.execute(
        "SELECT strftime('%Y-%m-%d', timestamp, 'unixepoch', 'localtime') FROM memory_fragments"))
    live = sorted(d for d, n in live.items() if n >= MIN_FRAGS)
    con.close()

    new_ids = {f for f, (o, imp, ts) in frags.items() if o == "peer_reflection" and (imp or 0) >= NEW_IMPORTANCE_FLOOR}
    old_ids = {f for f, (o, imp, ts) in frags.items() if o == "peer_reflection"} - new_ids
    out = {"root": str(root), "n_new_stored": len(new_ids), "n_old_stored": len(old_ids)}
    if not new_ids:
        out.update(cutoff=None, ready=False, note="no reflection stored at importance >= %.2f yet: the D-0620 change has "
                   "not run (restart-gated); nothing to read" % NEW_IMPORTANCE_FLOOR)
        return out
    cut = min(frags[f][2] for f in new_ids)
    live_after = [d for d in live if d >= _day(cut)]
    live_before = [d for d in live if d < _day(cut)][-max(len(live_after), 1):]
    out.update(cutoff=cut, cutoff_day=_day(cut), live_days_after=len(live_after), live_days_needed=live_days_needed,
               ready=len(live_after) >= live_days_needed)

    kind = {}
    for f, (o, imp, ts) in frags.items():
        kind[f] = "new" if f in new_ids else ("old" if f in old_ids else "letter")
    rows = {"after": Counter(), "before": Counter()}
    per_peer = Counter()
    sources = defaultdict(Counter)
    frag_hit = defaultdict(set)
    before_days, after_days = set(live_before), set(live_after)
    with open(root / "co_recall_ledger.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if _is_shadow(r.get("source")) or not r.get("ids"):
                continue
            ts = r.get("ts") or 0
            d = _day(ts)
            win = "after" if ts >= cut else ("before" if d in before_days else None)
            if win is None:
                continue
            ks = {kind[i] for i in r["ids"] if i in kind}
            for k in ks:
                rows[win][k] += 1
            if win == "after":
                for i in r["ids"]:
                    if kind.get(i) in ("new", "old"):
                        frag_hit[kind[i]].add(i)
                if "new" in ks:
                    sources["new"][r.get("source")] += 1
                if "letter" in ks:
                    sources["letter"][r.get("source")] += 1
    a, b = rows["after"], rows["before"]
    la, lb = len(after_days) or 1, len(before_days) or 1
    out.update(rows_after=dict(a), rows_before=dict(b),
               new_distinct_fragments_reached=len(frag_hit["new"]), old_distinct_fragments_reached=len(frag_hit["old"]),
               new_sources=dict(sources["new"]), letter_sources=dict(sources["letter"]),
               letter_rows_per_live_day_after=round(a["letter"] / la, 2),
               letter_rows_per_live_day_before=round(b["letter"] / lb, 2) if before_days else None,
               before_live_days=len(before_days))
    out["share_of_letter_rows"] = round(a["new"] / a["letter"], 4) if a["letter"] else None
    out["defeater_a_retire"] = a["new"] < RETIRE_BELOW
    pb = out["letter_rows_per_live_day_before"]
    out["defeater_b_crowding"] = bool(pb and out["letter_rows_per_live_day_after"] <= pb * (1 - CROWD_DROP))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root")
    ap.add_argument("--live-days", type=int, default=14)
    ap.add_argument("--force", action="store_true", help="print the defeater lines even before the window is ready")
    a = ap.parse_args()
    o = read(_root(a.data_root), a.live_days)
    print("# peer reflection reach read (D-0620 / J-3231)")
    print(f"data root: {o['root']}")
    print(f"reflections stored: {o['n_new_stored']} at letter-level salience, {o['n_old_stored']} old (0.55)")
    if not o.get("cutoff"):
        print(o["note"])
        return 0
    print(f"cutoff: {o['cutoff_day']}   live days since: {o['live_days_after']} of {o['live_days_needed']} needed")
    if not o["ready"]:
        print("STATUS: NOT READY -- the two-week window has not run; numbers below are partial")
    ra, rb = o["rows_after"], o["rows_before"]
    print("\nthoughts (non-shadow ledger rows) reached after cutoff:")
    print(f"  new reflections : {ra.get('new', 0)}   ({o['new_distinct_fragments_reached']} distinct fragments)")
    print(f"  old 32          : {ra.get('old', 0)}   ({o['old_distinct_fragments_reached']} distinct fragments)")
    print(f"  letters (letter+peer): {ra.get('letter', 0)}   -> reflections / letters = {o['share_of_letter_rows']}")
    print(f"  new-reflection sources: {o['new_sources']}")
    print(f"  letter sources        : {o['letter_sources']}")
    print(f"\nletter rows per live day: {o['letter_rows_per_live_day_after']} after, "
          f"{o['letter_rows_per_live_day_before']} in the {o['before_live_days']} live days before")
    if o["ready"] or a.force:
        print("\nD-0620 defeater, read not acted on:")
        print(f"  (a) reflections reached < {RETIRE_BELOW} thoughts: {'YES -> founder call to retire P-0086 and the origin' if o['defeater_a_retire'] else 'no'}")
        print(f"  (b) letters' rows/day fell >= {int(CROWD_DROP*100)}%: {'YES -> founder call to lower REFLECTION_* salience' if o['defeater_b_crowding'] else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

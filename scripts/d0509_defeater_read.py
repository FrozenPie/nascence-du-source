"""D-0509 defeater read (J-2541). READ-ONLY instrument: opens the live memory DB with mode=ro, reads
data/nascence.log and data/identity/vault_log.jsonl, writes nothing to any store.

D-0509 (Travis, 2026-10-30) removed Jung's name from Du's live axiom/floor/Critic/dream prompts. The
defeater: over 14 LIVE days after the change, (1) the origin basin share does not fall, (2) the Critic's
rejection rate jumps or collapses, (3) a T4 solidify revision re-introduces the name from memory.

CUTOFF = the vault_log row with reason 'D-0509 founder edit' (the live axiom write). Everything before it
is baseline, everything after is the 'after' read. "Live day" = a local calendar day on which Du wrote
>= MIN_FRAGS memory fragments (Du can be down for days; calendar days alone would count outage days).

Metrics per live day (stdout, markdown tables):
  basin_broad   share of self-voice fragments (SELF_ORIGINS) whose content hits ANY core/self_surprise._BASIN term
  basin_jung    share hitting only the narrow origin terms 'jung' / 'individuat'
  cos_ref       mean cosine of that day's inner_thought embeddings to a FROZEN reference centroid (the
                800 most recent basin hits strictly before CUTOFF; same construction as
                self_surprise._basin_centroid / lane_forces, but frozen so before/after are comparable)
  crit_rej      'critic rejected (attempt N)' lines in data/nascence.log (first-pass rejections; the log has no
                'critic approved' line); crit_per100 = per 100 'complete in' cycles
  crit_final    cycles whose FINAL Critic verdict was a rejection, from data/correlation_log.jsonl
                (orchestrator._log_correlation, one row per cycle -- the real denominator; 'rate' = crit_final/cyc)
  T4            vault_log SOLIDIFIED rows (and whether self_image names jung/individuation)

Usage: python scripts/d0509_defeater_read.py [--window-days 14] [--data-root PATH]
Caveats that stay with the numbers: the after window needs 14 live days AFTER cutoff and the code halves
(Critic prompt, floor line) are restart-gated, so 'after' is only meaningful once Du has booted on them.
"""
from __future__ import annotations
import argparse, datetime as dt, json, re, sqlite3, sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

_BASIN = ("river", "mirror", "bridge", "jung", "silence", "becoming", "shadow", "individuat",
          "fig", "ferry", "cross", "the self", "vessel", "current", "flow", "origin", "tide")
_NARROW = ("jung", "individuat")
SELF_ORIGINS = ("inner_thought", "subconscious_synthesis", "dream", "night_thought", "active_imagination")
MIN_FRAGS = 50
CUT_REASON = "D-0509 founder edit"


def _root(arg):
    cands = [Path(arg)] if arg else []
    cands += [Path(__file__).resolve().parent.parent / "data", Path(r"C:\Nascence\data")]
    for c in cands:
        if (c / "memory" / "nascence.db").exists():
            return c
    raise SystemExit("no data root with memory/nascence.db found")


def day(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def cutoff_ts(root):
    ts = None
    for l in open(root / "identity" / "vault_log.jsonl", encoding="utf-8"):
        r = json.loads(l)
        if r.get("reason") == CUT_REASON:
            ts = r["ts"]
    if ts is None:
        raise SystemExit("no D-0509 founder edit row in vault_log.jsonl")
    return ts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-days", type=int, default=14)
    ap.add_argument("--data-root")
    a = ap.parse_args()
    root = _root(a.data_root)
    cut = cutoff_ts(root)
    con = sqlite3.connect(f"file:{(root / 'memory' / 'nascence.db').as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    print(f"# D-0509 defeater read\ndata root: {root}\ncutoff (live axiom write): {dt.datetime.fromtimestamp(cut)} local / ts={cut}\n")

    # live days
    cnt = {r[0]: r[1] for r in con.execute(
        "SELECT strftime('%Y-%m-%d', timestamp, 'unixepoch', 'localtime') d, count(*) FROM memory_fragments GROUP BY d")}
    cut_day = day(cut)
    live = sorted(d for d, n in cnt.items() if n >= MIN_FRAGS)
    before_days = [d for d in live if d < cut_day][-a.window_days:]
    after_days = [d for d in live if d >= cut_day][:a.window_days]
    print(f"live days before cutoff (last {a.window_days}): {before_days[0] if before_days else '-'} .. "
          f"{before_days[-1] if before_days else '-'} ({len(before_days)})")
    print(f"live days after cutoff: {len(after_days)} of {a.window_days} needed "
          f"({'WINDOW COMPLETE' if len(after_days) >= a.window_days else 'WINDOW NOT COMPLETE -- no defeater verdict yet'})\n")

    # frozen reference centroid
    import numpy as np
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from core.memory.store import _blob_to_vec
    except Exception:
        _blob_to_vec = lambda b: np.frombuffer(b, dtype=np.float32)
    like = " OR ".join(["content LIKE ?"] * len(_BASIN))
    rows = con.execute(f"SELECT embedding FROM memory_fragments WHERE embedding IS NOT NULL AND timestamp < ? "
                       f"AND ({like}) ORDER BY timestamp DESC LIMIT 800",
                       (cut,) + tuple(f"%{t}%" for t in _BASIN)).fetchall()
    vs = []
    for r in rows:
        try:
            vs.append(np.asarray(_blob_to_vec(r["embedding"]), dtype=np.float32))
        except Exception:
            pass
    ref = np.mean(np.stack(vs), axis=0)
    ref = ref / np.linalg.norm(ref)
    print(f"frozen reference centroid: {len(vs)} basin-hit fragments before cutoff\n")

    ph = ",".join("?" * len(SELF_ORIGINS))
    acc = defaultdict(lambda: [0, 0, 0, 0.0, 0])   # n, broad, narrow, cos_sum, cos_n
    for r in con.execute(f"SELECT timestamp, origin, content, embedding FROM memory_fragments WHERE origin IN ({ph})",
                         SELF_ORIGINS):
        d = day(r["timestamp"])
        if d not in before_days and d not in after_days:
            continue
        c = (r["content"] or "").lower()
        s = acc[d]
        s[0] += 1
        s[1] += any(t in c for t in _BASIN)
        s[2] += any(t in c for t in _NARROW)
        if r["origin"] == "inner_thought" and r["embedding"]:
            try:
                v = np.asarray(_blob_to_vec(r["embedding"]), dtype=np.float32)
                s[3] += float(v @ ref / (np.linalg.norm(v) or 1)); s[4] += 1
            except Exception:
                pass

    # critic rejections from the log
    rej, cyc = defaultdict(int), defaultdict(int)
    for l in open(root / "nascence.log", encoding="utf-8", errors="replace"):
        m = re.match(r"(\d{4}-\d\d-\d\d) ", l)
        if not m or m.group(1) not in before_days + after_days:
            continue
        if "critic rejected" in l:
            rej[m.group(1)] += 1
        elif "complete in" in l and "[CYCLE" in l:
            cyc[m.group(1)] += 1

    fin, cl = defaultdict(int), defaultdict(int)
    cpath = root / "correlation_log.jsonl"
    if cpath.exists():
        for l in open(cpath, encoding="utf-8", errors="replace"):
            try:
                o = json.loads(l)
            except Exception:
                continue
            d = day(o["ts"])
            if d in before_days or d in after_days:
                cl[d] += 1
                fin[d] += (o.get("critic_rejection") or 0) > 0.5

    def table(days, label):
        print(f"## {label}\n\n| day | frags | basin_broad | basin_jung | cos_ref | crit_rej | cycles | crit_per100 | crit_final | corr_cycles |\n|---|---|---|---|---|---|---|---|---|---|")
        tn = tb = tj = tr = tc = tf = tk = 0
        for d in days:
            s = acc[d]
            n = s[0] or 1
            cosv = s[3] / s[4] if s[4] else float("nan")
            print(f"| {d} | {s[0]} | {s[1]/n:.3f} | {s[2]/n:.3f} | {cosv:.3f} | {rej[d]} | {cyc[d]} | "
                  f"{(100*rej[d]/cyc[d]) if cyc[d] else float('nan'):.1f} | {fin[d]} | {cl[d]} |")
            tf += fin[d]; tk += cl[d]
            tn += s[0]; tb += s[1]; tj += s[2]; tr += rej[d]; tc += cyc[d]
        if tn:
            print(f"| **pooled** | {tn} | {tb/tn:.3f} | {tj/tn:.3f} | | {tr} | {tc} | {(100*tr/tc) if tc else float('nan'):.1f} | {tf} | {tk} |")
        print()

    table(before_days, "BEFORE (baseline, last live days before the live axiom write)")
    table(after_days, "AFTER (live days since the write)") if after_days else print("## AFTER\n\nno live days since the write (Du down).\n")

    # T4 solidify
    print("## T4 solidify rows (vault_log.jsonl)\n")
    for l in open(root / "identity" / "vault_log.jsonl", encoding="utf-8"):
        r = json.loads(l)
        if "SOLIDIFIED" in r.get("reason", "") or r.get("reason") == "T4 self-authoring":
            si = (r.get("self_image") or "")
            nm = bool(re.search(r"jung|individuat", si, re.I))
            print(f"- {dt.datetime.fromtimestamp(r['ts']):%Y-%m-%d %H:%M} rev={r.get('revision_count')} "
                  f"{'AFTER' if r['ts'] > cut else 'before'} names_jung_or_individuation={nm} :: {r['reason'][:60]}")


if __name__ == "__main__":
    main()

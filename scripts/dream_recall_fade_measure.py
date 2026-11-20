"""J-3175 / D-0563 / F-3566 (plan sleep_dream_redesign): before/after measurement of the dreamer's recall.

For each dream arc in dream_log.jsonl that carries scenes_detail + seed.fragment_ids, looks the recalled
fragments up in a nascence.db and reports, per 7-day window (and before/after --cutover):
  * dream-origin share of the recalled fragments            (F-3566: 47%; D-0563 defeater: still > 40% after)
  * share of recalled dream fragments younger than 7 days at arc time   (must be 0 after the change)
  * 5-word-run repetition rate: scenes sharing an exact 5-word run with a recalled DREAM fragment's first
    140 chars (dream prefix stripped)                        (F-3566: 57%)
  * single-word dominance: the content word present in the most arcs of the window, as a share of its arcs
    (thyme in 65 of 68 arcs = 96% on 10-12..10-18; D-0563 defeater: any 7-day window above 50%)
READER: the founder / whoever reads the D-0563 defeater after the restart; run it, it writes nothing.
Read-only: pass COPIES of the log and the db (never C:\\Nascence\\data), db is opened mode=ro.
Run: python scripts/dream_recall_fade_measure.py --log dream_log.jsonl --db nascence.db [--since 2026-10-05]
     [--cutover 2026-11-06T09:00]   (cutover = when Du restarted onto the J-3175 build; local time)"""
import argparse
import collections
import datetime as dt
import json
import re
import sqlite3
import sys

_STOP = set("""that this with from they them their were have been your what when where which while there then than
into onto about over under again very just like some such only also more most much many even ever each both
would could should will shall might must does doing done being those these here once upon through between
toward towards without within against around after before because until their theirs its his her hers our
ours mine you she him not but and the for are was can had has how why who whom all any one two out off too
still yet its something nothing everything""".split())
_PREFIX = re.compile(r"^\[Dream [^\]]*\]\s*")
_WORD = re.compile(r"[a-z']+")


def _words(t: str) -> list:
    return _WORD.findall((t or "").lower())


def _grams(t: str, n: int = 5) -> set:
    w = _words(t)
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def _ts(s: str) -> float:
    return dt.datetime.fromisoformat(s).timestamp()


def load(log: str, db: str, since: float):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    arcs = []
    for line in open(log, encoding="utf-8"):
        try:
            a = json.loads(line)
        except Exception:
            continue
        ts = float(a.get("ts") or 0)
        ids = ((a.get("seed") or {}).get("fragment_ids")) or []
        if ts < since or not a.get("scenes_detail") or not ids:
            continue
        ph = ",".join("?" * len(ids))
        frs = [dict(r) for r in conn.execute(
            f"SELECT fragment_id, origin, timestamp, content FROM memory_fragments WHERE fragment_id IN ({ph})", ids)]
        arcs.append({"ts": ts, "scenes": [s.get("narrative") or "" for s in a["scenes_detail"]], "frags": frs})
    conn.close()
    return arcs


def summarize(arcs: list) -> dict:
    n_frag = n_dream = n_young = n_scene = n_rep = 0
    arcs_with_dream = 0
    word_arcs = collections.Counter()
    for a in arcs:
        d = [f for f in a["frags"] if f["origin"] == "dream"]
        n_frag += len(a["frags"]); n_dream += len(d); arcs_with_dream += bool(d)
        n_young += sum(1 for f in d if (a["ts"] - float(f["timestamp"])) < 7 * 86400)
        dgrams = set()
        for f in d:
            dgrams |= _grams(_PREFIX.sub("", f["content"] or "")[:140])
        for s in a["scenes"]:
            n_scene += 1
            n_rep += bool(dgrams & _grams(s))
        words = set()
        for s in a["scenes"]:
            words |= {w for w in _words(s) if len(w) >= 4 and w not in _STOP}
        word_arcs.update(words)
    top = word_arcs.most_common(1)
    pct = lambda x, y: round(100.0 * x / y, 1) if y else None
    return {"arcs": len(arcs), "fragments": n_frag,
            "dream_share_pct": pct(n_dream, n_frag), "arcs_with_dream_fragment": arcs_with_dream,
            "dream_frags_younger_7d": n_young,
            "scenes": n_scene, "scenes_5word_run_with_recalled_dream_pct": pct(n_rep, n_scene),
            "top_word": top[0][0] if top else None,
            "top_word_arc_share_pct": pct(top[0][1], len(arcs)) if top else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--since", default="2026-10-05")
    ap.add_argument("--cutover", default=None, help="local ISO time of the restart onto the J-3175 build")
    a = ap.parse_args()
    arcs = load(a.log, a.db, _ts(a.since))
    if not arcs:
        print("no arcs with scenes_detail + seed.fragment_ids since", a.since)
        return 1
    print(f"arcs since {a.since}: {len(arcs)}")
    if a.cutover:
        cut = _ts(a.cutover)
        for label, sel in (("BEFORE cutover", [x for x in arcs if x["ts"] < cut]),
                           ("AFTER cutover", [x for x in arcs if x["ts"] >= cut])):
            print(label, json.dumps(summarize(sel)) if sel else "no arcs")
    print("per 7-day window (from the first arc):")
    t0 = min(x["ts"] for x in arcs)
    wins = collections.defaultdict(list)
    for x in arcs:
        wins[int((x["ts"] - t0) // (7 * 86400))].append(x)
    for w in sorted(wins):
        start = dt.datetime.fromtimestamp(t0 + w * 7 * 86400).strftime("%Y-%m-%d")
        print(f"  window from {start}: {json.dumps(summarize(wins[w]))}")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())

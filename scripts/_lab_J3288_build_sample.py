"""J-3288 step 1: build the sample of recent study notes with their recovered source passage and key_facts.
READ-ONLY on the live DB (immutable ro URI) and on data/Study/*.md. Writes only --out (default
docs/lab/J-3288_data/sample.json).
Run: python scripts/_lab_J3288_build_sample.py [--n 60] [--out PATH] [--db PATH] [--study-dir PATH]"""
from __future__ import annotations
import argparse, json, random, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

FM = re.compile(r"^\*A study note by .*?on: (?P<book>.*?) · subject: (?P<subject>.*?)(?: · pass: (?P<pass>\d+))?(?: · sittings: (?P<sit>\d+))?(?P<est> \(est\.\))?(?: · chars: (?P<chars>\d+))?\*\s*$", re.M)


def parse_note(path: Path) -> dict | None:
    try:
        t = path.read_text(encoding="utf-8")
    except Exception:
        return None
    m = FM.search(t.split("\n", 3)[2] if t.count("\n") > 2 else t)
    if not m:
        m = FM.search(t)
    if not m:
        return None
    fm_line = m.group(0)
    facts = []
    if "**What I learned:**" in t:
        blk = t.split("**What I learned:**", 1)[1]
        blk = re.split(r"\n\*\*(?:My thoughts|Connects to|Still wondering):\*\*", blk)[0]
        facts = [l[2:].strip() for l in blk.splitlines() if l.startswith("- ") and l[2:].strip()]
    understanding = t.split("*\n", 1)[1].split("\n**What I learned:**")[0].strip() if "*\n" in t else ""
    return {"book": m.group("book"), "subject": m.group("subject"),
            "pass": int(m.group("pass")) if m.group("pass") else None,
            "sittings": int(m.group("sit")) if m.group("sit") else None,
            "chars": int(m.group("chars")) if m.group("chars") else None,
            "revised": "revised" in fm_line, "key_facts": facts, "understanding": understanding}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--db", default=r"C:\Nascence\data\memory\nascence.db")
    ap.add_argument("--study-dir", default=r"C:\Nascence\data\Study")
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3288_data" / "sample.json"))
    ap.add_argument("--pool", type=int, default=400, help="most recent N study_note fragments scanned")
    a = ap.parse_args()
    c = sqlite3.connect(f"file:{a.db}?mode=ro&immutable=1", uri=True)
    c.row_factory = sqlite3.Row
    rows = c.execute("SELECT fragment_id,timestamp,source_id,encounter_id,source_pass FROM memory_fragments "
                     "WHERE origin='study' AND source_type='study_note' AND encounter_id IS NOT NULL "
                     "ORDER BY timestamp DESC LIMIT ?", (a.pool,)).fetchall()
    stats = {"scanned": len(rows), "no_file": 0, "revised": 0, "no_facts": 0, "no_source": 0, "short_source": 0, "usable": 0}
    usable = []
    # one pass over the reading rows of the pool's time span (no index on encounter_id: per-row lookups scan 1.3 GB)
    t0 = min(r["timestamp"] for r in rows) - 5
    reading = [dict(x) for x in c.execute("SELECT encounter_id,source_id,content,timestamp FROM memory_fragments "
                                          "WHERE origin='reading' AND timestamp>=? ORDER BY timestamp", (t0,))]
    by_enc = {}
    for f in reading:
        by_enc.setdefault(f["encounter_id"], f)
    for r in rows:
        p = Path(r["source_id"])
        if not p.exists():
            stats["no_file"] += 1; continue
        n = parse_note(p)
        if not n:
            stats["no_file"] += 1; continue
        if n["revised"]:
            stats["revised"] += 1; continue
        if not n["key_facts"]:
            stats["no_facts"] += 1; continue
        first = by_enc.get(r["encounter_id"])
        if not first:
            stats["no_source"] += 1; continue
        frs = [f for f in reading if f["source_id"] == first["source_id"]
               and first["timestamp"] - 0.5 <= f["timestamp"] <= r["timestamp"]]
        encs, order = {}, []
        for f in frs:
            if f["encounter_id"] not in encs:
                encs[f["encounter_id"]] = []; order.append(f["encounter_id"])
            encs[f["encounter_id"]].append(re.sub(r"^\[From '.*?'\]\s*", "", f["content"], count=1))
        want = n["sittings"] or 1
        take = order[:want]
        passage = " ".join(" ".join(encs[e]) for e in take)
        if len(take) < want or len(passage) < 800:
            stats["short_source"] += 1; continue
        stats["usable"] += 1
        usable.append({"fragment_id": r["fragment_id"], "ts": r["timestamp"], "note_file": str(p), **n,
                       "book_path": first["source_id"], "sittings_recovered": len(take),
                       "passage_chars": len(passage), "passage": passage})
    # "recent": evenly spaced across the a.pool most recent usable notes (newest first), so one binge on one book
    # cannot be the whole sample; deterministic.
    step = max(1, len(usable) // a.n)
    sample = usable[::step][: a.n]
    for s_ in sample:
        s_["passage_seen"] = s_["passage"][:5000]   # core/study_note.compose_note sends passage[:5000] (the live Du
        # process of 2026-11-05 predates D-0577 chunking: data/study_note_chunking_log.jsonl does not exist)
    json.dump({"stats": stats, "n": len(sample), "sample": sample}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(stats, "sample", len(sample), "books", len({s['book'] for s in sample}),
          "facts", sum(len(s['key_facts']) for s in sample))


if __name__ == "__main__":
    main()

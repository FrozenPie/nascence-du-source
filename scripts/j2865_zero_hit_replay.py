"""J-2865 replay: how many of the logged zero-hit librarian asks does heading normalisation rescue?

Read-only. Reads the live data/librarian_log.jsonl (path argument, default C:/Nascence/data/...), runs the
CURRENT core.librarian.normalise_headings over the headings of every n_hits==0 row that had headings, and
re-runs library_hand.search_by_subjects (catalogue CSV, read-only) with rank="distinct". Writes the
per-row result and a summary under the output dir (default docs/lab/J-2865_data). No model calls, no Ramses.
"""
import json, sys, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import librarian, library_hand  # noqa: E402  (core before lab_env)

log = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:/Nascence/data/librarian_log.jsonl")
out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "docs" / "lab" / "J-2865_data"
out.mkdir(parents=True, exist_ok=True)
random.seed(2865)
rows = [json.loads(l) for l in open(log, encoding="utf-8") if l.strip()]
zero = [r for r in rows if r.get("n_hits", 0) == 0 and r.get("subjects")]
res, rescued, unchanged = [], 0, 0
for r in zero:
    alt = librarian.normalise_headings(r["subjects"])
    same = [a.lower() for a in alt] == [x.lower().strip() for x in r["subjects"]]
    if same or not alt:
        unchanged += 1
        res.append({"question": r["question"][:100], "subjects": r["subjects"], "alt": alt, "n": 0, "same": True})
        continue
    hits = library_hand.search_by_subjects(alt, 8, "distinct")
    if hits:
        rescued += 1
    res.append({"question": r["question"][:100], "subjects": r["subjects"], "alt": alt,
                "n": len(hits), "titles": [h["title"][:50] for h in hits[:5]]})
summary = {"log_rows": len(rows), "zero_hit_with_headings": len(zero), "normalisation_changes_nothing": unchanged,
           "rescued": rescued, "rescued_share_of_zero": round(rescued / max(1, len(zero)), 3)}
(out / "zero_hit_replay.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in res), encoding="utf-8")
(out / "zero_hit_replay_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps(summary))

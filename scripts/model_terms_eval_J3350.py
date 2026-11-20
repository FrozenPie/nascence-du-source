"""J-3350 acceptance: replay core.model_terms.detect over every row of data/curiosity_log.jsonl.

Read-only against the live DB (mode=ro) and the live curiosity log; the index cache goes to a temp dir.
Run from the worktree:  python scripts/model_terms_eval_J3350.py [db_path] [curiosity_log_path]
Prints counts and a few pointers only. Context per row = logged themes + seeds (study snippets were not logged, which
is also what the prototype had), asof = the row's own timestamp.
"""
from __future__ import annotations
import json, pathlib, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                      # noqa: E402  (before anything else)
from core import model_terms as mt   # noqa: E402

db = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("C:/Nascence/data/memory/nascence.db")
log = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("C:/Nascence/data/curiosity_log.jsonl")
tmp = pathlib.Path(tempfile.mkdtemp(prefix="j3350_eval_"))
t0 = time.time()
idx = mt.FirstSeenIndex(db, tmp / "idx.json")
nfrag = idx.refresh()
print(f"index: {nfrag} fragments, {len(idx.first)} terms, {time.time() - t0:.1f}s")

rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
flagged, terms, hits = 0, {}, {}
for r in rows:
    qs = list(r.get("questions") or []) + list(r.get("directions") or [])
    ctx = " ".join(str(x) for x in (r.get("recent_themes") or []) + (r.get("seeds_offered") or []))
    ts = float(r.get("ts") or 0)
    got = mt.detect(qs, ctx, ts, idx)
    if got:
        flagged += 1
        for t in got:
            terms[t] = terms.get(t, 0) + 1
        for key in ("mottainai", "omotenashi", "ichigo", "ichie"):
            if key in got:
                hits[key] = hits.get(key, 0) + 1
print(f"rows {len(rows)}, flagged {flagged} ({100.0 * flagged / max(1, len(rows)):.1f} percent), distinct terms {len(terms)}")
print("named terms:", hits)
print("top terms:", sorted(terms.items(), key=lambda kv: -kv[1])[:25])

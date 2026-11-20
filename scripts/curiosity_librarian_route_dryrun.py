"""J-4267 read-only dry-run for docs/staged/curiosity_librarian_route.md Open Q1-Q3.

Samples real frontier questions (data/frontier.json, READ ONLY), runs core.librarian.subjects_for (one
judge-hub call each) then core.library_hand.search_by_subjects (CSV scan), with the librarian's own
normalise_headings retry as ask() does. Never calls request_book/present_page/ask/attach_finding.
Live-store safety: the librarian parse-fail log is redirected to the output dir, and a sha256 canary over
the data/ files that could be touched is compared before/after (call_node telemetry may append to llm logs;
those are reported, not hidden).
"""
import asyncio, hashlib, json, random, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (before any lab_env)
from core import librarian, library_hand

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scratch"
OUT.mkdir(parents=True, exist_ok=True)
librarian._PARSE_FAIL_LOG = OUT / "J-4267_parse_fail.jsonl"

WATCH = ["frontier.json", "librarian_log.jsonl", "llm_json_parse_fail.jsonl", "evidence_log.jsonl",
         "curiosity_log.jsonl"]


def snap():
    out = {}
    for n in WATCH:
        p = ROOT / "data" / n
        out[n] = hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.exists() else None
    return out


def sample(n_open=20, n_faded=20):
    qs = json.load(open(ROOT / "data" / "frontier.json", encoding="utf-8"))["questions"]
    op = [q for q in qs if q.get("status") in ("open", "provisional", "parked")]
    op.sort(key=lambda q: -q.get("born", 0))
    fd = [q for q in qs if q.get("status") == "faded" and q.get("kind") == "question" and len(q["q"]) >= 25]
    fd.sort(key=lambda q: -q.get("born", 0))
    return op[:n_open], fd[:n_faded]


async def main():
    before = snap()
    op, fd = sample()
    rows = []
    for grp, lst in (("open", op), ("faded", fd)):
        for q in lst:
            t0 = time.time()
            subs = await librarian.subjects_for(q["q"])
            hits, used = [], subs
            if subs:
                hits = library_hand.search_by_subjects(subs, 8, "distinct")
                if not hits:
                    alt = librarian.normalise_headings(subs)
                    if alt and [a.lower() for a in alt] != [x.lower() for x in subs]:
                        hits = library_hand.search_by_subjects(alt, 8, "distinct")
                        if hits:
                            used = alt
            rows.append({"grp": grp, "id": q["id"], "q": q["q"], "source": q.get("source"),
                         "kind": q.get("kind"), "subjects": subs, "used": used,
                         "n_hits": len(hits), "secs": round(time.time() - t0, 1),
                         "cands": [{"title": h["title"][:90], "author": (h["author"] or "")[:30],
                                    "dl": h["downloads"], "subjects": (h["subjects"] or "")[:200]}
                                   for h in hits[:5]]})
    after = snap()
    json.dump({"rows": rows, "canary_before": before, "canary_after": after},
              open(OUT / "J-4267_dryrun_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = len(rows)
    nosubs = sum(1 for r in rows if not r["subjects"])
    hit = sum(1 for r in rows if r["n_hits"] > 0)
    print(f"n={n} no_subjects={nosubs} hit={hit} ({hit/n:.1%}) zero_hit={n-hit} "
          f"zero_hit_with_subjects={n-hit-nosubs}")
    for g in ("open", "faded"):
        s = [r for r in rows if r["grp"] == g]
        print(g, len(s), "hit", sum(1 for r in s if r["n_hits"] > 0))
    print("canary changed:", {k: (before[k], after[k]) for k in before if before[k] != after[k]})


asyncio.run(main())

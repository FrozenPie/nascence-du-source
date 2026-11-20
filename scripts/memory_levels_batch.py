"""
One-off BATCH shadow-distill over recent CLEAN level-0 raw — generates the Memory-Levels Phase-1 evidence
battery in one pass instead of waiting days for sleep-paced accrual. Offline, read-only on Du's behaviour
(it only reads fragments + calls the LLM/Emissary), appends to the same shadow log, and prints the battery.
Uses the SAME pipeline as core.memory_levels.shadow_distill: cluster -> distil gist -> Emissary faithfulness
-> deterministic source_fidelity -> the invention backstop. Finer clustering (several clusters per kind) so we
get ~20 gists rather than the live probe's 1-per-kind.
"""
import asyncio
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))   # project root on path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from core.model_client import call_node_json
from core.schema import SERVE_CHAINS
from core import memory_levels as ml
from core import left_lane

_BASE = SERVE_CHAINS["background"]
_LOG = Path(__file__).parent.parent / "data" / "memory_levels_shadow.jsonl"
MAX_CLUSTERS = 20


def _fetch():
    from core.memory.store import _connect
    # `self` mode targets the self-material stream (the river — the loop-breaking gating case);
    # default scans all raw origins (reading-heavy right now).
    origins = ("subconscious_synthesis", "inner_thought", "lived") \
        if (len(sys.argv) > 1 and sys.argv[1] == "self") else ml._RAW_ORIGINS
    ph = ",".join("?" * len(origins))
    with _connect() as conn:
        return conn.execute(
            f"SELECT fragment_id, content, origin, keywords, timestamp FROM memory_fragments "
            f"WHERE abstraction_level = 0 AND cold = 0 AND origin IN ({ph}) "
            f"ORDER BY timestamp DESC LIMIT 450", origins).fetchall()


def _batch_cluster(rows):
    """Finer than the live probe: several topic-clusters per kind (non-overlapping), biggest first."""
    by_kind = defaultdict(list)
    for r in rows:
        k = ml._KIND.get(r["origin"])
        if k:
            by_kind[k].append(r)
    clusters = []
    for kind, krows in by_kind.items():
        buckets = defaultdict(list)
        for r in krows:
            kw = r["keywords"] if "keywords" in r.keys() else ""
            for tok in set(ml._tokens(kw, r["content"])):
                buckets[tok].append(r)
        taken = set()
        for tok, brows in sorted(buckets.items(), key=lambda kv: len(kv[1]), reverse=True):
            uniq = [r for r in brows if r["fragment_id"] not in taken]
            if len(uniq) >= ml._MIN_CLUSTER:
                cl = uniq[:ml._MAX_SOURCES]
                clusters.append((kind, tok, cl))
                taken.update(r["fragment_id"] for r in cl)
    clusters.sort(key=lambda c: len(c[2]), reverse=True)
    return clusters[:MAX_CLUSTERS]


async def _distil(kind, topic, material):
    _sys = ("/no_think\nThese are raw memory fragments of one kind, on one topic. Distil them into ONE short "
            "GIST that could stand in for them in ordinary recall — the technique / event / idea / feeling they "
            "amount to, NOT a list of them. Keep what they actually say; invent nothing. 2-4 sentences. Output "
            "ONLY JSON: {\"gist\": \"...\"}")
    try:
        data = await call_node_json(_BASE, _sys, f"Kind: {kind}. Topic: {topic}.\n\n{material[:4000]}",
                                    max_tokens=300, temperature=0.3)
        return str((data or {}).get("gist") or "").strip()
    except Exception:
        return ""


async def main():
    rows = _fetch()
    clusters = _batch_cluster(rows)
    print(f"scanned {len(rows)} clean level-0 raw fragments -> {len(clusters)} clusters\n")
    results = []
    for i, (kind, topic, crows) in enumerate(clusters, 1):
        sources = [" ".join((r["content"] or "").split())[:300] for r in crows]
        full_sources = [" ".join((r["content"] or "").split()) for r in crows]
        gist = await _distil(kind, topic, "\n".join(f"- {s}" for s in sources))
        if len(gist) < 40:
            print(f"  [{i:>2}/{len(clusters)}] {kind}/{topic}: (gist too short, skipped)")
            continue
        grade = await left_lane.grade_gist_faithfulness(gist, [s[:800] for s in full_sources])
        faithful = grade.get("faithful") if isinstance(grade, dict) else None
        invented = (grade or {}).get("invented", []) if isinstance(grade, dict) else []
        claims = ml.verify_invention_claims(invented, full_sources) if invented else []
        false_flags = sum(1 for c in claims if c[1] in ("IN_SOURCE", "CROSS_LINK"))
        sfid = ml.source_fidelity(gist, full_sources)
        rec = {"ts": time.time(), "kind": kind, "topic": topic, "n_sources": len(crows),
               "source_ids": [r["fragment_id"] for r in crows], "gist": gist[:400],
               "faithful": faithful, "source_fidelity": sfid,
               "feedback": (grade or {}).get("feedback", "")[:200] if isinstance(grade, dict) else "",
               "invented_claims": claims, "false_flags": false_flags,
               "source_sample": sources[0][:160] if sources else "", "batch": True}
        try:
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        results.append(rec)
        print(f"  [{i:>2}/{len(clusters)}] {kind:<9}/{topic:<14} faithful={faithful} src_fid={sfid} "
              f"false_flags={false_flags}")

    # ---- the battery ----
    print("\n" + "=" * 70 + "\n  PHASE-1 EVIDENCE BATTERY\n" + "=" * 70)
    fa = [r["faithful"] for r in results if isinstance(r["faithful"], (int, float))]
    sf = [r["source_fidelity"] for r in results if isinstance(r["source_fidelity"], (int, float))]
    selfk = [r for r in results if r["kind"] == "self"]
    n_claims = sum(len(r["invented_claims"]) for r in results)
    n_false = sum(r["false_flags"] for r in results)
    agree = [1 for r in results if isinstance(r["faithful"], (int, float))
             and isinstance(r["source_fidelity"], (int, float))
             and abs(r["faithful"] - r["source_fidelity"]) <= 0.25]
    print(f"  gists graded         : {len(fa)}")
    print(f"  mean_faithful (LLM)  : {round(sum(fa)/len(fa),3) if fa else None}   (gate: >= ~0.75)")
    print(f"  mean source_fidelity : {round(sum(sf)/len(sf),3) if sf else None}   (gate: >= ~0.6, deterministic)")
    print(f"  the two AGREE (+/-0.25): {len(agree)}/{len(fa)}   (the real gate — independent signals concur)")
    print(f"  self-kind gists      : {len(selfk)}  " +
          (f"faithful={[r['faithful'] for r in selfk]}" if selfk else "(none — need self-material)"))
    print(f"  invention claims     : {n_claims} total · {n_false} were FALSE flags (backstop overturned)")
    print("\n  5 clusters to eyeball for sane gist<->raw links:")
    for r in results[:5]:
        print(f"   - [{r['kind']}/{r['topic']}] f={r['faithful']} sf={r['source_fidelity']}")
        print(f"       gist: {r['gist'][:150]}")
        print(f"       raw : {r['source_sample'][:110]}")


if __name__ == "__main__":
    asyncio.run(main())

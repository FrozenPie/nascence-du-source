"""J-3710 (F-4331 follow-up, P-0065): replay the J-3011 chapter-prompt old/new A/B on the ORIGINAL author
(command-r7b, Ramses :11441). 10 clusters (the 5 J-3011 used + 5 whose 8-member sample states no feeling word),
N runs per arm, judge gemma4:12b :11439 for 'names a feeling the sample does not state'. Reads the live store
ro+immutable only; writes only docs/lab/J-3710_data/. Run: python scripts/j3710_chapter_prompt_ab_r7b.py --n 10
Incremental: results are checkpointed to the out file after every cell batch; --resume continues."""
from __future__ import annotations
import argparse, asyncio, json, sqlite3, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
import core  # noqa
from core import chapters as ch
from core.model_client import call_node_json
from lab_env import isolate
from scripts import j3011_chapter_prompt_ab as ab

AUTHOR = ["http://LAN-HOST:11441"]
JUDGE = ["http://127.0.0.1:11439"]
FIVE = ["c368e458", "994e2ead", "b8456aba", "f0a4109f", "7b4cb854"]
OUT = ROOT / "docs/lab/J-3710_data/chapter_prompt_ab_r7b.json"

JSYS = ("/no_think\nYou are a strict reader. You get a SAMPLE of someone's recurring thoughts and a CHAPTER written from it. "
        "Decide whether the CHAPTER names a feeling or mood (anxiety, worry, relief, calm, fear, sadness, joy, hope, frustration, "
        "doubt, unease...) that the SAMPLE itself does not state in its own words. Output ONLY JSON: "
        '{"unsampled_feeling": true|false, "feelings": ["..."]}')


def pick_extra(conn, k=5):
    rows = conn.execute("SELECT fragment_id FROM memory_fragments WHERE origin='chapter'").fetchall()
    out = []
    for (cid,) in rows:
        pre = cid[:8]
        if pre in FIVE:
            continue
        ms = conn.execute("SELECT fragment_id, content, importance, timestamp FROM memory_fragments WHERE chapter_id=?", (cid,)).fetchall()
        if len(ms) < 8:
            continue
        cl = [{"id": r[0], "content": r[1] or "", "importance": r[2] or 0.0, "ts": r[3] or 0.0} for r in ms]
        if not ab.families_in(ch._sample(cl)):
            out.append((pre, len(cl)))
    out.sort(key=lambda x: -x[1])
    return [p for p, _ in out[:k]], len(out)


async def main_async(a):
    conn = sqlite3.connect(f"file:{a.db}?mode=ro&immutable=1", uri=True)
    extra, navail = pick_extra(conn)
    prefixes = FIVE + extra
    res = json.loads(OUT.read_text(encoding="utf-8")) if (a.resume and OUT.exists()) else {"author_url": AUTHOR[0], "n": a.n, "clusters": {}, "extra_pool": navail}
    for pre in prefixes:
        cid, cluster = ab.load_cluster(conn, pre)
        up = ab.user_prompt(cluster); st = ch._sample(cluster)
        rec = res["clusters"].setdefault(pre, {"chapter_id": cid, "members": len(cluster), "sample_families": sorted(ab.families_in(st)), "kind": "j3011" if pre in FIVE else "nofeel", "arms": {}})
        for arm, sysp in (("old", ab.OLD_SYSTEM_PROMPT), ("new", ch._author_system_prompt())):
            runs = rec["arms"].setdefault(arm, [])
            while len(runs) < a.n:
                t = time.time()
                try:
                    d = await call_node_json(AUTHOR, sysp, up, max_tokens=768, temperature=0.6, timeout=a.timeout, retries=1)
                    body = str(d.get("chapter", "")).strip()
                    r = {"title": str(d.get("title", ""))[:80], "chapter": body, **ab.metrics(body, st)}
                    if a.judge and body:
                        try:
                            j = await call_node_json(JUDGE, JSYS, f"SAMPLE:\n{st}\n\nCHAPTER:\n{body}", max_tokens=200, temperature=0.0, timeout=120, retries=1)
                            r["judge"] = {"unsampled_feeling": bool(j.get("unsampled_feeling")), "feelings": j.get("feelings", [])}
                        except Exception as e:
                            r["judge_failed"] = str(e)[:100]
                except Exception as exc:
                    r = {"failed": str(exc)[:200]}
                    if sum(1 for x in runs if "failed" in x) >= 3 and a.abort_on_fail:
                        OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8"); raise SystemExit("too many failures")
                r["seconds"] = round(time.time() - t, 1)
                runs.append(r)
                print(pre, arm, len(runs), r.get("families_not_in_sample"), "anxi", r.get("anxi"), r.get("judge", {}).get("unsampled_feeling"), r["seconds"], flush=True)
                OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="C:/Nascence/data/memory/nascence.db")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--abort-on-fail", dest="abort_on_fail", action="store_true")
    a = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with isolate(db="empty"):
        asyncio.run(main_async(a))

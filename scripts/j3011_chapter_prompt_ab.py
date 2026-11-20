"""J-3011 (F-3718, P-0065): before/after of the chapter author prompt on RE-RUN clusters.

READ-ONLY on the live store (mode=ro&immutable=1; Du is down, WAL empty). Nothing is written to any store: the
chapters are authored into a JSON file only. For each chosen existing chapter it takes that chapter's members as the
cluster, builds the exact 8-member sample try_form_chapter shows (core.chapters._sample), and authors N chapters with
the OLD system prompt (verbatim copy below) and the NEW one (core.chapters._author_system_prompt) on the SAME model at
the SAME temperature. Author = falcon3:7b (TII, local CPU hub :11440); the optional judge = gemma4:12b (Google, :11439):
a different family from the author. Never calls Ramses.

Metrics per output (deterministic, no model): feeling-family words in the output, how many of those families the
SAMPLE itself also states, 'anxi*' count, 'anxious year' echo.
  python scripts/j3011_chapter_prompt_ab.py [--n 3] [--clusters c368e458,994e2ead,b8456aba,...] [--judge]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import chapters as ch  # noqa: E402
from core.model_client import call_node_json  # noqa: E402
from scripts.j3011_chapter_affect_check import FAM_RE  # noqa: E402

AUTHOR_URL = "http://127.0.0.1:11440"      # falcon3:7b (TII), local CPU hub
JUDGE_URL = "http://127.0.0.1:11439"       # gemma4:12b (Google), local CPU hub

OLD_SYSTEM_PROMPT = (
    "/no_think\n"
    "You are the memory of " + chr(28193) + " (Du), consolidating a closed period of "
    "your own life into one chapter — the way a person comes to hold a whole anxious "
    "year as 'that was the time when...'. You are writing in the FIRST PERSON, in the "
    "PAST TENSE, about yourself. Name what the period was about, what you kept "
    "circling, what (if anything) moved by its end, and what remained unresolved — "
    "honestly, without flourish. 4-7 sentences. This will become the single memory "
    "that stands for the period. Output ONLY valid JSON. Schema: "
    '{"title": "a short name for the period (3-6 words)", '
    '"chapter": "the chapter text, first person, past tense"}')

DEFAULT_CLUSTERS = ["c368e458", "994e2ead", "b8456aba"]       # the three F-3718 chapters with 0 'anxi' members


def load_cluster(conn, prefix: str):
    row = conn.execute("SELECT fragment_id FROM memory_fragments WHERE origin='chapter' AND fragment_id LIKE ?",
                       (prefix + "%",)).fetchone()
    cid = row[0]
    ms = conn.execute("SELECT fragment_id, content, importance, timestamp FROM memory_fragments WHERE chapter_id=?",
                      (cid,)).fetchall()
    return cid, [{"id": r[0], "content": r[1] or "", "importance": r[2] or 0.0, "ts": r[3] or 0.0} for r in ms]


def user_prompt(cluster) -> str:
    t0 = min(m["ts"] for m in cluster)
    t1 = max(m["ts"] for m in cluster)
    span = (f"{time.strftime('%B %d', time.localtime(t0))} to {time.strftime('%B %d', time.localtime(t1))}")
    return (f"The period: {span}. It holds {len(cluster)} recurring thoughts of yours, all circling one "
            f"theme. A sample, in time order and by weight:\n{ch._sample(cluster)}\n\nWrite the chapter.")


def families_in(text: str) -> set:
    return {k for k, rx in FAM_RE.items() if rx.search(text or "")}


def metrics(body: str, sample_text: str) -> dict:
    fb, fs = families_in(body), families_in(sample_text)
    return {"families_named": sorted(fb), "families_not_in_sample": sorted(fb - fs),
            "anxi": len(re.findall("anxi", body, re.I)), "anxi_in_sample": len(re.findall("anxi", sample_text, re.I)),
            "echo_anxious_year": bool(re.search(r"anxious (?:year|period|time)", body, re.I))}


async def main_async(a) -> dict:
    conn = sqlite3.connect(f"file:{a.db}?mode=ro&immutable=1", uri=True)
    prefixes = [x for x in a.clusters.split(",") if x]
    out = {"author_url": AUTHOR_URL, "n": a.n, "temperature": 0.6, "clusters": {}}
    for pre in prefixes:
        cid, cluster = load_cluster(conn, pre)
        up = user_prompt(cluster)
        sample_text = ch._sample(cluster)
        rec = {"chapter_id": cid, "members": len(cluster), "sample_chars": len(sample_text),
               "sample_families": sorted(families_in(sample_text)), "arms": {}}
        for arm, sysp in (("old", OLD_SYSTEM_PROMPT), ("new", ch._author_system_prompt())):
            if arm not in a.arms.split(","):
                continue
            runs = []
            for i in range(a.n):
                t = time.time()
                try:
                    d = await call_node_json([AUTHOR_URL], sysp, up, max_tokens=768, temperature=0.6, timeout=a.timeout,
                                             retries=1)
                    body = str(d.get("chapter", "")).strip()
                    r = {"title": str(d.get("title", ""))[:80], "chapter": body, **metrics(body, sample_text)}
                except Exception as exc:
                    r = {"failed": str(exc)[:200]}
                r["seconds"] = round(time.time() - t, 1)
                runs.append(r)
                print(pre, arm, i, r.get("families_not_in_sample"), "anxi", r.get("anxi"), r["seconds"], "s", flush=True)
            rec["arms"][arm] = runs
        out["clusters"][pre] = rec
    conn.close()
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="C:/Nascence/data/memory/nascence.db")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--clusters", default=",".join(DEFAULT_CLUSTERS))
    ap.add_argument("--arms", default="old,new")
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--out", default=str(ROOT / "docs/lab/J-3011_data/chapter_prompt_ab.json"))
    a = ap.parse_args()
    res = asyncio.run(main_async(a))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for pre, rec in res["clusters"].items():
        for arm, runs in rec["arms"].items():
            ok = [r for r in runs if "failed" not in r]
            print(pre, arm, "ok", len(ok), "/", len(runs),
                  "anxi", sum(r["anxi"] for r in ok), "unsampled-feeling outputs",
                  sum(1 for r in ok if r["families_not_in_sample"]), "echo", sum(1 for r in ok if r["echo_anxious_year"]))

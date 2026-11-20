"""
J-3031 (F-3739): replay the stored (letter, reply) pairs behind Du's first 32 stored peer reflections through the OLD
prompt (900-char caps, "His letter", old wording) and the NEW prompt (core/peer_model.update_after_exchange as it is in
this tree), with and without the "what you made of them last time" line, and COUNT second-person, first-person and
"nothing new" outputs with the same deterministic measures the live quality log uses (peer_model.quality_row).

LAB ONLY. Reads C:\\Nascence\\data read-only (the DB through a mode=ro&immutable=1 URI, thread.jsonl files as text);
every write goes under the lab_env.isolate() dir (empty DB, redirected peer_models.json and quality log); telemetry is
neutralised (scripts/lab_isolation.py). Local hub only (default the hot lane :11433, the model Du's reflection really
runs on; --url picks another). Never Ramses. No judge is involved: the measures are regex/shingle counts, so there is
no author-versus-judge family question; the AUTHOR model is named in the output.

Usage: python scripts/J-3031_reflection_replay.py [--url http://127.0.0.1:11433] [--limit 32] [--out FILE]
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (BEFORE lab_env)
from core import peer_model  # noqa: E402
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import lab_isolation  # noqa: E402

assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__

LIVE = Path(r"C:\Nascence\data")

# The pre-J-3031 system prompt, verbatim from master 223c95c6 core/peer_model.py (for the OLD arm).
OLD_SYS = (
    "You are 渡, thinking privately to yourself about a friendship -- not writing to anyone, not "
    "composing a letter. Given your friend {name}'s latest letter and your reply to it, what do you now "
    "understand about who {name} is and what your friendship is? Two or three short lines, plain and "
    "specific -- concrete things about THEM (their life, their voice, what they care about, something "
    "particular they said), never about yourself or your own nature. No flattery, no generic warmth "
    "(\"a kind friend who cares about me\") -- if nothing specific struck you this time, say that plainly "
    "rather than invent something. Output ONLY JSON: "
    "{{\"reflection\": \"...\", \"topics\": [\"a few words each\"]}}"
)


def build_pairs(limit: int) -> list:
    con = sqlite3.connect("file:" + (LIVE / "memory" / "nascence.db").as_posix() + "?mode=ro&immutable=1", uri=True)
    rows = con.execute("SELECT timestamp, keywords, content FROM memory_fragments WHERE origin='peer_reflection' "
                       "ORDER BY timestamp").fetchall()
    con.close()
    threads = {}
    pairs, prev_by_peer = [], {}
    for ts, kw, content in rows[:limit]:
        toks = (kw or "").split()
        persona = toks[1] if len(toks) > 1 else ""
        m = re.match(r"\(what you've come to understand of ([^)]+)\)\s*(.*)", content or "", re.S)
        name, text = (m.group(1), m.group(2)) if m else (persona, content or "")
        if persona not in threads:
            f = LIVE / "Correspondence" / persona / "thread.jsonl"
            threads[persona] = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()] \
                if f.exists() else []
        th = threads[persona]
        du = [(i, r) for i, r in enumerate(th) if r.get("from") == "du" and float(r.get("ts", 0)) <= ts + 5]
        if not du:
            continue
        i, dr = du[-1]
        letter = next((r["text"] for r in reversed(th[:i]) if r.get("from") == persona), "")
        pairs.append({"persona": persona, "name": name, "stored": text.strip(), "letter": letter, "reply": dr["text"],
                      "gap_s": round(ts - float(dr["ts"]), 1), "prev": prev_by_peer.get(persona)})
        prev_by_peer[persona] = text.strip()
    return pairs


def summarise(rows: list) -> dict:
    n = len(rows)
    ov = [r for r in rows if r["q"].get("overlap_contain") is not None]
    return {
        "n": n,
        "starts_with_you": sum(1 for r in rows if r["q"]["starts_with_you"]),
        "has_you": sum(1 for r in rows if r["q"]["has_you"]),
        "first_person": sum(1 for r in rows if r["q"]["first_person_n"] > 0),
        "nothing_new": sum(1 for r in rows if r["q"]["nothing_new"]),
        "empty": sum(1 for r in rows if not r["text"]),
        "overlap_n": len(ov),
        "overlap_contain_ge_0.5": sum(1 for r in ov if r["q"]["overlap_contain"] >= 0.5),
        "overlap_contain_mean": round(sum(r["q"]["overlap_contain"] for r in ov) / len(ov), 3) if ov else None,
        "mean_len": round(sum(r["q"]["len"] for r in rows) / n, 1) if n else None,
    }


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:11433")
    ap.add_argument("--limit", type=int, default=32)
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3031_data" / "replay_results.json"))
    ap.add_argument("--arms", default="old,new_noprev,new_prev", help="comma list of arms to run")
    ap.add_argument("--dry-run", action="store_true", help="build the pairs and the prompts, call nothing")
    a = ap.parse_args()
    pairs = build_pairs(a.limit)
    print(f"pairs built: {len(pairs)} (gap seconds reply->reflection: min {min(p['gap_s'] for p in pairs)}, "
          f"max {max(p['gap_s'] for p in pairs)})")
    if a.dry_run:
        return 0
    from core.model_client import call_node_json
    saved = lab_isolation.neutralize_telemetry()
    arms = [x for x in a.arms.split(",") if x]
    results = {k: [] for k in arms}
    t0 = time.time()
    with isolate(db="empty", also=[(peer_model, ["_PEER_MODEL_PATH", "_QUALITY_LOG"])]) as lab:
        async def real(base_urls, sys_p, user_p, max_tokens=180, temperature=0.5):
            return await call_node_json([a.url], sys_p, user_p, max_tokens=max_tokens, temperature=temperature,
                                        timeout=150, retries=1)
        for p in pairs:
            q_args = (len(p["letter"]), len(p["reply"]), p["persona"])
            # OLD arm: the pre-J-3031 prompt and caps, verbatim.
            up = (("His letter:\n\"" + p["letter"][:900] + "\"\n\n") if p["letter"] else "") + \
                 "Your reply:\n\"" + p["reply"][:900] + "\""
            if "old" in arms:
                try:
                    d = await real([a.url], OLD_SYS.format(name=p["name"]), up)
                    text = str((d or {}).get("reflection", "")).strip()
                except Exception as exc:
                    text = ""
                    print("old call failed:", repr(exc)[:120])
                results["old"].append({"persona": p["persona"], "text": text, "stored": p["stored"],
                                       "q": peer_model.quality_row(text, p["prev"], *q_args)})
            # NEW arms through the real update_after_exchange (own prompt build, own caps), prev seeded in the lab.
            for arm, with_prev in (("new_noprev", False), ("new_prev", True)):
                if arm not in arms:
                    continue
                peer_model._PREV_REFLECTION_IN_PROMPT = with_prev
                peer_model._PEER_MODEL_PATH.write_text(json.dumps(
                    {p["persona"]: {"name": p["name"], "recent_reflections": ([{"ts": 1.0, "text": p["prev"]}]
                                                                              if p["prev"] else [])}}), encoding="utf-8")
                seen = {}

                async def spy(base_urls, sys_p, user_p, max_tokens=180, temperature=0.5):
                    seen["user"] = user_p
                    return await real(base_urls, sys_p, user_p, max_tokens=max_tokens, temperature=temperature)
                try:
                    text = await peer_model.update_after_exchange(spy, [a.url], p["persona"], p["name"],
                                                                  p["letter"], p["reply"]) or ""
                except Exception as exc:
                    text = ""
                    print(arm, "call failed:", repr(exc)[:120])
                results[arm].append({"persona": p["persona"], "text": text, "prompt_chars": len(seen.get("user", "")),
                                     "q": peer_model.quality_row(text, p["prev"], *q_args,
                                                                 prev_in_prompt=with_prev and bool(p["prev"]))})
            print(f"  {p['persona']:10s} done  elapsed {time.time() - t0:.0f}s", flush=True)
    peer_model._PREV_REFLECTION_IN_PROMPT = False
    lab_isolation.restore_telemetry(__import__("core.telemetry", fromlist=["x"]), saved)
    out = {"url": a.url, "pairs": len(pairs), "stored_baseline": summarise(
        [{"text": p["stored"], "q": peer_model.quality_row(p["stored"], p["prev"], len(p["letter"]), len(p["reply"]),
                                                           p["persona"])} for p in pairs]),
           "summary": {k: summarise(v) for k, v in results.items()}, "rows": results}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"stored_baseline": out["stored_baseline"], **out["summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""
J-3162 / D-0550 pre-ship replay: would the T4 legacy author's candidates clear the admission bar (emissary_warranted >=
provisional_identity.WARRANTED_ADMIT_MIN = 0.6) if the judge were handed the lived `material` it read?

READ-ONLY. Reads data/logs/t4_emissary_judge.jsonl, data/nascence.log and data/memory/nascence.db (sqlite mode=ro) under
the LIVE data dir; writes ONLY to --out (a scratchpad file). Calls the judge-1 hub (:11439, the same judge the live
path uses; never the hot lane) with the identical system prompt and user-message shape as
left_lane.grade_self_revision_traced. It does NOT call the traced function itself, because that writes telemetry
(llm_latency) into the live data dir.

Legacy rows = a 'T4 decoupled-judge shadow' line in nascence.log with no 'T4 CHAIN' line in the preceding 600 s
(F-3763's method), matched to t4_emissary_judge.jsonl rows by timestamp.
Material for a row = newest 14 self-narrative fragments with  prev_judge_row_ts < ts <= row_ts  (the T4 gate sets
last_self_authoring on every attempt, so the window opens at the previous authoring attempt).
Caveat: old_self is not in pre-J-3108 rows; a fixed representative old self (the earliest logged one) is used.

  python scripts/replay_J-3162_legacy_gradeable.py --out <file> [--step 6] [--since 2026-09-29] [--until 2026-10-21]
"""
from __future__ import annotations
import argparse, asyncio, datetime as dt, json, re, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import left_lane as ll  # noqa: E402
import aiohttp  # noqa: E402

assert Path(ll.__file__).resolve().parent.parent == ROOT
LIVE = Path("C:/Nascence/data")
ORIGINS = ("session_summary", "subconscious_synthesis", "dream", "active_imagination")
ADMIT = 0.6


def legacy_ts(since, until):
    pat = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ .*\[subconscious\] T4 (CHAIN|decoupled-judge shadow)")
    last_chain = -1e18
    out = []
    with open(LIVE / "nascence.log", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = pat.match(line)
            if not m:
                continue
            t = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
            if m.group(2) == "CHAIN":
                last_chain = t
            elif t - last_chain > 600 and since <= t < until:
                out.append(t)
    return out


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--step", type=int, default=6)
    ap.add_argument("--since", default="2026-09-29")
    ap.add_argument("--until", default="2026-10-21")
    a = ap.parse_args()
    since = dt.datetime.fromisoformat(a.since).timestamp()
    until = dt.datetime.fromisoformat(a.until).timestamp()
    rows = [json.loads(l) for l in open(LIVE / "logs" / "t4_emissary_judge.jsonl", encoding="utf-8") if l.strip()]
    rows.sort(key=lambda r: r["ts"])
    old_self = next((r["old_self"] for r in rows if r.get("old_self")), "")
    lts = legacy_ts(since, until)
    legacy = []
    for t in lts:
        best = min(rows, key=lambda r: abs(r["ts"] - t))
        if abs(best["ts"] - t) < 5:
            legacy.append(best)
    print("legacy runs in log:", len(lts), "matched to judge rows:", len(legacy), flush=True)
    prev = {r["ts"]: (rows[i - 1]["ts"] if i else 0.0) for i, r in enumerate(rows)}
    sample = legacy[::a.step]
    print("replaying", len(sample), flush=True)
    conn = sqlite3.connect(f"file:{(LIVE / 'memory' / 'nascence.db').as_posix()}?mode=ro", uri=True)
    ph = ",".join("?" * len(ORIGINS))
    outf = open(a.out, "a", encoding="utf-8")
    async with aiohttp.ClientSession() as s:
        for r in sample:
            mat = conn.execute(
                f"SELECT content, origin, timestamp FROM memory_fragments WHERE origin IN ({ph}) "
                f"AND timestamp > ? AND timestamp <= ? ORDER BY timestamp DESC LIMIT 14",
                (*ORIGINS, prev[r["ts"]], r["ts"])).fetchall()
            ev = [f"[{o}] {(c or '')[:200].replace(chr(10), ' ')}" for c, o, _t in mat]
            evs = "\n".join(f"- {e}" for e in ev[:8] if e) or "(no lived evidence offered)"
            user = (f"His OLD sense of self:\n{(old_self or '')[:800]}\n\n"
                    f"The NEW self he proposes:\n{(r['candidate'] or '')[:800]}\n\n"
                    f"The lived evidence he offers as warrant:\n{evs[:2200]}")
            payload = {"model": ll.MODEL, "stream": False, "keep_alive": "30m",
                       "messages": [{"role": "system", "content": ll._revision_system()},
                                    {"role": "user", "content": user}],
                       "options": {"temperature": 0.0, "num_predict": ll.MAX_TOKENS, "num_gpu": 0}, "format": "json"}
            w = None; err = ""
            t0 = time.perf_counter()
            try:
                async with s.post(f"{ll.BASE_URL}/api/chat", json=payload,
                                  timeout=aiohttp.ClientTimeout(total=ll.JUDGE_TIMEOUT_S)) as resp:
                    resp.raise_for_status()
                    d = await resp.json()
                w = float(json.loads(d["message"]["content"])["warranted"])
            except Exception as e:
                err = repr(e)[:100]
            rec = {"ts": r["ts"], "day": dt.date.fromtimestamp(r["ts"]).isoformat(), "orig_warranted": r["emissary_warranted"],
                   "n_material": len(mat), "replay_warranted": w, "err": err, "s": round(time.perf_counter() - t0, 1),
                   "candidate": r["candidate"][:120]}
            outf.write(json.dumps(rec, ensure_ascii=False) + "\n"); outf.flush()
            print(rec["day"], len(mat), w, err, flush=True)


asyncio.run(main())

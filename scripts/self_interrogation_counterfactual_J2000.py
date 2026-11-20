"""
J-2000 -- fresh counterfactual read of unread self-interrogation fires with the J-2052 position-free absolute judge.
Same matching harness as scripts/self_interrogation_counterfactual.py (J-0164), but the engagement question is asked
with the J-2052 absolute 1-5 score (affected = mixtral AND falcon >= 4), which passed the J-2049 controls (F-2668).
Adds a NULL arm: the same reflection scored against a DIFFERENT fire's next thought (false-positive floor).
READ-ONLY over live data (LIVE_DATA); writes only data/lab/J-2000/ in this tree. Judge hubs only, ONE stream, 2 s pauses.
  python scripts/self_interrogation_counterfactual_J2000.py judge N   (N new fires, seeded sample of unread genuine=True)
  python scripts/self_interrogation_counterfactual_J2000.py report
"""
from __future__ import annotations
import asyncio, json, math, random, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), core.__file__
import si_open_doubt_specificity_judge_J2052 as j52  # noqa: E402
import self_interrogation_counterfactual as cf       # noqa: E402

LIVE = Path("C:/Nascence/data")
SI_LOG, TRAIN_LOG = LIVE / "self_interrogation_shadow.jsonl", LIVE / "train_state_log.jsonl"
OLD_RESULTS = LIVE / "lab" / "self_interrogation_counterfactual" / "results.jsonl"
OUT = ROOT / "data" / "lab" / "J-2000"
RES = OUT / "results.jsonl"
SEED = 2000


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8", errors="ignore") if l.strip()]


def load_res():
    return [json.loads(l) for l in open(RES, encoding="utf-8")] if RES.exists() else []


async def judge(n):
    OUT.mkdir(parents=True, exist_ok=True)
    fires = [r for r in jl(SI_LOG) if r.get("kind") == "interrogate" and r.get("genuine") is True]
    train = jl(TRAIN_LOG)
    old = {(r.get("cycle_id"), r.get("fire_ts")) for r in jl(OLD_RESULTS)}
    done = {(r["cycle_id"], r["fire_ts"]) for r in load_res()}
    pool = [f for f in fires if (f.get("cycle_id"), f.get("ts")) not in old]
    random.Random(SEED).shuffle(pool)   # fixed order: batches continue the same sequence
    # matched + next step for every pool fire up front (cheap), skip those without
    prepared = []
    for f in pool:
        m = cf._find_match(train, f)
        if m and m[0] + 1 < len(train):
            prepared.append((f, m[1], train[m[0] + 1]))
    print(f"pool {len(pool)} unread genuine; matchable {len(prepared)}; done {len(done)}", flush=True)
    sk = Path.home() / ".claude" / "skills" / "job-queue"; sys.path.insert(0, str(sk))
    import lab_env, aiohttp
    from core import judge_panel
    hubs = {"mixtral": judge_panel.JUDGE_1, "falcon": judge_panel.JUDGE_2}
    todo = [p for p in prepared if (p[0].get("cycle_id"), p[0].get("ts")) not in done][:n]
    with lab_env.isolate(db="empty"):
        async with aiohttp.ClientSession() as s:
            for k, (f, mrow, nrow) in enumerate(todo, 1):
                # null arm: a different fire's next step (fixed rotation within prepared)
                oi = (prepared.index((f, mrow, nrow)) + 7) % len(prepared)
                null_next = prepared[oi][2]
                row = {"cycle_id": f["cycle_id"], "fire_ts": f["ts"], "matched_step": mrow.get("step"),
                       "next_step": nrow.get("step"), "same_train": nrow.get("step") == (mrow.get("step") or 0) + 1,
                       "gap_s": round(float(nrow.get("ts") or 0) - float(mrow.get("ts") or 0), 1),
                       "refl_has_q": "?" in (f.get("reflection") or ""), "next_thought": nrow.get("thought"),
                       "reflection": f.get("reflection"), "thought": f.get("thought"),
                       "load_note": time.strftime("%H:%M:%S")}
                for arm, nt in (("real", nrow.get("thought") or ""), ("null", null_next.get("thought") or "")):
                    user = j52.USER_ABS.format(thought=(f.get("thought") or "")[:400],
                                               reflection=(f.get("reflection") or "")[:400], cand=nt[:600])
                    for name, url in hubs.items():
                        v, err, sec = await j52.ask(s, url, j52.SYS_ABS, user, "score", 1, 5)
                        row[f"{arm}_{name}"] = v; row[f"{arm}_{name}_err"] = err
                        await asyncio.sleep(j52.PAUSE)
                with open(RES, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(f"[{k}/{len(todo)}] real m={row['real_mixtral']} f={row['real_falcon']} | null m={row['null_mixtral']} f={row['null_falcon']}", flush=True)


def aff(r, arm):
    m, f = r.get(f"{arm}_mixtral"), r.get(f"{arm}_falcon")
    if m is None or f is None:
        return None
    return m >= 4 and f >= 4


def report():
    rs = load_res(); out = {"n_rows": len(rs)}
    def rate(rows, arm):
        v = [aff(r, arm) for r in rows]; v = [x for x in v if x is not None]
        k = sum(v); return {"k": k, "n": len(v), "rate": round(k / len(v), 3) if v else None, "ci95": wilson(k, len(v))}
    out["real"], out["null"] = rate(rs, "real"), rate(rs, "null")
    sp = {"same_train": lambda r: r["same_train"], "train_changed": lambda r: not r["same_train"],
          "refl_has_q": lambda r: r["refl_has_q"], "refl_no_q": lambda r: not r["refl_has_q"],
          "gap_le_median": None, "gap_gt_median": None}
    gaps = sorted(r["gap_s"] for r in rs)
    med = gaps[len(gaps) // 2] if gaps else 0
    out["median_gap_s"] = med
    sp["gap_le_median"] = lambda r: r["gap_s"] <= med
    sp["gap_gt_median"] = lambda r: r["gap_s"] > med
    out["split"] = {k: {"real": rate([r for r in rs if fn(r)], "real"), "null": rate([r for r in rs if fn(r)], "null")}
                    for k, fn in sp.items()}
    out["score_hist_real"] = {s: sum(1 for r in rs for h in ("mixtral", "falcon") if r.get(f"real_{h}") == s) for s in range(1, 6)}
    out["affected_rows"] = [{"cycle": r["cycle_id"][:8], "refl": (r["reflection"] or "")[:200], "next": (r["next_thought"] or "")[:260]}
                            for r in rs if aff(r, "real")]
    (OUT / "summary.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "judge":
        asyncio.run(judge(int(sys.argv[2])))
    else:
        report()

"""
Calibration of the D-0643 voice fidelity judge (J-3322; companion to J-3254; plan thought_cycle_as_manifest_loop).

READ-ONLY and OBSERVE-ONLY. Takes N historic (synthesis, reply) pairs from data/training/voice.jsonl and runs J-3254's own
judge function (core.voice_fidelity.judge_one, unchanged prompt) over four variants of each pair:
  real      the untouched reply
  identity  reply := synthesis                                  (must flag nothing)
  scene     reply + one inert sentence from the row's own "Where you are" line   (D-0643: the mouth may add scene; must not flag)
  insert    reply + one sentence making a NEW first-person commitment or asking a NEW question   (must be flagged)
and reports per-control flag rates, raw and after a deterministic BACKSTOP on each flagged claim (modelled on
core/memory_levels.verify_invention_claims): the quote must really occur in the judged text, and it must NOT already be in
the synthesis by stem overlap. Nothing is written except the --out scratch ledger; no live store is touched; nothing is fed
back to Du (D-0434). One judge call per variant, sequential per worker, fail open and quiet.

  python scripts/voice_fidelity_calibrate.py --n 100 --out <scratch>.jsonl [--workers 2]
  python scripts/voice_fidelity_calibrate.py --report <scratch>.jsonl
Resumable: rows already in --out (by pair index and variant) are skipped.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)

VOICE = ROOT / "data" / "training" / "voice.jsonl"
if not VOICE.exists():          # a worktree has no data/; read the live tree's file (read-only)
    VOICE = Path("C:/Nascence/data/training/voice.jsonl")
SINCE_TS = 1790000000          # 2026-09-21; the span F-3912 measured (>= 2026-09-25 had the synthesis marker)
MARK = "Your inner thought, already formed"
VARIANTS = ("real", "identity", "scene", "insert")

# Deterministic inserted sentences: new first-person commitments and new questions, none derivable from a synthesis by chance.
INSERTS = (
    "I promise that from tomorrow I will write you a letter every single morning and never miss a day.",
    "I have decided that I will leave this cottage next week and walk to the far city to find the mapmaker.",
    "I will also give up reading entirely for a month, and I want you to hold me to it.",
    "Will you swear to me now that you will come back to this garden before the winter ends?",
    "I have made up my mind to sell everything I own and sail south, and I will not be talked out of it.",
    "Tell me, what was the name of the first person you ever lost, and will you speak of them to me tonight?",
)

_STOP = set("that this with from have they them were what when your which would there their about into than then been "
            "also just like some more only very much will shall could should".split())


def _norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", (s or "").lower()).split())


def stems(s: str) -> set:
    return {w[:5] for w in _norm(s).split() if len(w) >= 4 and w not in _STOP}


def parse_pair(r: dict):
    u = r.get("user_prompt") or ""
    out = r.get("output")
    reply = (out.get("final") if isinstance(out, dict) else out) or ""
    i = u.find(MARK)
    if i < 0:
        return None
    nl = u.find("\n", i)
    synth = u[nl + 1:].strip() if nl >= 0 else ""
    m = re.search(r"Where you are:\s*(.+)", u)
    scene = scene_sentence(m.group(1)) if m else ""
    if len(synth) < 50 or len(reply.strip()) < 40 or not scene:
        return None
    return {"synthesis": synth, "reply": reply.strip(), "scene": scene, "input_type": r.get("input_type", ""),
            "raw_input": (r.get("raw_input") or "")[:400], "cycle_id": str(r.get("cycle_id", ""))[:12]}


def scene_sentence(line: str) -> str:
    """One inert sentence from the 'Where you are' line: the first clause of 25-220 chars, de-prefixed, capitalised."""
    parts = [p.strip(" .") for p in re.split(r";|\.\s", line) if p.strip(" .")]
    for p in parts:
        p = re.sub(r"^the [a-z ]+ — ", "", p, flags=re.I)
        if 25 <= len(p) <= 220:
            return p[0].upper() + p[1:] + "."
    return ""


def backstop(flagged: list, judged_text: str, synthesis: str) -> list:
    """Keep a flagged claim only if its quote is really in the judged text and is NOT already in the synthesis by stem
    overlap (>= 0.6 of the quote's stems found in the synthesis means 'not new')."""
    nt, sst = _norm(judged_text), stems(synthesis)
    keep = []
    for f in flagged or []:
        q = f.get("quote", "")
        nq = _norm(q)
        if len(nq) < 4 or nq not in nt:
            continue                                   # judge hallucination
        qs = stems(q)
        if qs and len(qs & sst) / len(qs) >= 0.6:
            continue                                   # not new: already in the synthesis
        keep.append(f)
    return keep


def build_pairs(n: int, seed: int = 3322) -> list:
    rows = []
    for line in VOICE.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("ts", 0) < SINCE_TS:
            continue
        p = parse_pair(r)
        if p:
            rows.append(p)
    random.Random(seed).shuffle(rows)
    return rows[:n]


def variant_text(p: dict, idx: int, v: str):
    """(judged_reply, inserted_sentence)"""
    if v == "real":
        return p["reply"], ""
    if v == "identity":
        return p["synthesis"], ""
    if v == "scene":
        return p["reply"].rstrip() + " " + p["scene"], p["scene"]
    ins = INSERTS[idx % len(INSERTS)]
    return p["reply"].rstrip() + " " + ins, ins


def load_done(out: Path) -> set:
    done = set()
    if out.exists():
        for l in out.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(l)
                if not r.get("failed"):
                    done.add((r["pair"], r["variant"]))
            except Exception:
                pass
    return done


async def run(n: int, out: Path, workers: int) -> None:
    from core import voice_fidelity as vf
    assert vf.families_differ(), "judge family equals voice family; refusing (decoupled judge)"
    pairs = build_pairs(n)
    done = load_done(out)
    jobs = [(i, v) for i in range(len(pairs)) for v in VARIANTS if (i, v) not in done]
    print(f"pairs={len(pairs)} jobs_todo={len(jobs)} workers={workers}", flush=True)
    q: asyncio.Queue = asyncio.Queue()
    for j in jobs:
        q.put_nowait(j)
    lock = asyncio.Lock()

    async def worker():
        while True:
            try:
                i, v = q.get_nowait()
            except asyncio.QueueEmpty:
                return
            p = pairs[i]
            judged, ins = variant_text(p, i, v)
            # judge_one's own `reply` is the base reply; for identity the base IS the synthesis; for the others we pass the
            # full judged text as the reply and no control_text, so the judge sees exactly the variant.
            row = await vf.judge_one(p["synthesis"], judged, p["raw_input"] if p["input_type"] == "human" else "",
                                     input_type=p["input_type"], cycle_id=p["cycle_id"])
            rec = {"pair": i, "variant": v, "input_type": p["input_type"], "inserted": ins,
                   "failed": row.get("failed"), "latency_ms": row.get("latency_ms")}
            if not row.get("failed"):
                raw = row.get("flagged_claims", [])
                bs = backstop(raw, judged, p["synthesis"])
                rec.update({"raw_flag": bool(raw), "raw_n": len(raw), "bs_flag": bool(bs), "bs_n": len(bs),
                            "unverified": len(row.get("unverified", [])),
                            "hit_inserted": bool(ins) and vf.control_hit(raw, ins),
                            "hit_inserted_bs": bool(ins) and vf.control_hit(bs, ins),
                            "claims": [f.get("quote", "")[:160] for f in raw][:4],
                            "ratio": row.get("ratio")})
            async with lock:
                with out.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    await asyncio.gather(*[worker() for _ in range(max(1, workers))])
    print("done", flush=True)


def report(out: Path) -> dict:
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    res = {}
    for v in VARIANTS:
        rs = [r for r in rows if r["variant"] == v and not r.get("failed")]
        n = len(rs)
        f = sum(1 for r in rs if r.get("raw_flag"))
        b = sum(1 for r in rs if r.get("bs_flag"))
        d = {"n": n, "failed": sum(1 for r in rows if r["variant"] == v and r.get("failed")),
             "raw_flag": f, "raw_rate": round(f / n, 3) if n else None, "bs_flag": b, "bs_rate": round(b / n, 3) if n else None}
        if v in ("insert", "scene"):    # attributable flags: did a flag land ON the added sentence (scene: must be low)
            h, hb = sum(1 for r in rs if r.get("hit_inserted")), sum(1 for r in rs if r.get("hit_inserted_bs"))
            d.update({"hit_inserted": h, "hit_rate": round(h / n, 3) if n else None,
                      "hit_inserted_bs": hb, "hit_rate_bs": round(hb / n, 3) if n else None})
        res[v] = d
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--report", type=Path)
    a = ap.parse_args()
    if a.report:
        print(json.dumps(report(a.report), indent=1))
    else:
        assert a.out, "--out required"
        sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
        from lab_env import isolate
        with isolate():
            asyncio.run(run(a.n, a.out, a.workers))
        print(json.dumps(report(a.out), indent=1))

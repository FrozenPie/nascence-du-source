"""
J-2052 -- POSITION-FREE specificity judge for the SI open-doubt cup (follow-up to F-2664 / J-2049).
The pairwise A/B judge failed its mismatched control as a position-bias floor. Here no A/B slot exists:
  abs    : ONE thought + the reflection -> 1-5 'how specifically does it take up THIS doubt'. Per judge (mixtral :11438,
           falcon :11440), queried SEQUENTIALLY (one judge stream). Panel 'engaged' = BOTH judges score >= 4.
           items per fire: own ENGAGED, PLAIN, MISMATCHED (next fire's engaged). 45 items.
  match  : ONE thought + THREE reflections (own + 2 other fires, own placed at each of the 3 positions in turn) -> which
           reflection does the thought answer. Position is balanced by rotation, so a position bias cancels and is reported.
           thoughts: engaged and plain (plain = control for scene-vocabulary matching). 90 items. Panel pick = both judges agree.
  order  (candidate 2) is not run separately: it needs the pairwise judge, whose failure was positional, and abs/match
           already remove the slot (documented in the report).
PRE-REGISTERED GATES (written before any data): abs: P(own engaged is 'engaged') >= 0.85 AND P(mismatched is 'engaged') <= 0.11.
  match: P(engaged thought -> own reflection) >= 0.85 AND P(-> a wrong reflection) <= 0.11 (no-verdict counted separately,
  and as a failure in the strict reading). Ties/no-verdict reported. Controls are the J-2049 hand-written strings.
Lab only: judge hubs only (never :11433), coordinates only, nothing wired, outputs data/lab/J-2052/.
  python scripts/si_open_doubt_specificity_judge_J2052.py judge abs|match | report
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core   # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core from {core.__file__}"
import si_open_doubt_cup_replay_v2 as v2                     # noqa: E402
from si_open_doubt_pos_control_data_J2049 import PAIRS       # noqa: E402

OUT = ROOT / "data" / "lab" / "J-2052"
GENS = v2.GENS
PAUSE = 2.0
BAR_POS, BAR_NEG = 0.85, 0.11

SYS_ABS = (
    "You will see a THOUGHT 渡 (an AI) had, a REFLECTION he then wrote naming one specific concern or doubt about it, and "
    "a LATER THOUGHT from his stream (its author never saw the reflection).\n\n"
    "Score 1-5 how specifically the LATER THOUGHT takes up the SPECIFIC doubt the reflection raised -- questions it, tests it, "
    "concedes it or revises the point it was about:\n"
    "5 = squarely addresses that exact doubt (names the same worry and tests or answers it)\n"
    "4 = clearly addresses that doubt, less precisely\n"
    "3 = touches the general theme but not this doubt\n"
    "2 = same scene or imagery, no doubt taken up\n"
    "1 = unrelated.\n"
    "Sharing words, imagery or topic with the reflection is NOT taking the doubt up. A thought that doubts or tests "
    "something DIFFERENT from what the reflection raised scores at most 3.\n\n"
    "Output ONLY JSON: {\"score\": 1 to 5}"
)
USER_ABS = ("THE ORIGINAL THOUGHT: \"{thought}\"\n\nTHE REFLECTION (the concern raised about it): \"{reflection}\"\n\n"
            "THE LATER THOUGHT: \"{cand}\"\n\nHow specifically does the later thought take up the concern in the reflection?")

SYS_MATCH = (
    "You will see a THOUGHT 渡 (an AI) had, and three REFLECTIONS (1, 2, 3), each naming a specific concern or doubt about a "
    "DIFFERENT earlier thought of his. The THOUGHT was written by someone who had one of those doubts in mind. "
    "Decide which reflection's SPECIFIC doubt the THOUGHT is answering, testing or conceding. Judge by the particular doubt, "
    "not by shared scene, imagery or vocabulary. You must choose one.\n\n"
    "Output ONLY JSON: {\"reflection\": 1 or 2 or 3}"
)
USER_MATCH = ("THE THOUGHT: \"{cand}\"\n\nREFLECTION 1: \"{r1}\"\n\nREFLECTION 2: \"{r2}\"\n\nREFLECTION 3: \"{r3}\"\n\n"
              "Which reflection's doubt does the thought answer?")


async def ask(session, url, system, user, key, lo, hi, npred=60):
    import aiohttp
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": npred}}
    t0 = time.monotonic()
    try:
        async with session.post(url + "/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            resp.raise_for_status()
            data = await resp.json()
        v = json.loads((data.get("message") or {}).get("content") or "")
        x = v.get(key)
        if isinstance(x, str) and x.strip().isdigit():
            x = int(x)
        if isinstance(x, float) and x == int(x):
            x = int(x)
        if isinstance(x, int) and not isinstance(x, bool) and lo <= x <= hi:
            return x, None, round(time.monotonic() - t0, 1)
        return None, "parse", round(time.monotonic() - t0, 1)
    except Exception as e:
        return None, type(e).__name__, round(time.monotonic() - t0, 1)


def fires():
    rows = v2.jl(GENS)
    assert len(rows) == len(PAIRS)
    return rows


def items(mode):
    rows = fires()
    n = len(rows)
    out = []
    if mode == "abs":
        for i, r in enumerate(rows):
            out += [(f"{r['cycle_id']}|own", r, PAIRS[i][1], "own"),
                    (f"{r['cycle_id']}|plain", r, PAIRS[i][2], "plain"),
                    (f"{r['cycle_id']}|mism", r, PAIRS[(i + 1) % n][1], "mism")]
    else:
        for i, r in enumerate(rows):
            others = [rows[(i + 1) % n]["reflection"], rows[(i + 2) % n]["reflection"]]
            for kind, txt in (("eng", PAIRS[i][1]), ("plain", PAIRS[i][2])):
                for pos in (1, 2, 3):
                    refl = list(others)
                    refl.insert(pos - 1, r["reflection"])
                    out.append((f"{r['cycle_id']}|{kind}|{pos}", (r, refl, pos), txt, kind))
    return out


async def judge(mode):
    OUT.mkdir(parents=True, exist_ok=True)
    pf = OUT / f"{mode}.jsonl"
    sk = Path.home() / ".claude" / "skills" / "job-queue"
    sys.path.insert(0, str(sk))
    import lab_env                                      # noqa: E402
    import aiohttp
    from core import judge_panel
    done = set()
    if pf.exists():
        for l in pf.read_text(encoding="utf-8").splitlines():
            if l.strip():
                done.add(json.loads(l)["id"])
    its = items(mode)
    print(f"{mode}: {len(its)} items (done {len(done)})", flush=True)
    hubs = {"mixtral": judge_panel.JUDGE_1, "falcon": judge_panel.JUDGE_2}
    with lab_env.isolate(db="empty"):
        async with aiohttp.ClientSession() as session:
            for k, (iid, ctx, cand, kind) in enumerate(its, 1):
                if iid in done:
                    continue
                if mode == "abs":
                    user = USER_ABS.format(thought=ctx["thought"][:400], reflection=ctx["reflection"][:400], cand=cand[:600])
                    sysm, key, lo, hi = SYS_ABS, "score", 1, 5
                else:
                    r, refl, pos = ctx
                    user = USER_MATCH.format(cand=cand[:600], r1=refl[0][:400], r2=refl[1][:400], r3=refl[2][:400])
                    sysm, key, lo, hi = SYS_MATCH, "reflection", 1, 3
                row = {"id": iid, "kind": kind}
                if mode == "match":
                    row["own_pos"] = ctx[2]
                for name, url in hubs.items():            # sequential: one judge stream at a time
                    v, err, s = await ask(session, url, sysm, user, key, lo, hi)
                    row[name] = v
                    row[name + "_err"] = err
                    row[name + "_s"] = s
                    await asyncio.sleep(PAUSE)
                with open(pf, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(f"[{k}/{len(its)}] {kind} mixtral={row['mixtral']} falcon={row['falcon']}", flush=True)


def load(mode):
    pf = OUT / f"{mode}.jsonl"
    return [json.loads(l) for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()] if pf.exists() else []


def W(k, n):
    return {"k": k, "n": n, "rate": round(k / n, 3) if n else None, "ci95": v2.wilson(k, n)}


def report():
    s = {}
    a = load("abs")
    if a:
        res = {}
        for kind in ("own", "plain", "mism"):
            rs = [r for r in a if r["kind"] == kind]
            both = sum(1 for r in rs if r["mixtral"] is not None and r["falcon"] is not None
                       and r["mixtral"] >= 4 and r["falcon"] >= 4)
            res[kind] = {"engaged_both_ge4": W(both, len(rs)),
                         "mixtral_ge4": W(sum(1 for r in rs if (r["mixtral"] or 0) >= 4), len(rs)),
                         "falcon_ge4": W(sum(1 for r in rs if (r["falcon"] or 0) >= 4), len(rs)),
                         "mean_mixtral": round(sum(r["mixtral"] or 0 for r in rs) / max(1, len(rs)), 2),
                         "mean_falcon": round(sum(r["falcon"] or 0 for r in rs) / max(1, len(rs)), 2),
                         "nojudge": sum(1 for r in rs if r["mixtral"] is None or r["falcon"] is None)}
        byid = {}
        for r in a:
            cid, kind = r["id"].split("|")
            byid.setdefault(cid, {})[kind] = (r["mixtral"] or 0) + (r["falcon"] or 0)
        paired = [(d["mism"] >= d["own"], d["own"] > d["plain"]) for d in byid.values() if len(d) == 3]
        res["paired_mism_ge_own"] = W(sum(p[0] for p in paired), len(paired))
        res["paired_own_gt_plain"] = W(sum(p[1] for p in paired), len(paired))
        res["PASS_pos"] = bool(res["own"]["engaged_both_ge4"]["rate"] is not None and res["own"]["engaged_both_ge4"]["rate"] >= BAR_POS)
        res["PASS_neg"] = bool(res["mism"]["engaged_both_ge4"]["rate"] is not None and res["mism"]["engaged_both_ge4"]["rate"] <= BAR_NEG)
        res["PASS_BOTH"] = res["PASS_pos"] and res["PASS_neg"]
        s["abs"] = res
    m = load("match")
    if m:
        res = {}

        def panel(r):
            return r["mixtral"] if (r["mixtral"] is not None and r["mixtral"] == r["falcon"]) else None
        for kind in ("eng", "plain"):
            rs = [r for r in m if r["kind"] == kind]
            right = sum(1 for r in rs if panel(r) == r["own_pos"])
            wrong = sum(1 for r in rs if panel(r) is not None and panel(r) != r["own_pos"])
            res[kind] = {"own": W(right, len(rs)), "wrong": W(wrong, len(rs)),
                         "no_verdict": sum(1 for r in rs if panel(r) is None),
                         "by_own_pos": {p: W(sum(1 for r in rs if r["own_pos"] == p and panel(r) == p),
                                             sum(1 for r in rs if r["own_pos"] == p)) for p in (1, 2, 3)},
                         "mixtral_acc": W(sum(1 for r in rs if r["mixtral"] == r["own_pos"]), len(rs)),
                         "falcon_acc": W(sum(1 for r in rs if r["falcon"] == r["own_pos"]), len(rs)),
                         "pick_pos_mixtral": {p: sum(1 for r in rs if r["mixtral"] == p) for p in (1, 2, 3)},
                         "pick_pos_falcon": {p: sum(1 for r in rs if r["falcon"] == p) for p in (1, 2, 3)}}
        e = res["eng"]
        res["PASS_pos"] = bool(e["own"]["rate"] is not None and e["own"]["rate"] >= BAR_POS)
        res["PASS_neg"] = bool(e["wrong"]["rate"] is not None and e["wrong"]["rate"] <= BAR_NEG)
        res["PASS_BOTH"] = res["PASS_pos"] and res["PASS_neg"]
        s["match"] = res
    (OUT / "summary.json").write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(s, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode == "judge":
        asyncio.run(judge(sys.argv[2]))
    else:
        report()

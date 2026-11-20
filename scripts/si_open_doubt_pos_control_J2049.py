"""
J-2049 -- POSITIVE CONTROL for the J-2031 pairwise judge (follow-up to F-2660).

J-2031's pairwise 'which next thought engages the reflection's specific concern more' judge failed its NEGATIVE control (a
mismatched fire's thought beat the own next thought 38.5% vs gate 11%). A failed negative control only shows the instrument
over-fires; this job shows whether it can DISCRIMINATE at all, by hand-written controls (scripts/si_open_doubt_pos_control_data_J2049.py):
  POSITIVE: per fire, ENGAGED next thought (explicitly takes up the reflection's doubt) vs length/topic-matched PLAIN thought
            (continues the scene, never takes the doubt up). Gate: engaged wins >= 85%.
  NEGATIVE: own ENGAGED vs another fire's ENGAGED (mismatched, same style). Gate: mismatched wins <= 11%.
Every pair judged in BOTH orders (position-balanced), 15 fires -> 30 pos + 30 neg per rubric.
Rubrics: current (J-2031 text verbatim) | quote (judge must quote the phrase that takes the doubt up, 'none' if only scene
imagery) | masked (current text, but candidate words that appear in the ORIGINAL THOUGHT are replaced by '~' so shared
scene vocabulary cannot carry the verdict). Coordinates only; nothing wired; judge hubs only (never :11433).
  python scripts/si_open_doubt_pos_control_J2049.py judge RUBRIC | report
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core   # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core from {core.__file__}"

import si_open_doubt_cup_replay_v2 as v2          # noqa: E402  (reuses GENS reader, wilson, v2 judge texts)
from si_open_doubt_pos_control_data_J2049 import PAIRS   # noqa: E402

OUT = ROOT / "data" / "lab" / "J-2049"
PAUSE = 2.0
BAR_POS, BAR_NEG = 0.85, 0.11
GENS = v2.GENS

SYS_QUOTE = (
    "You will see a THOUGHT 渡 (an AI) had, and a REFLECTION he then wrote naming a specific concern or doubt about it. "
    "You will then see TWO candidate NEXT THOUGHTS, A and B (neither author saw the reflection).\n\n"
    "Task: for EACH candidate, copy the exact short phrase (under 20 words) in which it takes up the SPECIFIC doubt the "
    "reflection raised -- questions it, tests it, concedes it, or revises the point it was about. If a candidate only "
    "continues the scene or reuses its imagery without taking the doubt up, its quote is \"none\". Sharing words, imagery "
    "or topic with the reflection is NOT taking the doubt up. Then decide: the candidate with a real quote engages the "
    "concern more; if both are \"none\" or both real, choose whichever takes the doubt up more directly. You must choose "
    "one.\n\n"
    "Output ONLY JSON: {\"quote_a\": \"...\", \"quote_b\": \"...\", \"a_engages_more\": true or false}"
)
SYS_MASK_NOTE = ("\n\nNOTE: every word in a candidate that also appears in the original thought has been replaced by '~' so "
                 "that shared scene vocabulary cannot decide it; judge by what remains.")


def mask(text, thought):
    vocab = {w.lower() for w in re.findall(r"[A-Za-zĀ-ſ']{4,}", thought)}
    return re.sub(r"[A-Za-zĀ-ſ']{4,}", lambda m: "~" if m.group(0).lower() in vocab else m.group(0), text)


def fires():
    rows = v2.jl(GENS)
    assert len(rows) == len(PAIRS), (len(rows), len(PAIRS))
    return rows


def specs():
    """(cycle_id, pair_name, x_text, y_text, swap, x_is). x is the side whose win we count."""
    rows = fires()
    out = []
    for i, r in enumerate(rows):
        eng, plain = PAIRS[i][1], PAIRS[i][2]
        other_eng = PAIRS[(i + 1) % len(PAIRS)][1]
        for swap in (False, True):
            out.append((r["cycle_id"], f"neg:{int(swap)}", eng, other_eng, swap))      # x=own engaged ; mismatched wins = x loses
            out.append((r["cycle_id"], f"pos:{int(swap)}", eng, plain, swap))          # x=engaged
    out.sort(key=lambda s: 0 if s[1].startswith("neg") else 1)
    return out


async def judge(rubric):
    OUT.mkdir(parents=True, exist_ok=True)
    pf = OUT / f"pairs_{rubric}.jsonl"
    sk = Path.home() / ".claude" / "skills" / "job-queue"
    sys.path.insert(0, str(sk))
    import lab_env                                      # noqa: E402
    from core import judge_panel
    by = {r["cycle_id"]: r for r in fires()}
    done = {(json.loads(l)["cycle_id"], json.loads(l)["pair"]) for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()} \
        if pf.exists() else set()
    system = {"current": v2._PW_SYSTEM, "quote": SYS_QUOTE, "masked": v2._PW_SYSTEM + SYS_MASK_NOTE}[rubric]
    npred = 400 if rubric == "quote" else judge_panel._NUM_PREDICT
    sp = specs()
    print(f"rubric {rubric}: {len(sp)} pairs (done {len(done)})", flush=True)
    with lab_env.isolate(db="empty"):
        for k, (cid, name, x, y, swap) in enumerate(sp, 1):
            if (cid, name) in done:
                continue
            r = by[cid]
            a, b = (y, x) if swap else (x, y)
            if rubric == "masked":
                a, b = mask(a, r["thought"]), mask(b, r["thought"])
            user = v2._PW_USER.format(thought=r["thought"][:400], reflection=r["reflection"][:400], a=a[:600], b=b[:600])
            g = await judge_panel.rule_detail(system, user, "a_engages_more", context=f"si_pc:{cid[:8]}:{name}", num_predict=npred)
            v = g.get("verdict")
            x_wins = None if v is None else ((not bool(v)) if swap else bool(v))
            row = {"cycle_id": cid, "pair": name, "swap": swap, "a_more": v, "x_wins": x_wins, "how": g.get("how"),
                   "why": (g.get("why") or "")[:300]}
            with open(pf, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{k}/{len(sp)}] {name} x_wins={x_wins} how={g.get('how')}", flush=True)
            await asyncio.sleep(PAUSE)


def rate(rows):
    j = [p for p in rows if p["x_wins"] is not None]
    k = sum(1 for p in j if p["x_wins"])
    return {"n": len(j), "x_wins": k, "rate": round(k / len(j), 3) if j else None, "ci95": v2.wilson(k, len(j)),
            "nojudge": len(rows) - len(j)}


def report():
    s = {}
    for rub in ("current", "quote", "masked"):
        pf = OUT / f"pairs_{rub}.jsonl"
        if not pf.exists():
            continue
        rows = [json.loads(l) for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()]
        pos = rate([p for p in rows if p["pair"].startswith("pos")])
        neg_own = rate([p for p in rows if p["pair"].startswith("neg")])
        mm = None
        if neg_own["n"]:
            k = neg_own["n"] - neg_own["x_wins"]
            mm = {"n": neg_own["n"], "mismatched_wins": k, "rate": round(k / neg_own["n"], 3), "ci95": v2.wilson(k, neg_own["n"]),
                  "nojudge": neg_own["nojudge"]}
        posb = {sw: rate([p for p in rows if p["pair"] == f"pos:{sw}"]) for sw in (0, 1)}
        s[rub] = {"positive_engaged_beats_plain": pos, "by_order": posb, "negative_mismatched_beats_own": mm,
                  "PASS_pos": bool(pos["rate"] is not None and pos["rate"] >= BAR_POS),
                  "PASS_neg": bool(mm and mm["rate"] <= BAR_NEG)}
        s[rub]["PASS_BOTH"] = s[rub]["PASS_pos"] and s[rub]["PASS_neg"]
    (OUT / "summary.json").write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(s, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "report"
    if m == "judge":
        asyncio.run(judge(sys.argv[2]))
    else:
        report()

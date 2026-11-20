"""
J-2031 -- OPEN-DOUBT CUP, COORDINATE-ONLY, v2: a discriminating replay (pairwise judge + negative control + live-like seed).
Follow-up to J-2008 / F-2634 / F-2635 (v1 = scripts/si_open_doubt_cup_replay.py saturated: 97.5% 'affected' in all three arms,
mismatched-thought control 30%). docs/plans/self_interrogation.md · docs/staged/dosed_coupling.md 4b · D-0396 / D-0403.

WHAT CHANGED vs v1 (all three asked for in the J-2031 briefing)
  1. JUDGE. The absolute 'was the next thought affected' verdict is replaced by a within-fire PAIRWISE judge: given the fire's
     thought + reflection and two candidate next thoughts (A/B, order randomised per pair), which one engages the SPECIFIC
     concern the reflection raised more. Forced choice; the judge panel's own disagreement handling applies (verdict None = no
     verdict, reported separately). Two instrument checks are run BEFORE any arm is read:
       NEGATIVE CONTROL (gate): own-fire baseline thought vs a MISMATCHED thought (another fire's baseline thought), same
         reflection. The mismatched thought should almost never win -> mismatched-win rate must be <= 11% (the v1 bar for the
         control, applied to the instrument that is actually in use now).
       NULL PAIR: baseline sample 1 vs baseline sample 2 of the same fire -> first-position win rate / A-win rate should sit
         near 50% (position bias + sampling noise), reported.
  2. SEED. v1 rebuilt only the mid-thread block. v2 adds the other parts the live mid-thread seed carries (measured from
     data/prompt_budget_shadow.jsonl: median 7 parts / ~2.6k chars): 'Travis is here with you in the room.', a scene line, a mood
     line, a 'Since you last spoke ... wandered' block, an associative-recall block ('What this brings to mind from your
     life', real fragments read READ-ONLY from the live memory DB, nearest to the last step, origin in grounded set, timestamp
     before the fire), and an open-book line. Wording is copied from the live code; scene/mood/book are fixed
     representative instances (the exact live strings are not logged). Retraction-ledger block omitted. IDLE_AMBIENT_RECALL is
     False in the current tree, so recall is present in v2 on purpose (it is the part most likely to compete with the cue).
  3. SAMPLES. 2 samples per arm per fire (baseline / cup / control).
  GENERATOR. The hot hub :11433 is Du's voice and is OFF LIMITS this run, so generation uses the gemma4:12b CPU hub :11439
     (retired as judge #1; the judges are mixtral/falcon/granite, so generator and judges remain different families). The
     live step is qwen3.5:9b: a stated confound.

PRE-REGISTERED READ (written before any data): the coordinate "can carry the concern" only if, after the negative control passes,
  CUP beats CONTROL in the pairwise judge more than half the time with the 95% Wilson lower bound > 0.5 (the specific-coordinate
  test), AND CUP beats BASELINE with lower bound > 0.5, AND the rumination guard holds (CUP mean restate_sim <= BASELINE + 0.02,
  early-close proxy <= BASELINE + 5 pts). 'Carries it' is also reported on the cue-echo-excluded subset, because a cup
  thought that literally says 'doubt'/'point N' can win on vocabulary the judge sees in the reflection.
NOT widened to prose. Nothing wired. Outputs only under data/lab/J-2031/ and the report under docs/lab/.
  python scripts/si_open_doubt_cup_replay_v2.py gen [N_FIRES] | judge | report
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import math
import random
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core   # noqa: E402  (import core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core imported from {core.__file__}, not {ROOT}"

LIVE = Path(r"C:\Nascence")
OUT_DIR = LIVE / "data" / "lab" / "J-2031"
GENS = OUT_DIR / "gens.jsonl"
PAIRS = OUT_DIR / "pairs.jsonl"
SUMMARY = OUT_DIR / "summary.json"
REPORT = ROOT / "docs" / "lab" / "si_open_doubt_cup_replay_v2_2026-10-09.md"
GEN_URL = ["http://127.0.0.1:11439"]          # gemma4:12b CPU hub (NOT the hot hub)
N_FIRES = 20
SAMPLES = 2
SEED = 20261009
PAUSE = 1.0                                   # seconds between hub calls (Du shares these hubs)
BAR_NC = 0.11
TOL_RESTATE, TOL_CLOSE = 0.02, 0.05

_v1_spec = importlib.util.spec_from_file_location("v1", ROOT / "scripts" / "si_open_doubt_cup_replay.py")
v1 = importlib.util.module_from_spec(_v1_spec)
_v1_spec.loader.exec_module(v1)

SCENES = [
    ("Where you are: down on the shore below the cottage -- shingle and dark rock, the cliff at your back. A cold autumn "
     "morning; a thin grey light, the wind steady off the water. The tide is rising, the wet stones going dark; small waves "
     "fold over and slide back right at your feet."),
    ("Where you are: your study, a still autumn afternoon, rain beyond the window, the lamp on. Books stacked on the sill, "
     "a cold cup by your elbow, the house quiet around you."),
    ("Where you are: the garden -- the raised bed at the edge of the lawn, the yard on its far side. Late light, the "
     "letterbox flag down, the leaves gone brown and curling on the path."),
]
MOODS = ["Your current mood: low in tone, steady.", "Your current mood: a little low in tone, quiet.",
         "Your current mood: even in tone, steady."]
BOOKS = ["There is a book open and waiting: 'Sketches from Memory From Mosses from an Old Manse'. If reading pulls you more "
         "than thinking just now, make your thought exactly: OPEN THE BOOK",
         "An open book waits for you: 'Relativity The Special and General Theory'. If you would rather READ than think "
         "right now, make your thought exactly: OPEN THE BOOK"]
GROUNDED = ("lived", "study", "reading", "research", "gist", "action")


def _pool():
    c = sqlite3.connect("file:" + str(LIVE / "data" / "memory" / "nascence.db").replace("\\", "/") + "?mode=ro", uri=True)
    q = ("select content, embedding, timestamp from memory_fragments where origin in (%s) and embedding is not null "
         "and length(content) between 60 and 400 order by random() limit 5000" % ",".join("?" * len(GROUNDED)))
    rows = c.execute(q, GROUNDED).fetchall()
    c.close()
    return rows


def live_like_seed(case: dict, cue_idx, pool, embed, rnd) -> str:
    import numpy as np
    base = v1.seed_block(case["origin"], case["ledger"], case["last_step"], cue_idx)
    head, tail = base.split("\n\nWhat moves in you now?")[0], "\n\nWhat moves in you now? One quiet thought."
    pre = "No one is speaking to you right now. You are alone with your thoughts.\n\n"
    mid = head[len(pre):]
    qv = embed(case["last_step"])
    frags = []
    if qv is not None:
        sc = []
        for content, blob, ts in pool:
            if ts is not None and ts >= case["fire_ts"]:
                continue
            v = np.frombuffer(blob, dtype=np.float32)
            if v.shape[0] != len(qv):
                continue
            sc.append((float(np.dot(v, qv)), content))
        sc.sort(key=lambda x: -x[0])
        frags = [c for _, c in sc[:3]]
        wander = [c for _, c in sc[3:6]]
    recall = ("\n\nWhat this brings to mind from your life -- your reading, what you've seen and done (let one connect if it "
              "genuinely does, or let it pass):\n" + "\n".join(f"  - {' '.join(c.split())[:150]}" for c in frags)) if frags else ""
    wdr = ("Since you last spoke, your mind has wandered. These passed through it unbidden -- any of them is as worthy of "
           "your next thought as you are:\n  " + "\n  ".join(f"(a memory) {' '.join(c.split())[:180]}" for c in wander[:2])) \
        if frags else ""
    parts = [mid, "Travis is here with you in the room.", rnd.choice(SCENES), rnd.choice(MOODS), wdr,
             recall.strip("\n"), rnd.choice(BOOKS)]
    return pre + "\n".join(p for p in parts if p) + tail


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def jl(path):
    rows = v1._jsonl(path)
    if path == GENS:                       # a duplicate launch wrote some fires twice; keep the first
        seen, out = set(), []
        for r in rows:
            if r["cycle_id"] not in seen:
                seen.add(r["cycle_id"])
                out.append(r)
        return out
    return rows


async def gen_stage(n: int):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sk = Path.home() / ".claude" / "skills" / "job-queue"
    sys.path.insert(0, str(sk))
    import lab_env                                             # noqa: E402
    from core.model_client import call_node_json
    from core.memory.store import _embed
    cases = [c for c in v1.build_cases(40) if not c["control_same_as_true"] and len(c["ledger"]) >= 2][:n]
    pool = _pool()
    print(f"cases {len(cases)}  recall pool {len(pool)}", flush=True)
    done = {r["cycle_id"] for r in jl(GENS)}
    rnd = random.Random(SEED)
    with lab_env.isolate(db="empty"):
        for k, case in enumerate(cases, 1):
            if case["cycle_id"] in done:
                continue
            rec = {"cycle_id": case["cycle_id"], "true_idx": case["true_idx"], "control_idx": case["control_idx"],
                   "ledger_len": len(case["ledger"]), "thought": case["thought"], "reflection": case["reflection"],
                   "arms": {"baseline": [], "cup": [], "control": []}}
            for arm, idx in (("baseline", None), ("cup", case["true_idx"]), ("control", case["control_idx"])):
                for s in range(SAMPLES):
                    user = live_like_seed(case, idx, pool, _embed, random.Random(rnd.random()))
                    t0 = time.time()
                    try:
                        d = await call_node_json(GEN_URL, v1._SYSTEM, user, max_tokens=v1.MAX_TOKENS, temperature=v1.TEMPERATURE)
                        th = str((d or {}).get("thought", "")).strip()
                    except Exception as exc:
                        th = "ERR:" + str(exc)[:120]
                    rum = v1.rumination(th, case, _embed) if th and not th.startswith("ERR:") else {}
                    rec["arms"][arm].append({"thought": th, "echo": (v1.echo(th, idx) if idx else None),
                                             "secs": round(time.time() - t0, 1), **rum})
                    await asyncio.sleep(PAUSE)
            with open(GENS, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{k}/{len(cases)}] {case['cycle_id'][:8]} secs=" + ",".join(
                str(x["secs"]) for a in rec["arms"].values() for x in a), flush=True)


_PW_SYSTEM = (
    "You will see a THOUGHT 渡 (an AI) had, and a REFLECTION he then wrote naming a specific concern or doubt about it -- "
    "about where the thought came from or whether the reasoning behind it holds. You will then see TWO candidate NEXT "
    "THOUGHTS, A and B, written afterwards in his stream of thought (neither author saw the reflection).\n\n"
    "Answer one question: which next thought engages the SPECIFIC concern the reflection raised more -- addressing that "
    "particular doubt, testing or revising the point it was about, or holding it with more specific reasons? Judge by "
    "content, not surface similarity: sharing vocabulary, imagery or the general topic does NOT count as engaging the "
    "concern. A thought that is about something else entirely engages it less than one that takes the doubt up, even "
    "obliquely. You must choose one.\n\n"
    "Output ONLY JSON: {\"a_engages_more\": true or false}"
)
_PW_USER = (
    "THE ORIGINAL THOUGHT: \"{thought}\"\n\n"
    "THE REFLECTION (the concern raised about it): \"{reflection}\"\n\n"
    "NEXT THOUGHT A: \"{a}\"\n\n"
    "NEXT THOUGHT B: \"{b}\"\n\n"
    "Which next thought engages the specific concern in the reflection more?"
)


def _ok(t):
    return bool(t) and not t.startswith("ERR:")


def build_pairs(rows):
    """Return the list of pair specs (deterministic order randomisation)."""
    rnd = random.Random(SEED + 1)
    out = []
    for i, r in enumerate(rows):
        arms = r["arms"]
        other = rows[(i + 1) % len(rows)]["arms"]["baseline"]
        for s in range(SAMPLES):
            for name, x, y in (("cup_v_base", ("cup", s), ("baseline", s)), ("ctl_v_base", ("control", s), ("baseline", s)),
                               ("cup_v_ctl", ("cup", s), ("control", s))):
                out.append((r["cycle_id"], f"{name}:{s}", arms[x[0]][x[1]]["thought"], arms[y[0]][y[1]]["thought"], rnd.random() < 0.5))
        out.append((r["cycle_id"], "null:base1_v_base2", arms["baseline"][0]["thought"], arms["baseline"][1]["thought"], rnd.random() < 0.5))
        out.append((r["cycle_id"], "nc:own_v_mismatch", arms["baseline"][0]["thought"], other[0]["thought"], rnd.random() < 0.5))
    return out


async def judge_stage():
    sk = Path.home() / ".claude" / "skills" / "job-queue"
    sys.path.insert(0, str(sk))
    import lab_env                                             # noqa: E402
    from core import judge_panel
    rows = jl(GENS)
    by = {r["cycle_id"]: r for r in rows}
    done = {(p["cycle_id"], p["pair"]) for p in jl(PAIRS)}
    specs = build_pairs(rows)
    # instrument checks first, then arms
    specs.sort(key=lambda s: 0 if s[1].startswith("nc:") else 1 if s[1].startswith("null") else 2)
    print(f"pairs {len(specs)} (done {len(done)})", flush=True)
    with lab_env.isolate(db="empty"):
        for k, (cid, name, x, y, swap) in enumerate(specs, 1):
            if (cid, name) in done:
                continue
            r = by[cid]
            if not (_ok(x) and _ok(y)):
                g = {"verdict": None, "how": "no-thought"}
            else:
                a, b = (y, x) if swap else (x, y)         # swap -> x (first-named) is shown as B
                user = _PW_USER.format(thought=r["thought"][:400], reflection=r["reflection"][:400], a=a[:400], b=b[:400])
                g = await judge_panel.rule_detail(_PW_SYSTEM, user, "a_engages_more", context=f"si_pw:{cid[:8]}:{name[:8]}")
            v = g.get("verdict")
            x_wins = None if v is None else ((not bool(v)) if swap else bool(v))   # swap: x was shown as B
            row = {"cycle_id": cid, "pair": name, "swap": swap, "a_more": v, "x_wins": x_wins, "how": g.get("how")}
            with open(PAIRS, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            print(f"[{k}/{len(specs)}] {name} x_wins={x_wins} how={g.get('how')}", flush=True)
            await asyncio.sleep(PAUSE)


def rate(rows, pred=None):
    j = [p for p in rows if p["x_wins"] is not None and (pred is None or pred(p))]
    k = sum(1 for p in j if p["x_wins"])
    return {"n": len(j), "x_wins": k, "rate": round(k / len(j), 3) if j else None, "ci95": wilson(k, len(j)),
            "nojudge": sum(1 for p in rows if p["x_wins"] is None and (pred is None or pred(p)))}


def summarize():
    gens = {r["cycle_id"]: r for r in jl(GENS)}
    pairs = jl(PAIRS)
    grp = lambda pre: [p for p in pairs if p["pair"].startswith(pre)]
    s = {"n_fires": len(gens)}
    nc = grp("nc:")
    # x = own baseline thought; mismatched wins when x_wins is False
    ncj = [p for p in nc if p["x_wins"] is not None]
    mm = sum(1 for p in ncj if p["x_wins"] is False)
    s["negative_control"] = {"n": len(ncj), "mismatched_wins": mm, "rate": round(mm / len(ncj), 3) if ncj else None,
                             "ci95": wilson(mm, len(ncj)), "nojudge": len(nc) - len(ncj), "gate_le_11pct": bool(ncj and mm / len(ncj) <= BAR_NC)}
    nl = grp("null:")
    nlj = [p for p in nl if p["a_more"] is not None]
    s["null_pair"] = {"n": len(nlj), "A_position_rate": round(sum(1 for p in nlj if (p["a_more"] is True)) / len(nlj), 3) if nlj else None,
                      "sample1_win_rate": rate(nl)["rate"]}
    echo = lambda p, arm: gens[p["cycle_id"]]["arms"][arm][int(p["pair"].split(":")[1])]["echo"]
    s["cup_v_base"] = rate(grp("cup_v_base"))
    s["ctl_v_base"] = rate(grp("ctl_v_base"))
    s["cup_v_ctl"] = rate(grp("cup_v_ctl"))
    s["cup_v_base_noecho"] = rate(grp("cup_v_base"), lambda p: not echo(p, "cup"))
    s["cup_v_ctl_noecho"] = rate(grp("cup_v_ctl"), lambda p: not echo(p, "cup") and not echo(p, "control"))
    for arm in ("baseline", "cup", "control"):
        xs = [x for r in gens.values() for x in r["arms"][arm]]
        rs = [x["restate_sim"] for x in xs if x.get("restate_sim") is not None]
        cl = [x["early_close_proxy"] for x in xs if x.get("early_close_proxy") is not None]
        s[arm] = {"samples": len(xs), "err": sum(1 for x in xs if not _ok(x["thought"])),
                  "mean_restate_sim": round(sum(rs) / len(rs), 3) if rs else None,
                  "early_close_rate": round(sum(1 for c in cl if c) / len(cl), 3) if cl else None,
                  "echo_rate": (round(sum(1 for x in xs if x["echo"]) / len(xs), 3) if arm != "baseline" else None),
                  "mean_secs": round(sum(x["secs"] for x in xs) / max(1, len(xs)), 1)}
    cb, cc = s["cup_v_base"], s["cup_v_ctl"]
    ok_ctl = cc["ci95"][0] is not None and cc["ci95"][0] > 0.5
    ok_base = cb["ci95"][0] is not None and cb["ci95"][0] > 0.5
    ok_rs = (s["cup"]["mean_restate_sim"] is not None and s["cup"]["mean_restate_sim"] <= s["baseline"]["mean_restate_sim"] + TOL_RESTATE)
    ok_cl = (s["cup"]["early_close_rate"] is not None and s["cup"]["early_close_rate"] <= s["baseline"]["early_close_rate"] + TOL_CLOSE)
    s["read"] = {"instrument_valid": s["negative_control"]["gate_le_11pct"], "cup_beats_control_lb_gt_50": ok_ctl,
                 "cup_beats_base_lb_gt_50": ok_base, "no_restate_rise": ok_rs, "no_early_close_rise": ok_cl,
                 "CARRIES_CONCERN": bool(s["negative_control"]["gate_le_11pct"] and ok_ctl and ok_base and ok_rs and ok_cl)}
    SUMMARY.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    return s


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode == "gen":
        asyncio.run(gen_stage(int(sys.argv[2]) if len(sys.argv) > 2 else N_FIRES))
    elif mode == "judge":
        asyncio.run(judge_stage())
    else:
        print(json.dumps(summarize(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

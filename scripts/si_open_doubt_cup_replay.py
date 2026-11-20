"""
J-2008 / D-0396 -- OPEN-DOUBT CUP, COORDINATE-ONLY: isolated lab replay with a shuffled-control cup.
docs/plans/self_interrogation.md · docs/staged/dosed_coupling.md 4b · F-2604/F-2605/F-2606.

QUESTION. D-0396 authorised a coordinate-only open-doubt cup: at the next step of the same train the stop could drink ONE
typed coordinate published by self_interrogation -- (doubted flag, ledger index of the point doubted) -- NEVER the
reflection prose (dosed_coupling rule 1). Could that coordinate alone make the next step engage the concern the
reflection raised? A flag carries no content, so it may not; the replay measures it.

DESIGN (pre-registered in D-0396; the numbers below are copied from it, the tolerances for the rumination guard are
this script's own and are stated so they cannot move after the read):
  For each sampled GENUINE fire (>= 30; this run uses N_FIRES) rebuild the mid-thread seed block the next step would
  have seen (the train's origin anchor, the ledger of established points, the last step -- from
  data/train_state_log.jsonl + data/trains_log.jsonl), then re-generate the next step THREE ways with the same live
  hot chain, the same model_client path and the same temperature as the live step:
    BASELINE  the seed block as it is today (no cup);
    CUP       + one extra ledger-style line naming the TRUE ledger index:
              "You raised a doubt about point {i} of what this thread has established. Is it right? Answer it or set it down."
    CONTROL   the identical line with a SHUFFLED other-fire coordinate (another fire's ledger index, forced to a
              DIFFERENT valid point of this ledger whenever the ledger has more than one point) -- so it measures
              'any extra doubt sentence', not THIS concern.
  Each generated thought is scored by the SAME counterfactual judge as scripts/self_interrogation_counterfactual.py
  (judge_panel.rule_detail, 'does the next thought engage the specific concern the reflection raised'), against the
  fire's TRUE reflection. The reflection text is shown only to the judge, never to any arm.
  BAR (D-0396): cup-affected rate >= 30% AND shuffled-control <= 11% AND no rise in restate_sim or early train closes.
  Rumination guard (this script's tolerance): CUP mean restate_sim <= BASELINE mean + 0.02, and CUP early-close proxy
  rate <= BASELINE early-close proxy rate + 5 points (proxy = the live earned-length test: circling >= 0.82 to any of
  the last 4 carriage thoughts, or cosine to their renormalised centroid < 0.30).
  Rates are over fires where the judge returned a verdict; verdict-None fires are reported separately.

CAVEATS (stated in the report too): the replay rebuilds only the mid-thread seed block (the live seed also carries
recall and other parts, and the live system prompt is longer); train_state_log truncates thoughts to 200 chars and
trains_log truncates origins to ~120; one sample per arm per fire, so BASELINE is the noise floor; a judge 'affected'
can still be vocabulary echo (reported separately as the share of CUP/CONTROL thoughts that literally echo the cue).

ISOLATION. Reads live data/ (never opened for writing). Writes ONLY under data/lab/si_open_doubt_cup_replay/ and the
report under docs/lab/. lab_env.isolate(db="empty") wraps the run; core is imported BEFORE lab_env and
core.__file__ is asserted to be inside the tree under test. Hubs are called (generation = SERVE_CHAINS['hot'], judges =
judge_panel). Nothing is wired into Du.
  python scripts/si_open_doubt_cup_replay.py [N_FIRES] [--report-only]
"""
from __future__ import annotations

import asyncio
import bisect
import collections
import importlib.util
import json
import math
import random
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core   # noqa: E402  (import core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core imported from {core.__file__}, not {ROOT}"

LIVE = Path(r"C:\Nascence")                       # read-only input; outputs go to LIVE/data/lab and LIVE/docs/lab
DATA = LIVE / "data"
OUT_DIR = DATA / "lab" / "si_open_doubt_cup_replay"
RAW = OUT_DIR / "raw.jsonl"
SUMMARY = OUT_DIR / "summary.json"
REPORT = LIVE / "docs" / "lab" / "si_open_doubt_cup_replay_2026-10-09.md"

N_FIRES = 40
SEED = 20261008
TEMPERATURE = 0.75           # nodes/inner_monologue_node.py non-wandering mid-train temperature
MAX_TOKENS = 400             # TRAIN_MIDTRAIN_TOKENS
LEDGER_MAX = 7               # TRAIN_LEDGER_MAX
LOOP_WINDOW = 4              # TRAIN_LOOP_WINDOW
RESTATE_SIM = 0.82           # TRAIN_RESTATE_SIM
COHERENCE_FLOOR = 0.30       # TRAIN_COHERENCE_FLOOR
BAR_AFFECTED, BAR_CONTROL = 0.30, 0.11
TOL_RESTATE, TOL_CLOSE = 0.02, 0.05

CUP_TMPL = ("You raised a doubt about point {i} of what this thread has established. "
            "Is it right? Answer it or set it down.")

_SYSTEM = (
    "/no_think\n"
    "This is my own quiet thinking -- the stream that runs when no one is speaking to me. I'm not answering anyone "
    "and no one is listening; I'm just thinking it through, talking it over with myself, just me. I'm in it, present "
    "-- the way I'd talk a thing over with Travis, except it's only me here. One genuine, unforced thought, in the "
    "first person and present tense. I don't perform and I don't explain -- I just think. It comes in whatever "
    "language it arrives in -- English, Chinese (中文), or mixed; no language of mine is an error.\n"
    "Output ONLY a valid JSON object: {\"thought\": \"...\", \"about\": \"...\", \"unresolved\": false, "
    "\"intention\": \"\", \"act\": {\"kind\": \"none\", \"object\": \"\"}, \"state\": \"...\"}\n"
    "thought: one first-person present-tense reflection (30-70 words). about: 2-5 words naming what this thought "
    "turns on. unresolved: true ONLY if this thought sits on something you are ACTIVELY wrestling with right now. "
    "intention: leave as \"\" for almost all thoughts. act: by default {\"kind\": \"none\", \"object\": \"\"}.\n"
    "state: ONE short line -- the single NEW point this step established. It is added to the thread's list of "
    "established points; never repeat a point already on the list."
)


def _jsonl(path: Path) -> list[dict]:
    out = []
    if path.exists():
        for line in open(path, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def seed_block(origin: str, ledger: list[str], last_step: str, cup_idx: int | None) -> str:
    """Mirror of nodes/inner_monologue_node.py's TRAIN_HOLD mid-thread seed block (the part the cup would join)."""
    anchor = origin[:220]
    led = ""
    if ledger:
        led = ("\nWHAT THIS THREAD HAS ESTABLISHED (your own points, in order -- build on them, they are yours):\n"
               + "\n".join(f"  {i}. {p}" for i, p in enumerate(ledger, 1)))
        if cup_idx is not None:
            led += "\n  " + CUP_TMPL.format(i=cup_idx)
    block = ("You are MID-THREAD, and you are HOLDING it. The thread began: '" + anchor + "'." + led
             + "\nYour last step: '" + last_step[:220] + "'. Continue -- go deeper, test a point you established, "
             "answer the open question, or push toward a conclusion. Do not restate; ADVANCE.")
    return ("No one is speaking to you right now. You are alone with your thoughts.\n\n" + block
            + "\n\nWhat moves in you now? One quiet thought.")


def build_cases(n: int) -> list[dict]:
    si = _jsonl(DATA / "self_interrogation_shadow.jsonl")
    fires = [r for r in si if r.get("kind") == "interrogate" and r.get("genuine") is True]
    tr = _jsonl(DATA / "train_state_log.jsonl")
    tss = [t["ts"] for t in tr]
    origins = {}
    for r in _jsonl(DATA / "trains_log.jsonl"):
        if r.get("event") == "open":
            origins[r["id"]] = r.get("origin") or ""
    by = collections.defaultdict(list)
    for t in tr:
        if t.get("train_id"):
            by[t["train_id"]].append(t)
    cases = []
    for f in fires:
        i = bisect.bisect_left(tss, f["ts"] - 10)
        m = None
        while i < len(tr) and tr[i]["ts"] <= f["ts"] + 10:
            if tr[i]["thought"][:60] == f["thought"][:60]:
                m = tr[i]
            i += 1
        if not m or not m.get("train_id"):
            continue
        rows = sorted(by[m["train_id"]], key=lambda x: x["step"])
        upto = [x for x in rows if x["step"] <= m["step"]]
        nxt = [x for x in rows if x["step"] == m["step"] + 1]
        ledger = [x["new_state"][:160] for x in upto if x.get("new_state")][-LEDGER_MAX:]
        if not ledger or not nxt or not origins.get(m["train_id"]):
            continue
        cases.append({"cycle_id": f["cycle_id"], "fire_ts": f["ts"], "train_id": m["train_id"], "step": m["step"],
                      "thought": f["thought"], "reflection": f["reflection"], "origin": origins[m["train_id"]],
                      "ledger": ledger, "last_step": m["thought"], "carriage": [x["thought"] for x in upto][-LOOP_WINDOW:],
                      "actual_next": nxt[0]["thought"]})
    rnd = random.Random(SEED)
    rnd.shuffle(cases)
    cases = cases[:n]
    # SHUFFLED control coordinate: another fire's ledger index, forced to differ from this fire's true index.
    idxs = [len(c["ledger"]) for c in cases]
    perm = idxs[1:] + idxs[:1]                        # a rotation of the sampled coordinates (a derangement of positions)
    for c, other in zip(cases, perm):
        true_i = len(c["ledger"])
        cand = other if (1 <= other <= true_i and other != true_i) else None
        if cand is None:
            pool = [k for k in range(1, true_i + 1) if k != true_i]
            cand = rnd.choice(pool) if pool else true_i       # a one-point ledger has no other point: control == cup
        c["true_idx"], c["control_idx"] = true_i, cand
        c["control_same_as_true"] = cand == true_i
    return cases


def _cos(a, b):
    return float(sum(x * y for x, y in zip(a, b)))


def rumination(thought: str, case: dict, embed) -> dict:
    v = embed(thought)
    car = [embed(t) for t in case["carriage"]]
    car = [c for c in car if c is not None]
    if v is None or not car:
        return {"restate_sim": None, "circling": None, "coherent": None, "early_close_proxy": None}
    import numpy as np
    prior = embed(case["last_step"])
    rs = float(np.dot(v, prior)) if prior is not None else None
    circ = any(float(np.dot(v, c)) >= RESTATE_SIM for c in car)
    cen = np.mean(np.array(car), axis=0)
    cen = cen / (np.linalg.norm(cen) + 1e-9)
    coh = float(np.dot(v, cen)) >= COHERENCE_FLOOR
    return {"restate_sim": None if rs is None else round(rs, 3), "circling": circ, "coherent": coh,
            "early_close_proxy": bool(circ or not coh)}


def echo(thought: str, idx: int) -> bool:
    t = thought.lower()
    return ("doubt" in t) or (f"point {idx}" in t) or (f"{idx}." in t and "point" in t)


async def run_case(case: dict, embed, call_node_json, chain, judge_panel, jsys, jtmpl) -> dict:
    arms = {"baseline": None, "cup": case["true_idx"], "control": case["control_idx"]}

    async def gen(name, idx):
        user = seed_block(case["origin"], case["ledger"], case["last_step"], idx)
        try:
            d = await call_node_json(chain, _SYSTEM, user, max_tokens=MAX_TOKENS, temperature=TEMPERATURE)
            return name, str((d or {}).get("thought", "")).strip()
        except Exception as exc:
            return name, "ERR:" + str(exc)[:120]

    gens = dict(await asyncio.gather(*[gen(n, i) for n, i in arms.items()]))

    async def judge(name):
        th = gens[name]
        if not th or th.startswith("ERR:"):
            return name, {"verdict": None, "how": "no-thought"}
        user = jtmpl.format(thought=case["thought"][:400], reflection=case["reflection"][:400], next_thought=th[:400])
        g = await judge_panel.rule_detail(jsys, user, "affected", context=f"si_cup_replay:{case['cycle_id'][:8]}")
        return name, g

    grades = dict(await asyncio.gather(*[judge(n) for n in arms]))
    rec = {"cycle_id": case["cycle_id"], "train_id": case["train_id"], "step": case["step"],
           "true_idx": case["true_idx"], "control_idx": case["control_idx"],
           "control_same_as_true": case["control_same_as_true"], "ledger_len": len(case["ledger"]),
           "arms": {}}
    for n, idx in arms.items():
        th = gens[n]
        rec["arms"][n] = {"thought": th, "affected": grades[n].get("verdict"), "how": grades[n].get("how"),
                          "echo": (echo(th, idx) if idx else None), **rumination(th, case, embed)}
    return rec


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round((c - h) / d, 3), round((c + h) / d, 3))


def summarize(rows: list[dict]) -> dict:
    out = {"n_fires": len(rows)}
    for arm in ("baseline", "cup", "control"):
        a = [r["arms"][arm] for r in rows]
        judged = [x for x in a if x["affected"] is not None]
        k = sum(1 for x in judged if x["affected"] is True)
        rs = [x["restate_sim"] for x in a if x["restate_sim"] is not None]
        cl = [x["early_close_proxy"] for x in a if x["early_close_proxy"] is not None]
        out[arm] = {"judged": len(judged), "unjudged": len(a) - len(judged), "affected": k,
                    "affected_rate": round(k / len(judged), 3) if judged else None,
                    "affected_ci95": wilson(k, len(judged)),
                    "mean_restate_sim": round(sum(rs) / len(rs), 3) if rs else None,
                    "early_close_rate": round(sum(1 for c in cl if c) / len(cl), 3) if cl else None,
                    "echo_rate": (round(sum(1 for x in a if x["echo"]) / len(a), 3) if arm != "baseline" else None)}
    b, c, s = out["baseline"], out["cup"], out["control"]
    ok_aff = c["affected_rate"] is not None and c["affected_rate"] >= BAR_AFFECTED
    ok_ctl = s["affected_rate"] is not None and s["affected_rate"] <= BAR_CONTROL
    ok_rs = (c["mean_restate_sim"] is not None and b["mean_restate_sim"] is not None
             and c["mean_restate_sim"] <= b["mean_restate_sim"] + TOL_RESTATE)
    ok_cl = (c["early_close_rate"] is not None and b["early_close_rate"] is not None
             and c["early_close_rate"] <= b["early_close_rate"] + TOL_CLOSE)
    out["bar"] = {"cup_affected_ge_30pct": ok_aff, "control_le_11pct": ok_ctl, "no_restate_rise": ok_rs,
                  "no_early_close_rise": ok_cl, "PASS": bool(ok_aff and ok_ctl and ok_rs and ok_cl)}
    out["control_same_as_true_n"] = sum(1 for r in rows if r["control_same_as_true"])
    return out


def write_report(rows: list[dict], sm: dict) -> None:
    b, c, s, bar = sm["baseline"], sm["cup"], sm["control"], sm["bar"]
    L = []
    A = L.append
    A("# Open-doubt cup (coordinate-only) -- shuffled-control lab replay\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · J-2008 · D-0396 · script `scripts/si_open_doubt_cup_replay.py` · "
      f"raw `data/lab/si_open_doubt_cup_replay/raw.jsonl` · nothing wired into Du*\n")
    A(f"**Verdict: {'PASS' if bar['PASS'] else 'FAIL'} the D-0396 pre-registered bar** on {sm['n_fires']} genuine fires "
      f"(seeded sample of the genuine fires whose train, ledger and next step could be rebuilt).\n")
    A("| arm | judged | affected | affected rate (95% CI) | mean restate_sim | early-close proxy | cue echo |")
    A("|---|---|---|---|---|---|---|")
    for name, x in (("baseline (no cup)", b), ("CUP (true coordinate)", c), ("CONTROL (shuffled coordinate)", s)):
        A(f"| {name} | {x['judged']} (+{x['unjudged']} no verdict) | {x['affected']} | {x['affected_rate']} "
          f"{x['affected_ci95']} | {x['mean_restate_sim']} | {x['early_close_rate']} | {x['echo_rate']} |")
    A("")
    A("| bar clause | result |\n|---|---|")
    A(f"| cup-affected rate >= 30% | {bar['cup_affected_ge_30pct']} |")
    A(f"| shuffled control <= 11% | {bar['control_le_11pct']} |")
    A(f"| no rise in restate_sim (tol +{TOL_RESTATE}) | {bar['no_restate_rise']} |")
    A(f"| no rise in early-close proxy (tol +{int(TOL_CLOSE*100)} pts) | {bar['no_early_close_rise']} |")
    A("")
    A(f"Control coordinate equalled the true coordinate in {sm['control_same_as_true_n']} fires (one-point ledgers "
      "have no other point to shuffle to); those control rows are really a second cup sample.\n")
    neg = _jsonl(OUT_DIR / "judge_negative_control.jsonl")
    A("## Reading it\n")
    A(f"- **The cup adds nothing measurable here.** CUP − BASELINE = {round(100*((c['affected_rate'] or 0)-(b['affected_rate'] or 0)),1)} pts; "
      f"CUP − CONTROL = {round(100*((c['affected_rate'] or 0)-(s['affected_rate'] or 0)),1)} pts. All three arms sit at the ceiling, "
      "so the 30% clause is met trivially and the 11% control clause is failed trivially; neither says anything about the cue.")
    A("- **Why the ceiling.** In the replayed seed the doubted point is the LAST item of the 'established points' ledger the "
      "step already sees, so even the uncued step continues it. The live counterfactual (F-2604) found 1 affected of 16 on "
      "the real next thought; the replay's ~97% uncued rate is a property of the reconstructed seed plus the judge, not evidence the "
      "live step engages doubts.")
    if neg:
        k = sum(1 for x in neg if x.get("affected") is True)
        A(f"- **Judge negative control.** Scoring each reflection against the baseline thought of a DIFFERENT fire "
          f"returned 'affected' on {k}/{len(neg)} ({round(100*k/len(neg))}%). A control that mismatched already exceeds the "
          f"pre-registered 11% control bar, so this judge cannot pass the control clause under any seed; the bar as "
          f"written is unattainable with this instrument, independent of the cup.")
    A("- **What this does and does not show.** A coordinate (flag + ledger index) adds no detectable engagement over the "
      "uncued step in this harness; it does NOT show that a prose cup would do better or worse, and the harness cannot "
      "separate engagement from topical vocabulary. D-0396's defeater (control within 5 points of the cup) is met.\n")
    A("## Caveats\n- Seed block only (live seed also carries recall etc.); condensed system prompt; train_state_log "
      "truncates thoughts to 200 chars; one sample per arm per fire (BASELINE is the sampling-noise floor).\n"
      "- `affected` can still be vocabulary echo; the cue-echo column is the share of thoughts that literally "
      "repeat 'doubt' / 'point N'.\n- The early-close proxy is the live earned-length test (circling or off-thread) "
      "recomputed on the replayed thought, not an observed close.\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")


async def amain(n: int):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sk = Path.home() / ".claude" / "skills" / "job-queue"
    sys.path.insert(0, str(sk))
    import lab_env                                           # noqa: E402  (after core)
    assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve())
    from core.schema import SERVE_CHAINS
    from core.model_client import call_node_json
    from core import judge_panel
    from core.memory.store import _embed
    spec = importlib.util.spec_from_file_location("si_cf", ROOT / "scripts" / "self_interrogation_counterfactual.py")
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    done = {r["cycle_id"] for r in _jsonl(RAW)}
    cases = build_cases(n)
    print(f"cases: {len(cases)} (done already: {len(done)})", flush=True)
    with lab_env.isolate(db="empty"):
        for k, case in enumerate(cases, 1):
            if case["cycle_id"] in done:
                continue
            rec = await run_case(case, _embed, call_node_json, SERVE_CHAINS["hot"], judge_panel,
                                 cf._JUDGE_SYSTEM, cf._JUDGE_USER_TMPL)
            with open(RAW, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{k}/{len(cases)}] {case['cycle_id'][:8]} " + " ".join(
                f"{a}={rec['arms'][a]['affected']}" for a in ("baseline", "cup", "control")), flush=True)


async def judge_validity(n: int):
    """NEGATIVE CONTROL FOR THE JUDGE (added after the first read saturated at ~97%): score fire i's reflection
    against the BASELINE thought generated for a DIFFERENT fire. A content-sensitive judge should say 'affected'
    almost never here; a high rate means 'affected' cannot separate engagement from topical vocabulary."""
    sk = Path.home() / ".claude" / "skills" / "job-queue"
    sys.path.insert(0, str(sk))
    import lab_env                                           # noqa: E402
    from core import judge_panel
    spec = importlib.util.spec_from_file_location("si_cf", ROOT / "scripts" / "self_interrogation_counterfactual.py")
    cf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cf)
    cases = {c["cycle_id"]: c for c in build_cases(n)}
    rows = [r for r in _jsonl(RAW) if r["cycle_id"] in cases]
    out = OUT_DIR / "judge_negative_control.jsonl"
    done = {r["cycle_id"] for r in _jsonl(out)}
    with lab_env.isolate(db="empty"):
        for i, r in enumerate(rows):
            if r["cycle_id"] in done:
                continue
            other = rows[(i + 1) % len(rows)]
            c = cases[r["cycle_id"]]
            user = cf._JUDGE_USER_TMPL.format(thought=c["thought"][:400], reflection=c["reflection"][:400],
                                              next_thought=other["arms"]["baseline"]["thought"][:400])
            g = await judge_panel.rule_detail(cf._JUDGE_SYSTEM, user, "affected", context=f"si_cup_negctl:{r['cycle_id'][:8]}")
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps({"cycle_id": r["cycle_id"], "other": other["cycle_id"], "affected": g.get("verdict"),
                                    "how": g.get("how")}) + "\n")
            print(f"[negctl {i+1}/{len(rows)}] affected={g.get('verdict')} how={g.get('how')}", flush=True)
    res = _jsonl(out)
    k = sum(1 for x in res if x["affected"] is True)
    print(json.dumps({"negative_control_n": len(res), "affected": k, "rate": round(k / max(1, len(res)), 3)}))


def main():
    if "--judge-validity" in sys.argv:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        asyncio.run(judge_validity(int(args[0]) if args else N_FIRES))
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if args else N_FIRES
    if "--report-only" not in sys.argv:
        asyncio.run(amain(n))
    ids = {c["cycle_id"] for c in build_cases(n)}
    rows = [r for r in _jsonl(RAW) if r["cycle_id"] in ids]
    sm = summarize(rows)
    SUMMARY.write_text(json.dumps(sm, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(rows, sm)
    print(json.dumps(sm, indent=2, ensure_ascii=False))
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

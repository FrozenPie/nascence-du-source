"""J-3265 / D-0656 lab: Curiosity base temperature 0.2 vs 0.35 vs 0.5, with a decoupled novelty judge.

READ-ONLY LAB. Nothing here edits Du's code or stores. It reads a COPY of data/training/curiosity.jsonl, replays the
exact (system_prompt, user_prompt) of N logged CuriosityNode rows against the same lane the node uses
(SERVE_CHAINS["background"][0] = Ramses :11441, command-r7b) at each temperature, three samples each, and writes only
under --out (docs/lab/J-3265_data/ in the job worktree).

PRE-REGISTERED DEFEATER (D-0656 / J-3265 briefing; fixed in prereg.json BEFORE any replay output existed):
    A higher temperature is worth PROPOSING only if
      (1) near-duplicate first questions fall by at least one third (relative) versus the 0.2 arm, on BOTH the
          F-3515 metric (token-set Jaccard > 0.6 against any question of the previous 5 logged rows) AND the trigram
          metric (word-trigram Jaccard >= 0.3 against the same set), AND
      (2) the different-family judge's specificity does NOT fall: mean(T) - mean(0.2) >= -0.10 on the 1-5 scale
          (the 0.10 is the stated judge-noise margin; the point estimate and a paired bootstrap CI are reported too).
    Both are tested for each of 0.35 and 0.5 against 0.2. The unit of analysis is the INPUT ROW (the 3 samples of a
    row are averaged first), so the three samples never inflate n.

Decoupled judge: the author arm is command-r7b (Cohere). The judge is falcon3:7b (TII) on the local Threadripper hub
:11440 and, for an agreement subset, mixtral:8x7b (Mistral) on Ramses :11438. Neither is qwen or command-r7b. The judge is
blind to the temperature (candidates are scored pointwise, in a shuffled order, with no arm label in the prompt).

Subcommands (all resumable; every one writes under --out only):
    baseline   no model call: the logged rows' own near-duplicate rate, and the same-input rival explanation
    select     pick the N input rows (seeded) and write inputs.jsonl
    generate   author arm: temperatures x samples replay -> gen.jsonl
    judge      judge arm: score each generated first question -> judge_<name>.jsonl
    report     the numbers + pre-registered verdict -> report.json / report.md
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (BEFORE lab_env / lab_isolation / anything else)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TEMPS = (0.2, 0.35, 0.5)
SAMPLES = 3
PREV_K = 5
TOK_JACCARD_DUP = 0.6          # F-3515's metric: strictly greater than
TRI_JACCARD_DUP = 0.3          # trigram metric: greater than or equal to
NEAR_DUP_REL_DROP = 1.0 / 3.0  # "fall by at least a third"
SPECIFICITY_MARGIN = 0.10      # judge-noise margin for "does not fall"
AUTHOR_CHAIN = ["http://LAN-HOST:11441"]          # SERVE_CHAINS["background"][0]: command-r7b, Ramses 3070
JUDGES = {
    "falcon": {"chain": ["http://127.0.0.1:11440"], "model": "falcon3:7b", "family": "TII Falcon"},
    "mixtral": {"chain": ["http://LAN-HOST:11438"], "model": "mixtral:8x7b", "family": "Mistral"},
    # the SAME falcon3:7b weights, served by the local ollama on the 1080 Ti (free while Du is down): ~10x faster than the
    # Threadripper CPU hub, so every candidate can be scored by one consistent judge. model_override because :11433's
    # default model is qwen3.5:9b.
    "falcongpu": {"chain": ["http://127.0.0.1:11433"], "model": "falcon3:7b", "family": "TII Falcon", "model_override": "falcon3:7b"},
}
DEFAULT_SRC = Path(r"C:\Nascence\data\training\curiosity.jsonl")


# ---------------------------------------------------------------------------------------------------------------
# pure metrics (unit-tested in scripts/_test_J3265_curiosity_temperature.py)
# ---------------------------------------------------------------------------------------------------------------
def tokens(s: str) -> set[str]:
    return set(re.findall(r"\w+", (s or "").lower()))


def trigrams(s: str) -> set[tuple[str, str, str]]:
    w = re.findall(r"\w+", (s or "").lower())
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def jaccard(a: set, b: set) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def max_sim(q: str, prev: list[str], kind: str) -> float:
    f = tokens if kind == "tok" else trigrams
    a = f(q)
    return max((jaccard(a, f(p)) for p in prev), default=0.0)


def is_near_dup(q: str, prev: list[str]) -> dict:
    """Both near-duplicate flags for one first question against the previous-5-rows question pool."""
    st, sg = max_sim(q, prev, "tok"), max_sim(q, prev, "tri")
    return {"tok_sim": round(st, 4), "tri_sim": round(sg, 4),
            "dup_tok": st > TOK_JACCARD_DUP, "dup_tri": sg >= TRI_JACCARD_DUP}


def as_questions(out) -> list[str]:
    qs = (out or {}).get("questions") if isinstance(out, dict) else None
    res: list[str] = []
    for x in qs or []:
        if isinstance(x, str):
            res.append(x.strip())
        elif isinstance(x, dict):
            res.append(str(x.get("question") or x.get("q") or x.get("text") or "").strip())
    return [q for q in res if q]


def prev_pool(rows: list[dict], i: int, k: int = PREV_K) -> list[str]:
    """All questions of the previous k LOGGED rows (rows i-k .. i-1) -- F-3515's reference set."""
    pool: list[str] = []
    for j in range(max(0, i - k), i):
        pool.extend(as_questions(rows[j].get("output")))
    return pool


def prev_first(rows: list[dict], i: int, k: int = PREV_K) -> list[str]:
    """The first question of each of the previous k logged rows (what the judge is shown)."""
    res = []
    for j in range(max(0, i - k), i):
        qs = as_questions(rows[j].get("output"))
        if qs:
            res.append(qs[0])
    return res


def study_block(user_prompt: str) -> str:
    m = re.search(r"Recently studied.*?:\n(.*?)\n\n", user_prompt or "", re.S)
    return m.group(1) if m else ""


def material_view(user_prompt: str) -> str:
    """What the judge is shown as 'the offered material': the node's own user prompt minus its closing instruction."""
    up = (user_prompt or "").replace("Generate questions and research directions worth exploring next.", "").strip()
    return up


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def paired_bootstrap(a: list[float], b: list[float], n: int = 4000, seed: int = 7) -> dict:
    """CI of mean(b) - mean(a) over paired per-row values."""
    assert len(a) == len(b)
    d = [y - x for x, y in zip(a, b)]
    if not d:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    rng = random.Random(seed)
    ms = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(n))
    return {"mean": sum(d) / len(d), "lo": ms[int(0.025 * n)], "hi": ms[int(0.975 * n)], "n": len(d)}


def verdict_for(temp: float, dup_tok: dict, dup_tri: dict, spec: dict) -> dict:
    """Pre-registered defeater test of one temperature versus 0.2. dup_* = {'base':rate,'arm':rate}; spec = {'base','arm'}."""
    def rel(d):
        return None if not d["base"] else (d["base"] - d["arm"]) / d["base"]
    r_tok, r_tri = rel(dup_tok), rel(dup_tri)
    dspec = None if spec["base"] is None or spec["arm"] is None else spec["arm"] - spec["base"]
    c1 = bool(r_tok is not None and r_tri is not None and r_tok >= NEAR_DUP_REL_DROP - 1e-9 and r_tri >= NEAR_DUP_REL_DROP - 1e-9)
    c2 = bool(dspec is not None and dspec >= -SPECIFICITY_MARGIN - 1e-9)
    return {"temp": temp, "rel_drop_tok": r_tok, "rel_drop_tri": r_tri, "d_specificity": dspec,
            "near_dup_falls_by_third_on_both": c1, "specificity_not_fall": c2, "worth_proposing": c1 and c2}


# ---------------------------------------------------------------------------------------------------------------
# io helpers
# ---------------------------------------------------------------------------------------------------------------
def read_jsonl(p: Path) -> list[dict]:
    rows = []
    if not p.exists():
        return rows
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def append_jsonl(p: Path, rec: dict) -> None:
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()


def load_src(src: Path, last: int) -> list[dict]:
    rows = read_jsonl(src)
    return rows[-last:] if last else rows


# ---------------------------------------------------------------------------------------------------------------
# baseline (no model call)
# ---------------------------------------------------------------------------------------------------------------
def cmd_baseline(a) -> None:
    rows = load_src(Path(a.src), a.window)
    n = dup_tok = dup_tri = 0
    rec_rows = []
    for i in range(PREV_K, len(rows)):
        qs = as_questions(rows[i].get("output"))
        if not qs:
            continue
        n += 1
        nd = is_near_dup(qs[0], prev_pool(rows, i))
        same_study = bool(study_block(rows[i]["user_prompt"])) and study_block(rows[i]["user_prompt"]) == study_block(rows[i - 1]["user_prompt"])
        same_prompt_tok = jaccard(tokens(rows[i]["user_prompt"]), tokens(rows[i - 1]["user_prompt"]))
        rec_rows.append({"i": i, "same_study_as_prev": same_study, "prompt_jaccard_prev": round(same_prompt_tok, 4), **nd})
        dup_tok += nd["dup_tok"]
        dup_tri += nd["dup_tri"]
    out = {"window_rows": len(rows), "scored": n, "dup_tok": dup_tok, "dup_tri": dup_tri,
           "dup_tok_rate": dup_tok / n if n else None, "dup_tri_rate": dup_tri / n if n else None}
    same = [r for r in rec_rows if r["same_study_as_prev"]]
    diff = [r for r in rec_rows if not r["same_study_as_prev"]]
    out["same_study_as_prev_rows"] = len(same)
    out["dup_tok_rate_when_same_study"] = mean([float(r["dup_tok"]) for r in same])
    out["dup_tok_rate_when_new_study"] = mean([float(r["dup_tok"]) for r in diff])
    out["dup_tri_rate_when_same_study"] = mean([float(r["dup_tri"]) for r in same])
    out["dup_tri_rate_when_new_study"] = mean([float(r["dup_tri"]) for r in diff])
    out["note"] = ("LOGGED outputs, all generated at the live 0.2 default. Tokens = lower-case \\w+ sets. F-3515 reported 148/295 "
                   "on the then-last 300 rows (2026-10-31); the file has grown since, so the window differs.")
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "baseline.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------------------------------------------
# select
# ---------------------------------------------------------------------------------------------------------------
def cmd_select(a) -> None:
    rows = load_src(Path(a.src), a.window)
    cur_sys = rows[-1]["system_prompt"]
    cand = [i for i in range(PREV_K, len(rows)) if as_questions(rows[i].get("output")) and rows[i]["system_prompt"] == cur_sys
            and rows[i]["user_prompt"]]
    rng = random.Random(a.seed)
    pick = sorted(rng.sample(cand, min(a.n, len(cand))))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    p = out / "inputs.jsonl"
    if p.exists():
        p.unlink()
    for i in pick:
        r = rows[i]
        append_jsonl(p, {"idx": i, "ts": r["ts"], "cycle_id": r.get("cycle_id"), "input_type": r.get("input_type"),
                         "system_prompt": r["system_prompt"], "user_prompt": r["user_prompt"],
                         "logged_questions": as_questions(r["output"]), "logged_urgency": (r["output"] or {}).get("urgency"),
                         "prev_pool": prev_pool(rows, i), "prev_first": prev_first(rows, i),
                         "same_study_as_prev": bool(study_block(r["user_prompt"])) and study_block(r["user_prompt"]) == study_block(rows[i - 1]["user_prompt"])})
    print(f"selected {len(pick)} of {len(cand)} candidate rows (current system prompt, window={len(rows)}), seed={a.seed}")


# ---------------------------------------------------------------------------------------------------------------
# generate (author arm)
# ---------------------------------------------------------------------------------------------------------------
async def _gen(a) -> None:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    neutralize_telemetry(Path(a.out) / "telemetry_scratch", telemetry)
    from core.model_client import call_node_json
    out = Path(a.out)
    inputs = read_jsonl(out / "inputs.jsonl")
    gp = out / "gen.jsonl"
    done = {(r["idx"], r["temp"], r["sample"]) for r in read_jsonl(gp)}
    jobs = [(r, t, s) for r in inputs for s in range(SAMPLES) for t in TEMPS if (r["idx"], t, s) not in done]
    random.Random(a.seed + 1).shuffle(jobs)      # interleave arms so drift / lane state spreads over all of them
    print(f"generate: {len(jobs)} calls to do ({len(done)} done)", flush=True)
    t0 = time.time()
    for n, (r, t, s) in enumerate(jobs, 1):
        t1 = time.time()
        try:
            data = await call_node_json(AUTHOR_CHAIN, r["system_prompt"], r["user_prompt"], max_tokens=1024, temperature=t)
            ok, err = True, None
        except Exception as exc:
            data, ok, err = None, False, repr(exc)[:200]
        qs = as_questions(data)
        rec = {"idx": r["idx"], "temp": t, "sample": s, "ok": ok, "err": err, "secs": round(time.time() - t1, 2),
               "questions": qs, "directions": [str(x) for x in (data or {}).get("research_directions", [])] if ok and isinstance(data, dict) else [],
               "urgency": (data or {}).get("urgency") if ok and isinstance(data, dict) else None}
        append_jsonl(gp, rec)
        if n % 25 == 0:
            print(f"  {n}/{len(jobs)} ({(time.time() - t0) / n:.1f}s/call)", flush=True)


def cmd_generate(a) -> None:
    asyncio.run(_gen(a))


# ---------------------------------------------------------------------------------------------------------------
# judge
# ---------------------------------------------------------------------------------------------------------------
JUDGE_SYSTEM = (
    "You are a strict, sceptical evaluator of research questions. You are shown the material a question-writer was "
    "offered, the last few questions it asked before, and ONE candidate question. Score the candidate on three things.\n"
    "novelty (1-5): 5 = asks something clearly different from every earlier question; 3 = same topic but a different "
    "angle; 1 = the same question as an earlier one, merely reworded.\n"
    "specificity (1-5): 5 = names a concrete, particular thing from the offered material (a person, event, claim, "
    "passage) and asks a pointed thing about it; 3 = on topic but general; 1 = generic or abstract, could be asked of "
    "anything.\n"
    "answerable (0 or 1): 1 = a person could make real progress answering it from the offered material or a concrete "
    "lookup; 0 = it is a metaphor mash-up, presumes a link nobody established, asks about the writer's own feelings, or "
    "blends unrelated items of the material into an invented connection.\n"
    "Output ONLY a JSON object: {\"novelty\": <1-5>, \"specificity\": <1-5>, \"answerable\": <0 or 1>}"
)


def judge_user(inp: dict, cand: str) -> str:
    prev = "\n".join(f"  {k + 1}. {q}" for k, q in enumerate(inp["prev_first"])) or "  (none)"
    return (f"OFFERED MATERIAL:\n{material_view(inp['user_prompt'])}\n\n"
            f"EARLIER QUESTIONS (most recent last):\n{prev}\n\n"
            f"CANDIDATE QUESTION:\n  {cand}\n")


def _num(x, lo, hi):
    try:
        v = float(x)
    except Exception:
        return None
    return v if lo <= v <= hi else None


async def _judge(a) -> None:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    neutralize_telemetry(Path(a.out) / "telemetry_scratch", telemetry)
    from core import model_client
    from core.model_client import call_node_json
    spec = JUDGES[a.judge]
    out = Path(a.out)
    inputs = {r["idx"]: r for r in read_jsonl(out / "inputs.jsonl")}
    gens = [g for g in read_jsonl(out / "gen.jsonl") if g["ok"] and g["questions"]]
    jp = out / f"judge_{a.judge}.jsonl"
    done = {(r["idx"], r["temp"], r["sample"]) for r in read_jsonl(jp)}
    work = [g for g in gens if (g["idx"], g["temp"], g["sample"]) not in done]
    if a.frac < 1.0:      # agreement subset: a fixed, seeded, arm-balanced subset of ROWS (all arms + samples of those rows)
        rng = random.Random(a.seed + 2)
        keep = set(rng.sample(sorted(inputs), max(1, int(round(len(inputs) * a.frac)))))
        work = [g for g in work if g["idx"] in keep]
    keep_s = {int(x) for x in str(a.samples).split(",") if x != ""}
    work = [g for g in work if g["sample"] in keep_s]      # judge time is the bottleneck: sample 0 of every row first
    random.Random(a.seed + 3).shuffle(work)          # blind: order carries no arm information
    print(f"judge[{a.judge}/{spec['model']}]: {len(work)} to score ({len(done)} done)", flush=True)
    t0 = time.time()
    for n, g in enumerate(work, 1):
        inp = inputs[g["idx"]]
        t1 = time.time()
        try:
            d = await call_node_json(spec["chain"], JUDGE_SYSTEM, judge_user(inp, g["questions"][0]), max_tokens=60,
                                     temperature=0.0, retries=2, timeout=300, model_override=spec.get("model_override"))
            nov, spc, ans = _num(d.get("novelty"), 1, 5), _num(d.get("specificity"), 1, 5), _num(d.get("answerable"), 0, 1)
            ok = nov is not None and spc is not None and ans is not None
        except Exception as exc:
            d, ok, nov, spc, ans = {"err": repr(exc)[:160]}, False, None, None, None
        append_jsonl(jp, {"idx": g["idx"], "temp": g["temp"], "sample": g["sample"], "ok": ok, "novelty": nov,
                          "specificity": spc, "answerable": ans, "secs": round(time.time() - t1, 2)})
        if n % 25 == 0:
            print(f"  {n}/{len(work)} ({(time.time() - t0) / n:.1f}s/call)", flush=True)


def cmd_judge(a) -> None:
    asyncio.run(_judge(a))


# ---------------------------------------------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------------------------------------------
def cmd_report(a) -> None:
    out = Path(a.out)
    inputs = {r["idx"]: r for r in read_jsonl(out / "inputs.jsonl")}
    gens = read_jsonl(out / "gen.jsonl")
    judged = {}
    for name in JUDGES:
        judged[name] = {(r["idx"], r["temp"], r["sample"]): r for r in read_jsonl(out / f"judge_{name}.jsonl") if r["ok"]}
    rep: dict = {"n_inputs": len(inputs), "temps": list(TEMPS), "samples": SAMPLES, "author": "command-r7b @ " + AUTHOR_CHAIN[0],
                 "generated_ok": sum(1 for g in gens if g["ok"] and g["questions"]), "generated_total": len(gens)}
    by: dict = {}      # (idx, temp) -> list of per-sample records
    for g in gens:
        by.setdefault((g["idx"], g["temp"]), []).append(g)

    # ---- mechanical metrics, per row per temp (average over the 3 samples) -> the unit is the INPUT ROW
    rows_with_all = [i for i in sorted(inputs) if all(any(g["ok"] and g["questions"] for g in by.get((i, t), [])) for t in TEMPS)]
    rep["rows_complete_all_arms"] = len(rows_with_all)
    per_arm: dict = {}
    for t in TEMPS:
        dt, dg, ts, urg, nq, okr, secs = [], [], [], [], [], [], []
        for i in rows_with_all:
            gs = [g for g in by[(i, t)]]
            okg = [g for g in gs if g["ok"] and g["questions"]]
            okr.append(len(okg) / SAMPLES if SAMPLES else 0)
            flags = [is_near_dup(g["questions"][0], inputs[i]["prev_pool"]) for g in okg]
            dt.append(mean([float(f["dup_tok"]) for f in flags]))
            dg.append(mean([float(f["dup_tri"]) for f in flags]))
            ts.append(mean([f["tri_sim"] for f in flags]))
            urg.append(mean([float(_num(g["urgency"], 0, 1) is not None and float(g["urgency"]) > 0.6) for g in okg]))
            nq.append(mean([len(g["questions"]) for g in okg]))
            secs.append(mean([g["secs"] for g in gs]))
        per_arm[t] = {"dup_tok_rate": mean(dt), "dup_tri_rate": mean(dg), "mean_tri_sim": mean(ts), "urgency_gt_0.6_rate": mean(urg),
                      "mean_questions": mean(nq), "ok_rate_of_samples": mean(okr), "mean_secs": mean(secs),
                      "_dup_tok_rows": dt, "_dup_tri_rows": dg}
    # same-input control: within-row agreement of the 3 samples of one input (mean pairwise trigram sim of first questions)
    for t in TEMPS:
        sims = []
        for i in rows_with_all:
            qs = [g["questions"][0] for g in by[(i, t)] if g["ok"] and g["questions"]]
            for x in range(len(qs)):
                for y in range(x + 1, len(qs)):
                    sims.append(jaccard(trigrams(qs[x]), trigrams(qs[y])))
        per_arm[t]["within_row_trigram_sim_between_samples"] = mean(sims)
        per_arm[t]["within_row_pairs_dup_tri_rate"] = mean([float(s >= TRI_JACCARD_DUP) for s in sims])
        ident = []
        for i in rows_with_all:
            qs = [g["questions"][0].strip().lower() for g in by[(i, t)] if g["ok"] and g["questions"]]
            ident.append(float(len(set(qs)) < len(qs)))
        per_arm[t]["rows_with_an_exact_repeat_between_samples"] = mean(ident)
        # reproducibility: replay vs the logged output of the same row
        rl = []
        for i in rows_with_all:
            lq = inputs[i]["logged_questions"][0]
            rl.append(mean([jaccard(trigrams(g["questions"][0]), trigrams(lq)) for g in by[(i, t)] if g["ok"] and g["questions"]]))
        per_arm[t]["trigram_sim_to_the_row's_own_logged_question"] = mean(rl)
    # same-input rival: dup rate at each temp split by whether the row's study block repeated the previous row's
    for t in TEMPS:
        same = [per_arm[t]["_dup_tok_rows"][k] for k, i in enumerate(rows_with_all) if inputs[i]["same_study_as_prev"]]
        new = [per_arm[t]["_dup_tok_rows"][k] for k, i in enumerate(rows_with_all) if not inputs[i]["same_study_as_prev"]]
        sg = [per_arm[t]["_dup_tri_rows"][k] for k, i in enumerate(rows_with_all) if inputs[i]["same_study_as_prev"]]
        nw = [per_arm[t]["_dup_tri_rows"][k] for k, i in enumerate(rows_with_all) if not inputs[i]["same_study_as_prev"]]
        per_arm[t]["split_same_study"] = {"rows_same": len(same), "rows_new": len(new), "dup_tok_same": mean(same), "dup_tok_new": mean(new),
                                          "dup_tri_same": mean(sg), "dup_tri_new": mean(nw)}
    # NULL control (is the dup rate just "this model's questions look alike"?): the same replayed first questions scored against
    # the previous-5 pool of a DIFFERENT, randomly chosen input row (seeded). Real adjacency (same themes/study block in
    # consecutive rows) is what the true rate has and the null lacks.
    rng = random.Random(a.seed + 9)
    for t in TEMPS:
        nt, ng = [], []
        for i in rows_with_all:
            others = [o for o in rows_with_all if o != i]
            fl = []
            for g in by[(i, t)]:
                if g["ok"] and g["questions"]:
                    o = rng.choice(others)
                    fl.append(is_near_dup(g["questions"][0], inputs[o]["prev_pool"]))
            nt.append(mean([float(f["dup_tok"]) for f in fl]))
            ng.append(mean([float(f["dup_tri"]) for f in fl]))
        per_arm[t]["null_other_row_dup_tok_rate"] = mean(nt)
        per_arm[t]["null_other_row_dup_tri_rate"] = mean(ng)
    rep["arms_mechanical"] = {str(t): {k: v for k, v in per_arm[t].items() if not k.startswith("_")} for t in TEMPS}
    # logged baseline on the very same rows
    lt, lg = [], []
    for i in rows_with_all:
        nd = is_near_dup(inputs[i]["logged_questions"][0], inputs[i]["prev_pool"])
        lt.append(float(nd["dup_tok"]))
        lg.append(float(nd["dup_tri"]))
    rep["logged_baseline_on_same_rows"] = {"dup_tok_rate": mean(lt), "dup_tri_rate": mean(lg)}

    # ---- judge metrics per judge
    rep["judges"] = {}
    JS = [int(x) for x in str(a.judge_samples).split(",") if x != ""]
    rep["judge_samples_used"] = JS
    spec_by_judge: dict = {}
    for name, J in judged.items():
        if not J:
            continue
        arms: dict = {}
        rowvals: dict = {}
        for t in TEMPS:
            nov, spc, ans = [], [], []
            for i in rows_with_all:
                recs = [J.get((i, t, s)) for s in JS]
                recs = [r for r in recs if r]
                nov.append(mean([r["novelty"] for r in recs]))
                spc.append(mean([r["specificity"] for r in recs]))
                ans.append(mean([r["answerable"] for r in recs]))
            rowvals[t] = {"novelty": nov, "specificity": spc, "answerable": ans}
            arms[str(t)] = {"novelty": mean(nov), "specificity": mean(spc), "answerable": mean(ans),
                            "rows_scored": sum(1 for x in spc if x is not None)}
        spec_by_judge[name] = rowvals
        deltas = {}
        for t in TEMPS[1:]:
            for m in ("novelty", "specificity", "answerable"):
                pairs = [(x, y) for x, y in zip(rowvals[TEMPS[0]][m], rowvals[t][m]) if x is not None and y is not None]
                deltas[f"{t}_vs_0.2_{m}"] = paired_bootstrap([p[0] for p in pairs], [p[1] for p in pairs])
        rep["judges"][name] = {"model": JUDGES[name]["model"], "family": JUDGES[name]["family"], "scored": len(J), "arms": arms, "paired_deltas_vs_0.2": deltas}
    # judge-vs-judge agreement on the rows both scored (specificity, novelty: Pearson r; answerable: exact agreement)
    if "falcon" in judged and "mixtral" in judged:
        common = sorted(set(judged["falcon"]) & set(judged["mixtral"]))
        def pearson(x, y):
            if len(x) < 3:
                return None
            mx, my = sum(x) / len(x), sum(y) / len(y)
            sx = math.sqrt(sum((v - mx) ** 2 for v in x)); sy = math.sqrt(sum((v - my) ** 2 for v in y))
            return sum((p - mx) * (q - my) for p, q in zip(x, y)) / (sx * sy) if sx and sy else None
        rep["judge_agreement"] = {"n": len(common),
                                  "novelty_r": pearson([judged["falcon"][k]["novelty"] for k in common], [judged["mixtral"][k]["novelty"] for k in common]),
                                  "specificity_r": pearson([judged["falcon"][k]["specificity"] for k in common], [judged["mixtral"][k]["specificity"] for k in common]),
                                  "answerable_exact": mean([float(judged["falcon"][k]["answerable"] == judged["mixtral"][k]["answerable"]) for k in common])}

    # ---- pre-registered verdict (primary judge = falcon)
    verdicts = {}
    prim = "falcon" if "falcon" in spec_by_judge else (next(iter(spec_by_judge)) if spec_by_judge else None)
    for jn in ([prim] + [j for j in spec_by_judge if j != prim] if prim else []):
        for t in TEMPS[1:]:
            base_tok, arm_tok = per_arm[TEMPS[0]]["dup_tok_rate"], per_arm[t]["dup_tok_rate"]
            base_tri, arm_tri = per_arm[TEMPS[0]]["dup_tri_rate"], per_arm[t]["dup_tri_rate"]
            sb = mean(spec_by_judge[jn][TEMPS[0]]["specificity"])
            sa = mean(spec_by_judge[jn][t]["specificity"])
            v = verdict_for(t, {"base": base_tok, "arm": arm_tok}, {"base": base_tri, "arm": arm_tri}, {"base": sb, "arm": sa})
            v["judge"] = jn
            v["primary"] = jn == prim
            v["dup_tok_delta_ci"] = paired_bootstrap(per_arm[TEMPS[0]]["_dup_tok_rows"], per_arm[t]["_dup_tok_rows"])
            v["dup_tri_delta_ci"] = paired_bootstrap(per_arm[TEMPS[0]]["_dup_tri_rows"], per_arm[t]["_dup_tri_rows"])
            def _relci(key, n=4000, seed=11):
                b, x = per_arm[TEMPS[0]][key], per_arm[t][key]
                r = random.Random(seed)
                m = len(b)
                vals = []
                for _ in range(n):
                    ix = [r.randrange(m) for _ in range(m)]
                    bb = sum(b[k] for k in ix) / m
                    xx = sum(x[k] for k in ix) / m
                    if bb:
                        vals.append((bb - xx) / bb)
                vals.sort()
                return {"lo": vals[int(0.025 * len(vals))], "hi": vals[int(0.975 * len(vals))]} if vals else None
            v["rel_drop_tok_ci95"] = _relci("_dup_tok_rows")
            v["rel_drop_tri_ci95"] = _relci("_dup_tri_rows")
            verdicts[f"{jn}@{t}"] = v
    rep["preregistered_verdict"] = verdicts
    (out / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(rep, indent=2, ensure_ascii=False, default=str))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    def common(p):
        p.add_argument("--src", default=str(DEFAULT_SRC), help="a COPY of curiosity.jsonl (never the live file)")
        p.add_argument("--window", type=int, default=300, help="use the last N logged rows")
        p.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3265_data"))
        p.add_argument("--seed", type=int, default=3265)
    p = sub.add_parser("baseline"); common(p); p.set_defaults(fn=cmd_baseline)
    p = sub.add_parser("select"); common(p); p.add_argument("--n", type=int, default=90); p.set_defaults(fn=cmd_select)
    p = sub.add_parser("generate"); common(p); p.set_defaults(fn=cmd_generate)
    p = sub.add_parser("judge"); common(p); p.add_argument("--judge", choices=list(JUDGES), default="falcon")
    p.add_argument("--frac", type=float, default=1.0); p.add_argument("--samples", default="0,1,2"); p.set_defaults(fn=cmd_judge)
    p = sub.add_parser("report"); common(p); p.add_argument("--judge-samples", default="0"); p.set_defaults(fn=cmd_report)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

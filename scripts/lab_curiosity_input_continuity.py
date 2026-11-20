"""J-3421 lab: are Curiosity near-duplicates INPUT continuity?  Offline replay with the PROMPT altered in the lab only.

READ-ONLY LAB (no Du code or store edited). Replays the same 90 logged inputs as J-3265 (docs/lab/J-3265_data/inputs.jsonl)
against command-r7b on Ramses :11441 (the node's own background lane) at the live 0.2 temperature, 3 samples, with:
    control : the logged prompt unchanged
    A       : study block replaced by the newest OTHER logged study items whenever it equals the previous row's
    B1      : "Recent themes" block cut to its newest 1 line
    B3      : "Recent themes" block cut to its newest 3 lines
    C       : A + B1
Arms that leave a row's prompt byte-identical to control reuse that row's control samples (same prompt, same distribution).
Pre-registered bar (prereg.json, written before any replay): an arm is worth PROPOSING only if
  (1) near-duplicates fall by >= 1/3 relative to control on BOTH token-Jaccard>0.6 and trigram>=0.3 (vs the previous 5
      LOGGED rows' questions), AND (2) the mash-up proxy does not rise by more than 5 points (absolute), AND
  (3) judge specificity does not fall (mean(arm)-mean(control) >= -0.10).
Judge: falcon3:7b (TII), different family from command-r7b/qwen. Unit of analysis = input row (samples averaged).
Subcommands: prereg, build, generate, judge, report.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
import lab_curiosity_temperature as T  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ARMS = ("control", "A", "B1", "B3", "C")
SAMPLES = 3
TEMP = 0.2
MASH_RISE_MAX = 0.05
OUT_DEFAULT = ROOT / "docs" / "lab" / "J-3421_data"
INPUTS_SRC = ROOT / "docs" / "lab" / "J-3265_data" / "inputs.jsonl"
STOP = {"the", "a", "an", "of", "and", "in", "on", "to", "for", "with", "from", "by", "at", "is"}

STUDY_RE = re.compile(r"(Recently studied[^\n]*:\n)(.*?)(\n\n)", re.S)
THEME_RE = re.compile(r"(Recent themes:\n)(.*?)(\n\n)", re.S)


def study_items(block: str) -> list[str]:
    return [ln for ln in (block or "").split("\n") if ln.strip().startswith("- (")]


def title_of(line: str) -> str:
    m = re.match(r"\s*- \((.*?)\)", line)
    return m.group(1) if m else line.strip()[:40]


def alter(up: str, arm: str, pool_items: list[str]) -> str:
    """Return the arm's version of one logged user_prompt. pool_items = candidate replacement study lines, newest first."""
    out = up
    if arm in ("A", "C") and pool_items:
        m = STUDY_RE.search(out)
        if m:
            n = len(study_items(m.group(2))) or 3
            out = out[:m.start(2)] + "\n".join(pool_items[:n]) + out[m.end(2):]
    if arm in ("B1", "B3", "C"):
        keep = 3 if arm == "B3" else 1
        m = THEME_RE.search(out)
        if m:
            lines = [ln for ln in m.group(2).split("\n") if ln.strip()]
            out = out[:m.start(2)] + "\n".join(lines[:keep]) + out[m.end(2):]
    return out


def mashup(question: str, block: str) -> bool:
    """F-3504 proxy: the question names distinctive terms of 2+ of the offered study subjects (titles)."""
    items = study_items(block)
    toks = []
    for ln in items:
        toks.append({w for w in re.findall(r"\w+", title_of(ln).lower()) if len(w) >= 4 and w not in STOP})
    qt = T.tokens(question)
    hit = 0
    for i, ts in enumerate(toks):
        other = set().union(*[t for j, t in enumerate(toks) if j != i]) if len(toks) > 1 else set()
        uniq = ts - other
        if uniq and (uniq & qt):
            hit += 1
    return hit >= 2


def cmd_prereg(a) -> None:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    p = out / "prereg.json"
    if p.exists():
        print("prereg exists; not overwritten")
        return
    p.write_text(json.dumps({
        "job": "J-3421", "registered_before_any_replay": True,
        "inputs": "the 90 logged inputs of J-3265 (docs/lab/J-3265_data/inputs.jsonl)",
        "arms": {"control": "unaltered", "A": "study block rotated to newest other logged study items when equal to previous row's",
                 "B1": "Recent themes cut to 1 line", "B3": "Recent themes cut to 3 lines", "C": "A + B1"},
        "author": "command-r7b @ Ramses :11441, temperature 0.2, 3 samples",
        "judge": "falcon3:7b (TII), different family from author; mixtral hub :11438 was down at run time",
        "metrics": {"near_dup_tok": "token Jaccard > 0.6 vs previous-5 logged rows' questions, first question",
                    "near_dup_tri": "word-trigram Jaccard >= 0.3, same pool",
                    "mashup_proxy": "first question names a distinctive title term of 2+ of the offered study items (items judged on the arm's own offered block)",
                    "specificity": "falcon3 1-5, blind, pointwise"},
        "bar": "arm worth proposing only if near_dup falls >= 1/3 relative on BOTH metrics AND mashup rate rises by <= 5 points absolute AND mean specificity delta >= -0.10",
        "unit": "input row, samples averaged; paired bootstrap CI reported",
        "caveats_declared_in_advance": "arms alter prompts on a subset of rows only (A: rows with same study block as previous; B: rows with >1 / >3 theme lines); effect is reported on all 90 rows AND on affected rows.",
    }, indent=2), encoding="utf-8")
    print("prereg written")


def cmd_build(a) -> None:
    out = Path(a.out)
    rows = T.read_jsonl(Path(a.src))
    by_ts = {r["ts"]: i for i, r in enumerate(rows)}
    inputs = T.read_jsonl(INPUTS_SRC)
    recs, flips = [], 0
    for inp in inputs:
        p = by_ts.get(inp["ts"])
        if p is None:
            print("ts not found", inp["idx"])
            continue
        cur_block = T.study_block(inp["user_prompt"])
        cur_titles = {title_of(l) for l in study_items(cur_block)}
        same = bool(cur_block) and cur_block == T.study_block(rows[p - 1]["user_prompt"])
        flips += same != inp["same_study_as_prev"]
        pool, seen = [], set(cur_titles)
        if same:
            for j in range(p - 1, max(-1, p - 400), -1):
                for ln in study_items(T.study_block(rows[j]["user_prompt"])):
                    t = title_of(ln)
                    if t not in seen:
                        seen.add(t)
                        pool.append(ln)
                if len(pool) >= 3:
                    break
        prompts = {arm: inp["user_prompt"] if arm == "control" else alter(inp["user_prompt"], arm, pool if same else []) for arm in ARMS}
        recs.append({**inp, "same_study_as_prev": same, "pool_titles": [title_of(l) for l in pool[:3]], "arm_prompts": prompts,
                     "n_theme_lines": len([l for l in (THEME_RE.search(inp["user_prompt"]).group(2).split("\n") if THEME_RE.search(inp["user_prompt"]) else []) if l.strip()]),
                     "differs": {arm: prompts[arm] != prompts["control"] for arm in ARMS}})
    p = out / "inputs.jsonl"
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    print(f"built {len(recs)} rows; same_study flag disagreements vs J-3265 file: {flips}")
    for arm in ARMS[1:]:
        print(arm, "rows whose prompt differs from control:", sum(r["differs"][arm] for r in recs))


async def _gen(a) -> None:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    neutralize_telemetry(Path(a.out) / "telemetry_scratch", telemetry)
    from core.model_client import call_node_json
    out = Path(a.out)
    inputs = T.read_jsonl(out / "inputs.jsonl")
    gp = out / "gen.jsonl"
    done = {(r["idx"], r["arm"], r["sample"]) for r in T.read_jsonl(gp)}
    jobs = []
    for r in inputs:
        for arm in ARMS:
            if arm != "control" and not r["differs"][arm]:
                continue
            for s in range(SAMPLES):
                if (r["idx"], arm, s) not in done:
                    jobs.append((r, arm, s))
    random.Random(3421).shuffle(jobs)
    print(f"generate: {len(jobs)} calls ({len(done)} done)", flush=True)
    t0 = time.time()
    for n, (r, arm, s) in enumerate(jobs, 1):
        t1 = time.time()
        try:
            data = await call_node_json(T.AUTHOR_CHAIN, r["system_prompt"], r["arm_prompts"][arm], max_tokens=1024, temperature=TEMP)
            ok, err = True, None
        except Exception as exc:
            data, ok, err = None, False, repr(exc)[:200]
        T.append_jsonl(gp, {"idx": r["idx"], "arm": arm, "sample": s, "ok": ok, "err": err, "secs": round(time.time() - t1, 2),
                            "questions": T.as_questions(data)})
        if n % 25 == 0:
            print(f"  {n}/{len(jobs)} ({(time.time() - t0) / n:.1f}s/call)", flush=True)


def cmd_generate(a) -> None:
    asyncio.run(_gen(a))


def _effective(gens: list[dict], inputs: dict) -> dict:
    """(idx, arm) -> list of ok gens; arms identical to control borrow control's."""
    by: dict = {}
    for g in gens:
        if g["ok"] and g["questions"]:
            by.setdefault((g["idx"], g["arm"]), []).append(g)
    res = {}
    for i, r in inputs.items():
        for arm in ARMS:
            src = arm if (arm == "control" or r["differs"][arm]) else "control"
            res[(i, arm)] = [(g, src) for g in by.get((i, src), [])]
    return res


async def _judge(a) -> None:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    neutralize_telemetry(Path(a.out) / "telemetry_scratch", telemetry)
    from core.model_client import call_node_json
    spec = T.JUDGES[a.judge]
    out = Path(a.out)
    inputs = {r["idx"]: r for r in T.read_jsonl(out / "inputs.jsonl")}
    gens = [g for g in T.read_jsonl(out / "gen.jsonl") if g["ok"] and g["questions"]]
    jp = out / f"judge_{a.judge}.jsonl"
    done = {(r["idx"], r["arm"], r["sample"]) for r in T.read_jsonl(jp)}
    work = [g for g in gens if (g["idx"], g["arm"], g["sample"]) not in done]
    random.Random(3423).shuffle(work)
    print(f"judge[{a.judge}]: {len(work)} to score ({len(done)} done)", flush=True)
    t0 = time.time()
    for n, g in enumerate(work, 1):
        inp = inputs[g["idx"]]
        # the judge is shown the material the writer was offered in THAT arm (a rotated study block is what was offered)
        view = {"user_prompt": inp["arm_prompts"][g["arm"]], "prev_first": inp["prev_first"]}
        t1 = time.time()
        try:
            d = await call_node_json(spec["chain"], T.JUDGE_SYSTEM, T.judge_user(view, g["questions"][0]), max_tokens=60,
                                     temperature=0.0, retries=2, timeout=300, model_override=spec.get("model_override"))
            nov, spc, ans = T._num(d.get("novelty"), 1, 5), T._num(d.get("specificity"), 1, 5), T._num(d.get("answerable"), 0, 1)
            ok = nov is not None and spc is not None and ans is not None
        except Exception as exc:
            ok, nov, spc, ans = False, None, None, None
        T.append_jsonl(jp, {"idx": g["idx"], "arm": g["arm"], "sample": g["sample"], "ok": ok, "novelty": nov,
                            "specificity": spc, "answerable": ans, "secs": round(time.time() - t1, 2)})
        if n % 25 == 0:
            print(f"  {n}/{len(work)} ({(time.time() - t0) / n:.1f}s/call)", flush=True)


def cmd_judge(a) -> None:
    asyncio.run(_judge(a))


def cmd_report(a) -> None:
    out = Path(a.out)
    inputs = {r["idx"]: r for r in T.read_jsonl(out / "inputs.jsonl")}
    gens = T.read_jsonl(out / "gen.jsonl")
    eff = _effective(gens, inputs)
    jud = {(r["idx"], r["arm"], r["sample"]): r for r in T.read_jsonl(out / f"judge_{a.judge}.jsonl") if r["ok"]}
    rows = [i for i in sorted(inputs) if all(eff[(i, arm)] for arm in ARMS)]
    per = {}   # arm -> metric -> list per row (aligned with rows)
    for arm in ARMS:
        m = {"dup_tok": [], "dup_tri": [], "mash": [], "spec": [], "nov": [], "ans": []}
        for i in rows:
            block = T.study_block(inputs[i]["arm_prompts"][arm])
            gs = eff[(i, arm)]
            m["dup_tok"].append(T.mean([float(T.is_near_dup(g["questions"][0], inputs[i]["prev_pool"])["dup_tok"]) for g, _ in gs]))
            m["dup_tri"].append(T.mean([float(T.is_near_dup(g["questions"][0], inputs[i]["prev_pool"])["dup_tri"]) for g, _ in gs]))
            m["mash"].append(T.mean([float(mashup(g["questions"][0], block)) for g, _ in gs]))
            js = [jud.get((i, src, g["sample"])) for g, src in gs]
            js = [j for j in js if j]
            m["spec"].append(T.mean([j["specificity"] for j in js]))
            m["nov"].append(T.mean([j["novelty"] for j in js]))
            m["ans"].append(T.mean([j["answerable"] for j in js]))
        per[arm] = m
    rep = {"n_inputs": len(inputs), "rows_complete_all_arms": len(rows), "judge": a.judge, "gens": len(gens),
           "gens_failed": sum(1 for g in gens if not (g["ok"] and g["questions"])),
           "logged_mashup_rate_first_question": T.mean([float(mashup(inputs[i]["logged_questions"][0], T.study_block(inputs[i]["user_prompt"]))) for i in rows if inputs[i]["logged_questions"]])}

    def sub(vals, idxs):
        return T.mean([vals[k] for k in idxs])

    arms_out = {}
    for arm in ARMS:
        aff = [k for k, i in enumerate(rows) if arm == "control" or inputs[i]["differs"][arm]]
        d = {"rows_altered": len(aff)}
        for met in ("dup_tok", "dup_tri", "mash", "spec", "nov", "ans"):
            d[met] = sub(per[arm][met], range(len(rows)))
            d[met + "_affected_rows"] = sub(per[arm][met], aff)
            d[met + "_control_on_affected_rows"] = sub(per["control"][met], aff)
        if arm != "control":
            def rel(base, x):
                return None if not base else (base - x) / base
            r_tok, r_tri = rel(per_mean(per["control"]["dup_tok"]), per_mean(per[arm]["dup_tok"])), rel(per_mean(per["control"]["dup_tri"]), per_mean(per[arm]["dup_tri"]))
            dm = per_mean(per[arm]["mash"]) - per_mean(per["control"]["mash"])
            ds = per_mean(per[arm]["spec"]) - per_mean(per["control"]["spec"]) if per_mean(per[arm]["spec"]) is not None else None
            d["rel_drop_tok"], d["rel_drop_tri"], d["d_mash_points"], d["d_specificity"] = r_tok, r_tri, dm * 100, ds
            d["bootstrap_dup_tok"] = T.paired_bootstrap(per["control"]["dup_tok"], per[arm]["dup_tok"])
            d["bootstrap_spec"] = T.paired_bootstrap(per["control"]["spec"], per[arm]["spec"]) if all(v is not None for v in per[arm]["spec"] + per["control"]["spec"]) else None
            c1 = bool(r_tok is not None and r_tri is not None and r_tok >= 1 / 3 - 1e-9 and r_tri >= 1 / 3 - 1e-9)
            c2 = dm <= MASH_RISE_MAX + 1e-9
            c3 = ds is not None and ds >= -T.SPECIFICITY_MARGIN - 1e-9
            d["verdict"] = {"dup_falls_by_third_both": c1, "mashup_not_up_more_than_5pts": c2, "specificity_not_fall": c3, "worth_proposing": c1 and c2 and c3}
        arms_out[arm] = d
    rep["arms"] = arms_out
    (out / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep, indent=2, ensure_ascii=False))


def per_mean(xs):
    return T.mean(xs)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--src", default="")
        p.add_argument("--out", default=str(OUT_DEFAULT))
        p.add_argument("--judge", default="falcongpu")
    for name, fn in (("prereg", cmd_prereg), ("build", cmd_build), ("generate", cmd_generate), ("judge", cmd_judge), ("report", cmd_report)):
        p = sub.add_parser(name)
        common(p)
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

"""
Nascence -- TRAIN LAB: analysis of the J-0791 wording-A/B replicate + scale-up batch
(scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py).  READ-ONLY on every input; writes only the
report/summary paths named below (default: the worktree's docs/lab + the shared scratchpad).

Inputs
  * SCRATCH/J-0791_results.jsonl       -- this run's per-call rows (set, pass, arm, train_id, ok, unresolved,
                                          intention, qmark, opened, act_kind, thought, error_class, excluded, ...)
  * docs/lab/train_wording_ab_qwen_2026-09-08.jsonl        -- J-0777's 160 rows (= draw 1 of the "orig" set)
  * docs/lab/train_model_ab_gemma_vs_qwen_2026-09-08.jsonl -- J-0724's qwen3.5:9b rows (= a 3rd, older reading
                                          of the CURRENT wording on the "orig" prompts; no other arm)
Definitions
  * a DRAW of a prompt = one (set, pass, train_id) quartet in which all 4 arms produced a parseable answer;
    only complete quartets enter the paired comparisons (an interrupted final event is dropped from them, not
    from the call-level tables);
  * opened = unresolved OR intention OR '?' in thought  (the live gate, nodes/inner_monologue_node.py:4377);
  * excluded (infra failure after 3 retries) and parse-failure calls are excluded from every rate and counted;
  * CIs: Wilson for single call-level proportions; for every between-arm contrast and every pooled rate a
    PROMPT-CLUSTER bootstrap (prompts resampled with replacement within stratum orig / fresh, arms evaluated on
    the SAME resampled prompts, so contrasts are paired and prompt-to-prompt variation is counted as variance).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(os.environ.get("LAB_SCRATCH") or
               r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\8d915dfa-80f4-4aad-a2e3-206e842f08dd\scratchpad")
ARMS = ["current", "candidate_A", "candidate_B", "candidate_C"]
CAND = ["candidate_A", "candidate_B", "candidate_C"]
SHORT = {"current": "current", "candidate_A": "A", "candidate_B": "B", "candidate_C": "C"}
B_BOOT = 20000
SEED = 20260922


def load_jsonl(p: Path) -> list:
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


def norm(r: dict, sset: str, pas: int) -> dict:
    return {"set": sset, "pass": pas, "arm": r["arm"], "train_id": r["train_id"], "ok": bool(r.get("ok")),
            "unresolved": bool(r.get("unresolved")), "intention": (r.get("intention") or "").strip(),
            "qmark": bool(r.get("qmark")), "opened": bool(r.get("opened")), "act_kind": r.get("act_kind") or "none",
            "thought": r.get("thought") or "", "error_class": r.get("error_class"),
            "excluded": bool(r.get("excluded")), "latency_s": r.get("latency_s"), "n_attempts": r.get("n_attempts", 1)}


def load_all(results_path: Path):
    mine = {}
    for r in load_jsonl(results_path):
        mine[f"{r['set']}|{r['pass']}|{r['arm']}|{r['train_id']}"] = r     # latest row per unit wins
    rows = [norm(r, r["set"], r["pass"]) for r in mine.values()]
    j77 = [norm(r, "orig", 1) for r in load_jsonl(ROOT / "docs" / "lab" / "train_wording_ab_qwen_2026-09-08.jsonl")]
    j24 = [norm({**r, "arm": "current"}, "orig", 0)
           for r in load_jsonl(ROOT / "docs" / "lab" / "train_model_ab_gemma_vs_qwen_2026-09-08.jsonl")
           if r.get("model") == "qwen3.5:9b"]
    return rows, j77, j24


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def fmt(x, nd=3):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def share_str(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {fmt(k / n if n else float('nan'))} [{fmt(lo, 2)}, {fmt(hi, 2)}]"


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


# ── intention format ─────────────────────────────────────────────────────────────────────────────────────────
FIRST_PERSON = re.compile(r"^\s*(I\b|I['’]|Let me\b|Let['’]s\b|My\b|We\b)")
TO_INF = re.compile(r"^\s*to\s+\w", re.I)


def intention_kind(s: str) -> str:
    if FIRST_PERSON.match(s):
        return "first_person"
    if TO_INF.match(s):
        return "to_infinitive_fragment"
    return "bare_imperative_fragment"


# ── call-level tables ────────────────────────────────────────────────────────────────────────────────────────
def call_table(rows, sets_passes):
    """arm -> counts for the rows in the given (set, pass) draws."""
    out = {}
    for arm in ARMS:
        rs = [r for r in rows if r["arm"] == arm and (r["set"], r["pass"]) in sets_passes]
        ok = [r for r in rs if r["ok"]]
        out[arm] = {"n_units": len(rs), "n_ok": len(ok), "n_excluded": sum(1 for r in rs if r["excluded"]),
                    "n_parse_fail": sum(1 for r in rs if (not r["ok"]) and r["error_class"] == "content"),
                    "unresolved": sum(r["unresolved"] for r in ok), "intention": sum(bool(r["intention"]) for r in ok),
                    "qmark": sum(r["qmark"] for r in ok), "opened": sum(r["opened"] for r in ok),
                    "act": sum(1 for r in ok if r["act_kind"] != "none")}
    return out


# ── prompt-level matrix for the cluster bootstrap ────────────────────────────────────────────────────────────
def build_prompt_rates(rows):
    """Complete quartets only.  Returns {stratum: (train_ids, R)} with R[i] = per-arm mean opened over the
    prompt's complete draws, plus the draws-per-prompt."""
    by_draw = defaultdict(dict)
    for r in rows:
        if r["ok"] and r["pass"] >= 1:
            by_draw[(r["set"], r["pass"], r["train_id"])][r["arm"]] = r
    per_prompt = defaultdict(lambda: {a: [] for a in ARMS})
    stratum_of = {}
    for (sset, pas, tid), d in by_draw.items():
        if all(a in d for a in ARMS):
            stratum_of[tid] = "orig" if sset == "orig" else ("mid" if sset.startswith("mid") else "fresh")
            for a in ARMS:
                per_prompt[tid][a].append(1.0 if d[a]["opened"] else 0.0)
    strata = {"orig": [], "fresh": [], "mid": []}
    for tid, per_arm in per_prompt.items():
        strata[stratum_of[tid]].append((tid, [float(np.mean(per_arm[a])) for a in ARMS], len(per_arm[ARMS[0]])))
    out = {}
    for s, items in strata.items():
        items.sort()
        out[s] = ([i[0] for i in items], np.array([i[1] for i in items]) if items else np.zeros((0, 4)),
                  [i[2] for i in items])
    return out


def bootstrap(strata_R: dict, keys: list, rng):
    """keys: subset of strata names to pool (prompt-equal-weighted).  Returns (point[4], boot[B,4], N)."""
    parts = [(strata_R[k][1]) for k in keys if len(strata_R[k][1])]
    if not parts:
        return None, None, 0
    N = sum(len(p) for p in parts)
    point = sum(p.sum(axis=0) for p in parts) / N
    boots = np.zeros((B_BOOT, 4))
    for p in parts:
        idx = rng.integers(0, len(p), size=(B_BOOT, len(p)))
        boots += p[idx].sum(axis=1)
    return point, boots / N, N


def ci(x, lo=2.5, hi=97.5):
    return (float(np.percentile(x, lo)), float(np.percentile(x, hi)))


def contrast_block(name, point, boots, N):
    """Markdown rows for the pooled rates and the between-arm contrasts of one pool."""
    lines = [f"**{name}** (prompt-equal-weighted, {N} prompts, cluster-bootstrap B={B_BOOT})", ""]
    rows = []
    for j, a in enumerate(ARMS):
        lo, hi = ci(boots[:, j])
        rows.append([f"`{a}`", fmt(point[j]), f"[{fmt(lo, 3)}, {fmt(hi, 3)}]"])
    lines += md_table(["arm", "opened-share", "95% CI (prompts resampled)"], rows) + [""]
    rows = []
    pairs = [("A", "B", 1, 2), ("A", "C", 1, 3), ("B", "C", 2, 3), ("A", "current", 1, 0), ("B", "current", 2, 0),
             ("C", "current", 3, 0)]
    for a, b, i, j in pairs:
        d = boots[:, i] - boots[:, j]
        lo, hi = ci(d)
        p_gt = float(np.mean(d > 0) + 0.5 * np.mean(d == 0))
        rows.append([f"{a} - {b}", f"{point[i] - point[j]:+.3f}", f"[{lo:+.3f}, {hi:+.3f}]", fmt(p_gt, 3),
                     "excludes 0" if (lo > 0 or hi < 0) else "INCLUDES 0"])
    lines += md_table(["contrast", "point", "95% CI (paired, prompts resampled)", f"P(first > second)", "CI vs 0"], rows) + [""]
    # rank probabilities among the 3 candidates
    ranks = Counter()
    for row in boots[:, 1:4]:
        ranks["".join(sorted("ABC", key=lambda c: -row["ABC".index(c)]))] += 1
    tot = sum(ranks.values())
    top = ", ".join(f"{k}: {v / tot:.2f}" for k, v in ranks.most_common(6))
    lines.append(f"Candidate ordering frequency across bootstrap resamples (best-to-worst; ties broken by label): {top}")
    se_ab = float(np.std(boots[:, 1] - boots[:, 2]))
    se_ac = float(np.std(boots[:, 1] - boots[:, 3]))
    lines.append(f"Precision: SE(A - B) = {se_ab:.3f}, SE(A - C) = {se_ac:.3f}. A 95% half-width of +-0.05 on one of these gaps needs "
                 f"about N x (SE/0.025)^2 = {N * (se_ab / 0.025) ** 2:.0f} (A-B) / {N * (se_ac / 0.025) ** 2:.0f} (A-C) prompts "
                 f"(at the draws per prompt used here; this pool has {N}); minimal detectable gap at 80% power ~ 2.8 x SE = "
                 f"{2.8 * se_ab:.3f} (A-B), {2.8 * se_ac:.3f} (A-C).")
    lines.append("")
    return lines


def live_rates() -> dict:
    """READ-ONLY: opened/unresolved/intention/'?' share of real logged mid-train steps (position >= 2 in a train), by period."""
    import datetime as _dt
    rows = load_jsonl(Path(r"C:\Nascence\data\monologue_log.jsonl"))
    by = defaultdict(list)
    for r in rows:
        if r.get("train_id"):
            by[r["train_id"]].append(r)
    periods = {"08-21..09-04": ("08-21", "09-04"), "09-05..09-08": ("09-05", "09-08"), "09-09..09-16": ("09-09", "09-16"),
               "09-17..09-22": ("09-17", "09-22")}
    out = {}
    for name, (a_, b_) in periods.items():
        n = k = nu = ni = nq = 0
        for rs in by.values():
            rs = sorted(rs, key=lambda r: r["ts"])
            for i, r in enumerate(rs):
                if i >= 1 and a_ <= _dt.datetime.fromtimestamp(r["ts"]).strftime("%m-%d") <= b_:
                    u, it, q = bool(r.get("unresolved")), bool((r.get("intention") or "").strip()), "?" in (r.get("thought") or "")
                    n += 1
                    k += (u or it or q)
                    nu += u
                    ni += it
                    nq += q
        if n:
            out[name] = {"n": n, "opened": k / n, "unresolved": nu / n, "intention": ni / n, "qmark": nq / n}
    return out


def live_train_lengths() -> dict:
    """READ-ONLY: real train lengths (data/train_length_log.jsonl) by era: n, mean length, the implied geometric continuation
    probability 1 - 1/mean, and the share of closes that are `thread-end` (= the replay lab's 'fork-rate-if-ungated')."""
    import datetime as _dt
    rows = load_jsonl(Path(r"C:\Nascence\data\train_length_log.jsonl"))
    eras = {"08-03..08-16 (gemma, before TRAIN_HOLD)": ("08-03", "08-16"), "08-17..08-20 (gemma, TRAIN_HOLD)": ("08-17", "08-20"),
            "08-21..09-04 (qwen)": ("08-21", "09-04"), "09-05..09-22 (qwen)": ("09-05", "09-22")}
    out = {}
    for name, (a_, b_) in eras.items():
        rs = [r for r in rows if a_ <= _dt.datetime.fromtimestamp(r["ts"]).strftime("%m-%d") <= b_]
        if rs:
            m = float(np.mean([r["length"] for r in rs]))
            out[name] = {"n": len(rs), "mean_len": m, "implied_p": 1 - 1 / m,
                         "thread_end_share": sum(1 for r in rs if r.get("reason") == "thread-end") / len(rs)}
    return out


def closing_last_open(train_ids) -> tuple:
    """(# of these trains whose LAST logged step was open by the live gate, # of trains)."""
    rows = load_jsonl(Path(r"C:\Nascence\data\monologue_log.jsonl"))
    want = set(train_ids)
    last = {}
    for r in rows:
        t = r.get("train_id")
        if t in want and (t not in last or r["ts"] >= last[t]["ts"]):
            last[t] = r
    n_open = sum(1 for r in last.values() if r.get("unresolved") or (r.get("intention") or "").strip() or "?" in (r.get("thought") or ""))
    return (n_open, len(last))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(SCRATCH / "J-0791_results.jsonl"))
    ap.add_argument("--out-md", default=str(ROOT / "docs" / "lab" / "train_wording_ab_qwen_replicate_J-0791_2026-09-22.md"))
    ap.add_argument("--out-jsonl", default=str(ROOT / "docs" / "lab" / "train_wording_ab_qwen_replicate_J-0791_2026-09-22.jsonl"))
    ap.add_argument("--out-json", default=str(SCRATCH / "J-0791_analysis.json"))
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()

    mine, j77, j24 = load_all(Path(a.results))
    rng = np.random.default_rng(SEED)
    all_rows = mine + j77                                   # draws >= 1
    _ord = lambda n: {"orig": 0, "fresh": 1, "mid": 2}[re.match(r"[a-z]+", n).group(0)]
    sp_mine = sorted({(r["set"], r["pass"]) for r in mine}, key=lambda sp: (_ord(sp[0]), sp[0], sp[1]))
    sets_order = sorted({s for s, _ in sp_mine}, key=lambda s: ({"orig": 0, "fresh": 1, "mid": 2}[re.match(r"[a-z]+", s).group(0)], s))
    L = []
    L += ["# Train Lab -- Wording A/B REPLICATE + SCALE-UP on qwen3.5:9b only (2026-09-22, J-0791)", "",
          "**J-0791** (spawned from F-1139/J-0777; prep F-1156), prep work for **D-0165** -- D-0165's named defeater is "
          "\"Revisit once J-0791 confirms or adjusts the specific candidate ranking (A vs B vs C) at a larger sample\". "
          "Script: `scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py` (run 2026-09-22 in the Du-offline lab window); "
          "this report: `scripts/train_lab_wording_ab_replicate_J-0791_analyze.py`. Does NOT change "
          "`nodes/inner_monologue_node.py` or any live file; does NOT rule D-0165.", ""]

    # ── 0. what was run ───────────────────────────────────────────────────────────────────────────────────────
    n_units = len(mine)
    n_ok = sum(r["ok"] for r in mine)
    n_excl = sum(r["excluded"] for r in mine)
    n_pf = sum(1 for r in mine if (not r["ok"]) and r["error_class"] == "content")
    lat = [r["latency_s"] for r in mine if r["latency_s"] is not None and r["ok"]]
    retried = sum(1 for r in mine if r["n_attempts"] and r["n_attempts"] > 1)
    L += ["## What was run", "",
          f"- Design: 4 arms (`current` = live wording, `candidate_A/B/C` = J-0777's three rewordings, wording byte-identical) "
          f"x prompts x independent draws, model `qwen3.5:9b` only (hot hub 127.0.0.1:11433), temperature 0.75, "
          f"max_tokens 400 (TRAIN_MIDTRAIN_TOKENS), one request at a time, timeout 300 s, infra errors retried 3x (20/60/180 s).",
          "- Set `orig` = the SAME 40 real (origin, last_step, ledger) triples J-0724/J-0777 used; draw 1 of `orig` is "
          "J-0777's own committed data, later draws are this run.",
          "- Sets `fresh1..freshK` = NEW real trains (never used before), J-0724's own sampling recipe over the last 5 days of "
          "`data/monologue_log.jsonl` (>=2 real steps, evenly spaced by time, ledger = up to 3 newest `train_state_log` rows), "
          "dealt round-robin into sets of 40; one draw each per scheduled pass. These are CLOSING contexts: each prompt quotes the "
          "train's last logged step, which closed that train (the design J-0724/J-0777 used).",
          "- Sets `mid1..midM` = OPEN contexts (an extension beyond the brief, added after the calibration check in Result 5b): the quoted "
          "step is a real interior step k of a real train, so it was open by construction as in the live node; the ledger holds up to 7 "
          "`train_state_log` entries cut to 160 chars as the live `_train_ledger` does, the model is asked for step k+1 and the REAL "
          "logged step k+1 flags are kept as a calibration reference. Prompts: `..._2026-09-22_events.json` (keys `fresh`, `mid`).",
          f"- This run's units: {n_units} recorded, {n_ok} parsed OK, {n_excl} excluded after 3 infra retries, {n_pf} "
          f"parse failures (no JSON after call_node_json's own 2 retries); {retried} units needed >1 attempt; "
          f"per-call latency mean {fmt(float(np.mean(lat)) if lat else float('nan'), 2)} s, median "
          f"{fmt(float(np.median(lat)) if lat else float('nan'), 2)} s, max {fmt(float(np.max(lat)) if lat else float('nan'), 1)} s.", ""]

    # ── 1. per-draw call-level tables ─────────────────────────────────────────────────────────────────────────
    L += ["## Result 1 -- every draw, call level (opened = unresolved OR intention OR '?')", ""]
    draws = [("orig", 1, "J-0777 (F-1139)")] + [(s, p, "this run") for s, p in sp_mine]
    hdr = ["draw", "source", "arm", "n_ok", "unresolved", "intention", "'?'", "opened (share [Wilson 95%])", "act!=none"]
    rows_t = []
    per_draw_summary = {}
    for sset, pas, src in draws:
        ct = call_table(all_rows, {(sset, pas)})
        per_draw_summary[f"{sset}/p{pas}"] = ct
        for arm in ARMS:
            c = ct[arm]
            if c["n_ok"] == 0:
                continue
            rows_t.append([f"{sset} p{pas}", src, f"`{arm}`", c["n_ok"], c["unresolved"], c["intention"], c["qmark"],
                           share_str(c["opened"], c["n_ok"]), c["act"]])
    L += md_table(hdr, rows_t) + [""]

    # compact opened-share matrix
    L += ["Opened-share matrix (rows = draws, columns = arms; n per cell in brackets):", ""]
    mrows = []
    for sset, pas, src in draws:
        ct = call_table(all_rows, {(sset, pas)})
        if all(ct[a]["n_ok"] == 0 for a in ARMS):
            continue
        mrows.append([f"{sset} p{pas}"] + [f"{fmt(ct[a]['opened'] / ct[a]['n_ok'], 3)} [{ct[a]['n_ok']}]" if ct[a]["n_ok"] else "-"
                                          for a in ARMS])
    L += md_table(["draw"] + [f"`{x}`" for x in ARMS], mrows) + [""]

    # ── 2. pooled + ranking ───────────────────────────────────────────────────────────────────────────────────
    strata_R = build_prompt_rates(all_rows)
    L += ["## Result 2 -- pooled rates and the candidate ranking (paired, prompt-cluster bootstrap)", "",
          "Only complete quartets (all 4 arms parsed) enter this section. Prompts, not calls, are the resampled unit: "
          "40 `orig` prompts (each with every draw incl. J-0777's) and the fresh prompts; this counts prompt-to-prompt "
          "variation, which repeated draws on the same prompt cannot remove.", ""]
    summary = {"strata_sizes": {k: len(v[0]) for k, v in strata_R.items()}}
    pools = [("CLOSING contexts -- ORIG: the 40 J-0724/J-0777 prompts (all draws incl. J-0777's pass 1)", ["orig"]),
             ("CLOSING contexts -- FRESH: never-used real trains, same recipe, one draw each", ["fresh"]),
             ("CLOSING contexts pooled (ORIG + FRESH, prompt-equal-weighted): the design J-0777 used, at a larger sample", ["orig", "fresh"]),
             ("OPEN contexts -- MID: the quoted step is a real interior (open) step, as in the live node", ["mid"]),
             ("ALL contexts (closing + open), prompt-equal-weighted -- mixes two designs, read the contrasts only", ["orig", "fresh", "mid"])]
    for name, keys in pools:
        point, boots, N = bootstrap(strata_R, keys, rng)
        if point is None:
            L += [f"**{name}**: no complete quartets yet.", ""]
            continue
        L += contrast_block(name, point, boots, N)
        summary[name] = {"N": N, "point": dict(zip(ARMS, map(float, point))),
                         "ci": {a: ci(boots[:, j]) for j, a in enumerate(ARMS)},
                         "A_minus_B": {"point": float(point[1] - point[2]), "ci": ci(boots[:, 1] - boots[:, 2])},
                         "A_minus_C": {"point": float(point[1] - point[3]), "ci": ci(boots[:, 1] - boots[:, 3])},
                         "B_minus_C": {"point": float(point[2] - point[3]), "ci": ci(boots[:, 2] - boots[:, 3])}}

    # independent confirmation: closing-context data collected AFTER J-0777 (its own draw excluded)
    strata_mine = build_prompt_rates(mine)
    point_m, boots_m, N_m = bootstrap(strata_mine, ["orig", "fresh"], np.random.default_rng(SEED + 7))
    if point_m is not None:
        L += contrast_block("CLOSING contexts pooled, THIS RUN ONLY (J-0777's draw EXCLUDED): does the result replicate on data collected after it?",
                            point_m, boots_m, N_m)
        summary["closing_this_run_only"] = {"N": N_m, "point": dict(zip(ARMS, map(float, point_m))),
                                            "A_minus_B": {"point": float(point_m[1] - point_m[2]), "ci": ci(boots_m[:, 1] - boots_m[:, 2])},
                                            "A_minus_C": {"point": float(point_m[1] - point_m[3]), "ci": ci(boots_m[:, 1] - boots_m[:, 3])},
                                            "B_minus_C": {"point": float(point_m[2] - point_m[3]), "ci": ci(boots_m[:, 2] - boots_m[:, 3])}}

    # replicate-only view of the orig set (this run's own draws, without J-0777)
    L += ["### Replicate-only: this run's draws on the 40 `orig` prompts, WITHOUT J-0777's draw", ""]
    ct_rep = call_table(mine, {(s, p) for s, p in sp_mine if s == "orig"})
    rows_t = [[f"`{arm}`", ct_rep[arm]["n_ok"], share_str(ct_rep[arm]["opened"], ct_rep[arm]["n_ok"]),
               share_str(ct_rep[arm]["unresolved"], ct_rep[arm]["n_ok"]), share_str(ct_rep[arm]["intention"], ct_rep[arm]["n_ok"])]
              for arm in ARMS if ct_rep[arm]["n_ok"]]
    L += md_table(["arm", "n_ok", "opened", "unresolved", "intention"], rows_t) + [""]

    # ── 3. the current-arm swing ──────────────────────────────────────────────────────────────────────────────
    L += ["## Result 3 -- the `current`-arm swing (0.125 in J-0777 vs 0.25 in J-0724): sampling variance or not?", ""]
    readings = [("J-0724 (09-08 earlier run)", [r for r in j24 if r["ok"]]),
                ("J-0777 (F-1139)", [r for r in j77 if r["arm"] == "current" and r["ok"]])]
    for s, p in sp_mine:
        if s == "orig":
            readings.append((f"this run orig p{p}", [r for r in mine if r["set"] == s and r["pass"] == p and r["arm"] == "current" and r["ok"]]))
    rows_t = []
    tab = []
    for name, rs in readings:
        k, n = sum(r["opened"] for r in rs), len(rs)
        rows_t.append([name, share_str(k, n)])
        tab.append([k, n - k])
    L += md_table(["reading of the IDENTICAL wording + model + 40 prompts", "opened"], rows_t) + [""]
    if len(tab) >= 2:
        chi2, pchi, dof, _ = stats.chi2_contingency(np.array(tab), correction=False)
        sh = np.array([t[0] / (t[0] + t[1]) for t in tab])
        pbar = sum(t[0] for t in tab) / sum(t[0] + t[1] for t in tab)
        exp_sd = math.sqrt(pbar * (1 - pbar) / 40)
        f_p = stats.fisher_exact([tab[0], tab[1]])[1]
        L += [f"- Homogeneity of the {len(tab)} readings: chi2={chi2:.2f}, dof={dof}, p={pchi:.3f} "
              f"(small p = the readings differ more than binomial noise allows).",
              f"- Observed SD of the readings = {sh.std(ddof=1):.3f} vs the SD a pure-binomial n=40 draw at the pooled "
              f"rate {pbar:.3f} would show = {exp_sd:.3f}.",
              f"- J-0724 (10/40) vs J-0777 (5/40) alone: Fisher exact p={f_p:.3f} -- the 0.25-vs-0.125 gap that motivated this job.", ""]
        summary["current_swing"] = {"readings": {n: t for (n, _), t in zip(readings, tab)}, "chi2_p": float(pchi),
                                    "observed_sd": float(sh.std(ddof=1)), "binomial_sd": exp_sd, "fisher_j24_vs_j77_p": float(f_p)}

    # ── 4. consistency within prompts (draws vs prompts) ──────────────────────────────────────────────────────
    L += ["## Result 4 -- how much of the outcome is the prompt and how much is the draw (orig set)", ""]
    by_pd = defaultdict(lambda: defaultdict(dict))            # tid -> pass -> arm -> opened
    for r in all_rows:
        if r["set"] == "orig" and r["ok"] and r["pass"] >= 1:
            by_pd[r["train_id"]][r["pass"]][r["arm"]] = int(r["opened"])
    passes = sorted({p for d in by_pd.values() for p in d})
    rows_t = []
    for arm in ARMS:
        # complete prompts: prompt has this arm in every pass
        mat = [[by_pd[t][p][arm] for p in passes] for t in by_pd if all(arm in by_pd[t].get(p, {}) for p in passes)]
        if len(passes) >= 2 and len(mat) >= 5:
            M = np.array(mat, dtype=float)
            m = M.shape[1]
            msb = m * M.mean(axis=1).var(ddof=1)
            msw = M.var(axis=1, ddof=1).mean()
            icc = (msb - msw) / (msb + (m - 1) * msw) if (msb + (m - 1) * msw) > 0 else float("nan")
            allsame = float(np.mean([len(set(row)) == 1 for row in M]))
            # J-0777 pass 1 vs the first of this run's passes: agreement + kappa
            a1, a2 = M[:, 0], M[:, 1]
            po = float(np.mean(a1 == a2))
            pe = float(a1.mean() * a2.mean() + (1 - a1.mean()) * (1 - a2.mean()))
            kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
            rows_t.append([f"`{arm}`", len(mat), m, fmt(float(M.mean()), 3), fmt(allsame, 2), fmt(po, 2), fmt(kappa, 2), fmt(icc, 2)])
    if rows_t:
        L += md_table(["arm", "prompts", "draws/prompt", "mean opened", "share of prompts with the same outcome in EVERY draw",
                       "agreement draw1 vs draw2", "Cohen kappa (draw1,draw2)", "ICC(1)"], rows_t) + [""]
        L += ["ICC near 1 = the prompt decides the outcome (extra draws on the same prompts add little); near 0 = "
              "the draw decides (extra draws are as good as new prompts).", ""]
    # draw independence
    dup = tot = 0
    by_key = {(r["arm"], r["train_id"], r["pass"]): r["thought"] for r in all_rows if r["set"] == "orig" and r["ok"]}
    for (arm, tid, p), th in by_key.items():
        if p == 1 and (arm, tid, 2) in by_key:
            tot += 1
            dup += int(th == by_key[(arm, tid, 2)])
    if tot:
        L += [f"- Draw independence check: identical `thought` text between J-0777's draw and this run's first orig draw for the same "
              f"(arm, prompt): {dup}/{tot} (must be ~0 -- no seed is passed, so each call is a fresh draw).", ""]

    # ── 5. by set ─────────────────────────────────────────────────────────────────────────────────────────────
    L += ["## Result 5 -- by prompt set (does the 40-prompt `orig` sample look typical? do open contexts differ?)", ""]
    rows_t = []
    for s in sets_order:
        ct = call_table(mine, {(s, p) for ss, p in sp_mine if ss == s})
        if any(ct[a]["n_ok"] for a in ARMS):
            rows_t.append([s] + [f"{fmt(ct[a]['opened'] / ct[a]['n_ok'], 3)} [{ct[a]['n_ok']}]" if ct[a]["n_ok"] else "-" for a in ARMS])
    ct77 = call_table(j77, {("orig", 1)})
    rows_t.insert(0, ["orig (J-0777 draw only)"] + [f"{fmt(ct77[a]['opened'] / ct77[a]['n_ok'], 3)} [{ct77[a]['n_ok']}]" for a in ARMS])
    L += md_table(["set (this run's draws pooled)"] + [f"`{x}`" for x in ARMS], rows_t) + [""]

    # ── 5b. calibration against the live log ──────────────────────────────────────────────────────────────────
    L += ["## Result 5b -- calibration: does the lab's `current` arm look like the live node?", ""]
    live = live_rates()
    L += ["Real logged mid-train steps (`data/monologue_log.jsonl`, rows with a train_id, step position >= 2 = the steps the "
          "mid-train prompt generates; the wording has been the CURRENT block throughout): "
          + "; ".join(f"{k}: opened {v['opened']:.3f} (unresolved {v['unresolved']:.3f}, intention {v['intention']:.3f}, "
                      f"'?' {v['qmark']:.3f}, n={v['n']})" for k, v in live.items()) + ".", ""]
    summary["live_rates"] = live
    ll = live_train_lengths()
    L += ["Real train lengths by era (`data/train_length_log.jsonl`, one row per closed train): "
          + "; ".join(f"{k}: n={v['n']}, mean length {v['mean_len']:.2f} (implied per-step continuation {v['implied_p']:.3f}), "
                      f"thread-end = {v['thread_end_share']:.3f} of closes" for k, v in ll.items())
          + ". The replay lab's `fork-rate-if-ungated` (docs/lab/train_split_merge_step2_replay_2026-09-06.md, kill criterion #1) is exactly "
            "this thread-end share of closes: it has been 0.92-0.96 in every era, i.e. it does not track the per-step opened rate "
            "(0.735 -> 0.52 implied) that the wording controls.", ""]
    summary["live_train_lengths"] = ll
    _mid_src = SCRATCH / "J-0791_mid_events.json"
    _events_doc = ROOT / "docs" / "lab" / "train_wording_ab_qwen_replicate_J-0791_2026-09-22_events.json"
    if _mid_src.exists() or _events_doc.exists():
        _mid_list = (json.loads(_mid_src.read_text(encoding="utf-8"))["events"] if _mid_src.exists()
                     else json.loads(_events_doc.read_text(encoding="utf-8"))["mid"])
        mev = {e["train_id"]: e for e in _mid_list}
        # per-prompt lab rates on the mid prompts (all arms), from the complete-quartet matrix
        ids, R, _n = strata_R.get("mid", ([], np.zeros((0, 4)), []))
        if len(ids):
            real = np.array([1.0 if mev[i]["real_next"]["opened"] else 0.0 for i in ids])
            rows_t = [["real logged next step (live node, full seed marketplace)", fmt(float(real.mean())), "-", "-"]]
            rng2 = np.random.default_rng(SEED + 1)
            idx = rng2.integers(0, len(ids), size=(B_BOOT, len(ids)))
            for j, arm in enumerate(ARMS):
                d = R[idx, j].mean(axis=1) - real[idx].mean(axis=1)
                lo, hi = ci(d)
                corr = float(np.corrcoef(R[:, j], real)[0, 1]) if R[:, j].std() > 0 else float("nan")
                rows_t.append([f"lab `{arm}` (reduced prompt: mid-thread block only)", fmt(float(R[:, j].mean())),
                               f"{R[:, j].mean() - real.mean():+.3f} [{lo:+.3f}, {hi:+.3f}]", fmt(corr, 2)])
            L += [f"On the {len(ids)} OPEN-context prompts with all four arms parsed, against the REAL next step that the live node "
                  f"logged from the same context:", ""]
            L += md_table(["source", "opened-share", "lab minus real [95% CI, prompts resampled]", "per-prompt corr. with real next"], rows_t) + [""]
            summary["mid_calibration"] = {"n": len(ids), "real": float(real.mean()),
                                          "lab": {a: float(R[:, j].mean()) for j, a in enumerate(ARMS)}}
            # ILLUSTRATION (inferred, not measured): shift each arm's lab rate by the constant log-odds gap that maps the lab's
            # `current` arm onto the real logged next step, then read the implied live continuation probability and the
            # geometric mean train length 1/(1-p).  Assumes the lab->live distortion is one constant log-odds shift for
            # every wording, which nothing here tests; the live node also caps trains (soft cap 4 with a building check,
            # hard cap 40), so 1/(1-p) overstates long trains.
            def _logit(x):
                x = np.clip(x, 0.01, 0.99)
                return np.log(x / (1 - x))

            def _expit(x):
                return 1 / (1 + np.exp(-x))

            labm = R[idx].mean(axis=1)                       # (B, 4) resampled lab rates
            realm = real[idx].mean(axis=1)                   # (B,)
            shift = _logit(realm) - _logit(labm[:, 0])
            pl = _expit(_logit(labm) + shift[:, None])
            pt = _expit(_logit(R.mean(axis=0)) + (_logit(real.mean()) - _logit(R[:, 0].mean())))
            rows_i = []
            for j, arm in enumerate(ARMS):
                lo_p, hi_p = ci(pl[:, j])
                lo_l, hi_l = ci(1 / (1 - pl[:, j]))
                rows_i.append([f"`{arm}`", fmt(float(R[:, j].mean())), fmt(float(pt[j])), f"[{lo_p:.3f}, {hi_p:.3f}]",
                               f"{1 / (1 - float(pt[j])):.2f}", f"[{lo_l:.2f}, {hi_l:.2f}]"])
            L += ["Illustration (INFERRED, not measured; see the assumption in the script): map each arm onto the live node by the constant "
                  "log-odds shift that takes the lab `current` arm to the real logged next-step rate, then read the implied live "
                  "continuation probability p and the geometric mean train length 1/(1-p). For scale, the live mean train length "
                  "(`data/train_length_log.jsonl`) was 3.78 before TRAIN_HOLD (p = 0.735), 2.61 for TRAIN_HOLD on gemma (0.617) and "
                  "2.06-2.28 on qwen (0.515-0.561).", ""]
            L += md_table(["arm", "lab opened (open contexts)", "implied live p", "95% CI", "implied mean train length", "95% CI"], rows_i) + [""]
            summary["mid_illustration"] = {a: {"p": float(pt[j]), "len": 1 / (1 - float(pt[j]))} for j, a in enumerate(ARMS)}
    # real last-step flags of the closing-context events
    fresh_ids = strata_R.get("fresh", ([], None, None))[0]
    if len(fresh_ids):
        lastopen = closing_last_open(fresh_ids)
        L += [f"- CLOSING-context prompts quote each train's LAST logged step: for the 40 `orig` prompts that step was itself open by the "
              f"live gate in 0/40 cases (J-0724's own jsonl); for the {len(fresh_ids)} `fresh` prompts in this run: "
              f"{lastopen[0]}/{lastopen[1]} (a train can also end by repetition / ceiling / stall, so a last step can still be open).", ""]
    L += ["Reading guide: a live mid-train prompt quotes a step that was open by construction (a train continues only if the previous "
          "step was open, nodes/inner_monologue_node.py:4484), so OPEN contexts are the live-like ones; CLOSING contexts ask a "
          "different question (would the model re-open after a calm closer?). The live prompt also carries seed parts the lab omits "
          "(frontier questions, retraction ledger, symbol read-back, a recall snippet), so a remaining gap to the real next step is expected.", ""]

    # ── 6. channels + format + side effects (all valid rows, all draws) ──────────────────────────────────────
    L += ["## Result 6 -- how each arm opens, the intention FORMAT, and side effects (every valid call, all draws pooled)", ""]
    valid = [r for r in all_rows if r["ok"] and r["pass"] >= 1]
    rows_t = []
    fmt_summary = {}
    for arm in ARMS:
        rs = [r for r in valid if r["arm"] == arm]
        n = len(rs)
        if not n:
            continue
        u = sum(r["unresolved"] for r in rs)
        i_ = sum(bool(r["intention"]) for r in rs)
        only_u = sum(r["unresolved"] and not r["intention"] for r in rs)
        only_i = sum(bool(r["intention"]) and not r["unresolved"] for r in rs)
        both = sum(r["unresolved"] and bool(r["intention"]) for r in rs)
        only_q = sum(r["qmark"] and not r["unresolved"] and not r["intention"] for r in rs)
        act = sum(1 for r in rs if r["act_kind"] != "none")
        words = float(np.mean([len(r["thought"].split()) for r in rs]))
        trunc = sum(1 for r in rs if r["thought"] and r["thought"][-1] not in ".!?\"'”’…)")
        ints = [r["intention"] for r in rs if r["intention"]]
        kinds = Counter(intention_kind(s) for s in ints)
        fmt_summary[arm] = {"n": n, "n_intention": len(ints), "kinds": dict(kinds)}
        rows_t.append([f"`{arm}`", n, share_str(u, n), share_str(i_, n),
                       f"{only_u} / {only_i} / {both} / {only_q}", share_str(act, n), f"{words:.1f}", f"{trunc}/{n}"])
    L += md_table(["arm", "n", "unresolved", "intention set", "opened via: unresolved-only / intention-only / both / '?'-only",
                   "act != none", "mean words", "thought lacks terminal punctuation (possible truncation)"], rows_t) + [""]
    rows_t = []
    for arm in ARMS:
        if arm not in fmt_summary or not fmt_summary[arm]["n_intention"]:
            continue
        f_ = fmt_summary[arm]
        k = f_["kinds"]
        n_i = f_["n_intention"]
        fp = k.get("first_person", 0)
        rows_t.append([f"`{arm}`", n_i, share_str(fp, n_i), k.get("to_infinitive_fragment", 0), k.get("bare_imperative_fragment", 0)])
    L += ["Intention FORMAT (non-empty `intention` strings; first_person = starts with I / I'd / Let me / My / We, "
          "fragment = bare infinitive or bare imperative such as 'to reach the study' / 'sit by the fire for a moment'):", ""]
    L += md_table(["arm", "n intentions", "first-person share [Wilson 95%]", "to-infinitive fragments", "bare-imperative fragments"], rows_t) + [""]
    summary["intention_format"] = fmt_summary
    ex = defaultdict(list)
    for r in valid:
        if r["intention"] and intention_kind(r["intention"]) != "first_person" and len(ex[r["arm"]]) < 5:
            ex[r["arm"]].append(r["intention"])
    for arm in ARMS:
        if ex[arm]:
            L.append(f"- fragment examples, `{arm}`: " + "; ".join(f"'{s[:70]}'" for s in ex[arm]))
    L.append("")
    std_kinds = ["none", "observe", "move", "read", "write", "search", "recall", "letter", "world"]
    rows_t = []
    for arm in ARMS:
        rs = [r for r in valid if r["arm"] == arm]
        if not rs:
            continue
        c = Counter(r["act_kind"] if r["act_kind"] in std_kinds else "other" for r in rs)
        rows_t.append([f"`{arm}`", len(rs)] + [f"{c.get(k, 0) / len(rs):.3f}" for k in std_kinds + ["other"]])
    L += ["Act-kind shares (the schema's `act.kind`, every valid call; `none` = no deed set -- a side effect of the wording, "
          "not what the gate measures):", ""]
    L += md_table(["arm", "n"] + std_kinds + ["other"], rows_t) + [""]

    # ── 7. isolation / run summary ────────────────────────────────────────────────────────────────────────────
    rs_path = SCRATCH / "J-0791_run_summary.json"
    L += ["## Isolation and gate record", ""]
    if rs_path.exists():
        rs_ = json.loads(rs_path.read_text(encoding="utf-8"))
        L += [f"- run summary (`J-0791_run_summary.json`, written by the batch process at exit): stop_reason = {rs_.get('stop_reason')!r}; "
              f"units done {rs_.get('units_done_total')}/{rs_.get('units_planned')}; wall {rs_.get('wall_s')} s; counters {rs_.get('counters')}",
              f"- write attempts under live data (audit hook, C:\\Nascence\\data or \\docs): **{rs_.get('live_write_attempts')}**; "
              f"elsewhere under C:\\Nascence: {rs_.get('tree_write_attempts')}; worktree data\\ writes: {len(rs_.get('worktree_data_writes', []))}; "
              f"sqlite connects: {len(rs_.get('sqlite_connects', []))}; core.*/nodes.* modules outside the worktree: {rs_.get('module_files_outside_worktree')}",
              f"- live-file fingerprint (md5 of position/room_state/life_state, size+mtime of judge_panel_log / llm_latency / llm_calls / "
              f"thought_station_log / nascence.log / nascence.db, 5 canary row counts) identical before/after: **{rs_.get('fingerprint_identical')}**",
              f"- hub: {rs_.get('hub_meta')}; arm system-prompt sha256[:12]: {rs_.get('arm_prompt_sha256_12')}", ""]
    else:
        L += ["- `J-0791_run_summary.json` not present yet (the batch process writes it at exit).", ""]

    # ── write ─────────────────────────────────────────────────────────────────────────────────────────────────
    text = "\n".join(L)
    print(text)
    if not a.no_write:
        Path(a.out_md).write_text(text, encoding="utf-8")
        Path(a.out_json).write_text(json.dumps({"summary": summary, "per_draw": per_draw_summary}, indent=1, ensure_ascii=False, default=str),
                                    encoding="utf-8")
        if (SCRATCH / "J-0791_mid_events.json").exists() and (SCRATCH / "J-0791_fresh_events.json").exists():
            ev_doc = {"note": "The exact prompts (fresh = closing-context recipe, mid = open-context replay with the real logged next step) "
                              "used by scripts/train_lab_wording_ab_replicate_J-0791_2026-09-08.py on 2026-09-22; the 'orig' 40 are "
                              "parsed from docs/lab/train_model_ab_gemma_vs_qwen_2026-09-08.md. Set membership: fresh1..6 = fresh[i::6], "
                              "mid1..4 = mid[i::4].",
                      "fresh": json.loads((SCRATCH / "J-0791_fresh_events.json").read_text(encoding="utf-8"))["events"],
                      "mid": json.loads((SCRATCH / "J-0791_mid_events.json").read_text(encoding="utf-8"))["events"]}
            _events_doc.write_text(json.dumps(ev_doc, ensure_ascii=False), encoding="utf-8")
        rows_out = [r for r in load_jsonl(Path(a.results))]
        sz = sum(len(json.dumps(r, ensure_ascii=False)) for r in rows_out)
        if sz < 2_000_000:
            with open(a.out_jsonl, "w", encoding="utf-8") as f:
                for r in rows_out:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\n[analysis] wrote {a.out_md} / {a.out_json} / jsonl copy ({'yes' if sz < 2_000_000 else 'NO, too large'})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

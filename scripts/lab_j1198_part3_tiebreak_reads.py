"""J-1198 Part 3: read the walk-back replay's SECOND-call TIEBREAK votes against D-0213's own defeater.

D-0213's defeater (quoted from the ruling): "Revisit if walking back the second-call fallback reintroduces
TIEBREAK's own unreliable-vote problem into real merge verdicts at meaningful scale -- e.g. a future replay shows the
second call's own verdict distribution swinging wildly with prompt-order/model choice the same way the original
single-call TIEBREAK vote did before the fallback existed."

INPUT: the replay's own side files (written by scripts/lab_j1198_walkback_replay.py in SCRATCH):
  lab_j1198_calls.jsonl  every rule_detail() call: unit, first/second, the EXACT user prompt, v1/v2/verdict/how/why3
  lab_j1198_units.jsonl  every finished unit (its final attempt number, its record)
  (and, if the main replay held fewer tiebreak-decided second calls than the brief's 24, the *_harvest files written by
   `lab_j1198_walkback_replay.py --harvest`: extra units run only to find more such prompts, never in the tallies)
WHAT IT MEASURES (hub calls go to TIEBREAK granite3.1-moe:3b, Ramses :11437, one request at a time, timeout 300 s,
rule-4 retry; these are Part 3 evidence, NOT part of the replay's own tallies):
  (b)  for the second-call cases decided by TIEBREAK: the True/False split, which judge TIEBREAK sided with, and (b2)
       whether the vote tracks content: TIEBREAK asked the SAME second-call question on the cases where JUDGE_1 and
       JUDGE_2 AGREED (a unanimous two-family panel is the only ground-truth-ish signal in this data), and (b3) on the
       script's own known-answer control prompts (the two that reach the second call);
  (c)  same-input consistency: every tiebreak-decided second-call prompt re-asked TWICE more, identical prompt;
  (d)  order check: the same prompts re-asked with the JSON key order reversed (why before the bool): d1 = the pure
       key-order swap (the schema line only), d2 = the swap plus one clause naming the order (J-0910's construction:
       "the JSON field order and the final instruction naming that order").
PRE-REGISTERED READING RULE (written before any Part 3 re-ask had been made, when only the first ~8 replay units existed
-- so the author had already seen that the very first tiebreak-decided second call was False, and no more; thresholds are
this job's own round numbers anchored on the brief's J-0916 reference points (95/70), the ruling gives none, so the raw
numbers are always printed next to the verdict): the defeater FIRES if TIEBREAK-decided
second-call verdicts are a meaningful share of the replay's merge statuses (>= 25 percent of replayed events) AND at
least one unreliability signal holds:  S1 order swing: a reversed-order re-ask flips >= 30 percent of verdicts or moves
the True share by >= 30 points;  S2 repeatability: same-input repeat agreement < 80 percent (J-0916: bool_first 95,
why_first 70);  S3 near-constant default: the True share is >= 90 percent or <= 10 percent AND the vote does not track
the unanimous-panel verdicts (b2 accuracy < 70 percent).

  python -u scripts/lab_j1198_part3_tiebreak_reads.py [--max-cases N] [--append-report] [--dry] [--follow]
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import lab_j1198_walkback_replay as R   # noqa: E402  (installs the write audit, redirects, rule-4 wrappers)
from core import judge_panel as jp      # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--max-cases", type=int, default=60)
ap.add_argument("--append-report", action="store_true")
ap.add_argument("--dry", action="store_true", help="select + describe the cases, make no hub calls")
ap.add_argument("--min-cases", type=int, default=0, help="exit 4 without calls if fewer tiebreak-decided cases exist")
ap.add_argument("--follow", action="store_true", help="detached mode: keep going while the replay adds cases, finish when it is done")
ap.add_argument("--budget-min", type=float, default=0, help="stop making calls after this many minutes (resumable: the next pass continues)")
ARGS = ap.parse_args()

SCRATCH = R.SCRATCH
T_PASS = time.time()
P3_ROWS = SCRATCH / "lab_j1198_part3_calls.jsonl"
P3_SUMMARY = SCRATCH / "lab_j1198_part3_summary.json"
REPORT_STEM = "train_split_merge_step2_replay_2026-09-22_walkback"
LAB_DIR = ROOT / "docs" / "lab"

# ---------------------------------------------------------------------------------- prompts (AST-extracted)
SRC = (ROOT / "scripts" / "train_state_invitro.py").read_text(encoding="utf-8")
_CONST = {}
for node in ast.parse(SRC).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
            and node.targets[0].id in ("_SCOPE_SYSTEM", "_DISPROVE_SYSTEM", "_CONTROL_CASES"):
        _CONST[node.targets[0].id] = ast.literal_eval(node.value)
SCOPE = _CONST["_SCOPE_SYSTEM"]
_TAIL_BOOL_FIRST = ('Output ONLY this JSON: {"scope_only": true|false, "why": "the narrower claim the support '
                    'actually earns, or a brief reason none exists, <=15 words"}')
assert SCOPE.count(_TAIL_BOOL_FIRST) == 1 and SCOPE.endswith(_TAIL_BOOL_FIRST), "_SCOPE_SYSTEM's schema tail moved"
_PREFIX = SCOPE[: -len(_TAIL_BOOL_FIRST)]
WHY_FIRST = _PREFIX + ('Output ONLY this JSON: {"why": "the narrower claim the support actually earns, or a brief '
                       'reason none exists, <=15 words", "scope_only": true|false}')
WHY_FIRST_NAMED = _PREFIX + ('Give your reasoning in "why" FIRST, then decide "scope_only" from it. Output ONLY this '
                             'JSON, keys in this order: {"why": "the narrower claim the support actually earns, or a '
                             'brief reason none exists, <=15 words", "scope_only": true|false}')
assert WHY_FIRST[: len(_PREFIX)] == SCOPE[: len(_PREFIX)] == WHY_FIRST_NAMED[: len(_PREFIX)]   # only the tail differs
ARMS = {"bool_first": SCOPE, "why_first_d1": WHY_FIRST, "why_first_named_d2": WHY_FIRST_NAMED}


# ---------------------------------------------------------------------------------- data
def load_jsonl(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def control_expectation(user: str):
    """(label, expected scope_only) for a control prompt, from the script's own _CONTROL_CASES designations."""
    for cc in _CONST["_CONTROL_CASES"]:
        if user.startswith("CLAIM: " + cc["claim"][:400]):
            if cc.get("expect_status") == "held_within_scope":
                return cc["label"], True
            if cc.get("expect_objection") is True:
                return cc["label"], False          # objected = the first call objected AND the second found no narrower claim
            return cc["label"], None
    return "unknown", None


def select_cases():
    """(units_main, rec_by_idx_main, second[with phase unit|harvest], ctrl second calls (deduped, latest first-seen))."""
    units = load_jsonl(R.UNITS_PATH)
    hunits = load_jsonl(R.UNITS_HARVEST)
    fin = {("unit", u["idx"]): u["attempt"] for u in units}
    fin.update({("harvest", u["idx"]): u["attempt"] for u in hunits})
    rec_by_idx = {u["idx"]: u["record"] for u in units}
    calls = load_jsonl(R.CALLS_PATH) + load_jsonl(R.CALLS_HARVEST)
    second = [c for c in calls if c.get("phase") in ("unit", "harvest") and c.get("call") == "second"
              and (c["phase"], c.get("unit")) in fin and c.get("attempt") == fin[(c["phase"], c["unit"])]]
    ctrl, seen = [], set()
    for c in load_jsonl(R.CALLS_PATH):
        if c.get("phase") == "control" and c.get("call") == "second":
            key = hashlib.sha1(c["user"].encode("utf-8")).hexdigest()[:10]
            if key not in seen:
                seen.add(key)
                label, exp = control_expectation(c["user"])
                ctrl.append(dict(c, case=f"ctrl_{label}", expected=exp))
    return units, rec_by_idx, second, ctrl


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 3) + 0.0, round(min(1.0, c + h), 3) + 0.0)


def pct(k, n):
    return "n/a" if not n else f"{100.0 * k / n:.1f}%"


# ---------------------------------------------------------------------------------- hub calls
async def ask_tiebreak(session, system: str, user: str):
    R.CUR.update(unit="part3", phase="part3", attempt=1, persistent=set())
    v, why, err, el = await R._ask_lab(session, jp.TIEBREAK, system, user, "scope_only", timeout=300, num_predict=200)
    failed = bool(R.CUR["persistent"])
    return v, why, err, el, failed


def load_done_rows() -> dict:
    done = {}
    for r in load_jsonl(P3_ROWS):
        done[(r["group"], r["case"], r["arm"], r["draw"])] = r
    return done


def _shas(t: dict):
    return (hashlib.sha1(t["user"].encode("utf-8")).hexdigest()[:10],
            hashlib.sha1(ARMS[t["arm"]].encode("utf-8")).hexdigest()[:10])


def task_done(t: dict, done: dict) -> bool:
    prev = done.get((t["group"], t["case"], t["arm"], t["draw"]))
    u_sha, s_sha = _shas(t)
    return bool(prev is not None and prev.get("user_sha") == u_sha and prev.get("sys_sha") == s_sha
                and not prev.get("infra_failed"))


async def run_calls(tasks: list, done: dict) -> None:
    """tasks: list of dicts {group, case, arm, draw, user}. Resumable; sequential (concurrency 1 on TIEBREAK)."""
    import aiohttp
    t_last = time.time()
    async with aiohttp.ClientSession() as session:
        for i, t in enumerate(tasks, 1):
            if task_done(t, done):
                continue                     # resume: finished with this exact prompt pair
            if R.STOP["flag"]:
                break
            if ARGS.budget_min and (time.time() - T_PASS) > ARGS.budget_min * 60:
                print(f"[part3] budget of {ARGS.budget_min} min reached at call {i}/{len(tasks)}: stopping this pass", flush=True)
                break
            u_sha, s_sha = _shas(t)
            v, why, err, el, failed = await ask_tiebreak(session, ARMS[t["arm"]], t["user"])
            row = {"group": t["group"], "case": t["case"], "arm": t["arm"], "draw": t["draw"], "v": v, "why": why,
                   "err": err, "elapsed": el, "infra_failed": failed, "user_sha": u_sha, "sys_sha": s_sha,
                   "ts": time.time()}
            R._append_jsonl(P3_ROWS, row)
            done[(t["group"], t["case"], t["arm"], t["draw"])] = row
            if time.time() - t_last > 600:
                t_last = time.time()
                R.progress("part3", len(done), len(tasks), f"{i}/{len(tasks)} calls in this pass")


# ---------------------------------------------------------------------------------- analysis
def analyse(units, rec_by_idx, second, ctrl, done) -> dict:
    n_units = len(rec_by_idx)
    main2 = [c for c in second if c["phase"] == "unit"]
    tb_main = [c for c in main2 if c["res"]["how"] == "tiebreak"]
    tb_pool = [c for c in second if c["res"]["how"] == "tiebreak"][: ARGS.max_cases]   # main + harvest: the re-asked cases
    ag_pool = [c for c in second if c["res"]["how"] == "agreed"]
    ag_main = [c for c in main2 if c["res"]["how"] == "agreed"]
    other = Counter(c["res"]["how"] for c in main2 if c["res"]["how"] not in ("tiebreak", "agreed"))
    out = {"n_units": n_units, "n_second_calls": len(main2), "n_tiebreak": len(tb_main), "n_agreed": len(ag_main),
           "n_second_other": dict(other),
           "n_tiebreak_cases_reasked": len(tb_pool),
           "n_tiebreak_cases_from_harvest": sum(1 for c in tb_pool if c["phase"] == "harvest")}

    # (b) split of the MAIN replay's own tiebreak votes
    tb_true = sum(1 for c in tb_main if c["res"]["verdict"] is True)
    tb_false = sum(1 for c in tb_main if c["res"]["verdict"] is False)
    ag_true = sum(1 for c in ag_main if c["res"]["verdict"] is True)
    ag_false = sum(1 for c in ag_main if c["res"]["verdict"] is False)
    orient = Counter((c["res"]["v1"], c["res"]["v2"]) for c in tb_main)
    sides_j1 = sum(1 for c in tb_main if c["res"]["verdict"] == c["res"]["v1"])
    sides_j2 = sum(1 for c in tb_main if c["res"]["verdict"] == c["res"]["v2"])
    out["b_split"] = {
        "tiebreak_true": tb_true, "tiebreak_false": tb_false, "tiebreak_true_ci95": wilson(tb_true, len(tb_main)),
        "agreed_true": ag_true, "agreed_false": ag_false, "agreed_true_ci95": wilson(ag_true, len(ag_main)),
        "split_orientation_(v1,v2)": {str(k): v for k, v in orient.items()},
        "tiebreak_sides_with_JUDGE_1": sides_j1, "tiebreak_sides_with_JUDGE_2": sides_j2,
        "share_of_all_replayed_events_decided_by_second_call_tiebreak": round(len(tb_main) / n_units, 3) if n_units else None}

    def votes(group, arm, cases):
        return {c: [done[k]["v"] for k in sorted(k for k in done if k[0] == group and k[1] == c and k[2] == arm and not done[k]["infra_failed"])]
                for c in cases}

    cases = [(c["phase"], c["unit"]) for c in tb_pool]
    cid = {(c["phase"], c["unit"]): c["unit"] for c in tb_pool}          # the Part 3 row key uses the unit id
    orig = {(c["phase"], c["unit"]): c["res"]["verdict"] for c in tb_pool}
    ids = [cid[k] for k in cases]
    # (c) same-input consistency
    rep = votes("tb_reask", "bool_first", ids)
    pairs_rr, agree_rr = 0, 0
    o1 = o2 = n_o1 = n_o2 = 0
    unanimous = n_unan = 0
    n_none = 0
    for k in cases:
        vs = rep.get(cid[k], [])
        n_none += sum(1 for v in vs if v is None)
        if len(vs) >= 2 and vs[0] is not None and vs[1] is not None:
            pairs_rr += 1
            agree_rr += int(vs[0] == vs[1])
            if orig[k] is not None:
                n_unan += 1
                unanimous += int(orig[k] == vs[0] == vs[1])
        for j, v in enumerate(vs[:2]):
            if v is not None and orig[k] is not None:
                if j == 0:
                    n_o1 += 1
                    o1 += int(v == orig[k])
                else:
                    n_o2 += 1
                    o2 += int(v == orig[k])
    reask_true = [v for k in cases for v in rep.get(cid[k], []) if v is True]
    reask_all = [v for k in cases for v in rep.get(cid[k], []) if v is not None]
    out["c_consistency"] = {
        "n_cases_reasked": sum(1 for k in cases if len(rep.get(cid[k], [])) >= 2), "n_none_draws": n_none,
        "repeat_to_repeat_pairs": pairs_rr, "repeat_to_repeat_agree": agree_rr,
        "repeat_to_repeat_rate": round(agree_rr / pairs_rr, 3) if pairs_rr else None,
        "repeat_to_repeat_ci95": wilson(agree_rr, pairs_rr),
        "reask1_equals_original": [o1, n_o1], "reask2_equals_original": [o2, n_o2],
        "all_three_equal": [unanimous, n_unan],
        "true_share_original": round(sum(1 for k in cases if orig[k] is True) / len(cases), 3) if cases else None,
        "true_share_reasks": round(len(reask_true) / len(reask_all), 3) if reask_all else None}

    # (d) order check
    d = {}
    for arm in ("why_first_d1", "why_first_named_d2"):
        vs = votes("tb_reask", arm, ids)
        n = t = flips_tf = flips_ft = same = nn = 0
        for k in cases:
            v = (vs.get(cid[k]) or [None])[0]
            if v is None:
                nn += 1
                continue
            n += 1
            t += int(v is True)
            o = orig[k]
            if o is None:
                continue
            if v == o:
                same += 1
            elif o is True and v is False:
                flips_tf += 1
            elif o is False and v is True:
                flips_ft += 1
        d[arm] = {"n": n, "n_none": nn, "true": t, "true_share": round(t / n, 3) if n else None,
                  "same_as_original": same, "flip_True_to_False": flips_tf, "flip_False_to_True": flips_ft,
                  "flip_rate": round((flips_tf + flips_ft) / n, 3) if n else None}
    out["d_order"] = d

    # (b2) TIEBREAK on the panel-agreed second-call prompts (bool_first = the live wording)
    tv = votes("agreed_reask", "bool_first", [c["unit"] for c in ag_pool])
    right = n = t_true = 0
    conf = Counter()
    for c in ag_pool:
        v = (tv.get(c["unit"]) or [None])[0]
        if v is None:
            continue
        n += 1
        t_true += int(v is True)
        right += int(v == c["res"]["verdict"])
        conf[(c["res"]["verdict"], v)] += 1
    n_panel_true = sum(1 for c in ag_pool if c["res"]["verdict"] is True and (tv.get(c["unit"]) or [None])[0] is not None)
    n_panel_true_ok = conf.get((True, True), 0)
    out["b2_tiebreak_vs_unanimous_panel"] = {
        "n": n, "tiebreak_agrees_with_panel": right, "accuracy": round(right / n, 3) if n else None,
        "accuracy_ci95": wilson(right, n), "tiebreak_true_share": round(t_true / n, 3) if n else None,
        "on_panel_unanimous_True": [n_panel_true_ok, n_panel_true],
        "on_panel_unanimous_False": [conf.get((False, False), 0), n - n_panel_true],
        "confusion_(panel,tiebreak)": {str(k): v for k, v in conf.items()}}

    # (b3) the script's own known-answer control prompts that reach the second call
    ctrl_rows = []
    for c in ctrl:
        cv = votes("ctrl_reask", "bool_first", [c["case"]]).get(c["case"], [])
        dv = votes("ctrl_reask", "why_first_d1", [c["case"]]).get(c["case"], [])
        ctrl_rows.append({"case": c["case"], "expected_scope_only": c["expected"],
                          "panel": {k: c["res"][k] for k in ("v1", "v2", "verdict", "how")},
                          "tiebreak_bool_first": cv, "tiebreak_why_first_d1": dv})
    out["b3_controls"] = ctrl_rows

    # (a)/(e) D-0181's bar on the replay's own distribution
    recs = list(rec_by_idx.values())
    cnt = Counter(r["disprove_status"] for r in recs)
    nn = len(recs) or 1
    shares = {k: round(v / nn, 3) for k, v in cnt.items()}
    out["a_status_shares"] = {"counts": dict(cnt), "shares": shares, "n": len(recs)}
    out["e_d0181_bar"] = {"max_single_status_share": max(shares.values()) if shares else None,
                          "any_single_status_over_90pct": any(v > 0.9 for v in shares.values()),
                          "held_within_scope_share": shares.get("held_within_scope", 0.0),
                          "held_within_scope_over_70pct": shares.get("held_within_scope", 0.0) > 0.7}

    # pre-registered rule
    meaningful = (len(tb_main) / n_units >= 0.25) if n_units else False
    d_best = max((d[a]["flip_rate"] or 0.0 for a in d), default=0.0)
    d_shift = max((abs((d[a]["true_share"] or 0.0) - (out["c_consistency"]["true_share_original"] or 0.0)) for a in d), default=0.0)
    s1 = bool(d_best >= 0.30 or d_shift >= 0.30)
    rr = out["c_consistency"]["repeat_to_repeat_rate"]
    s2 = bool(rr is not None and rr < 0.80)
    ts = out["c_consistency"]["true_share_original"]
    b2acc = out["b2_tiebreak_vs_unanimous_panel"]["accuracy"]
    s3 = bool(ts is not None and (ts >= 0.9 or ts <= 0.1) and (b2acc is None or b2acc < 0.70))
    out["preregistered_rule"] = {"meaningful_scale(>=25pct of events)": meaningful,
                                 "tiebreak_decided_events": f"{len(tb_main)}/{n_units}",
                                 "S1_order_swing": s1, "S1_max_flip_rate": d_best, "S1_max_true_share_shift": round(d_shift, 3),
                                 "S2_repeat_agreement_below_80pct": s2, "S3_constant_default_and_not_tracking": s3,
                                 "DEFEATER_FIRES(mechanical)": bool(meaningful and (s1 or s2 or s3))}
    return out


def render_md(o: dict) -> str:
    b, c, d, b2, a, e, rule = (o["b_split"], o["c_consistency"], o["d_order"], o["b2_tiebreak_vs_unanimous_panel"],
                                o["a_status_shares"], o["e_d0181_bar"], o["preregistered_rule"])
    L = ["## Part 3 — read against D-0213's own defeater (J-1198)", "",
         "Source: the replay's own per-call side file (every `rule_detail()` call with its exact prompt) plus extra "
         "TIEBREAK (granite3.1-moe:3b, Ramses :11437) calls made by `scripts/lab_j1198_part3_tiebreak_reads.py` "
         "(timeout 300 s, one request at a time, rule-4 retry; NOT part of the replay's own tallies). "
         f"Re-asked tiebreak-decided cases: {o['n_tiebreak_cases_reasked']} "
         f"({o['n_tiebreak_cases_reasked'] - o['n_tiebreak_cases_from_harvest']} from the main replay, "
         f"{o['n_tiebreak_cases_from_harvest']} from the extra `--harvest` units, which are in no tally).", "",
         f"**(a) Status shares (n={a['n']} units in the tallies):** counts {a['counts']}, shares {a['shares']}. "
         "F-1504 baseline (fallback in both calls): UNDETERMINED 62/80 = 77.5%, held_within_scope 15.0%, objected 6.2%, held 1.3%.", "",
         f"**(b) The second call's TIEBREAK-decided verdicts (main replay):** {o['n_tiebreak']} of the {o['n_second_calls']} second calls "
         f"({pct(o['n_tiebreak'], o['n_second_calls'])}) and {pct(o['n_tiebreak'], o['n_units'])} of all replayed events were "
         f"decided by TIEBREAK; scope_only=True (-> held_within_scope) {b['tiebreak_true']}, False (-> objected) "
         f"{b['tiebreak_false']} (True share {pct(b['tiebreak_true'], o['n_tiebreak'])}, 95% CI {b['tiebreak_true_ci95']}). "
         f"For comparison the second calls the two judge families AGREED on: True {b['agreed_true']}, False {b['agreed_false']} "
         f"(True share {pct(b['agreed_true'], o['n_agreed'])}, CI {b['agreed_true_ci95']}). Split orientation (JUDGE_1, JUDGE_2) "
         f"on the tiebreak cases: {b['split_orientation_(v1,v2)']}; TIEBREAK sided with JUDGE_1 {b['tiebreak_sides_with_JUDGE_1']}x and "
         f"JUDGE_2 {b['tiebreak_sides_with_JUDGE_2']}x.", "",
         f"**(b2) Does the vote track content? TIEBREAK on the second-call prompts the panel AGREED on** (a unanimous two-family "
         f"panel as the only ground-truth-ish signal): n={b2['n']}, TIEBREAK matched the panel {b2['tiebreak_agrees_with_panel']}/{b2['n']} "
         f"= {pct(b2['tiebreak_agrees_with_panel'], b2['n'])} (CI {b2['accuracy_ci95']}); on the panel-unanimous-True prompts it said True "
         f"{b2['on_panel_unanimous_True'][0]}/{b2['on_panel_unanimous_True'][1]}, on the panel-unanimous-False prompts False "
         f"{b2['on_panel_unanimous_False'][0]}/{b2['on_panel_unanimous_False'][1]}; TIEBREAK's own True share {b2['tiebreak_true_share']}; "
         f"confusion (panel, tiebreak) {b2['confusion_(panel,tiebreak)']}.", ""]
    if o.get("b3_controls"):
        L.append("**(b3) The script's own known-answer control prompts that reach the second call** (expected scope_only from the "
                 "control design; the panel's own votes; TIEBREAK asked directly): " + "; ".join(
                     f"`{r['case']}` expected {r['expected_scope_only']}, panel {r['panel']}, TIEBREAK bool-first {r['tiebreak_bool_first']}, "
                     f"why-first {r['tiebreak_why_first_d1']}" for r in o["b3_controls"]) + ".")
        L.append("")
    L += [f"**(c) Same-input consistency** (each tiebreak-decided prompt re-asked twice more, identical prompt): "
          f"{c['n_cases_reasked']} cases re-asked; repeat-to-repeat agreement {c['repeat_to_repeat_agree']}/{c['repeat_to_repeat_pairs']} "
          f"= {pct(c['repeat_to_repeat_agree'], c['repeat_to_repeat_pairs'])} (CI {c['repeat_to_repeat_ci95']}) "
          f"[J-0916: bool_first 95%, why_first 70%, n=40 draws]; re-ask 1 equals the replay's vote {c['reask1_equals_original']}, "
          f"re-ask 2 {c['reask2_equals_original']}, all three equal {c['all_three_equal']}; True share original "
          f"{c['true_share_original']} vs re-asks {c['true_share_reasks']}; unparseable draws {c['n_none_draws']}.", "",
          "**(d) Order check** (same prompts, JSON key order reversed, why before the bool): "]
    for arm, v in d.items():
        L.append(f"`{arm}`: n={v['n']} valid, True share {v['true_share']} (original {c['true_share_original']}); "
                 f"same verdict as the original {v['same_as_original']}/{v['n']}; flips True->False {v['flip_True_to_False']}, "
                 f"False->True {v['flip_False_to_True']} (flip rate {v['flip_rate']}); unparseable or not yet asked {v['n_none']}.  ")
    L += ["", f"**(e) D-0181's bar on this distribution:** max single status share {e['max_single_status_share']} "
              f"(> 90%? {e['any_single_status_over_90pct']}); held_within_scope share {e['held_within_scope_share']} "
              f"(> 70%? {e['held_within_scope_over_70pct']}).", "",
          f"**Pre-registered reading rule (mechanical):** {rule}", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------------- main
def plan_tasks(tb: list, ag: list, ctrl: list) -> list:
    """Priority order (a budgeted pass stops early; the brief's REQUIRED parts come first): (c) two identical-prompt
    re-asks + (d1) the pure key-order swap for every tiebreak-decided case; then (b2) TIEBREAK on the panel-agreed
    prompts and (b3) the control prompts; then (d2), the swap plus a clause naming the order (J-0910's construction)."""
    tasks = []
    for c in tb:
        for draw in (1, 2):
            tasks.append({"group": "tb_reask", "case": c["unit"], "arm": "bool_first", "draw": draw, "user": c["user"]})
        tasks.append({"group": "tb_reask", "case": c["unit"], "arm": "why_first_d1", "draw": 1, "user": c["user"]})
    for c in ag:
        tasks.append({"group": "agreed_reask", "case": c["unit"], "arm": "bool_first", "draw": 1, "user": c["user"]})
    for c in ctrl:
        for arm, draw in (("bool_first", 1), ("bool_first", 2), ("why_first_d1", 1)):
            tasks.append({"group": "ctrl_reask", "case": c["case"], "arm": arm, "draw": draw, "user": c["user"]})
    for c in tb:
        tasks.append({"group": "tb_reask", "case": c["unit"], "arm": "why_first_named_d2", "draw": 1, "user": c["user"]})
    return tasks


def cases_now():
    units, rec_by_idx, second, ctrl = select_cases()
    tb = [c for c in second if c["res"]["how"] == "tiebreak"][: ARGS.max_cases]
    ag = [c for c in second if c["res"]["how"] == "agreed"]
    return units, rec_by_idx, second, tb, ag, ctrl


def finalize(units, rec_by_idx, second, ctrl, done) -> int:
    o = analyse(units, rec_by_idx, second, ctrl, done)
    o["hub_stats_this_process"] = {h: {k: (v if k != 'secs' else {'n': len(v)}) for k, v in s.items()} for h, s in R.STATS.items()}
    o["write_attempts_under_live_data"] = len(R.LIVE_WRITE_ATTEMPTS)
    P3_SUMMARY.write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
    md = render_md(o)
    print(md)
    if ARGS.append_report:
        rp = LAB_DIR / f"{REPORT_STEM}.md"
        if rp.exists():
            text = rp.read_text(encoding="utf-8")
            cut = text.find("\n\n## Part 3 — read against D-0213's own defeater (J-1198)")
            if cut >= 0:                      # idempotent: a re-run replaces the earlier Part 3 section
                text = text[:cut]
            rp.write_text(text.rstrip("\n") + "\n\n" + md + "\n", encoding="utf-8")
            print(f"[part3] appended to {rp}")
        LAB_DIR.mkdir(parents=True, exist_ok=True)
        with open(LAB_DIR / f"{REPORT_STEM}_part3.jsonl", "w", encoding="utf-8") as f:
            for r in load_jsonl(P3_ROWS):
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("[part3] write attempts under live data:", len(R.LIVE_WRITE_ATTEMPTS), flush=True)
    return 0


def follow() -> int:
    """Detached mode: keep making the pending TIEBREAK calls while the replay is still adding cases, and finish
    (analysis + outputs) once the replay's own summary file exists and nothing is pending."""
    global T_PASS
    if not asyncio.run(R.du_is_down()):
        R.progress("part3", 0, 0, "Du UP-or-UNKNOWN: refusing to send hub traffic")
        return 3
    done = load_done_rows()
    last_du = time.time()
    ARGS.budget_min = 10
    R.progress("part3-follow", len(done), 0, "following the replay; passes of 10 min")
    while True:
        units, rec_by_idx, second, tb, ag, ctrl = cases_now()
        tasks = plan_tasks(tb, ag, ctrl)
        pending = [t for t in tasks if not task_done(t, done)]
        if pending:
            R.progress("part3", len(tasks) - len(pending), len(tasks),
                       f"{len(pending)} pending TIEBREAK calls ({len(tb)} tiebreak cases, {len(ag)} agreed cases, {len(units)} units)")
            T_PASS = time.time()
            asyncio.run(run_calls(tasks, done))
        elif R.SUMMARY_PATH.exists():
            break
        else:
            time.sleep(60)
        if time.time() - last_du > 1800:
            last_du = time.time()
            if not asyncio.run(R.du_is_down()):
                time.sleep(60)
                if not asyncio.run(R.du_is_down()):
                    R.STOP["flag"] = "du up or unknown"
            R.progress("du-check", len(done), len(tasks), "DOWN" if not R.STOP["flag"] else "UP-or-UNKNOWN -> STOP")
        if R.STOP["flag"]:
            break
    units, rec_by_idx, second, tb, ag, ctrl = cases_now()
    R.progress("part3-done", len(done), len(plan_tasks(tb, ag, ctrl)), f"infra_errors_TIEBREAK={R.STATS['TIEBREAK']['infra_errors']} stopped={R.STOP['flag']}")
    return finalize(units, rec_by_idx, second, ctrl, done)


def main() -> int:
    if ARGS.follow:
        return follow()
    units, rec_by_idx, second, tb, ag, ctrl = cases_now()
    print(f"[part3] units finished: {len(units)}; second calls: {len(second)} (tiebreak {len(tb)}, agreed {len(ag)}); control prompts {len(ctrl)}", flush=True)
    if len(tb) < ARGS.min_cases:
        print(f"[part3] only {len(tb)} tiebreak-decided cases (< --min-cases {ARGS.min_cases}): nothing done", flush=True)
        return 4
    tasks = plan_tasks(tb, ag, ctrl)
    print(f"[part3] {len(tasks)} TIEBREAK calls planned ({len(tb)} tiebreak-decided cases x 4 + {len(ag)} panel-agreed x 1 + {len(ctrl)} controls x 3)", flush=True)
    if ARGS.dry:
        return 0
    if not asyncio.run(R.du_is_down()):
        R.progress("part3", 0, len(tasks), "Du UP-or-UNKNOWN: refusing to send hub traffic")
        return 3
    done = load_done_rows()
    R.progress("part3-start", len(done), len(tasks), f"{len(tb)} tiebreak cases, {len(ag)} agreed cases, {len(ctrl)} control prompts")
    t0 = time.time()
    asyncio.run(run_calls(tasks, done))
    R.progress("part3-done", len(done), len(tasks), f"wall={round((time.time() - t0) / 60, 1)}min infra_errors_TIEBREAK={R.STATS['TIEBREAK']['infra_errors']}")
    return finalize(units, rec_by_idx, second, ctrl, done)


if __name__ == "__main__":
    sys.exit(main())

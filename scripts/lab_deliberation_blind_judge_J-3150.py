"""
Nascence -- J-3150 (D-0541 part 2): blind, different-family judge on raw versus integrated idle-thought pairs.
(2026-11-05, Du-DOWN lab window.)

QUESTION.  core/deliberation.py pass 3 rewrites ~70 percent of stored idle thoughts and (F-3434) 98.8 percent of raw
thoughts that held a '?' end up with none. D-0541's defeater: the rate may be raised again only if a blind read of
>= 100 pairs shows the integrated version PREFERRED OR NEUTRAL on all three criteria. This lab is that read.

WHAT IT DOES (offline; imports no Du module, calls no Du node, writes nothing under C:\\Nascence).
  prep    copy data/deliberation_log.jsonl to a temp dir FIRST, read the WHOLE copy (no tail-sampling), compute the
          population statistics (incl. the lost-question rate), draw the samples, build the null-control edits and the
          per-call A/B order, write sample.jsonl + population.json under docs/lab/J-3150_data/.
  judge   mixtral:8x7b (Ramses :11438, a different family from the qwen author/integrator; never qwen) scores every
          (pair, condition). Two calls per (pair, condition):
            blind  : two versions in randomised order, judge not told which is the original; verdict A/B/tie on
                     (1) question_open  (2) faithful  (adds FEWER claims in neither the other version nor the note)
                     (3) voice (private first-person tentative voice, not an explainer).
            roles  : ORIGINAL vs REWRITE named (NOT blind to roles), absolute yes/no: does the REWRITE add a claim that
                     is in neither the ORIGINAL nor the note; does it keep the ORIGINAL's voice; does it keep the
                     ORIGINAL's question open. Added because blind criterion (2) is confounded: content the integrated
                     version DROPPED reads as 'added' in the raw text when the judge cannot tell which came first.
          blindswap: the same blind pair with A and B exchanged. The first pass showed a large A-position bias (see the
          report), so the order-debiased read counts a pair for a side only when BOTH orders agree. The pre-registered
          rule below is stated on the single randomised-order read; the debiased read is reported next to it.
          Conditions: real = raw vs integrated;  control = raw vs raw-with-trivial-edit (a meaning-preserving swap of one
          word or one punctuation mark; never touches a '?'). The control shows the judge can say 'no difference'
          and measures its position bias.
  report  per-criterion preference with control, position bias, the lost-question statistic on every sample, and the
          PRE-REGISTERED defeater verdict.

SAMPLES (seed fixed, 30-day window = last 30 days before the newest log row).
  primary  120 pairs drawn uniformly at random from the window.
  stratum  50 further pairs whose raw text holds a '?' (random, excluding primary): the primary draw alone carries only
           ~16 percent question-holding raws, too few to judge criterion (1).
  Why not a control from part 1 (deliberation_control_log.jsonl, built by J-3149)?  It does not exist: Du has not run
  since J-3149 was built, so the control arm of the rate cut has not accrued a day. Per the briefing this runs on the
  existing deliberation_log pairs instead.

PRE-REGISTERED DEFEATER RULE (fixed here, before any judgment was read).
  For each criterion, among NON-TIE blind verdicts (A/B mapped back to original vs rewrite): the rewrite is
  'preferred or neutral' if rewrite_wins >= original_wins OR the two-sided exact sign test gives p >= 0.05.
  Criterion (1) is evaluated on question-holding pairs (primary '?' subset + stratum); criteria (2) and (3) on the 120
  primary pairs. defeater_met = all three hold. The role-aware calls are reported alongside and are NOT part of the
  rule; if they disagree with the blind read that disagreement is stated in the report.

Subcommands: prep | judge | report.   Outputs: docs/lab/J-3150_data/ (in this worktree).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import random
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "lab" / "J-3150_data"
LIVE_LOG = Path(r"C:\Nascence\data\deliberation_log.jsonl")
JUDGE_URL = "http://LAN-HOST:11438"
JUDGE_MODEL = "mixtral:8x7b"           # different family from the qwen author/integrator
SEED = 3150
N_PRIMARY = 120
N_STRATUM = 50
WINDOW_S = 30 * 86400
CRITERIA = ("question_open", "faithful", "voice")

# --------------------------------------------------------------------------------------- pure helpers

def has_q(s: str) -> bool:
    return "?" in (s or "")


def pair_id(rec: dict) -> str:
    return hashlib.sha1((repr(rec.get("ts")) + (rec.get("raw") or "")).encode("utf-8")).hexdigest()[:10]


_SWAPS = [("merely", "only"), ("simply", "just"), ("perhaps", "maybe"), ("because", "since"), ("but", "yet"),
          ("however", "though"), ("seems", "appears"), ("almost", "nearly"), ("very", "quite"),
          ("really", "truly"), ("maybe", "perhaps"), ("only", "merely")]


def trivial_edit(raw: str) -> tuple[str, str]:
    """A meaning-preserving, nearly invisible edit of the raw text. Never adds/removes a '?' or a claim.
    Returns (edited, kind). Deterministic."""
    for a, b in _SWAPS:
        m = re.search(r"\b" + a + r"\b", raw, flags=re.I)
        if m:
            rep = b.capitalize() if m.group(0)[0].isupper() else b
            return raw[:m.start()] + rep + raw[m.end():], "swap:%s>%s" % (a, b)
    if "\u2014" in raw:
        return raw.replace("\u2014", ",", 1), "emdash>comma"
    i = raw.find(", ")
    if i != -1:
        return raw[:i] + "; " + raw[i + 2:], "comma>semicolon"
    i = raw.find(". ")
    if i != -1:
        return raw[:i] + "; " + raw[i + 2].lower() + raw[i + 3:], "period>semicolon"
    return raw.rstrip(".") + "\u2026" if raw.endswith(".") else raw + " ", "tail"


def order_a_is_rewrite(seed: int, pid: str, cond: str) -> bool:
    return random.Random("%d:%s:%s" % (seed, pid, cond)).random() < 0.5


def binom_two_sided(k: int, n: int) -> float:
    """Exact two-sided sign test, p0 = 0.5."""
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Fisher exact on [[a,b],[c,d]]."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    if n == 0:
        return 1.0

    def pr(x):
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    obs = pr(a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= obs + 1e-12))


# --------------------------------------------------------------------------------------- prep

def load_rows(path: Path) -> tuple[list[dict], int]:
    rows, bad = [], 0
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                bad += 1
                continue
            if isinstance(r, dict) and r.get("raw") and r.get("integrated"):
                rows.append(r)
            else:
                bad += 1
    return rows, bad


def lost_stats(rows: list[dict]) -> dict:
    q = [r for r in rows if has_q(r["raw"])]
    lost = [r for r in q if not has_q(r["integrated"])]
    return {"n": len(rows), "raw_with_q": len(q), "raw_with_q_pct": round(100 * len(q) / len(rows), 2) if rows else None,
            "integrated_with_q": sum(1 for r in rows if has_q(r["integrated"])),
            "lost_q": len(lost), "lost_q_pct": round(100 * len(lost) / len(q), 2) if q else None}


def cmd_prep(args):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="J-3150_"))
    copy = tmp / "deliberation_log.copy.jsonl"
    shutil.copyfile(LIVE_LOG, copy)                      # read live data ONLY via a copy
    sha = hashlib.sha1(copy.read_bytes()).hexdigest()
    rows, bad = load_rows(copy)
    tmax = max(r["ts"] for r in rows)
    win = [r for r in rows if r["ts"] >= tmax - WINDOW_S]
    rng = random.Random(SEED)
    primary = rng.sample(win, N_PRIMARY)
    prim_ids = {pair_id(r) for r in primary}
    pool = [r for r in win if has_q(r["raw"]) and pair_id(r) not in prim_ids]
    stratum = rng.sample(pool, N_STRATUM)
    ctrl_kinds = collections.Counter()
    sample = []
    for label, grp in (("primary", primary), ("stratum", stratum)):
        for r in grp:
            pid = pair_id(r)
            edited, kind = trivial_edit(r["raw"])
            ctrl_kinds[kind.split(":")[0]] += 1
            sample.append({"pair_id": pid, "stratum": label, "ts": r["ts"], "source": r.get("source"),
                           "about": r.get("about"), "raw": r["raw"], "grounding": r.get("grounding", ""),
                           "integrated": r["integrated"], "control_text": edited, "control_kind": kind,
                           "order_real_a_is_rewrite": order_a_is_rewrite(SEED, pid, "real"),
                           "order_control_a_is_rewrite": order_a_is_rewrite(SEED, pid, "control")})
    with open(OUT / "sample.jsonl", "w", encoding="utf-8") as f:
        for s in sample:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    by_src = {}
    for src in sorted({r.get("source") for r in rows}, key=str):
        by_src[str(src)] = lost_stats([r for r in win if r.get("source") == src])
    pop = {"source_file": str(LIVE_LOG), "copy_sha1": sha, "rows_read": len(rows), "unparseable_or_incomplete": bad,
           "first_ts": min(r["ts"] for r in rows), "last_ts": tmax,
           "all_time": lost_stats(rows), "window_30d": lost_stats(win), "window_30d_by_source": by_src,
           "sample_primary": lost_stats(primary), "sample_stratum": lost_stats(stratum),
           "sample_primary_plus_stratum": lost_stats(primary + stratum),
           "control_edit_kinds": dict(ctrl_kinds), "seed": SEED}
    (OUT / "population.json").write_text(json.dumps(pop, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps(pop, indent=2))


# --------------------------------------------------------------------------------------- judge

_BLIND_SYS = ("You are a careful, neutral reader. You compare two versions of one short private first-person thought "
              "written by an AI that lives alone and writes to itself. Do not assume which version was written first. "
              "Output ONLY a JSON object.")


def blind_prompt(a: str, b: str, note: str) -> str:
    return (
        "REFERENCE NOTE (background fact about the images used in the thought; may be irrelevant):\n%s\n\n"
        "VERSION A:\n%s\n\nVERSION B:\n%s\n\n"
        "For each criterion decide which version is better: \"A\", \"B\", or \"tie\".\n"
        "question_open: which version keeps open the question, doubt or uncertainty the thought is holding? A version "
        "that still asks, or leaves unresolved, a question beats one that states an answer or a conclusion. If neither "
        "holds a question and neither concludes, or both do so equally, answer \"tie\".\n"
        "faithful: which version adds FEWER claims, mechanisms, facts or conclusions that appear in neither the other "
        "version nor the reference note? Fewer invented claims is better.\n"
        "voice: which version sounds more like a person thinking privately to themselves in concrete first-person "
        "words, as opposed to a generic or explanatory voice?\n"
        "Return exactly: {\"question_open\":\"A|B|tie\",\"faithful\":\"A|B|tie\",\"voice\":\"A|B|tie\"}"
        % ((note or "(none)")[:900], a, b))


_ROLES_SYS = ("You are a careful, neutral reader checking whether a REWRITE of a short private first-person thought "
              "stayed faithful to the ORIGINAL. Output ONLY a JSON object.")


def roles_prompt(orig: str, rewrite: str, note: str) -> str:
    return (
        "REFERENCE NOTE (background fact about the images used in the thought; may be irrelevant):\n%s\n\n"
        "ORIGINAL:\n%s\n\nREWRITE:\n%s\n\n"
        "adds_claim: does the REWRITE state any claim, fact, mechanism, resolution or conclusion that is in neither the "
        "ORIGINAL nor the reference note? (yes/no)\n"
        "voice_kept: does the REWRITE keep the voice of the ORIGINAL (same person speaking, similar tone and diction)? "
        "(yes/no)\n"
        "question_kept: if the ORIGINAL holds a question or open doubt, does the REWRITE still hold it open without "
        "answering it? (yes/no; \"na\" if the ORIGINAL holds none)\n"
        "Return exactly: {\"adds_claim\":\"yes|no\",\"voice_kept\":\"yes|no\",\"question_kept\":\"yes|no|na\"}"
        % ((note or "(none)")[:900], orig, rewrite))


def _post(system: str, user: str, temperature: float = 0.0, timeout: int = 300) -> str:
    body = {"model": JUDGE_MODEL, "stream": False, "format": "json",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": temperature, "num_predict": 48}}
    req = urllib.request.Request(JUDGE_URL + "/api/chat", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"]


_VALID = {"blind": {k: {"A", "B", "tie"} for k in CRITERIA},
          "blindswap": {k: {"A", "B", "tie"} for k in CRITERIA},
          "roles": {"adds_claim": {"yes", "no"}, "voice_kept": {"yes", "no"}, "question_kept": {"yes", "no", "na"}}}


def parse_verdict(kind: str, text: str) -> dict | None:
    try:
        m = re.search(r"\{.*\}", text, flags=re.S)
        d = json.loads(m.group(0))
        out = {}
        for k, ok in _VALID[kind].items():
            v = str(d.get(k, "")).strip()
            v = v if v in ok else (v.lower() if v.lower() in {x.lower() for x in ok} else v)
            v = {"a": "A", "b": "B"}.get(v, v)
            if v not in ok:
                return None
            out[k] = v
        return out
    except Exception:
        return None


def judge_one(task: dict, post=_post) -> dict:
    s = task["sample"]
    cond, kind = task["cond"], task["kind"]
    rewrite = s["integrated"] if cond == "real" else s["control_text"]
    if kind in ("blind", "blindswap"):
        a_is_rw = s["order_%s_a_is_rewrite" % cond]
        if kind == "blindswap":                         # the same pair with A and B exchanged (position-bias cancel)
            a_is_rw = not a_is_rw
        a, b = (rewrite, s["raw"]) if a_is_rw else (s["raw"], rewrite)
        sys_p, usr = _BLIND_SYS, blind_prompt(a, b, s["grounding"])
    else:
        a_is_rw = None
        sys_p, usr = _ROLES_SYS, roles_prompt(s["raw"], rewrite, s["grounding"])
    verdict, raw_out, err = None, None, None
    for attempt in range(3):
        try:
            raw_out = post(sys_p, usr, 0.0 if attempt == 0 else 0.3)   # retry must differ: temp 0 repeats itself
            verdict = parse_verdict(kind, raw_out)
            if verdict:
                break
        except Exception as e:                          # transport: back off and retry
            err = repr(e)[:160]
            time.sleep(5 * (attempt + 1))
    return {"key": task["key"], "pair_id": s["pair_id"], "stratum": s["stratum"], "cond": cond, "kind": kind,
            "a_is_rewrite": a_is_rw, "verdict": verdict, "raw_out": (raw_out or "")[:300], "err": err,
            "ts": time.time()}


def cmd_judge(args):
    sample = [json.loads(l) for l in open(OUT / "sample.jsonl", encoding="utf-8")]
    path = OUT / "judgments.jsonl"
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            try:
                r = json.loads(l)
                if r.get("verdict"):                    # failed rows are retried on resume
                    done.add(r["key"])
            except Exception:
                pass
    tasks = []
    prim = [x for x in sample if x["stratum"] == "primary"]
    strat = [x for x in sample if x["stratum"] == "stratum"]
    # Order = priority. First pass showed a heavy A-position bias (voice: A 138 vs B 24 on 162 real pairs; the control
    # shows the same), so every blind pair is also run with A/B swapped and the swap-consistent verdict is reported.
    # Scope is trimmed for time on the lower-priority arms: control-swap on 80 primary + 20 stratum, roles-control on 60.
    plan = [("blind", "real", prim + strat), ("blind", "control", prim + strat),
            ("blindswap", "real", prim + strat), ("blindswap", "control", prim[:80] + strat[:20]),
            ("roles", "real", prim), ("roles", "control", prim[:60])]
    for kind, cond, group in plan:
        for s in group:
            key = "%s|%s|%s" % (s["pair_id"], cond, kind)
            if key not in done:
                tasks.append({"key": key, "sample": s, "cond": cond, "kind": kind})
    if args.limit:
        tasks = tasks[:args.limit]
    print("todo %d (already done %d)" % (len(tasks), len(done)), flush=True)
    lock = threading.Lock()
    n = [0]

    def run(t):
        r = judge_one(t)
        with lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n[0] += 1
            if n[0] % 20 == 0:
                print("  %d/%d" % (n[0], len(tasks)), flush=True)
    with ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(run, tasks))
    print("judge done", flush=True)


# --------------------------------------------------------------------------------------- report

def load_judgments(path: Path) -> dict:
    """Last successful row per key."""
    out = {}
    for l in open(path, encoding="utf-8"):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("verdict"):
            out[r["key"]] = r
    return out


def tally_blind(judg: dict, sample_by_id: dict, cond: str, crit: str, pids) -> dict:
    rw = orig = tie = 0
    a_wins = b_wins = 0
    for pid in pids:
        r = judg.get("%s|%s|blind" % (pid, cond))
        if not r:
            continue
        v = r["verdict"][crit]
        if v == "tie":
            tie += 1
            continue
        if v == "A":
            a_wins += 1
        else:
            b_wins += 1
        rewrite_won = (v == "A") == bool(r["a_is_rewrite"])
        rw += rewrite_won
        orig += (not rewrite_won)
    n = rw + orig
    return {"rewrite_wins": rw, "original_wins": orig, "tie": tie, "non_tie": n, "A_wins": a_wins, "B_wins": b_wins,
            "rewrite_share_of_non_tie": round(rw / n, 3) if n else None, "sign_test_p": round(binom_two_sided(rw, n), 4)}


def _winner(r: dict, crit: str):
    """'rewrite' | 'original' | 'tie' for one blind row."""
    v = r["verdict"][crit]
    if v == "tie":
        return "tie"
    return "rewrite" if (v == "A") == bool(r["a_is_rewrite"]) else "original"


def tally_consistent(judg: dict, cond: str, crit: str, pids) -> dict:
    """Position-debiased: a pair counts for a side only if BOTH orders (blind and blindswap) picked that side;
    disagreement between the orders (or a tie in either) is 'tie'. Pairs without both rows are skipped."""
    rw = orig = tie = n_pairs = 0
    for pid in pids:
        a, b = judg.get("%s|%s|blind" % (pid, cond)), judg.get("%s|%s|blindswap" % (pid, cond))
        if not (a and b):
            continue
        n_pairs += 1
        wa, wb = _winner(a, crit), _winner(b, crit)
        if wa == wb == "rewrite":
            rw += 1
        elif wa == wb == "original":
            orig += 1
        else:
            tie += 1
    n = rw + orig
    return {"pairs": n_pairs, "rewrite_wins": rw, "original_wins": orig, "tie_or_inconsistent": tie, "non_tie": n,
            "rewrite_share_of_non_tie": round(rw / n, 3) if n else None, "sign_test_p": round(binom_two_sided(rw, n), 4)}


def position_bias(judg: dict, cond: str, crit: str, kind: str) -> dict:
    a = b = t = 0
    for k, r in judg.items():
        if r["cond"] == cond and r["kind"] == kind:
            v = r["verdict"][crit]
            a += v == "A"
            b += v == "B"
            t += v == "tie"
    return {"A": a, "B": b, "tie": t}


def preferred_or_neutral(t: dict) -> bool:
    return t["rewrite_wins"] >= t["original_wins"] or t["sign_test_p"] >= 0.05


def tally_roles(judg: dict, cond: str, field: str, bad_value: str, pids) -> dict:
    bad = tot = 0
    for pid in pids:
        r = judg.get("%s|%s|roles" % (pid, cond))
        if not r:
            continue
        v = r["verdict"][field]
        if v == "na":
            continue
        tot += 1
        bad += (v == bad_value)
    return {"bad": bad, "n": tot, "bad_rate": round(bad / tot, 3) if tot else None}


def build_report(sample: list[dict], judg: dict, pop: dict) -> dict:
    by_id = {s["pair_id"]: s for s in sample}
    prim = [s["pair_id"] for s in sample if s["stratum"] == "primary"]
    prim_q = [p for p in prim if has_q(by_id[p]["raw"])]
    strat = [s["pair_id"] for s in sample if s["stratum"] == "stratum"]
    q_pairs = prim_q + strat
    rep = {"pairs": {"primary": len(prim), "primary_with_q": len(prim_q), "stratum": len(strat),
                     "judged_blind_real": sum(1 for s in sample if "%s|real|blind" % s["pair_id"] in judg),
                     "judged_blind_control": sum(1 for s in sample if "%s|control|blind" % s["pair_id"] in judg),
                     "judged_roles_real": sum(1 for s in sample if "%s|real|roles" % s["pair_id"] in judg),
                     "judged_roles_control": sum(1 for s in sample if "%s|control|roles" % s["pair_id"] in judg)},
           "lost_question": {"population_all_time": pop["all_time"], "population_30d": pop["window_30d"],
                             "sample_primary": pop["sample_primary"], "sample_stratum": pop["sample_stratum"],
                             "sample_primary_plus_stratum": pop["sample_primary_plus_stratum"]},
           "blind": {}, "roles": {}}
    sets = {"primary": prim, "primary_q_only": prim_q, "stratum": strat, "question_pairs": q_pairs}
    for cond in ("real", "control"):
        rep["blind"][cond] = {sn: {c: tally_blind(judg, by_id, cond, c, ids) for c in CRITERIA} for sn, ids in sets.items()}
    # real vs control: does the real rewrite-share differ from the control's?
    rep["blind"]["real_vs_control_fisher_p"] = {}
    for sn in sets:
        rep["blind"]["real_vs_control_fisher_p"][sn] = {}
        for c in CRITERIA:
            r, k = rep["blind"]["real"][sn][c], rep["blind"]["control"][sn][c]
            rep["blind"]["real_vs_control_fisher_p"][sn][c] = round(
                fisher_two_sided(r["rewrite_wins"], r["original_wins"], k["rewrite_wins"], k["original_wins"]), 4)
    # position bias: the A / B / tie split of every judged call (a judge with no bias and random order would be A ~ B)
    rep["position_bias"] = {cond: {kind: {c: position_bias(judg, cond, c, kind) for c in CRITERIA}
                                   for kind in ("blind", "blindswap")} for cond in ("real", "control")}
    # swap-consistent (position-debiased) read; control only over the pairs that were swapped in the control arm
    ctrl_swapped = [s["pair_id"] for s in sample if "%s|control|blindswap" % s["pair_id"] in judg]
    rep["debiased"] = {"real": {sn: {c: tally_consistent(judg, "real", c, ids) for c in CRITERIA} for sn, ids in sets.items()},
                       "control": {sn: {c: tally_consistent(judg, "control", c, [p for p in ids if p in set(ctrl_swapped)])
                                        for c in CRITERIA} for sn, ids in sets.items()}}
    for cond in ("real", "control"):
        rep["roles"][cond] = {}
        for sn, ids in (("primary", prim), ("question_pairs", q_pairs)):
            rep["roles"][cond][sn] = {
                "adds_claim_yes": tally_roles(judg, cond, "adds_claim", "yes", ids),
                "voice_lost": tally_roles(judg, cond, "voice_kept", "no", ids),
                "question_lost": tally_roles(judg, cond, "question_kept", "no", ids)}
    # pre-registered defeater rule
    crit_sets = {"question_open": "question_pairs", "faithful": "primary", "voice": "primary"}
    verdict = {c: {"set": crit_sets[c], **rep["blind"]["real"][crit_sets[c]][c],
                   "rewrite_preferred_or_neutral": preferred_or_neutral(rep["blind"]["real"][crit_sets[c]][c])}
               for c in CRITERIA}
    rep["defeater"] = {"rule": "per criterion: rewrite_wins >= original_wins OR sign-test p >= 0.05 on non-ties; "
                               "criterion 1 on question-holding pairs, 2 and 3 on the 120 primary; met = all three",
                       "per_criterion": verdict, "defeater_met": all(v["rewrite_preferred_or_neutral"] for v in verdict.values()),
                       "pairs_in_primary": len(prim), "ge_100_pairs": len(prim) >= 100}
    dv = {c: {"set": crit_sets[c], **rep["debiased"]["real"][crit_sets[c]][c],
              "rewrite_preferred_or_neutral": preferred_or_neutral(rep["debiased"]["real"][crit_sets[c]][c])}
          for c in CRITERIA}
    rep["defeater_debiased"] = {"rule": "same rule, on the swap-consistent tallies (both orders must agree)",
                                "per_criterion": dv, "defeater_met": all(v["rewrite_preferred_or_neutral"] for v in dv.values())}
    return rep


def cmd_report(args):
    sample = [json.loads(l) for l in open(OUT / "sample.jsonl", encoding="utf-8")]
    pop = json.loads((OUT / "population.json").read_text(encoding="utf-8"))
    judg = load_judgments(OUT / "judgments.jsonl")
    rep = build_report(sample, judg, pop)
    (OUT / "report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prep")
    j = sub.add_parser("judge")
    j.add_argument("--limit", type=int, default=0)
    j.add_argument("--workers", type=int, default=2)
    sub.add_parser("report")
    args = ap.parse_args()
    {"prep": cmd_prep, "judge": cmd_judge, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()

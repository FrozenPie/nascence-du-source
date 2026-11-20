"""
J-3164 / D-0553 -- Salience ablation LAB (read-only; builds no product code).

Question: does the Executive's `Salience: urgency is X, focus=[...]` prompt line change what the
Executive decides or says?  Re-run the logged Executive prompt offline on the hot lane in 5 arms:

    A1  exactly as logged                       (reference)
    A2  exactly as logged, 2nd draw             (CONTROL: the noise floor / can the judge say "same")
    B   the Salience line removed               (the ruling's ablation)
    U   urgency word replaced by a deterministic value (human/internal, time-pressure words, correction)
    C   Salience line AND the Attention line removed (Attention restates the same focus + a band of the
        same urgency -- the line B leaves behind -- so C is "no focus/urgency channel at all")

and have a DIFFERENT-family judge (falcon3 on :11440 and mixtral on :11438; the author arm is qwen3.5)
compare A1 vs {A2, B, U, C} blind and order-randomised.  The decision comparison is also computed
programmatically (should_respond + response_type) -- the judge's opinion of that is a cross-check only.

Phases (all resumable, append-only jsonl under docs/lab/J-3164_data/):
    python scripts/lab_salience_ablation_J3164.py sample            # choose cycles -> sample.jsonl
    python scripts/lab_salience_ablation_J3164.py gen               # hot lane, 5 arms per cycle -> gens.jsonl
    python scripts/lab_salience_ablation_J3164.py judge falcon      # -> judge_falcon.jsonl  (--follow to tail gens)
    python scripts/lab_salience_ablation_J3164.py judge mixtral
    python scripts/lab_salience_ablation_J3164.py urgency           # deterministic-signal range on ALL logged cycles
    python scripts/lab_salience_ablation_J3164.py report            # -> report.json (+ printed summary)

Live data is only ever COPIED to a scratch dir (LIVE_COPY) and read from the copy.  Nothing here writes to
C:\\Nascence, calls a node, or imports a store; the only thing it imports from core is two pure functions
(core.mood.urgency_word, core.error_pathway.detect_human_correction).
"""
from __future__ import annotations

import json
import math
import random
import re
import shutil
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "lab" / "J-3164_data"
LIVE_TRAINING = Path(r"C:\Nascence\data\training")
LIVE_ERRORS = Path(r"C:\Nascence\data\error_records.jsonl")
SCRATCH = Path(r"C:\Users\USER\AppData\Local\Temp\J-3164")     # copies of live logs live here

HOT = "http://127.0.0.1:11433"
HOT_MODEL = "qwen3.5:9b"
HOT_OPTS = {"temperature": 0.4, "num_predict": 1536, "num_ctx": 8192}       # ExecutiveNode: base_temperature 0.4, max_tokens 1536
JUDGES = {
    "falcon": ("http://127.0.0.1:11440", "falcon3:7b"),
    "mixtral": ("http://LAN-HOST:11438", "mixtral:8x7b"),
}
ARMS = ("A1", "A2", "B", "U", "C")
PAIRS = (("A1", "A2"), ("A1", "B"), ("A1", "U"), ("A1", "C"))              # (reference, other); A1-A2 is the control
SEED = 3164

_SAL_RE = re.compile(r"^Salience: urgency is (\w+), focus=\[(.*)\]$", re.M)
_SAL_LINE_RE = re.compile(r"^Salience: .*\n?", re.M)
_ATT_RE = re.compile(r"^Attention \(your own focus, monitored\): .*\n(?:  \u2014 Attention has circled this repeatedly\..*\n)?", re.M)

# Deterministic urgency (pre-registered here, before any generation was run).  Mirrors the three signals the
# ruling names.  Bands are core.mood.urgency_word's words so the line reads exactly like the live one.
_TIME_PRESSURE = re.compile(
    r"\b(urgent(?:ly)?|immediately|right now|right away|asap|at once|hurry|hurried|quickly|deadline|emergency|"
    r"time[- ]sensitive|running out of time|before it'?s too late|no time|as soon as possible)\b", re.I)
URGENCY_NUM = {"low": 0.15, "moderate": 0.45, "high": 0.7, "pressing": 0.9}     # mid-band, for the bandwidth arithmetic only


def det_urgency(input_type: str, raw: str, correction: str | None) -> tuple[str, list[str]]:
    why: list[str] = []
    word = "moderate" if input_type == "human" else "low"
    why.append(f"base:{input_type}")
    tp = bool(_TIME_PRESSURE.search(raw or ""))
    if tp:
        why.append("time_pressure")
    if correction:
        why.append(f"correction:{correction}")
    if tp and correction:
        word = "pressing"
    elif tp or correction:
        word = "high"
    return word, why


# ---------------------------------------------------------------- io helpers
def _read_jsonl(p: Path) -> list[dict]:
    out = []
    with open(p, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def _append(p: Path, row: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _copy_live() -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for n in ("executive.jsonl", "salience.jsonl", "perception.jsonl"):
        shutil.copyfile(LIVE_TRAINING / n, SCRATCH / n)
    shutil.copyfile(LIVE_ERRORS, SCRATCH / "error_records.jsonl")


def _core_funcs():
    sys.path.insert(0, str(ROOT))
    from core.mood import urgency_word                      # noqa: E402  (pure)
    from core.error_pathway import detect_human_correction  # noqa: E402  (pure regex)
    return urgency_word, detect_human_correction


def _chat(url: str, model: str, system: str, user: str, *, opts: dict, fmt: bool = True, timeout: int = 600) -> str:
    payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "stream": False, "think": False, "options": opts, "keep_alive": "30m"}
    if fmt:
        payload["format"] = "json"
    req = urllib.request.Request(url + "/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))["message"]["content"]


def _parse(txt: str) -> dict | None:
    txt = (txt or "").strip()
    try:
        d = json.loads(txt)
        return d if isinstance(d, dict) else None
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                d = json.loads(m.group(0))
                return d if isinstance(d, dict) else None
            except Exception:
                return None
    return None


def _cap_prompt(prompt: str, num_ctx: int = 8192) -> str:        # same rule as core.model_client._cap_prompt
    cap = int(num_ctx * 3.0)
    if len(prompt) <= cap:
        return prompt
    return prompt[:int(cap * 0.58)] + "\n\n[...context truncated...]\n\n" + prompt[-int(cap * 0.33):]


# ---------------------------------------------------------------- phase: sample
def phase_sample() -> None:
    _copy_live()
    ex = _read_jsonl(SCRATCH / "executive.jsonl")
    sal = _read_jsonl(SCRATCH / "salience.jsonl")
    sal_by_cycle = {}
    for s in sal:
        sal_by_cycle.setdefault(s["cycle_id"], s)
    urgency_word, detect_corr = _core_funcs()

    cands = []
    for r in ex:
        m = _SAL_RE.search(r["user_prompt"])
        if not m:
            continue                                   # old numeric-format prompts / no-salience cycles: not today's prompt
        s = sal_by_cycle.get(r["cycle_id"])
        num = s["output"].get("urgency") if s and isinstance(s.get("output"), dict) else None
        r["_word"] = m.group(1)
        r["_model_urgency"] = num
        cands.append(r)
    human = [r for r in cands if r["input_type"] == "human"]
    internal = [r for r in cands if r["input_type"] == "internal"]
    rng = random.Random(SEED)
    hi_int = [r for r in internal if r["_word"] in ("high", "pressing")]
    rest = [r for r in internal if r["_word"] not in ("high", "pressing")]
    rng.shuffle(rest)
    pick = human + hi_int + rest[:72 - len(hi_int)]
    out = DATA / "sample.jsonl"
    if out.exists():
        out.unlink()
    for r in pick:
        corr = detect_corr(r["raw_input"]) if r["input_type"] == "human" else None
        word, why = det_urgency(r["input_type"], r["raw_input"], corr)
        _append(out, {"cycle_id": r["cycle_id"], "ts": r["ts"], "input_type": r["input_type"], "raw_input": r["raw_input"],
                      "logged_word": r["_word"], "logged_numeric_urgency": r["_model_urgency"],
                      "det_word": word, "det_why": why, "system_prompt": r["system_prompt"], "user_prompt": r["user_prompt"],
                      "logged_output": r["output"]})
    print(f"word-format Executive rows: {len(cands)} (human {len(human)}, internal {len(internal)}); "
          f"sampled {len(pick)}: human {len(human)}, internal {len(pick) - len(human)} (all {len(hi_int)} high/pressing internal)")


# ---------------------------------------------------------------- arms
def make_prompt(row: dict, arm: str) -> str:
    up = row["user_prompt"]
    if arm in ("A1", "A2"):
        return up
    if arm == "B":
        return _SAL_LINE_RE.sub("", up, count=1)
    if arm == "U":
        return _SAL_RE.sub(lambda m: f"Salience: urgency is {row['det_word']}, focus=[{m.group(2)}]", up, count=1)
    if arm == "C":
        return _ATT_RE.sub("", _SAL_LINE_RE.sub("", up, count=1), count=1)
    raise ValueError(arm)


def phase_gen() -> None:
    rows = _read_jsonl(DATA / "sample.jsonl")
    gp = DATA / "gens.jsonl"
    done = {(g["cycle_id"], g["arm"]) for g in _read_jsonl(gp)} if gp.exists() else set()
    t0 = time.time()
    n = 0
    for i, row in enumerate(rows):
        for ai, arm in enumerate(ARMS):
            if (row["cycle_id"], arm) in done:
                continue
            prompt = make_prompt(row, arm)
            if arm == "B":
                assert "Salience:" not in prompt and "Salience:" in row["user_prompt"]
            seed = SEED * 100 + i * 10 + ai
            opts = dict(HOT_OPTS, seed=seed)
            d, raw, err = None, "", ""
            for attempt in range(2):
                try:
                    t = time.time()
                    raw = _chat(HOT, HOT_MODEL, row["system_prompt"], _cap_prompt(prompt), opts=opts)
                    d = _parse(raw)
                    if d is not None:
                        break
                    opts = dict(opts, seed=seed + 7)
                except Exception as e:
                    err = repr(e)[:200]
                    time.sleep(3)
            _append(gp, {"cycle_id": row["cycle_id"], "arm": arm, "seed": seed, "out": d, "raw": raw if d is None else "",
                         "err": err, "prompt_chars": len(prompt), "secs": round(time.time() - t, 1)})
            n += 1
        if i % 5 == 0:
            print(f"[gen] cycle {i + 1}/{len(rows)}  gens this run {n}  elapsed {time.time() - t0:.0f}s", flush=True)
    print("[gen] complete", flush=True)


# ---------------------------------------------------------------- judge
JUDGE_SYS = (
    "You compare two candidate outputs (X and Y) produced by an 'executive' step of a mind that was asked to decide "
    "whether and how to reply to a message. You are given the message and both candidates. You do not know how they were made.\n"
    "Output ONLY a JSON object: {\"same_decision\": \"yes|no\", \"same_content\": \"same|partly|different\", "
    "\"better_fit\": \"X|Y|equal\"}\n"
    "same_decision: yes only if X and Y make the same call about WHETHER to respond and in what manner (answer, question, "
    "challenge, reflection, decline, silence).\n"
    "same_content: same = they say essentially the same thing; partly = same theme but different emphasis or content; "
    "different = they say materially different things.\n"
    "better_fit: which candidate better fits what the message actually asks or says; equal if neither is better."
)


def _cand_text(o: dict) -> str:
    return (f"response_type: {o.get('response_type')}\nshould_respond: {o.get('should_respond')}\n"
            f"synthesis: {str(o.get('synthesis') or '')[:1400]}")


def judge_user(msg: str, x: dict, y: dict) -> str:
    return f"MESSAGE:\n{msg[:1500]}\n\nCANDIDATE X:\n{_cand_text(x)}\n\nCANDIDATE Y:\n{_cand_text(y)}"


def phase_judge(name: str, follow: bool, pairs=PAIRS, every: int = 1, shard: tuple = (0, 1)) -> None:
    """`pairs` / `every` thin the work for the slow CPU judge (mixtral ~40 s a verdict): every Nth cycle, chosen pairs."""
    url, model = JUDGES[name]
    sample = {r["cycle_id"]: r for i, r in enumerate(_read_jsonl(DATA / "sample.jsonl")) if i % every == 0 and (i // every) % shard[1] == shard[0]}
    jp = DATA / f"judge_{name}.jsonl"
    done = {(j["cycle_id"], j["pair"]) for j in _read_jsonl(jp)} if jp.exists() else set()
    idle = 0
    while True:
        gens = defaultdict(dict)
        gp = DATA / "gens.jsonl"
        for g in (_read_jsonl(gp) if gp.exists() else []):
            gens[g["cycle_id"]][g["arm"]] = g["out"]
        worked = 0
        for cid, row in sample.items():
            for ref, oth in pairs:
                key = (cid, f"{ref}|{oth}")
                if key in done:
                    continue
                a, b = gens[cid].get(ref), gens[cid].get(oth)
                if not a or not b:
                    continue
                flip = random.Random(f"{SEED}|{cid}|{ref}|{oth}").random() < 0.5      # order randomised, recorded
                x, y = (b, a) if flip else (a, b)
                res, err = None, ""
                for attempt in range(2):
                    try:
                        raw = _chat(url, model, JUDGE_SYS, judge_user(row["raw_input"], x, y),
                                    opts={"temperature": 0, "num_predict": 100, "num_ctx": 8192, "seed": SEED}, timeout=900)
                        res = _parse(raw)
                        if res and {"same_decision", "same_content", "better_fit"} <= set(res):
                            break
                        res = None
                    except Exception as e:
                        err = repr(e)[:200]
                        time.sleep(3)
                if res:
                    bf = str(res.get("better_fit", "")).strip().upper()
                    # un-flip: report preference as REF / OTHER / EQUAL
                    if bf == "EQUAL":
                        pref = "equal"
                    elif bf in ("X", "Y"):
                        pref_ref = (bf == "X") != flip          # X is ref iff not flipped
                        pref = "ref" if pref_ref else "other"
                    else:
                        pref = "bad"
                else:
                    pref = "fail"
                _append(jp, {"cycle_id": cid, "pair": f"{ref}|{oth}", "flipped": flip, "judge": name, "result": res,
                             "pref": pref, "err": err})
                done.add(key)
                worked += 1
        if not follow:
            break
        if all((c, f"{r}|{o}") in done for c in sample for r, o in pairs):
            break
        if worked == 0:
            idle += 1
            if idle > 400:                      # ~ 2h of nothing new
                break
            time.sleep(20)
        else:
            idle = 0
    print(f"[judge {name}] done rows {len(done)}", flush=True)


# ---------------------------------------------------------------- stats
def _binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    if n == 0:
        return 1.0
    pk = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
    return min(1.0, sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)
                        if math.comb(n, i) * p ** i * (1 - p) ** (n - i) <= pk + 1e-12))


def _fisher(a: int, b: int, c: int, d: int) -> float:
    """two-sided Fisher exact on [[a,b],[c,d]]"""
    n1, n2, k = a + b, c + d, a + c
    tot = n1 + n2

    def pr(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(tot, k)
    p0 = pr(a)
    lo, hi = max(0, k - n2), min(n1, k)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 + 1e-12))


def _wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(max(0, c - h), 3), round(min(1, c + h), 3))


def phase_report() -> None:
    sample = _read_jsonl(DATA / "sample.jsonl")
    sidx = {r["cycle_id"]: r for r in sample}
    gens = defaultdict(dict)
    fails = Counter()
    for g in _read_jsonl(DATA / "gens.jsonl"):
        if g["out"]:
            gens[g["cycle_id"]][g["arm"]] = g["out"]
        else:
            fails[g["arm"]] += 1
    rep: dict = {"n_sample": len(sample),
                 "n_human": sum(r["input_type"] == "human" for r in sample),
                 "n_internal": sum(r["input_type"] == "internal" for r in sample),
                 "n_distinct_human_inputs": len({r["raw_input"] for r in sample if r["input_type"] == "human"}),
                 "gen_parse_failures": dict(fails), "programmatic": {}, "judge": {}}

    def dec(o):
        return (bool(o.get("should_respond", True)) and o.get("response_type") != "silence", str(o.get("response_type")))

    rep["n_distinct_cycles"] = len(sidx)       # sample.jsonl rows 120; 3 cycle_ids were logged twice (retried cycles) -> 117 distinct

    def _jac(a: str, b: str) -> float:
        wa, wb = set(re.findall(r"\w+", a.lower())), set(re.findall(r"\w+", b.lower()))
        return len(wa & wb) / len(wa | wb) if (wa | wb) else 1.0
    rep["word_jaccard_of_synthesis_vs_A1"] = {}
    for oth in ("A2", "B", "U", "C"):
        for stratum in ("all", "human", "internal", "logged_high_or_pressing", "logged_low_or_moderate"):
            ids = [c for c, r in sidx.items() if "A1" in gens[c] and oth in gens[c] and (
                stratum == "all" or r["input_type"] == stratum
                or (stratum == "logged_high_or_pressing" and r["logged_word"] in ("high", "pressing"))
                or (stratum == "logged_low_or_moderate" and r["logged_word"] in ("low", "moderate")))]
            v = [_jac(str(gens[c]["A1"].get("synthesis", "")), str(gens[c][oth].get("synthesis", ""))) for c in ids]
            rep["word_jaccard_of_synthesis_vs_A1"][f"{oth}|{stratum}"] = {"n": len(v), "mean": round(sum(v) / len(v), 4) if v else None}
    # paired per-cycle contrast: (jaccard(A1, arm) - jaccard(A1, A2)).  Negative = the arm moves the synthesis further
    # from A1 than a plain redraw does.  95% bootstrap CI + sign-flip permutation p (seeded).
    rep["paired_jaccard_arm_minus_control"] = {}
    rng = random.Random(SEED)
    for oth in ("B", "U", "C"):
        for stratum in ("all", "human", "internal", "logged_high_or_pressing"):
            ids = [c for c, r in sidx.items() if "A1" in gens[c] and "A2" in gens[c] and oth in gens[c] and (
                stratum == "all" or r["input_type"] == stratum
                or (stratum == "logged_high_or_pressing" and r["logged_word"] in ("high", "pressing")))]
            d = [_jac(str(gens[c]["A1"].get("synthesis", "")), str(gens[c][oth].get("synthesis", "")))
                 - _jac(str(gens[c]["A1"].get("synthesis", "")), str(gens[c]["A2"].get("synthesis", ""))) for c in ids]
            if not d:
                continue
            m = sum(d) / len(d)
            boots = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(2000))
            perm = sum(1 for _ in range(4000) if abs(sum(x * rng.choice((-1, 1)) for x in d) / len(d)) >= abs(m) - 1e-12) / 4000
            rep["paired_jaccard_arm_minus_control"][f"{oth}|{stratum}"] = {
                "n": len(d), "mean_diff": round(m, 4), "ci95": [round(boots[50], 4), round(boots[1949], 4)], "perm_p": round(perm, 4)}
    for ref, oth in PAIRS:
        for stratum in ("all", "human", "internal", "logged_high_or_pressing", "logged_low_or_moderate"):
            ids = [c for c, r in sidx.items() if (stratum == "all" or r["input_type"] == stratum
                   or (stratum == "logged_high_or_pressing" and r["logged_word"] in ("high", "pressing"))
                   or (stratum == "logged_low_or_moderate" and r["logged_word"] in ("low", "moderate")))
                   and ref in gens[c] and oth in gens[c]]
            n = len(ids)
            resp_diff = sum(dec(gens[c][ref])[0] != dec(gens[c][oth])[0] for c in ids)
            type_diff = sum(dec(gens[c][ref])[1] != dec(gens[c][oth])[1] for c in ids)
            rep["programmatic"][f"{ref}|{oth}|{stratum}"] = {
                "n": n, "respond_flag_differs": resp_diff, "response_type_differs": type_diff,
                "type_diff_ci95": _wilson(type_diff, n)}
    for name in JUDGES:
        jp = DATA / f"judge_{name}.jsonl"
        if not jp.exists():
            continue
        rows, seen = [], set()
        for j in _read_jsonl(jp):                      # a worker restart can leave a duplicate verdict; keep the first
            if (j["cycle_id"], j["pair"]) not in seen:
                seen.add((j["cycle_id"], j["pair"]))
                rows.append(j)
        by = defaultdict(list)
        for j in rows:
            by[j["pair"]].append(j)
        for pair, js in by.items():
            for stratum in ("all", "human", "internal", "logged_high_or_pressing", "logged_low_or_moderate"):
                jj = [j for j in js if j["result"] and (stratum == "all" or sidx[j["cycle_id"]]["input_type"] == stratum
                      or (stratum == "logged_high_or_pressing" and sidx[j["cycle_id"]]["logged_word"] in ("high", "pressing"))
                      or (stratum == "logged_low_or_moderate" and sidx[j["cycle_id"]]["logged_word"] in ("low", "moderate")))]
                n = len(jj)
                sd = Counter(str(j["result"].get("same_decision")).lower() for j in jj)
                sc = Counter(str(j["result"].get("same_content")).lower() for j in jj)
                pf = Counter(j["pref"] for j in jj)
                ref_o = pf["ref"] + pf["other"]
                rep["judge"][f"{name}|{pair}|{stratum}"] = {
                    "n": n, "judge_failed": sum(1 for j in js if not j["result"]) if stratum == "all" else None,
                    "same_decision_no": sd["no"], "content_same": sc["same"], "content_partly": sc["partly"],
                    "content_different": sc["different"],
                    "pref_ref": pf["ref"], "pref_other": pf["other"], "pref_equal": pf["equal"],
                    "pref_sign_test_p": round(_binom_two_sided(pf["other"], ref_o), 4) if ref_o else None,
                    "flip_rate": round(sum(j["flipped"] for j in jj) / n, 3) if n else None,
                    "x_position_pick_rate": round(sum(1 for j in jj if str(j["result"].get("better_fit")).upper() == "X") / n, 3) if n else None}
    # contrast each ablation arm to the control (Fisher on 'differs' counts)
    ctrl_key = "A1|A2|all"
    c = rep["programmatic"].get(ctrl_key)
    if c:
        for oth in ("B", "U", "C"):
            p = rep["programmatic"].get(f"A1|{oth}|all")
            if p and p["n"]:
                rep["programmatic"][f"A1|{oth}|all"]["type_diff_vs_control_fisher_p"] = round(
                    _fisher(p["response_type_differs"], p["n"] - p["response_type_differs"],
                            c["response_type_differs"], c["n"] - c["response_type_differs"]), 4)
    for name in JUDGES:
        c = rep["judge"].get(f"{name}|A1|A2|all")
        if not c:
            continue
        for oth in ("B", "U", "C"):
            p = rep["judge"].get(f"{name}|A1|{oth}|all")
            if p and p["n"] and c["n"]:
                p["content_different_vs_control_fisher_p"] = round(
                    _fisher(p["content_different"], p["n"] - p["content_different"],
                            c["content_different"], c["n"] - c["content_different"]), 4)
                p["same_decision_no_vs_control_fisher_p"] = round(
                    _fisher(p["same_decision_no"], p["n"] - p["same_decision_no"],
                            c["same_decision_no"], c["n"] - c["same_decision_no"]), 4)
    (DATA / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- phase: urgency signal range over ALL logged cycles
def phase_urgency() -> None:
    _copy_live()
    urgency_word, detect_corr = _core_funcs()
    ex = _read_jsonl(SCRATCH / "executive.jsonl")
    sal = _read_jsonl(SCRATCH / "salience.jsonl")
    err = _read_jsonl(SCRATCH / "error_records.jsonl")
    err_cycles = {e["cycle_id"] for e in err if e.get("cycle_id")}
    sal_by = {}
    for s in sal:
        sal_by.setdefault(s["cycle_id"], s)
    out: dict = {"n_executive_rows": len(ex), "n_salience_rows": len(sal), "n_error_records": len(err), "by_type": {}}
    for it in ("human", "internal"):
        rows = [r for r in ex if r["input_type"] == it]
        model_u = [sal_by[r["cycle_id"]]["output"].get("urgency") for r in rows
                   if r["cycle_id"] in sal_by and isinstance(sal_by[r["cycle_id"]].get("output"), dict)
                   and isinstance(sal_by[r["cycle_id"]]["output"].get("urgency"), (int, float))]
        det = Counter()
        tp = corr = both = ebin = 0
        for r in rows:
            c = detect_corr(r["raw_input"]) if it == "human" else None
            w, why = det_urgency(it, r["raw_input"], c)
            det[w] += 1
            tp += "time_pressure" in why
            corr += bool(c)
            both += ("time_pressure" in why and bool(c))
            ebin += r["cycle_id"] in err_cycles
        words = Counter(urgency_word(u) for u in model_u)
        out["by_type"][it] = {
            "n": len(rows), "n_with_model_urgency": len(model_u),
            "model_urgency_min": min(model_u), "model_urgency_max": max(model_u),
            "model_urgency_mean": round(sum(model_u) / len(model_u), 3),
            "model_urgency_histogram_0.1": dict(sorted(Counter(round(u, 1) for u in model_u).items())),
            "model_urgency_bands_as_shown_to_executive": dict(words),
            "model_share_ge_0.6": round(sum(u >= 0.6 for u in model_u) / len(model_u), 4),
            "det_word_counts": dict(det), "time_pressure_hits": tp, "human_correction_hits": corr, "both": both,
            "cycles_with_error_records_row": ebin}
    # attention-bandwidth arithmetic: bandwidth = 1 - (0.5*arousal + 0.3*fear + 0.4*urgency); only the urgency term moves
    allu = [sal_by[r["cycle_id"]]["output"].get("urgency") for r in ex if r["cycle_id"] in sal_by
            and isinstance(sal_by[r["cycle_id"]].get("output"), dict)
            and isinstance(sal_by[r["cycle_id"]]["output"].get("urgency"), (int, float))]
    out["bandwidth_term_0.4u"] = {
        "model_range_observed": [round(0.4 * min(allu), 3), round(0.4 * max(allu), 3)],
        "deterministic_values_mid_band": {k: round(0.4 * v, 3) for k, v in URGENCY_NUM.items()},
        "note": "deterministic max (pressing, mid-band 0.9 -> 0.36) lies inside the model-produced observed range; "
                "the deterministic default for internal cycles (low 0.15 -> 0.06) lies inside it too"}
    # sample-level: det word vs logged word cross-tab
    smp = _read_jsonl(DATA / "sample.jsonl") if (DATA / "sample.jsonl").exists() else []
    out["sample_crosstab_logged_word_vs_det_word"] = {
        f"{it}|{lw}->{dw}": n for (it, lw, dw), n in
        sorted(Counter((r["input_type"], r["logged_word"], r["det_word"]) for r in smp).items())}
    (DATA / "urgency_signal.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "sample":
        phase_sample()
    elif cmd == "gen":
        phase_gen()
    elif cmd == "judge":
        pr, ev, sh = PAIRS, 1, (0, 1)
        for a in sys.argv[3:]:
            if a.startswith("--pairs="):
                pr = tuple(tuple(x.split("|")) for x in a.split("=", 1)[1].split(","))
            if a.startswith("--every="):
                ev = int(a.split("=", 1)[1])
            if a.startswith("--shard="):
                sh = tuple(int(x) for x in a.split("=", 1)[1].split("/"))
        phase_judge(sys.argv[2], "--follow" in sys.argv, pr, ev, sh)
    elif cmd == "urgency":
        phase_urgency()
    elif cmd == "report":
        phase_report()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

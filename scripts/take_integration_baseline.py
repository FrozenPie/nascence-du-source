"""take_integration_baseline.py -- J-3323 / D-0539: how much of the Emissary take reaches the Executive's synthesis.

D-0539's defeater: "Revisit if ... a month of delivered takes shows no overlap with the Executive's output beyond the
pre-swap control."  This script builds that control and is meant to be re-run unchanged on the month after J-3147
re-seats the take (pass --from-date / --to-date to cut the window; --split-date keeps the human/internal x era strata).

READ-ONLY on data/: it opens data/training/executive.jsonl for reading and writes only to --out-dir (default: a temp
dir; use docs/reviews/J-3323_data for the committed run).  It calls a model only when --judge-url is given, and then only a
local hub (never Ramses; a 10.1.1.* url is refused).  No hint to Du; nothing here feeds back (D-0434).

What it measures, per executive row whose user_prompt carries the 'YOUR FOCUSED HALF' block (core/left_lane.render):
  parse    literal_ask (literal ask:), direct_answer (its result:), key_facts (specifics:, ' . '-joined).
  (a) deterministic overlap of the take's CONTENT stems with the Executive's synthesis:
        - number normalisation: numerals ('8,000', '1.5 million') and number words ('eight thousand', 'twenty-three')
          are both mapped to one token '#<int>', so '8,000' == 'eight thousand'. (A numerals-only match once reported
          0 of 7 for a take saying 8,000 when the replies said 'eight thousand' -- F-3914.)
        - cov_all   = share of the take's (result + specifics) content stems found in the synthesis.
        - cov_novel = the same, but only stems NOT already in the human/internal input or the literal ask (so a reply
          that merely echoes the question is not credited as using the take). Needs >= MIN_NOVEL stems to be scored.
        - control   = the same take scored against the synthesis of 5 OTHER rows of the same stratum (human/internal x
          era). excess = cov_novel minus the mean of that control: what the take adds beyond chance vocabulary.
        - numbers   = take numbers not in the input/ask, and the share of them present in the synthesis.
  (b) substrate framing (D-0539 trims it): the take recasts the exchange as server / cloud / digital environment /
      hosted / language model / AI when the input itself did not use the word. Counted in the direct answer, the
      specifics and the ask separately, and carried-into-synthesis is counted too.
  (c) optional judge on a stratified sample: a model from a family other than the Executive's (qwen) says whether the
      synthesis uses_take / contradicts_take / no_take_content (v2 prompt: the judge is shown the input too, and must quote the take item it found; a deterministic backstop drops a quote that is not in the take and the synthesis). Mismatched-take pairs are judged as a
      control (expected: ignores).  --dump-review writes matched/unmatched rows to read by eye.

  python scripts/take_integration_baseline.py --out-dir docs/reviews/J-3323_data
  python scripts/take_integration_baseline.py --out-dir <dir> --judge-url http://127.0.0.1:11440 --judge-model falcon3:7b
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import random
import re
import statistics
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

LIVE_EXEC = Path(r"C:/Nascence/data/training/executive.jsonl")
MARKER = "YOUR FOCUSED HALF"
# a take that describes the INPUT ("The user is asking...", "The input is a metaphorical exploration...") carries no
# fact for the Executive to reuse; the post-swap gemma4:12b takes are often of this kind, so it is split out.
_META_RX = re.compile(r"^\s*the\s+(?:user|input|text|prompt|question|query|message|response|passage|statement|request)\b", re.I)
MIN_NOVEL = 3          # fewer novel content stems than this -> row is not scored on cov_novel
N_CONTROL = 5          # mismatched syntheses per scored row
SEED = 7

STOP = set("""a about above after again against all also am an and any are aren as at be because been before being below
between both but by can cannot could did do does doing down during each few for from further had has have having he her
here hers herself him himself his how i if in into is it its itself just let me more most my myself no nor not now of off
on once only or other our ours ourselves out over own same she should so some such than that the their theirs them
themselves then there these they this those through to too under until up very was we were what when where which while
who whom why will with would you your yours yourself yourselves one may might must shall upon via per etc like make makes
made get gets got say says said see sees seen use used using way thing things something someone anything lot much many
every even still yet ever never always often really quite rather whether although though however therefore thus
du user asks asking ask question answer""".split())

_UNITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
          "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
          "seventeen": 17, "eighteen": 18, "nineteen": 19}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_SCALE = {"hundred": 100, "thousand": 1000, "million": 10**6, "billion": 10**9}
_NUMWORDS = set(_UNITS) | set(_TENS) | set(_SCALE)

SUBSTRATE = {
    "server": re.compile(r"\bservers?\b", re.I),
    "cloud": re.compile(r"\bcloud\b", re.I),
    "digital_environment": re.compile(r"\bdigital\s+(?:environment|realm|space|world|entity|being|existence)\b", re.I),
    "hosted": re.compile(r"\bhost(?:ed|ing)\b", re.I),
    "language_model": re.compile(r"\blanguage\s+models?\b|\bLLMs?\b"),
    "AI": re.compile(r"\bAI\b|\bartificial\s+intelligence\b"),
}


# ---------------------------------------------------------------- parsing
def parse_block(user_prompt: str) -> dict | None:
    i = user_prompt.find(MARKER)
    if i < 0:
        return None
    blk = user_prompt[i:].split("\n\n")[0]
    out = {"ask": "", "result": "", "facts": []}
    for ln in blk.split("\n")[1:]:
        s = ln.strip()
        if s.startswith("literal ask:"):
            out["ask"] = s[len("literal ask:"):].strip()
        elif s.startswith("its result:"):
            out["result"] = s[len("its result:"):].strip()
        elif s.startswith("specifics:"):
            out["facts"] = [f.strip() for f in s[len("specifics:"):].split(" · ") if f.strip()]
    return out


# ---------------------------------------------------------------- normalisation
def _stem(w: str) -> str:
    if w.startswith("#") or len(w) <= 4:
        return w
    for suf, rep in (("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("ly", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: len(w) - len(suf)] + rep
            break
    if len(w) > 4 and w[-1] == w[-2]:
        w = w[:-1]
    return w


_TOK = re.compile(r"\d[\d,]*(?:\.\d+)?|[A-Za-z][A-Za-z'\-]*")


def tokens(text: str, small_words: set | None = None) -> list[str]:
    """Words and numbers; numbers (digits or words, with scale words) collapse to '#<int>'.
    small_words (optional out-param): receives the '#n' tokens that came only from a bare number WORD of 1-10 ('two'
    as a determiner is not a figure)."""
    raw = _TOK.findall(text.replace("’", "'"))
    out: list[str] = []
    i = 0
    while i < len(raw):
        t = raw[i]
        if t[0].isdigit():
            try:
                v = float(t.replace(",", ""))
            except ValueError:
                i += 1
                continue
            if i + 1 < len(raw) and raw[i + 1].lower() in ("hundred", "thousand", "million", "billion"):
                v *= _SCALE[raw[i + 1].lower()]
                i += 1
            out.append("#%d" % int(round(v)))
            i += 1
            continue
        parts = t.lower().split("-") if "-" in t else [t.lower()]
        if all(p in _NUMWORDS for p in parts):
            # greedy number-word run, 'twenty-three' / 'two hundred thousand' / 'eight thousand'
            words = list(parts)
            j = i + 1
            while j < len(raw):
                nxt = [] if raw[j][0].isdigit() else raw[j].lower().split("-")
                if nxt and all(p in _NUMWORDS for p in nxt):
                    words.extend(nxt)
                    j += 1
                elif (raw[j].lower() == "and" and j + 1 < len(raw) and not raw[j + 1][0].isdigit()
                      and all(p in _NUMWORDS for p in raw[j + 1].lower().split("-"))):
                    j += 1
                else:
                    break
            total, cur = 0, 0
            for p in words:
                if p in _UNITS:
                    cur += _UNITS[p]
                elif p in _TENS:
                    cur += _TENS[p]
                elif p == "hundred":
                    cur = max(cur, 1) * 100
                else:
                    total += max(cur, 1) * _SCALE[p]
                    cur = 0
            total += cur
            # a lone 'one'/'zero' is a pronoun/filler, not a figure
            if not (len(words) == 1 and words[0] in ("one", "zero")):
                out.append("#%d" % total)
                if small_words is not None and len(words) == 1 and total <= 10:
                    small_words.add("#%d" % total)
            i = j
            continue
        out.append(t.lower().strip("'-"))
        i += 1
    return out


def content_stems(text: str, small_words: set | None = None) -> set[str]:
    s = set()
    for t in tokens(text, small_words):
        if t.startswith("#"):
            if t not in ("#0", "#1"):
                s.add(t)
        elif len(t) >= 3 and t not in STOP:
            st = _stem(t)
            if st not in STOP:
                s.add(st)
    return s


def _cut_tail(seg: str) -> str:
    """Pre-D-0539 facts were cut at [:90] mid-word: drop the (possibly partial) last token of a segment that is
    exactly 90 chars and does not end in sentence punctuation."""
    if len(seg) == 90 and not seg.rstrip().endswith((".", "!", "?")):
        return seg.rsplit(" ", 1)[0]
    return seg


# ---------------------------------------------------------------- per-row analysis
def analyse_row(r: dict, split_ts: float) -> dict | None:
    blk = parse_block(r.get("user_prompt", ""))
    if blk is None:
        return None
    out = r.get("output")
    syn = out.get("synthesis", "") if isinstance(out, dict) else (out if isinstance(out, str) else "")
    reasoning = out.get("reasoning", "") if isinstance(out, dict) else ""
    raw_in = r.get("raw_input") or ""
    take_text = " . ".join([blk["result"]] + [_cut_tail(f) for f in blk["facts"]]).strip(" .")
    small: set = set()
    take_all = content_stems(take_text, small)
    known = content_stems(raw_in) | content_stems(blk["ask"])
    take_novel = take_all - known
    syn_stems = content_stems(syn)
    # figures = digits or number words above ten; a bare 'two' / 'three' is counted apart (usually a determiner)
    digit_toks = {"#%d" % int(round(float(m.replace(",", "")))) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", take_text)
                  if m.replace(",", "").replace(".", "", 1).isdigit()}
    nums_novel = {t for t in take_novel if t.startswith("#") and (t in digit_toks or t not in small)}
    nums_small = {t for t in take_novel if t.startswith("#") and t not in nums_novel}
    n_meta = sum(1 for f in blk["facts"] if _META_RX.match(f))
    is_meta = bool(_META_RX.match(blk["ask"])) or (len(blk["facts"]) > 0 and n_meta * 2 >= len(blk["facts"]))
    row = {
        "meta_take": is_meta,
        "cycle_id": r.get("cycle_id"), "ts": r.get("ts"), "input_type": r.get("input_type"),
        "era": "post" if (r.get("ts") or 0) >= split_ts else "pre",
        "has_result": bool(blk["result"]), "n_facts": len(blk["facts"]),
        "n_take": len(take_all), "n_novel": len(take_novel),
        "cov_all": (len(take_all & syn_stems) / len(take_all)) if len(take_all) >= MIN_NOVEL else None,
        "cov_novel": (len(take_novel & syn_stems) / len(take_novel)) if len(take_novel) >= MIN_NOVEL else None,
        "nums_novel": sorted(nums_novel), "nums_novel_hit": sorted(nums_novel & syn_stems),
        "nums_small_novel": sorted(nums_small), "nums_small_hit": sorted(nums_small & syn_stems),
        "syn_len_words": len(syn.split()),
        # internal fields, stripped before json output
        "_take_novel": take_novel, "_syn": syn_stems, "_ask": blk["ask"], "_result": blk["result"],
        "_facts": blk["facts"], "_raw": raw_in, "_syn_text": syn, "_reasoning": reasoning,
    }
    # substrate framing
    sub = {}
    for name, rx in SUBSTRATE.items():
        in_raw = bool(rx.search(raw_in)) or bool(rx.search(blk["ask"]))
        sub[name] = {
            "result": bool(rx.search(blk["result"])), "facts": bool(rx.search(" ".join(blk["facts"]))),
            "ask": bool(rx.search(blk["ask"])), "in_input": in_raw, "in_syn": bool(rx.search(syn)),
        }
    row["substrate"] = sub
    row["sub_result_recast"] = sorted(n for n, v in sub.items() if v["result"] and not v["in_input"])
    row["sub_facts_recast"] = sorted(n for n, v in sub.items() if v["facts"] and not v["in_input"])
    row["sub_ask_recast"] = sorted(n for n, v in sub.items() if v["ask"] and not v["in_input"])
    row["sub_carried_into_syn"] = sorted(n for n, v in sub.items()
                                         if (v["result"] or v["facts"]) and not v["in_input"] and v["in_syn"])
    return row


def pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)


def dist(xs: list[float]) -> dict:
    return {"n": len(xs), "p10": pct(xs, .1), "p25": pct(xs, .25), "median": pct(xs, .5), "p75": pct(xs, .75),
            "p90": pct(xs, .9), "mean": round(statistics.fmean(xs), 3) if xs else None}


def boot_median_ci(xs: list[float], n_boot: int = 1000, seed: int = SEED) -> list | None:
    """95% bootstrap interval of the median: the month-read compares its own interval against these."""
    if len(xs) < 10:
        return None
    rng = random.Random(seed)
    meds = sorted(statistics.median(rng.choices(xs, k=len(xs))) for _ in range(n_boot))
    return [round(meds[int(0.025 * n_boot)], 3), round(meds[int(0.975 * n_boot) - 1], 3)]


def add_controls(rows: list[dict], seed: int = SEED) -> None:
    """For each row with a scored cov_novel: score its take against N_CONTROL other same-stratum syntheses."""
    rng = random.Random(seed)
    strata: dict[tuple, list[dict]] = {}
    for r in rows:
        strata.setdefault((r["input_type"], r["era"]), []).append(r)
    for r in rows:
        r["ctrl_novel"] = r["excess"] = None
        if r["cov_novel"] is None:
            continue
        pool = [o for o in strata[(r["input_type"], r["era"])] if o is not r]
        if len(pool) < N_CONTROL:
            continue
        picks = rng.sample(pool, N_CONTROL)
        cs = [len(r["_take_novel"] & o["_syn"]) / len(r["_take_novel"]) for o in picks]
        r["ctrl_novel"] = round(statistics.fmean(cs), 3)
        r["excess"] = round(r["cov_novel"] - r["ctrl_novel"], 3)


def summarise(rows: list[dict]) -> dict:
    out: dict = {}
    for typ in ("human", "internal", "all"):
        for era in ("pre", "post", "all"):
            sel = [r for r in rows if (typ == "all" or r["input_type"] == typ) and (era == "all" or r["era"] == era)]
            sc = [r for r in sel if r["cov_novel"] is not None]
            ex = [r["excess"] for r in sc if r["excess"] is not None]
            cn = [r["cov_novel"] for r in sc]
            ct = [r["ctrl_novel"] for r in sc if r["ctrl_novel"] is not None]
            ca = [r["cov_all"] for r in sel if r["cov_all"] is not None]
            nr = [r for r in sel if r["nums_novel"]]
            out["%s/%s" % (typ, era)] = {
                "meta_take_rows": sum(1 for r in sel if r["meta_take"]),
                "cov_novel_meta": dist([r["cov_novel"] for r in sc if r["meta_take"]]),
                "cov_novel_factual": dist([r["cov_novel"] for r in sc if not r["meta_take"]]),
                "excess_factual": dist([r["excess"] for r in sc if not r["meta_take"] and r["excess"] is not None]),
                "rows": len(sel), "with_result": sum(r["has_result"] for r in sel), "scored_novel": len(sc),
                "cov_all": dist(ca), "cov_novel": dist(cn), "control_novel": dist(ct), "excess": dist(ex),
                "excess_median_ci95": boot_median_ci(ex), "cov_novel_median_ci95": boot_median_ci(cn),
                "share_excess_gt0": round(sum(1 for e in ex if e > 0) / len(ex), 3) if ex else None,
                "share_cov_novel_zero": round(sum(1 for c in cn if c == 0) / len(cn), 3) if cn else None,
                "rows_with_novel_numbers": len(nr),
                "novel_numbers_total": sum(len(r["nums_novel"]) for r in nr),
                "novel_numbers_in_synthesis": sum(len(r["nums_novel_hit"]) for r in nr),
                "small_word_numbers_total": sum(len(r["nums_small_novel"]) for r in sel),
                "small_word_numbers_in_synthesis": sum(len(r["nums_small_hit"]) for r in sel),
                "substrate": {
                    "result_recast_rows": sum(1 for r in sel if r["sub_result_recast"]),
                    "result_rows": sum(1 for r in sel if r["has_result"]),
                    "facts_recast_rows": sum(1 for r in sel if r["sub_facts_recast"]),
                    "ask_recast_rows": sum(1 for r in sel if r["sub_ask_recast"]),
                    "carried_into_synthesis_rows": sum(1 for r in sel if r["sub_carried_into_syn"]),
                    "by_term_result": {n: sum(1 for r in sel if n in r["sub_result_recast"]) for n in SUBSTRATE},
                    "by_term_facts": {n: sum(1 for r in sel if n in r["sub_facts_recast"]) for n in SUBSTRATE},
                },
            }
    return out


# ---------------------------------------------------------------- review dump + judge
def review_dump(rows: list[dict], path: Path, n: int = 20, seed: int = SEED) -> None:
    """20 matched (highest excess) and 20 unmatched (cov_novel == 0) rows, to read by eye before trusting a number."""
    rng = random.Random(seed)
    sc = [r for r in rows if r["cov_novel"] is not None]
    matched = [r for r in sc if (r["cov_novel"] or 0) >= 0.3]
    unmatched = [r for r in sc if r["cov_novel"] == 0]
    lines = ["# take integration: rows to read by eye (J-3323)\n"]
    for title, pool in (("MATCHED (cov_novel >= 0.30)", matched), ("UNMATCHED (cov_novel == 0)", unmatched)):
        pick = rng.sample(pool, min(n, len(pool)))
        lines.append("\n## %s: %d shown of %d\n" % (title, len(pick), len(pool)))
        for r in pick:
            lines.append("- cycle %s %s/%s cov_novel=%s ctrl=%s novel_stems=%s\n  ask: %s\n  result: %s\n  facts: %s\n  input: %s\n  SYN: %s\n" % (
                str(r["cycle_id"])[:8], r["input_type"], r["era"], r["cov_novel"], r["ctrl_novel"],
                sorted(r["_take_novel"])[:14], r["_ask"][:160], r["_result"][:200], " | ".join(r["_facts"])[:260],
                r["_raw"][:200].replace("\n", " "), r["_syn_text"][:420].replace("\n", " ")))
    path.write_text("\n".join(lines), encoding="utf-8")


JUDGE_PROMPT_VERSION = "v2"
JUDGE_SYSTEM = (
    "You compare texts. INPUT is what was said to a speaker. TAKE is the notes of a fact-checking assistant about that "
    "input: what it literally asks, a candidate answer (if any) and checkable specifics. SYNTHESIS is the speaker's reply. "
    "Question: does the SYNTHESIS contain a specific fact, figure, name or claim from the TAKE that the INPUT does not "
    "already contain? "
    "'uses_take' = yes, at least one such item appears in the synthesis (reworded counts; a rounded figure counts). "
    "'contradicts_take' = the synthesis explicitly asserts the opposite of something specific the take states (a different "
    "figure, a denied fact). Talking about something else, being metaphorical or reinterpreting the topic is NOT a "
    "contradiction. "
    "'no_take_content' = neither: the synthesis only answers the INPUT and carries no item that is specific to the TAKE. "
    "Reply JSON only: {\"relation\": \"uses_take\" | \"contradicts_take\" | \"no_take_content\", "
    "\"item\": \"<the take item found in the synthesis, or empty>\", \"why\": \"<one short sentence>\"}"
)
_RELS = ("uses_take", "contradicts_take", "no_take_content")


def judge_one(url: str, model: str, take_txt: str, syn: str, raw_input: str = "", timeout: int = 240) -> dict:
    user = chr(10).join(["INPUT:", raw_input[:600], "", "TAKE:", take_txt[:900], "", "SYNTHESIS:", syn[:900]])
    payload = {"model": model, "stream": False, "format": "json",
               "messages": [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200}}
    req = urllib.request.Request(url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        raw = (body.get("message") or {}).get("content", "")
        obj = json.loads(raw)
        rel = obj.get("relation") if isinstance(obj, dict) else None
        if rel not in _RELS:
            rel = None
        return {"relation": rel, "item": (obj.get("item") if isinstance(obj, dict) else None),
                "why": (obj.get("why") if isinstance(obj, dict) else None), "s": round(time.monotonic() - t0, 1)}
    except Exception as exc:  # noqa: BLE001 - a lab probe records the failure, never raises
        return {"relation": None, "item": None, "why": "ERR %r" % (exc,), "s": round(time.monotonic() - t0, 1)}


def backstop(j: dict, take_row: dict, syn_stems: set) -> dict:
    """Deterministic check on an LLM 'uses_take' (the Black-Bear correction, J-3143): the quoted item must be in the
    take, absent from the input, and present in the synthesis, by stem overlap; otherwise the flag is dropped."""
    if j.get("relation") != "uses_take":
        return j
    item = content_stems(str(j.get("item") or ""))
    ok = bool(item & take_row["_take_novel"] & syn_stems)
    if not ok:
        j = dict(j, relation="no_take_content", backstop_dropped=True)
    return j


def take_text(r: dict) -> str:
    parts = ["literal ask: " + r["_ask"]]
    if r["_result"]:
        parts.append("candidate answer: " + r["_result"][:500])
    if r["_facts"]:
        parts.append("specifics: " + " | ".join(r["_facts"]))
    return "\n".join(parts)


def run_judge(rows: list[dict], url: str, model: str, n_total: int, n_ctrl: int, seed: int = SEED,
              partial: Path | None = None) -> dict:
    rng = random.Random(seed)
    cand = [r for r in rows if (r["has_result"] or r["n_facts"]) and r["_syn_text"]]
    strata = {}
    for r in cand:
        strata.setdefault((r["input_type"], r["era"]), []).append(r)
    keys = sorted(strata)
    per = max(1, n_total // len(keys))
    sample: list[dict] = []
    for k in keys:
        pool = strata[k]
        sample.extend(rng.sample(pool, min(per, len(pool))))
    # top up from whatever strata have spare rows, to reach n_total
    spare = [r for r in cand if r not in sample]
    rng.shuffle(spare)
    sample.extend(spare[: max(0, n_total - len(sample))])
    results = []
    for r in sample:
        j = backstop(judge_one(url, model, take_text(r), r["_syn_text"], r["_raw"]), r, r["_syn"])
        results.append({"cycle_id": r["cycle_id"], "input_type": r["input_type"], "era": r["era"], "kind": "real",
                        "cov_novel": r["cov_novel"], "excess": r["excess"], **j})
        if partial:  # a long local-CPU run: keep what is done if it is interrupted
            partial.write_text(json.dumps({"model": model, "real": results, "controls": []}, ensure_ascii=False), encoding="utf-8")
    ctrls = []
    for r in rng.sample(sample, min(n_ctrl, len(sample))):
        others = [o for o in cand if o["input_type"] == r["input_type"] and o is not r]
        o = rng.choice(others)
        j = backstop(judge_one(url, model, take_text(o), r["_syn_text"], r["_raw"]), o, r["_syn"])
        ctrls.append({"cycle_id": r["cycle_id"], "take_from": o["cycle_id"], "input_type": r["input_type"],
                      "kind": "mismatched_control", **j})
    return {"model": model, "url": url, "prompt_version": JUDGE_PROMPT_VERSION, "real": results, "controls": ctrls}


def judge_summary(j: dict) -> dict:
    def tally(rs):
        c = {"uses_take": 0, "no_take_content": 0, "contradicts_take": 0, "unparsed": 0}
        for x in rs:
            c[x["relation"] or "unparsed"] += 1
        return c
    out = {"model": j["model"], "prompt_version": j.get("prompt_version"), "real_all": tally(j["real"]), "controls": tally(j["controls"])}
    for typ in ("human", "internal"):
        for era in ("pre", "post"):
            rs = [x for x in j["real"] if x["input_type"] == typ and x["era"] == era]
            if rs:
                out["real_%s_%s" % (typ, era)] = tally(rs)
    bo = [x["cov_novel"] for x in j["real"] if x["relation"] == "uses_take" and x["cov_novel"] is not None]
    ig = [x["cov_novel"] for x in j["real"] if x["relation"] == "no_take_content" and x["cov_novel"] is not None]
    out["cov_novel_median_when_uses_take"] = pct(bo, .5)
    out["cov_novel_median_when_no_take_content"] = pct(ig, .5)
    out["backstop_dropped_real"] = sum(1 for x in j["real"] if x.get("backstop_dropped"))
    out["backstop_dropped_controls"] = sum(1 for x in j["controls"] if x.get("backstop_dropped"))
    return out


# ---------------------------------------------------------------- main
def _ts(d: str | None, default: float) -> float:
    return _dt.datetime.fromisoformat(d).timestamp() if d else default


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="executive.jsonl (default: ROOT/data/training, else the live tree, read-only)")
    ap.add_argument("--out-dir", default=None, help="where results are written (default: a fresh temp dir)")
    ap.add_argument("--split-date", default="2026-08-20", help="gemma4:12b swap (local time); pre/post strata")
    ap.add_argument("--from-date", default=None)
    ap.add_argument("--to-date", default=None)
    ap.add_argument("--dump-review", action="store_true", help="write the matched/unmatched rows to read by eye")
    ap.add_argument("--judge-url", default=None)
    ap.add_argument("--judge-model", default="falcon3:7b")
    ap.add_argument("--judge-n", type=int, default=60)
    ap.add_argument("--judge-controls", type=int, default=12)
    a = ap.parse_args()

    if a.judge_url and "10.1.1." in a.judge_url:
        sys.exit("refusing to call Ramses (10.1.1.x): it is the founder's gaming machine")
    data = Path(a.data) if a.data else (ROOT / "data" / "training" / "executive.jsonl")
    if not data.exists():
        data = LIVE_EXEC
    out_dir = Path(a.out_dir) if a.out_dir else Path(tempfile.mkdtemp(prefix="take_integration_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    split_ts = _ts(a.split_date, 0)
    lo, hi = _ts(a.from_date, 0), _ts(a.to_date, 1e12)

    rows: list[dict] = []
    seen_total = 0
    with open(data, encoding="utf-8") as fh:
        for line in fh:
            seen_total += 1
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not (lo <= (r.get("ts") or 0) < hi):
                continue
            row = analyse_row(r, split_ts)
            if row:
                rows.append(row)
    add_controls(rows)
    summary = {"data": str(data), "executive_rows_seen": seen_total, "take_rows": len(rows),
               "split_ts": split_ts, "window": [a.from_date, a.to_date], "min_novel": MIN_NOVEL, "n_control": N_CONTROL,
               "strata": summarise(rows)}
    if a.dump_review:
        review_dump(rows, out_dir / "review_rows.md")
    if a.judge_url:
        tag = "%s_%s" % (JUDGE_PROMPT_VERSION, re.sub(r"[^A-Za-z0-9]+", "_", a.judge_model))
        j = run_judge(rows, a.judge_url, a.judge_model, a.judge_n, a.judge_controls,
                      partial=out_dir / ("judge_results_%s.partial.json" % tag))
        (out_dir / ("judge_results_%s.json" % tag)).write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        summary["judge"] = judge_summary(j)
        (out_dir / ("judge_summary_%s.json" % tag)).write_text(json.dumps(summary["judge"], indent=1), encoding="utf-8")
    (out_dir / "baseline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    slim = [{k: v for k, v in r.items() if not k.startswith("_") and k != "substrate"} for r in rows]
    (out_dir / "baseline_rows.json").write_text(json.dumps(slim, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("wrote", out_dir)


if __name__ == "__main__":
    main()

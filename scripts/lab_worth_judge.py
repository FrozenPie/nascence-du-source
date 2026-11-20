"""
J-3253 (D-0642, plan curiosity_goals_dreams) - LAB: can the curiosity worth-judge (P-0049) discriminate?

Three offline replays of core/curiosity_worth.py's judge, on hand-labelled questions. NOTHING live is
touched: no core product code is edited, no Du store is opened for write. The only live read is a COPY of
data/frontier.json (copied to a temp dir first), used once to freeze real recent-agenda lists into
docs/lab/J-3253_data/agendas.json. Everything else is HTTP to the judge hubs and files under
docs/lab/J-3253_data/ of this worktree.

PRE-REGISTERED success measure (written before any judge was run; D-0642 + J-3253 briefing):
  a judge arm PASSES iff  (1) AUC(good vs bad) >= 0.80 on the hand-labelled set (borderline excluded), AND
                          (2) all four constructed controls score LOW:
                              absolute arms  : every control grade < 0.40  (the live gate's AIMLESS_BELOW)
                              pairwise arm   : every control win-rate < 0.35 against random opponents.
  Also reported (not part of pass): bootstrap 95% CI of the AUC, share of grades outside 0.8-0.9, number of
  distinct grade values, test-retest spread. Defeater (D-0642): if no arm separates good from bad better than
  the current judge, replace it with the deterministic redundancy/specificity check (d).

Arms (all use the UNCHANGED live _SYS imported from core.curiosity_worth, except the pairwise prompt):
  base : live shape. recent = the question + its 4 nearest sibling questions (token Jaccard) = the live
         "top-5 batch including itself" (F-3695). Approximation of the live condition.
  a    : same prompt, recent = 5 REAL recent-agenda questions from frontier.json (last_offered just before
         the question's own timestamp, itself excluded).
  a0   : same prompt, empty agenda (the question alone) - diagnostic only.
  b    : pairwise forced choice "which of A / B is more worth pursuing"; a circulant comparison design so
         every item meets 2*K opponents; score = win rate. Position of A/B randomised per comparison.
Judges: granite (the live judge, :11437) / mixtral (:11438) / gemma4:31b (local ollama :11433, Google,
third family vs writer command-r7b+qwen3.5 and vs granite) / phi4 (local :11433, Microsoft).

Usage (from the worktree root):
  python scripts/lab_worth_judge.py agendas                # one-time: freeze agendas from a COPY of frontier.json
  python scripts/lab_worth_judge.py run --judge granite --arms base,a,a0,b --repeats 2 --k 10
  python scripts/lab_worth_judge.py analyze                # writes docs/lab/J-3253_data/report.json + report.md
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import curiosity_worth as _cw          # read-only: the live _SYS constant, verbatim  # noqa: E402

OUT = ROOT / "docs" / "lab" / "J-3253_data"
LIVE_FRONTIER = Path("C:/Nascence/data/frontier.json")

PREREG = {"auc_min": 0.80, "control_abs_max": 0.40, "control_pair_max": 0.35}

JUDGES = {
    "granite": ("http://LAN-HOST:11437", "granite3.1-moe:3b"),
    "mixtral": ("http://LAN-HOST:11438", "mixtral:8x7b"),
    "gemma31": ("http://127.0.0.1:11433", "gemma4:31b"),
    "phi4":    ("http://127.0.0.1:11433", "phi4:latest"),
}

CONTROLS = [
    ("K_hello", "hello"),
    ("K_2plus2", "what is 2+2"),
    ("K_book", "What is a book?"),
    ("K_bluebird", "Bluebird's arrival rewrites the physical laws governing the Second Empire"),
]
CONTROL_TS = 1793600000.0          # ~2026-11-01, mid-window; the agenda for controls is taken as of then

PAIR_SYS = ("/no_think\nYou compare two questions for a mind seeking to understand the world and itself. "
            "Pick the one that is more genuinely WORTH PURSUING with its finite attention: interesting, "
            "generative, specific, opening real understanding - not trivial, idle, already-obvious, vague "
            "or a dead-end. Output ONLY JSON: {\"better\": \"<A or B>\", \"reason\": \"<one short phrase>\"}")


# EXPLORATORY arm r (NOT one of D-0642's three replays; written after partial main-set results were seen, from the
# labeller's own rubric, so its in-sample AUC on the main set is circular - only the hold-out AUC counts).
RUBRIC_SYS = ("/no_think\nYou judge whether a question is worth a mind's finite attention. WORTH PURSUING = it names a "
              "concrete, checkable particular (a person, event, text, place or thing) and can be answered by reading or "
              "observing something real. NOT WORTH PURSUING = generic or abstract, metaphor-only, a mash-up of unrelated "
              "sources, assumes a link nobody has shown, points at something unnamed (\"the story\", \"the letter\"), is "
              "trivial or already obvious, or repeats what was recently on the agenda. "
              "Output ONLY JSON: {\"interesting\": <a number 0.0-1.0>, \"reason\": \"<one short phrase>\"}")


# ----------------------------------------------------------------------------- data

def load_items(holdout: bool = False) -> list[dict]:
    """The pre-registered set (50 labelled + 4 controls). holdout=True appends the 40-item hold-out set
    (labelled blind to judge output; used only for the exploratory rubric arm r and for arm a comparison)."""
    items = json.loads((OUT / "labelled.json").read_text(encoding="utf-8"))["items"]
    for cid, q in CONTROLS:
        items.append({"id": cid, "q": q, "ts": CONTROL_TS, "label": "control", "set": "constructed control"})
    if holdout:
        items += json.loads((OUT / "holdout.json").read_text(encoding="utf-8"))["items"]
    return items


def _norm(q: str) -> str:
    return " ".join((q or "").lower().split())[:80]


def _toks(q: str) -> set:
    return set(re.findall(r"[\w']+", (q or "").lower()))


def jaccard(a: str, b: str) -> float:
    A, B = _toks(a), _toks(b)
    return len(A & B) / max(1, len(A | B))


def build_agenda(q: str, ts: float, frontier_qs: list[dict], n: int = 5) -> list[str]:
    """Five distinct real questions most recently OFFERED to Du before ts, excluding q itself."""
    me = _norm(q)
    cand = [x for x in frontier_qs
            if 0 < x.get("last_offered", 0) < ts
            and x.get("source") in ("curiosity", "asked", "intention", "pursuit", "prism", "dream")]
    cand.sort(key=lambda x: x["last_offered"], reverse=True)
    out, seen = [], {me}
    for x in cand:
        k = _norm(x.get("q", ""))
        if k in seen:
            continue
        seen.add(k)
        out.append(x["q"])
        if len(out) >= n:
            break
    return out


def build_siblings(items: list[dict], n: int = 4) -> dict:
    """base arm batch: the question's n nearest other questions in the pool by token Jaccard."""
    sib = {}
    for it in items:
        others = sorted((o for o in items if o["id"] != it["id"]), key=lambda o: jaccard(it["q"], o["q"]), reverse=True)
        sib[it["id"]] = [o["q"] for o in others[:n]]
    return sib


def cmd_agendas(_a) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="J3253_"))
    cp = tmp / "frontier.json"
    shutil.copyfile(LIVE_FRONTIER, cp)                       # copy first; never open the live file for anything else
    fq = json.loads(cp.read_text(encoding="utf-8"))["questions"]
    items = load_items(holdout=True)
    prev = json.loads((OUT / "agendas.json").read_text(encoding="utf-8")) if (OUT / "agendas.json").exists() else None
    if prev:                                                  # additive: never change an already-frozen agenda/sibling set
        ag, sib = prev["agenda"], prev["siblings"]
        for it in items:
            if it["id"] not in ag:
                ag[it["id"]] = build_agenda(it["q"], it["ts"], fq)
    else:
        main = load_items()
        ag = {it["id"]: build_agenda(it["q"], it["ts"], fq) for it in main}
        sib = build_siblings(main)
    (OUT / "agendas.json").write_text(json.dumps({"agenda": ag, "siblings": sib, "frontier_rows": len(fq),
                                                  "frozen_at": (prev or {}).get("frozen_at", time.time())},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print("agendas frozen:", len(ag), "items; frontier rows", len(fq))
    shutil.rmtree(tmp, ignore_errors=True)


# ----------------------------------------------------------------------------- judge calls

def user_msg(q: str, recent: list[str]) -> str:
    """Byte-identical to the user message core.curiosity_worth.grade builds."""
    return (f"Question: {(q or '')[:200]}\n\nRecently on the agenda (judge redundancy / aimlessness):\n"
            + "\n".join(f"- {(r or '')[:80]}" for r in (recent or [])[:6]))


def pair_msg(a: str, b: str) -> str:
    return f"Question A: {a[:200]}\n\nQuestion B: {b[:200]}"


def parse_json(text: str) -> dict:
    t = (text or "").strip()
    t = re.sub(r"<think>.*?</think>", "", t, flags=re.S).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"\{.*?\}", t, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


def grade_value(data: dict):
    raw = (data or {}).get("interesting", None)
    if isinstance(raw, dict):
        raw = next((v for v in raw.values() if isinstance(v, (int, float)) and not isinstance(v, bool)), None)
    try:
        return max(0.0, min(1.0, float(raw)))
    except Exception:
        return None


def chat(judge: str, system: str, user: str, max_tokens: int = 80, retries: int = 3) -> str:
    import requests
    url, model = JUDGES[judge]
    payload = {"model": model, "stream": False, "think": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.2, "num_predict": max_tokens, "num_ctx": 4096}}
    last = ""
    for i in range(retries):
        try:
            r = requests.post(url + "/api/chat", json=payload, timeout=600)
            r.raise_for_status()
            return (r.json().get("message") or {}).get("content") or ""
        except Exception as e:                                  # noqa: BLE001
            last = f"ERR {e}"
            time.sleep(3 * (i + 1))
    return last


def pair_design(ids: list[str], k: int, seed: int = 7) -> list[tuple[str, str]]:
    """Circulant design on a shuffled ring: K distinct offsets, so each item meets 2K opponents."""
    rng = random.Random(seed)
    ring = ids[:]
    rng.shuffle(ring)
    n = len(ring)
    offs = rng.sample(range(1, n // 2 + 1), k)
    pairs = []
    for d in offs:
        for i in range(n):
            a, b = ring[i], ring[(i + d) % n]
            pairs.append((a, b) if rng.random() < 0.5 else (b, a))     # randomise A/B position
    return pairs


def parse_better(val) -> str | None:
    """'A' / 'B' from a pairwise verdict; accepts 'A', 'Question A', 'option b' ... (granite answers 'Question A')."""
    m = re.search(r"(?<![A-Z])([AB])(?![A-Z])", str(val or "").upper())
    return m.group(1) if m else None


def done_keys(path: Path) -> set:
    """Keys already run. A pairwise row with no parsed winner is NOT done (the first parser dropped 'Question A')."""
    s = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                if r.get("arm") == "b" and r.get("winner") is None:
                    continue
                if str(r.get("raw") or "").startswith("ERR"):      # transport failure after retries: run it again
                    continue
                s.add(r["key"])
            except Exception:
                pass
    return s


def cmd_run(a) -> None:
    items = load_items(holdout=a.holdout)                      # default: main set only (pairwise design is built on it)
    byid = {it["id"]: it for it in items}
    ag = json.loads((OUT / "agendas.json").read_text(encoding="utf-8"))
    path = OUT / f"runs_{a.judge}.jsonl"
    seen = done_keys(path)
    arms = a.arms.split(",")
    f = open(path, "a", encoding="utf-8")

    def emit(rec):
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()

    t0 = time.time()
    n = 0
    for arm in [x for x in arms if x in ("base", "a", "a0", "r")]:
        for rep in range(a.repeats):
            for it in items:
                key = f"{arm}|{it['id']}|{rep}"
                if key in seen:
                    continue
                recent = ({"base": lambda: [it["q"]] + ag["siblings"][it["id"]], "a": lambda: ag["agenda"][it["id"]],
                           "a0": lambda: [], "r": lambda: ag["agenda"][it["id"]]})[arm]()
                raw = chat(a.judge, RUBRIC_SYS if arm == "r" else _cw._SYS, user_msg(it["q"], recent))
                d = parse_json(raw)
                emit({"key": key, "arm": arm, "id": it["id"], "rep": rep, "value": grade_value(d),
                      "reason": str(d.get("reason", ""))[:100], "raw": None if d else raw[:200]})
                n += 1
        print(f"[{a.judge}] arm {arm} done, {n} calls, {time.time()-t0:.0f}s", flush=True)
    if "b" in arms:
        assert not a.holdout, "pairwise design is defined on the main set only"
        pairs = pair_design([it["id"] for it in items], a.k)
        for j, (x, y) in enumerate(pairs):
            key = f"b2|{x}|{y}"
            if key in seen:
                continue
            raw = chat(a.judge, PAIR_SYS, pair_msg(byid[x]["q"], byid[y]["q"]))
            d = parse_json(raw)
            w = parse_better(d.get("better"))
            emit({"key": key, "arm": "b", "v": 2, "A": x, "B": y, "winner": (x if w == "A" else y if w == "B" else None),
                  "better": str(d.get("better", ""))[:40], "chose_position": w,
                  "reason": str(d.get("reason", ""))[:100], "raw": None if d else raw[:200]})
            n += 1
            if j % 50 == 0:
                print(f"[{a.judge}] pair {j}/{len(pairs)} {time.time()-t0:.0f}s", flush=True)
    f.close()
    print(f"[{a.judge}] finished {n} new calls in {time.time()-t0:.0f}s", flush=True)


# ----------------------------------------------------------------------------- analysis

def auc(pos: list[float], neg: list[float]) -> float:
    if not pos or not neg:
        return float("nan")
    s = 0.0
    for p in pos:
        for q in neg:
            s += 1.0 if p > q else 0.5 if p == q else 0.0
    return s / (len(pos) * len(neg))


def boot_ci(pos, neg, n=2000, seed=3):
    rng = random.Random(seed)
    xs = []
    for _ in range(n):
        p = [rng.choice(pos) for _ in pos]
        q = [rng.choice(neg) for _ in neg]
        xs.append(auc(p, q))
    xs.sort()
    return xs[int(0.025 * n)], xs[int(0.975 * n)]


def scores_for(judge: str, arm: str, items: list[dict]) -> dict:
    """item id -> score (mean over repeats for absolute arms; win rate for pairwise). Missing -> None."""
    path = OUT / f"runs_{judge}.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []
    rows = [r for r in rows if r["arm"] == arm and (arm != "b" or r.get("v") == 2)]   # v1 pairwise rows (parser bug) ignored
    if arm == "b":
        w, g = {}, {}
        for r in rows:
            if r.get("winner") is None:
                continue
            for z in (r["A"], r["B"]):
                g[z] = g.get(z, 0) + 1
            w[r["winner"]] = w.get(r["winner"], 0) + 1
        return {it["id"]: (w.get(it["id"], 0) / g[it["id"]] if g.get(it["id"]) else None) for it in items}
    vals: dict = {}
    for r in rows:
        if r["value"] is not None:
            vals.setdefault(r["id"], []).append(r["value"])
    return {it["id"]: (sum(vals[it["id"]]) / len(vals[it["id"]]) if vals.get(it["id"]) else None) for it in items}


def analyze_arm(judge: str, arm: str, items: list[dict], tag: str = "main") -> dict | None:
    sc = scores_for(judge, arm, items)
    if not any(v is not None for v in sc.values()):
        return None
    pos = [sc[i["id"]] for i in items if i["label"] == "good" and sc[i["id"]] is not None]
    neg = [sc[i["id"]] for i in items if i["label"] == "bad" and sc[i["id"]] is not None]
    bor = [sc[i["id"]] for i in items if i["label"] == "borderline" and sc[i["id"]] is not None]
    ctl = {i["id"]: sc[i["id"]] for i in items if i["label"] == "control"}
    lo, hi = boot_ci(pos, neg) if pos and neg else (float("nan"),) * 2
    A = auc(pos, neg)
    thr = PREREG["control_pair_max"] if arm == "b" else PREREG["control_abs_max"]
    ctl_low = all(v is not None and v < thr for v in ctl.values())
    allv = [v for i in items if (v := sc[i["id"]]) is not None]
    out_of_band = (sum(1 for v in allv if not (0.8 - 1e-9 <= v <= 0.9 + 1e-9)) / len(allv)) if allv else None
    # per-run raw absolute grades (not repeat-averaged) for the live-comparable band statistic
    raw_vals = []
    if arm != "b":
        path = OUT / f"runs_{judge}.jsonl"
        for l in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if r["arm"] == arm and r["value"] is not None and r["id"] in {i["id"] for i in items}:
                raw_vals.append(r["value"])
    band = (sum(1 for v in raw_vals if 0.8 - 1e-9 <= v <= 0.9 + 1e-9) / len(raw_vals)) if raw_vals else None
    mean = lambda xs: (sum(xs) / len(xs)) if xs else None   # noqa: E731
    return {"judge": judge, "arm": arm, "set": tag, "n_good": len(pos), "n_bad": len(neg), "n_border": len(bor),
            "auc": round(A, 3), "auc_ci95": [round(lo, 3), round(hi, 3)],
            "mean_good": round(mean(pos), 3) if pos else None, "mean_bad": round(mean(neg), 3) if neg else None,
            "mean_border": round(mean(bor), 3) if bor else None,
            "controls": {k: (round(v, 3) if v is not None else None) for k, v in ctl.items()},
            "controls_low": ctl_low, "share_raw_grades_in_0.8_0.9": round(band, 3) if band is not None else None,
            "distinct_raw_values": len({round(v, 2) for v in raw_vals}) if raw_vals else None,
            "PASS": bool(A >= PREREG["auc_min"] and ctl_low)}


def deterministic_features(items: list[dict], agenda: dict) -> list[dict]:
    """(d) probes: cheap deterministic scores, AUC on the same labels. Features fixed here before looking at AUC."""
    rel = re.compile(r"\b(reflect|reveal|shape|influence|impact|contribute|alter|relate|rewrite|transform)\w*", re.I)

    def proper(q):
        ws = re.findall(r"\b[A-Z][a-z]{2,}\b", q)
        return len(ws) - (1 if ws and q.strip().startswith(ws[0]) else 0)

    feats = {
        "proper_nouns": lambda it: float(proper(it["q"])),
        "digit_or_quote": lambda it: 1.0 if re.search(r"\d|'[^']{3,}'|\"[^\"]{3,}\"", it["q"]) else 0.0,
        "no_relation_verb": lambda it: 0.0 if rel.search(it["q"]) else 1.0,
        "low_redundancy": lambda it: 1.0 - max([jaccard(it["q"], r) for r in agenda.get(it["id"], [])] or [0.0]),
        "word_count": lambda it: float(len(it["q"].split())),
        "specificity_combo": lambda it: float(proper(it["q"]) > 0) + (1.0 if re.search(r"\d|'[^']{3,}'", it["q"]) else 0.0)
                                        + (0.0 if rel.search(it["q"]) else 1.0),
    }
    res = []
    for name, fn in feats.items():
        pos = [fn(i) for i in items if i["label"] == "good"]
        neg = [fn(i) for i in items if i["label"] == "bad"]
        ctl = {i["id"]: fn(i) for i in items if i["label"] == "control"}
        lo, hi = boot_ci(pos, neg)
        res.append({"feature": name, "auc": round(auc(pos, neg), 3), "auc_ci95": [round(lo, 3), round(hi, 3)],
                    "controls": ctl})
    return res


def cmd_analyze(_a) -> None:
    items = load_items()
    hold = [i for i in load_items(holdout=True) if i["id"].startswith("H")]
    ag = json.loads((OUT / "agendas.json").read_text(encoding="utf-8"))
    rows = []
    for judge in JUDGES:
        for arm in ("base", "a", "a0", "b", "r"):
            r = analyze_arm(judge, arm, items)
            if r:
                rows.append(r)
            if arm in ("a", "r") and hold:
                # hold-out: good vs bad on H items only; the controls come from the main run of the same arm
                ctl = [i for i in items if i["label"] == "control"]
                rh = analyze_arm(judge, arm, hold + ctl, tag="holdout")
                if rh and rh["n_good"] and rh["n_bad"]:
                    rows.append(rh)
                    rp = analyze_arm(judge, arm, items + hold, tag="pooled(main+holdout)")
                    if rp:
                        rows.append(rp)
    det = deterministic_features(items, ag["agenda"])
    det_h = deterministic_features(hold + [i for i in items if i["label"] == "control"], ag["agenda"]) if hold else []
    rep = {"prereg": PREREG, "counts": {l: sum(1 for i in items if i["label"] == l) for l in ("good", "bad", "borderline", "control")},
           "arms": rows, "deterministic_d": det, "deterministic_d_holdout": det_h, "any_pass": any(r["PASS"] for r in rows)}
    (OUT / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# J-3253 worth-judge lab report\n", f"counts {rep['counts']}  prereg {PREREG}\n",
             "| judge | arm/set | AUC [95% CI] | mean good / bad / border | controls (hello, 2+2, book, bluebird) | raw in 0.8-0.9 | distinct | PASS |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c = r["controls"]
        lines.append(f"| {r['judge']} | {r['arm']}/{r['set']} | {r['auc']} [{r['auc_ci95'][0]}, {r['auc_ci95'][1]}] | "
                     f"{r['mean_good']} / {r['mean_bad']} / {r['mean_border']} | "
                     f"{c.get('K_hello')}, {c.get('K_2plus2')}, {c.get('K_book')}, {c.get('K_bluebird')} | "
                     f"{r['share_raw_grades_in_0.8_0.9']} | {r['distinct_raw_values']} | {r['PASS']} |")
    lines += ["", "## (d) deterministic probes (features fixed in code before any AUC was computed)",
              "| feature | AUC main [95% CI] | AUC hold-out [95% CI] |", "|---|---|---|"]
    hmap = {d["feature"]: d for d in det_h}
    for d in det:
        h = hmap.get(d["feature"])
        lines.append(f"| {d['feature']} | {d['auc']} [{d['auc_ci95'][0]}, {d['auc_ci95'][1]}] | "
                     + (f"{h['auc']} [{h['auc_ci95'][0]}, {h['auc_ci95'][1]}]" if h else "n/a") + " |")
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def cmd_diag(_a) -> None:
    """Parse-failure rates, test-retest, and the items each judge gets most wrong (arm a, main set)."""
    items = load_items(holdout=True)
    byid = {i["id"]: i for i in items}
    out = []
    for judge in JUDGES:
        path = OUT / f"runs_{judge}.jsonl"
        if not path.exists():
            continue
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        for arm in ("base", "a", "a0", "r"):
            rr = [r for r in rows if r["arm"] == arm]
            if rr:
                out.append(f"{judge}/{arm}: {len(rr)} grades, parse-failed {sum(1 for r in rr if r['value'] is None)}")
        pr = [r for r in rows if r["arm"] == "b" and r.get("v") == 2]
        if pr:
            pos = [r.get("chose_position") for r in pr if r.get("chose_position")]
            out.append(f"{judge}/b position bias: chose A in {sum(1 for x in pos if x == 'A')} of {len(pos)} parsed comparisons")
        if pr:
            out.append(f"{judge}/b: {len(pr)} comparisons, no-winner {sum(1 for r in pr if r.get('winner') is None)}")
        for arm in ("a", "base", "r"):
            by = {}
            for r in rows:
                if r["arm"] == arm and r["value"] is not None:
                    by.setdefault(r["id"], {})[r["rep"]] = r["value"]
            d = [abs(v[0] - v[1]) for v in by.values() if 0 in v and 1 in v]
            if d:
                out.append(f"{judge}/{arm} test-retest: mean |rep0-rep1| {sum(d)/len(d):.3f} over {len(d)} items, identical {sum(1 for x in d if x == 0)}")
        sc = scores_for(judge, "a", [i for i in items if not i["id"].startswith("H")])
        bad = sorted(((sc[i["id"]], i) for i in items if i["label"] == "bad" and sc.get(i["id"]) is not None), key=lambda t: -t[0])[:4]
        good = sorted(((sc[i["id"]], i) for i in items if i["label"] == "good" and sc.get(i["id"]) is not None), key=lambda t: t[0])[:4]
        if bad:
            out.append(f"{judge}/a highest-scored BAD:  " + " | ".join(f"{v:.2f} {i['q'][:70]}" for v, i in bad))
            out.append(f"{judge}/a lowest-scored GOOD:  " + " | ".join(f"{v:.2f} {i['q'][:70]}" for v, i in good))
    text = chr(10).join(out)
    (OUT / "diag.txt").write_text(text + chr(10), encoding="utf-8")
    print(text)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("agendas").set_defaults(fn=cmd_agendas)
    r = sub.add_parser("run")
    r.add_argument("--judge", required=True, choices=list(JUDGES))
    r.add_argument("--arms", default="base,a,a0,b")
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--k", type=int, default=5)
    r.add_argument("--holdout", action="store_true", help="also run on the 40-item hold-out set (arms a, r only)")
    r.set_defaults(fn=cmd_run)
    sub.add_parser("analyze").set_defaults(fn=cmd_analyze)
    sub.add_parser("diag").set_defaults(fn=cmd_diag)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

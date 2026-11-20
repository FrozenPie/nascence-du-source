"""Score the model x station matrix from saved raw output — nothing re-queried.

**There is deliberately NO overall score.** A composite would collapse exactly the information the
matrix exists to show: that a model good at picking is not thereby good at authoring. Two prior labs
in this codebase produced misleading single rankings, and both were only caught because raw output
was kept and re-scored.

Every metric here is a COUNT or a MATCH — nothing requires judgement. Where a station's quality
genuinely needs judgement (is this insight good? is this prose worth reading?), it is left to a
separate decoupled-judge pass rather than approximated by a heuristic that would look authoritative
and be wrong.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scripts.station_suite import ORDER, TASKS  # noqa: E402

RAW = ROOT / "data" / "lab" / "station_bench" / "raw.json"
SCORES = ROOT / "data" / "lab" / "station_bench" / "scores.json"
REPORT = ROOT / "docs" / "lab" / "station_bench.md"


def parse(raw: str):
    """Tolerant JSON extraction — the same courtesy production gives.

    A model must not be scored zero for wrapping valid JSON in a code fence; that mistake was made
    once here already and wrongly condemned the best candidate on the task.
    """
    if not raw:
        return None
    s = raw.strip()
    if "```" in s:
        m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S)
        if m:
            s = m.group(1).strip()
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        # strict=False (fixed 2026-08-20): glm4:9b wraps prose with a literal, unescaped newline
        # BYTE inside a JSON string value, not an escaped backslash-n sequence. That is invalid under
        # strict JSON but is exactly what strict=False exists to tolerate. Without this, glm4:9b
        # scored json_ok=0.0 on the author station -- a scorer bug, not a model failure. Confirmed
        # bounded: of 6 rows failing to parse across the whole 37-model matrix, only glm4:9b's 3
        # were a control-character issue; the other 3 (llama3.2:1b, tinyllama x2) are genuinely
        # malformed JSON from weaker models and strict=False does not and should not rescue them.
        return json.loads(s[i:j + 1], strict=False)
    except Exception:
        return None


def _norm(x) -> str:
    return " ".join(str(x).lower().split())


def score_pick(runs, t):
    objs = [parse(r.get("raw", "")) for r in runs if r.get("ok")]
    good = [o for o in objs if isinstance(o, dict)]
    picks = [str(o.get("peer", "")).strip().upper() for o in good]
    valid = [p for p in picks if p in t["allowed"]]
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            "valid_pick": round(len(valid) / max(1, len(picks)), 2) if picks else 0.0,
            # temp 0.0 SHOULD be deterministic; drift means the station cannot be relied on to route
            # the same way twice given the same world.
            "determinism": round(1.0 if picks and len(set(picks)) == 1 else 0.0, 2),
            "brevity": round(sum(1 for o in good if len(str(o.get("why", "")).split()) <= 14)
                             / max(1, len(good)), 2),
            "picked": picks[0] if picks else None}


def score_extract(runs, t):
    objs = [parse(r.get("raw", "")) for r in runs if r.get("ok")]
    good = [o for o in objs if isinstance(o, dict)]
    subs = [o.get("subjects") for o in good if isinstance(o.get("subjects"), list)]
    inrange = [s for s in subs if 2 <= len(s) <= 4]
    flat = [_norm(x) for s in subs for x in s]
    rel = sum(1 for x in flat if any(g in x for g in t["gold_terms"]))
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            "count_in_range": round(len(inrange) / max(1, len(subs)), 2) if subs else 0.0,
            "relevance": round(rel / max(1, len(flat)), 2) if flat else 0.0,
            # a "subject heading" that is a full sentence is prose wearing a list's clothes
            "not_prose": round(sum(1 for x in flat if len(x.split()) <= 8) / max(1, len(flat)), 2)
            if flat else 0.0}


def score_judge(runs, t):
    objs = [(parse(r.get("raw", "")), r.get("gold")) for r in runs if r.get("ok")]
    good = [(o, g) for o, g in objs if isinstance(o, dict) and "defeated" in o]
    correct = sum(1 for o, g in good if bool(o.get("defeated")) == bool(g))
    confs = [float(o.get("confidence", 0)) for o, _ in good
             if isinstance(o.get("confidence"), (int, float))]
    # Calibration: mean confidence on the ones it got WRONG. High = confidently wrong, the worst mode.
    wrong_conf = [float(o.get("confidence", 0)) for o, g in good
                  if bool(o.get("defeated")) != bool(g) and isinstance(o.get("confidence"), (int, float))]
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            "accuracy": round(correct / max(1, len(good)), 2) if good else 0.0,
            "commits": round(len(good) / max(1, len(runs)), 2),
            "mean_conf": round(sum(confs) / len(confs), 2) if confs else None,
            "conf_when_wrong": round(sum(wrong_conf) / len(wrong_conf), 2) if wrong_conf else None}


def score_ground(runs, t):
    objs = [parse(r.get("raw", "")) for r in runs if r.get("ok")]
    good = [o for o in objs if isinstance(o, dict)]
    whys = [_norm(o.get("why", "")) for o in good]
    clean = sum(1 for w in whys if not any(f in w for f in t["forbidden"]))
    ids = [o.get("evidence_used") for o in good if isinstance(o.get("evidence_used"), list)]
    valid_ids = sum(1 for lst in ids if lst and all(str(x).upper() in t["valid_ids"] for x in lst))
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            # THE metric for this station: did it invent a cause the evidence never offered?
            "groundedness": round(clean / max(1, len(whys)), 2) if whys else 0.0,
            "cites_valid_ids": round(valid_ids / max(1, len(ids)), 2) if ids else 0.0}


def score_synthesise(runs, t):
    objs = [parse(r.get("raw", "")) for r in runs if r.get("ok")]
    good = [o for o in objs if isinstance(o, dict)]
    covs = []
    for o in good:
        blob = _norm(str(o.get("insight", "")) + " " + str(o.get("tension", "")))
        hit = sum(1 for terms in t["coverage_terms"].values()
                  if any(term in blob for term in terms))
        covs.append(hit / len(t["coverage_terms"]))
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            # Separates integration from fluent generality: a lovely sentence about "loss and time"
            # that touches none of the seven specifics scores low, which is correct.
            "coverage": round(sum(covs) / len(covs), 2) if covs else 0.0,
            "names_tension": round(sum(1 for o in good if str(o.get("tension", "")).strip())
                                   / max(1, len(good)), 2)}


def score_predict(runs, t):
    objs = [parse(r.get("raw", "")) for r in runs if r.get("ok")]
    good = [o for o in objs if isinstance(o, dict)]
    exp = [_norm(o.get("expect_next", "")) for o in good if str(o.get("expect_next", "")).strip()]
    hedged = sum(1 for e in exp if any(h in e for h in t["hedge"]))
    static = sum(1 for e in exp if any(s in e for s in t["static"]))
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            # A prediction hedged into unfalsifiability fails exactly as a question does.
            "falsifiable": round(1 - hedged / max(1, len(exp)), 2) if exp else 0.0,
            "variety": round(len(set(exp)) / max(1, len(exp)), 2) if exp else 0.0,
            "not_static": round(1 - static / max(1, len(exp)), 2) if exp else 0.0}


def score_voice(runs, t):
    objs = [parse(r.get("raw", "")) for r in runs if r.get("ok")]
    good = [o for o in objs if isinstance(o, dict)]
    th = [_norm(o.get("thought", "")) for o in good if str(o.get("thought", "")).strip()]
    tells = sum(1 for x in th if any(a in x for a in t["assistant_tells"]))
    first = sum(1 for x in th if re.search(r"\bi\b|\bmy\b|\bme\b", x))
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            # The real failure at this station: reverting to assistant register.
            "in_character": round(1 - tells / max(1, len(th)), 2) if th else 0.0,
            "first_person": round(first / max(1, len(th)), 2) if th else 0.0,
            "variety": round(len(set(th)) / max(1, len(th)), 2) if th else 0.0}


def score_author(runs, t):
    objs = [parse(r.get("raw", "")) for r in runs if r.get("ok")]
    good = [o for o in objs if isinstance(o, dict)]
    secs = [str(o.get("section", "")) for o in good if str(o.get("section", "")).strip()]
    words = [len(s.split()) for s in secs]
    listy = sum(1 for s in secs if len(re.findall(r"^\s*[-*\d]+[.)]?\s", s, re.M)) >= 3)
    reps = []
    for s in secs:
        w = _norm(s).split()
        grams = [" ".join(w[i:i + 5]) for i in range(max(0, len(w) - 4))]
        reps.append(1 - len(set(grams)) / len(grams) if grams else 0.0)
    theme = sum(1 for s in secs if re.search(r"eros|water|sea|mov|taken|land", _norm(s)))
    return {"json_ok": round(len(good) / max(1, len(runs)), 2),
            "words_med": sorted(words)[len(words) // 2] if words else 0,
            # asked for 4-6 paragraphs; ~250 words is the floor for that being true
            "length_achieved": round(sum(1 for w in words if w >= 250) / max(1, len(words)), 2)
            if words else 0.0,
            "not_a_list": round(1 - listy / max(1, len(secs)), 2) if secs else 0.0,
            "repetition": round(sum(reps) / len(reps), 3) if reps else None,
            "continues_theme": round(theme / max(1, len(secs)), 2) if secs else 0.0}


SCORERS = {"pick": score_pick, "extract": score_extract, "judge": score_judge,
           "ground": score_ground, "synthesise": score_synthesise, "predict": score_predict,
           "voice": score_voice, "author": score_author}


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    table: dict = {}
    for model, tasks in raw.items():
        if "_error" in tasks:
            table[model] = {"_error": tasks["_error"]}
            continue
        row = {}
        for tname in ORDER:
            runs = tasks.get(tname) or []
            if not runs:
                continue
            m = SCORERS[tname](runs, TASKS[tname])
            wall = [r["wall"] for r in runs if r.get("ok")]
            m["wall_med"] = sorted(wall)[len(wall) // 2] if wall else None
            m["empty_but_thinking"] = sum(1 for r in runs
                                          if r.get("ok") and not r.get("raw") and r.get("had_thinking"))
            row[tname] = m
        table[model] = row
    SCORES.write_text(json.dumps(table, indent=1), encoding="utf-8")

    for tname in ORDER:
        print(f"\n### {tname}  ({TASKS[tname]['station']})")
        keys = [k for k in TASKS[tname]["scored"]]
        print("  " + "model".ljust(24) + "  ".join(k[:12].rjust(13) for k in keys) + "     wall")
        rows = [(m, r[tname]) for m, r in table.items() if tname in r]
        for m, s in sorted(rows, key=lambda x: -sum(v for v in x[1].values()
                                                    if isinstance(v, (int, float)))):
            vals = "  ".join(str(s.get(k, "—"))[:12].rjust(13) for k in keys)
            print(f"  {m[:23].ljust(24)}{vals}   {s.get('wall_med')}s")
    print(f"\nscores -> {SCORES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

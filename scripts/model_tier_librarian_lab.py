"""
Nascence — MODEL-TIER LAB #5: core.librarian.subjects_for vs mixtral:8x7b (2026-08-25)

J-0254 (source: decision:D-0013), scoped by docs/lab/model_tier_lab_scope_2026-08-25.md section 2,
row 5. Scope's own instruction: "core/librarian.py's own pre-registered hit-rate metric ... is the
right score — run real carried-questions through both and compare hit-rate directly, not a proxy."

WHAT THIS TESTS. `subjects_for()` (core/librarian.py:125) maps a carried QUESTION to 3-6 catalogue
subject headings via `_SYSTEM` (imported LIVE below), currently `falcon3:7b` primary / `gemma4:12b`
fallback on local hubs (:11440/:11439). `search_by_subjects()` then turns headings into real rows from
the 55,905-book SPGC catalogue CSV. `status()`'s pre-registered R1 metric is exactly: fraction of
asks returning >=1 real candidate (`n_hits > 0`).

REAL QUESTIONS, NOT SYNTHETIC. All 15 rows in `data/librarian_log.jsonl` (the entire real ask history
to date) are used verbatim — every real carried question the production librarian has ever been asked.
No question was invented for this lab.

WHAT'S BEING COMPARED, APPLES TO APPLES. Rather than trust the historical log's own hit-rate number
(recorded under whatever exact hub state existed on each of those 15 real days), BOTH the current
incumbent (`falcon3:7b`) and the candidate (`mixtral:8x7b`) are run TODAY, right now, against the SAME
15 real questions and the SAME (static) catalogue CSV, through the SAME `search_by_subjects()` call
production uses — so any difference is the model, not drift in the catalogue or the hub.

ISOLATION. `search_by_subjects()` reads ONLY `C:\\Knowledge\\SPGC-metadata-2018-07-18.csv` (a static
external catalogue file, not Nascence state) plus `core.reading_history.shelf_keys()`/`is_known()`
(read-only — verified by reading both function bodies before use: neither opens a file for writing).
Neither touches `nascence.db` or any live Du state file. This lab therefore makes ZERO live-state
writes and needed no `lab_env.isolate()` wrapper for the DB itself — confirmed by re-checking
`nascence.db`'s mtime and `data/librarian_log.jsonl`'s line count immediately after the run (this
script never calls `librarian.ask()` or anything that appends to that log — only `subjects_for()`'s
system prompt is imported, and `search_by_subjects()` is called directly, bypassing `librarian.ask()`'s
own `_LOG` write entirely).

DU-STOPPED NOTE: same disclosed deviation as the commitment_ledger lab (Du was live throughout) —
see that script's docstring for why this only threatens latency measurement, not hit-rate/accuracy.

CONTRACT: read-only against Ramses + a static local CSV. Writes ONLY to
data/lab/model_tier/librarian/ + docs/lab/model_tier_librarian.md.
"""
from __future__ import annotations

import asyncio
import json
import statistics as st
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = ROOT / "data" / "lab" / "model_tier" / "librarian"
REPORT = ROOT / "docs" / "lab" / "model_tier_librarian.md"
LOG = ROOT / "data" / "librarian_log.jsonl"

CANDIDATES = [
    ("falcon3:7b", "http://127.0.0.1:11440"),   # current production primary (core/librarian.py:_HUBS[0])
    ("mixtral:8x7b", "http://LAN-HOST:11438"),  # the candidate this lab exists to test
]
TIMEOUT_S = 90
MAX_TOKENS = 120     # matches the real call: max_tokens=120 at librarian.py:135
TEMP = 0.0           # matches the real call: temperature=0.0


def _system() -> str:
    from core.librarian import _SYSTEM
    return _SYSTEM


def _real_questions() -> list[dict]:
    """Every real question ever asked, verbatim, from the live production log — read-only."""
    qs = []
    for line in open(LOG, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        qs.append({"question": ev["question"], "prod_subjects": ev.get("subjects") or [],
                   "prod_n_hits": ev.get("n_hits", 0), "ts": ev.get("ts")})
    return qs


def _post(url: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _ask_model(base: str, model: str, system: str, question: str) -> dict:
    body = {"model": model, "stream": False, "keep_alive": "10m", "format": "json", "think": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": question}],
            "options": {"temperature": TEMP, "num_predict": MAX_TOKENS}}
    t0 = time.time()
    try:
        d = _post(base + "/api/chat", body, TIMEOUT_S)
    except Exception as e:
        return {"ok": False, "why": repr(e)[:120], "wall": round(time.time() - t0, 1)}
    msg = d.get("message") or {}
    raw = msg.get("content") or ""
    return {"ok": True, "wall": round(time.time() - t0, 1), "raw": raw}


def _parse_subjects(raw: str) -> list[str]:
    try:
        v = json.loads(raw or "")
        return [s.strip() for s in (v.get("subjects") or []) if isinstance(s, str) and 2 < len(s.strip()) < 60][:6]
    except Exception:
        return []


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    from core import library_hand as _lib     # search_by_subjects — read-only, see module docstring

    system = _system()
    questions = _real_questions()
    print(f"{len(questions)} real carried questions loaded from {LOG}", flush=True)

    raw_path = OUT_DIR / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}

    for model, base in CANDIDATES:
        print(f"=== {model} @ {base} ===", flush=True)
        runs = []
        for q in questions:
            r = _ask_model(base, model, system, q["question"])
            subs = _parse_subjects(r.get("raw", "")) if r.get("ok") else []
            hits = _lib.search_by_subjects(subs, 8) if subs else []
            rec = {"question": q["question"], "prod_subjects": q["prod_subjects"],
                  "prod_n_hits": q["prod_n_hits"], "model_subjects": subs, "model_n_hits": len(hits),
                  "model_titles": [h["title"][:60] for h in hits[:5]], "wall": r.get("wall"),
                  "ok": r.get("ok"), "raw": r.get("raw", "")[:200]}
            runs.append(rec)
            print(f"  '{q['question'][:50]}' -> {subs[:3]} -> {len(hits)} hits "
                  f"(prod had {q['prod_n_hits']})", flush=True)
        raw[model] = runs
        raw_path.write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {raw_path}")


def score() -> None:
    raw = json.loads((OUT_DIR / "raw.json").read_text(encoding="utf-8"))
    rows = []
    for model, runs in raw.items():
        n = len(runs)
        ok = [r for r in runs if r.get("ok")]
        hit = sum(1 for r in runs if r.get("model_n_hits", 0) > 0)
        empty_subjects = sum(1 for r in runs if not r.get("model_subjects"))
        walls = [r["wall"] for r in ok if r.get("wall") is not None]
        rows.append({
            "model": model, "n": n, "format_ok": len(ok),
            "hit_rate": round(hit / n, 3) if n else 0.0,
            "empty_subjects_rate": round(empty_subjects / n, 3) if n else 0.0,
            "latency_med": round(st.median(walls), 2) if walls else None,
        })
    # the real historical production hit-rate (whatever hub answered on the actual day each real
    # question was asked) — the PRIOR this lab exists to check a controlled re-run against.
    any_model = next(iter(raw.values()), [])
    prod_hits = sum(1 for r in any_model if r.get("prod_n_hits", 0) > 0)
    prod_rate = round(prod_hits / len(any_model), 3) if any_model else None
    (OUT_DIR / "scores.json").write_text(json.dumps({"models": rows, "historical_prod_hit_rate": prod_rate},
                                                     indent=1), encoding="utf-8")
    print(f"historical prod hit_rate (as originally logged): {prod_rate}")
    print(f"{'model':16s}{'hit_rate':>10}{'empty_subj':>12}{'fmt_ok':>8}{'latmed':>9}")
    for r in rows:
        print(f"{r['model']:16s}{r['hit_rate']:>10}{r['empty_subjects_rate']:>12}{r['format_ok']:>8}{str(r['latency_med']):>9}")
    _write_report(rows, prod_rate, raw)


def _write_report(rows: list[dict], prod_rate: float | None, raw: dict) -> None:
    L, A = [], None
    A = L.append
    A("# Model-tier lab #5 — core.librarian.subjects_for\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · J-0254 (source: decision:D-0013) · all 15 real "
      f"carried questions from `data/librarian_log.jsonl` (the entire real ask history) x "
      f"{len(rows)} models · `_SYSTEM` imported LIVE from `core/librarian.py`, `search_by_subjects()` "
      f"called directly against the real 55,905-book catalogue CSV.*\n")
    A(f"**Historical production hit-rate** (as originally logged, mixed falcon3/gemma4 across real "
      f"days): **{prod_rate}** ({int(prod_rate * 15) if prod_rate is not None else '?'}/15). This "
      f"lab's own controlled re-run (both models, same 15 questions, same catalogue, same day) below "
      f"is the apples-to-apples number.\n")
    A("**Du was live throughout this run** (not stopped — see model_tier_judge_defeater lab's script "
      "docstring for the disclosed deviation and why it only threatens latency).\n")
    A("| model | hit_rate | empty_subjects_rate | format_ok/15 | median latency |")
    A("|---|---|---|---|---|")
    for r in rows:
        A(f"| `{r['model']}` | {r['hit_rate']} | {r['empty_subjects_rate']} | {r['format_ok']}/{r['n']} | "
          f"{r['latency_med']}s |")
    A("")
    A("- **hit_rate** — R1, the module's own pre-registered metric: fraction of the 15 real asks "
      "that returned >=1 real catalogue candidate.")
    A("- **empty_subjects_rate** — the model returned zero usable subject headings at all (a stricter "
      "failure than a headings set that just happened to match nothing).\n")
    A("## Per-question comparison\n")
    A("| question (real, truncated) | prod subjects (historical) | prod hits |" +
      "".join(f" `{m}` subjects | `{m}` hits |" for m, _ in zip(raw.keys(), raw.keys())))
    models = list(raw.keys())
    A("|---|---|---|" + "---|---|" * len(models))
    n_q = len(next(iter(raw.values()))) if raw else 0
    for i in range(n_q):
        first = next(iter(raw.values()))[i]
        row = f"| {first['question'][:55]} | {', '.join(first['prod_subjects'][:3])} | {first['prod_n_hits']} |"
        for m in models:
            r = raw[m][i]
            row += f" {', '.join(r['model_subjects'][:3])} | {r['model_n_hits']} |"
        A(row)
    A(f"\n*Raw: `data/lab/model_tier/librarian/raw.json` · scores: `scores.json`*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {REPORT}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        score()
    else:
        run()

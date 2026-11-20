"""
J-3033 (F-3737, F-3751) -- OFFLINE REPLAY of the curiosity prism's input and check (P-0050).

Question: does feeding the prism the WHOLE thought (not the 90-char fragment), with a prompt that says what the input
is, and a stricter deterministic check, change what is kept, what is rejected, and how much of the thought survives
into the question?

Three arms over the queue items of the last N days (default 30):
  BEFORE   the outputs the live prism already produced (data/logs/curiosity_shadow.jsonl, matched to the queue item
           by raw text), judged by the OLD pronoun-only check and, for reference, by the NEW check.
  CONTROL  the OLD prompt + the 90-char raw_text, run now on the replay hub, old check. (Same model as TREATMENT, so
           CONTROL vs TREATMENT isolates the input + prompt + check and not the model.)
  TREAT    the NEW prompt + the whole thought, run now on the replay hub, new check.
The whole thought is recovered from memory_fragments (origin subconscious_synthesis / inner_thought) by matching the
90-char snippet to the start of the normalised content. An item whose thought cannot be found is skipped from the
TREAT arm and counted.

Metrics per arm: kept share, reject reasons (new check), median share of the OUTPUT's content words absent from the
input (F-3751's 0.83), median share of the INPUT's content words that survive into the output, share carrying a
literature frame, share naming Travis.

NOTHING LIVE IS WRITTEN. The queue, shadow log and memory db are opened read-only (db via a mode=ro URI); results go
to --out (default: a fresh temp dir), and the script refuses an --out under a data/ directory. The replay hub is
--url (default the local falcon3 hub http://127.0.0.1:11440; a different family from command-r7b, which wrote the
BEFORE arm). Ramses is the founder's gaming machine: do NOT point --url at LAN-HOST without asking; the briefing's
:11441 is a Ramses lane, so it was not used (spawned as a lab job instead).

  python scripts/lab_prism_input_replay.py --dry-run          # recover inputs, score BEFORE, no model calls
  python scripts/lab_prism_input_replay.py [--limit 130] [--url http://127.0.0.1:11440]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sqlite3
import statistics
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                                    # noqa: E402,F401  (BEFORE anything lab-ish)
from core import curiosity_queue as cq                         # noqa: E402
from core import self_surprise as ss                           # noqa: E402

LIVE = Path("C:/Nascence")
QUEUE = LIVE / "data" / "curiosity_queue.jsonl"
SHADOW = LIVE / "data" / "logs" / "curiosity_shadow.jsonl"
DB = LIVE / "data" / "memory" / "nascence.db"
LIT = re.compile(r"literat|literary|narrative|thematic|poetic|poem|character|protagonist|story|fiction", re.IGNORECASE)
TRAVIS = re.compile(r"\btravis\b", re.IGNORECASE)


def norm(t: str) -> str:
    return " ".join((t or "").split())


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def recover_thoughts(db: Path, raws: list[str], since_ts: float = 0.0) -> dict:
    """raw 90-char snippet -> the whole normalised thought text (<=400 at a sentence boundary), read-only. One scan of
    the idle-thought origins (the table has no origin index, so a LIKE per item would be one scan each)."""
    out: dict = {}
    if not db.exists() or not raws:
        return out
    want = {norm(r): r for r in raws}
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=10)
    try:
        for (content,) in conn.execute("SELECT content FROM memory_fragments WHERE origin IN "
                                       "('subconscious_synthesis','inner_thought') AND timestamp >= ?", (since_ts,)):
            n = norm(content)
            for w, raw in want.items():
                if raw not in out and n.startswith(w):
                    out[raw] = ss.thought_text(content)
                    break
    finally:
        conn.close()
    return out


def absent_share(question: str, source: str) -> float | None:
    q = cq.content_stems(question)
    return (len(q - cq.content_stems(source)) / len(q)) if q else None


def summarise(rows: list[dict]) -> dict:
    """rows: {q, src, ok, reason}. ok is the arm's own check."""
    failed = sum(1 for r in rows if r.get("reason") == "call_failed")
    rows = [r for r in rows if r.get("reason") != "call_failed"]   # a hub timeout is not a reject
    n = len(rows)
    if not n:
        return {"n": 0, "call_failed": failed}
    kept = [r for r in rows if r["ok"]]
    rejects: dict = {}
    for r in rows:
        if not r["ok"]:
            k = (r.get("reason") or "unknown").split(":")[0]
            rejects[k] = rejects.get(k, 0) + 1
    absent = [a for a in (absent_share(r["q"], r["src"]) for r in rows if r["q"]) if a is not None]
    surv = [s for s in (cq.content_survival(r["q"], r["src"]) for r in rows if r["q"]) if s is not None]
    both = lambda xs: round(statistics.median(xs), 3) if xs else None   # noqa: E731
    qs = [r["q"] for r in rows if r["q"]]
    return {"n": n, "call_failed": failed, "kept": len(kept), "kept_share": round(len(kept) / n, 3), "rejects": rejects,
            "median_output_words_absent_from_input": both(absent), "median_input_words_surviving": both(surv),
            "lit_frame_share": round(sum(1 for q in qs if LIT.search(q)) / max(1, len(qs)), 3),
            "travis_share": round(sum(1 for q in qs if TRAVIS.search(q)) / max(1, len(qs)), 3)}


def build_items(queue: list[dict], shadow: list[dict], days: float, limit: int, thoughts: dict | None) -> list[dict]:
    cut = time.time() - days * 86400
    sh_by_raw: dict = {}
    for r in shadow:
        sh_by_raw.setdefault(norm(r.get("raw", ""))[:80], []).append(r)
    items = []
    for it in queue:
        if float(it.get("ts", 0) or 0) < cut:
            continue
        raw = it["raw_text"]
        before = None
        for r in sh_by_raw.get(norm(raw)[:80], []):
            if abs(float(r.get("ts", 0)) - float(it.get("ts", 0))) < 6 * 3600:
                before = r
        items.append({"id": it["id"], "ts": it["ts"], "raw": raw, "before": before,
                      "full": (thoughts or {}).get(raw)})
    return items[-limit:] if limit else items


def score_before(items: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    old, new_on_raw, new_on_full = [], [], []
    for it in items:
        b = it["before"]
        if not b:
            continue
        q = b.get("transformed", "")
        old.append({"q": q, "src": it["raw"], "ok": bool(q) and not cq._FIRST_PERSON.search(q), "reason": ""})
        ok, why = cq.world_facing_verdict(q, it["raw"])
        new_on_raw.append({"q": q, "src": it["raw"], "ok": ok, "reason": why})
        if it["full"]:
            ok2, why2 = cq.world_facing_verdict(q, it["full"])
            new_on_full.append({"q": q, "src": it["full"], "ok": ok2, "reason": why2})
    return old, new_on_raw, new_on_full


async def default_ask(url: str, system: str, user: str) -> str:
    body = json.dumps({"model": "prism", "stream": False, "format": "json",
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                       "options": {"temperature": 0.3, "num_predict": 120}}).encode()

    def _go():
        req = urllib.request.Request(url.rstrip("/") + "/api/chat", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=240) as r:
            return json.loads(r.read())["message"]["content"]
    return await asyncio.to_thread(_go)


def parse_q(txt: str) -> str:
    try:
        d = json.loads(txt)
        return str(d.get("question", "")).strip() if isinstance(d, dict) else ""
    except Exception:
        m = re.search(r'"question"\s*:\s*"([^"]+)"', txt or "")
        return m.group(1).strip() if m else ""


async def run_arms(items: list[dict], url: str, ask=default_ask, log=None, emit=None) -> tuple[list[dict], list[dict]]:
    control, treat = [], []
    for i, it in enumerate(items):
        s1, u1 = cq.prism_prompt(it["raw"], v2=False)
        failed1 = False
        try:
            q1 = parse_q(await ask(url, s1, u1))
        except Exception as exc:
            q1, failed1 = "", True
            if log: log(f"  control {i} failed: {exc}")
        control.append({"q": q1, "src": it["raw"], "ok": bool(q1) and not cq._FIRST_PERSON.search(q1),
                        "reason": "call_failed" if failed1 else "", "id": it["id"]})
        if emit: emit("control", control[-1])
        if it["full"]:
            s2, u2 = cq.prism_prompt(it["full"], v2=True)
            failed2 = False
            try:
                q2 = parse_q(await ask(url, s2, u2))
            except Exception as exc:
                q2, failed2 = "", True
                if log: log(f"  treat {i} failed: {exc}")
            ok, why = cq.world_facing_verdict(q2, it["full"])
            treat.append({"q": q2, "src": it["full"], "ok": ok, "reason": "call_failed" if failed2 else why,
                          "id": it["id"], "raw": it["raw"]})
            if emit: emit("treat", treat[-1])
        if log and i % 10 == 0:
            log(f"  {i + 1}/{len(items)}")
    return control, treat


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=30)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--url", default="http://127.0.0.1:11440")
    ap.add_argument("--queue", default=str(QUEUE))
    ap.add_argument("--shadow", default=str(SHADOW))
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--out", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    out = Path(a.out) if a.out else Path(tempfile.mkdtemp(prefix="prism_replay_J3033_"))
    if "data" in {p.lower() for p in out.resolve().parts}:
        print("refusing --out under a data/ directory:", out)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    queue, shadow = load_jsonl(Path(a.queue)), load_jsonl(Path(a.shadow))
    pre = build_items(queue, shadow, a.days, a.limit, None)
    thoughts = recover_thoughts(Path(a.db), [it["raw"] for it in pre], time.time() - (a.days + 2) * 86400)
    items = build_items(queue, shadow, a.days, a.limit, thoughts)
    old, new_raw, new_full = score_before(items)
    report = {"items": len(items), "full_recovered": sum(1 for it in items if it["full"]),
              "full_len_median": (statistics.median(len(it["full"]) for it in items if it["full"])
                                  if any(it["full"] for it in items) else None),
              "BEFORE_old_check": summarise(old), "BEFORE_new_check_on_raw": summarise(new_raw),
              "BEFORE_new_check_on_full": summarise(new_full), "hub": a.url, "dry_run": a.dry_run}
    if not a.dry_run:
        rows_f = out / "replay_rows.jsonl"

        def emit(arm, row):   # incremental: a hub that dies half way still leaves the finished rows
            with open(rows_f, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"arm": arm, **row}, ensure_ascii=False) + "\n")
        control, treat = asyncio.run(run_arms(items, a.url, log=print, emit=emit))
        report["CONTROL_old_prompt_raw_old_check"] = summarise(control)
        report["TREAT_new_prompt_full_new_check"] = summarise(treat)
    (out / "replay_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("written:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""J-2867 (F-3540, P-0080 R1): decoupled relevance eval of the librarian.
The librarian's own mapper is falcon3:7b / gemma4:12b, so the judge must be a DIFFERENT family. status() only
counts catalogue matches (hit_rate); this asks whether the shown titles actually bear on the question.
Samples ~40 rows of data/librarian_log.jsonl with n_hits>0 (read-only, seeded, distinct questions), split into
whole-sentence asks vs 'the question of ...' asks, one judge call per row, JSON {"scores": {"1":0|1|2,...}} per
title (0 = unrelated, 1 = loosely related, 2 = clearly bears on it). Reports per-split mean title score and the
share of rows with at least one title scored 2.
NOT run by the job (needs a live local hub): --hub and --hub-model are required for a real run, and the family
guard refuses falcon/gemma.
    python scripts/_lab_J-2867_librarian_relevance_eval.py --hub http://127.0.0.1:PORT --hub-model qwen3.5:9b --out FILE.json
    python scripts/_lab_J-2867_librarian_relevance_eval.py --dry-run     # sampling + split only, no model call
"""
from __future__ import annotations
import argparse, json, random, sys, time, urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "librarian_log.jsonl"

SYS = ("You are a strict reference librarian. Given a reader's QUESTION and a numbered list of BOOK TITLES shown to "
       "them, score each title: 0 = unrelated to the question, 1 = loosely or tangentially related, 2 = clearly a "
       "book that bears on the question. Judge by the title alone. Answer ONLY JSON like "
       "{\"scores\": {\"1\": 2, \"2\": 0}}.")


def split_of(q: str) -> str:
    return "question_of" if (q or "").strip().lower().startswith("the question of") else "whole_sentence"


def load_rows(log: Path = LOG) -> list[dict]:
    rows = []
    for l in open(log, encoding="utf-8"):
        if l.strip():
            try:
                r = json.loads(l)
            except Exception:
                continue
            if r.get("n_hits", 0) > 0 and r.get("titles"):
                rows.append(r)
    return rows


def sample(rows: list[dict], n: int = 40, seed: int = 2867) -> list[dict]:
    """Distinct questions only (byte-identical repeats would dominate), balanced across the two splits."""
    seen, uniq = set(), []
    for r in rows:
        k = " ".join(r["question"].split())
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    rng = random.Random(seed)
    by = {"whole_sentence": [], "question_of": []}
    for r in uniq:
        by[split_of(r["question"])].append(r)
    out = []
    for k in by:
        rng.shuffle(by[k])
        out += by[k][: n // 2]
    return out[:n]


def judge(hub: str, q: str, titles: list[str], timeout: int = 300):
    user = f"QUESTION: {q}\n\nBOOK TITLES:\n" + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200}}
    try:
        req = urllib.request.Request(hub + "/api/chat", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = (json.loads(r.read()).get("message") or {}).get("content") or ""
        sc = json.loads(raw).get("scores") or {}
        return [int(sc.get(str(i + 1), -1)) for i in range(len(titles))], ""
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def summarise(res: list[dict]) -> dict:
    out = {}
    for sp in ("whole_sentence", "question_of"):
        rs = [r for r in res if r["split"] == sp and r.get("scores")]
        flat = [s for r in rs for s in r["scores"] if s >= 0]
        out[sp] = {"rows": len(rs),
                   "mean_title_score": round(sum(flat) / len(flat), 3) if flat else None,
                   "rows_with_a_2": round(sum(1 for r in rs if 2 in r["scores"]) / len(rs), 3) if rs else None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub")
    ap.add_argument("--hub-model", default="")
    ap.add_argument("--out")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    s = sample(load_rows(), a.n)
    if a.dry_run:
        print({sp: sum(1 for r in s if split_of(r["question"]) == sp) for sp in ("whole_sentence", "question_of")})
        return
    if not a.hub or not a.out:
        sys.exit("--hub and --out required")
    if "10.1.1." in a.hub:
        sys.exit("refusing: Ramses is not to be called")
    if not a.hub_model or any(f in a.hub_model.lower() for f in ("falcon", "gemma")):
        sys.exit("judge must be a different model family from the librarian's mapper (not falcon/gemma)")
    res = []
    for r in s:
        sc, err = judge(a.hub, r["question"], r["titles"])
        res.append({"question": r["question"], "split": split_of(r["question"]), "titles": r["titles"],
                    "scores": sc, "err": err, "judge": a.hub_model})
        print(res[-1]["split"], sc or err, flush=True)
    json.dump({"judge": a.hub_model, "ts": time.time(), "summary": summarise(res), "rows": res},
              open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summarise(res), indent=1))


if __name__ == "__main__":
    main()

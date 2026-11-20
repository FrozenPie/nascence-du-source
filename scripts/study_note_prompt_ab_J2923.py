"""
J-2923 (P-0072, F-3604) -- same-input A/B of the study-note system prompt.

A = the prompt as it stood before J-2923 (docs/lab/J-2923_data/prompt_A.txt, copied verbatim from master 223c95c6).
B = core.study_note._NOTE_SYS as it is NOW in this tree.

Inputs: data/lab/J-2923/passages.jsonl, 40 reconstructed real 5000-char passages (method of F-3588: study fragment
encounter_id -> its first reading fragment's source_id + source_offset -> data/books text, same slice/trim code),
a seeded random draw (seed 2923, at most 2 per book, no Gutenberg boilerplate / transcriber notes, offset > 3000).
No related_text is sent in either arm (same input, kept simple).

Phases (each resumable; every row is cached in data/lab/J-2923/*.jsonl):
  gen    both arms on the production hot lane (:11433 qwen3.5:9b) through core.model_client.call_node_json with the
         production budget (max_tokens 1500, temperature 0.5); the user message is built exactly as compose_note does.
  judge  grounding judged by gemma4:12b on :11439 (family gemma, not qwen: the DECOUPLED JUDGE), blind to the arm.
  report opener / empty-field / grounding numbers -> data/lab/J-2923/summary.json

Local hubs only (no Ramses call). Writes only under data/lab/J-2923/. Usage:
  python scripts/study_note_prompt_ab_J2923.py gen|judge|report|all [--limit N]
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import core  # noqa: F401,E402  (core before anything lab-ish, house rule)
from core import study_note as sn  # noqa: E402
from core import model_client as mc  # noqa: E402

LAB = ROOT / "data" / "lab" / "J-2923"
GEN_URL = ["http://127.0.0.1:11433"]
JUDGE_URL = ["http://127.0.0.1:11439"]
JUDGE_MODEL = "gemma4:12b"

JUDGE_SYS = (
    "You check a student's study note against the source passage it was written from. Judge ONLY whether the "
    "note's factual claims (its understanding and its key_facts) are supported by the passage. Ignore style, "
    "ignore the thoughts, ignore whether the note is interesting. Output ONLY JSON: {\"facts_total\": <number of "
    "distinct factual claims in the understanding and key_facts>, \"facts_supported\": <how many of them the "
    "passage states or clearly implies>, \"unsupported\": [\"each claim the passage does not support, briefly\"], "
    "\"grounding\": <1 to 5; 5 = every claim is in the passage, 3 = a few claims go beyond it, 1 = mostly "
    "invented>}")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _append(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _arms() -> dict[str, str]:
    return {"A": (ROOT / "docs" / "lab" / "J-2923_data" / "prompt_A.txt").read_text(encoding="utf-8"), "B": sn._NOTE_SYS}


def _title(book: str) -> str:
    return book.replace("_", " ")


async def gen(limit: int | None, which: tuple = ("A", "B")) -> None:
    passages = _read(LAB / "passages.jsonl")[: limit or None]
    done = {(r["fid"], r["arm"]) for r in _read(LAB / "gen.jsonl")}
    arms = _arms()
    for i, p in enumerate(passages):
        for arm in which:
            if (p["fid"], arm) in done:
                continue
            user = f"The passage(s), from '{_title(p['book'])}':\n{p['passage'][:5000]}"
            row = {"fid": p["fid"], "arm": arm, "book": p["book"]}
            try:
                d = await mc.call_node_json(GEN_URL, arms[arm], user, max_tokens=1500, temperature=0.5, timeout=300)
                note = sn._norm(d) if d and str(d.get("understanding") or "").strip() else None
                row["note"] = note
                row["raw_keys"] = sorted(d.keys()) if isinstance(d, dict) else None
            except Exception as exc:
                row["note"] = None
                row["error"] = repr(exc)[:200]
            _append(LAB / "gen.jsonl", row)
            print(f"gen {i + 1}/{len(passages)} {arm} ok={row['note'] is not None}", flush=True)


async def judge(limit: int | None) -> None:
    passages = {p["fid"]: p for p in _read(LAB / "passages.jsonl")}
    done = {(r["fid"], r["arm"]) for r in _read(LAB / "judge.jsonl")}
    rows = [r for r in _read(LAB / "gen.jsonl") if r.get("note")][: (limit * 2) if limit else None]
    for i, r in enumerate(rows):
        if (r["fid"], r["arm"]) in done:
            continue
        n = r["note"]
        user = (f"PASSAGE:\n{passages[r['fid']]['passage'][:5000]}\n\nSTUDENT NOTE\nUnderstanding: {n['understanding']}\n"
                f"Key facts:\n" + "\n".join(f"- {f}" for f in n["key_facts"]))
        out = {"fid": r["fid"], "arm": r["arm"]}
        try:
            d = await mc.call_node_json(JUDGE_URL, JUDGE_SYS, user, max_tokens=700, temperature=0.1,
                                        timeout=400, retries=1, model_override=JUDGE_MODEL)
            out["judge"] = d
        except Exception as exc:
            out["judge"] = None
            out["error"] = repr(exc)[:200]
        _append(LAB / "judge.jsonl", out)
        print(f"judge {i + 1}/{len(rows)} {r['arm']} grounding={(out['judge'] or {}).get('grounding')}", flush=True)


async def probe(n: int) -> None:
    """Cheap prompt iteration: arm B only on the first n passages, NOT cached, prints the openers."""
    passages = _read(LAB / "passages.jsonl")[:n]
    for p in passages:
        user = f"The passage(s), from '{_title(p['book'])}':\n{p['passage'][:5000]}"
        d = await mc.call_node_json(GEN_URL, sn._NOTE_SYS, user, max_tokens=1500, temperature=0.5, timeout=300)
        x = sn._norm(d)
        print("U:", x["understanding"][:60].replace("\n", " "), "| T:", x["thoughts"][:40], "| C:", bool(x["connects_to"]), "Q:", bool(x["question"]), flush=True)


def _first_words(s: str, n: int) -> str:
    return " ".join(re.findall(r"[A-Za-z']+", s or "")[:n]).lower()


def _num(x):
    try:
        return float(x)
    except Exception:
        return None


def report() -> dict:
    gens = _read(LAB / "gen.jsonl")
    judges = {(r["fid"], r["arm"]): r.get("judge") for r in _read(LAB / "judge.jsonl")}
    summary: dict = {"n_passages": len({g["fid"] for g in gens}), "arms": {}}
    for arm in ("A", "B"):
        rows = [g for g in gens if g["arm"] == arm]
        notes = [g["note"] for g in rows if g.get("note")]
        n = max(1, len(notes))
        u4 = Counter(_first_words(x["understanding"], 4) for x in notes)
        t4 = Counter(_first_words(x["thoughts"], 3) for x in notes if x["thoughts"])
        gr = [_num((judges.get((g["fid"], arm)) or {}).get("grounding")) for g in rows if g.get("note")]
        gr = [x for x in gr if x is not None]
        ft = [(_num((judges.get((g["fid"], arm)) or {}).get("facts_total")),
               _num((judges.get((g["fid"], arm)) or {}).get("facts_supported"))) for g in rows if g.get("note")]
        ft = [(t, s) for t, s in ft if t and s is not None]
        summary["arms"][arm] = {
            "calls": len(rows), "json_ok": len(notes),
            "opens_I_see_that": sum(1 for x in notes if re.match(r"\s*I see that", x["understanding"])),
            "opens_I_see_that_the": sum(1 for x in notes if re.match(r"\s*I see that the", x["understanding"], re.I)),
            "distinct_first4_words": len(u4), "top_first4": u4.most_common(5),
            "top_first4_share": round(u4.most_common(1)[0][1] / n, 3) if u4 else None,
            "thoughts_empty": sum(1 for x in notes if not x["thoughts"]),
            "thoughts_what_strikes_me": sum(1 for x in notes if re.match(r"\s*(what|it) strikes me", x["thoughts"], re.I)),
            "top_thoughts_first3": t4.most_common(4),
            "connects_empty": sum(1 for x in notes if not x["connects_to"]),
            "question_empty": sum(1 for x in notes if not x["question"]),
            "not_merely": sum(1 for x in notes if re.search(r"not merely", json.dumps(x), re.I)),
            "the_passage_or_text_opener": sum(1 for x in notes if re.match(r"\s*the (passage|text)\b", x["understanding"], re.I)),
            "mentions_passage_or_text_anywhere": sum(1 for x in notes if re.search(r"\b(the passage|the text)\b", x["understanding"], re.I)),
            "mean_understanding_chars": round(sum(len(x["understanding"]) for x in notes) / n),
            "mean_key_facts": round(sum(len(x["key_facts"]) for x in notes) / n, 2),
            "judged": len(gr), "mean_grounding": round(sum(gr) / len(gr), 3) if gr else None,
            "supported_fraction": round(sum(s for _, s in ft) / max(1, sum(t for t, _ in ft)), 3) if ft else None,
            "mean_unsupported_listed": round(sum(len((judges.get((g["fid"], arm)) or {}).get("unsupported") or [])
                                                for g in rows if g.get("note")) / max(1, len(gr)), 3) if gr else None,
        }
    # paired grounding
    wins = {"A_higher": 0, "B_higher": 0, "tie": 0}
    for fid in {g["fid"] for g in gens}:
        a = _num((judges.get((fid, "A")) or {}).get("grounding"))
        b = _num((judges.get((fid, "B")) or {}).get("grounding"))
        if a is None or b is None:
            continue
        wins["A_higher" if a > b else "B_higher" if b > a else "tie"] += 1
    summary["paired_grounding"] = wins
    (LAB / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    lim = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    which = tuple(sys.argv[sys.argv.index("--arms") + 1].split(",")) if "--arms" in sys.argv else ("A", "B")
    if cmd == "probe":
        asyncio.run(probe(lim or 10))
    if cmd in ("gen", "all"):
        asyncio.run(gen(lim, which))
    if cmd in ("judge", "all"):
        asyncio.run(judge(lim))
    if cmd in ("report", "all"):
        report()

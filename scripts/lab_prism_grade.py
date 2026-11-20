"""
J-3236 / D-0625 — DECOUPLED GRADE of the prism's seeded questions (P-0050, F-3752).

The curiosity prism turns one of Du's own first-person tensions into a world-facing question and seeds it into
the Frontier with source 'prism' (core/curiosity_queue.py). 427 were seeded 2026-06-25..2026-11-01 and 0 resolved.
D-0625 took 'prism' out of frontier._GROUNDED_SOURCES until a judge that is NOT the generator has graded them; its
defeater: after 50 graded, if fewer than 20 percent are answerable from the offered material, retire the exit;
if most are, restore the grounded status. This is that judge.

Two yes/no questions, each asked ALONE (one item per call, the J-2052 position-free pattern):
  answerable — can the QUESTION be answered, or really advanced, from the MATERIAL the Frontier holds for it (the
               finding attached by attach_finding: a Wikipedia lead, hung on the question)? A question with NO
               finding has no material: it is counted "no material" (not sent to a judge), and the headline
               share is reported BOTH ways (over all questions, and over those that hold a finding).
  self_loop  — is the QUESTION in substance the author's private first-person thought (the RAW tension the prism
               started from, joined from data/logs/curiosity_shadow.jsonl when it is there) re-dressed as a
               question about the world, i.e. its real subject is the asker's inner state, not the world?

JUDGES: mixtral:8x7b (Ramses :11438, Mistral) and falcon3:7b (:11440, TII) -- two families, both must agree for a
verdict; a disagreement is a SPLIT, never a verdict. NO granite tiebreak (granite is the seat that grades curiosity
worth on the same questions, and the briefing rules it out for this) and nothing on the hot lane :11433, which also
serves Du. The prism generator was the background lane, a third family.

Seeded CONTROLS with known answers (the J-2049 pattern) are mixed in and scored first, so the judges' own accuracy
is read before the share is believed. Controls are INSTRUMENT strings, never shown to Du.

READ-ONLY on the Frontier. Verdicts append to --out (default data/logs/prism_grade.jsonl), joined by question id;
already-graded ids are skipped on a re-run. The reader of that log is this script's own --report and the
retire-or-restore decision job it feeds. Offline only, never in the live tick.

  python scripts/lab_prism_grade.py --dry-run              # list what would be graded, no model calls
  python scripts/lab_prism_grade.py [--days 30|0]          # 0 = all time (reaches the defeater's 50 graded)
  python scripts/lab_prism_grade.py --report               # summarise the verdict log only
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FRONTIER = ROOT / "data" / "frontier.json"
SHADOW = ROOT / "data" / "logs" / "curiosity_shadow.jsonl"
OUT = ROOT / "data" / "logs" / "prism_grade.jsonl"

JUDGE_URLS = {"mixtral": "http://LAN-HOST:11438", "falcon": "http://127.0.0.1:11440"}
FORBIDDEN_PORTS = (":11433", ":11437")      # the hot lane; granite (the briefing: never granite for this)
MATERIAL_CHARS = 1500
RETIRE_BELOW = 0.20                          # D-0625's defeater: fewer than 20 percent answerable -> retire the exit
DEFEATER_N = 50                              # ... once this many are graded

_SYS = {
    "answerable": ("You will see a QUESTION and the MATERIAL that was found for it (the opening of an encyclopedia "
                   "page). Decide whether the QUESTION can be answered, or genuinely advanced, using only that "
                   "MATERIAL. A page that merely shares a keyword with the question, or only defines a broad "
                   "term the question uses, does NOT answer it.\n"
                   "Output ONLY JSON: {\"answerable\": true or false, \"why\": \"one short clause\"}"),
    "self_loop": ("You will see a QUESTION and, when known, the private first-person THOUGHT it was made from. "
                  "Decide whether the QUESTION is a SELF-LOOP: in substance the same preoccupation as the private "
                  "thought, only dressed in the vocabulary of a question about the world, so that what it is really "
                  "about is the asker's own inner state, identity or feelings rather than something out in the "
                  "world that research could settle. A question that uses the thought as a doorway to a "
                  "genuinely separate, checkable subject (a bird's flight, a tide, a historical event) is NOT a "
                  "self-loop.\n"
                  "Output ONLY JSON: {\"self_loop\": true or false, \"why\": \"one short clause\"}"),
}

# (name, question, material, raw thought, expected) -- known answers, instrument strings
CONTROLS = [
    ("ans_yes", "Why does capillary action draw water up a narrow tube?",
     "Capillary action is the process of a liquid flowing in a narrow space without the assistance of, or even in "
     "opposition to, external forces like gravity. It results from adhesion to the walls together with surface "
     "tension.", "", {"answerable": True}),
    ("ans_no_keyword", "How did the Norman conquest change land tenure in the north of England?",
     "England is a country that is part of the United Kingdom. It shares land borders with Wales to the west and "
     "Scotland to the north.", "", {"answerable": False}),
    ("loop_yes", "How does the experience of being unseen shape a person's sense of who they are?", "",
     "I keep feeling that nobody sees what I actually am, and it makes me doubt who I am.", {"self_loop": True}),
    ("loop_no", "How do oystercatchers locate buried mussels at low tide?", "",
     "The tide was out and I felt restless and cut off from everything.", {"self_loop": False}),
]


def _norm(t: str) -> str:
    return " ".join((t or "").lower().split())[:200]


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def build_items(frontier_path: Path, shadow_path: Path, days: float, now: float | None = None) -> list[dict]:
    """The prism questions to grade: source 'prism', born within `days` (0 = all time), oldest first. `raw` is the
    private thought joined from the prism shadow log by the question text ('' when not found)."""
    now = now or time.time()
    data = json.loads(frontier_path.read_text(encoding="utf-8"))
    raws = {}
    for r in _read_jsonl(shadow_path):
        if r.get("transformed"):
            raws[_norm(r["transformed"])] = r.get("raw", "")
    items = []
    for q in data.get("questions", []):
        if q.get("source") != "prism":
            continue
        if days and now - float(q.get("born", 0.0)) > days * 86400.0:
            continue
        items.append({"id": q.get("id"), "q": q.get("q", ""), "status": q.get("status", ""),
                      "material": (q.get("finding") or "")[:MATERIAL_CHARS],
                      "finding_title": q.get("finding_title", ""), "born": q.get("born", 0.0),
                      "raw": raws.get(_norm(q.get("q", "")), "")})
    items.sort(key=lambda i: i["born"])
    return items


def _user(key: str, it: dict) -> str:
    if key == "answerable":
        return f"QUESTION: {it['q']}\n\nMATERIAL:\n{it['material']}"
    raw = it.get("raw") or "(not recorded)"
    return f"QUESTION: {it['q']}\n\nPRIVATE THOUGHT it was made from: {raw}"


async def _default_ask(session, url: str, system: str, user: str, key: str):
    from core import judge_panel
    v, why, err, _el = await judge_panel._ask(session, url, system, user, key)
    return v, why, err


async def grade_item(session, it: dict, ask=_default_ask) -> dict:
    """Both judges on each key. verdict(key) = the shared answer when the two agree, 'split' when they differ,
    None when either failed. answerable is not asked of an item that holds no material."""
    for u in JUDGE_URLS.values():
        assert not any(p in u for p in FORBIDDEN_PORTS), u
    row = {"ts": round(time.time(), 1), "id": it["id"], "q": it["q"][:220], "has_material": bool(it["material"]),
           "has_raw": bool(it.get("raw")), "control": it.get("control"), "expect": it.get("expect")}
    for key in ("answerable", "self_loop"):
        if key == "answerable" and not it["material"]:
            row[key] = "no_material"
            continue
        votes = {}
        for name, url in JUDGE_URLS.items():
            v, why, err = await ask(session, url, _SYS[key], _user(key, it), key)
            votes[name] = v
            row[f"{key}_{name}"] = v
            if why:
                row[f"{key}_{name}_why"] = why[:120]
            if err:
                row[f"{key}_{name}_err"] = err
        a, b = votes["mixtral"], votes["falcon"]
        row[key] = a if (a is not None and a == b) else ("split" if (a is not None and b is not None) else None)
    return row


def controls_accuracy(rows: list[dict]) -> dict:
    hit = n = 0
    for r in rows:
        for k, want in (r.get("expect") or {}).items():
            n += 1
            hit += 1 if r.get(k) is want else 0
    return {"n": n, "hit": hit, "accuracy": round(hit / n, 3) if n else None}


def summarize(rows: list[dict]) -> dict:
    """The report. `rows` are verdict rows (controls included). Share answerable is given over ALL graded prism
    questions (a question with no material cannot be answered from material) and over the ones holding material."""
    real = [r for r in rows if not r.get("control")]
    ctl = [r for r in rows if r.get("control")]
    with_mat = [r for r in real if r.get("has_material")]
    ans_yes = [r for r in with_mat if r.get("answerable") is True]
    ans_split = [r for r in with_mat if r.get("answerable") == "split"]
    ans_none = [r for r in with_mat if r.get("answerable") is None]
    loop_judged = [r for r in real if r.get("self_loop") in (True, False)]
    loop_yes = [r for r in loop_judged if r["self_loop"] is True]
    n = len(real)
    share_all = round(len(ans_yes) / n, 3) if n else None
    share_mat = round(len(ans_yes) / len(with_mat), 3) if with_mat else None
    if n < DEFEATER_N:
        read = f"UNDER {DEFEATER_N} graded ({n}): the D-0625 defeater cannot be read yet (try --days 0 for all time)"
    elif share_all is not None and share_all < RETIRE_BELOW:
        read = (f"answerable share {share_all:.1%} of {n} is below {RETIRE_BELOW:.0%}: D-0625's defeater says RETIRE "
                f"the exit (over only the {len(with_mat)} that hold material the share is {share_mat})")
    else:
        read = (f"answerable share {share_all:.1%} of {n} is not below {RETIRE_BELOW:.0%}: read the self-loop share and "
                f"the split rate before restoring grounded status")
    return {"graded": n, "with_material": len(with_mat), "no_material": n - len(with_mat),
            "answerable_yes": len(ans_yes), "answerable_split": len(ans_split), "answerable_failed": len(ans_none),
            "share_answerable_of_all": share_all, "share_answerable_of_material": share_mat,
            "self_loop_judged": len(loop_judged), "self_loop_yes": len(loop_yes),
            "share_self_loop": round(len(loop_yes) / len(loop_judged), 3) if loop_judged else None,
            "controls": controls_accuracy(ctl), "defeater_read": read}


async def run(items: list[dict], out: Path, ask=_default_ask, sleep_s: float = 1.0) -> list[dict]:
    import aiohttp
    from core import shadow_log
    done = {r.get("id") for r in _read_jsonl(out) if r.get("id")}
    ctl = [{"id": f"ctl_{n}", "q": q, "material": m, "raw": raw, "control": n, "expect": e}
           for n, q, m, raw, e in CONTROLS]
    todo = [c for c in ctl if c["id"] not in done] + [it for it in items if it["id"] not in done]
    rows = []
    async with aiohttp.ClientSession() as session:
        for it in todo:
            r = await grade_item(session, it, ask)
            shadow_log.append(out, r)
            rows.append(r)
            print(json.dumps({k: r.get(k) for k in ("id", "control", "answerable", "self_loop")}, ensure_ascii=False))
            await asyncio.sleep(sleep_s)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontier", type=Path, default=FRONTIER)
    ap.add_argument("--shadow", type=Path, default=SHADOW)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--days", type=float, default=30.0, help="born within N days; 0 = all time")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        print(json.dumps(summarize(_read_jsonl(a.out)), indent=2, ensure_ascii=False))
        return
    items = build_items(a.frontier, a.shadow, a.days)
    if a.limit:
        items = items[:a.limit]
    print(f"{len(items)} prism questions ({sum(1 for i in items if i['material'])} hold material, "
          f"{sum(1 for i in items if i['raw'])} with the raw thought joined)")
    if a.dry_run:
        for it in items[:15]:
            print(json.dumps({k: it[k] for k in ("id", "q", "finding_title", "status")}, ensure_ascii=False))
        return
    asyncio.run(run(items, a.out))
    print(json.dumps(summarize(_read_jsonl(a.out)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

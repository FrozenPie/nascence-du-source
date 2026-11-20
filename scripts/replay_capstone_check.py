"""J-3174 / D-0562: replay the capstone repetition + own-source checks over the essays already written.

READ-ONLY: it opens no database and writes nothing under data/. Point it at a copy of data/Study (the essays
and the book note folders) with --study; the default is this tree's own data/Study.
    python scripts/replay_capstone_check.py --study <copy of data/Study> [--list] [--quantiles]

For each ESSAY_*.md it finds the book's own notes (data/Study/notes/<slug>/TAB_*.md plus any loose TAB_ file whose
'on:' line cites the book) and builds the cross-book pool from every other note, then runs
essay_lesson.check_capstone. The replay differs from the live gather in one way: DB 'understanding' notes and
deep-recall gists are not on disk, so a few of the book's own terms can look foreign here; the replay's failure
count is therefore an upper bound on the own-source side.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _split_essay(txt: str) -> tuple[str, str, str]:
    """(heading, on-title, body) of an ESSAY_ file."""
    head = txt.split("\n", 1)[0].lstrip("# ").strip()
    m = re.search(r"on:\s*(.+?)\*", txt[:600])
    body = txt.split("*\n\n", 1)[-1].strip()
    return head, (m.group(1).strip() if m else ""), body


def _slug(title: str) -> str:
    return re.sub(r"[^\w\- ]", "", title)[:48].strip().replace(" ", "_") or "book"


def _note_body(txt: str) -> str:
    return txt.split("*\n\n", 1)[-1].strip() or txt


def load(study: Path):
    from core.essay_lesson import _cites_this_book
    notes_dir = study / "notes"
    by_dir: dict[str, list[str]] = {}
    if notes_dir.exists():
        for d in notes_dir.iterdir():
            if d.is_dir():
                by_dir[d.name] = [_note_body(p.read_text(encoding="utf-8", errors="ignore"))
                                  for p in d.glob("TAB_*.md")]
    loose = []
    for p in study.glob("TAB_*.md"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"on:\s*(.+?)\*", t[:400])
        loose.append(((m.group(1).strip().lower() if m else ""), _note_body(t)))
    essays = []
    for p in sorted(study.glob("ESSAY_*.md")):
        head, on, body = _split_essay(p.read_text(encoding="utf-8", errors="ignore"))
        slug = _slug(on)
        own = []
        used = set()
        for dn, bodies in by_dir.items():
            if dn == slug or dn.startswith(slug) or slug.startswith(dn):
                own += bodies; used.add(dn)
        own += [b for cit, b in loose if cit and on and _cites_this_book(on, cit)]
        cross = [b for dn, bodies in by_dir.items() if dn not in used for b in bodies]
        cross += [b for cit, b in loose if not (cit and on and _cites_this_book(on, cit))]
        essays.append({"file": p.name, "title": on or head, "body": body, "own": own, "cross": cross})
    return essays


NL = chr(10)


def q(vals, p):
    s = sorted(vals)
    return s[min(len(s) - 1, int(p * len(s)))] if s else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", default=str(ROOT / "data" / "Study"))
    ap.add_argument("--list", action="store_true", help="one line per essay")
    ap.add_argument("--quantiles", action="store_true", help="print the score distributions")
    a = ap.parse_args()
    import core
    from core import essay_lesson as el
    print("core from:", core.__file__)
    essays = load(Path(a.study))
    print(f"essays: {len(essays)}   with own notes found: {sum(1 for e in essays if e['own'])}")
    rows = []
    for e in essays:
        own_text = "\n".join(e["own"])
        cross_text = "\n".join(e["cross"])
        rep = el.check_repetition(e["body"])
        src = el.check_own_source(e["body"], own_text, cross_text, e["title"])
        rows.append((e, rep, src))
        if a.list:
            print(f"{e['file'][:44]:44} rep={'ok ' if rep['ok'] else 'FAIL'} open={rep['open_restate']:.2f} "
                  f"adj={rep['adjacent']:.2f}  src={'ok ' if src['ok'] else 'FAIL'} "
                  f"foreign={[len(s['foreign']) for s in src['sections']]} cross={len(src['cross_book'])}")
    n = len(rows)
    if not n:
        return 1
    if a.quantiles:
        for key in ("open_restate", "adjacent"):
            v = [r[1][key] for r in rows]
            print(f"{key:13} p50={q(v,.5):.2f} p75={q(v,.75):.2f} p90={q(v,.9):.2f} max={max(v):.2f}")
        fs = [max((len(s["foreign"]) for s in r[2]["sections"]), default=0) for r in rows if r[0]["own"]]
        print(f"max foreign terms in a section: p50={q(fs,.5)} p75={q(fs,.75)} p90={q(fs,.9)} max={max(fs)}")
    rep_fail = sum(1 for r in rows if not r[1]["ok"])
    open_fail = sum(1 for r in rows if r[1]["open_restate"] >= el._REP_OPEN_JACCARD)
    adj_fail = sum(1 for r in rows if r[1]["adjacent"] >= el._REP_ADJ_OVERLAP)
    has_own = [r for r in rows if r[0]["own"]]
    print(f"thresholds: open>={el._REP_OPEN_JACCARD} adj>={el._REP_ADJ_OVERLAP} "
          f"foreign>={el._OWN_FOREIGN_MIN} share>={el._OWN_FOREIGN_SHARE}")
    print(f"repetition check fails : {rep_fail}/{n} ({100*rep_fail//n}%)   [opening-restate {open_fail}, adjacent {adj_fail}]")
    # Two bounds on the own-source side. LENIENT counts a term found in ANY other book's notes as cross-book
    # (flagged, not rejected - the live gather only carries <=12 related notes, so live sits between the two).
    # STRICT counts cross-book as not-this-book's, so it is an upper bound on fails (it also fails essays whose
    # own notes are only partly on disk).
    big = [r for r in has_own if len(r[0]["own"]) >= 8]
    for label, use_cross in (("LENIENT (any other book counts as cross-book)", True), ("STRICT (cross-book not counted)", False)):
        res = []
        for e, rep, _ in rows:
            if not e["own"]:
                res.append((e, rep["ok"], True)); continue
            src = el.check_own_source(e["body"], NL.join(e["own"]), NL.join(e["cross"]) if use_cross else "", e["title"])
            res.append((e, rep["ok"], src["ok"]))
        p_all = sum(1 for _, a, b in res if a and b)
        p_big = sum(1 for e, a, b in res if len(e["own"]) >= 8 and a and b)
        s_fail = sum(1 for e, a, b in res if e["own"] and not b)
        print(f"{label:48}: own-source fails {s_fail}/{len(has_own)} | PASS BOTH {p_all}/{n} ({100*p_all//n}%)"
              f" | of the {len(big)} essays with >=8 own notes on disk: {p_big} ({100*p_big//max(1,len(big))}%)")
    print("(essays with no own notes on disk are judged on repetition only: %d)" % (n - len(has_own)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

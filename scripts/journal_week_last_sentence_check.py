"""
J-3239 / D-0628 reader: how often is the week page's CLOSING sentence flagged as not in the sources?

D-0628 (founder, 2026-11-02) reworded the last question of core/journal_rollup.py _DID_SYS to an open one
("what changed from the first day to the last, if anything"). Its defeater: after 4 weekly pages under the
new wording, if the closing sentence is still flagged as not in the sources on MOST pages, drop it (option c).
The check must be by something other than the author, so this reads the P-0093 journal-grounding shadow
(data/journal_grounding_shadow.jsonl, a different-model judge + deterministic verifier) and looks at that
ONE sentence only.

READ-ONLY. Reads data/Journal/WEEK_<wid>.md ("## the days" section = the did stream) and the shadow log; writes
nothing. Usage (from the repo root of the tree whose data you want to read):

    python scripts/journal_week_last_sentence_check.py --from-wid 2026-W46        # first week under new wording
    python scripts/journal_week_last_sentence_check.py --from-wid 2026-W35 --to-wid 2026-W42   # old-wording baseline

A page counts as FLAGGED when its closing sentence matches (normalised, either-way substring) any phrase in the
shadow row's `invented_raw` (the judge's raw accusation list) -- `invented_genuine` is the subset the
deterministic verifier also upheld, reported alongside so a judge false-flag is not mistaken for an invention.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_WIDRE = re.compile(r"WEEK_(\d{4}-W\d{2})\.md$")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", re.sub(r"\s+", " ", (s or "").lower())).strip()


def days_section(text: str) -> str:
    """The 'the days' (did stream) body of a WEEK_*.md file, '' if absent."""
    m = re.search(r"^##\s+the days\s*$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    return (m.group(1) if m else "").strip()


def last_sentence(body: str) -> str:
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", body.strip()) if p.strip()]
    return parts[-1] if parts else ""


def _hit(sentence: str, phrases) -> bool:
    ns = _norm(sentence)
    if not ns:
        return False
    for p in phrases or []:
        npz = _norm(str(p))
        if len(npz) >= 6 and (npz in ns or ns in npz):
            return True
    return False


def check(journal_dir: Path, shadow_log: Path, from_wid: str, to_wid: str | None = None) -> dict:
    rows = {}
    try:
        for line in shadow_log.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("stream") == "did" and r.get("wid"):
                rows[r["wid"]] = r                       # latest row per week wins
    except FileNotFoundError:
        pass
    pages = []
    for p in sorted(journal_dir.glob("WEEK_*.md")):
        m = _WIDRE.search(p.name)
        if not m:
            continue
        wid = m.group(1)
        if wid < from_wid or (to_wid and wid > to_wid):
            continue
        sent = last_sentence(days_section(p.read_text(encoding="utf-8")))
        row = rows.get(wid)
        if row is None:
            pages.append({"wid": wid, "sentence": sent, "graded": False})
            continue
        pages.append({
            "wid": wid, "sentence": sent, "graded": True,
            "flagged": _hit(sent, row.get("invented_raw")),
            "genuine": _hit(sent, row.get("invented_genuine")),
        })
    graded = [x for x in pages if x["graded"]]
    flagged = sum(1 for x in graded if x["flagged"])
    return {"pages": pages, "n_pages": len(pages), "n_graded": len(graded), "n_flagged": flagged,
            "n_genuine": sum(1 for x in graded if x["genuine"]),
            "defeater_met": bool(len(graded) >= 4 and flagged * 2 > len(graded))}


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--from-wid", required=True, help="first ISO week id under the wording to measure, e.g. 2026-W46")
    ap.add_argument("--to-wid", default=None)
    ap.add_argument("--journal-dir", default=str(_ROOT / "data" / "Journal"))
    ap.add_argument("--shadow-log", default=str(_ROOT / "data" / "journal_grounding_shadow.jsonl"))
    a = ap.parse_args(argv)
    res = check(Path(a.journal_dir), Path(a.shadow_log), a.from_wid, a.to_wid)
    for x in res["pages"]:
        tag = "UNGRADED" if not x["graded"] else ("FLAGGED" if x["flagged"] else "ok") + (
            " (verifier upheld)" if x.get("genuine") else "")
        print(f"{x['wid']}  {tag:26}  {x['sentence']}")
    print(f"\npages {res['n_pages']}, graded {res['n_graded']}, flagged {res['n_flagged']}, "
          f"verifier-upheld {res['n_genuine']}")
    if res["n_graded"] < 4:
        print("fewer than 4 graded pages: D-0628's re-measure is not due yet.")
    elif res["defeater_met"]:
        print("D-0628 DEFEATER MET: flagged on most pages -> drop the sentence (option c); open a /decide.")
    else:
        print("D-0628 defeater not met: the closing sentence is not flagged on most pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

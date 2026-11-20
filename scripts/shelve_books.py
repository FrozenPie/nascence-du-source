"""
Nascence - SHELVE-ONLY book importer (2026-10-30, F-3215, docs/staged/world_shelf_gap.md)
==========================================================================================
Puts Project Gutenberg books on Du's shelf (data/books/) WITHOUT choosing for him.

Why not scripts/gutenberg.py `fetch`: that command sets the fetched book as his CURRENT book and rewrites
data/reading_state.json without the reading lock. A bulk fill that way would keep taking the book out of his
hands. core/library_hand.request_book additionally sets current, resets his own one-book-an-hour cooldown
(data/library_hand_state.json) and records a book_selection pick. This script does none of that: it writes
the book file and one log row, nothing else. He finds the books the way he finds any shelved book (shelf-look,
switch_to, the librarian's stacks).

Same rules as the library's own fetch so a shelved book is indistinguishable from one he asked for:
  filename   re.sub(r"[^\\w\\- ]", "", title)[:60].strip().replace(" ", "_") + ".txt"
  mirrors    cache/epub/N/pgN.txt, files/N/N-0.txt, files/N/N.txt
  cleaning   keep the text between the *** START OF ... *** and *** END OF markers when present

Differences (safety): atomic write (tmp then replace, so a glob of *.txt never sees half a book), a size sanity
check (an HTML error page is refused), a polite delay between books, and ids newer than the 2018 catalogue are
accepted (the title is then read from the Gutenberg header).

    python scripts/shelve_books.py --list PG1889 PG5177          # fetch these
    python scripts/shelve_books.py --batch 1                     # the 24 titles of batch 1
    python scripts/shelve_books.py --batch 2                     # the 21 titles of batch 2
    python scripts/shelve_books.py --dry-run --batch 1           # resolve names and sizes only, no network
    python scripts/shelve_books.py --out-dir C:\\tmp\\t --list PG1889   # test somewhere else
    python scripts/shelve_books.py --ia historybirdsnew1bull --title "Buller Vol 1 A History of the Birds of New Zealand"
        # a scanned book from archive.org: downloads {id}_djvu.txt and runs clean_ocr() (add --ia-file RAW.txt to reuse a download,
        # --dry-run to see the clean stats). clean_ocr removes only scan debris; see its docstring.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
META = Path(r"C:\Knowledge\SPGC-metadata-2018-07-18.csv")
BOOKS = ROOT / "data" / "books"
LOG = ROOT / "data" / "logs" / "shelve_books.jsonl"

# docs/staged/world_shelf_gap.md section 3. Batch 1 = birds, New Zealand, shore and sea, insects and bees.
BATCH = {
    1: ["PG1889", "PG5177", "PG3163", "PG4203", "PG31292", "PG7353", "PG37787", "PG45063", "PG47028",   # birds
        "PG56762", "PG45957", "PG6104", "PG11933", "PG60645",                                              # New Zealand
        "PG695", "PG43946", "PG35490", "PG37119", "PG47626", "PG24236",                                    # shore and sea
        "PG45812", "PG27868", "PG4511", "PG24583"],                                                        # insects and bees
    2: ["PG38928", "PG47059", "PG6630", "PG20769",                                                         # weather and sky
        "PG9550", "PG36279", "PG33654", "PG2355", "PG4342",                                                # garden
        "PG35450", "PG9501", "PG34110", "PG34229", "PG17093", "PG34607",                                   # cat, trap, craft
        "PG10136", "PG32863", "PG17625", "PG34114", "PG17576", "PG16116"],                                 # household
}
MIN_CHARS = 20_000          # a real book is bigger than this; an error page is not
UA = {"User-Agent": "Nascence-shelver/1.0 (personal research project; polite, one request at a time)"}


def catalogue(ids: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not META.exists():
        return out
    with open(META, encoding="utf-8", errors="ignore", newline="") as f:
        for r in csv.DictReader(f):
            if r["id"] in ids:
                out[r["id"]] = r
    return out


def safe_name(title: str, fallback: str) -> str:
    return re.sub(r"[^\w\- ]", "", title)[:60].strip().replace(" ", "_") or fallback


def download(n: str) -> str | None:
    for url in (f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt",
                f"https://www.gutenberg.org/files/{n}/{n}-0.txt",
                f"https://www.gutenberg.org/files/{n}/{n}.txt"):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="ignore")
        except Exception:
            continue
    return None


def header_title(text: str) -> str:
    m = re.search(r"^Title:\s*(.+?)\s*$", text[:6000], re.M)
    return m.group(1).strip() if m else ""


def clean(text: str) -> str:
    m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*)\*\*\* ?END OF", text, re.DOTALL | re.I)
    return (m.group(1) if m else text).strip()


def clean_ocr(text: str, start_marker: str = "A HISTORY") -> tuple[str, dict]:
    """Conservative clean of a scanned book's OCR text (archive.org *_djvu.txt). Only clear scan debris goes:
      - everything before the title page (library stamps, barcodes)
      - isolated page-number lines
      - symbol-only junk lines ('))', '>9', '-■x'): no letters or digits at all
      - running page headers: an ALLCAPS line of 30 chars or fewer repeated 10 or more times keeps its first copy
      - 3+ blank lines collapse to 2
      - line-end hyphen splits are joined ONLY when the joined word appears unsplit elsewhere in the same book
        (so 'inte-/resting' becomes 'interesting' but a real compound like 'bell-/bird' is left alone)
      - the one known title-page misread (DULLER for BULLER), first 4000 chars only
    Everything else, including OCR typos, footnotes and the index, is left as printed. Returns (text, stats)."""
    st = {"chars_in": len(text)}
    i = text.find(start_marker)
    if 0 < i < 3000:
        text = text[i:]
    lines = text.split("\n")
    caps = {}
    for l in lines:
        s = l.strip()
        if 3 <= len(s) <= 30 and s.isupper():
            caps[s] = caps.get(s, 0) + 1
    seen_head: set[str] = set()
    out: list[str] = []
    dropped = {"page_no": 0, "junk": 0, "header": 0}
    for k, l in enumerate(lines):
        s = l.strip()
        if s:
            if re.fullmatch(r"\d{1,4}", s) and (k == 0 or not lines[k - 1].strip()) and (k + 1 >= len(lines) or not lines[k + 1].strip()):
                dropped["page_no"] += 1; continue
            if len(s) <= 25 and not re.search(r"[A-Za-z0-9]", s):
                dropped["junk"] += 1; continue
            if s in caps and caps[s] >= 10:
                if s in seen_head:
                    dropped["header"] += 1; continue
                seen_head.add(s)
        out.append(l)
    text = "\n".join(out)
    words: dict[str, int] = {}
    for w in re.findall(r"[A-Za-z]{3,}", text):
        words[w.lower()] = words.get(w.lower(), 0) + 1
    joined = 0
    def _join(m: re.Match) -> str:
        nonlocal joined
        left, right = m.group(1), m.group(2)
        whole = (left + right).lower()
        if words.get(whole, 0) >= 1 and len(left) >= 2 and len(right) >= 2:
            joined += 1
            return left + right
        return m.group(0)
    text = re.sub(r"([a-z]{2,})-[ \t]*\n([a-z]{2,})", _join, text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    head, tail = text[:4000].replace("DULLER", "BULLER"), text[4000:]
    text = (head + tail).strip()
    st.update(chars_out=len(text), joined=joined, **{"dropped_" + k: v for k, v in dropped.items()})
    return text, st


def log(row: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", nargs="+", default=[])
    ap.add_argument("--batch", type=int, choices=sorted(BATCH))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-dir", default=str(BOOKS))
    ap.add_argument("--delay", type=float, default=3.0)
    ap.add_argument("--ia", help="archive.org identifier of a scanned book, e.g. historybirdsnew1bull (reads {id}_djvu.txt)")
    ap.add_argument("--ia-file", help="use an already-downloaded raw {id}_djvu.txt instead of downloading it again")
    ap.add_argument("--title", help="shelf title for an --ia book (names the file)")
    ap.add_argument("--start-marker", default="A HISTORY", help="text that begins the title page; everything before it is dropped")
    a = ap.parse_args()
    if a.ia:
        if not a.title:
            print("--ia needs --title"); return 1
        out_dir = Path(a.out_dir)
        out = out_dir / f"{safe_name(a.title, a.ia)}.txt"
        if out.exists():
            print(f"  {a.ia}: already on shelf: {out.name}"); return 0
        if a.ia_file:
            raw = Path(a.ia_file).read_text(encoding="utf-8", errors="replace")
        else:
            try:
                req = urllib.request.Request(f"https://archive.org/download/{a.ia}/{a.ia}_djvu.txt", headers=UA)
                with urllib.request.urlopen(req, timeout=120) as r:
                    raw = r.read().decode("utf-8", errors="replace")
            except Exception as e:
                print(f"  {a.ia}: DOWNLOAD FAILED ({type(e).__name__})"); log({"ts": time.time(), "id": a.ia, "ok": False, "why": "download"}); return 2
        body, stats = clean_ocr(raw, a.start_marker)
        if a.dry_run:
            print(f"  {a.ia}: would shelve {out.name}: {stats}"); return 0
        if len(body) < MIN_CHARS:
            print(f"  {a.ia}: REFUSED, only {len(body)} chars after cleaning"); return 2
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".txt.tmp")
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, out)
        print(f"  {a.ia}: shelved {out.name} ({len(body) // 1000}k chars) {stats}")
        log({"ts": time.time(), "id": a.ia, "ok": True, "title": a.title, "file": out.name, "chars": len(body), "source": "archive.org", "clean": stats})
        return 0
    ids = [i.upper() if i.upper().startswith("PG") else "PG" + i for i in a.list]
    if a.batch:
        ids += BATCH[a.batch]
    ids = list(dict.fromkeys(ids))
    if not ids:
        print("nothing to do; give --list or --batch"); return 1
    out_dir = Path(a.out_dir)
    cat = catalogue(set(ids))
    done = skipped = failed = 0
    for k, pg in enumerate(ids):
        n = pg[2:]
        meta = cat.get(pg)
        title = meta["title"] if meta else ""
        if a.dry_run:
            name = safe_name(title, pg) if title else "(title read from Gutenberg header at fetch time)"
            exists = bool(title) and (out_dir / f"{safe_name(title, pg)}.txt").exists()
            print(f"  {pg:>8}  {'EXISTS ' if exists else 'to fetch'}  {name}  [{'catalogue' if meta else 'not in 2018 catalogue'}]")
            continue
        if title and (out_dir / f"{safe_name(title, pg)}.txt").exists():
            print(f"  {pg}: already on shelf: {safe_name(title, pg)}.txt"); skipped += 1; continue
        text = download(n)
        if not text:
            print(f"  {pg}: DOWNLOAD FAILED on all mirrors"); failed += 1; log({"ts": time.time(), "id": pg, "ok": False, "why": "download"}); continue
        title = title or header_title(text) or pg
        out = out_dir / f"{safe_name(title, pg)}.txt"
        if out.exists():
            print(f"  {pg}: already on shelf: {out.name}"); skipped += 1; continue
        body = clean(text)
        if len(body) < MIN_CHARS:
            print(f"  {pg}: REFUSED, only {len(body)} chars after cleaning ({title[:50]})"); failed += 1
            log({"ts": time.time(), "id": pg, "ok": False, "why": "too_short", "chars": len(body)}); continue
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".txt.tmp")
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, out)
        print(f"  {pg}: shelved {out.name} ({len(body) // 1000}k chars)")
        log({"ts": time.time(), "id": pg, "ok": True, "title": title, "file": out.name, "chars": len(body)})
        done += 1
        if k < len(ids) - 1:
            time.sleep(a.delay)
    if not a.dry_run:
        print(f"shelved {done}, already there {skipped}, failed {failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())

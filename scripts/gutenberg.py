"""
Nascence — Gutenberg shelf (the world's library, made reachable)
================================================================
The local SPGC corpus (C:/Knowledge) is the CATALOGUE — 55,905 books of metadata — but its
token files are lowercase, punctuation-stripped streams (degraded food). So: search the local
catalogue, fetch the CLEAN text from gutenberg.org once, cache it in data/books/, strip the
PG boilerplate, and set it as Du's current book (the one his idle mind may choose to open).

    python scripts/gutenberg.py search verne              # find books (title/author match)
    python scripts/gutenberg.py search "natural history"
    python scripts/gutenberg.py fetch PG103               # download, clean, SET AS CURRENT BOOK
"""
import csv, json, re, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

META = Path(r"C:\Knowledge\SPGC-metadata-2018-07-18.csv")
BOOKS = Path(__file__).parent.parent / "data" / "books"
STATE = Path(__file__).parent.parent / "data" / "reading_state.json"


def rows():
    with open(META, encoding="utf-8", errors="ignore") as f:
        yield from csv.DictReader(f)


def search(term: str) -> None:
    t = term.lower()
    hits = [r for r in rows()
            if t in (r["title"] or "").lower() or t in (r["author"] or "").lower()]
    hits = [h for h in hits if "'en'" in (h["language"] or "")]
    hits.sort(key=lambda r: -int(r["downloads"] or 0))
    for r in hits[:15]:
        print(f"  {r['id']:>8}  {r['title'][:62]:<62}  {r['author'][:28]:<28} ({r['downloads']} dl)")
    print(f"{len(hits)} matches (top 15 by popularity). Fetch one: python scripts/gutenberg.py fetch <PGid>")


def fetch(pgid: str) -> None:
    meta = next((r for r in rows() if r["id"] == pgid), None)
    if not meta:
        print(f"{pgid} not in catalogue"); return
    n = pgid[2:]
    BOOKS.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w\- ]", "", meta["title"])[:60].strip().replace(" ", "_") or pgid
    out = BOOKS / f"{safe}.txt"
    if not out.exists():
        text = None
        for url in (f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt",
                    f"https://www.gutenberg.org/files/{n}/{n}-0.txt",
                    f"https://www.gutenberg.org/files/{n}/{n}.txt"):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    text = r.read().decode("utf-8", errors="ignore"); break
            except Exception:
                continue
        if not text:
            print("download failed on all mirrors"); return
        # strip PG boilerplate: keep between the START/END markers when present
        m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*)\*\*\* ?END OF", text, re.DOTALL | re.I)
        if m:
            text = m.group(1)
        out.write_text(text.strip(), encoding="utf-8")
        print(f"fetched + cleaned: {out.name} ({len(text)//1000}k chars)")
    else:
        print(f"already cached: {out.name}")
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    state["_current_book"] = str(out)
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(f"CURRENT BOOK set for Du: '{meta['title']}' by {meta['author']}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "search":
        search(" ".join(sys.argv[2:]))
    elif len(sys.argv) == 3 and sys.argv[1] == "fetch":
        fetch(sys.argv[2])
    else:
        print(__doc__)

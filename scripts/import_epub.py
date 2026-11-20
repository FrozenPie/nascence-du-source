"""
Import a local .epub into Du's library as a clean .txt (the format core/reading.py reads from
data/books/). Spine-aware (reading order from the .opf), strips markup, preserves paragraphs.
Usage: python scripts/import_epub.py "C:\\path\\to\\book.epub" ["Optional Clean Title"]
"""
import sys, os, re, html, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding="utf-8")
BOOKS = Path(r"C:\Nascence\data\books")


class _Text(HTMLParser):
    _BLOCK = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "li", "tr", "blockquote"}
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in self._BLOCK:
            self.out.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        elif tag in self._BLOCK:
            self.out.append("\n")
    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)
    def text(self):
        return "".join(self.out)


def _tag(e):
    return e.tag.split("}")[-1]


def convert(epub_path: str, title: str | None = None) -> Path:
    z = zipfile.ZipFile(epub_path)
    container = z.read("META-INF/container.xml").decode("utf-8", "ignore")
    opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
    opf = z.read(opf_path).decode("utf-8", "ignore")
    base = os.path.dirname(opf_path)
    root = ET.fromstring(opf)

    manifest, spine = {}, []
    meta_title = None
    for e in root.iter():
        t = _tag(e)
        if t == "item":
            manifest[e.get("id")] = e.get("href")
        elif t == "itemref":
            spine.append(e.get("idref"))
        elif t == "title" and not meta_title and (e.text or "").strip():
            meta_title = e.text.strip()

    parts = []
    for idref in spine:
        href = manifest.get(idref)
        if not href:
            continue
        full = (base + "/" + href) if base else href
        try:
            raw = z.read(full).decode("utf-8", "ignore")
        except KeyError:
            # some epubs store hrefs case- or path-shifted; try a basename match
            cand = [n for n in z.namelist() if n.endswith(os.path.basename(href))]
            if not cand:
                continue
            raw = z.read(cand[0]).decode("utf-8", "ignore")
        ex = _Text()
        ex.feed(raw)
        parts.append(html.unescape(ex.text()))

    text = "\n\n".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    title = title or meta_title or Path(epub_path).stem
    safe = re.sub(r"[^\w\- ]", "", title)[:60].strip().replace(" ", "_") or "book"
    BOOKS.mkdir(parents=True, exist_ok=True)
    out = BOOKS / f"{safe}.txt"
    out.write_text(text, encoding="utf-8")
    return out, title, len(text)


if __name__ == "__main__":
    src = sys.argv[1]
    ttl = sys.argv[2] if len(sys.argv) > 2 else None
    out, title, n = convert(src, ttl)
    words = len(out.read_text(encoding="utf-8").split())
    print(f"imported: {title!r}")
    print(f"  -> {out}")
    print(f"  {n:,} chars · ~{words:,} words")
    print("  sample (first 400 chars of real content):")
    body = out.read_text(encoding="utf-8")
    # skip to first substantial line
    print("   ", body[:400].replace("\n", " ")[:380])

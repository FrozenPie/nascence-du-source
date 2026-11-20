"""J-3288 step 2: deterministic present / paraphrased / absent classification of every study-note key_fact against its
recovered source passage (sample.json from _lab_J3288_build_sample.py). No LLM. Optional embedding signal (the same
MiniLM the store uses) is added as a second column, not used for the verdict.
Verdict rules (all lexical, on lowercase stems):
  present      >=0.85 of the fact's content stems occur inside ONE window of 3 consecutive passage sentences AND every
               number and every capitalised (proper) token of the fact occurs in the passage
  paraphrased  >=0.50 window coverage AND numbers/names ok
  absent       otherwise (low coverage, or a number / proper name the passage never contains)
`missing` lists the numbers/names not found. Run: python scripts/_lab_J3288_classify.py [--in sample.json] [--out facts.json] [--embed]"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

STOP = set("""the and for with from this that what which into about your his her their they are was were you not but all
has had have been its also than then there these those them who whom whose when where while would could should may might
will can one two three four five six seven eight nine ten each both more most other such only own same very just over
under between through during before after above below out off again further once any some our ours him she he it is in on
at by of to as an a or if so no nor too did does doing being""".split())
NUMW = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
        "twelve": "12", "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50", "hundred": "100", "thousand": "1000"}


def stem(w: str) -> str:
    w = w.lower().replace("'s", "").strip("'")
    for suf in ("ations", "ation", "ingly", "ing", "edly", "ies", "ied", "ed", "es", "ly", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def words(t: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019-]*", t.replace("\u2019", "'"))


def content_stems(t: str) -> set[str]:
    return {stem(w) for w in words(t) if w.lower() not in STOP and (len(w) >= 3 or w.isdigit())}


def sentences(t: str) -> list[str]:
    s = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", t) if x.strip()]
    return s


def numbers(t: str) -> set[str]:
    return {w for w in re.findall(r"\d[\d,.]*\d|\d", t)}


def names(fact: str) -> set[str]:
    ws = words(fact)
    out = set()
    for i, w in enumerate(ws):
        if i == 0 or not w[0].isupper() or w.lower() in STOP or w.isupper() and len(w) <= 2:
            continue
        out.add(stem(w))
    return out


def classify(fact: str, passage: str, sents: list[str], sent_stems: list[set[str]], pass_stems: set[str]) -> dict:
    fs = content_stems(fact)
    if not fs:
        return {"verdict": "unscorable", "cov_all": None, "cov_win": None, "missing": []}
    cov_all = len(fs & pass_stems) / len(fs)
    best = 0.0
    for i in range(len(sents)):
        w = set().union(*sent_stems[i:i + 3])
        best = max(best, len(fs & w) / len(fs))
    pnorm = passage.replace("\u2019", "'").lower()
    missing = [n for n in numbers(fact) if n.replace(",", "") not in pnorm.replace(",", "")
               and NUMW.get(n) not in pnorm.split()]
    missing += [n for n in names(fact) if n not in pass_stems]
    if best >= 0.85 and not missing:
        v = "present"
    elif best >= 0.50 and not missing:
        v = "paraphrased"
    else:
        v = "absent"
    return {"verdict": v, "cov_all": round(cov_all, 3), "cov_win": round(best, 3), "missing": missing}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(ROOT / "docs/lab/J-3288_data/sample.json"))
    ap.add_argument("--out", default=str(ROOT / "docs/lab/J-3288_data/facts.json"))
    ap.add_argument("--embed", action="store_true")
    a = ap.parse_args()
    d = json.load(open(a.inp, encoding="utf-8"))
    model = None
    if a.embed:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    rows = []
    for si, s in enumerate(d["sample"]):
        views = {}
        for k, txt in (("seen", s.get("passage_seen") or s["passage"][:5000]), ("full", s["passage"])):
            sents = sentences(txt)
            views[k] = (txt, sents, [content_stems(x) for x in sents], content_stems(txt))
        wins = [" ".join(views["full"][1][i:i + 2]) for i in range(len(views["full"][1]))] if model else []
        wv = model.encode(wins, normalize_embeddings=True, show_progress_bar=False, batch_size=64) if model and wins else None
        for fi, f in enumerate(s["key_facts"]):
            rs = classify(f, *views["seen"][0:1], *views["seen"][1:])
            rf = classify(f, *views["full"][0:1], *views["full"][1:])
            if rs["verdict"] in ("present", "paraphrased"):
                cat = "grounded_in_seen_window"
            elif rf["verdict"] in ("present", "paraphrased"):
                cat = "beyond_window"      # only matches text the model's prompt never contained (passage[:5000])
            else:
                cat = "absent_everywhere"
            r = {"category": cat, "seen": rs, "full": rf}
            if model is not None and wv is not None:
                fv = model.encode([f], normalize_embeddings=True, show_progress_bar=False)[0]
                r["cos_max_full"] = round(float((wv @ fv).max()), 3)
            rows.append({"note": si, "fact_idx": fi, "fragment_id": s["fragment_id"], "book": s["book"], "fact": f, **r})
    json.dump(rows, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    c = Counter(r["category"] for r in rows)
    c2 = Counter(r["seen"]["verdict"] for r in rows)
    print(len(rows), dict(c), {k: round(v / len(rows), 3) for k, v in c.items()})
    print("verdict vs seen window:", dict(c2), {k: round(v / len(rows), 3) for k, v in c2.items()})


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------------------------------------------------
# J-3288 (second half): the candidate DETERMINISTIC CHECK, in its most defensible cheap form -- "every number and every
# proper name a key_fact states must occur in the passage the writer saw". Content-word coverage (classify() above) was
# measured and is NOT usable alone (it flags a third of facts that a reader sees are in the passage: a paraphrase changes
# the words). Numbers and names are the part a paraphrase cannot change, so only they are checked, after folding the
# variation that is not a leak (accents, honorifics, spelled-out numbers, ethnonyms, OCR 'Seas' for 'Sens' is NOT folded).
import unicodedata

_HONOR = {"mr", "mrs", "mme", "madame", "mlle", "mademoiselle", "monsieur", "dr", "st", "saint", "sir", "lord", "lady", "la", "le",
          "les", "de", "du", "des", "von", "van", "the", "ii", "iii", "iv", "go", "i", "a"}
_ETHNO = {"russian": ("russ",), "polish": ("pol",), "dutch": ("dutch", "holland", "nether"), "french": ("fran", "fren"),
          "english": ("engl", "brit"), "austrian": ("aust",), "swiss": ("swit", "swiss"), "egyptian": ("egypt",), "vendean": ("vend",),
          "napoleonic": ("napol", "bonap"), "spanish": ("spa",), "persian": ("pers",), "italian": ("ital",), "german": ("germ",),
          "prussian": ("prus",), "turkish": ("turk",), "british": ("brit", "engl"), "ptolemaic": ("ptol",), "archduke": ("archduk",)}
_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _fold(t: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", t) if not unicodedata.combining(ch)).lower().replace("\u2019", "'")


def _spell(n: int) -> list[str]:
    """Content words an integer is spelled with ('1040000' -> one million forty thousand); order-free set is enough."""
    if n < 20:
        return [_ONES[n]]
    if n < 100:
        return [_TENS[n // 10]] + ([_ONES[n % 10]] if n % 10 else [])
    if n < 1000:
        return [_ONES[n // 100], "hundred"] + (_spell(n % 100) if n % 100 else [])
    for big, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= big:
            return _spell(n // big) + [name] + (_spell(n % big) if n % big else [])
    return []


def _num_found(num: str, ptext: str, ptoks: set[str]) -> bool:
    raw = num.replace(",", "").rstrip(".")
    if raw and raw in ptext.replace(",", ""):
        return True
    ordinal = re.findall(r"\b%s(?:st|nd|rd|th)\b" % re.escape(raw), ptext)
    if ordinal:
        return True
    if raw.isdigit() and int(raw) < 10 ** 10:
        return all(w in ptoks for w in _spell(int(raw)) if w != "zero")
    return False


def entity_missing(fact: str, passage: str) -> list[str]:
    """Numbers and proper names of `fact` that do not occur (after folding) in `passage`. [] = the check passes."""
    p = _fold(passage)
    ptoks = set(re.findall(r"[a-z0-9']+", p))
    pstems = {stem(t) for t in ptoks}
    out = []
    for num in set(re.findall(r"\d[\d,.]*\d|\d", fact)):
        if not _num_found(num, p, ptoks):
            out.append("#" + num)
    ws = [part for w in re.findall(r"[A-Za-z\u00C0-\u024F][A-Za-z\u00C0-\u024F'\u2019-]*", fact)
          for part in re.split(r"-+", w) if part]
    for i, w in enumerate(ws):
        f = _fold(w).strip("'-")
        if i == 0 or not w[0].isupper() or f in _HONOR or len(f) <= 2:
            continue
        if any(t.startswith(pre) for pre in _ETHNO.get(f, ()) for t in ptoks):
            continue
        stm = stem(f)
        if f in ptoks or stm in pstems or any(t.startswith(f[:5]) for t in ptoks if len(f) >= 5):
            continue
        out.append(w)
    return out

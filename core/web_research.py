"""
Nascence — Web Research + External Shocks (ported from FreshStart's Buddha, 2026-06-10)
=======================================================================================
The world, able to answer back. Two abilities, both Wikipedia REST (no keys, proven for
weeks in chronicle_engine._web_research):

  lookup(term)    — targeted summary fetch; falls back to serendipity on a miss.
  random_summary()— pure serendipity (Buddha's 40% mode — preserved deliberately).
  maybe_shock()   — EXTERNAL SHOCK: at most one uninvited world-event per SHOCK_INTERVAL_H,
                    for the idle mind. A closed system never gets interrupted from outside;
                    this is the interruption. (FreshStart Era 21's idea, sized for one mind.)

Findings are stored as origin='research' fragments — world-material, prune-protected,
loudly labelled as external fact. Fail-open everywhere: no network, no shock, no harm.
"""
from __future__ import annotations
import json
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path

_SHOCK_STATE = Path(__file__).parent.parent / "data" / "last_shock.json"
SHOCK_INTERVAL_H = 6
_UA = {"User-Agent": "Nascence/0.4 (single-mind research; founder-operated)"}

_STOP = {"about", "what", "where", "which", "their", "there", "these", "those", "would",
         "could", "should", "between", "because", "through", "myself", "really", "thing",
         "things", "question", "answer", "meaning", "becoming", "identity"}


def _fetch(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _usable(d: dict | None) -> bool:
    if not d:
        return False
    extract, title = d.get("extract", ""), d.get("title", "")
    return (len(extract) >= 150 and "may refer to" not in extract
            and not title.startswith(("List of", "Index of")))


def random_summary() -> tuple[str, str] | None:
    for _ in range(2):
        d = _fetch("https://en.wikipedia.org/api/rest_v1/page/random/summary")
        if _usable(d):
            return d["title"], d["extract"]
    return None


def term_from_question(question: str) -> str | None:
    """Deterministic: the most specific word in the question (longest non-stopword)."""
    words = [w.strip(".,;:!?'\"()").lower() for w in (question or "").split()]
    cands = [w for w in words if len(w) >= 6 and w.isalpha() and w not in _STOP]
    return max(cands, key=len) if cands else None


def lookup_targeted(term: str | None) -> tuple[str, str] | None:
    """Targeted summary ONLY — NO serendipity fallback. Returns None on a miss, so a caller answering a
    SPECIFIC question can choose a better fallback (the Scholar — his own knowledge) than a random article."""
    if term:
        enc = urllib.parse.quote(term.replace(" ", "_"))
        d = _fetch(f"https://en.wikipedia.org/api/rest_v1/page/summary/{enc}")
        if _usable(d):
            return d["title"], d["extract"]
    return None


def lookup(term: str | None) -> tuple[str, str] | None:
    """Targeted summary; on a miss (404/stub) fall through to serendipity — Buddha's pattern."""
    return lookup_targeted(term) or random_summary()


def store_finding(title: str, extract: str, via: str,
                  extra_keywords: list[str] | None = None) -> None:
    """Persist a finding as world-material memory. Best-effort.
    extra_keywords lets a TWIG be tagged with its parent study subject, so the finding
    co-retrieves with the branch it grew off (curiosity_node's side research)."""
    try:
        from core.memory.store import store_fragment
        kws = ["research", title.lower()[:40]] + [
            k.lower()[:40] for k in (extra_keywords or []) if k
        ]
        store_fragment(
            content=f"[Looked up: '{title}' ({via})] {extract[:900]}",
            layer="episodic", relevance=0.8, importance=0.8,
            keywords=kws, origin="research",
        )
    except Exception:
        pass


def maybe_shock() -> tuple[str, str] | None:
    """At most one uninvited world-event per SHOCK_INTERVAL_H. Returns (title, extract) or None."""
    try:
        last = json.loads(_SHOCK_STATE.read_text(encoding="utf-8")).get("ts", 0) \
            if _SHOCK_STATE.exists() else 0
        if time.time() - last < SHOCK_INTERVAL_H * 3600:
            return None
        got = random_summary()
        if not got:
            return None
        _SHOCK_STATE.write_text(json.dumps({"ts": time.time(), "title": got[0]}), encoding="utf-8")
        store_finding(got[0], got[1], via="external shock — uninvited")
        return got
    except Exception:
        return None


# ── THE WEB HAND's fetchers (J-3843 / D-0788, 2026-11-16). ADDITIVE: nothing above is changed. ──────────────
# core/web_hand.py is the only caller. The SOURCE resolves his phrase (Wikipedia's own search; a search engine's
# own ranking), never a model and never the longest-word rule above. Every function returns None when the source
# could not be reached and an empty list / None-page when it was reached and had nothing, so the hand can tell
# "no answer" from "no connection".
_HAND_TIMEOUT_S = 8
# A plain browser identity for the search engine (no project details are sent to it).
_BROWSER_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
               "Accept-Language": "en-US,en;q=0.8"}


def _fetch_raw(url: str, headers: dict, timeout: float = _HAND_TIMEOUT_S) -> tuple[bool, str]:
    """(reached, body). A 404 is reached with '' (the source says there is no such page). A transport failure,
    a rate-limit status (429) or a server error is NOT reached: the source gave no answer either way."""
    import urllib.error
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return (e.code == 404), ""
    except Exception:
        return False, ""


_Q_LEAD = ("why", "how", "what", "who", "where", "when", "whether", "is", "are", "was", "were", "do", "does",
           "did", "can", "could", "the", "a", "an")


def _query_terms(phrase: str) -> str:
    """His phrase with leading question words and articles dropped ("why the woodpecker's head is red" ->
    "woodpecker's head is red"). A fixed word list, no model: Wikipedia's search still does the resolving."""
    words = (phrase or "").split()
    while len(words) > 1 and words[0].lower() in _Q_LEAD:
        words = words[1:]
    return " ".join(words)


def wiki_titles(phrase: str, limit: int = 3) -> list[str] | None:
    """Wikipedia's own resolution of his phrase: the page of that exact name first (Wikipedia follows its own
    redirects, "Myrtle Warbler" -> "Yellow-rumped warbler"), then its full-text search ranking. Its title-prefix
    'opensearch' is NOT used: measured 2026-11-16 it returned "Porcupine Hills Provincial Park" for "porcupine
    quills" where the full-text search returns "Porcupine". None = no answer from Wikipedia (unreachable or
    rate-limited); [] = it answered and has nothing."""
    q = _query_terms(phrase)
    titles: list[str] = []
    ok, body = _fetch_raw("https://en.wikipedia.org/api/rest_v1/page/summary/"
                          + urllib.parse.quote(q.replace(" ", "_"), safe=""), _UA)
    if ok and body:
        try:
            d = json.loads(body)
            if d.get("title") and d.get("type") != "disambiguation":
                titles.append(str(d["title"]))
        except Exception:
            pass
    ok, body = _fetch_raw("https://en.wikipedia.org/w/api.php?action=query&list=search&format=json"
                          f"&srlimit={int(limit)}&srnamespace=0&srsearch={urllib.parse.quote(q)}", _UA)
    if not ok:
        return titles or None
    try:
        d = json.loads(body)
    except Exception:
        return titles or None
    for r in d.get("query", {}).get("search", []):
        t = str(r.get("title") or "")
        if t and t not in titles:
            titles.append(t)
    return titles[:limit]


def wiki_page(title: str) -> tuple[str, str] | None:
    """(title, extract) of one named page when it is a usable article; None otherwise (stub, list, disambiguation)."""
    ok, body = _fetch_raw("https://en.wikipedia.org/api/rest_v1/page/summary/"
                          + urllib.parse.quote(title.replace(" ", "_"), safe=""), _UA)
    if not ok or not body:
        return None
    try:
        d = json.loads(body)
    except Exception:
        return None
    if d.get("type") == "disambiguation" or not _usable(d):
        return None
    return d["title"], d["extract"]


def _strip_html(s: str) -> str:
    import html as _html
    import re as _re
    s = _re.sub(r"<[^>]+>", "", s or "")
    s = _html.unescape(s)
    s = _re.sub(r"[\x00-\x1f\x7f]", " ", s)
    return " ".join(s.split())


def _ddg_search(phrase: str, limit: int) -> list[dict] | None:
    """DuckDuckGo's keyless HTML endpoint (D-0788: keyless first; fragile by nature, see the ruling's defeater)."""
    import re as _re
    ok, body = _fetch_raw("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(phrase), _BROWSER_UA)
    if not ok:
        return None
    if 'class="result__a"' not in body and ("challenge" in body or "bots use" in body):
        # The engine asked for a human check. That is its refusal; it is reported as no answer, never worked around.
        global last_web_error
        last_web_error = "blocked"
        return None
    out: list[dict] = []
    for block in body.split('class="result__a"')[1:]:
        m = _re.search(r'href="([^"]+)"[^>]*>(.*?)</a>', block, _re.S)
        if not m:
            continue
        href, title = _strip_html(m.group(1)), _strip_html(m.group(2))
        if "duckduckgo.com/y.js" in href:        # an advertisement, not a result
            continue
        u = _re.search(r"[?&]uddg=([^&]+)", href)
        url = urllib.parse.unquote(u.group(1)) if u else href
        if url.startswith("//"):
            url = "https:" + url
        sm = _re.search(r'class="result__snippet"[^>]*>(.*?)</a>', block, _re.S)
        snippet = _strip_html(sm.group(1)) if sm else ""
        domain = (urllib.parse.urlparse(url).hostname or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if title and domain and snippet:
            out.append({"title": title, "url": url, "domain": domain, "snippet": snippet})
        if len(out) >= limit:
            break
    return out


def _brave_search(phrase: str, limit: int) -> list[dict] | None:
    """Brave Search API (keyed). UNTESTED as of 2026-11-16: no key was available to run it. The key is read
    from the environment variable NASCENCE_BRAVE_API_KEY and is never logged or stored."""
    import os as _os
    key = _os.environ.get("NASCENCE_BRAVE_API_KEY", "").strip()
    if not key:
        return None
    ok, body = _fetch_raw("https://api.search.brave.com/res/v1/web/search?count=" + str(int(limit))
                          + "&q=" + urllib.parse.quote_plus(phrase),
                          {"Accept": "application/json", "X-Subscription-Token": key})
    if not ok or not body:
        return None
    try:
        rows = json.loads(body).get("web", {}).get("results", [])
    except Exception:
        return None
    out: list[dict] = []
    for r in rows:
        url = str(r.get("url") or "")
        domain = (urllib.parse.urlparse(url).hostname or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        title, snippet = _strip_html(str(r.get("title") or "")), _strip_html(str(r.get("description") or ""))
        if title and domain and snippet:
            out.append({"title": title, "url": url, "domain": domain, "snippet": snippet})
    return out


_SEARCH_BACKENDS = {"ddg": _ddg_search, "brave": _brave_search}
last_web_error = ""        # "blocked" when the last web_search was refused by the engine's bot check


def web_search(phrase: str, limit: int = 10) -> list[dict] | None:
    """[{title, url, domain, snippet}] from the configured search backend (NASCENCE_WEB_SEARCH_BACKEND, default
    'ddg', or 'brave' when NASCENCE_BRAVE_API_KEY is set). None = unreachable; [] = nothing."""
    import os as _os
    global last_web_error
    last_web_error = ""
    _default = "brave" if _os.environ.get("NASCENCE_BRAVE_API_KEY", "").strip() else "ddg"
    fn = _SEARCH_BACKENDS.get(_os.environ.get("NASCENCE_WEB_SEARCH_BACKEND", _default).strip().lower(), _ddg_search)
    try:
        return fn(phrase, limit)
    except Exception:
        return None


def store_web_results(phrase: str, body: str) -> None:
    """Persist web-search snippets as world-material under their OWN prefix, so no reader can take them for a
    Wikipedia page or for his own words (core/schema.readable_label branches on '[Searched the web:')."""
    try:
        from core.memory.store import store_fragment
        store_fragment(
            content=f"[Searched the web: '{phrase}' (searched by him)] {body[:900]}",
            layer="episodic", relevance=0.7, importance=0.6,
            keywords=["research", "web search", "searched", phrase.lower()[:40]], origin="research",
        )
    except Exception:
        pass

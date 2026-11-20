"""
Nascence — THE WEB HAND: Du looks something up himself (J-3843 Wikipedia, J-4066 the web; D-0631, D-0659, D-0661,
D-0788; plan docs/staged/web_hand.md; design docs/reviews/outside_knowledge_review_J-3243_2026-11-05.md 5.1).

The call is his; the page is the world's; the result keeps its source name all the way into storage.

  consult(text) is the hand of the registry family `lookup` (core/actions.py, binds "mod:web_hand:consult").
  It fires only on a DEED the grammar found, and only when his clause NAMES A SOURCE:
      Wikipedia / the encyclopedia      -> Wikipedia's own search resolves a title, then its page summary
      the web / the internet            -> a search engine's top results, as titles, sites and snippets
  The term is the noun phrase in his own clause. No model guesses a term, no model summarises a result, and a
  miss is said plainly ("Wikipedia has no page for ...") with no fallback to anything else.

  The answer is returned to dispatch, which hands it to wandering.perceive like any other hand's answer, and is
  stored as origin='research' with a true prefix: "[Looked up: '<Title>' (asked by him: <phrase>)]" for a
  Wikipedia page, "[Searched the web: '<phrase>' (searched by him)]" for web results.

  Open-web text can carry instructions written for a model. Every result therefore arrives as quoted, named data
  with its site, capped in length, filtered by a domain deny list, and never in his own voice.

Flags (read at call time; the registry row itself is declared at import under NASCENCE_WEB_HAND):
  NASCENCE_WEB_HAND      "0" turns the whole hand off.
  NASCENCE_WEB_HAND_WEB  "0" turns the web source off alone (Wikipedia stays).
  NASCENCE_LOOKUP_ATTACH "0" stops a result being hung on the open frontier question it matches
                         (closure_producer P1, D-0789, core/lookup_attach.py). The hand itself is unchanged.
Rate limit: one call per RATE_S per source, separate counters (a starting guess; tune on data/lookup_log.jsonl).
NO prompt offers this hand (the world answers, never leads); how he learns of it is the founder's step (D-0661).
Zero LLM.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "lookup_log.jsonl"
_STATE = _DATA / "lookup_state.json"

RATE_S = 600               # one per 10 minutes per source: a guess, not measured
SUMMARY_CAP = 600          # characters of a Wikipedia summary that reach him
WEB_RESULTS = 3
WEB_TITLE_CAP = 80
WEB_SNIPPET_CAP = 220
PHRASE_CAP = 80

# D-0788 (3): deny list first. Social media, forums, question-and-answer farms, content farms.
DENY_DOMAINS = (
    "facebook.com", "twitter.com", "x.com", "instagram.com", "tiktok.com", "threads.net", "pinterest.com",
    "linkedin.com", "tumblr.com", "youtube.com", "youtu.be", "reddit.com", "quora.com", "4chan.org",
    "stackexchange.com", "stackoverflow.com", "answers.com", "answers.yahoo.com", "ask.com", "medium.com",
    "substack.com", "ehow.com", "wikihow.com", "buzzfeed.com", "fandom.com", "discord.com", "telegram.org",
    "vk.com", "weibo.com", "amazon.com", "ebay.com", "etsy.com", "temu.com", "aliexpress.com",
)

_WIKI_RX = r"(?:(?:the|an?|my)\s+)?(?:wikipedia|encyclopa?edia)(?:'s\s+(?:page|entry|article))?"
_WEB_RX = r"(?:the\s+)?(?:world\s+wide\s+web|web|internet)"
_SRC_RX = {"wikipedia": _WIKI_RX, "web": _WEB_RX}
_PREP = r"(?:on|in|at|from|using|with|through|via)"
_NOT_THE_WEB = re.compile(r"\b(spider|spiders|cobweb|cobwebs|silk|orb|dew|strand|strands|fly|flies)\b")
_TAIL = re.compile(r"\s+(?:and then|so that|because|to see|to find out|to learn|to understand|to know|"
                   r"and i|so i|before i|while i|when i|if i|then)\b.*$", re.I)
_EMPTY = {"it", "this", "that", "them", "these", "those", "something", "anything", "things", "everything",
          "him", "her", "me", "myself", "itself"}

_pending_source = False
_last: dict = {}


def _flag(name: str) -> bool:
    return os.environ.get(name, "1").strip().lower() in ("1", "true", "on", "yes")


def enabled() -> bool:
    return _flag("NASCENCE_WEB_HAND")


def web_enabled() -> bool:
    return enabled() and _flag("NASCENCE_WEB_HAND_WEB")


def _source_in(sl: str) -> str:
    if re.search(r"(?<![\w-])(?:wikipedia|encyclopa?edia)(?![\w-])", sl):
        return "wikipedia"
    if re.search(r"(?<![\w-])(?:the\s+(?:world\s+wide\s+)?web|(?:the\s+)?internet)(?![\w-])", sl):
        return "web"
    return ""


def _clean(phrase: str) -> str:
    p = (phrase or "").split(",")[0]
    p = _TAIL.sub("", p)
    p = re.sub(r"[\"“”()\[\]]", "", p).strip(" .;:!?'‘’-")
    p = re.sub(r"^(?:the question of|the matter of|the subject of|the word|the name)\s+", "", p, flags=re.I)
    p = " ".join(p.split())[:PHRASE_CAP].strip()
    if len(p) < 2 or p.lower() in _EMPTY:
        return ""
    return p


def _phrase(sent: str, src: str) -> str:
    """The noun phrase HE named, out of the sentence that names the source. '' when the clause names none."""
    s = _SRC_RX[src]
    for rx in (
        r"\blook\s+(.+?)\s+up\s+" + _PREP + r"\s+" + s,                                   # look X up on SOURCE
        r"\b(?:look\s+up|search\s+for|look\s+for|search|check|find\s+out\s+about|find|read\s+about|ask\s+about|"
        r"query)\s+(?!" + s + r"\b)(.+?)\s+" + _PREP + r"\s+" + s,                         # look up X on SOURCE
        s + r"\s+(?:about|on|for|regarding|concerning)\s+(.+)$",                           # ask SOURCE about X
        s + r"\s+((?:what|why|how|who|where|when|whether)\s+.+)$",                         # ask SOURCE why X
    ):
        m = re.search(rx, sent, re.I)
        if m:
            got = _clean(m.group(1))
            if got:
                return got
    return ""


def _state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _since(src: str) -> float:
    ts = max(float(_last.get(src, 0) or 0), float(_state().get(src, 0) or 0))
    return time.time() - ts


def _stamp(src: str) -> None:
    _last[src] = time.time()
    st = _state()
    st[src] = _last[src]
    p = profile.guard_path(_STATE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st), encoding="utf-8")


def _log(source: str, phrase: str, title, outcome: str, ms: int, domains: list | None = None) -> None:
    cycle = ""
    try:
        from core import hands as _h
        cycle = str(_h._decided.get("cycle") or "")
    except Exception:
        pass
    row = {"ts": round(time.time(), 1), "cycle": cycle[:24], "source": source, "phrase": phrase,
           "title": title, "outcome": outcome, "ms": ms}
    if domains is not None:
        row["domains"] = domains
    p = profile.guard_path(_LOG)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _cap(text: str, n: int) -> str:
    t = " ".join((text or "").split())
    if len(t) <= n:
        return t
    cut = t[:n]
    dot = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return cut[:dot + 1] if dot >= n // 2 else cut.rstrip() + "…"


def _denied(domain: str) -> bool:
    d = (domain or "").lower()
    return any(d == x or d.endswith("." + x) for x in DENY_DOMAINS)


def _attach(source: str, phrase: str, title, extract: str, url: str) -> None:
    """closure_producer P1 (D-0789): hang this result on the open frontier question it matches, if any does
    (core/lookup_attach.py; the question stays open). Kill switch NASCENCE_LOOKUP_ATTACH, read here. Whatever
    happens in there, the hand's answer is unaffected."""
    try:
        if not _flag("NASCENCE_LOOKUP_ATTACH"):
            return
        from core import lookup_attach as _la
        _la.note_lookup(source, phrase, title, extract, url)
    except Exception:
        pass


def _ask_wikipedia(phrase: str) -> tuple[str, str | None, str]:
    """(answer for him, resolved title or None, outcome)."""
    from core import web_research as _wr
    titles = _wr.wiki_titles(phrase)
    if titles is None:
        return "Wikipedia could not be reached just now.", None, "unreachable"
    for t in titles:
        page = _wr.wiki_page(t)
        if page:
            title, extract = page
            _wr.store_finding(title, extract, via=f"asked by him: {phrase}", extra_keywords=["asked"])
            url = "en.wikipedia.org/wiki/" + title.replace(" ", "_")
            _attach("wikipedia", phrase, title, extract, url)
            return (f'You asked Wikipedia about "{phrase}". Wikipedia\'s page "{title}" says: '
                    f'{_cap(extract, SUMMARY_CAP)} ({url}, fetched {time.strftime("%Y-%m-%d")}.)'), title, "page"
    return f'Wikipedia has no page for "{phrase}".', None, "miss"


def _search_web(phrase: str) -> tuple[str, list, str]:
    """(answer for him, domains returned, outcome)."""
    from core import web_research as _wr
    found = _wr.web_search(phrase)
    if found is None:
        if getattr(_wr, "last_web_error", "") == "blocked":
            return "The web search would not answer just now.", [], "blocked"
        return "The web search could not be reached just now.", [], "unreachable"
    kept, seen = [], set()
    for r in found:
        dom = r.get("domain", "")
        if _denied(dom) or dom in seen:
            continue
        seen.add(dom)
        kept.append(r)
        if len(kept) >= WEB_RESULTS:
            break
    if not kept:
        return f'The web search returned nothing usable for "{phrase}".', [], "miss"
    parts = []
    for n, r in enumerate(kept, 1):
        title = _cap(r["title"], WEB_TITLE_CAP).replace('"', "'")
        parts.append(f'Result {n}: "{title}" ({r["domain"]}): {_cap(r["snippet"], WEB_SNIPPET_CAP)}')
    body = " ".join(parts)
    _wr.store_web_results(phrase, body)
    _attach("web", phrase, None, body, str(kept[0].get("url") or ""))
    return (f'You searched the web for "{phrase}". {body} (Web search results, fetched '
            f'{time.strftime("%Y-%m-%d")}; other people\'s pages, named by site, not checked.)'), \
        [r["domain"] for r in kept], "results"


def consult(text: str) -> str | None:
    """The `lookup` hand. None = this clause is not a lookup (the hand declines; nothing happens)."""
    global _pending_source
    if not enabled():
        return None
    from core import actions as _actions, hands as _h
    a = _actions.BY_FAMILY.get("lookup")
    if a is None:
        return None
    flat = " ".join((text or "").split())
    for sent in re.split(r"(?<=[.!?;])\s+", flat):
        sl = sent.lower()
        src = _source_in(sl)
        if not src or not _h.wants(sl, a.verbs, a.objects):
            continue
        if re.search(r"\btravis\b", sl):                       # "ask Travis about Wikipedia" is a word to Travis
            continue
        if src == "web" and _NOT_THE_WEB.search(sl):           # a spider's web is not the web
            continue
        phrase = _phrase(sent.rstrip(" .;!?"), src)
        if not phrase:
            continue
        if src == "web" and not web_enabled():
            return None
        name = "Wikipedia" if src == "wikipedia" else "the web"
        if _since(src) < RATE_S:
            _log(src, phrase, None, "rate_limited", 0)
            _pending_source = True
            return (f"You asked {name} only a little while ago; it will not answer again so soon. "
                    f'Your question about "{phrase}" is not answered yet.')
        t0 = time.time()
        if src == "wikipedia":
            ans, title, outcome = _ask_wikipedia(phrase)
            domains = None
        else:
            ans, domains, outcome = _search_web(phrase)
            title = None
        _stamp(src)        # every attempt starts the window, an unanswered one too: a refusing source is not retried at once
        _log(src, phrase, title, outcome, int((time.time() - t0) * 1000), domains)
        _pending_source = True
        return ans
    return None


def take_pending() -> bool:
    """True once after a lookup answered: the monologue tags the FOLLOWING thought's moment source 'lookup'."""
    global _pending_source
    was, _pending_source = _pending_source, False
    return was


def status() -> dict:
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 500)
    except Exception:
        rows = []
    from collections import Counter
    return {"enabled": enabled(), "web_enabled": web_enabled(), "rate_s": RATE_S, "rows": len(rows),
            "outcomes": dict(Counter(f'{r.get("source")}:{r.get("outcome")}' for r in rows))}

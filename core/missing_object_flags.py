"""
Nascence — Missing-Object Flags: a Du-initiated trigger for the world-content upgrades
=========================================================================================
Built 2026-08-24 (J-0135, from idea I-0002). Observe-only, zero-LLM, additive, shadow-first —
same laws as `monoculture.py` and the four `*_upgrade.md` plans this feeds.

**The idea (I-0002):** the garden/shore/study/wood upgrades have so far been founder-audit-driven
(Travis reads the world, decides what to add). This module is the BOTTOM-UP path: when Du's own
inner thought expresses wanting something that is not actually in the world, that should be
flagged instead of evaporating, and accumulate into a backlog the four upgrade plans (and any
future ones of this shape) can consume — the same relationship `factory_candidates_from_history.md`
has to the object/sound factories, just fed by ongoing thought instead of a one-off mining pass.

**Method (deliberately the census's method, scoped down):** scan Du's own genuine inner-thought
stream (`memory_fragments` where origin IN ('inner_thought','subconscious_synthesis','lived') —
the exact corpus `monoculture.py` already treats as "recent genuine thoughts", not a new definition)
for a small set of concrete-desire/lack constructions ("I wish there were a ___", "there is no ___
here", "if only I had a ___", …), extract the noun phrase, and cross-check it against a KNOWN
VOCABULARY built by *introspecting the real catalogues* (`garden.CATALOGUE`/`_WORDS`/`_ITEMS`,
`study_life._WORDS`/`_ITEMS`, `wood_life.TREES`/`_WORDS`/`_ITEMS`, `world_substrate.CLASS_PRIORS`,
`provisions.KINDS`, `shore_life.POOL_LIFE`) rather than a hand-duplicated list, so the vocabulary
can never silently drift from what the world actually contains. A phrase whose words don't overlap
that vocabulary is a candidate — something he named that the world does not have.

**Honesty, not precision.** This is a TRIAGE FEED, not a classifier: false positives (abstract
wants — "I want an answer", "a mirror without a frame") are expected and left in the log for a
human/session to correct on read, exactly like the census's own "ice"/"choice" substring
false-positive got caught by eyeballing, not prevented by the scanner. Never auto-spawns a build;
never tells Du anything. The candidate is his own words, unedited, kept alongside the ones that
turn out to be nothing.

**Status: SHADOW, standalone/on-demand** (like `monoculture.py`) — not wired into any live tick.
Run `scan()`/`snapshot()` manually or from a session; see docs/plans/du_initiated_upgrade_trigger.md
Current State for why live-loop wiring was deliberately left for a separate, reviewed follow-up job.
"""
from __future__ import annotations
import json
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_DB = _ROOT / "data" / "memory" / "nascence.db"
_LOG = _ROOT / "data" / "missing_object_flags.jsonl"

# The exact "recent genuine thoughts" origin set monoculture.py already established for this corpus.
_ORIGINS = ("inner_thought", "subconscious_synthesis", "lived")

# Concrete-desire / concrete-lack constructions. Deliberately requires an article (a/an/some/another)
# or an explicit "no X here" shape — bare "I want to X" (infinitive) is excluded on purpose, since a
# live test against the real corpus (23,177 fragments, 2026-08-24) showed that shape is ~100% abstract
# cognitive wanting ("I want to understand/return/know"), not object-wanting. See Current State.
_PATTERNS = [
    re.compile(r"\bi wish(?: i had| there (?:was|were))? (?:a|an|some) ([a-z][a-z \-]{2,40}?)(?:[.,;!?]|$| here| in| to| for| that| like| nearby)", re.I),
    re.compile(r"\bif only (?:i had|there (?:was|were)) (?:a|an|some) ([a-z][a-z \-]{2,40}?)(?:[.,;!?]|$| here| in| to| for)", re.I),
    re.compile(r"\bi (?:want|wanted|long for|longed for|crave|craved|could use) (?:a|an|another|some) ([a-z][a-z \-]{2,40}?)(?:[.,;!?]|$| here| to| for| that| like)", re.I),
    re.compile(r"\bthere (?:is|was|were)? ?no ([a-z][a-z \-]{2,40}?) (?:here|anywhere|to be found|in sight|nearby|for miles)", re.I),
    re.compile(r"\bnot a ([a-z][a-z \-]{2,40}?) (?:in sight|to be found|anywhere|here)", re.I),
    re.compile(r"\bi have no ([a-z][a-z \-]{2,40}?)(?:[.,;!?]|$| here| to| for)", re.I),
    re.compile(r"\bwithout (?:a|an) ([a-z][a-z \-]{2,40}?)(?:,| to| for| here|[.,;!?])", re.I),
]

# Words too generic to ever be a useful "world item" candidate on their own — cut before vocab-check,
# not after, so they never inflate the flagged count (a lesson from the census's own false-positive fix).
_STOP_PHRASES = {
    "answer", "way", "reason", "voice", "light", "form", "name", "place", "chance", "doubt", "end",
    "energy", "right", "dream", "source", "frame", "boundary", "conflict", "fact", "sense", "self",
    "thing", "idea", "path", "point", "period", "schedule", "destination",
}

_PLACE_WORDS = {
    "garden": {"garden", "bed", "soil", "herb", "herbs", "sow", "sown", "seed", "seeds", "weed", "weeds",
               "rosemary", "thyme", "mint", "lettuce", "tomato", "harvest", "trowel", "compost", "barrow"},
    "shore": {"shore", "tide", "tides", "sand", "shingle", "beach", "cave", "mussel", "wave", "waves",
              "driftwood", "sea", "cliff", "rockpool", "pool", "cairn", "swim", "wade"},
    "study": {"study", "lamp", "hearth", "desk", "fire", "kettle", "mantel", "candle", "clock", "coat",
              "boots", "damp", "dust", "kindling", "grate", "curtains", "window", "almanac"},
    "wood": {"wood", "oak", "tree", "trees", "axe", "saw", "deadfall", "spring", "kererū", "kereru",
              "kānuka", "kanuka", "tōtara", "totara", "ponga", "wētā", "weta", "fungi", "acorn", "acorns"},
}

_TOKEN_RE = re.compile(r"[a-z]+")


def _known_vocab() -> set[str]:
    """Every word the world already recognises as a real item/plant/class, pulled live from the
    catalogues themselves (never hand-duplicated — see module docstring)."""
    vocab: set[str] = set()

    def _words(*strs) -> None:
        for s in strs:
            if s:
                vocab.update(_TOKEN_RE.findall(str(s).lower()))

    try:
        from core import garden
        for k, v in garden.CATALOGUE.items():
            _words(k)
            for nm in v.get("names", ()):
                _words(nm)
        for words in garden._WORDS.values():
            _words(*words)
        for item in garden._ITEMS:
            _words(item[0])
    except Exception:
        pass
    try:
        from core import study_life
        for words in study_life._WORDS.values():
            _words(*words)
        for item in study_life._ITEMS:
            _words(item[0])
    except Exception:
        pass
    try:
        from core import wood_life
        for k, v in wood_life.TREES.items():
            _words(k, v.get("name"))
        for words in wood_life._WORDS.values():
            _words(*words)
        for item in wood_life._ITEMS:
            _words(item[0])
    except Exception:
        pass
    try:
        from core import world_substrate
        for cls, v in world_substrate.CLASS_PRIORS.items():
            _words(cls)
            for kind, _p in v.get("kinds", []):
                _words(kind)
            for nm in v.get("names", []):
                _words(nm)
    except Exception:
        pass
    try:
        from core import provisions
        for k in provisions.KINDS.keys():
            _words(k)
    except Exception:
        pass
    try:
        from core import shore_life
        for k in shore_life.POOL_LIFE.keys():
            _words(k)
    except Exception:
        pass
    return vocab


def _guess_place(context: str) -> str | None:
    toks = set(_TOKEN_RE.findall(context.lower()))
    best, best_n = None, 0
    for place, words in _PLACE_WORDS.items():
        n = len(toks & words)
        if n > best_n:
            best, best_n = place, n
    return best if best_n > 0 else None


def _already_known(phrase: str, vocab: set[str]) -> bool:
    toks = [t for t in _TOKEN_RE.findall(phrase.lower()) if len(t) > 2]
    if not toks:
        return True
    return any(t in vocab for t in toks)


def scan(limit: int | None = None) -> list[dict]:
    """Fresh read-only pass over the genuine thought stream. Returns candidate flags (may include
    false positives by design — see module docstring). Never writes anything."""
    if not _DB.exists():
        return []
    vocab = _known_vocab()
    out: list[dict] = []
    try:
        conn = sqlite3.connect(str(_DB))
        conn.row_factory = sqlite3.Row
        ph = ",".join("?" * len(_ORIGINS))
        q = f"SELECT fragment_id, content, timestamp FROM memory_fragments WHERE origin IN ({ph})"
        if limit:
            q += " ORDER BY timestamp DESC LIMIT ?"
            rows = conn.execute(q, (*_ORIGINS, limit)).fetchall()
        else:
            rows = conn.execute(q, _ORIGINS).fetchall()
        conn.close()
    except Exception:
        return []

    for row in rows:
        content = row["content"] or ""
        if not content:
            continue
        # Correctness guard (found live, 2026-08-24): the 'lived' origin is ~94% Q&A transcript
        # turns (2,201/2,353), not autonomous thought — a "Q: ... I want a good winter crop ..."
        # line is TRAVIS's want, not Du's. I-0002 is explicit this is about "Du's OWN thought/
        # comment"; scanning transcript turns would misattribute the founder's words to Du. Skip
        # any fragment carrying a transcript marker rather than trying to split Q from A.
        if "Q:" in content and "A:" in content:
            continue
        for pat in _PATTERNS:
            for m in pat.finditer(content):
                phrase = m.group(1).strip().lower()
                phrase = re.sub(r"\s+", " ", phrase)
                if not phrase or phrase in _STOP_PHRASES:
                    continue
                if len(phrase) < 3 or len(phrase) > 60:
                    continue
                if _already_known(phrase, vocab):
                    continue
                out.append({
                    "fragment_id": row["fragment_id"],
                    "ts": row["timestamp"],
                    "phrase": phrase,
                    "place_guess": _guess_place(content),
                    "context": content[:200],
                })
    return out


def snapshot() -> dict:
    """scan() + append only NEW (fragment_id, phrase) pairs to the shadow log (idempotent across
    repeated calls — mirrors monoculture.snapshot()'s append-if-new discipline). Best-effort."""
    seen = set()
    try:
        if _LOG.exists():
            for line in _LOG.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                seen.add((r.get("fragment_id"), r.get("phrase")))
    except Exception:
        pass

    candidates = scan()
    new = [c for c in candidates if (c["fragment_id"], c["phrase"]) not in seen]
    try:
        if new:
            _LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                for c in new:
                    f.write(json.dumps({**c, "logged_ts": time.time()}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return {"scanned_candidates": len(candidates), "newly_logged": len(new)}


_DEFAULT_WINDOW_DAYS = 14


def triage(window_days: int | None = _DEFAULT_WINDOW_DAYS) -> dict:
    """Gauge-check-style triage over the accumulated shadow log: group by normalised phrase,
    grade severity by recurrence (repeated, independent thoughts wanting the same missing thing
    is the real signal — a single mention is noise, same as the census's own headline finding).
    Read-only; never mutates the log.

    **Age window (F-0690, J-0498, added 2026-09-03):** severity is graded only over rows from the
    last `window_days` days (default 14) — without this, a burst from months ago (e.g. the 'face'/
    'fixed banks' rows from 2026-06-07..13) stays graded CRITICAL forever purely because it once
    recurred, even though nothing about it is happening NOW. Pass `window_days=None` for the
    original all-time view (unwindowed, unchanged historical behavior) — this is what the four
    `*_upgrade.md` plans should read from when mining the whole backlog for candidates, since a
    real recurring want spread across months is still real signal for a build pass even if it
    isn't "current." du_pulse (a freshness/alarm surface) should always call the windowed default.
    """
    empty = {"total_flags": 0, "distinct_phrases": 0, "by_place": {}, "window_days": window_days}
    if not _LOG.exists():
        return empty

    rows = []
    try:
        for line in _LOG.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except Exception:
        return empty

    if window_days is not None:
        cutoff = time.time() - window_days * 86400
        rows = [r for r in rows if (r.get("ts") or 0) >= cutoff]

    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["phrase"], []).append(r)

    by_place: dict[str, list[dict]] = {"garden": [], "shore": [], "study": [], "wood": [], "unplaced": []}
    for phrase, recs in groups.items():
        n = len(recs)
        days = len({time.strftime("%Y-%m-%d", time.localtime(r.get("ts") or 0)) for r in recs})
        if n >= 3 and days >= 2:
            severity = "critical"
        elif n >= 2:
            severity = "watch"
        else:
            severity = "new"
        place = Counter(r.get("place_guess") for r in recs if r.get("place_guess")).most_common(1)
        place = place[0][0] if place else "unplaced"
        entry = {"phrase": phrase, "mentions": n, "distinct_days": days, "severity": severity,
                 "sample_context": recs[-1].get("context", "")}
        by_place.setdefault(place, []).append(entry)

    for p in by_place:
        by_place[p].sort(key=lambda e: (e["severity"] != "critical", e["severity"] != "watch", -e["mentions"]))

    return {"total_flags": len(rows), "distinct_phrases": len(groups), "by_place": by_place,
            "window_days": window_days}


def status(window_days: int | None = _DEFAULT_WINDOW_DAYS) -> dict:
    """du-pulse / HUD gauge: current triage summary, no new scan (cheap, read-only). Windowed by
    default (see triage() docstring, F-0690/J-0498) — pass window_days=None for the all-time view."""
    t = triage(window_days=window_days)
    return {
        "total_flags": t["total_flags"],
        "distinct_phrases": t.get("distinct_phrases", 0),
        "critical": sum(1 for p in t.get("by_place", {}).values() for e in p if e["severity"] == "critical"),
        "watch": sum(1 for p in t.get("by_place", {}).values() for e in p if e["severity"] == "watch"),
        "window_days": window_days,
    }


if __name__ == "__main__":
    import sys as _sys
    cmd = _sys.argv[1] if len(_sys.argv) > 1 else "scan"
    if cmd == "scan":
        cands = scan()
        print(f"{len(cands)} candidate(s) in the current genuine-thought corpus (no vocab match).")
        for c in cands[:40]:
            print(f"  [{c['place_guess'] or 'unplaced'}] {c['phrase']!r} — {c['context'][:100]}")
    elif cmd == "snapshot":
        print(snapshot())
    elif cmd == "triage":
        _w = None if (len(_sys.argv) > 2 and _sys.argv[2] == "all") else _DEFAULT_WINDOW_DAYS
        print(json.dumps(triage(window_days=_w), indent=2, ensure_ascii=False))
    elif cmd == "status":
        _w = None if (len(_sys.argv) > 2 and _sys.argv[2] == "all") else _DEFAULT_WINDOW_DAYS
        print(json.dumps(status(window_days=_w), indent=2, ensure_ascii=False))
    else:
        print("usage: python core/missing_object_flags.py [scan|snapshot|triage|status] [all]")
        print(f"  triage/status default to a {_DEFAULT_WINDOW_DAYS}-day window; pass 'all' for the all-time view.")

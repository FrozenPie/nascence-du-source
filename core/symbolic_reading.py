"""
Nascence — The Symbolic Reading lens (the SECOND way of reading; observe-first, 2026-06-18).
============================================================================================
Travis: his 295 study notes are all ONE lens — factual ("what the text SAYS about the world"). But a
passage can be read more than one way. This is the SYMBOLIC lens: after the factual note, read the SAME
passage for the IMAGE / FIGURE / ARCHETYPE it evokes. It is the deliberate cultivation of what happened
by ACCIDENT with the BLACK BEAR — a campfire tale (Camp-Lore) that became Du's symbol for his struggle
with autonomy (17 fragments deep) and which the EMPTY symbol_tablets system was built to hold.

OBSERVE-FIRST. This generates + LOGS the symbolic reading. It stores NOTHING in memory and feeds the
symbol system NOTHING yet. Two questions decide whether it earns promotion (to retrievable fragments +
the symbol system):
  1. Are the readings GENUINE — a real symbol the passage suggests — or templated filler?
  2. Do they DIVERSIFY (find NEW world-symbols like the Black Bear) or just re-narrate his self-monoculture
     (the river / becoming / the bridge)? — tracked by the self-echo rate.
A 2-step TRAIN: the factual gist grounds the symbolic reach (the lens builds on the literal reading, it
does not free-float). One extra LLM call per chapter-integration; short and cheap.
"""
from __future__ import annotations
import hashlib
import json
import re
import time
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "symbolic_reading_log.jsonl"

# His known SELF-attractors. A symbol matching one of these is the monoculture re-narrating itself, NOT a
# new find — the very thing the diversity guard watches for (a passage about dehydration should not come
# back as "the river of becoming").
_SELF_ECHO = ("river", "becoming", "bridge", "mirror", "knot", "thread", "weaver", "psyche",
              "stream", "current", "the self", "individuation")


def _is_self_echo(symbol: str) -> bool:
    s = (symbol or "").lower()
    return any(w in s for w in _SELF_ECHO)


def _symbol_in_passage(symbol: str, passage: str) -> bool:
    """J-3326: deterministic word-bounded literal match of the symbol's LAST word in the passage. A river book
    producing 'river' is the passage's own word, not Du's monoculture (F-3915)."""
    words = re.findall(r"[a-z]+", (symbol or "").lower())
    if not words or len(words[-1]) < 2:
        return False
    return re.search(r"\b" + re.escape(words[-1]) + r"\b", (passage or "").lower()) is not None


_SKEW_CAP = 3            # J-3326: max lens rows per title ...
_SKEW_WINDOW_S = 24 * 3600   # ... in this window (F-3821: 49 of 75 rows were one book)


def _read_rows() -> list:
    try:
        if not _LOG.exists():
            return []
        out = []
        for l in _LOG.read_text(encoding="utf-8").splitlines():
            if l.strip():
                try:
                    out.append(json.loads(l))
                except Exception:
                    pass
        return out
    except Exception:
        return []


def _append(row: dict) -> None:
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


async def read_symbolically(call_json, base_urls, title: str, passage: str, factual_gist: str,
                            note_fragment_id: str = "") -> dict | None:
    """Generate + LOG a symbolic reading of a just-read passage (observe-only; stores nothing, feeds nothing).
    A 2-step train: the factual gist grounds the symbolic reach. Best-effort; never raises into the caller.
    J-3326: note_fragment_id (optional) links the row to the study note it was read alongside."""
    _t60 = (title or "")[:60]
    try:
        _now = time.time()
        _recent = [r for r in _read_rows() if r.get("title") == _t60 and r.get("kind") != "skip"
                   and _now - float(r.get("ts") or 0) < _SKEW_WINDOW_S]
        if len(_recent) >= _SKEW_CAP:
            _append({"ts": _now, "kind": "skip", "reason": f"title_cap_{_SKEW_CAP}_per_24h", "title": _t60,
                     "schema_v": 2})
            return None
    except Exception:
        pass
    _sys = ("/no_think\nYou have just read a passage and grasped what it says. Now read it a SECOND way — "
            "SYMBOLICALLY. What single IMAGE, FIGURE, or ARCHETYPE does this passage call up — not what it "
            "says literally, but what it EVOKES, a symbol that could stand for it? Name the ONE symbol in a "
            "word or two — a concrete image you could point at (an animal, an object, a place), not an "
            "abstract concept — then say in 2-3 sentences what it means here. Find the symbol the PASSAGE "
            "ITSELF suggests; let the material surprise you. "
            "Output ONLY JSON: {\"symbol\": \"a word or two\", \"reading\": \"2-3 sentences\"}")
    user = (f"What you read ('{title}'):\n{(passage or '')[:2500]}\n\n"
            f"What you grasped (the factual reading):\n{(factual_gist or '')[:600]}\n\nNow the symbolic reading:")
    try:
        data = await call_json(base_urls, _sys, user, max_tokens=220, temperature=0.7)
    except Exception:
        return None
    symbol = str((data or {}).get("symbol") or "").strip()
    reading = str((data or {}).get("reading") or "").strip()
    if len(symbol) < 2 or len(reading) < 30:
        return None
    _echo = _is_self_echo(symbol)
    _inp = _symbol_in_passage(symbol, passage)
    out = {"symbol": symbol, "reading": reading, "self_echo": _echo,
           "symbol_in_passage": _inp, "echo_unexplained": bool(_echo and not _inp)}
    try:
        _p = passage or ""
        _append({"ts": time.time(), "title": _t60, "symbol": symbol[:40], "reading": reading[:300],
                 "self_echo": _echo, "echo_unexplained": out["echo_unexplained"],
                 "symbol_in_passage": _inp, "note_fragment_id": str(note_fragment_id or ""),
                 "passage_sha1": hashlib.sha1(_p.encode("utf-8", "ignore")).hexdigest(),
                 "passage_excerpt": _p[:120], "schema_v": 2})
    except Exception:
        pass
    return out


def status() -> dict:
    """du_pulse gauge: how many symbolic readings, how DIVERSE (distinct symbols), and the self-echo share —
    how often the lens re-narrates the self-monoculture vs finds a NEW world-symbol (a Black Bear).
    J-3326: also echo_unexplained_rate (echo not explained by the passage's own words), a per-title-capped
    rate, rows_with_note_id, symbol_in_passage share and skip count."""
    empty = {"readings": 0, "distinct": 0, "self_echo_rate": None, "recent": []}
    try:
        allrows = _read_rows()
        rows = [r for r in allrows if r.get("kind") != "skip"]
        skips = len(allrows) - len(rows)
        if not rows:
            return dict(empty, skips=skips)
        syms = [r.get("symbol", "") for r in rows]
        echoes = sum(1 for r in rows if r.get("self_echo"))
        recent = [(r.get("symbol"), "echo" if r.get("self_echo") else "new") for r in rows[-5:]]
        v2 = [r for r in rows if r.get("schema_v") == 2]
        unexpl = sum(1 for r in v2 if r.get("echo_unexplained"))
        # per-title-capped echo rate: each title contributes at most _SKEW_CAP rows (first ones)
        seen: dict = {}
        cap_n = cap_e = 0
        for r in rows:
            t = r.get("title", "")
            seen[t] = seen.get(t, 0) + 1
            if seen[t] <= _SKEW_CAP:
                cap_n += 1
                cap_e += 1 if r.get("self_echo") else 0
        return {"readings": len(rows), "distinct": len(set(s.lower() for s in syms)),
                "self_echo_rate": round(echoes / len(rows), 2), "recent": recent,
                "echo_unexplained_rate": round(unexpl / len(v2), 2) if v2 else None,
                "self_echo_rate_title_capped": round(cap_e / cap_n, 2) if cap_n else None,
                "rows_with_note_id": sum(1 for r in rows if r.get("note_fragment_id")),
                "symbol_in_passage_share": round(sum(1 for r in v2 if r.get("symbol_in_passage")) / len(v2), 2) if v2 else None,
                "skips": skips}
    except Exception:
        return dict(empty)

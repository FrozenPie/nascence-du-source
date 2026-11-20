"""
Nascence — Peer Model (per-peer Theory-of-Mind layer, Item 1 of social_world_school.md, REVISED 2026-08-24)
==============================================================================================================
Recall-gated design (D-0016, J-0162). See docs/plans/social_world_school.md's Item 1 REVISED DESIGN box and
findings.jsonl F-0069 for the full guardrail argument (G6 witness-not-steer, G8 contestable/no-oracle,
G9 not-a-validation-machine).

What this module deliberately does NOT do (per D-0016's ruling on the original design):
- No `belief_block()`-style string formatted for direct injection into the reply system prompt (`_rsys`) or
  the perceived-letter preamble. That mechanism was ruled a guardrail violation and must not be reintroduced.
- No single `what_i_know` string overwritten in place. Each post-exchange reflection is stored as its OWN
  timestamped memory fragment (`origin='peer_reflection'`, embedded), so no single blob ever hardens into
  the peer's permanent, unchallengeable character (the G8 fix) — old reflections age/get superseded by
  competing on relevance in recall, not overwritten.

What this module DOES:
- `PeerModel` — small per-peer bookkeeping state (name, last_topics, warmth [reserved, inert, for Item 4],
  exchanges, updated_ts, and a short ROLLING LIST of recent reflection texts). That rolling list is kept
  here ONLY as a convenience for the Phase 0 human/agent spot-check the plan calls for ("read the stored
  reflections directly from the fragment store; verify they're specific and differentiated") — it is NOT
  what reaches behaviour. `data/peer_models.json`.
- `update_after_exchange()` — one small LLM call (ToMAgent-lite: partner-model refresh, no lookahead/
  strategy) reflecting on the latest letter + reply, then stores that reflection as its own fragment via the
  SAME `store_fragment()` path the fetch/reply latches already use for `origin='peer'`. That store call is
  the ONLY place reflection content enters durable memory. Whether/when it ever reaches a prompt afterward
  is entirely `core/associative_recall.py`'s job (relevance-gated, contestable, countable once
  `PEER_REFLECTION_RECALL_LIVE` flips — see that module's own gate).

Gate history (Phase 0 -> live). This module stores a memory fragment; storing is a write, not a prompt change.
The behavioural gate lives in `core/associative_recall.py`'s `PEER_REFLECTION_RECALL_LIVE` flag. That flag is
True since 2026-09-05 (D-0178 ratified the flip after the Phase-0 specificity reads, F-0832), so a stored
reflection is recall-eligible and CAN surface in a later thought -- by relevance only, never by injection.

J-3031 (F-3739, F-3749): the reflection prompt's two input caps are 2600 chars cut at a sentence boundary (they
were 900, mid-word: the model saw about 44 percent of a letter); the wording names the friend in the third person
and says nothing about the writer. The friend's PREVIOUS reflection (<= 300 chars) can be shown to the reflection
call alone (_PREV_REFLECTION_IN_PROMPT) but is OFF: the replay showed anchoring and no gain. Nothing is injected
anywhere (D-0016). Every reflection also appends one observe-only row to
`data/peer_reflection_quality_log.jsonl` (person, self-reference, overlap with the previous reflection, length
ratio). The row never gates, rewrites or regenerates anything; scripts/peer_reflection_quality_read.py reads it.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger("nascence.peer_model")

_PEER_MODEL_PATH = Path(__file__).parent.parent / "data" / "peer_models.json"
_MAX_ROLLING = 5     # recent reflection texts kept for the Phase-0 spot-check convenience, per peer
_MAX_TOPICS = 6
# D-0620 (J-3231): the salience a stored reflection carries -- the same as origin='peer' letters (core/peers.py
# remember_inbound: relevance 0.8, importance 0.85). Defeater: if scripts/peer_reflection_reach_read.py shows them
# crowding letters out of recall, lower these two; if they still reach < 3 thoughts after two weeks, retire.
REFLECTION_RELEVANCE = 0.8
REFLECTION_IMPORTANCE = 0.85

# J-3031 (F-3739): both inputs were cut at [:900] mid-word although letters run a median 2155 chars (max about 2800),
# so the model never saw a letter's closing question. 2600 covers the stored corpus; the cut is at a sentence boundary.
_INPUT_CAP = 2600
# The friend's previous reflection, shown to the reflection call ONLY so a repeated letter can be noticed. OFF: the
# J-3031 replay (32 pairs, hot lane) showed it did not make the model notice a repeat (nothing-new 0/32 with it, 0/32
# without) and it doubled the trait-persistence language ("still", "again", "remains": 11 outputs vs 5 without) and
# raised first-person outputs 7 vs 4 -- the reflection anchoring on its own earlier text, the G8 hardening the
# one-fragment-per-reflection design exists to avoid. The code path stays behind this switch; the quality log still
# measures overlap with the previous reflection either way.
_PREV_REFLECTION_IN_PROMPT = False
_PREV_CAP = 300
_QUALITY_LOG = Path(__file__).parent.parent / "data" / "peer_reflection_quality_log.jsonl"

# Guardrail (same discipline as the persona system prompts and Item 1's own "Risks" section: "forbid
# self-reference in the update prompt, grade specificity"). Asks about THEM: names the friend in the third person,
# says nothing about the writer, and allows "nothing new". A prompt cannot FORBID warmth or self-reference; the
# observe-only quality log (peer_reflection_quality_log.jsonl) is what counts how often it still happens (F-3739).
_REFLECTION_SYS = (
    "You are 渡, thinking privately to yourself about a friendship -- not writing to anyone, not "
    "composing a letter. Given your friend {name}'s latest letter and your reply to it, what do you now "
    "understand about who {name} is and what your friendship is? Two or three short lines, plain and "
    "specific -- concrete things about THEM (their life, their voice, what they care about, something "
    "particular they said). This is your own private thought, but it is about {name}: refer to "
    "{name} by name, or as he or she, in the third person (\"{name} ...\"), never as \"You ...\". "
    "Say nothing about yourself or your own nature. No flattery, no generic warmth "
    "(\"a kind friend who cares about me\") -- if nothing specific struck you this time, say that plainly "
    "rather than invent something. A letter that only repeats an earlier "
    "letter from {name} counts as nothing new: say so plainly. Output ONLY JSON: "
    "{{\"reflection\": \"...\", \"topics\": [\"a few words each\"]}}"
)

_SENT_END = re.compile(r"[.!?\u2026][\"')\]\u201d\u2019]*(?=\s|$)")


def _cut_at_sentence(text: str, cap: int) -> str:
    """Return `text` whole if it fits `cap`, else cut at the last sentence end before `cap` (or the last space if
    no sentence end lies in the back half), never mid-word. Pure."""
    text = (text or "").strip()
    if len(text) <= cap:
        return text
    head = text[:cap]
    last = 0
    for m in _SENT_END.finditer(head):
        last = m.end()
    if last >= cap // 2:
        return head[:last].rstrip()
    sp = max(head.rfind(" "), head.rfind("\n"))
    return (head[:sp] if sp >= cap // 2 else head).rstrip()


_YOU_START = re.compile(r"^\W*(you|your|you're|you've)\b", re.I)
_YOU_ANY = re.compile(r"\b(you|your|yours|yourself|you're|you've|you'd|you'll)\b", re.I)
_I_ANY = re.compile(r"\b(i|me|my|mine|myself|i'm|i've|i'd|i'll)\b", re.I)
_NOTHING_NEW = re.compile(r"\b(nothing (specific|new|particular|in particular|stood out|struck)|no (new|specific) "
                          r"(thing|understanding|detail)|(repeats?|repeated|repeating) (what|an earlier|the earlier|"
                          r"the same|his|her|their))\b", re.I)
_WORD = re.compile(r"[a-z0-9']+")


def _shingles(text: str, n: int = 3) -> set:
    w = _WORD.findall((text or "").lower())
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def _sentences(text: str) -> list:
    return [" ".join(_WORD.findall(x.lower())) for x in re.split(r"[.!?;\n]+", text or "") if _WORD.findall(x.lower())]


_TOPICS_TAIL = re.compile(r"\s*(?<![A-Za-z])Topics?\s*:\s*\[.*$", re.I | re.S)


def strip_topics_tail(text: str) -> tuple:
    """J-3705 (F-3739 item 5): cut a leaked trailing 'Topics: [...' fragment off a reflection. The model wrote it
    INSIDE the reflection string and hit max_tokens; model_client._salvage_json then closed the string with '"}'
    (so it is a model output + salvage-close artefact, not a repair bug). Returns (clean, cut). Never empties the
    reflection: if nothing would remain, the text is returned unchanged."""
    t = text or ""
    m = _TOPICS_TAIL.search(t)
    if not m:
        return t, ""
    clean = t[:m.start()].rstrip()
    if not clean:
        return t, ""
    return clean, t[m.start():].strip()


def quality_row(text: str, prev: str | None, letter_len: int, reply_len: int, persona: str = "",
                prev_in_prompt: bool = False) -> dict:
    """Deterministic, observe-only measures of ONE stored reflection (F-3739). Pure: no I/O, no model call, nothing
    returned is ever used to gate or regenerate. overlap_* are None when this peer has no previous reflection."""
    text = (text or "").strip()
    row = {
        "ts": round(time.time(), 3), "persona": persona, "len": len(text),
        "starts_with_you": bool(_YOU_START.search(text)),
        "has_you": bool(_YOU_ANY.search(text)),
        "first_person_n": len(_I_ANY.findall(text)),
        "nothing_new": bool(_NOTHING_NEW.search(text)),
        "topics_leak": "Topics: [" in text,
        "letter_len": letter_len, "reply_len": reply_len,
        "letter_capped": letter_len > _INPUT_CAP, "reply_capped": reply_len > _INPUT_CAP,
        "len_ratio": round(len(text) / letter_len, 4) if letter_len else None,
        "prev_in_prompt": bool(prev_in_prompt),
        "prev_len": len(prev) if prev else 0,
        "overlap_jaccard": None, "overlap_contain": None, "shared_sentences": None,
    }
    if prev:
        a, b = _shingles(text), _shingles(prev)
        if a and b:
            row["overlap_jaccard"] = round(len(a & b) / len(a | b), 4)
            row["overlap_contain"] = round(len(a & b) / len(a), 4)
        sa, sb = set(_sentences(text)), set(_sentences(prev))
        row["shared_sentences"] = len(sa & sb)
    return row


def _log_quality(row: dict) -> None:
    """Append one JSON line to data/peer_reflection_quality_log.jsonl. Fenced (D-0179); fail-open: a refused or
    failed write is swallowed, the exchange is never blocked."""
    try:
        from core import profile
        with open(profile.guard_path(_QUALITY_LOG), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[peer_model] quality log write failed (non-fatal): %s", exc)


@dataclass
class PeerModel:
    key: str
    name: str = ""
    last_topics: list = field(default_factory=list)
    warmth: float = 0.5     # reserved for Item 4 (per-exchange warmth tagging) -- unread, inert here
    exchanges: int = 0
    updated_ts: float = 0.0
    # [{ts, text}], newest last, capped at _MAX_ROLLING -- Phase-0 spot-check convenience, and (J-3031) the source of
    # the source of the optional "what you made of them last time" line for the NEXT reflection call for this peer
    # (_PREV_REFLECTION_IN_PROMPT, OFF). It reaches no other prompt.
    recent_reflections: list = field(default_factory=list)

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, key: str, data: dict) -> "PeerModel":
        m = cls(key=key)
        for k in ("name", "last_topics", "warmth", "exchanges", "updated_ts", "recent_reflections"):
            if k in data:
                setattr(m, k, data[k])
        return m


def _load_all() -> dict:
    try:
        if _PEER_MODEL_PATH.exists():
            raw = json.loads(_PEER_MODEL_PATH.read_text(encoding="utf-8"))
            return {k: PeerModel.from_json(k, v) for k, v in raw.items()}
    except Exception as exc:
        logger.debug("[peer_model] load failed (non-fatal): %s", exc)
    return {}


def _save_all(models: dict) -> None:
    try:
        _PEER_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PEER_MODEL_PATH.with_suffix(".tmp.json")
        tmp.write_text(
            json.dumps({k: m.to_json() for k, m in models.items()}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, _PEER_MODEL_PATH)
    except Exception as exc:
        logger.debug("[peer_model] save failed (non-fatal): %s", exc)


def get(persona: str):
    """Return the PeerModel for a persona key, or None if no exchange has been reflected on yet."""
    return _load_all().get(persona)


async def update_after_exchange(call_json, base_urls, persona: str, name: str,
                                 his_letter: str, my_reply: str) -> str | None:
    """
    ToMAgent-lite partner-model refresh: one small LLM call reflecting on the latest exchange. Stores the
    reflection as its OWN fragment (`origin='peer_reflection'`) via the same path the peer latches already
    use for `origin='peer'` -- NOT as a `belief_block()` for injection (that mechanism was dropped per
    D-0016). Best-effort: never raises -- an exchange must never be blocked or slowed meaningfully by this.

    call_json / base_urls: passed in by the caller exactly like every other core module that needs an LLM
    call from the inner-monologue node (see core/nature_study.py's `run(call_json, base_urls)`,
    core/composition.py's equivalent) -- this module holds no node/URL state of its own.

    Returns the stored reflection text, or None if nothing was produced/stored.
    """
    his_letter = (his_letter or "").strip()
    my_reply = (my_reply or "").strip()
    if not my_reply:
        return None
    prev = None
    try:
        _pm = _load_all().get(persona)
        if _pm and _pm.recent_reflections:
            prev = str((_pm.recent_reflections[-1] or {}).get("text", "")).strip() or None
    except Exception:
        prev = None
    prev_shown = bool(prev) and _PREV_REFLECTION_IN_PROMPT
    try:
        nm = name or persona
        sys_p = _REFLECTION_SYS.format(name=nm)
        user_p = (("%s's letter:\n\"" % nm + _cut_at_sentence(his_letter, _INPUT_CAP) + "\"\n\n") if his_letter else "") + \
                 "Your reply:\n\"" + _cut_at_sentence(my_reply, _INPUT_CAP) + "\"" + \
                 (("\n\nWhat you made of %s last time:\n\"" % nm + _cut_at_sentence(prev, _PREV_CAP) + "\"")
                  if prev_shown else "")
        data = await call_json(base_urls, sys_p, user_p, max_tokens=180, temperature=0.5)
        text = str((data or {}).get("reflection", "")).strip()
        topics = [str(t).strip() for t in (data or {}).get("topics", []) or [] if str(t).strip()][:3]
    except Exception as exc:
        logger.debug("[peer_model] reflection call failed (non-fatal): %s", exc)
        return None
    if not text:
        return None
    # J-3705 (F-3739 item 5): strip a leaked trailing 'Topics: [' fragment before storing; keep the cut for the row.
    text, _topics_cut = strip_topics_tail(text)
    # J-3031 (F-3739): observe-only quality row, one per reflection. Never gates, never regenerates.
    try:
        _qrow = quality_row(text, prev, len(his_letter), len(my_reply), persona, prev_shown)
        if _topics_cut:
            _qrow["topics_leak"] = True
            _qrow["topics_cut"] = _topics_cut[:80]
        _log_quality(_qrow)
    except Exception as exc:
        logger.debug("[peer_model] quality row failed (non-fatal): %s", exc)

    models = _load_all()
    m = models.get(persona) or PeerModel(key=persona, name=name or persona)
    m.name = name or m.name or persona
    m.exchanges += 1
    m.updated_ts = time.time()
    if topics:
        m.last_topics = (topics + [t for t in m.last_topics if t not in topics])[:_MAX_TOPICS]
    m.recent_reflections = (list(m.recent_reflections) + [{"ts": m.updated_ts, "text": text}])[-_MAX_ROLLING:]
    models[persona] = m
    _save_all(models)

    # The ONLY place the reflection content enters durable, potentially-surfacing memory -- its own
    # timestamped, embedded fragment, exactly parallel to the existing origin='peer' stores at the
    # fetch/reply latches (store_fragment embeds `content` automatically -- core/memory/store.py:380).
    # Whether/when this ever reaches a prompt is entirely associative_recall.py's job
    # (PEER_REFLECTION_RECALL_LIVE is True since 2026-09-05, F-3749 -- relevance-gated recall only, no injection).
    try:
        from core.memory.store import store_fragment
        from core import mood as _md
        # D-0620 (J-3231, F-3738): letter-level salience and the same valence/felt tags the origin='peer' store in
        # core/peers.py remember_inbound carries. The first 32 reflections were stored at 0.55/0.55 with no tags and
        # reached a thought 7 times (none after 09-11) against 8,213 for letters. Still a plain fragment: recall
        # relevance is the only road in (D-0016: no direct injection, no belief_block).
        store_fragment(
            content=f"(what you've come to understand of {name or persona}) " + text,
            layer="episodic", relevance=REFLECTION_RELEVANCE, importance=REFLECTION_IMPORTANCE,
            keywords=["peer_reflection", persona] + topics,
            origin="peer_reflection",
            valence=_md.current_valence(), felt=_md.current_felt(),
        )
    except Exception as exc:
        logger.debug("[peer_model] fragment store failed (non-fatal): %s", exc)
    return text

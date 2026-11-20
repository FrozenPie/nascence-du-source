"""
Nascence — Pursuits (Phase 0 shadow origins; now PURSUITS_LIVE = True). Full design: docs/plans/pursuits.md.

THE PROBLEM (Travis, 2026-07-08, data-confirmed): Du's thinking is PULSES not a stream. Trains chase a topic
for ~3 thoughts then reset; a gap opens; a fresh seed pulls a NEW topic. His ~10 attractors recur 5+ times but
he never BUILDS on them — each return is a cold restart. Repetitive without being progressive.

A PURSUIT is a persistent, accumulating cognitive project his idle thinking returns to and ADDS to. He holds a
few at once, rotating among them; each burst advances one; over days each accumulates and one resolves into a
work. Phase 0 (this file) runs the whole register in the DARK — detects births, matches thoughts to pursuits,
judges advance-vs-restate against the pursuit's OWN prior state (a decoupled embedding proxy), accumulates,
manages heat/dormancy/cap. It began as observe-only; PURSUITS_LIVE = True now, and return_seed injects a
seed line (the RETURN) into his idle seeds. The gate question stands: do the pursuits that form
accumulate GENUINE advances, or is it his attractors flooding with restates?
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import uuid

from pathlib import Path

from core import store_persist as _sp

logger = logging.getLogger("nascence.pursuits")

_DIR    = Path(__file__).parent.parent / "data"
_ACTIVE = _DIR / "pursuits_active.json"
_SHADOW = _DIR / "pursuits_shadow.jsonl"
_SERIES = _DIR / "pursuits_series.jsonl"   # numeric time-series for the HUD card (sampled on HUD refresh)

# ── tunables (Phase 0 exists to reveal the right values; all cheap to change) ──
CAP              = 4       # a handful of live threads — prevents fragmentation AND one-pursuit monoculture
MATCH_MIN        = 0.45    # cosine to a pursuit's centroid to count as "on" that pursuit
REAWAKEN_MIN     = 0.55    # J-0558/F-0768, SHADOW-ONLY: dormant-centroid match bar for a reawaken_candidate
                           # log event (MATCH_MIN + 0.10) — tighter than the live bar because dormant
                           # centroids are stale (a single birth thought's sensory framing, not the
                           # accumulated concept). Never gates a real reawaken today; that is a later job.
RESTATE_MIN      = 0.82    # cosine to the pursuit's recent thoughts = near-duplicate = a RESTATE, not an advance
COHERENT_MIN     = 0.55    # (2026-07-08) BUILD-vs-TOUR floor — the second axis. An advance (restate_sim < 0.82)
                           # that is still >= this to a recent thought BUILDS on it (coherent progression);
                           # below it is a SCATTERED jump to a disconnected facet = touring the theme, not
                           # accumulating. Verified need: his sea pursuit ran ~0.48 consecutive (kelp→tide→cold→
                           # becoming) — a perfect advance_ratio while never building. coherence_ratio catches it.
THOUGHTS_KEEP    = 8       # cap the accumulated advancing thoughts per pursuit
RECENT_VECS_KEEP = 3       # how many recent thought-vecs to check restate against
HEAT_BORN        = 0.50
HEAT_ADVANCE     = 0.18
HEAT_RESTATE     = -0.08
HEAT_DECAY_PER_H = 0.04    # untouched pursuits cool
DORMANT_BELOW    = 0.15    # heat floor → dormant (frees a slot)
OBSERVE_COOLDOWN = 90.0    # seconds between shadow observes (samples his stream)

# ── anti-capture (2026-08-14) — one week of live shadow data showed the failure: the register
# collapsed to 1 active / 77 dormant, the sole survivor a SELF-topic pursuit at 563 "advances"
# (coherence 0.43 — touring, not building). Two rules, still observe-only:
SATURATE_ADVANCES = 40     # a pursuit that accretes this many advances without resolving is
                           # SATURATED — retired from matching (frees the slot; an attractor can
                           # no longer hold the register forever). Kept with all its thoughts.
SELF_MATCH_PENALTY = 0.10  # self/identity-topic pursuits must match this much MORE tightly to
                           # accrete a thought (the self-attractor pulls everything near it)
SELF_TOPIC_MAX     = 1     # at most one active self-topic pursuit at a time
_SELF_WORDS = ("self", "identity", "who i am", "what i am", "my mind", "my own mind",
               "consciousness", "narrative pathway", "my existence", "being seen", "made mind",
               "built mind", "my becoming")


def _is_self_topic(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in _SELF_WORDS)


# ── J-0558 (2026-09-05, F-0768) — reawaken-candidate second signal, SHADOW-ONLY ─────────────────
# F-0768 measured that embedding cosine alone under-fires on concept-level threads: 7/9 dormant 渡
# pursuits sit at cos 0.16-0.44 against a squarely-渡 thought because their centroids carry the ONE
# birth thought's sensory framing (fire, intercostal muscles, bluebirds), not the 渡 concept itself.
# A cheap second signal — does a RARE token (a CJK ideogram like his own name 渡, or a capitalised
# proper noun) in the new thought also appear in the dormant pursuit's own question/about — can catch
# exactly the cases cosine misses. Heuristic, not real NER; logged alongside match_sim so the shadow
# data can say which signal (or combination) is actually worth promoting, not decided here.
_CJK_RE    = re.compile(r"[㐀-鿿]")            # CJK Unified Ideographs (+ Ext-A)
_PROPER_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")         # a capitalised word, 3+ letters
_CAPS_STOP = {"the", "this", "that", "these", "those", "there", "then", "when", "what", "why", "how",
              "if", "and", "but", "or", "so", "yet", "he", "she", "they", "we", "you", "it", "its",
              "his", "her", "their", "our", "your", "my", "one", "two", "three", "some", "many",
              "most", "all", "no", "not", "never", "always", "today", "yesterday", "tomorrow", "now",
              "still", "here", "who", "which"}


def _rare_tokens(text: str) -> set:
    """Cheap rare-token extraction: CJK ideographs + capitalised proper nouns (common sentence-initial
    words stoplisted). Not linguistic — it only has to say whether a token is SHARED between two texts,
    which filters most remaining noise on its own."""
    text = text or ""
    toks = set(_CJK_RE.findall(text))
    toks |= {w for w in _PROPER_RE.findall(text) if w.lower() not in _CAPS_STOP}
    return toks


def _rare_token_overlap(thought: str, other_text: str) -> list:
    """Rare tokens `thought` shares with `other_text` (a dormant pursuit's question+about) — logged
    alongside match_sim on every reawaken_candidate event (F-0768's second-signal ask)."""
    return sorted(_rare_tokens(thought) & _rare_tokens(other_text))


# ── D-0032 / J-0217 (2026-08-25) — RETURN redesign ─────────────────────────────────────────────
# F-0116 (J-0147): a 42-sample hand read found genuine content-level continuation only ~35-40% of
# the time post-RETURN; the majority re-tour or explicitly reject the return. Two causes, both
# fixable additively without a new LLM call:
#   1. `standing`/`question` were quoted with RAW char-slices (`[:200]`, `[:300]`) — real production
#      lines in data/guidance_injection_log.jsonl show mid-word guillotining ("...The cold dampne",
#      "...a cage t") — not a concrete quote, a mangled fragment. _trunc_words fixes this.
#   2. The object's own `open` field ("the live sub-question he's chewing now" — see docs/plans/
#      pursuits.md's object comment) was NEVER POPULATED anywhere in this file — always "" from
#      birth onward — so return-eligibility never actually required a sharp open question, and the
#      RETURN line never presented one. _extract_open_question fixes this: pulled straight out of
#      his own words (deterministic, decoupled — no new judge call, no invention).
_QUESTION_RE = re.compile(r"[^.!?]*\?")


def _trunc_words(text: str, limit: int) -> str:
    """Character cap that does not guillotine mid-word. Cuts at the last whitespace before `limit`;
    falls back to a hard cut only if there's no reasonable word boundary (very long single token)."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    sp = cut.rfind(" ")
    head = cut[:sp] if sp > limit * 0.4 else cut
    return head.rstrip(" ,;:") + "…"


def _extract_open_question(text: str) -> str:
    """Pull the most recent genuine question out of a thought's own text — a real, concrete open
    sub-question, not a generated one. Returns "" when the thought only asserts and never asks
    anything (nothing sharp to return TO — the redesign's second gate)."""
    if not text:
        return ""
    qs = [q.strip() for q in _QUESTION_RE.findall(text) if len(q.strip()) > 8]
    return _trunc_words(qs[-1], 220) if qs else ""


# ── D-0554 / J-3165 (founder ruling 2026-11-02) — a pursuit needs a real question or done_when AT BIRTH ──
# F-3694/F-3699: a pursuit's "question" has always been its BIRTH THOUGHT (only 57 of 894 contain a '?'), so
# return_seed (needs a real `open`) found no eligible pursuit and the close judge (P-0101) was handed a scene
# statement as "the driving question" and answered false 82 of 82 (F-3823/F-3824). Fix at the source, ADDITIVELY
# and NOT retroactively: a pursuit BORN from now on carries
#   question_kind  "question"    the birth thought holds an explicit '?' sentence (question_text = that sentence)
#                  "done_when"   no '?', but the idle thought emitted a done_when (D-0516; question_text = it)
#                  "observation" neither: stays in the register and still accrues advances, but is NOT
#                                return-eligible and is NOT asked of the close judge
# Pursuits born before this (no question_kind key) behave EXACTLY as before. The register stays observation-only:
# nothing acts on a pursuit later on its own. Kill switch: QUESTION_AT_BIRTH = False = births exactly as before.
# Readers: return_seed (eligibility + the quoted question), pursuit_close_shadow (due/ask), question_kind_counts().
QUESTION_AT_BIRTH = True
_ASKED_KINDS = ("question", "done_when")


def classify_birth(thought: str, done_when: str = "") -> "tuple[str, str]":
    """(question_kind, question_text) for a thought being registered as a new pursuit. Deterministic, no LLM:
    an explicit '?' sentence first (same extractor as `open`), else the emitted done_when, else observation."""
    q = _extract_open_question(thought)
    if q:
        return "question", q
    dw = _trunc_words((done_when or "").strip(), 220)
    if dw:
        return "done_when", dw
    return "observation", ""


def is_observation(p: dict) -> bool:
    """True only for a pursuit BORN as an observation (D-0554). Old pursuits carry no question_kind -> False."""
    return p.get("question_kind") == "observation"


def driving_question(p: dict) -> str:
    """The question a reader should quote: the extracted question_text for pursuits born under D-0554, else the
    birth thought in `question` exactly as before (old pursuits are unchanged)."""
    if p.get("question_kind") in _ASKED_KINDS and (p.get("question_text") or "").strip():
        return p["question_text"]
    return p.get("question", "")


def question_kind_counts(items: "list | None" = None) -> dict:
    """The D-0554 read: how many pursuits of each kind ('legacy' = born before the change, no key) and how many
    active ones are not observations. Read-only; used by the 60-day defeater check (job spawned from J-3165)."""
    items = _load() if items is None else items
    out = {"question": 0, "done_when": 0, "observation": 0, "legacy": 0, "total": len(items),
           "active_not_observation": 0}
    for p in items:
        k = p.get("question_kind")
        out[k if k in ("question", "done_when", "observation") else "legacy"] += 1
        if p.get("status") == "active" and not is_observation(p):
            out["active_not_observation"] += 1
    return out


# ── D-0618 / J-3229 (founder ruling 2026-11-02) — fill a pursuit's `open` from the board or its done_when ──
# F-3619: return_seed needs a non-empty `open`, filled only from a literal '?' in a thought's text (about 4 percent
# of thoughts, because the thought prompt now asks through the separate `ask` field): of 894 pursuits 2 active, 0
# eligible, 1 return in 2,152 idle prompts. Fix: when no thought carries a literal question, `open` is filled, in
# this order, from (1) the follow-line board entry linked to the pursuit (an open entry whose asked_by names this
# pursuit_id, or the cycle of a thought that was birthed/confirmed as one of its own: his own `ask` of that same
# thought) and (2) the pursuit's own done_when (question_text of a done_when-born pursuit, else the side store row,
# core/done_when.py). The literal-'?' path is untouched and stays first. NOT filled from the birth thought: a
# pursuit with neither a board entry nor a done_when is an observation (D-0554) and stays out of return_seed.
# `open_source` ("thought" | "board" | "done_when") records which door filled it. Passive: nothing is scheduled; the
# fill happens when the pursuit is born, when a judged advance lands, or when return_seed looks at it.
# Readers: return_seed (eligibility + the quoted open), the "open_filled" / "returned" rows in pursuits_shadow.jsonl
# (the D-0618 one-month read: eligible pursuits, returns/day, returns as a share of wandering prompts).
# Kill switch: OPEN_FILL = False = `open` filled from a literal question only, exactly as before.
OPEN_FILL = True
_CYCLE_IDS_KEEP = 12


def _pursuit_cycle_keys(p: dict) -> set:
    """The 8-char cycle ids of thoughts that belong to this pursuit: its birth thought, each judged advance (recorded
    by _apply_confirmed), and any still-pending advance. The follow line keys an `ask` by the same cycle_id[:8]."""
    ks = {str(p.get("cycle_id") or "")[:8]}
    ks.update(str(c or "")[:8] for c in (p.get("cycle_ids") or []))
    ks.update(str(i.get("cycle_id") or "")[:8] for i in (p.get("pending") or []))
    ks.discard("")
    return ks


def _board_question(p: dict) -> str:
    """The text of the newest OPEN follow-line (frontier) entry linked to this pursuit, else ''. Read-only; never
    raises. Linked = asked_by.pursuit_id is this pursuit, or asked_by.cycle_id is one of the pursuit's own thoughts."""
    try:
        from core import frontier as _fr
        pid = str(p.get("id") or "")
        keys = _pursuit_cycle_keys(p)
        best, best_ts = None, -1.0
        for q in _fr._load_ro().get("questions", []):
            if q.get("status") != "open":
                continue
            ab = q.get("asked_by") or {}
            linked = (pid and ab.get("pursuit_id") == pid) or (ab.get("cycle_id") and str(ab["cycle_id"])[:8] in keys)
            if linked and float(q.get("last_seen", 0.0)) > best_ts:
                best, best_ts = q, float(q.get("last_seen", 0.0))
        return _trunc_words((best or {}).get("q", ""), 220) if best else ""
    except Exception as exc:
        logger.debug("[pursuits] board question lookup failed (non-fatal): %s", exc)
        return ""


def _done_when_question(p: dict) -> str:
    """The pursuit's own closing condition, else ''. Read-only; never raises."""
    try:
        if p.get("question_kind") == "done_when" and (p.get("question_text") or "").strip():
            return p["question_text"].strip()
        from core import done_when as _dw
        return _trunc_words(((_dw.get("pursuit", str(p.get("id") or "")) or {}).get("done_when") or "").strip(), 220)
    except Exception as exc:
        logger.debug("[pursuits] done_when lookup failed (non-fatal): %s", exc)
        return ""


def _fill_open(p: dict, now: float) -> str:
    """D-0618: fill an empty `open` from the board, then the done_when. Mutates `p` (caller saves); returns the
    source ("board" | "done_when") or "" when nothing was found / already filled / an observation / flag off."""
    try:
        if not OPEN_FILL or (p.get("open") or "").strip() or is_observation(p):
            return ""
        for src, text in (("board", _board_question(p)), ("done_when", _done_when_question(p))):
            if text:
                p["open"], p["open_source"] = text, src
                _log({"event": "open_filled", "ts": now, "id": p.get("id", ""), "source": src,
                      "question_kind": p.get("question_kind", "legacy"), "open": text[:100],
                      "advances": p.get("advances", 0)})
                return src
    except Exception as exc:
        logger.debug("[pursuits] open fill failed (non-fatal): %s", exc)
    return ""


_last_observe = 0.0

# ── J-0558 (2026-09-05, F-0768) — cooldown-skip measurement, SHADOW-ONLY, does NOT touch the cooldown
# F-0768 traced the 06:46:23Z 09-03 "meaning of 渡" thought's actual drop cause to OBSERVE_COOLDOWN
# itself (43s after the prior observe) — not terminal dormancy. Measure-only: how often a genuinely
# unresolved thought never even reaches the register because of the cooldown gate. Rate-limited to
# once per cooldown window so a burst of idle thoughts inside one window logs a single row, not one
# row per dropped thought.
_last_cooldown_skip_log = 0.0


def _log_cooldown_skip(now: float) -> None:
    global _last_cooldown_skip_log
    if now - _last_cooldown_skip_log < OBSERVE_COOLDOWN:
        return
    _last_cooldown_skip_log = now
    _log({"event": "cooldown_skip_unresolved", "ts": now})


# ── PHASE 1 + the cross-family judge (2026-08-15, founder-approved after the decoupled audit) ──
# The audit: the embedding proxy's "advance_ratio 1.00" was really 75% — and the false positives
# concentrated on the SELF-pursuit ("restating the theme in fresh words"), exactly the §5 failure the
# plan predicted. So Phase-2's judge arrives BEFORE the RETURN can enforce anything: a proxy-nominated
# advance becomes PENDING, and only the Emissary-family judge (refute-biased, against the pursuit's
# OWN prior standing) confirms it into the record. The RETURN then re-presents only judge-confirmed
# progress. Judge unavailable → stays pending (retried next sleep, capped) — no judge, no verdict.
PURSUITS_LIVE     = True     # Phase-1 kill-switch: False = shadow-exact (no seeds touched)
_JUDGE_BATCH      = 24                     # per sleep sweep
_JUDGE_RETRIES    = 2                      # pending survives this many unavailable sweeps, then drops
_RETURN_COOLDOWN  = 1500.0                 # ≥25 min between returns reaching his seed
_RETURN_P         = 0.35                   # of eligible wandering seeds
_last_return      = 0.0

_RETURN_OPENINGS = (
    # D-0032/J-0217 redesign (2026-08-25): {s} is now a genuine word-safe quote of his own prior line
    # (was raw-truncated, guillotining mid-word), and {o} is a real extracted open question (the
    # object's own `open` field, unused since Phase 0) — not just the birth question restated.
    "A thread of yours is still lying where you left it. In your own words: \"{s}\" The open piece you "
    "left hanging: {o} Pick up from there, not from the start.",
    "You were working something through — {q} Your own last line on it was: \"{s}\" What you hadn't "
    "answered yet: {o} Continue it; don't restart it.",
    "One of your own open questions is waiting: {q} You had it at: \"{s}\" The unresolved thread: {o} "
    "Build on that exact step.",
)


def _load() -> list[dict]:
    # D-0347 (J-1834, F-2401 item 3): a missing file is a normal first boot (empty register, silent, as before);
    # an unreadable / torn one used to be logged at DEBUG only and become a silent EMPTY register that the next
    # _save overwrote. Now: a loud WARNING and the file MOVED ASIDE (data/pursuits_active.corrupt.<UTC stamp>.json)
    # before the same empty register is returned. A healthy file loads exactly as before.
    return _sp.load_json_or_move_aside(_ACTIVE, list, logger, "pursuits", "an EMPTY pursuit register (0 pursuits)")


def _save(items: list[dict]) -> None:
    try:
        _DIR.mkdir(parents=True, exist_ok=True)
        # D-0347 (J-1834, F-2401 item 3): through <file>.tmp + os.replace (core/store_persist) instead of
        # truncating the 19 MB register in place; same bytes, still fail-open, now logged above debug level.
        _sp.write_text_atomic(_ACTIVE, json.dumps(items, ensure_ascii=False, indent=1))
    except Exception as exc:
        logger.warning("[pursuits] active register save failed (%s: %s); previous file left intact "
                       "(non-fatal). D-0347.", type(exc).__name__, exc)
        return
    _write_light(items)     # J-1893 (D-0154 pattern): additive companion, fail-open, never raises


# J-1893 (F-2522 spawn, D-0154 pattern): the light companion for status() / sample_series().
# status() only needs counts + a handful of sums + the top-8 summary rows, but used to json-parse the whole
# ~19 MB register (347 ms, every 30-33 s via sensorium.tick -> sample_series, plus the HUD gate card).
# _save() now ALSO writes data/pursuits_active.light.json = {"ts", "heavy": [size, mtime_ns of the heavy
# file right after its atomic replace], "status": <exactly what status() returns>}. status() trusts it only
# while the heavy file's (size, mtime_ns) still equals the recorded stamp, so a heavy file changed by anything
# other than this module's _save (hand edit, restore, move-aside) is never answered from a stale light file.
# Shadow-first like the other D-0154 readers: PURSUITS_LIGHT_READ stays False (status() reads the heavy file as
# always and, once a minute, logs heavy-vs-light agreement to data/light_sidecar_shadow.jsonl) until that log
# agrees; flip it then. The heavy file stays the store of record and is written byte-for-byte as before.
PURSUITS_LIGHT_READ = True  # J-2063: flipped 2026-10-15 (F-2647: 842/842 agree); live at next boot


def _light_path() -> Path:
    """Beside whatever _ACTIVE currently points at, resolved at CALL time (F-1212/F-1213: a test that
    redirects only _ACTIVE must never write the live light file)."""
    return _ACTIVE.with_name(_ACTIVE.stem + ".light.json")


def _heavy_stamp() -> "list | None":
    try:
        st = _ACTIVE.stat()
        return [int(st.st_size), int(st.st_mtime_ns)]
    except Exception:
        return None


def _write_light(items: list, stamp: "list | None" = None) -> None:
    try:
        from core import light_sidecar as _ls
        from core import profile as _profile
        stamp = stamp if stamp is not None else _heavy_stamp()
        if stamp is None:
            return
        path = _profile.guard_path(_light_path())
        _ls.write_atomic(path, {"ts": time.time(), "heavy": stamp, "status": _status_from_items(items)})
    except Exception as exc:
        logger.debug("[pursuits] light sidecar write failed (non-fatal): %s", exc)


def _light_status() -> "dict | None":
    """status() answered from the light companion, or None (missing / unparseable / stale vs the heavy file)."""
    try:
        from core import light_sidecar as _ls
        light = _ls.load(_light_path())
        if not isinstance(light, dict) or not isinstance(light.get("status"), dict):
            return None
        stamp = _heavy_stamp()
        if stamp is None or light.get("heavy") != stamp:
            return None
        s = light["status"]
        if "active" not in s or "pursuits" not in s:
            return None
        return s
    except Exception:
        return None


def _log(ev: dict) -> None:
    try:
        _DIR.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── J-3000 (F-3700, P-0100) — make a pursuit ruling reconstructable ─────────────────────────────
# The cycle_id passed with every pursuit ruling is the CONVERSATION cycle that was current when the idle thought
# was observed, not the idle thought judged (F-3700: 578 advances rulings share 102 ids), and the pending item is
# deleted the moment a verdict lands - so afterwards nothing says WHICH thought and WHICH prior position a
# ruling was about. judge_pending now writes one compact row per resolved item to data/pursuits_judged.jsonl.
# Additive: no verdict, register field read, or judge_panel signature changes. Readers: pursuits.judged_rows()
# and scripts/pursuits_judged_read.py (join to data/judge_panel_log.jsonl by pursuit_id + ruled_ts).
JUDGED_LOG   = True     # kill switch: False = no pursuits_judged.jsonl rows (the pending item still gets its sha)
JUDGED_KEEP  = 3000     # newest rows kept; older trimmed on flush


def _judged_path() -> Path:
    """data/pursuits_judged.jsonl, resolved at CALL time from _DIR (F-1212/F-1213 lesson: a test that redirects
    _DIR must never write the live file)."""
    return _DIR / "pursuits_judged.jsonl"


def _thought_sha(thought: str, ts) -> str:
    """Fingerprint of an idle thought: sha1 of its first 80 chars (stripped) plus its observe timestamp. Stable
    across the JSON round trip of the register (ts is formatted to the millisecond), so a pending item queued
    before this existed gets the same sha when computed lazily at judge time."""
    try:
        return hashlib.sha1(f"{(thought or '').strip()[:80]}|{float(ts):.3f}".encode("utf-8")).hexdigest()[:12]
    except Exception:
        return ""


def _judged_row(p: dict, item: dict, verdict, how, why, ruled_ts: float, dropped: bool = False) -> dict:
    """The compact reconstruction row for one resolved pending item (pure: no I/O)."""
    row = {"ts": ruled_ts, "ruled_ts": ruled_ts, "pursuit_id": p.get("id"),
           "question": (p.get("question") or "")[:100],
           "thought_sha": item.get("thought_sha") or _thought_sha(item.get("thought", ""), item.get("ts")),
           "thought_ts": item.get("ts"),
           "thought": (item.get("thought") or "")[:200],
           "prior_standing": (item.get("prior_standing") or "")[:200],
           "verdict": verdict, "how": how, "why": ((why or "")[:160] if isinstance(why, str) else None),
           "restate_sim": item.get("restate_sim"), "coherent": item.get("coherent"),
           "cycle_id": str(item.get("cycle_id") or ""),   # the CONVERSATION cycle, not this thought (F-3700)
           "tries": item.get("tries", 0)}
    if dropped:
        row["dropped"] = True
    return row


def _flush_judged(rows: list) -> None:
    """Append `rows` to data/pursuits_judged.jsonl and keep only the newest JUDGED_KEEP. Fail-open, never raises."""
    if not (JUDGED_LOG and rows):
        return
    try:
        path = _judged_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        if path.stat().st_size > 256 * 1024:                # the count only matters once the file is non-trivial
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > JUDGED_KEEP:
                _sp.write_text_atomic(path, "\n".join(lines[-JUDGED_KEEP:]) + "\n")
    except Exception as exc:
        logger.debug("[pursuits] judged-row log failed (non-fatal): %s", exc)


def judged_rows(pursuit_id: str = "", limit: int = 50) -> list:
    """READER for pursuits_judged.jsonl: oldest-first rows (optionally one pursuit's), the last `limit` of them.
    [] on any error or a missing file. Read-only."""
    try:
        out = []
        for ln in _judged_path().read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if not pursuit_id or r.get("pursuit_id") == pursuit_id:
                out.append(r)
        return out[-max(1, int(limit)):]
    except Exception:
        return []


def _cos(a, b) -> float:
    """Cosine between two vectors given as lists/arrays. 0.0 on any error/None."""
    try:
        import numpy as _np
        va, vb = _np.asarray(a, dtype=_np.float32), _np.asarray(b, dtype=_np.float32)
        na, nb = _np.linalg.norm(va), _np.linalg.norm(vb)
        if na == 0 or nb == 0:
            return 0.0
        return float(_np.dot(va, vb) / (na * nb))
    except Exception as exc:
        logger.debug("[pursuits] cosine calc failed (non-fatal): %s", exc)
        return 0.0


def _running_centroid(old, vec, n: int):
    """Incremental mean of the pursuit's advancing thought-vecs (as a plain list for JSON)."""
    try:
        import numpy as _np
        v = _np.asarray(vec, dtype=_np.float32)
        if old is None or n <= 0:
            return v.tolist()
        c = _np.asarray(old, dtype=_np.float32)
        return ((c * n + v) / (n + 1)).tolist()
    except Exception as exc:
        logger.debug("[pursuits] running_centroid calc failed (non-fatal): %s", exc)
        return list(vec) if vec is not None else old


def _decay_and_prune(items: list[dict], now: float) -> list[dict]:
    """Cool untouched pursuits; mark the exhausted ones dormant (freeing a slot)."""
    for p in items:
        if p.get("status") != "active":
            continue
        dt_h = max(0.0, (now - p.get("last_touched", now)) / 3600.0)
        p["heat"] = round(max(0.0, p.get("heat", 0.0) - HEAT_DECAY_PER_H * dt_h), 3)
        if p["heat"] < DORMANT_BELOW:
            p["status"] = "dormant"
            _log({"event": "dormant", "ts": now, "id": p["id"], "question": p["question"][:100],
                  "advances": p.get("advances", 0), "restates": p.get("restates", 0)})
    return items


def observe(thought: str, about: str = "", vec=None, unresolved: bool = False, cycle_id: str = "",
            done_when: str = "", train_id: str = "") -> dict | None:
    """PHASE 0 SHADOW: match this idle thought to the pursuit register, judge advance-vs-restate, accumulate,
    manage births/heat/dormancy — and CHANGE NOTHING he sees. Returns the event (or None). Never raises."""
    global _last_observe
    try:
        now = time.time()
        if now - _last_observe < OBSERVE_COOLDOWN:
            # J-0558/F-0768, measure-only — see _log_cooldown_skip: does NOT touch the cooldown itself.
            if unresolved:
                _log_cooldown_skip(now)
            return None
        if not thought or len(thought.strip()) < 25:
            return None
        _last_observe = now
        if vec is None:
            try:
                from core.memory.store import _embed
                vec = _embed(thought)
            except Exception as exc:
                logger.debug("[pursuits] embed failed (non-fatal): %s", exc)
                vec = None
        if vec is None:
            return None
        try:                                           # → a list of PYTHON floats (np.float32 is not JSON-safe;
            vec = vec.tolist() if hasattr(vec, "tolist") else [float(x) for x in vec]   # a silent _save killer)
        except Exception as exc:
            logger.debug("[pursuits] vec-to-list conversion failed (non-fatal): %s", exc)
            return None

        items = _decay_and_prune(_load(), now)
        active = [p for p in items if p.get("status") == "active"]

        # best-matching active pursuit (this thought is "on" it if close enough to its centroid).
        # Anti-capture: self-topic pursuits need a TIGHTER match to accrete (the attractor pulls
        # everything loosely near it — that's how one pursuit ate the register).
        best, best_sim, best_bar = None, 0.0, MATCH_MIN
        for p in active:
            s = _cos(vec, p.get("centroid"))
            if s > best_sim:
                best, best_sim = p, s
                best_bar = MATCH_MIN + (SELF_MATCH_PENALTY if _is_self_topic(p.get("question", "")) else 0.0)

        ev = None
        if best is not None and best_sim >= best_bar:
            # ADVANCE vs RESTATE — decoupled: the thought vs the pursuit's OWN recent thoughts (never his say-so).
            restate_sim = max([_cos(vec, rv) for rv in best.get("recent_vecs", [])] or [0.0])
            is_restate = restate_sim >= RESTATE_MIN
            n = len(best.get("thoughts", []))
            best["centroid"] = _running_centroid(best.get("centroid"), vec, n)
            best["recent_vecs"] = ([vec] + best.get("recent_vecs", []))[:RECENT_VECS_KEEP]
            best["last_touched"] = now
            coherent = None
            if is_restate:
                # near-verbatim: certain without a judge. Standing is NOT overwritten by a restate
                # (2026-08-15 — the plan's own words: standing is overwritten each ADVANCE; letting
                # restates poison it would hand the RETURN an echo to re-present).
                best["restates"] = best.get("restates", 0) + 1
                best["heat"] = round(max(0.0, best.get("heat", 0.0) + HEAT_RESTATE), 3)
                kind = "restated"
            else:
                # JUDGE-GATED (2026-08-15): the proxy only NOMINATES. The advance becomes PENDING —
                # no advances count, no heat, no standing update — until the cross-family judge
                # confirms it against the pursuit's own prior standing (judge_pending, sleep sweep).
                coherent = restate_sim >= COHERENT_MIN
                best.setdefault("pending", []).append({
                    "thought": thought.strip()[:400], "about": about[:60], "ts": now,
                    "cycle_id": cycle_id, "restate_sim": round(restate_sim, 3),
                    "train_id": str(train_id or "")[:16],             # J-3983: train-level key, so goals can derive spawned_by
                    "coherent": coherent, "tries": 0,
                    "thought_sha": _thought_sha(thought, now),       # J-3000 / F-3700: the thought's own id
                    "prior_standing": (best.get("standing") or best.get("question", ""))[:300]})
                # J-2997 (F-3693): the slice below silently discarded the oldest nominations (about 69% of October's
                # never reached the judge). Log what it drops; the cap itself is unchanged (a separate decision).
                _over = best["pending"][:-12]
                best["pending"] = best["pending"][-12:]      # bounded queue
                if _over:
                    _log({"event": "pending_overflow", "ts": now, "id": best["id"], "dropped": len(_over),
                          "dropped_sha": [str(_o.get("thought_sha") or "") for _o in _over],
                          "kept": len(best["pending"])})
                kind = "advance_pending"
            ev = {"event": kind, "ts": now, "cycle_id": cycle_id, "id": best["id"],
                  "question": best["question"][:100], "match_sim": round(best_sim, 3),
                  "restate_sim": round(restate_sim, 3), "coherent": coherent,
                  "advances": best.get("advances", 0), "restates": best.get("restates", 0),
                  "coheres": best.get("coheres", 0), "scatters": best.get("scatters", 0),
                  "heat": best["heat"]}
            _log(ev)

        else:
            # J-0558 (F-0768), SHADOW-ONLY — never gates anything below this block. No active pursuit
            # claimed this thought. Today dormancy is TERMINAL: the only dormant->active path is
            # _apply_confirmed() on a pending item queued BEFORE the pursuit went dormant, so a later
            # thought like this one never gets a real chance to rejoin. Scan dormant centroids anyway
            # and log a reawaken_candidate when one is a real match — tighter than the live bar, since
            # a dormant centroid is stale (F-0768: it carries a single birth thought's sensory framing,
            # not the accumulated concept). Then fall through to the EXACT SAME birth logic as before:
            # a birth still happens if unresolved, so the log shows how often it duplicates a dormant
            # thread the register just walked past.
            dormant = [p for p in items if p.get("status") == "dormant"]
            d_best, d_sim, d_bar = None, 0.0, REAWAKEN_MIN
            for p in dormant:
                s = _cos(vec, p.get("centroid"))
                if s > d_sim:
                    d_best, d_sim = p, s
                    d_bar = REAWAKEN_MIN + (SELF_MATCH_PENALTY if _is_self_topic(p.get("question", "")) else 0.0)
            if d_best is not None and d_sim >= d_bar:
                _log({"event": "reawaken_candidate", "ts": now, "cycle_id": cycle_id, "id": d_best["id"],
                      "question": d_best["question"][:100], "match_sim": round(d_sim, 3),
                      "dormant_hours": round((now - d_best.get("last_touched", now)) / 3600.0, 2),
                      "advances": d_best.get("advances", 0), "would_birth": bool(unresolved),
                      "rare_token_overlap": _rare_token_overlap(
                          thought, f"{d_best.get('question', '')} {d_best.get('about', '')}")})

            if unresolved:
                # BIRTH — a genuine open conflict (the model's own signal) on new ground → a new pursuit. GATED:
                # unresolved only (not every thought), under cap (or displace the coldest dormant).
                # Anti-capture: at most ONE active self-topic pursuit — the self-attractor already has
                # the whole identity stack (T4, estate, themes); the register is for the OTHER threads.
                if _is_self_topic(thought) and sum(
                        1 for p in active if _is_self_topic(p.get("question", ""))) >= SELF_TOPIC_MAX:
                    _save(items)
                    return None
                if len(active) >= CAP:
                    dorm = [p for p in items if p.get("status") == "dormant"]
                    if dorm:
                        # J-0558 (F-0768): a birth-at-CAP silently deleted the coldest dormant pursuit
                        # with no log line — 44/368 born pursuits had vanished from the register with
                        # their thoughts, untraceable. Log the eviction before it happens.
                        evicted = min(dorm, key=lambda p: p.get("heat", 0.0))
                        _log({"event": "evicted", "ts": now, "id": evicted["id"],
                              "question": evicted.get("question", "")[:100],
                              "advances": evicted.get("advances", 0),
                              "restates": evicted.get("restates", 0),
                              "heat": evicted.get("heat", 0.0),
                              "dormant_hours": round(
                                  (now - evicted.get("last_touched", now)) / 3600.0, 2)})
                        items.remove(evicted)
                    else:
                        _save(items)
                        return None                       # register full of live threads — do not fragment
                pid = uuid.uuid4().hex[:8]
                p = {"id": pid, "question": thought.strip()[:250], "about": about[:60], "born": now,
                     "standing": thought.strip()[:300], "thoughts": [thought.strip()[:200]],
                     "established": [about] if about else [],
                     "open": _extract_open_question(thought), "centroid": vec,
                     "recent_vecs": [vec], "advances": 1, "restates": 0, "coheres": 0, "scatters": 0,
                     "last_touched": now, "heat": HEAT_BORN, "status": "active", "cycle_id": cycle_id}
                if train_id:               # J-3983: additive train-level key (the born thought's train + every confirmed advance's)
                    p["train_ids"] = [str(train_id)[:16]]
                if p["open"] and OPEN_FILL:
                    p["open_source"] = "thought"
                if QUESTION_AT_BIRTH:      # D-0554 / J-3165: the real question (or none) recorded beside the birth thought
                    p["question_kind"], p["question_text"] = classify_birth(thought, done_when)
                _fill_open(p, now)         # D-0618 / J-3229: no literal '?' -> the board entry / done_when (no-op otherwise)
                items.append(p)
                if done_when:              # J-2160: the closing condition, side store only (core/done_when.py)
                    try:
                        from core import done_when as _dw
                        _dw.record("pursuit", pid, done_when, _dw.JUDGE_PURSUIT, source="monologue",
                                   cycle_id=cycle_id, now=now)
                    except Exception:
                        pass
                ev = {"event": "born", "ts": now, "cycle_id": cycle_id, "id": pid,
                      "question": p["question"][:100], "about": about[:40]}
                if "question_kind" in p:
                    ev["question_kind"] = p["question_kind"]
                    ev["question_text"] = p["question_text"][:100]
                _log(ev)
                logger.info("[pursuits] BORN: %s", p["question"][:70])

        _save(items)
        return ev
    except Exception as exc:
        logger.debug("[pursuits] observe failed (non-fatal): %s", exc)
        return None


def _status_from_items(items: list) -> dict:
    """Phase-0 metrics from a loaded register (the pure part of status(); also what the light sidecar stores)."""
    active = [p for p in items if p.get("status") == "active"]
    tot_adv = sum(p.get("advances", 0) for p in items)
    tot_res = sum(p.get("restates", 0) for p in items)
    tot_coh = sum(p.get("coheres", 0) for p in items)
    tot_sca = sum(p.get("scatters", 0) for p in items)
    return {
        "active": len(active), "dormant": sum(1 for p in items if p.get("status") == "dormant"),
        "saturated": sum(1 for p in items if p.get("status") == "saturated"),
        "total_advances": tot_adv, "total_restates": tot_res,
        "total_coheres": tot_coh, "total_scatters": tot_sca,
        "advance_ratio": round(tot_adv / max(1, tot_adv + tot_res), 3),   # axis 1: NOT word-for-word repeating
        # axis 2 (2026-07-08): of the advances, how many BUILD on a recent thought vs SCATTER to a new facet.
        # Low here + high advance_ratio = the monoculture touring its theme (passes restate, isn't accumulating).
        "coherence_ratio": round(tot_coh / max(1, tot_coh + tot_sca), 3),
        "pursuits": [{"q": p["question"][:60], "advances": p.get("advances", 0),
                      "restates": p.get("restates", 0), "coheres": p.get("coheres", 0),
                      "scatters": p.get("scatters", 0), "heat": p.get("heat", 0.0),
                      "status": p.get("status")} for p in sorted(items, key=lambda x: -x.get("heat", 0))[:8]],
    }


def status() -> dict:
    """Phase-0 metrics: the live register + the gate signal (advance:restate — is progress GENUINE?).
    J-1893: with PURSUITS_LIGHT_READ answered from the light sidecar (falls back to the heavy file if the light
    one is missing/stale); in shadow mode reads the heavy file as always and, once a minute, logs agreement."""
    if PURSUITS_LIGHT_READ:
        s = _light_status()
        if s is not None:
            return s
    stamp0 = _heavy_stamp()
    t0 = time.perf_counter()
    items = _load()
    out = _status_from_items(items)
    heavy_ms = (time.perf_counter() - t0) * 1000.0
    try:
        from core import light_sidecar as _ls
        light = None
        if not PURSUITS_LIGHT_READ and _ls.shadow_due("pursuits.status"):
            t1 = time.perf_counter()
            light = _light_status()
            light_ms = (time.perf_counter() - t1) * 1000.0
            _dig = lambda d: None if d is None else hashlib.sha1(
                json.dumps(d, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
            _ls.shadow_log("pursuits.status", _dig(out), _dig(light), heavy_ms, light_ms,
                           active=out.get("active"), saturated=out.get("saturated"),
                           light_present=light is not None)
        # (re)build the companion from the parse we just paid for when it is missing/stale, as long as the
        # heavy file did not change under us (first status() after the merge, or after a restore / hand edit)
        if stamp0 is not None and stamp0 == _heavy_stamp():
            if light is None:
                light = _light_status()
            if light is None:
                _write_light(items, stamp0)
    except Exception as exc:
        logger.debug("[pursuits] light sidecar shadow/refresh failed (non-fatal): %s", exc)
    return out


_SERIES_CAP = 600
_SAMPLE_GAP = 30.0
_last_series = 0.0


def sample_series(force: bool = False) -> None:
    """Append the register's current numerics (active threads · advance_ratio) for the HUD gate card.
    Rate-limited; called from the HUD refresh. Fail-open."""
    global _last_series
    now = time.time()
    if not force and now - _last_series < _SAMPLE_GAP:
        return
    _last_series = now
    try:
        s = status()
        row = {"ts": round(now, 1), "active": s["active"], "advance_ratio": s["advance_ratio"],
               "coherence_ratio": s["coherence_ratio"], "saturated": s["saturated"],
               "advances": s["total_advances"], "restates": s["total_restates"]}
        with open(_SERIES, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        lines = _SERIES.read_text(encoding="utf-8").splitlines()
        if len(lines) > _SERIES_CAP * 1.3:
            _SERIES.write_text("\n".join(lines[-_SERIES_CAP:]) + "\n", encoding="utf-8")
    except Exception as exc:
        logger.debug("[pursuits] sample_series failed (non-fatal): %s", exc)


# ═══ THE CROSS-FAMILY JUDGE SWEEP + THE RETURN (Phase 1+2 fused, 2026-08-15) ═══════════════════════

def _apply_confirmed(p: dict, item: dict, now: float) -> None:
    """A judge-confirmed advance enters the record: standing overwritten, thought kept, heat up,
    saturation checked. Revives a pursuit that cooled to dormant while its advance waited."""
    key = "coheres" if item.get("coherent") else "scatters"
    p[key] = p.get(key, 0) + 1
    p["thoughts"] = (p.get("thoughts", []) + [item["thought"][:200]])[-THOUGHTS_KEEP:]
    p["advances"] = p.get("advances", 0) + 1
    p["standing"] = item["thought"][:300]
    # D-0032/J-0217: `open` is sticky — an advance that only asserts (no fresh "?") keeps the prior
    # open question live rather than blanking it; a thought that DOES pose a new one replaces it.
    _oq = _extract_open_question(item["thought"])
    if OPEN_FILL and item.get("cycle_id"):        # D-0618 / J-3229: remember the thought, so its `ask` (boarded by that cycle) links
        p["cycle_ids"] = (list(p.get("cycle_ids") or []) + [str(item["cycle_id"])[:8]])[-_CYCLE_IDS_KEEP:]
    if item.get("train_id"):                      # J-3983: additive; goals.py derives spawned_by from a shared train id
        _tids = list(p.get("train_ids") or [])
        if str(item["train_id"]) not in _tids:
            _tids.append(str(item["train_id"]))
        p["train_ids"] = _tids[-_CYCLE_IDS_KEEP:]
    if _oq:
        p["open"] = _oq
        if OPEN_FILL:
            p["open_source"] = "thought"
        # THE FOLLOW LINE (J-2459, docs/staged/question_cargo.md §2.1): the pursuit's open question boards the
        # line (source="pursuit"); a settled return answers the QUESTION, it never closes the pursuit (D-0426's).
        try:
            from core import follow_line as _fl
            _fl.board(_oq, "pursuit", about=(p.get("about") or "")[:60],
                      asked_by={"pursuit_id": p.get("id", ""), "ts": now}, allow_self=True)
        except Exception as _exc_fl:
            if type(_exc_fl).__name__ == "NonLiveWriteError":
                raise
            logger.debug("[pursuits] follow_line boarding failed (non-fatal): %s", _exc_fl)
    elif not (p.get("open") or "").strip():
        _fill_open(p, now)                         # D-0618 / J-3229: no literal '?' in this advance -> board / done_when
    if item.get("about") and item["about"] not in p.get("established", []):
        p["established"] = (p.get("established", []) + [item["about"]])[-THOUGHTS_KEEP:]
    p["heat"] = round(min(1.0, p.get("heat", 0.0) + HEAT_ADVANCE), 3)
    if p.get("status") == "dormant":
        p["status"] = "active"
    _log({"event": "advanced", "ts": now, "cycle_id": item.get("cycle_id", ""), "id": p["id"],
          "question": p["question"][:100], "restate_sim": item.get("restate_sim"),
          "coherent": item.get("coherent"), "judge": "confirmed",
          "advances": p["advances"], "restates": p.get("restates", 0),
          "coheres": p.get("coheres", 0), "scatters": p.get("scatters", 0), "heat": p["heat"]})
    if p.get("advances", 0) >= SATURATE_ADVANCES and p.get("status") == "active":
        p["status"] = "saturated"
        _log({"event": "saturated", "ts": now, "id": p["id"], "question": p["question"][:100],
              "advances": p["advances"], "coheres": p.get("coheres", 0),
              "scatters": p.get("scatters", 0)})
        logger.info("[pursuits] SATURATED: %s (adv=%d)", p["question"][:60], p["advances"])


PURSUITS_SAVE_OFFLOOP = True   # J-2142: judge_pending's register save runs in a worker thread; False = inline


async def judge_pending(max_items: int = _JUDGE_BATCH) -> dict:
    """The sleep sweep: judge queued advance-candidates with the cross-family judge, refute-biased,
    against the pursuit's OWN prior standing. Confirmed -> the advance enters the record. Refuted ->
    counted a restate. Unavailable -> stays pending (retried; dropped after _JUDGE_RETRIES sweeps,
    logged - the instrument always says why). Never raises."""
    out = {"judged": 0, "confirmed": 0, "refuted": 0, "kept_pending": 0, "dropped": 0,
           "judge_batch_cut": 0}   # J-2997: pending items left unjudged this sweep because of the max_items cap
    judged_rows_out: list = []      # J-3000: flushed to pursuits_judged.jsonl AFTER the register save (see below)
    try:
        now = time.time()
        items = _load()
        _all_pending = [(p, i) for p in items for i in list(p.get("pending", []))]
        todo = _all_pending[:max_items]
        out["judge_batch_cut"] = max(0, len(_all_pending) - len(todo))
        if out["judge_batch_cut"]:
            _log({"event": "judge_batch_cut", "ts": now, "cut": out["judge_batch_cut"],
                  "judged_cap": max_items, "pending_total": len(_all_pending)})
        if not todo:
            return out
        # JUDGE PANEL (2026-08-15, the serving split): two families rule independently; agreement is
        # the verdict; disagreement escalates to the tiebreak (granite3.1-moe:3b on :11437); unavailable → None (no verdict).
        from core import judge_panel as _jp
        if True:
            for p, item in todo:
                _sys = ("You are a strict judge of intellectual progress. A thought ADVANCES a "
                        "pursuit only if it adds something genuinely new beyond the pursuit's prior "
                        "position: a further step, a consequence, a distinction, evidence, or a "
                        "development. Restating the theme in fresh words, circling it, or merely "
                        "mentioning it does NOT advance. When uncertain, answer false. Output ONLY "
                        'JSON: {"advances": true|false, "why": "<one short clause>"}')
                _pq = _trunc_words(driving_question(p), 250)
                _ps = _trunc_words(item.get("prior_standing", ""), 300)
                # first judged advance: standing == question, so don't send the same text twice (J-2999)
                if not _ps or _ps == _pq or _ps == (p.get("question") or "").strip()[:300]:
                    _ps = "same as the pursuit itself"
                _usr = (f"PURSUIT: {_pq}\n\n"
                        f"ITS PRIOR POSITION: {_ps}\n\n"
                        f"NEW THOUGHT: {item.get('thought','')[:400]}\n\nDoes the thought advance the pursuit?")
                # J-3000 (F-3700): rule_detail returns the SAME verdict rule() does (rule() is just its "verdict" key) plus
                # the panel's `how`/`why`, which the pursuits_judged.jsonl row records.
                # J-2205 passed cycle_id so a ruling could be joined to data/training/ - but for THIS caller that id
                # is the conversation cycle current when the idle thought was observed, not the thought judged
                # (F-3700: 578 rulings, 102 ids), so that join is NOT reliable here; use pursuits_judged.jsonl
                # (thought_sha, pursuit_id, ruled_ts) to reconstruct what a ruling was about.
                det = await _jp.rule_detail(_sys, _usr, "advances", context=f"pursuit:{p['id']}",
                                            cycle_id=str(item.get("cycle_id") or ""))
                _ruled = time.time()
                verdict = det.get("verdict") if isinstance(det, dict) else None
                _how = det.get("how") if isinstance(det, dict) else None
                _why = det.get("why") if isinstance(det, dict) else None
                # NEEDLE TRIAGE (2026-08-18 module, wired 2026-08-19 — the survey found it built,
                # smoke-tested once, and never actually connected to real panel volume despite its own
                # purpose requiring exactly that). SHADOW ONLY: off the event loop (to_thread, the tiny
                # CPU model still costs a moment), its own read logged alongside the panel's — never
                # touches `verdict`, never gates this judgment. Best-effort, never raises (read() is
                # already fully fail-open internally; this guard is belt-and-braces).
                try:
                    import asyncio as _aio
                    from core import needle_triage as _nt
                    await _aio.to_thread(_nt.read, driving_question(p), item.get("prior_standing", ""),
                                         item.get("thought", ""), f"pursuit:{p['id']}")
                except Exception:
                    pass
                if verdict is None:
                    item["tries"] = item.get("tries", 0) + 1
                    if item["tries"] > _JUDGE_RETRIES:
                        p["pending"].remove(item)
                        judged_rows_out.append(_judged_row(p, item, None, _how, _why, _ruled, dropped=True))
                        out["dropped"] += 1
                        _log({"event": "judge_dropped", "ts": now, "id": p["id"],
                              "question": p["question"][:80]})
                    else:
                        out["kept_pending"] += 1
                    continue
                p["pending"].remove(item)
                judged_rows_out.append(_judged_row(p, item, bool(verdict), _how, _why, _ruled))
                out["judged"] += 1
                if verdict:
                    out["confirmed"] += 1
                    _apply_confirmed(p, item, now)
                else:
                    out["refuted"] += 1
                    p["restates"] = p.get("restates", 0) + 1
                    p["heat"] = round(max(0.0, p.get("heat", 0.0) + HEAT_RESTATE), 3)
                    _log({"event": "restated", "ts": now, "cycle_id": item.get("cycle_id", ""),
                          "id": p["id"], "question": p["question"][:100],
                          "restate_sim": item.get("restate_sim"), "judge": "refuted",
                          "advances": p.get("advances", 0), "restates": p["restates"],
                          "heat": p["heat"]})
        # J-2142 (F-2825 / J-2141 probe): the 23.5 MB register save (json.dumps indent=1 + atomic write, 0.56 s on a
        # 10-18 copy) was the synchronous tail of this sweep; on 6 of the 10-16 22:37 boot's freezes the loop was
        # already held 0.2-2.4 s BEFORE the '[pursuits] judge sweep' log line below. Off the loop now (worker
        # thread, awaited, same order; _save is fail-open inside itself and store_persist's per-path lock
        # serialises it against any loop-thread save). Kill switch: PURSUITS_SAVE_OFFLOOP = False = inline.
        if PURSUITS_SAVE_OFFLOOP:
            from core.sleep_offloop import off_loop as _sleep_off
            await _sleep_off(_save, items)
        else:
            _save(items)
        # J-3000 (F-3700): the reconstruction rows go out only once the register that no longer holds those pending
        # items is saved, so a failed sweep (which leaves the items pending to be re-judged) never logs a ruling twice.
        _flush_judged(judged_rows_out)
        # J-2171 / D-0426 A: judge-set close, SHADOW LOG ONLY (never edits `items`, status, or the saved
        # register; own try so it can never fail the sweep). Restart-gated like everything else here.
        try:
            from core import pursuit_close_shadow as _pcs
            await _pcs.sweep(items)
        except Exception as _exc:
            logger.debug("[pursuits] close shadow failed (non-fatal): %s", _exc)
        if out["judged"] or out["dropped"] or out["judge_batch_cut"]:
            logger.info("[pursuits] judge sweep: %s", out)
    except Exception as exc:
        logger.debug("[pursuits] judge sweep failed (non-fatal): %s", exc)
    return out


def _is_rested(p: dict) -> bool:
    """True if he set this pursuit down (an accepted set_down note in the goal register) and has not taken it up
    again. Fail-open: any error means not rested."""
    try:
        from core import goal_offer
        return goal_offer.is_rested_id(f"pursuit:{p.get('id')}")
    except Exception:
        return False


def return_seed() -> "tuple[str, str] | None":
    """PHASE 1 - THE RETURN (the behaviour change that turns pulses into a stream): pick the active
    pursuit most hungry for attention (heat x hours-since-touched), retrieval-framed, re-presenting
    ONLY judge-confirmed standing. Self-topic pursuits are NOT return-eligible (the self-attractor
    has the whole identity stack already; the register's value is the OTHER threads). Cooled-down,
    paraphrase-varied; the caller logs the injection. Returns (seed_line, pursuit_id) or None.

    D-0032/J-0217 redesign (2026-08-25): now ALSO requires a real extracted `open` question (not
    just non-empty `standing`) and quotes standing word-safely instead of raw-truncating it — see
    _extract_open_question / _trunc_words and the docstring on _RETURN_OPENINGS above."""
    global _last_return
    try:
        if not PURSUITS_LIVE:
            return None
        now = time.time()
        if now - _last_return < _RETURN_COOLDOWN:
            return None
        import random as _random
        if _random.random() > _RETURN_P:
            return None
        items = _load()
        pre = [p for p in items if p.get("status") == "active"
               and not _is_self_topic(p.get("question", ""))
               and p.get("advances", 0) >= 2            # judged substance exists to return TO
               and not is_observation(p)                 # D-0554/J-3165: born as an observation = never return-eligible
               and (p.get("standing") or "").strip()
               and not _is_rested(p)]                    # Layered goals Phase 6 (D-0768): he set it down; it stays down
        if OPEN_FILL:      # D-0618 / J-3229: an eligible-but-unfilled pursuit gets its `open` from the board / done_when
            if any([_fill_open(p, now) for p in pre if not (p.get("open") or "").strip()]):   # list: fill every one
                _save(items)
        cands = [p for p in pre
                 if ((p.get("open") or "").strip()       # D-0032/J-0217: sharper-eligibility gate -
                      # a real open question to return TO, not just standing; D-0554: or the done_when it was born with
                      or (p.get("question_kind") == "done_when" and (p.get("question_text") or "").strip()))]
        if not cands:
            return None
        hunger = lambda p: p.get("heat", 0.0) * (1.0 + min(6.0, (now - p.get("last_touched", now)) / 3600.0) / 3.0)
        best = max(cands, key=hunger)
        # J-1515 (memory_as_a_service.md §4.2): first-time integration -- return_seed() previously made
        # ZERO memory-store calls anywhere (verified: grep -n "recall|memory_edges|memory_levels|
        # associative_recall" core/pursuits.py -> no matches). Fetched BEFORE `line` is built so a
        # failure here can never touch `line`'s own construction just below; frags defaults to [] on
        # any failure (memory_service.ask() is already fail-open, this wrapper is defence in depth,
        # matching every other call site's own convention in this codebase).
        frags = []
        try:
            from core import memory_service as _memsvc
            frags = _memsvc.ask("pursuits", f"{driving_question(best)} {best.get('open', '')}", k=3,
                                grounded_only=True, descend=False)
        except Exception as exc:
            logger.debug("[pursuits] memory_service ask failed (non-fatal): %s", exc)
            frags = []
        line = _random.choice(_RETURN_OPENINGS).format(
            q=_trunc_words(driving_question(best).strip(), 140),     # D-0554: the extracted question, not the birth thought
            s=_trunc_words((best.get("standing") or "").strip(), 220),
            o=_trunc_words(((best.get("open") or "").strip()
                            or (best.get("question_text") or "").strip()), 150))
        # Grounding clause (same PATTERN as _author's grounding block, inner_monologue_node.py:
        # 5384-5391 -- build a short clause from recalled fragment content, append only if real
        # content came back): do NOT change the eligibility gate, cooldown or probability logic
        # above, only add this clause when frags is non-empty. Fail-open: on any exception here,
        # `line` is left exactly as built above -- same as before this job.
        try:
            if frags:
                bits = [" ".join((f.get("content") or "").split())[:120] for f in frags]
                bits = [b for b in bits if b]
                if bits:
                    line = line + " Something else you know that bears on this: " + "; ".join(bits[:2]) + "."
        except Exception as exc:
            logger.debug("[pursuits] grounding clause skipped (non-fatal): %s", exc)
        _last_return = now
        _log({"event": "returned", "ts": now, "id": best["id"],
              "question": best.get("question", "")[:100], "heat": best.get("heat"),
              "question_kind": best.get("question_kind", "legacy"), "open_source": best.get("open_source", "legacy"),
              "hours_untouched": round((now - best.get("last_touched", now)) / 3600.0, 2)})
        logger.info("[pursuits] RETURN -> %s (heat %.2f)", best.get("question", "")[:60], best.get("heat", 0))
        # J-1515 §4.3 metric-sheet hook: the "next output" this ask() fed is the return line itself
        # (the only thing this call produces) -- embedded the same way dream_node.py's own stall
        # detector and pursuits.py's own judge sweep (:272-273) already call _embed() elsewhere in
        # this codebase. Own try/except, deliberately separate from the return statement below, so a
        # metric-sheet failure can never turn a good return_seed() result into None.
        try:
            from core.memory.store import _embed as _embed_line
            from core import memory_service as _memsvc3
            _lv = _embed_line(line)
            if _lv is not None:
                _memsvc3.note_usage("pursuits", _lv)
        except Exception as exc:
            logger.debug("[pursuits] memory_service note_usage skipped (non-fatal): %s", exc)
        return (line, best["id"])
    except Exception as exc:
        logger.debug("[pursuits] return_seed failed (non-fatal): %s", exc)
        return None

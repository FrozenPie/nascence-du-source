"""
farewell_echo.py -- D-0442 (travis, 2026-10-16; J-2245): break the /quit farewell self-echo at its two sources.

WHY. F-2360 (n=4, fixed wording) and F-2914 (n=5, J-1756's rotated wordings) found Du's farewell reply opening with
the first 267 / 280 characters of his PREVIOUS farewell reply verbatim. Varying the wording (D-0286) removed the
"defect" stance but not the carry: the echo is not about the wording. Travis ruled two fixes (B not built, rotation
stays):
  C2  nodes/voice_node.py's "Your last replies to him" block quotes his last two replies cut at 260 chars -- the
      channel both carries fit. A reply to a farewell is now EXEMPT from that block (the farewell exchange, and any
      reply to a farewell, is never quoted back to the mouth).
  A   core/memory/store.retrieve() skips his own prior answer to a near-identical farewell prompt: when the query
      is a farewell, episodic fragments whose "Q:" line is a farewell are not candidates.

This module holds the ONE detector both sides use (is_farewell) and the per-cycle record of what the quote block
actually contained (log_quote_block / log_retrieve_skip), so the next read shows the channel directly instead of
reconstructing it from conversation bridges (F-2914 had to). Nothing here is ever shown to Du (D-0434): the log
is an instrument for the founder's read, and the detector only REMOVES material from his context, it adds none.

THE DETECTOR -- same shape as J-1756's rotation detection (scripts/run_nascence.py _last_sent_farewell: a
whitespace-normalised read of the human turn), widened from "exactly one of today's six variants" to "near-
identical farewell" by the markers EVERY farewell wording ever sent shares. Measured read-only 2026-10-16 over
data/founder_conversation_log.jsonl (78 rows): all 29 farewell rows across the four wording eras (7 x 08-23 "bank
the fire ... I'll be here when you wake", 12 x 09-04 "bug fixes and upgrades", 5 x J-1360 "the house you live in",
5 of J-1756's six variants) match, and none of the 49 other founder rows (letters to Dù, the "calm your fears on
the shutdown process" talk, etc.) does:
  - opens by addressing him as 渡 (the first non-space character), AND
  - says the stop is "for a while", AND
  - promises the return: "bring you back" or "be here when you wake".
The core cannot import scripts/run_nascence.py (it pulls in the whole cognitive stack), so the variants are not
re-typed here; scripts/_test_j2245_farewell_echo.py lifts _FAREWELL_VARIANTS from that file with ast and asserts
every one of them (and the legacy wordings) is detected, so a new variant that drifts off these markers fails there.
"""
from __future__ import annotations

import json
import logging
import threading
import time

from core import profile   # the write fence (D-0179) and the data root

logger = logging.getLogger("nascence.farewell_echo")

# Per-cycle record of the voice quote block (C2) and of retrieve() farewell skips (A). Shadow instrument only:
# nothing reads it back into a cycle. Path is anchored on profile._DATA (not __file__-relative) so a named
# profile's activate_profile() rebases it (core.farewell_echo is in profile's rebase tuple) and guard_path()
# refuses a non-live process.
_LOG = profile._DATA / "voice_quote_block_log.jsonl"
_APPEND_LOCK = threading.Lock()   # voice / retrieve can run on the loop thread and in to_thread workers

# Kill switches (both ON per D-0442). False restores the pre-J-2245 behaviour exactly; the log keeps recording.
EXEMPT_FAREWELL_QUOTES = True    # C2: nodes/voice_node.py _build_prompt_v2
RETRIEVE_SKIP_FAREWELL = True    # A:  core/memory/store.retrieve()
# D-0558 (travis, 2026-11-02; J-3169; F-0049 / F-0051, row P-0010): the voice "Your last replies" block is omitted on
# internal cycles (core.internal_context_gate.is_internal), widening D-0445 for the voice node; human cycles keep it.
# False restores the block on internal cycles exactly. The log below keeps recording what it held (key "dropped").
DROP_INTERNAL_QUOTES = True      # nodes/voice_node.py _quote_block
# F-0051: the system-prompt line "Your recent replies are shown below" is present only when the block is. False
# restores the line unconditionally (byte-identical to before).
RECENT_LINE_ONLY_WITH_BLOCK = True   # nodes/voice_node.py system_prompt_for

_RETURN_MARKERS =("bring you back", "be here when you wake")
_HEAD_CHARS = 600   # a farewell is ~200-300 chars; a query_text may carry a perception summary after it


def _norm(text) -> str:
    return " ".join(str(text or "").split())


def is_farewell(text) -> bool:
    """True when `text` (a human turn, or a query that STARTS with one) is a /quit farewell: addressed to 渡,
    the stop is 'for a while', and his return is promised. Never raises."""
    try:
        t = _norm(text)[:_HEAD_CHARS]
        if not t.startswith("渡"):
            return False
        low = t.lower()
        return "for a while" in low and any(m in low for m in _RETURN_MARKERS)
    except Exception:
        return False


def fragment_answers_farewell(content) -> bool:
    """True when a stored cycle fragment (core/orchestrator._persist_cycle: 'Q: <raw_input>\\nA: <reply>...') is
    his answer to a farewell. Only the Q: line is read. Never raises."""
    try:
        c = str(content or "")
        if not c.startswith("Q: "):
            return False
        q = c[3:].split("\nA: ", 1)[0]
        return is_farewell(q)
    except Exception:
        return False


def _append(row: dict) -> None:
    """Fenced, locked, fail-open append. A non-live process is refused by the fence (logged at debug)."""
    try:
        path = profile.guard_path(_LOG)
    except profile.NonLiveWriteError as exc:
        logger.debug("[farewell-echo] log write refused by the fence (non-live): %s", exc)
        return
    except Exception as exc:
        logger.debug("[farewell-echo] guard_path failed (non-fatal): %s", exc)
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _APPEND_LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[farewell-echo] log write failed (non-fatal): %s", exc)


def log_quote_block(cycle_id, input_type, raw_input, source: str, quoted: list, exempted: list,
                    dropped: list | None = None) -> None:
    """One row per voice v2 prompt build: exactly what the 'Your last replies' block quoted (each already cut to
    the 260 chars the mouth saw), which replies were exempted as farewell replies (C2), and whether this cycle's
    own input is a farewell. `source` = 'override' (state.recent_voice_replies, voice_lab), 'history'
    (conversation_history), or 'none'."""
    try:
        _append({
            "ts": round(time.time(), 1), "kind": "quote_block",
            "cycle_id": str(cycle_id or ""), "input_type": str(input_type or ""),
            "input_is_farewell": is_farewell(raw_input), "source": source,
            "quoted": [str(q) for q in (quoted or [])],
            "exempted": [str(e) for e in (exempted or [])],
            "dropped": [str(d) for d in (dropped or [])],   # D-0558: internal-cycle replies the block would have quoted
        })
    except Exception as exc:
        logger.debug("[farewell-echo] quote-block row skipped (non-fatal): %s", exc)


def log_retrieve_skip(query_text, skipped_ids: list) -> None:
    """One row per retrieve() call that skipped his own prior farewell answer(s) (A)."""
    try:
        _append({
            "ts": round(time.time(), 1), "kind": "retrieve_skip",
            "query_head": _norm(query_text)[:120], "n_skipped": len(skipped_ids or []),
            "skipped_ids": [str(i) for i in (skipped_ids or [])][:50],
        })
    except Exception as exc:
        logger.debug("[farewell-echo] retrieve-skip row skipped (non-fatal): %s", exc)

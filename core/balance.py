"""
Nascence — Balance (the reading-remediation gate, 2026-06-15)
============================================================
Du is structurally shadow/imagination-dominant: reality has no internal force (external-only) and the
self-lanes pull ~unanimously self-ward (see scripts/lane_forces.py). The counter-force is READING (reality
mass) + PLAY (light). This module is the LEDGER that gates a remediation SPRINT: while either axis is far
from balance, idle defaults to streaming books; when both reach ~50%, the sprint ends and normal life resumes.

Two axes, two shares:
  reality_share = world-origin memory / (world + self) memory      (reality ↔ imagination)
  light_share   = light_events / (light + shadow events)           (light ↔ dark)
                  — VERDICT sources only on both sides since D-0142 (2026-09-03): one verdict per
                  thought, see _LIGHT_VERDICT / _SHADOW_VERDICT below.
"about 50% of each" (Travis) → TARGET 0.5, with hysteresis so the sprint doesn't flap at the line.
Read-only; pure counts; no LLM.

WINDOWED (2026-08-16, founder-approved): shares are computed over a rolling WINDOW_DAYS window, not
all-time. The all-time integral never forgets — the Aug-15 restore of ~5,650 June self-fragments
(cold, invisible to recall, zero pull on live cognition) dropped the all-time ratio below REENTER_AT
and the sprint demanded ~5,000 readings as penance for an archival event (196 readings/h, thinking
crowded to 0.7x, 11 sleeps/day). The window measures what balance was always meant to measure — his
ongoing DIET — and is immune by construction to restores (old timestamps fall outside), to the
prune's asymmetric cold-demotion, and to any future archival event.
"""
from __future__ import annotations
import sqlite3
import time
from pathlib import Path

_DB = Path(__file__).parent.parent / "data" / "memory" / "nascence.db"

TARGET      = 0.50    # "about 50% of each"
EXIT_AT     = 0.47    # reach this to END the sprint (just under 50, so it's attainable)
REENTER_AT  = 0.42    # fall below this to RE-START it (hysteresis band, no flapping)
WINDOW_DAYS = 7.0     # the diet window — recent enough to react, wide enough to smooth a slow day

_WORLD = ("reading", "study", "research", "understanding", "essay")
_SELF  = ("inner_thought", "dream", "subconscious_synthesis", "lived",
          "active_imagination", "consolidation", "session_summary", "chapter")

# ONE CURRENCY (D-0142, 2026-09-03; F-0755). Shadow mints at most ONE event per thought (an unresolved
# thought, novelty-gated). After 06-15/16 light minted up to FOUR per thought — deliberation's
# integration crossing on every grounded thought, the play point on the joy clock (F-0749), the
# resolved-thought event, reading/study crossings — so the share climbed 0.50 → 0.74 while, in the
# currency the ledger was built in (one verdict per thought), he sat at ~0.45. Today 501 of 967
# thoughts stood on BOTH sides with identical text. The ledger now counts only the per-thought
# VERDICT sources on each side; play/integration/reading light events stay in the store, where T4's
# crossing retrieval and the climate's integration momentum still read them (their own currency
# question is D-0142's defeater, not this fix).
_LIGHT_VERDICT  = ("resolved_thought", "resolved_complexity", "resolved_dream")
_SHADOW_VERDICT = ("unresolved_thought", "unresolved_dream", "unresolved_dream_rest", "critic_rejection", "prediction_error")

# module-level latches (hysteresis across calls)
_sprinting: bool | None = None   # the overall sprint (either axis below target) — for the gauge
_reading:   bool | None = None   # the READING gate specifically (reality below target) — axis-aware


def _count(conn, table: str, where: str = "", args: tuple = (), fail: list | None = None) -> int:
    try:
        return conn.execute(f"SELECT COUNT(*) n FROM {table}{(' WHERE ' + where) if where else ''}",
                            args).fetchone()[0]
    except Exception:
        if fail is not None:       # J-1908: let shares() know this 0 is a failed read, not a real zero (never memoised)
            fail.append(table)
        return 0


# TWO ADDITIVE CUTS to the on-loop cost of shares() (J-1908, F-2540). shares() is four COUNT(*)s; the two over
# memory_fragments (121k rows) took ~250-280 ms EACH because the planner walked idx_origin (every row of the 13
# origins, ~100k) then filtered timestamp: ~535 ms per call, and one idle tick makes SIX calls (idle_allocator.
# _ch_balance_world/_light x2 each, inner_monologue needs_reality, told.ready) = ~3.3 s ON the event loop.
#  (1) `+origin IN (...)` (unary plus: the origin term can no longer use idx_origin) makes the planner range-scan
#      the EXISTING idx_timestamp (the 7-day window is ~3.7k rows) -> ~16 ms per count. Exactly the same rows, no DDL,
#      no staleness; if idx_timestamp were ever absent it just falls back to a scan (no INDEXED BY, nothing to error).
#  (2) a SHORT-TTL MEMO (below): the 7-day window moves by minutes, so the counts cannot meaningfully differ inside
#      one idle tick's back-to-back calls; serve the last real result for SHARES_TTL_S. Bounded staleness, so it is
#      the ONLY part that is not byte-exact per call; SHARES_TTL_S = 0 switches it off.
# Only SUCCESSFUL reads are memoised (a failure still returns the zeros fresh, exactly as before). The memo is
# keyed on everything shares() depends on (db path, window, origin/verdict sets) so a monkeypatched _DB/_WORLD
# or a changed WINDOW_DAYS is a miss, never a stale hit. SHARES_TTL_S <= 0 turns the memo off (= old behaviour).
# The hysteresis latches (_sprinting, _reading) are untouched: they still update on every call, on the memo'd values.
SHARES_TTL_S = 10.0
_shares_memo: tuple | None = None    # (monotonic_ts, key, result_dict)


def _shares_key() -> tuple:
    return (str(_DB), WINDOW_DAYS, _WORLD, _SELF, _LIGHT_VERDICT, _SHADOW_VERDICT)


def invalidate_shares_cache() -> None:
    """Drop the memo (tests / a caller that just wrote many fragments and wants a fresh read)."""
    global _shares_memo
    _shares_memo = None


def shares() -> dict:
    """Current reality_share and light_share (each 0..1) over the rolling WINDOW_DAYS diet window.
    Best-effort -> zeros. Memoised for SHARES_TTL_S seconds (see above); always returns a fresh dict."""
    global _shares_memo
    ttl = SHARES_TTL_S
    if ttl and ttl > 0:
        m = _shares_memo
        if m is not None and (time.monotonic() - m[0]) < ttl and m[1] == _shares_key():
            return dict(m[2])
        key = _shares_key()
        res, ok = _shares_uncached()
        if ok:
            _shares_memo = (time.monotonic(), key, dict(res))
        return res
    return _shares_uncached()[0]


def _shares_uncached() -> tuple[dict, bool]:
    """The real read: (result, ok). ok False = the best-effort zeros fallback, or any one count that failed and
    fell back to 0 (a locked DB / missing table) -- never memoised, so a transient failure costs one call, not a TTL."""
    try:
        cutoff = time.time() - WINDOW_DAYS * 86400
        failed: list = []
        with sqlite3.connect(_DB) as conn:
            wph = ",".join("?" * len(_WORLD)); sph = ",".join("?" * len(_SELF))
            world = _count(conn, "memory_fragments",
                           f"+origin IN ({wph}) AND timestamp >= ?", _WORLD + (cutoff,), failed)
            self_ = _count(conn, "memory_fragments",
                           f"+origin IN ({sph}) AND timestamp >= ?", _SELF + (cutoff,), failed)
            lph = ",".join("?" * len(_LIGHT_VERDICT)); shph = ",".join("?" * len(_SHADOW_VERDICT))
            light = _count(conn, "light_events",
                           f"source IN ({lph}) AND timestamp >= ?", _LIGHT_VERDICT + (cutoff,), failed)
            shadow = _count(conn, "shadow_events",
                            f"source IN ({shph}) AND timestamp >= ?", _SHADOW_VERDICT + (cutoff,), failed)
        reality_share = world / max(1, world + self_)
        light_share   = light / max(1, light + shadow)
        return ({"reality_share": reality_share, "light_share": light_share,
                 "world": world, "self": self_, "light": light, "shadow": shadow}, not failed)
    except Exception:
        return ({"reality_share": 0.0, "light_share": 0.0, "world": 0, "self": 0, "light": 0, "shadow": 0}, False)


def in_remediation() -> bool:
    """Is the reading-remediation sprint ON? Hysteresis: starts when either axis is below REENTER_AT,
    ends only when BOTH reach EXIT_AT — so a single axis crossing 50% doesn't stop the sprint early."""
    global _sprinting
    s = shares()
    r, l = s["reality_share"], s["light_share"]
    both_balanced = (r >= EXIT_AT and l >= EXIT_AT)
    either_low    = (r < REENTER_AT or l < REENTER_AT)
    if _sprinting is None:
        _sprinting = not both_balanced       # first call: sprint unless already balanced
    elif both_balanced:
        _sprinting = False
    elif either_low:
        _sprinting = True
    return _sprinting


def needs_reality() -> bool:
    """AXIS-AWARE (2026-06-16): is the READING stream still needed? Reading is the REALITY counter-force —
    once reality is balanced it does little for the LIGHT axis, so the stream should STOP and the freed idle
    go to light-generation (play, deliberation crossings, curiosity). Hysteresis on reality_share alone."""
    global _reading
    r = shares()["reality_share"]
    if _reading is None:
        _reading = r < EXIT_AT
    elif r >= EXIT_AT:
        _reading = False
    elif r < REENTER_AT:
        _reading = True
    return _reading


def needs_light() -> bool:
    """Reality is balanced but light is not — pour idle into light-generation, not more reading."""
    s = shares()
    return (not needs_reality()) and s["light_share"] < EXIT_AT


def status() -> dict:
    s = shares()
    s["remediating"] = in_remediation()
    s["needs_reality"] = needs_reality()
    s["needs_light"] = needs_light()
    return s

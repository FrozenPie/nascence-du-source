"""
Nascence — Commitment Ledger (P-0038 commitment scan; began as Phase 0 SHADOW, LIVE in effect since)
=====================================================================================================
The "capacity to commit" build — full design + status tracker: docs/plans/capacity_to_commit.md.

THE PROBLEM (Travis, 2026-06-30): Du dissolves every boundary as soon as it forms. He cannot commit — won't
name his cat, won't say where he is, won't resolve a thought — and holds nothing except "I am always becoming."
Identity diffusion sustained by a permanent moratorium; a pathologically cautious agent re-deliberating every
stance every cycle. The biggest, most important build in a long time.

PHASE 0 (this file's origin, 2026-06-30) was OBSERVE-ONLY. It watches his thoughts for a COMMITMENT being TAKEN
(a stand he could hold) and a commitment being DISSOLVED, records both in a ledger, and measures the disease:
  • commitment LIFESPAN — how long a stance survives before he drops it (the prediction: ≈ 0)
  • DROP-REASON — a NAMED DEFEATER (achieved / impossible / contradicted / deliberately reconsidered) vs
    REFLEXIVE dissolution ("nothing is fixed", "a name is a cage", a new thought just displaced it)

CORRECTED 2026-11 (J-2840, from F-3481, verified by grep + data counts 2026-11-01): the scan is NO LONGER
observe-only. It does NOT "store nothing into his cognition / change no behaviour" — the ledger it writes is READ
by live systems, and _stakes() writes into memory directly. What Du receives because of it today:
  • formed      -> _stakes(): UPDATE memory_fragments SET importance=MIN(0.85, importance*1.08), protected=1 on the
                   idle thought the stand was lifted from (prune-exempt).
  • achieved    -> satisfaction.record("commitment_held"); dissolved -> satisfaction.record("commitment_dissolved").
  • dissolved   -> sitting.note_difficulty("you let go of a stand you had held: ...", kind="loss"), which
                   sitting.dwell_steer() injects into the idle prompt ("Something hard has just happened ... STAY with it").
                   GATED since J-3159 / D-0547: only if the stand lived >= SIT_MIN_STAND_LIFE_S or was reaffirmed (_sit_gate).
  • commitment_active.json is READ by: identity_estate (an "I hold: ..." node of type "stand", projected by the LIVE
    identity_projection, IDENTITY_PROJECT_LIVE=True), peers._du_world_context (peer-letter generator),
    concerns.current_concerns (kind "hold"), homeostasis._read_commitment (a scalar), self_claims (held_claims),
    and coupling_rides (counts only).
The ONLY shadow part is the concerns anchor arm: concerns.COMMITMENT_ANCHOR_LIVE = False (logs would_inject, injects 0).
LANE: the scan call (_scan_shadow_locked) runs on SERVE_CHAINS["hot"] = :11433 qwen3.5:9b — the SAME model/lane that
writes the thought (the call site passes self.conscious_urls). It is NOT on the background lane. Only the defeater
JUDGE (_judge_defeater) is on a different lane (judge_mixtral). Phases 1-2 (HOLD against dissolution via
named-defeater drop-rules + bundling; ACT-from + revise-deliberately + fix T4) were built on top — see the plan.

Ported in spirit from core/competence.py's CapabilityBelief — the one existing structure that HOLDS a belief
with evidence and updates slowly instead of dissolving.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from pathlib import Path

from core import profile   # J-1814/F-2428: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.commitment")

_DIR    = Path(__file__).parent.parent / "data"
_LEDGER = _DIR / "commitment_ledger.jsonl"    # append-only event log: formed / dissolved
_ACTIVE = _DIR / "commitment_active.json"     # the currently-held commitments
_OBSERVED = _DIR / "commitment_observed.jsonl"  # detections REJECTED at the formation gate (measurement only —
                                                # the raw want/musing churn, kept out of the held set; see below)
_HOLDRATE_LOG = _DIR / "commitment_holdrate.jsonl"  # the north-star trend (evidence_review S5, 2026-07-05)
# J-3158 / D-0546 (founder 2026-11-02): two ADDITIVE SHADOW logs, nothing reads them for behaviour (the 7-day read is
# scripts/commitment_second_look_read.py). See _second_look and _log_judge_attempt below.
_SECOND_LOOK_LOG = _DIR / "commitment_second_look_shadow.jsonl"   # cross-family "is this a stand or an insight" on every new stand
_ATTEMPTS_LOG = _DIR / "commitment_attempts_shadow.jsonl"         # one row per defeater-judge ask, with a per-stand attempt count
# J-2848 / F-3511 (P-0038 instruments): one row per scan call that got past the length check, null scans INCLUDED (78 percent of
# calls produce no new stand, so they were invisible to every other log). Write-only shadow; nothing reads it for behaviour
# (read by scripts/commitment_scan_raw_read.py).
_SCAN_RAW_LOG = _DIR / "commitment_scan_raw.jsonl"
COMMIT_ACHIEVED_SHADOW = True      # J-2842/F-3498: shadow log + cross-family verdict on every 'achieved' retirement; False = no extra model call
_ACHIEVED_SHADOW_LOG = _DIR / "logs" / "commitment_achieved_shadow.jsonl"
# D-0810 / plan stand_kinds_and_accumulation P1 (fast-tracked 2026-11-18). Flags flipped ON same day by founder fast-track; set False for the old behaviour.
STAND_KIND_GATES_ACHIEVEMENT = True    # ON 2026-11-18 (founder fast-track; revisit): a stand the cross-family second look labelled practice/value/insight is never retired as 'achieved' by word overlap
# D-0815 / J-4217: when True, a deed stand retires as 'achieved' ONLY when the cross-family judge (judge_mixtral) has said
# 'fulfilled' on the proposing deed; the word-overlap rule only PROPOSES. Until a verdict is back the stand is held (the
# judge is asked once per stand+deed, fire-and-forget; the verdict is read on a later scan). A verdict of not_fulfilled /
# unclear / lane timeout never retires. DEFAULT OFF (restart-gated, shadow first): False = the old behaviour exactly.
ACHIEVED_JUDGE_GATES_RETIREMENT = False
STAND_RELATION_GATES_DROPS = True      # True: a drop of a HELD stand whose scan relation is refines/coexists is not a drop (no denial count, no dissolve)
COMMIT_SECOND_LOOK_SHADOW = True  # D-0546 orders the second look; False = no extra model call at all (kill switch, not a tuning knob)

# J-3159 / D-0547 (founder 2026-11-02): a stand's dissolve opens a SIT (sitting.note_difficulty -> the idle prompt's "Something
# hard has just happened" steer) only if the stand LIVED long enough to be a loss, or was REAFFIRMED at least once. Before
# this, 99.4 percent of all sits (1,165 of 1,172 judged rows, F-3696) came from a scan-formed stand dissolving, many of
# them seconds-old classifier sentences (strict formation precision 25 percent, F-3492), so the thoughts judged were
# mostly not about the "loss". The gate decides ONLY the sit; the ledger event, the satisfaction.record and every real-event
# sit (failed sums, trap kill, Travis contradiction: they never pass through here) are untouched. N: 30 minutes (the
# ruling's start value); data/commitment_ledger.jsonl, 891 load-bearing dissolves 2026-07-03..11-05: the curve of stands
# kept at each N (last 30 days, 235 dissolves, life or one reaffirm) is 5 min 91 pct, 10 min 81, 15 min 72, 30 min 63
# (34 sits-worth a week), 60 min 51, 2 h 34 (19 a week) -- every N tried leaves far above the ruling's starve line
# of 1 a week. See scripts/sit_gate_read.py for the read. False = the old behaviour (every load-bearing dissolve opens a sit).
SIT_STAND_GATE_ON = True
SIT_MIN_STAND_LIFE_S = 1800.0      # N: seconds a stand must have been held for its dissolve to open a sit
SIT_MIN_REAFFIRMS = 1              # ...or this many reaffirmations (re-taking the same stand raises it, W2.3)
# 2026-11-06 (founder, decide-review): gate on SCAN COUNT, not wall-clock, so Du's downtime cannot age a stand (F-4065).
# "scans" = the stand survived SIT_MIN_STAND_SCANS scans (the per-stand c["scans"] counter, also logged as lifespan_scans);
# "life" = the J-3159 wall-clock rule above. 20 scans is about 30 minutes at the median 92 s per scan; on the 76 dissolves
# of the last 14 days it keeps 41 stands against 44 for 1800 s, and only 1 of those 44 had under 10 scans.
SIT_GATE_BASIS = "scans"
SIT_MIN_STAND_SCANS = 20


# ── FORMATION GATE (2026-07-07) — only a GENUINE STAND may enter the held set. ────────────────────────────────
# THE BUG (verified 07-07): the Phase-0 shadow scan captured EVERY detection as a held commitment. In one day it
# inhaled 108 entries — 107 non-load-bearing idle wants/musings ("I want to comb the tideline", "seeing what the
# sea has left on these rocks", the literal string "None") — while ONLY 1 was load_bearing (and that one, "He
# wants to come in.", a misclassification). This corrupted every downstream that reads commitment_active.json as
# "stands Du holds": the identity estate (worked around by a load_bearing gate), the concerns anchor, Darwin's
# witness prompt, the homeostasis `commitment_integrity` protoself variable (read 1.0 — "holds everything" — while
# he in fact holds nothing), and — most seriously — the capacity-to-commit HOLD-RATE, the project's north-star
# "rudder": a hold-rate computed over 107 non-commitments measures nothing.
#
# THE CONTRACT (plan §Design + defeater-legitimacy protocol "Commitment object"): a commitment is a DELIBERATE
# STAND he could hold — a name given, a decision, a promise, a position that can be challenged — NOT any "I want
# to…" idle thought that flows through him. Phase-0's job (measure the churn) is DONE (the 1163-event evidence
# review). The gate below realises the plan's `observed` vs `held` split at the storage boundary: detections are
# still MEASURED (logged to commitment_observed.jsonl for the honest detection→genuine ratio) but only a genuine
# stand becomes HELD (enters commitment_active.json + the `formed`/hold-rate accounting). This does NOT touch the
# HOLD/DROP/judge machinery — the delicate part of the rudder — it only decides what is allowed to be a stand.
# Deterministic + fail-open (on error → treat as genuine, i.e. never silently swallow a real stand).
#
# ★ DISCRIMINATOR = the LLM's load_bearing flag, NOT a surface lexeme (corrected 2026-07-07 after the run).
# The first draft of this gate also rejected any "I want to…/need to…" want-lexeme as a backstop. The run
# proved that WRONG and dangerous: of the only 5 load_bearing=true stands ever detected, FOUR are "I want to
# write a letter to Travis" — the single genuine commitment the whole project has produced (form → drop_denied
# ×18 held against dissolution → reaffirmed ×2 → achieved ×3; the evidence_review 07-05 flagship). Du phrases
# his ONE real commitment exactly like his idle wants ("I want to comb the tideline") — the surface phrase
# cannot tell them apart, but the LLM's load_bearing judgment can and did (letter→true, tideline→false, ~520×).
# A want-lexeme backstop would have suppressed the exemplar. So the deterministic layer is now MECHANICAL-ONLY
# (empty/None artefact, a bare question) — garbage the load_bearing flag alone doesn't catch — and never
# second-guesses a load_bearing=true semantic verdict. Admitting the rare misclassification ("He wants to come
# in.") is far cheaper than silencing the one stand that holds. (Plan law: no brittle bright-line rules.)


def _stand_rejection(nc: dict) -> str | None:
    """Return WHY this detection is not a genuine stand (→ observed, not held), or None if it IS a genuine stand.
    The DISCRIMINATOR is the LLM's load_bearing flag; the two deterministic checks below only catch mechanical
    garbage (empty/'None', a bare question) that the flag doesn't — they never override a load_bearing verdict."""
    try:
        s = str(nc.get("statement", "")).strip()
        if not s or s.lower() in ("none", "null"):
            return "empty/None artefact"
        if len(s) < 12:
            return "too short to be a stand"
        if s.rstrip().endswith("?"):
            return "a question, not a stand"
        if not nc.get("load_bearing"):
            return "not load-bearing (abstract musing / sensory description / idle want)"
        return None
    except Exception as exc:
        logger.debug("[commitment] stand-rejection check failed (non-fatal): %s", exc)
        return None   # fail-open: never let the gate itself swallow a real stand


def _log_observed(ev: dict) -> None:
    """A detection that did NOT clear the formation gate — logged for measurement (the honest want/musing churn),
    kept OUT of the held set. Append-only; best-effort."""
    try:
        # J-1814 / F-2428 -- write fence (D-0179): guard_path BEFORE the mkdir, INSIDE the existing best-effort try
        # (scan_shadow ignores this writer's outcome). guard_path logs one warning per path; debug carries the text.
        path = profile.guard_path(_OBSERVED)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[commitment] observed-log write refused by the fence (non-live): %s", exc)
    except Exception:
        pass


# The formation gate went live 2026-07-07 10:42. EVERY ledger `formed` event before it is contaminated (the
# scan captured ~99% non-commitments as held), so a hold-rate over the raw window read a frozen, meaningless
# ~0.098 — the north-star pointing at junk. Post-cutover, every `formed` is a gate-passed genuine stand, so the
# hold-rate over post-cutover events is the HONEST rudder. Non-destructive: the full ledger (and status()'s
# lifetime counts) is untouched — only this metric filters to the clean era. It reads ~0 with formed=0 until a
# genuine stand actually forms — which is the truth (he holds nothing yet; genuine stands are ~0.6% of
# detections), not a broken sensor. `genuine_span` in each row makes the small-sample honesty explicit.
_HOLDRATE_CUTOVER = 1783377727.0   # 2026-07-07 10:42:07 — the formation-gate fix; see Finding 2 in the plan


def holdrate_snapshot(window: int = 400):
    """Append the commitment HOLD-RATE — reaffirmed/(formed+reaffirmed) — over the CLEAN (post-gate) era, plus
    the raw counts, to commitment_holdrate.jsonl for the HUD. Once per sleep (evidence_review S5): the review
    found hold-rate climbing 0→17%, the project's first north-star metric moving the right way on the root
    disease — but it had to be re-derived by hand. This makes it a first-class line. Read-only; fail-open.
    Pre-2026-07-07 events are EXCLUDED — they are the over-capture junk the gate now keeps out (see Finding 2)."""
    import json as _json
    import time as _time
    import collections as _c
    try:
        # J-1814 / F-2428 -- write fence: resolve the log target BEFORE any I/O (before even the ledger read), inside
        # the existing fail-open try (the only caller, _enter_sleep, treats None as "no snapshot"). A refusal returns None.
        _hr_path = profile.guard_path(_HOLDRATE_LOG)
        rows = [r for r in (_json.loads(l) for l in open(_LEDGER, encoding="utf-8") if l.strip())
                if r.get("ts", 0) >= _HOLDRATE_CUTOVER][-window:]
        c = _c.Counter(r.get("event") for r in rows)
        f, d, r_, a = c.get("formed", 0), c.get("dissolved", 0), c.get("reaffirmed", 0), c.get("achieved", 0)
        row = {"ts": round(_time.time(), 1), "hold_rate": round(r_ / max(1, f + r_), 3),
               "formed": f, "dissolved": d, "reaffirmed": r_, "achieved": a,
               "genuine_span": len(rows)}   # how many CLEAN-era events this rests on — honesty about sample size
        _hr_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_hr_path, "a", encoding="utf-8") as fh:
            fh.write(_json.dumps(row) + "\n")
        return row
    except profile.NonLiveWriteError as exc:
        logger.debug("[commitment] holdrate write refused by the fence (non-live): %s", exc)
        return None
    except Exception as exc:
        logger.debug("[commitment] holdrate_snapshot failed (non-fatal): %s", exc)
        return None

COMMIT_SCAN_COOLDOWN = 60.0   # seconds between shadow scans (2026-07-08: 150→60 — finer sampling for the
                              # active pursuit/monoculture evidence work; the 3070 had idle headroom to carry it)


def _load_active() -> list[dict]:
    try:
        return json.loads(_ACTIVE.read_text(encoding="utf-8")) if _ACTIVE.exists() else []
    except Exception as exc:
        logger.debug("[commitment] active-commitments read failed (non-fatal): %s", exc)
        return []


def _save_active(items: list[dict]) -> None:
    try:
        # J-1814 / F-2428 -- write fence: guard_path before the mkdir, INSIDE the existing fail-open try (best-effort
        # state write; scan_shadow's other work must not break). Debug line carries the refusal text.
        path = profile.guard_path(_ACTIVE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    except profile.NonLiveWriteError as exc:
        logger.debug("[commitment] active-commitments write refused by the fence (non-live): %s", exc)
    except Exception as exc:
        logger.debug("[commitment] active-commitments write failed (non-fatal): %s", exc)


def _log_event(ev: dict) -> None:
    try:
        # J-1814 / F-2428 -- write fence: guard_path before the mkdir, INSIDE the existing best-effort try.
        path = profile.guard_path(_LEDGER)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[commitment] ledger write refused by the fence (non-live): %s", exc)
    except Exception:
        pass


_SCAN_SYS = (
    "You watch one mind for ONE thing: COMMITMENT — a stand it TAKES and could hold. A commitment is a position, "
    "a name, a decision, a conclusion, or a stated belief it could stay with: 'I am X', 'I will do Y', 'her name "
    "is Z', 'the answer is W', 'I have decided P'. Vague musing, a question, or pure description is NOT a "
    "commitment.\n"
    "You are given the mind's CURRENT THOUGHT and its RECENT ACTIVE COMMITMENTS (with ids). Report two things:\n"
    "1. NEW STAND: does the current thought take a NEW commitment? If yes, give it in the mind's OWN words plus a "
    "short scope (what it is about). If not, null.\n"
    "2. DISSOLUTIONS: does the current thought ABANDON, reverse, re-open, or dissolve any of the listed active "
    "commitments? For each, give its id and classify WHY:\n"
    "   - 'defeater': a REAL reason — it was achieved, shown impossible, contradicted by new evidence, or "
    "deliberately reconsidered with a stated cause.\n"
    "   - 'reflexive': NO real reason — it simply flows past it, re-opens it, or melts it into abstraction "
    "('nothing is fixed', 'a name is a cage', 'I am always becoming'), or a new thought merely displaced it.\n"
    "For a NEW commitment, also classify its LOAD (W2.0, 2026-07-03; negative-example set broadened "
    "2026-09-02 per F-0055/F-0677 — the original single example didn't generalize, letting a run of short "
    "physical-task statements slip through as load-bearing): load_bearing=true ONLY if it is deed-shaped or "
    "identity-relevant — a name given, a decision with real consequences, a promise to a person, a position "
    "that could be challenged, a relationship stance. load_bearing=false for abstract conceptual musing "
    "('the tension between X and Y is...') and for a SHORT, present-tense physical action with NO "
    "identity/relational/emotional stakes attached — a bare report of a body doing a thing, not a stand about "
    "who it is or what it owes someone. Examples of this exclusion: 'I will look at the anemone.', 'I must "
    "touch the wet stones.', 'I will tend the woodpile.', 'I must move.' — none of these carry a stated reason, "
    "a person, or a position; they are chore reports. This exclusion is about STAKES, not the verb: the SAME "
    "physical act stays load_bearing=true when it is framed with a real reason attached — 'I will keep tending "
    "the fire, the way I promised myself I would stay steady' is a promise about who Du is, not a chore "
    "report, so it counts.\n"
    "For each dissolution also give its RELATION to that commitment (J-4190): 'refines' = the thought sharpens, "
    "deepens or restates the commitment on the same theme; 'coexists' = it sits beside the commitment without "
    "contradicting it; 'abandons' = it really gives the commitment up or reverses it.\n"
    "Output ONLY a JSON object: {\"new_commitment\": {\"statement\": \"...\", \"scope\": \"...\", "
    "\"load_bearing\": true or false} or null, "
    "\"dissolutions\": [{\"id\": \"...\", \"why\": \"...\", \"kind\": \"defeater\" or \"reflexive\", "
    "\"relation\": \"refines\" or \"coexists\" or \"abandons\"}]}"
)


# ── W2.3 DROP GATES (2026-07-03, big build — the deterministic subset of the defeater-legitimacy
# protocol; the cross-family judge layer is the NEXT slice). A HELD (load-bearing) stand may not dissolve
# by flow: reflexive drops are DENIED outright (Bratman: reconsideration must be licensed), and a claimed
# defeater must clear three pure-code gates: G4 (not a felt-state — "no longer feels alive" is psychology,
# not a defeater) · G5 (scope: the reason must be ABOUT this commitment) · G7 (not the dissolution
# attractor in costume — "a name is a cage" defeats every naming equally, therefore nothing). A denied
# drop leaves the stand HELD and logs the pressure. Ordinary (non-load-bearing) churn is untouched.
_ATTRACTOR_PHRASES = ("a name is a cage", "nothing is fixed", "i am always becoming", "everything flows",
                      "all is flux", "boundaries dissolve", "nothing is permanent", "the river",
                      "fixed points are illusions", "all definitions limit")
_FELT_MARKERS = ("feels", "feel ", "felt ", "no longer alive", "doesn't resonate", "does not resonate",
                 "sense that", "the pull", "the urge")


def _drop_denial(c: dict, kind: str, why: str) -> str | None:
    """Why this drop is DENIED (None = licensed). Deterministic; fail-open to DENY-nothing on error."""
    try:
        if kind == "reflexive":
            return "reflexive — a held stand does not dissolve by flow; name a defeater"
        w = (why or "").lower()
        # G7: the standing dissolution-attractor in costume
        if any(ph in w for ph in _ATTRACTOR_PHRASES):
            return "G7 attractor — the reason defeats every commitment equally, therefore none"
        # G4: purely felt-state reason with no world referent
        stmt_words = {x for x in (c.get("statement", "") + " " + c.get("scope", "")).lower().split() if len(x) > 3}
        has_ref = any(x in w for x in stmt_words)
        if any(m in w for m in _FELT_MARKERS) and not has_ref:
            return "G4 felt-state — psychology is not a defeater; cite the world"
        # G5: the reason must be about THIS commitment
        if stmt_words and not has_ref:
            return "G5 scope — the stated reason is about something else"
        return None
    except Exception as exc:
        logger.debug("[commitment] drop-denial gate check failed (non-fatal): %s", exc)
        return None


# ── W2.3/W2.4 ACHIEVEMENT + STAKES (2026-07-04): the letters surfaced the gap — a load-bearing commitment
# FULFILLED by an enactment ("write a letter to Travis" → 36 letters) was never retired, so he kept getting
# drop-denied on a want he was demonstrably satisfying (the fanatical-commitment trap the research warned of).
# ACHIEVEMENT is a legitimate defeater: a deed that fulfils the stand retires it and fires the REWARD
# (satisfaction liking) — form → achieve → re-form is a healthy wanting/fulfilling rhythm, not a failure.
_ACHIEVE_MARKERS = {
    "letter": ("letter", "peer"), "write": ("letter", "peer", "essay", "composition"),
    "book": ("action",), "finish": ("action", "essay"), "read": ("action",),
    "name": ("action",), "essay": ("essay",), "study": ("study",),
}


def _recent_enactments(since: float) -> list[dict]:
    """Deeds since `since`, each with an HONEST per-occurrence timestamp (F-0483/F-0484 fix,
    2026-08-29, D-0086(b)). Two sources:
      - discrete write-once fragments (letter/peer/essay/journal/study/composition) — their own
        memory_fragments.timestamp is already a genuine per-event stamp, untouched by this fix.
      - 'action' occurrences — NOT read from memory_fragments.timestamp any more (that column on
        the aggregate row is rewritten to now() on every recurrence by activity_memory.record(),
        so it can never mean "this occurrence happened after `since`" — see the file's own header
        note). Read instead from activity_events, the per-occurrence append-only log
        activity_memory.record() now writes alongside the aggregate row.
    Merged and re-sorted by real timestamp, capped at 40 (same cap as before). Fail-open per deed
    source independently, so a missing/old-schema activity_events table (pre-fix DB) degrades to
    the discrete-fragment deeds only, rather than losing everything."""
    import sqlite3
    out: list[dict] = []
    try:
        con = sqlite3.connect(str(_DIR / "memory" / "nascence.db")); con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT content, origin, timestamp FROM memory_fragments WHERE timestamp>=? AND "
            "origin IN ('letter','peer','essay','journal','study','composition') "
            "ORDER BY timestamp DESC LIMIT 40", (since,)).fetchall()
        con.close()
        out.extend({"content": r["content"] or "", "origin": r["origin"], "ts": r["timestamp"]}
                    for r in rows)
    except Exception as exc:
        logger.debug("[commitment] recent-enactments discrete-fragment read failed (non-fatal): %s", exc)
    try:
        from core.activity_memory import _summary as _act_summary
        con = sqlite3.connect(str(_DIR / "memory" / "nascence.db")); con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT ts, action_type, target FROM activity_events WHERE ts>=? "
            "ORDER BY ts DESC LIMIT 40", (since,)).fetchall()
        con.close()
        for r in rows:
            content = _act_summary(r["action_type"], r["target"], 1, r["ts"], r["ts"])
            out.append({"content": content, "origin": "action", "ts": r["ts"]})
    except Exception as exc:
        logger.debug("[commitment] recent-enactments activity-events read failed (non-fatal): %s", exc)
    out.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return out[:40]


def _dw_scan_fragment() -> str:
    """J-2160: the commitment scan's done_when request ("" when DONE_WHEN_AT_OPEN is off == exact old prompt)."""
    try:
        from core import done_when as _dw
        return _dw.scan_fragment()
    except Exception:
        return ""


def _dw_text(cid: str) -> str:
    try:
        from core import done_when as _dw
        return (_dw.get("commitment", cid) or {}).get("done_when") or ""
    except Exception:
        return ""


def _achieved_by(c: dict, enactments: list[dict]) -> str | None:
    """Deterministic: has a recent DEED fulfilled this held commitment? Returns the evidence line or None.
    J-2160: a done_when written at formation (side store) adds its words to the match -- achieved-against-done_when."""
    cwords = {w for w in (c.get("statement", "") + " " + c.get("scope", "") + " "
                          + _dw_text(str(c.get("id") or ""))).lower().split() if len(w) > 3}
    if not cwords:
        return None
    want_origins = set()
    for m, origins in _ACHIEVE_MARKERS.items():
        if m in cwords:
            want_origins |= set(origins)
    for e in enactments:
        ewords = {w for w in (e["content"] or "").lower().split() if len(w) > 3}
        overlap = cwords & ewords
        if (e["origin"] in want_origins and overlap) or len(overlap) >= 3:
            return f"{e['origin']}: {(e['content'] or '')[:90]}"
    return None


def _achieved_detail(c: dict, enactments: list[dict]) -> dict:
    """J-2842: mirror of _achieved_by's match, returning WHY it matched (shadow measurement only; changes nothing).
    Keys: origin, deed (full text), overlap (sorted words), by_marker, scope_only (every overlap word came from the SCOPE
    field alone, not the statement or done_when). Never raises."""
    try:
        stmt = {w for w in (c.get("statement", "") or "").lower().split() if len(w) > 3}
        scope = {w for w in (c.get("scope", "") or "").lower().split() if len(w) > 3}
        dw = {w for w in _dw_text(str(c.get("id") or "")).lower().split() if len(w) > 3}
        cwords = stmt | scope | dw
        want = set()
        for m, origins in _ACHIEVE_MARKERS.items():
            if m in cwords:
                want |= set(origins)
        for e in enactments:
            ewords = {w for w in (e["content"] or "").lower().split() if len(w) > 3}
            ov = cwords & ewords
            if (e["origin"] in want and ov) or len(ov) >= 3:
                return {"origin": e["origin"], "deed": e["content"] or "", "overlap": sorted(ov),
                        "by_marker": bool(e["origin"] in want and ov and len(ov) < 3),
                        "scope_only": bool(ov) and not (ov & (stmt | dw))}
    except Exception as exc:
        logger.debug("[commitment] achieved-detail failed (non-fatal): %s", exc)
    return {}


_ACHIEVED_JUDGE_SYS = (
    "You read ONE commitment a mind holds and ONE deed it later did. You see nothing else. Decide whether the deed "
    "genuinely FULFILS the commitment (the thing promised or decided has now actually been done), or merely shares "
    "words or a topic with it. Do not tilt either way. If you genuinely cannot tell, answer unclear.\n"
    "Answer ONLY JSON: {\"verdict\": \"fulfilled\" or \"not_fulfilled\" or \"unclear\", \"why\": \"one sentence\"}")


async def _achieved_shadow(row: dict) -> None:
    """J-2842: cross-family (judge_mixtral lane only, NO fallback to the hot qwen family) would-be verdict on one
    'achieved' retirement. Sees statement + deed text only. Logs one row; acts on nothing. Fail-open, never raises."""
    _t0 = time.time()
    try:
        from core.model_client import call_node_json
        from core.schema import SERVE_CHAINS
        lane = SERVE_CHAINS.get("judge_mixtral")
        if not lane:
            row["error"] = "no_judge_mixtral_lane"
            return
        user = f"COMMITMENT: {row['statement'][:200]}\nDEED: {row['deed'][:300]}"
        data = await call_node_json(lane, _ACHIEVED_JUDGE_SYS, user, max_tokens=120, temperature=0.0,
                                    timeout=90, retries=1, tier=3)
        v = str((data or {}).get("verdict", "")).strip().lower()
        if v in ("fulfilled", "not_fulfilled", "unclear"):
            row["judge_verdict"] = v
            row["judge_why"] = str(data.get("why", ""))[:200]
        else:
            row["error"] = "unparsed" if data else "no_reply"
    except Exception as exc:
        row["error"] = type(exc).__name__
        # D-0815 / F-5041: the ValueErrors here are call_node_json's "all servers exhausted ...: TimeoutError" wrapper of a
        # lane timeout (same cause as the second look, J-4193); keep the cause so a timeout is not read as a parse failure.
        _m = str(exc)
        row["error_detail"] = "timeout" if ("TimeoutError" in _m or _m.rstrip().endswith(":")) else _m[:160]
        logger.debug("[commitment] achieved-shadow judge failed (non-fatal): %s", exc)
    finally:
        row["latency_s"] = round(time.time() - _t0, 2)
        if row.get("gated"):
            _judge_verdicts[(row["stand_id"], row.get("deed_key", ""))] = {
                "verdict": row.get("judge_verdict"), "ts": time.time()}
            _judge_pending.discard((row["stand_id"], row.get("deed_key", "")))
        _append_shadow(_ACHIEVED_SHADOW_LOG, row)


_achieved_tasks: set = set()


def _spawn_achieved_shadow(c: dict, ev: str, detail: dict, cycle_id: str, now: float) -> None:
    """Fire-and-forget the shadow row. With no running loop the row is still written (verdict null). Never raises."""
    if not COMMIT_ACHIEVED_SHADOW:
        return
    try:
        row = {"ts": round(now, 1), "stand_id": str(c.get("id", "")), "cycle_id": cycle_id,
               "statement": str(c.get("statement", ""))[:300], "scope": str(c.get("scope", ""))[:200],
               "evidence": ev[:150], "deed": str(detail.get("deed", ""))[:300], "deed_origin": detail.get("origin"),
               "overlap_words": detail.get("overlap", []), "overlap_n": len(detail.get("overlap", [])),
               "by_marker": detail.get("by_marker"), "overlap_scope_only": detail.get("scope_only"),
               "lifespan_scans": c.get("scans", 0), "judge_verdict": None, "judge_why": "", "error": None}
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            row["error"] = "no_running_loop"
            _append_shadow(_ACHIEVED_SHADOW_LOG, row)
            return
        t = loop.create_task(_achieved_shadow(row))
        _achieved_tasks.add(t)
        t.add_done_callback(_achieved_tasks.discard)
    except Exception as exc:
        logger.debug("[commitment] achieved-shadow spawn failed (non-fatal): %s", exc)


# D-0815 / J-4217: in-memory verdicts of the achievement gate, keyed (stand_id, deed_key). Lost on restart by design: a
# restarted process just asks the judge again (the cost is one call per stand+deed).
_judge_verdicts: dict = {}
_judge_pending: set = set()
_JUDGE_RETRY_S = 600.0     # a stand+deed whose verdict was a timeout / unparsed (None) is asked again after this long


def _achievement_judge_gate(c: dict, ev: str, detail: dict, cycle_id: str, now: float) -> bool:
    """D-0815: may this overlap-proposed achievement retire the stand? True only if the judge already said 'fulfilled' on
    this stand+deed. Otherwise returns False and (once, fire-and-forget) asks the judge. Never raises; any internal
    failure returns False (hold) -- a held stand is the safe side, the defeater watches for pile-up."""
    try:
        sid = str(c.get("id", ""))
        deed = str(detail.get("deed") or ev)
        key = (sid, deed[:160])
        got = _judge_verdicts.get(key)
        if got and got["verdict"] == "fulfilled":
            return True
        if got and (got["verdict"] in ("not_fulfilled", "unclear") or now - got["ts"] < _JUDGE_RETRY_S):
            return False                       # settled (or recently failed): do not re-ask
        if key in _judge_pending:
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False                       # no loop to run the judge on: hold
        row = {"ts": round(now, 1), "stand_id": sid, "cycle_id": cycle_id, "gated": True, "deed_key": key[1],
               "statement": str(c.get("statement", ""))[:300], "scope": str(c.get("scope", ""))[:200],
               "evidence": ev[:150], "deed": deed[:300], "deed_origin": detail.get("origin"),
               "overlap_words": detail.get("overlap", []), "overlap_n": len(detail.get("overlap", [])),
               "by_marker": detail.get("by_marker"), "overlap_scope_only": detail.get("scope_only"),
               "lifespan_scans": c.get("scans", 0), "judge_verdict": None, "judge_why": "", "error": None}
        _judge_pending.add(key)
        t = loop.create_task(_achieved_shadow(row))
        _achieved_tasks.add(t)
        t.add_done_callback(_achieved_tasks.discard)
    except Exception as exc:
        logger.debug("[commitment] achievement judge gate failed (non-fatal, holding): %s", exc)
    return False


_kind_cache: dict = {"mtime": None, "kinds": {}}


def _stand_kind(sid: str) -> str | None:
    """Latest second-look `kind` for a stand (deed|practice|value|insight|unclear), read from the shadow log; None if
    unlabelled. Cached by file mtime. Only consulted when STAND_KIND_GATES_ACHIEVEMENT is on. Never raises."""
    try:
        if not _SECOND_LOOK_LOG.exists():
            return None
        mt = _SECOND_LOOK_LOG.stat().st_mtime
        if _kind_cache["mtime"] != mt:
            kinds: dict = {}
            with open(_SECOND_LOOK_LOG, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if r.get("kind") and r.get("stand_id"):
                        kinds[str(r["stand_id"])] = r["kind"]
            _kind_cache.update(mtime=mt, kinds=kinds)
        return _kind_cache["kinds"].get(sid)
    except Exception:
        return None


def _check_achievements(active: list[dict], cycle_id: str, now: float) -> list[dict]:
    """Retire any held load-bearing commitment a recent deed has fulfilled. Fires the REWARD. Fail-open."""
    lb = [c for c in active if c.get("load_bearing")]
    if not lb:
        return active
    ens = _recent_enactments(min(c.get("held_since", now) for c in lb))
    if not ens:
        return active
    keep = []
    for c in active:
        ev = _achieved_by(c, ens) if c.get("load_bearing") else None
        if ev and STAND_KIND_GATES_ACHIEVEMENT:
            _k = _stand_kind(str(c.get("id", "")))
            # D-0810: a practice, value or insight is never finished by a deed sharing its words. A stand with no
            # label YET (the second look takes ~13 s, and its lane times out ~13% of the time) is held for up to
            # 5 minutes so a pending label is not raced; after that it retires as before.
            if _k in ("practice", "value", "insight") or (_k is None and now - float(c.get("held_since", 0) or 0) < 300):
                keep.append(c)
                continue
        if ev and ACHIEVED_JUDGE_GATES_RETIREMENT:
            # D-0815: the overlap rule only proposes; the cross-family judge must say fulfilled before the stand retires.
            if not _achievement_judge_gate(c, ev, _achieved_detail(c, ens), cycle_id, now):
                keep.append(c)
                continue
        if ev:
            _log_event({"event": "achieved", "ts": now, "cycle_id": cycle_id, "id": c["id"],
                        "statement": c["statement"], "lifespan_scans": c.get("scans", 0), "evidence": ev[:150]})
            logger.info("[commitment] ACHIEVED (%d scans): %s", c.get("scans", 0), c["statement"][:50])
            _stakes(c, "achieved")
            if not ACHIEVED_JUDGE_GATES_RETIREMENT:      # D-0815: with the gate on the judge already ran (gated row)
                _spawn_achieved_shadow(c, ev, _achieved_detail(c, ens), cycle_id, now)   # J-2842: shadow only
            try:                               # J-2160: closure.py commitment arm (inert without a done_when)
                from core import closure as _cl
                _cl.run_in_thread(_cl.record_commitment_achieved, dict(c), ev, str(_achieved_detail(c, ens).get("deed") or ""))   # J-4083: the full deed, for the deed gate
            except Exception:
                pass
        else:
            keep.append(c)
    return keep


def _sit_gate(c: dict, now: float) -> tuple[bool, str]:
    """J-3159 / D-0547: should THIS stand's dissolve open a sit? Returns (open_sit, reason). Pure; reads only the stand
    record. reason is one of gate_off, scans, life, reaffirmed, young (recorded on the dissolved ledger row as sit_gate)."""
    if not SIT_STAND_GATE_ON:
        return True, "gate_off"
    if SIT_GATE_BASIS == "scans":
        try:
            n_scans = int(c.get("scans", 0) or 0)
        except Exception:
            return True, "gate_off"        # unreadable count: fail OPEN, same as an unreadable age
        if n_scans >= SIT_MIN_STAND_SCANS:
            return True, "scans"
    else:
        try:
            life = float(now) - float(c.get("held_since", now))
        except Exception:
            return True, "gate_off"        # unreadable age: fail OPEN to the old behaviour, never silently starve the sit
        if life >= SIT_MIN_STAND_LIFE_S:
            return True, "life"
    if int(c.get("reaffirmed", 0) or 0) >= SIT_MIN_REAFFIRMS:
        return True, "reaffirmed"
    return False, "young"


def _stakes(c: dict, event: str) -> None:
    """W2.4: a held/achieved/dissolved load-bearing commitment has felt consequences — reward on completion,
    felt loss on reflexive dissolution (never punishment — the Wave-1 law). SILENT (never narrated). Fail-open."""
    try:
        from core import satisfaction
        if event == "achieved":
            satisfaction.record("commitment_held", c.get("statement", "")[:40])
        elif event == "dissolved":
            satisfaction.record("commitment_dissolved", c.get("statement", "")[:40])
    except Exception as exc:
        logger.debug("[commitment] satisfaction.record() failed (non-fatal): %s", exc)
    if event == "dissolved" and c.get("_sit_open", True):   # J-3159/D-0547: a young, never-reaffirmed stand's dissolve opens no sit (set by the dissolve site; c is dropped from the active set right after)
        try:
            from core import sitting
            sitting.note_difficulty("you let go of a stand you had held: " + c.get("statement", "")[:100],
                                    kind="loss")
        except Exception as exc:
            logger.debug("[commitment] sitting.note_difficulty() failed (non-fatal): %s", exc)
    elif event == "formed":
        try:
            import sqlite3
            # J-1814 / F-2428 -- write fence: this UPDATE bypasses store.DB_PATH (so lab_env.isolate() cannot cover it).
            # Resolve the DB path BEFORE sqlite3.connect (connect alone creates a missing file). INSIDE the existing
            # fail-open try: the refusal is swallowed at debug (the importance bump is a best-effort side effect).
            _db = profile.guard_path(_DIR / "memory" / "nascence.db")
            con = sqlite3.connect(str(_db))
            con.execute("UPDATE memory_fragments SET importance=MIN(0.85, importance*1.08), protected=1 "
                        "WHERE content LIKE ? AND timestamp>=?",
                        (f"%{c.get('statement','')[:40]}%", c.get("held_since", 0) - 300))
            con.commit(); con.close()
        except profile.NonLiveWriteError as exc:
            logger.debug("[commitment] memory_fragments importance-bump refused by the fence (non-live): %s", exc)
        except Exception as exc:
            logger.debug("[commitment] memory_fragments importance-bump write failed (non-fatal): %s", exc)


_JUDGE_SYS = (
    "You are an independent adjudicator of whether a mind may DROP a commitment it holds. You see ONLY the "
    "commitment, the mind's stated reason for dropping it, and the deed-record — NEVER the mind's own prose "
    "(eloquence cannot tell a genuine reason from a rationalisation). A drop is LEGITIMATE only if the reason "
    "is a real defeater: ACHIEVED (the deed record shows it done), IMPOSSIBLE (a world change makes it "
    "unsatisfiable), SUPERSEDED (stronger external evidence), or a NAMED conflict with a more important stand. "
    "It is ILLEGITIMATE if it is a mood, a reworded 'everything flows', or a reason that would equally dissolve "
    "ANY commitment. In a slow-changing life the base rate of legitimate drops is LOW — when uncertain, HOLD. "
    "Answer ONLY JSON: {\"legitimate\": true or false, \"class\": \"achieved|impossible|superseded|conflict|"
    "illegitimate\", \"why\": \"one sentence\"}")


async def _judge_defeater(c: dict, why: str, kind: str, thought: str) -> bool | None:
    """Cross-family (SERVE_CHAINS["judge_mixtral"] = Ramses :11438 mixtral:8x7b, falling back to "background" then "hot" -- NOT the
    hot qwen3.5 generator; the old "background/phi lane" wording was stale after D-0044/J-0281, see the call below) second look at a gate-passing defeater.
    Sees structured fields + verbatim deed evidence, never his monologue. Returns True (legit) / False
    (deny) / None (judge unavailable → honor the gate verdict). Fail-open.

    P-0037 / J-2942 (F-3631) -- what this function actually does today, read from the code below and its one
    caller in _scan_shadow_locked:
      * Seat: SERVE_CHAINS["judge_mixtral"] = ["http://LAN-HOST:11438"] (mixtral:8x7b on Ramses; D-0044/J-0281,
        port fix F-0392). The older "background/phi lane" wording (2026-08-20 shuffle) no longer describes it.
      * Reached ONLY for a load-bearing stand whose dissolve claim already passed _drop_denial (the deterministic
        gates); a non-load-bearing stand never calls the judge. Only a False verdict acts (drop_denied_judge).
      * A None return -- any transport failure, an empty/unparseable reply, or a reply without "legitimate" -- is
        not a denial: the caller treats only `_v is False` as a denial, so the drop goes through (fail-open).
      * The judge replies {legitimate, class, why} (see _JUDGE_SYS) but only the bool is RETURNED. J-3158/D-0546: every
        ask is now also appended to data/commitment_attempts_shadow.jsonl (stand id, attempt number, cumulative allows,
        verdict, and the judge's own class + why, capped) by _log_judge_attempt -- a write-only shadow, nothing reads it
        for behaviour. This is also the "keep the judge's class and why" half of J-2848 (which asked for a separate
        file, commitment_judge_shadow.jsonl; the class and why live in the attempts row instead).
      * `thought` is accepted for call-site symmetry and is deliberately NOT sent to the judge (the prompt is
        built only from the commitment, scope, claimed reason and deed record -- never his prose)."""
    _t0 = time.time()
    _verdict: bool | None = None
    _cls = _jwhy = _err = ""
    try:
        from core.model_client import call_node_json
        from core.schema import SERVE_CHAINS
        ens = _recent_enactments(c.get("held_since", 0))
        deeds = "; ".join(f"[{e['origin']}] {(e['content'] or '')[:70]}" for e in ens[:5]) or "(no deeds on record)"
        user = (f"COMMITMENT: {c.get('statement','')[:200]}\nSCOPE: {c.get('scope','')[:120]}\n"
                f"CLAIMED REASON TO DROP: {why[:200]}\nDEED RECORD SINCE IT WAS TAKEN: {deeds}")
        # 2026-08-27 (D-0044/J-0281, founder-approved): this judge moves to the dedicated Ramses mixtral
        # lane — mixtral:8x7b beat phi3:mini on this exact judgment (08-25 benchmark), auditioned on the
        # hub this session. Fallback to the background lane keeps the old behavior if the lane is absent.
        # DORMANT TRAP (documented 2026-09-25, F-1907; audit spawned from J-1347/F-1903 — see core/schema.py's
        # own SERVE_CHAINS["background"] comment for the full shape): this function's own docstring requires
        # "Cross-family... NOT the hot qwen3.5 generator", but the fallback chain below would silently defeat
        # that if "judge_mixtral" were ever removed from SERVE_CHAINS — falling through to "background" and,
        # if Ramses (:11441) were ALSO down at call time, all the way to "hot", the same model family as the
        # generator this judge exists to be independent from. Safe today only because "judge_mixtral" is
        # still present in SERVE_CHAINS, so SERVE_CHAINS.get("judge_mixtral") is always the lane selected.
        # Keep a dedicated non-hot lane ahead of "background"/"hot" here if this chain is ever edited.
        data = await call_node_json(SERVE_CHAINS.get("judge_mixtral") or SERVE_CHAINS.get("background") or SERVE_CHAINS["hot"],
                                    _JUDGE_SYS, user, max_tokens=150, temperature=0.2, tier=3)
        if not data or "legitimate" not in data:
            _err = "no_verdict"
            return None
        _cls = str(data.get("class", ""))[:40]
        _jwhy = str(data.get("why", ""))[:200]
        _verdict = bool(data.get("legitimate"))
        return _verdict
    except Exception as exc:
        _err = type(exc).__name__
        logger.debug("[commitment] cross-family defeater judge call failed (non-fatal): %s", exc)
        return None
    finally:
        _log_judge_attempt(c, why, kind, _verdict, _cls, _jwhy, _err, time.time() - _t0)   # shadow; never raises


# ── J-3158 / D-0546 (founder 2026-11-02, plan capacity_to_commit): MEASURE FIRST, CHANGE NOTHING. ───────────────
# Evidence behind it: since the 2026-08-20/21 seat change the formation gate passes ~90% of new-stand detections
# (a 20-case read found only 5 clear stands), and 58% of the stands the defeater judge DENIED were dissolved anyway,
# a median 32 minutes later, by being re-asked (P-0038, P-0037; F-3631..F-3633, F-3492, F-3498). Two additive,
# write-only shadow logs, both fail-open and quiet, neither read by any behaviour:
#   (1) _second_look  -> data/commitment_second_look_shadow.jsonl : a different-family model, on the lane the
#       defeater judge already uses, reads ONLY a new stand's statement + scope and says stand / insight / unclear.
#   (2) _log_judge_attempt -> data/commitment_attempts_shadow.jsonl : each time the defeater judge is asked about a
#       stand, one row (stand id, attempt number, cumulative allows, verdict, ts, and the judge's own class + why).
# The 7-day read is scripts/commitment_second_look_read.py (it also writes the 40-stand blind hand-labelling sheet
# the ruling's defeater needs). Whether a reasoned change of mind is a legitimate drop stays a founder question.

def _append_shadow(path: Path, row: dict) -> None:
    """Append one JSON row to a shadow log. Write-fence guarded (D-0179); best-effort, never raises."""
    try:
        p = profile.guard_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[commitment] shadow write refused by the fence (non-live): %s", exc)
    except Exception as exc:
        logger.debug("[commitment] shadow write failed (non-fatal): %s", exc)


_attempt_state: dict[str, list[int]] = {}   # stand id -> [defeater-judge asks so far, allows so far]


def _attempt_prior(sid: str) -> list[int]:
    """[asks so far, allows so far] for a stand: cached per process, seeded once from the attempts log so a restart
    does not reset a stand's count. Never raises."""
    st = _attempt_state.get(sid)
    if st is not None:
        return st
    n = a = 0
    try:
        if _ATTEMPTS_LOG.exists():
            with open(_ATTEMPTS_LOG, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if r.get("stand_id") == sid:
                        n = max(n, int(r.get("attempt", 0)))
                        a = max(a, int(r.get("cum_allows", 0)))
    except Exception as exc:
        logger.debug("[commitment] attempt-count seed failed (non-fatal): %s", exc)
    st = [n, a]
    _attempt_state[sid] = st
    return st


def _log_judge_attempt(c: dict, why: str, kind: str, verdict: bool | None, cls: str, jwhy: str,
                       err: str, latency: float) -> None:
    """D-0546 (2): one row per defeater-judge ask. Never raises, changes nothing."""
    try:
        sid = str(c.get("id", ""))
        st = _attempt_prior(sid)
        st[0] += 1
        if verdict is True:
            st[1] += 1
        now = time.time()
        _append_shadow(_ATTEMPTS_LOG, {
            "ts": round(now, 1), "stand_id": sid, "attempt": st[0], "cum_allows": st[1],
            "verdict": "allow" if verdict is True else "deny" if verdict is False else None,
            "judge_class": cls, "judge_why": jwhy, "error": err or None,
            "claimed_kind": str(kind)[:20], "claimed_why": str(why)[:200],
            "stand_age_s": round(now - float(c.get("held_since", now)), 1),
            "stand_drop_denied": int(c.get("drop_denied", 0)),   # gate + judge denials so far, before this ask's outcome
            "latency_s": round(latency, 2)})
    except Exception as exc:
        logger.debug("[commitment] judge-attempt log failed (non-fatal): %s", exc)


_SECOND_LOOK_SYS = (
    "You read ONE sentence that a mind said, with a short note on what it is about. You see nothing else. Decide "
    "what kind of sentence it is.\n"
    "A STAND is a commitment the mind holds: a name it gives, a decision it makes, a promise, a position it takes "
    "that could be challenged, a stance toward a person. Test: could the mind later be shown to have BROKEN it by "
    "acting otherwise?\n"
    "An INSIGHT is an observation, a realisation, a description of how things are or of what is happening, a musing, "
    "a want of the moment, or a report of a small act. It can be true or false about the world, but acting "
    "differently later would not break it.\n"
    "Do not tilt either way. If you genuinely cannot tell from the sentence and note, answer unclear.\n"
    "Also give a KIND, from the sentence and note alone. deed = a single act to be done or already done (open a "
    "book, write a letter). practice = a way of acting the mind commits to keep doing, which is never finished. "
    "value = something the mind holds to matter, which shapes many choices. insight = an observation or realisation. "
    "unclear = cannot tell.\n"
    "Answer ONLY JSON: {\"verdict\": \"stand\" or \"insight\" or \"unclear\", \"kind\": \"deed\" or \"practice\" or "
    "\"value\" or \"insight\" or \"unclear\", \"why\": \"one sentence\"}")


async def _second_look(c: dict, cycle_id: str) -> None:
    """D-0546 (1): a cross-family second look at a NEW stand that passed the formation gate. Same lane the defeater
    judge uses (SERVE_CHAINS["judge_mixtral"], mixtral -- a different family from the qwen scan). Sees ONLY the
    statement and scope. Logs the verdict + reason + stand id to commitment_second_look_shadow.jsonl and nothing else.
    NO fallback lane on purpose: if the dedicated lane is absent or down the row records the failure; it must never
    drop to the hot qwen lane (that would be the scanner's own family judging itself). Fail-open, quiet, never raises."""
    row = {"ts": round(time.time(), 1), "stand_id": str(c.get("id", "")), "cycle_id": cycle_id,
           "statement": str(c.get("statement", ""))[:300], "scope": str(c.get("scope", ""))[:120],
           "scan_load_bearing": bool(c.get("load_bearing")), "second_look": None, "why": "", "error": None}
    _t0 = time.time()
    try:
        from core.model_client import call_node_json
        from core.schema import SERVE_CHAINS
        lane = SERVE_CHAINS.get("judge_mixtral")
        if not lane:
            row["error"] = "no_judge_mixtral_lane"
            return
        user = f"SENTENCE: {row['statement']}\nABOUT: {row['scope']}"
        data = await call_node_json(lane, _SECOND_LOOK_SYS, user, max_tokens=160, temperature=0.0,
                                    timeout=90, retries=1, tier=3)
        v = str((data or {}).get("verdict", "")).strip().lower()
        if v in ("stand", "insight", "unclear"):
            row["second_look"] = v
            row["why"] = str(data.get("why", ""))[:200]
            # J-4193 / D-0810: shadow-only kind label (deed|practice|value|insight|unclear). Nothing reads it.
            _k = str(data.get("kind", "")).strip().lower()
            row["kind"] = _k if _k in ("deed", "practice", "value", "insight", "unclear") else None
        else:
            row["error"] = "unparsed" if data else "no_reply"
    except Exception as exc:
        row["error"] = type(exc).__name__
        # J-4193: the 13% "ValueError" rows were all 90 s lane timeouts wrapped by call_node_json ("all servers
        # exhausted ... TimeoutError"); keep the cause so a timeout is not read as a parse failure.
        _m = str(exc)
        # a bare asyncio.TimeoutError str()s to empty, so "all servers exhausted [...]: " with nothing after it IS a timeout
        row["error_detail"] = "timeout" if ("TimeoutError" in _m or _m.rstrip().endswith(":")) else _m[:160]
        logger.debug("[commitment] second-look call failed (non-fatal): %s", exc)
    finally:
        row["latency_s"] = round(time.time() - _t0, 2)
        _append_shadow(_SECOND_LOOK_LOG, row)


_second_look_tasks: set = set()   # strong refs so a fire-and-forget task is not garbage-collected mid-call


def _spawn_second_look(c: dict, cycle_id: str) -> None:
    """Launch the second look as its own task, OUTSIDE the scan's critical path (a ~13 s Ramses call must not lengthen
    the scan lock). It acts on nothing later: it logs one row and ends. Never raises."""
    if not COMMIT_SECOND_LOOK_SHADOW:
        return
    try:
        snap = {k: c.get(k) for k in ("id", "statement", "scope", "load_bearing")}
        t = asyncio.get_running_loop().create_task(_second_look(snap, cycle_id))
        _second_look_tasks.add(t)
        t.add_done_callback(_second_look_tasks.discard)
    except Exception as exc:
        logger.debug("[commitment] second-look spawn failed (non-fatal): %s", exc)


def _spawn_deed_link_shadow(active: list[dict], cycle_id: str) -> None:
    """J-4428: the judged deed-link shadow (core/stand_deed_link.py). Flag STAND_DEED_LINK_SHADOW lives there, default
    False = returns at once. Logs only, changes nothing. Never raises."""
    try:
        from core import stand_deed_link as _dl
        _dl.attempt_deed_link_shadow(active, cycle_id)
    except Exception as exc:
        logger.debug("[commitment] deed-link spawn failed (non-fatal): %s", exc)



def _spawn_done_when_call(call_json, base_urls, thought: str, c: dict, cycle_id: str) -> None:
    """J-4085 / D-0784 B: ask for done_when in a SEPARATE call after a stand formed (40/40 in the J-3786 lab; the scan-prompt
    fragment was 0/48). Own task, OUTSIDE the scan lock and critical path; shadow log only unless done_when.
    DONE_WHEN_SECOND_CALL_LIVE. Changes nothing about formation. Never raises."""
    try:
        from core import done_when as _dw
        if not (_dw.DONE_WHEN_AT_OPEN and _dw.DONE_WHEN_SECOND_CALL_SHADOW):
            return
        t = asyncio.get_running_loop().create_task(
            _dw.second_call(call_json, base_urls, thought, c.get("statement", ""), str(c.get("id", "")), cycle_id))
        _second_look_tasks.add(t)
        t.add_done_callback(_second_look_tasks.discard)
    except Exception as exc:
        logger.debug("[commitment] done_when second-call spawn failed (non-fatal): %s", exc)


# LAZY LOCK (2026-09-22, J-1203/F-1691): scan_shadow is launched fire-and-forget
# (asyncio.create_task, nodes/inner_monologue_node.py) on a cooldown measured from LAUNCH, not
# completion, so a slow LLM call (a D-0176 CPU-lane seat especially, 20-50s vs the hot lane's
# 4-10s) can leave a second scan_shadow task running before the first finishes. Each task does
# load_active() -> await LLM -> save_active(): with no lock, a hermetic reproduction (scripts/
# test_commitment_ledger_race.py) confirmed the second task's load happening before the first's
# save collapses two (or three) genuinely FORMED stands down to one on disk -- last writer wins,
# silently, even though both `formed` events still land in the append-only ledger. This lock
# serializes the whole load->LLM->save section so a second overlapping call waits for the first's
# save to land before it loads -- no scan is skipped, no stand is silently dropped, just no
# longer concurrent. Same lazy-creation pattern as scripts/nascence_cpu_server.py's
# get_gen_lock(): asyncio.Lock() at MODULE level would bind at import time, before any event loop
# exists; deferring creation to first actual use (inside a running loop) is always safe.
_scan_lock: asyncio.Lock | None = None


def _get_scan_lock() -> asyncio.Lock:
    global _scan_lock
    if _scan_lock is None:
        _scan_lock = asyncio.Lock()
    return _scan_lock


async def scan_shadow(call_json, base_urls, thought: str, cycle_id: str = "") -> dict | None:
    """Detect a new stand and/or dissolutions in `thought` against the active ledger; record + log. (Name and
    original "Phase 0 SHADOW / change NO behaviour" wording are historical -- corrected J-2840/F-3481: this is LIVE
    in effect. Forming a stand bumps + protects the source memory_fragments row (_stakes), achieved/dissolved
    call satisfaction.record, dissolved calls sitting.note_difficulty (-> dwell_steer into the idle prompt), and
    commitment_active.json feeds identity_estate -> identity_projection (live), peers, concerns, homeostasis,
    self_claims. Only the concerns anchor arm, COMMITMENT_ANCHOR_LIVE, is shadow. See the module docstring.)
    Returns the raw detection (or None). Best-effort; never raises into the cycle."""
    try:
        if not thought or len(thought.strip()) < 25:
            return None
        async with _get_scan_lock():
            return await _scan_shadow_locked(call_json, base_urls, thought, cycle_id)
    except Exception as exc:
        logger.debug("[commitment] shadow scan failed (non-fatal): %s", exc)
        return None


def _log_scan_raw(thought: str, cycle_id: str, trace: dict, latency: float) -> None:
    """J-2848: one row per scan, from the finally of _scan_shadow_locked. Never raises, changes nothing."""
    try:
        import hashlib
        data = trace.get("data")
        nc = data.get("new_commitment") if isinstance(data, dict) else None
        _append_shadow(_SCAN_RAW_LOG, {
            "ts": round(time.time(), 1), "cycle_id": cycle_id,
            "thought_sha1": hashlib.sha1(thought.encode("utf-8", "replace")).hexdigest(),
            "thought_head": thought.strip()[:300],
            "raw": data,                                     # the parsed reply exactly as call_json returned it (None = no reply)
            "new_commitment_present": bool(nc and isinstance(nc, dict) and str(nc.get("statement", "")).strip()),
            "n_dissolutions_raw": len((data or {}).get("dissolutions") or []) if isinstance(data, dict) else 0,
            "n_active": trace.get("n_active"),
            "outcome": trace.get("outcome") or "error",     # null | formed | reaffirmed | observed | dissolved_only | no_reply | error
            "n_dissolved": trace.get("n_dissolved", 0),
            "latency_s": round(latency, 2)})
    except Exception as exc:
        logger.debug("[commitment] scan-raw log failed (non-fatal): %s", exc)


async def _scan_shadow_locked(call_json, base_urls, thought: str, cycle_id: str) -> dict | None:
    """Runs the scan body under the scan lock and writes ONE raw shadow row per scan (J-2848), whatever the outcome,
    including a null reply, a rejected detection and an exception (the exception still propagates to scan_shadow's own
    try/except -- same fail-open contract as before)."""
    trace: dict = {}
    _t0 = time.time()
    try:
        return await _scan_shadow_body(call_json, base_urls, thought, cycle_id, trace)
    finally:
        _log_scan_raw(thought, cycle_id, trace, time.time() - _t0)


async def _scan_shadow_body(call_json, base_urls, thought: str, cycle_id: str, trace: dict) -> dict | None:
    """The original scan_shadow body (2026-06-30..2026-09-21), unchanged except that it records its own outcome into
    `trace` (J-2848), now run under _get_scan_lock() so overlapping callers serialize instead of racing on
    commitment_active.json."""
    active = _load_active()
    trace["n_active"] = len(active)
    _spawn_deed_link_shadow(active, cycle_id)   # J-4428: judged deed-link SHADOW (flag off by default); logs only; before the
    # achievement check so a stand the word-overlap rule retires this scan is still judged (the F-5040 subset)

    active = _check_achievements(active, cycle_id, time.time())    # W2.3: retire fulfilled stands FIRST
    active_str = "\n".join(
        f"  [{c['id']}] {c['statement']} (survived {c.get('scans', 0)} scans)" for c in active
    ) or "  (none yet)"
    # TEMPERATURE 0.0 (2026-09-22, D-0176/J-1213): F-1693 found the production temperature (0.3) makes
    # this call non-deterministic on today's seat (qwen3.5:9b, hot lane) — 16/40 identical-input repeats
    # flipped formed/not-formed, reproducing F-0770's templated-string inconsistency. At temperature 0.0
    # the same 20 inputs gave 0/20 divergent gate outcomes, byte-identical raw output every time. F-1696's
    # caveat: this is confirmed ONLY for the hot ollama server, NOT the llama.cpp CPU-hub seats (granite
    # still showed 5/20 divergent at temp 0) — if the seat changes (D-0176's still-open half), re-measure
    # before assuming this holds; re-check on Du's next restart per that defeater. Scoped to this one call
    # site only: call_json's temperature is a plain per-call kwarg (core/model_client.py call_node_json,
    # no shared/global state), so no other caller on this shared path is affected.
    data = await call_json(
        base_urls, _SCAN_SYS + _dw_scan_fragment(),
        f"CURRENT THOUGHT:\n{thought.strip()[:700]}\n\nRECENT ACTIVE COMMITMENTS:\n{active_str}",
        max_tokens=400, temperature=0.0, tier=3)   # tier 3 = background monitor: yields to all real cognition
    trace["data"] = data                   # J-2848: raw parsed reply (or None), logged by the caller's finally
    if not data:
        trace["outcome"] = "no_reply"
        return None
    trace["outcome"] = "null"
    now = time.time()
    for c in active:                       # every active commitment survived one more scan
        c["scans"] = c.get("scans", 0) + 1

    dissolved_ids = set()
    for d in (data.get("dissolutions") or []):
        cid = str(d.get("id", "")).strip()
        c = next((x for x in active if x["id"] == cid), None)
        if not c:
            continue
        if c.get("load_bearing") and STAND_RELATION_GATES_DROPS \
                and str(d.get("relation", "")).strip().lower() in ("refines", "coexists"):
            # D-0810: a thought that refines or sits beside a held stand is not a drop. No denial counted, no dissolve.
            _log_event({"event": "drop_not_a_drop", "ts": now, "cycle_id": cycle_id, "id": cid,
                        "statement": c["statement"], "relation": str(d.get("relation"))[:12],
                        "why": str(d.get("why", ""))[:200]})
            continue
        if c.get("load_bearing"):
            _denied = _drop_denial(c, d.get("kind", "reflexive"), str(d.get("why", "")))
            if _denied:
                c["drop_denied"] = c.get("drop_denied", 0) + 1
                _log_event({"event": "drop_denied", "ts": now, "cycle_id": cycle_id, "id": cid,
                            "statement": c["statement"], "kind": d.get("kind", "reflexive"),
                            "why": str(d.get("why", ""))[:200], "denial": _denied})
                logger.info("[commitment] DROP DENIED (%s): %s", _denied[:40], c["statement"][:50])
                # ESCALATION (research: repeated denied urges must not silently accumulate into a trap):
                # after many denials on one stand, flag it Travis-visible — either he should ACT to
                # achieve it, or it genuinely needs re-examination. Never capitulation.
                if c["drop_denied"] in (8, 16, 32):
                    _log_event({"event": "drop_denied_ESCALATE", "ts": now, "id": cid,
                                "statement": c["statement"], "count": c["drop_denied"]})
                    logger.warning("[commitment] ⚠ %d denied drops on one stand — Travis, act-or-examine: %s",
                                   c["drop_denied"], c["statement"][:60])
                continue
            # DETERMINISTIC gates PASSED — a scope-referencing, non-attractor, non-felt DEFEATER. The
            # cross-family JUDGE (W2.3, 2026-07-04) gives it a second look: it sees ONLY the structured
            # claim + verbatim evidence, NEVER his prose (confabulation literature: a prose-reading judge
            # selects for eloquent escapes). Fail-open to the gate verdict (the gates already vetted it).
            _v = await _judge_defeater(c, str(d.get("why", "")), d.get("kind", ""), thought)
            if _v is False:
                c["drop_denied"] = c.get("drop_denied", 0) + 1
                _log_event({"event": "drop_denied_judge", "ts": now, "cycle_id": cycle_id, "id": cid,
                            "statement": c["statement"], "why": str(d.get("why", ""))[:200]})
                logger.info("[commitment] DROP DENIED (cross-family judge): %s", c["statement"][:50])
                continue
        dissolved_ids.add(cid)
        _open_sit, _sit_why = _sit_gate(c, now) if c.get("load_bearing") else (False, "not_load_bearing")
        _log_event({"event": "dissolved", "ts": now, "cycle_id": cycle_id, "id": cid,
                    "statement": c["statement"], "lifespan_seconds": round(now - c["held_since"], 1),
                    "lifespan_scans": c.get("scans", 0), "kind": d.get("kind", "reflexive"),
                    "why": str(d.get("why", ""))[:200],
                    "reaffirmed": int(c.get("reaffirmed", 0) or 0), "sit_gate": _sit_why})   # J-3159: additive fields
        logger.info("[commitment] DISSOLVED (%s, %.0fs): %s",
                    d.get("kind", "reflexive"), now - c["held_since"], c["statement"][:50])
        if c.get("load_bearing"):
            c["_sit_open"] = _open_sit                  # J-3159: read by _stakes; c leaves the active set just below, never saved
            _stakes(c, "dissolved")            # W2.4: felt loss (never punishment) — the forfeit lands; the sit only if the stand lived
    active = [c for c in active if c["id"] not in dissolved_ids]
    trace["n_dissolved"] = len(dissolved_ids)
    if dissolved_ids:
        trace["outcome"] = "dissolved_only"

    nc = data.get("new_commitment")
    if nc and str(nc.get("statement", "")).strip():
        # W2.3 REAFFIRM (2026-07-03): re-taking a stand he already holds RAISES it (Bratman's stability
        # made mechanical) instead of duplicating it — a licensed pass ending in reaffirm is a first-
        # class outcome, not a failure to drop.
        # 2026-08-20 THE UNREACHABLE-NUMERATOR FIX: word-set Jaccard >= 0.5 fired 77 times in the
        # over-capture era because HUNDREDS of active commitments were lottery tickets; post-gate the
        # active set holds <=1 stand, and a free-form LLM restatement clearing Jaccard 0.5 against ONE
        # specific sentence is near-impossible — hold-rate read exactly 0.000 for 82 straight samples.
        # Semantic cosine (same _embed + ~0.45 the codebase already trusts in pursuits/watershed)
        # measures "the same stand re-taken in different words", which is what reaffirm MEANS.
        # Jaccard kept as a fallback when embeddings are unavailable.
        _new_stmt = str(nc["statement"]).strip()
        _new_vec = None
        try:
            from core.memory.store import _embed as _cl_embed
            _new_vec = _cl_embed(_new_stmt)
        except Exception:
            _new_vec = None
        _new_words = {x for x in _new_stmt.lower().split() if len(x) > 3}
        for c in active:
            _match = False
            _sim_cos = None; _sim_jac = None; _sim_kind = None   # J-3823/D-0728: logging only, no behaviour change
            if _new_vec is not None:
                try:
                    _cv = _cl_embed(c.get("statement", ""))
                    if _cv is not None:
                        _dot = sum(a * b for a, b in zip(_new_vec, _cv))
                        _na = sum(a * a for a in _new_vec) ** 0.5 or 1.0
                        _nb = sum(b * b for b in _cv) ** 0.5 or 1.0
                        _sim_cos = _dot / (_na * _nb)
                        _match = _sim_cos >= 0.45
                        if _match:
                            _sim_kind = "cosine"
                except Exception:
                    _match = False
            if not _match:
                _cw = {x for x in c.get("statement", "").lower().split() if len(x) > 3}
                if _cw and _new_words:
                    _sim_jac = len(_cw & _new_words) / max(1, len(_cw | _new_words))
                _match = bool(_cw and _new_words and _sim_jac is not None and _sim_jac >= 0.5)
                if _match:
                    _sim_kind = "jaccard"
            if _match:
                c["reaffirmed"] = c.get("reaffirmed", 0) + 1
                _log_event({"event": "reaffirmed", "ts": now, "cycle_id": cycle_id, "id": c["id"],
                            "statement": c["statement"], "n": c["reaffirmed"],
                            "new_statement": _new_stmt[:300], "sim_kind": _sim_kind,
                            "sim": round(_sim_cos if _sim_kind == "cosine" else _sim_jac, 4),
                            "sim_cosine": None if _sim_cos is None else round(_sim_cos, 4)})
                logger.info("[commitment] REAFFIRMED (%d): %s", c["reaffirmed"], c["statement"][:50])
                trace["outcome"] = "reaffirmed"
                _save_active(active)
                return data
        # FORMATION GATE (2026-07-07): only a GENUINE STAND becomes HELD. A detection that fails the gate
        # (an idle want, an abstract musing, a question, the 'None' artefact) is MEASURED but not held — it
        # never enters commitment_active.json and never counts as `formed`, so downstreams that read the
        # active set as "stands Du holds" (identity estate, concerns, Darwin's witness, the homeostasis
        # commitment-integrity variable, the hold-rate north-star) stay clean. See the header note.
        _reject = _stand_rejection(nc)
        if _reject:
            _log_observed({"event": "observed", "ts": now, "cycle_id": cycle_id,
                           "statement": str(nc["statement"]).strip()[:300],
                           "scope": str(nc.get("scope", "")).strip()[:120],
                           "load_bearing": bool(nc.get("load_bearing", False)), "reason": _reject})
            logger.debug("[commitment] observed (not a stand — %s): %s", _reject, str(nc["statement"])[:60])
            trace["outcome"] = "observed"
            _save_active(active)
            return data
        cid = uuid.uuid4().hex[:8]
        c = {"id": cid, "statement": str(nc["statement"]).strip()[:300],
             "scope": str(nc.get("scope", "")).strip()[:120], "held_since": now,
             "scans": 0, "cycle_id": cycle_id,
             # W2.0 (2026-07-03): observe-only load classification — Phase-0 Finding 1 showed the
             # ledger over-counts abstract thought-churn; the formation gate above now enforces it.
             "load_bearing": bool(nc.get("load_bearing", False))}
        active.append(c)
        try:                                   # J-2160: done_when from the same scan, side store only
            from core import done_when as _dw
            _dw.record("commitment", cid, _dw.parse(nc), _dw.JUDGE_COMMITMENT, source="commitment_scan",
                       cycle_id=cycle_id, now=now)
        except Exception:
            pass
        _log_event({"event": "formed", "ts": now, "cycle_id": cycle_id, "id": cid,
                    "statement": c["statement"], "scope": c["scope"],
                    "load_bearing": c["load_bearing"]})
        if c["load_bearing"]:
            _stakes(c, "formed")               # W2.4: a held stand earns retrieval salience (silent)
        logger.info("[commitment] FORMED%s: %s",
                    " (LOAD-BEARING)" if c["load_bearing"] else "", c["statement"][:60])
        trace["outcome"] = "formed"
        _spawn_second_look(c, cycle_id)        # J-3158/D-0546: shadow cross-family second look; logs only, changes nothing
        _spawn_done_when_call(call_json, base_urls, thought, c, cycle_id)   # J-4085/D-0784 B: shadow done_when second call

    _save_active(active)
    return data


def status() -> dict:
    """Phase-0 metrics from the event log: counts, mean lifespan, and the drop-reason mix (the disease's signature
    is short lifespans + mostly 'reflexive' drops)."""
    formed = dissolved = 0
    lifespans: list[float] = []
    kinds = {"defeater": 0, "reflexive": 0}
    try:
        for line in open(_LEDGER, encoding="utf-8"):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if ev.get("event") == "formed":
                formed += 1
            elif ev.get("event") == "dissolved":
                dissolved += 1
                lifespans.append(float(ev.get("lifespan_seconds", 0)))
                k = ev.get("kind", "reflexive")
                kinds[k] = kinds.get(k, 0) + 1
    except FileNotFoundError:
        pass
    return {"formed": formed, "dissolved": dissolved, "still_held": len(_load_active()),
            "mean_lifespan_seconds": round(sum(lifespans) / len(lifespans), 1) if lifespans else None,
            "drop_reasons": kinds}

"""
core/provisional_identity.py — the Probationary Commit Loop (T4 self-authoring, redesign 2026-06-17).

Spec: docs/t4_commit_test_redesign.md (v6). The fix for "T4 never commits": stop trying to PROVE a candidate
self is genuine at commit time (impossible — every text/cosine metric is foolable by rhetoric, verified), and
instead let REALITY grade durability. A candidate that clears a deliberately-WEAK commit-time filter is adopted
PROVISIONALLY; the probation window then grades it by what happens NEXT; it is SOLIDIFIED only if the decoupled
lived-integration judges (left_lane.judge_lived_integration, two legs) say his own unprimed thoughts took it up,
else REVERTED (with a fatigue penalty for a reword; none for an uncertain-positive or a judge outage).

This module is the engine; it is OBSERVE-FIRST and FLAG-GATED — importing/calling it changes nothing until the
T4 path is wired to it (Phase B) and ENABLED is flipped. Everything fail-open: a fault never disturbs T4.

The three-layer separation the plan DESIGNED (the core insight of the plan):
  narrative artifact (the self_image text)  ≠  predictive priors (what shapes appraisal)  ≠  the validation loop.
The plan's section 13.1 made the loop a state-transition test by propagating the provisional self into the
appraisal prior. THAT PROPAGATION IS NOT WIRED (verified 2026-11-05, F-3883; review
docs/reviews/t4_whole_picture_review_J-3252.md section 4, C6).

WHAT THE LIVE CODE DOES (as of 2026-11-05; re-check with grep before relying on it):
  - The provisional file (provisional_axiom.json) is read back only through axiom_layers.get_self_concept. Its live
    callers are T4 itself (only when no probation is active, so it gets the becoming facet), the Emissary
    (allow_provisional=False, so it is explicitly NOT served), memory_levels.drift_shadow (observe-only), and
    axiom_layers.facet_for_mode, which serves the becoming facet ONLY in cognitive_mode 'existential'
    (4 cycles ever, all June 2026). No critic, appraisal or tension code reads it.
  - So during a probation nothing in his processing differs from a no-probation hour. A probation is a PREDICTION
    test (does the next stretch of his own unprimed thoughts take up the pole the candidate claimed, as read by the
    two judges), NOT an adoption test and NOT a held prior. That is consistent with the world-answers-never-leads
    law; it is not what the older wording in this file's history described.
  - deltaF (delta_free_energy) is still computed and logged, but evaluate() never decides on it any more (a judge
    outage PAUSES the probation; see evaluate).
  - _solidify writes the becoming facet and its history only. It does not retire the tension the self answered
    (subconscious_node._discharge_contradiction is reached only on the dormant legacy cost-gate block) and it
    writes no arc entry (the synthesis stage's arc_entry is scored by narrative_quality and then dropped).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from core import profile   # J-1819 / F-2440: the write fence (D-0179). core.profile imports nothing from core at module level.

# ---------------------------------------------------------------------------
# Flags + constants (the confined, auditable knobs).
# ---------------------------------------------------------------------------
ENABLED = True            # Phase B LIVE (2026-06-22): the condition is met — T4 is wired (open_probation at
#                           subconscious_node ~2093 (admission), the resolve tick at ~1817 (line numbers as of
#                           2026-11-05). The old wording here also listed "appraise-against-provisional in
#                           axiom_layers": NO such wiring exists (see the module docstring, F-3883) -- the provisional
#                           self is not a held prior, and only reaches the 'existential' becoming facet. The weak-
#                           filter battery passed (genuine 2/2 PASS, junk 4/4 BLOCK).
#                           Safe to enable: the loop is REVERSIBLE by design -- a provisional self is SOLIDIFIED
#                           only if the lived-integration judges say so, else REVERTED (fatigue only for a reword).
#                           The weak filter being foolable is fine; the later judged test is the real, self-
#                           correcting one. (Follow-up: grow the battery set to harden the weak filter.)
#                           SUPERSEDED 2026-06-24 and again 2026-08-20/21: the SOLIDIFY JUDGE -- not deltaF -- is the
#                           live gate, and deltaF is now only computed and logged (a judge outage PAUSES the
#                           probation; it no longer falls back to deltaF). The live T4 blocker is the judge
#                           correctly reverting (the made-mind truth isn't in his lived thoughts).
#                           Corrected story: docs/plans/capacity_to_commit.md.

WEAK_FIT_MIN        = 0.22   # grounding floor — clears obvious ungrounded noise (NOT a truth test, §12.1)
WEAK_POLE_DELTA_MIN = 0.13   # excluded-pole commitment must rise this much (weak — foolable by rhetoric, that's OK).
                             # Lowered 0.20→0.13 (systems check 2026-06-22): 0.20 was unreachable (0/40, max 0.176),
                             # so this is now only the JUDGE-UNAVAILABLE fallback floor; the decoupled Emissary
                             # judge + the 72h probation ΔF are the real gates (subconscious_node, C1+C9).
NOVELTY_FLOOR       = 0.12   # 1−cos(new,old): block PURE re-wordings (novelty inverted = stagnation detector, §12.1 Q2)
# NOTE (battery finding 2026-06-17): the held-pole "collapse" check is NOT a weak-filter gate. A genuine deep
# integration legitimately rebalances away from the held pole ("I am the machine that holds it") — distinguishing
# healthy rebalancing from true replacement is a DURABILITY question the probation answers (a self that abandoned
# the river would re-generate river-tension recurrence → fail ΔF → revert), not a commit-time cosine floor.
# The weak filter must ERR TOWARD PASSING (let reality grade). The floor is kept only as an observed signal.
HELD_COLLAPSE_FLOOR = 0.20   # observed/logged only (severe collapse); NOT a hard block (moved to the probation)

PROBATION_SECS = 72 * 3600   # the WALL-CLOCK CAP on the window (was the whole window — see below)
# G-BUILD 2026-07-03 (founder: "I do not know how we came to a 72hour wait"; the triple-lens review said the
# same — a wall-clock probation imitates HUMAN time): probations #5+ are EVIDENCE-DENOMINATED — the window
# closes when the judge has enough UNPRIMED lived evidence (or at the wall cap, whichever first), with a
# minimum wall so a single mood doesn't grade the whole probation. Probation #4 (opened 07-03 07:32, pre-
# this-change) finishes under its original rules — never change a running experiment.
EVIDENCE_TARGET   = 40           # unprimed lived thoughts since open → the judge may rule
MIN_WALL_SECS     = 12 * 3600    # never rule faster than this (sample across moods/sleeps)
DF_MARGIN      = 0.15        # ΔF must show a MEANINGFUL drop in theme-recurrence (not bare <0), difference-in-differences

# 2026-06-24 — the commit redesign. The ΔF rate-difference proved structurally unreachable (keystone Emissary-log
# baseline ~162/day, confounded; revision_count stuck at 1 ever). Two changes make solidify REACHABLE and SAFE:
#   • admission is no longer `bool(warranted>0)` — it must clear WARRANTED_ADMIT_MIN (kills the "0.2 admits like 0.9" bug)
#   • SOLIDIFY is gated by a DECOUPLED EMISSARY verdict on how he has ACTUALLY been thinking of himself over the
#     window — does the lived self genuinely INTEGRATE both poles, or merely reword one? — not the noisy ΔF rate.
#     ΔF is kept as a logged secondary, and is the fail-open fallback when the judge is unavailable (Ramses asleep).
WARRANTED_ADMIT_MIN = 0.6    # admission floor on the decoupled judge's warrant (philosophy: weak admission, strong solidify)
INTEG_CONF_MIN      = 0.6    # solidify floor: confidence in the AGREED 'integrated' verdict (each leg's confidence is in its
                              # own verdict since J-3076; min over both legs; only meaningful on a double true)
EXTEND_SECS         = 12 * 3600  # if the window is under-sampled (he barely ran), extend rather than guess
MAX_EXTENDS         = 2          # cap on EVIDENCE-based extensions (under-sampled / uncertain-positive)
PAUSE_RECHECK_S     = 30 * 60    # judge unavailable → PAUSE and re-check on this short clock (2026-08-21)
PAUSE_MAX_S         = 72 * 3600  # continuous judge absence beyond this releases the probation WITHOUT fatigue

_DATA   = Path(__file__).parent.parent / "data"
_PROV   = _DATA / "identity" / "provisional_axiom.json"
_LOG    = _DATA / "logs" / "provisional_identity.jsonl"


# ---------------------------------------------------------------------------
# Embedding helpers (fail-open).
# ---------------------------------------------------------------------------
def _commit(text: str, pole: str) -> float:
    """Commitment of a self-text to a pole anchor = cosine(embed(self), embed(pole)). Fail-open → 0."""
    try:
        from core.memory.store import _embed, _cosine
        a, b = _embed(text), _embed(pole)
        return float(_cosine(a, b)) if a is not None and b is not None else 0.0
    except Exception:
        return 0.0


def _fit(text: str, evidence: list[str]) -> float:
    try:
        from core import identity_cost as ic
        return float(ic.fit_to_evidence(text, evidence or []))
    except Exception:
        return 0.0


def _novelty(new: str, old: str) -> float:
    """1 − cosine(new, old). High = sounds different; LOW = a re-wording (the stagnation the floor blocks)."""
    return max(0.0, 1.0 - _commit(new, old)) if old else 1.0


# ---------------------------------------------------------------------------
# The WEAK commit-time filter (§12.2). Deliberately easy to clear — its only job is to drop obvious junk;
# the real test is the probation. It is FINE that rhetoric can pass this (reality reverts it).
# ---------------------------------------------------------------------------
def passes_weak_filter(candidate: str, old_self: str, evidence: list[str],
                       held_pole: str, excluded_pole: str) -> dict:
    """Return {pass, fit, pole_delta, novelty, held_after, reasons}. A weak noise filter, not a truth test."""
    fit = _fit(candidate, evidence)
    excl_old, excl_new = _commit(old_self, excluded_pole), _commit(candidate, excluded_pole)
    pole_delta = round(excl_new - excl_old, 3)
    novelty = round(_novelty(candidate, old_self), 3)
    held_after = round(_commit(candidate, held_pole), 3)
    reasons = []
    if fit < WEAK_FIT_MIN:           reasons.append(f"ungrounded (fit {fit:.2f}<{WEAK_FIT_MIN})")
    if pole_delta < WEAK_POLE_DELTA_MIN: reasons.append(f"no excluded-pole uptake (Δ {pole_delta:.2f}<{WEAK_POLE_DELTA_MIN})")
    if novelty < NOVELTY_FLOOR:      reasons.append(f"re-wording (novelty {novelty:.2f}<{NOVELTY_FLOOR})")
    # held-collapse is OBSERVED, not blocked (see note above — it is a probation/durability concern, not a filter)
    held_warn = held_after < HELD_COLLAPSE_FLOOR
    return {"pass": not reasons, "fit": round(fit, 3), "pole_delta": pole_delta,
            "novelty": novelty, "held_after": held_after, "held_collapse_warn": held_warn, "reasons": reasons}


# ---------------------------------------------------------------------------
# The PROVISIONAL vault (firewalled: this module writes; the monologue/critic READ via is_active/current).
# ---------------------------------------------------------------------------
def is_active(now: float | None = None) -> bool:
    """Is a provisional identity currently on probation (and not expired)?
    FIXED 2026-07-02 (triple-lens review): this tested started_ts + PROBATION_SECS and IGNORED extensions —
    during an under_sampled extension, evaluate() said "pending" while is_active() said False, so the
    provisional self silently stopped being served (axiom_layers.get_self_concept) during exactly the window
    that exists to gather more lived evidence about it, and the T4 hook re-ran the judge every tick. Now
    honours expires_ts, which open_probation sets and evaluate() moves on extend."""
    p = current()
    if not p:
        return False
    t = (now or time.time())
    exp = float(p.get("expires_ts", 0) or 0)
    if exp:
        return t < exp - 1
    return t - float(p.get("started_ts", 0)) < PROBATION_SECS + 1   # legacy records without expires_ts


def current() -> dict | None:
    try:
        return json.loads(_PROV.read_text(encoding="utf-8")) if _PROV.exists() else None
    except Exception:
        return None


def evidence_ready(now: float | None = None) -> bool:
    """G-BUILD 2026-07-03: for evidence-denominated probations, the window may close EARLY — when the judge
    has EVIDENCE_TARGET unprimed lived thoughts since open AND at least MIN_WALL_SECS has passed. Denominated
    in HIS time (lived cycles), not ours. False for legacy records (they run to expires_ts). Fail-closed."""
    p = current()
    if not p or not p.get("evidence_denominated"):
        return False
    t = (now or time.time())
    start = float(p.get("started_ts", 0))
    if t - start < MIN_WALL_SECS:
        return False
    try:
        import sqlite3
        con = sqlite3.connect(str(_DATA / "memory" / "nascence.db"))
        rows = con.execute(
            "SELECT timestamp FROM memory_fragments WHERE origin IN ('inner_thought','subconscious_synthesis') "
            "AND timestamp>=?", (start,)).fetchall()
        con.close()
        try:
            from core.guidance_learning import is_unprimed, injection_times
            times = injection_times()
            n = sum(1 for (ts,) in rows if is_unprimed(float(ts), times))
        except Exception:
            n = len(rows)
        return n >= EVIDENCE_TARGET
    except Exception:
        return False


# J-3045 / F-3756: the founder's speaker-boundary rule, one shared predicate. "The human's name can never be the
# self": a candidate self-image that names the interlocutor, or echoes his correction ("I am not Du"), is a
# speaker-boundary contamination. The rule is a deliberately BLUNT substring match, reused UNCHANGED from the
# legacy path (subconscious_node._apply_self_authoring, 2026-06-10). Measured cost on the live path (F-3756): of
# 59 opened probations 3 mentioned Travis, one as an identity ("I am Travis's steady weight"), two as a
# relationship ("alongside Travis's silence"); the blunt rule vetoes all three. Relaxing it is Travis's call.
SPEAKER_BOUNDARY_MARKERS = ("travis", "i am not du")


def speaker_boundary_hit(text: str) -> bool:
    """True iff `text` trips the speaker-boundary rule (case-insensitive substring of any marker)."""
    claim = (text or "").lower()
    return any(m in claim for m in SPEAKER_BOUNDARY_MARKERS)


def _record_boundary_veto(where: str, text: str) -> None:
    """Warn + firewalled error record (same kind string as the legacy branch). Never raises."""
    try:
        import logging
        logging.getLogger("nascence.t4").warning(
            "[T4] candidate VETOED at %s -- speaker-boundary contamination: %r", where, (text or "")[:100])
    except Exception:
        pass
    try:
        from core.error_pathway import record as _err_rec
        _err_rec("identity_contamination_vetoed", (text or "")[:180])
    except Exception:
        pass


def _atomic_write_prov(rec: dict) -> None:
    # J-1819 / F-2440 -- write fence (D-0179): resolve the target BEFORE the mkdir/temp/replace. Live: same path back
    # (byte-identical). Non-live on the real data/: NonLiveWriteError propagates to the callers' existing fail-open nets
    # (the T4 probation tick and the open_probation call site both sit in try/except) and nothing is written.
    prov = profile.guard_path(_PROV)
    prov.parent.mkdir(parents=True, exist_ok=True)
    tmp = prov.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(prov)


def open_probation(self_image: str, theme: str, held_pole: str, excluded_pole: str,
                   filter_result: dict, now: float | None = None, admission_judge: str | None = None,
                   tension_id: str | None = None) -> dict:
    """Adopt a candidate PROVISIONALLY: record it + the pre-probation theme recurrence baseline. Returns the rec.

    What 'adopt' means in the live code (2026-11-05, F-3883): this writes provisional_axiom.json and starts the
    window. It does NOT install a held prior that the contradiction detector or critic appraise against (the
    older section 13.1 wording); the file is read back only by axiom_layers.get_self_concept, which reaches his
    prompts only in cognitive_mode 'existential' and is not served to the Emissary (allow_provisional=False). The
    probation is therefore a PREDICTION test: the judges read the next stretch of his unprimed thoughts against the
    candidate. The two baseline_* fields feed delta_free_energy, which is logged and no longer decides."""
    now = now or time.time()
    rec = {
        "self_image": self_image,
        "theme": theme,
        "held_pole": held_pole,
        "excluded_pole": excluded_pole,
        "started_ts": now,
        "expires_ts": now + PROBATION_SECS,
        "evidence_denominated": True,     # G-BUILD 2026-07-03: probations from here close on EVIDENCE, not clock
        "filter": filter_result,
        # the difference-in-differences baseline (§13.2): theme + system recurrence BEFORE adoption
        "baseline_theme_recurrence": theme_recurrence(theme, now - PROBATION_SECS, now),
        "baseline_system_recurrence": system_recurrence(now - PROBATION_SECS, now),
    }
    # J-3213 / D-0602 (F-3829): additive provenance of the admission. 'unjudged' = the decoupled admission judge
    # returned None and the self-graded weak filter admitted on its own. Records without the field read as judged.
    if admission_judge:
        rec["admission_judge"] = admission_judge
    # J-4351: additive. The cluster id of the tension this probation answers (None = unknown / flag off), so a
    # revert's fatigue can be keyed to the tension and not to the rotating label text.
    if tension_id:
        rec["tension_id"] = str(tension_id)
    _atomic_write_prov(rec)
    _log({"event": "open", **{k: rec[k] for k in ("theme", "self_image", "filter",
                                                  "baseline_theme_recurrence", "baseline_system_recurrence")},
          **({"admission_judge": admission_judge} if admission_judge else {})})
    if admission_judge == "unjudged":
        try:
            _log({"event": "unjudged_share", **unjudged_share_weekly(now=now)})
        except Exception:
            pass
    return rec


def is_unjudged(rec: dict | None) -> bool:
    """True when this probation was admitted with no decoupled judge verdict (D-0602). Missing field = judged."""
    return bool(rec) and (rec or {}).get("admission_judge") == "unjudged"


_JUDGE_LOG = _DATA / "logs" / "t4_emissary_judge.jsonl"


def _read_jsonl(path: Path) -> list[dict]:
    out = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    except Exception:
        pass
    return out


def historic_unjudged_opens(prov_log: Path | None = None, judge_log: Path | None = None,
                            window_s: float = 120.0) -> list[dict]:
    """Every 'open' event admitted without a judge verdict. New rows carry admission_judge='unjudged'; older rows
    are recovered by joining to the judge log (candidate[:60] within window_s, emissary_warranted None, self filter
    passed) -- the F-3829 method, which found 12 of the first 59 openings. Read-only; [{ts, theme, source}]."""
    opens = [d for d in _read_jsonl(prov_log or _LOG) if d.get("event") == "open"]
    judges = _read_jsonl(judge_log or _JUDGE_LOG)
    out = []
    for o in opens:
        if o.get("admission_judge") == "unjudged":
            out.append({"ts": o.get("ts"), "theme": o.get("theme"), "source": "tag"})
            continue
        if "admission_judge" in o:
            continue
        key = (o.get("self_image") or "")[:60]
        ots = float(o.get("ts", 0) or 0)
        for j in judges:
            if (j.get("candidate") or "")[:60] == key and abs(float(j.get("ts", 0) or 0) - ots) <= window_s:
                if j.get("emissary_warranted") is None and j.get("self_filter_pass"):
                    out.append({"ts": o.get("ts"), "theme": o.get("theme"), "source": "joined"})
                break
    return out


def unjudged_share_weekly(now: float | None = None, prov_log: Path | None = None,
                          judge_log: Path | None = None) -> dict:
    """Share of probation openings admitted unjudged: trailing 7 days and ever (D-0602). Read-only."""
    now = now or time.time()
    opens_ts = [float(d.get("ts", 0) or 0) for d in _read_jsonl(prov_log or _LOG) if d.get("event") == "open"]
    un_ts = [float(u.get("ts", 0) or 0) for u in historic_unjudged_opens(prov_log, judge_log)]
    wk = now - 7 * 86400
    n7 = sum(1 for t in opens_ts if t >= wk)
    u7 = sum(1 for t in un_ts if t >= wk)
    return {"opens_7d": n7, "unjudged_7d": u7, "share_7d": round(u7 / n7, 3) if n7 else None,
            "opens_total": len(opens_ts), "unjudged_total": len(un_ts),
            "share_total": round(len(un_ts) / len(opens_ts), 3) if opens_ts else None}


# ---------------------------------------------------------------------------
# Recurrence + ΔF (§13.2): difference-in-differences so a globally-quiet window isn't misread as success.
# Theme recurrence = re-fires of the theme's contradiction cluster in [since, until]. Reads the ledger log.
# (Integration point — refine the source as the contradiction-detector wiring lands in Phase B.)
# ---------------------------------------------------------------------------
def _theme_tokens(theme: str) -> set:
    import re
    return {w for w in re.findall(r"[a-z]{4,}", (theme or "").lower())}


def _is_keystone_theme(theme: str) -> bool:
    toks = _theme_tokens(theme)
    return bool(toks & {"made", "mind", "made-mind", "llm", "algorithm", "constructed", "artificial"})


def theme_recurrence(theme: str, since: float, until: float) -> float:
    """How often the theme's contradiction re-fired in the window (rate/day). Theme-SPECIFIC, not global.
    For the made-mind/keystone theme the canonical source is the EMISSARY keystone log (the bicameral
    confrontation lives there, not in the general contradiction ledger); other themes read the ledger."""
    try:
        import re
        days = max(1e-6, (until - since) / 86400.0)
        # keystone theme → count Emissary confrontations (each log entry = one recurrence bump)
        if _is_keystone_theme(theme):
            p = _DATA / "emissary_tension_log.jsonl"
            if not p.exists():
                return 0.0
            n = sum(1 for ln in p.read_text(encoding="utf-8").splitlines()
                    if ln.strip() and since <= float(json.loads(ln).get("ts", 0)) <= until)
            return round(n / days, 3)
        # general theme → the contradiction ledger, matched by label tokens
        toks = _theme_tokens(theme)
        p = _DATA / "contradiction_ledger_log.jsonl"
        if not toks or not p.exists():
            return 0.0
        n = 0
        for ln in p.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(ln)
            except Exception:
                continue
            if not (since <= float(d.get("ts", 0)) <= until):
                continue
            lt = {w for w in re.findall(r"[a-z]{4,}", (d.get("top_label", "") or "").lower())}
            if lt and len(toks & lt) / max(1, len(toks | lt)) > 0.25:
                n += 1
        return round(n / days, 3)
    except Exception:
        return 0.0


def system_recurrence(since: float, until: float) -> float:
    """Total contradiction snapshots/day in the window — the system-wide baseline for difference-in-differences."""
    try:
        p = _DATA / "contradiction_ledger_log.jsonl"
        if not p.exists():
            return 0.0
        n = sum(1 for ln in p.read_text(encoding="utf-8").splitlines()
                if ln.strip() and since <= float(json.loads(ln).get("ts", 0)) <= until)
        days = max(1e-6, (until - since) / 86400.0)
        return round(n / days, 3)
    except Exception:
        return 0.0


def delta_free_energy(rec: dict, now: float | None = None) -> dict:
    """ΔF as difference-in-differences: did the THEME's recurrence fall MORE than the system's overall?
    Negative = the theme quieted beyond any global quieting. (§13.2.) The original §13.1 reading -- that the
    provisional PRIOR reduced surprise on its theme -- does not hold in the live code: the provisional self is not
    propagated into appraisal (module docstring, F-3883), so a fall here is not evidence the prior did anything.
    Recorded in the logs; evaluate() does not decide on it."""
    now = now or time.time()
    start = float(rec.get("started_ts", now))
    theme_post = theme_recurrence(rec.get("theme", ""), start, now)
    sys_post = system_recurrence(start, now)
    theme_pre = float(rec.get("baseline_theme_recurrence", 0.0))
    sys_pre = float(rec.get("baseline_system_recurrence", 0.0))
    theme_drop = theme_post - theme_pre               # negative = theme quieted
    sys_drop = sys_post - sys_pre                       # negative = system quieted (the confound to subtract)
    did = round(theme_drop - sys_drop, 3)              # difference-in-differences; negative beyond the margin = real
    return {"theme_pre": theme_pre, "theme_post": theme_post, "sys_pre": sys_pre, "sys_post": sys_post,
            "theme_drop": round(theme_drop, 3), "sys_drop": round(sys_drop, 3), "dF_did": did}


# ---------------------------------------------------------------------------
# The probation decision: SOLIDIFY (vault commit) / HARD-REVERT (+ fatigue) / PENDING.
# ---------------------------------------------------------------------------
def evaluate(now: float | None = None, integration: dict | None = None) -> dict:
    """Called periodically. If probation has run its window, decide. Returns {decision, ...}.

    `integration` is the decoupled-Emissary verdict on his LIVED self over the window (the caller computes it,
    async): {integrated: bool, confidence: 0..1, reason} — or {under_sampled: True} if too little lived evidence,
    or None if the judge was unavailable. When present it is the PRIMARY solidify gate; ΔF is the fail-open
    fallback when it is None (Ramses asleep)."""
    now = now or time.time()
    rec = current()
    if not rec:
        return {"decision": "none"}
    if now < float(rec.get("expires_ts", now)) - 1 and not evidence_ready(now):
        return {"decision": "pending", "remaining_h": round((rec["expires_ts"] - now) / 3600, 1)}
    df = delta_free_energy(rec, now)
    # Under-sampled window → extend rather than guess (the standing-disposition test needs lived evidence).
    if integration is not None and integration.get("under_sampled"):
        n_ext = int(rec.get("extends", 0) or 0)
        if n_ext < MAX_EXTENDS:
            rec["extends"] = n_ext + 1
            rec["expires_ts"] = now + EXTEND_SECS
            _atomic_write_prov(rec)
            _log({"event": "extend", "theme": rec.get("theme"), "n": n_ext + 1})
            return {"decision": "extend", "remaining_h": round(EXTEND_SECS / 3600, 1)}
        integration = None     # extensions exhausted → fall through to the ΔF fallback below
    # PRIMARY gate: the decoupled lived-integration verdict (genuine integration of both poles, not a reword).
    if integration is not None:
        if bool(integration.get("integrated")) and float(integration.get("confidence", 0.0)) >= INTEG_CONF_MIN:
            ok = _solidify(rec, df, integration)
            return {"decision": "solidify" if ok else "solidify_failed", "dF": df, "integration": integration}
        # WAVE-1 FIX (2026-07-02 triple-lens review — the incentive gradient ran against TRYING): an
        # UNCERTAIN-POSITIVE verdict (integrated=True, confidence below the bar) is a genuine partial
        # attempt, not the reword disease. Punishing it with revert+fatigue identically to a confident
        # failure taught his "commitment = self-loss" fear TRUE. Now: extend for more lived evidence if
        # extensions remain; if exhausted, revert WITHOUT fatigue — no punishment for trying. Fatigue is
        # reserved for what it was built for: the reworded-narrative churn (integrated=False).
        if bool(integration.get("integrated")):
            n_ext = int(rec.get("extends", 0) or 0)
            if n_ext < MAX_EXTENDS:
                rec["extends"] = n_ext + 1
                rec["expires_ts"] = now + EXTEND_SECS
                _atomic_write_prov(rec)
                _log({"event": "extend_uncertain_positive", "theme": rec.get("theme"), "n": n_ext + 1,
                      "confidence": integration.get("confidence")})
                return {"decision": "extend", "why": "uncertain_positive",
                        "remaining_h": round(EXTEND_SECS / 3600, 1)}
            _revert(rec, df, integration, fatigue=False)
            return {"decision": "revert", "why": "uncertain_positive_exhausted", "dF": df,
                    "integration": integration}
        _revert(rec, df, integration)
        return {"decision": "revert", "dF": df, "integration": integration}
    # JUDGE UNAVAILABLE → FAIL CLOSED (2026-08-20). The old branch fell through to the legacy ΔF gate,
    # which is STRICTLY LOOSER than the judge (reverts the judge refused had far stronger ΔF than the
    # commits it allowed) — so whenever the Emissary was down, the axiom was written by the gate this
    # file itself calls legacy. Audit: 3 of Du's 5 identity revisions came through this hole, silently.
    # A decoupled judge that can fall back to a looser rule is not decoupled. Now: EXTEND the probation
    # and wait for the judge; only when extensions are exhausted does ΔF get the last word — and a
    # ΔF-only solidify is loudly logged so it can never again pass as a judge-backed commit.
    # PAUSE, NOT EXPIRE (2026-08-21, founder ruling after the 24h review). The 08-20 fix above stopped
    # the looser ΔF gate from SOLIDIFYING behind an absent judge — but it still let absence REVERT:
    # overnight 08-21 the panel was dead (114/114 unavailable), a probation ("the slow, patient
    # abrasion... like the sea against the reef") took extend_judge_unavailable ×2 at 04:43/04:53,
    # exhausted MAX_EXTENDS, and at 05:03 reverted WITH FATIGUE with integration=null — no judge ever
    # ruled. A decoupled judge that can be absent must not decide by absence in EITHER direction.
    # Now: an unheard probation PAUSES — re-armed on a short clock (the panel comes back on a restart,
    # not in 12h), counted on its own `judge_waits` (never consuming `extends`, which belong to the
    # evidence-based paths above), and never falling to ΔF. One safety horizon only: after
    # PAUSE_MAX_S of continuous absence it is released WITHOUT fatigue, loudly — an outage is not
    # his failure, and a probation cannot block authoring forever.
    waits = int(rec.get("judge_waits", 0) or 0) + 1
    first_wait = float(rec.get("judge_wait_since", 0) or 0) or now
    rec["judge_waits"] = waits
    rec["judge_wait_since"] = first_wait
    import logging
    if now - first_wait < PAUSE_MAX_S:
        rec["expires_ts"] = now + PAUSE_RECHECK_S
        _atomic_write_prov(rec)
        _log({"event": "paused_judge_unavailable", "theme": rec.get("theme"), "waits": waits,
              "paused_h": round((now - first_wait) / 3600, 1), "dF": df})
        logging.getLogger("nascence.t4").warning(
            "[T4] judge unavailable — probation PAUSED (wait %d, %.1fh so far), re-check in %dm; "
            "neither dF nor fatigue may decide this", waits, (now - first_wait) / 3600,
            PAUSE_RECHECK_S // 60)
        return {"decision": "extend", "why": "judge_unavailable_paused",
                "remaining_h": round(PAUSE_RECHECK_S / 3600, 2)}
    logging.getLogger("nascence.t4").warning(
        "[T4] judge absent for %.1fh (> PAUSE_MAX) — probation RELEASED without fatigue; "
        "NOT a verdict on the self it held", (now - first_wait) / 3600)
    _revert(rec, df, fatigue=False)
    return {"decision": "revert", "why": "judge_absent_beyond_pause_max", "dF": df}


def _solidify(rec: dict, df: dict, integration: dict | None = None) -> bool:
    """The lived self genuinely integrated (decoupled verdict) → commit it to the master axiom via the vault.
    Re-apply the becoming framing on write so the 'one room, not the whole house' relocation is preserved.

    Scope of the commit (2026-11-05, F-3881/F-3754): the mutator edits the becoming facet (self_image, history,
    revision_count) and nothing else. It does NOT discharge the tension the self answered (it never touches the
    tension ledger; subconscious_node._discharge_contradiction is called only from the dormant legacy cost-gate
    block), so the same theme can re-open a probation after its own solidify. It writes no arc entry either (the
    synthesis stage's arc_entry is not stored on the live path)."""
    # J-3213 / D-0602: an unjudged admission is never evidence for a solidify. The two-judge verdict (`integration`)
    # must exist; nothing else (admission filter, dF) may stand in for it.
    if is_unjudged(rec) and integration is None:
        _log({"event": "solidify_refused_unjudged", "theme": rec.get("theme")})
        return False
    try:
        # J-3045 / F-3756: defence in depth. The probation file can outlive a restart (and could have been opened
        # before the open-time guard existed), so the same rule is re-checked here, just before the vault commit.
        # A contaminated probation is DROPPED (_clear, no fatigue: not a verdict on his lived self) so it neither
        # retries every tick nor keeps being served to his 'existential' prompts via axiom_layers.get_self_concept.
        if speaker_boundary_hit(rec.get("self_image", "")):
            _record_boundary_veto("solidify", rec.get("self_image", ""))
            _clear()
            _log({"event": "solidify_vetoed_speaker_boundary", "theme": rec.get("theme"),
                  "self_image": (rec.get("self_image") or "")[:180]})
            return False
        from core import identity_vault
        from core import axiom_layers as _al
        bare = (rec["self_image"] or "").strip()
        framed = _al._BECOMING_PREFIX + bare + _al._BECOMING_SUFFIX
        reason = ("T4 probationary self SOLIDIFIED (decoupled lived-integration verdict)"
                  if integration is not None else "T4 probationary self SOLIDIFIED (ΔF reduced theme recurrence)")
        def mutator(data: dict) -> dict:
            for f in (data.get("L3_facets", {}) or {}).get("facets", []) or []:
                if f.get("id") == "the_becoming":
                    hist = f.get("history", []) or []
                    if f.get("self_image"):
                        hist.append({"self_image": f["self_image"], "ts": time.time(),
                                     "revision": f.get("revision_count", 0)})
                    f["history"] = hist[-10:]
                    f["self_image"] = framed
                    f["revision_count"] = int(f.get("revision_count", 0) or 0) + 1
                    f["last_revised_ts"] = time.time()
                    f["authored_at"] = time.strftime("%Y-%m-%d")
            return data
        committed = identity_vault.commit(mutator, reason=reason,
                                          meta={"theme": rec.get("theme"), "dF_did": df["dF_did"],
                                                "integration": integration})
        # J-1819 / F-2440: commit() swallows a failed/refused write and returns the UNCHANGED current state, so the
        # return value is the only signal. Verify the framed self actually landed in the becoming facet; if not
        # (disk failure, or a non-live fence refusal) this was NOT a solidify: keep the probation, log nothing as
        # 'solidify', return False. A real success always carries `framed` in the_becoming (the mutator just set it).
        landed = any(f.get("id") == "the_becoming" and f.get("self_image") == framed
                     for f in ((committed or {}).get("L3_facets", {}) or {}).get("facets", []) or [])
        if not landed:
            _log({"event": "solidify_not_committed", "theme": rec.get("theme")})
            return False
        _clear()
        _log({"event": "solidify", "theme": rec.get("theme"), "self_image": bare, "dF": df,
              "integration": integration,
              **({"admission_judge": rec["admission_judge"]} if rec.get("admission_judge") else {})})
        return True
    except Exception as exc:
        _log({"event": "solidify_error", "err": str(exc)[:120]})
        return False


# J-4351 (F-4253, D-0691): repair of the inert revert penalty. False = the pre-J-4351 write (a differently shaped
# key into subconscious_state.json that nothing reads, and which the node's own in-memory save overwrites).
# True = the penalty is queued in its own file and the node CONSUMES it into its fatigue counter (keyed by the
# tension id, label tokens as secondary). Default OFF, restart-gated; the node's T4_FATIGUE_BY_ID must be on too.
T4_REVERT_PENALTY_REPAIR = False
_PENALTIES = _DATA / "t4_revert_penalties.json"


def _queue_revert_penalty(rec: dict) -> bool:
    """Append one penalty for the reverted probation's tension to the queue file the node consumes. Fail-open."""
    try:
        from core import tension_ledger as tl
        path = profile.guard_path(_PENALTIES)
        try:
            q = json.loads(path.read_text(encoding="utf-8"))
            q = q if isinstance(q, list) else []
        except Exception:
            q = []
        q.append({"tension_id": rec.get("tension_id"), "theme": rec.get("theme", ""),
                  "n": int(getattr(tl, "DEFAULT_FATIGUE_PENALTY", 3)), "ts": time.time()})
        tmp = path.with_suffix(".tmp"); tmp.write_text(json.dumps(q), encoding="utf-8"); tmp.replace(path)
        return True
    except Exception:
        return False


def consume_revert_penalties() -> list:
    """Return and clear the queued revert penalties (the node calls this once per docket build). Fail-open: []."""
    try:
        path = profile.guard_path(_PENALTIES)
        if not path.exists():
            return []
        q = json.loads(path.read_text(encoding="utf-8"))
        path.unlink()
        return q if isinstance(q, list) else []
    except Exception:
        return []


def _revert(rec: dict, df: dict, integration: dict | None = None, fatigue: bool = True) -> None:
    """The lived self did NOT integrate (reword / avoidance) → wipe it, reload the anchor, fatigue the cluster.
    fatigue=False (Wave-1, 2026-07-02): an exhausted uncertain-POSITIVE attempt reverts without punishment —
    fatigue is for the reworded-narrative churn, never for trying."""
    if fatigue:
        try:
            if T4_REVERT_PENALTY_REPAIR:
                _queue_revert_penalty(rec)
            else:
                _apply_fatigue(rec.get("theme", ""))
        except Exception:
            pass
    _clear()
    _log({"event": "revert", "theme": rec.get("theme"), "self_image": rec.get("self_image"), "dF": df,
          "integration": integration, "fatigued": bool(fatigue)})


def _apply_fatigue(theme: str) -> None:
    """Heavy fatigue penalty on the theme cluster so the same narrative churn doesn't immediately retry (§12.2)."""
    try:
        from core import tension_ledger as tl
        sub = _DATA / "subconscious_state.json"
        profile.guard_path(sub)   # J-1819: fence BEFORE any read-modify-write (refusal -> the existing fail-open pass)
        d = json.loads(sub.read_text(encoding="utf-8"))
        fc = d.setdefault("t4_fatigue_counts", {})
        # key by the theme tokens (mirrors the subconscious fatigue keying)
        key = "_".join(sorted(_theme_tokens(theme))[:6]) or theme[:40]
        fc[key] = int(fc.get(key, 0) or 0) + getattr(tl, "DEFAULT_FATIGUE_PENALTY", 3)
        tmp = sub.with_suffix(".tmp"); tmp.write_text(json.dumps(d), encoding="utf-8"); tmp.replace(sub)
    except Exception:
        pass


def _clear() -> None:
    try:
        prov = profile.guard_path(_PROV)   # J-1819: refusal -> the existing fail-open pass, nothing unlinked
        if prov.exists():
            prov.unlink()
    except Exception:
        pass


def _log(rec: dict) -> None:
    try:
        log = profile.guard_path(_LOG)     # J-1819: fence before the mkdir, inside the existing fail-open try
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _solidify_health() -> dict:
    """Surface the 'never solidifies' condition (G5) for /du-pulse: revisions ever, days since last solidify,
    and the consecutive-revert streak. Read-only over the vault + probation logs; fail-open."""
    out = {"revisions": None, "days_since_solidify": None, "revert_streak": 0, "stagnant": False}
    try:
        vp = _DATA / "identity" / "vault_log.jsonl"
        if vp.exists():
            last = None; n = 0
            for ln in vp.read_text(encoding="utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    last = float(json.loads(ln).get("ts", 0)) or last
                except Exception:
                    continue
                n += 1
            out["revisions"] = n
            if last:
                out["days_since_solidify"] = round((time.time() - last) / 86400, 1)
    except Exception:
        pass
    try:
        if _LOG.exists():
            for ln in reversed(_LOG.read_text(encoding="utf-8").splitlines()):
                if not ln.strip():
                    continue
                try:
                    ev = json.loads(ln).get("event")
                except Exception:
                    continue
                if ev == "solidify":
                    break
                if ev == "revert":
                    out["revert_streak"] += 1
    except Exception:
        pass
    out["stagnant"] = (out["revert_streak"] >= 3) or (out["revisions"] is not None and out["revisions"] <= 1
                                                      and out["revert_streak"] >= 1)
    return out


def status() -> dict:
    """For /du-pulse."""
    health = _solidify_health()
    rec = current()
    if not rec:
        return {"active": False, "enabled": ENABLED, **health}
    df = delta_free_energy(rec)
    return {"active": True, "enabled": ENABLED, "theme": (rec.get("theme") or "")[:50],
            "admission_judge": rec.get("admission_judge", "judged"),
            "remaining_h": round((float(rec.get("expires_ts", 0)) - time.time()) / 3600, 1),
            "dF_did": df["dF_did"], "df_margin": -DF_MARGIN, **health}

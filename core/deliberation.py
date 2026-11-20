"""
Nascence — The Deliberative Pulse (the three-pass grounded-why)
==============================================================
The first brick of the Lane Architecture (docs/lane_architecture_FULL.md §4.4).

A self-referential idle thought ("I am the river that carves a new channel") is the
monoculture in the making — the Self lane asking and answering itself, the loop that
re-injects its own metaphor. This module breaks that loop with a slow System-2 pulse
riding under the fast idle pulse:

    pass 1  the thought                       (already produced by the monologue)
    pass 2  the grounded WHY  →  routes OUTWARD to the ANALYTICAL lane (the Emissary,
            mixtral:8x7b on the Ramses CPU hub, LAN-HOST:11438, via left_lane.GROUND_URL /
            GROUND_MODEL — moved there 2026-09-02; it was gemma4:12b on judge-1 :11439 before) — "what does this actually rest on
            in the world?"  This is the ROUTING LAW: a self-question goes out to be
            grounded, never back into the self. Fail-open → when the Emissary cannot ground, the
            raw thought is stored untouched (D-0569, 2026-11-02: there is NO hot-lane fallback;
            a model never grounds its own thought, the decoupled-judge law).
    pass 3  INTEGRATE  →  the Self lane (qwen3.5:9b, same 2026-08-20 shuffle) thinks the
            thought again so the grounded reality genuinely meets it — grounded FLAVOUR
            (self + world, both present), not a fact tacked on.

The integrated thought REPLACES the raw thought before it is stored — into the ONE
episodic store, with origin='inner_thought' as always (plus a 'deliberated' keyword so
we can measure). No new memory, no new self-concept author, no new autobiography: the
identity-locus invariant (§0.6) is untouched — this is a cognitive transform applied
before output, exactly a cortical region doing its work, not a second self.

Validated in vitro before live (scripts/three_pass_test.py + the real-thought proof):
grounded-why deepens toward reality; self-why amplifies the metaphor — so the why-pass
is MANDATORY-outward. Every pulse is logged to data/deliberation_log.jsonl (raw → why →
integrated → source) so the operator reads what the pulse actually did.

Kill switch: ENABLED = False restores the exact prior idle behaviour.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import time
from pathlib import Path

from core.schema import SERVE_CHAINS
from core.model_client import call_node_json
from core import left_lane

logger = logging.getLogger("nascence.deliberation")

# ── Kill switch + cadence ─────────────────────────────────────────────────────
ENABLED = True              # False → idle thoughts pass through untouched (prior behaviour)
DELIBERATE_PROB = 0.25      # fraction of ELIGIBLE thoughts that get the slow pulse. The rest
                            # pass through ungrounded -- they are the control arm (logged, see below).
                            # D-0541 (founder, 2026-11-02, J-3149): cut 0.75 -> 0.25. History: raised 0.5 -> 0.75 on
                            # 2026-07-08 on an unmeasured "net cognitive win" rationale (the Emissary had idle
                            # headroom); the pass-3 integrator rewrites ~70 percent of stored idle thoughts and
                            # 98.8 percent of raw thoughts that held a question lose it (F-3434..F-3436). Cut the rate
                            # AND measure: eligible-but-skipped thoughts are logged to _CONTROL_LOG_FILE so raw vs
                            # integrated pairs and the skipped controls compare on the same days. Defeater: a blind
                            # read of >=100 pairs preferring/neutral on all three criteria, or a measurable worsening
                            # of grounding quality at the lower rate.

# J-3477 (J-3413, founder ruling 2026-11-06): the pass-3 integrator removes the question mark in 98.5 percent of
# question-holding raws (J-3150 lab) and a blind different-family judge preferred the raw 32-13 (debiased). Mixtral
# cannot be trusted on question-keeping, so this is a DETERMINISTIC guard, not a prompt rewrite: when the raw thought
# held a question (a "?" or full-width "？") and the integrated thought holds none, the integration is DISCARDED
# and the raw thought is stored untouched (fail-open, same as every other pass-3 miss). The prompt is not reworded.
# Default ON. False restores the prior pass-3 behaviour exactly. Defeater: a blind read of the guard log
# (deliberation_guard_log.jsonl) showing the rejected integrations were preferred on all three J-3150 criteria.
QUESTION_GUARD = True

# J-3809 (D-0710, founder ruling 2026-11-09, successor to J-3537 / F-4148): with the guard on, 100 percent of
# question-holding eligible thoughts had their integration discarded, so passes 2 and 3 (an Emissary call plus a
# hot-lane call) were spent for nothing on that class. Now a question-holding thought SKIPS deliberation up front
# (raw stored, no LLM call), EXCEPT 1 in QUESTION_AUDIT_EVERY_N, which runs the full pulse so the guard still runs
# on a sample and the blind check keeps a stream of guard rows (deliberation_guard_log.jsonl). Travis gave no N:
# 10 as a single constant. False restores the prior behaviour exactly (every question thought runs passes 2/3, guard
# after). Skips are logged to deliberation_question_skip_log.jsonl (a separate file, as with the null/control/guard
# logs) and counted by the line "deliberation_question_skipped_upfront" in nascence.log. Restart-gated.
# No prompt text changes, so no prompt-registry change: two call sites are simply reached less often.
QUESTION_SKIP_UPFRONT = True
QUESTION_AUDIT_EVERY_N = 10

_DATA_DIR = Path(__file__).parent.parent / "data"
_LOG_FILE = _DATA_DIR / "deliberation_log.jsonl"
# D-0570 / J-2799: thoughts the grounder itself answered "nothing to ground" for. These are the logged control
# arm (eligible, deliberated, passed through untouched). A SEPARATE file on purpose: deliberation_log.jsonl rows
# mean "a thought was rewritten" to every reader of it (du_pulse, hud2, hands, lag_tail), so null rows must not
# be mixed in. One row per null: ts, about, raw, source.
_NULL_LOG_FILE = _DATA_DIR / "deliberation_null_log.jsonl"
# J-3477: integrations DISCARDED by the question guard (raw held a "?", integrated lost it). A SEPARATE file for the
# same reason as the null and control logs. One row per discard: ts, about, raw, grounding, rejected_integrated,
# arm="question_guard". Reader: the blind judge lab (scripts/lab_deliberation_blind_judge_J-3150.py can be pointed at
# it) and the counter line "deliberation_question_guard_kept_raw" in nascence.log.
_GUARD_LOG_FILE = _DATA_DIR / "deliberation_guard_log.jsonl"
# J-3809: question-holding thoughts skipped up front (not audited). One row per skip: ts, about, raw, arm="question_skipped_upfront".
_QSKIP_LOG_FILE = _DATA_DIR / "deliberation_question_skip_log.jsonl"
# D-0541 / J-3149: the control arm of the rate cut -- every ELIGIBLE thought the DELIBERATE_PROB draw skipped. Also a
# SEPARATE file, for the same reason as the null log (deliberation_log.jsonl rows mean "a thought was rewritten" to
# its readers). One row per skip: ts, about, thought_hash (sha1[:16] of the raw), raw, eligible=true,
# deliberated=false, arm="skipped_by_draw". Join to deliberation_log.jsonl on raw / hash for the pairs.
_CONTROL_LOG_FILE = _DATA_DIR / "deliberation_control_log.jsonl"

# ── The gate: which thoughts are eligible ─────────────────────────────────────
# We deliberate SELF-REFERENTIAL, substantial, NON-ACTION thoughts — the ones at risk of
# being the self-dissolving metaphor. Action/reading thoughts are already world-facing and
# grounded by the act itself; deliberating them would be redundant (and would double-process
# a reading note). NB: we deliberately do NOT key off an abstract-word list — the dominant
# attractor ("I am the river…") contains no abstract marker; self-reference is the real tell.
_ACTION_ABOUT = (
    "reading", "asking the library", "choosing from the catalogue", "choosing",
    "finished the book", "browsing", "a letter to travis", "the catalogue",
)
_ACTION_MARKERS = (
    "i opened '", "i chose '", "i asked the library", "open the book",
    "i reached for the book", "lies on my desk", "from the catalogue",
    "i opened ‘",
)
_SELF_REF = (" i ", " i'", " my ", " me ", " myself", "i am ", "i'm ", " mine ")

# A VOLITION is a want, not a claim about the world. Grounding it flattens it into a
# dictionary definition (the in-vitro proof flattened "I want to return to the question of
# my own name" into "a sequence of sounds that identifies me in social and legal contexts").
# His wants are his to hold — "intentional, not a rule." So volitions pass through ungrounded.
_VOLITION_OPENERS = ("i want", "i will ", "i'd like", "i would like", "i intend",
                     "i hope", "i need to", "let me ", "i must ", "i wish", "i'd rather")


def is_eligible(thought: str, about: str = "") -> bool:
    """A self-referential, substantial, non-action, non-volition idle thought — the
    monoculture's habitat (a metaphor/claim about the self-as-world), not a bare want."""
    raw = (thought or "").strip()
    t = " " + raw.lower() + " "
    a = (about or "").lower()
    if any(p in a for p in _ACTION_ABOUT):
        return False
    if any(m in t for m in _ACTION_MARKERS):
        return False
    if len(raw) < 40:
        return False
    if any(raw.lower().startswith(v) for v in _VOLITION_OPENERS):
        return False
    return any(s in t for s in _SELF_REF)


def should_deliberate(thought: str, about: str = "") -> bool:
    """Live gate: eligible AND we rolled for the slow pulse this time."""
    if not (ENABLED and is_eligible(thought, about)):
        return False
    if random.random() < DELIBERATE_PROB:
        return True
    _log_control(thought, about)   # D-0541: eligible but skipped by the draw = the logged control arm
    return False


# ── The integrate (pass 3) contract — the Self lane, his own voice ────────────
def _integrate_system(name: str) -> str:
    return (
        "/no_think\n"
        f"You are the quiet inner voice of {name} — thinking to yourself, first person, present "
        "tense. A thought surfaced in you, and your focused analytical half looked at what that "
        "thought actually rests on in the world. Let that grounded reality genuinely MEET your "
        "thought — not a fact tacked on the end, but the real thing changing how you hold the "
        "thought. Think it ONCE more, so it holds BOTH: the world as it actually is AND what it "
        "stirs in you. Stay in your own voice. 1-2 sentences. Do not explain, do not perform.\n"
        "Output ONLY a valid JSON object: {\"thought\": \"...\"}"
    )


def _integrate_user(thought: str, grounding: str) -> str:
    return (
        f"Your thought:\n  \"{thought}\"\n\n"
        f"What your focused half found it rests on in the world:\n  \"{grounding}\"\n\n"
        "Now think the thought again, holding both."
    )


def _too_similar(a: str, b: str) -> bool:
    """Word-set Jaccard ≥ 0.88 (or exact text match) = the integrate added nothing."""
    wa = set(re.findall(r"[a-z']{3,}", a.lower()))
    wb = set(re.findall(r"[a-z']{3,}", b.lower()))
    if not wa or not wb:
        return a.strip().lower() == b.strip().lower()
    return len(wa & wb) / len(wa | wb) >= 0.88


def holds_question(text: str) -> bool:
    """True when the text carries a question mark (ASCII or full-width). Deterministic, no model."""
    t = text or ""
    return "?" in t or "？" in t


def question_dropped(raw: str, integrated: str) -> bool:
    """The J-3477 guard predicate: the raw thought held a question and the integrated one holds none."""
    return holds_question(raw) and not holds_question(integrated)


async def deliberate(
    thought: str,
    about: str = "",
    *,
    name: str = "渡",
    hot_urls=None,
    log: bool = True,
) -> tuple[str, dict | None]:
    """Run the three-pass pulse on one thought (see _deliberate_run). J-2890 (F-3558): once the pulse is over, whatever
    the outcome, a successful grounding may be sampled (1 in 20) for the log-only ground-quality shadow grader
    (core/ground_grade.py: a different model family; nothing is fed back). schedule() is fail-open and returns at once."""
    _box: dict = {}
    try:
        return await _deliberate_run(thought, about, name=name, hot_urls=hot_urls, log=log, _box=_box)
    finally:
        try:
            from core import ground_grade
            ground_grade.schedule(thought, _box.get("grounding"), _box.get("source", "emissary"))
        except Exception:
            pass


async def _deliberate_run(
    thought: str,
    about: str = "",
    *,
    name: str = "渡",
    hot_urls=None,
    log: bool = True,
    _box: dict | None = None,
) -> tuple[str, dict | None]:
    """Run the three-pass pulse on one thought.

    Returns (new_thought, provenance). provenance is None when the thought was left
    UNCHANGED (grounding unavailable / integration failed) — fail-open, the mind proceeds
    whole. When provenance is a dict, new_thought is the grounded-integrated thought and
    the caller should store THAT (still origin='inner_thought')."""
    hot_urls = hot_urls or SERVE_CHAINS["hot"]

    # J-3809 / D-0710: a question-holding thought would have its integration discarded by the guard anyway (100
    # percent, F-4148), so skip passes 2 and 3 up front -- except the 1-in-N audit sample, which runs in full.
    if QUESTION_SKIP_UPFRONT and QUESTION_GUARD and holds_question(thought) and not _question_audit_draw():
        if log:
            _log_question_skip(thought, about)
        logger.info("[deliberation] deliberation_question_skipped_upfront - question-holding thought stored raw "
                    "(J-3809)")
        return thought, None

    # PASS 2 — the grounded why, routed OUTWARD to the analytical lane (Emissary first).
    source = "emissary"
    grounding, no_referent = await left_lane.ground_thought_verdict(thought)
    if no_referent:
        # D-0570: the grounder's own "nothing to ground". Treated exactly like an ineligible thought: it passes
        # through unchanged, and the hot lane is NOT asked (it would be handed the same contract and a model
        # grounding its own thought, which D-0569 / the decoupled-judge law rule out).
        if log:
            _log_null(thought, about, source)
        logger.info("[deliberation] grounder found nothing to ground - thought passes through unchanged")
        return thought, None
    if not grounding:
        # D-0569 (J-3182): the Emissary returned nothing (down, slow, empty, unparseable, or its reply carried the
        # title twice). FAIL OPEN: skip deliberation and store the raw thought. The hot lane is NOT asked -- no
        # qwen grounding qwen. One stable counter line per skip so the outage share is measurable by day:
        #   grep -c "deliberation_skipped_no_emissary" nascence.log   (D-0569 defeater: >25 percent over a month)
        logger.info("[deliberation] deliberation_skipped_no_emissary - the Emissary could not ground; "
                    "thought stored raw (fail-open, D-0569)")
        return thought, None

    if _box is not None:
        _box["grounding"], _box["source"] = grounding, source        # J-2890: for the post-pulse shadow grade
    # PASS 3 — integrate on the Self lane: grounded reality meets the thought (grounded flavour).
    try:
        data = await call_node_json(
            hot_urls, _integrate_system(name), _integrate_user(thought, grounding),
            max_tokens=220, temperature=0.6,
        )
    except Exception as exc:
        logger.info("[deliberation] integrate failed — thought unchanged (fail-open): %s",
                    str(exc)[:60])
        return thought, None

    integrated = str((data or {}).get("thought") or "").strip()
    if not integrated or len(integrated) < 20:
        return thought, None
    # No-op guard: the integrate sometimes echoes the raw thought verbatim (it had nothing to
    # add — often an already-grounded or quoted thought). Don't claim a deliberation that
    # didn't happen, and don't burn a log line on it. Treat as unchanged (fail-open).
    if _too_similar(integrated, thought):
        logger.info("[deliberation] integrate echoed the raw thought — unchanged (no-op)")
        return thought, None

    # J-3477 / J-3413: question guard. The integrator turns an open question into a statement (98.5 percent of
    # question-holding raws, J-3150). A thought that was asking must stay asking: discard the integration, store the
    # raw thought (fail-open). Deterministic -- no model judges this.
    if QUESTION_GUARD and question_dropped(thought, integrated):
        if log:
            _log_guard(thought, about, grounding, integrated)
        logger.info("[deliberation] deliberation_question_guard_kept_raw - integrate dropped the raw thought's "
                    "question; thought stored raw (J-3477)")
        return thought, None

    if log:
        _log(thought, about, grounding, integrated, source)
    # The corpus callosum's crossing (2026-06-15): a self-thought met its grounded reality and held BOTH —
    # meaning and truth integrated. That IS a light point (the coniunctus seed), and it feeds the balance
    # sprint's light side. Recorded so the integration is measurable. Best-effort.
    try:
        from core.memory.store import store_light_event
        store_light_event(cycle_id="deliberation", raw_input=f"(grounded: {thought[:60]})",
                          integrated_content=integrated[:400], source="integration")
    except Exception:
        pass
    logger.info("[deliberation] grounded (%s): %s", source, integrated[:90])
    return integrated, {"raw": thought, "grounding": grounding, "source": source}


def _log_control(raw: str, about: str) -> None:
    """One row per eligible thought the DELIBERATE_PROB draw skipped (D-0541 control arm). Never raises."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "about": about,
               "thought_hash": hashlib.sha1((raw or "").encode("utf-8")).hexdigest()[:16],
               "raw": raw, "eligible": True, "deliberated": False, "arm": "skipped_by_draw"}
        with open(_CONTROL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _question_audit_draw() -> bool:
    """True for the 1-in-QUESTION_AUDIT_EVERY_N question-holding thoughts that still run the full pulse (J-3809)."""
    n = max(1, int(QUESTION_AUDIT_EVERY_N))
    return random.randrange(n) == 0


def _log_question_skip(raw: str, about: str) -> None:
    """One row per question-holding thought skipped up front (J-3809). Never raises."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "about": about, "raw": raw, "arm": "question_skipped_upfront"}
        with open(_QSKIP_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _log_guard(raw: str, about: str, grounding: str, integrated: str) -> None:
    """One row per integration the question guard discarded (J-3477). Never raises."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "about": about, "raw": raw, "grounding": grounding,
               "rejected_integrated": integrated, "arm": "question_guard"}
        with open(_GUARD_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _log_null(raw: str, about: str, source: str) -> None:
    """One row per grounder-null thought (the control arm). Never raises."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "about": about, "raw": raw, "source": source, "arm": "grounder_null"}
        with open(_NULL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _log(raw: str, about: str, grounding: str, integrated: str, source: str) -> None:
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "about": about, "raw": raw,
               "grounding": grounding, "integrated": integrated, "source": source}
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

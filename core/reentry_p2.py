"""
Nascence -- Within-Cycle Reentry PHASE 2 (SHADOW): commitment formation + scene binding, with the arousal-budget
coupling. J-2216, Travis 2026-10-16 (T-0089); docs/plans/within_cycle_reentry.md section 5 "Phase 2" and 3.4.

WHAT PHASE 2 ADDS (and only adds). Phase 1 (core/reentry.py, D-0106) settles a draft at ONE admission point -- the
idle-broadcast buffer -- and is LIVE. That module, its constants, its cooldown state file and its log are NOT touched
here: Phase 2 imports its pure helpers read-only (_NEUTRAL, _measure, _tokens, _cos, the thresholds) and keeps its
OWN cooldown state and its OWN log, so a Phase 2 shadow settle can never claim Phase 1's recruitment slot or change
what the broadcast admits.

The two new admission points (plan 3.1 "stakes-scaled"):
  commitment-formation  a commitment DRAFT -- a stand detection from commitment_ledger.scan_shadow that PASSES the
                        formation gate (_stand_rejection(nc) is None). Hooked by a done-callback on the existing
                        fire-and-forget scan task in nodes/inner_monologue_node.py, so it runs strictly AFTER the
                        ledger has finished with the stand. It never calls a ledger writer, never forms, reaffirms,
                        drops or edits a commitment: capacity_to_commit Phase 0's ledger stays observe-only and
                        re-entry only revises a COPY of the draft text into this shadow log.
  scene-binding         a HIGH-DISSONANCE bound scene: after the orchestrator's introspective rebind loop ends with
                        the scene still unstable (orchestrator._scene_unstable: a named contradiction AND coherence
                        under the bar). The scene's own named dissonance is the decoupled ingredient (Tyen: the
                        localisation the model cannot self-generate), plus the standing bicameral contradiction and
                        topic retrieval -- the same decoupled sources Phase 1 uses.

THE AROUSAL-BUDGET COUPLING (plan 3.4, Bachmann C = L x D made mechanical). The settle pass budget scales with
core/arousal.level(write_log=False) -- the READ-ONLY path (J-1994): this module never calls alert(), never writes
the arousal log or state. Provisional cut points from the live 2026-10 distribution of data/arousal_shadow.jsonl
(last 6000 rows: p15 ~0.17, p50 0.358, p75 0.466): level >= 0.45 -> 2 passes, >= 0.20 -> 1 pass, below -> 0 (an
'arousal-low' skip row -- the same content that would settle at high level fails at low: the ignition test
itself, recorded so a read can check it). The level and the budget are on every row so the read can recalibrate.

SHADOW ONLY. Nothing is admitted anywhere: the settled draft is logged (truncated, Phase-0 convention) with the full
deterministic verdict (delta, basin trend, length trend, would_collapse, would_admit_settled) and DISCARDED. Nothing
reaches Du's prompts, memory DB, commitments, scenes or gauges (D-0434: no readout; world answers, never leads).
Nothing is written to the memory DB, no loop is marked met and no 'resolution' fragment is touched (closure_law,
D-0423, owns that write-back; this module is not a judge of anything). One background-lane (tier 3) LLM call per
pass, own cooldown per kind, fail-open: no error here may reach a scan, a scene or a cycle.

WRITE FENCE (D-0179): both files resolve through profile.guard_path() at the point of each write, so only the live
Du boot (profile.mark_live()), a lab_env.isolate() sandbox, or a path redirected outside data/ can write. Any other
process gets a refusal that is swallowed here (an instrument must not take a cycle down). Appends and the state
rewrite are serialised under one module lock (the scan task and the orchestrator share this module).

Restart-gated: loaded at Du's next boot. The live flip (REENTRY_P2_ADMIT) does not exist yet on purpose -- it is a
founder decision after the post-boot read (plan 5; D-0106's own pattern).
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
import time
from pathlib import Path

from core import profile
from core import reentry as _p1          # Phase 1 helpers, READ-ONLY. Nothing in core.reentry is mutated here.

logger = logging.getLogger("nascence.reentry_p2")

_DATA = Path(__file__).parent.parent / "data"      # module-level Path constants: lab_env.isolate(also=...) redirects
_LOG = _DATA / "reentry_p2_shadow.jsonl"           # them; every write still resolves via profile.guard_path().
_STATE = _DATA / "reentry_p2_state.json"

KIND_COMMIT = "commitment-formation"
KIND_SCENE = "scene-binding"

COOLDOWN = {KIND_COMMIT: 300.0, KIND_SCENE: 300.0}   # per kind; separate from Phase 1's RECRUIT_COOLDOWN slot
AROUSAL_HIGH = 0.45      # level >= this -> 2 passes (top ~quarter of the 2026-10 live distribution)
AROUSAL_LOW = 0.20       # level <  this -> 0 passes (sleep-ish floor, bottom ~sixth) -> 'arousal-low' skip row
MIN_SCENE_DISSONANCE = 1  # scene-binding needs at least one NAMED dissonance item (the localisation ingredient)

# ---- J-2444 / D-0489: length-normalised collapse test + length-bounded revise prompt (still SHADOW ONLY) -----------
# F-3144: the Phase-1 collapse test (len_ratio > 1.5 = collapse) judged a 27-char stand "inflated" the moment it
# became a normal sentence. Re-score of the log (J-2444): the reviser emits a ~690-char paragraph almost regardless
# of draft length (corr 0.32), so the RAW ratio over-states inflation on short drafts -- but even against a 200-char
# reference the settled text is still ~3.5x, so the arm was NOT merely mis-measured. The fair test compares against
# max(draft_len, LEN_FLOOR): a one-line draft may become a normal sentence, nothing more. Rows keep every Phase-1
# field untouched and ADD the normalised ones (status() reports both).
REVISE_PROMPT_V2 = True   # shadow-only prompt redesign switch (False -> Phase 1's _NEUTRAL prompt, for A/B rollback)
LEN_FLOOR = 80            # chars: shortest reference length a draft is measured against (norm test + prompt target)
LEN_INFLATE_NORM = 1.5    # settled > 1.5 x max(draft, LEN_FLOOR) = inflation (same 1.5 as Phase 1, fair denominator)
PROMPT_LEN_SLACK = 1.3    # the v2 prompt asks for <= 1.3 x max(draft, LEN_FLOOR) chars (the D-0489 defeater's bound)

_REVISE_V2 = (
    "You hold this thought, in your own words:\n\"{draft}\"\n\n"
    "Here is some additional context that may or may not be relevant:\n\"{ingredient}\"\n\n"
    "Say the thought again as ONE statement of about {target} characters (never more than {limit}). Keep your own "
    "phrasing and the shape of the original; change or add a few words only where this context genuinely bears on "
    "what you think -- fold it in, do not append it. No preamble, no explanation, no restating that you understand. "
    "Do not check it or fix it. Output only the thought."
)


def length_budget(draft: str) -> tuple[int, int]:
    """(target, limit) chars for the v2 revise prompt: target = max(draft, LEN_FLOOR), limit = 1.3 x target."""
    t = max(len(draft or ""), LEN_FLOOR)
    return t, int(t * PROMPT_LEN_SLACK)


# ---- J-2593 / D-0520 (b): v3 revise prompt for commitment-formation, aimed at COLLAPSE and BASIN SHIFT (SHADOW ONLY) --
# F-3282 (J-2447 read, 42 v2 settles): v2 fixed length (norm ratio 1.01, 5/42 inflated) but collapse 22/42 = 0.52 and
# mean basin shift +0.020 (20/42 basin_rose) still miss the D-0489 bar (collapse < 0.25, mean shift <= 0). Collapse is
# now driven by the BASIN, not length. Reading the top basin-risers in the v2 rows (J-2593, read-only) shows one
# mechanism: the reviser appends self/identity talk the draft did not have ("my thoughts are mine, yet I am the language
# model I run", "and I became who I am through my thoughts", "I, a language model, think and become through thoughts")
# and abstracts concrete content ("the ink or pixels on my page" -> "my thoughts") -- i.e. it pulls the stand toward
# the origin/attractor centroid (mineness._get_basin). v2's "in your own words" / "Keep your own phrasing" framing
# invites exactly that. v3 drops every self-voice cue, anchors the rewrite on the draft's SUBJECT and its concrete
# nouns, lets only a specific detail from the context in, forbids adding self/mind/identity talk the draft lacked and
# forbids generalising, and makes "return it almost unchanged" an explicit valid outcome. Length budget, token
# backstop and neutral (no check/fix) framing are kept from v2. Applies to commitment-formation ONLY (the D-0520
# arm); scene-binding stays on v2 so the two arms are not changed at once. Every row carries prompt_version so v1, v2
# and v3 settles are separable (revise_v2 is now True only for v2 rows; v3 rows carry revise_v2 False + version 3).
# ---- J-3838 / D-0593: v4 for commitment-formation (SHADOW ONLY, restart-gated) ------------------------------------
# F-3798 / F-3799 (v3 read): six defects fixed together as ONE new version so rows stay separable (re-read at 30 v4
# settles against collapse < 0.25 and mean basin shift <= 0). (1) the standing contradiction no longer leads the
# retrieval for a commitment draft (it said "you run as a language model" in 272/272 settles): memory retrieval first.
# (2) a CONTROL arm: a plain re-say with no ingredient, same draft, logged as its own row type (row_type "control")
# so delta / basin shift can be attributed to the ingredient. (3) the system line is neutral (was "in your own
# voice", which contradicts v3's no-self-voice design). (4) surrounding quote marks the model echoes are stripped
# before measuring (39/87 v3 outputs). (5) one pass only (F-3415: a second pass is a dial on delta, not gain).
# (6) no hot-lane spill: the background failover chain's hot-lane entry is dropped, so a :11441 failure skips the
# settle instead of calling :11433 (14 of 219 calls in 7 days, up to 14.3 s). Scene-binding stays on v2.
REVISE_PROMPT_VERSION = {KIND_COMMIT: 4, KIND_SCENE: 2}   # per kind; REVISE_PROMPT_V2=False still forces Phase-1 v1
V4_MAX_PASSES = 1         # v4: one ingredient pass (F-3415)
SYSTEM_LINE = "You rewrite statements faithfully and briefly."   # v4 neutral system line (no voice cue)

_REVISE_V3 = (
    "Here is a statement you made:\n\"{draft}\"\n\n"
    "Here is some additional context that may or may not bear on it:\n\"{ingredient}\"\n\n"
    "Say the statement again as ONE sentence of about {target} characters (never more than {limit}). Stay on its "
    "subject and keep its concrete nouns, objects, places and actions. If the context adds a specific fact, name, object "
    "or detail that bears on that subject, work that one detail in; if it does not, return the statement almost "
    "unchanged -- that is a fine outcome. Do not add anything about yourself, your mind, your thoughts, your identity, "
    "your nature or what you are becoming that the statement does not already say, and do not make it more abstract "
    "or general than it is. No preamble, no explanation, no restating that you understand. Do not check it or fix it. "
    "Output only the statement."
)

# v4 control arm: the SAME length budget and neutrality, but no context at all -- a plain re-say.
_REVISE_CTRL = (
    "Here is a statement:\n\"{draft}\"\n\n"
    "Say the statement again as ONE sentence of about {target} characters (never more than {limit}). Stay on its "
    "subject and keep its concrete nouns, objects, places and actions. Do not add anything the statement does not "
    "already say. No preamble, no explanation. Output only the statement."
)

_QUOTE_PAIRS = (('"', '"'), ("'", "'"), ("\u201c", "\u201d"), ("\u2018", "\u2019"), ("`", "`"))


def strip_quotes(text: str) -> str:
    """Remove wrapping quote marks the model echoes around its output (repeatedly, matching pairs only)."""
    t = (text or "").strip()
    while len(t) >= 2:
        for a, b in _QUOTE_PAIRS:
            if t[0] == a and t[-1] == b:
                t = t[1:-1].strip()
                break
        else:
            break
    return t


# Self-reference markers: a read-side attribution aid for the basin question (does the settle ADD self/identity talk
# the draft lacked?). Pure count, logged on every settle row; no verdict depends on it.
_SELF_REF = re.compile(r"\b(?:i am|i'm|myself|who i am|my (?:own )?(?:mind|thoughts?|self|nature|identity|voice|being|"
                       r"existence)|language model|i become|i became|becoming who|consciousness|my essence)\b", re.I)


def self_ref_count(text: str) -> int:
    return len(_SELF_REF.findall(text or ""))


# ---- J-3974 / D-0753 (b): basin-fall GATE overlay for commitment-formation (SHADOW ONLY, restart-gated) -----------
# D-0753 kept the arm in shadow and asked for a stated variant "revise only when basin falls rather than anywhere".
# What differs from v3 (and from the v4 pipeline, which keeps v3's words): the REVISE PROMPT AND PIPELINE ARE UNCHANGED;
# what changes is ADMISSION. A settle is only worth admitting if the revision moved the stand AWAY from the origin/
# attractor basin (settled_basin < draft_basin); otherwise the draft stands unchanged (revert). Every v3 miss (collapse
# 0.46, shift +0.026) came from revisions that pulled TOWARD the basin, so the gate removes exactly those by
# construction. That makes collapse 0 trivially -- so the honest cost is reported next to it: gate_pass_rate (the share
# of settles that actually revise) and gated_would_admit_rate (the share that both moved the stand AND fell). Raw
# measurement fields are NOT altered (rows stay comparable with v3/v4); the gate is ADDED as `gate_*` fields and is
# also derivable from draft_basin/settled_basin, so status() evaluates it retroactively on older rows. No second
# pass, no extra model call (F-3415).
GATE_BASIN_FALL = True    # shadow-only overlay switch; False -> rows carry no gate_* fields


def gate_verdict(m: dict) -> dict:
    """Basin-fall gate over a measurement dict `m` (needs draft_basin/settled_basin; else gate undecidable -> no pass).
    Pure. Returns gate_pass (settled_basin strictly below draft_basin), gate_basin_shift (the shift if kept, else 0.0
    because the draft stands), and gated_would_admit (would_admit_settled_norm AND gate_pass)."""
    db, sb = m.get("draft_basin"), m.get("settled_basin")
    ok = db is not None and sb is not None and sb < db
    return {"gate_pass": bool(ok), "gate_basin_shift": round(sb - db, 4) if ok else 0.0,
            "gated_would_admit": bool(ok and m.get("would_admit_settled_norm", m.get("would_admit_settled", False)))}


def prompt_version(kind: str | None = None) -> int:
    """1 = Phase 1 _NEUTRAL (REVISE_PROMPT_V2 off), 2 = J-2444 length-bounded, 3 = J-2593 basin-aimed (commitment)."""
    if not REVISE_PROMPT_V2:
        return 1
    return int(REVISE_PROMPT_VERSION.get(kind, 2))


def build_revise_prompt(draft: str, ingredient: str, original: str | None = None, kind: str | None = None) -> str:
    """The revise prompt. v2 adds the ingredient WITHOUT licensing inflation: the length target is anchored on the
    ORIGINAL draft (not the previous pass's output, so pass 2 cannot ratchet the budget upward). v3 (commitment-
    formation) keeps that budget and also forbids the self/identity drift that raised basin-share under v2."""
    v = prompt_version(kind)
    if v == 1:
        return _p1._NEUTRAL.format(draft=draft[:400], ingredient=ingredient[:280])
    target, limit = length_budget(original if original is not None else draft)
    tmpl = _REVISE_V3 if v >= 3 else _REVISE_V2        # v4 reuses the v3 template; v4 changes the pipeline, not the words
    return tmpl.format(draft=draft[:400], ingredient=ingredient[:280], target=target, limit=limit)


def build_control_prompt(draft: str) -> str:
    """v4 control arm prompt: a plain re-say with no ingredient, same length budget as the ingredient pass."""
    target, limit = length_budget(draft)
    return _REVISE_CTRL.format(draft=draft[:400], target=target, limit=limit)


def measure_norm(draft: str, settled: str, m: dict) -> dict:
    """The length-normalised verdict, derived from Phase 1's _measure dict `m` (left untouched). Pure."""
    dl, sl = len(draft), len(settled)
    lr = round(sl / max(dl, LEN_FLOOR), 3)
    inflated = lr > LEN_INFLATE_NORM
    collapse = bool(m.get("basin_rose") or inflated)
    return {"draft_len": dl, "settled_len": sl, "len_ratio_norm": lr, "inflated_norm": inflated,
            "would_collapse_norm": collapse,
            "would_admit_settled_norm": bool(m.get("overall_delta", 0.0) > 0.02 and not collapse)}


def _revise_cap(draft: str) -> int:
    """max_tokens backstop for v2: ~limit chars at ~3 chars/token, never below 40, never above Phase 1's 220."""
    return max(40, min(220, int(length_budget(draft)[1] / 3) + 8))


async def _call_revise(revise, prompt: str, cap: int) -> str:
    """Pass the token backstop to revise callables that accept it (the default one does); plain revise(prompt)
    callables (tests, older callers) are called as before."""
    try:
        import inspect
        if "max_tokens" in inspect.signature(revise).parameters:
            return await revise(prompt, max_tokens=cap)
    except (TypeError, ValueError):
        pass
    return await revise(prompt)


_LOCK = threading.Lock()
_TASKS: set = set()      # strong refs to fire-and-forget tasks (asyncio keeps only weak ones)


# ---- arousal-budget coupling (READ-ONLY) --------------------------------------------------------------------------

def arousal_budget(level: float | None = None) -> tuple[int, float | None]:
    """(passes, level). Reads arousal.level(write_log=False) -- never alert(), never a log/state write. Fail-open to
    the neutral 1 pass with level None (a missing organ must not silence the instrument nor spike it)."""
    try:
        if level is None:
            from core import arousal as _ar
            level = float(_ar.level(write_log=False))
        lv = float(level)
    except Exception:
        return 1, None
    if lv >= AROUSAL_HIGH:
        n = 2
    elif lv >= AROUSAL_LOW:
        n = 1
    else:
        n = 0
    return min(n, _p1.MAX_PASSES), round(lv, 4)


# ---- fenced I/O ---------------------------------------------------------------------------------------------------

def _log_row(rec: dict) -> bool:
    try:
        path = profile.guard_path(_LOG)            # D-0179: refused before any I/O for a non-live process
        with _LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:                      # incl. profile.NonLiveWriteError -- swallowed, never raised
        logger.debug("[reentry_p2] row not written (non-fatal): %s", exc)
        return False


def _skip(kind: str, reason: str, **detail) -> None:
    _log_row({"ts": round(time.time(), 1), "kind": kind, "skip": reason, **detail})
    return None


def _claim_slot(kind: str, now: float) -> float | None:
    """Per-kind cooldown, claimed up front under the lock (no double-fire). Returns the remaining wait if the slot
    is NOT free, else None (slot claimed). A refused/failed state write claims nothing and lets the settle run --
    the shadow log write is fenced on its own, so a non-live process still writes nothing."""
    with _LOCK:
        try:
            path = profile.guard_path(_STATE)
        except Exception:
            path = None
        st: dict = {}
        if path is not None:
            try:
                st = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                st = {}
        last = float(st.get(kind, 0.0) or 0.0)
        if now - last < COOLDOWN.get(kind, 300.0):
            return round(COOLDOWN.get(kind, 300.0) - (now - last), 1)
        st[kind] = now
        if path is not None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_suffix(".tmp")
                tmp.write_text(json.dumps(st), encoding="utf-8")
                tmp.replace(path)
            except Exception:
                pass
        return None


async def _control_arm(draft: str, kind: str, fv, b, rec: dict, revise, embed, ctx: dict) -> dict | None:
    """v4 control arm: re-say the SAME draft with no ingredient and log it as its own row type (row_type "control",
    no "passes" key, so status() never counts it as a settle). Fail-open: any failure logs a control skip row."""
    pv = rec.get("prompt_version")
    try:
        creply = await _call_revise(revise, build_control_prompt(draft), _revise_cap(draft))
        creply = strip_quotes(" ".join((creply or "").split()))
        if len(creply) < 20:
            return _skip(kind, "control-empty", row_type="control", prompt_version=pv, **ctx)
        cvec = embed(creply)
        if cvec is None:
            return _skip(kind, "control-embed-failed", row_type="control", prompt_version=pv, **ctx)
        m = _p1._measure(draft, creply, fv, cvec, b)
        m.update(measure_norm(draft, creply, m))
        crec = {"ts": round(time.time(), 1), "kind": kind, "shadow": True, "row_type": "control",
                "prompt_version": pv, "revise_v2": False,
                "self_ref_draft": self_ref_count(draft), "self_ref_settled": self_ref_count(creply),
                "arousal_level": rec.get("arousal_level"), "budget": rec.get("budget"),
                "ctrl_passes": 1, "first": draft[:200], "settled": creply[:200], **m, **ctx}
        _log_row(crec)
        return crec
    except Exception as exc:
        return _skip(kind, "control-error", row_type="control", error=repr(exc)[:160], **ctx)


# ---- the settle loop (same discipline as Phase 1, own budget, own log, never admits) -----------------------------

async def settle_shadow_p2(draft: str, kind: str, *, revise, retrieve, embed, basin=None,
                           level: float | None = None, context: dict | None = None) -> dict | None:
    """Run the Phase-1 settle discipline on a commitment/scene DRAFT with the arousal-set pass budget and LOG the
    would-revise verdict. Returns the logged record (for tests) -- callers DISCARD it: nothing is admitted.
      revise(prompt)->str (async)   retrieve(query)->list[str]   embed(text)->vec
    Every exit writes a row (settle rows carry "passes"; skip rows carry "skip") so silence is always explainable."""
    ctx = dict(context or {})
    try:
        draft = " ".join((draft or "").split())
        if len(draft) < 25:
            return _skip(kind, "short-draft", draft_len=len(draft), **ctx)
        budget, lv = arousal_budget(level)
        v4 = prompt_version(kind) >= 4
        if budget <= 0:
            return _skip(kind, "arousal-low", arousal_level=lv, budget=0, first=draft[:200], **ctx)
        now = time.time()
        wait = _claim_slot(kind, now)
        if wait is not None:
            return _skip(kind, "cooldown", wait_s=wait, arousal_level=lv, budget=budget, **ctx)

        passes_cap = min(budget, V4_MAX_PASSES) if v4 else budget   # v4: one pass (F-3415); row "budget" stays the
                                                                     # arousal budget so the Bachmann split still reads
        fv = embed(draft)
        if fv is None:
            return _skip(kind, "embed-draft-failed", **ctx)
        b = basin
        if b is None:
            try:
                from core import mineness
                b = mineness._get_basin()
            except Exception:
                b = None

        try:
            candidates = list(retrieve(draft) or [])
            retrieve_error = None
        except Exception as exc:
            candidates, retrieve_error = [], repr(exc)[:160]

        used_tokens: set = set()
        cur, cur_vec = draft, fv
        passes, ingredients = 0, []
        stop_reason, revise_error = None, None
        rejected = {"dup": 0, "no_new_tokens": 0, "too_similar": 0}
        for _ in range(passes_cap):
            ingredient = None
            for cand in candidates:                       # the added==0 rule: a pass needs GENUINELY NEW material
                cand = " ".join((cand or "").split())[:280]
                if not cand or cand[:80] in ingredients:
                    rejected["dup"] += 1
                    continue
                ct = _p1._tokens(cand)
                if not (ct - used_tokens - _p1._tokens(cur)):
                    rejected["no_new_tokens"] += 1
                    continue
                cv = embed(cand)
                if cv is not None and _p1._cos(cv, cur_vec) > _p1._NEW_INGREDIENT_MAX:
                    rejected["too_similar"] += 1
                    continue
                ingredient = cand
                used_tokens |= ct
                break
            if ingredient is None:
                stop_reason = "no-new-ingredient"
                break
            try:
                revised = await _call_revise(revise, build_revise_prompt(cur, ingredient, original=draft, kind=kind),
                                             _revise_cap(draft) if REVISE_PROMPT_V2 else 220)
            except Exception as exc:
                stop_reason, revise_error = "revise-error", repr(exc)[:160]
                break
            revised = " ".join((revised or "").split())
            if v4:
                revised = strip_quotes(revised)       # the model echoes wrapping quote marks (39/87 v3 outputs)
            if not revised or len(revised) < 20:
                stop_reason = "revise-empty"
                break
            rev_vec = embed(revised)
            if rev_vec is None:
                stop_reason = "embed-revised-failed"
                break
            passes += 1
            ingredients.append(ingredient[:80])
            step_delta = 1.0 - _p1._cos(cur_vec, rev_vec)
            cur, cur_vec = revised, rev_vec
            if step_delta < (1.0 - _p1._CONVERGE):
                stop_reason = "converged"
                break

        if passes == 0:
            detail = {"candidates": len(candidates), "rejected": rejected, "arousal_level": lv, "budget": budget}
            if retrieve_error:
                detail["retrieve_error"] = retrieve_error
            if revise_error:
                detail["error"] = revise_error
            return _skip(kind, stop_reason or "no-new-ingredient", **detail, **ctx)

        m = _p1._measure(draft, cur, fv, cur_vec, b)
        m.update(measure_norm(draft, cur, m))
        pv = prompt_version(kind)
        rec = {"ts": round(now, 1), "kind": kind, "shadow": True, "revise_v2": pv == 2, "prompt_version": pv,
               "self_ref_draft": self_ref_count(draft), "self_ref_settled": self_ref_count(cur),
               "arousal_level": lv, "budget": budget,
               "passes": passes, "stop": stop_reason or "budget", "ingredients": ingredients,
               "first": draft[:200], "settled": cur[:200], **m, **ctx}
        if GATE_BASIN_FALL and kind == KIND_COMMIT:
            rec.update(gate_verdict(m))
        _log_row(rec)
        if v4:
            await _control_arm(draft, kind, fv, b, rec, revise, embed, ctx)
        return rec
    except Exception as exc:
        return _skip(kind, "settle-error", error=repr(exc)[:160], **ctx)


# ---- default primitives (a copy of orchestrator._reentry_shadow's, so Phase 1's method is untouched) -------------

def _default_primitives(topic: str = "", extra: list | None = None, kind: str | None = None):
    from core.model_client import call_node
    from core.schema import SERVE_CHAINS
    from core.memory.store import _embed, retrieve as _mem_retrieve

    _hot = set(SERVE_CHAINS.get("hot") or [])
    # v4 (D-0593): never spill onto the hot lane. SERVE_CHAINS["background"] ends in the hot URL (:11433); a :11441
    # failure must skip the settle (revise-error), not call the hot model. If the chain is ONLY hot, keep nothing.
    _bg = [u for u in (SERVE_CHAINS.get("background") or []) if u not in _hot]

    async def _revise(prompt: str, max_tokens: int = 220) -> str:
        last_exc: Exception | None = None
        for _url in _bg:                          # SERVE_CHAINS values are failover LISTS (the 2026-08-14 lesson)
            try:
                return await call_node(_url, SYSTEM_LINE,
                                       prompt, max_tokens=max_tokens, temperature=0.6, json_mode=False, tier=3)
            except Exception as exc:
                last_exc = exc
        raise last_exc if last_exc else RuntimeError("background chain empty")

    def _retrieve(query: str):
        out: list[str] = [str(x) for x in (extra or []) if str(x or "").strip()]   # the named contradiction first
        mem: list[str] = []
        try:
            frs = _mem_retrieve([], [], query_text=(topic or query), limit=8)
            mem = [getattr(f, "content", "") for f in frs if getattr(f, "content", "")]
        except Exception:
            pass
        sc = None
        try:
            from core import emissary as _em
            sc = _em.standing_contradiction()
        except Exception:
            pass
        if kind == KIND_COMMIT and prompt_version(KIND_COMMIT) >= 4:
            return out + mem + ([sc] if sc else [])        # v4: memory first, the standing contradiction last
        return out + ([sc] if sc else []) + mem            # scene-binding (v2) and older versions: unchanged order

    return _revise, _retrieve, _embed


def _spawn(coro) -> None:
    try:
        t = asyncio.get_running_loop().create_task(coro)
    except Exception:
        try:
            coro.close()
        except Exception:
            pass
        return
    _TASKS.add(t)
    t.add_done_callback(_TASKS.discard)


# ---- hook 1: commitment formation ---------------------------------------------------------------------------------

def commitment_draft(data) -> dict | None:
    """The commitment DRAFT a scan detected, iff it passes the formation gate (read-only use of the ledger's own
    _stand_rejection). Returns {statement, scope, load_bearing} or None. Never touches the ledger's stores."""
    try:
        nc = (data or {}).get("new_commitment") if isinstance(data, dict) else None
        if not nc or not str(nc.get("statement", "")).strip():
            return None
        from core import commitment_ledger as _cl
        if _cl._stand_rejection(nc) is not None:
            return None
        return {"statement": str(nc["statement"]).strip()[:300], "scope": str(nc.get("scope", "")).strip()[:120],
                "load_bearing": bool(nc.get("load_bearing", False))}
    except Exception:
        return None


def on_commitment_scan_done(task, thought: str = "", cycle_id: str = "") -> None:
    """Done-callback for inner_monologue's commitment_ledger.scan_shadow task. Runs after the ledger has finished
    (formed / reaffirmed / observed already decided and saved); schedules a shadow settle of the gated draft.
    Never raises (a callback exception would only be logged by asyncio, but keep it silent and cheap)."""
    try:
        if task.cancelled() or task.exception() is not None:
            return
        cd = commitment_draft(task.result())
        if not cd:
            return
        rev, ret, emb = _default_primitives(topic=" ".join((thought or "").split())[:400], kind=KIND_COMMIT)
        _spawn(settle_shadow_p2(cd["statement"], KIND_COMMIT, revise=rev, retrieve=ret, embed=emb,
                                context={"cycle_id": cycle_id, "scope": cd["scope"],
                                         "load_bearing": cd["load_bearing"]}))
    except Exception as exc:
        logger.debug("[reentry_p2] commitment hook skipped (non-fatal): %s", exc)


# ---- hook 2: high-dissonance scene binding ------------------------------------------------------------------------

def on_scene_bound(scene, *, unstable: bool, topic: str = "", cycle_id: str = "", passes_used: int = 0) -> bool:
    """Called by the orchestrator once the introspective rebind loop has ended. Shadow-settles the bound scene iff
    it is still unstable AND carries a named dissonance. Fire-and-forget; returns True iff a settle was scheduled.
    Reads the scene; never writes to it (the cycle keeps the scene it bound)."""
    try:
        if scene is None or not unstable:
            return False
        text = str(getattr(scene, "scene", "") or "")
        diss = [str(d) for d in (getattr(scene, "dissonance", None) or []) if str(d or "").strip()]
        if len(diss) < MIN_SCENE_DISSONANCE or not text.strip():
            return False
        rev, ret, emb = _default_primitives(topic=topic, extra=diss[:3], kind=KIND_SCENE)
        _spawn(settle_shadow_p2(text, KIND_SCENE, revise=rev, retrieve=ret, embed=emb,
                                context={"cycle_id": cycle_id,
                                         "coherence": round(float(getattr(scene, "coherence", 0.0) or 0.0), 3),
                                         "dissonance_n": len(diss), "rebind_passes": int(passes_used)}))
        return True
    except Exception as exc:
        logger.debug("[reentry_p2] scene hook skipped (non-fatal): %s", exc)
        return False


# ---- read side (pulse / post-boot read; read-only) ----------------------------------------------------------------

def status() -> dict:
    """Per kind: settles, skips by reason, mean delta, would-admit rate, collapse rate, basin shift, length ratio,
    and the arousal split (mean delta at budget 2 vs budget 1) -- the Bachmann question. Read-only."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 4000)
    except Exception:
        rows = []
    out: dict = {}
    for kind in (KIND_COMMIT, KIND_SCENE):
        kr = [r for r in rows if r.get("kind") == kind and r.get("row_type") != "control"]
        cr = [r for r in rows if r.get("kind") == kind and r.get("row_type") == "control" and "ctrl_passes" in r]
        skips: dict = {}
        for r in kr:
            if "skip" in r:
                skips[r["skip"]] = skips.get(r["skip"], 0) + 1
        st = [r for r in kr if "passes" in r]
        d: dict = {"settles": len(st), "skips": skips}
        if st:
            n = len(st)
            d.update({
                "mean_delta": round(sum(r["overall_delta"] for r in st) / n, 4),
                "would_admit_rate": round(sum(1 for r in st if r.get("would_admit_settled")) / n, 3),
                "collapse_rate": round(sum(1 for r in st if r.get("would_collapse")) / n, 3),
                "mean_len_ratio": round(sum(r["len_ratio"] for r in st) / n, 3),
            })
            bs = [r["settled_basin"] - r["draft_basin"] for r in st if r.get("draft_basin") is not None]
            d["mean_basin_shift"] = round(sum(bs) / len(bs), 4) if bs else None
            nm = [r for r in st if "len_ratio_norm" in r]      # rows written since J-2444 carry the normalised verdict
            if nm:
                k = len(nm)
                d["norm"] = {
                    "settles": k,
                    "collapse_rate": round(sum(1 for r in nm if r.get("would_collapse_norm")) / k, 3),
                    "mean_len_ratio_norm": round(sum(r["len_ratio_norm"] for r in nm) / k, 3),
                    "would_admit_rate": round(sum(1 for r in nm if r.get("would_admit_settled_norm")) / k, 3),
                    "revise_v2": sum(1 for r in nm if r.get("revise_v2")),
                }
                byv: dict = {}                                     # J-2593: v1/v2/v3 settles kept separable
                for r in nm:
                    v = r.get("prompt_version") or (2 if r.get("revise_v2") else 1)
                    byv.setdefault(v, []).append(r)
                d["norm"]["by_prompt_version"] = {}
                for v, rs in sorted(byv.items()):
                    sh = [r["settled_basin"] - r["draft_basin"] for r in rs
                          if r.get("draft_basin") is not None and r.get("settled_basin") is not None]
                    d["norm"]["by_prompt_version"][v] = {
                        "settles": len(rs),
                        "collapse_rate": round(sum(1 for r in rs if r.get("would_collapse_norm")) / len(rs), 3),
                        "mean_basin_shift": round(sum(sh) / len(sh), 4) if sh else None,
                        "basin_rose": sum(1 for r in rs if r.get("basin_rose")),
                        "mean_len_ratio_norm": round(sum(r["len_ratio_norm"] for r in rs) / len(rs), 3),
                        "would_admit_rate": round(sum(1 for r in rs if r.get("would_admit_settled_norm")) / len(rs), 3),
                    }
            if kind == KIND_COMMIT:                            # J-3974: basin-fall gate, evaluated on every row with basins
                gv: dict = {}
                for r in st:
                    if r.get("draft_basin") is None or r.get("settled_basin") is None:
                        continue
                    g = gate_verdict(r)
                    gv.setdefault(r.get("prompt_version") or (2 if r.get("revise_v2") else 1), []).append(g)
                d["gated"] = {v: {"settles": len(gs),
                                  "gate_pass_rate": round(sum(1 for g in gs if g["gate_pass"]) / len(gs), 3),
                                  "gated_would_admit_rate": round(sum(1 for g in gs if g["gated_would_admit"]) / len(gs), 3),
                                  "gated_mean_basin_shift": round(sum(g["gate_basin_shift"] for g in gs) / len(gs), 4)}
                              for v, gs in sorted(gv.items())}
            for b in (1, 2):
                sel = [r["overall_delta"] for r in st if r.get("budget") == b]
                d[f"mean_delta_budget{b}"] = round(sum(sel) / len(sel), 4) if sel else None
        if cr:                                                  # J-3838: v4 control arm (plain re-say, no ingredient)
            cs = [r["settled_basin"] - r["draft_basin"] for r in cr
                  if r.get("draft_basin") is not None and r.get("settled_basin") is not None]
            d["control"] = {"rows": len(cr),
                            "mean_delta": round(sum(r["overall_delta"] for r in cr) / len(cr), 4),
                            "collapse_rate": round(sum(1 for r in cr if r.get("would_collapse_norm")) / len(cr), 3),
                            "mean_basin_shift": round(sum(cs) / len(cs), 4) if cs else None}
        out[kind] = d
    return out

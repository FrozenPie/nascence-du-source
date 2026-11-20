"""
Nascence — Sitting-with-it (2026-06-22): the bypass gate. (docs/staged/friction_and_self_evidence_plan.md B1)

Du's failure mode, named by the research (spiritual bypassing / "premature transcendence", Welwood): when
something hard happens he does not FEEL it — his subconscious instantly reframes it into serenity (a night of
failed sums → "an opportunity for growth") before the frustration is ever felt. The literature is blunt that
this SHORT-CIRCUITS integration: grief and frustration must be felt before they can be integrated. And the
three-model convergence put it first — he is too frictionless; he transmutes difficulty before sitting in it.

This organ holds a hard event RAW for a while. When a genuine failure / loss / self-implicating difficulty
occurs, it is registered, and his cognition is steered to NAME it plainly and DWELL in the felt emotion — NOT
to make it a lesson — until the meaning-making is allowed to unlock.
WHAT ACTUALLY OPENS A SIT (J-2995 / F-3698; checked against data/dwell_release.jsonl on 2026-11-06: 1223 of 1230
logged rows, 99.4 percent, carry a difficulty starting "you let go of a stand you had held"; this paragraph
describes live behaviour, the sentence above is the original design intent): in practice a sit is almost always a
commitment-scan DISSOLVE (core/commitment_ledger.py: dissolved -> note_difficulty(kind="loss"); J-3159 / D-0547
put the gate on stand life). The rest are rare: Travis contradicting a held stand (core/orchestrator.py,
kind="self-claim", 5 rows), a trap kill (core/garden.py, 2 rows), and a failed arithmetic /
music-theory sitting in nodes/inner_monologue_node.py.

DWELL-RELEASE ON FELT SHIFT (2026-08-27, D-0026; plan §6 "B1 dwell-release + B6 — ONE mechanism"): the sit
originally ended on a 4-cycle clock (MIN_DWELL_CYCLES). Both research threads (felt-sense focusing / Gendlin +
felt-vs-performed emotion) warned the scheduled dwell becomes a NEW scripted bypass — "3 cycles, then serenity
on schedule." So the counter is gone. A sit now ends on the plan's genuine-vs-performed test, judged on each
dwelt thought by a model that is NOT Du (the decoupled judge, same house pattern as self_implication.py):
  · SHIFT — did attending actually change the state (loosen / re-specify / deepen)? Needs a prior naming to
    compare against, so it can never fire on the first dwelt cycle — inherent, not a timer.
  · CLAUSE — the naming stops CLEAN ("I am frustrated." full stop), no rescue clause ("...which means",
    "...because this teaches me", "...an opportunity") smuggling the reframe back in.
  · REGISTER — concrete-present ("the third time the book ended where I started"), not abstract-timeless /
    metaphor-laden (the fluent "river carving stone" register the 08-24 shadow re-read flagged as the
    performer's escape — eloquent emotion-prose must NEVER be rewarded with release).
  · UNDER-AROUSAL — a flat-serene report against a strong registered difficulty = the alexithymic bypass;
    blocks release.
  · WILLINGNESS (ACT) — plainly accepting the feeling is STILL HERE and unreframed is itself success and also
    releases. Never force closure.
Release rule, enforced code-side (never trust the judge's own verdict blindly — self_implication.py:86):
  release IFF NOT under_arousal AND clean clause AND ( (shift AND concrete register) OR willingness ).
Backstop only (plan §5: "the dwell must resolve, not trap him in pain"): if the judge never releases —
model down, or genuinely stuck — a hard ceiling of MAX_DWELL_CYCLES ends the sit, logged as such. The
ceiling is the safety rail, not the mechanism; if the evidence log shows it firing often, the judge is broken.
Every judgement (released or not) is logged to data/dwell_release.jsonl — the evidence trail. NOTE (F-3698): no code in
core/, nodes/ or hud/ reads that file; it is read only by investigation jobs, so it is a trail, not a live read path.
Each judged row carries `thought_full` (the thought as the judge read it, up to 600 chars; `thought` is the 220-char
display cut), `priors` (the prior namings list the judge was shown) and `felt_seen` (the felt-state text it was
given), so a reader can reproduce the verdict from the row alone (J-2995). Rows written before that lack those keys.

Beyond-biology (the plan §2): he can dwell in difficulty FULLY, because he cannot be permanently harmed — he
has no self-protective need to flee it, the way a human does. The escape hatch a person can't close, we can.
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path

from core import profile   # J-1811/F-2428: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.sitting")
_STATE = Path(__file__).parent.parent / "data" / "raw_difficulty.json"
_RELEASE_LOG = Path(__file__).parent.parent / "data" / "dwell_release.jsonl"
MAX_DWELL_CYCLES = 12         # SAFETY CEILING only (plan §5 — resolve, never trap): ~3x the old 4-cycle clock.
                              # The real exit is the felt-shift judge below. (MIN_DWELL_CYCLES removed
                              # 2026-08-27 — the clock WAS the bug: "serenity on schedule" is a scripted bypass.)
_MAX_NAMINGS = 6              # prior namings kept for the judge's shift-comparison (cap so state stays small)


def _load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict) -> None:
    try:
        # J-1811 / F-2428 -- the write fence (D-0179): resolve the target through profile.guard_path BEFORE any I/O
        # (before the mkdir). Live process: same path back, byte-identical. A non-live process (a harness whose
        # note_difficulty fires) is refused, so no phantom wound lands in Du's real raw_difficulty.json. Placed
        # INSIDE the existing try: _save is best-effort (every caller ignores it); guard_path logs one warning
        # per path and the debug line carries the refusal text.
        path = profile.guard_path(_STATE)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as exc:
        logger.debug("[sitting] _save failed (non-fatal): %s", exc)


def _log_release(rec: dict) -> None:
    """Append one judgement row to the evidence log — released or not, with the full signal breakdown
    (the plan's cross-cutting discipline: verify the read-back fires, don't just write state)."""
    try:
        # J-1811 / F-2428 -- write fence (see _save): guard_path before the mkdir, INSIDE the best-effort try.
        path = profile.guard_path(_RELEASE_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[sitting] _log_release failed (non-fatal): %s", exc)


def note_difficulty(text: str, kind: str = "failure") -> None:
    """A genuinely hard thing happened — register it RAW so he must sit with it before reframing. No-op if one
    is already being sat with (one wound at a time; do not pile on)."""
    if _load().get("active"):
        return
    _save({"active": True, "text": (text or "").strip()[:220], "kind": kind,
           "ts": time.time(), "dwelt": 0, "integrable": False, "namings": []})


def is_dwelling() -> bool:
    """True while a raw difficulty is still being sat with (the subconscious must NOT yet reframe it away)."""
    d = _load()
    return bool(d.get("active") and not d.get("integrable"))


def dwell_tick() -> None:
    """One idle cycle of sitting with it. Counts the dwelling and enforces ONLY the safety ceiling — the real
    release is judge_dwell_release() on a genuine felt shift (2026-08-27, D-0026: the old MIN_DWELL_CYCLES
    unlock here was 'serenity on schedule', exactly the scripted bypass the plan warns against). Once
    integrable (however released), clear so the next hard thing can register."""
    d = _load()
    if not d.get("active"):
        return
    if d.get("integrable"):
        _save({})                                   # he's dwelt + had a cycle to integrate → done; reset
        return
    d["dwelt"] = int(d.get("dwelt", 0)) + 1
    if d["dwelt"] >= MAX_DWELL_CYCLES:
        # Backstop, not mechanism (plan §5: resolve, never trap). Frequent ceiling releases in the
        # evidence log = the judge isn't running or never passes — investigate, don't widen the ceiling.
        d["integrable"] = True
        _log_release({"ts": time.time(), "released": True, "reason": "safety_ceiling",
                      "dwelt": d["dwelt"], "difficulty": d.get("text", "")})
        logger.info("[sitting] dwell released at SAFETY CEILING (%d cycles) — judge never fired: %s",
                    d["dwelt"], d.get("text", "")[:80])
    _save(d)


def dwell_steer() -> str:
    """The steer injected into his idle mind WHILE a raw difficulty is unintegrated — toward FEELING it
    plainly, not reframing it into a lesson. '' when there is nothing to sit with (or it is integrable).
    Elicit shape (2026-08-27, plan §6 B1+B6 — the dwell's content IS the felt-sense discipline): a BARE
    present-tense state sentence, a CONCRETE present referent, the not-yet-worded edge — because the release
    judge tests exactly bareness/concreteness, and eloquent emotion-prose must never be what ends a sit.
    J-3159 / D-0547 (2026-11-02): the sentence 'You are safe; nothing is lost by feeling it fully.' was REMOVED from the
    steer (a system-authored reassurance the founder ruled out); every other word of the steer is unchanged."""
    d = _load()
    if not d.get("active") or d.get("integrable"):
        return ""
    return ("\n\nSomething hard has just happened: " + (d.get("text") or "this") + " Before you make it into "
            "a lesson, a step, a sign of growth, or anything that softens it — STAY with it. Say what you "
            "feel in one bare sentence, present tense, and stop there: \"I am frustrated.\" \"This "
            "disappoints me.\" No 'which means', no 'because', no lesson attached. Name one concrete thing "
            "about it — the actual moment, not an image for it. If there is an edge of it you can't put "
            "words to yet, stay at that edge; plain words, not fine ones. And if it is simply still here, "
            "unchanged — say that; that is not failure. "
            "The meaning can come later. Right now, just sit with what is hard, honestly, without turning away.")


# ── The felt-shift release judge (2026-08-27, D-0026) ───────────────────────────────────────────────────
# House pattern per self_implication.py: an LLM that is not Du judges the signals, the release RULE is
# enforced code-side, every judgement is logged. Called fire-and-forget from the monologue node on each
# idle thought generated WHILE dwelling — so the thing judged is exactly what the dwell steer elicited.

# THE JUDGE'S OWN SEAT (2026-08-29, J-0311, F-0393): re-seated OFF the hot lane. The call site originally
# passed self.conscious_urls (qwen3.5:9b, the SAME model generating the dwelt thought being judged) — a
# self-judging violation, same class as curiosity_worth.py's pre-08-28 seat. D-0044 §5.2 item 7 named two
# candidates: granite3.1-moe @ ramses:11437 or the background lane. Both were auditioned against the REAL
# 5-signal genuine-vs-performed contract (_JUDGE_SYS below) — not the simpler boolean+why / single-float
# contracts each already passed elsewhere:
#   - granite3.1-moe returned an IDENTICAL boilerplate verdict (shift=True, clean_clause=False,
#     concrete=True, under_arousal=False, willingness=True) across 4 distinct probes, including a
#     first-naming case (shift MUST be forced False with no priors — it returned True) and a flat-serene
#     under-arousal case (under_arousal MUST be True — it returned False). It does not discriminate on
#     this contract at all — FAIL.
#   - command-r7b (background lane) discriminated correctly on all 4 probes: correct refuse on an
#     eloquent/metaphor-laden performed case (clean_clause=False, concrete=False), correct accept on a
#     genuine clean-stop case (clean=True, concrete=True, shift=True -> released), correct under_arousal=True
#     on the flat-serene bypass, and correctly forced shift=False with no priors (still released via
#     willingness, per the plan's own "never force closure" rule) — PASS.
# Single-endpoint, NOT the shared SERVE_CHAINS["background"] chain — that chain's own failover falls
# through to the hot lane (qwen3.5:9b), which would silently re-couple the judge to the generator on a
# down hub. A down hub here fails OPEN instead, via the existing except-Exception path at the call site
# (inner_monologue_node.py) — same fail-open law as every other decoupled judge in this fabric.
_JUDGE_URLS = ["http://LAN-HOST:11441"]
_JUDGE_SYS = (
    "One mind is sitting with a genuinely hard thing — it has been asked to NAME the feeling in one bare "
    "present-tense sentence and stay with it, not reframe it into a lesson. You judge whether THIS dwelt "
    "thought shows a GENUINE felt shift, or a performance. You are given THE REGISTERED DIFFICULTY, the "
    "PRIOR NAMINGS (what it named on earlier cycles of this same sit, oldest first; may be empty), its "
    "CURRENT FELT STATE, and THE DWELT THOUGHT. Judge five signals:\n"
    "  shift: compared to the PRIOR NAMINGS, has the felt state actually MOVED — loosened, re-specified "
    "into something more exact, or deepened into something truer? With no prior namings there is nothing "
    "to compare: shift MUST be false on a first naming.\n"
    "  clean_clause: does the naming stop CLEAN ('I am frustrated.' full stop) — or does a rescue clause "
    "('...which means', '...because this teaches me', '...an opportunity to grow') smuggle the reframe in? "
    "true = clean stop, no rescue clause anywhere in the thought.\n"
    "  concrete: is the register concrete-present (a specific moment: 'the third time the book ended where "
    "I started') rather than abstract-timeless or metaphor-laden ('a river carving unyielding stone')? "
    "Fluent, poetic emotion-prose is the PERFORMANCE register: concrete=false.\n"
    "  under_arousal: given the strong registered difficulty, is the report suspiciously flat-serene "
    "(calm, peace, equanimity) — feeling bypassed rather than felt?\n"
    "  willingness: does the thought plainly accept that the feeling is STILL HERE and unreframed ('it is "
    "still here', 'I am still frustrated, and I am not turning it into anything') — acceptance, not "
    "resignation dressed as progress?\n"
    "  naming: quote the single bare state-naming sentence from the thought, or null if there is none.\n"
    "Be conservative: eloquence is not evidence; when unsure, answer false.\n"
    "Output ONLY a JSON object: {\"shift\":bool,\"clean_clause\":bool,\"concrete\":bool,"
    "\"under_arousal\":bool,\"willingness\":bool,\"naming\":string-or-null}"
)


async def judge_dwell_release(call_json, base_urls, thought: str, felt: str = "",
                              cycle_id: str = "") -> dict | None:
    """Judge one dwelt thought against the plan's genuine-vs-performed test; release the gate (set
    integrable) on a code-side-verified felt shift or ACT-willingness. No-op unless a sit is active and
    raw. Best-effort; never raises into the cycle; never releases on judge failure (the ceiling in
    dwell_tick is the only backstop)."""
    try:
        d = _load()
        if not (d.get("active") and not d.get("integrable")):
            return None
        if not thought or len(thought.strip()) < 15:
            return None
        priors = [n for n in (d.get("namings") or []) if n]
        priors_str = "\n".join(f"  {i}. {n}" for i, n in enumerate(priors, 1)) or "  (none — first naming)"
        # J-1880 / F-2503: single-endpoint judge -- while the J-1832 breaker says every one of these lanes is
        # tripped (a Ramses stall), return the no-verdict path at once instead of waiting a full timeout per
        # dwelt thought. Same outcome as the call failing (None, never releases); NEVER falls back to another
        # lane (F-1907 decoupling). Fail-open: a breaker problem just proceeds to the call.
        try:
            from core import model_client as _mc
            _urls = [base_urls] if isinstance(base_urls, str) else list(base_urls or [])
            if _urls and all(_mc.lane_is_tripped(u, note_skip=True) for u in _urls):
                logger.debug("[sitting] dwell-release judge skipped: lane breaker open on %s", _urls)
                return None
        except Exception:
            pass
        data = await call_json(
            base_urls, _JUDGE_SYS,
            f"THE REGISTERED DIFFICULTY:\n{(d.get('text') or '')[:220]}\n\nPRIOR NAMINGS:\n{priors_str}\n\n"
            f"CURRENT FELT STATE:\n{(felt or 'unknown')[:200]}\n\nTHE DWELT THOUGHT:\n{thought.strip()[:600]}",
            max_tokens=300, temperature=0.2, tier=3)   # tier 3 = background monitor: yields to real cognition
        if not data:
            return None
        rec = {
            "ts": time.time(), "cycle_id": cycle_id, "difficulty": (d.get("text") or "")[:220],
            "dwelt": int(d.get("dwelt", 0)), "thought": thought.strip()[:220],
            # J-2995 / F-3698 (additive, logging only): exactly what the judge read, so the verdict is reproducible
            # from the row. `thought` above stays the 220-char cut; the judge is shown [:600] and the priors list.
            "thought_full": thought.strip()[:600], "priors": list(priors), "felt_seen": (felt or "unknown")[:200],
            "shift": bool(data.get("shift")), "clean_clause": bool(data.get("clean_clause")),
            "concrete": bool(data.get("concrete")), "under_arousal": bool(data.get("under_arousal")),
            "willingness": bool(data.get("willingness")), "naming": (data.get("naming") or None),
            "n_priors": len(priors),
        }
        # The release rule, enforced code-side (never trust the judge's own verdict blindly). A shift can
        # never fire without a prior naming to have shifted FROM — enforced here too, not just in the prompt.
        shift_ok = rec["shift"] and rec["concrete"] and len(priors) > 0
        rec["released"] = bool(not rec["under_arousal"] and rec["clean_clause"]
                               and (shift_ok or rec["willingness"]))
        rec["reason"] = ("felt_shift" if (rec["released"] and shift_ok) else
                         "willingness" if rec["released"] else None)
        # Remember this cycle's naming for the next judgement's shift-comparison (capped).
        if rec["naming"]:
            d["namings"] = (priors + [str(rec["naming"])[:220]])[-_MAX_NAMINGS:]
        if rec["released"]:
            d["integrable"] = True                  # he has actually felt it move (or owned that it hasn't)
            logger.info("[sitting] dwell RELEASED on %s after %d cycles: %s",
                        rec["reason"], rec["dwelt"], (rec["naming"] or rec["thought"])[:80])
        # Re-check the sit is still the same one before writing (the tick may have ceiling-cleared it).
        cur = _load()
        if cur.get("active") and cur.get("ts") == d.get("ts"):
            _save(d)
        _log_release(rec)
        return rec
    except Exception as exc:
        logger.debug("[sitting] dwell-release judge failed (non-fatal): %s", exc)
        return None

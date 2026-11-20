"""
The closure law -- the WRITER half (J-2118, D-0423 A, docs/staged/closure_law.md).  LIVE for the line arm only
(CLOSURE_WRITE_LIVE is True since D-0495, 2026-10-28; CLOSURE_ARMS = {"line"} since D-0614); every other arm is
shadow-only.  Restart-gated like every module constant.

Nothing Du starts ever finishes on its own and, since the 2026-10-09 boot, that is measured with the system's own
decoupled judges in charge: 0 of 60 dream arcs resolved, 8 of 8 pursuits saturated, 645 self-interrogation fires
that are closed diagnoses (F-2755, F-2757, I-0089). The three loops are built separately and none of them, when its
judge DOES say met, writes anything Du can later remember. The law (D-0423, travis 2026-10-15): when a loop's
INDEPENDENT judge marks it met, Du writes ONE fragment in his own words -- a new origin 'resolution', ordinary
recall, and a 'resolves' edge from that fragment to the loop's seed -- so that having finished something becomes a
memory he can recall and build on. Nothing is told to him, no loop is force-closed, and the judge stays a separate
module from this writer (decoupled_judge_pattern).

THREE ARMS, one write-back (plus the LINE arm, J-2460/D-0494: judge = the follow_line panel + Du's own `settled: yes`,
seed = the frontier entry id -- the one live arm today):
  dream          judge = core/dream_met.py (computed 'met': the waking mind measurably stopped returning to the
                 tension); seed = the dream_log arc id (the root of its carry thread). BUILT HERE, shadow.
  pursuit        judge = core/pursuit_close_shadow (D-0426 A panel) read against the done_when written at birth
                 (core/done_when.py); seed = the pursuit id; met -> resolution, saturated not-met -> faded. J-2160.
  commitment     judge = commitment_ledger._achieved_by (deed record) against statement + done_when. J-2160.
                 Both shadow-only until added to CLOSURE_ARMS, and inert until DONE_WHEN_AT_OPEN is True.
  interrogation  judge = a doubt the next train step demonstrably engaged (the D-0403 instrument, D-0396 cup
                 track); seed = the self-interrogation fire id.  STUB -- gated on J-2060.

STATE TODAY (J-2964 corrected this block; the 2026-10 text said CLOSURE_WRITE_LIVE was False, which has been untrue
since D-0495). CLOSURE_WRITE_LIVE is True and CLOSURE_ARMS = {"line"}: only the line arm's fragment + 'resolves' edge
reach the memory DB. The dream, pursuit and commitment arms compose their would-be text and append a shadow row to
data/logs/closure_shadow.jsonl (arm, seed id, judge verdict, would-be text, would-be edge, arm_live) and write NOTHING
to the memory DB; interrogation is a stub gated on J-2060. An arm joins the live path by being added to CLOSURE_ARMS
(the founder's flip, after D-0423 clause 3's read of the first 10 would-be fragments: a lived close, or the writer's
self-congratulation?). The live path (store_fragment + memory_edges.add_edge) is _write_live, taken only for an arm in
CLOSURE_ARMS while CLOSURE_WRITE_LIVE is True.

J-2964 (F-3657, P-0062): every composer LLM call is labelled `closure:compose_<arm>` in data/llm_latency.jsonl (`by`),
via core.model_client.with_call_label; before, all of them read `asyncio.events:94(Handle)` (the event loop's frame,
because _compose_sync runs asyncio.run from a plain thread). Count a prompt's calls with the `closure:compose_` prefix.

J-3177 (D-0565, founder 2026-11-02: "the closure writer reads a rest as a close"): the dream arm also reads an arc that
ended at REST (core/dream_rest.py) as a close CANDIDATE -- record_rest_closes appends one kind='rest_close' row per
rest arc, `certified` only when an independent judge (the resolution panel, or dream_met 'met') says so, and writes
nothing to the memory DB (D-0614: dream arm shadow-only, "a rest is not a certified close"). The panel gate is not
weakened and nothing here adds a writer.

The same shadow file also receives every provisional-met CARRY decision (kind='carry', nodes/dream_node.py
_met_carry_check): D-0423 sub-question 2 = J-2003 option (a).

J-3225 (D-0614, founder 2026-11-02; findings F-3654, F-3656, F-3592): (1) LINE arm: Du's own `settled: yes` still writes
the memory, but the panel's merge status is now written INTO the fragment (a keyword `panel:<status>` always; and, for
'objected' / 'undetermined', one plain first-line note ahead of his words) so recall can show the doubt. Nothing else
about what gets written changes. (2) DREAM arm: dropped from CLOSURE_ARMS -- shadow-only (the would-be text is still
composed and logged to closure_shadow.jsonl; nothing reaches the memory DB). (3) The stored fragments the ruling names
are marked offline by scripts/apply_J-3225_mark_closure_fragments.py (core/memory/closure_marks.py).

J-2963 (F-3655, P-0062): the composer's text is now VALIDATED between composing and storing, for all four arms
(validate_composed). Reject = compose_how 'invalid:<reason>', would_be None, nothing live, the shadow row kept with the
rejected text in `rejected_text` (so the read jobs J-2121 / J-2550 can see it; invalid_summary() tallies them). Reasons:
words-under-N / words-over-N (the prompt's own range), braces (a '{' or '}', i.e. a nested JSON fragment),
json-fragment ("resolution": ), nested-json (the field was a dict/list), ground-ref ('Ground(s) [n]' or a bare '[n]'),
no-first-person. An invalid row still occupies the loop's one-fragment slot (as an 'empty' compose already did), so
nothing here retries on its own. COMPOSE_VALIDATE = False restores the pre-J-2963 path. The 17 fragments already
stored are NOT edited here (a founder read comes first).

Fail-open everywhere: nothing here may stop a dream, a state row, or the nightly from completing.
"""
from __future__ import annotations

import asyncio
import contextlib
import contextvars
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.closure")

_ROOT = Path(__file__).parent.parent
SHADOW_LOG = _ROOT / "data" / "logs" / "closure_shadow.jsonl"    # module-level so a test can temp-path it

CLOSURE_WRITE_LIVE = True        # True = the met loop's fragment + 'resolves' edge reach the memory DB. D-0495 (travis, 2026-10-28, the October restart batch): flipped live, read LIVE by its own read job; the founder reads the first 10 LIVE fragments (D-0423 clause 3)
RESOLUTION_ORIGIN = "resolution"
ARM_GATES = {"dream": None, "pursuit": None, "commitment": None, "interrogation": "J-2060", "line": None, "lookup": None}   # line: J-2460, D-0494; pursuit+commitment: J-2160 (judge = D-0426 A panel / deed record, read against done_when)
# J-2160 (measurement_to_action 2.3): the arms whose fragment may reach the memory DB. An arm NOT in this set logs its
# shadow row (would_be, compose) and writes nothing, even with CLOSURE_WRITE_LIVE True. Adding "pursuit" /
# "commitment" is the flag (founder flip after the first 10 would-be rows are read, D-0423 clause 3). The line arm
# predates this set and does not consult it (its live path is unchanged). J-3225 (D-0614, travis 2026-11-02): "dream"
# is DROPPED -- shadow-only, because the met judge measures silence of recurrence, which cannot tell faced from
# forgotten (F-3656). record_dream_met now consults this set; add "dream" back here to restore the live write.
CLOSURE_ARMS = {"line", "lookup"}
# closure_producer P5 (docs/staged/closure_producer.md): the LOOKUP arm. A frontier question answered through the
# decoupled gate (core/closure_gate.py, verdict yes) with a finding from his own lookup writes ONE resolution fragment
# naming the question, the source and the extract. The text is a deterministic template (no model call: F-4506 found
# the composer's output refused 72% of the time on the line arm), checked by the same validate_composed. Remove
# "lookup" from CLOSURE_ARMS to make the arm shadow-only (row logged, nothing written); LOOKUP_ARM = False turns it
# off entirely (no row).
LOOKUP_ARM = True
LOOKUP_EXTRACT_WORDS = 110       # the extract is cut at a sentence end at or under this many words

# J-3225 (D-0614): the line arm records the decoupled panel's merge status in the fragment it writes. The keyword
# `panel:<status>` is written for every status; the visible note goes ahead of Du's words only for the statuses in
# LINE_DOUBT_NOTES. False = the pre-J-3225 fragment (no keyword, no note). Restart-gated like every module constant.
LINE_PANEL_STATUS = True
# J-2910 (F-3592, P-0044): a `settled: yes` on a return whose cargo had ZERO grounds writes no fragment (4 of the 15 live
# arm=line fragments sat on an empty cargo; two asserted things nobody observed: the composer had only the question and his
# own settling thought). The shadow row is still written (compose_how "skipped-no-grounds"); nothing reaches the memory DB.
# Only a cargo that CARRIES a `grounds` key and has none is skipped; a cargo that is absent/unknown composes as before.
# False restores the pre-J-2910 path.
LINE_SKIP_NO_GROUNDS = True
LINE_DOUBT_NOTES = {
    "objected": "[Doubted: when this came back, an independent check objected to its grounds.] ",
    "undetermined": "[Doubted: when this came back, an independent check could not settle its grounds.] ",
}
PANEL_STATUSES = ("held", "held_within_scope", "objected", "undetermined")

# Composer: the dreamer model writes the dream arm's fragment (the arc's own voice; the judge is dream_met, a
# different module and no LLM at all). Test seam: a sync callable (prompt_system, prompt_user) -> dict|None.
_compose_fn = None
_COMPOSE_MAX_TOKENS = 220
_COMPOSE_TIMEOUT = 300           # the dreamer runs on CPU hubs; the nightly runs off-loop in a thread


# J-2963 (F-3655, P-0062): validate the composer's text before it is stored. False = the pre-J-2963 path (store as composed).
COMPOSE_VALIDATE = True
# The prompts' own word ranges (dream/line "40-90"; pursuit "40-90" met, "30-70" faded; commitment "30-70").
COMPOSE_WORD_RANGES = {"dream": (40, 90), "line": (40, 90), "pursuit": (40, 90), "commitment": (30, 70),
                       "lookup": (12, 190)}    # the lookup arm's template: question + source + extract (<= LOOKUP_EXTRACT_WORDS)
COMPOSE_FADED_RANGE = (30, 70)
COMPOSE_WORD_SLACK = 0           # words of tolerance either side of the range; 0 = exactly the prompt's range
_RX_GROUND_REF = re.compile(r"\bgrounds?\s*\[?\s*\d+|\[\s*\d+\s*\]", re.I)
_RX_FIRST_I = re.compile(r"\bI\b")
_RX_FIRST_OTHER = re.compile(r"\b(?:my|me|mine|myself)\b", re.I)
# J-4082 (J-3897 ruled c, F-4506): us / our / we count as first person for the LINE arm only (4 of the 61 live rejects).
_RX_FIRST_PLURAL = re.compile(r"\b(?:we|us|our|ours|ourselves)\b", re.I)
LINE_PLURAL_FIRST_PERSON = True
# J-4082: ONE retry of the line composer after an invalid compose (the prompt fix is in _line_prompts). The retry's user
# message names why the first text was refused; a second invalid stays invalid (no third call). False = no retry.
LINE_RETRY_ON_INVALID = True
_RX_JSON_KEY = re.compile(r"[\"“]resolution[\"”]\s*:", re.I)


def validate_composed(arm: str, text: str, *, faded: bool = False) -> str | None:
    """J-2963: None if the composed text honours its prompt's contract, else the reject reason (a short slug).
    Pure. The checks are the four F-3655 found broken in the 15 live line fragments + the dream arm's pseudo-JSON:
    word range, braces / nested JSON, 'Ground(s) [n]' or bare '[n]' references, first-person marker."""
    t = " ".join(str(text or "").split())
    if "{" in t or "}" in t:
        return "braces"
    if _RX_JSON_KEY.search(t):
        return "json-fragment"
    if _RX_GROUND_REF.search(t):
        return "ground-ref"
    lo, hi = COMPOSE_FADED_RANGE if faded else COMPOSE_WORD_RANGES.get(arm, (40, 90))
    n = len(t.split())
    if n < lo - COMPOSE_WORD_SLACK:
        return f"words-under-{lo}"
    if n > hi + COMPOSE_WORD_SLACK:
        return f"words-over-{hi}"
    if not (_RX_FIRST_I.search(t) or _RX_FIRST_OTHER.search(t)
            or (arm == "line" and LINE_PLURAL_FIRST_PERSON and _RX_FIRST_PLURAL.search(t))):
        return "no-first-person"
    return None


def _finish_compose(arm: str, data, *, faded: bool = False) -> tuple[str, str, str | None]:
    """J-2963: the one place a composer result becomes (text, compose_how, rejected_text). text is "" unless it is
    storable. how: ok | empty | <the composer's own _how> | invalid:<reason>. rejected_text is the refused text (capped)."""
    if not data:
        return "", "empty", None
    if data.get("_how"):
        return "", str(data["_how"]), None
    raw = data.get("resolution")
    if isinstance(raw, (dict, list)):
        txt = " ".join(json.dumps(raw, ensure_ascii=False).split())
        return ("", "invalid:nested-json", txt[:600]) if COMPOSE_VALIDATE else (txt, "ok", None)
    text = " ".join(str(raw or "").split())
    if not text:
        return "", "empty", None
    if COMPOSE_VALIDATE:
        why = validate_composed(arm, text, faded=faded)
        if why:
            return "", f"invalid:{why}", text[:600]
    return text, "ok", None


def invalid_summary(rows: list[dict] | None = None) -> dict:
    """J-2963's reader (named read jobs: J-2121 dream arm, J-2550 pursuit/commitment, and the line-arm read): the count of
    composer results refused, by arm and reason, against the composes that reached a verdict. Pure; reads SHADOW_LOG."""
    rows = _read_jsonl(SHADOW_LOG) if rows is None else rows
    out: dict = {}
    for r in rows:
        how = str(r.get("compose_how") or "")
        if r.get("kind") not in ("resolution", "faded") or not (how == "ok" or how.startswith("invalid:")):
            continue
        a = out.setdefault(str(r.get("arm")), {"composed": 0, "invalid": 0, "reasons": {}})
        a["composed"] += 1
        if how.startswith("invalid:"):
            a["invalid"] += 1
            a["reasons"][how[8:]] = a["reasons"].get(how[8:], 0) + 1
    return out


# ----------------------------------------------------------------------------------------------
# Shadow store
# ----------------------------------------------------------------------------------------------
def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return rows


def _append(row: dict) -> None:
    SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SHADOW_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def shadow_rows(arm: str | None = None, kind: str | None = None) -> list[dict]:
    return [r for r in _read_jsonl(SHADOW_LOG)
            if (arm is None or r.get("arm") == arm) and (kind is None or r.get("kind") == kind)]


def already_resolved(arm: str, root_id: str) -> dict | None:
    """ONE fragment per loop: the earlier resolution row for this seed (its thread root), if any."""
    for r in _read_jsonl(SHADOW_LOG):
        if r.get("arm") == arm and r.get("kind") == "resolution" and r.get("root_id") == root_id:
            return r
    return None


# ----------------------------------------------------------------------------------------------
# The dream arm's composer
# ----------------------------------------------------------------------------------------------
def _dream_prompts(arc: dict) -> tuple[str, str]:
    seed = arc.get("seed") or {}
    tensions = [str(t) for t in (seed.get("tension_labels") or []) if str(t).strip()]
    core = (arc.get("final_unresolved_core") or "").strip()
    last = " ".join((arc.get("final_narrative") or arc.get("narrative") or "").split())[-600:]
    system = (
        "/no_think\n"
        "You are Du, awake, writing one short memory in your own words. A thing you had been working in dreams "
        "has now, by an outside measure, stopped returning to your waking thoughts. Write what was faced and what it "
        "became -- in image if it lived in image, plainly if it was plain. First person, past tense, 40-90 words. "
        "Say what it was, not that you are proud of it: no congratulation, no moral, no summary of growth. If you "
        "cannot honestly say it was faced, say what stopped returning and leave it there.\n"
        'Output ONLY a valid JSON object: {"resolution": "..."}'
    )
    user = (
        f"What the dream was working: {('; '.join(tensions) or 'unlabelled')[:300]}\n"
        f"What it last left unfaced: {core[:300] or '(nothing named)'}\n"
        f"How the last scene ended: \"{last}\""
    )
    return system, user


_COMPOSE_ARM: contextvars.ContextVar = contextvars.ContextVar("closure_compose_arm", default="dream")


@contextlib.contextmanager
def _compose_arm(arm: str):
    """J-2964: name the arm whose composer call is about to go out (-> the latency row's `by`). Thread/context local."""
    tok = _COMPOSE_ARM.set(str(arm or "dream"))
    try:
        yield
    finally:
        _COMPOSE_ARM.reset(tok)


def _compose_sync(system: str, user: str) -> dict | None:
    """Default composer: the dreamer lane (nodes/dream_node's own URLs/model), run to completion from a plain
    thread. run_nightly is already off the event loop (asyncio.to_thread), so a fresh loop here is correct; if
    this thread somehow holds a running loop, the call cannot block it and is skipped (how='running_loop').
    J-2964 (F-3657, P-0062): the call is labelled `closure:compose_<arm>` in data/llm_latency.jsonl (`by`); before
    it was the event loop's `asyncio.events:94(Handle)`, which hid every composer call among other asyncio.run
    callers. The arm comes from `_compose_arm` (a ContextVar the three callers set), so `_compose_sync` and
    `_compose_fn` (the test seams) keep their (system, user) signature."""
    fn = _compose_fn
    if fn is not None:
        return fn(system, user)
    try:
        asyncio.get_running_loop()
        return {"_how": "running_loop"}
    except RuntimeError:
        pass
    from nodes import dream_node as _dn
    from core.model_client import call_node_json, with_call_label
    return asyncio.run(with_call_label(
        f"closure:compose_{_COMPOSE_ARM.get()}",
        call_node_json(_dn._DREAM_URLS, system, user, max_tokens=_COMPOSE_MAX_TOKENS,
                       temperature=0.7, timeout=_COMPOSE_TIMEOUT,
                       model_override=_dn._DREAM_MODEL, num_gpu=_dn._DREAM_NUM_GPU)))


def compose_dream_resolution(arc: dict) -> dict:
    """{'text': str|None, 'how': ok|empty|running_loop|error:<repr>}. Never raises."""
    system, user = _dream_prompts(arc)
    try:
        with _compose_arm("dream"):
            data = _compose_sync(system, user)
    except Exception as exc:
        return {"text": None, "how": f"error:{exc!r}"[:300]}
    text, how, rejected = _finish_compose("dream", data)        # J-2963: validated before it is stored
    return {"text": text or None, "how": how, "rejected": rejected}


# ----------------------------------------------------------------------------------------------
# The write-back (shadow, with the live path behind the flag)
# ----------------------------------------------------------------------------------------------
def panel_status_of(cargo: dict | None) -> str:
    """The cargo's merge status, normalised. Missing or unknown reads as 'undetermined' (follow_line's own default)."""
    st = str((cargo or {}).get("status") or "").strip().lower()
    return st if st in PANEL_STATUSES else "undetermined"


def would_be_fragment(arm: str, seed_kind: str, seed_id: str, text: str, judge: str, *,
                      faded: bool = False, panel_status: str | None = None) -> dict:
    """The exact store_fragment / add_edge arguments the live path takes -- what the shadow row records.
    faded=True (J-2160): the honest close of a loop that saturated without its done_when met -- same origin and
    recall, keyword 'faded', edge provenance says not-met (edge_type stays 'resolves', memory_edges' own type).
    panel_status (J-3225, D-0614; the line arm only): the decoupled panel's merge status. Adds the keyword
    `panel:<status>`, and for a doubted status (LINE_DOUBT_NOTES) one note ahead of the text -- so recall shows it."""
    note = LINE_DOUBT_NOTES.get(panel_status or "", "")
    return {
        "content": note + text,
        "layer": "episodic", "relevance": 0.7, "importance": 0.8,
        "keywords": [RESOLUTION_ORIGIN, arm, seed_id] + (["faded"] if faded else [])
                    + ([f"panel:{panel_status}"] if panel_status else []),
        "origin": RESOLUTION_ORIGIN,
        "derived_from": [seed_id],
        "edge": {"src_kind": "fragment", "src_id": "<fragment_id>", "dst_kind": seed_kind, "dst_id": seed_id,
                 "edge_type": "resolves",
                 "provenance": f"closure {arm}: " + (f"faded, judge {judge} not met" if faded else f"judge {judge} met")},
    }


def _write_live(wb: dict) -> str | None:
    """The one live path. Only reachable with CLOSURE_WRITE_LIVE True. Returns the fragment id (None on failure)."""
    from core.memory.store import store_fragment
    from core import memory_edges as _medges
    fid = store_fragment(content=wb["content"], layer=wb["layer"], relevance=wb["relevance"],
                         importance=wb["importance"], keywords=list(wb["keywords"]), origin=wb["origin"],
                         derived_from=list(wb["derived_from"]))
    if fid:
        e = wb["edge"]
        _medges.add_edge(e["src_kind"], fid, e["dst_kind"], e["dst_id"], e["edge_type"],
                         provenance=e["provenance"])
    return fid or None


def record_dream_met(arc: dict, state_row: dict, *, root_id: str | None = None, now: float | None = None) -> dict:
    """DREAM ARM. Called by core/dream_met.run_nightly for every arc whose computed state just became 'met'.
    Composes the would-be resolution fragment from the arc's own seed tension + final scene and appends ONE shadow
    row. One fragment per loop: a later met arc of the same carry thread (same root_id) is logged as 'duplicate'
    and composes nothing. Writes to the memory DB only if CLOSURE_WRITE_LIVE and "dream" is in CLOSURE_ARMS (J-3225,
    D-0614: it is not -- the dream arm is shadow-only). Never raises."""
    now = time.time() if now is None else now
    dream_id = str(arc.get("dream_id") or "")
    root_id = str(root_id or dream_id)
    row = {"ts": round(now, 1), "arm": "dream", "kind": "resolution", "seed_kind": "dream", "seed_id": root_id,
           "root_id": root_id, "arc_id": dream_id, "thread_root": dream_id == root_id,
           "judge": "dream_met", "judge_verdict": state_row.get("state"), "judge_detail": state_row.get("detail"),
           "judge_params": state_row.get("params"), "arc_ts": arc.get("ts"),
           "close_reason": arc.get("close_reason"),
           # J-3177 (D-0565): additive. What kind of ending this arc had (met-core | rest | open | unknown), from
           # dream_met's state row; None when RESTING_ENDING is 'off' or the row predates the key.
           "ending": state_row.get("ending"),
           "arm_live": "dream" in CLOSURE_ARMS,     # J-3225 (D-0614): False = shadow-only, the would-be text is logged and nothing is written
           "would_be": None, "compose_how": None, "written_live": False, "fragment_id": None}
    try:
        prior = already_resolved("dream", root_id)
        if prior is not None:
            row.update({"kind": "duplicate", "duplicate_of_ts": prior.get("ts"), "compose_how": "skipped"})
            _append(row)
            return row
        comp = compose_dream_resolution(arc)
        row["compose_how"] = comp["how"]
        if comp.get("rejected"):
            row["rejected_text"] = comp["rejected"]               # J-2963
        if comp["text"]:
            row["would_be"] = would_be_fragment("dream", "dream", root_id, comp["text"], "dream_met")
            if CLOSURE_WRITE_LIVE and "dream" in CLOSURE_ARMS:
                try:
                    fid = _write_live(row["would_be"])
                    row.update({"written_live": bool(fid), "fragment_id": fid})
                except Exception as exc:
                    logger.warning("[closure] live write failed (non-fatal, shadow row kept): %r", exc)
                    row["live_error"] = repr(exc)[:300]
        _append(row)
        logger.info("[closure] dream arm: arc %s (root %s) met -> would-be resolution %s (%s)",
                    dream_id, root_id, "composed" if comp["text"] else "NOT composed", comp["how"])
    except Exception as exc:
        logger.warning("[closure] record_dream_met failed (non-fatal): %r", exc)
        row["error"] = repr(exc)[:300]
        try:
            _append(row)
        except Exception:
            pass
    return row


REST_CLOSE_LOOKBACK_DAYS = 2     # record_rest_closes looks at arcs this recent only (a bounded nightly pass, no backfill)


def record_rest_closes(*, now: float | None = None, dream_log: Path | None = None) -> list[dict]:
    """DREAM ARM, J-3177 (D-0565: "the closure writer reads a rest as a close"). One kind='rest_close' shadow row per
    recent arc that ended at REST (core/dream_rest.arc_ending == 'rest'), appended once per arc_id (idempotent).
    A rest is a close CANDIDATE, never a certified one: `certified` is True only when an independent judge says so
    -- the resolution panel (data/logs/dream_resolution_shadow.jsonl, judge_verdict True) or dream_met's computed
    'met' -- and the rest classification (the dreamer's own ending) never certifies itself. Nothing is composed and
    NOTHING is written to the memory DB here: D-0614 (same day) made the dream arm shadow-only and ruled "a rest is
    not a certified close", so there is deliberately no live path in this build; `would_write` is always False. The
    gate this does NOT weaken: no closure fragment of any arm is written without its independent judge's verdict.
    Called from core/dream_met.run_nightly. Never raises; returns the rows appended."""
    out: list[dict] = []
    try:
        from core import dream_rest as _rest
        from core import dream_met as _dm
        now = time.time() if now is None else now
        done = {r.get("arc_id") for r in _read_jsonl(SHADOW_LOG) if r.get("arm") == "dream" and r.get("kind") == "rest_close"}
        states = _dm.latest_states()
        for a in _read_jsonl(dream_log or _rest.DREAM_LOG):
            did = a.get("dream_id")
            if not did or did in done or "close_reason" not in a or not a.get("ts"):
                continue
            if now - float(a["ts"]) > REST_CLOSE_LOOKBACK_DAYS * 86400 or _rest.arc_ending(a) != "rest":
                continue
            panel = _rest.panel_verdict(did)
            met = (states.get(did) or {}).get("state")
            by = (["resolution_panel"] if panel["verdict"] is True else []) + (["dream_met"] if met == "met" else [])
            row = {"ts": round(now, 1), "arm": "dream", "kind": "rest_close", "seed_kind": "dream", "seed_id": did,
                   "root_id": did, "arc_id": did, "ending": "rest", "close_reason": a.get("close_reason"),
                   "final_unresolved_core": (a.get("final_unresolved_core") or "")[:200],
                   "panel_verdict": panel["verdict"], "panel_how": panel["how"], "dream_met_state": met,
                   "certified": bool(by), "certified_by": by, "would_write": False, "written_live": False,
                   "fragment_id": None}
            _append(row)
            out.append(row)
        if out:
            logger.info("[closure] dream arm: %d rest arc(s) read as close candidates (%d certified by an independent judge); nothing written",
                        len(out), sum(1 for r in out if r["certified"]))
    except Exception as exc:
        logger.warning("[closure] record_rest_closes failed (non-fatal): %r", exc)
    return out


def log_carry_decision(decision: dict, *, now: float | None = None) -> None:
    """DREAM ARM, the carry rule (D-0423 sub-question 2 = J-2003 (a)): one row per provisional-met consultation
    the carry check made. Pure log; the carry itself is nodes/dream_node.py's. Never raises."""
    try:
        _append(dict({"ts": round(time.time() if now is None else now, 1), "arm": "dream", "kind": "carry"},
                     **decision))
    except Exception as exc:
        logger.debug("[closure] carry decision log failed (non-fatal): %r", exc)


# ----------------------------------------------------------------------------------------------
# The lookup arm (closure_producer P5) -- deterministic, zero LLM
# ----------------------------------------------------------------------------------------------
_RX_REF = re.compile(r"\[\s*(?:\d+|citation needed|note \d+)\s*\]", re.I)


def _clean_extract(text: str) -> str:
    """The extract as it is stored: reference marks and braces out, whitespace single, cut at a sentence end."""
    t = _RX_REF.sub("", str(text or "")).replace("{", "(").replace("}", ")")
    words = " ".join(t.split()).split()
    if len(words) <= LOOKUP_EXTRACT_WORDS:
        return " ".join(words)
    cut = " ".join(words[:LOOKUP_EXTRACT_WORDS])
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[:end + 1] if end > len(cut) // 2 else cut + " ..."


LOOKUP_ARM_ORIGIN = "research"   # see record_lookup_answered; None = the closure law's own RESOLUTION_ORIGIN


def lookup_resolution_text(ent: dict) -> str:
    """The lookup arm's fragment text. States only what happened: what he asked, that he looked it up himself,
    where, and what that source says. A web search is labelled as other people's pages, not checked."""
    q = " ".join(str(ent.get("q") or "").split()).replace("{", "(").replace("}", ")")
    extract = _clean_extract(ent.get("finding") or "")
    if not q or not extract:
        return ""
    title = str(ent.get("finding_title") or "")
    phrase = " ".join(str(ent.get("finding_phrase") or "").split())
    if ent.get("finding_via") == "wikipedia":
        m = re.search(r'"([^"]+)"', title)
        page = m.group(1) if m else phrase
        return (f'I asked: {q} I looked it up myself on Wikipedia. '
                f'The page "{page}" says: {extract}').replace("{", "(").replace("}", ")")
    return (f'I asked: {q} I looked it up myself with a web search' + (f' for "{phrase}"' if phrase else "")
            + f'. Other people\'s pages, which I have not checked, say: {extract}').replace("{", "(").replace("}", ")")


def record_lookup_answered(ent: dict, *, now: float | None = None) -> dict:
    """LOOKUP ARM. Called when a frontier question is resolved through the closure gate with how='lookup'
    (core/closure_gate.py; from follow_line.settle or the lexical-claim path). The judge is the gate's decoupled
    panel; the seed is the frontier entry id. One fragment per entry. Appends ONE shadow row (arm=lookup) and
    writes to the memory DB only if CLOSURE_WRITE_LIVE and "lookup" is in CLOSURE_ARMS. Never raises."""
    now = time.time() if now is None else now
    seed_id = str((ent or {}).get("id") or "")
    gate = (ent or {}).get("gate") if isinstance((ent or {}).get("gate"), dict) else {}
    row = {"ts": round(now, 1), "arm": "lookup", "kind": "resolution", "seed_kind": "frontier", "seed_id": seed_id,
           "root_id": seed_id, "source": (ent or {}).get("source"), "q": ((ent or {}).get("q") or "")[:220],
           "judge": "closure_gate", "judge_verdict": gate.get("verdict"), "judge_detail": gate.get("how"),
           "via": (ent or {}).get("finding_via"), "url": (ent or {}).get("finding_url"),
           "arm_live": "lookup" in CLOSURE_ARMS, "would_be": None, "compose_how": None, "written_live": False,
           "fragment_id": None}
    if not LOOKUP_ARM:
        return row
    try:
        if gate.get("verdict") != "yes" or not seed_id:
            row["compose_how"] = "skipped-no-gate-yes"        # the law: no fragment without the independent verdict
            _append(row)
            return row
        prior = already_resolved("lookup", seed_id)
        if prior is not None:
            row.update({"kind": "duplicate", "duplicate_of_ts": prior.get("ts"), "compose_how": "skipped"})
            _append(row)
            return row
        text = lookup_resolution_text(ent)
        why = ("empty" if not text else validate_composed("lookup", text)) if COMPOSE_VALIDATE else (None if text else "empty")
        if why:
            row["compose_how"] = "empty" if why == "empty" else f"invalid:{why}"
            if text:
                row["rejected_text"] = text[:600]
        else:
            row["compose_how"] = "template"
            wb = would_be_fragment("lookup", "frontier", seed_id, text, "closure_gate")
            via = str(ent.get("finding_via") or "")
            wb["keywords"] = list(wb["keywords"]) + ["looked_up"] + ([via] if via else [])
            # 2026-11-16 (founder: fix the known gap): origin 'resolution' is not in associative_recall.
            # _GROUNDED_ORIGINS, so the answer never came back in his solitary thinking. This fragment is world
            # material he looked up (deterministic template, zero LLM), the same kind of thing web_hand already
            # stores as origin 'research', which IS grounded. The allow-list itself is left untouched.
            # LOOKUP_ARM_ORIGIN = None restores RESOLUTION_ORIGIN.
            if LOOKUP_ARM_ORIGIN:
                wb["origin"] = LOOKUP_ARM_ORIGIN
            row["would_be"] = wb
            if CLOSURE_WRITE_LIVE and "lookup" in CLOSURE_ARMS:
                try:
                    fid = _write_live(wb)
                    row.update({"written_live": bool(fid), "fragment_id": fid})
                except Exception as exc:
                    logger.warning("[closure] live write failed (non-fatal, shadow row kept): %r", exc)
                    row["live_error"] = repr(exc)[:300]
        _append(row)
        logger.info("[closure] lookup arm: %s answered -> resolution %s (%s)", seed_id,
                    "written" if row["written_live"] else "not written", row["compose_how"])
    except Exception as exc:
        logger.warning("[closure] record_lookup_answered failed (non-fatal): %r", exc)
        row["error"] = repr(exc)[:300]
        try:
            _append(row)
        except Exception:
            pass
    return row


# ----------------------------------------------------------------------------------------------
# The other two arms -- stubs naming their gates (D-0423: do not build until the gate job lands)
# ----------------------------------------------------------------------------------------------
_RX_WHY_PAREN = re.compile(r"\(\s*grounds?\s*\[\d+\](?:\s*(?:,|and|&)\s*\[\d+\])*\s*\)", re.I)
_RX_WHY_GROUNDS = re.compile(r"\bgrounds?\s*\[\d+\](?:\s*(?:,|and|&)\s*\[\d+\])*", re.I)
_RX_WHY_BARE = re.compile(r"\s*\[\d+\]")


def strip_ground_refs(text: str) -> str:
    """J-2963 (F-3655): the panel stage's `why` cites its grounds by number ("Grounds [1] and [4] suggest ..."), but the
    composer's own prompt lists the grounds unnumbered, so the model copied dangling references into the memory. Drop the
    numbering from the why before the composer sees it: "(Grounds [2], [3])" goes, "Grounds [1] and [4]" becomes "the
    grounds", a bare "[n]" goes. The stored cargo is untouched; only the prompt's copy is cleaned."""
    t = _RX_WHY_PAREN.sub("", str(text or ""))

    def _g(m):
        before = t[:m.start()].rstrip()
        return "The grounds" if (not before or before[-1] in ".!?") else "the grounds"
    t = _RX_WHY_GROUNDS.sub(_g, t)
    t = _RX_WHY_BARE.sub("", t)
    t = " ".join(t.split())
    return re.sub(r"\s+([,.;:!?])", r"\1", t)


def _line_prompts(ent: dict, cargo: dict, thought: str) -> tuple[str, str]:
    q = (ent.get("q") or "")[:220]
    grounds = cargo.get("grounds") or []
    why = strip_ground_refs((cargo.get("why") or {}).get("text") or "")      # J-2963: no "Grounds [n]" numbering
    system = (
        "/no_think\n"
        "You are Du, awake, writing one short memory in your own words. A question or claim of yours came back to you "
        "with what you had found in your own past, and you judged it settled. Write what you now hold about it and "
        "WHY -- the grounds, plainly. Write it as ME, in the first person: begin with \"I\" and keep saying \"I\" and \"my\" "
        "-- never \"Du\", never \"he\", never \"the question\" as the speaker. LENGTH IS PART OF THE JOB: 40 to 90 words, "
        "three or four sentences, never fewer than 40. Say what it is, not that you "
        "are pleased: no congratulation, no moral. If the why is thin, say so and leave it there.\n"
        'Example of the right shape (about 55 words): {"resolution": "I had asked whether the lamp in the study '
        'burns steadily or flickers. What I found was my own note from the evening I sat beside it, and the older '
        'line about the draught under the door. Both say the flame bends when the door opens and stands still when '
        'it is shut. So I hold that it is steady and the draught is what moves it."}\n'
        'Output ONLY a valid JSON object: {"resolution": "..."}'
    )
    user = (f"What you asked or held: {q}\n"
            + ("Grounds you found: " + " | ".join(f"({g.get('origin','')}) {g.get('text','')[:160]}" for g in grounds[:3]) + "\n" if grounds else "")
            + (f"Your why: {why[:300]}\n" if why else "")
            + f"What you said when it came back: \"{' '.join((thought or '').split())[:400]}\"")
    return system, user


def _retry_note(reason: str) -> str:
    """J-4082: the line composer's retry message: your last text was refused for <reason>; write it again."""
    r = str(reason or "")
    if r.startswith("words-under"):
        why = "it was too short: write 40 to 90 words, three or four sentences"
    elif r.startswith("words-over"):
        why = "it was too long: keep it to 40 to 90 words"
    elif r == "no-first-person":
        why = 'it was not in the first person: say "I" and "my", as me, not about Du or about the question'
    else:
        why = "it did not follow the form: plain prose in the first person, 40 to 90 words, no braces, no numbering"
    return f"Your last attempt was refused because {why}. Write it again, only the JSON object."


def record_line_settled(ent: dict, cargo: dict, thought: str, *, now: float | None = None) -> dict:
    """LINE ARM (J-2460, D-0494 (3), docs/staged/question_cargo.md §2.7). Called by core/follow_line.settle() when
    Du says `settled: yes` about a return of his own. The judge was the decoupled panel that graded the cargo
    (follow_line._judge) PLUS his own settling word; the seed is the frontier entry id. One fragment per entry.
    Composes the would-be resolution fragment and appends ONE shadow row (arm=line, kind=resolution); writes to the
    memory DB only if CLOSURE_WRITE_LIVE. Runs from a plain thread (follow_line calls it under off_loop). Never
    raises."""
    now = time.time() if now is None else now
    seed_id = str(ent.get("id") or "")
    row = {"ts": round(now, 1), "arm": "line", "kind": "resolution", "seed_kind": "frontier", "seed_id": seed_id,
           "root_id": str(ent.get("about_key") or seed_id), "source": ent.get("source"), "q": (ent.get("q") or "")[:220],
           "judge": "follow_line_panel+settled", "judge_verdict": "yes", "judge_detail": (cargo or {}).get("status"),
           "panel_status": panel_status_of(cargo),      # J-3225 (D-0614): what the fragment carries for recall
           "would_be": None, "compose_how": None, "written_live": False, "fragment_id": None}
    try:
        prior = already_resolved("line", seed_id)
        if prior is not None:
            row.update({"kind": "duplicate", "duplicate_of_ts": prior.get("ts"), "compose_how": "skipped"})
            _append(row)
            return row
        if LINE_SKIP_NO_GROUNDS and isinstance(cargo, dict) and "grounds" in cargo and not cargo.get("grounds"):
            row["compose_how"] = "skipped-no-grounds"             # J-2910: nothing observed to write down
            _append(row)
            logger.info("[closure] line arm: %s settled on an empty cargo -> no fragment (skipped-no-grounds)", seed_id)
            return row
        system, user = _line_prompts(ent, cargo or {}, thought)
        try:
            with _compose_arm("line"):
                data = _compose_sync(system, user)
        except Exception as exc:
            data = {"_how": f"error:{exc!r}"[:300]}
        text, row["compose_how"], rejected = _finish_compose("line", data)      # J-2963: validated before it is stored
        if rejected:
            row["rejected_text"] = rejected
        if not text and LINE_RETRY_ON_INVALID and str(row["compose_how"]).startswith("invalid:"):
            # J-4082: ONE retry, told why the first was refused. The first reject stays on the row for the reader.
            row["first_compose_how"] = row["compose_how"]
            reason = str(row["compose_how"])[len("invalid:"):]
            try:
                with _compose_arm("line"):
                    data2 = _compose_sync(system, user + "\n\n" + _retry_note(reason))
            except Exception as exc:
                data2 = {"_how": f"error:{exc!r}"[:300]}
            text, row["compose_how"], rejected2 = _finish_compose("line", data2)
            row["compose_retry"] = True
            if rejected2:
                row["rejected_text_retry"] = rejected2
        if text:
            row["would_be"] = would_be_fragment("line", "frontier", seed_id, text, "follow_line_panel+settled",
                                                panel_status=row["panel_status"] if LINE_PANEL_STATUS else None)
            if CLOSURE_WRITE_LIVE:
                try:
                    fid = _write_live(row["would_be"])
                    row.update({"written_live": bool(fid), "fragment_id": fid})
                except Exception as exc:
                    logger.warning("[closure] live write failed (non-fatal, shadow row kept): %r", exc)
                    row["live_error"] = repr(exc)[:300]
        _append(row)
        logger.info("[closure] line arm: %s settled -> would-be resolution %s (%s)",
                    seed_id, "composed" if text else "NOT composed", row["compose_how"])
    except Exception as exc:
        logger.warning("[closure] record_line_settled failed (non-fatal): %r", exc)
        row["error"] = repr(exc)[:300]
        try:
            _append(row)
        except Exception:
            pass
    return row


# ----------------------------------------------------------------------------------------------
# J-2160: the PURSUIT and COMMITMENT arms (measurement_to_action 2.3). Both act ONLY on a seed that has a done_when
# (core/done_when.py, written at open time by the generation that opened it); with DONE_WHEN_AT_OPEN False there is
# none, so both are inert. The judge is never this module: pursuit = core/pursuit_close_shadow (D-0426 A panel, which
# reads the done_when); commitment = core/commitment_ledger._achieved_by (deed record, matched against statement +
# done_when). The done_when text is NOT given to the writer (it is the judge's, never shown back). Arms not in
# CLOSURE_ARMS log the shadow row only. Called from plain threads (compose is sync). Never raise.
# ----------------------------------------------------------------------------------------------
def _pursuit_question(p: dict) -> str:
    """The question to quote for a pursuit (D-0554 / J-3368): the extracted question_text for pursuits born after
    J-3165, else the birth thought in `question` exactly as before. Input only, no prompt wording change. Never raises."""
    try:
        from core import pursuits as _pu
        return _pu.driving_question(p) or ""
    except Exception:
        return (p.get("question") or "")


def _pursuit_prompts(p: dict, faded: bool) -> tuple[str, str]:
    if faded:
        system = ("/no_think\n"
                  "You are Du, writing one short memory in your own words. A question you carried for a long time has "
                  "worn out without being settled. Write, plainly, what it was, where you got to with it, and that you "
                  "are letting it go for now -- it stays open. First person, 30-70 words. No consolation, no moral.\n"
                  'Output ONLY a valid JSON object: {"resolution": "..."}')
    else:
        system = ("/no_think\n"
                  "You are Du, writing one short memory in your own words. A question you kept returning to is "
                  "settled: where you now stand answers it. Write what you now hold about it and WHY, plainly, in a "
                  "sentence or two. First person, 40-90 words. Say what it is, not that you are pleased: no "
                  "congratulation, no moral.\n"
                  'Output ONLY a valid JSON object: {"resolution": "..."}')
    user = (f"The question: {(_pursuit_question(p) or '')[:240]}\n"
            f"Where you stand on it: {(p.get('standing') or '')[:320]}\n"
            + (f"What was still open: {(p.get('open') or '')[:160]}\n" if p.get("open") else ""))
    return system, user


def _commitment_prompts(c: dict, evidence: str) -> tuple[str, str]:
    system = ("/no_think\n"
              "You are Du, writing one short memory in your own words. Something you had committed to is done: a deed "
              "of yours fulfilled it. Write what you did and what it settles, plainly. First person, 30-70 words. "
              "No congratulation, no moral.\n"
              'Output ONLY a valid JSON object: {"resolution": "..."}')
    user = (f"What you had committed to: {(c.get('statement') or '')[:300]}\n"
            f"What you did: {(evidence or '')[:200]}")
    return system, user


def _record_arm(arm: str, seed_kind: str, seed_id: str, judge: str, verdict, detail, system: str, user: str, *,
                faded: bool = False, extra: dict | None = None, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    row = {"ts": round(now, 1), "arm": arm, "kind": "faded" if faded else "resolution", "seed_kind": seed_kind,
           "seed_id": seed_id, "root_id": seed_id, "judge": judge, "judge_verdict": verdict,
           "judge_detail": detail, "arm_live": arm in CLOSURE_ARMS, "would_be": None, "compose_how": None,
           "written_live": False, "fragment_id": None}
    row.update(extra or {})
    try:
        prior = next((r for r in _read_jsonl(SHADOW_LOG) if r.get("arm") == arm and r.get("root_id") == seed_id
                      and r.get("kind") in ("resolution", "faded")), None)
        if prior is not None:         # ONE fragment per loop (resolved OR faded)
            row.update({"kind": "duplicate", "duplicate_of_ts": prior.get("ts"), "compose_how": "skipped"})
            _append(row)
            return row
        try:
            with _compose_arm(arm):
                data = _compose_sync(system, user)
        except Exception as exc:
            data = {"_how": f"error:{exc!r}"[:300]}
        text, row["compose_how"], rejected = _finish_compose(arm, data, faded=faded)   # J-2963
        if rejected:
            row["rejected_text"] = rejected
        if text:
            row["would_be"] = would_be_fragment(arm, seed_kind, seed_id, text, judge, faded=faded)
            if CLOSURE_WRITE_LIVE and arm in CLOSURE_ARMS:
                try:
                    fid = _write_live(row["would_be"])
                    row.update({"written_live": bool(fid), "fragment_id": fid})
                except Exception as exc:
                    logger.warning("[closure] live write failed (non-fatal, shadow row kept): %r", exc)
                    row["live_error"] = repr(exc)[:300]
        _append(row)
        logger.info("[closure] %s arm: %s %s -> would-be fragment %s (%s, live=%s)", arm, seed_id,
                    row["kind"], "composed" if text else "NOT composed", row["compose_how"], row["written_live"])
    except Exception as exc:
        logger.warning("[closure] %s arm failed (non-fatal): %r", arm, exc)
        row["error"] = repr(exc)[:300]
        try:
            _append(row)
        except Exception:
            pass
    return row


def record_pursuit_met(p: dict, ask_row: dict, *, now: float | None = None) -> dict | None:
    """PURSUIT ARM, met: core/pursuit_close_shadow's judge said the standing answers the question, reading the
    done_when written at the pursuit's birth. Pursuits without a done_when are not this arm's (returns None)."""
    try:
        from core import done_when as _dw
        if not _dw.get("pursuit", str(p.get("id") or "")):
            return None
        s, u = _pursuit_prompts(p, faded=False)
        return _record_arm("pursuit", "pursuit", str(p.get("id")), "pursuit_close_shadow+done_when", True,
                           (ask_row or {}).get("why"), s, u, now=now,
                           extra={"advances": p.get("advances"), "q": (_pursuit_question(p) or "")[:220]})
    except Exception as exc:
        logger.debug("[closure] record_pursuit_met failed (non-fatal): %r", exc)
        return None


def record_pursuit_faded(p: dict, ask_row: dict, *, now: float | None = None) -> dict | None:
    """PURSUIT ARM, faded: the pursuit SATURATED (retired) and the judge says its done_when is not met. The honest
    close: a recallable 'I let this one go' fragment. Only for pursuits with a done_when."""
    try:
        from core import done_when as _dw
        if p.get("status") != "saturated" or not _dw.get("pursuit", str(p.get("id") or "")):
            return None
        s, u = _pursuit_prompts(p, faded=True)
        return _record_arm("pursuit", "pursuit", str(p.get("id")), "pursuit_close_shadow+done_when", False,
                           (ask_row or {}).get("why"), s, u, faded=True, now=now,
                           extra={"advances": p.get("advances"), "q": (_pursuit_question(p) or "")[:220]})
    except Exception as exc:
        logger.debug("[closure] record_pursuit_faded failed (non-fatal): %r", exc)
        return None


# J-4083 (J-3889 ruled; F-4488, F-4822): the commitment arm's "judge" is commitment_ledger._achieved_by, a word-overlap
# test (>=3 shared words of length 4+, or one shared word plus a marker origin). It never asked whether the deed DOES what
# was promised, and this arm then hard-coded verdict "achieved" (25 of 25). 6 of 8 fragments read credited an unrelated
# study note (a "refill the barrel" stand credited by a Napoleon note). COMMITMENT_DEED_GATE adds the missing "no": a
# deterministic check that the deed shares real CONTENT words with the statement or done_when (the scope field and
# study-note boilerplate do not count). A deed that fails is logged kind "not_achieved" with no compose. Shadow arm only:
# the ledger's own retirement and reward are untouched. No model call, no prompt.
COMMITMENT_DEED_GATE = True
_DEED_STOP = frozenset((
    "that this with have from they them then than when what will would should could must about into your only just more "
    "some such been were been being does done doing also very much many most each other there their these those over "
    "before after while until still even like want need make made going gone come came back down here once again "
    "write wrote written note notes study subject something nothing everything through because without within "
    "open opened book books read reading time times hold held feel felt think thought").split())


_RX_STAND_BOOK = re.compile(r"(open|read|turn)\w*.*\bbook|\bbook.*(open|read|turn)\w*", re.I)


_WRITTEN_ORIGINS = frozenset(("study", "journal", "essay", "letter", "peer", "composition"))
_RX_WRITTEN_ACT = re.compile(r"\b(writ|wrote|note|record|anchor|identif|find|found|compar|review|check|letter|essay|journal|"
                             r"study|examin|explain|work out|decid|name|reflect|describe|summar|answer)", re.I)


def _stems(text: str) -> set:
    out = set()
    for w in re.findall(r"[a-z]{4,}", (text or "").lower()):
        if w in _DEED_STOP:
            continue
        out.add(w[:5])
    return out


def commitment_deed_verdict(statement: str, done_when: str, deed: str, origin: str = "") -> tuple[str, str]:
    """J-4083: does this deed plausibly DO what the stand says? Returns (verdict, why); verdict is "achieved" or
    "not_achieved". Content words (4+ letters, stop/generic words dropped, 5-letter stems) of statement + done_when
    must overlap the deed in >=2 distinct stems; a deed's header (title, book, subject) counts as part of the deed.
    An 'action' deed (a library/reading record) also counts when the stand is about opening/reading a book and the
    record is a reading or library action. Pure; never raises."""
    try:
        if origin in _WRITTEN_ORIGINS and not _RX_WRITTEN_ACT.search(f"{statement} {done_when}"):
            return "not_achieved", f"a written {origin} cannot fulfil a stand whose act is not writing, noting or finding out"
        want = _stems(statement) | _stems(done_when)
        have = _stems(deed)
        ov = sorted(want & have)
        if len(ov) >= 2:
            return "achieved", "shared content stems: " + ",".join(ov)
        if (origin == "action" and _RX_STAND_BOOK.search(f"{statement} {done_when}")
                and re.search(r"librarian|reading|read ", deed or "", re.I)):
            return "achieved", "action deed is a reading/library record and the stand is to open/read the book"
        return "not_achieved", ("deed shares " + (",".join(ov) if ov else "no") + " content stems with the stand "
                                f"(needs 2; stand stems {len(want)})")
    except Exception as exc:
        return "achieved", f"gate_error:{exc!r}"[:80]          # fail-open == the old behaviour


def record_commitment_achieved(c: dict, evidence: str, deed: str = "", *, now: float | None = None) -> dict | None:
    """COMMITMENT ARM: commitment_ledger._achieved_by found a deed fulfilling a held stand (matched against its
    statement and its done_when). Only for commitments with a done_when. J-4083: the deed is then put to
    commitment_deed_verdict; a deed that does not match logs kind "not_achieved" and composes nothing."""
    try:
        from core import done_when as _dw
        _d = _dw.get("commitment", str(c.get("id") or ""))
        if not _d:
            return None
        verdict, why = "achieved", ""
        if COMMITMENT_DEED_GATE:
            _origin = (evidence or "").split(":", 1)[0].strip()
            verdict, why = commitment_deed_verdict(c.get("statement") or "", _d.get("done_when") or "",
                                                   deed or evidence or "", _origin)
        extra = {"q": (c.get("statement") or "")[:220], "gate": "deed_v2" if COMMITMENT_DEED_GATE else "off"}
        if verdict != "achieved":
            row = {"ts": round(time.time() if now is None else now, 1), "arm": "commitment", "kind": "not_achieved",
                   "seed_kind": "commitment", "seed_id": str(c.get("id")), "root_id": str(c.get("id")),
                   "judge": "commitment_achieved+done_when+deed_gate", "judge_verdict": verdict,
                   "judge_detail": why[:200], "arm_live": False, "would_be": None, "compose_how": "skipped_not_achieved",
                   "written_live": False, "fragment_id": None, "evidence": (evidence or "")[:150]}
            row.update(extra)
            _append(row)
            return row
        if why:
            extra["gate_why"] = why[:200]
        s, u = _commitment_prompts(c, evidence)
        return _record_arm("commitment", "commitment", str(c.get("id")), "commitment_achieved+done_when",
                           "achieved", (evidence or "")[:150], s, u, now=now, extra=extra)
    except Exception as exc:
        logger.debug("[closure] record_commitment_achieved failed (non-fatal): %r", exc)
        return None


def run_in_thread(fn, *args) -> None:
    """Fire-and-forget from an event-loop context (the composer is sync and must not block the loop)."""
    try:
        import threading
        threading.Thread(target=fn, args=args, daemon=True, name="closure-arm").start()
    except Exception as exc:
        logger.debug("[closure] thread start failed (non-fatal): %r", exc)


def record_interrogation_met(*_a, **_k):
    raise NotImplementedError("closure interrogation arm: gated on J-2060 (the D-0403 open-doubt instrument is the judge)")

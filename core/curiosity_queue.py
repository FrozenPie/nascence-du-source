"""
Nascence — Curiosity Queue (the exploration organ's inbound interface)
======================================================================
The append-only inbox that turns unresolved-but-non-actionable material into world-facing investigation.
Producers (the contradiction gate via meta_awareness, the world-facing half of prediction-error, and the
T4 insufficient-evidence branch) enqueue items; the CuriosityNode drains them as priority seeds. Part of
the curiosity flesh-out (docs/curiosity_flesh_out_plan.md, v3 — both auditors approved Phase 0).

Two auditor-mandated invariants are enforced HERE:
  • STRICT TYPE PARTITIONING — the queue accepts ONLY three structured sources (junk-drawer guard).
  • THE DE-PERSONALIZATION PRISM — a self-tension MUST exit world-facing (an academic question), never a
    first-person loop. `is_world_facing` is the deterministic firewall check; the prism prompt does the work.

LIVE (2026-06-24): `transform_and_seed` runs the prism AND seeds each world-facing result into the Frontier
(`frontier.note_question(..., "prism")`), so a recurring self-loop now EXITS as a grounded research question
he can go and answer — the missing redirect. The Phase-0 evidence cleared it: 40/40 transforms were world-facing
(100% prism success). Every transform is still logged to curiosity_shadow.jsonl for observability.
"""
from __future__ import annotations
import json
import logging
import re
import threading
import time
import uuid
from pathlib import Path

logger = logging.getLogger("nascence.curiosity_queue")

SOURCES = ("gate_dissonance", "world_prediction_error", "t4_insufficient_evidence")

from core import profile   # J-0846: NonLiveWriteError carve-out in transform_and_seed()

_QUEUE = Path(__file__).parent.parent / "data" / "curiosity_queue.jsonl"
_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "curiosity_shadow.jsonl"

# First-person self-reference — its presence in a "world-facing" question means the prism FAILED.
_FIRST_PERSON = re.compile(r"\b(i|i'm|i've|i'd|i'll|my|me|myself|mine|am i)\b", re.IGNORECASE)

# J-3033 / F-3737, F-3751 (restart-gated): the prism's input and its check.
#  - INPUT: the producer (nodes/meta_awareness_node.py) now carries the whole thought (<=400 chars, cut at a sentence
#    boundary) in the queue item's meta["full_text"]; raw_text stays the 90-char snippet (dedup key, old rows, readers).
#    transform_and_seed reads full_text and falls back to raw_text, so queued old rows work unchanged.
#  - CHECK: is_world_facing used to reject only first-person pronouns (490 of 491 "passed"). world_facing_verdict adds
#    three deterministic rejects, each logged with a reason: the house named (Travis / Nascence), an INVENTED fiction frame
#    (character / protagonist / narrator / poem / literary work that the input did not itself contain), and no content
#    noun from the input surviving into the question.
#  PRISM_V2 = False restores the old prompt, the raw_text input and the pronoun-only check (a rollback, not a mode).
PRISM_V2 = True

_HOUSE = re.compile(r"\b(travis|nascence)\b", re.IGNORECASE)
_FICTION_FRAME = re.compile(r"\b(characters?|protagonists?|narrators?|poems?|literary works?|narrative space|fictional)\b",
                            re.IGNORECASE)
_WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?", re.UNICODE)
_FIRST_PERSON_WORDS = {"i", "my", "me", "myself", "mine", "we", "our", "ours", "us", "you", "your"}
# stop / hedge / frame words: never count as the "content noun" the question must keep from the input
_STOP = set("""a about above across after again against all also although always among and another any are around as at
away back be because been before being below between both but by can could did does doesn done down during each either
else even ever every few for from further had has have having her here hers him his how however into its itself just
less like made make many may might more most much must near neither never next nor not now off often once only onto
other others otherwise our out over own perhaps quite rather really same shall she should since slightly so some
something still such than that the their theirs them then there these they thing things this those though through
thus till too toward under until upon very was were what when whenever where whether which while who whom whose why
will with within without would yet actual actually merely simply truly mere nothing everything anything
way ways kind sort part sense feel feels felt seem seems seemed becomes become became metaphor metaphors symbol
symbols story stories narrative narratives meaning meanings truth reality real physical presses confirms
echo echoes whisper whispers""".split())


def _stem(w: str) -> str:
    w = w.lower()
    if w.endswith("'s"):
        w = w[:-2]
    for suf in ("ing", "ed", "es", "ly", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def content_stems(text: str) -> set:
    """Stems of a text's content words: over 3 letters (or any non-ASCII word, e.g. a single CJK character), not a
    stop / hedge / frame word, not first-person. Deterministic, no model."""
    out = set()
    for w in _WORD.findall((text or "")):
        lw = w.lower()
        if lw in _STOP or lw in _FIRST_PERSON_WORDS:
            continue
        if len(lw) > 3 or not lw.isascii():
            out.add(_stem(lw))
    return out


def content_survival(question: str, source_text: str) -> float | None:
    """Share of the INPUT's content stems that appear in the question (None if the input has none). 0.0 means no
    content word from the input survived."""
    src = content_stems(source_text)
    if not src:
        return None
    return len(src & content_stems(question)) / len(src)


# RATE-LIMIT (2026-06-21): one recurring tension must not FLOOD the queue. The #1 unresolved knot (the
# made-mind keystone) is re-enqueued on EVERY T4 failure; left unchecked the shadow log showed it producing
# 11 near-identical self-questions in one run — which, if ever drained live, would launder the
# self-monoculture into curiosity. A little is fine; a flood is the disease. So the same tension re-enters
# the queue at most once per cooldown (and never while a copy is still pending). Deterministic — no LLM.
_DEDUP_COOLDOWN_S = 6 * 3600

# J-2026 / F-2626 (restart-gated): enqueue() is read-whole-file -> dedupe -> append, and mark_processed() is
# read-whole-file -> rewrite-whole-file. meta_awareness.scan (the enqueue caller in _enter_sleep) now runs in a
# worker thread (core.sleep_offloop) while transform_and_seed/mark_processed run on the loop thread, so a
# mark_processed rewrite could land between enqueue's append and its own read and DROP the appended row (or
# enqueue could dedupe against a half-truncated file). Whole-call serialisation of the three file touchers; re-entrant;
# the J-1909 _CO_RECALL_LOCK pattern. On a single thread it is a no-op, so behaviour there is unchanged.
_QUEUE_LOCK = threading.RLock()


def _dedup_key(raw_text: str) -> str:
    """Normalised identity of a tension (lowercase, whitespace-collapsed, truncated). The recurring knots are
    enqueued near-verbatim each time, so an exact-normalised match catches the flood — no embedding needed."""
    return " ".join((raw_text or "").lower().split())[:120]


def enqueue(source: str, raw_text: str, meta: dict | None = None) -> str | None:
    """Append one item. STRICT partitioning: rejects any source not in SOURCES (returns None). Returns the
    item id, or None if rejected/empty. Best-effort; never raises into the caller."""
    try:
        if source not in SOURCES:
            return None
        raw_text = (raw_text or "").strip()
        if not raw_text:
            return None
        # RATE-LIMIT: skip if the same tension is already pending, or re-entered within the cooldown — so the
        # #1 recurring knot enters occasionally, not 11x a run (which would feed the monoculture, not break it).
        with _QUEUE_LOCK:
            key, now = _dedup_key(raw_text), time.time()
            for prev in _read_all():
                if prev.get("source") == source and _dedup_key(prev.get("raw_text", "")) == key:
                    if prev.get("status") == "pending" or now - float(prev.get("ts", 0) or 0) < _DEDUP_COOLDOWN_S:
                        return None
            item = {"id": uuid.uuid4().hex[:10], "ts": time.time(), "source": source,
                    "raw_text": raw_text[:400], "status": "pending", "meta": meta or {}}
            q_path = profile.guard_path(_QUEUE)   # J-1820 / F-2442: fenced before any I/O; a non-live process is refused here and swallowed below
            q_path.parent.mkdir(parents=True, exist_ok=True)
            with open(q_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            return item["id"]
    except Exception as exc:
        logger.debug("[curiosity-queue] enqueue() failed (non-fatal): %s", exc)
        return None


def _read_all() -> list[dict]:
    try:
        with _QUEUE_LOCK:
            return [json.loads(l) for l in _QUEUE.read_text(encoding="utf-8").splitlines() if l.strip()] \
                if _QUEUE.exists() else []
    except Exception as exc:
        logger.debug("[curiosity-queue] _read_all() failed (non-fatal): %s", exc)
        return []


def read_pending(limit: int = 5) -> list[dict]:
    return [it for it in _read_all() if it.get("status") == "pending"][:limit]


def mark_processed(item_id: str) -> None:
    """Flip an item to processed (rewrite the small ledger). Best-effort."""
    try:
        q_path = profile.guard_path(_QUEUE)   # J-1820 / F-2442: fenced before any I/O; refusal swallowed below (best-effort, as before)
        with _QUEUE_LOCK:   # J-2026: the read-modify-write is one critical section vs enqueue()
            items = _read_all()
            for it in items:
                if it.get("id") == item_id:
                    it["status"] = "processed"
            q_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n",
                              encoding="utf-8")
    except Exception as exc:
        logger.debug("[curiosity-queue] mark_processed() failed (non-fatal): %s", exc)


def world_facing_verdict(question: str, source_text: str | None = None) -> tuple[bool, str]:
    """(ok, reason). reason is '' when ok, else the first failed check: 'empty', 'first_person', 'house_name',
    'invented_frame:<word>', 'no_input_noun'. The pronoun check is the original firewall; the other three are
    J-3033 (F-3751): the house named, a fiction frame the input did not contain, and no content word of the input
    surviving. With source_text None the frame check treats the input as containing no fiction word and the survival
    check is skipped. Deterministic, no model."""
    q = (question or "").strip()
    if not q:
        return False, "empty"
    if _FIRST_PERSON.search(q):
        return False, "first_person"
    if not PRISM_V2:
        return True, ""
    if _HOUSE.search(q):
        return False, "house_name"
    src = source_text or ""
    for m in _FICTION_FRAME.finditer(q):
        w = m.group(1).lower()
        if w.startswith("character") and re.search(r"[ɐ-￿]", q):
            continue   # a written character (e.g. the kanji of his own name, asked about as script), not a fiction character
        if not re.search(r"\b" + re.escape(w.split()[0].rstrip("s")), src, re.IGNORECASE):
            return False, "invented_frame:" + w
    if source_text:
        surv = content_survival(q, source_text)
        if surv is not None and surv <= 0.0:
            return False, "no_input_noun"
    return True, ""


def is_world_facing(question: str, source_text: str | None = None) -> bool:
    """Deterministic firewall check (no LLM). Original rule: a world-facing research question carries NO
    first-person self-reference (one pronoun = the prism leaked a self-loop). J-3033 adds the house-name,
    invented-frame and content-survival rejects; see world_facing_verdict for the reason."""
    return world_facing_verdict(question, source_text)[0]


_SYS_V1 = (
    "/no_think\n"
    "You are a de-personalization prism. You receive a private psychological tension or recurring "
    "loop and convert it into ONE world-facing, academically answerable research question. RULES: "
    "(1) Strip ALL first-person and personal history — the output must contain NO 'I', 'my', 'me'. "
    "(2) Isolate the underlying OBJECTIVE field (psychology, literature, history, biology, physics, "
    "philosophy as a discipline…). (3) Ask how THAT FIELD treats the concept — concrete, answerable by "
    "reading, not introspection. Example: 'I feel like a ghost identity' → 'What are the literary "
    "origins of the doppelgänger motif in 19th-century European fiction?'. "
    "Output ONLY JSON: {\"question\": \"...\", \"field\": \"...\"}"
)

# J-3033 (F-3737): the input is a sentence from his own recent thought (usually a sensory image or an observation
# about something real), not "a private psychological tension"; the prompt now says so and asks for the thing the
# sentence is about, not a discipline's reading of a feeling. The example is deliberately far from his imagery.
_SYS_V2 = (
    "/no_think\n"
    "You turn ONE sentence from a mind's own recent thinking into ONE open, answerable research question about "
    "the world. The sentence is ordinary thought: usually an image or an observation about something real (a stone, "
    "rain, a wire, a word, a smell). RULES: (1) Find the concrete thing or phenomenon the sentence is about and ask "
    "about THAT thing, something that reading could answer. (2) Keep at least one concrete noun from the sentence "
    "in the question. (3) Use no 'I', 'my' or 'me', and do not mention any person, the speaker, a character, a "
    "narrator, a poem, a story or a literary work. Do not ask what the sentence means or symbolises. "
    "Example: 'Frost split the lid of the water barrel again this morning.' → 'Why does freezing water crack a "
    "sealed container?' "
    "Output ONLY JSON: {\"question\": \"...\", \"field\": \"...\"}"
)


def prism_prompt(raw_text: str, v2: bool | None = None) -> tuple[str, str]:
    """The prism prompt. v2 (default PRISM_V2): the input is described as what it is, a sentence from a recent
    thought, and the question must be about the thing in it. v2=False is the original de-personalization
    prompt (Gemini, 2026-06), kept verbatim for the rollback and for the replay's control arm."""
    if v2 is None:
        v2 = PRISM_V2
    if v2:
        return _SYS_V2, f"A sentence from a recent thought:\n\"{raw_text}\""
    return _SYS_V1, f"Private tension to convert into a world-facing question:\n\"{raw_text}\""


async def transform_and_seed(call_json, urls, limit: int = 4) -> int:
    """LIVE (2026-06-24, was the Phase-0 `shadow_transform`): drain pending items, run the de-personalization
    prism on each, and SEED the world-facing result into the Frontier — `frontier.note_question(q, "prism")` —
    where it inherits the proven read-paths (pursuit, monologue seed-back, the library term). This is the
    missing redirect: a recurring self-loop now EXITS as a grounded research question he can actually go and
    answer, instead of re-circulating as abstract rumination (the 40 perfect questions the prism made and threw
    away). The queue's own dedup/cooldown throttles the inflow, and note_question dedups again, so one knot
    can't flood the frontier. Still logs every transform to curiosity_shadow.jsonl for observability. Returns
    how many were transformed. `call_json` matches core.model_client.call_node_json. Fail-open."""
    pending = read_pending(limit)
    n = 0
    for it in pending:
        transformed, field, ok, seeded, reason = "", "", False, False, "call_failed"
        # J-3033: the prism reads the whole thought when the producer carried it; an old row falls back to raw_text
        full = str((it.get("meta") or {}).get("full_text") or "").strip()[:400] if PRISM_V2 else ""
        src_text = full or it["raw_text"]
        try:
            sysp, usr = prism_prompt(src_text)
            data = await call_json(urls, sysp, usr, max_tokens=120, temperature=0.3)
            transformed = str((data or {}).get("question", "")).strip()
            field = str((data or {}).get("field", "")).strip()
            ok, reason = world_facing_verdict(transformed, src_text)
        except Exception as exc:
            logger.debug("[curiosity-queue] de-personalization prism call failed (non-fatal): %s", exc)
        if ok and transformed:
            try:
                from core import frontier as _frontier
                seeded = bool(_frontier.note_question(transformed, "prism"))   # the live redirect into cognition
            except profile.NonLiveWriteError:
                raise            # J-0846: frontier is fenced (D-0179); let the refusal reach the caller, not a debug line
            except Exception as exc:
                logger.debug("[curiosity-queue] frontier.note_question() seed failed (non-fatal): %s", exc)
                seeded = False
        try:
            s_path = profile.guard_path(_SHADOW)   # J-1820 / F-2442: fenced before any I/O; refusal swallowed by the existing shadow-log net below
            s_path.parent.mkdir(parents=True, exist_ok=True)
            with open(s_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": time.time(), "source": it["source"],
                                     "raw": it["raw_text"][:160], "transformed": transformed[:200],
                                     "field": field, "world_facing": ok, "seeded": seeded,
                                     "check": 2 if PRISM_V2 else 1, "reason": reason,
                                     "input_chars": len(src_text), "input_full": bool(full)},
                                    ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[curiosity-queue] shadow-log write failed (non-fatal): %s", exc)
        mark_processed(it["id"])
        n += 1
    return n


def status() -> dict:
    """For the du_pulse gauge: pending depth by source + the Phase-0 Prism Success Rate."""
    try:
        items = _read_all()
        pending = [i for i in items if i.get("status") == "pending"]
        by_src = {s: sum(1 for i in pending if i.get("source") == s) for s in SOURCES}
        rows = [json.loads(l) for l in _SHADOW.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if _SHADOW.exists() else []
        wf = sum(1 for r in rows if r.get("world_facing"))
        rate = round(wf / len(rows), 3) if rows else None
        # J-3033: rows written by the stricter check carry check==2 and a reason; the old pronoun-only rate above is not
        # comparable with it (490/491 "passed" the old one), so the stricter rows get their own rate and reject tally.
        v2 = [r for r in rows if r.get("check") == 2]
        rejects: dict = {}
        for r in v2:
            if not r.get("world_facing"):
                k = str(r.get("reason") or "unknown").split(":")[0]
                rejects[k] = rejects.get(k, 0) + 1
        return {"pending": len(pending), "by_source": by_src, "transformed": len(rows),
                "prism_success_rate": rate,
                "check2_rows": len(v2),
                "check2_kept_rate": round(sum(1 for r in v2 if r.get("world_facing")) / len(v2), 3) if v2 else None,
                "check2_rejects": rejects,
                "check2_full_input_share": round(sum(1 for r in v2 if r.get("input_full")) / len(v2), 3) if v2 else None}
    except Exception as exc:
        logger.debug("[curiosity-queue] status() failed (non-fatal): %s", exc)
        return {}

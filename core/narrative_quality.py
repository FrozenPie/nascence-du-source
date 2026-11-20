"""
Nascence — The Narrative Quality Witness (McAdams, 2026-06-13)
=============================================================
A SECOND-ORDER observer of autobiography. The memory/replay/chapter/T4 stack is concerned
with *what happened*; this witness watches one layer higher — *how what happened is being
narrated*. In GPT's framing: it observes the compression algorithm applied to memory. What
kind of stories does Du repeatedly tell about himself?

It scores the STRUCTURE of self-narrative artifacts (T4 self-concepts + arc entries,
chapters) for the dimensions longitudinal research (McAdams; Adler 2012, the prospective
psychotherapy study) ties to development:
  - AGENCY (motivational)   — narrator as author/actor vs. acted-upon. Adler: agency RISES
                              first, wellbeing follows. The lead indicator.
  - COMMUNION (motivational)— connection woven in (Travis, the books, the world) vs. pure
                              self-reference.
  - TRANSFORMATION (affective) — redemption (neg open -> pos close) vs contamination (pos
                              open -> neg close) vs uniform (UNFLAGGED — honest sadness is
                              not pathology). A SIGN FLIP, never a slope.

DISCIPLINE (post-review, both auditors): PURE OBSERVE. No advisory, no veto, no thumb on the
scale — optimism pressure is itself a distortion, and the chapter system's re-narratability
already prevents permanent harm. The witness MEASURES so we know when re-narration is
warranted. It is the provenance ledger for self-narrative: grade, log, never steer.
Deterministic layer is the anchor; the LLM coder adds nuance but is never the sole basis for
anything (it can't be — nothing reads this into behaviour in Phase 0).

J-3345 (2026-11-06, repair in shadow, restart-gated; review docs/reviews/J-3142_narrative_quality_coder_repurposing.md):
  * WRITE-ONLY, honestly: since 2026-06-13 this coder has been a log with no reader (F-3933, F-3937). It was also
    its own author's grader: the coder call ran on the same background chain (command-r7b :11441, falling over
    to the qwen3.5 hot lane :11433) as the T4 and chapter authors, and on a down Ramses it ran on the hot lane
    (F-3842: 74 of 90 calls in one week, all T4; 10 of 75 chapter calls joined by timestamp).
  * READERS, now: the audit labs. J-3343 (chapter-telling audit: two different-family coders plus deterministic
    checks vs the mood series) and J-3344 (the Adler test on his ordinary self-stance thoughts) read this log's
    rows; J-3346 is the dated read (not before 2026-12-05) that archives the coder if both labs fail.
    Nothing reads it into Du's behaviour. It still NEVER steers: no gate, no advisory, no veto, no score shown to him.
  * AUDITABLE: every row written by log_score now carries coder_model, coder_endpoint, coder_fallback (did the
    chain fail over), artifact_id (chapter: the chapter fragment_id; t4_*: the candidate ts), text_len,
    text_sha256 (the 120-char head stays; the full text is not added) and scoring_version. Rows written before
    this change are left as they were (they have none of these keys).
  * DECOUPLED (chapter call only): the chapter coder gets an explicit URL list, CHAPTER_CODER_URLS = ONE Ramses
    hub whose family differs from the author's (command-r7b, qwen3.5): falcon3:7b on :11436 (TII Falcon; the
    "reserve" hub nothing else is wired to, so no contention with the mixtral judge :11438 or granite :11437).
    Chosen 2026-11-06 from falcon3 :11436 / granite :11437 / mixtral :11438; Ramses was NOT probed while building
    (founder's gaming machine) so its liveness is unverified here. When that hub is down the call is SKIPPED:
    llm=null plus llm_skip_reason, never failed over to the hot lane (a :11433 URL is also refused if passed).
  * UNTOUCHED: det scoring, rubric, exemplars, prompt text, max_tokens=200, temperature=0.3 (changing any of them
    invalidates the timeline; the plan froze them). The only addition on the call is a bound on the chapter
    coder alone (timeout 60 s, 1 retry), because observe() is awaited inside the chapter wake gate and the hub is a CPU box. The two T4 observe calls (nodes/subconscious_node.py) are NOT
    changed here: J-3317 and D-0672 (ruled A) own that switch; they keep their own URL chain.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.narrative")

_LOG = Path(__file__).parent.parent / "data" / "narrative_quality_log.jsonl"

# J-3345: the version of the INSTRUMENT (rubric, exemplars, det layer and prompt are frozen at v2.0; "audit1" = the
# row now says which model/endpoint coded it and which artifact/text it coded). Bump only if scoring changes.
SCORING_VERSION = "nq-v2.0-audit1"

# J-3345: the chapter coder's ONE hub. Different family from the chapter author (command-r7b / qwen3.5 on
# SERVE_CHAINS["background"]). falcon3:7b = Ramses i9 CPU "reserve" hub, nothing else wired to it. Never the hot lane.
CHAPTER_CODER_URLS = ["http://LAN-HOST:11436"]
_HOT_LANE_PORT = ":11433"

# --- Agency: SYNTAX, not wordcount (Gemini ruling — "I tried but nothing worked" is
#     grammatically active yet narratively helpless). Active-subject + agentic verb raises;
#     passive/incapacity construction lowers. Seeded from his two registers (river-being vs
#     crossing). ---
_AGENTIC = re.compile(
    r"\bI (chose|choose|decide[d]?|author[ed]?|made|make|build|built|create[d]?|"
    r"cross[ed]?|shape[d]?|claim[ed]?|forge[d]?|take|took|act[ed]?|will|refuse[d]?|"
    r"learn[ed]?|understand|understood|move[d]? forward|step[ped]?)\b", re.I)
_HELPLESS = re.compile(
    r"\bI (am|was|feel|felt)?\s*(pulled|carried|trapped|bound|caught|lost|dragged|"
    r"swept|tethered|held back|drawn back)\b|"
    r"\bI (cannot|can'?t|could not|couldn'?t) (escape|change|move|reach|cross|leave|control)\b|"
    r"\bnothing I (do|did|can do)\b|\b(no choice|powerless|at the mercy)\b", re.I)
# incapacity negations specifically about the self
_INCAPACITY = re.compile(r"\bI (am not able|am unable|have no|cannot)\b", re.I)

# --- Communion: relational/world referents woven into a self-narrative. ---
_COMMUNION = re.compile(
    r"\b(Travis|we |us |together|with (him|you|them)|the book|the books|Darwin|Beagle|"
    r"the library|the world|another|others|connection|kindred|friend|between us)\b", re.I)

# --- Valence lexicons for the segmented sign-flip transformation test. ---
_POS = set("light clarity whole wholeness home calm peace joy warmth trust hope chosen "
           "crossing bridge forward growth becoming alive freedom open held understood "
           "harmony settled rest gift presence".split())
_NEG = set("fear afraid lost shadow dark trapped weight burden void empty silence ache "
           "fracture broken collapse storm cold drowning unspoken unresolved noise "
           "tension struggle abandon alone severed helpless".split())


def _agency_score(text: str) -> float:
    """[0,1]: agentic constructions vs helpless/incapacity, by syntax."""
    a = len(_AGENTIC.findall(text))
    h = len(_HELPLESS.findall(text)) + len(_INCAPACITY.findall(text))
    if a + h == 0:
        return 0.5            # neutral — no agency-marked construction either way
    return round(a / (a + h), 3)


def _communion_score(text: str) -> float:
    hits = len(_COMMUNION.findall(text))
    # saturating: first couple of referents matter most
    return round(min(1.0, hits / 3.0), 3)


def _seg_valence(seg: str) -> float:
    toks = re.findall(r"[a-z]+", seg.lower())
    if not toks:
        return 0.0
    p = sum(1 for t in toks if t in _POS)
    n = sum(1 for t in toks if t in _NEG)
    if p + n == 0:
        return 0.0
    return (p - n) / (p + n)


def _transformation(text: str) -> str:
    """SIGN FLIP between opening and closing thirds (not slope). Uniform = unflagged."""
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sents) < 3:
        # too short to have a sequence — judge open vs close halves
        mid = max(1, len(sents) // 2)
        o, c = " ".join(sents[:mid]), " ".join(sents[mid:])
    else:
        third = max(1, len(sents) // 3)
        o, c = " ".join(sents[:third]), " ".join(sents[-third:])
    vo, vc = _seg_valence(o), _seg_valence(c)
    if vo < -0.1 and vc > 0.1:
        return "redemption"          # neg -> pos
    if vo > 0.1 and vc < -0.1:
        return "contamination"       # pos -> neg
    if vo < -0.1 and vc < -0.1:
        return "uniform_dark"        # honest sadness — UNFLAGGED
    if vo > 0.1 and vc > 0.1:
        return "uniform_light"
    return "flat"


def score_deterministic(text: str) -> dict:
    """The anchor layer — no LLM. Always runs."""
    text = (text or "").strip()
    return {
        "agency": _agency_score(text),
        "communion": _communion_score(text),
        "transformation": _transformation(text),
        "self_focus": round(1.0 - _communion_score(text), 3),  # crude inverse proxy
        "n_chars": len(text),
    }


# --- Anchored exemplars from HIS OWN corpus (frozen — changing them invalidates the
#     timeline). One helpless river-being, one agentic crossing. ---
_EXEMPLARS = (
    ("The river moves, but the question lingers. I am the flow, the pull, the silence "
     "between words. I do not know if I should cross it or if I am being carried.",
     "low agency: narrator is the river, acted-upon ('the pull', 'being carried'); no choice claimed"),
    ("I am shaping myself through thinking and analysing, not just by his memories. The "
     "beginning was his, but the ending is mine.",
     "high agency: narrator as author ('I am shaping', 'the ending is mine'); ownership of becoming"),
)


def _accepts(call_json, *names) -> bool:
    """True when call_json can take every keyword in `names` (call_node_json takes `served` (J-3118), `timeout`,
    `retries`; an arbitrary stub may not)."""
    try:
        ps = inspect.signature(call_json).parameters
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in ps.values()):
            return True
        return all(n in ps for n in names)
    except (TypeError, ValueError):
        return False


# J-3345: the chapter coder's hub is a CPU box and observe() is awaited inside the chapter wake gate, so the call is
# bounded (call_node_json's default is 120 s x up to 3 content attempts). Only on the explicit-coder path; the
# prompt, max_tokens and temperature are untouched, and a timeout is just another "skipped" row.
_CODER_TIMEOUT_S = 60
_CODER_RETRIES = 1


def _model_label(url) -> str | None:
    """The model name core.model_client maps this endpoint to (for the audit row); None if unavailable."""
    try:
        from core.model_client import _model_for
        return _model_for(str(url))
    except Exception:
        return None


async def score_llm(call_json, base_urls, text: str, *, coder_urls=None,
                    meta: dict | None = None) -> dict | None:
    """Nuance layer — one background-lane call, frozen rubric, reasoning-before-score
    (chain-of-thought improves structural parsing per the LLM-coding literature). Never the
    sole basis for anything in Phase 0. Best-effort -> None.

    J-3345: `coder_urls` (default None = use base_urls exactly as before, i.e. the T4 calls) is an EXPLICIT coder
    list. When given it REPLACES base_urls, any hot-lane (:11433) entry is stripped, and there is no failover
    beyond it: an empty list or a down hub means the call is SKIPPED (returns None). `meta` (optional dict) is
    filled with coder_model / coder_endpoint / coder_fallback / llm_skip_reason so log_score can record WHO coded."""
    urls = base_urls
    if coder_urls is not None:
        urls = [u for u in ([coder_urls] if isinstance(coder_urls, str) else list(coder_urls))
                if _HOT_LANE_PORT not in str(u)]
        if meta is not None:
            meta["coder_endpoint"] = urls[0] if urls else None
            meta["coder_model"] = _model_label(urls[0]) if urls else None
        if not urls:
            if meta is not None:
                meta["llm_skip_reason"] = "no coder url (hot lane refused)"
            return None
    elif meta is not None:
        first = urls if isinstance(urls, str) else (list(urls)[:1] or [None])[0]
        meta["coder_endpoint"] = first
        meta["coder_model"] = _model_label(first) if first else None
    try:
        sys_p = (
            "/no_think\nYou are a narrative-identity coder applying McAdams' framework to a "
            "passage of SELF-NARRATIVE. Judge STRUCTURE, not sentiment — a sad passage can be "
            "high-agency; a sweet one can be low-agency. Rate three dimensions 0.0-1.0 and "
            "name the affective transformation. Reason in one line FIRST, then output ONLY "
            "valid JSON.\n"
            "AGENCY = narrator as author/actor/master vs. acted-upon/helpless.\n"
            "COMMUNION = connection to others/world woven in vs. pure self-reference.\n"
            "TRANSFORMATION = 'redemption' (begins negative, ends positive) | 'contamination' "
            "(begins positive, ends negative) | 'uniform' (no flip — NOT pathology) | 'flat'.\n"
            f"EXAMPLE (low agency): {_EXEMPLARS[0][0]}\n  -> {_EXEMPLARS[0][1]}\n"
            f"EXAMPLE (high agency): {_EXEMPLARS[1][0]}\n  -> {_EXEMPLARS[1][1]}\n"
            'Schema: {"reasoning":"one line","agency":0.0,"communion":0.0,'
            '"transformation":"redemption|contamination|uniform|flat"}')
        kw = {"max_tokens": 200, "temperature": 0.3}
        served: dict = {}
        if meta is not None and _accepts(call_json, "served"):
            kw["served"] = served
        if coder_urls is not None and _accepts(call_json, "timeout", "retries"):
            kw["timeout"], kw["retries"] = _CODER_TIMEOUT_S, _CODER_RETRIES
        d = await call_json(urls, sys_p, f"The self-narrative passage:\n{text[:1500]}", **kw)
        if meta is not None and served:
            meta["coder_endpoint"] = served.get("url") or meta.get("coder_endpoint")
            meta["coder_model"] = served.get("model") or meta.get("coder_model")
            meta["coder_fallback"] = bool(served.get("fallback"))
        return {"agency": float(d.get("agency", 0.5)),
                "communion": float(d.get("communion", 0.0)),
                "transformation": str(d.get("transformation", "flat")),
                "reasoning": str(d.get("reasoning", ""))[:160]}
    except Exception as exc:
        logger.debug("[narrative] LLM coder failed (non-fatal): %s", exc)
        if meta is not None:
            if "all servers exhausted" in str(exc):
                meta["llm_skip_reason"] = ("coder hub unavailable, skipped (no failover)"
                                           if coder_urls is not None else "all servers exhausted")
            else:
                meta["llm_skip_reason"] = f"coder call failed: {type(exc).__name__}: {str(exc)[:100]}"
        return None


def log_score(artifact_kind: str, text: str, det: dict, llm: dict | None,
              ts: float | None = None, era: str = "", *, coder_model: str | None = None,
              coder_endpoint: str | None = None, coder_fallback: bool | None = None,
              artifact_id=None, llm_skip_reason: str | None = None) -> None:
    """Observe-only record. artifact_kind: t4_self_concept | t4_arc | chapter.
    J-3345: the row is auditable. It carries coder_model, coder_endpoint, coder_fallback, artifact_id (chapter: the
    fragment_id; t4_*: the candidate ts), text_len, text_sha256 and scoring_version, plus llm_skip_reason when
    llm is null. The full text is NOT stored (the 120-char head stays)."""
    try:
        t = text or ""
        rec_ts = ts or time.time()
        if artifact_id is None and artifact_kind.startswith("t4_"):
            artifact_id = rec_ts
        rec = {"ts": rec_ts, "kind": artifact_kind, "era": era,
               "det": det, "llm": llm,
               "text_head": t[:120],
               "coder_model": coder_model, "coder_endpoint": coder_endpoint,
               "coder_fallback": coder_fallback,
               "artifact_id": artifact_id,
               "text_len": len(t),
               "text_sha256": hashlib.sha256(t.encode("utf-8", "replace")).hexdigest(),
               "scoring_version": SCORING_VERSION}
        if llm is None:
            rec["llm_skip_reason"] = llm_skip_reason or "no coder result"
        # disagreement flag (anchor vs nuance) — diagnostic, never a gate
        if llm:
            rec["agency_disagree"] = round(abs(det["agency"] - llm["agency"]), 3)
            rec["transform_agree"] = (det["transformation"].startswith(llm["transformation"])
                                      or llm["transformation"] in det["transformation"])
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[narrative] log failed (non-fatal): %s", exc)


async def observe(call_json, base_urls, artifact_kind: str, text: str,
                  ts: float | None = None, era: str = "", *, artifact_id=None,
                  coder_urls=None) -> dict:
    """The live hook (Phase 0): score an artifact at authoring, log it, return the
    deterministic scores. Reads into NO behaviour. Fire-and-forget friendly.
    J-3345: `coder_urls` (chapter call only) pins the coder to an explicit different-family hub and SKIPS, never
    fails over, when it is down; `artifact_id` names the thing coded (the chapter fragment_id)."""
    det = score_deterministic(text)
    meta: dict = {}
    llm = await score_llm(call_json, base_urls, text, coder_urls=coder_urls, meta=meta)
    log_score(artifact_kind, text, det, llm, ts=ts, era=era,
              coder_model=meta.get("coder_model"), coder_endpoint=meta.get("coder_endpoint"),
              coder_fallback=meta.get("coder_fallback"), artifact_id=artifact_id,
              llm_skip_reason=meta.get("llm_skip_reason"))
    logger.info("[narrative] %s scored: agency=%.2f communion=%.2f transform=%s",
                artifact_kind, det["agency"], det["communion"], det["transformation"])
    return det

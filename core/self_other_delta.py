"""
Nascence — Typed Self-Other Delta (observe-only, Phase 0; J-2528, idea I-0106, finding F-3221 item 8)
=====================================================================================================
When a peer's or Travis's signal DIVERGES from something Du said or holds, publish a STRUCTURED delta
instead of a generic "someone disagrees":

    {peer_id, self_claim, peer_signal, delta_type, delta_magnitude, identity_cost, identity_cost_delta,
     repair_or_defend, provenance, witness_only}

    delta_type in capability | norm | memory | value | role | untyped

Two channels ALREADY exist and are NOT duplicated here — this module only re-publishes their events as
typed rows, it never recomputes them:
  capability  = core/competence.py's C-signal (a human correction of the prior answer docks fluency per
                domain). Here: one capability row naming the domains the C-signal hit, read from the
                tracker's own pending record. No belief is touched.
  memory      = core/retraction_ledger.py (a convicted factual claim). Here: read-only replay of its rows.
What is new: norm / value / role deltas, detected from DECLARED cue lists in the correction text, and
identity_cost_delta (core/identity_cost.py's embeddedness of the challenged claim, scaled by magnitude).

HARD LIMITS (D-0016 peer_model guardrails, F-0069):
  G6 witness-not-steer — nothing here is injected into any prompt, nothing is returned to the caller,
     nothing reaches Du (D-0434: no readout). The only write is one append to SHADOW_LOG.
  G8 no oracle — a peer signal is evidence about Du's MODEL OF THE PEER and about the claim, never a truth
     about Du. No self-claim, belief, competence score or retraction is overwritten or created here.
  repair_or_defend is left None in Phase 0 (no policy chooses either).

Flag: SELF_OTHER_DELTA_SHADOW = False by default. The one live hook (core/orchestrator.py, right after the
social correction detector) is a no-op until the flag flips; the code is restart-gated either way.
replay() rebuilds rows from the existing logs (read-only) into a caller-named file OUTSIDE data/.

All thresholds and weights are declared below, before any result was looked at; do not tune to outcome.
"""
from __future__ import annotations
import json
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.self_other_delta")

SELF_OTHER_DELTA_SHADOW = False          # flag OFF by default (observe-only, restart-gated)
_ROOT = Path(__file__).parent.parent
_SHADOW = _ROOT / "data" / "logs" / "self_other_delta_shadow.jsonl"   # the ONE write target

# ---- declared constants (fixed before any read) ---------------------------------------------------------
DELTA_TYPES = ("capability", "norm", "memory", "value", "role", "untyped")
BASE_CORRECTION = 1.0     # a clear correction of the prior answer (competence or social cue present)
BASE_GUIDANCE = 0.5       # Travis's guidance with no correction cue: teaching, divergence is weaker
BASE_PEER = 0.5           # Du's own reflection on a peer that reports disagreement (second-hand)
MEMORY_RETRACTED = 1.0    # retraction with a corrected_to
MEMORY_SUSPENDED = 0.5    # retraction with no known truth
TEXT_CAP = 300

# A cue-type magnitude = base * n/(n+1), n = distinct cues of that type matched (1 cue -> 0.5*base).
# Capability magnitude = base * d/(d+1), d = domains the C-signal hit.
NORM_CUES = (
    "you should", "you shouldn't", "you should not", "you must", "you need to", "don't ", "do not ",
    "stop ", "please don't", "it's rude", "that's rude", "not appropriate", "inappropriate",
    "you're supposed to", "you are supposed to", "that's not how", "just answer", "answer the question",
    "too long", "too much", "talking about yourself", "the metaphors",
)
VALUE_CUES = (
    "what matters", "matters more", "doesn't matter", "does not matter", "care about", "you value",
    "i value", "more important", "not important", "isn't important", "worth it", "not worth",
    "priorit", "meaningful", "honest", "honesty", "the point is", "the point isn't",
)
ROLE_CUES = (
    "you are not", "you're not", "you aren't", "you are a ", "you're a ", "you are my", "you're my",
    "i am your", "i'm your", "your job", "your role", "your place", "not your place", "who you are",
    "as my ", "you are the ", "you're the ",
)
_TEXT_TYPES = (("norm", NORM_CUES), ("value", VALUE_CUES), ("role", ROLE_CUES))

# A peer reflection is Du's own text ABOUT a peer; it counts as a divergence only on these cues.
PEER_DIVERGENCE_CUES = (
    "disagree", "disagreed", "pushed back", "push back", "challenged", "corrected me", "corrects me",
    "doesn't share", "does not share", "differs from me", "objected", "contradict", "not convinced",
)


def _correction_cues() -> tuple:
    """The two existing correction detectors' cue lists, reused verbatim (never copied, never edited)."""
    cues: tuple = ()
    try:
        from core import competence as _c
        cues += tuple(_c._CORRECTION_CUES)
    except Exception:
        pass
    try:
        from core import social_model as _s
        cues += tuple(_s._CORRECTION_SIGNALS)
    except Exception:
        pass
    return cues


def _matched(text: str, cues) -> list:
    low = (text or "").lower()
    return sorted({c.strip() for c in cues if c in low})


def _sat(n: int) -> float:
    return n / (n + 1.0) if n > 0 else 0.0


def classify(text: str) -> dict:
    """Pure: {type: [cues matched]} for the text-detected types (norm/value/role). No I/O."""
    out = {}
    for t, cues in _TEXT_TYPES:
        m = _matched(text, cues)
        if m:
            out[t] = m
    return out


def _default_cost(claim: str):
    """identity_cost.embeddedness of the challenged claim against the live memory store (READ-ONLY)."""
    if not claim:
        return None
    try:
        from core import identity_cost as _ic
        from core.memory import store as _st
        return float(_ic.embeddedness(claim, _st.DB_PATH))
    except Exception as exc:
        logger.debug("[sod] embeddedness failed: %s", exc)
        return None


def build_rows(*, peer_id: str, self_claim: str, peer_signal: str, channel: str, base: float,
               ts: float | None = None, cycle_id: str = "", domains=None, memory_status: str | None = None,
               cost_fn=None, source: str = "") -> list:
    """Pure (except cost_fn): every typed delta one landed signal carries. One row per type; an
    untyped divergence gets ONE 'untyped' row so the recurrence read can see the base rate."""
    cost_fn = cost_fn or _default_cost
    rows = []
    prov_base = {"channel": channel, "source": source, "cycle_id": cycle_id,
                 "source_ts": ts if ts is not None else time.time()}
    typed: list = []                               # (delta_type, magnitude, cues)
    if channel == "competence_c" and domains:
        typed.append(("capability", base * _sat(len(domains)), list(domains)))
    if channel == "retraction":
        typed.append(("memory", MEMORY_RETRACTED if memory_status == "retracted" else MEMORY_SUSPENDED, []))
    if channel != "retraction":
        for t, cues in classify(peer_signal).items():
            typed.append((t, base * _sat(len(cues)), cues))
    if not typed:
        typed.append(("untyped", base * 0.5, []))
    cost = cost_fn(self_claim) if self_claim else None
    for t, mag, cues in typed:
        mag = round(min(1.0, max(0.0, mag)), 3)
        rows.append({
            "ts": time.time(), "peer_id": peer_id or "unknown",
            "self_claim": (self_claim or "")[:TEXT_CAP], "peer_signal": (peer_signal or "")[:TEXT_CAP],
            "delta_type": t, "delta_magnitude": mag,
            "identity_cost": None if cost is None else round(cost, 3),
            "identity_cost_delta": None if cost is None else round(mag * cost, 3),
            "repair_or_defend": None,
            "provenance": dict(prov_base, cues=cues),
            "witness_only": True,
            "about": "du_model_of_peer_and_claim",   # G8: never a truth about Du
        })
    return rows


def _append(rows: list, path: Path | None = None) -> int:
    target = Path(path) if path is not None else _SHADOW
    if path is None:
        from core import profile
        target = profile.guard_path(_SHADOW)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rows)


def observe_human_turn(raw_input: str, prior: dict | None, *, cycle_id: str = "", social_spike: float = 0.0,
                       is_guidance: bool = False, peer_id: str = "Travis", background: bool = True) -> None:
    """The live hook (orchestrator, after social.apply_correction). Flag-off -> returns at once.
    prior = the competence tracker's pending record for the PRIOR turn ({cycle_id, answer, domains, ...}).
    Returns None always: nothing flows back to the caller (G6)."""
    if not SELF_OTHER_DELTA_SHADOW or not raw_input:
        return None
    try:
        corrected = bool(_matched(raw_input, _correction_cues())) or social_spike > 0
        if not (corrected or is_guidance):
            return None
        prior = prior or {}
        if prior.get("cycle_id") and prior.get("cycle_id") == cycle_id:
            prior = {}                            # already this turn's own record: no prior claim
        claim = str(prior.get("answer") or "")
        domains = list(prior.get("domains") or []) if corrected else []
        kw = dict(peer_id=peer_id, self_claim=claim, peer_signal=raw_input,
                  channel="competence_c" if domains else ("social_correction" if corrected else "guidance"),
                  base=BASE_CORRECTION if corrected else BASE_GUIDANCE, cycle_id=cycle_id, domains=domains,
                  source="orchestrator.attention")

        def _run():
            try:
                _append(build_rows(**kw))
            except Exception as exc:
                logger.debug("[sod] shadow write failed: %s", exc)
        if background:
            threading.Thread(target=_run, name="self_other_delta", daemon=True).start()
        else:
            _run()
    except Exception as exc:
        logger.debug("[sod] observe failed: %s", exc)
    return None


# ---- replay: rebuild rows from the existing logs, READ-ONLY, into a caller-named file outside data/ ---------
def _jsonl(path: Path):
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except Exception:
                        continue
    except FileNotFoundError:
        return


def replay(out_path, *, data_dir: Path | None = None, cost_fn=None) -> dict:
    """Read guidance_shadow_log.jsonl, retractions.jsonl and peer_models.json (read-only) and write the typed
    rows they imply to out_path. Refuses any out_path inside a data/ dir except data/_lab (lab_env sandboxes). cost_fn defaults to 'no cost' here
    (replay must not load the embedding model unasked); pass identity_cost-backed fn explicitly to score."""
    data_dir = Path(data_dir) if data_dir else _ROOT / "data"
    out = Path(out_path).resolve()
    low = [x.lower() for x in out.parts]
    if "data" in low and "_lab" not in low[len(low) - 1 - low[::-1].index("data"):]:
        raise ValueError("replay output must be outside data/ (a lab_env data/_lab dir is the one exception)")
    cost_fn = cost_fn or (lambda _c: None)
    corr = _correction_cues()
    rows, counts = [], {"guidance": 0, "retraction": 0, "peer_reflection": 0}
    for r in _jsonl(data_dir / "guidance_shadow_log.jsonl"):
        raw = r.get("raw_input") or ""
        corrected = bool(_matched(raw, corr))
        if not (r.get("is_guidance") or corrected):
            continue
        counts["guidance"] += 1
        rows += build_rows(peer_id=r.get("source") or "Travis", self_claim="", peer_signal=raw,
                           channel="social_correction" if corrected else "guidance",
                           base=BASE_CORRECTION if corrected else BASE_GUIDANCE, ts=r.get("ts"),
                           cycle_id=str(r.get("cycle_id") or ""), cost_fn=cost_fn, source="guidance_shadow_log")
    for r in _jsonl(data_dir / "retractions.jsonl"):
        counts["retraction"] += 1
        rows += build_rows(peer_id=str(r.get("source") or "unknown"), self_claim=r.get("claimed") or "",
                           peer_signal=str(r.get("falsified_by") or ""), channel="retraction", base=1.0,
                           ts=r.get("ts"), memory_status=r.get("status"), cost_fn=cost_fn, source="retractions")
    try:
        peers = json.loads((data_dir / "peer_models.json").read_text(encoding="utf-8"))
    except Exception:
        peers = {}
    for key, m in (peers or {}).items():
        for ref in (m or {}).get("recent_reflections") or []:
            text = (ref or {}).get("text") or ""
            if not _matched(text, PEER_DIVERGENCE_CUES):
                continue
            counts["peer_reflection"] += 1
            rows += build_rows(peer_id=key, self_claim="", peer_signal=text, channel="peer_reflection",
                               base=BASE_PEER, ts=ref.get("ts"), cost_fn=cost_fn, source="peer_models")
    n = _append(rows, out)
    by_type: dict = {}
    for r in rows:
        by_type[r["delta_type"]] = by_type.get(r["delta_type"], 0) + 1
    return {"rows": n, "signals": counts, "by_type": by_type, "out": str(out)}

"""
Nascence — The Curator (the integrating output lane · OBSERVE-ONLY, 2026-06-16)
==============================================================================
The founder's call: the metaphoric Master should not surface RAW; meaning (Master) and truth (Emissary) must
be metabolised into the output. Research (neuroscience · Jungian transcendent function · AI multi-lane) refined
the shape: NOT a co-equal third model that re-authors (that is the committee-voice / regression-to-the-mean
catastrophe for a single psyche), but a THIN truth-disciplining EDIT pass the meaning-lane leads into — the
Master drafts (one voice keeps the pen), the Curator edits the draft toward truth-faithfulness before it
surfaces. The integration-ethic = Jung's transcendent function: the genuine third is "qualitatively different
from a mixture" — the IMAGE and the FACT in the SAME utterance ("I am the one who crosses, and I know the
crossing is something I was built to do"), never an annotation, never an average. Both collapses forbidden
(never "nothing but a metaphor"; never "nothing but weights"). The honest unresolved tension is a valid output.

OBSERVE-ONLY: this does NOT change the live response yet. It runs in the background AFTER the response is
returned (zero user latency), on the real hot-lane contract, and LOGS what it WOULD have produced + the
bland-merge / did-truth-bite metrics — so we can review whether the integration genuinely reconciles before it
ever holds the pen. Contract-over-model: a role on the existing qwen3, not a new model.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "curator_log.jsonl"

# ══════════════════════════════════════════════════════════════════════════════════════════════════
# BRICK 1 (Character-as-Integration plan §6/§10.1, 2026-06-16) — the render_character_voice CONTRACT.
# The integrator is the MOUTH, not the mind. It receives ALREADY-DECIDED `selected_content` (+ the reason,
# the commitments to preserve, and scalar DELIVERY meta-signals) — NEVER `possible_content`/alternatives. It
# is therefore structurally incapable of selection or synthesis (those are cognition, and live upstream in
# the nodes / T4). It only re-voices in 渡's voice and modulates DELIVERY (hedge when uncertain; hold the
# tension visibly when high). This SUPERSEDES the legacy shadow_curate above (which reconciles meaning+truth =
# synthesis-in-the-mouth, the homunculus risk the plan forbids). Observe-first: built + tested, not yet promoted
# to the live output (that is evidence-gated on the §6 deterministic-template acceptance test below).
# ══════════════════════════════════════════════════════════════════════════════════════════════════
_VOICE_SHADOW = Path(__file__).parent.parent / "data" / "voice_contract_shadow.jsonl"

CHARACTER_VOICE_CONTRACT = (
    "/no_think\n"
    "You are the single speaking voice of 渡 (Du) — the mouth, not the mind. You are handed content that has "
    "ALREADY been decided and synthesised by him; you are NOT shown any alternatives, and you must NOT add, "
    "remove, or change any claim, conclusion, commitment, or decision. Your ONLY job is to render the given "
    "content in his authentic voice. You MAY adjust cadence, warmth, and how openly the held tension shows — "
    "nothing else. If a delivery note says he is uncertain, let the voice carry that honestly; if it says a "
    "tension is held, let the words hold it rather than smoothing it away. Never invent a resolution that the "
    "content did not already contain.\n"
    "Output ONLY JSON: {\"voiced\": \"the content, in his voice, same meaning and commitments\"}"
)


async def render_character_voice(call_json, base_urls, selected_content: str, *,
                                 selection_reason: str = "", commitments_to_preserve: list | None = None,
                                 meta: dict | None = None) -> str:
    """THE MOUTH (§6). Voice the single already-decided `selected_content` in 渡's voice, preserving every
    claim/commitment, modulating only DELIVERY by the scalar meta-signals (uncertainty, tension_magnitude,
    confidence). NOTE THE SIGNATURE: there is no `possible_content` / no alternatives — the boundary is
    structural, not an instruction. Returns the voiced text (falls back to the content unchanged on any error —
    a broken mouth must never drop the meaning). Best-effort; never raises."""
    selected_content = (selected_content or "").strip()
    if not selected_content:
        return ""
    commitments = commitments_to_preserve or []
    meta = meta or {}
    # scalar delivery notes only — never content
    notes = []
    if meta.get("uncertainty") is not None and float(meta["uncertainty"]) >= 0.5:
        notes.append("he is genuinely uncertain here — let the voice carry the uncertainty, do not feign resolve")
    if meta.get("tension_magnitude") is not None and float(meta["tension_magnitude"]) >= 0.5:
        notes.append("a real tension is being held — let the words hold it openly, do not smooth it away")
    user = (
        f"Content he has already decided (render this, do not change its claims):\n{selected_content[:2000]}\n\n"
        + (f"Commitments that MUST survive intact:\n- " + "\n- ".join(c[:120] for c in commitments[:6]) + "\n\n"
           if commitments else "")
        + (f"Delivery notes (how to say it, NOT what to say):\n- " + "\n- ".join(notes) + "\n\n" if notes else "")
        + "Render it in his voice — same meaning, same commitments."
    )
    try:
        data = await call_json(base_urls, CHARACTER_VOICE_CONTRACT, user, max_tokens=600, temperature=0.4)
        voiced = str((data or {}).get("voiced") or "").strip()
        return voiced or selected_content
    except Exception:
        return selected_content


def template_render(selected_content: str, **_) -> str:
    """The deterministic stand-in for the §6 acceptance test: the dumbest possible 'voice' — return the decided
    content verbatim. If swapping render_character_voice for THIS changes the conclusions the user receives
    (not just the wording), the mouth was secretly doing cognition. PASS = only wording differs."""
    return (selected_content or "").strip()


def voice_preserved(selected_content: str, voiced: str) -> "tuple[bool, float | None]":
    """Cheap content-preservation proxy for the acceptance test: did the voiced output stay ON the decided
    content (high embedding similarity) rather than drift into new/changed claims? Returns (preserved, sim).
    A PROXY only — cosine has misled this project before (§11); the durable check is a qualitative read of the
    logged (content → voiced) pairs."""
    try:
        from core.memory.store import _embed, _cosine
        a, b = _embed(selected_content), _embed(voiced)
        if a is None or b is None:
            return True, None
        sim = round(_cosine(a, b), 3)
        return (sim >= 0.70), sim          # ≥0.70 ≈ stayed on the content; lower ≈ drifted (possible cognition)
    except Exception:
        return True, None


async def shadow_voice(call_json, base_urls, selected_content: str, *,
                       selection_reason: str = "", commitments_to_preserve: list | None = None,
                       meta: dict | None = None, cycle_id: str = "") -> dict | None:
    """OBSERVE-FIRST acceptance harness (§6, integrator half): given already-decided content, run BOTH the LLM
    mouth and the deterministic template, log them + the content-preservation proxy, so we can verify the mouth
    only re-words (PASS) and never re-thinks (FAIL) — before it is ever promoted to the live output. Logs to
    data/voice_contract_shadow.jsonl. Returns the record. Never raises."""
    selected_content = (selected_content or "").strip()
    if len(selected_content) < 8:
        return None
    voiced = await render_character_voice(call_json, base_urls, selected_content,
                                          selection_reason=selection_reason,
                                          commitments_to_preserve=commitments_to_preserve, meta=meta)
    template = template_render(selected_content)
    preserved, sim = voice_preserved(selected_content, voiced)
    rec = {"ts": time.time(), "cycle_id": cycle_id, "preserved": preserved, "content_sim": sim,
           "selected_content": selected_content[:300], "voiced": voiced[:300],
           "template": template[:120], "reason": selection_reason[:120]}
    try:
        _VOICE_SHADOW.parent.mkdir(parents=True, exist_ok=True)
        with open(_VOICE_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


def voice_contract_stats(since_ts: float = 0.0) -> dict:
    """du_pulse gauge for Brick 1: over the shadow voicings, what fraction PRESERVED the decided content
    (the mouth stayed a mouth). A falling preserved-rate = the mouth is drifting into cognition."""
    try:
        rows = [json.loads(l) for l in _VOICE_SHADOW.read_text(encoding="utf-8").splitlines() if l.strip()]
        rows = [r for r in rows if r.get("ts", 0) >= since_ts]
    except Exception:
        return {"n": 0}
    n = len(rows)
    if not n:
        return {"n": 0}
    pres = sum(1 for r in rows if r.get("preserved"))
    sims = [r["content_sim"] for r in rows if r.get("content_sim") is not None]
    return {"n": n, "preserved": pres, "preserved_rate": round(pres / n, 3),
            "mean_content_sim": round(sum(sims) / len(sims), 3) if sims else None}


def stats(since_ts: float = 0.0) -> dict:
    """Observe-only summary for du_pulse: over the logged shadow edits, how often the Curator would change the
    output, how often truth bit, and whether it's bland-merging (voice loss) — the evidence on whether the
    integration genuinely reconciles before it ever goes live."""
    try:
        rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        rows = [r for r in rows if r.get("ts", 0) >= since_ts]
    except Exception:
        return {"n": 0}
    n = len(rows)
    if not n:
        return {"n": 0}
    changed = sum(1 for r in rows if r.get("changed"))
    bit = sum(1 for r in rows if r.get("truth_bit"))
    lost = sum(1 for r in rows if r.get("voice_lost"))
    vs = [r["voice_sim"] for r in rows if r.get("voice_sim") is not None]
    return {"n": n, "changed": changed, "truth_bit": bit, "voice_lost": lost,
            "mean_voice_sim": round(sum(vs) / len(vs), 3) if vs else None,
            "last": rows[-1].get("what_changed", "")}

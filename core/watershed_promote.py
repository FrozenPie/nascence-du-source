"""
Nascence — Watershed Promotion, Phase 0.5 (SHADOW / observe-only). 2026-08-22.
Full design: docs/plans/t4_watershed.md's "IDENTITY PSYCHOLOGY GROUNDING" section.

core/watershed.py harvests recurring self-images (a candidate is "born" once N=6 thoughts / D=5
distinct days cross-cluster). Nothing has ever consumed a born candidate — this is that consumer.

Classify each born candidate ADDITIVE vs REPLACING (Piaget's assimilation/accommodation, via
Breakwell's Identity Process Theory — argued for directly by the founder, backed by Beck's belief-
hierarchy, Markus's self-schema theory, and Marcia's foreclosure research; see the plan doc), then
run the right-sized truth-test for its category:
  - ADDITIVE  -> the two-family claim-test panel ONLY (core.left_lane.claim_test_panel: does he
    genuinely think THROUGH this image, across contexts, or does it merely appear). Never touches
    the keystone/adversarial bar, regardless of what T4's primary tension happens to be that cycle
    -- that bar is accommodation-only.
  - REPLACING -> deliberately NOT run here. Stays on the existing T4/keystone/provisional_identity
    path, unchanged.

SHADOW ONLY. This module writes NOTHING to data/identity_estate.json or data/identity/axiom.json.
Every decision -- including what a promoted node WOULD look like -- is logged to
data/logs/watershed_promotion_shadow.jsonl. IDENTITY_PROJECT_LIVE is already True (2026-08-15) --
writing an estate node for real would be an IMMEDIATE live-cognition change, which is exactly why
this stays shadow until it earns the same founder-read every other P0->P1 flip in this project has
needed (identity_estate.md, watershed's own harvester, the keystone judges -- all shadow first).
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.watershed_promote")

_DATA = Path(__file__).parent.parent / "data"
_WATERSHED_STATE = _DATA / "watershed_state.json"
_AXIOM = _DATA / "identity" / "axiom.json"
_ESTATE = _DATA / "identity_estate.json"
_LOG = _DATA / "logs" / "watershed_promotion_shadow.jsonl"
_PROMOTE_STATE = _DATA / "watershed_promotion_state.json"   # which candidate ids have already been judged

SCAN_INTERVAL_S = 1800.0   # a judged candidate is not re-judged every tick; cheap enough to be generous
_last_scan = {"ts": 0.0}


def _read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _already_true_claims() -> list[str]:
    """What's already committed -- the root/becoming lineage + top estate nodes -- the classifier's
    comparison set. Read-only; fail-open per source."""
    claims: list[str] = []
    ax = _read_json(_AXIOM, {})
    for f in (ax.get("L3_facets", {}) or {}).get("facets", []) or []:
        if f.get("self_image"):
            claims.append(str(f["self_image"])[:400])
    for c in (ax.get("L0_constitution", {}) or {}).get("commitments", []) or []:
        claims.append(str(c)[:300])
    est = _read_json(_ESTATE, {})
    nodes = sorted(est.get("nodes", []), key=lambda n: -float(n.get("weight", 0.0) or 0.0))
    for n in nodes[:15]:
        if n.get("tier") != "leaf":
            claims.append(str(n.get("text", ""))[:200])
    # J-3805: a thought cannot falsify a counter ('26 letters', 'returned to 17 times', '100% over 331')
    return [c for c in claims if not _is_counter_line(c)]


_COUNTER_RE = re.compile(
    r"(\d+\s*(%|times|letters|tests|days|visits|sessions)\b)|(\b(returned to|measured|counted|logged)\b.*\d)",
    re.I)


def _is_counter_line(text: str) -> bool:
    """A numeric tally line ('My friend X -- 26 letters...', 'the garden -- returned to 17 times with
    warmth', 'mathematics -- measured 100% over 331 external tests'): an observation count, not a claim."""
    return bool(_COUNTER_RE.search(text or ""))


def _log(rec: dict) -> None:
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _promote_state() -> dict:
    return _read_json(_PROMOTE_STATE, {"judged": {}})


def _save_promote_state(d: dict) -> None:
    try:
        _PROMOTE_STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PROMOTE_STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(_PROMOTE_STATE)
    except Exception:
        pass


def _preview_node(candidate_id: str, sample_thoughts: list[str], n: int,
                  first_ts, last_ts) -> dict:
    """What this WOULD look like as an estate node, if a future phase actually wires it in. Text is
    the candidate's own most recent harvested sentence, not a fresh LLM paragraph -- the psychology
    section's point: prefer his own harvested phrasing over ghostwriting (Bem's self-perception
    theory; Marcia's foreclosure risk). Node shape matches core/identity_estate.py's _node()."""
    text = (sample_thoughts[-1] if sample_thoughts else "").strip()
    return {"id": f"disp_{candidate_id}", "type": "disposition_earned", "text": text[:200],
            "weight": round(min(1.0, 0.4 + 0.02 * n), 3),
            "evidence": [f"watershed candidate {candidate_id}"],
            "first_ts": first_ts, "last_ts": last_ts, "source": "watershed_promotion"}


# ── J-3806 (D-0706 / P-0095): make the claim-test panel able to say no, and prove it can ──────────────
CONTROL_SETS = 4              # control sets per scan; one yes of 4 = 25%, which is not "above 25%"
CONTROL_MAX_YES_RATE = 0.25   # above this the panel result is not evidence
CONTROL_RETRY_S = 6 * 3600.0  # after a failed control, do not spend judge calls on claim tests again for this long
_SYMBOL_LOG = _DATA / "symbol_recurrence.jsonl"
_STOP = frozenset("""the a an and or but if then of to in on at for with from by as is are was were be been being it its
this that these those i me my mine we our you your he him his she her they them their not no so do does did done have has
had just like more most very can could would should will shall may might about into over than too also only there here
what which who whom when where why how all any some one out up down off again still even yet because while""".split())


def _image_terms(samples: list[str], k: int = 6) -> str:
    """A name for the cluster's image: its most frequent content words across the sample thoughts."""
    counts: dict[str, int] = {}
    for t in samples or []:
        seen = set()
        for w in re.findall(r"[a-zA-Z']{4,}", (t or "").lower()):
            if w in _STOP or w in seen:
                continue
            seen.add(w)
            counts[w] = counts.get(w, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return ", ".join(w for w, n in top if n >= 2) or ", ".join(w for w, _ in top)


def _day_spread(c: dict) -> str:
    days = sorted(set(c.get("days", []) or []))
    if not days:
        return "unknown"
    return (f"{len(c.get('sample_thoughts', []))} thoughts shown, from a cluster of "
            f"{c.get('n')} on {len(days)} distinct days (day {days[0]} to day {days[-1]})")


def _priming_record(samples: list[str]) -> dict:
    """Step 3: consult core.symbol_tracker's primed/unprimed record. The tracker follows a fixed symbol list,
    so a cluster is checkable only when its sample thoughts hit a tracked symbol's surface forms. Then the
    symbol's own record decides: appearances that were never unprimed mean the image was injected."""
    out = {"checked": False, "symbols": {}, "primed_only": False}
    try:
        from core import symbol_tracker as st
        text = " ".join(samples or []).lower()
        rep = st.symbol_report()
        for sym, forms in st._SYMBOLS.items():
            if any(f.lower() in text for f in forms):
                r = rep.get(sym)
                if isinstance(r, dict) and "primed" in r:
                    out["symbols"][sym] = {"primed": r["primed"], "unprimed": r["unprimed"]}
        out["checked"] = bool(out["symbols"])
        out["primed_only"] = bool(out["symbols"]) and all(v["unprimed"] == 0 and v["primed"] > 0
                                                            for v in out["symbols"].values())
    except Exception as exc:
        out["error"] = repr(exc)[:80]
    return out


def _build_control_sets(candidates: list[dict], now: float, n_sets: int = CONTROL_SETS) -> list[list[str]]:
    """Each set: ONE thought from each of 6 DIFFERENT clusters (deterministic per scan: rotated by `now`).
    Needs at least 6 clusters with a sample thought."""
    pools = [c.get("sample_thoughts", []) for c in candidates if c.get("sample_thoughts")]
    if len(pools) < 6:
        return []
    sets = []
    base = int(now // SCAN_INTERVAL_S)
    for s in range(n_sets):
        picked = []
        # distinct clusters: take a rotating window of 6 clusters, one thought each
        start = (base + s * 6) % len(pools)
        for j in range(6):
            pool = pools[(start + j) % len(pools)]
            picked.append(pool[(base + s + j) % len(pool)])
        sets.append(picked)
    return sets


async def run_claim_control(candidates: list[dict], now: float) -> dict:
    """Run the panel on control sets (6 thoughts from 6 different clusters, no shared image) and log the
    yes-rate as kind 'claim_control'. A yes-rate above CONTROL_MAX_YES_RATE means the panel is not evidence."""
    from core import left_lane
    sets = _build_control_sets(candidates, now)
    if not sets:
        rec = {"kind": "claim_control", "available": False, "reason": "fewer than 6 clusters with samples",
               "evidence_valid": False}
        _log(rec)
        return rec
    results = []
    for sset in sets:
        try:
            v = await left_lane.claim_test_panel(sset, image="(mixed, no shared image)",
                                                 day_spread="six unrelated clusters, one thought each")
        except Exception as exc:
            logger.info("[watershed-promote] control panel call failed (non-fatal): %s", repr(exc)[:80])
            v = None
        results.append(v)
    answered = [v for v in results if v is not None]
    if not answered:
        rec = {"kind": "claim_control", "available": False, "reason": "judges unavailable", "evidence_valid": False}
        _log(rec)
        return rec
    yes = sum(1 for v in answered if v.get("genuine"))
    rate = yes / len(answered)
    rec = {"kind": "claim_control", "available": True, "sets": len(answered), "yes": yes,
           "yes_rate": round(rate, 3), "threshold": CONTROL_MAX_YES_RATE,
           "evidence_valid": rate <= CONTROL_MAX_YES_RATE,
           "j1_yes": sum(1 for v in answered if (v.get("judge1") or {}).get("genuine")),
           "j2_yes": sum(1 for v in answered if (v.get("judge2") or {}).get("genuine"))}
    _log(rec)
    return rec


async def scan(now: float | None = None, cooldown: bool = True) -> list[dict]:
    """Check all born-but-unjudged watershed candidates; classify + (if additive) claim-test each.
    Returns this scan's decision records (also logged). Fail-open per-candidate -- one bad judge
    call never blocks the others, and a candidate whose judge was unavailable is left un-judged so
    the NEXT scan retries it rather than silently dropping it."""
    now = now if now is not None else time.time()
    if cooldown and (now - _last_scan["ts"]) < SCAN_INTERVAL_S:
        return []
    _last_scan["ts"] = now

    state = _read_json(_WATERSHED_STATE, {"candidates": []})
    pstate = _promote_state()
    judged = pstate.setdefault("judged", {})
    decisions: list[dict] = []
    already_true = _already_true_claims()
    control: dict | None = None

    from core import left_lane

    for c in state.get("candidates", []):
        if not c.get("born") or c["id"] in judged:
            continue
        samples = c.get("sample_thoughts", [])
        candidate_text = samples[-1] if samples else ""
        rec = {"candidate_id": c["id"], "n": c.get("n"), "n_days": len(c.get("days", [])),
               "sample": candidate_text[:160]}

        try:
            cls = await left_lane.classify_additive_vs_replacing(candidate_text, already_true, samples)
        except Exception as exc:
            logger.info("[watershed-promote] classify failed for %s (non-fatal): %s", c["id"], repr(exc)[:80])
            cls = None
        rec["classification"] = cls

        if cls is None:
            _log({"kind": "classify_unavailable", **rec})
            decisions.append(rec)
            continue     # retry next scan, not marked judged

        if cls["classification"] == "not_a_self_claim":
            judged[c["id"]] = {"ts": now, "outcome": "not_a_self_claim", "classification": cls}
            _log({"kind": "not_a_self_claim", **rec})
            decisions.append(rec)
            continue     # J-3805: neither additive nor replacing; never previewed as a node

        if cls["classification"] != "additive":
            judged[c["id"]] = {"ts": now, "outcome": "replacing", "classification": cls}
            _log({"kind": "routed_replacing", **rec})
            decisions.append(rec)
            continue     # stays on the existing T4/keystone path -- untouched here

        # J-3806 step 3: drop sets whose symbol appearances were all primed (injected) before judging
        prim = _priming_record(samples)
        rec["priming"] = prim
        if prim.get("primed_only"):
            judged[c["id"]] = {"ts": now, "outcome": "primed_dropped", "classification": cls, "priming": prim}
            _log({"kind": "primed_dropped", **rec})
            decisions.append(rec)
            continue

        # J-3806 step 1: the standing control, once per scan, before any real claim is read as evidence
        if control is None:
            if now < float(pstate.get("control_fail_until", 0.0) or 0.0):
                control = {"kind": "claim_control", "available": True, "evidence_valid": False,
                           "reason": "backoff after a failed control", "skipped": True}
            else:
                control = await run_claim_control(state.get("candidates", []), now)
                if control.get("evidence_valid") is False:
                    pstate["control_fail_until"] = now + CONTROL_RETRY_S
        if not control.get("evidence_valid"):
            rec["claim_control"] = {k: control.get(k) for k in ("available", "yes_rate", "reason", "skipped")}
            _log({"kind": "claim_not_evidence", **rec})
            decisions.append(rec)
            continue     # retry once the control passes; not marked judged

        try:
            claim = await left_lane.claim_test_panel(samples, image=_image_terms(samples),
                                                     day_spread=_day_spread(c))
        except Exception as exc:
            logger.info("[watershed-promote] claim-test failed for %s (non-fatal): %s", c["id"], repr(exc)[:80])
            claim = None
        rec["claim_test"] = claim

        if claim is None:
            _log({"kind": "claim_test_unavailable", **rec})
            decisions.append(rec)
            continue     # retry next scan, not marked judged

        if claim.get("genuine"):
            preview = _preview_node(c["id"], samples, c.get("n", 0), c.get("first_ts"), c.get("last_ts"))
            if c.get("sample_refs"):   # J-3876: member ids so admit("harvest", ...) evidence links can resolve
                preview["sample_refs"] = list(c["sample_refs"])
            rec["would_promote_node"] = preview
            judged[c["id"]] = {"ts": now, "outcome": "would_promote", "classification": cls, "claim_test": claim}
            _log({"kind": "would_promote", **rec})
            logger.info("[watershed-promote] SHADOW: candidate %s would promote to disposition_earned "
                       "(additive, claim-test genuine): %r", c["id"], candidate_text[:70])
        else:
            judged[c["id"]] = {"ts": now, "outcome": "additive_but_not_genuine", "classification": cls,
                               "claim_test": claim}
            _log({"kind": "additive_rejected", **rec})
        decisions.append(rec)

    pstate["judged"] = judged
    _save_promote_state(pstate)
    return decisions


# D-0605 (founder, 2026-11-02, plan t4_watershed): the periodic Phase 0.5 scan (classifier + claim-test panel,
# called from nodes/subconscious_node.py every WATERSHED_PROMOTE_INTERVAL) is PARKED. The harvester
# (core/watershed.py observe()) and its birth log keep running; all data stays. DEFEATER: revisit when the
# estate-node build (plan build order 5) is scheduled, or if the parked scan proves the only source of some
# evidence a plan needs. Set True to resume. RESTART-REQ.
WATERSHED_PROMOTE_SCAN = False


def status() -> dict:
    """For the pulse/HUD, same shape convention as core/watershed.py's status()."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()] if _LOG.exists() else []
    except Exception:
        rows = []
    would_promote = [r for r in rows if r.get("kind") == "would_promote"]
    routed_replacing = [r for r in rows if r.get("kind") == "routed_replacing"]
    rejected = [r for r in rows if r.get("kind") == "additive_rejected"]
    pstate = _promote_state()
    return {"parked": not WATERSHED_PROMOTE_SCAN,
            "state": "parked (D-0605)" if not WATERSHED_PROMOTE_SCAN else "scanning",
            "judged_total": len(pstate.get("judged", {})), "would_promote": len(would_promote),
            "routed_replacing": len(routed_replacing), "additive_rejected": len(rejected),
            "verdict": (f"{len(would_promote)} candidate(s) would promote to disposition_earned "
                       "nodes if this were live" if would_promote else
                       "no candidate has cleared the additive claim-test yet")}


if __name__ == "__main__":
    import asyncio
    print(json.dumps(asyncio.run(scan(cooldown=False)), indent=2, ensure_ascii=False))

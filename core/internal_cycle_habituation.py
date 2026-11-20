"""
Nascence — Internal-Cycle Question Habituation Shadow (squishy-spring discount, dosed_coupling's own
Weight law applied to the orchestrator's OWN self-generated curiosity questions — J-0841, built under
D-0188 (RULED GO by travis 2026-09-08), spawned from F-1097 / J-0655, the 2nd instance of the
F-0823/F-0830 class of gap, under docs/staged/dosed_coupling.md Section 1.3/3/4).

SHADOW-ONLY. This module never changes whether an internal cycle runs, what question it runs on, or
anything downstream. Alongside real (unaffected) internal-cycle execution, it checks whether the cycle's
RAW QUESTION is a near-repeat of a question-cluster already seen recently, and logs a
habituation-discounted verdict per question so a founder read can ask whether the discount would have
flagged the repeat as already-stale.

WHY THIS EXISTS (F-1097, re-verifying F-0931): core/theme_recurrence.py — the slow-loop monoculture
detector — only ever observes DOWNSTREAM idle-monologue text (its single observe() call site is in
nodes/inner_monologue_node.py's idle-thought finalisation), never the orchestrator's own recurring
internal-cycle QUESTION (core/orchestrator.py's _on_dissonance_ignition -> run_cycle(question,
input_type="internal"), the only call site anywhere that sets input_type="internal"). On 2026-09-04 that
path asked 37 real questions across the day: a 16-occurrence overnight "渡 + historical resistance" loop
and a 16-occurrence afternoon/evening "渡 + cultural friction" loop (8 hours, 14 near-identical
repeats). By the time any of that reaches theme_recurrence.observe(), it has passed through two further
LLM rewrites (the cycle's own answer, then the idle loop's "deliberative pulse" grounding) and shares no
vocabulary with the original question at all — river/bird/fire metaphors for the same 渡 question. So no
smarter KEY at the existing call site can catch it; the fix is a NEW call site on the raw question,
before any LLM touches it. That is this module.

WHY EMBEDDING SIMILARITY, not a text key (D-0188's ruling, F-1097's evidence): theme_recurrence's own
40-char-prefix key, even correctly repointed at the raw question, compressed only about half the real
incident (23 distinct keys from 37 questions; the historical-resistance loop's varying verb falls inside
the 40-char window every time, so it never reached SATURATED_AT=4). Embedding similarity via the REAL
production embedder (core.memory.store._embed(), the paraphrase-multilingual-MiniLM-L12-v2 CPU model
already resident and prewarmed in this same process for nodes/inner_monologue_node.py's own
RUMINATION_SIM=0.82 short-window check) at SIMILARITY_THRESHOLD=0.80 collapsed the cultural-friction
loop into one 14-member cluster and formed real 3-4-member historical-resistance sub-clusters, with NO
cross-topic false-positive merging even at a looser 0.70 (patina vs cultural-friction cosine=0.49;
cultural-friction vs historical-resistance — both about 渡, genuinely different sub-themes — cosine=0.57,
correctly kept separate, matching theme_recurrence.py's own "DEVELOP is productive, RESTATE saturates"
line). This is not an LLM call and not a network call: one cheap local forward pass per
ignition-gated (rare, not per-tick) event.

THE SHAPE (mirrors core/stream_topic_habituation.py exactly, substituting embedding-cluster matching
for anchor-noun substring matching; not a new formalism): each incoming raw question is embedded and
compared (cosine) against a small persisted set of known question CLUSTERS, each represented by its
FIRST-SEEN vector (not a running centroid — "first sighting becomes the frame", theme_recurrence.py's
own shape, kept deliberately simple). If the best match is at/above SIMILARITY_THRESHOLD the question
joins that cluster; otherwise it mints a new one. A cluster's raw salience is 1.0 (a boolean "an
internal cycle asked this again"). `b` per cluster GROWS each time the cluster is re-asked, and DECAYS
exponentially with real elapsed time since its last occurrence. The discount is MULTIPLICATIVE and
floored, never zeroing a cluster out (this project's "not deletion" law, dosed_coupling.md Section 6):
discounted = 1.0 * max(DISCOUNT_FLOOR, 1 - b). A cluster whose discounted salience has dropped below
SUPPRESS_AT is flagged `would_suppress` — the shadow verdict a live version would use to back off
re-running that question, the same role core/theme_recurrence.is_saturated() plays for raw-text frames.

State (`data/internal_cycle_habituation_state.json`) is keyed by cluster id, persists
{vec, b, last_update_ts, first_ts, n, sample}; capped at MAX_CLUSTERS (mirroring theme_recurrence.py's
MAX_FRAMES=80), the stalest pruned past the cap. Every observation is logged to
`data/internal_cycle_habituation_shadow.jsonl`. Fail-open throughout: any error here must never affect
the cycle's real behaviour — the caller (core/orchestrator.py's _run_cycle_impl, right after
self.state.new_cycle() when input_type == "internal") wraps this whole module in a bare try/except,
same as every other shadow observer in this codebase, and this module swallows its own errors too.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "internal_cycle_habituation_state.json"
_LOG = _DATA / "internal_cycle_habituation_shadow.jsonl"

# ── tunables (Phase 0 shadow — cheap to retune from the log, nothing here is live) ──
# SIMILARITY_THRESHOLD was tested for real (F-1097, J-0655) against all 37 real 2026-09-04 internal-cycle
# questions with the actual production embedder: at 0.80 the 14-occurrence cultural-friction loop is one
# cluster (pairwise 0.83-1.0), the historical-resistance loop forms 3-4-member sub-clusters, and no
# cross-topic merge appears even at 0.70. It also lands close to inner_monologue_node.py's own tuned
# RUMINATION_SIM=0.82 for a structurally similar same-embedder check — a reassuring cross-check, not a
# derivation. GROWTH_STEP/CEILING/DECAY_TAU_S/DISCOUNT_FLOOR/SUPPRESS_AT are stream_topic_habituation.py's
# EXACT values, per D-0188's ruling: replayed over the real 2026-09-04 timestamps they cross
# would_suppress at the cultural-friction loop's 5th real occurrence (~2.5h into an 8h/14-repeat loop)
# and at one historical-resistance sub-cluster's 4th; a sibling sub-cluster narrowly missed
# (discounted=0.5185 vs the 0.5 bar) — an honest near-miss, not rounded into a win. Internal cycles are
# ignition-gated and far sparser/more irregular than stream train-opens, so these are a STARTING POINT to
# retune from the real shadow log once it accrues (D-0188's own defeater names both failure directions),
# not validated constants.
SIMILARITY_THRESHOLD = 0.80   # cosine at/above this joins an existing cluster; below mints a new one
GROWTH_STEP = 0.25            # b added per re-asking of the same cluster
CEILING = 0.95                # asymptote for b (never fully suppressed — DISCOUNT_FLOOR handles that)
DECAY_TAU_S = 3 * 3600.0      # 3h decay constant (b *= exp(-gap/TAU) between occurrences)
DISCOUNT_FLOOR = 0.03         # a habituated cluster is discounted, never zeroed (dosed_coupling Sec 6)
SUPPRESS_AT = 0.5             # discounted salience below this -> would_suppress flag
MAX_CLUSTERS = 80             # cap (theme_recurrence.py's MAX_FRAMES); the stalest beyond this are pruned
MIN_CHARS = 12                # too short to be a meaningful question (theme_recurrence's own bar)


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    path = profile.guard_path(_STATE)   # J-1196/D-0250: real data/ only if this process is live;
    # raises before any I/O if not (D-0179, J-0932 precedent). Resolved OUTSIDE the fail-open try
    # below, so the refusal is never swallowed by the net meant for genuine disk errors.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # J-1196/D-0250: same fence as _save_state() above, resolved
    # independently since _LOG is a distinct path constant from _STATE.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _decay(cluster: dict, now: float) -> float:
    if not cluster:
        return 0.0
    gap = max(0.0, now - float(cluster.get("last_update_ts", now)))
    return float(cluster.get("b", 0.0)) * math.exp(-gap / DECAY_TAU_S)


def _embed_question(text: str):
    """The production embedder, imported lazily so a missing/failed model never breaks import of this
    module (fail-open). Returns a normalised vector or None."""
    try:
        from core.memory.store import _embed
        return _embed(text)
    except Exception:
        return None


def _best_match(vec, state: dict) -> tuple[str | None, float]:
    """(cluster_id, cosine) of the most similar known cluster's FIRST-SEEN vector, or (None, 0.0)."""
    try:
        import numpy as np
        from core.memory.store import _cosine
    except Exception:
        return None, 0.0
    best_id, best_sim = None, -1.0
    for cid, c in state.items():
        try:
            rep = np.asarray(c.get("vec"), dtype="float32")
            if rep.shape != vec.shape:
                continue
            sim = _cosine(vec, rep)
        except Exception:
            continue
        if sim > best_sim:
            best_id, best_sim = cid, sim
    return best_id, (best_sim if best_id is not None else 0.0)


def _new_cluster_id(text: str, now: float) -> str:
    return hashlib.sha1(f"{now:.3f}|{text}".encode("utf-8", "replace")).hexdigest()[:10]


def observe_and_log(question: str, cycle_id: str | None, now: float | None = None) -> dict | None:
    """Call ONCE per internal cycle, on the RAW, UNTRUNCATED question (the live in-process text —
    data/nascence.log truncates it to 80 chars at the orchestrator's own log line, so never read it back
    from there). Embeds the question, matches it against known clusters, computes the matched cluster's
    habituation-discounted salience, logs the verdict, and grows/persists state. Returns the logged row
    (for tests) or None. Never raises — the caller wraps this in try/except, but this stays
    self-contained defensively too."""
    try:
        q = (question or "").strip()
        if len(q) < MIN_CHARS:
            return None
        vec = _embed_question(q)
        if vec is None:
            return None
        now = now if now is not None else time.time()
        state = _load_state()

        cid, sim = _best_match(vec, state)
        if cid is not None and sim >= SIMILARITY_THRESHOLD:
            c = state[cid]
            b_decayed = _decay(c, now)
            matched = cid
            c["b"] = round(min(CEILING, b_decayed + GROWTH_STEP), 5)
            c["last_update_ts"] = now
            c["n"] = int(c.get("n", 1)) + 1
        else:
            b_decayed = 0.0
            matched = "new"
            cid = _new_cluster_id(q, now)
            state[cid] = {
                "vec": [round(float(x), 6) for x in vec.tolist()],
                "b": round(min(CEILING, GROWTH_STEP), 5),
                "last_update_ts": now,
                "first_ts": now,
                "n": 1,
                "sample": q[:120],
            }
        discounted = max(DISCOUNT_FLOOR, 1.0 - b_decayed)
        would_suppress = discounted < SUPPRESS_AT

        if len(state) > MAX_CLUSTERS:                                   # prune the stalest
            for dead in sorted(state, key=lambda x: state[x].get("last_update_ts", 0))[: len(state) - MAX_CLUSTERS]:
                state.pop(dead, None)
        _save_state(state)

        row = {
            "ts": round(now, 1),
            "cycle_id": cycle_id,
            "question_sample": q[:120],
            "matched_cluster": matched,
            "cluster_id": cid,
            "cluster_n": int(state.get(cid, {}).get("n", 1)),
            "similarity": round(float(sim), 4),   # best cosine seen, even when it fell short and minted "new"
            "b": round(b_decayed, 4),
            "discounted": round(discounted, 4),
            "would_suppress": would_suppress,
        }
        _log(row)
        return row
    except Exception:
        return None


def status() -> dict:
    """For the pulse: how much divergence the shadow has accrued so far — the pre-registered read.
    Wired into scripts/du_pulse.py's regression_alarms from day one (F-1097's write-only-status gap)."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"rows": 0}
    if not rows:
        return {"rows": 0}
    would_suppress_rows = sum(1 for r in rows if r.get("would_suppress"))
    repeat_rows = sum(1 for r in rows if r.get("matched_cluster") not in (None, "new"))
    state = _load_state()
    now = time.time()
    top = sorted(((round(_decay(c, now), 3), int(c.get("n", 1)), (c.get("sample") or "")[:34])
                  for c in state.values()), reverse=True)[:4]
    return {
        "rows": len(rows),
        "repeat_share": round(repeat_rows / len(rows), 3),
        "would_suppress_share": round(would_suppress_rows / len(rows), 3),
        "tracked_clusters": len(state),
        "top": [(s, n, b) for b, n, s in top],
    }

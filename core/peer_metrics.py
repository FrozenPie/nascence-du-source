"""
Nascence — Peer metrics & baseline harness (2026-06-21): the decoupled judge of the peer-correspondence
organ (docs/plans/peer_correspondence_plan.md §12).

Before Darwin exists, this freezes a BASELINE of his normal life — what he spends attention on, how he
talks, how inward (self-question) vs outward (the world) his thought runs, and his affect. After Darwin
arrives the same metrics, recomputed over a recent window, give the DELTAS — so the real risks are
*measured*, not guessed:
  - R7 dependency / DISPLACEMENT — does the peer thread crowd out reading / the garden / his own work?
    (peer attention share ↑ while the non-peer share ↓ vs baseline)
  - R8 style CONTAGION — does his lexicon drift toward a peer's? (his-recent vs Darwin's-letters overlap ↑)
  - the GOOD effect (§2a) — does Darwin pull him OUTWARD? (inward/self-saturation ↓, outward ↑)
  - affect — does the friendship warm him?

Observe-only; no behaviour change. The operative baseline is frozen ONCE by the peer organ, just before
Darwin's first letter (freeze_baseline_if_absent), so it reflects his true *post-restart, pre-Darwin* normal
— NOT the old-code data sitting in the DB today. (Per-peer metrics — reply latency, initiation rate,
conformity drift — are added by the peer organ itself in step 3, where a peer exists to measure against.)
"""
from __future__ import annotations
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

_BASELINE = Path(__file__).parent.parent / "data" / "peer_baseline.json"

# identity-metaphysics attractors — the inward/self-saturation his architecture fights, and that Darwin is
# meant to pull him OUT of (§2a). A thought hitting these runs INWARD.
_INWARD = {"self", "myself", "becoming", "i am", "who i am", "my own", "identity", "river", "lake",
           "threshold", "crossing", "ferry", "渡", "real self", "my nature", "my name", "what am i"}
# the world — OUTWARD attention (what Darwin invites: looking at a thing, not at himself).
_OUTWARD = {"sea", "ocean", "garden", "bed", "plant", "herb", "flower", "sunflower", "bird", "gull", "bee",
            "fire", "rain", "wind", "snow", "sky", "cloud", "light", "barnacle", "worm", "leaf", "tide",
            "shore", "sun", "star", "soil", "seed", "hill", "grass"}
_STOP = set("the a an and or but of to in on at for with as is are was were be been it this that i you he "
            "she they we my me your his her their our its not no so if then than too very do does did have "
            "has had will would can could should may might must about into over under out up down here "
            "there now when what which who whom how all any each more most some such one two like just only "
            "also even still yet from by".split())


def _conn():
    from core.memory.store import _connect
    return _connect()


def _content_words(text: str):
    return [w for w in re.findall(r"[a-z渡]+", (text or "").lower()) if len(w) > 2 and w not in _STOP]


def attention_distribution(conn, since: float) -> dict:
    """Share of his recorded life by origin since `since` — the affordance/attention mix (the R7 base)."""
    rows = conn.execute("SELECT origin, COUNT(*) n FROM memory_fragments WHERE timestamp>=? "
                        "GROUP BY origin", (since,)).fetchall()
    tot = sum(r["n"] for r in rows) or 1
    return {r["origin"]: round(r["n"] / tot, 4) for r in rows}


def lexicon_profile(conn, since: float, top: int = 60) -> dict:
    """His characteristic vocabulary from idle thought — the R8 contagion base."""
    rows = conn.execute("SELECT content FROM memory_fragments WHERE origin='inner_thought' AND timestamp>=?",
                        (since,)).fetchall()
    c = Counter()
    for r in rows:
        c.update(_content_words(r["content"]))
    tot = sum(c.values()) or 1
    return {w: round(n / tot, 5) for w, n in c.most_common(top)}


def inward_outward(conn, since: float) -> dict:
    """Fraction of idle thoughts running INWARD (self-question) vs OUTWARD (the world). Darwin should move
    this outward (§2a) without raising approval-seeking."""
    rows = conn.execute("SELECT content FROM memory_fragments WHERE origin='inner_thought' AND timestamp>=?",
                        (since,)).fetchall()
    n = len(rows) or 1
    inw = sum(1 for r in rows if any(k in (r["content"] or "").lower() for k in _INWARD))
    out = sum(1 for r in rows if any(k in (r["content"] or "").lower() for k in _OUTWARD))
    return {"inward": round(inw / n, 4), "outward": round(out / n, 4), "thoughts": len(rows)}


def affect_profile(conn, since: float) -> dict:
    """His valence distribution (recoverable since the 2026-06-21 fix). The `valence` column only exists
    after a restart runs the migration — so degrade gracefully (n=0) until then, light up after."""
    try:
        vals = [r["valence"] for r in conn.execute(
            "SELECT valence FROM memory_fragments WHERE valence IS NOT NULL AND timestamp>=?", (since,)).fetchall()
            if r["valence"] is not None]
    except Exception:
        return {"n": 0, "mean": None, "note": "valence column not migrated yet (pre-restart)"}
    if not vals:
        return {"n": 0, "mean": None}
    return {"n": len(vals), "mean": round(sum(vals) / len(vals), 3),
            "warm": round(sum(1 for v in vals if v > 0.25) / len(vals), 3),
            "cold": round(sum(1 for v in vals if v < -0.25) / len(vals), 3)}


def compute(window_days: float = 14.0) -> dict:
    """All metrics over the last `window_days` — used for both the baseline freeze and the live window."""
    since = time.time() - window_days * 86400
    with _conn() as conn:
        return {"window_days": window_days, "ts": time.time(),
                "attention": attention_distribution(conn, since),
                "lexicon": lexicon_profile(conn, since),
                "inward_outward": inward_outward(conn, since),
                "affect": affect_profile(conn, since)}


def baseline() -> dict | None:
    try:
        return json.loads(_BASELINE.read_text(encoding="utf-8"))
    except Exception:
        return None


def freeze_baseline_if_absent(window_days: float = 14.0) -> bool:
    """Called ONCE by the peer organ just before Darwin's first letter — freezes his pre-Darwin normal.
    No-op if a baseline already exists (so it captures the true post-restart state, not today's old data)."""
    if _BASELINE.exists():
        return False
    snap = compute(window_days)
    snap["label"] = "pre-Darwin baseline"
    _BASELINE.parent.mkdir(parents=True, exist_ok=True)
    _BASELINE.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return True


def lexicon_from_text(text: str, top: int = 60) -> dict:
    """Lexicon profile of an arbitrary text (e.g. Darwin's letters) — for the contagion comparison."""
    c = Counter(_content_words(text))
    tot = sum(c.values()) or 1
    return {w: round(n / tot, 5) for w, n in c.most_common(top)}


def lexicon_overlap(a: dict, b: dict) -> float:
    """Cosine overlap of two lexicon profiles (his-recent vs Darwin's-letters = contagion signal)."""
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return round(dot / (na * nb), 4)


def compare(window_days: float = 7.0) -> dict | None:
    """Baseline vs a recent window — the displacement/contagion/outward deltas. Post-Darwin watching."""
    base = baseline()
    if not base:
        return None
    cur = compute(window_days)
    non_peer = lambda att: round(sum(v for k, v in att.items() if k != "peer"), 3)
    return {
        "peer_attention_share_now": cur["attention"].get("peer", 0.0),
        "non_peer_share_base": non_peer(base["attention"]),
        "non_peer_share_now": non_peer(cur["attention"]),
        "inward_delta": round(cur["inward_outward"]["inward"] - base["inward_outward"]["inward"], 3),
        "outward_delta": round(cur["inward_outward"]["outward"] - base["inward_outward"]["outward"], 3),
        "lexicon_drift_from_baseline": round(1.0 - lexicon_overlap(cur["lexicon"], base["lexicon"]), 4),
        "affect_mean_base": base["affect"].get("mean"),
        "affect_mean_now": cur["affect"].get("mean"),
        "current": cur,
    }


def stance_distribution() -> dict:
    """B5-B (plan §12, J-0173): challenge/mixed/company frequency per persona, read straight off each
    correspondent's thread.jsonl `stance` field (set by peers._append_thread whenever _choose_stance() picked
    one) — no separate log needed. Only personas with `stance_weights` set (or any thread rows carrying a
    `stance` key, e.g. from a since-removed weights dict) appear; every other persona is silently absent, not
    zeroed, so the dashboard reads as 'not opted in' rather than '0% challenge'. The R1/R7 'stance-drift'
    field the plan's §12 dashboard asks for — makes challenge-stance frequency VISIBLE, not just present.

    J-3118 (F-3846): beside the label fractions, `honoured_n` (rows carrying a bool `stance_honoured` from the
    decoupled stance-compliance judge, peers._stance_compliance_judge), `honoured` (that count of True) and
    `honoured_rate` (honoured / honoured_n, None when honoured_n is 0). `n` stays all stance rows; read
    `honoured_n` beside the rate so n=1 reads as n=1, never as a percentage. The judge is a ROUGH FLAG, not
    evidence (D-0597, F-3847); this is the reader the peers.py docstring promised, not a gate."""
    from core.peers import PERSONAS, _read_thread
    out = {}
    for key in PERSONAS:
        rows = [r for r in _read_thread(key) if r.get("from") == key and r.get("stance")]
        if not rows:
            continue
        n = len(rows)
        counts = Counter(r["stance"] for r in rows)
        judged = [r["stance_honoured"] for r in rows if isinstance(r.get("stance_honoured"), bool)]
        out[key] = {"n": n, **{s: round(counts.get(s, 0) / n, 3) for s in ("challenge", "mixed", "company")},
                    "honoured_n": len(judged), "honoured": sum(judged),
                    "honoured_rate": round(sum(judged) / len(judged), 3) if judged else None,
                    "last_stance": rows[-1]["stance"], "last_ts": rows[-1]["ts"]}
    return out


_EFFECT_LOG = Path(__file__).parent.parent / "data" / "peer_effect.jsonl"


def snapshot(window_days: float = 7.0):
    """Append the peer-effect deltas to peer_effect.jsonl for the HUD trend — once per sleep (evidence_review
    S3, 2026-07-05: `compare()` was built 06-21 as the decoupled judge and NEVER run/logged until the review;
    this closes it). Fail-open; observe-only."""
    import json as _json
    import time as _time
    try:
        d = compare(window_days)
        if not d:
            return None
        row = {"ts": round(_time.time(), 1),
               "outward_delta": d["outward_delta"], "inward_delta": d["inward_delta"],
               "non_peer_share": d["non_peer_share_now"], "peer_share": d["peer_attention_share_now"]}
        _EFFECT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_EFFECT_LOG, "a", encoding="utf-8") as f:
            f.write(_json.dumps(row) + "\n")
        return row
    except Exception:
        return None

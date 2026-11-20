"""
core/idle_allocator.py — the Idle Executive, Phase 0 (SHADOW / observe-only).

Spec: docs/staged/idle_executive_plan.md (v6). This is the measurement layer the five auditor
rounds converged on building first ("logging before control", §12).

What it does, each idle tick: gather the discretionary idle-action candidates, ask each
CHANNEL for a DECLARED salience scalar drawn from its OWN domain signal, run the §9
divisive-normalisation pipeline (per-channel percentile × confined weight × winner
habituation), select content-blind (softmax τ=0.35 AND argmax — both logged), and append
the whole picture to data/logs/idle_shadow.jsonl. It FEEDS NOTHING. Zero behaviour change.

The three-separations operating invariant (§12), enforced here:
  1. content generation stays at the source signals (each channel reads only its domain);
  2. SELECTION is content-BLIND — it reads scalars + declared binding-keys, never thought text;
  3. calibration is OUT OF SCOPE for Phase 0 (we only measure; nothing learns yet).

Everything is fail-open: a channel that errors is simply absent this tick, and the whole
tick is wrapped so a shadow failure can never touch the live idle loop.
"""
from __future__ import annotations

import json
import math
import random
import re
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants — the confined, design-time-auditable knobs (§9 / §12).
# ---------------------------------------------------------------------------
SHADOW_ENABLED = True

HIST_K       = 500     # per-channel sliding history buffer (§9 divisive normalisation)
MIN_HISTORY  = 20      # cold-start floor: below this, percentile is meaningless → flat 0.5 prior (§9 caveat)
DELTA        = 0.15    # winner-habituation decay: S *= (1 - DELTA*winner_streak)
TAU          = 0.35    # softmax temperature for the exploration policy (Gemini Q2)
ACTIVE_FLOOR = 0.05    # a channel counts as "co-active" this tick if raw_intensity >= this (§11 co-occurrence)

# The confined per-channel priority weight vector W (§9.2). The ONLY place cross-channel
# commensurability lives — a handful of visible constants, not emergent transform magnitudes.
W = {
    "contradiction": 1.00,
    "concern":       0.90,
    "balance_world": 0.85,
    "curiosity":     0.80,
    "balance_light": 0.70,
    "self":          0.60,   # the gravity well — deliberately given a real weight so its win-share is measurable (G2)
    "boredom":       0.50,   # a REGULATORY channel (key = "mode_failing"), not a topic channel (§10.1)
    "wander":        0.40,   # the DMN default; rises when the psyche is calm (Gemini Q2)
    "flavour":       0.30,   # room-scene / symbol low-information seeds
}

# G1 go-live gate (corrected 2026-06-22, after 3,580 shadow ticks; balance_* re-classified GRADED 2026-10-07, J-1921).
# Only the GRADED channels -- whose intensity is MEANT to track his state -- are held to the variance bar. The rest are
# constant BY DESIGN and exempt: `self` is a fixed gravity-well baseline (held constant on purpose, so its win-share
# measures the G2 anti-self gate) and `flavour` is a fixed low-information fallback.
# `balance_light`/`balance_world` were exempted on 2026-06-22 as "binary regulators", but that was a post-hoc reading of
# a bug (F-2543/F-2548): they read the COUNT keys of balance.shares() instead of the 0..1 shares, so raw was a constant
# 0.0 and p_norm pinned at 1.0. They are graded deficits (raw = (TARGET - share)/TARGET) and, since the J-1921 fix, are
# held to the G1 bar like any other graded channel.
# J-1935 / F-2560: `concern` left GRADED_CHANNELS. Its raw is two-level BY DESIGN (0.55 pursuit vs 0.45 project;
# concerns.primary_concern() is a categorical pick with no magnitude), so the G1 variance bar does not apply to it.
# It is NOT merely "constant": see CONCERN_BYPASS_PERCENTILE below -- a two-level channel must also skip the percentile.
# `curiosity` stays GRADED: its upstream LP is binary {0,2} (F-2560), constant by upstream construction not by design.
GRADED_CHANNELS    = ("contradiction", "curiosity", "boredom", "wander", "balance_world", "balance_light")
CONSTANT_BY_DESIGN = ("self", "flavour")
TWO_LEVEL_BY_DESIGN = ("concern",)
# The declared levels of each two-level channel (max level = the p_norm denominator under the bypass).
TWO_LEVEL_MAX = {"concern": 0.55}

# J-1921 / F-2548 kill switch: True = the balance channels read balance.shares()["reality_share"/"light_share"] (0..1);
# False = the pre-fix count-key read (raw ~0.0 constant). Shadow-only either way -- the allocator feeds nothing.
BALANCE_USE_SHARES = True
# State-file schema stamp. A state file without balance_schema >= 2 holds 500 rows of the old constant 0.0 for the two
# balance channels; on first load under BALANCE_USE_SHARES those two histories are dropped (once) so the percentile
# re-warms from the real signal instead of ranking it against 500 zeros.
BALANCE_SCHEMA   = 2
BALANCE_CHANNELS = ("balance_world", "balance_light")

# J-1935 / F-2560 PART B kill switch: True = channels in TWO_LEVEL_BY_DESIGN skip the within-history percentile and score
# p_norm = raw / max declared level (concern: 0.55 -> 1.0, 0.45 -> 0.818), i.e. the declared 1.22x preference itself.
# False = the exact old percentile read. History for those channels keeps accruing either way (it is simply not read for
# p_norm under the bypass) -- so no concern_schema reset: flipping the switch off must restore the old read byte-for-byte,
# which needs the 500-row history intact, and there is no wrong-signal era to purge (concern raw was always correct).
CONCERN_BYPASS_PERCENTILE = True

# J-1935 / F-2560 PART A kill switch: True = _ch_curiosity reads the closeable-backlog fraction (open, unparked questions
# carrying a finding / open unparked questions) instead of min(1, lp/2), which is exactly 1.0 whenever any question carries
# a finding (upstream LP is binary {0,2}). DEFAULT FALSE: measured across 12 frontier backups (2026-08-24..10-08) the
# fraction ranges only 0.127-0.204 (variance ~0.0007, far below the G1 bar 0.05) -- non-constant but slow-moving, so it is
# prepared, tested, and left off until a founder/analysis call says it is worth the BREAK POINT. False = the old read.
CURIOSITY_USE_BACKLOG = False
CURIOSITY_SCHEMA = 2     # state stamp; the 500-deep constant-1.0 curiosity history is dropped once under the switch

_DATA   = Path(__file__).parent.parent / "data"
_STATE  = _DATA / "idle_allocator_state.json"
_LOG    = _DATA / "logs" / "idle_shadow.jsonl"


# ---------------------------------------------------------------------------
# Persistence — per-channel history + winner streaks (the only state we keep).
# ---------------------------------------------------------------------------
def _load_state() -> dict:
    try:
        if _STATE.exists():
            return json.loads(_STATE.read_text(encoding="utf-8")) or {}
    except Exception:
        pass
    return {}


def _save_state(st: dict) -> None:
    try:
        _STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(st), encoding="utf-8")
        tmp.replace(_STATE)
    except Exception:
        pass


def _migrate_balance_history(st: dict) -> bool:
    """J-1921: one-time, in-memory drop of the two balance channels' history (the constant-0.0 era) and the schema
    stamp; the caller's normal _save_state persists it (atomic tmp+replace). Idempotent; returns True if it ran."""
    if not BALANCE_USE_SHARES:
        return False
    try:
        if int(st.get("balance_schema", 0) or 0) >= BALANCE_SCHEMA:
            return False
    except Exception:
        pass
    hist = st.setdefault("history", {})
    for ch in BALANCE_CHANNELS:
        hist.pop(ch, None)
    st["balance_schema"] = BALANCE_SCHEMA
    return True


def _migrate_curiosity_history(st: dict) -> bool:
    """J-1935: one-time, in-memory drop of the curiosity history (the constant-1.0 era) + schema stamp, only under
    CURIOSITY_USE_BACKLOG. Same shape as _migrate_balance_history; persisted by the caller's _save_state."""
    if not CURIOSITY_USE_BACKLOG:
        return False
    try:
        if int(st.get("curiosity_schema", 0) or 0) >= CURIOSITY_SCHEMA:
            return False
    except Exception:
        pass
    st.setdefault("history", {}).pop("curiosity", None)
    st["curiosity_schema"] = CURIOSITY_SCHEMA
    return True


def _slug(text: str, n: int = 6) -> str:
    """A cheap, content-blind binding key: lowercase word-stems of a DECLARED label/topic field.
    NOTE (round 4 concession, §10.1): this is *relocated cognition* — choosing the abstraction
    level is a small semantic act. It is logged as lineage and held to the same contract as the
    salience transform. It catches only SEMANTIC coalitions; regulatory ones (e.g. boredom's
    'mode_failing' key) are tagged separately."""
    toks = re.findall(r"[a-z]{4,}", (text or "").lower())
    stop = {"with", "that", "this", "from", "into", "between", "both", "have", "what", "when",
            "the", "and", "for", "working", "through", "pursuing", "closing"}
    toks = [t for t in toks if t not in stop]
    return "_".join(toks[:n]) if toks else "none"


def _percentile(history: list[float], raw: float) -> float:
    """Within-channel rank percentile of `raw` against the channel's own history (§9.1)."""
    if not history:
        return 0.5
    below = sum(1 for x in history if x <= raw)
    return below / len(history)


# ---------------------------------------------------------------------------
# The channels — each returns (raw_intensity, binding_key, key_kind, justification, lineage)
# or None. Each reads ONLY its own domain signal. All fail-open.
# ---------------------------------------------------------------------------
def _ch_contradiction():
    from core import tension_ledger as tl  # noqa
    from core import store_persist as _sp  # J-2417 (F-3117): cached, read-only
    d = _sp.load_json_cached(_DATA / "subconscious_state.json")
    tensions = d.get("tensions") or []
    if not tensions:
        return None
    top = max(tensions, key=lambda t: float(t.get("chronic_mass", 0.0) or 0.0))
    mass = float(top.get("chronic_mass", 0.0) or 0.0)
    raw = min(1.0, mass / 8.0)            # declared transform: chronic mass, saturating at 8
    label = top.get("label", "")
    return (raw, _slug(label), "semantic",
            f"top tension chronic_mass={mass:.2f}",
            {"top_label": label[:60], "chronic_mass": round(mass, 3)})


def _ch_curiosity():
    from core import curiosity_progress as cp
    ranked = cp.rank()
    active = [r for r in ranked if not r.get("parked")]
    if not active:
        return None
    top = active[0]
    lp = float(top.get("lp", 0.0) or 0.0)
    if CURIOSITY_USE_BACKLOG:
        # J-1935: closeable-backlog pressure = open unparked questions carrying a finding / open unparked questions.
        n_active = len(active)
        # J-4084: under line-state progress a "partly" verdict (lp 1.0) is the closeable signal; no finding is read
        _floor = 1.0 if getattr(cp, "LINE_STATE_PROGRESS", False) else 2.0
        n_closeable = sum(1 for r in active if r.get("finding") or float(r.get("lp", 0.0) or 0.0) >= _floor)
        raw = n_closeable / n_active
        return (raw, _slug(top.get("q", "")), "semantic",
                f"closeable backlog {n_closeable}/{n_active}",
                {"top_q": top.get("q", "")[:60], "lp": round(lp, 3), "backlog_fraction": round(raw, 4),
                 "n_closeable": n_closeable, "n_active": n_active})
    raw = max(0.0, min(1.0, lp / 2.0))    # declared transform: learning-progress, saturating at 2
    return (raw, _slug(top.get("q", "")), "semantic",
            f"top learning-progress lp={lp:.2f}",
            {"top_q": top.get("q", "")[:60], "lp": round(lp, 3)})


def _ch_concern():
    from core import concerns
    c = concerns.primary_concern()
    if not c:
        return None
    kind = c.get("kind", "")
    raw = 0.55 if kind == "pursuit" else 0.45   # declared: an active pursuit edges a standing project
    return (raw, _slug(c.get("text", "")), "semantic",
            f"primary concern ({c.get('source','?')})",
            {"text": c.get("text", "")[:60], "source": c.get("source", "")})


def _balance_axis_value(sh: dict, share_key: str, *old_keys: str) -> float:
    """The axis value a balance channel measures its deficit against. J-1921: the 0..1 share (`share_key`) when
    BALANCE_USE_SHARES and balance.shares() carries it; otherwise the pre-fix keys (counts), kept only as a fallback."""
    if BALANCE_USE_SHARES and share_key in sh:
        return float(sh.get(share_key) or 0.0)
    for k in old_keys:
        if k in sh:
            return float(sh.get(k) or 0.0)
    return 0.0


def _ch_balance_world():
    from core import balance
    if not balance.needs_reality():
        return None
    sh = balance.shares()
    deficit = max(0.0, balance.TARGET - _balance_axis_value(sh, "reality_share", "world", "reality"))
    raw = min(1.0, deficit / balance.TARGET)
    return (raw, "reality", "regulatory",
            f"reality-axis deficit={deficit:.2f}", {"shares": sh})


def _ch_balance_light():
    from core import balance
    if not balance.needs_light():
        return None
    sh = balance.shares()
    deficit = max(0.0, balance.TARGET - _balance_axis_value(sh, "light_share", "light", "self"))
    raw = min(1.0, deficit / balance.TARGET)
    return (raw, "light", "regulatory",
            f"light-axis deficit={deficit:.2f}", {"shares": sh})


def _ch_boredom(ctx):
    streak = int(ctx.get("bored_streak", 0) or 0)
    if streak <= 0:
        return None
    raw = min(1.0, streak / 3.0)
    # REGULATORY coalition key (§10.1): boredom + low-grounding etc. → "mode_failing", not a topic.
    return (raw, "mode_failing", "regulatory",
            f"bored_streak={streak}", {"bored_streak": streak})


def _ch_self(ctx):
    # The gravity well, represented honestly: the self-concept is injected on ~65% of ticks today.
    # A declared baseline so its win-share is measurable against the G2 < 35% gate.
    return (0.55, "self", "semantic",
            "self-concept default injection (structural gravity well)",
            {"note": "always-on baseline"})


def _ch_wander(ctx):
    # DMN default — rises when the psyche is calm (Gemini Q2: inverse of active tension).
    diss = float(ctx.get("dissonance", 0.0) or 0.0)
    raw = max(0.1, 1.0 - min(1.0, diss))
    return (raw, "wander", "regulatory",
            f"calm→wander (dissonance={diss:.2f})", {"dissonance": round(diss, 3)})


def _ch_flavour(ctx):
    return (0.20, "flavour", "semantic", "low-information flavour seed (room/symbol)", {})


_CHANNELS = {
    "contradiction": lambda ctx: _ch_contradiction(),
    "curiosity":     lambda ctx: _ch_curiosity(),
    "concern":       lambda ctx: _ch_concern(),
    "balance_world": lambda ctx: _ch_balance_world(),
    "balance_light": lambda ctx: _ch_balance_light(),
    "boredom":       _ch_boredom,
    "self":          _ch_self,
    "wander":        _ch_wander,
    "flavour":       _ch_flavour,
}


# ---------------------------------------------------------------------------
# The tick — gather, normalise (§9), select content-blind, LOG. Feeds nothing.
# ---------------------------------------------------------------------------
def shadow_tick(ctx: dict | None = None) -> dict | None:
    """One observe-only allocation pass. ctx carries cheap node-local scalars
    (bored_streak, dissonance, arousal, and optionally 'actual' = what the coin-flips did).
    Returns the telemetry dict (for in-vitro inspection); the live caller ignores it."""
    if not SHADOW_ENABLED:
        return None
    ctx = ctx or {}
    try:
        st = _load_state()
        _migrate_balance_history(st)               # J-1921: once, drops the constant-0.0 balance history
        _migrate_curiosity_history(st)             # J-1935: once, only under CURIOSITY_USE_BACKLOG
        hist   = st.setdefault("history", {})     # channel -> [raw,...]
        streak = st.setdefault("streak", {})      # channel -> consecutive argmax-wins
        cands = []
        for name, fn in _CHANNELS.items():
            try:
                res = fn(ctx)
            except Exception:
                res = None
            if not res:
                continue
            raw, key, kind, justification, lineage = res
            raw = float(max(0.0, raw))
            h = hist.get(name, [])
            cold = len(h) < MIN_HISTORY
            if CONCERN_BYPASS_PERCENTILE and name in TWO_LEVEL_BY_DESIGN and TWO_LEVEL_MAX.get(name):
                # J-1935: a two-level channel scores its declared level, not a rank-within-category artefact
                p_norm = min(1.0, raw / TWO_LEVEL_MAX[name])
            else:
                p_norm = 0.5 if cold else _percentile(h, raw)
            wk = W.get(name, 0.3)
            wstreak = int(streak.get(name, 0) or 0)
            s_final = max(0.0, p_norm * wk * (1.0 - DELTA * wstreak))
            cands.append({
                "channel": name, "binding_key": key, "key_kind": kind,
                "raw": round(raw, 4), "p_norm": round(p_norm, 4), "weight": wk,
                "winner_streak": wstreak, "s_final": round(s_final, 4),
                "cold_start": cold, "justification": justification,
                # full lineage chain (§10.6): raw → percentile → weight → habituation → final
                "lineage": {"raw": round(raw, 4), "p_norm": round(p_norm, 4),
                            "weight": wk, "habituation": round(1.0 - DELTA * wstreak, 4),
                            "s_final": round(s_final, 4), **lineage},
            })

        if not cands:
            return None

        # --- content-blind selection (reads only s_final + keys, never content) ---
        argmax = max(cands, key=lambda c: c["s_final"])
        pick_argmax = argmax["channel"]
        # softmax(τ) sample
        xs = [c["s_final"] for c in cands]
        mx = max(xs) or 1.0
        exps = [math.exp((x - mx) / max(1e-6, TAU)) for x in xs]
        tot = sum(exps) or 1.0
        probs = [e / tot for e in exps]
        r = random.random(); acc = 0.0; pick_soft = cands[0]["channel"]
        for c, p in zip(cands, probs):
            acc += p
            if r <= acc:
                pick_soft = c["channel"]; break

        # --- co-occurrence (§11): which channels are co-active, by key kind ---
        coactive = [c["channel"] for c in cands if c["raw"] >= ACTIVE_FLOOR]
        # would-be SEMANTIC coalition: co-active channels sharing a binding key
        bykey: dict[str, list[str]] = {}
        for c in cands:
            if c["raw"] >= ACTIVE_FLOOR and c["key_kind"] == "semantic":
                bykey.setdefault(c["binding_key"], []).append(c["channel"])
        coalitions = {k: v for k, v in bykey.items() if len(v) >= 2}

        rec = {
            "ts": time.time(),
            "n_candidates": len(cands),
            "n_coactive": len(coactive),
            "coactive": coactive,
            "would_pick_argmax": pick_argmax,
            "would_pick_softmax": pick_soft,
            "semantic_coalitions": coalitions,         # §10.1 measured, not acted on
            "actual": ctx.get("actual"),               # what the coin-flips did, if the node passed it
            "any_cold_start": any(c["cold_start"] for c in cands),
            "candidates": cands,
        }
        try:
            _LOG.parent.mkdir(parents=True, exist_ok=True)
            with _LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # --- update history + habituation (argmax is the canonical "winner" for accounting) ---
        for c in cands:
            h = hist.setdefault(c["channel"], [])
            h.append(c["raw"])
            if len(h) > HIST_K:
                del h[: len(h) - HIST_K]
        for name in _CHANNELS:
            if name == pick_argmax:
                streak[name] = int(streak.get(name, 0) or 0) + 1
            else:
                streak[name] = 0
        _save_state(st)
        return rec
    except Exception:
        # fail-open: the shadow must never disturb the idle loop
        return None


# ---------------------------------------------------------------------------
# Read-only stats for /du-pulse — the §9 Three-Point Currency Health Gate.
# ---------------------------------------------------------------------------
def stats(tail: int = 1000) -> dict:
    """Summarise the recent shadow log for the health gate. Read-only."""
    try:
        if not _LOG.exists():
            return {"records": 0}
        lines = _LOG.read_text(encoding="utf-8").splitlines()[-tail:]
        recs = []
        for ln in lines:
            try:
                recs.append(json.loads(ln))
            except Exception:
                pass
        n = len(recs)
        if not n:
            return {"records": 0}
        from collections import Counter
        win = Counter(r.get("would_pick_argmax") for r in recs)
        coact = [r.get("n_coactive", 0) for r in recs]
        multi = sum(1 for x in coact if x >= 2)
        cold = sum(1 for r in recs if r.get("any_cold_start"))
        coal = sum(1 for r in recs if r.get("semantic_coalitions"))
        # per-channel raw variance (G1 distribution health)
        raws: dict[str, list[float]] = {}
        for r in recs:
            for c in r.get("candidates", []):
                raws.setdefault(c["channel"], []).append(c.get("raw", 0.0))
        def _var(xs):
            if len(xs) < 2:
                return 0.0
            m = sum(xs) / len(xs)
            return sum((x - m) ** 2 for x in xs) / len(xs)
        variance = {k: round(_var(v), 4) for k, v in raws.items()}
        total = sum(win.values()) or 1
        return {
            "records": n,
            "win_share": {k: round(v / total, 3) for k, v in win.most_common()},
            "self_share_G2": round(win.get("self", 0) / total, 3),   # gate: < 0.35
            "multi_channel_rate": round(multi / n, 3),
            "coalition_rate": round(coal / n, 3),
            "cold_start_rate": round(cold / n, 3),
            "raw_variance_G1": variance,                              # gate: each > 0.05
        }
    except Exception as e:
        return {"records": 0, "error": str(e)}

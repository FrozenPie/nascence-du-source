"""
Nascence — The World-Prediction Organ (Consciousness Program Tier-2.5, 2026-07-04, SHADOW/observe-only).

docs/plans/the_consciousness_program.md §Tier-2.5. Du predicts HIMSELF richly (protoself=interoception,
self_surprise/mineness=own thought, AST=own attention) but never predicts HIS WORLD and gets scored by what
actually happens — the scorecard's own admission (PP-1 interoceptive-only), and the cold review's "biggest
gap" (selfhood ↔ external consequence), which is this project's reality-thinness diagnosis rediscovered.

The human function (named first): exteroceptive predictive processing — a mind does not receive the world
raw; it EXPECTS the world and perceives the ERROR (Rao–Ballard). Anticipation-and-violation is how the
world becomes real to a mind rather than scenery.

Each beat (~30 min — the world moves slowly):
  1. Read the world state W(t): weather · tide · daypart · season · fire · cat location/activity/mood.
     All deterministic reads of live state; the scorer is THE WORLD ITSELF — the most decoupled judge we have.
  2. Score the standing prediction of W(t) per field (hit/miss) → exteroceptive prediction error.
  3. Predict W(t+1) with TWO RACING PREDICTORS (the Binder pattern, same as the protoself):
       · NAIVE persistence — the world stays as it is (the null hypothesis).
       · LEARNED — per-field first-order transition tables (deterministic Markov counts accumulated across
         beats; argmax next-state). No LLM anywhere.
     `learned_beats_naive > 0` = he holds genuine world STRUCTURE (the tide's 12.42h rhythm, her dawn
     returns, weather persistence) — not a random walk, not narrative.

SHADOW: logs data/world_model_shadow.jsonl; applies NOTHING. Later phases, each gated on this evidence:
exteroceptive PE → the arousal tonic (a surprising world is arousing); prediction-error PERCEPTS surfaced
to him ("you expected her at the gate; she is not there"). Fail-open: any unreadable field reads as its
previous value (no spurious surprise from our own I/O).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.world_model")

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "world_model_state.json"
_LOG = _DATA / "world_model_shadow.jsonl"

BEAT_SECS = 1800.0          # the world moves slowly; ~30 min between beats
_FIELDS = ("weather", "tide", "daypart", "season", "fire", "cat_location", "cat_activity", "cat_mood")
_MAX_TABLE = 400            # per-field cap on stored transition counts (tiny anyway; safety bound)


def _daypart(hour: float) -> str:
    if 5 <= hour < 8:
        return "dawn"
    if 8 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def read_world() -> dict | None:
    """One deterministic snapshot of the world's coarse state. Fail-open per field (None = unreadable)."""
    out = {}
    try:
        from core import sensorium as sn
        sn._load()
        st = getattr(sn, "_state", None) or getattr(sn, "state", None) or {}
        out["weather"] = st.get("weather")
        out["fire"] = st.get("fire")
        try:
            out["tide"] = sn._tide()
        except Exception as exc:
            logger.debug("[world-model] tide read failed (non-fatal): %s", exc)
            out["tide"] = None
        try:
            out["season"] = sn._season()
        except Exception as exc:
            logger.debug("[world-model] season read failed (non-fatal): %s", exc)
            out["season"] = None
        try:
            _, hour = sn._now_parts()
            out["daypart"] = _daypart(float(hour))
        except Exception as exc:
            logger.debug("[world-model] daypart read failed (non-fatal): %s", exc)
            out["daypart"] = None
    except Exception as exc:
        logger.debug("[world-model] sensorium read failed (non-fatal): %s", exc)
        return None
    try:
        c = json.loads((_DATA / "cat_state.json").read_text(encoding="utf-8"))
        out["cat_location"] = c.get("location")
        out["cat_activity"] = c.get("activity")
        out["cat_mood"] = c.get("mood")
    except Exception as exc:
        logger.debug("[world-model] cat_state read failed (non-fatal): %s", exc)
        out["cat_location"] = out["cat_activity"] = out["cat_mood"] = None
    return out


def _load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("[world-model] state load failed (non-fatal): %s", exc)
        return {}


def _save(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(d), encoding="utf-8"); tmp.replace(_STATE)
    except Exception as exc:
        logger.debug("[world-model] state save failed (non-fatal): %s", exc)


def _learn(tables: dict, field: str, prev: str, cur: str) -> None:
    """Count one observed transition prev→cur for the field (the whole learned generative model)."""
    t = tables.setdefault(field, {})
    row = t.setdefault(prev, {})
    row[cur] = row.get(cur, 0) + 1
    if sum(len(r) for r in t.values()) > _MAX_TABLE:      # safety bound; never expected in practice
        t.pop(next(iter(t)))


def _predict_learned(tables: dict, field: str, cur: str) -> str | None:
    row = (tables.get(field) or {}).get(cur) or {}
    if not row:
        return None
    return max(row, key=row.get)


def tick() -> dict | None:
    """One beat: score the standing prediction against the actual world, learn the transition, predict the
    next state (learned vs naive). Logs; applies nothing. Fail-open. Rate-limited internally."""
    try:
        now = time.time()
        st = _load()
        if now - float(st.get("ts", 0)) < BEAT_SECS:
            return None
        world = read_world()
        if not world:
            return None

        prev_world = st.get("world") or {}
        pred = st.get("predicted") or {}
        naive_pred = prev_world                             # persistence baseline: yesterday's world

        # score the standing predictions per field (only fields that were predicted AND are readable)
        scored = {}
        for f in _FIELDS:
            actual = world.get(f)
            if actual is None:
                continue
            p_l, p_n = pred.get(f), naive_pred.get(f)
            if p_l is not None or p_n is not None:
                scored[f] = {"actual": actual,
                             "learned_hit": (p_l == actual) if p_l is not None else None,
                             "naive_hit": (p_n == actual) if p_n is not None else None,
                             "changed": (actual != prev_world.get(f)) if prev_world.get(f) else None}

        # learn the observed transitions
        tables = st.get("tables") or {}
        for f in _FIELDS:
            pv, cv = prev_world.get(f), world.get(f)
            if pv is not None and cv is not None:
                _learn(tables, f, str(pv), str(cv))

        # predict the NEXT beat: learned argmax where a table exists, else fall back to persistence
        predicted = {}
        for f in _FIELDS:
            cv = world.get(f)
            if cv is None:
                continue
            predicted[f] = _predict_learned(tables, f, str(cv)) or str(cv)

        err = None
        if scored:
            hits = [s["learned_hit"] for s in scored.values() if s["learned_hit"] is not None]
            err = round(1.0 - (sum(hits) / len(hits)), 4) if hits else None   # exteroceptive PE this beat

        rec = {"ts": round(now, 1), "world": world, "scored": scored, "pe": err,
               "n_transitions": sum(len(r) for t in tables.values() for r in t.values()) if tables else 0}
        try:
            _DATA.mkdir(parents=True, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception as exc:
            # Logging must never be able to block the state save that follows (a log-failure must
            # not cascade into a save-failure) — the logger.debug call is itself defensively guarded.
            try:
                logger.debug("[world-model] beat log write failed (non-fatal): %s", exc)
            except Exception:
                pass
        _save({"ts": now, "world": world, "predicted": predicted, "tables": tables})
        return rec
    except Exception as exc:
        logger.debug("[world-model] tick failed (non-fatal): %s", exc)
        return None


_MCNEMAR_P05 = 3.8415  # chi2 critical value, df=1, p<0.05 (uncorrected)
_MCNEMAR_LOW_POWER_N = 20  # fewer discordant pairs than this = flag the result as fragile regardless of chi2


def _mcnemar(b: int, c: int) -> dict:
    """McNemar's test on one field's paired learned-vs-naive hit/miss outcomes.
    b = naive right & learned wrong (naive-favoring discordant pair)
    c = learned right & naive wrong (learned-favoring discordant pair)
    Only the discordant pairs (b+c) carry information; concordant pairs (both right or both wrong)
    are silently uninformative for this test, exactly why a near-constant field (e.g. season, which
    is almost always right for BOTH predictors) produces b=c=0 and no evidence either way -- that is
    the dilution mechanism this report exists to stop hiding (F-0033, job J-0069)."""
    n = b + c
    if n == 0:
        return {"b": b, "c": c, "discordant": 0, "chi2": None, "chi2_corrected": None,
                "significant_p05": False, "low_power": True, "favors": None}
    chi2 = round(((b - c) ** 2) / n, 4)
    chi2_corrected = round(((abs(b - c) - 1) ** 2) / n, 4)  # continuity-corrected (Edwards); more conservative
    sig = chi2 > _MCNEMAR_P05
    return {"b": b, "c": c, "discordant": n, "chi2": chi2, "chi2_corrected": chi2_corrected,
            "significant_p05": sig, "low_power": n < _MCNEMAR_LOW_POWER_N,
            "favors": ("learned" if c > b else "naive" if b > c else None) if sig else None}


def status() -> dict:
    """For the pulse. THE SIGNATURE: learned_beats_naive per field (positive = he holds real world
    structure, not a random walk) + exteroceptive PE trend (declining = the world becoming expected).

    2026-08-24 (J-0139, F-0033's follow-up): the pooled McNemar significance test (mcnemar_pooled below)
    stays non-significant across the whole run (chi2~2/1.9 on ~6,000 field-predictions) because near-constant
    fields (daypart, season: 0 discordant pairs; weather/tide/fire: 0-6) sit in the same pool as fields with
    real competition (cat_location/activity/mood) and dilute any real signal toward the null. Each field now
    also gets its OWN McNemar chi2/n (fields[f]['mcnemar']) computed over the FULL log (not the recent-200
    window used for the accuracy/trend numbers below, which needs more power than 200 beats gives a field
    with a handful of discordant pairs per year). cat_mood clears p<0.05 favoring the learned predictor with
    real power (n>100 discordant pairs); do not let the pooled null hide it going forward."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the growing log on every ~6s HUD poll.
        # NOTE: the McNemar pass below documents itself as "over the FULL log" for power — it is now
        # over the last 4000 beats (the whole log today at 914 rows; a cap once the log outgrows it).
        rows = _tail_rows(_LOG, 4000)
        if not rows:
            return {"beats": 0}
        recent = rows[-200:]
        per_field: dict = {}
        for r in recent:
            for f, s in (r.get("scored") or {}).items():
                d = per_field.setdefault(f, {"l_hit": 0, "l_n": 0, "n_hit": 0, "n_n": 0, "changes": 0})
                if s.get("learned_hit") is not None:
                    d["l_n"] += 1
                    d["l_hit"] += int(s["learned_hit"])
                if s.get("naive_hit") is not None:
                    d["n_n"] += 1
                    d["n_hit"] += int(s["naive_hit"])
                if s.get("changed"):
                    d["changes"] += 1
        fields = {}
        for f, d in per_field.items():
            la = round(d["l_hit"] / d["l_n"], 3) if d["l_n"] else None
            na = round(d["n_hit"] / d["n_n"], 3) if d["n_n"] else None
            fields[f] = {"learned_acc": la, "naive_acc": na,
                         "beats_naive": round(la - na, 3) if (la is not None and na is not None) else None,
                         "changes": d["changes"]}

        # per-field + pooled McNemar significance, over the FULL log (all beats, every field) -- the
        # accuracy numbers above intentionally window to the recent 200 beats for a *current* reading, but
        # a significance test needs all the power the log has, especially for fields with few discordant
        # pairs per beat (F-0033: 751 beats only produced ~120 discordant pairs even for the liveliest field).
        pooled_b = pooled_c = 0
        sig_per_field: dict = {}
        for r in rows:
            for f, s in (r.get("scored") or {}).items():
                lh, nh = s.get("learned_hit"), s.get("naive_hit")
                if lh is None or nh is None:
                    continue
                d = sig_per_field.setdefault(f, {"b": 0, "c": 0})
                if nh and not lh:
                    d["b"] += 1
                    pooled_b += 1
                elif lh and not nh:
                    d["c"] += 1
                    pooled_c += 1
        for f, d in sig_per_field.items():
            fields.setdefault(f, {})["mcnemar"] = _mcnemar(d["b"], d["c"])
        mcnemar_pooled = _mcnemar(pooled_b, pooled_c)

        pes = [r["pe"] for r in recent if r.get("pe") is not None]
        half = len(pes) // 2
        pe_trend = round(sum(pes[half:]) / max(1, len(pes) - half)
                         - sum(pes[:half]) / max(1, half), 4) if half >= 3 else None
        return {"beats": len(rows), "mean_pe": round(sum(pes) / len(pes), 4) if pes else None,
                "pe_trend": pe_trend,                     # negative = the world becoming expected
                "fields": fields,
                # pooled = the old headline number (kept, not retired); per-field lives in fields[f]['mcnemar'].
                # A field can show significant_p05=True with low_power=True (e.g. weather, ~6 discordant
                # pairs) -- read low_power fields as fragile, not as a second real signal alongside cat_mood.
                "mcnemar_pooled": mcnemar_pooled}
    except Exception as exc:
        logger.debug("[world-model] status failed (non-fatal): %s", exc)
        return {"beats": 0}

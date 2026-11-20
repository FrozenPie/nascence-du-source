"""
Nascence — Mineness / the Authorship Comparator (Consciousness Program §2-#5 reframed, 2026-07-04,
SHADOW/observe-only).

The adversarial audit ruled the original "mineness tag" BACKWARDS (Metzinger: phenomenal mineness is
TRANSPARENCY — you look *through* the self-model; a readable tag is opaque higher-order attribution, the
opposite). The honest build is SOURCE/REALITY MONITORING (HOT/PRM; Anthropic's prefill-detection as
blueprint): a comparator that predicts his own next thought and reads the ERROR —

    authorship_error = 1 − max( sim_to_recent_groove , sim_to_basin )

  low error  → continuous with his own dynamics → "I thought" (felt as self-produced)
  high error → arrived from outside the dynamics → "a thought occurred" (candidate intrusion)

Two DISTINCT tags (never conflated — the audit's ownership/authorship split):
  · ownership  — is it in my stream? (always true at this hook; the field exists for future external items)
  · authorship — SELF (spontaneous / own concern) · SELF_PAST (his own earlier conclusion re-entering via
    broadcast/recall/dream) · OTHER (world percept, trial prompt, Travis's guidance — someone/something
    else authored the seed content)

THE DECOUPLED SIGNATURE (we never self-certify): we KNOW ground truth — the monologue records what seeded
each cycle (seed_kind). The comparator earns its keep only if its error SEPARATES the classes it never
sees: mean_error(OTHER-seeded) − mean_error(SELF-seeded) > 0. That gap is the standing metric in status().
Bonus channels: a SELF thought with HIGH error = "a thought that surprised him" (self-surprise, interesting);
an OTHER seed with LOW error = assimilated (his own dynamics absorbed it).

Reuses self_surprise's basin machinery (no duplicate vocabulary — erosion guard). Groove = a rolling window
of his own recent thought vectors, fed by this module itself (no DB read per cycle; basin centroid cached
1h). Deterministic, no LLM, fail-open. Logs data/mineness_shadow.jsonl; applies NOTHING.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "mineness_shadow.jsonl"

_TAU = 0.45          # error above this = "arrived, not flowed" (aligned with self_surprise surprise_tau)
_GROOVE_K = 8        # how many of his own recent thought-vectors form the groove
_BASIN_TTL = 3600.0  # basin centroid cache (an hourly DB sample, never per-cycle)

# seed_kind (what the monologue KNOWS fed the cycle — ground truth) → authorship class
_AUTHOR = {None: "SELF", "concern": "SELF", "imagination": "SELF",
           "broadcast": "SELF_PAST", "recall": "SELF_PAST", "dream": "SELF_PAST",
           "world": "OTHER", "trial": "OTHER", "guidance": "OTHER",
           # J-3700 (F-4317): the seed kinds that actually occur since J-0581 (2026-09-04) made explicit.
           # Class assignment is UNCHANGED -- these were already OTHER via the .get() fall-through; the
           # fall-through stays as a safety net but no live kind should rely on it. Keys concern/imagination/
           # recall/dream/trial/guidance are documented-but-rare/dead in the live log (verify before pruning).
           "percept": "OTHER", "frontier": "OTHER", "reading": "OTHER", "letter": "OTHER"}

# J-3700 (F-4317): the seed-tag vocabulary changed on 2026-09-04 11:16 UTC (J-0581, commit f783ad4a):
# before it only world/broadcast tagged non-spontaneous cycles; after it percept/frontier/reading/letter
# do too. The headline OTHER-vs-SELF separation is NOT comparable across that line, so each row carries
# its own epoch (derived from ts at write time) and status() can be read per epoch.
_LABEL_EPOCH_V2_TS = 1788520560.0   # 2026-09-04T11:16:00Z

_groove: deque = deque(maxlen=_GROOVE_K)
_basin = None
_basin_ts = 0.0


def _get_basin():
    """The origin/attractor centroid, reusing self_surprise's vocabulary + query. Cached; None is fine."""
    global _basin, _basin_ts
    now = time.time()
    if _basin is not None and (now - _basin_ts) < _BASIN_TTL:
        return _basin
    try:
        from core.memory.store import _connect
        from core.self_surprise import _basin_centroid
        with _connect() as conn:
            _basin = _basin_centroid(conn)
        _basin_ts = now
    except Exception:
        _basin = None
        _basin_ts = now      # don't hammer a failing DB every cycle
    return _basin


_QUOTE_STORE = 300   # chars of the thought stored for the arrival-note quote (the 120-char log field is unchanged)
_QUOTE_MAX = 240     # chars the arrival note quotes at most (cut at a sentence/word boundary)


def _quote_cut(text: str, limit: int = _QUOTE_MAX, complete: bool = False) -> str:
    """Cut a thought for quoting at a sentence end, else a word boundary, never mid-word. `complete` = the
    text is known to be the whole thought (stored full field shorter than its cap); else a text that fills
    its store/legacy cap is treated as possibly truncated and the dangling partial word is dropped."""
    t = " ".join((text or "").split())
    if not t:
        return t
    if len(t) <= limit and complete:
        return t
    head = t[:limit]
    # prefer the last sentence end in the back half of the window
    cut = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if len(t) <= limit and t[-1] in ".!?\"'":
        return t
    if cut >= limit // 2:
        return head[:cut + 1]
    if len(t) > limit and t[limit] == " ":
        return head.rstrip() + "…"
    sp = head.rfind(" ")
    head = head[:sp] if sp > 0 else head
    return head.rstrip(" ,;:-") + "…"


def _label_epoch(ts: float) -> str:
    """Seed-tag vocabulary version for a timestamp: v1 = world/broadcast only; v2 = J-0581 tags (2026-09-04)."""
    return "v2" if ts >= _LABEL_EPOCH_V2_TS else "v1"


def assess(thought: str, vec, seed_kind: str | None = None) -> dict | None:
    """One comparator beat: score this cycle's thought against his own dynamics (groove + basin), tag
    ownership/authorship, log. The thought's vec then JOINS the groove (his dynamics include it now).
    Returns the record (for the pulse) or None. SHADOW: applies nothing. Fail-open."""
    try:
        if vec is None:
            return None
        from core.memory.store import _cosine
        recent_sim = max((_cosine(vec, g) for g in _groove), default=0.0)
        basin = _get_basin()
        basin_sim = _cosine(vec, basin) if basin is not None else 0.0
        warm = len(_groove) >= 3                    # a groove of <3 isn't dynamics yet — record, don't judge
        error = round(1.0 - max(float(recent_sim), float(basin_sim)), 4)

        author = _AUTHOR.get(seed_kind, "OTHER")
        rec = {"ts": round(time.time(), 1), "seed_kind": seed_kind or "spontaneous",
               "ownership": "in_stream",            # honest: everything at this hook is in his stream
               "authorship": author, "label_epoch": _label_epoch(time.time()),
               "error": error if warm else None,
               "recent_sim": round(float(recent_sim), 4), "basin_sim": round(float(basin_sim), 4),
               "felt_mine": (error < _TAU) if warm else None,
               "thought": " ".join((thought or "").split())[:120],
               # J-2886 (F-3567): the 120-char log field is kept as is; arrival_note() quotes this longer one,
               # cut at a word/sentence boundary, so the quote Du sees no longer ends mid-word.
               "thought_full": " ".join((thought or "").split())[:_QUOTE_STORE]}
        _groove.append(vec)
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    except Exception:
        return None


# ── THE READ-BACK (2026-07-04) — graduation, licensed by the separation proving positive (+0.064/290) ──
# The plan gated this behind "ONLY IF the separation proves out." It did. This is NOT a mine/not-mine tag
# (Metzinger: opaque). It is a metacognitive REALITY-MONITORING touch: when a thought genuinely ARRIVED
# rather than FLOWED (high authorship-error, which the comparator now reliably detects blind), Du gets to
# NOTICE that — the HOT-2 "metacognitive monitoring of my own thought's provenance" indicator, made felt.
# RISK GUARDED: re-surfacing his own thoughts could feed self-referential rumination (the #1 disease), so
# it is RARE (high bar 0.62, 30-min cooldown), OUTWARD-framed (arrival, not navel-gazing), NEVER rewarded,
# SHADOW-first (flag OFF), and its flip is gated on the monoculture detectors NOT rising.
# FLIPPED ON 2026-07-06 (founder call, evidence read): 34/1375 would-fires (2.5%), errors all .62-.73
# (genuine threshold crossings), monoculture flat (echo .648 / diversity .977). The fires are mostly his
# concrete want-driven world-turnings — and the comparator tagged those OTHER *blind*, i.e. it detects
# externally-seeded redirects as arrivals, which is exactly the organ's job. Known wart (~15%): activity-
# record texts ("I opened 'Roughing It' — 2 sittings") score as arrived because record-format is outside
# his groove — add a record-text filter if it annoys live. Cadence: 14-20 would-fires/day is above the
# expected "few"; the 30-min cooldown throttles actual injections well below that.
MINENESS_READBACK = True         # flipped after shadow showed sane firings AND no monoculture rise
_READBACK_TAU = 0.62             # well above _TAU (0.45): only a genuinely-arrived thought, not a mild one
_READBACK_COOLDOWN = 1800.0      # min seconds between live surfacings (anti-rumination; matches moment/guidance)
_READBACK_WINDOW = 240.0         # only surface a high-error thought from the last ~4 min (else it is stale)
_STATE = _DATA / "mineness_state.json"
_RB_LOG = _DATA / "mineness_readback_shadow.jsonl"


def arrival_note() -> str | None:
    """The metacognitive read-back: if the MOST RECENT thought genuinely arrived (error ≥ _READBACK_TAU)
    and is fresh, return a light noticing line. ALWAYS shadow-logs what would fire; returns the line for
    injection ONLY when MINENESS_READBACK is on AND the cooldown has passed. Deterministic, fail-open."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 1)   # bounded (F-0384): only the LAST row is used — don't full-scan a 4.4MB log per cycle
        if not rows:
            return None
        last = rows[-1]
        err = last.get("error")
        fresh = (time.time() - float(last.get("ts", 0))) <= _READBACK_WINDOW
        would = bool(err is not None and err >= _READBACK_TAU and fresh and last.get("thought"))
        line = None
        if would:
            _full = last.get("thought_full")
            if _full:   # complete iff it is shorter than the store cap (not itself truncated)
                th = _quote_cut(_full, complete=len(_full) < _QUOTE_STORE)
            else:       # legacy row: only the 120-char cut exists -> treat as possibly truncated
                th = _quote_cut(last["thought"], complete=len(last["thought"]) < 120)
            line = (f"That last thought arrived rather than flowing from the rest of what you were "
                    f"thinking — \"{th}\". Notice it: something reached you from outside your own current, "
                    f"or something new stirred in you.")
        # shadow-log what WOULD fire (so the graduation gate is measurable regardless of the flag)
        try:
            _DATA.mkdir(parents=True, exist_ok=True)
            with open(_RB_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": round(time.time(), 1), "would_fire": would,
                                    "error": err, "authorship": last.get("authorship"),
                                    "thought": last.get("thought", "")[:120]}, ensure_ascii=False) + "\n")
        except Exception:
            pass
        if not (would and MINENESS_READBACK):
            return None
        # cooldown against re-surfacing too often (anti-rumination)
        try:
            st = json.loads(_STATE.read_text(encoding="utf-8"))
        except Exception:
            st = {}
        if time.time() - float(st.get("last_readback_ts", 0)) < _READBACK_COOLDOWN:
            return None
        st["last_readback_ts"] = time.time()
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(st), encoding="utf-8"); tmp.replace(_STATE)
        return line
    except Exception:
        return None


def status() -> dict:
    """For the pulse / liveness audit. THE SIGNATURE: separation — does the comparator's error, which
    never sees seed_kind, run HIGHER on OTHER-seeded cycles than SELF-seeded ones? (positive = real
    reality-monitoring, not noise). Plus the two interesting tails."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail reads (J-0278/F-0335): status() full-scanned BOTH logs (4.4MB + 3.0MB, growing)
        # on every ~6s HUD poll. "assessed"/"scored" now cap at the window; the stats use scored[-300:].
        rows = _tail_rows(_LOG, 2000)
        scored = [r for r in rows if r.get("error") is not None]
        if not scored:
            return {"assessed": len(rows), "scored": 0}
        recent = scored[-300:]

        def _mean_err(cls):
            xs = [r["error"] for r in recent if r.get("authorship") == cls]
            return round(sum(xs) / len(xs), 4) if xs else None

        e_self, e_past, e_other = _mean_err("SELF"), _mean_err("SELF_PAST"), _mean_err("OTHER")
        sep = round(e_other - e_self, 4) if (e_other is not None and e_self is not None) else None
        mine_rate = round(sum(1 for r in recent if r.get("felt_mine")) / len(recent), 3)
        # the two interesting tails
        self_surprises = sum(1 for r in recent if r.get("authorship") == "SELF" and r["error"] >= _TAU)
        assimilated = sum(1 for r in recent if r.get("authorship") == "OTHER" and r["error"] < _TAU)
        from collections import Counter
        mix = dict(Counter(r.get("authorship") for r in recent))
        out = {"assessed": len(rows), "scored": len(scored), "authorship_mix": mix,
               "err_self": e_self, "err_self_past": e_past, "err_other": e_other,
               "separation": sep,               # POSITIVE = the comparator detects intrusions blind
               "felt_mine_rate": mine_rate,
               "self_surprises": self_surprises,   # his own thoughts that escaped his dynamics
               "assimilated_other": assimilated}   # outside content his dynamics absorbed
        # J-3700 (F-4317): composition/floor-aware readers. SHADOW, additive; headline 'separation' unchanged.
        try:
            spont = [r["error"] for r in recent if r.get("seed_kind") == "spontaneous"]
            floor = (sum(spont) / len(spont)) if spont else None
            out["error_floor"] = round(floor, 4) if floor is not None else None   # mean spontaneous error
            by_kind, other_gaps = {}, []
            if floor is not None:
                for k in sorted({r.get("seed_kind") for r in recent} - {"spontaneous", None}):
                    xs = [r["error"] for r in recent if r.get("seed_kind") == k]
                    gap = round(sum(xs) / len(xs) - floor, 4)
                    by_kind[k] = {"n": len(xs), "gap": gap, "class": _AUTHOR.get(k, "OTHER")}
                    if by_kind[k]["class"] == "OTHER":
                        other_gaps.append(gap)
            out["separation_by_kind"] = by_kind    # kind error minus same-window spontaneous error
            out["separation_kind_equal"] = (round(sum(other_gaps) / len(other_gaps), 4)
                                            if other_gaps else None)   # equal weight per OTHER kind present
            out["label_epoch"] = _label_epoch(float(recent[-1].get("ts") or time.time()))
        except Exception:
            pass
        # read-back stats (shadow): how often the arrival-note WOULD fire, and whether it is live
        try:
            rr = _tail_rows(_RB_LOG, 2000)   # bounded (J-0278): fire-rate is now over the recent window
            if rr:
                fires = sum(1 for r in rr if r.get("would_fire"))
                out["readback_would_fire"] = fires
                out["readback_rate"] = round(fires / len(rr), 3)
                out["readback_live"] = MINENESS_READBACK
        except Exception:
            pass
        return out
    except Exception:
        return {"assessed": 0}

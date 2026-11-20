"""
core/pulse_shadow.py — Pulse / Lifecycle Manager, Phase 0 (SHADOW / observe-only).

docs/staged/pulse_manager_wiring_plan.md (v6). The measurement layer the four auditor rounds converged on building
FIRST. Each idle tick it records what a wired LIFECYCLE manager WOULD do — which source would hold the contended
hot-GPU lease (RUNNING), what would run free in BACKGROUND, what would be SUSPENDED — plus the real per-lane
CONTENTION (was a slow/PROTECTED source like T4 ready but blocked by a fast burst holding the lease?), and the
signals for the lull census and the T4-canary safety gate. It FEEDS NOTHING. Fail-open throughout.

Content-blind invariant (§12.1): this logger reads only DECLARED, NON-SEMANTIC signals — lane occupancy,
capacity, time-on-task, each source's own cheap progress flag + horizon prior. It never reads thought content
and never judges worth. The horizon labels are an INITIAL PRIOR (§2.4), to be overwritten by the empirical
payoff-delay census; nothing here gates behaviour.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

SHADOW_ENABLED = True

_DATA  = Path(__file__).parent.parent / "data"
_LOG   = _DATA / "logs" / "pulse_shadow.jsonl"
_STATE = _DATA / "pulse_shadow_state.json"

IDLE_SECS = 60.0   # person considered "away" after this many seconds with no input

# Horizon priors (§2.4 — INITIAL prior, to be overwritten by the empirical payoff-delay census).
# fast  = local progress reliable → burstable on the hot lane.
# slow  = PROTECTED → never progress-gated (T4 is the canary).
# floor = DMN idle self-reflection → never accelerated.
HORIZON = {"reading": "fast", "math": "fast", "study": "fast",
           "frontier": "slow", "t4": "slow",
           "idle_thought": "floor"}
LANE    = {"reading": "hot", "math": "hot", "study": "hot", "frontier": "hot", "t4": "hot",
           "idle_thought": "background"}
# fast-source priority for the would-be hot-lane lease (declared, content-blind)
FAST_PRIORITY = {"math": 3, "reading": 2, "study": 1}


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        _STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        tmp.replace(_STATE)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Per-source cheap readers → (present, progressing, detail). All fail-open.
# present   = this source has work available right now
# progressing = a cheap, non-semantic progress flag (only MEANINGFUL for fast sources; logged for all)
# ---------------------------------------------------------------------------
def _src_reading():
    from core import reading
    book = reading.current_book()
    st = reading._load_state() if hasattr(reading, "_load_state") else {}
    rec = st.get(str(book), {}) if isinstance(st, dict) else {}
    pct = float(rec.get("pct", 0.0) or 0.0)
    present = pct < 99.5                       # a book in progress
    return present, present, f"{book.stem[:22]} {pct:.0f}%"


def _src_math():
    from core import math_drill
    s = math_drill.status()
    present = math_drill.due()
    progressing = int(s.get("streak", 0) or 0) > 0
    return present, progressing, f"L{s.get('level')} streak{s.get('streak')} {s.get('today_done')}/{s.get('target')}"


def _src_study():
    # study-lookup rides reading/school; treat as present during school time
    try:
        from core import school
        return bool(school.is_school_time()), True, "school" if school.is_school_time() else "—"
    except Exception:
        return False, False, "—"


def _src_frontier():
    from core import frontier
    n = frontier.open_count()
    findings = sum(1 for q in frontier.top_open(8) if q.get("has_finding"))
    present = n > 0
    return present, findings > 0, f"open {n} / findings {findings}"   # progress shown but NOT gated (slow/protected)


def _src_t4():
    # T4 readiness = a high-chronic-mass tension exists; opportunity = its subconscious pass cadence.
    top = 0.0
    try:
        from core import store_persist as _sp  # J-2417 (F-3117): cached, read-only
        d = _sp.load_json_cached(_DATA / "subconscious_state.json")
        tensions = d.get("tensions") or []
        if tensions:
            top = max(float(t.get("chronic_mass", 0.0) or 0.0) for t in tensions)
        ready = top >= 2.0
        return ready, False, f"chronic {top:.1f} authored×{d.get('self_authoring_count', 0)}"
    except Exception:
        return False, False, "—"


def _src_idle():
    return True, False, "DMN floor"


_SOURCES = {"reading": _src_reading, "math": _src_math, "study": _src_study,
            "frontier": _src_frontier, "t4": _src_t4, "idle_thought": _src_idle}


def _capacity(ctx: dict) -> dict:
    """Hard-gate capacity (§2.3): machine (hot GPU free) AND person-presence. Content-blind."""
    idle_secs = float(ctx.get("idle_secs", 9e9) or 9e9)
    person_away = idle_secs >= IDLE_SECS
    gpu_util = None
    try:
        from core import exogenous
        r = exogenous.read_gpu()
        if getattr(r, "ok", True):
            # parse "util NN%" out of the human string, best-effort
            import re
            m = re.search(r"util (\d+)%", getattr(r, "detail", "") or "")
            if m:
                gpu_util = int(m.group(1))
    except Exception:
        pass
    # hot lane is "free to lease" only when the person is away (a user turn owns the hot lane) and,
    # if we can read it, the GPU isn't already busy serving something.
    hot_free = person_away and (gpu_util is None or gpu_util < 50)
    return {"person_away": person_away, "gpu_util": gpu_util, "hot_free": hot_free}


def observe(ctx: dict | None = None) -> dict | None:
    """One observe-only lifecycle pass. Logs what a wired manager WOULD do + contention. Feeds nothing."""
    if not SHADOW_ENABLED:
        return None
    ctx = ctx or {}
    try:
        cap = _capacity(ctx)
        srcs = {}
        for name, fn in _SOURCES.items():
            try:
                present, progressing, detail = fn()
            except Exception:
                present, progressing, detail = False, False, "err"
            srcs[name] = {"present": present, "progressing": progressing,
                          "horizon": HORIZON.get(name, "?"), "lane": LANE.get(name, "?"),
                          "detail": detail}

        # Who would hold the contended hot lane (RUNNING)? Highest-priority FAST source that is present +
        # progressing, only if the hot lane is free. (Content-blind: declared priority over declared flags.)
        fast_ready = [n for n, s in srcs.items()
                      if s["horizon"] == "fast" and s["present"] and s["progressing"]]
        would_run = None
        if cap["hot_free"] and fast_ready:
            would_run = max(fast_ready, key=lambda n: FAST_PRIORITY.get(n, 0))

        # Slow/PROTECTED sources that are ready (want the hot lane for a commit/pursuit).
        slow_ready = [n for n, s in srcs.items() if s["horizon"] == "slow" and s["present"]]
        # CONTENTION (the core Phase-0 measurement): a slow/protected source is ready but a fast burst
        # would hold the hot lane → the protected source is BLOCKED. T4-blocked is the canary event.
        contended = bool(would_run and slow_ready and LANE.get(would_run) == "hot")
        t4_blocked = contended and "t4" in slow_ready

        # Lifecycle snapshot
        running = would_run
        background = [n for n, s in srcs.items() if s["present"] and s["lane"] == "background"]
        suspended = [n for n, s in srcs.items()
                     if s["present"] and s["lane"] == "hot" and n != running]

        # T4-canary trend: track its pass count so we can later check Δ opportunity ≥ 0.
        t4_authored = None
        try:
            from core import store_persist as _sp  # J-2417 (F-3117): cached, read-only
            d = _sp.load_json_cached(_DATA / "subconscious_state.json")
            t4_authored = int(d.get("self_authoring_count", 0) or 0)
        except Exception:
            pass

        rec = {
            "ts": time.time(),
            "capacity": cap,
            "would_run": running,                 # who'd hold the hot-lane lease (None = nothing/idle or user)
            "fast_ready": fast_ready,
            "slow_ready": slow_ready,
            "contended": contended,               # a protected source blocked by a fast burst
            "t4_blocked": t4_blocked,             # the canary contention event
            "background": background,
            "suspended": suspended,
            "t4_authored_count": t4_authored,     # canary opportunity trend
            "sources": srcs,
        }
        try:
            _LOG.parent.mkdir(parents=True, exist_ok=True)
            with _LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return rec
    except Exception:
        return None   # fail-open: never disturb the idle loop


# ---------------------------------------------------------------------------
# Read-only analysis for /du-pulse.
# ---------------------------------------------------------------------------
def lull_census(hours: float = 8.0) -> dict:
    """Classify gaps in self-firing cognition as sleep / conversation / genuine-stall (the real wasted idle)."""
    try:
        import sqlite3
        db = _DATA / "memory" / "nascence.db"
        con = sqlite3.connect(str(db))
        now = time.time(); cut = now - hours * 3600
        IDLE = ("inner_thought", "reading", "dream", "study", "understanding", "research", "subconscious_synthesis")
        q = ("SELECT timestamp FROM memory_fragments WHERE origin IN (%s) AND timestamp>? ORDER BY timestamp"
             % ",".join("?" * len(IDLE)))
        ts = [r[0] for r in con.execute(q, (*IDLE, cut)).fetchall()]
        # dreams = sleep markers; affect cycles = conversation markers
        dreams = [r[0] for r in con.execute(
            "SELECT timestamp FROM memory_fragments WHERE origin='dream' AND timestamp>?", (cut,)).fetchall()]
        con.close()
        if len(ts) < 3:
            return {"events": len(ts)}
        acts = [ts[0]]
        for t in ts[1:]:
            if t - acts[-1] > 10:
                acts.append(t)
        gaps = [(acts[i + 1] - acts[i], acts[i], acts[i + 1]) for i in range(len(acts) - 1)]
        lulls = [(g, a, b) for g, a, b in gaps if g > 300]
        def is_sleep(a, b):
            return any(a - 120 <= d <= b + 120 for d in dreams)
        sleep_t = sum(g for g, a, b in lulls if is_sleep(a, b))
        stall_t = sum(g for g, a, b in lulls if not is_sleep(a, b))
        span = acts[-1] - acts[0]
        return {"events": len(acts), "span_min": round(span / 60), "n_lulls": len(lulls),
                "sleep_min": round(sleep_t / 60), "genuine_stall_min": round(stall_t / 60),
                "longest_min": round(max((g for g, _, _ in gaps), default=0) / 60),
                "stall_share": round(stall_t / span, 3) if span else 0.0}
    except Exception as e:
        return {"error": str(e)}


def stats(tail: int = 2000) -> dict:
    """Shadow-log summary for the health view: contention, T4-blocked rate, fast-availability, canary trend."""
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
        contended = sum(1 for r in recs if r.get("contended"))
        t4_blocked = sum(1 for r in recs if r.get("t4_blocked"))
        fast_avail = sum(1 for r in recs if r.get("fast_ready"))
        hot_free = sum(1 for r in recs if (r.get("capacity") or {}).get("hot_free"))
        from collections import Counter
        runwin = Counter(r.get("would_run") for r in recs if r.get("would_run"))
        t4c = [r.get("t4_authored_count") for r in recs if r.get("t4_authored_count") is not None]
        t4_delta = (t4c[-1] - t4c[0]) if len(t4c) >= 2 else None
        return {"records": n,
                "would_run_share": {k: round(v / n, 3) for k, v in runwin.most_common()},
                "fast_available_rate": round(fast_avail / n, 3),
                "hot_free_rate": round(hot_free / n, 3),
                "contention_rate": round(contended / n, 3),
                "t4_blocked_rate": round(t4_blocked / n, 3),          # the canary contention
                "t4_authored_delta": t4_delta}                        # canary opportunity trend (≥0 wanted)
    except Exception as e:
        return {"records": 0, "error": str(e)}

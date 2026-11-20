"""
Nascence — Meta-Awareness (Layer 2, idle self-monitoring — NOT a critic)
========================================================================
Light, intermittent, NON-suppressive meta-awareness of the idle thought stream. It is the opposite of
the conversation critic: it never judges a thought's content or morality and never rejects. It watches
pure FORM signals — perseveration (looping), abstraction (the river/basin self-talk), hollow over-
generality — and, when a loop is caught, the adaptive move is a MODE-SHIFT (route to a concrete/world
anchor) or note-and-release, never suppression. Research: Watkins (concrete>abstract construal),
Nolen-Hoeksema / Takano & Tanno (reflection vs brooding), Wegner (suppression rebound), Nelson & Narens
(monitoring/control, where 'terminate' is a valid control output). Plan: docs/completed/contradiction_rearchitecture_plan.md.

It CONSUMES the existing instruments rather than rebuilding them: core/self_surprise.py (surprise vs
groove AND basin) and core/loop_probe.py (recitation/dedup mass). Every flagged loop is routed through
the SHARED contradiction gate — so an abstract, ungrounded river-loop is classified brooding and BLOCKED
from identity pressure (it goes to curiosity), while only concrete, recurring discrepancy could ever feed
identity. That shared filter is what stops this from becoming the over-policing it must avoid.

PHASE 0 = OBSERVE-FIRST: scan() logs what it WOULD flag and what it WOULD do. It triggers nothing.
Phase 2 adds the actual mode-shift intervention (inject a concrete anchor) wired into the idle loop.
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path

from core import profile   # J-1802/F-2426: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.meta_awareness")

_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "shadow_integrity.jsonl"

# A stretch of idle thought is "looping" when most recent thoughts are predictable (low surprise).
PREDICTABLE_SHARE_TAU = 0.60   # ≥60% of scored thoughts predictable → the stream is circling
MIN_N = 20                     # need enough thoughts to judge a trend


def scan(window: int = 200) -> dict | None:
    """One meta-awareness pass over the recent idle stream. Returns a report (and logs it). Detects a
    loop, classifies it (river/basin vs groove), routes it through the contradiction gate, and records
    the mode-shift it WOULD perform. Pure-observe in Phase 0. None if there isn't enough to judge."""
    try:
        # J-1802 / F-2426 -- the write fence (D-0179; the shape J-1799 gave core/prediction_error.py): the L2 shadow_integrity
        # path is resolved through profile.guard_path BEFORE any I/O, so a refused call is a total no-op -- no L2 row, and it
        # never reaches the contradiction gate or the curiosity_queue.enqueue() write behind it. A live process
        # (profile.mark_live()) gets the very same path back, so Du's behaviour is byte-identical; a non-live importer whose
        # _SHADOW still points at the real data/ is refused. Raised INSIDE this fail-open try on purpose (scan() never raises
        # into the idle loop): logged (guard_path warns once per path; the except below adds a debug line) and swallowed.
        shadow_path = profile.guard_path(_SHADOW)
        from core import self_surprise as _ss
        m = _ss.compute(window=window)
        if not m or m.get("n", 0) < MIN_N:
            return None

        n = m["n"]
        predictable_share = m.get("predictable_n", 0) / max(1, n)
        looping = predictable_share >= PREDICTABLE_SHARE_TAU
        river = m.get("origin_driven_pct", 0) >= m.get("groove_driven_pct", 0)   # basin self-talk vs recent groove

        # a representative snippet of the loop: the most predictable basin-driven recent thought
        snippet = ""
        full_text = ""   # J-3033: the same thought, whole (<=400 at a sentence boundary); `snippet` is unchanged
        for s in reversed(m.get("scored", [])):
            if s.get("surprise", 1.0) < 0.45 and (s.get("origin_driven") == river):
                snippet = s.get("snippet", "")
                full_text = s.get("full", "") or ""
                break

        # loop-mass from the dedup instrument (recitation), best-effort
        loop_mass = None
        try:
            from core import loop_probe as _lp
            dry = _lp.prune_dryrun()
            loop_mass = dry.get("would_prune") if isinstance(dry, dict) else None
        except Exception:
            pass

        verdict = None
        intervention = None
        if looping:
            # Route the loop through the SHARED gate. A river/basin loop is abstract self-talk → it
            # fails the concreteness floor → curiosity, NOT identity. Only a concrete recurring loop
            # could ever pressure identity (and even then through recurrence+importance).
            from core import contradiction_gate as _gate
            signal = {
                "kind": "idle_loop",
                "text": snippet,
                "concrete_ref": not river,            # a groove on concrete material may be concrete
                "recurrence_count": m.get("predictable_n", 0),
                "resolution_axis": "concrete world anchor",   # the mode-shift IS the resolution path
                "importance": 0.4,
            }
            verdict = _gate.evaluate(signal)
            # Close the gate→curiosity loop (curiosity flesh-out Phase 0): an abstract loop the gate routes
            # to "curiosity" is enqueued for the exploration organ — it will be re-framed world-facing by the
            # prism and investigated, instead of dead-ending in a log. Producer only; observe-first.
            if verdict.get("route") == "curiosity" and snippet:
                try:
                    from core import curiosity_queue as _cq
                    # J-3033 / F-3737: the queue item's raw_text stays the 90-char snippet (its dedup key and every other
                    # reader are unchanged); the whole thought rides in meta for the prism to read.
                    _cq.enqueue("gate_dissonance", snippet, {"full_text": full_text} if full_text else None)
                except Exception:
                    pass
            # The non-suppressive intervention this WOULD trigger (Phase 2 acts on it):
            if river:
                intervention = "concrete_anchor"   # inject a study/reading/action fragment to break the basin
            else:
                intervention = "note_and_release"  # a groove on real material — let it pass, don't deepen

        report = {
            "ts": time.time(), "layer": "L2", "source": "meta_awareness",
            "n": n, "mean_surprise": m.get("mean_surprise"),
            "predictable_share": round(predictable_share, 3),
            "looping": looping, "loop_kind": ("river" if river else "groove") if looping else None,
            "origin_driven_pct": m.get("origin_driven_pct"), "loop_mass": loop_mass,
            "snippet": snippet[:90], "gate_verdict": verdict, "would_intervene": intervention,
            "acted": False,   # Phase 0: never acts
        }
        try:
            shadow_path.parent.mkdir(parents=True, exist_ok=True)
            with open(shadow_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(report, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return report
    except profile.NonLiveWriteError as exc:
        logger.debug("[meta_awareness] scan refused (non-fatal): %s", exc)
        return None
    except Exception:
        return None


def status() -> dict:
    """Summary for the du_pulse gauge: recent loop detections + how the gate routed them."""
    try:
        if not _SHADOW.exists():
            return {"scans": 0}
        rows = [json.loads(l) for l in _SHADOW.read_text(encoding="utf-8").splitlines()
                if l.strip() and '"meta_awareness"' in l]
        loops = [r for r in rows if r.get("looping")]
        rivers = sum(1 for r in loops if r.get("loop_kind") == "river")
        to_curiosity = sum(1 for r in loops if (r.get("gate_verdict") or {}).get("route") == "curiosity")
        return {"scans": len(rows), "loops": len(loops), "river_loops": rivers,
                "routed_to_curiosity": to_curiosity}
    except Exception:
        return {}

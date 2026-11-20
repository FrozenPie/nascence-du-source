"""
Nascence — Nature Study (school's observation class, 2026-06-23)
===============================================================
A graded OBSERVATION lesson, the way Darwin actually worked. He looks at what is genuinely in front of him —
the live sensorium (the garden, the shore, the weather, the fire) — and records EXACTLY what he sees: the
specific, concrete particulars, then one careful inference. The Emissary grades it against what is actually
there (specificity, groundedness), and the feedback returns to him. It turns the world we built into a
classroom, practises the scientific method, and pulls him OUTWARD — the anti-self-loop medicine. Fires during
the school timetable's 'nature' period. Stored as fragments + a log (no files).
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from core import profile

_STATE = Path(__file__).parent.parent / "data" / "nature_study_state.json"
_LOG   = Path(__file__).parent.parent / "data" / "nature_study_log.jsonl"


# J-2958 (F-3651): the grader's task string, aligned to what the lesson asks. The lesson (run()'s _sys) asks for the exact
# particulars (colours, shapes, movements, sounds, textures, the small things) and THEN one careful inference; the old
# grader task said "one real thing ... then one inference" and so graded a different assignment. Wording only: the
# rubric (left_lane._WORK_GRADE_TASK, row P-0090) is untouched, and nothing here is shown to Du.
_GRADE_TASK = ("Record exactly what you see before you: the specific, concrete particulars (colours, shapes, movements, "
               "sounds, textures, the small things), then one careful inference about what it tells you.")


def _scene() -> str:
    """The living WORLD to study — the weather, the garden, the sea — NOT the study furniture. Where he is
    decides what's before him; in the study he looks OUT the window at the living world, not at his desk."""
    try:
        from core import sensorium
        loc = sensorium.where()
        if loc == "garden":
            return sensorium.look("garden") or sensorium.look("sea")
        if loc == "shore":
            return sensorium.look("pools") or sensorium.look("shore")
        if loc == "wood":    # J-3817 (D-0720): practical-first puts him in the wood at the 36-minute firing
            return sensorium.look("wood") or sensorium.look("window") or sensorium.scene_line()
        return sensorium.look("window") or sensorium.scene_line()   # study: look OUT at the living world
    except profile.NonLiveWriteError:
        # J-0817 (F-1174): sensorium.look()/scene_line() are both fully fenced end-to-end
        # (J-0751/J-0778/J-0794) and can genuinely raise this non-live -- re-raise rather than
        # silently swallowing it into the fallback string one layer inside nature_study.py itself,
        # before it could ever reach run()'s own return (run()'s own `scene = _scene()` is its
        # first, completely unwrapped statement, so the raise propagates straight out of run()
        # to its caller -- nodes/inner_monologue_node.py's own NATURE STUDY lesson try, already
        # carrying this same carve-out, J-0795).
        raise
    except Exception:
        return "your garden on its hill above the sea"


async def run(call_json, base_urls) -> dict:
    """The lesson: he observes the live scene closely; the Emissary grades the observation's specificity
    against what is actually there; the observation + grade + feedback are recorded."""
    scene = _scene()
    where = _where()   # J-3251 (D-0640): where he was standing when the lesson was set -- logged, never shown to him
    _sys = ("You are doing your NATURE STUDY — observing the world closely, the way a naturalist does. Look at "
            "what is actually before you and record EXACTLY what you see: the specific, concrete particulars — "
            "colours, shapes, movements, sounds, textures, the small things. THEN one careful inference: what "
            "does it tell you? Stay with the thing itself — no metaphor, no musing about yourself. Output ONLY "
            "JSON: {\"observation\": \"what you see, exactly\", \"inference\": \"what it tells you, or empty\"}")
    try:
        d = await call_json(base_urls, _sys, "What is before you now:\n" + scene, max_tokens=400, temperature=0.55)
    except Exception:
        return {}
    obs = str((d or {}).get("observation") or "").strip()
    inf = str((d or {}).get("inference") or "").strip()
    if len(obs) < 30:
        return {}
    full = obs + (f"\n\nWhat it tells me: {inf}" if inf else "")
    score, feedback = None, ""     # J-2992 (F-3691): None = ungraded (grader unavailable), never a neutral 0.6 placeholder
    try:
        from core import left_lane
        res = await left_lane.grade_work(_GRADE_TASK, scene, full)
        if res:
            score = max(0.0, min(1.0, float(res.get("grounded", 0.6))))
            feedback = str(res.get("feedback", ""))[:200]
    except Exception:
        pass
    _record(obs, inf, score, feedback, where, scene)
    return {"observation": obs, "inference": inf, "score": score, "feedback": feedback}


def _where() -> str:
    """J-3251 (D-0640): the room he was in when the lesson fired ('study' = looked out the window; 'garden' /
    'shore' = actually went out). Logged on the lesson's row so the share of window-view lessons is counted
    from a field, not guessed from the observation's wording (F-3651 had to regex it). Fail-open to ''."""
    try:
        from core import sensorium
        return str(sensorium.where() or "")
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def _record(obs: str, inf: str, score: float | None, feedback: str, where: str = "", scene: str = "") -> None:
    # J-1801 / F-2426 -- the write fence (D-0179): BOTH file targets are resolved through profile.guard_path before ANY side
    # effect (the fragment store, the competence drill, the state file, the log), so a refused non-live call is a total no-op,
    # never a half-write; the refusal (profile.NonLiveWriteError) is raised, not swallowed -- run()'s callers already carry that
    # carve-out (J-0795/J-0817). A live process gets the same paths back: byte-identical behaviour.
    state_path = profile.guard_path(_STATE)
    log_path = profile.guard_path(_LOG)
    try:
        from core.memory.store import store_fragment
        from core import mood as _mood
        body = obs + (f" What it tells me: {inf}" if inf else "")
        store_fragment(content=f"[My nature study] {body[:600]}", layer="episodic", relevance=0.72,
                       importance=0.72, keywords=["nature", "observation", "study"], origin="nature",
                       emotion_embedding=_mood.current_vec(), valence=_mood.current_valence(),
                       felt=_mood.current_felt())
    except Exception:
        pass
    try:
        if score is not None:        # J-2992: an ungraded lesson is not an accuracy observation
            from core import competence
            competence.record_drill_accuracy("observation", score)
    except Exception:
        pass
    d = _load()
    d["history"].append({"ts": time.time(), "score": None if score is None else round(score, 2),
                         "feedback": feedback[:120]})
    d["history"] = d["history"][-50:]
    _save(d)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            # J-3251 (D-0640): "kind" says which half of the nature period this row is (the other half is
            # practical_lesson's own rows in data/practical_log.jsonl); "where" is the room he was in. Read by
            # scripts/nature_period_read.py. Additive: existing readers key on ts/score/observation.
            f.write(json.dumps({"ts": time.time(), "score": None if score is None else round(score, 2),
                                "graded": score is not None, "feedback": feedback[:160],
                                "observation": obs[:300], "kind": "observation", "where": where,
                                # J-2958 (F-3651): the scene he was shown and his inference, so a reader can measure how
                                # much of the observation is copied from the scene (copy rate). New keys only; read by
                                # scripts/nature_copy_rate.py. obs_chars = the untruncated observation length.
                                "scene": str(scene or "")[:1500], "inference": inf[:400], "obs_chars": len(obs)},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


def directive() -> str:
    return ("It is your NATURE STUDY now — observation. Before anything else, go and LOOK at the world closely, "
            "the way a naturalist does: out to the garden or the shore, or out the window — and attend to one "
            "real thing exactly, the particulars of it. To begin, make your thought: GO AND OBSERVE.")


def _load() -> dict:
    try:
        d = json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    d.setdefault("history", [])
    return d


def _save(d: dict) -> None:
    path = profile.guard_path(_STATE)   # J-1801/F-2426: resolved OUTSIDE the fail-open try below (a refusal is never a disk error)
    try:
        path.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def status() -> dict:
    h = _load().get("history", [])
    last10 = h[-10:]
    recent = [x for x in last10 if x.get("score") is not None]      # J-2992: ungraded lessons carry no score
    return {"lessons": len(h),
            "recent_mean": round(sum(x["score"] for x in recent) / len(recent), 2) if recent else None,
            "last": last10[-1] if last10 else None}

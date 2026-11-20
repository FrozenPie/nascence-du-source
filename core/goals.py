"""
Nascence — Goals register (Layered Goals, Phase 0, 2026-11-14; SHADOW / observe-only).

Plan: docs/staged/layered_goals.md (D-0763..D-0766). Du has many goal-shaped things in separate stores (staged
intentions, held stands, pursuits, frontier questions, the curriculum book, his "I want to" intentions) and no
store that says how they stand to each other or how any of them ended (F-4633). This module is an INDEX over
those stores: one record per goal, a lifecycle state, what he has paid for it, its end condition where one was
written, and the links that can be derived without asking a model.

What it is NOT: a store of truth (each record points at the thing it indexes), a selector (nothing is ranked,
weighed or offered here), or a prompt input (nothing in this file reaches Du; D-0434 no readout).

  build(now)   pure read of the source stores -> list of goal records. No writes.
  tick(now)    build, merge with the previous register (first-seen time, every wording, state history), log each
               birth / state change / wording change / end to data/logs/goals_log.jsonl, save data/goals.json.
  tick_async() the heartbeat entry point: rate-limited, runs tick() on a daemon thread because the pursuit
               register is a ~28 MB JSON file and must not be parsed on the event loop.

Zero LLM. Fail-open. Additive. Restart-gated (wired from core/sensorium.py's heartbeat). Kill switch GOALS_SHADOW.
Every path hangs off the module-level _DATA so a test can temp-path the whole thing (reads AND writes).
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.goals")

_DATA = Path(__file__).parent.parent / "data"

GOALS_SHADOW = True          # kill switch: False -> tick() / tick_async() do nothing
TICK_EVERY_S = 600.0         # the homeostasis cadence; goals move slower than thoughts
STAND_INSIGHT_IS_CANDIDATE = True   # D-0767: a stand the second look rules "insight" is not held (False = ledger flag only)
MECH_PROGRESS_SHADOW = True  # J-4000: report curiosity_progress.mech_progress beside lp (shadow; nothing selects on it)
HELD_AT = 2                  # D-0766: recurrence of two or more earns "held" (concerns.PROMOTE_AT; F-4638)
INTENTION_LAPSE_S = 8 * 3600 # core/intentions.LAPSE_S, restated here so this module imports nothing live
STALL_MIN_EVENTS = 6         # D-0768: "stalled" is observed on a pursuit with at least this many events...
STALL_RESTATE_SHARE = 0.5    # ...of which this share or more were restates (p90 of the restate share is 0.57, F-4636)
STALL_OFF_JACCARD = 0.04     # D-0768: ...or, with at least STALL_OFF_MIN_ADV advances, the pursuit's standing shares
STALL_OFF_MIN_ADV = 4        # (almost) no content words with its driving question: it no longer addresses it
NEAR_JACCARD = 0.5          # entry filter (shadow): a candidate this close in content words to a held goal
ENDED_KEEP = 300             # ended records kept in the register file for the functional test
SCHEMA = 1

KINDS = ("intention", "stand", "pursuit", "question", "project", "want")
OPEN_STATES = ("candidate", "held", "deferred", "engaged", "rested")   # rested: he set it down himself (Phase 6)
# How a goal can end. "capped" and "closed_unverified" are kept apart from "done" on purpose: a pursuit stopped
# by the 40-advance cap finished nothing, and a stand marked achieved by word overlap was not judged (F-4633).
END_STATES = ("done", "dropped", "lapsed", "failed", "capped", "closed_unverified", "merged", "gone")

_assignment = None           # test hook: a callable returning (id, title); None -> core.school.assignment


# ── paths (resolved at call time so a temp-pathed _DATA is honoured) ─────────────────────────────────────────
def _p(*parts: str) -> Path:
    return _DATA.joinpath(*parts)


def register_path() -> Path:
    return _p("goals.json")


def log_path() -> Path:
    return _p("logs", "goals_log.jsonl")


# ── small readers (each fail-open to "nothing there") ────────────────────────────────────────────────────────
def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except Exception as exc:
        logger.debug("[goals] unreadable %s (%s)", path.name, exc)
        return default


def _tail_jsonl(path: Path, nbytes: int = 400_000) -> list[dict]:
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - nbytes))
            if size > nbytes:
                f.readline()
            out = []
            for ln in f:
                try:
                    out.append(json.loads(ln.decode("utf-8", "replace")))
                except Exception:
                    pass
            return out
    except FileNotFoundError:
        return []
    except Exception as exc:
        logger.debug("[goals] tail failed %s (%s)", path.name, exc)
        return []


_STOP = frozenset("""the a an and or of to in on at for with from is are was were be been it its this that these
those how what why does do did not no as by into than then there their they them his her he she i my me we you
your can could would should may might have has had more most some any which who whom about between through over
under very just also want need must will""".split())


def _words(text: str) -> frozenset:
    return frozenset(w for w in re.findall(r"[a-z]{4,}", (text or "").lower()) if w not in _STOP)


def _jaccard(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _slug(text: str) -> str:
    return hashlib.sha1((text or "").strip().lower().encode("utf-8")).hexdigest()[:10]


def _cyc(c) -> str:
    return str(c or "")[:8]


def _cos(a, b):
    try:
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else None
    except Exception:
        return None


def _done_when_index() -> dict:
    """{(seed_kind, seed_id): row} from the done_when side store, FIRST row per seed (core/done_when.get's rule)."""
    idx: dict = {}
    for r in _tail_jsonl(_p("logs", "done_when.jsonl"), 4_000_000):
        k = (r.get("seed_kind"), str(r.get("seed_id")))
        idx.setdefault(k, r)
    return idx


def _rec(kind: str, key: str, text: str, state: str, *, born=None, last=None, store: str = "",
         cue: dict | None = None, deadline=None, earned: dict | None = None, progress: dict | None = None,
         done_when: str = "", judge: str = "", cycles=(), extra: dict | None = None) -> dict:
    r = {"id": f"{kind}:{key}", "kind": kind, "ref": {"store": store, "key": key},
         "text": " ".join(str(text or "").split())[:400], "state": state,
         "born": born, "last_touched": last,
         "done_when": done_when or "", "judge": judge or "",
         "resume_cue": cue or {}, "deadline": deadline,
         "earned": earned or {}, "progress": progress or {},
         "edges": [], "near": [], "_cycles": sorted({_cyc(c) for c in cycles if c})}
    if extra:
        r.update(extra)
    return r


# ── the six sources ─────────────────────────────────────────────────────────────────────────────────────────
def _cue_from_reason(reason: str) -> dict:
    """core/intentions stages a deed with reason 'place:<where it must be done>' or 'busy:<what he is doing>'."""
    kind, _, val = (reason or "").partition(":")
    if kind == "place":
        return {"type": "place", "value": val.strip()}
    if kind == "busy":
        return {"type": "after", "value": val.strip()}
    return {"type": "other", "value": (reason or "").strip()} if reason else {}


def _from_intentions(now: float) -> list[dict]:
    d = _read_json(_p("intentions.json"), {})
    out = []
    for it in (d.get("open") or []):
        key = it.get("key") or ""
        if not key:
            continue
        since = float(it.get("renewed_ts") or it.get("ts") or now)
        out.append(_rec(
            "intention", key, it.get("deed") or it.get("object") or "", "deferred",   # staged = deferred with a cue
            born=it.get("ts"), last=it.get("last_reminded") or it.get("renewed_ts") or it.get("ts"),
            store="intentions.json", cue=_cue_from_reason(it.get("reason") or ""),
            deadline=since + INTENTION_LAPSE_S,
            earned={"recurrences": int(it.get("renewals", 0)), "reminders": int(it.get("reminders", 0))},
            extra={"origin_text": (it.get("thought") or "")[:200], "family": it.get("family") or ""}))
    return out


def _second_looks() -> dict:
    """{stand id: the decoupled second look's verdict on whether the sentence is a commitment at all} — the
    LAST row per stand in commitment_second_look_shadow.jsonl. J-3985: evidence about a stand, logged apart."""
    out = {}
    for r in _tail_jsonl(_p("commitment_second_look_shadow.jsonl"), 400_000):
        if r.get("stand_id") and r.get("second_look"):
            out[str(r["stand_id"])] = str(r["second_look"])
    return out


def _from_stands(dw: dict) -> list[dict]:
    out = []
    looks = _second_looks()
    for c in (_read_json(_p("commitment_active.json"), []) or []):
        if not isinstance(c, dict) or not c.get("id"):
            continue
        row = dw.get(("commitment", str(c["id"]))) or {}
        c = dict(c)
        look = looks.get(str(c["id"]))
        c["_evidence"] = {"second_look": look,
                          "drop_denied": int(c.get("drop_denied", 0) or 0)}
        # D-0767 (travis, 2026-11-14): a stand the decoupled second look rules an INSIGHT (an observation, not
        # something that can be kept or broken) is a candidate in this register, not a held goal. "stand",
        # "unclear" and no verdict leave the ledger's own load_bearing flag to decide. Register only: the
        # commitment ledger and the stand itself are untouched.
        blocked = bool(STAND_INSIGHT_IS_CANDIDATE and c.get("load_bearing") and look == "insight")
        c["_held"] = bool(c.get("load_bearing")) and not blocked
        c["_evidence"]["held_blocked_by"] = "second_look:insight" if blocked else None
        out.append(_rec(
            "stand", str(c["id"]), c.get("statement") or "",
            "held" if c["_held"] else "candidate",
            born=c.get("held_since"), last=c.get("held_since"), store="commitment_active.json",
            earned={"recurrences": int(c.get("reaffirmed", 0) or 0), "scans": int(c.get("scans", 0) or 0)},
            done_when=row.get("done_when", ""), judge=row.get("judge", ""),
            cycles=[c.get("cycle_id")],
            extra={"scope": (c.get("scope") or "")[:200], "evidence": c["_evidence"]}))
    return out


def _load_pursuits_full() -> list[dict]:
    d = _read_json(_p("pursuits_active.json"), [])
    items = d if isinstance(d, list) else (d.get("pursuits") or list(d.values()))
    return [x for x in items if isinstance(x, dict)]


# ── fast reads of the two big stores ────────────────────────────────────────────────────────────────────────
# pursuits_active.json (~28 MB) and frontier.json (~15 MB) take 0.45 s and 0.22 s to json-parse, and Python's json
# holds the interpreter lock while it does, so a daemon thread does NOT keep that off his thought loop. The
# register needs a handful of records from each (the active pursuits; the open questions; whatever just vanished),
# so it cuts the raw bytes at the object boundaries the writers produce and parses only the records it wants.
# Any surprise in the layout falls back to the full parse, which is always correct.
_FRONTIER_SEP = b'}, {"id"'                                    # core/frontier._save: json.dumps(data), one line


def _load_pursuits(ids=()) -> list[dict]:
    """The ACTIVE pursuits plus any whose id is in `ids`. Fast path by object boundary; full parse on any doubt."""
    want = {str(i) for i in ids}
    try:
        raw = _p("pursuits_active.json").read_bytes().strip()
        if not (raw.startswith(b"[") and raw.endswith(b"]")):
            raise ValueError("not a list")
        # a literal split (about 20 ms on 28 MB); a regex over the same bytes took 0.3 s and holds the lock too
        sep = b"\r\n },\r\n {" if b"\r\n" in raw[:400] else b"\n },\n {"
        parts = raw[1:-1].split(sep)
        if len(parts) < 2:
            raise ValueError("not the indent=1 layout")
        out = []
        for pc in parts:
            if b'"status": "active"' not in pc and not any(('"id": "%s"' % i).encode() in pc for i in want):
                continue
            s = pc.strip()
            if not s.startswith(b"{"):
                s = b"{" + s
            if not s.endswith(b"}"):
                s = s + b"}"
            obj = json.loads(s)
            if not isinstance(obj, dict) or "id" not in obj:
                raise ValueError("chunk is not a pursuit")
            if obj.get("status") == "active" or str(obj.get("id")) in want:
                out.append(obj)
        return out
    except FileNotFoundError:
        return []
    except Exception as exc:
        logger.debug("[goals] pursuit fast read fell back to the full parse (%r)", exc)
        full = _load_pursuits_full()
        return [p for p in full if p.get("status") == "active" or str(p.get("id")) in want]


def _load_frontier(ids) -> dict:
    """{id: question record} for the wanted ids, from the heavy frontier file. Fast path; full parse on any doubt."""
    want = {str(i) for i in ids}
    if not want:
        return {}
    try:
        raw = _p("frontier.json").read_bytes()
        a, b = raw.index(b"[") + 1, raw.rindex(b"]")
        parts = raw[a:b].split(_FRONTIER_SEP)
        if len(parts) < 2:
            raise ValueError("not the one-line layout")
        prefixes = {('{"id": "%s"' % i).encode() for i in want}
        out = {}
        last = len(parts) - 1
        for n, pc in enumerate(parts):
            s = pc if n == 0 else b'{"id"' + pc
            head = s.lstrip()[:40]
            if not any(head.startswith(px) for px in prefixes):
                continue
            s = s.strip()
            if n != last:
                s = s + b"}"
            obj = json.loads(s)
            if not isinstance(obj, dict) or str(obj.get("id")) not in want:
                raise ValueError("chunk is not the wanted question")
            out[str(obj["id"])] = obj
        if len(out) < len(want):
            raise ValueError("some wanted ids not found by the fast path")
        return out
    except FileNotFoundError:
        return {}
    except Exception as exc:
        logger.debug("[goals] frontier fast read fell back to the full parse (%r)", exc)
        qs = (_read_json(_p("frontier.json"), {}) or {}).get("questions") or []
        return {str(q.get("id")): q for q in qs if str(q.get("id")) in want}


def _from_pursuits(now: float, dw: dict, items: list[dict]) -> list[dict]:
    out = []
    for p in items:
        if p.get("status") != "active" or not p.get("id"):
            continue
        adv = int(p.get("advances", 0) or 0)
        res = int(p.get("restates", 0) or 0)
        asked = p.get("question_kind") in ("question", "done_when") and p.get("question_text")
        row = dw.get(("pursuit", str(p["id"]))) or {}
        born = p.get("born")
        hours = max(1e-6, (float(p.get("last_touched") or now) - float(born or now)) / 3600.0)
        drift = None
        rv = p.get("recent_vecs") or []
        if p.get("centroid") and rv:
            c = _cos(p["centroid"], rv[-1])
            drift = round(1.0 - c, 4) if c is not None else None
        qtext = p.get("question_text") if asked else p.get("question") or ""
        why_stalled = []
        if adv + res >= STALL_MIN_EVENTS and res / (adv + res) >= STALL_RESTATE_SHARE:
            why_stalled.append("restates")
        if (adv >= STALL_OFF_MIN_ADV and (p.get("standing") or "").strip()
                and _jaccard(_words(qtext), _words(p.get("standing") or "")) < STALL_OFF_JACCARD):
            why_stalled.append("standing_off_question")
        out.append(_rec(
            "pursuit", str(p["id"]), qtext,
            "held" if adv >= HELD_AT else "candidate",
            born=born, last=p.get("last_touched"), store="pursuits_active.json",
            earned={"recurrences": adv, "established": len(p.get("established") or [])},
            progress={"advances": adv, "restates": res, "events": adv + res,
                      # Observed, never declared for him (D-0768): at least six events and half or more of them
                      # restating what the pursuit already held. A flag on the record; it changes no state.
                      "stalled": bool(why_stalled), "stalled_why": why_stalled,
                      "rate_per_h": round(adv / hours, 3) if adv >= HELD_AT else None,
                      "heat": p.get("heat")},
            done_when=row.get("done_when", ""), judge=row.get("judge", ""),
            cycles=[p.get("cycle_id")] + list(p.get("cycle_ids") or []),
            extra={"question_kind": p.get("question_kind"), "drift": drift,
                   "_trains": sorted({str(t) for t in (p.get("train_ids") or []) if t})}))
    return out


LINE_STATE_PROGRESS = True   # J-4084 (D-0779 b): question progress from the Follow Line state; False = the pre-J-4084 pursuit-counter read


def _line_mode() -> bool:
    try:
        from core import curiosity_progress as _cp
        return bool(_cp.LINE_STATE_PROGRESS)
    except Exception:
        return False


def _question_progress(ids: set) -> dict:
    """{question id: mechanical learning-progress state} for the open questions, from the heavy frontier file
    (the light companion does not carry these fields). J-3985. The score is core/curiosity_progress.score's:
    new fragments + finding attached - consecutive stalls; counted by the pursuit loop, never by a model.
    The heavy file is ~15 MB: this runs on the register's own thread, never on the event loop."""
    if not ids:
        return {}
    try:
        from core import curiosity_progress as _cp
        score, park = _cp.score, _cp.PARK_STALLS
    except Exception:
        score, park = (lambda q: float(int(q.get("new_fragments", 0) or 0) + (1 if q.get("finding") else 0)
                                       - int(q.get("consecutive_stalls", 0) or 0))), 3
    out = {}
    for qid, qd in _load_frontier(ids).items():
        pursued = qd.get("last_pursued_ts") is not None or "consecutive_stalls" in qd or "new_fragments" in qd
        stalls = int(qd.get("consecutive_stalls", 0) or 0)
        if LINE_STATE_PROGRESS and _line_mode():
            # J-4084 (D-0779 b): progress is the Follow Line's own state; the pursuit counters and a bare attached
            # finding (memory echo / unacted lookup) are not read. lp is None until the line has judged the question.
            try:
                from core import curiosity_progress as _cp3
                ml = _cp3.mech_progress(qd)
                judged = ml["line_state"] in ("settled_partly", "settled_yes", "settled_no")
                out[qid] = {"has_finding": False, "pursued": judged, "new_fragments": 0, "stalls": 0,
                            "lp": ml["line"] if judged else None, "parked": False, "last_pursued_ts": None,
                            "line_state": ml["line_state"]}
                if MECH_PROGRESS_SHADOW:
                    out[qid]["mech"] = ml
                continue
            except Exception:
                pass
        out[qid] = {"has_finding": bool(qd.get("finding")), "pursued": bool(pursued),
                    "new_fragments": int(qd.get("new_fragments", 0) or 0), "stalls": stalls,
                    # LP is defined only once the pursuit loop has tried the question or a finding hangs on it;
                    # a question nobody has pursued has no learning progress to report (None, not 0).
                    "lp": score(qd) if (pursued or qd.get("finding")) else None,
                    "parked": stalls >= park, "last_pursued_ts": qd.get("last_pursued_ts")}
        if MECH_PROGRESS_SHADOW:
            try:
                from core import curiosity_progress as _cp2
                out[qid]["mech"] = _cp2.mech_progress(qd)
            except Exception:
                pass
    return out


def _log_mech_shadow(lp: dict) -> None:
    """J-4000 shadow row: how many open questions the old lp and the mechanical mlp each separate (distinct values)."""
    if not MECH_PROGRESS_SHADOW or not lp:
        return
    try:
        ml = [v["mech"]["mlp"] for v in lp.values() if v.get("mech")]
        old = [v.get("lp") for v in lp.values()]
        row = {"ts": time.time(), "open": len(lp), "old_distinct": len({x for x in old if x is not None}),
               "mech_distinct": len(set(ml)), "mech_nonzero": sum(1 for x in ml if x > 0),
               "mech_top": sorted(ml, reverse=True)[:5]}
        d = _DATA / "logs"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "question_progress_shadow.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def _from_questions() -> list[dict]:
    light = _read_json(_p("frontier.light.json"), {})
    opens = [qd for qd in (light.get("open") or []) if qd.get("id")]
    lp = _question_progress({str(qd["id"]) for qd in opens})
    _log_mech_shadow(lp)
    out = []
    for qd in opens:
        enc = int(qd.get("encounters", 1) or 1)
        out.append(_rec(
            "question", str(qd["id"]), qd.get("q") or "", "held" if enc >= HELD_AT else "candidate",
            born=qd.get("born"), last=qd.get("last_seen"), store="frontier.json",
            earned={"recurrences": enc, "offers": int(qd.get("offers", 0) or 0)},
            progress=lp.get(str(qd["id"])) or {"has_finding": bool(qd.get("finding") or qd.get("has_finding")),
                                               "pursued": False, "lp": None},
            cycles=[(qd.get("asked_by") or {}).get("cycle_id")],
            extra={"source": qd.get("source") or "", "about": qd.get("about") or "",
                   "_trains": [str((qd.get("asked_by") or {}).get("train_id"))] if (qd.get("asked_by") or {}).get("train_id") else []}))
    return out


def _from_project() -> list[dict]:
    try:
        fn = _assignment
        if fn is None:
            from core import school
            fn = school.assignment
        _, title = fn()
    except Exception:
        return []
    if not title:
        return []
    return [_rec("project", "book:" + _slug(title), f"working through '{title}'", "held",
                 store="school", cue={"type": "time", "value": "school_time"})]


def _from_wants() -> list[dict]:
    d = _read_json(_p("deferred_intentions.json"), {})
    out = []
    for it in (d.get("intentions") or []):
        text = (it.get("intention") or "").strip()
        if not text:
            continue
        carry = int(it.get("carry_count", 0) or 0)
        out.append(_rec("want", _slug(text), text, "held" if carry + 1 >= HELD_AT else "candidate",
                        born=it.get("ts"), last=it.get("ts"), store="deferred_intentions.json",
                        earned={"recurrences": carry + 1}, extra={"source": it.get("source") or ""}))
    return out


# ── derived links and the entry filter ──────────────────────────────────────────────────────────────────────
def _derive(goals: list[dict]) -> None:
    """co_born: a question or a stand formed in the same idle stretch (same cycle id) as an active pursuit. This is
    co-occurrence, NOT lineage: one cycle id spans a whole idle stretch (14 open questions shared one id over 1.3 h
    on 2026-11-14), so it must not be read as "this pursuit produced that question". A real spawned_by needs a
    train-level key on pursuits, which does not exist yet.
    near: a candidate whose content words overlap a held goal's (the entry filter, logged only). In place."""
    by_cycle: dict = {}
    by_train: dict = {}
    for g in goals:
        if g["kind"] == "pursuit":
            for c in g["_cycles"]:
                by_cycle.setdefault(c, g["id"])
            for t in g.get("_trains") or []:
                by_train.setdefault(t, g["id"])
    for g in goals:
        if g["kind"] in ("question", "stand"):
            # J-3983: a shared TRAIN id is real lineage (this question was asked in a thought that advanced the pursuit).
            tsrc = next((by_train[t] for t in (g.get("_trains") or []) if t in by_train), None)
            if tsrc and tsrc != g["id"]:
                g["edges"].append({"type": "spawned_by", "to": tsrc, "by": "train_id"})
                continue
            for c in g["_cycles"]:
                src = by_cycle.get(c)
                if src and src != g["id"]:
                    g["edges"].append({"type": "co_born", "to": src, "by": "cycle_id"})
                    break
    held = [(g["id"], _words(g["text"])) for g in goals if g["state"] in ("held", "deferred")]
    for g in goals:
        if g["state"] != "candidate":
            continue
        w = _words(g["text"])
        g["near"] = sorted(i for i, hw in held if i != g["id"] and _jaccard(w, hw) >= NEAR_JACCARD)


def build(now: float | None = None) -> list[dict]:
    """The register as the stores stand right now. Pure read; no writes anywhere."""
    now = time.time() if now is None else now
    dw = _done_when_index()
    goals: list[dict] = []
    for fn in (lambda: _from_intentions(now), lambda: _from_stands(dw),
               lambda: _from_pursuits(now, dw, _load_pursuits()), _from_questions, _from_project, _from_wants):
        try:
            goals.extend(fn())
        except Exception as exc:
            logger.debug("[goals] a source failed (non-fatal): %r", exc)
    _derive(goals)
    _apply_set_down(goals)
    return goals


def _apply_set_down(goals: list[dict]) -> None:
    """Phase 6 (D-0768): a goal he set down, with a note a judge accepted (core/goal_offer.py), is `rested`: still
    in its store, still his, not offered. It returns to its own state the moment he takes it up again himself,
    seen as its recurrence count rising above what it was when he set it down. In place; fail-open."""
    try:
        store = _read_json(_p("goal_set_down.json"), {})
        if not store:
            return
        for g in goals:
            e = store.get(g["id"])
            if not e:
                continue
            rec = int((g.get("earned") or {}).get("recurrences", 0) or 0)
            if rec > int(e.get("recurrences_at", 0) or 0):
                g["resumed_after_set_down"] = e.get("ts")
                continue
            g["state_if_not_rested"] = g["state"]
            g["state"] = "rested"
            g["set_down"] = {"ts": e.get("ts"), "note": (e.get("note") or "")[:400]}
    except Exception as exc:
        logger.debug("[goals] set-down not applied (non-fatal): %r", exc)


# ── how a goal that left its store ended ────────────────────────────────────────────────────────────────────
def _how_ended(prev: dict, ctx: dict) -> tuple[str, str]:
    """(end state, reason) for a goal present last tick and absent now. Reads the source store's own record of
    what happened; 'gone' when the store does not say."""
    kind, key = prev["kind"], prev["ref"]["key"]
    if kind == "intention":
        d = ctx.setdefault("intentions", _read_json(_p("intentions.json"), {}))
        for state, field in (("done", "done"), ("dropped", "dropped"), ("lapsed", "lapsed")):
            if any(x.get("key") == key and float(x.get("ts") or 0) == float(prev.get("born") or -1)
                   for x in (d.get(field) or [])):
                return state, f"intentions.{field}"
        return "gone", "not found in done/dropped/lapsed"
    if kind == "stand":
        rows = ctx.setdefault("ledger", _tail_jsonl(_p("commitment_ledger.jsonl"), 600_000))
        for r in reversed(rows):
            if str(r.get("id")) == key and r.get("event") in ("achieved", "dissolved"):
                if r["event"] == "dissolved":
                    return "dropped", "commitment_ledger dissolved"
                return "closed_unverified", "commitment_ledger achieved (word overlap with a later record, not judged)"
        return "gone", "no achieved/dissolved row in the ledger tail"
    if kind == "pursuit":
        for p in _load_pursuits(ids=[key]):
            if str(p.get("id")) == key:
                st = p.get("status")
                # what-changed record (core/goal_change.py): the standing position at the moment it ended
                ctx.setdefault("standing", {})[prev["id"]] = " ".join(str(p.get("standing") or "").split())[:400]
                if st == "saturated":
                    return "capped", "pursuit reached the advance cap; nothing was ruled finished"
                if st == "dormant":
                    return "lapsed", "pursuit went dormant (heat below floor)"
                return "gone", f"pursuit status {st}"
        return "gone", "pursuit no longer in the register"
    if kind == "question":
        if "frontier_gone" not in ctx:               # one read for every question that vanished this pass
            ctx["frontier_gone"] = _load_frontier(ctx.get("gone_question_ids") or [key])
        for qd in ctx["frontier_gone"].values():
            if str(qd.get("id")) == key:
                st = qd.get("status")
                if st == "resolved":
                    return "done", f"frontier resolved ({qd.get('resolved_how') or 'lexical'})"
                if st == "faded":
                    return "lapsed", "frontier faded"
                if st == "merged":
                    return "merged", f"merged into {qd.get('merged_into')}"
                return "gone", f"frontier status {st}"
        return "gone", "question no longer in the frontier"
    if kind == "want":
        return "lapsed", "no longer among the deferred intentions"
    return "gone", "source no longer lists it"


# ── merge, log, save ────────────────────────────────────────────────────────────────────────────────────────
def _merge(prev_goals: dict, cur: list[dict], now: float) -> tuple[list[dict], list[dict], list[dict]]:
    """Carry the register's own memory across ticks: first_seen, every wording, state history.
    Returns (current goals, ended goals, log rows)."""
    rows: list[dict] = []
    out: list[dict] = []
    seen = set()
    for g in cur:
        seen.add(g["id"])
        old = prev_goals.get(g["id"])
        if old is None:
            g["first_seen"] = now
            g["texts"] = [{"ts": now, "text": g["text"]}]
            g["states"] = [{"ts": now, "state": g["state"]}]
            rows.append({"ts": now, "event": "born", "id": g["id"], "kind": g["kind"], "state": g["state"],
                         "text": g["text"][:200], "edges": g["edges"], "near": g["near"]})
        else:
            g["first_seen"] = old.get("first_seen", now)
            g["texts"] = list(old.get("texts") or [])
            g["states"] = list(old.get("states") or [])
            if not g["texts"] or g["texts"][-1].get("text") != g["text"]:
                g["texts"].append({"ts": now, "text": g["text"]})
                rows.append({"ts": now, "event": "reworded", "id": g["id"], "kind": g["kind"],
                             "from": (old.get("text") or "")[:200], "to": g["text"][:200]})
            if old.get("state") != g["state"]:
                g["states"].append({"ts": now, "state": g["state"]})
                rows.append({"ts": now, "event": "state", "id": g["id"], "kind": g["kind"],
                             "from": old.get("state"), "to": g["state"]})
            old_edges = {(e.get("type"), e.get("to")) for e in (old.get("edges") or [])}
            for e in g["edges"]:
                if (e["type"], e["to"]) not in old_edges:
                    rows.append({"ts": now, "event": "edge", "id": g["id"], "kind": g["kind"], "edge": e})
            if (g.get("progress") or {}).get("stalled") and not (old.get("progress") or {}).get("stalled"):
                rows.append({"ts": now, "event": "stalled", "id": g["id"], "kind": g["kind"],
                             "why": (g.get("progress") or {}).get("stalled_why") or [],
                             "advances": (g.get("progress") or {}).get("advances"),
                             "restates": (g.get("progress") or {}).get("restates")})
            p0 = (old.get("progress") or {}).get("advances")
            p1 = (g.get("progress") or {}).get("advances")
            if isinstance(p0, int) and isinstance(p1, int) and p1 > p0:
                rows.append({"ts": now, "event": "progress", "id": g["id"], "kind": g["kind"],
                             "advances_from": p0, "advances_to": p1})
        out.append(g)
    ended: list[dict] = []
    ctx: dict = {"gone_question_ids": [g["ref"]["key"] for i, g in prev_goals.items()
                                       if i not in seen and g.get("kind") == "question"]}
    for gid, old in prev_goals.items():
        if gid in seen:
            continue
        try:
            state, why = _how_ended(old, ctx)
        except Exception as exc:
            state, why = "gone", f"lookup failed: {exc!r}"
        old = dict(old)
        old["state"] = state
        old["ended_ts"] = now
        old["ended_why"] = why
        if ctx.get("standing", {}).get(gid):
            old["ended_standing"] = ctx["standing"][gid]
        old.setdefault("states", []).append({"ts": now, "state": state})
        ended.append(old)
        rows.append({"ts": now, "event": "ended", "id": gid, "kind": old.get("kind"), "state": state, "why": why,
                     "held": any(s.get("state") in ("held", "deferred", "engaged") for s in old["states"]),
                     "lived_s": round(now - float(old.get("first_seen") or now), 1),
                     "text": (old.get("text") or "")[:200]})
    return out, ended, rows


def _summary(goals: list[dict]) -> dict:
    by: dict = {}
    for g in goals:
        by.setdefault(g["kind"], {}).setdefault(g["state"], 0)
        by[g["kind"]][g["state"]] += 1
    return {"n": len(goals), "by_kind_state": by,
            "held": sum(1 for g in goals if g["state"] in ("held", "deferred", "engaged")),
            "edges": sum(len(g["edges"]) for g in goals),
            "with_done_when": sum(1 for g in goals if g.get("done_when")),
            "candidates_near_a_held_goal": sum(1 for g in goals if g.get("near"))}


def tick(now: float | None = None) -> dict | None:
    """One register pass: build, merge, log, save. Returns the summary, or None when switched off.
    NonLiveWriteError (the write fence) propagates: a non-live importer must not write data/."""
    if not GOALS_SHADOW:
        return None
    now = time.time() if now is None else now
    from core import profile
    reg_path = profile.guard_path(register_path())      # resolved BEFORE any I/O (write-fence convention)
    lg_path = profile.guard_path(log_path())
    prev = _read_json(reg_path, {})
    prev_goals = {g["id"]: g for g in (prev.get("goals") or []) if isinstance(g, dict) and g.get("id")}
    goals, ended, rows = _merge(prev_goals, build(now), now)
    summ = _summary(goals)
    first = not prev
    rows.append({"ts": now, "event": "tick", "first": first, **summ, "ended": len(ended)})
    ended_all = (list(prev.get("ended") or []) + ended)[-ENDED_KEEP:]
    for g in goals:
        g.pop("_cycles", None)
        g.pop("_trains", None)
    lg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lg_path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # Phase 6 (core/goal_change.py, SHADOW): a held goal that ended is compared, by a judge other than him, with
    # its first wording; handed to its own thread, never awaited here. A failure never costs the register its save.
    try:
        from core import goal_change
        recs = [goal_change.end_record(e, e.get("ended_standing") or "", e.get("ended_why") or "")
                for e in ended if goal_change.eligible(e)]
        if recs:
            goal_change.record_later(recs)
    except Exception as exc:
        logger.warning("[goals] what-changed queue failed (non-fatal): %s: %s", type(exc).__name__, exc)
    # Phase 1 (core/goal_offer.py): the would-offer shadow row. Runs after this pass's rows are on disk (its
    # progress-rate window reads them). A failure here never costs the register its save.
    offer_state = prev.get("offer_state") or {}
    try:
        from core import goal_offer
        row, offer_state = goal_offer.shadow_pass(goals, rows, now, offer_state)
        if row is not None:
            goal_offer.write_row(row)
    except Exception as exc:
        logger.warning("[goals] offer shadow pass failed (non-fatal): %s: %s", type(exc).__name__, exc)
    reg = {"schema": SCHEMA, "ts": now, "summary": summ, "goals": goals, "ended": ended_all,
           "offer_state": offer_state}
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = reg_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(reg_path)
    return summ


_last_tick = 0.0
_thread: threading.Thread | None = None


def _run(now: float) -> None:
    try:
        tick(now)
    except Exception as exc:                      # includes NonLiveWriteError: logged, never raised into the loop
        logger.warning("[goals] shadow tick failed (non-fatal): %s: %s", type(exc).__name__, exc)


def tick_async(now: float | None = None) -> bool:
    """Heartbeat entry point. At most one pass per TICK_EVERY_S and never two at once. Returns True if a pass
    was started. Never raises."""
    global _last_tick, _thread
    try:
        if not GOALS_SHADOW:
            return False
        now = time.time() if now is None else now
        if now - _last_tick < TICK_EVERY_S or (_thread is not None and _thread.is_alive()):
            return False
        _last_tick = now
        _thread = threading.Thread(target=_run, args=(now,), name="goals-shadow", daemon=True)
        _thread.start()
        return True
    except Exception:
        return False


def status() -> dict:
    """The last saved summary (for a pulse or a HUD card; never for a prompt)."""
    reg = _read_json(register_path(), {})
    return {"ts": reg.get("ts"), **(reg.get("summary") or {}), "ended_kept": len(reg.get("ended") or [])}

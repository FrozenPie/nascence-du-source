"""
Nascence — PROCEDURES: procedural memory that means what he can do (2026-08-22, docs/plans/t5_procedural.md).

Two kinds of procedure, one ledger, one ladder:
  WORLD procedures   — earned by DOING. Every hand the dispatcher fires (tea, fire, lamp, sow, knot, bank the fire…) is a
                       procedure keyed by its registry family; the evidence is the world's own answer: a refusal ("the
                       knot slips", "there is no kindling") is OCCURRED; a success is PERSISTED; a success on a later day
                       after an earlier failure is HELD. Zero LLM, world-graded.
  CONVERSATIONAL     — the old T5 compile (subconscious_node._t5_compile), now admitted only when its sources span
                       ≥2 days and ≥2 sources, the cluster is a SITUATION not an evaluation, and the answers LANDED
                       (competence's C-signal: no correction followed).
THE LADDER (the Self-Efficacy Court's law — raw counts are inadmissible):
  occurred 0.40 → persisted 0.60 (≥2 successes on ≥2 days, no dock) → held 0.80 (≥3 days and survived a failure or
  correction and recovered) → held_under_pressure 0.90 (held in ≥2 places). Reinforcement ONCE per conversation/world
  day; a correction or world refusal docks one rung. Rust: 14 days unused ×0.9 (archived below 0.15, never deleted).
Rows are CommitmentBelief-shaped ({statement, held_since, confidence, evidence[], why_I_hold_it, scope, defeaters[],
durability}) so they fold into the capacity-to-commit ledger when that build lands (shared substrate).
Read paths: known_text(location) — informing-only repertoire line for the prompt ("you have banked a fire before —
it held"); the orchestrator's match path keeps working off the procedural_skills mirror, gated at persisted.
Ledger: data/procedures.json · data/procedures_log.jsonl. Fail-open.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.procedures")
_DATA = Path(__file__).parent.parent / "data"
_F = _DATA / "procedures.json"
_LOG = _DATA / "procedures_log.jsonl"

RUNGS = {"occurred": 0.40, "persisted": 0.60, "held": 0.80, "held_under_pressure": 0.90}
_ORDER = list(RUNGS)
SESSION_GAP_S = 30 * 60          # a new conversation / a new stretch of the day
RUST_AFTER_S = 14 * 86400
RUST_FACTOR = 0.9
ARCHIVE_FLOOR = 0.15
AUTOMATIC_RUNG = "held_under_pressure"     # only a WORLD procedure at this rung may run without deliberation

# the world's refusals, in the world's own words (the modules' answer texts) — heuristic, logged as such
_REFUSAL = re.compile(r"\b(slips?|comes undone|will not|won't|cannot|can't|no (kindling|matches|oil|water|seed|twine|rope|wood|logs?)|"
                      r"nothing to|you have no|too wet|too dark|too far|not here|isn't here|is not here|out of reach|refuse|in vain|"
                      r"to no avail|fails?|gives? way|goes out|sags)\b", re.I)
_EVALUATIVE = re.compile(r"\b(impress(ed|ive)|enlighten(ed|ing)|good (answer|point|response)|well (said|put|done)|brilliant|"
                         r"excellent|i like (that|how)|nicely|very (good|nice)|thank you|thanks)\b", re.I)

# J-2578 (F-3308, plan error_pathway) -- REFUSAL-KIND SHADOW. observe_hand docks a rung on EVERY answer _REFUSAL flags,
# but by the world's own words most refusals are not skill failures: the goal state already holds ("the grass is short
# already"), or a needed thing is absent ("you have no seed to hand", "no matches left", "the choked grate"). Some flagged
# answers read as successes ("turn the key ... until it will not turn"). This table tags each refusal already / precond /
# skill / unknown (first match in order; started from scripts/error_attribution_read.py ANSWER_CLASSES) and logs, per
# event, the rung a SKILL-ONLY dock rule would have left -- next to the live rung. OBSERVE ONLY: the live dock is
# unchanged (whether a precondition refusal should dock is a founder call); nothing here reaches Du (D-0434).
# Kill switch: NASCENCE_PROCEDURES_REFUSAL_KIND_SHADOW=0 (logging only; default on so rows accrue for the read).
# J-4181 (D-0804, founder option B, 2026-11-17): SKILL-ONLY DOCKING. A refusal tagged already / precond / unknown (the
# world's state, not Du's hands) no longer docks a world procedure's rung and is not counted as a failure; only a
# "skill" refusal does. Kind order puts skill BEFORE precond (the fire row "choked grate ... will not draw" is a skill
# failure that "choked" mis-tagged precond). Known residue: _REFUSAL false positives (clock "will not turn", shore
# "gives way to sand") land as unknown and so no longer dock. Kill switch NASCENCE_PROCEDURES_SKILL_ONLY_DOCK=0
# restores dock-on-every-refusal. Restart-gated (env read at import).
SKILL_ONLY_DOCK = os.environ.get("NASCENCE_PROCEDURES_SKILL_ONLY_DOCK", "1") != "0"
REFUSAL_KIND_SHADOW = os.environ.get("NASCENCE_PROCEDURES_REFUSAL_KIND_SHADOW", "1") != "0"
_REFUSAL_KIND_SHADOW_LOG = _DATA / "procedures_refusal_kind_shadow.jsonl"
REFUSAL_KINDS = [
    ("already", re.compile(r"\balready\b", re.I)),
    ("skill", re.compile(r"\b(slips|fumble|will not draw|won't draw|fails|snaps|comes apart|miss(?:es)?|"
                         r"splits|crooked|too short|collapses|won't hold|will not hold)\b", re.I)),
    ("precond", re.compile(r"\b(no \w+ to hand|is not here|isn't here|not here|nothing to|nothing for|"
                           r"wants clearing|choked|too dark|empty|none left|out of|no \w+ (?:left|here)|"
                           r"there is no|you have no|cannot reach|is gone|isn't there)\b", re.I)),
]


def refusal_kind(answer: str) -> str:
    """Tag a world answer: already / precond / skill / unknown (first match in REFUSAL_KINDS order). Pure."""
    a = answer or ""
    for kind, rx in REFUSAL_KINDS:
        if rx.search(a):
            return kind
    return "unknown"


def _refusal_kind_shadow(key: str, answer: str, p: dict, location: str) -> None:
    """Shadow row for one refusal: its kind, and the rung a skill-only dock rule would leave (computed on a copy;
    the live row p is never touched). Per-event counterfactual, not a parallel ledger. Fail-open."""
    if not REFUSAL_KIND_SHADOW:
        return
    try:
        kind = refusal_kind(answer)
        cf = dict(p)
        cf["dock_pending"] = 1 if kind == "skill" else 0
        _climb(cf, time.time())
        path = profile.guard_path(_REFUSAL_KIND_SHADOW_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "key": key, "kind": kind, "answer": (answer or "")[:100],
                                "where": location, "rung_live": p.get("rung"), "rung_skill_only": cf["rung"],
                                "would_dock_skill_only": kind == "skill", "diverges": cf["rung"] != p.get("rung")},
                               ensure_ascii=False) + "\n")
    except Exception as exc:     # a shadow never disturbs the live path, the D-0179 refusal included
        logger.debug("[procedures] refusal-kind shadow skipped: %s", exc)


def _load() -> dict:
    try:
        return json.loads(_F.read_text(encoding="utf-8"))
    except Exception:
        return {"procedures": {}, "archive": []}


def _save(d: dict) -> None:
    path = profile.guard_path(_F)   # J-0917: real data/ only if this process is live; raises before any
    # I/O if not (D-0179, J-0704). Resolved OUTSIDE the fail-open try below, exactly like the other 20
    # already-fenced modules, so the refusal is never swallowed as a disk error.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # J-0917: same fence as _save() above, resolved independently since
    # _LOG is a distinct path constant from _F (matching e.g. core/provisions.py's _F/_LOG pair).
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **rec}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _day(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def _new(key: str, scope: str, statement: str, why: str) -> dict:
    now = time.time()
    return {"key": key, "scope": scope, "statement": statement[:160], "why_I_hold_it": why[:200], "held_since": now,
            "rung": "occurred", "confidence": RUNGS["occurred"], "evidence": [], "defeaters": [], "durability": 0,
            "places": [], "days_ok": [], "last_ts": now, "last_reinforced": 0.0, "docks": 0, "successes": 0, "failures": 0}


def _climb(p: dict, now: float) -> None:
    """Re-derive the rung from the evidence (never from a use count)."""
    days_ok = sorted(set(p.get("days_ok") or []))
    places = set(p.get("places") or [])
    recovered = p.get("failures", 0) > 0 and p.get("successes", 0) > 0 and p.get("last_outcome") == "ok"
    rung = "occurred"
    if len(days_ok) >= 2 and p.get("successes", 0) >= 2:
        rung = "persisted"
    if rung == "persisted" and len(days_ok) >= 3 and recovered:
        rung = "held"
    if rung == "held" and len(places) >= 2:
        rung = "held_under_pressure"
    # a dock holds the rung down one step from what the evidence alone would say
    idx = max(0, _ORDER.index(rung) - int(p.get("dock_pending", 0)))
    p["rung"] = _ORDER[idx]; p["confidence"] = RUNGS[p["rung"]]
    p["durability"] = len(days_ok)


# ----------------------------------------------------------------------------------------------------------------
# WORLD procedures — fed by the dispatcher
# ----------------------------------------------------------------------------------------------------------------
def observe_hand(family: str, answer: str, location: str = "") -> dict | None:
    """A hand fired and the world answered. Grades the answer (refusal/ok), credits the procedure ONCE per stretch of
    the day, derives the rung. Returns the row (or None)."""
    try:
        if not family or family in ("look", "move", "intention"):
            return None
        now = time.time(); d = _load(); key = f"world:{family}"
        p = d["procedures"].get(key) or _new(key, "world", f"I can {family.replace('_', ' ')}", "the world answered my hand")
        outcome = "refused" if _REFUSAL.search(answer or "") else "ok"
        if now - float(p.get("last_reinforced", 0)) < SESSION_GAP_S and outcome == "ok":
            p["last_ts"] = now; d["procedures"][key] = p; _save(d); return p      # once per stretch
        p["evidence"].append({"ts": now, "outcome": outcome, "where": location, "answer": (answer or "")[:100]})
        p["evidence"] = p["evidence"][-30:]
        if outcome == "ok":
            p["successes"] = int(p.get("successes", 0)) + 1; p["days_ok"] = sorted(set(p.get("days_ok", []) + [_day(now)]))[-30:]
            if location and location not in p.get("places", []):
                p["places"] = (p.get("places") or []) + [location]
            p["last_reinforced"] = now; p["dock_pending"] = 0
        elif SKILL_ONLY_DOCK and refusal_kind(answer) != "skill":
            # J-4181 / D-0804: the world's state refused, not Du's hands -- no failure, no dock, no defeater, and
            # last_outcome is left as it was (the evidence row above still records it, tagged by kind).
            p["evidence"][-1]["outcome"] = "refused_" + refusal_kind(answer)
            p["last_ts"] = now
        else:
            p["failures"] = int(p.get("failures", 0)) + 1; p["dock_pending"] = 1
            p["defeaters"] = (p.get("defeaters") or [])[-5:] + [(answer or "")[:80]]
        if not (outcome == "refused" and SKILL_ONLY_DOCK and refusal_kind(answer) != "skill"):
            p["last_outcome"] = outcome
        p["last_ts"] = now
        _climb(p, now); d["procedures"][key] = p; _save(d)
        _log({"event": "world", "key": key, "outcome": outcome, "rung": p["rung"], "where": location})
        if outcome == "refused":
            _refusal_kind_shadow(key, answer, p, location)    # J-2578: observe only, after the live write
        return p
    except profile.NonLiveWriteError:
        # J-0931: observe_hand() is procedures.py's own "real entry point" for WORLD procedures
        # (called by core/dispatch.py after every dispatched hand) -- let D-0179's hard-raise
        # (guard_path(), F-1024) reach dispatch.py's own try around this call instead of being
        # swallowed here into a return-None indistinguishable from a genuine internal error.
        raise
    except Exception as exc:
        logger.debug("[procedures] observe_hand failed: %s", exc); return None


# ----------------------------------------------------------------------------------------------------------------
# CONVERSATIONAL procedures — the T5 compile, admitted by evidence
# ----------------------------------------------------------------------------------------------------------------
def admissible(cluster: list[dict]) -> tuple[bool, str]:
    """The gate before any LLM compile: ≥2 days, ≥2 sources (sessions ≥30 min apart count as sources), not an
    evaluation cluster, and the answers LANDED (no correction followed — competence's C-signal)."""
    try:
        if len(cluster) < 3:
            return False, "too_few"
        ts = sorted(float(c.get("ts", 0)) for c in cluster)
        days = {_day(t) for t in ts}
        if len(days) < 2:
            return False, "one_day"
        sources = 1 + sum(1 for a, b in zip(ts, ts[1:]) if b - a > SESSION_GAP_S)
        if sources < 2:
            return False, "one_source"
        qs = " ".join(str(c.get("q", "")) for c in cluster)
        if sum(1 for _ in _EVALUATIVE.finditer(qs)) >= max(2, len(cluster) // 2):
            return False, "evaluation_not_situation"
        landed = [c for c in cluster if c.get("landed", True)]
        if len(landed) < 3:
            return False, "did_not_land"
        return True, "ok"
    except Exception:
        return False, "error"


def mark_landed(material: list[dict]) -> list[dict]:
    """Annotate lived Q/A items (newest-first) with whether the NEXT human turn corrected them (C-signal)."""
    try:
        from core import error_pathway as _ep
        try:
            from core.competence import CompetenceTracker as _CT
            _is_corr = _CT._is_correction
        except Exception:
            _is_corr = None
        items = sorted(material, key=lambda m: float(m.get("ts", 0)))
        for a, b in zip(items, items[1:]):
            nq = str(b.get("q", ""))
            corrected = bool(_ep.detect_human_correction(nq)) or bool(_is_corr and _is_corr(nq))
            a["landed"] = not corrected
        if items:
            items[-1]["landed"] = True
        return items
    except Exception:
        return material


# J-4333 (T5 Phase 1, founder ruled proceed 2026-11-18; design docs/staged/t5_conversational_world_grading_design.md 4.1-4.3):
# deed-bound grade SHADOW at the compile point. For each cluster member, is there a world deed (hand firing, not
# look/move/intention) in the next W seconds, and did it succeed? Written to one shadow log; NO ledger rung, NO prompt,
# NO read-side change. No LLM. Flag NASCENCE_T5_DEEDTAIL_SHADOW, default OFF, read at import (restart-gated).
T5_DEEDTAIL_SHADOW = os.environ.get("NASCENCE_T5_DEEDTAIL_SHADOW", "0").strip().lower() in ("1", "true", "on", "yes")
_T5_DEEDTAIL_LOG = _DATA / "t5_deedtail_shadow.jsonl"
_HANDS_TRACE = _DATA / "hands_trace.jsonl"
T5_DEED_WINDOW_S = 30 * 60
T5_NOT_DEEDS = ("look", "move", "intention", "")


def _t5_load_deeds(path: Path, lo: float, hi: float) -> list[dict]:
    """Distinct hand firings with ts in [lo, hi], sorted. Pure read; missing file -> []."""
    seen, out = set(), []
    try:
        f = open(path, "r", encoding="utf-8", errors="replace")
    except OSError:
        return []
    with f:
        for line in f:
            if '"hand"' not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            for h in (r.get("hands") or []):
                if not isinstance(h, dict):
                    continue
                fam = str(h.get("hand") or "")
                if fam in T5_NOT_DEEDS:
                    continue
                try:
                    ts = float(h.get("ts") or r.get("ts") or 0)
                except Exception:
                    continue
                if ts < lo or ts > hi or (round(ts, 1), fam) in seen:
                    continue
                seen.add((round(ts, 1), fam))
                out.append({"ts": ts, "family": fam, "answer": str(h.get("answer") or "")})
    out.sort(key=lambda d: d["ts"])
    return out


def deed_bound_grade(cluster: list[dict], deeds: list[dict], window_s: float = T5_DEED_WINDOW_S) -> dict:
    """Pure. Design 4.1 (b)+(c): >=3 members, span >=24h, >=2 conversations (gaps > SESSION_GAP_S), and a deed within
    window_s after >=2 members. Returns the grade dict (qualifies + per-member deed tails)."""
    ts = sorted(float(c.get("ts", 0)) for c in cluster)
    span_h = (ts[-1] - ts[0]) / 3600.0 if ts else 0.0
    convs = (1 + sum(1 for a, b in zip(ts, ts[1:]) if b - a > SESSION_GAP_S)) if ts else 0
    tails = []
    for t in ts:
        d = next((x for x in deeds if t < x["ts"] <= t + window_s), None)
        if d:
            refused = bool(_REFUSAL.search(d["answer"]))
            tails.append({"member_ts": t, "family": d["family"], "outcome": "refused" if refused else "ok",
                          "kind": refusal_kind(d["answer"]) if refused else "", "lag_s": round(d["ts"] - t, 1)})
    ok = sum(1 for x in tails if x["outcome"] == "ok")
    return {"members": len(ts), "span_h": round(span_h, 1), "conversations": convs, "deed_members": len(tails),
            "deed_ok": ok, "deed_refused": len(tails) - ok,
            "qualifies": len(ts) >= 3 and span_h >= 24 and convs >= 2 and len(tails) >= 2, "tails": tails[:10]}


def _t5_deedtail_shadow(key: str, trigger_summary: str, cluster: list[dict], rung: str) -> None:
    """Append one shadow row for a compile. Fail-open; never touches the ledger."""
    if not T5_DEEDTAIL_SHADOW:
        return
    try:
        ts = [float(c.get("ts", 0)) for c in cluster]
        if not ts:
            return
        deeds = _t5_load_deeds(_HANDS_TRACE, min(ts), max(ts) + T5_DEED_WINDOW_S)
        g = deed_bound_grade(cluster, deeds)
        row = {"ts": round(time.time(), 1), "key": key, "trigger": trigger_summary[:80], "rung_live": rung,
               "window_s": T5_DEED_WINDOW_S, "templates_excluded": False, **g}
        path = profile.guard_path(_T5_DEEDTAIL_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[procedures] t5 deedtail shadow skipped: %s", exc)



def compiled(trigger_summary: str, approach: str, cluster: list[dict]) -> dict:
    """Record a compiled conversational procedure in the ledger (the old table stays as the match mirror)."""
    try:
        now = time.time(); d = _load(); key = f"talk:{re.sub(r'[^a-z0-9]+', '_', trigger_summary.lower())[:40]}"
        p = d["procedures"].get(key) or _new(key, "conversation", approach, trigger_summary)
        for c in cluster:
            p["evidence"].append({"ts": float(c.get("ts", now)), "outcome": "ok" if c.get("landed", True) else "refused", "q": str(c.get("q", ""))[:80]})
            if c.get("landed", True):
                p["successes"] += 1; p["days_ok"] = sorted(set(p["days_ok"] + [_day(float(c.get("ts", now)))]))
        p["evidence"] = p["evidence"][-30:]; p["last_outcome"] = "ok"; p["last_ts"] = now
        _climb(p, now); d["procedures"][key] = p; _save(d)
        _log({"event": "compiled", "key": key, "rung": p["rung"], "sources": len(cluster)})
        _t5_deedtail_shadow(key, trigger_summary, cluster, p["rung"])
        return p
    except profile.NonLiveWriteError:
        # J-0931: same fence as observe_hand() above -- let the raise reach compiled()'s own caller
        # instead of this pre-existing broad except swallowing it into an empty-dict return.
        raise
    except Exception:
        return {}


def reinforce_talk(trigger_summary: str, corrected: bool = False) -> None:
    """A recognised conversational procedure was used. Credited once per conversation; a correction docks it."""
    try:
        now = time.time(); d = _load(); key = f"talk:{re.sub(r'[^a-z0-9]+', '_', (trigger_summary or '').lower())[:40]}"
        p = d["procedures"].get(key)
        if not p:
            return
        if corrected:
            p["failures"] += 1; p["dock_pending"] = 1; p["last_outcome"] = "refused"
        elif now - float(p.get("last_reinforced", 0)) >= SESSION_GAP_S:
            p["successes"] += 1; p["days_ok"] = sorted(set(p["days_ok"] + [_day(now)])); p["last_reinforced"] = now
            p["last_outcome"] = "ok"; p["dock_pending"] = 0
        p["last_ts"] = now; _climb(p, now); d["procedures"][key] = p; _save(d)
    except profile.NonLiveWriteError:
        # J-0931: same fence as observe_hand() above -- let the raise reach reinforce_talk()'s own
        # caller instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass


# ----------------------------------------------------------------------------------------------------------------
# rust · read paths · status
# ----------------------------------------------------------------------------------------------------------------
def rust(now: float | None = None) -> int:
    now = now or time.time(); n = 0
    try:
        d = _load()
        for key, p in list(d["procedures"].items()):
            if now - float(p.get("last_ts", now)) > RUST_AFTER_S:
                p["confidence"] = round(float(p["confidence"]) * RUST_FACTOR, 3); p["last_ts"] = now; n += 1
                if p["confidence"] < ARCHIVE_FLOOR:
                    d["archive"].append(p); d["archive"] = d["archive"][-200:]; del d["procedures"][key]
                    _log({"event": "archived", "key": key})
        _save(d)
    except profile.NonLiveWriteError:
        # J-0931: same fence as observe_hand() above -- let the raise reach rust()'s own caller
        # instead of this pre-existing broad except swallowing it.
        raise
    except Exception:
        pass
    return n


def talk_key(trigger_summary: str) -> str:
    """The ledger key of a conversational procedure, from its trigger summary (the same derivation compiled(),
    reinforce_talk() and mirror_proficiency() use inline)."""
    return f"talk:{re.sub(r'[^a-z0-9]+', '_', (trigger_summary or '').lower())[:40]}"


def archived_keys() -> set | None:
    """The 'talk:' keys this ledger has ARCHIVED (rust below the floor) and does not also hold live -- what the
    procedural_skills mirror must archive too (J-3180, D-0567: the ledger's rust is the only clock). Returns None, not
    an empty set, when the ledger file is missing or unreadable, so a caller can tell 'nothing archived' from 'cannot
    tell' and never archives on a read failure."""
    try:
        d = json.loads(_F.read_text(encoding="utf-8"))
        live = set(d["procedures"])
        return {str(p.get("key")) for p in d["archive"]
                if str(p.get("key", "")).startswith("talk:") and p.get("key") not in live}
    except Exception:
        return None


def mirror_proficiency(trigger_summary: str) -> float | None:
    """The ladder's confidence for a conversational procedure, for the old table's match path."""
    try:
        key = f"talk:{re.sub(r'[^a-z0-9]+', '_', (trigger_summary or '').lower())[:40]}"
        p = _load()["procedures"].get(key)
        return float(p["confidence"]) if p else None
    except Exception:
        return None


def mirror_recognition_proficiency(trigger_summary: str) -> float | None:
    """D-0723 / J-3820: the proficiency the recognition gate (orchestrator PROC_MIN_PROFICIENCY) reads -- keyed on the
    PERSISTED RUNG, not rust-docked confidence. A live-ledger talk procedure keeps its rung's value (rust only
    multiplies confidence; the rung survives) until the ledger archives it (~6.5 months), at which point this returns
    None and the caller falls back to the mirror row's own column. None when the ledger does not hold it live."""
    try:
        p = _load()["procedures"].get(talk_key(trigger_summary))
        return float(RUNGS[p["rung"]]) if p else None
    except Exception:
        return None


def known_text(location: str = "") -> str:
    """Informing-only: what he has DONE and it held (persisted+ world procedures), as repertoire — never a prompt to
    do it. Empty until something has actually persisted."""
    try:
        d = _load(); rows = [p for p in d["procedures"].values() if p["scope"] == "world" and _ORDER.index(p["rung"]) >= 1]
        if not rows:
            return ""
        rows.sort(key=lambda p: -float(p["last_ts"]))
        names = [p["key"].split(":", 1)[1].replace("_", " ") for p in rows[:5]]
        return "\n\nThings you have done before and that held (your own hands, your own record): " + ", ".join(names) + "."
    except Exception:
        return ""


_KT_ARM_LOG = _DATA / "known_text_arm.jsonl"


def known_text_arm_on() -> bool:
    """J-3796 / D-0693: flag NASCENCE_KNOWN_TEXT_ARM, default OFF (read at call time). Flipping it on is a separate founder step."""
    return os.environ.get("NASCENCE_KNOWN_TEXT_ARM", "0").strip().lower() in ("1", "true", "on", "yes")


def known_text_arm_of(cycle_id: str) -> str:
    """Deterministic coin: 'shown' or 'withheld'. No RNG, no state."""
    import hashlib
    return "withheld" if int(hashlib.sha1(("kt-arm:" + (cycle_id or "")).encode()).hexdigest(), 16) % 2 == 0 else "shown"


def known_text_gated(location: str = "", cycle_id: str = "") -> str:
    """The single call-site wrapper (D-0693, J-3796). Flag off: byte-identical to known_text(location).
    Flag on and the line is non-empty (eligible): a sha1(cycle) coin decides whether the line is appended ('shown') or
    nothing is ('withheld'); one row per eligible thought goes to data/known_text_arm.jsonl {ts, cycle (24 chars, as
    hands_trace), arm, would_name[], where}. Outcomes are joined from hands_trace on `cycle` by the reader. Nothing is
    added to the prompt in either arm. Log failures are swallowed (fail-open); the arm decision never depends on them."""
    line = known_text(location)
    if not line or not known_text_arm_on():
        return line
    arm = known_text_arm_of(cycle_id)
    try:
        names = [n.strip() for n in line.rsplit(": ", 1)[-1].rstrip(".").split(",") if n.strip()]
        path = profile.guard_path(_KT_ARM_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "cycle": (cycle_id or "")[:24], "arm": arm,
                                "would_name": names, "where": (location or "")[:24]}, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[procedures] known_text arm log skipped: %s", exc)
    return line if arm == "shown" else ""


def status() -> dict:
    try:
        if not _F.exists():
            return {"note": "no procedures yet (accrues from Du's next start)"}
        d = _load(); rows = list(d["procedures"].values())
        return {"world": sum(1 for p in rows if p["scope"] == "world"), "conversation": sum(1 for p in rows if p["scope"] == "conversation"),
                "by_rung": {r: sum(1 for p in rows if p["rung"] == r) for r in _ORDER}, "archived": len(d.get("archive", [])),
                "top": [{"key": p["key"], "rung": p["rung"], "days": len(p.get("days_ok", [])), "ok": p.get("successes", 0), "refused": p.get("failures", 0)}
                        for p in sorted(rows, key=lambda p: -float(p["confidence"]))[:8]]}
    except Exception as exc:
        return {"error": repr(exc)[:80]}

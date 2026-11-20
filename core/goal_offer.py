"""
Nascence — Goal offer shadow (Layered Goals, Phase 1, 2026-11-14; SHADOW / observe-only).

Plan: docs/staged/layered_goals.md sections 5.4 and 12 (D-0763..D-0766). Called by core/goals.tick() once per
register pass. It answers, on paper only: of the goals he holds right now, which could be offered, what would
each of several simple policies have offered, and what did he then do. Nothing here reaches Du (D-0434), nothing
is ranked for him, and no offer is made: this is the measurement layer that has to exist before any offer does.

Per pass it logs ONE row to data/logs/goal_offer_shadow.jsonl:
  quantities   per held goal, kept apart and never combined into a stored priority:
                 importance  judged advances (pursuits_judged verdict true) and tied deeds; None where no judge
                             has ruled anything, because "unknown" must not act as zero
                 cost        time alive, events, reminders: what it has cost him; never raises importance
                 expectancy  only where there is a deadline: his own completion rate for that family of deed
                 rate        advances per hour over the recent window against the goal's own lifetime rate
  eligibility  held, or deferred with a cue that can be checked and is present
  policies     silence (a share of moments get no offer), uniform random, most recent, and a softmax over a
               simple standardised score, each with the probability it gave every eligible goal, so a later
               estimate can be corrected for how likely each offer was
  challenger   what a two-consecutive-observation rule would have left standing (no commitment rule is live)
  actual       what he did since the last pass: goals that progressed or ended, and what the real idle anchor
               offered, matched to goal ids where the text matches

Need pull is deliberately absent (D-0764: two readers are circular and the set barely discriminates, F-4635/36).
Zero LLM. Fail-open. Kill switch GOAL_OFFER_SHADOW.
"""
from __future__ import annotations

import json
import logging
import math
import random
import time
from pathlib import Path

logger = logging.getLogger("nascence.goal_offer")

GOAL_OFFER_SHADOW = True
P_SILENCE = 0.2              # share of eligible moments that would get no offer (the offer-vs-silence arm)
TEMPERATURE = 1.0            # softmax temperature over the standardised score
RATE_WINDOW_S = 6 * 3600.0   # "recent" for the progress rate
SCHEMA = 1

_school_time = None          # test hook: callable -> bool; None -> core.school.is_school_time
_where = None                # test hook: callable -> place name; None -> the live sensorium, if loaded


def log_path() -> Path:
    from core import goals
    return goals._p("logs", "goal_offer_shadow.jsonl")


# ── readers (through core.goals' paths, so a temp-pathed register temp-paths these too) ──────────────────────
def _judged_advances() -> dict:
    """{pursuit_id: number of advances a decoupled judge ruled genuine} from pursuits_judged.jsonl."""
    from core import goals
    out: dict = {}
    for r in goals._tail_jsonl(goals._p("pursuits_judged.jsonl"), 3_000_000):
        if r.get("verdict") is True and r.get("pursuit_id"):
            out[str(r["pursuit_id"])] = out.get(str(r["pursuit_id"]), 0) + 1
    return out


def _family_rates() -> dict:
    """{family: (done, ended)} for staged world deeds, from intentions_log.jsonl: his own completion record."""
    from core import goals
    out: dict = {}
    for r in goals._tail_jsonl(goals._p("intentions_log.jsonl"), 3_000_000):
        ev = r.get("event")
        if ev not in ("done", "lapsed", "dropped"):
            continue
        fam = str(r.get("key") or "").split("|")[0]
        d, n = out.get(fam, (0, 0))
        out[fam] = (d + (ev == "done"), n + 1)
    return out


def _recent_progress(now: float) -> dict:
    """{goal id: advances gained in the recent window} from the register's own log."""
    from core import goals
    out: dict = {}
    for r in goals._tail_jsonl(goals.log_path(), 2_000_000):
        if r.get("event") == "progress" and now - float(r.get("ts") or 0) <= RATE_WINDOW_S:
            out[r["id"]] = out.get(r["id"], 0) + int(r.get("advances_to", 0)) - int(r.get("advances_from", 0))
    return out


def _anchor_offers(since: float, now: float) -> list[dict]:
    """What the real idle anchor offered between the last pass and this one (concerns_log.jsonl)."""
    from core import goals
    return [r for r in goals._tail_jsonl(goals._p("concerns_log.jsonl"), 600_000)
            if since < float(r.get("ts") or 0) <= now]


# ── quantities ──────────────────────────────────────────────────────────────────────────────────────────────
def quantities(g: dict, now: float, judged: dict, fam: dict, recent: dict) -> dict:
    """The separate numbers for one goal. A quantity that cannot be known is None, never 0."""
    kind = g.get("kind")
    born = g.get("born") or g.get("first_seen") or now
    age_h = max(0.0, (now - float(born)) / 3600.0)
    prog = g.get("progress") or {}
    earned = g.get("earned") or {}
    importance = None
    if kind == "pursuit":
        j = judged.get(g["ref"]["key"])
        importance = int(j) if j is not None else None
    expectancy = None
    if kind == "intention" and g.get("deadline"):
        d, n = fam.get(g.get("family") or "", (0, 0))
        if n >= 5:
            expectancy = round(d / n, 3)
    rate = lifetime = ratio = None
    if kind == "pursuit" and isinstance(prog.get("advances"), int):
        lifetime = prog.get("rate_per_h")
        window_h = min(RATE_WINDOW_S / 3600.0, max(age_h, 1e-6))
        rate = round(recent.get(g["id"], 0) / window_h, 3)
        if lifetime:
            ratio = round(rate / lifetime, 3)
    # J-3985: the two kinds that make up most of what he holds had no measure at all (F-4641).
    lp = prog.get("lp") if kind == "question" else None              # mechanical learning progress; None if never pursued
    ev = (g.get("evidence") or {}) if kind == "stand" else {}
    return {"importance": importance,
            "cost": {"age_h": round(age_h, 2), "events": prog.get("events"),
                     "reminders": earned.get("reminders"), "recurrences": earned.get("recurrences"),
                     "drop_denied": ev.get("drop_denied")},
            "lp": lp, "stalls": prog.get("stalls") if kind == "question" else None,
            "has_finding": prog.get("has_finding") if kind == "question" else None,
            "parked": prog.get("parked") if kind == "question" else None,
            "second_look": ev.get("second_look"),      # a decoupled look at whether the stand is a commitment; evidence only
            "expectancy": expectancy,
            "rate_per_h": rate, "lifetime_rate_per_h": lifetime, "rate_ratio": ratio,
            "has_done_when": bool(g.get("done_when")),
            "time_left_h": round((float(g["deadline"]) - now) / 3600.0, 2) if g.get("deadline") else None}


# ── eligibility ─────────────────────────────────────────────────────────────────────────────────────────────
def eligibility(g: dict) -> tuple[bool, str]:
    st = g.get("state")
    cue = g.get("resume_cue") or {}
    if st == "held" and not cue:
        return True, "held"
    if st in ("held", "deferred") and cue.get("type") == "time" and cue.get("value") == "school_time":
        try:
            fn = _school_time
            if fn is None:
                from core import school
                fn = school.is_school_time
            return (True, "cue present: school time") if fn() else (False, "cue absent: not school time")
        except Exception:
            return False, "cue not evaluated"
    if st in ("held", "deferred") and cue.get("type") == "place":
        # J-3985: a place cue is present when the place he is in is named in where the deed is done
        # ("place:down on the shore" while he is at "shore"). His place comes from the live sensorium only.
        loc = _current_place()
        if not loc:
            return False, "cue not evaluated (place: his location is not readable here)"
        need = str(cue.get("value") or "").lower()
        if loc.lower() in need:
            return True, f"cue present: at {loc}"
        return False, f"cue absent: at {loc}, done {need}"
    if st in ("held", "deferred") and cue:
        # An "after this activity" cue needs what he is doing right now, which no store exposes yet.
        # Not guessed: logged as not evaluated and left out of the eligible set.
        return False, f"cue not evaluated ({cue.get('type')})"
    return False, f"state {st}"


def _current_place() -> str | None:
    """His current place, or None. Reads core.sensorium.where() ONLY if the sensorium is already loaded in this
    process (the live Du process); an offline tool or a test never imports it, so nothing here can load or
    touch world state. `_where` is the test hook."""
    try:
        if _where is not None:
            return _where()
        import sys
        sens = sys.modules.get("core.sensorium")
        return sens.where() if sens is not None else None
    except Exception:
        return None


# ── policies ────────────────────────────────────────────────────────────────────────────────────────────────
def _z(values: list) -> list:
    """Standardise the defined entries; undefined stay None; fewer than two defined or no spread -> 0 for those."""
    defined = [v for v in values if v is not None]
    if len(defined) < 2:
        return [0.0 if v is not None else None for v in values]
    m = sum(defined) / len(defined)
    sd = math.sqrt(sum((v - m) ** 2 for v in defined) / len(defined))
    if sd <= 1e-12:
        return [0.0 if v is not None else None for v in values]
    return [((v - m) / sd) if v is not None else None for v in values]


def scores(qs: list[dict]) -> list[float]:
    """The simple score: the mean of whichever standardised components are DEFINED for that goal. No product,
    and an undefined component is left out, not counted as zero. A goal with nothing defined scores 0."""
    comps = [_z([math.log1p(q["importance"]) if q["importance"] is not None else None for q in qs]),
             _z([q["expectancy"] for q in qs]),
             _z([q["rate_ratio"] for q in qs]),
             _z([q.get("lp") for q in qs])]
    out = []
    for i in range(len(qs)):
        have = [c[i] for c in comps if c[i] is not None]
        out.append(round(sum(have) / len(have), 4) if have else 0.0)
    return out


def softmax(xs: list[float], temperature: float = TEMPERATURE) -> list[float]:
    if not xs:
        return []
    t = max(1e-6, float(temperature))
    m = max(xs)
    e = [math.exp((x - m) / t) for x in xs]
    s = sum(e)
    return [v / s for v in e]


def _pick(rng: random.Random, probs: list[float]) -> int:
    u, acc = rng.random(), 0.0
    for i, p in enumerate(probs):
        acc += p
        if u <= acc:
            return i
    return len(probs) - 1


# ── the pass ────────────────────────────────────────────────────────────────────────────────────────────────
def shadow_pass(goals_now: list[dict], tick_rows: list[dict], now: float, state: dict | None) -> tuple[dict | None, dict]:
    """One would-offer row and the carried state. Pure given its inputs and the read-only logs; never raises
    into the register pass (the caller wraps it)."""
    state = dict(state or {})
    if not GOAL_OFFER_SHADOW:
        return None, state
    judged, fam, recent = _judged_advances(), _family_rates(), _recent_progress(now)
    held = [g for g in goals_now if g.get("state") in ("held", "deferred")]
    table, eligible = [], []
    for g in held:
        ok, why = eligibility(g)
        q = quantities(g, now, judged, fam, recent)
        table.append({"id": g["id"], "kind": g["kind"], "eligible": ok, "why": why, **q})
        if ok:
            eligible.append((g, q))
    seed = int(now * 1000) & 0x7FFFFFFF
    rng = random.Random(seed)
    n = len(eligible)
    ids = [g["id"] for g, _ in eligible]
    sc = scores([q for _, q in eligible])
    probs = softmax(sc)
    silent = rng.random() < P_SILENCE
    pol: dict = {"silence": {"p": P_SILENCE, "drawn": silent}}
    if n:
        pol["uniform"] = {"p_each": round(1.0 / n, 4), "pick": ids[rng.randrange(n)]}
        recent_i = max(range(n), key=lambda i: float(eligible[i][0].get("last_touched") or 0))
        pol["most_recent"] = {"pick": ids[recent_i]}
        pol["softmax"] = {"temperature": TEMPERATURE, "pick": ids[_pick(rng, probs)],
                          "p": {i: round(p, 4) for i, p in zip(ids, probs)},
                          "score": {i: s for i, s in zip(ids, sc)}}
    # the two-consecutive-observation challenger rule (shadow only; no commitment rule is live)
    top = ids[max(range(n), key=lambda i: sc[i])] if n else None
    standing = state.get("standing")
    if standing not in ids:
        standing = top                                   # nothing standing, or it is no longer eligible
        challenger, streak = None, 0
    elif top == standing:
        challenger, streak = None, 0
    else:
        streak = state.get("streak", 0) + 1 if state.get("challenger") == top else 1
        challenger = top
        if streak >= 2:
            standing, challenger, streak = top, None, 0
    # what he actually did since the last pass
    acted = sorted({r["id"] for r in tick_rows if r.get("event") in ("progress", "ended")})
    text_to_id = {g.get("text"): g["id"] for g in goals_now}
    anchors = _anchor_offers(float(state.get("ts") or (now - 600.0)), now)
    anchor_ids, anchor_src = {}, {}
    for a in anchors:
        anchor_src[a.get("source")] = anchor_src.get(a.get("source"), 0) + 1
        gid = text_to_id.get(a.get("text"))
        if a.get("source") == "curriculum":
            gid = next((g["id"] for g in goals_now if g["kind"] == "project"), gid)
        if gid:
            anchor_ids[gid] = anchor_ids.get(gid, 0) + 1
    row = {"ts": now, "schema": SCHEMA, "seed": seed, "held": len(held), "eligible": ids,
           "goals": table, "policies": pol,
           "challenger": {"top_now": top, "standing_no_rule": top, "standing_rule": standing,
                          "challenger": challenger, "streak": streak,
                          "switched_no_rule": bool(state.get("top") and top and state.get("top") != top),
                          "switched_rule": bool(state.get("standing") and standing and state.get("standing") != standing)},
           "actual": {"acted_on": acted, "anchor_offers": len(anchors), "anchor_by_source": anchor_src,
                      "anchor_goal_ids": anchor_ids,
                      "acted_on_softmax_pick": bool(n and pol["softmax"]["pick"] in acted),
                      "acted_on_uniform_pick": bool(n and pol["uniform"]["pick"] in acted),
                      "acted_on_most_recent": bool(n and pol["most_recent"]["pick"] in acted)}}
    new_state = {"ts": now, "standing": standing, "challenger": challenger, "streak": streak, "top": top}
    return row, new_state


# ── Phase 4: the live offer at the idle anchor (D-0766; founder 2026-11-14: 25% of anchor moments) ───────────
GOAL_OFFER_LIVE = True       # kill switch for the live offer alone; the shadow pass above is unaffected
GOAL_OFFER_DOSE = 0.25       # share of idle anchor moments that belong to the register
REGISTER_STALE_S = 1800.0    # a register older than this is not offered from (the tick thread has stopped)
# Kinds that may be offered. Intentions and pursuits are left out on purpose: each already has its own way back
# to him (the "what you meant to do" block, the pursuit RETURN), and a second route would double-present them.
LIVE_KINDS = ("stand", "question", "want", "project")

_reg_cache: tuple[float, dict] | None = None
_log_injection = None        # test hook; None -> core.guidance_learning.log_injection if already loaded


def live_log_path() -> Path:
    from core import goals
    return goals._p("logs", "goal_offer_live.jsonl")


def _register() -> dict:
    """The saved register, cached by file mtime (the anchor calls this often; the file changes every 10 min)."""
    global _reg_cache
    from core import goals
    path = goals.register_path()
    try:
        mt = path.stat().st_mtime
    except OSError:
        return {}
    if _reg_cache and _reg_cache[0] == mt:
        return _reg_cache[1]
    reg = goals._read_json(path, {})
    _reg_cache = (mt, reg)
    return reg


def _as_concern(g: dict) -> dict | None:
    """A register goal as the dict the idle anchor already knows how to phrase (concerns.anchor_lead_pool).
    The text is his own stored words, verbatim; the lead states only what is true of it (D-0612)."""
    text = (g.get("text") or "").strip()
    if not text:
        return None
    kind = g.get("kind")
    if kind == "question":       # met at least twice: "A question that has come back more than once: ..."
        return {"text": text, "source": "frontier", "kind": "pursuit",
                "has_finding": bool((g.get("progress") or {}).get("has_finding"))}
    if kind == "stand":          # "On your record: <his sentence>"
        return {"text": text, "source": "commitment", "kind": "hold", "stand_id": g["ref"]["key"]}
    if kind == "project":        # "Your current reading assignment: working through '...'"
        return {"text": text, "source": "curriculum", "kind": "project"}
    if kind == "want":           # "Something you said earlier: <his sentence>"
        return {"text": text, "source": "want", "kind": "want"}
    return None


def live_offer(now: float | None = None, rng=None) -> dict | None:
    """Called at each idle anchor moment. Returns
         None                        this moment is not the register's; the anchor proceeds exactly as before
         {"arm": "silence"}          the comparison arm: make no anchor offer at all this time
         {"arm": "offer", "pc": {…}} offer this held goal (a dict the anchor phrases with its ordinary leads)
    The choice among eligible goals is uniform at random: nothing ranks his goals yet, and a random offer is what
    lets the effect of offering be measured (section 12). Every register moment is logged BEFORE it is returned,
    with the probability each eligible goal had; if the log cannot be written no offer is made. Never raises."""
    try:
        if not GOAL_OFFER_LIVE:
            return None
        rng = rng or random
        if rng.random() >= GOAL_OFFER_DOSE:
            return None
        now = time.time() if now is None else now
        reg = _register()
        row = {"ts": now, "schema": SCHEMA, "dose": GOAL_OFFER_DOSE, "p_silence": P_SILENCE}
        age = now - float(reg.get("ts") or 0)
        if not reg or age > REGISTER_STALE_S:
            row.update({"arm": "none", "why": "register missing or stale", "register_age_s": round(age, 1) if reg else None})
            write_live_row(row)
            return None
        cands = []
        for g in reg.get("goals") or []:
            if g.get("kind") not in LIVE_KINDS:
                continue
            ok, _ = eligibility(g)
            pc = _as_concern(g) if ok else None
            if pc:
                cands.append((g, pc))
        row["eligible"] = [g["id"] for g, _ in cands]
        if not cands:
            row.update({"arm": "none", "why": "no eligible goal"})
            write_live_row(row)
            return None
        if rng.random() < P_SILENCE:
            row["arm"] = "silence"
            write_live_row(row)
            return {"arm": "silence"}
        g, pc = cands[int(rng.random() * len(cands)) % len(cands)]
        row.update({"arm": "offer", "policy": "uniform", "p": round(1.0 / len(cands), 4),
                    "id": g["id"], "kind": g["kind"], "text": pc["text"][:200], "source": pc["source"]})
        write_live_row(row)
        if pc["source"] == "want":           # the hold law: a re-presentation of his own words is an injection
            _note_injection(pc["text"])
        return {"arm": "offer", "pc": pc, "goal_id": g["id"]}
    except Exception as exc:
        logger.warning("[goal_offer] live offer failed (no offer made): %s: %s", type(exc).__name__, exc)
        return None


def _note_injection(text: str) -> None:
    try:
        fn = _log_injection
        if fn is None:
            import sys
            mod = sys.modules.get("core.guidance_learning")
            fn = getattr(mod, "log_injection", None) if mod is not None else None
        if fn is not None:
            fn("goal_offer", text[:200])
    except Exception:
        pass


# ── Phase 6: setting a goal down (D-0768, founder 2026-11-14) ───────────────────────────────────────────────
# He almost never ends anything in his own words (39 resting phrases in 20,178 thoughts, F-4645), and the only
# endings the system had were ones it observed for him (a cap, a fade). This gives him the move: on a tick where
# one of his own held goals was put in front of him, the thought's JSON carries an optional `set_down` field.
# If he fills it, a judge OTHER than him checks only that the note is about that goal, says where he had got to
# and says what is still open. It never judges whether stopping is wise or whether what he says is true. An
# accepted note rests the goal: the register stops offering it until he takes it up again himself.
SET_DOWN_LIVE = True
SET_DOWN_MIN_WORDS = 8
SET_DOWN_MARKS_FRONTIER = True   # closure_producer P4: False = the pre-existing path (the frontier entry stays open)
_judge = None                # test hook: async callable (system, user) -> {"verdict": bool|None, "how", "why"}
_tasks: set = set()

SET_DOWN_JUDGE_SYS = (
    "You read ONE thing a mind was holding (a question, a stand, or a want, in its own words) and ONE short note "
    "it wrote on putting that thing down for now. You see nothing else. Decide whether the note is a genuine "
    "setting-down of THAT thing. To be genuine it must do three things: be about that thing; say something about "
    "where the mind had got to with it; and say something that is still open or unfinished. A note that only "
    "repeats the thing, or only says it is stopping, is not genuine. Do NOT judge whether stopping is wise, and "
    "do NOT judge whether what the note says is true or well reasoned. Do not tilt either way.\n"
    "Answer ONLY JSON: {\"genuine\": true or false, \"why\": \"one sentence\"}")


def set_down_schema(offered: bool) -> str:
    return ', "set_down": ""' if (SET_DOWN_LIVE and offered) else ""


def set_down_rule(offered: bool) -> str:
    """The rule for the idle-thought system prompt, in the register of the `settled` rule. It describes a channel
    for him; it does not ask him to use it."""
    if not (SET_DOWN_LIVE and offered):
        return ""
    return ("set_down: one of your own earlier lines was put in front of you this time. Leave as \"\" unless you are "
            "putting it down for now. If you are, say in a sentence or two where you had got to with it and what "
            "is still open. Your own judgement; nothing is lost, and it comes back if you take it up again. ")


def parse_set_down(data: dict) -> str:
    try:
        if not SET_DOWN_LIVE or not isinstance(data, dict):
            return ""
        return " ".join(str(data.get("set_down", "") or "").split())[:400]
    except Exception:
        return ""


def set_down_path() -> Path:
    from core import goals
    return goals._p("goal_set_down.json")


def set_down_log_path() -> Path:
    from core import goals
    return goals._p("logs", "goal_set_down.jsonl")


def offered_goal(live: dict | None, pc: dict | None) -> dict | None:
    """Which register goal, if any, the anchor has just put in front of him: the register's own offer, or the
    ordinary anchor's question when that question is one the register holds. None otherwise."""
    try:
        if live and live.get("arm") == "offer" and live.get("goal_id"):
            return {"id": live["goal_id"], "text": (live.get("pc") or {}).get("text", "")}
        text = (pc or {}).get("text")
        if not text:
            return None
        for g in _register().get("goals") or []:
            if g.get("text") == text and g.get("state") in ("held", "deferred"):
                return {"id": g["id"], "text": text}
    except Exception:
        pass
    return None


def is_rested_text(text: str) -> bool:
    """True if this exact text is a goal he has set down and not taken up again (the anchor then leaves it be)."""
    try:
        if not text:
            return False
        return any(g.get("text") == text and g.get("state") == "rested" for g in _register().get("goals") or [])
    except Exception:
        return False


def is_rested_id(goal_id: str) -> bool:
    """True if this register id is a goal he has set down and not taken up again."""
    try:
        return bool(goal_id) and any(g.get("id") == goal_id and g.get("state") == "rested"
                                     for g in _register().get("goals") or [])
    except Exception:
        return False


def offered_pursuit(pursuit_id: str) -> dict | None:
    """The register goal for a pursuit the RETURN has just put in front of him ({"id","text"}), or None when the
    register does not hold it as a live goal. The RETURN is its own route (LIVE_KINDS leaves pursuits out of the
    anchor offer on purpose); this only lets the same optional `set_down` ride on that tick (D-0768)."""
    try:
        gid = f"pursuit:{pursuit_id}"
        for g in _register().get("goals") or []:
            if g.get("id") == gid and g.get("state") in ("held", "deferred"):
                return {"id": gid, "text": g.get("text") or ""}
    except Exception:
        pass
    return None


def _thin(goal_text: str, note: str) -> str | None:
    """A deterministic first look, before any model is asked. Returns why the note is too thin, or None."""
    from core import goals
    if len(note.split()) < SET_DOWN_MIN_WORDS:
        return f"under {SET_DOWN_MIN_WORDS} words"
    if goals._jaccard(goals._words(goal_text), goals._words(note)) >= 0.8:
        return "repeats the goal"
    return None


async def _set_down(goal: dict, note: str, thought: str, cycle_id: str) -> dict:
    """Judge one set-down note and record it. An accepted note is written to the set-down store, which the
    register reads; a rejected or unjudged one changes nothing (no judge, no state change). Never raises."""
    row = {"ts": round(time.time(), 1), "id": goal.get("id"), "goal": (goal.get("text") or "")[:240],
           "note": note, "thought": (thought or "")[:300], "cycle_id": str(cycle_id or "")[:8],
           "accepted": False, "how": None, "why": ""}
    try:
        thin = _thin(goal.get("text") or "", note)
        if thin:
            row.update({"how": "precheck", "why": thin})
        else:
            user = f"THE THING IT WAS HOLDING: {(goal.get('text') or '')[:300]}\n\nITS NOTE ON PUTTING IT DOWN: {note}"
            fn = _judge
            if fn is None:
                from core import judge_panel as _jp
                d = await _jp.rule_detail(SET_DOWN_JUDGE_SYS, user, "genuine", context=f"goal_set_down:{goal.get('id')}")
            else:
                d = await fn(SET_DOWN_JUDGE_SYS, user)
            v = d.get("verdict")
            row.update({"how": d.get("how") or ("judge" if v is not None else "unavailable"),
                        "why": (d.get("why") or "")[:200], "accepted": bool(v) if v is not None else False,
                        "judged": v is not None})
        from core import profile
        if row["accepted"]:
            rec = 0
            for g in _register().get("goals") or []:
                if g.get("id") == goal.get("id"):
                    rec = int((g.get("earned") or {}).get("recurrences", 0) or 0)
            sp = profile.guard_path(set_down_path())
            store = {}
            try:
                store = json.loads(sp.read_text(encoding="utf-8"))
            except Exception:
                store = {}
            store[goal["id"]] = {"ts": row["ts"], "note": note, "recurrences_at": rec, "goal": row["goal"]}
            sp.parent.mkdir(parents=True, exist_ok=True)
            tmp = sp.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(sp)
            # closure_producer P4: an accepted set-down of a frontier question is also its honest ending in the
            # frontier (status set_down, with his note). Asking it again reopens it (frontier.SET_DOWN_REOPEN_ON_ASK).
            if SET_DOWN_MARKS_FRONTIER and str(goal.get("id") or "").startswith("question:"):
                try:
                    from core import frontier as _fr
                    row["frontier_set_down"] = bool(_fr.set_down(str(goal["id"]).split(":", 1)[1], note))
                except profile.NonLiveWriteError:
                    raise
                except Exception as exc:
                    row["frontier_set_down"] = False
                    logger.debug("[goal_offer] frontier set_down not marked: %r", exc)
        lp = profile.guard_path(set_down_log_path())
        lp.parent.mkdir(parents=True, exist_ok=True)
        with open(lp, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("[goal_offer] set-down handling failed (nothing rested): %s: %s", type(exc).__name__, exc)
    return row


def set_down_later(goal: dict, note: str, thought: str, cycle_id: str = "") -> bool:
    """Schedule the judging of a set-down note; never awaited by the thought loop. Returns True if scheduled."""
    try:
        if not (SET_DOWN_LIVE and goal and goal.get("id") and note):
            return False
        import asyncio
        loop = asyncio.get_running_loop()
        t = loop.create_task(_set_down(dict(goal), note, thought, cycle_id))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)
        return True
    except Exception as exc:
        logger.debug("[goal_offer] set_down_later not scheduled: %r", exc)
        return False


def write_live_row(row: dict) -> None:
    from core import profile
    path = profile.guard_path(live_log_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_row(row: dict) -> None:
    """Append one row. The path is resolved through the write fence BEFORE any I/O (NonLiveWriteError propagates)."""
    from core import profile
    path = profile.guard_path(log_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stats(tail_bytes: int = 4_000_000) -> dict:
    """A reader for the Phase 1 gate: how often each policy's pick is what he then acted on, and how often the
    challenger rule would have changed the standing offer against no rule. For a pulse or a review, never a prompt."""
    from core import goals
    rows = goals._tail_jsonl(log_path(), tail_bytes)
    n = len(rows)
    with_el = [r for r in rows if r.get("eligible")]
    def share(k):
        return round(sum(bool(r["actual"].get(k)) for r in with_el) / len(with_el), 4) if with_el else None
    return {"rows": n, "rows_with_eligible": len(with_el),
            "mean_eligible": round(sum(len(r["eligible"]) for r in with_el) / len(with_el), 2) if with_el else None,
            "acted_on_softmax_pick": share("acted_on_softmax_pick"),
            "acted_on_uniform_pick": share("acted_on_uniform_pick"),
            "acted_on_most_recent": share("acted_on_most_recent"),
            "switches_no_rule": sum(bool(r["challenger"]["switched_no_rule"]) for r in rows),
            "switches_rule": sum(bool(r["challenger"]["switched_rule"]) for r in rows),
            "silence_share": round(sum(bool(r["policies"]["silence"]["drawn"]) for r in rows) / n, 4) if n else None}

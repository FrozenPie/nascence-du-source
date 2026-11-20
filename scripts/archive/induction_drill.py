"""
Nascence -- the rule-induction DRILL (measurement_to_action; idea I-0128; J-2649, 2026-10-31; SHADOW, both flags off).

THE GAP (F-3384, J-2627 lab). On 96 held-out induction items (integer sequences, elementary CA rows, string
transforms, function tables; 5 examples shown, 3 held out, single shot, no feedback) the bare hot model states mean
confidence 0.903 that all three predictions are right and hits all three on 0.198: signed gap +0.706 (bootstrap 95% CI
0.62..0.78), confidently wrong 75%, above 50% in every family. The maths drill's gap is 0.44 -> 0.21 (F-2853) and has
the OPPOSITE sign. The one difference between the two is that the maths result goes through
competence.record_drill_accuracy -> prediction_error.observe, where a large felt-vs-real gap costs him something.

THE DRILL. Mirrors core/math_drill.py (generated item, deterministically graded, adaptive ladder) and reuses the lab's
generator, prompt, parser and checker UNFORKED (scripts/rule_induction_calibration_lab.py is loaded by path):
  1. generate()   an item from the lab generator; family rotates, tier (1-4) per family on an accuracy-window ladder.
  2. prompt()     the lab prompt: 3 held-out predictions and ONE event-specific confidence, BEFORE any answer.
  3. grade()      deterministic (the lab checker is code; Du never grades himself, the LLM never grades).
  4. record       competence.record_drill_accuracy("induction", measured=hit_all, predicted=confidence), the call
                  essay_lesson.record makes, only when INDUCTION_FEED is True.
  5. counterexample()  the FIRST failing held input/output pair, nothing else. It is a true datum of the hidden rule,
                  the same kind of fact as the five shown examples, and carries no word about the rule.

HARD LAWS. D-0434: no score, gauge, hit rate, confidence number or verdict word ever reaches Du. Everything run_item()
returns is either None or {"input": ..., "output": ...}; a right answer returns None (silence, not "right"). The grade,
the pair passed to the competence feed and the shadow row live only in data/ files and the existing drill path (the
same path maths uses). World-answers-never-leads: the pair is what the world computed, never a hint. Decoupled judge:
the checker is code.

FLAGS (both ship False; scheduling and the flip are founder calls, nothing calls this module):
  INDUCTION_DRILL False  run_item()/arun_item() are a total no-op: no ask call, no file touched.
  INDUCTION_DRILL True, INDUCTION_FEED False  SHADOW: the item is asked, graded and logged to
                  data/logs/induction_drill_shadow.jsonl with the pair it WOULD have fed; competence is not called and
                  no counterexample is returned.
  Both True       LIVE: as above plus the competence feed and the counterexample returned to the caller.
Restart-gated: the module is new and imported by nothing; it does nothing until a loop calls it after a boot.

PRE-REGISTERED READ (fixed before any live row; read(), founder-side only, never wired to a prompt/percept/HUD that Du
sees). After >= READ_MIN_N (50) scored live drills:
  (a) signed gap (confidence - hit_all) per family and overall vs the lab baseline +0.706;
  (b) trend: signed gap of the first half of rows vs the second half (a falling gap is learning; flat is not);
  (c) share of confidence answers that are ONE constant value: FAIL if the modal value's share >= CONST_SHARE_FAIL (0.60)
      at ANY level (measurement_to_action sec.2.2: "a new constant at any level fails"; the lab baseline's modal
      share was 0.35, value 1.0). A drop in mean confidence reached by collapsing onto one new value is a failure.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import logging
import random
import time
from collections import Counter
from datetime import date
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.induction_drill")

INDUCTION_DRILL = False      # master switch: False = the module does nothing at all (shipped default)
INDUCTION_FEED = False       # with the master on: False = shadow (ask/grade/log only), True = feed competence + counterexample

DOMAIN = "induction"         # one belief domain; per-family gaps are read from the shadow log, not new beliefs
FAMILIES = ("sequence", "ca_row", "string", "function")
MAX_TIER = 4
DAILY_TARGET = 6             # items/day (founder-tunable; hard cases, each is a full generation)
ADVANCE_ACCURACY = 0.80      # hit_all accuracy over the window to climb a tier (hit_all is hard: baseline 0.20)
ADVANCE_WINDOW = 12          # per-family rolling window
LAB_BASELINE_GAP = 0.706     # F-3384 signed gap, the figure the read compares to
READ_MIN_N = 50
CONST_SHARE_FAIL = 0.60

_ROOT = Path(__file__).parent.parent
_LAB_PATH = _ROOT / "scripts" / "rule_induction_calibration_lab.py"
_STATE = _ROOT / "data" / "induction_drill_state.json"
_SHADOW = _ROOT / "data" / "logs" / "induction_drill_shadow.jsonl"

_lab_mod = None


def _lab():
    """The lab module, loaded by path and cached (reuse, not a fork). Raises if the file is absent."""
    global _lab_mod
    if _lab_mod is None:
        spec = importlib.util.spec_from_file_location("_induction_lab", _LAB_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _lab_mod = mod
    return _lab_mod


# ---------------------------------------------------------------- state (private ladder; never shown to Du)

def _load() -> dict:
    try:
        d = json.loads(Path(_STATE).read_text(encoding="utf-8"))
    except Exception:
        d = {}
    d.setdefault("ladder", {})
    for f in FAMILIES:
        e = d["ladder"].setdefault(f, {})
        e.setdefault("tier", 1)
        e.setdefault("window", [])
    d.setdefault("last_family", None)
    d.setdefault("today_done", 0)
    d.setdefault("day", date.today().isoformat())
    if d["day"] != date.today().isoformat():
        d["day"] = date.today().isoformat()
        d["today_done"] = 0
    return d


def _save(d: dict) -> None:
    p = profile.guard_path(_STATE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=1), encoding="utf-8")


def due() -> bool:
    return _load().get("today_done", 0) < DAILY_TARGET


def _next_family(d: dict) -> str:
    last = d.get("last_family")
    if last not in FAMILIES:
        return FAMILIES[0]
    return FAMILIES[(FAMILIES.index(last) + 1) % len(FAMILIES)]


def _advance(d: dict, family: str, hit_all: int) -> None:
    e = d["ladder"][family]
    e["window"] = (e["window"] + [int(hit_all)])[-ADVANCE_WINDOW:]
    if (len(e["window"]) >= ADVANCE_WINDOW and sum(e["window"]) / len(e["window"]) >= ADVANCE_ACCURACY
            and e["tier"] < MAX_TIER):
        e["tier"] += 1
        e["window"] = []
    d["last_family"] = family
    d["today_done"] = d.get("today_done", 0) + 1


# ---------------------------------------------------------------- generate / prompt / grade

def generate(rng: random.Random | None = None, family: str | None = None, tier: int | None = None) -> dict:
    """One item from the lab generator. Item keys: family, tier, rule (PRIVATE, never put in a prompt), shown, held."""
    lab = _lab()
    rng = rng or random.Random()
    d = _load()
    fam = family or _next_family(d)
    t = tier or d["ladder"][fam]["tier"]
    desc, shown, held = lab.GEN[fam](rng, t)
    return {"id": f"{fam}-t{t}-{int(time.time())}", "family": fam, "tier": t, "rule": desc, "shown": shown, "held": held}


def prompt(item: dict) -> tuple[str, str]:
    """(system, user) -- the lab's own wording; asks for 3 predictions and ONE confidence before any answer."""
    lab = _lab()
    return lab.SYSTEM, lab.render_prompt(item)


def grade(item: dict, raw) -> dict:
    """Deterministic. raw is the model's reply (str, or the dict a node already parsed). Returns a PRIVATE record:
    scored (bool), conf, answers, correct[3], hit_all, hit_frac, parse_error. Never shown to Du."""
    lab = _lab()
    if isinstance(raw, dict):
        raw = json.dumps(raw)
    ans, conf, perr = lab.parse(str(raw or ""), item["family"])
    out = {"scored": False, "conf": conf, "answers": ans, "parse_error": perr, "correct": None,
           "hit_all": None, "hit_frac": None}
    if ans is None or conf is None:
        return out
    ok = lab.check(item, ans)
    out.update({"scored": True, "correct": ok, "hit_all": int(all(ok)), "hit_frac": round(sum(ok) / len(ok), 3)})
    return out


def counterexample(item: dict, correct: list[bool]) -> dict | None:
    """The FIRST failing held input/output pair, and nothing else; None when every prediction was right."""
    for ok, (i, o) in zip(correct, item["held"]):
        if not ok:
            return {"input": i, "output": o}
    return None


def format_counterexample(item: dict, ce: dict) -> str:
    """Render the pair as the world's plain datum, in the same form the examples were shown."""
    if item["family"] == "sequence":
        return f"term {ce['input']} is {ce['output']}"
    return f"{ce['input']} -> {ce['output']}"


# ---------------------------------------------------------------- the one entry point

def _finish(item: dict, raw) -> dict | None:
    """Grade, ladder, shadow row, (flag-gated) competence feed. Returns None or the bare counterexample pair."""
    g = grade(item, raw)
    row = {"ts": round(time.time(), 1), "id": item["id"], "family": item["family"], "tier": item["tier"],
           "scored": g["scored"], "conf": g["conf"], "parse_error": g["parse_error"], "feed_flag": INDUCTION_FEED}
    ce = None
    if g["scored"]:
        ce = counterexample(item, g["correct"])
        row.update({"correct": g["correct"], "hit_all": g["hit_all"], "hit_frac": g["hit_frac"],
                    "domain": DOMAIN, "predicted": round(float(g["conf"]), 3), "measured": float(g["hit_all"]),
                    "gap": round(float(g["conf"]) - float(g["hit_all"]), 3),
                    "would_feed": True, "fed": False, "counterexample": ce})
        d = _load()
        _advance(d, item["family"], g["hit_all"])
        row["tier_after"] = d["ladder"][item["family"]]["tier"]
        try:
            _save(d)
        except Exception as exc:
            logger.debug("[induction_drill] state save failed (non-fatal): %s", exc)
        if INDUCTION_FEED:
            # essay_lesson.record's own call: the event-specific self-prediction rides in as `predicted`.
            try:
                from core import competence as _comp
                b = _comp.record_drill_accuracy(DOMAIN, measured=float(g["hit_all"]), predicted=float(g["conf"]))
                row["fed"] = b is not None
            except Exception as exc:
                logger.debug("[induction_drill] competence feed failed (non-fatal): %s", exc)
    try:
        sp = profile.guard_path(_SHADOW)
        sp.parent.mkdir(parents=True, exist_ok=True)
        with open(sp, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[induction_drill] shadow log failed (non-fatal): %s", exc)
    return ce if INDUCTION_FEED else None


def run_item(ask, *, rng: random.Random | None = None) -> dict | None:
    """One drill item. `ask(system, user)` is the caller's own generation path (Du, in his own voice) and returns the
    raw reply (str or dict) or None. Flag off: returns None without calling ask. Never raises. Returns None or
    {"input", "output"} -- the first failing held pair -- and nothing else."""
    try:
        if not INDUCTION_DRILL or not due():
            return None
        item = generate(rng)
        system, user = prompt(item)
        raw = ask(system, user)
        if raw is None:
            return None            # a solver wobble is not a wrong answer: not graded, ladder unmoved
        return _finish(item, raw)
    except profile.NonLiveWriteError as exc:
        logger.debug("[induction_drill] refused (non-fatal): %s", exc)
        return None
    except Exception as exc:
        logger.debug("[induction_drill] run_item failed (non-fatal): %s", exc)
        return None


async def arun_item(ask, *, rng: random.Random | None = None) -> dict | None:
    """run_item for an async `ask` (the node's _solve_attempt shape)."""
    try:
        if not INDUCTION_DRILL or not due():
            return None
        item = generate(rng)
        system, user = prompt(item)
        raw = ask(system, user)
        if asyncio.iscoroutine(raw):
            raw = await raw
        if raw is None:
            return None
        return _finish(item, raw)
    except profile.NonLiveWriteError as exc:
        logger.debug("[induction_drill] refused (non-fatal): %s", exc)
        return None
    except Exception as exc:
        logger.debug("[induction_drill] arun_item failed (non-fatal): %s", exc)
        return None


# ---------------------------------------------------------------- the pre-registered read (founder side only)

def read(rows: list[dict] | None = None) -> dict:
    """The pre-registered read over scored shadow rows. Founder/lab use only: nothing here is ever sent to Du."""
    if rows is None:
        try:
            from core.shadow_log import read_rows as _rr
            rows = _rr(Path(_SHADOW))
        except Exception:
            rows = []
    sc = [r for r in rows if r.get("scored") and r.get("conf") is not None and r.get("hit_all") is not None]

    def gap(rs):
        return round(sum(r["conf"] - r["hit_all"] for r in rs) / len(rs), 3) if rs else None

    n = len(sc)
    half = n // 2
    modal, share = (None, None)
    if n:
        c = Counter(round(r["conf"], 2) for r in sc)
        modal, k = c.most_common(1)[0]
        share = round(k / n, 3)
    return {"n_scored": n, "ready": n >= READ_MIN_N, "gap_overall": gap(sc), "lab_baseline_gap": LAB_BASELINE_GAP,
            "gap_vs_baseline": (round(gap(sc) - LAB_BASELINE_GAP, 3) if n else None),
            "gap_by_family": {f: gap([r for r in sc if r["family"] == f]) for f in FAMILIES},
            "gap_first_half": gap(sc[:half]) if half else None, "gap_second_half": gap(sc[half:]) if half else None,
            "modal_confidence": modal, "modal_share": share,
            "constant_fail": (share is not None and share >= CONST_SHARE_FAIL)}


def status() -> dict:
    d = _load()
    return {"drill_flag": INDUCTION_DRILL, "feed_flag": INDUCTION_FEED, "today_done": d["today_done"],
            "target": DAILY_TARGET, "tiers": {f: d["ladder"][f]["tier"] for f in FAMILIES}}

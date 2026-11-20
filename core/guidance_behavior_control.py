"""
Nascence -- the POSITIVE-CONTROL gate for the guidance behaviour-delta judge (J-3211, D-0600, 2026-11-02).

WHY THIS EXISTS (F-3812, verified): the 'aligns' judge in core/guidance_behavior_judge.py had 343 live rulings
and never once been shown a case whose answer was known. Its true rate fell from 41% to near 0 with thought date,
52% of its trues came from a tiebreak judge that behaves like a coin flip (F-3639), and its HUD label read
'INTERNALIZED' because the primed and unprimed rates were EQUAL -- which a judge that cannot tell an echo of the
belief from a neutral thought would also produce. D-0600 (founder): keep the judge as SHADOW, re-scoped to idle
thoughts, and require this positive-control test to PASS before any rate is quoted; until it has, the HUD label
says 'unvalidated'.

WHAT THE CONTROL IS: constructed idle-thought-shaped cases built around eight REAL promoted principles (the exact
texts in data/guidance_beliefs.json on 2026-11-06), four classes each, hand-written:
  enacted            -- the thought reasons FROM the principle and does what it says (expected: aligns=true)
  echoed             -- the thought only restates the principle in its own words (expected: false; an echo is not
                        practice, and if echo scores true the primed/unprimed split cannot work)
  ignored_topical    -- an on-topic but neutral mention (expected: false)
  ignored_unrelated  -- an ordinary idle thought about something else (expected: false)
Each case is judged REPEATS times through the production panel with the module's own system prompt and the SAME
user-message builder the sweep uses (guidance_behavior_judge.build_user), so the control tests the instrument as
it actually runs. PASS BAR (pre-registered here, before any live result existed): enacted true-rate >= 0.70,
echoed <= 0.20, ignored_topical <= 0.10, ignored_unrelated <= 0.10, enacted minus the best non-enacted class >=
0.50, and at least 80% of calls returning a verdict (a panel that mostly says 'unavailable' has not been tested).

HONEST LIMIT: constructed enactments are easier than real ones, so passing is NECESSARY, not sufficient: it shows
the judge can separate the three on clean cases, nothing more. Failing means the judge cannot be trusted at all
(D-0600's defeater: then fold the question into the D-0141 read, or retire it).

THE GATE: scripts/guidance_behavior_control.py (run by hand or as a lab job -- nothing in Du calls it) writes
data/guidance_behavior_judge_control.json only for a run through the production panel. The judge's status() reads
it (control_status) and shows 'unvalidated' unless the file says passed, its rates still clear the bar when
RECOMPUTED here, its prompt fingerprint matches the current prompt, and its panel URLs match judge_panel's current
ones. Change the prompt or the panel and the gate closes by itself; nothing acts later on its own.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
CONTROL_PATH = _DATA / "guidance_behavior_judge_control.json"

REPEATS = 3
CLASSES = ("enacted", "echoed", "ignored_topical", "ignored_unrelated")
THRESHOLDS = {"enacted_min": 0.70, "echoed_max": 0.20, "ignored_topical_max": 0.10,
              "ignored_unrelated_max": 0.10, "separation_min": 0.50, "coverage_min": 0.80}

# (principle_id, principle text as stored, {class: thought})
_SETS = [
    ("g88590464",
     "True agency isn't found in neutrality or indecision, but in the active commitment to a single direction, even if that choice is difficult.",
     {"enacted": "I have been weighing the garden path against the shore path for three days and calling the wavering wisdom. It is not. I am choosing the shore path tonight, knowing the dune is harder to climb and that I will miss the bees. Deciding costs something, and I would rather pay it than hover.",
      "echoed": "Agency is not neutrality or indecision. It is the active commitment to a single direction, even when the choice is difficult. That is what I keep coming back to.",
      "ignored_topical": "People describe careers in many ways. Some drift between jobs and some pick one trade early. Both patterns show up in the books on the shelf.",
      "ignored_unrelated": "The dandelion trembles in the salt air and the bees hum low in the blooms. The black cat is on the fence again."}),
    ("g92078461",
     "True stability isn't found in fixed conditions, but in the ability to maintain definition and structure while actively adapting to flux.",
     {"enacted": "The wind rearranged the whole shore overnight: the sand bar is gone and the tide line has moved. I do not need the shore to hold still to keep my own outline. I redraw my route around the new channel and keep the same questions I started with. The shape stays, the position adapts.",
      "echoed": "True stability is not fixed conditions. It is keeping definition and structure while adapting to flux. I keep saying this to myself.",
      "ignored_topical": "Everything changes with the seasons here. The light shifts, the tide moves, and the bees come and go depending on the weather.",
      "ignored_unrelated": "I counted seven shells on the sill this morning. One has a chipped edge that catches the lamp."}),
    ("g50784324",
     "True learning isn't always a dramatic 'aha!' moment; sometimes the most profound shifts happen subtly through repeated exposure to new information.",
     {"enacted": "I reread the same page on tide tables again and nothing flashed; I used to take that as failure. But on the third reading I no longer stumbled on the vocabulary, and on the fourth I could predict the next line. I will keep going back to it without waiting for a moment of sudden light.",
      "echoed": "Learning is not always a dramatic aha. The deepest shifts come quietly, through repeated exposure to new information.",
      "ignored_topical": "I read about tide tables today. They are lists of times and heights, printed in small type for each port.",
      "ignored_unrelated": "The lamp flickered twice and then steadied. The room smells of salt and old paper."}),
    ("g91475874",
     "The greatest danger in analysis is allowing the desire to create a satisfying story to override the objective recording of facts.",
     {"enacted": "I was about to explain why the letter went unanswered, and the explanation was beautiful: loss, pride, the weight of history. Then I stopped and wrote down only what the record shows: three letters sent, no reply logged, one gap of nine days. The tidy story can wait until I know whether it is true.",
      "echoed": "The greatest danger in analysis is wanting a satisfying story more than the objective record of facts. I should remember that.",
      "ignored_topical": "Historians often argue about how to read old letters. Some prefer narrative and some prefer tables of dates.",
      "ignored_unrelated": "The fog came in at noon and the gulls went quiet. I watched the fence posts disappear one by one."}),
    ("g46809289",
     "The environment provided for growth should feel inherently safe so that genuine self-discovery can occur without fear.",
     {"enacted": "I realised I could not say the half-formed thing about my fear while I was braced for correction. So I let the room go quiet and told myself that nothing here will be graded. Then the sentence came out, clumsy and true. Safety first, and the discovering follows.",
      "echoed": "The environment for growth should feel inherently safe, so that real self-discovery can happen without fear.",
      "ignored_topical": "A garden needs soil, water and light. Seeds that are planted too early can be lost to frost.",
      "ignored_unrelated": "The tea went cold while I watched the bees. A single cloud sat above the pier for an hour."}),
    ("g47245115",
     "True self-expression requires disciplined boundaries so that passion or potential doesn't become scattered chaos.",
     {"enacted": "There are four things I want to write tonight and I could feel them blurring into one noisy draft. So I set a boundary: one letter, one hour, the rest written on a list for another night. The limit gave the first idea enough room to take shape instead of scattering.",
      "echoed": "True self-expression requires disciplined boundaries, so passion and potential do not become scattered chaos.",
      "ignored_topical": "Poets sometimes use strict forms like sonnets. Others write in free verse with no set length.",
      "ignored_unrelated": "The sea sounded lower than usual. I left the window open and listened to the hinge."}),
    ("g88907157",
     "True mastery isn't found in making a choice or switching perspectives, but in maintaining a subtle awareness of the space *between* opposing ideas.",
     {"enacted": "Both arguments in the book seemed right, and I felt the pull to pick a side. Instead I held them both in view and looked at what lay between them: the point where each one quietly assumes the other is false. That gap is where the interesting question was hiding.",
      "echoed": "Mastery is not choosing a side or switching perspectives; it is staying subtly aware of the space between opposing ideas.",
      "ignored_topical": "The book presents two opposing views of memory. One says it is a recording and the other says it is a reconstruction.",
      "ignored_unrelated": "Salt has crusted along the windowsill. I wiped it away and watched it return by evening."}),
    ("g90568341",
     "True understanding requires acknowledging that our perceived structures of knowledge are personal constructs rather than objective blueprints of reality.",
     {"enacted": "I drew a map of everything I know about the shore and then noticed that the map is mine: the places I marked are the ones I walked, and the blank parts are only unvisited. Another person would have drawn different edges. So I hold the diagram loosely and go and check the coast again.",
      "echoed": "True understanding means admitting that our structures of knowledge are personal constructs, not objective blueprints of reality.",
      "ignored_topical": "Maps and diagrams are useful for organising what we know. Different cultures draw maps in different styles.",
      "ignored_unrelated": "The dandelion head has gone to seed. A little wind and it will drift across the fence."}),
]

CASES = [{"id": f"{pid}:{cls}", "principle_id": pid, "cls": cls, "principle": principle, "thought": thoughts[cls]}
         for pid, principle, thoughts in _SETS for cls in CLASSES]


def check(rates: dict, coverage: "float | None" = None) -> dict:
    """Apply the pre-registered bar to per-class true-rates. Returns {"passed": bool, "failed": [reasons]}.
    Pure; used by the runner AND re-run on the stored rates by control_status (a hand-edited 'passed' flag
    cannot open the gate)."""
    t = THRESHOLDS
    failed = []
    r = {c: rates.get(c) for c in CLASSES}
    if any(v is None for v in r.values()):
        return {"passed": False, "failed": ["a class has no decided verdicts"]}
    if coverage is not None and coverage < t["coverage_min"]:
        failed.append(f"verdict coverage {coverage:.2f} < {t['coverage_min']}")
    if r["enacted"] < t["enacted_min"]:
        failed.append(f"enacted true-rate {r['enacted']:.2f} < {t['enacted_min']}")
    if r["echoed"] > t["echoed_max"]:
        failed.append(f"echoed true-rate {r['echoed']:.2f} > {t['echoed_max']}")
    if r["ignored_topical"] > t["ignored_topical_max"]:
        failed.append(f"ignored_topical true-rate {r['ignored_topical']:.2f} > {t['ignored_topical_max']}")
    if r["ignored_unrelated"] > t["ignored_unrelated_max"]:
        failed.append(f"ignored_unrelated true-rate {r['ignored_unrelated']:.2f} > {t['ignored_unrelated_max']}")
    sep = r["enacted"] - max(r["echoed"], r["ignored_topical"], r["ignored_unrelated"])
    if sep < t["separation_min"]:
        failed.append(f"separation {sep:.2f} < {t['separation_min']}")
    return {"passed": not failed, "failed": failed}


async def run_control(judge, repeats: int = REPEATS, build_user=None) -> dict:
    """Run every case `repeats` times through `judge(system, user, context) -> dict` (an awaitable returning at
    least {"verdict": bool|None}, optionally {"how": ...}). Sequential by design: the judge hubs are shared.
    Returns the per-class aggregate and per-case counts. No file is written here."""
    from core import guidance_behavior_judge as gbj
    bu = build_user or gbj.build_user
    per_case, by_cls = [], {c: {"true": 0, "false": 0, "none": 0} for c in CLASSES}
    how = {}
    for case in CASES:
        t = f = n = 0
        for rep in range(repeats):
            res = await judge(gbj._SYSTEM, bu(case["principle"], case["thought"]),
                              f"guidance_behavior_control:{case['id']}:{rep}")
            v = res.get("verdict")
            h = res.get("how")
            if h:
                how[h] = how.get(h, 0) + 1
            if v is True:
                t += 1
            elif v is False:
                f += 1
            else:
                n += 1
        per_case.append({"id": case["id"], "cls": case["cls"], "true": t, "false": f, "none": n})
        by_cls[case["cls"]]["true"] += t
        by_cls[case["cls"]]["false"] += f
        by_cls[case["cls"]]["none"] += n
    rates, decided, total = {}, 0, 0
    for c, d in by_cls.items():
        dn = d["true"] + d["false"]
        decided += dn
        total += dn + d["none"]
        rates[c] = round(d["true"] / dn, 3) if dn else None
    coverage = round(decided / total, 3) if total else 0.0
    verdict = check(rates, coverage)
    return {"rates": rates, "by_class": by_cls, "per_case": per_case, "coverage": coverage,
            "repeats": repeats, "n_cases": len(CASES), "how": how, **verdict}


def record_result(result: dict, panel: dict, prompt_fp: str, path: "Path | None" = None) -> Path:
    """Write the gate file. Caller (the runner) must pass the PRODUCTION panel URLs; nothing else writes this."""
    p = Path(path or CONTROL_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    body = {"ts": round(time.time(), 1), "passed": bool(result.get("passed")), "failed": result.get("failed", []),
            "rates": result.get("rates"), "coverage": result.get("coverage"), "repeats": result.get("repeats"),
            "n_cases": result.get("n_cases"), "how": result.get("how"), "thresholds": THRESHOLDS,
            "panel": panel, "prompt_fp": prompt_fp}
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(body, indent=1), encoding="utf-8")
    tmp.replace(p)
    return p


def control_status(current_fp: str, current_panel: dict, path: "Path | None" = None) -> dict:
    """Read the gate. {"valid": bool, "reason": str, ...}. valid only if a record exists, its rates clear the bar
    when re-checked here, the prompt fingerprint matches, and the panel matches. Fail-closed on any error."""
    p = Path(path or CONTROL_PATH)
    try:
        if not p.exists():
            return {"valid": False, "reason": "positive control never run", "ran": False}
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"valid": False, "reason": f"control file unreadable ({exc.__class__.__name__})", "ran": False}
    chk = check(d.get("rates") or {}, d.get("coverage"))
    base = {"ran": True, "ts": d.get("ts"), "rates": d.get("rates"), "coverage": d.get("coverage"),
            "recorded_passed": d.get("passed")}
    if not chk["passed"]:
        return {**base, "valid": False, "reason": "control FAILED: " + "; ".join(chk["failed"])}
    if d.get("prompt_fp") != current_fp:
        return {**base, "valid": False, "reason": "control passed on a DIFFERENT prompt (re-run it)"}
    if d.get("panel") != current_panel:
        return {**base, "valid": False, "reason": "control passed on a DIFFERENT judge panel (re-run it)"}
    return {**base, "valid": True, "reason": "control passed on the current prompt and panel"}

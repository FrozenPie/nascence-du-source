"""
Cross-system error-source attribution, OBSERVE-ONLY (J-2532, I-0110, F-3224 direction 5; plan error_pathway).

QUESTION. When an expectation of Du's fails, which of five sources was wrong?
    prediction    - his own prediction was wrong (a deterministic / Emissary / world grade is present)
    action        - the world refused an action whose preconditions held (skill / procedure fault)
    claim         - a claim of his was falsified (retraction ledger, active rows only)
    peer_model    - his model of another agent was wrong (peer letters, the cat)
    changed_world - the world moved between expectation and outcome (world census diff)
Each event is assigned by DECLARED evidence rules (below, fixed before the first run). An event with
evidence for exactly one source is SINGLE; for two or more it is CONTESTED (reported, and resolved by the
declared PRIORITY only for the headline distribution); with no diagnostic evidence it is UNATTRIBUTABLE.
The unattributable + contested share is the finding. Nothing here is a consequence path (one shared error
signal is the affective-hijack shape) and nothing reaches Du (D-0434).

READ-ONLY. Reads data/*.jsonl with plain open(..., 'r'); imports nothing from core/ or nodes/; zero LLM.

FAILURE EVENTS ENUMERATED (detectors; the ledger an event lives in is its detector, not its attribution):
  E_PE   data/prediction_error_log.jsonl rows with gap >= GAP_THRESHOLD (core/prediction_error.py: 0.40)
  E_REF  data/procedures_log.jsonl rows with outcome == 'refused' (the world refused a dispatched hand)
  E_CAL  data/world_calibration.jsonl rows with outcome == 'REFUTED' (world-investigation prediction refuted)
  E_RET  data/retractions.jsonl rows with status != 'withdrawn'
  (side count, not in the distribution: data/hands_trace.jsonl unanswered_deed == true -- an intended deed
   nothing answered; that is the dispatcher's own gap, not a world-graded outcome)
  Peer-model: no ledger records a peer model being WRONG (data/peer_models.json holds reflections only,
   data/peer_effect.jsonl holds Du's own deltas); the cat is the one other agent with a world answer, so
   cat refusals carry peer_model evidence.

DECLARED EVIDENCE RULES
  E_PE, lesson domains (anything but fieldcraft): grade present -> prediction. No world census is relevant.
  E_PE, domain fieldcraft: join the fieldcraft_ledger row within JOIN_FC_S; ok False -> action evidence too
       (contested prediction+action); ok True -> prediction only (he mis-predicted a success).
  E_REF: join the hands_trace answer of the same hand family within JOIN_HANDS_S; classify the answer text
       (first match in ANSWER_CLASSES order):
         already  - the goal state already holds  -> changed_world if CENSUS fires, else UNATTRIBUTABLE
         precond  - a needed object/state absent  -> changed_world if CENSUS fires, else UNATTRIBUTABLE
                    (no ledger records what Du BELIEVED the state was, so 'his model was stale' and
                     'the world moved unrecorded' cannot be separated)
         skill    - execution failed              -> action
         none     - no answer joined / no match   -> UNATTRIBUTABLE
       family 'cat' adds peer_model evidence. CENSUS: data/world_model_shadow.jsonl, any tick in
       [t - CENSUS_LOOKBACK_S, t] whose scored[var].changed is true for a var in RELEVANT[family].
       A family with no relevant var -> census not evaluable (counted).
  E_CAL: predicted text matching INSTRUMENT_RE -> UNATTRIBUTABLE (the judge's own coverage gap);
       else prediction, + changed_world if the census fires for the investigation's family (fire/cat/...).
  E_RET: claim.
PRIORITY (headline resolution of CONTESTED only): changed_world > claim > peer_model > action > prediction.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import json
import re
from pathlib import Path

GAP_THRESHOLD = 0.40          # = core/prediction_error.py GAP_THRESHOLD
JOIN_FC_S = 5.0               # PE fieldcraft row <-> fieldcraft_ledger row
JOIN_HANDS_S = 120.0          # procedures refusal <-> hands_trace answer
CENSUS_LOOKBACK_S = 1800.0    # world moved within the last 30 min before the outcome
PRIORITY = ["changed_world", "claim", "peer_model", "action", "prediction"]
ANSWER_CLASSES = [
    ("already", re.compile(r"\balready\b", re.I)),
    ("precond", re.compile(r"\b(no \w+ to hand|is not here|isn't here|not here|nothing to|nothing for|"
                           r"wants clearing|choked|too dark|empty|none left|out of|no \w+ (?:left|here)|"
                           r"there is no|you have no|cannot reach|is gone|isn't there)\b", re.I)),
    ("skill", re.compile(r"\b(slips|fumble|will not draw|won't draw|fails|snaps|comes apart|miss(?:es)?|"
                         r"splits|crooked|too short|collapses|won't hold|will not hold)\b", re.I)),
]
INSTRUMENT_RE = re.compile(r"coverage gap|not among the advisor|heuristic", re.I)
RELEVANT = {
    "sow": ["weather", "season"], "weed": ["weather", "season"], "water": ["weather"],
    "mow": ["weather", "season"], "save_seed": ["season"], "fire": ["fire", "weather"],
    "lamp": ["fire", "daypart"], "fieldcraft": ["fire", "weather"], "shore": ["tide", "weather"],
    "trap": ["tide", "weather"], "cat": ["cat_location", "cat_activity", "cat_mood"],
}
CAL_FAMILY_RE = [("fire", re.compile(r"fire|ember|fuel|grate", re.I)),
                 ("cat", re.compile(r"\bcat\b", re.I)), ("shore", re.compile(r"tide|shore|sea", re.I)),
                 ("sow", re.compile(r"garden|seed|soil|bed", re.I))]

DATA = Path(__file__).resolve().parent.parent / "data"


def _rows(p: Path):
    out = []
    if not p.exists():
        return out
    with open(p, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--since", default=None, help="local 'YYYY-MM-DD HH:MM' window start")
    ap.add_argument("--until", default=None)
    ap.add_argument("--examples", type=int, default=20)
    a = ap.parse_args()
    d = Path(a.data)
    t0 = dt.datetime.strptime(a.since, "%Y-%m-%d %H:%M").timestamp() if a.since else 0.0
    t1 = dt.datetime.strptime(a.until, "%Y-%m-%d %H:%M").timestamp() if a.until else 9e12
    inwin = lambda t: t0 <= t < t1  # noqa: E731

    pe = _rows(d / "prediction_error_log.jsonl")
    proc = _rows(d / "procedures_log.jsonl")
    fc = sorted(_rows(d / "fieldcraft_ledger.jsonl"), key=lambda r: r["ts"])
    cal = _rows(d / "world_calibration.jsonl")
    ret = _rows(d / "retractions.jsonl")
    census = sorted(_rows(d / "world_model_shadow.jsonl"), key=lambda r: r["ts"])
    hands = []
    unanswered = []
    for r in _rows(d / "hands_trace.jsonl"):
        if r.get("unanswered_deed") and inwin(r.get("ts", 0)):
            unanswered.append(r)
        for h in r.get("hands") or []:
            if isinstance(h, dict) and h.get("answer"):
                hands.append((h.get("ts", r["ts"]), h.get("hand"), h["answer"], r.get("cycle")))
    hands.sort(key=lambda x: x[0])
    hts = [h[0] for h in hands]
    fts = [r["ts"] for r in fc]
    cts = [r["ts"] for r in census]
    census_cov = (_iso(cts[0]), _iso(cts[-1]), len(cts)) if cts else None

    def census_fires(t: float, family: str):
        vars_ = RELEVANT.get(family)
        if not vars_:
            return None  # not evaluable
        i = bisect.bisect_left(cts, t - CENSUS_LOOKBACK_S)
        j = bisect.bisect_right(cts, t)
        if i >= j:
            return None  # no census tick in the lookback: not evaluable
        hit = []
        for r in census[i:j]:
            for v in vars_:
                s = (r.get("scored") or {}).get(v) or {}
                if s.get("changed"):
                    hit.append(f"{v}@{_iso(r['ts'])}->{s.get('actual')}")
        return hit

    events = []

    def add(kind, ts, ref, sources, note, census_state="n/a"):
        srcs = sorted(set(sources), key=PRIORITY.index)
        cls = "unattributable" if not srcs else ("single" if len(srcs) == 1 else "contested")
        events.append({"kind": kind, "ts": ts, "when": _iso(ts), "ref": ref, "sources": srcs,
                       "class": cls, "resolved": srcs[0] if srcs else "unattributable",
                       "census": census_state, "note": note})

    # E_PE
    for r in pe:
        if r.get("gap", 0) < GAP_THRESHOLD or not inwin(r["ts"]):
            continue
        ref = f"pe:{r['domain']}@{r['ts']}"
        src = ["prediction"]
        note = f"pred {r['predicted']} meas {r['measured']} gap {r['gap']}"
        if r["domain"] == "fieldcraft":
            i = bisect.bisect_left(fts, r["ts"] - JOIN_FC_S)
            row = next((x for x in fc[i:i + 6] if abs(x["ts"] - r["ts"]) <= JOIN_FC_S and "ok" in x), None)
            if row is None:
                note += " | no fieldcraft row joined"
            else:
                note += f" | {row.get('craft') or row.get('deed')} ok={row.get('ok')}"
                if row.get("ok") is False:
                    src.append("action")
        add("E_PE", r["ts"], ref, src, note)

    # E_REF
    for r in proc:
        if r.get("outcome") != "refused" or not inwin(r["ts"]):
            continue
        fam = r["key"].split(":", 1)[-1]
        i = bisect.bisect_left(hts, r["ts"] - JOIN_HANDS_S)
        cand = [h for h in hands[i:i + 60] if abs(h[0] - r["ts"]) <= JOIN_HANDS_S and h[1] == fam]
        ans = min(cand, key=lambda h: abs(h[0] - r["ts"])) if cand else None
        acls = "none"
        if ans:
            for name, rx in ANSWER_CLASSES:
                if rx.search(ans[2]):
                    acls = name
                    break
        src = []
        cz = census_fires(r["ts"], fam)
        cstate = "not_evaluable" if cz is None else ("fired" if cz else "quiet")
        if acls == "skill":
            src.append("action")
        elif acls in ("already", "precond") and cz:
            src.append("changed_world")
        if fam == "cat":
            src.append("peer_model")
            if cz:
                src.append("changed_world")
        note = f"{r['key']} answer_class={acls} | " + (ans[2][:110] if ans else "no hands answer joined")
        if cz:
            note += " | census " + ";".join(cz[:2])
        add("E_REF", r["ts"], f"proc:{r['key']}@{r['ts']}" + (f" cycle {ans[3]}" if ans else ""), src, note, cstate)

    # E_CAL
    for r in cal:
        if r.get("outcome") != "REFUTED" or not inwin(r["ts"]):
            continue
        txt = r.get("predicted", "")
        if INSTRUMENT_RE.search(txt):
            add("E_CAL", r["ts"], r.get("episode_id"), [], "instrument gap: " + txt[:110])
            continue
        fam = next((f for f, rx in CAL_FAMILY_RE if rx.search(txt)), None)
        cz = census_fires(r["ts"], fam) if fam else None
        src = ["prediction"] + (["changed_world"] if cz else [])
        add("E_CAL", r["ts"], r.get("episode_id"), src, txt[:110],
            "not_evaluable" if cz is None else ("fired" if cz else "quiet"))

    # E_RET
    ret_withdrawn = 0
    for r in ret:
        if r.get("status") == "withdrawn":
            ret_withdrawn += 1
            continue
        if inwin(r.get("ts", 0)):
            add("E_RET", r["ts"], f"ret@{r['ts']}", ["claim"], str(r.get("falsified_by")))

    n = len(events)
    by_kind = collections.Counter(e["kind"] for e in events)
    by_class = collections.Counter(e["class"] for e in events)
    resolved = collections.Counter(e["resolved"] for e in events)
    contested_pairs = collections.Counter("+".join(e["sources"]) for e in events if e["class"] == "contested")
    kind_class = collections.Counter(f"{e['kind']}:{e['class']}" for e in events)
    ref_answer = collections.Counter(re.search(r"answer_class=(\w+)", e["note"]).group(1)
                                     for e in events if e["kind"] == "E_REF")
    ref_census = collections.Counter(e["census"] for e in events if e["kind"] == "E_REF")
    pe_dom = collections.Counter(e["ref"].split("@")[0] for e in events if e["kind"] == "E_PE")
    # examples: unattributable first, then contested, then single; spread across kinds
    ex = []
    for cls in ("unattributable", "contested", "single"):
        pool = [e for e in events if e["class"] == cls]
        seen = collections.Counter()
        for e in sorted(pool, key=lambda e: -e["ts"]):
            key = (e["kind"], e["note"][:40])
            if seen[key] >= 1:
                continue
            seen[key] += 1
            ex.append(e)
            if len(ex) >= a.examples:
                break
        if len(ex) >= a.examples:
            break
    # POST-HOC VALIDITY CHECK (added after the first run, reported beside -- never replacing -- the declared
    # headline): fieldcraft PE rows whose 'predicted' is the constant placeholder 0.5 carry no prediction,
    # so gap 0.5 >= GAP_THRESHOLD on every attempt by construction. Measured 1.0 = not a failure at all;
    # measured 0.0 = a real failure whose source the row cannot name.
    fc_const = [e for e in events if e["kind"] == "E_PE" and e["ref"].startswith("pe:fieldcraft")
                and e["note"].startswith("pred 0.5 ")]
    fc_const_ok = sum(1 for e in fc_const if " meas 1.0 " in e["note"])
    n_adj = len(events) - fc_const_ok
    un_adj = sum(1 for e in events if e["class"] == "unattributable") + (len(fc_const) - fc_const_ok)
    sensitivity = {"fieldcraft_pe_constant_0.5": len(fc_const), "of_which_success_not_failure": fc_const_ok,
                   "n_events_adjusted": n_adj,
                   "unattributable_share_adjusted": round(un_adj / n_adj, 3) if n_adj else None}
    world = [e for e in events if e["kind"] in ("E_REF", "E_CAL")]
    world_un = sum(1 for e in world if e["class"] != "single")
    out = {
        "window": {"since": a.since, "until": a.until},
        "sensitivity_posthoc": sensitivity,
        "world_graded_events": len(world), "world_graded_not_single": world_un,
        "n_events": n, "by_kind": dict(by_kind), "by_class": dict(by_class),
        "unattributable_share": round(by_class["unattributable"] / n, 3) if n else None,
        "not_single_share": round((n - by_class["single"]) / n, 3) if n else None,
        "resolved_distribution": dict(resolved), "contested_pairs": dict(contested_pairs),
        "kind_by_class": dict(kind_class), "refusal_answer_classes": dict(ref_answer),
        "refusal_census": dict(ref_census), "pe_domains": dict(pe_dom),
        "retractions_withdrawn_excluded": ret_withdrawn,
        "peer_model_ledger_rows": 0,
        "census_coverage": census_cov,
        "side_unanswered_deeds": len(unanswered),
        "examples": ex,
    }
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""
Nascence — ACTIONS DECISION REPLAY (2026-08-30, J-0422 / actions_manager_overhaul).

The regression net for the actions-manager overhaul. dispatch.py's own pre-registered kill criterion is
"replayed over the hands_trace, the dispatcher must answer at least as many willed deeds as the latches
did on the same thoughts, with zero false fires on the adversarial strata" — but no replay tool was ever
built for it. This is that tool, used here for a stricter purpose: proving a REFACTOR changed nothing
except what it meant to change.

For every distinct thought in data/hands_trace.jsonl, at each of the four locations, it records what the
system DECIDES: each family's verdict, and what the dispatcher would then do with it (FIRE / STAGE-place /
STAGE-busy / DROP-weak-intent / DROP-no-hand).

IT NEVER CALLS hand.fn — no deed is executed, no world state is touched, no ledger is written. It replays
the DECISION, not the act. That is what makes it safe to run against the live tree while Du is down.

  python scripts/actions_decision_replay.py --save baseline.json     # snapshot before a change
  python scripts/actions_decision_replay.py --diff  baseline.json    # what a change actually altered

Read-only. Zero LLM.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TRACE = ROOT / "data" / "hands_trace.jsonl"
LOCATIONS = ("study", "garden", "shore", "wood")

# dispatch.py:180 — the dispatcher's own weak-intent reading, applied on top of the judge's
_WEAK = re.compile(r"\b(perhaps|maybe|might|could|would like to|i wonder|someday|one day)\b")


def thoughts(real_locations: bool = False) -> list[tuple]:
    """Distinct (thought, intention, act_kind, act_object[, location]) rows from the real trace,
    in first-seen order (location appended last, only in real_locations mode).

    real_locations=True (J-0423, 2026-08-30): rows written since hands.trace() records `location`
    replay as the DECISION AT THE PLACE DU ACTUALLY STOOD, instead of the all-four-locations cross
    product this script had to use when the trace didn't say. Rows from before the field existed
    have no location and are skipped in this mode (honestly absent, not guessed).

    act_kind/act_object now part of the dedup key too (J-0460, 2026-09-02): the same thought+
    intention text can carry a different structured act_kind/act_object from the voice across
    cycles (e.g. classified 'world' once, something else another time) — deduping on text alone
    could silently keep only a non-'world' row and drop the one case decide_one's new synthetic-
    candidate branch (F-0636) most needs to see.

    Dedup-collision warning (F-1785, J-1273, 2026-09-23): the key above is built from the STORED/
    truncated trace fields (hands.trace() writes thought[:200]/intention[:120]), not the voice's
    full text. F-1785 confirmed this has actually collapsed two genuinely different real thoughts
    into one replayed row, at least twice in hands_trace.jsonl's whole history — decide_one() then
    only ever replays ONE of the two real thoughts' decision for BOTH occurrences, silently. Telling
    a real collision apart from a genuine verbatim repeat needs full-text resolution against the
    twin logs (F-1785's own method) — out of scope for this hot-path tool. What IS cheap: counting,
    per dedup key, how many distinct trace `ts` were folded into it, and warning when that's >1, so
    a --save/--diff reader at least knows the corpus size may be undercounting true distinct trace
    rows, instead of the collapsing being invisible (see _warn_dedup_collisions).

    Two widths in one file (J-1758 / D-0325, 2026-10-04): hands.trace() now stores up to 1,200 / 400
    characters (core/hands.py _TRACE_THOUGHT_CAP / _TRACE_INTENTION_CAP) for every row written from Du's
    next restart on; every row already in the file stays 200/120-cut (never repaired). The key is an
    exact-equality tuple over the STORED text, so it is correct for both widths and for a file holding both:
    two WIDE rows that share a 200-char opening are now distinct keys (the F-1785 collision cannot recur
    between wide rows); two CUT rows with the same stored pair still fold (the legacy undercount the
    warning below reports, unchanged); an old cut row and a later wide row of the same thought never merge
    (different length), so at worst one thought is replayed twice -- once from each copy. Indices are
    first-seen order and new rows only ever append, so a --save baseline taken before the change keeps its
    indices. Replayed decisions on wide rows see the full text dispatch() saw (they used to see a cut)."""
    seen, out = set(), []
    key_ts: dict[tuple, set] = {}  # F-1785: dedup key -> set of distinct trace `ts` folded into it
    with open(TRACE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            thought, intention = r.get("thought") or "", r.get("intention") or ""
            act_kind, act_object = r.get("act_kind") or "", r.get("act_object") or ""
            if not thought:
                continue
            if real_locations:
                location = r.get("location") or ""
                if not location:
                    continue
                row = (thought, intention, act_kind, act_object, location)
            else:
                row = (thought, intention, act_kind, act_object)
            ts = r.get("ts")
            if ts is not None:
                key_ts.setdefault(row, set()).add(ts)
            if row not in seen:
                seen.add(row)
                out.append(row)
    _warn_dedup_collisions(key_ts, len(out))
    return out


def _warn_dedup_collisions(key_ts: dict, n_distinct: int) -> None:
    """F-1785: print a one-line warning when the truncated-text dedup key in thoughts() has folded
    more than one distinct trace `ts` into a single replayed row. This cannot itself tell a real
    collision (two different full-text thoughts sharing a truncated prefix — F-1785 confirmed at
    least 2 of 66 recurring candidates checked by full-text twin-matching) apart from a genuine
    verbatim repeat (the other 64); it only surfaces how much of the corpus is AT RISK of being
    undercounted, so that is not silently invisible the way it was before this warning existed."""
    colliding = {k: len(v) for k, v in key_ts.items() if len(v) > 1}
    if not colliding:
        return
    n_keys = len(colliding)
    n_rows = sum(colliding.values())
    n_hidden = n_rows - n_keys
    print(f"  NOTE (F-1785): {n_keys} of {n_distinct} dedup keys recur across >1 distinct trace ts, "
          f"folding {n_rows} real trace row(s) into those {n_keys} replayed entrie(s) -- {n_hidden} "
          f"row(s) are never separately decided. Not every recurrence is a real collision (most are "
          f"genuine verbatim repeats); F-1785 confirmed at least 2 truly are different thoughts. True "
          f"distinct-trace-row count may be undercounted by up to {n_hidden}.")


def _claims(cands: list) -> dict:
    """dispatch.py's CLAIMS step (J-0540 / F-0733): {dropped_family: claiming_family} over one classify set."""
    try:
        from core import actions as _actions
        return _actions.claimed_by((c.get("family", ""), c.get("object"), c.get("clause"))
                                   for c in cands if c.get("verdict") == "DEED")
    except Exception:
        return {}


def _decide_fate(fam: str, c: dict, here: str, world_done: str | None, by_family: dict,
                 claimed: dict | None = None) -> tuple[dict, str | None]:
    """One DEED candidate's fate — mirrors dispatch.py:204-222 minus the actual hand.fn() call
    (and minus staging/resolving side effects, which decide_one never performs either)."""
    verdict = c.get("verdict", "DEED")
    if claimed and fam in claimed:   # dispatch.py's CLAIMS drop (J-0540): the same clause's compound noun
        return {"family": fam, "verdict": verdict, "action": f"DROP-claimed:{claimed[fam]}"}, world_done
    hand = by_family.get(fam)
    if not hand:
        return {"family": fam, "verdict": verdict, "action": "DROP-no-hand"}, world_done
    clause = (c.get("clause") or "").lower()
    if _WEAK.search(clause):
        return {"family": fam, "verdict": verdict, "action": "DROP-weak-intent"}, world_done
    if "any" not in hand.where and here not in hand.where:
        return {"family": fam, "verdict": verdict, "action": "STAGE-place"}, world_done
    if hand.world and world_done:
        return {"family": fam, "verdict": verdict, "action": f"STAGE-busy:{world_done}"}, world_done
    if hand.world:
        world_done = fam
    return {"family": fam, "verdict": verdict, "action": "FIRE"}, world_done


def decide_one(thought: str, intention: str, here: str, act_kind: str = "", act_object: str = "") -> list[dict]:
    """Replay dispatch.dispatch()'s DECISION for one thought at one location. Calls no hand.

    act_kind/act_object (J-0460, F-0636, 2026-09-02): mirrors dispatch.py:191-198's synthetic-
    candidate branch, which this replay was missing entirely. When act_kind=='world', the voice's
    own structured act_object is classified as a SEPARATE 'I will <act_object>' candidate set
    FIRST (dispatch.py:191-195); any family it names as a DEED there pre-empts that same family
    from the thought/intention pass below (dispatch.py:197's dedup), decided only once, from the
    synthetic candidate. Without this branch decide_one could never see a candidate that only ever
    fires via the synthetic act_object path — the exact gap F-0636 found."""
    from core import dispatch as dp
    from core import literal_will as lw

    by_family = {h.family: h for h in dp.HANDS}
    out: list[dict] = []
    claimed: set[str] = set()
    world_done: str | None = None

    if (act_kind or "").lower() == "world" and act_object:
        try:
            obj_text = "I will " + act_object.strip().rstrip(".")
            synth = lw.classify(obj_text, "", location=here)
        except Exception as exc:
            return [{"family": "<classify-error>", "verdict": "ERROR", "action": str(exc)[:80]}]
        _cl_synth = _claims(synth)
        for c in synth:
            if c.get("verdict") != "DEED":
                continue                      # dispatch.py:194 — a non-DEED synthetic verdict is never looked at
            fam = c.get("family", "")
            row, world_done = _decide_fate(fam, c, here, world_done, by_family, _cl_synth)
            out.append(row)
            claimed.add(fam)

    try:
        cands = lw.classify(thought, intention, location=here)
    except Exception as exc:
        return [{"family": "<classify-error>", "verdict": "ERROR", "action": str(exc)[:80]}]

    # dispatch.py builds ONE candidate list (synthetic first, then the thought's, deduped by family) and runs
    # claimed_by over all of it; a synthetic reading's clause is the "I will <act_object>" text, so it can only
    # ever claim / be claimed within its own set — computing per set here is the same decision.
    _cl_thought = _claims([c for c in cands if c.get("family", "") not in claimed])
    for c in cands:
        fam, verdict = c.get("family", ""), c.get("verdict", "")
        if verdict != "DEED":
            # non-DEED verdicts are recorded too: a refactor that turns a MUSING into a DEED must show up
            out.append({"family": fam, "verdict": verdict, "action": "no-fire"})
            continue
        if fam in claimed:
            continue                          # dispatch.py:197 — already decided (by the synthetic candidate, or earlier here)
        claimed.add(fam)
        row, world_done = _decide_fate(fam, c, here, world_done, by_family, _cl_thought)
        out.append(row)
    return out


def snapshot(real_locations: bool = False) -> dict:
    pairs = thoughts(real_locations)
    rows: dict[str, list] = {}
    for i, p in enumerate(pairs):
        t, inten, act_kind, act_object = p[0], p[1], p[2], p[3]
        for here in ((p[4],) if real_locations else LOCATIONS):
            key = f"{i}|{here}"
            decisions = decide_one(t, inten, here, act_kind, act_object)
            if decisions:
                rows[key] = [[d["family"], d["verdict"], d["action"]] for d in decisions]
    return {"n_thoughts": len(pairs), "locations": list(LOCATIONS), "rows": rows,
            "thoughts": [list(p) for p in pairs], "real_locations": real_locations}


def summarise(snap: dict) -> dict:
    from collections import Counter
    acts = Counter(d[2].split(":")[0] for r in snap["rows"].values() for d in r)
    return dict(acts.most_common())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save")
    ap.add_argument("--diff")
    ap.add_argument("--limit", type=int, default=0, help="only diff the first N differences")
    ap.add_argument("--real-locations", action="store_true",
                    help="replay each traced thought only at the location the trace recorded "
                         "(rows without the J-0423 location field are skipped)")
    a = ap.parse_args()

    snap = snapshot(a.real_locations)
    if a.real_locations:
        print(f"replayed {snap['n_thoughts']} distinct (thought, location) rows at their REAL recorded "
              f"location = {len(snap['rows'])} decision rows (pre-J-0423 rows without a location skipped)")
    else:
        print(f"replayed {snap['n_thoughts']} distinct thoughts x {len(LOCATIONS)} locations "
              f"= {len(snap['rows'])} decision rows")
    print("  decisions:", summarise(snap))

    if a.save:
        Path(a.save).write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
        print(f"  baseline written: {a.save}")
        return 0

    if a.diff:
        base = json.loads(Path(a.diff).read_text(encoding="utf-8"))
        b_rows, n_rows = base["rows"], snap["rows"]
        b_thoughts = base.get("thoughts", [])
        changed = []
        for key in sorted(set(b_rows) | set(n_rows), key=lambda k: (int(k.split("|")[0]), k)):
            before, after = b_rows.get(key), n_rows.get(key)
            if before != after:
                changed.append((key, before, after))
        print(f"\n  {len(changed)} decision row(s) differ from baseline "
              f"(of {max(len(b_rows), len(n_rows))})")
        shown = changed if not a.limit else changed[:a.limit]
        for key, before, after in shown:
            idx, here = key.split("|")
            t = b_thoughts[int(idx)][0] if int(idx) < len(b_thoughts) else "?"
            print(f"\n  [{here}] {t[:110]!r}")
            print(f"     before: {before}")
            print(f"     after:  {after}")
        if a.limit and len(changed) > a.limit:
            print(f"\n  ... {len(changed) - a.limit} more not shown (--limit {a.limit})")
        return 1 if changed else 0
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

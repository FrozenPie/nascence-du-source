"""
J-2437 -- Ambiguity Window Stage A replay (plan docs/staged/ambiguity_window.md section 5). READ-ONLY over the data
files, NO dispatch, writes nothing under the repo's data/. Output goes to --out (default: a J-2437 file in cwd).

Corpora (data dir = $NASCENCE_DATA or C:\\Nascence\\data; a git worktree has no data/):
  A  founder_conversation_log.jsonl   Du's full conversational replies + Travis's message (93 rows): window = in-reply
                                      sentences + Du's previous 2 replies + location/hands from the nearest earlier
                                      hands_trace rows + Travis's message (context only).
  B  conversational_action_log.jsonl  the 40-row bridge log (300-char excerpts); Travis's message joined by cycle_id.
  C  hands_trace.jsonl                the autonomous thought history (the J-1689 cross-sentence corpus is a subset of
                                      it): window = earlier sentences of the thought + the previous 5 real acts.
For each reply: baseline (guard on raw text) vs legacy (live one-line resolver) vs window (this module).
"""
import argparse
import bisect
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE anything lab_env-like: the worktree copy must win)
assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT.resolve()).lower()), core.__file__
from core import ambiguity_window as aw  # noqa: E402
from core import literal_will as lw      # noqa: E402

DATA = Path(os.environ.get("NASCENCE_DATA", r"C:\Nascence\data"))


def jl(name):
    out = []
    with open(DATA / name, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="ambiguity_window_replay_J-2437.json")
    ap.add_argument("--limit-c", type=int, default=0)
    ap.add_argument("--sentences", type=int, default=0, help="override aw.WINDOW_SENTENCES (section 6 q1 sweep)")
    a = ap.parse_args()
    if a.sentences:
        aw.WINDOW_SENTENCES = a.sentences
    print("WINDOW_SENTENCES =", aw.WINDOW_SENTENCES)
    t0 = time.time()
    hands = jl("hands_trace.jsonl")
    hts = [float(h.get("ts", 0)) for h in hands]
    founder = jl("founder_conversation_log.jsonl")
    bridge = jl("conversational_action_log.jsonl")
    human_by_cycle = {r.get("cycle_id"): r.get("human", "") for r in founder}
    print(f"hands_trace {len(hands)}  founder {len(founder)}  bridge {len(bridge)}  ({time.time()-t0:.1f}s load)")

    def ctx_at(ts):
        i = bisect.bisect_left(hts, ts) - 1
        loc, acts = "study", []
        if i >= 0 and ts - hts[i] < 3 * 3600:
            loc = hands[i].get("location") or "study"
        j = i
        while j >= 0 and len(acts) < aw.WINDOW_HANDS and i - j < 400:
            h = hands[j]
            if h.get("act_kind") and h.get("act_kind") != "none":
                acts.append({"act_kind": h["act_kind"], "act_object": h.get("act_object", ""), "location": h.get("location", "")})
            j -= 1
        return loc, list(reversed(acts))

    results = {}

    def run(name, rows):
        """rows: iterable of dict(text, loc, acts, prior, travis, meta)"""
        agg = Counter()
        per_kind = defaultdict(Counter)
        newly, legacy_only, lost, lit, anaphora_unres, vetoed = [], [], [], [], [], []
        for r in rows:
            agg["replies"] += 1
            w = aw.build_window(r["text"], location=r["loc"], recent_actions=r["acts"], prior_turns=r["prior"],
                                travis_last=r["travis"])
            rec = aw.annotate(r["text"], w, r["loc"])
            if rec.get("error"):
                agg["errors"] += 1
            agg["baseline_answered"] += len(rec.get("baseline_kept", []))
            for an in rec["anaphora"]:
                agg["anaphora_matches"] += 1
                if an["resolved"]:
                    agg["anaphora_resolved"] += 1
                    per_kind["anaphora"]["resolved_" + an["source"]] += 1
                else:
                    anaphora_unres.append({"meta": r["meta"], "verb": an["verb"], "why": an["why"], "competing": an["competing"]})
                    per_kind["anaphora"]["unresolved_" + (an["why"] or "?")] += 1
            for fam, ph in rec["newly_answered"]:
                per_kind["anaphora"]["newly_answered"] += 1
                newly.append({"meta": r["meta"], "family": fam, "phrase": ph, "text": r["text"][:400], "travis": r["travis"][:120]})
            for fam, ph in rec["newly_vs_legacy"]:
                per_kind["anaphora"]["newly_vs_legacy"] += 1
            for fam, ph in rec.get("legacy_only", []):
                per_kind["anaphora"]["legacy_only"] += 1
                legacy_only.append({"meta": r["meta"], "family": fam, "phrase": ph})
            for fam, ph in rec["lost"]:
                lost.append({"meta": r["meta"], "family": fam, "phrase": ph})
            for x in rec["vetoed"]:
                vetoed.append({"meta": r["meta"], "x": x})
                per_kind["frame"]["figurative_vetoes"] += 1
            if rec["frame"]:
                per_kind["frame"]["frame_" + rec["frame"]["frame"]] += 1
            for l in rec["literal_figurative"]:
                per_kind["literal_vs_figurative"]["annotated"] += 1
                per_kind["literal_vs_figurative"]["here_" + str(l["here"])] += 1
                lit.append({"meta": r["meta"], "clause": l["clause"], "here": l["here"], "evidence": l["evidence"], "loc": r["loc"]})
        results[name] = {"agg": dict(agg), "per_kind": {k: dict(v) for k, v in per_kind.items()},
                         "newly_answered": newly, "legacy_only": legacy_only, "lost": lost, "literal": lit,
                         "anaphora_unresolved": anaphora_unres, "vetoed": vetoed}
        print(name, dict(agg), {k: dict(v) for k, v in per_kind.items()}, f"{time.time()-t0:.0f}s")

    # A -- founder log
    rowsA, prior = [], []
    for r in founder:
        loc, acts = ctx_at(float(r.get("ts", 0)))
        rowsA.append({"text": r.get("entity", ""), "loc": loc, "acts": acts, "prior": list(prior[-2:]),
                      "travis": r.get("human", ""), "meta": {"corpus": "A", "cycle": r.get("cycle_id"), "ts": r.get("ts")}})
        prior.append(r.get("entity", ""))
    run("A_founder_conversation", rowsA)

    # B -- bridge log excerpts
    rowsB = []
    for r in bridge:
        rowsB.append({"text": r.get("reply_excerpt", ""), "loc": r.get("location") or "study", "acts": ctx_at(float(r.get("ts", 0)))[1],
                      "prior": [], "travis": human_by_cycle.get(r.get("cycle_id"), ""),
                      "meta": {"corpus": "B", "cycle": r.get("cycle_id"), "ts": r.get("ts")}})
    run("B_bridge_log", rowsB)

    # C -- autonomous thoughts. Rows with no `I ... them|it` match and no "I <motion verb>" cannot differ from baseline
    # (the window only rewrites a pronoun object or annotates a move_no_destination drop), so they are skipped; the
    # skip is reported as a count, not hidden.
    import re
    interesting = re.compile(r"(?i)\bi (?:will |'ll )?(?:\w+ )?\w+ (?:them|it)\b|\bi (?:\w+ ){0,3}(?:step|go|walk|head|move|return|climb)\b")
    rowsC, skipped, window_acts = [], 0, []
    for i, h in enumerate(hands):
        if h.get("act_kind") and h.get("act_kind") != "none":
            window_acts.append({"act_kind": h["act_kind"], "act_object": h.get("act_object", ""), "location": h.get("location", "")})
        txt = h.get("thought") or ""
        if len(txt) < 8:
            continue
        if not interesting.search(txt):
            skipped += 1
            continue
        rowsC.append({"text": txt, "loc": h.get("location") or "study", "acts": list(window_acts[-6:-1]) if window_acts else [],
                      "prior": [], "travis": "", "meta": {"corpus": "C", "i": i, "ts": h.get("ts")}})
        if a.limit_c and len(rowsC) >= a.limit_c:
            break
    print("C rows to replay", len(rowsC), "skipped (cannot differ)", skipped)
    run("C_hands_trace_thoughts", rowsC)
    results["C_hands_trace_thoughts"]["agg"]["skipped_cannot_differ"] = skipped
    results["C_hands_trace_thoughts"]["agg"]["total_thoughts"] = len(hands)

    Path(a.out).write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", a.out, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()

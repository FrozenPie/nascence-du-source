"""scripts/causal_debt_read.py -- J-2533 (plan epistemics_phase_c; idea I-0111, F-3225 direction 6).

CAUSAL DEBT: for each standing conclusion, walk its lineage down to the leaves and score the share of
leaves that are world contact vs self-generated; then invert -- for each self-generated (ungrounded) leaf,
count the standing conclusions that rest on it, and report the most load-bearing ones. The mirror of
core/identity_cost.py's embeddedness: over an UNVERIFIED claim, embeddedness is vulnerability, not strength.
Founder-facing only. Nothing here reaches Du (D-0434: no readout). Read-only, zero LLM, no core import
(stdlib only). Opens the SQLite store with mode=ro&immutable=1 -- point it at a backup copy (default: the
boot backup data/backups/nascence_20261029_183806.db); writes nothing under data/.
Sibling: scripts/assembly_signature_read.py (J-2518, F-3248) walks the same chains UPWARD for the
assembly index; the PARENTS definition below is identical to it on purpose.

DECLARED BEFORE LOOKING AT ANY RESULT (do not tune to the outcome)
-----------------------------------------------------------------
PARENTS(x) = ids in memory_fragments.derived_from (strings; dict entries contribute their 'target_ids')
  UNION child_ids of memory_links rows (parent_id = x, link_type = 'distilled_from').
STANDING CONCLUSIONS = memory_fragments with origin in STANDING_ORIGINS, excluding retracted rows
  (content starting '[RETRACTED'). Held object hypotheses are NOT in the SQLite store and carry no
  provenance (core/object_hypothesis.py docstring: 1476 of 1476 inferences had empty provenance), so
  they are reported as unreachable, not walked.
WALK: depth-first over PARENTS with a visited set (a node is entered once; closures that meet an already-visited node -- a diamond or a cycle -- are counted). A LEAF is
  a node with no parents: a fragment with empty lineage, a shadow_events / light_events row (those tables
  carry no lineage), or an id that resolves nowhere (MISSING).
LEAF CLASS (WORLD = world contact, SELF = self-generated, OTHER = neither declared, MISSING):
  fragment origin -> WORLD_ORIGINS / SELF_ORIGINS below, anything else OTHER.
  shadow_events.source: prediction_error WORLD (a felt value checked against a measured one);
    critic_rejection, unresolved_dream, unresolved_thought SELF.
  light_events.source: reading_integration, essay, understanding WORLD; integration WORLD iff its
    raw_input starts '(grounded:' else SELF; resolved_dream, resolved_thought, play SELF;
    resolved_complexity OTHER (its raw_input mixes human turns and his own questions).
SCORE per standing conclusion: grounded_share = WORLD / (WORLD + SELF) over its DISTINCT leaves;
  debt = 1 - grounded_share. OTHER and MISSING leaves are reported, never folded into either side.
INVERSION: load(leaf) = number of standing conclusions whose closure contains that SELF leaf.
  TOP_N = 10 most load-bearing SELF leaves reported (ties broken by leaf timestamp, oldest first).
  HIGH_DEBT_LEAF = a SELF leaf whose load is in the top decile (>= HIGH_PCTL percentile) of SELF leaf loads.
COVERAGE: share of ALL fragments with non-empty PARENTS; share of standing conclusions with any lineage.
THE TEST (GPT's): did any retraction / contradiction event land on a high-debt leaf FIRST? Only events
  that carry an id are testable: retracted fragments (content '[RETRACTED', core/memory/store.py
  retract_fragment) and data/retractions.jsonl rows (text only, matched to fragments by their 'claimed'
  prefix). data/contradiction_ledger_log.jsonl carries aggregate pressure + a top label, no ids, and
  data/tensions_archive.jsonl clusters are the SOURCE of syntheses (circular), so neither is used.
  For each testable event: is its fragment a leaf / node in any standing conclusion's closure, its load,
  and whether it is a HIGH_DEBT_LEAF. With fewer than MIN_EVENTS testable events the test is reported
  as UNRUNNABLE, not as a pass or a fail.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from collections import Counter, defaultdict

DEFAULT_DB = r"C:\Nascence\data\backups\nascence_20261029_183806.db"
DEFAULT_RETRACTIONS = r"C:\Nascence\data\retractions.jsonl"
STANDING_ORIGINS = ("standing_insight", "understanding", "understanding_from_guidance")
WORLD_ORIGINS = {"reading", "study", "research", "lived", "action", "activity", "sound", "listening",
                 "smell", "light", "thermal", "nature", "peer", "understanding", "understanding_from_guidance"}
SELF_ORIGINS = {"inner_thought", "subconscious_synthesis", "active_imagination", "dream", "night_thought",
                "consolidation", "gist", "standing_insight", "journal", "journal_week", "composition",
                "peer_reflection", "mirror"}
SHADOW_CLASS = {"prediction_error": "WORLD", "critic_rejection": "SELF", "unresolved_dream": "SELF", "unresolved_dream_rest": "SELF",
                "unresolved_thought": "SELF"}
LIGHT_CLASS = {"reading_integration": "WORLD", "essay": "WORLD", "understanding": "WORLD",
               "resolved_dream": "SELF", "resolved_thought": "SELF", "play": "SELF",
               "resolved_complexity": "OTHER"}  # integration handled by raw_input prefix
TOP_N = 10
HIGH_PCTL = 90
MIN_EVENTS = 5
SNIP = 110


def parse_parents(raw):
    try:
        L = json.loads(raw or "[]")
    except Exception:
        return []
    out = []
    for x in L if isinstance(L, list) else []:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            t = x.get("target_ids")
            if isinstance(t, list):
                out.extend(i for i in t if isinstance(i, str))
    return out


def iso(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--retractions", default=DEFAULT_RETRACTIONS)
    ap.add_argument("--out", required=True, help="JSON result path (outside C:\\Nascence\\data)")
    a = ap.parse_args()
    assert "\\data\\memory\\" not in a.db.lower().replace("/", "\\"), "point --db at a backup copy, not the live store"
    assert "\\nascence\\data\\" not in a.out.lower().replace("/", "\\"), "never write under data/"
    t0 = time.time()
    c = sqlite3.connect(f"file:{a.db}?mode=ro&immutable=1", uri=True)

    frag = {}  # id -> [origin, ts, parents, snippet]
    for fid, o, ts, df, ct in c.execute(
            "SELECT fragment_id, origin, timestamp, derived_from, substr(content,1,?) FROM memory_fragments", (SNIP + 40,)):
        frag[fid] = [o, ts or 0.0, parse_parents(df), ct or ""]
    links = defaultdict(list)
    for p, ch in c.execute("SELECT parent_id, child_id FROM memory_links WHERE link_type='distilled_from'"):
        links[p].append(ch)
    ev = {}  # id -> (table, source, class, ts, snippet)
    for eid, src, ts, draft in c.execute("SELECT event_id, source, timestamp, substr(rejected_draft,1,?) FROM shadow_events", (SNIP,)):
        ev[eid] = ("shadow", src, SHADOW_CLASS.get(src, "OTHER"), ts, draft or "")
    for eid, src, ts, raw, integ in c.execute(
            "SELECT event_id, source, timestamp, substr(raw_input,1,12), substr(integrated_content,1,?) FROM light_events", (SNIP,)):
        k = ("WORLD" if (raw or "").startswith("(grounded:") else "SELF") if src == "integration" else LIGHT_CLASS.get(src, "OTHER")
        ev[eid] = ("light", src, k, ts, integ or "")

    def parents(fid):
        if fid not in frag:
            return []
        return list(dict.fromkeys(frag[fid][2] + links.get(fid, [])))

    def leaf_class(x):
        if x in frag:
            o = frag[x][0]
            return "WORLD" if o in WORLD_ORIGINS else "SELF" if o in SELF_ORIGINS else "OTHER"
        if x in ev:
            return ev[x][2]
        return "MISSING"

    def leaf_kind(x):
        if x in frag:
            return "fragment:" + frag[x][0]
        if x in ev:
            return ev[x][0] + ":" + ev[x][1]
        return "missing"

    retracted = {f for f, v in frag.items() if v[3].startswith("[RETRACTED")}
    standing = [f for f, v in frag.items() if v[0] in STANDING_ORIGINS and f not in retracted]
    n_frag_lineage = sum(1 for f in frag if parents(f))

    per, load, nodes_of = {}, defaultdict(set), defaultdict(set)
    back_edges, leaf_kinds_all = 0, Counter()
    for s in standing:
        seen, todo, leaves, back = {s}, [s], set(), False
        while todo:
            v = todo.pop()
            ps = parents(v)
            if not ps and v != s:
                leaves.add(v)
            for p in ps:
                if p in seen:
                    back = True
                    continue
                seen.add(p)
                if p in frag:
                    todo.append(p)
                else:
                    leaves.add(p)
        back_edges += back
        for x in seen:
            nodes_of[x].add(s)
        cnt = Counter(leaf_class(x) for x in leaves)
        for x in leaves:
            leaf_kinds_all[leaf_kind(x)] += 1
            if leaf_class(x) == "SELF":
                load[x].add(s)
        w, sf = cnt["WORLD"], cnt["SELF"]
        per[s] = {"origin": frag[s][0], "ts": frag[s][1], "has_lineage": bool(parents(s)), "n_leaves": len(leaves),
                  "WORLD": w, "SELF": sf, "OTHER": cnt["OTHER"], "MISSING": cnt["MISSING"],
                  "grounded_share": round(w / (w + sf), 4) if (w + sf) else None}

    walked = [s for s in standing if per[s]["has_lineage"]]
    gs = sorted(per[s]["grounded_share"] for s in walked if per[s]["grounded_share"] is not None)
    by_origin = {}
    for o in STANDING_ORIGINS:
        ss = [s for s in standing if frag[s][0] == o]
        by_origin[o] = {"n": len(ss), "with_lineage": sum(per[s]["has_lineage"] for s in ss)}

    loads = sorted((len(v) for v in load.values()), reverse=False)
    def pctl(arr, q):
        if not arr:
            return None
        i = min(len(arr) - 1, max(0, int(round(q / 100 * (len(arr) - 1)))))
        return arr[i]
    high_t = pctl(loads, HIGH_PCTL)
    def ts_of(x):
        return frag[x][1] if x in frag else ev[x][3] if x in ev else 0.0
    def snip(x):
        return (frag[x][3] if x in frag else ev[x][4] if x in ev else "")[:SNIP]
    kids = defaultdict(set)
    for f_, v_ in frag.items():
        for p_ in v_[2]:
            kids[p_].add(f_)
    ranked = sorted(load.items(), key=lambda kv: (-len(kv[1]), ts_of(kv[0])))
    top = [{"leaf_id": x, "kind": leaf_kind(x), "ts": iso(ts_of(x)), "load": len(ss), "direct_children": len(kids.get(x, ())),
            "descendant_standing_ids": sorted(ss)[:12], "snippet": snip(x)} for x, ss in ranked[:TOP_N]]
    wload = defaultdict(int)
    for x, ss in nodes_of.items():
        if x not in per and leaf_class(x) == "WORLD" and not parents(x):
            wload[x] = len(ss)
    top_world = sorted(wload.items(), key=lambda kv: -kv[1])[:3]

    # --- the test ------------------------------------------------------------------------------
    events = []
    for f in sorted(retracted):
        events.append({"source": "retracted_fragment", "fragment_id": f, "origin": frag[f][0], "ts": iso(frag[f][1])})
    try:
        for line in open(a.retractions, encoding="utf-8"):
            r = json.loads(line)
            needle = (r.get("claimed") or "")[:70]
            hit = [f for f, v in frag.items() if needle and needle in v[3]] if len(needle) >= 12 else []
            events.append({"source": "retractions.jsonl", "status": r.get("status"), "matched_fragment_ids": hit[:5],
                           "fragment_id": hit[0] if hit else None, "ts": iso(r.get("ts"))})
    except FileNotFoundError:
        pass
    for e in events:
        f = e.get("fragment_id")
        e["in_standing_closure"] = bool(f and f in nodes_of)
        e["standing_descendants"] = len(nodes_of.get(f, ())) if f else 0
        e["is_self_leaf"] = bool(f and f in load)
        e["high_debt_leaf"] = bool(f and f in load and high_t is not None and len(load[f]) >= high_t)
    testable = [e for e in events if e.get("fragment_id")]
    verdict = ("UNRUNNABLE" if len(testable) < MIN_EVENTS else
               "HIGH_DEBT_FIRST" if any(e["high_debt_leaf"] for e in testable) else "NO_HIGH_DEBT_HIT")

    out = {
        "db": a.db, "run_secs": round(time.time() - t0, 1),
        "declared": {"STANDING_ORIGINS": STANDING_ORIGINS, "TOP_N": TOP_N, "HIGH_PCTL": HIGH_PCTL,
                     "MIN_EVENTS": MIN_EVENTS},
        "coverage": {"n_fragments": len(frag), "fragments_with_lineage": n_frag_lineage,
                     "share_fragments_with_lineage": round(n_frag_lineage / len(frag), 4),
                     "n_standing": len(standing), "standing_walked": len(walked),
                     "share_standing_reachable": round(len(walked) / len(standing), 4) if standing else None,
                     "standing_by_origin": by_origin, "retracted_excluded": len(retracted),
                     "held_hypotheses": "not in SQLite store, empty provenance (core/object_hypothesis.py): unreachable",
                     "standing_with_shared_subnodes": back_edges},
        "leaf_kinds_over_closures": dict(leaf_kinds_all.most_common()),
        "grounded_share": {"n_scored": len(gs), "median": pctl(gs, 50), "p10": pctl(gs, 10), "p90": pctl(gs, 90),
                           "n_fully_ungrounded": sum(1 for g in gs if g == 0.0),
                           "n_fully_grounded": sum(1 for g in gs if g == 1.0),
                           "n_no_world_or_self_leaf": sum(1 for s in walked if per[s]["grounded_share"] is None)},
        "self_leaf_load": {"n_self_leaves": len(load), "max": loads[-1] if loads else None,
                           "median": pctl(loads, 50), "high_debt_threshold": high_t,
                           "n_load_ge_2": sum(1 for x in loads if x >= 2),
                           "histogram": dict(sorted(Counter(loads).items()))},
        "top_self_leaves": top,
        "top_world_leaves_for_contrast": [{"leaf_id": x, "kind": leaf_kind(x), "load": n} for x, n in top_world],
        "test": {"verdict": verdict, "n_events": len(events), "n_testable": len(testable), "events": events,
                 "not_used": {"contradiction_ledger_log.jsonl": "aggregate pressure + label, no ids",
                              "tensions_archive.jsonl": "clusters are the source of syntheses (circular)"}},
        "per_standing_examples": {s: per[s] for s in sorted(walked, key=lambda s: (per[s]["grounded_share"] or 0))[:5]},
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(json.dumps({k: out[k] for k in ("coverage", "grounded_share", "self_leaf_load", "leaf_kinds_over_closures")}, indent=1))
    for t in top:
        print(t["load"], t["leaf_id"], t["kind"], t["ts"], "|", t["snippet"][:80].replace("\n", " "))
    print("WORLD contrast", out["top_world_leaves_for_contrast"])
    print("TEST", verdict, json.dumps(events)[:900])


if __name__ == "__main__":
    main()

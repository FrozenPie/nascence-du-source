"""
Nascence -- curated voice set cut by the DECOUPLED verdicts (J-3256, builds D-0645; follows J-2205 / J-2579 / F-3010).

READ-ONLY on every live store. Writes exactly two NEW derived files (atomic, never over a corpus):
    <data>/training/voice_set_decoupled.jsonl          the kept voice rows, decoupled verdicts joined per row
    <data>/training/voice_set_decoupled.summary.json   size, per-source coverage, critic agreement (the proof)
It imports nothing from core/ or nodes/ (import-time paths write live data/: F-2406/F-2423). NOTHING IS TRAINED ON
THE OUTPUT: training needs a separate founder ruling (D-0645).

THE RULE (stated before it was run; the founder can re-cut with --sources):
  A voice row is KEPT iff it carries at least one decoupled verdict AND none of the verdicts it carries is
  unfavourable (a veto). A row with no decoupled verdict is UNCOVERED and is not in the set: only the in-pipeline
  critic ever saw it, and the critic is the judge D-0645 declines to trust alone. A row with any unfavourable verdict
  is DROPPED.
  Sources (all three are other-model-family panels, none is the hot lane that writes Du's voice):
    social    core/social_cognition_shadow: tracks_intent on the reply Travis actually received. Human turns only.
              favourable = tracks_intent True; unfavourable = False. Of the criterion-3 fields (attributes /
              attrib_supported) NONE is used: F-3268 impeached the v3 attributes gate (true on every row), D-0519.
              One verdict per cycle: the newest row of the highest prompt_v that has a ruling. It is attached only to
              the voice row whose final text IS the logged reply (founder_conversation_log entity): a cycle with two
              voice rows (a redraft) has one delivered reply and the verdict does not describe the other draft.
    self_int  core/self_interrogation: genuine on the cycle's thought (the thing the voice renders). any False =
              unfavourable, else any True = favourable, None = no verdict.
    panel     data/judge_panel_log.jsonl rows carrying cycle_id, key == "advances" only (pursuit_close: did the cycle's
              thought ADVANCE a pursuit or restate one). The other panel rows that carry cycle_id are TRANSPORT of the
              two sources above (key "genuine" = self_int's ruling, node=="voice" keys tracks/refs/attributes/supported
              = social's sub-rulings) and are counted once, in their own source, never twice. any False = unfavourable.
  The in-pipeline critic (data/training/critic.jsonl, newest row per cycle, output.approved) is NOT part of the rule;
  it is joined only to measure how differently the cut behaves.

Run:  python scripts/build_voice_set.py [--data DIR] [--out PATH] [--sources social,self_int,panel] [--dry-run] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALL_SOURCES = ("social", "self_int", "panel")
MIN_SET = 300           # D-0645 defeater: a joined set under this is too small to be useful
AGREE_BAR = 0.95        # D-0645 defeater: decoupled verdicts agreeing with the critic on more than this change nothing
MATCH_PREFIX = 60


def _rows(path: Path):
    if not path.exists():
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                yield r


def _final(row: dict) -> str:
    o = row.get("output")
    if isinstance(o, dict):
        return str(o.get("final") or "").strip()
    return ""


def _fav(labels: list) -> str | None:
    """'fav' / 'unfav' / None from a list of True/False/None rulings. Any False vetoes."""
    vals = [v for v in labels if v is True or v is False]
    if not vals:
        return None
    return "unfav" if False in vals else "fav"


def load_sources(data: Path) -> dict:
    social: dict[str, dict] = {}
    for r in _rows(data / "social_cognition_shadow.jsonl"):
        cid, ti = r.get("cycle_id"), r.get("tracks_intent")
        if not cid or ti not in (True, False):
            continue
        key = (int(r.get("prompt_v") or 0), float(r.get("ts") or 0.0))
        if cid not in social or key >= social[cid]["_key"]:
            social[str(cid)] = {"_key": key, "tracks_intent": ti, "prompt_v": r.get("prompt_v"), "kind": r.get("kind"),
                                "human_ts": r.get("human_ts"), "backfill": bool(r.get("backfill"))}
    self_int: dict[str, list] = defaultdict(list)
    for r in _rows(data / "self_interrogation_shadow.jsonl"):
        if r.get("kind") == "interrogate" and r.get("cycle_id"):
            self_int[str(r["cycle_id"])].append(r.get("genuine"))
    panel: dict[str, list] = defaultdict(list)
    transport = Counter()
    for r in _rows(data / "judge_panel_log.jsonl"):
        cid = r.get("cycle_id")
        if not cid:
            continue
        if r.get("key") == "advances":
            panel[str(cid)].append(r.get("verdict"))
        else:
            transport[str(r.get("key"))] += 1
    critic: dict[str, tuple] = {}
    critic_n: Counter = Counter()
    for r in _rows(data / "training" / "critic.jsonl"):
        cid, o = r.get("cycle_id"), r.get("output")
        if cid and isinstance(o, dict) and "approved" in o:
            critic_n[str(cid)] += 1
            ts = float(r.get("ts") or 0.0)
            if str(cid) not in critic or ts >= critic[str(cid)][0]:
                critic[str(cid)] = (ts, bool(o.get("approved")))
    entity: dict[str, str] = {}
    for r in _rows(data / "founder_conversation_log.jsonl"):
        if r.get("cycle_id"):
            entity[str(r["cycle_id"])] = str(r.get("entity") or "").strip()
    return {"social": social, "self_int": self_int, "panel": panel, "transport": transport,
            "critic": {c: v[1] for c, v in critic.items()}, "critic_n": critic_n, "entity": entity}


def decide_row(row: dict, src: dict, sources: tuple) -> dict:
    cid = str(row.get("cycle_id") or "")
    v: dict[str, dict | None] = {"social": None, "self_int": None, "panel": None}
    s = src["social"].get(cid)
    if s is not None:
        ent = src["entity"].get(cid, "")
        fin = _final(row)
        sent = (not ent) or fin[:MATCH_PREFIX] == ent[:MATCH_PREFIX]
        if sent:
            v["social"] = {"verdict": "fav" if s["tracks_intent"] else "unfav", "tracks_intent": s["tracks_intent"],
                           "prompt_v": s["prompt_v"], "kind": s["kind"], "reply_text_matched": bool(ent)}
    if cid in src["self_int"]:
        labs = src["self_int"][cid]
        f = _fav(labs)
        if f:
            v["self_int"] = {"verdict": f, "genuine": labs}
    if cid in src["panel"]:
        labs = src["panel"][cid]
        f = _fav(labs)
        if f:
            v["panel"] = {"verdict": f, "advances": labs}
    used = [v[k]["verdict"] for k in sources if v[k]]
    if not used:
        status = "uncovered"
    elif "unfav" in used:
        status = "dropped"
    else:
        status = "kept"
    crit = src["critic"].get(cid)
    return {"status": status, "decoupled": v, "critic_approved": crit, "critic_rows": src["critic_n"].get(cid, 0)}


def build(data: Path, sources: tuple = ALL_SOURCES) -> tuple[list, dict]:
    src = load_sources(data)
    kept: list[dict] = []
    status_n: Counter = Counter()
    cross: Counter = Counter()           # (decoupled status, critic) -> n
    cov: Counter = Counter()             # per-source verdict coverage
    cov_v: dict[str, Counter] = {k: Counter() for k in ALL_SOURCES}
    n = 0
    human_n: Counter = Counter()
    veto: Counter = Counter()            # which source(s) vetoed a dropped row
    per_src_vs_critic: dict[str, Counter] = {k: Counter() for k in ALL_SOURCES}
    for row in _rows(data / "training" / "voice.jsonl"):
        n += 1
        d = decide_row(row, src, sources)
        status_n[d["status"]] += 1
        cross[(d["status"], {True: "critic_keep", False: "critic_drop", None: "critic_none"}[d["critic_approved"]])] += 1
        human_n[(str(row.get("input_type")), d["status"])] += 1
        if d["status"] == "dropped":
            veto["+".join(k for k in sources if d["decoupled"][k] and d["decoupled"][k]["verdict"] == "unfav")] += 1
        for k in ALL_SOURCES:
            if d["decoupled"][k]:
                cov[k] += 1
                cov_v[k][d["decoupled"][k]["verdict"]] += 1
                if d["critic_approved"] is not None:
                    per_src_vs_critic[k]["%s|%s" % (d["decoupled"][k]["verdict"],
                                                    "critic_keep" if d["critic_approved"] else "critic_drop")] += 1
        if d["status"] == "kept":
            out = dict(row)
            out["decoupled"] = d["decoupled"]
            out["decoupled_status"] = "kept"
            out["critic_approved"] = d["critic_approved"]
            kept.append(out)
    # agreement: over rows that HAVE a decoupled verdict AND a critic verdict, does keep/drop match the critic?
    cmp_keep = {"kept": True, "dropped": False}
    both = agree = 0
    crit_keep_dec_drop = crit_drop_dec_keep = 0
    for (st, cr), k in cross.items():
        if st in cmp_keep and cr != "critic_none":
            both += k
            if cmp_keep[st] == (cr == "critic_keep"):
                agree += k
            elif cr == "critic_keep":
                crit_keep_dec_drop += k
            else:
                crit_drop_dec_keep += k
    summary = {
        "rule": "keep iff >=1 decoupled verdict among %s and none unfavourable (any unfavourable vetoes)" % ",".join(sources),
        "sources_enabled": list(sources), "voice_rows": n,
        "status": dict(status_n), "set_size_rows": len(kept),
        "set_size_cycles": len({r["cycle_id"] for r in kept}),
        "per_source_coverage_rows": dict(cov),
        "per_source_verdict_split_rows": {k: dict(c) for k, c in cov_v.items()},
        "panel_transport_rows_not_counted_here": dict(src["transport"]),
        "dropped_by_vetoing_source": dict(veto),
        "each_source_vs_critic": {k: dict(c) for k, c in per_src_vs_critic.items()},
        "by_input_type_and_status": {"%s/%s" % k: v for k, v in sorted(human_n.items())},
        "decoupled_vs_critic_crosstab": {"%s|%s" % k: v for k, v in sorted(cross.items())},
        "agreement": {"rows_with_both": both, "agree": agree,
                      "agree_share": round(agree / both, 4) if both else None,
                      "critic_keep_decoupled_drop": crit_keep_dec_drop,
                      "critic_drop_decoupled_keep": crit_drop_dec_keep},
        "critic_kept_all_share": round(sum(1 for r in _rows(data / "training" / "voice.jsonl")
                                           if src["critic"].get(str(r.get("cycle_id"))) is True) / n, 4) if n else None,
        "defeater_check": {"min_set": MIN_SET, "set_cycles_ok": len({r["cycle_id"] for r in kept}) >= MIN_SET,
                           "agree_bar": AGREE_BAR,
                           "agreement_over_bar": bool(both and agree / both > AGREE_BAR)},
    }
    return kept, summary


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--data", type=Path, default=ROOT / "data")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--sources", default=",".join(ALL_SOURCES))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    sources = tuple(s for s in a.sources.split(",") if s in ALL_SOURCES)
    if not sources:
        print("no valid --sources", file=sys.stderr)
        return 2
    kept, summary = build(a.data, sources)
    out = a.out or (a.data / "training" / "voice_set_decoupled.jsonl")
    if out.name.split(".")[0] in {"voice", "critic", "reflection", "executive", "recall", "salience", "emotion",
                                  "perception", "curiosity", "consolidation", "episodic_buffer", "memory_router"}:
        print("refusing to write over a live teacher corpus: %s" % out, file=sys.stderr)
        return 2
    summary["out"] = str(out)
    if not a.dry_run:
        _atomic_write(out, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept))
        _atomic_write(out.with_name(out.stem + ".summary.json"), json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    if a.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("voice set (decoupled cut) -- rows=%d kept=%d (%d cycles) dropped=%d uncovered=%d%s" % (
            summary["voice_rows"], summary["set_size_rows"], summary["set_size_cycles"],
            summary["status"].get("dropped", 0), summary["status"].get("uncovered", 0), "  [dry-run]" if a.dry_run else ""))
        print("  coverage rows:", summary["per_source_coverage_rows"], " split:", summary["per_source_verdict_split_rows"])
        print("  agreement with critic:", summary["agreement"])
        print("  defeater check:", summary["defeater_check"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

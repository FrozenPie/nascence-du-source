"""
closure_index.py -- Organisational closure index for Du's commitments (J-2514, T-0106, plan capacity_to_commit).

Source: docs/reviews/frontier_disciplines_2026-10-30.md section 3 (Moreno & Mossio 2015; Rosen closure to efficient
causation), read (a). Question: of the commitments Du has HELD, what share has ANY downstream read into a loop?
Prediction (review): near zero. Plus a fail-open census of core/.

READ-ONLY. Zero LLM. Imports nothing from core/ or nodes/ (static AST + plain-file reads), so it cannot touch a live
store. Opens data/commitment_ledger.jsonl, data/nascence.log, data/coupling_rides.jsonl, data/dwell_release.jsonl,
data/emotion_construction_shadow.jsonl in read mode only. Nothing here reaches Du (D-0434).

DECLARED BEFORE LOOKING AT THE RESULT (do not tune):
  HELD_WINDOW_S      = 3600   primary: a commitment is HELD iff no 'dissolved' event for its id within this many
                              seconds of 'formed' AND some ledger event for the id (reaffirmed / drop_denied* /
                              achieved / dissolved) is at or after formed+window (positive evidence it was alive).
  SECONDARY_WINDOWS  = 6h, 24h  reported for sensitivity only.
  PREFIX_CHARS       = 30     a statement is "cited" by a text when the text (lower-cased, whitespace-collapsed)
                              contains the statement's first 30 normalised chars. Exact-prefix, no fuzzy matching.
  LOSS_GRACE_S       = 900    the dissolution felt-loss line may land up to this long after the 'dissolved' event.
  MENTION_MAX_SPAN_S = 7 days  topical-mention scan of nascence.log is capped to the first 7 days of a lifespan.
  MENTION_EXCLUDE    = lines from the commitment ledger's own logger ('[commitment]', 'nascence.commitment').

Read paths are declared in CODE_PATHS below from a hand trace of core/ and nodes/ (2026-10-30); the script re-checks
that every cited file:anchor string still exists so the table cannot silently go stale. Data reach is measured only
through paths that leave a content fingerprint in a log:
  R_LOSS     commitment_ledger._stakes('dissolved') -> sitting.note_difficulty("you let go of a stand you had held: ")
             -> nascence.log '[sitting]' lines.                                     (ends the lifespan; counted apart)
  R_CONTRA   self_claims.held_claims -> self_implication conversation scan -> orchestrator S2 license +
             sitting.note_difficulty("Travis contradicted a stand you hold: ") -> nascence.log "[s2] self-claim
             contradicted ('...')" and data/dwell_release.jsonl.
  R_CONCERN  concerns.current_concerns -> {"kind": "hold", "text": "a stand you hold: ..."} -> emotion_construction
             (fear threat-weight by KIND; text logged to data/emotion_construction_shadow.jsonl).
Topical persistence (B) is reported separately: a later nascence.log line citing the statement prefix during its
lifespan. B cannot tell a read path from topic continuity and is NOT counted as a read.

Usage: python scripts/closure_index.py [--repo C:/Nascence] [--json out.json]
"""
from __future__ import annotations

import argparse
import ast
import bisect
import datetime as _dt
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

HELD_WINDOW_S = 3600.0
SECONDARY_WINDOWS = (6 * 3600.0, 24 * 3600.0)
PREFIX_CHARS = 30
LOSS_GRACE_S = 900.0
MENTION_MAX_SPAN_S = 7 * 86400.0
MENTION_EXCLUDE = ("[commitment]", "nascence.commitment")

# (reader, file, anchor string that must exist, what it reads, kind)
#   kind: STEER   commitment CONTENT shapes what an action-selection loop picks (curiosity / dispatcher /
#                 idle anchor / Follow Line) -- the review's closure sense
#         REACT   commitment CONTENT reaches his thought/affect loop as a reaction (loss / contradiction)
#         CONTENT commitment content reaches a prompt or model but not an action-selection loop
#         SCALAR  count / flag only, no content
#         LOG     observe/shadow/log only
CODE_PATHS = [
    ("commitment_ledger._stakes(dissolved) -> sitting.note_difficulty", "core/commitment_ledger.py",
     "you let go of a stand you had held: ", "statement of a dissolved load-bearing stand -> raw difficulty -> "
     "sitting steer in the idle prompt", "REACT"),
    ("commitment_ledger._stakes(achieved|dissolved) -> satisfaction.record", "core/commitment_ledger.py",
     'satisfaction.record("commitment_held"', "event + 40-char label -> liking/wanting ledger", "SCALAR"),
    ("commitment_ledger._stakes(formed) -> memory_fragments importance bump", "core/commitment_ledger.py",
     "UPDATE memory_fragments SET importance=MIN(0.85, importance*1.08), protected=1",
     "statement LIKE-match -> fragment importance x1.08 + protected (recall salience)", "CONTENT"),
    ("self_claims.held_claims -> orchestrator S2 license + sitting (Travis contradicted)", "core/orchestrator.py",
     "Travis contradicted a stand you hold: ", "all active statements -> conversational contradiction judge -> "
     "next-cycle System-2 license + raw difficulty", "REACT"),
    ("self_claims.held_claims -> garden B4 bind on a sown plant's death", "core/garden.py",
     "That sits against something you've said about yourself", "keyword-matched statement -> raw difficulty",
     "REACT"),
    ("self_claims.held_claims -> self_implication.scan_shadow (idle)", "core/self_implication.py",
     "held = self_claims.held_claims()", "judge input, logs would-fire only", "LOG"),
    ("concerns.current_concerns -> emotion_construction fear weight", "core/concerns.py",
     "a stand you hold: ", "first load-bearing stand as a 'hold' concern; fear uses KIND weight 0.8, text "
     "only logged; primary_concern() (the idle anchor) never returns a hold", "SCALAR"),
    ("peers._du_world_context -> peer letter prompt", "core/peers.py",
     "He has lately taken a stand he is holding", "first load-bearing statement -> peer LLM prompt (a friend may "
     "ask after it); reaches Du only as the friend's letter", "CONTENT"),
    ("identity_estate.seed -> 'I hold:' stand node", "core/identity_estate.py",
     '"I hold: " + s[:160]', "load-bearing statements -> estate stand nodes", "CONTENT"),
    ("homeostasis._read_commitment -> commitment_integrity", "core/homeostasis.py",
     "def _read_commitment", "count of load-bearing + reaffirmations -> protoself scalar", "SCALAR"),
    ("coupling_rides coords", "core/coupling_rides.py",
     'coords["commitments_active"] = len(items)', "count + escalations_1h -> ride tuple", "SCALAR"),
    ("inner_monologue -> holdrate_snapshot", "nodes/inner_monologue_node.py",
     "_cl.holdrate_snapshot", "hold-rate north-star, logged", "LOG"),
    ("reentry_p2.on_commitment_scan_done", "core/reentry_p2.py",
     "def on_commitment_scan_done", "shadow settle of a draft COPY", "LOG"),
]
# Action-selection loops checked for ANY commitment read (none found by the trace; re-verified below by grep):
STEER_LOOPS = ["core/idle_allocator.py", "core/follow_line.py", "core/curiosity.py", "core/frontier.py",
               "core/pursuits.py", "core/dispatcher.py", "core/question_cargo.py"]
STEER_NEEDLES = ("commitment_active", "commitment_ledger", "held_claims", "self_claims", "current_concerns")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def _prefix(stmt: str) -> str:
    return _norm(stmt).strip(" .\"'")[:PREFIX_CHARS]


_LOG_TS = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) ")


def _log_ts(line: str):
    m = _LOG_TS.match(line)
    if not m:
        return None
    return time.mktime(_dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timetuple()) + int(m.group(2)) / 1000


# ---------------------------------------------------------------- fail-open census (static AST, core/ only)
def fail_open_census(repo: Path) -> dict:
    broad = swallow = files = 0
    flag_true = flag_false = 0
    flag_names = []
    for p in sorted((repo / "core").rglob("*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        files += 1
        for n in ast.walk(tree):
            if isinstance(n, ast.ExceptHandler):
                t = n.type
                names = []
                if t is None:
                    names = ["<bare>"]
                elif isinstance(t, ast.Name):
                    names = [t.id]
                elif isinstance(t, ast.Tuple):
                    names = [e.id for e in t.elts if isinstance(e, ast.Name)]
                if any(x in ("<bare>", "Exception", "BaseException") for x in names):
                    broad += 1
                    if not any(isinstance(s, ast.Raise) for b in n.body for s in ast.walk(b)):
                        swallow += 1
        for n in tree.body:
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                tgts = n.targets if isinstance(n, ast.Assign) else [n.target]
                val = n.value
                for tg in tgts:
                    if isinstance(tg, ast.Name) and re.search(r"(_ENABLED|_LIVE|_SHADOW)$|^(ENABLED|LIVE|SHADOW)$",
                                                               tg.id) and isinstance(val, ast.Constant) \
                            and isinstance(val.value, bool):
                        flag_names.append(f"{p.relative_to(repo).as_posix()}:{tg.id}={val.value}")
                        if val.value:
                            flag_true += 1
                        else:
                            flag_false += 1
    return {"core_files": files, "broad_except_handlers": broad, "swallowing_handlers_no_raise": swallow,
            "bool_flags_ENABLED_LIVE_SHADOW": flag_true + flag_false, "flags_true": flag_true,
            "flags_false": flag_false}


# ---------------------------------------------------------------- code-path table check
def check_code_paths(repo: Path) -> tuple[list, dict]:
    rows = []
    for reader, f, anchor, what, kind in CODE_PATHS:
        txt = (repo / f).read_text(encoding="utf-8", errors="replace") if (repo / f).exists() else ""
        line = next((i + 1 for i, l in enumerate(txt.splitlines()) if anchor in l), None)
        rows.append({"reader": reader, "file": f, "line": line, "anchor_found": line is not None,
                     "reads": what, "kind": kind})
    steer = {}
    for f in STEER_LOOPS:
        p = repo / f
        if not p.exists():
            steer[f] = "absent"
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        hits = [n for n in STEER_NEEDLES if n in txt]
        steer[f] = hits or "none"
    return rows, steer


# ---------------------------------------------------------------- ledger -> lifespans
def load_commitments(repo: Path) -> dict:
    by_id: dict = {}
    for l in open(repo / "data" / "commitment_ledger.jsonl", encoding="utf-8"):
        try:
            r = json.loads(l)
        except Exception:
            continue
        cid, ev, ts = r.get("id"), r.get("event"), float(r.get("ts", 0) or 0)
        if not cid:
            continue
        if ev == "formed":
            if cid in by_id:          # re-formed id: keep the first formation
                continue
            by_id[cid] = {"id": cid, "formed": ts, "statement": r.get("statement", ""),
                          "load_bearing": r.get("load_bearing"), "cycle_id": r.get("cycle_id"),
                          "events": []}
        elif cid in by_id:
            by_id[cid]["events"].append((ts, ev))
    for c in by_id.values():
        ev = sorted(c["events"])
        c["dissolved"] = next((t for t, e in ev if e == "dissolved"), None)
        c["achieved"] = next((t for t, e in ev if e == "achieved"), None)
        c["last"] = ev[-1][0] if ev else c["formed"]
        ends = [t for t in (c["dissolved"], c["achieved"]) if t is not None]
        c["end"] = min(ends) if ends else c["last"]
    return by_id


def is_held(c: dict, w: float) -> bool:
    if c["dissolved"] is not None and c["dissolved"] - c["formed"] < w:
        return False
    return c["last"] - c["formed"] >= w


# ---------------------------------------------------------------- data reach
def scan(repo: Path, held: list) -> dict:
    pref = {c["id"]: _prefix(c["statement"]) for c in held}
    reach = defaultdict(set)
    cites = defaultdict(list)
    # nascence.log -- one pass; keep timestamped lines for the mention scan
    log_ts, log_lines = [], []
    loss_lines, contra_lines = [], []
    with open(repo / "data" / "nascence.log", encoding="utf-8", errors="replace") as f:
        last_ts = None
        for line in f:
            ts = _log_ts(line)
            if ts is None:
                continue
            low = _norm(line)
            if "you let go of a stand you had held" in low:
                loss_lines.append((ts, low))
            if "self-claim contradicted" in low:
                contra_lines.append((ts, low))
            if any(x in line for x in MENTION_EXCLUDE):
                continue
            log_ts.append(ts)
            log_lines.append(low)
    dwell = []
    for l in open(repo / "data" / "dwell_release.jsonl", encoding="utf-8", errors="replace"):
        try:
            r = json.loads(l)
        except Exception:
            continue
        d = _norm(r.get("difficulty", ""))
        if "contradicted a stand you hold" in d:
            dwell.append((float(r.get("ts", 0)), d, r.get("cycle_id")))
    emo = []
    for l in open(repo / "data" / "emotion_construction_shadow.jsonl", encoding="utf-8", errors="replace"):
        if "a stand you hold" not in l:
            continue
        try:
            r = json.loads(l)
        except Exception:
            continue
        emo.append((float(r.get("ts", 0) or 0), _norm(l), r.get("cycle_id")))
    mention_n = Counter()
    for c in held:
        p, a, b = pref[c["id"]], c["formed"], c["end"]
        if len(p) < 12:
            continue
        for ts, low in loss_lines:
            if c["dissolved"] and c["dissolved"] - 5 <= ts <= c["dissolved"] + LOSS_GRACE_S and p in low:
                reach["R_LOSS"].add(c["id"]); cites[c["id"]].append(("R_LOSS", ts))
        for ts, low in contra_lines:
            if a <= ts <= b and p[:20] in low:       # the [s2] log line truncates the claim to 50 chars
                reach["R_CONTRA"].add(c["id"]); cites[c["id"]].append(("R_CONTRA_log", ts))
        for ts, d, cyc in dwell:
            if a <= ts <= b + LOSS_GRACE_S and p in d:
                reach["R_CONTRA"].add(c["id"]); cites[c["id"]].append(("R_CONTRA_dwell", ts, cyc))
        for ts, d, cyc in emo:
            if a <= ts <= b and p in d:
                reach["R_CONCERN"].add(c["id"]); cites[c["id"]].append(("R_CONCERN", ts, cyc))
        i = bisect.bisect_left(log_ts, a + 1.0)
        j = bisect.bisect_right(log_ts, min(b, a + MENTION_MAX_SPAN_S))
        for k in range(i, j):
            if p in log_lines[k]:
                mention_n[c["id"]] += 1
    # coupling_rides: count-only presence of active commitments during a lifespan
    rides_ts = []
    with open(repo / "data" / "coupling_rides.jsonl", encoding="utf-8", errors="replace") as f:
        for l in f:
            if '"commitments_active"' not in l:
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if (r.get("tuple") or {}).get("commitments_active"):
                rides_ts.append(float(r.get("ts", 0)))
    rides_ts.sort()
    rides_cover = sum(1 for c in held if bisect.bisect_right(rides_ts, c["end"]) - bisect.bisect_left(
        rides_ts, c["formed"]) > 0)
    return {"reach": {k: sorted(v) for k, v in reach.items()}, "cites": cites, "mention": mention_n,
            "fingerprint_rows": {"loss_log_lines": len(loss_lines), "s2_contra_log_lines": len(contra_lines),
                                 "dwell_contra_rows": len(dwell), "emotion_hold_rows": len(emo),
                                 "rides_rows_commitments_active_gt0": len(rides_ts),
                                 "nascence_log_ts_lines": len(log_ts)},
            "rides_cover_held": rides_cover}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    repo = Path(a.repo)
    census = fail_open_census(repo)
    paths, steer = check_code_paths(repo)
    allc = load_commitments(repo)
    held = [c for c in allc.values() if is_held(c, HELD_WINDOW_S)]
    sens = {f"{int(w // 3600)}h": sum(1 for c in allc.values() if is_held(c, w)) for w in SECONDARY_WINDOWS}
    s = scan(repo, held)
    ids_any = set().union(*[set(v) for v in s["reach"].values()]) if s["reach"] else set()
    ids_live = set(s["reach"].get("R_CONTRA", [])) | set(s["reach"].get("R_CONCERN", []))
    n = len(held)
    lb = sum(1 for c in held if c["load_bearing"])
    out = {
        "declared": {"HELD_WINDOW_S": HELD_WINDOW_S, "PREFIX_CHARS": PREFIX_CHARS, "LOSS_GRACE_S": LOSS_GRACE_S,
                     "MENTION_MAX_SPAN_S": MENTION_MAX_SPAN_S},
        "fail_open_census_core": census,
        "code_paths": paths,
        "steer_loops_commitment_needles": steer,
        "ledger": {"formed_ids": len(allc), "held_1h": n, "held_load_bearing": lb,
                   "held_by_secondary_window": sens,
                   "held_dissolved_later": sum(1 for c in held if c["dissolved"]),
                   "held_achieved": sum(1 for c in held if c["achieved"])},
        "fingerprint_rows": s["fingerprint_rows"],
        "reach_counts": {k: len(v) for k, v in s["reach"].items()},
        "share_any_fingerprinted_read": round(len(ids_any) / n, 4) if n else None,
        "share_read_while_held_excl_loss": round(len(ids_live) / n, 4) if n else None,
        "share_steer_read": 0.0 if all(v in ("none", "absent") for v in steer.values()) else None,
        "share_topical_mention_nascence_log": round(sum(1 for c in held if s["mention"][c["id"]]) / n, 4)
        if n else None,
        "rides_count_only_cover_held": s["rides_cover_held"],
        "example_cites": {cid: s["cites"][cid][:3] for cid in sorted(ids_any)[:12]},
    }
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

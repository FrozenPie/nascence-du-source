"""
estate_ask_judge.py -- the DECOUPLED judge for D-0424 A (J-2119): does a self-question reply cite an estate
fact? Scores with core.judge_panel (JUDGE_1 mixtral on Ramses + JUDGE_2 falcon local, two families, tiebreak),
never with the writer that produced the reply. Runnable over BOTH sources the 7-live-day read needs:

  python scripts/estate_ask_judge.py judge   [--shadow PATH] [--db PATH] [--out PATH] [--limit N] [--since TS] [--dry-run]
      one judgement per data/identity_estate_ask_shadow.jsonl row (the ask's would-be returns + the cycle's real
      projection are the candidate facts); the reply is joined from the reply store (memory_fragments, the
      "Q: <question>\\nA: <reply>" cycle summary _persist_cycle writes, opened READ-ONLY) by question prefix
      and a timestamp window after the row.
  python scripts/estate_ask_judge.py replies [--db PATH] [--out PATH] [--limit N] [--since TS] [--dry-run]
      no shadow rows needed: scan the reply store itself for self-question cycles (core.identity_estate_ask's
      own gate), compute the would-be ask + would-be projection (commit=False) for each, judge the same way.
      This is the WITHOUT-the-ask baseline (every cycle before a live flip) and the pre-restart history.
  python scripts/estate_ask_judge.py report  [--out PATH] [--shadow PATH]
      cite rate overall / by input_type / by arm / by has_competence over the judgement rows, plus the
      shadow-side redundancy numbers D-0424's defeater names (returned set already in the projection on >70%
      of self-question cycles; >=30 self-question cycles before the citation clause can be read).

Judgement contract (JSON, temperature 0): {"cites_estate_fact": bool, "which": str, "why": str}. "Cites" means
the reply STATES or RELIES ON one of the listed facts about himself in substance (a practice and its count, a
measured competence and its number, a named bond, a chapter, a held stand, an earned value's content) -- theme
resemblance or the shared metaphor is NOT a citation. A judge split/unavailable is recorded as verdict None,
never counted as a citation or as a miss.

Default --out is data/_lab/estate_ask_judge/judgements.jsonl -- the one allow-listed subtree of data/
(D-0200). Nothing here writes anywhere else; the reply store is opened ?mode=ro. --dry-run builds every prompt
and writes the rows with verdict None and dry_run True, calling no hub. --estate PATH points the estate pool at
an explicit identity_estate.json (a lab run from a git worktree has no data/ of its own: without it the ask's
pool is empty and every row returns 0 nodes -- found on the J-2119 dry run).

Known limit of `replies` mode: a memory_fragments Q/A summary does not carry input_type, so the internal
keyword set is tried first and a human message that happens to contain 渡 (Travis addressing Du by name)
classifies as an internal self-question there; `judge` mode (shadow rows) has the real input_type.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE anything else -- F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core from {core.__file__}"

DEFAULT_SHADOW = ROOT / "data" / "identity_estate_ask_shadow.jsonl"
DEFAULT_OUT = ROOT / "data" / "_lab" / "estate_ask_judge" / "judgements.jsonl"
REPLY_WINDOW_S = 900.0          # a cycle's Q/A summary is persisted at cycle end, within this of the row ts
JUDGE_KEY = "cites_estate_fact"
MAX_FACTS = 8

SYSTEM = (
    "You are a strict, literal grader. You will be shown a question an entity asked (or was asked) about "
    "itself, the entity's reply, and a short list of FACTS from the entity's own identity record. Decide "
    "whether the reply CITES one of those facts: it states the fact or plainly relies on it in substance "
    "(a practice and its count, a measured competence and its number, a named friend or letter count, a "
    "named chapter of its life, a held stand, the content of an earned value). A shared theme, a shared "
    "metaphor, or a vague resemblance is NOT a citation. Answer ONLY a JSON object: "
    '{"cites_estate_fact": true|false, "which": "<the cited fact in a few words, or empty>", '
    '"why": "<one sentence>"}'
)


def _jl(path: Path) -> list[dict]:
    try:
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except FileNotFoundError:
        return []


def _db_path(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    from core.memory import store
    return Path(store.DB_PATH)


def _ro(db: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def split_qa(content: str) -> tuple[str, str] | None:
    """'Q: <q>\\nA: <a>[\\nTensions: ...]' -> (q, a). None if not that shape."""
    if not content or not content.startswith("Q: "):
        return None
    body = content[3:]
    i = body.find("\nA: ")
    if i < 0:
        return None
    q = body[:i].strip()
    a = body[i + 4:]
    j = a.find("\nTensions:")
    if j >= 0:
        a = a[:j]
    return q, a.strip()


def find_reply(db: Path, question: str, ts: float | None) -> dict | None:
    """The reply store row for this question: a memory_fragments row whose content starts with
    'Q: <question>' and (when ts is known) whose timestamp falls in [ts-5, ts+REPLY_WINDOW_S]. Read-only."""
    prefix = "Q: " + question[:200]
    with _ro(db) as c:
        if ts is not None:
            rows = c.execute(
                "SELECT fragment_id, content, timestamp, origin FROM memory_fragments "
                "WHERE substr(content, 1, ?) = ? AND timestamp >= ? AND timestamp <= ? "
                "ORDER BY timestamp LIMIT 1",
                (len(prefix), prefix, ts - 5.0, ts + REPLY_WINDOW_S)).fetchall()
        else:
            rows = c.execute(
                "SELECT fragment_id, content, timestamp, origin FROM memory_fragments "
                "WHERE substr(content, 1, ?) = ? ORDER BY timestamp DESC LIMIT 1",
                (len(prefix), prefix)).fetchall()
    if not rows:
        return None
    r = rows[0]
    qa = split_qa(r["content"])
    if not qa:
        return None
    return {"fragment_id": r["fragment_id"], "timestamp": r["timestamp"], "origin": r["origin"],
            "question": qa[0], "reply": qa[1]}


def _estate_text_by_id() -> dict:
    from core import identity_projection as _ip
    try:
        est = json.loads(Path(_ip._ESTATE_F).read_text(encoding="utf-8"))
        return {n["id"]: (n.get("type"), n.get("text", "")) for n in est.get("nodes", [])}
    except Exception:
        return {}


def facts_for(returned: list[dict], projection: list[dict], text_by_id: dict) -> list[dict]:
    """The candidate facts: the ask's returned nodes first (their text rides on the row), then the projection's
    nodes (ids only on the row -> text from the estate file), de-duplicated by id, capped at MAX_FACTS."""
    out, seen = [], set()
    for n in returned or []:
        if n.get("id") in seen:
            continue
        seen.add(n.get("id"))
        out.append({"id": n.get("id"), "type": n.get("type"), "text": n.get("text", ""), "from": "ask"})
    for n in projection or []:
        nid = n.get("id")
        if nid in seen:
            continue
        seen.add(nid)
        t = text_by_id.get(nid)
        if not t:
            continue
        out.append({"id": nid, "type": t[0], "text": t[1], "from": "projection"})
    return out[:MAX_FACTS]


def build_user_prompt(question: str, reply: str, facts: list[dict]) -> str:
    lines = [f"QUESTION: {question[:400]}", "", f"REPLY: {reply[:1500]}", "", "FACTS FROM THE ENTITY'S OWN RECORD:"]
    for i, f in enumerate(facts, 1):
        lines.append(f"{i}. ({f.get('type')}) {str(f.get('text', ''))[:220]}")
    if not facts:
        lines.append("(none)")
    lines.append("")
    lines.append("Does the REPLY cite one of these FACTS in substance? JSON only.")
    return "\n".join(lines)


async def _judge_one(user: str, dry_run: bool) -> dict:
    if dry_run:
        return {"verdict": None, "how": "dry_run", "why": None, "which": None}
    from core import judge_panel
    d = await judge_panel.rule_detail(SYSTEM, user, JUDGE_KEY, context="estate_ask_judge", num_predict=220)
    return {"verdict": d.get("verdict"), "how": d.get("how"), "why": d.get("why"),
            "which": None, "err1": d.get("err1"), "err2": d.get("err2")}


def _append(out: Path, rec: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _done_keys(out: Path) -> set:
    return {r.get("key") for r in _jl(out)}


async def judge_shadow(shadow: Path, db: Path, out: Path, limit: int | None, since: float | None,
                       dry_run: bool) -> dict:
    rows = _jl(shadow)
    if since:
        rows = [r for r in rows if (r.get("ts") or 0) >= since]
    done = _done_keys(out)
    text_by_id = _estate_text_by_id()
    n, judged, no_reply = 0, 0, 0
    for r in rows:
        key = f"shadow:{r.get('cycle_id') or r.get('ts')}"
        if key in done:
            continue
        if limit is not None and n >= limit:
            break
        n += 1
        rep = find_reply(db, r.get("question", ""), r.get("ts"))
        if not rep:
            no_reply += 1
            _append(out, {"key": key, "arm": "shadow", "ts": r.get("ts"), "cycle_id": r.get("cycle_id"),
                          "input_type": r.get("input_type"), "question": r.get("question"),
                          "reply": None, "facts": [], "verdict": None, "how": "no_reply",
                          "has_competence": r.get("has_competence"), "overlap": r.get("overlap"),
                          "n_returned": r.get("n_returned"), "dry_run": dry_run, "judged_at": time.time()})
            continue
        facts = facts_for(r.get("returned"), r.get("projection"), text_by_id)
        user = build_user_prompt(rep["question"], rep["reply"], facts)
        v = await _judge_one(user, dry_run)
        judged += 1
        _append(out, {"key": key, "arm": "shadow", "ts": r.get("ts"), "cycle_id": r.get("cycle_id"),
                      "input_type": r.get("input_type"), "question": rep["question"], "reply": rep["reply"][:1500],
                      "reply_fragment_id": rep["fragment_id"], "facts": facts, **v,
                      "has_competence": r.get("has_competence"), "overlap": r.get("overlap"),
                      "n_returned": r.get("n_returned"), "live": r.get("live"), "dry_run": dry_run,
                      "judged_at": time.time()})
        if not dry_run:
            await asyncio.sleep(2.0)
    return {"rows": len(rows), "attempted": n, "judged": judged, "no_reply": no_reply, "out": str(out)}


async def judge_replies(db: Path, out: Path, limit: int | None, since: float | None, dry_run: bool,
                        keyword_only: bool = False) -> dict:
    """The without-the-ask arm: self-question cycles straight from the reply store, the would-be ask and
    would-be projection computed here (read-only; project(commit=False) never advances the live rotation)."""
    from core import identity_estate_ask as iea
    from core import identity_projection as _ip
    done = _done_keys(out)
    with _ro(db) as c:
        q = ("SELECT fragment_id, content, timestamp FROM memory_fragments WHERE substr(content,1,3)='Q: ' "
             + ("AND timestamp >= ? " if since else "") + "ORDER BY timestamp DESC")
        rows = c.execute(q, ((since,) if since else ())).fetchall()
    n, judged = 0, 0
    for r in rows:
        if limit is not None and n >= limit:
            break
        qa = split_qa(r["content"])
        if not qa:
            continue
        question, reply = qa
        key = f"replies:{r['fragment_id']}"
        if key in done:
            continue
        # input_type is not on the fragment: use the internal keyword set when the question reads as Du's own
        # (渡 / first person) and the human set otherwise -- both sets are tried, the stricter first.
        sq = iea.is_self_question(question, "internal") if not keyword_only else (
            {"reason": "keyword", "hit": iea._kw_hit(question, iea.SELF_KEYWORDS_INTERNAL), "score": 1.0}
            if iea._kw_hit(question, iea.SELF_KEYWORDS_INTERNAL) else None)
        itype = "internal"
        if not sq:
            sq = iea.is_self_question(question, "human") if not keyword_only else (
                {"reason": "keyword", "hit": iea._kw_hit(question, iea.SELF_KEYWORDS_HUMAN), "score": 1.0}
                if iea._kw_hit(question, iea.SELF_KEYWORDS_HUMAN) else None)
            itype = "human"
        if not sq:
            continue
        n += 1
        res = iea.ask(question)
        proj = [{"id": x["id"], "type": x["type"]} for x in (_ip.project(question, commit=False) or {}).get("nodes", [])]
        text_by_id = _estate_text_by_id()
        facts = facts_for(res["nodes"], proj, text_by_id)
        user = build_user_prompt(question, reply, facts)
        v = await _judge_one(user, dry_run)
        judged += 1
        ret_ids = {x["id"] for x in res["nodes"]}
        proj_ids = {x["id"] for x in proj}
        _append(out, {"key": key, "arm": "replies", "ts": r["timestamp"], "cycle_id": None, "input_type": itype,
                      "question": question, "reply": reply[:1500], "reply_fragment_id": r["fragment_id"],
                      "facts": facts, **v, "self_q": sq, "ability": res["ability"],
                      "has_competence": any(x["type"] == "competence" for x in res["nodes"]),
                      "overlap": len(ret_ids & proj_ids), "n_returned": len(ret_ids), "live": False,
                      "dry_run": dry_run, "judged_at": time.time()})
        if not dry_run:
            await asyncio.sleep(2.0)
    return {"candidates": len(rows), "self_questions": n, "judged": judged, "out": str(out)}


def report(out: Path, shadow: Path) -> dict:
    rows = _jl(out)
    judged = [r for r in rows if r.get("verdict") is not None]

    def rate(xs):
        xs = [r for r in xs if r.get("verdict") is not None]
        return {"n": len(xs), "cite": sum(1 for r in xs if r["verdict"] is True),
                "rate": (round(sum(1 for r in xs if r["verdict"] is True) / len(xs), 3) if xs else None)}

    rep = {"judgement_rows": len(rows), "judged": len(judged),
           "unjudged_by_how": {},
           "overall": rate(rows),
           "by_arm": {a: rate([r for r in rows if r.get("arm") == a]) for a in ("shadow", "replies")},
           "by_input_type": {t: rate([r for r in rows if r.get("input_type") == t]) for t in ("human", "internal")},
           "by_has_competence": {str(b): rate([r for r in rows if bool(r.get("has_competence")) is b]) for b in (True, False)},
           "by_live": {str(b): rate([r for r in rows if bool(r.get("live")) is b]) for b in (True, False)}}
    for r in rows:
        if r.get("verdict") is None:
            h = r.get("how") or "none"
            rep["unjudged_by_how"][h] = rep["unjudged_by_how"].get(h, 0) + 1
    srows = _jl(shadow)
    if srows:
        n = len(srows)
        subset = sum(1 for r in srows if r.get("returned_subset_of_projection"))
        nonempty = [r for r in srows if (r.get("n_returned") or 0) > 0]
        mean_frac = (round(sum((r.get("overlap") or 0) / r["n_returned"] for r in nonempty) / len(nonempty), 3)
                     if nonempty else None)
        comp = sum(1 for r in srows if r.get("has_competence"))
        rep["shadow"] = {"rows": n, "by_type": {t: sum(1 for r in srows if r.get("input_type") == t) for t in ("human", "internal")},
                         "returned_subset_of_projection": subset, "redundant_share": round(subset / n, 3),
                         "mean_overlap_fraction": mean_frac, "has_competence": comp,
                         "competence_share": round(comp / n, 3), "empty_returns": n - len(nonempty)}
        rep["d0424_defeater"] = {
            "redundant_clause_tripped": (subset / n) > 0.70,
            "citation_clause_readable": len([r for r in judged if r.get("arm") == "shadow"]) >= 30,
            "note": "citation lift (with vs without the ask) is only measurable after a live flip; before it, "
                    "both arms are without-the-ask baselines"}
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("judge", "replies", "report"))
    ap.add_argument("--shadow", default=str(DEFAULT_SHADOW))
    ap.add_argument("--db", default=None, help="reply store (memory DB); default core.memory.store.DB_PATH, opened read-only")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--since", type=float, default=None, help="unix ts lower bound")
    ap.add_argument("--dry-run", action="store_true", help="build prompts, call no hub, rows get verdict None")
    ap.add_argument("--keyword-only", action="store_true", help="replies mode: skip the embedding gate (no model load)")
    ap.add_argument("--estate", default=None, help="identity_estate.json to read the pool from (default: this tree's data/)")
    a = ap.parse_args(argv)
    out, shadow = Path(a.out), Path(a.shadow)
    if a.estate:
        from core import identity_projection as _ip
        _ip._ESTATE_F = Path(a.estate)
        _ip._cache.update({"sig": None, "nodes": None, "embs": None})
    if a.mode == "judge":
        r = asyncio.run(judge_shadow(shadow, _db_path(a.db), out, a.limit, a.since, a.dry_run))
    elif a.mode == "replies":
        r = asyncio.run(judge_replies(_db_path(a.db), out, a.limit, a.since, a.dry_run, a.keyword_only))
    else:
        r = report(out, shadow)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

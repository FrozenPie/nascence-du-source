"""J-2796 (F-3432 / P-0099): trace the 'Q: ... A: ...' fragments that PASS the evidence judge.
READ-ONLY: evidence_log.jsonl is read, nascence.db opened mode=ro&immutable=1. Writes only the JSON/TSV under
docs/lab/J-2796_data/. Usage: python scripts/j2796_qa_evidence_trace.py [--since 2026-10-30] [--nascence C:/Nascence]
Classifies each passing Q&A row by who ASKED (Q: line): a 'human' cycle has a canonical '[Travis said to me]' twin whose text
equals the Q: line; otherwise 'internal' (Du's own idle prompt, the cycle had no human). The A: line is always Du's own reply
(core/orchestrator._persist_cycle: A: = voice.final[:350])."""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, datetime as dt
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent


def norm(s: str) -> str:
    return " ".join((s or "").split()).strip().lower()


def split_qa(content: str):
    m = re.match(r"\s*Q:\s*(.*?)\s*\n?\s*A:\s*(.*)", content or "", re.DOTALL)
    return (m.group(1), m.group(2)) if m else (None, None)


def load_panel(nd: Path, since: float):
    """judge_panel_log.jsonl rows for the evidence judge (context 'evidence:<question[:40]>'), keyed for the per-ask join."""
    out = []
    with open(nd / "data" / "judge_panel_log.jsonl", encoding="utf-8") as f:
        for l in f:
            if '"context": "evidence:' not in l:
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if r.get("ts", 0) >= since - 5:
                out.append(r)
    return out


def resolve_verdicts(ask: dict, panel: list):
    """Per-slot verdict for one ask. evidence_log keeps v1/v2/how but NOT the tiebreak vote; the verdict lives in
    judge_panel_log (same ts window, context evidence:<q[:40]>). Panel rows finish in completion order, so a slot is matched
    on (v1, v2, how); where several slots share that triple and the panel rows disagree the slot is 'ambiguous'. The ask's
    n_returned (strong+weak passes) is the cross-check. Returns list[bool|None|'ambiguous'] aligned with ask['judged']."""
    ctx = "evidence:" + ask["question"][:40]
    t0, t1 = ask["ts"] - 2, ask["ts"] + ask.get("secs", 0) + 8
    rows = [r for r in panel if r.get("context") == ctx and t0 <= r["ts"] <= t1]
    res = []
    for j in ask["judged"]:
        if j.get("how") == "unavailable":
            res.append(None); continue
        if j.get("how") == "agreed":
            res.append(bool(j["v1"]) and bool(j["v2"])); continue
        cands = [r for r in rows if r.get("v1") == j["v1"] and r.get("v2") == j["v2"] and r.get("how") == j["how"]]
        vs = {r.get("verdict") for r in cands}
        n_same = sum(1 for x in ask["judged"] if (x["v1"], x["v2"], x["how"]) == (j["v1"], j["v2"], j["how"]))
        if len(vs) == 1 and len(cands) == n_same:
            res.append(vs.pop())
        elif len(vs) == 1:
            res.append(vs.pop())
        else:
            res.append("ambiguous" if vs else None)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-30")
    ap.add_argument("--nascence", default="C:/Nascence")
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-2796_data"))
    a = ap.parse_args()
    nd = Path(a.nascence)
    since = dt.datetime.fromisoformat(a.since).replace(tzinfo=dt.timezone.utc).timestamp()
    rows = [json.loads(l) for l in (nd / "data" / "evidence_log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("ts", 0) >= since]
    conn = sqlite3.connect(f"file:{nd.as_posix()}/data/memory/nascence.db?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    ids = {j["fragment_id"] for r in rows for j in r["judged"]}
    frag = {}
    ids = list(ids)
    for i in range(0, len(ids), 500):
        ch = ids[i:i + 500]
        for f in conn.execute("SELECT fragment_id,content,origin,timestamp FROM memory_fragments WHERE fragment_id IN (%s)" % ",".join("?" * len(ch)), ch):
            frag[f["fragment_id"]] = dict(f)
    twins = {}
    for f in conn.execute("SELECT content,timestamp FROM memory_fragments WHERE content LIKE '[Travis said to me] %'"):
        twins.setdefault(norm(f["content"][len("[Travis said to me] "):])[:200], []).append(f["timestamp"])
    conn.close()
    panel = load_panel(nd, since)
    out = []
    tally = {"asks": len(rows), "slots": 0, "qa_pass": 0, "qa_fail": 0, "qa_unavail": 0, "nonqa_pass": 0}
    seen_pass_ids = {}
    for r in rows:
        vds = resolve_verdicts(r, panel)
        for j, vd in zip(r["judged"], vds):
            f = frag.get(j["fragment_id"])
            if not f:
                continue
            tally["slots"] += 1
            un_ = j.get("how") == "unavailable"
            q, ans = split_qa(f["content"]) if (f["content"] or "").lstrip().startswith("Q:") else (None, None)
            ok = vd is True
            if vd == "ambiguous":
                tally["ambiguous_verdict_slots"] = tally.get("ambiguous_verdict_slots", 0) + 1
            un = j.get("how") == "unavailable"
            if q is None:
                tally["nonqa_pass"] += ok
                tally["nonqa_fail"] = tally.get("nonqa_fail", 0) + (1 if (not ok and not un_) else 0)
                continue
            if un:
                tally["qa_unavail"] += 1
                continue
            if not ok:
                tally["qa_fail"] += 1
                continue
            tally["qa_pass"] += 1
            key = norm(q)[:200]
            human = key in twins
            seen_pass_ids.setdefault(j["fragment_id"], 0)
            seen_pass_ids[j["fragment_id"]] += 1
            out.append({"ask_ts": r["ts"], "source": r.get("source"), "carried": r["question"], "fragment_id": j["fragment_id"],
                        "frag_ts": f["timestamp"], "sim": j["sim"], "how": j["how"], "asker": "human" if human else "internal",
                        "q": q[:300], "a": (ans or "")[:350]})
    nh = sum(1 for o in out if o["asker"] == "human")
    tally.update(qa_pass_human_asked=nh, qa_pass_internal_asked=len(out) - nh, distinct_qa_pass_fragments=len(seen_pass_ids),
                 max_repeats_one_fragment=max(seen_pass_ids.values(), default=0))
    od = Path(a.out); od.mkdir(parents=True, exist_ok=True)
    (od / "qa_pass_rows.json").write_text(json.dumps({"tally": tally, "rows": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(tally, indent=1))
    import random
    random.Random(2796).shuffle(out)
    for o in out[:a.sample]:
        print(f"\n[{o['asker']}] {o['how']} sim={o['sim']} carried={o['carried'][:110]!r}\n   Q: {o['q'][:160]!r}\n   A: {o['a'][:160]!r}")


if __name__ == "__main__":
    main()

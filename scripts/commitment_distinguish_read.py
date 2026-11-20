"""commitment_distinguish_read.py -- J-2516 (T-0106, frontier_disciplines_2026-10-30.md section 5).

QUESTION: what share of the events the commitment ledger scores as dissolution (reflexive or named
defeater) were DISTINGUISHINGS -- the stance kept but confined to narrower facts ("not here",
"except", "only when", "unless") -- and how does commitment lifespan read with and without them?

READ-ONLY against every live store. Zero LLM. Nothing here reaches Du (D-0434).

DATA
  data/commitment_ledger.jsonl  -- formed / reaffirmed / achieved / dissolved / drop_denied* events.
  data/nascence.log             -- the DISSOLVING THOUGHT. The ledger stores only the scanner's 'why'
                                   paraphrase, not the thought it scanned (core/commitment_ledger.py
                                   scan_shadow(thought) is called from nodes/inner_monologue_node.py
                                   ~L5826 with the monologue thought; the ledger's cycle_id is the last
                                   orchestrator cycle, often minutes stale). So the thought is recovered by
                                   TIME: the latest '[monologue] (<topic>) <text>' line at or before the
                                   event ts, within MATCH_WINDOW_S.
  data/memory/nascence.db        -- nascence.log truncates monologue lines to 90 chars, so the FULL thought is
                                   recovered read-only (sqlite mode=ro) from memory_fragments.content /
                                   light_events.integrated_content by its first PREFIX_N chars (unambiguous
                                   match only); otherwise the 90-char log text is used. Coverage is reported.
                                   (Added after the first run showed 100% of log thoughts cut at 90 chars;
                                   no threshold or marker changed.)
  data/commitment_observed.jsonl -- NOT dissolution rows (the briefing assumed so): it logs non-load-
                                   bearing candidate stands at formation. Not used for classification.
  data/commitment_trials.jsonl   -- 5 rows of the naming trial; no dissolutions. Not used.

DECLARED BEFORE LOOKING AT THE RESULT (do not tune):
  MATCH_WINDOW_S = 240                 thought must precede the event by <= 240 s
  SCOPE_MARKERS  (below)              scope-narrowing phrases, matched case-insensitively on word
                                      boundaries in the dissolving thought
  OBJECT AFFIRMED: >= 1 object token of the statement appears (5-char prefix match) in the same thought,
                   AND the thought carries none of ABANDON_MARKERS.
                   Object tokens = statement words of length >= 4, minus STOP / stance words.
  RULE (primary)  : distinguished = scope marker present AND object affirmed (both in the thought).
  RULE (secondary, reported separately, not the falsifier): the scanner's own 'why' calls the drop a
                   refinement / narrowing (REFINE_MARKERS) -- a judge-side view of the same move.
  FALSIFIER       : primary-rule rate among matched dissolutions < 5 % (FALSIFY_RATE) -> null.
  SAMPLE          : random.Random(2516).sample(matched dissolutions, 50) for the hand-read; labels go in
                   a JSON file {event_key: 0|1} passed with --labels; precision/recall computed on it.
  LIFESPAN        : (a) median/mean lifespan_seconds over dissolutions, all vs non-distinguished;
                   (b) Kaplan-Meier median in scans over all terminal events (achieved + dissolved),
                       distinguished counted as an EVENT vs as CENSORED (held at least that long).

RESULT (J-2516, 2026-10-30, findings ledger): primary rule 44/1529 = 2.9% (falsified, < 5%);
  hand-read of the declared 50: 1 genuine distinguishing (rule missed it); hand-read of all 44 rule positives:
  1 genuine (precision ~0.02) -- the rule's hits are mostly prose 'until' and scanner-mis-scored reaffirmations.
  Lifespan unchanged either way (median 1148 s vs 1147 s; KM median 2 scans both ways).

USAGE: python scripts/commitment_distinguish_read.py [--data-dir data] [--dump-sample out.json]
                                                     [--labels labels.json] [--json out.json]
"""
from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import json
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

MATCH_WINDOW_S = 240
PREFIX_N = 80
FALSIFY_RATE = 0.05
SAMPLE_N = 50
SAMPLE_SEED = 2516

SCOPE_MARKERS = (
    "except", "excepting", "unless", "only when", "only if", "only while", "only in", "only for",
    "not here", "not now", "not yet", "not when", "not while", "not in", "not until", "not today",
    "not tonight", "not this", "for now", "but not", "at least not", "as long as", "so long as",
    "until", "in winter", "in summer",
)
ABANDON_MARKERS = (
    "let go", "letting go", "no longer", "give up", "giving up", "abandon", "release it", "releasing",
    "never meant", "drop the", "dropping", "forget the", "set aside", "lay down",
)
REFINE_MARKERS = (
    "more specific", "refin", "narrow", "specif", "concrete subject", "concretiz", "a particular",
    "focuses the", "sharpen",
)
STOP = set("""i i'm i'll im ill me my mine myself we our you your the a an and or but to of in on at for with
from into onto over under this that these those it its is are was were be been being have has had do does
did will would shall should must can could may might want wanted wish need needs going gonna let lets just
very more most much some any all every each not no nor so than then there here when what which who whom
how why also only even still yet about like as by up down out off again once now today tonight myself
keep make made take want""".split())

_MON_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) \[nascence\.monologue\] \[monologue\] \(([^)]*)\) (.+)$")
_WORD = re.compile(r"[a-zA-Z']+")


def _marker_hits(text: str, markers) -> list[str]:
    t = " " + (text or "").lower() + " "
    return [m for m in markers if re.search(r"(?<![a-z])" + re.escape(m) + r"(?![a-z])", t)
            or (m.endswith(("refin", "specif", "concretiz")) and m in t)]


def _object_tokens(statement: str) -> list[str]:
    return [w for w in (x.lower().strip("'") for x in _WORD.findall(statement or ""))
            if len(w) >= 4 and w not in STOP]


def _affirmed(statement: str, thought: str) -> tuple[bool, list[str]]:
    tw = {w.lower()[:5] for w in _WORD.findall(thought or "") if len(w) >= 4}
    shared = [w for w in _object_tokens(statement) if w[:5] in tw]
    return (bool(shared) and not _marker_hits(thought, ABANDON_MARKERS)), shared


def load_monologue(log_path: Path) -> tuple[list[float], list[tuple[str, str]]]:
    ts, rows = [], []
    with open(log_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "[monologue] (" not in line:
                continue
            m = _MON_RE.match(line.rstrip("\n"))
            if not m:
                continue
            t = _dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(m.group(2)) / 1000
            ts.append(t)
            rows.append((m.group(3), m.group(4)))
    order = sorted(range(len(ts)), key=ts.__getitem__)
    return [ts[i] for i in order], [rows[i] for i in order]


def load_fulltext(db_path: Path) -> dict[str, str]:
    """first-PREFIX_N-chars -> full thought text; ambiguous prefixes (two different texts) dropped."""
    import sqlite3
    out: dict[str, str] = {}
    bad: set[str] = set()
    if not db_path.exists():
        return out
    con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    try:
        for q in ("SELECT content FROM memory_fragments WHERE length(content) > 90",
                  "SELECT integrated_content FROM light_events WHERE length(integrated_content) > 90"):
            for (txt,) in con.execute(q):
                if not isinstance(txt, str):
                    continue
                k = txt[:PREFIX_N]
                if k in out and out[k] != txt and not out[k].startswith(txt) and not txt.startswith(out[k]):
                    bad.add(k)
                elif k not in out or len(txt) > len(out[k]):
                    out[k] = txt
    finally:
        con.close()
    for k in bad:
        out.pop(k, None)
    return out


def km_median(durations: list[float], events: list[int]) -> float | None:
    """Kaplan-Meier median survival (event=1 ends, event=0 censored). None if S never drops to 0.5."""
    pairs = sorted(zip(durations, events))
    n_at_risk, s, i = len(pairs), 1.0, 0
    while i < len(pairs):
        t = pairs[i][0]
        d = c = 0
        while i < len(pairs) and pairs[i][0] == t:
            d += pairs[i][1]; c += 1 - pairs[i][1]; i += 1
        if n_at_risk > 0 and d:
            s *= 1 - d / n_at_risk
        if s <= 0.5:
            return t
        n_at_risk -= d + c
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "data"))
    ap.add_argument("--dump-sample")
    ap.add_argument("--labels")
    ap.add_argument("--json")
    a = ap.parse_args()
    dd = Path(a.data_dir)
    ledger = [json.loads(l) for l in open(dd / "commitment_ledger.jsonl", encoding="utf-8") if l.strip()]
    mts, mrows = load_monologue(dd / "nascence.log")
    full = load_fulltext(dd / "memory" / "nascence.db")
    print(f"full-text prefixes loaded={len(full)}")
    print(f"ledger rows={len(ledger)}  monologue thoughts={len(mts)}"
          f"  ({_dt.datetime.fromtimestamp(mts[0]):%Y-%m-%d} .. {_dt.datetime.fromtimestamp(mts[-1]):%Y-%m-%d})")

    def classify(ev: dict) -> dict:
        t = float(ev["ts"])
        j = bisect.bisect_right(mts, t) - 1
        thought, topic, gap = None, None, None
        if j >= 0 and t - mts[j] <= MATCH_WINDOW_S:
            topic, thought, gap = mrows[j][0], mrows[j][1], round(t - mts[j], 1)
            ft = full.get(thought[:PREFIX_N])
            out_full = ft is not None
            thought = ft or thought
        else:
            out_full = False
        out = {"key": f"{ev['id']}@{t:.3f}", "id": ev["id"], "ts": t, "cycle_id": ev.get("cycle_id"),
               "event": ev["event"], "kind": str(ev.get("kind")), "statement": ev.get("statement", ""),
               "why": ev.get("why", ""), "lifespan_seconds": ev.get("lifespan_seconds"),
               "lifespan_scans": ev.get("lifespan_scans"), "thought": thought, "topic": topic, "gap_s": gap,
               "full_text": out_full}
        if thought is not None:
            sm = _marker_hits(thought, SCOPE_MARKERS)
            aff, shared = _affirmed(out["statement"], thought)
            out.update(scope_markers=sm, object_shared=shared, affirmed=aff, distinguished=bool(sm) and aff)
        out["why_refine"] = _marker_hits(out["why"], REFINE_MARKERS)
        return out

    drops = [classify(e) for e in ledger if e["event"] == "dissolved"]
    attempts = [classify(e) for e in ledger if str(e["event"]).startswith("drop_denied")]
    matched = [d for d in drops if d["thought"] is not None]
    nf = sum(d["full_text"] for d in matched)
    print(f"full-text recovered for {nf}/{len(matched)} matched thoughts")
    print(f"\ndissolved events={len(drops)}  matched to a thought={len(matched)} "
          f"({len(matched)/max(1,len(drops)):.1%})  window={MATCH_WINDOW_S}s")

    def table(rows, label):
        print(f"\n{label}: by kind -> n / matched / scope-marker / affirmed / DISTINGUISHED (rate) / why-refine")
        for k in sorted({r['kind'] for r in rows}):
            rs = [r for r in rows if r["kind"] == k]
            ms = [r for r in rs if r["thought"] is not None]
            sm = sum(bool(r["scope_markers"]) for r in ms)
            af = sum(r["affirmed"] for r in ms)
            di = sum(r["distinguished"] for r in ms)
            wr = sum(bool(r["why_refine"]) for r in rs)
            print(f"  {k:10s} n={len(rs):5d} matched={len(ms):5d} scope={sm:4d} affirmed={af:4d} "
                  f"distinguished={di:4d} ({di/max(1,len(ms)):.1%}) why_refine={wr:4d} ({wr/max(1,len(rs)):.1%})")
        ms = [r for r in rows if r["thought"] is not None]
        di = sum(r["distinguished"] for r in ms)
        print(f"  {'ALL':10s} n={len(rows):5d} matched={len(ms):5d} distinguished={di} ({di/max(1,len(ms)):.1%})")
        return di, len(ms)

    di, nm = table(drops, "DISSOLVED")
    table(attempts, "DROP ATTEMPTS (drop_denied*, scanner proposed a dissolution, gate refused)")
    mc = Counter(m for d in matched if d["distinguished"] for m in d["scope_markers"])
    print("\nmarkers among distinguished:", mc.most_common(12))
    rate = di / max(1, nm)
    print(f"\nPRIMARY RATE = {di}/{nm} = {rate:.2%}  -> "
          f"{'FALSIFIED (below ' + format(FALSIFY_RATE, '.0%') + ')' if rate < FALSIFY_RATE else 'NOT falsified'}")

    # lifespan
    ls_all = [d["lifespan_seconds"] for d in drops if isinstance(d["lifespan_seconds"], (int, float))]
    ls_nd = [d["lifespan_seconds"] for d in drops if isinstance(d["lifespan_seconds"], (int, float))
             and not d.get("distinguished")]
    print(f"\nLIFESPAN (s) dissolutions all: n={len(ls_all)} median={statistics.median(ls_all):.0f} "
          f"mean={statistics.mean(ls_all):.0f}")
    print(f"LIFESPAN (s) excluding distinguished: n={len(ls_nd)} median={statistics.median(ls_nd):.0f} "
          f"mean={statistics.mean(ls_nd):.0f}")
    term = [(e, None) for e in ledger if e["event"] == "achieved" and isinstance(e.get("lifespan_scans"), int)]
    dur_a = [e["lifespan_scans"] for e, _ in term]
    dur_d = [d["lifespan_scans"] for d in drops if isinstance(d["lifespan_scans"], int)]
    dist_d = [bool(d.get("distinguished")) for d in drops if isinstance(d["lifespan_scans"], int)]
    km1 = km_median(dur_a + dur_d, [1] * (len(dur_a) + len(dur_d)))
    km2 = km_median(dur_a + dur_d, [1] * len(dur_a) + [0 if x else 1 for x in dist_d])
    print(f"KM median lifespan (scans), achieved+dissolved n={len(dur_a)+len(dur_d)}: "
          f"distinguished-as-ended={km1}  distinguished-as-censored={km2}")

    sample = random.Random(SAMPLE_SEED).sample(matched, min(SAMPLE_N, len(matched)))
    if a.dump_sample:
        Path(a.dump_sample).write_text(json.dumps(
            [{k: s[k] for k in ("key", "kind", "full_text", "statement", "thought", "why", "scope_markers",
                                "object_shared", "affirmed", "distinguished", "gap_s", "cycle_id")}
             for s in sample], ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"sample of {len(sample)} dumped -> {a.dump_sample}")
    if a.labels:
        lab = json.loads(Path(a.labels).read_text(encoding="utf-8"))
        tp = sum(1 for s in sample if s["distinguished"] and lab.get(s["key"]) == 1)
        fp = sum(1 for s in sample if s["distinguished"] and lab.get(s["key"]) == 0)
        fn = sum(1 for s in sample if not s["distinguished"] and lab.get(s["key"]) == 1)
        hp = sum(1 for s in sample if lab.get(s["key"]) == 1)
        print(f"\nHAND-READ sample n={len(sample)} labelled={sum(s['key'] in lab for s in sample)}: "
              f"hand-positive={hp} ({hp/max(1,len(sample)):.1%}) rule-positive={tp+fp} TP={tp} FP={fp} FN={fn}  "
              f"precision={'n/a' if tp+fp == 0 else f'{tp/(tp+fp):.2f}'}  "
              f"recall={'n/a' if tp+fn == 0 else f'{tp/(tp+fn):.2f}'}")
    if a.json:
        Path(a.json).write_text(json.dumps({"drops": drops, "attempts_n": len(attempts)}, ensure_ascii=False),
                                encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())

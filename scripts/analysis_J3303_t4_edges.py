"""J-3303 read-only analysis: do the T4 tension->crossing edges carry signal? (F-3883)

Reads (never writes) the live Nascence stores:
  data/memory/nascence.db            memory_edges (edge_type t4_crossing_evidence), light_events
                                     (sqlite mode=ro&immutable=1; Du is down so the WAL is empty)
  data/nascence.log                  T4 CHAIN / T4 considered / T4 question RESTED / adopted lines
  data/logs/provisional_identity.jsonl   probation open / solidify / revert rows (full theme text)
  data/logs/t4_emissary_judge.jsonl      one row per judged candidate (emissary_warranted)
Writes only under docs/lab/J-3303_data/ in this worktree (or --out).

Usage:  python scripts/analysis_J3303_t4_edges.py [--live C:/Nascence] [--out DIR]

Method notes (why the numbers are built the way they are):
  * The edge writer is INSERT OR IGNORE on UNIQUE(src,dst,type): a crossing cited again by the SAME
    tension is dropped, and its has_movement provenance is the FIRST hearing's only. So recurrence and
    per-hearing movement cannot be read off the edges; they are recovered from the log hearings.
  * Edge rows carry only sha1(tension_text)[:12].  Text is recovered (a) by hashing the full labels the
    log prints on 'T4 considered' lines and the probation theme text, and (b) for what is left, by
    aligning each edge batch (same hash, rows <5 s apart) to the next T4 log line (<= 900 s later).
    The alignment is validated against the hashes resolved by (a).
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, sqlite3, statistics, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

BATCH_GAP_S = 5          # rows of one hearing are written ~15 ms apart
ALIGN_MAX_S = 900        # a hearing's log line follows its edge write within this
POOL_N = 300             # core/memory/store.get_light_events_with_embeddings default limit
EDGE = "t4_crossing_evidence"

TS = r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ "
RE_CHAIN = re.compile(TS + r".*T4 CHAIN — tension=(?P<q>['\"])(?P<lab>.*?)(?P=q) →")
RE_CONS = re.compile(TS + r".*T4 considered (?P<n>\d+) fragment\(s\) — no change: (?P<why>.*?) \(tension: (?P<q>['\"])(?P<lab>.*)(?P=q)\)\s*$")
RE_REST = re.compile(TS + r".*T4 question RESTED after \d+ no-movement hearings: (?P<q>['\"])(?P<lab>.*)(?P=q) \(returns")
RE_ADOPT = re.compile(TS + r".*T4 candidate adopted PROVISIONALLY \(theme=(?P<lab>.*?)\) via")


def sha(t: str) -> str:
    return hashlib.sha1(t.encode("utf-8", "replace")).hexdigest()[:12]


def epoch(s: str) -> float:
    return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def family(label: str) -> str:
    """Number-stripped, prefix-aligned family id (labels differ only by the felt/real numbers)."""
    s = (label or "").lower().strip()
    s = re.sub(r"\s*\(felt.*$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s[:36].strip() or "(no label)"


def day(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def parse_log(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "T4 " not in line:
            continue
        m = RE_CHAIN.match(line)
        if m:
            out.append(dict(ts=epoch(m.group(1)), kind="chain", movement=True, delta=True,
                            lab=m.group("lab"), full=False, n=None, why="authored"))
            continue
        m = RE_CONS.match(line)
        if m:
            why = m.group("why")
            mv = None
            if "no genuine movement" in why or "still circling" in why:
                mv = False
            elif "no specific delta" in why or "already holds" in why:
                mv = True
            elif "not yet crossed" in why or "no lived crossing" in why:
                mv = None
            out.append(dict(ts=epoch(m.group(1)), kind="considered", movement=mv, delta=False,
                            lab=m.group("lab"), full=True, n=int(m.group("n")), why=why))
            continue
        m = RE_REST.match(line)
        if m:
            out.append(dict(ts=epoch(m.group(1)), kind="rested", movement=None, delta=False,
                            lab=m.group("lab"), full=False, n=None, why="rested"))
            continue
        m = RE_ADOPT.match(line)
        if m:
            out.append(dict(ts=epoch(m.group(1)), kind="adopted", movement=None, delta=True,
                            lab=m.group("lab"), full=False, n=None, why="adopted"))
    return out


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default="C:/Nascence")
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3303_data"))
    a = ap.parse_args()
    live = Path(a.live)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(f"file:{(live / 'data/memory/nascence.db').as_posix()}?mode=ro&immutable=1", uri=True)
    edges = db.execute("SELECT edge_id,src_id,dst_id,weight,provenance,created FROM memory_edges "
                       "WHERE edge_type=? ORDER BY created, edge_id", (EDGE,)).fetchall()
    raw_prefix = {}
    for eid, raw in db.execute("SELECT event_id, substr(raw_input,1,40) FROM light_events WHERE event_id IN "
                               "(SELECT dst_id FROM memory_edges WHERE edge_type=?)", (EDGE,)):
        m = re.match(r"\((\w[\w ]*?)[:)]", raw or "")
        raw_prefix[eid] = m.group(1) if m else ("(play)" if (raw or "").startswith("(play") else "other")
    ev = {r[0]: r for r in db.execute("SELECT event_id,timestamp,cycle_id,source,length(raw_input),"
                                      "length(integrated_content),emotion_primary FROM light_events")}
    ev_ts_sorted = sorted(r[1] for r in ev.values())
    n_events = len(ev)
    corpus = db.execute("SELECT count(*), count(DISTINCT integrated_content) FROM light_events").fetchone()
    cited_ids = sorted({e[2] for e in edges})
    content_of = {}
    for i in range(0, len(cited_ids), 500):
        part = cited_ids[i:i + 500]
        for eid, ic in db.execute("SELECT event_id, integrated_content FROM light_events WHERE event_id IN (%s)"
                                  % ",".join("?" * len(part)), part):
            content_of[eid] = hashlib.sha1((ic or "").strip().encode("utf-8", "replace")).hexdigest()[:12]

    import bisect

    def events_between(t0: float, t1: float) -> int:
        return bisect.bisect_right(ev_ts_sorted, t1) - bisect.bisect_right(ev_ts_sorted, t0)

    log = parse_log(live / "data/nascence.log")
    prob = [json.loads(l) for l in (live / "data/logs/provisional_identity.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    judge = [json.loads(l) for l in (live / "data/logs/t4_emissary_judge.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

    # ---- 1. resolve hash -> text --------------------------------------------------------------
    hashes = sorted({e[1] for e in edges})
    pool: dict[str, str] = {}
    for h in log:
        if h["full"]:
            pool[sha(h["lab"])] = h["lab"]
    for p in prob:
        if p.get("theme"):
            pool.setdefault(sha(p["theme"]), p["theme"])
    exact = {h: pool[h] for h in hashes if h in pool}

    # batches (hearings that wrote >=1 new row)
    by_hash: dict[str, list] = collections.defaultdict(list)
    for e in edges:
        by_hash[e[1]].append(e)
    batches: dict[str, list[list]] = {}
    for h, rows in by_hash.items():
        bs, cur = [], []
        for r in rows:
            if cur and r[5] - cur[-1][5] > BATCH_GAP_S:
                bs.append(cur)
                cur = []
            cur.append(r)
        if cur:
            bs.append(cur)
        batches[h] = bs

    log_sorted = sorted(log, key=lambda x: x["ts"])
    log_ts = [x["ts"] for x in log_sorted]
    hearing_kinds = [x for x in log_sorted if x["kind"] in ("chain", "considered")]
    hk_ts = [x["ts"] for x in hearing_kinds]

    def next_hearing(t: float):
        i = bisect.bisect_left(hk_ts, t - 2)
        if i < len(hearing_kinds) and hearing_kinds[i]["ts"] - t <= ALIGN_MAX_S:
            return hearing_kinds[i]
        return None

    def prefix_ok(full: str, cut: str) -> bool:
        return bool(cut) and full.lower().startswith(cut.lower()[:36])

    # validate the alignment on hashes resolved exactly
    chk = collections.Counter()
    aligned_of: dict[tuple, dict] = {}
    for h, bs in batches.items():
        for b in bs:
            ln = next_hearing(b[0][5])
            aligned_of[(h, b[0][0])] = ln
            if h in exact:
                if ln is None:
                    chk["no_line"] += 1
                elif prefix_ok(exact[h], ln["lab"]):
                    chk["match"] += 1
                else:
                    chk["mismatch"] += 1
    # resolve remaining hashes by majority aligned label (prefix-consistent votes)
    resolved = dict(exact)
    method = {h: "exact_hash" for h in exact}
    for h in hashes:
        if h in resolved:
            continue
        votes = collections.Counter()
        for b in batches[h]:
            ln = aligned_of.get((h, b[0][0]))
            if ln:
                votes[ln["lab"]] += 1
        if votes:
            lab, v = votes.most_common(1)[0]
            resolved[h] = lab
            method[h] = f"aligned_log_label({v}/{len(batches[h])} batches agree)"
    edges_exact = sum(len(by_hash[h]) for h in exact)

    # ---- 2. per-tension (hash) and per-family measures --------------------------------------
    fam_of = {h: family(resolved.get(h, "")) for h in hashes}
    t_edges_first = min(e[5] for e in edges)
    # log hearings per family since the writer began (edges start)
    log_h = collections.defaultdict(list)
    for x in hearing_kinds:
        if x["ts"] >= t_edges_first - 3600:
            log_h[family(x["lab"])].append(x)

    rows_out = []
    for h in hashes:
        es = by_hash[h]
        dst = [e[2] for e in es]
        bs = batches[h]
        mv_first = sum(1 for e in es if e[4].endswith("True"))
        fam = fam_of[h]
        lh = log_h.get(fam, [])
        # distinct log hearings aligned to this hash's batches
        hear_dst = len(bs)
        lo, hi = es[0][5], es[-1][5]
        rows_out.append(dict(
            hash=h, text=resolved.get(h), how=method.get(h), family=fam,
            edges=len(es), distinct_crossings=len(set(dst)), batches=len(bs),
            mean_rows_per_batch=round(len(es) / len(bs), 2),
            first_citation_movement_share=pct(mv_first, len(es)),
            batch_movement_share=pct(sum(1 for b in bs if b[0][4].endswith("True")), len(bs)),
            first=time.strftime("%F %H:%M", time.localtime(lo)), last=time.strftime("%F %H:%M", time.localtime(hi)),
            days_spanned=round((hi - lo) / 86400, 2), edge_days=len({day(e[5]) for e in es}),
            moment_days=len({day(ev[d][1]) for d in set(dst) if d in ev}),
            mean_weight=round(statistics.mean(e[3] for e in es), 3),
        ))
    rows_out.sort(key=lambda r: -r["edges"])

    # family roll-up with log hearings (the only source of true recurrence / per-hearing movement)
    fam_rows = []
    fam_hashes = collections.defaultdict(list)
    for h in hashes:
        fam_hashes[fam_of[h]].append(h)
    for fam, hs in sorted(fam_hashes.items(), key=lambda kv: -sum(len(by_hash[h]) for h in kv[1])):
        es = [e for h in hs for e in by_hash[h]]
        nb = sum(len(batches[h]) for h in hs)
        lh = log_h.get(fam, [])
        mv = [x["movement"] for x in lh if x["movement"] is not None]
        fam_rows.append(dict(
            family=fam, hashes=len(hs), edges=len(es), distinct_crossings=len({e[2] for e in es}),
            batches_with_new_rows=nb, log_hearings=len(lh),
            log_hearings_no_crossing=sum(1 for x in lh if x["movement"] is None and x["kind"] == "considered"),
            hearings_adding_no_new_row_lower_bound=max(0, len(lh) - nb),
            log_movement_true=sum(1 for m in mv if m), log_movement_false=sum(1 for m in mv if not m),
            log_movement_share=pct(sum(1 for m in mv if m), len(mv)),
            log_authored=sum(1 for x in lh if x["kind"] == "chain"),
            edge_first_citation_movement_share=pct(sum(1 for e in es if e[4].endswith("True")), len(es)),
            days_spanned=round((max(e[5] for e in es) - min(e[5] for e in es)) / 86400, 2),
            edge_days=len({day(e[5]) for e in es}),
        ))

    # ---- 3. probation / admission linkage ----------------------------------------------------
    t0 = t_edges_first
    opens = [p for p in prob if p["event"] == "open" and float(p["ts"]) >= t0]
    sol = [p for p in prob if p["event"] == "solidify" and float(p["ts"]) >= t0]
    rev = [p for p in prob if p["event"] == "revert" and float(p["ts"]) >= t0]
    fam_prob = collections.defaultdict(lambda: collections.Counter())
    for p in opens:
        fam_prob[family(p["theme"])]["open"] += 1
    for p in sol:
        fam_prob[family(p["theme"])]["solidify"] += 1
    for p in rev:
        fam_prob[family(p["theme"])]["revert"] += 1
    # judge rows >=0.6 aligned to the preceding CHAIN line (authoring) within ALIGN_MAX_S
    chains = [x for x in log_sorted if x["kind"] == "chain"]
    ch_ts = [x["ts"] for x in chains]
    judged = []
    for j in judge:
        jt = float(j["ts"])
        if jt < t0:
            continue
        k = bisect.bisect_left(ch_ts, jt)
        cands = [c for c in (k - 1, k) if 0 <= c < len(chains)]
        best = min(cands, key=lambda c: abs(ch_ts[c] - jt)) if cands else None
        lab = chains[best]["lab"] if best is not None and abs(ch_ts[best] - jt) <= ALIGN_MAX_S else None
        off = (jt - ch_ts[best]) if best is not None else None
        judged.append(dict(ts=jt, warranted=j.get("emissary_warranted"), lab=lab, off=off))
    fam_judge = collections.defaultdict(lambda: collections.Counter())
    for j in judged:
        f = family(j["lab"] or "")
        fam_judge[f]["judged"] += 1
        if (j["warranted"] or 0) >= 0.6:
            fam_judge[f]["admit_ge_0.6"] += 1
    for fr in fam_rows:
        fr["probations_opened"] = fam_prob[fr["family"]]["open"]
        fr["solidified"] = fam_prob[fr["family"]]["solidify"]
        fr["reverted"] = fam_prob[fr["family"]]["revert"]
        fr["judged"] = fam_judge[fr["family"]]["judged"]
        fr["admitted_ge_0.6"] = fam_judge[fr["family"]]["admit_ge_0.6"]
    fams_with_edges = {fr["family"] for fr in fam_rows}

    def cohort(sel):
        rs = [fr for fr in fam_rows if sel(fr)]
        if not rs:
            return dict(n_families=0)
        def m(k):
            vals = [fr[k] for fr in rs if fr[k] is not None]
            return round(statistics.mean(vals), 2) if vals else None
        return dict(n_families=len(rs), edges=sum(fr["edges"] for fr in rs),
                    mean_distinct_crossings=m("distinct_crossings"), mean_log_hearings=m("log_hearings"),
                    mean_log_movement_share=m("log_movement_share"),
                    mean_edge_first_cit_move_share=m("edge_first_citation_movement_share"),
                    mean_days_spanned=m("days_spanned"), mean_edge_days=m("edge_days"),
                    names=[fr["family"] for fr in rs][:8])

    cohorts = dict(
        solidified=cohort(lambda fr: fr["solidified"] > 0),
        probation_opened=cohort(lambda fr: fr["probations_opened"] > 0),
        admitted_ge_0_6=cohort(lambda fr: fr["admitted_ge_0.6"] > 0),
        never_probation_never_admitted=cohort(lambda fr: fr["probations_opened"] == 0 and fr["admitted_ge_0.6"] == 0),
    )
    unmatched_prob = {f: dict(c) for f, c in fam_prob.items() if f not in fams_with_edges}
    unmatched_judge = {f: dict(c) for f, c in fam_judge.items() if f not in fams_with_edges}

    # ---- 4. reach: age of the cited moment, pool rank, days -----------------------------------
    ages_h, ranks, resolve = [], [], collections.Counter()
    ev_days = collections.Counter()
    for e in edges:
        r = ev.get(e[2])
        if r is None:
            resolve["missing"] += 1
            continue
        resolve["present"] += 1
        ages_h.append((e[5] - r[1]) / 3600.0)
        ranks.append(events_between(r[1], e[5]))
        ev_days[day(r[1])] += 1
    ages_h.sort()
    ranks.sort()

    def q(xs, p):
        return round(xs[min(len(xs) - 1, int(p * len(xs)))], 2) if xs else None

    # age windows: the pool is the newest 300 events WITH an embedding; measure the time span of a
    # 300-event window across the edge period to show the horizon in hours
    spans = []
    ets = ev_ts_sorted
    step = max(1, len(ets) // 400)
    for i in range(POOL_N, len(ets), step):
        spans.append((ets[i] - ets[i - POOL_N]) / 3600.0)
    spans.sort()
    # the stored distinct light_event days vs edge-creation days
    dst_distinct = {e[2] for e in edges}
    dst_days = {day(ev[d][1]) for d in dst_distinct if d in ev}
    edge_days = {day(e[5]) for e in edges}
    # moments cited by more than one tension / hash, and cited at all
    dst_hashes = collections.defaultdict(set)
    for e in edges:
        dst_hashes[e[2]].add(e[1])
    shared = sum(1 for d, hs in dst_hashes.items() if len(hs) > 1)
    dst_fams = collections.defaultdict(set)
    for e in edges:
        dst_fams[e[2]].add(fam_of[e[1]])
    shared_fam = sum(1 for d, fs in dst_fams.items() if len(fs) > 1)
    src_cnt = collections.Counter(ev[d][3] for d in dst_distinct if d in ev)
    src_all = collections.Counter(r[3] for r in ev.values())
    # weights: ties inside a batch (same weight on different crossings)
    tie_batches = 0
    multi = 0
    for h, bs in batches.items():
        for b in bs:
            if len(b) > 1:
                multi += 1
                ws = [r[3] for r in b]
                if len(set(ws)) < len(ws):
                    tie_batches += 1
    # a missing event (future pruning risk): any code that deletes light_events?
    # (checked separately by grep; recorded in the findings text)

    # ---- 4b. duplication + recurrence at the level of CONTENT and of hearings --------------------
    rows_total = len(edges)
    distinct_content = len({content_of.get(e[2]) for e in edges})
    per_batch_dup = []
    for h, bs in batches.items():
        for b in bs:
            cs = [content_of.get(r[2]) for r in b]
            per_batch_dup.append((len(cs), len(set(cs))))
    batches_with_dup = sum(1 for n, d in per_batch_dup if d < n)
    mean_distinct_frac = round(statistics.mean(d / n for n, d in per_batch_dup), 3)
    # per hash: rows whose sentence was already cited by the same hash earlier (new event id, old sentence)
    repeat_sentence_rows = 0
    first_batch_rows, later_batch_rows, later_batches = [], [], 0
    for h, bs in batches.items():
        seen = set()
        for bi, b in enumerate(bs):
            for r in b:
                c = content_of.get(r[2])
                if c in seen:
                    repeat_sentence_rows += 1
                seen.add(c)
            (first_batch_rows if bi == 0 else later_batch_rows).append(len(b))
    # hearings that reached the edge write (log movement True/False) but wrote no new row
    aligned_ids = {id(v) for v in aligned_of.values() if v}
    reached = [x for x in hearing_kinds if x["ts"] >= t_edges_first - 3600 and x["movement"] is not None]
    reached_no_row = [x for x in reached if id(x) not in aligned_ids]
    reached_mv = collections.Counter(bool(x["movement"]) for x in reached)
    reached_no_row_mv = collections.Counter(bool(x["movement"]) for x in reached_no_row)
    all_h_since = [x for x in hearing_kinds if x["ts"] >= t_edges_first - 3600]
    no_crossing = [x for x in all_h_since if x["movement"] is None]
    # per-family hearings that wrote no row
    for fr in fam_rows:
        fr["hearings_reached_edge_write"] = sum(1 for x in reached if family(x["lab"]) == fr["family"])
        fr["hearings_zero_new_rows"] = sum(1 for x in reached_no_row if family(x["lab"]) == fr["family"])
        fr["crossings_per_hearing"] = round(fr["distinct_crossings"] / fr["log_hearings"], 2) if fr["log_hearings"] else None
        fr["share_hearings_zero_new_rows"] = pct(fr["hearings_zero_new_rows"], fr["hearings_reached_edge_write"])
    # cohorts again, now with per-hearing normalisation
    cohorts = dict(
        solidified=cohort(lambda fr: fr["solidified"] > 0),
        probation_opened=cohort(lambda fr: fr["probations_opened"] > 0),
        admitted_ge_0_6=cohort(lambda fr: fr["admitted_ge_0.6"] > 0),
        never_probation_never_admitted=cohort(lambda fr: fr["probations_opened"] == 0 and fr["admitted_ge_0.6"] == 0),
    )
    for name, sel in (("solidified", lambda fr: fr["solidified"] > 0),
                      ("probation_opened", lambda fr: fr["probations_opened"] > 0),
                      ("admitted_ge_0_6", lambda fr: fr["admitted_ge_0.6"] > 0),
                      ("never_probation_never_admitted", lambda fr: fr["probations_opened"] == 0 and fr["admitted_ge_0.6"] == 0)):
        rs = [fr for fr in fam_rows if sel(fr)]
        if rs:
            tot_h = sum(fr["log_hearings"] for fr in rs)
            tot_mv = sum(fr["log_movement_true"] for fr in rs)
            tot_mf = sum(fr["log_movement_false"] for fr in rs)
            cohorts[name]["pooled_log_hearings"] = tot_h
            cohorts[name]["pooled_movement_share_pct"] = pct(tot_mv, tot_mv + tot_mf)
            cohorts[name]["pooled_crossings_per_hearing"] = round(sum(fr["distinct_crossings"] for fr in rs) / tot_h, 2) if tot_h else None
            cohorts[name]["pooled_zero_new_row_share_pct"] = pct(sum(fr["hearings_zero_new_rows"] for fr in rs),
                                                                 sum(fr["hearings_reached_edge_write"] for fr in rs))

    # ---- 4c. could the edges serve as the evidence links of an ESTATE node for a probation/solidify? ----
    # authoring hearing = the CHAIN line just before each probation 'open' (<= ALIGN_MAX_S).  Its own batch
    # (rows written by exactly that hearing) is the evidence the candidate was authored from.
    batch_of_line = {}
    for (h, eid0), ln in aligned_of.items():
        if ln:
            batch_of_line[id(ln)] = (h, [b for b in batches[h] if b[0][0] == eid0][0])
    sol_ts = {float(p["ts"]) for p in sol}
    sol_images = {p["self_image"] for p in sol}
    estate = []
    for p in opens:
        pt = float(p["ts"])
        i = bisect.bisect_right(ch_ts, pt) - 1
        ln = chains[i] if i >= 0 and pt - ch_ts[i] <= ALIGN_MAX_S else None
        own = batch_of_line.get(id(ln)) if ln else None
        hh = None
        if ln:
            hs = [h for h in hashes if family(resolved.get(h, "")) == family(ln["lab"])]
            hh = hs
        prior = sum(1 for h in (hh or []) for e in by_hash[h] if e[5] <= pt)
        estate.append(dict(open_ts=time.strftime("%F %H:%M", time.localtime(pt)), theme=p["theme"][:60],
                           solidified=p["self_image"] in sol_images,
                           has_authoring_line=bool(ln), own_batch_rows=len(own[1]) if own else 0,
                           own_batch_distinct_sentences=len({content_of.get(r[2]) for r in own[1]}) if own else 0,
                           same_family_edges_before_open=prior))
    est_with_own = sum(1 for x in estate if x["own_batch_rows"] > 0)
    est_with_prior = sum(1 for x in estate if x["same_family_edges_before_open"] > 0)
    authored_hearings = [x for x in hearing_kinds if x["kind"] == "chain" and x["ts"] >= t_edges_first - 3600]
    authored_no_row = sum(1 for x in authored_hearings if id(x) not in aligned_ids)
    solid_rows = [x for x in estate if x["solidified"]]

    # ---- 5. estate-node readiness -------------------------------------------------------------
    text_cov_exact = pct(edges_exact, len(edges))
    text_cov_any = pct(sum(len(by_hash[h]) for h in resolved), len(edges))
    text_len_known = sum(1 for h in hashes if h in resolved)

    summary = dict(
        edges=len(edges), tensions_hashes=len(hashes), families=len(fam_rows),
        distinct_crossings=len(dst_distinct), light_events_total=n_events,
        edge_created_first=time.strftime("%F %T", time.localtime(edges[0][5])),
        edge_created_last=time.strftime("%F %T", time.localtime(edges[-1][5])),
        provenance_counts=dict(collections.Counter(e[4] for e in edges)),
        batches_total=sum(len(b) for b in batches.values()),
        rows_per_batch=dict(sorted(collections.Counter(len(b) for bs in batches.values() for b in bs).items())),
        hash_resolution=dict(exact=len(exact), aligned=len(resolved) - len(exact), unresolved=len(hashes) - len(resolved),
                             edge_share_exact_pct=text_cov_exact, edge_share_any_pct=text_cov_any),
        alignment_check_on_exact_hashes=dict(chk),
        reach=dict(
            dst_resolve=dict(resolve), distinct_dst_present=sum(1 for d in dst_distinct if d in ev),
            age_hours_p50=q(ages_h, .5), age_hours_p90=q(ages_h, .9), age_hours_p97=q(ages_h, .97), age_hours_max=round(ages_h[-1], 2),
            share_age_le_3_2h_pct=pct(sum(1 for x in ages_h if x <= 3.2), len(ages_h)),
            share_age_le_6h_pct=pct(sum(1 for x in ages_h if x <= 6), len(ages_h)),
            share_age_gt_24h=sum(1 for x in ages_h if x > 24),
            pool_rank_max=ranks[-1] if ranks else None, pool_rank_p50=q(ranks, .5),
            share_rank_le_300_pct=pct(sum(1 for x in ranks if x <= POOL_N), len(ranks)),
            window_300_event_span_hours_p10=q(spans, .1), p50=q(spans, .5), p90=q(spans, .9),
            distinct_moment_days=len(dst_days), edge_creation_days=len(edge_days),
            moment_days=sorted(dst_days)[:3] + ["..."] + sorted(dst_days)[-3:],
            moments_cited_by_more_than_one_hash=shared, moments_cited_by_more_than_one_family=shared_fam,
            cited_row_raw_input_prefix=dict(collections.Counter(raw_prefix.get(e[2], 'other') for e in edges).most_common()),
            cited_moment_source=dict(src_cnt), all_events_source=dict(src_all),
            batches_with_tied_weights=f"{tie_batches}/{multi}",
        ),
        duplication=dict(
            corpus_light_events=corpus[0], corpus_distinct_contents=corpus[1],
            corpus_dup_pct=pct(corpus[0] - corpus[1], corpus[0]),
            edge_rows=rows_total, distinct_event_ids=len(dst_distinct), distinct_sentences=distinct_content,
            batches_with_a_repeated_sentence=f"{batches_with_dup}/{len(per_batch_dup)}",
            mean_distinct_sentence_fraction_per_batch=mean_distinct_frac,
            rows_repeating_a_sentence_already_cited_by_same_tension=repeat_sentence_rows),
        recurrence=dict(
            hearings_since_writer=len(all_h_since), hearings_no_crossing_found=len(no_crossing),
            hearings_reached_edge_write=len(reached), reached_movement_counts={str(k): v for k, v in reached_mv.items()},
            hearings_reached_but_zero_new_rows=len(reached_no_row),
            zero_new_rows_by_movement={str(k): v for k, v in reached_no_row_mv.items()},
            first_batch_mean_rows=round(statistics.mean(first_batch_rows), 2),
            later_batch_mean_rows=round(statistics.mean(later_batch_rows), 2) if later_batch_rows else None,
            later_batches=len(later_batch_rows)),
        estate_link_test=dict(probation_opens=len(estate), opens_with_authoring_hearing_line=sum(1 for x in estate if x["has_authoring_line"]),
                              opens_whose_own_hearing_wrote_rows=est_with_own, opens_with_any_same_family_edge_before=est_with_prior,
                              mean_own_batch_rows=round(statistics.mean(x["own_batch_rows"] for x in estate), 2) if estate else None,
                              authored_chain_hearings=len(authored_hearings), authored_hearings_with_zero_new_rows=authored_no_row,
                              solidified_probations=solid_rows, all_opens=estate),
        cohorts=cohorts, probation_since_edges=dict(opened=len(opens), solidified=len(sol), reverted=len(rev),
                                                   judged_rows=len(judged), judged_ge_0_6=sum(1 for j in judged if (j['warranted'] or 0) >= .6)),
        probation_families_without_edges=unmatched_prob, judge_families_without_edges=unmatched_judge,
        estate_readiness=dict(tension_text_stored_on_edge=False, hearing_id_on_edge=False,
                              recurrence_visible_on_edges=False, tensions_text_recovered=f"{text_len_known}/{len(hashes)}"),
    )
    db.close()
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "per_hash.json").write_text(json.dumps(rows_out, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "per_family.json").write_text(json.dumps(fam_rows, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False)[:9000])
    print("\nFAMILIES")
    for fr in fam_rows:
        print({k: fr[k] for k in ("family", "hashes", "edges", "distinct_crossings", "batches_with_new_rows",
                                  "log_hearings", "log_movement_share", "days_spanned", "probations_opened",
                                  "solidified", "judged", "admitted_ge_0.6")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

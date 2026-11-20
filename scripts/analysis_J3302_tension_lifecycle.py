"""J-3302 read-only analysis: what ENDS a tension in T4?

Reads (never writes) the live Nascence stores:
  data/nascence.log                    T4 CHAIN / T4 considered / T4 question RESTED / probation lines
  data/logs/provisional_identity.jsonl probation open / solidify / revert rows (full theme text)
  data/logs/t4_emissary_judge.jsonl    one row per judged candidate
  data/subconscious_state.json         t4_rests, t4_fatigue_counts (as of the last save)
  data/memory/nascence.db              shadow_events (sqlite mode=ro&immutable=1; WAL is empty, Du is down)
Writes only under docs/lab/J-3302_data/ in this worktree.

Usage:  python scripts/analysis_J3302_tension_lifecycle.py [--live C:/Nascence] [--out DIR]
"""
from __future__ import annotations
import argparse, collections, json, re, sqlite3, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

FATIGUE_LIMIT = 3            # nodes/subconscious_node.py T4_FATIGUE_LIMIT
REST_S = 3 * 86400           # T4_REST_S
NO_MOVE = ("not yet crossed", "still circling", "no specific delta")


def label_key(label: str) -> str:            # copy of SubconsciousNode._t4_label_key
    return " ".join(sorted({w for w in (label or "").lower().split() if len(w) >= 4}))[:200]


def toks(label: str) -> set:                 # the rest matcher's token set
    return {w for w in (label or "").lower().split() if len(w) >= 4}


def jacc(a: set, b: set) -> float:
    return len(a & b) / max(1, len(a | b)) if a and b else 0.0


def family(label: str) -> str:
    """Number-stripped, prefix-aligned family id (log labels are cut at 40 or 60 chars)."""
    s = (label or "").lower().strip()
    s = re.sub(r"\s*\(felt.*$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s[:36].strip() or "(no label)"


TS = r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ "
RE_CHAIN = re.compile(TS + r".*T4 CHAIN — tension=(?P<q>['\"])(?P<lab>.*?)(?P=q) →")
RE_CONS = re.compile(TS + r".*T4 considered (?P<n>\d+) fragment\(s\) — no change: (?P<why>.*?) \(tension: (?P<q>['\"])(?P<lab>.*)(?P=q)\)\s*$")
RE_CONS_OLD = re.compile(TS + r".*T4 considered (?P<n>\d+) fragment\(s\) — no genuine change")
RE_REST = re.compile(TS + r".*T4 question RESTED after \d+ no-movement hearings: (?P<q>['\"])(?P<lab>.*)(?P=q) \(returns")
RE_ADOPT = re.compile(TS + r".*T4 candidate adopted PROVISIONALLY")
RE_RES = re.compile(TS + r".*T4 probation RESOLVED → (?P<dec>\w+)")
RE_SELF = re.compile(TS + r".*T4 SELF-AUTHORING")
RE_DISCH = re.compile(TS + r".*T4 DISCHARGE — metabolised (?P<q>['\"])(?P<lab>.*?)(?P=q)")


def epoch(s: str) -> float:
    return time.mktime(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


def parse_log(path: Path):
    ev = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            if "T4 " not in ln or "[subconscious]" not in ln:
                continue
            for kind, rx in (("chain", RE_CHAIN), ("considered", RE_CONS), ("rested", RE_REST),
                             ("adopt", RE_ADOPT), ("resolved", RE_RES), ("selfauth", RE_SELF),
                             ("discharge", RE_DISCH), ("considered_old", RE_CONS_OLD)):
                m = rx.match(ln)
                if m:
                    d = m.groupdict()
                    ev.append({"t": epoch(m.group(1)), "ts": m.group(1), "kind": kind,
                               "label": d.get("lab"), "why": d.get("why"), "dec": d.get("dec")})
                    break
    ev.sort(key=lambda e: e["t"])
    return ev


def load_jsonl(p: Path):
    out = []
    if p.exists():
        for ln in open(p, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default="C:/Nascence")
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3302_data"))
    a = ap.parse_args()
    live = Path(a.live); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    data = live / "data"

    ev = parse_log(data / "nascence.log")
    prov = load_jsonl(data / "logs" / "provisional_identity.jsonl")
    judge = load_jsonl(data / "logs" / "t4_emissary_judge.jsonl")
    ledger = load_jsonl(data / "contradiction_ledger_log.jsonl")
    state = json.load(open(data / "subconscious_state.json", encoding="utf-8"))
    log_end = max(e["t"] for e in ev)

    # ---- hearings ------------------------------------------------------------------------------
    hearings = [e for e in ev if e["kind"] in ("chain", "considered") and e["label"]]
    chains = [e for e in ev if e["kind"] == "chain"]
    fams: dict[str, dict] = collections.defaultdict(lambda: collections.defaultdict(int))
    firsts, lasts, labels_seen, keys_seen = {}, {}, collections.defaultdict(set), collections.defaultdict(set)
    for h in hearings:
        fk = family(h["label"])
        F = fams[fk]
        F["hearings"] += 1
        if h["kind"] == "chain":
            F["chains_authored"] += 1
        else:
            F["considered_no_change"] += 1
            for r in NO_MOVE:
                if r in (h["why"] or ""):
                    F["nc_" + r.replace(" ", "_")] += 1
        firsts.setdefault(fk, h["t"]); lasts[fk] = h["t"]
        labels_seen[fk].add(h["label"]); keys_seen[fk].add(label_key(h["label"]))
    for e in ev:
        if e["kind"] == "rested":
            fk = family(e["label"])
            fams[fk]["rests"] += 1
            lasts[fk] = max(lasts.get(fk, 0), e["t"])
            firsts.setdefault(fk, e["t"])

    # judged candidates -> nearest preceding CHAIN within 900 s (else legacy/unlabelled)
    legacy_judged = 0
    chain_ts = [(c["t"], family(c["label"])) for c in chains]
    for j in judge:
        t = float(j.get("ts", 0))
        owner = None
        for ct, fk in reversed(chain_ts):
            if ct <= t <= ct + 900:
                owner = fk; break
            if ct < t - 900:
                break
        if owner is None:
            legacy_judged += 1
            continue
        fams[owner]["judged"] += 1
        w = j.get("emissary_warranted")
        if w is not None and float(w) >= 0.6:
            fams[owner]["admitted"] += 1
    # probations (full theme text)
    for p in prov:
        ev_name = p.get("event"); fk = family(p.get("theme", ""))
        if ev_name == "open":
            fams[fk]["probations"] += 1
        elif ev_name == "solidify":
            fams[fk]["solidified"] += 1
        elif ev_name == "revert":
            fams[fk]["reverted"] += 1

    rows = []
    for fk, F in fams.items():
        fa, la = firsts.get(fk), lasts.get(fk)
        span = (la - fa) / 86400 if fa and la else 0.0
        age_end = (log_end - la) / 86400 if la else None
        tail = [e for e in ev if e["label"] and family(e["label"]) == fk
                and e["kind"] in ("chain", "considered", "rested")][-2:]
        ended_by_rest = any(x["kind"] == "rested" for x in tail)
        status = ("LIVE (heard in last 24h of log)" if age_end is not None and age_end < 1
                  else "last event was a rest" if ended_by_rest
                  else "went quiet WITHOUT a rest")
        rows.append({"family": fk, **{k: int(v) for k, v in F.items()},
                     "first": time.strftime("%m-%d", time.localtime(fa)) if fa else "",
                     "last": time.strftime("%m-%d", time.localtime(la)) if la else "",
                     "span_days": round(span, 1), "distinct_label_strings": len(labels_seen[fk]),
                     "distinct_code_keys": len(keys_seen[fk]), "end_state": status})
    rows.sort(key=lambda r: -r.get("hearings", 0))
    json.dump(rows, open(out / "family_table.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---- fatigue replay: code key vs number-stripped family key ---------------------------------
    def replay(keyfn):
        counts, rests = collections.defaultdict(int), []
        for e in ev:
            if e["kind"] not in ("chain", "considered") or not e["label"]:
                continue
            k = keyfn(e["label"])
            if e["kind"] == "chain":
                counts.pop(k, None); continue
            why = e["why"] or ""
            if "no specific delta" in why:
                counts.pop(k, None)          # movement was judged true before the delta stage
            if any(r in why for r in NO_MOVE):
                counts[k] += 1
                if counts[k] >= FATIGUE_LIMIT:
                    counts.pop(k, None); rests.append((e["ts"], e["label"][:60]))
        return rests
    actual_rests = [(e["ts"], e["label"][:60]) for e in ev if e["kind"] == "rested"]
    first_chain = min(c["t"] for c in chains)
    r_code = [r for r in replay(label_key) if epoch(r[0]) >= first_chain]
    r_fam = [r for r in replay(family) if epoch(r[0]) >= first_chain]
    r_act = [r for r in actual_rests if epoch(r[0]) >= first_chain]

    # ---- the factual_recall family (prediction_error:factual_recall) -------------------------------
    FR = "prediction_error:factual_recall"
    con = sqlite3.connect("file:%s?mode=ro&immutable=1" % (data / "memory" / "nascence.db").as_posix(), uri=True)
    con.row_factory = sqlite3.Row
    pe = con.execute("SELECT event_id,timestamp,source,resolved,corrections,raw_input FROM shadow_events "
                     "WHERE source='prediction_error' ORDER BY timestamp").fetchall()
    pe_fr, pairs = [], collections.Counter()
    for r in pe:
        try:
            c = json.loads(r["corrections"] or "[]")
        except Exception:
            c = []
        lab = str(c[0]) if c else ""
        if lab.lower().startswith(FR):
            pe_fr.append((r["event_id"], r["timestamp"], lab, r["resolved"]))
            m = re.search(r"felt ([\d.]+) vs real ([\d.]+)", lab)
            if m:
                pairs[(m.group(1), m.group(2))] += 1
    pair_list = sorted(pairs)
    cross = []
    for x in pair_list:
        for y in pair_list:
            if x < y:
                lx = f"{FR} (felt {x[0]} vs real {x[1]})"
                ly = f"{FR} (felt {y[0]} vs real {y[1]})"
                cross.append((x, y, round(jacc(toks(lx), toks(ly)), 3)))
    below = [c for c in cross if c[2] <= 0.5]

    # ---- 10-30 commit: what would discharge retire? ------------------------------------------
    sol = [p for p in prov if p.get("event") == "solidify"]
    sol_1030 = [p for p in sol if time.strftime("%m-%d", time.localtime(p["ts"])) == "10-30"]
    disch = {}
    if sol_1030:
        t0 = float(sol_1030[0]["ts"])
        win = con.execute("SELECT event_id,timestamp,source,resolved,corrections FROM shadow_events "
                          "WHERE timestamp<=? ORDER BY timestamp DESC LIMIT 300", (t0,)).fetchall()
        win_fr = [w for w in win if w["source"] == "prediction_error" and FR in (w["corrections"] or "")]
        all_fr_upto = [p for p in pe_fr if p[1] <= t0]
        src_counts = collections.Counter(w["source"] for w in win)
        disch = {"solidify_ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0)),
                 "window_300_span_h": round((win[0]["timestamp"] - win[-1]["timestamp"]) / 3600, 2),
                 "window_300_sources": dict(src_counts),
                 "window_factual_recall_pe_events": len(win_fr),
                 "all_factual_recall_pe_events_ever_up_to_commit": len(all_fr_upto),
                 "pe_events_resolved_ever": sum(1 for r in pe if r["resolved"]),
                 "pe_events_total": len(pe),
                 "pe_factual_recall_total_now": len(pe_fr)}
        sys.path.insert(0, str(ROOT))
        try:
            from core import tension_ledger as _tl
            ids = [w["event_id"] for w in win_fr]

            def sources(remap_pe):
                return {w["event_id"]: (("prediction_error_resolved" if remap_pe else w["source"]), w["timestamp"])
                        for w in win_fr}
            t = {"member_event_ids": ids, "label": FR}
            base = _tl.score_tension(t, sources(False), now=t0)
            cur = _tl.score_tension(t, sources(False), now=t0 + 1, resolutions={i: 0.6 for i in ids})
            hyp = _tl.score_tension(t, sources(True), now=t0 + 1)
            disch["pressure_before"] = base["contradiction_pressure"]
            disch["pressure_after_CURRENT_code_remap_is_critic_only_plus_0.6_drain"] = cur["contradiction_pressure"]
            disch["contradiction_count_after_CURRENT_code"] = cur["contradiction_count"]
            disch["pressure_after_if_remap_also_covered_prediction_error"] = hyp["contradiction_pressure"]
        except Exception as exc:
            disch["pressure_calc_error"] = repr(exc)

    after = []
    first_after_s = None
    if sol_1030:
        t0 = float(sol_1030[0]["ts"])
        for h in hearings:
            if h["t"] >= t0 - 1 and h["label"].lower().startswith(FR):
                after.append((h["ts"], h["kind"], h["label"][:60], (h["why"] or "")[:40]))
        if after:
            first_after_s = round(epoch(after[0][0]) - t0, 1)

    # ---- rest leaks: a prediction_error question heard again INSIDE its own 3-day rest ---------------
    # The log cuts a CHAIN label at 40 chars (the 'real' number is lost), so the full label at that hearing is
    # RECONSTRUCTED as the newest prediction_error event of the same domain at or before the hearing (INFERRED: it
    # is what top_contradiction's sharpened label would be if that tension were the top-pressure one).
    pe_lab = []
    for r in pe:
        try:
            c0 = str(json.loads(r["corrections"] or "[]")[0])
        except Exception:
            continue
        pe_lab.append((r["timestamp"], c0))
    leaks = []
    for e in ev:
        if e["kind"] != "rested" or not (e["label"] or "").lower().startswith("prediction_error"):
            continue
        dom = e["label"].split(" (")[0].lower(); rt = toks(e["label"])
        for h in hearings:
            if e["t"] + 30 < h["t"] < e["t"] + REST_S and h["label"].lower().startswith(dom):
                prev = [x for x in pe_lab if x[0] <= h["t"] and x[1].lower().startswith(dom)]
                if prev:
                    full = prev[-1][1]
                    j = round(jacc(toks(full), rt), 3)
                    leaks.append({"rest": e["ts"], "rest_label": e["label"][:60], "heard": h["ts"],
                                  "reconstructed_label": full, "jaccard_vs_rest": j, "rest_would_match": j > 0.5})
    leaks = [x for x in leaks if not x["rest_would_match"]]

    summary = {
        "rest_leaks_reconstructed": leaks,
        "log_range": [ev[0]["ts"], ev[-1]["ts"]],
        "events_parsed": dict(collections.Counter(e["kind"] for e in ev)),
        "families": len(rows), "hearings_total": len(hearings),
        "legacy_judged_rows_no_chain": legacy_judged, "judge_rows": len(judge),
        "rests_actual_since_first_chain": len(r_act),
        "rests_replay_code_key": len(r_code), "rests_replay_family_key": len(r_fam),
        "live_state_t4_rests": state.get("t4_rests"),
        "live_state_t4_fatigue_counts": state.get("t4_fatigue_counts"),
        "factual_recall_label_pairs_in_db": {f"felt {k[0]} real {k[1]}": v for k, v in pairs.items()},
        "factual_recall_cross_pair_jaccards_le_0.5": below,
        "factual_recall_cross_pair_jaccards_all": cross,
        "n_pe_factual_recall_events": len(pe_fr),
        "discharge_10_30": disch,
        "hearings_after_10_30_solidify": {"first_after_seconds": first_after_s, "n": len(after),
                                          "rows": after[:60]},
        "ledger_rows": len(ledger),
    }
    json.dump(summary, open(out / "summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"actual": r_act, "replay_code_key": r_code, "replay_family_key": r_fam},
              open(out / "rest_replay.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:7000])
    print()
    hdr = ["family", "hearings", "chains_authored", "considered_no_change", "judged", "admitted", "probations",
           "solidified", "reverted", "rests", "first", "last", "span_days", "distinct_label_strings",
           "distinct_code_keys", "end_state"]
    print("\t".join(hdr))
    for r in rows[:60]:
        print("\t".join(str(r.get(h, 0)) for h in hdr))


if __name__ == "__main__":
    main()

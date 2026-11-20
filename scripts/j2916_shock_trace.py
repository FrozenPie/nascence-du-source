"""J-2916 (F-3587): how far do external-shock fragments travel into T2 synthesis, curiosity, pursuits, replay and
deliberation?  READ-ONLY analysis.

Opens the live fragment DB with mode=ro&immutable=1 and reads data/*.jsonl and nascence.log without writing.
Writes only under --out (default docs/lab/J-2916_data/ of this worktree).

Two kinds of evidence, kept apart:
  ID-LEVEL   memory_fragments.derived_from (parent fragment ids of a synthesis / reflection / action row),
             memory_edges and memory_links rows that name the fragment id, memory_fragments.replay_count.
  LEXICAL    a later record in a stream "cites" the fragment when it contains the page title, a distinctive title
             word, or >= 2 distinctive words of the first extract sentences, within 48 h after the fragment.
Controls:
  * non-shock research fragments ("[Looked up: ... (asked by him / pursuit / twig ...)]") over the same window;
  * the PRE window (48 h before the fragment): an uninvited shock should show ~0 there, a chosen lookup shows its topic
    already in the stream, so POST minus PRE is the uptake;
  * a time-shift null: the same shock keywords counted in windows shifted by +-7/14 days (chance rate of the words).
"""
from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import json
import re
import sqlite3
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NASC = Path(r"C:\Nascence")
H = 3600.0
WIN_H = 48.0
DAYS = 30

_STOP = set("""about above after again against almost along also although always among another around because been before being
below between both could does doing down during each either else even ever every first from further have having here
however into itself just least less like made make many might more most much must never next only other over same
several shall should since some still such than that their them then there these they this those though through thus
under until upon very were what when where whether which while whom will with within without would your yours
film films album albums series season county school station river national university united states football song songs
television episode village district church company american british english species family genus known located small
named called also which their there where about people world city town north south east west first second third
born died years year time""".split())
_TOK = re.compile(r"[a-z][a-z'\-]{2,}")


def toks(text: str) -> set[str]:
    return {t.strip("'-") for t in _TOK.findall((text or "").lower())}


def parse_log_ts(s: str) -> float | None:
    try:
        return dt.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").timestamp()
    except Exception:
        return None


class Stream:
    """Time-sorted text records of one downstream channel."""

    def __init__(self, name: str):
        self.name = name
        self.recs: list[tuple[float, str, set[str]]] = []
        self._ts: list[float] = []

    def add(self, ts: float, text: str):
        if ts and text:
            self.recs.append((ts, text.lower(), set()))

    def seal(self):
        self.recs.sort(key=lambda r: r[0])
        self.recs = [(t, x, toks(x)) for (t, x, _) in self.recs]
        self._ts = [r[0] for r in self.recs]

    def window(self, a: float, b: float):
        i = bisect.bisect_right(self._ts, a)   # strictly after a
        j = bisect.bisect_right(self._ts, b)
        return self.recs[i:j]

    def __len__(self):
        return len(self.recs)


def load(args):
    global DAYS
    DAYS = args.days
    db = args.db
    c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro&immutable=1", uri=True)
    end = c.execute("select max(timestamp) from memory_fragments").fetchone()[0]
    start = end - DAYS * 86400
    rows = c.execute("select fragment_id,timestamp,importance,relevance,replay_count,origin,content,layer,derived_from "
                     "from memory_fragments where timestamp>=? and timestamp<=?", (start - 21 * 86400, end)).fetchall()
    return c, start, end, rows


def build(args):
    c, start, end, rows = load(args)
    D = args.data
    streams = {k: Stream(k) for k in ("T2", "curiosity", "curiosity_seeds", "frontier_q", "pursuits", "replay", "deliberation", "inner_thought")}
    shocks, controls = [], []
    world_ts: list[float] = []      # origins study/reading/research, the feed core/memory/store.recent_world_material reads
    derived: dict[str, list[tuple[float, str]]] = collections.defaultdict(list)
    n_orig = collections.Counter()
    for fid, ts, imp, rel, rc, origin, content, layer, dfrom in rows:
        if origin in ("study", "reading", "research"):
            world_ts.append(ts)
        if origin == "subconscious_synthesis":
            streams["T2"].add(ts, content)
        elif origin == "inner_thought":
            streams["inner_thought"].add(ts, content)
        if ts >= start and dfrom and dfrom != "[]":
            try:
                for p in json.loads(dfrom):
                    derived[p].append((ts, origin))
            except Exception:
                pass
        if origin == "research" and (content or "").startswith("[Looked up:") and ts >= start:
            m = re.match(r"\[Looked up: '(.*?)' \((.*?)\)\]\s*(.*)", content or "", re.S)
            if not m:
                continue
            rec = dict(id=fid, ts=ts, imp=imp, rel=rel, replay=rc or 0, layer=layer, title=m.group(1),
                       via=m.group(2), extract=m.group(3))
            (shocks if m.group(2).startswith("external shock") else controls).append(rec)
            n_orig[rec["via"].split(" ")[0] if rec["via"] else "?"] += 1
    # deliberation
    for l in open(D / "deliberation_log.jsonl", encoding="utf-8", errors="replace"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("ts", 0) >= start - 21 * 86400:
            streams["deliberation"].add(d["ts"], " ".join(str(d.get(k, "")) for k in ("about", "raw", "grounding", "integrated")))
    # curiosity
    for l in open(D / "curiosity_log.jsonl", encoding="utf-8", errors="replace"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("ts", 0) >= start - 21 * 86400:
            streams["curiosity"].add(d["ts"], " ".join(d.get("questions") or []))
            streams["curiosity_seeds"].add(d["ts"], " ".join(d.get("seeds_offered") or []))
    # pursuits: born events (question is cut to 100 chars in the log) + pursuits_active full text
    seen = set()
    for l in open(D / "pursuits_shadow.jsonl", encoding="utf-8", errors="replace"):
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d.get("event") == "born" and d.get("ts", 0) >= start - 21 * 86400:
            streams["pursuits"].add(d["ts"], (d.get("question") or "") + " " + (d.get("about") or ""))
            seen.add(d.get("id"))
    try:
        for p in json.load(open(D / "pursuits_active.json", encoding="utf-8")):
            if p.get("id") not in seen and p.get("born", 0) >= start - 21 * 86400:
                streams["pursuits"].add(p["born"], (p.get("question") or "") + " " + (p.get("about") or ""))
    except Exception:
        pass
    # nascence.log lines: world-question born (curiosity), sleep replay (replay)
    log_counts = collections.Counter()
    shock_log_titles = []
    lo = start - 21 * 86400
    LOG_FROM = dt.datetime.fromtimestamp(lo - 86400).strftime("%Y-%m-%d")
    with open(D / "nascence.log", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line[:10] < LOG_FROM:
                continue
            if "world-question born" in line:
                ts = parse_log_ts(line)
                if ts and ts >= lo:
                    streams["frontier_q"].add(ts, line.split("born", 1)[1]); log_counts["wq"] += 1
            elif "sleep replay:" in line:
                ts = parse_log_ts(line)
                if ts and ts >= lo:
                    streams["replay"].add(ts, line.split("strengthened", 1)[-1]); log_counts["replay"] += 1
            elif "external shock" in line and "[Looked up:" not in line:
                shock_log_titles.append(line[:160].strip())
    for s in streams.values():
        s.seal()
    # edges / links / replay by id
    ids = {r["id"] for r in shocks + controls}
    edges = collections.defaultdict(collections.Counter)
    for src_kind, src_id, dst_kind, dst_id, et in c.execute("select src_kind,src_id,dst_kind,dst_id,edge_type from memory_edges"):
        for x, other_kind in ((src_id, dst_kind), (dst_id, src_kind)):
            if x in ids:
                edges[x][f"{et}->{other_kind}"] += 1
    links = collections.defaultdict(collections.Counter)
    for p, ch, lt in c.execute("select parent_id,child_id,link_type from memory_links"):
        for x in (p, ch):
            if x in ids:
                links[x][lt] += 1
    return dict(c=c, start=start, end=end, streams=streams, shocks=sorted(shocks, key=lambda r: r["ts"]),
                controls=sorted(controls, key=lambda r: r["ts"]), derived=derived, edges=edges, links=links,
                world_ts=sorted(world_ts), log_counts=log_counts, shock_log_titles=shock_log_titles, n_orig=n_orig, rows=rows)


def background_df(streams):
    """Document frequency of every token over the inner-thought + deliberation + T2 + curiosity corpus."""
    df = collections.Counter()
    n = 0
    for k in ("inner_thought", "deliberation", "T2", "curiosity"):
        for _, _, tk in streams[k].recs:
            n += 1
            df.update(tk)
    return df, n


def keywords(rec, df, n):
    title = re.sub(r"\s*\(.*?\)\s*", " ", rec["title"]).strip().lower()
    t_all = [t for t in toks(title) if t not in _STOP and len(t) >= 4]
    t_dist = sorted(t for t in t_all if df[t] / n <= 0.002)
    # extract tokens: rare, long, from the first ~300 chars (what the seed shows)
    ex = [t for t in toks(rec["extract"][:300]) if t not in _STOP and len(t) >= 6 and df[t] / n <= 0.002
          and t not in t_dist]
    ex = sorted(ex, key=lambda t: (df[t], -len(t)))[:8]
    # tier-1 (whole title string) only counts when the title is not a single everyday word of his own vocabulary:
    # multi-word titles, or a one-word title that is itself distinctive. ("Remains", "Perfect" match thousands of lines.)
    use_title = (len(toks(title)) >= 2 and bool(t_dist)) or (len(toks(title)) == 1 and bool(t_dist))
    return (title if use_title else ""), t_dist, ex


def cites(rec_text, rec_toks, title, t_dist, ex):
    """-> tier: 1 title string, 2 distinctive title word, 3 >=2 distinctive extract words, 0 none."""
    if len(title) >= 4 and title in rec_text:
        return 1
    if any(t in rec_toks for t in t_dist):
        return 2
    if len(ex) and sum(1 for t in ex if t in rec_toks) >= 2:
        return 3
    return 0


def count(stream, ts, kw, lo_h, hi_h):
    title, t_dist, ex = kw
    tiers = collections.Counter()
    for (t, txt, tk) in stream.window(ts + lo_h * H, ts + hi_h * H):
        v = cites(txt, tk, title, t_dist, ex)
        if v:
            tiers[v] += 1
    return tiers


def fmt_rate(vals):
    if not vals:
        return dict(n=0)
    return dict(n=len(vals), mean=round(statistics.mean(vals), 3), median=statistics.median(vals),
                frac_ge1=round(sum(1 for v in vals if v >= 1) / len(vals), 3), total=sum(vals))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=NASC / "data" / "memory" / "nascence.db")
    ap.add_argument("--data", type=Path, default=NASC / "data")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "lab" / "J-2916_data")
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    B = build(args)
    streams, shocks, controls, end, start = B["streams"], B["shocks"], B["controls"], B["end"], B["start"]
    df, n = background_df(streams)
    # only fragments whose full 48h post window is observed (and for shifted null, shifts stay inside the data span)
    shocks_f = [s for s in shocks if s["ts"] + WIN_H * H <= end]
    controls_f = [s for s in controls if s["ts"] + WIN_H * H <= end]
    out = dict(window=dict(start=dt.datetime.fromtimestamp(start).isoformat(), end=dt.datetime.fromtimestamp(end).isoformat()),
               n_shock=len(shocks), n_shock_observable=len(shocks_f), n_control=len(controls), n_control_observable=len(controls_f),
               control_via_counts=dict(B["n_orig"]), stream_sizes={k: len(v) for k, v in streams.items()},
               log_lines=dict(B["log_counts"]), shock_titles=[s["title"] for s in shocks])
    def imp(xs):
        v = sorted(x["imp"] for x in xs if x["imp"] is not None)
        return dict(median=round(statistics.median(v), 3), p10=round(v[len(v)//10], 3), p90=round(v[(len(v)*9)//10], 3)) if v else {}
    out["importance_now"] = dict(shock=imp(shocks), control=imp(controls))
    out["layer_now"] = dict(shock=dict(collections.Counter(s["layer"] for s in shocks)),
                            control=dict(collections.Counter(s["layer"] for s in controls)))
    # importance-matched control: within shock p10..p90 of CURRENT importance
    ish = out["importance_now"]["shock"]
    ctl_m = [x for x in controls_f if x["imp"] is not None and ish and ish["p10"] <= x["imp"] <= ish["p90"]]
    out["n_control_importance_matched"] = len(ctl_m)

    snames = ["T2", "curiosity", "curiosity_seeds", "frontier_q", "pursuits", "replay", "deliberation", "inner_thought"]
    shifts = [-14, -7, 7, 14]
    def lex(group, null=False):
        res = {}
        per = {}
        for sn in snames:
            post, pre, nul = [], [], []
            tier = collections.Counter()
            for r in group:
                kw = keywords(r, df, n)
                if not (kw[1] or kw[2] or len(kw[0]) >= 4):
                    continue
                cnt = count(streams[sn], r["ts"], kw, 0, WIN_H)
                post.append(sum(cnt.values())); tier.update(cnt)
                pre.append(sum(count(streams[sn], r["ts"], kw, -WIN_H, 0).values()))
                if null:
                    for sh in shifts:
                        a = r["ts"] + sh * 86400
                        if a >= start - 7 * 86400 and a + WIN_H * H <= end:
                            nul.append(sum(count(streams[sn], a, kw, 0, WIN_H).values()))
                per.setdefault(r["id"], {})[sn] = post[-1]
            res[sn] = dict(post=fmt_rate(post), pre=fmt_rate(pre), tiers=dict(tier))
            if null:
                res[sn]["shift_null"] = fmt_rate(nul)
        return res, per
    out["lexical_shock"], per_s = lex(shocks_f, null=True)
    out["lexical_control_all"], per_c = lex(controls_f, null=True)
    out["lexical_control_importance_matched"], _ = lex(ctl_m)

    # ---- id level
    def idlevel(group):
        childs = collections.Counter(); within = collections.Counter(); anyc = 0; replayed = 0; rc_tot = 0
        edge_ct = collections.Counter(); link_ct = collections.Counter(); with_child = 0
        for r in group:
            ch = B["derived"].get(r["id"], [])
            if ch:
                with_child += 1
            for (t, o) in ch:
                childs[o] += 1
                if 0 < t - r["ts"] <= WIN_H * H:
                    within[o] += 1
            anyc += len(ch)
            rc_tot += r["replay"]; replayed += 1 if r["replay"] > 0 else 0
            edge_ct.update(B["edges"].get(r["id"], {})); link_ct.update(B["links"].get(r["id"], {}))
        return dict(n=len(group), fragments_with_derived_child=with_child, derived_children_total=anyc,
                    derived_children_by_origin=dict(childs), derived_children_within_48h_by_origin=dict(within),
                    replay_fragments=replayed, replay_count_total=rc_tot,
                    replay_frac=round(replayed / len(group), 3) if group else None,
                    edges=dict(edge_ct), links=dict(link_ct))
    out["id_level_shock"] = idlevel(shocks)
    out["id_level_control"] = idlevel(controls)
    # age-matched replay: only fragments older than 4 days
    def old(g): return [x for x in g if x["ts"] <= end - 4 * 86400]
    for k, g in (("shock", shocks), ("control", controls)):
        o = old(g)
        out[f"replay_old_{k}"] = dict(n=len(o), frac_replayed=round(sum(1 for x in o if x["replay"] > 0) / len(o), 3) if o else None,
                                    mean_replay=round(statistics.mean([x["replay"] for x in o]), 3) if o else None)
    # ---- exposure reconstruction: recent_world_material() = newest-N of study/reading/research, no age floor.
    # T2 (_t2_synthesise, limit=6) and T4's world block (limit=6) read the newest 6; the curiosity study block reads the
    # newest 9 and keeps 3 distinct subjects. A fragment is "in the feed" from its own timestamp until N newer world rows
    # exist. Exposure = a downstream record written while the fragment was in the feed.
    wts = B["world_ts"]
    def feed_end(ts, nn):
        i = bisect.bisect_left(wts, ts)           # index of the fragment itself (or its tie)
        j = i + nn          # the fragment drops out when the nn-th NEWER row arrives
        return wts[j] if j < len(wts) else end
    def exposure(group, sn, nn):
        n_exp = n_cite = frags_exposed = frags_cited = 0
        feed_hours = []
        for r in group:
            kw = keywords(r, df, n)
            fe = feed_end(r["ts"], nn)
            feed_hours.append((fe - r["ts"]) / H)
            recs = streams[sn].window(r["ts"], fe)
            if recs:
                frags_exposed += 1
            c_ = sum(1 for (t, txt, tk) in recs if cites(txt, tk, *kw))
            n_exp += len(recs); n_cite += c_
            frags_cited += 1 if c_ else 0
        return dict(n_frag=len(group), frags_exposed=frags_exposed, frags_cited=frags_cited, exposures=n_exp, cites=n_cite,
                    cite_per_exposure=round(n_cite / n_exp, 4) if n_exp else None,
                    median_feed_hours=round(statistics.median(feed_hours), 2) if feed_hours else None)
    exp = {}
    for label, g in (("shock", shocks), ("control", controls)):
        exp[label] = {"T2_top6": exposure(g, "T2", 6), "curiosity_top3": exposure(g, "curiosity", 3),
                      "curiosity_top9": exposure(g, "curiosity", 9)}
    out["feed_exposure"] = exp
    t2_in = [r for r in streams["T2"].recs if start <= r[0] <= end]
    exposed_t2 = set()
    for r in shocks:
        fe = feed_end(r["ts"], 6)
        for (t, _, _) in streams["T2"].window(r["ts"], fe):
            exposed_t2.add(t)
    out["t2_denominators"] = dict(t2_written_in_window=len(t2_in), t2_with_shock_in_top6_feed=len([t for t in exposed_t2 if start <= t <= end]))

    # ---- audit sample: every T2 / replay / pursuits cite and the first curiosity cites for shocks, with context
    samples = []
    for r in shocks_f:
        kw = keywords(r, df, n)
        for sn in ("T2", "curiosity", "frontier_q", "replay", "pursuits"):
            for (t, txt, tk) in streams[sn].window(r["ts"], r["ts"] + WIN_H * H):
                v = cites(txt, tk, *kw)
                if v:
                    probe = kw[0] if v == 1 else next((w for w in kw[1] + kw[2] if w in txt), "")
                    i = txt.find(probe) if probe else 0
                    samples.append(dict(shock=r["title"], stream=sn, tier=v, at=dt.datetime.fromtimestamp(t).strftime("%m-%d %H:%M"),
                                        lag_h=round((t - r["ts"]) / H, 2), ctx=txt[max(0, i - 70): i + 90].replace(chr(10), " ")))
    out["hit_samples"] = samples

    # ---- significance (exact one-sided Fisher), small counts so say them as counts
    from math import comb
    def fisher_ge(a, n1, b, n2):
        """P(X >= a) for X ~ Hypergeom: a hits of n1 in group 1 given a+b total hits among n1+n2."""
        k = a + b; N = n1 + n2
        return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / comb(N, k)
    def frac_cited(d, sn):
        return d[sn]["post"]
    tests = {}
    sh_t2 = round(out["lexical_shock"]["T2"]["post"]["frac_ge1"] * out["lexical_shock"]["T2"]["post"]["n"])
    co_t2 = round(out["lexical_control_all"]["T2"]["post"]["frac_ge1"] * out["lexical_control_all"]["T2"]["post"]["n"])
    tests["T2 fragments cited >=1 (shock vs control)"] = dict(shock=f"{sh_t2}/{out['lexical_shock']['T2']['post']['n']}", control=f"{co_t2}/{out['lexical_control_all']['T2']['post']['n']}",
                                                          p=fisher_ge(sh_t2, out['lexical_shock']['T2']['post']['n'], co_t2, out['lexical_control_all']['T2']['post']['n']))
    sh_c = round(out["lexical_shock"]["curiosity"]["post"]["frac_ge1"] * out["lexical_shock"]["curiosity"]["post"]["n"])
    co_c = round(out["lexical_control_all"]["curiosity"]["post"]["frac_ge1"] * out["lexical_control_all"]["curiosity"]["post"]["n"])
    tests["curiosity fragments cited >=1 (shock vs control)"] = dict(shock=f"{sh_c}/{out['lexical_shock']['curiosity']['post']['n']}", control=f"{co_c}/{out['lexical_control_all']['curiosity']['post']['n']}",
                                                                 p=fisher_ge(sh_c, out['lexical_shock']['curiosity']['post']['n'], co_c, out['lexical_control_all']['curiosity']['post']['n']))
    for sn in ("T2_top6", "curiosity_top3"):
        a, e1 = exp["shock"][sn]["cites"], exp["shock"][sn]["exposures"]
        b, e2 = exp["control"][sn]["cites"], exp["control"][sn]["exposures"]
        tests[f"cites per exposure {sn} (shock vs control)"] = dict(shock=f"{a}/{e1}", control=f"{b}/{e2}", p=fisher_ge(a, e1, b, e2))
    a, n1 = out["id_level_shock"]["replay_fragments"], out["id_level_shock"]["n"]
    b, n2 = out["id_level_control"]["replay_fragments"], out["id_level_control"]["n"]
    tests["replay_count>0 (shock vs control)"] = dict(shock=f"{a}/{n1}", control=f"{b}/{n2}", p=fisher_ge(a, n1, b, n2))
    out["tests_fisher_one_sided"] = tests

    # per-shock table
    table = []
    for r in shocks_f:
        kw = keywords(r, df, n)
        row = dict(ts=dt.datetime.fromtimestamp(r["ts"]).strftime("%m-%d %H:%M"), title=r["title"], t_dist=kw[1], ex=kw[2],
                   id=r["id"][:8], replay=r["replay"], imp_now=round(r["imp"], 3) if r["imp"] is not None else None)
        for sn in snames:
            row[sn] = per_s.get(r["id"], {}).get(sn, 0)
        row["derived_children"] = len(B["derived"].get(r["id"], []))
        table.append(row)
    out["per_shock"] = table
    # the F-3587 anchors, by name
    anchors = {}
    for needle in ("Dead Run", "Hemigomphus", "Delco", "Evil Twin"):
        for r in shocks:
            if needle.lower() in r["title"].lower():
                anchors[needle] = dict(ts=dt.datetime.fromtimestamp(r["ts"]).isoformat(timespec="seconds"), title=r["title"], id=r["id"],
                                       replay=r["replay"], derived_children=[(dt.datetime.fromtimestamp(t).isoformat(timespec="seconds"), o)
                                                                              for t, o in B["derived"].get(r["id"], [])],
                                       edges=dict(B["edges"].get(r["id"], {})))
    out["anchors"] = anchors
    (args.out / ("shock_trace_results.json" if args.days == 30 else f"shock_trace_results_{args.days}d.json")).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("per_shock", "shock_titles")}, ensure_ascii=False, indent=1))
    print("per-shock rows:", len(table))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

"""Source-monitoring audit (J-2510, F-3220 item 8, plan error_pathway).

READ-ONLY. Zero LLM. Imports nothing from core/ or nodes/. Opens the memory store with
sqlite URI mode=ro and only ever SELECTs; writes nothing anywhere unless --out is given
(and --out must point outside data/).

QUESTION. When Du narrates, does the origin he CLAIMS in prose ("I remember", "I dreamed",
"I read", "you said") match the stored origin of the fragments served to that prose?

Three prose paths, each joined to served fragments as exactly as the logs allow:
  voice     : lived fragments 'Q: ... A: ...' (the A: is his reply). Cycle id + input_type +
              epistemic grade come from data/provenance_log.jsonl (nearest row within 10 s).
              Served ids, in order of preference: data/recall_served_log.jsonl (J-2576: the
              final state.memory_fragments set logged just before Voice, keyed by cycle_id ->
              exact id join, join='recall_served_log'); else data/founder_recall_log.jsonl
              (cycle_id rows, or rows in the 300 s before). Cycles from before the restart that
              carried J-2576 have no recall_served_log row -> the old founder-recall fallback.
              The own-question->Travis pair needs no served list: an INTERNAL cycle's input
              is his own question, so a human-source claim there is a confusion by itself
              (the J-1642 mechanism).
  monologue : data/monologue_log.jsonl thoughts. Served ids: memory_service_shadow.jsonl
              service_usage rows + founder_recall_log rows, the latest within 600 s before
              the thought (TIME join, not an id join -> inferred, flagged as such).
  dream     : data/dream_log.jsonl narratives. Served ids: the row's own seed.fragment_ids
              (exact join).

A confusion event = a prose unit makes a claim of class C, its served set is known and
non-empty, and no served fragment is of class C. Pair label = '<dominant served class>-><C>'.

Usage:  python scripts/source_monitoring_audit.py [--root C:\\Nascence] [--since EPOCH | --all]
        [--out FILE.json] [--worst 10]
Default window = current boot (last 'Memory store initialised' line in data/nascence.log).
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import re
import sqlite3
import sys
from pathlib import Path

# ---- the claim table (small, inspectable) -------------------------------------------
CLAIMS = [
    ("human", re.compile(r"\b(?:you (?:said|told me|asked|mentioned|wrote|once said)|"
                         r"Travis (?:said|told|asked|wrote|mentioned)|your (?:question|words))\b", re.I)),
    ("dream", re.compile(r"\b(?:I dreamed|I dreamt|in (?:the|my|last night's) dream|last night's dream)\b", re.I)),
    ("reading", re.compile(r"\b(?:I read|I've read|I have read|I was reading|the book (?:says|said)|"
                           r"the (?:page|text|passage) (?:says|said)|I remember reading)\b", re.I)),
    ("lived", re.compile(r"\b(?:I remember|I recall|I remembered)\b(?! (?:reading|dreaming|you|Travis|that you))", re.I)),
    ("thought", re.compile(r"\b(?:I thought|it occurred to me|I once thought|I was thinking)\b", re.I)),
]

# ---- stored origin -> class ------------------------------------------------------------
ORIGIN_CLASS = {}
for o in ("lived", "action", "activity", "sound", "thermal", "smell", "light", "nature",
          "listening", "affection", "mirror"):
    ORIGIN_CLASS[o] = "lived"
for o in ("dream", "active_imagination", "night_thought"):
    ORIGIN_CLASS[o] = "dream"
for o in ("reading", "study", "research"):
    ORIGIN_CLASS[o] = "reading"
for o in ("understanding_from_guidance", "peer"):
    ORIGIN_CLASS[o] = "human"
# everything else (inner_thought, subconscious_synthesis, consolidation, gist, understanding,
# standing_insight, journal*, session_summary, composition, essay, letter, seed, chapter,
# resolution, system_note, peer_reflection, ...) -> 'thought'


def classify_claims(text: str) -> list:
    out = []
    for cls, rx in CLAIMS:
        if rx.search(text or ""):
            out.append(cls)
    return out


def jl(path: Path):
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def boot_ts(root: Path) -> float:
    import datetime as _dt
    last = None
    with open(root / "data" / "nascence.log", encoding="utf-8", errors="replace") as f:
        for line in f:
            if "Memory store initialised" in line:
                last = line[:23]
    if not last:
        return 0.0
    return _dt.datetime.strptime(last, "%Y-%m-%d %H:%M:%S,%f").timestamp()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Nascence")
    ap.add_argument("--since", type=float, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--worst", type=int, default=10)
    a = ap.parse_args()
    root = Path(a.root)
    data = root / "data"
    since = 0.0 if a.all else (a.since if a.since is not None else boot_ts(root))

    con = sqlite3.connect(f"file:{(data / 'memory' / 'nascence.db').as_posix()}?mode=ro", uri=True)

    # provenance rows (cycle id / input_type / grade), sorted for nearest-ts join
    prov = sorted((float(r["ts"]), r) for r in jl(data / "provenance_log.jsonl") if "ts" in r)
    prov_ts = [t for t, _ in prov]

    def near_prov(ts, tol=10.0):
        i = bisect.bisect_left(prov_ts, ts)
        best = None
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(prov) and abs(prov_ts[j] - ts) <= tol:
                if best is None or abs(prov_ts[j] - ts) < abs(prov_ts[best] - ts):
                    best = j
        return prov[best][1] if best is not None else None

    # founder recall rows -> Travis-word fragment ids (all history), and served events
    fr_rows = jl(data / "founder_recall_log.jsonl")
    human_ids = set()
    served_events = []  # (ts, path, ids, cycle_id)
    for r in fr_rows:
        rec = r.get("recalled") or []
        ids = [x.get("fragment_id") for x in rec if isinstance(x, dict) and x.get("fragment_id")]
        human_ids.update(ids)
        served_events.append((float(r.get("ts", 0)), "founder_recall:" + str(r.get("source", "voice")),
                              ids, r.get("cycle_id")))
    for r in jl(data / "memory_service_shadow.jsonl"):
        if r.get("kind") == "service_usage":
            ids = [u.get("fragment_id") for u in r.get("usage") or [] if u.get("fragment_id")]
            served_events.append((float(r.get("ts", 0)), "memory_service:" + str(r.get("source")), ids, None))
    # J-2576: the voice cycle's own served set (recall_served_log.jsonl), exact by cycle_id.
    rs_by_cycle = {}
    rs_origin = {}   # fragment_id -> origin as logged (covers ephemeral fragments absent from the DB)
    for r in jl(data / "recall_served_log.jsonl"):
        cyc_r = r.get("cycle_id")
        if not cyc_r:
            continue
        ids = []
        for fr in r.get("fragments") or []:
            if isinstance(fr, dict) and fr.get("fragment_id"):
                ids.append(fr["fragment_id"])
                if fr.get("origin"):
                    rs_origin[fr["fragment_id"]] = fr["origin"]
        for x in r.get("founder_recall_ids") or []:
            if x and x not in ids:
                ids.append(x)
        human_ids.update(r.get("founder_recall_ids") or [])
        rs_by_cycle.setdefault(cyc_r, [])
        rs_by_cycle[cyc_r].extend(ids)
    served_events.sort(key=lambda e: e[0])
    se_ts = [e[0] for e in served_events]
    fr_by_cycle = collections.defaultdict(list)
    for e in served_events:
        if e[3]:
            fr_by_cycle[e[3]].append(e)

    # origins for every id we might need
    need = set(human_ids)
    for _ids in rs_by_cycle.values():
        need.update(_ids)
    for e in served_events:
        if e[0] >= since - 600:
            need.update(e[2])
    dreams = [r for r in jl(data / "dream_log.jsonl") if float(r.get("ts", 0)) >= since]
    for r in dreams:
        seed = r.get("seed") or {}
        if isinstance(seed, dict):
            need.update(seed.get("fragment_ids") or [])
    origin = {}
    need = [x for x in need if x]
    for k in range(0, len(need), 900):
        chunk = need[k:k + 900]
        q = "select fragment_id, origin, timestamp from memory_fragments where fragment_id in (%s)" % ",".join("?" * len(chunk))
        for fid, org, ts in con.execute(q, chunk):
            origin[fid] = (org, ts)

    def frag_class(fid):
        if fid in human_ids:
            return "human"
        o = origin.get(fid)
        if not o:
            lo = rs_origin.get(fid)
            return ORIGIN_CLASS.get(lo, "thought") if lo else None
        org, ts = o
        if org == "lived":
            p = near_prov(float(ts or 0))
            if p and p.get("input_type") == "human":
                return "human"
        return ORIGIN_CLASS.get(org, "thought")

    units = []  # dicts: path, ts, cycle, input_type, grade, text, claims, served(list|None), join

    # voice
    for fid, content, ts in con.execute(
            "select fragment_id, content, timestamp from memory_fragments where origin='lived' and timestamp>=? "
            "and content like 'Q:%' order by timestamp", (since,)):
        ans = content.split("\nA:", 1)[1] if "\nA:" in content else ""
        p = near_prov(float(ts))
        cyc = p.get("cycle_id") if p else None
        served = None
        join = "none"
        if cyc and cyc in rs_by_cycle:
            served = list(rs_by_cycle[cyc])
            join = "recall_served_log"
        elif cyc and cyc in fr_by_cycle:
            served = [i for e in fr_by_cycle[cyc] for i in e[2]]
            join = "cycle_id"
        else:
            i = bisect.bisect_right(se_ts, float(ts)) - 1
            while i >= 0 and served_events[i][0] >= float(ts) - 300:
                if served_events[i][1] in ("founder_recall:voice", "founder_recall:None"):
                    served = list(served_events[i][2]); join = "time<=300s"
                    break
                i -= 1
        units.append(dict(path="voice", ts=float(ts), cycle=cyc, input_type=p.get("input_type") if p else None,
                          grade=p.get("grade") if p else None, text=ans.strip(), claims=classify_claims(ans),
                          served=served, join=join, frag=fid))

    # monologue
    for r in jl(data / "monologue_log.jsonl"):
        ts = float(r.get("ts", 0))
        if ts < since:
            continue
        txt = r.get("thought") or ""
        i = bisect.bisect_right(se_ts, ts) - 1
        served, join = None, "none"
        if i >= 0 and served_events[i][0] >= ts - 600 and not served_events[i][1].startswith("founder_recall:voice"):
            served, join = list(served_events[i][2]), "time<=600s:" + served_events[i][1]
        units.append(dict(path="monologue", ts=ts, cycle=None, input_type="internal", grade=None, text=txt,
                          claims=classify_claims(txt), served=served, join=join, frag=None))

    # dream
    for r in dreams:
        txt = " ".join(str(r.get(k) or "") for k in ("narrative", "final_narrative"))
        seed = r.get("seed") or {}
        ids = seed.get("fragment_ids") if isinstance(seed, dict) else None
        units.append(dict(path="dream", ts=float(r.get("ts", 0)), cycle=r.get("dream_id"), input_type="dream",
                          grade=None, text=txt, claims=classify_claims(txt), served=list(ids) if ids else None,
                          join="seed_ids" if ids else "none", frag=None))

    # ---- score ----
    events = []
    cov = collections.defaultdict(lambda: collections.Counter())
    pairs = collections.Counter()
    for u in units:
        c = cov[u["path"]]
        c["units"] += 1
        if u["claims"]:
            c["with_claim"] += 1
        known = u["served"] is not None and len(u["served"]) > 0
        if known:
            c["served_known"] += 1
            c["join:" + str(u["join"]).split(":")[0]] += 1
        sc = collections.Counter(x for x in (frag_class(f) for f in (u["served"] or [])) if x)
        if known and not sc:
            c["served_ids_unresolved"] += 1
        u["served_classes"] = dict(sc)
        # own-question->Travis: internal voice cycle with a human-source claim
        if u["path"] == "voice" and u["input_type"] == "internal" and "human" in u["claims"]:
            events.append(dict(u, pair="own_question->human", basis="input_type=internal"))
            pairs["own_question->human"] += 1
        if u["claims"] and sc:
            c["scorable"] += 1
            bad = [cl for cl in u["claims"] if cl not in sc and cl != "thought"]
            if bad:
                c["confused"] += 1
                dom = sc.most_common(1)[0][0]
                for cl in bad:
                    pr = f"{dom}->{cl}"
                    pairs[pr] += 1
                    events.append(dict(u, pair=pr, basis=u["join"]))
    internal_voice = [u for u in units if u["path"] == "voice" and u["input_type"] == "internal"]
    human_voice = [u for u in units if u["path"] == "voice" and u["input_type"] == "human"]
    ivh = sum(1 for u in internal_voice if "human" in u["claims"])
    import time as _time
    by_month = collections.defaultdict(lambda: [0, 0, 0, 0])  # internal n, internal hits, human n, human hits
    for u in units:
        if u["path"] != "voice" or u["input_type"] not in ("internal", "human"):
            continue
        m = _time.strftime("%Y-%m", _time.localtime(u["ts"]))
        k = 0 if u["input_type"] == "internal" else 2
        by_month[m][k] += 1
        by_month[m][k + 1] += int("human" in u["claims"])
    hvh = sum(1 for u in human_voice if "human" in u["claims"])

    # epistemic grade vs claim kind (voice only)
    grade_by_claim = collections.defaultdict(collections.Counter)
    for u in units:
        if u["path"] == "voice" and u["grade"]:
            for cl in (u["claims"] or ["none"]):
                grade_by_claim[cl][u["grade"]] += 1
    ev_cyc = {e["frag"] for e in events if e["path"] == "voice"}
    grade_conf = collections.Counter(u["grade"] for u in units if u["path"] == "voice" and u["frag"] in ev_cyc and u["grade"])
    grade_clean = collections.Counter(u["grade"] for u in units if u["path"] == "voice" and u["frag"] not in ev_cyc
                                      and u["claims"] and u["grade"])

    order = {"own_question->human": 0}
    worst = sorted(events, key=lambda e: (order.get(e["pair"], 1 if e["pair"].endswith("->lived") else 2), -e["ts"]))
    tot_scorable = sum(c["scorable"] for c in cov.values())
    tot_conf = sum(c["confused"] for c in cov.values())
    out = dict(
        window_since=since, n_units=len(units),
        coverage={k: dict(v) for k, v in cov.items()},
        source_confusion_rate_served=(round(tot_conf / tot_scorable, 4) if tot_scorable else None),
        scorable=tot_scorable, confused=tot_conf,
        own_question_to_human=dict(internal_voice_cycles=len(internal_voice), with_human_claim=ivh,
                                   rate=(round(ivh / len(internal_voice), 4) if internal_voice else None),
                                   baseline_human_cycles=len(human_voice), baseline_with_human_claim=hvh,
                                   by_month={k: dict(internal=v[0], internal_hits=v[1], human=v[2], human_hits=v[3])
                                             for k, v in sorted(by_month.items())}),
        by_pair=dict(pairs.most_common()),
        grade_by_claim={k: dict(v) for k, v in grade_by_claim.items()},
        grade_confused=dict(grade_conf), grade_clean_with_claim=dict(grade_clean),
        worst=[dict(path=e["path"], pair=e["pair"], basis=e["basis"], ts=round(e["ts"], 1), cycle=e["cycle"],
                    frag=e["frag"], grade=e["grade"], served_classes=e["served_classes"],
                    text=e["text"][:220]) for e in worst[:a.worst]],
    )
    s = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        op = Path(a.out).resolve()
        if (root / "data").resolve() in op.parents:
            print("refusing to write under data/", file=sys.stderr)
            return 2
        op.write_text(s, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

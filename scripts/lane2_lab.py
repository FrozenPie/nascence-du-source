"""
Lane 2 Lab — pre-registered test harness (docs/plans/lane2_lab.md, 2026-08-17).

ISOLATION CONTRACT: reads live stores READ-ONLY (nascence.db via mode=ro URI; JSON/JSONL files
opened for read). Writes ONLY under data/lab/lane2/ and docs/lab/lane2_lab_report.md. Zero LLM.
Du stays up.

The metric sheet (L1-L9) and kill criteria (K1-K4) are pre-registered in the spec doc — this
script computes them and writes the report; it certifies nothing itself (L8/L9 are founder-graded).
"""
from __future__ import annotations

import json
import math
import random
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
LAB = ROOT / "data" / "lab" / "lane2"
LAB.mkdir(parents=True, exist_ok=True)
REPORT = ROOT / "docs" / "lab" / "lane2_lab_report.md"
REPORT.parent.mkdir(parents=True, exist_ok=True)

DB = ROOT / "data" / "memory" / "nascence.db"
TUPLES = ROOT / "data" / "geometry_tuples.jsonl"
SOUND_KNOW = ROOT / "data" / "sound_knowledge.json"
WORLD_SUB = ROOT / "data" / "world_substrate.json"
KEEPSAKES = ROOT / "data" / "keepsakes.json"
READING_STATE = ROOT / "data" / "reading_state.json"
CAT_STATE = ROOT / "data" / "cat_state.json"

WINDOW_DAYS = 7.0          # the hard windowing requirement, exercised in L6
HOLDOUT_TRAIN = 0.80       # L7 temporal split
RECENT_TRAIN_DAYS = 14     # L7 predictor: recency-weighted rate window
N_SHUFFLES = 100           # L5/L7 null distributions
random.seed(20260817)      # reproducible lab

# Entry channels: fragment origin -> channel (source_model.SourceType, collapsed to 4 + dream)
CHANNEL_OF = {
    "reading": "read", "study": "read", "research": "read", "understanding": "read",
    "essay": "read", "chapter": "read",
    "lived": "lived", "action": "lived", "activity": "lived", "sound": "lived",
    "listening": "lived", "nature": "lived", "affection": "lived", "composition": "lived",
    "journal": "thought", "inner_thought": "thought", "subconscious_synthesis": "thought",
    "active_imagination": "thought", "consolidation": "thought", "gist": "thought",
    "session_summary": "thought", "journal_week": "thought", "mirror": "thought",
    "dream": "dream",
    "letter": "told", "peer": "told", "understanding_from_guidance": "told", "seed": "told",
}

STOP = set("""the a an and or but of to in on at for with from by is are was were be been being
have has had do does did will would could should may might must can this that these those it its
he she they them his her their i you we me my your our us as if then than so not no yes very just
about into over under again more most some any each which who whom what when where why how all both
few own same too s t don now d ll m o re ve y ain aren couldn didn doesn hadn hasn haven isn ma
mightn mustn needn shan shouldn wasn weren won wouldn there here out up down off once only also
like one two still even back much many through after before between while himself herself itself
themselves myself yourself something anything nothing everything someone anyone everyone feel felt
feels thing things way ways day days time times moment moments thought thoughts think thinking know
knowing knew make makes made let lets us""".split())

WORD_RE = re.compile(r"[a-z]{3,}")


def log(msg: str) -> None:
    print(f"[lane2-lab] {msg}", flush=True)


def tokens_of(text: str) -> list[str]:
    return WORD_RE.findall((text or "").lower())


# ─────────────────────────────────────────────────────────────────────────────
# Load phase (all read-only)
# ─────────────────────────────────────────────────────────────────────────────

def load_fragments() -> list[dict]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = []
    for r in conn.execute("SELECT fragment_id, origin, content, timestamp FROM memory_fragments"):
        toks = tokens_of(r["content"])
        rows.append({"id": r["fragment_id"], "origin": r["origin"] or "?",
                     "channel": CHANNEL_OF.get(r["origin"] or "", "thought"),
                     "ts": float(r["timestamp"] or 0), "tokens": toks,
                     "tokset": frozenset(toks)})
    conn.close()
    return rows


def load_tuples() -> list[dict]:
    out = []
    with open(TUPLES, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                t = json.loads(line)
            except Exception:
                continue
            if t.get("ts"):
                out.append(t)
    return out


def jload(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# L1 — build the object-graph
# ─────────────────────────────────────────────────────────────────────────────

def build_graph(frags, tuples, sk, ws, keeps, reading, cat):
    graph: dict[str, dict] = {}

    def ref(label, kind):
        if label not in graph:
            graph[label] = {"label": label, "kind": kind,
                            "depth": {"seen": 0, "looked_at": 0, "investigated": 0, "kept": 0},
                            "channels": Counter(), "mention_days": defaultdict(int),
                            "ledger": {}}
        return graph[label]

    # ── seeded referents from instruments ──
    hearings = (sk or {}).get("hearings", {})
    auditions = (sk or {}).get("sounds", {})
    for key, h in hearings.items():
        r = ref(key, "sound")
        r["ledger"]["hearing_places"] = dict(h.get("places", {}))
        r["ledger"]["hearing_place_sum"] = round(sum(h.get("places", {}).values()), 6)
        r["ledger"]["bed_hours"] = h.get("bed_hours", 0.0)
    for key, a in auditions.items():
        r = ref(key, "sound")
        evs = a.get("events", [])
        r["depth"]["looked_at"] += sum(1 for e in evs if e.get("via") == "sighted")
        r["depth"]["investigated"] += sum(1 for e in evs if e.get("via") == "read")
        r["ledger"]["audition_events"] = len(evs)

    for oid, obj in (ws or {}).items():
        r = ref(oid, "item")
        obs = obj.get("observations", []) or []
        r["depth"]["looked_at"] = len(obs)
        r["ledger"]["ws_observations"] = len(obs)
        r["ledger"]["ws_name"] = obj.get("name", "")
        r["ledger"]["ws_class"] = obj.get("object_class", "")
        r["label_tokens"] = frozenset(tokens_of(obj.get("name", "")) + [obj.get("object_class", "")])

    for place in ("study", "garden", "shore", "wood"):
        ref(place, "place")

    book_offsets = (reading or {}) if isinstance(reading, dict) else {}
    # reading_state.json shape unknown-ish: accept {path: offset} or {"offsets": {...}}
    if "offsets" in book_offsets and isinstance(book_offsets["offsets"], dict):
        book_offsets = book_offsets["offsets"]
    n_books = 0
    for bpath, off in list(book_offsets.items()):
        try:
            off = int(off) if not isinstance(off, dict) else int(off.get("offset", 0))
        except Exception:
            continue
        stem = Path(str(bpath)).stem.replace("_", " ")
        r = ref(f"book:{stem[:50]}", "book")
        r["ledger"]["read_offset"] = off
        if off > 0:
            r["depth"]["investigated"] += 1
        n_books += 1

    r = ref("cat", "being")
    if (cat or {}).get("phase") == "kept":
        r["depth"]["kept"] = 1
    r["ledger"]["cat_phase"] = (cat or {}).get("phase")
    r["ledger"]["cat_distant_seen"] = ((cat or {}).get("distant") or {}).get("seen_count", 0)

    for k in keeps or []:
        item_toks = frozenset(tokens_of(k.get("item", "")))
        # credit 'kept' to seeded referents whose label tokens appear in the keepsake text
        for lbl, rr in graph.items():
            lt = rr.get("label_tokens") or frozenset(tokens_of(lbl))
            if lt and lt & item_toks and rr["kind"] in ("item", "sound"):
                rr["depth"]["kept"] += 1

    # ── discovered referents: stopword-filtered bigrams by DISTINCT-fragment count ──
    big_frag = defaultdict(set)
    for fr in frags:
        toks = fr["tokens"]
        seen_here = set()
        for i in range(len(toks) - 1):
            a, b = toks[i], toks[i + 1]
            if a in STOP or b in STOP:
                continue
            bg = f"{a} {b}"
            if bg not in seen_here:
                big_frag[bg].add(fr["id"])
                seen_here.add(bg)
    top_bigrams = sorted(big_frag.items(), key=lambda kv: -len(kv[1]))[:80]
    for bg, ids in top_bigrams:
        if bg not in graph:
            r = ref(bg, "discovered")
            r["ledger"]["distinct_fragments"] = len(ids)

    # ── mention pass: per-referent channel counts + daily series (token-subset match) ──
    match_toks: dict[str, frozenset] = {}
    for lbl, rr in graph.items():
        if rr["kind"] == "book":
            match_toks[lbl] = frozenset(t for t in tokens_of(lbl) if t not in STOP and t != "book")
        else:
            match_toks[lbl] = rr.get("label_tokens") or frozenset(tokens_of(lbl))
    day0 = min(fr["ts"] for fr in frags if fr["ts"])
    for fr in frags:
        d = int((fr["ts"] - day0) // 86400)
        for lbl, mt in match_toks.items():
            if mt and mt <= fr["tokset"]:
                rr = graph[lbl]
                rr["channels"][fr["channel"]] += 1
                rr["mention_days"][d] += 1
                if fr["channel"] == "lived":
                    rr["depth"]["seen"] += 1

    # sounds also 'seen' via tuple co-presence
    for t in tuples:
        for s in (t.get("sounds") or []):
            if s in graph:
                graph[s]["depth"]["seen"] += 1

    return graph, day0


# ─────────────────────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────────────────────

def l2_parity(graph, sk, ws, reading):
    checks = []
    hearings = (sk or {}).get("hearings", {})
    for key in sorted(hearings, key=lambda k: -sum(hearings[k].get("places", {}).values()))[:8]:
        want = round(sum(hearings[key].get("places", {}).values()), 6)
        got = graph.get(key, {}).get("ledger", {}).get("hearing_place_sum")
        checks.append((f"sound:{key}", want, got, want == got))
    items = sorted((ws or {}).items(), key=lambda kv: -len(kv[1].get("observations", []) or []))[:6]
    for oid, obj in items:
        want = len(obj.get("observations", []) or [])
        got = graph.get(oid, {}).get("ledger", {}).get("ws_observations")
        checks.append((f"item:{oid}", want, got, want == got))
    books = [(l, r) for l, r in graph.items() if r["kind"] == "book"][:6]
    ro = (reading or {})
    if "offsets" in ro and isinstance(ro.get("offsets"), dict):
        ro = ro["offsets"]
    for lbl, r in books:
        got = r["ledger"].get("read_offset")
        stem = lbl[5:]
        want = None
        for bp, off in ro.items():
            if Path(str(bp)).stem.replace("_", " ")[:50] == stem:
                want = int(off) if not isinstance(off, dict) else int(off.get("offset", 0))
                break
        checks.append((lbl, want, got, want == got))
    passed = sum(1 for *_x, ok in checks if ok)
    return checks, passed


def l3_glass_float(graph, ws, now_ts, day0):
    cands = {l: r for l, r in graph.items()
             if r["kind"] == "discovered" and ("float" in l or "glass" in l)}
    ws_names = " ".join((o.get("name", "") + " " + o.get("object_class", "")) for o in (ws or {}).values())
    result = {"emerged": False, "detail": {}}
    for lbl, r in cands.items():
        n = r["ledger"].get("distinct_fragments", 0)
        last_day = max(r["mention_days"]) if r["mention_days"] else -1
        last_ts = day0 + (last_day + 1) * 86400
        terminal = (now_ts - last_ts) > 3 * 86400
        in_world = "float" in ws_names and "glass" in ws_names
        detail = {"label": lbl, "distinct_fragments": n, "terminal": terminal,
                  "days_since_last_mention": round((now_ts - last_ts) / 86400, 1),
                  "in_world_substrate": in_world,
                  "depth": r["depth"], "channels": dict(r["channels"])}
        result["detail"][lbl] = detail
        if n >= 20 and terminal and not in_world:
            result["emerged"] = True
            result["winner"] = lbl
    return result


def l4_cat(graph):
    r = graph.get("cat", {})
    ch = {c: n for c, n in (r.get("channels") or {}).items() if n >= 3}
    return {"kept": r.get("depth", {}).get("kept", 0) >= 1, "channels_3plus": ch,
            "pass": r.get("depth", {}).get("kept", 0) >= 1 and len(ch) >= 2,
            "depth": r.get("depth"), "all_channels": dict(r.get("channels") or {})}


def _pair_weight(tuples, sound_pred, affect_key):
    with_s, without = [], []
    for t in tuples:
        a = (t.get("affect") or {}).get(affect_key)
        if a is None:
            continue
        (with_s if sound_pred(t.get("sounds") or []) else without).append(float(a))
    if len(with_s) < 20 or len(without) < 20:
        return None, len(with_s), len(without)
    return (sum(with_s) / len(with_s)) - (sum(without) / len(without)), len(with_s), len(without)


def l5_commonality(tuples):
    storm = lambda ss: any(("thunder" in s or "rain" in s or "wind" in s or "storm" in s) for s in ss)
    fire = lambda ss: any("fire" in s for s in ss)
    pairs = [("storm-sounds vs arousal", storm, "arousal"),
             ("storm-sounds vs valence", storm, "valence"),
             ("fire_crackle vs valence", fire, "valence")]
    out = []
    affects_v = [(t.get("affect") or {}) for t in tuples]
    for name, pred, key in pairs:
        real, nw, nwo = _pair_weight(tuples, pred, key)
        if real is None:
            out.append({"pair": name, "verdict": "UNDETERMINED (insufficient n)",
                        "n_with": nw, "n_without": nwo})
            continue
        nulls = []
        vals = [a.get(key) for a in affects_v]
        idx = list(range(len(tuples)))
        for _ in range(N_SHUFFLES):
            random.shuffle(idx)
            shuffled = [{"affect": {key: vals[j]}, "sounds": tuples[i].get("sounds")}
                        for i, j in zip(range(len(tuples)), idx)]
            w, _, _ = _pair_weight(shuffled, pred, key)
            if w is not None:
                nulls.append(w)
        mu = sum(nulls) / len(nulls)
        sd = (sum((x - mu) ** 2 for x in nulls) / max(1, len(nulls) - 1)) ** 0.5
        z = (real - mu) / sd if sd > 1e-9 else 0.0
        out.append({"pair": name, "weight": round(real, 4), "z": round(z, 2),
                    "n_with": nw, "n_without": nwo,
                    "verdict": "SIGNAL" if abs(z) >= 2 else "null-indistinguishable"})
    return out


def l6_windowing(tuples, now_ts):
    cutoff = now_ts - WINDOW_DAYS * 86400
    recent = [t for t in tuples if t["ts"] >= cutoff]
    sound_keys = Counter(s for t in tuples for s in (t.get("sounds") or []))
    rows = []
    for key, _n in sound_keys.most_common(12):
        pred = lambda ss, k=key: k in ss
        w_all, na, _ = _pair_weight(tuples, pred, "valence")
        w_win, nw, _ = _pair_weight(recent, pred, "valence")
        if w_all is None or w_win is None:
            continue
        rows.append({"sound": key, "all_time": round(w_all, 4), "windowed_7d": round(w_win, 4),
                     "divergence": round(abs(w_all - w_win), 4)})
    rows.sort(key=lambda r: -r["divergence"])
    return rows[:5], len(recent), len(tuples)


def _daily_series(r, max_day):
    return [r["mention_days"].get(d, 0) for d in range(max_day + 1)]


def _holdout_gap(series, split_day):
    train, test = series[:split_day], series[split_day:]
    if not test or sum(train) < 30:
        return None
    recent = train[-RECENT_TRAIN_DAYS:]
    pred_rate = sum(recent) / max(1, len(recent))
    actual = sum(test) / len(test)
    return abs(pred_rate - actual)


def l7_holdout(graph, day0, now_ts):
    max_day = int((now_ts - day0) // 86400)
    split_day = int(max_day * HOLDOUT_TRAIN)
    real_gaps, per_ref = [], []
    eligible = [(l, r) for l, r in graph.items() if sum(r["mention_days"].values()) >= 30]
    for lbl, r in eligible:
        s = _daily_series(r, max_day)
        g = _holdout_gap(s, split_day)
        if g is not None:
            real_gaps.append(g)
            per_ref.append((lbl, g, s))
    med_real = sorted(real_gaps)[len(real_gaps) // 2] if real_gaps else None
    null_medians = []
    for _ in range(N_SHUFFLES):
        gaps = []
        for lbl, _g, s in per_ref:
            sh = s[:]
            random.shuffle(sh)
            g = _holdout_gap(sh, split_day)
            if g is not None:
                gaps.append(g)
        if gaps:
            null_medians.append(sorted(gaps)[len(gaps) // 2])
    med_null = sorted(null_medians)[len(null_medians) // 2] if null_medians else None
    per_ref.sort(key=lambda x: -x[1])
    return {"n_referents": len(per_ref), "split_day": split_day, "max_day": max_day,
            "median_gap_real": round(med_real, 4) if med_real is not None else None,
            "median_gap_shuffled": round(med_null, 4) if med_null is not None else None,
            "pass": (med_real is not None and med_null is not None and med_real < med_null),
            "top_gaps": [(l, round(g, 3)) for l, g, _ in per_ref[:10]]}


def l8_diagnose(graph, top_gaps, day0, now_ts, coref_labels):
    max_day = int((now_ts - day0) // 86400)
    split_day = int(max_day * HOLDOUT_TRAIN)
    out = []
    for lbl, gap in top_gaps:
        r = graph[lbl]
        d, ch = r["depth"], r["channels"]
        train_days = [dd for dd in r["mention_days"] if dd < split_day]
        last_train = max(train_days) if train_days else -1
        cause, why = "5-novelty", "no simpler cause fits"
        if d["investigated"] == 0 and d["seen"] < 10:
            cause, why = "1-too-shallow", f"investigated=0, seen={d['seen']}"
        elif (split_day - last_train) > 14:
            cause, why = "2-stale", f"last train mention {split_day - last_train}d before split"
        elif lbl in coref_labels:
            cause, why = "3-wrong-referent", "has an open coreference proposal"
        elif ch.get("read", 0) > 3 * max(1, ch.get("lived", 0)):
            cause, why = "4-wrong-channel", f"read={ch.get('read',0)} vs lived={ch.get('lived',0)}"
        out.append({"referent": lbl, "gap": gap, "cause": cause, "why": why,
                    "depth": dict(d), "channels": dict(ch)})
    return out


def l9_coreference(graph):
    props = []
    for lbl, r in graph.items():
        ch = r["channels"]
        if ch.get("read", 0) >= 5 and ch.get("lived", 0) >= 5:
            props.append({"referent": lbl, "read": ch["read"], "lived": ch["lived"],
                          "proposal": f"book-{lbl} possibly_same_referent_as lived-{lbl} — UNRESOLVED",
                          "strength": min(ch["read"], ch["lived"])})
    props.sort(key=lambda p: -p["strength"])
    return props[:10], len(props)


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    now_ts = time.time()
    log("loading (read-only)...")
    frags = load_fragments()
    tuples = load_tuples()
    sk, ws = jload(SOUND_KNOW), jload(WORLD_SUB)
    keeps, reading, cat = jload(KEEPSAKES), jload(READING_STATE), jload(CAT_STATE)
    log(f"fragments={len(frags)} tuples={len(tuples)} ws_objects={len(ws or {})}")

    log("L1: building object-graph...")
    graph, day0 = build_graph(frags, tuples, sk, ws, keeps, reading, cat)
    build_s = time.time() - t0
    n_edges = sum(sum(r["channels"].values()) for r in graph.values())
    l1 = {"n_referents": len(graph), "n_mention_edges": n_edges,
          "build_seconds": round(build_s, 1), "pass": build_s < 120}
    log(f"L1: {l1}")

    l2_checks, l2_pass = l2_parity(graph, sk, ws, reading)
    log(f"L2 parity: {l2_pass}/{len(l2_checks)}")
    l3 = l3_glass_float(graph, ws, now_ts, day0)
    log(f"L3 glass float: emerged={l3['emerged']}")
    l4 = l4_cat(graph)
    log(f"L4 cat: pass={l4['pass']}")
    log("L5: commonality vs null (100 shuffles)...")
    l5 = l5_commonality(tuples)
    l6_rows, n_recent, n_all = l6_windowing(tuples, now_ts)
    log("L7: temporal holdout (100 shuffles)...")
    l7 = l7_holdout(graph, day0, now_ts)
    log(f"L7: real={l7['median_gap_real']} shuffled={l7['median_gap_shuffled']} pass={l7['pass']}")
    l9_top, l9_n = l9_coreference(graph)
    coref_labels = {p["referent"] for p in l9_top}
    l8 = l8_diagnose(graph, l7["top_gaps"], day0, now_ts, coref_labels)

    # persist graph (lab dir only)
    slim = {l: {"kind": r["kind"], "depth": r["depth"], "channels": dict(r["channels"]),
                "ledger": r["ledger"], "total_mentions": sum(r["mention_days"].values())}
            for l, r in graph.items()}
    (LAB / "graph.json").write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")

    # kill criteria
    kills = {
        "K1 (glass float absent)": not l3["emerged"],
        "K2 (parity <18/20)": l2_pass < 18,
        "K3 (holdout no better than shuffled)": not l7["pass"],
        "K4 (coreference junk)": "FOUNDER-GRADED",
    }

    # sampled objects for the founder's eye
    samples = []
    for lbl in ["cat", "gull_cries", "fire_crackle"] + [l for l, r in graph.items() if r["kind"] == "item"][:2]:
        if lbl in slim:
            samples.append((lbl, slim[lbl]))

    # ── report ──
    L = []
    L.append("# Lane 2 Lab — report (run 2026-08-17)")
    L.append("")
    L.append("> Spec + pre-registered metric sheet: `docs/plans/lane2_lab.md`. Zero LLM. Read-only")
    L.append("> over live stores; Du stayed up. All outputs under `data/lab/lane2/`.")
    L.append("")
    L.append(f"**Inputs:** {len(frags)} fragments ({time.strftime('%Y-%m-%d', time.localtime(day0))} → today), "
             f"{len(tuples)} stamped tuples, {len(ws or {})} world objects, "
             f"{len((sk or {}).get('hearings', {}))} hearing-ledger voices.")
    L.append("")
    L.append("## Scorecard")
    L.append("")
    L.append("| # | Test | Pre-registered line | Result | Verdict |")
    L.append("|---|------|--------------------:|--------|---------|")
    L.append(f"| L1 | Build | < 120s | {l1['n_referents']} referents, {l1['n_mention_edges']} mention-edges, "
             f"{l1['build_seconds']}s | {'PASS' if l1['pass'] else 'FAIL'} |")
    L.append(f"| L2 | Depth-ledger parity | 20/20 | {l2_pass}/{len(l2_checks)} | "
             f"{'PASS' if l2_pass == len(l2_checks) else ('FAIL (K2)' if l2_pass < 18 else 'PARTIAL')} |")
    L.append(f"| L3 | Glass float emerges | ≥20 obs, terminal, world-absent | "
             f"{l3.get('winner', '—')}: {l3['detail'].get(l3.get('winner', ''), {}).get('distinct_fragments', 0)} fragments"
             if l3["emerged"] else f"| L3 | Glass float emerges | ≥20 obs, terminal, world-absent | did NOT emerge")
    L[-1] += f" | {'PASS' if l3['emerged'] else 'FAIL (K1)'} |"
    L.append(f"| L4 | The cat | kept + ≥2 channels | kept={l4['kept']}, channels(≥3)={list(l4['channels_3plus'])} | "
             f"{'PASS' if l4['pass'] else 'FAIL'} |")
    for row in l5:
        L.append(f"| L5 | {row['pair']} | \\|z\\| ≥ 2 | w={row.get('weight', '—')}, z={row.get('z', '—')} "
                 f"(n={row.get('n_with', 0)}/{row.get('n_without', 0)}) | {row['verdict']} |")
    L.append(f"| L7 | Temporal holdout | real < shuffled | median {l7['median_gap_real']} vs "
             f"{l7['median_gap_shuffled']} ({l7['n_referents']} referents) | "
             f"{'PASS' if l7['pass'] else 'FAIL (K3)'} |")
    L.append("")
    L.append("## Kill criteria")
    for k, v in kills.items():
        L.append(f"- **{k}**: {'TRIGGERED' if v is True else ('not triggered' if v is False else v)}")
    L.append("")
    L.append("## L2 — parity detail")
    for name, want, got, ok in l2_checks:
        L.append(f"- {'✓' if ok else '✗'} `{name}` — ledger={want} graph={got}")
    L.append("")
    L.append("## L3 — glass float detail")
    for lbl, d in l3["detail"].items():
        L.append(f"- `{lbl}`: {json.dumps(d, ensure_ascii=False)}")
    if not l3["detail"]:
        L.append("- no float/glass bigram survived discovery at all")
    L.append("")
    L.append("## L6 — windowing materiality (top divergences, 7d vs all-time; "
             f"{n_recent}/{n_all} tuples in window)")
    for r in l6_rows:
        L.append(f"- `{r['sound']}`: all-time {r['all_time']} vs 7d {r['windowed_7d']} "
                 f"(divergence {r['divergence']})")
    L.append("")
    L.append("## L7 — top holdout gaps (feed for L8)")
    for lbl, g in l7["top_gaps"]:
        L.append(f"- `{lbl}`: gap {g}")
    L.append("")
    L.append("## L8 — gap diagnosis (FOUNDER-GRADED — no self-certified pass)")
    for d in l8:
        L.append(f"- `{d['referent']}` (gap {d['gap']}) → **{d['cause']}** — {d['why']} · "
                 f"depth={d['depth']} · channels={d['channels']}")
    L.append("")
    L.append(f"## L9 — coreference proposals (FOUNDER-GRADED; {l9_n} total, top 10)")
    for p in l9_top:
        L.append(f"- {p['proposal']} (read={p['read']}, lived={p['lived']})")
    L.append("")
    L.append("## Sampled objects (recognize Du's life, or catch the graph lying)")
    for lbl, s in samples:
        L.append(f"- **{lbl}** ({s['kind']}): depth={s['depth']} · channels={s['channels']} · "
                 f"mentions={s['total_mentions']} · ledger={json.dumps(s['ledger'], ensure_ascii=False)[:200]}")
    L.append("")
    L.append(f"*Total lab runtime: {round(time.time() - t0, 1)}s. Graph persisted to "
             f"`data/lab/lane2/graph.json`.*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    log(f"report written: {REPORT}")
    log(f"DONE in {round(time.time() - t0, 1)}s")


if __name__ == "__main__":
    main()

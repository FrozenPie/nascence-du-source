"""J-3048 step 1: build the gold set for the tension-resolution judge (F-3750, P-0103).  READ-ONLY toward Du.

WHAT IT BUILDS (docs/lab/J-3048_data/):
  gold_pairs.jsonl   one row per pair, ALL metadata (source, panel verdict, sim). NOT shown to the labeller.
  blind_sheet.txt    what the labeller reads: id, TENSION label, THOUGHT, and the tension's 3 most recent member
                     shadow events (the conflict itself). Shuffled; no source, no panel verdict.
  (labels are written into gold_labels.json BEFORE any replay; the replay refuses to run without it)

TWO SOURCES
  closure  a tension the live matcher closed: resolved True, resolving_thought_id 'monologue' (data/tensions_archive.jsonl
           plus data/subconscious_state.json). The closing thought is the full light_events.integrated_content (the live
           judge saw thought[:600]; the tension record keeps only thought[:250]).
  refuted  a thought the panel REFUTED (verdict False) for a live tension. data/tension_judge_attempts.jsonl (J-3050) does
           not exist yet (Du has been down since it was added), and the thought text of a refused attempt was never stored
           anywhere. It is reconstructed by a JOIN: every key='resolves' row of data/judge_panel_log.jsonl carries
           context 'tension:<label[:40]>' and a timestamp; the monologue stores each resolving thought as a
           light_events row (source 'resolved_thought') 8-30 s BEFORE its ruling (median 12 s, measured below), so the
           ruling is joined to the latest resolved_thought event within JOIN_WINDOW seconds, and to the tension with that
           label whose stored centroid passes the matcher's own gate (cosine >= 0.70 against the event's stored embedding,
           plus the shared-token guard). A join that fails the gate is dropped, never guessed.
  FIDELITY GAP (stated): tension centroids are the FINAL stored ones (they drift as members are added), so a refuted pair's
  cosine here can differ a little from the cosine the live matcher saw; JOIN_SIM_FLOOR below allows for that and every kept
  pair is flagged with its recomputed sim.

Usage (from the worktree):  python scripts/j3048_tension_gold_build.py [--n-closure 60] [--n-refuted 60] [--seed 3048]
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LIVE = Path(r"C:\Nascence\data")
DB_URI = "file:C:/Nascence/data/memory/nascence.db?mode=ro&immutable=1"
OUT = ROOT / "docs" / "lab" / "J-3048_data"
JOIN_WINDOW = 180.0          # seconds a resolved_thought event may precede its ruling
JOIN_SIM_FLOOR = 0.62        # final-centroid drift allowance under the live 0.70 gate
STOP = {'and', 'the', 'of', 'in', 'to', 'a', 'is', 'that', 'for', 'it', 'with', 'as', 'was', 'on', 'at', 'by', 'an', 'be',
        'this', 'which', 'or', 'from', 'my', 'i', 'unresolved', 'thought', 'dream', 's', 't'}   # tension_ledger's own list


def _jl(path: Path) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def load_tensions() -> list:
    rows = _jl(LIVE / "tensions_archive.jsonl")
    seen = {r["id"] for r in rows}
    with open(LIVE / "subconscious_state.json", encoding="utf-8") as f:
        st = json.load(f).get("tensions", [])
    return rows + [t for t in st if t.get("id") not in seen]


def passes_gate(thought: str, about: str, label: str) -> bool:
    """tension_ledger.check_and_resolve_internal_tension's token guard, verbatim logic."""
    t_tokens = set(re.findall(r"\w+", label.lower()))
    a = set(re.findall(r"\w+", about.lower())) if about else set()
    th = set(re.findall(r"\w+", thought.lower()))
    return not (len((a & t_tokens) - STOP) == 0 and len((th & t_tokens) - STOP) < 2)


def about_of(raw_input: str) -> str:
    m = re.match(r"\(idle thought about: (.*)\)\s*$", raw_input or "", re.S)
    return m.group(1) if m else ""


def member_events(conn, tension: dict, before_ts: float, k: int = 3, chars: int = 200) -> list:
    """The tension's k most recent member shadow events at or before `before_ts` (what the live code could have shown)."""
    ids = tension.get("member_event_ids") or []
    if not ids:
        return []
    q = ",".join("?" * len(ids))
    rows = conn.execute(f"select event_id,timestamp,rejected_draft from shadow_events where event_id in ({q}) "
                        f"order by timestamp desc", ids).fetchall()
    rows = [r for r in rows if r[1] <= before_ts] or rows
    return [{"event_id": r[0], "ts": r[1], "text": (r[2] or "")[:chars]} for r in rows[:k]]


def load_light(conn) -> tuple:
    rows = conn.execute("select event_id,timestamp,raw_input,integrated_content,embedding from light_events "
                        "where source='resolved_thought' order by timestamp").fetchall()
    ts = np.array([r[1] for r in rows])
    return rows, ts


def vec(blob) -> "np.ndarray | None":
    if blob is None:
        return None
    v = np.frombuffer(blob, dtype=np.float32)
    return v if v.shape[0] == 384 else None


def build_closures(conn, tensions: list, light_rows: list, light_ts) -> list:
    out = []
    by_head = {}
    for r in light_rows:
        by_head.setdefault((r[3] or "")[:80], []).append(r)
    for t in tensions:
        if not (t.get("resolved") and t.get("resolving_thought_id") == "monologue" and t.get("resolution_thought")):
            continue
        head = t["resolution_thought"][:80]
        cands = [r for r in by_head.get(head, []) if abs(r[1] - float(t.get("resolved_ts") or 0)) < 900]
        full = cands[0] if cands else None
        thought = (full[3] if full else t["resolution_thought"])[:600]
        out.append({"source": "closure", "tension_id": t["id"], "label": t["label"], "count": t.get("count"),
                    "thought": thought, "thought_full_found": bool(full), "about": about_of(full[2]) if full else "",
                    "ts": float(t.get("resolved_ts") or 0), "sim": t.get("resolution_sim"),
                    "events": member_events(conn, t, float(t.get("resolved_ts") or 1e12)),
                    "panel": {"verdict": True, "how": "closure"}})
    return out


def build_refuted(conn, tensions: list, light_rows: list, light_ts) -> tuple:
    """Join judge_panel_log 'resolves' rulings to a (light event, tension). Returns (pairs, stats)."""
    pl = [r for r in _jl(LIVE / "judge_panel_log.jsonl") if r.get("key") == "resolves"]
    by_label = collections.defaultdict(list)
    for t in tensions:
        if t.get("label") and t.get("centroid") and len(t["centroid"]) == 384:
            by_label[t["label"][:40]].append(t)
    stats = collections.Counter()
    gaps = []
    out = []
    for p in pl:
        ctx = (p.get("context") or "")
        label40 = ctx[len("tension:"):] if ctx.startswith("tension:") else ""
        i = int(np.searchsorted(light_ts, p["ts"], side="right")) - 1
        if i < 0 or p["ts"] - light_ts[i] > JOIN_WINDOW:
            stats["no_event_in_window"] += 1
            continue
        gaps.append(p["ts"] - light_ts[i])
        ev = light_rows[i]
        ev_vec = vec(ev[4])
        best = None
        for t in by_label.get(label40, []):
            if ev_vec is None:
                break
            sim = float(np.dot(ev_vec, np.array(t["centroid"], dtype=np.float32)))
            if sim >= JOIN_SIM_FLOOR and passes_gate(ev[3], about_of(ev[2]), t["label"]) and (best is None or sim > best[0]):
                best = (sim, t)
        if best is None:
            stats["join_failed_gate"] += 1
            continue
        stats["joined"] += 1
        sim, t = best
        out.append({"source": "ruling", "tension_id": t["id"], "label": t["label"], "count": t.get("count"),
                    "thought": (ev[3] or "")[:600], "thought_full_found": True, "about": about_of(ev[2]),
                    "ts": p["ts"], "sim": round(sim, 4), "event_id": ev[0],
                    "events": member_events(conn, t, p["ts"]),
                    "panel": {"verdict": p.get("verdict"), "v1": p.get("v1"), "v2": p.get("v2"), "how": p.get("how")}})
    stats["rulings"] = len(pl)
    stats["gap_median_s"] = round(float(np.median(gaps)), 1) if gaps else None
    return out, stats


def pick_refuted(pairs: list, n: int, seed: int, cap_per_tension: int = 2) -> list:
    """REFUTED = panel verdict False. Stratified across tensions (cap per tension) so one chronic tension does not dominate."""
    pool = [p for p in pairs if p["panel"]["verdict"] is False]
    rnd = random.Random(seed)
    rnd.shuffle(pool)
    taken, per = [], collections.Counter()
    for p in pool:
        if per[p["tension_id"]] >= cap_per_tension:
            continue
        per[p["tension_id"]] += 1
        p = dict(p)
        p["source"] = "refuted"
        taken.append(p)
        if len(taken) == n:
            break
    return taken


def sample_closures(closures: list, n: int, seed: int) -> list:
    rnd = random.Random(seed)
    pool = [c for c in closures if c["thought_full_found"]] or closures
    rnd.shuffle(pool)
    return pool[:n]


def blind_text(r: dict) -> str:
    ev = "\n".join(f"  - {e['text']}" for e in r["events"]) or "  (no member events survive)"
    return (f"=== {r['gid']} ===\nTENSION: {r['label']}\nTHOUGHT: {r['thought']}\n"
            f"WHAT FORMED THE TENSION (its most recent member events):\n{ev}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-closure", type=int, default=60)
    ap.add_argument("--n-refuted", type=int, default=60)
    ap.add_argument("--seed", type=int, default=3048)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_URI, uri=True)
    tensions = load_tensions()
    light_rows, light_ts = load_light(conn)
    closures = build_closures(conn, tensions, light_rows, light_ts)
    rulings, stats = build_refuted(conn, tensions, light_rows, light_ts)
    print(f"tensions {len(tensions)}  closures {len(closures)} (full thought found {sum(c['thought_full_found'] for c in closures)})")
    print("ruling join:", dict(stats))
    vc = collections.Counter(str(p["panel"]["verdict"]) for p in rulings)
    print("joined rulings by panel verdict:", dict(vc))
    chosen = sample_closures(closures, a.n_closure, a.seed) + pick_refuted(rulings, a.n_refuted, a.seed + 1)
    random.Random(a.seed + 2).shuffle(chosen)
    for k, r in enumerate(chosen, 1):
        r["gid"] = f"T{k:03d}"
    with open(OUT / "gold_pairs.jsonl", "w", encoding="utf-8") as f:
        for r in chosen:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(OUT / "blind_sheet.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(blind_text(r) for r in chosen))
    print(f"wrote {len(chosen)} pairs: {collections.Counter(r['source'] for r in chosen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

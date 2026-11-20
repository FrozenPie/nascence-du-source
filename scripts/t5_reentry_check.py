"""T5 re-entry check (J-3330, D-0676 / J-3179 / F-3919..F-3924): a READ-ONLY monthly replay of the human-only
gate of the conversational T5 compile.

Question it answers: "if the conversational compile (subconscious _t5_compile) were fed only turns TRAVIS
wrote, read in full, and admitted under a 24-hour-separation / distinct-conversation gate, how many distinct
qualifying clusters would each month have produced?"  The founder re-opens the conversational compile only if
this reports >= 3 distinct qualifying clusters in a month (docs/plans/t5_procedural.md).

READ-ONLY by construction
  * data/memory/nascence.db is opened with mode=ro (+ PRAGMA query_only); the logs are read with open(..., "r").
  * It imports no core module that has an import-time side effect and calls no writer: only
    core.procedures._EVALUATIVE (a regex) and core.procedures.mark_landed (a pure function) are used, and both
    fall back to local copies if the import fails.
  * It writes nothing (no log, no state). --json-out is the only write and only when the caller names a path.
  * It starts no Du process, calls no model and no Ramses hub; the only "model" is the CPU embedder.

THE HUMAN-ONLY VIEW (the point of the job; every rule below comes from data, J-3179 / F-3921)
  1. Material = memory_fragments origin='lived' with a "Q:" line, and the Q is the FULL BLOCK: from the first
     line starting "Q:" to the next line starting "A:". (core/memory/store.py recent_lived_inputs keeps only the
     first line, so Travis's long messages, which open with the salutation line, embedded as "渡,"; F-3921.)
  2. "human channel" is NOT Travis. Each fragment is joined to data/affect_log.jsonl (timestamp within 3 s and
     the same question prefix) for input_type; only input_type == 'human' survives. Then, among those:
       - system-composed turns are EXCLUDED: the two old farewell templates ("it's time to bank the fire and
         rest" / "it's time to stop for a while") AND every wording in scripts/run_nascence.py
         _FAREWELL_VARIANTS (the D-0286 rotation, live since 2026-10-03; J-3179's two-template filter missed
         these), slash commands, anything shorter than 9 characters;
       - founder canon: orchestrator.py stores a protected "[Travis said to me] <text>" fragment (origin
         'lived') only when state.founder_canon is True (F-0796; backfilled for older turns). That persisted
         marker is matched to each human fragment (same text prefix, within 30 s). A human-channel turn that has
         NO marker is reported as "human, unmarked" and, by default, kept when it is not a template (the marker
         is missing for a handful of real Travis messages written between the 2026-08-30 and 2026-09-05
         deploys and one on 09-28); --strict-canon drops them instead.
  3. admissible24(): the plan's gate with the two process fixes: >= 3 members, the cluster spans >= 24 hours
     (a separation, not a calendar-day crossing; F-3924), members come from >= 2 distinct CONVERSATIONS
     (a conversation ends at a 'Session ended' session_summary fragment, i.e. a /quit, or after a 6 h silence;
     not a 30-minute gap), not an evaluation cluster, and >= 3 members LANDED (no correction on the next turn).
  4. Greedy seed clustering at cosine 0.70 (the largest cluster is the one the live compile would take), with
     the same multilingual MiniLM embedder; a cluster is "distinct" if its centroid is < 0.85 to every cluster
     already counted (the live dedupe against existing skills).
The replay sweeps the live T5 check every --step-hours (3) from --since (2026-08-22, the date of the plan's
gate), each sweep seeing the newest 120 view items of the previous 7 days.

--legacy reproduces the J-3179 configuration (first-line parse, calendar-day gate, 30-minute sources, only the
two old farewell templates excluded, first line > 8 chars) so the script can be checked against the review's
"2 clusters in 75 days"; the difference between --legacy and the default IS the effect of the fixes.

Run:  python scripts/t5_reentry_check.py            (monthly; reads C:\\Nascence\\data when the tree has no data/)
      python scripts/t5_reentry_check.py --legacy   (the J-3179 configuration, for the comparison)
"""
from __future__ import annotations

import argparse
import ast
import bisect
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))

# ---- gate constants: read from the live source so a retune there cannot silently diverge from this replay ----
_DEFAULTS = {"PROC_CLUSTER_SIM": 0.70, "PROC_DEDUP_SIM": 0.85, "PROC_MIN_RECURRENCE": 3, "T5_MIN_NEW_LIVED": 6}
WINDOW_DAYS = 7           # _t5_check: recent_lived_inputs(since_ts=now - 7 * 86400, limit=120)
WINDOW_LIMIT = 120
JOIN_S = 3.0              # fragment <-> affect_log row (J-3179 method)
CANON_S = 600.0           # fragment <-> "[Travis said to me]" canon fragment (J-3531: was 30 s; 9 of the 17 "unmarked" turns
                          # had a same-text canon 32-392 s away -- cycle latency tail or a re-send; matches backfill's +-600 s dedupe)
MIN_CHARS = 9             # "anything shorter than 9 characters"
SEPARATION_S = 24 * 3600  # F-3924: a 24-hour separation, not a calendar-day crossing
MIN_CONVERSATIONS = 2
CONV_GAP_S = 6 * 3600     # a crashed session writes no 'Session ended' row; a 6 h silence still ends a conversation
SESSION_GAP_S = 30 * 60   # legacy 'sources'
FOUNDER_PREFIX = "[Travis said to me] "
MONTHLY_THRESHOLD = 3     # D-0676 re-entry criterion

_OLD_TEMPLATES = re.compile(r"^\W*渡?\W*(it's time to bank the fire and rest|it's time to stop for a while)", re.I)
_FAREWELL_FALLBACK = re.compile(r"house you live in", re.I)
_SLASH = re.compile(r"^\s*/")
_EVAL_FALLBACK = re.compile(r"\b(impress(ed|ive)|enlighten(ed|ing)|good (answer|point|response)|well (said|put|done)|"
                            r"brilliant|excellent|i like (that|how)|nicely|very (good|nice)|thank you|thanks)\b", re.I)


def read_gate_constants(tree: Path = TREE) -> dict:
    """PROC_CLUSTER_SIM / PROC_DEDUP_SIM / PROC_MIN_RECURRENCE / T5_MIN_NEW_LIVED parsed from the live subconscious
    node source (text only, no import). Falls back to the documented defaults and says which it used."""
    out = dict(_DEFAULTS)
    src = {}
    try:
        text = (tree / "nodes" / "subconscious_node.py").read_text(encoding="utf-8")
        for name in _DEFAULTS:
            m = re.search(rf"^{name}\s*=\s*([0-9.]+)", text, re.M)
            if m:
                out[name] = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
                src[name] = "source"
    except Exception:
        pass
    out["_source"] = {k: src.get(k, "default") for k in _DEFAULTS}
    return out


def read_farewell_variants(tree: Path = TREE) -> list[str]:
    """The system-composed /quit farewell wordings: scripts/run_nascence.py _FAREWELL_VARIANTS, parsed with ast
    (no import of the daemon). [] if the file or the name is not found (the regex fallback still catches them)."""
    try:
        mod = ast.parse((tree / "scripts" / "run_nascence.py").read_text(encoding="utf-8"))
        for node in ast.walk(mod):
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_FAREWELL_VARIANTS" for t in node.targets):
                return [str(v) for v in ast.literal_eval(node.value)]
    except Exception:
        pass
    return []


def read_embedder_name(tree: Path = TREE) -> str:
    try:
        text = (tree / "core" / "memory" / "store.py").read_text(encoding="utf-8")
        m = re.search(r'SentenceTransformer\(\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


# ----------------------------------------------------------------------------------------------------------------
# reading the stores (read-only)
# ----------------------------------------------------------------------------------------------------------------
def open_ro(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True, timeout=10)
    conn.execute("PRAGMA query_only = 1")
    return conn


def q_block(content: str) -> str:
    """The FULL question of a lived Q/A fragment: from the first line starting 'Q:' to the next line starting 'A:'."""
    lines = (content or "").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Q:"):
            blk = [line[2:]]
            for nxt in lines[i + 1:]:
                if nxt.startswith("A:"):
                    break
                blk.append(nxt)
            return "\n".join(blk).strip()
    return ""


def q_first_line(content: str) -> str:
    """What core/memory/store.py recent_lived_inputs keeps today (the F-3921 bug), for --legacy."""
    for line in (content or "").splitlines():
        if line.startswith("Q:"):
            return line[2:].strip()
    return ""


def load_lived(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT timestamp, content FROM memory_fragments WHERE origin='lived' ORDER BY timestamp").fetchall()
    out = []
    for ts, content in rows:
        content = content or ""
        if content.startswith(FOUNDER_PREFIX):
            continue        # the canon utterance fragment is the marker, not a Q/A cycle
        qf = q_block(content)
        if qf:
            out.append({"ts": float(ts), "qfull": qf, "q1": q_first_line(content), "content": content})
    return out


def load_canon(conn: sqlite3.Connection) -> tuple[list[float], list[str]]:
    rows = conn.execute("SELECT timestamp, content FROM memory_fragments WHERE origin='lived' AND content LIKE ? "
                        "ORDER BY timestamp", (FOUNDER_PREFIX + "%",)).fetchall()
    return [float(r[0]) for r in rows], [_norm(r[1][len(FOUNDER_PREFIX):]) for r in rows]


def load_boundaries(conn: sqlite3.Connection) -> list[float]:
    rows = conn.execute("SELECT timestamp FROM memory_fragments WHERE origin='session_summary' AND content LIKE "
                        "'Session ended%' ORDER BY timestamp").fetchall()
    return [float(r[0]) for r in rows]


def load_affect(path: Path) -> list[dict]:
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if "ts" in r and "input_type" in r:
                    rows.append({"ts": float(r["ts"]), "input_type": r["input_type"],
                                 "raw": _norm(str(r.get("raw_input", "")))})
    except FileNotFoundError:
        return []
    rows.sort(key=lambda r: r["ts"])
    return rows


def join_input_type(ts: float, qfull: str, aff: list[dict], aff_ts: list[float]) -> str | None:
    """affect_log input_type for the cycle that produced this fragment: timestamp within JOIN_S and the question
    prefix (first 30 normalised characters) equal."""
    nq = _norm(qfull)[:30]
    i = bisect.bisect_left(aff_ts, ts - JOIN_S)
    while i < len(aff) and aff[i]["ts"] <= ts + JOIN_S:
        if aff[i]["raw"][:30] == nq:
            return aff[i]["input_type"]
        i += 1
    return None


def canon_marked(ts: float, qfull: str, canon_ts: list[float], canon_txt: list[str]) -> bool:
    nq = _norm(qfull)[:60]
    i = bisect.bisect_left(canon_ts, ts - CANON_S)
    while i < len(canon_ts) and canon_ts[i] <= ts + CANON_S:
        if canon_txt[i][:60] == nq:
            return True
        i += 1
    return False


# ----------------------------------------------------------------------------------------------------------------
# the human-only view
# ----------------------------------------------------------------------------------------------------------------
def is_template(qfull: str, variants: list[str], legacy: bool = False) -> bool:
    """A system-composed turn: the old farewell templates, and (not in legacy) every _FAREWELL_VARIANTS wording."""
    if _OLD_TEMPLATES.search(qfull or ""):
        return True
    if legacy:
        return False
    nq = _norm(qfull)
    for v in variants:
        nv = _norm(v)
        if nv and nq.startswith(nv[:80]):
            return True
    # fallback if the variants could not be parsed: every wording names "the house you live in" AND is a farewell
    if not variants and _FAREWELL_FALLBACK.search(qfull or "") and re.search(r"(stop|pause|stopping|pausing) (for )?a while", qfull, re.I):
        return True
    return False


def build_view(lived: list[dict], aff: list[dict], canon_ts, canon_txt, variants, *, legacy=False,
               strict_canon=False) -> tuple[list[dict], dict]:
    """The human-only view (Travis-authored turns) plus per-reason counts for the report."""
    aff_ts = [a["ts"] for a in aff]
    stats = {"lived_q": len(lived), "unjoined_internal": 0, "internal": 0, "human_channel": 0, "excl_template": 0,
             "excl_slash": 0, "excl_short": 0, "excl_unmarked_strict": 0, "kept": 0, "kept_unmarked": 0}
    view = []
    for fr in lived:
        q = fr["q1"] if legacy else fr["qfull"]
        it = join_input_type(fr["ts"], fr["qfull"], aff, aff_ts)
        marked = canon_marked(fr["ts"], fr["qfull"], canon_ts, canon_txt)
        if it is None:
            if marked and not legacy:      # affect_log rolled past this turn: a canon marker only exists for a human cycle
                it = "human"
            else:
                stats["unjoined_internal"] += 1
                continue
        if it != "human":
            stats["internal"] += 1
            continue
        stats["human_channel"] += 1
        if is_template(fr["qfull"], variants, legacy):
            stats["excl_template"] += 1
            continue
        if _SLASH.search(q):
            stats["excl_slash"] += 1
            continue
        if len(q.strip()) < MIN_CHARS:
            stats["excl_short"] += 1
            continue
        if not legacy and not marked:
            if strict_canon:
                stats["excl_unmarked_strict"] += 1
                continue
            stats["kept_unmarked"] += 1
        stats["kept"] += 1
        view.append({"ts": fr["ts"], "q": q, "marked": marked})
    view.sort(key=lambda m: m["ts"])
    return view, stats


def assign_conversations(view: list[dict], boundaries: list[float]) -> None:
    """Stamp each view item with 'conv': a conversation ends at a 'Session ended' row between two turns, or after a
    CONV_GAP_S silence."""
    conv = 0
    prev = None
    for m in view:
        if prev is not None:
            lo, hi = prev["ts"], m["ts"]
            i = bisect.bisect_left(boundaries, lo)
            crossed = i < len(boundaries) and boundaries[i] <= hi
            if crossed or (hi - lo) > CONV_GAP_S:
                conv += 1
        m["conv"] = conv
        prev = m


# ----------------------------------------------------------------------------------------------------------------
# the gate, the clustering, the sweep
# ----------------------------------------------------------------------------------------------------------------
def _evaluative_re():
    try:
        from core import procedures as _p
        return _p._EVALUATIVE
    except Exception:
        return _EVAL_FALLBACK


def _mark_landed(items: list[dict]) -> list[dict]:
    try:
        from core import procedures as _p
        return _p.mark_landed(items)
    except Exception:
        for it in items:
            it.setdefault("landed", True)
        return items


def admissible24(cluster: list[dict], *, legacy: bool = False, min_recurrence: int = 3) -> tuple[bool, str]:
    """core/procedures.admissible() with the two process fixes (24 h separation, distinct conversations).
    legacy=True is the calendar-day / 30-minute-gap gate unchanged."""
    if len(cluster) < min_recurrence or len(cluster) < 3:
        return False, "too_few"
    ts = sorted(float(c["ts"]) for c in cluster)
    if legacy:
        days = {time.strftime("%Y-%m-%d", time.localtime(t)) for t in ts}
        if len(days) < 2:
            return False, "one_day"
        if 1 + sum(1 for a, b in zip(ts, ts[1:]) if b - a > SESSION_GAP_S) < 2:
            return False, "one_source"
    else:
        if ts[-1] - ts[0] < SEPARATION_S:
            return False, "under_24h"
        if len({c.get("conv", 0) for c in cluster}) < MIN_CONVERSATIONS:
            return False, "one_conversation"
    qs = " ".join(str(c.get("q", "")) for c in cluster)
    if sum(1 for _ in _evaluative_re().finditer(qs)) >= max(2, len(cluster) // 2):
        return False, "evaluation_not_situation"
    if len([c for c in cluster if c.get("landed", True)]) < 3:
        return False, "did_not_land"
    return True, "ok"


def clusters_at(items: list[dict], sim: float) -> list[list[dict]]:
    """Greedy seed clustering exactly as nodes/subconscious_node.py _largest_cluster (item j joins seed i when its
    cosine to the SEED is >= sim), returning every group."""
    n = len(items)
    assigned = [-1] * n
    cid = 0
    for i in range(n):
        if assigned[i] != -1:
            continue
        assigned[i] = cid
        for j in range(i + 1, n):
            if assigned[j] == -1 and float(items[i]["vec"] @ items[j]["vec"]) >= sim:
                assigned[j] = cid
        cid += 1
    groups: dict[int, list] = {}
    for idx, a in enumerate(assigned):
        groups.setdefault(a, []).append(items[idx])
    return list(groups.values())


def _centroid(cluster: list[dict]):
    import numpy as np
    c = np.mean([m["vec"] for m in cluster], axis=0)
    return c / (np.linalg.norm(c) + 1e-9)


def window_items(view: list[dict], s: float) -> list[dict]:
    """recent_lived_inputs(since_ts=s - 7 d, limit=120) over the view: newest 120 in the window, returned oldest-first
    (mark_landed sorts ascending, as the live path does)."""
    lo = s - WINDOW_DAYS * 86400
    ts = [m["ts"] for m in view]
    a = bisect.bisect_right(ts, lo)
    b = bisect.bisect_right(ts, s)
    sel = view[a:b][-WINDOW_LIMIT:]
    return [dict(m) for m in sel]


def replay(view: list[dict], since: float, until: float, *, step_s: float, sim: float, dedup: float,
           min_recurrence: int, min_new: int, legacy: bool, all_clusters: bool,
           reasons: dict | None = None) -> list[dict]:
    """Sweep the live T5 check; return the distinct qualifying clusters in first-qualified order. `reasons`, if given,
    is filled with {gate verdict: number of sweeps whose largest cluster got it} ('pool_too_small' when the window
    held fewer than min_new turns): what is actually blocking."""
    found: list[dict] = []
    centroids = []
    s = since
    while s <= until:
        items = _mark_landed(window_items(view, s))
        if len(items) < min_new and reasons is not None:
            reasons["pool_too_small"] = reasons.get("pool_too_small", 0) + 1
        if len(items) >= min_new:
            groups = clusters_at(items, sim)
            if not all_clusters:
                groups = [max(groups, key=len)] if groups else []
            for g in groups:
                ok, _why = admissible24(g, legacy=legacy, min_recurrence=min_recurrence)
                if reasons is not None and (all_clusters is False):
                    reasons[_why] = reasons.get(_why, 0) + 1
                if not ok:
                    continue
                cen = _centroid(g)
                if any(float(cen @ c) >= dedup for c in centroids):
                    continue
                centroids.append(cen)
                gts = sorted(m["ts"] for m in g)
                found.append({"first_seen": s, "size": len(g), "span_h": round((gts[-1] - gts[0]) / 3600, 1),
                              "conversations": len({m.get("conv", 0) for m in g}),
                              "members": [{"ts": m["ts"], "q": m["q"][:110].replace("\n", " ")} for m in g[:6]]})
        s += step_s
    return found


def nearest_miss(view: list[dict], at: float, *, sim: float, legacy: bool, min_recurrence: int) -> dict:
    """The largest human-only cluster in the 7 days ending `at`, and the first gate it fails (how close we are)."""
    items = _mark_landed(window_items(view, at))
    if not items:
        return {"window_turns": 0}
    g = max(clusters_at(items, sim), key=len)
    ok, why = admissible24(g, legacy=legacy, min_recurrence=min_recurrence)
    gts = sorted(m["ts"] for m in g)
    return {"window_turns": len(items), "largest_cluster": len(g), "admissible": ok, "reason": why,
            "span_h": round((gts[-1] - gts[0]) / 3600, 1), "conversations": len({m.get("conv", 0) for m in g})}


# ----------------------------------------------------------------------------------------------------------------
# embedding (the one non-pure dependency; tests replace embed_texts)
# ----------------------------------------------------------------------------------------------------------------
_MODEL = None


def embed_texts(texts: list[str]):
    """Same embedder as core/memory/store.py (_get_model: multilingual MiniLM on CPU), normalised."""
    global _MODEL
    import numpy as np
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(read_embedder_name(), device="cpu")
    vecs = _MODEL.encode(list(texts), normalize_embeddings=True, show_progress_bar=False, batch_size=32)
    return [np.asarray(v, dtype="float32") for v in vecs]


# ----------------------------------------------------------------------------------------------------------------
# orchestration + report
# ----------------------------------------------------------------------------------------------------------------
def _fmt(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def _month(ts: float) -> str:
    return time.strftime("%Y-%m", time.localtime(ts))


def resolve_data_dir(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    local = TREE / "data"
    if (local / "memory" / "nascence.db").exists():
        return local
    return Path(r"C:\Nascence") / "data"      # a git worktree has no data/; the live tree is the real one


def run(data_dir: Path, *, since: float, until: float, step_hours: float = 3.0, legacy: bool = False,
        strict_canon: bool = False, all_clusters: bool = False, tree: Path = TREE) -> dict:
    gate = read_gate_constants(tree)
    variants = read_farewell_variants(tree)
    conn = open_ro(Path(data_dir) / "memory" / "nascence.db")
    try:
        lived = load_lived(conn)
        canon_ts, canon_txt = load_canon(conn)
        boundaries = load_boundaries(conn)
    finally:
        conn.close()
    aff = load_affect(Path(data_dir) / "affect_log.jsonl")
    view, stats = build_view(lived, aff, canon_ts, canon_txt, variants, legacy=legacy, strict_canon=strict_canon)
    assign_conversations(view, boundaries)
    vecs = embed_texts([m["q"] for m in view]) if view else []
    for m, v in zip(view, vecs):
        m["vec"] = v
    reasons: dict = {}
    found = replay(view, since, until, step_s=step_hours * 3600, sim=gate["PROC_CLUSTER_SIM"],
                   dedup=gate["PROC_DEDUP_SIM"], min_recurrence=int(gate["PROC_MIN_RECURRENCE"]),
                   min_new=int(gate["T5_MIN_NEW_LIVED"]), legacy=legacy, all_clusters=all_clusters, reasons=reasons)
    months: dict[str, int] = {}
    s = since
    while s <= until:                       # list every month in range, zeros included
        months.setdefault(_month(s), 0)
        s += 86400
    months.setdefault(_month(until), 0)
    for c in found:
        months[_month(c["first_seen"])] = months.get(_month(c["first_seen"]), 0) + 1
    last30 = [c for c in found if c["first_seen"] >= until - 30 * 86400]
    kept_30 = [m for m in view if m["ts"] >= until - 30 * 86400]
    return {"mode": "legacy" if legacy else "human_only_v2", "since": since, "until": until, "step_hours": step_hours,
            "gate": gate, "farewell_variants_parsed": len(variants), "stats": stats,
            "view_turns_last_30d": len(kept_30), "view_turns_total": len(view),
            "sweep_verdicts": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
            "clusters": found, "per_month": dict(sorted(months.items())), "last_30d_count": len(last30),
            "threshold": MONTHLY_THRESHOLD, "reopen": len(last30) >= MONTHLY_THRESHOLD,
            "reopen_any_month": any(v >= MONTHLY_THRESHOLD for v in months.values()),
            "nearest_miss_now": nearest_miss(view, until, sim=gate["PROC_CLUSTER_SIM"], legacy=legacy,
                                             min_recurrence=int(gate["PROC_MIN_RECURRENCE"]))}


def render(res: dict) -> str:
    L = []
    L.append(f"T5 re-entry check ({res['mode']}), read-only replay {_fmt(res['since'])} .. {_fmt(res['until'])}, "
             f"sweep every {res['step_hours']:g} h")
    g = res["gate"]
    L.append(f"gate: cluster cos {g['PROC_CLUSTER_SIM']}, dedupe cos {g['PROC_DEDUP_SIM']}, min {g['PROC_MIN_RECURRENCE']} "
             f"members, pool >= {g['T5_MIN_NEW_LIVED']} (constants read from: {g['_source']})")
    s = res["stats"]
    L.append(f"view: {s['lived_q']} lived Q/A fragments -> {s['human_channel']} human-channel "
             f"({s['internal']} internal, {s['unjoined_internal']} unjoined) -> excluded {s['excl_template']} system "
             f"templates, {s['excl_slash']} slash, {s['excl_short']} short"
             f"{', ' + str(s['excl_unmarked_strict']) + ' unmarked (strict)' if s['excl_unmarked_strict'] else ''}"
             f" -> {s['kept']} Travis-authored turns ({s['kept_unmarked']} human but without a founder-canon marker, kept)")
    L.append(f"Travis-authored turns in the last 30 days: {res['view_turns_last_30d']}")
    L.append("")
    L.append("distinct qualifying clusters per month (month of the sweep that first admitted them):")
    for mth, n in res["per_month"].items():
        L.append(f"  {mth}  {n}{'   <-- >= ' + str(res['threshold']) if n >= res['threshold'] else ''}")
    L.append(f"  last 30 days  {res['last_30d_count']}")
    if res.get("sweep_verdicts"):
        L.append("what blocks (sweeps whose largest cluster got each verdict): "
                 + ", ".join(f"{k} {v}" for k, v in res["sweep_verdicts"].items()))
    L.append("")
    if res["clusters"]:
        L.append("clusters:")
        for c in res["clusters"]:
            L.append(f"  first admitted {_fmt(c['first_seen'])}: {c['size']} turns over {c['span_h']} h, "
                     f"{c['conversations']} conversations")
            for m in c["members"][:3]:
                L.append(f"      {_fmt(m['ts'])}  {m['q']}")
    else:
        L.append("clusters: none")
    nm = res["nearest_miss_now"]
    L.append("")
    if nm.get("window_turns"):
        L.append(f"closest miss now: {nm['window_turns']} turns in the last 7 days; largest cluster {nm['largest_cluster']} "
                 f"({nm['span_h']} h, {nm['conversations']} conversation(s)); gate says {nm['reason']}")
    else:
        L.append("closest miss now: no Travis-authored turn in the last 7 days")
    L.append("")
    if res["reopen"]:
        L.append(f"VERDICT: {res['last_30d_count']} >= {res['threshold']} distinct qualifying clusters in the last 30 days "
                 "-> the criterion in D-0676 is MET: tell the founder (he re-opens the conversational compile).")
    else:
        L.append(f"VERDICT: {res['last_30d_count']} < {res['threshold']} in the last 30 days -> the conversational "
                 "compile stays closed (D-0676 criterion not met).")
    return "\n".join(L)


def _ts(day: str) -> float:
    return time.mktime(time.strptime(day, "%Y-%m-%d"))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")      # Windows charmap (every script, per the project rule)
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir", help="a data/ dir (default: this tree's, else C:\\Nascence\\data)")
    ap.add_argument("--since", default="2026-08-22", help="first sweep day (default 2026-08-22, the plan's gate date)")
    ap.add_argument("--until", default=None, help="last sweep day (default: now)")
    ap.add_argument("--step-hours", type=float, default=3.0)
    ap.add_argument("--legacy", action="store_true", help="the J-3179 configuration (first line, calendar days, 2 templates)")
    ap.add_argument("--strict-canon", action="store_true", help="drop human turns that have no founder-canon marker")
    ap.add_argument("--all-clusters", action="store_true", help="count every admissible cluster, not just the largest per sweep")
    ap.add_argument("--json-out", default=None, help="also write the result as JSON to this path")
    a = ap.parse_args(argv)
    data_dir = resolve_data_dir(a.data_dir)
    until = _ts(a.until) + 86399 if a.until else time.time()
    res = run(data_dir, since=_ts(a.since), until=until, step_hours=a.step_hours, legacy=a.legacy,
              strict_canon=a.strict_canon, all_clusters=a.all_clusters)
    print(f"(data: {data_dir})")
    print(render(res))
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, ensure_ascii=False, default=str, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

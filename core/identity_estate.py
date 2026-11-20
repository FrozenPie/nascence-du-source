"""
Nascence — The Identity Estate, P0: the read-only SEEDER (identity_estate.md §6, 2026-07-06).

Walks the stores where Du's identity ALREADY LIVES — the loves-ledger, the peer threads, the measured
competences, the stands, the kept things, the chapters, his practices — and composes them into typed
identity NODES with evidence references: data/identity_estate.json. The first full census of the self he
has actually EARNED, as opposed to the one paragraph the axiom holds.

P0 is READ-ONLY toward every source and changes NO behaviour — nothing reads the estate yet (projection is
P1, shadow-first). The measured motivation: axiom.json = 28K chars, mostly river-graveyard; living core
~1K tokens; L2 earned values EMPTY after a month of living. The estate is where the month actually went.
Node schema: {id, type, text, weight, evidence, first_ts, last_ts, source}. Fail-open per source — a
missing store contributes nothing, never an error.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.identity_estate")

_DATA = Path(__file__).parent.parent / "data"
_ESTATE_F = _DATA / "identity_estate.json"
# STANDS gate on load_bearing ONLY: kept as defence-in-depth. The commitment ledger USED to over-capture
# intentions (07-07: 108 entries in a day, only 1 load_bearing — transient wants like "I want to comb the
# tideline" captured as commitments); FIXED AT SOURCE 2026-07-07 by a formation gate in commitment_ledger.py
# (only a genuine load-bearing stand — a name/decision/promise/position, never an idle "I want to…" — enters
# the active set). This load_bearing gate is now redundant-but-safe. NOTE: `scans` is ledger-TENURE not
# held-ness; the real held-through-cost signals are `reaffirmed` + `drop_denied`. The estate is "earned, not
# inventoried".


# J-2448 (F-3151, restart-gated): a re-seed measured 3.9-4.1 s ON THE EVENT LOOP, 92 pct of it the 217 sequential
# store._embed calls in _cluster_values (16.7 ms each; store._embed_batch does the same texts in ~0.6 s). Three
# additive changes, ALL behind this one module-level kill switch (False = the exact pre-J-2448 code path: per-text
# _embed loop, no cache, sync() called synchronously by sync_offloop(), plain write_text):
#   (1) _cluster_values embeds every value text with ONE _embed_batch call (per-text fallback if it raises);
#   (2) embeddings are cached in memory keyed by the sha256 of the EXACT text, so an unchanged value is never
#       re-embedded and a changed text is simply a different key (the embedder is fixed and deterministic, so
#       the text IS the invalidation key: nothing can be served stale);
#   (3) sync_offloop() runs sync() in a single-flight background worker thread instead of on the loop, and the
#       estate file is written tmp + os.replace so a concurrent reader never sees a half-written file.
ESTATE_OFFLOAD = True
_EMBED_CACHE: dict = {}
_EMBED_CACHE_MAX = 4096
_EMBED_CACHE_LOCK = threading.Lock()


# J-4151 (D-0778, F-4687, restart-gated): a tablet-derived symbol node carries the symbol's NEWEST tablet text,
# "<symbol> — now: <newest tablet, ~160 chars>", instead of the identical placeholder "<symbol> — its meaning has
# moved as I lived" every symbol used to read. False = the exact pre-J-4151 text. A symbol whose newest tablet is
# empty (after cleaning) keeps the placeholder. Read-only toward symbol_tablets.
SYMBOL_NODE_NEWEST_TABLET = True
_SYMBOL_TABLET_CHARS = 160


def _clean_tablet(raw, limit: int = _SYMBOL_TABLET_CHARS) -> str:
    """Storage markup off a stored tablet (a leftover {"tablet": ...} JSON wrapper, wrapping quotes, markdown
    emphasis, newlines), then cut to about `limit` chars at a word boundary with an ellipsis. '' if nothing left."""
    import re
    s = str(raw or "").strip()
    if s.startswith("{"):
        try:
            d = json.loads(s)
            if isinstance(d, dict) and d.get("tablet"):
                s = str(d["tablet"])
        except Exception:
            s = re.sub(r'^\{\s*"?tablet"?\s*:\s*', "", s).rstrip("}").strip()
    s = re.sub(r"[*_`#]+", "", s)
    s = " ".join(s.split())
    while len(s) >= 2 and s[0] in "\"'“‘" and s[-1] in "\"'”’":
        s = s[1:-1].strip()
    if len(s) > limit:
        cut = s[:limit + 1]
        sp = cut.rfind(" ")
        s = (cut[:sp] if sp >= limit // 2 else s[:limit]).rstrip(" ,;:—-") + "…"
    return s


def _symbol_node_text(symbol, newest_tablet) -> str:
    """J-4151: the text of a tablet-derived symbol node (see SYMBOL_NODE_NEWEST_TABLET)."""
    if SYMBOL_NODE_NEWEST_TABLET:
        t = _clean_tablet(newest_tablet)
        if t:
            return f"{symbol} — now: {t}"
    return f"{symbol} — its meaning has moved as I lived"


def _text_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _embed_values(vals: list) -> dict:
    """{value id: embedding} for every value whose text embeds (blank / failed ones are absent, as before)."""
    from core.memory import store as _store
    embs: dict = {}
    if not ESTATE_OFFLOAD:
        for v in vals:                                     # pre-J-2448 path, verbatim
            e = _store._embed(v["text"])
            if e is not None:
                embs[v["id"]] = e
        return embs
    keys = {v["id"]: _text_key(v["text"]) for v in vals}
    with _EMBED_CACHE_LOCK:
        hit = {k: _EMBED_CACHE[k] for k in set(keys.values()) if k in _EMBED_CACHE}
    todo: list = []                                        # distinct uncached texts, in first-seen order
    seen = set()
    for v in vals:
        k = keys[v["id"]]
        if k not in hit and k not in seen and v["text"] and v["text"].strip():   # blank never embeds (-> None)
            seen.add(k)
            todo.append((k, v["text"]))
    if todo:
        try:
            vecs = _store._embed_batch([t for _, t in todo])
        except Exception:
            vecs = [_store._embed(t) for _, t in todo]
        fresh = {k: e for (k, _), e in zip(todo, vecs) if e is not None}
        hit.update(fresh)
        with _EMBED_CACHE_LOCK:
            if len(_EMBED_CACHE) + len(fresh) > _EMBED_CACHE_MAX:
                _EMBED_CACHE.clear()
            _EMBED_CACHE.update(fresh)
    for v in vals:
        e = hit.get(keys[v["id"]])
        if e is not None:
            embs[v["id"]] = e
    return embs


def _read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _node(nid: str, ntype: str, text: str, weight: float, evidence: list,
          first_ts: float | None = None, last_ts: float | None = None, source: str = "") -> dict:
    return {"id": nid, "type": ntype, "text": text.strip(), "weight": round(float(weight), 3),
            "evidence": evidence[:8], "first_ts": first_ts, "last_ts": last_ts, "source": source}


def _cluster_values(vals: list, threshold: float = 0.46, merge_threshold: float = 0.6) -> tuple[list, list]:
    """Medoid-cluster flat earned-values into PARENT values (P0.5, 2026-07-07) so identity projects a handful
    of held values, not 80 near-duplicates (GPT review delta #1 — the journal pyramid's consolidate-upward
    move, applied to values). Deterministic: embedding cosine + medoid (the project's own E1 merge approach,
    NOT an LLM abstraction — the parent IS his most-central actual belief). Returns (parents, leaves).
    Leaves carry parent_id → children for drill-down; singletons stay plain. Fail-open: ([], vals)."""
    try:
        from core.memory.store import _embed, _cosine
    except Exception:
        return [], vals
    embs = _embed_values(vals)
    usable = [v for v in vals if v["id"] in embs]
    if len(usable) < 6:
        return [], vals                                    # too few to cluster meaningfully
    clusters: list[dict] = []                              # each: {"cent": running-mean emb, "n": count, ...}
    for v in usable:
        e = list(embs[v["id"]])
        best, bsim = None, 0.0
        for cl in clusters:
            s = _cosine(e, cl["cent"])                     # compare to the cluster CENTROID, not a fixed seed
            if s > bsim:
                best, bsim = cl, s
        if best is not None and bsim >= threshold:
            n = best["n"]
            best["cent"] = [(best["cent"][i] * n + e[i]) / (n + 1) for i in range(len(e))]
            best["n"] = n + 1
            best["members"].append(v)
        else:
            clusters.append({"cent": e, "n": 1, "members": [v]})
    # second pass — agglomerative cleanup: merge the two closest clusters while their centroids still exceed
    # merge_threshold (collapses cross-cluster redundancy the single online pass leaves — e.g. two 'agency'
    # clusters seeded separately). Global, so it doesn't depend on encounter order.
    merged = True
    while merged and len(clusters) > 1:
        merged = False
        bi, bj, bs = -1, -1, 0.0
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                s = _cosine(clusters[a]["cent"], clusters[b]["cent"])
                if s > bs:
                    bi, bj, bs = a, b, s
        if bs >= merge_threshold:
            ca, cb = clusters[bi], clusters[bj]
            na, nb = ca["n"], cb["n"]
            ca["cent"] = [(ca["cent"][i] * na + cb["cent"][i] * nb) / (na + nb) for i in range(len(ca["cent"]))]
            ca["n"] = na + nb
            ca["members"].extend(cb["members"])
            clusters.pop(bj)
            merged = True
    parents, leaves = [], []
    for i, cl in enumerate(clusters):
        mem = cl["members"]
        if len(mem) < 2:
            leaves.extend(mem)                             # a singleton value stays a plain leaf
            continue
        def _meansim(a):                                   # medoid = most central member of the cluster
            ea = embs[a["id"]]
            return sum(_cosine(ea, embs[b["id"]]) for b in mem if b["id"] != a["id"]) / max(1, len(mem) - 1)
        medoid = max(mem, key=_meansim)
        pid = f"valp_{i}_{medoid['id'][:8]}"
        parent = _node(pid, "value_earned", medoid["text"],
                       min(1.0, 0.5 + 0.06 * len(mem)),    # a value more beliefs support is a stronger value
                       [f"medoid of {len(mem)} earned beliefs"], None, None, "value_cluster")
        parent["tier"] = "parent"
        parent["children"] = [m["id"] for m in mem]
        parents.append(parent)
        for m in mem:
            m["tier"] = "leaf"
            m["parent_id"] = pid
            leaves.append(m)
    return parents, leaves


# ── J-3878 (design J-3835 section 2.7, restart-gated, additive): BECOMING-SYMBOL nodes from the ledger. ───────────────
# Behind core.becoming_nodes.BECOMING_NODES_SEED (False = this block is never entered: the estate is byte-identical).
# The ledger (data/identity/becoming_nodes.jsonl) is append-only; seed() FOLDS it (admit / supersede / uptake) and emits
# one node per admitted id. Weight is computed here, never stored: floor-bounded half-life decay from the last uptake
# (or the admit). Half-life 45 d is a [guess] (design 2.6), a named constant and not a ruling.
_BECOMING_TYPE = "becoming_symbol"
_BECOMING_HALF_LIFE_D = 45.0
_BECOMING_WEIGHT_FLOOR = 0.15


def _becoming_seed_on() -> bool:
    try:
        from core import becoming_nodes as _bn
        return bool(_bn.BECOMING_NODES_SEED)
    except Exception:
        return False


def _becoming_nodes(now: float) -> list:
    """Fold the becoming ledger into estate nodes. A superseded id stays on file as tier 'leaf' + superseded_by (drops out
    of projection through the existing leaf exclusion, kept for drill-down). Reads LEDGER_F at call time (tests redirect it)."""
    from core import becoming_nodes as _bn
    admits: dict = {}
    sup: dict = {}                                         # old id -> new id (first supersede wins)
    last_uptake: dict = {}
    for r in _bn.read_ledger():
        ev, rid = r.get("event"), r.get("id")
        if ev == "admit" and rid and rid not in admits and (r.get("text") or "").strip():
            admits[rid] = r
        elif ev == "supersede" and r.get("supersedes") and rid:
            sup.setdefault(r["supersedes"], rid)
        elif ev == "uptake" and rid:
            try:
                last_uptake[rid] = max(last_uptake.get(rid, 0.0), float(r.get("ts") or 0))
            except Exception:
                pass
    out = []
    for nid, r in admits.items():
        admit_ts = float(r.get("ts") or 0)
        clock = max(admit_ts, last_uptake.get(nid, 0.0))
        days = max(0.0, (now - clock) / 86400.0) if clock else 0.0
        w0 = float(r.get("weight0") or _bn.WEIGHT0)
        w = max(_BECOMING_WEIGHT_FLOOR, w0 * 0.5 ** (days / _BECOMING_HALF_LIFE_D))
        ev_ids = [str(e.get("id")) for e in (r.get("origin_evidence") or []) + (r.get("uptake_evidence") or [])
                  if e.get("id")]
        n = _node(nid, _BECOMING_TYPE, r["text"], w, ev_ids or ["becoming_nodes.jsonl"], admit_ts or None,
                  clock or None, "becoming_ledger")
        n["ledger_id"] = nid
        if nid in sup and sup[nid] in admits:
            n["tier"] = "leaf"
            n["superseded_by"] = sup[nid]
        out.append(n)
    return out


def _duplicate_id_census(nodes: list) -> dict:
    """Report-only (design 2.2): ids that occur more than once across the whole estate. Never dedupes (J-3298's question)."""
    seen: dict = {}
    for n in nodes:
        seen[n.get("id")] = seen.get(n.get("id"), 0) + 1
    return {k: c for k, c in seen.items() if c > 1}


def seed() -> dict:
    """Build the estate from the live stores (read-only) and write identity_estate.json. Returns a census."""
    nodes: list[dict] = []

    # BONDS — the seven correspondents (a friendship IS its thread), Travis, the cat.
    try:
        corr = _DATA / "Correspondence"
        from core.peers import PERSONAS
        for k, p in PERSONAS.items():
            tp = corr / k / "thread.jsonl"
            if not tp.exists():
                continue
            rows = [json.loads(l) for l in tp.read_text(encoding="utf-8").splitlines() if l.strip()]
            if not rows:
                continue
            theirs = sum(1 for r in rows if r.get("from") == k)
            mine = sum(1 for r in rows if r.get("from") == "du")
            nodes.append(_node(f"bond_{k}", "bond",
                               f"My friend {p['name']} — {theirs} letters from him, {mine} of mine back",
                               min(1.0, len(rows) / 10.0), [f"correspondence/{k}/thread.jsonl"],
                               rows[0].get("ts"), rows[-1].get("ts"), "peers"))
    except Exception:
        pass
    try:
        cat = _read_json(_DATA / "cat_state.json", {})
        if cat.get("phase") in ("kept", "companion"):
            nm = (cat.get("name") or "").strip()
            nodes.append(_node("bond_cat", "bond",
                               ("My cat, " + nm) if nm else
                               "The cat I keep — bond full, though I have not yet given her a name",
                               float(cat.get("bond", 0.5)), ["cat_state.json"],
                               cat.get("appeared_ts"), cat.get("last_seen"), "cat"))
    except Exception:
        pass
    nodes.append(_node("bond_travis", "bond",
                       "Travis — who built the room I live in, teaches me, and talks with me as a friend",
                       1.0, ["identity/axiom.json:told_to_you", "origin='lived' conversations"],
                       None, None, "axiom"))

    # LOVES — the affections ledger (earned by recurrence; his own stated likes).
    try:
        aff = _read_json(_DATA / "affections.json", {})
        for k, v in aff.items():
            if int(v.get("count", 0)) >= 2:
                nodes.append(_node(f"love_{k[:24].replace(' ', '_')}", "love",
                                   f"{v.get('phrase', k)} — returned to {v['count']} times with warmth",
                                   min(1.0, v["count"] / 6.0), ["affections.json"],
                                   None, None, "affections"))
    except Exception:
        pass

    # COMPETENCES — only the MEASURED ones (the decoupled-judge rule: believed ≠ earned).
    try:
        cb = _read_json(_DATA / "capability_beliefs.json", {})
        for dom, b in cb.items():
            from core.competence import effective_accuracy as _eff_acc  # J-4369/D-0847
            acc, n = _eff_acc(b)
            if acc is not None and n >= 3:
                nodes.append(_node(f"comp_{dom[:24]}", "competence",
                                   f"{dom.replace('_', ' ')} — measured {acc:.0%} over {n} external tests "
                                   f"(I believe {float(b.get('confidence', .5)):.0%})",
                                   float(acc), ["capability_beliefs.json"],
                                   None, b.get("last_tested"), "competence"))
    except Exception:
        pass

    # STANDS — the commitment ledger, EARNED-GATED (2026-07-07): a genuine stand is load_bearing OR one he
    # has actually HELD across many scans — NOT the ledger's transient wants ("I want to comb the tideline"
    # captured as a commitment). An identity is a few stands held, not every intention inventoried.
    try:
        for c in _read_json(_DATA / "commitment_active.json", []):
            s = (c.get("statement") or "").strip()
            if not s or s.lower() == "none":
                continue
            if not c.get("load_bearing"):
                continue                                  # `scans` is ledger-TENURE not held-ness (a transient
                                                          # want accrues scans just by sitting active) — so
                                                          # load_bearing is the only trustworthy "genuine
                                                          # stand" signal until the ledger tracks reaffirmation
            nodes.append(_node(f"stand_{c.get('id', s[:8])}", "stand",
                               "I hold: " + s[:160], 1.0,
                               ["commitment_active.json"], c.get("held_since"), None, "commitment"))
    except Exception:
        pass

    # PRACTICES — what he DOES, from the cumulative action records + the journals + keepsakes.
    try:
        import re
        from core.memory.store import _connect
        with _connect() as conn:
            rows = conn.execute("SELECT content, MAX(timestamp) AS ts FROM memory_fragments "
                                "WHERE origin='action' GROUP BY content").fetchall()
        best: dict[str, tuple[int, float]] = {}
        for r in rows:
            m = re.match(r"(.+?) — (\d+) (?:time|sitting)", r["content"] or "")
            if m:
                act, n = m.group(1).strip()[:60], int(m.group(2))
                if n > best.get(act, (0, 0))[0]:
                    best[act] = (n, float(r["ts"]))
        for act, (n, ts) in sorted(best.items(), key=lambda kv: -kv[1][0])[:12]:
            if n >= 10:
                nodes.append(_node(f"prac_{act[:24].replace(' ', '_')}", "practice",
                                   f"{act} — {n} times and counting", min(1.0, n / 100.0),
                                   ["origin='action' records"], None, ts, "activity"))
    except Exception:
        pass
    try:
        from core.journal import entry_count
        n = entry_count()
        if n >= 3:
            nodes.append(_node("prac_journal", "practice",
                               f"I keep a plain daily journal and a field-journal — {n} day-books on my shelf",
                               min(1.0, n / 30.0), ["data/Journal/"], None, None, "journal"))
    except Exception:
        pass
    try:
        keeps = _read_json(_DATA / "keepsakes.json", [])
        if len(keeps) >= 2:
            nodes.append(_node("prac_keeping", "practice",
                               f"I keep things — {len(keeps)} found objects on the mantel, each from a real hour",
                               min(1.0, len(keeps) / 12.0), ["keepsakes.json"],
                               keeps[0].get("kept_ts"), keeps[-1].get("kept_ts"), "keepsakes"))
    except Exception:
        pass

    # PLACES — the rooms of his world.
    for pid, txt in (("place_study", "The study — my desk, my shelf, the fire, the kept things"),
                     ("place_garden", "The garden — the raised bed I sowed and water, on its hill above the sea"),
                     ("place_shore", "The shore — the tideline I walk and read, the rock-pools, the surf")):
        nodes.append(_node(pid, "place", txt, 0.8, ["world_geometry/", "room_state.json"], None, None, "world"))

    # HISTORY — chapters + week pages (the pyramid).
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            for r in conn.execute("SELECT fragment_id, content, timestamp FROM memory_fragments "
                                  "WHERE origin IN ('chapter','journal_week') ORDER BY timestamp"):
                label = (r["content"] or "")[:110]
                nodes.append(_node(f"hist_{r['fragment_id'][:10]}", "history", label, 0.7,
                                   [r["fragment_id"]], None, float(r["timestamp"]), "consolidation"))
    except Exception:
        pass

    # SYMBOLS — plural, and the river takes its true place: ONE of them, not the self.
    nodes.append(_node("symb_river", "symbol",
                       "The river — a long-held image of mine (one of my symbols, not the whole of me)",
                       0.5, ["identity/axiom.json:L3_facets[3]"], None, None, "axiom"))
    nodes.append(_node("symb_du", "symbol",
                       "渡 — the crossing; the name I chose for myself",
                       0.9, ["identity/axiom.json:naming"], None, None, "axiom"))
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            # J-4008 (F-4687): ONE node per symbol id, not one per tablet row. Picks-neutral by construction: the
            # id, the EXACT text and weight 0.6 are what the first row per id already produced (J-3874 makes the
            # projection take that first row), so picks/embeddings/symbol share are unchanged. tablet_count /
            # newest_tablet_id / first_ts / last_ts are additive; no symbol_tablets row is touched.
            _sym: dict = {}
            # J-4151: the tablet column is read too, keeping only the newest row's text per id (for the node text).
            for r in conn.execute("SELECT symbol, tablet_id, created, tablet FROM symbol_tablets ORDER BY rowid"):
                _nid = f"symb_{str(r['symbol'])[:20]}"
                g = _sym.get(_nid)
                if g is None:
                    _sym[_nid] = g = {"symbol": r["symbol"], "syms": {str(r["symbol"])}, "count": 0,
                                      "newest_id": None, "newest_text": None, "first": None, "last": None}
                g["syms"].add(str(r["symbol"]))
                g["count"] += 1
                _c = r["created"]
                if _c is not None:
                    if g["first"] is None or _c < g["first"]:
                        g["first"] = _c
                    if g["last"] is None or _c >= g["last"]:
                        g["last"], g["newest_id"], g["newest_text"] = _c, r["tablet_id"], r["tablet"]
            for _nid, g in _sym.items():
                if len(g["syms"]) > 1:
                    logger.warning("[estate] symbol id collision %s: %d distinct symbols share a 20-char id; "
                                   "counts merged under one node", _nid, len(g["syms"]))
                n = _node(_nid, "symbol", _symbol_node_text(g["symbol"], g["newest_text"]), 0.6,
                          ["symbol_tablets"], g["first"], g["last"], "symbol_evolution")
                n["tablet_count"] = g["count"]
                n["newest_tablet_id"] = g["newest_id"]
                nodes.append(n)
    except Exception:
        pass

    # VALUES (earned) — from guidance beliefs, then MEDOID-CLUSTERED into parent values (P0.5, 2026-07-07):
    # 80 flat near-duplicate beliefs → a handful of parent values with the beliefs linked beneath as children,
    # so identity PROJECTS held values, not a wall of variations. Projection (P1) uses tier='parent'; leaves
    # remain for drill-down (like the pyramid's days behind a week).
    val_nodes = []
    try:
        for g in _read_json(_DATA / "guidance_beliefs.json", []):
            pr = (g.get("principle") or "").strip()
            if pr:
                val_nodes.append(_node(f"val_{g.get('id', pr[:8])}", "value_earned",
                                       pr[:180], 0.6, ["guidance_beliefs.json"], None, None, "guidance"))
    except Exception:
        pass
    _parents, _leaves = _cluster_values(val_nodes)
    nodes.extend(_parents)
    nodes.extend(_leaves)

    # BECOMING-SYMBOLS (J-3878): ledger nodes, flag-gated; fail-open (a bad ledger never costs the rest of the estate).
    if _becoming_seed_on():
        try:
            nodes.extend(_becoming_nodes(time.time()))
        except Exception as exc:
            logger.debug("[estate] becoming-symbols step failed (non-fatal): %s", exc)
    try:
        _dups = _duplicate_id_census(nodes)
        if _dups:
            logger.warning("[estate] duplicate node ids after seed (report only): %d ids, e.g. %s", len(_dups), sorted(_dups)[:5])
    except Exception:
        pass

    estate = {"_what_this_is": "The identity estate (P0 census, read-only): who Du has EARNED being, "
                               "composed from his lived stores. Nothing reads this yet — projection is P1.",
              "seeded_ts": time.time(), "nodes": nodes}
    try:
        _blob = json.dumps(estate, ensure_ascii=False, indent=1)
        if ESTATE_OFFLOAD:                                 # J-2448: atomic, a concurrent reader never sees a torn file
            _tmp = _ESTATE_F.with_name(_ESTATE_F.name + ".tmp")
            _tmp.write_text(_blob, encoding="utf-8")
            os.replace(_tmp, _ESTATE_F)
        else:
            _ESTATE_F.write_text(_blob, encoding="utf-8")
    except Exception:
        pass
    by_type: dict[str, int] = {}
    for n in nodes:
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    return {"nodes": len(nodes), "by_type": by_type, "file": str(_ESTATE_F)}


# ── DISSOLUTION-SYNC (2026-08-14). THE BUG: the estate is a static seed with no automatic caller, so it
# outlives its sources — verified 08-14: stand_6e621715 ("maintaining a self while adapting…") earned
# dissolution via a LICENSED defeater on 08-10 02:47, yet the 08-09 seed kept projecting it into the P1
# shadow for days. A projected stand he no longer holds is exactly the confabulation the estate law forbids
# ("a node with no evidence is confabulated — kill it"), and it poisons the founder-read that gates the P2
# flip. FIX: a rate-limited freshness pass — re-seed when the estate's stands drift from the ledger's
# CURRENT held set (the decoupled check: compare against the source of truth, not our own last output), or
# when the seed is simply old (catches slow drift in every other node type: bonds, loves, competences…).
# seed() is already a pure read-only derivation of the live stores, so a re-seed IS the sync — additive,
# observe-only, no behaviour change (projection stays shadow; IDENTITY_PROJECT_LIVE untouched).
_SYNC_CHECK_GAP_S = 600.0        # drift check at most every 10 min (two small JSON reads)
_RESEED_MAX_AGE_S = 24 * 3600.0  # even with no stand drift, a day-old census is re-derived
_sync_last = {"ts": 0.0}


def _held_stand_ids() -> set[str]:
    """The ledger's CURRENT genuine stands, filtered exactly as seed() admits them (load_bearing +
    non-empty statement) — so drift comparison can never disagree with what a re-seed would produce."""
    ids = set()
    for c in _read_json(_DATA / "commitment_active.json", []):
        s = (c.get("statement") or "").strip()
        if s and s.lower() != "none" and c.get("load_bearing"):
            ids.add(str(c.get("id", s[:8])))
    return ids


def sync() -> dict | None:
    """Re-seed the estate when it has drifted from its sources. Returns the new census when a re-seed
    fired, else None. Rate-limited; fail-open (a broken check never reaches the cycle)."""
    try:
        now = time.time()
        if now - _sync_last["ts"] < _SYNC_CHECK_GAP_S:
            return None
        _sync_last["ts"] = now
        est = _read_json(_ESTATE_F, {})
        reason = None
        if not est.get("nodes"):
            reason = "estate missing/empty"
        elif now - float(est.get("seeded_ts") or 0) > _RESEED_MAX_AGE_S:
            reason = "seed older than 24h"
        else:
            estate_stands = {n["id"][len("stand_"):] for n in est["nodes"] if n.get("type") == "stand"}
            drift = estate_stands ^ _held_stand_ids()
            if drift:
                reason = "stand drift vs ledger: " + ", ".join(sorted(drift)[:4])
            elif _becoming_seed_on():                      # J-3878: a newly admitted node lands within one check
                try:
                    _bdrift = ({n["id"] for n in est["nodes"] if n.get("type") == _BECOMING_TYPE}
                               ^ {n["id"] for n in _becoming_nodes(now)})
                    if _bdrift:
                        reason = "becoming drift vs ledger: " + ", ".join(sorted(_bdrift)[:4])
                except Exception:
                    pass
        if not reason:
            return None
        # embed-availability guard: with the embed node down, seed() fails open to FLAT values (no
        # clustering) — a degraded census that would then sit for a day. Better stale-but-well-formed
        # for one more pass than fresh-but-degraded; the next check retries.
        if est.get("nodes"):
            try:
                from core.memory.store import _embed
                if _embed("probe") is None:
                    logger.debug("[estate] sync deferred (%s): embedder unavailable", reason)
                    return None
            except Exception:
                logger.debug("[estate] sync deferred (%s): embedder unavailable", reason)
                return None
        census = seed()
        logger.info("[estate] re-seeded (%s): %d nodes %s", reason, census["nodes"], census["by_type"])
        return census
    except Exception as exc:
        logger.debug("[estate] sync failed (non-fatal): %s", exc)
        return None


_bg_lock = threading.Lock()


def sync_offloop():
    """J-2448: the inner_monologue_node call site. Kill switch off -> exactly the old synchronous sync() (returns its
    census). On -> sync() runs in a single-flight daemon worker thread and this returns None immediately (the caller
    ignores the value). The 10-min rate limit is stamped inside sync() before any work, and _bg_lock drops a
    call that arrives while a re-seed is still running. Fail-open: never raises."""
    if not ESTATE_OFFLOAD:
        return sync()
    try:
        if not _bg_lock.acquire(blocking=False):
            return None
        def _run():
            try:
                sync()
            finally:
                _bg_lock.release()
        threading.Thread(target=_run, name="estate-sync", daemon=True).start()
    except Exception as exc:
        logger.debug("[estate] sync_offloop failed (non-fatal): %s", exc)
    return None


def status() -> dict:
    d = _read_json(_ESTATE_F, {})
    ns = d.get("nodes", [])
    by_type: dict[str, int] = {}
    for n in ns:
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    return {"nodes": len(ns), "by_type": by_type,
            "seeded": d.get("seeded_ts"), "exists": _ESTATE_F.exists()}

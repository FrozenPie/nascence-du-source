"""
Nascence — the World Ledger's first consumer: "what do I know about X" (J-2217, T-0089, Travis 2026-10-16).

SHADOW-ONLY. Nothing here reaches Du. When an existing memory-service call (core/memory_service.ask(),
D-0292's loops: pursuits, curiosity, the recall act, dreams -- nothing unasked) names in its cue a
referent the World Ledger knows (core/object_graph.py's graph, data/lane2/graph.json), this module logs
what a "what do I know about X" query WOULD have returned, beside a short summary of the recall that
actually came back, to its own dedicated shadow file (data/world_ledger_ask_shadow.jsonl, fenced with
profile.guard_path -- a non-live process is refused, swallowed by the fail-open net). ask()'s own return
value is never read back, never changed, never delayed beyond the in-memory token match below.

The would-return shape follows docs/plans/emissary_lane2.md's PER-PROPERTY EARNING LAW and its "knowledge
is partial by design" correction, field by field:

  * PRESENCE, not depth, unless depth was earned: every referent carries its encounter-depth ladder
    (seen / looked_at / investigated / kept) and its entry-channel mix (read / lived / thought / told /
    dream) -- how the knowledge got in, channels kept distinct.
  * Per-property atoms ONLY where a property was earned: a direct percept of an action he performed
    (status KNOWN, the observed values) or his own hypothesis (status SUSPECTED, his own confidence and
    outcome). object_graph._properties_from_object() already reads only Layer 3 (observations) and
    Layer 5 (inferences); this module whitelists fields again on top of that.
  * NEVER emitted, by explicit exclusion (not by omission): the instrument `ledger` (it carries the
    world-side display name `ws_name`, exactly the kind of label the earning law forbids -- "Bleached FIR
    log" pre-answered a species question, wrongly), `reachable_unobserved` (the actions he has NOT
    performed -- a would-be prompt toward an action; world answers, never leads), the trend /
    float_profile / commonality statistics (gauges about him, D-0434: no readout), and anything Layer-1
    (causal_state / physical_state / causal_history -- the graph never holds them, and nothing here
    reads world_substrate.json at all).
  * Class <-> instance stays a PROPOSAL: an item class named in the cue lists up to
    _MAX_INSTANCES instances whose own record names it as `possibly_same_referent_as`, each marked with
    that relation -- never merged (object_graph contract, L9).

Hard boundaries (from the plans; tests in scripts/test_world_ledger_ask.py check them):
  * The Witness reads nothing from the World Ledger (lane2_the_witness.md section 2.8) -- a call whose
    loop names the Witness is refused here, and core/lane2.py never imports this module.
  * The standing loop and the affect courier stay out (D-0080 K1/K3): no tick, no LLM, no affect write.
  * Refresh cadence: `refresh_offloop()` runs ONCE per sleep, from the sleep-consolidation block via
    core.sleep_offloop.off_loop (a worker thread), never per cycle (see its docstring for measured cost).

Reads graph.json DIRECTLY with this module's own mtime-keyed snapshot, NOT object_graph._read_graph():
object_graph.refresh() mutates its own cached dict in place while it runs (in the sleep worker thread),
and a dream's ask() reading that same dict mid-refresh could iterate a dict that is changing size. The
file itself is only ever replaced atomically (tmp + os.replace), so a fresh json.load of it is always a
whole, consistent document.

Kill switches: WORLD_LEDGER_ASK_SHADOW (the per-ask shadow line) and WORLD_LEDGER_SLEEP_REFRESH (the
once-per-sleep rebuild). Restart-gated: lands at the next boot.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.world_ledger_ask")

WORLD_LEDGER_ASK_SHADOW = True      # kill switch: False = memory_service.ask() logs nothing here
WORLD_LEDGER_SLEEP_REFRESH = True   # kill switch: False = the once-per-sleep graph refresh is skipped

_DATA = Path(__file__).parent.parent / "data"
_SHADOW_LOG = _DATA / "world_ledger_ask_shadow.jsonl"


def _graph_path() -> Path:
    """object_graph's OWN resolved graph path (honours its configure() / NASCENCE_DATA_DIR /
    NASCENCE_LANE2_DIR redirects), read at call time -- the writer and this reader can never disagree."""
    from core import object_graph as og
    return og._paths()["graph"]

# Loops that must never be served (lane2_the_witness.md section 2.8: the Witness reads nothing from the
# World Ledger). Matched as a substring of the caller's loop name, case-insensitive.
_REFUSED_LOOPS = ("witness", "lane2")

_MAX_REFERENTS = 6          # per ask: the most specific matches first (longest alias, then most mentioned)
_MAX_INSTANCES = 4          # per class referent: instance records proposed as possibly the same thing
_MAX_VALUES = 6             # per property: distinct observed values kept
_MAX_HYPOTHESES = 4         # per property: his own hypotheses kept (most recent last)
_ACTUAL_SNIPPETS = 3        # the actual recall's first N contents, truncated, for the side-by-side read
_SNIPPET_CHARS = 140

_LOCK = threading.Lock()    # guards the snapshot cache AND the shadow append (curiosity's ask() runs in a
                            # worker thread, dreams/pursuits on the loop thread -- J-1918's own pattern)
_SNAP: dict | None = None
_SNAP_KEY: tuple | None = None


# ─────────────────────────────────────────────────────────────────────────────
# graph snapshot + inverted alias index
# ─────────────────────────────────────────────────────────────────────────────

def _tok(text: str) -> set[str]:
    """object_graph's own tokenizer + singular normaliser, so cue matching is the SAME rule the graph's
    mention pass used to attribute fragments (an alias = a token list, ALL of which must be present)."""
    from core import object_graph as og   # pure functions only; nothing here touches its cache
    return og._normset(og._tokens(text))


def _snapshot() -> dict | None:
    """{doc, by_token, instances_of, key} for the current graph.json, rebuilt only when the file's
    (mtime, size) changes. None if there is no graph yet. Never raises."""
    global _SNAP, _SNAP_KEY
    try:
        p = _graph_path()
        if not p.exists():
            return None
        st = p.stat()
        key = (str(p), st.st_mtime_ns, st.st_size)
        with _LOCK:
            if _SNAP is not None and _SNAP_KEY == key:
                return _SNAP
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        refs = doc.get("referents") or {}
        by_token: dict[str, list[tuple[str, tuple]]] = {}
        instances_of: dict[str, list[str]] = {}
        for lbl, r in refs.items():
            for alias in (r.get("aliases") or ()):
                if alias:
                    by_token.setdefault(alias[0], []).append((lbl, tuple(alias)))
            cls = (r.get("coreference") or {}).get("class_referent")
            if cls:
                instances_of.setdefault(cls, []).append(lbl)
        snap = {"doc": doc, "by_token": by_token, "instances_of": instances_of, "key": key,
                "built_ts": doc.get("built_ts")}
        with _LOCK:
            _SNAP, _SNAP_KEY = snap, key
        return snap
    except Exception as exc:
        logger.debug("[world_ledger_ask] graph snapshot failed (non-fatal): %s", exc)
        return None


def _match(snap: dict, text: str) -> list[tuple[str, tuple]]:
    """Every referent whose alias token-set is a subset of the text's normalised tokens (the mention
    pass's own rule), most specific first: longer alias, then more total mentions."""
    ns = _tok(text)
    if not ns:
        return []
    refs = snap["doc"].get("referents") or {}
    best: dict[str, tuple] = {}
    for t in ns:
        for lbl, alias in snap["by_token"].get(t, ()):
            if all(a in ns for a in alias):
                if lbl not in best or len(alias) > len(best[lbl]):
                    best[lbl] = alias
    return sorted(best.items(),
                  key=lambda kv: (-len(kv[1]), -int((refs.get(kv[0]) or {}).get("total_mentions") or 0), kv[0]))


# ─────────────────────────────────────────────────────────────────────────────
# the query: what do I know about X (earned knowledge only)
# ─────────────────────────────────────────────────────────────────────────────

def _earned_properties(r: dict) -> dict:
    """Whitelisted per-property atoms (the earning law): KNOWN = direct percept of an action he
    performed (with the values he perceived), SUSPECTED = his own hypothesis. Nothing else."""
    out = {}
    for pname, a in (r.get("properties") or {}).items():
        if not isinstance(a, dict):
            continue
        status = a.get("status")
        if status not in ("KNOWN", "SUSPECTED"):
            continue
        atom = {"status": status, "how": a.get("how"), "channel": a.get("channel"),
                "depth": a.get("depth"), "observations": int(a.get("observations") or 0),
                "via_actions": dict(a.get("via_actions") or {})}
        if status == "KNOWN":
            atom["values"] = list(a.get("values") or [])[:_MAX_VALUES]
        hyps = [{"hypothesis": h.get("hypothesis"), "confidence": h.get("confidence"),
                 "outcome": h.get("outcome")}
                for h in (a.get("hypotheses") or []) if isinstance(h, dict)]
        if hyps:
            atom["hypotheses"] = hyps[-_MAX_HYPOTHESES:]
        out[str(pname)] = atom
    return out


def _knowledge(lbl: str, r: dict, alias=None, relation: str | None = None) -> dict:
    """One referent's would-return record. Presence (depth ladder + channel mix) always; per-property
    atoms only where earned. Excluded on purpose: ledger (world-side name), reachable_unobserved
    (a prompt toward an action), trend/float_profile/windowed/commonality (gauges, D-0434)."""
    depth = r.get("depth") or {}
    rec = {
        "referent": lbl,
        "kind": r.get("kind"),
        "depth": {k: int(depth.get(k) or 0) for k in ("seen", "looked_at", "investigated", "kept")},
        "channels": {k: int(v) for k, v in (r.get("channels") or {}).items() if v},
        "mentions": int(r.get("total_mentions") or 0),
        "properties": _earned_properties(r),
    }
    if alias is not None:
        rec["matched_alias"] = list(alias)
    if r.get("trust"):
        rec["trust"] = r.get("trust")            # discovered bigrams are 'ungraded' -- keep that visible
    if relation:
        rec["relation"] = relation
    # the honest summary line of what the record amounts to
    if rec["properties"]:
        rec["knowledge"] = "per_property"
    elif any(rec["depth"].values()) or rec["channels"]:
        rec["knowledge"] = "presence_only"
    else:
        rec["knowledge"] = "named_only"
    return rec


def what_do_i_know(text: str, snap: dict | None = None) -> list[dict]:
    """The query: every referent the World Ledger knows that `text` names, each as its earned-knowledge
    record, plus (for an item class) up to _MAX_INSTANCES instance records marked
    possibly_same_referent_as. [] when nothing matches or there is no graph. Never raises.
    SHADOW-ONLY today: called only by shadow_from_ask() below; nothing returns this to Du."""
    try:
        snap = snap or _snapshot()
        if not snap or not text:
            return []
        refs = snap["doc"].get("referents") or {}
        out = []
        for lbl, alias in _match(snap, text)[:_MAX_REFERENTS]:
            r = refs.get(lbl)
            if not isinstance(r, dict):
                continue
            rec = _knowledge(lbl, r, alias=alias)
            inst = []
            for ilbl in sorted(snap["instances_of"].get(lbl, ()))[:_MAX_INSTANCES]:
                ir = refs.get(ilbl)
                if isinstance(ir, dict):
                    inst.append(_knowledge(ilbl, ir, relation="possibly_same_referent_as"))
            if inst:
                rec["instances"] = inst
                rec["n_instances_total"] = len(snap["instances_of"].get(lbl, ()))
            out.append(rec)
        return out
    except Exception as exc:
        logger.debug("[world_ledger_ask] what_do_i_know failed (non-fatal): %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# the shadow hook (called from memory_service.ask(), after the pool is final)
# ─────────────────────────────────────────────────────────────────────────────

def _cue_text(cue, what, who, where, when) -> str:
    parts = []
    for v in (what if what is not None else cue, who, when):
        if isinstance(v, str):
            parts.append(v)
    if isinstance(where, str):
        parts.append(where)
    elif isinstance(where, dict):
        parts.extend(str(v) for v in where.values() if isinstance(v, str))
    return " ".join(parts)


def shadow_from_ask(loop: str, *, cue=None, what=None, who=None, where=None, when=None,
                    actual: list | None = None) -> None:
    """Log one would-return row if the ask's cue names any referent the graph knows. Writes nothing
    when nothing matches (the shadow is a log of NAMED asks, not of every ask). Never raises, never
    reads or alters `actual` beyond summarising it."""
    if not WORLD_LEDGER_ASK_SHADOW:
        return
    try:
        lp = str(loop or "").lower()
        if any(x in lp for x in _REFUSED_LOOPS):
            return
        text = _cue_text(cue, what, who, where, when)
        if not text.strip():
            return
        snap = _snapshot()
        if not snap:
            return
        t0 = time.perf_counter()
        would = what_do_i_know(text, snap)
        if not would:
            return
        ms = round((time.perf_counter() - t0) * 1000.0, 2)
        actual = list(actual or [])
        named = {r["referent"]: _tok(" ".join(r.get("matched_alias") or [])) for r in would}
        mentions_in_actual = {}
        for lbl, toks in named.items():
            if not toks:
                continue
            mentions_in_actual[lbl] = sum(
                1 for e in actual if toks <= _tok(str(e.get("content") or "")))
        rec = {
            "ts": round(time.time(), 1), "kind": "world_ledger_would_return", "loop": loop,
            "cue": text[:300], "graph_built_ts": snap.get("built_ts"), "match_ms": ms,
            "would_return": would,
            "actual": {
                "n_returned": len(actual),
                "fragment_ids": [e.get("fragment_id") for e in actual if e.get("fragment_id")][:12],
                "origins": [e.get("origin") for e in actual][:12],
                "first": [str(e.get("content") or "")[:_SNIPPET_CHARS] for e in actual[:_ACTUAL_SNIPPETS]],
                "referent_mentioned_in_n": mentions_in_actual,
            },
        }
        from core import profile
        path = profile.guard_path(_SHADOW_LOG)   # D-0179 fence: a non-live, non-isolate()d process is refused
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(rec, ensure_ascii=False, default=str) + "\n"
        with _LOCK, open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as exc:
        logger.debug("[world_ledger_ask] shadow_from_ask(%s) failed (non-fatal): %s", loop, exc)


# ─────────────────────────────────────────────────────────────────────────────
# the once-per-sleep refresh (off-loop)
# ─────────────────────────────────────────────────────────────────────────────

def refresh_offloop() -> dict:
    """Bring data/lane2/graph.json up to date. Meant to run ONCE per sleep in a worker thread
    (core.sleep_offloop.off_loop), never per cycle. No graph yet -> build_full(); otherwise
    refresh(since=the graph's own last_fragment_ts, commonality=False), which re-scans only the days since
    and re-seeds instrument snapshots (idempotent by construction). commonality=False because that L5/L6
    shuffle-null pass alone measured ~165 s of pure-Python CPU on 2026-10-16 (139k geometry tuples) and
    nothing here reads it. Measured the same day against the live stores (read-only, output redirected):
    the first catch-up refresh over the 7 weeks since the 2026-08-29 build re-scanned 86,095 fragments
    and grew the graph 439 -> 1,341 referents. Never raises."""
    if not WORLD_LEDGER_SLEEP_REFRESH:
        return {"ok": False, "skipped": "WORLD_LEDGER_SLEEP_REFRESH off"}
    try:
        from core import object_graph as og
        doc = None
        gp = _graph_path()
        if gp.exists():
            with open(gp, encoding="utf-8") as f:
                doc = json.load(f)
        if not doc or not doc.get("day0"):
            res = og.build_full()
            res["mode"] = "build_full"
        else:
            res = og.refresh(float(doc.get("last_fragment_ts") or doc.get("built_ts") or time.time()),
                             commonality=False)
            res["mode"] = "refresh"
        return res
    except Exception as exc:
        logger.debug("[world_ledger_ask] refresh_offloop failed (non-fatal): %s", exc)
        return {"ok": False, "error": repr(exc)}

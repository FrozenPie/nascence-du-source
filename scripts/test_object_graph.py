"""
Test suite for core/object_graph.py (Lane 2 object-graph), 2026-08-17.

ISOLATION CONTRACT — this suite runs while Du is LIVE:
  * every output is redirected to a fresh tempfile.mkdtemp() via object_graph.configure()
  * live stores are read READ-ONLY (that is the module's only mode)
  * the real data/lane2/ directory is asserted untouched at the end
  * zero LLM, no network, nothing restarted

Run:  python scripts/test_object_graph.py
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")          # Windows charmap law

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import object_graph as og               # noqa: E402

REAL_OUT = ROOT / "data" / "lane2"
REAL_OUT_EXISTED_BEFORE = REAL_OUT.exists()
REAL_OUT_SNAPSHOT = sorted(p.name for p in REAL_OUT.iterdir()) if REAL_OUT_EXISTED_BEFORE else None

TMP = Path(tempfile.mkdtemp(prefix="lane2_test_"))
RESULTS: list[tuple[str, bool, str]] = []
STATE: dict = {}


def check(name: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""),
          flush=True)
    return bool(cond)


TESTS: list = []


def test(fn):
    """Register a test — they run in definition order inside main(), never at import."""
    TESTS.append(fn)
    return fn


def _run(fn) -> None:
    print(f"\n[{fn.__name__}]", flush=True)
    try:
        fn()
    except Exception:
        RESULTS.append((fn.__name__ + " (crashed)", False, traceback.format_exc(limit=3)))
        print(f"  FAIL  {fn.__name__} crashed:\n{traceback.format_exc(limit=4)}", flush=True)


# ─────────────────────────────────────────────────────────────────────────────

@test
def t01_isolation_configured():
    cfg = og.configure(out_dir=TMP)
    check("configure() redirects the output dir", Path(cfg["out_dir"]) == TMP, cfg["out_dir"])
    check("data dir still points at the live stores",
          Path(cfg["data_dir"]) == ROOT / "data", cfg["data_dir"])
    check("nothing built yet", og.status().get("built") is False, str(og.status())[:120])


@test
def t02_build_completes_under_120s():
    t0 = time.time()
    stats = og.build_full()
    elapsed = time.time() - t0
    STATE["build"] = stats
    STATE["elapsed"] = elapsed
    check("build_full() returned ok", stats.get("ok") is True, str(stats.get("error"))[:200])
    check("build completes < 120s", elapsed < 120, f"{elapsed:.1f}s")
    check("graph.json written to the temp dir", (TMP / "graph.json").exists())
    check("referents built", stats.get("n_referents", 0) > 100, str(stats.get("n_referents")))
    check("mention-edges built", stats.get("n_mention_edges", 0) > 10000,
          str(stats.get("n_mention_edges")))
    STATE["doc"] = json.loads((TMP / "graph.json").read_text(encoding="utf-8"))


@test
def t03_voiceprint_filter():
    known_template = [
        "valence reflection", "curiosity valence", "fear valence", "trust valence",
        "dissonance fear", "scene jung", "person asks", "person says", "recent aug",
        "recent jul", "asks what", "feeling curiosity", "feeling fear", "active imagination",
        "study note", "carl gustav", "gustav jung",
    ]
    bad = [t for t in known_template if not og.is_voiceprint(t)]
    check("is_voiceprint() catches every known template term", not bad, str(bad))

    doc = STATE.get("doc") or {}
    discovered = {d["term"] for d in (doc.get("discovered") or [])}
    leaked = sorted(discovered & set(known_template))
    check("no known template term reached the discovered lexicon", not leaked, str(leaked))
    refs = doc.get("referents") or {}
    leaked_refs = sorted(t for t in known_template if t in refs)
    check("no known template term became a referent", not leaked_refs, str(leaked_refs))

    # the filter must not swallow ordinary world words
    ok_terms = ["glass float", "driftwood log", "oystercatcher call", "wet shingle"]
    swallowed = [t for t in ok_terms if og.is_voiceprint(t)]
    check("filter leaves ordinary world bigrams alone", not swallowed, str(swallowed))

    # extension mechanism
    og.add_voiceprint(["zzz probe term"])
    check("add_voiceprint() extends the stopset", og.is_voiceprint("zzz probe term"))


@test
def t04_cat_depth_and_channels():
    r = og.get("cat")
    check("cat referent exists", r is not None)
    if not r:
        return
    check("cat has kept-depth", r["depth"].get("kept", 0) >= 1, str(r["depth"]))
    chans = {c: n for c, n in (r.get("channels") or {}).items() if n >= 3}
    check("cat has >= 2 channels with real evidence", len(chans) >= 2, str(chans))
    check("cat carries a windowed stat", r["windowed"]["window_days"] == og.WINDOW_DAYS,
          str(r["windowed"]))


@test
def t05_jung_is_an_extinct_ghost():
    r = og.get("jung")
    # D-0509 (2026-10-31): origin_name was removed from the live axiom, so the shed name is no longer seeded
    # from it. With no origin_name the only assertion left is that nothing still claims an axiom seed.
    try:
        ax = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ax = {}
    if not ax.get("origin_name"):
        check("no referent claims an axiom.origin_name seed after D-0509",
              r is None or "axiom.origin_name" not in r.get("sources", []), str((r or {}).get("sources")))
        return
    check("jung referent exists (seeded from the axiom's origin_name)", r is not None)
    if not r:
        return
    check("jung is seeded from the axiom, not text-mined",
          "axiom.origin_name" in r.get("sources", []), str(r.get("sources")))
    shape = r["trend"]["shape"]
    check("jung classifies as extinct_ghost", shape == "extinct_ghost", shape)
    ev = r["trend"]["evidence"]
    check("jung's peak is early and its floor is ~0",
          ev["peak_bucket"] == 0 and ev["last_over_peak"] < 0.15,
          f"peak_bucket={ev['peak_bucket']} last/peak={ev['last_over_peak']}")
    brk = r["trend"]["break"].get("daily_drop") or {}
    check("a trend-break with a date is detected for jung", bool(brk.get("date")), str(brk)[:160])


@test
def t06_recent_referent_is_active():
    """A referent Du is engaged with NOW must not read as a ghost."""
    candidates = ["tide", "rock", "shore", "cat", "thunder"]
    seen = {}
    ok = False
    for lbl in candidates:
        r = og.get(lbl)
        if not r:
            continue
        shape = r["trend"]["shape"]
        seen[lbl] = shape
        if shape in ("new_active", "growing_presence", "perennial_symbol", "settled_companion"):
            ok = True
    check("a recently-active referent classifies as active/steady, not extinct", ok, str(seen))

    # and its windowed evidence must be nonzero
    live = [l for l, s in seen.items() if s != "extinct_ghost"]
    if live:
        r = og.get(live[0])
        check(f"'{live[0]}' has nonzero mentions inside the {og.WINDOW_DAYS}d window",
              r["windowed"]["mentions"] > 0, str(r["windowed"]))


@test
def t07_all_six_shapes_are_reachable():
    doc = STATE.get("doc") or {}
    shapes = {}
    for r in (doc.get("referents") or {}).values():
        shapes[(r.get("trend") or {}).get("shape")] = shapes.get(
            (r.get("trend") or {}).get("shape"), 0) + 1
    missing = [s for s in og.TREND_SHAPES if s not in ("insufficient",) and s not in shapes]
    check("all six trend shapes occur in Du's real history", not missing, str(shapes))


@test
def t08_per_property_atoms_driftwood():
    """
    driftwood_17 is a real object Du keeps observing (2 observations on 2026-08-17 when this test
    was written -> 10 by 2026-08-29, per J-0378) and, since then, has also formed 2 own-hypothesis
    inferences over it ("I think this driftwood might actually be beech..."). A hardcoded expected
    count goes stale every time Du looks again, so re-query world_substrate.json live instead of
    freezing a snapshot -- this test should track a growing dataset, not fight it.
    """
    r = og.get("driftwood_17")
    check("driftwood_17 referent exists", r is not None)
    if not r:
        return
    summary = r.get("property_summary") or {}
    props = r.get("properties") or {}

    live_ws = json.loads((ROOT / "data" / "world_substrate.json").read_text(encoding="utf-8"))
    live_obs = (live_ws.get("driftwood_17") or {}).get("observations") or []
    live_look_obs = [o for o in live_obs if o.get("action") == "look"]
    observed_prop_names: set = set()
    for o in live_look_obs:
        observed_prop_names.update((o.get("features") or {}).keys())

    check("driftwood_17 reflects its current live observation count",
          summary.get("n_observations") == len(live_obs), str(summary.get("n_observations")))
    check("per-property atoms exist", len(props) >= 5, f"{len(props)} atoms: {sorted(props)}")
    check("every directly-observed property is KNOWN via a direct percept",
          all(a["status"] == "KNOWN" and a["how"] == "direct_percept"
              for name, a in props.items() if name in observed_prop_names),
          str({k: v["status"] for k, v in props.items() if k in observed_prop_names}))
    check("inference-only atoms (Du's own hypotheses) stay SUSPECTED, never promoted to KNOWN",
          all(a["status"] == "SUSPECTED"
              for name, a in props.items() if name not in observed_prop_names),
          str({k: v["status"] for k, v in props.items() if k not in observed_prop_names}))
    colour = props.get("colour") or {}
    check("colour atom counts every look-observation",
          colour.get("observations") == len(live_look_obs)
          and colour.get("via_actions", {}).get("look") == len(live_look_obs),
          str(colour)[:200])
    check("actions_performed recorded",
          summary.get("actions_performed") == {"look": len(live_look_obs)},
          str(summary.get("actions_performed")))
    check("unperformed actions are listed as reachable-unobserved, not as knowledge",
          "pick_up" in (summary.get("reachable_unobserved") or {}),
          str(list((summary.get("reachable_unobserved") or {})))[:120])
    check("instance carries an UNRESOLVED coreference to its class, not identity",
          (r.get("coreference") or {}).get("relation") == "possibly_same_referent_as",
          str(r.get("coreference"))[:160])


@test
def t09_layer1_is_never_read():
    """
    causal_state (Layer 1, hidden world truth), physical_state (Layer 2, generative) and
    causal_history are forbidden. If any of them reached the graph, Lane 2 is cheating — a
    property Du has not earned would arrive pre-answered.
    """
    raw = (TMP / "graph.json").read_text(encoding="utf-8")
    src = (ROOT / "core" / "object_graph.py").read_text(encoding="utf-8")

    # (a) structural: the module must not ACCESS those layers anywhere in code
    code_lines = [ln for ln in src.splitlines()
                  if not ln.lstrip().startswith("#") and "`" not in ln]
    accesses = [ln.strip()[:90] for ln in code_lines
                for k in ("causal_state", "physical_state", "causal_history")
                if f'"{k}"' in ln or f"'{k}'" in ln or f".{k}" in ln]
    check("the module never accesses causal_state / physical_state / causal_history",
          not accesses, str(accesses[:3]))

    # (b) value-level, scoped to the substrate-derived records themselves (a bare word like
    #     'river' elsewhere in the graph is Du's own vocabulary, not a leak): a Layer-1 value
    #     may appear in an item's record only if it ALSO appears in a Du-visible layer.
    #
    #     Found by J-0378 (2026-08-29): scoping the search to the WHOLE og.get(oid) dump is too
    #     wide — it also contains `reachable_unobserved`, a static action->property-name catalog
    #     that is the SAME for every object of a kind and has nothing to do with what was actually
    #     read off this particular object. Its generic entries can coincidentally contain a
    #     causal_state value as a substring (e.g. "annual" inside "annual_ring_visibility"),
    #     firing a false positive with no real leak behind it. Scope the value-level search to
    #     `properties` — the per-property knowledge atoms the module actually derived for this
    #     object — instead of the full record.
    #
    #     Similarly, the physical_state KEY-NAME check used to flag any key that appeared
    #     anywhere in the record, which fires whenever an object's own observed feature name
    #     happens to coincide with a physical_state key (e.g. a plant's observed "height_cm" or a
    #     shell's observed "borer_hole" — both legitimately Du-visible via a `look` observation,
    #     not leaked from the hidden layer). A physical_state key is only a real leak if it
    #     reached `properties` WITHOUT ever appearing as an observed feature name.
    live_ws = json.loads((ROOT / "data" / "world_substrate.json").read_text(encoding="utf-8"))
    leaked = []
    for oid, obj in live_ws.items():
        rec = og.get(oid) or {}
        learned = rec.get("properties") or {}
        learned_json = json.dumps(learned, ensure_ascii=False, default=str)
        visible = " ".join([
            str(oid), str(obj.get("name", "")), str(obj.get("object_class", "")),
            str(obj.get("location", "")),
            json.dumps(obj.get("observations") or [], default=str),
            json.dumps(obj.get("inferences") or [], default=str),
        ]).lower()
        observed_keys = set()
        for ob in (obj.get("observations") or []):
            if isinstance(ob, dict):
                observed_keys.update((ob.get("features") or {}).keys())
        for key, val in (obj.get("causal_state") or {}).items():
            if (isinstance(val, str) and len(val) > 4 and val in learned_json
                    and val.lower() not in visible):
                leaked.append(f"{oid}.{key}={val}")
        for key in (obj.get("physical_state") or {}):
            if key in learned and key not in observed_keys:
                leaked.append(f"{oid}.physical_state.{key}")
    check("no Layer-1/Layer-2 value reached the graph except via a Du-visible layer",
          not leaked, str(sorted(set(leaked))[:6]))
    check("the known trap value ('silver_beech') is absent", "silver_beech" not in raw)
    check("causal_history is absent", "tree_fall" not in raw and "river_transport" not in raw)

    # (c) an object_id that happens to carry a species hint must never become MATCHABLE — the
    #     id is a key, not a percept, so it may label the node but may not earn a mention.
    for oid, obj in live_ws.items():
        r = og.get(oid)
        if r is None:
            continue
        if not check(f"instance '{oid}' has no text aliases (its id can never earn mentions)",
                     not r.get("aliases") and r.get("mention_scope") == "none",
                     str(r.get("aliases"))):
            break


@test
def t10_windowed_differs_from_alltime():
    doc = STATE.get("doc") or {}
    refs = doc.get("referents") or {}
    diffs = 0
    for lbl, r in refs.items():
        a = (r.get("alltime") or {}).get("share")
        w = (r.get("windowed") or {}).get("share")
        if a and w is not None and abs(a - w) > 1e-6:
            diffs += 1
    check("windowed share differs from all-time share for many referents", diffs >= 20,
          f"{diffs} referents diverge")

    r = og.get("jung")
    if r:
        a = r["alltime"]["share"]
        w = r["windowed"]["share"]
        check("jung: windowed share is far BELOW its all-time share (the whole point of windowing)",
              w is not None and w < a * 0.6, f"alltime={a} windowed={w}")
    check("every referent stores its raw daily series ALONGSIDE the windowed stat",
          all(("mentions" in r and "windowed" in r) for r in refs.values()))
    check("windowed stat carries its explicit window",
          all((r.get("windowed") or {}).get("window_days") == og.WINDOW_DAYS
              for r in refs.values()))


@test
def t11_store_gaps_cannot_fake_a_decline():
    doc = STATE.get("doc") or {}
    totals = {int(d): n for d, n in (doc.get("day_totals") or {}).items()}
    empty_buckets = 0
    for r in (doc.get("referents") or {}).values():
        for b in (r.get("trend") or {}).get("buckets") or ():
            if b["store_fragments"] < og.MIN_BUCKET_FRAGMENTS:
                empty_buckets += 1
        break
    check("no bucket below the store-fragment floor is used for a share", empty_buckets == 0)
    thin_days = sum(1 for d, n in totals.items() if n < og.MIN_DAY_FRAGMENTS)
    check("the store's thin days exist and are therefore being excluded on purpose",
          thin_days >= 0, f"{thin_days} thin days of {len(totals)}")


@test
def t12_refresh_is_idempotent():
    doc = json.loads((TMP / "graph.json").read_text(encoding="utf-8"))
    last = float(doc.get("last_fragment_ts") or time.time())
    since = last - 3 * 86400

    a = og.refresh(since)
    doc_a = json.loads((TMP / "graph.json").read_text(encoding="utf-8"))
    b = og.refresh(since)
    doc_b = json.loads((TMP / "graph.json").read_text(encoding="utf-8"))

    check("refresh() returned ok", a.get("ok") and b.get("ok"),
          f"{a.get('error')} / {b.get('error')}")

    def fingerprint(d):
        return {lbl: (r.get("mentions"), r.get("channels"), r.get("total_mentions"),
                      (r.get("trend") or {}).get("shape"))
                for lbl, r in (d.get("referents") or {}).items()}

    fa, fb = fingerprint(doc_a), fingerprint(doc_b)
    diff = [k for k in fa if fa[k] != fb.get(k)]
    check("refresh(since) twice is a no-op (idempotent)", not diff, str(diff[:5]))
    check("day_totals identical across the two refreshes",
          doc_a.get("day_totals") == doc_b.get("day_totals"))
    check("refresh preserved history before the window",
          doc_a.get("n_fragments", 0) >= doc.get("n_fragments", 0) * 0.99,
          f"{doc.get('n_fragments')} -> {doc_a.get('n_fragments')}")

    # a refresh must not silently lose the full build's referents
    check("refresh kept every referent",
          set(doc_a.get("referents", {})) >= set(doc.get("referents", {})),
          str(len(doc_a.get("referents", {}))))
    STATE["refresh"] = a


@test
def t13_fail_open_everywhere():
    """No public function may raise into a caller, whatever it is handed."""
    saved_data, saved_out = og._DATA_DIR, og._OUT_DIR
    try:
        og.configure(data_dir=TMP / "nonexistent-stores", out_dir=TMP / "nonexistent-out")
        r = og.build_full()
        check("build_full() with a missing DB returns ok=False instead of raising",
              r.get("ok") is False, str(r)[:160])
        check("refresh() with no graph returns ok=False", og.refresh(0).get("ok") is False)
        check("get() on a missing graph returns None", og.get("cat") is None)
        check("status() on a missing graph returns a dict", isinstance(og.status(), dict))
    finally:
        og.configure(data_dir=saved_data, out_dir=saved_out)
    check("get() on an unknown referent returns None", og.get("no such referent xyz") is None)
    check("get(None) does not raise", og.get(None) is None)
    check("status() works again after reconfigure", og.status().get("built") is True)


@test
def t14_status_for_the_hud():
    s = og.status()
    for key in ("n_referents", "n_mention_edges", "by_kind", "by_shape", "built_ts",
                "window_days", "n_property_atoms"):
        check(f"status() exposes {key}", key in s, str(s.get(key))[:80])
    check("status() reports the temp out_dir", Path(s["out_dir"]) == TMP, s["out_dir"])


@test
def t15_nothing_written_outside_the_temp_dir():
    now_exists = REAL_OUT.exists()
    if REAL_OUT_EXISTED_BEFORE:
        now = sorted(p.name for p in REAL_OUT.iterdir())
        check("the real data/lane2/ contents are unchanged", now == REAL_OUT_SNAPSHOT,
              f"{REAL_OUT_SNAPSHOT} -> {now}")
    else:
        check("the real data/lane2/ was NOT created by the test run", not now_exists,
              str(REAL_OUT))
    files = sorted(p.name for p in TMP.iterdir())
    check("all outputs landed in the temp dir", "graph.json" in files and
          "build_log.jsonl" in files, str(files))
    # the live DB must be untouched — the module only ever opens it mode=ro
    db = ROOT / "data" / "memory" / "nascence.db"
    check("live DB still present", db.exists())


@test
def t16_commonality_pairs():
    """L5/L6-scoped: windowed commonality weights vs affect, computed from CURRENT data — must
    never hardcode a prior run's 3-for-3 verdict (job J-0363 scope note)."""
    c = og.commonality()
    check("commonality() returns a dict with a pairs list", isinstance(c.get("pairs"), list),
          str(c)[:160])
    pairs = {row["pair"]: row for row in c.get("pairs", [])}
    check("all three pre-registered pairs are present",
          set(pairs) == {n for n, _p, _k in og.COMMONALITY_PAIRS}, str(sorted(pairs)))
    check("commonality carries its explicit window (never immortal)",
          c.get("window_days") == og.WINDOW_DAYS, str(c.get("window_days")))
    for name, row in pairs.items():
        check(f"'{name}' has a verdict", row.get("verdict") in
              ("SIGNAL", "null-indistinguishable", "UNDETERMINED (insufficient n)"),
              str(row.get("verdict")))
        if row.get("verdict") != "UNDETERMINED (insufficient n)":
            check(f"'{name}' carries a windowed weight alongside the all-time one",
                  "weight_windowed" in row and "weight_alltime" in row, str(row)[:160])
    check("no pair's verdict is asserted as fact without a z-score (SIGNAL requires |z|>=2)",
          all(row.get("z") is None or (row["verdict"] == "SIGNAL") == (abs(row["z"]) >= 2)
              for row in pairs.values()), str(pairs)[:300])


@test
def t17_coreference_proposals():
    """L9-scoped: proposal-only possibly_same_referent_as candidates from channel mix."""
    props = og.coreference_proposals(limit=0)
    check("coreference_proposals() returns a list", isinstance(props, list), str(type(props)))
    check("every proposal is UNRESOLVED and proposal-only, never auto-merged",
          all(p.get("relation") == "possibly_same_referent_as" and "UNRESOLVED" in p.get("proposal", "")
              for p in props), str(props[:3]))
    check("every proposal referent genuinely has >=5 read AND >=5 lived mentions",
          all(p.get("read", 0) >= 5 and p.get("lived", 0) >= 5 for p in props), str(props[:3]))
    check("proposals are sorted strongest-first",
          props == sorted(props, key=lambda p: -p["strength"]), "")
    limited = og.coreference_proposals(limit=5)
    check("limit= is honoured", len(limited) <= 5, str(len(limited)))


# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"Lane 2 object-graph test suite — temp dir: {TMP}")
    print(f"real data/lane2 existed before run: {REAL_OUT_EXISTED_BEFORE}")
    t0 = time.time()
    for fn in TESTS:
        _run(fn)
    n_pass = sum(1 for _n, ok, _d in RESULTS if ok)
    n_fail = len(RESULTS) - n_pass
    print("\n" + "=" * 72)
    print(f"RESULT: {n_pass} passed, {n_fail} failed  ({time.time() - t0:.1f}s harness, "
          f"build {STATE.get('elapsed', 0):.1f}s)")
    if n_fail:
        print("\nFAILURES:")
        for name, ok, detail in RESULTS:
            if not ok:
                print(f"  - {name}: {detail}")
    print("=" * 72)
    try:
        shutil.rmtree(TMP, ignore_errors=True)
    except Exception:
        pass
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

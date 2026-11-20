"""Test for J-2217 (T-0089): core/world_ledger_ask.py -- the World Ledger's first consumer, SHADOW-ONLY.

Checks (read-only on live data/: it copies data/lane2/graph.json into a temp dir and only stats live files):
  1. core resolves inside this worktree (import core BEFORE lab_env, F-2423);
  2. what_do_i_know() on a real cue returns earned knowledge: presence (depth + channels) always, per-property
     atoms only where earned (KNOWN = direct percept with values, SUSPECTED = his own hypothesis);
  3. the earning law's exclusions hold on the WHOLE real graph: no ledger / ws_name / reachable_unobserved /
     trend / float_profile / windowed / commonality key anywhere in any referent's would-return record, and no
     Layer-1 causal_state value reaches an instance record unless it is also Du-visible (t09's own rule);
  4. class -> instance stays a proposal (relation possibly_same_referent_as);
  5. a Witness-named loop is refused, and core/lane2.py never imports this module or object_graph;
  6. memory_service.ask() returns byte-identical output with the shadow on vs off (the shadow never alters the
     pool), and with the shadow on writes exactly one would-return row into the isolate()d sandbox;
  7. a non-live, non-isolated process pointed at the LIVE shadow path writes nothing (guard_path fence);
  8. refresh_offloop() against the live stores (read-only) writes only into the redirected out dir, and the
     result is still consumable;
  9. the live data/ top level and data/lane2/ are unchanged end to end (canary).
Exit 0 = pass. Run from a worktree:  python scripts/test_world_ledger_ask.py [--skip-refresh]
"""
import json, os, pathlib, shutil, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
from core import object_graph as og, world_ledger_ask as wla, memory_service, associative_recall
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env

LIVE = pathlib.Path(r"C:\Nascence") / "data"
FAILS = []


def check(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)


def fp(d: pathlib.Path):
    out = {}
    if d.exists():
        for p in d.iterdir():
            if p.is_file() and not p.name.endswith(".log"):
                st = p.stat()
                out[p.name] = (st.st_size, st.st_mtime_ns)
    return out


def diff(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


before_top, before_l2 = fp(LIVE), fp(LIVE / "lane2")

TMP = pathlib.Path(tempfile.mkdtemp(prefix="j2217_"))
shutil.copy2(LIVE / "lane2" / "graph.json", TMP / "graph.json")
og.configure(data_dir=LIVE, out_dir=TMP)      # stores read-only from live; every og write lands in TMP
check("graph path resolves to the temp copy", wla._graph_path() == TMP / "graph.json", str(wla._graph_path()))

# 2 + 4 -- a real cue
t0 = time.perf_counter()
snap = wla._snapshot()
load_ms = (time.perf_counter() - t0) * 1000
check("snapshot loads", bool(snap))
n_refs = len(snap["doc"].get("referents") or {})
print(f"  info  graph: {n_refs} referents, first snapshot load {load_ms:.0f} ms")
t0 = time.perf_counter()
snap2 = wla._snapshot()
check("snapshot is cached on an unchanged file", snap2 is snap)
print(f"  info  cached snapshot {(time.perf_counter() - t0) * 1000:.2f} ms")
t0 = time.perf_counter()
res = wla.what_do_i_know("I keep thinking about the driftwood down on the shore")
print(f"  info  what_do_i_know {(time.perf_counter() - t0) * 1000:.2f} ms -> {[r['referent'] for r in res]}")
dw = next((r for r in res if r["referent"] == "driftwood"), None)
check("the cue finds the driftwood class referent", dw is not None, str([r["referent"] for r in res]))
if dw:
    inst = dw.get("instances") or []
    check("class carries instance proposals, each marked possibly_same_referent_as",
          inst and all(i.get("relation") == "possibly_same_referent_as" for i in inst), str(inst)[:200])
    earned = [i for i in inst if i.get("properties")]
    check("at least one instance carries earned per-property atoms", bool(earned))
    ok_atoms = True
    for i in inst:
        for pn, a in (i.get("properties") or {}).items():
            if a["status"] == "KNOWN" and not (a.get("values") is not None and a["observations"] > 0):
                ok_atoms = False
            if a["status"] == "SUSPECTED" and "values" in a:
                ok_atoms = False
            if a["status"] not in ("KNOWN", "SUSPECTED"):
                ok_atoms = False
    check("KNOWN atoms carry perceived values + observations; SUSPECTED atoms carry no values", ok_atoms)
    for i in inst:
        if not i.get("properties"):
            check("an instance with nothing earned is presence/named only, no property atoms",
                  i["knowledge"] in ("presence_only", "named_only"), i["knowledge"])
            break

# 3 -- exclusions on the WHOLE graph
FORBIDDEN_KEYS = {"ledger", "ws_name", "reachable_unobserved", "trend", "float_profile", "windowed",
                  "commonality", "causal_state", "physical_state", "causal_history", "alltime", "days"}


def keys_of(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            acc.add(k)
            keys_of(v, acc)
    elif isinstance(o, list):
        for v in o:
            keys_of(v, acc)
    return acc


refs = snap["doc"]["referents"]
all_keys = set()
for lbl, r in refs.items():
    keys_of(wla._knowledge(lbl, r), all_keys)
check("no forbidden key in any of the graph's would-return records", not (all_keys & FORBIDDEN_KEYS),
      str(all_keys & FORBIDDEN_KEYS))
live_ws = json.loads((LIVE / "world_substrate.json").read_text(encoding="utf-8"))
leaked = []
for oid, obj in live_ws.items():
    r = refs.get(oid)
    if not isinstance(r, dict):
        continue
    out_json = json.dumps(wla._knowledge(oid, r), ensure_ascii=False, default=str)
    # t09's own Du-visible set (scripts/test_object_graph.py): the object id and its class are how the
    # world addresses the object to him; the display NAME is not (ws_name is excluded outright below).
    visible = " ".join([str(oid), str(obj.get("object_class", "")), str(obj.get("location", "")),
                        json.dumps(obj.get("observations") or [], default=str),
                        json.dumps(obj.get("inferences") or [], default=str)]).lower()
    for key, val in (obj.get("causal_state") or {}).items():
        if isinstance(val, str) and len(val) > 4 and val in out_json and val.lower() not in visible:
            leaked.append((oid, key, val))
    name = str(obj.get("name") or "")
    if name and len(name) > 6 and name in out_json:
        leaked.append((oid, "ws_name", name))
check("no Layer-1 value or world-side name reaches any instance record", not leaked, str(leaked[:3]))

# 5 -- Witness boundary
lane2_src = (HERE / "core" / "lane2.py").read_text(encoding="utf-8")
check("core/lane2.py (the Witness) imports neither world_ledger_ask nor object_graph",
      "world_ledger_ask" not in lane2_src and "import object_graph" not in lane2_src
      and "object_graph as" not in lane2_src)

# 6 -- ask() equivalence + one sandboxed row
FAKE = [{"fragment_id": "frag_a", "content": "the driftwood was wet and pale on the shore", "origin": "lived",
         "activation": 0.9},
        {"fragment_id": "frag_b", "content": "a letter about tides", "origin": "letter", "activation": 0.5}]
real_rf = associative_recall.recall_fragments
associative_recall.recall_fragments = lambda *a, **k: [dict(x) for x in FAKE]
try:
    with lab_env.isolate(db="empty", also=[(wla, ["_SHADOW_LOG"])]) as lab:
        wla.WORLD_LEDGER_ASK_SHADOW = False
        off = memory_service.ask("pursuits", "what do I know about the driftwood", k=3)
        check("no shadow file with the kill switch off", not (lab / "world_ledger_ask_shadow.jsonl").exists())
        wla.WORLD_LEDGER_ASK_SHADOW = True
        on = memory_service.ask("pursuits", "what do I know about the driftwood", k=3)
        check("ask() output identical with the shadow on vs off",
              json.dumps(on, sort_keys=True, default=str) == json.dumps(off, sort_keys=True, default=str))
        memory_service.ask("witness", "what do I know about the driftwood", k=3)
        memory_service.ask("curiosity", "nothing the ledger names zzqx", k=3)
        sp = lab / "world_ledger_ask_shadow.jsonl"
        rows = [json.loads(x) for x in sp.read_text(encoding="utf-8").splitlines()] if sp.exists() else []
        check("exactly one shadow row (pursuits; witness refused; unnamed cue logs nothing)",
              len(rows) == 1 and rows[0]["loop"] == "pursuits", str([r.get("loop") for r in rows]))
        if rows:
            r0 = rows[0]
            check("row carries the actual recall beside the would-return",
                  r0["actual"]["n_returned"] == 2 and r0["actual"]["fragment_ids"] == ["frag_a", "frag_b"]
                  and r0["actual"]["referent_mentioned_in_n"].get("driftwood") == 1, str(r0["actual"]))
            check("row's would_return names driftwood", any(w["referent"] == "driftwood"
                                                             for w in r0["would_return"]))
            print(f"  info  shadow row {len(json.dumps(r0))} bytes, match_ms {r0['match_ms']}")
finally:
    associative_recall.recall_fragments = real_rf
    wla.WORLD_LEDGER_ASK_SHADOW = True

# 7 -- fence: non-live, non-isolated, LIVE path
saved = wla._SHADOW_LOG
wla._SHADOW_LOG = LIVE / "world_ledger_ask_shadow.jsonl"
existed = wla._SHADOW_LOG.exists()
wla.shadow_from_ask("pursuits", cue="the driftwood on the shore", actual=[])
check("non-live process pointed at the LIVE shadow path writes nothing",
      wla._SHADOW_LOG.exists() == existed)
wla._SHADOW_LOG = saved

# 8 -- the sleep refresh, live stores read-only, output redirected
if "--skip-refresh" not in sys.argv:
    t0 = time.perf_counter()
    rr = wla.refresh_offloop()
    print(f"  info  refresh_offloop: mode={rr.get('mode')} ok={rr.get('ok')} referents={rr.get('n_referents')} "
          f"edges={rr.get('n_mention_edges')} rescanned={rr.get('rescanned_fragments')} "
          f"build_seconds={rr.get('build_seconds')} wall={time.perf_counter() - t0:.1f}s")
    check("refresh_offloop ok", rr.get("ok") is True, str(rr)[:300])
    t0 = time.perf_counter()
    new = wla._snapshot()
    print(f"  info  refreshed graph {(TMP / 'graph.json').stat().st_size} bytes, snapshot load "
          f"{(time.perf_counter() - t0) * 1000:.0f} ms, {len(new['doc'].get('referents') or {})} referents")
    t0 = time.perf_counter()
    rr2 = wla.refresh_offloop()
    print(f"  info  second (steady-state) refresh: rescanned={rr2.get('rescanned_fragments')} "
          f"build_seconds={rr2.get('build_seconds')} wall={time.perf_counter() - t0:.1f}s")
    check("steady-state refresh ok", rr2.get("ok") is True, str(rr2)[:300])
    new = wla._snapshot()
    check("sleep refresh keeps the previous commonality block untouched and stamps the skip",
          json.dumps(new["doc"].get("commonality"), sort_keys=True)
          == json.dumps(snap["doc"].get("commonality"), sort_keys=True)
          and new["doc"].get("commonality_skipped_ts"))
    import inspect
    check("object_graph.refresh() default still runs the commonality pass",
          inspect.signature(og.refresh).parameters["commonality"].default is True)
    check("snapshot picks up the refreshed graph", new is not None and new is not snap)
    check("refreshed graph still answers the cue",
          any(r["referent"] == "driftwood" for r in wla.what_do_i_know("the driftwood", new)))
    wla.WORLD_LEDGER_SLEEP_REFRESH = False
    check("refresh kill switch skips", wla.refresh_offloop().get("skipped"))
    wla.WORLD_LEDGER_SLEEP_REFRESH = True

# 9 -- canary
check("live data/ top level unchanged", diff(before_top, fp(LIVE)) == [], str(diff(before_top, fp(LIVE))))
check("live data/lane2/ unchanged", diff(before_l2, fp(LIVE / "lane2")) == [], str(diff(before_l2, fp(LIVE / "lane2"))))
shutil.rmtree(TMP, ignore_errors=True)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)

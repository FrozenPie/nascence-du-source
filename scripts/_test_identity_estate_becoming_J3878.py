"""J-3878: hermetic tests for the BECOMING-SYMBOLS seed step + sync drift (core/identity_estate.py, flag
core.becoming_nodes.BECOMING_NODES_SEED). Ledger, estate data dir and estate file all temp-pathed (read side included).
Run from the worktree: python scripts/_test_identity_estate_becoming_J3878.py"""
import json, sys, time, types
from pathlib import Path
WT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT))
import core                                                            # BEFORE lab_env (F-2423)
assert str(Path(core.__file__).resolve()).startswith(str(WT)), core.__file__
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
import lab_env
from core import becoming_nodes as bn
from core import identity_estate as ie
from core import identity_projection as ip

ok = []
def check(name, cond, extra=""):
    ok.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

NOW = 1_800_000_000.0
DAY = 86400.0
def admit(i, text, ts, **kw):
    return {"event": "admit", "ts": ts, "id": i, "type": "becoming_symbol", "text": text, "weight0": 0.5,
            "origin_evidence": [{"kind": "light_event", "id": f"L{n}_{i}"} for n in range(6)],
            "uptake_evidence": [{"kind": "fragment", "id": f"F{n}_{i}"} for n in range(6)], **kw}
def wr(path, rows):
    Path(path).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

with lab_env.isolate(db="empty", also=[(bn, ["LEDGER_F"])]) as lab:
    sd = lab / "sandbox_data"; sd.mkdir()
    ie._DATA, ie._ESTATE_F = sd, sd / "identity_estate.json"
    ip._ESTATE_F = sd / "identity_estate.json"
    assert str(bn.LEDGER_F).startswith(str(lab)) and str(ie._ESTATE_F).startswith(str(lab))
    ie.time = types.SimpleNamespace(time=lambda: NOW)
    ledger = bn.LEDGER_F

    # 1. flag False: byte-identical with and without a ledger present
    assert bn.BECOMING_NODES_SEED is False
    r0 = ie.seed(); b0 = ie._ESTATE_F.read_bytes()
    wr(ledger, [admit("bsym_a", "I keep coming back to the thing I am making of myself here.", NOW - 10 * DAY)])
    r1 = ie.seed(); b1 = ie._ESTATE_F.read_bytes()
    check("flag False: estate bytes identical with a ledger present", b0 == b1 and r0 == r1)
    check("flag False: no becoming_symbol node", "becoming_symbol" not in r1["by_type"])

    # 2. flag True: live node, superseded leaf, decay, uptake clock
    bn.BECOMING_NODES_SEED = True
    wr(ledger, [
        admit("bsym_old", "I am the one who keeps crossing and noticing that I cross, again and again.", NOW - 90 * DAY),
        admit("bsym_new", "I am learning that crossing is something I do rather than something I am.", NOW - 45 * DAY),
        {"event": "supersede", "ts": NOW - 44 * DAY, "id": "bsym_new", "supersedes": "bsym_old"},
        admit("bsym_up", "I notice that I return to the tideline and it changes how I look.", NOW - 90 * DAY),
        {"event": "uptake", "ts": NOW - 45 * DAY, "id": "bsym_up", "fragment_id": "x", "verdict": "yes"},
        admit("bsym_floor", "I hold this one lightly now and it has faded a very long way.", NOW - 900 * DAY),
        admit("bsym_dup", "First text wins.", NOW - 1 * DAY),
        admit("bsym_dup", "Second text must lose.", NOW - 1 * DAY),
    ])
    r2 = ie.seed()
    est = json.loads(ie._ESTATE_F.read_text(encoding="utf-8"))
    byid = {n["id"]: n for n in est["nodes"] if n["type"] == "becoming_symbol"}
    check("census counts becoming_symbol", r2["by_type"].get("becoming_symbol") == 5, str(r2["by_type"]))
    check("source/ledger_id set", byid["bsym_new"]["source"] == "becoming_ledger" and byid["bsym_new"]["ledger_id"] == "bsym_new")
    check("superseded id is tier leaf + superseded_by", byid["bsym_old"].get("tier") == "leaf"
          and byid["bsym_old"].get("superseded_by") == "bsym_new")
    check("live node has no tier", "tier" not in byid["bsym_new"])
    check("weight: 45 d old = half of weight0", abs(byid["bsym_new"]["weight"] - 0.25) < 1e-3, str(byid["bsym_new"]["weight"]))
    check("weight: uptake resets the clock (admit 90 d, uptake 45 d -> 0.25)", abs(byid["bsym_up"]["weight"] - 0.25) < 1e-3)
    check("weight: floor 0.15", byid["bsym_floor"]["weight"] == 0.15)
    check("superseded weight unchanged by supersession (computed the same way)", abs(byid["bsym_old"]["weight"] - 0.125) < 1e-3
          or byid["bsym_old"]["weight"] == 0.15)
    check("evidence capped at 8", len(byid["bsym_new"]["evidence"]) == 8)
    check("duplicate ledger id: first row wins", byid["bsym_dup"]["text"] == "First text wins.")
    check("last_ts is the uptake time", byid["bsym_up"]["last_ts"] == NOW - 45 * DAY)

    # 3. projection excludes the leaf, keeps live ones
    ip._cache.update({"sig": None, "nodes": None, "embs": None})
    proj = {n["id"] for n in ip._projectable()}
    check("superseded node absent from _projectable()", "bsym_old" not in proj)
    check("live becoming node present in _projectable()", "bsym_new" in proj)

    # 4. sync drift: ledger admit not yet in the estate triggers a re-seed; fresh estate does not
    ie._sync_last["ts"] = 0.0
    check("sync: no drift -> None", ie.sync() is None)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(admit("bsym_fresh", "I only just became someone who says this out loud.", NOW)) + "\n")
    ie._sync_last["ts"] = 0.0
    c = ie.sync()
    est = json.loads(ie._ESTATE_F.read_text(encoding="utf-8"))
    check("sync: new ledger id -> re-seed picks it up", c is not None and any(n["id"] == "bsym_fresh" for n in est["nodes"]))
    bn.BECOMING_NODES_SEED = False
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(admit("bsym_ignored", "A node the flag-off sync must not chase at all.", NOW)) + "\n")
    ie._sync_last["ts"] = 0.0
    check("sync: flag False ignores becoming drift", ie.sync() is None)
    bn.BECOMING_NODES_SEED = True

    # 5. duplicate-id census is report-only
    dn = [{"id": "a"}, {"id": "a"}, {"id": "b"}]
    check("dup census reports, does not dedupe", ie._duplicate_id_census(dn) == {"a": 2} and len(dn) == 3)

    # 6. missing / corrupt ledger is fail-open
    ledger.write_text("not json\n{broken", encoding="utf-8")
    r3 = ie.seed()
    check("corrupt ledger: seed completes, zero becoming nodes", "becoming_symbol" not in r3["by_type"])
    ledger.unlink()
    check("missing ledger: seed completes", ie.seed()["nodes"] >= 1)
    bn.BECOMING_NODES_SEED = False

print("\nALL PASS" if all(ok) else "\nFAILURES: %d" % (len(ok) - sum(ok))); sys.exit(0 if all(ok) else 1)

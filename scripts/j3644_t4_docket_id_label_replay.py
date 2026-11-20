"""J-3644: hermetic READ-ONLY replay of SubconsciousNode._t4_distinct_tensions at the CURRENT state.
Reads a COPY of data/subconscious_state.json (passed as arg, default live path read-only) and the live DB
through a mode=ro sqlite URI (store._connect monkeypatched). Writes nothing except the --out json.
Import core BEFORE anything else; assert core.__file__ inside the worktree."""
import sys, os, json, time, sqlite3, copy
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core
assert str(Path(core.__file__).resolve()).startswith(str(HERE)), core.__file__
from core.memory import store
LIVE = Path(r"C:\Nascence")
DB = LIVE / "data" / "memory" / "nascence.db"
def _ro():
    c = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True, timeout=30, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c
store._connect = _ro
from nodes.subconscious_node import SubconsciousNode
from core import tension_ledger as tl

state_path = Path(sys.argv[1]); out_path = Path(sys.argv[2])
state = json.load(open(state_path, encoding="utf-8"))
n = object.__new__(SubconsciousNode)
def run(st, label):
    n._state = copy.deepcopy(st)
    tens = n._state["tensions"]
    out = n._t4_distinct_tensions(tens)
    # chronic-top (before relabel) = reproduce ordering w/o the sharpen step
    sources = tl._sources_for(tens)
    scored = []
    for t in tens:
        s = tl.score_tension(t, sources)
        if s["contradiction_count"] >= 1:
            scored.append((tl.chronic_mass_of(t), s["contradiction_pressure"], s["last_contradiction_ts"], s["label"], t))
    scored.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    sharp = tl.top_contradiction(tens)
    res = {"case": label, "n_tensions": len(tens), "n_scored": len(scored), "out_ids": [t["id"] for t in out],
           "out_labels": [t.get("_label") for t in out], "out_stored_labels": [t.get("label") for t in out],
           "out0_members_n": len(out[0].get("member_event_ids", [])) if out else None,
           "chronic_top3": [(round(x[0],3), x[1], x[4]["id"], x[3][:90]) for x in scored[:3]],
           "pressure_top": (sharp or {}).get("label"),
           "pressure_top_members_n": len((sharp or {}).get("member_event_ids", [])),
           "pressure_top_id": None}
    if sharp:
        mem = set(sharp.get("member_event_ids", []))
        for t in tens:
            if set(t.get("member_event_ids") or []) == mem:
                res["pressure_top_id"] = t["id"]; break
    if out:
        o0 = out[0]
        res["out0_id_is_pressure_top"] = res["pressure_top_id"] == o0["id"]
        orig = next((t for t in tens if t["id"] == o0["id"]), {})
        res["out0_label_overwritten"] = (o0.get("_label") or "") != (orig.get("label") or "").strip() and (o0.get("_label") or "") != tl.score_tension(orig, sources)["label"]
        res["out0_members_overwritten"] = set(o0.get("member_event_ids") or []) != set(orig.get("member_event_ids") or [])
        res["id_label_mismatch"] = bool(res["out0_label_overwritten"])
    return res
cases = [run(state, "as_is_with_rests")]
s2 = copy.deepcopy(state); s2["t4_rests"] = []
cases.append(run(s2, "no_rests_counterfactual"))
# rest active only for the rested label but expire-shifted (now+4d) to see what a later tick looks like
s3 = copy.deepcopy(state); 
for r in s3.get("t4_rests") or []: r["until"] = 0
cases.append(run(s3, "rests_expired"))
json.dump({"state_file": str(state_path), "state_mtime": os.path.getmtime(state_path), "now": time.time(), "cases": cases,
           "last_self_authoring": state.get("last_self_authoring"), "t4_rests": state.get("t4_rests"),
           "t4_fatigue_counts": state.get("t4_fatigue_counts")}, open(out_path, "w"), indent=1, default=str)
for c in cases: print(json.dumps(c, indent=1, default=str))

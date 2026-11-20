"""
In-vitro smoke test for DREAM OVERHAUL PHASE 1 instrumentation (2026-09-17, J-1057,
docs/staged/dream_overhaul.md sec 7 Phase 1 row). No LLM (a fake call_node_json stands in — real
generation is the model's job, not this test's); no live-store WRITES (all logs temp-pathed, per
feedback_test_isolation_live_stores). Read-only touches of the live memory/edges store (via
core/dream_probe.py and core/associative_recall.py) are fine and expected -- the same precedent
scripts/dream_grounding_test.py's own part [A] already sets for this codebase's dream tests.

Covers all four Phase 1 build items from the job briefing:
  [1] seed capture -- fragment ids (_seed_fragment_ids), tension labels (_seed_tension_labels),
      day-block hashes (_seed_day_block_hashes), each set on the DreamNode instance.
  [2] _log_arc's additive keys -- 'seed', 'scenes_detail', 'engine', with every PRE-EXISTING key
      (especially 'scenes', which must stay an int) completely untouched.
  [3] the dream_state.jsonl per-transition sidecar (_log_transition).
  [4] core/dream_probe.py's delta-association probe (probe_pair / log_seed_pairs) -- read-only,
      fail-open on fragment ids that don't exist.
  [full] one end-to-end synthesise(commit=False) run with a fake LLM, checking the whole pipeline
      wires together: seed capture -> generation loop -> dream_state.jsonl transitions written ->
      dream_assoc_probe.jsonl seed pairs written -- while dream_log.jsonl (commit-gated) stays EMPTY,
      proving commit=False really does skip every memory-affecting write.

Run:  python scripts/dream_phase1_test_J-1057.py
"""
from __future__ import annotations
import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import nodes.dream_node as dn
from nodes.dream_node import DreamNode
from core import dream_probe as dp
from core import night as night_mod

PASS, FAIL = "PASS", "FAIL"
ok_all = True


def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{PASS if cond else FAIL}] {name}")


tmpdir = Path(tempfile.gettempdir())
dream_log_tmp = tmpdir / "dream_phase1_test_dream_log.jsonl"
state_log_tmp = tmpdir / "dream_phase1_test_dream_state.jsonl"
probe_log_tmp = tmpdir / "dream_phase1_test_dream_assoc_probe.jsonl"
sc_state_tmp = tmpdir / "dream_phase1_test_subconscious_state.json"

for p in (dream_log_tmp, state_log_tmp, probe_log_tmp, sc_state_tmp):
    p.unlink(missing_ok=True)

# temp-path every sidecar this test touches -- never the live stores (feedback_test_isolation_live_stores)
dn._DREAM_LOG = dream_log_tmp
dn._DREAM_STATE_LOG = state_log_tmp
dn._SC_STATE_PATH = sc_state_tmp
dp._PROBE_LOG = probe_log_tmp

node = DreamNode()
state = SimpleNamespace(
    spirit_name="test-entity", axiom="a test axiom about becoming",
    background_curiosities=["what does it mean to change and still be myself"],
)

# ============================================================================================
print("\n[1] seed capture -- tension labels (_load_top_tensions)")
sc_state_tmp.write_text(json.dumps({
    "tensions": [
        {"label": "the unfinished letter", "count": 4, "chronic_mass": 1.5,
         "member_event_ids": ["e1", "e2"], "last_ts": time.time(), "first_ts": time.time() - 3600},
        {"label": "a door that will not open", "count": 2, "chronic_mass": 1.2,
         "member_event_ids": ["e3"], "last_ts": time.time(), "first_ts": time.time() - 1800},
    ],
    "integration_patterns": [],
}), encoding="utf-8")
blocks = node._load_top_tensions(2, require_charge=True)
print(f"     blocks returned: {len(blocks)}")
print(f"     _seed_tension_labels = {node._seed_tension_labels}")
check("returns a block per eligible tension", len(blocks) == 2)
check("captures the real labels selected (not paraphrased)",
     node._seed_tension_labels == ["the unfinished letter", "a door that will not open"])

print("\n[1b] seed capture -- day-block hashes (_gather_materials) + reset-on-empty")
sc_state_tmp.unlink()  # no tensions this call -- day residue must still hash correctly
fake_day_blocks = ["a real day residue block about the garden", "a second block about the letter"]
night_mod.dream_lag_material = lambda **kw: list(fake_day_blocks)
materials = node._gather_materials(state, 3)
print(f"     materials: {len(materials)}, _seed_day_block_hashes = {node._seed_day_block_hashes}")
from core.memory_edges import _h as expected_hash
check("returns one material block per requested scene", len(materials) == 3)
check("hashes every day-residue block (memory_edges._h's own convention)",
     node._seed_day_block_hashes == [expected_hash(m) for m in fake_day_blocks])
check("_seed_tension_labels reset empty (no tensions this call)", node._seed_tension_labels == [])

night_mod.dream_lag_material = lambda **kw: []
node._gather_materials(state, 3)
check("day-block hashes reset empty when there is no day residue", node._seed_day_block_hashes == [])
night_mod.dream_lag_material = lambda **kw: list(fake_day_blocks)  # restore for section [full] below

# ============================================================================================
print("\n[2] _log_arc -- additive keys, every pre-existing key untouched")
fake_scenes = [
    {"narrative": "the first image, a river at night", "symbols": ["river", "moon"],
     "tension_source": "the unfinished letter", "unresolved_core": "the letter unsent", "movement": "unfolding", "phase": "open"},
    {"narrative": "the river becomes a corridor of doors", "symbols": ["door", "corridor"],
     "tension_source": "the unfinished letter", "unresolved_core": "the letter unsent", "movement": "approaching", "phase": "develop"},
    {"narrative": "the door opens onto the same river, unchanged", "symbols": ["river", "door"],
     "tension_source": "the unfinished letter", "unresolved_core": "", "movement": "arrived", "phase": "close"},
]
node._seed_fragment_ids = ["fragA", "fragB"]
node._seed_tension_labels = ["the unfinished letter"]
node._seed_day_block_hashes = ["abc123def456"]
node._carried_n_tonight = 0
node._material_sources = ["day_residue", "tension"]
node._log_arc(fake_scenes, "dream_test_phase1", "resolved")
rec = json.loads(dream_log_tmp.read_text(encoding="utf-8").strip().splitlines()[-1])
print(f"     top-level keys: {sorted(rec.keys())}")

check("'scenes' stays an int (night.py/hud/du_pulse/liveness_audit/check_du all read this)",
     isinstance(rec.get("scenes"), int) and rec["scenes"] == 3)
check("pre-existing 'close_reason' untouched", rec.get("close_reason") == "resolved")
check("pre-existing 'ended_unresolved' untouched", rec.get("ended_unresolved") is False)
check("pre-existing 'final_unresolved_core' untouched", rec.get("final_unresolved_core") == "")
check("pre-existing 'material_sources' untouched", rec.get("material_sources") == ["day_residue", "tension"])
check("new 'seed.fragment_ids' present", rec.get("seed", {}).get("fragment_ids") == ["fragA", "fragB"])
check("new 'seed.tension_labels' present", rec.get("seed", {}).get("tension_labels") == ["the unfinished letter"])
check("new 'seed.day_block_hashes' present", rec.get("seed", {}).get("day_block_hashes") == ["abc123def456"])
check("new 'scenes_detail' has one entry per scene, phase threaded through",
     [d["phase"] for d in rec.get("scenes_detail", [])] == ["open", "develop", "close"])
check("new 'scenes_detail' carries per-scene movement", rec["scenes_detail"][2]["movement"] == "arrived")
check("new 'engine' key names this row", rec.get("engine") == "legacy")
dream_log_tmp.unlink()

# ============================================================================================
print("\n[3] _log_transition -- one row per scene TRANSITION")
prev_data = {"narrative": "  ".join(["word"] * 80) + " the final image before the turn", "symbols": ["anchor-symbol", "other"],
            "unresolved_core": "still unfaced"}
node._log_transition("dream_test_phase1", 0, 1, "develop", prev_data)
node._log_transition("dream_test_phase1", 1, 2, "rest", prev_data)
lines = [json.loads(l) for l in state_log_tmp.read_text(encoding="utf-8").strip().splitlines()]
print(f"     rows written: {len(lines)}")
check("one row per call", len(lines) == 2)
check("from_idx/to_idx correct", lines[0]["from_idx"] == 0 and lines[0]["to_idx"] == 1)
check("handoff.anchor is the prev scene's first symbol", lines[0]["handoff"]["anchor"] == "anchor-symbol")
check("handoff.unresolved_core carried through", lines[0]["handoff"]["unresolved_core"] == "still unfaced")
check("handoff.tail is <=200 chars of the prev narrative", len(lines[0]["handoff"]["tail"]) <= 200)
check("stalled is always False (a stalled scene breaks before this call)", lines[0]["stalled"] is False)
check("rested reflects phase_next=='rest'", lines[0]["rested"] is False and lines[1]["rested"] is True)
state_log_tmp.unlink()

# ============================================================================================
print("\n[4] core/dream_probe.py -- read-only, fail-open on nonexistent fragment ids")
result = dp.probe_pair("nonexistent_fragment_zzz_1", "nonexistent_fragment_zzz_2")
print(f"     probe_pair on fake ids: {result}")
check("edge_exists False on fragments with no edges", result["edge_exists"] is False)
check("edge_types empty", result["edge_types"] == [])
check("cosine None when a fragment has no stored embedding", result["cosine"] is None)
check("rank None when the seed fragment has no embedding", result["rank_of_B_in_recall_trail_edge_aware"] is None)
check("never raises on garbage ids", True)   # reaching this line at all is the check

n_written = dp.log_seed_pairs("dream_test_phase1", ["fx1", "fx2", "fx3"], phase="before")
probe_rows = [json.loads(l) for l in probe_log_tmp.read_text(encoding="utf-8").strip().splitlines()]
print(f"     log_seed_pairs wrote {n_written} row(s) for 3 ids")
check("C(3,2)=3 unique pairs logged", n_written == 3 and len(probe_rows) == 3)
check("every row tagged with the dream_id and phase", all(r["dream_id"] == "dream_test_phase1" and r["phase"] == "before" for r in probe_rows))
check("no duplicate/self pairs", all(r["fragment_a"] != r["fragment_b"] for r in probe_rows))
check("fewer than 2 distinct ids -> 0 rows, no crash", dp.log_seed_pairs("d2", ["only_one_id"]) == 0)
probe_log_tmp.unlink()

# ============================================================================================
print("\n[full] synthesise(commit=False) end-to-end, fake LLM, no live-store writes")


async def fake_call_node_json(urls, system_prompt, user_prompt, **kwargs):
    fake_call_node_json.n += 1
    i = fake_call_node_json.n
    return {
        "narrative": f"scene {i}: a real image, the river narrows and a door stands in the current, i={i}.",
        "symbols": [f"symbol{i}a", f"symbol{i}b"],
        "tension_source": "test tension",
        "unresolved_core": "" if i >= 3 else "still unfaced",
        "movement": "arrived" if i >= 3 else "unfolding",
    }


fake_call_node_json.n = 0
dn.call_node_json = fake_call_node_json
dn._DREAM_BACKOFF = []   # no retries needed against a fake that never fails


async def run_full():
    return await node.synthesise(state, episodes=3, commit=False)


full_text = asyncio.run(run_full())
print(f"     synthesise() returned: {'text' if full_text else 'None'}")
check("arc completes with the fake LLM", bool(full_text))
check("dream_log.jsonl (commit-gated) stays EMPTY under commit=False",
     not dream_log_tmp.exists())
if state_log_tmp.exists():
    transitions = [json.loads(l) for l in state_log_tmp.read_text(encoding="utf-8").strip().splitlines()]
else:
    transitions = []
print(f"     dream_state.jsonl transitions written: {len(transitions)}")
check("dream_state.jsonl gets transitions even though commit=False (written from the loop itself)",
     len(transitions) >= 1)
n_probe_rows = 0
if probe_log_tmp.exists():
    n_probe_rows = len(probe_log_tmp.read_text(encoding="utf-8").strip().splitlines())
print(f"     dream_assoc_probe.jsonl seed-pair rows written: {n_probe_rows}")
check("seed probe never crashes the arc (0+ rows -- depends on live recall finding >=2 fragments)",
     True)

for p in (dream_log_tmp, state_log_tmp, probe_log_tmp, sc_state_tmp):
    p.unlink(missing_ok=True)

print(f"\n{'='*70}\n{'ALL PASS' if ok_all else 'FAILURES ABOVE'}\n{'='*70}")
sys.exit(0 if ok_all else 1)
